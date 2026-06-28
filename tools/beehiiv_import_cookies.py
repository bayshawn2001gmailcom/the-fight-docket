#!/usr/bin/env python3
"""
The Fight Docket — Beehiiv Cookie Import (one-time setup)

Import Beehiiv cookies from a JSON file (exported from Chrome DevTools)
and save them as a Playwright session for automation.

HOW TO EXPORT COOKIES FROM CHROME:
  1. Log into app.beehiiv.com in Chrome
  2. Open DevTools: F12 → Application tab → Cookies → https://app.beehiiv.com
  3. Install "Cookie-Editor" extension from Chrome Web Store (it's free)
  4. Click the extension icon on app.beehiiv.com → Export → "Export as JSON"
  5. Save the file as: Fight Newsletter/beehiiv_cookies.json
  6. Run this script: python tools/beehiiv_import_cookies.py

Run:
    python tools/beehiiv_import_cookies.py
    python tools/beehiiv_import_cookies.py --cookies path/to/cookies.json
"""
import json, sys, argparse
from pathlib import Path

ROOT         = Path(__file__).parent.parent
SESSION_FILE = ROOT / ".beehiiv_session.json"
DEFAULT_COOKIES_FILE = ROOT / "beehiiv_cookies.json"


_SAME_SITE_MAP = {"strict": "Strict", "lax": "Lax", "no_restriction": "None", "none": "None"}

def normalize_cookie(c: dict) -> dict:
    """Normalize a Cookie-Editor export to Playwright format."""
    raw_ss = c.get("sameSite") or "Lax"
    same_site = _SAME_SITE_MAP.get(raw_ss.lower(), "Lax") if raw_ss else "Lax"
    return {
        "name":     c.get("name", ""),
        "value":    c.get("value", ""),
        "domain":   c.get("domain", ".beehiiv.com"),
        "path":     c.get("path", "/"),
        "secure":   bool(c.get("secure", False)),
        "httpOnly": bool(c.get("httpOnly", False)),
        "sameSite": same_site,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cookies", default=str(DEFAULT_COOKIES_FILE),
                        help="Path to cookies JSON file (default: beehiiv_cookies.json)")
    args = parser.parse_args()

    cookies_file = Path(args.cookies)
    if not cookies_file.exists():
        print(f"Cookie file not found: {cookies_file}")
        print()
        print("How to get your Beehiiv cookies:")
        print("  1. Install 'Cookie-Editor' from Chrome Web Store (free)")
        print("  2. Go to app.beehiiv.com (while logged in)")
        print("  3. Click Cookie-Editor icon → Export → 'Export as JSON'")
        print(f"  4. Save to: {DEFAULT_COOKIES_FILE}")
        print(f"  5. Run: python tools/beehiiv_import_cookies.py")
        sys.exit(1)

    raw = json.loads(cookies_file.read_text(encoding="utf-8"))
    # Accept both array and dict with 'cookies' key
    if isinstance(raw, dict):
        raw = raw.get("cookies", [])

    cookies = [normalize_cookie(c) for c in raw if "beehiiv" in c.get("domain", "")]

    if not cookies:
        # If no domain filter matched, take all (user may have exported all cookies)
        cookies = [normalize_cookie(c) for c in raw]

    if not cookies:
        print("No cookies found in the file.")
        sys.exit(1)

    state = {"cookies": cookies, "origins": []}
    SESSION_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"Saved {len(cookies)} cookies -> {SESSION_FILE.name}")
    print()
    print("Session imported. Test it:")
    print("  python tools/beehiiv_browser_post.py --draft-only")


if __name__ == "__main__":
    main()
