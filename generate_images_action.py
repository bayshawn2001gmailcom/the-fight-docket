#!/usr/bin/env python3
"""
generate_images_action.py — Run by GitHub Actions to generate newsletter images.
Reads prompts/weekly_prompts.json, calls Nano Banana 2 (Gemini), saves to assets/newsletter_images/.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

PROMPTS_FILE = Path("prompts/weekly_prompts.json")
OUTPUT_DIR = Path("assets/newsletter_images")


def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("ERROR: GEMINI_API_KEY secret not set in GitHub Actions.")
        sys.exit(1)
    return key


def generate_image(prompt, api_key, aspect_ratio="16:9", resolution="2K"):
    from google import genai
    from google.genai import types
    import time

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=resolution,
        ),
    )

    retries = 5
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=[prompt],
                config=config,
            )
            for part in response.parts:
                if part.inline_data is not None:
                    return part.inline_data.data, part.inline_data.mime_type
        except Exception as e:
            msg = str(e)
            if "503" in msg or "429" in msg or "UNAVAILABLE" in msg:
                wait = 15 * attempt
                print(f"  Attempt {attempt}/{retries} — busy, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Error: {e}")
                return None, None
    return None, None


def main():
    api_key = get_api_key()

    if not PROMPTS_FILE.exists():
        print(f"ERROR: {PROMPTS_FILE} not found. Skipping image generation.")
        sys.exit(0)

    with open(PROMPTS_FILE) as f:
        data = json.load(f)

    issue_date = data.get("issue_date", datetime.now().strftime("%Y-%m-%d"))
    prompts = data.get("prompts", [])

    if not prompts:
        print("No prompts found in weekly_prompts.json. Nothing to generate.")
        sys.exit(0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n  Fight Docket — Nano Banana 2 via GitHub Actions")
    print(f"  Issue: {issue_date} | {len(prompts)} images to generate")
    print("=" * 55)

    generated = []
    for i, item in enumerate(prompts, 1):
        section = item.get("section", f"section_{i}")
        prompt = item.get("prompt", "")
        topic = item.get("topic", "")

        if not prompt:
            print(f"  [{i}/{len(prompts)}] {section} — no prompt, skipping")
            continue

        print(f"\n  [{i}/{len(prompts)}] {section}: {topic}")
        print(f"  Prompt: {prompt[:80]}...")

        image_bytes, mime_type = generate_image(prompt, api_key)

        if image_bytes:
            ext = "jpg" if mime_type and "jpeg" in mime_type else "png"
            filename = f"nb2_{issue_date}_{section}.{ext}"
            output_path = OUTPUT_DIR / filename
            output_path.write_bytes(image_bytes)
            print(f"  Saved: {filename} ({len(image_bytes) / 1024:.1f} KB)")
            generated.append({
                "section": section,
                "file": filename,
                "url": f"https://raw.githubusercontent.com/{{GITHUB_REPOSITORY}}/main/assets/newsletter_images/{filename}"
            })
        else:
            print(f"  FAILED to generate image for {section}")

    print(f"\n  Done. {len(generated)}/{len(prompts)} images generated.")
    print("=" * 55)

    # Write a summary of generated image URLs for reference
    summary_path = Path("prompts/last_generated_images.json")
    with open(summary_path, "w") as f:
        json.dump({"issue_date": issue_date, "images": generated}, f, indent=2)
    print(f"  Image URLs saved to {summary_path}")


if __name__ == "__main__":
    main()
