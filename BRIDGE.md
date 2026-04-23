# BRIDGE.md — MTN Session: Pydantic Schema Correction
## 23 April 2026

**What this is:** Targeted briefing for the MTN CC session that
corrects the Pydantic models. Read before starting any work.

---

## What happened

The SCHEMA_CONTRACTS.md that MTN Session 7 built to was wrong.
It was built from a conversation report, not from engine.py.
Session 7 moved the Pydantic models from mostly-correct
(Session 6) to incorrect (matching the wrong contract).

The Scout developer has now verified the actual field names
directly from engine.py on the VPS. The corrected schema is
in the updated SCHEMA_CONTRACTS.md in this repo.

## What Session 6 had (original models)

```python
class Heuristic(BaseModel):
    id: str
    statement: str
    confidence: Literal["high", "medium", "low"]
    self_type: Literal["present", "cast"]
```

## What Session 7 changed them to (wrong — built to bad contract)

```python
class Heuristic(BaseModel):
    domain: str
    rule: str
    confidence: Literal["stated", "inferred"]
    source_layer: str | None = None
```

## What engine.py actually produces (correct — verified on VPS)

```yaml
heuristics:
  - id: str
    statement: str
    evidence: str
    confidence: "high" | "medium" | "low"
    self_type: "present" | "cast"
    invocation_note: str

failure_modes:
  - pattern: str
    trigger: str | null
    tells: str | null
    interrupts: str | null       # PLURAL
    north_watch: str | null

context_triggers:
  - id: str
    condition: str
    deviation: str
    north_watch: str | null

north_instructions:
  sensitive_areas:               # conditional
    - hat: str
      note: str
```

## What this session must do

1. Revert the Heuristic model to Session 6 field names (id,
   statement, confidence high/medium/low, self_type) and ADD
   two fields Session 6 was missing: `evidence: str` and
   `invocation_note: str`
2. Revert FailureMode: change `interrupt` back to `interrupts`
   (plural)
3. Revert ContextTrigger: change `situation` back to
   `condition`, change `response` back to `deviation`, ADD
   `id: str`
4. SensitiveArea is correct — no changes needed
5. Update all tests to match the corrected field names
6. Check C2 and C3 helpers — `_build_standing_instructions`
   reads `north_watch` (unchanged) but verify no helper
   references any renamed field
7. Confirm pope.yaml still loads (backwards compat)
8. Confirm all tests pass
9. Update SESSION_REPORT.md

## What this session must NOT do

- Do not deploy. Pope holds the deploy gate.
- Do not change C2 or C3 logic
- Do not add new features

## Decisions in effect

- DEC-PM-001: Models must match SCHEMA_CONTRACTS.md, which
  is now verified against engine.py source code
- DEC-SHARED-002: Test using production code path — load a
  YAML fixture that matches Scout's actual output format

## Deploy state

- Scout VPS: fully deployed
- MTN VPS: running Session 4 code. Sessions 5, 6, 7, and
  this correction will deploy together when Pope pulls.
- After MTN deploys: Pope bridges a real post-Sprint-1 spine
  from this weekend's production sessions

---

*This BRIDGE.md is disposable. It serves this session only.*
