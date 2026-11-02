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

## Pending proposals

- Replace or supplement the provisional crosswalk with an authoritative administrative reference.
- Approve permanent reference and geographic aggregate objects in DuckDB.
- Resolve the source_id omission in analytics.charging_by_state before multi-snapshot loading.
- Approve a reusable point-power parser/view.
- Decide whether BBSR settlement typology adds analytical value.
- Complete source-data redistribution and final public-extract licensing review.
