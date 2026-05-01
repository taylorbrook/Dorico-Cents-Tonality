"""Byte-faithful XML emission for cents.doricolib.

This is the ONLY module that knows about Dorico's XML quirks. Every
formatting decision (tabs, lowercase booleans, raw n/d rationals, six-decimal
float strings, comma-space ID lists, capital-X uppercase hex codepoints,
self-closing empty arrays, '.0' componentInstanceId suffix, utf-8 lowercase
encoding declaration, LF line endings) lives here.

Forward references in section emission are INTENTIONAL — see SECTION_ORDER
in constants.py. Dorico's parser is two-pass and resolves entityIDs across
the whole document. Do NOT topologically sort sections.
"""
from __future__ import annotations

import pathlib
import xml.etree.ElementTree as ET

from .constants import FILE_VERSION, SECTION_ORDER, TEMPERAMENT_12EDO_DIVISIONS  # noqa: F401  (TEMPERAMENT_12EDO_DIVISIONS used by Plan 03 callers; kept here for re-export visibility if Plan 03 imports from emit)
from .entities import (
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

# ----------------------------------------------------------------------------
# Private formatters — every quirky value funnels through these
# ----------------------------------------------------------------------------
def _fmt_tuple(x: float, y: float) -> str:
    """'(0, 0)' or '(0.192, 2.116)' — WITH space after comma.

    Integers emit without a decimal point (matches template's '(0, 0)');
    non-integer floats emit with whatever Python's str() produces (matches
    template's '(0.192, 2.116)').
    """
    def _f(v: float) -> str:
        return str(int(v)) if float(v).is_integer() else str(v)
    return f"({_f(x)}, {_f(y)})"


def _fmt_id_list(ids: tuple[str, ...] | list[str]) -> str:
    """'id1, id2, id3' — comma-space joined."""
    return ", ".join(ids)


def _fmt_bool(b: bool) -> str:
    """'true' or 'false' lowercase."""
    return "true" if b else "false"


def _fmt_hex_codepoint(cp: int) -> str:
    """'0xE262' — capital X, uppercase hex digits, 4-digit padded."""
    return f"0x{cp:04X}"


SCALE_LITERAL: str = "100.000000"
"""Literal six-decimal scale string. Matches template; locale-independent."""


# ----------------------------------------------------------------------------
# Element builders — one per dataclass, plus structural helpers
# ----------------------------------------------------------------------------
def _add_text(parent: ET.Element, tag: str, value: str) -> ET.Element:
    """Add a child element with text content. ElementTree handles XML escaping."""
    child = ET.SubElement(parent, tag)
    child.text = value
    return child


def _add_empty(parent: ET.Element, tag: str) -> ET.Element:
    """Add a self-closing empty child (e.g. <parentEntityID/>)."""
    return ET.SubElement(parent, tag)


def _add_empty_array(parent: ET.Element, tag: str) -> ET.Element:
    """Add a self-closing empty array (e.g. <scalingRules array="true"/>).

    CRITICAL for Pitfall 3 (silent text-component drop) — Dorico expects
    these to be present-and-empty, NOT omitted.
    """
    return ET.SubElement(parent, tag, attrib={"array": "true"})


def _add_parent_entity_id(parent: ET.Element, value: str) -> ET.Element:
    """Add <parentEntityID/> (self-closing) or <parentEntityID>...</parentEntityID>."""
    if value:
        return _add_text(parent, "parentEntityID", value)
    return _add_empty(parent, "parentEntityID")


def _build_temperament(t: TemperamentDef) -> ET.Element:
    el = ET.Element("TemperamentDefinition")
    _add_text(el, "name", t.name)
    _add_text(el, "entityID", t.entity_id)
    _add_parent_entity_id(el, t.parent_entity_id)
    _add_text(el, "inheritanceMask", str(t.inheritance_mask))
    _add_text(el, "precedence", str(t.precedence))
    rdd = ET.SubElement(el, "relativeDiatonicDivisions")
    _add_text(rdd, "noteAtoB", str(t.note_a_to_b))
    _add_text(rdd, "noteBtoC", str(t.note_b_to_c))
    _add_text(rdd, "noteCtoD", str(t.note_c_to_d))
    _add_text(rdd, "noteDtoE", str(t.note_d_to_e))
    _add_text(rdd, "noteEtoF", str(t.note_e_to_f))
    _add_text(rdd, "noteFtoG", str(t.note_f_to_g))
    _add_text(rdd, "noteGtoA", str(t.note_g_to_a))
    return el


def _build_accidental_system(a: AccidentalSystemDef) -> ET.Element:
    el = ET.Element("AccidentalSystem")
    _add_text(el, "name", a.name)
    _add_text(el, "entityID", a.entity_id)
    _add_parent_entity_id(el, a.parent_entity_id)
    _add_text(el, "inheritanceMask", str(a.inheritance_mask))
    _add_text(el, "accidentalDefinitionIDs", _fmt_id_list(a.accidental_definition_ids))
    _add_text(el, "precedence", str(a.precedence))
    return el


def _build_accidental(a: AccidentalDef) -> ET.Element:
    el = ET.Element("AccidentalDefinition")
    _add_text(el, "name", a.name)
    _add_text(el, "entityID", a.entity_id)
    _add_parent_entity_id(el, a.parent_entity_id)
    _add_text(el, "inheritanceMask", str(a.inheritance_mask))
    _add_text(el, "compositeID", a.composite_id)
    _add_text(el, "pitchDeltaFromNatural", a.pitch_delta_from_natural)
    _add_text(el, "cutOutNW", _fmt_tuple(*a.cut_out_nw))
    _add_text(el, "cutOutNE", _fmt_tuple(*a.cut_out_ne))
    _add_text(el, "cutOutSE", _fmt_tuple(*a.cut_out_se))
    _add_text(el, "cutOutSW", _fmt_tuple(*a.cut_out_sw))
    return el


def _build_tonality_system(t: TonalitySystemDef) -> ET.Element:
    """Build a TonalitySystemDefinition with the fixed customKeySignatures stub.

    The stub is verbatim from template lines 85-101 (one customKeySignature
    with empty accidentals array, kKeySigCustom on root note C).
    """
    el = ET.Element("TonalitySystemDefinition")
    _add_text(el, "name", t.name)
    _add_text(el, "entityID", t.entity_id)
    _add_parent_entity_id(el, t.parent_entity_id)
    _add_text(el, "inheritanceMask", str(t.inheritance_mask))
    _add_text(el, "temperamentDefinition", t.temperament_definition_id)
    _add_text(el, "accidentalSystem", t.accidental_system_id)

    # customKeySignatures fixed boilerplate stub — verbatim from template.
    cks = ET.SubElement(el, "customKeySignatures", attrib={"array": "true"})
    cks_one = ET.SubElement(cks, "customKeySignature")
    _add_text(cks_one, "name", "New key signature")
    _add_empty(cks_one, "clefID")
    ksig = ET.SubElement(cks_one, "keySignature")
    _add_text(ksig, "showCautionaryNaturals", _fmt_bool(False))
    ksig_root_outer = ET.SubElement(ksig, "root")
    _add_text(ksig_root_outer, "tonalityType", "kKeySigCustom")
    ksig_root_inner = ET.SubElement(ksig_root_outer, "root")
    _add_text(ksig_root_inner, "noteName", "C")
    _add_empty(ksig_root_inner, "accidentalID")
    _add_empty_array(ksig, "accidentals")
    return el


def _build_text(t: TextDef) -> ET.Element:
    el = ET.Element("TextPrimitiveEntityDefinition")
    _add_text(el, "name", t.name)
    _add_text(el, "entityID", t.entity_id)
    _add_parent_entity_id(el, t.parent_entity_id)
    _add_text(el, "inheritanceMask", str(t.inheritance_mask))
    _add_text(el, "fontStyle", t.font_style)
    _add_text(el, "text", t.text)
    return el


def _build_glyph(g: GlyphDef) -> ET.Element:
    el = ET.Element("GlyphPrimitiveEntityDefinition")
    _add_text(el, "name", g.name)
    _add_text(el, "entityID", g.entity_id)
    _add_parent_entity_id(el, g.parent_entity_id)
    _add_text(el, "inheritanceMask", str(g.inheritance_mask))
    _add_text(el, "codePoint", _fmt_hex_codepoint(g.code_point))
    _add_text(el, "isSmufl", _fmt_bool(g.is_smufl))
    if g.alternate_for_glyph:
        _add_text(el, "alternateForGlyph", g.alternate_for_glyph)
    else:
        _add_empty(el, "alternateForGlyph")
    _add_text(el, "fontStyle", g.font_style)
    _add_text(el, "pointSize", str(g.point_size))
    _add_text(el, "rotation", str(g.rotation))
    _add_text(el, "colour", g.colour)
    return el


def _build_component(c: Component) -> ET.Element:
    el = ET.Element("component")
    _add_text(el, "componentId", c.component_id)
    _add_text(el, "componentType", c.component_type)
    _add_text(el, "xOffset", str(c.x_offset))
    _add_text(el, "yOffset", str(c.y_offset))
    # Six-decimal scale literal — locale-independent.
    _add_text(el, "xScale", SCALE_LITERAL if c.x_scale == 100.0 else f"{c.x_scale:.6f}")
    _add_text(el, "yScale", SCALE_LITERAL if c.y_scale == 100.0 else f"{c.y_scale:.6f}")
    _add_text(el, "zOrder", str(c.z_order))
    _add_text(el, "maxOpticalScale", str(c.max_optical_scale))
    _add_text(el, "componentInstance", str(c.component_instance))
    _add_text(el, "colour", c.colour)
    return el


def _build_relative_attachment(r: RelativeAttachment) -> ET.Element:
    el = ET.Element("relativeAttachment")
    _add_text(el, "xOffset", str(r.x_offset))
    _add_text(el, "yOffset", str(r.y_offset))
    p1 = ET.SubElement(el, "componentRelativePair1")
    _add_text(p1, "componentInstanceId", r.pair1_component_instance_id)
    _add_text(p1, "componentAttachmentPoint", r.pair1_attachment_point)
    p2 = ET.SubElement(el, "componentRelativePair2")
    _add_text(p2, "componentInstanceId", r.pair2_component_instance_id)
    _add_text(p2, "componentAttachmentPoint", r.pair2_attachment_point)
    return el


def _build_composite(c: CompositeDef) -> ET.Element:
    el = ET.Element("CompositeDefinition")
    _add_text(el, "name", c.name)
    _add_text(el, "entityID", c.entity_id)
    _add_parent_entity_id(el, c.parent_entity_id)
    _add_text(el, "inheritanceMask", str(c.inheritance_mask))
    _add_text(el, "category", c.category)

    # components is always non-empty for our use case, but emit the array
    # wrapper consistently (template style).
    comps = ET.SubElement(el, "components", attrib={"array": "true"})
    for comp in c.components:
        comps.append(_build_component(comp))

    # relativeAttachments is empty for Class A and C; populated for Class B.
    # CRITICAL: must always emit (Pitfall 3), self-closing when empty.
    if c.relative_attachments:
        attachments = ET.SubElement(el, "relativeAttachments", attrib={"array": "true"})
        for att in c.relative_attachments:
            attachments.append(_build_relative_attachment(att))
    else:
        _add_empty_array(el, "relativeAttachments")

    # scalingRules is always empty for accidentals — always self-closing.
    _add_empty_array(el, "scalingRules")
    return el


# ----------------------------------------------------------------------------
# Public API: write a complete cents.doricolib
# ----------------------------------------------------------------------------
def write(
    path: pathlib.Path,
    *,
    temperament: TemperamentDef,
    accidental_system: AccidentalSystemDef,
    tonality_system: TonalitySystemDef,
    accidentals: tuple[AccidentalDef, ...],
    composites: tuple[CompositeDef, ...],
    glyphs: tuple[GlyphDef, ...],
    texts: tuple[TextDef, ...],
) -> None:
    """Serialize the complete library and write to `path`.

    Caller (orchestrator) is responsible for ordering within each section.
    Sections are emitted in SECTION_ORDER (canonical, do not reorder).
    """
    root = ET.Element("kScoreLibrary")
    _add_text(root, "fileVersion", FILE_VERSION)

    # Map section name → entity element name → list of built ET.Elements.
    # We pre-build each section's list to keep the SECTION_ORDER iteration
    # purely structural.
    section_payloads: dict[str, list[ET.Element]] = {
        "temperaments":              [_build_temperament(temperament)],
        "accidentalSystems":         [_build_accidental_system(accidental_system)],
        "accidentalDefinitions":     [_build_accidental(a) for a in accidentals],
        "tonalitySystemDefinitions": [_build_tonality_system(tonality_system)],
        "textDefinitions":           [_build_text(t) for t in texts],
        "glyphDefinitions":          [_build_glyph(g) for g in glyphs],
        "compositeDefinitions":      [_build_composite(c) for c in composites],
    }

    for section_name, _entity_tag in SECTION_ORDER:
        section_el = ET.SubElement(root, section_name)
        entities_wrapper = ET.SubElement(section_el, "entities", attrib={"array": "true"})
        for entity_el in section_payloads[section_name]:
            entities_wrapper.append(entity_el)

    # Tab indent (Python 3.9+). Produces '\t'-prefixed lines.
    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)

    # Serialize to bytes with utf-8 lowercase declaration. Use short_empty_elements
    # so empty elements (parentEntityID, scalingRules array=true, etc.) self-close.
    body = ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    )

    # Byte-fidelity post-process: Python's ElementTree emits self-closing tags
    # as '<tag />' (with a space before '/>'). The Dorico template uses the
    # no-space form ('<tag/>' and '<tag attr="v"/>'). Both are XML-equivalent,
    # but Plan 03's round-trip diff requires byte equality. Replace ' />' with
    # '/>' globally — safe because the only place ' />' can occur in valid XML
    # is at the end of a self-closing tag (attribute values are quoted; text
    # nodes can contain ' />' literally only via &#62; escaping, which we don't
    # use anywhere in this fixture).
    body = body.replace(b" />", b"/>")

    # Force LF line endings (avoid Windows CRLF surprises). Write in binary.
    # Append a trailing newline to match the template (template ends with '\n').
    if not body.endswith(b"\n"):
        body = body + b"\n"
    path.write_bytes(body)
