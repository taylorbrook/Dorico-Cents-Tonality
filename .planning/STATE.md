---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-05-02T01:31:14.019Z"
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 6
  completed_plans: 4
  percent: 67
---

# State: Cents — Custom Tonality System for Dorico

**Last updated:** 2026-05-02 (after Phase 02 Plan 01 execution — pitch_delta_numerator helper)

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
Plan: 2 of 3

- **Phase:** 2 — Range Expansion to ±99¢
- **Plan:** 01 complete (`pitch_delta_numerator` helper at `src/cents_generator/pitch.py` + 12 hand-calculated unit tests; Pitfall 1 defeated; GEN-05 satisfied); next is Plan 02 (cents-mode emission sweep)
- **Status:** Executing Phase 02
- **Progress:** [███████░░░] 67%

```
[done] Phase 1: Generator Skeleton + Template Round-Trip   ← complete
[····] Phase 2: Range Expansion to ±99¢                    ← next
[····] Phase 3: Dorico Import + Playback Validation
[····] Phase 4: README + Packaging
```

Overall: 1/4 phases complete (25%)

## Performance Metrics

- **v1 requirements mapped:** 30/30 (100%)
- **Phases complete:** 1/4
- **Plans complete in Phase 01:** 3/3 (Plan 01-01 — 5.6min; Plan 01-02 — 5.5min; Plan 01-03 — 5.2min)
- **Plans complete in Phase 02:** 1/3 (Plan 02-01 — 1.7min, 12 tests added, 2 files created)
- **Code review depth:** standard (per config.json)
- **Phase 01 deliverable:** 9057-byte `.doricolib` byte-identical to TonalitySystemStartTemplate.doricolib (modulo entityIDs); 81 tests pass; md5 = `5f207c1de7f8ddf7f0af678384828cd4`
- **Phase 02 Plan 01 deliverable:** `src/cents_generator/pitch.py` (59 lines, stdlib only) + `tests/test_pitch.py` (80 lines, 12 tests). 93/93 tests pass (81 Phase 1 + 12 new). Zero Phase 1 files modified.

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

- **Last action:** Plan 02-01 executed (commits `fe95617` RED + `164f6d3` GREEN). Created `src/cents_generator/pitch.py` exporting `pitch_delta_numerator(base, cents) -> int` returning `{natural: 0, sharp: 100, flat: -100}[base] + cents`. Created `tests/test_pitch.py` with 12 hand-calculated one-assertion tests pinning the D-06 cases plus the Sharp -50 / Natural +50 enharmonic invariant. Pitfall 1 (off-by-100 trap) defeated: helper is the only producer of computed pitch-delta numerators in `src/`. GEN-05 marked complete in REQUIREMENTS.md. Full pytest suite green at 93/93. Zero Phase 1 files modified (verified by `git diff --stat HEAD~2 HEAD`).
- **Next action:** Plan 02-02 — cents-mode emission sweep using the helper. Wires `from cents_generator.pitch import pitch_delta_numerator` into the Class A/B/C dispatcher; introduces `build_cents_full_sweep()` and the `--mode cents|template` CLI flag (D-04).
- **Resumption hint:** All context is in `.planning/`. The helper + tests live in `src/cents_generator/pitch.py` and `tests/test_pitch.py`; Plan 02-02 will read from these. Phase 02 decisions remain locked in `.planning/phases/02-range-expansion-to-99/02-CONTEXT.md`. Plan 02-01 SUMMARY at `.planning/phases/02-range-expansion-to-99/02-01-SUMMARY.md`.

---
*State initialized: 2026-05-01*
