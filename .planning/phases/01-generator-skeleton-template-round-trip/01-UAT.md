---
status: complete
phase: 01-generator-skeleton-template-round-trip
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md]
started: 2026-05-01T17:00:00Z
updated: 2026-05-01T17:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: From the project root, `python3 build.py --out /tmp/cents-smoke.doricolib` exits 0 with no output and produces a 9057-byte file. No import or path errors.
result: pass
notes: exit=0, 9057 bytes confirmed. CLI prints `wrote <path>` confirmation line — intentional, not an error.

### 2. Full Test Suite Passes
expected: `pytest tests/ -v` runs to completion — 81 tests pass, 0 fail, 0 errors. (One test may skip with the message "TonalitySystemStartTemplate.doricolib not present" if the template file is missing locally.)
result: pass
notes: 81 passed in 0.15s, exit 0. No skips — template file present locally so round-trip tests ran for real.

### 3. Determinism Across Two Runs
expected: Running `python3 build.py --out /tmp/a.doricolib && python3 build.py --out /tmp/b.doricolib && diff /tmp/a.doricolib /tmp/b.doricolib` exits 0 with empty stdout. `md5 /tmp/a.doricolib /tmp/b.doricolib` shows identical hashes (`5f207c1de7f8ddf7f0af678384828cd4`).
result: pass
notes: diff exit 0 (empty), both MD5s = 5f207c1de7f8ddf7f0af678384828cd4 — matches the SUMMARY's pinned hash.

### 4. Round-trip vs Template
expected: With `TonalitySystemStartTemplate.doricolib` in the project root, `pytest tests/test_template_roundtrip.py -v` runs all 8 round-trip tests and they all pass — meaning generator output is byte-identical to the template modulo entityIDs.
result: pass
notes: all 8 test_template_roundtrip tests passed inside Test 2's pytest run (test_round_trip_byte_identical_modulo_entity_ids passed — template file present locally).

### 5. XML Well-formedness
expected: `xmllint --noout /tmp/cents-smoke.doricolib` exits 0 with no output (silent success).
result: pass
notes: xmllint_exit=0, no output.

### 6. Schema Essentials Visible
expected: `head -2 /tmp/cents-smoke.doricolib` shows `<?xml version="1.0" encoding="utf-8"?>` (double-quoted) on line 1 and `<kScoreLibrary>` on line 2. `grep '<fileVersion>1.1450</fileVersion>' /tmp/cents-smoke.doricolib` finds exactly one match.
result: pass
notes: line 1 = `<?xml version="1.0" encoding="utf-8"?>` (double-quoted, lowercase utf-8), line 2 = `<kScoreLibrary>`, fileVersion grep = 1 match.

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
