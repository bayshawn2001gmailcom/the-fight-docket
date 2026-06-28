#!/usr/bin/env python3
"""
The Fight Docket — Beehiiv Quick Post Helper

Opens the Beehiiv new-post editor in your real Chrome browser (where you're
already logged in) and copies the newsletter HTML to your clipboard so you
can paste it in one step.

Run:
    python tools/beehiiv_open_editor.py

Steps after running:
    1. Chrome opens to app.beehiiv.com/posts/new
    2. Fill in the subject line (shown in terminal)
    3. Click the HTML/Source toggle button in the editor
    4. Select all (Ctrl+A) and paste (Ctrl+V)
    5. Save as draft or schedule
"""
import json, sys, subprocess, time
from pathlib import Path

ROOT    = Path(__file__).parent.parent
TMP_DIR = ROOT / ".tmp"


def load_newsletter() -> tuple[str, str]:
    files = sorted(ROOT.glob("newsletter_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit("No newsletter_*.html found. Run tools/html_renderer.py first.")
    latest = files[0]
    return latest.name, latest.read_text(encoding="utf-8")


def load_ig_data() -> dict:
    ig_files = sorted(TMP_DIR.glob("weekly_ig_data_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if ig_files:
        return json.loads(ig_files[0].read_text(encoding="utf-8"))
    return {}


def build_subject(ig_data: dict, newsletter_name: str) -> str:
    stories = ig_data.get("preview_stories", [])
    if stories:
        return f"The Fight Docket | {stories[0][:60]}"
    date_str = newsletter_name.replace("newsletter_", "").replace(".html", "")
    return f"The Fight Docket | {date_str}"


def copy_to_clipboard(text: str):
    """Copy text to Windows clipboard via PowerShell, preserving UTF-8 characters."""
    import tempfile, os
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".html", delete=False) as f:
            f.write(text)
            temp_path = f.name
        ps_cmd = (
            f"$text = [System.IO.File]::ReadAllText('{temp_path}', [System.Text.Encoding]::UTF8);"
            f" Set-Clipboard -Value $text"
        )
        proc = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
        os.unlink(temp_path)
        return proc.returncode == 0
    except Exception:
        return False


def open_in_chrome(url: str):
    """Open URL in default browser (Chrome)."""
    import webbrowser
    webbrowser.open(url)


def main():
    print("=" * 60)
    print("  The Fight Docket -- Beehiiv Quick Post")
    print("=" * 60)

    name, html = load_newsletter()
    ig_data    = load_ig_data()
    subject    = build_subject(ig_data, name)

    print(f"\n  Newsletter : {name}")
    print(f"  Subject    : {subject}")
    print()

    copied = copy_to_clipboard(html)
    if copied:
        print("  HTML copied to clipboard.")
    else:
        print("  Could not copy to clipboard automatically.")
        print(f"  HTML is at: {ROOT / name}")

    print()
    print("  Opening Beehiiv editor in Chrome...")
    open_in_chrome("https://app.beehiiv.com/posts/new")
    time.sleep(1)

    print()
    print("=" * 60)
    print("  NEXT STEPS:")
    print("=" * 60)
    print(f"  1. Subject line: {subject}")
    print()
    print("  2. Click the HTML/Source toggle in the editor toolbar")
    print("     (looks like '</>' or 'HTML' button)")
    print()
    print("  3. Select all (Ctrl+A) then paste (Ctrl+V)")
    if not copied:
        print(f"     HTML file: {ROOT / name}")
    print()
    print("  4. Save as draft -> review in Beehiiv preview")
    print("  5. Schedule for Monday noon EDT when ready")
    print("=" * 60)


if __name__ == "__main__":
    main()
