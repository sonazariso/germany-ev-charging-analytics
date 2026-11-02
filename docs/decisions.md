# Decision log

This log separates approved decisions, implementation details, and pending proposals. A local document entry is not an official data-source decision.

## Approved decisions

### Python + DuckDB + Tableau Public stack

- Decision: Use Python for ingestion/profiling, DuckDB for local analytical storage, and Tableau Public as the planned reporting layer.
- Reason: The stack is reproducible on the local macOS workflow and supports a compact dashboard extract without a continuously running database.
- Alternatives, if known: Pandas-first processing, a server database, or a cloud warehouse.
- Consequences: The repository must document Python commands, DuckDB read-only analysis, and Tableau extract constraints.
- Status: Approved and implemented as the current stack; Tableau is planned, not complete.
- Evidence: README, requirements-phase03.txt, current scripts, and tableau/README.md.

### Full Germany coverage

- Decision: Cover all 16 federal states without arbitrary state exclusions or samples.
- Reason: State and district comparisons require national coverage.
- Consequences: Source row counts and KBA alternative grains must be reconciled rather than reduced.
- Status: Approved and implemented for the current snapshots.
- Evidence: Source profiles and phase validation reports.

### Complete raw-data preservation

- Decision: Preserve original workbooks locally and retain all populated source worksheet rows in DuckDB raw.
- Reason: Reproducibility and auditability require source detail, including footnotes and alternate KBA structures.
- Consequences: Raw data, the DuckDB database, and large exports are excluded from Git.
- Status: Approved and implemented.
- Evidence: scripts/01_download.py, scripts/02_profile_xlsx.py, scripts/03_build_duckdb.py.

### Equipment-versus-point granularity

- Decision: Keep charging equipment and charging-point slots as separate analytical grains.
- Reason: One BNetzA equipment record can represent several points; row count is not point count.
- Consequences: Equipment-level nominal power must not be multiplied by a point join; point-level power is parsed inside each point row.
- Status: Approved and implemented.
- Evidence: core table definitions and 117,662-to-211,253 reconciliation.

### No preemptive RAM or thread limits in the current workflow

- Decision: Do not introduce memory, thread, or disk limits in Batch 04 or the current read-only analysis workflow.
- Reason: The project owner explicitly prohibited adding such limits, and the current build uses DuckDB defaults.
- Consequences: sql/duckdb_initial_settings.sql remains prospective documentation and is not applied by Batch 04.
- Status: Approved boundary; prospective settings require a future decision.
- Evidence: Batch 04 scope and current build behavior.

### Geographic crosswalk approach

- Decision: Use a versioned CSV crosswalk with state-aware and administrative-type-aware matching, explicit aliases, verification status, notes, and evidence URL.
- Reason: BNetzA and KBA district labels differ and name-only matching is unsafe in collision cases.
- Consequences: The crosswalk remains auditable and provisional rows cannot be silently hidden.
- Status: Approved and implemented locally; authoritative review remains pending.
- Evidence: data/reference/bnetza_kba_district_crosswalk_2026.csv and Batch 03 report.

### Trier aggregate-before-join rule

- Decision: Aggregate BNetzA charging metrics by KBA code before joining KBA stock.
- Reason: Trier city and Trier-Saarburg both map to KBA registration code 07211.
- Consequences: A raw source-row join is prohibited for combined vehicle/infrastructure KPIs.
- Status: Approved and implemented in the crosswalk validation logic; permanent DuckDB integration is pending.
- Evidence: Batch 03 aggregate-before-join check.

### Batch 09 owner-approved geographic controls

- Decision: Keep the 22 identity- and code-supported aliases operationally provisional until sufficient code-system equivalence evidence exists.
- Reason: Row-level identity evidence does not establish a universal KBA registration-code = Destatis AGS/ARS relationship.
- Consequences: The 22 aliases remain visibly provisional in the Crosswalk and deployed reference table; no status promotion occurs in Batch 09.
- Status: Approved owner control; documented and unchanged.

- Decision: Use the combined dashboard label **Trier / Trier-Saarburg (gemeinsamer Zulassungsbezirk)** for the shared KBA registration region.
- Reason: KBA FZ 27.15 reports one combined registration row while Destatis and BBSR retain separate administrative rows.
- Consequences: The label must not imply that the KBA stock belongs to either administrative unit alone.
- Status: Approved owner control; display guidance only, with no current view change.

- Decision: Never allocate the shared Trier KBA vehicle stock between Trier city and Trier-Saarburg without a separately approved, defensible allocation method.
- Reason: The available sources provide combined registration-region stock but no validated city/county allocation.
- Consequences: Aggregate charging to KBA code `07211`, join stock once, and retain a mixed/unresolved treatment for future BBSR category rollups.
- Status: Approved owner control; implemented in the existing aggregate-before-join rule.

- Decision: Document geographic boundary-vintage limitations for historical and cross-source comparisons.
- Reason: BNetzA, KBA, Destatis, and BBSR use dated products and do not necessarily share the same effective boundary vintage.
- Consequences: Every future geographic comparison must retain source dates, classification vintage, and incompatibility flags; historical trends require an explicit compatibility check.
- Status: Approved owner control; Batch 09 adds the BBSR/Hanau vintage note.

### Batch 09 research-only scope

- Decision: Conduct the BBSR feasibility assessment as research and documentation only.
- Reason: The owner did not authorize BBSR ingestion, database modification, Crosswalk changes, or KPI changes in this batch.
- Consequences: The official BBSR reference workbook was inspected in temporary storage only; no BBSR object or analytical value was added to the project.
- Status: Approved and completed in Batch 09.

### Batch 10 separate BBSR reference scope

- Decision: Acquire the latest suitable official BBSR reference workbook and build a versioned local four-category Kreis reference outside DuckDB and the existing BNetzA-to-KBA Crosswalk.
- Reason: The owner approved a reproducible BBSR reference while explicitly excluding complete INKAR, KBA classification, shared Trier allocation, KPI changes, and database changes.
- Consequences: The 2025 geographic stand is preserved at one row per BBSR KRS2025 administrative Kreis row, with Kreisregion relationships, source version, reference date, source lineage, and checksums visible. The raw workbook remains ignored by Git.
- Status: Approved and implemented in Batch 10. BBSR-to-KBA compatibility, mixed/unresolved treatment, and category-level KPI use remain pending.
- Evidence: scripts/10_build_bbsr_reference.py, data/reference/bbsr_settlement_types_2025.csv, data/reference/bbsr_source_manifest.json, and reports/batch10_bbsr_reference_validation.md.

### Batch 06 permanent geographic layer deployment

- Decision: Deploy the approved geographic reference table and two snapshot-specific analytics views to the existing DuckDB file, and correct `analytics.charging_by_state` to use `(source_id, excel_row)` for point aggregation and joins.
- Reason: The Batch 05 read-only validation established the required grains, power-band parser, mapping flags, and aggregate-before-join rule; Batch 06 approval authorized the permanent local implementation.
- Consequences: The reference table preserves all 401 CSV rows and 24 provisional mappings; charging metrics are unique at 400 KBA codes; combined rows retain the BNetzA date and actual KBA stock date; infrastructure values repeat across KBA dates and must not be summed.
- Backup and rollback: Create and independently validate a timestamped ignored backup before database modification; apply the deployment in one transaction; use the verified backup or an approved object-level rollback if restoration is needed.
- Status: Approved and implemented locally in Batch 06. No source workbook or Crosswalk CSV was modified.
- Evidence: `sql/06_geographic_layer.sql`, `scripts/06_deploy_geographic_layer.py`, `scripts/06_validate_geographic_layer.py`, and `reports/batch06_geographic_deployment.md`.

### No premature causal conclusions

- Decision: Treat vehicle-stock growth and infrastructure mix as descriptive comparisons, not causal evidence.
- Reason: The data are snapshots with different dates, incomplete published infrastructure coverage, and no demand or utilization measures.
- Consequences: Combined KPIs are provisional and findings avoid causal language.
- Status: Approved and applied in the KPI catalog and findings.

### Local-first Git workflow

- Decision: Initialize and use Git locally before any publication.
- Reason: Review and history should be established without exposing raw data or incomplete artifacts.
- Consequences: No remote is configured and no push or upload occurs in Batch 04.
- Status: Approved and implemented.

### No GitHub publication until project completion

- Decision: Do not create, modify, or push to a GitHub repository until final review and explicit approval.
- Reason: Licensing, raw-data exclusion, dashboard, and quality checks are incomplete.
- Consequences: The current baseline is local-only.
- Status: Approved and active.

## Implementation details, not new approvals

- DuckDB schemas are raw, core, and analytics.
- The current source-local equipment key is source_id plus Excel row.
- The read-only Batch Analysis Runner accepts named SELECT or WITH queries and can read the crosswalk CSV as a query-scoped relation.
- Current generated reports retain source reference dates and validation results.
- Batch 07 evidence review: 22 of the 24 provisional mappings are independently supported at the row/entity level; the two Trier rows are partially supported as one KBA registration region; no row identity is unresolved. This is an evidence classification, not approval to change operational statuses. Destatis AGS/ARS keys and KBA registration-region keys remain distinct concepts.
- Batch 07 confirmed that the July 2026 KBA FZ 27.15 value of 7,869 BEVs belongs to the combined `07211 TRIER-SAARBURG` row. A common registration authority does not justify splitting that stock between the two administrative units.
- Batch 08 refined the evidence classification: all 22 aliases have direct row-level five-digit key evidence, but no universal KBA-to-AGS/ARS equivalence was found; the two Trier rows remain entity-level combined-region evidence. All 24 operational statuses remain provisional.
- Batch 08 confirmed that the 2026-09-30 BNetzA source and all three local 2026 FZ 27.15 snapshots represent Hanau (`06415`) and Main-Kinzig-Kreis (`06435`) separately. The current 400-code model is defensible as a KBA registration-region model, while historical boundary compatibility remains unmeasured.

## Pending proposals

- Approve whether the 22 row/entity-supported aliases may move out of the operational provisional status; retain the two Trier rows as a combined KBA registration region unless direct allocation evidence is found.
- Replace or supplement the provisional crosswalk with an authoritative KBA-to-administrative reference that explicitly identifies the code system and effective date.
- Decide whether a dated historical-boundary compatibility note and additional pre-2026 KBA snapshots are required before publishing any historical or cross-product regional trend.
- Approve permanent reference and geographic aggregate objects in DuckDB.
- Resolve the source_id omission in analytics.charging_by_state before multi-snapshot loading.
- Approve a reusable point-power parser/view.
- Approve or defer the dated BBSR/KBA compatibility bridge and any BBSR category-level KPI or Tableau use; the separate BBSR reference itself is implemented.
- Complete source-data redistribution and final public-extract licensing review.
