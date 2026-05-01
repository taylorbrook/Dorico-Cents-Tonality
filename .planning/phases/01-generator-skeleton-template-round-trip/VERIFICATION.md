---
phase: 01-generator-skeleton-template-round-trip
verified: 2026-05-01T23:44:47Z
status: passed
score: 9/9 must-haves verified (4/4 phase success criteria + 9/9 requirements)
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: ""
  gaps_closed: []
  gaps_remaining: []
  regressions: []
verdict: PASS
---

# Phase 1: Generator Skeleton + Template Round-Trip — Verification Report

**Phase Goal:** A deterministic Python generator emits byte-faithful Dorico XML, proven by reproducing the working template's three entities (Natural / `-14` / `#-31`) byte-for-byte modulo entityIDs — exercising every composite class once before any scale-up.

**Verified:** 2026-05-01T23:44:47Z
**Status:** passed
**Mode:** initial verification (no previous VERIFICATION.md existed)

---

## Goal-backward Analysis

### Question: What must be TRUE for the goal to be achieved?

The phase goal decomposes into four observable success criteria from `ROADMAP.md` lines 25-29 and reinforced in `<phase_goal>`:

1. **Determinism** — two consecutive runs produce byte-identical output.
2. **Round-trip** — generator output equals `TonalitySystemStartTemplate.doricolib` byte-for-byte modulo entityIDs.
3. **UUID snapshot** — pinned hex values prevent silent regression of Pitfall 2 (non-deterministic UUIDs).
4. **Well-formedness** — `xmllint --noout` passes; `<fileVersion>1.1450</fileVersion>` present.

### Question: What must EXIST and be WIRED for those truths?

A 6-module Python 3.11+ stdlib generator (uuids, constants, entities, compose, emit, main) plus a CLI shim (build.py), with three test suites (round-trip, determinism, snapshot) and the supporting unit-test layer (uuids/entities/compose/emit_format).

### Verification result

**All four success criteria are proven by code AND by re-running the build manually during this verification.** Live reproduction during verification (not just SUMMARY claims):

```
$ python3 build.py --out /tmp/cents_run1.doricolib
$ python3 build.py --out /tmp/cents_run2.doricolib
$ md5 /tmp/cents_run1.doricolib /tmp/cents_run2.doricolib
MD5 (/tmp/cents_run1.doricolib) = 5f207c1de7f8ddf7f0af678384828cd4
MD5 (/tmp/cents_run2.doricolib) = 5f207c1de7f8ddf7f0af678384828cd4
$ cmp -s /tmp/cents_run1.doricolib /tmp/cents_run2.doricolib && echo IDENTICAL
IDENTICAL
$ xmllint --noout /tmp/cents_run1.doricolib    # silent → PASS
$ wc -c /tmp/cents_run1.doricolib TonalitySystemStartTemplate.doricolib
9057  /tmp/cents_run1.doricolib
9057  TonalitySystemStartTemplate.doricolib
$ python3 -m pytest -q
81 passed in 0.14s
```

Both files are 9057 bytes (identical length); MD5 matches the value claimed in SUMMARY.md and STATE.md (`5f207c1de7f8ddf7f0af678384828cd4`); the only byte differences between generated and template are inside `<entityID>` and `<componentInstanceId>` strings (Dorico-random hex vs. our uuid5-derived hex) — verified by direct normalization (see Quality Gates below).

---

## Observable Truths

| #   | Truth                                                                                        | Status     | Evidence                                                                                                                                                                                  |
| --- | -------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Two consecutive runs produce byte-identical output (`diff` empty)                             | ✓ VERIFIED | `tests/test_determinism.py` — 3 tests (in-process, subprocess, `diff` recipe). Live: `cmp -s` returns 0 across two `python3 build.py` runs in this verification session.                  |
| 2   | Output reproduces template's three entities byte-for-byte modulo entityIDs                    | ✓ VERIFIED | `tests/test_template_roundtrip.py::test_round_trip_byte_identical_modulo_entity_ids` passes. Live: normalized template (8409 bytes) == normalized generated (8409 bytes) — verified inline. |
| 3   | UUID snapshot pins entityIDs to defeat silent Pitfall 2 regression                            | ✓ VERIFIED | `tests/test_uuid_snapshot.py` — 7 tests pinning all 13 distinct entityIDs (3 singletons + 3 accidentals + 3 composites + 2 glyphs + 2 texts) plus a direct `entity_id()` re-derivation check. |
| 4   | `<fileVersion>1.1450</fileVersion>` + `<kScoreLibrary>` root + 7 canonical sections in order  | ✓ VERIFIED | `test_round_trip_file_version_is_1_1450`, `test_root_is_kscorelibrary`, `test_sections_appear_in_canonical_order`, `test_round_trip_section_ordering_matches_template`. Live: line 3 of generated output is `\t<fileVersion>1.1450</fileVersion>`. |
| 5   | Output is well-formed XML (`xmllint --noout` passes, with `ET.parse()` fallback)              | ✓ VERIFIED | `test_round_trip_xmllint_well_formed` — uses `xmllint` when present, `ET.parse()` fallback otherwise. Live: `xmllint --noout /tmp/cents_run1.doricolib` exited 0.                          |
| 6   | Single CLI command on Python 3.11+ stdlib only (no third-party deps)                          | ✓ VERIFIED | `python3 build.py --out <path>` works in one invocation. `grep -rE "^(import\|from )" src/cents_generator build.py conftest.py` shows only `__future__`, `argparse`, `pathlib`, `sys`, `uuid`, `dataclasses`, `typing`, `re`, `xml.etree`, `collections` — all stdlib. |
| 7   | Code split into 5 discrete modules + orchestrator (uuids, constants, entities, compose, emit, main)| ✓ VERIFIED | All 6 files present in `src/cents_generator/`. Each module has a single concern verified by direct inspection (uuids.py = 51 lines, constants.py = 79 lines, entities.py = 183 lines, compose.py = 285 lines, emit.py = 342 lines, main.py = 228 lines). |
| 8   | `PROJECT_NAMESPACE` is a single named UUID constant with never-rotate warning                 | ✓ VERIFIED | `src/cents_generator/uuids.py:24` — `PROJECT_NAMESPACE: uuid.UUID = uuid.UUID("6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c")`. Lines 12-23 contain the `NEVER ROTATE` warning block. `tests/test_uuids.py::test_project_namespace_is_pinned` enforces the value. |
| 9   | All quirky formatting (tabs / lowercase booleans / raw `n/d` / `0xE26X` hex / 6-decimal floats / comma-space IDs / self-closing empty arrays) | ✓ VERIFIED | `tests/test_emit_format.py` — 27 tests, all passing. Live grep on output: `\t<` indent, `<isSmufl>true`, `<pitchDeltaFromNatural>0/24`, `<codePoint>0xE261`, `<xScale>100.000000`, `accidentalDefinitionIDs>...,...,...`, `<scalingRules array="true"/>`. |

**Score:** 9/9 truths verified.

---

## Required Artifacts

| Artifact                                  | Expected                                            | Status                  | Details                                                                                                |
| ----------------------------------------- | --------------------------------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------ |
| `src/cents_generator/__init__.py`         | Package marker                                      | ✓ VERIFIED              | 0-byte package marker.                                                                                 |
| `src/cents_generator/uuids.py`            | `PROJECT_NAMESPACE` + `entity_id(kind, key)`        | ✓ VERIFIED              | 51 lines; pinned UUID + `uuid5(NAMESPACE, f"{kind}:{key}").hex` derivation. Used by 4 of 5 sibling modules + 3 tests. |
| `src/cents_generator/constants.py`        | FILE_VERSION, SMuFL codepoints, fonts, KIND prefixes, SECTION_ORDER, 12-EDO divisions | ✓ VERIFIED  | 79 lines; all 9 expected constants exported. SECTION_ORDER is a 7-tuple in canonical Dorico order with NEVER REORDER warning. |
| `src/cents_generator/entities.py`         | 9 frozen+slots dataclasses                          | ✓ VERIFIED              | 9 entity dataclasses (TemperamentDef, AccidentalSystemDef, AccidentalDef, TonalitySystemDef, TextDef, GlyphDef, CompositeDef + Component + RelativeAttachment); all `@dataclass(frozen=True, slots=True)`. |
| `src/cents_generator/compose.py`          | Three-class dispatcher (build_class_a/b/c)          | ✓ VERIFIED              | 285 lines. Class A returns AccidentalBundle(glyph, no text); Class B (sharp/flat) returns (glyph + text + relativeAttachment(-8,-12) kBaselineRight↔kBaselineLeft); Class C (natural-base) returns (text-only at xOffset=18, yOffset=-12). 11 unit tests pass. |
| `src/cents_generator/emit.py`             | Byte-faithful XML emission, `write()` public API    | ✓ VERIFIED              | 342 lines. All formatters (_fmt_tuple, _fmt_id_list, _fmt_bool, _fmt_hex_codepoint, SCALE_LITERAL) implemented. Two byte-fidelity post-processes: ` />` → `/>` and XML-declaration single-quote → double-quote. 27 unit tests pass. |
| `src/cents_generator/main.py`             | Orchestrator: `build_template_three()` + `run()` + `main()` argparse | ✓ VERIFIED | 228 lines. Imports all 5 sibling modules. Hand-orders section tuples to match template byte-for-byte. CLI exits 0 with `--out <path>`.                          |
| `build.py`                                | CLI shim                                            | ✓ VERIFIED              | 23 lines. Adjusts sys.path and delegates to `cents_generator.main.main`. Used by `test_two_subprocess_runs_via_cli_are_byte_identical`.                       |
| `conftest.py`                             | Pytest path shim                                    | ✓ VERIFIED              | 8 lines, idempotent.                                                                                                                                            |
| `tests/test_uuids.py`                     | UUID determinism + format tests                     | ✓ VERIFIED              | 10 tests, all pass.                                                                                                                                             |
| `tests/test_entities.py`                  | Dataclass construction + frozen-semantics tests     | ✓ VERIFIED              | 15 tests, all pass.                                                                                                                                             |
| `tests/test_compose.py`                   | Per-class shape tests                               | ✓ VERIFIED              | 11 tests, all pass.                                                                                                                                             |
| `tests/test_emit_format.py`               | Format-quirk tests                                  | ✓ VERIFIED              | 27 tests, all pass.                                                                                                                                             |
| `tests/test_template_roundtrip.py`        | Round-trip + structural tests                       | ✓ VERIFIED              | 8 tests, all pass; round-trip skips cleanly when template absent.                                                                                              |
| `tests/test_determinism.py`               | Two-run byte-identical tests                        | ✓ VERIFIED              | 3 tests, all pass (in-process + subprocess + `diff` recipe).                                                                                                   |
| `tests/test_uuid_snapshot.py`             | EntityID hex pinning                                | ✓ VERIFIED              | 7 tests, all pass; covers all 13 distinct emitted entityIDs.                                                                                                   |
| `TonalitySystemStartTemplate.doricolib`   | The round-trip target (user-local artifact)         | ✓ PRESENT               | 9057 bytes; gitignored per `.gitignore`.                                                                                                                       |

**Total:** 17/17 expected artifacts present, substantive (not stubs), and wired (imported by tests and/or main pipeline).

---

## Key Link Verification

| From              | To                       | Via                                                          | Status   | Details                                                                                                       |
| ----------------- | ------------------------ | ------------------------------------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------- |
| `build.py`        | `cents_generator.main`   | `from cents_generator.main import main`                      | ✓ WIRED  | `python3 build.py --out X` actually writes the file (re-verified live).                                       |
| `main.py`         | `compose.py`             | `from .compose import build_class_a, build_class_b, build_class_c` | ✓ WIRED | All three class functions invoked in `build_template_three()` (lines 80-112).                                  |
| `main.py`         | `emit.py`                | `from .emit import write` then `write(out_path, ...)`        | ✓ WIRED  | `run()` calls `write()` with all 7 keyword arguments matching `emit.write()` signature.                        |
| `main.py`         | `entities.py`            | direct import + dataclass construction                       | ✓ WIRED  | `TemperamentDef`, `AccidentalSystemDef`, `TonalitySystemDef` constructed in `build_template_three()`.          |
| `main.py`         | `uuids.py`               | `from .uuids import entity_id`                               | ✓ WIRED  | Used for the three singletons (temperament, acc system, tonality).                                             |
| `compose.py`      | `entities.py`            | imports + constructs all dataclasses                         | ✓ WIRED  | Each `build_class_*` returns an `AccidentalBundle` whose internals reference real `AccidentalDef`/`CompositeDef`/`GlyphDef`/`TextDef`. |
| `compose.py`      | `uuids.py`               | `from .uuids import entity_id`                               | ✓ WIRED  | Used inside `_glyph_for`, `_text_for`, and the three class functions for accidental/composite IDs.             |
| `emit.py`         | `entities.py`            | per-dataclass `_build_*` element builders                    | ✓ WIRED  | Every dataclass has a corresponding `_build_*` function that emits its tag tree.                               |
| `emit.py`         | `constants.py`           | `from .constants import FILE_VERSION, SECTION_ORDER`         | ✓ WIRED  | `<fileVersion>` injected from constant; `SECTION_ORDER` drives section iteration.                              |
| Tests             | `cents_generator.*`      | various                                                      | ✓ WIRED  | 7 test files, 81 tests. All imports resolve via `conftest.py`'s `sys.path` shim.                               |
| `entity_id()`     | emitted XML output       | `<entityID>...</entityID>` text                              | ✓ WIRED  | Snapshot test `test_snapshot_emitted_xml_contains_all_entity_ids` confirms all 13 derived entityIDs appear in the output bytes. |

---

## Data-Flow Trace (Level 4)

The generator is a build-time tool, not a UI. It produces a single XML artifact whose data flow is:

`(kind, key) tuples` → `entity_id()` (uuid5) → entity dataclasses (compose.py) → ElementTree → bytes (emit.py) → `<path>.doricolib` on disk.

| Node                     | Input              | Output                                       | Produces Real Data? | Status     |
| ------------------------ | ------------------ | -------------------------------------------- | ------------------- | ---------- |
| `entity_id(kind, key)`   | strings            | 13 distinct entityID strings                 | YES                 | ✓ FLOWING  |
| `build_class_{a,b,c}()`  | name, key, label   | AccidentalBundles with real dataclasses      | YES                 | ✓ FLOWING  |
| `build_template_three()` | (none — Phase 1 hardcoded keys) | 7-tuple of singletons + ordered tuples | YES (3 acc + 3 comp + 2 glyph + 2 text + 3 singletons = 13 entities) | ✓ FLOWING |
| `emit.write()`           | 7 keyword args     | 9057-byte UTF-8 file with 7 sections         | YES                 | ✓ FLOWING  |
| Output `.doricolib`      | (file)             | XML matching template (modulo entityIDs)     | YES                 | ✓ FLOWING  |

No hollow nodes. Every entity asserted by `test_round_trip_entity_count_matches_template` (1 Temperament, 1 AccidentalSystem, 3 AccidentalDefinitions, 1 TonalitySystem, 2 Texts, 2 Glyphs, 3 Composites) appears in real form in the emitted bytes — verified live this session.

---

## Behavioral Spot-Checks

| Behavior                                  | Command                                                                       | Result                                  | Status |
| ----------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------- | ------ |
| `python3 build.py --out X` writes file    | `python3 build.py --out /tmp/cents_run1.doricolib`                            | exit 0; file 9057 bytes                 | ✓ PASS |
| Two runs produce byte-identical output    | `cmp -s /tmp/cents_run1.doricolib /tmp/cents_run2.doricolib`                  | exit 0 (silent)                         | ✓ PASS |
| MD5 matches SUMMARY claim                 | `md5 /tmp/cents_run1.doricolib`                                               | `5f207c1de7f8ddf7f0af678384828cd4` (matches SUMMARY.md and STATE.md) | ✓ PASS |
| `xmllint --noout` accepts output          | `xmllint --noout /tmp/cents_run1.doricolib`                                   | exit 0 (silent)                         | ✓ PASS |
| `<fileVersion>1.1450</fileVersion>` present | `grep '<fileVersion>1.1450</fileVersion>' /tmp/cents_run1.doricolib`        | matches line 3                          | ✓ PASS |
| Generated file size matches template      | `wc -c` on both                                                                | both 9057 bytes                         | ✓ PASS |
| Round-trip normalization equal            | inline Python: `normalize(generated) == normalize(template)`                  | True (both 8409 chars after norm)       | ✓ PASS |
| Full pytest suite                         | `python3 -m pytest -q`                                                        | 81 passed in 0.14s                      | ✓ PASS |
| Stdlib-only check                         | grep all imports                                                              | only `__future__`, `argparse`, `pathlib`, `sys`, `uuid`, `dataclasses`, `typing`, `re`, `xml.etree`, `collections` | ✓ PASS |
| Round-trip regex tightness (adversarial)  | inject capitalized boolean `True` and re-normalize → expect mismatch          | normalization detects drift             | ✓ PASS |

The adversarial check is the one the success_criteria explicitly asked for: confirm the round-trip test would fail if a real byte regression were introduced. Three injected drifts (`0/24` → `0/1200`, tab → 4 spaces, `true` → `True`) all cause the normalized strings to diverge — confirming the entityID-only normalization regex does not mask other byte differences.

---

## Pitfall Mitigation Status

The phase_goal flagged Pitfalls 1, 2, 3, 7, 13 as Phase-1 concerns. Plus Pitfall 4 (fileVersion) is implicit in success criterion 4.

| Pitfall                                              | Mitigation in code                                                                                                       | Test that catches regression                                                                                              | Status     |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **1: Off-by-100 in `pitchDeltaFromNatural`**         | Phase 1 uses literal template strings (`0/24`, `-14/1200`, `69/1200`) — no math. Centralized helper deferred to Phase 2 (GEN-05). | `test_round_trip_pitch_deltas_match_template` asserts the three exact strings.                                            | ✓ DEFERRED (correct — GEN-05 is Phase 2's scope per ROADMAP coverage audit) |
| **2: Non-deterministic UUIDs**                       | `uuid.uuid5(PROJECT_NAMESPACE, f"{kind}:{key}")` exclusively. `PROJECT_NAMESPACE` pinned in `uuids.py` line 24 with never-rotate warning. | Three layers: `tests/test_uuids.py` unit determinism; `tests/test_determinism.py` two-run byte equality; `tests/test_uuid_snapshot.py` 13-entityID hex pinning. | ✓ MITIGATED |
| **3: Silent text-component drop on import (empty arrays)** | `_add_empty_array` in `emit.py` always emits `<scalingRules array="true"/>` and `<relativeAttachments array="true"/>`, never omitted. | `test_self_closing_empty_arrays`, `test_round_trip_byte_identical_modulo_entity_ids` (template has all three present-and-empty) | ✓ MITIGATED |
| **7: XML formatting drift**                          | Every quirk routed through a private formatter (`_fmt_tuple`, `_fmt_id_list`, `_fmt_bool`, `_fmt_hex_codepoint`, `SCALE_LITERAL`). Two byte-fidelity post-processes: ` />` → `/>` and single-quote → double-quote in XML declaration. | 27 tests in `test_emit_format.py` plus `test_round_trip_byte_identical_modulo_entity_ids` (full integration check)         | ✓ MITIGATED |
| **13: Forward-reference confusion / topological sort temptation** | `SECTION_ORDER` is a fixed 7-tuple in canonical Dorico order. `emit.py` iterates it directly; never sorts. Comment block in `constants.py` warns: `DO NOT REORDER`. Forward refs intentional. | `test_sections_appear_in_canonical_order`, `test_round_trip_section_ordering_matches_template` | ✓ MITIGATED |
| **4: Wrong fileVersion** (implicit in SC #4)         | `FILE_VERSION = "1.1450"` constant; emit.py injects it as first child of `<kScoreLibrary>`.                              | `test_fileversion_is_first_child`, `test_round_trip_file_version_is_1_1450`                                               | ✓ MITIGATED |

---

## Requirements Coverage

The phase claims requirements GEN-01, GEN-02, GEN-03, GEN-04, SCH-01, SCH-02, SCH-03, SCH-04, SCH-05 (9 requirements per ROADMAP.md line 24).

| Requirement | Source Plan                  | Description                                                                                                                                         | Status      | Evidence                                                                                                       |
| ----------- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------- |
| GEN-01      | 01-03                        | Python 3.11+ stdlib-only generator runs from a single command                                                                                       | ✓ SATISFIED | `python3 build.py --out X` works; verified live this session. No third-party imports anywhere in `src/`.       |
| GEN-02      | 01-03                        | Re-running the generator produces a byte-identical file (deterministic uuid5)                                                                       | ✓ SATISFIED | `tests/test_determinism.py` (3 tests) + `tests/test_uuids.py` + `tests/test_uuid_snapshot.py`. Live `cmp -s`.  |
| GEN-03      | 01-01, 01-02, 01-03          | Code split into discrete modules (uuid derivation, entity dataclasses, composite dispatcher, XML emission, orchestrator)                            | ✓ SATISFIED | 5 distinct modules + main.py orchestrator + build.py CLI shim. Each has a single concern verified by inspection. |
| GEN-04      | 01-01                        | Pinned project namespace UUID as a single named constant with never-rotate warning                                                                  | ✓ SATISFIED | `uuids.py:24` + lines 12-23 warning block. `test_project_namespace_is_pinned` enforces the value.              |
| SCH-01      | 01-02, 01-03                 | Emit seven canonical sections in Dorico's export order                                                                                              | ✓ SATISFIED | `SECTION_ORDER` constant; `test_sections_appear_in_canonical_order`; `test_round_trip_section_ordering_matches_template`. |
| SCH-02      | 01-01, 01-02, 01-03          | `<fileVersion>1.1450</fileVersion>` and `<kScoreLibrary>` root                                                                                       | ✓ SATISFIED | `FILE_VERSION = "1.1450"` constant; `test_root_is_kscorelibrary`; `test_round_trip_file_version_is_1_1450`. Live grep confirms line 3 of output. |
| SCH-03      | 01-02, 01-03                 | Tab indent, lowercase booleans, `(x, y)` tuples, raw `n/1200`, `0xE26X` hex, six-decimal floats, comma-space ID lists                                | ✓ SATISFIED | `tests/test_emit_format.py` — 27 tests, one per quirk. Live grep confirms each pattern in output.              |
| SCH-04      | 01-02, 01-03                 | Empty arrays serialize as self-closing `<scalingRules array="true"/>` and `<relativeAttachments array="true"/>`                                       | ✓ SATISFIED | `_add_empty_array` always emits; `test_self_closing_empty_arrays`. Live grep on output: 4 `array="true"/>` self-closes. |
| SCH-05      | 01-03                        | Round-trip test reproduces the three template entities byte-for-byte modulo entityIDs                                                               | ✓ SATISFIED | `tests/test_template_roundtrip.py::test_round_trip_byte_identical_modulo_entity_ids` plus 7 supporting tests.   |

**9 of 9 phase requirements satisfied.** No orphaned requirements (REQUIREMENTS.md traceability table marks all 9 as Complete; the 21 remaining requirements are explicitly mapped to Phases 2-4).

---

## Quality Gates

| Gate                          | Result                                                                                                            | Status |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------ |
| **Determinism (two-run)**     | `cmp -s /tmp/cents_run1.doricolib /tmp/cents_run2.doricolib` exits 0; MD5 identical (`5f207c1de7f8ddf7f0af678384828cd4`) | ✓ PASS |
| **Round-trip vs. template**   | Both files 9057 bytes; normalized strings byte-identical (8409 chars each); 8 round-trip tests pass               | ✓ PASS |
| **Round-trip regex tightness**| Adversarial drift injection (boolean capitalization, tuple format, indent) is detected — entityID-only mask is not too loose | ✓ PASS |
| **XML well-formedness**       | `xmllint --noout` exits 0 (silent); `ET.parse()` fallback also passes                                            | ✓ PASS |
| **`<fileVersion>1.1450>`**    | Present at output line 3; asserted by 2 tests                                                                     | ✓ PASS |
| **UUID snapshot**             | All 13 entityID hex strings pinned; 7 snapshot tests pass; values match emitted XML                              | ✓ PASS |
| **Stdlib only**               | grep across `src/` and `build.py` shows zero third-party imports                                                  | ✓ PASS |
| **Test suite**                | 81 tests pass in 0.14 s (10 uuid + 15 entities + 11 compose + 27 emit format + 8 round-trip + 3 determinism + 7 snapshot) | ✓ PASS |
| **Byte-fidelity post-processes** | `b" />" → b"/>"` and XML-decl `'1.0' → "1.0"` both bounded and necessary; documented at the call site            | ✓ PASS |

---

## Anti-Patterns Scan

| File                              | Line | Pattern                                                                  | Severity | Impact                                                                                                |
| --------------------------------- | ---- | ------------------------------------------------------------------------ | -------- | ----------------------------------------------------------------------------------------------------- |
| (none)                            |      |                                                                          |          | No `TODO`/`FIXME`/`XXX`/`HACK`/`PLACEHOLDER` comments in `src/cents_generator/`. No empty `return null` / `return {}`/ `return []` shortcuts. No `console.log`/`print` debug statements (only the legitimate `print(f"wrote {args.out}", file=sys.stderr)` in `main.py`). |

The two byte-fidelity post-processes in `emit.py` (` />` → `/>` and `'1.0'` → `"1.0"` in XML declaration) might initially look like hacks, but each is documented at the call site, bounded to a known-safe replacement, and necessary because Python 3.13+ ElementTree changed serialization defaults. Both transformations are XML-equivalent (only byte-form differs) — and required for the byte-equal round-trip diff. Not a regression risk.

---

## Deviations & Disposition

The four deviations flagged in `<known_deviations_to_assess>` are addressed below:

### 1. Round-trip interpretation: "byte-identical modulo normalized entityIDs"

**Plan 01-03** implements the round-trip test by running both files through a regex that maps each `<kind>.user.<32hex>` to a per-kind sequential placeholder, then byte-comparing the normalized strings.

**Verdict:** ✓ CORRECT INTERPRETATION. The phase goal is bounded by physics: Dorico-written templates carry random entityIDs that we cannot reproduce, but our generator's uuid5-derived IDs ARE deterministic. The only achievable interpretation of "byte-identical modulo entityIDs" is exactly what's implemented. The normalization regex `([a-z-]+)\.user\.([0-9a-f]{32})` matches both `<entityID>` payloads and `<componentInstanceId>` payloads (which carry `.0` suffixes after the hex) — it captures only the 32-hex part and replaces it, leaving everything else untouched. Adversarial test confirmed: introducing a non-entityID drift (boolean case, tuple format, indent) is caught.

### 2. TDD-gate ordering note (Plan 01-03 Task 2)

Plan 01-03 noted that Task 2 (round-trip + determinism + UUID snapshot tests) committed in a single test commit rather than RED-then-GREEN, because Task 1 (orchestrator + CLI) shipped before the test commit and the tests passed on first run.

**Verdict:** ✓ ACCEPTABLE. The tests are integration-level invariants over an already-built API surface (the `run()`, `build_template_three()`, `entity_id()` functions are all exercised by 63 prior unit tests). They are not driving design — they are validating behavior. None of these tests effectively retrofit to passing — they assert tight, externally-observable conditions (byte equality, snapshot hex values, xmllint passing). The commit ordering is a minor process variance; the substantive test quality is intact.

### 3. STATE.md SDK schema mismatch (recurring)

Across all three plans, `gsd-sdk query state.advance-plan / record-metric / add-decision / record-session` failed because the project's STATE.md uses heading conventions the SDK regex doesn't recognize. Authoritative `progress` frontmatter updated correctly via `state.update-progress`.

**Verdict:** ⚠️ TOOLING-ONLY ISSUE (NOT A PHASE-GOAL REGRESSION). Logged in `deferred-items.md`. The phase goal is independent of SDK section parsing; the executor hand-aligned the human-readable narrative in STATE.md to match the authoritative frontmatter, which is sufficient. Recommend the project owner reconcile STATE.md with SDK regexes (one-time fix); not a blocker for proceeding to Phase 2.

### 4. Plan 01-02 Rule-1 fix (`b" />" → b"/>"`) and Plan 01-03 fix (XML decl quote style)

Both are bounded byte replacements applied post-`ET.tostring()`:

- ` />` → `/>`: defeats Python 3.13+ ElementTree's space-before-self-close. Bounded — ` />` cannot appear in valid XML outside the end of a self-closing tag (attribute values are quoted; `Element.text` auto-escapes `>`).
- `'1.0'` → `"1.0"` and `'utf-8'` → `"utf-8"` in the XML declaration: defeats ET's single-quote attribute syntax in the declaration line only. Bounded — applied only to the first line (the declaration); element attributes inside the body always use double quotes in ET output.

**Verdict:** ✓ NECESSARY AND CORRECT. Both transformations are XML-equivalent (only byte-form differs). Each is required for the byte-equal round-trip diff, and each is documented at the call site with a comment block explaining why it is bounded and safe. Without these, the round-trip test would fail in a way that has nothing to do with Dorico schema fidelity.

---

## Human Verification Required

**(none.)** Phase 1 is a pure build-time generator with no UI surface, no real-time behavior, no external service integration. All four success criteria are programmatically verifiable and were re-verified live this session. The Dorico-import physical validation is explicitly Phase 3's scope (per ROADMAP.md line 17).

---

## Verdict

### **PASS**

All four phase success criteria are satisfied with codebase evidence (not just SUMMARY claims) verified live during this verification:

1. ✓ Two consecutive runs produce byte-identical 9057-byte files (MD5 `5f207c1de7f8ddf7f0af678384828cd4`).
2. ✓ Generated output equals template byte-for-byte modulo entityIDs (both 9057 bytes raw, both 8409 chars after normalization, normalized strings exactly equal).
3. ✓ UUID snapshot pins all 13 distinct entityID hex values; tampering with `PROJECT_NAMESPACE` or key strings would produce 13 simultaneous test failures.
4. ✓ `xmllint --noout` exits silently; `<fileVersion>1.1450</fileVersion>` is line 3 of the output.

All 9 Phase-1 requirements (GEN-01..04, SCH-01..05) are satisfied. All five flagged Pitfalls (1, 2, 3, 7, 13) are mitigated in code with corresponding test coverage. All 81 tests pass in 0.14 s. The codebase is stdlib-only, modular per the requirements split, and the round-trip test's entityID-normalization regex is tight enough to catch any non-ID byte drift (verified adversarially).

The four flagged deviations (round-trip interpretation, TDD ordering, STATE.md SDK mismatch, byte-fidelity post-processes) are all either correct, acceptable, or tooling-only issues that do not affect the phase deliverable. The STATE.md SDK mismatch is logged in `deferred-items.md` for the project owner to address as a one-time tooling reconciliation; it does not block Phase 2.

**Phase 1 is complete. Ready to proceed to Phase 2 (Range Expansion to ±99¢).**

---

_Verified: 2026-05-01T23:44:47Z_
_Verifier: Claude (gsd-verifier)_
