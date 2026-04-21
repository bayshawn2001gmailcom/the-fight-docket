#!/usr/bin/env python3
"""
flux_gen.py — Generate images using FLUX.1-schnell via OpenRouter.

Usage:
    python flux_gen.py "A dramatic UFC fighter silhouette backlit by arena lights"

Requirements:
    pip install requests pillow

Environment:
    OPENROUTER_API_KEY — your OpenRouter API key
"""

import os
import sys
import base64
import argparse
import requests
from datetime import datetime
from pathlib import Path


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/images/generations"
MODEL = "black-forest-labs/flux-schnell"
OUTPUT_DIR = Path(__file__).parent / "assets" / "newsletter_images"


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.", file=sys.stderr)
        print("  export OPENROUTER_API_KEY=your_key_here", file=sys.stderr)
        sys.exit(1)
    return key


def generate_image(prompt: str, api_key: str) -> bytes:
    """Send prompt to OpenRouter and return raw image bytes."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://thefightdocket.com",
        "X-Title": "The Fight Docket Newsletter",
    }

    payload = {
    "model": MODEL,
    "prompt": prompt,  # Image models on OpenRouter often use a flat prompt field
    "width": 1024,
    "height": 1024,
    "steps": 4,        # Schnell is optimized for 4 steps
    "n": 1
}
    print(f"  Model   : {MODEL}")
    print(f"  Prompt  : {prompt}")
    print("  Sending request to OpenRouter...")

    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=120)

    if response.status_code != 200:
        print(f"Error: OpenRouter returned HTTP {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        sys.exit(1)

    data = response.json()

    # OpenRouter image models return a URL or base64 data in the content field
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        print(f"Error: Unexpected response structure: {data}", file=sys.stderr)
        sys.exit(1)

    # Handle base64-encoded image data (data URI)
    if isinstance(content, str) and content.startswith("data:image"):
        _, b64data = content.split(",", 1)
        return base64.b64decode(b64data)

    # Handle list of content blocks (multimodal response)
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "image_url":
                    img_url = block["image_url"]["url"]
                    if img_url.startswith("data:image"):
                        _, b64data = img_url.split(",", 1)
                        return base64.b64decode(b64data)
                    else:
                        print(f"  Downloading image from URL: {img_url}")
                        img_response = requests.get(img_url, timeout=60)
                        img_response.raise_for_status()
                        return img_response.content

    # Handle plain URL string
    if isinstance(content, str) and content.startswith("http"):
        print(f"  Downloading image from URL: {content}")
        img_response = requests.get(content, timeout=60)
        img_response.raise_for_status()
        return img_response.content

    print(f"Error: Could not extract image from response content:\n{content}", file=sys.stderr)
    sys.exit(1)


def save_image(image_bytes: bytes, prompt: str) -> Path:
    """Save image bytes to the output directory with a timestamped filename."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Create a short slug from the prompt for readability
    slug = "_".join(prompt.lower().split()[:5])
    slug = "".join(c if c.isalnum() or c == "_" else "" for c in slug)
    filename = f"{timestamp}_{slug}.png"
    output_path = OUTPUT_DIR / filename

    output_path.write_bytes(image_bytes)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate images with FLUX.1-schnell via OpenRouter."
    )
    parser.add_argument("prompt", help="The image generation prompt.")
    args = parser.parse_args()

    api_key = get_api_key()

    print("\n🖼  FLUX Image Generator")
    print("─" * 40)

    image_bytes = generate_image(args.prompt, api_key)
    output_path = save_image(image_bytes, args.prompt)

    print(f"  ✓ Saved : {output_path}")
    print(f"  Size    : {len(image_bytes) / 1024:.1f} KB")
    print("─" * 40 + "\n")


if __name__ == "__main__":
    main()
