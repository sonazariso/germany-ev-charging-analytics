# Changelog

This changelog records project milestones and local repository changes. Historical Batch 01–03 entries describe work evidenced by local reports; they do not imply historical Git commits or inferred dates.

## Historical project milestones before the local Git baseline

- Source discovery and profiling: created the source manifest, downloaded or verified the BNetzA 2026-09-30 workbook and three KBA FZ 27 2026 workbooks, preserved hashes, and profiled every worksheet.
- DuckDB ingestion and validation: preserved raw worksheet rows and built the initial normalized equipment, charging-point, and KBA tables with validation artifacts.
- Data-quality investigations: reconciled equipment rows to charging-point slots, inspected KBA alternative grains, investigated connector-power text, and documented data-quality exceptions.
- Charging and BEV analytical exploration: calculated declared-power bands, equipment nominal power, state-level summaries, and KBA stock comparisons.
- Batch 01: completed live read-only DuckDB baseline validation.
- Batch 02: completed charging-power analysis and geographic-crosswalk readiness review.
- Batch 03: created the versioned BNetzA-to-KBA crosswalk, aggregate-before-join validation, and reusable read-only Batch Analysis Runner.

## 2026-11-02 — Batch 04

- Added professional English project documentation under docs/.
- Reworked README.md into a GitHub-ready landing page without claiming Tableau or BBSR completion.
- Added AGENTS.md, PROJECT_STATUS.md, and this changelog.
- Updated .gitignore for local databases, raw sources, temporary data, uncontrolled exports, and internal working notes while allowing the curated crosswalk.
- Added local Git metadata and prepared the first reviewed baseline commit.
- Preserved source workbooks and DuckDB outside the commit.
- No GitHub remote was added and nothing was uploaded.

## 2026-11-02 — Batch 05

- Validated the pre-integration geographic model with one read-only DuckDB connection and SELECT/CTE queries.
- Recomputed KBA-code regional power bands from all semicolon-separated connector-power tokens using the maximum valid value per point.
- Confirmed source-aware equipment-to-point retention, 401 BNetzA combinations, 400 KBA codes, 24 explicit provisional mappings, and 1,200 KBA code/date rows.
- Documented the proposed permanent reference table and analytical views, including source dates, mapping flags, Trier handling, the existing state-view join correction, and backup/rollback requirements.
- Added the Batch 05 pre-integration review report and updated geographic, KPI, and data-quality documentation.
- Did not modify the Crosswalk CSV, source workbooks, or DuckDB; no remote was added and nothing was uploaded.

## 2026-11-02 — Batch 06

- Created and verified a byte-preserving pre-deployment DuckDB backup before the approved database change.
- Deployed `reference.bnetza_kba_district_crosswalk_2026`, `analytics.charging_by_kba_district_2026_09_30`, and `analytics.kba_district_charging_vs_bev_2026`.
- Corrected `analytics.charging_by_state` to aggregate and join charging points on `(source_id, equipment_excel_row)` while preserving the 16-state baseline output.
- Added reproducible deployment SQL, controlled deployment code, and an independent read-only validation suite.
- Documented the deployed grains, source dates, provisional mappings, shared Trier treatment, backup evidence, and remaining limitations.
- Did not modify source workbooks or the Crosswalk CSV; no remote was added and nothing was uploaded.

## 2026-11-02 — Batch 06.1

- Audited the English KPI catalog against the 16 requested metric domains and the validated local reports/source fields.
- Preserved the 20 existing numbered KPI definitions and added explicit state/district distribution and data-quality coverage definitions.
- Added status distinctions for validated, provisional, exploratory, defined-but-not-validated, proposed, and unsupported measures.
- Recorded PHEV candidate measures, city/county, operator, descriptive source-field, KBA ownership/postcode/municipality, BBSR, and unsupported real-time domains without promoting unapproved analyses.
- Added `reports/batch06-1_kpi_documentation_audit.md` and generated the private Persian KPI reference outside the Git worktree.
- Did not modify source workbooks, DuckDB objects, the Crosswalk CSV, or raw data; no remote was added and nothing was uploaded or published.

## 2026-11-02 — Batch 06.2

- Relocated the complete local project into the established `dev` development root, preserving `.git`, the ignored source workbooks, DuckDB database and backups, `.venv`, reports, scripts, SQL, documentation, and configuration.
- Relocated the private Persian KPI catalog into the sibling `../germany-ev-charging-analytics-private/` directory, completely outside the Git repository.
- Verified before/after inventories and hashes, Git history, clean status, absent remotes, read-only database and backup integrity, Crosswalk integrity, and the independent Batch 06 validator after relocation.
- Updated the local DBeaver connection/output paths and VS Code workspace record to the relocated project; these machine-local settings remain outside Git.
- Documented the project-relative reproducibility workflow and the preserved `.venv` portability caveat; no dependency installation or recreation was performed.
- Did not change source workbooks, DuckDB schemas or objects, analytical logic, or the Crosswalk CSV; no remote was added and nothing was uploaded or published.
