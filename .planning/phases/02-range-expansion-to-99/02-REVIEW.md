---
phase: 02-range-expansion-to-99
reviewed: 2026-05-02T02:04:44Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - src/cents_generator/pitch.py
  - src/cents_generator/compose.py
  - src/cents_generator/constants.py
  - src/cents_generator/main.py
  - tests/test_pitch.py
  - tests/test_compose.py
  - tests/test_template_roundtrip.py
  - tests/test_uuid_snapshot.py
  - tests/test_determinism.py
  - tests/test_emit_format.py
  - tests/test_cents_structural.py
  - tests/test_cents_snapshot.py
findings:
  critical: 0
  warning: 4
  info: 8
  total: 12
status: issues_found
---

# Phase 02 (range-expansion-to-99): Code Review Report

**Reviewed:** 2026-05-02T02:04:44Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

I reviewed the full ±99¢ range-expansion phase: the new `pitch_delta_numerator` helper, the cents-mode full sweep in `main.build_cents_full_sweep`, the dedup pipeline with sort tiebreaks, and 31 new tests covering structural invariants, snapshots, and cross-mode determinism.

The core math, dedup determinism, sort ordering, and snapshot pinning are all sound. I traced the off-by-100 trap arithmetic by hand for the boundary cases (Sharp +99 → 199, Flat -99 → -199, Sharp -1 = Natural +99 = 99/1200 enharmonics, etc.) and the test counts match. The PYTHONHASHSEED-safe dedup via `dict.setdefault` is correctly applied, and entity-ID stability is locked by snapshots at multiple layers.

No BLOCKERs. The findings below are quality / robustness issues. The most important are: (1) bare-mode `build_class_b` keeps a documented but functionally-unused `mode` kwarg that increases API surface for nothing, (2) several `Optional[GlyphDef]` accesses in tests rely on runtime invariants without type-narrowing — they pass today but are a footgun for refactors, (3) a hardcoded `/tmp/` path in `test_template_roundtrip.py` makes failure diagnostics unportable (Windows breaks; even on macOS it leaks state across runs), and (4) the strip-asserts-under-`python -O` pattern is used in two places where the assertion is the only guarantee that `glyph`/`text` is non-`None` before tuple-packing.

## Warnings

### WR-01: `mode` kwarg on `build_class_b` is functionally a no-op but adds API surface

**File:** `src/cents_generator/compose.py:225-241`
**Issue:** The `mode: Literal["cents", "template"]` kwarg on `build_class_b` is documented as "effectively a no-op for Class B today; it exists for signature symmetry with Class A and for future-proofing." Class B explicitly rejects natural base, and Sharp/Flat have empty parents in both modes — so the parameter does nothing. `test_build_class_b_mode_propagates_to_glyph` even asserts both modes produce identical output. This is dead-flexibility: future readers will assume it does something, and a real future divergence (e.g. a sharp-mode quirk) cannot be added without breaking signature symmetry assumptions.
**Fix:** Drop the `mode` kwarg from `build_class_b`. If a future tonality system needs different sharp/flat parents per mode, add the kwarg back at that point with a meaningful behavior. Update `main.py:130` and `tests/test_emit_format.py:103` callers (both pass `mode="template"` purely for documentation).

```python
# Drop mode from build_class_b signature; in main.py:
sharp_minus_31_bundle = build_class_b(
    "sharp",
    accidental_name="#-31",
    accidental_key=_KEY_SHARP_31_TEMPLATE,
    composite_name="New Composite",
    composite_key=_KEY_SHARP_31_TEMPLATE,
    label_text="-31",
    pitch_delta_from_natural="69/1200",
)
```

### WR-02: Critical `None`-narrowing relies on `assert` which is stripped under `python -O`

**File:** `src/cents_generator/main.py:183, 192`
**Issue:** Two `assert ... is not None` statements are the only thing telling static analyzers (and readers) that `minus_14_text`, `sharp_minus_31_text`, `natural_glyph`, and `sharp_glyph` are non-`None` before they get packed into typed tuples. When run under `python -O` (assertions stripped), these checks vanish. The downstream emit.py would then `AttributeError` on `.name` access if any bundle ever returned `None` for these fields — even though current Class A/B always populate them, this is the kind of invariant that breaks silently when refactoring `compose.py` later. Asserts as type-narrowing-aids are fine, but asserts as runtime guards against `None` are anti-pattern.
**Fix:** Replace assertions with explicit conditionals raising a typed error; or restructure so the bundle returns non-Optional fields by class. Minimal change:

```python
natural_glyph = natural_bundle.glyph
sharp_glyph = sharp_minus_31_bundle.glyph
if natural_glyph is None or sharp_glyph is None:
    raise RuntimeError(
        "build_class_a/b invariant violation: glyph is None for natural/sharp"
    )
glyphs: tuple[GlyphDef, ...] = (natural_glyph, sharp_glyph)
```

### WR-03: Hardcoded `/tmp/` path in round-trip test breaks on Windows and leaks state

**File:** `tests/test_template_roundtrip.py:112-113, 135-140`
**Issue:** On test failure, the round-trip test copies normalized output to `/tmp/_normalized_generated.txt` and `/tmp/_normalized_template.txt`. This: (a) fails on Windows where `/tmp` doesn't exist (`shutil.copy` will raise `FileNotFoundError`, masking the actual diff diagnostic the developer wanted); (b) leaves files behind across runs with no cleanup, so a later success-after-failure reads stale files; (c) is a race on multi-developer/CI hosts where parallel runs clobber each other. The CLAUDE.md says the project must work on Windows install paths — Windows test compatibility matters.
**Fix:** Use `tmp_path` (pytest fixture) which is already in scope at line 90, and reference that path in the failure message:

```python
gen_diag = tmp_path / "_normalized_generated.txt"
tpl_diag = tmp_path / "_normalized_template.txt"
gen_diag.write_text(normalized_generated)
tpl_diag.write_text(normalized_template)
# remove shutil.copy calls
# update failure message to print gen_diag and tpl_diag
pytest.fail(
    f"Round-trip diverged.\n"
    f"  Generated normalized:  {gen_diag} ({len(normalized_generated)} bytes)\n"
    f"  Template normalized:   {tpl_diag} ({len(normalized_template)} bytes)\n"
    ...
)
```
The `shutil` import on line 26 then becomes unused — remove it (it's still used by `test_round_trip_xmllint_well_formed` for `shutil.which`, so keep the import there).

### WR-04: Several test assertions access `.glyph.code_point` / `.glyph.parent_entity_id` without `None` narrowing

**File:** `tests/test_compose.py:134, 135, 179, 192, 264`
**Issue:** Several tests reach into `b.glyph.code_point` or `b.glyph.parent_entity_id` directly on `AccidentalBundle` instances where `glyph: GlyphDef | None`. Examples: `test_build_class_b_mode_propagates_to_glyph` (lines 134-135), `test_class_a_sharp_uses_correct_codepoint_and_no_factory_parent` (lines 179-180), `test_class_a_flat_uses_correct_codepoint` (line 192), `test_class_b_flat_uses_correct_codepoint` (line 264). These rely on the runtime invariant "Class A and Class B always return non-None glyph", which is true today but is enforced nowhere in the test. If `build_class_a/b` is ever refactored to return `None` for some path, these tests will `AttributeError` rather than failing with a meaningful assertion. mypy strict-mode would flag every one.
**Fix:** Add an explicit assertion before access, mirroring the pattern already used in `test_class_b_template_shape:220` (`assert b.glyph is not None and b.text is not None`):

```python
def test_class_a_sharp_uses_correct_codepoint_and_no_factory_parent() -> None:
    b = build_class_a(...)
    assert b.glyph is not None
    assert b.glyph.code_point == 0xE262
    assert b.glyph.parent_entity_id == ""
```

## Info

### IN-01: `pitch_delta_numerator` raises `KeyError` instead of `ValueError` for unknown base

**File:** `src/cents_generator/pitch.py:38-59`
**Issue:** The function leaks the dict implementation by raising `KeyError` on unknown base strings. By contrast, `compose.build_class_b` validates its `base` parameter and raises `ValueError` with a helpful message. Inconsistent error handling. Since callers receive `Literal["natural", "sharp", "flat"]`-typed values from the orchestrator, this won't fire in practice, but if `pitch_delta_numerator` is ever called from a less-typed context (e.g. a CLI extension), `KeyError("foo")` is far less actionable than `ValueError("base must be in ('natural', 'sharp', 'flat'); got 'foo'")`.
**Fix:** Add a runtime guard:
```python
if base not in _BASE_OFFSET_CENTS:
    raise ValueError(
        f"base must be one of {tuple(_BASE_OFFSET_CENTS)}; got {base!r}"
    )
```

### IN-02: `SECTION_ORDER` carries an inner-element name that's never read

**File:** `src/cents_generator/constants.py:70-78` and `src/cents_generator/emit.py:292`
**Issue:** `SECTION_ORDER` is `tuple[tuple[str, str], ...]` — each entry is `(section_name, inner_entity_element_name)`. But `emit.py:292` iterates `for section_name, _entity_tag in SECTION_ORDER` and discards the second field. The inner element name is encoded redundantly inside each `_build_*` function (e.g. `ET.Element("TemperamentDefinition")`). Either drop it from `SECTION_ORDER` or use it as a sanity check.
**Fix:** Either flatten to `tuple[str, ...]`, or assert at build time that each section's payload tag matches `SECTION_ORDER[i][1]` to catch drift.

### IN-03: `test_class_b_template_shape` is misnamed — it uses default cents mode

**File:** `tests/test_compose.py:209`
**Issue:** The test is named `test_class_b_template_shape` and its docstring says "Reproduces the template's #-31 entity shape", but it never passes `mode="template"`. It uses the default `mode="cents"`. The shape assertions (z-orders, attachment offsets) are mode-independent so the test passes regardless, but the name implies a template-mode check that isn't happening.
**Fix:** Rename to `test_class_b_shape_matches_template_layout` (or similar — emphasize that we're verifying the layout shape, not exercising template mode) — or pass `mode="template"` for documentation parity.

### IN-04: `test_round_trip_xmllint_well_formed` does not gate on template presence

**File:** `tests/test_template_roundtrip.py:171-188`
**Issue:** The test runs `run(out_path, mode="template")` which doesn't read `TonalitySystemStartTemplate.doricolib`, but the test lives in `test_template_roundtrip.py` whose name implies template-dependence. It works (because mode='template' is build-only — only the round-trip diff requires the template file), but the placement is mildly inconsistent. Several other "round-trip" tests in this file (`test_round_trip_entity_count_matches_template`, `test_round_trip_accidental_names_match_template`, `test_round_trip_pitch_deltas_match_template`, `test_round_trip_file_version_is_1_1450`) similarly run without `_require_template()`. Not a bug — they don't compare against the file — but the naming is misleading.
**Fix:** Either rename the file `test_template_mode_emit.py` (since most tests here check what template-mode build emits), or move the non-comparison tests into `test_emit_format.py`.

### IN-05: `_BASE_PRIORITY` and `_BASE_DISPLAY` are private but distant from where they're used

**File:** `src/cents_generator/main.py:216-217`
**Issue:** Two module-level dicts (`_BASE_PRIORITY`, `_BASE_DISPLAY`) hold mappings used only inside `_cents_accidental_name`, `_cents_accidental_key`, and `build_cents_full_sweep`. They're declared 60+ lines before their first use. Co-locating with the helpers would aid readability. Minor.
**Fix:** Move both dict definitions immediately above `_cents_accidental_name` (or convert to function-local constants if Python micro-optimisation is irrelevant here, which it is).

### IN-06: Cents-mode `_cents_accidental_key` and the doc-only "+0" edge case

**File:** `src/cents_generator/main.py:227-235`
**Issue:** The function has a `cents == 0` branch that returns the bare base. This is essential — without it, `f"{base}{cents:+d}"` for `cents=0` would yield `"sharp+0"`, which would (a) collide with no real key but is semantically odd and (b) produce a different `entity_id` from `"sharp"`. The branch is correct. The concern is purely defensive: a reader seeing `f"{cents:+d}"` may not realize `+d` formats `0` as `"+0"`. A 1-line comment naming this trap would help.
**Fix:** Add a comment:

```python
def _cents_accidental_key(base: str, cents: int) -> str:
    # NB: '{cents:+d}' formats 0 as '+0' — explicit branch keeps the
    # zero-dev key as bare-base ('sharp', not 'sharp+0').
    if cents == 0:
        return base
    return f"{base}{cents:+d}"
```

### IN-07: `build_cents_full_sweep` uses string-typed forward reference for `AccidentalBundle`

**File:** `src/cents_generator/main.py:269-271`
**Issue:** The local list type annotation `list[tuple[int, int, int, "AccidentalBundle"]]` uses a forward-reference string for `AccidentalBundle`, with a comment that says "loose-typed to avoid a TYPE_CHECKING circular import shape." But `AccidentalBundle` is already imported at the top via `if TYPE_CHECKING: from .compose import AccidentalBundle` — there is no actual circular import (compose.py doesn't import from main.py). The string-quoted form works but the comment is misleading; the real reason is that `AccidentalBundle` is only available at type-check time, hence the string form.
**Fix:** Update the comment:

```python
# AccidentalBundle imported under TYPE_CHECKING to avoid pulling compose
# into main's runtime path; string-quoted forward reference required.
```

### IN-08: Phase 1 template tests in `test_compose.py` use bare keys that collide with Phase 2 cents-mode keys

**File:** `tests/test_compose.py:25-49, 100-112, 196-201, 322-348`
**Issue:** Several `build_class_a`/`build_class_c` tests in `test_compose.py` use `accidental_key="natural"` / `composite_key="natural"` / `accidental_key="natural+14"` etc. — exactly the keys Phase 2 cents-mode emits. This means the test produces an `AccidentalBundle` whose `entity_id` matches the production cents-mode entity. Tests run in isolation (no end-to-end emit), so no functional collision, but it's a maintenance hazard: a future test that emits AND asserts production-mode output, then runs alongside these tests, could see overlap. The intent was to use bare keys for brevity, but they happen to be the same keys D-05 locked forever.
**Fix:** No code change required. Optionally, prefix unit-test keys (`"natural-unit"`, `"natural+14-unit"`) to make it explicit that these aren't production paths. Keep current as-is if the alignment is intentional for verifying determinism.

---

_Reviewed: 2026-05-02T02:04:44Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
