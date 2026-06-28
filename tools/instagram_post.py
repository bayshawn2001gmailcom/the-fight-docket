#!/usr/bin/env python3
"""
The Fight Docket — Instagram Graph API Poster (WAT Framework)
Posts branded IG cards from .tmp/ig/ to @thefightdocket via the official
Instagram Graph API. No browser automation — no bot risk.

Usage:
  python tools/instagram_post.py --card=preview
  python tools/instagram_post.py --card=result
  python tools/instagram_post.py --card=announcement
  python tools/instagram_post.py --card=quote
  python tools/instagram_post.py --card=preview --dry-run

Card → posting day:
  preview      Monday   (newsletter launch)
  result       Tuesday  (fight recap)
  announcement Thursday (upcoming fight)
  quote        Saturday (quote card)

Required .env keys:
  INSTAGRAM_ACCOUNT_ID   — numeric IG Business account ID
  INSTAGRAM_PAGE_TOKEN   — long-lived Page access token (valid 60 days)

Setup (one-time, free):
  1. Go to developers.facebook.com → create an App (type: Business)
  2. Add Instagram Graph API product
  3. Link your Instagram Business account to your Facebook Page
  4. Get a long-lived token: run tools/refresh_tokens.py --setup
  5. Add INSTAGRAM_ACCOUNT_ID + INSTAGRAM_PAGE_TOKEN to .env

Token refresh:
  Long-lived tokens expire in 60 days. Run tools/refresh_tokens.py weekly
  or set up Task Scheduler to run it every Monday (it's a no-op if > 14 days remain).
"""
import os, sys, io, json, glob as _glob, time, argparse
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
INSTAGRAM_PAGE_TOKEN = os.getenv("INSTAGRAM_PAGE_TOKEN", "")
IMGBB_API_KEY        = os.getenv("IMGBB_API_KEY", "")

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
    """Find the most recent card PNG for the given type."""
    pattern = CARD_PATTERNS[card_type]
    matches = sorted(IG_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    if not matches:
        raise SystemExit(
            f"No {card_type} card found in .tmp/ig/\n"
            "Run tools/ig_graphics.py first."
        )
    return matches[0]


def _find_caption(card_type: str) -> str:
    """Extract caption for the given card type from the most recent captions file."""
    caption_files = sorted(IG_DIR.glob("*_captions.txt"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not caption_files:
        return ""

    text = caption_files[0].read_text(encoding="utf-8")
    section_header = f"--- {CAPTION_SECTIONS[card_type]} ---"

    start = text.find(section_header)
    if start == -1:
        return ""

    # Find the next section boundary
    next_section = text.find("---", start + len(section_header))
    if next_section == -1:
        block = text[start + len(section_header):]
    else:
        block = text[start + len(section_header):next_section]

    # Strip the section header and surrounding whitespace
    return block.strip()


def _upload_image_to_imgbb(image_path: Path) -> str:
    """Upload a local PNG to ImgBB and return a public URL."""
    if not IMGBB_API_KEY:
        raise SystemExit(
            "IMGBB_API_KEY not set. Instagram Graph API requires a public image URL.\n"
            "Add IMGBB_API_KEY to .env — ImgBB free tier is sufficient."
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


def _create_media_container(image_url: str, caption: str) -> str:
    """Step 1 of Graph API: create a media container. Returns container ID."""
    endpoint = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        "image_url": image_url,
        "caption":   caption,
        "access_token": INSTAGRAM_PAGE_TOKEN,
    }
    resp = requests.post(endpoint, data=payload, timeout=30)
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"Graph API media container error: {data['error']}")

    container_id = data.get("id")
    if not container_id:
        raise RuntimeError(f"No container ID returned: {data}")

    print(f"  Container created: {container_id}")
    return container_id


def _wait_for_container(container_id: str, max_wait: int = 60) -> None:
    """Poll until the container status is FINISHED (image processed by Meta)."""
    endpoint = f"{GRAPH_BASE}/{container_id}"
    for attempt in range(max_wait // 5):
        resp = requests.get(
            endpoint,
            params={"fields": "status_code", "access_token": INSTAGRAM_PAGE_TOKEN},
            timeout=15,
        )
        status = resp.json().get("status_code", "")
        if status == "FINISHED":
            print(f"  Container ready (attempt {attempt + 1})")
            return
        if status == "ERROR":
            raise RuntimeError(f"Container processing failed: {resp.json()}")
        time.sleep(5)
    raise RuntimeError(f"Container not ready after {max_wait}s — try again later")


def _publish_container(container_id: str) -> str:
    """Step 2 of Graph API: publish the container. Returns the post ID."""
    endpoint = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    payload = {
        "creation_id":  container_id,
        "access_token": INSTAGRAM_PAGE_TOKEN,
    }
    resp = requests.post(endpoint, data=payload, timeout=30)
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"Graph API publish error: {data['error']}")

    post_id = data.get("id")
    if not post_id:
        raise RuntimeError(f"No post ID returned: {data}")

    return post_id


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Post an IG card via Instagram Graph API")
    parser.add_argument("--card", required=True, choices=list(CARD_PATTERNS.keys()),
                        help="Which card to post: preview|result|announcement|quote")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be posted without actually posting")
    args = parser.parse_args()

    print("=" * 55)
    print("  The Fight Docket — Instagram Poster")
    print(f"  Card: {args.card}  |  Date: {date.today().isoformat()}")
    if args.dry_run:
        print("  MODE: DRY RUN — nothing will be posted")
    print("=" * 55)

    if not args.dry_run:
        if not INSTAGRAM_ACCOUNT_ID:
            raise SystemExit("Missing INSTAGRAM_ACCOUNT_ID in .env")
        if not INSTAGRAM_PAGE_TOKEN:
            raise SystemExit("Missing INSTAGRAM_PAGE_TOKEN in .env")

    print(f"\n[1/4] Finding {args.card} card...")
    card_path = _find_card(args.card)
    print(f"  Found: {card_path.name}")

    print(f"\n[2/4] Loading caption...")
    caption = _find_caption(args.card)
    if caption:
        print(f"  Caption ({len(caption)} chars):")
        print(f"  {caption[:120]}{'...' if len(caption) > 120 else ''}")
    else:
        print("  No caption file found — will post without caption")

    if args.dry_run:
        print(f"\n[DRY RUN] Would upload: {card_path}")
        print(f"[DRY RUN] Would post caption:\n{caption}")
        print("\n  Dry run complete — no post made.")
        return

    print(f"\n[3/4] Uploading image to ImgBB for public URL...")
    image_url = _upload_image_to_imgbb(card_path)

    print(f"\n[4/4] Posting to Instagram...")
    container_id = _create_media_container(image_url, caption)
    print(f"  Waiting for Meta to process image...")
    _wait_for_container(container_id)
    post_id = _publish_container(container_id)

    print("\n" + "=" * 55)
    print(f"  POSTED — Instagram post ID: {post_id}")
    print(f"  Card: {args.card}  |  {card_path.name}")
    print("=" * 55)


if __name__ == "__main__":
    main()
