# SCHEMA_CONTRACTS.md
## Spine YAML Schema — The Interface Contract Between Scout and MTN

**Last updated:** 25 April 2026
**Verified from:** Real production spine (key NlF6dc4mdobt,
25 April 2026) per Update Protocol Rule 5 — actual output
is the highest authority.
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

Verified from production spine, 25 April 2026.

### meta

```yaml
meta:
  session_date: str            # "2026-04-25"
  schema_version: str          # "1.0"
```

**Field note:** `key` and `session_type` fields were not
present in this spine. `schema_version` was present instead.
[VERIFY on next production session — may vary by session.]

### purpose

```yaml
purpose:
  stated_reason: str           # what the person said they came for
  actual_concern: str          # what Scout observed underneath
  evidence: str                # transcript evidence
```

**Field note:** Three-part structure. Not a single `statement`
field as previously assumed.

### hats

```yaml
hats:
  self_described:
    - label: str               # role name as the person said it
      feeling: str             # how they feel about the role
  observed_roles:
    - label: str               # role Scout observed but person didn't name
      evidence: str            # transcript evidence
```

**Field note:** Two-tier structure — `self_described` and
`observed_roles`. Not a flat list. Not `name`/`description`/
`cost`/`energy` as previously assumed.

### values

```yaml
values:
  - value: str                 # the value as identified
    evidence: str              # transcript evidence
    gravity: str               # how heavily it operates
```

**Field note:** Fields are `value`, `evidence`, `gravity`.
Not `name`/`description` as previously assumed.

### hard_limits

```yaml
hard_limits:
  - limit: str                 # the non-negotiable line
    evidence: str              # transcript evidence
    cost_when_tested: str      # what it costs to hold
```

**Field note:** Three-field object structure. Not a flat list
of strings as previously assumed.

---

## Existing Sections — Call 3

Verified from production spine, 25 April 2026.

### shadows

```yaml
shadows:
  - str                        # prose paragraph, no sub-fields
```

Flat list of strings confirmed.

### long_game

```yaml
long_game:
  vision: str                  # what they're building toward
  gap: str                     # distance between now and vision
  what_would_need_to_change: str
  beneath_the_vision: str      # what the vision is really about
  core_fear: str               # what they're most afraid of
```

**Field note:** Five named fields. Not a flat structure as
previously assumed.

### relationships

```yaml
relationships:
  - name: str                  # person's name or role
    role: str                  # relationship type
    dynamic: str               # how the relationship operates
    cost_or_gift: str          # what it costs or gives
```

Four-field object confirmed.

---

## Existing Sections — Call 4

Verified from production spine, 25 April 2026.

### north_instructions

```yaml
north_instructions:
  session_quality: str         # Scout's assessment of the session
  what_happened: str           # summary of the session arc
  geographical_psychospiritual_context: str
  return_points:
    - str                      # list of strings — threads to pick up
```

**Field note:** Four fields. `return_points` is a list of
strings. No `north_moments` field observed — previous spec
was wrong.

### intellectual_diet

```yaml
intellectual_diet:
  stated_sources: list         # may be empty list
  ghost_library: str           # influences present but not named
  interpretation: str          # what the diet reveals
```

**Field note:** Three-field structure. Not a flat list as
previously assumed.

### unresolved

```yaml
unresolved:
  - zone: str                  # area of unresolved tension
    content: str               # what remains open
```

Two-field object per entry confirmed.

---

## Sprint 1 Sections — Call 3

Verified from engine.py on VPS, 23 April 2026. Confirmed
operational in production spine, 25 April 2026.

### heuristics
Top-level section. List of objects. May be empty list.

```yaml
heuristics:
  - id: str                    # snake_case identifier
    statement: str             # the rule as the person would state it
    evidence: str | null       # specific transcript moment
    confidence: Literal["high", "medium", "low"]
    self_type: Literal["present", "cast"]
    invocation_note: str | null  # direct instruction to North
```

**Field note:** Both `evidence` and `invocation_note` may be
null on sparse sessions — the model omits rather than
fabricates when evidence is thin. Production spine confirmed
all fields populated on 4 entries.

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

**Field note:** `interrupts` is PLURAL. Production spine
confirmed `interrupts` null on two of three entries (honest
null working correctly).

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
"present but empty list." Production spine confirmed: absent
(no Tier 2 handling occurred).

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

**25 April 2026 — All [VERIFY] markers resolved.** Production
spine (key NlF6dc4mdobt) provided the actual field names for
all pre-Sprint-1 sections. Nearly every section differed from
what was previously assumed. Per Update Protocol Rule 5, the
spine output is the highest authority.

| Section | Previously assumed | Actual (from spine) |
|---------|-------------------|---------------------|
| meta | session_date, key, session_type, north_notes | session_date, schema_version |
| purpose | statement (single field) | stated_reason, actual_concern, evidence |
| hats | flat list with name/description/cost/energy | two-tier: self_described + observed_roles |
| values | name, description | value, evidence, gravity |
| hard_limits | flat list of strings | limit, evidence, cost_when_tested |
| long_game | unstructured | vision, gap, what_would_need_to_change, beneath_the_vision, core_fear |
| relationships | unstructured | name, role, dynamic, cost_or_gift |
| north_instructions | north_moments | session_quality, what_happened, geographical_psychospiritual_context, return_points |
| intellectual_diet | unstructured | stated_sources, ghost_library, interpretation |
| unresolved | unstructured | zone, content |

**23 April 2026 — Full Sprint 1 correction.** Original contract
(22 April) was built from a developer's conversation report,
not from engine.py. Corrected against engine.py source code.

| Field | Was (wrong) | Is (correct) |
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
5. **Actual output is the highest authority.** Once a real
   spine exists from a production session, the spine YAML file
   itself is the primary reference for resolving [VERIFY]
   markers and confirming field names. A real spine shows what
   Scout actually produced — not what engine.py asked the model
   to produce, not what a developer recalls. When a spine file
   and engine.py disagree, the spine file wins because that is
   what MTN will actually receive. Engine.py is secondary.
   Developer interpretation of engine.py is tertiary.

6. **Forward compatibility — bridge.py treats every mapped input
   field as optional.** If a Scout field is present, bridge.py uses
   it. If absent, bridge.py defaults gracefully. No field absence
   crashes the translation. Scout can deploy new fields independently
   — bridge.py handles both old and new spines without updates.
   (DEC-PM-005)

7. **Forward compatibility — bridge.py ignores unmapped fields.**
   A new Scout section that bridge.py has no mapping for passes
   silently. No crash, no warning. When PM decides the field should
   become operational, PM scopes a bridge.py update to add the
   mapping. Scout deploys first, bridge.py catches up on its own
   schedule. (DEC-PM-005)

8. **Scout changes never assume bridge.py awareness.** Scout's
   extraction prompt produces whatever the interview warrants.
   Scout does not shape its YAML to match MTN's operating format.
   Scout's only contract is this file — it emits the fields defined
   here, in the shapes defined here. (DEC-PM-005)

This file is the contract. Code follows the contract.
The contract does not follow the code.

---

*Authoritative copy lives in the PM project. Copied to both
repos after every update.*
