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
- Batch 07: authoritative evidence review of the 24 provisional crosswalk rows.
- Batch 08: independent code-system and boundary verification for the 22 aliases, Trier, Hanau, and the 400-code model.

These are project milestones supported by local artifacts. They are not historical Git commits unless a local commit is explicitly identified in the handoff.

## Batch 06 completion

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

## Batch 07 and Batch 08 completion

- [x] Review every provisional crosswalk row against dated administrative and KBA evidence.
- [x] Distinguish row-level five-digit key evidence from universal AGS/ARS equivalence.
- [x] Verify Hanau's 2026 administrative separation in BNetzA and all three local KBA FZ 27.15 snapshots.
- [x] Verify the combined Trier registration-region stock and aggregate-before-join treatment.
- [x] Re-run structural geographic validations without changing source data or operational statuses.
- [x] Document unresolved code-system and historical-vintage gaps for owner review.

## Planned next stages

- [ ] Decision on the final treatment and display of shared Trier/Trier-Saarburg registration code 07211.
- [ ] Decide whether a historical boundary-vintage note and additional pre-2026 KBA snapshots are required before older or cross-product regional trends.
- [ ] Reconcile KBA district versus state-level Sonstige and national-total differences.
- [ ] Decide whether maximum-per-point power parsing becomes a reusable view or core field.
- [x] Assess BBSR four-category suitability, boundary vintages, and licensing in Batch 09; no implementation or complete INKAR download.
- [ ] Approve a dated BBSR/KBA compatibility bridge, mixed/unresolved status, Hanau treatment, and any future BBSR reference model before implementation.
- [ ] Further KPI validation and dashboard-specific denominator review.
- [ ] Prepare compact Tableau extracts and source-date metadata.
- [ ] Develop a Germany-wide overview and selected drill-down dashboard.
- [ ] Complete code, dependency, data, licensing, and screenshot review.
- [ ] Obtain explicit user approval for any remote or GitHub publication.
