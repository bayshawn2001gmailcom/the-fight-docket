#!/usr/bin/env python3
"""
build_newsletter_images.py
Generates section images from prompts/weekly_prompts.json, saves web copies to .tmp/newsletter_images/, points the HTML at the public GitHub repo,
saves thumbnail to .tmp/newsletter_images/, copies final HTML to clipboard.

Run: python build_newsletter_images.py [newsletter_html_file]
If no file given, uses the most recent newsletter_*.html
"""
import os, sys, json, re, time, base64, shutil
import requests
from pathlib import Path
from dotenv import load_dotenv

from issue_selector import latest_issue

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SCRIPT_DIR   = Path(__file__).parent
ASSETS_DIR   = SCRIPT_DIR / "assets" / "newsletter_images"
TMP_IMG_DIR  = SCRIPT_DIR / ".tmp" / "newsletter_images"
TMP_IMG_DIR.mkdir(parents=True, exist_ok=True)

REPO_RAW = "https://raw.githubusercontent.com/bayshawn2001gmailcom/the-fight-docket/main"
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
    # Selected by the date in the filename, never mtime — see issue_selector.py.
    # No age limit here: this is build tooling and is legitimately re-run on
    # older issues to regenerate their images.
    _, path = latest_issue(SCRIPT_DIR, max_age_days=None)
    return path


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


STYLE_SUFFIX = (" Photorealistic live sports photojournalism, real venue, natural grain, sharp focus,"
                " brand accent colors black #0A0A0A, red #C8102E and gold #C9A84C."
                " No identifiable real person's face, no rendered text, no logos or trademarks.")

def load_weekly_prompts(issue_date):
    """Per-issue prompts written by newsletter_generator.py — in context with each section
    (intro, main_story, fight_previews, business_intel). These take priority over the
    generic SECTION_PROMPTS so every image matches this week's actual articles."""
    pf = SCRIPT_DIR / "prompts" / "weekly_prompts.json"
    if not pf.exists():
        return {}
    try:
        data = json.loads(pf.read_text(encoding="utf-8"))
        if data.get("issue_date") != issue_date:
            print(f"  weekly_prompts.json is for {data.get('issue_date')}, not {issue_date} — ignoring")
            return {}
        return {p["section"]: p["prompt"].rstrip(".") + "." + STYLE_SUFFIX
                for p in data.get("prompts", []) if p.get("section") and p.get("prompt")}
    except Exception as e:
        print(f"  Could not load weekly_prompts.json: {e}")
        return {}


def generate_missing_images(issue_date, existing_sections):
    # Story-specific prompts only. The generic SECTION_PROMPTS fallback produced
    # images that did not match their section, so it is no longer used.
    prompts = load_weekly_prompts(issue_date)
    if not prompts:
        print("  No weekly_prompts.json for this issue - write prompts first.")
        return
    needed = [s for s in prompts if s not in existing_sections]
    if not needed:
        print("  All section images already exist — skipping generation.")
        return

    for section in needed:
        prompt = prompts[section]
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
# Web copies
# ------------------------------------------------------------------ #

WEB_WIDTH   = 1200   # 2x the 600px display width, for retina
WEB_QUALITY = 82

def compress_for_web(src: Path) -> Path:
    """Raw Nano Banana 2 output is ~3MB at 2752px; the newsletter shows it at 600px.
    Seven uncompressed images is ~21MB and Beehiiv/email clients silently drop them.
    Always upload the derivative, never the original. The full-size file stays in
    assets/ as the archive copy."""
    from PIL import Image
    dst = TMP_IMG_DIR / f"{src.stem}_web.jpg"
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if w > WEB_WIDTH:
        im = im.resize((WEB_WIDTH, round(h * WEB_WIDTH / w)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=WEB_QUALITY, optimize=True, progressive=True)
    print(f"    compressed {src.stat().st_size//1024}KB -> {dst.stat().st_size//1024}KB")
    return dst



# ------------------------------------------------------------------ #
# HTML injection
# ------------------------------------------------------------------ #

SECTION_MARKERS = {
    "This Week in 60 Seconds": "intro",
    "Business Intel":     "business",
    "Fight Schedule":     "schedule",
    "Sources and Further Reading": "sources",
    "The Number":         "spotlight",
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
    "BUSINESS INTEL":     "business_intel",
    "Fighter Spotlight":  "fighter_spotlight",
    "FIGHTER SPOTLIGHT":  "fighter_spotlight",
}

# The red underline div that appears after each section label
RED_DIVIDER = re.compile(r'style="width:40px; height:3px; background:#(?:DE1E20|C8102E); margin-bottom:22px;"')

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
            # Match the label ONLY where it is an actual section header, i.e.
            # inside the letter-spacing:4px label <p>. Plain html.find(label)
            # also matched body prose (an Editor's Note that says "Business
            # Intel below" stole the Main Story slot), so anchor the match.
            m = re.search(
                r"letter-spacing:4px;[^>]*>\s*" + re.escape(label) + r"[^<]*</p>",
                html,
            )
            if not m:
                continue
            label_idx = m.end()

            # Find the red divider div that comes after this label
            dm = RED_DIVIDER.search(html, label_idx)
            if not dm:
                continue
            divider_idx = dm.start()

            # Insert AFTER the divider's closing </div>, never inside it —
            # the divider is 40px wide x 3px tall, an img inside renders 40px wide
            div_close = html.find('</div>', divider_idx)
            if div_close == -1:
                continue

            insert_pos = div_close + len('</div>')

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

    # Step 2: Compress web copies into .tmp/newsletter_images/ (tracked in git) and
    # point every image at the repo. ImgBB links died, so the repo is the only host.
    print("\n[2/4] Building web copies (1200px) and repo URLs...")
    url_map = {}
    for f in sorted(ASSETS_DIR.glob(f"nb2_{issue_date}_*.jpg")):
        section = f.stem.replace(f"nb2_{issue_date}_", "")
        web = compress_for_web(f)
        url_map[section] = f"{REPO_RAW}/.tmp/newsletter_images/{web.name}"
    print("  Commit and push assets/ and .tmp/newsletter_images/ before Muse builds the draft.")

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

    # Copy FINAL newsletter HTML to clipboard — user pastes straight into
    # Beehiiv's <> HTML source editor. Never put inject.js here (user directive).
    copy_to_clipboard(html)

    inject_js_path = SCRIPT_DIR / newsletter_path.name.replace(".html", ".inject.js")
    print("\n" + "=" * 55)
    print("  DONE")
    print(f"  HTML       : {newsletter_path.name} (images injected)")
    print(f"  Inject JS  : {inject_js_path.name if inject_js_path.exists() else 'N/A'} (fallback only)")
    print(f"  Thumbnail  : .tmp/newsletter_images/nb2_{issue_date}_thumbnail.jpg")
    print(f"  Clipboard  : final newsletter HTML — paste into Beehiiv <> editor")
    print("=" * 55)


if __name__ == "__main__":
    main()
