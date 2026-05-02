"""Byte-faithful round-trip test against TonalitySystemStartTemplate.doricolib.

SCH-05: The generator must re-emit the three template entities (Natural,
-14, #-31) byte-for-byte against the working template, modulo entityIDs.

Strategy: normalize every '<kind>.user.<32hex>' in BOTH files to a
deterministic per-kind sequence ('temperament-definition.user.<auto-0>',
'accidental.user.<auto-0>', 'accidental.user.<auto-1>', ...). Since the
first appearance of a given UUID in document order is the same logical
entity in both files (we structured the orchestrator's output ordering to
match the template), the normalized strings should match byte-for-byte.

If this test fails:
- Run a manual diff between the normalized files (saved to /tmp on test
  failure for inspection) to see the structural drift.
- Cross-reference STACK.md / PITFALLS Pitfall 7 for which formatter is wrong.

If TonalitySystemStartTemplate.doricolib is absent, the round-trip tests
that require it skip cleanly so CI without the user's local file still runs.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

import pytest

from cents_generator.main import run

REPO_ROOT = pathlib.Path(__file__).parent.parent
TEMPLATE = REPO_ROOT / "TonalitySystemStartTemplate.doricolib"

ENTITY_ID_RE = re.compile(r"([a-z-]+)\.user\.([0-9a-f]{32})")


def _normalize_entity_ids(content: str) -> str:
    """Replace each '<kind>.user.<32hex>' with '<kind>.user.<auto-N>'.

    N is the per-kind sequential index of first appearance. Subsequent
    occurrences of the same (kind, hex) get the same N. Different (kind, hex)
    pairs get distinct Ns within their kind's namespace.

    This makes byte-comparison robust against UUID differences while still
    catching structural drift (different entity counts, reordered references,
    cross-kind reference confusion).
    """
    # Map (kind, hex) → assigned canonical token, in first-appearance order.
    seen: dict[tuple[str, str], str] = {}
    per_kind_counter: dict[str, int] = {}

    def _replace(match: re.Match[str]) -> str:
        kind = match.group(1)
        hex_part = match.group(2)
        key = (kind, hex_part)
        if key not in seen:
            idx = per_kind_counter.get(kind, 0)
            seen[key] = f"{kind}.user.<auto-{idx}>"
            per_kind_counter[kind] = idx + 1
        return seen[key]

    return ENTITY_ID_RE.sub(_replace, content)


def _require_template() -> None:
    """Skip the test cleanly if the user's template file is absent.

    The round-trip target is a local artifact (per CLAUDE.md it is intentionally
    not checked into git). On a fresh CI clone or another developer's machine
    without the file, the round-trip tests should skip rather than fail."""
    if not TEMPLATE.exists():
        pytest.skip(
            f"TonalitySystemStartTemplate.doricolib not found at {TEMPLATE}; "
            "round-trip cannot be exercised without the user's local template."
        )


def test_template_exists_or_skip() -> None:
    """Sanity record: either the template is present (and other tests run) or
    we skip the round-trip suite. This test is informational — it never fails."""
    if TEMPLATE.exists():
        size = TEMPLATE.stat().st_size
        assert size > 0, f"template at {TEMPLATE} is empty"
    else:
        pytest.skip(f"TonalitySystemStartTemplate.doricolib absent at {TEMPLATE}")


def test_round_trip_byte_identical_modulo_entity_ids(tmp_path: pathlib.Path) -> None:
    """The generator's output, with entityIDs normalized, must equal the
    template's bytes with entityIDs normalized. Anything else is structural
    drift — see PITFALLS Pitfall 7."""
    _require_template()
    out_path = tmp_path / "generated.doricolib"
    run(out_path, mode="template")

    generated_bytes = out_path.read_bytes()
    template_bytes = TEMPLATE.read_bytes()

    # Decode as UTF-8 for normalization. Both files claim utf-8 in their declaration.
    generated_str = generated_bytes.decode("utf-8")
    template_str = template_bytes.decode("utf-8")

    normalized_generated = _normalize_entity_ids(generated_str)
    normalized_template = _normalize_entity_ids(template_str)

    if normalized_generated != normalized_template:
        # Save normalized versions for human inspection.
        (tmp_path / "_normalized_generated.txt").write_text(normalized_generated)
        (tmp_path / "_normalized_template.txt").write_text(normalized_template)
        shutil.copy(tmp_path / "_normalized_generated.txt", "/tmp/_normalized_generated.txt")
        shutil.copy(tmp_path / "_normalized_template.txt", "/tmp/_normalized_template.txt")

        # Show first divergent line for diagnosis.
        gen_lines = normalized_generated.splitlines()
        tpl_lines = normalized_template.splitlines()
        divergence_line: tuple[int, str, str] | None = None
        for i, (gl, tl) in enumerate(zip(gen_lines, tpl_lines), start=1):
            if gl != tl:
                divergence_line = (i, gl, tl)
                break
        if divergence_line is None and len(gen_lines) != len(tpl_lines):
            divergence_line = (
                min(len(gen_lines), len(tpl_lines)) + 1,
                f"<EOF in {'gen' if len(gen_lines) < len(tpl_lines) else 'tpl'}>",
                f"line count: gen={len(gen_lines)}, tpl={len(tpl_lines)}",
            )

        line_no = divergence_line[0] if divergence_line else "?"
        gen_repr = repr(divergence_line[1]) if divergence_line else "?"
        tpl_repr = repr(divergence_line[2]) if divergence_line else "?"
        pytest.fail(
            f"Round-trip diverged.\n"
            f"  Generated normalized:  /tmp/_normalized_generated.txt ({len(normalized_generated)} bytes)\n"
            f"  Template normalized:   /tmp/_normalized_template.txt  ({len(normalized_template)} bytes)\n"
            f"  First divergence at line {line_no}:\n"
            f"    gen: {gen_repr}\n"
            f"    tpl: {tpl_repr}\n"
            f"  Run: diff /tmp/_normalized_template.txt /tmp/_normalized_generated.txt"
        )


def test_round_trip_section_ordering_matches_template(tmp_path: pathlib.Path) -> None:
    """Sanity check: even if normalization fails, sections must appear in the
    same order in both files."""
    _require_template()
    out_path = tmp_path / "generated.doricolib"
    run(out_path, mode="template")

    generated_str = out_path.read_text("utf-8")
    template_str = TEMPLATE.read_text("utf-8")

    section_tags = [
        "<temperaments>",
        "<accidentalSystems>",
        "<accidentalDefinitions>",
        "<tonalitySystemDefinitions>",
        "<textDefinitions>",
        "<glyphDefinitions>",
        "<compositeDefinitions>",
    ]
    gen_positions = [generated_str.index(tag) for tag in section_tags]
    tpl_positions = [template_str.index(tag) for tag in section_tags]
    assert gen_positions == sorted(gen_positions), \
        f"generated sections out of order: {dict(zip(section_tags, gen_positions))}"
    assert tpl_positions == sorted(tpl_positions), \
        f"template sections out of order: {dict(zip(section_tags, tpl_positions))}"


def test_round_trip_xmllint_well_formed(tmp_path: pathlib.Path) -> None:
    """xmllint --noout proves XML well-formedness. Falls back to Python's
    ElementTree.parse() when xmllint is unavailable on the runner — both
    are acceptable proxies for 'this file parses cleanly'."""
    out_path = tmp_path / "generated.doricolib"
    run(out_path, mode="template")
    if shutil.which("xmllint"):
        result = subprocess.run(
            ["xmllint", "--noout", str(out_path)],
            capture_output=True,
        )
        assert result.returncode == 0, f"xmllint failed: {result.stderr.decode()}"
    else:
        # Python ET fallback: parse the file. If it raises, the file is malformed.
        try:
            ET.parse(out_path)
        except ET.ParseError as e:  # pragma: no cover - we're in fallback path
            pytest.fail(f"Python ElementTree.parse() failed (xmllint absent): {e}")


def test_round_trip_entity_count_matches_template(tmp_path: pathlib.Path) -> None:
    """The template has exactly: 1 Temperament, 1 AccidentalSystem, 3
    AccidentalDefinitions, 1 TonalitySystem, 2 Texts, 2 Glyphs, 3 Composites."""
    out_path = tmp_path / "generated.doricolib"
    run(out_path, mode="template")
    body = out_path.read_text("utf-8")

    assert body.count("<TemperamentDefinition>") == 1
    assert body.count("<AccidentalSystem>") == 1
    assert body.count("<AccidentalDefinition>") == 3
    assert body.count("<TonalitySystemDefinition>") == 1
    assert body.count("<TextPrimitiveEntityDefinition>") == 2
    assert body.count("<GlyphPrimitiveEntityDefinition>") == 2
    assert body.count("<CompositeDefinition>") == 3


def test_round_trip_accidental_names_match_template(tmp_path: pathlib.Path) -> None:
    """Verify the three accidental names appear verbatim — these are the
    user-visible labels that traveled forward."""
    out_path = tmp_path / "generated.doricolib"
    run(out_path, mode="template")
    body = out_path.read_text("utf-8")

    assert "<name>Natural</name>" in body
    assert "<name>-14</name>" in body
    assert "<name>#-31</name>" in body
    assert "<name>Psychography</name>" in body  # tonality system name


def test_round_trip_pitch_deltas_match_template(tmp_path: pathlib.Path) -> None:
    """Critical: pitch deltas must be the template's literal strings."""
    out_path = tmp_path / "generated.doricolib"
    run(out_path, mode="template")
    body = out_path.read_text("utf-8")

    assert "<pitchDeltaFromNatural>0/24</pitchDeltaFromNatural>" in body
    assert "<pitchDeltaFromNatural>-14/1200</pitchDeltaFromNatural>" in body
    assert "<pitchDeltaFromNatural>69/1200</pitchDeltaFromNatural>" in body


def test_round_trip_file_version_is_1_1450(tmp_path: pathlib.Path) -> None:
    """fileVersion must be exactly 1.1450 (Dorico Pro 6.x library format).

    Pitfall 4 mitigation — wrong fileVersion causes Dorico to reject the file
    or strip data on import."""
    out_path = tmp_path / "generated.doricolib"
    run(out_path, mode="template")
    body = out_path.read_text("utf-8")
    assert "<fileVersion>1.1450</fileVersion>" in body
