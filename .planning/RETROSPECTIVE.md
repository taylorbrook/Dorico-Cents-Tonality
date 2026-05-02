# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-05-02
**Phases:** 4 | **Plans:** 11 | **Timeline:** 2 days (2026-05-01 → 2026-05-02) | **Commits:** 53

### What Was Built

- `cents.doricolib` (1.26 MB, 1,411 entities) covering all 597 accidentals across `(natural, sharp, flat) × ±99¢` with overlapping enharmonic spellings — every cent accurate to ±1¢, validated against HALion + tuner.
- Deterministic Python 3.11+ stdlib-only generator (`build.py` + `src/cents_generator/`) with `uuid5(PROJECT_NAMESPACE, key)` discipline; cross-PYTHONHASHSEED byte-identical output verified end-to-end.
- 133-test suite covering byte-faithful round-trip against `TonalitySystemStartTemplate.doricolib`, structural invariants, UUID pins + byte-faithful snippet snapshots, two-run determinism, and pitch-math hand-calculations.
- `README.md` (126 lines) leading with Dorico Pro 6.0+ requirement and Shift+K → "open" key-signature walkthrough; MIT `LICENSE`.

### What Worked

- **Three-class composite dispatcher (Class A glyph-only / B glyph+text / C text-only) discovered in Phase 1.** Mapping the template's three composite patterns (Natural / `#-31` / `-14`) to one code path per class meant Phase 2's 597-entity sweep reused the dispatcher unchanged. Classification was the right abstraction at the right time — discovered while solving Phase 1 byte-faithful round-trip, not invented up front.
- **Centralized `pitch_delta_numerator(base, cents)` helper as Phase 2 Plan 01.** Pulling the off-by-100 trap (Pitfall 1) out as a single 12-test pure function before any orchestrator code went near it meant the math trap was impossible to introduce in user code. Phase 3's tuner matrix confirmed it cleanly.
- **Byte-faithful round-trip test against the user's working template (Phase 1 Plan 03) as the determinism anchor.** Diff-based validation against a known-good Dorico-written file caught every formatting quirk (tab indent, lowercase booleans, raw `n/1200` rationals, capital-X hex, six-decimal floats, comma-space CSV, self-closing empty arrays) without needing an XSD that doesn't exist.
- **Two-plan split in Phase 3 (cheap UX-01 + UX-02 first, time-intensive PLAY/UX-03 second).** Validated panel population + search ergonomics before committing to the 12-row HALion tuner matrix; if panel had broken at scale, the tuner work would have been wasted.
- **README open-key-signature step front-loaded (Phase 4 Plan 01).** The #1 silent-failure mode for any custom tonality system; user verified all 6 walkthrough steps matched observed UI on first try in Plan 04-03.

### What Was Inefficient

- **REQUIREMENTS.md ledger lag through Phase 3 → Phase 4.** Phase 3 SUMMARYs validated PLAY-02/PLAY-03/UX-01/UX-02/UX-03 but the checkboxes weren't flipped, leaving the v1 ledger reading 25/30 until milestone close did a manual flip. Future phases should flip the requirement checkboxes inside the verifier loop, not at milestone close.
- **Some plan SUMMARYs (02-01, 02-02, 02-03, 03-01, 03-02, 04-01, 04-03) wrote the one-liner in a non-canonical format that `gsd-sdk query summary-extract` couldn't parse cleanly.** The milestone.complete handler emitted "One-liner:" / "Phase:" placeholder strings into MILESTONES.md, requiring manual rewrite. Future SUMMARYs should put the one-liner as the first quoted string after a `## One-liner` heading or as a plain top-level field.
- **Worktree isolation unavailable on this checkout, so Phase 4 Wave 1 (Plan 04-01 README + Plan 04-02 LICENSE) ran sequentially despite being parallel-safe (no shared files).** Cost ~2 minutes of unnecessary serialization. Worth checking before phase plan whether the executor can actually parallelize what the plan declares parallel.

### Patterns Established

- **"Discover the dispatcher in Phase 1, scale in Phase 2."** First phase exercises every code path against a tiny known-good fixture (3 entities); second phase scales the same dispatcher across the production range. Pattern transferred from this project; reusable for any "build a generator over a known schema" project.
- **"Centralized math helper as its own first plan."** Any time a phase contains a single math operation that's high-risk (off-by-100 here), pull it into its own plan with hand-calculated unit tests before any orchestrator code uses it. The 12-row hand-calculation table in Plan 02-01 paid for itself in Phase 3 tuner validation.
- **"Two-plan split for manual validation phases."** Cheap structural checks (panel populates, search returns matches) in the first plan; expensive perceptual checks (tuner matrix, visual collision audit) in the second. Frontloads cheap go/no-go decisions.
- **"Plan IS the protocol" for non-autonomous validation phases (CONTEXT.md D-01 in Phase 3).** When the plan body is the user's step-by-step protocol, no separate walkthrough document is needed. Reduces context fragmentation.

### Key Lessons

1. **The off-by-100 trap (sharp/flat-base accidentals carrying ±100¢ before the cent offset is applied) is the highest-risk math error in any cent-deviation system.** Defending it as a single named helper with hand-calculated unit tests is non-negotiable. Future microtonal projects should adopt the same pattern.
2. **Byte-faithful round-trip against a known-good file is a stronger validation contract than schema validation when no schema exists.** The Dorico format has no XSD; diff-based round-trip testing against a Dorico-written template caught every formatting quirk that schema validation could have caught and several that no schema would specify (e.g., capital-X hex literals, comma-space CSV).
3. **Open-key-signature gating is the #1 silent-failure mode for custom tonality systems.** The README must lead with it; the first-note walkthrough must include the Shift+K → "open" step explicitly. User verification confirmed this on first try; without it, the cents tonality would have been invisible in the panel.
4. **Determinism via `uuid5(NAMESPACE, key)` + cross-PYTHONHASHSEED testing is the only safe path for re-importable user libraries.** Random UUIDs would have produced 1,411 duplicate entries in Dorico on every re-import. Pinning `PROJECT_NAMESPACE` once with a never-rotate comment is the right discipline.
5. **Manual playback validation against a tuner is the right ROI for an XML deliverable that no headless tool can validate.** Cheaper than building automated regression and catches both math errors and Dorico-acceptance issues. Don't over-engineer headless validation when the deliverable is a user-imported library file.

### Cost Observations

- **Sessions:** Tracked across `/gsd-execute-phase` calls (4 phases × ~1 session each + 1 milestone-close session ≈ 5 sessions).
- **Plan execution times** (from STATE.md Performance Metrics):
  - Phase 1: ~16 min total (3 plans, 5.6 + 5.5 + 5.2 min)
  - Phase 2: ~17 min total (3 plans, 1.7 + 8 + 7 min)
  - Phase 3: manual user-physical validation (HALion + tuner; not timed by harness)
  - Phase 4: 1m 29s + 37s + manual user verification
- **Notable:** Phase 4 Plan 02 (LICENSE) finished in 37s because the deliverable was a single canonical text file; Plan 04-03 (manual install verification) took the longest non-execution wall-clock time because it required the user to physically run Dorico and a tuner. Manual-validation phases dominate ship-readiness wall-clock, not code-execution wall-clock.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~5 | 4 | Established three-class dispatcher pattern + centralized-math-helper-as-first-plan + byte-faithful round-trip discipline |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 133 | 30/30 v1 reqs (100%) | 0 (stdlib only) |

### Top Lessons (Verified Across Milestones)

1. (Pending v1.1+ to verify) — Off-by-100 trap defense via centralized helper + hand-calculated unit tests.
2. (Pending v1.1+ to verify) — Byte-faithful round-trip against known-good fixture beats absent-schema validation.
