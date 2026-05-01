# Project Research Summary

**Project:** Cents — Custom Tonality System for Dorico
**Domain:** XML build-tooling for a Steinberg Dorico Pro 6.x `.doricolib` library — single-artifact deliverable (no runtime stack), built by a Python stdlib generator, distributed alongside a README
**Researched:** 2026-05-01
**Confidence:** HIGH

## Executive Summary

This is a **single-artifact XML build project**: a Python 3.11+ stdlib generator that emits one deterministic `.doricolib` file (~1411 entities) plus a README. The deliverable extends Dorico Pro 6.x with ~600 microtonal accidentals — every integer cent in ±99¢ around natural / sharp / flat — using standard SMuFL glyphs paired with signed cent text labels. The schema is well-understood (the user's working `TonalitySystemStartTemplate.doricolib` is a hand-validated, byte-faithful reference) and Dorico's import path is documented; the engineering challenge is **byte-faithful XML emission with deterministic UUIDs**, not novel algorithm work.

The recommended approach is a **5-module Python stdlib generator** (`uuids.py` for `uuid5(PROJECT_NAMESPACE, key)`, `entities.py` for frozen dataclasses, `compose.py` for a **three-class composite dispatcher** — glyph-only / glyph+text / text-only — `emit.py` for byte-faithful ElementTree serialization, `main.py` orchestrator) with a **Phase 1 round-trip test against the working template** as the structural anchor. The template happens to include exactly one of each composite class (Natural is glyph-only, `-14` is text-only, `#-31` is glyph+text), making Phase 1 a complete-coverage exercise of every code path before scaling. Stack is locked: `xml.etree.ElementTree` (not lxml — no XSD exists; lxml's value props are irrelevant here), `uuid.uuid5` deterministic UUIDs, raw `n/1200` rational strings (do not auto-reduce), tab indentation, lowercase booleans, six-decimal float strings as literals.

The dominant risks are **silent failures**, not crashes. Three are critical and ship-blocking: (1) the **off-by-100 pitch math trap** — `pitchDeltaFromNatural` is relative to natural pitch, not the base accidental, so `Sharp +14` is `114/1200` not `14/1200`, and getting this wrong produces a library that looks correct and plays exactly 100¢ wrong on every sharp/flat-base accidental; (2) Dorico's documented **silent text-component drop on import** (forum #154743) when XML structure deviates from canonical, mitigated by byte-faithful template round-trip; (3) **non-deterministic UUIDs** would cause every re-import to duplicate ~600 entities. Two more are HIGH severity: (4) the **open/atonal key signature requirement** is the #1 silent failure for any Dorico custom tonality system — without it the panel stays empty and users abandon the library, so the README must lead with this; and (5) **`DefaultLibraryAdditions/` parse failures crash Dorico at launch**, so README must recommend Library Manager as the primary install path. Mitigations are well-defined and live in specific phases.

## Key Findings

### Recommended Stack

Python 3.11+ stdlib only (`xml.etree.ElementTree`, `uuid`, `fractions`, `pathlib`, `argparse`); zero runtime dependencies in the shipped artifact. `lxml`, `jinja2`, and `xmltodict` are explicitly ruled out — lxml's value (XPath, XSD validation) is irrelevant because **no public Dorico XSD exists**, and templating tools fight determinism. Validation is empirical: byte-diff against the user's working template + Dorico import + tuner check.

**Core technologies:**
- **Python 3.11+** — `ET.indent()` (tab-faithful), `tomllib`, deterministic dict ordering. 3.12 is the sweet spot.
- **`xml.etree.ElementTree` (stdlib)** — element-first model maps cleanly to the entity-heavy schema; preserves attribute order; auto-escapes via `Element.text`. ElementTree's `indent(space="\t")` produces Dorico's tab indentation.
- **`uuid.uuid5(PROJECT_NAMESPACE, key)`** — deterministic, RFC 9562 compliant. Same `(kind, key)` pair → same UUID forever → re-imports update existing entries instead of duplicating. **`PROJECT_NAMESPACE` must be pinned once and never rotated.**
- **SMuFL standard accidentals** — codepoints `0xE260` (flat), `0xE261` (natural), `0xE262` (sharp) via `font.defaultmusic` (Bravura). Stable across SMuFL 1.0 → 1.18.
- **`fileVersion 1.1450`** — Dorico Pro 6.x library format; will not load on Dorico 5 or earlier. Pro-only in practice (Elements/SE lack tonality-system editing).

### Expected Features

Domain analysis found **no published microtonal Dorico library covers the full ±99¢ cent space** around the three base accidentals — Plainsound HEJI2 is ratio-based (~50–100 entries), the factory 24-EDO Stein-Zimmermann set is ~6 entries. **This project occupies an unfilled niche** in the Dorico ecosystem at unprecedented entity density (~600 accidentals, 1411 total entities). At this scale, **panel-search ergonomics become a load-bearing UX concern** that the naming convention must address.

**Must have (table stakes):**
- Tonality system imports cleanly via Library Manager with `<fileVersion>1.1450</fileVersion>`
- Cent-accurate playback (±1¢) — `pitchDeltaFromNatural = n/1200`
- Visible cent label always matches actual playback delta
- Clean ♯/♭/♮ at 0¢ render with **no** cent label (so C-major passages don't show "+0" everywhere)
- Both enharmonic spellings available (`C♯ -50` and `D♭ +50` both exist)
- Naming convention `<base> <signed-cents>` — `Sharp +14`, `Flat -50`, `Natural -7`, plus zero-deviation `Sharp` / `Flat` / `Natural`. Enables search-first navigation in the panel (typing `+14` matches all three +14 variants; typing `Sharp +` filters to all sharp-side positives).
- Deterministic re-imports (re-running generator updates, doesn't duplicate)
- README states Pro-only requirement, both install paths, and the open/atonal key signature gating step

**Should have (differentiators, low-effort):**
- Cents reference chart (auto-generated by the same Python script)
- Troubleshooting section in README addressing the top silent-failure modes
- License (MIT) + version stated in README and XML comment
- Sample test score (`cents-test.dorico`) — currently in PROJECT.md Out of Scope but flagged as the highest-leverage post-v1 differentiator

**Defer (v2+):**
- Public GitHub release (PROJECT.md says "single-user tool first, public release deferred until validated")
- Sample test score
- Stream Deck / AHK / Keyboard Maestro power-user recipes
- HEJI / Sagittal interop layer

**Anti-features (deliberately NOT building):**
- Double-sharp / double-flat × cents (~400 more entries, picker bloat, no marginal value — the ±99¢ range already covers –199¢ to +199¢ with overlap)
- Sub-cent precision (musical use cases plateau at integer cents; would balloon picker to ~6000 entries)
- Pre-baked custom microtonal key signatures (arbitrary curation; users author per-project)
- Alternative sign conventions (locked to `+N` / `-N`)
- Custom installer (drop-in is one step already)

### Architecture Approach

Two architectures live in the project: (a) the **internal entity graph** of the emitted XML (7 sections, 7 entity types, atomic render unit = 4–7 entities per accidental), and (b) the **Python generator's 5-module structure** that emits it. The central design idea is the **three-class composite dispatcher** in `compose.py` — every accidental falls into one of three visual classes determined by `(base, cents == 0)`: **Class A (glyph-only)** for zero-deviation, **Class B (glyph + text)** for sharp/flat-base at non-zero cents (with `relativeAttachment` `kBaselineRight ↔ kBaselineLeft`, offset `(-8, -12)`), **Class C (text-only)** for natural-base at non-zero cents (text positioned by direct `xOffset/yOffset = (18, -12)`, no glyph, no relativeAttachment). The working template includes one of each class, making Phase 1 round-trip a complete-coverage test of every emission path.

**Major components (Python generator):**
1. **`uuids.py`** — `PROJECT_NAMESPACE` pinned constant + `entity_id(kind, key)` helper. Single chokepoint for determinism.
2. **`entities.py`** — Frozen dataclasses (`@dataclass(frozen=True, slots=True)`) per entity type, each with `to_xml() → ET.Element`. Immutable-from-creation prevents mid-emission mutation.
3. **`compose.py`** — `build_accidental(base, cents) → AccidentalBundle` three-class dispatcher. Pure data construction, no XML emission.
4. **`emit.py`** — Byte-faithful ElementTree serialization. Owns every formatting quirk (tab indent, lowercase `true`/`false`, `(0, 0)` tuple syntax, raw `n/1200` rationals, `0xE262` capital-X hex, `100.000000` six-decimal floats, `, ` comma-space CSV).
5. **`main.py`** — Orchestrator. Builds singletons, loops `(natural, sharp, flat) × range(-99, 100)`, dedupes by entityID via `dict.setdefault`, groups into seven canonical sections, calls `emit.write`.

**Major components (entity graph in the .doricolib):**
- **Singletons (3 entities):** `TonalitySystemDefinition` ("cents"), `TemperamentDefinition` (12-EDO), `AccidentalSystem` (CSV of all ~600 accidental IDs).
- **Per-accidental atoms:** 600 `AccidentalDefinition` (carries `pitchDeltaFromNatural` + `compositeID`), 600 `CompositeDefinition` (one per accidental, **not shared** — every composite is unique).
- **Shared primitives:** 3 `GlyphPrimitiveEntityDefinition` (sharp/flat/natural), 198 `TextPrimitiveEntityDefinition` (one per signed cent value −99..−1, +1..+99, shared across the three base accidentals at that cent value).

**Section emission order is fixed** by Dorico's own canonical export: temperaments → accidentalSystems → accidentalDefinitions → tonalitySystemDefinitions → textDefinitions → glyphDefinitions → compositeDefinitions. **Forward references work** (Dorico is two-pass) — do NOT topologically sort.

### Critical Pitfalls

The four research files together carry strong, specific recommendations. The pitfalls list is led by silent failures — things that look right but ship broken.

1. **CRITICAL — Off-by-100 in `pitchDeltaFromNatural`.** The field is delta from natural pitch, not from base accidental. `Sharp +14` is `114/1200`, NOT `14/1200`. Getting this wrong silently miscalibrates every sharp/flat-base accidental by exactly ±100¢. **Avoid:** centralize in `pitch_delta_numerator(base, cents)` helper with `{"natural": 0, "sharp": 100, "flat": -100}[base] + cents`; unit-test against hand-calculated values; tuner-check `Sharp +50` (=+150¢), `Flat -7` (=−107¢) in Phase 3.

2. **CRITICAL — Silent text-component drop on import** (Dorico bug, forum #154743). `.doricolib` imports cleanly with no error, accidentals appear in panel, but cent deviations are silently lost — Dorico's lenient parser drops fields when XML structure deviates from canonical. **Avoid:** Phase 1 round-trip test re-emits the three template entities byte-faithfully (modulo entityIDs); always emit `<scalingRules array="true"/>`, `<relativeAttachments array="true"/>` (self-closing) even when empty; match section order exactly; Phase 3 tuner-check (don't trust "no error dialog").

3. **CRITICAL — Non-deterministic UUIDs duplicate everything on re-import.** `uuid.uuid4()` in any code path means re-running the generator produces different UUIDs, and re-importing adds 600 *more* accidentals alongside the existing ones. **Avoid:** `uuid.uuid5(PROJECT_NAMESPACE, key)` exclusively; `PROJECT_NAMESPACE` pinned once, never rotated; CI step diffs two consecutive runs; `grep -rn "uuid[14]" src/` returns nothing.

4. **HIGH (gating) — Open/atonal key signature requirement.** The #1 silent failure: user picks "cents" from the tonality dropdown and sees an empty accidentals panel, concludes the library is broken, abandons it. Without an open or atonal key signature in the flow (Shift+K → "open"), the panel doesn't populate. Confirmed by Steinberg docs and forum threads #109521, #893290, #884737. **Avoid:** README leads with this in the Quick Install walkthrough at step 2 or 3; troubleshooting section repeats it.

5. **HIGH — `DefaultLibraryAdditions/` parse failures crash Dorico at launch.** If a `.doricolib` in this folder fails to parse, Dorico hangs at startup or quits. Confirmed by Steinberg moderator on forum #914859. **Avoid:** README recommends Library Manager (per-project, recoverable on failure) as primary install method, `DefaultLibraryAdditions/` as power-user option with explicit "remove if launch fails" warning; `xmllint --noout` in CI; ElementTree's automatic escaping (no string-concat XML).

Additional HIGH-severity pitfalls covered in PITFALLS.md: re-import key-rename breaks notes already placed (lock keys forever), XML formatting drift (tabs vs. spaces, lowercase booleans, raw rationals), and forward-reference "fixing" by future maintainers (comment in `emit.py` warning against topological sort).

## Implications for Roadmap

Based on combined research, the natural phase progression is four phases. The dependency structure is clean — no hidden cross-phase coupling — and Phase 1's template round-trip exercises every code path before Phase 2 scales up.

### Phase 1: Generator Skeleton + Template Round-Trip
**Rationale:** The working template includes one of each composite class (Natural=Class A, `-14`=Class C, `#-31`=Class B), so reproducing it byte-faithfully (modulo entityIDs) is a complete-coverage test of every emission path. Locks down deterministic UUIDs, byte-faithful XML, three-class dispatcher, and section ordering before any scale-up. This is the structural anchor for everything that follows.
**Delivers:** Working `uuids.py`, `entities.py`, `compose.py`, `emit.py`, `main.py` skeleton; round-trip test passing; CI step diffing two consecutive runs.
**Addresses:** Determinism (Pitfall 2), silent text-component drop (Pitfall 3), XML formatting drift (Pitfall 7), forward-reference confusion (Pitfall 13), locale/dict-order non-determinism (Pitfalls 14–15), XML escaping (Pitfall 16).
**Avoids:** Three of three CRITICAL pitfalls' structural causes.

### Phase 2: Range Expansion to ±99¢
**Rationale:** Once Phase 1 proves the three-class dispatcher works for any one accidental, Phase 2 is purely a parameter sweep over `(natural, sharp, flat) × range(-99, 100)` plus the three zero-deviation entries. No new schema discovery; only the math helper and the AccidentalSystem CSV scale.
**Delivers:** Full ~600 AccidentalDefinitions, ~600 CompositeDefinitions, ~198 TextDefinitions, 3 GlyphDefinitions; AccidentalSystem with all 600 IDs comma-space–joined; the `cents.doricolib` artifact.
**Uses:** `compose.py` three-class dispatcher; `pitch_delta_numerator(base, cents)` helper.
**Implements:** Section-grouped emission with deduplication by entityID.
**Addresses:** Off-by-100 pitch math (Pitfall 1 — the CRITICAL math trap lives here), zero-deviation Natural inclusion (Pitfall 8 — Dorico crashes if missing).

### Phase 3: Validation (Dorico Import + Tuner + Visual)
**Rationale:** Physical verification is the only ground truth — no public XSD, no Dorico headless mode. Spot-checks must cover all three composite classes, the off-by-100 trap (`Sharp +50` should play +150¢), enharmonic-equivalent pairs (`Sharp -50` and `Natural +50`), dense-passage collisions, and panel-search ergonomics at 600 entries (unprecedented scale; empirically unverified).
**Delivers:** Validated `.doricolib`; documented behavior at scale; bugs captured for fix.
**Addresses:** Pitch math correctness (Pitfall 1), import correctness (Pitfall 3), visual collisions (Pitfall 9), enharmonic behavior (Pitfall 10), VST microtonal compatibility against HALion (Pitfall 12).

### Phase 4: README + Packaging
**Rationale:** Documentation is the single biggest leverage point against silent-failure user abandonment. The 13-section README structure (per FEATURES.md §Q5) handles every documented silent-failure mode: open-key-signature gating, both install paths with the launch-crash warning, naming reference, third-party VST troubleshooting, font-customization caveat, cross-tonality invisible-accidentals behavior, version compatibility matrix, license. Could in principle parallelize with Phase 2/3 but troubleshooting benefits from validation learnings.
**Delivers:** README.md, LICENSE (MIT), version comment in XML; optional cents reference chart.
**Addresses:** Open-key-signature gotcha (Pitfall 5 — HIGH), `DefaultLibraryAdditions/` launch crash warning (Pitfall 4), re-import behavior (Pitfall 6), font override (Pitfall 11), VST playback (Pitfall 12), Dorico 7+ future (Pitfall 17), `.dorico` file sharing (Pitfall 18).

### Phase Ordering Rationale

- **Phase 1 before Phase 2:** Template round-trip surfaces emission bugs against a known-good 3-entity reference. Skipping straight to Phase 2 (it's the same code, just looped) loses the byte-faithful comparison anchor; structural bugs would surface in Phase 3 instead, with 600 entries to debug across.
- **Phase 2 before Phase 3:** Validation needs the full file to test panel-search ergonomics at scale (the 600-entry concern is empirically unverified).
- **Phase 3 before Phase 4 (loosely):** README troubleshooting benefits from real validation findings, but the open-key-signature gotcha and install-path warnings are documented up-front and could be drafted in parallel.
- **No hidden dependencies that would re-order phases.** The one coupling worth noting: if Phase 3 reveals a Dorico rejection of an emission detail, the fix lives in Phase 1's `emit.py` and ripples forward. Mitigation: Phase 1's round-trip test runs continuously.

### Research Flags

**Phases needing deeper research during planning:** **None.** All four research files are HIGH confidence with the working template as ground truth. The schema, SMuFL codepoints, Python tooling, install paths, naming conventions, three-class dispatcher, off-by-100 math, and silent-failure modes are all specifically characterized.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Generator Skeleton):** STACK.md + ARCHITECTURE.md fully specify the 5-module structure, UUID pattern, and emission quirks.
- **Phase 2 (Range Expansion):** Pure parameter sweep over Phase 1's primitives; FEATURES.md locks naming convention; PITFALLS.md specifies the math helper.
- **Phase 4 (README + Packaging):** FEATURES.md §Q5 provides the complete 13-section structure with content for each.

**Phases that may surface unknowns during execution:**
- **Phase 3 (Validation)** — search ergonomics at 600 entries is empirically unverified at this scale (no public Dorico tonality system has reached this density). Mitigation strategy is the naming convention; if it fails, the fix is name format adjustments in `compose.py`, no architectural change.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Schema verified element-by-element against the user's working template; SMuFL codepoints are stable spec; Python stdlib choices are uncontroversial. MEDIUM only on `fileVersion 1.1450 → Dorico 6.x` mapping (Steinberg doesn't publish a version table) but inferred from working template. |
| Features | HIGH | Steinberg docs + multiple forum threads cover panel UX, tonality-system workflow, install paths. MEDIUM only on exact panel-search behavior at 600 entries (unprecedented scale; mitigation is naming convention). |
| Architecture | HIGH | Entity graph cross-checked element-by-element against the template; emission order is template-canonical (Dorico's own export order); three-class composite dispatcher maps cleanly to template's three sample entities; generator module breakdown driven by deliverable shape and determinism requirement. |
| Pitfalls | HIGH | Off-by-100 math, silent-text-drop, UUID determinism, open-key-signature gating, `DefaultLibraryAdditions` launch crash all confirmed by Steinberg docs / Daniel Spreadbury forum posts / multiple independent reports. MEDIUM on collision behavior at 600-entry scale and Dorico-7-future compat. |

**Overall confidence:** **HIGH**

### Gaps to Address

These cannot be resolved by further desk research; they require physical validation in Phase 3.

- **Panel-search ergonomics at 600 entries.** No published Dorico tonality system has reached this density; forum users complained about "unwieldy" pickers at much smaller scales. Mitigation: naming convention `Sharp +14` enables substring search. Validation: Phase 3 tests `+14`, `Sharp -`, `Flat +50` queries explicitly. If insufficient, fix is name-format adjustment in `compose.py` — no architectural change.
- **Cent-label collisions in dense passages.** Template's `(-8, -12)` and `(18, -12)` offsets are validated for sparse layouts. Validation: Phase 3 places `Sharp -50` + `Natural +50` + `Flat +50` chord (all three are or near +50¢) on a single beat; eyeball. Workaround if needed: per-score Engrave-mode adjustment documented in README.
- **Third-party VST microtonal playback.** HALion and NotePerformer confirmed cent-accurate; Kontakt 8 / SWAM / Falcon report mixed support (forum #1030334). Out of project scope; README troubleshooting names confirmed-working engines.
- **Dorico 7+ future compatibility.** Not yet released. Steinberg has historically broken library format across major versions (5→6 documented). Mitigation: pin to 6.x explicitly in README; treat Dorico 7 as a separate generator target when it ships.
- **Enharmonic-equivalent pitch behavior.** `Sharp -50` and `Natural +50` are the same absolute pitch; Dorico's enharmonic-resolution logic with mid-microtonal accidentals at boundary cases is unverified. Phase 3 places both on tied notes; verify same pitch, distinct visual.

## Sources

### Primary (HIGH confidence)
- Working template `/Users/taylorbrook/Dev/dorico tonality/TonalitySystemStartTemplate.doricolib`
- Sibling research files (`STACK.md`, `FEATURES.md`, `ARCHITECTURE.md`, `PITFALLS.md`)
- SMuFL standard accidentals spec (U+E260–U+E26F)
- Python `xml.etree.ElementTree` documentation
- Python `uuid` documentation (RFC 9562 / uuid5)
- Steinberg forum #154743 (silent text-component drop, Daniel Spreadbury confirmation)
- Steinberg forum #914859 (`DefaultLibraryAdditions/` parse failure crashes Dorico)
- Steinberg forum #109521 (open/atonal key signature requirement)

### Secondary (MEDIUM confidence)
- Steinberg help: Key Signatures, Tonality Systems, and Accidentals panel (Dorico Pro 6.1)
- Steinberg help: Edit Tonality System dialog, Custom accidentals (v5 archives)
- Steinberg forum #832085 (no popover; pain at smaller-scale picker)
- Steinberg forum #987754 (5→6 silent partial failure)
- Steinberg forum #1030334 (third-party VST microtonal limitations)
- PLAINSOUND/HEJI2 GitHub repository (closest published comparable, ratio-based)
- Scoring Notes — Microtonal playback in Dorico (HALion + NotePerformer cent-accurate)

### Tertiary (LOW confidence)
- Dorico 6 release announcement (`fileVersion 1.1450 → Dorico 6.x` inferred)
- Steinberg forum #877243 (font-override interaction, single source)
- Panel-search performance at 600 entries — no source at this scale; empirical only
