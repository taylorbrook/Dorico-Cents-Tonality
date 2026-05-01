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
