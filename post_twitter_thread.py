#!/usr/bin/env python3
"""
The Fight Docket — Twitter/X Thread Poster
Reads the latest newsletter HTML → Gemini writes a 6-tweet thread → posts to @thefightdocket
Run: python post_twitter_thread.py
Or triggered by GitHub Actions (twitter_thread.yml) every Thursday 10pm EDT
"""
import os, sys, json, re, glob, requests, time
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

TWITTER_API_KEY            = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET         = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN       = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
GEMINI_API_KEY             = os.getenv("GEMINI_API_KEY", "")

for k, v in [
    ("TWITTER_API_KEY", TWITTER_API_KEY),
    ("TWITTER_API_SECRET", TWITTER_API_SECRET),
    ("TWITTER_ACCESS_TOKEN", TWITTER_ACCESS_TOKEN),
    ("TWITTER_ACCESS_TOKEN_SECRET", TWITTER_ACCESS_TOKEN_SECRET),
    ("GEMINI_API_KEY", GEMINI_API_KEY),
]:
    if not v:
        raise SystemExit(f"Missing {k}")

SCRIPT_DIR = Path(__file__).parent


# ---------------------------------------------------------------------------
# Twitter OAuth 1.0a posting (tweepy)
# ---------------------------------------------------------------------------

def get_twitter_client():
    import tweepy
    return tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
    )


def post_thread(tweets):
    """Post a list of tweet strings as a thread. Returns list of posted tweet IDs."""
    client = get_twitter_client()
    posted = []
    reply_to = None

    for i, text in enumerate(tweets):
        try:
            if reply_to:
                resp = client.create_tweet(text=text, in_reply_to_tweet_id=reply_to)
            else:
                resp = client.create_tweet(text=text)

            tweet_id = resp.data["id"]
            posted.append(tweet_id)
            reply_to = tweet_id
            print(f"  [{i+1}/{len(tweets)}] Posted: {text[:60]}...")
            time.sleep(2)

        except Exception as e:
            print(f"  [{i+1}/{len(tweets)}] FAILED: {e}")
            break

    return posted


# ---------------------------------------------------------------------------
# Newsletter reading
# ---------------------------------------------------------------------------

def load_newsletter():
    """Find and read the most recent newsletter HTML."""
    files = sorted(SCRIPT_DIR.glob("newsletter_*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None, None
    latest = files[0]
    return latest.name, latest.read_text(encoding="utf-8")


def load_ig_data():
    """Load IG/newsletter data for structured info."""
    ig_file = SCRIPT_DIR / "prompts" / "weekly_ig_data.json"
    if ig_file.exists():
        return json.loads(ig_file.read_text(encoding="utf-8"))
    return {}


def strip_html(html):
    """Strip HTML tags, return plain text."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Gemini thread generation
# ---------------------------------------------------------------------------

THREAD_PROMPT = """You are the social media voice of The Fight Docket — a premium combat sports
business intelligence newsletter (@thefightdocket on X/Twitter).

Write a 6-tweet thread based on the newsletter content below.

THREAD RULES:
- Tweet 1 (Hook): Specific, provocative opener. End with 🧵. MAX 240 chars — must end on a complete sentence.
- Tweet 2-5 (Body): Each covers one key story — business angle, specific figures, implications.
  No fluff. Each MAX 240 chars — must end on a complete sentence or thought.
- Tweet 6 (CTA): Drive to newsletter subscribe page. Include URL placeholder [NEWSLETTER_URL]. MAX 240 chars.
  Frame as "subscribe free" or "join X readers" — make the ask explicit. Add 2-3 hashtags: #MMA #Boxing #UFC etc.

FORMATTING RULES (critical):
- Plain text only. NO markdown. No **bold**, no *italic*, no underscores.
- No bullet points or dashes inside tweets.
- Each tweet must be a complete thought — never end mid-sentence.
- Count characters carefully. 240 is a hard ceiling including spaces and emoji.

TONE: Authoritative, insider. Specific $$ figures, named sources, implications.
NEVER use: "exciting", "amazing", "thrilled". No emojis except 🧵 on tweet 1 and 🥊 sparingly.

Output ONLY a JSON array of 6 strings (the tweets), no other text:
["tweet1", "tweet2", "tweet3", "tweet4", "tweet5", "tweet6"]
"""


def generate_thread(newsletter_text, ig_data):
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)

    context = f"Newsletter date: {date.today().strftime('%B %d, %Y')}\n\n"
    if ig_data.get("preview_stories"):
        context += "Top stories: " + " | ".join(ig_data["preview_stories"]) + "\n\n"
    context += f"Newsletter content:\n{newsletter_text[:8000]}"

    prompt = f"{THREAD_PROMPT}\n\n{context}\n\nGenerate the 6-tweet thread JSON array now:"

    print("  Calling Gemini to write thread...")
    response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt])
    raw = response.text.strip()

    # Strip markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw.strip())

    start = raw.find("[")
    end   = raw.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON array in Gemini response:\n{raw[:300]}")

    tweets = json.loads(raw[start:end])

    # Replace newsletter URL placeholder — points directly to subscribe page
    newsletter_url = "https://www.thefightdocket.com"
    tweets = [t.replace("[NEWSLETTER_URL]", newsletter_url) for t in tweets]

    # Hard truncate only if Gemini ignores the 240-char instruction
    safe = []
    for t in tweets:
        if len(t) > 280:
            t = t[:277] + "..."
        safe.append(t)

    return safe


# ---------------------------------------------------------------------------
# Save log
# ---------------------------------------------------------------------------

def save_log(tweets, tweet_ids, newsletter_name):
    log_file = SCRIPT_DIR / "social-log.md"
    today = date.today().isoformat()

    entry = f"\n## {today} — Twitter Thread (@thefightdocket)\n\n"
    entry += f"- Newsletter: {newsletter_name}\n"
    entry += f"- Tweets posted: {len(tweet_ids)}\n"
    if tweet_ids:
        entry += f"- Thread root: https://x.com/thefightdocket/status/{tweet_ids[0]}\n"
    entry += "\n"
    for i, (tweet, tid) in enumerate(zip(tweets, tweet_ids), 1):
        entry += f"  T{i}: {tweet[:80]}...\n"
    entry += f"\n- Status: {'✅ Posted' if len(tweet_ids) == len(tweets) else '⚠️ Partial'}\n"

    existing = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
    log_file.write_text(entry + existing, encoding="utf-8")
    print(f"  Log updated: social-log.md")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 55)
    print("  The Fight Docket — Twitter Thread Poster")
    print(f"  Date: {date.today().isoformat()}")
    print("=" * 55)

    print("\n[1/3] Loading newsletter...")
    name, html = load_newsletter()
    if not html:
        raise SystemExit("No newsletter_*.html found. Run newsletter_generator.py first.")
    print(f"  Found: {name}")

    ig_data = load_ig_data()
    newsletter_text = strip_html(html)

    print("\n[2/3] Generating thread with Gemini...")
    tweets = generate_thread(newsletter_text, ig_data)
    print(f"  Generated {len(tweets)} tweets:")
    for i, t in enumerate(tweets, 1):
        print(f"    T{i} ({len(t)} chars): {t[:70]}...")

    print("\n[3/3] Posting thread to @thefightdocket...")
    tweet_ids = post_thread(tweets)

    save_log(tweets, tweet_ids, name)

    print("\n" + "=" * 55)
    if tweet_ids:
        print(f"  DONE — {len(tweet_ids)}/{len(tweets)} tweets posted")
        print(f"  Thread: https://x.com/thefightdocket/status/{tweet_ids[0]}")
    else:
        print("  FAILED — no tweets posted. Check credentials.")
    print("=" * 55)

    return len(tweet_ids) == len(tweets)


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
