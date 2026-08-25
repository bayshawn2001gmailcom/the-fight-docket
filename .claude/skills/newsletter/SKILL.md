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

## Step 2 — Write the 7 sections

Order: Editor's Note, Main Story, Legal Tracker, Rumor Mill, Fight Card Previews,
Business Intel, Fighter Spotlight.

**Voice: Dan Rafael.** State what happened plainly in the first sentence. No scene
setting, no rhetorical questions, no "what this signals to the market is." Headlines
are active, names first, one vivid verb. Full formal title names on first reference.
Records as `(23-2, 13 KOs)`. Scorecards in order. Restrained but real adjectives. A
wry line inside straight reporting is right; hype words are not.

**No em-dashes.** Not `—`, not `&mdash;`. Restructure the sentence; do not swap in
an en-dash. Sweep the finished HTML before delivering.

**Structure rules** are in `newsletter_2026-08-24.html`, the current reference file.
Copy its markup exactly. The two that matter most:

- **Every section carries its own `background-color:#0D0D0D`.** Beehiiv fragments
  the paste and later sections lose any ancestor background. This includes the
  content wrapper, every section div, every divider wrapper, and the blockquote.
- **Every body `<p>` needs inline `style="color:#F2F2E8;"`.** Beehiiv strips the
  `<style>` block. Keep the style block anyway for email clients.
- Divider spacing goes in the wrapper's padding, never as the child's margin, or
  vertical margins collapse out and leave white bands.

Rumor Mill uses three confidence levels with left border colors: HIGH `#C5A059`
(0.85-0.95), MEDIUM `#888888` (0.55-0.75), LOW `#444444` (0.25-0.40).

---

## Step 3 — Images

Write 7 story-specific prompts to `prompts/weekly_prompts.json` (schema: `issue_date`
plus a `prompts` array of `{section, prompt}`), then:

```bash
PYTHONUTF8=1 python build_newsletter_images.py newsletter_YYYY-MM-DD.html
```

It generates via Nano Banana 2, **compresses to 1200px/q82 before uploading**,
pushes to ImgBB, and injects each `<img>` after the section's red divider.

Prompt rules from `ROLES/IMAGE_STYLE_GUIDE.md`: vary the style week to week
(cinematic, documentary, fine art, noir, abstract), let color follow mood, and for a
named fighter matchup use silhouettes or gloves. **No faces and no logos are the two
rules that never change.** Look at the images before shipping them.

---

## Step 4 — Verify. Do not skip and do not eyeball the source.

```bash
PYTHONUTF8=1 python verify_issue.py newsletter_YYYY-MM-DD.html
```

Renders the Beehiiv worst case (style block stripped, outer container gone, white
page), then checks that all 7 images load at full size, that no paragraph falls below
3:1 contrast, and that there are no em-dashes. Exit 0 means safe to paste.

It writes a full-page screenshot next to the output. **Open it and look at it.**

If images report broken, warm the ImgBB URLs with curl once and re-run; a fresh
upload is cold for 5-11s and looks identical to a dead link.

---

## Step 5 — Deliver

```bash
python beehiiv_prep.py newsletter_YYYY-MM-DD.html
```

Then put the **raw HTML** on the clipboard, always last, after every other script has
run (`build_newsletter_images.py` leaves inject.js on the clipboard):

```powershell
$html = [System.IO.File]::ReadAllText("<abs path>\newsletter_YYYY-MM-DD.html", [System.Text.Encoding]::UTF8)
Set-Clipboard -Value $html
```

The user pastes that into Beehiiv's `<>` **HTML source editor**, not the visual
editor. `.inject.js` is the browser-console alternative; the two are not
interchangeable.

Give the **Beehiiv post title as a plain copy-paste line**, in a fenced block, not
buried in prose.

---

## Step 6 — Stage social. Do not post.

The user's standing choice is stage-and-approve. Generate, report, and wait.

```bash
PYTHONUTF8=1 python post_twitter_thread.py --dry-run   # if unsupported, generate and print without posting
PYTHONUTF8=1 python ig_content_generator.py            # 4 PNGs + captions in instagram_content/
```

Show the thread text and name the generated files. Post to X, Instagram or Facebook
**only after the user says go**, in that message or a later one. Instagram cards must
be converted to JPEG before the Graph API will accept them.

---

## Step 7 — Commit

Commit the issue, images, prompts and clean/inject files. Do not push unless asked;
say that it is committed locally and offer.

---

## What the user has called unacceptable

An issue with no images. Body text that renders invisible in Beehiiv. `<div>`
wrappers instead of inline styles on each `<p>`. Stale or hallucinated fight
previews. inject.js pasted as visible text in the newsletter body. Em-dashes.
Multi-MB images that silently fail to load.
