"""
The Fight Docket — Test Instagram Post
Manual test with real fight: Jarrell "Big Baby" Miller vs Lenier Pero
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Instagram templates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ig_templates import fight_result

# ──────────────────────────────────────────────────────────────
# TEST DATA: Jarrell Miller vs Lenier Pero
# ──────────────────────────────────────────────────────────────

TEST_FIGHT = {
    "winner": "Jarrell Miller",
    "loser": "Lenier Pero",
    "method": "KO/TKO",  # Actual result
    "round_num": "R1",    # Actual round
    "time": "1:45",       # Actual time
    "event": "Boxing Results",  # Event name
}

# ──────────────────────────────────────────────────────────────
# INSTAGRAM POSTING
# ──────────────────────────────────────────────────────────────

def post_to_instagram_test(image_path, caption, dry_run=False):
    """
    Post image + caption to Instagram via instagrapi.
    Set dry_run=True to skip actual posting (just test image generation).
    """
    INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
    INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        print("❌ Instagram credentials not found in .env")
        print("   Create a .env file with:")
        print("   INSTAGRAM_USERNAME=your_email@gmail.com")
        print("   INSTAGRAM_PASSWORD=your_password")
        return False

    if dry_run:
        print(f"\n🏁 DRY RUN: Would post to Instagram with caption:")
        print(f"{'='*60}")
        print(caption)
        print(f"{'='*60}\n")
        return True

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
# MAIN TEST
# ──────────────────────────────────────────────────────────────

def main(dry_run=True):
    """
    Generate test image and post to Instagram.
    Set dry_run=False to actually post (use with caution!)
    """
    print(f"\n{'='*60}")
    print(f"🥊 TESTING: Jarrell Miller vs Lenier Pero")
    print(f"{'='*60}\n")

    # Generate branded image
    print(f"🎨 Generating test image...")
    image_path = fight_result(
        winner=TEST_FIGHT['winner'],
        loser=TEST_FIGHT['loser'],
        method=TEST_FIGHT['method'],
        round_num=TEST_FIGHT['round_num'],
        time=TEST_FIGHT['time'],
        event=TEST_FIGHT['event'],
        filename="test_miller_vs_pero.png"
    )

    print(f"✅ Image saved: {image_path}")

    # Build caption
    caption = f"""
🥊 FIGHT RESULT

{TEST_FIGHT['winner'].upper()} def. {TEST_FIGHT['loser'].upper()}
{TEST_FIGHT['method']} · {TEST_FIGHT['round_num']} · {TEST_FIGHT['time']}

📍 {TEST_FIGHT['event']}

#Boxing #FightResults #TheFightDocket
    """.strip()

    # Post to Instagram
    if dry_run:
        print(f"\n⚠️  DRY RUN MODE (won't actually post)")
        print(f"To actually post, run: python test_instagram_post.py --actual\n")

    success = post_to_instagram_test(image_path, caption, dry_run=dry_run)

    if success:
        if dry_run:
            print(f"✅ Test passed! Ready to post for real.")
        else:
            print(f"✅ Successfully posted!")
    else:
        print(f"❌ Test failed!")

    return success

if __name__ == "__main__":
    import sys
    dry_run = "--actual" not in sys.argv

    if not dry_run:
        confirm = input("\n⚠️  WARNING: This will ACTUALLY POST to Instagram. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)

    success = main(dry_run=dry_run)
    sys.exit(0 if success else 1)
