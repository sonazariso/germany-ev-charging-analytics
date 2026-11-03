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
- Batch 10: acquired and validated the latest suitable official BBSR reference, preserved source provenance, and built a separate four-category Kreis CSV without changing DuckDB or the Crosswalk.
- Batch 11: completed a read-only BBSR/KBA compatibility and coverage audit for all 400 KBA regions, with explicit non-operational statuses and no production integration.
- Batch 12: completed a read-only two-path BBSR compatibility investigation, with a conditional charging-only Path A assessment, a no-go Path B assessment, full denominators, and no production integration.
- Batch 13: deployed the approved source-grain BBSR charging-only bridge and category views with 399 verified classifications, two visible unclassified districts, full charging reconciliation, and no KBA stock integration.
- Batch 13.1: deployed the separate owner-approved Hanau/Main-Kinzig analytical scenario with a two-row override reference, 401 classified source districts, zero scenario-unclassified districts, and no change to the official Batch 13 baseline.
- Batch 13.2: audited the BBSR 68-versus-67 discrepancy, corrected the Kassel city/county join only in a new layer, and deployed a historical Hanau/Main-Kinzig BBSR 2025 harmonization with 401 source components, 400 target units, and full national reconciliation.
- Batch 14: completed a read-only statistical analysis of the harmonized BBSR charging layer, including category KPIs, within-unit distributions, weighted/unweighted comparisons, concentration/outlier screens, evidence-labelled interpretations, and future Tableau KPI evaluation. No database objects were changed.
- Batch 15: completed a read-only KBA FZ 27 stock, growth, geography, ownership, worksheet-capability and historical-series analysis with deterministic outputs and explicit national/state/`Sonstige`/400-region scopes.
- Batch 16: completed a read-only 16-state comparison of KBA July 2026 passenger-car stock versus BNetzA September 2026 charging infrastructure, with deterministic reconciliation, cross-source ratios, outlier screens, descriptive correlations and KPI evaluation. No database objects were changed.
- Batch 17: completed a read-only temporal-validity audit of the Batch 16 cross-source KPIs, including commissioning-date quality, published-versus-survivor cohort sensitivity, 16-state ranking/outlier comparison, fixed-denominator vehicle-stock illustration and KPI publication decisions. No database objects were changed.
- Batch 18: completed the source-readiness review, canonical 59-row KPI register, historical-panel feasibility decision, Tableau candidate assessment, concise narrative recommendation and decision register. No database objects, source files, Tableau assets or new datasets were changed.

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
- [x] Acquire and build the versioned BBSR four-category administrative reference in Batch 10; preserve raw source outside Git and keep it separate from KBA classification.
- [x] Audit BBSR/KBA compatibility, Hanau/Main-Kinzig vintage conflict, Trier mixed coverage, Kreisregion relationships, and full-denominator coverage in Batch 11; keep statuses non-operational.
- [x] Evaluate separate BNetzA-to-BBSR and KBA-to-administration-to-BBSR paths in Batch 12; preserve Path A/Path B evidence statuses and keep all outputs non-operational.
- [x] Approve and deploy the separate BNetzA-source-grain charging-only BBSR bridge and category views; preserve mixed/unresolved status, Hanau treatment, and no Trier allocation.
- [x] Deploy the owner-approved 2026 Hanau/Main-Kinzig scenario as a separate, versioned charging-only layer; preserve the official BBSR 2025 five-row baseline and explicit non-official provenance.
- [x] Independently explain the 68-versus-67 discrepancy, document official Hanau boundary evidence, and deploy the historical BBSR 2025 target-unit harmonization without changing Batch 13, Batch 13.1, KBA, or Crosswalk objects.
- [x] Run the Batch 14 read-only harmonized-layer analysis and produce the report plus deterministic type/district diagnostic CSVs.
- [x] Reconcile Batch 14 national totals, source fingerprints, duplicate/orphan checks, category counts, and maximum-per-point power bands.
- [x] Evaluate and recommend a small future Tableau KPI set without deploying views or BBSR/KBA ratios.
- [x] Run Batch 15 read-only KBA FZ 27 stock, growth, geography, ownership, worksheet-capability and historical-series analysis with deterministic CSV/report outputs.
- [x] Reconcile national, 16-state, `Sonstige` and 400 KBA-region passenger-car/BEV/PHEV scopes; preserve Trier `07211` as one shared registration region.
- [x] Document FZ 27.5 owner residuals, FZ 27.16/27.17 alternative grains, national quarterly history, and the exploratory 1,000-BEV percentage-growth threshold.
- [x] Run the Batch 16 state EV stock versus charging alignment analyzer and produce the report plus state, reconciliation and association CSVs.
- [x] Reconcile BNetzA infrastructure totals, KBA national/16-state/`Sonstige`/400-region totals, exact 16-state joins, source fingerprints, power bands, statuses, safe denominators and unchanged DuckDB bytes.
- [x] Document the 16-state benchmark, separate published-national benchmark, both snapshot dates, outliers, large-state sensitivity and non-causal interpretation safeguards.
- [x] Run the Batch 17 temporal-validity analyzer with the actual equipment commissioning-date field and produce deterministic cohort, state-sensitivity, KPI-decision and vehicle-stock-sensitivity outputs.
- [x] Reconcile published September infrastructure, the inclusive July cutoff cohort, the post-cutoff complement, all four point-power bands, equipment statuses and KBA January/April/July denominator scopes.
- [x] Document the distinction between published cross-snapshot comparison, retrospective September-survivor cohort and unavailable true historical infrastructure snapshots.
- [x] Decide that BEVs per point is secondary `CONTEXT_ONLY`, power-normalized/share/ranking/correlation measures are `EXPLORATORY_SENSITIVITY`, and adequacy/shortage/surplus is `NOT_SUPPORTED`.
- [ ] Approve a dated BBSR/KBA compatibility bridge before any KBA-level BBSR classification or vehicle-stock ratio.
- [ ] Decide whether a post-2026 BBSR vintage, a product-specific KBA bridge, historical KBA snapshots, or future Tableau work is required; no universal prefix rule or Trier allocation is approved.
- [x] Review Batch 15 findings and complete the Batch 16 state-level denominator/date review before any Tableau implementation.
- [ ] Approve whether a contemporaneous infrastructure panel or product-specific geographic bridge is needed for future cross-source trends.
- [ ] Prepare compact Tableau extracts and source-date metadata.
- [ ] Develop a Germany-wide overview and selected drill-down dashboard.
- [ ] Complete code, dependency, data, licensing, and screenshot review.
- [ ] Obtain explicit user approval for any remote or GitHub publication.

## Batch 18 readiness boundary

- [x] Finalize the canonical publication statuses and machine-readable KPI readiness register.
- [x] Separate headline-ready, date-labelled, context-only, exploratory and unsupported measures.
- [x] Confirm the supported state, KBA registration-region, BNetzA source-grain and historical BBSR charging-only geographies.
- [x] Decide that genuine historical infrastructure-panel development is `BLOCKED` with the current single BNetzA snapshot.
- [x] Identify Tableau-ready source outputs, grain relationships, dates and join risks without creating Tableau assets.
- [x] Recommend a question-led Tableau narrative while keeping dashboard implementation owner-approval gated.
- [ ] Obtain explicit owner approval before implementing any Batch 19 extract or dashboard work.

## Batch 19 completion

- [x] Prepare deterministic national/state BNetzA charging extracts with
  source date and separate equipment/point measures.
- [x] Prepare charging-only historical BBSR district/type extracts from the
  Batch 13.2 401-to-400 harmonized layer.
- [x] Prepare KBA state and registration-region stock extracts for the three
  validated 2026 dates, plus the validated national history.
- [x] Reuse and validate the Batch 16 state comparison and Batch 17 temporal
  sensitivity calculations without changing their formulas or statuses.
- [x] Publish export contracts, manifest, checksums and measured validation
  report; verify byte-identical second execution and source/database
  immutability.

Batch 19 did not create a historical infrastructure panel, add a KBA-to-BBSR
vehicle join, download new data, build Tableau assets or publish remotely.

## Batch 20 completion

- [x] Inventory the nine Batch 19 exports using manifest filenames, actual
  columns, data types and measured row counts.
- [x] Design separate logical Fact/Dimension models for charging, historical
  BBSR charging, KBA stock, state comparison and temporal sensitivity.
- [x] Evaluate and reject the initial multi-fact relationship model in favor of
  separate subject data sources.
- [x] Document relationship keys, cardinality assumptions, valid/invalid filter
  paths, date roles, geographic exceptions and duplicate-measure safeguards.
- [x] Map all 59 Batch 18 KPI IDs to facts, dimensions, formulas, calculation
  locations, filters, dates, risks and readiness.
- [x] Run read-only key, relationship, reconciliation, manifest, fingerprint,
  documentation and DuckDB immutability checks.
- [x] Update the English design documentation and the private Persian
  reference outside Git.

Batch 20 did not create physical Fact/Dimension tables, Tableau workbooks or
extracts, schema changes, source changes, new datasets, or a KBA-to-BBSR
vehicle bridge.

## Next decision-gated stage

Batch 21 has implemented the separate Tableau subject-source preparation and
quality gates from the existing exports. The remaining handoff is manual
Tableau Desktop authoring of the two dashboards, official 16-state map
recognition, screenshot checks, owner review and saving a verified local
workbook. Keep physical marts, historical infrastructure, KBA-to-BBSR vehicle
integration, adequacy interpretation and remote publication outside scope
until their prerequisites and permissions are separately approved.

## Batch 21 completion

- [x] Validate the actual Batch 19 manifest, all nine export headers/rows/
  checksums and all manifest-listed source/reference fingerprints.
- [x] Reconcile national equipment, points, nested power thresholds, nominal
  MW, national KBA July stock, 16-state KBA July stock, and the `Sonstige`
  distinction.
- [x] Create deterministic four-band power-mix and equipment-status CSVs with
  source documentation and hashes.
- [x] Write the two-page Tableau implementation specification with field
  mappings, aggregations, calculations, colors, layout and manual steps.
- [x] Confirm read-only DuckDB access and unchanged database/source/export
  fingerprints.
- [ ] Build and open the actual Tableau workbook in Tableau Desktop.
- [ ] Verify all 16 official map geometries and capture final screenshots.
- [ ] Review licensing and obtain separate approval before any publication.
