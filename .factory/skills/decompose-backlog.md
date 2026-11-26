# Skill: Decompose Planning Specs into Milestones & Issues

## Objective
Read `.factory/PRD.md`, `.factory/ARCHITECTURE.md`, and `.factory/TECH_STACK.md`, and generate `.factory/BACKLOG.md` containing a complete, ordered list of Milestones and atomic Issues.

## Core Rules
1. **Single-Session Scope:** Every issue must be small enough for a single fresh subagent session to implement, test, and open a PR without exhausting its context window (typically 1–4 files modified/created per issue).
2. **Explicit File Ownership:** Every issue MUST list the exact files or directories it will create or modify. Never write vague scopes like "update backend."
3. **Verifiable Acceptance Criteria:** Every criterion must be objectively testable (command exit codes, HTTP status codes, UI states, unit test assertions). No subjective language ("works cleanly", "looks good").
4. **No Missing Glue:** Include foundational setup issues (database schemas, shared types, test harness setup, CI workflow) explicitly as early Milestone 1 issues.
5. **CI Comes First:** Place the CI workflow issue immediately after the minimal scaffolding it needs (usually the second issue), so every later issue's PR is verified by real CI. Only the issues before it may report `Remote CI: NOT CONFIGURED`.
6. **Strict Spec Alignment:** Do not invent features not present in `PRD.md`, and do not deviate from module boundaries or folder paths defined in `ARCHITECTURE.md`.

## Output Format (`.factory/BACKLOG.md`)
Structure the generated file strictly using this template:

```markdown
# Project Backlog

## Milestone 1: [Milestone Name]
**Goal:** [1-sentence milestone deliverable]

### [M1-01] [Imperative Issue Title]
- **Status:** `TODO`
- **Target Files:**
  - `path/to/file1` (create)
  - `path/to/file2` (modify)
- **Context & Requirements:**
  - [Specific implementation details referencing ARCHITECTURE.md]
- **Acceptance Criteria:**
  - [ ] [Concrete, testable condition 1]
  - [ ] [Concrete, testable condition 2]
- **Verification Command:** `[exact command from TECH_STACK.md to test this slice]`
```

## Self-Check Before Finishing
- Does every requirement in `PRD.md` map to at least one issue?
- Are any issues touching >5 files? If so, split them into smaller vertical or layered issues.
- Are all target file paths consistent with `ARCHITECTURE.md`?