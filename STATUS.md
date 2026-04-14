# Scout — Project Status

Last updated: 2026-04-09

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

42. **Session dismissal fix** — Case C rewritten: natural close under 5 exchanges asks "would you like to go further or shall I put together what we have" instead of dismissing. Case F rewritten: explicit request at any depth always generates, no exceptions. _has_depth() replaced with _can_generate() — simple 10-message threshold, no keyword scanning. Hard Rule updated: Scout never decides a session is too short, never dismisses, never says "we did not get far enough." Chronicler works with whatever material exists. [2026-04-14]

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
- **FUTURE** — No admin interface for key management. [2026-04-06]
- **FUTURE** — Portrait page requires active flask session. If session expires, /portrait returns empty state. [2026-04-09]
- **FUTURE** — send_message() sync function unused by web app (only run_session.py). [2026-04-06]
- [SUPERSEDED 2026-04-09: "No VPS deployment" — VPS is now live at scout.regtool.org]
- [SUPERSEDED 2026-04-09: "Spine save path hardcoded to /home/scout/spines" — now uses SPINE_DIR env var]
- [SUPERSEDED 2026-04-09: "Portrait loads from sessionStorage" — now served from disk]

---

## Next Session Priorities

1. **Pseudonym collection** — ask user for pseudonym before or after interview. [2026-04-09]
2. **Gunicorn WSGI server** — replace Flask dev server. [2026-04-07]
3. **Chronicler output review** — evaluate portrait quality after real sessions. [2026-04-07]
4. **Stripe donation page** — separate discoverable URL, 24–48hrs post session. [2026-04-07]
5. **Scout → MTN handshake button design** [2026-04-07]

---

## Model Allocation

| Function | Model | Why |
|---|---|---|
| Interview (send_message_stream) | claude-sonnet-4-5 | Cost-efficient for many round-trips. [2026-04-06] |
| YAML generation (generate_yaml_sections) | claude-sonnet-4-5 | Structured output, follows schema reliably. [2026-04-06] |
| Portrait (generate_portrait) | claude-opus-4-6 | Literary quality, emotional precision. [2026-04-07] |
| Test mode (all functions) | claude-haiku-4-5-20251001 | Fast and cheap for logistics testing. [2026-04-07] |

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
