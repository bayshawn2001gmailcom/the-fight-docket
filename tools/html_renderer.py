#!/usr/bin/env python3
"""
The Fight Docket — HTML Renderer (WAT Framework)
Reads newsletter_draft_YYYY-MM-DD.json + asset_urls_YYYY-MM-DD.json,
renders Jinja2 template → newsletter_YYYY-MM-DD.html

Run: python tools/html_renderer.py
     python tools/html_renderer.py 2026-05-12   (specific date)
"""
import json, sys
from datetime import date
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    raise SystemExit("Missing: pip install jinja2")

ROOT         = Path(__file__).parent.parent
TMP_DIR      = ROOT / ".tmp"
TEMPLATE_DIR = Path(__file__).parent / "templates"


def find_latest(pattern: str, directory: Path) -> Path | None:
    files = sorted(directory.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load_draft(date_iso: str | None = None) -> dict:
    if date_iso:
        path = TMP_DIR / f"newsletter_draft_{date_iso}.json"
        if not path.exists():
            raise SystemExit(f"Draft not found: {path}")
    else:
        path = find_latest("newsletter_draft_*.json", TMP_DIR)
        if not path:
            raise SystemExit("No newsletter_draft_*.json found in .tmp/. Run tools/newsletter_draft.py first.")
    print(f"  Draft    : {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_asset_urls(date_iso: str | None = None) -> dict:
    """Load ImgBB URLs. Returns empty dict if not generated yet — images become optional."""
    if date_iso:
        path = TMP_DIR / f"asset_urls_{date_iso}.json"
    else:
        path = find_latest("asset_urls_*.json", TMP_DIR)

    if path and path.exists():
        print(f"  Assets   : {path.name}")
        return json.loads(path.read_text(encoding="utf-8"))

    print("  Assets   : none found — newsletter will render without images")
    return {}


def render(draft: dict, asset_urls: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,  # HTML content from Gemini is trusted
    )
    template = env.get_template("newsletter.html.j2")

    # Map section keys to image URL variables
    section_image_map = {
        "intro":             "intro_image_url",
        "main_story":        "main_story_image_url",
        "legal":             "legal_image_url",
        "rumor":             "rumor_image_url",
        "fight_previews":    "fight_previews_image_url",
        "business_intel":    "business_intel_image_url",
        "fighter_spotlight": "fighter_spotlight_image_url",
    }

    image_vars = {v: asset_urls.get(k, "") for k, v in section_image_map.items()}

    context = {
        "issue_date_display":     draft.get("issue_date_display", date.today().strftime("%B %d, %Y").upper()),
        "editors_note_html":      draft.get("editors_note_html", ""),
        "main_story_headline":    draft.get("main_story_headline", "This Week in Combat Sports"),
        "main_story_html":        draft.get("main_story_html", ""),
        "legal_tracker_headline": draft.get("legal_tracker_headline", "Court Watch"),
        "legal_tracker_html":     draft.get("legal_tracker_html", ""),
        "rumor_mill_html":        draft.get("rumor_mill_html", ""),
        "fight_previews_headline":draft.get("fight_previews_headline", "What's on Deck"),
        "fight_previews_html":    draft.get("fight_previews_html", ""),
        "business_intel_headline":draft.get("business_intel_headline", "Business Intel"),
        "business_intel_html":    draft.get("business_intel_html", ""),
        "fighter_spotlight_name": draft.get("fighter_spotlight_name", "Fighter Spotlight"),
        "fighter_spotlight_html": draft.get("fighter_spotlight_html", ""),
        **image_vars,
    }

    return template.render(**context)


def main():
    date_iso = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print("  The Fight Docket — HTML Renderer")
    print("=" * 60)

    draft     = load_draft(date_iso)
    asset_urls = load_asset_urls(date_iso or draft.get("issue_date"))

    print("\n  Rendering template...")
    html = render(draft, asset_urls)

    issue_date = draft.get("issue_date", date.today().isoformat())
    out_path   = ROOT / f"newsletter_{issue_date}.html"
    out_path.write_text(html, encoding="utf-8")

    print(f"\n  Output   : {out_path.name} ({len(html):,} chars)")
    print("\n  DONE — Next step: run tools/beehiiv_post.py")


if __name__ == "__main__":
    main()
