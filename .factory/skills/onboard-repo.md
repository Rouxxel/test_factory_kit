# Skill: Onboard Existing Undocumented Repository

## Objective
Inspect an existing codebase that lacks `.factory/` documentation and reverse-engineer accurate, factual baseline files for `.factory/TECH_STACK.md`, `.factory/ARCHITECTURE.md`, `.factory/MCPS.md`, and `.factory/LEARNINGS.md`.

## Inspection Checklist (Read-Only)
Before writing any spec files, inspect:
1. **Top-level directory tree** (2–3 levels deep, ignoring `node_modules`, `.git`, `dist`, `build`, `__pycache__`, `.venv`).
2. **Dependency & build manifests** (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`, `Dockerfile`).
3. **CI/CD pipelines** (`.github/workflows/*`, `.gitlab-ci.yml`) to find the exact commands CI runs for build, lint, typecheck, and tests.
4. **Entry points & core modules** (main server/app entry, router/controller layer, data/schema layer, test folder structure).
5. **Existing AI/editor configs** (`README.md`, `CLAUDE.md`, `.cursor/`, `.env.example`) for existing conventions or environment requirements.

## Output Files to Generate
Using the exact structures in `.factory/steering/spec-blueprints.md`, generate:
1. **`.factory/TECH_STACK.md`** — Document the actual languages, frameworks, and exact CLI commands verified from manifests and CI configs.
2. **`.factory/ARCHITECTURE.md`** — Map the real directory tree, module boundaries, data models/APIs, and shared high-contention files (e.g., central route files, schema files, barrel exports).
3. **`.factory/MCPS.md`** — List currently available MCP servers and how they map to this repo's git host and stack.
4. **`.factory/LEARNINGS.md`** — Pre-populate any non-obvious setup quirks found in `README.md`, `.env.example`, or CI scripts (e.g., required env vars, codegen steps, test DB setup).

## Rules
- **Fact-only:** Document what actually exists in the codebase today—do not propose refactors or aspirational architecture in these baseline docs.
- **Flag unknowns:** If a test or lint command cannot be verified from the repo, mark it `[VERIFY WITH USER]` rather than guessing.
- **Stop after onboarding:** Present a concise summary of the generated baseline docs and ask the user whether they are adding a **new feature** (draft delta `PRD.md` -> `BACKLOG.md`) or fixing a **specific bug** (run `bugfix-issue.md`).