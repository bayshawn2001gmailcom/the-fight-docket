#!/usr/bin/env python3
"""
The Fight Docket — Upcoming Fights Crawler
Runs: Friday 6:00pm EDT via GitHub Actions (friday-crawl-fights.yml)
Crawls UFC.com + ESPN Boxing for this weekend's fights, saves to upcoming_fights.json
"""
import os, sys, json, requests, time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
if not FIRECRAWL_API_KEY:
    raise SystemExit("Missing FIRECRAWL_API_KEY")

SCRIPT_DIR          = Path(__file__).parent
UPCOMING_FIGHTS_FILE = SCRIPT_DIR / "upcoming_fights.json"
FC_HEADERS = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}"}


def firecrawl_extract(url, prompt):
    """Structured extraction via Firecrawl."""
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
        resp.raise_for_status()
        data = resp.json()
        return (data.get("data") or {}).get("json") or data.get("json") or []
    except Exception as e:
        print(f"  Firecrawl failed for {url}: {e}")
        return []


def crawl_upcoming_ufc():
    print("  Crawling UFC.com for upcoming events...")
    fights = firecrawl_extract(
        "https://www.ufc.com/events",
        "Extract all upcoming UFC events and their main card fights. For each fight return: "
        "fighter1 (string), fighter2 (string), event (string, e.g. 'UFC 329'), "
        "date (string, e.g. 'July 11, 2026'), venue (string), city (string), "
        "weight_class (string), is_title_fight (boolean). Return as array of objects.",
    )
    if isinstance(fights, list):
        return [f for f in fights if isinstance(f, dict)]
    if isinstance(fights, dict):
        return fights.get("fights", []) or fights.get("events", []) or []
    return []


def crawl_upcoming_boxing():
    print("  Crawling ESPN for upcoming boxing cards...")
    fights = firecrawl_extract(
        "https://www.espn.com/boxing/schedule",
        "Extract upcoming boxing matches scheduled within the next 30 days. For each fight: "
        "fighter1, fighter2, event_name, date, venue, city, weight_class, is_title_fight. "
        "Return as array of objects.",
    )
    if isinstance(fights, list):
        return [f for f in fights if isinstance(f, dict)]
    if isinstance(fights, dict):
        return fights.get("fights", []) or fights.get("schedule", []) or []
    return []


def main():
    print("=" * 55)
    print("  Fight Docket — Upcoming Fights Crawler")
    print(f"  {datetime.now().strftime('%A %B %d, %Y — %H:%M')}")
    print("=" * 55)

    ufc_fights     = crawl_upcoming_ufc()
    time.sleep(0.5)
    boxing_fights  = crawl_upcoming_boxing()

    all_fights = {
        "crawled_at": datetime.utcnow().isoformat() + "Z",
        "ufc":    ufc_fights,
        "boxing": boxing_fights,
    }

    UPCOMING_FIGHTS_FILE.write_text(json.dumps(all_fights, indent=2), encoding="utf-8")

    print(f"\n  UFC fights found   : {len(ufc_fights)}")
    print(f"  Boxing fights found: {len(boxing_fights)}")
    print(f"  Saved to: {UPCOMING_FIGHTS_FILE.name}")
    print("=" * 55)

    return bool(ufc_fights or boxing_fights)


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
