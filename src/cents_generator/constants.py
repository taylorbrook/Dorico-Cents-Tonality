"""Project-wide constants for the cents Dorico tonality-system generator.

Centralizing magic numbers and identifiers here makes them grep-able and
prevents stringly-typed drift across modules. Anything emitted into the
.doricolib that has a single canonical value lives here.
"""
from __future__ import annotations


# ----------------------------------------------------------------------------
# File format
# ----------------------------------------------------------------------------
# Dorico Pro 6.x library format. Will not load on Dorico 5 or earlier.
# Verified in TonalitySystemStartTemplate.doricolib line 3.
FILE_VERSION: str = "1.1450"


# ----------------------------------------------------------------------------
# SMuFL Standard Accidentals (12-EDO) — codepoints stable across SMuFL 1.0–1.18.
# Use base codepoints; let Dorico's optical scaling handle small-stave variants.
# ----------------------------------------------------------------------------
SMUFL_FLAT: int    = 0xE260
SMUFL_NATURAL: int = 0xE261
SMUFL_SHARP: int   = 0xE262


# ----------------------------------------------------------------------------
# Font style references — these are Dorico style aliases, not concrete font
# families. Resolves to Bravura (music) and the user's text font (text).
# ----------------------------------------------------------------------------
FONT_DEFAULT_MUSIC: str = "font.defaultmusic"
FONT_DEFAULT_TEXT: str  = "font.defaulttext"


# ----------------------------------------------------------------------------
# EntityID kind prefixes. Dorico stores entityIDs as '<kind>.user.<32hex>'.
# NOTE: 'tonalitysystem' has no hyphen and no dot between 'tonality' and
# 'system' — this is a schema quirk verified in the template (line 80).
# ----------------------------------------------------------------------------
KIND_TEMPERAMENT: str       = "temperament-definition"
KIND_ACCIDENTAL_SYSTEM: str = "accidental-system"
KIND_ACCIDENTAL: str        = "accidental"
KIND_TONALITY_SYSTEM: str   = "tonalitysystem"
KIND_TEXT: str              = "text"
KIND_GLYPH: str             = "glyph"
KIND_COMPOSITE: str         = "comp"


# ----------------------------------------------------------------------------
# 12-EDO temperament: standard relativeDiatonicDivisions in cents.
# A→B=200, B→C=100, C→D=200, D→E=200, E→F=100, F→G=200, G→A=200; sum = 1200.
# Verified in template lines 13-19.
# ----------------------------------------------------------------------------
TEMPERAMENT_12EDO_DIVISIONS: tuple[int, int, int, int, int, int, int] = (
    200, 100, 200, 200, 100, 200, 200,
)


# ----------------------------------------------------------------------------
# Canonical section emission order — DO NOT REORDER.
#
# This is Dorico's own canonical export order, NOT alphabetical and NOT
# dependency-ordered. Forward references (e.g. accidentalDefinitions in
# section 3 referencing compositeDefinitions in section 7) ARE intentional
# and DO work — Dorico's parser does two-pass entityID resolution. Do not
# topologically sort to "fix" forward references — see PITFALLS.md Pitfall 13.
#
# Each entry is (XML wrapper section name, inner entity element name).
# ----------------------------------------------------------------------------
SECTION_ORDER: tuple[tuple[str, str], ...] = (
    ("temperaments",              "TemperamentDefinition"),
    ("accidentalSystems",         "AccidentalSystem"),
    ("accidentalDefinitions",     "AccidentalDefinition"),
    ("tonalitySystemDefinitions", "TonalitySystemDefinition"),
    ("textDefinitions",           "TextPrimitiveEntityDefinition"),
    ("glyphDefinitions",          "GlyphPrimitiveEntityDefinition"),
    ("compositeDefinitions",      "CompositeDefinition"),
)
