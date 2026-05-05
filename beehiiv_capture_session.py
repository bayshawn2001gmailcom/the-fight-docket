#!/usr/bin/env python3
"""
Connect to your REAL Chrome browser (not Playwright Chromium) so Beehiiv
allows login, then save the authenticated session for GitHub Actions.

Run: python beehiiv_capture_session.py
"""
import base64, subprocess, time, sys
from pathlib import Path

SESSION_FILE = Path(__file__).parent / "beehiiv_session.json"

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Users\baysh\AppData\Local\Google\Chrome\Application\chrome.exe",
]


def find_chrome():
    for path in CHROME_PATHS:
        if Path(path).exists():
            return path
    return None


def kill_chrome():
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
    time.sleep(2)


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Run: pip install playwright && playwright install chromium")

    chrome = find_chrome()
    if not chrome:
        raise SystemExit("Chrome not found.")

    print("=" * 55)
    print("  Beehiiv Session Capture")
    print("=" * 55)
    print()
    print("IMPORTANT: This opens your REAL Chrome (not a fake one).")
    print("You should be able to log in normally.")
    print()
    input("Press Enter to close Chrome and reopen it with debug port... ")

    print("\nClosing Chrome...")
    kill_chrome()

    print("Opening your real Chrome browser...")
    # Open Chrome pointing directly at the dashboard — if the profile
    # has a saved session it will auto-login; otherwise the user logs in manually
    subprocess.Popen([
        chrome,
        "--remote-debugging-port=9222",
        "--no-first-run",
        "--no-default-browser-check",
        "https://app.beehiiv.com/dashboard",
    ])
    time.sleep(4)

    print()
    print("Chrome is open. You need to be on your Beehiiv DASHBOARD.")
    print("- If Chrome already shows your dashboard → you're done, press Enter.")
    print("- If Chrome shows the login page → log in normally (email/password works in real Chrome).")
    print("- Wait until you can see your posts/dashboard before pressing Enter.")
    print()
    input("Press Enter ONLY when your Beehiiv dashboard is fully loaded... ")

    print("\nConnecting to Chrome and verifying session...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            raise SystemExit(f"Could not connect to Chrome: {e}")

        ctx = browser.contexts[0] if browser.contexts else None
        if not ctx:
            raise SystemExit("No browser context found.")

        # Find the beehiiv page and verify it's actually logged in
        pages = ctx.pages
        beehiiv_page = None
        for pg in pages:
            if "beehiiv.com" in pg.url:
                beehiiv_page = pg
                break

        if not beehiiv_page:
            print("Warning: no Beehiiv page found — capturing session anyway")
        elif "/login" in beehiiv_page.url:
            print(f"\nERROR: You are still on the login page ({beehiiv_page.url})")
            print("Please log in to Beehiiv first, then run this script again.")
            browser.close()
            return
        else:
            print(f"  Verified: logged in at {beehiiv_page.url}")

        ctx.storage_state(path=str(SESSION_FILE))
        size = SESSION_FILE.stat().st_size
        print(f"  Session saved ({size} bytes)")
        browser.close()

    if size < 100:
        print("WARNING: Session file is very small — may be empty. Are you sure you were logged in?")
        return

    # Encode and set GitHub secret
    encoded = base64.b64encode(SESSION_FILE.read_bytes()).decode()
    print(f"  Encoded ({len(encoded)} chars)")

    result = subprocess.run(
        ["gh", "secret", "set", "BEEHIIV_SESSION",
         "--body", encoded,
         "--repo", "bayshawn2001gmailcom/the-fight-docket"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("\nBEEHIIV_SESSION secret updated in GitHub Actions.")
        print("Run the newsletter pipeline to test:")
        print("  gh workflow run newsletter_pipeline.yml")
    else:
        print("gh secret set failed:", result.stderr.strip())


if __name__ == "__main__":
    main()
