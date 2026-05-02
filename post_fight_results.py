"""
The Fight Docket — Automated Fight Results Poster
Crawls UFC.com and boxing sources, generates branded image, posts to Instagram
Runs: Sunday 1:00am, retries at 2:00am if results missing, posts at 4:00am
"""

import os
import sys
import json
import re
import requests
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
    Crawl UFC.com for recent results using Firecrawl.
    Returns list of {winner, loser, method, round_num, time, event}
    """
    try:
        print("🥊 Crawling UFC.com for results...")

        # Use Firecrawl to scrape UFC.com results page
        url = "https://www.ufc.com/results"

        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}"
        }

        # Query Firecrawl API to extract fight results
        firecrawl_payload = {
            "url": url,
            "formats": ["json"],
            "jsonOptions": {
                "prompt": "Extract recent UFC fight results. For each fight, provide: winner name, loser name, winning method (KO/TKO/SUBMISSION/DECISION), round number, time of finish (or fight duration), and event name. Return as array of objects."
            }
        }

        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json=firecrawl_payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            results_text = data.get('json', {})

            # Parse extracted results into standardized format
            if results_text:
                results = []
                # Firecrawl returns structured JSON — parse it into fight objects
                if isinstance(results_text, list):
                    for fight in results_text[:3]:  # Get top 3 recent fights
                        parsed = parse_fight_results(fight)
                        if parsed:
                            results.append(parsed)

                print(f"✅ Found {len(results)} UFC results")
                return results
        else:
            print(f"⚠️  Firecrawl UFC crawl returned {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ UFC crawl failed: {e}")
        return []

def crawl_boxing_results():
    """
    Crawl BoxRec and ESPN for boxing results using Firecrawl.
    Returns list of {winner, loser, method, round_num, time, event}
    """
    try:
        print("🥊 Crawling BoxRec + ESPN for boxing results...")

        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}"
        }

        all_results = []

        # Crawl BoxRec for recent results
        boxrec_payload = {
            "url": "https://www.boxrec.com/en/results",
            "formats": ["json"],
            "jsonOptions": {
                "prompt": "Extract recent boxing fight results from this page. For each fight, provide: winner name, loser name, winning method (KO/TKO/DECISION/POINTS), round number, time of finish, and event name. Return as array of objects."
            }
        }

        try:
            response = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                json=boxrec_payload,
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('json'):
                    results_list = data.get('json', [])
                    if isinstance(results_list, list):
                        for fight in results_list[:2]:  # Get top 2 BoxRec fights
                            parsed = parse_fight_results(fight)
                            if parsed:
                                all_results.append(parsed)
                    print(f"✅ Found {len(all_results)} BoxRec results")
        except Exception as e:
            print(f"⚠️  BoxRec crawl skipped: {e}")

        # Crawl ESPN for additional boxing coverage
        espn_payload = {
            "url": "https://www.espn.com/boxing/results",
            "formats": ["json"],
            "jsonOptions": {
                "prompt": "Extract recent boxing fight results. For each fight: winner, loser, method (KO/TKO/DECISION), round, time, and event name. Return as array of objects."
            }
        }

        try:
            response = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                json=espn_payload,
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('json'):
                    results_list = data.get('json', [])
                    if isinstance(results_list, list):
                        for fight in results_list[:1]:  # Get top 1 ESPN fight
                            parsed = parse_fight_results(fight)
                            if parsed:
                                all_results.append(parsed)
                    print(f"✅ Found {len(all_results)} total boxing results")
        except Exception as e:
            print(f"⚠️  ESPN crawl skipped: {e}")

        return all_results

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
    raw_data: dict from Firecrawl extraction with fight details

    Returns: {
        'winner': 'Fighter Name',
        'loser': 'Fighter Name',
        'method': 'KO/TKO | SUBMISSION | DECISION',
        'round_num': 'R1',
        'time': '3:45',
        'event': 'UFC 328'
    }
    """
    try:
        if not raw_data:
            return None

        # Extract and normalize fields
        winner = raw_data.get('winner') or raw_data.get('winner_name') or ''
        loser = raw_data.get('loser') or raw_data.get('loser_name') or ''
        method = raw_data.get('method') or raw_data.get('winning_method') or ''
        round_num = raw_data.get('round') or raw_data.get('round_number') or 'R1'
        time = raw_data.get('time') or raw_data.get('time_finish') or 'Full'
        event = raw_data.get('event') or raw_data.get('event_name') or 'Fight Night'

        # Clean up method (standardize)
        method = method.upper().strip()
        if 'KO' in method or 'KNOCKOUT' in method:
            method = 'KO'
        elif 'TKO' in method or 'TECHNICAL' in method:
            method = 'TKO'
        elif 'SUBMISSION' in method:
            method = 'SUBMISSION'
        elif 'DECISION' in method or 'DEC' in method or 'POINTS' in method:
            method = 'DECISION'

        # Clean up round (ensure R format)
        round_num = str(round_num).upper().strip()
        if not round_num.startswith('R'):
            round_num = f"R{round_num}"

        # Validate required fields
        if not winner or not loser or not method or not event:
            print(f"⚠️  Incomplete fight data: {raw_data}")
            return None

        return {
            'winner': winner.strip(),
            'loser': loser.strip(),
            'method': method,
            'round_num': round_num,
            'time': time.strip(),
            'event': event.strip()
        }

    except Exception as e:
        print(f"⚠️  Error parsing fight result: {e}")
        return None

# ──────────────────────────────────────────────────────────────
# INSTAGRAM POSTING
# ──────────────────────────────────────────────────────────────

SESSION_FILE = os.path.join(SCRIPT_DIR, "instagram_content", ".ig_session.json")


def post_to_instagram(image_path, caption):
    """
    Post image + caption to Instagram via instagrapi.
    Uses session persistence to reduce login challenges from GitHub Actions IPs.
    """
    try:
        from instagrapi import Client
        from instagrapi.exceptions import LoginRequired, ChallengeRequired

        print(f"  Posting to Instagram: @{INSTAGRAM_USERNAME}")
        cl = Client()
        cl.delay_range = [2, 5]

        # Try loading saved session first (avoids fresh login from new IPs)
        if os.path.exists(SESSION_FILE):
            try:
                cl.load_settings(SESSION_FILE)
                cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                print("  Session loaded from file")
            except (LoginRequired, Exception):
                print("  Saved session expired, logging in fresh...")
                cl = Client()
                cl.delay_range = [2, 5]
                cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        else:
            cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

        # Save session for next run
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        cl.dump_settings(SESSION_FILE)

        media = cl.photo_upload(image_path, caption=caption)
        print(f"  Posted. Media ID: {media.id}")
        cl.logout()
        return True

    except Exception as e:
        print(f"  Instagram post failed: {e}")
        print("  Image and caption saved — post manually from instagram_content/")
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
