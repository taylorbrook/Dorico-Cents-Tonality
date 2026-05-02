---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-05-02T05:17:49.784Z"
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 11
  completed_plans: 9
  percent: 82
---

# State: Cents — Custom Tonality System for Dorico

**Last updated:** 2026-05-02 (after Phase 04 Plan 01 execution — DIST-01 closed, README.md shipped at repo root)

## Project Reference

- **Project:** Cents — Custom Tonality System for Dorico
- **Core value:** A Dorico user can import the file, write any pitch to ±1 cent of accuracy using familiar accidental glyphs plus a cent label, and Dorico plays it back at that exact cent.
- **Project doc:** `.planning/PROJECT.md`
- **Requirements:** `.planning/REQUIREMENTS.md` (30 v1 requirements across 7 categories)
- **Roadmap:** `.planning/ROADMAP.md` (4 phases)
- **Research:** `.planning/research/` (SUMMARY, STACK, FEATURES, ARCHITECTURE, PITFALLS)
- **Current focus:** Phase 04 — readme-packaging

## Current Position

Phase: 04 (readme-packaging) — EXECUTING
Plan: 2 of 3

- **Phase:** 4
- **Current Plan:** 2
- **Total Plans in Phase:** 3
- **Status:** Executing Phase 04 (Plan 04-01 complete; Plan 04-02 next in Wave 1)
- **Progress:** [████████░░] 82%

```
[done] Phase 1: Generator Skeleton + Template Round-Trip   ← complete
[done] Phase 2: Range Expansion to ±99¢                    ← complete (all 3 plans)
[done] Phase 3: Dorico Import + Playback Validation        ← complete (all 2 plans)
[wip ] Phase 4: README + Packaging                         ← in progress (1/3 plans)
```

Overall: 3/4 phases complete (75%); 9/11 plans complete (82%)

## Performance Metrics

- **v1 requirements mapped:** 30/30 (100%)
- **Phases complete:** 3/4
- **Plans complete in Phase 01:** 3/3 (Plan 01-01 — 5.6min; Plan 01-02 — 5.5min; Plan 01-03 — 5.2min)
- **Plans complete in Phase 02:** 3/3 (Plan 02-01 — 1.7min, 12 tests added, 2 files created; Plan 02-02 — ~8min, 9 new tests, 8 files modified, 0 created; Plan 02-03 — ~7min, 31 new tests, 3 files created, 1 modified)
- **Plans complete in Phase 03:** 2/2 (Plan 03-01 — UX-01/UX-02 manual validation pass; Plan 03-02 — PLAY-02/PLAY-03/UX-03 12-row HALion matrix pass)
- **Plans complete in Phase 04:** 1/3 (Plan 04-01 — 1m 29s, README.md authored, 126 lines, 26/26 acceptance gates pass; commit `437b38a`)
- **Code review depth:** standard (per config.json)
- **Phase 01 deliverable:** 9057-byte `.doricolib` byte-identical to TonalitySystemStartTemplate.doricolib (modulo entityIDs); 81 tests pass; md5 = `5f207c1de7f8ddf7f0af678384828cd4`
- **Phase 02 Plan 01 deliverable:** `src/cents_generator/pitch.py` (59 lines, stdlib only) + `tests/test_pitch.py` (80 lines, 12 tests). 93/93 tests pass (81 Phase 1 + 12 new). Zero Phase 1 files modified.
- **Phase 02 Plan 02 deliverable:** `build_cents_full_sweep()` in main.py (~155 added lines) + mode-aware `_glyph_for` in compose.py (+41 lines) + locked cents-mode constants in constants.py (+27 lines) + `--mode {cents,template}` CLI default cents. Cross-PYTHONHASHSEED determinism verified. Full suite 102/102 (81 Phase 1 + 12 Plan 02-01 + 9 Plan 02-02). Phase 1 byte-faithful round-trip preserved via `--mode template` (D-03).
- **Phase 02 Plan 03 deliverable:** Production `cents.doricolib` shipped at repo root (1,261,618 bytes, md5 `4cd707d2f4b10154a528b95e2ff5db9f`). Test net: 31 new tests across `tests/test_cents_structural.py` (12 tests, 289 lines) + `tests/test_cents_snapshot.py` (16 tests, 578 lines, 22 pinned UUIDs + 10 byte-faithful snippet snapshots) + `tests/test_determinism.py` extension (3 cents-mode tests appended). Full suite 133/133. Production-scale determinism end-to-end verified (`diff cents.doricolib /tmp/cents-rerun.doricolib` exits empty). All 13 Phase 2 requirements (GEN-05, TON-01..06, VIS-01..05, PLAY-01) closed.
- **Phase 04 Plan 01 deliverable:** `README.md` at repo root (126 lines, MIT-described). Ten DIST-01 sections in canonical order: title + tagline; Requirements (Dorico Pro 6.0+ front-loaded); Package Contents (597 entries cited); Library Manager primary install; DefaultLibraryAdditions power-user install with `remove if Dorico fails to launch` recovery instruction; first-note walkthrough leading with Shift+K → "open" key signature step; Naming Convention with 7-row examples table (Sharp +14 / Flat -50 / Natural -7 / Sharp -50); Troubleshooting with four subsections (open-key-sig → VST limits → font.defaulttext → re-import); Compatibility matrix (Dorico Pro 6.0–6.2.x YES, Dorico 5/Elements/SE excluded; fileVersion 1.1450); License (LICENSE link). All 26 acceptance gates (22 grep + 1 line-count + 4 awk-ordering) passed. DIST-01 closed.

## Accumulated Context

### Key decisions (carried from PROJECT.md / research)

- **Stack:** Python 3.11+ stdlib only (`xml.etree.ElementTree`, `uuid`, `fractions`, `pathlib`, `argparse`); no third-party runtime deps.
- **Determinism:** `uuid.uuid5(PROJECT_NAMESPACE, key)` exclusively. `PROJECT_NAMESPACE` pinned once, never rotated.
- **Schema:** `<fileVersion>1.1450</fileVersion>`, `<kScoreLibrary>` root; seven canonical sections in Dorico's own export order; tab indent, lowercase booleans, raw `n/1200` rationals, `0xE262` capital-X hex, six-decimal float strings, comma-space CSV ID lists, self-closing empty arrays.
- **Three-class composite dispatcher:** Class A (glyph-only) for zero-deviation; Class B (glyph + text via `relativeAttachment` `(-8, -12)`) for sharp/flat-base non-zero; Class C (text-only at `xOffset/yOffset = (18, -12)`) for natural-base non-zero.
- **Pitch math:** `pitch_delta_numerator(base, cents) = {natural: 0, sharp: 100, flat: -100}[base] + cents` — centralized to defeat the off-by-100 trap.
- **Total entity count:** 1411 = 1 Temperament + 1 AccidentalSystem + 1 TonalitySystem + 597 AccidentalDefinitions + 597 CompositeDefinitions + 3 Glyphs + 198 Texts.
- **Validation:** manual import into Dorico Pro 6.x + tuner spot-check; no automated headless validation possible (Dorico has no headless mode).

### Critical pitfalls to address by phase

- **Phase 1:** non-deterministic UUIDs (Pitfall 2 — CRITICAL); silent text-component drop on import (Pitfall 3 — CRITICAL); XML formatting drift (Pitfall 7 — HIGH); forward-reference confusion (Pitfall 13).
- **Phase 2:** off-by-100 in `pitchDeltaFromNatural` (Pitfall 1 — CRITICAL, the math trap lives here); Natural accidental must be present in AccidentalSystem (Pitfall 8).
- **Phase 3:** physical playback verification (Pitfall 1, 3); dense-passage collisions (Pitfall 9); enharmonic-equivalent behavior (Pitfall 10); HALion-specific validation (Pitfall 12).
- **Phase 4:** open-key-signature gotcha leads README (Pitfall 5 — HIGH); `DefaultLibraryAdditions/` launch-crash warning (Pitfall 4 — HIGH); re-import behavior (Pitfall 6); font override caveat (Pitfall 11); third-party VST limits (Pitfall 12).

### TODOs

- (none yet — accumulates as phases execute)

### Blockers

- (none)

### Open questions

- Panel-search ergonomics at 597 entries is empirically unverified at this scale (no published Dorico tonality system has reached this density). Validated in Phase 3.
- Cent-label collision behavior in dense microtonal chords. Validated in Phase 3.

## Session Continuity

- **Last action:** Plan 04-01 executed (commit `437b38a` — `docs(04-01): author user-facing README.md (DIST-01)`). Created `README.md` at repo root (126 lines) with all ten DIST-01 sections in canonical order: title + tagline; Requirements (Dorico Pro 6.0+ front-loaded as first heading); Package Contents (597 entries); Library Manager primary install with Dorico Pro 6.2.2 validation citation; DefaultLibraryAdditions power-user install with literal `remove if Dorico fails to launch` recovery instruction (T-04-01 mitigation); first-note walkthrough leading with Shift+K → "open" key signature step (Pitfall 5 defense); Naming Convention 7-row examples table (Sharp +14 / Flat -50 / Natural -7 / Sharp -50); Troubleshooting with four subsections in priority order (open-key-sig → VST instrument table with HALion/NotePerformer confirmed and Kontakt/SWAM/Falcon caveat → font.defaulttext caveat → re-import determinism); Compatibility matrix (Dorico Pro 6.0–6.2.x YES; Dorico 5 / Elements / SE excluded; fileVersion 1.1450 cited); License (MIT, LICENSE file linked, Copyright (c) 2026 Taylor Brook). All 26 acceptance gates passed (22 literal-string grep + 1 line-count ≥100 + 4 awk-ordering); verify chain prints `README ACCEPTANCE PASSED`. Zero deviations from plan text — heading text was treated as load-bearing per plan and preserved verbatim. DIST-01 requirement marked complete in REQUIREMENTS.md.
- **Next action:** Plan 04-02 (DIST-02 — MIT LICENSE at repo root, Copyright (c) 2026 Taylor Brook). Wave 1 parallel sibling of 04-01; no shared files. After 04-02 lands, Plan 04-03 (DIST-03 — non-autonomous: user runs README install + first-note walkthrough on their macOS Dorico Pro 6.x install).
- **Resumption hint:** Phase 4 in progress (1/3 plans complete). README at `/Users/taylorbrook/Dev/dorico tonality/README.md`. SUMMARY at `.planning/phases/04-readme-packaging/04-01-SUMMARY.md`. The README acts as the contractual user-facing doc for the full v1 ship — its troubleshooting + compatibility content is what mitigates T-04-01/02/03 (DoS via launch crash, repudiation via unsupported edition, false playback expectation). LICENSE file referenced in §10 must exist before v1 ships — Plan 04-02 closes that loop.

---
*State initialized: 2026-05-01*
