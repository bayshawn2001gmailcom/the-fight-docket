#!/usr/bin/env python3
"""
Generate the 4 April 6, 2026 images for The Fight Docket newsletter.

Run from C:\The fight Docket\ :
    python gen_apr06_images.py

Requires:
    pip install google-genai pillow
"""

import os
import sys
import time
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "assets" / "newsletter_images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGES = [
    {
        "filename": "fight-docket-img-main_event_apr06.png",
        "section": "April 6 — Main Event (Queensberry $1B lawsuit)",
        "prompt": (
            "Photorealistic documentary photograph of a thick legal complaint document "
            "stamped FILED resting on a dark mahogany desk, a worn boxing glove placed "
            "beside it, brass desk lamp casting a hard circle of warm light, deep shadows "
            "at edges, desaturated warm tones, no recognizable text in focus, no logos "
            "no faces, Editorial sports photography style, gritty, high contrast"
        ),
    },
    {
        "filename": "fight-docket-img-undercard1_apr06.png",
        "section": "April 6 — Undercard 1 (Queensberry vs. Matchroom)",
        "prompt": (
            "Photorealistic editorial photograph of two empty boxing corner stools facing "
            "each other across a ring, neither occupied, arena lights above creating hard "
            "rim lighting on each stool, cold steel blue background, symmetric composition, "
            "empty ring canvas between them, no people no logos, tense and adversarial mood, "
            "Editorial sports photography style, gritty, high contrast"
        ),
    },
    {
        "filename": "fight-docket-img-undercard2_apr06.png",
        "section": "April 6 — Undercard 2 (UFC White House event)",
        "prompt": (
            "Photorealistic editorial photograph of a temporary boxing ring erected on an "
            "outdoor lawn at dusk, portable event spotlights casting hard shadows on empty "
            "canvas, neoclassical government building architecture silhouetted against deep "
            "blue twilight sky in background, desaturated cool tones, no people no faces, "
            "no logos no text, Editorial sports photography style, gritty, high contrast"
        ),
    },
    {
        "filename": "fight-docket-img-undercard3_apr06.png",
        "section": "April 6 — Undercard 3 (PFL debt clearance)",
        "prompt": (
            "Photorealistic documentary photograph of an open financial ledger with a heavy "
            "rubber stamp impression on the page, a pair of MMA gloves resting beside it on "
            "a clean corporate desk, cold overhead fluorescent office lighting casting hard "
            "downward shadows, desaturated blue-gray tones, shallow depth of field, no "
            "recognizable logos no faces no text in focus, Editorial sports photography "
            "style, gritty, high contrast"
        ),
    },
]


def generate_one(client, prompt, filename, retries=3):
    from google.genai import types

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K",
        ),
    )

    for attempt in range(1, retries + 1):
        print(f"    Attempt {attempt}/{retries}...")
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=[prompt],
                config=config,
            )
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data is not None:
                    data = part.inline_data.data
                    mime = part.inline_data.mime_type
                    # Determine extension from response
                    ext = "jpg" if "jpeg" in mime else "png"
                    # Save with correct final filename (force .png extension as specified)
                    out_path = OUTPUT_DIR / filename
                    out_path.write_bytes(data)
                    return str(out_path), len(data)
            print("    No image in response, retrying...")
        except Exception as e:
            err = str(e)
            print(f"    Error: {err}")
            if "503" in err or "overloaded" in err.lower():
                wait = 10 * attempt
                print(f"    503 — waiting {wait}s...")
                time.sleep(wait)
            elif attempt < retries:
                wait = 10 * attempt
                print(f"    Waiting {wait}s...")
                time.sleep(wait)
    return None, 0


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set in environment.")
        print("  Set it with:  set GEMINI_API_KEY=your_key_here  (Windows CMD)")
        print("  or:           $env:GEMINI_API_KEY='your_key_here'  (PowerShell)")
        sys.exit(1)

    try:
        from google import genai
    except ImportError:
        print("ERROR: google-genai not installed. Run:  pip install google-genai pillow")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("\nNano Banana 2 — April 6, 2026 Image Generation")
    print("=" * 55)

    results = []
    for img in IMAGES:
        out_path = OUTPUT_DIR / img["filename"]
        if out_path.exists() and out_path.stat().st_size > 1000:
            size_kb = out_path.stat().st_size // 1024
            print(f"\n[SKIP] {img['filename']}  ({size_kb}KB — already exists)")
            results.append(("skipped", img["filename"], size_kb))
            continue

        print(f"\n[GEN]  {img['section']}")
        print(f"       → {img['filename']}")
        saved_path, size = generate_one(client, img["prompt"], img["filename"])
        if saved_path:
            size_kb = size // 1024
            print(f"  ✓  Saved  ({size_kb}KB)")
            results.append(("ok", img["filename"], size_kb))
        else:
            print(f"  ✗  FAILED after all retries")
            results.append(("failed", img["filename"], 0))

    print("\n" + "=" * 55)
    print("Summary:")
    for status, name, size_kb in results:
        icon = "✓" if status in ("ok", "skipped") else "✗"
        note = f"({size_kb}KB)" if size_kb else "(FAILED)"
        print(f"  {icon}  {name}  {note}")

    print("\nFinal contents of assets/newsletter_images/:")
    for f in sorted(OUTPUT_DIR.iterdir()):
        if f.stat().st_size > 0:
            print(f"  {f.name}  ({f.stat().st_size // 1024}KB)")


if __name__ == "__main__":
    main()
