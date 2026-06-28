#!/usr/bin/env python3
"""
The Fight Docket — Beehiiv Session Capture (one-time setup)

Extracts Beehiiv cookies from your existing Chrome session and saves them
in a format that Playwright can reuse for automation.

Prerequisites:
  1. Log into app.beehiiv.com in your regular Chrome browser
  2. Close ALL Chrome windows completely (needed to access the cookie database)
  3. Run this script

Run:
    python tools/beehiiv_capture_session.py

After running, test it works:
    python tools/beehiiv_browser_post.py --draft-only
"""
import json, sys, time
from pathlib import Path
from datetime import datetime, timezone

ROOT         = Path(__file__).parent.parent
SESSION_FILE = ROOT / ".beehiiv_session.json"


def extract_from_chrome() -> list[dict]:
    """Extract Beehiiv cookies from Chrome using browser_cookie3."""
    try:
        import browser_cookie3
        jar = browser_cookie3.chrome(domain_name=".beehiiv.com")
        cookies = []
        for c in jar:
            cookies.append({
                "name":     c.name,
                "value":    c.value,
                "domain":   c.domain or ".beehiiv.com",
                "path":     c.path or "/",
                "secure":   bool(c.secure),
                "httpOnly": False,
                "sameSite": "Lax",
            })
        return cookies
    except Exception as e:
        raise SystemExit(f"Cookie extraction failed: {e}\nMake sure Chrome is FULLY closed and browser_cookie3 is installed.")


def build_storage_state(cookies: list[dict]) -> dict:
    """Wrap cookies in Playwright storage_state format."""
    return {
        "cookies": cookies,
        "origins": [],
    }


def verify_session(session_file: Path) -> bool:
    """Quick Playwright verification that the session can reach Beehiiv dashboard."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx  = browser.new_context(storage_state=str(session_file))
            page = ctx.new_page()
            page.goto("https://app.beehiiv.com/dashboard", wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)
            logged_in = "/login" not in page.url and "beehiiv.com" in page.url
            browser.close()
            return logged_in
    except Exception as e:
        print(f"  Verification error: {e}")
        return False


def main():
    print("=" * 60)
    print("  Beehiiv Session Capture")
    print("=" * 60)
    print()
    print("  Extracting Beehiiv cookies from Chrome...")
    print("  (Chrome must be fully closed for this to work)")
    print()

    cookies = extract_from_chrome()
    if not cookies:
        raise SystemExit(
            "No Beehiiv cookies found in Chrome.\n"
            "Make sure you're logged into app.beehiiv.com in Chrome first."
        )
    print(f"  Found {len(cookies)} Beehiiv cookies")

    state = build_storage_state(cookies)
    SESSION_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"  Saved → {SESSION_FILE.name}")
    print()

    print("  Verifying session with Playwright...")
    ok = verify_session(SESSION_FILE)
    if ok:
        print("  Session valid — automation is ready.")
        print()
        print("  Next step:")
        print("    python tools/beehiiv_browser_post.py --draft-only")
    else:
        print("  Session verification failed — cookies may have expired.")
        print("  Log into Beehiiv in Chrome, close Chrome, and run this script again.")
        SESSION_FILE.unlink(missing_ok=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
