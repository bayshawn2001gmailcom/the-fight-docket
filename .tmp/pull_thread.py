#!/usr/bin/env python3
"""Archive then delete one thread from @thefightdocket.

Reads need the app bearer token; OAuth1 user tokens 401 on reads but are the
only thing that can delete. Archive first, always: deletion is irreversible.

Usage: python pull_thread.py <root_tweet_id> [--delete]
Without --delete it only reads and archives.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import tweepy
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path.home() / ".env", override=False)


def _tok(key, *alts):
    for k in (key, *alts):
        v = os.getenv(k)
        if v:
            return v.strip().strip("'\"")
    return ""


BEARER = _tok("TWITTER_BEARER_TOKEN")
API_KEY = _tok("TWITTER_API_KEY")
API_SECRET = _tok("TWITTER_API_SECRET")
ACCESS = _tok("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = _tok("TWITTER_ACCESS_TOKEN_SECRET", "TWITTER_ACCESS_SECRET")

root_id = sys.argv[1]
do_delete = "--delete" in sys.argv

read = tweepy.Client(bearer_token=BEARER)
write = tweepy.Client(
    consumer_key=API_KEY, consumer_secret=API_SECRET,
    access_token=ACCESS, access_token_secret=ACCESS_SECRET,
)

# Identify the account that owns the thread, then walk its recent tweets for
# everything sharing the root's conversation_id.
me = write.get_me()
uid, handle = me.data.id, me.data.username
print(f"  account: @{handle} ({uid})")

collected = {}
root = read.get_tweet(root_id, tweet_fields=["created_at", "conversation_id", "text"])
if root.data:
    collected[str(root.data.id)] = root.data
    conv = str(root.data.conversation_id)
    print(f"  conversation: {conv}")
else:
    raise SystemExit(f"  Root tweet {root_id} not found. It may already be gone.")

paginator = tweepy.Paginator(
    read.get_users_tweets, uid, max_results=100,
    tweet_fields=["created_at", "conversation_id", "text"], limit=3,
)
for page in paginator:
    for t in (page.data or []):
        if str(t.conversation_id) == conv:
            collected[str(t.id)] = t

ordered = sorted(collected.values(), key=lambda t: int(t.id))
print(f"  found {len(ordered)} tweets in the thread")

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
archive = ROOT / ".tmp" / f"deleted_thread_{conv}_{stamp}.json"
archive.write_text(json.dumps(
    [{"id": str(t.id),
      "created_at": str(t.created_at),
      "text": t.text} for t in ordered],
    indent=2, ensure_ascii=False), encoding="utf-8")
print(f"  archived: {archive}")

for i, t in enumerate(ordered, 1):
    print(f"\n--- T{i} ({t.id}) ---\n{t.text}")

if not do_delete:
    print("\n  READ ONLY. Re-run with --delete to remove these.")
    sys.exit(0)

print("\n  Deleting...")
results = []
for i, t in enumerate(ordered, 1):
    try:
        r = write.delete_tweet(t.id)
        ok = bool(r.data and r.data.get("deleted"))
    except Exception as e:
        ok = False
        print(f"    T{i} {t.id}: ERROR {e}")
    results.append((str(t.id), ok))
    if ok:
        print(f"    T{i} {t.id}: deleted")

done = sum(1 for _, ok in results if ok)
print(f"\n  {done}/{len(results)} deleted")
sys.exit(0 if done == len(results) else 1)
