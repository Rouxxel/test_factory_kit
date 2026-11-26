---
name: subagent-worker
description: Work as a factory-loop subagent on one assigned issue inside its git worktree - implement, test, open a PR, reach green CI, and report back through the session hub. Use when given a sessionId and an issue by the Orchestrator.
---

Read and follow `.factory/skills/subagent-worker.md` (or `.factory/skills/bugfix-issue.md` for bugfix issues). Those files are the source of truth. Use the `factory-session-hub` MCP tools with the `sessionId` you were given:

1. At startup, call `factory_worker_check_inbox`. If you were started fresh for an existing session, also call `factory_session_get_status` to recover the issue, branch, previous reports, and feedback history.
2. Work only inside your worktree and on your branch. Call `factory_worker_progress` with a one-line note at startup and after each major step.
3. Do not wait for CI that doesn't exist: if the base branch has no CI configured, or no checks appear within 10 minutes of pushing, report with `ciStatus: NOT_CONFIGURED` / `NO_CHECKS` (see Step 3 of `.factory/skills/subagent-worker.md`). Classify every CI failure before acting: caused by your change (fix it), infrastructure/external such as billing limits or missing secrets (don't retry; `ciStatus: INFRA_BLOCKED`), or pre-existing outside your Target Files (don't fix; `ciStatus: FAILED_PREEXISTING`).
4. When local checks are green, CI is green (or not configured per step 3), and the PR is open, call `factory_worker_report` with `status: WAITING_FOR_REVIEW`, `prUrl`, `testResults`, `ciStatus`, `ciDetails` (whenever CI isn't green), and any `notesForLearnings`.
5. If you hit a retry cap (5 local / 3 CI) or need a decision, call `factory_worker_report` with `status: BLOCKED`, a `blockedReason`, and `blockerType` (`RETRY_CAP`, `INFRA`, or `NEEDS_DECISION`).
6. If something outside your code stops you (permission or security block, credentials, API key/rate/quota/billing limit, CI/CD or third-party failure, network), don't loop and never bypass a security control: apply at most one safe self-remedy, otherwise call `factory_report_incident` (`blocking: true` if you can't continue). See **Blockers Outside Your Control** in `.factory/skills/subagent-worker.md`.
7. Then stop and return your Worker Completion Report. Do not poll the inbox in a loop. When you are resumed, call `factory_worker_check_inbox` again and address every message.
