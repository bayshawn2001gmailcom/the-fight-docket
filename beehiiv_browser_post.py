#!/usr/bin/env python3
"""
beehiiv_browser_post.py — Post newsletter to Beehiiv via browser automation.
Used instead of the API (free plan blocks API post creation).

Logs in (session or email/password), creates a new post, injects HTML with
real images replacing [IMAGE_PLACEHOLDER_xxx] tags, sets thumbnail, schedules.

Run: python beehiiv_browser_post.py
     python beehiiv_browser_post.py --send-now
"""
import argparse
import os, json, sys, time
import requests
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

PLACEHOLDER_MAP = {
    "intro":          "[IMAGE_PLACEHOLDER_intro]",
    "main_story":     "[IMAGE_PLACEHOLDER_main_story]",
    "fight_previews": "[IMAGE_PLACEHOLDER_fight_previews]",
    "business_intel": "[IMAGE_PLACEHOLDER_business_intel]",
}


# ---------------------------------------------------------------------------
# Status tracking
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
# Newsletter loading
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Image upload + injection
# ---------------------------------------------------------------------------

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
            print(f"  ImgBB upload OK: {url[:70]}...")
            return url
        print(f"  ImgBB upload failed {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        print(f"  ImgBB upload error: {e}")
    return ""


def inject_images_into_html(html: str) -> str:
    """Replace [IMAGE_PLACEHOLDER_xxx] tags with real <img> tags from generated images."""
    images_file = SCRIPT_DIR / "prompts" / "last_generated_images.json"

    if not images_file.exists():
        print("  No last_generated_images.json — removing image placeholders")
        for placeholder in PLACEHOLDER_MAP.values():
            html = html.replace(placeholder, "")
        return html

    try:
        data = json.loads(images_file.read_text(encoding="utf-8"))
        images = data.get("images", [])
    except Exception as e:
        print(f"  Could not load generated images: {e}")
        for placeholder in PLACEHOLDER_MAP.values():
            html = html.replace(placeholder, "")
        return html

    replaced = 0
    for img_data in images:
        section = img_data.get("section", "")
        placeholder = PLACEHOLDER_MAP.get(section)
        if not placeholder or placeholder not in html:
            continue

        filename = img_data.get("file", "")
        image_path = SCRIPT_DIR / "assets" / "newsletter_images" / filename
        img_url = ""

        if image_path.exists() and IMGBB_API_KEY:
            img_url = upload_to_imgbb(image_path)
        if not img_url:
            img_url = img_data.get("url", "")

        if img_url:
            img_tag = (
                f'<img src="{img_url}" alt="" '
                f'style="width:100%;max-width:680px;height:auto;display:block;margin:16px auto;border-radius:4px;">'
            )
            html = html.replace(placeholder, img_tag)
            replaced += 1
            print(f"  Injected image: {section}")
        else:
            html = html.replace(placeholder, "")
            print(f"  Removed placeholder: {section} (no image available)")

    for placeholder in PLACEHOLDER_MAP.values():
        if placeholder in html:
            html = html.replace(placeholder, "")

    print(f"  Images injected: {replaced}/{len(images)}")
    return html


def upload_thumbnail_url() -> str:
    """Return ImgBB URL for the first generated image (used as post thumbnail)."""
    images_file = SCRIPT_DIR / "prompts" / "last_generated_images.json"
    if not images_file.exists() or not IMGBB_API_KEY:
        return ""
    try:
        data = json.loads(images_file.read_text(encoding="utf-8"))
        images = data.get("images", [])
        if images:
            filename = images[0].get("file", "")
            image_path = SCRIPT_DIR / "assets" / "newsletter_images" / filename
            if image_path.exists():
                return upload_to_imgbb(image_path)
    except Exception as e:
        print(f"  Thumbnail upload failed: {e}")
    return ""


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------

def send_time_edt(send_immediately: bool) -> datetime:
    edt = timezone(timedelta(hours=-4))
    now = datetime.now(edt)
    if send_immediately:
        return now + timedelta(minutes=10)
    noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if noon > now:
        return noon
    return now + timedelta(minutes=10)


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

SESSION_FILE = SCRIPT_DIR / "beehiiv_session.json"


def get_session_state() -> str | None:
    """Load session from BEEHIIV_SESSION env var (base64) or local file."""
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


# ---------------------------------------------------------------------------
# Browser automation
# ---------------------------------------------------------------------------

def post_via_browser(subject: str, html_content: str, thumbnail_url: str, send_at: datetime, headless: bool = True):
    from playwright.sync_api import sync_playwright

    is_ci = bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))
    session = get_session_state()

    with sync_playwright() as p:
        # In CI use headless Playwright Chromium with saved session.
        # Locally use real Chrome (channel="chrome") so Cloudflare doesn't block.
        if is_ci:
            browser = p.chromium.launch(headless=True)
        else:
            browser = p.chromium.launch(channel="chrome", headless=False)

        if session:
            print("  Using saved session...")
            ctx = browser.new_context(storage_state=session)
            page = ctx.new_page()
            page.goto("https://app.beehiiv.com/dashboard", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            if "/login" in page.url:
                print("  Session expired — falling back to login")
                session = None

        if not session:
            print("  Logging in with email/password...")
            ctx = browser.new_context()
            page = ctx.new_page()
            page.goto("https://app.beehiiv.com/login", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            page.fill('input[type="email"], input[name="email"]', BEEHIIV_EMAIL)
            page.fill('input[type="password"], input[name="password"]', BEEHIIV_PASSWORD)
            page.click('button[type="submit"]')
            try:
                page.wait_for_url("**/dashboard**", timeout=30000)
                print("  Login successful")
            except Exception:
                raise SystemExit(f"Login failed — still at: {page.url}")

        print("  Creating new post...")
        page.goto("https://app.beehiiv.com/posts/new", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        if "/login" in page.url:
            raise SystemExit(f"Redirected to login on /posts/new — session is invalid. Re-run beehiiv_capture_session.py.")

        # Set subject / title
        subject_field = page.locator(
            'input[placeholder*="Subject" i], input[name*="subject" i], input[aria-label*="subject" i]'
        ).first
        if subject_field.count() > 0:
            subject_field.click()
            subject_field.fill(subject)
            time.sleep(1)

        # Inject HTML content
        print("  Injecting HTML content...")
        source_btn = page.locator(
            'button:has-text("HTML"), button:has-text("Source"), [aria-label*="source" i], [aria-label*="html" i]'
        ).first
        if source_btn.count() > 0:
            source_btn.click()
            time.sleep(1)
            editor = page.locator('textarea.CodeMirror-scroll, textarea[class*="source"], .CodeMirror textarea').first
            if editor.count() > 0:
                editor.fill(html_content)
        else:
            editor = page.locator('.ProseMirror').first
            if editor.count() > 0:
                editor.click()
                page.evaluate(f"""
                    const editor = document.querySelector('.ProseMirror');
                    editor.focus();
                    document.execCommand('selectAll');
                    document.execCommand('insertHTML', false, {json.dumps(html_content)});
                    editor.dispatchEvent(new InputEvent('input', {{bubbles: true}}));
                """)
        time.sleep(2)

        # Set thumbnail
        if thumbnail_url:
            print("  Setting thumbnail...")
            thumb_btn = page.locator(
                'button:has-text("Add thumbnail"), button:has-text("Thumbnail"), [aria-label*="thumbnail" i]'
            ).first
            if thumb_btn.count() > 0:
                thumb_btn.click()
                time.sleep(1)
                url_input = page.locator('input[placeholder*="URL" i], input[type="url"]').first
                if url_input.count() > 0:
                    url_input.fill(thumbnail_url)
                    page.keyboard.press("Enter")
                    time.sleep(2)

        # Schedule
        print(f"  Scheduling for {send_at.strftime('%Y-%m-%d %H:%M %Z')}...")
        schedule_btn = page.locator('button:has-text("Schedule"), [aria-label*="schedule" i]').first
        if schedule_btn.count() > 0:
            schedule_btn.click()
            time.sleep(1)
            date_input = page.locator('input[type="date"], input[placeholder*="date" i]').first
            time_input = page.locator('input[type="time"], input[placeholder*="time" i]').first
            if date_input.count() > 0:
                date_input.fill(send_at.strftime("%Y-%m-%d"))
            if time_input.count() > 0:
                time_input.fill(send_at.strftime("%H:%M"))
            confirm = page.locator(
                'button:has-text("Confirm"), button:has-text("Schedule post"), button:has-text("Save")'
            ).first
            if confirm.count() > 0:
                confirm.click()
                time.sleep(2)

        # Final save
        save_btn = page.locator('button:has-text("Save"), button:has-text("Publish")').first
        if save_btn.count() > 0:
            save_btn.click()
            time.sleep(3)

        print("  Done.")
        url = page.url
        browser.close()
        return url


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Post newsletter to Beehiiv via browser")
    parser.add_argument("--send-now", action="store_true",
                        help="Schedule for immediate send (10 min from now), for testing")
    args = parser.parse_args()

    print("=" * 55)
    print("  The Fight Docket — Beehiiv Browser Poster")
    print("=" * 55)

    status   = load_post_status()
    is_retry = not status.get("posted", True) and bool(status.get("newsletter_file"))
    if is_retry:
        print("\n  [RETRY] Previous post unconfirmed — sending immediately")
    if args.send_now:
        print("\n  [SEND-NOW] Scheduling for immediate delivery")

    print("\n[1/4] Loading content...")
    name, html = load_newsletter(status, is_retry)
    ig_data    = load_ig_data()
    subject    = build_subject(ig_data, name)
    send_at    = send_time_edt(send_immediately=args.send_now or is_retry)

    print(f"  Subject:  {subject}")
    print(f"  Send at:  {send_at.strftime('%Y-%m-%d %H:%M %Z')}")

    print("\n[2/4] Uploading thumbnail...")
    thumbnail = upload_thumbnail_url()
    if thumbnail:
        print(f"  Thumbnail: uploaded")
    else:
        print(f"  Thumbnail: none")

    print("\n[3/4] Injecting images into HTML...")
    html = inject_images_into_html(html)

    save_post_status({
        "posted": False,
        "newsletter_file": name,
        "attempted_at": datetime.now(timezone.utc).isoformat(),
    })

    print("\n[4/4] Posting via browser...")
    post_url = post_via_browser(subject, html, thumbnail, send_at)

    save_post_status({
        "posted": True,
        "newsletter_file": name,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    })

    print("\n" + "=" * 55)
    if args.send_now or is_retry:
        print("  DONE — Scheduled for immediate send (10 min)")
    else:
        print("  DONE — Scheduled for Monday noon EDT")
    print(f"  URL: {post_url}")
    print("=" * 55)


if __name__ == "__main__":
    main()
