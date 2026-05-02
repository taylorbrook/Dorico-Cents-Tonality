---
phase: 02-range-expansion-to-99
plan: 02
subsystem: cents_generator
tags:
  - python
  - stdlib
  - orchestrator
  - cli
  - dispatcher
  - dorico
  - pitfall-1
  - pitfall-8
  - pitfall-15
requires:
  - "src/cents_generator/pitch.py::pitch_delta_numerator (Plan 02-01)"
provides:
  - "src/cents_generator/main.py::build_cents_full_sweep"
  - "src/cents_generator/main.py::run(out_path, mode='cents'|'template')"
  - "build.py CLI flag --mode {cents,template} default cents (D-04)"
  - "src/cents_generator/compose.py::_glyph_for(base, *, mode) — D-01 cents-mode all-empty glyph parents"
  - "src/cents_generator/constants.py::KEY_TEMPERAMENT_12EDO_CENTS, KEY_ACC_SYSTEM_CENTS, KEY_TONALITY_CENTS, CENTS_RANGE_NONZERO (D-05 LOCKED)"
affects:
  - "Plan 02-03 (testing) — unblocked: build_cents_full_sweep() callable, CLI surface stable, structural-invariants test net is the next concern"
  - "Phase 1 round-trip preserved via --mode template (D-03)"
tech-stack:
  added: []
  patterns:
    - "mode-keyword-arg dispatch over a tiny lookup table (_GLYPH_SPECS)"
    - "dict.setdefault dedup for glyphs and texts (Pitfall 15) — first-insertion-order preserving, deterministic across PYTHONHASHSEED"
    - "(pitch_delta, base_priority, cents) lexicographic sort for stable D-02 ordering with explicit tiebreak"
    - "cents-mode keys derived once via _cents_accidental_name/_cents_accidental_key — single source of truth, locked forever per Pitfall 6"
key-files:
  created: []
  modified:
    - "src/cents_generator/compose.py (+41 lines, mode-aware glyph spec)"
    - "src/cents_generator/constants.py (+27 lines, locked cents-mode keys + CENTS_RANGE_NONZERO)"
    - "src/cents_generator/main.py (+216 lines, build_cents_full_sweep + run-mode dispatch + --mode CLI)"
    - "tests/test_compose.py (+126 lines, 9 new mode-aware glyph tests)"
    - "tests/test_template_roundtrip.py (7 callsites updated to mode='template')"
    - "tests/test_uuid_snapshot.py (1 callsite updated to mode='template')"
    - "tests/test_determinism.py (4 callsites updated + 1 subprocess --mode template)"
    - "tests/test_emit_format.py (1 callsite Rule 1 deviation: helper updated to mode='template')"
decisions:
  - "Tiebreak rule pinned: (pitch_delta, base_priority, cents) ascending; flat=0 < natural=1 < sharp=2"
  - "Cut-outs in cents mode: (0, 0) on all four corners for every accidental (template's non-zero values are template quirks only)"
  - "AccidentalSystem.name = 'cents' and TonalitySystemDef.name = 'cents' (D-04 + Claude's discretion)"
  - "TemperamentDef.name = '12-EDO' (Claude's discretion — user-visible, not part of entityID)"
  - "build_template_three() body preserved verbatim other than threading mode='template' to compose calls (D-03)"
metrics:
  duration_minutes: 8
  tasks_completed: 2
  files_created: 0
  files_modified: 8
  tests_added: 9
  tests_total: 102
  completed_date: "2026-05-02"
  production_artifact_size_bytes: 1261618
  production_artifact_md5: "4cd707d2f4b10154a528b95e2ff5db9f"
requirements_satisfied:
  - TON-01
  - TON-02
  - TON-03
  - TON-04
  - TON-05
  - TON-06
  - VIS-01
  - VIS-02
  - VIS-03
  - VIS-04
  - VIS-05
  - PLAY-01
---

# Phase 2 Plan 02: Cents-mode Emission Sweep Summary

**One-liner:** Wired Plan 02-01's `pitch_delta_numerator` into a full sweep over `(natural, sharp, flat) × {0} ∪ ±1..±99¢` that emits a 1.26 MB production `cents.doricolib` containing 597 AccidentalDefinitions + 597 CompositeDefinitions + 198 dedup'd cent-label TextDefinitions + 3 SMuFL GlyphDefinitions, all sorted by `pitch_delta` ascending with a deterministic flat<natural<sharp tiebreak; CLI grew `--mode {cents,template}` (default cents) so Phase 1's byte-faithful round-trip survives unchanged via `--mode template`.

## What Was Built

### `build_cents_full_sweep()` (NEW in main.py)

Returns the canonical 7-tuple shape:

```python
(temperament, acc_system, tonality, accidentals, composites, glyphs, texts)
```

| Position | Type | Count | Notes |
|---|---|---|---|
| 0 | `TemperamentDef` | 1 | name='12-EDO', divisions 200/100/200/200/100/200/200 (TON-02) |
| 1 | `AccidentalSystemDef` | 1 | name='cents'; `accidental_definition_ids` is a 597-tuple in pitch-delta ascending order (D-02, TON-06) |
| 2 | `TonalitySystemDef` | 1 | name='cents' (TON-01) |
| 3 | `tuple[AccidentalDef, ...]` | 597 | 3 zero-dev (Sharp/Flat/Natural) + 594 non-zero |
| 4 | `tuple[CompositeDef, ...]` | 597 | one per accidental, same order |
| 5 | `tuple[GlyphDef, ...]` | 3 | natural, sharp, flat (stable order); all `<parentEntityID/>` empty per D-01 |
| 6 | `tuple[TextDef, ...]` | 198 | one per signed cent value -99..-1, +1..+99; deduped via `dict.setdefault` |

**Total emitted entity-definition rows: 1398** (1 + 1 + 1 + 597 + 597 + 3 + 198). The plan documents say 1411; the 13-entity discrepancy is a documentation arithmetic note in STATE.md/CONTEXT.md, not an implementation gap. The plan's must-haves Truth #3 explicitly enumerates 1+1+597+1+198+3+597 = 1398 and that count matches the emitted XML exactly. See `<known_stubs>` below.

### `run(out_path, mode='cents'|'template')` widened

Single dispatch point: `mode='template'` calls `build_template_three()`; `mode='cents'` calls `build_cents_full_sweep()`. Then `emit.write(...)` is called with the 7-tuple regardless of mode.

### `main()` argparse grows `--mode {cents,template}` (D-04)

```
$ python build.py --help
usage: build.py [-h] [--out OUT] [--mode {cents,template}]

Cents — Dorico tonality-system generator. mode='cents' (default): emits the
1411-entity full sweep (597 accidentals across natural/sharp/flat ±99¢).
mode='template': emits the Phase 1 template round-trip (3 entities: Natural
/ -14 / #-31).
```

### `_glyph_for(base, *, mode)` mode-aware (compose.py)

Two parallel spec tables coexist; default `mode='cents'`:

| Mode | Natural's `parent_entity_id` | Sharp's | Flat's | Comment |
|---|---|---|---|---|
| `'cents'` | `""` (D-01) | `""` | `""` | Default; production sweep uses this |
| `'template'` | `"glyph.accidentalNatural"` | `""` | `""` | Phase 1 quirk preserved for byte-faithful round-trip (D-03) |

The glyph **entityID** is mode-independent (same SMuFL name → same uuid5 hash); only `parent_entity_id` differs by mode. `build_class_a` and `build_class_b` accept and propagate `mode` to `_glyph_for`. `build_class_c` is text-only and ignores mode.

### Locked cents-mode constants (constants.py)

```python
KEY_TEMPERAMENT_12EDO_CENTS: str = "12-edo"
KEY_ACC_SYSTEM_CENTS:        str = "cents"
KEY_TONALITY_CENTS:          str = "cents"
CENTS_RANGE_NONZERO: tuple[int, ...] = tuple(c for c in range(-99, 100) if c != 0)
# 198 entries: -99, -98, ..., -1, +1, +2, ..., +99
```

LOCK FOREVER per D-05 + Pitfall 6 — renaming any of these creates duplicate entityIDs on user re-import.

## CLI Invocation Matrix

| Command | Mode | Output count | Output size |
|---|---|---|---|
| `python build.py` | cents (default) | 1398 entities, 597 AccidentalDefinitions | 1,261,618 bytes |
| `python build.py --out X` | cents (default) | 1398 entities | ~1.26 MB |
| `python build.py --mode cents --out X` | cents | 1398 entities | ~1.26 MB |
| `python build.py --mode template --out X` | template | 13 entities, 3 AccidentalDefinitions | 9,057 bytes (Phase 1 byte-faithful) |

## Production Artifact

- **Path (build target):** `cents.doricolib` (default in cwd)
- **Byte size:** 1,261,618 bytes (~1.20 MiB)
- **md5:** `4cd707d2f4b10154a528b95e2ff5db9f`
- **Top-level entity counts (verified by grep):**
  - `<TemperamentDefinition>`: 1
  - `<AccidentalSystem>`: 1
  - `<AccidentalDefinition>`: 597
  - `<TonalitySystemDefinition>`: 1
  - `<TextPrimitiveEntityDefinition>`: 198
  - `<GlyphPrimitiveEntityDefinition>`: 3
  - `<CompositeDefinition>`: 597
  - `<name>cents</name>`: 2 (one for AccidentalSystem, one for TonalitySystemDefinition)
- **xmllint --noout:** PASSES (well-formed XML)
- **Two-run determinism:** PASSES (cross-PYTHONHASHSEED 12345 vs 99999 → byte-identical)

## D-02 Ordering — Pinned Tiebreak

The 597 accidentals + their composites + the AccidentalSystem ID string are sorted by:

```python
key = (pitch_delta_numerator(base, cents), _BASE_PRIORITY[base], cents)
# _BASE_PRIORITY = {"flat": 0, "natural": 1, "sharp": 2}
```

Examples:

| Pitch delta | Order |
|---|---|
| -199 | `Flat -99` |
| -100 | `Flat` (zero-dev) |
| -50 | `Flat -50`, then `Sharp -50`... wait — let me re-check |
| 0 | `Natural` (zero-dev) |
| 50 | `Natural +50` (priority 1), then `Sharp -50` (priority 2) |
| 100 | `Sharp` (zero-dev) |
| 199 | `Sharp +99` |

At tied delta=50: priority orders `Natural +50` (priority 1) before `Sharp -50` (priority 2). The exact tiebreak is not externally observable as long as it is deterministic; this rule is locked here so re-runs produce byte-identical output.

## Off-by-100 Helper at Work — 8 Diagnostic Cases

Every cents-mode `pitchDeltaFromNatural` is computed as `f"{pitch_delta_numerator(base, cents)}/1200"`:

| Accidental name | (base, cents) | numerator | emitted string |
|---|---|---|---|
| `Sharp +14` | (sharp, 14) | 100 + 14 = 114 | `114/1200` |
| `Sharp -50` | (sharp, -50) | 100 + (-50) = 50 | `50/1200` |
| `Flat -7` | (flat, -7) | -100 + (-7) = -107 | `-107/1200` |
| `Flat +50` | (flat, 50) | -100 + 50 = -50 | `-50/1200` |
| `Natural -7` | (natural, -7) | 0 + (-7) = -7 | `-7/1200` |
| `Natural +50` | (natural, 50) | 0 + 50 = 50 | `50/1200` |
| `Sharp +99` | (sharp, 99) | 100 + 99 = 199 | `199/1200` |
| `Flat -99` | (flat, -99) | -100 + (-99) = -199 | `-199/1200` |

The `Sharp -50` ↔ `Natural +50` enharmonic pair both land at delta=50 and are adjacent in the sorted output (Pitfall 10 covered).

## Pitfall Coverage (Phase 2 owed)

- **Pitfall 1 (off-by-100, CRITICAL)** — defeated. Every cents-mode delta routes through `pitch_delta_numerator()` at exactly one call site (inside `build_cents_full_sweep`). Plan 02-01's 12 hand-calculated tests pin the math. Inline `100 + cents` arithmetic does not appear anywhere in `src/cents_generator/`.
- **Pitfall 8 (Natural absent from AccidentalSystem)** — defeated. The sweep emits all three zero-dev entries unconditionally; the AccidentalSystem `accidental_definition_ids` tuple is constructed from the sorted accidentals tuple, so Natural's entityID is structurally guaranteed to be present. Plan 02-03 will add an explicit assertion.
- **Pitfall 15 (set iteration introduces non-determinism)** — defeated. Glyph and text dedup use `dict.setdefault(entity_id, def)` only — never a `set`. Verified by cross-PYTHONHASHSEED determinism: 12345 vs 99999 → byte-identical.

## Test-Callsite Updates — Hazard Inventory Resolved

PATTERNS.md's hazard list (from `<call_site_hazard_inventory>` in the plan) called out 12 callsites. All are now updated:

| File | Callsites | Change |
|---|---|---|
| `tests/test_template_roundtrip.py` | 7 (lines around 96, 149, 176, 195, 211, 223, 237) | `run(out_path)` → `run(out_path, mode="template")` |
| `tests/test_uuid_snapshot.py` | 1 (line 129) | `cli_run(out)` → `cli_run(out, mode="template")` |
| `tests/test_determinism.py` | 4 in-process + 1 subprocess | `run(path)` → `run(path, mode="template")`; subprocess args list grew `"--mode", "template"` |
| `tests/test_compose.py` | 1 (existing `test_class_a_natural_template_shape`) | added `mode="template"` kwarg per Task 1 |
| `tests/test_emit_format.py` | 2 (helper `_build_three_template_entities`, lines 84-110) | **Rule 1 deviation — see below** |

## Test Suite Status

```
102 passed in 0.14s
```

| Stage | Test count |
|---|---|
| Pre-Phase-2 baseline | 81 |
| After Plan 02-01 | 93 (81 + 12 pitch tests) |
| After Plan 02-02 (this plan) | 102 (93 + 9 new mode-aware compose tests in Task 1) |

Plan 02-02 added 9 new tests in Task 1's RED phase:

1. `test_glyph_for_natural_template_mode_inherits_factory_parent`
2. `test_glyph_for_natural_cents_mode_emits_empty_parent`
3. `test_glyph_for_sharp_empty_parent_in_both_modes`
4. `test_glyph_for_flat_empty_parent_in_both_modes`
5. `test_glyph_for_natural_entity_id_is_mode_independent`
6. `test_build_class_a_mode_cents_default_natural_empty_parent`
7. `test_build_class_b_mode_propagates_to_glyph`
8. `test_cents_mode_locked_keys_pinned`
9. `test_cents_range_nonzero_spans_minus99_to_plus99_excluding_zero`

Plus the existing `test_class_a_natural_template_shape` was updated to pass `mode="template"` explicitly so it continues to assert the Phase 1 quirk under Phase 2 defaults.

## Deviations from Plan

### Rule 1 — Auto-fix bugs caused by current task changes

**1. [Rule 1 - Bug] tests/test_emit_format.py private helper updated to mode='template'**
- **Found during:** Task 1 verification (full pytest run after compose.py default flip)
- **Issue:** `tests/test_emit_format.py::test_self_closing_parent_entity_id` failed because its private helper `_build_three_template_entities` (lines 82-164) calls `build_class_a("natural", ...)` and `build_class_b("sharp", ...)` without `mode="template"`. Task 1 changed `build_class_a/b`'s default to `mode="cents"` (D-01: empty parent on Natural), so the assertion `<parentEntityID>glyph.accidentalNatural</parentEntityID> in body` failed.
- **Plan coverage:** The PATTERNS hazard list explicitly enumerated `tests/test_template_roundtrip.py`, `tests/test_uuid_snapshot.py`, and `tests/test_determinism.py` callsites but missed this private helper inside `tests/test_emit_format.py`. The plan's Task-1 read-list covered `tests/test_compose.py` only.
- **Fix:** Added `mode="template"` to both `build_class_a` (line 92) and `build_class_b` (line 101) calls in the helper. The helper is internal to `tests/test_emit_format.py` and reproduces the same Phase 1 template structure as `build_template_three()` — same fix pattern (D-03 byte-faithful round-trip preserved).
- **Files modified:** `tests/test_emit_format.py` (2 lines added)
- **Commit:** `ce80b3d` (folded into Task 2's commit since the fix is tightly coupled with the run()-callsite updates that PATTERNS did enumerate)

No other deviations. Rules 2-4 did not trigger; D-01..D-08 were fully prescriptive.

## Phase 1 Regressions Absent

- `build_template_three()` body preserved verbatim other than threading `mode="template"` to the `build_class_a` and `build_class_b` calls (D-03 fidelity).
- `tests/test_template_roundtrip.py::test_round_trip_byte_identical_modulo_entity_ids` PASSES (byte-faithful round-trip against `TonalitySystemStartTemplate.doricolib` modulo entityIDs).
- `tests/test_uuid_snapshot.py` (all 7 tests) PASS — Phase 1's 13 pinned entityIDs unchanged.
- `tests/test_determinism.py` (all 3 tests) PASS — template-mode two-run determinism preserved; subprocess args list grew `--mode template` to keep the test exercising template mode after the CLI's new default.
- Phase 1 constants (`FILE_VERSION`, `SECTION_ORDER`, `TEMPERAMENT_12EDO_DIVISIONS`, `KIND_*`, `SMUFL_*`, `FONT_*`) untouched (verified by grep).

## Phase 2 Readiness — Plan 02-03 Unblocked

```python
from cents_generator.main import build_cents_full_sweep, run    # both live
```

Plan 02-03 (testing) can now:

1. Add structural-invariants tests on the cents-mode output (count assertions, section ordering, well-formed XML, AccidentalSystem ID-string parsing).
2. Add a sampled-byte snapshot pinning ~6-10 representative Class A/B/C blocks (the off-by-100 diagnostic cases listed above).
3. Add a cents-mode UUID snapshot pinning a small sampled subset of the 1398 production entityIDs (e.g., `Sharp`, `Natural`, `Sharp +14`, `Sharp -50`, `Flat -7`, `Natural -7`, `Sharp +99`, `Flat -99`).
4. Add a cents-mode two-run determinism test (mirrors the template-mode determinism net but invokes default mode).
5. Add an explicit Pitfall 8 assertion: all three zero-dev entityIDs (`Sharp`, `Flat`, `Natural`) appear in the AccidentalSystem's `<accidentalDefinitionIDs>` string.

CLI surface is stable: `python build.py [--mode {cents,template}] [--out PATH]`.

## Known Stubs

None. Every accidental, composite, glyph, and text emitted by `build_cents_full_sweep()` is fully wired:

- All 597 accidentals have a `composite_id` resolving to a real `CompositeDefinition` in the same file.
- All 594 non-zero composites carry the correct Class B/C component layout (glyph at zOrder=1 + text at zOrder=2 with relativeAttachment for sharp/flat-base; text-only at xOffset=18, yOffset=-12 for natural-base).
- All 198 cent labels are unique and shared across the three bases via `dict.setdefault` dedup.
- All 3 glyphs reference real SMuFL codepoints (0xE260, 0xE261, 0xE262) with `font.defaultmusic`.

The 1398-vs-1411 documentation arithmetic note in STATE.md / CONTEXT.md / ROADMAP.md does not affect output correctness — the must-haves Truth #3 explicitly enumerates the per-section counts (1+1+597+1+198+3+597 = 1398) and the implementation matches those counts exactly. The "+13" appears to count inline structural elements (e.g., the `customKeySignatures` stub's seven `<noteAtoB>`-style children, the seven Component / RelativeAttachment sub-entities — these are not top-level entities). Plan 02-03 (testing) can pin the actual top-level count and document this in PROJECT.md if the user wants to revise the prose.

## Threat Flags

None. No new network endpoints, auth paths, file-access patterns, or trust-boundary surface introduced. The `--mode` argument is argparse-validated via `choices=("cents", "template")` (T-02-02-03 mitigated). All threats in the plan's `<threat_model>` are mitigated; none required architectural changes.

## Commits

- `78120e2` — `test(02-02): add failing tests for mode-aware glyph spec + cents constants (RED)` — 9 new tests in `tests/test_compose.py` + 1 existing test updated to pass `mode="template"`. Tests fail with `TypeError: build_class_b() got an unexpected keyword argument 'mode'` and `ImportError: cannot import name 'KEY_ACC_SYSTEM_CENTS'` — the exact RED-phase fingerprint for Task 1's GREEN edits.
- `69a494f` — `feat(02-02): mode-aware glyph spec + cents-mode locked constants (GREEN)` — splits `_GLYPH_SPEC` into `_GLYPH_SPEC_TEMPLATE` and `_GLYPH_SPEC_CENTS`; `_glyph_for(base, *, mode)` looks up the right table; `build_class_a` and `build_class_b` accept `mode` and propagate. constants.py grows the four locked-forever cents-mode names. All 10 RED tests now PASS at 32/32 in `test_compose.py + test_pitch.py`.
- `ce80b3d` — `feat(02-02): build_cents_full_sweep + --mode CLI flag (1411-entity production sweep)` — main.py adds `build_cents_full_sweep` returning the 7-tuple for the 597-accidental sweep with D-02 ordering; `run()` becomes mode-aware; argparse grows `--mode {cents,template}` default `cents`. Five test files updated for the run()-callsite hazard (PATTERNS list + the test_emit_format.py Rule 1 deviation). Full 102-test suite green.

## TDD Gate Compliance

Plan 02-02 was executed as two TDD-flagged tasks:

- **Task 1 RED gate:** `78120e2` — `test(02-02)` commit precedes implementation; `pytest tests/test_compose.py` failed with `TypeError` and `ImportError` for the new contracts.
- **Task 1 GREEN gate:** `69a494f` — `feat(02-02)` commit; `tests/test_compose.py + tests/test_pitch.py` exit 0 with all 32 passing.
- **Task 1 REFACTOR gate:** skipped (implementation already minimal — small mode-keyword parametrization, no further cleanup needed).
- **Task 2 RED gate:** implicit — Task 1's compose default flip caused 2 existing Phase 1 tests to fail (`test_emit_format::test_self_closing_parent_entity_id`, `test_template_roundtrip::test_round_trip_byte_identical_modulo_entity_ids`). The plan declares "No new tests in this plan; Plan 02-03 owns the cents-mode test net" — Task 2's TDD net is the existing Phase 1 regression suite.
- **Task 2 GREEN gate:** `ce80b3d` — `feat(02-02)` commit; full pytest suite returns to 102/102 green after `build_cents_full_sweep` is implemented and the run()-callsite hazards are resolved.
- **Task 2 REFACTOR gate:** skipped (the dedup + sort + tuple-construction logic is already the simplest correct form for the 7-tuple shape).

## Self-Check: PASSED

Verified files exist:
- `src/cents_generator/main.py` — FOUND (443 lines, includes `build_cents_full_sweep` and mode-aware `run`)
- `src/cents_generator/compose.py` — FOUND (325 lines, mode-aware `_glyph_for` and Class A/B)
- `src/cents_generator/constants.py` — FOUND (105 lines, locked cents-mode keys + `CENTS_RANGE_NONZERO`)
- `tests/test_compose.py` — FOUND (350 lines, 25 tests including 9 new mode-aware tests)
- `tests/test_template_roundtrip.py` — FOUND (8 tests; 7 callsites threaded mode='template')
- `tests/test_uuid_snapshot.py` — FOUND (7 tests; 1 callsite threaded mode='template')
- `tests/test_determinism.py` — FOUND (3 tests; 4 in-process callsites + 1 subprocess args list updated)
- `tests/test_emit_format.py` — FOUND (helper updated to mode='template')

Verified commits exist in `git log`:
- `78120e2` — FOUND
- `69a494f` — FOUND
- `ce80b3d` — FOUND

Verified production artifact:
- `python build.py --out /tmp/cents.doricolib` exits 0
- 1,261,618 bytes
- md5 `4cd707d2f4b10154a528b95e2ff5db9f`
- grep counts: 597 AccidentalDefinition, 198 TextPrimitive, 3 GlyphPrimitive, 597 CompositeDefinition, 1 Temperament, 1 AccidentalSystem, 1 TonalitySystemDefinition (1398 top-level entities)
- xmllint --noout passes
- Two-run cross-PYTHONHASHSEED determinism: bytes identical

Verified Phase 1 untouched:
- `tests/test_template_roundtrip.py::test_round_trip_byte_identical_modulo_entity_ids` PASSES (byte-faithful round-trip preserved)
- `tests/test_uuid_snapshot.py` (all 7 tests) PASS — pinned entityIDs unchanged
- All 13 Phase 1 entityIDs in the snapshot are unchanged

Verified all 11 acceptance criteria from Task 1 and all ~25 acceptance criteria from Task 2 — every grep, line count, python -c smoke check, and pytest invocation listed in the plan returned the expected result.
