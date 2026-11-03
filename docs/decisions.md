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
- Status: Approved and implemented in Batch 10. BBSR-to-KBA compatibility and mixed/unresolved KBA treatment remained pending until the separately approved Batch 13 source-grain charging-only layer.
- Evidence: scripts/10_build_bbsr_reference.py, data/reference/bbsr_settlement_types_2025.csv, data/reference/bbsr_source_manifest.json, and reports/batch10_bbsr_reference_validation.md.

### Batch 11 non-operational BBSR–KBA compatibility audit

- Decision: Keep BBSR-to-KBA compatibility findings in a read-only audit output and do not promote them to the operational Crosswalk or DuckDB.
- Reason: The available evidence contains BBSR administrative/Kreisregion keys, KBA registration-region keys, local BNetzA-to-KBA identity evidence, and source vintages, but no authoritative dated KBA-to-BBSR boundary bridge.
- Consequences: The 400 KBA regions remain visible with explicit audit statuses. The strict result is 0 `EXACT`, 0 `HOMOGENEOUS_COMPOSITE`, 1 `MIXED` for Trier, 2 `VINTAGE_CONFLICT` for Hanau/Main-Kinzig, 397 `UNRESOLVED`, and 0 `CONFLICTING`. Prefix intersections remain diagnostic only.
- Status: Approved for Batch 11 audit scope; operational integration remains **NOT IMPLEMENTED** and requires new owner approval.
- Evidence: scripts/11_audit_bbsr_kba_compatibility.py, reports/batch11_bbsr_kba_compatibility.md, and reports/batch11_bbsr_kba_compatibility_audit.csv.

- Decision: Preserve full KBA denominators and aggregate-before-join treatment while reporting compatibility coverage.
- Reason: Unresolved regions must remain visible, infrastructure is unique at KBA-code grain, and shared Trier stock must not be duplicated or allocated.
- Consequences: Coverage reconciles to 400 KBA regions, 211,253 charging points, and 2,362,218 July BEVs. The result is an audit of classification readiness, not a BBSR KPI.
- Status: Applied in the Batch 11 audit only; no analytical view or KPI formula changed.

### Batch 12 two-path BBSR integration investigation

- Decision: Keep the BNetzA administrative charging path and the KBA registration path separate; do not promote either audit output to the operational Crosswalk or DuckDB.
- Reason: Path A has a usable source-grain identity assessment for 399 rows but still has a 2025/2026 vintage boundary and Hanau gap. Path B has no verified universal, dated KBA-to-administration-to-BBSR bridge and remains strictly unverified for all 400 KBA regions.
- Consequences: Path A is **CONDITIONAL GO** only for a separately labelled, charging-only descriptive enrichment at BNetzA source geography. Path B is **NO-GO** for production BBSR assignment or BBSR-based BEV ratios. Hanau remains unresolved in Path A, Main-Kinzig remains conditional, and KBA `07211` remains mixed with no Trier stock allocation.
- Status: Approved and completed within the Batch 12 read-only investigation scope; any future implementation requires a new owner decision.
- Evidence: [`reports/batch12_bbsr_integration_paths.md`](../reports/batch12_bbsr_integration_paths.md), [`scripts/12_audit_bbsr_integration_paths.py`](../scripts/12_audit_bbsr_integration_paths.py), and the non-operational CSV output.

- Decision: Preserve full denominators and source dates for both Batch 12 paths.
- Reason: Coverage must not be increased by dropping unresolved source districts, assigning a prefix candidate as a code-system bridge, duplicating KBA infrastructure across stock dates, or allocating shared Trier stock.
- Consequences: Path A reports 399 verified rows covering 117,077 equipment records and 210,262 points; Path B reports 0 strict verified regions, points, or July BEVs and retains 397 unresolved regions plus the mixed/vintage exceptions.
- Status: Applied in the Batch 12 audit only; no KPI definition or analytical value changed.

### Batch 13 BBSR charging-only analytics deployment

- Decision: Deploy a separate, versioned BNetzA-to-BBSR bridge and charging-only analytics layer at the original BNetzA state/district grain.
- Reason: Batch 12 Path A independently supports 399 source-grain identities, while Main-Kinzig has a boundary-vintage condition and Hanau is absent from the BBSR 2025 reference. Charging-only analysis does not require a KBA vehicle-stock denominator.
- Consequences: `reference.bnetza_bbsr_district_bridge_2025` has 401 rows; `analytics.charging_by_bbsr_district_2025` has 401 rows; `analytics.charging_by_bbsr_type_2025` has four categories plus `UNCLASSIFIED`. Main-Kinzig and Hanau remain unclassified for category KPIs.
- Controls: Do not modify the KBA Crosswalk, assign BBSR to KBA registration regions, join BEV/PHEV stock, or allocate Trier stock. Keep BNetzA/BBSR dates, status, evidence, and unclassified rows visible.
- Status: Approved and implemented locally after a verified ignored backup, transaction validation, independent read-only checks, and repeat execution.
- Evidence: [`sql/13_bbsr_charging_layer.sql`](../sql/13_bbsr_charging_layer.sql), [`scripts/13_deploy_bbsr_charging_layer.py`](../scripts/13_deploy_bbsr_charging_layer.py), bridge CSV/manifest, and [`reports/batch13_bbsr_charging_deployment.md`](../reports/batch13_bbsr_charging_deployment.md).

### Batch 13.1 owner-approved 2026 BBSR-like scenario

- Decision: Add a separate, versioned owner-override reference and charging-only scenario for Hanau `06415` → category 1 and Main-Kinzig-Kreis `06435` → category 2.
- Reason: The owner approved an analytical scenario for the 2026 boundary context while requiring the official BBSR 2025 baseline to remain unchanged and Hanau's category 1 to remain explicitly non-official.
- Controls: Use the actual BNetzA source identity and existing Crosswalk `kba_district_code` as an identifier only. Set `classification_method` to `OWNER_APPROVED_SCENARIO` for Hanau and `HISTORICAL_BBSR_CARRY_FORWARD` for Main-Kinzig. Keep `official_bbsr_verification = false` for both; expose scenario version, source vintage, boundary vintage, caveat, provenance, evidence URLs, and audit hash.
- Consequences: `reference.bnetza_bbsr_owner_override_2026` has exactly two rows; the scenario district view has 401 rows; the scenario type view has four rows with zero unclassified districts. The official five-row `analytics.charging_by_bbsr_type_2025` summary remains available and unchanged. National charging totals remain 117,662 equipment, 211,253 points, and 9,215.4173 MW.
- Evidence: [`data/reference/bnetza_bbsr_owner_override_2026.csv`](../data/reference/bnetza_bbsr_owner_override_2026.csv), [`sql/13_1_bbsr_scenario.sql`](../sql/13_1_bbsr_scenario.sql), [`scripts/13_1_deploy_bbsr_scenario.py`](../scripts/13_1_deploy_bbsr_scenario.py), and [`reports/batch13_1_bbsr_scenario_classification.md`](../reports/batch13_1_bbsr_scenario_classification.md).

### Batch 13.2 historical BBSR boundary harmonization

- Decision: Add a separate, versioned historical BBSR target-unit layer after independently auditing the BBSR 68-versus-67 discrepancy; preserve the official Batch 13 bridge/views and the Batch 13.1 owner scenario unchanged.
- Reason: Strict anti-joins identify an existing Kassel city/county join error plus the expected Hanau vintage difference. The official Hessian boundary law supports reconstructing the pre-2026 Main-Kinzig target as Hanau plus the remaining Main-Kinzig component.
- Controls: Use raw BBSR `SLK2025` to distinguish city and county, correct Kassel only in the new layer, aggregate Hanau and remaining Main-Kinzig to historical BBSR `06435000` type 2, retain both source dates, and do not claim an official 2026 Hanau BBSR type. Do not use KBA codes as BBSR assignment proof, join vehicle stock, allocate Trier stock, or change the Crosswalk.
- Consequences: 401 BNetzA source components map to 400 historical BBSR target units with type counts 68 / 131 / 98 / 103. National charging totals remain 117,662 equipment, 211,253 points, and 9,215.4173 MW; the Hanau/Main-Kinzig target is 585 equipment and 991 points.
- Status: Approved and implemented locally after a verified ignored backup, transactional deployment, protected-object snapshots, read-only validation, and repeat-safe execution.
- Evidence: [`sql/13_2_hanau_geographic_harmonization.sql`](../sql/13_2_hanau_geographic_harmonization.sql), [`scripts/13_2_deploy_hanau_geographic_harmonization.py`](../scripts/13_2_deploy_hanau_geographic_harmonization.py), versioned reference CSV/manifest, and [`reports/batch13_2_hanau_geographic_harmonization.md`](../reports/batch13_2_hanau_geographic_harmonization.md).

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
- Keep the deployed source-aware `analytics.charging_by_state` definition before any multi-snapshot loading.
- Approve a reusable point-power parser/view.
- Keep the Batch 13 source-grain BBSR category KPIs descriptive; approve any future BBSR-to-KBA bridge or Tableau use separately.
- Decide whether a post-2026 BBSR reference is required before any Hanau/Main-Kinzig category comparison; do not inherit Main-Kinzig type 2 for Hanau without authoritative evidence.
- Decide whether to commission a product-specific, dated KBA-to-AGS/ARS/KRS bridge investigation; do not approve a universal five-digit prefix rule.
- Reaffirm that KBA `07211` remains the combined Trier/Trier-Saarburg display region and that its 7,869 July BEVs are not allocated between BBSR rows.
- Decide whether historical KBA snapshots are required before publishing pre-2026 or cross-vintage regional trends.
- Approve any new source download, future KBA-level DuckDB object, or Tableau enrichment separately; no KBA–BBSR integration is authorized by Batch 13.
- Complete source-data redistribution and final public-extract licensing review.

## Batch 14 decision: use the harmonized layer for descriptive BBSR analysis

- Decision: Use only `analytics.charging_by_bbsr_district_2025_harmonized`
  and its four-category summary as the primary Batch 14 analytical baseline.
- Reason: Batch 13.2 is the validated layer that resolves the historical
  Hanau/Main-Kinzig target and the Kassel city/county identity while preserving
  source-component provenance.
- Controls: Keep BNetzA `2026-09-30` and BBSR `2025-12-31` visible; preserve
  `fast >22 kW`, `>=150 kW`, and `>=350 kW` as nested declared-power measures;
  do not use KBA stock or create a BBSR/KBA ratio.
- Decision: Treat category shares, distributions, weighted/unweighted
  comparisons, and concentration rankings as descriptive. Do not call them
  access, demand, quality, utilization, or causal KPIs.
- Decision: Use a 30-point minimum only as an exploratory stability filter for
  share-based outlier rankings. It is not an official statistical standard.
- Consequence: Batch 14 creates a read-only analyzer, report, and diagnostic
  CSVs only. No DuckDB view, table, mapping, source file, or official KPI
  deployment changes.
- Status: Approved and applied for Batch 14; any Tableau deployment still
  requires separate approval.
