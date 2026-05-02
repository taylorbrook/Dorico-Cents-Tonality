# Phase 04 — DIST-03 Manual Install Verification

**Date:** 2026-05-02
**Dorico build:** Dorico Pro 6.2.2 macOS (per Phase 03 03-01-SUMMARY; user did not record a different build)
**Result:** PASS — user approved end-to-end install + first-note flow on their actual macOS Dorico Pro 6.x install.

## Test Path A — Library Manager (primary path)

| Step | README says | Observed | OK? |
|------|-------------|----------|-----|
| 1 | Shift+K → type `open` → Enter | matched | yes |
| 2 | Setup mode → Players → Tonality System → `cents` | matched | yes |
| 3 | Accidentals panel populates with 597 entries | matched | yes |
| 4 | Search `+14` → 3 matches | matched | yes |
| 5 | Apply `Sharp +14` — glyph + `+14` label appears | matched | yes |
| 6 | Tuner reads ~14¢ sharp (HALion or NotePerformer) | matched | yes |

User resume signal: `approved` (with self-noted intent to make manual README copy edits later — not a wording bug, not a Dorico-version difference, not a library bug; tracked as a future-cosmetic item, no patch applied here).

## Test Path B — DefaultLibraryAdditions (power-user path)

Not tested in this verification round; covered by README warning + Phase 3 03-01-SUMMARY (Library Manager path used to avoid Pitfall 4 risk). Path B remains documented in README §5 with the `remove if Dorico fails to launch` recovery instruction; user accepted that surface as-is.

## DIST-03 Closure

User-confirmed end-to-end install + first-note flow on their actual macOS Dorico Pro 6.x install. README is accurate as written. No patches applied by the executor in this verification round. Any future manual README edits the user makes are out of scope for DIST-03 closure (the user owns the README copy from this point forward; the v1 ship gate is closed).

## Regression sanity check

Plan 04-01's full acceptance chain (literal strings + section-ordering awk checks + line-count gate) re-run after verification — all gates still pass (no required strings stripped, no ordering invariants broken). README still prints `README ACCEPTANCE PASSED`.
