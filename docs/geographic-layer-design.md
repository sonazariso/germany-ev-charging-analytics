# Geographic analytical layer design

## Status and decision boundary

This is a Batch 05 design proposal. The read-only validation passed for the current local snapshots, but none of the objects below has been deployed to DuckDB. The Crosswalk CSV, source workbooks, and existing database objects remain unchanged.

The design is intentionally limited to the existing BNetzA and KBA sources. It does not add BBSR, boundary geometries, utilization data, energy delivery, or a second infrastructure snapshot.

## Inputs and snapshot meaning

The proposed layer uses:

- BNetzA charging equipment and point slots from `2026-09-30`, identified by source ID `bnetza_charging_2026_09_30`.
- KBA FZ 27.15 district stock from `2026-01-01`, `2026-04-01`, and `2026-07-01`.
- `data/reference/bnetza_kba_district_crosswalk_2026.csv`, whose `kba_reference_date` (`2026-07-01`) is the local KBA release used to resolve and check the crosswalk labels.

The crosswalk reference date is not a replacement for the KBA stock date. The analytical join must keep `bnetza_reference_date` and the actual `kba_reference_date` from `core.kba_district_ev_stock` visible in every combined row. The infrastructure measures are repeated for each KBA stock date for comparison; they are not summed across dates.

## Proposed objects

The current database has only `raw`, `core`, and `analytics` schemas. A future approved migration may add `reference`; the names below are proposed and are not currently present.

| Object | Type | Row grain | Proposed unique key | Purpose |
|---|---|---|---|---|
| `reference.bnetza_kba_district_crosswalk` | table | One BNetzA source snapshot, state/district pair, and crosswalk version | `(crosswalk_version, bnetza_source_id, bnetza_state_name, bnetza_district_name)` | Permanent, auditable copy of the approved CSV mapping and its verification fields |
| `analytics.charging_by_kba_district` | view | One BNetzA source snapshot and KBA district code; an unmapped quality row may have a null code | `(bnetza_source_id, kba_district_code)` for mapped rows | Equipment, point, power-band, and mapping-quality measures after aggregate-before-join |
| `analytics.charging_vs_kba_district_stock` | view | One BNetzA source snapshot, KBA district code, and KBA stock reference date | `(bnetza_source_id, kba_district_code, kba_reference_date)` for mapped rows | Combined descriptive infrastructure/vehicle relation with both source dates and quality flags |

The reference table should retain every current CSV column, including `mapping_status`, `mapping_method`, `verification_status`, `mapping_note`, `evidence_url`, and the source aggregate fields. `bnetza_source_id` is a load-time lineage field derived from the source manifest; adding it to a future permanent table does not authorize changing the current CSV.

## Reference-table definition

The following is design SQL only. It must not be run until the layer design, backup, and rollback plan are approved.

~~~sql
CREATE TABLE reference.bnetza_kba_district_crosswalk (
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

`analytics.charging_by_kba_district` must aggregate equipment and point measures separately. This prevents equipment nominal power from being multiplied by the number of point slots. The source-aware equipment-to-point join uses both `source_id` and Excel row. The point-level power parser splits every semicolon-separated token, converts decimal commas to decimal points, keeps only successfully parsed numeric values, and uses the maximum value within the point. It never sums connector powers.

The following definition is design SQL only. The literal source ID and date are shown to make the current snapshot contract explicit; an approved implementation may resolve them from a source catalog.

~~~sql
CREATE VIEW analytics.charging_by_kba_district AS
WITH current_crosswalk AS (
    SELECT *
    FROM reference.bnetza_kba_district_crosswalk
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
CREATE VIEW analytics.charging_vs_kba_district_stock AS
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
FROM analytics.charging_by_kba_district c
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

## Existing state-view correction

The current `analytics.charging_by_state` view is not changed in Batch 05. Its point subquery groups by `equipment_excel_row` only and joins on Excel row only. The minimal source-aware correction is:

~~~sql
LEFT JOIN (
    SELECT source_id, equipment_excel_row, COUNT(*) AS point_slots
    FROM core.charging_point
    GROUP BY source_id, equipment_excel_row
) p
  ON e.source_id = p.source_id
 AND e.excel_row = p.equipment_excel_row
~~~

The correction still requires an approved migration and validation against the current single-snapshot totals before it is deployed. The Batch 05 geographic views must not depend on the unsafe view.

## Pre-deployment acceptance checks

The following checks are required before any permanent object is created:

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

## Backup and rollback considerations

Before an approved schema change:

1. Close all DuckDB writers and record the baseline database hash, size, and current Git commit.
2. Make a byte-preserving backup outside the tracked repository tree, with the source date and migration identifier in the filename. Include any associated WAL only if it exists and the recovery procedure requires it.
3. Test the DDL against a copy of the backup first. Prefer building a new database copy and atomically switching only after all acceptance checks pass.
4. Keep the current database untouched until the new objects have been validated against the read-only Batch 05 results.

Rollback is to stop using the new copy and restore the byte-preserving baseline backup or remove only the newly created objects inside an approved transaction. No rollback should delete source workbooks, the curated CSV, or the original baseline database. These steps are design requirements only; no backup, DDL, or rollback action was executed in Batch 05.
