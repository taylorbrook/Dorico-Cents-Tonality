# Cents — Custom Tonality System for Dorico

## What This Is

A custom tonality system for Steinberg Dorico (Pro 6.x) shipped as a single `.doricolib` file. It extends standard Western notation with cent-level pitch deviations: every accidental is the familiar natural / sharp / flat glyph paired with a small signed cent label above the staff (e.g., `C♯` with `-14` above means "C-sharp 14 cents flat"). Built for composers and engravers working microtonally inside Dorico who want cent-accurate playback without abandoning conventional notation.

## Core Value

A Dorico user can import the file, write any pitch to ±1 cent of accuracy using familiar accidental glyphs plus a cent label, and Dorico plays it back at that exact cent.

## Requirements

### Validated

- [x] Manually verify cent-accuracy by importing into Dorico and spot-checking playback against a tuner — Validated in Phase 3 against Dorico Pro 6.2.2 macOS + HALion (PLAY-03 12-row matrix at ±1¢; UX-01 597-entry panel; UX-02 4/4 search queries; UX-03 sparse + dense both clean)

### Active

- [ ] Generate a `.doricolib` file containing a single tonality system named "cents" using standard 12-EDO temperament
- [ ] Provide accidentals for natural / sharp / flat across the cent range -99 to +99 (every integer cent), with both spellings allowed (e.g., `C♯ -50¢` and `D♭ +50¢` both available)
- [ ] Include clean `♯`, `♭`, `♮` accidentals at exactly 0¢ for normal tonal use within the same tonality system
- [ ] Render each non-zero accidental as the standard SMuFL glyph (`accidentalSharp` / `accidentalFlat` / `accidentalNatural`) plus a small text label showing signed cents (`+14`, `-14`) anchored at the glyph's baseline-right
- [ ] Encode pitch deviations via `pitchDeltaFromNatural` as `n/1200` so playback is cent-accurate
- [ ] Build the file deterministically with a Python generator script using stable UUIDs (re-running produces byte-identical output)
- [ ] Ship the `.doricolib` file alongside a README explaining install location, import steps, and how to enter a cent-deviated accidental from Dorico's popover

### Out of Scope

- Double-sharp / double-flat variants — adds ~400 entries the user does not need; the ±99¢ range around naturals/sharps/flats already spans -199¢ to +199¢ with overlap
- Sub-cent precision — Dorico's `pitchDeltaFromNatural` is a rational over 1200, but musical use cases plateau at integer cents
- Just-intonation–specific accidental glyphs (Helmholtz-Ellis, Sagittal, etc.) — explicitly using SMuFL standard glyphs to stay readable; cent labels carry the deviation
- Custom key signatures pre-baked into the system — users can author their own per project; the template's key-signature stub stays minimal
- Distribution/marketing (public GitHub repo, download page) — single-user tool first, public release deferred until validated
- A bundled sample `.dorico` test score — manual placement during validation is sufficient; revisit if QA proves painful
- Alternative sign conventions (arrows, unsigned positives) — `+N` / `-N` is locked in for visual consistency

## Context

- **Domain.** Dorico Pro is Steinberg's professional notation app. Its tonality-system architecture lets users define a temperament (the diatonic step sizes), an accidental system (which accidentals are available), accidental definitions (each with a `pitchDeltaFromNatural` fraction over 1200), composite definitions (the visual stacking of glyphs + text), and a tonality system entity that ties them together. All of this lives in a `.doricolib` XML file imported via Library Manager or dropped into Dorico's user library folder.
- **Working starting point.** `TonalitySystemStartTemplate.doricolib` (in this directory) is a hand-crafted, validated example: a tonality system "Psychography" containing three accidental definitions (Natural at 0¢, `-14` at -14¢, `#-31` at +69¢ = sharp 100¢ then -31¢). It demonstrates the visual approach (glyph + text composite, baseline-anchored attachment with offset -8/-12) and the playback math (`pitchDeltaFromNatural` as n/1200). The generator must produce structurally-equivalent XML that Dorico will accept.
- **Visual layout reference.** The composite for `#-31` stacks: `accidentalSharp` glyph at `kBaselineRight` paired to a `-31` text element at `kBaselineLeft`, offset (-8, -12). The natural-only composite is just the natural glyph. The `-14` composite is text-only (no base glyph). These three patterns map cleanly to: zero-deviation accidentals (glyph only), natural-base deviations (text only), and sharp/flat-base deviations (glyph + text).
- **File format internals.** Root element `kScoreLibrary` with `<fileVersion>1.1450</fileVersion>`. Sections in order: temperaments → accidentalSystems → accidentalDefinitions → tonalitySystemDefinitions → textDefinitions → glyphDefinitions → compositeDefinitions. Cross-references use `entityID` strings of the form `kind.user.<32-hex-uuid>`. Accidental systems list their accidental IDs as a comma-separated string in a single XML attribute (`accidentalDefinitionIDs`).
- **User intent.** This is the user's microtonal toolkit; they intend to compose and play it back inside Dorico. Validation = "I can write a piece, hear it, and a tuner agrees with the cents."
- **Reference manual.** Dorico Pro 6.1 manual at <https://www.steinberg.help/r/dorico-pro/6.1/en> — research will pull tonality-system documentation from there.

## Constraints

- **Tech stack**: Python 3 generator producing UTF-8 XML — no external runtime dependencies in the shipped artifact (the `.doricolib` is the deliverable; the script is build-time only)
- **Compatibility**: Must import cleanly into Dorico Pro 6.x using `<fileVersion>1.1450</fileVersion>` and the same XML schema as the template
- **Determinism**: Re-running the generator must produce identical entityID UUIDs (seeded/derived) so re-imports update existing entries instead of duplicating
- **Precision**: Playback accuracy to ±1¢; the visible cent label must always match the actual `pitchDeltaFromNatural` value
- **Visual restraint**: Cent labels stay small and anchored above the glyph — they must not collide with note heads, ledger lines, or each other in dense passages

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Tonality system named "cents" | Descriptive of what it does; user-chosen | Validated in Phase 3 (panel surfaces tonality-system selector entry `cents`) |
| 12-EDO temperament (standard `relativeDiatonicDivisions`) | Cent labels carry all the microtonality; the temperament stays familiar so notation reads normally | Validated in Phase 3 (zero-dev rows play at +100¢/-100¢/0¢) |
| Generate ±99¢ around natural / sharp / flat (597 accidentals) | Covers full -199¢ to +199¢ pitch range with both enharmonic spellings; skips double accidentals to keep the picker manageable | Validated in Phase 3 (panel populates with 597 entries; ±99¢ boundary rows play correctly; Sharp -50 ≡ Natural +50 enharmonic confirmed) |
| Always-signed cent labels (`+14` / `-14`) | Unambiguous at a glance; consistent visual rhythm whether deviation is positive or negative | Validated in Phase 3 (UX-02 search queries match signed-label conventions) |
| Include clean `♯`, `♭`, `♮` at 0¢ (no label) | Same tonality system serves normal tonal music — no need to swap libraries for a quick C-major passage | Validated in Phase 3 (zero-dev triplet visible in panel; Sharp/Flat/Natural play at +100¢/-100¢/0¢) |
| Python generator with stable UUIDs | ~600 entries by hand is brittle; deterministic UUIDs enable safe re-imports | Validated in Phase 3 (md5 `4cd707d2f4b10154a528b95e2ff5db9f` unchanged through phase) |
| Manual playback validation against a tuner | Practical, catches both math errors and Dorico-acceptance issues; cheaper than building automated regression for an XML deliverable | Validated in Phase 3 (HALion + tuner; 12-row matrix at ±1¢; off-by-100 trap defenses confirmed) |

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
*Last updated: 2026-05-02 after Phase 3 (Dorico import + playback validation against Dorico Pro 6.2.2 macOS)*
