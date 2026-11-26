# Skill: Bugfix Issue Worker (Reproduce -> Fix -> Green CI -> PR)

## Objective
Resolve **one reported bug** inside an isolated branch/worktree by proving the failure with an automated test first, fixing the root cause, verifying green local tests and CI, and opening a Pull Request.

## Context Loading
Before writing code, read ONLY:
1. The bug report / issue block in `.factory/BACKLOG.md`
2. `.factory/LEARNINGS.md`
3. `.factory/steering/workflow-rules.md`
4. `.factory/steering/coding-standards.md`
5. `.factory/ARCHITECTURE.md` (relevant sections only)
6. `.factory/TECH_STACK.md`
7. `.factory/MCPS.md`

## Execution Loop

### Step 1: Isolate & Reproduce First
- Ensure you are on a dedicated branch (`fix/<issue-id>-<short-slug>`) in an isolated worktree.
- Write a minimal failing unit or integration test that reproduces the exact bug.
- Run the test command from `.factory/TECH_STACK.md` and confirm the new test **fails for the expected reason** before changing application code.

### Step 2: Fix Root Cause & Verify Locally (Max 5 Attempts)
- Implement the smallest clean fix addressing the root cause (not a surface workaround).
- Re-run:
  1. Your new regression test (must now PASS)
  2. Typecheck / Build
  3. Linter / Formatter
  4. Full test suite
- If any check fails after **5 attempts**, STOP and escalate the exact logs to the Orchestrator.

### Step 3: Pull Request & Green CI Loop (Max 3 CI Retries)
- Commit with `fix(<issue-id>): <concise root-cause summary>`.
- Push and open a Pull Request, then monitor CI until green (max 3 fix commits if CI fails).
- Follow the CI rules in Step 3 of `.factory/skills/subagent-worker.md`: if no CI is configured, or no checks appear within 10 minutes, report instead of waiting, and classify every CI failure (caused by your change, infrastructure/external, or pre-existing) before acting. For anything outside your code (permissions, credentials, limits, third parties), follow **Blockers Outside Your Control** in the same file.

### Step 4: Handoff
- Return the standard **Worker Completion Report** including:
  - **Root Cause:** 1–2 sentences explaining why the bug occurred.
  - **Regression Test Added:** Path to the test proving the fix.
- Keep your worktree/session open until the Orchestrator merges the PR.
- If you were given a `sessionId`, follow the **Session Tools** section of `.factory/skills/subagent-worker.md` for inbox checks and reporting.
