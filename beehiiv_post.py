#!/usr/bin/env python3
"""
The Fight Docket — Beehiiv Auto-Poster
Reads the latest newsletter HTML + prompts/weekly_ig_data.json,
creates a post via Beehiiv API v2, and schedules it for Monday noon EDT.

Retry logic: if prompts/post_status.json shows a previous failed attempt,
uses that newsletter and sends immediately instead of waiting for noon.

Run: python beehiiv_post.py
Or triggered by newsletter_pipeline.yml after newsletter_generator.py
"""
import os, sys, re, json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import requests

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

API_KEY        = os.getenv("BEEHIIV_API_KEY", "")
PUBLICATION_ID = os.getenv("BEEHIIV_PUBLICATION_ID", "")
IMGBB_API_KEY  = os.getenv("IMGBB_API_KEY", "")

for k, v in [("BEEHIIV_API_KEY", API_KEY), ("BEEHIIV_PUBLICATION_ID", PUBLICATION_ID)]:
    if not v:
        raise SystemExit(f"Missing {k}")

SCRIPT_DIR  = Path(__file__).parent
BASE_URL    = "https://api.beehiiv.com/v2"
HEADERS     = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
STATUS_FILE = SCRIPT_DIR / "prompts" / "post_status.json"


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
    STATUS_FILE.parent.mkdir(exist_ok=True)
    STATUS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Load newsletter content
# ---------------------------------------------------------------------------

def load_newsletter(status: dict, is_retry: bool) -> tuple:
    """Return (filename, html). On retry, use the previously unposted file."""
    if is_retry and status.get("newsletter_file"):
        candidate = SCRIPT_DIR / status["newsletter_file"]
        if candidate.exists():
            print(f"  Retrying unposted newsletter: {candidate.name}")
            return candidate.name, candidate.read_text(encoding="utf-8")
        print(f"  Retry file not found ({status['newsletter_file']}), finding latest...")

    files = sorted(SCRIPT_DIR.glob("newsletter_*.html"), reverse=True)
    if not files:
        raise SystemExit("No newsletter_*.html found. Run newsletter_generator.py first.")
    latest = files[0]
    print(f"  Newsletter: {latest.name}")
    return latest.name, latest.read_text(encoding="utf-8")


def load_ig_data() -> dict:
    ig_file = SCRIPT_DIR / "prompts" / "weekly_ig_data.json"
    if ig_file.exists():
        return json.loads(ig_file.read_text(encoding="utf-8"))
    return {}


def upload_to_imgbb(image_path: Path) -> str:
    """Upload image file to ImgBB and return the direct image URL."""
    if not IMGBB_API_KEY:
        print("  Warning: IMGBB_API_KEY not set — skipping thumbnail upload")
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
            print(f"  ImgBB upload OK: {url[:70]}...")
            return url
        print(f"  ImgBB upload failed {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        print(f"  ImgBB upload error: {e}")
    return ""


def load_thumbnail_url() -> str:
    """Upload the first generated image to ImgBB and return the hosted URL."""
    images_file = SCRIPT_DIR / "prompts" / "last_generated_images.json"
    if not images_file.exists():
        print("  No last_generated_images.json — no thumbnail")
        return ""
    try:
        data = json.loads(images_file.read_text(encoding="utf-8"))
        images = data.get("images", [])
        if images:
            filename = images[0].get("file", "")
            if filename:
                image_path = SCRIPT_DIR / "assets" / "newsletter_images" / filename
                if image_path.exists():
                    return upload_to_imgbb(image_path)
                print(f"  Image file not found locally: {filename}")
    except Exception as e:
        print(f"  load_thumbnail_url error: {e}")
    return ""


def build_subject(ig_data: dict, newsletter_name: str) -> str:
    stories = ig_data.get("preview_stories", [])
    if stories:
        lead = stories[0][:60]
        return f"The Fight Docket | {lead}"
    date_str = newsletter_name.replace("newsletter_", "").replace(".html", "")
    return f"The Fight Docket | {date_str}"


def build_preview_text(ig_data: dict) -> str:
    stories = ig_data.get("preview_stories", [])
    if len(stories) >= 2:
        return f"{stories[1][:80]}..." if len(stories[1]) > 80 else stories[1]
    return "Combat sports business intelligence — this week's biggest stories."


# ---------------------------------------------------------------------------
# Schedule: noon EDT normally; immediate (now + 5 min) on retry or if late
# ---------------------------------------------------------------------------

def send_time_edt(send_immediately: bool) -> int:
    edt = timezone(timedelta(hours=-4))
    now = datetime.now(edt)
    if send_immediately:
        return int((now + timedelta(minutes=5)).timestamp())
    noon_today = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if noon_today > now:
        return int(noon_today.timestamp())
    # Past noon on expected send day — fire in 5 minutes
    return int((now + timedelta(minutes=5)).timestamp())


# ---------------------------------------------------------------------------
# Beehiiv API calls
# ---------------------------------------------------------------------------

def create_post(subject: str, preview_text: str, html_content: str, thumbnail_url: str = "") -> dict:
    url = f"{BASE_URL}/publications/{PUBLICATION_ID}/posts"

    payload = {
        "subject":      subject,
        "preview_text": preview_text,
        "content_type": "html",
        "content":      html_content,
        "status":       "draft",
        "audience":     "all",
    }
    if thumbnail_url:
        payload["thumbnail_url"] = thumbnail_url

    print(f"  Creating post: '{subject}'")
    if thumbnail_url:
        print(f"  Thumbnail: {thumbnail_url[:80]}...")
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=30)

    if not resp.ok:
        raise SystemExit(f"Beehiiv API error {resp.status_code}: {resp.text[:300]}")

    return resp.json().get("data", {})


def schedule_post(post_id: str, send_at: int):
    url = f"{BASE_URL}/publications/{PUBLICATION_ID}/posts/{post_id}"

    payload = {
        "status":  "confirmed",
        "send_at": send_at,
    }

    print(f"  Scheduling post {post_id} at UTC {datetime.utcfromtimestamp(send_at).strftime('%Y-%m-%d %H:%M')}")
    resp = requests.patch(url, json=payload, headers=HEADERS, timeout=30)

    if not resp.ok:
        print(f"  Warning: scheduling failed {resp.status_code}: {resp.text[:200]}")
        print(f"  Post created as draft — schedule manually in Beehiiv.")
        return False

    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 55)
    print("  The Fight Docket — Beehiiv Auto-Poster")
    print("=" * 55)

    # Check for a previously failed/unposted newsletter
    status = load_post_status()
    is_retry = not status.get("posted", True) and bool(status.get("newsletter_file"))
    if is_retry:
        print(f"\n  [RETRY] Previous post not confirmed — retrying with immediate send")

    print("\n[1/3] Loading newsletter...")
    name, html   = load_newsletter(status, is_retry)
    ig_data      = load_ig_data()
    thumbnail    = load_thumbnail_url()

    subject      = build_subject(ig_data, name)
    preview_text = build_preview_text(ig_data)
    send_at      = send_time_edt(send_immediately=is_retry)

    print(f"  Subject:   {subject}")
    print(f"  Preview:   {preview_text[:60]}...")
    print(f"  Send at:   {datetime.utcfromtimestamp(send_at).strftime('%Y-%m-%d %H:%M UTC')}")
    if thumbnail:
        print(f"  Thumbnail: (loaded from last_generated_images.json)")
    else:
        print(f"  Thumbnail: none — last_generated_images.json not found")

    # Mark attempt in progress before API call
    save_post_status({
        "posted": False,
        "newsletter_file": name,
        "attempted_at": datetime.now(timezone.utc).isoformat(),
    })

    print("\n[2/3] Creating post in Beehiiv...")
    post = create_post(subject, preview_text, html, thumbnail)
    post_id = post.get("id", "")
    if not post_id:
        raise SystemExit(f"No post ID returned: {post}")
    print(f"  Post ID: {post_id}")

    print("\n[3/3] Scheduling post...")
    scheduled = schedule_post(post_id, send_at)

    # Persist success so next run won't retry the same newsletter
    save_post_status({
        "posted": True,
        "newsletter_file": name,
        "post_id": post_id,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    })

    print("\n" + "=" * 55)
    if scheduled:
        send_label = "immediately (retry)" if is_retry else "Monday noon EDT"
        print(f"  DONE — Post scheduled ({send_label})")
        print(f"  View: https://app.beehiiv.com/posts/{post_id}")
    else:
        print(f"  DONE — Draft created (schedule manually)")
        print(f"  View: https://app.beehiiv.com/posts/{post_id}")
    print("=" * 55)
    return True


if __name__ == "__main__":
    main()
