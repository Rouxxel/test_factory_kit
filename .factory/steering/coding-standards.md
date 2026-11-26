---
inclusion: always
---

# Universal Coding Standards

## 1. Project Sources of Truth

- Before changing code, read the relevant sections of `.factory/PRD.md`, `.factory/ARCHITECTURE.md`, `.factory/TECH_STACK.md`, `.factory/LEARNINGS.md`, and the assigned backlog issue.
- Follow the repository's established stack, patterns, naming, formatting, and test conventions. If these are undocumented, infer them from nearby production and test code rather than introducing a competing style.
- The project documents take precedence over generic preferences. Record a verified repo-specific convention in the appropriate project document or `.factory/LEARNINGS.md`; do not add it to this reusable file.
- Do not guess a command or dependency version. Use the canonical commands and versions in `.factory/TECH_STACK.md` or a verified project manifest and CI configuration.

## 2. Scope and Design

- Implement only the requested behavior and the files named by the assigned task.
- Keep changes small and cohesive. Refactor only when it is required for correctness or directly supports the assigned change.
- Preserve existing public interfaces unless the task explicitly requires a contract change. Update every known caller and document breaking changes.
- Respect module boundaries and dependency direction in `.factory/ARCHITECTURE.md`. Keep domain logic independent of infrastructure where the existing architecture does so.
- Prefer the smallest clear solution over speculative abstractions, feature flags, compatibility layers, or future-facing configuration.
- Make behavior explicit in code. Avoid hidden global state, silent fallbacks, and unrelated side effects.
- Reuse existing helpers, components, models, error types, configuration, and test utilities before adding equivalents.

## 3. Implementation Quality

- Use meaningful, consistent names and keep functions, components, modules, and classes focused on one responsibility.
- Make invalid states difficult or impossible to represent through types or invariants appropriate to the language.
- Validate data at system boundaries, including user input, external services, persisted data, and API responses.
- Handle errors deliberately. Preserve useful context and present errors in the format already established by the project.
- Never expose secrets, tokens, private data, or sensitive internal details in logs, responses, tests, fixtures, or commits.
- Avoid logging unnecessary payloads or personal data. Never introduce telemetry or third-party network behavior outside the approved scope.
- Use the project's formatter and follow existing file organization. Do not mix unrelated formatting or generated-code changes into implementation diffs.
- Do not disable checks, suppress diagnostics, or exclude failing tests to achieve a passing result.

## 4. Dependencies and Data

- Add dependencies only when needed and permitted by the project. Prefer maintained packages that fit the existing dependency and build system.
- Record dependency changes through the project's normal manifest and lockfile workflow.
- Do not pin, upgrade, or replace dependencies casually; keep changes in scope and verify compatibility.
- Use parameterized queries or the project's database/ORM APIs. Never construct queries or commands by unsafely concatenating untrusted input.
- Preserve data migration compatibility when required by the project. Never delete or overwrite shared data outside an explicit migration or task.

## 5. Testing

- Add or update tests for behavior introduced or changed by the task.
- Cover the normal path and relevant edge or failure cases. Prefer focused tests close to the unit or boundary they verify.
- Reproduce bugs with a failing regression test before the fix whenever the bug is observable through an automated test.
- Do not delete, weaken, skip, or duplicate tests to hide failures. Fix the implementation or the test setup if a test is invalid.
- Use realistic fixtures and deterministic time, randomness, network, and external-state behavior. Do not commit live credentials or environment-dependent data.
- Run the smallest relevant test first, then the broader checks required by the project. Full verification commands come from `.factory/TECH_STACK.md` or CI.
- If a test passes for the wrong reason or cannot exercise the acceptance criterion, improve the test or explain the gap to the reviewer.

## 6. Documentation and Contracts

- Update directly related documentation, examples, schemas, or generated artifacts when behavior or interfaces change.
- Keep comments focused on intent, constraints, and non-obvious tradeoffs. Do not narrate implementation or restate the code.
- Name configuration and environment variables consistently with the existing project and document required placeholders in `.env.example` or the project equivalent.
- For API, CLI, schema, or data-contract changes, update the authoritative contract and any generated clients or documentation required by the project.

## 7. Commits and Pull Requests

- Keep commits atomic and the diff limited to assigned work.
- Use the repository's issue and commit conventions. When no convention exists, use a concise imperative subject prefixed with the issue ID.
- Include a clear summary of what changed and the relevant verification in the pull request or worker report.
- Never include generated secrets, local configuration, caches, build output, or unrelated files.
- Do not rewrite shared history or use force-push on base branches.

## 8. Definition of Done

A task is complete only when all applicable items are satisfied:

- The implementation matches the acceptance criteria and project architecture.
- Tests cover the changed behavior, including meaningful edge cases.
- Relevant focused checks and the project's build/typecheck, lint/format, and test commands pass.
- CI is green when CI or a pull request is part of the workflow.
- Public interfaces and directly related documentation are updated where needed.
- The diff contains no secrets, debug artifacts, unrelated changes, or unexplained deviations.
- The backlog or spec checkbox is updated only to reflect work that is actually complete.
