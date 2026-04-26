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

## Instagram Automation Setup (April 26, 2026)

**Account credentials:**
- Email: `thefightdocket@gmail.com`
- GitHub repo: https://github.com/bayshawn2001gmailcom/the-fight-docket

**Automation schedule:**
- **Friday 6:00pm EDT** — `upcoming_fights_crawler.py` crawls UFC.com + BoxRec + ESPN for upcoming weekend fights
- **Sunday 1:00am EDT** — `post_fight_results.py` crawls results, generates image, posts to Instagram
- **Sunday 2:00am EDT** — Retry if results missing (wait 1 hour for full result population)
- **Sunday 4:00am EDT** — Post to Instagram (fresh for followers Monday morning)

**Scripts created:**
- `post_fight_results.py` — main posting workflow (crawls + posts)
- `upcoming_fights_crawler.py` — Friday pre-crawl for backup reference
- `test_instagram_post.py` — manual test script (used Miller vs Pero test 4/26/2026)
- `.env.example` — credentials template (GitHub Secrets: INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, FIRECRAWL_API_KEY, GEMINI_API_KEY)
- `.github/workflows/friday-crawl-fights.yml` — Friday 6pm automation
- `.github/workflows/sunday-post-results.yml` — Sunday 1am-4am automation with retry logic

**Test result (April 26, 2026):**
- Generated branded image for Jarrell "Big Baby" Miller vs Lenier Pero (KO/TKO R1 1:45)
- Image generation ✅ successful
- Instagram posting: attempted via instagrapi (failed due to proxy/connection — Instagram anti-bot measures)
- **Workaround:** Manual post to Instagram while GitHub automation handles future posts

**Next steps:**
1. Set GitHub Secrets (INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, FIRECRAWL_API_KEY)
2. Manually post test_miller_vs_pero.png to @thefightdocket
3. Implement Firecrawl crawling logic in post_fight_results.py (currently placeholder)
4. Test full automation on next fight weekend
