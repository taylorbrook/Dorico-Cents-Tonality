# Architecture Research

**Domain:** XML build-tooling for a Steinberg Dorico Pro 6.x tonality-system library file (`.doricolib`). Two distinct architectures live in this project: (a) the **internal entity graph** of the emitted XML, and (b) the **module structure of the Python generator** that emits it.
**Researched:** 2026-05-01
**Confidence:** HIGH on the entity graph (cross-checked element-by-element against the working `TonalitySystemStartTemplate.doricolib`), HIGH on emission order (template is the authoritative emission order Dorico produces itself), HIGH on the generator module breakdown (driven by deliverable shape + deterministic-rebuild requirement), MEDIUM on whether composites can be safely deduplicated across many `AccidentalDefinition`s (Dorico tolerates it in principle, but we have only the user's three-entity template for empirical confirmation — recommendation is "do not share" for v1, see §Reuse Strategy).

---

## TL;DR

- **Atomic render unit** = 4 entities: 1 `AccidentalDefinition` → 1 `CompositeDefinition` → 1 or 2 of `{GlyphPrimitiveEntityDefinition`, `TextPrimitiveEntityDefinition}`. The remaining three entity types (`TemperamentDefinition`, `AccidentalSystem`, `TonalitySystemDefinition`) are singletons for the whole library.
- **Three composite shapes** map cleanly to the three accidental classes:
  1. **Glyph-only** (zero-deviation `Natural`/`Sharp`/`Flat` at 0¢) — 1 component, no attachments.
  2. **Glyph + text** (sharp-base or flat-base accidentals at non-zero cents) — 2 components, 1 `relativeAttachment` between glyph `kBaselineRight` and text `kBaselineLeft`.
  3. **Text-only** (natural-base accidentals at non-zero cents) — 1 text component, no glyph, no attachments — text is positioned by direct `xOffset`/`yOffset` on the component itself (template uses `(18, -12)`).
- **Forward references are fine.** The template emits AccidentalDefinitions (section 3) that reference CompositeDefinitions (section 7) that haven't been declared yet. Dorico clearly two-pass-resolves entityIDs across the whole document.
- **Emission section order is fixed** by Dorico's own canonical output: temperaments → accidentalSystems → accidentalDefinitions → tonalitySystemDefinitions → textDefinitions → glyphDefinitions → compositeDefinitions. **Match it byte-for-byte** so generator output diffs cleanly against any Dorico-exported file.
- **Generator: 5 modules.** `uuids.py`, `entities.py` (dataclasses), `compose.py` (build_accidental factory), `emit.py` (XML serialization with byte-faithful tabs/lowercase booleans/inline tuple syntax), `main.py` (orchestrator). This split aligns precisely with the deterministic-rebuild and human-readability goals.
- **Reuse counts** for the full ±99¢ build (recommended): **1** `TemperamentDefinition` + **1** `AccidentalSystem` + **1** `TonalitySystemDefinition` + **3** glyphs (`accidentalSharp`, `accidentalFlat`, `accidentalNatural`) + **198** text definitions (one per signed cent value `-99…-1, +1…+99`) + **600** AccidentalDefinitions + **600** CompositeDefinitions (one per accidental, **not shared**). Total = **1411** entities for a ~600-accidental library. Composite-sharing is technically possible but **not recommended for v1** — see §Reuse Strategy.

---

## Standard Architecture

### System Overview — entity graph inside the .doricolib

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          kScoreLibrary (root)                             │
│  fileVersion 1.1450                                                       │
└──────────────────────────────────────────────────────────────────────────┘
        │
        │ contains 7 sections, each with <entities array="true">
        ▼
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│ TonalitySystem       │───►│ Temperament          │    │ AccidentalSystem     │
│ Definition (1×)      │    │ Definition (1×)      │    │ (1×)                 │
│  name="cents"        │    │  12-EDO              │◄──┐│  accidentalDefinitionIDs:
│  customKeySignatures │    │  noteAtoB=200, etc.  │   ││   "id1, id2, id3, …"  (CSV string)
│  (one empty stub)    │    └──────────────────────┘   │└────────────┬─────────┘
└─────────┬────────────┘                                │              │
          │ references both                              │              │ references N×
          ▼                                              │              ▼
   (these two refs)                                      │   ┌──────────────────────┐
                                                         │   │ AccidentalDefinition │
                                                         │   │ (~600×)              │
                                                         │   │  name="Sharp +14"    │
                                                         │   │  pitchDeltaFromNatural│
                                                         │   │      ="114/1200"     │
                                                         │   │  cutOutNW/NE/SE/SW   │
                                                         │   │  compositeID ────────┼──┐
                                                         │   └──────────────────────┘  │
                                                         │                              │ references 1×
                                                         │                              ▼
                                                         │                  ┌──────────────────────┐
                                                         │                  │ CompositeDefinition  │
                                                         │                  │ (~600×)              │
                                                         │                  │  category=kAccidentals│
                                                         │                  │  components[]: 1 or 2│
                                                         │                  │  relativeAttachments[]│
                                                         │                  │  scalingRules[] (∅)  │
                                                         │                  └──┬─────────────────┬─┘
                                                         │                     │ references 1×    │ references 0–1×
                                                         │                     ▼                  ▼
                                                         │       ┌─────────────────────┐ ┌─────────────────────┐
                                                         │       │ GlyphPrimitive      │ │ TextPrimitive       │
                                                         │       │ EntityDefinition    │ │ EntityDefinition    │
                                                         │       │ (3× total, shared)  │ │ (~198× total, shared)│
                                                         │       │  codePoint=0xE262   │ │  text="+14"         │
                                                         │       │  isSmufl=true       │ │  fontStyle          │
                                                         │       │  fontStyle          │ │   =font.defaulttext │
                                                         │       │   =font.defaultmusic│ │                     │
                                                         │       └─────────────────────┘ └─────────────────────┘
                                                         │                                          ▲
                                                         │                                          │
                                                         └──────────────────────────────────────────┘
                                                            (AccidentalSystem ◄─ AccidentalDefinitions
                                                             listed via comma-separated ID string,
                                                             which is the picker's display order)
```

### Reference graph (directed, by entity type)

Read `A → B` as "A holds an entityID reference to B".

```
TonalitySystemDefinition  → TemperamentDefinition
TonalitySystemDefinition  → AccidentalSystem
AccidentalSystem          → AccidentalDefinition  (N×, comma-separated CSV in one XML element's text)
AccidentalDefinition      → CompositeDefinition   (1× per accidental, via <compositeID>)
CompositeDefinition       → GlyphPrimitiveEntityDefinition  (0..N×, via component[].componentId when componentType=kGlyph)
CompositeDefinition       → TextPrimitiveEntityDefinition   (0..N×, via component[].componentId when componentType=kText)
CompositeDefinition       → ComponentInstanceID            (relativeAttachment.componentRelativePair{1,2}.componentInstanceId
                                                            = "<componentId>.<componentInstance>" — same entityID with .N suffix)
```

**Forward references are tolerated by Dorico.** The template's emission order means AccidentalDefinitions reference CompositeDefinitions four sections before those Composites are declared, and CompositeDefinitions reference Glyph/Text primitives one to two sections before they're declared. Dorico evidently parses the whole document, then resolves entityIDs in a second pass. The generator must NOT reorder sections to satisfy a forward-reference theory — match Dorico's canonical order verbatim.

### Atomic render unit — minimum entities for one accidental to render

For a single accidental like `Sharp +14` to display and play correctly, the file must contain — at minimum — these entities:

| Entity | Count | Why required |
|---|---|---|
| `TonalitySystemDefinition` | 1 | The dropdown entry users pick in the panel; ties everything together |
| `TemperamentDefinition` | 1 | The 7 diatonic step sizes (200/100/200/200/100/200/200 for 12-EDO); referenced by the TonalitySystem |
| `AccidentalSystem` | 1 | The list of accidental IDs the picker shows; referenced by the TonalitySystem; must contain at least one ID |
| `AccidentalDefinition` | 1 | Carries `pitchDeltaFromNatural` (the playback math) and points at a Composite (the visual) |
| `CompositeDefinition` | 1 | The visual recipe (glyph + text layering); referenced by the AccidentalDefinition |
| `GlyphPrimitiveEntityDefinition` | 1 (sharp/flat-base) or 0 (natural-base) | The SMuFL glyph the composite draws |
| `TextPrimitiveEntityDefinition` | 1 (non-zero cents) or 0 (zero cents) | The cent-label text the composite draws |

So the **atomic unit** the generator should emit for any one accidental is **5 to 7 entities** depending on the visual class:

- **Class A — zero-deviation (`Natural`, `Sharp`, `Flat` at 0¢):** 6 entities = 1 TonalitySystem + 1 Temperament + 1 AccidentalSystem + 1 AccidentalDefinition + 1 CompositeDefinition + 1 Glyph. No text.
- **Class B — sharp-base or flat-base at non-zero cents (e.g. `Sharp +14`):** 7 entities = above + 1 Text.
- **Class C — natural-base at non-zero cents (e.g. `Natural -14`):** 6 entities = above without the Glyph (text-only composite).

Across the full ±99¢ build the singletons (TonalitySystem, Temperament, AccidentalSystem) collapse to one each, the glyphs collapse to three (sharp/flat/natural) shared by every Class A and Class B/C user, and the texts collapse to ~198 (one per signed cent value `-99..-1, +1..+99`).

### Component Responsibilities (entity types)

| Entity type | Owns | Cross-references |
|---|---|---|
| `TemperamentDefinition` | The 7 diatonic step sizes summing to 1200 cents (`relativeDiatonicDivisions`); free `name`. Singleton per tonality system. | (none outbound; referenced by `TonalitySystemDefinition`) |
| `AccidentalSystem` | The set of accidentals available in this tonality. Holds `<accidentalDefinitionIDs>` as a single comma-space–separated string of all accidental entityIDs. **Order in this string is the order of appearance in the panel** (Dorico re-sorts by pitch delta visually, but the string is what the entity tracks). | → many `AccidentalDefinition` |
| `AccidentalDefinition` | Playback math (`pitchDeltaFromNatural` rational `n/1200`); visual reference (`compositeID`); collision shape (`cutOutNW/NE/SE/SW` tuples); search/display name. | → 1 `CompositeDefinition` |
| `TonalitySystemDefinition` | The user-facing tonality entry (dropdown name); custom key signatures (one minimal empty stub for cents). | → 1 `TemperamentDefinition`, → 1 `AccidentalSystem` |
| `TextPrimitiveEntityDefinition` | A reusable text label (e.g. the literal string `+14`); font style reference (`font.defaulttext`); name `<text>.font.defaulttext`. | (none outbound; referenced by `CompositeDefinition` components) |
| `GlyphPrimitiveEntityDefinition` | A reusable SMuFL glyph reference (codepoint, `isSmufl=true`, font style `font.defaultmusic`, `pointSize=1`). | (none outbound; referenced by `CompositeDefinition` components) |
| `CompositeDefinition` | The visual recipe: `components[]` (each carrying `componentId`, `componentType` ∈ {`kGlyph`, `kText`}, position offset, scale, z-order, and a `componentInstance` integer); `relativeAttachments[]` (positional anchoring between two component instances using `kBaselineLeft/Right` etc., with `xOffset`/`yOffset`); `scalingRules[]` (always empty for accidentals); `category=kAccidentals`. | → 0..N `GlyphPrimitiveEntityDefinition`, → 0..N `TextPrimitiveEntityDefinition` |

### Key cross-reference details that bite

- **`accidentalDefinitionIDs` is a CSV string in one element's text, not a list of child elements.** Easy to miss when scanning the schema visually. Generator: emit `", ".join(ids)` with a space after each comma (matches the template byte-for-byte).
- **`componentInstanceId` is `<entityID>.<int>` not just `<entityID>`.** The integer suffix matches the corresponding component's `<componentInstance>` value (always `0` in the template — Dorico uses the suffix for cases where a composite has two of the same glyph, e.g. a double-sharp built from two sharp glyphs, but for our use case it's always `.0`).
- **`pitchDeltaFromNatural` is emitted as a literal rational string, not auto-reduced.** The template uses `0/24` for Natural (denominator inherited from somewhere else, NOT 1200). For our generated content, use `n/1200` consistently (`0/1200` for clean ♯/♭/♮, `14/1200` for `Sharp +14` which sits 14¢ above standard sharp = +114¢ from natural — so the actual delta is `114/1200`, not `14/1200`). **Critical math:** `pitchDeltaFromNatural` is always relative to the natural pitch, not relative to the base accidental.
- **`<parentEntityID>` is empty for nearly all entities except some glyphs.** The template has `accidentalNatural` with `<parentEntityID>glyph.accidentalNatural</parentEntityID>` (inheriting from a Dorico factory glyph) but `accidentalSharp` with `<parentEntityID/>` empty. STACK.md recommends emitting all our glyphs with empty parent — safer because we don't depend on factory entityIDs that could shift between Dorico versions. The downside is we don't inherit any Dorico-built-in collision tuning, but for SMuFL standard glyphs that's negligible.
- **`cutOutNE` non-zero only on Natural in the template** — `(0.192, 2.116)` and `cutOutSW` `(0.476, 0.512)`. For sharp/flat-base accidentals with text labels the template uses `(0, 0)` for all four corners. The generator should emit `(0, 0)` for everything in v1 — collision tuning is not in scope for the cents library, and zero corners are the safe Dorico default.

---

## Recommended Project Structure

```
dorico-tonality/
├── build.py                 # Thin CLI entry point — parses args, calls main.run()
├── src/
│   └── cents_generator/
│       ├── __init__.py      # Package marker, exposes run() + version constant
│       ├── uuids.py         # UUID5 derivation (PROJECT_NAMESPACE pinned here)
│       ├── entities.py      # Frozen dataclasses for each entity type
│       ├── compose.py       # build_accidental(base, cents) → list[Entity]
│       ├── emit.py          # ElementTree-based XML serialization (byte-faithful)
│       ├── main.py          # Orchestrator: build entity list, group by section, emit
│       └── constants.py     # SMuFL codepoints, font-style names, fileVersion, etc.
├── tests/
│   ├── test_determinism.py  # Two consecutive runs produce byte-identical output
│   ├── test_template_roundtrip.py  # Generator can re-emit the 3 template entities byte-faithfully
│   └── test_compose.py      # build_accidental output shape per class (A/B/C)
├── .planning/               # GSD planning artifacts (existing)
├── TonalitySystemStartTemplate.doricolib  # Reference fixture, kept for tests
├── README.md                # User-facing install + usage docs
├── LICENSE                  # MIT
├── pyproject.toml           # Package metadata, ruff config, pytest config
└── cents.doricolib          # Generated artifact — committed for direct download
```

### Structure Rationale

- **`build.py` at root, package under `src/cents_generator/`:** Standard "src layout" — cleanly separates the generator's import surface from the build entrypoint. Lets `python build.py` be a one-liner for users who just want to regenerate, while the package can be tested in isolation. Stdlib-only means no `pyproject.toml` dependencies, but the file still earns its place by holding ruff/mypy/pytest config.
- **`uuids.py` is its own module:** The `PROJECT_NAMESPACE` constant is the most important value in the project — re-rotating it would break update-in-place semantics for every existing user. Isolating it makes that constraint visible. It also keeps the deterministic-UUID logic testable in one place.
- **`entities.py` uses frozen dataclasses (`@dataclass(frozen=True, slots=True)`):** Each entity type (`TemperamentDef`, `AccidentalDef`, `CompositeDef`, `Component`, `RelativeAttachment`, `GlyphDef`, `TextDef`, `TonalitySystemDef`, `AccidentalSystemDef`) gets one dataclass. Frozen means hashable + immutable so you can't accidentally mutate entities mid-emission. Slots reduces memory (1411 entities is small but slots is free correctness). Each dataclass has one method, `to_xml(self) -> ET.Element`, called by `emit.py`.
- **`compose.py` is the high-level domain logic:** This is the only module a future maintainer needs to touch when adding a new accidental shape. The signature is roughly:

  ```python
  def build_accidental(base: Literal["natural", "sharp", "flat"], cents: int) -> list[Entity]:
      """Returns 1–4 entities: AccidentalDef, CompositeDef, optional GlyphDef ref, optional TextDef ref.
      Glyphs and texts are returned as Entity references; main.py deduplicates them across calls
      so we emit each unique glyph/text exactly once."""
  ```

  The function dispatches on `(base, cents == 0)` to the three classes (A/B/C). All UUID derivation happens via `uuids.entity_id(kind, key)`. No XML emission here — pure data construction.
- **`emit.py` owns byte-faithful serialization:** This is the only module that knows about XML quirks (tabs not spaces, lowercase `true`/`false`, `(0, 0)` tuple syntax with the space, `100.000000` float format with six zeros, `0xE262` hex literal format, `<parentEntityID/>` self-closing). Every entity dataclass emits its element via `entity.to_xml()`, and `emit.py` wraps the section + root + writes to disk. The boundary makes "byte-faithfulness audits" reviewable in one file.
- **`main.py` is the orchestrator:** Builds the singleton entities, iterates `(base, cents)` over the full range, calls `compose.build_accidental` for each, deduplicates Glyphs and Texts by entityID, sorts entities into the seven sections, calls `emit.write(path, sections)`. Should be < 100 lines.
- **`constants.py` holds magic numbers and identifiers:** `FILE_VERSION = "1.1450"`, `SMUFL_SHARP = 0xE262`, `FONT_DEFAULT_MUSIC = "font.defaultmusic"`, `FONT_DEFAULT_TEXT = "font.defaulttext"`, the `PROJECT_NAMESPACE` UUID (re-exported through `uuids.py`), the canonical section emission order. Pulling these into a constants module makes them grep-able and prevents stringly-typed drift.
- **Tests as smoke checks, not exhaustive:** Three focused tests validate the three load-bearing properties (determinism, template byte-faithfulness, per-class output shape). The full ±99¢ build is too large to assert by hand; the three smoke tests + manual Dorico import validation per PROJECT.md is the right balance.

### Validation against goals

| Goal | How the structure addresses it |
|---|---|
| Deterministic regeneration | `uuids.py` is a single 30-line module with a pinned namespace; `emit.py` is the single chokepoint for any non-determinism (formatting variance, dict-ordering, line endings). Both are independently testable. |
| Human-readable code | Each entity type has its own dataclass with a `to_xml` method; the generator's flow (`main.py`) reads top-to-bottom as "build singletons → loop accidentals → group by section → emit". No metaclasses, no codegen, no template-string black magic. |
| Easy to add new accidental shapes | New shapes (e.g. double-sharp variants, custom glyphs) require: (a) a new branch in `compose.build_accidental` if the dispatch logic differs, (b) maybe a new entity dataclass in `entities.py` if the schema differs (it won't for accidentals — only the composite contents change). The boundary is clean. |

---

## Architectural Patterns

### Pattern 1: Deterministic UUID derivation via uuid5

**What:** Every entityID in the output file is `uuid5(PROJECT_NAMESPACE, f"{kind}:{key}").hex` formatted as `<kind>.user.<32-hex>`. The same `(kind, key)` pair produces the same UUID across every run, on every machine, forever.

**When to use:** Always — this is the foundation of "re-imports update existing entries instead of duplicating". Per STACK.md this is non-negotiable.

**Trade-offs:**
- **Pro:** Free determinism with no per-entity state; entityID is a pure function of stable human-readable keys (e.g. `("accidental", "sharp+14")`).
- **Pro:** Adding a new accidental in the future doesn't shift any existing UUIDs — keys are independent.
- **Con:** If you ever rename a key (e.g. change `"sharp+14"` to `"Sharp +14"`), the UUID changes and a re-import would create a duplicate alongside the old. Fix: keys are an internal convention; lock the key format on day one and never change it. Display names (the `<name>` element) are independent of keys.
- **Con:** SHA-1 is the underlying hash; collisions are astronomically unlikely at our scale (~1411 entities) but technically not zero.

**Example:**
```python
# uuids.py
import uuid
PROJECT_NAMESPACE = uuid.UUID("6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c")  # PIN ONCE — NEVER ROTATE

def entity_id(kind: str, key: str) -> str:
    """kind in {accidental, glyph, text, comp, temperament-definition,
                accidental-system, tonalitysystem}; key is a stable human-readable name."""
    return f"{kind}.user.{uuid.uuid5(PROJECT_NAMESPACE, f'{kind}:{key}').hex}"

# Examples — same input, same output, every run:
entity_id("accidental", "sharp+14")           # accidental.user.<deterministic 32 hex>
entity_id("glyph",      "accidentalSharp")    # glyph.user.<deterministic 32 hex>
entity_id("text",       "+14")                # text.user.<deterministic 32 hex>
entity_id("comp",       "sharp+14")           # comp.user.<deterministic 32 hex>
entity_id("temperament-definition", "12-edo") # temperament-definition.user.<deterministic 32 hex>
```

Key conventions to lock day one:
- Accidental key: `"<base><signed-cents>"` lowercase, e.g. `sharp+14`, `flat-50`, `natural-7`. Zero-deviation: `sharp`, `flat`, `natural`.
- Composite key: same as accidental key.
- Glyph key: SMuFL glyph name verbatim (`accidentalSharp`).
- Text key: the literal text (`+14`, `-50`, `+99`).
- Singleton keys: `"12-edo"`, `"cents"`, `"cents"` (for AccidentalSystem matching the tonality name).

### Pattern 2: Three-class composite dispatch

**What:** Every accidental falls into one of three visual classes determined by `(base, cents == 0)`. A single dispatch function builds the correct composite shape.

**When to use:** This is the core of `compose.py`. Future shape additions (double-accidentals, custom symbol sets) just add new classes.

**Trade-offs:**
- **Pro:** The three classes have visibly different XML structures; pretending they're uniform via "one composite shape with optional fields" obscures the actual shape constraints (e.g. Class C has no glyph and no relativeAttachment; Class A has no text and no relativeAttachment).
- **Pro:** Adding new shapes is additive — no rewrite of existing class handlers.
- **Con:** Two of the three classes (A and C) skip relativeAttachments entirely; you might expect to model "always emit a relativeAttachment, sometimes empty" but the template clearly emits `<relativeAttachments array="true"/>` (self-closing empty array) for classes A and C. The dispatch handles this correctly; just don't be tempted to "unify" it.

**Example:**
```python
# compose.py
def build_accidental(base: Literal["natural", "sharp", "flat"], cents: int) -> AccidentalBundle:
    if cents == 0:
        # Class A: glyph-only, no text, no relativeAttachment
        return _build_class_a(base)
    elif base == "natural":
        # Class C: text-only (no glyph), no relativeAttachment, text positioned by xOffset/yOffset
        return _build_class_c(cents)
    else:
        # Class B: glyph + text, with relativeAttachment kBaselineRight↔kBaselineLeft, offset (-8, -12)
        return _build_class_b(base, cents)

# Class B and C produce different geometry for the cent label:
#   - Class B: text positioned via relativeAttachment to the glyph's baseline-right
#   - Class C: text positioned via direct xOffset=18, yOffset=-12 on the component (NO relativeAttachment)
# Both come from the working template — preserve verbatim.
```

### Pattern 3: Section-grouped emission with deduplication

**What:** After `compose.build_accidental` is called for every `(base, cents)` pair, the orchestrator deduplicates Glyph and Text entities by entityID (same key → same UUID → only emit once), then groups all entities into the seven canonical sections, and emits in fixed section order.

**When to use:** Always — Dorico expects this section order specifically (matches its own export output).

**Trade-offs:**
- **Pro:** Deduplication is free if entityIDs are deterministic — just dict-by-id and take values. ~1200 calls to `build_accidental` produce ~1411 unique entities, with the dedupe hitting on glyphs (3 unique across ~600 references) and texts (~198 unique across ~600 references).
- **Pro:** Section ordering is data-driven (a constant list), not control-flow-driven (no nested if-elif). Easy to verify against the template.
- **Con:** Forward references are now intentional — the file emits AccidentalDefinitions before their target Composites. This is correct for Dorico but unusual for other XML tooling. Document it in `emit.py` so a future contributor doesn't "fix" it.

**Example:**
```python
# main.py (sketch)
SECTION_ORDER = [
    ("temperaments",            TemperamentDef),
    ("accidentalSystems",       AccidentalSystemDef),
    ("accidentalDefinitions",   AccidentalDef),
    ("tonalitySystemDefinitions", TonalitySystemDef),
    ("textDefinitions",         TextDef),
    ("glyphDefinitions",        GlyphDef),
    ("compositeDefinitions",    CompositeDef),
]

def run(out_path: Path) -> None:
    entities: dict[str, Entity] = {}  # dedupe by entity_id

    # 1. Singletons
    temperament = build_temperament_12edo()
    entities[temperament.entity_id] = temperament
    # ... AccidentalSystem and TonalitySystem are singletons too, but the AccidentalSystem
    #     needs the full list of accidental IDs which is built in the loop below; defer it.

    # 2. Loop accidentals
    accidental_ids: list[str] = []
    for base in ("natural", "sharp", "flat"):
        for cents in range(-99, 100):  # -99..+99 inclusive
            bundle = compose.build_accidental(base, cents)
            for ent in bundle.entities:
                entities.setdefault(ent.entity_id, ent)  # dedupe
            accidental_ids.append(bundle.accidental.entity_id)

    # 3. Build the AccidentalSystem now that we have all IDs
    acc_system = build_accidental_system(accidental_ids)
    entities[acc_system.entity_id] = acc_system
    tonality = build_tonality_system(temperament.entity_id, acc_system.entity_id)
    entities[tonality.entity_id] = tonality

    # 4. Group by section, emit in fixed order
    sections = group_by_section(entities.values(), SECTION_ORDER)
    emit.write(out_path, sections)
```

---

## Data Flow

### Input → Output

```
        ┌─────────────────────────────────────────┐
        │  Inputs (compile-time constants)         │
        │   • PROJECT_NAMESPACE (uuid.UUID)        │
        │   • cents range: -99..+99                 │
        │   • base accidentals: natural/sharp/flat  │
        │   • SMuFL codepoints (3 glyphs)           │
        │   • fileVersion 1.1450                    │
        │   • naming convention (Sharp +14, …)      │
        └──────────────────────┬──────────────────┘
                               ▼
              ┌────────────────────────────────────┐
              │  main.py: orchestrator              │
              │   1. Build singletons (Temperament) │
              │   2. Iterate (base, cents)          │
              └──────────────────┬─────────────────┘
                                 ▼
              ┌────────────────────────────────────┐
              │  compose.py: build_accidental       │
              │   dispatches on class (A/B/C)       │
              │   returns AccidentalBundle =        │
              │   { accidental, composite, glyph?,  │
              │     text? }                         │
              └────────┬─────────────────┬─────────┘
                       │                 │
                       │ uuids.entity_id │
                       ▼                 │
              ┌─────────────────┐        │
              │  uuids.py       │        │
              │   uuid5 of      │        │
              │   (kind, key)   │        │
              └────────┬────────┘        │
                       │                 │
                       └────────┬────────┘
                                ▼
              ┌────────────────────────────────────┐
              │  main.py: deduplicate + group       │
              │   • dict-by-entity-id               │
              │   • build AccidentalSystem from IDs │
              │   • build TonalitySystem            │
              │   • group entities by section       │
              └──────────────────┬─────────────────┘
                                 ▼
              ┌────────────────────────────────────┐
              │  emit.py: ElementTree → bytes       │
              │   • for each entity: to_xml()       │
              │   • indent with tabs                │
              │   • lowercase booleans              │
              │   • inline tuples and rationals     │
              │   • write UTF-8 with LF endings     │
              └──────────────────┬─────────────────┘
                                 ▼
              ┌────────────────────────────────────┐
              │  cents.doricolib (output, ~1411    │
              │  entities, ~7 sections)             │
              └────────────────────────────────────┘
```

### Determinism budget

For two runs to produce byte-identical output:

1. **Iteration order is deterministic:** Python's `for cents in range(-99, 100)` is fixed. `for base in ("natural", "sharp", "flat")` is a tuple, fixed.
2. **`dict.setdefault` preserves first-insertion order** (Python 3.7+).
3. **`uuid5` is pure** — same inputs, same hash.
4. **`ET.indent(tree, space="\t")` is deterministic.**
5. **Floats formatted as fixed strings** (`"100.000000"`) not via `f"{value:.6f}"` of a float — no IEEE-754 surprises.
6. **Line endings forced to LF** by writing in binary mode.

A 5-line CI check (`diff <(python build.py --stdout) <(python build.py --stdout)`) catches any regression in any of these.

### Build order — confirmation that template's section order works

The user's working template emits sections in this order, and Dorico Pro 6.x accepts it cleanly:

```
1. <temperaments>              (no outbound refs)
2. <accidentalSystems>         (refs forward to <accidentalDefinitions>, section 3 — RESOLVED)
3. <accidentalDefinitions>     (refs forward to <compositeDefinitions>, section 7 — RESOLVED)
4. <tonalitySystemDefinitions> (refs back to sections 1 + 2 — RESOLVED)
5. <textDefinitions>           (no outbound refs)
6. <glyphDefinitions>          (sometimes refs factory parentEntityID — see §accidentalNatural caveat)
7. <compositeDefinitions>      (refs back to sections 5 + 6 — RESOLVED)
```

Confirmed observations:
- **Forward references work.** Section 2 → 3 and section 3 → 7 are both forward-references in file order, and Dorico resolves them. So the generator does NOT need to topologically sort — it just emits in the canonical order.
- **No alphabetical or dependency-based reordering.** This is Dorico's own canonical export order. Deviating (e.g. moving compositeDefinitions before accidentalDefinitions to "satisfy" forward refs) would diverge from any Dorico-exported file and complicate diffs. Don't do it.
- **The order is stable across the file format's lifetime** (template's `fileVersion 1.1450` matches Dorico Pro 6.x export). If a future Dorico version reorders sections, treat it as a new generator target (per STACK.md's "Stack Patterns by Variant").

---

## Phasing Implications

### Natural build order (informs roadmap)

Given the entity graph, the natural phase progression is:

1. **Phase 1 — Generator skeleton + template round-trip.**
   Implement `uuids.py`, the entity dataclasses for the three template entities (Natural / `-14` / `#-31`) and their dependencies (Temperament, AccidentalSystem, TonalitySystem, 2 glyphs, 2 texts, 3 composites), plus minimal `emit.py`. Goal: **byte-identical reproduction of the template** (with renamed entityIDs, since UUIDs derive from our keys not the template's). Validation: import the round-trip output into Dorico, confirm it loads and behaves like the original. Manually compare structural patterns against the template.
   - **Risk:** XML byte-faithfulness (tabs, lowercase booleans, inline tuple syntax) takes more iteration than expected. Budget a debugging session for `emit.py`.
   - **No hidden dependency:** This phase covers all three composite classes (the template happens to include one of each: Natural is Class A glyph-only, `-14` is Class C text-only, `#-31` is Class B glyph+text). Implementing the round-trip exercises every code path.

2. **Phase 2 — Range expansion to ±99¢.**
   Generalize `compose.build_accidental` to handle arbitrary `(base, cents)` inputs. Loop over `(natural, sharp, flat) × (-99..+99)` plus the three zero-deviation entries. Generate ~600 AccidentalDefinitions, ~600 CompositeDefinitions, ~198 TextDefinitions, 3 GlyphDefinitions. Build the AccidentalSystem with all 600 IDs as a comma-separated string.
   - **Risk:** Search-friendliness of names (per FEATURES.md) — name format must be `Sharp +14`, `Flat -50`, etc. Not free-text. Lock this in compose.py.
   - **Risk:** `pitchDeltaFromNatural` math — must be relative to natural (so `Sharp +14` is `114/1200`, not `14/1200`). Easy to get wrong on first pass; covered by §"Key cross-reference details that bite".
   - **No hidden dependency:** Phase 1's three-class dispatcher is the right primitive; Phase 2 is purely a parameter sweep.

3. **Phase 3 — Validation (Dorico import + playback).**
   Manually import into Dorico Pro 6.x. Spot-check 5–10 accidentals across the range against a tuner (Class A, Class B at -50/+50/-99/+99, Class C at -50/+50). Verify the panel search filters as expected (`"Sharp +14"` finds one entry, `"+14"` finds three). Verify zero-deviation entries render without cent labels.
   - **Risk:** Open/atonal key signature gotcha (per FEATURES.md) — without it, the panel is empty and "validation fails" for the wrong reason. Document this in the validation runbook.
   - **No hidden dependency:** Decoupled from Phase 1/2 once the file is built.

4. **Phase 4 — README + packaging.**
   Write the README per FEATURES.md §Q5 (13-section structure). Include install paths, the open-key-signature walkthrough, naming reference, troubleshooting, license. Optionally generate a cents reference chart from the same Python script.
   - **No hidden dependency:** Pure documentation; could in principle parallelize with Phase 2/3 but the troubleshooting section benefits from learnings during validation.

### Are there hidden dependencies that would change this ordering?

I scrutinized the entity graph for cross-phase coupling and found **none that would re-order phases**. The relevant signals:

- **Phase 1 is the right MVP.** The template happens to include one of each composite class, so Phase 1 forces every code path to exist before Phase 2 scales up. Skipping straight to Phase 2 is tempting (it's the same code, just looped) but loses the byte-faithful template comparison anchor.
- **Phase 2 has no schema-discovery risk.** Every entity field used in Phase 2 already appears in the Phase 1 template; only their values vary.
- **Phase 3's playback validation could in principle expose a math error in `pitchDeltaFromNatural`,** which would force a Phase 2 fix. Mitigation: include a unit test in Phase 2 asserting `pitchDeltaFromNatural` for a known accidental against a hand-calculated value. (`Sharp +14` → `114/1200`, `Flat -7` → `-107/1200` since flat is `-100/1200` plus `-7/1200`, etc.)
- **Phase 3 may also surface naming/search issues** — e.g. the panel might not search efficiently with 600 names. FEATURES.md flags this is empirically unverified at this scale. If validation reveals search problems, the fix is name format adjustments in Phase 2's `compose.py`, no architectural change. Phase ordering still correct.

**One coupling worth noting:** if Phase 3 reveals that Dorico actually rejects some emission detail (e.g. the textOnly composite with no relativeAttachment, or the comma-separated `accidentalDefinitionIDs` at 600-entry length), the fix lives in Phase 1's `emit.py` or `compose.py` and ripples forward. This is a known risk; the mitigation is having the template round-trip test running continuously to catch any regression.

---

## Reuse Strategy

### Per-entity counts for the full ±99¢ build

Recommended counts for the ~600-accidental cents library:

| Entity type | Count | Reuse pattern | Why this number |
|---|---|---|---|
| `TemperamentDefinition` | **1** | Singleton | One 12-EDO temperament covers everything; no need to vary it. |
| `AccidentalSystem` | **1** | Singleton with all ~600 IDs in one CSV | The picker's content is governed entirely by this list. One per tonality. |
| `TonalitySystemDefinition` | **1** | Singleton | One dropdown entry named "cents" wraps it all. |
| `GlyphPrimitiveEntityDefinition` | **3** | Shared across all composites of matching base | `accidentalSharp` (used by all sharp-base Class B), `accidentalFlat` (all flat-base Class B), `accidentalNatural` (used only by Class A natural — not by Class C natural-base, which has no glyph). |
| `TextPrimitiveEntityDefinition` | **198** | Shared across all composites with the same cent value | One unique `<text>` value per signed cent: `-99..-1, +1..+99` = 198 unique texts. The same `+14` text is referenced by `Sharp +14`, `Flat +14`, and `Natural +14` composites. |
| `AccidentalDefinition` | **600** | One per accidental, never shared | (199 × 3 base − overlap) where overlap = the 3 zero-deviation entries we want to surface as named ♯/♭/♮ once each. Math: 199 cents × 3 bases = 597 non-zero entries + 3 zero entries (Sharp at 0, Flat at 0, Natural at 0) = **600**. |
| `CompositeDefinition` | **600** | One per accidental, **not shared** (recommended) | Each accidental gets its own composite. See §"Composite sharing — recommended NOT to share" below. |

**Total: 1 + 1 + 1 + 3 + 198 + 600 + 600 = 1411 entities** for a ~600-accidental library.

### Composite sharing — recommended NOT to share

In principle, two AccidentalDefinitions with the same visual could share a single CompositeDefinition (e.g. `Sharp +14` and `Flat +14` both visually display `glyph + "+14"` text — but with **different glyphs** so they don't actually share). The cases where composites *could* legitimately be shared are narrower than they look:

- **Class A composites:** the three zero-deviation entries (`Sharp`, `Flat`, `Natural`) have distinct glyphs, so no sharing.
- **Class B composites:** sharp-base and flat-base never share (different base glyph), but two sharp-base composites with the same cent value? They don't exist — each cent value gives one sharp-base accidental.
- **Class C composites:** natural-base text-only — also unique per cent value.

So the natural deduplication ratio is **1:1 — every composite is unique** in the cents library. There's no opportunity to share composites across accidentals without conflating semantically different entities.

**However, `Natural -14` and `Natural +14` could in theory share a composite if we built it as "the +14 text composite" reused by both** — but they'd then share a name and `pitchDeltaFromNatural`, which would defeat the picker. They're inherently distinct accidentals.

**Recommendation: 1 CompositeDefinition per AccidentalDefinition.** This is what the template does (3 accidentals, 3 composites, no sharing) and what FEATURES.md/STACK.md assume.

### What CAN safely share

- **Glyphs (3 entities, ~600 references):** every Class A `Sharp` and every Class B `Sharp +N` references the same `accidentalSharp` glyph entity. Same for flat and natural. Cleanly factored.
- **Texts (198 entities, ~600 references):** every composite with cent value `+14` (all three of them — Sharp +14, Flat +14, Natural +14) references the same `text "+14"` entity. The text content is the only distinguishing feature, so identical text = identical entity.
- **The single `Temperament` and the single `AccidentalSystem` and the single `TonalitySystem` are obviously shared singletons.**

### Edge case: Should Class A's `Natural` composite share its glyph with no other accidental?

Class C accidentals (natural-base at non-zero cents like `Natural +14`) display **only text, no glyph**. So the `accidentalNatural` glyph is referenced **only by the Class A `Natural` composite** — it has exactly one user. We still emit it as a separate entity (rather than inlining the glyph data into the composite) because:

1. The schema requires composites to reference glyphs by entityID, not inline.
2. Future shape additions might add a Class B "natural + cents with the natural glyph" variant; keeping the glyph as a separate entity makes this trivial.

**Net: 3 glyph entities is the right count. Don't try to optimize.**

### What this implies for `compose.py` and `main.py`

```python
# compose.build_accidental returns a bundle that names ALL involved entities,
# including the shared ones. The orchestrator deduplicates by entityID.

@dataclass(frozen=True)
class AccidentalBundle:
    accidental: AccidentalDef       # always 1, always unique
    composite: CompositeDef         # always 1, always unique (recommended)
    glyph: GlyphDef | None          # 1 for Class A and B, None for Class C
    text: TextDef | None            # 1 for Class B and C, None for Class A
    @property
    def entities(self) -> list[Entity]:
        return [e for e in (self.accidental, self.composite, self.glyph, self.text) if e is not None]

# In main.py:
all_entities: dict[str, Entity] = {}
for base, cents in product(("natural", "sharp", "flat"), range(-99, 100)):
    bundle = compose.build_accidental(base, cents)
    for ent in bundle.entities:
        all_entities.setdefault(ent.entity_id, ent)  # ←─ dedupe across calls
# Now all_entities has 1411 unique entities. Group by section, emit.
```

The deduplication is **idempotent and order-independent** because entityIDs are deterministic. Same input set → same dedup'd dict.

---

## Scaling Considerations

This is a single-file artifact, not a service, so traditional scaling (concurrent users, throughput) doesn't apply. The relevant scaling axes are:

| Scale axis | Current target | If pushed further |
|---|---|---|
| Number of accidentals | ~600 (cents ±99 × 3 bases) | At ~1500 (e.g. ±99¢ × 5 bases including double-sharp/flat), the panel becomes hard to navigate even with search per FEATURES.md forum thread #832085. **Recommendation: don't.** |
| Number of unique texts | ~198 | If the design changes to sub-cent precision (e.g. tenths), text count balloons to ~1980. PROJECT.md correctly flags sub-cent as out of scope. |
| Generator runtime | < 1 second for 1411 entities | Stays linear in entity count — no quadratic operations. Fine through 10× growth. |
| Output file size | ~250 KB est. (1411 entities × ~180 bytes avg) | Linear in entity count. Dorico parses this in milliseconds. Not a concern through 10× growth. |
| Re-import update behavior | Dorico matches by entityID, so updates in place | Stays correct as long as `PROJECT_NAMESPACE` doesn't rotate and key conventions don't change. |

### Scaling priorities

1. **Picker usability is the first ceiling**, hit at ~600–1000 entries per FEATURES.md. Fixed by naming convention (`Sharp +14`) for searchability, not by architecture changes. Already in scope.
2. **Determinism is the silent non-issue**: as long as the patterns above are followed, scaling to 10,000 entities wouldn't break re-import semantics. The architecture is correct by construction.
3. **No architecture change needed** for any plausible v2 scope. If the project ever grows to multiple tonality systems in one file (e.g. cents + 31-EDO), each TonalitySystemDefinition is independent; just emit two. The generator becomes "per-tonality compose, then merge into one library file" — additive, not architectural.

---

## Anti-Patterns

### Anti-Pattern 1: Topologically sorting sections to satisfy forward references

**What people do:** Notice that AccidentalDefinitions reference CompositeDefinitions in a later section, conclude this is a bug, reorder sections to compositeDefinitions → accidentalDefinitions.

**Why it's wrong:** Dorico's own export emits the canonical order (temperaments → accidentalSystems → accidentalDefinitions → tonalitySystemDefinitions → textDefinitions → glyphDefinitions → compositeDefinitions). Two-pass entityID resolution is how Dorico parses, so forward references work fine. Reordering would diverge from any Dorico-exported file and break round-trip diffs.

**Do this instead:** Emit in the canonical order verbatim. If forward references make tooling unhappy (e.g. a hypothetical XSD validator), it's the tool that's wrong, not the schema.

### Anti-Pattern 2: Auto-reducing pitchDeltaFromNatural fractions

**What people do:** Use `Fraction(114, 1200)` and let it auto-reduce to `Fraction(19, 200)` because Python's Fraction class normalizes by default.

**Why it's wrong:** The template uses `69/1200` and `-14/1200` literally — Dorico stores raw `n/1200` rationals (and sometimes `n/24` for natural — see template). Auto-reducing produces `19/200` etc., which may parse correctly but diverges visibly from any Dorico-exported file. Worse, it's harder to debug ("is this 114¢ or 14¢?" is harder to answer when you see `19/200`).

**Do this instead:** Build the rational string manually as `f"{cents}/1200"`. For zero deviation, emit `"0/1200"` (the template's `0/24` for Natural is a Dorico-side legacy that we don't need to reproduce since our generator's output is authoritative).

### Anti-Pattern 3: Storing entity IDs as raw UUID objects in dataclasses

**What people do:** Make `entity_id: uuid.UUID` a field, then format it on emission.

**Why it's wrong:** entityIDs in Dorico's format are `<kind>.user.<32-hex>` — they're not raw UUIDs, they're prefix-tagged strings. Storing as `uuid.UUID` requires every reference site to remember the kind prefix, which is error-prone (mix up `glyph` and `text` and the file silently breaks).

**Do this instead:** Store as `str` with the full prefix (`"glyph.user.bf2fcca40371420f99106bd86bf99ab8"`). The `entity_id(kind, key)` helper in `uuids.py` is the only place that knows the prefix format. Treat the resulting string as the canonical ID throughout.

### Anti-Pattern 4: Pretty-printing XML with ElementTree's default `tostring(pretty_print=...)`

**What people do:** Call `ET.tostring(root, encoding="utf-8", pretty_print=True)` or rely on minidom's `toprettyxml()`.

**Why it's wrong:** `pretty_print=True` doesn't exist in stdlib ElementTree (that's lxml). Minidom's `toprettyxml()` uses 2-space indent and inserts trailing whitespace inconsistently — both diverge from Dorico's tab-indent canonical output. Worse, minidom round-trips strip and recreate the XML declaration in subtly different ways.

**Do this instead:** Use `ET.indent(tree, space="\t", level=0)` (Python 3.9+) which produces tab-indented output, then `ET.tostring(root, encoding="utf-8", xml_declaration=True)`. Verify with a hex dump that the indent character is `\t` (0x09), not multiple spaces (0x20).

### Anti-Pattern 5: Re-using a fresh PROJECT_NAMESPACE on each major version

**What people do:** "v2 is a major change, let's rotate the namespace UUID."

**Why it's wrong:** Every existing user's library would gain duplicate entities on import (old IDs from v1 + new IDs from v2). Dorico has no "merge by name" fallback; it matches strictly on entityID.

**Do this instead:** **Pin `PROJECT_NAMESPACE` once at project inception. Never rotate.** If a v2 needs to "rename" an accidental (e.g. change the key from `sharp+14` to `Sharp +14`), document it as a migration step in the README and ship a one-time cleanup script — don't try to solve it via UUID rotation.

### Anti-Pattern 6: Inlining glyph or text content directly into composite XML

**What people do:** Try to put `<codePoint>0xE262</codePoint>` directly inside the `<component>` element, skipping the `GlyphPrimitiveEntityDefinition` indirection.

**Why it's wrong:** The schema requires composites to reference glyphs and texts by entityID — there's no inline form. Trying it produces a file Dorico rejects on import.

**Do this instead:** Always emit the GlyphPrimitiveEntityDefinition / TextPrimitiveEntityDefinition first (logically — actually they're emitted in a later section, but they exist as separate entities), and reference them by entityID from the composite's `<componentId>`.

---

## Integration Points

### External services / files

| Service | Integration Pattern | Notes |
|---|---|---|
| Dorico Pro 6.x | File-based: `.doricolib` dropped into `~/Library/Application Support/Steinberg/Dorico 6/DefaultLibraryAdditions/` (macOS) or imported via Library Manager | One-way: we emit, Dorico consumes. No round-trip API. Validation = manual import + playback test. |
| SMuFL / Bravura font | Static codepoint references (`0xE260`, `0xE261`, `0xE262`) | Bundled with Dorico; we reference by `font.defaultmusic` style alias, not by font family name. No external dependency at our build step — codepoints are constants. |
| User's tuner (validation only) | Manual: play a note, listen, compare | One-time per cent value during validation phase; not automatable. |

### Internal boundaries

| Boundary | Communication | Notes |
|---|---|---|
| `compose.py` ↔ `uuids.py` | Function call: `entity_id(kind, key)` | Pure dependency; uuids.py has no knowledge of compose.py. |
| `compose.py` ↔ `entities.py` | Constructor calls: `AccidentalDef(...)`, `CompositeDef(...)`, etc. | Frozen dataclasses; no setters; immutable from creation. |
| `main.py` ↔ `compose.py` | Function call: `build_accidental(base, cents) → AccidentalBundle` | One call per accidental; main.py drives the loop and dedupe. |
| `main.py` ↔ `emit.py` | Function call: `emit.write(path, sections)` | Sections is a `dict[str, list[Entity]]` keyed by section name. |
| `emit.py` ↔ `entities.py` | Method call: `entity.to_xml() → ET.Element` | Each entity dataclass owns its XML serialization. emit.py only knows how to wrap and write. |

---

## Sources

### Authoritative — HIGH confidence

- [Working template `TonalitySystemStartTemplate.doricolib`](file:///Users/taylorbrook/Dev/dorico%20tonality/TonalitySystemStartTemplate.doricolib) — primary source-of-truth for the entity graph, cross-reference patterns, and section emission order. Hand-validated by user against Dorico Pro 6.x.
- Sibling research file `/Users/taylorbrook/Dev/dorico tonality/.planning/research/STACK.md` — stack decisions, schema details, SMuFL codepoints, deterministic UUID strategy.
- Sibling research file `/Users/taylorbrook/Dev/dorico tonality/.planning/research/FEATURES.md` — naming conventions, panel UX constraints, in-Dorico user flow.
- Project specification `/Users/taylorbrook/Dev/dorico tonality/.planning/PROJECT.md` — scope, requirements, key decisions.
- [Python `xml.etree.ElementTree` documentation](https://docs.python.org/3/library/xml.etree.elementtree.html) — `ET.indent()` since 3.9, attribute-order preservation since 3.8.
- [Python `uuid` documentation (RFC 9562)](https://docs.python.org/3/library/uuid.html) — uuid5 deterministic namespace UUIDs.

### Steinberg / Dorico — MEDIUM confidence (no public schema)

- [Edit Tonality System dialog (Dorico Pro v5 archive)](https://archive.steinberg.help/dorico_pro/v5/en/dorico/topics/library/library_tonality_systems_edit_tonality_system_dialog_r.html) — confirms tonality system = temperament + accidentals + (optional) custom key signatures.
- [Custom accidentals (Dorico Pro v5 archive)](https://www.steinberg.help/r/dorico-pro/5.1/en/dorico/topics/library/library_tonality_systems_custom_accidentals_c.html) — confirms composite = glyph + text + graphic components.
- [Importing libraries (Dorico v5 archive)](https://archive.steinberg.help/dorico/v5/en/dorico/topics/library/library_importing_t.html) — confirms re-import-by-entityID semantics.

---

*Architecture research for: Dorico cents tonality system (`.doricolib` library + Python generator)*
*Researched: 2026-05-01*
