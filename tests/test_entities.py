"""Construction tests for entity dataclasses.

Verifies frozen + slots semantics and field defaults match the template's
most common values. Does not test XML emission (that lives in emit.py / Plan 02).
"""
from __future__ import annotations

import pytest

from cents_generator.entities import (
    AccidentalDef,
    AccidentalSystemDef,
    Component,
    CompositeDef,
    GlyphDef,
    RelativeAttachment,
    TemperamentDef,
    TextDef,
    TonalitySystemDef,
)


def test_temperament_def_constructs_with_12edo_divisions() -> None:
    t = TemperamentDef(
        name="New Temperament Definition",
        entity_id="temperament-definition.user.deadbeef",
        note_a_to_b=200, note_b_to_c=100, note_c_to_d=200, note_d_to_e=200,
        note_e_to_f=100, note_f_to_g=200, note_g_to_a=200,
    )
    assert t.note_a_to_b == 200
    assert t.precedence == 0
    assert t.inheritance_mask == 0
    assert t.parent_entity_id == ""


def test_temperament_def_is_frozen() -> None:
    t = TemperamentDef(
        name="t", entity_id="x", note_a_to_b=200, note_b_to_c=100,
        note_c_to_d=200, note_d_to_e=200, note_e_to_f=100,
        note_f_to_g=200, note_g_to_a=200,
    )
    with pytest.raises((AttributeError, Exception)):
        t.note_a_to_b = 999  # type: ignore[misc]


def test_accidental_system_def_takes_tuple_of_ids() -> None:
    a = AccidentalSystemDef(
        name="New Accidental System",
        entity_id="accidental-system.user.x",
        accidental_definition_ids=("accidental.user.a", "accidental.user.b"),
    )
    assert len(a.accidental_definition_ids) == 2
    # Tuple is immutable — required for frozen dataclass.
    assert isinstance(a.accidental_definition_ids, tuple)


def test_accidental_def_default_cutouts_are_zero() -> None:
    a = AccidentalDef(
        name="Sharp +14",
        entity_id="accidental.user.x",
        composite_id="comp.user.y",
        pitch_delta_from_natural="114/1200",
    )
    assert a.cut_out_nw == (0.0, 0.0)
    assert a.cut_out_ne == (0.0, 0.0)
    assert a.cut_out_se == (0.0, 0.0)
    assert a.cut_out_sw == (0.0, 0.0)


def test_accidental_def_natural_template_cutouts() -> None:
    # Natural in the template has non-zero cutOutNE and cutOutSW (line 70, 72).
    a = AccidentalDef(
        name="Natural",
        entity_id="accidental.user.x",
        composite_id="comp.user.y",
        pitch_delta_from_natural="0/24",
        cut_out_ne=(0.192, 2.116),
        cut_out_sw=(0.476, 0.512),
    )
    assert a.cut_out_ne == (0.192, 2.116)
    assert a.cut_out_sw == (0.476, 0.512)


def test_accidental_def_pitch_delta_is_raw_string() -> None:
    # Must be a string (raw 'n/d'), NOT auto-reduced.
    a = AccidentalDef(
        name="x", entity_id="x", composite_id="y",
        pitch_delta_from_natural="-14/1200",
    )
    assert a.pitch_delta_from_natural == "-14/1200"
    assert isinstance(a.pitch_delta_from_natural, str)


def test_text_def_defaults_to_font_defaulttext() -> None:
    t = TextDef(
        name="-14.font.defaulttext",
        entity_id="text.user.x",
        text="-14",
    )
    assert t.font_style == "font.defaulttext"


def test_glyph_def_defaults_to_font_defaultmusic() -> None:
    g = GlyphDef(
        name="accidentalSharp",
        entity_id="glyph.user.x",
        code_point=0xE262,
    )
    assert g.font_style == "font.defaultmusic"
    assert g.is_smufl is True
    assert g.point_size == 1
    assert g.parent_entity_id == ""


def test_glyph_def_natural_inherits_factory_parent() -> None:
    # accidentalNatural in the template inherits parent_entity_id='glyph.accidentalNatural'.
    g = GlyphDef(
        name="accidentalNatural",
        entity_id="glyph.user.x",
        code_point=0xE261,
        parent_entity_id="glyph.accidentalNatural",
    )
    assert g.parent_entity_id == "glyph.accidentalNatural"


def test_component_constructs_with_template_offsets() -> None:
    # Class C text-only composite uses xOffset=18, yOffset=-12 (template line 238-239).
    c = Component(
        component_id="text.user.x",
        component_type="kText",
        x_offset=18,
        y_offset=-12,
    )
    assert c.x_offset == 18
    assert c.y_offset == -12
    assert c.x_scale == 100.0
    assert c.y_scale == 100.0


def test_relative_attachment_class_b_offsets() -> None:
    # Class B composite uses (-8, -12) per template line 213-215.
    r = RelativeAttachment(
        x_offset=-8,
        y_offset=-12,
        pair1_component_instance_id="glyph.user.x.0",
        pair1_attachment_point="kBaselineRight",
        pair2_component_instance_id="text.user.y.0",
        pair2_attachment_point="kBaselineLeft",
    )
    assert r.x_offset == -8
    assert r.y_offset == -12


def test_composite_def_class_a_no_attachments_no_text() -> None:
    # Natural (Class A) composite: 1 component (glyph), no attachments.
    c = CompositeDef(
        name="Natural",
        entity_id="comp.user.x",
        components=(Component(component_id="glyph.user.x", component_type="kGlyph"),),
    )
    assert len(c.components) == 1
    assert c.relative_attachments == ()
    assert c.category == "kAccidentals"


def test_composite_def_class_b_has_two_components_and_one_attachment() -> None:
    comp = CompositeDef(
        name="New Composite",
        entity_id="comp.user.x",
        components=(
            Component(component_id="glyph.user.s", component_type="kGlyph", z_order=1),
            Component(component_id="text.user.t", component_type="kText", z_order=2),
        ),
        relative_attachments=(
            RelativeAttachment(
                x_offset=-8, y_offset=-12,
                pair1_component_instance_id="glyph.user.s.0",
                pair1_attachment_point="kBaselineRight",
                pair2_component_instance_id="text.user.t.0",
                pair2_attachment_point="kBaselineLeft",
            ),
        ),
    )
    assert len(comp.components) == 2
    assert len(comp.relative_attachments) == 1


def test_composite_def_class_c_text_only_no_attachment() -> None:
    # text-only composite: 1 component (text), no attachment, text positioned via xOffset/yOffset.
    c = CompositeDef(
        name="New Composite",
        entity_id="comp.user.x",
        components=(
            Component(
                component_id="text.user.x",
                component_type="kText",
                x_offset=18,
                y_offset=-12,
            ),
        ),
    )
    assert c.components[0].x_offset == 18
    assert c.components[0].y_offset == -12
    assert c.relative_attachments == ()


def test_tonality_system_def_holds_two_outbound_refs() -> None:
    t = TonalitySystemDef(
        name="cents",
        entity_id="tonalitysystem.user.x",
        temperament_definition_id="temperament-definition.user.t",
        accidental_system_id="accidental-system.user.a",
    )
    assert t.temperament_definition_id.startswith("temperament-definition.user.")
    assert t.accidental_system_id.startswith("accidental-system.user.")
