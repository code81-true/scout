# KNOWN_ISSUES.md — What Is Broken, Parked, or Watched

This document is the honest inventory. It lists what
does not work, what was deferred on purpose, and what
the models do that we have learned to catch rather than
prevent.

If a new issue is discovered, add it here before you
ship the session that hit it. If an issue is fixed,
remove it — do not leave it lingering with a crossed-out
note.

Three sections:
1. **Active bugs** — things that are wrong and should be
   fixed, but are not blocking ship.
2. **Parked features** — things that are deliberately
   not built yet. Each has a target release.
3. **Known model behaviour issues** — things Claude does
   that we handle at the plumbing layer rather than by
   fighting the model.

---

## 1. Active bugs

*(Sprint 2 closed A08, A10, A11, A12 on 2026-04-22 — entries removed.
The Sprint 2 commit sits on master; Pope holds the deploy gate.)*

### VPS system restart pending
The VPS reports "System restart required" — 23 pending updates as
of 2026-05-01. Not urgent. Restart will briefly take Scout offline,
so schedule during a quiet maintenance window. No code change
needed; this is operational hygiene only.

---

## 2. Parked features (deliberate deferrals)

Each entry names the target release. These are not bugs.
They are things we have chosen not to build yet.

### Prompt caching (broader scope) — v1.1
System-prompt caching is already implemented (see
DEC-SCOUT-011). Broader caching — per-session strategies,
caching across derivative calls — is a v1.1 item.

### Prompt compression — v1.1
A 34% token reduction has been identified via analysis.
The full analysis is in STATUS.md. Not yet implemented.
Targeted at v1.1.

### Sliding context window — v1.2
For sessions over 90 minutes, a sliding window
approach may be needed to keep prompt size manageable.
Targeted at v1.2. Note: any such window must preserve
Scout's ability to detect long-range contradictions
(DEC-SCOUT-001).

### Mobile responsive full redesign — v1.1
A triage CSS fix for the 480px breakpoint is in place
(see commit for "mobile triage"). A full mobile redesign
— typography scale, input treatment, generation screen
layout — is targeted at v1.1.

### Email invitation system — Phase 2
Sending keys via a real invitation flow (as opposed to
handing them out by hand) is a Phase 2 scope item.

### Admin dashboard authentication — Phase 2
Per DEC-SCOUT-010. Security-through-obscurity is
acceptable for single-operator beta only.

### File deletion after download — v2.0 commercial launch
Automatic deletion of spine/portrait/Meridian files from
`/home/scout/spines/` after confirmed download is
targeted at v2.0 commercial launch. For now, files are
retained on the VPS post-delivery.

### Background generation during settling — parked
Per DEC-SCOUT-012.

### Six delivery edge cases — shipped 2026-04-22
*(Sprint 2. A token-not-found distinct from expired, D
returning-user partial-download cue, E file-missing
Scout-register page, F already-collected re-request
Scout-register page, G rate-limit-on-verify muted
surface, H token case-insensitive lookup. Tests in
tests/test_collect.py. Committed, awaiting deploy.)*

### "Keep your Meridian safe" message after download — shipped 2026-04-22
*(Sprint 2. Two-line closed block in collect.html:
primary line retained, secondary muted line below with
the safe-keeping copy. Rendered in both the `closed`
status branch and the valid-with-JS-fade-in branch.)*

### Scout → MTN handshake button — item 19
A one-click handshake that moves a spine from Scout to
MyTrueNorth is designed but not built. Current bridge is
manual (see ARCHITECTURE.md).

### Waitlist capture for organic discovery — Phase 2
A waitlist form for people arriving at Scout without a
key is a Phase 2 item. Not yet built.

### Generation time estimate in waiting screen — item 06, parked
Showing a time estimate during the generation wait is
parked. The estimate was too variable to be honest, and
dishonesty in a waiting screen violates SOUL.md §6.

---

## 3. Known model behaviour issues

These are things the Anthropic models occasionally do
that we handle defensively. They are documented here so
that we do not re-discover them each time and so that
the plumbing stays in place even when the model changes.

### Scout occasionally produces YAML in production
Despite Hard Rules and DEC-SCOUT-005, Scout will
sometimes emit a YAML fragment mid-conversation. The
`yamlDropped` filter on the frontend catches these and
silently discards them before they reach the person.
The filter is not optional — do not remove it just
because prompts have improved.

### Meridian writer occasionally produces fewer than 5 paragraphs
The Meridian prompt asks for five declarative
statements. Occasionally Opus returns four or three.
The server pads the output with empty strings so
downstream rendering does not fail. This is a patch,
not a fix — the prompt itself may need tightening.

### YAML validation fails on long sessions
On sessions with 200+ exchanges, YAML validation can
fail because of truncation artefacts at the tail. A
line-by-line recovery path catches most cases but the
resulting YAML is thinner than it would be for a
shorter session. If long sessions become common, this
is worth a real fix.

### Session_complete trigger may not fire on alternate phrasing
The session close is detected by the phrase "Give me a
moment" appearing inside a 40-message window. If Scout
closes with different phrasing, the trigger does not
fire. A 90-second fallback timer catches the case and
still moves the session forward, so no session is ever
stranded — but the primary trigger is imperfect.

---

## How to use this document

Before you ship a change that touches generation,
delivery, the waiting screen, the prompt, or the state
machine, read the relevant section of this file. Many
past bugs rhyme with current temptations.

When an issue here is closed, delete the entry. This
file is only useful if it reflects current reality.
