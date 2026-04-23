# Scout — Project Status

Last updated: 2026-04-23 (all commits deployed to VPS; doc corrections; DEC-SCOUT-018; SCHEMA_CONTRACTS.md)

---

## Current State

Scout is a single-session AI interview engine that guides one person through seven layers of self-examination and produces two outputs: a structured spine.yaml (personal constitution for the MyTrueNorth system) and a prose portrait written by the Chronicler. The system runs as a Flask web application with a landing page, single-use key authentication, streaming conversation UI, compass-themed portrait display page, and WeasyPrint PDF portrait generation. Deployed to VPS at scout.regtool.org. The backend supports per-key session isolation, session resumption after disconnection, test mode with Haiku for logistics testing, transcript persistence to disk, and a settling conversation before generation begins. [MODIFIED 2026-04-09: updated to reflect VPS deployment, settling conversation, and PDF generation]

---

## What Is Complete

### Brain

- **Scout system prompt** (`scout/prompt.py`) — ~1,570 lines across 8 sections: Identity & Disposition, Hard Rules (10 rules), How Scout Listens, Pre-Layer Arrival (5 register-dependent opening variations, settling exchange, "Ready?" gate, thin-answer rule), Seven Layers (Roles, Work, People, Body, Beliefs, Shadows, Long Game), The Closing (closing acknowledgement, final questions, closing conversation with 6-case decision tree: A natural close, B depth-reached stop, C too-early stop, D stop-during-closing, E explicit request with depth, F explicit request too early), Parsing Pass (full spine.yaml schema, 7 parsing rules), Safety (11 hard constraints). [MODIFIED 2026-04-09: renamed settling→closing conversation, added edge case decision tree with Cases A–F, Case B uses pseudonym]
- **Chronicler prompt** (`scout/chronicler.py`) — Portrait writing prompt with two required moments: Half-Seen Shadow and Unacknowledged Greatness. Includes [SHADOW]/[SURPRISE] markup instructions, length guidance (600–1800 words), advice prohibition in final third, and final-name instruction (pseudonym in last sentence only). [MODIFIED 2026-04-09: added final-name instruction]
- **Test prompt** (`scout/test_prompt.py`) — Minimal 3-exchange interview for logistics testing. Includes settling conversation with fixed closing line for pipeline testing. [MODIFIED 2026-04-09: added settling instruction]

### Backend

- `scout/engine.py` — Context window engine. Full transcript on every API call. Three model constants: MODEL (Sonnet), OPUS_MODEL (Opus), TEST_MODEL (Haiku). Functions: create_client(), send_message(), send_message_stream() (with optional prompt/model override), generate_portrait() (Opus, 10k tokens), generate_yaml_sections() (4 sequential calls + YAML stitching + PyYAML validation). [2026-04-06]
- `scout/session.py` — In-memory transcript holder. [2026-04-06]
- `app.py` — Flask application with per-key session isolation. Routes: GET / (landing), POST /auth (key auth with resume detection), POST /burn (key expiry + transcript deletion + session cleanup), POST /chat (streaming SSE with dual completion: session_complete + settling_complete), POST /generate (YAML + portrait saved to SPINE_DIR), GET /portrait (serves from disk), GET /download-portrait (WeasyPrint PDF generation), POST /test-generate (dev route). [MODIFIED 2026-04-09: added settling_complete, download-portrait, portrait from disk]
- `keys_generate.py` — Key generator in project root. Production keys (10-char) and TEST- keys (6-char). [2026-04-07]
- `access/keys.txt` — Key store. VPS only, never in git. [2026-04-06]
- `run_session.py` — Terminal entry point for brain-only mode (PR 1). [2026-04-06]

### Frontend

- `templates/index.html` — Three-state SPA: [MODIFIED 2026-04-09: added settling state, fenced YAML filter, compass animation, three download buttons]
  - **State 1 (Landing)**: Dark background, Scout wordmark with forged bronze gradient, guide link, key console with age notice, breathing animations, vignette pulse, input focus fade, black fade transition on auth.
  - **State 2 (Guide)**: "Technically" and "With truth" sections. Session resumption, mental health, relational complexity notices. Bottom nav with scroll-top and return buttons.
  - **State 3 (Conversation)**: Streaming typewriter UI (28ms base, punctuation pauses). Scout messages in Cormorant Garant italic gold, user messages in system sans-serif. Fenced-block YAML filter strips ```yaml...``` blocks and --- separators silently. session_complete unlocks for settling conversation. settling_complete locks permanently and triggers generation. Compass animation during generation (searching → settling → settled phases). Three download buttons: Download Portrait (gold, PDF), View Portrait (secondary), Download Spine (understated, YAML blob).
- `templates/portrait.html` — Compass portrait display page served from disk. Marker-based [SHADOW]/[SURPRISE] passage detection. [2026-04-07]
- `templates/portrait_pdf.html` — WeasyPrint A4 PDF template. Ivory #FDFAF5 edge-to-edge, cover page with centred compass + pseudonym, body with gold hairline rules and paragraph break protection, colophon centred on final page. [MODIFIED 2026-04-09: fixed cover centering, edge-to-edge background, paragraph breaks, colophon centering]

### Infrastructure

- **Deployed** to VPS at scout.regtool.org (178.104.57.52, Hetzner Ubuntu 24.04). [MODIFIED 2026-04-09: updated from "not yet deployed"]
- Gunicorn 25.3.0 installed, 3 workers, replacing Flask dev server. [2026-04-09]
- nginx reverse proxy with SSL via Let's Encrypt (expires 2026-07-05).
- systemd service at /etc/systemd/system/scout.service.
- Server-side filesystem sessions via flask-session.
- Transcript persistence to sessions/transcripts/.
- Per-key session isolation — multiple concurrent users supported.
- /health endpoint for uptime monitoring — returns {"status": "ok"}. [2026-04-09]

---

## Design Decisions

1. **Full transcript on every API call** — no summarisation, non-negotiable for quality. [2026-04-06]
2. **Single context window architecture** — no RAG, no vector store. [2026-04-06]
3. **Client-side typewriter effect** — tokens buffered client-side, drained with human-like timing. [2026-04-06]
4. **Four sequential YAML generation calls** — schema too large for single call. [2026-04-06]
5. **Portrait by Opus, interview by Sonnet** — literary quality vs cost efficiency. [2026-04-06]
6. **Single-use key system** — no accounts, one session, burned on completion. [2026-04-06]
7. **Key lifecycle: unused → active → used** — active + no transcript = rejected. [2026-04-06]
8. **Transcript saved to disk after every exchange** — enables resume after disconnect. [2026-04-07]
9. **Session completion detected server-side** — "Give me a moment" + 40 messages (production), YAML detection (test). [MODIFIED 2026-04-09: added settling_complete as second trigger]
10. **Test mode via key prefix** — TEST- keys route to Haiku with minimal prompt. [2026-04-07]
11. **YAML stitching with validation** — strips fencing, deduplicates root keys, validates with PyYAML. [2026-04-06]
12. **Exit warning after burn** — beforeunload activates after key burned, deactivates after download. [2026-04-07]
13. **Resume acknowledgement injected as system note** — warm return message referencing last topic. [2026-04-07]
14. **Per-key session isolation** — _sessions dict + _started_keys set, cleaned up on burn. [2026-04-07]
15. **Marker-based passage detection** — [SHADOW]/[SURPRISE] markers parsed structurally, not by regex. [2026-04-07]
16. **Surprise typography: weight over style** — 400 weight + 19.5px, shadow uses italic. [2026-04-07]
17. **Adults-only with clarification before rejection** — one clarifying question before stopping. [2026-04-07]
18. **Legal notices on all outputs** — legal_note in spine.yaml meta, "For adults only" on portrait colophon. [2026-04-07]
19. **Mental health pause not burn** — key stays active, person can return. Past history does not trigger. [2026-04-07]
20. **Sexual complexity acknowledged not explored** — redirect to human specialist, no moralising. [2026-04-07]
21. **Closing conversation (renamed from settling) with 6-case decision tree** — Cases A–F handle every session ending: natural close, depth-reached stop (uses pseudonym), too-early stop (key burned), stop-during-closing (generate immediately), explicit request with depth, explicit request too early. Depth detection via _has_depth() (8+ post-arrival exchanges + layer keyword). session_depth boolean in SSE stream. /generate returns 422 insufficient_depth if too shallow. 10-minute fallback timer if settling_complete never fires. Too-early message screen with gold text and close link. [SUPERSEDED 2026-04-09: replaces "settling conversation before generation"]
22. **Fenced-block YAML filter** — strips only ```yaml...``` blocks and standalone --- separators, resumes rendering after. [2026-04-09]
23. **Portrait served from disk not sessionStorage** — survives tab close and mobile browser. [2026-04-09]
24. **PDF generation via WeasyPrint** — A4, ivory background, compass cover, paragraph break protection. [2026-04-09]

---

## Changes Based on Review

1. **max_tokens 300 → 1500 → 5000** — Pope increased token limit twice. [2026-04-06]
2. **Prompt rewrite** — Pope replaced initial 93-line prompt with 1,152-line comprehensive prompt. [2026-04-06]
3. **Removed /reset route** — single-session tool should not have reset. [2026-04-06]
4. **"Cormorant Garamond" → "Cormorant Garant"** — typeface name correction. [2026-04-06]
5. **generate_portrait() max_tokens 8000 → 10000** [2026-04-06]
6. **generate_yaml_sections() max_tokens MAX_TOKENS → 4000** [2026-04-06]
7. **GET /portrait → POST /portrait** — prevents sensitive data in URL. [SUPERSEDED 2026-04-09: /portrait changed back to GET, serves from disk]
8. **Active key resume security tightening** — active + no transcript = reject. [2026-04-07]
9. **Landing page visual adjustments** — breathing animations, gold focus border. [2026-04-07]
10. **Pattern matching → marker-based passage detection** [2026-04-07]
11. **Surprise passage typography** — 400 weight, 19.5px. [2026-04-07]
12. **Constraint 9 — minor detection** [2026-04-07]
13. **Age notice on landing page** [2026-04-07]
14. **Legal footer on outputs** [2026-04-07]
15. **Prompt additions: layer transitions, reflection discipline, closing acknowledgement** [2026-04-07]
16. **Constraint 10 — mental health boundary** [2026-04-07]
17. **Constraint 11 — sexual and relational complexity** [2026-04-07]
18. **Guide page mental health and relational notices** [2026-04-07]
19. **Guide page — time commitment, guide link text, MyTrueNorth paragraph** [2026-04-07]
20. **Five UI animations** — vignette pulse, wordmark hover, focus fade, black transition, generating messages. [2026-04-07]
21. **Guide page rewrite** — pristine copy, conversation framing, "When you are ready — enter your key." [2026-04-07]
22. **CSS/layout audit fixes and conversation restyling** — colophon overlap, contrast fixes, guide nav, Scout/user message restyling, YAML block rendering. [2026-04-08]
23. **Two new Hard Rules + five contradiction fixes** — Rule A (no fabrication), Rule B (not the subject), Constraint 7 rewritten, reflection example fixed, Layer 2 opening removed, closing duplication clarified. [2026-04-08]
24. **Portrait pipeline: save to disk, serve via URL** — fixes mobile and tab-close loss. [2026-04-09]
25. **WeasyPrint added** — weasyprint>=68.0 in requirements.txt. [2026-04-09]
26. **WeasyPrint PDF portrait route, chronicler final name, guide copy** — /download-portrait route, pseudonym in final sentence, guide mentions portrait + spine. [2026-04-09]
27. **sessionEnded flag** — prevents triggerGenerate interruption. [2026-04-09]
28. **Settling conversation, YAML removed from screen, settling_complete trigger** [2026-04-09]
29. **Four production bug fixes** — fenced YAML filter, compass alignment, portrait button fix. [2026-04-09]
30. **PDF layout fixes** — cover centred, ivory edge-to-edge, paragraph breaks, colophon centred. [2026-04-09]
31. **Strip portrait markdown headers** — server-side stripping of # lines at save point. [2026-04-09]
32. **WeasyPrint paragraph break fix** — break-inside: avoid + page-break-inside: avoid on div wrappers. [2026-04-09]
33. **SSE generator flask_session write removed** — flask_session["session_depth"] = depth was inside streaming generator, caused RuntimeError under Gunicorn. Removed — depth already sent via SSE payload and computed independently by /generate route. [2026-04-09]
34. **robots.txt + noindex meta** — static/robots.txt blocks all crawlers, /robots.txt route serves it, noindex nofollow meta tag on index.html. Scout is invitation-only — no search engine indexing. [2026-04-10]
35. **Three surgical fixes** — Flask secret key from FLASK_SECRET_KEY env var with dev fallback. Case D closing line: removed "Of course." (banned phrase). Chronicler "Fix 3" label renamed to "The final exchange". [2026-04-10]
36. **No markdown in conversation + extended fence filter** — New Hard Rule: Scout must never use backtick fences, pipes, tables, bullets, or headers in conversational responses. TypeWriter filter extended to catch all ``` openings (not just ```yaml), skips language tag, strips entire block. Fixes visible backtick and pipe rendering in production. [2026-04-10]
37. **Closing line completeness + parsing pass YAML-only** — Closing line must be delivered as complete two-sentence sequence in single response, never split or modified — system trigger, any variation breaks delivery. Parsing pass produces structured YAML only — no prose, no explanations, no meta-commentary once parsing begins. [2026-04-10]
38. **No-markdown first hard rule + two-path fence filter** — [FIRST RULE — NO EXCEPTIONS] moved to top of Hard Rules, strongest possible language against backtick fences in conversation. Parsing Pass preamble added: ``` markers are structural delimiters, never for conversation. TypeWriter filter rewritten with two paths: Path A (```yaml) drops all content, Path B (any other ```) strips fence markers but keeps content visible. Prevents Scout responses from being silently dropped when model wraps in plain fences. [2026-04-10]

39. **Energy signal + portrait direction** — Sixth detection mechanism added to How Scout Listens: tracks where the force of the person's mind is actually moving vs stated agenda. Signals of genuine vs blocked energy. Informs portrait and shadow passage, never stated to person. Chronicler orientation added: portrait answers where the force of the person's being is pointed, final third leaves sense of direction not just recognition. [2026-04-10]

40. **Pseudonym detection fix + compass waiting message** — Pseudonym detection window widened from len < 30 to len < 80. Added prefix patterns: "you can call me", "i'd like to be called", "just call me", "let's go with", "how about". Longer prefixes listed first for correct matching. Static context message added below compass during generation: "Your spine and portrait are being composed." in muted gold italic. [MODIFIED 2026-04-10: fixes pseudonym not capturing in production]

41. **Prompt caching on Scout system prompt** — cache_control ephemeral applied to three API call sites: send_message(), generate_yaml_sections() (4 calls in loop), send_message_stream(). Chronicler generate_portrait() excluded — different prompt per session. Reduces input token costs on repeated calls within same session. [2026-04-11]

42. **Admin dashboard + new key format + outcome tracking** — Admin at /admin-7x9k2m (no auth Phase 1). Key format: 12-char mixed case (A-Z, a-z, 0-9), old uppercase keys still valid. keys.txt format extended to key:status:recipient (third field optional). Session outcomes tracked in SQLite: completed, sufficient, user_terminated, safety_exit, abandoned, technical_failure. Outcome set in /burn based on transcript length and state. Admin dashboard: summary stats, key generation with recipient note, all-keys table with manual outcome override. Sessions table permanent — cleanup_session deletes transcripts only. /auth: .upper() removed (case-sensitive keys), recipient copied from keys.txt to database on first auth. Migration adds outcome + recipient columns to existing databases. [2026-04-19]

44. **Admin dashboard — notes field + test key generation** — sessions table gains `notes` column with migration (set_note() in scout/database.py). Admin UI adds a Notes column to the all-keys table with inline save form per row. Key generation form adds a "Test keys" checkbox that emits TEST- prefixed 6-char keys (Crockford-safe alphabet) instead of the 12-char production format. Committed but not yet deployed — requires PRE-DEPLOY CHECKLIST run. [2026-04-19]

45. **Documentation sprint — six authoritative documents written** — SOUL.md (why Scout exists, what it must never compromise, Planes Architecture, Boss/David standard), ARCHITECTURE.md (stack, domains, session lifecycle, model allocation, key system, DB, deploy pipeline, Scout→MTN manual bridge), DECISIONS.md (14 numbered decisions with date, reasoning, status), KNOWN_ISSUES.md (active bugs, parked features, known model behaviour issues), ROADMAP.md (v1.0–v3.0 + A01–A12 aesthetics register), HANDOVER.md (replaces founding handover — who Pope is, what Scout is today, deployment state, next agenda, read order). Committed in 417d839. These six files are now the source of truth; if a CC session contradicts them, the docs win. [2026-04-19]

46. **Admin manual delivery — one-time link generation** — New `deliveries` table (token PK, key, expires_at, portrait_downloaded, meridian_downloaded, downloaded, downloaded_at). New routes: POST /admin-7x9k2m/generate (fast path checks for {key}_*_portrait_delivery.pdf and _meridian_delivery.pdf in spines/ first; if both present, copy to deliveries/ and mint token with no API calls; otherwise full pipeline runs and saves canonical _delivery.pdf alongside TXT artifacts), GET /collect/<token> (renders new collect.html in expired/closed/valid states), POST /collect/<token>/verify (rate-limited 10/min, returns {valid: true|false} only — case-sensitive, whitespace stripped, no info leak), GET /collect/<token>/portrait and /meridian (validates token + per-kind not-yet-downloaded, marks the per-kind flag on serve, combined downloaded flag flips when both served; expired/already-downloaded responses use plain-text 410). New helpers _render_portrait_pdf_bytes() and _render_meridian_pdf_bytes() — existing /download-portrait and /download-meridian refactored to call them. /generate (user route) now also writes {key}_{date}_portrait_delivery.pdf and _meridian_delivery.pdf to spines/ at session end (try/except — render failure does not break user session) so the admin fast path fires for every completed session. _read_keys_with_db() adds first_used field (created_at gated on state != 'pending'), has_transcript field (SQLite OR flat-file backup), and the admin All Keys table gains Deliver column (Generate & Deliver button shown only when status is active|used and a transcript exists somewhere) and renames Created column to First used. New collect.html is full Scout register: dark background, Bodoni Moda gold-gradient wordmark, key input with shake animation on wrong key, two oversized 240×280 square buttons (compass-rose SVG for Portrait, orthographic-globe SVG for Meridian), buttons start desaturated and lock until verify succeeds, freeze 150 ms after click, italic closed message fades in when both done. Mobile stacks vertically. Tested locally via stub PDFs end-to-end (12-step sequence + bug-fix bonus all passed at server level); WeasyPrint local Windows env failed at PDF render only, production VPS unaffected. Committed but not yet deployed. [2026-04-20]

47. **Bug fix — notes and outcome overrides on unauthenticated keys** — Root cause: set_note(), set_outcome(), set_recipient() ran UPDATE statements that matched zero rows for keys that had never been authenticated (no session row exists until /auth → create_session). All three are now UPSERTs that create a `state='pending'` row when missing. create_session() promotes pending → interviewing on first /auth and resets created_at so "First used" reflects the true first auth time, not the prior admin-annotation timestamp. get_session_stats total now excludes pending rows so admin annotations on unused keys don't inflate counts. [2026-04-20]

48. **VPS now live with 25d1faa — admin dashboard + manual delivery in production** — Commits 876f7cc, 25fcdea, 25d1faa deployed successfully via PRE-DEPLOY CHECKLIST. Verified 2026-04-21: scout.regtool.org/admin-7x9k2m returns 200, /collect/<token>/verify accepts POST. VPS HEAD matches master. Supersedes the "committed but not yet deployed" status tracked in these commits. [2026-04-21]

49. **PROJECT_STATE.md — cross-product manager snapshot created** — New top-level file for the project manager overseeing Scout, MTN, and commercialisation. Eleven sections: product identity, live state, committed-not-deployed, known issues, four-sprint plan, MTN dependencies, commercial dependencies, beta cohort (3/50 with Boss, JRMTWFU4FL, GHR7U6GEGU), decisions in effect (13 active + 2 pending for Sprint 1), manager priorities, reading order. Status tags: [LIVE], [COMMITTED], [IN SPRINT N], [BLOCKED ON MTN], [BLOCKED ON LEGAL], [PARKED], [PENDING], [VERIFY]. Updated at end of every CC session. [2026-04-21]

50. **Portrait altitude fix scheduled for Sprint 1** — First cohort feedback (2026-04-21) from sessions JRMTWFU4FL and GHR7U6GEGU identified a portrait altitude issue. Not yet in code. Chronicler prompt tuning — adjust tone/depth calibration — scheduled for Sprint 1 alongside three-tier mental health and decision architecture YAML extraction work. No new portraits should go to beta users until the fix ships. [SUPERSEDED 2026-04-21: fix shipped in commit below]

56. **Deploy confirmed + documentation corrections + SCHEMA_CONTRACTS.md verified** — All five pending commits now live on VPS (HEAD = `ead7f58`, verified 2026-04-23 via SSH `git log`): Sprint 1, Sprint 2, P0 YAML extractor fix, transcript retention, interview depth fixes. Three documentation gaps addressed in one commit. (a) DECISIONS.md: added DEC-SCOUT-018 — Interview prompt and extraction prompt must be separate system prompts. `generate_yaml_sections()` uses `YAML_EXTRACTOR_PROMPT`, never `SYSTEM_PROMPT`. Root cause recorded: Sprint 1's Hard Rule C in SYSTEM_PROMPT bled into extraction calls, model obeyed the rule and refused to generate YAML, portrait and Meridian built from empty spine. (b) PROJECT_STATE.md: Section 2 updated with new LIVE items (three-tier mental health, decision architecture YAML, pre-session framing, Chronicler altitude directive, interview depth discipline, separate extractor prompt, A08/A10/A11/A12 fixes, "Keep your Meridian safe"); VPS HEAD updated to `ead7f58`. Section 3 emptied — no commits pending deploy. Section 4 active bugs list emptied — A08/A10/A11/A12 closed and deployed. Section 5 Sprint 1 and Sprint 2 status tags changed from "DEPLOY PENDING" to "LIVE". Section 8 portrait altitude status rewritten as deployed-but-verification-pending. Section 9 rebuilt with all 17 active decisions (012 parked excluded); pending block removed since 015/016/017/018 are all written. Section 10 manager priorities reordered — MTN Pydantic update promoted to #1 priority since every new spine will now contain Sprint 1 sections that the current MTN loader cannot accept. Stale "today" references removed. (c) SCHEMA_CONTRACTS.md: authoritative contract for Scout's YAML output, verified against engine.py on VPS 2026-04-23 by the PM. Added to Scout repo root. Correction history records that original 22-April version was built from a developer's conversation report (not from engine.py) and had wrong field names; the 23-April version is the correct contract. MTN Session 7's Pydantic model work built to the incorrect contract is now invalidated and must be redone against this file. [2026-04-23]

55. **Interview depth fixes — threading discipline, L6/L7 depth signal tightening, closing gate** — Prompt-only; no other files touched. Identified from a live production session 2026-04-22. (a) Fix 1 — turn-by-turn threading: new Hard Rule inserted between "never accept first answer" and "never give advice". "Before asking the next question, make contact with what was just said. Not a summary. Not a reflection. A question that could only exist because of that specific answer." This replaces mechanical list-working without reintroducing verbal repetition (reflection ration at one-per-five exchanges is preserved). (b) Fix 2a — Layer 6 depth signal tightening: second paragraph added to existing depth signal block requiring a specific person, moment, or external cost — not a category of difficulty. Example preserved: "I tend to avoid conflict" is not the signal; "My business partner stopped bringing ideas to me after what happened in March" is. (c) Fix 2b — Layer 7 depth signal tightening: parallel addition requiring specific, unpolished language. Example: "I want to be free" is not the signal; "I am afraid I will get to sixty and realise I optimised for the wrong thing" is. (d) Fix 3 — closing sequence gate: new block inserted at the top of Section 5 (before The closing acknowledgement). Scout must not initiate closing unless L6 and L7 have each produced their depth signal. Distinguishes touched vs opened — touched is mentioned, opened is specific and unspoken. Go-back instruction supplied with exact wording: "Before we finish — there is something we only touched on earlier. [name it]. I want to go there properly." Token budget: SYSTEM_PROMPT grew from ~12,700 tokens to ~13,100 tokens — well under the 15,000 target ceiling and a tiny fraction of the 200K context window. MAX_TOKENS = 5000 on chat responses unchanged. [2026-04-22]

54. **Transcripts retained during beta — DEC-SCOUT-017** — All three transcript-deletion points in the `/burn` flow are disabled. `cleanup_session()` body in scout/database.py is now a no-op (historical `DELETE FROM transcripts WHERE key` commented out). `delete_transcript(key)` call removed from `/burn` in app.py. Flat-file `os.remove(transcript_path)` block removed from `/burn` in app.py. Public `delete_transcript()` function kept intact in scout/database.py as an API primitive for future operator use. Intent: during the beta phase (cohort at 3/50) every real session carries disproportionate diagnostic weight — portrait altitude review and regression diagnosis both require the transcript. DEC-SCOUT-014 (sessions row permanent) stands; DEC-SCOUT-017 extends permanence to the transcripts row. Decision supersedes itself on v2.0 commercial launch when deletion returns per SOUL.md §Custody. [2026-04-22]

53. **P0 regression fix — generate_yaml_sections uses YAML_EXTRACTOR_PROMPT not SYSTEM_PROMPT** — Sprint 1 added Hard Rule C to SYSTEM_PROMPT: "You must never generate the spine YAML inside the conversation window." generate_yaml_sections() was passing SYSTEM_PROMPT as the system prompt for every YAML extraction call, so the model correctly obeyed Hard Rule C and refused — returning refusal prose instead of structured YAML. Portrait and Meridian then generated from an empty spine. Fix: new YAML_EXTRACTOR_PROMPT constant in scout/engine.py — short extractor-register prompt ("You are a structured data extractor. Your job is to read a conversation transcript and extract information into YAML format…"). Only the generate_yaml_sections() call site was changed. send_message() and send_message_stream() still use SYSTEM_PROMPT with cache_control (correct — those run in interview mode). cache_control removed from the extractor call since the prompt is short and doesn't benefit from caching. This matches the STOP 3 isolated-Sonnet test from 2026-04-21 (which also bypassed SYSTEM_PROMPT and produced clean YAML with all six keys) — the production flow now matches that verified path. [2026-04-22]

52. **Sprint 2 shipped — delivery edge cases, Meridian safe message, A08 A10 A11 A12 fixes** — Committed but not yet deployed. (a) app.py + templates/collect.html: six delivery edge cases implemented — A token-not-found renders "This link is not valid." + 404 (distinct from expired); D returning-user with partial download gets a .returning-note cue on page load + pre-frozen button; E file-missing-on-disk renders Scout-register error page ("Something didn't arrive as it should. Reach out to the person who gave you your key.") + 404 not raw text; F already-collected re-request renders Scout-register error page ("This document has already been collected.") + 410 not raw text; G rate-limit-on-/verify now surfaces via a muted amber .rate-limit-note element ("Too many attempts. Wait a moment before trying again.") — client JS checks res.status === 429 before JSON parse and does NOT trigger shake (shake implies wrong key); H token case-insensitive lookup — every /collect/<token>* route starts with token = token.lower() before DB lookup. (b) templates/collect.html: two-line closed block — original "Both documents have been saved. This link is now closed." stays as .closed-primary; new .closed-safe line below in muted register ("Both documents are yours. No copy exists anywhere else — not on this server, not with Scout. Save them somewhere you will find them."). Both closed and valid branches render this block. (c) templates/portrait_pdf.html: A08 — break-inside: avoid + page-break-inside: avoid + orphans: 4 + widows: 4 added to <p> elements inside .para-wrap, .shadow-passage, .surprise-passage (previously only on the wrapper). A10 — cover compass SVG viewBox "0 0 240 240" → "-10 -10 260 260" giving 10 units of padding on all sides so the "N" text at y=10 with font-size 12 no longer clips at A4 print. (d) app.py: A11 — Meridian body font 9.5pt → 11pt, leading 5mm → 5.8mm, section titles 7.5pt → 8.5pt, pseudonym 10.5pt → 11.5pt. All as named constants at top of the loop for future tuning. (e) templates/index.html: A12 — msgEl gets explicit width:100% + maxWidth:480px + marginLeft/Right:auto; genMsg inline style switched from max-width:400px to width:400px + max-width:100% (mobile fallback) so compass horizontal position is stable regardless of message content length. (f) tests/test_collect.py — new file, 10 unittest tests covering all six edge cases + happy paths + expired-token no-regression. Limiter reset hook added in setUp so the rate-limit test doesn't poison downstream tests. All 10 pass locally. [2026-04-22]

**Portrait altitude post-fix review** — pending verification across the next three cohort sessions. Sprint 1 shipped the Chronicler altitude directive in chronicler.py; Sprint 2 did not touch it. Cannot be confirmed without real Sonnet/Opus portraits on real sessions — flagged here as an open verification item, not a Sprint 2 deliverable. Not a blocker on Sprint 2 acceptance. [2026-04-22]

51. **Sprint 1 shipped — portrait altitude fix, three-tier mental health, decision architecture YAML extraction** — Committed but not yet deployed. (a) scout/chronicler.py: new altitude directive placed after marker housekeeping and before the identity block — "The portrait must never merely confirm what the subject already believes… the win is not 'I didn't know that' but 'I've never heard it said like that.'" Addresses cohort feedback from JRMTWFU4FL and GHR7U6GEGU. (b) scout/prompt.py: CONSTRAINT 10 rewritten from binary to three tiers (acknowledge / slow / close-for-safety); "we can stay here" offer gated to heavier-end Tier 2 only; crisis resources exact wording preserved. Pre-session framing added after anonymity line, before Layer 1 — "One note before we begin. Scout goes to real depth…" delivered once, never repeated. Layer 6 four-part shadow listening (pattern/trigger/tells/interrupt) with door-opens-only probing rules. Layer 2 decision-rules listening, Layer 5 compiled-wisdom origin, Layer 7 context-trigger listening — all surface as byproducts of richer listening, not new question types. Scout's interview register unchanged. (c) scout/engine.py: Call 3 adds heuristics, failure_modes (enriched four-part with north_watch), context_triggers (with north_watch). Call 4 adds conditional sensitive_areas under north_instructions when Tier 2 handling detected. Non-negotiable across all three new sections: empty list beats invented content, null beats invented field. Verified via isolated Sonnet call on production-mode transcript: all six top-level keys present with full schema, honest empty list and null honoured, no invented content. DEC-SCOUT-015 and DEC-SCOUT-016 written to DECISIONS.md. [2026-04-21]

43. **Pseudonym removed — all sessions anonymous** — Pseudonym question replaced with "I won't ask your name. You are anonymous. It is the point here, not a limitation." All pseudonym detection code removed from app.py (prefix scanning, set_pseudonym, get_pseudonym). All sessions use "Anonymous". Chronicler and constitution still receive "Anonymous" as pseudonym parameter. [2026-04-16]

43. **Guide closing line** — After "When you are ready — enter your key.": gold hairline rule (0.5px, 40px, opacity 0.25) + "One suffers less not by controlling life more, but by understanding oneself more deeply." (Cormorant Garant 300 italic, 17px, gold, still). Last element before return button. [2026-04-16]

43. **Landing stripped back, guide opens with subline + tagline** — Landing page: removed tagline lines and subline, now shows only wordmark → guide link → key console → colophon. Guide page: opens with "Scout is built to sharpen what everyone wants to blur." (20px gold) + "An examined life is not for everyone. That is why you are here." (17px muted) + gold hairline rule before existing content. [2026-04-16]

43. **Landing subline + pseudonym question rewrite** — New line under Scout wordmark: "Built to sharpen what everyone wants to blur." (Cormorant Garant 300 italic, 16px, #6A6560, still). Pseudonym question rewritten: "What would you like to be called in this moment? Doesn't have to be your name. Choose something that feels honest." [2026-04-16]

43. **lock_input on settling phrase** — lock_input = True now fires when settling phrase detected, not only on 40-message completion. Fixes test sessions and direct-close production sessions where state went interviewing→closing→generating without lock_input, leaving compass and input lock unfired. [2026-04-16]

43. **Copy refinements across 3 files** — Tagline: "An examined life is not for everyone. / That is why you are here." Guide link: "Read this before you enter your key — it will make the difference." Colophon: "For those who are ready to look." Guide headings: "While you are here", "What this asks of you", "One thing to know first". Generation wait: single breathing message replacing 5 rotating messages ("What you brought to this session is being carefully woven." with 4s opacity pulse). Download copy: "Both documents are yours alone." Constitution section 4: "Where you draw in stone." Portrait PDF colophon: "Written for you alone, and for no one else." [2026-04-16]

43. **Guide page copy rewrite** — Four sections replacing two: opening (no heading), "Your session" (privacy + key expiry), "What this requires" (honesty standard + MTN companion preview), "Before you begin" (mental health + relational complexity). Removed "Technically" and "With truth" headings. Removed "AI interviewer" framing. Added "already in development" companion reference. Privacy language strengthened: "permanently removed", "leaves no trace". [2026-04-16]

43. **Session ending architecture fix** — Parsing pass (Section 6) removed entirely from prompt.py (239 lines, full YAML schema + rules). Scout never produces YAML in conversation. YAML generation handled exclusively by generate_yaml_sections() in engine.py. "Then begin the parsing pass" replaced with "Then the session is complete. Your role ends here." Three Hard Rules kept: no YAML in conversation, no social close without formal sequence, closing statement is only valid session end. Test prompt rewritten: no YAML generation, settling phrase only. app.py: YAML-in-production detection removed, test mode YAML trigger removed, both production and test use same settling phrase detection. lock_input signal added to SSE when state→closing. Frontend: inSettling flag allows settling exchanges while sessionEnded blocks interview input, gotLockInput scoped per-call. TypeWriter YAML filter kept as dormant safety net. [2026-04-16]

43. **Mobile triage — responsive CSS at 480px** — index.html: landing page (wordmark 52px, key input 16px full-width prevents iOS zoom, reveal button 48px touch target), guide page (15px body, 20px padding), conversation (92% message width, sticky input, 16px font, 48px send button, bottom padding for input clearance), compass/generation (100px fixed, 13px messages with ellipsis), maintenance (15px, 320px max). portrait.html: body 16px line-height 1.8, container padding with iOS home bar clearance, drop cap 42px, shadow/surprise 16px padding-left, full-width 52px download button. CSS-only, no logic changes, no !important on desktop. [2026-04-16]

43. **Meridian PDF with ReportLab + constitution prompt rewrite** — /download-meridian now generates A4 PDF via ReportLab: ivory background, globe watermark (orthographic projection lat=20 lon=15, 100mm radius, 9 continents as filled polygons, bold prime meridian + equator, faint grid), pseudonym Times-BoldItalic 38pt gold, five sections auto-spaced (Helvetica-Bold titles with 0.8mm letter-spacing, Times-Roman 9.5pt body), final pseudonym in gold italic, preamble at bottom ("THIS IS MERIDIAN" + two Lora-Italic lines), colophon. Constitution prompt rewritten: five plain paragraphs only, no headers/titles/preamble/markdown, pseudonym in final sentence of paragraph 5 only, Krishnamurti register. reportlab>=4.0.0 added to requirements.txt. [2026-04-15]

43. **EXTRACT marker + chronicler discipline + test pseudonym** — _parse_portrait_markers() handles [EXTRACT] as surprise type, strips unrecognised [TAG] markers via regex fallback. Chronicler EXTRACT instruction removed — only SHADOW and SURPRISE markers allowed, explicit no-other-markers rule added. Test keys (TEST-) skip pseudonym detection entirely — always "Anonymous". [2026-04-15]

43. **SQLite session state architecture** — In-memory _sessions dict and _started_keys set replaced with SQLite database (scout/database.py, 213 lines, WAL mode). Two tables: sessions (key, state, pseudonym, started) and transcripts (key, JSON transcript). Server-side state machine: interviewing→closing→generating→delivered. State transitions validated and logged. Single session_state string sent to frontend via SSE — replaces session_complete/settling_complete/session_depth booleans. Frontend simplified: no local state vars, no fallback timers, reads session_state only. APScheduler background job every 30s transitions stale closing sessions to generating after 90s. /chat returns 403 for generating/delivered sessions — frontend handles gracefully. /download-constitution renamed to /download-meridian. Hard gate reverted (from earlier fix). apscheduler added to requirements.txt. [MODIFIED 2026-04-15: supersedes all previous session state handling, fallback timers, and multi-boolean SSE signals]

43. **Landing page polish** — Tagline: "Knowing oneself is a big headstart / You are here because someone believes you deserve it." Guide link: "Important — read completely before entering the key." with gold→rose gold 3s breathing. Age notice: "Not yet eighteen? Come back later." moved below input field. Key label directly above input. [MODIFIED 2026-04-15: hard gate reverted — key input enabled by default]

43. **Meridian naming sweep** — All user-facing references to "spine" and "constitution" replaced with "Meridian" across 4 files (14 lines). prompt.py: closing dialogue, Constraint 7 data handling. constitution.py: document title. index.html: guide page, waiting messages, download button, exit warning. app.py: resume acknowledgement. Internal code (variable names, YAML fields, function names, file paths) unchanged. [2026-04-15]

43. **YAML prose truncation + clean transcript for Chronicler** — YAML stitcher now truncates at first non-YAML prose line, logs what was cut. PyYAML validation runs after truncation — if still invalid, recovery extracts content line-by-line to last valid point. Chronicler transcript now stripped of all ```yaml blocks from assistant messages before portrait generation. Prevents YAML contamination in portrait and prose contamination in spine. [2026-04-15]

43. **session_complete fallback for generation** — Fallback timer reduced from 10 minutes to 60 seconds. If settling_complete does not fire within 60 seconds of session_complete, triggerGenerate() fires automatically. Prevents users being stuck on compass screen when Scout uses own closing words instead of exact trigger phrase. Production safety fix. [2026-04-15]

43. **Personal constitution deliverable** — New scout/constitution.py with Krishnamurti-register prompt (5 sections, preamble, one-page constraint). generate_constitution() in engine.py — Opus, 2000 tokens, receives transcript + spine YAML + pseudonym. /generate route produces all three: YAML (stays on server), portrait, constitution. /download-constitution route serves as text file. Constitution restored on /auth resume. Download Spine button replaced with Download Constitution. Guide page updated: portrait + constitution, no mention of spine/YAML. Constraint 7 updated: portrait + constitution delivered, spine stays with tool, transcript deleted. View Portrait opens in new tab. [2026-04-15]

43. **Layer A sprint: north_moments, extractable sentence, portrait tokens** — north_moments field added to YAML schema with moment/spine_field/timing/trigger structure. Rule 8 parsing instructions: MTN interaction vocabulary, 5–10 for full session, confidence over completeness. Chronicler: [EXTRACT]...[/EXTRACT] marker instruction for sharpest sentence, stored separately for future MTN use. Portrait max_tokens raised from 10000 to 16000 in engine.py. [2026-04-15]

43. **Resilient settling detection + portrait restore on resume** — Settling detection changed from exact em-dash match to two-phrase check: "I'll start now" AND "give me a few minutes" both present. Fires regardless of dash type or punctuation variance. Portrait restore on /auth resume: scans SPINE_DIR for {key}_*_portrait.txt, restores portrait_file/date/user_id to flask_session. Portrait immediately available after browser refresh or reconnect. Fixes: mid-sentence closing line failure, portrait loss after refresh, input staying active, compass delay. [2026-04-15]

43. **Maintenance page layout fix** — Maintenance state div: added flex-direction column, align-items/justify-content center, padding. Message: 18px Cormorant Garant 300 italic gold, no opacity override. Return time: 14px muted #6A6560. Generous spacing, max-width 480px. Matches landing page register. [2026-04-14]

43. **Session dismissal fix** — Case C rewritten: natural close under 5 exchanges asks "would you like to go further or shall I put together what we have" instead of dismissing. Case F rewritten: explicit request at any depth always generates, no exceptions. _has_depth() replaced with _can_generate() — simple 10-message threshold, no keyword scanning. Hard Rule updated: Scout never decides a session is too short, never dismisses, never says "we did not get far enough." Chronicler works with whatever material exists. [2026-04-14]

43. **Pre-deploy checklist** — Mandatory 8-step checklist added to CLAUDE.md. Covers: active session check, health check, maintenance activation, deploy, env var addition, smoke test, maintenance deactivation. Includes one-block copy-paste version for Steps 3–8. Rollback instructions included. [2026-04-14]

43. **Maintenance mode** — /status route returns maintenance state + message + return_minutes from env vars. /auth returns 503 during maintenance. Landing page checks /status on load, switches to maintenance state with custom message and return time. Env vars: MAINTENANCE_MODE, MAINTENANCE_MESSAGE, MAINTENANCE_RETURN_MINUTES. Activated via sed on VPS .env + systemctl restart. [2026-04-14]

43. **Three production bug fixes** — Bug 1: Chronicler pseudonym hard constraint at top of prompt — use exactly as given, never substitute. Bug 2: session_date injected via datetime.date.today().isoformat() in first YAML directive — model no longer guesses date. Bug 3: generateCalled guard prevents double triggerGenerate() calls, scrollIntoView ensures compass visibility. [2026-04-14]

44. **No-portrait-in-stream + early-stop handling** — Two new Hard Rules: Scout must never generate portrait content, Chronicler-style prose, or anything resembling a portrait in the chat stream. If person asks to stop or requests portrait, deliver settling transition line immediately — no argument, no summary, no inline generation. Root cause: Scout was generating portrait prose in chat when user requested early stop. Fix is prompt-only, no code changes. [2026-04-13]

43. **Pseudonym collection + Chronicler pseudonym fix** — Scout asks for pseudonym in Arrival section before Layer 1. Server-side detection in /chat (exchanges 2–7, under 30 chars, strips common prefixes, checks decline signals). Chronicler receives pseudonym explicitly in user message — never invents or substitutes. chronicler.py rule added: use exact pseudonym, "Anonymous" means "Anonymous". portrait.html Save Portrait button changed to Download Portrait linking to /download-portrait. generate_portrait() accepts pseudonym parameter. [SUPERSEDED 2026-04-10: "No pseudonym collection" known gap resolved] [2026-04-10]

---

## Changes Based on User Testing

- **First real user session (Boss, K7M3WNPX4R)** — portrait generated but not delivered in-session. Manual recovery required. Scout fabricated explanation about portrait status. Led to Rule A (no fabrication), portrait pipeline fix, and settling conversation. [2026-04-08]
- **Second test session on VPS** — YAML appeared on screen, settling conversation did not fire in test mode, compass not visible, Download Portrait button missing. Led to fenced-block filter, test prompt settling instruction, compass alignment fix, button type change. [2026-04-09]
- **PDF test** — white border visible, cover not centred, paragraphs breaking across pages, colophon at top of page. Led to zero-margin page with content padding, 267mm flex containers, para-wrap divs, expanded SVG viewBox. [2026-04-09]
- **Arrival pre-layer** — untested in test mode by design. test_prompt.py runs independent minimal structure. Arrival section verified in prompt.py only. Production session required for arrival verification. Technical exception accepted — tested in production with real key, session stopped midway. [2026-04-09]

---

## Known Gaps

- [SUPERSEDED 2026-04-10: "No pseudonym collection" — Scout now asks for pseudonym in Arrival, detected server-side, passed explicitly to Chronicler]
- **IMPORTANT** — YAML stitching sometimes double-indents already-indented content. [2026-04-06]
- [SUPERSEDED 2026-04-09: "Gunicorn needed" — Gunicorn 25.3.0 installed with 3 workers]
- [SUPERSEDED 2026-04-09: "No rate limiting on /auth" — Flask-Limiter added, 5/min/IP on /auth]
- **SECURITY BACKLOG v1.2** — Gunicorn running as root user — acceptable for beta, must create dedicated scout system user and run Gunicorn under that account before commercial launch. [2026-04-09]
- **FUTURE** — No logging or monitoring beyond Flask debug output. [2026-04-06]
- [SUPERSEDED 2026-04-19: "No admin interface for key management" — admin dashboard at /admin-7x9k2m with key generation, outcome override, recipient field, notes field, test-key toggle; committed but not yet deployed]
- **FUTURE** — Portrait page requires active flask session. If session expires, /portrait returns empty state. [2026-04-09]
- **FUTURE** — send_message() sync function unused by web app (only run_session.py). [2026-04-06]
- [SUPERSEDED 2026-04-09: "No VPS deployment" — VPS is now live at scout.regtool.org]
- [SUPERSEDED 2026-04-09: "Spine save path hardcoded to /home/scout/spines" — now uses SPINE_DIR env var]
- [SUPERSEDED 2026-04-09: "Portrait loads from sessionStorage" — now served from disk]

---

## Next Session Priorities

1. **Deploy Sprint 1 + Sprint 2 to VPS.** Sprint 1 (prompt.py + engine.py + chronicler.py) and Sprint 2 (app.py + templates/collect.html + portrait_pdf.html + index.html + tests/) both on master, neither live. Run PRE-DEPLOY CHECKLIST in CLAUDE.md end to end. No new env vars across both sprints. No database migration. Smoke test with a TEST- key after deploy (flow only — TEST mode does not exercise Sprint 1 prompt content; first real session will). Portrait altitude post-fix review is pending across next three real cohort sessions. [2026-04-22]
2. **Open MTN CC chat and update Pydantic models.** Before any post-Sprint-1 spine is loaded into MTN, MTN must accept heuristics, failure_modes, context_triggers, and sensitive_areas. Current model will crash or silently drop them. MTN documentation arc (SOUL, ARCHITECTURE, DECISIONS, KNOWN_ISSUES, ROADMAP, HANDOVER) comes first. [2026-04-19]
3. **Design Scout → MTN YAML bridge.** Once MTN Pydantic models are ready. The handshake is the most important conversion point in the product. [2026-04-19]
4. **Portrait altitude verification.** First post-deploy production session: compare portrait tone/depth against the Boss/David bar and the altitude directive language ("I've never heard it said like that"). If it lands, close the Sprint 1 cohort-feedback loop on JRMTWFU4FL and GHR7U6GEGU. [2026-04-21]
5. **Stripe donation page** — deferred to v2.0 per ROADMAP.md. Kept here for visibility only. [2026-04-07]

- [SUPERSEDED 2026-04-21: "Sprint 1 — three-tier mental health + decision architecture + portrait altitude fix" — shipped in prompt.py/engine.py/chronicler.py. DEC-SCOUT-015 and DEC-SCOUT-016 written. Deploy pending.]
- [SUPERSEDED 2026-04-21: "Deploy admin dashboard + manual delivery to VPS" — shipped, verified live via HTTP 200 on /admin-7x9k2m and /collect/<token>/verify. VPS HEAD at 25d1faa matches master.]
- [SUPERSEDED 2026-04-19: "Pseudonym collection" — DEC-SCOUT-005, all sessions Anonymous, pseudonym detection removed]
- [SUPERSEDED 2026-04-19: "Gunicorn WSGI server" — Gunicorn 25.3.0 shipped 2026-04-09, already live]

---

## Model Allocation

| Function | Model | Why |
|---|---|---|
| Interview (send_message_stream) | claude-sonnet-4-5 | Cost-efficient for many round-trips. [2026-04-06] |
| YAML generation (generate_yaml_sections) | claude-sonnet-4-5 | Structured output, follows schema reliably. [2026-04-06] |
| Portrait (generate_portrait) | claude-opus-4-6 | Literary quality, emotional precision. [2026-04-07] |
| Test mode (all functions) | claude-haiku-4-5-20251001 | Fast and cheap for logistics testing. [2026-04-07] |

---

## Key Decisions

- **DEC-SCOUT-001**: Key format changed from 10-character uppercase alphanumeric to 12-character mixed case alphanumeric (A-Z, a-z, 0-9). Old keys remain valid. New format example: aK7mP2xQr9Nw. [2026-04-19]
- **DEC-SCOUT-002**: Admin dashboard at unpredictable URL /admin-7x9k2m. No authentication in Phase 1. Password protection deferred to Phase 2. [2026-04-19]
- **DEC-SCOUT-003**: Session outcomes tracked in SQLite sessions table. Six values: completed, sufficient, user_terminated, safety_exit, abandoned, technical_failure. Manual override available via admin dashboard. [2026-04-19]
- **DEC-SCOUT-004**: Key recipient name/email recorded at generation time as a note field. Email invitation system deferred to Phase 2. [2026-04-19]
- **DEC-SCOUT-005**: All sessions are Anonymous. Pseudonym detection removed entirely. No name is ever asked or stored. [2026-04-16]
- **DEC-SCOUT-006**: Meridian replaces constitution as the user-facing name for the personal constitution document. [2026-04-15]
- **DEC-SCOUT-007**: Portrait and Meridian generated as PDFs using ReportLab (Meridian) and WeasyPrint (Portrait). Text file delivery removed. [2026-04-15]
- **DEC-SCOUT-008**: YAML parsing pass removed from prompt.py. Scout never produces YAML in conversation. YAML generated server-side by generate_yaml_sections() only. [2026-04-16]

---

## Key Files

| File | Description |
|---|---|
| `CLAUDE.md` | Project instructions, constraints, review gates, STATUS.md rules for CC [2026-04-06] |
| `STATUS.md` | Single source of truth for project status [2026-04-06] |
| `.gitignore` | Excludes .env, venv, __pycache__, access/keys.txt, sessions/, run_local.bat [2026-04-06] |
| `.env` | ANTHROPIC_API_KEY only [2026-04-06] |
| `requirements.txt` | anthropic, flask, python-dotenv, pyyaml, flask-session, weasyprint [MODIFIED 2026-04-09: added weasyprint] |
| `app.py` | Flask app — all routes, auth, per-key sessions, test mode, PDF generation [MODIFIED 2026-04-09] |
| `run_session.py` | Terminal entry point for brain-only mode [2026-04-06] |
| `scout/__init__.py` | Package marker [2026-04-06] |
| `scout/prompt.py` | Scout system prompt — ~1,370 lines, the complete interviewer brain [MODIFIED 2026-04-09] |
| `scout/chronicler.py` | Chronicler prompt — portrait writing with SHADOW/SURPRISE markers, final name [MODIFIED 2026-04-09] |
| `scout/test_prompt.py` | Test mode prompt — 3-exchange with settling instruction [MODIFIED 2026-04-09] |
| `scout/engine.py` | Context window engine — API calls, YAML stitching, three model constants [2026-04-06] |
| `scout/session.py` | In-memory transcript holder [2026-04-06] |
| `keys_generate.py` | Key generator — production and TEST- keys [2026-04-07] |
| `access/keys.txt` | Key store — VPS only, never in git [2026-04-06] |
| `templates/index.html` | Landing + guide + conversation UI (three-state SPA) [MODIFIED 2026-04-09] |
| `templates/portrait.html` | Compass portrait display page [2026-04-07] |
| `templates/portrait_pdf.html` | WeasyPrint A4 PDF template [MODIFIED 2026-04-09] |
| `tests/mock_transcript.json` | 8-exchange mock transcript for testing [2026-04-06] |
| `deploy.sh` | VPS deployment script [2026-04-07] |
| `generate_keys.bat` | Windows batch — generates 10 production keys on VPS [2026-04-07] |
| `generate_test_keys.bat` | Windows batch — generates 5 test keys on VPS [2026-04-07] |
| `boss_portrait.html` | Static rendered portrait for Boss (first real user) [2026-04-08] |
| `SCOUT_MASTER_HANDOVER.md` | Master handover document for new Claude sessions [2026-04-08] |
