# Agent Operating Instructions

This repository uses a spec-driven workflow of Milestones and Issues stored in `.factory/`. `.factory/` is the single source of truth; adapters and plugins point to it instead of copying it.

## First-Time Setup ("Handle It" Protocol)
If the user asks you to initialize, set up, or handle this workflow in a new repository:
1. **Tool Adaptation:** Check what AI environment you are running in. If your runtime expects instructions or skills in a specific folder (e.g., `CLAUDE.md`, `.claude/skills/`, `.kiro/steering/`, `.cursor/rules/`), create lightweight symlinks or adapter files pointing to `.factory/` so rules and skills load natively.
   - **Session plugin (optional):** If `.agents/plugins/factory-loop/` exists, register its `factory-session-hub` MCP server by running `python .agents/plugins/factory-loop/scripts/install.py --host <host>` (`claude`, `cursor`, `vscode`, `kiro`, `devin`, `antigravity`, or `codex`; use whichever Python 3 command exists: `python3`, `python`, or `py -3`). Ask the user before using `--host codex`, because it edits a global config. Then tell the user to fully restart or reload the tool, since the new tools usually won't appear in the current session. After the restart, confirm `factory_session_list` works.
2. **Existing Codebase Check:** If the repository already contains application code but has no `.factory/TECH_STACK.md` or `.factory/ARCHITECTURE.md`, run `.factory/skills/onboard-repo.md` first. It reverse-engineers baseline `TECH_STACK.md`, `ARCHITECTURE.md`, `MCPS.md`, and `LEARNINGS.md` from the real code, then asks whether the user wants a **new feature** (draft a delta `PRD.md`, then follow the steps below) or a **specific bug fix** (`.factory/skills/bugfix-issue.md`). Skip Planning Mode's full interview for a brownfield repo; only the delta `PRD.md` is needed.
3. **Project Spec Check:** Check whether `.factory/PRD.md`, `.factory/ARCHITECTURE.md`, `.factory/TECH_STACK.md`, and `.factory/MCPS.md` exist.
   - If they are missing, enter **Planning Mode**: interview the user briefly about their project idea and iteratively draft those 4 files using the exact templates in `.factory/steering/spec-blueprints.md`.
   - Once the 4 specs are approved, run `.factory/skills/decompose-backlog.md` followed by `.factory/skills/schedule-dag.md` to generate `.factory/BACKLOG.md`.
   - Once `.factory/BACKLOG.md` is approved, enter **Orchestrator Mode** (`.factory/skills/orchestrator.md`) to execute the issues.

## Always-On Steering Rules
Read and obey these files on every session:
1. `.factory/steering/workflow-rules.md` — Universal coding, testing, git, and MCP guardrails.
2. `.factory/steering/coding-standards.md` — Stack-agnostic implementation, testing, documentation, and delivery standards.
3. `.factory/steering/spec-blueprints.md` — Canonical templates for generating project specs.

## Project Specs (Read when present)
- `.factory/PRD.md` — Product requirements and scope boundaries
- `.factory/ARCHITECTURE.md` — System design, directory tree, and module contracts
- `.factory/TECH_STACK.md` — Stack, dependencies, and exact build/lint/test commands
- `.factory/MCPS.md` — Configured MCP servers and tool usage rules
- `.factory/BACKLOG.md` — Milestones, atomic issues, and per-issue serial/parallel schedule

## Workflow Skills (`.factory/skills/`)
- `onboard-repo.md` — Reverse-engineers baseline specs (`TECH_STACK.md`, `ARCHITECTURE.md`, `MCPS.md`, `LEARNINGS.md`) for an existing undocumented repository
- `decompose-backlog.md` — Turns specs into atomic, single-session issues in `BACKLOG.md`
- `schedule-dag.md` — Marks each issue Serial or Parallel, with dependencies and file conflicts
- `orchestrator.md` — Main coordinating session loop (dispatches ready issues, reviews PRs, merges)
- `subagent-worker.md` — Isolated per-issue worker SOP (build -> local test -> green CI -> PR)
- `bugfix-issue.md` — Reproduce-first worker SOP for bugfix issues (failing test -> fix -> green CI -> PR)