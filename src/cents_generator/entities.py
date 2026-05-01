"""Frozen dataclasses for every entity type emitted into cents.doricolib.

Each class is a pure data container. XML emission lives in emit.py (Plan 02).
Frozen + slots prevents accidental mutation between construction and emission,
which is important for determinism.

Entity ID values are stored as full prefixed strings (e.g.
'glyph.user.bf2fcca40371420f99106bd86bf99ab8'), not raw uuid.UUID objects.
The kind prefix is part of Dorico's entity-reference contract and must always
travel with the hex.
"""
from __future__ import annotations

from dataclasses import dataclass


# ----------------------------------------------------------------------------
# Helper sub-structs (used inside CompositeDef, not emitted as top-level entities)
# ----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Component:
    """One element inside a CompositeDefinition's <components> array.

    Refers to either a GlyphPrimitiveEntityDefinition (component_type='kGlyph')
    or a TextPrimitiveEntityDefinition (component_type='kText') by entityID.
    """
    component_id: str            # full prefixed entityID, e.g. "glyph.user.<hex>"
    component_type: str          # "kGlyph" or "kText"
    x_offset: int = 0
    y_offset: int = 0
    x_scale: float = 100.0       # emitted as "100.000000" (six-decimal string)
    y_scale: float = 100.0
    z_order: int = 0
    max_optical_scale: int = 100
    component_instance: int = 0
    colour: str = "kDefault"


@dataclass(frozen=True, slots=True)
class RelativeAttachment:
    """Positional anchoring between two component instances.

    Used by Class B composites (sharp/flat-base + cents text) to anchor the
    cent label to the glyph's baseline. Class A and Class C composites do not
    use this.

    The componentInstanceId fields are '<entityID>.<componentInstance>' — the
    trailing '.0' (or other int) matches the corresponding Component's
    component_instance value. Always '.0' for our use case.
    """
    x_offset: int                       # template uses int e.g. -8 (line 214)
    y_offset: int                       # template uses int e.g. -12 (line 215)
    pair1_component_instance_id: str    # e.g. "glyph.user.<hex>.0"
    pair1_attachment_point: str         # "kBaselineRight"
    pair2_component_instance_id: str    # e.g. "text.user.<hex>.0"
    pair2_attachment_point: str         # "kBaselineLeft"


# ----------------------------------------------------------------------------
# Top-level entity types — one dataclass per <SECTION_ORDER> entry
# ----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TemperamentDef:
    """One TemperamentDefinition. Defines diatonic step sizes summing to 1200¢.

    12-EDO uses (200, 100, 200, 200, 100, 200, 200) per
    constants.TEMPERAMENT_12EDO_DIVISIONS.
    """
    name: str
    entity_id: str
    note_a_to_b: int
    note_b_to_c: int
    note_c_to_d: int
    note_d_to_e: int
    note_e_to_f: int
    note_f_to_g: int
    note_g_to_a: int
    parent_entity_id: str = ""
    inheritance_mask: int = 0
    precedence: int = 0


@dataclass(frozen=True, slots=True)
class AccidentalSystemDef:
    """One AccidentalSystem. Lists all accidental entityIDs in the picker
    as a single comma-space-joined string in <accidentalDefinitionIDs>."""
    name: str
    entity_id: str
    accidental_definition_ids: tuple[str, ...]
    parent_entity_id: str = ""
    inheritance_mask: int = 0
    precedence: int = 0


@dataclass(frozen=True, slots=True)
class AccidentalDef:
    """One AccidentalDefinition. Carries playback math
    (pitch_delta_from_natural as a raw 'n/d' string), visual reference
    (composite_id), and four cutOut tuples for collision shape.

    pitch_delta_from_natural is a literal string like '69/1200' or '-14/1200'
    or '0/24' (Natural in template uses 0/24 — see PITFALLS Pitfall 7;
    denominator is whatever Dorico wrote, NOT auto-reduced)."""
    name: str
    entity_id: str
    composite_id: str
    pitch_delta_from_natural: str
    cut_out_nw: tuple[float, float] = (0.0, 0.0)
    cut_out_ne: tuple[float, float] = (0.0, 0.0)
    cut_out_se: tuple[float, float] = (0.0, 0.0)
    cut_out_sw: tuple[float, float] = (0.0, 0.0)
    parent_entity_id: str = ""
    inheritance_mask: int = 0


@dataclass(frozen=True, slots=True)
class TonalitySystemDef:
    """One TonalitySystemDefinition. Ties a temperament to an accidental
    system; carries one minimal empty customKeySignature stub (handled by
    emit.py — no fields needed here)."""
    name: str
    entity_id: str
    temperament_definition_id: str
    accidental_system_id: str
    parent_entity_id: str = ""
    inheritance_mask: int = 0


@dataclass(frozen=True, slots=True)
class TextDef:
    """One TextPrimitiveEntityDefinition. Holds a literal text label
    (e.g. '-14') and the font-style alias. Name follows
    '<text>.font.defaulttext' convention from the template (line 108)."""
    name: str
    entity_id: str
    text: str
    font_style: str = "font.defaulttext"
    parent_entity_id: str = ""
    inheritance_mask: int = 0


@dataclass(frozen=True, slots=True)
class GlyphDef:
    """One GlyphPrimitiveEntityDefinition. References a SMuFL codepoint via
    the music-font alias.

    Two patterns appear in the template:
    - accidentalNatural carries parent_entity_id='glyph.accidentalNatural'
      (inheriting from a Dorico factory glyph; template line 130).
    - accidentalSharp has parent_entity_id='' empty (template line 143).

    For Phase 1 round-trip we faithfully reproduce both shapes. STACK.md
    recommends empty parent for new generator entries to avoid factory
    version coupling — Phase 2 will adopt that policy generally."""
    name: str
    entity_id: str
    code_point: int                  # e.g. 0xE262 (emitted as '0xE262' upper hex)
    parent_entity_id: str = ""
    is_smufl: bool = True
    alternate_for_glyph: str = ""
    font_style: str = "font.defaultmusic"
    point_size: int = 1
    rotation: int = 0
    colour: str = "kDefault"
    inheritance_mask: int = 0


@dataclass(frozen=True, slots=True)
class CompositeDef:
    """One CompositeDefinition. The visual recipe: ordered components and
    zero or more relativeAttachments. category='kAccidentals' for accidental
    composites. scaling_rules is always empty for our use case (handled by
    emit.py as self-closing <scalingRules array="true"/>)."""
    name: str
    entity_id: str
    components: tuple[Component, ...]
    relative_attachments: tuple[RelativeAttachment, ...] = ()
    category: str = "kAccidentals"
    parent_entity_id: str = ""
    inheritance_mask: int = 0
