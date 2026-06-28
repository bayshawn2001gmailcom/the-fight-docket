> ⚠️ **DEPRECATED — 2026-06-28**
> This agent has been retired. API keys are now stored in GitHub Secrets
> (`the-fight-docket` repo → Settings → Secrets → Actions).
> Use Claude Code + GitHub Actions instead of this launch sequence.
> The folder is kept for historical reference only — do not run these steps.

---

# Fight Night Watchdog — Launch Sequence (ARCHIVED)

Each step reads IDS.env first and skips if the object already exists.
Re-run from any failed step — no duplicates created.

```bash
cd "C:\Users\baysh\Fight Newsletter\my-agent"
set -a; source .env; set +a
BASE=https://api.anthropic.com/v1
H=(-H "x-api-key: $ANTHROPIC_API_KEY" \
   -H "anthropic-version: 2023-06-01" \
   -H "anthropic-beta: managed-agents-2026-04-01" \
   -H "content-type: application/json")
```

---

## Step 1 — Pick the newest Opus-class model

```bash
curl -sS "$BASE/models" "${H[@]:0:4}" | python3 -c "
import json,sys
d=json.JSONDecoder(strict=False).decode(sys.stdin.read())
models=[m['id'] for m in d['data'] if 'opus' in m['id'].lower()]
print('Opus models:', models[:5])
"
# Update agent.json model.id to the newest one listed, then continue.
```

---

## Step 2 — Create environment (skip if ENV_ID is set)

```bash
set -a; source IDS.env; set +a
if [ -z "$ENV_ID" ]; then
  curl -sS --fail-with-body "$BASE/environments" "${H[@]}" -d @environment.json \
    -o /tmp/env.json -w '%{http_code}\n'
  ENV_ID=$(python3 -c "import json; print(json.JSONDecoder(strict=False).decode(open('/tmp/env.json').read())['id'])")
  echo "ENV_ID=$ENV_ID" >> IDS.env
  echo "✅ 📦 Environment: $ENV_ID"
else
  echo "  Skipping — ENV_ID already set: $ENV_ID"
fi
```

---

## Step 3 — Create agent (skip if AGENT_ID is set)

```bash
set -a; source IDS.env; set +a
if [ -z "$AGENT_ID" ]; then
  curl -sS --fail-with-body "$BASE/agents" "${H[@]}" -d @agent.json \
    -o /tmp/agent.json -w '%{http_code}\n'
  AGENT_ID=$(python3 -c "import json; d=json.JSONDecoder(strict=False).decode(open('/tmp/agent.json').read()); print(d['id'])")
  AGENT_VERSION=$(python3 -c "import json; d=json.JSONDecoder(strict=False).decode(open('/tmp/agent.json').read()); print(d['version'])")
  echo "AGENT_ID=$AGENT_ID" >> IDS.env
  echo "AGENT_VERSION=$AGENT_VERSION" >> IDS.env
  echo "✅ 🤖 Agent: $AGENT_ID (v$AGENT_VERSION)"
else
  echo "  Skipping — AGENT_ID already set: $AGENT_ID"
fi
```

---

## Step 4 — Create memory store (skip if MEMORY_STORE_ID is set)

```bash
set -a; source IDS.env; set +a
if [ -z "$MEMORY_STORE_ID" ]; then
  curl -sS --fail-with-body "$BASE/memory_stores" "${H[@]}" \
    -d '{"name":"fight-results-memory","description":"Tracks posted fight results across sessions to prevent duplicate social posts. Format per line: ISO datetime | event | winner def. loser | method Rround time"}' \
    -o /tmp/mem.json -w '%{http_code}\n'
  MEMORY_STORE_ID=$(python3 -c "import json; print(json.JSONDecoder(strict=False).decode(open('/tmp/mem.json').read())['id'])")
  echo "MEMORY_STORE_ID=$MEMORY_STORE_ID" >> IDS.env
  echo "✅ 🧠 Memory store: $MEMORY_STORE_ID"
else
  echo "  Skipping — MEMORY_STORE_ID already set: $MEMORY_STORE_ID"
fi
```

---

## Step 5 — Create vault and load credentials

You need these values from your .env files. Open them in a separate terminal:
```
C:\Users\baysh\Fight Newsletter\.env   → GEMINI_API_KEY, INSTAGRAM_ACCOUNT_ID, INSTAGRAM_PAGE_TOKEN,
                                          FACEBOOK_PAGE_ID, FACEBOOK_PAGE_TOKEN, IMGBB_API_KEY
the-fight-docket repo secrets          → TWITTER_API_KEY, TWITTER_API_SECRET,
                                          TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
```

```bash
set -a; source IDS.env; set +a
if [ -z "$VAULT_ID" ]; then
  VAULT_ID=$(curl -sS --fail-with-body "$BASE/vaults" "${H[@]}" \
    -d '{"display_name":"fight-docket-social-vault"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
  echo "VAULT_ID=$VAULT_ID" >> IDS.env
  echo "✅ 🔐 Vault: $VAULT_ID"
fi

# Load each credential — replace VALUE with actual values from your .env files
set -a; source "C:/Users/baysh/Fight Newsletter/.env"; set +a

for SECRET_NAME in GEMINI_API_KEY INSTAGRAM_ACCOUNT_ID INSTAGRAM_PAGE_TOKEN FACEBOOK_PAGE_ID FACEBOOK_PAGE_TOKEN IMGBB_API_KEY; do
  SECRET_VALUE="${!SECRET_NAME}"
  if [ -n "$SECRET_VALUE" ]; then
    curl -sS --fail-with-body "$BASE/vaults/$VAULT_ID/credentials" "${H[@]}" \
      -d "{\"display_name\":\"$SECRET_NAME\",\"auth\":{\"type\":\"environment_variable\",\"secret_name\":\"$SECRET_NAME\",\"secret_value\":\"$SECRET_VALUE\",\"networking\":{\"type\":\"unrestricted\"}}}" \
      -o /tmp/cred.json -w '%{http_code}\n'
    echo "  ✅ Credential: $SECRET_NAME"
  else
    echo "  ⚠️  Missing: $SECRET_NAME — check your .env"
  fi
done

# Twitter credentials — load manually (from the-fight-docket project or GitHub secrets)
# Replace each XXX with the actual value
for SECRET_NAME in TWITTER_API_KEY TWITTER_API_SECRET TWITTER_ACCESS_TOKEN TWITTER_ACCESS_TOKEN_SECRET; do
  echo "  ⚠️  Twitter: $SECRET_NAME — add manually (see the-fight-docket/.env or GitHub secrets)"
done
```

---

## Step 6 — First session + kickoff (the test run)

```bash
set -a; source IDS.env; set +a

# Create session
curl -sS --fail-with-body "$BASE/sessions" "${H[@]}" \
  -d "{\"agent\":\"$AGENT_ID\",\"environment_id\":\"$ENV_ID\",\"vault_ids\":[\"$VAULT_ID\"],\"title\":\"fight-night-watchdog-test\",\"resources\":[{\"type\":\"memory_store\",\"memory_store_id\":\"$MEMORY_STORE_ID\",\"access\":\"read_write\",\"instructions\":\"Track every fight result posted. Read before posting to avoid duplicates. Append after each post.\"}]}" \
  -o /tmp/session.json -w '%{http_code}\n'

SESSION_ID=$(python3 -c "import json; print(json.JSONDecoder(strict=False).decode(open('/tmp/session.json').read())['id'])")
echo "SESSION_ID=$SESSION_ID"
echo "SESSION_ID=$SESSION_ID" >> IDS.env
echo "✅ ▶️ Session: $SESSION_ID"

# Kickoff with outcome
EVT=$(python3 -c "
import json
task=open('first_prompt.txt').read()
rubric=open('outcome.md').read()
print(json.dumps({'type':'user.define_outcome','description':task,'rubric':{'type':'text','content':rubric},'max_iterations':5}))
")
curl -sS --fail-with-body "$BASE/sessions/$SESSION_ID/events" "${H[@]}" \
  -d "{\"events\":[$EVT]}" -w '%{http_code}\n'

echo ""
echo "🚀 Agent is running. Console link:"
echo "   https://platform.claude.com/workspaces/default/sessions/$SESSION_ID"
echo "   (If you don't see it, switch workspace — Settings → API Keys shows which workspace your key belongs to)"
```

---

## Step 7 — Watch the run

```bash
# Poll status (run this in a loop or watch manually)
curl -sS "$BASE/sessions/$SESSION_ID" "${H[@]}" -o /tmp/sess.json
python3 -c "
import json
d=json.JSONDecoder(strict=False).decode(open('/tmp/sess.json').read())
print('Status:', d['status'])
evals=[e.get('result','?') for e in d.get('outcome_evaluations',[])]
if evals: print('Verdict:', evals)
"

# Fetch output file when done
curl -sS "$BASE/files?scope_id=$SESSION_ID" "${H[@]}" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for f in d.get('data',[]): print(f['id'], f['filename'])
"
# Then: curl -sS "$BASE/files/FILE_ID/content" "${H[@]}"
```

---

## Step 8 — Create scheduled deployment (after first run passes)

```bash
set -a; source IDS.env; set +a

EVT=$(python3 -c "
import json
task=open('first_prompt.txt').read()
# Remove the test scenario line from the deployment version
task_deploy=task.replace('\n\nTest scenario for this first run: Justin Gaethje def. Ilia Topuria | TKO R4 4:51 | UFC Freedom 250. Use this as eval case 1 to verify the full pipeline works end-to-end.','')
rubric=open('outcome.md').read()
print(json.dumps({'type':'user.define_outcome','description':task_deploy,'rubric':{'type':'text','content':rubric},'max_iterations':5}))
")

curl -sS --fail-with-body "$BASE/deployments?beta=true" "${H[@]}" \
  -d "{
    \"name\": \"fight-night-watchdog\",
    \"agent\": \"$AGENT_ID\",
    \"environment_id\": \"$ENV_ID\",
    \"vault_ids\": [\"$VAULT_ID\"],
    \"resources\": [{\"type\":\"memory_store\",\"memory_store_id\":\"$MEMORY_STORE_ID\",\"access\":\"read_write\",\"instructions\":\"Track every fight result posted. Read before posting to avoid duplicates. Append after each post.\"}],
    \"schedule\": {\"type\":\"cron\",\"expression\":\"*/10 * * * 5,6\",\"timezone\":\"UTC\"},
    \"initial_events\": [$EVT]
  }" \
  -o /tmp/deploy.json -w '%{http_code}\n'

DEPLOYMENT_ID=$(python3 -c "import json; print(json.JSONDecoder(strict=False).decode(open('/tmp/deploy.json').read())['id'])")
echo "DEPLOYMENT_ID=$DEPLOYMENT_ID" >> IDS.env
echo "✅ 🗓️ Deployment: $DEPLOYMENT_ID"

# Show upcoming runs
python3 -c "
import json
d=json.JSONDecoder(strict=False).decode(open('/tmp/deploy.json').read())
runs=d.get('schedule',{}).get('upcoming_runs_at',[])
print('Upcoming runs (UTC):', runs[:5])
"

# Manual test fire
echo "Manual test fire:"
curl -sS -X POST -d '{}' "$BASE/deployments/$DEPLOYMENT_ID/run?beta=true" "${H[@]}" \
  -o /tmp/manual_run.json -w '%{http_code}\n'
python3 -c "import json; d=json.JSONDecoder(strict=False).decode(open('/tmp/manual_run.json').read()); print('Session started:', d.get('session_id','?'))"
```
