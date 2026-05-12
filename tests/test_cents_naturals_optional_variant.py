"""Variant-mode tests for --mode cents-naturals-optional.

The cents-naturals-optional variant differs from both cents mode and
cents-naturals mode by emitting BOTH flavors of every nonzero natural
±cent — a Class C text-only entry AND a Class B ♮+text entry — under
DIFFERENT entityIDs but the SAME pitch_delta_from_natural. Zero-cent
natural stays Class A (one entry). Sharp/flat ±cents are single Class B
entries (one entry, same shape as cents-naturals mode).

These tests pin: the two natural flavors' shapes, their shared pitch
delta + distinct entityIDs, the cross-mode sharp/flat parity, the new
ordering tiebreak (text-only before with-glyph), determinism, and the
cents + cents-naturals regression md5s.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

from cents_generator.constants import (
    KEY_ACC_SYSTEM_CENTS,
    KEY_ACC_SYSTEM_CENTS_NATURALS,
    KEY_ACC_SYSTEM_CENTS_NATURALS_OPTIONAL,
    KEY_TEMPERAMENT_12EDO_CENTS,
    KEY_TONALITY_CENTS,
    KEY_TONALITY_CENTS_NATURALS,
    KEY_TONALITY_CENTS_NATURALS_OPTIONAL,
    KIND_ACCIDENTAL,
    KIND_ACCIDENTAL_SYSTEM,
    KIND_GLYPH,
    KIND_TEMPERAMENT,
    KIND_TONALITY_SYSTEM,
)
from cents_generator.main import run
from cents_generator.uuids import entity_id


# ----------------------------------------------------------------------------
# 1. Class-C shape for the text-only natural +14 flavor
# ----------------------------------------------------------------------------
def test_text_only_natural_plus_14_is_class_c_shaped(tmp_path):
    out = tmp_path / "cno.doricolib"
    run(out, mode="cents-naturals-optional")
    body = out.read_text("utf-8")

    eid = entity_id(
        KIND_ACCIDENTAL, "natural+14-cents-naturals-optional-textonly"
    )
    assert eid in body
    # AccidentalDefinition has user-visible name "+14" (Class C convention).
    acc_match = re.search(
        r"<AccidentalDefinition>\s*<name>\+14</name>\s*"
        r"<entityID>" + re.escape(eid) + r"</entityID>"
        r".*?<compositeID>(comp\.user\.[0-9a-f]{32})</compositeID>"
        r".*?<pitchDeltaFromNatural>14/1200</pitchDeltaFromNatural>",
        body, re.DOTALL,
    )
    assert acc_match, "could not locate text-only natural+14 AccidentalDefinition"
    comp_eid = acc_match.group(1)
    comp_match = re.search(
        r"<CompositeDefinition>\s*<name>\+14</name>\s*"
        r"<entityID>" + re.escape(comp_eid) + r"</entityID>.*?"
        r"</CompositeDefinition>",
        body, re.DOTALL,
    )
    assert comp_match
    comp_block = comp_match.group(0)
    # Class C: 1 kText, 0 kGlyph, 0 inner <relativeAttachment>.
    assert comp_block.count("<componentType>kText</componentType>") == 1
    assert comp_block.count("<componentType>kGlyph</componentType>") == 0
    assert "<relativeAttachment>" not in comp_block


# ----------------------------------------------------------------------------
# 2. Class-B shape for the with-glyph natural +14 flavor
# ----------------------------------------------------------------------------
def test_with_glyph_natural_plus_14_is_class_b_shaped(tmp_path):
    out = tmp_path / "cno.doricolib"
    run(out, mode="cents-naturals-optional")
    body = out.read_text("utf-8")

    eid = entity_id(
        KIND_ACCIDENTAL, "natural+14-cents-naturals-optional-withglyph"
    )
    assert eid in body
    acc_match = re.search(
        r"<AccidentalDefinition>\s*<name>Natural \+14</name>\s*"
        r"<entityID>" + re.escape(eid) + r"</entityID>"
        r".*?<compositeID>(comp\.user\.[0-9a-f]{32})</compositeID>"
        r".*?<pitchDeltaFromNatural>14/1200</pitchDeltaFromNatural>",
        body, re.DOTALL,
    )
    assert acc_match, "could not locate with-glyph natural+14 AccidentalDefinition"
    comp_eid = acc_match.group(1)
    comp_match = re.search(
        r"<CompositeDefinition>\s*<name>Natural \+14</name>\s*"
        r"<entityID>" + re.escape(comp_eid) + r"</entityID>.*?"
        r"</CompositeDefinition>",
        body, re.DOTALL,
    )
    assert comp_match
    comp_block = comp_match.group(0)
    # Class B: 1 kGlyph + 1 kText + 1 relativeAttachment.
    assert comp_block.count("<componentType>kGlyph</componentType>") == 1
    assert comp_block.count("<componentType>kText</componentType>") == 1
    ra_match = re.search(
        r"<relativeAttachment>.*?</relativeAttachment>", comp_block, re.DOTALL,
    )
    assert ra_match
    ra_block = ra_match.group(0)
    assert "<xOffset>-8</xOffset>" in ra_block
    assert "<yOffset>-12</yOffset>" in ra_block
    assert ra_block.count(
        "<componentAttachmentPoint>kBaselineRight</componentAttachmentPoint>"
    ) == 1
    assert ra_block.count(
        "<componentAttachmentPoint>kBaselineLeft</componentAttachmentPoint>"
    ) == 1


# ----------------------------------------------------------------------------
# 3. Both natural flavors share the same pitch delta but distinct entityIDs
# ----------------------------------------------------------------------------
def test_both_natural_flavors_share_pitch_delta_distinct_entityids():
    # SAME pitchDeltaFromNatural is asserted via the file body in tests 1
    # and 2 above. Here we pin the entityID-distinctness invariant
    # directly from the uuid layer.
    text_only_eid = entity_id(
        KIND_ACCIDENTAL, "natural+14-cents-naturals-optional-textonly"
    )
    with_glyph_eid = entity_id(
        KIND_ACCIDENTAL, "natural+14-cents-naturals-optional-withglyph"
    )
    assert text_only_eid != with_glyph_eid


# ----------------------------------------------------------------------------
# 4. Class-A shape for natural-zero
# ----------------------------------------------------------------------------
def test_natural_zero_is_class_a_shaped(tmp_path):
    out = tmp_path / "cno.doricolib"
    run(out, mode="cents-naturals-optional")
    body = out.read_text("utf-8")

    eid = entity_id(KIND_ACCIDENTAL, "natural-cents-naturals-optional")
    assert eid in body
    acc_match = re.search(
        r"<AccidentalDefinition>\s*<name>Natural</name>\s*"
        r"<entityID>" + re.escape(eid) + r"</entityID>"
        r".*?<compositeID>(comp\.user\.[0-9a-f]{32})</compositeID>",
        body, re.DOTALL,
    )
    assert acc_match
    comp_eid = acc_match.group(1)
    comp_match = re.search(
        r"<CompositeDefinition>\s*<name>Natural</name>\s*"
        r"<entityID>" + re.escape(comp_eid) + r"</entityID>.*?"
        r"</CompositeDefinition>",
        body, re.DOTALL,
    )
    assert comp_match
    comp_block = comp_match.group(0)
    assert comp_block.count("<componentType>kGlyph</componentType>") == 1
    assert comp_block.count("<componentType>kText</componentType>") == 0
    assert "<relativeAttachment>" not in comp_block


# ----------------------------------------------------------------------------
# 5. Sharp/flat parity with cents-naturals mode (block byte-identical
#    after entityID normalization)
# ----------------------------------------------------------------------------
def test_sharp_plus_14_composite_block_byte_identical_modulo_eids(tmp_path):
    out_cn = tmp_path / "cn.doricolib"
    out_cno = tmp_path / "cno.doricolib"
    run(out_cn, mode="cents-naturals")
    run(out_cno, mode="cents-naturals-optional")
    body_cn = out_cn.read_text("utf-8")
    body_cno = out_cno.read_text("utf-8")

    def extract(body: str) -> str:
        m = re.search(
            r"<CompositeDefinition>\s*<name>Sharp \+14</name>.*?</CompositeDefinition>",
            body, re.DOTALL,
        )
        assert m, "Sharp +14 CompositeDefinition not found"
        return m.group(0)

    norm = lambda s: re.sub(
        r"(comp|accidental|glyph|text)\.user\.[0-9a-f]{32}",
        r"\1.user.<HEX>", s,
    )
    assert norm(extract(body_cn)) == norm(extract(body_cno))


# ----------------------------------------------------------------------------
# 6. Determinism (in-process and subprocess)
# ----------------------------------------------------------------------------
def test_two_in_process_runs_byte_identical(tmp_path):
    a = tmp_path / "a.doricolib"
    b = tmp_path / "b.doricolib"
    run(a, mode="cents-naturals-optional")
    run(b, mode="cents-naturals-optional")
    assert a.read_bytes() == b.read_bytes()


def test_two_subprocess_runs_byte_identical(tmp_path):
    repo_root = pathlib.Path(__file__).parent.parent
    build_py = repo_root / "build.py"
    a = tmp_path / "a.doricolib"
    b = tmp_path / "b.doricolib"
    for path in (a, b):
        r = subprocess.run(
            [sys.executable, str(build_py),
             "--mode", "cents-naturals-optional", "--out", str(path)],
            capture_output=True, cwd=str(repo_root),
        )
        assert r.returncode == 0, r.stderr.decode()
    assert a.read_bytes() == b.read_bytes()


# ----------------------------------------------------------------------------
# 7. EntityID isolation vs cents AND cents-naturals modes
# ----------------------------------------------------------------------------
def test_variant_entityids_isolated_from_prior_modes():
    # Tonality + accidental-system: all three modes DIFFER
    eids_tonality = {
        entity_id(KIND_TONALITY_SYSTEM, KEY_TONALITY_CENTS),
        entity_id(KIND_TONALITY_SYSTEM, KEY_TONALITY_CENTS_NATURALS),
        entity_id(KIND_TONALITY_SYSTEM, KEY_TONALITY_CENTS_NATURALS_OPTIONAL),
    }
    assert len(eids_tonality) == 3
    eids_acc_system = {
        entity_id(KIND_ACCIDENTAL_SYSTEM, KEY_ACC_SYSTEM_CENTS),
        entity_id(KIND_ACCIDENTAL_SYSTEM, KEY_ACC_SYSTEM_CENTS_NATURALS),
        entity_id(KIND_ACCIDENTAL_SYSTEM, KEY_ACC_SYSTEM_CENTS_NATURALS_OPTIONAL),
    }
    assert len(eids_acc_system) == 3
    # natural+14 accidentals: cents (Class C key='natural+14') vs
    # cents-naturals (Class B key='natural+14-cents-naturals') vs the
    # new variant's TWO flavors — all four must be distinct.
    eids_natural14 = {
        entity_id(KIND_ACCIDENTAL, "natural+14"),
        entity_id(KIND_ACCIDENTAL, "natural+14-cents-naturals"),
        entity_id(KIND_ACCIDENTAL, "natural+14-cents-naturals-optional-textonly"),
        entity_id(KIND_ACCIDENTAL, "natural+14-cents-naturals-optional-withglyph"),
    }
    assert len(eids_natural14) == 4
    # 12-EDO temperament: SHARED across all modes (uses same key)
    # — sanity-pin the determinism of entity_id over the canonical key
    assert (
        entity_id(KIND_TEMPERAMENT, KEY_TEMPERAMENT_12EDO_CENTS)
        == entity_id(KIND_TEMPERAMENT, KEY_TEMPERAMENT_12EDO_CENTS)
    )
    # Glyph entityIDs: SHARED (mode-independent SMuFL name)
    assert (
        entity_id(KIND_GLYPH, "accidentalNatural")
        == entity_id(KIND_GLYPH, "accidentalNatural")
    )


# ----------------------------------------------------------------------------
# 8. Entity count sanity
# ----------------------------------------------------------------------------
def test_entity_section_counts(tmp_path):
    out = tmp_path / "cno.doricolib"
    run(out, mode="cents-naturals-optional")
    body = out.read_text("utf-8")
    assert body.count("<AccidentalDefinition>") == 795
    assert body.count("<CompositeDefinition>") == 795
    assert body.count("<TextPrimitiveEntityDefinition>") == 198
    assert body.count("<GlyphPrimitiveEntityDefinition>") == 3
    assert body.count("<TonalitySystemDefinition>") == 1
    assert body.count("<AccidentalSystem>") == 1
    assert body.count("<TemperamentDefinition>") == 1


# ----------------------------------------------------------------------------
# 9. Regression: cents and cents-naturals modes byte-identical to shipped
# ----------------------------------------------------------------------------
def test_cents_mode_md5_unchanged(tmp_path):
    out = tmp_path / "c.doricolib"
    run(out, mode="cents")
    md5 = hashlib.md5(out.read_bytes()).hexdigest()
    assert md5 == "4cd707d2f4b10154a528b95e2ff5db9f", (
        f"cents-mode regression: got md5 {md5}, expected "
        "4cd707d2f4b10154a528b95e2ff5db9f"
    )


def test_cents_naturals_mode_md5_unchanged(tmp_path):
    out = tmp_path / "cn.doricolib"
    run(out, mode="cents-naturals")
    md5 = hashlib.md5(out.read_bytes()).hexdigest()
    assert md5 == "205a51d2639d6fcfd79c48b874af38e5", (
        f"cents-naturals-mode regression: got md5 {md5}, expected "
        "205a51d2639d6fcfd79c48b874af38e5"
    )


# ----------------------------------------------------------------------------
# 10. Sort tiebreak: text-only natural before with-glyph natural at +14
# ----------------------------------------------------------------------------
def test_natural_plus_14_textonly_appears_before_withglyph_in_acc_system(tmp_path):
    """LOCKED ordering: variant_tiebreak=0 (text-only) comes before
    variant_tiebreak=1 (with-glyph) at the same (delta, base, cents).
    Asserted via index position in <accidentalDefinitionIDs>.
    """
    out = tmp_path / "cno.doricolib"
    run(out, mode="cents-naturals-optional")
    body = out.read_text("utf-8")

    # Extract the AccidentalSystem's IDs string.
    m = re.search(
        r"<accidentalDefinitionIDs>([^<]+)</accidentalDefinitionIDs>",
        body,
    )
    assert m, "accidentalDefinitionIDs missing"
    ids_str = m.group(1)

    text_only_eid = entity_id(
        KIND_ACCIDENTAL, "natural+14-cents-naturals-optional-textonly"
    )
    with_glyph_eid = entity_id(
        KIND_ACCIDENTAL, "natural+14-cents-naturals-optional-withglyph"
    )
    i_text = ids_str.find(text_only_eid)
    i_glyph = ids_str.find(with_glyph_eid)
    assert i_text != -1 and i_glyph != -1
    assert i_text < i_glyph, (
        "tiebreak violation: text-only natural+14 must appear BEFORE "
        "with-glyph natural+14 in accidentalDefinitionIDs (LOCKED order)"
    )
