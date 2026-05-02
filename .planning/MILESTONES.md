# Milestones

## v1.0 MVP (Shipped: 2026-05-02)

**Phases completed:** 4 phases, 11 plans
**Timeline:** 2026-05-01 → 2026-05-02 (2 days)
**Git range:** `6a054c4` → `dc51e25` (53 commits)
**Code:** 3,979 LOC Python (generator + 133-test suite)
**Deliverables:** `cents.doricolib` (1.26 MB, 1,411 entities, md5 `4cd707d2f4b10154a528b95e2ff5db9f`) + `README.md` (126 lines) + MIT `LICENSE`
**Requirements:** 30/30 v1 requirements complete (100%)

**Key accomplishments:**

- **Phase 1 — Generator Skeleton + Template Round-Trip**: Deterministic Python 3.11+ stdlib-only generator with byte-faithful XML emission that reproduces the working template's three entities (Natural / `-14` / `#-31`) byte-for-byte modulo entityIDs. Anchored on `uuid5(PROJECT_NAMESPACE, key)` discipline, frozen+slots dataclasses for all 9 entity types, three-class composite dispatcher (Class A glyph-only / B glyph+text / C text-only), and a 9,057-byte round-trip artifact byte-identical to `TonalitySystemStartTemplate.doricolib`.
- **Phase 2 — Range Expansion to ±99¢**: Production `cents.doricolib` shipped (1.26 MB, 1,411 entities) covering all 597 accidentals across `(natural, sharp, flat) × ±99¢` with overlapping enharmonic spellings. Centralized `pitch_delta_numerator(base, cents)` helper defeats the off-by-100 trap (Pitfall 1) — the only place pitch math lives. Test net: 31 new tests across structural invariants, byte-faithful snippet snapshots, and cents-mode determinism (133/133 total passing).
- **Phase 3 — Dorico Import + Playback Validation**: User physically validated end-to-end on Dorico Pro 6.2.2 macOS + HALion. 597-entry panel populates in usable interactive time; 12-row tuner spot-check matrix passes at ±1¢ (3 zero-deviation + 2 off-by-100 trap rows + 6 boundary values + 1 enharmonic-equivalent pair); sparse passages render clean, dense chord stacks documented with Engrave-mode workaround.
- **Phase 4 — README + Packaging**: Shipped `README.md` (126 lines, 26 acceptance gates) leading with the Dorico Pro 6.0+ requirement and a Shift+K → "open" key-signature walkthrough that defeats the #1 silent-failure mode. MIT `LICENSE` at repo root (1,069 bytes, byte-identical to canonical MIT modulo copyright). Install path verified end-to-end on the user's actual macOS Dorico Pro 6.x install.

---
