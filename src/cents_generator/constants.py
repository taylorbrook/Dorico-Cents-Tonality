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


# ----------------------------------------------------------------------------
# Cents-mode key strings. THESE LOCK FOREVER (D-05, PITFALLS.md §"Pitfall 6").
# ----------------------------------------------------------------------------
# The strings below are the second argument to entity_id(kind, key). Renaming
# any of them creates duplicate entityIDs on user re-import — there is no
# clean migration path. If a future major version requires renaming, document
# it as a one-time manual cleanup in the README; do NOT rotate these
# constants in code.
#
# Phase 1's '-template'-suffixed keys live in main.py and are distinct from
# these — both sets coexist in the same PROJECT_NAMESPACE because they
# produce different entityIDs.
# ----------------------------------------------------------------------------
KEY_TEMPERAMENT_12EDO_CENTS: str = "12-edo"
KEY_ACC_SYSTEM_CENTS: str        = "cents"
KEY_TONALITY_CENTS: str          = "cents"


# ----------------------------------------------------------------------------
# cents-naturals variant keys. THESE LOCK FOREVER once shipped (same D-05
# rationale as KEY_*_CENTS above). The variant tonality re-uses the cents-
# mode 12-EDO temperament entityID (KEY_TEMPERAMENT_12EDO_CENTS) — there is
# exactly one 12-EDO temperament — but uses distinct accidental-system and
# tonality keys so the two libraries coexist in Dorico's picker without
# entityID collision.
# ----------------------------------------------------------------------------
KEY_TONALITY_CENTS_NATURALS: str   = "cents-naturals"
KEY_ACC_SYSTEM_CENTS_NATURALS: str = "cents-naturals"


# ----------------------------------------------------------------------------
# Cents-mode sweep range: signed cent deviations from -99 to +99, excluding 0.
# The zero-deviation case is emitted via bare-base accidentals (Sharp/Flat/
# Natural) once per base, NOT iterated as cents=0. See CONTEXT.md D-05 and
# main.py::build_cents_full_sweep().
# ----------------------------------------------------------------------------
CENTS_RANGE_NONZERO: tuple[int, ...] = tuple(c for c in range(-99, 100) if c != 0)
