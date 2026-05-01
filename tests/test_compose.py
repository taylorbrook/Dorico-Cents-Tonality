"""Per-class output shape tests for the three-class composite dispatcher."""
from __future__ import annotations

import pytest

from cents_generator.compose import (
    AccidentalBundle,
    build_class_a,
    build_class_b,
    build_class_c,
)


# ----------------------------------------------------------------------------
# Class A: glyph-only, no text, no attachment
# ----------------------------------------------------------------------------
def test_class_a_natural_template_shape() -> None:
    """Reproduces the template's Natural entity shape (modulo entityIDs)."""
    b = build_class_a(
        "natural",
        accidental_name="Natural",
        accidental_key="natural",
        composite_name="Natural",
        composite_key="natural",
        pitch_delta_from_natural="0/24",
        cut_out_ne=(0.192, 2.116),
        cut_out_sw=(0.476, 0.512),
    )
    assert b.glyph is not None
    assert b.text is None
    assert b.glyph.code_point == 0xE261
    assert b.glyph.parent_entity_id == "glyph.accidentalNatural"
    assert b.composite.name == "Natural"
    assert len(b.composite.components) == 1
    assert b.composite.components[0].component_type == "kGlyph"
    assert b.composite.components[0].x_offset == 0
    assert b.composite.components[0].y_offset == 0
    assert b.composite.components[0].z_order == 0
    assert b.composite.relative_attachments == ()
    assert b.accidental.pitch_delta_from_natural == "0/24"
    assert b.accidental.cut_out_ne == (0.192, 2.116)
    assert b.accidental.cut_out_sw == (0.476, 0.512)


def test_class_a_sharp_uses_correct_codepoint_and_no_factory_parent() -> None:
    b = build_class_a(
        "sharp",
        accidental_name="Sharp",
        accidental_key="sharp",
        composite_name="Sharp",
        composite_key="sharp",
        pitch_delta_from_natural="100/1200",
    )
    assert b.glyph.code_point == 0xE262
    assert b.glyph.parent_entity_id == ""


def test_class_a_flat_uses_correct_codepoint() -> None:
    b = build_class_a(
        "flat",
        accidental_name="Flat",
        accidental_key="flat",
        composite_name="Flat",
        composite_key="flat",
        pitch_delta_from_natural="-100/1200",
    )
    assert b.glyph.code_point == 0xE260


def test_class_a_entities_property_omits_none() -> None:
    b = build_class_a(
        "natural",
        accidental_name="N", accidental_key="natural",
        composite_name="N", composite_key="natural",
        pitch_delta_from_natural="0/1200",
    )
    # AccidentalDef + CompositeDef + GlyphDef = 3 entities; no TextDef.
    assert len(b.entities) == 3


# ----------------------------------------------------------------------------
# Class B: glyph + text via relativeAttachment kBaselineRight↔kBaselineLeft (-8, -12)
# ----------------------------------------------------------------------------
def test_class_b_template_shape() -> None:
    """Reproduces the template's #-31 entity shape (modulo entityIDs)."""
    b = build_class_b(
        "sharp",
        accidental_name="#-31",
        accidental_key="sharp-31",
        composite_name="New Composite",
        composite_key="sharp-31",
        label_text="-31",
        pitch_delta_from_natural="69/1200",
    )
    assert b.glyph is not None and b.text is not None
    assert b.glyph.code_point == 0xE262
    assert b.text.text == "-31"
    assert b.text.name == "-31.font.defaulttext"
    assert b.composite.name == "New Composite"
    assert len(b.composite.components) == 2

    # Glyph component is zOrder=1, text is zOrder=2 (per template).
    glyph_comp = b.composite.components[0]
    text_comp = b.composite.components[1]
    assert glyph_comp.component_type == "kGlyph" and glyph_comp.z_order == 1
    assert text_comp.component_type == "kText" and text_comp.z_order == 2

    # Exactly one relativeAttachment with the canonical offset and points.
    assert len(b.composite.relative_attachments) == 1
    att = b.composite.relative_attachments[0]
    assert att.x_offset == -8
    assert att.y_offset == -12
    assert att.pair1_attachment_point == "kBaselineRight"
    assert att.pair2_attachment_point == "kBaselineLeft"
    # pair instance IDs end with .0 suffix (matches componentInstance=0)
    assert att.pair1_component_instance_id == f"{b.glyph.entity_id}.0"
    assert att.pair2_component_instance_id == f"{b.text.entity_id}.0"

    assert b.accidental.pitch_delta_from_natural == "69/1200"


def test_class_b_rejects_natural_base() -> None:
    with pytest.raises(ValueError):
        build_class_b(
            "natural",  # type: ignore[arg-type]
            accidental_name="x", accidental_key="x",
            composite_name="x", composite_key="x",
            label_text="+1", pitch_delta_from_natural="1/1200",
        )


def test_class_b_flat_uses_correct_codepoint() -> None:
    b = build_class_b(
        "flat",
        accidental_name="b-7", accidental_key="flat-7",
        composite_name="New Composite", composite_key="flat-7",
        label_text="-7", pitch_delta_from_natural="-107/1200",
    )
    assert b.glyph.code_point == 0xE260


def test_class_b_entities_property_includes_all_four() -> None:
    b = build_class_b(
        "sharp",
        accidental_name="x", accidental_key="x",
        composite_name="x", composite_key="x",
        label_text="-31", pitch_delta_from_natural="69/1200",
    )
    # AccidentalDef + CompositeDef + GlyphDef + TextDef = 4 entities.
    assert len(b.entities) == 4


# ----------------------------------------------------------------------------
# Class C: text-only, natural-base, no glyph, no attachment, text at (18, -12)
# ----------------------------------------------------------------------------
def test_class_c_template_shape() -> None:
    """Reproduces the template's -14 entity shape (modulo entityIDs)."""
    b = build_class_c(
        accidental_name="-14",
        accidental_key="natural-14",
        composite_name="New Composite",
        composite_key="natural-14",
        label_text="-14",
        pitch_delta_from_natural="-14/1200",
    )
    assert b.glyph is None
    assert b.text is not None
    assert b.text.text == "-14"
    assert b.text.name == "-14.font.defaulttext"
    assert b.composite.name == "New Composite"
    assert len(b.composite.components) == 1

    text_comp = b.composite.components[0]
    assert text_comp.component_type == "kText"
    assert text_comp.x_offset == 18
    assert text_comp.y_offset == -12
    assert text_comp.z_order == 0

    assert b.composite.relative_attachments == ()
    assert b.accidental.pitch_delta_from_natural == "-14/1200"


def test_class_c_entities_property_omits_glyph() -> None:
    b = build_class_c(
        accidental_name="x", accidental_key="natural-1",
        composite_name="x", composite_key="natural-1",
        label_text="-1", pitch_delta_from_natural="-1/1200",
    )
    # AccidentalDef + CompositeDef + TextDef = 3 entities; no GlyphDef.
    assert len(b.entities) == 3


# ----------------------------------------------------------------------------
# Determinism cross-check
# ----------------------------------------------------------------------------
def test_same_inputs_produce_identical_entity_ids_across_classes() -> None:
    """Class A natural + Class C natural-cent compose against the same glyph
    key — should NOT collide because Class C has no glyph. But the text
    entity from Class C with label '+14' should match a future Class B's
    text with the same label."""
    c1 = build_class_c(
        accidental_name="x", accidental_key="natural+14",
        composite_name="x", composite_key="natural+14",
        label_text="+14", pitch_delta_from_natural="14/1200",
    )
    c2 = build_class_c(
        accidental_name="y", accidental_key="natural+14",
        composite_name="y", composite_key="natural+14",
        label_text="+14", pitch_delta_from_natural="14/1200",
    )
    # Same accidental_key + composite_key → same entityIDs.
    assert c1.accidental.entity_id == c2.accidental.entity_id
    assert c1.composite.entity_id == c2.composite.entity_id
    assert c1.text.entity_id == c2.text.entity_id

    # Different accidental keys → different entityIDs.
    c3 = build_class_c(
        accidental_name="z", accidental_key="natural+15",
        composite_name="z", composite_key="natural+15",
        label_text="+15", pitch_delta_from_natural="15/1200",
    )
    assert c1.accidental.entity_id != c3.accidental.entity_id
    assert c1.text.entity_id != c3.text.entity_id
