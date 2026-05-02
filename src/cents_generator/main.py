"""Orchestrator + CLI entrypoint for the cents Dorico tonality-system generator.

Two build paths coexist in this module:

- build_template_three() (Phase 1, preserved per D-03) reproduces the
  TonalitySystemStartTemplate.doricolib's three-entity Psychography library
  byte-for-byte (modulo entityIDs). Reachable via `--mode template`.

- build_cents_full_sweep() (Phase 2) emits the production cents.doricolib:
  597 accidentals (3 zero-dev + 594 non-zero) across (natural, sharp, flat)
  x signed cents in {0} U range(-99..+99) excluding 0; total entity count
  1411. Reachable via `--mode cents` (the default).

Pitch math in cents mode is centralized in pitch_delta_numerator (D-06,
GEN-05). Template mode preserves Phase 1's literal pitch-delta strings
('0/24', '-14/1200', '69/1200') verbatim — that's intentional template
fidelity, NOT a bug.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import TYPE_CHECKING, Literal

from .compose import build_class_a, build_class_b, build_class_c
from .constants import (
    CENTS_RANGE_NONZERO,
    KEY_ACC_SYSTEM_CENTS,
    KEY_TEMPERAMENT_12EDO_CENTS,
    KEY_TONALITY_CENTS,
    KIND_ACCIDENTAL_SYSTEM,
    KIND_GLYPH,
    KIND_TEMPERAMENT,
    KIND_TEXT,
    KIND_TONALITY_SYSTEM,
    TEMPERAMENT_12EDO_DIVISIONS,
)
from .emit import write
from .entities import (
    AccidentalDef,
    AccidentalSystemDef,
    CompositeDef,
    GlyphDef,
    TemperamentDef,
    TextDef,
    TonalitySystemDef,
)
from .pitch import pitch_delta_numerator
from .uuids import entity_id

if TYPE_CHECKING:
    from collections.abc import Sequence
    from .compose import AccidentalBundle


# ----------------------------------------------------------------------------
# Phase 1 round-trip: build the 3 template entities (Natural / -14 / #-31)
# ----------------------------------------------------------------------------
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


def build_template_three() -> tuple[
    TemperamentDef,
    AccidentalSystemDef,
    TonalitySystemDef,
    tuple[AccidentalDef, ...],
    tuple[CompositeDef, ...],
    tuple[GlyphDef, ...],
    tuple[TextDef, ...],
]:
    """Reproduce the working template's three accidentals + Psychography singletons.

    Returns the singletons + four ordered tuples (accidentals, composites, glyphs,
    texts) ready to pass to emit.write. Tuple ordering matches the template.

    Composite-class assignment:
    - Natural    = Class A (glyph-only, zero deviation)
    - -14        = Class C (text-only, natural-base)
    - #-31       = Class B (sharp-base + cents text)

    Pitch-delta values are template literals (NOT computed via a helper —
    Phase 2 introduces the centralized pitch_delta_numerator(base, cents)).
    """
    # ---- Class A: Natural (template lines 62-73, 157-179, 127-139) ---------
    natural_bundle = build_class_a(
        "natural",
        accidental_name="Natural",
        accidental_key=_KEY_NATURAL_TEMPLATE,
        composite_name="Natural",
        composite_key=_KEY_NATURAL_TEMPLATE,
        pitch_delta_from_natural="0/24",  # template literal — see PITFALLS Pitfall 7
        cut_out_nw=(0.0, 0.0),
        cut_out_ne=(0.192, 2.116),         # template line 70
        cut_out_se=(0.0, 0.0),
        cut_out_sw=(0.476, 0.512),         # template line 72
        mode="template",                   # Phase 1 quirk: Natural inherits 'glyph.accidentalNatural'
    )

    # ---- Class C: -14 (text-only, natural-base; template lines 50-61, 228-250, 107-114) ----
    minus_14_bundle = build_class_c(
        accidental_name="-14",
        accidental_key=_KEY_MINUS_14_TEMPLATE,
        composite_name="New Composite",
        composite_key=_KEY_MINUS_14_TEMPLATE,
        label_text="-14",
        pitch_delta_from_natural="-14/1200",
    )

    # ---- Class B: #-31 (sharp + cents text; template lines 38-49, 180-227, 140-152, 115-122) ----
    sharp_minus_31_bundle = build_class_b(
        "sharp",
        accidental_name="#-31",
        accidental_key=_KEY_SHARP_31_TEMPLATE,
        composite_name="New Composite",
        composite_key=_KEY_SHARP_31_TEMPLATE,
        label_text="-31",
        pitch_delta_from_natural="69/1200",  # template literal: 100 + (-31) = 69 (Pitfall 1)
        mode="template",                     # signature symmetry; Sharp's parent is empty in both modes
    )

    # ---- Singletons (Psychography tonality, 12-EDO temperament) ------------
    temperament = TemperamentDef(
        name="New Temperament Definition",
        entity_id=entity_id(KIND_TEMPERAMENT, _KEY_TEMPERAMENT_12EDO),
        note_a_to_b=TEMPERAMENT_12EDO_DIVISIONS[0],
        note_b_to_c=TEMPERAMENT_12EDO_DIVISIONS[1],
        note_c_to_d=TEMPERAMENT_12EDO_DIVISIONS[2],
        note_d_to_e=TEMPERAMENT_12EDO_DIVISIONS[3],
        note_e_to_f=TEMPERAMENT_12EDO_DIVISIONS[4],
        note_f_to_g=TEMPERAMENT_12EDO_DIVISIONS[5],
        note_g_to_a=TEMPERAMENT_12EDO_DIVISIONS[6],
    )

    # accidentalDefinitionIDs ordering matches template line 31:
    # Natural, -14, #-31.
    acc_system = AccidentalSystemDef(
        name="New Accidental System",
        entity_id=entity_id(KIND_ACCIDENTAL_SYSTEM, _KEY_ACC_SYSTEM),
        accidental_definition_ids=(
            natural_bundle.accidental.entity_id,
            minus_14_bundle.accidental.entity_id,
            sharp_minus_31_bundle.accidental.entity_id,
        ),
    )

    tonality = TonalitySystemDef(
        name="Psychography",
        entity_id=entity_id(KIND_TONALITY_SYSTEM, _KEY_TONALITY),
        temperament_definition_id=temperament.entity_id,
        accidental_system_id=acc_system.entity_id,
    )

    # ---- Section-internal orderings (matching template byte-for-byte) ------
    # accidentalDefinitions: #-31, -14, Natural (template lines 38-73)
    accidentals: tuple[AccidentalDef, ...] = (
        sharp_minus_31_bundle.accidental,
        minus_14_bundle.accidental,
        natural_bundle.accidental,
    )

    # compositeDefinitions: Natural, #-31's "New Composite", -14's "New Composite"
    # (template lines 157-250)
    composites: tuple[CompositeDef, ...] = (
        natural_bundle.composite,
        sharp_minus_31_bundle.composite,
        minus_14_bundle.composite,
    )

    # textDefinitions: -14, -31 (template lines 107-122)
    minus_14_text = minus_14_bundle.text
    sharp_minus_31_text = sharp_minus_31_bundle.text
    assert minus_14_text is not None and sharp_minus_31_text is not None  # Class C and B always provide text
    texts: tuple[TextDef, ...] = (
        minus_14_text,           # -14
        sharp_minus_31_text,     # -31
    )

    # glyphDefinitions: accidentalNatural, accidentalSharp (template lines 127-152)
    natural_glyph = natural_bundle.glyph
    sharp_glyph = sharp_minus_31_bundle.glyph
    assert natural_glyph is not None and sharp_glyph is not None  # Class A and B always provide glyph
    glyphs: tuple[GlyphDef, ...] = (
        natural_glyph,           # accidentalNatural
        sharp_glyph,             # accidentalSharp
    )

    return temperament, acc_system, tonality, accidentals, composites, glyphs, texts


# ----------------------------------------------------------------------------
# Phase 2 cents-mode sweep: 597 accidentals, 198 dedup'd cent labels, 3 glyphs.
# ----------------------------------------------------------------------------
# Section-internal output ordering (D-02 + Claude's discretion locked here):
# - accidentals + composites + accidentalDefinitionIDs string: by
#   (pitch_delta, base_priority, cents) ascending; flat=0 < natural=1 < sharp=2
#   for tiebreaks at the same delta (e.g. Natural +50 before Sharp -50 at
#   delta=50).
# - texts: by signed cent ascending (-99..-1, +1..+99).
# - glyphs: natural, sharp, flat (deterministic stable order).
#
# Cut-outs default to (0, 0) for all four corners on every cents-mode
# accidental — the (0.192, 2.116) etc. values in template mode are template
# quirks (Phase 1 fidelity only).
# ----------------------------------------------------------------------------
_BASE_PRIORITY: dict[str, int] = {"flat": 0, "natural": 1, "sharp": 2}
_BASE_DISPLAY: dict[str, str] = {"sharp": "Sharp", "flat": "Flat", "natural": "Natural"}


def _cents_accidental_name(base: str, cents: int) -> str:
    """e.g. ('sharp', 14) -> 'Sharp +14'; ('sharp', 0) -> 'Sharp'."""
    if cents == 0:
        return _BASE_DISPLAY[base]
    return f"{_BASE_DISPLAY[base]} {cents:+d}"


def _cents_accidental_key(base: str, cents: int) -> str:
    """e.g. ('sharp', 14) -> 'sharp+14'; ('sharp', 0) -> 'sharp'.

    LOCKED FOREVER per D-05 + Pitfall 6. Renaming this format (or any
    zero-dev bare-base value) creates duplicate entityIDs on user re-import.
    """
    if cents == 0:
        return base
    return f"{base}{cents:+d}"


def build_cents_full_sweep() -> tuple[
    TemperamentDef,
    AccidentalSystemDef,
    TonalitySystemDef,
    tuple[AccidentalDef, ...],
    tuple[CompositeDef, ...],
    tuple[GlyphDef, ...],
    tuple[TextDef, ...],
]:
    """Build the full cents-mode .doricolib payload: 1411 entities total.

    Sweeps (base, cents) for base in (natural, sharp, flat) and cents in
    (0,) + range(-99..-1) + range(1..99). Class A for cents==0; Class B for
    sharp/flat with cents != 0; Class C for natural with cents != 0.

    Pitch deltas come from pitch_delta_numerator (D-06, GEN-05) — the only
    place pitch math lives in cents mode (Pitfall 1 defense).

    Returns the same 7-tuple shape as build_template_three() so run() can
    dispatch to either build function and pass the result to emit.write
    unchanged.

    Output counts:
    - 1 TemperamentDef (12-EDO, name='12-EDO')
    - 1 AccidentalSystemDef (name='cents', 597 IDs sorted by pitch delta)
    - 1 TonalitySystemDef (name='cents')
    - 597 AccidentalDefs (3 zero-dev + 594 non-zero)
    - 597 CompositeDefs (one per accidental)
    - 3 GlyphDefs (natural, sharp, flat — all <parentEntityID/> empty per D-01)
    - 198 TextDefs (one per signed cent value -99..-1, +1..+99)
    """
    # (delta, base_priority, cents, AccidentalBundle) — bundle is loose-typed
    # to avoid a TYPE_CHECKING circular import shape.
    bundles: list[tuple[int, int, int, "AccidentalBundle"]] = []
    glyph_by_id: dict[str, GlyphDef] = {}
    text_by_id: dict[str, TextDef] = {}

    for base in ("natural", "sharp", "flat"):
        # Iterate (0,) + non-zero range. cents == 0 -> Class A; otherwise
        # Class B (sharp/flat) or Class C (natural).
        for cents in (0, *CENTS_RANGE_NONZERO):
            acc_name = _cents_accidental_name(base, cents)
            acc_key = _cents_accidental_key(base, cents)
            pdelta = pitch_delta_numerator(base, cents)
            pdelta_str = f"{pdelta}/1200"

            if cents == 0:
                bundle = build_class_a(
                    base,
                    accidental_name=acc_name,
                    accidental_key=acc_key,
                    composite_name=acc_name,
                    composite_key=acc_key,
                    pitch_delta_from_natural=pdelta_str,
                    # cut-outs default to (0, 0) on all four corners.
                    mode="cents",
                )
            elif base == "natural":
                bundle = build_class_c(
                    accidental_name=acc_name,
                    accidental_key=acc_key,
                    composite_name=acc_name,
                    composite_key=acc_key,
                    label_text=f"{cents:+d}",
                    pitch_delta_from_natural=pdelta_str,
                )
            else:  # base in ("sharp", "flat")
                bundle = build_class_b(
                    base,
                    accidental_name=acc_name,
                    accidental_key=acc_key,
                    composite_name=acc_name,
                    composite_key=acc_key,
                    label_text=f"{cents:+d}",
                    pitch_delta_from_natural=pdelta_str,
                    mode="cents",
                )

            bundles.append((pdelta, _BASE_PRIORITY[base], cents, bundle))

            # Pitfall 15 dedup: dict.setdefault preserves first-insertion order
            # and is deterministic across PYTHONHASHSEED randomization.
            if bundle.glyph is not None:
                glyph_by_id.setdefault(bundle.glyph.entity_id, bundle.glyph)
            if bundle.text is not None:
                text_by_id.setdefault(bundle.text.entity_id, bundle.text)

    # Sort by (delta, base_priority, cents) ascending — D-02 ordering.
    # Tiebreak: flat=0 < natural=1 < sharp=2 at the same delta.
    bundles.sort(key=lambda t: (t[0], t[1], t[2]))

    accidentals: tuple[AccidentalDef, ...] = tuple(b[3].accidental for b in bundles)
    composites: tuple[CompositeDef, ...] = tuple(b[3].composite for b in bundles)

    # Glyph order: natural, sharp, flat (stable, deterministic).
    glyph_natural = glyph_by_id[entity_id(KIND_GLYPH, "accidentalNatural")]
    glyph_sharp = glyph_by_id[entity_id(KIND_GLYPH, "accidentalSharp")]
    glyph_flat = glyph_by_id[entity_id(KIND_GLYPH, "accidentalFlat")]
    glyphs: tuple[GlyphDef, ...] = (glyph_natural, glyph_sharp, glyph_flat)

    # Text order: signed cent ascending (-99..-1, +1..+99). 198 entries.
    # Build by walking the sorted nonzero range and resolving entityIDs.
    ordered_text_keys = [f"{c:+d}" for c in CENTS_RANGE_NONZERO]  # already sorted ascending
    texts: tuple[TextDef, ...] = tuple(
        text_by_id[entity_id(KIND_TEXT, k)] for k in ordered_text_keys
    )

    # Singletons — D-05 locked keys, D-04 cents tonality "cents".
    temperament = TemperamentDef(
        name="12-EDO",
        entity_id=entity_id(KIND_TEMPERAMENT, KEY_TEMPERAMENT_12EDO_CENTS),
        note_a_to_b=TEMPERAMENT_12EDO_DIVISIONS[0],
        note_b_to_c=TEMPERAMENT_12EDO_DIVISIONS[1],
        note_c_to_d=TEMPERAMENT_12EDO_DIVISIONS[2],
        note_d_to_e=TEMPERAMENT_12EDO_DIVISIONS[3],
        note_e_to_f=TEMPERAMENT_12EDO_DIVISIONS[4],
        note_f_to_g=TEMPERAMENT_12EDO_DIVISIONS[5],
        note_g_to_a=TEMPERAMENT_12EDO_DIVISIONS[6],
    )

    # AccidentalSystem's IDs string: D-02 — sorted by pitch delta ascending.
    acc_system = AccidentalSystemDef(
        name="cents",
        entity_id=entity_id(KIND_ACCIDENTAL_SYSTEM, KEY_ACC_SYSTEM_CENTS),
        accidental_definition_ids=tuple(a.entity_id for a in accidentals),
    )

    tonality = TonalitySystemDef(
        name="cents",
        entity_id=entity_id(KIND_TONALITY_SYSTEM, KEY_TONALITY_CENTS),
        temperament_definition_id=temperament.entity_id,
        accidental_system_id=acc_system.entity_id,
    )

    return temperament, acc_system, tonality, accidentals, composites, glyphs, texts


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------
def run(
    out_path: pathlib.Path,
    mode: Literal["cents", "template"] = "cents",
) -> None:
    """Build the cents.doricolib and emit it.

    mode='cents' (default): the production 1411-entity sweep over
    (natural, sharp, flat) x signed cents in {0} U range(-99..+99) excluding 0.
    mode='template': Phase 1's three-entity round-trip artifact, preserved
    as a permanent regression check on the Class A/B/C dispatcher's
    structural fidelity against TonalitySystemStartTemplate.doricolib.
    """
    if mode == "template":
        payload = build_template_three()
    else:
        payload = build_cents_full_sweep()
    temperament, acc_system, tonality, accidentals, composites, glyphs, texts = payload
    write(
        out_path,
        temperament=temperament,
        accidental_system=acc_system,
        tonality_system=tonality,
        accidentals=accidentals,
        composites=composites,
        glyphs=glyphs,
        texts=texts,
    )


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def main(argv: "Sequence[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build.py",
        description=(
            "Cents — Dorico tonality-system generator. "
            "mode='cents' (default): emits the 1411-entity full sweep "
            "(597 accidentals across natural/sharp/flat ±99¢). "
            "mode='template': emits the Phase 1 template round-trip "
            "(3 entities: Natural / -14 / #-31)."
        ),
    )
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=pathlib.Path("cents.doricolib"),
        help="Output path for the generated .doricolib (default: cents.doricolib in cwd).",
    )
    parser.add_argument(
        "--mode",
        choices=("cents", "template"),
        default="cents",
        help=(
            "Generator mode: 'cents' (production, 597 accidentals) or "
            "'template' (Phase 1 round-trip, 3 entities). Default: cents."
        ),
    )
    args = parser.parse_args(argv)
    run(args.out, mode=args.mode)
    print(f"wrote {args.out} (mode={args.mode})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
