---
phase: 02-range-expansion-to-99
plan: 01
subsystem: cents_generator
tags:
  - python
  - stdlib
  - pure-function
  - tdd
  - pitfall-1
  - gen-05
requires: []
provides:
  - "src/cents_generator/pitch.py::pitch_delta_numerator"
  - "_BASE_OFFSET_CENTS lookup table (private)"
affects:
  - "Plan 02-02 (cents-mode emission) — unblocked: from cents_generator.pitch import pitch_delta_numerator is live"
tech-stack:
  added: []
  patterns:
    - "single-purpose stdlib utility module mirroring uuids.py shape"
    - "locked-constant comment block (NEVER ALTER) mirrors PROJECT_NAMESPACE pattern"
    - "one-assertion-per-test discipline (no pytest.parametrize)"
key-files:
  created:
    - "src/cents_generator/pitch.py (59 lines)"
    - "tests/test_pitch.py (80 lines, 12 test functions)"
  modified: []
decisions:
  - "Module location: dedicated src/cents_generator/pitch.py (vs. inlining into compose.py/constants.py) — chosen for cohesion with uuids.py analog"
  - "_BASE_OFFSET_CENTS is a private module-level dict (leading underscore) — implementation detail; only pitch_delta_numerator is public"
  - "Helper raises KeyError on unsupported base — accepted per threat T-02-01-02 (Literal type hint signals supported values; clear error vs silent wrong output)"
metrics:
  duration_minutes: 1.7
  tasks_completed: 2
  files_created: 2
  files_modified: 0
  tests_added: 12
  tests_total: 93
  completed_date: "2026-05-02"
requirements_satisfied:
  - GEN-05
---

# Phase 2 Plan 01: pitch_delta_numerator helper Summary

**One-liner:** Centralized pitch-delta numerator helper (`{natural: 0, sharp: 100, flat: -100}[base] + cents`) shipped as a single-purpose stdlib module with 12 hand-calculated unit tests pinning the math; defeats Pitfall 1 (the off-by-100 trap) by making the formula impossible to inline incorrectly downstream.

## What Was Built

### `src/cents_generator/pitch.py` (NEW, 59 lines)

**Public API:**

```python
def pitch_delta_numerator(
    base: Literal["natural", "sharp", "flat"],
    cents: int,
) -> int
```

Returns `_BASE_OFFSET_CENTS[base] + cents` where `_BASE_OFFSET_CENTS = {"natural": 0, "sharp": 100, "flat": -100}`.

- Stdlib only: `from __future__ import annotations` + `from typing import Literal`. No third-party imports.
- Module docstring explains Pitfall 1 defense + template-mode opt-out (template mode preserves literal pitch-delta strings and does NOT call this helper).
- Constant `_BASE_OFFSET_CENTS` carries a "NEVER ALTER WITHOUT COORDINATED MATH REVIEW" comment block mirroring `uuids.py::PROJECT_NAMESPACE` pattern.
- Pure function: no I/O, no logging, no side effects, O(1) dict lookup + integer add.
- Returns `int`; callers responsible for `f"{n}/1200"` formatting (no float, no `Fraction`).

### `tests/test_pitch.py` (NEW, 80 lines, 12 test functions)

Twelve explicit one-assertion-per-test cases (mirrors `tests/test_uuids.py` discipline — no `pytest.parametrize` so failure messages name the offending case unambiguously):

| # | Test name | Input | Expected |
|---|-----------|-------|----------|
| 1 | `test_pitch_delta_sharp_14_is_114` | `("sharp", 14)` | `114` |
| 2 | `test_pitch_delta_sharp_minus_50_is_50` | `("sharp", -50)` | `50` *(off-by-100 trap diagnostic)* |
| 3 | `test_pitch_delta_flat_minus_7_is_minus_107` | `("flat", -7)` | `-107` |
| 4 | `test_pitch_delta_flat_50_is_minus_50` | `("flat", 50)` | `-50` |
| 5 | `test_pitch_delta_natural_minus_7_is_minus_7` | `("natural", -7)` | `-7` |
| 6 | `test_pitch_delta_zero_dev_sharp_is_100` | `("sharp", 0)` | `100` |
| 7 | `test_pitch_delta_zero_dev_flat_is_minus_100` | `("flat", 0)` | `-100` |
| 8 | `test_pitch_delta_zero_dev_natural_is_0` | `("natural", 0)` | `0` |
| 9 | `test_pitch_delta_boundary_sharp_99_is_199` | `("sharp", 99)` | `199` |
| 10 | `test_pitch_delta_boundary_flat_minus_99_is_minus_199` | `("flat", -99)` | `-199` |
| 11 | `test_pitch_delta_boundary_natural_99_is_99` | `("natural", 99)` | `99` |
| 12 | `test_enharmonic_pair_sharp_minus_50_equals_natural_50` | `("sharp", -50)` & `("natural", 50)` | both `50` *(Pitfall 10)* |

## Test Suite Status

```
93 passed in 0.14s
```

- **Total:** 93 tests
- **Phase 1 baseline:** 81 tests (untouched, still passing — confirmed by `git diff --stat HEAD~2 HEAD` showing zero modifications to any Phase 1 file)
- **Added by this plan:** 12 tests in `tests/test_pitch.py`
- **Plan-2-01 specific run:** `python3 -m pytest tests/test_pitch.py -v` → 12 passed in 0.01s

## Phase 1 Untouched — Verification

`git diff --stat HEAD~2 HEAD` against the seven Phase 1 source files (`entities.py`, `emit.py`, `uuids.py`, `compose.py`, `main.py`, `constants.py`) and the seven Phase 1 test files (`test_uuids.py`, `test_compose.py`, `test_emit_format.py`, `test_entities.py`, `test_template_roundtrip.py`, `test_uuid_snapshot.py`, `test_determinism.py`) returns empty. Only two new files exist in this plan:

```
src/cents_generator/pitch.py    (new)
tests/test_pitch.py             (new)
```

This plan is purely additive.

## Pitfall 1 Defeated

The off-by-100 trap (PITFALLS.md §"Pitfall 1") is now structurally impossible to introduce in cents-mode code: every Plan 02-02 caller will route through `pitch_delta_numerator(base, cents)`, and any regression of the helper triggers an immediate, named test failure (e.g., `test_pitch_delta_sharp_minus_50_is_50` would fail with the exact diagnostic case in the failure message).

`grep -rE 'pitch_delta_numerator|pitchDeltaFromNatural\s*=\s*[^"]' src/cents_generator/` confirms `pitch.py` is the only producer — no inline `100 + cents` arithmetic anywhere else in `src/`.

## Phase 2 Readiness — Plan 02-02 Unblocked

```python
from cents_generator.pitch import pitch_delta_numerator    # live
```

Plan 02-02 (cents-mode emission) can now sweep over `[(b, c) for b in ("natural","sharp","flat") for c in range(-99, 100)]`, computing `pitch_delta_from_natural=f"{pitch_delta_numerator(b, c)}/1200"` per accidental, and feeding the resulting bundles into `emit.write()` unchanged.

## Deviations from Plan

None — plan executed exactly as written. D-06 was fully prescriptive; the only Claude's-discretion choice (module location) defaulted to the recommended `src/cents_generator/pitch.py` for cohesion with the `uuids.py` analog.

## Commits

- `fe95617` — `test(02-01): add failing tests for pitch_delta_numerator (RED)` — 12 hand-calculated cases, fails with `ModuleNotFoundError` (RED gate)
- `164f6d3` — `feat(02-01): implement pitch_delta_numerator helper (GREEN)` — helper module, all 12 tests pass (GREEN gate)

REFACTOR phase: not needed — implementation is the minimal correct form (one-line return).

## TDD Gate Compliance

- RED gate: `fe95617` — `test(...)` commit precedes implementation; `pytest tests/test_pitch.py` failed with `ModuleNotFoundError: No module named 'cents_generator.pitch'`.
- GREEN gate: `164f6d3` — `feat(...)` commit; same test command exits 0 with all 12 passing.
- REFACTOR gate: skipped (implementation already minimal).

## Self-Check: PASSED

Verified files exist:
- `src/cents_generator/pitch.py` — FOUND (59 lines)
- `tests/test_pitch.py` — FOUND (80 lines)

Verified commits exist in `git log`:
- `fe95617` — FOUND
- `164f6d3` — FOUND

Verified all 12 acceptance criteria from Task 1 (file size, test count, no parametrize, RED phase fingerprint) and all 11 acceptance criteria from Task 2 (file size, function definition, mapping values, stdlib-only imports, helper math one-liner, full pytest run).
