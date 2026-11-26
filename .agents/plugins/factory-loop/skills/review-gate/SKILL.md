---
name: review-gate
description: Review a factory-loop subagent's PR before merge against the backlog acceptance criteria, architecture, steering rules, and coding standards. Use when a session reports WAITING_FOR_REVIEW.
---

Apply the PR Review Gate in `.factory/skills/orchestrator.md` (Steps 4-5, the source of truth) to the diff from `factory_session_get_status` with `includeDiff: true`. Check:

1. **Acceptance criteria** in `.factory/BACKLOG.md`: is every checkbox genuinely satisfied?
2. **Architecture** in `.factory/ARCHITECTURE.md`: correct structure and patterns, and only the issue's `Target Files` (or the symbols it owns in shared files) changed.
3. **Steering** in `.factory/steering/workflow-rules.md`: no Hard Red Line violations, no leftover debug code, and tests cover the change.
4. **Coding standards** in `.factory/steering/coding-standards.md`.
5. **CI status** (`ciStatus`): `NOT_CONFIGURED` is acceptable only before the CI workflow issue is merged. `INFRA_BLOCKED` needs the user's decision (fix and re-run, or waive); it should have a matching incident. `FAILED_PREEXISTING` is acceptable once confirmed on the base branch, with a follow-up issue. `FAILED` is never approved.

Outcome:
- **Changes needed:** send concrete, line-specific feedback with `factory_session_send_feedback` and the next `round` (max 3; round 4 blocks the session for human escalation).
- **Approved:** merge, then `factory_session_teardown`.
