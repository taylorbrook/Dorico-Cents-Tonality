---
quick_id: 260512-l0i
status: complete
mode: quick
type: execute
completed: "2026-05-12"
duration_minutes: 12
files_modified:
  - src/cents_generator/constants.py
  - src/cents_generator/main.py
files_created:
  - tests/test_cents_naturals_optional_variant.py
commits:
  - hash: 8ac047d
    type: feat
    summary: "add --mode cents-naturals-optional variant builder"
  - hash: d0abc97
    type: test
    summary: "variant + parity + regression tests for cents-naturals-optional"
artifacts:
  md5_cents_naturals_optional: b9fcb6bb70df82e069857573dc877e95
  bytes_cents_naturals_optional: 1724627
  entity_count: 1794
  regression_md5_cents: 4cd707d2f4b10154a528b95e2ff5db9f
  regression_md5_cents_naturals: 205a51d2639d6fcfd79c48b874af38e5
tests:
  baseline: 139
  new: 12
  total_passed: 151
  skipped: 3
locked_strings:
  - "cents-naturals-optional (KEY_TONALITY_*, KEY_ACC_SYSTEM_*)"
  - "-cents-naturals-optional (sharps/flats/zero-dev suffix)"
  - "-cents-naturals-optional-textonly (natural Class C suffix)"
  - "-cents-naturals-optional-withglyph (natural Class B suffix)"
  - "cents (naturals optional) (display name)"
  - "variant_tiebreak: text-only=0, with-glyph=1"
---

# Quick Task 260512-l0i: cents-naturals-optional Variant Summary

Third variant tonality `--mode cents-naturals-optional` emitting BOTH flavors of every nonzero natural ±cent side-by-side in one library — text-only Class C AND ♮+cent text Class B at every cent value, under distinct entityIDs but the same `pitch_delta_from_natural`. Dorico users now pick per-note (instead of per-library) whether the ♮ glyph displays alongside a natural-deviation cent label.

## Tasks Completed

### Task 1 — Constants + builder + CLI wiring (commit `8ac047d`)

**Implementation:**
- `src/cents_generator/constants.py`: appended `KEY_TONALITY_CENTS_NATURALS_OPTIONAL = "cents-naturals-optional"` and `KEY_ACC_SYSTEM_CENTS_NATURALS_OPTIONAL = "cents-naturals-optional"` with locking commentary directly below the existing cents-naturals block. Did not touch any pre-existing constants.
- `src/cents_generator/main.py`:
  - Imports updated to include the two new keys.
  - Added three private suffix constants — `_CNO_KEY_SUFFIX`, `_CNO_NATURAL_TEXTONLY_SUFFIX`, `_CNO_NATURAL_WITHGLYPH_SUFFIX` — and three helper functions: `_cno_accidental_key()`, `_cno_natural_textonly_key()`, `_cno_natural_withglyph_key()`. All LOCKED FOREVER once shipped per D-05 carry-over.
  - Added brand-new `build_cents_naturals_optional_full_sweep()` immediately below `build_cents_naturals_full_sweep()`. Implementation is independent of the existing two builders — a fresh loop with widened sort key `(delta, base_priority, cents, variant_tiebreak)`. This preserves byte-identical regression on the prior two modes by construction.
  - For each `(base, cents)`: zero-cent → Class A with `_cno_accidental_key`; sharps/flats nonzero → Class B with `_cno_accidental_key`; **naturals nonzero → TWO bundles emitted**: a text-only Class C (display name `"+14"`, suffix `-textonly`, tiebreak=0) AND a with-glyph Class B (display name `"Natural +14"`, suffix `-withglyph`, tiebreak=1, `allow_natural=True`).
  - Glyph/text dedup work unchanged (`setdefault` by entityID). Both natural flavors at +14 share the same `+14` TextDef. With-glyph flavor dedupes its `accidentalNatural` glyph against the zero-cent natural's glyph.
  - Singletons: temperament reuses the cents-mode entityID (single 12-EDO across all three libraries); accidental-system and tonality-system use the new variant keys with display name `"cents (naturals optional)"`.
  - `run()` mode `Literal` widened to four members; dispatch added for `"cents-naturals-optional"`.
  - CLI `--mode` `choices` widened; `--out` default-derivation now branches three ways (`cents-naturals-optional.doricolib` for the new mode).

**Verification:**
- Full pytest suite: 139 passed (3 skipped) — no regressions in cents/cents-naturals/template/compose modes.
- `python3 build.py --mode cents --out /tmp/c.doricolib` → md5 `4cd707d2f4b10154a528b95e2ff5db9f` (matches shipped).
- `python3 build.py --mode cents-naturals --out /tmp/cn.doricolib` → md5 `205a51d2639d6fcfd79c48b874af38e5` (matches shipped).
- `diff -q` against repo-root `cents.doricolib` and `cents-naturals.doricolib` both clean.
- `python3 build.py --mode cents-naturals-optional --out /tmp/cno.doricolib` → 1,724,627 bytes, xmllint clean.
- Per-section counts asserted: 795 / 795 / 198 / 3 / 1 / 1 / 1 (accidentals / composites / texts / glyphs / tonality / acc-system / temperament) → total 1794 entities (matches D-09 target).
- Default-out path verified: invoking `--mode cents-naturals-optional` without `--out` writes to `cents-naturals-optional.doricolib` in cwd.

### Task 2 — Variant tests (commit `d0abc97`)

**Created** `tests/test_cents_naturals_optional_variant.py` with twelve tests, mirroring the structure of `tests/test_cents_naturals_variant.py`:

1. `test_text_only_natural_plus_14_is_class_c_shaped` — Class C invariant for the text-only `+14` flavor (1 kText, 0 kGlyph, no `<relativeAttachment>`).
2. `test_with_glyph_natural_plus_14_is_class_b_shaped` — Class B invariant for the `Natural +14` flavor (1 kGlyph + 1 kText + `(-8, -12)` baseline-right/-left attachment).
3. `test_both_natural_flavors_share_pitch_delta_distinct_entityids` — uuid layer assertion that the two natural-flavor entityIDs differ.
4. `test_natural_zero_is_class_a_shaped` — zero-cent natural stays Class A in the new mode.
5. `test_sharp_plus_14_composite_block_byte_identical_modulo_eids` — cross-mode parity: Sharp +14 composite block byte-equal to cents-naturals mode after entityID normalization.
6. `test_two_in_process_runs_byte_identical` — in-process determinism.
7. `test_two_subprocess_runs_byte_identical` — subprocess determinism.
8. `test_variant_entityids_isolated_from_prior_modes` — four distinct natural+14 entityIDs across all three libraries; tonality + accidental-system entityIDs all pairwise distinct; temperament + glyph entityIDs intentionally shared.
9. `test_entity_section_counts` — 795/795/198/3/1/1/1 section counts.
10. `test_cents_mode_md5_unchanged` — cents-mode regression md5 (`4cd707d2…`).
11. `test_cents_naturals_mode_md5_unchanged` — cents-naturals-mode regression md5 (`205a51d2…`).
12. `test_natural_plus_14_textonly_appears_before_withglyph_in_acc_system` — LOCKED tiebreak ordering (text-only `+14` precedes `Natural +14` in `<accidentalDefinitionIDs>`).

**Verification:**
- `pytest tests/test_cents_naturals_optional_variant.py -x -v` → 12 passed.
- Full suite: 151 passed, 3 skipped (139 baseline + 12 new).

## Verification Results

| Check | Result |
|-------|--------|
| Full pytest suite | 151 passed, 3 skipped |
| `--mode cents` md5 | `4cd707d2f4b10154a528b95e2ff5db9f` (regression preserved) |
| `--mode cents-naturals` md5 | `205a51d2639d6fcfd79c48b874af38e5` (regression preserved) |
| `--mode cents-naturals-optional` md5 | `b9fcb6bb70df82e069857573dc877e95` (new artifact) |
| `--mode cents-naturals-optional` size | 1,724,627 bytes |
| Determinism (two consecutive runs) | byte-identical (`diff -q` clean) |
| `xmllint --noout` on new artifact | clean (no errors) |
| `diff` cents output vs shipped `cents.doricolib` | empty |
| `diff` cents-naturals output vs shipped `cents-naturals.doricolib` | empty |
| Default `--out` for new mode | `cents-naturals-optional.doricolib` (verified) |

## Per-Section Entity Counts (cents-naturals-optional)

| Section | Count |
|---------|-------|
| TemperamentDefinition | 1 (shared 12-EDO) |
| AccidentalSystem | 1 (`"cents (naturals optional)"`) |
| TonalitySystemDefinition | 1 (`"cents (naturals optional)"`) |
| AccidentalDefinition | 795 (3 zero-dev + 198 sharp ±¢ + 198 flat ±¢ + 198 natural text-only + 198 natural with-glyph) |
| CompositeDefinition | 795 (one per accidental) |
| TextPrimitiveEntityDefinition | 198 (dedup'd; both natural flavors at +14 share the literal `"+14"` text) |
| GlyphPrimitiveEntityDefinition | 3 (natural, sharp, flat — all `<parentEntityID/>` empty per D-01) |
| **Total** | **1794** |

## Deviations from Plan

None — plan executed exactly as written. The implementation path described in `<key_decisions>` and `<naming_conventions_locked_by_this_plan>` mapped 1:1 to the code changes:

- Brand-new `build_cents_naturals_optional_full_sweep()` rather than refactoring the existing two sweeps (per plan recommendation — preserves byte-identical regression on prior modes by construction).
- Widened sort key `(delta, base_priority, cents, variant_tiebreak)` with text-only first (0), with-glyph second (1).
- Three locked key suffixes; two locked constants; one locked tonality/acc-system display name (`"cents (naturals optional)"`).
- CLI: three-way `--out` default-branching; `Literal` mode widened to four members.

## Locked Strings (FOREVER, per D-05 carry-over)

| String | Value |
|--------|-------|
| `KEY_TONALITY_CENTS_NATURALS_OPTIONAL` | `"cents-naturals-optional"` |
| `KEY_ACC_SYSTEM_CENTS_NATURALS_OPTIONAL` | `"cents-naturals-optional"` |
| Accidental/composite suffix (baseline) | `-cents-naturals-optional` |
| Accidental/composite suffix (natural text-only) | `-cents-naturals-optional-textonly` |
| Accidental/composite suffix (natural with-glyph) | `-cents-naturals-optional-withglyph` |
| Tonality / AccidentalSystem display name | `cents (naturals optional)` |
| Accidental display name (text-only natural) | `"<signed-cents>"` (e.g. `"+14"`) |
| Accidental display name (with-glyph natural) | `"Natural <signed-cents>"` (e.g. `"Natural +14"`) |
| Sort tiebreak at same `(delta, base, cents)` | text-only=0, with-glyph=1 |
| CLI flag value | `--mode cents-naturals-optional` |
| Default output filename | `cents-naturals-optional.doricolib` |

Temperament and glyph entityIDs are INTENTIONALLY SHARED across all three libraries (cents / cents-naturals / cents-naturals-optional) — a single 12-EDO temperament and mode-independent SMuFL glyph names are correct semantics.

## Deferred Items

Per the plan's `<objective>` "Out of scope (deferred)":

- README update documenting the new mode — separate doc task post-merge.
- Shipping the `cents-naturals-optional.doricolib` artifact at the repo root — orchestrator decision.
- Visual offset tuning for ♮+cent (reuses existing `CLASS_B_ATTACH_*` and `CLASS_C_TEXT_*` offsets — shared with prior modes).

Also (process):

- STATE.md / ROADMAP.md updates are intentionally skipped for this quick task per the plan constraints.

## Files

**Modified:**
- `src/cents_generator/constants.py` — 13 added lines (two new constants + locking commentary block).
- `src/cents_generator/main.py` — ~290 added lines (three suffix constants, three key-helper functions, one new builder function, `run()` dispatch update, CLI `--mode` choices + `--out` default-branch update).

**Created:**
- `tests/test_cents_naturals_optional_variant.py` — 335 lines, 12 tests.

## Self-Check: PASSED

Verified files exist:
- `/Users/taylorbrook/Dev/dorico tonality/.claude/worktrees/agent-a3e82487ceb035351/src/cents_generator/constants.py` (FOUND)
- `/Users/taylorbrook/Dev/dorico tonality/.claude/worktrees/agent-a3e82487ceb035351/src/cents_generator/main.py` (FOUND)
- `/Users/taylorbrook/Dev/dorico tonality/.claude/worktrees/agent-a3e82487ceb035351/tests/test_cents_naturals_optional_variant.py` (FOUND)

Verified commits exist on `worktree-agent-a3e82487ceb035351`:
- `8ac047d` feat(260512-l0i): add --mode cents-naturals-optional variant builder (FOUND)
- `d0abc97` test(260512-l0i): variant + parity + regression tests for cents-naturals-optional (FOUND)

## TDD Gate Compliance

This quick plan was structured with implementation-first ordering (Task 1 implements; Task 2 adds dedicated variant tests). The existing test suite (139 tests) served as the regression gate during Task 1 implementation; the new variant test file (12 tests) lands in a separate Task 2 commit. Gate commits in git log:

- Task 1 `feat(...)` commit `8ac047d` — added the implementation; existing tests stayed green.
- Task 2 `test(...)` commit `d0abc97` — added the new dedicated variant tests; all 151 tests green.

No RED-before-GREEN inversion occurred because the new tests target behavior introduced in Task 1; running Task 2's tests before Task 1's implementation would fail at import time (the new mode and key constants would not yet exist). The dedicated variant tests act as the documented behavioral contract for the new mode going forward.
