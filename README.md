# test_factory_kit

AI Spec-Driven Development Starter Kit setup for autonomous planning, decomposition, and execution.

## Overview

This repository uses a spec-driven development loop:
1. **Planning Mode**: Define project specs in .factory/ (PRD.md, ARCHITECTURE.md, TECH_STACK.md, MCPS.md).
2. **Decomposition & Scheduling**: Break specs into atomic issues and build a dependency DAG in .factory/BACKLOG.md.
3. **Orchestrator Mode**: Coordinates subagent sessions in isolated Git worktrees, verifying builds and tests before merging.

## Quick Reference

- **Entry Point**: [AGENTS.md](AGENTS.md)
- **Always-on Steering**: [.factory/steering/](.factory/steering/)
  - [workflow-rules.md](.factory/steering/workflow-rules.md)
  - [coding-standards.md](.factory/steering/coding-standards.md)
  - [spec-blueprints.md](.factory/steering/spec-blueprints.md)
- **Skills**: [.factory/skills/](.factory/skills/)
- **Live Memory & State**:
  - [.factory/SESSION_STATE.md](.factory/SESSION_STATE.md)
  - [.factory/LEARNINGS.md](.factory/LEARNINGS.md)
