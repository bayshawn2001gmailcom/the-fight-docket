"""
The Fight Docket — Upcoming Fights Crawler
Runs: Friday 6:00pm EDT
Purpose: Crawl UFC.com + boxing sources for UPCOMING fights
Stores card info as backup reference for Sunday results crawling
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPCOMING_FIGHTS_FILE = os.path.join(SCRIPT_DIR, "upcoming_fights.json")

# ──────────────────────────────────────────────────────────────
# CRAWL UPCOMING FIGHTS
# ──────────────────────────────────────────────────────────────

def crawl_upcoming_ufc():
    """
    Crawl UFC.com for upcoming fights this weekend.
    Returns: list of {fighter1, fighter2, event, date, weight_class, time}
    """
    try:
        print("🥊 Crawling UFC.com for upcoming fights...")
        fights = []
        # TODO: Implement Firecrawl crawling of UFC.com/events
        return fights
    except Exception as e:
        print(f"❌ UFC crawl failed: {e}")
        return []

def crawl_upcoming_boxing():
    """
    Crawl BoxRec + ESPN for upcoming boxing matches this weekend.
    Returns: list of {fighter1, fighter2, event, date, weight_class, time}
    """
    try:
        print("🥊 Crawling BoxRec + ESPN for upcoming boxing...")
        fights = []
        # TODO: Implement Firecrawl crawling
        return fights
    except Exception as e:
        print(f"❌ Boxing crawl failed: {e}")
        return []

# ──────────────────────────────────────────────────────────────
# STORE UPCOMING FIGHTS
# ──────────────────────────────────────────────────────────────

def save_upcoming_fights(fights_data):
    """Save upcoming fights to JSON for Sunday's results crawling."""
    try:
        with open(UPCOMING_FIGHTS_FILE, 'w') as f:
            json.dump(fights_data, f, indent=2)
        print(f"✅ Saved {len(fights_data)} upcoming fights to {UPCOMING_FIGHTS_FILE}")
        return True
    except Exception as e:
        print(f"❌ Failed to save fights: {e}")
        return False

# ──────────────────────────────────────────────────────────────
# MAIN WORKFLOW
# ──────────────────────────────────────────────────────────────

def main():
    """
    Main workflow: Crawl upcoming fights, store as backup.
    Runs Friday 6pm EDT.
    """
    print(f"\n{'='*60}")
    print(f"🥊 Upcoming Fights Crawler — {datetime.now()}")
    print(f"{'='*60}\n")

    # Crawl upcoming fights
    ufc_fights = crawl_upcoming_ufc()
    boxing_fights = crawl_upcoming_boxing()

    all_fights = ufc_fights + boxing_fights

    print(f"\n📊 Found {len(all_fights)} upcoming fights:")
    for fight in all_fights:
        print(f"  • {fight.get('fighter1')} vs {fight.get('fighter2')} — {fight.get('event')}")

    # Save for Sunday's use
    save_upcoming_fights({
        "crawled_at": datetime.now().isoformat(),
        "fights": all_fights,
        "ufc_count": len(ufc_fights),
        "boxing_count": len(boxing_fights)
    })

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
