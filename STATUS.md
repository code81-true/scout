# Scout — Project Status

Last updated: 2026-04-07

---

## Current State

Scout is a single-session AI interview engine that guides one person through seven layers of self-examination and produces two outputs: a structured spine.yaml (personal constitution for the MyTrueNorth system) and a prose portrait written by the Chronicler. The system runs as a Flask web application on localhost with a landing page, single-use key authentication, streaming conversation UI, and a compass-themed portrait display page. It has not yet been deployed to VPS. The backend supports per-key session isolation, session resumption after disconnection, test mode with Haiku for logistics testing, and transcript persistence to disk during active sessions.

---

## What Is Complete

### Brain

- **Scout system prompt** (`scout/prompt.py`) — ~1,355 lines across 7 sections: Identity & Disposition, Hard Rules (one question per response, no "why", banned phrases), How Scout Listens (5-level reading framework, priority stack, Socratic/Elicitation/Columbo techniques, smokescreen detection, emotional weight handling, reflection discipline, layer transition rules, cliche handling, resistance handling), Seven Layers (Roles, Work, People, Body, Beliefs, Shadows, Long Game with opening questions, evasion patterns, depth signals for each), The Closing (closing acknowledgement, 5 contextual final questions, closing statement guidelines), Parsing Pass (full spine.yaml schema with 13 top-level sections including legal_note field, 7 parsing rules including self-type marking and health data filter), Safety (11 hard constraints including crisis intervention, health data exclusion, no real names, no advice, no political positions, no manipulation, data transparency, scope limits, minor detection, mental health boundary, sexual and relational complexity).
- **Chronicler prompt** (`scout/chronicler.py`) — Portrait writing prompt with two required moments: the Half-Seen Shadow (something the person tried hardest not to say) and the Unacknowledged Greatness (a quality they know they possess but never felt entitled to name). Includes explicit `[SHADOW]...[/SHADOW]` and `[SURPRISE]...[/SURPRISE]` markup instructions for passage detection. Length guidance tied to session depth (600–800, 900–1200, or 1400–1800 words). Explicit prohibition on advice, coaching, and resolution in the final third.
- **Test prompt** (`scout/test_prompt.py`) — Minimal 3-exchange interview for logistics testing. Produces a 10% completion spine.yaml with all fields marked low confidence.

### Backend

- `scout/engine.py` — Context window engine. Full transcript sent on every API call. Functions: `create_client()`, `send_message()` (sync), `send_message_stream()` (streaming with optional system_prompt/model override), `generate_portrait()` (Chronicler call, Opus model, 10k tokens), `generate_yaml_sections()` (4 sequential section calls + YAML stitching + PyYAML validation), `_stitch_yaml_sections()` (strips fencing, deduplicates spine: root, indents root-level keys). Three model constants: `MODEL` (Sonnet), `OPUS_MODEL` (Opus), `TEST_MODEL` (Haiku).
- `scout/session.py` — In-memory transcript holder with `add_user()` and `add_assistant()`.
- `app.py` — Flask application with per-key session isolation (`_sessions` dict + `_started_keys` set + `get_session()` helper). Routes: `GET /` (landing page), `POST /auth` (single-use key authentication with resume detection and hijack prevention), `POST /burn` (key expiry + transcript deletion + session cleanup), `POST /chat` (streaming SSE with dual completion detection — "Give me a moment" + 40 messages for production, YAML detection for test keys — transcript persistence, resume acknowledgement injection, test mode routing), `POST /generate` (YAML + portrait generation, filesystem save), `POST /portrait` (portrait display page), `POST /test-generate` (dev route using mock transcript). Test mode detection via `_is_test_key()` routes TEST- keys to Haiku model with test prompt.
- `access/keygen.py` — Key generator. 10-char uppercase alphanumeric (excluding 0/O/I/1). `--test` flag generates TEST-XXXXXX format keys. Appends to keys.txt.
- `access/keys.txt` — Key store. 22 production keys + 3 test keys. Format: `KEY:status` where status is `unused`, `active`, or `used`.
- `run_session.py` — Terminal entry point for the original PR 1 brain-only mode.

### Frontend

- `templates/index.html` — Three-state single page application:
  - **State 1 (Landing)**: Dark background (#0D0B0A), two muted statement lines in Cormorant Garant 300, "Scout" wordmark with forged bronze gradient (16-stop linear-gradient at 108deg), "What you are about to enter" guide link, key input console with password field, age notice ("Scout is for adults only"), "Reveal" auth button, "By invitation only" colophon. Breathing animation on guide link, key label (in phase), and reveal button (0.5s offset). Five UI animations: vignette pulse (12s cycle), wordmark letter-spacing on hover with crosshair cursor, input focus fade (statement and wordmark to 0.2 opacity), black fade transition on auth success (1.5s fade to black, 0.5s hold, 1s fade in), generating message rotation (5 messages, 18s intervals, gold Cormorant Garant italic).
  - **State 2 (Guide)**: "Technically" and "With truth" sections explaining what Scout is and how to approach it. Includes session resumption explanation, mental health stability notice, and relational complexity notice. Back link returns to landing.
  - **State 3 (Conversation)**: Streaming chat UI with client-side typewriter effect (28ms base delay, +/-8ms jitter, 600ms pause after periods, 250ms after commas, 900ms after paragraph breaks). Scout messages left-aligned, user messages right-aligned. Dark monospace aesthetic. Input locks during Scout response. Session completion detected via `session_complete` SSE flag. Post-session: rotating generating messages (5 messages, 18s crossfade, gold italic), then Download Spine + View Portrait buttons fade in. Exit warning activates after /burn, deactivates after download.
- `templates/portrait.html` — Compass portrait display page. Warm ivory background (#F5F0E8), warm near-black text (#1C1917), antique gold accent (#B8965A). Compass SVG watermark (220px, opacity 0.07) with outer ring, degree ticks, 8-point rose, cardinal letters, centre dot. Bodoni Moda italic for pseudonym (58px) and drop capital (52px). Cormorant Garant 300 for body (19px, line-height 1.95). Cormorant SC for colophon (10px, letter-spacing 0.22em). Gold gradient rules. Movement breaks (two lines flanking rotated diamond). Shadow passages detected via `[SHADOW]` markers — italic, 1px gold left border. Surprise moments detected via `[SURPRISE]` markers — 400 weight, 19.5px, 2px gold left border, subtle gold tint. North needle SVG above final line. Colophon includes "For adults only" and "Not a therapeutic or medical tool" legal notices. "Save Portrait" button triggers window.print(). Print styles hide button and set white background.

### Infrastructure

- **Not yet deployed.** All development and testing is on localhost:5000.
- Flask dev server with debug mode.
- Server-side filesystem sessions via flask-session.
- Transcript persistence to `sessions/transcripts/`.
- Flask session files in `sessions/flask_sessions/`.
- Per-key session isolation — multiple concurrent users supported in-memory.
- No VPS, no nginx, no SSL, no systemd service yet.

---

## Design Decisions

1. **Full transcript on every API call** — no summarisation, no truncation. The entire conversation history is sent fresh with the system prompt on every call. This ensures Scout has perfect recall and can reference early statements when detecting contradictions. Cost is higher token usage but fidelity is non-negotiable for this use case.

2. **Single context window architecture** — no RAG, no vector store, no memory system. Scout operates entirely within one conversation context. This was chosen because the interview is a single session and the full transcript must be available for the parsing pass.

3. **Client-side typewriter effect, not server-side delays** — streaming tokens arrive as fast as the API sends them and are buffered client-side, then drained character-by-character with human-like timing. This means the full response is received quickly (no timeout risk) while the display feels natural.

4. **Four sequential YAML generation calls instead of one** — the spine.yaml schema is too large for a single generation call to populate reliably. Splitting into 4 section-focused calls (meta/purpose/hats, values/hard_limits, shadows/long_game/relationships, north_instructions/intellectual_diet/unresolved) produces more complete output. Trade-off: 4x API calls, ~60s total generation time.

5. **Portrait written by Opus, interview conducted by Sonnet** — the Chronicler portrait requires literary quality and emotional precision that benefits from the most capable model. The interview itself runs on Sonnet for cost efficiency and speed given the many round-trips.

6. **Single-use key system instead of accounts** — Scout is a one-session tool. No accounts, no passwords, no email. A key is issued by invitation, used once, burned on completion. This matches the product philosophy: one person, one session, one spine.

7. **Key lifecycle: unused → active → used** — three states prevent replay attacks. Active keys with no transcript file are rejected (prevents session hijacking). Used keys are permanently expired.

8. **Transcript saved to disk after every exchange** — enables session resumption after browser crash or network drop. Transcript file is deleted when the key is burned. No transcript data persists after spine delivery.

9. **Session completion detected server-side, not client-side** — the server checks for "Give me a moment" in Scout's response AND >=40 messages (20 exchanges) for production sessions. Test sessions use YAML detection instead (```yaml + spine: in response). This prevents premature completion detection from partial phrase matches during early exchanges while allowing test mode to complete in 3 exchanges.

10. **Test mode via key prefix** — TEST- prefixed keys route to Haiku model with a minimal 3-exchange prompt. No code branching needed beyond key detection. Same pipeline, different model and prompt.

11. **YAML stitching with validation** — raw section responses are stripped of code fencing, duplicate `spine:` root keys are removed, root-level keys are indented under `spine:`, and the result is validated with PyYAML. If validation fails, the raw string is returned rather than crashing.

12. **Exit warning after burn, not before** — the beforeunload listener activates only after the key is burned (spine delivered). This prevents the user from closing the window and losing their spine without downloading it. Deactivates after download.

13. **Resume acknowledgement injected as system note** — when a session resumes, a system message is injected into the transcript instructing Scout to acknowledge the return warmly and reference where the conversation left off. This feels natural rather than mechanical.

14. **Per-key session isolation** — each authenticated key gets its own Session instance stored in `_sessions` dict, with a separate `_started_keys` set tracking which keys have received their opening. Prevents transcript collision between concurrent users. Sessions and started flags are cleaned up on burn.

15. **Marker-based passage detection, not content pattern matching** — the Chronicler wraps shadow passages in `[SHADOW]...[/SHADOW]` and surprise moments in `[SURPRISE]...[/SURPRISE]`. The portrait page parses these markers and applies CSS classes accordingly. Markers are stripped from displayed text. This replaces fragile regex pattern matching that would break when the Chronicler varied its language.

16. **Surprise passage typography: weight over style** — surprise moments use font-weight 400 (one step heavier than the 300 body text) and font-size 19.5px (barely perceptible increase). The shadow passage uses italic as its distinguishing quality. This prevents both passage types from competing visually while giving each a distinct character.

17. **Adults-only constraint with clarification before rejection** — Scout does not stop immediately on minor signals (school references, parent mentions). It asks one clarifying question first because adults frequently reference school-era memories. Only a confirmed or implied under-18 status triggers session termination. This avoids false positives while maintaining the safeguard.

18. **Legal notices on all outputs** — the spine.yaml schema includes a `legal_note` field in meta, and the portrait colophon includes "For adults only" and "Not a therapeutic or medical tool". These appear on every generated document regardless of content, establishing the tool's legal position at the point of output.

19. **Mental health pause not burn** — when a person discloses current significant mental health difficulty, Scout pauses the session and recommends they speak with their therapist or doctor. The key remains active — they can return when ready. This is a pause, not a termination. Past mental health history (therapy attended years ago, difficult periods navigated) does not trigger this constraint. The distinction between current crisis and past experience is critical to avoid over-triggering.

20. **Sexual complexity acknowledged not explored** — Scout receives sexual and relational complexity without judgement and notes it in the spine, but does not explore it at depth. It redirects to a human specialist (therapist or couples counsellor) once. No moralising. No opinions on relationship structures. The spine records what is real — not what should be real. This protects both the person and the tool from territory that requires human expertise.

---

## Changes Based on Review

1. **max_tokens 300 → 1500 → 5000** — Pope increased token limit twice. Original 300 was too restrictive for Scout's responses, especially in later layers and the closing.

2. **Prompt rewrite** — Pope replaced the initial 93-line prompt with a 1,152-line comprehensive prompt covering all seven layers, listening framework, evasion handling, closing ceremony, parsing pass schema, and safety constraints.

3. **Removed /reset route** — Pope requested removal. Single-session tool should not have a reset mechanism.

4. **"Cormorant Garamond" → "Cormorant Garant"** — Typeface name correction across Google Fonts URL and CSS declarations in portrait.html.

5. **generate_portrait() max_tokens 8000 → 10000** — Increased to give the Chronicler more room for the portrait prose.

6. **generate_yaml_sections() max_tokens MAX_TOKENS → 4000** — Each section call gets its own 4000 token budget rather than sharing the global MAX_TOKENS.

7. **GET /portrait → POST /portrait** — Changed from query parameters to JSON request body with Flask session storage. Prevents sensitive data in URL.

8. **Active key resume security tightening** — Initially active keys allowed re-auth without verification. Pope identified the hijack risk: active key + no transcript = reject. Only active key + existing transcript = allow resume.

9. **Landing page visual adjustments** — Guide link, key label, reveal button: increased font sizes, lighter colours, breathing animation. Key input: subtle background, gold focus border. Guide section titles: gold colour, wider letter-spacing.

10. **Pattern matching → marker-based passage detection** — Pope identified that regex content matching for shadow/surprise passages in portrait.html was fragile and would break in production. Replaced with explicit `[SHADOW]` and `[SURPRISE]` markers in the Chronicler prompt, parsed structurally by the frontend.

11. **Surprise passage typography** — Pope specified font-weight 400 and font-size 19.5px for surprise moments, distinguishing them from shadow passages (which use italic at 300 weight) without competing visually.

12. **Constraint 9 — minor detection** — Pope added adults-only safeguard. Scout asks one clarifying question if minor signals appear. If confirmed under 18, session stops immediately with no spine or portrait generated.

13. **Age notice on landing page** — Pope added italic notice between key label and input: "Scout is for adults only. If you are under 18 — this is not for you."

14. **Legal footer on outputs** — Pope added "For adults only" and "Not a therapeutic or medical tool" to portrait colophon, and `legal_note` field to spine.yaml meta schema.

15. **Prompt additions: layer transitions, reflection discipline, closing acknowledgement** — Pope added three new sections to the Scout prompt: rules for seamless layer transitions (no announcements), when to reflect vs ask directly (max once per five exchanges), and a closing acknowledgement passage before the final question.

16. **Constraint 10 — mental health boundary** — Pope added pause-not-burn behaviour for current mental health crisis disclosure. Key stays active. Past history does not trigger.

17. **Constraint 11 — sexual and relational complexity** — Pope added acknowledge-not-explore behaviour. Scout notes it in the spine but redirects to human specialist. No moralising.

18. **Guide page mental health and relational notices** — Pope added two paragraphs to the "With truth" section advising people in active mental health difficulty to consult their therapist first, and noting Scout's approach to sexual/relational complexity.

19. **Guide page — time commitment, guide link text, MyTrueNorth paragraph** — Pope added "Set aside two hours" as first paragraph in Technically section. Changed guide link from "Before you begin — read this" to "What you are about to enter — read this first". Added MyTrueNorth companion paragraph to With truth section before mental health notice.

20. **Five UI animations** — Pope specified vignette pulse, wordmark hover with crosshair cursor, input focus fade, black fade transition on auth success, and generating message rotation with five gold italic messages at 18s intervals.

21. **Guide page rewrite** — Pope replaced all guide page copy with pristine version. Removed "AI interviewer" framing, replaced with conversation framing. Contradictions removed. Closing line changed to "When you are ready — enter your key."

22. **CSS/layout audit fixes and conversation restyling** — Colophon overlap fixed (absolute → margin), conversation height fixed (min-height → height), contrast improved on age notice, error messages, and guide-back link. Portrait colophon and save button increased to 11px. Portrait padding reduced with intermediate breakpoint. Guide page bottom nav added (scroll-top + return button). Scout messages restyled to Cormorant Garant italic gold. User messages restyled to system sans-serif. YAML blocks in Scout messages post-rendered to monospace green-grey on dark background.

23. **Two new Hard Rules + five contradiction fixes** — Rule A: Scout has no knowledge of delivery systems, never fabricates explanations about technical features. Rule B: Scout is not the subject, every question about it is a doorway back to the person ("calibrated witness with no agenda" not "friend"). Contradiction fixes: Constraint 7 rewritten to match reality (transcript held temporarily, deleted after delivery), "It sounds like" example changed to "X seems to matter" to avoid conflict with reflection ban, Layer 2 scripted opening removed (violated transition rules), closing acknowledgement/statement duplication clarified.

24. **Portrait pipeline: save to disk, serve via URL** — Portrait text saved to SPINE_DIR/{key}_{date}_portrait.txt alongside YAML. /portrait changed from POST to GET, reads from disk via flask_session filename. portrait.html reads from Jinja template variable instead of sessionStorage. View Portrait button navigates to /portrait URL. Fixes mobile browser sessionStorage loss and tab-close loss permanently. SPINE_DIR uses os.getenv with "spines" default locally, overridable to /home/scout/spines on VPS.

25. **WeasyPrint added** — weasyprint>=68.0 added to requirements.txt. WeasyPrint 68.1 installed on VPS. Server-side PDF generation planned for portrait output.

26. **WeasyPrint PDF portrait route, chronicler final name, guide copy** — /download-portrait route generates A4 PDF via WeasyPrint with compass cover page, gold typography, shadow/surprise passage styling, pseudonym in final line. Chronicler instructed to address person by pseudonym in final sentence only. Guide page updated to mention both portrait and spine. Download screen redesigned: gold "Download Portrait" primary, understated "Download Spine" secondary.

27. **sessionEnded flag** — global JS flag prevents any sendMessage() call after session_complete is detected. Fixes bug where Scout's follow-up message after YAML generation interrupted triggerGenerate() before it could fire. Mode-agnostic — works identically for TEST- and production keys.

28. **PDF ivory redesign, View Portrait restored, compass animation** — portrait_pdf.html redesigned: ivory #FDFAF5 background, 15mm margins, cover centred, compass opacity 0.10, Cormorant Garant 11.5pt, footer with pseudonym/rule/page number, no footer on cover or colophon. View Portrait button restored as secondary between Download Portrait and Download Spine. Animated compass SVG during generation wait: searching phase (erratic needle, loops), settling phase (damped oscillation to north, 3s), settled phase (true north, N marker gold pulse, 2s), then compass fades out as download buttons fade in.

---

## Changes Based on User Testing

No live user testing has been conducted yet. All testing has been against the mock transcript (`tests/mock_transcript.json`) and local browser testing of the landing page and auth flow.

---

## Known Gaps

- **IMPORTANT** — No VPS deployment yet. nginx, SSL, systemd service, Gunicorn all needed.
- **IMPORTANT** — Spine save path is hardcoded to `/home/scout/spines` which doesn't exist on Windows localhost. Will fail silently on /generate.
- **IMPORTANT** — No pseudonym collection. Portrait page defaults to "Anonymous". Need to ask user for pseudonym during or after interview.
- **IMPORTANT** — YAML stitching produces valid structure but section responses sometimes include content already indented, leading to double-indentation. Needs more robust whitespace handling.
- **FUTURE** — No rate limiting on /auth. Brute force key guessing is theoretically possible (though 30^10 keyspace makes it impractical).
- **FUTURE** — No logging or monitoring beyond Flask debug output.
- **FUTURE** — No admin interface for key management. Keys managed via CLI keygen.py only.
- **FUTURE** — Portrait page requires active flask session. If session expires, /portrait returns empty state.
- **FUTURE** — The `send_message()` sync function is unused by the web app (only used by `run_session.py`). Could be removed or kept for terminal mode.

---

## Next Session Priorities

1. **VPS deployment** — Set up nginx reverse proxy, SSL via Let's Encrypt, Gunicorn WSGI server, systemd service. Update spine save path to VPS filesystem. Full production setup.

2. **First real user session on production** — End-to-end test with a real person on the live VPS. Validate all seven layers, closing, YAML generation, portrait delivery, key burn, and exit warning.

3. **Chronicler output review after first real session** — Evaluate portrait quality, marker placement, length, and whether the final third stays within bounds. Adjust Chronicler prompt if needed based on real output.

4. **Stripe donation page** — Separate discoverable URL, not on the portrait page. Placed 24–48hrs after session or on a page the person can find themselves. Never immediately after portrait delivery.

5. **Scout → MTN handshake button design** — First-class feature on the post-session screen. Clear, elegant path from Scout to MyTrueNorth. Not upselling — the natural next step.

---

## Model Allocation

| Function | Model | Why |
|---|---|---|
| Interview (send_message_stream) | claude-sonnet-4-5 | Cost-efficient for many round-trips. Sonnet handles the interview framework well. |
| YAML generation (generate_yaml_sections) | claude-sonnet-4-5 | Structured output generation. Sonnet follows schema instructions reliably. |
| Portrait (generate_portrait) | claude-opus-4-6 | Literary quality. The portrait requires emotional precision and prose craft that benefits from the most capable model. |
| Test mode (all functions) | claude-haiku-4-5-20251001 | Fast and cheap for logistics testing. No need for quality in test sessions. |

---

## Key Files

| File | Description |
|---|---|
| `CLAUDE.md` | Project instructions, constraints, human review gates, and STATUS.md update rules for CC |
| `STATUS.md` | This file — single source of truth for project status |
| `.gitignore` | Excludes .env, venv, __pycache__, access/ directory |
| `.env` | ANTHROPIC_API_KEY only |
| `requirements.txt` | Python dependencies: anthropic, flask, python-dotenv, pyyaml, flask-session |
| `app.py` | Flask application — all routes, auth, per-key session management, test mode detection |
| `run_session.py` | Terminal entry point for brain-only mode (PR 1) |
| `scout/__init__.py` | Package marker |
| `scout/prompt.py` | Scout system prompt — 1,152 lines, the complete interviewer brain |
| `scout/chronicler.py` | Chronicler system prompt — portrait writing with SHADOW/SURPRISE markers |
| `scout/test_prompt.py` | Test mode prompt — 3-exchange minimal interview |
| `scout/engine.py` | Context window engine — all API call functions, YAML stitching, three model constants |
| `scout/session.py` | In-memory transcript holder |
| `keys_generate.py` | Key generator — production keys and TEST- prefixed test keys. Lives in project root so it deploys via git. |
| `access/keys.txt` | Key store — not committed to git |
| `templates/index.html` | Landing page + guide + conversation UI (three-state SPA) |
| `templates/portrait.html` | Compass portrait display page with marker-based passage detection |
| `tests/mock_transcript.json` | 8-exchange mock transcript for testing generation pipeline |
| `deploy.sh` | VPS deployment script. Cleans session files, pulls from GitHub, installs dependencies, restarts Scout. Lives in repo root. |
| `generate_keys.bat` | Windows batch file. SSHs into VPS, generates 10 production keys, downloads updated keys.txt to local machine. |
| `generate_test_keys.bat` | Windows batch file. SSHs into VPS, generates 5 test keys, downloads updated keys.txt to local machine. |
