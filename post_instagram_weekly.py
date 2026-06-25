#!/usr/bin/env python3
"""
The Fight Docket — Weekly Instagram + Facebook Card Poster
Posts one of the 4 weekly branded cards via the official Graph API.

Usage:
    python post_instagram_weekly.py --card preview|result|announcement|quote
    python post_instagram_weekly.py --card preview --platform instagram
    python post_instagram_weekly.py --card preview --dry-run

Runs from GitHub Actions on Mon/Tue/Thu/Sat.
Token refresh required every 60 days — see INSTAGRAM_TOKEN_ISSUED_AT in .env.
"""
import argparse, base64, glob, json, os, re, sys, time
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

def _tok(key):
    """Get env var and strip surrounding quotes/whitespace that .env editors add."""
    v = os.getenv(key, "").strip().strip("'\"")
    return v

INSTAGRAM_ACCOUNT_ID = _tok("INSTAGRAM_ACCOUNT_ID")
INSTAGRAM_PAGE_TOKEN = _tok("INSTAGRAM_PAGE_TOKEN")
FACEBOOK_PAGE_ID     = _tok("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_TOKEN  = _tok("FACEBOOK_PAGE_TOKEN")
IMGBB_API_KEY        = os.getenv("IMGBB_API_KEY", "")

CARD_PATTERNS = {
    "preview":      "*_newsletter_preview.png",
    "result":       "*_result.png",
    "announcement": "*_announcement.png",
    "quote":        "*_quote.png",
}

DAY_HEADERS = {
    "preview":      "MONDAY",
    "result":       "TUESDAY",
    "announcement": "THURSDAY",
    "quote":        "SATURDAY",
}

SCRIPT_DIR = Path(__file__).parent
IG_CONTENT  = SCRIPT_DIR / "instagram_content"


def load_manifest() -> dict:
    """Read current_week.json written by ig_content_generator.py."""
    manifest_file = IG_CONTENT / "current_week.json"
    if manifest_file.exists():
        return json.loads(manifest_file.read_text(encoding="utf-8"))
    return {}


def find_latest_image(card: str) -> Path:
    # Prefer manifest — mtime sort is unreliable on GitHub Actions (all files same timestamp)
    manifest = load_manifest()
    if manifest.get(card):
        p = IG_CONTENT / manifest[card]
        if p.exists():
            print(f"  (via manifest: issue {manifest.get('issue', '?')})")
            return p

    # Fallback: mtime sort (works locally where files have real timestamps)
    pattern = str(IG_CONTENT / CARD_PATTERNS[card])
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not files:
        raise SystemExit(f"No image found for card='{card}' in {IG_CONTENT}/")
    return Path(files[0])


def parse_caption(card: str) -> str:
    # Prefer manifest for captions file too
    manifest = load_manifest()
    caps_name = manifest.get("captions")
    if caps_name:
        caps_path = IG_CONTENT / caps_name
        if caps_path.exists():
            text = caps_path.read_text(encoding="utf-8")
            day  = DAY_HEADERS[card]
            pattern = rf"---\s+{day}:.*?---\n(.*?)(?=\n---\s+[A-Z]+:|\Z)"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

    # Fallback: mtime sort across all captions files
    caps = sorted(IG_CONTENT.glob("*_captions.txt"), key=os.path.getmtime, reverse=True)
    if not caps:
        raise SystemExit(f"No captions file found in {IG_CONTENT}/")

    text = caps[0].read_text(encoding="utf-8")
    day  = DAY_HEADERS[card]
    pattern = rf"---\s+{day}:.*?---\n(.*?)(?=\n---\s+[A-Z]+:|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise SystemExit(f"No caption section for {day} in {caps[0].name}")

    return match.group(1).strip()


def upload_imgbb(img_path: Path) -> str:
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    r = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "image": b64, "expiration": 0},
        timeout=30,
    )
    r.raise_for_status()
    url = r.json()["data"]["url"]
    if not url:
        raise SystemExit("ImgBB upload returned empty URL")
    return url


def post_instagram(img_url: str, caption: str) -> bool:
    ig = INSTAGRAM_ACCOUNT_ID
    tok = INSTAGRAM_PAGE_TOKEN

    # Step 1: Create media container
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{ig}/media",
        data={"image_url": img_url, "caption": caption, "access_token": tok},
        timeout=30,
    )
    cid = r.json().get("id")
    if not cid:
        print(f"  IG container error: {r.json()}")
        return False

    # Step 2: Poll until container is FINISHED (Instagram processes the image async)
    for attempt in range(12):
        time.sleep(5)
        status = requests.get(
            f"https://graph.facebook.com/v19.0/{cid}",
            params={"fields": "status_code", "access_token": tok},
            timeout=15,
        ).json().get("status_code", "")
        print(f"  IG container status: {status} (attempt {attempt + 1})")
        if status == "FINISHED":
            break
        if status == "ERROR":
            print("  IG container processing failed")
            return False
    else:
        print("  IG container timed out — never reached FINISHED")
        return False

    # Step 3: Publish
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{ig}/media_publish",
        data={"creation_id": cid, "access_token": tok},
        timeout=30,
    )
    ok = "id" in r.json()
    if not ok:
        print(f"  IG publish error: {r.json()}")
    return ok


def post_facebook(img_url: str, caption: str) -> bool:
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos",
        data={"url": img_url, "message": caption, "access_token": FACEBOOK_PAGE_TOKEN},
        timeout=30,
    )
    ok = "id" in r.json()
    if not ok:
        print(f"  FB post error: {r.json()}")
    return ok


def check_credentials(platform: str) -> None:
    needed = {"IMGBB_API_KEY": IMGBB_API_KEY}
    if platform in ("instagram", "both"):
        needed["INSTAGRAM_ACCOUNT_ID"] = INSTAGRAM_ACCOUNT_ID
        needed["INSTAGRAM_PAGE_TOKEN"] = INSTAGRAM_PAGE_TOKEN
    if platform in ("facebook", "both"):
        needed["FACEBOOK_PAGE_ID"] = FACEBOOK_PAGE_ID
        needed["FACEBOOK_PAGE_TOKEN"] = FACEBOOK_PAGE_TOKEN
    missing = [k for k, v in needed.items() if not v]
    if missing:
        raise SystemExit(f"Missing env vars: {', '.join(missing)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--card", required=True, choices=["preview", "result", "announcement", "quote"])
    parser.add_argument("--platform", default="both", choices=["instagram", "facebook", "both"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"\n  Fight Docket — IG/FB Weekly Post ({args.card})")
    print(f"  Platform: {args.platform}")

    check_credentials(args.platform)

    print(f"\n[1/4] Finding {args.card} image...")
    img_path = find_latest_image(args.card)
    print(f"  {img_path.name}")

    print("[2/4] Parsing caption...")
    caption = parse_caption(args.card)
    print(f"  {caption[:80]}...")

    if args.dry_run:
        print("\n  [DRY RUN] — would post:")
        print(f"  Image : {img_path}")
        print(f"  Caption:\n{caption}")
        return

    print("[3/4] Uploading image to ImgBB...")
    img_url = upload_imgbb(img_path)
    print(f"  {img_url}")

    print("[4/4] Posting...")
    ig_ok = fb_ok = False

    if args.platform in ("instagram", "both"):
        ig_ok = post_instagram(img_url, caption)
        print(f"  Instagram: {'OK ✓' if ig_ok else 'FAILED ✗'}")

    if args.platform in ("facebook", "both"):
        fb_ok = post_facebook(img_url, caption)
        print(f"  Facebook:  {'OK ✓' if fb_ok else 'FAILED ✗'}")

    any_ok = ig_ok or fb_ok
    print(f"\n  {'Done.' if any_ok else 'All platforms failed.'}")
    sys.exit(0 if any_ok else 1)


if __name__ == "__main__":
    main()
