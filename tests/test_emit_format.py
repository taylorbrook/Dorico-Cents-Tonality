"""Format-quirk verification tests for emit.py.

Each test isolates one formatting requirement from STACK.md / PITFALLS Pitfall 7.
"""
from __future__ import annotations

import pathlib
import re

from cents_generator.compose import build_class_a, build_class_b, build_class_c
from cents_generator.constants import (
    FILE_VERSION,
    SECTION_ORDER,
    TEMPERAMENT_12EDO_DIVISIONS,
    KIND_ACCIDENTAL_SYSTEM,
    KIND_TEMPERAMENT,
    KIND_TONALITY_SYSTEM,
)
from cents_generator.emit import (
    SCALE_LITERAL,
    _fmt_bool,
    _fmt_hex_codepoint,
    _fmt_id_list,
    _fmt_tuple,
    write,
)
from cents_generator.entities import (
    AccidentalSystemDef,
    TemperamentDef,
    TonalitySystemDef,
)
from cents_generator.uuids import entity_id


# ----------------------------------------------------------------------------
# Private formatter unit tests
# ----------------------------------------------------------------------------
def test_fmt_tuple_zero_zero() -> None:
    assert _fmt_tuple(0, 0) == "(0, 0)"


def test_fmt_tuple_template_natural_cutoutne() -> None:
    # Template line 70: (0.192, 2.116) — non-integer floats with space.
    assert _fmt_tuple(0.192, 2.116) == "(0.192, 2.116)"


def test_fmt_tuple_has_space_after_comma() -> None:
    assert ", " in _fmt_tuple(0, 0)
    assert _fmt_tuple(1, 2).count(",") == 1
    assert _fmt_tuple(1, 2)[2:4] == ", "  # 'x, y' → space after comma


def test_fmt_id_list_comma_space_joined() -> None:
    assert _fmt_id_list(("a", "b", "c")) == "a, b, c"


def test_fmt_id_list_single_id() -> None:
    assert _fmt_id_list(("solo",)) == "solo"


def test_fmt_bool_lowercase() -> None:
    assert _fmt_bool(True) == "true"
    assert _fmt_bool(False) == "false"


def test_fmt_hex_codepoint_uppercase() -> None:
    # Capital X, capital hex digits, four-digit zero-padded.
    assert _fmt_hex_codepoint(0xE262) == "0xE262"
    assert _fmt_hex_codepoint(0xE260) == "0xE260"
    assert _fmt_hex_codepoint(0xE261) == "0xE261"


def test_scale_literal_six_decimals() -> None:
    assert SCALE_LITERAL == "100.000000"
    assert SCALE_LITERAL.count(".") == 1
    assert len(SCALE_LITERAL.split(".")[1]) == 6


# ----------------------------------------------------------------------------
# End-to-end emission: build the template's three entities and inspect output
# ----------------------------------------------------------------------------
def _build_three_template_entities():
    """Reproduce Natural, -14, #-31 using compose + assemble singletons."""
    natural_bundle = build_class_a(
        "natural",
        accidental_name="Natural",
        accidental_key="natural",
        composite_name="Natural",
        composite_key="natural",
        pitch_delta_from_natural="0/24",
        cut_out_ne=(0.192, 2.116),
        cut_out_sw=(0.476, 0.512),
        mode="template",  # Phase 2: preserve Phase 1 quirk (Natural inherits 'glyph.accidentalNatural')
    )
    sharp_minus_31 = build_class_b(
        "sharp",
        accidental_name="#-31",
        accidental_key="sharp-31-template",
        composite_name="New Composite",
        composite_key="sharp-31-template",
        label_text="-31",
        pitch_delta_from_natural="69/1200",
        mode="template",  # signature symmetry; Sharp's parent is empty in both modes
    )
    natural_minus_14 = build_class_c(
        accidental_name="-14",
        accidental_key="natural-14-template",
        composite_name="New Composite",
        composite_key="natural-14-template",
        label_text="-14",
        pitch_delta_from_natural="-14/1200",
    )

    # Singletons matching the template (Psychography tonality, etc.)
    temperament = TemperamentDef(
        name="New Temperament Definition",
        entity_id=entity_id(KIND_TEMPERAMENT, "12-edo-template"),
        note_a_to_b=TEMPERAMENT_12EDO_DIVISIONS[0],
        note_b_to_c=TEMPERAMENT_12EDO_DIVISIONS[1],
        note_c_to_d=TEMPERAMENT_12EDO_DIVISIONS[2],
        note_d_to_e=TEMPERAMENT_12EDO_DIVISIONS[3],
        note_e_to_f=TEMPERAMENT_12EDO_DIVISIONS[4],
        note_f_to_g=TEMPERAMENT_12EDO_DIVISIONS[5],
        note_g_to_a=TEMPERAMENT_12EDO_DIVISIONS[6],
    )
    # AccidentalSystem ID order from template line 31: Natural, -14, #-31.
    acc_system = AccidentalSystemDef(
        name="New Accidental System",
        entity_id=entity_id(KIND_ACCIDENTAL_SYSTEM, "psychography-template"),
        accidental_definition_ids=(
            natural_bundle.accidental.entity_id,
            natural_minus_14.accidental.entity_id,
            sharp_minus_31.accidental.entity_id,
        ),
    )
    tonality = TonalitySystemDef(
        name="Psychography",
        entity_id=entity_id(KIND_TONALITY_SYSTEM, "psychography-template"),
        temperament_definition_id=temperament.entity_id,
        accidental_system_id=acc_system.entity_id,
    )

    # Section orderings matching the template:
    # accidentalDefinitions: #-31, -14, Natural (template lines 38-73)
    # textDefinitions: -14, -31 (template lines 107-122)
    # glyphDefinitions: accidentalNatural, accidentalSharp (template lines 127-152)
    # compositeDefinitions: Natural, #-31's New Composite, -14's New Composite (template lines 157-250)
    accidentals = (
        sharp_minus_31.accidental,
        natural_minus_14.accidental,
        natural_bundle.accidental,
    )
    composites = (
        natural_bundle.composite,
        sharp_minus_31.composite,
        natural_minus_14.composite,
    )
    glyphs = (
        natural_bundle.glyph,
        sharp_minus_31.glyph,
    )
    texts = (
        natural_minus_14.text,
        sharp_minus_31.text,
    )
    return temperament, acc_system, tonality, accidentals, composites, glyphs, texts


def _emit_three_entity_doricolib(tmp_path: pathlib.Path) -> bytes:
    out = tmp_path / "test.doricolib"
    t, a, ts, accs, comps, gs, txs = _build_three_template_entities()
    write(out, temperament=t, accidental_system=a, tonality_system=ts,
          accidentals=accs, composites=comps, glyphs=gs, texts=txs)
    return out.read_bytes()


def test_xml_declaration_uses_lowercase_utf8(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path)
    # First line must be <?xml version='1.0' encoding='utf-8'?> (or with double quotes).
    first_line = body.split(b"\n", 1)[0]
    assert b"encoding=" in first_line
    assert b"utf-8" in first_line.lower()
    # Lowercase utf-8, not UTF-8.
    assert b"UTF-8" not in first_line


def test_root_is_kscorelibrary(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path)
    assert b"<kScoreLibrary>" in body


def test_fileversion_is_first_child(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    assert f"<fileVersion>{FILE_VERSION}</fileVersion>" in body
    # fileVersion must appear before the first section element.
    fv_idx = body.index("<fileVersion>")
    temperaments_idx = body.index("<temperaments>")
    assert fv_idx < temperaments_idx


def test_sections_appear_in_canonical_order(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    positions = []
    for section_name, _ in SECTION_ORDER:
        idx = body.find(f"<{section_name}>")
        assert idx != -1, f"section {section_name!r} not found"
        positions.append(idx)
    assert positions == sorted(positions), \
        f"sections out of canonical order: {positions}"


def test_indentation_uses_tabs(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path)
    # At least 50 lines should start with one or more tabs.
    tab_indented_lines = sum(1 for line in body.split(b"\n") if line.startswith(b"\t"))
    assert tab_indented_lines > 50, f"too few tab-indented lines: {tab_indented_lines}"


def test_indentation_does_not_use_spaces(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path)
    # No line should start with two or more spaces (which would be space-indent).
    for line in body.split(b"\n"):
        assert not line.startswith(b"  "), f"space-indented line: {line!r}"


def test_lowercase_booleans(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    # isSmufl, showCautionaryNaturals appear; both must be lowercase.
    assert "<isSmufl>true</isSmufl>" in body
    assert "<showCautionaryNaturals>false</showCautionaryNaturals>" in body
    assert "<isSmufl>True" not in body
    assert "<isSmufl>False" not in body


def test_uppercase_hex_codepoints(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    # accidentalNatural=0xE261 and accidentalSharp=0xE262 must appear.
    assert "<codePoint>0xE261</codePoint>" in body
    assert "<codePoint>0xE262</codePoint>" in body
    # Lowercase hex must NOT appear.
    assert "<codePoint>0xe261" not in body
    assert "<codePoint>0xe262" not in body


def test_six_decimal_scale_literals(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    assert "<xScale>100.000000</xScale>" in body
    assert "<yScale>100.000000</yScale>" in body


def test_raw_pitch_delta_no_reduction(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    # Raw template values: 0/24 (Natural), -14/1200 (-14), 69/1200 (#-31).
    assert "<pitchDeltaFromNatural>0/24</pitchDeltaFromNatural>" in body
    assert "<pitchDeltaFromNatural>-14/1200</pitchDeltaFromNatural>" in body
    assert "<pitchDeltaFromNatural>69/1200</pitchDeltaFromNatural>" in body


def test_cut_out_tuples_have_space_after_comma(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    # Most cutOuts are (0, 0).
    assert "<cutOutNW>(0, 0)</cutOutNW>" in body
    # Natural's cutOutNE is (0.192, 2.116) per template line 70.
    assert "<cutOutNE>(0.192, 2.116)</cutOutNE>" in body
    assert "<cutOutSW>(0.476, 0.512)</cutOutSW>" in body
    # Comma-without-space must NOT appear in any tuple.
    assert not re.search(r"\(\d[^)]*,\d", body), "tuple without space after comma"


def test_id_list_has_comma_space_separator(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    # accidentalDefinitionIDs is the only place this appears in this fixture.
    m = re.search(r"<accidentalDefinitionIDs>([^<]+)</accidentalDefinitionIDs>", body)
    assert m, "accidentalDefinitionIDs element not found"
    ids_text = m.group(1)
    # Three IDs in our fixture, joined by ", ".
    assert ids_text.count(", ") == 2, f"expected exactly 2 ', ' separators in {ids_text!r}"
    # No comma-without-space.
    assert not re.search(r",[^ ]", ids_text)


def test_self_closing_empty_arrays(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    # scalingRules is always empty → self-closing.
    assert '<scalingRules array="true"/>' in body
    # Class A and Class C composites have empty relativeAttachments → self-closing.
    assert '<relativeAttachments array="true"/>' in body
    # Empty <accidentals array="true"/> in the customKeySignature stub.
    assert '<accidentals array="true"/>' in body


def test_self_closing_parent_entity_id(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    # Most parentEntityID elements are self-closing.
    assert "<parentEntityID/>" in body
    # accidentalNatural's parentEntityID is non-empty (factory inheritance).
    assert "<parentEntityID>glyph.accidentalNatural</parentEntityID>" in body


def test_class_b_attachment_offsets_in_emitted_xml(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    # The relativeAttachment for #-31 has xOffset=-8, yOffset=-12.
    # Search for the pattern within a relativeAttachment block.
    m = re.search(
        r"<relativeAttachment>\s*<xOffset>(-?\d+)</xOffset>\s*<yOffset>(-?\d+)</yOffset>",
        body,
    )
    assert m, "relativeAttachment block not found"
    assert m.group(1) == "-8"
    assert m.group(2) == "-12"


def test_class_c_text_offsets_in_emitted_xml(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    # Class C composite has a single text component with xOffset=18, yOffset=-12.
    # Look for the pattern: <componentType>kText</componentType>\s*<xOffset>18</xOffset>\s*<yOffset>-12</yOffset>
    assert re.search(
        r"<componentType>kText</componentType>\s*<xOffset>18</xOffset>\s*<yOffset>-12</yOffset>",
        body,
    ), "Class C text component (18, -12) not found"


def test_component_instance_id_has_dot_zero_suffix(tmp_path: pathlib.Path) -> None:
    body = _emit_three_entity_doricolib(tmp_path).decode()
    # Every componentInstanceId must end with .0 (matches componentInstance=0).
    for m in re.finditer(r"<componentInstanceId>([^<]+)</componentInstanceId>", body):
        assert m.group(1).endswith(".0"), \
            f"componentInstanceId missing .N suffix: {m.group(1)}"


def test_xmllint_well_formed(tmp_path: pathlib.Path) -> None:
    """xmllint --noout proves well-formedness (necessary, not sufficient)."""
    import shutil
    import subprocess
    if not shutil.which("xmllint"):
        import pytest
        pytest.skip("xmllint not installed; install via 'brew install libxml2' on macOS")

    out = tmp_path / "test.doricolib"
    t, a, ts, accs, comps, gs, txs = _build_three_template_entities()
    write(out, temperament=t, accidental_system=a, tonality_system=ts,
          accidentals=accs, composites=comps, glyphs=gs, texts=txs)
    result = subprocess.run(
        ["xmllint", "--noout", str(out)],
        capture_output=True,
    )
    assert result.returncode == 0, f"xmllint failed: {result.stderr.decode()}"


def test_two_runs_produce_byte_identical_output(tmp_path: pathlib.Path) -> None:
    """Smoke test for determinism (full file-level diff is in Plan 03)."""
    out_a = tmp_path / "a.doricolib"
    out_b = tmp_path / "b.doricolib"
    for path in (out_a, out_b):
        t, a, ts, accs, comps, gs, txs = _build_three_template_entities()
        write(path, temperament=t, accidental_system=a, tonality_system=ts,
              accidentals=accs, composites=comps, glyphs=gs, texts=txs)
    assert out_a.read_bytes() == out_b.read_bytes()
