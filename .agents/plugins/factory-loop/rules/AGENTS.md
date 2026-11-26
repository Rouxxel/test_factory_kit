# factory-loop Plugin Rules

This plugin only provides the `factory-session-hub` MCP tools and thin skill adapters. All workflow rules live in the repository:

- Entry point: `AGENTS.md` at the repository root.
- Always-on steering: `.factory/steering/workflow-rules.md`, `.factory/steering/coding-standards.md`, `.factory/steering/spec-blueprints.md`.
- Skills: `.factory/skills/*.md`.

When the `factory_session_*` / `factory_worker_*` tools are available, use them for worktree sessions and Orchestrator <-> subagent messaging instead of manual `git worktree` commands. Never edit files under `.factory/sessions/` by hand.
