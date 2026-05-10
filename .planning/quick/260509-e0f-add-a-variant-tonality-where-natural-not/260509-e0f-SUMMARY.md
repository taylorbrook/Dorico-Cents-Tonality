---
quick_id: 260509-e0f
type: summary
mode: quick
status: complete
completed_date: "2026-05-09"
duration_minutes: 18
commits:
  - hash: e1117ac
    type: feat
    summary: relax Class B for natural base behind allow_natural opt-in
  - hash: 720efd0
    type: feat
    summary: add --mode cents-naturals variant tonality
  - hash: cd06571
    type: test
    summary: variant-mode structural + parity + determinism tests
tasks_total: 3
tasks_completed: 3
files_modified:
  - src/cents_generator/constants.py
  - src/cents_generator/compose.py
  - src/cents_generator/main.py
  - tests/test_compose.py
files_created:
  - tests/test_cents_naturals_variant.py
metrics:
  tests_added: 9      # 3 in test_compose.py + 6 in test_cents_naturals_variant.py
  tests_total: 139    # 130 baseline + 9 new
  cents_md5_preserved: 4cd707d2f4b10154a528b95e2ff5db9f
  cents_naturals_md5: 205a51d2639d6fcfd79c48b874af38e5
  cents_naturals_byte_size: 1464800
  cents_byte_size: 1261618
key-decisions:
  - Variant accidental key suffix is "-cents-naturals" (matches CLI flag verbatim; self-describing in grep).
  - Reuse cents-mode 12-EDO temperament entityID — single shared TemperamentDefinition row when both libraries import.
  - Reuse cents-mode glyph and text entityIDs — mode-independent SMuFL names and label strings.
  - allow_natural=False default preserves Class B's existing rejection contract for unrelated callers.
---

# Quick 260509-e0f: cents-naturals variant tonality — Summary

**One-liner:** Sibling `--mode cents-naturals` library where natural ±cents accidentals render as ♮ + cent text (Class B) instead of bare cent text (Class C); shipped as a coexisting `.doricolib` with variant-suffixed entityIDs, 100% byte-stable cents.doricolib regression preserved.

## What was implemented

### Task 1 — `e1117ac feat(260509-e0f): relax Class B for natural base behind allow_natural opt-in`
- `build_class_b` accepts `base="natural"` only when caller opts in with `allow_natural=True`. Default behavior (no flag, or `allow_natural=False`) still raises `ValueError`, preserving the existing API contract for all unrelated callers.
- Added `KEY_TONALITY_CENTS_NATURALS = "cents-naturals"` and `KEY_ACC_SYSTEM_CENTS_NATURALS = "cents-naturals"` to `constants.py` with D-05 lock-forever commentary.
- 3 new tests in `tests/test_compose.py`:
  - `test_class_b_natural_with_opt_in_returns_glyph_plus_text_shape`: pins ♮ + cent text shape (codepoint, components, attachment offsets, pair points).
  - `test_class_b_natural_without_opt_in_still_rejects`: pins the default-rejection contract.
  - `test_class_b_sharp_signature_unchanged_by_new_flag`: pins that the flag is a no-op for sharp/flat (same entityIDs across both flag values).

### Task 2 — `720efd0 feat(260509-e0f): add --mode cents-naturals variant tonality`
- Added `_cents_naturals_accidental_key(base, cents)` helper (locked suffix `-cents-naturals`).
- Added `build_cents_naturals_full_sweep()` mirroring `build_cents_full_sweep()` with two surgical deltas: natural ±cents → Class B with `allow_natural=True`; variant-suffixed accidental/composite/system/tonality entityIDs. Sharp/flat dispatch and dedup logic unchanged.
- Reuses cents-mode 12-EDO temperament entityID (shared single TemperamentDefinition when both libraries imported).
- Reuses cents-mode glyph and text entityIDs (mode-independent SMuFL/label keys).
- Tonality + AccidentalSystem display name: `cents (naturals shown)`.
- `run()` mode dispatch broadened to `Literal["cents", "template", "cents-naturals"]`.
- CLI `--mode` choices include `cents-naturals`; `--out` defaults to `cents-naturals.doricolib` for variant mode and `cents.doricolib` for cents/template (preserved).

### Task 3 — `cd06571 test(260509-e0f): variant-mode structural + parity + determinism tests`
- New file `tests/test_cents_naturals_variant.py` with 6 tests pinning the variant's behavior:
  1. `test_natural_plus_14_is_class_b_shaped_in_variant` — Class B shape (1 kGlyph + 1 kText + relativeAttachment with -8/-12 offsets and kBaselineRight/kBaselineLeft pair points).
  2. `test_natural_zero_is_class_a_shaped_in_variant` — natural at 0¢ stays Class A (single kGlyph, no kText, no relativeAttachment).
  3. `test_sharp_plus_14_composite_block_byte_identical_modulo_eids` — sharp/flat ±cents shape is cross-mode invariant after entityID normalization.
  4. `test_two_in_process_runs_byte_identical` — in-process determinism.
  5. `test_two_subprocess_runs_byte_identical` — subprocess determinism via `build.py`.
  6. `test_variant_entityids_isolated_from_cents_mode` — pins which keys differ across modes (tonality, accidental-system, accidental) vs intentionally shared (12-EDO temperament, glyph names).

## Verification results

| Check | Result |
| --- | --- |
| Full pytest suite (`python3 -m pytest -x -q`) | 139 passed, 3 skipped |
| Variant test file alone | 6/6 passed |
| Updated compose tests | 23/23 passed (20 existing + 3 new) |
| Cents-mode regression md5 | `4cd707d2f4b10154a528b95e2ff5db9f` (matches v1.0 shipped artifact byte-for-byte) |
| Cents-naturals.doricolib md5 (deterministic) | `205a51d2639d6fcfd79c48b874af38e5` |
| Cents-naturals.doricolib byte size | 1,464,800 bytes (~203 KB larger than cents.doricolib — 594 natural-deviation accidentals each gain glyph + attachment payload, expected) |
| Cents-naturals per-section counts | 1 TemperamentDef, 1 AccidentalSystem, 597 AccidentalDefs, 1 TonalitySystemDef, 198 TextDefs, 3 GlyphDefs, 597 CompositeDefs |
| `xmllint --noout cents-naturals.doricolib` | Clean (no errors) |
| Determinism: two consecutive `--mode cents-naturals` runs | Byte-identical (in-process and subprocess) |
| Default `--out` for `--mode cents-naturals` | `cents-naturals.doricolib` (cwd) |
| Default `--out` for `--mode cents` | `cents.doricolib` (cwd, preserved) |
| `<name>cents (naturals shown)</name>` in variant output | Confirmed |
| `<fileVersion>1.1450</fileVersion>` in variant output | Confirmed |

## Deviations from plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Test assertion strings used wrong XML element names**
- **Found during:** Task 3 RED phase (initial test run failed with assertion error).
- **Issue:** The plan's test code asserted on `<RelativeAttachment>` (capital R) and `<pair1AttachmentPoint>`/`<pair2AttachmentPoint>` element names. The actual emitter outputs `<relativeAttachment>` (lowercase first character; the wrapper is `<relativeAttachments array="true">`) and uses `<componentAttachmentPoint>` inside `<componentRelativePair1>`/`<componentRelativePair2>` blocks.
- **Fix:** Adjusted the assertions in `test_natural_plus_14_is_class_b_shaped_in_variant` to use the correct XML element names, and sliced the relativeAttachment block out of the composite to avoid accidentally matching the (zero-valued) component xOffset/yOffset fields. Also fixed the corresponding `<RelativeAttachment>` reference in `test_natural_zero_is_class_a_shaped_in_variant`.
- **Files modified:** `tests/test_cents_naturals_variant.py`
- **Commit:** Folded into Task 3 commit `cd06571`.
- **Rationale for not pausing:** The plan's test text was a strawman against the actual emitter shape — the underlying invariant being tested (Class B has glyph + text + attachment with -8/-12 offsets and kBaselineRight/kBaselineLeft pair points) is unchanged. The fix matches the true emit format already validated by existing snapshot/structural tests.

## Deferred items

- README update documenting `--mode cents-naturals` and the sibling `cents-naturals.doricolib` artifact (explicitly deferred per plan `<objective>` "Out of scope (deferred)" section).
- Visual offset tuning for ♮+cent (uses existing `CLASS_B_ATTACH_X_OFFSET=-8`, `CLASS_B_ATTACH_Y_OFFSET=-12` shared with sharp/flat; if naturals collide more than sharps/flats, adjust in a follow-up — explicitly deferred per plan).
- The `cents-naturals.doricolib` artifact is NOT shipped at the repo root in this commit — generated on demand via `python3 build.py --mode cents-naturals`. Shipping the binary artifact is a separate decision (sibling of cents.doricolib v1.0 commit) and not requested by the plan.

## Files

### Modified
- `src/cents_generator/constants.py` — added `KEY_TONALITY_CENTS_NATURALS`, `KEY_ACC_SYSTEM_CENTS_NATURALS`.
- `src/cents_generator/compose.py` — `build_class_b` accepts `base="natural"` behind `allow_natural=True` opt-in.
- `src/cents_generator/main.py` — added `_cents_naturals_accidental_key`, `build_cents_naturals_full_sweep`, broadened `run()` mode dispatch, wired `--mode cents-naturals` CLI.
- `tests/test_compose.py` — 3 new Class-B-natural tests alongside the preserved ValueError test.

### Created
- `tests/test_cents_naturals_variant.py` — 6 tests pinning variant-mode structural diffs, sharp/flat parity, determinism (in-process + subprocess), and entityID isolation.

## Self-Check: PASSED

- `src/cents_generator/constants.py` — FOUND
- `src/cents_generator/compose.py` — FOUND
- `src/cents_generator/main.py` — FOUND
- `tests/test_compose.py` — FOUND
- `tests/test_cents_naturals_variant.py` — FOUND
- Commit `e1117ac` — FOUND in git log
- Commit `720efd0` — FOUND in git log
- Commit `cd06571` — FOUND in git log
- cents.doricolib md5 `4cd707d2f4b10154a528b95e2ff5db9f` — UNCHANGED
- cents-naturals.doricolib determinism — VERIFIED byte-identical across runs
- Full pytest suite — 139 passed, 3 skipped
