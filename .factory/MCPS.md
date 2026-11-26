# Configured MCP Servers & Usage Rules

## Active MCPs
- **factory-session-hub:**
  - **When to use:** Orchestrator session dispatch (`factory_session_dispatch`), worker reporting (`factory_worker_report`), progress tracking (`factory_worker_progress`), incident logging (`factory_report_incident`), and review feedback (`factory_session_send_feedback`).
  - **Rules:** Never edit files inside `.factory/sessions/` directly; coordinate exclusively via MCP tools. If the server is not available in the current session, fall back to `git worktree` and `.factory/SESSION_STATE.md`.

## Other Tools
- **GitHub CLI (`gh`):** Authenticated as `Rouxxel`. Use for PR creation, CI checks, and merges against `Rouxxel/test_factory_kit`.