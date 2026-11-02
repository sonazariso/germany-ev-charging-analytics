# Roadmap

This roadmap distinguishes established work from planned work. A planned item is not presented as complete.

## Established project history

- Source discovery and profiling: manifest-driven retrieval/verification, checksums, full worksheet profiling, and source-preservation rules.
- DuckDB ingestion and validation: raw workbook rows, normalized charging equipment and point tables, KBA state/district/postcode/municipality tables, and initial analytics views.
- Data-quality investigations: equipment-to-point reconciliation, KBA grain and subtotal cautions, connector-power parsing, coordinate review, and the source-aware state-view issue.
- Charging and BEV analytical exploration: point-power thresholds, equipment nominal power, KBA snapshot comparison, state aggregates, and date/coverage caveats.
- Batch 01: live read-only DuckDB baseline validation.
- Batch 02: charging-power and geographic-readiness analysis.
- Batch 03: versioned BNetzA-to-KBA crosswalk and reusable read-only Batch Analysis Runner.
- Batch 04: professional English documentation, project governance files, safe local Git setup, and the local baseline commit.
- Batch 05: read-only pre-integration geographic validation and permanent-layer design.
- Batch 06: verified-backup deployment of the permanent geographic layer and source-aware state-view correction.

These are project milestones supported by local artifacts. They are not historical Git commits unless a local commit is explicitly identified in the handoff.

## Current Batch 06 completion

- [x] Document current architecture and data lineage.
- [x] Document source metadata, checksums, worksheet coverage, and licenses from the manifest and profiles.
- [x] Document actual DuckDB schemas and important fields.
- [x] Create a KPI catalog with formula, denominator, grain, date, status, and limitations.
- [x] Separate verified findings, exploratory results, and open questions.
- [x] Record crosswalk methodology, provisional aliases, and Trier handling.
- [x] Approve and deploy the minimum geographic DuckDB integration design.
- [x] Create and validate a pre-deployment backup before the approved schema change.
- [x] Build and validate permanent geographic reference and aggregate objects.
- [x] Correct and validate the source-aware state view.
- [x] Establish persistent project instructions and tracking files.
- [x] Initialize Git locally without a remote.

## Planned next stages

- [ ] Independent review of every provisional geographic alias.
- [ ] Decision on the final treatment and display of shared Trier/Trier-Saarburg registration code 07211.
- [ ] Reconcile KBA district versus state-level Sonstige and national-total differences.
- [ ] Decide whether maximum-per-point power parsing becomes a reusable view or core field.
- [ ] Assess BBSR suitability, boundary vintages, and licensing; do not download until approved.
- [ ] Further KPI validation and dashboard-specific denominator review.
- [ ] Prepare compact Tableau extracts and source-date metadata.
- [ ] Develop a Germany-wide overview and selected drill-down dashboard.
- [ ] Complete code, dependency, data, licensing, and screenshot review.
- [ ] Obtain explicit user approval for any remote or GitHub publication.
