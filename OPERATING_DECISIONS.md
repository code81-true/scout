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

---

### DEC-PM-002 — Beta recruitment held pending depth fix verification
**Date:** 22 April 2026
**Trigger:** Post-Sprint-1 production session showed Scout
rushing interviews — shallow threading, generic depth signals
clearing the bar, closing sequence firing before shadows opened.
Portrait and Meridian mediocre. User experience degraded from
pre-Sprint-1 baseline.

**Decision:** No new Scout keys issued until a post-fix
production session confirms interview depth has been restored.
The warm network is finite and non-renewable — one bad
experience per person is all you get.

**Status:** ACTIVE. Three depth fixes deployed (turn-by-turn
threading Hard Rule, L6/L7 depth signal tightening, closing
sequence gate). Awaiting verification session.

**Lift condition:** A production session where the user reports
the interview went deep, the portrait clears the SOUL.md bar
("I've never heard it said like that"), and the Meridian does
not flag insufficient depth in its own closing line.

---

### DEC-SHARED-001 — Sprint specs include Invariants section
**Date:** 22 April 2026
**Trigger:** Sprint 1 added listening targets to Scout's prompt
without specifying that interview depth, threading quality, and
depth-before-closing must not degrade. The model optimised for
breadth of extraction over depth of pursuit. No one noticed
because the spec didn't say depth had to hold.

**Decision:** Every sprint or session brief that modifies a
system prompt (Scout's prompt.py or MTN's system.txt) must
include an "Invariants" section listing the behaviours that
must not degrade. The developer checks these post-build. The
PM checks post-deploy via a production session or structured
verification.

**Applies to:** Both repos. Any prompt-modifying work.

---

### DEC-SHARED-002 — Verification tests production code path
**Date:** 22 April 2026
**Trigger:** Sprint 1 added Hard Rule C ("never generate YAML
in conversation") to SYSTEM_PROMPT. The YAML extraction function
generate_yaml_sections() used SYSTEM_PROMPT as its system prompt.
Model obeyed → refused to generate YAML → empty spine → empty
portrait. The STOP 3 verification tested an isolated Sonnet call
that bypassed SYSTEM_PROMPT entirely. The bug was latent until
first production session.

**Decision:** Verification of any code change must exercise the
actual function the server calls, not an isolated API call that
bypasses the production code path. "Isolated call works" ≠
"production path works." The verification bar is: the exact
code path the server uses, with the exact prompts it sends,
produces the expected output.

**Applies to:** Both repos. Any change that affects API call
behaviour.

---

### DEC-SHARED-003 — Prompt changes are transformative, not additive
**Date:** 22 April 2026
**Trigger:** Sprint 1 added four new listening targets to
Scout's prompt. The additions were individually correct. But
collectively they changed how the model weighed every existing
instruction — shifting optimisation from "go deep on fewer
things" to "cover more things adequately." This was not
anticipated because the additions were treated as incremental.

**Decision:** Every instruction added to a prompt changes how
the model weighs every existing instruction. No prompt change
is purely additive. When reviewing a prompt modification, ask:
"Does this change make the model busier? If so, which existing
behaviours might lose weight?" Re-examine progression
thresholds, depth signals, and pacing gates whenever extraction
targets or listening instructions are added.

**Applies to:** Both repos. Any prompt modification.

---

*Update this file when a cross-cutting decision is made.
Copy to both repos after every update. The PM project holds
the authoritative copy.*
