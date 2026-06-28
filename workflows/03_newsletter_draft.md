# Workflow 03: Newsletter Draft Generation

## Objective
Crawl 10 combat sports news sources + query Perplexity Sonar for real-time news, generate a structured 7-section newsletter draft via Gemini 2.5 Pro, and produce image prompts + IG metadata.

## Trigger
Monday morning, before 8am EDT. (Or immediately after major weekend fights — see Fight Recap rule below.)

## Required Inputs
- `FIRECRAWL_API_KEY` in `~/.env`
- `GEMINI_API_KEY` in `~/.env`
- `PERPLEXITY_API_KEY` in `~/.env`

## Tool
`tools/newsletter_draft.py`

## Steps

1. **Run the draft generator**
   ```
   python tools/newsletter_draft.py
   ```
   To generate for a specific date (e.g. a fight-recap issue on a non-Monday):
   ```
   python tools/newsletter_draft.py 2026-05-24
   ```

2. **Verify outputs exist in `.tmp/`**
   - `newsletter_draft_YYYY-MM-DD.json` — 7-section structured draft
   - `weekly_prompts_YYYY-MM-DD.json` — 8 Nano Banana image prompts (incl. thumbnail)
   - `weekly_ig_data_YYYY-MM-DD.json` — Instagram metadata

3. **Review the draft JSON** — open `newsletter_draft_YYYY-MM-DD.json` and check:
   - `main_story_headline`: Is it specific and punchy? ("Dana White Faces Deposition Over Fighter Pay Records" not "UFC News Update")
   - `main_story_html`: Does it have 4-5 paragraphs? Is the voice analytical, not promotional?
   - `legal_tracker_html`: Does it reference real case numbers? Is `has_legal_content` accurate?
   - `rumor_mill_html`: Are confidence ratings present (0.XX format)? Are sources properly qualified?
   - `fighter_spotlight_name`: Is it a fighter with actual news this week?

4. **Manual overrides** — if a section is weak, edit the JSON directly before proceeding:
   - Open `.tmp/newsletter_draft_YYYY-MM-DD.json`
   - Edit the relevant HTML field
   - Save — subsequent steps read from this file

## News Sources Crawled (10 total)

- mmafighting.com (MMA news)
- espn.com/mma (MMA + boxing)
- ufc.com/news (UFC official)
- boxingscene.com (boxing news)
- sherdog.com/news (MMA records + news)
- bloodyelbow.com (labor/business angle)
- ringtv.com (Ring Magazine boxing authority)
- badlefthook.com (analytical boxing)
- mixedmartialarts.com (community intelligence)
- **fightnews.com (boxing results — added after Keyshawn Davis fight was missed)**

## Perplexity Sonar (Step 1b)

After Firecrawl scraping, the script fires 6 targeted Perplexity Sonar queries:

1. MMA fight results and news (past 7 days)
2. Boxing fight results and news (past 7 days)
3. **Federal courts and PACER** — active combat sports litigation, new filings, case numbers, rulings (UFC/TKO/Top Rank/Matchroom/Golden Boy/PFL)
4. **Athletic commissions** — NYSAC, CSAC, NSAC decisions, suspensions, USADA/VADA drug test results (past 7 days)
5. **Business intelligence** — media rights deals, TV ratings, PPV buyrates, sponsor deals, promoter acquisitions, fighter pay disputes
6. **All fight results from the specific past Saturday and Sunday** — exhaustive, named-event level detail

Queries 3 and 4 feed directly into the Legal Tracker section (Section 3 of the newsletter). Query 6 is dynamically constructed using the computed `LAST_SAT`/`LAST_SUN` dates — fix for missed Saturday-night results.

Cost: ~$0.045/run (6 queries).

## Editorial Priority Rule

The system prompt instructs Gemini: **if a major title fight or marquee main event occurred in the past 72 hours, it MUST be the main_story.** Business and legal stories are secondary unless of once-in-a-decade significance. This prevents the model from burying fight results under promotional deal analysis.

## Fight Recap Rule
If the newsletter covers fights that occurred on the weekend (Sat/Sun), **publish immediately** after creation — do NOT schedule for Monday noon. Fight results are time-sensitive. Use the date CLI arg so you don't overwrite an already-posted issue:
```
python tools/newsletter_draft.py 2026-05-24
```

## Newsletter Sections
1. **Editor's Note** — 3 paragraphs, personal tone, sets the week's themes
2. **Main Story: Deep Dive** — 600-800 words, your deepest analytical reporting
3. **Legal Tracker** — active federal cases, new docket activity flagged
4. **Rumor Mill** — 2-3 items with explicit confidence ratings (0.0-1.0)
5. **Fight Card Previews** — 2-3 upcoming fights, 150-200 words each
6. **Business Intel** — media rights, contracts, promoter moves, TV numbers
7. **Fighter Spotlight** — 400 words on one fighter's career arc

## Voice Guidelines
- **Analytical, not promotional.** Never "exciting" or "amazing" — find precise adjectives.
- **First-person, direct.** "My read is...", "Sources tell me...", "What this means is..."
- **Lead with implications.** Not what happened — why it matters, what comes next.
- **Specific figures.** Dollar amounts, dates, case numbers, record stats when available.
- **Benchmark:** The April 27, 2026 Dana White deposition piece. That is the target quality.

## Slow News Week Fallbacks
If a week has no major MMA or boxing news:
- **Main Story:** Go analytical on a structural issue — fighter pay, promotion economics, sanctioning body politics
- **Legal Tracker:** Provide a "State of Play" summary on the Johnson v. Zuffa antitrust case even without new filings
- **Fighter Spotlight:** Profile an up-and-coming fighter before they make major news (positions you as ahead of the curve)
- **Rumor Mill:** Use lower confidence ratings honestly rather than inflating confidence to fill space

## Gemini Model Fallback Order
1. `gemini-2.5-pro` (primary — best analytical writing)
2. `gemini-2.5-flash` (fallback if Pro is unavailable or rate-limited)
3. `gemini-2.0-flash` (emergency fallback)

## Rate Limits & Errors
- **429 (rate limit):** Script retries automatically with 30s/60s backoff. Wait it out.
- **Firecrawl 402 (credits exhausted):** Script auto-switches ALL remaining sources to **Crawl4AI** (local headless browser via Playwright). Coverage stays high — Crawl4AI extracts clean markdown and handles JavaScript-rendered pages. No API credits required. Top up Firecrawl credits at firecrawl.dev before the weekend for best speed, but Crawl4AI is a reliable fallback.
- **Individual source 403:** Normal — some sites block scrapers. Perplexity Sonar compensates for missed sources.
- **JSON parse error:** Script tries to strip markdown fences and re-parse. If it still fails, check the raw `response.text` in the error output.

## Firecrawl Credit Management

- The Saturday/Sunday GitHub Actions (live fight results) previously burned credits automatically every weekend. The Sunday workflow is now **manual-trigger only** — run it from GitHub Actions when there are actual fights.
- Top up Firecrawl before a big fight weekend so Monday's newsletter has full coverage.

## Output File Locations
All outputs in `.tmp/` (gitignored, regeneratable):
```
.tmp/
  newsletter_draft_2026-05-24.json
  weekly_prompts_2026-05-24.json
  weekly_ig_data_2026-05-24.json
```

## Next Step
→ Run `tools/image_generator.py` to generate the 8 Nano Banana section images
