# Phase 3: Dorico Import + Playback Validation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-02
**Phase:** 3-dorico-import-playback-validation
**Areas discussed:** Test scaffold form, VST sign-off scope, Failure-handling policy, Results artifact format

---

## Test scaffold form

| Option | Description | Selected |
|--------|-------------|----------|
| Markdown protocol only (Recommended) | A `03-VALIDATION-PROTOCOL.md` document that walks the user through opening a fresh Dorico project, inserting an open key sig, switching to `cents`, and placing each spot-check accidental on a single staff one at a time. | |
| Generated `.dorico` test project | A Python tool (e.g., `tools/build_test_score.py`) that emits a `.dorico` file with all PLAY-03 spot-check notes pre-arranged on a chromatic-ish line plus the dense-passage chord. Higher leverage but `.dorico` is a binary-zip XML format — reverse-engineering is real work; PROJECT.md defers the bundled test score to v2. | |
| Hybrid: protocol + manual `.dorico` template | Markdown protocol drives placement; the user saves the resulting Dorico project once as `validation-scratch.dorico` (gitignored) so re-runs don't require re-placing every note. | |
| **Other (user-provided)** | "No test scaffold is needed, I'll just import it into a dorico project to test." | ✓ |

**User's choice:** No scaffold — neither code nor markdown protocol document. The Phase 3 plan IS the protocol; user works it against a Dorico project of their choice.
**Notes:** Trims Phase 3 scope further than the recommended option. Forces the planner to make the plan itself fully tickable as a checklist (cases enumerated verbatim, expected match counts pre-computed) since there's no separate walkthrough to lean on. Preserves PROJECT.md's "Out of Scope: bundled sample .dorico test score" line.

---

## VST sign-off scope

| Option | Description | Selected |
|--------|-------------|----------|
| HALion only (Recommended) | Dorico stock sounds. Confirmed cent-accurate per Pitfall 12. Zero extra setup — already there. If HALion plays correctly, library math is correct; third-party VST issues are downstream and Phase 4 documents them in README troubleshooting. | ✓ |
| HALion + NotePerformer | Both must pass. NotePerformer also confirmed cent-accurate (responds to VST micro-tuning messages per Scoring Notes). Doubles as broader confidence — only useful if the user owns NotePerformer and wants to claim it works in the README based on first-hand testing. | |
| HALion required, NotePerformer optional | HALion is the gate. NotePerformer is "nice if you have it" — if it works, the README can claim it; if not tested, README stays HALion-only. | |

**User's choice:** HALion only.
**Notes:** Phase 4 README will name HALion as the validated engine and reference NotePerformer as a separately-confirmed cent-accurate engine (per published Scoring Notes commentary) without our re-validation.

---

## Failure-handling policy

| Option | Description | Selected |
|--------|-------------|----------|
| Pause-and-fix loop (Recommended) | Stop Phase 3, diagnose root cause, fix in Phase 2's `compose.py` / `pitch.py` / `emit.py`, re-run `python build.py --out cents.doricolib`, re-import, re-test. Phase 3 doesn't close until every PLAY-03 + UX-01..03 check passes. Matches ROADMAP's "if validation surfaces issues, fix is name-format adjustment in Phase 2's compose.py". | ✓ |
| Capture-and-defer | Record failure in results doc and continue testing the rest. Spawn a separate Phase 2.5 patch phase for accumulated failures, then re-validate. | |
| Note-and-continue (cosmetic-only) | Pause-and-fix for math/playback failures (Pitfalls 1, 3, 8). For visual/UX issues only (collisions, search ergonomics) — capture in results doc as known limitation; Phase 4 README documents the workaround instead of looping. | |

**User's choice:** Pause-and-fix loop.
**Notes:** Determinism contract is the guardrail that makes the loop cheap — `PROJECT_NAMESPACE` and key strings stay locked, so re-imports update existing entities in-place rather than duplicating. CONTEXT.md D-03 carves out a single narrow exception for UX-03 dense-passage layout (the ROADMAP-sanctioned Engrave-mode workaround), keeping all playback / math / panel-population checks under hard pause-and-fix.

---

## Results artifact format

| Option | Description | Selected |
|--------|-------------|----------|
| Formal `03-VALIDATION-REPORT.md` (Recommended) | Committed to phase dir. Structured table per dimension. Each row: case → expected → measured → pass/fail → notes. Phase 4 README cites this directly. | |
| Inline in plan SUMMARY files | Each Phase 3 plan SUMMARY captures its slice of results. No separate report. Lighter, but Phase 4 stitches citations across files. | |
| Single VERIFICATION.md note | Phase 3 produces one VERIFICATION.md (standard GSD verifier output) with results inline. Mirrors Phase 1/2 pattern; no extra artifact. | ✓ |

**User's choice:** Single `03-VERIFICATION.md`.
**Notes:** Mirrors Phase 1's `VERIFICATION.md` and Phase 2's `02-VERIFICATION.md`. No new artifact type. Phase 4's README cites `03-VERIFICATION.md` for its "validated against HALion" claim. Generated by `/gsd-verify-phase` after the user signs off on every check.

---

## Claude's Discretion

- Exact within-plan ordering of spot-checks (sensible default: import → open key sig → tonality switch → panel-population → search queries → playback matrix → sparse-passage layout → dense-passage layout — planner may re-order).
- Per-row case phrasing in the plan ("Place `Sharp +50` on a C5 → expect tuner reads ~+150¢ above C natural" vs. terser variants).
- Whether `03-VERIFICATION.md` table includes "Dorico build version" and "Notes" columns (recommended: yes to both).
- Whether to include `xmllint --noout cents.doricolib` as an explicit pre-import sanity check (recommended: yes — Pitfall 4 defense, costs nothing).
- Format for recording the dense-passage Engrave-mode workaround if needed (inline in `03-VERIFICATION.md` vs. TODO for Phase 4 README).
- Plan splitting: one plan vs. two plans (UX-01/UX-02 split from PLAY-02/PLAY-03/UX-03). Planner picks based on cohesion. The user explicitly does NOT want artificial three-wave fan-out for what is a one-pass manual checklist.
- HALion patch choice for sustained-tone tuner reading (e.g., bowed string, organ) — Claude's discretion if planner thinks it matters; otherwise Phase 4 troubleshooting can pick this up later.

## Deferred Ideas

- Generated `.dorico` test project (`cents-test.dorico`) → v2 (DIFF-01).
- NotePerformer empirical re-validation → out of v1; Phase 4 README cites Scoring Notes' published commentary instead.
- Markdown step-by-step `03-VALIDATION-PROTOCOL.md` → user rejected; the Phase 3 plan IS the protocol.
- Formal `03-VALIDATION-REPORT.md` separate from VERIFICATION.md → not adopted; standard `03-VERIFICATION.md` is the canonical record.
- HALion patch-specific tuning notes → Claude's discretion or Phase 4 README troubleshooting.
- `DefaultLibraryAdditions/` install-path validation → Phase 4 (README packaging).
- Open-key-signature gating documentation prose → Phase 4 (README).
- Engrave-mode dense-passage workaround documentation → Phase 4 (README troubleshooting).
- Cross-tonality-system invisible-accidentals behavior (Pitfall 6 user-facing variant) → Phase 4 (README).
- Re-import duplicate-detection empirical check (Pitfall 2 + 6) → planner's call whether to add as belt-and-braces (already asserted by `tests/test_determinism.py`).

### Discussion stayed within phase scope
No scope-creep redirects emerged. The user trimmed scope further than the presented options on two questions (D-01 dropping the protocol document; D-02 dropping NotePerformer) — Phase 3 narrowed during discussion rather than widened.
