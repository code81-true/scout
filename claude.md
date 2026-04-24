# Scout — AI Interview Engine

## Read OPERATING_DECISIONS.md for cross-cutting rules that
govern how Scout and MTN interact. These decisions apply
to every session.

## Read SCHEMA_CONTRACTS.md before writing any code that
modifies Scout's YAML output. This is the interface
contract with MTN. Update this file FIRST when output
changes — code follows the contract.

## Read BRIDGE.md if present at session start. It carries
context from MTN and the PM that is relevant to this
session's work.

## What this is
Scout is a single-session AI interview engine that builds a 
spine.yaml — a personal constitution for the MyTrueNorth 
system. It interviews one person, one time, and produces 
a structured YAML file that lives only in their custody.

## Current objective
PR 1 — The Brain only. Pure Python. Terminal only.
No frontend. No database. No auth. Just Scout interviewing.

## Stack
- Python 3.12+
- Anthropic API (claude-sonnet-4-5)
- Single context window — full transcript every call
- No frameworks beyond what is necessary

## Project structure (to be built by CC)
scout/
├── CLAUDE.md
├── README.md
├── .env                  # ANTHROPIC_API_KEY, FLASK_SECRET_KEY,
│                         # MAINTENANCE_MODE, MAINTENANCE_MESSAGE,
│                         # MAINTENANCE_RETURN_MINUTES,
│                         # DELETE_TRANSCRIPTS_ON_BURN
│                         #   (false during beta and development,
│                         #    true at commercial launch — DEC-SCOUT-017)
├── requirements.txt
├── scout/
│   ├── __init__.py
│   ├── prompt.py         # Scout system prompt
│   ├── engine.py         # Context window loop
│   └── session.py        # Session state (in memory only)
└── run_session.py        # Entry point — python run_session.py

## PR 1 success condition
A real person can sit down, run python run_session.py,
complete all seven layers, and receive a draft spine.yaml
in the terminal at the end. Scout must feel like a 
calibrated witness — not a chatbot.

## Key constraints
- One question per Scout response. Never two.
- Never use the word "why"
- Full transcript sent on every API call — no summarisation
- Banned phrases: absolutely, certainly, of course, 
  great question, I can hear that, thank you for sharing
- Health data must not appear in the output YAML

## Anthropic API
- Model: claude-sonnet-4-5
- Max tokens per response: 300 (Scout is concise)
- Temperature: 1.0 (natural variation in language)

## Working arrangement
- Always cd to C:\Users\Manmo\Projectns\scout\ first
- Activate venv before any python commands
- Never assume correct directory

## Human Review Gates — STOP and ask before proceeding

CC is running in auto-approve mode. The following decisions
require Pope to review and confirm before any code is written
or any action is taken. STOP. State the decision clearly.
Wait for explicit approval.

### STOP points:

1. SYSTEM PROMPT CONTENT
   Before writing scout/prompt.py — paste the full proposed
   Scout system prompt for review. This is the brain.
   Do not proceed until Pope approves it word for word.

2. API CALL STRUCTURE
   Before writing engine.py — show the exact structure of 
   the API call: model, temperature, max_tokens, how the
   transcript is assembled. Wait for approval.

3. YAML SCHEMA
   Before writing the parsing pass — show the full proposed
   spine.yaml schema. Every field. Wait for approval.

4. ANY FILE DELETION
   Never delete any file without explicit instruction.
   State what you intend to delete and why. Wait.

5. ANY .ENV ACCESS
   Never read, write, or modify .env. Never print its 
   contents. Never log API keys anywhere.

6. EXTERNAL NETWORK CALLS
   The only permitted external call is to api.anthropic.com.
   Any other network call requires explicit approval first.

7. BEFORE FIRST REAL SESSION
   Before running a live session with a real person —
   show Pope the complete run_session.py flow end to end.
   Wait for approval.

8. ANYTHING THAT FEELS LIKE A BIG DECISION
   If CC is unsure whether something needs review — it does.
   Stop and ask. Overcommunication is correct here.

## What CC can do without asking
- Create new files
- Install pip packages (state what and why first)
- Refactor within an already-approved structure
- Fix bugs in already-approved code
- Run python commands to test already-approved code

## Status tracking
At the end of every CC session, update STATUS.md:
- Mark completed items as done
- Add any new design decisions
- Add any changes made during the session
- Update Next Session Priorities
This file is the single source of truth for project status.
Never let it go stale.

Before every git commit and push, update STATUS.md. Mark
completed items, add any new design decisions made in this
session, add any changes based on review, update Known Gaps,
and update Next Session Priorities. STATUS.md must be current
at the moment of every commit. Never commit without updating
it first.

Before committing, review STATUS.md as a whole document.
Check that it is internally coherent and does not contradict
itself — e.g. an item listed as complete in one section but
as a known gap in another, or a design decision that conflicts
with a later change. Fix any contradictions before committing.

## STATUS.md Rules

Rule 1 — Date stamps:
Every update to STATUS.md must include a date stamp in the
format [YYYY-MM-DD] on the same line as the update. No entry
ever appears without a date. Example:
- Portrait pipeline fixed — serves from disk not sessionStorage [2026-04-09]

Rule 2 — Full read before update:
Before updating STATUS.md, read the entire file. Any existing
entry that is no longer accurate must be marked
[SUPERSEDED YYYY-MM-DD: reason] — never silently deleted or
overwritten. Any entry that has been partially modified must
be marked [MODIFIED YYYY-MM-DD: what changed]. New entries go
at the top of the relevant section with a date stamp.

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

## Security Rules

The access/ directory is sensitive territory.
- access/keys.txt — VPS only, never in git, contains live keys
- Never add any file to access/ without Pope explicitly approving it
- Never commit anything from access/ except keys_generate.py
- If uncertain whether something belongs in access/ — it doesn't
- Keys, credentials, tokens, secrets — VPS .env only, never git

## Next session priorities (as of 2026-04-07)
1. First real user session — monitor and note any issues
2. Post-session Chronicler output review
3. Gunicorn production WSGI server — replace Flask dev server
4. SSH key authentication on VPS — replace password auth
5. Prompt compression — CC analysis report ready, awaiting implementation

## Session Reporting Rule

After every `git push`, deployment to VPS, or milestone completion,
append a new entry to `SESSION_REPORT.md` in the project root.
Do not wait for session end. Do not overwrite previous entries.
Newest entry goes at the top of the file. The file is a permanent
running changelog.

Format — append above all previous entries:

---

## {date, time} — {one-line summary of what just shipped}
**Trigger:** git push / deploy / milestone

### Shipped
- {what was completed and committed}

### Deployed
- {what hit VPS, or "Not yet deployed"}

### Decisions Made
- {any decisions with reasoning, or "None"}

### Blockers Resolved
- {anything unblocked, or "None"}

### New Blockers
- {anything now stuck, or "None"}

### PM Note
- {anything the project PM needs to know — timeline impact,
  scope change, dependency on MTN or commercial, risk flagged}

---

This file is read by the project PM in MTN_SCOUT_MARKET.
Never delete previous entries. The history is the audit trail.