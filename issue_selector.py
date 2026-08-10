#!/usr/bin/env python3
"""
Canonical "which newsletter issue is current?" logic.

WHY THIS EXISTS
---------------
Every script that needed the latest newsletter used to do:

    sorted(SCRIPT_DIR.glob("newsletter_*.html"), key=lambda f: f.stat().st_mtime)

That is broken in GitHub Actions. Git does not record or restore mtimes, so a
fresh clone stamps every file with its checkout time. "Newest by mtime" then
resolves to an effectively arbitrary file.

Real damage: the Monday Twitter thread posted from newsletter_2026-07-27 on
2026-08-10 and from newsletter_2026-07-20 on 2026-08-03 — two weeks stale both
times, including a since-retracted claim about an ESPN rights negotiation.

Always select by the ISO date embedded in the FILENAME, never by mtime.
"""
import os
import re
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# Canonical issue file only, e.g. newsletter_2026-08-10.html.
# Excludes derived variants such as newsletter_2026-08-10_clean.html.
ISSUE_RE = re.compile(r"^newsletter_(\d{4}-\d{2}-\d{2})\.html$")

# Anything older than this means the generator failed upstream and we would be
# publishing stale news. Callers that post publicly should enforce it.
MAX_ISSUE_AGE_DAYS = 3


def find_issues(directory: Path = None):
    """Return [(issue_date, path), ...] for canonical issues, newest first."""
    directory = directory or SCRIPT_DIR
    found = []
    for p in directory.glob("newsletter_*.html"):
        m = ISSUE_RE.match(p.name)
        if not m:
            continue
        try:
            issue_date = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        found.append((issue_date, p))
    return sorted(found, key=lambda t: t[0], reverse=True)


def latest_issue(directory: Path = None, max_age_days: int = None,
                 allow_stale_env: str = "ALLOW_STALE_ISSUE"):
    """Newest issue as (issue_date, path).

    Raises SystemExit if none exist, or if the newest is older than
    max_age_days. Set the named env var to "1" to override the age check.
    Pass max_age_days=None to skip the check entirely (local tooling).
    """
    issues = find_issues(directory)
    if not issues:
        raise SystemExit(
            "No newsletter_YYYY-MM-DD.html found. Run newsletter_generator.py first."
        )

    issue_date, path = issues[0]
    if max_age_days is not None:
        age = (date.today() - issue_date).days
        if age > max_age_days and os.getenv(allow_stale_env) != "1":
            raise SystemExit(
                f"Refusing to proceed: newest issue is {path.name} ({age} days old, "
                f"limit {max_age_days}). The newsletter pipeline likely failed upstream. "
                f"Fix that first, or set {allow_stale_env}=1 to override."
            )
    return issue_date, path
