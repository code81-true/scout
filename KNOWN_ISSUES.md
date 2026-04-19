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

### A10 — Portrait PDF cover: compass north needle clipped
The compass north needle on the portrait cover PDF is
slightly clipped at the top. Visual only; layout
otherwise correct. Needs the cover canvas or SVG
viewport widened by a few points.

### A12 — Compass animation shifts position on message length
During the generation waiting screen, the rotating
messages change length. When they do, the compass
animation's horizontal position shifts with them. The
container needs a fixed width so the compass stays
centred while the text cycles.

### A08 — Portrait paragraphs break across pages in WeasyPrint
Occasionally a portrait paragraph is split across a page
boundary mid-paragraph rather than breaking at the
paragraph boundary. Needs `page-break-inside: avoid` on
paragraph elements in the WeasyPrint template, or
equivalent.

### A11 — Meridian body font too small
The auto-fit routine that sizes the Meridian body text
scales too conservatively — even short Meridians come
out smaller than the target register. Tune the auto-fit
bounds upward, or set a minimum body size.

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

### Six delivery edge cases — not implemented (item 13)
Six delivery edge cases have been designed on paper but
are not yet implemented. Review before the next batch of
public sessions.

### "Keep your Meridian safe" message after download — item 14
A post-download message reminding the person to store
their Meridian somewhere safe has been designed but not
shipped.

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
