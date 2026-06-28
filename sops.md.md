---
title: The Fight Docket — SOP
type: standard-operating-procedure
status: living document
created: 2026-06-28
tags: [fight-docket, sop, runbook, claude-code]
---

# The Fight Docket — SOP

> Operational runbook for producing and shipping a single newsletter issue. If a step isn't here, it isn't part of the process — add it or remove it.

## Pre-Flight Checklist
Before starting an issue, confirm:
- [ ] Claude Code session is open with project directory loaded
- [ ] Firecrawl MCP is connected and authenticated
- [ ] Beehiiv MCP / API credentials are active
- [ ] Last issue's performance metrics have been reviewed (opens, CTR, unsubscribes)

---

## Phase 1 — Research & Source Gathering
**Owner:** Claude Code + Firecrawl MCP
**Time budget:** 15–20 min

1. Define the issue's coverage window (e.g., "events from [last issue date] to [today]").
2. Prompt Claude Code to scrape the standing source list:
   - State athletic commission result pages (CA, NV, NY, TX, FL at minimum)
   - UFC / Bellator / PFL / ONE event calendars
   - Major boxing sanctioning body pages (WBC, WBA, IBF, WBO)
   - Tapology / BoxRec for cross-reference
3. Output a raw data dump: fights, results, upcoming cards, notable storylines.
4. Spot-check 2–3 results against a second source before drafting.

**Stop condition:** You have at least [X] verified items to fill the issue's standard sections.

---

## Phase 2 — Drafting
**Owner:** Claude Code
**Time budget:** 20–30 min

1. Feed the verified research dump into a drafting prompt.
2. Generate in this order:
   - **Subject line** (A/B variants if Beehiiv tier supports it)
   - **Preview text** (90 chars max, doesn't repeat subject)
   - **Lead section** — biggest story of the week
   - **Results recap** — structured, scannable
   - **Upcoming cards** — next 7–14 days
   - **Closing hook** — one storyline to watch
3. Review pass: cut anything that reads like AI filler ("In the ever-evolving world of…").
4. Verify every fighter name, record, and result against the research dump.

**Stop condition:** Draft reads like a human wrote it and every fact is traceable to a source.

---

## Phase 3 — Social Adaptation
**Owner:** Claude Code
**Time budget:** 10 min

1. Generate platform-specific posts from the newsletter draft:
   - **X / Twitter:** 2–3 posts, plain text only — **no markdown, no asterisks, no headers**
   - **Instagram:** 1 caption + image suggestion
   - **Facebook:** 1 post, slightly longer than X
2. **Critical:** Run X output through a markdown-stripping step before scheduling. Known bug — see Context.md.
3. Every social post must include a CTA + link to the Beehiiv subscribe page.

**Stop condition:** All social copy is plain-text clean and contains a subscribe CTA.

---

## Phase 4 — Publish
**Owner:** Claude Code via Beehiiv API
**Time budget:** 5–10 min

1. Push draft to Beehiiv via API.
2. **Manual review in Beehiiv UI before send:**
   - Render preview on desktop and mobile
   - Click every link
   - Confirm sender name, reply-to address, and segment targeting
3. Schedule or send.
4. Cross-post social adaptations on their respective platforms.

**Stop condition:** Issue is live, social is queued, confirmation email received.

---

## Phase 5 — Post-Send (within 48 hours)
**Owner:** You
**Time budget:** 10 min

1. Log metrics in tracking sheet:
   - Subscribers at send time
   - Open rate
   - CTR
   - Unsubscribes
   - New subscribers gained in 48hr window
2. Note any anomalies (broken link, formatting issue, deliverability problem).
3. Update [[the-fight-docket/context.md]] if any standing fact changed (new bug, new monetization, new channel).

---

## Standing Rules
- **Never** send an issue without a manual eye on the Beehiiv preview.
- **Never** post to X without the markdown-strip step.
- If a session demands more than ~90 minutes total, the workflow is broken — stop and fix the process before producing more content.
- One source ≠ verified. Always cross-reference fight results.

## Escalation / Kill Criteria
Sunset or pause the newsletter if:
- 4 consecutive issues require >2 hours of manual labor each.
- Open rate drops below [X]% for 3 consecutive sends.
- Subscriber growth is flat or negative for 60 days with no fixable cause.

## Related Notes
- [[Context]]
- [[Claude Code]]
- [[Firecrawl MCP]]
- [[Beehiiv API]]