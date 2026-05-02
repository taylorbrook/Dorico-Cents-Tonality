---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-05-02T02:43:52.199Z"
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 8
  completed_plans: 6
  percent: 75
---

# State: Cents — Custom Tonality System for Dorico

**Last updated:** 2026-05-02 (after Phase 02 Plan 03 execution — cents-mode test net + production cents.doricolib shipped)

## Project Reference

- **Project:** Cents — Custom Tonality System for Dorico
- **Core value:** A Dorico user can import the file, write any pitch to ±1 cent of accuracy using familiar accidental glyphs plus a cent label, and Dorico plays it back at that exact cent.
- **Project doc:** `.planning/PROJECT.md`
- **Requirements:** `.planning/REQUIREMENTS.md` (30 v1 requirements across 7 categories)
- **Roadmap:** `.planning/ROADMAP.md` (4 phases)
- **Research:** `.planning/research/` (SUMMARY, STACK, FEATURES, ARCHITECTURE, PITFALLS)
- **Current focus:** Phase 02 — range-expansion-to-99

## Current Position

Phase: 02 (range-expansion-to-99) — COMPLETE
Plan: 3 of 3 — DONE

- **Phase:** 3
- **Plan:** Not started
- **Status:** Ready to execute
- **Progress:** [██████████] 100%

```
[done] Phase 1: Generator Skeleton + Template Round-Trip   ← complete
[done] Phase 2: Range Expansion to ±99¢                    ← complete (all 3 plans)
[····] Phase 3: Dorico Import + Playback Validation       ← next
[····] Phase 4: README + Packaging
```

Overall: 2/4 phases complete (50%)

## Performance Metrics

- **v1 requirements mapped:** 30/30 (100%)
- **Phases complete:** 2/4
- **Plans complete in Phase 01:** 3/3 (Plan 01-01 — 5.6min; Plan 01-02 — 5.5min; Plan 01-03 — 5.2min)
- **Plans complete in Phase 02:** 3/3 (Plan 02-01 — 1.7min, 12 tests added, 2 files created; Plan 02-02 — ~8min, 9 new tests, 8 files modified, 0 created; Plan 02-03 — ~7min, 31 new tests, 3 files created, 1 modified)
- **Code review depth:** standard (per config.json)
- **Phase 01 deliverable:** 9057-byte `.doricolib` byte-identical to TonalitySystemStartTemplate.doricolib (modulo entityIDs); 81 tests pass; md5 = `5f207c1de7f8ddf7f0af678384828cd4`
- **Phase 02 Plan 01 deliverable:** `src/cents_generator/pitch.py` (59 lines, stdlib only) + `tests/test_pitch.py` (80 lines, 12 tests). 93/93 tests pass (81 Phase 1 + 12 new). Zero Phase 1 files modified.
- **Phase 02 Plan 02 deliverable:** `build_cents_full_sweep()` in main.py (~155 added lines) + mode-aware `_glyph_for` in compose.py (+41 lines) + locked cents-mode constants in constants.py (+27 lines) + `--mode {cents,template}` CLI default cents. Cross-PYTHONHASHSEED determinism verified. Full suite 102/102 (81 Phase 1 + 12 Plan 02-01 + 9 Plan 02-02). Phase 1 byte-faithful round-trip preserved via `--mode template` (D-03).
- **Phase 02 Plan 03 deliverable:** Production `cents.doricolib` shipped at repo root (1,261,618 bytes, md5 `4cd707d2f4b10154a528b95e2ff5db9f`). Test net: 31 new tests across `tests/test_cents_structural.py` (12 tests, 289 lines) + `tests/test_cents_snapshot.py` (16 tests, 578 lines, 22 pinned UUIDs + 10 byte-faithful snippet snapshots) + `tests/test_determinism.py` extension (3 cents-mode tests appended). Full suite 133/133. Production-scale determinism end-to-end verified (`diff cents.doricolib /tmp/cents-rerun.doricolib` exits empty). All 13 Phase 2 requirements (GEN-05, TON-01..06, VIS-01..05, PLAY-01) closed.

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

- **Last action:** Plan 02-03 executed (commits `be3d8a0` Task-1 structural-invariants tests + `c1cc472` Task-2 UUID pins + byte-faithful snippet snapshots + `2790422` Task-3 determinism extension + production cents.doricolib). Created `tests/test_cents_structural.py` (289 lines, 12 tests) asserting per-section counts (1+1+597+1+198+3+597 = 1398), tonality name 'cents', 12-EDO temperament divisions, section ordering, xmllint well-formedness, Pitfall 8 defense (all three zero-dev entityIDs in `<accidentalDefinitionIDs>`), D-02 pitch-delta ascending order, Pitfall 1 delta-count invariants, D-01 empty-parent on glyphs, fileVersion 1.1450. Created `tests/test_cents_snapshot.py` (578 lines, 16 tests) pinning 22 cents-mode entityIDs (3 singletons + 11 accidentals + 3 glyphs including Phase 1 cross-mode invariant + 6 texts) plus 5 AccidentalDefinition + 5 CompositeDefinition byte-faithful snippet snapshots covering Class A/B/C and the off-by-100 trap diagnostic cases (Sharp +14 → 114/1200, Sharp -50 → 50/1200, Flat -7 → -107/1200, Natural +50 → 50/1200, Sharp zero-dev → 100/1200). Modified `tests/test_determinism.py` to append 3 cents-mode determinism tests (in-process two-run, subprocess CLI two-run, diff-command two-run); existing 3 template-mode tests preserved verbatim. Emitted production `cents.doricolib` at repo root (1,261,618 bytes, md5 `4cd707d2f4b10154a528b95e2ff5db9f`); committed in Task-3's commit. Full pytest suite: 133/133 (102 + 31 new). [Rule 1 - Bug] deviation: corrected the 99/1200 / -99/1200 expected counts in test_cents_no_off_by_100_in_pitch_deltas from `== 1` (plan text) to `== 2` (correct math: Sharp -1 + Natural +99 both produce 99). All 13 Phase 2 requirements closed (GEN-05, TON-01..06, VIS-01..05, PLAY-01). Phase 1 byte-faithful round-trip preserved.
- **Next action:** Phase 02 closure. Run `/gsd-verify-phase` (verifier sweep) and/or `/gsd-uat-phase` (UAT sign-off), then `/gsd-transition` to advance into Phase 03 (Dorico Import + Playback Validation — manual import of `cents.doricolib` into the user's macOS Dorico Pro 6.x install + tuner spot-checks across the ±99¢ range + panel-search ergonomics + dense-passage collision evaluation + HALion/NotePerformer playback validation).
- **Resumption hint:** All context is in `.planning/`. Phase 2 closed; production `cents.doricolib` at repo root. `build_cents_full_sweep()` callable; CLI stable at `python build.py [--mode {cents,template}] [--out PATH]`. Phase 02 decisions locked in `.planning/phases/02-range-expansion-to-99/02-CONTEXT.md`. Plan SUMMARYs at `.planning/phases/02-range-expansion-to-99/02-{01,02,03}-SUMMARY.md`. The test net (133 tests) defends against off-by-100 (Pitfall 1), Natural-absent-from-AccidentalSystem (Pitfall 8), set-iteration non-determinism (Pitfall 15), and pinned-snapshot drift. Phase 3 will be physical Dorico import — no more code work in this layer until tuner spot-checks reveal pitch errors.

---
*State initialized: 2026-05-01*
