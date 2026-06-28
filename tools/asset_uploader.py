#!/usr/bin/env python3
"""
The Fight Docket — Asset Uploader (WAT Framework)
Uploads all PNGs/JPGs in .tmp/newsletter_images/ to ImgBB.
Returns a section→URL map saved as .tmp/asset_urls_YYYY-MM-DD.json.

Run: python tools/asset_uploader.py
     python tools/asset_uploader.py 2026-05-12   (specific date)
"""
import os, json, sys
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
import requests

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")
TMP_DIR       = ROOT / ".tmp"


def upload_to_imgbb(image_path: Path) -> str:
    """Upload one image file to ImgBB. Returns direct URL or empty string on failure."""
    if not IMGBB_API_KEY:
        print("  Warning: IMGBB_API_KEY not set — skipping upload")
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
            print(f"    OK  {url[:72]}...")
            return url
        print(f"    FAIL {image_path.name}: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        print(f"    ERROR {image_path.name}: {e}")
    return ""


def main():
    date_iso = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

    images_dir = TMP_DIR / "newsletter_images"
    if not images_dir.exists():
        raise SystemExit(f"No images found at {images_dir}. Run tools/image_generator.py first.")

    # Find images for this issue date (nb2_YYYY-MM-DD_section.ext)
    images = sorted(images_dir.glob(f"nb2_{date_iso}_*.png")) + \
             sorted(images_dir.glob(f"nb2_{date_iso}_*.jpg"))

    if not images:
        # Fall back to any images in the directory
        images = sorted(images_dir.glob("nb2_*.png")) + sorted(images_dir.glob("nb2_*.jpg"))
        if not images:
            raise SystemExit(f"No nb2_*.png/jpg images found in {images_dir}")
        print(f"  Warning: no images for {date_iso}, uploading latest available")

    print("=" * 60)
    print(f"  The Fight Docket — Asset Uploader")
    print(f"  Uploading {len(images)} image(s) to ImgBB...")
    print("=" * 60)

    asset_urls: dict[str, str] = {}

    for img_path in images:
        # Extract section from filename: nb2_2026-05-12_main_story.jpg → main_story
        stem = img_path.stem  # e.g. nb2_2026-05-12_main_story
        parts = stem.split("_", 3)  # ['nb2', '2026', '05', '12_main_story'] or similar
        # More reliable: strip the date prefix
        section = stem.replace(f"nb2_{date_iso}_", "") or stem
        print(f"  Uploading {section} ({img_path.name})...")
        url = upload_to_imgbb(img_path)
        if url:
            asset_urls[section] = url

    out_path = TMP_DIR / f"asset_urls_{date_iso}.json"
    out_path.write_text(json.dumps(asset_urls, indent=2), encoding="utf-8")

    print(f"\n  Saved    : {out_path.name}")
    print(f"  Uploaded : {len(asset_urls)}/{len(images)} images")
    print("\n  DONE — Next step: run tools/html_renderer.py")


if __name__ == "__main__":
    main()
