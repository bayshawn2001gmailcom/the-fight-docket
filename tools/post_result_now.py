#!/usr/bin/env python3
"""
The Fight Docket — Instant Fight Result Poster (WAT Framework)
Run this RIGHT AFTER a fight ends to generate and post the result card immediately.

Usage:
  python tools/post_result_now.py --winner="Gaethje" --loser="Topuria" --method="TKO" --round=4 --time="4:51" --event="UFC Freedom 250"
  python tools/post_result_now.py --winner="Usyk" --loser="Fury" --method="UD" --round=12 --time="3:00" --event="Usyk vs. Fury 2" --dry-run

Arguments:
  --winner    Winner's last name (or full name)
  --loser     Loser's last name (or full name)
  --method    KO | TKO | UD | SD | MD | RTD | DQ | NC
  --round     Round number (e.g. 3)
  --time      Time in round (e.g. 2:47)
  --event     Event name (e.g. UFC 310 | Canelo vs. Munguia)
  --platform  instagram | facebook | all  (default: all)
  --dry-run   Generate card without posting
"""
import sys, io, os, argparse, subprocess
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)

# Import fight_result from ig_graphics
sys.path.insert(0, str(ROOT / "tools"))
from ig_graphics import fight_result


def main():
    parser = argparse.ArgumentParser(description="Generate and post a fight result card immediately")
    parser.add_argument("--winner",   required=True, help="Winner name")
    parser.add_argument("--loser",    required=True, help="Loser name")
    parser.add_argument("--method",   required=True, help="KO|TKO|UD|SD|MD|RTD|DQ")
    parser.add_argument("--round",    required=True, dest="round_num", help="Round number")
    parser.add_argument("--time",     required=True, help="Time in round (e.g. 2:47)")
    parser.add_argument("--event",    required=True, help="Event name")
    parser.add_argument("--platform", default="all", choices=["instagram", "facebook", "all"])
    parser.add_argument("--dry-run",  action="store_true")
    args = parser.parse_args()

    print("=" * 55)
    print("  The Fight Docket — Instant Result Poster")
    print(f"  {args.winner.upper()} def. {args.loser.upper()} — {args.method.upper()} R{args.round_num} {args.time}")
    print(f"  Event: {args.event}")
    if args.dry_run:
        print("  MODE: DRY RUN")
    print("=" * 55)

    print("\n[1/2] Generating result card...")
    slug      = args.winner.lower().replace(" ", "_")
    filename  = f"{date.today().strftime('%b%d_%Y').lower()}_{slug}_result.png"
    card_path = fight_result(
        winner    = args.winner,
        loser     = args.loser,
        method    = args.method,
        round_num = f"R{args.round_num}",
        time      = args.time,
        event     = args.event,
        filename  = filename,
    )
    print(f"  Saved: {filename}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would post: {card_path}")
        print("  Dry run complete — no post made.")
        return

    print("\n[2/2] Posting to social media...")
    cmd = [sys.executable, str(ROOT / "tools" / "social_post.py"),
           "--card=result", f"--platform={args.platform}"]
    result = subprocess.run(cmd, cwd=str(ROOT))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
