# SESSION REPORT — Scout

Permanent changelog. Newest entry first.

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

