#!/usr/bin/env python3
"""
The Fight Docket — Weekly Newsletter Generator
Crawls fight news → Gemini drafts newsletter HTML + image prompts + IG content data
Run: python newsletter_generator.py
"""
import os, sys, json, re, requests, time
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

if not GEMINI_API_KEY:
    raise SystemExit("Missing GEMINI_API_KEY")

def _crawl4ai_available():
    try:
        import crawl4ai  # noqa: F401
        return True
    except ImportError:
        return False

CRAWL4AI_AVAILABLE = _crawl4ai_available()

if not FIRECRAWL_API_KEY:
    if CRAWL4AI_AVAILABLE:
        print("Warning: FIRECRAWL_API_KEY not set — using Crawl4AI for scraping")
    else:
        print("Warning: No FIRECRAWL_API_KEY and crawl4ai not installed.")
        print("  Install: pip install crawl4ai && crawl4ai-setup")

SCRIPT_DIR   = Path(__file__).parent
PROMPTS_DIR  = SCRIPT_DIR / "prompts"
PROMPTS_DIR.mkdir(exist_ok=True)

TODAY        = date.today()
_days_since_sat = (TODAY.weekday() - 5) % 7
LAST_SAT     = TODAY - timedelta(days=_days_since_sat) if _days_since_sat > 0 else TODAY
LAST_SUN     = LAST_SAT + timedelta(days=1)
ISSUE_DATE   = TODAY.strftime("%B %d, %Y").upper()
ISSUE_SLUG   = TODAY.strftime("%b%d_%Y").lower()
ISSUE_FILE   = SCRIPT_DIR / f"newsletter_{TODAY.isoformat()}.html"
PROMPTS_FILE         = PROMPTS_DIR / "weekly_prompts.json"
IG_DATA_FILE         = PROMPTS_DIR / "weekly_ig_data.json"
UPCOMING_FIGHTS_FILE = SCRIPT_DIR / "upcoming_fights.json"

FC_HEADERS = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}"}

NEWS_SOURCES = [
    "https://www.mmafighting.com/",
    "https://www.espn.com/mma/",
    "https://www.ufc.com/news",
    "https://www.boxingscene.com/",
    "https://www.sherdog.com/news/",
    "https://www.bloodyelbow.com/",
    "https://www.ringtv.com/",
    "https://www.badlefthook.com/",
    "https://www.mixedmartialarts.com/",
    "https://www.fightnews.com/",
]


# ---------------------------------------------------------------------------
# Crawling
# ---------------------------------------------------------------------------

def firecrawl_scrape(url):
    """Returns content string, or None on 402 (credits exhausted)."""
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "removeBase64Images": True,
                "excludeTags": ["nav", "footer", "aside", "header", "form", "script", "style"],
                "maxAge": 86400000,
            },
            headers=FC_HEADERS,
            timeout=30,
        )
        if resp.status_code == 402:
            return None
        resp.raise_for_status()
        data = resp.json()
        return (data.get("data") or {}).get("markdown", "") or data.get("markdown", "")
    except Exception as e:
        print(f"  Firecrawl failed for {url}: {e}")
        return ""


def crawl4ai_scrape(url):
    """Crawl4AI fallback — free, no credits."""
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler
        async def _run():
            async with AsyncWebCrawler(headless=True) as crawler:
                r = await crawler.arun(url=url, only_text=True, word_count_threshold=10)
                return r.markdown or ""
        return asyncio.run(_run())
    except Exception as e:
        print(f"  Crawl4AI failed for {url}: {e}")
        return ""


def crawl_news():
    chunks = []
    use_fallback = not bool(FIRECRAWL_API_KEY)
    for url in NEWS_SOURCES:
        print(f"  Crawling {url}...")
        if use_fallback:
            content = crawl4ai_scrape(url)
        else:
            content = firecrawl_scrape(url)
            if content is None:
                print("  Firecrawl credits exhausted — switching to Crawl4AI")
                use_fallback = True
                content = crawl4ai_scrape(url)
        if content:
            chunks.append(f"=== {url} ===\n{content[:3000]}\n")
        time.sleep(0.5)
    return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Upcoming fights loader (Friday crawler output — authoritative source)
# ---------------------------------------------------------------------------

def load_upcoming_fights():
    """Load upcoming_fights.json written by friday-crawl-fights.yml.
    Returns a formatted text block used as the exclusive source for Fight Card Previews."""
    if not UPCOMING_FIGHTS_FILE.exists():
        return ""
    try:
        with open(UPCOMING_FIGHTS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        crawled_at = data.get("crawled_at", "")[:10]
        lines = [f"CONFIRMED UPCOMING FIGHTS (crawled {crawled_at}, verified by Friday crawler):"]
        found_any = False
        for sport, key in [("UFC / MMA", "ufc"), ("Boxing", "boxing")]:
            fights = data.get(key, [])
            if not fights:
                continue
            lines.append(f"\n{sport}:")
            for fight in fights:
                parts = []
                if fight.get("fighter1") and fight.get("fighter2"):
                    parts.append(f"{fight['fighter1']} vs {fight['fighter2']}")
                if fight.get("event"):
                    parts.append(fight["event"])
                if fight.get("date"):
                    parts.append(fight["date"])
                if fight.get("venue") and fight.get("city"):
                    parts.append(f"{fight['venue']}, {fight['city']}")
                elif fight.get("city"):
                    parts.append(fight["city"])
                if fight.get("weight_class"):
                    parts.append(fight["weight_class"])
                if fight.get("is_title_fight"):
                    parts.append("TITLE FIGHT")
                lines.append(f"  - {' | '.join(parts)}")
                found_any = True
        return "\n".join(lines) if found_any else ""
    except Exception as e:
        print(f"  Could not load upcoming_fights.json: {e}")
        return ""


# ---------------------------------------------------------------------------
# Perplexity Sonar -- real-time supplemental news search
# ---------------------------------------------------------------------------

# (query, max_tokens) — legal/results queries get more room to be thorough
PERPLEXITY_QUERIES = [
    # Q1: MMA news
    ("What are the biggest MMA fight results and news from the past 7 days? Include fight results, fighter news, contract signings, and promotional announcements.", 600),
    # Q2: Boxing news
    ("What are the biggest professional boxing fight results and news from the past 7 days? Include title fights, results, upcoming cards, and fighter moves.", 600),
    # Q3: Federal courts and PACER — active combat sports litigation
    ("What are the latest federal court filings, PACER docket updates, and legal developments in combat sports from the past 7 days? Include active cases involving UFC, TKO Group, Top Rank, Matchroom, Golden Boy, PFL, and any fighters. Include case numbers, courts, and filing dates where available. Check for new complaints, motions, rulings, and settlements.", 1000),
    # Q4: Athletic commissions — NYSAC, CSAC, NSAC decisions
    ("What are the latest decisions, suspensions, license denials, and regulatory actions from the New York State Athletic Commission (NYSAC), California State Athletic Commission (CSAC), and Nevada State Athletic Commission (NSAC) in the past 7 days? Include any fighter suspensions, drug test results (USADA/VADA), and hearing outcomes.", 1000),
    # Q5: Combat sports business intelligence
    ("What is the latest combat sports business and financial news from the past 7 days? Include media rights deals, TV ratings, PPV buyrate estimates, sponsor announcements, promoter acquisitions, venue contracts, broadcast rights negotiations, and fighter pay disputes.", 600),
    # Q6: Weekend results — exhaustive, date-anchored
    (f"List ALL combat sports fight results from {LAST_SAT.strftime('%B %d')} and {LAST_SUN.strftime('%B %d, %Y')} this past weekend. Include EVERY title fight, main event, and co-main event — winner, method of victory, round, and time. Cover boxing and MMA. Be exhaustive.", 1000),
    # Q7: Confirmed upcoming fights — future only, strict date filter
    (f"What professional boxing and MMA fights are officially announced and confirmed for dates STRICTLY AFTER {TODAY.strftime('%B %d, %Y')}? For each fight list: exact confirmed date, event name, venue and city, both fighters' full names, weight class, and whether it is a title fight. CRITICAL: Only include fights that have NOT yet taken place as of {TODAY.strftime('%B %d, %Y')}. Do NOT include past results, fights that already occurred, or unconfirmed rumors.", 800),
]


def perplexity_search():
    if not PERPLEXITY_API_KEY:
        print("  Perplexity key not set -- skipping")
        return ""
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    chunks = []
    for i, (query, max_tokens) in enumerate(PERPLEXITY_QUERIES, 1):
        print(f"  Perplexity query {i}/{len(PERPLEXITY_QUERIES)}...")
        try:
            resp = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": query}],
                    "max_tokens": max_tokens,
                },
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])
            citation_str = "\n".join(f"  - {c}" for c in citations[:5])
            chunks.append(f"=== Perplexity: {query[:60]}... ===\n{answer}\nSources: {citation_str}\n")
        except Exception as e:
            print(f"  Perplexity query {i} failed: {e}")
        time.sleep(1)
    return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""You are the editor of The Fight Docket — an institutional-grade combat sports intelligence newsletter covering the financial, legal, and operational drivers of MMA and professional boxing.

EDITORIAL PRIORITY RULE: If any major boxing or MMA title fight, championship bout, or marquee main event occurred in the past 72 hours, it MUST be the main_story. Recent fight results ARE business intelligence — a title change reshuffles the entire promotional landscape. Do NOT lead with a business or legal story when a major fight result exists in the source data. Only override if the business/legal story is of once-in-a-decade significance.

VOICE: Authoritative, unbiased. Strategic framing — every story is about what it means operationally or financially. Technical precision: case numbers, dollar figures, contract terms. First-person analytical: "My read is...", "The filing reveals...", "What this signals to the market is..." No promotional language. No "exciting" or "amazing". Benchmark: Bloomberg Businessweek meets legal trade press, applied to combat sports.

DARK THEME: ALL inline HTML styles must use color:#F2F2E8 for body text, color:#888888 for secondary text, color:#DE1E20 for links and labels, color:#F2F2E8 for bold. Do NOT use dark text like #333 — invisible on dark background.

FIGHT CARD PREVIEWS — MANDATORY ACCURACY RULE:
The FIGHT CARD PREVIEWS section MUST use ONLY fights that appear in the "CONFIRMED UPCOMING FIGHTS" data block passed to you. Fight announcement web pages found in crawled news content are NOT reliable for this section — those pages stay indexed on the internet for months or years after the fight has already taken place. A crawled page announcing a fight is NOT proof that fight is upcoming.
Rules you must follow:
(1) Only write Fight Card Preview entries for fights explicitly listed in the CONFIRMED UPCOMING FIGHTS block.
(2) NEVER include a fight whose date has already passed as of {TODAY.strftime("%B %d, %Y")}.
(3) NEVER include a fighter who is retired or has announced retirement.
(4) If the CONFIRMED UPCOMING FIGHTS block is empty or has no fights scheduled within the next 30 days, write exactly this in the Fight Card Previews section: "No major fights are confirmed for the coming week as of press time. Check thefightdocket.com Friday evening for the full card breakdown."
(5) Do NOT fabricate matchups, dates, venues, or event names.

TODAY: {TODAY.strftime("%B %d, %Y")}

Based on the crawled news, write this week's full newsletter. Output ONLY valid JSON:

{{
  "newsletter_html": "<complete HTML>",
  "image_prompts": [
    {{"section": "intro",         "topic": "15-word topic",  "prompt": "cinematic image prompt, no faces, no logos, dark editorial atmosphere"}},
    {{"section": "main_story",    "topic": "15-word topic",  "prompt": "..."}},
    {{"section": "fight_previews","topic": "15-word topic",  "prompt": "..."}},
    {{"section": "business_intel","topic": "15-word topic",  "prompt": "..."}}
  ],
  "ig_data": {{
    "date":  "MAY 9, 2026",
    "issue": "may09_2026",
    "preview_stories": ["story 1 under 80 chars", "story 2", "story 3"],
    "announcement": {{
      "fighter1": "Last Name", "fighter2": "Last Name",
      "event": "UFC 329", "date": "July 11 · Las Vegas, NV",
      "weight_class": "Welterweight", "filename": "f1_vs_f2_announcement.png"
    }},
    "result": {{
      "winner": "Name", "loser": "Name", "method": "KO/TKO",
      "round_num": "R2", "time": "3:45", "event": "UFC Fight Night",
      "filename": "name_result.png"
    }},
    "quote": {{
      "quote": "Pull quote under 120 chars", "attribution": "Person Name",
      "context": "Event context", "filename": "quote_card.png"
    }}
  }}
}}

For newsletter_html use EXACTLY this dark-branded structure (preserve ALL inline styles):

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="dark">
<title>The Fight Docket | {TODAY.strftime("%B %d, %Y").upper()}</title>
<style>
  body {{ margin:0; padding:0; background-color:#0D0D0D !important; }}
  p {{ margin:0 0 18px 0; color:#F2F2E8; font-size:16px; line-height:1.8; }}
  a {{ color:#DE1E20; text-decoration:none; }}
  strong, b {{ color:#F2F2E8; }}
  h2, h3 {{ color:#F2F2E8; }}
</style>
</head>
<body style="margin:0; padding:0; background-color:#0D0D0D;">
<div style="max-width:680px; margin:0 auto; background-color:#0D0D0D; font-family:Georgia,'Times New Roman',serif; color:#F2F2E8;">

  <!-- HEADER -->
  <div style="background:#0D0D0D; border-top:6px solid #DE1E20; padding:36px 40px 28px 40px;">
    <p style="margin:0 0 1px 0; font-family:Arial,Helvetica,sans-serif; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:8px; color:#C5A059;">The</p>
    <div style="font-family:Arial Black,Impact,Helvetica,sans-serif; font-size:56px; font-weight:900; text-transform:uppercase; color:#F2F2E8; line-height:0.95; letter-spacing:-2px; margin:0 0 16px 0;">FIGHT<br>DOCKET</div>
    <div style="height:1px; background:#C5A059; margin:0 0 12px 0;"></div>
    <p style="margin:0 0 4px 0; font-family:Arial,Helvetica,sans-serif; font-size:10px; text-transform:uppercase; letter-spacing:4px; color:#C5A059;">Boxing &middot; MMA &middot; The Stories Behind The Sport</p>
    <p style="margin:0; font-family:Arial,Helvetica,sans-serif; font-size:11px; text-transform:uppercase; letter-spacing:2px; color:#555;">{TODAY.strftime("%B %d, %Y").upper()}</p>
  </div>

  <!-- CONTENT -->
  <div style="padding:0 40px 48px 40px;">

    <!-- EDITOR'S NOTE -->
    <div style="padding-top:40px;">
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#C5A059;">Editor's Note</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      [IMAGE_PLACEHOLDER_intro]
      <div style="color:#F2F2E8;">[3 paragraphs of editorial context — personal tone ("My read..."), sets the week's themes. Each <p> must have style='color:#F2F2E8;']</div>
    </div>

    <div style="height:1px; background:#1E1E1E; border-top:1px solid #C5A059; opacity:0.25; margin:40px 0;"></div>

    <!-- MAIN STORY -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Main Story</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      [IMAGE_PLACEHOLDER_main_story]
      <h2 style="font-family:Arial Black,Impact,Helvetica,sans-serif; font-size:28px; font-weight:900; line-height:1.2; margin:0 0 22px 0; letter-spacing:-0.5px; color:#F2F2E8; text-transform:uppercase;">[HEADLINE]</h2>
      <div style="color:#F2F2E8;">[4-5 paragraphs of deep analytical reporting. Each <p> must have style='color:#F2F2E8;']</div>
    </div>

    <div style="height:1px; background:#C5A059; opacity:0.2; margin:40px 0;"></div>

    <!-- LEGAL TRACKER -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Legal Tracker</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      [IMAGE_PLACEHOLDER_legal]
      <p style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:2px; color:#DE1E20; margin:0 0 20px 0;">Active Federal Cases</p>
      [For each active case: <p style='margin:0 0 20px 0; color:#F2F2E8;'><strong style='color:#F2F2E8;'>CASE NAME (COURT NO.)</strong><br><span style='color:#888;'>Last activity: DATE</span> — analytical description<br><em style='color:#888;'>Status: phrase</em></p>. If no new activity, one analytical sentence on the Johnson v. Zuffa antitrust (D. Nev. 2:21-cv-01189) state of play. Also include any NYSAC/CSAC/NSAC suspensions or USADA/VADA results from this week.]
    </div>

    <div style="height:1px; background:#C5A059; opacity:0.2; margin:40px 0;"></div>

    <!-- RUMOR MILL -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Rumor Mill</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      [IMAGE_PLACEHOLDER_rumor]
      [2-3 rumor items. HIGH confidence (#C5A059), MEDIUM (#888888), LOW (#444444). Format each as:
      <div style='border-left:3px solid COLOR; padding:4px 0 4px 18px; margin-bottom:28px;'>
        <p style='font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:3px; color:COLOR; margin:0 0 10px 0;'>CONFIDENCE — 0.XX</p>
        <p style='margin:0; color:#F2F2E8; line-height:1.8;'>Rumor text. Name the source publication or flag as unverified.</p>
      </div>]
    </div>

    <div style="height:1px; background:#C5A059; opacity:0.2; margin:40px 0;"></div>

    <!-- FIGHT CARD PREVIEWS -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Fight Card Previews</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      [IMAGE_PLACEHOLDER_fight_previews]
      <h2 style="font-family:Arial Black,Impact,Helvetica,sans-serif; font-size:22px; font-weight:900; line-height:1.2; margin:0 0 20px 0; letter-spacing:-0.5px; color:#F2F2E8; text-transform:uppercase;">What's on Deck</h2>
      <div style="color:#F2F2E8;">[2-3 fights. Use <strong style='color:#DE1E20;'>Fighter vs Fighter (Date)</strong> subheads. Odds context and what each fight means for rankings and promoter economics. Each <p> must have style='color:#F2F2E8;']</div>
    </div>

    <div style="height:1px; background:#C5A059; opacity:0.2; margin:40px 0;"></div>

    <!-- BUSINESS INTEL -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Business Intel</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      [IMAGE_PLACEHOLDER_business_intel]
      <h2 style="font-family:Arial Black,Impact,Helvetica,sans-serif; font-size:22px; font-weight:900; line-height:1.2; margin:0 0 20px 0; letter-spacing:-0.5px; color:#F2F2E8; text-transform:uppercase;">[HEADLINE]</h2>
      <div style="color:#F2F2E8;">[3-4 paragraphs on media rights, TV ratings, PPV buyrates, contracts, fighter pay, promoter moves. Each <p> must have style='color:#F2F2E8;']</div>
    </div>

    <div style="height:1px; background:#C5A059; opacity:0.2; margin:40px 0;"></div>

    <!-- FIGHTER SPOTLIGHT -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Fighter Spotlight</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      [IMAGE_PLACEHOLDER_fighter_spotlight]
      <h2 style="font-family:Arial Black,Impact,Helvetica,sans-serif; font-size:22px; font-weight:900; line-height:1.2; margin:0 0 20px 0; letter-spacing:-0.5px; color:#F2F2E8; text-transform:uppercase;">[FIGHTER NAME]</h2>
      <div style="color:#F2F2E8;">[400 words on one fighter's career arc, earnings trajectory, and what fight makes commercial and competitive sense next. Each <p> must have style='color:#F2F2E8;']</div>
    </div>

  </div>

  <!-- FOOTER -->
  <div style="border-top:1px solid #C5A059; background:#0D0D0D; padding:32px 40px 36px 40px;">
    <p style="margin:0 0 2px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:6px; color:#C5A059;">The Fight Docket</p>
    <p style="margin:0 0 16px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; text-transform:uppercase; letter-spacing:3px; color:#888888;">Boxing &middot; MMA &middot; The Stories Behind The Sport</p>
    <p style="margin:0 0 6px 0; font-family:Arial,Helvetica,sans-serif; font-size:13px; color:#888888;">
      <a href="https://www.thefightdocket.com/" style="color:#DE1E20; text-decoration:none;">www.thefightdocket.com</a>
      &nbsp;&middot;&nbsp;
      Tips &amp; sources: <a href="mailto:tips@thefightdocket.com" style="color:#DE1E20; text-decoration:none;">tips@thefightdocket.com</a>
    </p>
    <p style="margin:12px 0 0 0; font-family:Arial,Helvetica,sans-serif; font-size:11px; color:#777777;">You're receiving this because you subscribed. Forward to a fight fan who thinks like an analyst.</p>
    <p style="margin:6px 0 0 0; font-family:Arial,Helvetica,sans-serif; font-size:11px; color:#777777;">Not subscribed yet? Join free &rarr; <a href="https://www.thefightdocket.com/" style="color:#DE1E20; text-decoration:none;">www.thefightdocket.com</a></p>
  </div>

</div>
</body>
</html>
"""


GEMINI_MODELS = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]


def build_newsletter(news_content, upcoming_fights_data=""):
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)

    if upcoming_fights_data:
        upcoming_block = f"\n\n{upcoming_fights_data}"
    else:
        upcoming_block = (
            "\n\nCONFIRMED UPCOMING FIGHTS: None available — upcoming_fights.json was not found "
            "or the Friday crawler has not run yet. For the Fight Card Previews section, use ONLY "
            "fights confirmed by the Q7 Perplexity query above. If none are confirmed, write: "
            "'No major fights are confirmed for the coming week as of press time. Check "
            "thefightdocket.com Friday evening for the full card breakdown.'"
        )

    prompt = f"""{SYSTEM_PROMPT}
{upcoming_block}

CRAWLED NEWS CONTENT (use this as source material — {len(news_content):,} chars):
{news_content[:24000]}

Generate the newsletter JSON now:"""

    last_err = None
    for model in GEMINI_MODELS:
        for attempt in range(2):
            print(f"  Calling Gemini ({model}, attempt {attempt+1})...")
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[prompt],
                    config={"response_mime_type": "application/json"},
                )
                return json.loads(response.text)
            except json.JSONDecodeError as e:
                print(f"  JSON parse error: {e} — retrying")
                last_err = e
            except Exception as e:
                msg = str(e)
                if "429" in msg or "503" in msg:
                    wait = 30 * (attempt + 1)
                    print(f"  Rate limit ({model}): retrying in {wait}s")
                    time.sleep(wait)
                else:
                    print(f"  Error ({model}): {msg[:120]}")
                    last_err = e
                    break
        time.sleep(5)

    raise SystemExit(f"Newsletter generation failed. Last error: {last_err}")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

LAST_IMAGES_FILE = PROMPTS_DIR / "last_generated_images.json"
IMG_STYLE = 'width:100%; max-width:600px; display:block; margin:0 0 28px 0; border:1px solid #1E1E1E;'

PLACEHOLDER_SECTIONS = {
    "[IMAGE_PLACEHOLDER_intro]":         "intro",
    "[IMAGE_PLACEHOLDER_main_story]":    "main_story",
    "[IMAGE_PLACEHOLDER_fight_previews]":"fight_previews",
    "[IMAGE_PLACEHOLDER_business_intel]":"business_intel",
}


def inject_images(html):
    """Replace [IMAGE_PLACEHOLDER_*] tags with <img> tags from last_generated_images.json."""
    if not LAST_IMAGES_FILE.exists():
        print("  No last_generated_images.json — placeholders left as-is")
        return html

    with open(LAST_IMAGES_FILE) as f:
        img_data = json.load(f)

    url_map = {item["section"]: item["url"] for item in img_data.get("images", [])}
    replaced = 0
    for placeholder, section in PLACEHOLDER_SECTIONS.items():
        url = url_map.get(section)
        if url:
            img_tag = f'<img src="{url}" alt="{section}" style="{IMG_STYLE}">'
            html = html.replace(placeholder, img_tag)
            replaced += 1
        else:
            html = html.replace(placeholder, "")
    print(f"  Images      : {replaced}/4 placeholders replaced")
    return html


def write_outputs(data):
    # Newsletter HTML — inject images then save
    html = inject_images(data["newsletter_html"])
    ISSUE_FILE.write_text(html, encoding="utf-8")
    print(f"  Newsletter  : {ISSUE_FILE.name}")

    # Image prompts
    PROMPTS_FILE.write_text(
        json.dumps({"issue_date": TODAY.isoformat(), "prompts": data["image_prompts"]}, indent=2),
        encoding="utf-8",
    )
    print(f"  Prompts     : {PROMPTS_FILE.name}")

    # IG data
    IG_DATA_FILE.write_text(json.dumps(data["ig_data"], indent=2), encoding="utf-8")
    print(f"  IG data     : {IG_DATA_FILE.name}")


def _already_generated_upstream() -> bool:
    """Check origin/main for today's issue file before burning Firecrawl/Perplexity/Gemini
    calls on a duplicate local run. Never blocks on network/git failure — only blocks on a
    confirmed match. Bypass with FORCE_REGENERATE=1."""
    import subprocess
    if os.getenv("FORCE_REGENERATE"):
        return False
    try:
        subprocess.run(["git", "fetch", "origin", "main", "--quiet"], cwd=SCRIPT_DIR,
                        timeout=20, check=False)
        result = subprocess.run(
            ["git", "cat-file", "-e", f"origin/main:{ISSUE_FILE.name}"],
            cwd=SCRIPT_DIR, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def main():
    print("=" * 55)
    print("  The Fight Docket — Newsletter Generator")
    print(f"  Issue: {ISSUE_DATE}")
    print("=" * 55)

    if _already_generated_upstream():
        raise SystemExit(
            f"\n{ISSUE_FILE.name} already exists on origin/main — GitHub Actions has already "
            f"generated this issue. Skipping to avoid duplicate Firecrawl/Perplexity/Gemini "
            f"calls. Run `git pull` to get it locally, or set FORCE_REGENERATE=1 to regenerate "
            f"anyway."
        )

    print("\n[1/4] Loading confirmed upcoming fights...")
    upcoming_fights_data = load_upcoming_fights()
    if upcoming_fights_data:
        fight_lines = upcoming_fights_data.count("\n") + 1
        print(f"  Upcoming fights: loaded ({fight_lines} lines from upcoming_fights.json)")
    else:
        print("  Upcoming fights: upcoming_fights.json not found or empty")
        print("  (Fight Card Previews will rely on Q7 Perplexity query only)")

    print(f"\n[2/4] Querying Perplexity Sonar ({len(PERPLEXITY_QUERIES)} queries)...")
    perplexity_content = perplexity_search()
    if perplexity_content:
        print(f"  Perplexity  : {len(perplexity_content):,} chars")
    else:
        print("  Perplexity  : skipped (no key or all queries failed)")

    print("\n[3/4] Scraping news sources (Firecrawl → Crawl4AI fallback)...")
    scraped_content = crawl_news()
    if scraped_content:
        print(f"  Scraped     : {len(scraped_content):,} chars")
    else:
        print("  Scraped     : nothing returned")

    news_content = "\n\n".join(filter(None, [perplexity_content, scraped_content]))
    if not news_content.strip():
        raise SystemExit("ERROR: All sources returned empty. Check API keys and network.")

    print("\n[4/4] Generating newsletter with Gemini...")
    data = build_newsletter(news_content, upcoming_fights_data)

    print("\n[5/5] Writing outputs...")
    write_outputs(data)

    print("\n" + "=" * 55)
    print("  DONE")
    print(f"  Newsletter : {ISSUE_FILE.name}")
    print(f"  Prompts    : prompts/weekly_prompts.json  (triggers image generation)")
    print(f"  IG data    : prompts/weekly_ig_data.json  (used by ig_content_generator.py)")
    print("=" * 55)


if __name__ == "__main__":
    main()
