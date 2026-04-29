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

## Read SESSION_REPORT.md to understand what was shipped in
previous sessions. Newest entry first. Do not repeat work
that is already committed.

## What this is
Scout is a two-hour single-session interview engine, live at scout.regtool.org
behind an invitation-key gate. Each session produces three artifacts: a spine.yaml
that feeds MyTrueNorth, a Portrait PDF, and a Meridian PDF — the latter two
delivered to the recipient bound to the key.

## Key constraints
- Full transcript sent on every API call — no summarisation. See DEC-SCOUT-001.
- Health data must not appear in the output YAML.
- Scout's interview rules (banned phrases, "why" prohibition, one-question-per-turn,
  and all other conversation discipline) are enforced in scout/prompt.py.
  See SOUL.md for the philosophy behind them.

## Working arrangement
- Always cd to C:\Users\Manmo\Projectns\Scout\ first
- Activate venv before any python commands
- Never assume correct directory

## Environment variables
All env vars live in `.env` on the VPS only — never committed to git, never logged.

- `ANTHROPIC_API_KEY` — Anthropic API credential.
- `FLASK_SECRET_KEY` — Flask session signing key.
- `MAINTENANCE_MODE` — `true` blocks the landing page and routes; `false` is normal operation.
- `MAINTENANCE_MESSAGE` — copy shown on the maintenance page.
- `MAINTENANCE_RETURN_MINUTES` — estimated return time displayed under the message.
- `DELETE_TRANSCRIPTS_ON_BURN` — `false` during beta and development, `true` at
  commercial launch. See DEC-SCOUT-017.

## Human Review Gates — STOP and ask before proceeding

CC is running in auto-approve mode. The following decisions
require Pope to review and confirm before any code is written
or any action is taken. STOP. State the decision clearly.
Wait for explicit approval.

### STOP points:

1. SYSTEM PROMPT CONTENT
   Before changing scout/prompt.py — paste the proposed diff
   for review. This is the brain. Do not proceed until Pope
   approves it word for word.

2. API CALL STRUCTURE
   Before changing engine.py — show the exact structure of
   the API call: model, temperature, max_tokens, how the
   transcript is assembled. Wait for approval.

3. YAML SCHEMA
   Before changing the spine.yaml schema — update
   SCHEMA_CONTRACTS.md first, then show the diff. Code follows
   the contract. Wait for approval.

4. ANY FILE DELETION
   Never delete any file without explicit instruction.
   State what you intend to delete and why. Wait.

5. ANY .ENV ACCESS
   Never read, write, or modify .env. Never print its 
   contents. Never log API keys anywhere.

6. EXTERNAL NETWORK CALLS
   The only permitted external call is to api.anthropic.com.
   Any other network call requires explicit approval first.

7. BEFORE LIFTING MAINTENANCE
   Before lifting maintenance mode after any prompt change
   that has not been verified in production — wait. Run a
   TEST- key session first. Lift only after the smoke test
   passes. See DEC-SHARED-004 in OPERATING_DECISIONS.md.

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
Full checklist lives in PRE_DEPLOY.md. Run it before every deploy that touches
user-facing code. No exceptions. No shortcuts.

## Security Rules

The access/ directory is sensitive territory.
- access/keys.txt — VPS only, never in git, contains live keys
- Never add any file to access/ without Pope explicitly approving it
- Never commit anything from access/ except keys_generate.py
- If uncertain whether something belongs in access/ — it doesn't
- Keys, credentials, tokens, secrets — VPS .env only, never git

## Session Reporting Rule
After every git push, deployment to VPS, or milestone completion, append a new
entry to SESSION_REPORT.md. Format and trigger conditions defined in
SESSION_REPORTING.md. Newest entry goes at the top. Never delete previous entries.