# Skill: Dependency Analysis & Issue Scheduler (Serial vs. Parallel)

## Objective
Read `.factory/BACKLOG.md` and `.factory/ARCHITECTURE.md`, determine hard dependencies and file-level conflicts between issues, and enrich `.factory/BACKLOG.md` with an **Execution Schedule** and per-issue scheduling metadata. The backlog is organized only as **Milestones and Issues**; the Orchestrator picks ready issues continuously based on this metadata.

## Scheduling Fields
- **Execution Mode:**
  - `SERIAL` — must run with **no other issue in flight** (scaffolding, CI setup, core configuration, cross-cutting changes).
  - `PARALLEL` — may run alongside other ready `PARALLEL` issues, except those listed in `Conflicts With`.
- **Depends On:** Issues that must be `DONE` before this issue starts (order matters).
- **Conflicts With:** Issues that must not be in flight at the same time as this issue (order does not matter). Always list conflicts symmetrically on both issues.

## Classification Rules

### Add `Depends On` when ANY of these hold:
1. **Contract Dependency:** Issue B consumes an API endpoint, database table, interface, or module produced by Issue A.
2. **Foundational Setup:** Project scaffolding, CI setup, or core configuration must complete before feature work branches out.
   - **CI rule:** the CI workflow issue is `SERIAL`, and **every later issue that opens a PR lists it in `Depends On`**. Otherwise those PRs have no checks to wait for.
3. **Ordered File Overlap:** Issue B's edit to a shared file builds on Issue A's edit to that file.

### Mark as `SERIAL` when:
- The issue is foundational or cross-cutting (touches many modules, global config, or shared tooling) so nothing else should run at the same time.

### Shared Files Between Parallel Issues
Each issue runs in its own worktree, so parallel issues never write the same file on disk; the risk is merge and semantic conflicts when their branches are merged.
1. **Same file, disjoint symbols → may stay PARALLEL** when ALL of these hold:
   - Each issue's `Target Files` entry names the distinct symbols or sections it owns, e.g. `src/api/users.ts` (modify: `getUser`) vs. `src/api/users.ts` (modify: `listUsers`).
   - The edited regions are not adjacent.
   - Neither issue changes shared imports, exports, or signatures used by the other.
2. **Same file, risky overlap → NOT parallel.** If the file is a lockfile, schema/migration, route or DI registry, barrel/index file, generated file, or shared config, or both issues edit the same symbol, link the issues with `Depends On` (if order matters) or `Conflicts With` (if it doesn't). Alternatively, extract the shared edit into an earlier issue.

### Mark as `PARALLEL` when ALL of these hold:
1. Target file sets are disjoint, or every shared file satisfies the "disjoint symbols" rule above.
2. The issue can be tested independently without race conditions on shared external state (databases, ports, fixtures).

## Required Updates to `.factory/BACKLOG.md`

### 1. Add a Top-Level Execution Schedule Table
Insert this table at the top of `.factory/BACKLOG.md`:

```markdown
## Execution Schedule
| Issue | Mode | Depends On | Conflicts With | Execution Notes |
| :--- | :--- | :--- | :--- | :--- |
| `M1-01` | Serial | None | None | Repo & schema foundation |
| `M1-02` | Parallel | `M1-01` | None | Shares `src/api/users.ts` with M1-03 (`getUser` only) |
| `M1-03` | Parallel | `M1-01` | None | Shares `src/api/users.ts` with M1-02 (`listUsers` only) |
| `M1-04` | Parallel | `M1-01` | `M1-05` | Both edit `src/routes/index.ts` registry |
| `M1-05` | Parallel | `M1-01` | `M1-04` | Both edit `src/routes/index.ts` registry |
| `M1-06` | Serial | `M1-02`, `M1-03` | None | Integrates M1-02 and M1-03 |
```

### 2. Add Scheduling Metadata to Every Issue Block
Add these three fields directly under `**Status:**` on every issue:

```markdown
- **Execution Mode:** `SERIAL` | `PARALLEL`
- **Depends On:** `None` | `M1-01, M1-02`
- **Conflicts With:** `None` | `M1-04`
```

## Self-Check Before Finishing
- Verify there are **zero circular dependencies**.
- Verify the CI workflow issue is `SERIAL` and every issue scheduled after it depends on it (directly or through another dependency).
- Verify every `Conflicts With` entry is listed on both issues.
- Verify that any two `PARALLEL` issues that could be in flight together and share a file path either satisfy the "disjoint symbols" rule (with symbols named in `Target Files`) or are linked by `Depends On` / `Conflicts With`.
