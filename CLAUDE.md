# The Fight Docket — Claude Instructions

These rules govern Claude's behavior in this project. They override default behavior and must be followed exactly.

---

## Image Generation Workflow

Every image generated for The Fight Docket must follow this four-step process, in order, without skipping steps.

### Step 1 — Extract Context Anchors

Before writing a prompt, read the article or section content and identify **Context Anchors**: the specific, concrete subjects that define what the piece is actually about. Examples:

- Sport type (MMA, boxing, wrestling)
- Legal or regulatory themes (contracts, commissions, suspensions)
- Financial themes (purses, PPV, sponsorship deals)
- Fighter identity (without using their face or likeness)
- Event or venue context

These anchors are the only permitted subjects for the image. Do not generate imagery that is thematically adjacent but not directly tied to the anchor.

### Step 2 — Cross-Reference the Visual Bible

Open and re-read `ROLES/IMAGE_STYLE_GUIDE.md` before writing every prompt. Verify the planned image satisfies:

- The Contextual Lock rule (subject matches the article)
- The Aesthetic Standard (photojournalistic realism)
- The Lighting rules (high contrast, cinematic)
- The Color Palette (muted, desaturated, no vibrant AI colors)
- The Hard No List (no faces, no logos, no cartoons, no 3D renders)
- The Pre-Generation Checklist (all six boxes)

Do not proceed to Step 3 until the prompt passes this check.

### Step 3 — Generate Using flux_gen.py or nano_banana_gen.py

Two image generation backends are available. Both save output to `assets/newsletter_images/` with a timestamped filename automatically.

**Option A — FLUX via OpenRouter (default)**

```bash
python flux_gen.py "<your prompt here>"
```

Requires `OPENROUTER_API_KEY` in the environment.

**Option B — Nano Banana 2 (Gemini 3.1 Flash Image Preview)**

```bash
python nano_banana_gen.py "<your prompt here>"
# Optional flags:
#   --aspect-ratio 16:9   (default: 1:1)
#   --resolution 2K       (default: 1K; choices: 512, 1K, 2K, 4K)
#   --image-only          suppress accompanying text output
```

Requires `GEMINI_API_KEY` in the environment. Install the dependency once with `pip install google-genai pillow`. Output filenames are prefixed with `nb2_` to distinguish them from FLUX outputs.

### Step 4 — Mandatory Prompt Suffix

**Always** append the following string to the end of every prompt sent to `flux_gen.py`, verbatim:

> `Editorial sports photography style, gritty, high contrast`

No exceptions. This suffix anchors every generation to the correct aesthetic baseline regardless of the specific subject matter.

---

## Notes

- The Visual Bible (`ROLES/IMAGE_STYLE_GUIDE.md`) is the authoritative reference for all image decisions. When in doubt, defer to it.
- Never generate an image speculatively. Always tie generation to a specific article or section being published.
- Images land in `assets/newsletter_images/`. Review the output visually before including it in any issue.
