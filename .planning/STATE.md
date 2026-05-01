---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: completed
last_updated: "2026-05-01T23:56:04.340Z"
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
  percent: 100
---

# State: Cents — Custom Tonality System for Dorico

**Last updated:** 2026-05-01 (after Plan 01-03 — Phase 01 complete)

## Project Reference

- **Project:** Cents — Custom Tonality System for Dorico
- **Core value:** A Dorico user can import the file, write any pitch to ±1 cent of accuracy using familiar accidental glyphs plus a cent label, and Dorico plays it back at that exact cent.
- **Project doc:** `.planning/PROJECT.md`
- **Requirements:** `.planning/REQUIREMENTS.md` (30 v1 requirements across 7 categories)
- **Roadmap:** `.planning/ROADMAP.md` (4 phases)
- **Research:** `.planning/research/` (SUMMARY, STACK, FEATURES, ARCHITECTURE, PITFALLS)
- **Current focus:** Phase 01 — generator-skeleton-template-round-trip

## Current Position

Phase: 1 — COMPLETE
Plan: 3 of 3 complete; Phase 01 closed; next phase: 02 (range expansion to ±99¢)

- **Phase:** 1 — Generator Skeleton + Template Round-Trip
- **Plan:** 03 complete (orchestrator + CLI + round-trip + determinism + UUID snapshot tests); Phase 01 closed
- **Status:** Phase 1 complete
- **Progress:** [██████████] 100%

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
- **Code review depth:** standard (per config.json)
- **Phase 01 deliverable:** 9057-byte `.doricolib` byte-identical to TonalitySystemStartTemplate.doricolib (modulo entityIDs); 81 tests pass; md5 = `5f207c1de7f8ddf7f0af678384828cd4`

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

- **Last action:** Plan 01-03 complete — orchestrator + CLI shipped (`python build.py --out cents.doricolib`), byte-faithful round-trip vs. TonalitySystemStartTemplate.doricolib proven, two-run determinism proven across in-process and subprocess paths, UUID snapshot pinned for all 13 entityIDs. 81 tests pass (18 new). All four Phase 01 success criteria are proven by passing tests. Phase 01 closed.
- **Next action:** Begin Phase 02 — range expansion to ±99¢ (parameter sweep over `(natural, sharp, flat) × range(-99, 100)`; introduces `pitch_delta_numerator(base, cents)` to defeat Pitfall 1 off-by-100).
- **Resumption hint:** All context is in `.planning/` — load PROJECT.md → REQUIREMENTS.md → ROADMAP.md → research/SUMMARY.md to re-orient. Phase 01 implementation lives in `src/cents_generator/` (uuids, constants, entities, compose, emit, main); CLI is `build.py`; tests in `tests/`.

---
*State initialized: 2026-05-01*
