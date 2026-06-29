#!/usr/bin/env python3
"""
build_newsletter_images.py
Generates missing section images, uploads all to ImgBB, injects into newsletter HTML,
saves thumbnail to .tmp/newsletter_images/, copies final HTML to clipboard.

Run: python build_newsletter_images.py [newsletter_html_file]
If no file given, uses the most recent newsletter_*.html
"""
import os, sys, json, re, time, base64, shutil
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
IMGBB_API_KEY  = os.getenv("IMGBB_API_KEY", "")

SCRIPT_DIR   = Path(__file__).parent
ASSETS_DIR   = SCRIPT_DIR / "assets" / "newsletter_images"
TMP_IMG_DIR  = SCRIPT_DIR / ".tmp" / "newsletter_images"
TMP_IMG_DIR.mkdir(parents=True, exist_ok=True)

IMG_STYLE = 'width:100%; max-width:600px; display:block; margin:0 0 28px 0; border:1px solid #1E1E1E;'

# ------------------------------------------------------------------ #
# Locate newsletter HTML
# ------------------------------------------------------------------ #

def find_newsletter(path_arg=None):
    if path_arg:
        p = Path(path_arg)
        if not p.exists():
            raise SystemExit(f"File not found: {path_arg}")
        return p
    files = sorted(SCRIPT_DIR.glob("newsletter_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    # skip _clean.html files
    files = [f for f in files if "_clean" not in f.name]
    if not files:
        raise SystemExit("No newsletter_*.html found.")
    return files[0]


# ------------------------------------------------------------------ #
# Gemini image generation
# ------------------------------------------------------------------ #

SECTION_PROMPTS = {
    "legal": (
        "Interior of a federal courthouse at dusk, empty wooden benches, tall windows casting long shadows, "
        "scales of justice barely visible on a wall. Dark editorial atmosphere, no people, no logos, cinematic."
    ),
    "rumor": (
        "Two anonymous silhouettes meeting in a dimly lit hallway, one handing a document to the other. "
        "Noir-style lighting, high contrast, dark shadows, no faces visible, editorial atmosphere."
    ),
    "fighter_spotlight": (
        "A single championship boxing belt resting on a velvet cloth under a spotlight in an empty arena. "
        "Cinematic macro shot, dark background, gold and leather detail, no faces, no logos, dramatic editorial style."
    ),
}

def generate_image_bytes(prompt):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="16:9", image_size="2K"),
    )
    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=[prompt],
                config=config,
            )
            for part in response.parts:
                if part.inline_data is not None:
                    return part.inline_data.data
        except Exception as e:
            msg = str(e)
            if "503" in msg or "429" in msg or "UNAVAILABLE" in msg:
                wait = 20 * attempt
                print(f"    Rate limit — retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"    Error: {e}")
                return None
    return None


def generate_missing_images(issue_date, existing_sections):
    needed = [s for s in SECTION_PROMPTS if s not in existing_sections]
    if not needed:
        print("  All section images already exist — skipping generation.")
        return

    for section in needed:
        prompt = SECTION_PROMPTS[section]
        filename = f"nb2_{issue_date}_{section}.jpg"
        out_path = ASSETS_DIR / filename
        if out_path.exists():
            print(f"  [{section}] Already exists at assets/ — skipping")
            continue

        print(f"  Generating [{section}]...")
        image_bytes = generate_image_bytes(prompt)
        if image_bytes:
            out_path.write_bytes(image_bytes)
            print(f"    Saved: {filename} ({len(image_bytes)//1024} KB)")
        else:
            print(f"    FAILED to generate {section}")


# ------------------------------------------------------------------ #
# ImgBB upload
# ------------------------------------------------------------------ #

def upload_to_imgbb(image_path: Path) -> str:
    if not IMGBB_API_KEY:
        print(f"  Warning: IMGBB_API_KEY not set — skipping {image_path.name}")
        return ""
    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": IMGBB_API_KEY},
                files={"image": f},
                timeout=60,
            )
        if resp.ok:
            url = resp.json()["data"]["url"]
            print(f"    ImgBB: {url[:70]}...")
            return url
        print(f"    ImgBB failed {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"    ImgBB error: {e}")
    return ""


def upload_all_images(issue_date):
    """Upload all section images for this issue date to ImgBB. Returns {section: url}."""
    section_names = ["intro", "main_story", "legal", "rumor", "fight_previews", "business_intel", "fighter_spotlight"]
    url_map = {}
    for section in section_names:
        filename = f"nb2_{issue_date}_{section}.jpg"
        img_path = ASSETS_DIR / filename
        if not img_path.exists():
            print(f"  [{section}] File not found: {filename} — skipping")
            continue
        print(f"  Uploading [{section}]...")
        url = upload_to_imgbb(img_path)
        if url:
            url_map[section] = url
    return url_map


# ------------------------------------------------------------------ #
# HTML injection
# ------------------------------------------------------------------ #

SECTION_MARKERS = {
    "Editor's Note":      "intro",
    "EDITOR'S NOTE":      "intro",
    "Main Story":         "main_story",
    "MAIN STORY":         "main_story",
    "Legal Tracker":      "legal",
    "LEGAL TRACKER":      "legal",
    "Rumor Mill":         "rumor",
    "RUMOR MILL":         "rumor",
    "Fight Card Previews": "fight_previews",
    "FIGHT CARD PREVIEWS": "fight_previews",
    "Business Intel":     "business_intel",
    "BUSINESS INTEL":     "business_intel",
    "Fighter Spotlight":  "fighter_spotlight",
    "FIGHTER SPOTLIGHT":  "fighter_spotlight",
}

# The red underline div that appears after each section label
RED_DIVIDER = 'style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"'

def inject_images_into_html(html: str, url_map: dict) -> str:
    """For each section, insert <img> tag after the red divider div."""
    injected = 0
    for section, img_url in url_map.items():
        # Find what label text maps to this section
        labels = [k for k, v in SECTION_MARKERS.items() if v == section]
        if not labels:
            continue

        # Build img tag
        img_tag = f'\n      <img src="{img_url}" alt="{section}" style="{IMG_STYLE}">'

        # For each label, find the block and inject after the red divider
        for label in labels:
            # Find the label in the HTML
            label_idx = html.find(label)
            if label_idx == -1:
                continue

            # Find the red divider div that comes after this label
            divider_idx = html.find(RED_DIVIDER, label_idx)
            if divider_idx == -1:
                continue

            # Find the end of that div tag
            close_bracket = html.find('>', divider_idx)
            if close_bracket == -1:
                continue

            insert_pos = close_bracket + 1

            # Check if img already exists right after this divider
            snippet = html[insert_pos:insert_pos+100]
            if '<img' in snippet:
                print(f"  [{section}] Image already present — replacing")
                # Remove existing img tag first
                img_end = html.find('>', insert_pos + 4) + 1
                html = html[:insert_pos] + html[img_end:]

            html = html[:insert_pos] + img_tag + html[insert_pos:]
            injected += 1
            print(f"  [{section}] Injected image")
            break

    print(f"  Total: {injected}/{len(url_map)} images injected")
    return html


# ------------------------------------------------------------------ #
# Clipboard
# ------------------------------------------------------------------ #

def copy_to_clipboard(text: str):
    try:
        import subprocess
        proc = subprocess.Popen(
            ["powershell", "-Command", "Set-Clipboard -Value $input"],
            stdin=subprocess.PIPE,
        )
        proc.communicate(input=text.encode("utf-8"))
        print("  HTML copied to clipboard")
    except Exception as e:
        print(f"  Clipboard copy failed: {e}")


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #

def main():
    newsletter_path = find_newsletter(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"\n  Build Newsletter Images")
    print(f"  File: {newsletter_path.name}")
    print("=" * 55)

    # Extract issue date from filename
    m = re.search(r"(\d{4}-\d{2}-\d{2})", newsletter_path.name)
    if not m:
        raise SystemExit("Could not extract date from filename")
    issue_date = m.group(1)
    print(f"  Issue date: {issue_date}")

    # Determine which images already exist
    existing = {
        f.stem.replace(f"nb2_{issue_date}_", "")
        for f in ASSETS_DIR.glob(f"nb2_{issue_date}_*.jpg")
    }
    print(f"  Existing images: {', '.join(sorted(existing)) or 'none'}")

    # Step 1: Generate missing images
    print(f"\n[1/4] Generating missing section images...")
    if not GEMINI_API_KEY:
        print("  GEMINI_API_KEY not set — skipping generation")
    else:
        generate_missing_images(issue_date, existing)

    # Step 2: Upload all to ImgBB
    print(f"\n[2/4] Uploading images to ImgBB...")
    if not IMGBB_API_KEY:
        print("  IMGBB_API_KEY not set — cannot upload, will use raw GitHub URLs")
        # Fallback: build url_map from GitHub raw URLs
        url_map = {}
        for f in ASSETS_DIR.glob(f"nb2_{issue_date}_*.jpg"):
            section = f.stem.replace(f"nb2_{issue_date}_", "")
            url_map[section] = f"https://raw.githubusercontent.com/bayshawn2001gmailcom/the-fight-docket/main/assets/newsletter_images/{f.name}"
    else:
        url_map = upload_all_images(issue_date)

    print(f"  Sections with URLs: {', '.join(sorted(url_map.keys()))}")

    # Step 3: Inject into HTML
    print(f"\n[3/4] Injecting images into newsletter HTML...")
    html = newsletter_path.read_text(encoding="utf-8")
    html = inject_images_into_html(html, url_map)
    newsletter_path.write_text(html, encoding="utf-8")
    print(f"  Updated: {newsletter_path.name}")

    # Step 4: Save thumbnail to .tmp
    thumb_dest = TMP_IMG_DIR / f"nb2_{issue_date}_thumbnail.jpg"
    thumb_src = ASSETS_DIR / f"nb2_{issue_date}_main_story.jpg"
    if not thumb_src.exists():
        thumb_src = ASSETS_DIR / f"nb2_{issue_date}_intro.jpg"
    if thumb_src.exists():
        shutil.copy2(thumb_src, thumb_dest)
        print(f"\n[4/4] Thumbnail saved: .tmp/newsletter_images/{thumb_dest.name}")
    else:
        print(f"\n[4/4] Thumbnail source not found — skipping")

    # Step 5: Regenerate inject.js
    print(f"\n[5/5] Regenerating inject.js...")
    try:
        import subprocess
        result = subprocess.run(
            ["python", "beehiiv_prep.py", newsletter_path.name],
            capture_output=True, text=True, cwd=str(SCRIPT_DIR)
        )
        print(result.stdout.strip())
    except Exception as e:
        print(f"  beehiiv_prep.py error: {e}")

    # Copy HTML to clipboard
    inject_js_path = SCRIPT_DIR / newsletter_path.name.replace(".html", ".inject.js")
    if inject_js_path.exists():
        copy_to_clipboard(inject_js_path.read_text(encoding="utf-8"))
    else:
        copy_to_clipboard(html)

    print("\n" + "=" * 55)
    print("  DONE")
    print(f"  HTML       : {newsletter_path.name} (images injected)")
    print(f"  Inject JS  : {inject_js_path.name if inject_js_path.exists() else 'N/A'}")
    print(f"  Thumbnail  : .tmp/newsletter_images/nb2_{issue_date}_thumbnail.jpg")
    print(f"  Clipboard  : inject.js contents copied")
    print("=" * 55)


if __name__ == "__main__":
    main()
