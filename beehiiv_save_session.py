#!/usr/bin/env python3
"""
One-time setup: opens a real browser window so you can log in to Beehiiv manually.
Saves the session cookies to beehiiv_session.json for automated use.

Run once: python beehiiv_save_session.py
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = Path(__file__).parent / "beehiiv_session.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()

    print("Opening Beehiiv login page...")
    print("Log in manually in the browser window, then come back here.")
    page.goto("https://app.beehiiv.com/login")

    # Wait until the dashboard loads (user is logged in)
    print("Waiting for dashboard...")
    page.wait_for_url("**/dashboard**", timeout=120000)
    print("Logged in. Saving session...")

    ctx.storage_state(path=str(SESSION_FILE))
    print(f"Session saved to {SESSION_FILE}")
    browser.close()
