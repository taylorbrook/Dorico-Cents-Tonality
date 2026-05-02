# Phase 2: Range Expansion to ±99¢ - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 2 - Range Expansion to ±99¢
**Areas discussed:** Glyph parent strategy, AccidentalSystem ID ordering, Phase 1 helper fate, Zero-deviation key naming, CLI shape, Test strategy

---

## Glyph parent_entityID strategy

| Option | Description | Selected |
|--------|-------------|----------|
| All-empty | Sharp/Flat/Natural all emit `<parentEntityID/>`. Decouples from Steinberg factory glyph IDs that could shift between Dorico point releases. STACK.md's recommendation. Diverges structurally from the Phase 1 template (which had Natural inherit `glyph.accidentalNatural`). | ✓ |
| Template-faithful | Reproduce the template heterogeneously: Natural inherits `glyph.accidentalNatural`; Sharp/Flat empty. Maximally byte-similar to Steinberg-exported output, but couples us to a factory entityID we don't control. | |

**User's choice:** All-empty (recommended)
**Notes:** Phase 1's template-faithful behavior is preserved only in template mode (D-03/D-04). Cents-mode glyphs are uniformly empty-parent. `_GLYPH_SPEC` in compose.py already flags this transition in a comment.

---

## `<accidentalDefinitionIDs>` ordering

| Option | Description | Selected |
|--------|-------------|----------|
| By pitch delta | Sort by `pitchDeltaFromNatural` ascending: -199¢ → +199¢, with the three zero-dev entries grouped at their math positions (Flat=-100, Natural=0, Sharp=+100). Mirrors Dorico's automatic panel sort; easiest to skim in a text editor. | ✓ |
| Zero-dev first, then base × cents | Sharp, Flat, Natural (zero-dev) lead; then Sharp ±99, Flat ±99, Natural ±99 in cent order per base. Puts the everyday accidentals at the top of the string — useful for debugging and matches mental model of "the three primary ones, plus deviations." | |
| Grouped by base | All Sharp entries (zero + ±99), then all Flat (zero + ±99), then all Natural (zero + ±99). Easy to find a base's full block when debugging; no special status for zero-dev. | |

**User's choice:** By pitch delta
**Notes:** Dorico panel order is automatic by `pitchDeltaFromNatural`, so the string order is mostly cosmetic — but it's burned into the deterministic byte output. Pitch-delta ordering matches the panel and is the lowest-friction debugging view.

---

## Phase 1 `build_template_three()` fate

| Option | Description | Selected |
|--------|-------------|----------|
| Keep as regression test | Retain `build_template_three()` and the byte-faithful template round-trip test as a permanent regression check on Class A/B/C dispatcher fidelity. Add a `--mode template|cents` CLI flag (or a separate test-only entrypoint). Preserves the structural anchor against the hand-validated template; no production cost. | ✓ |
| Retire entirely | Delete `build_template_three()` and the template round-trip test now that Phase 1's success criteria are proven. New Phase 2 structural tests (entity counts, schema invariants, pitch-helper unit tests) replace it. Smaller surface area, but loses the byte-anchor against the hand-verified template. | |

**User's choice:** Keep as regression test (recommended)
**Notes:** The hand-validated template is irreplaceable as a structural anchor; retiring it would lose ground-truth coverage of Class A/B/C dispatch fidelity that Phase 2's sampled snapshots can't replicate end-to-end.

---

## Zero-deviation entry key naming

| Option | Description | Selected |
|--------|-------------|----------|
| Bare base | `sharp`, `flat`, `natural`. Cleanest; matches how users mentally refer to them; no collision with Phase 1's `*-template` keys. | ✓ |
| Explicit-zero | `sharp+0`, `flat+0`, `natural+0`. Mechanically uniform with the non-zero key format. Trivially scriptable. Slightly noisier; the displayed name (`Sharp`) and the internal key (`sharp+0`) diverge. | |
| Suffixed | `sharp-zero`, `flat-zero`, `natural-zero`. Explicit semantic marker. Avoids any risk of confusion with the non-zero `+0` form. Most verbose. | |

**User's choice:** Bare base
**Notes:** This is a forever-locked stability contract per Pitfall 6 — once shipped, renaming creates duplicate entityIDs on user re-import. No collision with the Phase 1 `*-template` suffixed keys; bare-base keys slot in cleanly as the implicit-zero variants alongside `sharp+14`, `flat-50`, `natural-7`.

---

## CLI shape for the two modes

| Option | Description | Selected |
|--------|-------------|----------|
| `--mode cents\|template`, default cents | `python build.py --out cents.doricolib` = production sweep (default). `python build.py --mode template --out template-roundtrip.doricolib` = Phase 1's three-entity Psychography build. Production path is the obvious one; template mode is opt-in for tests. | ✓ |
| Separate scripts | `build.py` + `build_template.py`. `build.py` always emits the production cents library; tiny shim drives the template build. No flag on the production CLI; cleaner user-facing surface; slightly more files. | |
| Test-only template path | `build.py` only emits production cents. The template round-trip lives entirely inside `tests/test_template_roundtrip.py` calling `build_template_three()` directly — no separate CLI / file output. Smallest user-facing surface; the template build never produces a real file. | |

**User's choice:** `--mode cents|template`, default cents (recommended)
**Notes:** User's choice signals the template build should remain a real, runnable, file-producing entrypoint with documentation value as the smallest possible byte-faithful library — not buried inside test code.

---

## Test strategy at 1411-entity scale

| Option | Description | Selected |
|--------|-------------|----------|
| Layered: structural invariants + sampled byte snapshots | Unit tests on `pitch_delta_numerator`. Structural invariants on the full output (1411-entity count, 597 accidentals, 198 texts, 3 glyphs, ID string, sort order, schema sections). Plus byte-faithful snapshot of ~6–10 representative accidentals across all three classes including off-by-100 diagnostic cases and boundary values. | ✓ |
| Full-output byte snapshot | Commit the entire emitted `cents.doricolib` as a snapshot file in `tests/`. Re-runs diff against it. Maximally rigorous; catches every drift, including ones you didn't think to assert. Costs a several-hundred-KB binary diff in every PR that touches generation. | |
| Property + structural only | Unit tests on the math helper + structural invariants only. No byte snapshots beyond Phase 1's 3-entity template round-trip. Leanest test surface; relies on Phase 3's physical Dorico import to catch byte-level regressions. | |

**User's choice:** Layered: structural invariants + sampled byte snapshots (recommended)
**Notes:** Sampled snapshots specifically pin the off-by-100 trap diagnostic cases (Sharp +14 → 114/1200, Sharp -50 → 50/1200, Flat -7 → -107/1200) and the enharmonic pair (Sharp -50 / Natural +50 both at 50/1200). Avoids committing a several-hundred-KB binary diff per PR.

---

## Claude's Discretion

- Module placement of `pitch_delta_numerator` (new `pitch.py` vs. existing module).
- The exact name of the cents-mode counterpart to `build_template_three()`.
- Key derivation strings for the cents-mode `AccidentalSystemDef` and `TonalitySystemDef` (sensible default: `cents` for both).
- Section-internal ordering for `accidentalDefinitions`, `compositeDefinitions`, and `textDefinitions` (sensible default: pitch-delta ascending; for textDefinitions, ascending by signed cent value -99..-1, +1..+99).
- Cut-out tuples for the 596 newly-emitted cents-mode accidentals (sensible default: `(0, 0)` for all four corners, matching template Class B/C convention).

## Deferred Ideas

- Physical Dorico Pro 6.x import + tuner spot-checks → Phase 3.
- Panel-search ergonomics testing at 597 entries → Phase 3.
- Dense-passage cent-label collision behavior → Phase 3.
- README open/atonal key signature gating documentation → Phase 4.
- Re-import behavior across `cents.doricolib` versions → Phase 3 tests, Phase 4 documents.
- `xmllint --noout` CI integration → Phase 4 packaging or standalone tooling task.
