---
phase: 01-generator-skeleton-template-round-trip
plan: 03
subsystem: generator-orchestration

tags: [python, stdlib, argparse, cli, byte-faithful-roundtrip, determinism, uuid-snapshot, dorico]

# Dependency graph
requires:
  - "Plan 01-01: PROJECT_NAMESPACE, entity_id(), constants (FILE_VERSION, KIND_*, TEMPERAMENT_12EDO_DIVISIONS, SECTION_ORDER), 9 frozen+slots dataclasses"
  - "Plan 01-02: compose.build_class_a/b/c + AccidentalBundle, emit.write() byte-faithful XML emitter"
provides:
  - "build.py CLI shim — 'python build.py --out cents.doricolib' is the single user-facing command"
  - "src/cents_generator/main.py — orchestrator (build_template_three) + run() + main() argparse wrapper"
  - "Phase 1 deliverable: a generator that emits a 9057-byte .doricolib byte-identical to TonalitySystemStartTemplate.doricolib (modulo entityIDs)"
  - "Pinned UUID snapshot covering all 13 distinct entityIDs (3 singletons + 3 accidentals + 3 composites + 2 glyphs + 2 texts)"
  - "Round-trip + determinism test infrastructure ready for Phase 2 to extend (the test files use the same 'normalize entityIDs and diff' pattern Phase 2 will scale to 1411 entities)"
affects: [02-range-expansion, 03-validation, 04-readme-and-packaging]

# Tech tracking
tech-stack:
  added:
    - "argparse (stdlib) — CLI flag parsing for build.py"
    - "Two-layer byte-fidelity post-process in emit.py — ' />' -> '/>' (Plan 02) plus single-quote -> double-quote in XML decl (Plan 03)"
  patterns:
    - "CLI shim at project root + main.py orchestrator pattern: build.py is a 20-line entrypoint that adjusts sys.path and delegates to cents_generator.main.main"
    - "Hand-ordered tuples for section-internal entity emission — matches the template's quirky orderings byte-for-byte (Phase 2 will adopt a systematic ordering)"
    - "EntityID normalization for round-trip diff — replace '<kind>.user.<32hex>' with '<kind>.user.<auto-N>' per-kind sequence; identical structure produces identical normalized strings"
    - "UUID snapshot test as third-layer determinism defense — pins actual hex values so PROJECT_NAMESPACE rotation or key-string drift cannot ship silently"
    - "Conditional skip on missing local artifact — TonalitySystemStartTemplate.doricolib is a user-only file; round-trip test calls pytest.skip() when absent rather than failing CI"

key-files:
  created:
    - "src/cents_generator/main.py — orchestrator (build_template_three, run, main/argparse)"
    - "build.py — project-root CLI shim"
    - "tests/test_template_roundtrip.py — 8 round-trip tests vs TonalitySystemStartTemplate.doricolib"
    - "tests/test_determinism.py — 3 byte-identical-across-runs tests (in-process + subprocess + diff-recipe)"
    - "tests/test_uuid_snapshot.py — 7 entityID-hex pinning tests (3 singletons + accidentals + composites + glyphs + texts + entity_id direct + emitted-XML containment)"
  modified:
    - "src/cents_generator/emit.py — added XML-declaration single-quote -> double-quote post-process (Rule 1 deviation, Pitfall 7)"
    - "conftest.py — tightened to plan's idempotent shim (added docstring + idempotence guard; no behavior change)"
    - ".gitignore — added TonalitySystemStartTemplate.doricolib so the local round-trip target stays out of the repo"

key-decisions:
  - "Skip the round-trip test cleanly when TonalitySystemStartTemplate.doricolib is absent (pytest.skip), rather than fail. The template is the user's local artifact (kept out of git per CLAUDE.md); CI on a fresh clone or another developer's machine should still pass the rest of the suite."
  - "Add a UUID snapshot test (tests/test_uuid_snapshot.py) beyond the plan's spec. Project context flagged this as essential — pinning the actual hex values for the 13 distinct entityIDs is the only way to catch silent PROJECT_NAMESPACE rotation or key-string drift across commits."
  - "Apply XML-declaration quote-style fix in emit.py (single-quote -> double-quote) — same byte-fidelity-post-process pattern as Plan 02's ' />' -> '/>' fix. The fix is bounded to the first line because element attributes inside the body always use double quotes in ET output."
  - "xmllint test gracefully falls back to xml.etree.ElementTree.parse() when xmllint is unavailable on the runner. Plan called for skip-only; the fallback gives a stronger guarantee on the well-formedness criterion (criterion 3) on machines without libxml2."
  - "Test commit is a 'test()' commit (not RED-then-GREEN). Per the plan's task ordering, Task 1 (orchestrator + CLI) shipped before Task 2's tests, so the strict TDD gate doesn't hit a RED state. Tests pass on first run against the existing implementation. This is acceptable here because the implementation surface is fully exercised by 63 prior unit tests across Plans 01-01 and 01-02; the new tests are integration-level invariants."

patterns-established:
  - "Phase 2 round-trip-at-scale pattern: same _normalize_entity_ids regex + per-kind sequencing approach should scale to 1411 entities. Phase 2 will need to capture entity-counts up front (1 / 1 / 597 / 1 / 198 / 3 / 597) for the analogous test."
  - "Three-layer determinism defense (Plan 01-01 unit tests for entity_id; Plan 01-03 two-run byte-equality; Plan 01-03 hex snapshot) is the template Phase 2's range expansion will inherit and extend."
  - "When test files reference user-local artifacts (here: the template), use a _require_template() helper that calls pytest.skip() with a clear message — keeps tests portable across environments without weakening the assertions where the artifact is present."

requirements-completed: [GEN-01, GEN-02, GEN-03, SCH-01, SCH-02, SCH-03, SCH-04, SCH-05]

# Metrics
duration: 5.2min
completed: 2026-05-01
---

# Phase 01 Plan 03: Orchestrator + Template Round-Trip Summary

**Single CLI command (`python build.py --out <path>`) wires Plans 01-01 and 01-02 into a deterministic generator that emits a 9057-byte `.doricolib` byte-identical to `TonalitySystemStartTemplate.doricolib` modulo entityIDs, proven by 18 new tests across round-trip / determinism / UUID-snapshot suites.**

## Performance

- **Duration:** 5.2 min (315 s)
- **Started:** 2026-05-01T23:31:36Z
- **Completed:** 2026-05-01T23:36:51Z
- **Tasks:** 2 of 2 complete
- **Files created:** 5
- **Files modified:** 3

## Accomplishments

- **CLI entrypoint shipped.** `python build.py --out cents.doricolib` builds the three-template-entity `.doricolib` in roughly 20 ms on this machine. argparse handles the `--out` flag with a sensible default (`cents.doricolib` in cwd). The shim at the repo root delegates to `src/cents_generator/main.py:main()`; the orchestrator imports all five sibling modules (`compose`, `emit`, `uuids`, `entities`, `constants`) for the full pipeline.
- **Byte-faithful round-trip proven.** `test_round_trip_byte_identical_modulo_entity_ids` passes — generator output, with entityIDs replaced by `<kind>.user.<auto-N>` per-kind sequence tokens, is byte-identical to the template after the same normalization. This validates all Plan 02 formatting quirks at the integration level (tab indent, lowercase utf-8 declaration, raw `n/d` rationals, `(0, 0)` tuples, comma-space ID joins, uppercase hex codepoints, `100.000000` six-decimal scale, self-closing empty arrays, `customKeySignatures` boilerplate).
- **Determinism verified at three layers.** (1) In-process `run()` twice → identical bytes. (2) Subprocess `python build.py` twice → identical bytes (catches `PYTHONHASHSEED` randomization). (3) Snapshot test pins all 13 entityID hex strings — silently rotating `PROJECT_NAMESPACE` would now produce 13 simultaneous test failures.
- **XML well-formedness proven.** `xmllint --noout` cleanly accepts the output. The test gracefully falls back to `xml.etree.ElementTree.parse()` if xmllint is unavailable on the runner, so the criterion-3 guarantee holds on any Python 3.11+ machine.
- **fileVersion locked.** `<fileVersion>1.1450</fileVersion>` is asserted directly in `test_round_trip_file_version_is_1_1450` — Pitfall 4 (launch-crash on wrong version) cannot regress without that test failing.
- **81 tests pass** (63 prior + 18 new) in 0.14 s. Stdlib-only verified by grep: 0 occurrences of `lxml|jinja2|xmltodict|requests|httpx|aiohttp|numpy|pandas|pydantic|attrs|click|typer` across `src/cents_generator/`, `build.py`, and `conftest.py`.

## Output Artifact

The generated `.doricolib` is **9057 bytes**. MD5 across two consecutive `python build.py` runs:

```
$ python3 build.py --out /tmp/cents-a.doricolib && python3 build.py --out /tmp/cents-b.doricolib
$ md5 /tmp/cents-a.doricolib /tmp/cents-b.doricolib
MD5 (/tmp/cents-a.doricolib) = 5f207c1de7f8ddf7f0af678384828cd4
MD5 (/tmp/cents-b.doricolib) = 5f207c1de7f8ddf7f0af678384828cd4
$ diff /tmp/cents-a.doricolib /tmp/cents-b.doricolib
$ xmllint --noout /tmp/cents-a.doricolib
$
```

(Identical hashes; diff empty; xmllint silent.)

## Phase 1 Success Criteria — Proof Map

| # | Criterion | Test that proves it |
|---|-----------|---------------------|
| 1 | Byte-identical determinism (two consecutive runs hash identically) | `tests/test_determinism.py::test_two_runs_in_process_are_byte_identical`, `::test_two_subprocess_runs_via_cli_are_byte_identical`, `::test_diff_command_returns_empty` |
| 2 | Template round-trip (output equals template modulo entityIDs) | `tests/test_template_roundtrip.py::test_round_trip_byte_identical_modulo_entity_ids` (plus 7 supporting structural tests in the same file) |
| 3 | UUID snapshot (entityIDs pinned against silent regression) | `tests/test_uuid_snapshot.py` — 7 tests pinning 13 entityIDs across singletons, accidentals, composites, glyphs, and texts; plus a direct `entity_id()` belt-and-braces check |
| 4 | XML well-formedness + `<fileVersion>1.1450</fileVersion>` present | `tests/test_template_roundtrip.py::test_round_trip_xmllint_well_formed` (with `ET.parse()` fallback), `::test_round_trip_file_version_is_1_1450` |

## Task Commits

1. **Task 1: orchestrator + CLI entrypoint (with embedded Rule 1 fix)** — `20d95d3` (feat)
2. **Task 2: round-trip + determinism + UUID snapshot tests** — `7838124` (test)

_Plan metadata commit (this SUMMARY + STATE/ROADMAP updates) follows separately._

## Files Created/Modified

### Created
- `src/cents_generator/main.py` — orchestrator. Public surface: `build_template_three()` returns the seven-tuple of singletons + section-ordered tuples; `run(out_path)` is the import-friendly entrypoint; `main(argv)` is the argparse CLI.
- `build.py` — project-root CLI shim. Adds `./src` to `sys.path`, imports `cents_generator.main.main`, exits with its return code.
- `tests/test_template_roundtrip.py` — 8 tests against `TonalitySystemStartTemplate.doricolib`: byte-identical-modulo-entityIDs, section ordering, xmllint well-formedness (with ET fallback), entity counts, accidental names, pitch deltas, fileVersion. Skips cleanly on missing template.
- `tests/test_determinism.py` — 3 tests: in-process two-run, subprocess CLI two-run, `diff a b` returns empty.
- `tests/test_uuid_snapshot.py` — 7 tests pinning every entityID hex string; includes a direct `entity_id()` re-derivation and an end-to-end "every snapshot ID appears in emitted XML" check.

### Modified
- `src/cents_generator/emit.py` — added bounded XML-declaration single-quote → double-quote post-process. Same pattern as Plan 02's existing ` />` → `/>` fix; safe because ET only emits single-quote attribute syntax in the XML declaration line.
- `conftest.py` — added module docstring and idempotence guard (`if str(SRC) not in sys.path`). Behavior unchanged.
- `.gitignore` — added `TonalitySystemStartTemplate.doricolib` so the user's local round-trip target cannot accidentally be committed by future `git add` invocations.

## Decisions Made

- **Wired the test directly to `cents_generator.main.run()` rather than to `emit.write()` directly.** This exercises the full orchestrator-to-emit pipeline so any drift in `build_template_three()` (orderings, hand-picked names, key strings, pitch-delta literals) shows up in the test, not just emit-level format quirks.
- **Used absolute paths in subprocess test (`sys.executable`, repo-root resolved from `__file__`).** Survives the executor's working-directory reset between bash calls.
- **Snapshot file is a freestanding test file (`tests/test_uuid_snapshot.py`) rather than embedded in `test_template_roundtrip.py`.** The two concerns (round-trip to template vs. pin entity IDs) are orthogonal — the snapshot must hold even if the template file is missing on the runner. Keeping them separate also means a snapshot regression doesn't mask a round-trip regression and vice versa.
- **Did not add `--namespace-key` or `--verbose` CLI flags.** Project context mentioned these as future overrides; the plan only requires `--out`. Kept the surface minimal for Phase 1 — Phase 2 can add flags as the orchestrator grows.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] XML declaration quote style drift (Pitfall 7 — formatting drift)**

- **Found during:** Task 1, post-implementation byte-diff probe vs. template
- **Issue:** Python 3.14 `ElementTree.tostring(xml_declaration=True)` emits the XML declaration with **single quotes** (`<?xml version='1.0' encoding='utf-8'?>`), but the Dorico template uses **double quotes** (`<?xml version="1.0" encoding="utf-8"?>`). Both are XML-equivalent, but Plan 03's round-trip diff requires byte equality, and the existing entity-ID normalization regex (`<kind>.user.<32hex>` → `<auto-N>`) does not normalize attribute quote style. Without the fix, every round-trip test would have failed at line 1 of the diff.
- **Fix:** Added a bounded byte-replacement step in `emit.py` after the existing ` />` → `/>` post-process. Operates only on the first line (extracted at the first `\n`), replaces `version='1.0'` with `version="1.0"` and `encoding='utf-8'` with `encoding="utf-8"`. Element-attribute syntax inside the document body uses double quotes in ET output, so the replacement cannot touch anything else.
- **Files modified:** `src/cents_generator/emit.py` (one block added inside `write()`).
- **Verification:** `head -1 cents.doricolib` shows the double-quote form; all 81 tests pass; `xmllint --noout` accepts the output; round-trip diff against the template is empty after entityID normalization.
- **Committed in:** `20d95d3` (rolled into Task 1 commit).

### TDD Gate Compliance Note

- **Plan stated:** Task 2 is `tdd="true"`, expecting a RED commit (failing test) before a GREEN commit (passing implementation).
- **Actual:** Plan ordering placed Task 1 (orchestrator + CLI) before Task 2 (tests). By the time Task 2 ran, the implementation surface was fully in place from Task 1 plus Plans 01-01 and 01-02 (63 prior tests already passed). The new tests in Task 2 verify integration-level invariants (round-trip byte equality, determinism across processes, UUID snapshot pinning) — they pass on first run rather than failing first.
- **Action:** Committed Task 2 as a single `test()` commit rather than the standard RED + GREEN pair. Documented here for SUMMARY traceability. The strict TDD gate cannot be honored when integration tests run after the integration is already complete; the spirit (tests precede shipping) is honored at the per-module level via Plans 01-01's and 01-02's RED-then-GREEN commits.

### Snapshot test added beyond plan spec

- **Plan stated:** Task 2 produces `tests/test_template_roundtrip.py` and `tests/test_determinism.py` only.
- **Actual:** Added a third file, `tests/test_uuid_snapshot.py`, with 7 tests pinning all 13 distinct entityID hex strings.
- **Why:** Project context explicitly listed "UUID snapshot — at least one test pins the entityID hex strings produced by `entity_id(kind, key)` so that future Pitfall 2 regressions are caught immediately" as a phase success criterion. Without it, an accidental rotation of `PROJECT_NAMESPACE` or drift in the orchestrator's key strings would produce different (but still deterministic) UUIDs that pass the round-trip test (since normalization erases the actual hex) but break update-in-place re-imports for every existing user. This is exactly Pitfall 2.
- **Action:** No change needed — this is a Rule 2 (auto-add missing critical functionality) deviation, justified by the project_context's explicit success criterion 3.

---

**Total deviations:** 1 auto-fix (Rule 1 byte-fidelity post-process, mirrors Plan 02's existing fix), 1 TDD-gate ordering note, 1 plan-spec extension (Rule 2 snapshot test).

**Impact on plan:** No scope creep. The auto-fix is a bounded byte-replacement defeating Pitfall 7 in the only place it could leak (ET's XML-declaration quote style). The snapshot test is required by the explicit project-context success criterion. The TDD ordering note is documentation only.

## Three-Template-Entity Round-Trip — Final Confirmation

| Template entity | Class | Plan 02 data-shape match | Plan 03 byte-faithful round-trip |
|-----------------|-------|--------------------------|----------------------------------|
| Natural (template lines 62-73, 157-179, 127-139) | A | `test_class_a_natural_template_shape` (Plan 02) | `test_round_trip_byte_identical_modulo_entity_ids` (this plan) |
| -14 (template lines 50-61, 228-250, 107-114)    | C | `test_class_c_template_shape` (Plan 02)         | `test_round_trip_byte_identical_modulo_entity_ids` (this plan) |
| #-31 (template lines 38-49, 180-227, 140-152)   | B | `test_class_b_template_shape` (Plan 02)         | `test_round_trip_byte_identical_modulo_entity_ids` (this plan) |

Plan 02 proved each composite class's data shape in isolation. Plan 03 proves the full pipeline (orchestrator → compose → emit → on-disk bytes) reproduces the template byte-for-byte modulo entityIDs.

## Issues Encountered

- **Python 3.14 ElementTree XML-declaration quote style.** Discovered during Task 1's byte-diff probe (run before commit). Resolved with the same bounded-byte-replacement pattern Plan 02 used for ` />` → `/>`. Documented as Rule 1 deviation above. The fix sits in `emit.py` because Pitfall 7 (formatting drift) is its concern.
- **STATE.md / SDK schema mismatch (carried from prior plans).** The same four `gsd-sdk query state.*` handlers documented in `deferred-items.md` from Plans 01-01 and 01-02 still don't match this project's STATE.md schema. Plan 03 follows the same best-effort policy: try the SDK, log to deferred-items if calls fail, do **not** hand-edit STATE.md outside the SDK's authoritative frontmatter `progress` block. The Current Position narrative section may need a manual update for "Plan 03 complete" — that's tracked in deferred-items.

## Self-Check

Verified all created files and commits exist on disk:

- FOUND: `src/cents_generator/main.py`
- FOUND: `build.py`
- FOUND: `tests/test_template_roundtrip.py`
- FOUND: `tests/test_determinism.py`
- FOUND: `tests/test_uuid_snapshot.py`
- FOUND modified: `src/cents_generator/emit.py`
- FOUND modified: `conftest.py`
- FOUND modified: `.gitignore`
- FOUND commit: `20d95d3` (Task 1)
- FOUND commit: `7838124` (Task 2)

`pytest tests/ -v` exits 0; 81 tests pass (25 from Plan 01-01 + 38 from Plan 01-02 + 18 from this plan).

`python3 build.py --out /tmp/cents-a.doricolib && python3 build.py --out /tmp/cents-b.doricolib && diff /tmp/cents-a.doricolib /tmp/cents-b.doricolib` exits 0 with empty stdout.

`xmllint --noout /tmp/cents-a.doricolib` exits 0 with no output.

## Self-Check: PASSED

## Next Phase Readiness

- **Phase 1 closed.** All four phase success criteria are proven by passing tests. The generator is a single-file CLI deliverable, deterministic to the byte, structurally equivalent to the template.
- **Phase 2 (range expansion to ±99¢) ready to start.** The orchestrator's `build_template_three()` will be replaced by a parameter sweep `for base in (natural, sharp, flat): for cents in range(-99, 100):`. The compose-class dispatcher already handles all three classes generically; the centralized `pitch_delta_numerator(base, cents)` helper that defeats Pitfall 1 (off-by-100 in pitchDeltaFromNatural) is the new piece Phase 2 introduces.
- **What's locked for Phase 2:**
  - `PROJECT_NAMESPACE` (never rotate — locked by Plan 01-01 + this plan's snapshot test)
  - `entity_id()` algorithm (uuid5 of `f"{kind}:{key}"`)
  - Phase 1's three template-specific keys (`natural-template`, `natural-14-template`, `sharp-31-template`, `12-edo-template`, `psychography-template`) — they are template-specific and use the `-template` suffix to avoid colliding with Phase 2's clean `sharp+14` / `flat-50` / `natural-7` key conventions. Phase 1's three template entities will continue to ship verbatim into the Phase 2 build (since the user's existing imports reference these specific entityIDs).
  - All emit.py formatting quirks (tab indent, lowercase utf-8 declaration, raw `n/d` rationals, comma-space ID joins, uppercase hex codepoints, six-decimal scale literals, self-closing empty arrays, double-quote XML declaration, no-space self-closing element form).
- **What Phase 2 must add:**
  - `pitch_delta_numerator(base: Literal["natural","sharp","flat"], cents: int) -> int` returning `{"natural": 0, "sharp": 100, "flat": -100}[base] + cents` — defeats Pitfall 1.
  - Parameter sweep: 3 bases × 199 cents (-99..+99 inclusive) = 597 accidentals, 597 composites; plus 198 distinct text labels (-99..-1 and +1..+99 — zero is implicit), 3 glyphs (one per base), 3 zero-deviation accidentals (Sharp / Flat / Natural at 0¢).
  - Section-internal ordering policy (sorted by pitch delta — Phase 1's hand-picked template orderings will not scale).
  - Natural accidental presence in AccidentalSystem (Pitfall 8).
- **No blockers, no open architectural questions.**
- **Stub list:** None. All exports are real, fully implemented, and tested.
- **Threat flags:** None. No new security-relevant surface beyond the `--out` path argument (Trust Boundary T-01-03-01, accepted in plan threat model: single-developer build tool).

## TDD Gate Compliance

This plan's two tasks are mixed-mode:

- **Task 1:** `type="auto"` (no TDD requirement). Single feat commit `20d95d3`. ✓
- **Task 2:** `tdd="true"`. Single test commit `7838124` rather than the standard RED + GREEN pair. The implementation surface was already in place from Task 1 plus Plans 01-01 and 01-02 (63 prior tests passed against it), so the integration-level tests pass on first run rather than failing first. The strict gate cannot be honored when tests run after the integration is already complete; documented as a deviation. ⚠️ (gate documented as deviation, see "TDD Gate Compliance Note" above)

Plan-level `type: tdd` does not apply (this plan is `type: execute`).

---
*Phase: 01-generator-skeleton-template-round-trip*
*Plan: 03*
*Completed: 2026-05-01*
