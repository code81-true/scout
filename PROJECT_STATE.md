# PROJECT_STATE.md — Scout

Last updated: 2026-04-21
Purpose: single source of truth for the project manager
overseeing Scout, MTN, and commercialisation in parallel.
Read once a week. Updated at the end of every CC session.

Reading order for full depth: CLAUDE.md → SOUL.md →
ARCHITECTURE.md → KNOWN_ISSUES.md → DECISIONS.md →
STATUS.md → this file.

---

## 1. Product identity

Scout is a two-hour, single-session AI interview engine. One
person, one time. It produces a spine.yaml (structured), a
Portrait PDF (continuous prose), and a Meridian PDF (five
declarative lines). Scout is the front end of a three-layer arc:
**Scout** (the interview) → **spine.yaml** (the artifact) →
**MyTrueNorth / MTN** (the daily layer that reads the spine
every morning). Scout is free indefinitely; MTN subscription
is the commercial engine. Scout makes itself unnecessary once
the spine is delivered.

---

## 2. Current live state — scout.regtool.org

Everything below is confirmed running in production on the
Hetzner VPS (178.104.57.52, Ubuntu 24.04). VPS HEAD matches
master at commit 25d1faa (verified 2026-04-21).

- Interview engine with seven-layer arc [LIVE]
- Settling conversation after interview close (DEC-SCOUT-006) [LIVE]
- Server-owned four-state machine: interviewing → closing →
  generating → delivered (DEC-SCOUT-003) [LIVE]
- SQLite session + transcript persistence (DEC-SCOUT-002) [LIVE]
- Portrait PDF via WeasyPrint, Meridian PDF via ReportLab
  (DEC-SCOUT-008, DEC-SCOUT-009) [LIVE]
- Full transcript on every API call (DEC-SCOUT-001) [LIVE]
- System-prompt prompt caching (DEC-SCOUT-011) [LIVE]
- All sessions Anonymous — pseudonym detection removed
  (DEC-SCOUT-004) [LIVE]
- YAML parsing pass removed from prompt.py; YAML generated
  server-side only (DEC-SCOUT-005) [LIVE]
- Session row retained after delivery; transcript deleted
  (DEC-SCOUT-014) [LIVE]
- 12-character mixed-case alphanumeric keys; old keys still
  valid (DEC-SCOUT-013) [LIVE]
- Single-use key gate — `KEY:status:recipient` format [LIVE]
- Admin dashboard at `/admin-7x9k2m` (no auth, DEC-SCOUT-010)
  with summary stats, key generation, outcome override,
  recipient + notes fields, test-key toggle [LIVE]
- Admin manual delivery: POST `/admin-7x9k2m/generate` (fast
  path reuses existing `*_delivery.pdf` in spines/, slow path
  runs full pipeline and saves canonical PDFs) [LIVE]
- Public collect flow: GET `/collect/<token>` Scout-register
  landing page, POST `/collect/<token>/verify` (10/min rate
  limit, returns `{valid: true|false}` only), GET
  `/collect/<token>/portrait` and `/meridian` (per-file
  one-shot downloads) [LIVE]
- `/generate` saves canonical `*_delivery.pdf` to spines/ at
  session end so admin fast path fires for every completed
  session [LIVE]
- Maintenance mode via `.env` toggle [LIVE]
- Rate limiting on /auth (5/min/IP) [LIVE]
- robots.txt + noindex meta (no search indexing) [LIVE]
- Gunicorn 3 workers behind nginx with SSL (cert expires
  2026-07-05) [LIVE]
- /health endpoint [LIVE]
- Model allocation: Sonnet interview + YAML, Opus portrait +
  Meridian, Haiku test mode [LIVE]

---

## 3. Committed but not yet deployed

None. VPS HEAD matches master (25d1faa) as of 2026-04-21.
New work from Sprint 1 will populate this section as commits
land on master but await the PRE-DEPLOY CHECKLIST.

---

## 4. Known issues (live)

Active bugs affecting real users today (ordered by severity).
From KNOWN_ISSUES.md. Model-behaviour issues have defensive
handling in production and are not listed here.

- **A08** — Portrait paragraphs occasionally break mid-paragraph
  across page boundaries in WeasyPrint. [degraded]
- **A11** — Meridian body font scales too small on short
  Meridians. [degraded]
- **A10** — Portrait PDF cover: compass north needle slightly
  clipped at top on A4 print. [cosmetic]
- **A12** — Compass animation horizontal position shifts with
  rotating message length. [cosmetic]

---

## 5. Sprint plan

Four sprints, in order. Sprint 1 is the current in-flight
work from the April 21 project update. Dependencies on MTN
are flagged.

### Sprint 1 — Three-tier mental health + decision architecture + portrait altitude (IN FLIGHT)

**Theme.** Replace binary pause-or-continue CONSTRAINT 10 with
a three-tier response (acknowledge / slow / close-for-safety).
Enrich Scout's listening in Layers 2, 5, 6, 7 to extract
heuristics, failure-modes, context-triggers as byproducts of
attention — not new question types. Fix portrait altitude
identified from first cohort feedback (2026-04-21). Scout's
interview register does not change.

**Items.**
- Component 0 — Pre-session framing: one grounding statement
  after the "Ready?" threshold, before Layer 1 [IN SPRINT 1]
- Component 1 — New CONSTRAINT 10 with three tiers
  (acknowledge / slow / close-for-safety). "We can stay here
  as long as this needs" offer gated to heavier end of Tier 2
  only [IN SPRINT 1]
- Component 2 — Layer 6 (Shadows) enrichment: four-part
  failure pattern listening (pattern/trigger/tells/interrupt),
  reach-for-missing-parts questions only when door opens [IN SPRINT 1]
- Component 3 — Layer 2 / 5 / 7 listening additions:
  decision rules in Work, belief-origin in Beliefs, context
  triggers in Long Game [IN SPRINT 1]
- Component 4 — engine.py Call 3 adds `heuristics`,
  enriched `failure_modes` (with `north_watch`),
  `context_triggers` (with `north_watch`). Call 4 adds
  `sensitive_areas` under `north_instructions` when Tier 2
  handling occurred [IN SPRINT 1]
- Portrait altitude fix — identified from first cohort
  feedback on 2026-04-21; not yet in code. Chronicler prompt
  tuning to adjust tone/depth calibration [IN SPRINT 1]
- DEC-SCOUT-015 (three-tier mental health) and DEC-SCOUT-016
  (decision architecture YAML extraction) to be written into
  DECISIONS.md on commit

**Definition of done.**
- Local test session produces YAML containing `heuristics`,
  `failure_modes`, `context_triggers` keys (empty lists OK)
- No invented content in any of the three sections
- Scout behaviour verified against a simulated Tier 2
  disclosure — slows down without announcing
- Portrait altitude fix ships; next cohort session confirms
  corrected tone
- Deployed to VPS via PRE-DEPLOY CHECKLIST
- MTN Pydantic models updated to accept new sections
  (Component 5) before any spine is bridged [BLOCKED ON MTN]

### Sprint 2 — Portrait polish + delivery edge cases

**Theme.** Complete the v1.1 polish items that tune around
the live admin + delivery flow now that it's in users' hands.

**Items.**
- Six delivery edge cases — design exists, implement [IN SPRINT 2]
- "Keep your Meridian safe" post-download message [IN SPRINT 2]
- Fix A08 (paragraph page-break) and A11 (Meridian font
  size) — small code changes, ship with this sprint [IN SPRINT 2]
- Fix A10 (compass needle clipped) and A12 (compass animation
  shift) — cosmetic, ship with this sprint [IN SPRINT 2]
- Chronicler portrait altitude post-fix review: confirm
  Sprint 1 fix held across next three cohort sessions [IN SPRINT 2]

**Definition of done.**
- All six delivery edge cases handled with test coverage
- A08, A10, A11, A12 closed in KNOWN_ISSUES.md
- "Keep your Meridian safe" message reaches users after
  download

### Sprint 3 — MTN bridge + v1.1 polish

**Theme.** Replace the manual YAML copy with a real handshake.
Complete the v1.1 polish items from ROADMAP.md.

**Items.**
- MTN documentation sprint (SOUL/ARCHITECTURE/DECISIONS/
  KNOWN_ISSUES/ROADMAP/HANDOVER) [BLOCKED ON MTN]
- Scout → MTN handshake button — one-click bridge [BLOCKED ON MTN]
- Mobile full redesign (typography, input treatment, generation
  screen layout) [IN SPRINT 3]
- Prompt compression — 34% token reduction identified [IN SPRINT 3]
- Waitlist capture for organic discovery [IN SPRINT 3]
- Prompt caching broader scope (per-session strategies) [IN SPRINT 3]

**Definition of done.**
- Bridge is a button the user presses, not a file Pope copies
- MTN can read new YAML sections (heuristics, failure_modes,
  context_triggers, sensitive_areas) without crashing
- Mobile passes a real-device review at 390px, 480px, 768px
- Token cost per session drops measurably after compression

### Sprint 4 — v1.2 stability and scale

**Theme.** Production-grade observability and the operator
affordances a one-person beta outgrows.

**Items.**
- Structured JSON logging (session id, state, model, latency) [IN SPRINT 4]
- Cost tracking per session (Anthropic usage attributed) [IN SPRINT 4]
- Sliding context window for sessions > 90 minutes
  (must preserve DEC-SCOUT-001) [IN SPRINT 4]
- Spine review cycle — 90-day prompt to revisit [IN SPRINT 4]
- Partial session warning — detect unclean closes [IN SPRINT 4]
- Admin dashboard authentication (replaces DEC-SCOUT-010
  Phase 1 obscurity) [IN SPRINT 4]
- Dedicated non-root `scout` user for Gunicorn
  (security backlog item) [IN SPRINT 4]

**Definition of done.**
- `journalctl -u scout` emits parseable JSON
- Admin sees $ per session in dashboard
- Long sessions don't fail YAML validation
- /admin-7x9k2m gated by real auth

---

## 6. MTN dependencies

**What Scout produces for MTN today.** spine.yaml with
sections: meta, purpose, hats, values, hard_limits, shadows,
long_game, relationships, north_instructions (with
north_moments), intellectual_diet, unresolved.

**What Scout will produce after Sprint 1 ships.** All of the
above plus: heuristics, enriched failure_modes (with
north_watch), context_triggers (with north_watch), and
sensitive_areas nested under north_instructions when Tier 2
handling occurred.

**What MTN must build before Scout can bridge.**
- Pydantic model updates to accept the new sections without
  crashing or silently dropping them (Component 5)
- Handler for `north_watch` directives — invocation logic
  that surfaces heuristics/failure-mode warnings in daily
  dialogue
- Handler for `sensitive_areas` — territory to hold without
  probing, only surfaced on user initiation

**Current bridge status.** Manual. The YAML file is copied
by hand from `/home/scout/spines/` to MTN's input path.
No API. No shared bucket. No automated handoff.

**Deployment sequence — do not violate.**
1. Ship Sprint 1 Scout changes
2. Test locally that new YAML sections appear
3. Deploy Scout to VPS
4. Open fresh CC session for MTN — update Pydantic models
5. Only then bridge any new spine to MTN

Loading a post-Sprint-1 spine into the current MTN will
crash the loader or silently drop the new sections.

---

## 7. Commercial dependencies

Scout is free. MTN is the commercial layer. Nothing below is
built yet. Every item is gated on legal or external work.

- **Legal review** — terms, privacy, consent copy
  [BLOCKED ON LEGAL]
- **GDPR compliance** — DPA, data map, deletion workflow
  [BLOCKED ON LEGAL]
- **User accounts** — for MTN subscribers only; Scout
  sessions remain anonymous (DEC-SCOUT-004) [PARKED until v2.0]
- **Encrypted spine storage** — opt-in server-side custody
  for MTN accounts [PARKED until v2.0]
- **Stripe billing** — MTN subscription [PARKED until v2.0]
- **Stripe donation page** — optional post-session donation
  [PARKED until v2.0]
- **Email invitation system** — current key delivery is
  manual [PARKED until Phase 2]
- **Admin dashboard auth** — replaces DEC-SCOUT-010 Phase 1
  obscurity before operator count exceeds 1 [IN SPRINT 4]
- **File deletion after download** — `/home/scout/spines/`
  cleanup post-delivery [PARKED until v2.0]

---

## 8. Beta cohort status

- **Target.** 50 sessions.
- **Current count.** 3 real user sessions completed — Boss,
  JRMTWFU4FL, GHR7U6GEGU.
- **Feedback summary.** Boss cleared the Boss/David standard
  (SOUL.md) — portrait named what he carried without being
  asked. His session led to the settling conversation
  (DEC-SCOUT-006) after he was left emotionally open at
  generation time. First-cohort feedback (2026-04-21) from
  JRMTWFU4FL and GHR7U6GEGU identified a portrait altitude
  issue — now scheduled for Sprint 1 fix.
- **Portrait altitude fix status.** Pending. Not yet in code.
  Identified from first cohort feedback on 2026-04-21.
  Scheduled for Sprint 1.
- **Beta feedback log.** No dedicated file exists yet.
  Feedback is captured in STATUS.md for now. A dedicated
  log may be worth creating once the cohort grows beyond
  ~10 sessions.

---

## 9. Decisions in effect

Active decisions from DECISIONS.md. Parked (DEC-SCOUT-012)
excluded. Two further decisions (DEC-SCOUT-015 three-tier
mental health, DEC-SCOUT-016 decision architecture YAML) are
planned for Sprint 1 commit and not yet in DECISIONS.md.

- **DEC-SCOUT-001** — Full transcript on every API call.
  No summarisation, no rolling window. [2026-04-06]
- **DEC-SCOUT-002** — SQLite persistence over in-memory
  sessions. Survives process restart. [2026-04-15]
- **DEC-SCOUT-003** — Server owns session state. Four
  states only: interviewing → closing → generating →
  delivered. [2026-04-15]
- **DEC-SCOUT-004** — All sessions Anonymous. Pseudonym
  detection removed. [2026-04-16]
- **DEC-SCOUT-005** — Scout never produces YAML in
  conversation. YAML extraction is a separate server-side
  pass. [2026-04-16]
- **DEC-SCOUT-006** — Settling conversation between
  interview close and artifact generation returns the
  person to the surface. [2026-04-09]
- **DEC-SCOUT-007** — Meridian replaces Constitution as the
  user-facing name for the five-line document. [2026-04-15]
- **DEC-SCOUT-008** — PDF delivery only; no plain text
  file. [2026-04-09]
- **DEC-SCOUT-009** — Meridian via ReportLab (precise
  layout); Portrait via WeasyPrint (HTML/CSS). [2026-04-15]
- **DEC-SCOUT-010** — Admin dashboard at unpredictable URL,
  no auth; Phase 1 only. [2026-04-19]
- **DEC-SCOUT-011** — Prompt caching on Scout system
  prompt (system prompt only). [2026-04-11]
- **DEC-SCOUT-013** — 12-character mixed-case alphanumeric
  keys. Old keys remain valid. [2026-04-19]
- **DEC-SCOUT-014** — After delivery, transcripts are
  deleted; sessions row retained as permanent history. [2026-04-19]

**Pending (Sprint 1 commit).**
- **DEC-SCOUT-015** — Three-tier mental health response
  replaces binary CONSTRAINT 10. Tier detection in Scout's
  judgment. Close only for immediate safety. [PENDING]
- **DEC-SCOUT-016** — Decision architecture YAML extraction:
  heuristics, enriched failure_modes with north_watch,
  context_triggers with north_watch. Interview register
  unchanged. [PENDING]

---

## 10. What the manager needs to know right now

1. **Sprint 1 is the critical path, and it blocks on MTN.**
   Three-tier mental health + decision architecture +
   portrait altitude fix is the active Scout work. The new
   YAML sections it emits (heuristics, failure_modes,
   context_triggers, sensitive_areas) will crash or silently
   drop in the current MTN Pydantic model. A new spine must
   not be bridged until MTN updates. Ask about MTN session
   start date.
2. **Portrait altitude was flagged 2026-04-21 by the first
   cohort.** JRMTWFU4FL and GHR7U6GEGU surfaced it. The fix
   is scheduled for Sprint 1 but is not yet in code. No new
   portraits should go to beta users until the fix ships.
3. **Beta cohort is at 3/50.** Scout has fewer real sessions
   than it has design decisions. Portrait tuning has limited
   signal until the cohort grows. Ask about recruitment plan
   and cadence.
4. **Legal review has not started.** v2.0 commercial launch
   depends on it — terms, privacy, GDPR, DPA. Long lead-time
   item. Ask about engagement date.
5. **Admin dashboard has no auth (Phase 1 obscurity only).**
   Acceptable today — one operator, one unpredictable URL,
   no public discovery path. Becomes unsafe the moment
   operator count > 1. Sprint 4 commits to real auth.

---

## 11. How to read the codebase

In order. Do not skip.

1. **CLAUDE.md** — the project contract. Review gates,
   PRE-DEPLOY CHECKLIST, security rules, STATUS.md rules.
2. **SOUL.md** — why Scout exists. What must never
   compromise. If a decision conflicts with SOUL.md, the
   decision is wrong.
3. **ARCHITECTURE.md** — physical shape: stack, domains,
   session lifecycle, models, keys, DB, deploy.
4. **KNOWN_ISSUES.md** — live bugs, parked features, model
   quirks with defensive handling.
5. **DECISIONS.md** — why any specific choice was made.
6. **STATUS.md** — live state at moment of last commit
   (date-stamped, detailed).
7. **This file** — cross-product snapshot for managerial
   read.

Implementation files:
- `app.py` — Flask routes and orchestration
- `scout/prompt.py` — the Scout interviewer system prompt
- `scout/engine.py` — API calls, YAML assembly, model routing
- `scout/database.py` — SQLite schema and queries
- `scout/chronicler.py` — portrait-writing prompt
- `scout/constitution.py` — Meridian prompt
- `templates/index.html` — three-state SPA (landing, guide,
  conversation)
- `templates/portrait.html` — portrait display page
- `templates/portrait_pdf.html` — WeasyPrint PDF template
- `templates/admin.html` — admin dashboard
- `templates/collect.html` — delivery landing page
