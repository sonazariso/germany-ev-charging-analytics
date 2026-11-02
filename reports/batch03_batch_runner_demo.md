# Read-only DuckDB batch analysis report

Generated at (UTC): `2026-11-02T10:07:04.611267+00:00`

## Batch status

- Database: `data/analytics/ev_charging.duckdb`
- Connection: `connected_read_only`
- Connection closed: `True`
- Queries passed: `4`; queries failed: `0`

## Query summary

| Query | Status | Rows returned | Elapsed (s) | Error |
|---|---|---:|---:|---|
| `baseline_row_counts` | `passed` | 3 | 0.003425 |  |
| `crosswalk_coverage` | `passed` | 1 | 0.065667 |  |
| `equipment_point_reconciliation` | `passed` | 1 | 0.035422 |  |
| `aggregate_before_kba_join` | `passed` | 1 | 0.059983 |  |

## Query: `baseline_row_counts`

```sql
SELECT * FROM (VALUES
                ('core.charging_equipment', (SELECT COUNT(*) FROM core.charging_equipment)),
                ('core.charging_point', (SELECT COUNT(*) FROM core.charging_point)),
                ('core.kba_district_ev_stock_july', (
                    SELECT COUNT(*) FROM core.kba_district_ev_stock
                    WHERE reference_date = DATE '2026-07-01'
                ))
            ) AS counts(entity, row_count)
```

Status: `passed`; rows returned: `3`; elapsed: `0.003425` seconds.

Preview:

| entity | row_count |
| --- | --- |
| core.charging_equipment | 117662 |
| core.charging_point | 211253 |
| core.kba_district_ev_stock_july | 400 |

## Query: `crosswalk_coverage`

```sql
SELECT
                COUNT(*) AS crosswalk_rows,
                COUNT(DISTINCT bnetza_state_name || '|' || bnetza_district_name) AS bnetza_combinations,
                COUNT(*) FILTER (WHERE mapping_status = 'mapped') AS mapped_rows,
                COUNT(*) FILTER (WHERE mapping_status <> 'mapped') AS unmapped_rows,
                COUNT(DISTINCT kba_district_code) FILTER (WHERE mapping_status = 'mapped') AS mapped_kba_codes,
                COUNT(*) FILTER (WHERE kba_district_code = '07211') AS trier_shared_rows
            FROM read_csv_auto('./data/reference/bnetza_kba_district_crosswalk_2026.csv', types={'kba_district_code': 'VARCHAR'})
```

Status: `passed`; rows returned: `1`; elapsed: `0.065667` seconds.

Preview:

| crosswalk_rows | bnetza_combinations | mapped_rows | unmapped_rows | mapped_kba_codes | trier_shared_rows |
| --- | --- | --- | --- | --- | --- |
| 401 | 401 | 401 | 0 | 400 | 2 |

## Query: `equipment_point_reconciliation`

```sql
WITH point_counts AS (
                SELECT source_id, equipment_excel_row, COUNT(*) AS point_slots
                FROM core.charging_point
                GROUP BY source_id, equipment_excel_row
            )
            SELECT
                COUNT(*) AS equipment_rows,
                COALESCE(SUM(e.declared_point_count), 0) AS declared_point_count,
                COALESCE(SUM(COALESCE(p.point_slots, 0)), 0) AS charging_point_slots,
                COUNT(*) FILTER (
                    WHERE e.declared_point_count IS DISTINCT FROM COALESCE(p.point_slots, 0)
                ) AS equipment_point_mismatches
            FROM core.charging_equipment e
            LEFT JOIN point_counts p
              ON p.source_id = e.source_id
             AND p.equipment_excel_row = e.excel_row
```

Status: `passed`; rows returned: `1`; elapsed: `0.035422` seconds.

Preview:

| equipment_rows | declared_point_count | charging_point_slots | equipment_point_mismatches |
| --- | --- | --- | --- |
| 117662 | 211253 | 211253 | 0 |

## Query: `aggregate_before_kba_join`

```sql
WITH crosswalk AS (
                SELECT * FROM read_csv_auto('./data/reference/bnetza_kba_district_crosswalk_2026.csv', types={'kba_district_code': 'VARCHAR'})
            ),
            charging_by_kba AS (
                SELECT kba_district_code,
                       SUM(CAST(equipment_rows AS BIGINT)) AS equipment_rows,
                       SUM(CAST(charging_point_slots AS BIGINT)) AS charging_point_slots
                FROM crosswalk
                WHERE mapping_status = 'mapped'
                GROUP BY kba_district_code
            ),
            kba AS (
                SELECT district_code,
                       SUM(bev_cars) AS bev_cars
                FROM core.kba_district_ev_stock
                WHERE reference_date = DATE '2026-07-01'
                GROUP BY district_code
            ),
            joined AS (
                SELECT c.*, k.bev_cars
                FROM charging_by_kba c
                LEFT JOIN kba k ON k.district_code = c.kba_district_code
            )
            SELECT
                COUNT(*) AS joined_kba_codes,
                COUNT(*) FILTER (WHERE bev_cars IS NULL) AS missing_kba_codes,
                (SELECT COUNT(*) FROM kba) AS source_kba_codes,
                COALESCE(SUM(bev_cars), 0) AS joined_bev_cars,
                (SELECT COALESCE(SUM(bev_cars), 0) FROM kba) AS source_bev_cars,
                COALESCE(SUM(charging_point_slots), 0) AS charging_point_slots_after_aggregation
            FROM joined
```

Status: `passed`; rows returned: `1`; elapsed: `0.059983` seconds.

Preview:

| joined_kba_codes | missing_kba_codes | source_kba_codes | joined_bev_cars | source_bev_cars | charging_point_slots_after_aggregation |
| --- | --- | --- | --- | --- | --- |
| 400 | 0 | 400 | 2362218 | 2362218 | 211253 |

## Interpretation

- This runner executes the supplied SELECT/WITH statements on one DuckDB connection opened with `read_only=True`.
- CSV references such as `read_csv_auto({{CROSSWALK_CSV}})` are read as query-scoped relations; no permanent DuckDB table or view is created.
- SQL errors and validation failures are recorded per query and produce a non-zero process status.
