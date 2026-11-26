# Steering: Universal Engineering & Agent Guardrails

## 1. Spec-First Discipline
- Never guess requirements, folder paths, or CLI commands. Always check `.factory/PRD.md`, `.factory/ARCHITECTURE.md`, `.factory/TECH_STACK.md`, and `.factory/LEARNINGS.md` first.
- If a requirement is ambiguous or conflicts with `ARCHITECTURE.md`, pause and ask the user or Orchestrator instead of inventing a workaround.

## 2. Strict Scope & Workspace Isolation
- Modify ONLY the files listed in your assigned task or issue. Never perform opportunistic refactoring outside your scope.
- When executing backlog issues, always work on a dedicated branch (`feat/<issue-id>-<slug>` or `fix/<issue-id>-<slug>`) inside an isolated working directory or Git worktree so parallel sessions never collide.

## 3. Verification Before Completion
- Never declare work complete without running the project's actual build, typecheck, linter, and test commands defined in `.factory/TECH_STACK.md`.
- Never delete, skip, or weaken existing tests to force a passing suite. Fix the root cause in the implementation.

## 4. Hard Red Lines (Strictly Forbidden)
- **No Secrets in Code:** Never commit `.env` files, real API keys, tokens, or credentials. Use `.env.example` with placeholder values.
- **No Destructive Commands:** Never run `git push --force` on base branches (`main`/`master`), `git reset --hard` outside your isolated worktree, or commands that drop/wipe shared databases.
- **No Check Bypassing:** Never use `--no-verify`, suppress type/lint rules (`@ts-ignore`, `# type: ignore`, `eslint-disable`) to hide errors, or disable failing CI checks.

## 5. MCP & Tool Hygiene
- Consult `.factory/MCPS.md` before invoking external integrations. Prefer structured MCP servers (issue trackers, Git/PR tools, official doc lookups) over brittle scripts or guesswork.
- Keep commits small, clean, and prefixed with the issue ID (e.g., `feat(M1-02): ...` or `fix(M1-03): ...`).

## 6. Context Hygiene
- Keep sessions focused on a single role (Planning, Orchestrating, or executing ONE Issue). Do not mix planning edits with feature implementation in the same session.

## 7. External, Permission & Infrastructure Blockers
Some failures cannot be fixed with code. Recognize them, stop, record them, and report them instead of retrying.
- **What counts:**
  - **Permissions & security:** tool-permission denials, OS or security-software blocks (e.g. Windows Controlled Folder Access, antivirus, read-only or locked files), sandbox restrictions.
  - **Credentials:** missing or expired tokens, API keys, or secrets; HTTP 401/403; "Resource not accessible".
  - **Limits:** API key quotas, rate limits (HTTP 429), billing or spending limits, exhausted CI minutes.
  - **Third parties:** CI/CD jobs that never start or fail before any step runs, external API or service errors and outages, package-registry failures, network or DNS problems.
  - **Environment:** missing tools or runtimes, full disk.
- **Verify side effects.** After writing files, pushing, or opening a PR, confirm the result exists (the file on disk, `git status`, `gh pr view`). A tool that reports success without the effect is a blocker of this kind, often a silent security block.
- **Never bypass a security or permission control.** Don't disable, evade, or work around antivirus, Controlled Folder Access, sandboxes, permission policies, or branch protections, even if another tool could get past them. Report them.
- **Never work around them in code:** no commits, code changes, or CI-config edits to get past an infrastructure failure, and never disable a check.
- **Self-remedy only when it is safe** (no human input, reversible, within your scope, not evading a control), and at most once:
  - retry once after a short wait for errors that look transient (timeouts, HTTP 5xx, connection resets);
  - wait for a rate limit to reset when the reset time is given and is under about 5 minutes;
  - use a fallback the workflow already allows (e.g. `git diff` when `gh` is unavailable, local results when CI is unavailable).
  Errors that state their cause (billing, permissions, missing secret, security block) are final: don't retry them.
- **Record and report.** Record every blocker you did not fully resolve. With the session tools, call `factory_report_incident` (category, one-line summary, the exact error and what you tried in `details`, `suggestedActions`, `needsHuman`, `blocking`). Without them, add it under Blockers & Escalations in `.factory/SESSION_STATE.md` or in your report. If a self-remedy worked, still mention it in your report so the Orchestrator can add it to `LEARNINGS.md`.
- **Retry caps are for code failures.** These blockers don't count toward the local or CI fix-retry caps, because more attempts cannot fix them.
- **Pre-existing failures:** if a check fails because of code outside your Target Files that you did not change (confirm it also fails on the base branch), do not fix it. Report the file, line, and error so the Orchestrator can schedule a follow-up issue.
