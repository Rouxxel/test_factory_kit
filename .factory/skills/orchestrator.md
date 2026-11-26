# Skill: Project Orchestrator

## Objective
Manage end-to-end execution of `.factory/BACKLOG.md` (Milestones and Issues) issue by issue. You do NOT write feature code directly; you dispatch isolated subagent sessions, enforce quality gates, review PRs, maintain session state, and merge only verified work.

## Session Tools
If the `factory-session-hub` MCP server is available, use its tools instead of the manual steps below: `factory_session_dispatch`, `factory_session_list`, `factory_session_get_status`, `factory_session_send_feedback`, `factory_session_teardown`, `factory_report_incident`, and `factory_resolve_incident`. Otherwise, run the equivalent `git worktree` commands and track sessions in `.factory/SESSION_STATE.md` manually.

## Startup & Resume Check
Before dispatching anything, read `.factory/SESSION_STATE.md`, `.factory/BACKLOG.md`, and `.factory/LEARNINGS.md`:
- If `SESSION_STATE.md` (or `factory_session_list`) shows in-flight worktrees or open PRs from an earlier session, inspect their current status first before starting new work.

## Orchestration Loop

### Step 1: Select Ready Issues
- A **ready issue** is a `TODO` issue whose `Depends On` prerequisites are all `DONE`. Consider issues in Milestone order.
- If a `SERIAL` issue is in flight, dispatch nothing else until it is merged.
- If the earliest ready issue is `SERIAL`, wait until nothing is in flight, then dispatch it alone.
- Otherwise, dispatch **up to N concurrent subagent sessions** for ready `PARALLEL` issues, skipping any issue listed in `Conflicts With` of an issue that is in flight or already selected.
- Re-evaluate ready issues after every merge; do not wait for a whole batch to finish.

### Step 2: Provision Isolated Workspaces & Dispatch
For each issue being dispatched:
1. Create an isolated Git worktree and branch (`factory_session_dispatch`, or `git worktree add ../wt-<issue-id> -b feat/<issue-id>` / `fix/<issue-id>`).
2. Open a **fresh subagent session** inside that worktree using your tool's native subagent mechanism, and include the `sessionId` (if using session tools) and worktree path in its prompt.
3. Pass the subagent:
   - Instructions to follow `.factory/skills/bugfix-issue.md` (if it is a bugfix) or `.factory/skills/subagent-worker.md` (for all other issues)
   - The exact issue block from `.factory/BACKLOG.md`
   - Pointers to `.factory/ARCHITECTURE.md`, `.factory/TECH_STACK.md`, `.factory/MCPS.md`, and `.factory/LEARNINGS.md`
4. Mark the issue status in `.factory/BACKLOG.md` as `IN_PROGRESS` and record the active branch/worktree in `.factory/SESSION_STATE.md`.

### Step 3: Monitor In-Flight Sessions
- Check `factory_session_list` (or the worktree's `git log` / `git status` without session tools) when waiting on workers.
- A session is **stalled** if it is `IN_PROGRESS` and `minutesSinceWorkerContact` (or, if the worker never made contact, `minutesSinceDispatch`) exceeds **15 minutes**. Before re-dispatching, inspect the worktree: commits on the branch, uncommitted changes, and whether the PR exists.
  - Work is done but no report arrived: send an instruction (`factory_session_send_feedback` without `round`) telling the worker to report, then resume or rehydrate it.
  - No changes at all: the worker likely never started, is waiting on a tool-permission prompt, or is being blocked by the environment. Check for environment blocks first; on Windows, Controlled Folder Access blocks appear as event 1123 in `Get-WinEvent -LogName 'Microsoft-Windows-Windows Defender/Operational' -MaxEvents 300 | Where-Object Id -eq 1123`. Record anything you find with `factory_report_incident`, tell the user, then resume or rehydrate the worker once it's fixed.
- Redispatching the same instructions repeats the same failure. If a session stalls twice, set it aside and ask the user.

### Step 4: PR Review Gate (When Subagent Reports Ready)
When a subagent returns a Worker Completion Report, inspect the PR diff against:
1. **Acceptance Criteria** in `.factory/BACKLOG.md` (is every checkbox genuinely satisfied?)
2. **Architectural Compliance** in `.factory/ARCHITECTURE.md` (correct folder structure, patterns, no unauthorized file edits?)
3. **Steering Compliance** in `.factory/steering/workflow-rules.md` (no Hard Red Line violations, no leftover debug logs, proper test coverage?)
4. **Coding Standards Compliance** in `.factory/steering/coding-standards.md` (scope, implementation quality, tests, contracts, and delivery requirements)
5. **CI Status** (`ciStatus` in the report):
   - `NOT_CONFIGURED` is acceptable only for issues scheduled before the CI workflow issue is merged; rely on the reported local results. After the CI issue merges, require green CI, and ask in-flight sessions to rebase so their PRs get checks.
   - `INFRA_BLOCKED`: review the code normally, but don't merge on that basis alone. Handle it under **Incidents, Blockers & Follow-ups** below.
   - `FAILED_PREEXISTING`: confirm the failure also occurs on the base branch. If it does, it doesn't block this PR; add a follow-up issue (below).
   - `FAILED` must never be approved.

### Step 5: Approve & Merge OR Reprompt Subagent
- **If Changes Needed:** Do NOT fix it yourself. Send concrete, line-specific review feedback (`factory_session_send_feedback`) and deliver it to the **existing subagent session** so it retains context, fixes the PR, and re-verifies green CI. If your tool cannot resume that subagent, spawn a fresh subagent in the **same worktree and branch** with the same `sessionId`; it rebuilds context from the session record and inbox. (Max 3 review rounds before escalating to the human user.)
- **If Approved:**
  1. Merge the PR into the base branch.
  2. Close the subagent session and remove its Git worktree (`factory_session_teardown`, or `git worktree remove ../wt-<issue-id>`).
  3. Update the issue status in `.factory/BACKLOG.md` to `DONE`.
  4. If other in-flight issues share a file with the merged PR, send them feedback to rebase onto the base branch and re-verify CI.
  5. If the subagent surfaced a reusable environment or codebase gotcha, append a concise bullet to `.factory/LEARNINGS.md`.
  6. Update `.factory/SESSION_STATE.md` with current progress and proceed to the next ready issues.

## Incidents, Blockers & Follow-ups
Workers record problems outside their control (permission or security blocks, credentials, API key/rate/quota/billing limits, CI/CD or third-party failures, network problems) as incidents. One incident often affects several sessions; handle it once.
- **Check open incidents every loop:** `openIncidents` in `factory_session_list` (without session tools: Blockers & Escalations in `SESSION_STATE.md` and the worker reports). You can record problems you find yourself with `factory_report_incident` (omit `sessionId`).
- **Triage each incident:**
  1. **A safe automatic fix exists:** no human input needed, reversible, within the project, and not bypassing any security or permission control (e.g. waiting for a short rate-limit reset, re-running a check after a transient outage, telling a worker to use a fallback the workflow allows). Apply it, call `factory_resolve_incident` with what you did, send each session in `sessionsToUnblock` an instruction (`factory_session_send_feedback` without `round`), resume them, and add a `LEARNINGS.md` bullet if it can recur.
  2. **It needs the user, or there are several reasonable options** (billing, credentials, security or permission settings, changing tools or scope): ask the user **once**, giving the incident ID, the exact error, numbered options with their trade-offs, and your recommendation. Record the question under Blockers & Escalations. When the user decides, carry it out, call `factory_resolve_incident`, and unblock the affected sessions.
  3. **While waiting**, keep working on issues the incident doesn't affect. Don't redispatch affected sessions or re-run checks to "try again".
- **CI infrastructure blockers** (`ciStatus: INFRA_BLOCKED`, e.g. CI billing or spending limits): the usual options are (a) fix the infrastructure, then re-run the checks (e.g. `gh run rerun <run-id>`); (b) waive CI for the affected PRs and merge on the reviewed local results, recording the waiver in `SESSION_STATE.md`; or (c) pause. Don't merge PRs that need CI until the user answers.
- **Pre-existing failures** reported by a worker: confirm them on the base branch, then add a follow-up bugfix issue to `BACKLOG.md` (file, line, error, scheduling fields), tell the user, and schedule it before issues that require green CI.

## Escalation Rule
Pause, update `.factory/SESSION_STATE.md` to `BLOCKED`, and ask the human user for intervention if:
- A subagent hits its local test retry cap (5) or CI retry cap (3).
- A PR fails 3 Orchestrator review rounds.
- A fundamental flaw in `PRD.md` or `ARCHITECTURE.md` is discovered mid-build.
- An incident needs the user's decision (see **Incidents, Blockers & Follow-ups**); ask once per incident, not once per session.