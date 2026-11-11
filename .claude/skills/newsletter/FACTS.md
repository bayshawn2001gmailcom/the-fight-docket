# Standing Facts — Fight Docket

Verified facts the writer needs at the start of every issue. Read this before
researching (Step 0). These are settled; do not re-derive them from memory each
week, and do not contradict them without a primary source that says otherwise.

If a fact here turns out wrong, correct it here with the date and the source,
and log the correction in LESSONS.md. A fact that is contradicted gets dropped,
not argued with.

---

## Rights and money (verified)

- **Paramount holds US UFC rights** under a 7-year, ~$7.7B deal that took
  effect January 2026. Any claim that TKO is negotiating UFC rights with ESPN
  is false; grep every draft for `ESPN` (see LESSONS.md).
- **UFC revenue, Nov 9 issue:** $519.2M for the reported quarter, up 60%,
  $285.3M EBITDA, about 55 cents on the dollar. That 55% margin ended up in a
  legal brief; it is the angle, not just a number. (Source: Nov 9, 2026 issue;
  re-verify before reusing in a later issue.)
- **Zuffa Boxing:** 12 events in 2026 at the time of the Nov 16 draft.
  Garcia–Benn Super Fight, Sept 12, ~19,000 attendance, $8M-plus gate.
  Roster 100+ fighters. Sela (not TKO) covers Conor Benn's reported $15M
  one-fight purse. Zuffa Boxing 13, Nov 14, Riyadh.
- **WWE revenue:** $399.3M, down 1% (Nov 16 draft period).

## Sources that lie or break

- `espn.com/mma/results` and `espn.com/boxing/results` are dead 404s that
  return a full HTML error page. A scrape "succeeds" with nav junk. Do not
  use them.
- Aggregators disagree on dates. Boxing247 vs DAZN disagreed on Nov 2026
  dates. Confirm every schedule bout on the promoter's or broadcaster's own
  page.
- Boxing record sources disagree. boxingnews.com printed wrong records for
  Clarke vs Billam-Smith (Nov 7, 2026). Records need two agreeing sources.

## Fight timing (researched Nov 7, 2026)

- UFC numbered, Paramount+ era: early prelims 5pm ET, prelims 7pm, main card
  9pm, main event walks ~11:00–11:30pm, wraps ~10:45pm–12:30am.
- UFC Fight Night: prelims 5pm, main card 8pm, main event ~10:00–10:30pm,
  done ~10:45–11:30pm. Apex: main event ~9–10pm.
- Boxing US: broadcast 7–8pm ET (9pm big PPVs), ring walks ~11pm–midnight,
  done ~11:45pm–1am. UK boxing: ring walks 10–11pm GMT = 5–6pm ET, done
  ~6–6:30pm ET.
- The Sunday 5am sweep lands complete results.

## Photos (verified)

- Licensed headliner photo library in `assets/fighters/`: 32 fighters, real
  photos with credits. No AI likenesses of real fighters, ever.
- Result cards post only when the winner has a licensed photo; otherwise the
  card is skipped and logged, and the tweet still posts.
- Section-header images are AI-made backgrounds with no faces.
- Missing from the library (cards skip): Adames, Warburton, Opetaia, Kabayel,
  Clarke, Buatsi, Hutchinson, Cortes-Acosta, Johnny Walker, Olascuaga,
  Pacheco, Zhang Weili, Crawford, Ennis, Teofimo Lopez, Dubois, Serrano,
  Katie Taylor, Schofield, Fundora, Vanhouter, Suarez, Gabriela Fundora.

## Platform facts

- **Beehiiv Free plan:** plain paste, no Custom HTML block. Native Poll block
  is paywalled, so the poll runs as text. Drafts over ~100KB warn they "may
  get clipped by Gmail."
- **Instagram:** needs JPEG for some cards; convert before posting if the
  Graph API rejects a PNG. Feed captions carry no clickable links. Clickable
  paths are the Story Link sticker, the bio link, and the Facebook first
  comment.
- **X:** Monday thread is manual, from the staged file, only after approval.
  `twitter_thread.yml` still runs plain `post_twitter_thread.py`, which drafts
  and posts a NEW thread. Do not fire that workflow.
- **GitHub Actions:** cron runs land hours late. `post_live_result.py` always
  exits 0, so a green run proves nothing; the commit log and
  `posted_results.json` are the real record.
- **Gemini:** result workflows failed Oct 18–Nov 5 on 402
  RESOURCE_EXHAUSTED until credits were topped up. Watch for 402s as the
  first sign of a silent outage.
- **Firecrawl v2 (migrated Nov 11, 2026):** all 5 crawler scripts call
  `api.firecrawl.dev/v2/scrape`. v1 returns 410 after Dec 10, 2026. JSON
  extraction uses `formats: [{"type": "json", "prompt": ...}]`; the old
  top-level `jsonOptions` is gone in v2. `maxAge: 0` in
  `post_live_result.py` still forces a fresh fetch.
- **Mobile Gmail:** tables wider than ~360px crush on a phone. The 6-column
  Legal Tracker squeezed to ~55px per column in the Nov 9 issue and the text
  broke mid-word. Wrap tables in a horizontal-scroll div (`overflow-x:auto`,
  table `min-width:600px` Legal Tracker / `520px` Schedule). Media queries
  do NOT work in Gmail. Verify at 375px wide before shipping.

## Cadence and rules (standing)

- Write the issue Sunday night AFTER the weekend fights are final. Shawn
  approves Monday. Muse sends Monday after approval. Social posts are
  approved by name and posted on their own days, never all at once.
- Main Story event must be within 7 days of the issue date (staleness rule).
- Every main story lands one clear position in Why it matters (Take rule).
- Never re-upload fight video clips. Link official free highlights only.
  Results as text with real licensed photos.
- Author photo/bio parked; Shawn to supply.
