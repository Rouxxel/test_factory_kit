# Steering: Project Spec Blueprints

When bootstrapping a new project during the Planning Phase, generate the following 4 files inside `.factory/` using these exact structures so downstream skills (`decompose-backlog.md`, `schedule-dag.md`, `subagent-worker.md`) can parse them reliably.

---

## Blueprint 1: `.factory/PRD.md`
```markdown
# Product Requirements Document (PRD)

## 1. Problem & Goal
[1–2 paragraphs on what we are building, who it is for, and the core value]

## 2. Core User Flows & Features
- **[Feature Name]:** [Concrete behavior, inputs, outputs, and edge cases]

## 3. Explicit Non-Goals (Out of Scope)
- [What we are NOT building in this version]

## 4. Global Success Criteria
- [Measurable criteria defining a complete v1]
```

---

## Blueprint 2: `.factory/ARCHITECTURE.md`
```markdown
# System Architecture

## 1. Directory & File Map
[Exact folder tree showing where modules, routes, components, schemas, and tests live]

## 2. Module Boundaries & Responsibilities
- **[Module Name] (`path/to/module`):** [Responsibility, public interface, dependencies]

## 3. Data Models & API Contracts
[Schemas, types, request/response shapes — critical so parallel subagents do not collide]

## 4. Shared / High-Contention Files
[List central registries, route tables, config files, or schemas that must be edited serially]
```

---

## Blueprint 3: `.factory/TECH_STACK.md`
```markdown
# Tech Stack & Verification Commands

## 1. Stack & Key Dependencies
- **Language / Runtime:** [e.g., TypeScript / Node 22, Python 3.12]
- **Framework & Libraries:** [Core libraries and versions]
- **Database / Infra:** [Storage, auth, hosting]

## 2. Canonical CLI Commands
- **Install:** `[command]`
- **Build / Typecheck:** `[command]`
- **Lint / Format:** `[command]`
- **Test (Single File/Slice):** `[command pattern]`
- **Test (Full Suite):** `[command]`
```

---

## Blueprint 4: `.factory/MCPS.md`
```markdown
# Configured MCP Servers & Usage Rules

## Active MCPs
- **[MCP Name] (e.g., GitHub / Linear / Context7 / Playwright):**
  - **When to use:** [Specific trigger, e.g., "Opening PRs and inspecting CI logs"]
  - **Rules:** [Any guardrails, e.g., "Never merge PRs directly; only open and update"]
```