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

## 2026-11-02 — Batch 07

- Reviewed all 24 provisional BNetzA-to-KBA crosswalk rows against the Destatis GV-ISys Q3 2026 administrative classification and official KBA FZ 27.15 July 2026 evidence.
- Classified 22 mappings as independently supported at the row/entity level, two Trier mappings as partially supported shared KBA-registration-region mappings, and zero row identities as unresolved.
- Confirmed the distinction between Destatis AGS/ARS and KBA registration-district keys; no universal code-system equivalence was inferred.
- Confirmed that KBA FZ 27.15 reports 7,869 July 2026 BEVs for combined row `07211 TRIER-SAARBURG`; preserved aggregate-before-join and did not allocate the stock to either administrative unit.
- Added the Batch 07 evidence report and updated geographic methodology, data-quality, decision-log, and project-status documentation.
- Did not modify the Crosswalk CSV, DuckDB reference table, analytics views, KPIs, source workbooks, Python environment, dependencies, or datasets; no remote was added and nothing was uploaded or published.

## 2026-11-02 — Batch 08

- Independently verified all 22 identity-supported aliases with dated Destatis and local KBA FZ 27.15 evidence, distinguishing row-level five-digit key evidence from universal AGS/ARS equivalence.
- Confirmed that Hanau and Main-Kinzig-Kreis are separate in the 2026-09-30 BNetzA source and in the 2026-01-01, 2026-04-01, and 2026-07-01 KBA FZ 27.15 snapshots.
- Confirmed that Trier city and Trier-Saarburg remain one combined KBA registration region, with July 2026 BEV stock of 7,869 joined once after KBA-code aggregation.
- Added `reports/batch08_geographic_code_verification.md` and updated geographic methodology, data-quality, findings, decisions, roadmap, and project-status documentation.
- Preserved all 24 operational provisional statuses and all verified metrics; no source workbook, Crosswalk CSV, DuckDB object, view, KPI formula, or raw data was changed.
- No remote was added and nothing was uploaded or published.

## 2026-11-02 — Batch 09

- Researched the official BBSR four-category settlement-structural district typology, current reference-table downloads, Kreis/Kreisregion distinction, Umsteigeschlüssel, INKAR context, Destatis key definitions, and licensing.
- Identified `raumgliederungen-referenzen-2025.xlsx` and its `Kreisreferenz` sheet as the smallest suitable current official reference artifact found; documented its 31.12.2025 geographic stand, 400 Kreis rows, 362 Kreisregion keys, compact type codes 1–4, and attribution requirements.
- Performed a read-only KBA/BBSR prefix compatibility screen and documented the Hanau vintage gap, mixed Trier types, smaller-city Kreisregion groups, Berlin/Hamburg/Bremen/Bremerhaven, and special administrative structures.
- Compared direct, controlled administrative, and separate-detail integration strategies; recommended a conditional future Strategy C with visible `mixed_or_unresolved` and `vintage_mismatch` statuses.
- Added `reports/batch09_bbsr_feasibility.md` and updated project geography, data sources, architecture, KPI candidates, data quality, findings, decisions, roadmap, README, project status, and charter documentation.
- Kept BBSR integration NOT IMPLEMENTED: no complete INKAR download, source-manifest entry, Crosswalk change, DuckDB change, KPI value/formula change, Trier allocation, remote, upload, or publication.

## 2026-11-02 — Batch 10

- Rechecked the official BBSR reference-download page and selected the latest suitable listed workbook, `raumgliederungen-referenzen-2025.xlsx`; no 2026 workbook was listed at the check time, and the complete INKAR database was not downloaded.
- Downloaded and preserved the original BBSR workbook under the ignored `data/raw/bbsr/` path with its URL, workbook geographic stand `2025-12-31`, workbook stand `2026-09-11`, response metadata, actual size, UTC download timestamp, and SHA-256.
- Added `scripts/10_build_bbsr_reference.py`, which inspects all six sheets, validates the exact `Kreisreferenz` source fields, preserves string codes and original names, extracts compact BBSR types 1–4, and fails on missing fields, categories, duplicate grain keys, inconsistent relationships, or silent row loss.
- Added `data/reference/bbsr_settlement_types_2025.csv`, `data/reference/bbsr_source_manifest.json`, `data/profiles/bbsr_reference_profile.json`, and `reports/batch10_bbsr_reference_validation.md`; the deterministic derived reference contains 400 Kreis rows and 362 Kreisregion keys.
- Documented the Hanau vintage mismatch, separate Trier type 1/type 3 rows, Berlin/Hamburg/Bremen/Bremerhaven fixtures, 36 multi-district Kreisregion groups, licensing, attribution, and the continued prohibition on direct KBA assignment or shared Trier allocation.
- Updated the source workflow so separately profiled reference workbooks are ignored by the DuckDB rebuild script; no DuckDB object, Crosswalk row, KPI formula/value, dependency, remote, upload, or publication was changed.

## 2026-11-02 — Batch 11

- Added `scripts/11_audit_bbsr_kba_compatibility.py`, a deterministic read-only audit of all 400 KBA FZ 27.15 registration regions against the separate BBSR 2025 four-category Kreis reference.
- Added `reports/batch11_bbsr_kba_compatibility.md` and the clearly non-operational `reports/batch11_bbsr_kba_compatibility_audit.csv` with source identities, candidate components, evidence types, vintage flags, status recommendations, and charging/BEV coverage.
- Validated strict audit results: 0 `EXACT`, 0 `HOMOGENEOUS_COMPOSITE`, 1 `MIXED` Trier region, 2 `VINTAGE_CONFLICT` Hanau/Main-Kinzig regions, 397 `UNRESOLVED`, and 0 `CONFLICTING`.
- Confirmed full-denominator reconciliation to 211,253 charging points and 2,362,218 July 2026 BEVs without duplicating Trier or summing infrastructure across KBA dates; strict BBSR classification coverage remains zero.
- Updated geographic methodology, data-quality, decisions, roadmap, project status, and this changelog. BBSR-to-KBA integration remains **NOT IMPLEMENTED**; no source CSV, DuckDB object, KPI formula, dependency, remote, upload, or publication was changed.
