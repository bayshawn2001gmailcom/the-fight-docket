---
title: The Fight Docket — System Architecture
type: technical-architecture
status: living document
created: 2026-06-28
tags: [fight-docket, architecture, claude-code, mcp, beehiiv, github-actions]
---

# The Fight Docket — System Architecture

> Technical reference for how the newsletter operation is wired. Source of truth for components, data flow, credentials, and failure modes. See [[Context]] for business context and [[SOP]] for the operational runbook.

---

## Components

### 1. Claude Code — Orchestration Layer
- **Role:** Primary work surface for development, debugging, ad-hoc sessions, and one-off tasks.
- **Runs on:** Local machine — `C:\Users\baysh\Command-Center\the-fight-docket`
- **Persistent anchor file:** `CLAUDE.md` at project root — standing instructions, source list, voice/tone guidelines.
- **Failure mode:** If Claude Code is unavailable, ad-hoc and development work halts. The scheduled GitHub Actions pipeline runs independently.

### 2. GitHub Actions — Automation & Scheduling Layer
- **Role:** Runs the full weekly pipeline on schedule — no operator trigger required.
- **Repo:** https://github.com/bayshawn2001gmailcom/the-fight-docket

| Day/Time (EDT) | Workflow | Script |
| --- | --- | --- |
| Fri 6pm | `friday-crawl-fights.yml` | `upcoming_fights_crawler.py` → `upcoming_fights.json` |
| Fri 9pm / 11pm / 12:30am | `friday-night-results.yml` | `post_live_result.py` → live tweets + IG cards (deduped) |
| Sat 9pm / 11pm | `saturday-night-results.yml` | `post_live_result.py` → live tweets + IG cards (deduped) |
| Sun 1am | `sunday-post-results.yml` | `post_fight_results.py` → recap image + Instagram |
| Sun 7:15pm | `generate_images.yml` | `generate_images_action.py` → Gemini image generation |
| Mon 8am | `newsletter_pipeline.yml` | `newsletter_generator.py` → auto-posts to Beehiiv → noon send |
| Mon 10am | `twitter_thread.yml` | `post_twitter_thread.py` → 6-tweet thread |
| Mon 11am | `weekly_ig_content.yml` | `ig_content_generator.py` → 4 IG graphics + captions |

- **Failure mode:** Workflow failure sends GitHub notification. No auto-retry — operator restarts manually.

### 3. Firecrawl — Primary Scraper
- **Role:** Default scraping tool. Pulls structured content from athletic commission sites, event calendars, and results aggregators.
- **Use when:** Running any standard recurring scrape.
- **Connection:** MCP server in Claude Code + direct API calls from scripts.
- **Auth:** `FIRECRAWL_API_KEY` in `~/.env` and GitHub Secrets.
- **Failure mode:** If rate-limited, erroring, or returning incomplete data → fall back to Crawl4AI.

### 4. Crawl4AI — Fallback Scraper
- **Role:** Backup scraper used when Firecrawl errors, hits token/rate limits, or when Crawl4AI produces demonstrably better output on a given source.
- **Use when:** Firecrawl fails, or Crawl4AI is clearly the better tool for the content structure.
- **Auth:** None (open source, local install).
- **Failure mode:** JS-heavy or anti-bot sites may fail → return to Firecrawl or use Perplexity.

### 5. Perplexity — Research & Synthesis Layer
- **Role:** Active research tool used to its full capability. Fills the gap between raw scraping and Claude Code's own reasoning.
- **Use when:**
  - Narrative / context queries ("what's the storyline going into Saturday's main event")
  - Breaking news or analysis not worth a full scrape
  - Source discovery (finding new commission pages or coverage outlets)
  - One-off lookups where a synthesized answer beats raw HTML
- **Auth:** `PERPLEXITY_API_KEY` in `~/.env` (add to GitHub Secrets if used in Actions workflows).
- **Failure mode:** Outage → fall back to Claude Code's built-in web tools or manual research.

### Scraping & Research Decision Rule

| Use Case | Tool |
| --- | --- |
| Standard recurring scrape (commission results, fight cards) | **Firecrawl** |
| Firecrawl error / token limit / better output expected | **Crawl4AI** |
| Narrative context, breaking news, synthesized answer | **Perplexity** |
| Source discovery / "is there a better feed for X" | **Perplexity** |
| One-off lookup, no scrape needed | **Perplexity** |

If Crawl4AI or Perplexity are being used more than Firecrawl on repeating tasks, that's an efficiency signal — flag it (see Efficiency Review Protocol below).

### 6. Beehiiv — Publishing + Distribution
- **Role:** Email delivery, subscriber management, web archive, analytics.
- **Access from scripts:** Direct REST API via `beehiiv_post.py`; Beehiiv MCP available for Claude Code sessions.
- **Auth:** `BEEHIIV_API_KEY` in `~/.env`; publication ID `pub_3ee36121-475b-43f5-87b9-9a610d46779b`.
- **System of record for:** Subscriber list, issue archive, open/click/unsubscribe analytics, Boosts config.
- **Failure mode:** Outage delays send. Drafts safe in local FS and GitHub repo — retry when restored.

### 7. Social Channels — Automated Where Possible
- **X / Twitter:** Automated — 6-tweet thread via `post_twitter_thread.py` every Monday 10am EDT. Plain text only — no markdown, no asterisks, no headers.
- **Instagram:** Automated when possible via `ig_content_generator.py` (Monday 11am EDT). GitHub Actions IPs may be blocked by Instagram — images and captions are always committed to `instagram_content/` as a manual posting fallback.
- **Facebook:** Manual — operator posts from Claude Code output.
- **Known bug:** Markdown must be stripped from all X output. `post_twitter_thread.py` must enforce plain-text — no asterisks, headers, or bullet syntax in tweets.

### 8. Local Filesystem + Git — Working Storage & Backup
- **Role:** Working storage for research dumps, draft markdown, prompt templates, Obsidian vault.
- **Backup:** Git remote — https://github.com/bayshawn2001gmailcom/the-fight-docket
- **Failure mode:** Uncommitted research/drafts are lost if local FS fails. Committed work and subscriber list (Beehiiv) are safe.

---

## Data Flow — Single Issue (Automated)

1. **GitHub Actions** triggers `newsletter_pipeline.yml` Monday 8am EDT
2. **`newsletter_generator.py`** → Firecrawl scrapes source list (Crawl4AI fallback if needed); Perplexity for narrative context
3. **Gemini** drafts newsletter from research output
4. **`beehiiv_post.py`** → auto-posts to Beehiiv, schedules noon send
5. **`post_twitter_thread.py`** → 6-tweet thread (Monday 10am EDT)
6. **`ig_content_generator.py`** → 4 IG graphics + captions (Monday 11am EDT; manual post if Actions IPs blocked)

---

## Credentials Inventory

| System | Env Var | Storage Location |
| --- | --- | --- |
| Firecrawl | `FIRECRAWL_API_KEY` | `~/.env` + GitHub Secrets |
| Beehiiv API | `BEEHIIV_API_KEY` | `~/.env` + GitHub Secrets |
| Beehiiv Publication | `BEEHIIV_PUBLICATION_ID` | `~/.env` (`pub_3ee36121-475b-43f5-87b9-9a610d46779b`) |
| Gemini | `GEMINI_API_KEY` | `~/.env` + GitHub Secrets |
| Perplexity | `PERPLEXITY_API_KEY` | `~/.env` (add to GitHub Secrets if used in Actions) |
| Twitter/X | `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`, `TWITTER_BEARER_TOKEN`, `TWITTER_CLIENT_ID`, `TWITTER_CLIENT_SECRET` | GitHub Secrets |
| Instagram | `INSTAGRAM_USERNAME`, `INSTAGRAM_PASSWORD` | GitHub Secrets |
| Crawl4AI | None | N/A (open source, local) |

---

## Single Points of Failure
- **GitHub Actions** — if the repo or Actions is unavailable, the scheduled pipeline halts.
- **Firecrawl** — primary scraper; Crawl4AI fallback covers most cases but not all.
- **Local filesystem** — uncommitted research/drafts not backed up until pushed to GitHub.
- **Instagram posting** — GitHub Actions IPs may be blocked; manual fallback required.

## Known Technical Debt
- No automated social → Beehiiv funnel (no UTMs, no tracked CTAs, social accounts not cross-linked from Beehiiv site).
- No analytics pipe — open rate / CTR / churn lives only in Beehiiv UI; not exported or trended over time.
- Facebook posting remains fully manual — no API integration.
- Perplexity API key needs to be added to GitHub Secrets if used in Actions workflows.

## Future Architecture Considerations
- **If subscriber count justifies it:** Enable Beehiiv Boosts — no new infra, just configuration.
- **If Facebook becomes a real channel:** API integration via Buffer or direct Graph API.
- **If issue cadence increases:** Review pipeline for parallelization opportunities within GitHub Actions.

---

## Efficiency Review Protocol

**Standing rule:** Anything running inefficiently must be surfaced immediately with a proposed fix. The bar is the six-to-seven-figure scaling goal — every dollar of API spend, every wasted token, every manual step that should be automated, and every weak data source is a tax on that goal.

### What Counts as "Inefficient"

1. **Token waste** — prompts pulling more context than needed; repeated re-scraping of the same data; verbose outputs where structured/short would do; using a frontier model for a task a cheaper one handles.
2. **Tool misuse** — using Firecrawl when Crawl4AI produces better data (paying for what's free); using Crawl4AI on anti-bot sites that keep failing (should be Firecrawl); using Perplexity for structured scrapes (wrong tool, weaker data); any tool used outside the decision rule above.
3. **Information quality** — sources returning stale or unverified data; manual cross-checks repeatedly catching errors from the same source → drop or replace it.
4. **Process drag** — manual steps that recur every issue and could be automated; time-per-issue trending up; operator review catching the same class of error repeatedly.
5. **Cost creep** — monthly tool spend rising without matching subscriber/revenue growth; new tools added without retiring old ones.

### How Surfacing Works
When Claude notices an inefficiency in any session, the report must include:
- **What's inefficient** — specific component, prompt, or step
- **Why it matters** — token cost, time cost, quality cost, or revenue ceiling
- **Proposed fix** — concrete change (swap tool, rewrite prompt, automate step, drop source)
- **Tradeoff** — cost to implement vs. what it saves
- **Impact on the scaling goal** — does this unlock scale, or just polish?

### Review Cadence
- **Per-session:** Surface inefficiencies as noticed, in the same response.
- **Per-issue (post-send):** Quick scan — anything from this issue worth flagging?
- **Monthly:** Full review of tool spend, time-per-issue trend, source quality, and subscriber growth vs. cost.

---

## Related Notes
- [[Context]]
- [[SOP]]
- [[Claude Code]]
- [[Firecrawl MCP]]
- [[Crawl4AI]]
- [[Perplexity]]
- [[Beehiiv API]]
