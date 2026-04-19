# DECISIONS.md — Scout Design Decisions

This is the running log of non-obvious design decisions
made during Scout's development. Each entry captures what
was chosen, when, and — most importantly — why.

Use this document when you are tempted to reverse a
decision. Read the reasoning first. If the reasoning
still holds, the decision still holds. If the reasoning
no longer applies, supersede the entry rather than
silently changing behaviour.

Format:
```
DEC-SCOUT-NNN | Title | Date | Decision | Reasoning | Status
```

---

### DEC-SCOUT-001 | Full transcript on every API call

**Date:** 2026-04-06
**Decision:** Every call to the Anthropic API includes the
complete session transcript. No summarisation, no rolling
window, no compression.
**Reasoning:** Scout's job is to notice contradictions,
repeated themes, and the thing the person circled around
at minute 40 and returned to at minute 90. Summarisation
destroys exactly the signal Scout is paid to detect. The
token cost of a full transcript is the price of the
product working.
**Status:** Active.

---

### DEC-SCOUT-002 | SQLite over in-memory sessions

**Date:** 2026-04-15
**Decision:** Session state and transcripts are persisted
to SQLite after each turn rather than held only in
process memory.
**Reasoning:** David's session proved transcripts must
survive process restarts. An in-memory session that
vanishes when Gunicorn reloads is a session that asked a
person for two hours and then lost them. SQLite on disk,
written every turn, is the minimum acceptable durability.
**Status:** Active.

---

### DEC-SCOUT-003 | Server owns session state

**Date:** 2026-04-15
**Decision:** Session state lives on the server. Exactly
four states: `interviewing → closing → generating →
delivered`. The frontend reads state from the server and
does not maintain its own.
**Reasoning:** An earlier design used three boolean flags
synchronised between server and frontend over SSE. Any
desynchronisation cascaded — a stuck boolean in one place
caused failed transitions in another. Replacing the three
flags with a single server-owned enum eliminated a class
of failures entirely. The frontend is now a view, not a
state machine.
**Status:** Active.

---

### DEC-SCOUT-004 | All sessions anonymous

**Date:** 2026-04-16
**Decision:** Pseudonym detection is removed. Every
session is labelled Anonymous in outputs and admin views.
**Reasoning:** Two real session failures exposed the
problem. One person typed "it was busy i was distracted"
and the detector pulled a name-shaped fragment. Another
gave a casual answer that was misread as self-naming.
The detector was wrong often enough that being right the
remaining times did not justify the harm. Anonymous by
default is the only safe register.
**Status:** Active.

---

### DEC-SCOUT-005 | Scout never produces YAML in conversation

**Date:** 2026-04-16
**Decision:** The YAML parsing pass section is removed
from `prompt.py`. Scout produces conversation only. YAML
extraction is a separate post-session pass with its own
prompt.
**Reasoning:** The old prompt contained both Hard Rule C
("produce only one question per turn, never YAML") and a
parsing-pass section instructing Scout to produce YAML on
cue. Given contradictory instructions, Scout chose wrong.
Separating the two concerns — one prompt for the
interview, another for extraction — removed the conflict
entirely.
**Status:** Active.

---

### DEC-SCOUT-006 | Settling conversation after interview close

**Date:** 2026-04-09
**Decision:** After the interview ends and before
artifact generation, a brief settling conversation returns
the person to the surface.
**Reasoning:** Boss's session. He gave two honest hours,
reached a depth that mattered, and was then dropped into
"we're generating your portrait." He was left emotionally
open with no landing. The settling conversation is the
return-to-surface commitment from SOUL.md §Planes made
literal in the product flow.
**Status:** Active.

---

### DEC-SCOUT-007 | Meridian replaces Constitution

**Date:** 2026-04-15
**Decision:** The five-line declarative output is named
Meridian in all user-facing copy. The internal file is
still `<session>_constitution.txt` for now.
**Reasoning:** "Constitution" read as a legal document —
the wrong register for what is effectively a compass
reading. "Meridian" connects to the globe watermark on
the PDF and to the broader navigation metaphor that runs
through Scout and MyTrueNorth. The name now matches the
object.
**Status:** Active.

---

### DEC-SCOUT-008 | PDF delivery only

**Date:** 2026-04-09
**Decision:** Portrait and Meridian are delivered as PDFs.
No plain text file is sent alongside.
**Reasoning:** The document should feel worth keeping.
A `.txt` file is a draft; a typeset PDF is an artifact.
A person who has given two hours should receive
something they will print, save, or read from again in
five years — not something that looks like an export.
**Status:** Active.

---

### DEC-SCOUT-009 | ReportLab for Meridian, WeasyPrint for Portrait

**Date:** 2026-04-15
**Decision:** The Meridian PDF is rendered with ReportLab.
The Portrait PDF is rendered with WeasyPrint from an
HTML/CSS template.
**Reasoning:** The two documents have different needs.
The Meridian is a short, layout-precise object with a
globe watermark — ReportLab's drawing primitives give
exact control. The Portrait is long-form prose with
typographic detail — an HTML/CSS template rendered via
WeasyPrint is the right fit and keeps the design
editable in the tools designers actually use.
**Status:** Active.

---

### DEC-SCOUT-010 | Admin dashboard at unpredictable URL, no auth

**Date:** 2026-04-19
**Decision:** The Phase 1 admin dashboard is served at an
unpredictable URL with no authentication layer.
**Reasoning:** Security through obscurity is acceptable
for a single-operator beta with no public discovery path.
Adding real auth in Phase 1 is engineering effort spent
on a problem that does not yet exist. Auth is committed
to Phase 2 before the operator count exceeds one.
**Status:** Active (Phase 1 only).

---

### DEC-SCOUT-011 | Prompt caching for Scout system prompt

**Date:** 2026-04-11
**Decision:** Anthropic prompt caching is implemented for
the Scout system prompt. The transcript is not cached —
it changes every turn.
**Reasoning:** Scout uses one API key shared across all
users, which means the cached system prompt is shared
and efficient across sessions — a real win. Caching the
transcript is not attempted because the transcript grows
with every turn and invalidates immediately; the cost of
a cache miss on a changing body is higher than no cache
at all.
**Status:** Active (system prompt only). Note: broader
caching scope (e.g. per-session caching strategies)
remains a v1.1 item.

---

### DEC-SCOUT-012 | Background generation during settling parked

**Date:** 2026-04
**Decision:** Starting artifact generation in a background
thread during the settling conversation is parked. Not
rejected, not scheduled.
**Reasoning:** Two problems. First, the settling
conversation may surface late material — a closing
sentence that the Chronicler should have had — and
running generation in parallel risks producing artifacts
that do not include it. Second, threaded background work
makes silent failures more likely in exactly the place
Scout must be loudest (SOUL.md §6). The correct fix is
not parallelism; it is making generation fast enough
that serial execution is acceptable.
**Status:** Parked.

---

### DEC-SCOUT-013 | 12-character mixed-case alphanumeric key format

**Date:** 2026-04-19
**Decision:** New keys are 12 characters, mixed case,
alphanumeric. Keys issued under the old format remain
valid.
**Reasoning:** Longer mixed-case keys are harder to
guess, and they look more professional on the card a
person receives. Invalidating old keys would have broken
sessions already promised, which was not an acceptable
cost for a format refresh.
**Status:** Active.

---

### DEC-SCOUT-014 | Session row retained after delivery

**Date:** 2026-04-19
**Decision:** After a session is delivered, the
`transcripts` rows for that session are deleted. The
`sessions` row is retained permanently.
**Reasoning:** The transcript is the person's private
material — it is deleted on delivery as a custody
commitment. The session row holds only metadata (id,
state, timestamps, outcome) and is required for the
admin dashboard to show a true history of what Scout has
done. Deleting the session row would leave the operator
blind to their own system.
**Status:** Active.
