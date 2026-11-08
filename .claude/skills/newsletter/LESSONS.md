# Lessons Learned — Fight Docket

The repo's memory. Every entry is a real failure, correction, or gotcha from a
shipped issue or a run, with the date it happened and what changed because of it.

**How it works (the learning loop):**

1. **Read this file at the start of every issue** (Step 0). The Active checks
   at the top are the patterns to verify against before anything ships.
2. **After every issue, log what went wrong or got corrected here** (Step 8).
   One entry per lesson: date, issue, what happened, what changed.
3. **Promote repeats into the skill.** When a lesson shows up a second time,
   it stops being a log entry and becomes a rule in SKILL.md (fact-check list,
   staleness rule, unacceptable list). The log entry then points at the rule.
4. **Drop what is contradicted.** If a later session proves a lesson wrong,
   mark it SUPERSEDED with the date and the reason. Do not delete it; the
   history is the point.

---

## Active checks

Run these against every draft in Step 4 verification. Each one has shipped as
an error before.

- [ ] Main Story event is within 7 days of the issue date (staleness rule).
- [ ] Grep the draft for `ESPN`. The phantom "TKO in exclusive negotiation
      with ESPN for UFC rights" hallucination has returned three times.
      Paramount holds US UFC rights under a 7-year, ~$7.7B deal effective
      January 2026.
- [ ] Champion status verified for every fighter called champion, and how
      they won the belt.
- [ ] Records checked entering AND after the fight.
- [ ] Weight class confirmed for every title fight.
- [ ] No docket number published unless seen in a source.
- [ ] Dates use the card's local date (a late Las Vegas main event is
      reported as the next day by UK outlets).
- [ ] Scorecards read before calling a fight lopsided.
- [ ] Business Intel grepped against the previous two issues for recycled
      news (see the `grep -oE` command in SKILL.md Step 1).
- [ ] No photorealistic AI faces of real fighters. Fighter photos are real
      licensed photos only; section headers are AI backgrounds with no faces.
- [ ] No em-dashes or en-dashes anywhere in either HTML file.
- [ ] All section images load at full size after push; no image over ~250KB
      without a web copy.
- [ ] No `<div>` wrappers in the native HTML; inline styles on each `<p>`.
- [ ] No `inject.js` or script text visible in the body.

---

## Log

### 2026-11-08 — Fundora lead was 30 days stale

**Issue:** Nov 16 (early draft, scrapped).
**What happened:** The early Nov 16 draft led with Fundora KO Hadribeaj, Oct 17.
Shawn caught it: Oct 17 to Nov 16 is 30 days, not news. The draft was scrapped
and the issue was rewritten fresh Nov 15 after UFC 334.
**What changed:** Hard staleness rule in SKILL.md Step 0 and Step 4. Main Story
event must be within 7 days of the issue date. A stale lead fails verification.
**Status:** Active, promoted to SKILL.md.

### 2026-11-08 — Firecrawl served cached pages up to 2 days old

**Issue:** Result loop, Oct–Nov 2026.
**What happened:** Fight-night result runs "succeeded" with 0 results on
Nov 6 and earlier nights. Root cause: Firecrawl served cached pages.
**What changed:** `post_live_result.py` now sets Firecrawl `maxAge: 0`.
Results are no longer marked posted when tweet + IG + FB all fail.
**Status:** Active, promoted to code (commit `4ba1226d`).

### 2026-11-08 — Thread script drafted a NEW thread instead of posting the approved one

**Issue:** Nov 9 Monday X thread.
**What happened:** `post_twitter_thread.py` invoked plain drafted and posted a
new Gemini thread instead of the approved staged thread.
**What changed:** SKILL.md Step 6 now uses
`post_twitter_thread.py --from-file .tmp/thread_<issue>.txt`. The dry-run hint
in the script prints the `--from-file` command with the actual staged path.
**Status:** Active, promoted to SKILL.md and code (commits `d9397459`,
`762582b3`).

### 2026-11-08 — Result loop silent since Oct 11

**Issue:** Fight-night results, Oct 12–Nov 6.
**What happened:** No results posted after Oct 11. Fundora–Hadribeaj Oct 17
went unposted. Partly a deliberate pause (Nov 6 commits), partly the Firecrawl
cache bug, partly GitHub cron runs landing hours late.
**What changed:** Muse-runner plan written (`muse-runner-plan.md`): Muse checks
sources directly every 30 min Fri/Sat 8pm–1am EST plus a Sun 5am sweep, no
Firecrawl, ~30 min latency. Goes live only after keys arrive and Shawn
approves.
**Status:** Active. `post_live_result.py` always exits 0, so a green run
proves nothing; the commit log and `posted_results.json` are the real record.

### 2026-11-07 — Boxing record sources disagree

**Issue:** Nov 16 early draft (Zuffa Boxing 12).
**What happened:** boxingnews.com printed Clarke 14-2 and Billam-Smith 23-3.
Five other sources agreed Clarke 13-2 (10 KOs), Billam-Smith 22-3 (14 KOs).
**What changed:** Records need two agreeing sources, not one. Added to the
fact-check list.
**Status:** Active, promoted to SKILL.md.

### 2026-11-07 — Walker notice period was 5 days, not 9

**Issue:** Nov 16 early draft (UFC Vegas 124).
**What happened:** Draft said Walker took the Cortes-Acosta fight on nine
days' notice. Sherdog said five.
**What changed:** Notice periods and short-notice claims need a named source.
**Status:** Active.

### 2026-11-06 — Weekly IG drip is dead on two gates

**Issue:** Weekly IG content.
**What happened:** `instagram_content/current_week.json` is the Oct 12 issue,
`approved: false`, stale. The drip needs a new approved issue, not a code fix.
**What changed:** Noted here. The Monday preview card has no cron; the manual
`post_instagram_weekly.py --card preview` run is the only thing that posts it.
**Status:** Active.

### 2026-11-06 — GitHub cron runs hours late

**Issue:** Friday crawl scheduled Fri 23:00 UTC ran Nov 7 02:30 UTC, 3.5h late.
Oct 11 commits landed ~6h late.
**What changed:** Do not rely on GitHub cron timing for fight-night results.
See the Muse-runner plan.
**Status:** Active.

### 2026-11-05 — Gemini credits ran dry (402 RESOURCE_EXHAUSTED)

**Issue:** All social automation, Oct 18–Nov 5.
**What happened:** Every result workflow failed on Gemini 402 errors until
credits were topped up Nov 5, 21:33 EST.
**What changed:** Credits topped up. Watch for 402s as the first sign of a
silent outage; a workflow that exits 0 can still have posted nothing.
**Status:** Active.

### 2026-11-05 — ESPN rights hallucination, third return

**Issue:** Nov 9 issue (and twice before).
**What happened:** The draft claimed TKO was in exclusive negotiation with
ESPN for UFC rights. False. Paramount holds US UFC rights under a 7-year,
~$7.7B deal effective January 2026.
**What changed:** Grep the finished draft for `ESPN` every time. Added to
the fact-check list and to Active checks above.
**Status:** Active, promoted to SKILL.md.

### 2026-11-05 — espn.com results pages are dead 404s

**Issue:** Research, multiple issues.
**What happened:** `espn.com/mma/results` and `espn.com/boxing/results`
return a full HTML error page, so a scrape "succeeds" with nav junk.
**What changed:** Do not use them. Listed in SKILL.md Step 1.
**Status:** Active, promoted to SKILL.md.

### 2026-11-05 — Beehiiv draft clipped by Gmail warning

**Issue:** Nov 16 early Beehiiv draft.
**What happened:** Post is 107KB; Beehiiv warns it "may get clipped by Gmail."
**What changed:** Keep issues lean. If a draft crosses ~100KB, trim before
sending.
**Status:** Active.

### 2026-10-26 — IG templates shipped clipped watermarks

**Issue:** Weekly IG cards.
**What happened:** Card templates shipped with clipped watermarks and
stranded text.
**What changed:** Look at the cards yourself before showing them to Shawn.
Added to SKILL.md Step 6.
**Status:** Active, promoted to SKILL.md.

### Earlier — Champion, record, division, docket, date, scorecard errors

**Issue:** Multiple issues before Nov 2026.
**What happened:** Topuria called featherweight champion, O'Malley called
bantamweight champion, Romero's belt credited to the wrong opponent. Records
printed post-fight while describing the fighter before the fight. Divisions
conflated. Docket numbers invented. Late Las Vegas main events dated the next
day by UK outlets. Fights called lopsided on 48-47 cards.
**What changed:** The standing fact-check list in SKILL.md Step 1. Each item
there is one of these errors.
**Status:** Active, promoted to SKILL.md.

### Earlier — Multi-MB images silently fail to load

**Issue:** Multiple issues.
**What happened:** Images over a few MB silently failed in Beehiiv and in
the verification render.
**What changed:** 1200px web copies for every section image; check they load
at full size after push (Step 4).
**Status:** Active, promoted to SKILL.md.

### Earlier — inject.js pasted as visible text

**Issue:** Multiple issues.
**What happened:** The inject script text appeared in the newsletter body.
**What changed:** Added to the unacceptable list and to Active checks above.
**Status:** Active, promoted to SKILL.md.

### Earlier — Invisible body text in Beehiiv

**Issue:** Multiple issues.
**What happened:** Body text rendered invisible (white on white) in Beehiiv's
editor.
**What changed:** Inline styles with explicit text color on each `<p>`; no
`<div>` wrappers. Verify with the worst-case render in Step 4.
**Status:** Active, promoted to SKILL.md.
