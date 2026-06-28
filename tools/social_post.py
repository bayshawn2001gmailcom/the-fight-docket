#!/usr/bin/env python3
"""
The Fight Docket — Unified Social Poster (WAT Framework)
Single entry point to post IG cards to Instagram and/or Facebook.

Usage:
  python tools/social_post.py --card=preview --platform=all
  python tools/social_post.py --card=result --platform=instagram
  python tools/social_post.py --card=announcement --platform=facebook
  python tools/social_post.py --card=quote --platform=all --dry-run

Posting schedule:
  Monday    → preview       (run manually after newsletter pipeline)
  Tuesday   → result        (Task Scheduler: 9am EDT)
  Thursday  → announcement  (Task Scheduler: 9am EDT)
  Saturday  → quote         (Task Scheduler: 10am EDT)

Run --dry-run first when testing a new card type or after credential changes.
"""
import sys, io, subprocess, argparse
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent

PLATFORMS = ["instagram", "facebook", "all"]
CARDS     = ["preview", "result", "announcement", "quote"]


def run_script(script: str, card: str, dry_run: bool) -> bool:
    """Run a platform posting script. Returns True on success."""
    cmd = [sys.executable, str(ROOT / "tools" / script), f"--card={card}"]
    if dry_run:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Post a Fight Docket card to social platforms")
    parser.add_argument("--card", required=True, choices=CARDS,
                        help="preview|result|announcement|quote")
    parser.add_argument("--platform", required=True, choices=PLATFORMS,
                        help="instagram|facebook|all")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be posted without posting")
    args = parser.parse_args()

    print("=" * 55)
    print("  The Fight Docket — Social Poster")
    print(f"  Card: {args.card}  |  Platform: {args.platform}  |  Date: {date.today().isoformat()}")
    if args.dry_run:
        print("  MODE: DRY RUN")
    print("=" * 55)

    results = {}

    if args.platform in ("instagram", "all"):
        print("\n>>> Instagram")
        results["instagram"] = run_script("instagram_post.py", args.card, args.dry_run)

    if args.platform in ("facebook", "all"):
        print("\n>>> Facebook")
        results["facebook"] = run_script("facebook_post.py", args.card, args.dry_run)

    print("\n" + "=" * 55)
    print("  SUMMARY")
    all_ok = True
    for platform, ok in results.items():
        status = "✅ OK" if ok else "❌ FAILED"
        print(f"  {platform.capitalize():12} {status}")
        if not ok:
            all_ok = False
    print("=" * 55)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
