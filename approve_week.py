#!/usr/bin/env python3
"""
approve_week.py — sign off this week's Instagram/Facebook cards.

The Tue/Thu/Fri crons are a release schedule, not a publisher: they only post
cards a human has actually looked at. This is the moment that happens.

    python approve_week.py            # show the cards, then approve
    python approve_week.py --status   # just report, change nothing
    python approve_week.py --revoke   # un-approve (stops the remaining drip)
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
MANIFEST = SCRIPT_DIR / "instagram_content" / "current_week.json"

CARDS = [("preview", "Mon"), ("result", "Tue"), ("announcement", "Thu"), ("quote", "Fri")]


def load():
    if not MANIFEST.exists():
        raise SystemExit(f"No manifest at {MANIFEST}. Run ig_content_generator.py first.")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def report(m):
    print(f"  Issue      : {m.get('issue')} ({m.get('issue_date')})")
    state = m.get("approved")
    label = "APPROVED" if state is True else "NOT APPROVED"
    print(f"  Status     : {label}")
    if m.get("approved_at"):
        print(f"  Approved at: {m['approved_at']}")
    print("  Cards:")
    missing = []
    for key, day in CARDS:
        name = m.get(key) or ""
        path = SCRIPT_DIR / "instagram_content" / name
        ok = bool(name) and path.exists()
        if not ok:
            missing.append(key)
        print(f"    {day}  {key:<13} {name or '(none)'}  {'' if ok else '  <-- MISSING'}")
    return missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true", help="report only")
    ap.add_argument("--revoke", action="store_true", help="un-approve this week")
    args = ap.parse_args()

    m = load()
    print("\n  Fight Docket — weekly card approval")
    print("=" * 55)
    missing = report(m)

    if args.status:
        return

    if args.revoke:
        m["approved"] = False
        m.pop("approved_at", None)
        MANIFEST.write_text(json.dumps(m, indent=2), encoding="utf-8")
        print("\n  Revoked. The remaining drip posts will refuse until re-approved.")
        return

    if missing:
        raise SystemExit(
            f"\n  Refusing to approve: missing card file(s) for {', '.join(missing)}.\n"
            "  Regenerate with ig_content_generator.py first."
        )

    m["approved"] = True
    m["approved_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    MANIFEST.write_text(json.dumps(m, indent=2), encoding="utf-8")
    print(f"\n  Approved. Tue/Thu/Fri drip will post these cards.")
    print("  Commit and push so the crons see it.")


if __name__ == "__main__":
    main()
