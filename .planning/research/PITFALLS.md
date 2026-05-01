# Pitfalls Research

**Domain:** Dorico Pro 6.x `.doricolib` tonality-system generation — XML build-tooling for a static library file delivering ~1411 entities (3 glyphs + 198 text labels + 600 accidentals + 600 composites + 1 each temperament/system/tonality), built by a Python stdlib generator with deterministic UUIDs.
**Researched:** 2026-05-01
**Confidence:** HIGH on XML-emission and UUID concerns (verified against the working template + multiple forum threads), HIGH on the open-key-signature gating gotcha (Steinberg docs + forum #109521 / #893290), HIGH on the historical "cent deviations lost on import" bug (forum #154743 — Daniel Spreadbury confirmed root cause), MEDIUM on collision behavior at 600-entry scale (no forum thread tests this scale), MEDIUM on Dorico-7-future compatibility (not yet released), MEDIUM on third-party VST microtonal compatibility (forum reports + Scoring Notes).

---

## Critical Pitfalls

### Pitfall 1: `pitchDeltaFromNatural` calculated against the base accidental instead of natural pitch

**What goes wrong:**
Generator emits `<pitchDeltaFromNatural>14/1200</pitchDeltaFromNatural>` for `Sharp +14` instead of the correct `114/1200`. The accidental displays correctly (`♯` glyph + `+14` text label) but plays back at the wrong pitch — the user hears a pitch 14¢ above natural rather than 14¢ above standard sharp (i.e., +114¢ above natural). Every sharp-side and flat-side accidental in the library is silently miscalibrated by ±100¢. The visible label still says `+14` but the played pitch is 100¢ off. This is the worst kind of failure — looks correct, plays wrong, and a user without a tuner won't notice for months.

**Why it happens:**
The field name `pitchDeltaFromNatural` is misleading on first read — the natural-language interpretation is "delta from the *base* accidental", because when you write `Sharp +14` you're mentally thinking "sharp + 14¢". But Dorico stores the delta relative to the **natural pitch**, not the base accidental. Cross-confirmed in ARCHITECTURE.md §"Key cross-reference details that bite": for `Sharp +14`, the actual delta is `(100 + 14)/1200 = 114/1200`. For `Flat -7`, it's `(-100 + -7)/1200 = -107/1200`. For `Natural +14`, it's `14/1200`. The math sign convention (negative = flatter, positive = sharper) is straightforward; the off-by-100 trap is the gotcha.

**How to avoid:**
1. Centralize the math in a single helper:
   ```python
   def pitch_delta_numerator(base: Literal["natural", "sharp", "flat"], cents: int) -> int:
       offset = {"natural": 0, "sharp": 100, "flat": -100}[base]
       return offset + cents
   ```
2. Unit-test the helper with hand-calculated values:
   - `pitch_delta_numerator("natural", 0) == 0`
   - `pitch_delta_numerator("sharp", 0) == 100`
   - `pitch_delta_numerator("sharp", 14) == 114`
   - `pitch_delta_numerator("sharp", -50) == 50`
   - `pitch_delta_numerator("flat", 0) == -100`
   - `pitch_delta_numerator("flat", -7) == -107`
   - `pitch_delta_numerator("flat", 50) == -50`
3. Validate physically against a tuner during Phase 3 — spot-check `Sharp +50` (should be A4 + 150¢ on top of A=440), `Flat -50` (should be -150¢), `Natural +14` (+14¢).

**Warning signs:**
- Phase 3 tuner spot-check disagrees with the on-staff label by exactly ±100¢. The "exactly 100" pattern is the diagnostic — random noise is a different bug.
- Sharp-side and flat-side accidentals at the same visible cent value play different absolute pitches than expected (correctly so) but the delta from natural doesn't match the formula.
- `Sharp -50` and `Natural +50` should play the *same* pitch — if they don't, the math is wrong somewhere.

**Phase to address:** Phase 2 (range) — implement the helper before generating any sharp/flat-base accidental. Phase 3 (validation) — verify with tuner.

**Severity: CRITICAL.** This silently miscalibrates the entire deliverable. Without prevention, the user ships a broken library and won't discover it until they put it on a real piece.

---

### Pitfall 2: Random/non-deterministic UUIDs cause re-imports to duplicate every entity

**What goes wrong:**
Re-running the generator produces a different UUID for each entity each time. Re-importing the updated `.doricolib` into a project that already has the previous version doesn't update the existing accidentals — it adds 600 *more* accidentals alongside them. After three iterations, the user's panel has 1800 accidentals; after five, 3000. Notes already placed using v1's accidentals continue to reference v1's entityIDs, which are still present, so they appear correct — but the v2 entries are duplicates with the same names. The picker becomes unscrollable; the user assumes the library is broken.

**Why it happens:**
The default `uuid.uuid4()` is random by design. Anyone reaching for "I need a UUID" naturally types `uuid4()`. Dorico matches imports by entityID strictly — there's no "merge by name" fallback (confirmed: Steinberg docs and forum #944092). Once two accidentals share a name but have different entityIDs, Dorico treats them as distinct entities forever.

**How to avoid:**
1. Use `uuid.uuid5(PROJECT_NAMESPACE, key)` exclusively. Pin `PROJECT_NAMESPACE` as a module-level constant in `uuids.py` and **never rotate it**.
2. Lock key conventions on day one (e.g. `accidental:sharp+14`, `glyph:accidentalSharp`, `text:+14`). Never change a key once the library is shipped — a rename creates a new UUID and a duplicate.
3. CI/pre-commit step: run the generator twice, `diff` outputs, fail if non-empty.
4. Audit all UUID uses with `grep -rn "uuid" src/` — if `uuid4` or `uuid1` appears, it's a bug.

**Warning signs:**
- `diff /tmp/a.doricolib /tmp/b.doricolib` produces non-empty output across consecutive runs.
- Re-importing into a project that already has the library duplicates every accidental.
- Number of accidentals in the panel grows by ~600 per re-import.

**Phase to address:** Phase 1 (skeleton) — uuids.py is one of the first modules. Phase 1 verification = byte-identical re-runs.

**Severity: CRITICAL.** Users will iterate; non-deterministic UUIDs make the artifact unusable after the first update.

---

### Pitfall 3: Library imports cleanly but cent deviations are silently lost (Dorico's historical "text component" import bug)

**What goes wrong:**
The `.doricolib` imports without any error dialog. The tonality system appears in the dropdown. The accidentals appear in the panel with their names ("Sharp +14"). But when the user places one on a note, it plays back at the standard sharp pitch — the cent deviation is gone. Visually, the cent label may also be missing.

**Why it happens:**
Documented Dorico bug from 3.5-era (forum #154743) — Daniel Spreadbury confirmed: *"Dorico is failing to import the text components of your accidental definitions."* The bug was the engine silently dropping `TextPrimitiveEntityDefinition` references during the import pass when the structure didn't exactly match Dorico's own export. Spreadbury said it was fixed in internal builds, but similar silent-import-loss patterns recur in Dorico 5→6 transitions (forum #987754: "silent partial failure" — files import but settings come from unintended sections).

The risk for our generator is that subtle structural differences from Dorico-canonical export (e.g. a section ordered differently, an empty element written as `<x></x>` instead of `<x/>`, a `<scalingRules array="true"/>` element omitted) could trigger Dorico's lenient parser to drop fields silently rather than fail loudly.

**How to avoid:**
1. **Match the working template byte-for-byte structurally.** The template has been hand-validated against Dorico Pro 6.x — copy its conventions verbatim:
   - Section emission order: temperaments → accidentalSystems → accidentalDefinitions → tonalitySystemDefinitions → textDefinitions → glyphDefinitions → compositeDefinitions.
   - Always emit `<scalingRules array="true"/>` (self-closing) on every CompositeDefinition, even when empty.
   - Always emit `<relativeAttachments array="true"/>` for Class A and Class C composites (self-closing).
   - Always emit `<components array="true">` even for single-component composites.
   - Always emit `<parentEntityID/>` self-closing for entities without an inherited parent.
2. **Phase 1 round-trip test:** Re-emit the three template entities (Natural, `-14`, `#-31`) using our generator with the original keys. Byte-diff against the original template — should differ only in entityIDs (because our keys produce different UUIDs than the hand-written template's). If structure differs in any other way, fix `emit.py` before scaling to Phase 2.
3. **Phase 3 tuner validation tests playback, not just import.** Don't trust "Dorico didn't show an error dialog" — verify physically.

**Warning signs:**
- Tonality system appears in dropdown but accidentals panel is empty → AccidentalSystem failed to import.
- Accidentals appear but play at standard pitch → text components or pitchDeltaFromNatural lost.
- Visible cent label missing on staff but accidental plays at correct pitch → composite components dropped (rare; usually pitch is lost too).
- Re-export from Dorico produces a file that differs from our generator output in significant structural ways (not just whitespace).

**Phase to address:** Phase 1 (structural correctness via round-trip test) and Phase 3 (playback validation).

**Severity: CRITICAL.** This is the exact failure mode the question asks about — "library imports but doesn't work." Documented to have happened in Dorico 3.5 and 5→6 transitions.

---

### Pitfall 4: Library file in `DefaultLibraryAdditions/` causes Dorico to fail to launch

**What goes wrong:**
The user copies `cents.doricolib` into `~/Library/Application Support/Steinberg/Dorico 6/DefaultLibraryAdditions/`. Next launch, Dorico hangs at startup, shows a parse error dialog, or quits. Until the user finds and removes the file, the application is unusable.

**Why it happens:**
Documented behavior, confirmed by Steinberg moderators on forum #914859: *"If Dorico can't parse the contents of doricolib files in the DefaultLibraryAdditions folder, then it will flag an error and quit. In which case, you should remove the lib files and relaunch Dorico."* Unlike per-project Library Manager imports (which fail gracefully and let the user keep working), parse failures in the `DefaultLibraryAdditions/` folder are fatal at startup. Any malformed XML — an unescaped `&` in a name, a stray byte, mismatched tags — bricks the application.

**How to avoid:**
1. **Run `xmllint --noout cents.doricolib` as a CI step.** Well-formedness is necessary but not sufficient (Dorico's parser is stricter than xmllint), but it catches the most common breakage.
2. **README MUST recommend Library Manager (per-project) as the primary install method**, with `DefaultLibraryAdditions/` as a power-user option clearly flagged: *"If Dorico fails to launch after dropping the file here, remove it and relaunch. Use this folder only after confirming the file works via Library Manager."*
3. **Phase 1 round-trip into Dorico via Library Manager first.** Don't drop into `DefaultLibraryAdditions/` until at least one round of validation passes.
4. **XML escaping discipline in `emit.py`.** Although our names (`Sharp +14`, `Natural -50`) contain only ASCII and `+`/`-`, defensive coding matters: use `xml.etree.ElementTree`'s built-in escaping (it's automatic via `Element.text` assignment, which is what our `to_xml()` methods will use). Never build XML by string concatenation.

**Warning signs:**
- Dorico shows a parse error dialog at startup naming our file.
- Dorico hangs at the splash screen.
- Other libraries in the same folder work, but ours doesn't.

**Phase to address:** Phase 4 (packaging) — README warning; Phase 1 (skeleton) — XML escaping built into `emit.py`; Phase 3 (validation) — Library Manager test before recommending the auto-load folder.

**Severity: HIGH.** Recoverable (delete the file), but the user-experience cost is severe — Dorico is the user's primary tool.

---

### Pitfall 5: User changes tonality system, sees empty accidentals panel, concludes library is broken

**What goes wrong:**
User imports `cents.doricolib`, opens a project, picks "cents" from the tonality system dropdown — but the accidentals panel is empty (or only shows the standard 12-EDO accidentals). They conclude the library is broken and abandon it.

**Why it happens:**
**The #1 silent failure for any custom tonality system in Dorico.** To use accidentals from a custom tonality system, the user must first insert an **open** or **atonal** key signature in the flow (Shift+K → "open" or "atonal"). Without this, the panel doesn't populate. Multiple forum threads confirm this is the most common stumbling block:
- Forum #109521: *"select the rest, then select 24-EDO in the right hand panel, then type shift-K and 'atonal'"* — strict ordering required.
- Forum #893290: *"I didn't insert a key signature ... going forward I guess I have to swap steps 3 and 4"* — user resolves their own bug after weeks.
- Forum #884737: similar root cause.
- FEATURES.md flagged this as the #1 README priority.

**How to avoid:**
1. **README leads with this.** Quick-install walkthrough, step 2: *"Press Shift+K, type `open`, press Enter. This is required — the panel stays empty until you do."*
2. **Troubleshooting section addresses it explicitly:** *"I changed the tonality system but the panel is empty → Insert an open/atonal key signature first."*
3. **(Differentiator if scoped in)** The bundled sample test score (`cents-test.dorico`) ships with an open key signature already in place. Users who open it see the system working immediately, then learn the workflow from a known-good starting point.

**Warning signs:**
- User reports "the library doesn't work" without further detail → almost certainly this.
- Panel shows "0 accidentals" or only standard 12-EDO entries.
- Apply-accidental click does nothing.

**Phase to address:** Phase 4 (README + packaging) — this is documentation, not code.

**Severity: HIGH.** Doesn't break anything technically, but the user-perception cost is total — they abandon the library before it ever runs.

---

### Pitfall 6: Re-importing a v2 of the library breaks notes already placed using v1's accidentals

**What goes wrong:**
User places notes in a score using `cents.doricolib v1` accidentals (e.g. `Sharp +14`). Later, they re-import an updated `cents.doricolib v2` that has the same accidentals plus some new ones. If v2's UUIDs match v1's (i.e., determinism worked), the existing notes update silently and continue to play correctly. If v2's UUIDs don't match — even for accidentals that conceptually didn't change — the existing notes either keep referencing v1's entities (which now exist alongside v2's duplicates), or worse, they "lose" their accidental and revert to natural.

A second, more insidious variant: the official Dorico docs warn (per microtonal-accidentals docs): *"when you change the tonality system of existing notation with accidentals, some or all of them may disappear – they are still there and functioning the same in terms of pitch, just invisible, if they are not defined in the current system."* So if a user switches tonality systems mid-project (e.g. demos a HEJI system, then comes back to cents), accidentals can become invisible while still affecting pitch — extremely confusing.

**Why it happens:**
- Dorico matches accidentals across imports by entityID. UUID stability is the only contract.
- Tonality systems are project-scoped (each `.dorico` project file embeds the libraries it uses); re-imports replace by entityID match.
- Any rename of an internal key (the input to `uuid5`) breaks this.

**How to avoid:**
1. **Lock key conventions in `compose.py` and `uuids.py` on day one.** Document them as a project-stability promise: never change `f"accidental:{base}{signed_cents}"` formatting.
2. **Version the file via the README and a comment in the XML, NOT via entity names.** Entity names like `Sharp +14 v2` would break update-in-place.
3. **README must warn about cross-tonality-system invisible-accidentals behavior** — if a user has a piece using `cents` and they switch to a different tonality system mid-project, accidentals can vanish. The documented Steinberg behavior; not our bug, but our README's responsibility.
4. **Treat any change to key format, name format, or PROJECT_NAMESPACE as a breaking change** that requires a manual migration step (which we do not currently provide).

**Warning signs:**
- After re-import, panel shows duplicates with the same names.
- Notes lose their accidental on re-import.
- Notes still play microtonally but no accidental visible (cross-tonality issue).

**Phase to address:** Phase 1 (skeleton) — lock key conventions immediately. Phase 4 (README) — document the workflow.

**Severity: HIGH.** Real iteration scenario; mitigated by Phase 1 deterministic UUIDs but requires discipline forever.

---

### Pitfall 7: XML formatting drift breaks Dorico's strict-but-silent parser

**What goes wrong:**
Generator output passes `xmllint --noout` but Dorico imports it with subtly missing fields — a composite has no glyph, a text label is empty, the AccidentalSystem references nothing. No error dialog appears.

**Why it happens:**
Dorico's parser tolerates well-formed XML that doesn't exactly match its expectations by silently dropping fields rather than failing loudly. Specific known gotchas (cross-checked against the working template):

| Quirk | Wrong | Right |
|---|---|---|
| Indentation | 2 or 4 spaces | Tabs (`\t`) — verified in the template via hex dump |
| Booleans | `True` / `False` (Python default) | `true` / `false` lowercase |
| Empty elements | `<parentEntityID></parentEntityID>` | `<parentEntityID/>` self-closing |
| Tuple syntax | `(0,0)` no space | `(0, 0)` with space after comma |
| Rational syntax | `19/200` (auto-reduced) | `114/1200` raw |
| ID list separator | `id1,id2,id3` no space | `id1, id2, id3` with space after each comma |
| Float format | `100.0` | `100.000000` six decimals |
| Hex format | `0xe262` lowercase | `0xE262` capital X, capital hex |
| Encoding declaration | `UTF-8` uppercase | `utf-8` lowercase |
| componentInstanceId | `glyph.user.<hex>` | `glyph.user.<hex>.0` (with `.N` suffix matching componentInstance) |

**How to avoid:**
1. **Centralize formatting in `emit.py`.** Every quirky field has one helper:
   ```python
   def fmt_tuple(x: float, y: float) -> str: return f"({x}, {y})"
   def fmt_rational(num: int, den: int = 1200) -> str: return f"{num}/{den}"
   def fmt_id_list(ids: list[str]) -> str: return ", ".join(ids)
   def fmt_bool(b: bool) -> str: return "true" if b else "false"
   def fmt_hex_codepoint(cp: int) -> str: return f"0x{cp:04X}"
   def fmt_scale(s: float) -> str: return f"{s:.6f}"
   ```
2. **Phase 1 round-trip test diffs byte-by-byte** against the working template (modulo entityIDs). Catches every quirk above.
3. **Verify with hex viewer** that the indent is `\t` (0x09), not spaces (0x20). One-time check.

**Warning signs:**
- Round-trip diff against the template shows differences other than entityIDs.
- Dorico imports the file but specific entities are missing fields (e.g. composite has no glyph).
- File size is significantly different from a hand-built equivalent.

**Phase to address:** Phase 1 (skeleton) — emit.py is built around these formatters from day one. Round-trip test is the verification.

**Severity: HIGH.** Each quirk individually is a "looks done but isn't" failure; cumulative risk is high.

---

## Moderate Pitfalls

### Pitfall 8: Removing the natural accidental from the AccidentalSystem causes Dorico to crash

**What goes wrong:**
If our AccidentalSystem's `<accidentalDefinitionIDs>` list omits a Natural entry, Dorico can crash when the user attempts to input notes. Documented in forum #110776 (Dorico 2 era): *"the problem is indeed caused by you having removed the default natural accidental from the tonality system – don't do that!"* Steinberg said they'd harden against it, but the assumption is baked deep in the engine.

**Why it happens:**
Dorico's note-input pipeline expects to be able to fall back to a natural accidental when no other accidental applies. Without one in the system, the engine hits an unhandled assumption.

**How to avoid:**
The accidental system list MUST include the zero-deviation `Natural` entry as one of the IDs. Our spec already does this (per FEATURES.md: zero-deviation `♯`/`♭`/`♮` are required). Don't ever optimize them out.

**Warning signs:**
Dorico crashes on note input after switching to our tonality system. Specifically reproducible.

**Phase to address:** Phase 2 (range) — the loop that builds the AccidentalSystem must include the three zero-deviation entries.

**Severity: MEDIUM** (rare to accidentally delete, but catastrophic when it happens).

---

### Pitfall 9: Cent labels collide with note heads, ledger lines, beams, or each other in dense passages

**What goes wrong:**
The template's `(-8, -12)` offset for the text-relative-to-glyph attachment is known to work for a single accidental on a single staff position. At 600-entry scale across real scores with chords, ledger-line notes, beamed groups, and dense passages, collisions are inevitable. Cent labels may overlap note heads above them, ledger lines, or adjacent accidentals.

**Why it happens:**
Dorico has explicit limitations on accidental positioning: *"you can't move accidentals vertically, I'm afraid"* (forum #821103). And the ledger-line interaction is documented: accidentals appear closer to noteheads than they are when ledger lines are present. We can't reposition labels per-note; the offset is library-wide.

**How to avoid:**
1. **Accept that `(-8, -12)` is "good enough"** for the v1 deliverable — it's the empirically-validated offset from the working template.
2. **Phase 3 validation includes dense-passage spot-checks:** stack three notes with `Sharp -50`, `Natural +50`, `Flat +50` (which are the same pitch — see Pitfall 10) on a single beat, eyeball the result.
3. **Cut-out tuples could in theory help** — Dorico uses `cutOutNW/NE/SE/SW` for collision shapes. Our generator emits `(0, 0)` for everything per the template's pattern for non-natural accidentals. Worth flagging that future versions could populate these for tighter collision avoidance.
4. **README troubleshooting note:** "If labels collide in dense passages, manually reposition with the staff-spacing tool in Engrave mode (per-note adjustment) or expand vertical staff spacing."

**Warning signs:**
- Labels visibly overlap glyphs or noteheads in test scores with ledger-line notes.
- Adjacent accidentals' labels touch in chords.

**Phase to address:** Phase 3 (validation) — exercise dense passages. Phase 4 (README) — troubleshooting note.

**Severity: MEDIUM.** Visual issue, not functional. Workarounds exist in Engrave mode.

---

### Pitfall 10: Enharmonic-equivalent pitches across base accidentals create three "different" accidentals at the same pitch

**What goes wrong:**
`Sharp -50` (delta = +50¢ from natural), `Natural +50`, and `Flat +150`... wait, the last one is out of our range. But `Sharp -50` and `Natural +50` *do* both produce +50¢ from natural — they're the same pitch with different spellings. The user might be confused: the panel shows three accidentals that look different but two of them are the same pitch (in our range, `Sharp -50` and `Natural +50` are the cleanest example; `Flat -50` is at -150¢ from natural, which is the same as `Natural` 50¢ flatter than `Flat`'s `-100`).

Actually, more precisely: `Sharp -50` = +50¢, `Natural +50` = +50¢, and `Flat +50` = -50¢. So `Sharp -50` and `Natural +50` are enharmonic. This is intentional (the user explicitly wants both spellings) but Dorico's behavior with enharmonic accidentals in the same tonality system is not 100% characterized — does the panel sort show them adjacent? Does pitch-search find both?

**Why it happens:**
The point of the cents library is dual-spelling availability. The risk is that Dorico's enharmonic-resolution logic (which normally rewrites `B♯` → `C` based on key context) may interfere unexpectedly. Microtonal accidentals are supposed to be exempt from this, but at the boundary cases (e.g. `Sharp -50` colliding with `Natural +50`) edge-case behavior is unverified.

**How to avoid:**
1. **Phase 3 spot-check enharmonic behavior:** place `Sharp -50` and `Natural +50` on a tied note pair, verify they play the same pitch and are visually distinguishable.
2. **README documents this as a feature** (FEATURES.md already plans this): "Both spellings of every cent are available — `C♯ -50¢` and `D♭ +50¢` both exist for the same absolute pitch."
3. **Keep the panel naming distinct:** `Sharp -50`, `Natural +50`, `Flat +50` are unambiguously different strings, so search disambiguates them clearly.

**Warning signs:**
- Dorico spontaneously rewrites a note's accidental on a re-spelling action.
- Two enharmonic accidentals play different absolute pitches (would indicate math error).

**Phase to address:** Phase 3 (validation).

**Severity: MEDIUM** — likely fine but unverified at this scale.

---

### Pitfall 11: User overrides `font.defaultmusic` or `font.defaulttext` in their score, breaking cent labels

**What goes wrong:**
Cent labels render in an unexpected font (e.g. Times New Roman instead of Bravura's text variant) because the user has overridden `font.defaulttext` at the score or paragraph-style level. Worse, there's a documented Dorico bug (forum #877243): *"Changing 'Default Text Font' overrides 'Default Music Text Font'"* — single-axis font changes can affect more than the user intends.

**Why it happens:**
Our template references `<fontStyle>font.defaulttext</fontStyle>` for text labels and `<fontStyle>font.defaultmusic</fontStyle>` for glyphs. These are style references, not concrete font families — they resolve via the user's Font Styles settings. Whatever the user has bound `font.defaulttext` to in their score is what cent labels render in. If they've bound it to a non-monospace, narrow, or oversized font, labels could be illegible or collide more aggressively (Pitfall 9).

**How to avoid:**
1. **Stick with the template's style references** — don't try to override at the library level. Worst case the user customizes for their score, which is correct Dorico behavior.
2. **README documents the dependency:** "Cent labels use Dorico's `font.defaulttext` style. If you've customized this font in your score, cent labels will render in your custom font."
3. **(Optional, future)** Define a custom paragraph style `centsLabel` referenced by our text definitions, giving us per-library font control. Out of scope for v1 — the style reference approach is correct.

**Warning signs:**
- User reports labels look wrong (oversized, weird font, italics) in a specific score but not others.
- Labels are illegible at default zoom in some scores.

**Phase to address:** Phase 4 (README) — documentation only.

**Severity: MEDIUM** — affects a subset of users with customized scores.

---

### Pitfall 12: VST instrument doesn't support cent-accurate microtonal playback

**What goes wrong:**
Dorico sends the cent deviation correctly, but the user's VST instrument (Kontakt 8, SWAM, Falcon, third-party libraries) doesn't receive or apply it. Playback sounds at standard equal-tempered pitches. The user blames our library; the actual issue is the playback engine. Documented in forum #1030334 — *"there's no straightforward way for Dorico to communicate this using its alternate tuning accidental systems"* with several common VST3 instruments.

**Why it happens:**
Microtonal pitch info travels via different transport mechanisms depending on the instrument:
- **HALion / Dorico's stock sounds:** confirmed cent-accurate (forum threads + Scoring Notes).
- **NotePerformer:** *"responds to the VST micro tuning messages"* (Scoring Notes commenter) — confirmed working.
- **VST3 with Note Expression:** can pass per-note pitch info, but instrument must implement it.
- **VST2 with VST tuning messages:** legacy, unreliable, typically only NotePerformer.
- **Pitch bend (expression map):** universal but only one bend per channel — chords with mixed cent deviations conflict.
- **MPE per-note pitch bend:** works for instruments that support it (some Spitfire, Output, etc.).

**How to avoid:**
1. **README troubleshooting section names confirmed-working engines:** *"HALion (Dorico's default sounds) and NotePerformer play cent deviations correctly out of the box. Third-party VST instruments may require Pitch Bend in the Expression Map or MPE support."*
2. **Validation phase uses HALion specifically.** If we validate against HALion only, we know the library is correct; failures elsewhere are engine-side.
3. **Don't try to solve this in the library.** It's a Dorico/VST contract issue, not ours.

**Warning signs:**
- User reports "playback isn't cent-accurate" with a third-party VST.
- Pitch bend works for melodic lines but breaks on chords (single-channel constraint).

**Phase to address:** Phase 4 (README troubleshooting); Phase 3 (validation against HALion specifically).

**Severity: MEDIUM** — outside our control but inside our README's responsibility.

---

### Pitfall 13: Forward references in section emission look like a bug to a future maintainer

**What goes wrong:**
A future contributor reads the generator output, sees `accidentalDefinitions` (section 3) referencing IDs that aren't declared until `compositeDefinitions` (section 7), concludes "this is wrong, sections need topological reordering" and "fixes" it. Result: file no longer matches Dorico's canonical export order; structural diffs against Dorico-exported files become noisy.

**Why it happens:**
Forward references genuinely look wrong by mainstream-XML conventions. Dorico actually does two-pass entityID resolution, so it's fine. ARCHITECTURE.md §"Anti-Pattern 1" already flags this.

**How to avoid:**
1. **Comment in `emit.py`:** at the top, comment explaining "Section emission order is dictated by Dorico's own canonical export. Do NOT topologically sort. Forward references are resolved by Dorico's two-pass parser."
2. **Test asserts the section order** matches the canonical list — any change to ordering fails the test.

**Warning signs:**
- Round-trip diff against template grows after a code change.
- Dorico import succeeds but section ordering looks suspicious.

**Phase to address:** Phase 1 (skeleton) — the `SECTION_ORDER` constant is one of the first definitions.

**Severity: LOW** — only matters if a future contributor "improves" it.

---

## Minor Pitfalls

### Pitfall 14: Locale-sensitive float formatting

**What goes wrong:**
Generator runs on a machine with a non-English locale, producing `100,000000` (comma decimal) instead of `100.000000` for `xScale`. Dorico parses it as malformed.

**Why it happens:**
Some Python f-string formatting paths historically respected locale, though this is now rare. `f"{value:.6f}"` is locale-independent, but `format(value, "n")` is not. `str(Fraction(...))` is also locale-independent.

**How to avoid:**
1. Hardcode float strings: emit `"100.000000"` as a literal, not `f"{100.0:.6f}"`. Per STACK.md's determinism checklist: *"Avoid floating-point formatting variance — emit `100.000000` as a string literal, not via f-string of a float."*
2. Never use `locale.format_string()` or `locale.atof()`.
3. CI runs the generator under `LC_ALL=C` and `LC_ALL=de_DE.UTF-8` — outputs must match.

**Warning signs:**
- Generator output differs across machines (specifically one with European locale).
- Dorico rejects the file with a parse error specifically on float fields.

**Phase to address:** Phase 1 (skeleton) — emit.py uses string literals.

**Severity: LOW** — rare in practice but trivially preventable.

---

### Pitfall 15: Python dict-ordering or set-iteration non-determinism

**What goes wrong:**
Generator output differs across runs because a `set()` is iterated in different orders, or a `dict` was built non-deterministically.

**Why it happens:**
`dict` insertion order is preserved since Python 3.7 (guaranteed since 3.8) and is fine. `set` iteration order is not deterministic across Python invocations (PYTHONHASHSEED randomization).

**How to avoid:**
1. **Never iterate a `set` for emission.** If dedup is needed, use `dict.setdefault` (which preserves first-insertion order) and iterate `.values()`.
2. **Sort all collections explicitly before iteration:** `for k in sorted(d.keys()):` if order matters.
3. CI runs the generator twice and diffs.

**Warning signs:**
- `diff /tmp/a.doricolib /tmp/b.doricolib` shows reordered entities across runs.

**Phase to address:** Phase 1 (skeleton) — main.py uses `dict` for dedup, not `set`.

**Severity: LOW** — easy to prevent with discipline.

---

### Pitfall 16: XML escaping for `<`, `>`, `&` in names

**What goes wrong:**
Hypothetical future user adds a custom accidental named `Sharp & Flat` or `<custom>`; ElementTree handles escaping via `Element.text` assignment, but a hand-written string-concat approach would corrupt the file.

**Why it happens:**
Our names are controlled (`Sharp +14`, `Flat -50`) and contain no XML-special characters. But defensive coding is cheap.

**How to avoid:**
1. **Always emit text via `Element.text = value`**, never via f-string concatenation into XML strings. ElementTree escapes automatically.
2. Avoid `ET.fromstring(f"<x>{value}</x>")` patterns.

**Warning signs:**
- File fails to parse with character-encoding errors.

**Phase to address:** Phase 1 (skeleton) — `emit.py` discipline.

**Severity: LOW.**

---

### Pitfall 17: Dorico 7+ future incompatibility

**What goes wrong:**
A future Dorico 7 ships a new `fileVersion` (e.g. 1.2000) and refuses to load 1.1450 files, or loads them with deprecated/silently-converted fields.

**Why it happens:**
Steinberg has historically broken library format across major versions: 5→6 had documented breakage (forum #987754 — "silent partial failure" with layout fields). 6→7 will likely repeat the pattern.

**How to avoid:**
1. **README states current target version explicitly:** "Tested on Dorico Pro 6.0 / 6.1 / 6.2.x. Dorico 7+ untested at release; please report issues."
2. **Treat Dorico 7 as a new generator target.** When 7 ships, open the working template in 7, save out a fresh tonality system, inspect that file's `fileVersion` and section ordering, treat as a separate variant. Per STACK.md's "Stack Patterns by Variant".
3. **Don't try to forward-compat now** — over-engineering for unknown future formats.

**Warning signs:**
- Dorico 7 release announcement.
- User reports import failures specifically on Dorico 7.

**Phase to address:** Phase 4 (README) — version compatibility matrix; future post-v1 work as needed.

**Severity: LOW** — future concern, not blocking v1.

---

### Pitfall 18: User shares a `.dorico` project file using cents accidentals; recipient doesn't have the library

**What goes wrong:**
User A composes a piece using `cents` accidentals and emails the `.dorico` file to user B. User B opens it without having imported `cents.doricolib`. Per Dorico's design, libraries are project-embedded — but only the entities actually used in the project are embedded. If User A's piece doesn't use every accidental in the cents library, User B's project won't have the unused ones available for editing.

**Why it happens:**
Dorico embeds the library in projects on save. Used entities travel; unused ones don't. This is correct behavior but surprising for users who expect "library = always-shippable bundle".

**How to avoid:**
1. **README explains:** "When you save a project using cents accidentals, the project embeds the library. Recipients can play and edit existing notes, but to add new accidentals from the full library, they need to import `cents.doricolib` themselves."
2. Recommend distributing the `.doricolib` alongside any `.dorico` file that uses it.

**Warning signs:**
- Recipient reports "I can play your file but can't add new cent accidentals."

**Phase to address:** Phase 4 (README troubleshooting).

**Severity: LOW** — a workflow note, not a bug.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode the three working template entities into the generator instead of round-tripping | Phase 1 ships faster | Round-trip fidelity test never written; structural drift goes undetected; emit.py quirks are unverified | Never — Phase 1's whole point is the round-trip anchor |
| Use `uuid4()` "for now, we'll switch later" | Generator runs immediately | Every existing user's library duplicates on update; recovery requires manual deletion | Never — uuid5 is no harder to type than uuid4 |
| Skip the deterministic-rebuild CI check | One less pre-commit hook | Determinism regressions slip in over time; bug surfaces months later when a user re-imports | Never — the check is 5 lines |
| Auto-reduce `pitchDeltaFromNatural` via `Fraction.numerator/Fraction.denominator` | Cleaner-looking values | Diverges from Dorico's canonical output; harder to debug ("is this 19/200 or 114/1200?") | Never — emit raw `n/1200` |
| Emit `<elem></elem>` instead of `<elem/>` for empty elements | Marginally easier ElementTree config | Diverges from template; might trigger Dorico's silent-drop parser quirks | Never — ElementTree does self-closing automatically |
| Skip the `xmllint` CI step | One less tool | Malformed XML reaches users; if it lands in `DefaultLibraryAdditions/` Dorico fails to launch | Never — xmllint is one shell command |
| Validate manually only against HALion, skip third-party VST testing | Faster validation | Third-party-VST users encounter playback issues; support burden | Acceptable for v1 (out of scope per PROJECT.md); revisit if external users report issues |
| Skip the round-trip test against the working template | Saves 1-2 hours of test setup | Phase 1 has no anchor for "did emit.py get the structure right?"; structural bugs surface in Phase 3 instead | Never — this is Phase 1's primary verification |
| Use raw f-strings for XML emission instead of ElementTree | Slightly more compact code | Loses automatic escaping; whitespace control becomes manual; encoding bugs likely | Never — ElementTree's escaping is the value prop |
| Inline pitch math at each call site instead of centralizing | Minor convenience | Pitfall 1 (off-by-100) more likely; harder to test | Never — single helper, single test |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Dorico Pro 6.x library import (Library Manager) | Drop file into `DefaultLibraryAdditions/` first, see Dorico fail to launch | Always test via Library Manager (per-project, recoverable on failure) before promoting to auto-load folder |
| Dorico Pro 6.x library import (Library Manager) | Forget to insert open/atonal key signature, conclude library is broken | README leads with this requirement (Pitfall 5) |
| `DefaultLibraryAdditions/` auto-load | Assume Dorico will skip malformed files | Dorico quits at startup on parse failure (forum #914859); test in Library Manager first |
| Dorico's tonality system change | Mid-project switch from cents to another system silently makes accidentals invisible while still affecting pitch | README documents this Steinberg-side behavior; users should commit to one tonality system per flow |
| HALion Sonic SE / Dorico stock sounds | Assume third-party VSTs receive cent info equivalently | HALion + NotePerformer are confirmed cent-accurate; third-party VSTs require pitch-bend Expression Map or MPE; README troubleshooting names this |
| MIDI export to DAW | Assume cent deviation passes through | Pitch info travels via VST3 Note Expression / VST2 microtuning / pitch bend; MIDI export is per-channel pitch bend by default; README notes the limitation |
| Sharing `.dorico` project files using cents | Assume recipient has full library access | Dorico embeds used entities only; recipients need `.doricolib` for editing access (Pitfall 18) |
| Updating the library (re-import v2) | Assume Dorico merges by name | Dorico matches strictly by entityID; rename = duplicate; uuid5 + locked keys is the only contract (Pitfall 6) |
| Cross-version (Dorico 5 → 6 → 7) | Assume backward compatibility | Documented breakage at major versions (forum #987754); pin to 6.x and treat 7 as separate target (Pitfall 17) |
| Dorico's accidental positioning | Assume per-note offset is possible | Dorico can't move accidentals vertically (forum #821103); offset is library-wide and `(-8, -12)` is the validated value |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Picker scrollability at 600 entries | Users complain panel is "unwieldy" (forum #832085 at much smaller scales) | Naming convention `Sharp +14` enables search-first navigation (FEATURES.md priority); names contain searchable substrings | At 600 entries (current scale); worse at 1000+; reason to reject double-accidental × cents expansion |
| Comma-separated `accidentalDefinitionIDs` string at 600 IDs | Long single XML element text content (~30 KB just for the ID list) | Confirmed format from template; Dorico parses fine; no perf workaround needed | Theoretically problematic at 10,000+ IDs; never in our scope |
| Generator runtime | None expected | Single pass; no quadratic operations; ~1411 entities runs in <1s | Stays linear through 10× growth |
| Re-import time on a project with library already present | Slow if Dorico does pairwise comparison | Not observed; entityID-based matching is hash-lookup | Stays fast |
| Search lag in panel with 600 entries | None reported in our scope; forum #832085 hints at slowness at lower scales | Naming convention helps narrow quickly | Likely fine at 600; revisit if reports surface |

---

## Security Mistakes

This is a static XML deliverable distributed to a single user (and possibly a small group). No network, no auth, no data ingestion. Traditional security concerns don't apply, but a few file-handling concerns:

| Mistake | Risk | Prevention |
|---------|------|------------|
| Generator script with arbitrary user-controlled keys (e.g. accepting `--label "<script>alert(1)</script>"`) | XML injection if labels are not escaped | ElementTree's `Element.text` assignment escapes automatically; never build XML by string concatenation |
| Distributing a `.doricolib` from an untrusted source | A maliciously-crafted `.doricolib` could exploit Dorico parser bugs | Out of scope (we're the source); user discipline if they ever import third-party libs |
| Committing the working template with embedded user-identifying UUIDs to a public repo | The template's UUIDs (`28c8da0eebd8441f8e626e070b6bfd45` etc.) are not secrets, but copying them to a public repo with provenance metadata could be undesirable | The template UUIDs are already random/non-identifying; deriving our UUIDs via uuid5 from a project-pinned namespace is the right pattern |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Empty panel after tonality system change | User thinks library is broken, abandons it | README leads with the open/atonal key signature requirement; troubleshooting section repeats it (Pitfall 5) |
| Dorico fails to launch after dropping file in `DefaultLibraryAdditions/` | User has to figure out which file to remove from a system folder | README recommends Library Manager primary, auto-load folder secondary; explicit "remove if launch fails" warning (Pitfall 4) |
| Inconsistent label baseline between Class B (with cent label) and Class C (text-only) accidentals | Visual rhythm broken in dense passages | Template's offsets `(-8, -12)` for Class B and `(18, -12)` for Class C are the validated values; Phase 3 spot-checks dense passages (Pitfall 9) |
| Non-zero accidentals show cent label, zero-deviation `Sharp` shows none | Visual height inconsistency in passages mixing both | Intentional and correct — users expect clean ♯ in C-major contexts; the inconsistency is the right tradeoff |
| Search behavior unverified at 600 entries | If search is slow or imprecise, users can't find specific accidentals | Phase 3 validation explicitly tests search ergonomics (`+14`, `Sharp -`, `Flat +50` queries) |
| Panel sort order based on pitch delta, not name | User mentally maps "near zero" to "near middle of list" — works for them | Confirmed correct Dorico behavior; FEATURES.md verified |
| User accidentally loses notes' accidental on tonality switch | Pitch correct, accidental invisible | README troubleshooting names this Steinberg behavior; users should pick one tonality system per flow |
| Cent labels in unexpected font when score has customized `font.defaulttext` | Visual surprise but functional | Document the dependency in README (Pitfall 11) |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Generator runs:** Often missing byte-identical determinism — verify with `diff <(python build.py --stdout) <(python build.py --stdout)`
- [ ] **`.doricolib` imports:** Often missing actual playback verification — verify by placing each visual class on a note and matching against a tuner
- [ ] **Cent labels render:** Often missing the on-pitch math check — verify `Sharp +14` plays at +114¢ from natural (NOT +14¢; see Pitfall 1)
- [ ] **Library Manager import succeeds:** Often missing the open/atonal key signature step — verify by switching to `cents` and confirming the panel populates
- [ ] **Re-import works:** Often missing duplicate detection — verify by importing twice and confirming the panel shows 600 entries, not 1200
- [ ] **All 600 accidentals exist:** Often missing the zero-deviation `Sharp`, `Flat`, `Natural` entries — verify the panel includes them and they render without cent labels
- [ ] **Class A/B/C composites correct:** Often missing the right composite shape per class — verify Class A (`Sharp` at 0¢) is glyph-only, Class B (`Sharp +14`) is glyph+text, Class C (`Natural -14`) is text-only
- [ ] **AccidentalSystem includes all IDs:** Often missing entries dropped silently — verify `<accidentalDefinitionIDs>` string contains exactly 600 comma-separated IDs
- [ ] **EntityID format is `kind.user.<32-hex>`:** Often wrong (missing `.user.` segment, or dashes in UUID) — verify with regex `^[a-z-]+\.user\.[0-9a-f]{32}$`
- [ ] **Forward references resolve:** Often broken if sections reordered — verify section emission order matches canonical (temperaments → accidentalSystems → accidentalDefinitions → tonalitySystemDefinitions → textDefinitions → glyphDefinitions → compositeDefinitions)
- [ ] **README documents open-key-signature requirement:** Often missing or buried — verify it's in the Quick Install walkthrough at step 2 or 3
- [ ] **README states Dorico Pro 6.x requirement:** Often missing or implicit — verify the first paragraph
- [ ] **README warns about `DefaultLibraryAdditions/` parse-failure-on-launch:** Often missing — verify the install section
- [ ] **README troubleshooting covers the top 5 silent failures:** open-key-sig, third-party VST playback, re-import duplicates, font customization, cross-tonality invisible accidentals
- [ ] **License file present:** Often forgotten — verify `LICENSE` exists at root
- [ ] **Version stated in README and XML comment:** Often inconsistent — verify they match
- [ ] **No `uuid4()` calls anywhere in generator:** Often slips in via copy-paste — verify with `grep -rn "uuid[14]\|uuid.uuid_" src/`
- [ ] **All XML elements use ElementTree (not string concat):** Often slips in for "just one" formatting case — verify by reviewing emit.py
- [ ] **CI runs generator twice and diffs:** Often skipped — verify CI config or pre-commit hook
- [ ] **Locale-independent float formatting:** Often slips in via `f"{x:.6f}"` of a float — verify emit.py uses string literals or locale-safe formatters

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Pitch-delta off-by-100 (Pitfall 1) | LOW (in code) / HIGH (for users with affected scores) | Fix the helper, re-run generator with same `PROJECT_NAMESPACE` (entityIDs unchanged → in-place update). Existing notes update silently. Notify users to re-import. |
| Non-deterministic UUIDs (Pitfall 2) | HIGH | Switch to uuid5; users with existing libraries must manually delete the old library entries from their projects, then re-import. There is no clean automatic migration. |
| Library imports but cent deviations lost (Pitfall 3) | MEDIUM | Compare generator output against working template; identify structural divergence; fix emit.py; re-run; users re-import (clean update via uuid5). |
| Dorico fails to launch (Pitfall 4) | LOW (for user) | User removes the file from `DefaultLibraryAdditions/`, relaunches Dorico, switches to Library Manager import. We fix the underlying parse issue and ship a new file. |
| Empty panel after tonality switch (Pitfall 5) | LOW | User inserts open/atonal key signature; problem resolves. |
| Re-import breaks existing notes (Pitfall 6) | MEDIUM-HIGH | If UUIDs match (deterministic), problem doesn't occur. If keys were renamed, users must manually re-apply accidentals to affected notes. There's no automated rescue. Mitigation: lock keys forever. |
| XML formatting drift (Pitfall 7) | LOW | Round-trip diff against template surfaces any drift; fix emit.py; re-ship. |
| Accidentals removed natural causes crash (Pitfall 8) | LOW | Add the natural accidental back to the AccidentalSystem; re-ship. |
| Cent labels collide visually (Pitfall 9) | LOW (per-score workaround) / MEDIUM (library-wide tweak) | Per-score: user manually adjusts in Engrave mode. Library-wide: tweak `(-8, -12)` offsets, ship update; users re-import. |
| VST instrument doesn't play microtonally (Pitfall 12) | N/A (out of our scope) | User switches to HALion or NotePerformer for cent-accurate playback. |
| Future Dorico version compat break (Pitfall 17) | MEDIUM | Open template in new version, save fresh, treat as new generator target; ship variant of `.doricolib` for the new version. Old version stays supported for 6.x users. |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Severity | Prevention Phase | Verification |
|---------|----------|------------------|--------------|
| 1. `pitchDeltaFromNatural` off-by-100 | CRITICAL | Phase 2 (math helper); Phase 3 (tuner check) | Unit test on helper; tuner spot-check on `Sharp +50` (= +150¢), `Flat -7` (= -107¢) |
| 2. Non-deterministic UUIDs | CRITICAL | Phase 1 (uuids.py from start) | Two-run byte-diff in CI; pre-commit hook |
| 3. Library imports but cent deviations lost | CRITICAL | Phase 1 (round-trip test) | Round-trip the 3 template entities byte-faithfully (modulo UUIDs); Phase 3 import + tuner |
| 4. Dorico fails to launch on parse error | HIGH | Phase 1 (XML escaping in emit.py); Phase 4 (README warning) | `xmllint --noout` in CI; Library Manager test before `DefaultLibraryAdditions/` |
| 5. Empty panel after tonality change (open key sig) | HIGH | Phase 4 (README leads with this) | README review; user-test the install walkthrough |
| 6. Re-import breaks existing notes | HIGH | Phase 1 (uuids.py + key conventions); Phase 4 (README) | Manual: import v1, place notes, regenerate, re-import, verify notes still play correctly |
| 7. XML formatting drift | HIGH | Phase 1 (centralized formatters in emit.py) | Round-trip diff; hex viewer indent check |
| 8. Removing natural accidental crashes Dorico | MEDIUM | Phase 2 (loop includes zero-deviation Natural) | Phase 3 import + note-input test |
| 9. Cent labels collide in dense passages | MEDIUM | Phase 3 (dense-passage spot-checks); Phase 4 (README workaround note) | Place chord with `Sharp -50`, `Natural +50`, `Flat +50` on one beat; eyeball |
| 10. Enharmonic-equivalent pitches confusion | MEDIUM | Phase 3 (validation); Phase 4 (README documentation) | Place `Sharp -50` and `Natural +50` on tied notes; verify same pitch, different visual |
| 11. Font override breaks cent labels | MEDIUM | Phase 4 (README documentation) | Test with a custom-font score |
| 12. VST instrument doesn't support microtonal playback | MEDIUM | Phase 3 (validate against HALion specifically); Phase 4 (README troubleshooting) | Tuner check against HALion stock sounds |
| 13. Forward references look like a bug | LOW | Phase 1 (comment in emit.py + section-order test) | Test asserts `SECTION_ORDER` matches canonical |
| 14. Locale-sensitive float formatting | LOW | Phase 1 (string-literal floats in emit.py) | CI runs with `LC_ALL=C` and `LC_ALL=de_DE.UTF-8`, diffs |
| 15. Dict/set ordering non-determinism | LOW | Phase 1 (use `dict.setdefault` for dedup, never iterate `set`) | Two-run byte-diff |
| 16. XML escaping for special chars | LOW | Phase 1 (use ElementTree's automatic escaping) | Code review |
| 17. Dorico 7+ future incompatibility | LOW | Phase 4 (README version compat matrix) | Document; revisit when Dorico 7 ships |
| 18. Sharing `.dorico` files cross-user | LOW | Phase 4 (README documents library-embedding behavior) | README review |

### Phase coverage summary

- **Phase 1 (skeleton):** Pitfalls 2, 3, 4, 7, 13, 14, 15, 16. Goal: get the structural and determinism foundation right; round-trip the working template.
- **Phase 2 (range):** Pitfalls 1, 8. Goal: correct math, complete coverage including zero-deviation entries.
- **Phase 3 (validation):** Pitfalls 1, 3, 4 (recovery test), 8, 9, 10, 12. Goal: physical verification with Dorico import + tuner + visual spot-checks.
- **Phase 4 (packaging):** Pitfalls 4, 5, 6 (documentation side), 9 (workaround note), 11, 12 (troubleshooting), 17, 18. Goal: README handles every documented silent-failure mode and version concern.

---

## Sources

### Primary — directly observed failure modes (HIGH confidence)

- [Custom Tonality System export doesn't work (#154743)](https://forums.steinberg.net/t/custom-tonality-system-export-doesnt-work/154743) — Daniel Spreadbury confirmed Dorico's import dropped text components silently; cent deviations lost on re-import. Root cause for Pitfall 3.
- [Doricolib not seen by default (Windows) (#914859)](https://forums.steinberg.net/t/doricolib-not-seen-by-default-windows/914859) — Steinberg moderator confirmed Dorico fails to launch on parse error in `DefaultLibraryAdditions/`. Root cause for Pitfall 4.
- [Libraries created in Dorico 5 don't seem to import properly to 6 (#987754)](https://forums.steinberg.net/t/libraries-created-in-dorico-5-dont-seem-to-import-properly-to-6/987754) — Confirmed silent partial failure pattern in Dorico 5→6 library imports. Root cause for Pitfall 3 (current era) and Pitfall 17.
- [Reusable Custom Accidentals (#944092)](https://forums.steinberg.net/t/reusable-custom-accidentals/944092) — Library loading conflicts when `userlibrary.xml` exists alongside `.doricolib` files. "Save as Default" crashes. Workflow gotchas.
- [Dorico Pro 2 crashes when inputting custom accidentals (#110776)](https://forums.steinberg.net/t/dorico-pro-2-crashes-when-inputting-custom-accidentals/110776) — Crash when natural accidental removed from tonality system. Root cause for Pitfall 8.
- [Tonality System not working in 5.1.10 (#893290)](https://forums.steinberg.net/t/tonality-system-not-working-in-5-1-10/893290) — User-reported confusion resolved by inserting open key signature first. Root cause for Pitfall 5.
- [I can't create a new tonality system and save it (#884737)](https://forums.steinberg.net/t/i-cant-create-a-new-tonality-system-and-save-it/884737) — Same root cause as #893290.
- [Microtonal problem (#109521)](https://forums.steinberg.net/t/microtonal-problem/109521) — Strict ordering required: select rest → tonality → atonal key signature. Root cause for Pitfall 5.
- [Position of custom accidentals (#821103)](https://forums.steinberg.net/t/postion-of-custom-accidentals/821103) — Daniel Spreadbury: "you can't move accidentals vertically." Root cause for Pitfall 9.
- [Microtonal playback with Kontakt 8, SWAM, and Falcon (#1030334)](https://forums.steinberg.net/t/microtonal-playback-with-kontakt-8-swam-and-falcon/1030334) — Third-party VST instruments lack straightforward microtonal communication. Root cause for Pitfall 12.

### Steinberg / Dorico documentation (HIGH confidence)

- [Microtonal accidentals (Dorico Pro v3 archive)](https://archive.steinberg.help/dorico/v3/en/dorico/topics/notation_reference/notation_reference_accidentals/notation_reference_accidentals_microtonal_c.html) — Confirms open/atonal key signature requirement and cross-tonality invisible-accidentals behavior.
- [Inputting microtonal accidentals (Dorico Pro v1 archive)](https://archive.steinberg.help/dorico/v1/en/dorico/topics/notation_reference/notation_reference_accidentals_microtonal_input_t.html) — Workflow reference.
- [Importing libraries (Dorico v5 archive)](https://archive.steinberg.help/dorico/v5/en/dorico/topics/library/library_importing_t.html) — Confirms entityID-based matching for re-imports.

### Stack/scoring industry sources (MEDIUM-HIGH confidence)

- [Microtonal playback in Dorico (Scoring Notes)](https://www.scoringnotes.com/reviews/microtonal-playback-in-dorico/) — HALion + NotePerformer confirmed cent-accurate; commenter notes NotePerformer "responds to the VST micro tuning messages."
- [Microtonal notation in Dorico (Scoring Notes)](https://www.scoringnotes.com/reviews/microtonal-notation-in-dorico/) — General overview; cents-precision capability confirmed.

### Auxiliary forum reports (MEDIUM confidence)

- [Popover for accidentals + accidental organizer (#832085)](https://forums.steinberg.net/t/popover-for-accidentals-plus-accidental-organizer/832085) — User pain at smaller-scale picker; basis for 600-entry concern.
- [Changing "Default Text Font" overrides "Default Music Text Font" (#877243)](https://forums.steinberg.net/t/changing-default-text-font-overrides-default-music-text-font/877243) — Documents cross-style override bug. Root cause for Pitfall 11.
- [Disappearing accidentals panel content (#987678)](https://forums.steinberg.net/t/disappearing-accidentals-panel-content/987678) — Known Dorico bug with toggling 'Play notes during note input'.

### Sibling research files (HIGH confidence — internal cross-reference)

- `/Users/taylorbrook/Dev/dorico tonality/.planning/research/STACK.md` — Schema details, deterministic UUID strategy, install paths, version compatibility matrix.
- `/Users/taylorbrook/Dev/dorico tonality/.planning/research/FEATURES.md` — Open-key-signature gating, naming convention, panel UX at scale.
- `/Users/taylorbrook/Dev/dorico tonality/.planning/research/ARCHITECTURE.md` — Three-class composite dispatch, `pitchDeltaFromNatural` math, forward-reference tolerance.
- `/Users/taylorbrook/Dev/dorico tonality/TonalitySystemStartTemplate.doricolib` — Working schema reference; byte-faithful comparison anchor.

---

*Pitfalls research for: Dorico cents tonality system (`.doricolib` library + Python generator)*
*Researched: 2026-05-01*
