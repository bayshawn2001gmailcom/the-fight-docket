---
title: The Fight Docket — System Architecture
type: technical-architecture
status: living document
created: 2026-06-28
tags: [fight-docket, architecture, claude-code, mcp, beehiiv]
---

# The Fight Docket — System Architecture

> Technical reference for how the newsletter operation is wired. Source of truth for components, data flow, credentials, and failure modes.

## High-Level Diagram

---

## Components

### 1. Claude Code (Orchestration Layer)
- **Role:** Primary work surface. Handles reasoning, drafting, MCP tool calls, and file I/O.
- **Runs on:** Local machine.
- **Project directory:** `[fill in path]`
- **Persistent anchor file:** `CLAUDE.md` at project root — contains standing instructions, source list, voice/tone guidelines.
- **Failure mode:** If Claude Code is unavailable, the entire pipeline halts. No fallback drafting workflow exists.

### 2. Firecrawl MCP (Scraping Layer)
- **Role:** Pulls structured content from athletic commission sites, event calendars, results aggregators.
- **Connection:** MCP server registered in Claude Code config.
- **Auth:** API key stored in `[fill in: 1Password / .env / config location]`.
- **Rate limits:** [fill in based on current Firecrawl plan]
- **Failure mode:** If Firecrawl is down or rate-limited, research phase blocks. No automated retry — operator restarts manually.
- **Evaluated alternative:** Direct `web_fetch` from Claude Code for low-volume sessions; full scrape replacement would require a new MCP integration.

### 3. Beehiiv (Publishing + Distribution Layer)
- **Role:** Email delivery, subscriber management, web archive, analytics.
- **Access from Claude Code:** Beehiiv MCP server + direct REST API as fallback.
- **Auth:** Publication API key stored in `[fill in location]`.
- **What lives there:**
  - Subscriber list (system of record)
  - Issue archive
  - Open / click / unsubscribe analytics
  - Boosts configuration (when activated)
- **Failure mode:** Beehiiv outage delays send; drafts remain safe in local FS and can be retried.

### 4. Local Filesystem (Working Storage)
- **Role:** Holds research dumps, draft markdown, prompt templates, this Obsidian vault.
- **Structure (proposed):**

- **Backup:** [fill in: iCloud / Dropbox / Git remote / none]
- **Failure mode:** Loss of local FS = loss of historical research and drafts. Subscriber list is safe (lives in Beehiiv).

### 5. Social Channels (Manual Distribution)
- **X / Twitter, Instagram, Facebook:** Not API-integrated. Operator copies Claude Code output and posts manually.
- **Known issue:** Markdown leaks into X posts because there's no programmatic stripping step — see SOP Phase 3.
- **Failure mode:** Low — social is currently low-value, so an outage on any platform is non-blocking.

---

## Data Flow — Single Issue

1. **Operator → Claude Code:** Prompt with coverage window.
2. **Claude Code → Firecrawl MCP:** Scrape requests against source list.
3. **Firecrawl MCP → Source sites → back to Claude Code:** Raw results returned.
4. **Claude Code → Local FS:** Research dump written to `/research/YYYY-MM-DD.md`.
5. **Claude Code (drafting prompt) → Local FS:** Draft written to `/drafts/YYYY-MM-DD.md`.
6. **Claude Code → Beehiiv API:** Draft pushed as Beehiiv post.
7. **Operator → Beehiiv UI:** Manual review, send.
8. **Beehiiv → Subscribers:** Email delivered, analytics begin accruing.
9. **Operator → Social channels:** Manual paste of Claude Code's social output.
10. **Operator → Local FS:** Issue moved to `/sent/`.

---

## Credentials Inventory
| System | Credential Type | Storage Location | Rotation Cadence |
|---|---|---|---|
| Firecrawl MCP | API key | [fill in] | [fill in] |
| Beehiiv | Publication API key | [fill in] | [fill in] |
| X / Twitter | Manual login | Password manager | N/A |
| Instagram | Manual login | Password manager | N/A |
| Facebook | Manual login | Password manager | N/A |

---

## Single Points of Failure
- **Claude Code availability** — no fallback drafting workflow.
- **Local filesystem** — no documented backup of research/drafts.
- **Operator** — entire pipeline is single-threaded through one human at the publish step.

## Known Technical Debt
- X markdown-strip step is missing from the publish workflow (see Context.md and SOP Phase 3).
- No automated subscriber funnel from social → Beehiiv (no UTMs, no tracked CTAs).
- No analytics pipe — open rate / CTR / churn data lives only in Beehiiv UI; not exported, not trended over time.
- Source list lives only inside `CLAUDE.md` — not version-controlled separately, easy to lose if the file is overwritten.

## Future Architecture Considerations
- **If subscriber count justifies it:** Add Beehiiv Boosts (no new infra — just configuration).
- **If issue cadence increases:** Move from on-demand Claude Code sessions to a scheduled trigger (cron + Claude Code in headless mode, or a lightweight wrapper script).
- **If social becomes a real channel:** API integration for at least X (Buffer, Typefully, or direct API) to eliminate manual paste and fix the markdown bug at the source.

---
title: The Fight Docket — System Architecture
type: master-reference
status: living document
created: 2026-06-28
tags: [fight-docket, architecture, sop, context, claude-code, mcp]
---

# The Fight Docket — System Architecture

> Master reference for The Fight Docket. Combines business context, operational runbook, and technical architecture in one file. If a fact about this operation isn't here, it isn't documented.

---

# PART 1 — CONTEXT

## Identity
The Fight Docket is a **combat sports newsletter** published on **Beehiiv**. Coverage spans MMA, boxing, and adjacent combat disciplines, with an editorial angle that leans on athletic commission data, fight results, and event tracking rather than personality/opinion content.

## Business Model
- **Primary surface:** Beehiiv newsletter (free tier, with paid tier and ad/boost monetization as the growth path).
- **Monetization levers (future):**
  - Beehiiv Boosts (paid recommendations from other newsletters)
  - Sponsored placements once subscriber count justifies CPM rates
  - Affiliate revenue (sportsbooks, merch, training gear) — secondary
- **Reference model:** The Rundown AI — daily AI-curated newsletter that scaled to 7-figure ad revenue with a small team. The Fight Docket applies the same automation-heavy, low-headcount model to combat sports.
- **Backup:** `[fill in: iCloud / Dropbox / Git remote / none]`
- **Failure mode:** Loss = historical research and drafts gone. Subscriber list is safe (Beehiiv).

### 7. Social Channels — Manual Distribution
- **Platforms:** X / Twitter, Instagram, Facebook.
- **Integration:** None. Operator copies Claude Code output and posts manually.
- **Known bug:** Markdown leaks into X posts — no programmatic stripping step. See SOP Phase 3.

## Data Flow — Single Issue
1. **Operator → Claude Code:** Prompt with coverage window.
2. **Claude Code → Crawl4AI / Firecrawl / Perplexity:** Research requests per decision rule.
3. **Tools → Claude Code:** Raw + synthesized research returned.
4. **Claude Code → Local FS:** Research dump written to `/research/YYYY-MM-DD.md`.
5. **Claude Code → Local FS:** Draft written to `/drafts/YYYY-MM-DD.md`.
6. **Claude Code → Beehiiv:** Draft pushed via MCP/API.
7. **Operator → Beehiiv UI:** Manual review, send.
8. **Beehiiv → Subscribers:** Email delivered, analytics begin.
9. **Operator → Social:** Manual paste of Claude Code's social output.
10. **Operator → Local FS:** Issue moved to `/sent/`.

## Credentials Inventory
| System | Credential Type | Storage Location | Rotation Cadence |
|---|---|---|---|
| Crawl4AI | None (local) | N/A | N/A |
| Firecrawl MCP | API key | [fill in] | [fill in] |
| Perplexity | API key | [fill in] | [fill in] |
| Beehiiv | Publication API key | [fill in] | [fill in] |
| X / IG / FB | Manual login | Password manager | N/A |

## Single Points of Failure
- **Claude Code availability** — no fallback drafting workflow.
- **Local filesystem** — no documented backup of research/drafts.
- **Operator** — single-threaded through one human at the publish step.

## Known Technical Debt
- X markdown-strip step missing from publish workflow.
- No automated social → Beehiiv funnel (no UTMs, no tracked CTAs).
- No analytics pipe — open rate / CTR / churn lives only in Beehiiv UI.
- Source list lives only in `CLAUDE.md` — not version-controlled, easy to lose.

---

# PART 3 — STANDARD OPERATING PROCEDURE

## Pre-Flight Checklist
- [ ] Claude Code session open with project directory loaded
- [ ] Crawl4AI installed and reachable
- [ ] Firecrawl MCP authenticated
- [ ] Perplexity API key valid (if planning to use it this issue)
- [ ] Beehiiv MCP / API credentials active
- [ ] Last issue's metrics reviewed (opens, CTR, unsubscribes)

## Phase 1 — Research & Source Gathering
**Owner:** Claude Code + scraping/research stack
**Time budget:** 15–20 min

1. Define coverage window (e.g., "events from [last issue date] to [today]").
2. Apply the **Scraping & Research Decision Rule** (Part 2):
   - Default to Crawl4AI for the standing source list (state commissions, UFC/Bellator/PFL/ONE calendars, WBC/WBA/IBF/WBO pages, Tapology, BoxRec).
   - Fall back to Firecrawl on any site where Crawl4AI fails.
   - Use Perplexity for narrative context, breaking storylines, or anything not worth a full scrape.
3. Output a raw data dump: fights, results, upcoming cards, storylines.
4. Spot-check 2–3 results against a second source before drafting.

**Stop condition:** Verified items in hand to fill every standard section.

## Phase 2 — Drafting
**Owner:** Claude Code
**Time budget:** 20–30 min

1. Feed verified research into the drafting prompt.
2. Generate in order:
   - Subject line (A/B variants if available)
   - Preview text (90 char max, no repeat of subject)
   - Lead section — biggest story
   - Results recap — scannable
   - Upcoming cards — next 7–14 days
   - Closing hook — one storyline to watch
3. Review pass: cut AI filler ("In the ever-evolving world of…").
4. Verify every name, record, and result against the research dump.

**Stop condition:** Reads like a human wrote it. Every fact is traceable.

## Phase 3 — Social Adaptation
**Owner:** Claude Code
**Time budget:** 10 min

1. Generate platform-specific posts:
   - **X:** 2–3 posts, **plain text only — no markdown, no asterisks, no headers**
   - **Instagram:** 1 caption + image suggestion
   - **Facebook:** 1 post, slightly longer than X
2. **Critical:** Run X output through markdown-strip step before scheduling.
3. Every social post includes a CTA + Beehiiv subscribe link.

**Stop condition:** Clean plain-text social, every post has a subscribe CTA.

## Phase 4 — Publish
**Owner:** Claude Code via Beehiiv
**Time budget:** 5–10 min

1. Push draft to Beehiiv.
2. Manual review in Beehiiv UI:
   - Desktop + mobile render
   - Click every link
   - Confirm sender, reply-to, segment targeting
3. Schedule or send.
4. Cross-post social.

**Stop condition:** Issue live, social queued, confirmation email received.

## Phase 5 — Post-Send (within 48 hours)
**Owner:** You
**Time budget:** 10 min

1. Log metrics: subscribers at send, open rate, CTR, unsubs, 48hr new subs.
2. Note anomalies.
3. Update this file if any standing fact changed.

## Standing Rules
- **Never** send without a manual eye on the Beehiiv preview.
- **Never** post to X without the markdown-strip step.
- If a session demands more than ~90 minutes total, the workflow is broken — stop and fix it.
- One source ≠ verified. Always cross-reference.

## Kill / Pause Criteria
Sunset or pause if:
- 4 consecutive issues require >2 hours of manual labor each.
- Open rate drops below `[X]%` for 3 consecutive sends.
- Subscriber growth flat or negative for 60 days with no fixable cause.

---
## Components

### 1. Claude Code — Orchestration Layer
- **Role:** Primary work surface. Handles reasoning, drafting, MCP tool calls, file I/O.
- **Runs on:** Local machine.
- **Project directory:** `[fill in path]`
- **Persistent anchor file:** `CLAUDE.md` at project root — standing instructions, source list, voice/tone guidelines.
- **Failure mode:** If Claude Code is unavailable, the pipeline halts. No fallback drafting workflow.

### 2. Crawl4AI — Primary Scraper (Default)
- **Role:** High-volume, recurring scrapes of structured pages (athletic commission results, event calendars).
- **Why default:** Open-source, free — zero per-scrape cost. Aligns with token/cost discipline required to scale to six/seven figures.
- **Use when:** Source is reachable, static-ish HTML, and the scrape pattern repeats issue-over-issue.
- **Failure mode:** JS-heavy / anti-bot sites may fail or return incomplete data → fall back to Firecrawl.

### 3. Firecrawl MCP — Fallback Scraper
- **Role:** Cleanup scraper for sites where Crawl4AI fails (JS rendering, anti-bot, dynamic content) or when cleaner markdown extraction is needed.
- **Why fallback (not default):** Paid per request. Used sparingly to control cost.
- **Auth:** API key stored in `[fill in: 1Password / .env / config location]`
- **Failure mode:** Rate limit or outage → blocks research phase only if Crawl4AI already failed on that source.

### 4. Perplexity — Research & Synthesis Layer
- **Role:** Situational use, decided per-issue. Three valid use cases:
  - **Narrative / context queries** — "what's the storyline going into Saturday's main event"
  - **Source discovery** — finding new coverage outlets or commission pages
  - **Light scraping alternative** — when a synthesized answer beats raw HTML
- **Why included:** Fills the gap between Crawl4AI (raw structured data) and Claude Code's own reasoning (which lacks live web access by default). Faster than spinning up a scrape for one-off questions.
- **Access:** API call from Claude Code, or manual operator query pasted in.
- **Auth:** API key in `[fill in location]` (if API), otherwise N/A.
- **Failure mode:** Outage → fall back to Claude Code's built-in web tools or manual research.

### Scraping & Research Decision Rule
| Use Case | Tool |
|---|---|
| Repeating structured scrape (commission results, fight cards) | **Crawl4AI** |
| Crawl4AI failed on a site, or need clean markdown | **Firecrawl** |
| Narrative, breaking news, synthesized answer needed | **Perplexity** |
| Source discovery / "is there a better feed for X" | **Perplexity** |
| One-off lookup, don't need to scrape | **Perplexity** |

If you find yourself reaching for Firecrawl or Perplexity more often than Crawl4AI on repeating tasks, that's an efficiency signal — flag it (see Part 4).

### 5. Beehiiv — Publishing + Distribution
- **Role:** Email delivery, subscriber management, web archive, analytics.
- **Access from Claude Code:** Beehiiv MCP server + REST API as fallback.
- **Auth:** Publication API key in `[fill in location]`.
- **System of record for:** Subscribers, issue archive, open/click/unsubscribe analytics, Boosts config.
- **Failure mode:** Outage delays send; drafts safe in local FS, retry when restored.

### 6. Local Filesystem
- **Role:** Working storage for research, drafts, prompts, Obsidian vault.
- **Proposed structure:**
# PART 4 — EFFICIENCY REVIEW PROTOCOL

**Standing rule:** Anything in this operation running inefficiently must be surfaced to me immediately with a proposed fix. The bar is the six-to-seven-figure scaling goal — every dollar of API spend, every wasted token, every manual step that should be automated, and every weak data source is a tax on that goal.

## What Counts as "Inefficient"

1. **Token waste**
   - Prompts that pull more context than needed
   - Repeated work across sessions (re-scraping, re-summarizing the same data)
   - Verbose model outputs where structured/short would do
   - Using a frontier model for a task a cheaper one handles

2. **Tool misuse**
   - Reaching for Firecrawl when Crawl4AI would work (paying for what's free)
   - Using Perplexity for structured scrapes (wrong tool, weaker data)
   - Using Crawl4AI on a JS-heavy site that keeps failing (should be Firecrawl)
   - Any tool used outside the decision rule in Part 2

3. **Information quality**
   - Sources returning stale, incomplete, or unverified data
   - Manual cross-checks repeatedly catching errors from the same source → drop or replace it
   - Coverage gaps (events, fighters, storylines being missed)

4. **Process drag**
   - Manual steps that recur every issue and could be automated (the X markdown bug is the canonical example)
   - Time-per-issue trending up instead of down
   - Operator review catching the same class of error repeatedly

5. **Cost creep**
   - Monthly tool spend rising without a matching subscriber/revenue increase
   - New tools added without retiring old ones
   - Any single line item that, if doubled, wouldn't be justified by the output

## How Surfacing Works

When Claude (in any session, this one included) notices an inefficiency, the report should include:

- **What's inefficient** — specific component, prompt, or step
- **Why it matters** — token cost, time cost, quality cost, or revenue ceiling
- **Proposed fix** — concrete change (swap tool, rewrite prompt, automate step, drop source)
- **Tradeoff** — what the fix costs to implement vs. what it saves
- **Impact on the six/seven-figure goal** — does this fix unlock scale, or just polish?

## Review Cadence
- **Per-session:** Surface inefficiencies as they're noticed, in the same response.
- **Per-issue (post-send):** Quick scan — anything from this issue worth flagging?
- **Monthly:** Full review of tool spend, time-per-issue trend, source quality, and subscriber growth vs. cost.

---

## Related Notes
- [[Claude Code]]
- [[Crawl4AI]]
- [[Firecrawl MCP]]
- [[Perplexity]]
- [[Beehiiv API]]

## Distribution

## Related Notes
- [[Context]]
- [[SOP]]
- [[Claude Code]]
- [[Firecrawl MCP]]
- [[Beehiiv API]]