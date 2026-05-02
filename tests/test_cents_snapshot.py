"""Snapshot tests for cents-mode entityIDs and byte-faithful AccidentalDefinition
+ CompositeDefinition snippets.

Three layers of cents-mode determinism defense (D-07.3):

  1. UUID pins: 20 sampled entityIDs are pinned by hex; any drift signals
     either PROJECT_NAMESPACE rotation (BUG) or D-05 key drift (BUG).
  2. End-to-end appearance check: every pinned UUID must appear in the
     emitted body (catches Pitfall 3 silent-drop variant at the cents scale).
  3. Byte-faithful snippet pins: 4 AccidentalDefinition blocks plus their
     corresponding 4 CompositeDefinition blocks are pinned as multiline
     strings (with entityIDs normalized to '<HEX>') — covering the off-by-100
     trap diagnostic cases (Sharp +14, Sharp -50, Flat -7, Natural +50)
     plus a Class A zero-dev case (Sharp).

If a snapshot ever needs updating, that is a deliberate change requiring
discussion: rotating PROJECT_NAMESPACE or the D-05 cents-mode keys
creates duplicate entityIDs on user re-import. Treat any drift here
as a regression and revert to the previously-shipped values.
"""
from __future__ import annotations

import pathlib
import re

from cents_generator.constants import (
    KIND_ACCIDENTAL,
    KIND_ACCIDENTAL_SYSTEM,
    KIND_GLYPH,
    KIND_TEMPERAMENT,
    KIND_TEXT,
    KIND_TONALITY_SYSTEM,
)
from cents_generator.main import run
from cents_generator.uuids import entity_id

# ============================================================================
# SNAPSHOT_*: pinned entityIDs. These are FIRST-RUN CAPTURES from
# uuid5(PROJECT_NAMESPACE, f"{kind}:{key}").hex with the keys locked by D-05.
# DO NOT update these to make a test pass. If they fail, restore the
# previously-shipped values — drift signals a regression bug.
# ============================================================================

# Singletons (cents-mode keys: D-05 + Plan 02-02)
SNAPSHOT_TEMPERAMENT_CENTS       = "temperament-definition.user.2694060037a05ad4ba25ed0bbb4f48d2"
SNAPSHOT_ACCIDENTAL_SYSTEM_CENTS = "accidental-system.user.fd8362e5ea0158439a9229239bc4a872"
SNAPSHOT_TONALITY_CENTS          = "tonalitysystem.user.72901957c7f8528ba84773c522004339"

# Accidentals (8 diagnostic cases — D-07.3)
SNAPSHOT_ACCIDENTAL_SHARP_ZERO        = "accidental.user.4e6f65dbec1b5c79ac25b4145c7c3127"  # key="sharp"
SNAPSHOT_ACCIDENTAL_FLAT_ZERO         = "accidental.user.8fda3150007a5d219130d6f007abf8bb"  # key="flat"
SNAPSHOT_ACCIDENTAL_NATURAL_ZERO      = "accidental.user.d883791e97b753e6a3c77d46827cee13"  # key="natural"
SNAPSHOT_ACCIDENTAL_SHARP_PLUS_14     = "accidental.user.f95f5061066e544ead43514e6c06621f"  # key="sharp+14" — off-by-100 trap diagnostic
SNAPSHOT_ACCIDENTAL_SHARP_MINUS_50    = "accidental.user.f47fe28e59de50c0aa07daa8a6051e3e"  # key="sharp-50" — off-by-100 trap diagnostic
SNAPSHOT_ACCIDENTAL_FLAT_MINUS_7      = "accidental.user.f36571f7d7365b27983a68aeea0ea6cb"  # key="flat-7"
SNAPSHOT_ACCIDENTAL_NATURAL_MINUS_7   = "accidental.user.1355546289c850c383ba125dca96757d"  # key="natural-7"
SNAPSHOT_ACCIDENTAL_NATURAL_PLUS_50   = "accidental.user.25592617a5bd5dc38c78473538405381"  # key="natural+50" — enharmonic of sharp-50
SNAPSHOT_ACCIDENTAL_SHARP_PLUS_99     = "accidental.user.f49e07369ee75b74a0cb12b3adcb8bcc"  # key="sharp+99" — boundary
SNAPSHOT_ACCIDENTAL_FLAT_MINUS_99     = "accidental.user.46d3ef532e0c5eac8b27088175feaa7d"  # key="flat-99" — boundary

# Glyphs (entityID is mode-independent — same SMuFL name -> same uuid5 hash;
# the Phase 1 SNAPSHOT_GLYPH_NATURAL and SNAPSHOT_GLYPH_SHARP from
# tests/test_uuid_snapshot.py MUST equal these.)
SNAPSHOT_GLYPH_NATURAL_CENTS = "glyph.user.e8de539f177b5b4993136069f4ddadc5"  # Phase 1 pin
SNAPSHOT_GLYPH_SHARP_CENTS   = "glyph.user.70da2ea18dd55597b7da8f5ee79b671c"  # Phase 1 pin
SNAPSHOT_GLYPH_FLAT_CENTS    = "glyph.user.a63d6a3d7ac35905bc3418ade80029a8"  # new in Phase 2

# Texts (sample diagnostic labels)
SNAPSHOT_TEXT_PLUS_14  = "text.user.a3c1b98958835a2b9363d2320ad88981"  # key="+14"
SNAPSHOT_TEXT_MINUS_50 = "text.user.9ac4419947575f529300d2759999a19a"  # key="-50"
SNAPSHOT_TEXT_MINUS_7  = "text.user.841503ce49c351b1aa8345fefe48feea"  # key="-7"
SNAPSHOT_TEXT_PLUS_50  = "text.user.2623716b91f652dc9da77628697ef321"  # key="+50"
SNAPSHOT_TEXT_PLUS_99  = "text.user.c670997c707d50b786e01cbf5cf1f29a"  # key="+99"
SNAPSHOT_TEXT_MINUS_99 = "text.user.0a6af889dd7653afb033bd3c71d0c1c5"  # key="-99"


# ============================================================================
# Byte-faithful snippet snapshots — 5 AccidentalDefinition blocks + 5
# CompositeDefinition blocks for the off-by-100 trap diagnostic cases plus
# a Class A zero-dev case. EntityIDs are normalized to '<HEX>' for
# robustness against UUID values; structural fields (names, deltas, offsets,
# cut-outs, components) are pinned literally.
# ============================================================================

ENTITY_ID_RE = re.compile(r"([a-z-]+)\.user\.[0-9a-f]{32}")


def _normalize_entity_ids(s: str) -> str:
    """Mask each '<kind>.user.<32hex>' to '<kind>.user.<HEX>'.

    Simpler than test_template_roundtrip.py's per-kind sequential index —
    for snippet diffing within a single AccidentalDefinition / CompositeDefinition
    block we just need 'this is some 32-hex UUID' equivalence, not 'first
    occurrence here matches first occurrence there'.
    """
    return ENTITY_ID_RE.sub(r"\1.user.<HEX>", s)


# ---- AccidentalDefinition snapshots ----------------------------------------
# Pinned snippet for Sharp +14 AccidentalDefinition (off-by-100 trap diagnostic).
# Pinned delta: 114/1200 (NOT 14/1200 — that would mean the helper was bypassed).
SNAPSHOT_SHARP_PLUS_14_ACCIDENTAL_BLOCK = (
    "\t\t\t<AccidentalDefinition>\n"
    "\t\t\t\t<name>Sharp +14</name>\n"
    "\t\t\t\t<entityID>accidental.user.<HEX></entityID>\n"
    "\t\t\t\t<parentEntityID/>\n"
    "\t\t\t\t<inheritanceMask>0</inheritanceMask>\n"
    "\t\t\t\t<compositeID>comp.user.<HEX></compositeID>\n"
    "\t\t\t\t<pitchDeltaFromNatural>114/1200</pitchDeltaFromNatural>\n"
    "\t\t\t\t<cutOutNW>(0, 0)</cutOutNW>\n"
    "\t\t\t\t<cutOutNE>(0, 0)</cutOutNE>\n"
    "\t\t\t\t<cutOutSE>(0, 0)</cutOutSE>\n"
    "\t\t\t\t<cutOutSW>(0, 0)</cutOutSW>\n"
    "\t\t\t</AccidentalDefinition>"
)

# Pinned snippet for Sharp -50 (off-by-100 trap diagnostic):
# delta 50/1200 from 100 + (-50). If the helper were bypassed, would be -50/1200.
SNAPSHOT_SHARP_MINUS_50_ACCIDENTAL_BLOCK = (
    "\t\t\t<AccidentalDefinition>\n"
    "\t\t\t\t<name>Sharp -50</name>\n"
    "\t\t\t\t<entityID>accidental.user.<HEX></entityID>\n"
    "\t\t\t\t<parentEntityID/>\n"
    "\t\t\t\t<inheritanceMask>0</inheritanceMask>\n"
    "\t\t\t\t<compositeID>comp.user.<HEX></compositeID>\n"
    "\t\t\t\t<pitchDeltaFromNatural>50/1200</pitchDeltaFromNatural>\n"
    "\t\t\t\t<cutOutNW>(0, 0)</cutOutNW>\n"
    "\t\t\t\t<cutOutNE>(0, 0)</cutOutNE>\n"
    "\t\t\t\t<cutOutSE>(0, 0)</cutOutSE>\n"
    "\t\t\t\t<cutOutSW>(0, 0)</cutOutSW>\n"
    "\t\t\t</AccidentalDefinition>"
)

# Pinned snippet for Flat -7 (flat-side off-by-100 mirror case):
# delta -107/1200 from -100 + (-7).
SNAPSHOT_FLAT_MINUS_7_ACCIDENTAL_BLOCK = (
    "\t\t\t<AccidentalDefinition>\n"
    "\t\t\t\t<name>Flat -7</name>\n"
    "\t\t\t\t<entityID>accidental.user.<HEX></entityID>\n"
    "\t\t\t\t<parentEntityID/>\n"
    "\t\t\t\t<inheritanceMask>0</inheritanceMask>\n"
    "\t\t\t\t<compositeID>comp.user.<HEX></compositeID>\n"
    "\t\t\t\t<pitchDeltaFromNatural>-107/1200</pitchDeltaFromNatural>\n"
    "\t\t\t\t<cutOutNW>(0, 0)</cutOutNW>\n"
    "\t\t\t\t<cutOutNE>(0, 0)</cutOutNE>\n"
    "\t\t\t\t<cutOutSE>(0, 0)</cutOutSE>\n"
    "\t\t\t\t<cutOutSW>(0, 0)</cutOutSW>\n"
    "\t\t\t</AccidentalDefinition>"
)

# Pinned snippet for Natural +50 (Class C — enharmonic of Sharp -50 at delta=50):
# delta 50/1200 from 0 + 50.
SNAPSHOT_NATURAL_PLUS_50_ACCIDENTAL_BLOCK = (
    "\t\t\t<AccidentalDefinition>\n"
    "\t\t\t\t<name>Natural +50</name>\n"
    "\t\t\t\t<entityID>accidental.user.<HEX></entityID>\n"
    "\t\t\t\t<parentEntityID/>\n"
    "\t\t\t\t<inheritanceMask>0</inheritanceMask>\n"
    "\t\t\t\t<compositeID>comp.user.<HEX></compositeID>\n"
    "\t\t\t\t<pitchDeltaFromNatural>50/1200</pitchDeltaFromNatural>\n"
    "\t\t\t\t<cutOutNW>(0, 0)</cutOutNW>\n"
    "\t\t\t\t<cutOutNE>(0, 0)</cutOutNE>\n"
    "\t\t\t\t<cutOutSE>(0, 0)</cutOutSE>\n"
    "\t\t\t\t<cutOutSW>(0, 0)</cutOutSW>\n"
    "\t\t\t</AccidentalDefinition>"
)

# Pinned snippet for Sharp (zero-dev, Class A code path):
# delta 100/1200 from 100 + 0.
SNAPSHOT_SHARP_ZERO_ACCIDENTAL_BLOCK = (
    "\t\t\t<AccidentalDefinition>\n"
    "\t\t\t\t<name>Sharp</name>\n"
    "\t\t\t\t<entityID>accidental.user.<HEX></entityID>\n"
    "\t\t\t\t<parentEntityID/>\n"
    "\t\t\t\t<inheritanceMask>0</inheritanceMask>\n"
    "\t\t\t\t<compositeID>comp.user.<HEX></compositeID>\n"
    "\t\t\t\t<pitchDeltaFromNatural>100/1200</pitchDeltaFromNatural>\n"
    "\t\t\t\t<cutOutNW>(0, 0)</cutOutNW>\n"
    "\t\t\t\t<cutOutNE>(0, 0)</cutOutNE>\n"
    "\t\t\t\t<cutOutSE>(0, 0)</cutOutSE>\n"
    "\t\t\t\t<cutOutSW>(0, 0)</cutOutSW>\n"
    "\t\t\t</AccidentalDefinition>"
)


# ---- CompositeDefinition snapshots -----------------------------------------
# Class B (Sharp +14): 2 components (kGlyph zOrder=1 + kText zOrder=2),
# 1 relativeAttachment with offset (-8, -12).
SNAPSHOT_SHARP_PLUS_14_COMPOSITE_BLOCK = (
    "\t\t\t<CompositeDefinition>\n"
    "\t\t\t\t<name>Sharp +14</name>\n"
    "\t\t\t\t<entityID>comp.user.<HEX></entityID>\n"
    "\t\t\t\t<parentEntityID/>\n"
    "\t\t\t\t<inheritanceMask>0</inheritanceMask>\n"
    "\t\t\t\t<category>kAccidentals</category>\n"
    "\t\t\t\t<components array=\"true\">\n"
    "\t\t\t\t\t<component>\n"
    "\t\t\t\t\t\t<componentId>glyph.user.<HEX></componentId>\n"
    "\t\t\t\t\t\t<componentType>kGlyph</componentType>\n"
    "\t\t\t\t\t\t<xOffset>0</xOffset>\n"
    "\t\t\t\t\t\t<yOffset>0</yOffset>\n"
    "\t\t\t\t\t\t<xScale>100.000000</xScale>\n"
    "\t\t\t\t\t\t<yScale>100.000000</yScale>\n"
    "\t\t\t\t\t\t<zOrder>1</zOrder>\n"
    "\t\t\t\t\t\t<maxOpticalScale>100</maxOpticalScale>\n"
    "\t\t\t\t\t\t<componentInstance>0</componentInstance>\n"
    "\t\t\t\t\t\t<colour>kDefault</colour>\n"
    "\t\t\t\t\t</component>\n"
    "\t\t\t\t\t<component>\n"
    "\t\t\t\t\t\t<componentId>text.user.<HEX></componentId>\n"
    "\t\t\t\t\t\t<componentType>kText</componentType>\n"
    "\t\t\t\t\t\t<xOffset>0</xOffset>\n"
    "\t\t\t\t\t\t<yOffset>0</yOffset>\n"
    "\t\t\t\t\t\t<xScale>100.000000</xScale>\n"
    "\t\t\t\t\t\t<yScale>100.000000</yScale>\n"
    "\t\t\t\t\t\t<zOrder>2</zOrder>\n"
    "\t\t\t\t\t\t<maxOpticalScale>100</maxOpticalScale>\n"
    "\t\t\t\t\t\t<componentInstance>0</componentInstance>\n"
    "\t\t\t\t\t\t<colour>kDefault</colour>\n"
    "\t\t\t\t\t</component>\n"
    "\t\t\t\t</components>\n"
    "\t\t\t\t<relativeAttachments array=\"true\">\n"
    "\t\t\t\t\t<relativeAttachment>\n"
    "\t\t\t\t\t\t<xOffset>-8</xOffset>\n"
    "\t\t\t\t\t\t<yOffset>-12</yOffset>\n"
    "\t\t\t\t\t\t<componentRelativePair1>\n"
    "\t\t\t\t\t\t\t<componentInstanceId>glyph.user.<HEX>.0</componentInstanceId>\n"
    "\t\t\t\t\t\t\t<componentAttachmentPoint>kBaselineRight</componentAttachmentPoint>\n"
    "\t\t\t\t\t\t</componentRelativePair1>\n"
    "\t\t\t\t\t\t<componentRelativePair2>\n"
    "\t\t\t\t\t\t\t<componentInstanceId>text.user.<HEX>.0</componentInstanceId>\n"
    "\t\t\t\t\t\t\t<componentAttachmentPoint>kBaselineLeft</componentAttachmentPoint>\n"
    "\t\t\t\t\t\t</componentRelativePair2>\n"
    "\t\t\t\t\t</relativeAttachment>\n"
    "\t\t\t\t</relativeAttachments>\n"
    "\t\t\t\t<scalingRules array=\"true\"/>\n"
    "\t\t\t</CompositeDefinition>"
)

# Class B (Sharp -50): same shape as Sharp +14 (different name, different IDs).
SNAPSHOT_SHARP_MINUS_50_COMPOSITE_BLOCK = SNAPSHOT_SHARP_PLUS_14_COMPOSITE_BLOCK.replace(
    "<name>Sharp +14</name>", "<name>Sharp -50</name>"
)

# Class B (Flat -7): same shape as Sharp +14 (different name, different IDs).
SNAPSHOT_FLAT_MINUS_7_COMPOSITE_BLOCK = SNAPSHOT_SHARP_PLUS_14_COMPOSITE_BLOCK.replace(
    "<name>Sharp +14</name>", "<name>Flat -7</name>"
)

# Class C (Natural +50): 1 component (kText, xOffset=18, yOffset=-12, zOrder=0),
# 0 relativeAttachments.
SNAPSHOT_NATURAL_PLUS_50_COMPOSITE_BLOCK = (
    "\t\t\t<CompositeDefinition>\n"
    "\t\t\t\t<name>Natural +50</name>\n"
    "\t\t\t\t<entityID>comp.user.<HEX></entityID>\n"
    "\t\t\t\t<parentEntityID/>\n"
    "\t\t\t\t<inheritanceMask>0</inheritanceMask>\n"
    "\t\t\t\t<category>kAccidentals</category>\n"
    "\t\t\t\t<components array=\"true\">\n"
    "\t\t\t\t\t<component>\n"
    "\t\t\t\t\t\t<componentId>text.user.<HEX></componentId>\n"
    "\t\t\t\t\t\t<componentType>kText</componentType>\n"
    "\t\t\t\t\t\t<xOffset>18</xOffset>\n"
    "\t\t\t\t\t\t<yOffset>-12</yOffset>\n"
    "\t\t\t\t\t\t<xScale>100.000000</xScale>\n"
    "\t\t\t\t\t\t<yScale>100.000000</yScale>\n"
    "\t\t\t\t\t\t<zOrder>0</zOrder>\n"
    "\t\t\t\t\t\t<maxOpticalScale>100</maxOpticalScale>\n"
    "\t\t\t\t\t\t<componentInstance>0</componentInstance>\n"
    "\t\t\t\t\t\t<colour>kDefault</colour>\n"
    "\t\t\t\t\t</component>\n"
    "\t\t\t\t</components>\n"
    "\t\t\t\t<relativeAttachments array=\"true\"/>\n"
    "\t\t\t\t<scalingRules array=\"true\"/>\n"
    "\t\t\t</CompositeDefinition>"
)

# Class A (Sharp zero-dev): 1 component (kGlyph, xOffset=0, yOffset=0, zOrder=0),
# 0 relativeAttachments.
SNAPSHOT_SHARP_ZERO_COMPOSITE_BLOCK = (
    "\t\t\t<CompositeDefinition>\n"
    "\t\t\t\t<name>Sharp</name>\n"
    "\t\t\t\t<entityID>comp.user.<HEX></entityID>\n"
    "\t\t\t\t<parentEntityID/>\n"
    "\t\t\t\t<inheritanceMask>0</inheritanceMask>\n"
    "\t\t\t\t<category>kAccidentals</category>\n"
    "\t\t\t\t<components array=\"true\">\n"
    "\t\t\t\t\t<component>\n"
    "\t\t\t\t\t\t<componentId>glyph.user.<HEX></componentId>\n"
    "\t\t\t\t\t\t<componentType>kGlyph</componentType>\n"
    "\t\t\t\t\t\t<xOffset>0</xOffset>\n"
    "\t\t\t\t\t\t<yOffset>0</yOffset>\n"
    "\t\t\t\t\t\t<xScale>100.000000</xScale>\n"
    "\t\t\t\t\t\t<yScale>100.000000</yScale>\n"
    "\t\t\t\t\t\t<zOrder>0</zOrder>\n"
    "\t\t\t\t\t\t<maxOpticalScale>100</maxOpticalScale>\n"
    "\t\t\t\t\t\t<componentInstance>0</componentInstance>\n"
    "\t\t\t\t\t\t<colour>kDefault</colour>\n"
    "\t\t\t\t\t</component>\n"
    "\t\t\t\t</components>\n"
    "\t\t\t\t<relativeAttachments array=\"true\"/>\n"
    "\t\t\t\t<scalingRules array=\"true\"/>\n"
    "\t\t\t</CompositeDefinition>"
)


# ============================================================================
# Tests
# ============================================================================

def test_snapshot_singletons_match() -> None:
    """The three cents-mode singletons keep their pinned hex values."""
    assert entity_id(KIND_TEMPERAMENT, "12-edo") == SNAPSHOT_TEMPERAMENT_CENTS
    assert entity_id(KIND_ACCIDENTAL_SYSTEM, "cents") == SNAPSHOT_ACCIDENTAL_SYSTEM_CENTS
    assert entity_id(KIND_TONALITY_SYSTEM, "cents") == SNAPSHOT_TONALITY_CENTS


def test_snapshot_sampled_accidentals_match() -> None:
    """Pinned hex values for the 8 diagnostic accidentals + 3 zero-dev."""
    assert entity_id(KIND_ACCIDENTAL, "sharp") == SNAPSHOT_ACCIDENTAL_SHARP_ZERO
    assert entity_id(KIND_ACCIDENTAL, "flat") == SNAPSHOT_ACCIDENTAL_FLAT_ZERO
    assert entity_id(KIND_ACCIDENTAL, "natural") == SNAPSHOT_ACCIDENTAL_NATURAL_ZERO
    assert entity_id(KIND_ACCIDENTAL, "sharp+14") == SNAPSHOT_ACCIDENTAL_SHARP_PLUS_14
    assert entity_id(KIND_ACCIDENTAL, "sharp-50") == SNAPSHOT_ACCIDENTAL_SHARP_MINUS_50
    assert entity_id(KIND_ACCIDENTAL, "flat-7") == SNAPSHOT_ACCIDENTAL_FLAT_MINUS_7
    assert entity_id(KIND_ACCIDENTAL, "natural-7") == SNAPSHOT_ACCIDENTAL_NATURAL_MINUS_7
    assert entity_id(KIND_ACCIDENTAL, "natural+50") == SNAPSHOT_ACCIDENTAL_NATURAL_PLUS_50
    assert entity_id(KIND_ACCIDENTAL, "sharp+99") == SNAPSHOT_ACCIDENTAL_SHARP_PLUS_99
    assert entity_id(KIND_ACCIDENTAL, "flat-99") == SNAPSHOT_ACCIDENTAL_FLAT_MINUS_99


def test_snapshot_glyphs_match_phase_1() -> None:
    """Cross-mode invariant: glyph entityID is mode-independent. Phase 1
    pinned natural and sharp hex values; cents mode must produce the SAME
    hex (same SMuFL name -> same uuid5 hash)."""
    # Re-derive directly to verify mode-independence at the hash layer.
    assert entity_id(KIND_GLYPH, "accidentalNatural") == SNAPSHOT_GLYPH_NATURAL_CENTS
    assert entity_id(KIND_GLYPH, "accidentalSharp") == SNAPSHOT_GLYPH_SHARP_CENTS
    assert entity_id(KIND_GLYPH, "accidentalFlat") == SNAPSHOT_GLYPH_FLAT_CENTS

    # Cross-check Phase 1's pins MUST equal these (the PROJECT_NAMESPACE and
    # SMuFL-name keys are stable across modes — Plan 02-02 explicit claim).
    PHASE_1_GLYPH_NATURAL = "glyph.user.e8de539f177b5b4993136069f4ddadc5"
    PHASE_1_GLYPH_SHARP = "glyph.user.70da2ea18dd55597b7da8f5ee79b671c"
    assert SNAPSHOT_GLYPH_NATURAL_CENTS == PHASE_1_GLYPH_NATURAL, \
        "cross-mode invariant broken: glyph entityID is supposed to be mode-independent"
    assert SNAPSHOT_GLYPH_SHARP_CENTS == PHASE_1_GLYPH_SHARP, \
        "cross-mode invariant broken: glyph entityID is supposed to be mode-independent"


def test_snapshot_sampled_texts_match() -> None:
    """Pinned hex values for 6 sample text labels."""
    assert entity_id(KIND_TEXT, "+14") == SNAPSHOT_TEXT_PLUS_14
    assert entity_id(KIND_TEXT, "-50") == SNAPSHOT_TEXT_MINUS_50
    assert entity_id(KIND_TEXT, "-7") == SNAPSHOT_TEXT_MINUS_7
    assert entity_id(KIND_TEXT, "+50") == SNAPSHOT_TEXT_PLUS_50
    assert entity_id(KIND_TEXT, "+99") == SNAPSHOT_TEXT_PLUS_99
    assert entity_id(KIND_TEXT, "-99") == SNAPSHOT_TEXT_MINUS_99


def test_snapshot_emitted_xml_contains_all_entity_ids(tmp_path: pathlib.Path) -> None:
    """End-to-end check: every snapshot entityID appears in the emitted file.

    Catches regressions where the orchestrator returns the right values but
    emit.write() drops or rewrites them (Pitfall 3 silent-drop variant)."""
    out = tmp_path / "snap.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    expected = [
        SNAPSHOT_TEMPERAMENT_CENTS,
        SNAPSHOT_ACCIDENTAL_SYSTEM_CENTS,
        SNAPSHOT_TONALITY_CENTS,
        SNAPSHOT_ACCIDENTAL_SHARP_ZERO,
        SNAPSHOT_ACCIDENTAL_FLAT_ZERO,
        SNAPSHOT_ACCIDENTAL_NATURAL_ZERO,
        SNAPSHOT_ACCIDENTAL_SHARP_PLUS_14,
        SNAPSHOT_ACCIDENTAL_SHARP_MINUS_50,
        SNAPSHOT_ACCIDENTAL_FLAT_MINUS_7,
        SNAPSHOT_ACCIDENTAL_NATURAL_MINUS_7,
        SNAPSHOT_ACCIDENTAL_NATURAL_PLUS_50,
        SNAPSHOT_ACCIDENTAL_SHARP_PLUS_99,
        SNAPSHOT_ACCIDENTAL_FLAT_MINUS_99,
        SNAPSHOT_GLYPH_NATURAL_CENTS,
        SNAPSHOT_GLYPH_SHARP_CENTS,
        SNAPSHOT_GLYPH_FLAT_CENTS,
        SNAPSHOT_TEXT_PLUS_14,
        SNAPSHOT_TEXT_MINUS_50,
        SNAPSHOT_TEXT_MINUS_7,
        SNAPSHOT_TEXT_PLUS_50,
        SNAPSHOT_TEXT_PLUS_99,
        SNAPSHOT_TEXT_MINUS_99,
    ]
    missing = [e for e in expected if e not in body]
    assert not missing, f"snapshot entityIDs missing from emitted XML: {missing}"


def test_snapshot_keys_produce_pinned_singletons_directly() -> None:
    """Belt-and-braces: re-derive the singletons from raw entity_id() calls.

    If build_cents_full_sweep() drifts but entity_id() still produces the
    same hex for the same (kind, key) inputs, this test stays green and the
    end-to-end appearance check flags the drift. If entity_id() itself drifts
    (PROJECT_NAMESPACE rotation, hashing algorithm change), this test fails
    alongside the others — pinpointing the lower-level break."""
    assert entity_id(KIND_TEMPERAMENT, "12-edo") == SNAPSHOT_TEMPERAMENT_CENTS
    assert entity_id(KIND_ACCIDENTAL_SYSTEM, "cents") == SNAPSHOT_ACCIDENTAL_SYSTEM_CENTS
    assert entity_id(KIND_TONALITY_SYSTEM, "cents") == SNAPSHOT_TONALITY_CENTS


# ----------------------------------------------------------------------------
# Byte-faithful AccidentalDefinition snippet snapshots
# ----------------------------------------------------------------------------
def _extract_accidental_block(body: str, name: str) -> str:
    """Extract the <AccidentalDefinition> block whose <name> equals `name`."""
    pattern = (
        r"\t\t\t<AccidentalDefinition>\n"
        r"\t\t\t\t<name>" + re.escape(name) + r"</name>"
        r".*?</AccidentalDefinition>"
    )
    m = re.search(pattern, body, re.DOTALL)
    assert m, f"AccidentalDefinition block for <name>{name}</name> not found"
    return m.group(0)


def _extract_composite_block(body: str, name: str) -> str:
    """Extract the <CompositeDefinition> block whose <name> equals `name`."""
    pattern = (
        r"\t\t\t<CompositeDefinition>\n"
        r"\t\t\t\t<name>" + re.escape(name) + r"</name>"
        r".*?</CompositeDefinition>"
    )
    m = re.search(pattern, body, re.DOTALL)
    assert m, f"CompositeDefinition block for <name>{name}</name> not found"
    return m.group(0)


def test_snapshot_sharp_plus_14_accidental_block(tmp_path: pathlib.Path) -> None:
    """Off-by-100 trap diagnostic: Sharp +14 AccidentalDefinition pins 114/1200."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    block = _extract_accidental_block(body, "Sharp +14")
    actual = _normalize_entity_ids(block)
    assert actual == SNAPSHOT_SHARP_PLUS_14_ACCIDENTAL_BLOCK, (
        f"snapshot diverged for Sharp +14:\n"
        f"  actual:   {actual!r}\n"
        f"  expected: {SNAPSHOT_SHARP_PLUS_14_ACCIDENTAL_BLOCK!r}"
    )


def test_snapshot_sharp_minus_50_accidental_block(tmp_path: pathlib.Path) -> None:
    """Off-by-100 trap diagnostic: Sharp -50 AccidentalDefinition pins 50/1200."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    block = _extract_accidental_block(body, "Sharp -50")
    actual = _normalize_entity_ids(block)
    assert actual == SNAPSHOT_SHARP_MINUS_50_ACCIDENTAL_BLOCK, (
        f"snapshot diverged for Sharp -50:\n"
        f"  actual:   {actual!r}\n"
        f"  expected: {SNAPSHOT_SHARP_MINUS_50_ACCIDENTAL_BLOCK!r}"
    )


def test_snapshot_flat_minus_7_accidental_block(tmp_path: pathlib.Path) -> None:
    """Off-by-100 trap mirror: Flat -7 AccidentalDefinition pins -107/1200."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    block = _extract_accidental_block(body, "Flat -7")
    actual = _normalize_entity_ids(block)
    assert actual == SNAPSHOT_FLAT_MINUS_7_ACCIDENTAL_BLOCK, (
        f"snapshot diverged for Flat -7:\n"
        f"  actual:   {actual!r}\n"
        f"  expected: {SNAPSHOT_FLAT_MINUS_7_ACCIDENTAL_BLOCK!r}"
    )


def test_snapshot_natural_plus_50_accidental_block(tmp_path: pathlib.Path) -> None:
    """Class C (text-only) — Natural +50 AccidentalDefinition pins 50/1200."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    block = _extract_accidental_block(body, "Natural +50")
    actual = _normalize_entity_ids(block)
    assert actual == SNAPSHOT_NATURAL_PLUS_50_ACCIDENTAL_BLOCK, (
        f"snapshot diverged for Natural +50:\n"
        f"  actual:   {actual!r}\n"
        f"  expected: {SNAPSHOT_NATURAL_PLUS_50_ACCIDENTAL_BLOCK!r}"
    )


def test_snapshot_sharp_zero_dev_accidental_block(tmp_path: pathlib.Path) -> None:
    """Class A (zero-dev, glyph-only): Sharp AccidentalDefinition pins 100/1200."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    block = _extract_accidental_block(body, "Sharp")
    actual = _normalize_entity_ids(block)
    assert actual == SNAPSHOT_SHARP_ZERO_ACCIDENTAL_BLOCK, (
        f"snapshot diverged for Sharp (zero-dev):\n"
        f"  actual:   {actual!r}\n"
        f"  expected: {SNAPSHOT_SHARP_ZERO_ACCIDENTAL_BLOCK!r}"
    )


# ----------------------------------------------------------------------------
# Byte-faithful CompositeDefinition snippet snapshots
# ----------------------------------------------------------------------------
def test_snapshot_sharp_plus_14_composite_block(tmp_path: pathlib.Path) -> None:
    """Class B composite for Sharp +14: glyph + text via relativeAttachment."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    block = _extract_composite_block(body, "Sharp +14")
    actual = _normalize_entity_ids(block)
    assert actual == SNAPSHOT_SHARP_PLUS_14_COMPOSITE_BLOCK, (
        f"snapshot diverged for Sharp +14 composite:\n"
        f"  actual:   {actual!r}\n"
        f"  expected: {SNAPSHOT_SHARP_PLUS_14_COMPOSITE_BLOCK!r}"
    )


def test_snapshot_sharp_minus_50_composite_block(tmp_path: pathlib.Path) -> None:
    """Class B composite for Sharp -50."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    block = _extract_composite_block(body, "Sharp -50")
    actual = _normalize_entity_ids(block)
    assert actual == SNAPSHOT_SHARP_MINUS_50_COMPOSITE_BLOCK, (
        f"snapshot diverged for Sharp -50 composite:\n"
        f"  actual:   {actual!r}\n"
        f"  expected: {SNAPSHOT_SHARP_MINUS_50_COMPOSITE_BLOCK!r}"
    )


def test_snapshot_flat_minus_7_composite_block(tmp_path: pathlib.Path) -> None:
    """Class B composite for Flat -7."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    block = _extract_composite_block(body, "Flat -7")
    actual = _normalize_entity_ids(block)
    assert actual == SNAPSHOT_FLAT_MINUS_7_COMPOSITE_BLOCK, (
        f"snapshot diverged for Flat -7 composite:\n"
        f"  actual:   {actual!r}\n"
        f"  expected: {SNAPSHOT_FLAT_MINUS_7_COMPOSITE_BLOCK!r}"
    )


def test_snapshot_natural_plus_50_composite_block(tmp_path: pathlib.Path) -> None:
    """Class C composite for Natural +50: text-only at xOffset=18, yOffset=-12."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    block = _extract_composite_block(body, "Natural +50")
    actual = _normalize_entity_ids(block)
    assert actual == SNAPSHOT_NATURAL_PLUS_50_COMPOSITE_BLOCK, (
        f"snapshot diverged for Natural +50 composite:\n"
        f"  actual:   {actual!r}\n"
        f"  expected: {SNAPSHOT_NATURAL_PLUS_50_COMPOSITE_BLOCK!r}"
    )


def test_snapshot_sharp_zero_dev_composite_block(tmp_path: pathlib.Path) -> None:
    """Class A composite for Sharp (zero-dev): glyph-only, no attachments."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    block = _extract_composite_block(body, "Sharp")
    actual = _normalize_entity_ids(block)
    assert actual == SNAPSHOT_SHARP_ZERO_COMPOSITE_BLOCK, (
        f"snapshot diverged for Sharp (zero-dev) composite:\n"
        f"  actual:   {actual!r}\n"
        f"  expected: {SNAPSHOT_SHARP_ZERO_COMPOSITE_BLOCK!r}"
    )
