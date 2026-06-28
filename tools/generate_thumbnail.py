#!/usr/bin/env python3
"""
The Fight Docket — Thumbnail Generator
Generates a single newsletter thumbnail image based on draft context.
Uploads to ImgBB and updates asset_urls_*.json.

Run:
    python tools/generate_thumbnail.py            (latest draft)
    python tools/generate_thumbnail.py 2026-05-08 (specific date)
"""
import os, sys, json, time, base64, requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
IMGBB_API_KEY  = os.getenv("IMGBB_API_KEY", "")
TMP_DIR        = ROOT / ".tmp"
OUTPUT_DIR     = TMP_DIR / "newsletter_images"

IMAGE_MODELS = [
    "gemini-2.5-flash-image",
    "gemini-2.0-flash-preview-image-generation",
]


def build_thumbnail_prompt(draft: dict) -> str:
    headline  = draft.get("main_story_headline", "")
    spotlight = draft.get("fighter_spotlight_name", "")
    preview   = draft.get("fight_previews_headline", "")

    # Build context-specific prompt from newsletter content
    context_parts = []
    if "Netflix" in headline or "streaming" in headline.lower():
        context_parts.append("boxing streaming broadcast deal, dramatic arena with glowing screens")
    if "Mayweather" in headline or "Pacquiao" in headline:
        context_parts.append("two legendary boxing champions, pre-fight intensity")
    if "UFC" in str(draft.get("fight_previews_html", "")):
        context_parts.append("MMA octagon, championship fight atmosphere")
    if spotlight:
        context_parts.append(f"elite combat sports athlete, championship energy")

    context = ", ".join(context_parts) if context_parts else "elite combat sports, championship atmosphere"

    return (
        f"Premium sports editorial thumbnail: {context}. "
        "Cinematic wide banner composition, dramatic arena spotlight lighting from above, "
        "black background (#0D0D0D), deep crimson red (#DE1E20) and gold (#C5A059) color palette, "
        "dark editorial atmosphere, premium sports magazine cover style, "
        "high contrast, moody. No faces clearly visible, no text, no logos, no watermarks."
    )


def generate_image(prompt: str) -> tuple[bytes | None, str]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="16:9"),
    )

    for model in IMAGE_MODELS:
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=model, contents=[prompt], config=config,
                )
                for part in response.parts:
                    if part.inline_data is not None:
                        return part.inline_data.data, part.inline_data.mime_type
                print(f"    {model}: no image returned, trying next...")
                break
            except Exception as e:
                msg = str(e)
                if "not found" in msg.lower() or "404" in msg:
                    print(f"    {model}: unavailable, trying next...")
                    break
                if "503" in msg or "429" in msg or "UNAVAILABLE" in msg:
                    wait = 20 * attempt
                    print(f"    {model} attempt {attempt}/3 — retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"    {model} error: {msg[:120]}")
                    break
    return None, ""


def upload_to_imgbb(image_bytes: bytes, name: str) -> str:
    if not IMGBB_API_KEY:
        print("  No IMGBB_API_KEY — skipping upload")
        return ""
    b64 = base64.b64encode(image_bytes).decode()
    r = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "name": name, "image": b64},
        timeout=30,
    )
    if r.status_code == 200:
        return r.json()["data"]["url"]
    print(f"  ImgBB upload failed: {r.status_code} {r.text[:100]}")
    return ""


def main():
    date_iso = sys.argv[1] if len(sys.argv) > 1 else None

    # Find the draft file
    if date_iso:
        draft_path = TMP_DIR / f"newsletter_draft_{date_iso}.json"
    else:
        files = sorted(TMP_DIR.glob("newsletter_draft_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            raise SystemExit("No newsletter_draft_*.json found. Run tools/newsletter_draft.py first.")
        draft_path = files[0]

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    issue_date = draft.get("issue_date", draft_path.stem.replace("newsletter_draft_", ""))

    print("=" * 60)
    print("  The Fight Docket -- Thumbnail Generator")
    print(f"  Issue: {issue_date}")
    print("=" * 60)

    prompt = build_thumbnail_prompt(draft)
    print(f"\n  Prompt: {prompt[:120]}...")
    print("\n  Generating thumbnail...")

    image_bytes, mime_type = generate_image(prompt)

    if not image_bytes:
        raise SystemExit("Image generation failed.")

    ext      = "jpg" if mime_type and "jpeg" in mime_type else "png"
    filename = f"nb2_{issue_date}_thumbnail.{ext}"
    out_path = OUTPUT_DIR / filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(image_bytes)
    print(f"  Saved: {filename} ({len(image_bytes) / 1024:.0f} KB)")

    print("\n  Uploading to ImgBB...")
    url = upload_to_imgbb(image_bytes, filename.replace(f".{ext}", ""))

    if url:
        print(f"  URL: {url}")

        # Update asset_urls JSON
        asset_file = TMP_DIR / f"asset_urls_{issue_date}.json"
        if asset_file.exists():
            urls = json.loads(asset_file.read_text(encoding="utf-8"))
        else:
            urls = {}
        urls["thumbnail"] = url
        asset_file.write_text(json.dumps(urls, indent=2), encoding="utf-8")
        print(f"  Updated: {asset_file.name}")
    else:
        print(f"  Local only: {out_path}")

    print("\n" + "=" * 60)
    print("  DONE")
    if url:
        print(f"\n  Thumbnail URL (paste into Beehiiv post settings):")
        print(f"  {url}")
    print("=" * 60)


if __name__ == "__main__":
    main()
