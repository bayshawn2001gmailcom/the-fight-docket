---
title: The Fight Docket — Context
type: business-context
status: active / early-stage
created: 2026-06-28
tags: [fight-docket, newsletter, beehiiv, combat-sports, ai-pipeline]
---

# ---
title: The Fight Docket — Context
type: business-context
status: active / early-stage
created: 2026-06-28
tags: [fight-docket, newsletter, beehiiv, combat-sports, claude-code]
---

# The Fight Docket — Context

## Identity
The Fight Docket is a **combat sports newsletter** published on **Beehiiv**. Coverage spans MMA, boxing, and adjacent combat disciplines, with an editorial angle that leans on athletic commission data, fight results, and event tracking rather than personality/opinion content.

## Business Model
- **Primary surface:** Beehiiv newsletter (free tier subscribers, with paid tier and ad/boost monetization as the growth path).
- **Monetization levers (future):**
  - Beehiiv Boosts (paid recommendations from other newsletters).
  - Sponsored placements once subscriber count justifies CPM rates.
  - Affiliate revenue (sportsbooks, merch, training gear) — secondary.
- **Reference model:** [[The Rundown AI]] — daily AI-curated newsletter that scaled to 7-figure ad revenue with a small team. The Fight Docket applies the same automation-heavy, low-headcount model to combat sports.

## Distribution
- **Newsletter:** Beehiiv (primary)
- **Social channels (currently underleveraged):**
  - X / Twitter
  - Instagram
  - Facebook
- **Known gap:** Social accounts are **not cross-linked** from the Beehiiv site or from each other. Subscriber funnel is leaky.

## Current Traction (as of last audit)
- Subscriber base is **very small** — pre-product-market-fit territory.
- Social accounts exist but are not driving meaningful traffic.
- No paid acquisition running.
- Content is produced ad-hoc through Claude Code sessions rather than on a fixed editorial cadence.

## Tech Stack
Operations run through **[[Claude Code]]** as the primary work surface. No standing multi-agent pipeline — workflows are executed on-demand via prompted Claude Code sessions.

| Function | How it's handled |
|---|---|
| **Research / scraping** | Claude Code session invoking [[Firecrawl MCP]] against athletic commission sites, event calendars, and fight results |
| **Drafting** | Claude Code generates newsletter copy and social posts from research output |
| **Publishing** | Beehiiv API calls executed from within Claude Code; manual review before send |

### Why Claude Code (vs. a standing agent system)
- Zero infrastructure overhead — no servers, no process managers, no agent orchestration to maintain.
- Fits the **near-fully-automated-or-sunset** rule: time only goes in when an issue is being produced.
- MCP server access (Firecrawl, Beehiiv) gives the same capability surface a custom multi-agent system would, without the maintenance tax.

## Known Issues / Bugs
- **Markdown-rendering bug on X:** Posts get piped from Claude Code output (markdown-formatted) into the X publishing step **without a format-conversion layer**. Asterisks, headers, and bullet syntax leak into tweets. Needs a stripping step in the publish workflow before posting to X.
- **Social → newsletter funnel is broken:** No bio links, no consistent CTA to subscribe.
- **No subscriber retention/engagement loop** — open rates, CTR, and churn not actively monitored.

## Strategic Notes
- Newsletter is a **content/distribution asset**. Treat as long-tail optionality: low time investment via Claude Code, monetize if it scales.
- ROI bar: must remain low-touch. Any week where it demands meaningful manual hours is a signal to either tighten the Claude Code workflow or sunset the project.

## Open Questions
- What's the minimum subscriber count to justify turning on Boosts?
- Is there a niche-within-the-niche (regional commission coverage? amateur circuit data?) that would differentiate vs. larger combat sports newsletters?
- Should the X markdown bug be fixed before or after solving the funnel/cross-linking issue? (Funnel first — no point posting cleanly to dead accounts.)

## Related Notes
- [[Claude Code]]
- [[Firecrawl MCP]]
- [[Beehiiv API]]
- [[The Rundown AI]]