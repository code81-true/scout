# SCHEMA_CONTRACTS.md
## Spine YAML Schema — The Interface Contract Between Scout and MTN

**Last updated:** 23 April 2026
**Verified from:** engine.py on Scout VPS (generate_yaml_sections,
Calls 1–4), 23 April 2026
**Authoritative home:** PM project
**Copied to:** Scout repo root, MTN repo root

Scout produces the spine. MTN consumes it. This file defines
exactly what Scout emits and exactly what MTN must accept.
No developer builds to a recalled spec. Both sides read this
file before writing any code that produces or consumes spine
YAML.

When Scout's output changes, this file updates FIRST. Then
the BRIDGE.md for the MTN session carries the change. Then
MTN updates its models.

---

## Existing Sections — Calls 1 and 2

Call 1 produces: meta, purpose, hats.
Call 2 produces: values, hard_limits.

No explicit field-level schema exists in the engine.py
extraction directives for these sections. The model is told
to use "the exact schema defined in your instructions." Field
names for these sections must be verified from actual spine
output on a full production session.

```yaml
meta:                              # [VERIFY from full session]
  session_date: str
  key: str
  session_type: str
  north_notes: str | null

purpose:                           # [VERIFY from full session]
  statement: str

hats:                              # [VERIFY from full session]
  - name: str
    description: str
    cost: str | null
    energy: str | null

values:                            # [VERIFY from full session]
  - name: str
    description: str

hard_limits:                       # [VERIFY from full session]
  - str
```

**These [VERIFY] markers will be resolved from the first full
production session spine generated this weekend.**

---

## Existing Sections — Call 3 (partial)

Call 3 also produces: shadows, long_game, relationships.
Same situation as Calls 1 and 2 — no explicit field-level
schema in the extraction directives.

```yaml
shadows:                           # [VERIFY from full session]

long_game:                         # [VERIFY from full session]

relationships:                     # [VERIFY from full session]
```

---

## Sprint 1 Sections — Call 3

Verified from engine.py on VPS, 23 April 2026. These are the
literal field names the model is instructed to produce.

### heuristics
Top-level section. List of objects. May be empty list.

```yaml
heuristics:
  - id: str                    # snake_case identifier
    statement: str             # the rule as the person would state it
    evidence: str              # specific transcript moment
    confidence: Literal["high", "medium", "low"]
    self_type: Literal["present", "cast"]
    invocation_note: str       # direct instruction to North
```

**If nothing surfaced:** `heuristics: []`

### failure_modes
Top-level section. List of objects. May be empty list.
No `id` field.

```yaml
failure_modes:
  - pattern: str               # what they actually do
    trigger: str | null        # what sets it off
    tells: str | null          # observable signals
    interrupts: str | null     # what has worked — null if unknown
    north_watch: str | null    # direct instruction to North
```

**Field note:** `interrupts` is PLURAL.

### context_triggers
Top-level section. List of objects. May be empty list.

```yaml
context_triggers:
  - id: str                    # snake_case identifier
    condition: str             # specific circumstance
    deviation: str             # what they actually do
    north_watch: str | null    # direct instruction to North
```

**If nothing surfaced:** `context_triggers: []`

---

## Sprint 1 Sections — Call 4

### sensitive_areas
Nested under `north_instructions`. NOT a top-level section.
Conditional — only present when Tier 2 mental health handling
occurred during the Scout session.

```yaml
north_instructions:
  sensitive_areas:             # CONDITIONAL — may not exist
    - hat: str                 # required
      note: str                # required
```

**If no Tier 2 handling occurred:** `sensitive_areas` is omitted
entirely from the spine. MTN must handle both "missing" and
"present but empty list."

---

## Schema Rules

1. **Empty list beats invented content.** If Scout didn't
   extract anything, the section is `[]`.
2. **Null beats invented field.** If a field wasn't observed,
   it's `null`.
3. **All Sprint 1 sections are optional.** Pre-Sprint-1 spines
   load without error using `[]` or `None` defaults.
4. **sensitive_areas may be absent entirely.** Unlike the other
   three Sprint 1 sections which are always present (even if
   empty), sensitive_areas only appears when Tier 2 handling
   occurred.

---

## Correction History

**23 April 2026 — Full Sprint 1 correction.** Original contract
(22 April) was built from a developer's conversation report,
not from engine.py. Multiple field names were wrong. Corrected
against engine.py source code verified on Scout VPS. This
correction invalidates MTN Session 7's Pydantic model changes,
which were built to the incorrect contract.

| Field | Was (wrong) | Is (correct, from engine.py) |
|-------|-------------|------------------------------|
| heuristics fields | domain, rule, source_layer | id, statement, evidence, self_type, invocation_note |
| heuristics confidence | "stated" / "inferred" | "high" / "medium" / "low" |
| failure_modes.interrupts | interrupt (singular) | interrupts (plural) |
| context_triggers fields | situation, response (no id) | condition, deviation (with id) |

---

## Update Protocol

1. Scout changes its YAML output → Scout developer updates
   this file with exact field names from engine.py → PM copies
   to MTN repo and PM project
2. MTN needs a new field from Scout → PM adds it here first →
   Scout implements → MTN consumes
3. Neither side implements schema changes without this file
   being updated first
4. **DEC-PM-001 enforcement:** This file must be verified
   against actual code or actual YAML output. Never from
   conversation, memory, or session notes.

This file is the contract. Code follows the contract.
The contract does not follow the code.

---

*Authoritative copy lives in the PM project. Copied to both
repos after every update.*
