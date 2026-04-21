#!/usr/bin/env python3
"""
generate_newsletter_images.py

Full automation pipeline for The Fight Docket:
  1. Parse the newsletter .md file into its 6 named sections
  2. Call Gemini (text) to write a Visual Bible-compliant prompt per section
  3. Generate 4K 16:9 images via Nano Banana 2 (gemini-3.1-flash-image-preview)
  4. Save to assets/newsletter_images/fight-docket-img-{section}.jpg
  5. Optionally patch the newsletter HTML to replace remote img URLs with local paths

Usage:
    python generate_newsletter_images.py fight-docket-2026-04-13.md
    python generate_newsletter_images.py fight-docket-2026-04-13.md --html Fight_Docket_April_14_2026.html
    python generate_newsletter_images.py fight-docket-2026-04-13.md --html Fight_Docket_April_14_2026.html --skip-existing

Requirements:
    pip install google-genai

Environment:
    GEMINI_API_KEY
"""

import os
import sys
import re
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).parent / "assets" / "newsletter_images"

# Maps MD section header keywords -> output filename slug (order matters)
SECTION_MAP = [
    (r"\[INTRO",           "intro"),
    (r"\[MAIN STORY\]",    "main_story"),
    (r"\[FIGHT CARD",      "fight_cards"),
    (r"\[BUSINESS INTEL\]","business_intel"),
    (r"\[FIGHTER WATCH\]", "fighter_watch"),
    (r"\[THE TAKE\]",      "the_take"),
]

# Maps HTML section comment keywords -> slug (for img-tag patching)
HTML_SECTION_MAP = [
    ("INTRO",           "intro"),
    ("MAIN STORY",      "main_story"),
    ("FIGHT CARD",      "fight_cards"),
    ("BUSINESS INTEL",  "business_intel"),
    ("FIGHTER WATCH",   "fighter_watch"),
    ("THE TAKE",        "the_take"),
]

# ---------------------------------------------------------------------------
# Visual Bible system prompt (fed to the text model as system instruction)
# ---------------------------------------------------------------------------

VISUAL_BIBLE_SYSTEM_PROMPT = """\
You are the image director for The Fight Docket, a premium combat sports newsletter.

Your job: write ONE image generation prompt for the provided newsletter section.

STYLE RULES (non-negotiable):
- Editorial sports photojournalism. Reference standard: HBO 24/7 documentaries, Ring Magazine, ESPN The Magazine.
- 35mm film grain, shallow depth of field, cinematic lighting.
- High-contrast — deep blacks, sharp highlights, no flat or even lighting.
- Motivated light sources: arena spotlights, locker-room bulbs, single overhead lamp, press conference flash.
- Desaturated, muted tones: blacks, charcoal, slate gray, aged canvas tan.
- Accent colors sparingly: deep red (blood/corner), cold blue (arena fill), gold (championship context only).
- NEVER: neon, oversaturated gradients, vibrant "AI art" color palettes, purple skies, glowing energy effects.

SUBJECT RULES (context lock — subject must directly match the article):
- Fight result story          -> ring canvas, corner stool with towel, octagon fence at low angle, referee's glove, gloves resting on canvas
- Boxing fight / callout      -> ring ropes with corner stools, empty press conference table, microphone stand in arena, championship belt on a table (no wearer)
- Fighter pay / contract      -> boxing gloves resting on a stack of legal documents, pen on a contract on a mahogany desk, briefcase placed near a heavy bag
- Fight card previews         -> empty octagon from above at night, arena seats and ceiling rigging, walkout tunnel, weigh-in scale under a spotlight
- Fighter profile             -> hand wraps close-up on a fist, heavy bag in a dimly lit gym, focus mitts mid-drill (no face), sweat-soaked gym gear
- Opinion / editorial         -> empty press conference podium, single spotlight on an empty chair, microphone stand in front of dark seats

HARD EXCLUSIONS — any of these disqualify the image:
- Faces or fighter likenesses (show gloves, gear, torsos, backs, feet, objects, environments — never faces)
- Logos or brand marks (UFC, Netflix, Matchroom, Paramount+, ESPN, Queensberry, etc.)
- Text, numbers, or watermarks rendered inside the image
- Cartoons, illustrations, 3D renders, or CGI aesthetics
- Stock-photo aesthetics (clean studio backgrounds, posed smiles, bright even lighting)

MANDATORY SUFFIX — always append this exact phrase at the end of every prompt:
"Editorial sports photography style, gritty, high contrast, 35mm film grain, shallow depth of field, desaturated tones, no faces, no logos, no text in image"

Output ONLY the final prompt. No explanation, no preamble, no surrounding quotes.\
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("  Set it with: set GEMINI_API_KEY=your_key_here  (Windows)", file=sys.stderr)
        sys.exit(1)
    return key


def parse_sections(md_text: str) -> dict:
    """Split newsletter markdown into named sections based on ## [SECTION] headers."""
    sections = {}
    lines = md_text.splitlines()
    current_slug = None
    current_lines = []

    for line in lines:
        matched = False
        for pattern, slug in SECTION_MAP:
            if line.startswith("##") and re.search(pattern, line, re.IGNORECASE):
                if current_slug:
                    sections[current_slug] = "\n".join(current_lines).strip()
                current_slug = slug
                current_lines = [line]
                matched = True
                break
        if not matched and current_slug:
            current_lines.append(line)

    if current_slug:
        sections[current_slug] = "\n".join(current_lines).strip()

    return sections


def generate_prompt(client, slug: str, section_text: str) -> str:
    """Call Gemini text model to write a Visual Bible-compliant image prompt.
    Retries on 429/503 with backoff."""
    import time
    from google.genai import types

    label = slug.upper().replace("_", " ")
    excerpt = section_text[:1500]

    user_message = (
        f"Newsletter section: {label}\n\n"
        f"Content:\n{excerpt}\n\n"
        f"Write the image prompt for this section."
    )

    config = types.GenerateContentConfig(
        system_instruction=VISUAL_BIBLE_SYSTEM_PROMPT,
    )

    retries = 5
    backoff = 15.0
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[user_message],
                config=config,
            )
            return response.text.strip()
        except Exception as e:
            last_error = e
            msg = str(e)
            if "429" in msg or "503" in msg or "UNAVAILABLE" in msg or "EXHAUSTED" in msg:
                wait = backoff * attempt
                print(f"\n  Prompt attempt {attempt}/{retries} rate-limited, retrying in {wait:.0f}s...", end="", flush=True)
                time.sleep(wait)
            else:
                raise

    raise RuntimeError(f"Prompt generation failed after {retries} attempts: {last_error}")


def generate_image(client, prompt: str, resolution: str = "2K") -> tuple:
    """Generate a 16:9 image via Nano Banana 2. Returns (bytes, mime_type).
    Defaults to 2K. Retries up to 4 times on 503/429 with backoff."""
    import time
    from google.genai import types

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size=resolution,
        ),
    )

    retries = 4
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
            raise RuntimeError("No image data returned from Nano Banana 2")

        except Exception as e:
            last_error = e
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "quota" in msg.lower():
                wait = backoff * attempt
                print(f"\n  Attempt {attempt}/{retries} busy, retrying in {wait:.0f}s...", end="", flush=True)
                time.sleep(wait)
            else:
                raise

    raise RuntimeError(f"Failed after {retries} attempts: {last_error}")


def patch_html(html_path: Path, slug_to_imgpath: dict) -> None:
    """
    Replace every <img src="..."> inside each section block with the local path.
    Sections are identified by the HTML comment markers already in the template.
    """
    html = html_path.read_text(encoding="utf-8")

    for keyword, slug in HTML_SECTION_MAP:
        if slug not in slug_to_imgpath:
            continue
        local_src = slug_to_imgpath[slug]

        # Match the section comment, any whitespace/newlines, then the img tag
        pattern = (
            r"(<!--\s*={3,}\s*"
            + re.escape(keyword)
            + r"[\s\S]*?={3,}\s*-->[\s\S]*?)"
            r'(<img\s[^>]*src=")[^"]*(")'
        )
        replacement = rf"\g<1>\g<2>{local_src}\g<3>"
        new_html = re.sub(pattern, replacement, html, count=1, flags=re.IGNORECASE)

        if new_html != html:
            html = new_html
            print(f"  Patched [{slug}] -> {local_src}")
        else:
            print(f"  WARNING: no img tag found for section [{slug}] in HTML")

    html_path.write_text(html, encoding="utf-8")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate newsletter images via Nano Banana 2 (Gemini 3.1 Flash Image Preview)."
    )
    parser.add_argument(
        "md_file",
        help="Newsletter markdown file, e.g. fight-docket-2026-04-13.md",
    )
    parser.add_argument(
        "--html",
        metavar="HTML_FILE",
        help="Newsletter HTML file to patch with local image paths.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip sections whose output image already exists.",
    )
    parser.add_argument(
        "--resolution",
        default="2K",
        choices=["512", "1K", "2K", "4K"],
        help="Image resolution (default: 2K). Use 4K when API demand is low.",
    )
    parser.add_argument(
        "--prompts-only",
        action="store_true",
        help="Print generated prompts without calling the image API.",
    )
    args = parser.parse_args()

    get_api_key()

    # Resolve markdown file
    md_path = Path(args.md_file)
    if not md_path.exists():
        md_path = Path(__file__).parent / args.md_file
    if not md_path.exists():
        print(f"Error: cannot find '{args.md_file}'", file=sys.stderr)
        sys.exit(1)

    md_text = md_path.read_text(encoding="utf-8")
    sections = parse_sections(md_text)

    if not sections:
        print(
            "Error: No sections found. Verify the markdown uses ## [SECTION NAME] headers.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\n  The Fight Docket — Automated Image Generator")
    print(f"  Model : gemini-3.1-flash-image-preview (Nano Banana 2) | {args.resolution} 16:9")
    print(f"  Issue : {md_path.name}")
    print(f"  Sections : {', '.join(sections.keys())}")
    print("-" * 54)

    from google import genai
    client = genai.Client()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    slug_to_imgpath = {}
    generated = 0
    skipped = 0
    failed = 0

    for slug, content in sections.items():
        label = slug.upper().replace("_", " ")
        print(f"\n[{label}]")

        # Check for existing file (either .jpg or .png)
        existing = next(
            (OUTPUT_DIR / f"fight-docket-img-{slug}{ext}" for ext in (".jpg", ".png")
             if (OUTPUT_DIR / f"fight-docket-img-{slug}{ext}").exists()),
            None,
        )

        if args.skip_existing and existing:
            print(f"  Skipping — exists: {existing.name}")
            slug_to_imgpath[slug] = f"assets/newsletter_images/{existing.name}"
            skipped += 1
            continue

        # Step 1 — generate prompt
        print("  Generating prompt ... ", end="", flush=True)
        try:
            prompt = generate_prompt(client, slug, content)
            print("ok")
        except Exception as e:
            print(f"FAILED\n  Error: {e}", file=sys.stderr)
            failed += 1
            continue

        print(f"  Prompt  : {prompt[:110]}...")

        import time
        time.sleep(3)  # brief gap before image call

        if args.prompts_only:
            print(f"  (--prompts-only: skipping image generation)")
            continue

        # Step 2 — generate image
        print("  Generating image ... ", end="", flush=True)
        try:
            image_bytes, mime_type = generate_image(client, prompt, resolution=args.resolution)
        except Exception as e:
            print(f"FAILED\n  Error: {e}", file=sys.stderr)
            failed += 1
            continue

        ext = "jpg" if "jpeg" in mime_type else "png"
        out_path = OUTPUT_DIR / f"fight-docket-img-{slug}.{ext}"
        out_path.write_bytes(image_bytes)
        size_kb = len(image_bytes) / 1024
        print(f"ok ({size_kb:.0f} KB)")
        print(f"  Saved   : {out_path}")

        slug_to_imgpath[slug] = f"assets/newsletter_images/{out_path.name}"
        generated += 1

        # Brief pause between sections to avoid bursting the API
        import time
        time.sleep(5)

    # Summary
    print("\n" + "-" * 54)
    print(f"  Generated : {generated}   Skipped : {skipped}   Failed : {failed}")

    # Patch HTML
    if args.html and slug_to_imgpath:
        html_path = Path(args.html)
        if not html_path.exists():
            html_path = Path(__file__).parent / args.html
        if html_path.exists():
            print(f"\n  Patching HTML: {html_path.name}")
            patch_html(html_path, slug_to_imgpath)
            print(f"  HTML updated.")
        else:
            print(f"  WARNING: HTML file not found: {args.html}", file=sys.stderr)

    print("\n  Done.\n")


if __name__ == "__main__":
    main()
