# Phase 3: Dorico Import + Playback Validation - Context

**Gathered:** 2026-05-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Physically validate the production `cents.doricolib` (1,261,618 bytes, md5 `4cd707d2f4b10154a528b95e2ff5db9f`, shipped at repo root by Phase 2) against the user's installed Dorico Pro 6.x on macOS. Validation = (a) Library Manager import succeeds; (b) panel populates with all 597 accidentals after an open/atonal key signature is in place; (c) tuner spot-checks confirm cent-accurate playback against HALion across the PLAY-03 named matrix; (d) panel-search ergonomics work at 597-entry scale across the four named queries; (e) cent-label collision behavior is sparse-clean and dense-passage-documented.

Phase 3 is **manual-validation work** — Dorico has no headless mode. The user runs every check by hand against their actual install. No code is written in this phase unless a check fails (in which case the fix loops back to Phase 2 modules — see D-03 below).

**In scope:**
- Library Manager import smoke test on macOS Dorico Pro 6.x
- Open/atonal key-signature gate verification (Pitfall 5 defense)
- Panel-population check at 597-entry scale (UX-01)
- Panel-search ergonomics across `+14`, `Sharp -`, `Flat +50`, `Natural` (UX-02)
- Tuner spot-checks against HALion across PLAY-03's named matrix (PLAY-02 + PLAY-03)
- Sparse-passage no-collision check + dense-passage documentation of `Sharp -50` + `Natural +50` + `Flat +50` chord stack on a single beat (UX-03)
- Recording results in a single `03-VERIFICATION.md` (D-04)
- If any check fails: pause-and-fix loop into Phase 2 modules → re-emit `cents.doricolib` → re-import → re-test (D-03)

**Explicitly NOT in scope (deferred):**
- NotePerformer or third-party VST validation → out of v1 (D-02); Phase 4 README troubleshooting names HALion/NotePerformer as confirmed engines without us re-testing NP
- Generated `.dorico` test project / `cents-test.dorico` deliverable → rejected at PROJECT.md scope (v2 DIFF-01); user will not write code or build a scaffold artifact (D-01)
- Markdown step-by-step protocol document → not needed; user will improvise the import workflow against an existing Dorico project of their choice (D-01)
- README content, install-path documentation, troubleshooting prose → Phase 4
- Any change to `compose.py` / `pitch.py` / `emit.py` unless triggered by a Phase 3 failure (D-03)
- Code review / security audit of validation results (no code is written in Phase 3 absent a failure)

</domain>

<decisions>
## Implementation Decisions

### Test scaffold
- **D-01:** **No test scaffold artifact.** The user opens an existing Dorico project of their choice (or creates a fresh one ad hoc), imports `cents.doricolib` via Library Manager, inserts an open key signature (Shift+K → `open`), switches the tonality system to `cents`, and walks the spot-check matrix manually. No `tools/build_test_score.py`, no markdown walkthrough, no `validation-scratch.dorico` template. The PLAY-03/UX-01..03 case list lives in the Phase 3 plan itself; the user reads it and runs the checks. This is the lowest-cost path and matches PROJECT.md's "Out of Scope: bundled sample .dorico test score" line.
  - The Phase 3 plan must enumerate every spot-check case explicitly (not "etc.") so the user can tick them off without thinking.
  - The plan must call out the open-key-signature step as the first action (Pitfall 5 defense — silent failure if skipped).

### VST sign-off
- **D-02:** **HALion only.** Dorico's stock playback engine is the gate for Phase 3 sign-off. NotePerformer is not required to be tested even if owned. Rationale: HALion is confirmed cent-accurate (per Pitfall 12 research and Scoring Notes); if HALion plays the matrix correctly, the library's pitch-delta math is correct and downstream VST issues are engine-side, not library-side. Phase 4's README will name HALion as the validated engine and mention NotePerformer as a separately-confirmed cent-accurate engine (per published Scoring Notes commentary) without our re-validation.
  - The Phase 3 plan does NOT need a NotePerformer column, NotePerformer setup steps, or NotePerformer fallback notes.

### Failure-handling policy
- **D-03:** **Pause-and-fix loop.** If any tuner check, panel-search query, or layout check fails, Phase 3 pauses, the root cause is diagnosed, and the fix lands in the appropriate Phase 2 module (`pitch.py` for math errors, `compose.py` for class-dispatch / naming / offset errors, `emit.py` for XML formatting drift, `main.py` for orchestration). The generator re-runs (`python build.py --out cents.doricolib`), the user re-imports via Library Manager, and the failed check is re-run. Phase 3 does NOT close until every PLAY-03 + UX-01..03 check passes against a single committed `cents.doricolib`.
  - This matches ROADMAP.md's note: *"if validation surfaces issues, the fix is name-format adjustment in Phase 2's compose.py (no architectural change)"*.
  - The fix loop does NOT spawn a separate "Phase 2.5 patch phase" — fixes commit to the existing Phase 2 module surface and the existing test net (`tests/test_pitch.py`, `tests/test_cents_structural.py`, `tests/test_cents_snapshot.py`, `tests/test_determinism.py`) gains a regression test for the specific failure before re-emission.
  - Determinism contract is preserved across the loop: `PROJECT_NAMESPACE` MUST NOT rotate; key strings (`sharp`, `flat`, `natural`, `<base><signed-cents>`) MUST NOT change (Pitfall 6). Any fix that would require renaming an entity key is a hard stop and must be escalated.
  - If a failure is purely cosmetic (UX-03 dense-passage collision behavior) and the math/playback is correct, the failure is documented in `03-VERIFICATION.md` as a known limitation with the Engrave-mode workaround named (per ROADMAP success criterion 3) — this is the one exception to "loop until all pass" and applies ONLY to UX-03 dense-passage layout, NOT to UX-03 sparse-passage cleanliness, panel-population, panel-search, or any playback check.

### Results artifact
- **D-04:** **Single `03-VERIFICATION.md`.** The standard GSD verifier output is the canonical record — no separate `03-VALIDATION-REPORT.md`. It mirrors Phase 1 and Phase 2's pattern (`.planning/phases/01-.../VERIFICATION.md`, `.planning/phases/02-.../02-VERIFICATION.md`). Structure: a row per success criterion / requirement (PLAY-02, PLAY-03 broken into the named cases, UX-01, UX-02 broken into the four queries, UX-03 sparse + UX-03 dense), each row carrying expected behavior, observed behavior, pass/fail, and Dorico build version. Phase 4's README will cite `03-VERIFICATION.md` for its "validated against HALion" claim.
  - Path: `.planning/phases/03-dorico-import-playback-validation/03-VERIFICATION.md`.
  - Generated by `/gsd-verify-phase` (or its equivalent) after the user signs off on every check.

### Plan structure (Claude's discretion → guidance)
- **D-05:** Phase 3 likely needs **one plan** (not three waves) because there is no code work absent a failure. The single plan is a checklist with explicit cases drawn from PLAY-03 + UX-01..03; the user works it top-to-bottom. If a failure triggers the D-03 loop, the loop's code fix is appended to the same plan or split out at planner discretion.
  - Planner may instead split into 2 plans if useful: Plan 03-01 = import + panel-population + panel-search (UX-01, UX-02); Plan 03-02 = playback spot-check matrix + collision check (PLAY-02, PLAY-03, UX-03). Both shapes are acceptable. The user does NOT want artificial three-wave fan-out for what is fundamentally a one-pass manual checklist.

### Claude's Discretion
- Exact ordering of spot-checks within the plan (likely sensible: import → open key sig → tonality switch → panel-population check → search queries → playback matrix → sparse-passage layout → dense-passage layout — but the planner can re-order).
- Phrasing of the per-row case in the plan (e.g., "Place `Sharp +50` on a C5 → expect tuner reads ~+150¢ above C natural" vs. terser variants).
- Whether `03-VERIFICATION.md` table columns include a "Dorico build version" cell (recommended) and a "Notes" cell (recommended) on top of expected/observed/pass-fail.
- Whether to include `xmllint --noout cents.doricolib` as an explicit pre-import sanity check before opening Dorico (recommended — Pitfall 4 defense, costs nothing).
- Format for recording the dense-passage Engrave-mode workaround (if needed) — inline in `03-VERIFICATION.md` or as a TODO for Phase 4 README.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project locks (NOT to be re-litigated)
- `.planning/PROJECT.md` — locked decisions: tonality named "cents", 12-EDO temperament, ±99¢ around natural/sharp/flat ≈600 accidentals, always-signed labels, deterministic UUIDs. "Out of Scope" line excluding the bundled sample test score is what makes D-01 (no scaffold) the right call.
- `.planning/REQUIREMENTS.md` — 5 phase-3 requirements: PLAY-02, PLAY-03, UX-01, UX-02, UX-03. The exact wording in PLAY-03 and UX-02 enumerates the named spot-check matrix and the four search queries — Phase 3's plan must mirror them verbatim.
- `.planning/ROADMAP.md` §"Phase 3: Dorico Import + Playback Validation" — phase goal + 3 success criteria. Success criterion 3 explicitly names the dense-passage chord (`Sharp -50` + `Natural +50` + `Flat +50` on a single beat) and the Engrave-mode workaround clause that backs the D-03 cosmetic-only exception.
- `.planning/STATE.md` §"Accumulated Context" — Phase 1+2 deliverable md5s, three-class dispatcher, helper formula, total entity count (1411), the phase-3 open-question pair (panel-search ergonomics + dense-passage collision behavior).

### Research (load on planning)
- `.planning/research/PITFALLS.md` §"Pitfall 1" — off-by-100 trap; `Sharp +50` should play at +150¢ from natural, `Flat -7` at -107¢. The named cases in PLAY-03 are the diagnostic spot-checks for this trap.
- `.planning/research/PITFALLS.md` §"Pitfall 3" — silent text-component drop on import; if a tonality system imports but accidentals play at standard pitch, this is the suspect. Tuner check is the only way to detect.
- `.planning/research/PITFALLS.md` §"Pitfall 4" — `DefaultLibraryAdditions/` parse-failure-on-launch; Library Manager is the safer first-import path. `xmllint --noout` is the cheap pre-flight (referenced in D-05 Claude's Discretion).
- `.planning/research/PITFALLS.md` §"Pitfall 5" — open/atonal key signature is the #1 silent failure. Phase 3 plan's first action MUST be Shift+K → `open` (D-01).
- `.planning/research/PITFALLS.md` §"Pitfall 6" — re-import behavior; locked entity keys (`sharp`, `flat`, `natural`, `<base><signed-cents>`) and pinned `PROJECT_NAMESPACE`. The D-03 fix loop must NOT rename keys or rotate the namespace.
- `.planning/research/PITFALLS.md` §"Pitfall 8" — Natural absent from AccidentalSystem causes crash; the structural test (`tests/test_cents_structural.py`) already defends, Phase 3 is the empirical confirmation that note input doesn't crash.
- `.planning/research/PITFALLS.md` §"Pitfall 9" — accidentals can't move vertically; `(-8, -12)` Class B / `(18, -12)` Class C offsets are library-wide. Dense-passage collisions are expected and addressable only via Engrave mode (per-note adjust).
- `.planning/research/PITFALLS.md` §"Pitfall 10" — enharmonic-equivalent behavior; `Sharp -50` and `Natural +50` should play the same absolute pitch and remain visually distinct in the panel.
- `.planning/research/PITFALLS.md` §"Pitfall 12" — third-party VST microtonal compatibility; HALion and NotePerformer confirmed cent-accurate. D-02 picks HALion as the sign-off engine because it's stock and confirmed.
- `.planning/research/PITFALLS.md` §"Pitfall-to-Phase Mapping" — Phase 3 owns Pitfalls 1, 3, 4 (recovery test), 8, 9, 10, 12. The plan should organize spot-checks against this list.
- `.planning/research/PITFALLS.md` §"Recovery Strategies" — pitch-delta off-by-100 fix path: "Fix the helper, re-run generator with same `PROJECT_NAMESPACE` (entityIDs unchanged → in-place update). Existing notes update silently." This is the D-03 loop in operational form.
- `.planning/research/FEATURES.md` §"Q1 — Inside-Dorico user experience" — the panel UX (Key Signatures, Tonality Systems, and Accidentals panel; sort by pitch delta; search by name substring; click-to-apply). Defines what UX-01/UX-02 are testing against.
- `.planning/research/FEATURES.md` §"Q2 — Naming conventions" — confirms the search semantics that UX-02's four named queries are testing (`+14` → all three +14 variants; `Sharp -` → all sharp-side negatives; `Flat +50` → one entry; `Natural` → the zero-dev natural plus all natural-base entries).
- `.planning/research/FEATURES.md` §"Q3 — Key signature support" — open/atonal hard gate; the Phase 3 plan's first action.

### Working anchor
- `cents.doricolib` (repo root) — the production artifact under test. md5 `4cd707d2f4b10154a528b95e2ff5db9f`. Phase 3 must NOT modify it directly; any change is via re-emission from Phase 2 modules through `python build.py --out cents.doricolib`.
- `TonalitySystemStartTemplate.doricolib` (repo root) — Phase 1 hand-validated reference; not directly under test in Phase 3 but available as a known-good comparison if Library Manager misbehaves.

### Phase 1 + 2 implementation (untouched in Phase 3 unless D-03 loop triggers)
- `src/cents_generator/pitch.py` — `pitch_delta_numerator(base, cents)`. The off-by-100 trap defense; if PLAY-03 spot-checks reveal a math error, this is the first suspect.
- `src/cents_generator/compose.py` — `build_class_a/b/c()`, `_glyph_for()`, `_text_for()`. If a class-dispatch error surfaces (e.g., zero-dev `Sharp` rendering with a label), fix here.
- `src/cents_generator/emit.py` — XML formatters. If Dorico imports but a field is silently dropped (Pitfall 3, Pitfall 7), suspect formatting drift here.
- `src/cents_generator/main.py` — `build_cents_full_sweep()` and orchestrator dedup. If panel shows wrong total or missing entries, suspect orchestrator dedup.
- `src/cents_generator/uuids.py` — `PROJECT_NAMESPACE` (LOCKED FOREVER), `entity_id(kind, key)`. Phase 3 NEVER touches this; D-03 loop NEVER rotates the namespace.
- `src/cents_generator/constants.py` — section order, codepoints, font references. Phase 3 NEVER touches.
- `src/cents_generator/entities.py` — frozen dataclasses. Phase 3 NEVER touches absent a structural-schema bug, which would be a much bigger issue than D-03 covers.
- `tests/test_pitch.py`, `tests/test_cents_structural.py`, `tests/test_cents_snapshot.py`, `tests/test_determinism.py`, `tests/test_template_roundtrip.py`, `tests/test_uuid_snapshot.py` — the 133-test net. The D-03 loop adds a regression test for any failure before re-emission.

### Phase 2 prior context
- `.planning/phases/02-range-expansion-to-99/02-CONTEXT.md` — Phase 2 decisions (D-01 all-empty glyph parents, D-02 pitch-delta-ascending ID order, D-05 zero-dev key strings LOCKED FOREVER, D-06 helper formula, D-07 test layering). Phase 3 builds on these without revisiting.
- `.planning/phases/02-range-expansion-to-99/02-VERIFICATION.md` — Phase 2 verification template the Phase 3 verification will mirror in structure.
- `.planning/phases/02-range-expansion-to-99/02-{01,02,03}-SUMMARY.md` — Phase 2 plan SUMMARYs; useful context if a Phase 3 failure traces back to a specific Phase 2 plan.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`cents.doricolib` at repo root (1,261,618 bytes, md5 `4cd707d2f4b10154a528b95e2ff5db9f`)** — Phase 3's input. The user imports this exact file; re-emit only on D-03 loop trigger.
- **`python build.py --out cents.doricolib`** — re-emission CLI (D-04 from Phase 2). The D-03 loop's standard re-build incantation.
- **`xmllint --noout cents.doricolib`** — Pitfall 4 pre-flight (well-formedness sanity check before Library Manager import). Available in macOS by default. Phase 3 plan should include this as a one-line check.
- **133-test pytest suite** — the existing test net is the regression floor for the D-03 loop. Any Phase 3 failure adds a test before the fix lands.

### Established Patterns
- **Determinism contract is the iteration safety net.** Same `PROJECT_NAMESPACE` + same key strings → same UUIDs → re-imports update existing entities in-place (Pitfall 6 mitigation). This is why D-03 can promise "fix → re-emit → re-import" without breaking notes already placed in the user's test project.
- **Phase 1+2 verification artifact pattern (`{NN}-VERIFICATION.md`)** — Phase 3 mirrors this rather than inventing a new artifact name (D-04).
- **Plan SUMMARY per plan** — if Phase 3 splits into multiple plans (D-05 second variant), each plan still gets a SUMMARY mirroring Phase 1+2 convention.

### Integration Points
- **Library Manager** is the validated import path (Pitfall 4 defense; Library Manager fails gracefully, `DefaultLibraryAdditions/` fails fatally). Phase 3 uses Library Manager exclusively; `DefaultLibraryAdditions/` is a Phase 4 README concern, not a Phase 3 test.
- **HALion (Dorico stock sounds)** is the sole playback engine under test (D-02). Plan must NOT include any patch-load or VST configuration steps beyond Dorico defaults.
- **The user's installed Dorico Pro 6.x on macOS** is the test bench. Phase 3 records the exact Dorico build version (e.g., 6.2.20) in `03-VERIFICATION.md` for Phase 4 README citation.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly rejected even a markdown protocol document. The plan IS the protocol — whatever the planner emits must be tickable as a checklist directly without a separate walkthrough artifact.
- The named PLAY-03 cases (`Sharp +50` plays +150¢, `Flat -7` plays -107¢, boundaries `Sharp +99`, `Flat -99`, `Natural ±99`, enharmonic `Sharp -50` ≡ `Natural +50`) are the off-by-100 trap diagnostic surface. They MUST appear verbatim in the plan — no "etc.", no sampling.
- The four UX-02 search queries (`+14`, `Sharp -`, `Flat +50`, `Natural`) MUST appear verbatim with their expected match counts (e.g., `+14` → 3 matches: `Natural +14`, `Sharp +14`, `Flat +14`; `Flat +50` → 1 match) so the user can ✓ or ✗ each one without computing the expected count themselves.
- The dense-passage chord (UX-03) is exactly `Sharp -50` + `Natural +50` + `Flat +50` on a single beat — three notes that produce two distinct sounding pitches (the first two are enharmonic at +50¢ from natural; `Flat +50` is at -50¢). The "documented with Engrave-mode workaround if collisions occur" clause from ROADMAP success criterion 3 is the exact escape hatch D-03's cosmetic-only carve-out invokes.
- HALion is "Dorico's stock playback engine" — no extra purchase, no setup. The user has it the moment Dorico is installed. This is the practical reason D-02 lands on HALion-only and why Phase 3 does NOT include "install / configure HALion" as a step.

</specifics>

<deferred>
## Deferred Ideas

### Carried out of scope to other phases
- **Generated `.dorico` test project / `cents-test.dorico` deliverable** → v2 (DIFF-01 in REQUIREMENTS.md). User-rejected for v1 in this discussion (D-01).
- **NotePerformer empirical re-validation** → out of v1. Phase 4's README cites NotePerformer as confirmed cent-accurate based on Scoring Notes' published commentary, not on our re-test (D-02).
- **Markdown step-by-step `03-VALIDATION-PROTOCOL.md`** → user rejected; the Phase 3 plan IS the protocol (D-01).
- **Formal `03-VALIDATION-REPORT.md` separate from VERIFICATION.md** → not adopted; standard `03-VERIFICATION.md` carries results (D-04).
- **HALion patch-specific tuning notes** (e.g., "load the Steinway D piano for sustained tones to make tuner reading easier") — Claude's discretion if the planner thinks it matters; otherwise Phase 4 README troubleshooting can pick this up.
- **`DefaultLibraryAdditions/` install-path validation** → Phase 4 (README packaging). Phase 3 uses Library Manager exclusively per Pitfall 4.
- **Open-key-signature gating documentation prose** → Phase 4 (README). Phase 3's plan only references the action ("Shift+K → `open`") in checklist form.
- **Engrave-mode dense-passage workaround documentation** → Phase 4 (README troubleshooting). Phase 3's `03-VERIFICATION.md` notes whether the workaround is needed; Phase 4 writes the prose.
- **Cross-tonality-system invisible-accidentals behavior** (Pitfall 6 user-facing variant) → Phase 4 (README). Out of Phase 3 scope; the user is testing within a single tonality system.
- **Re-import duplicate-detection test** (Pitfall 2 + 6) — could be folded into Phase 3 as "import twice and verify panel still shows 597, not 1194" but is determinism-already-asserted by `tests/test_determinism.py`. Planner's call whether to add as a belt-and-braces empirical check.

### Discussion stayed within phase scope
No scope-creep redirects emerged. User explicitly trimmed scope (D-01 dropped the protocol document and the test scaffold; D-02 dropped NotePerformer) — the phase narrowed during discussion rather than widened.

</deferred>

---

*Phase: 3 - Dorico Import + Playback Validation*
*Context gathered: 2026-05-02*
