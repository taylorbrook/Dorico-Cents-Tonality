# Requirements: Cents — Custom Tonality System for Dorico

**Defined:** 2026-05-01
**Core Value:** A Dorico user can import the file, write any pitch to ±1 cent of accuracy using familiar accidental glyphs plus a cent label, and Dorico plays it back at that exact cent.

## v1 Requirements

### Generator (Python build tool)

- [x] **GEN-01**: A Python 3.11+ stdlib-only generator script produces `cents.doricolib` from a single command (no third-party dependencies)
- [x] **GEN-02**: Re-running the generator produces a byte-identical `cents.doricolib` (deterministic UUIDs via `uuid5(PROJECT_NAMESPACE, key)`)
- [x] **GEN-03**: Generator code is split into discrete modules — UUID derivation, entity dataclasses, composite dispatcher, XML emission, orchestrator — so individual concerns can be modified independently
- [x] **GEN-04**: A pinned project namespace UUID lives as a single named constant; comments warn against rotating it
- [x] **GEN-05**: A central pitch-delta helper computes `pitchDeltaFromNatural` numerator from `(base, cents)` so the off-by-100 trap is impossible to introduce in user code (`Sharp +14` → `114/1200`, `Flat -7` → `-107/1200`, `Natural -7` → `-7/1200`)

### Schema fidelity

- [x] **SCH-01**: Generator emits the seven canonical sections in Dorico's export order: temperaments → accidentalSystems → accidentalDefinitions → tonalitySystemDefinitions → textDefinitions → glyphDefinitions → compositeDefinitions
- [x] **SCH-02**: Output uses `<fileVersion>1.1450</fileVersion>` and `<kScoreLibrary>` root, matching the working template
- [x] **SCH-03**: Output uses tab indentation, lowercase booleans (`true`/`false`), inline `(x, y)` tuple syntax for cutOut points, raw `n/1200` rational fractions for pitch deltas (no auto-reduction), uppercase-X hex codepoints (`0xE262`), six-decimal float strings (`100.000000`), and comma-space–separated ID lists
- [x] **SCH-04**: Empty arrays serialize as self-closing `<scalingRules array="true"/>` and `<relativeAttachments array="true"/>` (never as omitted elements) — required to avoid Dorico's silent-text-component-drop bug
- [x] **SCH-05**: A round-trip test reproduces the three template entities (Natural, `-14`, `#-31`) byte-for-byte modulo entityIDs, exercising all three composite classes (glyph-only, text-only, glyph+text)

### Tonality system & accidentals

- [x] **TON-01**: Output contains exactly one `TonalitySystemDefinition` named "cents" wrapping one 12-EDO `TemperamentDefinition` and one `AccidentalSystem`
- [x] **TON-02**: 12-EDO temperament uses standard `relativeDiatonicDivisions` (200/100/200/200/100/200/200) — diatonic spacing is unchanged
- [x] **TON-03**: Three zero-deviation accidentals are present and named `Sharp`, `Flat`, `Natural`; their composites are glyph-only (no cent label)
- [x] **TON-04**: For each base in {natural, sharp, flat} and each integer cent in -99..-1 and +1..+99, a non-zero accidental exists with name `<Base> <signed-cents>` (e.g., `Sharp +14`, `Flat -50`, `Natural -7`)
- [x] **TON-05**: Accidentals span the union -199¢..+199¢ around natural pitch with overlapping spellings (`Sharp -50` and `Natural +50` both available; `Flat +50` and `Natural -50` both available)
- [x] **TON-06**: Total non-zero accidentals = 3 bases × 198 cents = 594; total accidentals including zero-deviation = 597; AccidentalSystem `accidentalDefinitionIDs` lists all 597 in a single comma-space–separated string

### Visual rendering

- [x] **VIS-01**: Zero-deviation accidentals (`Sharp`, `Flat`, `Natural`) render only the standard SMuFL glyph (codepoints `0xE262`, `0xE260`, `0xE261` respectively) via `font.defaultmusic`
- [x] **VIS-02**: Sharp/flat-base non-zero accidentals render the SMuFL glyph plus a small signed cent text label, joined by a `relativeAttachment` from the glyph's `kBaselineRight` to the text's `kBaselineLeft` with offset `(-8, -12)` (matches the template's `#-31` composite)
- [x] **VIS-03**: Natural-base non-zero accidentals render the signed cent label only (no base glyph), positioned at `xOffset/yOffset = (18, -12)` (matches the template's `-14` composite)
- [x] **VIS-04**: Cent labels use `font.defaulttext` and always include the sign character (`+14` for positive, `-14` for negative)
- [x] **VIS-05**: Cent labels are deduplicated as shared `TextPrimitiveEntityDefinition`s — one per signed cent value (-99..-1, +1..+99 = 198 entries) reused across the three base accidentals at that cent value

### Playback accuracy

- [x] **PLAY-01**: Each accidental's `pitchDeltaFromNatural` resolves to its labeled cent value relative to natural pitch, accurate to ±1¢
- [ ] **PLAY-02**: When imported into Dorico Pro 6.x and placed in an open/atonal-key flow, every accidental plays back at its expected pitch (verified by tuner against HALion or NotePerformer)
- [ ] **PLAY-03**: Spot-check matrix in Phase 3 covers: a zero-deviation accidental on each base, the off-by-100 trap (`Sharp +50` plays +150¢, `Flat -7` plays -107¢), boundary values (`Sharp +99`, `Flat -99`, `Natural ±99`), and one enharmonic-equivalent pair (`Sharp -50` and `Natural +50` produce the same sounding pitch)

### Visual & UX validation

- [ ] **UX-01**: After import in Dorico Pro 6.x, the Key Signatures, Tonality Systems, and Accidentals panel displays all 597 accidentals when the flow uses an open or atonal key signature
- [ ] **UX-02**: Panel-search ergonomics are tested at scale: queries `+14`, `Sharp -`, `Flat +50`, and `Natural` each return the expected matches in usable time
- [ ] **UX-03**: Cent labels do not collide with note heads, ledger lines, or each other in a sparse passage; visual layout in dense passages is documented (with Engrave-mode workaround if collisions occur)

### Distribution

- [x] **DIST-01**: A README accompanies the `.doricolib` and covers, in order: project name, Dorico Pro 6.0+ requirement, package contents, Library Manager install (per-project, primary path), `DefaultLibraryAdditions/` install (power-user path with explicit "remove if Dorico fails to launch" warning), first-note walkthrough that includes the open/atonal key signature step, naming convention reference, troubleshooting (open-key-sig gotcha, third-party VST limits, font-override caveat), version compatibility note, and license
- [ ] **DIST-02**: An `MIT` `LICENSE` file is included
- [ ] **DIST-03**: The `.doricolib` and README install path is verified on the user's actual macOS Dorico install (manual check)

## v2 Requirements

Deferred. Tracked here so they don't get re-litigated.

### Future enhancements

- **DIFF-01**: Sample test score (`cents-test.dorico`) auto-generated by the same script, placing every accidental on a chromatic line for one-shot audition
- **DIFF-02**: Auto-generated cents reference chart in markdown alongside the `.doricolib`
- **DIFF-03**: Public release (GitHub repo with download page, version tagging, release notes)
- **DIFF-04**: Stream Deck / AHK / Keyboard Maestro recipes for power users invoking accidentals from a hardware controller
- **DIFF-05**: HEJI / Sagittal interop layer mapping ratio-based notation to cent equivalents

## Out of Scope

| Feature | Reason |
|---------|--------|
| Double-sharp / double-flat × cents (~400 entries) | The ±99¢ range around natural / sharp / flat already spans -199¢..+199¢ with overlapping spellings; doubles add picker bloat with no additional pitch coverage |
| Sub-cent precision | Musical use cases plateau at integer cents; sub-cent would balloon the picker to thousands of entries |
| Pre-baked microtonal key signatures | Arbitrary curation — users author their own per-project; the customKeySignature stub stays minimal |
| Alternative sign conventions (arrows, unsigned positives, etc.) | Locked to `+N` / `-N` for visual consistency and unambiguity |
| Bundled sample `.dorico` test score | Manual placement during validation is sufficient for v1; promoted to v2 (DIFF-01) |
| Cents reference chart artifact | README description sufficient; promoted to v2 (DIFF-02) |
| Public GitHub release / marketing | Single-user tool first; release deferred until v1 is validated in personal use |
| Custom installer | Drop-in to `DefaultLibraryAdditions/` is one step already; not worth building |
| Dorico 5 / Elements / SE compatibility | `fileVersion 1.1450` requires Dorico Pro 6.0+; older versions and lower editions lack the necessary library import |
| HEJI / Sagittal native glyphs | Standard SMuFL glyphs + cent labels keep notation readable; specialized JI glyph systems are out of scope |
| Automated headless validation | Dorico has no headless mode; validation is manual playback against a tuner |

## Traceability

Mapped by the roadmapper agent on 2026-05-01.

| Requirement | Phase | Status |
|-------------|-------|--------|
| GEN-01 | Phase 1 | Complete |
| GEN-02 | Phase 1 | Complete |
| GEN-03 | Phase 1 | Complete |
| GEN-04 | Phase 1 | Complete |
| GEN-05 | Phase 2 | Complete |
| SCH-01 | Phase 1 | Complete |
| SCH-02 | Phase 1 | Complete |
| SCH-03 | Phase 1 | Complete |
| SCH-04 | Phase 1 | Complete |
| SCH-05 | Phase 1 | Complete |
| TON-01 | Phase 2 | Complete |
| TON-02 | Phase 2 | Complete |
| TON-03 | Phase 2 | Complete |
| TON-04 | Phase 2 | Complete |
| TON-05 | Phase 2 | Complete |
| TON-06 | Phase 2 | Complete |
| VIS-01 | Phase 2 | Complete |
| VIS-02 | Phase 2 | Complete |
| VIS-03 | Phase 2 | Complete |
| VIS-04 | Phase 2 | Complete |
| VIS-05 | Phase 2 | Complete |
| PLAY-01 | Phase 2 | Complete |
| PLAY-02 | Phase 3 | Pending |
| PLAY-03 | Phase 3 | Pending |
| UX-01 | Phase 3 | Pending |
| UX-02 | Phase 3 | Pending |
| UX-03 | Phase 3 | Pending |
| DIST-01 | Phase 4 | Complete |
| DIST-02 | Phase 4 | Pending |
| DIST-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30 (100%)
- Unmapped: 0 ✓

**Phase distribution:**
- Phase 1 (Generator Skeleton + Template Round-Trip): 9 requirements
- Phase 2 (Range Expansion to ±99¢): 13 requirements
- Phase 3 (Dorico Import + Playback Validation): 5 requirements
- Phase 4 (README + Packaging): 3 requirements

---
*Requirements defined: 2026-05-01*
*Last updated: 2026-05-01 — roadmapper traceability mapping*
