#!/usr/bin/env python3
"""
The Fight Docket — Token Refresh & Expiry Monitor (WAT Framework)
Manages Instagram and Facebook long-lived access tokens (expire in 60 days).

Usage:
  python tools/refresh_tokens.py            (check expiry, refresh if < 14 days remain)
  python tools/refresh_tokens.py --status   (show token age and days remaining)
  python tools/refresh_tokens.py --setup    (interactive first-time token setup)

Run this weekly (Task Scheduler: every Monday after the newsletter pipeline).
It's a no-op if tokens have > 14 days remaining — safe to run often.

How Instagram long-lived tokens work:
  - Short-lived token (1 hour): generated in Facebook Developer portal
  - Exchange for long-lived token (60 days): one API call
  - Refresh before expiry: another API call resets to 60 days
  - The long-lived token is the same for both Instagram and Facebook Page access

Required .env keys for refresh (after --setup):
  INSTAGRAM_PAGE_TOKEN       — current long-lived token
  INSTAGRAM_TOKEN_ISSUED_AT  — ISO date when token was last refreshed (YYYY-MM-DD)
  FACEBOOK_APP_ID            — Facebook App ID (from developers.facebook.com)
  FACEBOOK_APP_SECRET        — Facebook App Secret

First-time setup:
  1. Go to developers.facebook.com → your App → Tools → Graph API Explorer
  2. Generate a User token with permissions:
       instagram_basic, instagram_content_publish,
       pages_read_engagement, pages_manage_posts
  3. Exchange for long-lived token:
       GET /oauth/access_token?grant_type=fb_exchange_token
           &client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN
  4. Get your Page token from:
       GET /me/accounts?access_token=LONG_LIVED_USER_TOKEN
  5. Store the Page token as INSTAGRAM_PAGE_TOKEN (and FACEBOOK_PAGE_TOKEN if different)
  6. Run: python tools/refresh_tokens.py --setup   to record the issue date

Or run --setup and follow the interactive prompts.
"""
import os, sys, io, json, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv, set_key
import requests

ROOT    = Path(__file__).parent.parent
ENV     = ROOT / ".env"
HOME_ENV = Path.home() / ".env"

load_dotenv(ENV)
load_dotenv(HOME_ENV, override=False)

INSTAGRAM_PAGE_TOKEN      = os.getenv("INSTAGRAM_PAGE_TOKEN", "")
INSTAGRAM_TOKEN_ISSUED_AT = os.getenv("INSTAGRAM_TOKEN_ISSUED_AT", "")
FACEBOOK_APP_ID           = os.getenv("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET       = os.getenv("FACEBOOK_APP_SECRET", "")

GRAPH_BASE    = "https://graph.facebook.com/v21.0"
WARN_DAYS     = 14   # warn and refresh when < this many days remain
TOKEN_TTL     = 60   # Instagram long-lived token TTL in days


# ---------------------------------------------------------------------------
# Token age calculation
# ---------------------------------------------------------------------------

def _token_age() -> int | None:
    """Returns days since token was issued, or None if unknown."""
    if not INSTAGRAM_TOKEN_ISSUED_AT:
        return None
    try:
        issued = date.fromisoformat(INSTAGRAM_TOKEN_ISSUED_AT)
        return (date.today() - issued).days
    except ValueError:
        return None


def _days_remaining() -> int | None:
    age = _token_age()
    if age is None:
        return None
    return TOKEN_TTL - age


# ---------------------------------------------------------------------------
# Token refresh via Graph API
# ---------------------------------------------------------------------------

def _refresh_token(current_token: str) -> str:
    """Exchange current long-lived token for a new 60-day token."""
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        raise SystemExit(
            "Missing FACEBOOK_APP_ID or FACEBOOK_APP_SECRET in .env\n"
            "These are required for automatic refresh. Run --setup to configure."
        )

    resp = requests.get(
        f"{GRAPH_BASE}/oauth/access_token",
        params={
            "grant_type":        "fb_exchange_token",
            "client_id":         FACEBOOK_APP_ID,
            "client_secret":     FACEBOOK_APP_SECRET,
            "fb_exchange_token": current_token,
        },
        timeout=15,
    )
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"Token refresh failed: {data['error']}")

    new_token = data.get("access_token")
    if not new_token:
        raise RuntimeError(f"No access_token in response: {data}")

    return new_token


def _save_token(new_token: str) -> None:
    """Write new token + issue date to .env."""
    today = date.today().isoformat()
    if ENV.exists():
        set_key(str(ENV), "INSTAGRAM_PAGE_TOKEN", new_token)
        set_key(str(ENV), "FACEBOOK_PAGE_TOKEN", new_token)
        set_key(str(ENV), "INSTAGRAM_TOKEN_ISSUED_AT", today)
        print(f"  Token saved to {ENV}")
    else:
        print(f"  WARNING: {ENV} not found. Add these lines manually:")
        print(f"  INSTAGRAM_PAGE_TOKEN={new_token}")
        print(f"  FACEBOOK_PAGE_TOKEN={new_token}")
        print(f"  INSTAGRAM_TOKEN_ISSUED_AT={today}")


# ---------------------------------------------------------------------------
# Setup mode
# ---------------------------------------------------------------------------

def _setup():
    print("=" * 55)
    print("  Token Setup — The Fight Docket")
    print("=" * 55)
    print()
    print("Follow these steps:")
    print("  1. Go to: https://developers.facebook.com/tools/explorer/")
    print("  2. Select your Fight Docket App")
    print("  3. Generate a User token with these permissions:")
    print("       instagram_basic")
    print("       instagram_content_publish")
    print("       pages_read_engagement")
    print("       pages_manage_posts")
    print("  4. Paste the short-lived token below")
    print()

    short_token = input("Paste your short-lived token here: ").strip()
    app_id      = input("Facebook App ID: ").strip()
    app_secret  = input("Facebook App Secret: ").strip()

    print("\n  Exchanging for long-lived token (60 days)...")
    resp = requests.get(
        f"{GRAPH_BASE}/oauth/access_token",
        params={
            "grant_type":        "fb_exchange_token",
            "client_id":         app_id,
            "client_secret":     app_secret,
            "fb_exchange_token": short_token,
        },
        timeout=15,
    )
    data = resp.json()
    if "error" in data:
        raise SystemExit(f"Exchange failed: {data['error']}")

    long_token = data.get("access_token")
    expires_in = data.get("expires_in", TOKEN_TTL * 86400)
    print(f"  Got long-lived token (expires in ~{expires_in // 86400} days)")

    print("\n  Fetching your Facebook Page access token...")
    pages_resp = requests.get(
        f"{GRAPH_BASE}/me/accounts",
        params={"access_token": long_token},
        timeout=15,
    )
    pages_data = pages_resp.json()
    pages = pages_data.get("data", [])

    if not pages:
        print("  No pages found. Using the long-lived user token as page token.")
        page_token = long_token
        page_id    = input("Paste your Facebook Page ID (number from the page URL): ").strip()
    else:
        print("\n  Your Facebook Pages:")
        for i, p in enumerate(pages):
            print(f"    [{i}] {p.get('name')} (ID: {p.get('id')})")
        choice = int(input("  Choose page number: ").strip())
        page   = pages[choice]
        page_token = page.get("access_token", long_token)
        page_id    = page.get("id", "")
        print(f"  Selected: {page.get('name')} (ID: {page_id})")

    ig_account_id = input("\nPaste your Instagram Business Account ID\n  (find it in Instagram app: Settings > Account > Switch to Professional): ").strip()

    today = date.today().isoformat()
    if ENV.exists():
        set_key(str(ENV), "FACEBOOK_APP_ID", app_id)
        set_key(str(ENV), "FACEBOOK_APP_SECRET", app_secret)
        set_key(str(ENV), "FACEBOOK_PAGE_ID", page_id)
        set_key(str(ENV), "FACEBOOK_PAGE_TOKEN", page_token)
        set_key(str(ENV), "INSTAGRAM_ACCOUNT_ID", ig_account_id)
        set_key(str(ENV), "INSTAGRAM_PAGE_TOKEN", page_token)
        set_key(str(ENV), "INSTAGRAM_TOKEN_ISSUED_AT", today)
        print(f"\n  All credentials saved to {ENV}")
    else:
        print("\n  Add these to your .env:")
        print(f"  FACEBOOK_APP_ID={app_id}")
        print(f"  FACEBOOK_APP_SECRET={app_secret}")
        print(f"  FACEBOOK_PAGE_ID={page_id}")
        print(f"  FACEBOOK_PAGE_TOKEN={page_token}")
        print(f"  INSTAGRAM_ACCOUNT_ID={ig_account_id}")
        print(f"  INSTAGRAM_PAGE_TOKEN={page_token}")
        print(f"  INSTAGRAM_TOKEN_ISSUED_AT={today}")

    print(f"\n  Setup complete. Token expires ~{TOKEN_TTL} days from today ({today}).")
    print(f"  Next refresh needed before: {(date.today().__class__.fromisoformat(today)).__class__.fromordinal(date.today().toordinal() + TOKEN_TTL - WARN_DAYS).isoformat()}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Check and refresh Instagram/Facebook tokens")
    parser.add_argument("--status", action="store_true", help="Show token status only")
    parser.add_argument("--setup", action="store_true", help="Interactive first-time token setup")
    parser.add_argument("--force", action="store_true", help="Force refresh even if token is fresh")
    args = parser.parse_args()

    if args.setup:
        _setup()
        return

    print("=" * 55)
    print("  The Fight Docket — Token Status")
    print(f"  Date: {date.today().isoformat()}")
    print("=" * 55)

    age      = _token_age()
    remaining = _days_remaining()

    if age is None:
        print("\n  ⚠️  INSTAGRAM_TOKEN_ISSUED_AT not set in .env")
        print("  Run: python tools/refresh_tokens.py --setup")
        return

    if not INSTAGRAM_PAGE_TOKEN:
        print("\n  ❌  INSTAGRAM_PAGE_TOKEN not set in .env")
        print("  Run: python tools/refresh_tokens.py --setup")
        return

    print(f"\n  Token issued:     {INSTAGRAM_TOKEN_ISSUED_AT}")
    print(f"  Days used:        {age} / {TOKEN_TTL}")
    print(f"  Days remaining:   {remaining}")

    if args.status:
        status = "✅ Fresh" if remaining > WARN_DAYS else ("⚠️  Expiring soon" if remaining > 0 else "❌  EXPIRED")
        print(f"  Status:           {status}")
        return

    if remaining > WARN_DAYS and not args.force:
        print(f"\n  ✅ Token is fresh ({remaining} days left) — no refresh needed.")
        return

    if remaining <= 0:
        print(f"\n  ❌ Token EXPIRED {abs(remaining)} days ago!")
        print("  You must generate a new token via --setup.")
        sys.exit(1)

    print(f"\n  ⚠️  Only {remaining} days remain — refreshing now...")
    new_token = _refresh_token(INSTAGRAM_PAGE_TOKEN)
    _save_token(new_token)
    print(f"  ✅ Token refreshed. New expiry: ~{TOKEN_TTL} days from today.")


if __name__ == "__main__":
    main()
