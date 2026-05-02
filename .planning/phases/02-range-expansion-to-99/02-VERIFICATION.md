---
phase: 02-range-expansion-to-99
verified: 2026-05-01T12:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 2: Range Expansion to ±99¢ — Verification Report

**Phase Goal:** A complete `cents.doricolib` containing all 597 accidentals (3 zero-deviation + 594 non-zero) spanning -199¢..+199¢ around natural pitch with overlapping spellings, every cent accurate to ±1¢ via a centralized off-by-100-safe pitch-delta helper.

**Verified:** 2026-05-01
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | One TonalitySystemDefinition "cents" wraps one 12-EDO TemperamentDefinition (200/100/200/200/100/200/200) and one AccidentalSystem with comma-space ID string of 597 entityIDs | VERIFIED | `ET.parse(cents.doricolib)`: TonalitySystemDefinition name='cents'; TemperamentDefinition name='12-EDO' with noteAtoB=200, BtoC=100, CtoD=200, DtoE=200, EtoF=100, FtoG=200, GtoA=200; AccidentalSystem name='cents' has accidentalDefinitionIDs string parsing to exactly 597 IDs |
| 2 | 597 accidentals: 3 zero-dev (Class A glyph-only at 0xE262/0xE260/0xE261) + 594 non-zero across {natural,sharp,flat} × {-99..-1, +1..+99}; overlapping enharmonic spellings present | VERIFIED | grep `<AccidentalDefinition>` = 597; grep `<name>Sharp</name>` = 2 (one on AccidentalDefinition, one on Composite), same for Flat/Natural; grep `<name>Sharp -50</name>`=2 AND `<name>Natural +50</name>`=2 (enharmonic pair at +50¢); `<name>Flat +50</name>`=2 AND `<name>Natural -50</name>`=2 (enharmonic pair at -50¢); 3 GlyphPrimitiveEntityDefinitions with codepoints 0xE261/0xE262/0xE260, fontStyle=font.defaultmusic, isSmufl=true, all `<parentEntityID/>` empty (D-01) |
| 3 | Class A glyph-only; Class B = glyph + text @ kBaselineRight↔kBaselineLeft offset (-8, -12); Class C = text-only @ (18, -12); cent labels font.defaulttext, signed, 198 deduped TextDefs | VERIFIED | Sharp +14 (Class B) emits `relativeAttachment xOffset=-8 yOffset=-12`; Natural +50 (Class C) emits text-only component with xOffset=18 yOffset=-12, empty relativeAttachments; 198 TextPrimitiveEntityDefinitions all using fontStyle=font.defaulttext; all 198 text strings start with `+` or `-` (signed); range covers `-99..-1, +1..+99` |
| 4 | Central pitch_delta_numerator(base, cents) = {natural:0, sharp:100, flat:-100}[base] + cents; hand-calc unit tests (Sharp +14→114, Flat -7→-107, Natural -7→-7, Sharp -50→50, Flat +50→-50); ONLY place pitch math lives | VERIFIED | `src/cents_generator/pitch.py` exports `pitch_delta_numerator(base, cents)` with `_BASE_OFFSET_CENTS={"natural":0,"sharp":100,"flat":-100}`; `tests/test_pitch.py` has 12 explicit test functions covering all hand-calculated cases (Sharp +14→114, Sharp -50→50, Flat -7→-107, Flat +50→-50, Natural -7→-7, zero-dev cases, ±99 boundaries, enharmonic pair); grep confirms `pitch_delta_numerator` is the only producer in `src/cents_generator/`; `main.py:281` shows `pdelta = pitch_delta_numerator(base, cents); pdelta_str = f"{pdelta}/1200"` is the single emission point in cents mode |
| 5 | Total entity count is 1411 (1+1+1+597+597+3+198 = 1397 + 14 inline children = 1411). SUMMARY documents 1398 top-level + 13 inline = 1411 — verify reconciles | VERIFIED (with documented arithmetic note) | Per-section top-level entity-definition row counts in cents.doricolib: TemperamentDef=1, AccidentalSystem=1, TonalitySystemDef=1, AccidentalDefinitions=597, CompositeDefinitions=597, GlyphPrimitiveEntityDefinitions=3, TextPrimitiveEntityDefinitions=198 → 1398 top-level rows. Plan 02-02 SUMMARY explicitly reconciles: 1398 top-level + 13 inline structural elements = 1411. The prompt's must-have #5 explicitly accepts this reconciliation ("verify this reconciles with must-have intent"). All per-section counts match the must-have decomposition exactly. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/cents_generator/pitch.py` | Exports `pitch_delta_numerator(base, cents) -> int`; ONLY place pitch math lives | VERIFIED | 59 lines; `_BASE_OFFSET_CENTS={"natural":0,"sharp":100,"flat":-100}`; pure stdlib (`from typing import Literal`); no other public symbols |
| `src/cents_generator/main.py` | Contains `build_cents_full_sweep()`; `run(out_path, mode)`; argparse `--mode {cents,template}` | VERIFIED | 443 lines; imports `pitch_delta_numerator` at line 49; calls it at line 281; `build_cents_full_sweep()` returns 7-tuple (1, 1, 1, 597, 597, 3, 198); `--mode cents` is the default and produces production output; `--mode template` reproduces Phase 1 build |
| `src/cents_generator/compose.py` | Mode-aware `_glyph_for(base, *, mode)`; cents-mode all-empty glyph parents (D-01) | VERIFIED | 325 lines; mode-aware glyph spec; emitted file shows all 3 glyphs with empty `<parentEntityID/>` |
| `src/cents_generator/constants.py` | Locked `KEY_TEMPERAMENT_12EDO_CENTS`, `KEY_ACC_SYSTEM_CENTS`, `KEY_TONALITY_CENTS`, `CENTS_RANGE_NONZERO` | VERIFIED | 105 lines; `KEY_TEMPERAMENT_12EDO_CENTS="12-edo"`, `KEY_ACC_SYSTEM_CENTS="cents"`, `KEY_TONALITY_CENTS="cents"`, `CENTS_RANGE_NONZERO=tuple(c for c in range(-99,100) if c != 0)` (198 entries) |
| `tests/test_pitch.py` | 12 hand-calculated cases pinning Pitfall-1 math | VERIFIED | 80 lines; 12 explicit one-assertion test functions; pytest passes |
| `tests/test_cents_structural.py` | D-07.2 structural invariants (per-section counts, Pitfall-1 delta counts, Pitfall-8 zero-dev presence, ordering) | VERIFIED | 289 lines; 12 test functions; all pass |
| `tests/test_cents_snapshot.py` | UUID pins + byte-faithful AccidentalDefinition/CompositeDefinition snippets for off-by-100 diagnostics | VERIFIED | 578 lines; 16 test functions; all pass |
| `tests/test_determinism.py` | 3 cents-mode determinism variants appended to existing 3 template-mode tests | VERIFIED | 130 lines; 6 tests total (3 template + 3 cents-mode); 3 occurrences of `_cents_mode` confirmed |
| `cents.doricolib` (production deliverable) | At repo root; xmllint passes; counts match | VERIFIED | 1,261,618 bytes; md5 `4cd707d2f4b10154a528b95e2ff5db9f` (matches SUMMARY); xmllint --noout passes; `xml.etree.ElementTree.parse()` succeeds |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `main.py::build_cents_full_sweep` | `pitch.py::pitch_delta_numerator` | Import + per-(base, cents) invocation | WIRED | `from .pitch import pitch_delta_numerator` (line 49); `pdelta = pitch_delta_numerator(base, cents)` (line 281) is the only delta computation in cents-mode emission |
| `main.py::build_cents_full_sweep` | `compose.py::build_class_a/b/c` | Per-pair dispatch with dict.setdefault dedup (Pitfall 15) | WIRED | grep confirms `build_class_a/b/c` calls + `setdefault` usage; deterministic across PYTHONHASHSEED |
| `compose.py::_glyph_for` | `_GLYPH_SPEC_CENTS` / `_GLYPH_SPEC_TEMPLATE` | mode kwarg selects spec; cents emits empty parents (D-01) | WIRED | All 3 cents-mode glyphs emit `<parentEntityID/>` self-closing; template mode preserves Natural inheriting `glyph.accidentalNatural` |
| `build.py` CLI | `main.run(out_path, mode)` | argparse `--mode {cents,template}` default cents | WIRED | `python build.py --out X` defaults to cents (verified by emitting 597-entity file); `--mode template --out X` produces Phase 1 byte-faithful template |
| Production artifact | `pitch_delta_numerator()` | Off-by-100 diagnostic deltas appear in emitted XML | WIRED | grep `cents.doricolib`: `114/1200`=1 (Sharp +14), `-107/1200`=1 (Flat -7), `50/1200`=2 (Sharp -50 + Natural +50, enharmonic), `-50/1200`=2 (Flat +50 + Natural -50, enharmonic), `199/1200`=1 (Sharp +99), `-199/1200`=1 (Flat -99) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `cents.doricolib` per-accidental `pitchDeltaFromNatural` | `pdelta_str` in main.py:282 | `pitch_delta_numerator(base, cents)` | YES — verified by structural delta-count tests + 4 byte-faithful AccidentalDefinition snapshots | FLOWING |
| `cents.doricolib` AccidentalSystem ID list | `acc_system.accidental_definition_ids` | Built from sorted accidentals tuple in `build_cents_full_sweep` | YES — 597 distinct IDs, monotonically ascending by pitch-delta | FLOWING |
| `cents.doricolib` 198 dedup'd cent labels | `texts` tuple via `dict.setdefault` | `_text_for(label)` in compose.py | YES — all 198 unique TextDefs present, deterministic | FLOWING |
| `cents.doricolib` 3 SMuFL glyphs | `glyphs` tuple | `_glyph_for(base, mode='cents')` | YES — 3 distinct codepoints (0xE260/E261/E262), all empty parents | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All tests pass | `python3 -m pytest -q` | `133 passed in 1.47s` | PASS |
| Production build runs | `python3 build.py --out /tmp/cents-rerun.doricolib` | exits 0, prints "wrote /tmp/cents-rerun.doricolib (mode=cents)" | PASS |
| Two-run determinism (production) | `diff cents.doricolib /tmp/cents-rerun.doricolib` | empty stdout, exits 0 | PASS |
| Re-run md5 matches | `md5 /tmp/cents-rerun.doricolib` | `4cd707d2f4b10154a528b95e2ff5db9f` (matches committed) | PASS |
| XML well-formed | `xmllint --noout cents.doricolib` | exits 0 | PASS |
| ElementTree parses | `python3 -c "import xml.etree.ElementTree as ET; ET.parse('cents.doricolib')"` | exits 0 | PASS |
| Section counts | grep AccidentalDefinition / TextPrimitive / GlyphPrimitive / CompositeDefinition / Temperament / AccidentalSystem / TonalitySystem | 597 / 198 / 3 / 597 / 1 / 1 / 1 | PASS |
| Template-mode regression preserved | `python3 build.py --mode template --out /tmp/template-roundtrip.doricolib` | exits 0, mode=template | PASS |
| Helper is single producer | `grep -rE "100\\s*\\+\\s*cents\|cents\\s*\\+\\s*100" src/cents_generator/` outside `pitch.py` | no matches | PASS |
| Pitch-delta off-by-100 diagnostics | grep delta strings in cents.doricolib | 50/1200=2, -50/1200=2, 114/1200=1, -107/1200=1, 199/1200=1, -199/1200=1 (all match expected math) | PASS |
| Enharmonic pair textual | grep `<name>Sharp -50</name>` AND `<name>Natural +50</name>` | both =2 each | PASS |
| Zero-deviation entries present in AccidentalSystem | parse `<accidentalDefinitionIDs>` and resolve | All 597 IDs found, ascending by pitch-delta -199¢..+199¢ | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| GEN-05 | 02-01 | Central pitch-delta helper, off-by-100 trap defense | SATISFIED | `src/cents_generator/pitch.py` + 12 hand-calculated unit tests in `tests/test_pitch.py`; helper is the only producer in `src/cents_generator/` |
| TON-01 | 02-02, 02-03 | TonalitySystemDefinition name='cents' wrapping 12-EDO temperament + AccidentalSystem | SATISFIED | ElementTree parse: `<TonalitySystemDefinition><name>cents</name>` references both temperament and acc system; `test_cents_tonality_name` asserts name appears 2x (acc system + tonality system) |
| TON-02 | 02-02, 02-03 | 12-EDO temperament 200/100/200/200/100/200/200 | SATISFIED | TemperamentDefinition relativeDiatonicDivisions: 200/100/200/200/100/200/200 (verified via parse); `test_cents_temperament_divisions` |
| TON-03 | 02-02, 02-03 | Three zero-deviation accidentals named Sharp/Flat/Natural, glyph-only | SATISFIED | grep `<name>Sharp</name>` etc each present; `test_cents_zero_dev_names_present` + Class A snapshot test |
| TON-04 | 02-02 | Non-zero accidentals named `<Base> <signed-cents>` for cents in -99..-1 ∪ +1..+99 | SATISFIED | 597-3=594 non-zero accidentals; `test_cents_signed_label_names_present` checks 7 representative names |
| TON-05 | 02-02 | Spans -199¢..+199¢ with overlapping enharmonic spellings | SATISFIED | First delta in AccidentalSystem ID list = -199/1200, last = +199/1200; grep confirms Sharp -50, Natural +50, Flat +50, Natural -50 all present |
| TON-06 | 02-02, 02-03 | 597 accidentals total; AccidentalSystem ID string lists all 597 | SATISFIED | Parse: 597 IDs in monotonic ascending pitch-delta order; `test_cents_accidental_definition_ids_in_pitch_delta_order` + `test_cents_accidental_system_includes_all_three_zero_dev` (Pitfall 8 defense) |
| VIS-01 | 02-02, 02-03 | Zero-dev accidentals render only SMuFL glyph at 0xE262/0xE260/0xE261 via font.defaultmusic | SATISFIED | 3 glyphs verified with codepoints 0xE261 (Natural), 0xE262 (Sharp), 0xE260 (Flat), fontStyle=font.defaultmusic, isSmufl=true; Sharp zero-dev composite snapshot pinned (Class A glyph-only) |
| VIS-02 | 02-02, 02-03 | Sharp/flat-base non-zero render glyph + text via relativeAttachment kBaselineRight↔kBaselineLeft (-8, -12) | SATISFIED | Sharp +14 composite has relativeAttachment with xOffset=-8 yOffset=-12; 3 byte-faithful Class B snapshot tests (Sharp +14, Sharp -50, Flat -7) |
| VIS-03 | 02-02, 02-03 | Natural-base non-zero render text-only at xOffset/yOffset=(18, -12) | SATISFIED | Natural +50 composite is text-only with xOffset=18, yOffset=-12, empty relativeAttachments; `test_snapshot_natural_plus_50_composite_block` |
| VIS-04 | 02-02, 02-03 | Cent labels font.defaulttext, always signed | SATISFIED | All 198 TextDefs have fontStyle=font.defaulttext; all text strings start with `+` or `-` (verified by parse) |
| VIS-05 | 02-02, 02-03 | 198 deduped TextDefs shared across bases | SATISFIED | TextPrimitiveEntityDefinition count=198 (one per signed cent value); `test_cents_entity_counts` asserts 198 |
| PLAY-01 | 02-02, 02-03 | Each accidental's pitchDeltaFromNatural resolves to labeled cent value to ±1¢ | SATISFIED | All deltas computed via `pitch_delta_numerator`; pitch-delta delta-count invariants pass; 4 byte-faithful AccidentalDefinition snapshots pin off-by-100 diagnostic cases (114/1200, 50/1200, -107/1200) |

**Coverage:** 13/13 phase 2 requirements satisfied. No orphans (all REQUIREMENTS.md phase-2 IDs are claimed by at least one plan).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | — | — | No TODO/FIXME/PLACEHOLDER stubs in src/cents_generator/ phase-2 code; no inline pitch math outside pitch.py; no third-party imports added; no hardcoded empty values flowing to user-visible output |

### Human Verification Required

None. Phase 2's scope is generator/emission correctness; physical Dorico import + tuner playback is explicitly deferred to Phase 3 (per CONTEXT.md and ROADMAP.md). All Phase 2 truths can be verified programmatically against the codebase + emitted artifact.

### Gaps Summary

No gaps. All 5 ROADMAP success criteria are verified in the codebase + the emitted `cents.doricolib`. The "1411 vs 1398 top-level entity-definition rows" arithmetic is documented in the SUMMARY and explicitly accepted in the prompt's must-have #5 ("verify this reconciles with must-have intent"). The reconciliation — 1398 top-level + 13 inline structural children = 1411 — matches the must-have decomposition (1+1+1+597+597+3+198 = 1398 top-level; the additional 13 are inline structural elements like the `customKeySignature` stub and counted differently in the ROADMAP narrative). Functional correctness is unaffected: every per-section count from the must-have explicitly matches the emission exactly.

### Phase Goal Achievement Summary

The phase goal is achieved end-to-end:

1. The shipped `cents.doricolib` (1,261,618 bytes, md5 `4cd707d2f4b10154a528b95e2ff5db9f`) contains all 597 accidentals (3 zero-deviation Class A + 594 non-zero across {natural,sharp,flat} × ±99¢) spanning -199¢..+199¢ with overlapping enharmonic spellings.
2. Cent accuracy ±1¢ is structurally guaranteed: every cents-mode `pitchDeltaFromNatural` is computed by the centralized `pitch_delta_numerator(base, cents)` helper and emitted as a raw `n/1200` rational. Off-by-100 diagnostic deltas (114/1200, -107/1200, 50/1200, -50/1200, 199/1200, -199/1200) all match expected math at correct counts.
3. The helper is the single producer of pitch-delta numerators across the package — verified by grep across `src/cents_generator/`.
4. 133 tests pass; cents-mode determinism is verified at the production scale (re-run is byte-identical, including under PYTHONHASHSEED randomization across subprocess).
5. Phase 1 D-03 round-trip is preserved via `--mode template`.

---

_Verified: 2026-05-01_
_Verifier: Claude (gsd-verifier)_
