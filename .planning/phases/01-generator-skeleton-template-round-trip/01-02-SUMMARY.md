---
phase: 01-generator-skeleton-template-round-trip
plan: 02
subsystem: generator-emission
tags: [python, stdlib, xml-elementtree, byte-faithful, three-class-composite, dorico, smufl]

# Dependency graph
requires:
  - "Plan 01-01: PROJECT_NAMESPACE, entity_id(), constants (FILE_VERSION, SMUFL_*, FONT_*, KIND_*, SECTION_ORDER), 9 frozen+slots dataclasses"
provides:
  - "compose.AccidentalBundle frozen+slots dataclass (accidental, composite, glyph|None, text|None) with .entities helper for orchestrator dedup"
  - "compose.build_class_a(base, *, accidental_name, accidental_key, composite_name, composite_key, pitch_delta_from_natural, cut_out_*=...) — glyph-only zero-deviation"
  - "compose.build_class_b(base, *, accidental_name, accidental_key, composite_name, composite_key, label_text, pitch_delta_from_natural) — sharp/flat-base + cents text via relativeAttachment kBaselineRight↔kBaselineLeft (-8, -12)"
  - "compose.build_class_c(*, accidental_name, accidental_key, composite_name, composite_key, label_text, pitch_delta_from_natural) — natural-base text-only at (18, -12)"
  - "compose.{CLASS_B_ATTACH_X_OFFSET=-8, CLASS_B_ATTACH_Y_OFFSET=-12, CLASS_C_TEXT_X_OFFSET=18, CLASS_C_TEXT_Y_OFFSET=-12} module-level visual constants"
  - "emit.write(path, *, temperament, accidental_system, tonality_system, accidentals, composites, glyphs, texts) — UTF-8 XML to disk"
  - "emit.{_fmt_tuple, _fmt_id_list, _fmt_bool, _fmt_hex_codepoint, SCALE_LITERAL} byte-faithful formatter helpers"
affects: [01-03-orchestrator, 02-range-expansion, 03-validation]

# Tech tracking
tech-stack:
  added:
    - "xml.etree.ElementTree (stdlib) — verified working under Python 3.14.2"
    - "ET.indent(tree, space='\\t', level=0) for tab indentation"
    - "ET.tostring(root, encoding='utf-8', xml_declaration=True, short_empty_elements=True) for serialization"
  patterns:
    - "Three-class composite dispatcher — pure function per class, returns AccidentalBundle dataclass; orchestrator (Plan 03) composes singletons + dedup"
    - "Byte-fidelity post-process: replace ' />' with '/>' to match template's no-space self-closing style (Python 3.13+ ET added the space; template predates that)"
    - "Element.text-only emission (no string concat) so XML escaping is automatic (Pitfall 16 mitigation)"
    - "String literal SCALE_LITERAL = '100.000000' — locale-independent (Pitfall 14 mitigation)"
    - "_add_empty_array helper always emits <tag array=\"true\"/> rather than omitting (Pitfall 3 mitigation — silent text-component drop)"
    - "TDD RED→GREEN cycle for both compose and emit — failing test commit precedes implementation commit"

key-files:
  created:
    - "src/cents_generator/compose.py"
    - "src/cents_generator/emit.py"
    - "tests/test_compose.py"
    - "tests/test_emit_format.py"
  modified: []

key-decisions:
  - "AccidentalBundle is the sole return type for all three class functions — uniform interface for the orchestrator, even though glyph and text are conditionally None per class"
  - "compose.py surface uses keyword-only arguments after the positional `base` so callers MUST be explicit about names/keys — protects against argument-order bugs at the 597-call scale of Phase 2"
  - "compose.py functions accept pitch_delta_from_natural as a string (caller-supplied) — Phase 1 reproduces the template's '0/24' literal verbatim; Phase 2 introduces the centralized pitch_delta_numerator helper that defeats the off-by-100 trap (Pitfall 1)"
  - "emit.py sees ET's '<tag />' (with space) and post-processes to '<tag/>' (no space) by byte replacement — bounded, safe (no XML-text contains ' />' in our fixtures), required for Plan 03 byte-level diff"
  - "Empty <relativeAttachments array=\"true\"/> ALWAYS emitted (Class A/C) — Pitfall 3 mitigation. _add_empty_array helper centralizes the policy so it cannot be skipped per-call"
  - "Section iteration is driven by SECTION_ORDER constant — emit.py never sorts; comment block warns against topological reordering (forward references are intentional)"

patterns-established:
  - "Per-dataclass element builder functions (_build_temperament, _build_accidental, _build_glyph, etc.) keep emit.py readable — one function per entity type, all wired by the public write() at the end"
  - "Private helpers (_add_text, _add_empty, _add_empty_array, _add_parent_entity_id) make the empty-array vs text-content distinction explicit at every call site"
  - "Format-quirk verification tests one per quirk — readable failure messages, easy to extend in Phase 2 when new entity types appear"

requirements-completed: [SCH-01, SCH-03, SCH-04]

# Metrics
duration: 5.5min
completed: 2026-05-01
---

# Phase 01 Plan 02: Three-class composite dispatcher + byte-faithful XML emission

**Implemented `compose.py` (the three-class dispatcher returning AccidentalBundle for Class A/B/C accidentals) and `emit.py` (the only module that knows about Dorico's XML quirks). Together they reproduce every formatting quirk in the template's three entities and lay the byte-faithful emission foundation Plan 03 will diff against the actual template file.**

## Performance

- **Duration:** 5.5 min (331 s)
- **Started:** 2026-05-01T23:21:21Z
- **Completed:** 2026-05-01T23:26:52Z
- **Tasks:** 2 of 2 complete (each TDD: RED + GREEN commit)
- **Files created:** 4
- **Files modified:** 0

## Accomplishments

- **Three-class composite dispatcher locked in.** `compose.py` exposes `build_class_a`, `build_class_b`, `build_class_c`, all returning `AccidentalBundle(accidental, composite, glyph|None, text|None)`. Each class function reproduces its corresponding template entity's structure: Class A (Natural) is glyph-only with `parent_entity_id='glyph.accidentalNatural'` for the Natural glyph; Class B (`#-31`) attaches text to glyph with `kBaselineRight↔kBaselineLeft`, `xOffset=-8`, `yOffset=-12`; Class C (`-14`) is text-only at `xOffset=18`, `yOffset=-12` with no attachment.
- **Byte-faithful emission landed.** `emit.py` is the sole repository for XML quirks: tab indentation, lowercase utf-8 declaration, lowercase booleans, raw `n/d` rationals (`0/24`, `-14/1200`, `69/1200` verbatim — no reduction), uppercase hex codepoints (`0xE261`, `0xE262`, `0xE260`), six-decimal scale literals (`100.000000` as a string constant — locale-independent), comma-space ID lists, tuple-with-space (`(0, 0)`, `(0.192, 2.116)`), self-closing empty arrays (`<scalingRules array="true"/>`, `<relativeAttachments array="true"/>`), self-closing `<parentEntityID/>`, and the verbatim `customKeySignatures` boilerplate stub.
- **Pitfall mitigations in code.** Pitfall 3 (silent text-component drop) — `_add_empty_array` always emits the array element, never omits. Pitfall 7 (formatting drift) — every quirk routed through a private formatter; format tests assert against template-derived expected strings. Pitfall 13 (forward-reference confusion) — `SECTION_ORDER` iteration is fixed; emit.py never topologically sorts. Pitfall 14 (locale) — `SCALE_LITERAL` is a string constant, never a `f"{value:.6f}"` from a float. Pitfall 16 (XML escaping) — every string flows through `Element.text`, never f-string concatenation.
- **38 new unit tests pass (63 total project-wide).** 11 in `tests/test_compose.py` (per-class shape contracts: codepoints, attachment offsets, attachment-point names, zOrder, `.0` componentInstanceId suffix, entityID determinism). 27 in `tests/test_emit_format.py` (8 formatter unit checks + 19 end-to-end emission format-quirk verifications, including `xmllint --noout` well-formedness and a two-run determinism smoke test).
- **xmllint passes; emissions are byte-deterministic.** `xmllint --noout` accepts the emitted file. Two consecutive `write()` calls produce byte-identical output (smoke check; full file-level diff against the template is Plan 03's job).

## Task Commits

Each task was committed as a TDD pair (RED test commit followed by GREEN implementation commit):

1. **Task 1 RED: Failing tests for compose.py** — `c8c3202` (test) — 11 tests
2. **Task 1 GREEN: Implement three-class composite dispatcher** — `accc761` (feat)
3. **Task 2 RED: Failing tests for emit.py** — `506c76d` (test) — 27 tests
4. **Task 2 GREEN: Implement byte-faithful XML emission** — `4d70261` (feat) — includes one Rule 1 fix (see Deviations)

_Plan metadata commit (this SUMMARY + STATE/ROADMAP updates) follows separately._

## Files Created/Modified

- `src/cents_generator/compose.py` — three-class dispatcher (`build_class_a`/`b`/`c`), `AccidentalBundle` frozen+slots dataclass, glyph factory (`_glyph_for`), text factory (`_text_for`), four module-level visual constants
- `src/cents_generator/emit.py` — public `write()`, private `_fmt_*` formatters, `SCALE_LITERAL` constant, per-entity `_build_*` element builders (`_build_temperament`, `_build_accidental_system`, `_build_accidental`, `_build_tonality_system`, `_build_text`, `_build_glyph`, `_build_component`, `_build_relative_attachment`, `_build_composite`), structural helpers (`_add_text`, `_add_empty`, `_add_empty_array`, `_add_parent_entity_id`)
- `tests/test_compose.py` — 11 per-class shape tests
- `tests/test_emit_format.py` — 27 formatter + emission tests

## Decisions Made

- **Followed the plan's interface contract exactly.** All public surfaces (function signatures, dataclass fields, helper names) match the `<interfaces>` block of `01-02-PLAN.md` and the `<action>` blocks. No structural deviations.
- **Adopted byte-fidelity post-process for self-closing tags.** Python 3.13+ ElementTree emits `<tag />` with a space; the Dorico template uses `<tag/>` without. Both are XML-equivalent; Plan 03 needs byte equality. Replacement is bounded (` />` cannot occur outside self-closing tags in our fixtures: no escaped `>`, no attribute values containing it). Documented as a Rule 1 deviation.
- **Tested `xmllint` availability rather than hard-requiring it.** `test_xmllint_well_formed` skips gracefully if `xmllint` is missing; on this machine it ran (xmllint is installed at `/usr/bin/xmllint`).
- **Test count differs from plan (27 vs. 22 in `test_emit_format.py`).** The plan's verbatim test source contains 27 distinct test functions; the plan's prose summary said 22. All 27 pass. Total unit-test count for this plan is 38 (not 33 as the plan's success-criteria stated). The plan miscounted; tests themselves are correct as authored.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Python 3.14 ElementTree emits `<tag />` (space before `/>`) instead of `<tag/>` (no space)**

- **Found during:** Task 2 GREEN, post-implementation. `test_self_closing_empty_arrays` and `test_self_closing_parent_entity_id` failed because the emitted bytes contained `<scalingRules array="true" />` (with space) but the template uses `<scalingRules array="true"/>` (no space) and the tests assert against the template form.
- **Issue:** This is exactly Pitfall 7 (formatting drift). The XML semantics are identical — both forms are well-formed, syntactically equivalent self-closing tags — but byte equality is required for Plan 03's round-trip diff. Python's ET added the space behavior somewhere around 3.13; the template was authored under earlier behavior or by Dorico itself (which writes the no-space form).
- **Fix:** Added `body = body.replace(b" />", b"/>")` after `ET.tostring()` and before writing to disk. This is a bounded byte replacement: ` />` cannot occur in valid XML outside the end of a self-closing tag (attribute values are quoted, text nodes never contain literal `>` because `Element.text` auto-escapes it to `&gt;`). The replacement is explained in a comment block at the call site.
- **Files modified:** `src/cents_generator/emit.py`
- **Verification:** All 27 emit tests pass; `xmllint --noout` still accepts the post-processed output; two-run determinism smoke test passes.
- **Committed in:** `4d70261` (rolled into Task 2 GREEN before commit)

### Test count differs from plan (27 vs. 22 in test_emit_format.py)

- **Plan stated:** "all 22 tests passing".
- **Actual:** The plan's verbatim test source contains 27 test functions: 8 formatter unit tests + 19 emission tests (`test_xml_declaration_uses_lowercase_utf8`, `test_root_is_kscorelibrary`, `test_fileversion_is_first_child`, `test_sections_appear_in_canonical_order`, `test_indentation_uses_tabs`, `test_indentation_does_not_use_spaces`, `test_lowercase_booleans`, `test_uppercase_hex_codepoints`, `test_six_decimal_scale_literals`, `test_raw_pitch_delta_no_reduction`, `test_cut_out_tuples_have_space_after_comma`, `test_id_list_has_comma_space_separator`, `test_self_closing_empty_arrays`, `test_self_closing_parent_entity_id`, `test_class_b_attachment_offsets_in_emitted_xml`, `test_class_c_text_offsets_in_emitted_xml`, `test_component_instance_id_has_dot_zero_suffix`, `test_xmllint_well_formed`, `test_two_runs_produce_byte_identical_output`). All 27 pass.
- **Action:** None — the plan miscounted; the test code itself is correct and was reproduced verbatim. Total test count for the plan is 38 (11 compose + 27 emit), not 33 as the verification section claims.

---

**Total deviations:** 1 auto-fix (Rule 1 byte-fidelity post-process — necessary for Plan 03 byte-level round-trip) + 1 plan-count correction (no code change).
**Impact on plan:** No scope changes. The auto-fix is a single line of bounded byte replacement that defeats Pitfall 7 in the only place it can leak (ET's self-closing tag emission).

## Three-Template-Entity Round-Trip Confirmation (Data-Shape Level)

This plan's tests confirm that `build_class_a` / `build_class_b` / `build_class_c` produce `AccidentalBundle`s whose contents — when fed through `emit.write()` — match the template's three entities at every formatting quirk:

| Template entity | Class | Template literal | Confirmed by                                               |
| --------------- | ----- | ---------------- | ---------------------------------------------------------- |
| Natural (line 63-73)  | A | `pitchDeltaFromNatural=0/24`, `cutOutNE=(0.192, 2.116)`, `cutOutSW=(0.476, 0.512)` | `test_class_a_natural_template_shape`, `test_raw_pitch_delta_no_reduction`, `test_cut_out_tuples_have_space_after_comma` |
| -14 (line 50-61)      | C | `pitchDeltaFromNatural=-14/1200`, text component at `(18, -12)`                   | `test_class_c_template_shape`, `test_class_c_text_offsets_in_emitted_xml`, `test_raw_pitch_delta_no_reduction` |
| #-31 (line 38-49)     | B | `pitchDeltaFromNatural=69/1200`, attachment at `(-8, -12)` `kBaselineRight↔kBaselineLeft` | `test_class_b_template_shape`, `test_class_b_attachment_offsets_in_emitted_xml`, `test_raw_pitch_delta_no_reduction` |

Plan 03 will perform the actual byte-level diff against `TonalitySystemStartTemplate.doricolib`. This plan only proves the data-shape and formatting-quirk pieces in isolation.

## Issues Encountered

- **Python 3.14 ElementTree self-closing space.** Detailed above (Rule 1 deviation). Resolved with bounded byte replacement.

## Self-Check

Verified all created files and commits exist on disk:

- FOUND: `src/cents_generator/compose.py`
- FOUND: `src/cents_generator/emit.py`
- FOUND: `tests/test_compose.py`
- FOUND: `tests/test_emit_format.py`
- FOUND commit: `c8c3202` (Task 1 RED)
- FOUND commit: `accc761` (Task 1 GREEN)
- FOUND commit: `506c76d` (Task 2 RED)
- FOUND commit: `4d70261` (Task 2 GREEN)

`pytest tests/ -v` exits 0; 63 tests pass (25 from Plan 01-01 + 38 from this plan).

## Self-Check: PASSED

## Next Phase Readiness

- **Plan 01-03 (orchestrator + round-trip) ready to start.** It can import `compose.AccidentalBundle`, `compose.build_class_a/b/c`, `compose.CLASS_*` visual constants, `emit.write`, and the formatters. The orchestrator will:
  1. Build the three template entities (Natural/-14/#-31) via the class functions.
  2. Construct the singleton `TemperamentDef`/`AccidentalSystemDef`/`TonalitySystemDef` matching the template's "Psychography" identifiers.
  3. Run `emit.write()` to produce a `.doricolib` file.
  4. Diff byte-for-byte against `TonalitySystemStartTemplate.doricolib` (modulo entityIDs, which are derived from a different namespace seed than the template's hand-rolled UUIDs — so an entityID-mapping pass is needed in Plan 03).
- **Pitfall 1 (off-by-100 in pitchDeltaFromNatural)** is NOT yet defeated in code — Phase 1 callers supply the string verbatim. Phase 2 will introduce `pitch_delta_numerator(base, cents)` that centralizes the math.
- **No blockers, no open architectural questions.**
- **Stub list:** None. All exports are real, fully implemented, and tested.

## TDD Gate Compliance

This plan's tasks each used TDD (`tdd="true"`):

- **Task 1:** RED commit `c8c3202` (test only, fails) → GREEN commit `accc761` (implementation, passes). ✓
- **Task 2:** RED commit `506c76d` (test only, fails) → GREEN commit `4d70261` (implementation, passes — with embedded Rule 1 fix). ✓

Both gates present. No plan-level `type: tdd` requirement applies (this plan is `type: execute`).

---
*Phase: 01-generator-skeleton-template-round-trip*
*Plan: 02*
*Completed: 2026-05-01*
