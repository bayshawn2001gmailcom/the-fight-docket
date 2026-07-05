# The Fight Docket — Claude Instructions

These rules govern Claude's behavior in this project.

---

## Image Generation Workflow

All images are generated with **Nano Banana 2** (Gemini 3.1 Flash Image Preview) via `nano_banana_gen.py` locally or `generate_images_action.py` in GitHub Actions. FLUX is a last-resort fallback only if Nano Banana 2 has a catastrophic, unrecoverable failure.

Images are saved to `assets/newsletter_images/` automatically.

---

### Step 1 — Read the Story, Find the Core

Before writing a prompt, identify:
- **The Subject** — what is this story literally about?
- **The Emotion/Tension** — what does the reader *feel* reading it?

The image should capture both. Let the story's specific theme and emotion drive every creative decision.

---

### Step 2 — Build a Creative, Story-Specific Prompt

Reference `ROLES/IMAGE_STYLE_GUIDE.md` for style options, subject-to-visual mapping, and prompt structure. 

Key principles:
- **Vary the style** — don't default to the same look every week. Rotate through cinematic, documentary, abstract, fine art, atmospheric, etc. based on what serves the story.
- **Let the subject range widely** — legal stories, money stories, fight announcements, human interest, regulatory drama all call for different visuals. Use the full creative range.
- **Color follows mood** — warm for human interest/legacy, cold blue for power/legal, high contrast for action, desaturated for corruption/dispute. Don't apply the same palette to every image.
- **Named fighter matchups** — if a section mentions two fighters by name facing each other, generate a standoff/confrontation image using silhouettes, shadow figures, from-behind shots, or two pairs of gloves. No identifiable faces — right-of-publicity legal line, not a style choice.
- **No faces, no logos** — the only two rules that never change.

---

### Step 3 — Generate

**Nano Banana 2 (default):**
```bash
python nano_banana_gen.py "<your prompt here>"
# Optional flags:
#   --aspect-ratio 16:9   (default: 1:1)
#   --resolution 2K       (default: 1K; choices: 512, 1K, 2K, 4K)
#   --image-only          suppress accompanying text output
```
Requires `GEMINI_API_KEY`. Install once: `pip install google-genai pillow`.

**FLUX (catastrophic fallback only):**
```bash
python flux_gen.py "<your prompt here>"
```
Requires `OPENROUTER_API_KEY`.

---

## Notes

- Never generate an image speculatively. Always tie it to a specific article or section.
- Images land in `assets/newsletter_images/`. Review visually before including in any issue.
- For the weekly automated pipeline: prompts are written to `prompts/weekly_prompts.json` by the Cowork task, then GitHub Actions generates the images at Sunday 7:15 PM EDT.

---

## Beehiiv HTML Injection — Clean Posting Workflow

**Root cause of spacing/font bugs:** Injecting raw HTML via `execCommand('insertHTML')` into Beehiiv's ProseMirror editor creates empty block elements:
- Blank lines between `<p>` tags → empty `<p>` nodes
- `<div class="subtitle">` wrappers → orphaned empty `<div>` nodes

**Fix — always pre-process HTML before injecting:**

```bash
# Step 1: Run the pre-processor on the HTML file
python beehiiv_prep.py Fight_Docket_YYYY-MM-DD.html
# Outputs: Fight_Docket_YYYY-MM-DD_clean.html + Fight_Docket_YYYY-MM-DD.inject.js
```

The `.inject.js` file contains the full browser console script with clean HTML already embedded. Copy-paste it into the Beehiiv editor console.

**If injection was already done without pre-processing**, run this cleanup script in the browser console on the editor page:

```javascript
(function() {
  const editor = document.querySelector('.ProseMirror');
  editor.focus();
  let removed = 0;
  Array.from(editor.querySelectorAll('p')).forEach(p => {
    if (p.textContent.trim() === '') { p.remove(); removed++; }
  });
  Array.from(editor.querySelectorAll('div')).forEach(d => {
    if (d.className === '' && d.textContent.trim() === '' && !d.querySelector('img')) {
      d.remove(); removed++;
    }
  });
  editor.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true }));
  console.log('Removed ' + removed + ' empty elements. Check for Synced status.');
})();
```

Wait for "Synced" status to confirm autosave.

---

## Social Media Accounts (set up April 21, 2026)

### Instagram — @thefightdocket
- Profile photo: `fight_docket_logo.png` (black/red/gold BigShoulders-Bold design)
- Bio: "🥊 Boxing & MMA news, fight breakdowns & the stories behind the sport / 📰 Weekly newsletter — subscribe below"
- Account type: Personal (linked alongside @atlantaturfdoctor and personal account)

### Facebook — The Fight Docket Page
- URL: https://www.facebook.com/profile.php?id=61567987746089
- Category: Sports & recreation
- Cover photo: `fight_docket_fb_cover.png` (text in top 42%, red design fills bottom half — avoids profile circle overlap)
- Profile photo: `fight_docket_logo.png`
- Bio: "Boxing & MMA news, fight breakdowns & the stories behind the sport. Weekly newsletter — subscribe at thefightdocket.com"

---

## Instagram Content Automation

### Brand assets
- Logo: `fight_docket_logo.png` (1080x1080, also used as FB profile photo)
- FB Cover: `fight_docket_fb_cover.png` (1640x624, text in top 42% only)
- Brand colors: Black `#0A0A0A`, Red `#C8102E`, Gold `#C9A84C`, White `#F0EDE8`
- Fonts: BigShoulders-Bold (headlines), InstrumentSans (body/tags), Lora-Bold (quotes)

### Content pipeline
- Templates: `ig_templates.py` — 4 functions: `newsletter_preview()`, `fight_announcement()`, `fight_result()`, `quote_card()`
- Generator: `generate_weekly_ig.py` — edit the `WEEK = {}` block each issue, then run to produce all 4 graphics
- Output folder: `instagram_content/` — PNGs + captions txt file per issue
- Scheduled task: **fight-docket-ig-content-reminder** — runs every Monday 9am, auto-reads newsletter, updates generator, produces graphics + captions

### Weekly posting schedule
| Day | Post type |
|-----|-----------|
| Monday | Newsletter Preview (new issue announcement) |
| Tuesday | Fight Result (weekend recap) |
| Thursday | Fight Announcement (upcoming card hype) |
| Saturday | Quote Card (engagement post before fight night) |

### To generate content manually
```bash
# 1. Edit the WEEK = {} block in generate_weekly_ig.py with this issue's data
# 2. Run:
python "The fight Docket/generate_weekly_ig.py"
# 3. Review PNGs in instagram_content/
# 4. Use captions from [issue]_captions.txt
```

---

## Full Automation Pipeline (rebuilt & verified July 5, 2026)

**Account credentials:**
- Instagram: `thefightdocket@gmail.com` / `@thefightdocket`
- Twitter/X: `@thefightdocket`
- GitHub repo: https://github.com/bayshawn2001gmailcom/the-fight-docket

**Weekly automation schedule (all crons live on GitHub as of 2026-07-05):**
| Day/Time (EDT) | Workflow | Script |
|----------|----------|--------|
| Fri 6pm | `friday-crawl-fights.yml` | `upcoming_fights_crawler.py` → upcoming_fights.json |
| Fri 9pm/11pm/12:30am | `friday-night-results.yml` | `post_live_result.py` → X + IG + FB (deduped) |
| Sat 9pm/11pm | `saturday-night-results.yml` | `post_live_result.py` → X + IG + FB (deduped) |
| Sun 6am | `sunday-post-results.yml` | `post_live_result.py` final sweep — catches missed results |
| Sun 7:15pm | `generate_images.yml` | `generate_images_action.py` → newsletter images from prompts |
| Mon 8am | `newsletter_pipeline.yml` | `newsletter_generator.py` → newsletter HTML |
| Mon 10am | `twitter_thread.yml` | `post_twitter_thread.py` → 6-tweet thread |
| Mon 11am | `weekly_ig_content.yml` | `ig_content_generator.py` → 4 IG graphics + captions |
| Tue/Thu/Sat 12pm | `weekly_ig_post_*.yml` | `post_instagram_weekly.py` → IG + FB card |

**Key scripts:**
- `newsletter_generator.py` — Firecrawl + Gemini full newsletter automation
- `ig_content_generator.py` — auto-generates 4 IG graphics from weekly_ig_data.json
- `post_twitter_thread.py` — Gemini writes + tweepy posts thread to @thefightdocket
- `post_live_result.py` — ALL fight-night results (Fri/Sat/Sun): crawl → Gemini → X + IG + FB via Graph API
- `post_fight_results.py` — DEPRECATED (instagrapi-based; replaced by post_live_result.py)
- `upcoming_fights_crawler.py` — Friday pre-crawl via Firecrawl
- `beehiiv_prep.py` — pre-processes newsletter HTML for clean Beehiiv injection
- `generate_weekly_ig.py` — manual fallback for IG content (edit WEEK block)

**Deduplication:** `posted_results.json` tracks every result posted live so re-runs don't double-post.

---

## HARD-WON LESSONS — read before touching the automation (July 5, 2026 debugging session)

These bugs silently broke the pipeline for up to 9 weeks. Do not reintroduce them.

1. **Local changes do NOT reach GitHub on their own.** The Friday crawler was fixed locally
   July 3 but GitHub ran the broken copy for 9 straight weeks. As of 2026-07-05 this folder
   IS a git repo (shallow clone, origin = GitHub, autocrlf=true) — so the fix is now:
   `git add <files> && git commit && git push` after any script/workflow change, then verify
   the commit landed on GitHub main. First push may prompt a GitHub browser login (Git
   Credential Manager). Note: git history is shallow (depth 1); run `git fetch --unshallow`
   if full history is ever needed.

2. **Never use instagrapi in GitHub Actions.** Instagram blocks Actions IPs — it hangs until
   the job times out (the old Sunday workflow burned 1-hour timeouts every week). Always use
   the official Graph API (see `post_instagram_weekly.py` / `post_to_instagram()` in
   `post_live_result.py`): ImgBB upload → media container → poll status → publish.

3. **Strip credentials in every script:** `os.getenv(k).strip().strip("'\"")`. A trailing
   newline pasted into a GitHub secret caused weeks of Twitter 401s even though the token
   itself was valid. The `_tok()` helper exists in both posting scripts — use it for ALL creds.

4. **Workflow `secrets.X` names must match what's actually stored.** A workflow referencing a
   secret that doesn't exist resolves to an empty string — no error, just silent 401s.
   Both `TWITTER_ACCESS_SECRET` and `TWITTER_ACCESS_TOKEN_SECRET` exist as secrets; scripts
   accept either env name.

5. **Dead scrape sources fail silently.** `espn.com/mma/results` and `espn.com/boxing/results`
   are 404s that return a full HTML error page — the crawl "succeeds" with nav junk. Current
   good sources: `ufc.com/events`, `sherdog.com/events/recent`, `boxingscene.com/results`,
   `boxingscene.com/articles`. `firecrawl_scrape()` now checks `metadata.statusCode >= 400`.
   Use `onlyMainContent: true` on all Firecrawl scrapes.

6. **Don't starve Gemini of content.** The old code sent 2,500 chars/source truncated to 8K
   total (all nav junk) → 0 results extracted every time while runs showed green. Current
   budgets: 8K/source, 30K to Gemini. Boxing goes 12 rounds — the extraction schema must say
   round 1–12, not 1–5, or Gemini drops late-round boxing stoppages (this hid Mason vs Bell).

7. **"Success" ≠ "posted."** These scripts exit 0 when nothing is found, so green runs can mean
   zero output for weeks. When auditing, check `posted_results.json` / bot commits / the actual
   social accounts, not just run status.

8. **Scheduled Cowork/Claude tasks are machine-dependent.** The "CMA Fight Night Watchdog" that
   replaced the night crons silently ceased to exist, killing all fight-night coverage. Standing
   automation belongs in GitHub Actions crons; Claude-side scheduled tasks are for reminders only.

9. **Gemini 503s crash the posting script** (no retry wrapper yet). The multiple crons per fight
   night absorb one-off failures; if adding new single-shot workflows, add a retry.

**Fixed 2026-07-05 (evening):** git link established (this folder is now a real clone);
image generation moved into the Monday pipeline (`newsletter_pipeline.yml`) so images match
the current issue — the Sunday image cron is gone (its push-trigger never fired because
GITHUB_TOKEN pushes don't trigger workflows).

**Known open items:** Carrington vs Palacios (Jul 4) posted to IG/FB but never tweeted
(Twitter was still broken at that moment). Local working tree has minor drift vs GitHub
(newsletter_2026-06-29.html, some locally-generated images) — reconcile with git when convenient.
