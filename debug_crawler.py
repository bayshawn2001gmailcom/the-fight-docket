#!/usr/bin/env python3
"""Debug Firecrawl extraction for upcoming fights."""
import os, json, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
if not FIRECRAWL_API_KEY:
    raise SystemExit("Missing FIRECRAWL_API_KEY")

FC_HEADERS = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}"}

def test_url(url, prompt):
    """Test Firecrawl extraction with debug output."""
    print(f"\n{'='*60}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={
                "url": url,
                "formats": ["json"],
                "jsonOptions": {"prompt": prompt},
            },
            headers=FC_HEADERS,
            timeout=30,
        )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Full response:\n{json.dumps(data, indent=2)}")

        extracted = (data.get("data") or {}).get("json") or data.get("json") or []
        print(f"\nExtracted data type: {type(extracted)}")
        print(f"Extracted data:\n{json.dumps(extracted, indent=2)}")

    except Exception as e:
        print(f"ERROR: {e}")

# Test UFC
test_url(
    "https://www.ufc.com/events",
    "Extract all upcoming UFC events and their main card fights. For each fight return: "
    "fighter1, fighter2, event, date, venue, city, weight_class, is_title_fight. Return as array."
)

# Test ESPN
test_url(
    "https://www.espn.com/boxing/schedule",
    "Extract upcoming boxing matches. For each fight: "
    "fighter1, fighter2, event_name, date, venue, city, weight_class, is_title_fight. Return as array."
)
