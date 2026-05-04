#!/usr/bin/env python3
"""
beehiiv_browser_post.py — Post newsletter to Beehiiv via browser automation.
Used instead of the API (free plan blocks API post creation).

Logs in, creates a new post, injects HTML content, sets thumbnail, schedules send.

Run: python beehiiv_browser_post.py
"""
import os, json, sys, time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

BEEHIIV_EMAIL    = os.getenv("BEEHIIV_EMAIL", "")
BEEHIIV_PASSWORD = os.getenv("BEEHIIV_PASSWORD", "")
PUBLICATION_ID   = os.getenv("BEEHIIV_PUBLICATION_ID", "pub_3ee36121-475b-43f5-87b9-9a610d46779b")
IMGBB_API_KEY    = os.getenv("IMGBB_API_KEY", "")

SCRIPT_DIR  = Path(__file__).parent
STATUS_FILE = SCRIPT_DIR / "prompts" / "post_status.json"


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


def load_newsletter(status: dict, is_retry: bool) -> tuple:
    if is_retry and status.get("newsletter_file"):
        candidate = SCRIPT_DIR / status["newsletter_file"]
        if candidate.exists():
            print(f"  Retrying: {candidate.name}")
            return candidate.name, candidate.read_text(encoding="utf-8")
    files = sorted(SCRIPT_DIR.glob("newsletter_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit("No newsletter_*.html found.")
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
        return f"The Fight Docket | {stories[0][:60]}"
    date_str = newsletter_name.replace("newsletter_", "").replace(".html", "")
    return f"The Fight Docket | {date_str}"


def upload_thumbnail_to_imgbb() -> str:
    images_file = SCRIPT_DIR / "prompts" / "last_generated_images.json"
    if not images_file.exists() or not IMGBB_API_KEY:
        return ""
    try:
        import requests
        data = json.loads(images_file.read_text(encoding="utf-8"))
        images = data.get("images", [])
        if images:
            filename = images[0].get("file", "")
            image_path = SCRIPT_DIR / "assets" / "newsletter_images" / filename
            if image_path.exists():
                with open(image_path, "rb") as f:
                    resp = requests.post(
                        "https://api.imgbb.com/1/upload",
                        params={"key": IMGBB_API_KEY},
                        files={"image": f},
                        timeout=60,
                    )
                if resp.ok:
                    url = resp.json()["data"]["url"]
                    print(f"  Thumbnail uploaded: {url[:70]}...")
                    return url
    except Exception as e:
        print(f"  Thumbnail upload failed: {e}")
    return ""


def send_time_edt(send_immediately: bool) -> datetime:
    edt = timezone(timedelta(hours=-4))
    now = datetime.now(edt)
    if send_immediately:
        return now + timedelta(minutes=10)
    noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if noon > now:
        return noon
    return now + timedelta(minutes=10)


SESSION_FILE = SCRIPT_DIR / "beehiiv_session.json"


def get_session_state() -> str | None:
    """Load session from file or BEEHIIV_SESSION env var (base64 encoded for GitHub Actions)."""
    env_session = os.getenv("BEEHIIV_SESSION", "")
    if env_session:
        import base64, tempfile
        data = base64.b64decode(env_session)
        tmp = Path(tempfile.mktemp(suffix=".json"))
        tmp.write_bytes(data)
        return str(tmp)
    if SESSION_FILE.exists():
        return str(SESSION_FILE)
    return None


def post_via_browser(subject: str, html_content: str, thumbnail_url: str, send_at: datetime, headless: bool = True):
    from playwright.sync_api import sync_playwright

    session = get_session_state()
    if not session:
        raise SystemExit(
            "No Beehiiv session found. Run: python beehiiv_save_session.py\n"
            "Then encode for GitHub Actions: python beehiiv_encode_session.py"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(storage_state=session)
        page = ctx.new_page()

        print("  Loading Beehiiv (using saved session)...")
        page.goto("https://app.beehiiv.com/dashboard", wait_until="domcontentloaded", timeout=20000)
        # If redirected to login, session expired
        if "/login" in page.url:
            raise SystemExit("Session expired. Re-run: python beehiiv_save_session.py")

        print("  Creating new post...")
        page.goto(f"https://app.beehiiv.com/posts/new")
        page.wait_for_load_state("networkidle", timeout=15000)

        # Set subject / title
        subject_field = page.locator('input[placeholder*="Subject"], input[name*="subject"], input[aria-label*="subject" i]').first
        subject_field.click()
        subject_field.fill(subject)

        # Inject HTML via the source editor
        print("  Injecting HTML content...")
        # Try to find the HTML/source editor toggle
        source_btn = page.locator('button:has-text("HTML"), button:has-text("Source"), [aria-label*="source" i], [aria-label*="html" i]').first
        if source_btn.count() > 0:
            source_btn.click()
            time.sleep(1)
            editor = page.locator('textarea.CodeMirror-scroll, textarea[class*="source"], .CodeMirror textarea').first
            editor.fill(html_content)
        else:
            # ProseMirror editor — paste as HTML via JS
            editor = page.locator('.ProseMirror').first
            editor.click()
            page.evaluate(f"""
                const editor = document.querySelector('.ProseMirror');
                editor.focus();
                document.execCommand('selectAll');
                document.execCommand('insertHTML', false, {json.dumps(html_content)});
                editor.dispatchEvent(new InputEvent('input', {{bubbles: true}}));
            """)

        time.sleep(2)

        # Set thumbnail if we have one
        if thumbnail_url:
            print("  Setting thumbnail via URL...")
            thumb_btn = page.locator('button:has-text("Add thumbnail"), button:has-text("Thumbnail"), [aria-label*="thumbnail" i]').first
            if thumb_btn.count() > 0:
                thumb_btn.click()
                time.sleep(1)
                url_input = page.locator('input[placeholder*="URL"], input[type="url"]').first
                if url_input.count() > 0:
                    url_input.fill(thumbnail_url)
                    page.keyboard.press("Enter")
                    time.sleep(2)

        # Schedule the send
        print(f"  Scheduling for {send_at.strftime('%Y-%m-%d %H:%M %Z')}...")
        schedule_btn = page.locator('button:has-text("Schedule"), [aria-label*="schedule" i]').first
        if schedule_btn.count() > 0:
            schedule_btn.click()
            time.sleep(1)
            # Fill date/time fields
            date_input = page.locator('input[type="date"], input[placeholder*="date" i]').first
            time_input = page.locator('input[type="time"], input[placeholder*="time" i]').first
            if date_input.count() > 0:
                date_input.fill(send_at.strftime("%Y-%m-%d"))
            if time_input.count() > 0:
                time_input.fill(send_at.strftime("%H:%M"))
            confirm = page.locator('button:has-text("Confirm"), button:has-text("Schedule post"), button:has-text("Save")').first
            if confirm.count() > 0:
                confirm.click()
                time.sleep(2)

        # Save/publish
        save_btn = page.locator('button:has-text("Save"), button:has-text("Publish")').first
        if save_btn.count() > 0:
            save_btn.click()
            time.sleep(3)

        print("  Done.")
        url = page.url
        browser.close()
        return url


def main():
    print("=" * 55)
    print("  The Fight Docket — Beehiiv Browser Poster")
    print("=" * 55)

    status    = load_post_status()
    is_retry  = not status.get("posted", True) and bool(status.get("newsletter_file"))
    if is_retry:
        print("\n  [RETRY] Previous post unconfirmed — sending immediately")

    print("\n[1/3] Loading content...")
    name, html   = load_newsletter(status, is_retry)
    ig_data      = load_ig_data()
    subject      = build_subject(ig_data, name)
    thumbnail    = upload_thumbnail_to_imgbb()
    send_at      = send_time_edt(send_immediately=is_retry)

    print(f"  Subject:  {subject}")
    print(f"  Send at:  {send_at.strftime('%Y-%m-%d %H:%M %Z')}")

    save_post_status({"posted": False, "newsletter_file": name, "attempted_at": datetime.now(timezone.utc).isoformat()})

    print("\n[2/3] Posting via browser...")
    post_url = post_via_browser(subject, html, thumbnail, send_at)

    save_post_status({"posted": True, "newsletter_file": name, "posted_at": datetime.now(timezone.utc).isoformat()})

    print("\n" + "=" * 55)
    print(f"  DONE — {'Retry sent immediately' if is_retry else 'Scheduled for noon EDT'}")
    print(f"  URL: {post_url}")
    print("=" * 55)


if __name__ == "__main__":
    main()
