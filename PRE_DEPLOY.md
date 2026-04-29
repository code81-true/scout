# PRE_DEPLOY.md — Scout VPS Deploy Checklist
# Run this before every deploy that touches user-facing code. No exceptions.
# Referenced by CLAUDE.md.

## PRE-DEPLOY CHECKLIST — MANDATORY

Run this before EVERY deploy that touches user-facing code. No exceptions.
Pope copies the entire block below and runs it on the VPS. Do not skip steps.
Do not deploy if any step fails or shows unexpected output.

### Step 1 — Check for active sessions
Run on VPS:
journalctl -u scout -n 50 --no-pager | grep "POST /chat" | tail -5

Expected: no output, or last entry older than 10 minutes.
If recent /chat calls exist — STOP. Wait until quiet. Do not proceed.

### Step 2 — Check Scout is healthy
curl -s https://scout.regtool.org/status

Expected: {"maintenance": false, ...}
If Scout is unreachable or returns error — STOP. Fix the issue first.

### Step 3 — Activate maintenance mode
sed -i 's/MAINTENANCE_MODE=false/MAINTENANCE_MODE=true/' /home/scout/.env
systemctl restart scout
sleep 3

### Step 4 — Confirm maintenance is live
curl -s https://scout.regtool.org/status

Expected: {"maintenance": true, ...}
If maintenance is NOT showing — STOP. Do not deploy. Check .env and restart.

### Step 5 — Deploy
cd /home/scout && bash deploy.sh

Expected: Fast-forward, files updated, "Scout deployed."
If "Already up to date" — check git log. Code may not have been pushed.
If merge conflict — STOP. Resolve locally, push, then redeploy.

### Step 6 — Add any new env vars
Check release notes for new env vars before this step.
Add them now: echo "VAR=value" >> /home/scout/.env
If no new vars — skip this step.

### Step 7 — Restart and smoke test
systemctl restart scout
sleep 5
curl -s https://scout.regtool.org/status

Expected: {"maintenance": true, ...} — Scout is up, still in maintenance.
Open https://scout.regtool.org in browser — confirm maintenance page shows.
Run one TEST- key session to confirm core flow works.

### Step 8 — Deactivate maintenance mode
Only run this after Step 7 passes completely.
sed -i 's/MAINTENANCE_MODE=true/MAINTENANCE_MODE=false/' /home/scout/.env
systemctl restart scout
sleep 3
curl -s https://scout.regtool.org/status

Expected: {"maintenance": false, ...}
Open https://scout.regtool.org — confirm landing page is back to normal.

### If anything goes wrong
DO NOT deactivate maintenance mode until the issue is resolved.
Maintenance mode protects users. Keep it on until Scout is confirmed clean.
To check logs: journalctl -u scout -n 100 --no-pager
To hard restart: systemctl restart scout
To rollback: git checkout HEAD~1 && bash deploy.sh (then fix forward)

### One-block copy-paste version (Steps 3–8 only, after Steps 1–2 pass):
sed -i 's/MAINTENANCE_MODE=false/MAINTENANCE_MODE=true/' /home/scout/.env && systemctl restart scout && sleep 3 && curl -s https://scout.regtool.org/status && cd /home/scout && bash deploy.sh && systemctl restart scout && sleep 5 && curl -s https://scout.regtool.org/status
