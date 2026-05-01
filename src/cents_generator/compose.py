"""Three-class composite dispatcher.

Every accidental in the cents library falls into one of three visual classes
determined by (base, cents == 0). This module is the only place that
encodes that dispatch — adding a new shape (e.g. double-accidental + cents)
means adding a new class function here.

Phase 1 scope: implement build_class_a, build_class_b, build_class_c with
enough fidelity to reproduce the template's three entities (Natural, -14,
#-31). Phase 1 callers supply the pitch-delta string directly (since GEN-05's
centralized helper lands in Phase 2).

Each function returns an AccidentalBundle: an AccidentalDef + CompositeDef
plus optional shared GlyphDef and/or TextDef. The orchestrator (Plan 03)
deduplicates shared glyphs/texts across calls by entityID.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .constants import (
    FONT_DEFAULT_MUSIC,
    FONT_DEFAULT_TEXT,
    KIND_ACCIDENTAL,
    KIND_COMPOSITE,
    KIND_GLYPH,
    KIND_TEXT,
    SMUFL_FLAT,
    SMUFL_NATURAL,
    SMUFL_SHARP,
)
from .entities import (
    AccidentalDef,
    Component,
    CompositeDef,
    GlyphDef,
    RelativeAttachment,
    TextDef,
)
from .uuids import entity_id

# ----------------------------------------------------------------------------
# Class B / C visual constants — from template, validated against Dorico.
# ----------------------------------------------------------------------------
# Class B: sharp/flat glyph at zOrder=1, text at zOrder=2, attached
# kBaselineRight (glyph) ↔ kBaselineLeft (text) with offset (-8, -12).
# Source: TonalitySystemStartTemplate.doricolib lines 213-224.
CLASS_B_ATTACH_X_OFFSET: int = -8
CLASS_B_ATTACH_Y_OFFSET: int = -12

# Class C: text-only at xOffset=18, yOffset=-12, zOrder=0, no relativeAttachment.
# Source: TonalitySystemStartTemplate.doricolib lines 238-239.
CLASS_C_TEXT_X_OFFSET: int = 18
CLASS_C_TEXT_Y_OFFSET: int = -12


# ----------------------------------------------------------------------------
# Glyph factory — produces deterministic GlyphDefs for the 3 SMuFL accidentals
# ----------------------------------------------------------------------------
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


def _text_for(label: str) -> TextDef:
    """Create a TextDef with the canonical name '<label>.font.defaulttext'."""
    return TextDef(
        name=f"{label}.font.defaulttext",
        entity_id=entity_id(KIND_TEXT, label),
        text=label,
        font_style=FONT_DEFAULT_TEXT,
    )


# ----------------------------------------------------------------------------
# AccidentalBundle — return type for the three class functions
# ----------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class AccidentalBundle:
    """The set of entities produced by one accidental.

    - accidental: always 1, always unique to this accidental
    - composite:  always 1, always unique to this accidental (per ARCHITECTURE
                  reuse strategy — composites are never shared)
    - glyph:      1 for Class A (zero-deviation) and Class B (sharp/flat-base
                  with cents); None for Class C (natural-base with cents,
                  text-only)
    - text:       1 for Class B and Class C; None for Class A
    """
    accidental: AccidentalDef
    composite: CompositeDef
    glyph: GlyphDef | None
    text: TextDef | None

    @property
    def entities(self) -> tuple[object, ...]:
        """All non-None contained entities, for orchestrator dedup."""
        return tuple(e for e in (self.accidental, self.composite, self.glyph, self.text) if e is not None)


# ----------------------------------------------------------------------------
# Class A — zero-deviation: glyph only, no text, no relativeAttachment
# ----------------------------------------------------------------------------
def build_class_a(
    base: Literal["natural", "sharp", "flat"],
    *,
    accidental_name: str,
    accidental_key: str,
    composite_name: str,
    composite_key: str,
    pitch_delta_from_natural: str,
    cut_out_nw: tuple[float, float] = (0.0, 0.0),
    cut_out_ne: tuple[float, float] = (0.0, 0.0),
    cut_out_se: tuple[float, float] = (0.0, 0.0),
    cut_out_sw: tuple[float, float] = (0.0, 0.0),
) -> AccidentalBundle:
    """Build a Class A (glyph-only) accidental.

    Used by template's `Natural` entity. The pitch_delta_from_natural and
    cut_out_* values are caller-supplied so Plan 03 can emit Natural with
    the template's literal `0/24` and non-zero cut-outs verbatim.

    Phase 2 will introduce a higher-level wrapper that hardcodes "0/1200"
    for the three regular zero-deviation entries (Sharp, Flat, Natural) —
    but Phase 1's round-trip needs the exact template literal `0/24` for
    Natural, hence the explicit parameter.
    """
    glyph = _glyph_for(base)
    comp_eid = entity_id(KIND_COMPOSITE, composite_key)
    composite = CompositeDef(
        name=composite_name,
        entity_id=comp_eid,
        components=(
            Component(
                component_id=glyph.entity_id,
                component_type="kGlyph",
                x_offset=0, y_offset=0,
                z_order=0,
                component_instance=0,
            ),
        ),
        relative_attachments=(),
        category="kAccidentals",
    )
    accidental = AccidentalDef(
        name=accidental_name,
        entity_id=entity_id(KIND_ACCIDENTAL, accidental_key),
        composite_id=comp_eid,
        pitch_delta_from_natural=pitch_delta_from_natural,
        cut_out_nw=cut_out_nw,
        cut_out_ne=cut_out_ne,
        cut_out_se=cut_out_se,
        cut_out_sw=cut_out_sw,
    )
    return AccidentalBundle(accidental=accidental, composite=composite, glyph=glyph, text=None)


# ----------------------------------------------------------------------------
# Class B — sharp/flat-base + cents: glyph + text via relativeAttachment
# ----------------------------------------------------------------------------
def build_class_b(
    base: Literal["sharp", "flat"],
    *,
    accidental_name: str,
    accidental_key: str,
    composite_name: str,
    composite_key: str,
    label_text: str,
    pitch_delta_from_natural: str,
) -> AccidentalBundle:
    """Build a Class B (glyph + cents-label) accidental.

    Used by template's `#-31` entity. The glyph is at zOrder=1, the text at
    zOrder=2, with a relativeAttachment anchoring the text to the glyph's
    kBaselineRight via the text's kBaselineLeft using offset (-8, -12).
    """
    if base not in ("sharp", "flat"):
        raise ValueError(f"Class B requires base in ('sharp', 'flat'); got {base!r}")
    glyph = _glyph_for(base)
    text = _text_for(label_text)
    comp_eid = entity_id(KIND_COMPOSITE, composite_key)

    glyph_component = Component(
        component_id=glyph.entity_id,
        component_type="kGlyph",
        x_offset=0, y_offset=0,
        z_order=1,
        component_instance=0,
    )
    text_component = Component(
        component_id=text.entity_id,
        component_type="kText",
        x_offset=0, y_offset=0,
        z_order=2,
        component_instance=0,
    )
    attachment = RelativeAttachment(
        x_offset=CLASS_B_ATTACH_X_OFFSET,
        y_offset=CLASS_B_ATTACH_Y_OFFSET,
        pair1_component_instance_id=f"{glyph.entity_id}.0",
        pair1_attachment_point="kBaselineRight",
        pair2_component_instance_id=f"{text.entity_id}.0",
        pair2_attachment_point="kBaselineLeft",
    )
    composite = CompositeDef(
        name=composite_name,
        entity_id=comp_eid,
        components=(glyph_component, text_component),
        relative_attachments=(attachment,),
        category="kAccidentals",
    )
    accidental = AccidentalDef(
        name=accidental_name,
        entity_id=entity_id(KIND_ACCIDENTAL, accidental_key),
        composite_id=comp_eid,
        pitch_delta_from_natural=pitch_delta_from_natural,
    )
    return AccidentalBundle(accidental=accidental, composite=composite, glyph=glyph, text=text)


# ----------------------------------------------------------------------------
# Class C — natural-base + cents: text only, no glyph, no attachment
# ----------------------------------------------------------------------------
def build_class_c(
    *,
    accidental_name: str,
    accidental_key: str,
    composite_name: str,
    composite_key: str,
    label_text: str,
    pitch_delta_from_natural: str,
) -> AccidentalBundle:
    """Build a Class C (text-only, natural-base) accidental.

    Used by template's `-14` entity. The text is positioned via direct
    Component.x_offset=18, y_offset=-12; there is no glyph and no
    relativeAttachment.
    """
    text = _text_for(label_text)
    comp_eid = entity_id(KIND_COMPOSITE, composite_key)
    composite = CompositeDef(
        name=composite_name,
        entity_id=comp_eid,
        components=(
            Component(
                component_id=text.entity_id,
                component_type="kText",
                x_offset=CLASS_C_TEXT_X_OFFSET,
                y_offset=CLASS_C_TEXT_Y_OFFSET,
                z_order=0,
                component_instance=0,
            ),
        ),
        relative_attachments=(),
        category="kAccidentals",
    )
    accidental = AccidentalDef(
        name=accidental_name,
        entity_id=entity_id(KIND_ACCIDENTAL, accidental_key),
        composite_id=comp_eid,
        pitch_delta_from_natural=pitch_delta_from_natural,
    )
    return AccidentalBundle(accidental=accidental, composite=composite, glyph=None, text=text)
