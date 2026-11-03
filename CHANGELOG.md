# Changelog

This changelog records project milestones and local repository changes. Historical Batch 01–03 entries describe work evidenced by local reports; they do not imply historical Git commits or inferred dates.

## 2026-11-03 — Batch 21

- Added `scripts/21_prepare_tableau_overview.py`, a deterministic read-only preparation and validation script for the approved `01 — National Summary` and `02 — Geographic View` dashboards.
- Added the mutually exclusive four-band presentation contract at `data/exports/tableau/preparation/power_band_distribution_2026_09_30.csv` and the published equipment-status contract at `data/exports/tableau/preparation/equipment_status_breakdown_2026_09_30.csv`.
- Added `docs/tableau-executive-overview.md` with exact source files, worksheet definitions, fields, aggregations, calculations, design tokens, dashboard geometry, geographic safeguards and manual Tableau Desktop steps.
- Added `reports/batch21_tableau_overview_validation.md` with `DATA_PREPARATION_PASS`, source/export checksums, national and 16-state reconciliations, actual 33-row KBA history validation, derived hashes and screenshot/workbook status.
- Confirmed 117,662 equipment, 211,253 points, all four mutually exclusive power bands, 9,215.4173 MW, national July BEV/PHEV 2,365,047/1,226,863, sixteen-state July BEV/PHEV 2,362,218/1,225,241, and the 2,829 `Sonstige` BEV distinction.
- Confirmed no Batch 19 CSV, DuckDB, raw source, reference crosswalk, backup, remote, upload or publication changed. Tableau Desktop is installed, but no approved authoring bridge was available; no `.twb`, `.twbx` or screenshot is claimed.
- Updated the README, project status, architecture, Tableau semantic/relationship documents, KPI catalog, data dictionary, decisions, roadmap, reproducibility guide, data-source notes, Tableau handoff README and the private Persian reference outside Git.

## 2026-11-03 — Batch 20

- Added the design-only Tableau semantic model specification in `docs/tableau-semantic-model.md`, with separate subject models, date roles, measure behavior, alternative-model evaluation, and future implementation prerequisites.
- Added `docs/tableau-fact-dimension-catalog.md` and `docs/tableau-relationship-design.md`, including logical fact/dimension grains, actual source keys and fields, relationship contracts, cardinality assumptions, filter paths, and Mermaid diagrams.
- Added `reports/batch20_kpi_model_mapping.csv` with exactly one mapping row for each of the 59 Batch 18 KPI IDs, preserving publication status and documenting facts, dimensions, formula, calculation location, filters, dates, risks, and readiness.
- Added `reports/batch20_semantic_model_validation.md` and `reports/batch20_architecture_decision.md` with measured export/key/reconciliation/fingerprint validation and the recommendation to use separate validated Tableau data sources initially.
- Updated the README, architecture, data dictionary, KPI catalog, decision log, roadmap, reproducibility guide, and project status. Updated the private Persian reference outside the repository with the Batch 20 fact/dimension and relationship guidance.
- Confirmed no DuckDB object/schema/data, Batch 19 CSV, raw source, Crosswalk, Tableau asset, dependency, dataset, remote, or upload changed. No private Persian file is tracked or staged.

## 2026-11-03 — Batch 19

- Added `scripts/19_prepare_tableau_data.py`, a deterministic read-only exporter that inspects required DuckDB objects, protects approved source fingerprints, keeps equipment and point grains separate, validates expected grains, and fails on unsafe or missing inputs.
- Added nine Tableau-ready CSVs under `data/exports/tableau/`: national/state charging, historical BBSR district/type charging, KBA state/registration-region stock, the validated state comparison, temporal sensitivity, and the optional 33-observation national KBA history.
- Added `data/exports/tableau/export_manifest.json`, `reports/batch19_tableau_export_contracts.md`, and `reports/batch19_tableau_data_validation.md` with row grains, keys, columns, dates, checksums, publication statuses, relationship rules, measured reconciliation and limitations.
- Validated 117,662 equipment records, 211,253 point slots, all power bands, 9,215.4173 MW, 16 states, 400 BBSR historical units from 401 source components, 48 KBA state/date rows, 1,200 KBA registration-region/date rows, 16 temporal rows and 33 national-history rows.
- Preserved Hanau/Main-Kinzig historical consolidation, corrected Kassel city category, separate Trier charging components, and the no-allocation rule for KBA `07211`. No KBA stock was joined to BBSR.
- Confirmed the DuckDB SHA-256 remained `5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3`, all approved input fingerprints matched, and the second export execution was byte-identical. No dependency, dataset, DuckDB object, source workbook, reference table, remote, upload, Tableau asset or publication changed.
- Updated the English documentation and private Persian KPI catalog outside Git. Existing canonical KPI readiness statuses remain unchanged.

## 2026-11-03 — Batch 18

- Added `reports/batch18_analytics_readiness_review.md`, `reports/batch18_kpi_readiness_register.csv`, `reports/batch18_historical_data_feasibility.md`, `reports/batch18_tableau_analysis_candidates.md`, and `reports/batch18_readiness_decisions.md`.
- Consolidated the validated Batches 01–17 evidence into a deterministic 59-row KPI readiness register with `HEADLINE_READY`, `HEADLINE_READY_WITH_DATES`, `CONTEXT_ONLY`, `EXPLORATORY`, and `NOT_SUPPORTED` statuses.
- Preserved the distinction between equipment records, populated charging-point slots, declared maximum connector-power classes, KBA registered stock, BBSR historical target geography, and the published-register coverage limitation.
- Decided that BEVs per registered charging point is `CONTEXT_ONLY`, temporal survivor-cohort metrics are `EXPLORATORY`, and adequacy/shortage/surplus, utilization, demand and causal claims are `NOT_SUPPORTED`.
- Decided that genuine historical infrastructure-panel development is `BLOCKED` with the current single BNetzA snapshot; documented the multiple-snapshot, identity, removal, attribute-history and completeness prerequisites without implementing a panel.
- Documented the supported Tableau source grains, state/KBA/BBSR join risks, five-page question-led narrative recommendation, distinctive analytical candidates and deferred work. No Tableau asset or extract was created.
- Updated the README, KPI catalog, data sources, data dictionary, data quality, analysis findings, geographic methodology, decisions, roadmap, reproducibility guide, project status and the private Persian KPI catalog outside Git.
- Verified the required Batch 17 commit `ed0320fc956ad5da733bf933c88dec22dcb7f4c7`, clean initial worktree, absent remote, unchanged source/reference fingerprints, read-only DuckDB access and unchanged database hash. No dependency, dataset, raw source, reference crosswalk or remote publication changed.

## 2026-11-03 — Batch 17

- Added `scripts/17_analyze_temporal_kpi_validity.py`, a deterministic read-only analyzer for temporal compatibility between KBA registered passenger-car stock and the BNetzA September charging register.
- Added `reports/batch17_temporal_kpi_validity.md`, `reports/batch17_equipment_commissioning_cohorts.csv`, `reports/batch17_state_temporal_sensitivity.csv`, `reports/batch17_kpi_publication_decisions.csv`, and `reports/batch17_vehicle_stock_denominator_sensitivity.csv`.
- Audited the actual equipment-level commissioning-date field and preserved raw values: 117,662 nonblank values, 0 parsing failures, 0 future dates, 2,762 equipment and 4,888 point rows after the inclusive 2026-07-01 cutoff, and 80 equipment records exactly on the cutoff.
- Reconciled the full 2026-09-30 publication with the retrospective September-survivor cohort: 117,662 equipment / 211,253 points published versus 114,900 equipment / 206,365 retained survivor points; maximum-per-point bands and all equipment statuses remain visible.
- Documented the 91-day KBA/BNetzA mismatch, the absence of point-level activation dates, state ranking/outlier sensitivity, fixed-September vehicle-stock illustration, unsupported historical interpretations, and chart warning labels. BEVs per point is `CONTEXT_ONLY` secondary context; power/ranking/share/correlation comparisons are `EXPLORATORY_SENSITIVITY`; adequacy/shortage/surplus is `NOT_SUPPORTED`.
- Validated exact KBA January/April/July and July national/16-state/`Sonstige`/400-region scopes, source-aware point integrity, six source fingerprints, unchanged DuckDB bytes, and deterministic outputs. No source workbook, Crosswalk, DuckDB object, dependency, remote, upload, Tableau asset, or publication changed.
- Updated the README, findings, KPI catalog, data quality, data sources, geographic methodology, decision log, roadmap, project status, reproducibility documentation, and the private Persian KPI catalog outside Git.

## 2026-11-03 — Batch 16

- Added `scripts/16_analyze_state_ev_charging_alignment.py`, a deterministic read-only analyzer that pre-aggregates KBA FZ 27.2 July 2026 passenger-car stock and BNetzA September 2026 infrastructure separately at the 16-state grain before joining.
- Added `reports/batch16_state_ev_charging_alignment.md`, `reports/batch16_state_comparison.csv`, `reports/batch16_national_reconciliation.csv`, and `reports/batch16_state_associations.csv` with the complete state KPI comparison, national/16-state/`Sonstige`/400-region reconciliation, outlier tables, descriptive Pearson/Spearman associations, denominator safeguards, KPI evaluation, and source fingerprints.
- Reconciled 117,662 equipment records, 211,253 declared/populated points, 156,155 normal points, 55,098 fast points, 40,950 points >=150 kW, 6,950 points >=350 kW, and 9,215.4173 MW; reconciled July KBA national, 16-state, `Sonstige`, and 400-region passenger-car/BEV/PHEV totals.
- Documented the primary 16-state benchmark of 2,362,218 BEVs / 211,253 registered points = 11.18 BEVs per point and kept the published-national 2,365,047-BEV benchmark separate because it includes 2,829 `Sonstige` BEVs.
- Verified exactly 16 state joins, maximum-per-point power definitions, equipment statuses, safe ratio denominators, unchanged source fingerprints, unchanged DuckDB bytes, and byte-identical second-run outputs. No DuckDB object, raw workbook, geographic Crosswalk, BBSR layer, dependency, remote, upload, Tableau asset, or publication changed.
- Updated the English README, findings, KPI catalog, data-quality, geographic-methodology, decision, roadmap and project-status documentation, plus the private Persian KPI catalog outside Git.

## 2026-11-03 — Batch 15

- Added `scripts/15_analyze_kba_ev_stock.py`, a deterministic read-only analyzer for the three local KBA FZ 27 releases dated 2026-01-01, 2026-04-01, and 2026-07-01.
- Added `reports/batch15_kba_ev_stock_analysis.md` and five diagnostic CSVs covering worksheet capabilities, national trends, federal-state metrics, 400 KBA registration-region metrics, and FZ 27.5 ownership composition.
- Reconciled national, 16-state, `Sonstige`, and 400-region passenger-car/BEV/PHEV totals; confirmed 400 region codes per snapshot and preserved the shared Trier code `07211` without allocation.
- Documented national January–July growth of +16.26% for BEVs and +9.25% for PHEVs, same-grain penetration measures, 23 low-baseline percentage-growth exclusions, ownership residuals, postcode/municipality limitations, and the 33-observation national quarterly history.
- Updated the README, project status, data sources, data dictionary, KPI catalog, data quality, findings, geographic methodology, decision log, roadmap, and reproducibility documentation. Updated the private Persian KPI catalog outside Git.
- No DuckDB object, raw workbook, reference file, Crosswalk, BBSR layer, charging object, dependency, remote, upload, or publication changed.

## 2026-11-03 — Batch 14

- Added `scripts/14_analyze_bbsr_charging_patterns.py`, a deterministic read-only analyzer whose primary source is the Batch 13.2 harmonized BBSR district/type layer.
- Added `reports/batch14_bbsr_charging_analysis.md`, `reports/batch14_bbsr_type_metrics.csv`, and `reports/batch14_bbsr_district_metrics.csv` with category KPIs, distributions, weighted/unweighted comparisons, concentration statistics, outlier screens, evidence labels, KPI evaluation, source fingerprints, and validation results.
- Validated 400 historical BBSR target units from 401 BNetzA source components; reconciled 117,662 equipment rows, 211,253 points, all four power bands, and 9,215.4173 MW of declared equipment nominal power.
- Documented that type 2 has the largest absolute point/fast-point totals while type 4 has the highest within-category fast share; the national weighted fast share is 26.08% versus a 31.25% unweighted unit mean.
- Recommended a small future Tableau set and explicitly excluded BBSR-based BEV-to-charger ratios, accessibility, utilization, and causal interpretations. No DuckDB table/view, raw data, reference, Crosswalk, KBA object, dependency, or source file changed.
- Updated English findings, KPI, data-quality, decision, reproducibility, roadmap, README, and project-status documentation plus the private Persian KPI catalog outside Git. No remote was added and nothing was uploaded or published.

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

## 2026-11-02 — Batch 12

- Added `scripts/12_audit_bbsr_integration_paths.py`, a deterministic read-only investigation of the separate BNetzA administrative-to-BBSR and KBA-to-administration-to-BBSR paths.
- Added `reports/batch12_bbsr_integration_paths.md` and the clearly non-operational `reports/batch12_bbsr_integration_paths_audit.csv`, preserving 401 Path A source districts and 400 Path B KBA regions with dates, candidate identifiers, evidence statuses, and coverage fields.
- Validated Path A as 399 `VERIFIED_COMPATIBLE`, one `CONDITIONAL_VINTAGE` Main-Kinzig-Kreis row, and one `UNRESOLVED` Hanau row; verified rows cover 99.502813% of equipment and 99.530894% of charging points.
- Confirmed Path B remains 0 strict verified regions, points, or July BEVs: 1 `MIXED` Trier region, 2 `VINTAGE_CONFLICT` Hanau/Main-Kinzig rows, 397 `UNRESOLVED`, and 0 `CONFLICTING`.
- Reviewed official Destatis, BBSR, Federal Employment Agency, KBA, Hessen, and Trier documentation; no universal dated KBA-to-AGS/ARS/KRS/BBSR bridge was verified. Path A is **CONDITIONAL GO** only for a separate charging-only descriptive path; Path B is **NO-GO** for production BBSR assignment or BBSR-based BEV ratios.
- Updated geographic methodology, data-quality, decisions, roadmap, project status, and README. No DuckDB object, Crosswalk row, BBSR CSV, KPI definition, dependency, dataset download, remote, upload, or publication was changed.

## 2026-11-02 — Batch 13

- Added `scripts/13_deploy_bbsr_charging_layer.py` and `sql/13_bbsr_charging_layer.sql` for repeat-safe, transaction-based deployment with read-only preflight, verified backup validation, source fingerprints, and existing-KBA integrity checks.
- Added the reproducible `data/reference/bnetza_bbsr_bridge_2025.csv` and deterministic provenance manifest. The bridge keeps one row per BNetzA state/district, preserves string BBSR codes, and records 399 `VERIFIED_COMPATIBLE`, one `CONDITIONAL_VINTAGE` Main-Kinzig-Kreis, and one `UNRESOLVED` Hanau row.
- Deployed `reference.bnetza_bbsr_district_bridge_2025`, `analytics.charging_by_bbsr_district_2025`, and `analytics.charging_by_bbsr_type_2025` without changing the KBA Crosswalk or any existing KBA/state object.
- Implemented charging-only BBSR KPIs with separate equipment/point aggregation, composite source-local keys, maximum-per-point semicolon-token power parsing, explicit unknown-power reporting, all equipment statuses, and a five-group national reconciliation.
- Validated 117,662 equipment rows, 211,253 points, 156,155 normal points, 55,098 fast points, 40,950 points >=150 kW, 6,950 points >=350 kW, and 9,215.4173 MW. `UNCLASSIFIED` contains Hanau and Main-Kinzig: 585 equipment and 991 points.
- Added `reports/batch13_bbsr_charging_deployment.md` and updated the English documentation and private Persian KPI reference. No new dataset, dependency, remote, upload, or publication was added.

## 2026-11-02 — Batch 13.1

- Added the reproducible two-row `data/reference/bnetza_bbsr_owner_override_2026.csv` and deterministic manifest. The rows use the actual BNetzA source identities and existing Crosswalk `kba_district_code` identifiers: Hanau `06415` → category 1 and Main-Kinzig-Kreis `06435` → category 2.
- Added `scripts/13_1_deploy_bbsr_scenario.py` and `sql/13_1_bbsr_scenario.sql` with read-only preflight, lock/WAL checks, timestamped verified backup, transactional deployment, official-object snapshots, independent reconciliation, and repeat-safe execution.
- Deployed only `reference.bnetza_bbsr_owner_override_2026`, `analytics.charging_by_bbsr_district_2026_scenario`, and `analytics.charging_by_bbsr_type_2026_scenario`. The official BBSR 2025 CSV, original bridge, Crosswalk, raw/core data, and Batch 13 baseline views remain unchanged.
- Applied Hanau's category 1 as `OWNER_APPROVED_SCENARIO` and Main-Kinzig's category 2 as `HISTORICAL_BBSR_CARRY_FORWARD`; both remain `official_bbsr_verification = false` and are not labelled `VERIFIED_COMPATIBLE`.
- Reclassified the database-derived 585 equipment records and 991 charging points from the official baseline `UNCLASSIFIED` group into scenario categories 1 and 2. The scenario covers 401 districts with zero unclassified districts and reconciles all national charging totals.
- Added `reports/batch13_1_bbsr_scenario_classification.md` and updated the English documentation plus the private Persian KPI reference outside the Git worktree. No KBA stock integration, Trier allocation, Tableau work, remote, upload, or publication was performed.

## 2026-11-02 — Batch 13.2

- Added the independent strict and semantic bidirectional audit explaining the BBSR 68-versus-67 discrepancy: the preserved Batch 13 bridge maps Kassel city to the county row, while Hanau is the genuine current-versus-2025 vintage difference; Kreis versus Kreisregion does not explain the mismatch.
- Added official Hanau boundary evidence and a documented historical union rule: Hanau and the remaining Main-Kinzig source row aggregate to historical BBSR `06435000` type 2; the layer does not claim an official 2026 Hanau BBSR classification.
- Added the deterministic `data/reference/bnetza_bbsr_historical_harmonization_2025.csv` and manifest, using raw BBSR `SLK2025` to independently preserve city/county form and correcting Kassel city to `06611000` type 1 only in the new layer.
- Added `scripts/13_2_deploy_hanau_geographic_harmonization.py` and `sql/13_2_hanau_geographic_harmonization.sql` with read-only preflight, anti-join checks, lock/WAL checks, verified backup, transactional deployment, protected-object snapshots, national reconciliation, and repeat-safe validation.
- Deployed only the new Batch 13.2 reference table and historical district/type views. The official Batch 13 baseline, Batch 13.1 scenario, Crosswalk, KBA objects, raw/core data, and Trier handling remain unchanged.
- Added `reports/batch13_2_hanau_geographic_harmonization.md` and updated the English documentation plus the private Persian KPI reference outside the Git worktree. No remote, upload, publication, vehicle-stock join, or source workbook modification was performed.
