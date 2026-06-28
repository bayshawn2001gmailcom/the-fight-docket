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

## Distribution

## Related Notes
- [[Context]]
- [[SOP]]
- [[Claude Code]]
- [[Firecrawl MCP]]
- [[Beehiiv API]]