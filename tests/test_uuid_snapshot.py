"""UUID snapshot test — pins entityID hex strings for the three template entities.

This is the third layer of the determinism defense (Pitfall 2 — non-deterministic
UUIDs):
  1. Plan 01-01 verifies entity_id() produces the same hex within a single
     process and across consecutive calls.
  2. Plan 01-03 test_determinism.py verifies two CLI invocations produce the
     same bytes.
  3. THIS TEST verifies the actual hex values do not silently change between
     commits — catches accidental rotation of PROJECT_NAMESPACE, drift in the
     key strings used by build_template_three(), or changes to the
     entity_id() hashing algorithm.

If the snapshot ever needs updating, that is a deliberate change requiring
discussion: rotating PROJECT_NAMESPACE or the key conventions breaks
update-in-place re-imports for every existing user. See uuids.py header.
"""
from __future__ import annotations

import pathlib

from cents_generator.constants import (
    KIND_ACCIDENTAL_SYSTEM,
    KIND_TEMPERAMENT,
    KIND_TONALITY_SYSTEM,
)
from cents_generator.main import build_template_three
from cents_generator.uuids import entity_id


# Pinned by Plan 01-03 first-run capture. Rotating PROJECT_NAMESPACE or the
# Phase 1 key strings will cause every value in this snapshot to change —
# which is a re-import duplication bug, NOT a test bug. Treat any drift here
# as a regression and revert to the previously-shipped values.
SNAPSHOT_TEMPERAMENT = "temperament-definition.user.aeae963766a157fbb1e4c2b0c127e8a7"
SNAPSHOT_ACCIDENTAL_SYSTEM = "accidental-system.user.a0e56c76efd450ecbb44120e7909d5d7"
SNAPSHOT_TONALITY = "tonalitysystem.user.9648fe6490d45bc180ac2166455fb224"

SNAPSHOT_ACCIDENTAL_SHARP_31 = "accidental.user.df943e16be3151d3bb5e6df4c4ceb5e3"
SNAPSHOT_ACCIDENTAL_MINUS_14 = "accidental.user.95bede5da6f659fa8fabaec729bd20b0"
SNAPSHOT_ACCIDENTAL_NATURAL = "accidental.user.dc0afe1368685513856fddd1be5c4896"

SNAPSHOT_COMPOSITE_NATURAL = "comp.user.fcb0e88075bc55438ad08e2b7ee97c44"
SNAPSHOT_COMPOSITE_SHARP_31 = "comp.user.08b051781e1f595cab1b865bbbc5e91c"
SNAPSHOT_COMPOSITE_MINUS_14 = "comp.user.56ec559b75145e47be939c815c3c122a"

SNAPSHOT_GLYPH_NATURAL = "glyph.user.e8de539f177b5b4993136069f4ddadc5"
SNAPSHOT_GLYPH_SHARP = "glyph.user.70da2ea18dd55597b7da8f5ee79b671c"

SNAPSHOT_TEXT_MINUS_14 = "text.user.2691a244ed425014844d0de5e8cf4d3c"
SNAPSHOT_TEXT_MINUS_31 = "text.user.234604b68c7959488305f5c0259b9278"


def test_snapshot_singletons_match() -> None:
    """The three Psychography singletons keep their pinned hex values."""
    temperament, acc_system, tonality, _, _, _, _ = build_template_three()
    assert temperament.entity_id == SNAPSHOT_TEMPERAMENT
    assert acc_system.entity_id == SNAPSHOT_ACCIDENTAL_SYSTEM
    assert tonality.entity_id == SNAPSHOT_TONALITY


def test_snapshot_accidentals_match() -> None:
    """The three accidentalDefinition entityIDs keep their pinned values.

    Tuple order is: #-31, -14, Natural (matches the template's
    accidentalDefinitions section ordering)."""
    _, _, _, accidentals, _, _, _ = build_template_three()
    by_name = {a.name: a.entity_id for a in accidentals}
    assert by_name["#-31"] == SNAPSHOT_ACCIDENTAL_SHARP_31
    assert by_name["-14"] == SNAPSHOT_ACCIDENTAL_MINUS_14
    assert by_name["Natural"] == SNAPSHOT_ACCIDENTAL_NATURAL


def test_snapshot_composites_match() -> None:
    """The three CompositeDefinition entityIDs keep their pinned values.

    Composite names are non-unique in the template (#-31's and -14's
    composites both share '<name>New Composite</name>') so we map by
    composite_id from the accidentals."""
    _, _, _, accidentals, composites, _, _ = build_template_three()
    composite_by_id = {c.entity_id: c for c in composites}
    accidental_by_name = {a.name: a for a in accidentals}

    natural_composite = composite_by_id[accidental_by_name["Natural"].composite_id]
    sharp_31_composite = composite_by_id[accidental_by_name["#-31"].composite_id]
    minus_14_composite = composite_by_id[accidental_by_name["-14"].composite_id]

    assert natural_composite.entity_id == SNAPSHOT_COMPOSITE_NATURAL
    assert sharp_31_composite.entity_id == SNAPSHOT_COMPOSITE_SHARP_31
    assert minus_14_composite.entity_id == SNAPSHOT_COMPOSITE_MINUS_14


def test_snapshot_glyphs_match() -> None:
    """The two glyph entityIDs (accidentalNatural, accidentalSharp) match."""
    _, _, _, _, _, glyphs, _ = build_template_three()
    by_name = {g.name: g.entity_id for g in glyphs}
    assert by_name["accidentalNatural"] == SNAPSHOT_GLYPH_NATURAL
    assert by_name["accidentalSharp"] == SNAPSHOT_GLYPH_SHARP


def test_snapshot_texts_match() -> None:
    """The two text entityIDs (-14, -31) keep their pinned values."""
    _, _, _, _, _, _, texts = build_template_three()
    by_text = {t.text: t.entity_id for t in texts}
    assert by_text["-14"] == SNAPSHOT_TEXT_MINUS_14
    assert by_text["-31"] == SNAPSHOT_TEXT_MINUS_31


def test_snapshot_keys_produce_pinned_singletons_directly() -> None:
    """Belt-and-braces: re-derive the singletons from raw entity_id() calls.

    If build_template_three() drifts but entity_id() still produces the same
    hex for the same (kind, key) inputs, this test stays green and
    test_snapshot_singletons_match() flags the drift. If entity_id() itself
    drifts (PROJECT_NAMESPACE rotation, hashing algorithm change), this test
    fails alongside the others — pinpointing the lower-level break."""
    assert entity_id(KIND_TEMPERAMENT, "12-edo-template") == SNAPSHOT_TEMPERAMENT
    assert entity_id(KIND_ACCIDENTAL_SYSTEM, "psychography-template") == SNAPSHOT_ACCIDENTAL_SYSTEM
    assert entity_id(KIND_TONALITY_SYSTEM, "psychography-template") == SNAPSHOT_TONALITY


def test_snapshot_emitted_xml_contains_all_entity_ids(tmp_path: pathlib.Path) -> None:
    """End-to-end check: every snapshot entityID appears in the emitted file.

    Catches regressions where build_template_three() returns the right values
    but emit.write() drops or rewrites them (Pitfall 3 silent-drop variant)."""
    from cents_generator.main import run as cli_run
    out = tmp_path / "snap.doricolib"
    cli_run(out, mode="template")
    body = out.read_text("utf-8")

    expected = [
        SNAPSHOT_TEMPERAMENT,
        SNAPSHOT_ACCIDENTAL_SYSTEM,
        SNAPSHOT_TONALITY,
        SNAPSHOT_ACCIDENTAL_SHARP_31,
        SNAPSHOT_ACCIDENTAL_MINUS_14,
        SNAPSHOT_ACCIDENTAL_NATURAL,
        SNAPSHOT_COMPOSITE_NATURAL,
        SNAPSHOT_COMPOSITE_SHARP_31,
        SNAPSHOT_COMPOSITE_MINUS_14,
        SNAPSHOT_GLYPH_NATURAL,
        SNAPSHOT_GLYPH_SHARP,
        SNAPSHOT_TEXT_MINUS_14,
        SNAPSHOT_TEXT_MINUS_31,
    ]
    missing = [e for e in expected if e not in body]
    assert not missing, f"snapshot entityIDs missing from emitted XML: {missing}"
