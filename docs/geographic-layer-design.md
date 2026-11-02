# Geographic analytical layer design

## Status and decision boundary

Batch 05 established this design proposal and Batch 06 deployed its approved local implementation. The Crosswalk CSV and source workbooks remain unchanged. The executable definitions are in [sql/06_geographic_layer.sql](../sql/06_geographic_layer.sql), and the deployment/validation evidence is in [reports/batch06_geographic_deployment.md](../reports/batch06_geographic_deployment.md).

The design is intentionally limited to the existing BNetzA and KBA sources. It does not add BBSR, boundary geometries, utilization data, energy delivery, or a second infrastructure snapshot.

## Inputs and snapshot meaning

The deployed layer uses:

- BNetzA charging equipment and point slots from `2026-09-30`, identified by source ID `bnetza_charging_2026_09_30`.
- KBA FZ 27.15 district stock from `2026-01-01`, `2026-04-01`, and `2026-07-01`.
- `data/reference/bnetza_kba_district_crosswalk_2026.csv`, whose `kba_reference_date` (`2026-07-01`) is the local KBA release used to resolve and check the crosswalk labels.

The crosswalk reference date is not a replacement for the KBA stock date. The analytical join must keep `bnetza_reference_date` and the actual `kba_reference_date` from `core.kba_district_ev_stock` visible in every combined row. The infrastructure measures are repeated for each KBA stock date for comparison; they are not summed across dates.

## Deployed objects

The current database has `raw`, `core`, `reference`, and `analytics` schemas. The names and grains below are the approved Batch 06 objects.

| Object | Type | Row grain | Proposed unique key | Purpose |
|---|---|---|---|---|
| `reference.bnetza_kba_district_crosswalk_2026` | table | One BNetzA source snapshot, state/district pair, and crosswalk version | `(crosswalk_version, bnetza_source_id, bnetza_state_name, bnetza_district_name)` | Permanent, auditable copy of the approved CSV mapping and its verification fields |
| `analytics.charging_by_kba_district_2026_09_30` | view | One BNetzA source snapshot and KBA district code; an unmapped quality row may have a null code | `(bnetza_source_id, kba_district_code)` for mapped rows | Equipment, point, power-band, and mapping-quality measures after aggregate-before-join |
| `analytics.kba_district_charging_vs_bev_2026` | view | One BNetzA source snapshot, KBA district code, and KBA stock reference date | `(bnetza_source_id, kba_district_code, kba_reference_date)` for mapped rows | Combined descriptive infrastructure/vehicle relation with both source dates and quality flags |

The reference table should retain every current CSV column, including `mapping_status`, `mapping_method`, `verification_status`, `mapping_note`, `evidence_url`, and the source aggregate fields. `bnetza_source_id` is a load-time lineage field derived from the source manifest; adding it to a future permanent table does not authorize changing the current CSV.

## Reference-table definition

The following is the design-history table definition. The deployed SQL is maintained in `sql/06_geographic_layer.sql` and was run only after the Batch 06 approval, backup, and rollback checks.

~~~sql
CREATE TABLE reference.bnetza_kba_district_crosswalk_2026 (
    crosswalk_version VARCHAR NOT NULL,
    bnetza_source_id VARCHAR NOT NULL,
    bnetza_reference_date DATE NOT NULL,
    kba_reference_date DATE NOT NULL,
    bnetza_state_name VARCHAR NOT NULL,
    bnetza_district_name VARCHAR NOT NULL,
    bnetza_admin_type VARCHAR,
    kba_state_name VARCHAR,
    kba_district_code VARCHAR,
    kba_district_name VARCHAR,
    kba_admin_type VARCHAR,
    mapping_status VARCHAR NOT NULL,
    mapping_method VARCHAR NOT NULL,
    verification_status VARCHAR NOT NULL,
    mapping_note VARCHAR,
    evidence_url VARCHAR,
    equipment_rows BIGINT,
    declared_point_count BIGINT,
    charging_point_slots BIGINT,
    equipment_nominal_power_kw DOUBLE,
    UNIQUE (crosswalk_version, bnetza_source_id,
            bnetza_state_name, bnetza_district_name)
);
~~~

The target KBA code is not unique in the reference table: code `07211` is intentionally represented by both Trier source rows. The source-geography key is unique. A load check must reject duplicate source-geography keys, missing target codes, or a change in the explicitly documented duplicate-target set.

## Charging aggregation definition

`analytics.charging_by_kba_district_2026_09_30` aggregates equipment and point measures separately. This prevents equipment nominal power from being multiplied by the number of point slots. The source-aware equipment-to-point join uses both `source_id` and Excel row. The point-level power parser splits every semicolon-separated token, converts decimal commas to decimal points, keeps only successfully parsed numeric values, and uses the maximum value within the point. It never sums connector powers.

The following definition is design-history SQL. The literal source ID and date make the current snapshot contract explicit; the deployed implementation keeps these values in the reproducible SQL template.

~~~sql
CREATE VIEW analytics.charging_by_kba_district_2026_09_30 AS
WITH current_crosswalk AS (
    SELECT *
    FROM reference.bnetza_kba_district_crosswalk_2026
    WHERE crosswalk_version = '2026-07-01'
      AND bnetza_source_id = 'bnetza_charging_2026_09_30'
      AND bnetza_reference_date = DATE '2026-09-30'
),
source_equipment AS (
    SELECT e.*, c.kba_district_code, c.mapping_status,
           c.verification_status
    FROM core.charging_equipment e
    LEFT JOIN current_crosswalk c
      ON c.bnetza_source_id = e.source_id
     AND c.bnetza_state_name = e.state_name
     AND c.bnetza_district_name = e.district_name
    WHERE e.source_id = 'bnetza_charging_2026_09_30'
),
source_geography AS (
    SELECT DISTINCT source_id, state_name, district_name,
           kba_district_code, mapping_status, verification_status
    FROM source_equipment
),
source_points AS (
    SELECT p.source_id, p.equipment_excel_row, p.point_number,
           p.connector_power_raw, e.kba_district_code,
           e.mapping_status, e.verification_status
    FROM core.charging_point p
    LEFT JOIN source_equipment e
      ON e.source_id = p.source_id
     AND e.excel_row = p.equipment_excel_row
    WHERE p.source_id = 'bnetza_charging_2026_09_30'
),
point_power_tokens AS (
    SELECT p.source_id, p.equipment_excel_row, p.point_number,
           TRY_CAST(REPLACE(TRIM(token), ',', '.') AS DOUBLE) AS power_kw
    FROM source_points p
    CROSS JOIN LATERAL UNNEST(
        STRING_SPLIT(COALESCE(p.connector_power_raw, ''), ';')
    ) AS tokens(token)
),
point_power AS (
    SELECT source_id, equipment_excel_row, point_number,
           MAX(power_kw) AS max_declared_point_power_kw
    FROM point_power_tokens
    GROUP BY source_id, equipment_excel_row, point_number
),
equipment_by_code AS (
    SELECT source_id, kba_district_code,
           COUNT(*) AS equipment_count,
           SUM(equipment_nominal_power_kw) / 1000.0
               AS equipment_nominal_power_mw
    FROM source_equipment
    GROUP BY source_id, kba_district_code
),
points_by_code AS (
    SELECT p.source_id, p.kba_district_code,
           COUNT(*) AS charging_point_count,
           COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw <= 22)
               AS normal_points_le_22_kw,
           COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw > 22)
               AS fast_points_gt_22_kw,
           COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw >= 150)
               AS points_ge_150_kw,
           COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw >= 350)
               AS points_ge_350_kw,
           COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw IS NULL)
               AS points_without_valid_power
    FROM source_points p
    LEFT JOIN point_power pp
      ON pp.source_id = p.source_id
     AND pp.equipment_excel_row = p.equipment_excel_row
     AND pp.point_number = p.point_number
    GROUP BY p.source_id, p.kba_district_code
),
mapping_by_code AS (
    SELECT kba_district_code,
           CASE WHEN kba_district_code IS NULL
                THEN 'unmapped' ELSE 'mapped' END AS mapping_status,
           CASE WHEN COUNT(*) FILTER (
                        WHERE verification_status LIKE 'provisional%'
                    ) > 0
                THEN 'provisional'
                ELSE 'observed_local_snapshot'
           END AS mapping_verification_status,
           COUNT(*) AS source_geography_rows,
           COUNT(*) FILTER (WHERE verification_status LIKE 'provisional%')
               AS provisional_mapping_rows,
           COUNT(*) FILTER (WHERE kba_district_code IS NULL)
               AS unmapped_source_geography_rows
    FROM source_geography
    GROUP BY kba_district_code
),
regional AS (
    SELECT COALESCE(e.source_id, p.source_id) AS bnetza_source_id,
           COALESCE(e.kba_district_code, p.kba_district_code)
               AS kba_district_code,
           COALESCE(m.mapping_status,
                    CASE WHEN COALESCE(e.kba_district_code,
                                       p.kba_district_code) IS NULL
                         THEN 'unmapped' ELSE 'mapped' END)
               AS mapping_status,
           COALESCE(m.mapping_verification_status, 'unmapped')
               AS mapping_verification_status,
           COALESCE(m.source_geography_rows, 0) AS source_geography_rows,
           COALESCE(m.provisional_mapping_rows, 0)
               AS provisional_mapping_rows,
           COALESCE(m.unmapped_source_geography_rows, 0)
               AS unmapped_source_geography_rows,
           COALESCE(e.equipment_count, 0) AS equipment_count,
           COALESCE(p.charging_point_count, 0) AS charging_point_count,
           COALESCE(p.normal_points_le_22_kw, 0)
               AS normal_points_le_22_kw,
           COALESCE(p.fast_points_gt_22_kw, 0)
               AS fast_points_gt_22_kw,
           COALESCE(p.points_ge_150_kw, 0) AS points_ge_150_kw,
           COALESCE(p.points_ge_350_kw, 0) AS points_ge_350_kw,
           COALESCE(p.points_without_valid_power, 0)
               AS points_without_valid_power,
           COALESCE(e.equipment_nominal_power_mw, 0)
               AS equipment_nominal_power_mw
    FROM equipment_by_code e
    FULL OUTER JOIN points_by_code p
      ON e.source_id = p.source_id
     AND e.kba_district_code IS NOT DISTINCT FROM p.kba_district_code
    LEFT JOIN mapping_by_code m
      ON m.kba_district_code IS NOT DISTINCT FROM
         COALESCE(e.kba_district_code, p.kba_district_code)
)
SELECT regional.*,
       ROUND(100.0 * fast_points_gt_22_kw
             / NULLIF(charging_point_count, 0), 2)
           AS fast_point_percentage,
       ROUND(100.0 * points_ge_150_kw
             / NULLIF(charging_point_count, 0), 2)
           AS high_power_percentage,
       DATE '2026-09-30' AS bnetza_reference_date
FROM regional;
~~~

The current validation produced 400 mapped regional rows with no null KBA code, but the left joins and quality columns are deliberate. A future load with an unmapped source geography must expose the row and fail the deployment checks; it must not silently drop equipment or points.

## Combined stock definition

The combined view must join the regional result to KBA district stock by code only after the charging aggregation is complete. KBA uniqueness must be checked at `(district_code, reference_date)` before the view is created.

~~~sql
CREATE VIEW analytics.kba_district_charging_vs_bev_2026 AS
SELECT c.bnetza_source_id,
       c.bnetza_reference_date,
       c.kba_district_code,
       k.reference_date AS kba_reference_date,
       c.source_geography_rows,
       c.provisional_mapping_rows,
       c.unmapped_source_geography_rows,
       c.equipment_count,
       c.charging_point_count,
       c.normal_points_le_22_kw,
       c.fast_points_gt_22_kw,
       c.points_ge_150_kw,
       c.points_ge_350_kw,
       c.points_without_valid_power,
       c.fast_point_percentage,
       c.high_power_percentage,
       c.equipment_nominal_power_mw,
       k.passenger_cars,
       k.bev_cars,
       k.phev_cars
FROM analytics.charging_by_kba_district_2026_09_30 c
LEFT JOIN core.kba_district_ev_stock k
  ON k.district_code = c.kba_district_code;
~~~

This produces 400 x 3 = 1,200 combined rows for the current snapshots. The BNetzA measures repeat across the three KBA dates; the view must not provide a query that sums those repeated infrastructure measures across dates. A BEV-per-point ratio derived from this view remains a provisional cross-snapshot indicator.

## Mapping and verification fields

- `mapping_status` remains the source-level status from the crosswalk. No provisional row may be relabelled as officially verified.
- The regional view exposes a derived `mapping_status` (`mapped` or `unmapped`) and `mapping_verification_status` (`provisional`, `observed_local_snapshot`, or `unmapped`); the reference table retains the source-level statuses and notes.
- `verification_status LIKE 'provisional%'` is the explicit quality rule for the current 24 provisional source mappings: 22 aliases and two Trier shared-region rows.
- `source_geography_rows` must be 2 for KBA code `07211` and 1 for the other currently mapped codes.
- `kba_district_code` is not a unique key in the reference table; it becomes unique only after source-geography aggregation.
- The KBA stock relation must retain one row per district code and stock date. The shared Trier code therefore has three stock rows, not six.

## Deployed state-view correction

Before Batch 06, `analytics.charging_by_state` grouped its point subquery by `equipment_excel_row` only and joined on Excel row only. Batch 06 applied the following source-aware correction:

~~~sql
LEFT JOIN (
    SELECT source_id, equipment_excel_row, COUNT(*) AS point_slots
    FROM core.charging_point
    GROUP BY source_id, equipment_excel_row
) p
  ON e.source_id = p.source_id
 AND e.excel_row = p.equipment_excel_row
~~~

The deployed view was validated against the recorded 16-state baseline and an independent source-aware aggregation. The Batch 06 geographic views do not depend on the state view.

## Deployment acceptance checks

The following checks were used before and after deployment and remain required for a future source-date change:

| Check | Current expected result |
|---|---:|
| BNetzA source geographies retained | 401 |
| Crosswalk rows and mapped source geographies | 401 / 401 |
| Distinct mapped KBA codes | 400 |
| Explicit provisional source mappings | 24 |
| Equipment rows retained after source-aware mapping | 117,662 |
| Point rows retained after source-aware equipment join | 211,253 |
| Orphan point rows on `(source_id, equipment_excel_row)` | 0 |
| Point rows without a valid maximum parsed power | 0 |
| Normal points / fast points | 156,155 / 55,098 |
| Points at least 150 / 350 kW | 40,950 / 6,950 |
| Equipment nominal power | 9,215.4173 MW |
| KBA stock rows per date / combined rows | 400 / 1,200 |
| Duplicate KBA `(code, date)` keys | 0 |
| July 2026 district BEV stock | 2,362,218 |
| KBA stock duplicated by raw Trier crosswalk join | prohibited; must not occur |

The power-band identity must hold for every regional row: normal points plus fast points equals all point slots; the high-power bands must be nested within fast points; and percentages must use the point-slot denominator. Equipment nominal power must be aggregated before any equipment-to-point join.

## Backup and rollback record

Before the approved Batch 06 schema change:

1. Close all DuckDB writers and record the baseline database hash, size, and current Git commit.
2. Make a byte-preserving backup under an ignored local backup directory, with the source date and migration identifier in the filename. Include any associated WAL only if it exists and the recovery procedure requires it.
3. Validate the backup through a separate read-only connection, including baseline table counts and the state-view row count.
4. Apply the DDL in one transaction and validate the new objects against the read-only Batch 05 results before treating the deployment as successful.

Batch 06 executed this procedure. The verified pre-deployment backup was `data/backups/ev_charging_pre_batch06_20261102_113900.duckdb`; its size was 39,071,744 bytes, its SHA-256 was `a51b350d337ba8fa057dc62406e38bcda1d9872a41b606629b815c110f10d11a`, it had no WAL, and a separate read-only connection confirmed the baseline counts. Rollback remains to stop using the deployed objects and restore this backup, or remove only the newly created/modified objects inside an explicitly approved transaction. No rollback should delete source workbooks, the curated CSV, or the original baseline database.
