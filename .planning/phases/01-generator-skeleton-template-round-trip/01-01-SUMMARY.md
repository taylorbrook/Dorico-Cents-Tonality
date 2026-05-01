---
phase: 01-generator-skeleton-template-round-trip
plan: 01
subsystem: generator-foundation
tags: [python, stdlib, uuid5, dataclasses, frozen-slots, smufl, dorico, xml-emission-deferred]

# Dependency graph
requires: []
provides:
  - "PROJECT_NAMESPACE pinned UUID 6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c (never-rotate)"
  - "entity_id(kind, key) deterministic helper returning '<kind>.user.<32 lowercase hex>'"
  - "constants module: FILE_VERSION='1.1450', SMUFL_FLAT/NATURAL/SHARP, FONT_DEFAULT_*, KIND_*, TEMPERAMENT_12EDO_DIVISIONS, SECTION_ORDER 7-tuple"
  - "9 frozen+slots entity dataclasses (Component, RelativeAttachment, TemperamentDef, AccidentalSystemDef, AccidentalDef, TonalitySystemDef, TextDef, GlyphDef, CompositeDef)"
  - "conftest.py + pytest infrastructure resolving cents_generator on PYTHONPATH"
affects: [01-02-emit, 01-03-orchestrator, 02-range-expansion, 03-validation]

# Tech tracking
tech-stack:
  added:
    - "Python 3.11+ stdlib (uuid, dataclasses) — verified working under Python 3.14.2"
    - "pytest 9.0.2 (dev-only test runner)"
  patterns:
    - "Frozen+slots dataclasses for all entity types — enforces immutability between construction and XML emission"
    - "Full prefixed entityID strings ('<kind>.user.<hex>'), never raw uuid.UUID — kind prefix is part of Dorico's reference contract"
    - "Tuples (not lists) for collection fields on frozen dataclasses — required for hashability/freezing"
    - "Raw 'n/1200' rational strings for pitchDeltaFromNatural — no auto-reduction (preserves '0/24' template idiom)"
    - "TDD RED→GREEN cycle for foundational logic (uuids, entities) — failing test commit precedes implementation commit"

key-files:
  created:
    - "src/cents_generator/__init__.py"
    - "src/cents_generator/uuids.py"
    - "src/cents_generator/constants.py"
    - "src/cents_generator/entities.py"
    - "tests/__init__.py"
    - "tests/test_uuids.py"
    - "tests/test_entities.py"
    - "conftest.py"
    - ".gitignore"
  modified: []

key-decisions:
  - "PROJECT_NAMESPACE = uuid.UUID('6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c') — pinned; rotation forbidden (would duplicate 1411 entities on every existing user's re-import)"
  - "entity_id signature: entity_id(kind: str, key: str) -> str using uuid5(PROJECT_NAMESPACE, f'{kind}:{key}').hex — kind is part of the hash input, so same key under different kinds yields different UUIDs"
  - "All 9 entity dataclasses are frozen+slots; collection fields use tuple[T, ...] not list[T] — required for frozen hash semantics"
  - "Conftest.py at project root inserts ./src on sys.path so 'cents_generator' resolves under pytest without needing a pyproject.toml install"
  - "Two distinct GlyphDef defaults preserved: parent_entity_id='' (sharp/flat — STACK.md preferred) vs parent_entity_id='glyph.accidentalNatural' (Natural — template line 130). Phase 1 reproduces both shapes faithfully; Phase 2 may unify on empty parent."
  - "Tab indent + 6-decimal float emission + uppercase-X hex + (x, y) tuple syntax — these formatting decisions are deferred to emit.py (Plan 02); entities.py stores typed values, not formatted strings"

patterns-established:
  - "Pinned-namespace + uuid5 derivation — every entityID hashes from the same seed, guaranteeing byte-identical re-runs"
  - "Test-first foundational logic — uuids and entities are TDD; constants is straight implementation (no behavioral surface to test beyond presence)"
  - "Acceptance-criteria–driven verification — each task's automated grep checks are run inline before commit"

requirements-completed: [GEN-03, GEN-04, SCH-02]

# Metrics
duration: 5.6min
completed: 2026-05-01
---

# Phase 01 Plan 01: Generator Skeleton Foundations Summary

**Pinned PROJECT_NAMESPACE UUID, deterministic entity_id() helper, project-wide constants module, and 9 frozen+slots dataclasses covering every entity type used by the three template entities (Natural / `-14` / `#-31`).**

## Performance

- **Duration:** 5.6 min (339 s)
- **Started:** 2026-05-01T23:10:14Z
- **Completed:** 2026-05-01T23:15:53Z
- **Tasks:** 3 of 3 complete
- **Files created:** 9
- **Files modified:** 0

## Accomplishments

- **Determinism foundation locked in.** `PROJECT_NAMESPACE = uuid.UUID('6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c')` is pinned in `src/cents_generator/uuids.py` with a NEVER ROTATE warning block. `entity_id('accidental', 'sharp+14')` returns `accidental.user.f95f5061066e544ead43514e6c06621f` deterministically across consecutive process invocations (verified twice in succession with identical hex output).
- **Constants module covers every magic value Plans 02 and 03 will need.** `FILE_VERSION='1.1450'`, the three SMuFL codepoints (`SMUFL_FLAT=0xE260`, `SMUFL_NATURAL=0xE261`, `SMUFL_SHARP=0xE262`), font-style aliases, 7 entity-kind prefixes (preserving the `tonalitysystem` no-hyphen schema quirk), 12-EDO divisions tuple, and `SECTION_ORDER` 7-tuple in canonical Dorico export order with a `DO NOT REORDER` warning.
- **9 frozen+slots dataclasses cover every shape in the template.** `Component`, `RelativeAttachment`, `TemperamentDef`, `AccidentalSystemDef`, `AccidentalDef`, `TonalitySystemDef`, `TextDef`, `GlyphDef`, `CompositeDef`. EntityIDs stored as full prefixed strings; `pitch_delta_from_natural` stored as raw string (no auto-reduction); `accidental_definition_ids` stored as `tuple[str, ...]` (immutable).
- **25 unit tests pass.** 10 in `tests/test_uuids.py` (format, determinism, kind/key sensitivity, lowercase hex, no-hyphens, pinned-namespace check), 15 in `tests/test_entities.py` (construction, frozen semantics, default cutouts, template-faithful overrides for Natural/Class A/B/C composites).

## Task Commits

Each task was committed atomically. TDD-tagged tasks have separate RED (test) and GREEN (implementation) commits:

1. **Task 1 RED: Failing tests for entity_id and PROJECT_NAMESPACE** — `0f86cc3` (test)
2. **Task 1 GREEN: Pin PROJECT_NAMESPACE + implement entity_id** — `026223b` (feat) — also adds `.gitignore` for Python cache directories
3. **Task 2: Project-wide constants module** — `9aab757` (feat)
4. **Task 3 RED: Failing tests for entity dataclasses** — `955d6ac` (test)
5. **Task 3 GREEN: Implement frozen entity dataclasses** — `ad0d3ba` (feat)

_Plan metadata commit (this SUMMARY + STATE/ROADMAP updates) follows separately._

## Files Created/Modified

- `src/cents_generator/__init__.py` — package marker (empty)
- `src/cents_generator/uuids.py` — pinned `PROJECT_NAMESPACE` + `entity_id(kind, key)` helper with `NEVER ROTATE` warning block
- `src/cents_generator/constants.py` — `FILE_VERSION`, SMuFL codepoints, font-style aliases, kind prefixes, 12-EDO divisions tuple, `SECTION_ORDER` 7-tuple
- `src/cents_generator/entities.py` — 9 frozen+slots dataclasses for every entity shape in the template
- `tests/__init__.py` — test package marker (empty)
- `tests/test_uuids.py` — 10 determinism + format tests (one more than the plan's stated 9 — see Deviations)
- `tests/test_entities.py` — 15 dataclass construction + frozen-semantics tests
- `conftest.py` — pytest infrastructure inserting `./src` on `sys.path` so `import cents_generator` resolves without an installed package
- `.gitignore` — excludes `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, build/dist directories

## Decisions Made

- **Followed the plan's interface contract exactly.** `uuids.py`, `constants.py`, and `entities.py` public surfaces match the `<interfaces>` section of the plan. No structural changes; the only divergence is a single comment rewording (see Deviations).
- **Conftest.py over pyproject.toml.** Plan suggested `conftest.py` as the simplest path-resolution shim. Adopted as-is — no `pyproject.toml` install needed for Phase 1; can be added later if Plan 03 needs CLI installation.
- **Added `.gitignore` proactively.** No `.gitignore` existed in the repo before this plan. Once `pytest` and `python` started running, `__pycache__/` and `.pytest_cache/` appeared as untracked. Per the executor protocol on untracked files, generated artifacts get gitignored. Committed alongside Task 1 GREEN since it's necessary infrastructure.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Reworded a comment so it does not literally contain `uuid.uuid4(`**

- **Found during:** Task 1 GREEN, post-implementation acceptance-criteria check
- **Issue:** Acceptance criterion required `grep -E 'uuid\.uuid[14]\(' src/cents_generator/uuids.py` to return 0 matches. The original comment block contained the literal text `python -c "import uuid; print(uuid.uuid4())"` describing how `PROJECT_NAMESPACE` was generated, which matched the regex.
- **Fix:** Rephrased the comment to read "generated once with a random-UUID call (uuid v4) at project inception" — preserves the intent while avoiding the regex match. The actual implementation already used `uuid.uuid5` exclusively; the comment was the only false positive.
- **Files modified:** `src/cents_generator/uuids.py`
- **Verification:** `grep -cE 'uuid\.uuid[14]\(' src/cents_generator/uuids.py` now returns 0; all 10 unit tests still pass.
- **Committed in:** `026223b` (rolled into Task 1 GREEN before commit)

### Test count differs from plan (10 vs. 9 in test_uuids.py)

- **Plan stated:** "Run the tests; all 9 must pass." and "9 unit tests pass" in the done criterion.
- **Actual:** The plan's verbatim test source contains **10** test functions (`test_project_namespace_is_uuid_instance`, `test_project_namespace_is_pinned`, `test_entity_id_format_matches_dorico_pattern`, `test_entity_id_is_deterministic_across_calls`, `test_entity_id_differs_by_key`, `test_entity_id_differs_by_kind`, `test_entity_id_handles_all_kinds`, `test_entity_id_no_hyphens_in_hex`, `test_entity_id_hex_is_lowercase`, `test_entity_id_known_pinned_value`). All 10 pass.
- **Action:** None — the plan miscounted; the test code itself is correct and was reproduced verbatim. Total test count for the plan is 25 (10 uuid + 15 entities), not 24 as the verification section claims.

---

**Total deviations:** 1 auto-fix (Rule 1 cosmetic comment reword) + 1 plan-count correction (no code change).
**Impact on plan:** No scope changes. The auto-fix is a single-line comment edit to satisfy a literal grep acceptance criterion; semantics unchanged.

## Issues Encountered

None.

## Self-Check

Verified all created files and commits exist on disk:

- FOUND: `src/cents_generator/__init__.py`
- FOUND: `src/cents_generator/uuids.py`
- FOUND: `src/cents_generator/constants.py`
- FOUND: `src/cents_generator/entities.py`
- FOUND: `tests/__init__.py`
- FOUND: `tests/test_uuids.py`
- FOUND: `tests/test_entities.py`
- FOUND: `conftest.py`
- FOUND: `.gitignore`
- FOUND commit: `0f86cc3` (Task 1 RED)
- FOUND commit: `026223b` (Task 1 GREEN)
- FOUND commit: `9aab757` (Task 2)
- FOUND commit: `955d6ac` (Task 3 RED)
- FOUND commit: `ad0d3ba` (Task 3 GREEN)

`pytest tests/ -v` exits 0; 25 tests pass.

## Self-Check: PASSED

## Next Phase Readiness

- **Plan 01-02 (compose + emit) ready to start.** It can import from `cents_generator.constants` (FILE_VERSION, SMUFL_*, FONT_*, KIND_*, SECTION_ORDER), `cents_generator.uuids` (`entity_id`), and `cents_generator.entities` (all 9 dataclasses). The `<interfaces>` block of 01-01-PLAN.md is honored verbatim — no executor of 01-02 needs to inspect this code beyond the public surface.
- **Plan 01-03 (orchestrator + round-trip) ready.** The pinned namespace UUID makes the determinism check in Plan 03 reduce to running the generator twice and `diff`ing.
- **No blockers, no open architectural questions.**
- **Stub list:** None. All exports are real, fully implemented, and tested.

---
*Phase: 01-generator-skeleton-template-round-trip*
*Plan: 01*
*Completed: 2026-05-01*
