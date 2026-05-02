"""Structural-invariants tests for the cents-mode 1411-entity output (D-07.2).

These tests run the orchestrator end-to-end via run(out_path, mode="cents")
and assert structural invariants on the emitted bytes:
- Per-section entity counts (1/1/597/1/198/3/597 = 1398 top-level entity-
  definition rows; total entity count "1411" in CONTEXT.md counts inline
  structural elements which are not top-level entities — the operational
  per-section counts are pinned here)
- Tonality system name 'cents'
- Temperament uses 12-EDO divisions (200/100/200/200/100/200/200)
- Section ordering matches canonical SECTION_ORDER
- xmllint --noout passes (well-formed XML), with ElementTree fallback
- Pitfall 8: all three zero-dev entityIDs (Sharp/Flat/Natural) appear in
  the AccidentalSystem's ID list
- D-02: AccidentalSystem ID list is in pitch-delta ascending order
- Pitfall 1: pitch-delta count invariants prove the centralized helper went
  through every accidental — e.g. 50/1200 must appear exactly twice
  (Sharp -50 and Natural +50), which is impossible if the helper is bypassed
  (a bypass would emit -50/1200 for Sharp -50 instead).
- D-01: all 3 glyph blocks emit <parentEntityID/> self-closing empty
- File version is 1.1450 (Pitfall 4)
- User-visible names follow FEATURES.md naming convention

Mirrors tests/test_template_roundtrip.py but at the production scale.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

import pytest

from cents_generator.constants import KIND_ACCIDENTAL
from cents_generator.main import run
from cents_generator.uuids import entity_id


def test_cents_entity_counts(tmp_path: pathlib.Path) -> None:
    """Per-section entity-definition counts (1+1+597+1+198+3+597 = 1398 rows)."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    assert body.count("<TemperamentDefinition>") == 1, \
        f"expected 1 TemperamentDefinition, got {body.count('<TemperamentDefinition>')}"
    assert body.count("<AccidentalSystem>") == 1, \
        f"expected 1 AccidentalSystem, got {body.count('<AccidentalSystem>')}"
    assert body.count("<AccidentalDefinition>") == 597, \
        f"expected 597 AccidentalDefinitions, got {body.count('<AccidentalDefinition>')}"
    assert body.count("<TonalitySystemDefinition>") == 1, \
        f"expected 1 TonalitySystemDefinition, got {body.count('<TonalitySystemDefinition>')}"
    assert body.count("<TextPrimitiveEntityDefinition>") == 198, \
        f"expected 198 TextPrimitiveEntityDefinitions, got {body.count('<TextPrimitiveEntityDefinition>')}"
    assert body.count("<GlyphPrimitiveEntityDefinition>") == 3, \
        f"expected 3 GlyphPrimitiveEntityDefinitions, got {body.count('<GlyphPrimitiveEntityDefinition>')}"
    assert body.count("<CompositeDefinition>") == 597, \
        f"expected 597 CompositeDefinitions, got {body.count('<CompositeDefinition>')}"


def test_cents_tonality_name(tmp_path: pathlib.Path) -> None:
    """TON-01: TonalitySystemDefinition name is 'cents'."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    # Both AccidentalSystem and TonalitySystemDefinition use name='cents'.
    # The name appears at least 2x; assert presence (specific position later).
    assert "<name>cents</name>" in body, "missing user-visible 'cents' name"
    assert body.count("<name>cents</name>") == 2, \
        f"expected 2 occurrences of <name>cents</name> (AccidentalSystem + TonalitySystemDefinition), got {body.count('<name>cents</name>')}"


def test_cents_temperament_divisions(tmp_path: pathlib.Path) -> None:
    """TON-02: 12-EDO temperament has divisions 200/100/200/200/100/200/200."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    assert "<noteAtoB>200</noteAtoB>" in body
    assert "<noteBtoC>100</noteBtoC>" in body
    assert "<noteCtoD>200</noteCtoD>" in body
    assert "<noteDtoE>200</noteDtoE>" in body
    assert "<noteEtoF>100</noteEtoF>" in body
    assert "<noteFtoG>200</noteFtoG>" in body
    assert "<noteGtoA>200</noteGtoA>" in body


def test_cents_section_ordering_matches(tmp_path: pathlib.Path) -> None:
    """Section tags appear in canonical SECTION_ORDER."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    section_tags = [
        "<temperaments>",
        "<accidentalSystems>",
        "<accidentalDefinitions>",
        "<tonalitySystemDefinitions>",
        "<textDefinitions>",
        "<glyphDefinitions>",
        "<compositeDefinitions>",
    ]
    positions = [body.index(tag) for tag in section_tags]
    assert positions == sorted(positions), \
        f"sections out of order: {dict(zip(section_tags, positions))}"


def test_cents_xmllint_well_formed(tmp_path: pathlib.Path) -> None:
    """xmllint --noout proves XML well-formedness; falls back to ElementTree."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    if shutil.which("xmllint"):
        result = subprocess.run(
            ["xmllint", "--noout", str(out)],
            capture_output=True,
        )
        assert result.returncode == 0, f"xmllint failed: {result.stderr.decode()}"
    else:
        try:
            ET.parse(out)
        except ET.ParseError as e:  # pragma: no cover
            pytest.fail(f"Python ElementTree.parse() failed (xmllint absent): {e}")


def test_cents_accidental_system_includes_all_three_zero_dev(tmp_path: pathlib.Path) -> None:
    """Pitfall 8: removing Natural from AccidentalSystem causes Dorico to crash on
    note input. Asserting all three zero-dev entityIDs (Sharp, Flat, Natural) are
    present in the 597-ID string is the structural defense."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    m = re.search(r"<accidentalDefinitionIDs>([^<]+)</accidentalDefinitionIDs>", body)
    assert m, "accidentalDefinitionIDs element not found"
    ids = set(m.group(1).split(", "))

    expected_natural = entity_id(KIND_ACCIDENTAL, "natural")
    expected_sharp = entity_id(KIND_ACCIDENTAL, "sharp")
    expected_flat = entity_id(KIND_ACCIDENTAL, "flat")
    assert expected_natural in ids, \
        "Pitfall 8: Natural zero-dev missing from AccidentalSystem ID list"
    assert expected_sharp in ids, \
        "zero-dev Sharp missing from AccidentalSystem ID list"
    assert expected_flat in ids, \
        "zero-dev Flat missing from AccidentalSystem ID list"


def test_cents_accidental_definition_ids_in_pitch_delta_order(tmp_path: pathlib.Path) -> None:
    """D-02: accidentalDefinitionIDs string is ordered by pitchDeltaFromNatural ascending."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    m = re.search(r"<accidentalDefinitionIDs>([^<]+)</accidentalDefinitionIDs>", body)
    assert m, "accidentalDefinitionIDs element not found"
    ids = m.group(1).split(", ")
    assert len(ids) == 597, f"expected 597 IDs, got {len(ids)}"

    # Build {accidental entityID -> int(pitch_delta numerator)} from the
    # AccidentalDefinition blocks. Multiline regex captures (entityID, num).
    acc_re = re.compile(
        r"<AccidentalDefinition>.*?<entityID>(accidental\.user\.[0-9a-f]{32})</entityID>"
        r".*?<pitchDeltaFromNatural>(-?\d+)/1200</pitchDeltaFromNatural>",
        re.DOTALL,
    )
    delta_by_id = {match.group(1): int(match.group(2)) for match in acc_re.finditer(body)}
    assert len(delta_by_id) == 597, \
        f"expected 597 accidental blocks, got {len(delta_by_id)}"

    # Resolve each ID in the AccidentalSystem string to its delta; assert monotonic.
    deltas_in_string_order = [delta_by_id[i] for i in ids]
    assert deltas_in_string_order == sorted(deltas_in_string_order), (
        f"accidentalDefinitionIDs string is NOT in pitch-delta ascending order. "
        f"First few: {deltas_in_string_order[:10]}; last few: {deltas_in_string_order[-10:]}"
    )
    # And spot-check the boundaries.
    assert deltas_in_string_order[0] == -199, \
        f"first delta should be -199, got {deltas_in_string_order[0]}"
    assert deltas_in_string_order[-1] == 199, \
        f"last delta should be 199, got {deltas_in_string_order[-1]}"


def test_cents_no_off_by_100_in_pitch_deltas(tmp_path: pathlib.Path) -> None:
    """Pitfall 1: every non-zero-dev accidental's pitchDeltaFromNatural must
    come from the centralized helper. Verify by counting specific delta strings
    — these counts are impossible if the helper is bypassed.

    Example diagnostic: 50/1200 must appear exactly twice (Sharp -50 from
    100 + (-50) and Natural +50 from 0 + 50). If the helper were bypassed and
    someone wrote `pitch_delta = cents`, Sharp -50 would emit -50/1200 (wrong)
    and 50/1200 would appear only once (Natural +50).
    """
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    # 50/1200 appears exactly twice: Sharp -50 (100 + -50 = 50) and Natural +50.
    assert body.count("<pitchDeltaFromNatural>50/1200</pitchDeltaFromNatural>") == 2, \
        "expected 50/1200 twice (Sharp -50 + Natural +50) — Pitfall 1 diagnostic"
    # -50/1200 appears exactly twice: Flat +50 (-100 + 50) and Natural -50.
    assert body.count("<pitchDeltaFromNatural>-50/1200</pitchDeltaFromNatural>") == 2, \
        "expected -50/1200 twice (Flat +50 + Natural -50)"
    # Off-by-100 trap diagnostic counts (single occurrences):
    assert body.count("<pitchDeltaFromNatural>114/1200</pitchDeltaFromNatural>") == 1, \
        "expected 114/1200 once (Sharp +14)"
    assert body.count("<pitchDeltaFromNatural>-107/1200</pitchDeltaFromNatural>") == 1, \
        "expected -107/1200 once (Flat -7)"
    # Boundaries (single occurrences — only one (base, cents) combination yields these):
    assert body.count("<pitchDeltaFromNatural>199/1200</pitchDeltaFromNatural>") == 1, \
        "expected 199/1200 once (Sharp +99)"
    assert body.count("<pitchDeltaFromNatural>-199/1200</pitchDeltaFromNatural>") == 1, \
        "expected -199/1200 once (Flat -99)"
    # Note: 99/1200 and -99/1200 each appear TWICE under the helper's correct math
    # (Plan deviation Rule 1 — see SUMMARY): Sharp -1 (100 + -1 = 99) and
    # Natural +99 (0 + 99 = 99) both land at 99; Flat +1 (-100 + 1 = -99) and
    # Natural -99 (0 + -99 = -99) both land at -99. The plan's pinned == 1 was
    # mathematically inconsistent with the centralized helper — corrected below.
    assert body.count("<pitchDeltaFromNatural>99/1200</pitchDeltaFromNatural>") == 2, \
        "expected 99/1200 twice (Sharp -1 + Natural +99) — Pitfall 1 diagnostic"
    assert body.count("<pitchDeltaFromNatural>-99/1200</pitchDeltaFromNatural>") == 2, \
        "expected -99/1200 twice (Flat +1 + Natural -99)"
    # Zero-dev (single occurrences):
    assert body.count("<pitchDeltaFromNatural>100/1200</pitchDeltaFromNatural>") == 1, \
        "expected 100/1200 once (Sharp zero-dev)"
    assert body.count("<pitchDeltaFromNatural>-100/1200</pitchDeltaFromNatural>") == 1, \
        "expected -100/1200 once (Flat zero-dev)"
    assert body.count("<pitchDeltaFromNatural>0/1200</pitchDeltaFromNatural>") == 1, \
        "expected 0/1200 once (Natural zero-dev)"


def test_cents_zero_dev_names_present(tmp_path: pathlib.Path) -> None:
    """TON-03: clean Sharp/Flat/Natural at 0¢ user-visible names appear."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    assert "<name>Sharp</name>" in body, "missing zero-dev <name>Sharp</name>"
    assert "<name>Flat</name>" in body, "missing zero-dev <name>Flat</name>"
    assert "<name>Natural</name>" in body, "missing zero-dev <name>Natural</name>"


def test_cents_signed_label_names_present(tmp_path: pathlib.Path) -> None:
    """TON-04, TON-05: signed-label names appear for sample non-zero accidentals."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    assert "<name>Sharp +14</name>" in body
    assert "<name>Sharp -50</name>" in body
    assert "<name>Flat -7</name>" in body
    assert "<name>Natural -7</name>" in body
    assert "<name>Natural +50</name>" in body
    assert "<name>Sharp +99</name>" in body
    assert "<name>Flat -99</name>" in body


def test_cents_file_version_is_1_1450(tmp_path: pathlib.Path) -> None:
    """fileVersion is 1.1450 (Dorico Pro 6.x library format) — Pitfall 4."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")
    assert "<fileVersion>1.1450</fileVersion>" in body


def test_cents_glyphs_have_empty_parents(tmp_path: pathlib.Path) -> None:
    """D-01: all 3 cents-mode glyphs emit <parentEntityID/> (self-closing empty),
    decoupling from any factory glyph entityID Steinberg might shift."""
    out = tmp_path / "cents.doricolib"
    run(out, mode="cents")
    body = out.read_text("utf-8")

    # Extract the <glyphDefinitions> section only — counting <parentEntityID/>
    # globally would over-match (AccidentalDefinitions also have it).
    m = re.search(r"<glyphDefinitions>(.*?)</glyphDefinitions>", body, re.DOTALL)
    assert m, "glyphDefinitions section not found"
    glyph_section = m.group(1)
    # All three glyph blocks should have <parentEntityID/> self-closing empty.
    # If Natural inherited 'glyph.accidentalNatural' (template-mode quirk),
    # we'd see <parentEntityID>glyph.accidentalNatural</parentEntityID> instead.
    assert glyph_section.count("<parentEntityID/>") == 3, (
        f"expected 3 self-closing empty parentEntityID elements in glyph section, "
        f"got {glyph_section.count('<parentEntityID/>')}"
    )
    assert "glyph.accidentalNatural</parentEntityID>" not in glyph_section, (
        "D-01 violated: cents-mode Natural glyph has a non-empty parentEntityID "
        "(this should be template-mode-only behavior)"
    )
