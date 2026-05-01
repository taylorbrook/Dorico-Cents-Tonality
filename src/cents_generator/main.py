"""Orchestrator + CLI entrypoint for the cents Dorico tonality-system generator.

Phase 1 scope: build the three template entities (Natural / -14 / #-31) plus
the Psychography singletons, dedupe by entityID, and emit via emit.write.
The output is a structurally complete .doricolib that round-trips byte-for-byte
against TonalitySystemStartTemplate.doricolib (modulo entityIDs).

Phase 2 will replace build_template_three() with a parameter sweep over
(natural, sharp, flat) x range(-99, 100) and a centralized pitch-delta helper.
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
    AccidentalDef,
    AccidentalSystemDef,
    CompositeDef,
    GlyphDef,
    TemperamentDef,
    TextDef,
    TonalitySystemDef,
)
from .uuids import entity_id

if TYPE_CHECKING:
    from collections.abc import Sequence


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
# Public API
# ----------------------------------------------------------------------------
def run(out_path: pathlib.Path) -> None:
    """Build the Phase 1 cents.doricolib (template-3-entity round-trip) and emit it."""
    temperament, acc_system, tonality, accidentals, composites, glyphs, texts = (
        build_template_three()
    )
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


if __name__ == "__main__":
    raise SystemExit(main())
