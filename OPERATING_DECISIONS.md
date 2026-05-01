# OPERATING_DECISIONS.md
## Cross-cutting decisions governing Scout ↔ MTN ↔ Commercial

Decisions that apply to both repos and to how the PM writes
session briefs. Repo-specific decisions stay in each repo's
DECISIONS.md. Decisions here govern the boundaries between
systems.

Read this file at the start of every CC session alongside
CLAUDE.md.

---

### DEC-PM-001 — Schema specs verified against actual code output
**Date:** 22 April 2026
**Trigger:** MTN Session 6 built Pydantic models to a spec that
didn't match Scout Sprint 1's actual YAML output. Field names,
enum values, and structure all diverged. Models crashed on real
Scout spines.

**Decision:** When one repo produces structured data the other
consumes, the PM must extract the literal field names, types,
and enums from the producing repo's actual code (not session
notes, not memory, not prior conversation) and deliver them to
the consuming repo's CC session brief before any models are
written. The canonical source for the spine schema is
SCHEMA_CONTRACTS.md.

**What changes:** Every BRIDGE.md that involves schema work
must include the relevant section of SCHEMA_CONTRACTS.md
verbatim. No developer builds to a recalled spec.

**Clarification (23 April 2026):** The consuming side never
specifies what the producing side emits. Information flows
producer → PM → consumer. Never consumer → PM →
producer-assumed-to-agree.

---

### DEC-PM-002 — Beta recruitment hold
**Date:** 22 April 2026
**Status:** LIFTED — 1 May 2026

**Trigger:** Post-Sprint-1 production session showed Scout
rushing interviews — shallow threading, generic depth signals
clearing the bar, closing sequence firing before shadows opened.

**Decision:** No new Scout keys issued until a post-fix
production session confirms interview depth has been restored.

**Lift condition met:** Two production sessions cleared the bar
(NlF6dc4mdobt on 25 April, 1JNQrG6CnglM on 1 May). Sprint 3
barrier toolkit and diagnostic arc verified in production.
Extraction prompt locked to SCHEMA_CONTRACTS.md. Beta
recruitment is open.

---

### DEC-PM-003 — Translation lives in bridge.py only
**Date:** 1 May 2026
**Trigger:** Scout's YAML output and MTN's operating format
don't map 1:1. A translation layer is needed. Three options
considered: loader-side reshaping, separate script, or bridge.py.

**Decision:** Three independent layers. No exceptions.
Scout (producer) → bridge.py (translator + transport) → MTN
(consumer). Scout evolves its interview and extraction without
knowing MTN exists. MTN evolves its operating format without
knowing Scout exists. bridge.py is the only code that knows
both schemas. When either side changes, bridge.py updates.
Neither product touches the other.

---

### DEC-PM-004 — Silence thresholds from failure_mode density
**Date:** 1 May 2026
**Trigger:** Silence threshold for hats needs to be derived
automatically, not hardcoded. People with intense focus on a
hat should have shorter thresholds.

**Decision:** Derive from failure_mode and context_trigger
density per hat. High (3+ matches): 3 days. Medium (1-2): 7
days. Low (0): 14 days. Automated, grounded in what the user
said to Scout, no operator judgment required.

---

### DEC-PM-005 — Forward compatibility protocol
**Date:** 1 May 2026
**Trigger:** Scout prompt changes could produce new spine
fields that break bridge.py. Need a protocol that lets both
sides evolve independently.

**Decision:** Three rules. (1) bridge.py treats every mapped
input field as optional — present → use, absent → default.
(2) bridge.py ignores unmapped fields silently — no crash,
no warning. (3) Scout changes never assume bridge.py awareness
— Scout deploys independently, bridge.py catches up on its
own schedule. Rules 6-8 added to SCHEMA_CONTRACTS.md Update
Protocol in both repos.

---

### DEC-PM-006 — Two-tier hats
**Date:** 1 May 2026
**Trigger:** Scout produces self_described hats (user named)
and observed_roles (Scout noticed). Both should be operational
but treated differently to preserve trust.

**Decision:** observed_roles become operational hats with
`confirmed: false`. North introduces them conversationally
before activating: "Scout noticed you seem to carry [X] as a
role. Does that feel right?" User confirms → `confirmed: true`,
full tracking begins. User rejects → hat removed.
self_described hats are `confirmed: true` with immediate full
tracking.

---

### DEC-PM-007 — Caller.py amendment for ops scripts
**Date:** 1 May 2026
**Trigger:** bridge.py needs to call the Anthropic API for
Sonnet translation but can't import caller.py without pulling
in service dependencies.

**Decision:** caller.py is the mandatory path for all runtime
API calls made on behalf of a user inside the FastAPI service.
Ops scripts (bridge.py, admin tools, migration scripts) may
call the Anthropic API directly. Criteria: if the call happens
during a user's live session → caller.py. If operator-initiated
with no user waiting → direct call. All direct calls log model,
token count, and cost to stdout. Amends original caller.py
standing rule.

---

### DEC-PM-008 — Spine evolution
**Date:** 1 May 2026
**Trigger:** Operating spine fields start empty at translation
time (cooling, weekly_minimum, etc.) and need to fill through
use. Question: how do updates happen?

**Decision:** Operating spine evolves continuously from
conversation evidence. Subtle changes (new hard limit from
clear evidence, silence threshold adjustment) apply
automatically. Quarterly review presents accumulated evolution
as a summary — "here's how we've evolved" — not as a list of
approval requests. User is a witness. User intervenes only if
something feels wrong. Amends DEC-009: ceremony means
visibility of change, not permission to change.

---

### DEC-PM-009 — Cooling protocol replaces static never
**Date:** 1 May 2026
**Trigger:** The static `never` list was a permanent
behavioural prohibition. In reality, North should never
permanently abandon a topic — that makes it a people-pleaser.

**Decision:** Pushback triggers a cooling period. First
pushback: 14 days. Second: 30 days. Third: dormant (North
stops initiating, user can reactivate). North never permanently
deletes — it gives space. The `never` field is replaced by
`cooling: list` in the Pydantic model. Runtime implementation
is a future session.

---

### DEC-PM-010 — Weekly review shows the full board
**Date:** 1 May 2026
**Trigger:** `weekly_minimum` as static engagement frequencies
is prescriptive and nagging. Better to show the full picture
and let the user draw conclusions.

**Decision:** All hats surfaced every week with engagement
level. Quiet hats noted without judgment. The review accepts
uneven attention as natural — wave patterns differ per person.
Purpose is awareness, not correction.

---

### DEC-PM-011 — Spine lineage
**Date:** 1 May 2026
**Trigger:** After translation, the operating spine contains
Sonnet-inferred fields the person never said. Which spine is
the source of truth?

**Decision:** The Scout spine is the constitutional record —
what the person said at a point in time. Immutable. Archived.
Never modified. The operating spine is derived and evolves
through use. A second Scout session merges new constitutional
input into the existing operating spine — does not replace it.
Runtime state (cooling, engagement, confirmed hats) preserved
across sessions.

---

### DEC-PM-012 — Tone calibration
**Date:** 1 May 2026
**Trigger:** How should North's tone be determined? People's
stated preference for feedback style is unreliable — everyone
says "be honest" but not everyone means it.

**Decision:** Scout's interview behaviour is the primary tone
signal. Scout already calibrates in real time — sharp with
people who engage directly, softer with people who need it. A
future closeout question confirms the register established
during the session. bridge.py passes through when present,
derives from session arc when absent. No second-guessing
demonstrated tolerance. The closeout question is confirmatory,
not qualifying.

---

### DEC-SHARED-001 — Sprint specs include Invariants section
**Date:** 22 April 2026

**Decision:** Every sprint or session brief that modifies a
system prompt must include an "Invariants" section listing the
behaviours that must not degrade. The developer checks post-
build. The PM checks post-deploy via production verification.

**Applies to:** Both repos. Any prompt-modifying work.

---

### DEC-SHARED-002 — Verification tests production code path
**Date:** 22 April 2026

**Decision:** Verification must exercise the actual function
the server calls, not an isolated API call that bypasses the
production code path. "Isolated call works" ≠ "production
path works."

**Applies to:** Both repos. Any change that affects API call
behaviour.

---

### DEC-SHARED-003 — Prompt changes are transformative, not additive
**Date:** 22 April 2026

**Decision:** Every instruction added to a prompt changes how
the model weighs every existing instruction. No prompt change
is purely additive. When reviewing modifications, ask: "Does
this make the model busier? Which existing behaviours might
lose weight?"

**Applies to:** Both repos. Any prompt modification.

---

### DEC-SHARED-004 — Prompt deploys require verification before beta exposure
**Date:** 23 April 2026

**Decision:** Any deploy that modifies an interview or system
prompt requires a verification session before beta users are
exposed. Deploy freely. Verify before inviting users.

**Applies to:** Both repos. Any prompt-modifying deploy.

---

*Update this file when a cross-cutting decision is made.
Copy to both repos after every update. The PM project holds
the authoritative copy.*
