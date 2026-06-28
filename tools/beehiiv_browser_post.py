#!/usr/bin/env python3
"""
The Fight Docket — Beehiiv Browser Automation (WAT Framework)
Fallback when API post creation returns 403 (requires enterprise plan).

Logs in with BEEHIIV_EMAIL + BEEHIIV_PASSWORD, creates a new post,
pastes the rendered HTML, optionally schedules for Monday noon EDT.

Run: python tools/beehiiv_browser_post.py
     python tools/beehiiv_browser_post.py --draft-only   (save, don't schedule)
     python tools/beehiiv_browser_post.py --send-now     (schedule 10 min out)

Requires:
  BEEHIIV_EMAIL     in ~/.env or .env
  BEEHIIV_PASSWORD  in ~/.env or .env
"""
import argparse, os, json, sys, time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

BEEHIIV_EMAIL    = os.getenv("BEEHIIV_EMAIL", "")
BEEHIIV_PASSWORD = os.getenv("BEEHIIV_PASSWORD", "")
PUBLICATION_ID   = os.getenv("BEEHIIV_PUBLICATION_ID", "pub_3ee36121-475b-43f5-87b9-9a610d46779b")

TMP_DIR     = ROOT / ".tmp"
STATUS_FILE = TMP_DIR / "post_status.json"
SESSION_FILE = ROOT / ".beehiiv_session.json"


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
    TMP_DIR.mkdir(exist_ok=True)
    STATUS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Content loading
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


def load_thumbnail_url() -> str:
    asset_files = sorted(TMP_DIR.glob("asset_urls_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if asset_files:
        urls = json.loads(asset_files[0].read_text(encoding="utf-8"))
        # Prefer dedicated thumbnail key; fall back to main_story, then first available
        return urls.get("thumbnail") or urls.get("main_story") or next(iter(urls.values()), "")
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
# Schedule helper
# ---------------------------------------------------------------------------

def send_time_edt(send_immediately: bool) -> datetime:
    edt = timezone(timedelta(hours=-4))
    now = datetime.now(edt)
    if send_immediately:
        return now + timedelta(minutes=10)
    noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    return noon if noon > now else now + timedelta(minutes=10)


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def get_session_path() -> str | None:
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


def save_session(ctx):
    ctx.storage_state(path=str(SESSION_FILE))
    print(f"  Session saved → {SESSION_FILE.name}")


# ---------------------------------------------------------------------------
# Browser automation
# ---------------------------------------------------------------------------

def post_via_browser(subject: str, preview_text: str, html_content: str,
                     thumbnail_url: str, send_at: datetime, draft_only: bool) -> str:
    from playwright.sync_api import sync_playwright

    is_ci = bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))
    session_path = get_session_path()

    if not session_path and not is_ci:
        raise SystemExit(
            "No Beehiiv session found.\n"
            "Run:  python tools/beehiiv_capture_session.py\n"
            "Log in manually once — automation reuses the saved session."
        )

    with sync_playwright() as p:
        if is_ci:
            browser = p.chromium.launch(headless=True)
        else:
            browser = p.chromium.launch(channel="chrome", headless=False)

        if session_path:
            print("  Using saved session...")
            ctx = browser.new_context(storage_state=session_path)
        else:
            ctx = browser.new_context()
        page = ctx.new_page()

        print("  Navigating to Beehiiv...")
        page.goto("https://app.beehiiv.com/dashboard", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        if "/login" in page.url:
            if not BEEHIIV_EMAIL or not BEEHIIV_PASSWORD:
                raise SystemExit(
                    "Session expired and no credentials available.\n"
                    "Run:  python tools/beehiiv_capture_session.py"
                )
            print("  Session expired — logging in with credentials...")
            page.goto("https://app.beehiiv.com/login", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            email_input = page.locator('input[type="email"], input[name="email"]').first
            email_input.wait_for(state="visible", timeout=10000)
            email_input.fill(BEEHIIV_EMAIL)
            time.sleep(0.5)
            password_input = page.locator('input[type="password"]').first
            if password_input.count() == 0 or not password_input.is_visible():
                page.locator('button[type="submit"]').first.click()
                time.sleep(2)
                page.locator('input[type="password"]').first.wait_for(state="visible", timeout=10000)
                password_input = page.locator('input[type="password"]').first
            password_input.fill(BEEHIIV_PASSWORD)
            time.sleep(0.5)
            page.locator('button[type="submit"]').first.click()
            try:
                page.wait_for_function(
                    "() => !window.location.pathname.startsWith('/login')",
                    timeout=30000
                )
                save_session(ctx)
            except Exception:
                raise SystemExit(f"Login failed — at: {page.url}")

        print(f"  Dashboard loaded")

        # Navigate to new post — click through UI (avoids bot checks on direct URL)
        print("  Creating new post...")
        new_post_btn = page.locator(
            'a[href*="/posts/new"], button:has-text("New post"), button:has-text("New Post"), '
            'a:has-text("New post"), a:has-text("New Post"), [data-testid*="new-post"]'
        ).first
        if new_post_btn.count() > 0:
            new_post_btn.click()
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            time.sleep(3)
        else:
            page.goto("https://app.beehiiv.com/posts/new", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

        if "/login" in page.url:
            raise SystemExit("Redirected to login on /posts/new — session invalid. Delete .beehiiv_session.json and retry.")

        # Subject line
        subject_sel = 'input[placeholder*="Subject" i], input[name*="subject" i], input[aria-label*="subject" i]'
        subject_field = page.locator(subject_sel).first
        if subject_field.count() > 0:
            subject_field.click()
            subject_field.fill(subject)
            time.sleep(0.5)

        # Inject HTML — try source/HTML toggle first, fall back to JS injection
        print("  Injecting HTML...")
        html_btn = page.locator(
            'button:has-text("HTML"), button:has-text("Source"), [aria-label*="source" i], [aria-label*="html" i]'
        ).first
        injected = False

        if html_btn.count() > 0:
            html_btn.click()
            time.sleep(1)
            editor = page.locator(
                'textarea.CodeMirror-scroll, textarea[class*="source"], .CodeMirror textarea'
            ).first
            if editor.count() > 0:
                editor.fill(html_content)
                injected = True

        if not injected:
            editor = page.locator('.ProseMirror').first
            if editor.count() > 0:
                editor.click()
                page.evaluate(f"""
                    (() => {{
                        const editor = document.querySelector('.ProseMirror');
                        if (!editor) return;
                        editor.focus();
                        document.execCommand('selectAll');
                        document.execCommand('insertHTML', false, {json.dumps(html_content)});
                        editor.dispatchEvent(new InputEvent('input', {{bubbles: true}}));
                    }})();
                """)
                injected = True

        if not injected:
            print("  WARNING: Could not locate editor — content may not be set")
        time.sleep(2)

        # Thumbnail
        if thumbnail_url:
            print("  Setting thumbnail...")
            thumb_btn = page.locator(
                'button:has-text("thumbnail"), [aria-label*="thumbnail" i]'
            ).first
            if thumb_btn.count() > 0:
                thumb_btn.click()
                time.sleep(1)
                url_input = page.locator('input[placeholder*="URL" i], input[type="url"]').first
                if url_input.count() > 0:
                    url_input.fill(thumbnail_url)
                    page.keyboard.press("Enter")
                    time.sleep(2)

        # Schedule (unless draft-only)
        if not draft_only:
            print(f"  Scheduling for {send_at.strftime('%Y-%m-%d %H:%M %Z')}...")
            schedule_btn = page.locator('button:has-text("Schedule"), [aria-label*="schedule" i]').first
            if schedule_btn.count() > 0:
                schedule_btn.click()
                time.sleep(1)
                date_input = page.locator('input[type="date"]').first
                time_input = page.locator('input[type="time"]').first
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

        # Save / publish
        save_btn = page.locator('button:has-text("Save draft"), button:has-text("Save"), button:has-text("Publish")').first
        if save_btn.count() > 0:
            save_btn.click()
            time.sleep(3)

        final_url = page.url
        browser.close()
        return final_url


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Post newsletter to Beehiiv via browser automation")
    parser.add_argument("--draft-only", action="store_true", help="Save as draft, skip scheduling")
    parser.add_argument("--send-now",   action="store_true", help="Schedule for 10 minutes from now")
    args = parser.parse_args()

    print("=" * 60)
    print("  The Fight Docket — Beehiiv Browser Post")
    print("=" * 60)

    status   = load_post_status()
    is_retry = not status.get("posted", True) and bool(status.get("newsletter_file"))
    if is_retry:
        print("\n  [RETRY] Previous post unconfirmed — sending immediately")

    print("\n[1/3] Loading content...")
    name, html   = load_newsletter(status, is_retry)
    ig_data      = load_ig_data()
    subject      = build_subject(ig_data, name)
    preview_text = build_preview_text(ig_data)
    thumbnail    = load_thumbnail_url()
    send_at      = send_time_edt(send_immediately=args.send_now or is_retry)

    print(f"  Subject  : {subject}")
    print(f"  Preview  : {preview_text[:60]}...")
    print(f"  Thumbnail: {'yes' if thumbnail else 'none'}")
    print(f"  Send at  : {send_at.strftime('%Y-%m-%d %H:%M %Z')}")

    save_post_status({
        "posted": False,
        "newsletter_file": name,
        "attempted_at": datetime.now(timezone.utc).isoformat(),
    })

    print("\n[2/3] Launching browser...")
    post_url = post_via_browser(
        subject, preview_text, html, thumbnail, send_at,
        draft_only=args.draft_only
    )

    save_post_status({
        "posted": True,
        "newsletter_file": name,
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "post_url": post_url,
    })

    print("\n[3/3] Done.")
    print("=" * 60)
    if args.draft_only:
        print("  DONE — Saved as draft")
    elif args.send_now or is_retry:
        print("  DONE — Scheduled for immediate send")
    else:
        print("  DONE — Scheduled for Monday noon EDT")
    print(f"  URL: {post_url}")
    print("=" * 60)


if __name__ == "__main__":
    main()
