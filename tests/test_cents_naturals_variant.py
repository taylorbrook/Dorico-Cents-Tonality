"""Variant-mode tests for --mode cents-naturals.

The cents-naturals variant differs from cents mode in exactly two ways:
  1. Natural ±cents accidentals render as ♮ + cent text (Class B),
     not bare cent text (Class C).
  2. Tonality + AccidentalSystem + Accidental + Composite entityIDs
     use a '-cents-naturals' suffix so the two libraries coexist
     in Dorico's picker without collision.

These tests pin those two deltas. Glyph/Text/Temperament entityIDs
are intentionally SHARED across modes (mode-independent SMuFL names,
text labels, and a single 12-EDO temperament).
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

from cents_generator.constants import (
    KEY_ACC_SYSTEM_CENTS,
    KEY_ACC_SYSTEM_CENTS_NATURALS,
    KEY_TEMPERAMENT_12EDO_CENTS,
    KEY_TONALITY_CENTS,
    KEY_TONALITY_CENTS_NATURALS,
    KIND_ACCIDENTAL,
    KIND_ACCIDENTAL_SYSTEM,
    KIND_GLYPH,
    KIND_TEMPERAMENT,
    KIND_TONALITY_SYSTEM,
)
from cents_generator.main import run
from cents_generator.uuids import entity_id


# ----------------------------------------------------------------------------
# 1. Class-B shape for natural +14 in cents-naturals mode
# ----------------------------------------------------------------------------
def test_natural_plus_14_is_class_b_shaped_in_variant(tmp_path):
    """Headline behavioral diff: natural+14 emits ♮ glyph + cent text.

    Cents mode would emit Class C (text-only, no glyph, no attachment).
    """
    out = tmp_path / "cn.doricolib"
    run(out, mode="cents-naturals")
    body = out.read_text("utf-8")

    natural_plus_14_eid = entity_id(
        KIND_ACCIDENTAL, "natural+14-cents-naturals"
    )
    assert natural_plus_14_eid in body, "natural+14 accidental missing"

    # Find the AccidentalDefinition for natural+14 -> get its
    # compositeID -> find that CompositeDefinition.
    acc_match = re.search(
        r"<AccidentalDefinition>\s*<name>Natural \+14</name>\s*"
        r"<entityID>" + re.escape(natural_plus_14_eid) + r"</entityID>"
        r".*?<compositeID>(comp\.user\.[0-9a-f]{32})</compositeID>",
        body, re.DOTALL,
    )
    assert acc_match, "could not locate Natural +14 AccidentalDefinition"
    comp_eid = acc_match.group(1)

    # Locate that CompositeDefinition
    comp_re = (
        r"<CompositeDefinition>\s*<name>Natural \+14</name>\s*"
        r"<entityID>" + re.escape(comp_eid) + r"</entityID>.*?"
        r"</CompositeDefinition>"
    )
    comp_match = re.search(comp_re, body, re.DOTALL)
    assert comp_match, f"could not locate CompositeDefinition {comp_eid}"
    comp_block = comp_match.group(0)

    # Class B invariants: glyph + text + relativeAttachment
    # (XML uses lowercase-first <relativeAttachment> inside the
    # <relativeAttachments> wrapper, with kBaselineRight on pair1 and
    # kBaselineLeft on pair2 — these are the cross-mode-stable Class B
    # offsets and pair points.)
    assert comp_block.count("<componentType>kGlyph</componentType>") == 1, \
        "Natural +14 must have exactly 1 kGlyph component (Class B)"
    assert comp_block.count("<componentType>kText</componentType>") == 1, \
        "Natural +14 must have exactly 1 kText component (Class B)"
    assert "<relativeAttachment>" in comp_block, \
        "Natural +14 must have a relativeAttachment (Class B), not Class C"
    # Offsets live inside the relativeAttachment, not the components
    # (component offsets are 0 for Class B). Slice to that block to avoid
    # matching component offsets accidentally.
    ra_match = re.search(
        r"<relativeAttachment>.*?</relativeAttachment>", comp_block, re.DOTALL,
    )
    assert ra_match, "relativeAttachment block missing"
    ra_block = ra_match.group(0)
    assert "<xOffset>-8</xOffset>" in ra_block
    assert "<yOffset>-12</yOffset>" in ra_block
    assert ra_block.count("<componentAttachmentPoint>kBaselineRight</componentAttachmentPoint>") == 1
    assert ra_block.count("<componentAttachmentPoint>kBaselineLeft</componentAttachmentPoint>") == 1


# ----------------------------------------------------------------------------
# 2. Class-A shape for natural-zero in cents-naturals mode
# ----------------------------------------------------------------------------
def test_natural_zero_is_class_a_shaped_in_variant(tmp_path):
    """Zero-cent natural is Class A (glyph only) in BOTH modes.

    The variant only changes natural ±cents — natural at 0¢ stays a
    single ♮ glyph with no text and no relativeAttachment.
    """
    out = tmp_path / "cn.doricolib"
    run(out, mode="cents-naturals")
    body = out.read_text("utf-8")

    natural_zero_eid = entity_id(
        KIND_ACCIDENTAL, "natural-cents-naturals"
    )
    assert natural_zero_eid in body
    # Locate AccidentalDefinition -> compositeID -> CompositeDefinition
    acc_match = re.search(
        r"<AccidentalDefinition>\s*<name>Natural</name>\s*"
        r"<entityID>" + re.escape(natural_zero_eid) + r"</entityID>"
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
    # Class A: one kGlyph, NO kText, NO <relativeAttachment> inner element.
    # (The <relativeAttachments array="true"/> wrapper may still appear as
    # an empty self-closing element — Class A invariant is the absence of
    # an inner <relativeAttachment> child.)
    assert comp_block.count("<componentType>kGlyph</componentType>") == 1
    assert comp_block.count("<componentType>kText</componentType>") == 0
    assert "<relativeAttachment>" not in comp_block


# ----------------------------------------------------------------------------
# 3. Sharp/flat parity: sharp+14 byte-identical between modes after
#    entityID normalization
# ----------------------------------------------------------------------------
def test_sharp_plus_14_composite_block_byte_identical_modulo_eids(tmp_path):
    """Sharp/flat ±cents shape must be cross-mode invariant.

    After substituting all entityIDs to a placeholder, the Sharp +14
    CompositeDefinition block in cents-naturals mode must be byte-equal
    to the same block in cents mode. This guarantees the only behavioral
    diff between the two modes is the natural-class dispatch.
    """
    out_c = tmp_path / "c.doricolib"
    out_cn = tmp_path / "cn.doricolib"
    run(out_c, mode="cents")
    run(out_cn, mode="cents-naturals")
    body_c = out_c.read_text("utf-8")
    body_cn = out_cn.read_text("utf-8")

    def extract_sharp14_block(body: str) -> str:
        m = re.search(
            r"<CompositeDefinition>\s*<name>Sharp \+14</name>.*?</CompositeDefinition>",
            body, re.DOTALL,
        )
        assert m, "Sharp +14 CompositeDefinition not found"
        return m.group(0)

    block_c = extract_sharp14_block(body_c)
    block_cn = extract_sharp14_block(body_cn)
    # Normalize entityIDs to a placeholder.
    norm = lambda s: re.sub(
        r"(comp|accidental|glyph|text)\.user\.[0-9a-f]{32}",
        r"\1.user.<HEX>", s,
    )
    assert norm(block_c) == norm(block_cn), (
        "Sharp +14 composite differs between cents and cents-naturals "
        "modes after entityID normalization — sharp/flat shape must "
        "be byte-identical across modes."
    )


# ----------------------------------------------------------------------------
# 4. Determinism (in-process and subprocess)
# ----------------------------------------------------------------------------
def test_two_in_process_runs_byte_identical(tmp_path):
    a = tmp_path / "a.doricolib"
    b = tmp_path / "b.doricolib"
    run(a, mode="cents-naturals")
    run(b, mode="cents-naturals")
    assert a.read_bytes() == b.read_bytes()


def test_two_subprocess_runs_byte_identical(tmp_path):
    repo_root = pathlib.Path(__file__).parent.parent
    build_py = repo_root / "build.py"
    a = tmp_path / "a.doricolib"
    b = tmp_path / "b.doricolib"
    for path in (a, b):
        r = subprocess.run(
            [sys.executable, str(build_py),
             "--mode", "cents-naturals", "--out", str(path)],
            capture_output=True, cwd=str(repo_root),
        )
        assert r.returncode == 0, r.stderr.decode()
    assert a.read_bytes() == b.read_bytes()


# ----------------------------------------------------------------------------
# 5. EntityID isolation vs cents mode
# ----------------------------------------------------------------------------
def test_variant_entityids_isolated_from_cents_mode():
    """Pin which entityIDs differ across modes and which are intentionally
    shared, so the two libraries coexist in Dorico's picker.
    """
    # Tonality + accidental-system: DIFFERENT (variant suffix)
    assert (
        entity_id(KIND_TONALITY_SYSTEM, KEY_TONALITY_CENTS)
        != entity_id(KIND_TONALITY_SYSTEM, KEY_TONALITY_CENTS_NATURALS)
    )
    assert (
        entity_id(KIND_ACCIDENTAL_SYSTEM, KEY_ACC_SYSTEM_CENTS)
        != entity_id(KIND_ACCIDENTAL_SYSTEM, KEY_ACC_SYSTEM_CENTS_NATURALS)
    )
    # natural+14 accidental: DIFFERENT
    assert (
        entity_id(KIND_ACCIDENTAL, "natural+14")
        != entity_id(KIND_ACCIDENTAL, "natural+14-cents-naturals")
    )
    # 12-EDO temperament: SHARED (intentional)
    assert entity_id(KIND_TEMPERAMENT, KEY_TEMPERAMENT_12EDO_CENTS) == \
           entity_id(KIND_TEMPERAMENT, KEY_TEMPERAMENT_12EDO_CENTS)
    # Glyph entityIDs: SHARED (mode-independent SMuFL name)
    assert entity_id(KIND_GLYPH, "accidentalNatural") == \
           entity_id(KIND_GLYPH, "accidentalNatural")
