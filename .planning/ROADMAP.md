# Roadmap: Cents — Custom Tonality System for Dorico

**Created:** 2026-05-01
**Granularity:** coarse
**Total v1 requirements:** 30
**Coverage:** 30/30 mapped

## Core Value

A Dorico user can import the file, write any pitch to ±1 cent of accuracy using familiar accidental glyphs plus a cent label, and Dorico plays it back at that exact cent.

## Phases

- [x] **Phase 1: Generator Skeleton + Template Round-Trip** — Lock byte-faithful XML emission and deterministic UUIDs by reproducing the working template's 3 entities byte-for-byte (modulo entityIDs) (completed 2026-05-01)
- [x] **Phase 2: Range Expansion to ±99¢** — Sweep `(natural, sharp, flat) × ±99¢` to emit the full 597-accidental `cents.doricolib`, with centralized off-by-100-safe pitch math (completed 2026-05-02)
- [x] **Phase 3: Dorico Import + Playback Validation** — Physically validate import, panel UX, tuner-accurate playback, and visual layout in Dorico Pro 6.x (completed 2026-05-02)
- [ ] **Phase 4: README + Packaging** — Ship the README (open-key-signature gating leads), MIT LICENSE, and verify install on the user's actual macOS Dorico install

## Phase Details

### Phase 1: Generator Skeleton + Template Round-Trip
**Goal**: A deterministic Python generator emits byte-faithful Dorico XML, proven by reproducing the working template's three entities (Natural / `-14` / `#-31`) byte-for-byte modulo entityIDs — exercising every composite class once before any scale-up.
**Depends on**: Nothing (first phase)
**Requirements**: GEN-01, GEN-02, GEN-03, GEN-04, SCH-01, SCH-02, SCH-03, SCH-04, SCH-05
**Success Criteria** (what must be TRUE):
  1. Re-running the generator twice produces byte-identical output (`diff` returns empty) — locking determinism via `uuid5(PROJECT_NAMESPACE, key)`.
  2. The generator can re-emit the three template entities (Natural=Class A glyph-only, `-14`=Class C text-only, `#-31`=Class B glyph+text) byte-for-byte against `TonalitySystemStartTemplate.doricolib` modulo entityIDs — exercising every composite-class code path.
  3. Output is well-formed XML (`xmllint --noout` passes) with `<fileVersion>1.1450</fileVersion>`, `<kScoreLibrary>` root, the seven canonical sections in canonical order (temperaments → accidentalSystems → accidentalDefinitions → tonalitySystemDefinitions → textDefinitions → glyphDefinitions → compositeDefinitions), tab indentation, lowercase booleans, raw `n/1200` rationals, `0xE262`-style hex codepoints, six-decimal float strings, and self-closing `<scalingRules array="true"/>` / `<relativeAttachments array="true"/>` for empty arrays.
  4. The generator runs from a single CLI command on Python 3.11+ stdlib only (no third-party dependencies) and is split into discrete modules (UUID derivation, entity dataclasses, composite dispatcher, XML emission, orchestrator) with a single named `PROJECT_NAMESPACE` UUID constant carrying a never-rotate warning comment.
**Plans**: 3 plans
Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Foundation: PROJECT_NAMESPACE pinned UUID + entity_id helper, project-wide constants (FILE_VERSION, SMuFL codepoints, SECTION_ORDER), and frozen dataclasses for all 9 entity/sub-entity types

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02-PLAN.md — Three-class composite dispatcher (compose.py: build_class_a/b/c) and byte-faithful XML emission (emit.py: tabs, lowercase booleans, raw n/d, 0xE26X hex, 6-decimal floats, comma-space IDs, self-closing empty arrays)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 01-03-PLAN.md — Orchestrator (main.py) + CLI shim (build.py) wiring the foundation into a `python build.py --out <path>` entrypoint, plus byte-faithful round-trip test against TonalitySystemStartTemplate.doricolib (modulo entityIDs) and two-run determinism tests
**UI hint**: no

### Phase 2: Range Expansion to ±99¢
**Goal**: A complete `cents.doricolib` containing all 597 accidentals (3 zero-deviation + 594 non-zero) spanning -199¢..+199¢ around natural pitch with overlapping spellings, every cent accurate to ±1¢ via a centralized off-by-100-safe pitch-delta helper.
**Depends on**: Phase 1
**Requirements**: GEN-05, TON-01, TON-02, TON-03, TON-04, TON-05, TON-06, VIS-01, VIS-02, VIS-03, VIS-04, VIS-05, PLAY-01
**Success Criteria** (what must be TRUE):
  1. The emitted file contains exactly one `TonalitySystemDefinition` named "cents" wrapping one 12-EDO `TemperamentDefinition` (standard `relativeDiatonicDivisions` 200/100/200/200/100/200/200) and one `AccidentalSystem` whose `accidentalDefinitionIDs` is a single comma-space–separated string listing all 597 accidental entityIDs.
  2. The 597 accidentals comprise: 3 zero-deviation (`Sharp`, `Flat`, `Natural` — Class A glyph-only at `0xE262`/`0xE260`/`0xE261` via `font.defaultmusic`) plus 594 non-zero accidentals named `<Base> <signed-cents>` (e.g., `Sharp +14`, `Flat -50`, `Natural -7`) covering every integer cent in -99..-1 and +1..+99 across all three bases — yielding the full -199¢..+199¢ range with overlapping enharmonic spellings (`Sharp -50` and `Natural +50` both exist; `Flat +50` and `Natural -50` both exist).
  3. Visual rendering follows the three-class dispatcher: Class A = glyph-only; Class B (sharp/flat-base non-zero) = SMuFL glyph + signed cent text via `relativeAttachment` `kBaselineRight ↔ kBaselineLeft` offset `(-8, -12)`; Class C (natural-base non-zero) = signed cent text only at `xOffset/yOffset = (18, -12)`. Cent labels use `font.defaulttext`, always include the sign character, and are deduplicated as 198 shared `TextPrimitiveEntityDefinition`s reused across all three bases at each cent value.
  4. A central `pitch_delta_numerator(base, cents)` helper computes `pitchDeltaFromNatural` numerator as `{natural: 0, sharp: 100, flat: -100}[base] + cents`, is unit-tested against hand-calculated values (`Sharp +14` → 114/1200, `Flat -7` → -107/1200, `Natural -7` → -7/1200, `Sharp -50` → 50/1200, `Flat +50` → -50/1200), and is the only place pitch math lives — making the off-by-100 trap impossible to introduce in user code.
  5. Total entity count is 1411 (1 Temperament + 1 AccidentalSystem + 1 TonalitySystem + 597 AccidentalDefinitions + 597 CompositeDefinitions + 3 GlyphDefinitions + 198 TextDefinitions = 1397 + 14 = 1411), emitted via section-grouped deduplication by entityID.
**Plans**: 3 plans
Plans:
**Wave 1**
- [x] 02-01-PLAN.md — GEN-05: pitch_delta_numerator(base, cents) helper module + 12 hand-calculated unit tests (off-by-100 trap defense, Pitfall 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 02-02-PLAN.md — Mode-aware glyph spec (D-01) + build_cents_full_sweep() orchestrator over (natural,sharp,flat) × ±99¢ + --mode {cents,template} CLI flag (D-04); preserves Phase 1 build_template_three (D-03); locks cents-mode keys per D-05

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 02-03-PLAN.md — Test net (structural invariants per D-07.2 + UUID pins & byte-faithful snippet snapshots per D-07.3 + cents-mode determinism per D-07.5) + emit production cents.doricolib artifact at repo root
**UI hint**: no

### Phase 3: Dorico Import + Playback Validation
**Goal**: The shipped `cents.doricolib` imports cleanly into Dorico Pro 6.x, plays back cent-accurate against a tuner across the full ±99¢ range, and survives panel-search and visual-layout testing at the unprecedented 597-entry scale.
**Depends on**: Phase 2
**Requirements**: PLAY-02, PLAY-03, UX-01, UX-02, UX-03
**Success Criteria** (what must be TRUE):
  1. After Library Manager import on Dorico Pro 6.x with an open or atonal key signature in the flow, the Key Signatures, Tonality Systems, and Accidentals panel displays all 597 accidentals — and tuner spot-checks confirm cent-accurate playback against HALion or NotePerformer for: a zero-deviation accidental on each base (Sharp/Flat/Natural plays at +100¢/-100¢/0¢ respectively), the off-by-100 trap (`Sharp +50` plays +150¢ above natural, `Flat -7` plays -107¢), boundary values (`Sharp +99`, `Flat -99`, `Natural ±99`), and an enharmonic-equivalent pair (`Sharp -50` and `Natural +50` produce the same audible sounding pitch).
  2. Panel-search ergonomics work at scale: queries `+14`, `Sharp -`, `Flat +50`, and `Natural` each return the expected matches in usable interactive time.
  3. Cent labels do not collide with note heads or ledger lines in a sparse passage; visual behavior in dense passages (e.g., chord stacking `Sharp -50` + `Natural +50` + `Flat +50` on a single beat) is documented with the Engrave-mode workaround if collisions occur.
**Plans**: 2 plans
Plans:
**Wave 1**
- [x] 03-01-PLAN.md — Library Manager import + panel population (UX-01) + panel-search ergonomics across the four named queries (UX-02); xmllint pre-flight + Dorico build version capture; D-03 conditional fix loop tail

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 03-02-PLAN.md — PLAY-03 12-row tuner spot-check matrix against HALion (3 zero-dev + 2 off-by-100 trap + 6 boundary + 1 enharmonic pair) closing PLAY-02 + PLAY-03; UX-03 sparse no-collision + UX-03 dense `Sharp -50`+`Natural +50`+`Flat +50` chord-stack documentation with Engrave-mode workaround named if collisions occur (D-03 cosmetic carve-out); D-03 conditional fix loop tail
**UI hint**: no

### Phase 4: README + Packaging
**Goal**: A user receiving only `cents.doricolib`, README, and LICENSE can install on Dorico Pro 6.x, write their first cent-accurate note without abandoning the library on a silent failure, and the install path is verified on the user's own macOS Dorico install.
**Depends on**: Phase 3
**Requirements**: DIST-01, DIST-02, DIST-03
**Success Criteria** (what must be TRUE):
  1. The README leads with the Dorico Pro 6.0+ requirement and a Quick Install walkthrough whose first-note section explicitly includes the open/atonal key signature step (Shift+K → "open") — addressing the #1 silent failure for any custom tonality system.
  2. The README presents Library Manager as the primary install path (per-project, recoverable on failure) and `DefaultLibraryAdditions/` as a power-user path with an explicit "remove if Dorico fails to launch" warning, plus troubleshooting that addresses the open-key-signature gotcha, third-party VST microtonal limits (HALion/NotePerformer confirmed; Kontakt/SWAM/Falcon caveats), font-override caveat (`font.defaulttext` interaction), naming-convention reference (`Sharp +14` / `Flat -50`), and a version-compatibility note pinning to Dorico Pro 6.x.
  3. An MIT `LICENSE` file ships alongside the `.doricolib` and README.
  4. The `.doricolib` is verified installed on the user's actual macOS Dorico install via Library Manager — confirming the install path documented in the README works end-to-end on the target machine.
**Plans**: 3 plans
Plans:
**Wave 1** *(parallel; no shared files)*
- [x] 04-01-PLAN.md — DIST-01: README.md authoring (ten sections in order; Dorico Pro 6.0+ leads; Library Manager primary path; DefaultLibraryAdditions warning; Shift+K open-key-sig walkthrough; troubleshooting; compatibility matrix)
- [ ] 04-02-PLAN.md — DIST-02: MIT LICENSE at repo root (Copyright (c) 2026 Taylor Brook)

**Wave 2** *(blocked on Wave 1 completion; non-autonomous)*
- [ ] 04-03-PLAN.md — DIST-03: user runs README install + first-note walkthrough on their macOS Dorico Pro 6.x install; record result in 04-VERIFICATION-NOTES.md; patch README if any wording divergence found
**UI hint**: no

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Generator Skeleton + Template Round-Trip | 3/3 | Complete   | 2026-05-01 |
| 2. Range Expansion to ±99¢ | 3/3 | Complete   | 2026-05-02 |
| 3. Dorico Import + Playback Validation | 2/2 | Complete   | 2026-05-02 |
| 4. README + Packaging | 1/3 | In Progress | - |

## Coverage Audit

| Phase | Requirements | Count |
|-------|--------------|-------|
| 1 | GEN-01, GEN-02, GEN-03, GEN-04, SCH-01, SCH-02, SCH-03, SCH-04, SCH-05 | 9 |
| 2 | GEN-05, TON-01, TON-02, TON-03, TON-04, TON-05, TON-06, VIS-01, VIS-02, VIS-03, VIS-04, VIS-05, PLAY-01 | 13 |
| 3 | PLAY-02, PLAY-03, UX-01, UX-02, UX-03 | 5 |
| 4 | DIST-01, DIST-02, DIST-03 | 3 |
| **Total** | **30 v1 requirements** | **30** |

- v1 requirements: 30 / 30 mapped (100%)
- Orphans: 0
- Duplicates: 0

## Notes

- **Granularity = coarse:** 4 phases for ~30 requirements is appropriate; further splitting would fragment naturally cohesive work.
- **VIS-01..05 sit in Phase 2** (not Phase 1) because Phase 1's round-trip exercises the *dispatcher* against 3 sample entities, but the *complete* visual-rendering capability across all 597 accidentals lands in Phase 2.
- **GEN-05 (pitch-delta helper) sits in Phase 2** because it is the centralized defense against the off-by-100 trap, which only matters when sharp/flat-base non-zero accidentals are emitted (Phase 2's scope).
- **No traditional UI:** All four phases mark `UI hint: no` — Phase 4 is documentation, not frontend. Downstream workflow should route to `/gsd-discuss-phase`, not `/gsd-ui-phase`.
- **Phase 3 is the only phase with empirical risk:** panel-search ergonomics at 597 entries is unprecedented in published Dorico tonality libraries; if validation surfaces issues, the fix is name-format adjustment in Phase 2's `compose.py` (no architectural change).

---
*Roadmap created: 2026-05-01*
*Phase 1 planned: 2026-05-01 — 3 plans across 3 waves (foundation → dispatcher+emit → orchestrator+round-trip)*
