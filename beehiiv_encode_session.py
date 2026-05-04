#!/usr/bin/env python3
"""
After running beehiiv_save_session.py, run this to encode the session
for GitHub Actions and add it as a secret automatically.

Run: python beehiiv_encode_session.py
"""
import base64, subprocess
from pathlib import Path

SESSION_FILE = Path(__file__).parent / "beehiiv_session.json"

if not SESSION_FILE.exists():
    raise SystemExit("No session file found. Run beehiiv_save_session.py first.")

encoded = base64.b64encode(SESSION_FILE.read_bytes()).decode()
print(f"Session encoded ({len(encoded)} chars)")

# Add to GitHub secrets automatically
result = subprocess.run(
    ["gh", "secret", "set", "BEEHIIV_SESSION",
     "--body", encoded,
     "--repo", "bayshawn2001gmailcom/the-fight-docket"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("BEEHIIV_SESSION secret set in GitHub Actions.")
else:
    print("gh secret set failed:", result.stderr)
    print("Set it manually with:")
    print(f'  gh secret set BEEHIIV_SESSION --body "{encoded[:40]}..." --repo ...')
