#!/usr/bin/env python3
"""
One-shot script: update Beehiiv post thumbnails for the Apr 27 and May 4 issues.
Run AFTER the images are committed and pushed to GitHub.

Usage: python fix_thumbnails.py
"""
import os, json, sys
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

API_KEY        = os.getenv("BEEHIIV_API_KEY", "")
PUBLICATION_ID = os.getenv("BEEHIIV_PUBLICATION_ID", "")
BASE_URL       = "https://api.beehiiv.com/v2"
HEADERS        = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
REPO           = "bayshawn2001gmailcom/the-fight-docket"

if not API_KEY or not PUBLICATION_ID:
    raise SystemExit("Missing BEEHIIV_API_KEY or BEEHIIV_PUBLICATION_ID")

# Filenames of the two generated thumbnails
APR27_IMG = "nb2_20260504_025846_stack_of_legal_documents_and.jpg"
MAY4_IMG  = "nb2_20260504_030315_boxing_championship_belt_gleaming_under.jpg"

# Subject keyword fragments to identify the posts (case-insensitive)
APR27_KEYWORD = "two fronts"
MAY4_KEYWORD  = "monster"


def raw_url(filename: str) -> str:
    return f"https://raw.githubusercontent.com/{REPO}/main/assets/newsletter_images/{filename}"


def list_posts():
    url = f"{BASE_URL}/publications/{PUBLICATION_ID}/posts"
    params = {"limit": 20}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if not resp.ok:
        raise SystemExit(f"List posts failed {resp.status_code}: {resp.text[:300]}")
    return resp.json().get("data", [])


def find_post(posts, keyword):
    for p in posts:
        if keyword.lower() in p.get("subject", "").lower():
            return p
    return None


def patch_thumbnail(post_id: str, thumbnail_url: str, label: str):
    url = f"{BASE_URL}/publications/{PUBLICATION_ID}/posts/{post_id}"
    resp = requests.patch(url, json={"thumbnail_url": thumbnail_url}, headers=HEADERS, timeout=30)
    if resp.ok:
        print(f"  OK   {label}")
        print(f"       → {thumbnail_url}")
    else:
        print(f"  FAIL {label}: {resp.status_code} {resp.text[:200]}")


def main():
    # Verify images exist locally
    img_dir = Path(__file__).parent / "assets" / "newsletter_images"
    for fname in [APR27_IMG, MAY4_IMG]:
        if not (img_dir / fname).exists():
            raise SystemExit(f"Image not found: {fname}\nRun nano_banana_gen.py first.")

    print("Fetching Beehiiv posts...")
    posts = list_posts()
    print(f"Found {len(posts)} posts:")
    for p in posts:
        print(f"  [{p.get('id','?')}] {p.get('subject','')[:70]}")

    apr27 = find_post(posts, APR27_KEYWORD)
    may4  = find_post(posts, MAY4_KEYWORD)

    if not apr27:
        raise SystemExit(f"Could not find Apr 27 post (keyword: '{APR27_KEYWORD}'). Check subject line.")
    if not may4:
        raise SystemExit(f"Could not find May 4 post (keyword: '{MAY4_KEYWORD}'). Check subject line.")

    print(f"\nMatched:")
    print(f"  Apr 27 → [{apr27['id']}] {apr27.get('subject','')[:60]}")
    print(f"  May 4  → [{may4['id']}]  {may4.get('subject','')[:60]}")

    print("\nPatching thumbnails...")
    patch_thumbnail(apr27["id"], raw_url(APR27_IMG), "Apr 27 — Fight Game on Two Fronts")
    patch_thumbnail(may4["id"],  raw_url(MAY4_IMG),  "May 4  — The Monster Made It")

    print("\nDone. Thumbnails updated in Beehiiv.")


if __name__ == "__main__":
    main()
