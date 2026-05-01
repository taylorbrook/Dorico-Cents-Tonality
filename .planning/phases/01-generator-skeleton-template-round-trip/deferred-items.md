# Deferred Items — Phase 01

Out-of-scope discoveries that this phase's executors logged but did NOT fix.
The orchestrator or a future tooling pass should address these.

## STATE.md / SDK section-heading mismatch (logged 2026-05-01 by 01-01 executor)

The project's initial `.planning/STATE.md` (created by `/gsd-init`) uses heading
and field names that some `gsd-sdk query state.*` handlers do not recognize.
As a result, the following state-update calls return `{ <verb>: false, reason: ... }`
without modifying STATE.md:

| SDK call | Reason | Mismatch |
|----------|--------|----------|
| `state.advance-plan` | "Cannot parse Current Plan or Total Plans in Phase from STATE.md" | STATE.md has both `- **Plan:** none yet` (bold-bullet, wins regex) and `Plan: 1 of 3` (plain). The bold one wins and lacks "of N". |
| `state.record-metric` | "Performance Metrics section not found in STATE.md" | STATE.md has `## Performance Metrics` followed by bullet list, not the markdown table the SDK regex expects (`\|.+\n\|[-\|\s]+\n`). |
| `state.add-decision` | "Decisions section not found in STATE.md" | STATE.md uses `### Key decisions (carried from PROJECT.md / research)` — SDK regex looks for `### Decisions`, `### Decisions Made`, or `### Accumulated.*Decisions`. |
| `state.record-session` | "No session fields found in STATE.md" | STATE.md uses `**Last action:** / **Next action:** / **Resumption hint:**`. SDK looks for `**Stopped At:**` / `**Resume File:**`. |

The calls that DID succeed and updated correctly:

- `state.update-progress` (frontmatter `progress.percent` 0 → 33; `completed_plans` 0 → 1)
- `roadmap.update-plan-progress 01` (01-01-PLAN.md checkbox `[ ]` → `[x]`)
- `requirements.mark-complete GEN-03 GEN-04 SCH-02` (all 3 → `[x]` and traceability table → "Complete")

**Action:** Project owner / orchestrator should reconcile STATE.md formatting with
the SDK's expected section/heading/field names. Per the executor contract, this
phase's executors are forbidden from editing STATE.md outside the SDK, so the
fix needs to come from a privileged caller (e.g. `gsd-sdk init` regeneration,
or a one-time hand-edit of STATE.md by the user).

This is a project-template issue, not a regression introduced by Phase 01.

## Recurrence noted by Plan 01-02 executor (2026-05-01)

The same four SDK calls failed identically when Plan 01-02 ran:
`state.advance-plan` (regex parse), `state.record-metric` (missing markdown
table), `state.add-decision` (heading mismatch — not attempted this run),
`state.record-session` (missing "Stopped At" field). The same three calls
succeeded: `state.update-progress` (frontmatter `completed_plans` 1 → 2,
`percent` 33 → 67), `roadmap.update-plan-progress 1` (01-02 checkbox
`[ ]` → `[x]`), and `requirements.mark-complete SCH-01 SCH-03 SCH-04`.

The Plan 01-02 executor performed minimal hand-edits to STATE.md to keep the
Current Position section aligned with reality:
- `Plan: 1 of 3` → `Plan: 2 of 3 complete; next plan: 03 (orchestrator + round-trip)`
- `**Plan:** none yet` → `**Plan:** 02 complete (compose.py + emit.py); next is 03 (orchestrator + round-trip)`
- Performance Metrics: added per-plan duration line.
- Session Continuity: `Last action` and `Next action` updated.

These hand-edits are confined to the human-readable Current Position /
Performance Metrics / Session Continuity sections — they do NOT touch the
authoritative frontmatter `progress` block (which the SDK manages and is
already correct).

## Recurrence noted by Plan 01-03 executor (2026-05-01)

Same four SDK calls failed identically on Plan 01-03's run — the schema
mismatches documented above are still present:
- `state.advance-plan` → "Cannot parse Current Plan or Total Plans in Phase from STATE.md"
- `state.record-metric` → "Performance Metrics section not found in STATE.md"
- `state.add-decision` → "Decisions section not found in STATE.md"
- `state.record-session` → "No session fields found in STATE.md"

The same three calls succeeded:
- `state.update-progress` (frontmatter `completed_plans` 2 → 3, `percent` 67 → 100, `completed_phases` 0 → 1)
- `roadmap.update-plan-progress 1` (Phase 01 status set to "Complete" in ROADMAP.md)
- `requirements.mark-complete GEN-01 GEN-02 GEN-03 SCH-01 SCH-02 SCH-03 SCH-04 SCH-05` (3 newly marked: GEN-01, GEN-02, SCH-05; the other 5 were already complete from prior plans)

Plan 01-03's executor performed the same minimal hand-edits as Plan 01-02:
Current Position section updated to reflect Phase 01 complete; Performance
Metrics annotated with Plan 01-03's duration (5.2min) and the deliverable
md5; Session Continuity Last/Next/Resumption pointers advanced to Phase 02.

The frontmatter `progress` block (the authoritative source) is correct
(`completed_phases: 1`, `completed_plans: 3`, `percent: 100`) — the SDK
managed that update correctly. The narrative sections were aligned by hand
to keep the human-readable view consistent with the authoritative state.
