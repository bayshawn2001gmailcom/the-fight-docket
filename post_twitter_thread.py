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

from issue_selector import MAX_ISSUE_AGE_DAYS, latest_issue

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

def _tok(key):
    """Get env var, stripping whitespace/newlines/quotes that copy-paste adds."""
    return os.getenv(key, "").strip().strip("'\"")

TWITTER_API_KEY            = _tok("TWITTER_API_KEY")
TWITTER_API_SECRET         = _tok("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN       = _tok("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = _tok("TWITTER_ACCESS_TOKEN_SECRET")
GEMINI_API_KEY             = _tok("GEMINI_API_KEY")

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
    """Read the current newsletter, selected by the date in its FILENAME.

    Never sort by st_mtime — see issue_selector.py for why that shipped two
    stale threads before it was caught.
    """
    _, path = latest_issue(SCRIPT_DIR, max_age_days=MAX_ISSUE_AGE_DAYS)
    return path.name, path.read_text(encoding="utf-8")


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


def _gemini_call_with_retry(client, model, prompt, attempts=3):
    """Retry on 429/503 with backoff; raises on other errors or after exhausting attempts."""
    last_err = None
    for attempt in range(attempts):
        try:
            return client.models.generate_content(model=model, contents=[prompt])
        except Exception as e:
            msg = str(e)
            last_err = e
            if "429" in msg or "503" in msg:
                wait = 20 * (attempt + 1)
                print(f"  Gemini {msg[:30]} — retrying in {wait}s (attempt {attempt+1}/{attempts})")
                time.sleep(wait)
            else:
                raise
    raise SystemExit(f"Gemini call failed after {attempts} attempts: {last_err}")


def generate_thread(newsletter_text, ig_data):
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)

    context = f"Newsletter date: {date.today().strftime('%B %d, %Y')}\n\n"
    if ig_data.get("preview_stories"):
        context += "Top stories: " + " | ".join(ig_data["preview_stories"]) + "\n\n"
    context += f"Newsletter content:\n{newsletter_text[:8000]}"

    prompt = f"{THREAD_PROMPT}\n\n{context}\n\nGenerate the 6-tweet thread JSON array now:"

    print("  Calling Gemini to write thread...")
    response = _gemini_call_with_retry(client, "gemini-2.5-flash", prompt)
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
    newsletter_url = "https://www.thefightdocket.com/"
    tweets = [t.replace("[NEWSLETTER_URL]", newsletter_url) for t in tweets]

    # Truncate only if Gemini ignores the 240-char instruction. Cut on a sentence
    # boundary where possible and a word boundary otherwise: slicing at [:277] left
    # tweets ending mid-word ("Serious allegations for comb..."), which posts publicly
    # looking broken.
    safe = [_fit_tweet(t) for t in tweets]
    return safe


TWEET_LIMIT = 280


def _fit_tweet(t: str) -> str:
    t = t.strip()
    if len(t) <= TWEET_LIMIT:
        return t

    head = t[:TWEET_LIMIT - 1]

    # Prefer ending on a complete sentence, if that keeps enough of the tweet.
    end = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
    if end >= TWEET_LIMIT * 0.6:
        return head[:end + 1].strip()

    # Otherwise cut at the last word boundary and mark the elision.
    cut = head.rfind(" ")
    if cut <= 0:
        cut = TWEET_LIMIT - 4
    return head[:cut].rstrip(" ,;:-") + "..."


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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="write the thread to disk and print it, post nothing")
    args = parser.parse_args()

    print("=" * 55)
    print("  The Fight Docket — Twitter Thread Poster")
    print(f"  Date: {date.today().isoformat()}")
    if args.dry_run:
        print("  MODE: dry run, nothing will be posted")
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

    if args.dry_run:
        staged = SCRIPT_DIR / ".tmp" / f"thread_{name.replace('.html', '')}.txt"
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_text(
            "\n\n".join(f"[T{i}] {t}" for i, t in enumerate(tweets, 1)),
            encoding="utf-8")
        print("\n[3/3] DRY RUN — not posting. Full thread:")
        for i, t in enumerate(tweets, 1):
            print(f"\n--- T{i} ({len(t)} chars) ---\n{t}")
        print(f"\n  Staged for review: {staged}")
        print("  Post it with: python post_twitter_thread.py")
        return True

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
