"""
The Fight Docket — Weekly Instagram Content Generator
Run this each week to produce 4 ready-to-post graphics.
Edit the WEEKLY_CONTENT block below with each issue's details.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ig_templates import newsletter_preview, fight_announcement, fight_result, quote_card

# ══════════════════════════════════════════════════════════════
# ✏️  EDIT THIS SECTION EACH WEEK
# ══════════════════════════════════════════════════════════════

WEEK = {
    "date":    "APRIL 20, 2026",
    "issue":   "apr20_2026",

    # 1. Newsletter preview — 3 top stories from the issue
    "preview_stories": [
        "Conor McGregor deal 'looking good' — Dana White signals optimism on contract talks",
        "Khamzat Chimaev signs with Real American Freestyle 3 weeks before UFC 328 title fight",
        "Le v. Zuffa settlement pays out $237M+ to 984 fighters; second antitrust case looms",
    ],

    # 2. Fight announcement (biggest upcoming fight from the issue)
    "announcement": {
        "fighter1":    "Khamzat Chimaev",
        "fighter2":    "Sean Strickland",
        "event":       "UFC 328",
        "date":        "May 9 · Newark, NJ",
        "weight_class":"Middleweight Title Defense",
        "filename":    "chimaev_vs_strickland_announcement.png",
    },

    # 3. Fight result (biggest result from the weekend)
    "result": {
        "winner":    "Mike Malott",
        "loser":     "Gilbert Burns",
        "method":    "KO/TKO",
        "round_num": "R3",
        "time":      "2:15",
        "event":     "UFC Winnipeg",
        "filename":  "malott_burns_result.png",
    },

    # 4. Quote card — pull quote from the newsletter
    "quote": {
        "quote":       "The sport does not always give us the ending we deserve.",
        "attribution": "The Fight Docket, April 20 Issue",
        "context":     "Gilbert Burns retirement",
        "filename":    "burns_legacy_quote.png",
    },
}

# ══════════════════════════════════════════════════════════════
# Generate all 4 graphics
# ══════════════════════════════════════════════════════════════

def run():
    issue = WEEK["issue"]
    print(f"\n🥊 Generating Fight Docket Instagram content — {WEEK['date']}\n")

    # 1. Newsletter preview
    newsletter_preview(
        date_label = WEEK["date"],
        stories    = WEEK["preview_stories"],
        filename   = f"{issue}_newsletter_preview.png",
    )

    # 2. Fight announcement
    a = WEEK["announcement"]
    fight_announcement(
        fighter1    = a["fighter1"],
        fighter2    = a["fighter2"],
        event       = a["event"],
        date        = a["date"],
        weight_class= a["weight_class"],
        filename    = f"{issue}_{a['filename']}",
    )

    # 3. Fight result
    r = WEEK["result"]
    fight_result(
        winner   = r["winner"],
        loser    = r["loser"],
        method   = r["method"],
        round_num= r["round_num"],
        time     = r["time"],
        event    = r["event"],
        filename = f"{issue}_{r['filename']}",
    )

    # 4. Quote card
    q = WEEK["quote"]
    quote_card(
        quote       = q["quote"],
        attribution = q["attribution"],
        context     = q["context"],
        filename    = f"{issue}_{q['filename']}",
    )

    print(f"\n✅ All 4 graphics saved to:\n   The fight Docket/instagram_content/\n")
    print("Post schedule suggestion:")
    print("  📅 Mon — Newsletter Preview (announce the new issue)")
    print("  📅 Tue — Fight Result (weekend recap)")
    print("  📅 Thu — Fight Announcement (hype upcoming card)")
    print("  📅 Sat — Quote Card (engagement post before fight night)")

if __name__ == "__main__":
    run()
