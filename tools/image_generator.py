#!/usr/bin/env python3
"""
The Fight Docket — Image Generator (WAT Framework)
Reads .tmp/weekly_prompts_YYYY-MM-DD.json, generates all 7 section images
via Nano Banana (best available Gemini image generation model).

Tries models in order of capability:
  1. gemini-2.0-flash-preview-image-generation  (newer, check availability)
  2. gemini-3.1-flash-image-preview             (proven, current stable)

Output: .tmp/newsletter_images/nb2_YYYY-MM-DD_section.jpg

Run: python tools/image_generator.py
     python tools/image_generator.py 2026-05-12   (specific date)
"""
import os, sys, json, time
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise SystemExit("Missing GEMINI_API_KEY")

TMP_DIR    = ROOT / ".tmp"
OUTPUT_DIR = TMP_DIR / "newsletter_images"

# Try the newest model first; fall back to proven stable model
IMAGE_MODELS = [
    "gemini-2.0-flash-preview-image-generation",
    "gemini-3.1-flash-image-preview",
]


def generate_image(prompt: str, api_key: str, aspect_ratio: str = "16:9", resolution: str = "2K") -> tuple[bytes | None, str]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=resolution,
        ),
    )

    for model in IMAGE_MODELS:
        for attempt in range(1, 6):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[prompt],
                    config=config,
                )
                for part in response.parts:
                    if part.inline_data is not None:
                        return part.inline_data.data, part.inline_data.mime_type
                # Model responded but no image — try next model
                print(f"    {model}: no image in response, trying next model...")
                break
            except Exception as e:
                msg = str(e)
                if "not found" in msg.lower() or "404" in msg:
                    print(f"    {model}: not available, trying next...")
                    break
                if "503" in msg or "429" in msg or "UNAVAILABLE" in msg:
                    wait = 15 * attempt
                    print(f"    {model} attempt {attempt}/5 — retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"    {model} error: {msg[:100]}")
                    break

    return None, ""


def find_prompts_file(date_iso: str | None) -> Path:
    if date_iso:
        path = TMP_DIR / f"weekly_prompts_{date_iso}.json"
        if path.exists():
            return path
        raise SystemExit(f"Prompts file not found: {path}")
    files = sorted(TMP_DIR.glob("weekly_prompts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit("No weekly_prompts_*.json found. Run tools/newsletter_draft.py first.")
    return files[0]


def main():
    date_iso = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

    prompts_file = find_prompts_file(date_iso)
    data = json.loads(prompts_file.read_text(encoding="utf-8"))

    issue_date = data.get("issue_date", date_iso)
    prompts    = data.get("prompts", [])

    if not prompts:
        raise SystemExit("No prompts found in prompts file.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"  The Fight Docket — Nano Banana Image Generator")
    print(f"  Issue: {issue_date} | {len(prompts)} images")
    print("=" * 60)

    # Section aspect ratios
    aspect_map = {
        "thumbnail": "16:9",  # wide cover image for Beehiiv post + webpage
        "rumor":     "1:1",
        "legal":     "16:9",
    }

    generated = []
    for i, item in enumerate(prompts, 1):
        section = item.get("section", f"section_{i}")
        prompt  = item.get("prompt", "")
        topic   = item.get("topic", "")

        if not prompt:
            print(f"\n  [{i}/{len(prompts)}] {section} — no prompt, skipping")
            continue

        # Skip if any variant (jpg/png) already exists for this section
        existing = list(OUTPUT_DIR.glob(f"nb2_{issue_date}_{section}.*"))
        if existing:
            print(f"\n  [{i}/{len(prompts)}] {section} — already exists, skipping ({existing[0].name})")
            generated.append({"section": section, "file": existing[0].name})
            continue

        aspect = aspect_map.get(section, "16:9")
        print(f"\n  [{i}/{len(prompts)}] {section}: {topic[:60]}")
        print(f"  Prompt: {prompt[:80]}...")

        image_bytes, mime_type = generate_image(prompt, GEMINI_API_KEY, aspect_ratio=aspect, resolution="2K")

        if image_bytes:
            ext      = "jpg" if mime_type and "jpeg" in mime_type else "png"
            filename = f"nb2_{issue_date}_{section}.{ext}"
            out_path = OUTPUT_DIR / filename
            out_path.write_bytes(image_bytes)
            print(f"  Saved: {filename} ({len(image_bytes) / 1024:.0f} KB)")
            generated.append({"section": section, "file": filename})
        else:
            print(f"  FAILED to generate image for {section}")

    # Write summary
    summary = TMP_DIR / f"last_generated_images_{issue_date}.json"
    summary.write_text(json.dumps({"issue_date": issue_date, "images": generated}, indent=2), encoding="utf-8")

    print(f"\n  Done: {len(generated)}/{len(prompts)} images generated")
    print(f"  Summary: {summary.name}")
    print("\n  DONE — Next step: run tools/asset_uploader.py")


if __name__ == "__main__":
    main()
