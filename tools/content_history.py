#!/usr/bin/env python3
"""
Content history utility — SQLite-backed cross-issue memory.

Tables:
  stories     — every story covered, by issue date and subject names
  legal_cases — tracked federal cases with last-known docket state

Usage:
  from tools.content_history import ContentHistory
  db = ContentHistory()
  db.was_covered_recently("Canelo", weeks=3)   # → True/False
  db.record_story(issue_date, headline, subjects, story_type)
"""
import sqlite3
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "content_history.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist. Safe to call on every run."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS stories (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_date    TEXT NOT NULL,
                story_type    TEXT NOT NULL,
                headline      TEXT NOT NULL,
                subject_names TEXT NOT NULL,
                summary_hash  TEXT,
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS legal_cases (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number   TEXT NOT NULL UNIQUE,
                case_name     TEXT NOT NULL,
                docket_url    TEXT,
                last_checked  TEXT,
                last_update   TEXT,
                entry_count   INTEGER DEFAULT 0,
                status        TEXT DEFAULT 'active',
                notes         TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_stories_issue ON stories(issue_date);
            CREATE INDEX IF NOT EXISTS idx_stories_subjects ON stories(subject_names);
        """)


def record_story(issue_date: str, headline: str, subjects: list[str], story_type: str = "main"):
    """Log a covered story to prevent repetition across issues."""
    init_db()
    subject_str = json.dumps(sorted(s.lower() for s in subjects))
    summary_hash = hashlib.md5(headline.lower().encode()).hexdigest()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO stories (issue_date, story_type, headline, subject_names, summary_hash) VALUES (?,?,?,?,?)",
            (issue_date, story_type, headline, subject_str, summary_hash),
        )


def was_covered_recently(subject: str, weeks: int = 3) -> bool:
    """Return True if this subject was the focus of a story in the past N weeks."""
    init_db()
    cutoff = (date.today() - timedelta(weeks=weeks)).isoformat()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM stories WHERE issue_date >= ? AND subject_names LIKE ? LIMIT 1",
            (cutoff, f'%"{subject.lower()}"%'),
        ).fetchone()
    return row is not None


def recent_stories(weeks: int = 4) -> list[dict]:
    """Return all stories from the past N weeks for deduplication context."""
    init_db()
    cutoff = (date.today() - timedelta(weeks=weeks)).isoformat()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT issue_date, story_type, headline, subject_names FROM stories WHERE issue_date >= ? ORDER BY issue_date DESC",
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


def upsert_legal_case(case_number: str, case_name: str, docket_url: str = "", entry_count: int = 0, notes: str = ""):
    """Add or update a tracked federal case."""
    init_db()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO legal_cases (case_number, case_name, docket_url, last_checked, entry_count, notes)
            VALUES (?, ?, ?, datetime('now'), ?, ?)
            ON CONFLICT(case_number) DO UPDATE SET
                last_checked = datetime('now'),
                entry_count  = excluded.entry_count,
                notes        = excluded.notes
        """, (case_number, case_name, docket_url, entry_count, notes))


def get_legal_cases(status: str = "active") -> list[dict]:
    """Return all tracked cases with given status."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM legal_cases WHERE status = ? ORDER BY case_name",
            (status,),
        ).fetchall()
    return [dict(r) for r in rows]


def seed_ufc_antitrust_cases():
    """Seed the three known UFC antitrust cases. Safe to call multiple times."""
    cases = [
        ("2:21-cv-01189", "Johnson v. Zuffa", "https://www.courtlistener.com/docket/4366408/"),
        ("2:25-cv-00914", "Cirkunovs v. Zuffa", "https://www.courtlistener.com/docket/?case_name=Cirkunovs+v.+Zuffa"),
        ("2:25-cv-00946", "Davis v. Zuffa", "https://www.courtlistener.com/docket/?case_name=Davis+v.+Zuffa"),
    ]
    for case_num, case_name, url in cases:
        upsert_legal_case(case_num, case_name, url)
    print(f"  Seeded {len(cases)} UFC antitrust cases into content_history.db")


if __name__ == "__main__":
    init_db()
    seed_ufc_antitrust_cases()
    print("  content_history.db initialized.")
    cases = get_legal_cases()
    for c in cases:
        print(f"  Case: {c['case_name']} ({c['case_number']})")
