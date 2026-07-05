#!/usr/bin/env python3
"""
The Fight Docket — Live Fight Night Result Poster
Runs during Friday and Saturday night fight windows (every 90 min).
Crawls for fresh results → deduplicates → tweets → generates IG card.

Run: python post_live_result.py
Or triggered by GitHub Actions (friday-night-results.yml / saturday-night-results.yml)
"""
import os, sys, json, re, time
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

def _tok(key):
    """Get env var and strip surrounding quotes/whitespace that .env editors add."""
    return os.getenv(key, "").strip().strip("'\"")

FIRECRAWL_API_KEY    = os.getenv("FIRECRAWL_API_KEY", "")
GEMINI_API_KEY       = os.getenv("GEMINI_API_KEY", "")
TWITTER_API_KEY      = _tok("TWITTER_API_KEY")
TWITTER_API_SECRET   = _tok("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = _tok("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET= _tok("TWITTER_ACCESS_SECRET") or _tok("TWITTER_ACCESS_TOKEN_SECRET")
# Official Graph API credentials (replaces instagrapi username/password login,
# which Instagram blocks from GitHub Actions IPs)
INSTAGRAM_ACCOUNT_ID = _tok("INSTAGRAM_ACCOUNT_ID")
INSTAGRAM_PAGE_TOKEN = _tok("INSTAGRAM_PAGE_TOKEN")
FACEBOOK_PAGE_ID     = _tok("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_TOKEN  = _tok("FACEBOOK_PAGE_TOKEN")
IMGBB_API_KEY        = os.getenv("IMGBB_API_KEY", "")

for k, v in [("FIRECRAWL_API_KEY", FIRECRAWL_API_KEY), ("GEMINI_API_KEY", GEMINI_API_KEY)]:
    if not v:
        raise SystemExit(f"Missing {k}")

SCRIPT_DIR    = Path(__file__).parent
POSTED_FILE   = SCRIPT_DIR / "posted_results.json"
IG_DIR        = SCRIPT_DIR / "instagram_content"
SESSION_FILE  = IG_DIR / ".ig_session.json"
IG_DIR.mkdir(exist_ok=True)

FC_HEADERS = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"}

# NOTE: espn.com/mma/results and espn.com/boxing/results are dead (404) — removed 2026-07-05
RESULT_SOURCES = [
    "https://www.ufc.com/events",
    "https://www.sherdog.com/events/recent",
]
BOXING_SOURCES = [
    "https://www.boxingscene.com/results",
    "https://www.boxingscene.com/articles",
]


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def load_posted() -> dict:
    if POSTED_FILE.exists():
        return json.loads(POSTED_FILE.read_text(encoding="utf-8"))
    return {}


def save_posted(posted: dict):
    POSTED_FILE.write_text(json.dumps(posted, indent=2), encoding="utf-8")


def is_new(fight_id: str, posted: dict) -> bool:
    return fight_id not in posted


def mark_posted(fight_id: str, posted: dict, meta: dict):
    posted[fight_id] = {**meta, "posted_at": date.today().isoformat()}


# ---------------------------------------------------------------------------
# Crawl
# ---------------------------------------------------------------------------

def firecrawl_scrape(url: str) -> str:
    import requests
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"], "waitFor": 2000, "onlyMainContent": True},
            headers=FC_HEADERS, timeout=30
        )
        data = resp.json()
        md = (data.get("data") or {}).get("markdown", "")
        # Guard against soft-404s: error pages full of nav links, no real content
        meta = (data.get("data") or {}).get("metadata", {})
        if meta.get("statusCode") and meta["statusCode"] >= 400:
            print(f"  Warning: {url} returned HTTP {meta['statusCode']} — skipping")
            return ""
        return md
    except Exception as e:
        print(f"  Warning: crawl failed for {url}: {e}")
        return ""


def crawl_all_results() -> str:
    print("  Crawling fight result sources...")
    parts = []
    for url in RESULT_SOURCES + BOXING_SOURCES:
        content = firecrawl_scrape(url)
        if content:
            domain = url.split("/")[2]
            parts.append(f"### {domain}\n{content[:8000]}")
            print(f"    Got {len(content)} chars from {domain}")
        time.sleep(1)
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Gemini extraction
# ---------------------------------------------------------------------------

EXTRACT_PROMPT = """Extract ALL completed professional fight results from THE LAST 48 HOURS from this content.
Today's date is {today}. Include results from fights that took place yesterday or today.
Results may appear as headlines (e.g. "X halts Y in the last round", "X dominates Y to retain title").
Relative timestamps like "912h ago" are often BROKEN on these sites — do not use them to judge recency.
Judge recency by explicit fight dates, or include headline results that read as fresh news.
Return ONLY a valid JSON array. If no results found, return [].

Each result object MUST have these exact keys:
- "fight_id": string like "LastName1-vs-LastName2-YYYY-MM-DD" (use today's date if unknown)
- "winner": full fighter name
- "loser": full fighter name
- "method": one of "KO/TKO", "Submission", "Decision (Unanimous)", "Decision (Split)", "Decision (Majority)", "DQ", "No Contest"
- "round": integer (1–5 for MMA, 1–12 for boxing)
- "time": string like "3:45"
- "event": event name, e.g. "UFC 315" or "Canelo vs. Munguia 2"
- "weight_class": e.g. "Heavyweight", "Welterweight", "Super Middleweight"
- "is_main_event": boolean
- "sport": "MMA" or "Boxing"

ONLY include fights with confirmed COMPLETED results. Exclude upcoming or scheduled bouts.
If round or time is unknown, use 0 and "0:00". A missing detail (round, time, weight class)
is NOT a reason to exclude a result — include it with the unknown fields defaulted.

Content:
{content}

JSON array:"""


def extract_results(raw_content: str) -> list:
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = EXTRACT_PROMPT.replace("{today}", date.today().isoformat()).replace("{content}", raw_content[:30000])
    print("  Calling Gemini to extract results...")
    response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt])
    raw = response.text.strip()

    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw.strip())

    start, end = raw.find("["), raw.rfind("]") + 1
    if start == -1 or end == 0:
        print(f"  No results found (empty response)")
        return []

    try:
        results = json.loads(raw[start:end])
        print(f"  Extracted {len(results)} result(s)")
        return results
    except json.JSONDecodeError as e:
        print(f"  Warning: JSON parse failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Twitter
# ---------------------------------------------------------------------------

def tweet_result(result: dict) -> str | None:
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        print("  Skipping Twitter — credentials not set")
        return None

    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET,
        )

        method = result["method"]
        winner = result["winner"]
        loser  = result["loser"]
        rnd    = result["round"]
        t      = result["time"]
        event  = result["event"]
        wc     = result["weight_class"]
        main   = result.get("is_main_event", False)

        prefix = "MAIN EVENT RESULT 🏆" if main else "RESULT"
        if method in ("KO/TKO", "Submission"):
            text = f"{prefix} | {winner} def. {loser} by {method} (R{rnd}, {t}) — {event} [{wc}] #MMA #Boxing #UFC"
        else:
            text = f"{prefix} | {winner} def. {loser} by {method} — {event} [{wc}] #MMA #Boxing #UFC"

        if len(text) > 280:
            text = text[:277] + "..."

        resp = client.create_tweet(text=text)
        tweet_id = resp.data["id"]
        url = f"https://x.com/thefightdocket/status/{tweet_id}"
        print(f"  Tweeted: {text[:70]}...")
        print(f"  URL: {url}")
        return url
    except Exception as e:
        print(f"  Twitter post failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Instagram card
# ---------------------------------------------------------------------------

def generate_ig_card(result: dict) -> str | None:
    try:
        from ig_templates import fight_result as make_card
        today = date.today().strftime("%Y%m%d")
        slug  = result["fight_id"].replace(" ", "_")[:40]
        fname = f"live_result_{today}_{slug}.png"

        path = make_card(
            winner    = result["winner"],
            loser     = result["loser"],
            method    = result["method"],
            round_num = f"R{result['round']}" if result["round"] else "R?",
            time      = result["time"],
            event     = result["event"],
            filename  = fname,
        )
        print(f"  IG card saved: {fname}")
        return path
    except Exception as e:
        print(f"  IG card generation failed: {e}")
        return None


def _upload_imgbb(image_path: str) -> str | None:
    """Instagram Graph API requires a public image URL — host on ImgBB first."""
    import base64, requests
    if not IMGBB_API_KEY:
        print("  Skipping image host — IMGBB_API_KEY not set")
        return None
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        r = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY, "image": b64, "expiration": 0},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["data"]["url"]
    except Exception as e:
        print(f"  ImgBB upload failed: {e}")
        return None


def post_to_instagram(image_path: str, caption: str, img_url: str | None = None) -> bool:
    """Post via official Instagram Graph API (works from GitHub Actions IPs)."""
    import requests
    if not all([INSTAGRAM_ACCOUNT_ID, INSTAGRAM_PAGE_TOKEN]):
        print("  Skipping Instagram — Graph API credentials not set")
        return False
    img_url = img_url or _upload_imgbb(image_path)
    if not img_url:
        return False
    try:
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media",
            data={"image_url": img_url, "caption": caption, "access_token": INSTAGRAM_PAGE_TOKEN},
            timeout=30,
        )
        cid = r.json().get("id")
        if not cid:
            print(f"  IG container error: {r.json()}")
            return False

        for attempt in range(12):
            time.sleep(5)
            status = requests.get(
                f"https://graph.facebook.com/v19.0/{cid}",
                params={"fields": "status_code", "access_token": INSTAGRAM_PAGE_TOKEN},
                timeout=15,
            ).json().get("status_code", "")
            if status == "FINISHED":
                break
            if status == "ERROR":
                print("  IG container processing failed")
                return False
        else:
            print("  IG container timed out — never reached FINISHED")
            return False

        r = requests.post(
            f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
            data={"creation_id": cid, "access_token": INSTAGRAM_PAGE_TOKEN},
            timeout=30,
        )
        ok = "id" in r.json()
        print("  Posted to Instagram" if ok else f"  IG publish error: {r.json()}")
        return ok
    except Exception as e:
        print(f"  Instagram post failed (image committed for manual posting): {e}")
        return False


def post_to_facebook(image_path: str, caption: str, img_url: str | None = None) -> bool:
    """Post the same card to the Facebook page."""
    import requests
    if not all([FACEBOOK_PAGE_ID, FACEBOOK_PAGE_TOKEN]):
        print("  Skipping Facebook — Graph API credentials not set")
        return False
    img_url = img_url or _upload_imgbb(image_path)
    if not img_url:
        return False
    try:
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos",
            data={"url": img_url, "message": caption, "access_token": FACEBOOK_PAGE_TOKEN},
            timeout=30,
        )
        ok = "id" in r.json()
        print("  Posted to Facebook" if ok else f"  FB post error: {r.json()}")
        return ok
    except Exception as e:
        print(f"  Facebook post failed: {e}")
        return False


def build_ig_caption(result: dict, tweet_url: str | None) -> str:
    winner = result["winner"]
    loser  = result["loser"]
    method = result["method"]
    event  = result["event"]
    rnd    = result["round"]
    t      = result["time"]
    wc     = result["weight_class"]

    caption  = f"{winner} defeats {loser}\n"
    caption += f"{method}"
    if rnd and rnd > 0:
        caption += f" | R{rnd} {t}"
    caption += f"\n{event} • {wc}\n\n"
    caption += "#MMA #Boxing #FightNight #TheFightDocket"
    if tweet_url:
        caption += f"\n\nFull thread on X 👆"
    return caption


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 55)
    print("  The Fight Docket — Live Fight Night Results")
    print(f"  {date.today().isoformat()}")
    print("=" * 55)

    posted = load_posted()

    print("\n[1/3] Crawling for results...")
    raw_content = crawl_all_results()
    if not raw_content:
        print("  No content retrieved. Exiting.")
        return

    print("\n[2/3] Extracting results with Gemini...")
    results = extract_results(raw_content)
    if not results:
        print("  No completed results found tonight.")
        return

    new_results = [r for r in results if is_new(r["fight_id"], posted)]
    print(f"  {len(new_results)} new result(s) out of {len(results)} total")

    if not new_results:
        print("  All results already posted. Nothing to do.")
        return

    print("\n[3/3] Posting new results...")
    posted_count = 0
    for result in new_results:
        fid = result["fight_id"]
        print(f"\n  → {result['winner']} def. {result['loser']} ({result['method']})")

        tweet_url = tweet_result(result)
        card_path = generate_ig_card(result)

        if card_path:
            caption = build_ig_caption(result, tweet_url)
            img_url = _upload_imgbb(card_path)  # upload once, share across platforms
            post_to_instagram(card_path, caption, img_url)
            post_to_facebook(card_path, caption, img_url)

        mark_posted(fid, posted, {
            "winner":  result["winner"],
            "loser":   result["loser"],
            "method":  result["method"],
            "event":   result["event"],
            "tweet":   tweet_url or "",
            "card":    card_path or "",
        })
        posted_count += 1
        time.sleep(3)

    save_posted(posted)
    print(f"\n  Done — {posted_count} result(s) posted and logged.")
    print("=" * 55)
    return posted_count > 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 0)  # Never fail CI — no results tonight is not an error
