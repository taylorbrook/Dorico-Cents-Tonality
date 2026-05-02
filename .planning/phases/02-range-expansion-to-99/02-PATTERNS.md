# Phase 2: Range Expansion to ±99¢ - Pattern Map

**Mapped:** 2026-05-01
**Files analyzed:** 9 (3 new + 6 modified)
**Analogs found:** 9 / 9 (every new/modified file has a strong in-repo analog)

---

## File Classification

| New/Modified File | Status | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|---|
| `src/cents_generator/pitch.py` | NEW (Claude's Discretion — D-06) | utility (pure math helper) | transform | `src/cents_generator/uuids.py` | role-match (single-purpose stdlib utility module) |
| `src/cents_generator/main.py` | MODIFIED | orchestrator | batch / pipeline | `src/cents_generator/main.py` (Phase 1 itself — extend in place) | exact (self-extension) |
| `src/cents_generator/compose.py` | MODIFIED | service / dispatcher | transform | `src/cents_generator/compose.py` (Phase 1 itself — `_GLYPH_SPEC` swap) | exact (self-extension) |
| `build.py` | MODIFIED | CLI entrypoint | request-response | `src/cents_generator/main.py::main()` (argparse pattern) | exact (existing parser grows one flag) |
| `tests/test_pitch.py` | NEW | test (unit) | transform | `tests/test_uuids.py` | exact (parametrized stdlib helper unit tests) |
| `tests/test_cents_structural.py` | NEW | test (structural invariants) | batch | `tests/test_template_roundtrip.py` (the count + name + section-order asserts) | exact (same shape, different fixture + bigger numbers) |
| `tests/test_cents_snapshot.py` | NEW | test (sampled byte snapshots + UUID pins) | batch | `tests/test_uuid_snapshot.py` | exact (pin known hex; verify in emitted body) |
| `tests/test_determinism.py` | MODIFIED | test (two-run byte-diff) | batch | `tests/test_determinism.py` (extend in place) | exact (add cents-mode fixtures) |
| `src/cents_generator/constants.py` | MODIFIED (additive only) | config | n/a | `src/cents_generator/constants.py` (append `CENTS_RANGE`, `KEY_*` if planner extracts) | exact (self-extension) |

> **Note:** `entities.py`, `emit.py`, `uuids.py` are **not modified** in Phase 2. They are reused verbatim. Phase 2 reads from them only.

---

## Pattern Assignments

### `src/cents_generator/pitch.py` (NEW — utility, transform)

**Analog:** `src/cents_generator/uuids.py`
**Why this analog:** Both are single-purpose stdlib-only "pure function over a constant" modules. `uuids.py` exposes one function (`entity_id`) over one pinned constant (`PROJECT_NAMESPACE`); `pitch.py` exposes one function (`pitch_delta_numerator`) over one pinned mapping (`{natural: 0, sharp: 100, flat: -100}`). Same shape, same forever-locked semantics, same test treatment.

**Module-docstring pattern** (mirror `uuids.py:1-7`):
```python
"""Deterministic entityID derivation for the cents Dorico tonality system.

Every entityID emitted into cents.doricolib is derived from a single pinned
project namespace UUID via uuid5 (RFC 9562 SHA-1 namespace hashing). Same
(kind, key) pair → same UUID forever — re-imports into Dorico match by
entityID and update existing entries instead of duplicating.
"""
```
→ Phase 2 should mirror this with: "Centralized pitch-delta math. The single source of truth (Pitfall 1: off-by-100 trap). `pitch_delta_numerator(base, cents)` is the ONLY place pitch math lives in cents mode."

**Locked-constant + `from __future__ import annotations` pattern** (`uuids.py:8-24`):
```python
from __future__ import annotations

import uuid

# ============================================================================
# PROJECT_NAMESPACE — PINNED ONCE. NEVER ROTATE.
# ----------------------------------------------------------------------------
# Rotating this UUID would break update-in-place semantics for every existing
# user [...]
# ============================================================================
PROJECT_NAMESPACE: uuid.UUID = uuid.UUID("6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c")
```
→ Phase 2 mirrors with `_BASE_OFFSET_CENTS: dict[str, int] = {"natural": 0, "sharp": 100, "flat": -100}` carrying the same "this lock derives Pitfall 1 prevention; do NOT alter without coordinated math review" comment block.

**Function signature + docstring + lookup-table pattern** (`uuids.py:27-50`):
```python
def entity_id(kind: str, key: str) -> str:
    """Return the prefixed entityID string for a (kind, key) pair.

    Format: '<kind>.user.<32 lowercase hex>'  (Dorico's canonical entityID shape)

    Args:
        kind: One of {'temperament-definition', 'accidental-system', ...}
        key:  A stable human-readable key. LOCK THESE FOREVER once shipped: ...

    Returns:
        A string like 'glyph.user.bf2fcca40371420f99106bd86bf99ab8'.
    """
    u = uuid.uuid5(PROJECT_NAMESPACE, f"{kind}:{key}")
    return f"{kind}.user.{u.hex}"
```
→ Phase 2 produces:
```python
from typing import Literal

def pitch_delta_numerator(base: Literal["natural", "sharp", "flat"], cents: int) -> int:
    """Return the numerator of pitchDeltaFromNatural for (base, cents).

    Defeats Pitfall 1 (off-by-100 trap): for `Sharp +14`, the correct delta
    is (100 + 14)/1200 = 114/1200, NOT 14/1200. Callers format as
    f"{n}/1200"; this helper returns only the integer numerator.

    Args:
        base:  one of "natural", "sharp", "flat".
        cents: signed cent deviation, e.g. -99..+99 in v1.

    Returns:
        Integer numerator. e.g. ("sharp", 14) → 114; ("flat", -7) → -107;
        ("natural", 0) → 0.
    """
    return _BASE_OFFSET_CENTS[base] + cents
```

**Critical pattern** (carried verbatim from CONTEXT.md D-06):
- Helper returns numerator ONLY. The `f"{n}/1200"` formatting happens at the call site (in `compose.py` or in a small wrapper inside `main.py`).
- Helper is **not** called from template-mode paths (`build_template_three()` keeps `"0/24"`, `"-14/1200"`, `"69/1200"` literals).

---

### `src/cents_generator/main.py` (MODIFIED — orchestrator, batch)

**Analog:** existing `build_template_three()` in the same file (lines 57-180)
**Why this analog:** Phase 2's new `build_cents_full_sweep()` (or chosen name) is the production-scale counterpart. Same function shape: returns `(temperament, acc_system, tonality, accidentals_tuple, composites_tuple, glyphs_tuple, texts_tuple)` for `emit.write()`. Same dedup-by-entityID pattern. Same singleton-construction pattern.

**Imports pattern** (`main.py:1-35`):
```python
"""Orchestrator + CLI entrypoint for the cents Dorico tonality-system generator.
[...]
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import TYPE_CHECKING

from .compose import build_class_a, build_class_b, build_class_c
from .constants import (
    KIND_ACCIDENTAL_SYSTEM,
    KIND_TEMPERAMENT,
    KIND_TONALITY_SYSTEM,
    TEMPERAMENT_12EDO_DIVISIONS,
)
from .emit import write
from .entities import (
    AccidentalDef, AccidentalSystemDef, CompositeDef, GlyphDef,
    TemperamentDef, TextDef, TonalitySystemDef,
)
from .uuids import entity_id

if TYPE_CHECKING:
    from collections.abc import Sequence
```
→ Phase 2 adds: `from .pitch import pitch_delta_numerator` (or imports from wherever the helper lands).

**Key-string locking pattern** (`main.py:44-54`):
```python
# Template-faithful key strings. These are stable forever — see Pitfall 6.
# Phase 2's full sweep will use the canonical 'sharp+14' / 'flat-50' /
# 'natural-7' format; Phase 1's three keys are template-specific and use
# distinct '-template' suffixes so they don't collide with Phase 2's keys
# in the same PROJECT_NAMESPACE.
_KEY_NATURAL_TEMPLATE   = "natural-template"
_KEY_MINUS_14_TEMPLATE  = "natural-14-template"
_KEY_SHARP_31_TEMPLATE  = "sharp-31-template"
_KEY_TEMPERAMENT_12EDO  = "12-edo-template"
_KEY_ACC_SYSTEM         = "psychography-template"
_KEY_TONALITY           = "psychography-template"
```
→ Phase 2 mirrors with cents-mode keys (block comment must say "LOCKS FOREVER per Pitfall 6 + D-05"):
```python
# Cents-mode keys. THESE LOCK FOREVER (D-05, Pitfall 6).
# Zero-deviation: bare base. Non-zero: f"{base}{signed_cents}", e.g. "sharp+14".
_KEY_TEMPERAMENT_12EDO_CENTS = "12-edo"
_KEY_ACC_SYSTEM_CENTS        = "cents"   # see CONTEXT.md Claude's Discretion
_KEY_TONALITY_CENTS          = "cents"
```

**Build function signature + return-tuple shape** (`main.py:57-65`):
```python
def build_template_three() -> tuple[
    TemperamentDef,
    AccidentalSystemDef,
    TonalitySystemDef,
    tuple[AccidentalDef, ...],
    tuple[CompositeDef, ...],
    tuple[GlyphDef, ...],
    tuple[TextDef, ...],
]:
```
→ Phase 2 `build_cents_full_sweep()` returns the same 7-tuple type signature. **Reuse this signature exactly** so `run()` can call either build function and pass results to `emit.write()` unchanged.

**Dedup-by-entityID pattern** (Phase 1 hardcodes 3 bundles, but the pattern is "construct N bundles, then collect unique entities by entityID"):
- Phase 1 dedups manually: `glyphs = (natural_bundle.glyph, sharp_glyph)` — only 2 glyphs because Class C's #-31 has no glyph.
- Phase 2 needs explicit dedup since the sweep produces 597 bundles with massive overlap (3 glyphs shared 597 ways, 198 texts shared up to 3 ways each). Use `dict[str, ...]` keyed on `entity_id` (per Pitfall 15: never iterate a `set`):

```python
# Dedup-by-entityID pattern (Pitfall 15 — never iterate a set).
glyph_by_id: dict[str, GlyphDef] = {}
text_by_id: dict[str, TextDef] = {}
accidentals_in_order: list[AccidentalDef] = []
composites_in_order: list[CompositeDef] = []

for base, cents in _iter_sweep():    # generator yielding (base, cents) in pitch-delta order
    bundle = _build_one(base, cents)  # dispatches Class A/B/C
    accidentals_in_order.append(bundle.accidental)
    composites_in_order.append(bundle.composite)
    if bundle.glyph is not None:
        glyph_by_id.setdefault(bundle.glyph.entity_id, bundle.glyph)
    if bundle.text is not None:
        text_by_id.setdefault(bundle.text.entity_id, bundle.text)
```

`dict.setdefault` preserves first-insertion order (guaranteed since Python 3.8) and is the explicit Pitfall-15 prevention.

**Sweep order (D-02 — pitch-delta ascending)**: build `(base, cents)` pairs sorted by `pitch_delta_numerator(base, cents)` ascending, with secondary key on `(base_priority, cents)` for tie-breaks (e.g. `Sharp -50` and `Natural +50` both at +50 — pick a stable tiebreak; the planner decides exact rule).

**Singleton construction** (Phase 1 reference, `main.py:115-144`) — copy verbatim, only changing keys + name:
```python
temperament = TemperamentDef(
    name="New Temperament Definition",
    entity_id=entity_id(KIND_TEMPERAMENT, _KEY_TEMPERAMENT_12EDO),
    note_a_to_b=TEMPERAMENT_12EDO_DIVISIONS[0],
    note_b_to_c=TEMPERAMENT_12EDO_DIVISIONS[1],
    # ...
)
acc_system = AccidentalSystemDef(
    name="New Accidental System",
    entity_id=entity_id(KIND_ACCIDENTAL_SYSTEM, _KEY_ACC_SYSTEM),
    accidental_definition_ids=( ... 3 IDs in template ... ),
)
tonality = TonalitySystemDef(
    name="Psychography",
    entity_id=entity_id(KIND_TONALITY_SYSTEM, _KEY_TONALITY),
    temperament_definition_id=temperament.entity_id,
    accidental_system_id=acc_system.entity_id,
)
```
→ Phase 2 cents-mode: `name="cents"` for `TonalitySystemDef`, key `"12-edo"` and `"cents"` for the other singletons. `accidental_definition_ids` is the 597-tuple in pitch-delta order (D-02).

**`run()` dispatch pattern** (`main.py:186-200`):
```python
def run(out_path: pathlib.Path) -> None:
    """Build the Phase 1 cents.doricolib (template-3-entity round-trip) and emit it."""
    temperament, acc_system, tonality, accidentals, composites, glyphs, texts = (
        build_template_three()
    )
    write(
        out_path,
        temperament=temperament,
        # ... etc
    )
```
→ Phase 2 grows `mode` parameter:
```python
def run(out_path: pathlib.Path, mode: Literal["cents", "template"] = "cents") -> None:
    if mode == "template":
        payload = build_template_three()
    else:
        payload = build_cents_full_sweep()
    temperament, acc_system, tonality, accidentals, composites, glyphs, texts = payload
    write(out_path, temperament=temperament, accidental_system=acc_system, ...)
```

**`main()` argparse pattern** (`main.py:206-223`):
```python
def main(argv: "Sequence[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build.py",
        description=(
            "Cents — Dorico tonality-system generator. "
            "Phase 1: emits the three template entities (Natural / -14 / #-31)."
        ),
    )
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=pathlib.Path("cents.doricolib"),
        help="Output path for the generated .doricolib (default: cents.doricolib in cwd).",
    )
    args = parser.parse_args(argv)
    run(args.out)
    print(f"wrote {args.out}", file=sys.stderr)
    return 0
```
→ Phase 2 grows the `--mode` flag:
```python
parser.add_argument(
    "--mode",
    choices=("cents", "template"),
    default="cents",
    help="Generator mode: 'cents' (production, 597 accidentals) or 'template' (Phase 1 round-trip, 3 entities). Default: cents.",
)
# ...
run(args.out, mode=args.mode)
```

---

### `src/cents_generator/compose.py` (MODIFIED — service, transform)

**Analog:** `_GLYPH_SPEC` and `_glyph_for()` in the same file (lines 61-83)
**Why this analog:** D-01 says cents-mode glyphs use ALL-empty `<parentEntityID/>` while template-mode preserves the Natural-inherits-factory quirk. The change is a per-mode swap of the `_GLYPH_SPEC` parent column.

**Existing pattern** (`compose.py:61-83`):
```python
_GLYPH_SPEC: dict[str, tuple[str, int, str]] = {
    # base → (smufl_name, codepoint, parent_entity_id)
    # Natural carries the factory parent_entity_id 'glyph.accidentalNatural'
    # (template line 130). Sharp and Flat have empty parent (template line 143).
    # NOTE: Phase 2 may switch all glyphs to empty parent for Dorico-version
    # decoupling; Phase 1 reproduces the template verbatim.
    "natural": ("accidentalNatural", SMUFL_NATURAL, "glyph.accidentalNatural"),
    "sharp":   ("accidentalSharp",   SMUFL_SHARP,   ""),
    "flat":    ("accidentalFlat",    SMUFL_FLAT,    ""),
}


def _glyph_for(base: Literal["natural", "sharp", "flat"]) -> GlyphDef:
    smufl_name, codepoint, parent = _GLYPH_SPEC[base]
    return GlyphDef(
        name=smufl_name,
        entity_id=entity_id(KIND_GLYPH, smufl_name),
        code_point=codepoint,
        parent_entity_id=parent,
        is_smufl=True,
        font_style=FONT_DEFAULT_MUSIC,
        point_size=1,
    )
```

**Phase 2 transition pattern (D-01)** — three viable shapes; planner chooses:

**Option A (recommended):** Add a second `_GLYPH_SPEC_CENTS` table and parametrize `_glyph_for(base, *, mode="cents")`:
```python
_GLYPH_SPEC_TEMPLATE: dict[str, tuple[str, int, str]] = {
    "natural": ("accidentalNatural", SMUFL_NATURAL, "glyph.accidentalNatural"),
    "sharp":   ("accidentalSharp",   SMUFL_SHARP,   ""),
    "flat":    ("accidentalFlat",    SMUFL_FLAT,    ""),
}

# Cents-mode: all-empty parents per D-01 (decouple from Dorico factory IDs;
# STACK.md §"Stack Patterns by Variant"). DO NOT collapse with the template
# spec — the template-mode round-trip is a permanent regression check that
# requires Natural to inherit 'glyph.accidentalNatural'.
_GLYPH_SPEC_CENTS: dict[str, tuple[str, int, str]] = {
    "natural": ("accidentalNatural", SMUFL_NATURAL, ""),
    "sharp":   ("accidentalSharp",   SMUFL_SHARP,   ""),
    "flat":    ("accidentalFlat",    SMUFL_FLAT,    ""),
}

_GLYPH_SPECS: dict[str, dict[str, tuple[str, int, str]]] = {
    "template": _GLYPH_SPEC_TEMPLATE,
    "cents":    _GLYPH_SPEC_CENTS,
}

def _glyph_for(base: Literal["natural", "sharp", "flat"], *, mode: Literal["cents", "template"] = "cents") -> GlyphDef:
    smufl_name, codepoint, parent = _GLYPH_SPECS[mode][base]
    return GlyphDef(...)  # unchanged otherwise
```
Then `build_class_a/b` accepts a `mode` kwarg and threads it to `_glyph_for`. Default `mode="cents"` keeps the production sweep ergonomic; template-mode call sites in `build_template_three()` pass `mode="template"`.

**CRITICAL pattern preservation** — every call to `_glyph_for(base)` in template paths MUST pass `mode="template"` after the change. Phase 1's existing tests (`test_class_a_natural_template_shape`, `test_template_roundtrip.py`) will fail otherwise. The planner must explicitly enumerate:
- `build_template_three()` → all `_glyph_for` calls become template-mode (or the build_class_a/b calls receive a `mode` kwarg that propagates).
- New cents-mode caller `build_cents_full_sweep()` → cents-mode (default).

**Reuse `_text_for(label)` verbatim** (`compose.py:86-93`):
```python
def _text_for(label: str) -> TextDef:
    """Create a TextDef with the canonical name '<label>.font.defaulttext'."""
    return TextDef(
        name=f"{label}.font.defaulttext",
        entity_id=entity_id(KIND_TEXT, label),
        text=label,
        font_style=FONT_DEFAULT_TEXT,
    )
```
This is correct for cents-mode unchanged. The `entity_id(KIND_TEXT, label)` call dedups all 198 unique cent labels naturally because `_text_for("+14")` always produces the same UUID regardless of which base accidental triggered the call.

**Reuse `build_class_a/b/c` signatures unchanged** — Phase 2's caller supplies:
- `pitch_delta_from_natural=f"{pitch_delta_numerator(base, cents)}/1200"` (the formatted string).
- `accidental_name`: e.g. `"Sharp +14"`, `"Flat -50"`, `"Natural -7"` — always-signed per FEATURES.md naming convention; zero-dev: `"Sharp"`, `"Flat"`, `"Natural"` (D-05).
- `accidental_key`: `f"{base}{signed}"` (e.g. `"sharp+14"`, `"flat-50"`); zero-dev: bare `"sharp"`, `"flat"`, `"natural"` (D-05). **LOCKS FOREVER.**
- `composite_name`: same convention as `accidental_name` per Claude's Discretion.
- `composite_key`: same as `accidental_key`.
- `label_text`: signed cents string (e.g. `"+14"`, `"-50"`); never used for zero-dev (Class A path).
- `cut_out_*`: default `(0, 0)` everywhere for cents-mode (Claude's Discretion).

---

### `build.py` (MODIFIED — CLI entrypoint)

**Analog:** the same file (lines 1-23 — pure shim that calls `cents_generator.main:main()`)
**Why this analog:** `build.py` does almost nothing; all argparse logic is inside `main.py::main()`. So `build.py` itself doesn't change — only `main()` in `main.py` grows the `--mode` flag (covered above). Read this row as: **`build.py` requires no edits if `main()` grows the flag in place.** The planner should confirm this and not introduce a redundant argparse layer in `build.py`.

```python
# build.py — current shape, unchanged in Phase 2:
from cents_generator.main import main

if __name__ == "__main__":
    raise SystemExit(main())
```

If the planner prefers `--mode` at the `build.py` level (NOT recommended — duplicates argparse), the existing pattern still applies but with a thin wrapper. **Recommended: leave `build.py` alone, grow `main()` in `main.py`.**

---

### `tests/test_pitch.py` (NEW — unit test)

**Analog:** `tests/test_uuids.py`
**Why this analog:** Same shape — small unit tests for a single helper module. `test_uuids.py` pins `entity_id` behavior; `test_pitch.py` pins `pitch_delta_numerator` behavior. Same import style, same `from __future__ import annotations`, same one-assertion-per-test discipline.

**Imports + module docstring pattern** (`test_uuids.py:1-9`):
```python
"""Determinism + format tests for entity_id() and PROJECT_NAMESPACE."""
from __future__ import annotations

import re
import uuid

from cents_generator.uuids import PROJECT_NAMESPACE, entity_id
```
→ Phase 2:
```python
"""Unit tests for pitch_delta_numerator (D-06, Pitfall 1: off-by-100 trap).

Hand-calculated cases pin the math against the natural-pitch reference frame.
For 'Sharp +14', the correct delta is (100 + 14)/1200 = 114/1200 — NOT 14/1200.
For 'Flat -7', the correct delta is (-100 + -7)/1200 = -107/1200.
Re-deriving these by hand on every test prevents the regression mode where
'I refactored the helper and the tests still pass because they share a bug'.
"""
from __future__ import annotations

from cents_generator.pitch import pitch_delta_numerator
```

**One-assertion-per-test pattern** (`test_uuids.py:23-44`):
```python
def test_entity_id_format_matches_dorico_pattern() -> None:
    eid = entity_id("accidental", "sharp+14")
    assert ENTITY_ID_PATTERN.match(eid), f"bad format: {eid!r}"


def test_entity_id_is_deterministic_across_calls() -> None:
    a = entity_id("accidental", "sharp+14")
    b = entity_id("accidental", "sharp+14")
    assert a == b


def test_entity_id_differs_by_key() -> None:
    a = entity_id("accidental", "sharp+14")
    b = entity_id("accidental", "sharp+15")
    assert a != b
```
→ Phase 2 mirrors with the 11 hand-calculated cases from CONTEXT.md D-06:
```python
def test_pitch_delta_sharp_14_is_114() -> None:
    assert pitch_delta_numerator("sharp", 14) == 114


def test_pitch_delta_sharp_minus_50_is_50() -> None:
    """The off-by-100 trap diagnostic case: would be -50 if calculated wrong."""
    assert pitch_delta_numerator("sharp", -50) == 50


def test_pitch_delta_flat_minus_7_is_minus_107() -> None:
    assert pitch_delta_numerator("flat", -7) == -107


def test_pitch_delta_flat_50_is_minus_50() -> None:
    """Flat-side enharmonic with positive cents."""
    assert pitch_delta_numerator("flat", 50) == -50


def test_pitch_delta_natural_minus_7_is_minus_7() -> None:
    assert pitch_delta_numerator("natural", -7) == -7


def test_pitch_delta_zero_dev_sharp_is_100() -> None:
    assert pitch_delta_numerator("sharp", 0) == 100


def test_pitch_delta_zero_dev_flat_is_minus_100() -> None:
    assert pitch_delta_numerator("flat", 0) == -100


def test_pitch_delta_zero_dev_natural_is_0() -> None:
    assert pitch_delta_numerator("natural", 0) == 0


def test_pitch_delta_boundary_sharp_99_is_199() -> None:
    assert pitch_delta_numerator("sharp", 99) == 199


def test_pitch_delta_boundary_flat_minus_99_is_minus_199() -> None:
    assert pitch_delta_numerator("flat", -99) == -199


def test_pitch_delta_boundary_natural_99_is_99() -> None:
    assert pitch_delta_numerator("natural", 99) == 99


def test_enharmonic_pair_sharp_minus_50_equals_natural_50() -> None:
    """Sharp -50 and Natural +50 are the same pitch (Pitfall 10)."""
    assert pitch_delta_numerator("sharp", -50) == pitch_delta_numerator("natural", 50) == 50
```

**No parametrize** — `test_uuids.py` doesn't use `pytest.parametrize` despite having repetitive cases. Stay consistent with that style: one explicit named test per case so failure messages name the offending case unambiguously.

---

### `tests/test_cents_structural.py` (NEW — structural invariants)

**Analog:** `tests/test_template_roundtrip.py` (specifically the count + name + section-order + xmllint asserts at lines 144-239)
**Why this analog:** Both tests run the orchestrator end-to-end and assert structural invariants on the emitted bytes. Phase 2 is the same pattern at the production scale: emit → read text → count substrings → assert.

**Build-and-emit pattern** (`test_template_roundtrip.py:191-204`):
```python
def test_round_trip_entity_count_matches_template(tmp_path: pathlib.Path) -> None:
    """The template has exactly: 1 Temperament, 1 AccidentalSystem, 3
    AccidentalDefinitions, 1 TonalitySystem, 2 Texts, 2 Glyphs, 3 Composites."""
    out_path = tmp_path / "generated.doricolib"
    run(out_path)
    body = out_path.read_text("utf-8")

    assert body.count("<TemperamentDefinition>") == 1
    assert body.count("<AccidentalSystem>") == 1
    assert body.count("<AccidentalDefinition>") == 3
    assert body.count("<TonalitySystemDefinition>") == 1
    assert body.count("<TextPrimitiveEntityDefinition>") == 2
    assert body.count("<GlyphPrimitiveEntityDefinition>") == 2
    assert body.count("<CompositeDefinition>") == 3
```
→ Phase 2 cents-mode counterpart (per D-07.2):
```python
def test_cents_entity_counts(tmp_path: pathlib.Path) -> None:
    """Cents-mode total = 1411: 1 Temperament + 1 AccidentalSystem + 597 Accidentals
    + 1 TonalitySystem + 198 Texts + 3 Glyphs + 597 Composites + 13 sub-entities (XML
    structural elements that don't count)."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    assert body.count("<TemperamentDefinition>") == 1
    assert body.count("<AccidentalSystem>") == 1
    assert body.count("<AccidentalDefinition>") == 597    # 594 + 3 zero-dev (D-07.2)
    assert body.count("<TonalitySystemDefinition>") == 1
    assert body.count("<TextPrimitiveEntityDefinition>") == 198   # one per signed cent ±99 (D-07.2)
    assert body.count("<GlyphPrimitiveEntityDefinition>") == 3    # natural, sharp, flat (D-07.2)
    assert body.count("<CompositeDefinition>") == 597
```

**Section-ordering pattern** (`test_template_roundtrip.py:144-168`):
→ Phase 2 reuses the exact same `gen_positions = [body.find(...) for tag in section_tags]; assert sorted` pattern.

**xmllint pattern** (`test_template_roundtrip.py:171-188`):
→ Phase 2 reuses verbatim — well-formedness check with ElementTree fallback.

**Tonality system name pattern** (`test_template_roundtrip.py:207-217`):
→ Phase 2:
```python
def test_cents_tonality_name(tmp_path: pathlib.Path) -> None:
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    assert "<name>cents</name>" in body
```

**Pitfall 8 invariant (NEW — Phase 2 owes this per D-08):**
```python
def test_cents_accidental_system_includes_natural(tmp_path: pathlib.Path) -> None:
    """Pitfall 8: removing the Natural accidental from AccidentalSystem causes
    Dorico to crash on note input. The 597-ID list MUST include all three
    zero-deviation entities (Sharp, Flat, Natural)."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    # Locate the <accidentalDefinitionIDs> element
    import re
    m = re.search(r"<accidentalDefinitionIDs>([^<]+)</accidentalDefinitionIDs>", body)
    assert m, "accidentalDefinitionIDs element not found"
    ids = m.group(1).split(", ")
    assert len(ids) == 597, f"expected 597 IDs, got {len(ids)}"

    # Resolve the three zero-dev entityIDs and assert presence.
    from cents_generator.uuids import entity_id
    from cents_generator.constants import KIND_ACCIDENTAL
    expected_natural = entity_id(KIND_ACCIDENTAL, "natural")
    expected_sharp = entity_id(KIND_ACCIDENTAL, "sharp")
    expected_flat = entity_id(KIND_ACCIDENTAL, "flat")
    assert expected_natural in ids
    assert expected_sharp in ids
    assert expected_flat in ids
```

**Pitfall 1 invariant (verify helper went through every accidental)**:
```python
def test_cents_no_zero_padded_pitch_deltas(tmp_path: pathlib.Path) -> None:
    """Pitfall 1: every non-zero-dev accidental's pitchDeltaFromNatural must
    have the helper-derived (base_offset + cents) numerator. Specifically,
    the off-by-100 trap diagnostic: 'Sharp -50' must produce 50/1200 NOT
    -50/1200; 'Flat +50' must produce -50/1200 NOT 50/1200."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    # Sharp -50 → 50/1200 (NOT -50/1200 — that would be Flat +50)
    # Flat +50 → -50/1200 (NOT 50/1200 — that would be Sharp -50)
    # Natural +50 → 50/1200 (Sharp -50 enharmonic)
    # We can't disambiguate purely by content (Sharp -50 and Natural +50 share
    # 50/1200), so the structural check is: count of each delta string.
    # In ±99 cents range, '50/1200' appears for both Sharp -50 and Natural +50 → 2 times.
    # And '-50/1200' appears for both Flat +50 and Natural -50 → 2 times.
    assert body.count("<pitchDeltaFromNatural>50/1200</pitchDeltaFromNatural>") == 2
    assert body.count("<pitchDeltaFromNatural>-50/1200</pitchDeltaFromNatural>") == 2
    # Boundary: 199/1200 should appear once (Sharp +99 only).
    assert body.count("<pitchDeltaFromNatural>199/1200</pitchDeltaFromNatural>") == 1
    # Boundary: -199/1200 should appear once (Flat -99 only).
    assert body.count("<pitchDeltaFromNatural>-199/1200</pitchDeltaFromNatural>") == 1
```

**Pitch-delta ascending order invariant (D-02)**:
```python
def test_cents_accidental_definition_ids_in_pitch_delta_order(tmp_path: pathlib.Path) -> None:
    """D-02: accidentalDefinitionIDs must be ordered by pitch delta ascending."""
    # Implementation: read the body, parse <pitchDeltaFromNatural> values
    # in document order from <AccidentalDefinition> blocks (pitch-delta order
    # for the accidentalDefinitions section per D-02 + Claude's Discretion),
    # OR resolve each entityID in the <accidentalDefinitionIDs> list back to
    # its delta and assert monotonic.
    ...
```

---

### `tests/test_cents_snapshot.py` (NEW — sampled byte snapshots + UUID pins)

**Analog:** `tests/test_uuid_snapshot.py`
**Why this analog:** Same role — pin specific entityIDs and assert they appear in the emitted XML. D-07.3 calls for ~6-10 representative `(AccidentalDefinition, CompositeDefinition)` blocks with byte-faithful comparison; the UUID-pinning half maps directly to `test_uuid_snapshot.py`'s pattern.

**UUID pin pattern** (`test_uuid_snapshot.py:31-51`):
```python
SNAPSHOT_TEMPERAMENT = "temperament-definition.user.aeae963766a157fbb1e4c2b0c127e8a7"
SNAPSHOT_ACCIDENTAL_SYSTEM = "accidental-system.user.a0e56c76efd450ecbb44120e7909d5d7"
SNAPSHOT_TONALITY = "tonalitysystem.user.9648fe6490d45bc180ac2166455fb224"

SNAPSHOT_ACCIDENTAL_SHARP_31 = "accidental.user.df943e16be3151d3bb5e6df4c4ceb5e3"
# ...
```
→ Phase 2 cents-mode pins for the diagnostic cases listed in CONTEXT.md D-07.3:
```python
# Pinned UUIDs for the 8 sampled cents-mode entities (D-07.3 — covers off-by-100
# trap, enharmonic pair, and ±99 boundaries). First-run capture from
# uuid5(PROJECT_NAMESPACE, f"{kind}:{key}").hex with the keys locked by D-05.
# DO NOT update these to make a test pass — that signals a regression bug
# (PROJECT_NAMESPACE rotation or key drift), NOT a test bug.
SNAPSHOT_ACCIDENTAL_SHARP_ZERO = "accidental.user.<TBD-first-run>"  # key="sharp"
SNAPSHOT_ACCIDENTAL_SHARP_PLUS_14 = "accidental.user.<TBD>"         # key="sharp+14"
SNAPSHOT_ACCIDENTAL_SHARP_MINUS_50 = "accidental.user.<TBD>"        # key="sharp-50" — off-by-100 trap
SNAPSHOT_ACCIDENTAL_FLAT_MINUS_7 = "accidental.user.<TBD>"          # key="flat-7"
SNAPSHOT_ACCIDENTAL_NATURAL_MINUS_7 = "accidental.user.<TBD>"       # key="natural-7"
SNAPSHOT_ACCIDENTAL_NATURAL_PLUS_50 = "accidental.user.<TBD>"       # key="natural+50" — enharmonic of sharp-50
SNAPSHOT_ACCIDENTAL_SHARP_PLUS_99 = "accidental.user.<TBD>"         # key="sharp+99" — boundary
SNAPSHOT_ACCIDENTAL_FLAT_MINUS_99 = "accidental.user.<TBD>"         # key="flat-99" — boundary
```
The planner's first-run task is identical to Plan 01-03's: run `entity_id(KIND_ACCIDENTAL, "sharp+14")` once, copy the hex into the snapshot constant, commit.

**End-to-end "every snapshot ID appears in body" pattern** (`test_uuid_snapshot.py:122-148`):
```python
def test_snapshot_emitted_xml_contains_all_entity_ids(tmp_path: pathlib.Path) -> None:
    """End-to-end check: every snapshot entityID appears in the emitted file.

    Catches regressions where build_template_three() returns the right values
    but emit.write() drops or rewrites them (Pitfall 3 silent-drop variant)."""
    from cents_generator.main import run as cli_run
    out = tmp_path / "snap.doricolib"
    cli_run(out)
    body = out.read_text("utf-8")

    expected = [
        SNAPSHOT_TEMPERAMENT,
        # ...
    ]
    missing = [e for e in expected if e not in body]
    assert not missing, f"snapshot entityIDs missing from emitted XML: {missing}"
```
→ Phase 2 mirrors with `cli_run(out, mode="cents")` and the cents snapshot list.

**Byte-faithful snapshot block pattern (NEW for D-07.3)** — *no direct in-repo analog* for "pin a multiline XML block string"; closest existing pattern is `test_template_roundtrip.py`'s `_normalize_entity_ids` + diff approach, but at smaller scope. Recommended approach: use `re` to extract the relevant `<AccidentalDefinition>...</AccidentalDefinition>` block from the emitted body, normalize entityIDs (reuse the regex helper from `test_template_roundtrip.py:36`), and compare to a pinned-string fixture:

```python
ENTITY_ID_RE = re.compile(r"([a-z-]+)\.user\.[0-9a-f]{32}")  # same as test_template_roundtrip.py:36

def _normalize_entity_ids(s: str) -> str:
    """Mask UUIDs to '<kind>.user.<HEX>' for byte-faithful comparison."""
    return ENTITY_ID_RE.sub(r"\1.user.<HEX>", s)


# Pinned snapshot for `Sharp +14` AccidentalDefinition block (post-normalization).
SNAPSHOT_SHARP_PLUS_14_ACCIDENTAL_BLOCK = """\t\t\t<AccidentalDefinition>
\t\t\t\t<name>Sharp +14</name>
\t\t\t\t<entityID>accidental.user.<HEX></entityID>
\t\t\t\t<parentEntityID/>
\t\t\t\t<inheritanceMask>0</inheritanceMask>
\t\t\t\t<compositeID>comp.user.<HEX></compositeID>
\t\t\t\t<pitchDeltaFromNatural>114/1200</pitchDeltaFromNatural>
\t\t\t\t<cutOutNW>(0, 0)</cutOutNW>
\t\t\t\t<cutOutNE>(0, 0)</cutOutNE>
\t\t\t\t<cutOutSE>(0, 0)</cutOutSE>
\t\t\t\t<cutOutSW>(0, 0)</cutOutSW>
\t\t\t</AccidentalDefinition>"""


def test_snapshot_sharp_plus_14_accidental_block(tmp_path: pathlib.Path) -> None:
    """Pin the byte content of the Sharp +14 AccidentalDefinition (off-by-100
    trap diagnostic)."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    # Extract the Sharp +14 block by name.
    m = re.search(
        r"\t\t\t<AccidentalDefinition>\n\t\t\t\t<name>Sharp \+14</name>\n.*?</AccidentalDefinition>",
        body, re.DOTALL,
    )
    assert m, "Sharp +14 AccidentalDefinition block not found"
    actual = _normalize_entity_ids(m.group(0))
    assert actual == SNAPSHOT_SHARP_PLUS_14_ACCIDENTAL_BLOCK, \
        f"snapshot diverged:\n  actual: {actual!r}\n  expected: {SNAPSHOT_SHARP_PLUS_14_ACCIDENTAL_BLOCK!r}"
```

The 8 snapshots (per D-07.3 + the off-by-100 trap diagnostic guidance in `<specifics>`):
1. `Sharp` (Class A zero-dev, +100/1200)
2. `Sharp +14` (Class B sharp+text, **114/1200** — off-by-100 trap)
3. `Sharp -50` (Class B sharp+text negative, **50/1200** — off-by-100 trap)
4. `Flat -7` (Class B flat+text, **-107/1200** — off-by-100 trap)
5. `Natural -7` (Class C, -7/1200)
6. `Natural +50` (Class C, **50/1200** — enharmonic of Sharp -50)
7. `Sharp +99` (Class B boundary, 199/1200)
8. `Flat -99` (Class B boundary, -199/1200)

For each, pin BOTH the AccidentalDefinition block and the corresponding CompositeDefinition block.

---

### `tests/test_determinism.py` (MODIFIED — extend in place for cents mode)

**Analog:** `tests/test_determinism.py` (the file itself — lines 15-67 are the three patterns to mirror)
**Why this analog:** Phase 2 needs determinism checks on cents mode in addition to template mode. Mirror each existing test with a `mode="cents"` variant.

**In-process two-run pattern** (`test_determinism.py:15-25`):
```python
def test_two_runs_in_process_are_byte_identical(tmp_path: pathlib.Path) -> None:
    path_a = tmp_path / "a.doricolib"
    path_b = tmp_path / "b.doricolib"
    run(path_a)
    run(path_b)
    a = path_a.read_bytes()
    b = path_b.read_bytes()
    assert a == b, (
        f"two consecutive in-process runs produced different output: "
        f"len(a)={len(a)}, len(b)={len(b)}"
    )
```
→ Phase 2 adds `..._cents_mode` variant:
```python
def test_two_runs_in_process_are_byte_identical_cents_mode(tmp_path: pathlib.Path) -> None:
    path_a = tmp_path / "a.doricolib"
    path_b = tmp_path / "b.doricolib"
    run(path_a, mode="cents")
    run(path_b, mode="cents")
    assert path_a.read_bytes() == path_b.read_bytes()
```

**Subprocess-CLI pattern** (`test_determinism.py:28-52`) — mirror with `["--mode", "cents", "--out", str(path)]`.

**Diff-command pattern** (`test_determinism.py:55-67`) — mirror with `mode="cents"` calls.

**Existing tests survive** — keep the original three (template-mode default) tests intact. The default `mode="cents"` change in `run()` means template-mode tests must explicitly pass `mode="template"` after Phase 2. Update the existing tests to do so:
```python
def test_two_runs_in_process_are_byte_identical(tmp_path: pathlib.Path) -> None:
    """Template mode (Phase 1 round-trip artifact) — survives as regression check."""
    path_a = tmp_path / "a.doricolib"
    path_b = tmp_path / "b.doricolib"
    run(path_a, mode="template")
    run(path_b, mode="template")
    assert path_a.read_bytes() == path_b.read_bytes()
```

Note: `test_template_roundtrip.py::test_round_trip_byte_identical_modulo_entity_ids` calls `run(out_path)` with no mode argument. Phase 2 must update that call to `run(out_path, mode="template")` once `run`'s default flips to `cents`. Same for every other `run(out_path)` call in `test_template_roundtrip.py` and `test_uuid_snapshot.py`. **The planner must enumerate these call-site fixes**.

---

### `src/cents_generator/constants.py` (MODIFIED — additive only)

**Analog:** the same file (the existing constants block — lines 38-78)
**Why this analog:** If the planner extracts `_KEY_TEMPERAMENT_12EDO_CENTS = "12-edo"`, `_KEY_ACC_SYSTEM_CENTS = "cents"`, `_KEY_TONALITY_CENTS = "cents"`, `CENTS_RANGE = range(-99, 100)`, etc., they fit the existing constants module's grouped + commented style:

```python
# ----------------------------------------------------------------------------
# EntityID kind prefixes. Dorico stores entityIDs as '<kind>.user.<32hex>'.
# NOTE: 'tonalitysystem' has no hyphen and no dot between 'tonality' and
# 'system' — this is a schema quirk verified in the template (line 80).
# ----------------------------------------------------------------------------
KIND_TEMPERAMENT: str       = "temperament-definition"
KIND_ACCIDENTAL_SYSTEM: str = "accidental-system"
# ...
```
→ Phase 2 mirror (if extracted):
```python
# ----------------------------------------------------------------------------
# Cents-mode key strings. THESE LOCK FOREVER (D-05, Pitfall 6).
# Renaming them creates duplicate entityIDs on user re-import. There is no
# clean migration path. Document major-version migrations in the README; do
# NOT rotate these constants.
# ----------------------------------------------------------------------------
KEY_TEMPERAMENT_12EDO_CENTS: str = "12-edo"
KEY_ACC_SYSTEM_CENTS: str        = "cents"
KEY_TONALITY_CENTS: str          = "cents"

# ----------------------------------------------------------------------------
# Cents-mode sweep range: ±99¢ around (natural, sharp, flat).
# Excludes 0 (the zero-dev case is emitted via bare-base keys, not "<base>+0").
# ----------------------------------------------------------------------------
CENTS_RANGE_NONZERO: tuple[int, ...] = tuple(c for c in range(-99, 100) if c != 0)
```

**ANTI-PATTERN to avoid:** `SECTION_ORDER` is the canonical Dorico-faithful order — Phase 2 MUST NOT modify it (Pitfall 13 — forward references are intentional). Comment in `constants.py` lines 60-66 already flags this; preserve verbatim.

---

## Shared Patterns

### Pattern: Deterministic UUID derivation (uuids.py is the only source)

**Source:** `src/cents_generator/uuids.py:27-50`
**Apply to:** Every entityID-bearing entity in `build_cents_full_sweep()` (one per accidental, composite, glyph, text, plus three singletons).

```python
from cents_generator.uuids import entity_id
from cents_generator.constants import KIND_ACCIDENTAL, KIND_COMPOSITE, KIND_TEXT

# Inside the sweep:
acc_eid = entity_id(KIND_ACCIDENTAL, "sharp+14")    # → "accidental.user.<32hex>"
comp_eid = entity_id(KIND_COMPOSITE, "sharp+14")    # → "comp.user.<32hex>"
text_eid = entity_id(KIND_TEXT, "+14")              # → "text.user.<32hex>"
```

**Pitfall 6 / D-05 lock:** The string passed to `entity_id` (the `key` arg) is the forever-locked stability contract. Zero-dev keys are bare: `"sharp"`, `"flat"`, `"natural"`. Non-zero keys are `"<base><signed>"`: `"sharp+14"`, `"flat-50"`, `"natural-7"`. Text keys are bare label strings: `"+14"`, `"-50"`, `"-7"` (the literal text label, including the sign).

### Pattern: Pure-stdlib + `from __future__ import annotations` discipline

**Source:** every file in `src/cents_generator/` opens with `from __future__ import annotations`.
**Apply to:** `src/cents_generator/pitch.py` (new file) MUST open with it. Every new Phase 2 test file (`test_pitch.py`, `test_cents_structural.py`, `test_cents_snapshot.py`) MUST open with it. No new pip dependencies — Phase 2 stays stdlib-only.

### Pattern: Frozen dataclasses for entities (no mutations between construction and emission)

**Source:** `src/cents_generator/entities.py:21-22, 40-41, 64-65 ...` — every dataclass uses `@dataclass(frozen=True, slots=True)`.
**Apply to:** Phase 2 does NOT add new dataclasses (reuse `entities.py` verbatim). If the planner introduces a small intermediate (e.g. a `SweepItem(NamedTuple)` for `(base, cents, sort_key)`), use `typing.NamedTuple` or `@dataclass(frozen=True, slots=True)` consistently.

### Pattern: Centralized formatters in emit.py (no string-concat XML emission)

**Source:** `src/cents_generator/emit.py:34-62` (`_fmt_tuple`, `_fmt_id_list`, `_fmt_bool`, `_fmt_hex_codepoint`, `SCALE_LITERAL`).
**Apply to:** Phase 2 does NOT add new formatters. The Class A/B/C dispatcher already feeds through `emit.write()`. The pitch-delta string is the only new formatted value, and `f"{pitch_delta_numerator(b, c)}/1200"` is constructed at the call site (in `compose.py` or `main.py`) and passed as the existing `pitch_delta_from_natural: str` arg to `build_class_a/b/c`. **Don't add a `_fmt_pitch_delta` helper to `emit.py`** — it would couple emit.py to pitch math and break the existing template-mode literal-string flow.

### Pattern: Section-internal ordering specified by orchestrator (not by emit.py)

**Source:** `emit.py:282-296` — `emit.write()` iterates `SECTION_ORDER` for section-emission order, but the orchestrator supplies pre-ordered tuples for entities within each section. `main.py:148-178` shows Phase 1 supplying explicit ordering.
**Apply to:** `build_cents_full_sweep()` must supply 7 ordered tuples per the rules:
- `accidentals`: 597-tuple in pitch-delta ascending order (D-02 + Claude's Discretion).
- `composites`: 597-tuple, same order as accidentals (Claude's Discretion).
- `glyphs`: 3-tuple — natural, sharp, flat (or whatever order — only 3 of them, planner picks).
- `texts`: 198-tuple in signed-cent ascending order: `-99, -98, ..., -1, +1, ..., +99` (Claude's Discretion).

### Pattern: Pitfall-15 dedup via `dict.setdefault`, never via `set` iteration

**Source:** PITFALLS.md Pitfall 15.
**Apply to:** `build_cents_full_sweep()` deduplicates the 597 glyph references (down to 3 unique) and the 597-ish text references (down to 198 unique) using `dict.setdefault(entity_id, entity)`, then `tuple(d.values())` for emission. NEVER `set()`; NEVER iterate a `set`.

### Pattern: Locale-independent literal formatting (Pitfall 14)

**Source:** `emit.py:61` — `SCALE_LITERAL: str = "100.000000"` is a string literal, not an f-string of a float.
**Apply to:** `pitch_delta_numerator` returns `int`; the `f"{n}/1200"` formatting uses integer interpolation (locale-independent). No floats anywhere in the pitch-delta path.

### Pattern: Test imports use full package path (`cents_generator.X`)

**Source:** every test file. E.g. `test_uuids.py:7`: `from cents_generator.uuids import PROJECT_NAMESPACE, entity_id`.
**Apply to:** Phase 2's three new test files use the same import style: `from cents_generator.pitch import pitch_delta_numerator`, `from cents_generator.main import run, build_cents_full_sweep`, etc.

### Pattern: Test file size — small, focused, one concern per file

**Source:** existing tests are 60-360 lines, one concern each (`test_uuids.py` = entity_id only, `test_compose.py` = three-class dispatcher only, `test_determinism.py` = two-run byte-diff only).
**Apply to:** Phase 2's three new test files split by concern as listed:
- `test_pitch.py`: helper math only (~80 lines, the 11 cases above).
- `test_cents_structural.py`: counts + invariants on the full sweep (~150 lines).
- `test_cents_snapshot.py`: UUID pins + sampled byte-block snapshots (~250 lines).

---

## No Analog Found

| File | Role | Data Flow | Reason | Recommended approach |
|---|---|---|---|---|
| (none) | — | — | — | — |

Every Phase 2 file has a strong in-repo analog. The closest "no analog" risk is the byte-faithful sampled-snapshot pattern in `test_cents_snapshot.py` — but `test_template_roundtrip.py`'s `_normalize_entity_ids` regex helper is reusable and the assertion shape is identical (extract block → normalize → compare to pinned string).

---

## Pitfall Coverage Matrix (cross-reference for planner)

| Pitfall | Phase 2 owes? | Where addressed |
|---|---|---|
| Pitfall 1 (off-by-100, CRITICAL) | YES (D-08) | `pitch.py` helper + `test_pitch.py` 11 cases + `test_cents_structural.py::test_cents_no_zero_padded_pitch_deltas` + `test_cents_snapshot.py` Sharp -50 / Sharp +14 / Flat -7 blocks |
| Pitfall 6 (key conventions lock forever) | YES | Locked-key constants block in `main.py` (or `constants.py`) with explicit "LOCKS FOREVER" comment + UUID-snapshot pins in `test_cents_snapshot.py` flag any drift |
| Pitfall 7 (XML formatting drift) | INDIRECTLY | Inherited from `emit.py` (already centralized). `test_cents_structural.py` is a regression net via xmllint + section-order asserts. |
| Pitfall 8 (Natural absent from AccidentalSystem) | YES (D-08) | `test_cents_structural.py::test_cents_accidental_system_includes_natural` |
| Pitfall 13 (forward-reference temptation) | INDIRECTLY | Inherited via `SECTION_ORDER` reuse — Phase 2 must NOT touch it. |
| Pitfall 15 (dict/set ordering) | YES | `dict.setdefault` in dedup (orchestrator pattern) + two-run determinism in `test_determinism.py` cents-mode variant. |

Pitfalls 2, 3, 4, 5, 9, 10, 11, 12, 14, 16, 17, 18 are owned by other phases per PITFALLS.md §"Pitfall-to-Phase Mapping".

---

## Metadata

**Analog search scope:**
- `src/cents_generator/` — all 6 modules read in full
- `tests/` — all 7 test files read in full
- `build.py` — read in full
- `.planning/phases/02-range-expansion-to-99/02-CONTEXT.md` — read in full
- `.planning/research/PITFALLS.md` — read in full

**Files scanned:** 16 (all source + tests + planning context)

**Pattern extraction date:** 2026-05-01

**Key constraints carried forward (locked, do not re-litigate):**
- D-01: cents-mode glyphs all-empty `<parentEntityID/>`; template mode keeps Natural-inherits-factory.
- D-04: `--mode cents|template`, default `cents`.
- D-05: zero-dev keys are bare `sharp`/`flat`/`natural`; non-zero keys are `<base><signed>` — LOCKS FOREVER.
- D-06: `pitch_delta_numerator(base, cents) -> int`, returns numerator only, ONLY place pitch math lives.
- D-07: layered tests = unit on helper + structural invariants + 6-10 sampled byte snapshots.
- D-08: Phase 2 owes Pitfall 1 (off-by-100) and Pitfall 8 (Natural in AccidentalSystem).
