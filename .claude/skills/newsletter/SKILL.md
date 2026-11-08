---
name: newsletter
description: Build a complete Fight Docket issue on demand — research the weekend's boxing and MMA live from primary sources, write all 7 sections, generate and verify images, put the final HTML on the clipboard, and stage the X thread and Instagram assets for approval. Use when asked to create, build, or write the newsletter for a date.
---

# Build a Fight Docket Issue

Replaces the old Monday cron pipeline. Everything is researched at the moment it is
asked for, because the thing that broke every previous issue was Gemini writing
business, legal and rumor copy from stale recall. **You research; you do not ask a
model to remember.**

Target: about 20 minutes, one pass, nothing shipped that has not been verified.

---

## Step 0 — Fix the date and the windows

The issue date is whatever the user asked for. If they did not say, use the most
recent Monday. Derive two windows from it:

- **Results window:** the Thursday before the issue date through the issue date.
  Catches Friday, Saturday and Sunday cards. Never assume a card was on Saturday;
  check each result's actual date, because separate cards get collapsed together.
- **Previews window:** issue date through +3 weeks.

Announce both windows before you start so the user can correct you cheaply.

**Staleness rule (hard guardrail, added Nov 8, 2026 after the Fundora miss).**
The Main Story event must have happened within 7 days of the issue date. A fight
from Oct 17 cannot lead a Nov 16 issue. If no fight in the results window
qualifies as the lead, the Main Story must be a business or legal development
from within the window, not an older fight. Never lead with a fight older than
7 days. Check the Main Story event date against the issue date before writing,
and again in Step 4 verification. A stale lead fails verification.

---

## Step 1 — Research, primary sources only

Run searches in parallel. Do not accept a single source for anything that will
appear as a number in the issue.

**Results (usually reliable):** `ufc.com/events`, `sherdog.com/events/recent`,
Wikipedia event pages (good for attendance, gate, bonuses, full cards),
`boxingscene.com/results`, ESPN, `danrafael.substack.com/archive`.

**Business, legal and rumor (where every past issue went wrong):** go to the
primary source. Company press rooms and investor pages for TKO and Paramount,
court filings and law-firm case pages for litigation, the promotion's own
announcement for a signing.

`espn.com/mma/results` and `espn.com/boxing/results` are dead 404s that return a
full HTML error page, so a scrape of them "succeeds" with nav junk. Do not use them.

### The standing fact-check list

Every one of these has shipped as an error before. Check each explicitly:

- **Champion status.** Verify who actually holds a belt before calling anyone
  champion, and verify *how* they won it. Past errors: Topuria called featherweight
  champion, O'Malley called bantamweight champion, Romero's belt credited to the
  wrong opponent.
- **Records.** Get the record *entering* and *after*. Sources routinely print the
  post-fight record while describing the fighter before the fight.
- **Division.** Confirm the weight class of a title fight. Easy to conflate.
- **Docket numbers.** Never publish one you have not seen in a source. Invented
  case numbers have shipped before.
- **Dates.** A late main event in Las Vegas is reported as the next day by UK
  outlets. Use the card's local date.
- **Scorecards.** Read the actual cards before calling a fight lopsided. A 48-47
  means somebody won rounds.
- **Is it new?** Before writing Business Intel, grep the previous two issues:
  ```
  grep -oE '(Paramount|TKO|ESPN|DAZN|merger|rights deal)' newsletter_<prev>.html | sort | uniq -c
  ```
  A real deal recycled as breaking news is as bad as a fake one. If last week led
  with it, find a fresh angle or a different story.
- **Grep the finished draft for `ESPN`.** The phantom "TKO in exclusive negotiation
  with ESPN for UFC rights" hallucination has returned three times. Paramount holds
  US UFC rights under a 7-year, ~$7.7B deal that took effect January 2026.
- **Confidence calibration.** If a fighter said it on record in an interview, it is
  not a 0.40 rumor.
- **Whose card was it?** Promoter ownership of title inventory is usually the real
  business story. Always note which promotion ran the event.

---

## Step 2 — Write the issue (business-of-sports format, decided 2026-11-05)

The lane is a weekly boxing and MMA **business** digest (models: Huddle Up, Front
Office Sports, Extra Points). Results and rumors are covered faster elsewhere; the
edge is money and law. Monday morning ET, about a 5-minute read. Sections in order:

1. **This Week in 60 Seconds** — 3 bullets, each ending in a source link.
2. **Main Story** — ONE numbers-led essay, 400-600 words, on a fight-business or
   legal development. Numbers in the first paragraph (purse, rights fee, revenue,
   damages, valuation). Close with **Why it matters** and **What to watch**. Its
   headline is the Beehiiv title and subject line. **The Take:** every main story
   must land one clear position, not just numbers. One sentence that says what
   the writer believes the numbers mean and who is wrong or exposed because of
   them. A reader should be able to argue with it. If the draft has no sentence
   a reader could disagree with, it has no take. Rewrite the close until it
   does. The take lives in Why it matters, not in a separate section.
3. **Business Intel** — 4-6 briefs, 2-3 sentences each (rights deals, sponsors,
   promoter and manager moves, gate/PPV numbers, fighter pay). Each ends with a
   number or a link.
4. **Legal Tracker** — a TABLE: case or matter | court or body | last movement
   (date) | next date | money at stake | source link. Public filings and reported
   items only. Link every row. Never invent a docket number or a date.
5. **Fight Schedule** — a TABLE for the next 7 days: date | fight | broadcaster |
   title at stake. Top 5-7 bouts. Confirm each on the promoter's or broadcaster's
   own page; aggregators disagree on dates (Boxing247 vs DAZN did on Nov 2026).
6. **The Number** (Fighter Spotlight) — MONTHLY only, a data profile: reported
   career purses, next fight, contract status, social following.
7. **Sources and Further Reading** — every substantive claim, linked.
8. **Poll** — one question, 3 options. 9. **Referral footer.**

**Rumors are cut by default.** At most 2-3 items under "Reported, not confirmed",
each with a named source publication, a confidence label, one sentence and a link.

**Voice: Dan Rafael.** Plain first sentences, names first, active headlines,
records as `(23-2, 13 KOs)`. **No em-dashes or en-dashes.**

**Files:** `newsletter_YYYY-MM-DD.html` (styled, brand colors black `#0A0A0A`, red
`#C8102E`, gold `#C9A84C`, every block with its own dark background and inline text
color) and `newsletter_YYYY-MM-DD_native.html` (plain h3/p/ul/table version for
Beehiiv's native editor). Reference: the 2026-11-09 issue.

---

## Step 3 — Images (one per section: 6, or 7 with The Number)

Write prompts to `prompts/weekly_prompts.json` (`issue_date` + `prompts` array of
`{section, prompt}`; sections `intro`, `main_story`, `business`, `legal`,
`schedule`, `spotlight`, `sources`), then:

```bash
PYTHONUTF8=1 python build_newsletter_images.py newsletter_YYYY-MM-DD.html
```

It generates with Nano Banana 2 into `assets/newsletter_images/nb2_<date>_<section>.jpg`,
writes 1200px web copies to `.tmp/newsletter_images/nb2_<date>_<section>_web.jpg`,
and points the HTML at the public GitHub raw URLs. **No ImgBB** (those links are
dead). The images must be pushed before Muse builds the draft.

Style: real sports photojournalism, real venues, real moments, brand accent colors.
The photo must say what the section is about (legal = courtroom or documents,
business = boardroom or money). No generic silhouettes-in-smoke or dark stock looks.
Do not generate photorealistic faces of real fighters or render real logos: a
fake photo of a real person in a news product misleads readers and carries
right-of-publicity risk. Show fighters from behind, mid-motion, or by setting.

---

## Step 4 — Verify. Do not skip and do not eyeball the source.

```bash
PYTHONUTF8=1 python verify_issue.py newsletter_YYYY-MM-DD.html
```

Renders the Beehiiv worst case (style block stripped, outer container gone, white
page), then checks that all 6 or 7 section images load at full size, that no paragraph falls below
3:1 contrast, and that there are no em-dashes. Exit 0 means safe to paste.

It writes a full-page screenshot next to the output. **Open it and look at it.**

Images only load after they are pushed to GitHub, so run this after the push.

**Staleness check (part of verification).** Before calling the issue done, confirm
the Main Story event date is within 7 days of the issue date. If it is older,
the issue fails verification. Rewrite the lead around a timely event.

---

## Step 5 — Deliver to the repo for Muse

Muse (a second agent) picks the issue up from GitHub, creates the Beehiiv draft
(Free plan: plain paste, no Custom HTML block), adds images by repo URL and fixes
what the paste loses. Muse never sends. The user approves every issue.

So delivery is: commit `newsletter_<date>.html`, `newsletter_<date>_native.html`,
`prompts/weekly_prompts.json`, `assets/newsletter_images/nb2_<date>_*` and
`.tmp/newsletter_images/nb2_<date>_*_web.jpg`, push to `main`, then tell the user
the issue is ready and give the title as a plain copy-paste line.

---

## Step 6 — Stage social, then post only what is approved

The user's standing choice is stage-and-approve. Generate everything, show it,
and wait for an explicit go.

```bash
PYTHONUTF8=1 python post_twitter_thread.py --dry-run   # writes .tmp/thread_<issue>.txt
PYTHONUTF8=1 python ig_content_generator.py            # 4 cards + captions, marked NOT approved
```

Show the thread text and the four cards. **Look at the cards yourself first** —
the templates have shipped clipped watermarks and stranded text before.

When the user says go:

```bash
PYTHONUTF8=1 python approve_week.py            # flips approved:true in current_week.json
PYTHONUTF8=1 python post_twitter_thread.py --from-file .tmp/thread_<issue>.txt  # posts the approved thread
PYTHONUTF8=1 python post_instagram_weekly.py --card preview   # Monday's IG + FB post
```

**Monday's preview card has no cron.** It used to ride along with
`weekly_ig_content.yml`, which is now disabled, so this run is the only thing
that posts it. Forgetting it means Monday has no social presence at all.

The rest of the week drips automatically from the crons, and they will only
post cards that `approve_week.py` has signed off:

| Day | Card | Posted by |
|---|---|---|
| Mon | Newsletter preview | **this run, manually** |
| Tue | Fight result | cron |
| Thu | Fight announcement | cron |
| Fri | Quote card | cron |

Instagram needs JPEG for some cards; convert before posting if the Graph API
rejects a PNG. Nothing posts to X, Instagram or Facebook without an explicit go.

## Step 7 — Commit and push

The user's workflow is repo-first: commit and push to `main` so Muse can pick it up.
Nothing is sent or published from here.

---

## What the user has called unacceptable

An issue with no images. Body text that renders invisible in Beehiiv. `<div>`
wrappers instead of inline styles on each `<p>`. Stale or hallucinated fight
previews. A Main Story about a fight more than 7 days old. inject.js pasted as visible text in the newsletter body. Em-dashes.
Multi-MB images that silently fail to load.
