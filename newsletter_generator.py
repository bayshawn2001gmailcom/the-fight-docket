#!/usr/bin/env python3
"""
The Fight Docket — Weekly Newsletter Generator
Crawls fight news → Gemini drafts newsletter HTML + image prompts + IG content data
Run: python newsletter_generator.py
"""
import os, sys, json, re, requests, time
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path.home() / ".env", override=False)

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

if not FIRECRAWL_API_KEY:
    raise SystemExit("Missing FIRECRAWL_API_KEY")
if not GEMINI_API_KEY:
    raise SystemExit("Missing GEMINI_API_KEY")

SCRIPT_DIR   = Path(__file__).parent
PROMPTS_DIR  = SCRIPT_DIR / "prompts"
PROMPTS_DIR.mkdir(exist_ok=True)

TODAY        = date.today()
ISSUE_DATE   = TODAY.strftime("%B %d, %Y").upper()
ISSUE_SLUG   = TODAY.strftime("%b%d_%Y").lower()
ISSUE_FILE   = SCRIPT_DIR / f"newsletter_{TODAY.isoformat()}.html"
PROMPTS_FILE = PROMPTS_DIR / "weekly_prompts.json"
IG_DATA_FILE = PROMPTS_DIR / "weekly_ig_data.json"

FC_HEADERS = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}"}

NEWS_SOURCES = [
    "https://www.mmafighting.com/",
    "https://www.ufc.com/news",
    "https://www.espn.com/mma/",
    "https://www.boxingscene.com/",
]


# ---------------------------------------------------------------------------
# Crawling
# ---------------------------------------------------------------------------

def firecrawl_scrape(url):
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"]},
            headers=FC_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return (data.get("data") or {}).get("markdown", "") or data.get("markdown", "")
    except Exception as e:
        print(f"  Firecrawl failed for {url}: {e}")
        return ""


def crawl_news():
    chunks = []
    for url in NEWS_SOURCES:
        print(f"  Crawling {url}...")
        content = firecrawl_scrape(url)
        if content:
            chunks.append(f"=== {url} ===\n{content[:3500]}\n")
        time.sleep(0.4)
    return "\n\n".join(chunks)


# ---------------------------------------------------------------------------
# Perplexity Sonar -- real-time supplemental news search
# ---------------------------------------------------------------------------

PERPLEXITY_QUERIES = [
    "What are the biggest MMA fight results and news from the past 7 days? Include fight results, fighter news, and promotional announcements.",
    "What are the biggest professional boxing fight results and news from the past 7 days? Include title fights, results, and upcoming cards.",
    "What is the latest combat sports business, legal, and financial news from the past 7 days? Include media rights deals, lawsuits, and regulatory updates.",
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
    for i, query in enumerate(PERPLEXITY_QUERIES, 1):
        print(f"  Perplexity query {i}/{len(PERPLEXITY_QUERIES)}...")
        try:
            resp = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": query}],
                    "max_tokens": 600,
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

SYSTEM_PROMPT = f"""You are the editor of The Fight Docket, a premium weekly newsletter covering
the combat sports industry (MMA + boxing) from a business intelligence angle.

VOICE: Analytical, insider, authoritative. Direct first person ("My read is...", "Sources tell me...").
Lead with implications, not just events. Specific figures ($, dates, deals) when available.
No promotional language. No "exciting" or "amazing" — find precise adjectives.

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

For newsletter_html use EXACTLY this structure (do not omit any inline styles):

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Fight Docket | {TODAY.strftime("%B %d, %Y").upper()}</title>
</head>
<body style="font-family: Georgia, 'Times New Roman', serif; max-width: 680px; margin: 0 auto; padding: 20px; color: #1a1a1a; line-height: 1.7; background: #ffffff;">

<div style="text-align: center; border-bottom: 3px solid #1a1a1a; padding-bottom: 20px; margin-bottom: 30px;">
  <h1 style="font-size: 36px; font-weight: 900; letter-spacing: -1px; margin: 0; text-transform: uppercase;">The Fight Docket</h1>
  <p style="margin: 6px 0 0 0; font-size: 13px; text-transform: uppercase; letter-spacing: 2px; color: #555;">Business Intelligence for the Combat Sports Industry</p>
  <p style="margin: 4px 0 0 0; font-size: 12px; color: #888;">{TODAY.strftime("%B %d, %Y").upper()}</p>
</div>

<!-- EDITOR'S NOTE (3 paragraphs, no headline) -->
<p style="font-size: 14px; text-transform: uppercase; letter-spacing: 2px; color: #888; margin-bottom: 6px;">Editor's Note</p>
[IMAGE_PLACEHOLDER_intro]
[3 paragraphs of editorial context — personal tone, sets the week's themes]

<hr style="border: none; border-top: 2px solid #1a1a1a; margin: 32px 0;">

<!-- MAIN STORY (4-5 paragraphs) -->
[IMAGE_PLACEHOLDER_main_story]
<p style="font-size: 14px; text-transform: uppercase; letter-spacing: 2px; color: #888; margin-bottom: 6px;">Main Story</p>
<h2 style="font-size: 26px; font-weight: 800; line-height: 1.2; margin-top: 0; margin-bottom: 16px;">[HEADLINE]</h2>
[4-5 paragraphs of deep analytical reporting]

<hr style="border: none; border-top: 2px solid #1a1a1a; margin: 32px 0;">

<!-- FIGHT CARD PREVIEWS (3-4 paragraphs, subheads for each fight) -->
[IMAGE_PLACEHOLDER_fight_previews]
<p style="font-size: 14px; text-transform: uppercase; letter-spacing: 2px; color: #888; margin-bottom: 6px;">Fight Card Previews</p>
<h2 style="font-size: 26px; font-weight: 800; line-height: 1.2; margin-top: 0; margin-bottom: 16px;">What's Coming Up</h2>
[2-3 fights with <p style="font-size: 16px; font-weight: 700; margin-bottom: 4px;">FIGHTER vs FIGHTER, Event, Date</p> subheads]

<hr style="border: none; border-top: 2px solid #1a1a1a; margin: 32px 0;">

<!-- BUSINESS INTEL (3-4 paragraphs) -->
[IMAGE_PLACEHOLDER_business_intel]
<p style="font-size: 14px; text-transform: uppercase; letter-spacing: 2px; color: #888; margin-bottom: 6px;">Business Intel</p>
<h2 style="font-size: 26px; font-weight: 800; line-height: 1.2; margin-top: 0; margin-bottom: 16px;">[HEADLINE]</h2>
[3-4 paragraphs on media rights, contracts, fighter pay, regulatory moves]

<hr style="border: none; border-top: 2px solid #1a1a1a; margin: 32px 0;">

<p style="font-size: 13px; color: #888; text-align: center; margin-top: 32px;">
  The Fight Docket &nbsp;·&nbsp; <a href="https://thefightdocket.com" style="color:#888;">thefightdocket.com</a> &nbsp;·&nbsp; Subscribe free
</p>

</body>
</html>
"""


GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]


def build_newsletter(news_content):
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""{SYSTEM_PROMPT}

CRAWLED NEWS CONTENT (use this as source material):
{news_content[:14000]}

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

def write_outputs(data):
    # Newsletter HTML
    html = data["newsletter_html"]
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


def main():
    print("=" * 55)
    print("  The Fight Docket — Newsletter Generator")
    print(f"  Issue: {ISSUE_DATE}")
    print("=" * 55)

    print("\n[1/3] Crawling news sources...")
    news_content = crawl_news()
    if not news_content.strip():
        raise SystemExit("ERROR: No content crawled. Check FIRECRAWL_API_KEY.")
    print(f"  Crawled {len(news_content):,} chars")

    print(f"\n[1b/3] Querying Perplexity Sonar ({len(PERPLEXITY_QUERIES)} queries)...")
    perplexity_content = perplexity_search()
    if perplexity_content:
        print(f"  Perplexity  : {len(perplexity_content):,} chars")
        news_content = news_content + "\n\n" + perplexity_content
    else:
        print("  Perplexity  : skipped")

    print("\n[2/3] Generating newsletter with Gemini...")
    data = build_newsletter(news_content)

    print("\n[3/3] Writing outputs...")
    write_outputs(data)

    print("\n" + "=" * 55)
    print("  DONE")
    print(f"  Newsletter : {ISSUE_FILE.name}")
    print(f"  Prompts    : prompts/weekly_prompts.json  (triggers image generation)")
    print(f"  IG data    : prompts/weekly_ig_data.json  (used by ig_content_generator.py)")
    print("=" * 55)


if __name__ == "__main__":
    main()
