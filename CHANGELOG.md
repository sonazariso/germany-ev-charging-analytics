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
