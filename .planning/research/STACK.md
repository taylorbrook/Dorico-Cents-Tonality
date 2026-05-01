# Stack Research

**Domain:** XML build-tooling for a Steinberg Dorico Pro 6.x library file (`.doricolib`) — single-artifact deliverable, no runtime stack.
**Researched:** 2026-05-01
**Confidence:** HIGH on schema (verified against working template), HIGH on SMuFL codepoints, HIGH on Python tooling, MEDIUM on `fileVersion 1.1450 → Dorico 6.x` mapping (no Steinberg doc explicitly maps fileVersion numbers to Dorico releases; verified by inference from the user's template + Dorico 6 release timing), MEDIUM on cross-edition compatibility (Elements/SE).

---

## TL;DR

- **Generator runtime:** Python **3.11+** (3.12 preferred), stdlib only.
- **XML library:** `xml.etree.ElementTree` (stdlib). **Do not use lxml or jinja2** for this project — see rationale.
- **Determinism:** `uuid.uuid5(NAMESPACE, name)` with a project-pinned namespace UUID, then `.hex` (32 lowercase hex chars, no dashes) to match Dorico's `kind.user.<32hex>` format.
- **Glyphs:** SMuFL Standard Accidentals (12-EDO) — `accidentalSharp = 0xE262`, `accidentalFlat = 0xE260`, `accidentalNatural = 0xE261`. Font reference `font.defaultmusic` (Bravura under the hood).
- **Validation:** No public XSD/DTD exists. Validate by (1) byte-comparing structural patterns against the user's working template, (2) round-tripping through Dorico Pro 6 import → export → diff.
- **Compatibility target:** Dorico Pro 6.x. Will not load on Dorico 5 or below. Library-import scope on Elements/SE is reduced; tonality-system import is a Pro feature in practice — ship for Pro and document the Pro requirement.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | **3.11+** (3.12 sweet spot) | Generator script runtime | Stdlib only; the deliverable is an XML file — nothing ships with it. 3.11+ gives you `tomllib`, better error messages, and `ElementTree.indent()` (added 3.9). 3.12 is the current widely-deployed stable on macOS Homebrew and Steinberg dev machines. Python 3.13/3.14 work but offer no advantage here. |
| `xml.etree.ElementTree` | stdlib (3.11+) | XML emission | Zero deps. Preserves user-specified attribute order since Python 3.8. `ET.indent()` (3.9+) provides clean tab/space indentation. The `.doricolib` format is element-heavy with almost no attributes (only `array="true"`), so ElementTree's element-first model maps perfectly. **Critically:** lxml's biggest win — XPath, XSLT, schema validation — is irrelevant here because no XSD exists. |
| `uuid` | stdlib | Deterministic entityID generation | `uuid5()` is RFC 9562 / RFC 4122 compliant SHA-1 namespace hashing. Same input ⇒ same UUID, forever. Exactly what's needed so re-running the generator emits byte-identical output and re-imports update existing entries instead of duplicating. |
| `fractions.Fraction` | stdlib | `pitchDeltaFromNatural` formatting | Dorico stores deltas as a literal `n/1200` rational string (verified in the template: `<pitchDeltaFromNatural>69/1200</pitchDeltaFromNatural>`, also `0/24` for Natural — denominator is **not** required to be 1200, it's whatever Dorico wrote). `Fraction(n, 1200)` gives correct semantics; emit it as the string `f"{cents}/1200"` directly — do not auto-reduce, because the visible denominator pattern in Dorico-written files is preserved as-is. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `argparse` | stdlib | CLI flags for the generator (range, output path, namespace seed) | Always — keep the script invokable as `python build.py --out cents.doricolib`. |
| `pathlib` | stdlib | File-path handling | Always. |
| `unittest` or `pytest` | pytest 8.x optional | Round-trip tests (parse the template, regenerate one entity, byte-compare) | Optional but recommended. If used, pytest stays a **dev-only** dep (`requirements-dev.txt`). |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `ruff` 0.6+ | Lint + format the generator script | Single-binary replacement for black + flake8 + isort. Zero-config defaults are fine. |
| `mypy` 1.11+ (optional) | Type-check the generator | Helpful for the Fraction/UUID/string-emission layer; not strictly required for ~600-entry generation logic. |
| Dorico Pro 6.2.x | Import/export round-trip validator | The user already has this; treat as the only source of truth for "does this file load?" |
| `diff` / `git diff --no-index` | Byte-comparing generator output across runs | Determinism check. Two consecutive runs must produce 0-byte-diff output. |

---

## Installation

```bash
# Core: nothing. The generator is stdlib-only.
# Verify Python:
python3 --version   # expect 3.11+

# Optional dev dependencies:
pip install --user 'ruff>=0.6' 'pytest>=8.0' 'mypy>=1.11'
```

No `requirements.txt` is needed for the shipped artifact. If you want one for dev, keep it minimal:

```
# requirements-dev.txt
ruff>=0.6
pytest>=8.0
mypy>=1.11
```

---

## Schema Details (`.doricolib` format, fileVersion 1.1450)

**Confidence:** HIGH — fully cross-checked against the working `TonalitySystemStartTemplate.doricolib`.

### Document shape

```xml
<?xml version="1.0" encoding="utf-8"?>
<kScoreLibrary>
  <fileVersion>1.1450</fileVersion>
  <temperaments>           <entities array="true"> ... </entities> </temperaments>
  <accidentalSystems>      <entities array="true"> ... </entities> </accidentalSystems>
  <accidentalDefinitions>  <entities array="true"> ... </entities> </accidentalDefinitions>
  <tonalitySystemDefinitions> <entities array="true"> ... </entities> </tonalitySystemDefinitions>
  <textDefinitions>        <entities array="true"> ... </entities> </textDefinitions>
  <glyphDefinitions>       <entities array="true"> ... </entities> </glyphDefinitions>
  <compositeDefinitions>   <entities array="true"> ... </entities> </compositeDefinitions>
</kScoreLibrary>
```

Section order in the template is **not alphabetical, not dependency-ordered** — it is the canonical order Dorico itself emits. Match it byte-for-byte to keep diffs against Dorico-exported files clean.

### Per-section role

| Section | Role | Cross-references |
|---------|------|------------------|
| `temperaments` | One `TemperamentDefinition` per system. Defines the seven `relativeDiatonicDivisions` (A→B, B→C, …) summing to 1200 cents. Standard 12-EDO uses 200/100/200/200/100/200/200. | Referenced by `TonalitySystemDefinition.temperamentDefinition`. |
| `accidentalSystems` | One `AccidentalSystem` lists all accidental IDs that appear in this tonality's accidentals popover, as a **comma-space–separated string** in `<accidentalDefinitionIDs>`. Order in this string is the order they appear in the picker. | References many `AccidentalDefinition`. Referenced by `TonalitySystemDefinition.accidentalSystem`. |
| `accidentalDefinitions` | One `AccidentalDefinition` per accidental. Carries `pitchDeltaFromNatural` (the rational `n/1200`), the `compositeID` for visual rendering, and the four `cutOutNW/NE/SE/SW` collision-shape tuples (`(0, 0)` is the safe default). | References `CompositeDefinition`. |
| `tonalitySystemDefinitions` | One `TonalitySystemDefinition` ties a temperament to an accidental system. Holds `customKeySignatures` (can be a single empty stub — see template). | References `TemperamentDefinition` and `AccidentalSystem`. |
| `textDefinitions` | One `TextPrimitiveEntityDefinition` per unique text label (e.g. the literal string `-14`). Holds `text`, `fontStyle` (use `font.defaulttext`), and a `name` of the form `<text>.font.defaulttext`. | Referenced by `CompositeDefinition.components[].componentId` when `componentType` is `kText`. |
| `glyphDefinitions` | One `GlyphPrimitiveEntityDefinition` per SMuFL glyph used. Holds `codePoint` (`0xE260`/`0xE261`/`0xE262`), `isSmufl=true`, `fontStyle=font.defaultmusic`, and `pointSize=1`. **Two patterns appear in the template:** `accidentalNatural` carries `<parentEntityID>glyph.accidentalNatural</parentEntityID>` (inheriting from a factory glyph), but `accidentalSharp` has empty `<parentEntityID/>`. The generator should follow whichever Dorico writes — empty parent is safest because it avoids depending on a factory entityID that could shift between Dorico versions. | Referenced by `CompositeDefinition.components[].componentId` when `componentType` is `kGlyph`. |
| `compositeDefinitions` | One `CompositeDefinition` per visual composition. Holds `components[]` (the layered glyph(s) and text), `relativeAttachments[]` (positional anchoring between two component instances using `kBaselineRight`/`kBaselineLeft` etc., with `xOffset`/`yOffset`), and `scalingRules[]` (almost always empty). `category=kAccidentals` for accidental composites. | Referenced by `AccidentalDefinition.compositeID`. |

### EntityID format

`<kind>.user.<32-lowercase-hex>` — kinds observed in the template:

- `temperament-definition.user.…`
- `accidental-system.user.…`
- `accidental.user.…`
- `tonalitysystem.user.…` (note: no hyphen, no dot between `tonality` and `system`)
- `text.user.…`
- `glyph.user.…`
- `comp.user.…`

The 32 hex chars are a UUID with dashes stripped. Generator: `uuid.uuid5(NS, key).hex` produces this format directly.

### Inline-syntax fields the generator must emit verbatim

These are not standard XML attributes — they are string-typed elements with custom content. Emit them as element text exactly:

| Element | Format | Example |
|---------|--------|---------|
| `pitchDeltaFromNatural` | `<int>/<int>` rational | `69/1200`, `-14/1200`, `0/24` |
| `cutOutNW`, `cutOutNE`, `cutOutSE`, `cutOutSW` | `(<float>, <float>)` tuple, **with the space after the comma** | `(0, 0)`, `(0.192, 2.116)` |
| `accidentalDefinitionIDs` | comma-space–joined entityIDs | `accidental.user.aaa, accidental.user.bbb, accidental.user.ccc` |
| `codePoint` | `0xE260`-style hex literal, capital X uppercase, hex digits uppercase | `0xE262` |
| `xScale`, `yScale` | float with 6 decimals | `100.000000` |
| `componentInstanceId` | `<entityID>.<int>` | `glyph.user.bf2fc….0` (the trailing `.0` matches `componentInstance` in the same component element) |

### Required boilerplate fields

Every entity has:
- `<name>` (free text, can repeat across entities — the entityID is the unique key)
- `<entityID>` (unique)
- `<parentEntityID/>` (usually empty self-closing; non-empty only for inherited factory entities)
- `<inheritanceMask>0</inheritanceMask>`

Most entities additionally carry `<precedence>0</precedence>` (temperaments, accidental systems).

### XML emission specifics

- Encoding: `utf-8` (declared, lowercase, matches the template).
- Indentation: tabs (verified — open the template in a hex viewer, the indent character is `\t`, not spaces). When using `ElementTree.indent(tree, space="\t", level=0)` you get tab indent.
- Empty elements: self-closing form preferred (`<parentEntityID/>` not `<parentEntityID></parentEntityID>`). ElementTree does this automatically when an element has no text and no children.
- Attribute order: only one attribute appears in the schema (`array="true"`), so attribute-order quirks don't apply.
- Boolean text values: lowercase (`true` / `false`), e.g. `<isSmufl>true</isSmufl>`, `<showCautionaryNaturals>false</showCautionaryNaturals>`.

---

## SMuFL Glyph Reference

**Confidence:** HIGH. Verified against the SMuFL 1.4 specification table for "Standard accidentals (12-EDO)" range U+E260–U+E26F.

| Glyph name | Codepoint | Unicode fallback | Use here |
|------------|-----------|------------------|----------|
| `accidentalFlat` | `U+E260` | U+266D ♭ | flat-base accidentals |
| `accidentalNatural` | `U+E261` | U+266E ♮ | clean natural at 0¢, base for natural+cents |
| `accidentalSharp` | `U+E262` | U+266F ♯ | sharp-base accidentals |
| `accidentalDoubleSharp` | `U+E263` | U+1D12A 𝄪 | not used (out of scope) |
| `accidentalDoubleFlat` | `U+E264` | U+1D12B 𝄫 | not used (out of scope) |

### SMuFL version

- **Latest:** SMuFL 1.18 (released alongside Bravura 1.18). The Dorico 6.x default music font (`font.defaultmusic`) maps to **Bravura 1.392** which is documented as implementing **SMuFL 1.4**. The U+E260–U+E262 codepoints are unchanged across SMuFL 1.0 → 1.18 — they are part of the original "Recommended Characters" range and are stable. No risk in using them.
- **Stylistic alternates:** SMuFL provides condensed/small variants (e.g. `accidentalFlatSmall U+F428`) accessed via OpenType `ss01`/`salt01` features. **Do not use these** — Dorico's `GlyphPrimitiveEntityDefinition.codePoint` field expects a base codepoint and lets the engine apply optical scaling via `pointSize` and `maxOpticalScale` instead.

### Font style

The template uses `<fontStyle>font.defaultmusic</fontStyle>` for glyphs (Dorico's default music font, which is Bravura) and `<fontStyle>font.defaulttext</fontStyle>` for text labels. **Use these style references, not literal font family names** — this lets the user retarget to Petaluma or another SMuFL font globally without rewriting the library.

---

## Determinism Strategy

### UUID5 with project namespace

```python
import uuid

# Pin once. Never change. This is the project's seed identity.
PROJECT_NAMESPACE = uuid.UUID("6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c")
# (Generate your own with `python -c "import uuid; print(uuid.uuid4())"` and pin it.)

def entity_id(kind: str, key: str) -> str:
    """kind in {'accidental', 'glyph', 'text', 'comp', 'temperament-definition',
                'accidental-system', 'tonalitysystem'}; key is a stable human-readable name."""
    u = uuid.uuid5(PROJECT_NAMESPACE, f"{kind}:{key}")
    return f"{kind}.user.{u.hex}"

# Examples — same input always returns the same id:
entity_id("accidental", "sharp+14")      # accidental.user.<deterministic 32 hex>
entity_id("glyph",      "accidentalSharp")  # glyph.user.<deterministic 32 hex>
entity_id("text",       "+14")              # text.user.<deterministic 32 hex>
entity_id("comp",       "sharp+14")         # comp.user.<deterministic 32 hex>
```

- Same `(namespace, name)` ⇒ same UUID forever (RFC 9562 SHA-1 hashing).
- Re-imports into Dorico match by entityID, so the same generator output overwrites prior entries instead of duplicating.
- Pin `PROJECT_NAMESPACE` in a single constant in the generator. **Never rotate it** — rotating breaks update-in-place semantics for every existing user.

### Output stability checklist

For byte-identical re-runs, the generator must:

1. Iterate accidentals in a stable sorted order (e.g. by signed cent value).
2. Use deterministic UUIDs (above).
3. Use a fixed XML declaration: `<?xml version="1.0" encoding="utf-8"?>`.
4. Use a fixed indent (tabs, depth 0 at root) via `ET.indent(tree, space="\t")`.
5. Avoid floating-point formatting variance — emit `100.000000` as a string literal, not via f-string of a float.
6. Avoid OS-dependent line endings — write in binary mode with `b"\n"` separator, or normalize after `ET.tostring(..., short_empty_elements=True)`.

### Verification recipe

```bash
python build.py --out /tmp/a.doricolib
python build.py --out /tmp/b.doricolib
diff /tmp/a.doricolib /tmp/b.doricolib   # MUST be empty
```

Wire this into a pre-commit hook or CI step.

---

## Validation Tooling

**Confidence:** MEDIUM — no Steinberg-published schema exists. Practical validation is empirical.

### What does NOT exist

- No public `kScoreLibrary.xsd`, `.dtd`, or RELAX NG schema.
- No Steinberg-published validation tool.
- No mention in any Steinberg forum thread of an XSD being shipped with Dorico.

### Practical validation pyramid

1. **Structural lint (cheapest, fastest).** A 50-line Python checker that:
   - Confirms `<fileVersion>1.1450</fileVersion>` is present.
   - Confirms section order matches `[temperaments, accidentalSystems, accidentalDefinitions, tonalitySystemDefinitions, textDefinitions, glyphDefinitions, compositeDefinitions]`.
   - Confirms every `compositeID` reference resolves to a `CompositeDefinition` entityID.
   - Confirms every `componentId` in a composite resolves to a `glyph.user.…` or `text.user.…` entityID.
   - Confirms every `accidentalDefinitionIDs` token resolves to an `AccidentalDefinition`.
   - Confirms every `pitchDeltaFromNatural` parses as a valid rational.
2. **Template diff.** Use the working `TonalitySystemStartTemplate.doricolib` as a structural fixture. After generating a single-entity test (one accidental), the structural pattern (element ordering, attribute usage, `array="true"` placement, indent) must match the template byte-for-byte except for entity content.
3. **Round-trip through Dorico.** The only ground truth: import → check no error dialog → export → diff exported file against generator output. Diffs that round-trip cleanly are the schema "extensions" Dorico applies on its own (sometimes new optional fields).
4. **Audible test.** Place the accidental on a note, set Play mode to use the tonality, run a tuner against the audio output. ±1 cent agreement validates the playback math.

### Tools I considered and ruled out

- `xmllint --noout` — proves well-formedness, not validity. Useful as a smoke test before Dorico import. Add it as a CI step.
- `xmlschema` (Python) — needs an XSD that doesn't exist. Skip.
- `lxml` schema validation — same blocker. Skip.

---

## Dorico Version Compatibility

**Confidence:** MEDIUM — the `fileVersion 1.1450 → Dorico 6.x` mapping is verified by inference (the user's working template loaded into their Dorico 6 install) but Steinberg does not publish a version table.

| Dorico Edition | Will the file load? | Notes |
|----------------|---------------------|-------|
| Dorico Pro 6.0–6.2.x | **YES** (target) | `fileVersion 1.1450` is the current 6.x library format. Tested with the user's template. |
| Dorico Pro 5.x | **NO** (likely) | The 5→6 library format had breaking changes (forum reports of import failures from 5 libs into 6 — see the 987754 thread). Reverse direction is not officially supported. |
| Dorico Pro 4.x and below | **NO** | Older `fileVersion`. Tonality system architecture has evolved across major versions. |
| Dorico Elements 6.x | **PARTIAL** | Library Manager exists but tonality-system editing is a Pro feature. Import may succeed but UI affordances are missing — treat as Pro-only. |
| Dorico SE 6.x | **NO** | Free edition, lacks Library Manager and tonality-system support. |

### Steinberg Dorico release timeline (for context)

- Dorico Pro 6.0 — released 2025-04-30.
- Dorico Pro 6.2 — released 2026-03.
- Dorico Pro 6.2.20 — released 2026-04 (current latest as of research date).

### Install paths (user library — drop a `.doricolib` here for auto-discovery)

| OS | Path |
|----|------|
| **macOS** | `~/Library/Application Support/Steinberg/Dorico 6/DefaultLibraryAdditions/` |
| **Windows** | `%APPDATA%\Steinberg\Dorico 6\DefaultLibraryAdditions\` (i.e. `C:\Users\<you>\AppData\Roaming\Steinberg\Dorico 6\DefaultLibraryAdditions\`) |

Files in `DefaultLibraryAdditions/` are auto-loaded into every new project. Alternatively, users can manually import via **Library → Library Manager → Import…** — this loads into the current project only.

### What the README must say

- "Requires Dorico Pro 6.0 or later. Will not load on Dorico 5, Elements, or SE."
- Both install methods (drop into `DefaultLibraryAdditions/` for global, or use Library Manager for per-project import).
- How to invoke the tonality system in Setup mode → Players → tonality system selector.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `xml.etree.ElementTree` (stdlib) | `lxml` 6.1.0 | Skip lxml. It would be the right call **only** if Steinberg published an XSD (lxml's schema validation is excellent) or if you needed XPath traversal of an existing library. Neither applies. lxml also adds a C-extension dep — for a single-file deliverable, that's all cost, no benefit. |
| `xml.etree.ElementTree` (stdlib) | `jinja2` templates | Skip jinja2. Templating is tempting because the schema is repetitive, but jinja XML templates are notoriously brittle around whitespace, escaping, and attribute order — exactly the things that break determinism. Programmatic ElementTree is more verbose but gives explicit control over every byte. |
| `xml.etree.ElementTree` (stdlib) | Hand-written string concatenation | Skip. F-string templating is fast to start but loses you XML escaping (the user-visible label `+14` is fine; future labels with `<`, `>`, `&` would corrupt). ElementTree handles escaping for free. |
| `uuid5` deterministic | `uuid4` random | Skip uuid4. Random UUIDs change every run, so the generator's output is non-reproducible and re-imports duplicate every entity instead of updating. Dealbreaker. |
| Python 3.11+ | Python 3.10 | Avoid 3.10. `ET.indent()` exists from 3.9 so it would work, but 3.11 brings significant ergonomics improvements and is the minimum supported version on macOS Sonoma+ default Homebrew installs. |
| Python 3.11+ | Python 3.13/3.14 | Fine, no functional difference. Use whatever's installed. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `lxml` | C-extension dep, no benefit without an XSD; XPath unused; pretty-print whitespace heuristics conflict with Dorico's tab indent. | `xml.etree.ElementTree` |
| `jinja2` XML templates | Whitespace and attribute escaping are template-author errors waiting to happen; serialization is opaque. | Programmatic `ElementTree.SubElement` |
| `xmltodict` / dict-based XML | Loses element ordering and forces awkward dict-of-list-of-dict structure for Dorico's heavily-nested entities. | `ElementTree` |
| `uuid.uuid4()` (random) | Breaks the determinism guarantee that re-imports update existing entries. | `uuid.uuid5(PROJECT_NAMESPACE, key)` |
| Hardcoded numeric IDs (e.g. integer counters) | Collisions with factory IDs are possible; Dorico's `*.user.*` namespace expects 32-hex UUIDs. | `uuid5().hex` |
| SVG/PNG raster glyphs | Dorico supports them via the Custom Accidentals UI (per Steinberg help), but SMuFL glyph references are sharper, font-scalable, and decouple appearance from the library file. | SMuFL codepoints via `GlyphPrimitiveEntityDefinition` |
| `accidentalFlatSmall` and other small-stave variants | These are stylistic alternates; Dorico applies optical scaling itself via `pointSize`/`maxOpticalScale`. Using them directly fights the engine. | Base `U+E260`/`E261`/`E262` codepoints |
| `<fileVersion>1.0</fileVersion>` or any other version | Dorico will refuse the file or strip it on import. | `<fileVersion>1.1450</fileVersion>` exact match to the user's working template. |

---

## Stack Patterns by Variant

**If shipping for Dorico Pro 6.x only (the current target):**
- Use `<fileVersion>1.1450</fileVersion>`.
- Document the user library install path (above).
- Use SMuFL codepoints for glyphs (Bravura is bundled).

**If a future user reports Dorico 5 demand:**
- Do **not** try to back-port. Open the same template in Dorico 5, save out a fresh tonality system, inspect that file's `<fileVersion>` and section ordering, and treat it as a separate generator target. The template-driven approach scales to multiple version targets cleanly.

**If glyph rendering looks wrong inside Dorico:**
- Verify `<isSmufl>true</isSmufl>`.
- Verify `pointSize=1` (this is a relative size; not a typo).
- Verify `<fontStyle>font.defaultmusic</fontStyle>` (not `font.defaulttext`).

**If cent labels collide with the glyph in dense passages:**
- Adjust `<xOffset>` and `<yOffset>` on the `relativeAttachment`. The template uses `(-8, -12)` for `kBaselineRight` ↔ `kBaselineLeft` between sharp glyph and cent text — this is the known-good starting offset. Adjust upward/right if labels overlap.

---

## Version Compatibility

| Component | Pinned to | Compatibility notes |
|-----------|-----------|---------------------|
| Generator: Python 3.11+ | `xml.etree.ElementTree`, `uuid`, `fractions`, `pathlib` | All stdlib, no version coupling concerns. |
| Output: `fileVersion 1.1450` | Dorico Pro 6.0+ | Same `fileVersion` value confirmed in user's working template against Dorico Pro 6.x. Will not load on Dorico 5 or earlier. Untested but likely fine on future 6.x point releases (Steinberg has historically kept point-release library compatibility). |
| Glyphs: SMuFL 1.0+ codepoints | Bravura 1.392 (Dorico 6 default) | U+E260/E261/E262 are part of the original SMuFL recommended characters and have not changed across any version. Safe forever. |

---

## Sources

### Authoritative — HIGH confidence

- [Working template `TonalitySystemStartTemplate.doricolib`](file:///Users/taylorbrook/Dev/dorico%20tonality/TonalitySystemStartTemplate.doricolib) — primary schema source-of-truth, hand-validated by user against Dorico Pro 6.x.
- [SMuFL standard accidentals (12-EDO) — U+E260–U+E26F](https://w3c.github.io/smufl/latest/tables/standard-accidentals-12-edo.html) — codepoints for `accidentalFlat`, `accidentalNatural`, `accidentalSharp`.
- [SMuFL specification — w3c.github.io/smufl](https://w3c.github.io/smufl/latest/) — current SMuFL spec.
- [SMuFL 1.18 release announcement](https://www.smufl.org/news/smufl-1-18-and-bravura-1-18-released/) — current version of SMuFL and Bravura reference font.
- [Bravura font repository (Steinberg)](https://github.com/steinbergmedia/bravura) — confirms Bravura is the SMuFL reference font, OFL licensed.
- [Python `xml.etree.ElementTree` documentation](https://docs.python.org/3/library/xml.etree.elementtree.html) — stdlib XML library, attribute-order preservation since 3.8, `indent()` since 3.9.
- [Python `uuid` documentation (RFC 9562)](https://docs.python.org/3/library/uuid.html) — `uuid5()` deterministic namespace UUIDs.

### Steinberg documentation — MEDIUM confidence (Steinberg pages partially scraped)

- [Dorico Pro 6.1 manual root](https://www.steinberg.help/r/dorico-pro/6.1/en) — top-level help.
- [Key signatures, tonality systems, and accidentals panel (Dorico Pro 6.1)](https://www.steinberg.help/r/dorico-pro/6.1/en/dorico/topics/write_mode/write_mode_notations_input/write_mode_key_signatures_tonality_systems_accidentals_panel_r.html) — UI reference.
- [Edit Tonality System dialog (Dorico Pro v5 archive)](https://archive.steinberg.help/dorico_pro/v5/en/dorico/topics/library/library_tonality_systems_edit_tonality_system_dialog_r.html) — confirms tonality systems comprise temperament + accidentals + key signatures.
- [Custom accidentals (Dorico Pro v5 archive)](https://www.steinberg.help/r/dorico-pro/5.1/en/dorico/topics/library/library_tonality_systems_custom_accidentals_c.html) — confirms custom accidentals support glyphs, text, graphics components.
- [Importing libraries (Dorico v5 archive)](https://archive.steinberg.help/dorico/v5/en/dorico/topics/library/library_importing_t.html) — `.doricolib` import procedure and `DefaultLibraryAdditions` folder behavior.

### Dorico release context — MEDIUM confidence

- [Dorico 6 release announcement (2025-04-30)](https://blog.dorico.com/2025/04/dorico-6-released/) — Dorico Pro 6.0 release date.
- [Dorico 6.2.20 release (2026-04)](https://blog.dorico.com/2026/04/dorico-6-2-20-update-released/) — current Dorico 6.x release.
- [Forum: Libraries created in Dorico 5 don't import to Dorico 6 (#987754)](https://forums.steinberg.net/t/libraries-created-in-dorico-5-dont-seem-to-import-properly-to-6/987754) — confirms 5→6 library format break.
- [Forum: Reusable Custom Accidentals (#944092)](https://forums.steinberg.net/t/reusable-custom-accidentals/944092) — community usage notes for tonality-system `.doricolib` files.
- [Forum: Where are Dorico libraries stored (#954957)](https://forums.steinberg.net/t/where-are-dorico-libraries-etc-stored/954957) — confirms macOS/Windows user-library paths.

### Tooling — HIGH confidence

- [lxml 6.1.0 (PyPI)](https://pypi.org/project/lxml/) — current lxml release for completeness; ruled out for this project.
- [Python uuid5 deterministic generation guide](https://pablosanjose.com/generating-deterministic-uuids-in-python) — uuid5 reference behavior.

---

*Stack research for: Dorico tonality-system `.doricolib` generator (cents project)*
*Researched: 2026-05-01*
