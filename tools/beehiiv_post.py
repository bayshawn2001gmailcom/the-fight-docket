#!/usr/bin/env python3
"""
The Fight Docket — Beehiiv Post Tool (WAT Framework)
Reads newsletter_YYYY-MM-DD.html, creates a Beehiiv post via API v2,
schedules for Monday noon EDT.

Retry logic: if .tmp/post_status.json shows a previous failed attempt,
uses that newsletter and sends immediately.

Run: python tools/beehiiv_post.py
     python tools/beehiiv_post.py --draft-only   (create draft, don't schedule)
"""
import os, sys, json
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv
import requests

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

API_KEY        = os.getenv("BEEHIIV_API_KEY", "")
PUBLICATION_ID = os.getenv("BEEHIIV_PUBLICATION_ID", "")
IMGBB_API_KEY  = os.getenv("IMGBB_API_KEY", "")

for k, v in [("BEEHIIV_API_KEY", API_KEY), ("BEEHIIV_PUBLICATION_ID", PUBLICATION_ID)]:
    if not v:
        raise SystemExit(f"Missing {k}")

TMP_DIR     = ROOT / ".tmp"
BASE_URL    = "https://api.beehiiv.com/v2"
HEADERS     = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
STATUS_FILE = TMP_DIR / "post_status.json"


# ---------------------------------------------------------------------------
# Post status tracking
# ---------------------------------------------------------------------------

def load_post_status() -> dict:
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_post_status(data: dict):
    STATUS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Load newsletter
# ---------------------------------------------------------------------------

def load_newsletter(status: dict, is_retry: bool) -> tuple[str, str]:
    if is_retry and status.get("newsletter_file"):
        candidate = ROOT / status["newsletter_file"]
        if candidate.exists():
            print(f"  Retrying: {candidate.name}")
            return candidate.name, candidate.read_text(encoding="utf-8")

    files = sorted(ROOT.glob("newsletter_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit("No newsletter_*.html found. Run tools/html_renderer.py first.")
    latest = files[0]
    print(f"  Newsletter: {latest.name}")
    return latest.name, latest.read_text(encoding="utf-8")


def load_ig_data() -> dict:
    ig_files = sorted(TMP_DIR.glob("weekly_ig_data_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if ig_files:
        return json.loads(ig_files[0].read_text(encoding="utf-8"))
    return {}


def upload_to_imgbb(image_path: Path) -> str:
    if not IMGBB_API_KEY:
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
            print(f"  Thumbnail: {url[:70]}...")
            return url
        print(f"  Thumbnail upload failed {resp.status_code}")
    except Exception as e:
        print(f"  Thumbnail error: {e}")
    return ""


def load_thumbnail_url() -> str:
    # Try asset_urls first (Nano Banana images)
    asset_files = sorted(TMP_DIR.glob("asset_urls_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if asset_files:
        urls = json.loads(asset_files[0].read_text(encoding="utf-8"))
        first_url = next(iter(urls.values()), "")
        if first_url:
            return first_url

    # Fall back: upload the first local image
    images_dir = TMP_DIR / "newsletter_images"
    if images_dir.exists():
        images = sorted(images_dir.glob("nb2_*.jpg")) + sorted(images_dir.glob("nb2_*.png"))
        if images:
            return upload_to_imgbb(images[0])
    return ""


def build_subject(ig_data: dict, newsletter_name: str) -> str:
    stories = ig_data.get("preview_stories", [])
    if stories:
        return f"The Fight Docket | {stories[0][:60]}"
    date_str = newsletter_name.replace("newsletter_", "").replace(".html", "")
    return f"The Fight Docket | {date_str}"


def build_preview_text(ig_data: dict) -> str:
    stories = ig_data.get("preview_stories", [])
    if len(stories) >= 2:
        return stories[1][:80]
    return "Combat sports business intelligence — this week's biggest stories."


# ---------------------------------------------------------------------------
# Schedule helpers
# ---------------------------------------------------------------------------

def send_time_edt(send_immediately: bool) -> int:
    edt = timezone(timedelta(hours=-4))
    now = datetime.now(edt)
    if send_immediately:
        return int((now + timedelta(minutes=5)).timestamp())
    noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    return int(noon.timestamp()) if noon > now else int((now + timedelta(minutes=5)).timestamp())


# ---------------------------------------------------------------------------
# Beehiiv API
# ---------------------------------------------------------------------------

def create_post(subject: str, preview_text: str, html_content: str, thumbnail_url: str) -> dict:
    url  = f"{BASE_URL}/publications/{PUBLICATION_ID}/posts"
    payload = {
        "title":        subject,
        "subject":      subject,
        "preview_text": preview_text,
        "content_type": "html",
        "content":      html_content,
        "status":       "draft",
        "audience":     "all",
    }
    if thumbnail_url:
        payload["thumbnail_url"] = thumbnail_url

    print(f"  Creating: '{subject}'")
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=30)
    if resp.status_code == 403:
        err = resp.json().get("errors", [{}])[0].get("message", "")
        if "enterprise" in err.lower():
            raise PermissionError("enterprise_required")
    if not resp.ok:
        raise SystemExit(f"Beehiiv API error {resp.status_code}: {resp.text[:300]}")
    return resp.json().get("data", {})


def schedule_post(post_id: str, send_at: int) -> bool:
    url = f"{BASE_URL}/publications/{PUBLICATION_ID}/posts/{post_id}"
    payload = {"status": "confirmed", "send_at": send_at}
    print(f"  Scheduling for {datetime.fromtimestamp(send_at, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    resp = requests.patch(url, json=payload, headers=HEADERS, timeout=30)
    if not resp.ok:
        print(f"  Warning: scheduling failed {resp.status_code} — post left as draft")
        return False
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    draft_only = "--draft-only" in sys.argv

    print("=" * 60)
    print("  The Fight Docket — Beehiiv Post Tool")
    print("=" * 60)

    status   = load_post_status()
    is_retry = not status.get("posted", True) and bool(status.get("newsletter_file"))
    if is_retry:
        print("\n  [RETRY] Previous post not confirmed — sending immediately")

    print("\n[1/3] Loading newsletter...")
    name, html   = load_newsletter(status, is_retry)
    ig_data      = load_ig_data()
    thumbnail    = load_thumbnail_url()
    subject      = build_subject(ig_data, name)
    preview_text = build_preview_text(ig_data)
    send_at      = send_time_edt(send_immediately=is_retry or draft_only)

    print(f"  Subject  : {subject}")
    print(f"  Preview  : {preview_text[:60]}...")

    save_post_status({"posted": False, "newsletter_file": name,
                      "attempted_at": datetime.now(timezone.utc).isoformat()})

    print("\n[2/3] Creating post in Beehiiv...")
    try:
        post    = create_post(subject, preview_text, html, thumbnail)
    except PermissionError:
        print("  API requires enterprise plan — falling back to browser automation...")
        import subprocess, sys as _sys
        browser_args = [_sys.executable, str(ROOT / "tools" / "beehiiv_browser_post.py")]
        if draft_only:
            browser_args.append("--draft-only")
        result = subprocess.run(browser_args, cwd=str(ROOT))
        raise SystemExit(result.returncode)
    post_id = post.get("id", "")
    if not post_id:
        raise SystemExit(f"No post ID returned: {post}")
    print(f"  Post ID  : {post_id}")

    if draft_only:
        save_post_status({"posted": False, "newsletter_file": name, "post_id": post_id,
                          "posted_at": datetime.now(timezone.utc).isoformat()})
        print("\n[3/3] Skipped scheduling (--draft-only mode)")
        print(f"\n  DONE — Draft created: https://app.beehiiv.com/posts/{post_id}")
        return

    print("\n[3/3] Scheduling...")
    scheduled = schedule_post(post_id, send_at)

    save_post_status({"posted": True, "newsletter_file": name, "post_id": post_id,
                      "posted_at": datetime.now(timezone.utc).isoformat()})

    print("\n" + "=" * 60)
    label = "immediately (retry)" if is_retry else "Monday noon EDT"
    print(f"  DONE — {'Scheduled' if scheduled else 'Draft (schedule manually)'} ({label})")
    print(f"  View: https://app.beehiiv.com/posts/{post_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
