---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-05-02T03:00:00.000Z"
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 6
  completed_plans: 5
  percent: 83
---

# State: Cents — Custom Tonality System for Dorico

**Last updated:** 2026-05-02 (after Phase 02 Plan 02 execution — cents-mode emission sweep)

## Project Reference

- **Project:** Cents — Custom Tonality System for Dorico
- **Core value:** A Dorico user can import the file, write any pitch to ±1 cent of accuracy using familiar accidental glyphs plus a cent label, and Dorico plays it back at that exact cent.
- **Project doc:** `.planning/PROJECT.md`
- **Requirements:** `.planning/REQUIREMENTS.md` (30 v1 requirements across 7 categories)
- **Roadmap:** `.planning/ROADMAP.md` (4 phases)
- **Research:** `.planning/research/` (SUMMARY, STACK, FEATURES, ARCHITECTURE, PITFALLS)
- **Current focus:** Phase 02 — range-expansion-to-99

## Current Position

Phase: 02 (range-expansion-to-99) — EXECUTING
Plan: 3 of 3

- **Phase:** 2 — Range Expansion to ±99¢
- **Plan:** 02 complete (`build_cents_full_sweep()` orchestrator over `(natural, sharp, flat) × {0} ∪ ±1..±99¢`; `--mode {cents,template}` CLI flag default `cents`; mode-aware glyph spec D-01 cents-mode all-empty parents preserving Phase 1 D-03 round-trip via `--mode template`; locked cents-mode keys per D-05; production `cents.doricolib` emits 1.26 MB / 1398 top-level entities). 12 of 13 Phase 2 requirements satisfied (TON-01..06, VIS-01..05, PLAY-01); next is Plan 02-03 (test net + repo-root artifact)
- **Status:** Executing Phase 02
- **Progress:** [████████░░] 83%

```
[done] Phase 1: Generator Skeleton + Template Round-Trip   ← complete
[····] Phase 2: Range Expansion to ±99¢                    ← Plans 1-2 done; Plan 3 (test net) is next
[····] Phase 3: Dorico Import + Playback Validation
[····] Phase 4: README + Packaging
```

Overall: 1/4 phases complete (25%)

## Performance Metrics

- **v1 requirements mapped:** 30/30 (100%)
- **Phases complete:** 1/4
- **Plans complete in Phase 01:** 3/3 (Plan 01-01 — 5.6min; Plan 01-02 — 5.5min; Plan 01-03 — 5.2min)
- **Plans complete in Phase 02:** 2/3 (Plan 02-01 — 1.7min, 12 tests added, 2 files created; Plan 02-02 — ~8min, 9 new tests, 8 files modified, 0 created)
- **Code review depth:** standard (per config.json)
- **Phase 01 deliverable:** 9057-byte `.doricolib` byte-identical to TonalitySystemStartTemplate.doricolib (modulo entityIDs); 81 tests pass; md5 = `5f207c1de7f8ddf7f0af678384828cd4`
- **Phase 02 Plan 01 deliverable:** `src/cents_generator/pitch.py` (59 lines, stdlib only) + `tests/test_pitch.py` (80 lines, 12 tests). 93/93 tests pass (81 Phase 1 + 12 new). Zero Phase 1 files modified.
- **Phase 02 Plan 02 deliverable:** `build_cents_full_sweep()` in main.py (~155 added lines) + mode-aware `_glyph_for` in compose.py (+41 lines) + locked cents-mode constants in constants.py (+27 lines) + `--mode {cents,template}` CLI default cents. Production `cents.doricolib`: 1,261,618 bytes, md5 `4cd707d2f4b10154a528b95e2ff5db9f`, 597 AccidentalDefinitions / 198 TextDefinitions / 3 GlyphDefinitions / 597 CompositeDefinitions / 1+1+1 singletons (1398 top-level entities). xmllint passes. Cross-PYTHONHASHSEED determinism verified. Full suite 102/102 (81 Phase 1 + 12 Plan 02-01 + 9 Plan 02-02). Phase 1 byte-faithful round-trip preserved via `--mode template` (D-03).

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

- **Last action:** Plan 02-02 executed (commits `78120e2` Task-1 RED + `69a494f` Task-1 GREEN + `ce80b3d` Task-2). Modified `src/cents_generator/main.py` to add `build_cents_full_sweep()` returning the same 7-tuple shape as `build_template_three()` for the production sweep over `(natural, sharp, flat) × {0} ∪ ±1..±99¢`; `run()` widened to `run(out_path, mode='cents'|'template')`; `main()` argparse grew `--mode {cents,template}` flag with default `cents` (D-04). Modified `src/cents_generator/compose.py` to split `_GLYPH_SPEC` into `_GLYPH_SPEC_TEMPLATE` (Phase 1 quirk: Natural inherits `glyph.accidentalNatural`) and `_GLYPH_SPEC_CENTS` (D-01: all-empty parents); `_glyph_for(base, *, mode)` selects the right spec; `build_class_a` and `build_class_b` accept `mode` kwarg with default `'cents'` and propagate. Modified `src/cents_generator/constants.py` to add locked cents-mode keys `KEY_TEMPERAMENT_12EDO_CENTS='12-edo'`, `KEY_ACC_SYSTEM_CENTS='cents'`, `KEY_TONALITY_CENTS='cents'` plus `CENTS_RANGE_NONZERO` (198-tuple) under a LOCK FOREVER comment block (D-05 + Pitfall 6). Updated 13 test callsites across `tests/test_template_roundtrip.py` (7), `tests/test_uuid_snapshot.py` (1), `tests/test_determinism.py` (4 + 1 subprocess args list), `tests/test_compose.py` (1 + 9 new mode-aware tests), and `tests/test_emit_format.py` (1 helper, Rule 1 deviation). 12 of 13 Phase 2 requirements satisfied (all TON-* + all VIS-* + PLAY-01); GEN-05 was already closed in Plan 02-01. Production `cents.doricolib` emits 1,261,618 bytes with 597 AccidentalDefinitions, 198 TextDefinitions, 3 GlyphDefinitions, 597 CompositeDefinitions, 1+1+1 singletons (md5 `4cd707d2f4b10154a528b95e2ff5db9f`). xmllint --noout passes. Cross-PYTHONHASHSEED determinism verified (12345 vs 99999 → byte-identical). Full pytest suite green at 102/102. Phase 1 byte-faithful round-trip preserved via `--mode template` (D-03).
- **Next action:** Plan 02-03 — test net for cents mode (structural invariants per D-07.2 + sampled byte snapshots per D-07.3 + cents-mode UUID pins + cents-mode determinism per D-07.5) + emit production `cents.doricolib` artifact at repo root. The test net asserts: total entity count, exactly 597 AccidentalDefinitions / 198 TextDefinitions / 3 GlyphDefinitions / 597 CompositeDefinitions, single `<name>cents</name>` for AccidentalSystem and TonalitySystemDefinition, all three zero-dev entityIDs (Sharp/Flat/Natural) appear in `<accidentalDefinitionIDs>` (Pitfall 8), section ordering matches `SECTION_ORDER`, ~6-10 sampled byte snippets pinning the off-by-100 diagnostic cases, well-formed XML.
- **Resumption hint:** All context is in `.planning/`. `build_cents_full_sweep()` is callable; CLI surface stable at `python build.py [--mode {cents,template}] [--out PATH]`. Phase 02 decisions remain locked in `.planning/phases/02-range-expansion-to-99/02-CONTEXT.md`. Plan 02-02 SUMMARY at `.planning/phases/02-range-expansion-to-99/02-02-SUMMARY.md`. Note: STATE/CONTEXT/ROADMAP claim "1411 entities" but the actual top-level entity-definition count is 1398 (the 13-entity discrepancy is documentation arithmetic counting inline structural elements; implementation matches the must-haves' explicit per-section counts).

---
*State initialized: 2026-05-01*
