# SESSION REPORT — Scout

Permanent changelog. Newest entry first.

---

## 2026-05-04, Landing + guide page cosmetic updates — text, spacing, mobile
**Trigger:** git push

### Shipped
- **Landing guide link restyled.** Class `guide-breathe` → `guide-glow`; old colour-cycle keyframes replaced with `@keyframes guide-glow-anim` (text-shadow pulse on `rgba(184,150,90, …)`). Visible text replaced with "Read the session guide first. This is not optional." rendered with three `<span class="u">` underlined fragments via a new `.guide-link .u { text-decoration: underline; text-underline-offset: 3px; }` rule. Colour `#8A8078` → `#B8965A` canonical Scout gold; hover `#7a7570` → `#C8A468`; letter-spacing `0.15em` → `0.18em`; margin-bottom `48px` → `56px`.
- **Age notice removed.** `<p class="age-notice">Not yet eighteen? Come back later. This will still be here.</p>` deleted from the landing HTML, plus its CSS in both the main block and the 480px media query. Adults-only enforcement remains via Scout's in-conversation clarification path (entry 17 / CONSTRAINT 10 / DEC-SCOUT unaffected).
- **Colophon removed.** `<div class="colophon-landing">For those who are ready to look.</div>` deleted from the landing HTML, plus its CSS. Landing is now `wordmark → guide link → key console`.
- **Three guide-page text replacements applied** (the fourth, "One thing to know first" → "One important bit", was retained per CC flag — original framing kept because it precedes the mental-health stable-place advisory and matches CONSTRAINT 10's three-tier weight): time-commitment paragraph reduced to "Set aside 90 minutes. No less."; section title "What this asks of you" → "This matters most — do this"; closing quote replaced with "The good life is understanding oneself with no resistance." (supersedes the line set in STATUS.md entry 43, 2026-04-16).
- **Desktop spacing refinements across landing and guide.** `#landing` padding 40 → 60 vertical; `.wordmark` margin-bottom 40 → 56; `.key-console` gap 16 → 20, max-width 280 → 300; `.key-label` letter-spacing 0.2 → 0.3em; `.key-input` padding 8px 0 → 12px 0; `.reveal-btn` letter-spacing 0.15 → 0.2em, padding 10px 32px → 12px 44px; `.reveal-btn:hover` color → `#B8965A`, border-color → `#5A4A38`; `#guide` top padding 60 → 80; `.guide-back` margin-bottom 60 → 72, hover colour → `#B8965A`; `.guide-content` max-width 600 → 580; `.guide-section-title` letter-spacing 0.3 → 0.35em, margin-bottom 24 → 28; `.guide-body` line-height 1.9 → 2.0, margin-bottom 56 → 64; `.guide-body p` margin-bottom 1.4em → 1.6em; `.guide-nav` margin-top 48 → 56; `.guide-return` letter-spacing 0.25 → 0.3em, padding 12px 36px → 14px 40px; inline guide intro spacing nudges (subtitle margin 12 → 16, body lead 24 → 32, top hr 32 → 40, closing hr 28 → 36, closing quote 16 → 20).
- **Mobile 480px breakpoint refined within existing v1.0 triage block.** KNOWN_ISSUES.md §2 v1.1 full mobile redesign scope (typography scale, input treatment, generation screen layout) deliberately untouched. Wordmark 52 → 64; `.guide-link` size 13 → 12 plus new letter-spacing/line-height/padding; `.key-console` gap added 18; `.key-input` padding added 10px 0; `.reveal-btn` letter-spacing/padding added; `#landing` padding 24 → 36; `#guide` top padding 32 → 40; new mobile rules for `.guide-back`, `.guide-section-title`, `.guide-body p`, `.guide-nav`; `.guide-body` adds margin-bottom 44; `.guide-return` adds letter-spacing 0.2em; `.age-notice` mobile rule removed alongside the main element.
- **STATUS.md updated.** New entries 72 (pass 1 — items 1/2/3/5/6 applied; item 4 held) and 73 (pass 2 — three of four held items applied per Pope direction). Cross-references on entries 13 (age notice → SUPERSEDED), 19 (time commitment → MODIFIED), 43 (landing strip-back → MODIFIED), 43 (copy refinements → MODIFIED), 43 (closing line → MODIFIED). Last-updated header rewritten with the 90-min-vs-two-hours rationale captured.

### Deployed
- Not yet deployed. `templates/index.html` only — no Python, no requirements, no schema, no env var changes. Awaits Pope to run `bash deploy.sh` on the VPS.

### Decisions Made
- None codified. Cosmetic only. The 90-min-on-the-guide-page-vs-two-hours-in-SOUL-md split was discussed and intentional: SOUL.md "two hours" is design philosophy and stays; the guide-page figure is practical instruction with a safety factor (sessions run 50–60 minutes per current cohort data, so 90 min is a deliberate over-budget). The two numbers serve different audiences — SOUL.md sets the engineering ceiling for the room Scout builds, the guide page sets the calendar block the participant should reserve.

### Blockers Resolved
- None.

### New Blockers
- None.

### PM Note
- SOUL.md "two hours" left untouched. The guide-page 90 minutes is practical instruction with safety factor — no SOUL.md change, no DEC-SHARED-004 verification needed, no prompt or schema changes.
- "One thing to know first" was kept on a deliberate veto: that section opens the mental-health stable-place advisory, and "One important bit" diminishes a serious safety boundary to a casualism. CONSTRAINT 10 is a three-tier mental-health gate; the framing of the section that introduces it should match its weight. Worth raising with Pope at the next copy review whether the heading needs a different treatment that avoids both extremes.
- Pre-existing JS issue surfaced during read but not in scope for this commit: the keyInput focus-fade handler in the script tag references `.landing-statement` which was removed from the landing HTML in entry 43 (2026-04-16). The line `document.querySelector('.landing-statement').style.opacity = '0.2';` will throw a null reference error on focus, which short-circuits the rest of the handler so the wordmark and guide link no longer fade either. Worth a one-line defensive fix in the next session — not part of this cosmetic-only commit per Pope brief.

---

## 2026-05-01, Sprint 3 deployed and verified — pipeline operational end-to-end
**Trigger:** deploy + verification session + pipeline test

### Shipped
- **Sprint 3 prompt enhancement** — `scout/prompt.py` SECTION 4B "When the Conversation Needs Help" inserted between Layer 7 and the closing sequence. Six barrier-breaking techniques with conditional framing (surfacing a contradiction without naming it, grounding to specifics, handling a first vulnerable disclosure, demonstrating real listening in the opening, asking about behaviour rather than belief, plus the privacy-response technique merged into CONSTRAINT 7). Five-phase diagnostic arc (state audit, energy mapping, fear probe with worst-case → likelihood → recovery sequence, cost accounting, reframe-and-surface) — all framed as fallback probes that fire only when organic conversation has not covered the territory.
- **CONSTRAINT 7 factual correction per DEC-SCOUT-017** — replaced the stale "interview transcript is deleted after delivery" line with the current beta-retention copy ("during this beta period the transcript is retained for quality review only — never shared, never exported, never used for anything else"). Added brevity instructions: answer briefly, return to interview, one response, do not over-explain. The constraint now reflects production reality.
- **Extraction prompt lockdown** — all four extraction calls in `generate_yaml_sections()` now use locked YAML templates with exact field names from SCHEMA_CONTRACTS.md. Negative examples explicitly forbid the field names Sonnet had previously invented (e.g. `archetype_primary`, `boundary` instead of `limit`, `temperament` instead of `session_quality`). The Sprint 1 sections (heuristics, failure_modes, context_triggers, sensitive_areas) were already correct and were preserved untouched as the reference pattern.
- **YAML truncation fix** — `YAML_EXTRACTOR_PROMPT` gains a formatting paragraph requiring every string value to be wrapped in double quotes, with internal double quotes escaped via backslash. Closes the truncation class that surfaced in 2026-04-26 (NlF6dc4mdobt) and again in the first 1JNQrG6CnglM re-extraction attempt.
- **deploy.sh fixed** — branch reference changed from `master` to `main`. Pre-fix, deploys were silently shipping the wrong branch.
- **Git reconciliation** — three-way split between local, GitHub, and VPS resolved. All three locations now sit on `main` at the same commit (`080ff9f`). `master` retired. Pipeline is one-directional: Local → GitHub → VPS. No direct VPS commits.
- **SCHEMA_CONTRACTS.md** — Update Protocol rules 6, 7, 8 added per DEC-PM-005 (forward compatibility: bridge.py treats mapped fields as optional, ignores unmapped fields, never assumes Scout shapes its YAML to MTN's operating format).
- **STATUS.md, KNOWN_ISSUES.md, DECISIONS.md** — all updated to reflect this state. YAML truncation entry removed from KNOWN_ISSUES.md §3 per the fix-then-delete rule. DEC-SCOUT-019, DEC-SCOUT-020, DEC-SCOUT-021 added to DECISIONS.md.

### Deployed
- VPS at commit `080ff9f` on `main`. All three locations (local, GitHub, VPS) synced. Health check returns 200.

### Decisions Made
- **DEC-SCOUT-019** — Extraction prompt field name lockdown. The contract precedes the code; extraction directives are now literal manifestations of SCHEMA_CONTRACTS.md.
- **DEC-SCOUT-020** — YAML quoting discipline in extractor prompt. Closes the truncation class.
- **DEC-SCOUT-021** — Branch name is `main` everywhere. `master` retired. Deployment pipeline is one-directional.
- **DEC-PM-002 LIFTED** — beta recruitment is open. Two production sessions (NlF6dc4mdobt 2026-04-25 and 1JNQrG6CnglM 2026-05-01) cleared the altitude bar; the verification gate that paused beta recruitment is satisfied.

### Blockers Resolved
- **Sprint 3 verification.** Key 1JNQrG6CnglM session: threading was fluid with smooth hat transitions, at least one barrier technique fired naturally (Scout dug into incomplete phrases), fear probe territory was covered organically and captured in the portrait, the closing depth gate held (Scout did not close early), and the portrait cleared the altitude bar with three moments above the user's existing self-model. All eight Sprint 3 invariants confirmed in production behaviour.
- **Pipeline operational end-to-end.** Scout spine for 1JNQrG6CnglM successfully bridged through `bridge.py` into MTN. The Scout → Portrait/Meridian + Scout → bridge.py → MTN pipeline now works as a single integrated flow.
- **Field name drift class closed.** Prior to lockdown, ten of fourteen sections diverged between SCHEMA_CONTRACTS.md and what Sonnet emitted. Post-lockdown, the corrected spine matches the contract section-for-section, field-for-field.
- **YAML truncation class closed.** First re-extraction of 1JNQrG6CnglM truncated at line 37 from an unquoted nested-quote value. Second re-extraction (after the quoting discipline rule was added) produced clean parseable YAML. Same fix path the 2026-04-26 entry had recommended — applied this sprint.
- **Branch confusion closed.** All three locations on `main`. `deploy.sh` references `main`. No more silently-shipping-the-wrong-branch failures.

### New Blockers
- None operational. One operational note (not a blocker): the VPS reports "System restart required" — 23 pending updates. Schedule during a quiet window. Tracked in KNOWN_ISSUES.md §1.
- Some legacy untracked files on the VPS (`keygen.py` deleted, leftover portrait files, contents of `spines/`) need cleanup in the next code-touching session. Cosmetic; no operational impact.

### PM Note
- This is the milestone where Scout has transitioned from "interviews work" to "the full pipeline works." The portrait and Meridian artifacts have been clearing their bar for some weeks; what landed today is that the spine is now in a shape MTN can consume, and the bridge actually consumes it. DEC-PM-002 lifts as a direct consequence — beta recruitment was paused on this exact dependency.
- Completed sessions to date: four (Boss / K7M3WNPX4R, JRMTWFU4FL, GHR7U6GEGU, 1JNQrG6CnglM). The 25 April and 1 May sessions are the two that cleared the altitude bar without caveats.
- `spine_validator.py` is the next CC session. Permanent post-extraction validation against SCHEMA_CONTRACTS.md, integrated into `generate_yaml_sections()` so a contract violation is caught at source rather than at bridge time. This is defensive plumbing in the same register as the existing `yamlDropped` filter and the YAML recovery path — it stays in place even when the extraction prompt is correct.
- The session's other parked items (mid-interview reflection, tone closeout question, prompt compression at v1.1) remain parked. Mid-interview reflection ships after the barrier toolkit is proven across multiple sessions, not just one.

---

## 2026-04-29, PRE_DEPLOY.md and SESSION_REPORTING.md split out of CLAUDE.md
**Trigger:** git push (documentation-only, no code changes)

### Shipped
- `PRE_DEPLOY.md` — new file at repo root. Full eight-step VPS deploy checklist extracted verbatim from CLAUDE.md, including Steps 1–8, the "If anything goes wrong" block, and the one-block copy-paste version for Steps 3–8 after Steps 1–2 pass. Three-line header at the top identifies the file purpose and notes that it is referenced by CLAUDE.md. 74 lines total (3-line header + 1 blank + 70 lines of extracted content).
- `SESSION_REPORTING.md` — new file at repo root. Session Reporting Rule extracted verbatim from CLAUDE.md, including the trigger conditions, the full format block (Trigger / Shipped / Deployed / Decisions Made / Blockers Resolved / New Blockers / PM Note), and the closing rule "This file is read by the project PM in MTN_SCOUT_MARKET. Never delete previous entries. The history is the audit trail." Three-line header at the top mirrors the PRE_DEPLOY.md pattern. 42 lines total (3-line header + 1 blank + 38 lines of extracted content).
- `CLAUDE.md` — both extracted blocks replaced with concise pointer paragraphs. The `## PRE-DEPLOY CHECKLIST — MANDATORY` heading stays; its body becomes "Full checklist lives in PRE_DEPLOY.md. Run it before every deploy that touches user-facing code. No exceptions. No shortcuts." The `## Session Reporting Rule` heading stays; its body becomes "After every git push, deployment to VPS, or milestone completion, append a new entry to SESSION_REPORT.md. Format and trigger conditions defined in SESSION_REPORTING.md. Newest entry goes at the top. Never delete previous entries." CLAUDE.md drops from 256 → 155 lines (~39% smaller).
- `STATUS.md` — entry 62 added. Header date stamp updated to today's split.

### Deployed
- Not yet deployed. Documentation-only; no VPS action required.

### Decisions Made
- **Pure extraction, no content changes.** Pope's instruction was explicit: every word moves exactly as written; nothing is rewritten or updated. Both new files contain the original content verbatim, with only a three-line header prepended.
- **Both new files use a `# header / # purpose / # Referenced by CLAUDE.md` triple-line header.** Pope's chosen format. Three H1 lines at the top is unusual markdown but matches the instruction verbatim.

### Blockers Resolved
- **CLAUDE.md size and read-cost.** Each new CC session reads CLAUDE.md first. Cutting 101 lines (PRE-DEPLOY 70 + Session Reporting 38, replaced by ~7 lines of pointers) reduces the read cost meaningfully without losing any operational guidance — the underlying content is one click away in dedicated files.

### New Blockers
- None.

### PM Note
- This split was deferred when the CLAUDE.md refactor landed earlier today (entry 61 / commit `63affdf`); Pope chose to do it as a separate clean commit. The two operations are now distinct in git history: one for content cleanup, one for file splits.
- Content-preservation check passed: 256 lines in pre-split CLAUDE.md = 155 lines in post-split CLAUDE.md + 70 lines in PRE_DEPLOY.md + 38 lines in SESSION_REPORTING.md – 7 lines of new pointer text inserted into CLAUDE.md = 256. No content lost.
- Pattern worth keeping: extract long, self-contained operational documents into dedicated files referenced from CLAUDE.md. This keeps CLAUDE.md as the read-on-arrival contract while preserving full content where it can be edited without touching the contract.

---

## 2026-04-29, CLAUDE.md refactor — stale content removed, review gates updated, env vars section added
**Trigger:** git push (documentation-only, no code changes)

### Shipped
- `CLAUDE.md` — refactored after a structured audit. Six section removals, seven rewrites, one insertion, one pointer added.
  - **Removals:** `## Current objective` (PR 1 framing), `## Stack` (ARCHITECTURE.md §Stack is authoritative), `## Project structure (to be built by CC)` (codebase is the truth), `## PR 1 success condition` (PR 1 closed in April), `## Anthropic API` (`max_tokens: 300` was 22+ days stale; current is 5000; ARCHITECTURE.md §Model allocation is the live spec), `## Next session priorities (as of 2026-04-07)` (STATUS.md is the live tracker; items 3 and 4 already done).
  - **Rewrites:** `## What this is` → two accurate sentences naming Portrait + Meridian + spine.yaml as the three artifacts (was "personal constitution" — superseded by DEC-SCOUT-007); `## Key constraints` → removed prompt.py-duplicating items (banned phrases, "why" rule, one-question rule), kept full transcript rule + health-data rule + pointer to scout/prompt.py and SOUL.md; `## Working arrangement` → path case fix (`scout\` → `Scout\`); review gates 1, 2, 3 → "Before writing X" → "Before changing X" (files exist; gate 3 defers to SCHEMA_CONTRACTS.md per DEC-PM-001; parsing pass framing removed per DEC-SCOUT-005); review gate 7 → "Before first real session" (long past) → "Before lifting maintenance after any unverified prompt change" with reference to DEC-SHARED-004.
  - **Insertion:** new `## Environment variables` section after `## Working arrangement` listing all six `.env` vars one-line-each with the VPS-only-never-in-git note. The list was previously embedded as comments inside the project-tree ASCII diagram; extracted to a proper section.
  - **Top-pointer addition:** `## Read SESSION_REPORT.md to understand what was shipped in previous sessions. Newest entry first. Do not repeat work that is already committed.` — sits below the existing OPERATING_DECISIONS / SCHEMA_CONTRACTS / BRIDGE pointers.
  - **Untouched:** all original top-of-file pointers, gates 4–6 and 8, `## What CC can do without asking`, `## Status tracking`, `## STATUS.md Rules`, full PRE-DEPLOY CHECKLIST (kept inline — split to PRE_DEPLOY.md deferred), `## Security Rules`, `## Session Reporting Rule`.
- `STATUS.md` — entry 61 added with full change list. Header date stamp bumped to 2026-04-29.

### Deployed
- Not yet deployed. Documentation-only; no VPS action required.

### Decisions Made
- **Defer split of PRE-DEPLOY.md.** The audit recommended splitting the eight-step checklist (~70 lines) into a dedicated PRE_DEPLOY.md. Pope chose to keep it inline for now. Re-evaluate if CLAUDE.md grows again.
- **No PROMPT_RULES.md created.** Conversation rules already live canonically in scout/prompt.py and philosophically in SOUL.md. Adding a third location would create a sync problem. CLAUDE.md now points to those two files instead.
- **Audit-confirmed cuts.** Six removals, seven rewrites, one insertion — all approved exactly as proposed at STOP 1.

### Blockers Resolved
- **Stale read-on-arrival contract.** Every new CC session reads CLAUDE.md first. The pre-refactor file declared Scout was "PR 1, terminal only, no frontend, no auth, no database" — every one of those statements was wrong by April 2026 production reality. The model would absorb that framing before reading the live docs. Fix lands an accurate, current contract.

### New Blockers
- None.

### PM Note
- File goes from 287 → 256 lines (~11% smaller). The bigger win is content quality, not size: the file no longer contradicts ARCHITECTURE.md, DECISIONS.md, or HANDOVER.md, and the removed sections were actively misleading rather than just redundant. Future-CC sessions arriving cold will now read a CLAUDE.md that matches today's Scout, not April-7th Scout.
- The new `## Read SESSION_REPORT.md` pointer raises the chance that future CC sessions consult the changelog before duplicating work — useful for the period when several documentation refactors are active in parallel across Scout, MTN, and the PM project.
- The audit identified TESTING_STANDARDS.md and SESSION_PROTOCOL.md as candidates considered and rejected for now. Verification rigour lives in DEC-SHARED-002 (OPERATING_DECISIONS.md); CC operating rules are best kept consolidated in CLAUDE.md rather than fragmented.

---

## 2026-04-26, spine regeneration and verification — stitcher fix confirmed working in production
**Trigger:** post-deploy verification of `31df371`

### Shipped
- No new code. This is the verification record for the 2026-04-25 stitcher fix.

### Deployed
- `31df371` deployed to VPS 2026-04-25 via `bash deploy.sh`.
- Spine for key `NlF6dc4mdobt` regenerated 2026-04-26 by running `generate_yaml_sections()` directly against the stored transcript (86 exchanges).

### Decisions Made
- None. Verification only.

### Blockers Resolved
- **Stitcher fix confirmed working in production.** Verification command per the original brief:
  ```
  python3 -c "import yaml; data = yaml.safe_load(open('/home/scout/spines/NlF6dc4mdobt_2026-04-25.yaml')); print(type(data['spine']['meta'])); print(data['spine']['meta'])"
  ```
  Output:
  ```
  <class 'dict'>
  {'session_date': '2026-04-25', 'anonymous_id': 'anon_20260425_001', 'scout_version': '2.0'}
  ```
  `spine.meta` is now a properly nested dict — not `NoneType`. The pre-fix bug (children parsed as siblings of `spine:`) is closed in production.

### New Blockers
- See the YAML truncation entry below — surfaced during this regeneration.

### PM Note
- The transcript was 86 exchanges — a substantial real session. The fix held under realistic input volume, not just the synthetic demo case. SCHEMA_CONTRACTS.md remains the authoritative shape; this regeneration confirms the stitcher now emits that shape consistently.
- The actual content of `data['spine']['meta']` differs slightly from the synthetic demo — production includes `anonymous_id` and `scout_version` fields that the synthetic test didn't model. These are model-emitted meta fields that vary by session; SCHEMA_CONTRACTS.md §meta already flags `[VERIFY on next production session — may vary by session]`. This regeneration adds two more confirmed fields to that note's evidence base.

---

## 2026-04-26, YAML truncation issue surfaced during NlF6dc4mdobt regeneration
**Trigger:** discovered during the spine regeneration above

### Shipped
- No code change. This entry records the issue, its scope, and the planned fix.
- `KNOWN_ISSUES.md` — added a new entry under §3 "Known model behaviour issues" so the issue is tracked alongside the existing model-behaviour patterns Scout handles defensively.

### Deployed
- N/A.

### Decisions Made
- **Fix scheduled for next sprint, not this commit.** The issue is contained, defensive recovery already kicks in (the existing `YAML recovery — truncated to N valid lines` log line fires), and live sessions are unaffected. Adding stricter output formatting to `YAML_EXTRACTOR_PROMPT` is the right fix but it's a prompt-tuning task that benefits from Pope's review, not an emergency hotfix.

### Blockers Resolved
- None. This entry opens a blocker, not closes one.

### New Blockers
- **YAML truncation on unquoted string values containing special characters.** Detail:
  - During regeneration of `NlF6dc4mdobt` (the freshly-fixed spine), PyYAML validation failed at line 155.
  - Error: *"while parsing a block mapping — expected block end, but found scalar"*.
  - Trigger: the model emitted an unquoted string value containing nested quotes and a colon — example shape `user_says: "time with my wife" is non-negotiable value`. PyYAML reads `"time with my wife"` as the start of a quoted key, then sees `is non-negotiable value` and throws because that's a scalar where a key was expected.
  - Recovery: the existing line-by-line recovery in `generate_yaml_sections()` truncated to 154 valid lines. The tail of the spine — including parts of the `relationships`, `long_game`, and possibly later sections — was lost.
  - File size impact: 14,322 chars (vs ~20,454 chars from a hypothetical clean regeneration with the same content).
  - Root cause: occasional model behaviour. The model knows quoted strings need to be wholly quoted; it fails at this when a value naturally contains both quoted and unquoted segments.
  - **Pre-existing.** Not caused by the 2026-04-25 stitcher fix — the truncation pattern would have surfaced just the same against any session producing this kind of value. The stitcher fix is what made it visible by pushing real-session regeneration to top of mind.
  - **Severity:** contained. Affects this regeneration only. Live sessions are unaffected — the issue surfaces only when the model produces malformed YAML values, and the defensive recovery prevents catastrophic failure (truncated > corrupted).

### PM Note
- The fix path is `YAML_EXTRACTOR_PROMPT` — add explicit instructions about quoting any value containing nested quotes, colons, or special characters. The current extractor prompt is brief on output formatting; tightening it is a small change. Scheduled for the next sprint.
- Knock-on for `NlF6dc4mdobt` specifically: the truncated file means MTN cannot bridge the full spine for that session. If the missing tail matters operationally, the regeneration can be retried — temperature variation may produce a clean output on the next attempt — or the session's `unresolved` and tail content will need manual reconstruction from the transcript. Pope's call.
- Worth keeping in view: the YAML stitcher had no structural test (called out in the 2026-04-25 PM note) and the YAML extraction prompt has no formatting test. Both are candidates for the regression-test follow-up. A small `tests/test_yaml_pipeline.py` covering both — synthetic stitcher input + a known-bad model output replay — would catch this whole class of regression cheaply.

---

## 2026-04-25, P0 stitcher indentation fix
**Trigger:** git push (emergency fix; Pope deploys immediately after)

### Shipped
- `scout/engine.py` — `_stitch_yaml_sections()` rewritten. Old logic shifted only root-level keys (no leading whitespace) by two spaces and left already-indented children alone. Result: child lines arriving from the model at column 2 ended up at the same depth as their parent key, becoming YAML siblings of `spine:` rather than children of their section. PyYAML returned `spine.meta` as `None`. New logic shifts every non-empty line by two spaces — preserving the model's relative indentation while pushing the entire section into the `spine:` namespace. Empty lines pass through unchanged. Docstring updated with the dated note.

### Deployed
- Deployed 2026-04-25 via `bash deploy.sh` on VPS. Spine for key NlF6dc4mdobt subsequently regenerated 2026-04-26 — see the 2026-04-26 entry above for the verification result.

### Decisions Made
- None. Bug fix in one function. No design change. No new env var. No schema change.

### Blockers Resolved
- **P0 stitcher indentation bug.** Production session NlF6dc4mdobt's spine had all section bodies parse as missing because of YAML structural collapse — section keys present but their children flattened into siblings of `spine:`. Fix lands the section bodies where they belong. SCHEMA_CONTRACTS.md (already updated 2026-04-25 with field structure verified from a separate good spine) remains the authoritative shape; this fix is the stitcher catching up so future spines emit that shape consistently.

### New Blockers
- None.

### PM Note
- Verification approach: real-session regeneration would have required pulling the production transcript locally, which the sandbox correctly blocks under SOUL.md custody rules. Instead the fix was verified via a deterministic before/after demo (`test_output/stitcher_demo.py`) on synthetic input shaped per SCHEMA_CONTRACTS.md. Old logic returns `spine.meta` as NoneType; new logic returns a dict with `session_date` and `schema_version`. Same input, two stitchers, two outcomes — proves the fix is correct in the abstract.
- Real-session verification (the actual command from the brief) executes post-deploy. Pope deploys → regenerates NlF6dc4mdobt via admin dashboard → runs the `yaml.safe_load(...)` check. Until then, the on-disk spine is the broken one.
- Lesson worth keeping: the YAML stitcher had been in the codebase since the early days (DEC-SCOUT-001 era) and never had a structural test. The bug only manifested when the model started returning sections with non-trivial nesting (added in Sprint 1 for the new YAML schema). The class of bug — code that's "always worked" because input shape was simple — deserves a regression test next time the schema evolves. Adding one is a small follow-up worth tracking.

---

## 2026-04-24, DELETE_TRANSCRIPTS_ON_BURN flag with deliverable gate
**Trigger:** git push

### Shipped
- `app.py` — new `_deliverables_complete(key)` helper that globs for `{key}_*.yaml`, `{key}_*_portrait_delivery.pdf`, and `{key}_*_meridian_delivery.pdf` in `spines/`. Returns True only when all three are present. `/burn` rewritten: reads `DELETE_TRANSCRIPTS_ON_BURN` via `os.getenv("DELETE_TRANSCRIPTS_ON_BURN", "false").lower() == "true"` — fail-safe default is retention. When the flag is true AND deliverables are complete, `delete_transcript(key)` fires. When the flag is true but deliverables are incomplete, deletion is skipped and a warning logged ("Transcript retained for {key} — deliverables incomplete, deletion skipped."). When the flag is false, deletion never runs — current beta behaviour.
- `scout/database.py` — `cleanup_session()` stays as a permanent no-op. Deletion logic lives in `/burn`, not in cleanup. Public `delete_transcript()` primitive remains intact.
- `CLAUDE.md` — DELETE_TRANSCRIPTS_ON_BURN added to the .env var list with the note "false during beta and development, true at commercial launch — DEC-SCOUT-017".
- `DECISIONS.md` — DEC-SCOUT-017 amended with `modified 2026-04-24` tag. Decision rewritten to reflect config-controlled + deliverable-gated behaviour. Reasoning updated to explain why config flag + gate is safer than the hardcoded disable: the flag flips cleanly at commercial launch without a code change, and the gate ensures a broken or partial generation never loses the transcript it would need for investigation.
- `STATUS.md` — entry 57 added.

### Deployed
- Not yet deployed. Pope must add `DELETE_TRANSCRIPTS_ON_BURN=false` to the VPS `.env` before running the PRE-DEPLOY CHECKLIST. If the env var is absent on the VPS, default is retention — no behavioural change vs current live. The new gate logic only activates when the flag is set to true.

### Decisions Made
- **DEC-SCOUT-017 amended.** Hardcoded retention replaced with `DELETE_TRANSCRIPTS_ON_BURN` env flag + deliverable gate. Default remains retention. Flip to deletion only happens at v2.0 commercial launch, and even then only when all three deliverables (YAML, portrait PDF, Meridian PDF) are confirmed on disk. The decision entry in DECISIONS.md retains the original 2026-04-22 date with a `modified 2026-04-24` marker in the amended body.

### Blockers Resolved
- **Commercial-launch flip-switch.** Prior to this commit, flipping transcript deletion back on at commercial launch would have required a code change (reverting or re-adding the `delete_transcript` call to `/burn`). Now it's a single env-var flip.
- **Loss-on-partial-generation risk.** Prior to this commit, if the flag were flipped on but a generation step had silently failed (e.g. the WeasyPrint render errored on deploy), the transcript would be deleted and we'd lose the only evidence. The deliverable gate prevents that — incomplete delivery means the transcript stays.

### New Blockers
- None.

### PM Note
- The deploy gate stays with Pope until `DELETE_TRANSCRIPTS_ON_BURN=false` is explicitly added to the VPS `.env`. The fail-safe default means even if Pope forgets, the live behaviour doesn't change (transcripts continue to be retained). The env var needs to be present so the flag is visible in `.env` as a concrete thing to flip at commercial launch — not merely an implicit default.
- Going forward, DECISIONS.md modifications use a `modified YYYY-MM-DD` tag in the entry rather than a second numbered decision. Avoids renumbering history while keeping the evolution visible.

---

## 2026-04-23, deploy confirmed + documentation corrections + SCHEMA_CONTRACTS.md
**Trigger:** git push (documentation-only, no code changes)

### Shipped
- `DECISIONS.md` — **DEC-SCOUT-018** added: Interview prompt and extraction prompt must be separate system prompts. `generate_yaml_sections()` (and all future generation calls) use `YAML_EXTRACTOR_PROMPT` — never `SYSTEM_PROMPT`. Records the root cause Sprint 1 + P0 regression: interview constraints bled into extraction calls through a shared system prompt.
- `PROJECT_STATE.md` — seven section corrections: Section 2 VPS HEAD updated to `ead7f58` with all newly-live items enumerated; Section 3 emptied; Section 4 active-bugs list emptied (A08/A10/A11/A12 closed and now live); Section 5 Sprint 1 and Sprint 2 headers retagged `LIVE`; Section 8 portrait altitude status rewritten to reflect deployed state with verification pending; Section 9 rebuilt with 17 active decisions (pending block removed, 015/016/017/018 added to active list); Section 10 manager priorities reordered with MTN Pydantic update promoted to #1.
- `SCHEMA_CONTRACTS.md` — new file at repo root. Authoritative contract for Scout's spine YAML output, verified against `engine.py` on VPS 2026-04-23 by the PM. Corrects wrong field names from the 22-April draft (which was built from a developer's conversation report, not from source). Correction table included at the bottom; invalidates MTN Session 7's Pydantic model changes that were built to the incorrect contract. Update protocol: Scout changes output → this file updates first → PM propagates to MTN repo and PM project → MTN implements against this file.
- `STATUS.md` — entry 56 added with full cross-reference to the three fixes above.

### Deployed
- All five pending code commits (`ea43ede`, `f920d6c`, `08d8350`, `87f0c5f`, `ead7f58`) confirmed LIVE on VPS at `ead7f58`, verified 2026-04-23 via `ssh root@178.104.57.52 "cd /home/scout && git log --oneline -3"`. Pope ran the PRE-DEPLOY CHECKLIST between yesterday's last push and today's session. This commit is documentation-only and does not need deploy.

### Decisions Made
- **DEC-SCOUT-018** — Interview prompt and extraction prompt must be separate system prompts. Already implemented in `08d8350` (the P0 fix); today's commit formalises it as a design decision in DECISIONS.md. Every future generation call must use `YAML_EXTRACTOR_PROMPT` (or its successor for future output types) rather than borrowing `SYSTEM_PROMPT`. The architectural principle is: interview prompts carry behavioural constraints for conversation; extraction prompts carry neutral data-extraction instructions. The two are not interchangeable.

### Blockers Resolved
- Stale VPS HEAD reference in PROJECT_STATE.md Section 2 (was claiming `25d1faa`, verified today at `ead7f58`).
- Stale "DEC-SCOUT-015/016 pending" block in Section 9 (both had been in DECISIONS.md since 2026-04-21).
- Stale "portrait altitude fix pending" in Section 8 (shipped 2026-04-21, deployed 2026-04-23).
- Missing DEC entry for the prompt-split architectural decision — now captured as DEC-SCOUT-018.
- Missing SCHEMA_CONTRACTS.md at repo root — now present and committed.

### New Blockers
- **MTN Session 7's Pydantic work must be redone.** Per SCHEMA_CONTRACTS.md §Correction History, the 22-April contract that MTN built against had wrong field names for heuristics, failure_modes, context_triggers. The 23-April contract (verified from Scout's engine.py) is the correct one. No spine bridge can proceed until MTN rebuilds its Pydantic models against the corrected contract.

### PM Note
- The PROJECT_STATE.md corrections happened because the weekly manager read would otherwise have shown stale state across multiple sections. Specifically: Section 2 implying nothing was deployed since 2026-04-21, Section 9 implying DEC-015/016 were not yet written. Both were factually wrong as of 2026-04-22. Caught today at the PM's request.
- The SCHEMA_CONTRACTS.md correction is a lesson worth capturing: PM-level contracts must be verified against code, not against session notes or developer recollection. DEC-PM-001 in SCHEMA_CONTRACTS.md enforces this going forward.
- Going forward, PROJECT_STATE.md Section 3 changes whenever any commit lands that is not immediately deployed — and clears back to empty when deploy happens. Section 2's VPS HEAD line is updated on every verified deploy.

---

## 2026-04-22, interview depth fixes — threading, L6/L7 depth signals, closing gate
**Trigger:** git push

### Shipped
- `scout/prompt.py` only. No other file touched.
- **Fix 1 — turn-by-turn threading.** New Hard Rule inserted between "never accept the first answer" and "never give advice". Copy: "Before asking the next question, make contact with what was just said. Not a summary. Not a reflection. A question that could only exist because of that specific answer. If the next question could have been asked regardless of what the person just said — it is not the next question. Stay until you find the one that could only come from this conversation, in this moment, from what was just said." This addresses the gap noted in the STOP 1 audit: the priority stack implied threading via "unresolved emotional charge / contradiction / absence," but no Hard Rule made it turn-by-turn discipline. The reflection-ration rule (one per five exchanges) is preserved — this is a question-construction rule, not a reflection rule.
- **Fix 2a — Layer 6 depth signal tightening.** Second paragraph added to the L6 Depth signal block. Requires a specific person, moment, or external cost — not a category of difficulty. "I tend to avoid conflict" is not the signal; "My business partner stopped bringing ideas to me after what happened in March" is. This stops the prompt being satisfied by generic shadow-like prose.
- **Fix 2b — Layer 7 depth signal tightening.** Parallel second paragraph added to the L7 Depth signal block. "I want to be free" is not the signal; "I am afraid I will get to sixty and realise I optimised for the wrong thing" is. Both tightenings raise the bar from "something has been named" to "something specific has been named in unpolished language."
- **Fix 3 — closing sequence gate.** New block inserted at the top of Section 5, immediately before `## The closing acknowledgement`. Scout must not initiate the closing sequence unless both L6 and L7 have produced their depth signal. Distinguishes touched (territory mentioned) vs opened (specific-and-unspoken named). Includes exact go-back wording: "Before we finish — there is something we only touched on earlier. [name it]. I want to go there properly." This gates the entry to the entire closing sequence (Reading A at STOP 1) — not the literal closing line which fires too late.
- `STATUS.md`, `PROJECT_STATE.md` — entries added, dates stamped, committed-not-deployed list extended.

### Deployed
- Not yet deployed. Pope deploys immediately after push.

### Decisions Made
- **Fix 3 placement — Reading A (top of Section 5).** Flagged at STOP 1 that "before the closing transition line" could be read as either the entry of the closing sequence (before the closing acknowledgement) or the literal line delivery inside Case A. Pope confirmed Reading A: gate at structural entry. A gate at the literal-line site would fire too late — Scout would already have begun the closing sequence in the user's experience.
- **No new numbered DEC entry.** These three fixes are prompt refinements within the existing interview philosophy (SOUL.md) — not a design change. DEC-SCOUT-015/016 stand; no new decision needed.

### Blockers Resolved
- Production session 2026-04-22 surfaced three problems: (1) Scout asked questions that did not build on the prior answer; (2) L6 and L7 were closed on generic-category statements rather than specific ones; (3) the closing sequence fired before either layer had been opened. All three addressed in this commit.

### New Blockers
- None.

### PM Note
- Token budget: SYSTEM_PROMPT grew from ~12,700 → ~13,100 tokens (under the 15,000 ceiling, tiny fraction of the 200K context window). `MAX_TOKENS = 5000` on chat responses unchanged — confirmed this at Pope's request before commit.
- This is the third commit of 2026-04-22 awaiting deploy (after the P0 regression fix at `08d8350` and the transcript-retention fix at `87f0c5f`). All four pending items — Sprint 1, Sprint 2, P0 fix, transcript retention, these depth fixes — deploy together via one PRE-DEPLOY CHECKLIST run. No new env vars, no schema migration, no new routes. All prompt/engine changes only.
- Portrait altitude post-fix verification still pending across next three real cohort sessions. The depth fixes landing today will compound with the altitude directive — first post-deploy session will be the real test of whether Scout + Chronicler now produce portraits at the Boss/David bar.

---

## 2026-04-22, transcript retention during beta — DEC-SCOUT-017
**Trigger:** git push

### Shipped
- `scout/database.py` — `cleanup_session()` body is now a no-op (explicit `return`). The historical `DELETE FROM transcripts WHERE key = ?` is gone. Docstring rewritten to explain the change and point to DEC-SCOUT-017. Public `delete_transcript()` function kept intact as an API primitive for future authorised operator use.
- `app.py` — `/burn` simplified. The `delete_transcript(key)` call is gone. The flat-file `os.remove(transcript_path)` block and its `try/except FileNotFoundError` wrapper are gone. `cleanup_session(key)` call retained as a no-op for call-site stability (cheap; no behaviour).
- `DECISIONS.md` — DEC-SCOUT-017 written with full reasoning. All three disabled deletion points enumerated explicitly so there is no ambiguity about the scope of retention.
- `STATUS.md` — entry 54 added. Date-stamped.

### Deployed
- Not yet deployed. Pope deploys.

### Decisions Made
- **DEC-SCOUT-017** — Transcripts retained during beta. Three deletion points disabled (cleanup_session body, delete_transcript call in /burn, flat-file os.remove in /burn). Public `delete_transcript()` function kept as API primitive. Decision self-supersedes on v2.0 commercial launch when deletion returns per SOUL.md §Custody.

### Blockers Resolved
- None directly. This unblocks portrait-altitude review and regression diagnosis on any real cohort session from 2026-04-22 onwards — previously those investigations had to fight against transcript deletion that fired on every /burn.

### New Blockers
- **None operationally, but one register-level tension surfaced.** SOUL.md §What Scout must never compromise #2 — "Custody. The output file lives with the person. Not on a server. Not in a database." — describes the output (Portrait, Meridian). The transcript is not the output, and retaining it server-side for operator diagnostic use is not the same as retaining the spine. DEC-SCOUT-017 explicitly notes the commitment stays narrow (no exposure, no export, no training, no other use). Worth reconciling the SOUL.md language on the next documentation pass so the distinction is codified.

### PM Note
- Pope spotted on review that changing only `cleanup_session()` would leave the stated intent ~33% achieved — `delete_transcript()` and the flat-file `os.remove()` both still fired from /burn. I flagged it, Pope confirmed the full three-point scope, and the commit reflects that. This is a rare "caught it before commit" moment — worth noting that the attention-error pattern (HANDOVER.md) can live on the CC side too when instructions are narrowly phrased. Next time, the move is to trace the intent to every call site before starting, not after.
- Scout's SQLite now grows monotonically in the transcripts table. Real cohort transcripts are small (<100 exchanges typical, ~50KB JSON). At 50 sessions the table is ~2.5MB — a non-issue. If the beta stretches past 500 sessions the retention policy should be revisited.

---

## 2026-04-22, P0 regression fix — generate_yaml_sections uses YAML_EXTRACTOR_PROMPT
**Trigger:** git push (emergency fix, Pope deploys immediately)

### Shipped
- `scout/engine.py` — new `YAML_EXTRACTOR_PROMPT` constant (short extractor-register system prompt). `generate_yaml_sections()` now passes `YAML_EXTRACTOR_PROMPT` as the system rather than `SYSTEM_PROMPT`. `cache_control` removed from this call site only — the extractor prompt is ~400 chars, caching would add no meaningful benefit. `send_message()` (line 52) and `send_message_stream()` (line 365) remain unchanged — both still use `SYSTEM_PROMPT` with `cache_control`, which is correct because those calls run in interview mode.
- `STATUS.md` — entry 53 documenting the regression and fix.

### Deployed
- Not yet deployed by this commit. Pope will deploy immediately after push.

### Decisions Made
- **Splitting interview system prompt from extraction system prompt.** The Scout interview prompt (with Hard Rule C: "never generate spine YAML in the conversation window") is the right register for chat. A different register is needed for server-side YAML extraction. These are two different jobs and need two different system prompts. Worth recording in DECISIONS.md next session pass.

### Blockers Resolved
- **P0 regression** — Sprint 1 introduced Hard Rule C to SYSTEM_PROMPT, and `generate_yaml_sections()` was passing that same SYSTEM_PROMPT to the extraction call. Model obeyed the rule → refused → empty spine → empty portrait/meridian. The STOP 3 isolated Sonnet test on 2026-04-21 actually already proved this was the failure mode (I ran it with an ad-hoc system prompt that was not SYSTEM_PROMPT and it produced clean YAML; I did not reconcile that success back to the production call path). Fix matches the STOP 3 shape: short extractor prompt, no interview constraints.

### New Blockers
- None.

### PM Note
- The regression was latent from the moment Sprint 1 shipped. It did not manifest in local tests because (a) the STOP 3 verification ran via an ad-hoc Sonnet call that bypassed SYSTEM_PROMPT, not through `generate_yaml_sections()`, and (b) TEST- mode's pre-existing YAML refusal pattern masked the behaviour in the TEST chat-through-`/generate` path. I should have reconciled the "isolated Sonnet works" result against "production `/generate` path" — the gap was real and is what just bit production.
- This is a Sprint 1/Sprint 2 post-fix item. The fix is prompt-only, one function touched, one constant added. No schema change, no route change, no new env var.
- Lesson for the testing protocol: "isolated call test" ≠ "production call path test." The isolated test confirmed the schema could be produced; it did not confirm that the actual server code would produce it. Next time, the verification bar is "exercise the exact function the server calls."

---

## 2026-04-22, end of session — Sprint 2 shipped: delivery edge cases, Meridian safe message, A08 A10 A11 A12 fixes
**Trigger:** git push

### Shipped
- `app.py` — /collect routes rewritten for edge cases. Token normalised to lowercase at every route entry (case H). `_serve_delivery_pdf` now renders `collect.html` with Scout-register statuses (`invalid`, `error_missing`, `error_collected`) instead of raw text. Meridian PDF font bumps (A11) as named constants: body 9.5→11pt, leading 5→5.8mm, titles 7.5→8.5pt, pseudonym 10.5→11.5pt.
- `templates/collect.html` — four new status branches (`invalid`, `error_missing`, `error_collected`, plus returning-user cue inside `valid`). Two-line closed block in both closed and valid branches: primary line retained, new muted `.closed-safe` line with the Keep-your-Meridian-safe copy. New `.rate-limit-note` element fades in on 429 (case G). JS now checks `res.status === 429` before JSON parse and does not shake on rate-limit (shake implies wrong key). Returning-user `.returning-note` shown when either `portrait_done` or `meridian_done` is true on page load (case D).
- `templates/portrait_pdf.html` — A08: `break-inside: avoid` + `page-break-inside: avoid` + `orphans: 4` + `widows: 4` now applied to `<p>` elements inside `.para-wrap`, `.shadow-passage`, `.surprise-passage` (previously only on the wrappers). A10: cover compass SVG viewBox `0 0 240 240` → `-10 -10 260 260` — pure geometry, no design change.
- `templates/index.html` — A12: `msgEl` container gets explicit `width: 100%` + `maxWidth: 480px` + `marginLeft/Right: auto`; generating-message inline style switches from `max-width:400px` to `width:400px; max-width:100%`. Compass horizontal position now independent of message content length.
- `tests/test_collect.py` — new file, 10 unittest tests. Covers all six edge cases (A, D, E, F, G, H), three happy paths (correct key, wrong key no-leak, expired), and one case-normalisation on /verify. `setUp` hook resets Flask-Limiter state between tests so the rate-limit test doesn't poison downstream tests. All 10 pass.
- `STATUS.md` — entry 52 added. Portrait altitude post-fix review flagged as pending verification across next three cohort sessions (not blocking Sprint 2).
- `KNOWN_ISSUES.md` — A08, A10, A11, A12 removed from active bugs. "Six delivery edge cases" and "Keep your Meridian safe" moved from parked to shipped.
- `PROJECT_STATE.md` — Section 3 now lists both Sprint 1 and Sprint 2 as committed-not-deployed. Section 4 active-bugs list annotates A08/A10/A11/A12 as "fix committed, awaiting deploy". Section 5 Sprint 2 marked SHIPPED, DEPLOY PENDING.

### Deployed
- Not yet deployed. VPS remains at previous commit. Pope holds the deploy gate manually. Sprint 1 and Sprint 2 will ship together — single PRE-DEPLOY CHECKLIST run covers both.

### Decisions Made
- None. Sprint 2 is implementation-only — existing decisions stood throughout.

### Blockers Resolved
- A08 (paragraph page-break), A10 (compass needle clip), A11 (Meridian font), A12 (compass shift) — all closed in KNOWN_ISSUES.md. Fixes committed; take effect on deploy.
- Six delivery edge cases "designed on paper, not implemented" — now implemented with test coverage.
- "Keep your Meridian safe" message — designed but not shipped → now shipped.

### New Blockers
- None.

### PM Note
- Two sprints now sitting on master awaiting deploy (ea43ede + the Sprint 2 commit). Pope holds the gate by design. Both together are: prompt/engine changes + delivery polish. No new env vars, no schema migration, no new routes. One PRE-DEPLOY CHECKLIST run covers both.
- Portrait altitude post-fix verification is pending across the next three real cohort sessions. This carries across the Sprint 1/2 boundary. Beta cohort still at 3/50 (Boss, JRMTWFU4FL, GHR7U6GEGU) — recruitment is the blocker on closing the altitude loop.
- MTN Pydantic update (Component 5) remains the critical dependency before any post-Sprint-1 spine can be bridged. Not touched in Sprint 2.

---

## 2026-04-21, end of session — Sprint 1 shipped: portrait altitude fix, three-tier mental health, decision architecture YAML extraction
**Trigger:** git push

### Shipped
- `scout/chronicler.py` — P0 portrait altitude directive placed after marker housekeeping, before identity block. "The portrait must never merely confirm what the subject already believes… the win is not 'I didn't know that' but 'I've never heard it said like that.'" Addresses cohort feedback from JRMTWFU4FL and GHR7U6GEGU (2026-04-21).
- `scout/prompt.py` — Component 0 pre-session framing after anonymity line, before Layer 1 ("One note before we begin. Scout goes to real depth…", delivered once). CONSTRAINT 10 fully rewritten from binary to three tiers (acknowledge / slow / close-for-safety); "we can stay here as long as this needs" offer gated to heavier end of Tier 2; crisis resources wording exact. Layer 6 four-part shadow listening (pattern/trigger/tells/interrupt) with door-opens-only probing. Layer 2 decision-rule listening, Layer 5 compiled-wisdom origin, Layer 7 context-trigger listening. Scout's interview register unchanged — new listening surfaces as byproducts, not new question types.
- `scout/engine.py` — Call 3 adds heuristics, failure_modes (four-part with north_watch), context_triggers (with north_watch). Call 4 adds conditional sensitive_areas under north_instructions when Tier 2 handling detected. Non-negotiable across all three: honest empty list beats invented content; null beats invented field.
- `DECISIONS.md` — DEC-SCOUT-015 (three-tier mental health) and DEC-SCOUT-016 (decision architecture YAML extraction) written with full reasoning.
- `STATUS.md` — entries 50 (superseded) and 51 (Sprint 1 shipped). Next Session Priorities rewritten: deploy is #1.
- `PROJECT_STATE.md` — Section 3 populated with Sprint 1 commit. Section 5 Sprint 1 status moved from IN FLIGHT to SHIPPED, DEPLOY PENDING. Section 10 manager priorities updated.
- `.gitignore` — added `test_output/` to exclude local verification artifacts.

### Deployed
- Not yet deployed. VPS remains at previous commit (25d1faa). Pope will run PRE-DEPLOY CHECKLIST separately. No new env vars, no database migration — prompt-and-engine change only.

### Decisions Made
- **DEC-SCOUT-015** — Three-tier mental health response replaces binary CONSTRAINT 10. Tier detection lives in Scout's judgment about full context, not individual words. Close only for immediate safety; everything else met with presence.
- **DEC-SCOUT-016** — Decision architecture YAML extraction. heuristics / failure_modes / context_triggers, each with north_watch directives, produced server-side by generate_yaml_sections. Honest empty list beats invented content.

### Blockers Resolved
- Portrait altitude regression (JRMTWFU4FL, GHR7U6GEGU, 2026-04-21) closed in code. Deploy + one production session will confirm it lands.

### New Blockers
- **MTN Pydantic update is now on the critical path.** Any spine generated post-Sprint-1 will include heuristics, failure_modes, context_triggers, sensitive_areas. Loading that into the current MTN loader will crash or silently drop content. No post-Sprint-1 spine may be bridged to MTN until the Pydantic models are updated (Component 5 — separate MTN session).

### PM Note
- Deploy sequence matters: Scout changes → test locally (done) → deploy Scout to VPS → open MTN CC chat → update Pydantic models → only then bridge.
- Sprint 1 verification note: runtime YAML test ran via isolated Sonnet call against a closed production-mode transcript — all six top-level keys present with full schema, honest empty list and null honoured, no invented content. TEST- mode cannot exercise the new prompt content because TEST_PROMPT overrides SYSTEM_PROMPT in chat (pre-existing architectural limit, documented in STOP 3). First post-deploy production session will exercise Components 0/1/2/3 and the altitude directive end-to-end.
- Beta cohort still at 3/50. Portrait altitude verification needs the next real session to close the loop.

---

