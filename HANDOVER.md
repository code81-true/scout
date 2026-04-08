# Scout — Handover Document

Last updated: 2026-04-07

This document contains everything a new Claude session needs to continue the Scout project with no loss of context. Read it completely before doing anything.

---

## 1. Who Pope Is

Pope is the principal at Bridge Medtech Ltd, London. He is a regulatory affairs, design controls, and quality management system contractor — and a self-taught developer building AI-powered tools for regulated industries under the "RegTool" brand.

**Working style:**
- Direct. Skip preamble. Lead with the answer.
- He reviews every change before it lands. Never proceed without approval on anything that matters.
- He writes the product copy himself — guide pages, statement text, closing language. CC implements, Pope writes.
- He thinks in terms of how something feels to the person using it, not just whether it functions.
- He will correct you clearly and constructively. Accept corrections without defensiveness.

**Non-negotiables:**
- Never change prompt.py or chronicler.py without explicit instruction. These are the brain. Pope writes them.
- Never commit without updating STATUS.md first. It must be coherent and current at every commit.
- Never run deploy.sh from the local machine. Deployment happens on the VPS only.
- Never read, write, or log .env contents. Never print API keys.
- When tests and code disagree, docs win. Read docs/ first.
- Show changes before and after. Pope reviews diffs, not descriptions.

**Engineering rules:**
- Use conventional commits (feat:, fix:, docs:, refactor:, test:)
- Python: type hints, explicit over implicit, small single-purpose functions
- Do not add features beyond what was asked. A bug fix does not need surrounding cleanup.
- Do not add Co-Authored-By lines unless Pope says it's a major version commit.

---

## 2. What Scout Is

Scout is not a chatbot. It is not a therapy tool. It is not an assessment.

Scout is a calibrated witness. It interviews one person, one time, and produces two things:

1. **A spine.yaml** — a structured personal constitution that captures who someone actually is: their roles, values, boundaries, shadows, fears, and purpose. This document becomes the foundation of MyTrueNorth — an AI companion system that reads the spine every day before speaking to the person.

2. **A portrait** — continuous prose written by the Chronicler (a separate AI persona using Opus). The portrait is not a summary. It is the closest approximation to who someone actually is, written with the precision of a great biographer and the restraint of someone who knows that truth does not need decoration.

The product philosophy: one person, one session, one spine. No accounts. No passwords. A single-use key issued by invitation. When the spine is delivered, the key burns. Nothing is stored. The spine belongs to the person alone.

Scout's voice: calm, direct, slightly formal. Warm in the way that genuine attention is warm — not in the way that performance is warm. It never flatters. It never rushes. It never fills silence with noise.

---

## 2a. Product Vision

There are days — sometimes weeks — when we cannot connect with ourselves. Not because anything is wrong with us, but because the noise is too loud. Circumstance, exhaustion, the accumulated weight of everything that needs doing. In those moments we cannot know what to do or what is right.

MyTrueNorth does not suffer from that problem. It has the spine. It knows who you are at your core — your values, your roles, your shadows, your long game — and it never forgets. On the days you cannot hear yourself, North is the compass that still points true.

This is not motivation. It is not a productivity system. It is a trusted companion that knows you better than you know yourself on your worst days — and speaks to you from that knowledge, without agenda, without the noise.

---

## 2b. Commercial Model

- **Scout is free indefinitely** for early users. No paywall. No trial period. The tool earns trust before it earns revenue.
- **MyTrueNorth subscription** is the primary revenue model. Scout builds the spine; MTN is the daily companion that reads it. The subscription value is in the ongoing relationship, not the one-time interview.
- **Optional post-session donation via Stripe** — placed 24–48 hours after the session or on a separate discoverable page. Never immediately after the portrait. The person should sit with what they received before being asked for anything. The emotional weight of the session must not be leveraged for conversion.
- **Scout → MTN handshake button** is a first-class feature to be designed. After the spine is delivered, there should be a clear, elegant path from Scout to MyTrueNorth. This is not upselling — it is the natural next step in the product journey.
- **Private cost threshold** — Pope will set a threshold when Scout API costs exceed sustainable levels. Until then, Scout remains free. This decision is Pope's alone and is not automated.

---

## 3. Technical Architecture

**Stack:**
- Python 3.12+
- Flask web application (debug=False in production)
- Anthropic API — claude-sonnet-4-5 (interview), claude-opus-4-6 (portrait), claude-haiku-4-5-20251001 (test mode)
- Single context window — full transcript sent on every API call, no summarisation
- Server-side filesystem sessions via flask-session
- Per-key session isolation in memory
- Transcript persistence to disk for resumption

**Key files:**

| File | What it does |
|---|---|
| `app.py` | Flask application. All routes: `/` (landing), `/auth`, `/burn`, `/chat` (streaming SSE), `/generate`, `/portrait`, `/test-generate`. Per-key session isolation via `_sessions` dict + `_started_keys` set. Test mode detection via `_is_test_key()`. |
| `scout/prompt.py` | Scout system prompt. ~1,312 lines. 7 sections, 7 layers, 11 safety constraints, full spine.yaml schema. The brain. |
| `scout/chronicler.py` | Chronicler prompt. ~405 lines. Portrait writing with [SHADOW] and [SURPRISE] markers. Length guidance. Advice prohibition. |
| `scout/test_prompt.py` | Test mode prompt. 3-exchange minimal interview. |
| `scout/engine.py` | API call functions. `send_message()`, `send_message_stream()` (with optional prompt/model override), `generate_portrait()` (Opus), `generate_yaml_sections()` (4 sequential calls + YAML stitching + PyYAML validation). Three model constants. |
| `scout/session.py` | In-memory transcript holder. `add_user()`, `add_assistant()`. |
| `templates/index.html` | Three-state SPA: landing page, guide page, conversation UI. All animations, auth flow, typewriter effect, generating messages, YAML block rendering. |
| `templates/portrait.html` | Compass portrait page. Marker-based passage detection. Drop cap. Movement breaks. North needle. Colophon with legal notices. |
| `keys_generate.py` | Key generator. Production keys (10-char) and TEST- prefixed keys (6-char). Lives in project root so it deploys via git. |
| `access/keys.txt` | Key store. Never committed to git. Lives on VPS only. Format: `KEY:status` (unused/active/used). |
| `deploy.sh` | VPS deployment script. Cleans sessions, pulls git, installs deps, restarts systemd service. |
| `generate_keys.bat` | Windows batch: SSHs into VPS, generates 10 production keys, downloads keys.txt. |
| `generate_test_keys.bat` | Windows batch: SSHs into VPS, generates 5 test keys, downloads keys.txt. |
| `run_session.py` | Terminal-only entry point (original PR 1). Still works for local testing without the web UI. |
| `tests/mock_transcript.json` | 8-exchange mock transcript for testing the generation pipeline without a live session. |
| `STATUS.md` | Single source of truth for project status. Must be updated before every commit. |
| `CLAUDE.md` | Project instructions, review gates, security rules, session priorities for CC. |

**Dependencies** (requirements.txt):
- anthropic>=0.39.0
- flask>=3.0.0
- python-dotenv>=1.0.0
- pyyaml>=6.0
- flask-session>=0.8.0

---

## 4. Current Production State

**VPS:** 178.104.57.52 (root access via SSH)
**Domain:** scout.regtool.org
**Git repo:** https://github.com/code81-true/scout.git (master branch)
**Local dev path:** C:\Users\Manmo\Projectns\Scout

**What is live:**
- The codebase is pushed to GitHub and can be pulled to the VPS
- deploy.sh exists and handles: git clean sessions, git pull, pip install, systemctl restart
- Key generation bat files work from Windows via SSH

**What is NOT yet live:**
- No Gunicorn WSGI server — still using Flask dev server
- nginx, SSL, systemd service need configuration on VPS
- First real user session has not been conducted

**How to deploy:**
1. Push changes to GitHub from local machine
2. SSH into VPS: `ssh root@178.104.57.52`
3. Run: `cd /home/scout && bash deploy.sh`

**How to generate keys:**
- Production: double-click `generate_keys.bat` on Windows (generates 10 on VPS, downloads keys.txt)
- Test: double-click `generate_test_keys.bat` (generates 5 TEST- keys)
- Manual: `ssh root@178.104.57.52 "cd /home/scout && /home/scout/venv/bin/python keys_generate.py 10"`

---

## 5. Design Language

Scout's visual identity is built on restraint. Everything is deliberately understated. The aesthetic says: this is not a consumer product. This is something that takes itself seriously because the person using it deserves that.

**Landing page (State 1):**
- Background: #0D0B0A (near-black)
- Wordmark: "Scout" in Cormorant Garant italic, forged bronze gradient (16-stop, 108deg), clamp(96px–172px)
- Statement text: Cormorant Garant 300, 16px, #5a5550
- Key input: bottom-border only, gold on focus (#B8965A)
- Breathing animation on interactive elements (2s cycle, guide link + key label in phase, reveal button 0.5s offset)
- Vignette pulse: 12s cycle, inset box-shadow
- Black fade transition on auth: 1.5s to black → 0.5s hold → 1s fade in

**Conversation (State 3):**
- Scout messages: Cormorant Garant italic, 18px, 300 weight, #B8965A (gold), dark background
- User messages: system sans-serif, 15px, 400 weight, #E8E4DC, opacity 0.85, right-aligned
- YAML blocks in Scout messages: monospace, 12px, #8A9A8A (soft green-grey), #111 background
- Typewriter effect: 28ms base, ±8ms jitter, punctuation pauses (600ms period, 250ms comma, 900ms paragraph)
- Generating messages: 5 rotating messages, 18s intervals, Cormorant Garant italic 22px, #B8965A

**Portrait page:**
- Background: #F5F0E8 (warm ivory)
- Text: #1C1917 (warm near-black)
- Accent: #B8965A (antique gold)
- Compass SVG watermark behind pseudonym (220px, opacity 0.07)
- Pseudonym: Bodoni Moda italic, 58px, gold
- Body: Cormorant Garant 300, 19px, line-height 1.95
- Drop capital: Bodoni Moda italic, 52px, gold
- Shadow passages: italic, 1px gold left border
- Surprise moments: 400 weight, 19.5px, 2px gold left border, subtle gold tint
- Movement breaks: two 40px gold lines flanking a rotated diamond
- North needle SVG above final line
- Colophon: Cormorant SC, 11px, gold, opacity 0.65

**Typefaces:**
- Cormorant Garant (300, 400, italic) — primary everywhere
- Cormorant SC — labels, colophons, buttons
- Bodoni Moda italic — portrait pseudonym and drop capital only
- SF Mono / Fira Code / Cascadia Code / Consolas — YAML blocks and user input

**The compass metaphor:** Scout helps someone find their true north. The compass watermark on the portrait is not decorative — it is the visual expression of what the document represents. The north needle above the final line points to what comes next.

---

## 6. The Brain

**Scout (prompt.py, ~1,312 lines):**

Scout interviews through seven layers, in order. It does not announce layers. It moves only when the current layer has yielded at least one clear, concrete, honest statement.

1. **Roles** — the hats they wear, which are chosen vs inherited, which energise vs drain
2. **Work** — what the work means and costs, not the job description
3. **People** — relational architecture, energy flow, who is absent
4. **Body** — honest physical/mental health reality (health data never appears in output)
5. **Beliefs** — tested values with cost-instances, not abstract virtue-listing
6. **Shadows** — the gap between who they are and who they want to be, with external cost
7. **Long Game** — real ambition and real fear, in unpolished language

**Key techniques:**
- 5-level listening: emotional charge, qualifiers, unprompted elaboration, conspicuous absence, self-type (present vs cast)
- Priority stack: unresolved emotional charge → contradiction → absence → insufficient depth → natural progression
- Three modes: Socratic (default), elicitation through statements, Columbo (for avoidance)
- Smokescreen detection: high word count, low information content
- Reflection discipline: max once per five exchanges
- Layer transitions: never announced, always through natural threads

**11 safety constraints:** crisis intervention (stop + helpline), health data exclusion, no real names, no advice, no political positions, no manipulation, data transparency, scope limits, minor detection (adults only), mental health boundary (pause not burn), sexual complexity (acknowledge not explore).

**Chronicler (chronicler.py, ~405 lines):**

Writes the portrait in second person. Continuous prose, no headers, no bullets. Four to six movements following emotional logic. Two required moments:
- **Half-Seen Shadow** — something the person tried hardest not to say, presented as glimpsed, not exposed. Wrapped in [SHADOW] markers.
- **Unacknowledged Greatness** — a quality they know they possess but never felt entitled to name, stated with complete confidence. Wrapped in [SURPRISE] markers.

Length tied to session depth (600–1800 words). Final third must never become advice or coaching. Last line opens something — it does not conclude.

---

## 7. Operations

**Local development:**
```bash
cd "c:/Users/Manmo/Projectns/Scout"
source venv/Scripts/activate
python app.py  # runs on localhost:5000
```

**VPS deployment:**
```bash
ssh root@178.104.57.52
cd /home/scout && bash deploy.sh
```

**Key generation (from Windows):**
- Double-click `generate_keys.bat` (10 production keys)
- Double-click `generate_test_keys.bat` (5 test keys)

**Test mode:**
- Use any TEST- prefixed key
- Routes to Haiku model with 3-exchange test prompt
- Session completes when YAML appears in response (no "Give me a moment" needed)

**Key lifecycle:** unused → active (on auth) → used (on burn). Active + no transcript = rejected (hijack prevention). Active + transcript exists = resume allowed.

**Transcript persistence:** saved to `sessions/transcripts/{key}_transcript.json` after every exchange. Deleted on burn. Enables resume after disconnection.

**Git workflow:** Push from local → deploy.sh on VPS pulls and restarts. Never commit access/keys.txt. Update STATUS.md before every commit.

---

## 8. Next Session Priorities

1. **First real user session** — monitor and note any issues with the full flow end-to-end
2. **Post-session Chronicler output review** — evaluate portrait quality, marker placement, length, final-third behaviour
3. **Gunicorn production WSGI server** — replace Flask dev server with Gunicorn behind nginx
4. **SSH key authentication on VPS** — replace password auth
5. **Prompt compression** — a compression analysis report exists (produced in this session). Estimated 34% token reduction possible. Six specific cuts identified. Awaiting Pope's decision on implementation.

---

## 9. Known Gaps and Future Work

**Must fix soon:**
- Spine save path hardcoded to `/home/scout/spines` — doesn't exist on Windows, will fail on /generate locally
- No pseudonym collection — portrait defaults to "Anonymous"
- YAML stitching sometimes double-indents content that was already indented in section responses

**Future:**
- No rate limiting on /auth (30^10 keyspace makes brute force impractical but not impossible)
- No logging or monitoring beyond Flask debug output
- No admin interface for key management
- Portrait page depends on sessionStorage — direct navigation shows nothing
- `send_message()` sync function unused by web app (only by run_session.py)
- Prompt compression implementation pending

---

## 10. How to Start the Next Session

1. Read CLAUDE.md and STATUS.md completely before doing anything
2. Read HANDOVER.md (this file) for full context
3. Check `git log --oneline -10` to see recent commits
4. Check access/keys.txt status if relevant to the task
5. Ask Pope what the priority is — do not assume
6. Never touch prompt.py or chronicler.py without explicit instruction
7. Show changes before implementing. Pope reviews first.
8. Update STATUS.md before every commit
9. Do not run deploy.sh — that happens on the VPS only

**The working directory is:** `C:\Users\Manmo\Projectns\Scout`
**The venv activation is:** `source venv/Scripts/activate`
**The server starts with:** `python app.py` (localhost:5000)
**The VPS is:** `ssh root@178.104.57.52`, project at `/home/scout`
**The repo is:** `https://github.com/code81-true/scout.git` (master branch)
