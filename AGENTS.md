# AGENTS.md — Germany EV Charging Analytics

These instructions apply to every future batch in this repository.

## Required batch workflow

1. Read AGENTS.md and PROJECT_STATUS.md before changing anything.
2. State the Batch objective and exact scope.
3. Perform only changes approved by the project owner.
4. Execute applicable validations in proportion to the change risk.
5. Never mark a failed, incomplete, or provisional stage as successful.
6. Update relevant technical and analytical documentation.
7. Update docs/kpi-catalog.md if a KPI definition, denominator, grain, or validation status changes.
8. Update docs/data-dictionary.md if schemas or important fields change.
9. Update docs/decisions.md when a new decision is approved.
10. Update CHANGELOG.md and PROJECT_STATUS.md.
11. Inspect the Git diff and staging area for unexpected files, secrets, raw data, binaries, and personal paths.
12. Commit locally only after successful validation.
13. Return the commit hash, changed files, test results, and unresolved issues.

## Scope and safety boundaries

- Never create a GitHub repository, add a remote, push, upload, or synchronize unless the user explicitly authorizes publication in a future task.
- Do not modify original BNetzA or KBA workbooks.
- Do not introduce BBSR or other external datasets without an approved scope change.
- Do not fabricate results, KPIs, source verification, tests, or design decisions.
- Use repository-relative paths in documentation and generated reports.
- Keep public-facing documentation professional and in English.
- Preserve existing useful documentation and source files; improve rather than overwrite.

## Database rules

- Read-only is the default for analysis and validation.
- Open DuckDB with read_only=True for analytical inspection.
- Use read-write access only after approved design and change scope.
- Never rebuild, migrate, overwrite, or delete the database without explicit approval.
- Plan backup and recovery before an approved schema change.
- Preserve complete source detail and distinguish raw, core, and analytics grains.
- Keep BNetzA equipment rows separate from charging-point rows.
- Aggregate charging measures by KBA district code before joining KBA vehicle stock.
- Never duplicate KBA stock for the shared Trier/Trier-Saarburg code 07211.
- Keep BNetzA and KBA reference dates visible in every combined measure.
- Do not infer utilization, energy delivery, real-time availability, queue times, reliability, sales, or causality from these sources.

## Git and data hygiene

- Review git status, git diff, and staged paths before every commit.
- Never use indiscriminate git add -A when large or unknown artifacts exist.
- Keep raw XLSX files, DuckDB files and WALs, virtual environments, temporary data, uncontrolled exports, secrets, and machine-local settings out of Git.
- The curated crosswalk CSV under data/reference is approved for tracking.
- Do not invent a Git identity or change global Git configuration to unblock a commit.

## Completion report

Every Batch handoff must include:

- Objective and scope completed.
- Changed files.
- Validation commands and results.
- Local commit hash, if a commit was requested and created.
- Unresolved issues, provisional mappings, and pending decisions.
- Explicit confirmation that no remote was added and nothing was uploaded when publication was not authorized.
