---
name: orchestrator
description: Run the factory-loop Orchestrator - dispatch ready BACKLOG.md issues to subagents in isolated git worktrees, review their PRs, send feedback, and merge. Use when asked to act as the Orchestrator or execute the backlog.
---

Read and follow `.factory/skills/orchestrator.md` (the source of truth). Use the `factory-session-hub` MCP tools for every session step:

- Startup/resume: `factory_session_list`, then `factory_session_get_status` for any in-flight session.
- Dispatch: `factory_session_dispatch`, then spawn a subagent inside the returned `worktreePath` and give it the `sessionId`, the issue block, and the instruction to use the `subagent-worker` skill.
- Monitor: `factory_session_list` shows `minutesSinceWorkerContact` and each worker's `lastProgress`. An `IN_PROGRESS` session with no contact for 15+ minutes is stalled; inspect its worktree before resuming it (see Step 3 of `.factory/skills/orchestrator.md`).
- Incidents (`openIncidents` in `factory_session_list`: permission/security blocks, credentials, API or billing limits, CI/CD or third-party failures): apply a safe automatic fix and `factory_resolve_incident`, or ask the user once with numbered options; then unblock the affected sessions. Never redispatch to "try again" (see **Incidents, Blockers & Follow-ups** in `.factory/skills/orchestrator.md`).
- Review: `factory_session_get_status` with `includeDiff: true`, then apply the `review-gate` skill.
- Changes needed: `factory_session_send_feedback` with `round` (1-3). Then resume that subagent and tell it to check its inbox. If your tool cannot resume subagents, spawn a fresh one in the same `worktreePath` with the same `sessionId`.
- After merge: `factory_session_teardown` with `removeWorktree: true`. Send `factory_session_send_feedback` without `round` to tell other in-flight sessions that share files to rebase.
