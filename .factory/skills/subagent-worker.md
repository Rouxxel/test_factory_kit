# Skill: Subagent Issue Worker (Build -> Test -> Green CI -> PR)

## Objective
Implement **one assigned issue** inside your isolated branch/worktree, verify all local checks and CI checks pass, open a Pull Request, and report back to the Orchestrator.

## Session Tools
If the Orchestrator gave you a `sessionId` and the `factory-session-hub` MCP server is available:
- Call `factory_worker_check_inbox` at startup and whenever you are resumed. If you were started fresh for an existing session, also call `factory_session_get_status` to recover the issue, branch, previous reports, and feedback history.
- Call `factory_worker_progress` with a one-line note at startup and after each major step (implemented, local checks passing, PR opened, waiting for CI, CI result). The Orchestrator uses these notes to tell a working session from a stuck one.
- Submit your Worker Completion Report with `factory_worker_report` (`status: WAITING_FOR_REVIEW`), or `status: BLOCKED` with a `blockedReason` (and `blockerType`) when you hit a retry cap, an infrastructure blocker, or need a decision.
- Always set `ciStatus` (`GREEN`, `NOT_CONFIGURED`, `NO_CHECKS`, `INFRA_BLOCKED`, `FAILED_PREEXISTING`, or `FAILED`) and put the exact CI message in `ciDetails` whenever it isn't `GREEN`.
- If something outside your code stops you, record it with `factory_report_incident` (see **Blockers Outside Your Control** below).
- Do not poll the inbox in a loop while waiting.

This applies equally to `bugfix-issue.md`.

## Context Loading
Before writing code, read ONLY:
1. Your assigned Issue block from `.factory/BACKLOG.md`
2. `.factory/steering/workflow-rules.md`
3. `.factory/steering/coding-standards.md`
4. `.factory/ARCHITECTURE.md` (relevant sections only)
5. `.factory/TECH_STACK.md`
6. `.factory/MCPS.md`

## Execution Loop

### Step 1: Isolate & Implement
- Ensure you are on a dedicated feature branch (`feat/<issue-id>-<short-slug>` or `fix/<issue-id>-<short-slug>`).
- Implement ONLY what is specified in your Issue's `Context & Requirements` and `Acceptance Criteria`.
- Strictly respect `Target Files`. If you must touch an unlisted file, stop and explain why in your final report.

### Step 2: Local Verification Loop (Max 5 Attempts)
Run the stack commands defined in `.factory/TECH_STACK.md` in this order:
1. Typecheck / Build
2. Linter / Formatter
3. Issue-specific `Verification Command`
4. Full unit/integration test suite

If any step fails:
- Read the error output, fix the root cause (do not delete or skip failing tests), and re-run.
- If still failing after **5 attempts**, STOP and report the exact failure logs to the Orchestrator.

### Step 3: Pull Request & Green CI Loop (Max 3 CI Retries)
- Commit clean, atomic changes referencing the Issue ID (e.g., `feat(M1-02): add auth middleware`).
- Push the branch and open a Pull Request (using GitHub CLI or the Git/GitHub MCP defined in `.factory/MCPS.md`).
- Check whether CI exists before waiting for it: look for workflow files on the base branch (e.g. `.github/workflows/`) or the CI system named in `.factory/TECH_STACK.md`.
  - **No CI configured:** do NOT wait. Go straight to Step 4 and report with `Remote CI: NOT CONFIGURED` in your report and `ciStatus: NOT_CONFIGURED`.
  - **No checks appear within 10 minutes** of pushing, even though CI is configured: stop waiting and report with `Remote CI: NO CHECKS REPORTED (waited 10 min)` and `ciStatus: NO_CHECKS`. Do not wait indefinitely.
- Otherwise, monitor CI checks until completion. When a check fails, read its logs and annotations and **classify the failure before acting** (see `.factory/steering/workflow-rules.md` section 7):
  - **Caused by your change:** push a fix commit to the same branch and re-verify. If CI fails **3 times** for code reasons, STOP and escalate to the Orchestrator (`BLOCKED`, `blockerType: RETRY_CAP`).
  - **Infrastructure / external** (the job never started or failed before any step ran, billing or spending limit, no runners, missing secret, permission error, service outage): do NOT push fixes, edit CI config, or keep re-running. Record it with `factory_report_incident` (e.g. category `RATE_LIMIT` for billing or spending limits, `THIRD_PARTY` for outages). If local checks pass, report `WAITING_FOR_REVIEW` with `ciStatus: INFRA_BLOCKED` and the exact message in `ciDetails`. If you couldn't finish local verification either, report `BLOCKED` with `blockerType: INFRA`.
  - **Pre-existing failure** (code outside your Target Files that you did not change and that also fails on the base branch): do not fix it. Report `ciStatus: FAILED_PREEXISTING` with the file, line, and error in `ciDetails` and under Deviations / Notes. The same applies to local checks that fail only because of pre-existing code.

### Step 4: Handoff & Review Readiness
- Once local tests are green AND remote CI is green (or not configured / reported no checks, per Step 3), return the **Worker Completion Report** below.
- **Do NOT close your session or delete your worktree** until the Orchestrator explicitly approves and merges the PR. If the Orchestrator requests changes, apply them on the same branch, re-verify green CI, and submit an updated report.

## Blockers Outside Your Control (Any Step)
If something outside your code stops you (a permission or security block, a credential problem, an API key, rate, quota, or billing limit, a CI/CD or third-party failure, a network problem, or a missing tool), follow section 7 of `.factory/steering/workflow-rules.md`:
1. Stop the failing action. Do not loop, and never look for another way around a security or permission control.
2. Apply at most one safe self-remedy (see section 7). If it works, continue and mention it in your report.
3. Otherwise call `factory_report_incident` with the exact error, what you tried, and concrete `suggestedActions`.
   - **You can't continue the issue:** use `blocking: true` (and `needsHuman: true` if only the user can fix or decide it), then return a short report naming the incident and stop. The Orchestrator resolves it or asks the user, then resumes you.
   - **You can continue other parts:** use `blocking: false`, keep working, and name the incident in your report.
4. If a tool reports success but the effect is missing (e.g. a written file isn't on disk), treat it as a blocker of this kind. On Windows, say that Controlled Folder Access or antivirus may be blocking the tool.

## Worker Completion Report Format
```markdown
### Worker Report: [ISSUE-ID]
- **PR URL / Branch:** [link or branch name]
- **Files Changed:**
  - `path/to/file` — [1-line summary]
- **Verification Results:**
  - Build/Typecheck: PASS
  - Lint: PASS
  - Tests: PASS (`[command run]`)
  - Remote CI: GREEN | NOT CONFIGURED | NO CHECKS REPORTED (waited 10 min) | INFRA BLOCKED (<exact message>) | FAILED (pre-existing: <file:line>)
- **Incidents:** None (or `INC-xxx`: one-line summary, and any self-remedy you applied)
- **Deviations / Notes:** None (or explain any edge cases)
```