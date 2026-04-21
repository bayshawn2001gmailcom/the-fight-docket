#!/usr/bin/env python3
"""
nano_banana_gen.py — Generate images using Nano Banana 2 (Gemini 3.1 Flash Image Preview).

Usage:
    python nano_banana_gen.py "A dramatic UFC fighter silhouette backlit by arena lights"

Optional flags:
    --aspect-ratio  One of: 1:1 (default), 16:9, 9:16, 4:3, 3:4, 3:2, 2:3, 4:5, 5:4, 21:9
    --resolution    One of: 512, 1K (default), 2K, 4K
    --image-only    Request only an image response (no accompanying text)

Requirements:
    pip install google-genai pillow

Environment:
    GEMINI_API_KEY — your Google Gemini API key
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "assets" / "newsletter_images"

VALID_ASPECT_RATIOS = {
    "1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3",
    "4:5", "5:4", "8:1", "9:16", "16:9", "21:9",
}
VALID_RESOLUTIONS = {"512", "1K", "2K", "4K"}


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("  export GEMINI_API_KEY=your_key_here", file=sys.stderr)
        sys.exit(1)
    return key


def generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
    image_only: bool = False,
) -> bytes:
    """Call Nano Banana 2 and return raw image bytes."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Error: google-genai package is not installed.", file=sys.stderr)
        print("  pip install google-genai", file=sys.stderr)
        sys.exit(1)

    client = genai.Client()

    modalities = ["IMAGE"] if image_only else ["TEXT", "IMAGE"]

    config = types.GenerateContentConfig(
        response_modalities=modalities,
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=resolution,
        ),
    )

    print(f"  Model         : gemini-3.1-flash-image-preview (Nano Banana 2)")
    print(f"  Aspect ratio  : {aspect_ratio}  |  Resolution: {resolution}")
    print(f"  Prompt        : {prompt}")
    print("  Sending request to Gemini API...")

    import time
    retries = 5
    backoff = 15.0
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=[prompt],
                config=config,
            )
            for part in response.parts:
                if part.thought:
                    continue
                if part.inline_data is not None:
                    return part.inline_data.data, part.inline_data.mime_type
                if part.text:
                    print(f"  Model note    : {part.text.strip()}")
            print("Error: No image was returned in the response.", file=sys.stderr)
            sys.exit(1)

        except Exception as e:
            last_error = e
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "EXHAUSTED" in msg:
                wait = backoff * attempt
                print(f"\n  Attempt {attempt}/{retries} busy, retrying in {wait:.0f}s...", end="", flush=True)
                time.sleep(wait)
            else:
                print(f"\nError: {e}", file=sys.stderr)
                sys.exit(1)

    print(f"\nError: Failed after {retries} attempts: {last_error}", file=sys.stderr)
    sys.exit(1)


def save_image(image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg") -> Path:
    """Save image bytes to the output directory with a timestamped filename."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ext = "jpg" if "jpeg" in mime_type else "png"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = "_".join(prompt.lower().split()[:5])
    slug = "".join(c if c.isalnum() or c == "_" else "" for c in slug)
    filename = f"nb2_{timestamp}_{slug}.{ext}"
    output_path = OUTPUT_DIR / filename

    output_path.write_bytes(image_bytes)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate images with Nano Banana 2 (Gemini 3.1 Flash Image Preview)."
    )
    parser.add_argument("prompt", help="The image generation prompt.")
    parser.add_argument(
        "--aspect-ratio",
        default="1:1",
        choices=sorted(VALID_ASPECT_RATIOS),
        metavar="RATIO",
        help="Output aspect ratio (default: 1:1). Choices: " + ", ".join(sorted(VALID_ASPECT_RATIOS)),
    )
    parser.add_argument(
        "--resolution",
        default="1K",
        choices=sorted(VALID_RESOLUTIONS),
        metavar="RES",
        help="Output resolution (default: 1K). Choices: 512, 1K, 2K, 4K",
    )
    parser.add_argument(
        "--image-only",
        action="store_true",
        help="Request only the image without accompanying text.",
    )
    args = parser.parse_args()

    get_api_key()  # Validate key exists before doing anything

    print("\n  Nano Banana 2 Image Generator")
    print("-" * 44)

    image_bytes, mime_type = generate_image(
        args.prompt,
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
        image_only=args.image_only,
    )
    output_path = save_image(image_bytes, args.prompt, mime_type)

    print(f"  Saved         : {output_path}")
    print(f"  Size          : {len(image_bytes) / 1024:.1f} KB")
    print("-" * 44 + "\n")


if __name__ == "__main__":
    main()
