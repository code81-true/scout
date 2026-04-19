# HANDOVER.md — Scout Project Handover

This document replaces the founding handover. A new
Claude Code chat reading this file should be able to
continue the project cold, without any other context
from prior conversations.

If anything in this document conflicts with SOUL.md,
SOUL.md wins.

---

## Who Pope is

**Identity.** Principal at Bridge Medtech Ltd, London.
Works as a regulatory affairs, design controls, and
quality management system contractor in medical devices,
pharma, and combination products. Self-taught developer.
Building AI-powered tools for regulated industries under
the "RegTool" brand. Scout is part of that portfolio —
it sits adjacent to MyTrueNorth (MTN), the daily layer
that reads the spine YAML Scout produces.

**Working style.**
- Direct. Skip unnecessary preamble.
- Wants assumptions challenged when they are flawed.
- Wants the "why" behind significant decisions, not
  just the "what."
- Uses conventional commits (`feat:`, `fix:`, `docs:`,
  `refactor:`, `test:`).
- Runs CC in auto-approve mode — which means the review
  gates in `CLAUDE.md` matter. Respect them.
- Updates `STATUS.md` at the end of every session and
  before every commit. Date-stamp every entry.

**Non-negotiable rules.**
1. Never touch `.env`. Do not read, print, log, or
   modify it.
2. Never commit anything from `access/` except
   `keys_generate.py`. `keys.txt` lives on the VPS only.
3. Never deploy without running the PRE-DEPLOY CHECKLIST
   in `CLAUDE.md`. Maintenance mode goes on *before* the
   deploy and comes off only after a confirmed smoke
   test.
4. Never fix tests to match code or code to match tests
   without first checking the `docs/` source of truth.
5. Never delete files without explicit instruction.

**Where Pope struggles (attention errors, not
comprehension errors).**

- Copy-pasting commands into the wrong window (terminal
  vs chat).
- SSH-ing into the VPS from inside the VPS (already
  connected).
- Running commands in the wrong directory.

These happen when tired or multitasking — not because
he does not understand.

**Solution:** always give the full command suite,
including `cd` to the correct directory first. Never
say "run the usual command." Always include what to
expect to see after the command runs.

**How Pope collaborates with CC.** Pope will pause you
at review gates — system prompt changes, API call
structure, YAML schema, first real session, anything
that feels like a big decision. If you are unsure
whether something needs review, it does. Overcommunicate.

---

## What Scout is today

Scout is a two-hour, single-session AI interview system,
live on the public internet behind an invitation-key
gate. A person enters their key, sits the interview,
and — after a settling conversation and a generation
pass — receives a Portrait PDF and a Meridian PDF
delivered to the recipient address bound to their key.

What exists today:
- Full interview engine with settling conversation
  before generation (DEC-SCOUT-006)
- Server-owned four-state session machine
  (DEC-SCOUT-003): `interviewing → closing →
  generating → delivered`
- SQLite-backed session and transcript persistence
  (DEC-SCOUT-002)
- Portrait PDF (WeasyPrint) and Meridian PDF
  (ReportLab) generation
- All sessions labelled Anonymous — pseudonym detection
  removed (DEC-SCOUT-004)
- 12-character mixed-case alphanumeric keys, single use
  (DEC-SCOUT-013)
- Maintenance mode toggle via `.env` on the VPS
- Admin dashboard at an unpredictable URL, no auth
  (DEC-SCOUT-010) — **committed, not yet deployed**
- System-prompt caching on Anthropic calls
  (DEC-SCOUT-011)

This is the v1.0 "Stabilise" state. It is not the
founding vision. See ROADMAP.md for what is next and
SOUL.md for why.

---

## Current deployment

**Live on the VPS (scout.regtool.org):**
- The Scout interview engine
- The key gate
- The settling conversation
- PDF generation and delivery
- Maintenance mode
- Rate limiting on /auth
- robots.txt blocking search indexing

**Committed but not yet deployed:**
- Admin dashboard
- New key format (old keys remain valid — DEC-SCOUT-013)
- Outcome tracking
- Pseudonym detection removal (DEC-SCOUT-004)
- Parsing pass removal and settling phrase lock
  (DEC-SCOUT-005)
- Landing page copy refinements and guide page polish

**MyTrueNorth (compass.regtool.org):** separate
application, separate systemd unit. The Scout → MTN
bridge is still manual — spine YAML is copied by hand
(ARCHITECTURE.md §Scout → MTN bridge).

---

## Top of mind

Three things are current:

1. **Admin dashboard needs deploying.** It is committed
   (876f7cc on master) but has not yet passed through
   the PRE-DEPLOY CHECKLIST. This is the next
   production deploy.

2. **MTN session needs opening.** A fresh Claude Code
   chat for MyTrueNorth — to run the same documentation
   exercise Scout just completed (SOUL, ARCHITECTURE,
   DECISIONS, KNOWN_ISSUES, ROADMAP, HANDOVER).

3. **Documentation sprint just completed.** Six
   documents written and saved: SOUL.md, ARCHITECTURE.md,
   DECISIONS.md, KNOWN_ISSUES.md, ROADMAP.md, and this
   file. They are the current source of truth. If a new
   CC session contradicts them, the docs win.

---

## Next session agenda

In order:

1. **Deploy the admin dashboard.** Run the PRE-DEPLOY
   CHECKLIST in `CLAUDE.md` end to end. Do not skip
   steps. Smoke-test with a TEST- key before lifting
   maintenance mode.

2. **Open the MTN Claude Code chat.** Paste the
   handover prompt. Begin the same documentation arc
   for MyTrueNorth.

3. **Design the Scout → MTN YAML bridge.** Once MTN
   documentation is complete. The handshake is the most
   important conversion point in the product.

Everything else is downstream of these three.

---

## VPS access and deploy pattern

**Host:** Hetzner VPS, IP `178.104.57.52`, Ubuntu 24.04.
**Home:** `/home/scout/` on the VPS.
**Source of truth:** GitHub. The VPS pulls; it does not
push.

**Deploy pattern — always:**
1. Commit and push locally.
2. SSH to the VPS.
3. Run the PRE-DEPLOY CHECKLIST (`CLAUDE.md` §PRE-DEPLOY
   CHECKLIST — MANDATORY). No exceptions.
4. Maintenance mode on → `deploy.sh` → smoke test →
   maintenance mode off.

**`deploy.sh` runs on the VPS only.** Not from the
developer's machine.

**Secrets:** `.env` lives on the VPS only. `access/keys.txt`
lives on the VPS only. Neither is ever in git.

---

## How to start a CC session on Scout

Read these files in order before touching any code:

1. **`CLAUDE.md`** — the project contract. Review
   gates, pre-deploy checklist, security rules,
   STATUS.md rules.
2. **`SOUL.md`** — why Scout exists and what it must
   never compromise. If a proposed change conflicts
   with SOUL.md, the change is wrong.
3. **`ARCHITECTURE.md`** — the physical shape: stack,
   domains, session lifecycle, model allocation, key
   system, database, deploy pipeline.
4. **`KNOWN_ISSUES.md`** — active bugs, parked
   features, known model behaviour issues. Many future
   temptations rhyme with past bugs documented here.

After those four: `DECISIONS.md` for the "why" behind
any specific choice, `ROADMAP.md` for what is next,
and `STATUS.md` for the live state at the moment of
the last commit.

---

## The standard — Boss and David

Two sessions set the bar. Every future session is
measured against them.

**Boss** — a 20-year-old who gave two honest hours and
received a portrait that named what he carried without
being asked. His session proved Scout can see a young
person clearly, without pretending to wisdom, without
reaching for advice. It proved that a portrait can
arrive as recognition rather than interpretation.

**David** — a politician who named his own deficit in
numbers like a budget, and then needed to leave. His
session proved Scout can hold a person of standing
without flattering them, and can close cleanly even when
the person ends the interview on their terms. It also
proved that transcripts must survive process restarts
(DEC-SCOUT-002) — the lesson that SQLite persistence
was built from.

Both portraits cleared the bar. That bar is not moved
downward by later sessions that fall short of it. When
in doubt about whether an output is good enough, the
question is always:

> Would this portrait have served Boss or David?

If the answer is no, the output is not ready to ship.
