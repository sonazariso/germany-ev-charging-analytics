# Batch 06 — Geographic analytics layer deployment

## Deployment status

PASS. Batch 06 deployed the approved geographic layer to the existing local DuckDB file. The original BNetzA and KBA workbooks and the curated Crosswalk CSV were not modified.

The implementation is reproducible with [sql/06_geographic_layer.sql](../sql/06_geographic_layer.sql), [scripts/06_deploy_geographic_layer.py](../scripts/06_deploy_geographic_layer.py), and [scripts/06_validate_geographic_layer.py](../scripts/06_validate_geographic_layer.py).

## Verified backup

The pre-deployment backup was created before any Batch 06 DDL:

`data/backups/ev_charging_pre_batch06_20261102_113900.duckdb`

- Size: 39,071,744 bytes.
- SHA-256: `a51b350d337ba8fa057dc62406e38bcda1d9872a41b606629b815c110f10d11a`.
- Source and backup hashes matched.
- No WAL existed before or after the backup.
- The repository filesystem check showed approximately 62 GiB free before backup creation.
- A separate read-only connection confirmed 117,662 equipment rows, 211,253 charging-point rows, 1,200 KBA district rows, and 16 state-view rows.
- The backup directory is ignored by Git and the backup is not staged or committed.

## Objects created or modified

Created:

- `reference.bnetza_kba_district_crosswalk_2026` — 401 rows at one BNetzA source state/district and crosswalk-version grain; `kba_district_code` remains text; the source geography key is unique and code `07211` occurs twice.
- `analytics.charging_by_kba_district_2026_09_30` — 400 rows at one KBA district code for the BNetzA 2026-09-30 snapshot.
- `analytics.kba_district_charging_vs_bev_2026` — 1,200 rows at one KBA district code and actual KBA stock reference date.

Modified:

- `analytics.charging_by_state` — point aggregation and join now use both `source_id` and `equipment_excel_row`; output names, order, 16-state grain, and baseline metrics are unchanged.

The geographic regional view aggregates equipment and point measures separately, parses every semicolon-delimited connector-power token, normalizes decimal commas, and uses the maximum valid token per point. It exposes an explicit `points_without_valid_power` count and does not sum connector powers.

## Validation results

### Source and mapping integrity

| Check | Result |
|---|---:|
| Equipment rows | 117,662 |
| Charging points | 211,253 |
| Orphan charging points | 0 |
| Duplicate equipment keys / point keys | 0 / 0 |
| Equipment-to-point count mismatches | 0 |
| Equipment mapped exactly once | 117,662 / 117,662 |
| Points mapped exactly once | 211,253 / 211,253 |
| Crosswalk rows / unique BNetzA keys | 401 / 401 |
| Unique KBA codes | 400 |
| Provisional mappings | 24 = 22 aliases + 2 Trier rows |

### Regional charging view

| Measure | Result |
|---|---:|
| Regional rows / unique KBA codes | 400 / 400 |
| Equipment total | 117,662 |
| Charging-point total | 211,253 |
| Declared charging-point total | 211,253 |
| Normal points, maximum declared power <=22 kW | 156,155 |
| Fast points, maximum declared power >22 kW | 55,098 |
| Points >=150 kW | 40,950 |
| Points >=350 kW | 6,950 |
| Points without valid maximum parsed power | 0 |
| Declared equipment nominal power | 9,215.4173 MW |

The band identity passed for every regional row: normal + fast + unclassifiable = all point slots; the >=150 kW band is nested within fast points; the >=350 kW band is nested within >=150 kW points.

### Combined KBA view and Trier reconciliation

The combined view contains 400 rows on each of 2026-01-01, 2026-04-01, and 2026-07-01, with no duplicate `(kba_district_code, kba_reference_date)` keys. District BEV totals are 2,031,870, 2,167,111, and 2,362,218 respectively. July district PHEV stock is 1,225,241.

KBA code `07211` has two source geography rows in the reference table, one regional charging row after aggregation, and one combined stock row per KBA date. Its July BEV stock is 7,869 and is counted exactly once. The infrastructure snapshot remains 2026-09-30 beside each KBA stock date; these are cross-snapshot descriptive comparisons, not contemporaneous coverage measures. Infrastructure rows must not be summed across KBA dates.

### State-view comparison

The pre-deployment view contained 16 state rows. After the source-aware correction, the independent direct aggregation returned the same 16 rows and every equipment, declared-point, and populated-point value remained unchanged. No new state metric was added.

## Commands and results

Executed from the repository root:

~~~bash
.venv/bin/python -m py_compile \
  scripts/06_deploy_geographic_layer.py \
  scripts/06_validate_geographic_layer.py
.venv/bin/python scripts/06_deploy_geographic_layer.py --json
.venv/bin/python scripts/06_validate_geographic_layer.py --json
git diff --check
~~~

All commands passed. A second deployment-script run also passed and validated existing objects without duplicating the reference table or changing the state-view metrics.

## Known limitations and unresolved issues

- The 24 crosswalk mappings remain provisional and require authoritative geographic review; no mapping was promoted during Batch 06.
- BNetzA infrastructure is dated 2026-09-30 while KBA stock dates are January, April, and July 2026; combined ratios are provisional cross-snapshot indicators.
- The BNetzA register is not exhaustive; declared power is not utilization, energy delivery, availability, reliability, or queue time.
- The 400-district KBA total differs from the state-level Deutschland total because of the documented Sonstige/reporting-structure reconciliation.
- One BNetzA coordinate remains outside the broad Germany bounding check.
- Tableau, BBSR assessment, final licensing review, and publication remain out of scope.

## Next recommended analytical step

Complete independent authoritative review of the provisional crosswalk and shared Trier treatment before using the combined view for public-facing regional rankings or Tableau extracts.

No Git remote was added and nothing was uploaded or published.
