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
                "waitFor": 3000,
            },
            headers=FC_HEADERS,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        result = (data.get("data") or {}).get("json") or data.get("json") or []

        # Check if we got valid data (not hallucinated dummy data)
        if isinstance(result, dict):
            result = result.get("upcoming_matches") or result.get("fights") or []

        return result if isinstance(result, list) else []
    except Exception as e:
        print(f"  Firecrawl failed for {url}: {e}")
        return []


def crawl_upcoming_ufc():
    print("  Crawling UFC.com for upcoming events...")

    # Use a very specific prompt based on UFC.com page structure
    fights = firecrawl_extract(
        "https://www.ufc.com/events",
        "Look at the page and find all upcoming UFC events listed. For each event, extract: "
        "1) Event name/number (e.g., 'UFC 329'), 2) Main fight matchup (e.g., 'McGregor vs Holloway'), "
        "3) Date and time if available, 4) Venue/Location. "
        "Return ONLY the event data you can actually see on the page. "
        "Return as: [{ 'event': 'UFC 329', 'main_fight': 'McGregor vs Holloway', 'date': '2026-07-11', 'location': 'Las Vegas' }, ...]",
    )

    # Parse the response - it might come as string, dict, or list
    valid_fights = []
    if isinstance(fights, str):
        try:
            fights = json.loads(fights)
        except:
            return []

    if isinstance(fights, list) and fights:
        for f in fights:
            if isinstance(f, dict) and f.get("event") and f.get("main_fight"):
                # Reject dummy data
                if not any(dummy in str(f.get("main_fight", "")).lower() for dummy in ["fighter a", "fighter b", "fighter c"]):
                    valid_fights.append(f)

    return valid_fights


def crawl_upcoming_boxing():
    print("  Crawling ESPN for upcoming boxing cards...")

    # Try ESPN boxing
    fights = firecrawl_extract(
        "https://www.espn.com/boxing/schedule",
        "Extract upcoming boxing matches in the next 30 days. For each match: "
        "fighter1_name, fighter2_name, event_name, date (YYYY-MM-DD), venue, city, weight_class, is_title_fight. "
        "Return as array of objects.",
    )

    # Validate - reject clearly fake data
    valid_fights = []
    if isinstance(fights, list):
        for f in fights:
            if isinstance(f, dict):
                # Check for dummy fighter names
                f1 = str(f.get("fighter1_name", "")).lower() if "fighter1_name" in f else str(f.get("fighter1", "")).lower()
                f2 = str(f.get("fighter2_name", "")).lower() if "fighter2_name" in f else str(f.get("fighter2", "")).lower()

                # Reject dummy names and 2023 dates (obvious hallucinations)
                date_str = str(f.get("date", ""))
                if not any(dummy in f1 for dummy in ["fighter a", "fighter b", "fighter c", "fighter d", "fighter e", "fighter f"]) and \
                   not any(dummy in f2 for dummy in ["fighter a", "fighter b", "fighter c", "fighter d", "fighter e", "fighter f"]) and \
                   not date_str.startswith("2023") and \
                   f1 and f2 and f1 != f2:
                    valid_fights.append(f)

    if isinstance(fights, dict):
        fights_list = fights.get("upcoming_matches", []) or fights.get("fights", []) or fights.get("schedule", []) or []
        valid_fights = [f for f in fights_list if isinstance(f, dict)]

    return valid_fights


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
