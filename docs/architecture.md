# Architecture

## Current architecture

The project is a local, file-based analytical workflow. The current DuckDB database is a built artifact under data/analytics and is inspected read-only during analysis. Original workbooks remain under data/raw and are not changed by the ingestion scripts.

~~~mermaid
flowchart LR
    A[Official XLSX sources] --> B[config/sources.json]
    B --> C[scripts/01_download.py]
    C --> D[data/profiles/download_inventory.json]
    C --> E[data/raw]
    E --> F[scripts/02_profile_xlsx.py]
    F --> G[data/profiles/workbook_profiles.json]
    E --> H[scripts/03_inspect_schema.py]
    H --> I[data/profiles/schema_inspection.json]
    E --> J[scripts/03_build_duckdb.py]
    G --> J
    J --> K[(DuckDB raw schema)]
    K --> L[(DuckDB core schema)]
    L --> M[(DuckDB analytics views)]
    L --> N[scripts/04_build_geographic_crosswalk.py]
    N --> O[data/reference/bnetza_kba_district_crosswalk_2026.csv]
    L --> P[scripts/batch_analysis.py]
    O --> P
    M -. planned extract .-> Q[Tableau Public]
    O -. planned integration .-> R[Geographic analytics layer]
    L -. planned .-> R
~~~

The dashed components are not complete. No Tableau workbook or permanent geographic DuckDB object exists in the current project. Batch 05 validates the proposed pre-integration design in [geographic-layer-design.md](geographic-layer-design.md); that document is design-only and does not represent deployed DuckDB objects.

## Source and ingestion stages

1. config/sources.json records the four official source IDs, reference dates, paths, direct URLs, source pages, and declared reuse licenses.
2. scripts/01_download.py downloads or verifies the original XLSX files and writes byte counts and SHA-256 hashes to data/profiles/download_inventory.json.
3. scripts/02_profile_xlsx.py streams the XML inside each workbook and counts every physical and populated row across every worksheet without rewriting the source.
4. scripts/03_inspect_schema.py previews early worksheet rows to identify title, header, and data positions.
5. scripts/03_build_duckdb.py inserts all populated raw worksheet rows, then creates the initial core tables and analytics views.
6. scripts/04_build_geographic_crosswalk.py opens DuckDB read-only and writes a versioned CSV crosswalk plus a validation report.
7. scripts/batch_analysis.py runs named SELECT or WITH queries on one read-only DuckDB connection and writes one structured Markdown report.

## DuckDB schemas

### raw

The raw schema preserves the source row structure:

- raw.bnetza_rows contains source_id, excel_row, and col_a through col_au for every populated BNetzA worksheet row, including metadata rows.
- raw.kba_rows contains source_id, reference_date, sheet_name, excel_row, and col_a through col_o for every populated row across all 20 worksheets in each KBA workbook.

Raw KBA rows retain title, header, footnote, subtotal, and alternate-breakdown content. They are not a vehicle fact table.

### core

The current core schema contains:

- core.charging_equipment: one row per BNetzA equipment record after the source header region.
- core.charging_point: one row per populated charging-point slot represented by the six repeated point groups in the BNetzA sheet.
- core.kba_state_fuel_stock: selected state-level FZ 27.2 fuel-category values across the three reference dates.
- core.kba_district_ev_stock: one row per KBA district code and reference date from FZ 27.15.
- core.kba_postcode_ev_stock: postcode-level BEV/PHEV values from FZ 27.16.
- core.kba_municipality_ev_stock: municipality-level commercial/private BEV/PHEV values from FZ 27.17.

### analytics

The current views are:

- analytics.charging_point_public: public charging-point detail joined to its equipment attributes; the source Public Key is not exposed.
- analytics.charging_by_state: state-level equipment and populated-point counts.
- analytics.kba_national_quarterly_stock: de-duplicated national historical rows from FZ 27.9.

The state view has a known source-aware join issue: its point-count subquery groups only by Excel row and the join omits source_id. It was not modified in Batch 04 or Batch 05. The issue must be resolved or explicitly constrained before multiple BNetzA snapshots are loaded together.

## Equipment-to-point relationship

The safe source-local relationship is:

- Equipment row identity: (source_id, excel_row).
- Point row relationship: (source_id, equipment_excel_row).
- Point slot identity for validation: (source_id, equipment_excel_row, point_number).

equipment_id is retained as the source identifier, but the build and validation logic uses source_id plus Excel row to avoid accidental collisions across source files. The current snapshot has 117,662 equipment rows and 211,253 point rows. Declared point count and populated point slots reconcile exactly in the current snapshot.

connector_types and connector_power_raw are point-level text fields. A semicolon-separated power string remains within one point row; it is not exploded into multiple points or connectors.

## Geographic crosswalk and planned reporting layer

The current crosswalk is a curated CSV reference with 401 BNetzA state/district rows and 400 distinct KBA district codes. It is not a DuckDB table or view. It includes mapping method, verification status, notes, evidence URL, and pre-aggregated BNetzA measures for the source geography.

The minimum approved-for-design geographic model is:

1. A reference relation containing one row per BNetzA state/district combination and its KBA code.
2. A charging aggregation at KBA district code and BNetzA reference date.
3. A KBA district-stock relation at KBA district code and KBA reference date.
4. A joined analytical relation at KBA district code with explicit infrastructure and vehicle dates.

Charging must be aggregated by KBA code before joining KBA stock. This is mandatory because Kreisfreie Stadt Trier and Landkreis Trier-Saarburg both map to KBA registration-region code 07211. A raw 401-row join would duplicate that KBA stock.

## Proposed SQL definitions — design-only history

The authoritative Batch 05 proposal, including source-aware joins, maximum-per-point power parsing, mapping flags, snapshot dates, acceptance checks, and backup/rollback requirements, is [geographic-layer-design.md](geographic-layer-design.md). The abbreviated definitions below are retained as architecture history and must not be executed as-is.

The following abbreviated definitions show the intended grain and join order. They were not executed in Batch 04 or Batch 05 and are not present as permanent DuckDB objects.

~~~sql
-- Planned reference relation; current source is the curated CSV.
CREATE TABLE reference.bnetza_kba_district_crosswalk (
    crosswalk_version VARCHAR,
    bnetza_reference_date DATE,
    kba_reference_date DATE,
    bnetza_state_name VARCHAR,
    bnetza_district_name VARCHAR,
    bnetza_admin_type VARCHAR,
    kba_district_code VARCHAR,
    kba_district_name VARCHAR,
    mapping_status VARCHAR,
    mapping_method VARCHAR,
    verification_status VARCHAR,
    mapping_note VARCHAR,
    evidence_url VARCHAR
);

-- Planned charging aggregation: one row per KBA code and BNetzA snapshot.
CREATE VIEW analytics.charging_by_kba_district AS
SELECT
    c.kba_district_code,
    SUM(equipment_rows) AS equipment_rows,
    SUM(declared_point_count) AS declared_point_count,
    SUM(charging_point_slots) AS charging_point_slots,
    SUM(equipment_nominal_power_kw) AS equipment_nominal_power_kw,
    DATE '2026-09-30' AS bnetza_reference_date
FROM reference.bnetza_kba_district_crosswalk c
WHERE c.mapping_status = 'mapped'
GROUP BY c.kba_district_code;

-- Planned vehicle join: preserve one KBA row per code and date.
CREATE VIEW analytics.charging_vs_bev_by_kba_district AS
SELECT
    c.kba_district_code,
    c.bnetza_reference_date,
    k.reference_date AS kba_reference_date,
    c.equipment_rows,
    c.charging_point_slots,
    k.passenger_cars,
    k.bev_cars,
    k.phev_cars
FROM analytics.charging_by_kba_district c
LEFT JOIN core.kba_district_ev_stock k
  ON k.district_code = c.kba_district_code
 AND k.reference_date = DATE '2026-07-01';
~~~

The final implementation must add source-date keys, preserve unmapped/provisional rows as quality flags, and validate code uniqueness before any DDL is approved.

## Database limitations

- DuckDB tables contain the current source snapshots, not a slowly changing historical infrastructure model.
- The BNetzA snapshot is a published register and is not exhaustive.
- KBA district rows, postcode rows, municipality rows, and state-level rows are alternative reporting grains. They must not be summed together as though they were additive partitions.
- The latest infrastructure and vehicle dates are not contemporaneous.
- No utilization or energy-delivery tables exist.
- The existing state view must be repaired or replaced before multi-snapshot loading.
