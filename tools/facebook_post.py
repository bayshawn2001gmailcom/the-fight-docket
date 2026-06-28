#!/usr/bin/env python3
"""
The Fight Docket — Facebook Graph API Poster (WAT Framework)
Posts branded IG cards from .tmp/ig/ to the Fight Docket Facebook Page.
Uses the same Facebook App credentials as instagram_post.py.

Usage:
  python tools/facebook_post.py --card=preview
  python tools/facebook_post.py --card=result
  python tools/facebook_post.py --card=announcement
  python tools/facebook_post.py --card=quote
  python tools/facebook_post.py --card=preview --dry-run

Required .env keys:
  FACEBOOK_PAGE_ID      — numeric Facebook Page ID
  FACEBOOK_PAGE_TOKEN   — long-lived Page access token (same Facebook App)

The Facebook Page ID for The Fight Docket is the number from:
  facebook.com/profile.php?id=61567987746089  →  61567987746089

To get a long-lived Page token, run: python tools/refresh_tokens.py --setup
"""
import os, sys, io, json, argparse
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

FACEBOOK_PAGE_ID    = os.getenv("FACEBOOK_PAGE_ID", "61567987746089")
FACEBOOK_PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_TOKEN", "")
IMGBB_API_KEY       = os.getenv("IMGBB_API_KEY", "")

GRAPH_BASE = "https://graph.facebook.com/v21.0"

TMP_DIR = ROOT / ".tmp"
IG_DIR  = TMP_DIR / "ig"

CARD_PATTERNS = {
    "preview":      "*_newsletter_preview.png",
    "result":       "*_result.png",
    "announcement": "*_announcement.png",
    "quote":        "*_quote_card.png",
}

CAPTION_SECTIONS = {
    "preview":      "MONDAY: Newsletter Preview",
    "result":       "TUESDAY: Fight Result",
    "announcement": "THURSDAY: Fight Announcement",
    "quote":        "SATURDAY: Quote Card",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_card(card_type: str) -> Path:
    pattern = CARD_PATTERNS[card_type]
    matches = sorted(IG_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    if not matches:
        raise SystemExit(
            f"No {card_type} card found in .tmp/ig/\n"
            "Run tools/ig_graphics.py first."
        )
    return matches[0]


def _find_caption(card_type: str) -> str:
    caption_files = sorted(IG_DIR.glob("*_captions.txt"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not caption_files:
        return ""

    text = caption_files[0].read_text(encoding="utf-8")
    section_header = f"--- {CAPTION_SECTIONS[card_type]} ---"

    start = text.find(section_header)
    if start == -1:
        return ""

    next_section = text.find("---", start + len(section_header))
    if next_section == -1:
        block = text[start + len(section_header):]
    else:
        block = text[start + len(section_header):next_section]

    return block.strip()


def _upload_image_to_imgbb(image_path: Path) -> str:
    if not IMGBB_API_KEY:
        raise SystemExit(
            "IMGBB_API_KEY not set. Facebook Graph API photo posts require a public URL.\n"
            "Add IMGBB_API_KEY to .env."
        )
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API_KEY},
            files={"image": f},
            timeout=30,
        )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"ImgBB upload failed: {data}")
    url = data["data"]["url"]
    print(f"  Uploaded to ImgBB: {url}")
    return url


def _post_photo(image_url: str, caption: str) -> str:
    """Post a photo to the Facebook Page feed. Returns the post ID."""
    endpoint = f"{GRAPH_BASE}/{FACEBOOK_PAGE_ID}/photos"
    payload = {
        "url":          image_url,
        "caption":      caption,
        "access_token": FACEBOOK_PAGE_TOKEN,
    }
    resp = requests.post(endpoint, data=payload, timeout=30)
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"Graph API photo post error: {data['error']}")

    post_id = data.get("post_id") or data.get("id")
    if not post_id:
        raise RuntimeError(f"No post ID returned: {data}")

    return post_id


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Post an IG card to the Facebook Page")
    parser.add_argument("--card", required=True, choices=list(CARD_PATTERNS.keys()),
                        help="Which card to post: preview|result|announcement|quote")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be posted without actually posting")
    args = parser.parse_args()

    print("=" * 55)
    print("  The Fight Docket — Facebook Poster")
    print(f"  Card: {args.card}  |  Date: {date.today().isoformat()}")
    if args.dry_run:
        print("  MODE: DRY RUN — nothing will be posted")
    print("=" * 55)

    if not args.dry_run and not FACEBOOK_PAGE_TOKEN:
        raise SystemExit("Missing FACEBOOK_PAGE_TOKEN in .env")

    print(f"\n[1/3] Finding {args.card} card...")
    card_path = _find_card(args.card)
    print(f"  Found: {card_path.name}")

    print(f"\n[2/3] Loading caption...")
    caption = _find_caption(args.card)
    if caption:
        print(f"  Caption ({len(caption)} chars): {caption[:100]}...")
    else:
        print("  No caption found — will post without caption")

    if args.dry_run:
        print(f"\n[DRY RUN] Would upload: {card_path}")
        print(f"[DRY RUN] Would post caption:\n{caption}")
        print("\n  Dry run complete — no post made.")
        return

    print(f"\n[3/3] Posting to Facebook Page {FACEBOOK_PAGE_ID}...")
    image_url = _upload_image_to_imgbb(card_path)
    post_id = _post_photo(image_url, caption)

    print("\n" + "=" * 55)
    print(f"  POSTED — Facebook post ID: {post_id}")
    print(f"  Card: {args.card}  |  {card_path.name}")
    print(f"  Page: https://www.facebook.com/profile.php?id={FACEBOOK_PAGE_ID}")
    print("=" * 55)


if __name__ == "__main__":
    main()
