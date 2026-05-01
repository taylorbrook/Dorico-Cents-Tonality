# Feature Research

**Domain:** Custom tonality-system library for Steinberg Dorico Pro 6.x — a static `.doricolib` deliverable plus README. Features here = user-visible capabilities of the imported library inside Dorico, plus distribution affordances (README, sample assets).
**Researched:** 2026-05-01
**Confidence:** HIGH on Dorico 6.x panel/popover UX (verified via Steinberg docs and forum threads), HIGH on HEJI as the closest published comparable, MEDIUM on exact panel-search behavior with ~600 entries (no forum thread tests this scale; users have only complained about "unwieldy" boxes at smaller scales).

---

## TL;DR for Roadmap

- The product is invoked via the **Key Signatures, Tonality Systems, and Accidentals panel** (Write mode → right-side panel). There is **no popover** for accidentals (Cmd+K is key signatures only) — feature was requested in 2023 and is "on the list" but unshipped as of 6.2.20.
- The panel sorts accidentals **by ascending pitch delta** and has a **search field** that filters by accidental `<name>`. **Naming convention is therefore load-bearing** — pick a string format that sorts numerically and searches sensibly.
- Recommended naming convention (specific, copy-pasteable): `<base> <signed-cents>` — e.g. `Sharp +14`, `Flat -50`, `Natural -7`, plus the three zero-deviation entries named `Sharp`, `Flat`, `Natural`. Rationale below in Table Stakes.
- The user must drop an **open/atonal key signature** into the score before any accidentals from a custom tonality system become available. README must say so explicitly — this is the single most common stumbling block in forum threads.
- Existing comparables (HEJI Plainsound, 24-EDO Stein-Zimmermann factory): no published cent-by-cent ±99¢ tonality system exists. This project is filling a gap.
- **README must cover:** Pro-only requirement, both install paths (DefaultLibraryAdditions vs. Library Manager per-project), the open-key-signature gotcha, the Setup-mode-applies-tonality detail, the playback expander/tuner verification step, license, and version compatibility.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users will assume exist. Missing these = "this library is broken."

| Feature | Why Expected | Complexity | Notes |
|---|---|---|---|
| Tonality system imports cleanly via Library Manager | Standard `.doricolib` workflow; if import errors out, users give up | LOW | Match `<fileVersion>1.1450</fileVersion>` exactly; structurally mirror the working template (already covered in STACK.md). |
| Tonality system imports cleanly via `DefaultLibraryAdditions/` drop | Power users want every project to inherit it; Steinberg's documented mechanism | LOW | Same file, different folder. **Caveat:** Dorico will refuse to launch if any file in `DefaultLibraryAdditions/` fails to parse — per-project import is the safer default to recommend. |
| Cent-accurate playback (±1¢) | Whole point of the library; users will run a tuner against it | LOW | Already specified by `pitchDeltaFromNatural = n/1200`. |
| Visible cent labels match playback | Trust: visible label "+14" must equal actual deviation | LOW | Single source of truth in the generator (one input cent integer drives both the text content and the rational). |
| Clean ♯/♭/♮ at 0¢ render with **no** cent label | A C-major passage shouldn't show "+0" everywhere | LOW | Distinct composite for zero-deviation cases (glyph-only, no text component). |
| Both enharmonic spellings available (sharp-side and flat-side) | Composers want `D♭ +50` *or* `C♯ -50` depending on harmonic context | LOW | Already in scope: ±99¢ around natural/sharp/flat overlaps cleanly. |
| Accidentals are searchable by typing in the panel's search field | Dorico 6 has this built in; users expect to type "+14" or "-50" and have one entry highlighted | LOW (naming-driven) | **Names must contain searchable substrings.** Recommended: `Sharp +14`, `Flat -50` etc. — a search for `+14` matches all three +14 variants (Natural+14, Sharp+14, Flat+14); a search for `Sharp +` filters to all sharp-side positives. |
| Accidentals sort sensibly in the panel (low → high pitch delta) | Dorico already does this; if it looks chaotic, naming is wrong | LOW | Sort is by `pitchDeltaFromNatural`, not by name — so the panel order is automatic. Users mentally scan top-to-bottom for "lower pitch" → "higher pitch", so the visual flow already works. |
| README explains the open/atonal key signature requirement | This is the #1 silent failure: users import the library, change tonality, see nothing in the panel, conclude it's broken | LOW (doc only) | Multiple forum threads (#109521, #157884, archived 5.x docs) confirm: tonality system change is gated behind an explicit key-signature insertion. |
| README states Dorico Pro 6.x requirement | Elements/SE users will try and fail; this is a Pro-only feature in practice | LOW (doc only) | One sentence at the top of the README. |
| README explains how to invoke the tonality system in Setup mode | Tonality is per-flow/per-instrument; users must know to apply it before the accidentals appear in the panel | LOW (doc only) | Part of the install walkthrough. |
| Deterministic re-imports (re-running generator updates, doesn't duplicate) | Users will iterate; if every re-import doubles their library, the artifact is unusable | LOW | Already specified via `uuid5(NAMESPACE, key).hex` — see STACK.md. |
| Tonality system has a clear, descriptive name in Dorico's tonality dropdown | Dropdown shows the `<TonalitySystemDefinition><name>` value; "New Tonality System" or "Untitled" is a usability failure | LOW | Locked: name = `cents` (per PROJECT.md key decisions). Recommend a slightly more descriptive variant like `Cents (±99¢ around 12-EDO)` for clarity in the dropdown — the user can override before shipping. |

### Differentiators (Worth Including)

These set the artifact apart from a bare `.doricolib`. Each is low-effort enough to be in scope; user value justifies inclusion.

| Feature | Value Proposition | Complexity | Notes |
|---|---|---|---|
| Sample test score (`cents-test.dorico`) shipped alongside the library | Users immediately see one of every accidental rendered, can hear the tuning ladder, and have a known-good template to copy from | MEDIUM | PROJECT.md currently has "bundled sample test score" in **Out of Scope** — flagging that this is the highest-leverage differentiator and worth reconsidering once core ships. The user can author it manually after one round of validation; it doubles as the validation artifact. |
| Cents reference chart in the README (markdown table or PDF) | "Which accidentals exist?" answered without launching Dorico; helps users plan before scoring | LOW | Auto-generate from the same Python script that builds the `.doricolib` — single source of truth. Table form: rows are cents −99 → +99, columns are Natural / Sharp / Flat, cell shows the resulting absolute cent offset from the natural. |
| Keyboard-shortcut recipe in README | Even though Dorico can't bind shortcuts to *specific* accidentals, users CAN bind shortcuts to "select next/previous accidental in panel" or use macro tools | LOW (doc only) | One-paragraph "Power-user tip" section. Honest framing: native shortcut binding to a microtonal accidental is a long-standing missing feature (forum #101640, #133160) — set expectations. |
| Recommended playback engine note (NotePerformer / HALion + microtonal-capable instruments) | Default HALion patches play microtonal info correctly but some VST instruments don't; users hit this and blame the library | LOW (doc only) | Scoring Notes' microtonal-playback review (2023) specifically calls out NotePerformer as compatible. One paragraph in README's Troubleshooting section. |
| MIDI export / DAW handoff guidance | Cent-accurate playback inside Dorico ≠ cent-accurate MIDI out; pitch-bend behavior depends on instrument config | LOW (doc only) | Brief Troubleshooting paragraph: "For pitch-accurate MIDI export, ensure your destination plugin supports MPE or per-note pitch bend." |
| Versioned releases (semver on the file + matching README) | Users will iterate; "which version do I have" is a real question once they share scores | LOW | `<TonalitySystemDefinition><name>cents v1.0</name>` is too noisy — instead include the version inside a comment at the top of the XML and in the README. |
| License file (MIT or CC0) | Composers redistribute scores publicly; ambiguous license = legal anxiety | LOW (doc only) | MIT recommended — permissive, allows derivatives, well-understood. Alternative: CC0 if the user wants pure public-domain semantics. |
| Pre-baked common key signatures (e.g., 12-TET major/minor at 0¢) inside the tonality system | Lets users write tonal music with the cents library loaded without manually authoring an open key sig every time | MEDIUM | **See "Anti-Features" — recommend NOT building this for v1.** The PROJECT.md keeps `customKeySignatures` minimal/empty, which is the right call. |

### Anti-Features (Deliberately NOT Building, With Reasoning)

Tempting to build, but cost > value or risk for v1.

| Feature | Why Tempting | Why NOT to Build | What to Do Instead |
|---|---|---|---|
| Pre-baked microtonal key signatures (e.g., "all sharps +14¢") | Looks like "completing the system"; reduces per-project setup | The cent space is infinite — picking a curated set is arbitrary, and Dorico already lets users author their own per-project. Adds significant XML volume. The empty-stub `customKeySignature` in the template is sufficient placeholder. | Leave one minimal empty `customKeySignature` stub (already in template). Document "users can author their own per project" in README. |
| Double-sharp / double-flat variants × cents (~400 more entries) | Symmetry; "complete coverage" | The picker would have ~1000 entries; ±99¢ around natural/sharp/flat already covers –199 to +199 cents with overlap. Diminishing returns become negative when the panel becomes unscrollable. | Stay in scope: ~600 entries (natural/sharp/flat × ±99¢ + 3 zero-deviation). |
| Sub-cent precision (e.g., tenths of a cent) | "Audiophile" framing; matches what Dorico's UI claims | Musical use cases plateau at integer cents; the panel would balloon to ~6000 entries; tuners can't reliably distinguish sub-cent differences in real instruments. | Stay at integer cents. PROJECT.md already excludes this. |
| HEJI / Sagittal-style ratio glyphs | Microtonal community familiarity; some users prefer ratio notation over cents | These are different notational philosophies — once you start, you compete with Plainsound's HEJI library and the unmaintained Sagittal Dorico work. The cents-label approach is the user's deliberate choice. | Stay with SMuFL standard glyphs + signed cent labels. Note in README: "If you want HEJI or Sagittal, see [Plainsound HEJI2 GitHub link]." |
| Custom signed-positive/unsigned/arrow conventions | Community variations exist (some prefer ↑14 / ↓14, some prefer unsigned positives) | Locked in PROJECT.md: `+N` / `-N` for unambiguous parsing and consistent visual rhythm. | Stay with `+14` / `-14`. |
| Per-instrument tonality variants | "What if a player wants different tuning per part?" | Dorico tonality systems are flow-scoped, not instrument-scoped, and the user can change tonality mid-flow. Adds no value for ±99¢ which already covers any single-line use case. | Document in README: "tonality is per-flow; change at any bar via the popover." |
| Bundling a public GitHub repo / website at v1 | "Open source from day one" | PROJECT.md scope explicitly says single-user tool first, public release deferred until validated. Premature distribution overhead. | Stay in scope: ship `.doricolib` + README in this repo only. Reassess after the user has used it on a real piece. |
| Keyboard-shortcut binding to specific accidentals | Power users will ask for it | Dorico does not support this natively (confirmed by Daniel Spreadbury, forum #133160, multi-year-open feature request). Building a workaround (e.g., a Stream Deck profile, AHK script) is out of scope for an XML library. | Document in README the existing limitation. Mention "select next/previous accidental in panel" key commands work and can be bound. |
| A custom installer / bash script | "Polish" | Drop-into-folder is already one step; an installer adds another moving piece that can break across OSes. | README shows the two install methods (drop into folder OR Library Manager import). |
| Automated regression tests against Dorico's import | "Real software has tests" | Dorico is closed-source and has no headless mode. Round-tripping requires GUI automation that's brittle. The script's deterministic byte-output is the best proxy we have. | Manual validation against a tuner, as PROJECT.md specifies. |

---

## Answers to the Specific Questions

### Q1 — Inside-Dorico user experience: how do users invoke a custom accidental?

**Confidence:** HIGH (Steinberg docs + multiple forum threads).

**The mechanism:**

1. **Setup mode** → The flow's tonality system is set on the project / per-flow. Library imports add the tonality system to the user library, and it then appears in the tonality-system selector.
2. **Write mode** → Open the **Key Signatures, Tonality Systems, and Accidentals panel** (right-side Notations toolbox).
3. The panel has three sections, top-to-bottom:
   - **Key Signatures** section
   - **Tonality System** section (dropdown to pick the active tonality system from the library)
   - **Accidentals** section (the picker)
4. **The Accidentals section displays accidentals in a list, sorted from lowest pitch delta at the top to highest at the bottom.**
5. **There is a Search field** that filters accidentals by `<name>` substring.
6. To apply: select one or more notes in the score, then click the desired accidental in the panel.

**What does NOT exist:**

- **No accidental popover.** Cmd+K / Shift+K opens the *key signature* popover — no equivalent exists for accidentals. This was formally requested in February 2023 (forum #832085); Daniel Spreadbury confirmed it's "on our list of things we plan to implement in future versions" but as of Dorico 6.2.20 it remains unshipped.
- **No keyboard binding to a specific custom accidental.** Long-standing missing feature (forums #101640, #133160). Users *can* bind shortcuts to "next accidental in panel" / "previous accidental in panel" but not to a specific one.
- **No drag-and-drop** of accidentals onto notes — the panel is click-driven.

**Discoverability pattern at scale (~600 accidentals):**

- The search field is the only practical way. Without it, users would scroll through all 600.
- One forum user already complained their accidental box at much smaller scale was "unwieldy" and "took a very long time" to navigate (#832085). Our 600 entries push this further — search-first naming becomes essential.
- Sort order is automatic by pitch delta — the user looking for "the sharp at +14¢" mentally maps "near-zero positive" → "near the middle of the list" and pages there, then types `Sharp +14` in search to pin it.

### Q2 — Naming conventions: what should accidentals be called?

**Confidence:** HIGH on what exists in the wild (HEJI uses ratio-based names, factory 24-EDO uses descriptive names like `accidentalQuarterToneFlatStein`); MEDIUM on what scales best for ~600 cent-labeled entries (no existing library reaches this density to compare against).

**Recommendation — exact string format:**

| Pitch delta | Name format | Examples |
|---|---|---|
| 0¢ (clean ♯/♭/♮) | `Sharp` / `Flat` / `Natural` | `Sharp`, `Flat`, `Natural` |
| Non-zero around natural | `Natural <signed-cents>` | `Natural +14`, `Natural -50`, `Natural +99`, `Natural -1` |
| Non-zero around sharp | `Sharp <signed-cents>` | `Sharp +14`, `Sharp -31`, `Sharp -99` |
| Non-zero around flat | `Flat <signed-cents>` | `Flat +50`, `Flat -7`, `Flat +99` |

**Why this format specifically:**

1. **Search-first.** Typing `+14` in the panel's search filters to exactly the three +14 variants. Typing `Sharp -` filters to all sharp-side negatives. Typing `Flat +50` pins one entry.
2. **Sort-stable inside a base group.** Dorico sorts the list by pitch delta (not by name), so within "all sharp-side accidentals" they already appear in cent order — names don't fight the sort.
3. **Visually parseable in the picker.** Each row shows the glyph + the name; reading left-to-right gives base accidental → signed cents in plain English.
4. **Matches the visible composite label.** The on-staff label is `+14` / `-14`; the panel name is `Sharp +14`. The cents portion is identical in both, reinforcing the user's mental model.
5. **Avoids special characters.** Don't use `♯`, `♭`, `♮` in names — Dorico's search is reasonably ASCII-tolerant but users on different keyboard layouts can't always type those characters.
6. **Avoids ambiguity at zero.** `Sharp` (no number) is unambiguously the standard 100¢ sharp; `Sharp +0` would be redundant and would dilute search.

**Alternatives considered:**

- `+14sharp` / `-31sharp` (cent-first): Awkward to read; loses parallelism with `Natural`.
- `S+14` / `F-50` / `N+7` (abbreviated): Compact but degrades search ergonomics.
- `Sharp 14¢ up` / `Flat 50¢ down` (verbose English): Verbose; the `¢` and word forms hurt searchability.

### Q3 — Key signature support: do microtonal users use them?

**Confidence:** HIGH on the technical requirement (every Steinberg microtonal doc says so); MEDIUM on community practice for cent-based work (small sample of forum threads).

**Findings:**

1. **Technical requirement:** Even to *use* a custom tonality system in a passage, users must input an open or atonal key signature. This is a hard gate — without it, the accidentals panel won't show your custom accidentals. Steinberg docs say so explicitly; multiple forum threads confirm it's the #1 source of "why isn't this working" confusion.
2. **Practical community pattern:** Microtonal composers using cents-based notation overwhelmingly write everything chromatically with explicit accidentals on each note. They use `open/atonal` as the key signature, not a custom microtonal one. The HEJI Plainsound documentation reinforces this — HEJI also expects per-note accidentals.
3. **When custom microtonal key signatures DO get used:** when a piece sits in a single non-12-EDO scale (e.g., a 31-EDO mode, a Pythagorean tuning) and the composer wants the recurring accidentals to be implied. This is *rare* for cent-based notation, where the deviation pattern changes constantly.

**Recommendation for v1:**

- Keep the empty `<customKeySignatures>` stub from the template (one entry with no accidentals — required by the schema, contains nothing).
- README must explicitly tell users: "Insert an **Open / Atonal** key signature at the start of any flow where you want to use cents accidentals (Shift+K → type `open` or `atonal`)."
- Do NOT pre-bake custom microtonal key signatures. (See Anti-Features.)

### Q4 — Existing alternatives: what's published?

**Confidence:** HIGH on what exists; MEDIUM on whether anything cent-based at this density has shipped before (didn't find one).

**Notable comparables:**

| Project | Approach | What's shipped | Relevance to this project |
|---|---|---|---|
| **Plainsound HEJI2** (Marc Sabat / Wolfgang von Schweinitz) | Just-intonation, ratio-based notation. ~50–100 accidentals representing 3-, 5-, 7-, 11-, 13-, 17-, 19-limit just intervals. | GitHub repo `PLAINSOUND/HEJI2`. Includes the SMuFL-encoded glyphs as a font, plus Dorico tonality system files. Distributed via `masa@plainsound.org` on request and at plainsound.org. Used by the contemporary-music academic community. | The single most relevant comparable. Confirms the .doricolib distribution model works in practice. **Different philosophy:** ratio notation, not cents. We're filling a different niche. |
| **Sagittal in Dorico** (community efforts) | Sagittal accidental notation — a unified microtonal symbol set covering many tuning systems via "shaft" and "flag" combinations. | Discussed on forum.sagittal.org; some users have hand-rolled tonality systems. No widely-distributed `.doricolib` that I could find. | Confirms the same workflow space; not direct competition. |
| **Dorico factory 24-EDO Stein-Zimmermann** | Quarter-tone accidentals: `accidentalQuarterToneFlatStein`, `accidentalThreeQuarterTonesFlatZimmermann`, etc. | Ships with Dorico. ~6 accidentals. | Reference for how Steinberg names/structures factory tonality systems. Naming style is descriptive (`accidentalQuarterToneSharpStein`), but our cents-based system has no analog to lean on — we're inventing the convention for our density. |
| **Dorico factory 12-EDO** | Default. ♯, ♭, ♮, 𝄪, 𝄫. | Always present. | Baseline; we're an additive alternative. |
| **31-EDO / Tartini-style tonality systems** | A few users have shared XML snippets in forum threads (e.g., #969610 walks through a 72-EDO setup) | No polished published library | Confirms the practice of custom tonality systems in Dorico is alive but boutique. |

**What none of them have done:**

- No published library covers the full ±99¢ cent space around all three base accidentals (~600 entries) with text-label-driven cent display.
- This project occupies an unfilled niche: integer-cent precision without committing to a specific tuning system. That positioning is the differentiator vs. HEJI/Sagittal.

### Q5 — README expected content: concrete section list

**Confidence:** HIGH (synthesized from the BensDoricoEarlyMusicBundle README, HEJI README pattern, and forum guidance).

**Section list — strict order:**

1. **Project name + one-sentence description.**
   `Cents — A Dorico Pro 6 tonality system for cent-accurate microtonal notation using standard SMuFL accidentals plus signed cent labels.`
2. **Requirements.**
   - Dorico **Pro** 6.0 or later. Will not load on Dorico 5, Elements, or SE.
   - macOS or Windows.
3. **What's in this package.**
   - `cents.doricolib` — the tonality system library file.
   - `README.md` (this file).
   - `LICENSE` — MIT (or chosen license).
   - (Optional, if differentiator added) `cents-test.dorico` — sample test score.
4. **Quick install (recommended, per-project):**
   1. Open your Dorico project.
   2. **Library → Library Manager**.
   3. In the Compare panel, select **Dorico project** and choose `cents.doricolib`.
   4. Tick the imports you want; click **Import**.
5. **Permanent install (auto-load in every project):**
   - **macOS:** copy `cents.doricolib` into `~/Library/Application Support/Steinberg/Dorico 6/DefaultLibraryAdditions/`. Create the folder if it doesn't exist.
   - **Windows:** copy into `%APPDATA%\Steinberg\Dorico 6\DefaultLibraryAdditions\`.
   - **Important:** If Dorico fails to launch after this, remove the file — Dorico aborts on parse errors in this folder.
6. **Usage walkthrough — your first cents-accidental note:**
   1. **Setup mode** → confirm your flow uses default settings (no custom tonality yet).
   2. **Write mode** → press **Shift+K**, type `open`, press Enter. This inserts an open/atonal key signature **(required)**.
   3. Open **Key Signatures, Tonality Systems, and Accidentals** panel (Notations toolbox, right-side panel icons).
   4. In the **Tonality System** section, click the dropdown → choose **`cents`**.
   5. Select a note in the score.
   6. In the **Accidentals** section, type `+14` in the search field. Click **`Sharp +14`** (or whichever variant you want).
   7. Verify playback against a tuner — the note should sound exactly 14 cents above the standard sharp pitch (i.e., 114 cents above the natural).
7. **Naming convention — quick reference.**
   - Brief table mirroring Q2 above, so users know what to type.
8. **Cents reference chart.**
   - Either inline (markdown table — 199 rows is borderline acceptable; abbreviate with key examples and a "see appendix" pointer) or a separate `cents-reference.md` file.
9. **Troubleshooting.**
   - "I changed the tonality system but the panel is empty." → Insert an open/atonal key signature first.
   - "I imported the file but it's not in the dropdown." → You imported into the project but didn't enable it; or you dropped into `DefaultLibraryAdditions/` and Dorico is using a per-project override; see Library Manager.
   - "The cent labels aren't visible / look ghosted." → Known Dorico bug after toggling 'Play notes during note input' (forum #987678); restart the project.
   - "Playback isn't cent-accurate." → Confirm your VST instrument supports microtonal pitch info. HALion/NotePerformer work out of the box; some third-party libraries don't.
   - "MIDI export to my DAW isn't pitch-accurate." → Ensure destination plugin supports MPE or per-note pitch bend.
10. **Version compatibility.**
    - Dorico Pro 6.0 / 6.1 / 6.2.x: tested.
    - Dorico 5 and below: not supported (file format incompatibility).
    - Future Dorico 7+: untested at release; report issues.
11. **License.**
    - MIT recommended. One paragraph + link to `LICENSE` file.
12. **Credits.**
    - Built with [PROJECT_NAME] by [author]; uses SMuFL standard accidentals via Bravura.
13. **Changelog.**
    - `1.0 — initial release. ~600 accidentals, ±99¢ around natural/sharp/flat plus zero-deviation ♯/♭/♮.`

### Q6 — Differentiating features: anything beyond core generation?

Highest-leverage differentiators (already in the table above; here's the priority ranking):

1. **Sample test score** — biggest user-experience win, doubles as validation artifact. Worth pulling out of Out of Scope after v1 ships.
2. **Cents reference chart** — generated by the same script; trivial cost.
3. **Troubleshooting section in README** — entirely doc-only; addresses the open/atonal key-signature gotcha and the playback-engine question proactively.
4. **License + Versioning** — table-stakes for any redistribution, even single-user.

NOT recommended for v1:
- Public GitHub release (deferred per PROJECT.md).
- Custom installer (drop-in is one step already).
- Pre-baked microtonal key signatures (anti-feature).

### Q7 — Anti-features: what to deliberately NOT build

See the Anti-Features table above. Top three:

1. **No double-sharp/double-flat × cents.** Picker bloat with no marginal value.
2. **No pre-baked custom microtonal key signatures.** Choices are arbitrary; users can author them per-project.
3. **No alternative sign conventions.** `+N` / `-N` is locked.

---

## Feature Dependencies

```
Dorico Pro 6.x install
    └──prerequisite──> Library import (Library Manager OR DefaultLibraryAdditions/)
                          └──prerequisite──> "cents" tonality system selectable in dropdown
                                                └──prerequisite──> Open/atonal key signature in flow
                                                                      └──enables──> Accidentals panel populates with ~600 entries
                                                                                      └──enabled-by──> Naming convention (search ergonomics)
                                                                                      └──enabled-by──> Pitch-delta sort order (vertical scan)
                                                                                                          └──enables──> Click-to-apply accidental
                                                                                                                          └──verified-by──> Playback ±1¢ vs. tuner

README install instructions ──enables──> Successful first-run
README open-key-signature note ──prevents──> Most-common silent-failure mode
README troubleshooting ──prevents──> Support burden
Sample test score ──validates──> All accidentals render + play correctly in one place

Cents reference chart ──enhances──> Naming convention (users can pre-look-up before searching)
```

### Dependency Notes

- **Open/atonal key signature requirement is a HARD gate.** Without it, the entire library is invisible to the user. README must lead with this.
- **Naming convention determines panel usability.** Pitch-delta sort is automatic (Dorico-controlled), but search depends entirely on `<name>` strings. The naming choice in Q2 is therefore a feature, not a cosmetic detail.
- **Library Manager import vs. DefaultLibraryAdditions are alternative paths**, not cumulative. README must present both clearly with their tradeoffs (per-project vs. global; Library Manager safer because parse failures don't crash launch).

---

## MVP Definition

### Launch With (v1) — strict minimum

- [x] `cents.doricolib` with all ~600 accidentals (in scope per PROJECT.md)
- [x] Naming convention: `Sharp +14`, `Flat -50`, `Natural -7`, plus zero-deviation `Sharp` / `Flat` / `Natural`
- [x] Empty `<customKeySignatures>` stub
- [x] Deterministic generator output
- [x] README covering: requirements, both install paths, open-key-sig walkthrough, naming reference, basic troubleshooting, version compat, license

### Add After Validation (v1.x)

- [ ] **Sample test score** (`cents-test.dorico`) showing all accidentals on staves with playback verification — trigger: after first real-piece use exposes any gaps
- [ ] **Cents reference chart** as a standalone file generated by the same script — trigger: if user asks for it once, ship it
- [ ] **Expanded troubleshooting** based on real questions encountered

### Future Consideration (v2+)

- [ ] Public GitHub release with download instructions — trigger: PROJECT.md says "until validated"
- [ ] Companion Stream Deck / AHK / Keyboard Maestro recipes for power-user invocation — trigger: user finds the panel-click flow painful in real composition
- [ ] HEJI / Sagittal interop layer — trigger: external user requests it
- [ ] Dorico 7 retest and potential reissue — trigger: Dorico 7 release

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---|---|---|---|
| ~600 cents accidentals correctly generated | HIGH (the product) | MEDIUM (already scoped) | P1 |
| Naming convention `<base> <signed-cents>` | HIGH (search ergonomics) | LOW (string formatting) | P1 |
| Deterministic re-imports | HIGH (iteration safety) | LOW (uuid5) | P1 |
| README install + walkthrough | HIGH (first-run success) | LOW (writing) | P1 |
| README open-key-signature gotcha | HIGH (prevents #1 silent failure) | LOW (one paragraph) | P1 |
| README troubleshooting | MEDIUM (support burden) | LOW (writing) | P1 |
| Version + License in README | MEDIUM (legal/clarity) | LOW (one paragraph each) | P1 |
| Cents reference chart | MEDIUM (planning aid) | LOW (script-generated) | P2 |
| Sample test score | HIGH (validation + onboarding) | MEDIUM (manual authoring) | P2 |
| Public GitHub repo | LOW for v1 (single-user) | MEDIUM | P3 |
| Pre-baked microtonal key signatures | LOW (anti-feature) | MEDIUM | NEVER |
| Double-accidental × cents | LOW (anti-feature) | HIGH | NEVER |
| Custom popover for accidentals | HIGH if Dorico had it | HIGH (we can't build into Dorico) | NEVER (out-of-system) |

**Priority key:**

- **P1:** Must ship in v1.
- **P2:** Add post-launch when validated.
- **P3:** Future / revisit only on demand.
- **NEVER:** Anti-feature; documented reason for not building.

---

## Competitor Feature Analysis

| Feature | Plainsound HEJI2 | Dorico factory 24-EDO | Our Approach |
|---|---|---|---|
| Notation philosophy | Ratio-based (just intonation) | Quarter-tone (Stein-Zimmermann symbols) | Cents-label (12-EDO + signed cent text) |
| Number of accidentals | ~50–100 | ~6 | ~600 |
| Naming style | Ratio-based names + ASCII codes | `accidentalQuarterToneFlatStein`-style descriptive names | `Sharp +14`, `Flat -50`, etc. (search-friendly) |
| Custom font required | Yes (HEJI font) | No (Bravura) | No (Bravura — uses standard SMuFL `accidentalSharp/Flat/Natural`) |
| Key signature requirement | Open/atonal | Open/atonal | Open/atonal (same constraint) |
| Sample score / test materials | Yes (provided on request) | N/A (factory) | **Recommend adding post-v1** |
| README/docs | Plainsound user guide PDF + GitHub README | Steinberg manual section | Markdown README in repo |
| Distribution | Via email request + GitHub | Bundled with Dorico | Single repo file (deferred public release) |
| License | (Verify on contact) | Steinberg proprietary | MIT recommended |
| Open/closed source | Open | Closed | Open (single-user first, public deferred) |
| Update cadence | Versioned (HEJI2 2020 with 2025 additions) | Bundled with Dorico releases | Versioned in changelog |

**Positioning summary:** This project is the cents-based counterpart to HEJI's ratio-based approach — both serve composers who want microtonal precision with score-readable notation, but they differ in notational philosophy. Stein-Zimmermann is the same idea at a much coarser quantization (quarter-tone). Our niche — integer-cent ±99¢ around three base accidentals — is unfilled in the published library landscape.

---

## Sources

### Highest-confidence (Steinberg official + working references)

- [Inputting microtonal accidentals — Dorico Pro 4.3 manual (current text matches 6.x behavior)](https://www.steinberg.help/r/dorico-pro/4.3/en/dorico/topics/notation_reference/notation_reference_accidentals/notation_reference_accidentals_microtonal_input_t.html)
- [Microtonal accidentals — Dorico v5 archive (confirms open/atonal key sig requirement)](https://archive.steinberg.help/dorico/v5/en/dorico/topics/notation_reference/notation_reference_accidentals/notation_reference_accidentals_microtonal_c.html)
- [Key Signatures, Tonality Systems, and Accidentals panel — Dorico Pro 6.1](https://www.steinberg.help/r/dorico-pro/6.1/en/dorico/topics/write_mode/write_mode_notations_input/write_mode_key_signatures_tonality_systems_accidentals_panel_r.html)
- [Library Manager — Dorico Pro 6.1](https://www.steinberg.help/r/dorico-pro/6.1/en/dorico/topics/library/library_manager_r.html)
- [Importing libraries — Dorico Pro 4.3](https://www.steinberg.help/r/dorico-pro/4.3/en/dorico/topics/library/library_importing_t.html)
- [Importing tonality systems — Dorico Pro v5 archive](https://archive.steinberg.help/dorico_pro/v5/en/dorico/topics/notation_reference/notation_reference_tonality_systems/notation_reference_tonality_systems_importing_t.html)
- [Edit Tonality System dialog — Dorico Pro v5 archive](https://archive.steinberg.help/dorico_pro/v5/en/dorico/topics/library/library_tonality_systems_edit_tonality_system_dialog_r.html)
- [SMuFL Stein-Zimmermann accidentals (24-EDO) reference](https://w3c.github.io/smufl/latest/tables/stein-zimmermann-accidentals-24-edo.html)
- [Tip: Change the Tonality System — Dorico Blog (2019)](https://blog.dorico.com/2019/04/tip-change-the-tonality-system/)

### Forum threads — community workflow + UX expectations (MEDIUM confidence)

- [Popover for accidentals + accidental organizer (#832085)](https://forums.steinberg.net/t/popover-for-accidentals-plus-accidental-organizer/832085) — confirms popover does NOT exist; on the wishlist; community pain point at scale.
- [Microtonal accidentals key commands (#101640)](https://forums.steinberg.net/t/microtonal-accidentals-key-commands/101640) — confirms keyboard binding to specific accidentals is unsupported.
- [Dorico 3 — keyboard shortcuts for microtonal accidentals (#133160)](https://forums.steinberg.net/t/dorico-3-keyboard-shortcuts-for-microtonal-accidentals/133160) — same.
- [Question about inputting microtonal accidentals (#687855)](https://forums.steinberg.net/t/question-about-inputting-microtonal-accidentals/687855) — confirms the open/atonal key signature requirement; outlines the panel-driven workflow.
- [Poor editing and filtering in microtonal tonality systems (#869316)](https://forums.steinberg.net/t/poor-editing-and-filtering-in-microtonal-tonality-systems/869316) — confirms users hit pain points at hundreds-of-accidentals scale; "Filter Notes by Pitch doesn't work in microtonal" is a known gap.
- [Disappearing accidentals panel content (#987678)](https://forums.steinberg.net/t/disappearing-accidentals-panel-content/987678) — known Dorico bug; relevant to README troubleshooting.
- [Reusable Custom Accidentals (#944092)](https://forums.steinberg.net/t/reusable-custom-accidentals/944092) — community use of `.doricolib` for custom accidentals; how files are shared.
- [Extended Helmholtz-Ellis (HEJI) Accidentals Update (#698060)](https://forums.steinberg.net/t/extended-helmholtz-ellis-heji-accidentals-update/698060) — HEJI integration discussion; "cannot import a tonality system on top of an existing one" pain point.
- [HEJI tonality system issue (#766730)](https://forums.steinberg.net/t/heji-tonality-system-issue/766730) — confirms HEJI is the de facto microtonal `.doricolib` comparable.
- [Help creating new tonality system (#969610)](https://forums.steinberg.net/t/help-creating-new-tonality-system/969610) — 72-EDO walkthrough; confirms accidental panel ordering and naming conventions in practice.
- [Doricolib not seen by default (Windows) (#914859)](https://forums.steinberg.net/t/doricolib-not-seen-by-default-windows/914859) — confirms the `DefaultLibraryAdditions/` install path and parse-error launch-failure behavior.
- [Custom key signatures (#108573)](https://forums.steinberg.net/t/custom-key-signatures/108573) — discussion of the customKeySignatures element.

### Comparables — published microtonal libraries

- [PLAINSOUND/HEJI2 GitHub repository](https://github.com/PLAINSOUND/HEJI2) — closest direct comparable; ratio-based.
- [Plainsound Harmonic Space Calculator User Guide (PDF)](https://www.plainsound.org/HEJI/Plainsound%20Harmonic%20Space%20Calculator.pdf) — example of microtonal Dorico documentation patterns.
- [HEJI2020 site](https://heji.plainsound.org/) — HEJI2 distribution.

### Industry reviews

- [Microtonal notation in Dorico — Scoring Notes (2018, updated)](https://www.scoringnotes.com/reviews/microtonal-notation-in-dorico/) — overview of Dorico's microtonal capabilities.
- [Microtonal playback in Dorico — Scoring Notes](https://www.scoringnotes.com/reviews/microtonal-playback-in-dorico/) — playback engine compatibility (HALion, NotePerformer).
- [Practical Tips for Notating Non-Western Scales and Microtonality in Dorico — The Music Theory Professor](https://themusictheoryprofessor.com/practical-tips-for-notating-non-western-scales-and-microtonality-in-dorico/) — practitioner workflow notes.

### Sibling research file (already complete)

- `/Users/taylorbrook/Dev/dorico tonality/.planning/research/STACK.md` — schema, install paths, version compatibility, file-format internals.

---

*Feature research for: Dorico cents tonality system (`.doricolib` library + README)*
*Researched: 2026-05-01*
