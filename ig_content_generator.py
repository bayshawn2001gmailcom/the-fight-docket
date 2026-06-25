#!/usr/bin/env python3
"""
The Fight Docket — Auto Instagram Content Generator
Reads prompts/weekly_ig_data.json → generates all 4 IG graphics + captions file
Run: python ig_content_generator.py
"""
import sys, os, json
from pathlib import Path
from datetime import date

SCRIPT_DIR    = Path(__file__).parent
IG_DATA_FILE  = SCRIPT_DIR / "prompts" / "weekly_ig_data.json"
IG_CONTENT_DIR = SCRIPT_DIR / "instagram_content"
IG_CONTENT_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(SCRIPT_DIR))


def main():
    if not IG_DATA_FILE.exists():
        raise SystemExit(f"ERROR: {IG_DATA_FILE} not found. Run newsletter_generator.py first.")

    with open(IG_DATA_FILE, encoding="utf-8") as f:
        week = json.load(f)

    issue = week.get("issue", date.today().strftime("%b%d_%Y").lower())
    print(f"\n  Fight Docket — IG Content Generator")
    print(f"  Issue: {week.get('date', issue)}\n")

    from ig_templates import newsletter_preview, fight_announcement, fight_result, quote_card

    # 1. Newsletter Preview
    print("[1/4] Newsletter preview card...")
    newsletter_preview(
        date_label=week["date"],
        stories=week["preview_stories"],
        filename=f"{issue}_newsletter_preview.png",
    )

    # 2. Fight Announcement
    a = week.get("announcement", {})
    if a:
        print("[2/4] Fight announcement card...")
        fight_announcement(
            fighter1=a["fighter1"],
            fighter2=a["fighter2"],
            event=a["event"],
            date=a["date"],
            weight_class=a.get("weight_class", ""),
            filename=f"{issue}_{a.get('filename', 'announcement.png')}",
        )
    else:
        print("[2/4] Skipped (no announcement data)")

    # 3. Fight Result
    r = week.get("result", {})
    if r:
        print("[3/4] Fight result card...")
        fight_result(
            winner=r["winner"],
            loser=r["loser"],
            method=r["method"],
            round_num=r["round_num"],
            time=r["time"],
            event=r.get("event", ""),
            filename=f"{issue}_{r.get('filename', 'result.png')}",
        )
    else:
        print("[3/4] Skipped (no result data)")

    # 4. Quote Card
    q = week.get("quote", {})
    if q:
        print("[4/4] Quote card...")
        quote_card(
            quote=q["quote"],
            attribution=q["attribution"],
            context=q.get("context", ""),
            filename=f"{issue}_{q.get('filename', 'quote.png')}",
        )
    else:
        print("[4/4] Skipped (no quote data)")

    # Write captions file
    f1 = a.get("fighter1", "") if a else ""
    f2 = a.get("fighter2", "") if a else ""
    event_ann = a.get("event", "") if a else ""
    date_ann  = a.get("date", "") if a else ""

    winner = r.get("winner", "") if r else ""
    loser  = r.get("loser", "") if r else ""
    method = r.get("method", "") if r else ""
    rnd    = r.get("round_num", "") if r else ""
    t      = r.get("time", "") if r else ""

    stories_text = "\n".join(f"  → {s}" for s in week.get("preview_stories", []))
    quote_text   = q.get("quote", "") if q else ""
    quote_attr   = q.get("attribution", "") if q else ""

    captions = f"""The Fight Docket — {week.get('date', '')}
Generated: {date.today().isoformat()}
=========================================

--- MONDAY: Newsletter Preview ---
\U0001f4f0 NEW ISSUE — The Fight Docket is out.

{stories_text}

Subscribe free → www.thefightdocket.com
#FightDocket #MMA #Boxing #CombatSports #UFC

--- TUESDAY: Fight Result ---
\U0001f94a RESULT

{winner.upper()} def. {loser.upper()}
{method} · {rnd} · {t}

Full breakdown in this week's newsletter → www.thefightdocket.com
#MMA #UFC #Boxing #FightResults #CombatSports

--- THURSDAY: Fight Announcement ---
\U0001f94a IT'S OFFICIAL

{f1} vs. {f2}
{event_ann} · {date_ann}

Full preview in The Fight Docket newsletter → www.thefightdocket.com
#UFC #MMA #FightAnnouncement #{event_ann.replace(' ', '')} #{f1.split()[-1]} #{f2.split()[-1]}

--- SATURDAY: Quote Card ---
"{quote_text}"
— {quote_attr}

Combat sports business intelligence, weekly and free.
Subscribe → www.thefightdocket.com
#FightDocket #MMA #Boxing #CombatSports
"""

    captions_file = IG_CONTENT_DIR / f"{issue}_captions.txt"
    captions_file.write_text(captions, encoding="utf-8")
    print(f"\n  Captions saved: {captions_file.name}")

    # Write manifest so post_instagram_weekly.py can find the right files
    # (GitHub Actions checkouts give all files identical timestamps, making mtime sort unreliable)
    ann_filename = f"{issue}_{a.get('filename', 'announcement.png')}" if a else ""
    res_filename = f"{issue}_{r.get('filename', 'result.png')}" if r else ""
    qot_filename = f"{issue}_{q.get('filename', 'quote.png')}" if q else ""
    manifest = {
        "issue": issue,
        "captions": captions_file.name,
        "preview":      f"{issue}_newsletter_preview.png",
        "announcement": ann_filename,
        "result":       res_filename,
        "quote":        qot_filename,
    }
    manifest_file = IG_CONTENT_DIR / "current_week.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"  Manifest saved: current_week.json  (issue: {issue})")

    print(f"\n  All 4 graphics + captions ready in instagram_content/")
    print(f"\n  Posting schedule:")
    print("    Mon  — Newsletter Preview")
    print("    Tue  — Fight Result")
    print("    Thu  — Fight Announcement")
    print("    Sat  — Quote Card")


if __name__ == "__main__":
    main()
