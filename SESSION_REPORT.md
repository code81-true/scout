# SESSION REPORT — Scout

Permanent changelog. Newest entry first.

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

