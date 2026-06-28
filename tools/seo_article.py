#!/usr/bin/env python3
"""
The Fight Docket — SEO Article Generator (WAT Framework)
Reads the latest newsletter draft JSON, uses Gemini to write a 600-800 word
SEO article targeting fight-week search terms, saves locally and creates
a Beehiiv draft.

No Firecrawl credits needed — reuses the existing newsletter draft.

Run:
    python tools/seo_article.py                   # latest draft
    python tools/seo_article.py --date=2026-06-15 # specific date
    python tools/seo_article.py --dry-run         # generate, print, don't post
    python tools/seo_article.py --publish         # also email to subscribers
"""
import os, sys, json, re, argparse
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
import requests

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
BEEHIIV_API_KEY = os.getenv("BEEHIIV_API_KEY", "")
PUBLICATION_ID  = os.getenv("BEEHIIV_PUBLICATION_ID", "")

if not GEMINI_API_KEY:
    raise SystemExit("Missing GEMINI_API_KEY")

TMP_DIR      = ROOT / ".tmp"
ARTICLES_DIR = TMP_DIR / "seo_articles"
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
STATUS_FILE  = ARTICLES_DIR / "seo_status.json"

BEEHIIV_BASE    = "https://api.beehiiv.com/v2"
BEEHIIV_HEADERS = {"Authorization": f"Bearer {BEEHIIV_API_KEY}", "Content-Type": "application/json"}
SUBSCRIBE_URL   = "https://thefightdocket.beehiiv.com/subscribe"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_draft(target_date: str | None = None) -> tuple[str, dict]:
    if target_date:
        path = TMP_DIR / f"newsletter_draft_{target_date}.json"
        if not path.exists():
            raise SystemExit(f"Draft not found: {path.name}")
        return target_date, json.loads(path.read_text(encoding="utf-8"))

    files = sorted(TMP_DIR.glob("newsletter_draft_*.json"), key=lambda f: f.name, reverse=True)
    if not files:
        raise SystemExit("No newsletter_draft_*.json in .tmp/ — run newsletter_draft.py first.")
    stem  = files[0].stem                    # e.g. "newsletter_draft_2026-06-15"
    d     = stem.replace("newsletter_draft_", "")
    print(f"  Draft: {files[0].name}")
    return d, json.loads(files[0].read_text(encoding="utf-8"))


def load_ig_data(target_date: str | None = None) -> dict:
    if target_date:
        path = TMP_DIR / f"weekly_ig_data_{target_date}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    files = sorted(TMP_DIR.glob("weekly_ig_data_*.json"), key=lambda f: f.name, reverse=True)
    return json.loads(files[0].read_text(encoding="utf-8")) if files else {}


def strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def load_status() -> dict:
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_status(data: dict):
    STATUS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Gemini article generation
# ---------------------------------------------------------------------------

SEO_PROMPT = """You are a combat sports journalist and SEO writer for The Fight Docket, a premium combat sports business intelligence newsletter.

TASK: Write a 600-800 word SEO article based on the newsletter content below.

ARTICLE RULES:
- Target the main fight-week search query (fighter names + event + result or preview)
- Tone: Analytical and authoritative, but accessible to casual fans. Not just a results recap — lead with the business and strategic angle.
- Structure: 3-4 sections with subheadings. No H1 (that's the title). Use simple HTML <h2> tags.
- Include specifics: round, time, financial implications, contract leverage, matchmaking implications
- NEVER use "exciting," "amazing," or generic sports clichés
- Final paragraph: naturally integrated CTA (part of the article flow, not a separate box)

CTA TEMPLATE — use this as the final paragraph, with [SUBSCRIBE_URL] replaced:
"For deeper analysis on fighter pay, contract leverage, and what the matchmakers are weighing next, subscribe free to The Fight Docket at [SUBSCRIBE_URL] — weekly combat sports business intelligence without the noise."

OUTPUT — valid JSON only, no markdown fences:
{
  "seo_title": "SEO-optimized title under 65 chars — include fighter names and event",
  "slug": "url-slug-with-hyphens-no-special-chars",
  "meta_description": "150-160 chars for Google snippet, include fighter names and event",
  "article_html": "<p>Opening paragraph...</p><h2>Section Title</h2><p>...</p>...",
  "word_count": 650
}"""


def generate_article(draft: dict, ig_data: dict, draft_date: str) -> dict:
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)

    main_headline  = draft.get("main_story_headline", "")
    main_story     = strip_html(draft.get("main_story_html", ""))[:3000]
    biz_headline   = draft.get("business_intel_headline", "")
    biz_intel      = strip_html(draft.get("business_intel_html", ""))[:2000]
    editors_note   = strip_html(draft.get("editors_note_html", ""))[:800]
    spotlight_name = draft.get("fighter_spotlight_name", "")
    spotlight_body = strip_html(draft.get("fighter_spotlight_html", ""))[:1000]
    preview_stories = ig_data.get("preview_stories", [])

    display_date = date.fromisoformat(draft_date).strftime("%B %d, %Y")

    context = f"""NEWSLETTER DATE: {display_date}
TOP STORIES: {' | '.join(preview_stories)}

MAIN STORY: {main_headline}
{main_story}

BUSINESS INTEL: {biz_headline}
{biz_intel}

EDITOR'S NOTE:
{editors_note}

FIGHTER IN FOCUS: {spotlight_name}
{spotlight_body}"""

    prompt = (
        SEO_PROMPT.replace("[SUBSCRIBE_URL]", SUBSCRIBE_URL)
        + f"\n\nNEWSLETTER CONTENT:\n{context}\n\nGenerate the SEO article JSON:"
    )

    print("  Calling Gemini (gemini-2.5-flash)...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
        config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)


# ---------------------------------------------------------------------------
# Local save
# ---------------------------------------------------------------------------

def save_local(article: dict, draft_date: str) -> Path:
    title  = article.get("seo_title", "The Fight Docket")
    slug   = article.get("slug", "article")
    meta   = article.get("meta_description", "")
    body   = article.get("article_html", "")
    words  = article.get("word_count", 0)
    d_obj  = date.fromisoformat(draft_date)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{meta}">
<title>{title} | The Fight Docket</title>
<style>
body{{font-family:Georgia,serif;max-width:740px;margin:40px auto;padding:0 20px;color:#1a1a1a;line-height:1.75;}}
h1{{font-size:30px;font-weight:900;line-height:1.2;margin-bottom:8px;}}
h2{{font-size:20px;font-weight:700;margin-top:32px;}}
.byline{{font-size:13px;color:#888;margin-bottom:32px;border-bottom:1px solid #eee;padding-bottom:16px;}}
</style>
</head>
<body>
<h1>{title}</h1>
<p class="byline">The Fight Docket &nbsp;·&nbsp; {d_obj.strftime('%B %d, %Y')} &nbsp;·&nbsp; ~{words} words</p>
{body}
</body>
</html>"""

    out = ARTICLES_DIR / f"{draft_date}_{slug}.html"
    out.write_text(html, encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Beehiiv draft
# ---------------------------------------------------------------------------

def create_beehiiv_draft(article: dict, draft_date: str) -> str:
    if not BEEHIIV_API_KEY or not PUBLICATION_ID:
        print("  Beehiiv credentials not set — skipping draft creation")
        return ""

    title  = article.get("seo_title", "Fight Week Analysis — The Fight Docket")
    meta   = article.get("meta_description", "")
    body   = article.get("article_html", "")
    d_obj  = date.fromisoformat(draft_date)

    full_html = (
        f"<p style='font-size:13px;color:#888;'>The Fight Docket &nbsp;·&nbsp; "
        f"{d_obj.strftime('%B %d, %Y')}</p>\n{body}"
    )

    payload = {
        "title":        title,
        "subject":      title,
        "preview_text": meta[:80] if meta else title[:80],
        "content_type": "html",
        "content":      full_html,
        "status":       "draft",
        "audience":     "all",
    }

    url  = f"{BEEHIIV_BASE}/publications/{PUBLICATION_ID}/posts"
    resp = requests.post(url, json=payload, headers=BEEHIIV_HEADERS, timeout=30)
    if not resp.ok:
        print(f"  Beehiiv draft failed {resp.status_code}: {resp.text[:200]}")
        return ""
    return resp.json().get("data", {}).get("id", "")


def confirm_beehiiv_post(post_id: str) -> bool:
    url     = f"{BEEHIIV_BASE}/publications/{PUBLICATION_ID}/posts/{post_id}"
    payload = {"status": "confirmed"}
    resp    = requests.patch(url, json=payload, headers=BEEHIIV_HEADERS, timeout=30)
    return resp.ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="The Fight Docket — SEO Article Generator")
    parser.add_argument("--date",    metavar="YYYY-MM-DD", help="Draft date (default: latest)")
    parser.add_argument("--dry-run", action="store_true",  help="Generate article, skip posting")
    parser.add_argument("--publish", action="store_true",  help="Confirm Beehiiv post (sends email to subscribers)")
    args = parser.parse_args()

    print("=" * 60)
    print("  The Fight Docket — SEO Article Generator")
    print(f"  Today: {date.today().isoformat()}")
    print("=" * 60)

    print("\n[1/3] Loading newsletter draft...")
    draft_date, draft = load_draft(args.date)
    ig_data = load_ig_data(draft_date)
    print(f"  Date  : {draft_date}")
    print(f"  Story : {draft.get('main_story_headline', 'N/A')[:65]}")

    status = load_status()
    if draft_date in status and not args.dry_run:
        print(f"\n  NOTE: Article already generated for {draft_date}")
        print(f"  Post ID: {status[draft_date].get('post_id', 'none')}")
        print(f"  Re-running will create a new draft in Beehiiv.")

    print("\n[2/3] Generating SEO article with Gemini...")
    article = generate_article(draft, ig_data, draft_date)

    title = article.get("seo_title", "")
    slug  = article.get("slug", "")
    words = article.get("word_count", 0)
    meta  = article.get("meta_description", "")

    print(f"  Title : {title}")
    print(f"  Slug  : {slug}")
    print(f"  Words : {words}")
    print(f"  Meta  : {meta[:70]}...")

    print("\n[3/3] Saving article...")
    local_path = save_local(article, draft_date)
    print(f"  Local : {local_path.name}")

    if args.dry_run:
        print("\n  [DRY RUN] Skipped Beehiiv. Article content preview:")
        body_text = strip_html(article.get("article_html", ""))
        print(f"\n  {body_text[:400]}...\n")
        print("=" * 60)
        print("  DONE — Dry run complete.")
        print(f"  File : {local_path}")
        print("=" * 60)
        return

    print("\n  Creating Beehiiv draft...")
    post_id = create_beehiiv_draft(article, draft_date)

    save_status({**status, draft_date: {
        "title":    title,
        "slug":     slug,
        "post_id":  post_id,
        "local":    str(local_path),
        "generated_at": date.today().isoformat(),
        "published": False,
    }})

    print("\n" + "=" * 60)
    if post_id:
        draft_url = f"https://app.beehiiv.com/posts/{post_id}"
        print(f"  Draft  : {draft_url}")

        if args.publish:
            ok = confirm_beehiiv_post(post_id)
            if ok:
                save_status({**load_status(), draft_date: {
                    **load_status().get(draft_date, {}), "published": True
                }})
                print(f"  Status : Published (sent to email list)")
            else:
                print(f"  Status : Confirm failed — post left as draft")
        else:
            print("\n  To publish as web-only (no email):")
            print(f"    1. Open  : {draft_url}")
            print(f"    2. Click : 'Publish' → 'Web only'")
            print(f"  To publish + email subscribers, re-run with --publish")
    else:
        print("  Beehiiv skipped — article saved locally only.")

    print(f"\n  Local  : {local_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
