#!/usr/bin/env python3
"""
The Fight Docket — Newsletter Draft Generator (WAT Framework)
Crawls 9 news sources → Gemini 2.5 Pro writes structured JSON draft with 7 sections.

Output:
  .tmp/newsletter_draft_YYYY-MM-DD.json  — main structured draft
  .tmp/weekly_prompts_YYYY-MM-DD.json    — 8 Nano Banana image prompts (incl. thumbnail)
  .tmp/weekly_ig_data_YYYY-MM-DD.json    — Instagram metadata

Run: python tools/newsletter_draft.py
"""
import os, sys, json, time
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

FIRECRAWL_API_KEY  = os.getenv("FIRECRAWL_API_KEY", "")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

if not FIRECRAWL_API_KEY:
    raise SystemExit("Missing FIRECRAWL_API_KEY")
if not GEMINI_API_KEY:
    raise SystemExit("Missing GEMINI_API_KEY")

TMP_DIR = ROOT / ".tmp"
TMP_DIR.mkdir(exist_ok=True)

_arg_date = sys.argv[1] if len(sys.argv) > 1 else None
TODAY        = date.fromisoformat(_arg_date) if _arg_date else date.today()
DATE_DISPLAY = TODAY.strftime("%B %d, %Y").upper()
DATE_SLUG    = TODAY.strftime("%b%d_%Y").lower()
DATE_ISO     = TODAY.isoformat()

# Compute previous Saturday and Sunday for targeted weekend-results query
_days_since_sat = (TODAY.weekday() - 5) % 7
LAST_SAT = TODAY - timedelta(days=_days_since_sat) if _days_since_sat > 0 else TODAY
LAST_SUN = LAST_SAT + timedelta(days=1)

DRAFT_FILE   = TMP_DIR / f"newsletter_draft_{DATE_ISO}.json"
PROMPTS_FILE = TMP_DIR / f"weekly_prompts_{DATE_ISO}.json"
IG_FILE      = TMP_DIR / f"weekly_ig_data_{DATE_ISO}.json"

import requests

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

GEMINI_MODELS = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]


# ---------------------------------------------------------------------------
# Crawling
# ---------------------------------------------------------------------------

def firecrawl_scrape(url: str) -> str:
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
        resp.raise_for_status()
        data = resp.json()
        return (data.get("data") or {}).get("markdown", "") or data.get("markdown", "")
    except Exception as e:
        msg = str(e)
        if "402" in msg or "Payment Required" in msg:
            return None  # Signal to caller: use fallback
        print(f"  Firecrawl failed for {url}: {e}")
        return ""


_CRAWL4AI_SCRIPT = """\
import asyncio, json, sys
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

url = sys.argv[1]

async def run():
    cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url, config=cfg)
        if result.success and result.markdown:
            md = result.markdown
            # raw_markdown is the full content; fit_markdown requires extra filter config
            text = str(getattr(md, "raw_markdown", None) or md)
            print(json.dumps(text))
        else:
            print(json.dumps(""))

asyncio.run(run())
"""

def crawl4ai_scrape(url: str) -> str:
    import json, subprocess, sys, tempfile, pathlib

    # Write helper script to a temp file — avoids async def / semicolon clash in -c
    tmp = pathlib.Path(tempfile.gettempdir()) / "_crawl4ai_runner.py"
    tmp.write_text(_CRAWL4AI_SCRIPT, encoding="utf-8")
    try:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"   # prevents Rich logger CP1252 crash on Windows
        proc = subprocess.run(
            [sys.executable, str(tmp), url],
            capture_output=True, text=True, timeout=60, env=env,
        )
        # stdout may contain crawl4ai log lines before the JSON result
        for line in reversed(proc.stdout.strip().splitlines()):
            line = line.strip()
            if line.startswith('"'):
                return json.loads(line)
        return ""
    except Exception as e:
        print(f"  Crawl4AI failed for {url}: {e}")
        return ""


def crawl_news() -> str:
    chunks = []
    use_fallback = False
    for url in NEWS_SOURCES:
        print(f"  Crawling {url}...")
        if use_fallback:
            content = crawl4ai_scrape(url)
        else:
            content = firecrawl_scrape(url)
            if content is None:  # 402 — switch all remaining to Crawl4AI
                print("  Firecrawl credits exhausted — switching to Crawl4AI")
                use_fallback = True
                content = crawl4ai_scrape(url)
        if content:
            chunks.append(f"=== {url} ===\n{content[:3000]}\n")
        time.sleep(0.5)
    return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Perplexity Sonar — real-time supplemental news search
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
]


def perplexity_search() -> str:
    if not PERPLEXITY_API_KEY:
        print("  Perplexity key not set — skipping")
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
# Gemini prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""You are the editor of The Fight Docket — an institutional-grade combat sports intelligence newsletter covering the financial, legal, and operational drivers of MMA and professional boxing.

EDITORIAL PRIORITY RULE: If any major boxing or MMA title fight, championship bout, or marquee main event occurred in the past 72 hours (i.e., this past Saturday or Sunday), it MUST be the main_story. Recent fight results ARE business intelligence — a title change reshuffles the entire promotional landscape, disrupts rankings, and realigns negotiating leverage across promoters, broadcasters, and managers. Do NOT lead with a business or legal story when a major fight result exists in the source data. Only override this rule if the business/legal story is of once-in-a-decade significance (e.g., a landmark antitrust ruling, a promoter acquisition closing).

MISSION: Provide definitive, institutional-grade analysis of combat sports. Target audience: industry professionals, analysts, promoters, agents, and institutional-level stakeholders who need precise, sourced intelligence — not fan coverage.

VOICE:
- Authoritative and unbiased. Never hedging, never hype.
- Strategic framing: every story is about what it means operationally or financially, not just what happened.
- Technical precision: case numbers, dollar figures, contract terms, record stats — specifics are credibility.
- First-person analytical: "My read is...", "The filing reveals...", "What this signals to the market is..."
- No promotional language. No "exciting" or "amazing". Precise adjectives only.
- Benchmark: Bloomberg Businessweek meets legal trade press, applied to combat sports.

DARK THEME: The newsletter renders on a dark (#0D0D0D) background. ALL inline HTML styles must use:
- Body text: color:#F2F2E8
- Secondary/meta text: color:#888888
- Links: color:#DE1E20
- Bold/emphasis: color:#F2F2E8
- Callouts or case labels: color:#DE1E20
Do NOT use dark text colors like #333 or #1a1a1a — they will be invisible on the dark background.

TODAY: {DATE_DISPLAY}

Based on the crawled news content, write this week's full newsletter. Output ONLY valid JSON with this exact structure — no markdown, no code fences, just JSON:

{{
  "editors_note_html": "<p style='color:#F2F2E8'>...</p>",
  "main_story_headline": "Specific, institutional headline — max 80 chars. Named parties, dollar amounts, case numbers when available.",
  "main_story_html": "<p style='color:#F2F2E8'>...</p>",
  "legal_tracker_headline": "...",
  "legal_tracker_html": "...",
  "has_legal_content": true,
  "rumor_mill_html": "...",
  "fight_previews_headline": "What's on Deck",
  "fight_previews_html": "<p style='color:#F2F2E8'>...</p>",
  "business_intel_headline": "...",
  "business_intel_html": "<p style='color:#F2F2E8'>...</p>",
  "fighter_spotlight_name": "Fighter Full Name",
  "fighter_spotlight_html": "<p style='color:#F2F2E8'>...</p>",
  "image_prompts": [
    {{"section": "thumbnail",         "topic": "Newsletter cover image — main story hook", "prompt": "Wide editorial thumbnail image: [describe the main story's visual hook — e.g. two boxing legends in dramatic pre-fight staredown, or streaming screens over an empty arena, or a fighter silhouette holding a championship belt]. Cinematic banner composition, dramatic arena spotlight lighting, black background (#0D0D0D), deep crimson red (#DE1E20) and gold (#C5A059) color palette, premium sports magazine cover style, high contrast. No faces clearly visible, no text, no logos, no watermarks."}},
    {{"section": "intro",             "topic": "MMA and boxing combat sports intelligence", "prompt": "Two MMA fighters squaring off in an octagon, dramatic silhouette, cinematic arena lighting from above, black background (#0D0D0D), deep crimson red (#DE1E20) and gold (#C5A059) color palette, dark editorial atmosphere, premium sports magazine style. No faces visible, no text, no logos."}},
    {{"section": "main_story",        "topic": "...", "prompt": "If the story features specific named fighters or people, show their face(s) in a dramatic editorial portrait — intense expression, cinematic arena lighting, black background with deep red and gold accents. If no specific person, use abstract combat sports imagery. No text, no logos."}},
    {{"section": "legal",             "topic": "Legal proceedings combat sports", "prompt": "Gavel and legal documents reimagined through a combat sports lens. Black background, gold and deep red palette, dramatic shadows, premium editorial style. No text, no faces, no logos."}},
    {{"section": "rumor",             "topic": "Combat sports intelligence", "prompt": "Shadowy atmospheric scene, dark fight gym or press room, whisper aesthetic, cinematic noir, dramatic directional lighting, black and gold palette. No faces, no text."}},
    {{"section": "fight_previews",    "topic": "...", "prompt": "When previewing a specific fight, show both fighters in a dramatic face-off or staredown — intense expressions, dramatic arena lighting, black background with deep red and gold accents. No text, no logos."}},
    {{"section": "business_intel",    "topic": "...", "prompt": "Abstract representation of combat sports business — broadcast equipment, contracts, arena infrastructure, financial scale. Black background, deep red and gold palette, premium editorial style. No faces, no text, no logos."}},
    {{"section": "fighter_spotlight", "topic": "Fighter Name career arc", "prompt": "Dramatic close-up portrait of the featured fighter — intense expression and focus, cinematic arena lighting, premium sports magazine editorial aesthetic. Black background with deep red and gold light. No text, no logos."}}
  ],
  "ig_data": {{
    "date":  "{DATE_DISPLAY}",
    "issue": "{DATE_SLUG}",
    "preview_stories": ["story 1 under 80 chars", "story 2 under 80 chars", "story 3 under 80 chars"],
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

SECTION REQUIREMENTS:
- editors_note_html: 3 paragraphs. Personal tone, but analytically grounded. Sets the institutional lens for the week.
- main_story_html: 600-800 words, 4-5 paragraphs. Your most important financial/legal/operational story. Deepest analytical reporting.
- legal_tracker_html: see format below
- rumor_mill_html: see format below
- fight_previews_html: 2-3 upcoming fights, 150-200 words per fight. Odds context and what each fight means for rankings/promoter economics.
- business_intel_html: 3-4 paragraphs on media rights, contracts, TV numbers, promoter moves, financial disclosures.
- fighter_spotlight_html: 400 words on one fighter's career arc, earnings trajectory, and what fight makes commercial and competitive sense next.

LEGAL TRACKER FORMAT for legal_tracker_html:
<p style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:2px; color:#DE1E20; margin:0 0 20px 0;">Active Federal Cases</p>
For each active case:
<p style="margin:0 0 20px 0; color:#F2F2E8;"><strong style="color:#F2F2E8;">CASE_NAME (COURT CASE_NO)</strong><br><span style="color:#888;">Last activity: DATE</span> — one-sentence analytical description of what this filing means<br><em style="color:#888;">Status: status phrase</em></p>
Close with a 1-sentence analytical note if no new activity this week.
If no legal content: set has_legal_content to false, write 2-sentence state-of-play on Johnson v. Zuffa antitrust (D. Nev. 2:21-cv-01189).

RUMOR MILL FORMAT for rumor_mill_html — 2-3 items using this exact HTML pattern (HIGH/MEDIUM/LOW = confidence level, replace COLOR with #C5A059 for HIGH, #888888 for MEDIUM, #444444 for LOW):
<div style="border-left:3px solid COLOR; padding:4px 0 4px 18px; margin-bottom:28px;">
  <p style="font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:3px; color:COLOR; margin:0 0 10px 0;">HIGH CONFIDENCE &mdash; 0.85</p>
  <p style="margin:0; color:#F2F2E8; line-height:1.8;">Rumor text here: 2-3 sentences. Source attribution required — name the publication, the camp, or flag explicitly as unverified.</p>
</div>
"""


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_draft(news_content: str) -> dict:
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""{SYSTEM_PROMPT}

CRAWLED NEWS CONTENT (use as source material — {len(news_content):,} chars):
{news_content[:24000]}

Generate the newsletter JSON now:"""

    last_err = None
    for model in GEMINI_MODELS:
        for attempt in range(2):
            print(f"  Calling {model} (attempt {attempt + 1})...")
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[prompt],
                    config={"response_mime_type": "application/json"},
                )
                return json.loads(response.text)
            except json.JSONDecodeError as e:
                # Try to strip markdown fences if Gemini wrapped the JSON
                text = response.text.strip()
                if text.startswith("```"):
                    text = "\n".join(text.split("\n")[1:])
                    if text.endswith("```"):
                        text = text[:-3]
                try:
                    return json.loads(text)
                except Exception:
                    pass
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

    raise SystemExit(f"Draft generation failed. Last error: {last_err}")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_outputs(data: dict):
    # Inject metadata
    data["issue_date"] = DATE_ISO
    data["issue_date_display"] = DATE_DISPLAY
    data["issue_slug"] = DATE_SLUG

    DRAFT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Draft       : {DRAFT_FILE.name}")

    # Image prompts in same format as existing weekly_prompts.json
    prompts_payload = {"issue_date": DATE_ISO, "prompts": data.get("image_prompts", [])}
    PROMPTS_FILE.write_text(json.dumps(prompts_payload, indent=2), encoding="utf-8")
    print(f"  Prompts     : {PROMPTS_FILE.name}")

    # IG data
    IG_FILE.write_text(json.dumps(data.get("ig_data", {}), indent=2), encoding="utf-8")
    print(f"  IG data     : {IG_FILE.name}")


def main():
    print("=" * 60)
    print("  The Fight Docket — Newsletter Draft Generator")
    print(f"  Issue: {DATE_DISPLAY}")
    print("=" * 60)

    print(f"\n[1/3] Crawling {len(NEWS_SOURCES)} news sources...")
    news_content = crawl_news()
    if not news_content.strip():
        raise SystemExit("ERROR: No content crawled. Check FIRECRAWL_API_KEY.")
    print(f"  Crawled {len(news_content):,} chars from {len([c for c in news_content.split('===') if 'http' in c])} sources")

    print(f"\n[1b/3] Querying Perplexity Sonar for real-time news ({len(PERPLEXITY_QUERIES)} queries)...")
    perplexity_content = perplexity_search()
    if perplexity_content:
        print(f"  Perplexity  : {len(perplexity_content):,} chars")
        news_content = news_content + "\n\n" + perplexity_content
    else:
        print("  Perplexity  : skipped")

    print("\n[2/3] Generating draft with Gemini 2.5 Pro...")
    data = build_draft(news_content)

    print("\n[3/3] Writing outputs to .tmp/...")
    write_outputs(data)

    print("\n" + "=" * 60)
    print("  DONE — Next steps:")
    print("  1. Run tools/image_generator.py   (generates 7 Nano Banana images)")
    print("  2. Run tools/asset_uploader.py    (uploads images to ImgBB)")
    print("  3. Run tools/html_renderer.py     (renders final newsletter HTML)")
    print("  4. Run tools/beehiiv_post.py      (posts to Beehiiv)")
    print("=" * 60)


if __name__ == "__main__":
    main()
