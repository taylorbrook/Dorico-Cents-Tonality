# Phase 2: Range Expansion to ±99¢ - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate the production `cents.doricolib` — a single tonality system named "cents" containing exactly 597 accidentals (3 zero-deviation + 594 non-zero across `(natural, sharp, flat) × ±99¢`) wrapping one 12-EDO `TemperamentDefinition` and one `AccidentalSystem`. Total emitted entity count: 1411. The off-by-100 trap (Pitfall 1) is defeated by a centralized `pitch_delta_numerator(base, cents)` helper that is the only place pitch math lives.

**In scope:** parameter sweep over the Phase 1 Class A/B/C dispatcher; introduction of `pitch_delta_numerator`; the production `cents.doricolib` as the deliverable; a `--mode` CLI flag preserving Phase 1's template round-trip; structural + sampled-byte tests at the new scale.

**Explicitly NOT in scope (deferred to later phases):**
- Physical Dorico import + tuner playback validation → Phase 3
- Panel-search ergonomics at 597 entries → Phase 3
- Dense-passage cent-label collision behavior → Phase 3
- README, install paths, troubleshooting, LICENSE → Phase 4
- Double-sharp/double-flat × cents (rejected at PROJECT.md scope)

</domain>

<decisions>
## Implementation Decisions

### Glyph definitions
- **D-01:** All three SMuFL glyph definitions (Sharp `0xE262`, Flat `0xE260`, Natural `0xE261`) emit `<parentEntityID/>` (self-closing, empty). This decouples the library from any factory `glyph.accidentalNatural` entityID Steinberg might shift between Dorico point releases (per STACK.md's recommendation). Diverges from Phase 1's template-faithful behavior, which had Natural inherit `glyph.accidentalNatural` — that quirk lives only in Phase 1's template-mode regression path.

### `<accidentalDefinitionIDs>` ordering
- **D-02:** Order all 597 IDs in the comma-space string by `pitchDeltaFromNatural` ascending: -199¢ → +199¢. The three zero-dev entries land at their math positions (Flat at -100¢, Natural at 0¢, Sharp at +100¢). Mirrors Dorico's automatic panel sort and is the easiest order to skim when debugging the file in a text editor.
  - Natural-base entries from -99..-1 occupy the front of the natural cluster around 0¢; sharps cluster around +100¢; flats around -100¢. Overlapping enharmonic regions (e.g., `Sharp -50` and `Natural +50` both at +50¢) are adjacent in the string.

### Phase 1 round-trip preservation
- **D-03:** `build_template_three()` and the byte-faithful template round-trip test stay alive as a permanent regression check on the Class A/B/C dispatcher's structural fidelity against the hand-validated `TonalitySystemStartTemplate.doricolib`. They are reachable via `--mode template` (see D-04). Phase 1's template-specific quirks — Natural's literal `0/24` pitch delta, Natural's inherited `glyph.accidentalNatural` parent, Class B's `accidentalSharp` empty parent, the `New Composite` names, the `*-template` key suffixes — are preserved verbatim *only* in template mode and do NOT leak into cents mode.

### CLI surface
- **D-04:** `build.py` grows a `--mode` flag with two values: `cents` (default) and `template`.
  - `python build.py --out cents.doricolib` → production sweep (1411 entities, 597 accidentals).
  - `python build.py --mode template --out template-roundtrip.doricolib` → Phase 1's three-entity Psychography build.
  - The default is `cents` so the production path is the obvious one; template mode is opt-in for the round-trip test.

### Zero-deviation entry naming
- **D-05:** Internal keys for the three zero-deviation entries in cents mode are bare base strings: `sharp`, `flat`, `natural`. Their displayed names are `Sharp`, `Flat`, `Natural` (no cent suffix). The non-zero entries use canonical `<base><signed-cents>` keys: `sharp+14`, `flat-50`, `natural-7`, etc. Bare-base zero-dev keys slot in cleanly as the implicit-zero variants; no collision with the `*-template` suffixed Phase 1 keys.
  - **THIS LOCKS FOREVER.** Per Pitfall 6, any rename of these key strings creates duplicate entityIDs on user re-import. The strings `sharp`, `flat`, `natural`, plus the `<base><signed-cents>` template, are a permanent stability contract.

### Pitch math centralization (GEN-05)
- **D-06:** Introduce `pitch_delta_numerator(base: Literal["natural","sharp","flat"], cents: int) -> int` that returns `{natural: 0, sharp: 100, flat: -100}[base] + cents`. Returns the numerator only; callers format as `f"{n}/1200"`. The helper is the **only** place pitch math lives. Cents-mode emission MUST go through it. Template mode preserves Phase 1's literal pitch-delta strings (`0/24`, `-14/1200`, `69/1200`) and does NOT call the helper — that's intentional template fidelity.
  - Hand-calculated unit tests pin: `("sharp", 14) → 114`, `("sharp", -50) → 50`, `("flat", -7) → -107`, `("flat", 50) → -50`, `("natural", -7) → -7`, `("sharp", 0) → 100`, `("flat", 0) → -100`, `("natural", 0) → 0`, plus boundary cases `("sharp", 99) → 199`, `("flat", -99) → -199`, `("natural", 99) → 99`.

### Test strategy at the 1411-entity scale
- **D-07:** Layered approach:
  1. **Unit tests on `pitch_delta_numerator`** — the GEN-05 hand-calculated cases above.
  2. **Structural invariants on the full cents-mode output** — total entity count = 1411; exactly 597 `AccidentalDefinition`s (594 non-zero + 3 zero-dev); exactly 198 `TextPrimitiveEntityDefinition`s (one per signed cent value -99..-1, +1..+99); exactly 3 `GlyphPrimitiveEntityDefinition`s; exactly 1 `TonalitySystemDefinition` named "cents"; exactly 1 `TemperamentDefinition` with the standard 12-EDO divisions; `<accidentalDefinitionIDs>` is a single comma-space string containing exactly 597 IDs in pitch-delta order; section emission order matches `SECTION_ORDER`; well-formed XML (`xmllint --noout` passes).
  3. **Sampled byte-faithful snapshots** — pin ~6–10 representative `AccidentalDefinition` + `CompositeDefinition` blocks against committed expected snippets: a Class A zero-dev (`Sharp` at +100¢), a Class B sharp+text (`Sharp +14` → 114/1200), a Class B sharp+text negative (`Sharp -50` → 50/1200, the off-by-100 trap), a Class B flat+text (`Flat -7` → -107/1200), a Class C natural+text (`Natural -7` → -7/1200), a Class C natural+text positive (`Natural +50` → 50/1200, the enharmonic of Sharp -50), and boundaries `Sharp +99` (→ 199/1200), `Flat -99` (→ -199/1200).
  4. **Phase 1's full template round-trip stays** as a regression check on Class A/B/C dispatcher byte-fidelity (executed via `--mode template`).
  5. **Two-run determinism test** continues to apply to cents mode (re-running must produce a byte-identical file).
- Avoid a several-hundred-KB full-output snapshot — drift detection is achieved more cheaply by structural invariants + sampled byte snapshots.

### Pitfall coverage owed by this phase (per PITFALLS.md)
- **D-08:** Phase 2 is responsible for two pitfalls:
  - **Pitfall 1 (off-by-100, CRITICAL)** → defeated by D-06's centralized helper + unit tests.
  - **Pitfall 8 (Natural absent from AccidentalSystem, MEDIUM)** → defeated by an explicit structural invariant in the test suite asserting all three zero-dev entries (Sharp, Flat, Natural) appear in the AccidentalSystem's ID string.

### Claude's Discretion
- Module structure: whether `pitch_delta_numerator` lives in a new `src/cents_generator/pitch.py` module or inside an existing module (`compose.py`, `constants.py`, `entities.py`). Researcher / planner may choose based on cohesion. The user's only requirement is *centralization* — single source of truth for pitch math.
- The exact name of the cents-mode equivalent of `build_template_three()` (e.g., `build_cents_full_sweep()`, `build_cents_library()`, `build_cents()`).
- How `AccidentalSystemDef.entity_id` and `TonalitySystemDef.entity_id` keys are derived for the new "cents" tonality system — a sensible default is `cents` (bare) for both, mirroring the bare-base zero-dev convention. Once shipped, locks forever per Pitfall 6.
- Section-internal ordering for `accidentalDefinitions`, `compositeDefinitions`, and `textDefinitions` — a sensible default is to mirror D-02's pitch-delta order for accidentalDefinitions and compositeDefinitions; for textDefinitions, ascending by signed cent value (-99..-1, +1..+99).
- Cut-out tuples for the 596 newly-emitted accidentals — Phase 1 emitted Natural's template-derived non-zero cut-outs `(0, 0)`, `(0.192, 2.116)`, `(0, 0)`, `(0.476, 0.512)` in template mode only. For cents-mode emission, default to `(0, 0)` for all four corners on every accidental (per template's Class B/C convention; see PITFALLS.md Pitfall 9 — collision shapes are MEDIUM and out of v1 scope).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project locks (NOT to be re-litigated)
- `.planning/PROJECT.md` — locked decisions (tonality named "cents", 12-EDO temperament, ±99¢ around natural/sharp/flat ≈600 accidentals, always-signed labels, deterministic UUIDs).
- `.planning/REQUIREMENTS.md` — 13 phase-2 requirements: GEN-05, TON-01..06, VIS-01..05, PLAY-01.
- `.planning/ROADMAP.md` §"Phase 2: Range Expansion to ±99¢" — phase goal + 5 success criteria; total entity count 1411 is fixed there.
- `.planning/STATE.md` §"Accumulated Context" — Phase 1 deliverable md5, three-class dispatcher, helper formula, total entity count.

### Research (load on planning)
- `.planning/research/PITFALLS.md` §"Pitfall 1" — the off-by-100 math trap; helper signature + unit-test cases.
- `.planning/research/PITFALLS.md` §"Pitfall 8" — Natural must be present in AccidentalSystem (crash trap).
- `.planning/research/PITFALLS.md` §"Pitfall 6" — key conventions lock forever; D-05 zero-dev keys must never be renamed.
- `.planning/research/PITFALLS.md` §"Pitfall 7" — XML formatting drift (the centralized formatters in `emit.py` must continue to be the only emission path).
- `.planning/research/STACK.md` §"Determinism Strategy" — `uuid5(PROJECT_NAMESPACE, key)` is the only UUID source; PROJECT_NAMESPACE never rotates.
- `.planning/research/STACK.md` §"Schema Details" + §"Stack Patterns by Variant" — the all-empty `<parentEntityID/>` recommendation is from here (D-01).
- `.planning/research/FEATURES.md` §"Naming convention" — `Sharp +14`, `Flat -50`, `Natural -7`, plus zero-dev `Sharp` / `Flat` / `Natural` (locked).
- `.planning/research/ARCHITECTURE.md` §"Anti-Pattern 1" — section emission order is canonical, not topological; forward references are intentional.

### Working anchor
- `TonalitySystemStartTemplate.doricolib` — hand-validated against Dorico Pro 6.x; the byte-faithful structural anchor for `--mode template`. Phase 2 must not modify it.

### Phase 1 implementation (build on, don't duplicate)
- `src/cents_generator/uuids.py` — `PROJECT_NAMESPACE`, `entity_id(kind, key)` (do NOT rotate the namespace; do NOT change the key→UUID derivation).
- `src/cents_generator/constants.py` — `FILE_VERSION`, `SECTION_ORDER`, `SMUFL_SHARP/FLAT/NATURAL`, `TEMPERAMENT_12EDO_DIVISIONS`, `KIND_*`, `FONT_DEFAULT_MUSIC`, `FONT_DEFAULT_TEXT`. Phase 2 reuses verbatim.
- `src/cents_generator/entities.py` — frozen dataclasses for all 9 entity / sub-entity types. Phase 2 reuses verbatim.
- `src/cents_generator/compose.py` — `build_class_a/b/c()` + `AccidentalBundle`; the dispatcher Phase 2 sweeps over. The `_glyph_for()` helper currently encodes Natural-inherits / Sharp-Flat-empty in `_GLYPH_SPEC` — Phase 2 needs cents-mode glyphs to all-empty (D-01). Note in compose.py line 64–66 already flags this transition.
- `src/cents_generator/emit.py` — XML emission with all the Pitfall 7 formatters (tabs, lowercase booleans, raw `n/1200`, `0xE26X` hex, six-decimal floats, comma-space ID lists, self-closing empty arrays). Phase 2 reuses verbatim.
- `src/cents_generator/main.py` — `run()`, `main()`, `build_template_three()`. Phase 2 adds the cents-mode counterpart and the `--mode` CLI flag (D-04); preserves `build_template_three()` (D-03).
- `build.py` — current CLI shim. Phase 2 wires `--mode`.
- `tests/test_template_roundtrip.py` — Phase 1's byte-faithful round-trip; survives as the template-mode regression check (D-03).
- `tests/test_uuid_snapshot.py` — pinned UUIDs for the 13 template-mode entityIDs; Phase 2 grows a separate cents-mode UUID snapshot for a sampled subset of the 1411 production entityIDs (D-07).
- `tests/test_determinism.py` — two-run byte-diff harness; Phase 2 extends it to cover cents mode.
- `tests/test_compose.py`, `tests/test_emit_format.py`, `tests/test_entities.py`, `tests/test_uuids.py` — existing unit tests Phase 2 builds on.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`build_class_a/b/c()` (compose.py)** — the entire dispatcher Phase 2 iterates. Three-class dispatch is already correct; Phase 2 supplies pitch-delta strings + names + keys + label_text per accidental.
- **`AccidentalBundle.entities` (compose.py:117)** — orchestrator-friendly tuple of all non-None entities; deduplication happens at the orchestrator layer by entityID.
- **`_text_for(label)` (compose.py:86)** — already produces a `TextDef` keyed by the label string. Phase 2's 198 dedup'd `TextDef`s come for free if cents-mode iteration reuses this helper for each cent label and dedupes by entityID at the orchestrator.
- **`emit.write()` (emit.py)** — production XML emitter; signature already takes ordered tuples of accidentals/composites/glyphs/texts plus the singletons. Phase 2 just feeds it larger tuples in pitch-delta order.
- **`entity_id(kind, key)` (uuids.py)** — deterministic UUID derivation; Phase 2 produces every cents-mode entityID via this single function with the keys named in D-05 (and the Claude's-discretion AccidentalSystem/TonalitySystem keys).
- **`SECTION_ORDER` (constants.py)** — canonical section emission order; emit.py iterates this. Phase 2 must NOT touch it (Pitfall 13 — forward references are intentional).
- **`TEMPERAMENT_12EDO_DIVISIONS` (constants.py)** — the standard `200/100/200/200/100/200/200`; Phase 2 reuses verbatim for the cents-mode `TemperamentDef`.

### Established Patterns
- **Entity-key strings are the uuid5 input and lock forever** (Pitfall 6). The keys defined in D-05 (`sharp`, `flat`, `natural`) plus the canonical `<base><signed-cents>` template (`sharp+14`, `flat-50`, `natural-7`, etc.) are a permanent stability contract.
- **The entire orchestrator dedupes by entityID** (Phase 1 main.py pattern). Phase 2's larger sweep keeps this — sharing the 198 TextDefs across the three bases at each cent value is achieved naturally because `entity_id(KIND_TEXT, "+14")` produces the same UUID regardless of which base accidental triggered the call.
- **Class assignment is purely a function of `(base, cents == 0)`**: `(natural, 0) | (sharp, 0) | (flat, 0)` → Class A; `(sharp|flat, ≠0)` → Class B; `(natural, ≠0)` → Class C. Phase 2's sweep is a single pass over `[(b, c) for b in ("natural","sharp","flat") for c in range(-99, 100)]` (where `c == 0` triggers Class A and skips text emission for the bases that don't use one).
  - Strictly: zero-dev entries are 3, not 9 — Sharp/Flat/Natural at 0¢ each, no `Sharp +0` etc. Iteration must NOT emit `<base> +0` / `<base> -0` for the zero case; the zero case emits the bare-base entry once per base.
- **Template-faithful behavior is template-mode only.** Cents mode applies D-01 (all-empty glyph parents) and D-06 (helper-derived `n/1200` pitch deltas). Template mode preserves Phase 1's quirks (Natural inheriting `glyph.accidentalNatural`, literal `0/24`, etc.).

### Integration Points
- **`build.py` grows `--mode`** (D-04); reuses the Phase 1 `argparse` shape; the new flag dispatches to `build_template_three()` (existing) vs. a new `build_cents_full_sweep()` (or whatever name is chosen — see Claude's Discretion).
- **`main.run(out_path)` becomes `main.run(out_path, mode)`** or grows a parallel `run_cents(out_path)` — implementation detail for the planner.
- **`tests/` grows three new files** (Plan-time decision): the helper unit tests, the structural-invariants test, the sampled byte-snapshot test. Phase 2's two-run determinism is asserted on cents mode in addition to template mode.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly invoked `--mode cents|template, default cents` over the simpler "test-only template path." This signals the user wants the template build to remain a real, runnable, file-producing entrypoint (not buried inside test code). The template-roundtrip artifact has documentation value as the smallest possible byte-faithful library.
- Sampled byte snapshots (D-07.3) should explicitly pin the **off-by-100 trap diagnostic cases**: `Sharp +14` (→114/1200), `Sharp -50` (→50/1200), `Flat -7` (→-107/1200), and the enharmonic pair `Sharp -50` / `Natural +50` (both at 50/1200). These are the cases most likely to regress silently.
- The pitch-delta numerator helper is named `pitch_delta_numerator` (per ROADMAP §Phase 2 success criterion 4 + STATE.md §Accumulated Context). The name is locked.

</specifics>

<deferred>
## Deferred Ideas

### Carried out of scope to other phases
- **Physical Dorico Pro 6.x import + tuner spot-checks** (Pitfall 1 verification, Pitfall 12 third-party VST behavior, Pitfall 10 enharmonic-equivalent confirmation) → Phase 3.
- **Panel-search ergonomics testing at 597 entries** (queries `+14`, `Sharp -`, `Flat +50`, `Natural`) → Phase 3.
- **Dense-passage cent-label collision behavior** (Pitfall 9) — the `(-8, -12)` and `(18, -12)` offsets are accepted as good-enough at v1 scope; collision-shape `cutOut*` tuples remain `(0, 0)` for the 596 new accidentals. → Phase 3 evaluates; Phase 4 documents Engrave-mode workaround if needed.
- **Open/atonal key signature gating documentation** (Pitfall 5, the #1 silent failure) → Phase 4 (README).
- **Re-import behavior across `cents.doricolib` versions** (Pitfall 6 user-facing behavior) — tested by Phase 3, documented by Phase 4.
- **`xmllint --noout` CI integration** — well-formedness check before any user receives the file. Worth queuing for Phase 4 packaging or as a small standalone tooling task.

### Discussion stayed within phase scope
No scope-creep redirects emerged during discussion.

</deferred>

---

*Phase: 2 - Range Expansion to ±99¢*
*Context gathered: 2026-05-01*
