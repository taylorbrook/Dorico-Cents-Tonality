---
phase: 01-generator-skeleton-template-round-trip
reviewed: 2026-05-01T23:55:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - src/cents_generator/__init__.py
  - src/cents_generator/uuids.py
  - src/cents_generator/constants.py
  - src/cents_generator/entities.py
  - src/cents_generator/compose.py
  - src/cents_generator/emit.py
  - src/cents_generator/main.py
  - build.py
  - conftest.py
  - tests/test_uuids.py
  - tests/test_entities.py
  - tests/test_compose.py
  - tests/test_emit_format.py
  - tests/test_template_roundtrip.py
  - tests/test_determinism.py
  - tests/test_uuid_snapshot.py
findings:
  blocker: 0
  high: 0
  medium: 4
  low: 5
  info: 3
  total: 12
verdict: APPROVE-WITH-FIXES
---

# Phase 1: Code Review Report

**Reviewed:** 2026-05-01T23:55:00Z
**Depth:** standard
**Python:** 3.14.2
**Files Reviewed:** 16
**Baseline Tests:** 81 passed in 0.16s (also 81 passed under PYTHONHASHSEED variations and `-O` flag)

## Summary

Phase 1 ships a deterministic, stdlib-only Python generator that reproduces the template's three entities byte-for-byte modulo entityIDs. The architecture is cleanly separated (uuids / constants / entities / compose / emit / main), determinism is defended at three layers (uuid5 unit tests, two-run byte equality tests, hex-snapshot pinning), and every Phase-1 pitfall is addressed in code with corresponding test coverage.

The implementation is correct and the tests are tight. No bugs that produce wrong output. No security exposure (build-time tool, no untrusted input). What I found is a small set of code-quality and robustness issues that should be addressed before Phase 2 scales the generator to ~1411 entities, plus a few low-priority cleanups.

The most important non-trivial finding (MED-01) is a duplicated test fixture in `test_emit_format.py` that already drifted from the orchestrator's keys. Phase 2 will compound this drift if not consolidated. None of the findings block Phase 1's success criteria.

**Verdict: APPROVE-WITH-FIXES** — Phase 1 deliverables meet stated success criteria; the issues listed below should be cleaned up before or during Phase 2.

## Findings

### MEDIUM

#### MED-01: Test fixture duplicates and drifts from orchestrator's accidental keys

- **File:** `tests/test_emit_format.py:82-164` (`_build_three_template_entities`) vs `src/cents_generator/main.py:49-180` (`build_template_three`)
- **Classification:** **WARNING** — code-quality / drift hazard
- **Issue:** `tests/test_emit_format.py::_build_three_template_entities` is a near-copy of `main.build_template_three`, but with different key strings. Specifically:
  - Test fixture uses `accidental_key="natural"` for the Natural Class-A bundle (line 87, 89)
  - Orchestrator uses `accidental_key="natural-template"` (`main.py:49`, `_KEY_NATURAL_TEMPLATE`)

  This means the fixture's Natural entity gets entityID `accidental.user.d883791e97b753e6a3c77d46827cee13`, while the orchestrator's gets `accidental.user.dc0afe1368685513856fddd1be5c4896` (verified by direct `entity_id()` re-derivation under the pinned namespace). Two parallel builds, two different outputs, both nominally "the template's three entities."

  Today the test still passes because `test_emit_format` only inspects format quirks of its own fixture's output — it never compares to `main.run()`. But:
  1. A reader navigating Phase 1 would reasonably assume the two builds produce the same bytes; they don't.
  2. Phase 2's range-expansion fixture will likely re-use this `_build_three_template_entities` shape; if the same drift continues, byte-comparison invariants between Plan 02 unit tests and Plan 03 integration tests will silently diverge again.
  3. The `-31` Class-B bundle and `-14` Class-C bundle DO use the orchestrator's keys (`sharp-31-template`, `natural-14-template`), so the drift is inconsistent — Natural drifted, the other two didn't. That's the worst-of-both-worlds case for a future grep-by-key audit.
- **Fix:** Consolidate. Either:
  - (a) Promote `_build_three_template_entities` out of `test_emit_format.py` into a shared `tests/conftest.py` fixture (or into a small helper in `cents_generator.main`), and have both `main.build_template_three` and the emit-format tests call the same builder.
  - (b) Just align the `accidental_key`/`composite_key` for Natural to `"natural-template"` to match the orchestrator. Then the snapshot test's `SNAPSHOT_ACCIDENTAL_NATURAL = "...dc0afe..."` value will match what the test fixture would produce too.

  Option (b) is the minimal fix:
  ```python
  # tests/test_emit_format.py
  natural_bundle = build_class_a(
      "natural",
      accidental_name="Natural",
      accidental_key="natural-template",   # was "natural"
      composite_name="Natural",
      composite_key="natural-template",    # was "natural"
      ...
  )
  ```

#### MED-02: `componentInstanceId` `.0` suffix is hardcoded; only safe because `component_instance` is always 0

- **File:** `src/cents_generator/compose.py:221, 223`
- **Classification:** **WARNING** — latent bug if `component_instance` ever moves off 0
- **Issue:** Class B's `RelativeAttachment` references the glyph and text components via:
  ```python
  pair1_component_instance_id=f"{glyph.entity_id}.0",
  pair2_component_instance_id=f"{text.entity_id}.0",
  ```
  while the corresponding `Component` instances are constructed at lines 209/216 with `component_instance=0`. The two values must agree (per CLAUDE.md: `componentInstanceId` is `<entityID>.<int>` where the int matches `componentInstance`). If a future change flips a `component_instance` to 1 or higher (e.g., for double-glyph composites in Phase 2 / v2), the relativeAttachment will silently dangle — `componentInstanceId` would still say `.0` while the actual `componentInstance` says `1`. Dorico's behavior on a dangling componentInstanceId is undefined and likely a Pitfall-3 silent-component-drop variant.

  This isn't a Phase-1 bug — `component_instance=0` everywhere. But it's a footgun planted in the dispatcher.
- **Fix:** Derive the suffix from the actual `Component` field, not a hardcoded `.0`:
  ```python
  glyph_component = Component(
      component_id=glyph.entity_id,
      component_type="kGlyph",
      ...
      component_instance=0,
  )
  text_component = Component(...)  # same
  attachment = RelativeAttachment(
      x_offset=CLASS_B_ATTACH_X_OFFSET,
      y_offset=CLASS_B_ATTACH_Y_OFFSET,
      pair1_component_instance_id=f"{glyph_component.component_id}.{glyph_component.component_instance}",
      pair1_attachment_point="kBaselineRight",
      pair2_component_instance_id=f"{text_component.component_id}.{text_component.component_instance}",
      pair2_attachment_point="kBaselineLeft",
  )
  ```
  Or, even better, expose a small helper `_instance_id(c: Component) -> str: return f"{c.component_id}.{c.component_instance}"` in `compose.py` and use it everywhere the `.N` suffix is needed.

#### MED-03: `emit.py` imports `TEMPERAMENT_12EDO_DIVISIONS` purely for "re-export visibility" but it never re-exports

- **File:** `src/cents_generator/emit.py:18`
- **Classification:** **WARNING** — dead code, misleading comment
- **Issue:** Line 18 reads:
  ```python
  from .constants import FILE_VERSION, SECTION_ORDER, TEMPERAMENT_12EDO_DIVISIONS  # noqa: F401  (TEMPERAMENT_12EDO_DIVISIONS used by Plan 03 callers; kept here for re-export visibility if Plan 03 imports from emit)
  ```
  But Plan 03's `main.py:23` imports `TEMPERAMENT_12EDO_DIVISIONS` directly from `.constants`, not from `.emit`. The same is true for `tests/test_emit_format.py:14`. AST analysis (verified during review) confirms `TEMPERAMENT_12EDO_DIVISIONS` is never referenced in `emit.py`'s body, and Python module imports do not auto-re-export unless declared in `__all__`. The `# noqa: F401` rationalization is incorrect — it's a genuinely unused import.
- **Fix:** Remove the unused name from the import:
  ```python
  from .constants import FILE_VERSION, SECTION_ORDER
  ```

#### MED-04: CLI emits raw traceback when `--out` parent directory doesn't exist

- **File:** `src/cents_generator/main.py:206-223` (`main` function)
- **Classification:** **WARNING** — UX / error-handling
- **Issue:** Running `python build.py --out /nonexistent-dir/foo.doricolib` exits with code 1 and prints a 15-line `FileNotFoundError` traceback originating in `pathlib.write_bytes`. For a build-tool CLI, this is poor UX — the user has no clean message saying "parent directory does not exist," only a stack trace pointing into `pathlib`. Not security-relevant; not a determinism bug; just rough edges that will surface during DIST-01 (README walkthrough).
- **Fix:** Wrap `run(args.out)` in `main()` in a focused try/except, or pre-check the parent directory:
  ```python
  def main(argv: "Sequence[str] | None" = None) -> int:
      parser = argparse.ArgumentParser(...)
      parser.add_argument("--out", type=pathlib.Path, default=...)
      args = parser.parse_args(argv)
      out_path: pathlib.Path = args.out
      if not out_path.parent.exists():
          parser.error(f"output directory does not exist: {out_path.parent}")
      run(out_path)
      print(f"wrote {out_path}", file=sys.stderr)
      return 0
  ```
  Using `parser.error(...)` exits with code 2 and emits a one-line message — the standard argparse pattern.

### LOW

#### LOW-01: `_fmt_tuple` will emit ugly floats for non-template values (e.g., `0.1+0.2`)

- **File:** `src/cents_generator/emit.py:34-43`
- **Classification:** **WARNING** — robustness for Phase 2
- **Issue:** `_fmt_tuple(0.1 + 0.2, 0)` returns `"(0.30000000000000004, 0)"`. For Phase 1 hardcoded values (template floats `0.192`, `2.116`, `0.476`, `0.512`, plus integers) this never triggers because all inputs are exact float literals. But Phase 2's range expansion may compute cut-out values, and any float arithmetic could leak this representation drift into the output, breaking the byte-identical determinism contract for some tuples.
- **Fix:** Either round explicitly inside the formatter (e.g., `round(v, 6)` then strip trailing zeros) or keep the formatter strict and document that callers must pass clean float literals — and add a test for both `(0.1+0.2, 0)` and a value that triggers the integer-vs-float branch crossing. Recommend the strict-callers approach since the template has only ~3 distinct cut-out values.

#### LOW-02: `assert` statements used for runtime invariants in `build_template_three`

- **File:** `src/cents_generator/main.py:165, 174`
- **Classification:** **WARNING** — robustness; assertions stripped under `python -O`
- **Issue:** Lines 165 and 174 use `assert ... is not None` as a type-narrowing mechanism for the static checker. Under `python -O`, these assertions are stripped, and although the behavior is currently still correct (Class B/C always return text; Class A/B always return glyph — guaranteed by `compose.py`), if any future refactor in `compose.py` ever returns `None` here, optimized runs would silently produce a tuple with a `None` in it, leading to a `TypeError` deep inside `emit._build_text/glyph` at run time. Verified runtime: `python3 -O build.py` works today, but the safety net is paper-thin.
- **Fix:** Use a `TYPE_CHECKING`-time `cast(...)`, or raise a real `RuntimeError` if the invariant fails:
  ```python
  if minus_14_text is None or sharp_minus_31_text is None:
      raise RuntimeError("compose.build_class_b/c must return non-None text")
  ```
  Same pattern for the glyph block.

#### LOW-03: Comment in `uuids.py` line 21-22 references "current task" / past action — violates CLAUDE.md comment hygiene

- **File:** `src/cents_generator/uuids.py:21-22`
- **Classification:** **WARNING** — convention violation per project CLAUDE.md
- **Issue:** Lines 21-22 read:
  ```python
  # This UUID was generated once with a random-UUID call (uuid v4) at project
  # inception and is now the project's seed identity for all entityID derivation.
  ```
  The user's CLAUDE.md profile (under "Frustrations" + repo conventions) says "default to writing no comments" and "don't reference the current task, fix, or callers." The line "was generated once... at project inception" is exactly that — narrative about how this constant came to be, not why it must stay this value. The "NEVER ROTATE" block above (lines 12-19) covers the why. The provenance line is noise.

  Note: this is a project-style violation only; the rest of `uuids.py`'s comment block (the never-rotate warning) is appropriate and required by GEN-04.
- **Fix:** Delete lines 21-22, keep the never-rotate block.

#### LOW-04: Inconsistent error type for invalid `base` between `build_class_a` and `build_class_b`

- **File:** `src/cents_generator/compose.py:73, 198-199`
- **Classification:** **WARNING** — API consistency
- **Issue:** Calling `build_class_a("double-sharp", ...)` raises `KeyError: 'double-sharp'` (from `_GLYPH_SPEC[base]`), while `build_class_b("natural", ...)` raises `ValueError("Class B requires base in ('sharp', 'flat'); got 'natural'")`. Same conceptual error, different exception type and message style. Class C doesn't take `base`, so isn't affected. For a public dispatch surface this should be uniform — pick `ValueError` everywhere.
- **Fix:** Add the same `if base not in (...): raise ValueError(...)` guard at the top of `build_class_a`, OR (better) move the validation into `_glyph_for`:
  ```python
  def _glyph_for(base: Literal["natural", "sharp", "flat"]) -> GlyphDef:
      if base not in _GLYPH_SPEC:
          raise ValueError(f"glyph base must be one of {tuple(_GLYPH_SPEC)}; got {base!r}")
      smufl_name, codepoint, parent = _GLYPH_SPEC[base]
      ...
  ```

#### LOW-05: `AccidentalBundle` imported but unused in `tests/test_compose.py`

- **File:** `tests/test_compose.py:7`
- **Classification:** **WARNING** — dead import
- **Issue:** Line 7 imports `AccidentalBundle` from `cents_generator.compose`, but the symbol is never referenced in the test body. Test functions invoke `build_class_a/b/c` and access fields like `b.accidental`, `b.glyph` directly — `AccidentalBundle` itself isn't constructed or type-asserted. Confirmed via `grep -nE "AccidentalBundle" tests/test_compose.py`: only the import line matches.
- **Fix:** Remove `AccidentalBundle` from the import block.

### INFO

#### INFO-01: `glyph.accidentalNatural` is a hardcoded factory entityID — Pitfall 13 risk acknowledged

- **File:** `src/cents_generator/compose.py:67`
- **Classification:** **INFO** — known issue, deferred
- **Issue:** The Natural glyph entry in `_GLYPH_SPEC` carries `parent_entity_id="glyph.accidentalNatural"`, coupling the generator's output to a Dorico factory entityID. PITFALLS Pitfall 13 + STACK.md both flag this: future Dorico versions could rename the factory glyph, breaking the parent reference and possibly causing import failure or visual regression. The plan acknowledges this and notes Phase 2 may switch all glyphs to empty parent for decoupling. Phase 1 reproduces the template verbatim (template line 130) so the round-trip diff stays clean.
- **Fix:** No action for Phase 1. Track for Phase 2: when scaling to 597 accidentals, the centralized policy should be empty-parent for all glyphs (per STACK.md recommendation). This will produce a non-template-faithful Natural glyph entityID structure but a more durable library across Dorico versions.

#### INFO-02: `conftest.py` lacks `from __future__ import annotations` (style inconsistency)

- **File:** `conftest.py:1-7`
- **Classification:** **INFO** — minor style inconsistency
- **Issue:** Every other `.py` file in the project starts with `from __future__ import annotations` (verified by grep). `conftest.py` does not. Strictly speaking, `conftest.py` doesn't need it — it has no type annotations — but the inconsistency stands out.
- **Fix:** Optional. Add the line for uniformity:
  ```python
  """Pytest configuration: prepend src/ to sys.path so 'import cents_generator' works."""
  from __future__ import annotations

  import sys
  ...
  ```

#### INFO-03: `build.py` and `conftest.py` independently shim `sys.path` to `src/` — duplication

- **File:** `build.py:14-17`, `conftest.py:5-7`
- **Classification:** **INFO** — micro-duplication, low impact
- **Issue:** Both files mutate `sys.path` to add `src/` so `import cents_generator` resolves. The two implementations are equivalent but not identical (`_SRC` vs `SRC`, different docstring). Long-term, the project should declare a `pyproject.toml` with `tool.setuptools.packages.find` or use a `[tool.pytest.ini_options] pythonpath = ["src"]` line, eliminating both shims. Out of scope for Phase 1; revisit when Phase 4 / DIST work begins (a real install path makes this question urgent).
- **Fix:** Defer to Phase 4 packaging.

## Test-coverage gaps

Spot-checked branches against tests:

| Area | Coverage |
|------|----------|
| `entity_id()` determinism, format, kind/key uniqueness | Strong — 10 tests |
| All 9 dataclasses construct + frozen | Strong — 15 tests |
| Three-class composite shape | Strong — 11 tests |
| Format quirks (tabs, hex, booleans, tuples, IDs, scale, self-close) | Strong — 27 tests |
| Round-trip vs template, modulo entityIDs | Strong — 8 tests |
| Determinism (in-process, subprocess, diff-recipe) | Strong — 3 tests |
| Hex snapshot pinning | Strong — 7 tests |

Two minor branches lack direct coverage:

- **`_fmt_tuple` non-integer float branch with rounding error:** No test for `_fmt_tuple(0.1+0.2, 0)`. Add when fixing LOW-01.
- **`emit.py` `_build_glyph` `alternate_for_glyph` non-empty branch:** Lines 189-190 only fire when `g.alternate_for_glyph` is truthy. No test exercises that branch (Phase 1 always has empty `alternate_for_glyph`). Acceptable for Phase 1; track for Phase 2 if any glyph ever uses an alternate.

No critical missing tests.

## Convention adherence

- **Stdlib only:** ✓ Verified — only `__future__`, `argparse`, `pathlib`, `sys`, `uuid`, `dataclasses`, `typing`, `re`, `xml.etree`, `collections` used across `src/` + `build.py` + `conftest.py`.
- **Python 3.11+ only features:** ✓ Uses `T | None` union syntax, `tuple[...]` generic, `Literal`, dataclass `slots=True` (3.10+). All compatible.
- **Determinism (no `uuid.uuid4`/`uuid.uuid1`, no time, no random):** ✓ Verified — only `uuid.uuid5(PROJECT_NAMESPACE, ...)`, no `time`/`random`/`os.urandom`.
- **`from __future__ import annotations`:** ✓ Consistent across all `.py` files except `conftest.py` (see INFO-02).
- **Frozen dataclasses with `slots=True`:** ✓ All 9 entity dataclasses + `AccidentalBundle` use `frozen=True, slots=True`.
- **Tab indentation in emitted XML, lowercase `utf-8` declaration, raw `n/d` rationals, `0xE26X` uppercase hex, six-decimal float literals, comma-space ID lists, self-closing empty arrays:** ✓ All verified by `test_emit_format.py` (27 tests) and the round-trip test.
- **No `print` debug statements:** ✓ The single `print(f"wrote {args.out}", file=sys.stderr)` in `main.py:222` is intentional CLI feedback.
- **No commented-out code:** ✓ No commented-out blocks found.
- **No TODO/FIXME/XXX/HACK markers in `src/`:** ✓ Verified.
- **Comment hygiene per project CLAUDE.md:** ✗ Minor violation in `uuids.py:21-22` (LOW-03).

## Byte-fidelity post-process safety review (per review focus)

The two bounded byte replacements in `emit.py:319, 332` were specifically called out for review. Verified:

- **` />` → `/>` replacement (line 319):** Provably safe. ElementTree always escapes `>` in element text and attribute values (verified empirically: `Element.text = "x />"` produces `<...>x /&gt;</...>`; attribute `x="a />"` produces `x="a /&gt;"`). The literal byte sequence ` />` therefore can only appear in well-formed ET output as the trailing characters of a self-closing tag. The replacement cannot mutate user-visible content.

- **XML-declaration single-quote → double-quote replacement (lines 328-335):** Provably safe. The replacement is bounded to the first line (everything up to the first `\n`). ET's default attribute syntax inside the document body uses double quotes; only the XML declaration uses single quotes. Verified empirically with multiple inputs. The `if body.startswith(b"<?xml ")` guard prevents accidental application to any future ET output that lacks a declaration.

Both replacements are correctly bounded and do not accidentally touch user-visible content.

## Forward-reference safety (per review focus)

`SECTION_ORDER` in `constants.py:70-78` is a fixed 7-tuple in Dorico's canonical order, and `emit.py:292-296` iterates it directly without any sorting or topological reordering. The "DO NOT REORDER" comment block (`constants.py:60-69`) and `compose.py`'s deliberate forward references match Pitfall 13's prescription.

## Off-by-100 trap (per review focus)

Phase 1 is correct here: the three pitch-delta strings (`"0/24"`, `"-14/1200"`, `"69/1200"`) are template literals passed in as parameters from `main.build_template_three()` (`main.py:86, 100, 111`). No code path in Phase 1 computes a pitch-delta numerator from `(base, cents)` — the centralized helper is GEN-05 / Phase 2's scope. There is exactly ONE place that produces pitch-delta strings (the orchestrator), and its values are pinned by `test_round_trip_pitch_deltas_match_template`. The trap is closed for Phase 1.

## Determinism correctness (per review focus)

Verified beyond the test suite:

- `python3 build.py` invoked twice → identical 9057-byte output (MD5 `5f207c1de7f8ddf7f0af678384828cd4`).
- `PYTHONHASHSEED=12345 python3 build.py` and `PYTHONHASHSEED=99999 python3 build.py` produce identical bytes.
- `python3 -O build.py` produces identical bytes (assertions stripped — orchestrator still works because non-None invariants hold by construction).
- No `set` iteration anywhere in the emission path; tuples used throughout for ordered collections.
- `uuid.uuid5` with a pinned namespace; no `uuid.uuid4`/`uuid.uuid1`.

Determinism is well-defended.

## Verdict

**APPROVE-WITH-FIXES**

Phase 1 meets all four stated success criteria with substantive test evidence. The codebase is clean, modular, and the determinism story is robust at three layers. None of the findings above prevent shipping Phase 1's deliverable.

Recommended fix prioritization before Phase 2 begins:

1. **MED-01** (consolidate test fixture vs orchestrator) — fixes a drift that will compound at Phase 2 scale.
2. **MED-02** (derive `componentInstanceId` suffix from `Component.component_instance`) — prevents a latent dangling-reference bug if Phase 2 ever uses non-zero instances.
3. **MED-03, MED-04** — small cleanups; do them while you're in the file.
4. **LOW-01..05, INFO-01..03** — opportunistic.

---

_Reviewed: 2026-05-01T23:55:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
