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
    """Reproduces the template's Natural entity shape (modulo entityIDs).

    Phase 2: explicit mode="template" required so the Phase 1 quirk
    (Natural inherits 'glyph.accidentalNatural') is reachable. Without
    mode="template", build_class_a defaults to mode="cents" (D-01) and
    Natural's parent is empty.
    """
    b = build_class_a(
        "natural",
        accidental_name="Natural",
        accidental_key="natural",
        composite_name="Natural",
        composite_key="natural",
        pitch_delta_from_natural="0/24",
        cut_out_ne=(0.192, 2.116),
        cut_out_sw=(0.476, 0.512),
        mode="template",
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


# ----------------------------------------------------------------------------
# Phase 2: mode-aware glyph spec — D-01 cents-mode all-empty parents,
# template-mode preserves the Natural-inherits-'glyph.accidentalNatural' quirk.
# ----------------------------------------------------------------------------
def test_glyph_for_natural_template_mode_inherits_factory_parent() -> None:
    """Template mode preserves Phase 1's Natural-parent quirk (D-03)."""
    from cents_generator.compose import _glyph_for

    g = _glyph_for("natural", mode="template")
    assert g.parent_entity_id == "glyph.accidentalNatural"
    assert g.code_point == 0xE261


def test_glyph_for_natural_cents_mode_emits_empty_parent() -> None:
    """Cents mode emits <parentEntityID/> empty for Natural (D-01)."""
    from cents_generator.compose import _glyph_for

    g = _glyph_for("natural", mode="cents")
    assert g.parent_entity_id == ""
    assert g.code_point == 0xE261


def test_glyph_for_sharp_empty_parent_in_both_modes() -> None:
    """Sharp's parent is empty in both modes (Phase 1 already had this empty)."""
    from cents_generator.compose import _glyph_for

    assert _glyph_for("sharp", mode="template").parent_entity_id == ""
    assert _glyph_for("sharp", mode="cents").parent_entity_id == ""


def test_glyph_for_flat_empty_parent_in_both_modes() -> None:
    """Flat's parent is empty in both modes (Phase 1 already had this empty)."""
    from cents_generator.compose import _glyph_for

    assert _glyph_for("flat", mode="template").parent_entity_id == ""
    assert _glyph_for("flat", mode="cents").parent_entity_id == ""


def test_glyph_for_natural_entity_id_is_mode_independent() -> None:
    """Same SMuFL name -> same uuid5 hash regardless of mode; only parent_entity_id differs."""
    from cents_generator.compose import _glyph_for

    gt = _glyph_for("natural", mode="template")
    gc = _glyph_for("natural", mode="cents")
    assert gt.entity_id == gc.entity_id
    assert gt.parent_entity_id != gc.parent_entity_id


def test_build_class_a_mode_cents_default_natural_empty_parent() -> None:
    """build_class_a default mode is 'cents' -> Natural parent is empty."""
    b = build_class_a(
        "natural",
        accidental_name="Natural",
        accidental_key="natural",
        composite_name="Natural",
        composite_key="natural",
        pitch_delta_from_natural="0/1200",
    )
    assert b.glyph is not None
    assert b.glyph.parent_entity_id == ""


def test_build_class_b_mode_propagates_to_glyph() -> None:
    """build_class_b accepts mode kwarg and propagates to _glyph_for.

    Sharp's parent is already empty in template mode so the assertion is
    on Sharp's code-point (mode acceptance is the contract being tested)."""
    b_template = build_class_b(
        "sharp",
        accidental_name="x", accidental_key="x-template",
        composite_name="x", composite_key="x-template",
        label_text="-31", pitch_delta_from_natural="69/1200",
        mode="template",
    )
    b_cents = build_class_b(
        "sharp",
        accidental_name="x", accidental_key="x-cents",
        composite_name="x", composite_key="x-cents",
        label_text="+14", pitch_delta_from_natural="114/1200",
        mode="cents",
    )
    # Both modes produce empty parent for Sharp; mode is accepted as a kwarg.
    assert b_template.glyph.parent_entity_id == ""
    assert b_cents.glyph.parent_entity_id == ""


# ----------------------------------------------------------------------------
# Phase 2: cents-mode constants pinned in constants.py — D-05 lock-forever keys
# ----------------------------------------------------------------------------
def test_cents_mode_locked_keys_pinned() -> None:
    """KEY_*_CENTS constants are pinned per D-05 (Pitfall 6 lock-forever)."""
    from cents_generator.constants import (
        KEY_ACC_SYSTEM_CENTS,
        KEY_TEMPERAMENT_12EDO_CENTS,
        KEY_TONALITY_CENTS,
    )

    assert KEY_TEMPERAMENT_12EDO_CENTS == "12-edo"
    assert KEY_ACC_SYSTEM_CENTS == "cents"
    assert KEY_TONALITY_CENTS == "cents"


def test_cents_range_nonzero_spans_minus99_to_plus99_excluding_zero() -> None:
    """CENTS_RANGE_NONZERO is the 198-entry tuple driving the cents-mode sweep."""
    from cents_generator.constants import CENTS_RANGE_NONZERO

    assert len(CENTS_RANGE_NONZERO) == 198
    assert 0 not in CENTS_RANGE_NONZERO
    assert -99 in CENTS_RANGE_NONZERO
    assert 99 in CENTS_RANGE_NONZERO
    # Ascending order: starts at -99, ends at +99.
    assert CENTS_RANGE_NONZERO[0] == -99
    assert CENTS_RANGE_NONZERO[-1] == 99
    # No zero gap in the middle: -1 immediately followed by +1.
    minus_one_idx = CENTS_RANGE_NONZERO.index(-1)
    assert CENTS_RANGE_NONZERO[minus_one_idx + 1] == 1


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
