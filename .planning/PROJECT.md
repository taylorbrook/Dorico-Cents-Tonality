# Cents — Custom Tonality System for Dorico

## What This Is

A custom tonality system for Steinberg Dorico (Pro 6.x) shipped as a single `.doricolib` file. It extends standard Western notation with cent-level pitch deviations: every accidental is the familiar natural / sharp / flat glyph paired with a small signed cent label above the staff (e.g., `C♯` with `-14` above means "C-sharp 14 cents flat"). Built for composers and engravers working microtonally inside Dorico who want cent-accurate playback without abandoning conventional notation.

## Core Value

A Dorico user can import the file, write any pitch to ±1 cent of accuracy using familiar accidental glyphs plus a cent label, and Dorico plays it back at that exact cent.

## Current State

**Shipped:** v1.0 MVP on 2026-05-02 (4 phases, 11 plans, 30/30 v1 requirements).

**Deliverables at repo root:** `cents.doricolib` (1.26 MB, 1,411 entities, md5 `4cd707d2f4b10154a528b95e2ff5db9f`) + `README.md` (126 lines, Dorico Pro 6.0+ + Shift+K open-key-sig walkthrough) + MIT `LICENSE`.

**Validation:** End-to-end install + first-note walkthrough verified by the user on macOS Dorico Pro 6.2.2 + HALion. 597-entry panel populates; 12-row tuner matrix passes at ±1¢ across zero-deviation, off-by-100 trap, boundary, and enharmonic-equivalent cases.

**Codebase:** 3,979 LOC Python (generator + 133-test suite, all passing). Stdlib only.

## Requirements

### Validated

- ✓ Single tonality system named "cents" using standard 12-EDO temperament — v1.0 (TON-01, TON-02)
- ✓ Accidentals across natural / sharp / flat at every integer cent in -99..+99 with both enharmonic spellings — v1.0 (TON-03..TON-06)
- ✓ Clean `♯`, `♭`, `♮` accidentals at 0¢ for normal tonal use — v1.0 (TON-03, VIS-01)
- ✓ Non-zero accidentals render as SMuFL glyph + signed cent text label anchored at glyph baseline-right — v1.0 (VIS-02..VIS-05)
- ✓ Pitch deviations encoded via `pitchDeltaFromNatural` as `n/1200` for cent-accurate playback — v1.0 (PLAY-01, PLAY-02, PLAY-03; HALion 12-row tuner matrix at ±1¢)
- ✓ Deterministic Python generator with stable UUIDs — re-running produces byte-identical output — v1.0 (GEN-01..GEN-05, SCH-01..SCH-05)
- ✓ Ship `.doricolib` alongside README explaining install + first-note walkthrough — v1.0 (DIST-01, DIST-02, DIST-03)
- ✓ Manual cent-accuracy validation against a tuner inside Dorico — v1.0 (Phase 3 against Dorico Pro 6.2.2 macOS + HALion; UX-01 597-entry panel; UX-02 4/4 search queries; UX-03 sparse + dense both clean)

### Active

(None — v1.0 shipped. v2 candidates tracked in REQUIREMENTS.md archive: DIFF-01 sample test score, DIFF-02 cents reference chart, DIFF-03 public release, DIFF-04 hardware-controller recipes, DIFF-05 HEJI/Sagittal interop. Awaiting next milestone definition.)

### Out of Scope

- Double-sharp / double-flat variants — adds ~400 entries the user does not need; the ±99¢ range around naturals/sharps/flats already spans -199¢ to +199¢ with overlap (post-ship: still valid; user has not requested doubles)
- Sub-cent precision — Dorico's `pitchDeltaFromNatural` is a rational over 1200, but musical use cases plateau at integer cents (post-ship: still valid; ±1¢ tuner accuracy validated as sufficient)
- Just-intonation–specific accidental glyphs (Helmholtz-Ellis, Sagittal, etc.) — explicitly using SMuFL standard glyphs to stay readable; cent labels carry the deviation (post-ship: still valid; SMuFL approach validated in Phase 3 panel)
- Custom key signatures pre-baked into the system — users can author their own per project; the template's key-signature stub stays minimal (post-ship: still valid; open key signature workflow documented in README §6)
- Distribution/marketing (public GitHub repo, download page) — single-user tool first, public release deferred until validated (post-ship: now eligible for v2 promotion as DIFF-03)
- A bundled sample `.dorico` test score — manual placement during validation is sufficient; revisit if QA proves painful (post-ship: validation went smoothly without one; promoted to v2 as DIFF-01)
- Alternative sign conventions (arrows, unsigned positives) — `+N` / `-N` is locked in for visual consistency (post-ship: still valid; UX-02 search ergonomics depend on signed convention)

## Context

- **Domain.** Dorico Pro is Steinberg's professional notation app. Its tonality-system architecture lets users define a temperament (the diatonic step sizes), an accidental system (which accidentals are available), accidental definitions (each with a `pitchDeltaFromNatural` fraction over 1200), composite definitions (the visual stacking of glyphs + text), and a tonality system entity that ties them together. All of this lives in a `.doricolib` XML file imported via Library Manager or dropped into Dorico's user library folder.
- **Working starting point.** `TonalitySystemStartTemplate.doricolib` (in this directory) was the hand-crafted, validated example: a tonality system "Psychography" containing three accidental definitions (Natural at 0¢, `-14` at -14¢, `#-31` at +69¢ = sharp 100¢ then -31¢). It demonstrated the visual approach (glyph + text composite, baseline-anchored attachment with offset -8/-12) and the playback math (`pitchDeltaFromNatural` as n/1200). Phase 1's round-trip test reproduces this template byte-for-byte modulo entityIDs and remains a regression guard.
- **Visual layout reference.** The composite for `#-31` stacks: `accidentalSharp` glyph at `kBaselineRight` paired to a `-31` text element at `kBaselineLeft`, offset (-8, -12). The natural-only composite is just the natural glyph. The `-14` composite is text-only (no base glyph). These three patterns map cleanly to: zero-deviation accidentals (glyph only), natural-base deviations (text only), and sharp/flat-base deviations (glyph + text) — implemented as the three-class dispatcher in `compose.py`.
- **File format internals.** Root element `kScoreLibrary` with `<fileVersion>1.1450</fileVersion>`. Sections in order: temperaments → accidentalSystems → accidentalDefinitions → tonalitySystemDefinitions → textDefinitions → glyphDefinitions → compositeDefinitions. Cross-references use `entityID` strings of the form `kind.user.<32-hex-uuid>`. Accidental systems list their accidental IDs as a comma-separated string in a single XML attribute (`accidentalDefinitionIDs`).
- **User intent.** This is the user's microtonal toolkit; they compose and play it back inside Dorico. Validation = "I can write a piece, hear it, and a tuner agrees with the cents." — confirmed in Phase 3 against HALion at ±1¢.
- **Known v1.0 limitations.**
  - Path B (`DefaultLibraryAdditions/`) install was not exercised in user verification this round; documented in README §5 with the `remove if Dorico fails to launch` recovery instruction. Path A (Library Manager) is the validated primary install.
  - HALion is the only validated playback engine; NotePerformer/Kontakt/SWAM/Falcon caveats documented in README troubleshooting but not validated.
  - Dense-passage cent-label collisions: Engrave-mode workaround documented (no architectural fix needed at v1.0 scope).
  - User noted intent for future manual README copy edits — independent of v1 ship gate; not blockers.
- **Reference manual.** Dorico Pro 6.1 manual at <https://www.steinberg.help/r/dorico-pro/6.1/en>.

## Constraints

- **Tech stack**: Python 3 generator producing UTF-8 XML — no external runtime dependencies in the shipped artifact (the `.doricolib` is the deliverable; the script is build-time only)
- **Compatibility**: Must import cleanly into Dorico Pro 6.x using `<fileVersion>1.1450</fileVersion>` and the same XML schema as the template
- **Determinism**: Re-running the generator must produce identical entityID UUIDs (seeded/derived) so re-imports update existing entries instead of duplicating
- **Precision**: Playback accuracy to ±1¢; the visible cent label must always match the actual `pitchDeltaFromNatural` value
- **Visual restraint**: Cent labels stay small and anchored above the glyph — they must not collide with note heads, ledger lines, or each other in dense passages

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Tonality system named "cents" | Descriptive of what it does; user-chosen | ✓ Good — Validated in Phase 3 (panel surfaces tonality-system selector entry `cents`) |
| 12-EDO temperament (standard `relativeDiatonicDivisions`) | Cent labels carry all the microtonality; the temperament stays familiar so notation reads normally | ✓ Good — Validated in Phase 3 (zero-dev rows play at +100¢/-100¢/0¢) |
| Generate ±99¢ around natural / sharp / flat (597 accidentals) | Covers full -199¢ to +199¢ pitch range with both enharmonic spellings; skips double accidentals to keep the picker manageable | ✓ Good — Validated in Phase 3 (panel populates with 597 entries; ±99¢ boundary rows play correctly; Sharp -50 ≡ Natural +50 enharmonic confirmed) |
| Always-signed cent labels (`+14` / `-14`) | Unambiguous at a glance; consistent visual rhythm whether deviation is positive or negative | ✓ Good — Validated in Phase 3 (UX-02 search queries match signed-label conventions) |
| Include clean `♯`, `♭`, `♮` at 0¢ (no label) | Same tonality system serves normal tonal music — no need to swap libraries for a quick C-major passage | ✓ Good — Validated in Phase 3 (zero-dev triplet visible in panel; Sharp/Flat/Natural play at +100¢/-100¢/0¢) |
| Python generator with stable UUIDs | ~600 entries by hand is brittle; deterministic UUIDs enable safe re-imports | ✓ Good — Cross-PYTHONHASHSEED determinism verified end-to-end; md5 `4cd707d2f4b10154a528b95e2ff5db9f` byte-stable across runs and through Phase 4 |
| Manual playback validation against a tuner | Practical, catches both math errors and Dorico-acceptance issues; cheaper than building automated regression for an XML deliverable | ✓ Good — Validated in Phase 3 (HALion + tuner; 12-row matrix at ±1¢; off-by-100 trap defenses confirmed) |
| Three-class composite dispatcher (Class A glyph-only / B glyph+text / C text-only) | Maps cleanly to Dorico's three template patterns (Natural / `#-31` / `-14`); each class has one code path | ✓ Good — All three classes round-tripped byte-identically against template in Phase 1; full sweep in Phase 2 reused the same dispatcher unchanged |
| Centralized `pitch_delta_numerator(base, cents)` helper | The off-by-100 trap (Pitfall 1) is the single highest-risk math error; one place to get right | ✓ Good — 12 hand-calculated unit tests + Phase 3 tuner validation confirmed `Sharp +50 → 150¢`, `Flat -7 → -107¢`, `Natural ±99` boundary rows |
| Library Manager as primary README install path | Recoverable on failure; `DefaultLibraryAdditions/` can crash Dorico on launch (Pitfall 4) | ✓ Good — User verified Path A end-to-end in Phase 4 (Plan 04-03); Path B documented with `remove if Dorico fails to launch` recovery |
| Open-key-signature step front-loaded in README first-note walkthrough | The #1 silent-failure mode for any custom tonality system; cents tonality won't surface in the panel without it | ✓ Good — User confirmed Shift+K → "open" step matched observed UI on macOS Dorico Pro 6.2.2 (Plan 04-03 PASS) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-02 after v1.0 milestone (4 phases, 11 plans, 30/30 v1 requirements; cents.doricolib + README + LICENSE shipped, user-verified on Dorico Pro 6.2.2 macOS)*
