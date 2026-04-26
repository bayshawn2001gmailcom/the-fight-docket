"""
The Fight Docket — Automated Fight Results Poster
Crawls UFC.com and boxing sources, generates branded image, posts to Instagram
Runs: Sunday 1:00am, retries at 2:00am if results missing, posts at 4:00am
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Instagram templates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ig_templates import fight_result

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPCOMING_FIGHTS_FILE = os.path.join(SCRIPT_DIR, "upcoming_fights.json")
INSTAGRAM_CONTENT_DIR = os.path.join(SCRIPT_DIR, "instagram_content")
os.makedirs(INSTAGRAM_CONTENT_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────
# FIRECRAWL CRAWLING (via web_fetch)
# ──────────────────────────────────────────────────────────────

def crawl_ufc_results():
    """
    Crawl UFC.com for recent results.
    Returns list of {winner, loser, method, round, time, event}
    """
    try:
        print("🥊 Crawling UFC.com for results...")
        # In production, use Firecrawl API here
        # For now, this is a placeholder
        results = []
        # TODO: Implement Firecrawl crawling
        return results
    except Exception as e:
        print(f"❌ UFC crawl failed: {e}")
        return []

def crawl_boxing_results():
    """
    Crawl BoxRec and ESPN for boxing results.
    Returns list of {winner, loser, method, round, time, event}
    """
    try:
        print("🥊 Crawling BoxRec + ESPN for boxing results...")
        # In production, use Firecrawl API here
        results = []
        # TODO: Implement Firecrawl crawling
        return results
    except Exception as e:
        print(f"❌ Boxing crawl failed: {e}")
        return []

# ──────────────────────────────────────────────────────────────
# BACKUP: LOAD UPCOMING FIGHTS
# ──────────────────────────────────────────────────────────────

def load_upcoming_fights():
    """Load fights we know about from Friday crawl (backup reference)."""
    if os.path.exists(UPCOMING_FIGHTS_FILE):
        try:
            with open(UPCOMING_FIGHTS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

# ──────────────────────────────────────────────────────────────
# RESULT PARSING
# ──────────────────────────────────────────────────────────────

def parse_fight_results(raw_data):
    """
    Parse crawled fight data into standardized format.
    Returns: {
        'winner': 'Fighter Name',
        'loser': 'Fighter Name',
        'method': 'KO/TKO | SUBMISSION | DECISION',
        'round_num': 'R1',
        'time': '3:45',
        'event': 'UFC 328'
    }
    """
    # This is a placeholder — in production, parse actual HTML/JSON
    return None

# ──────────────────────────────────────────────────────────────
# INSTAGRAM POSTING
# ──────────────────────────────────────────────────────────────

def post_to_instagram(image_path, caption):
    """
    Post image + caption to Instagram via instagrapi.
    """
    try:
        from instagrapi import Client

        print(f"📸 Posting to Instagram: @{INSTAGRAM_USERNAME}")
        client = Client()
        client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

        # Upload photo
        media = client.photo_upload(image_path, caption=caption)
        print(f"✅ Posted! Media ID: {media.id}")

        client.logout()
        return True
    except Exception as e:
        print(f"❌ Instagram post failed: {e}")
        return False

# ──────────────────────────────────────────────────────────────
# MAIN WORKFLOW
# ──────────────────────────────────────────────────────────────

def generate_and_post_result(result_data):
    """
    Take fight result data, generate image, post to Instagram.
    result_data: {winner, loser, method, round_num, time, event}
    """
    try:
        print(f"\n🎨 Generating image for {result_data['winner']} vs {result_data['loser']}...")

        # Generate branded image
        image_path = fight_result(
            winner=result_data['winner'],
            loser=result_data['loser'],
            method=result_data['method'],
            round_num=result_data['round_num'],
            time=result_data['time'],
            event=result_data['event'],
            filename=f"sunday_result_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
        )

        # Build caption
        caption = f"""
🥊 RESULT

{result_data['winner'].upper()} def. {result_data['loser'].upper()}
{result_data['method']} · {result_data['round_num']} · {result_data['time']}

📍 {result_data['event']}

#Boxing #UFC #MMA #FightResults
        """.strip()

        # Post to Instagram
        if post_to_instagram(image_path, caption):
            print(f"✅ Successfully posted fight result!")
            return True
        else:
            print(f"❌ Failed to post to Instagram")
            return False

    except Exception as e:
        print(f"❌ Error generating/posting: {e}")
        return False

def main():
    """
    Main workflow: Crawl results, generate image, post to Instagram.
    Called at: Sunday 1:00am (primary), 2:00am (retry)
    """
    print(f"\n{'='*60}")
    print(f"🥊 Fight Results Automation — {datetime.now()}")
    print(f"{'='*60}\n")

    # Crawl for results
    ufc_results = crawl_ufc_results()
    boxing_results = crawl_boxing_results()

    all_results = ufc_results + boxing_results

    if not all_results:
        print("⚠️  No results found yet. Check back at 2:00am EDT.")
        print("Loading upcoming fights as backup reference...")
        upcoming = load_upcoming_fights()
        if upcoming:
            print(f"Known fights: {json.dumps(upcoming, indent=2)}")
        return False

    # Process the main/biggest result
    main_result = all_results[0]  # Assume first is the biggest

    # Generate and post
    success = generate_and_post_result(main_result)

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
