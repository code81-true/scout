# Scout — AI Interview Engine

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
├── .env                  # ANTHROPIC_API_KEY only
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