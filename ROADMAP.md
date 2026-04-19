# ROADMAP.md — Scout Release Plan

This is the forward plan. It runs from the present
(v1.0 — Stabilise) through the v3.0 Planes Architecture
vision described in SOUL.md.

Each version has a theme. Items within a version are
tagged **complete**, **in progress**, or **parked**.

This document is pruned, not appended. When a version
ships, move the retained items to the next version and
delete the shipped ones. Do not keep stale entries.

---

## v1.0 — Stabilise (CURRENT)

The objective of v1.0 is a Scout that can be sat in
front of a real person without a support rope. Everything
in this version is about correctness, safety, and
finish.

- **complete** — All critical fixes (see DECISIONS.md
  001–009)
- **complete** — All security items: rate limiting on
  /auth, Flask secret key from env, robots.txt blocking
  search indexing, .env and access/ excluded from git
- **complete** — PDF generation for Portrait (WeasyPrint)
  and Meridian (ReportLab)
- **complete** — Settling conversation between interview
  close and artifact generation (DEC-SCOUT-006)
- **complete** — Mobile triage: responsive CSS at 480px
  breakpoint for all states
- **complete** — Admin dashboard (committed, not yet
  deployed — requires pre-deploy checklist run)
- **complete** — New key format: 12-character
  mixed-case alphanumeric (DEC-SCOUT-013)

---

## v1.1 — Post first sessions

The objective of v1.1 is to tune Scout based on what the
first batch of real sessions teaches us. Nothing
structural changes.

- Prompt caching — broader scope (per-session
  strategies, caching across derivative calls; system
  prompt caching is already done in v1.0)
- Prompt compression — 34% token reduction identified
  in analysis; implement
- Chronicler review — audit portrait quality against
  the Boss/David bar (SOUL.md §sessions that set the
  standard)
- Mobile full redesign — typography, input treatment,
  generation screen layout
- Six delivery edge cases — design is done, implement
- "Keep your Meridian safe" post-download message
- Admin dashboard authentication — replace Phase 1
  security-through-obscurity
- Waitlist capture for organic discovery
- Scout → MTN handshake button — replace the manual
  YAML copy
- Generation time estimate in waiting screen —
  reconsider only if an honest estimate becomes possible
  (SOUL.md §6)

---

## v1.2 — Stability and scale

The objective of v1.2 is to make Scout production-grade
under load and across longer time horizons.

- **complete** — Gunicorn workers (shipped in v1.0)
- Structured logging — JSON logs with session id,
  state, model, latency
- Cost tracking per session — Anthropic usage captured
  and attributed per session
- Sliding context window — for sessions over 90
  minutes, without breaking DEC-SCOUT-001
- Spine review cycle — a 90-day prompt to revisit the
  spine and update what has changed
- Partial session warning — detect and surface sessions
  that did not reach a clean close

---

## v2.0 — Commercial launch

The objective of v2.0 is a Scout that can take payment
and a MyTrueNorth that can run as a paid subscription.
Everything here has legal, billing, or data-protection
implications. Do not build any of this ahead of legal
sign-off.

- User accounts — for MTN subscribers, not Scout sessions
- Encrypted spine storage — for accounts that opt in to
  server-side custody
- MyTrueNorth subscription billing
- GDPR compliance — DPA, data map, deletion workflow
- Legal review — terms, privacy, consent copy for the
  session
- Scout → MTN auto-write — replace the handshake button
  with a silent, authorised write
- File deletion after download — automatic deletion of
  spine/portrait/Meridian from
  `/home/scout/spines/` on confirmed download
- Stripe donation page — for the donation-optional path

---

## v3.0 — Scout Deep (Planes Architecture)

The long vision. The Planes Architecture (SOUL.md) moves
Scout from a single two-hour session to a deeper
structure capable of traversing all nine planes with
the right pacing.

Nothing in v3.0 is scoped yet. These are the
commitments.

- Nine-plane interview model — environment → body →
  breath/senses → mind → memory → thoughts → emotions →
  ego → true self (and the return)
- Multi-session arc — the interview spans multiple
  sittings, not one
- Multi-layer spine schema — the YAML encodes depth,
  not just breadth
- Async interview over 7 days — the session does not
  have to be a single sitting
- Voice input — for the layers where typing gets in the
  way of the answer

---

## Aesthetics register

Design and polish items tracked separately from
functional bugs. Tags A01–A12.

- **A01** — "By invitation only" colophon needs more
  shimmer. Currently too muted.
- **A02** — "Read this first" link needs more shine and
  attention. Gold/rose gold oscillation animation added
  but copy still flat.
- **A03** — Reveal button name needs a decision. Current
  name "Reveal" is functional but not evocative.
  Candidates: Begin, Enter, I am ready, Open.
- **A04** — Generation wait screen: rotating messages
  timing — currently static single message. May need
  tuning after real user feedback.
- **A05** — Mobile notice on guide page — temporary text
  notice until full responsive redesign.
- **A06** — Portrait HTML screen and Portrait PDF —
  review for consistency of register now that both
  exist.
- **A07** — Portrait PDF and Meridian PDF colophon —
  "Scout · date" reads as a product signature. Consider
  something warmer.
- **A08** — Portrait paragraphs occasionally break
  across pages in WeasyPrint. Needs
  `page-break-inside: avoid` or equivalent.
- **A09** — Portrait PDF cover: pseudonym positioning
  relative to compass watermark needs refinement on A4
  print. Looks correct on screen but prints slightly
  high.
- **A10** — Portrait PDF cover: compass north needle
  slightly clipped at top.
- **A11** — Meridian body font too small — auto-fit
  scales too conservatively.
- **A12** — Compass animation shifts position when
  rotating messages change length. Needs fixed-width
  container.
