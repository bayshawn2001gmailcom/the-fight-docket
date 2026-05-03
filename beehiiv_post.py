#!/usr/bin/env python3
"""
The Fight Docket — Beehiiv Auto-Poster
Reads the latest newsletter HTML + prompts/weekly_ig_data.json,
creates a post via Beehiiv API v2, and schedules it for Monday noon EDT.

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

for k, v in [("BEEHIIV_API_KEY", API_KEY), ("BEEHIIV_PUBLICATION_ID", PUBLICATION_ID)]:
    if not v:
        raise SystemExit(f"Missing {k}")

SCRIPT_DIR = Path(__file__).parent
BASE_URL   = "https://api.beehiiv.com/v2"
HEADERS    = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# Load newsletter content
# ---------------------------------------------------------------------------

def load_newsletter():
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
# Schedule: next Monday noon EDT
# ---------------------------------------------------------------------------

def next_monday_noon_edt() -> int:
    """Return Unix timestamp for next Monday 12:00pm EDT (UTC-4)."""
    edt = timezone(timedelta(hours=-4))
    now = datetime.now(edt)
    days_until_monday = (7 - now.weekday()) % 7 or 7
    next_monday = now + timedelta(days=days_until_monday)
    scheduled = next_monday.replace(hour=12, minute=0, second=0, microsecond=0)
    return int(scheduled.timestamp())


# ---------------------------------------------------------------------------
# Beehiiv API calls
# ---------------------------------------------------------------------------

def create_post(subject: str, preview_text: str, html_content: str) -> dict:
    """Create a draft post via Beehiiv API v2."""
    url = f"{BASE_URL}/publications/{PUBLICATION_ID}/posts"

    payload = {
        "subject":      subject,
        "preview_text": preview_text,
        "content_type": "html",
        "content":      html_content,
        "status":       "draft",
        "audience":     "all",
    }

    print(f"  Creating post: '{subject}'")
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=30)

    if not resp.ok:
        raise SystemExit(f"Beehiiv API error {resp.status_code}: {resp.text[:300]}")

    return resp.json().get("data", {})


def schedule_post(post_id: str, send_at: int):
    """Schedule an existing draft post."""
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

    print("\n[1/3] Loading newsletter...")
    name, html = load_newsletter()
    ig_data    = load_ig_data()

    subject      = build_subject(ig_data, name)
    preview_text = build_preview_text(ig_data)
    send_at      = next_monday_noon_edt()

    print(f"  Subject:  {subject}")
    print(f"  Preview:  {preview_text[:60]}...")
    print(f"  Send at:  {datetime.utcfromtimestamp(send_at).strftime('%Y-%m-%d %H:%M UTC')}")

    print("\n[2/3] Creating post in Beehiiv...")
    post = create_post(subject, preview_text, html)
    post_id = post.get("id", "")
    if not post_id:
        raise SystemExit(f"No post ID returned: {post}")
    print(f"  Post ID: {post_id}")

    print("\n[3/3] Scheduling post...")
    scheduled = schedule_post(post_id, send_at)

    print("\n" + "=" * 55)
    if scheduled:
        print(f"  DONE — Post scheduled for Monday noon EDT")
        print(f"  View: https://app.beehiiv.com/posts/{post_id}")
    else:
        print(f"  DONE — Draft created (schedule manually)")
        print(f"  View: https://app.beehiiv.com/posts/{post_id}")
    print("=" * 55)
    return True


if __name__ == "__main__":
    main()
