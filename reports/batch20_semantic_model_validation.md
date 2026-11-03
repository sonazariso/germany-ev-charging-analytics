# Batch 20 — Tableau Semantic Model Validation

**Result: PASS**

Batch 20 completed the approved design-and-validation scope. It created a
semantic-model specification and KPI mapping only. It did not create Tableau
workbooks/extracts, physical Fact/Dimension tables, DuckDB objects, ETL
migrations, source/reference changes, new datasets, or dependencies.

## 1. Validation scope and controls

The initial project state was clean at commit `3be5f66`:

- `git rev-parse HEAD` resolved to `3be5f66` (`feat: prepare validated Tableau data exports (Batch 19)`).
- `git status --porcelain=v1` returned no paths before Batch 20 edits.
- `git remote -v` returned no configured remote.
- DuckDB was opened with `.venv/bin/python` and `duckdb.connect(..., read_only=True)`.
- Database checks used `SELECT` statements and `information_schema` only.
- CSV checks used the manifest, UTF-8 `csv.DictReader`, in-memory key sets, and
  SHA-256; no export was rewritten.

## 2. Batch 19 export contract validation

| Export | Manifest rows | Actual rows | Manifest columns | Actual columns | Natural key check | SHA-256 |
|---|---:|---:|---:|---:|---|---|
| `national_charging_2026_09_30.csv` | 1 | 1 | 14 | 14 | PASS: `geography_name` | MATCH |
| `state_charging_2026_09_30.csv` | 16 | 16 | 15 | 15 | PASS: `state_name` | MATCH |
| `bbsr_district_charging_2025_geography.csv` | 400 | 400 | 27 | 27 | PASS: historical BBSR code | MATCH |
| `bbsr_type_charging_2025_geography.csv` | 4 | 4 | 23 | 23 | PASS: type code | MATCH |
| `kba_state_ev_stock_2026.csv` | 48 | 48 | 13 | 13 | PASS: state/date | MATCH |
| `kba_registration_region_ev_stock_2026.csv` | 1,200 | 1,200 | 15 | 15 | PASS: region/date | MATCH |
| `state_ev_charging_comparison_2026.csv` | 16 | 16 | 28 | 28 | PASS: `state_name` | MATCH |
| `state_temporal_sensitivity_2026.csv` | 16 | 16 | 80 | 80 | PASS: `state_name` | MATCH |
| `kba_national_stock_history.csv` | 33 | 33 | 10 | 10 | PASS: `stock_date` | MATCH |
| **Total** | **1,734** | **1,734** | — | — | **PASS** | **All nine match manifest** |

Share columns in the national, state, and BBSR district exports were recomputed
from their stored numerator and denominator columns. All checks passed without
averaging stored percentages.

## 3. Actual DuckDB schema evidence

The following actual objects and key types were inspected. The full object
contract remains in `data/exports/tableau/export_manifest.json` and the
Batch 19 validation report.

| Object | Actual type | Actual key/date/measure fields inspected |
|---|---|---|
| `core.charging_equipment` | BASE TABLE | `source_id VARCHAR`, `excel_row INTEGER`, `status VARCHAR`, `declared_point_count INTEGER`, `equipment_nominal_power_kw DOUBLE`, `commissioning_date DATE`, `state_name VARCHAR` |
| `core.charging_point` | BASE TABLE | `source_id VARCHAR`, `equipment_excel_row INTEGER`, `point_number INTEGER`, `connector_power_raw VARCHAR`, `connector_power_kw_single DOUBLE` |
| `core.kba_state_fuel_stock` | BASE TABLE | `source_id VARCHAR`, `reference_date DATE`, `state_name VARCHAR`, `fuel_type VARCHAR`, `passenger_cars BIGINT` |
| `core.kba_district_ev_stock` | BASE TABLE | `source_id VARCHAR`, `reference_date DATE`, `state_name VARCHAR`, `district_code VARCHAR`, `passenger_cars BIGINT`, `bev_cars BIGINT`, `phev_cars BIGINT` |
| `analytics.charging_by_state` | VIEW | `state_name VARCHAR`, `equipment_rows BIGINT`, `declared_points HUGEINT`, `populated_point_slots HUGEINT` |
| `analytics.charging_by_bbsr_district_2025_harmonized` | VIEW | historical BBSR target identity/date fields plus `equipment_count HUGEINT`, `charging_point_count HUGEINT`, `fast_charging_point_count HUGEINT`, `total_equipment_nominal_power_mw DOUBLE` |
| `analytics.kba_national_quarterly_stock` | VIEW | `stock_date DATE`, `passenger_bev BIGINT`, `passenger_phev BIGINT`, `passenger_cars_total BIGINT` |

The point-level analytical view exposes `connector_power_raw` and
`connector_power_kw_single`; it does not expose an invented
`max_connector_power_kw` field. Batch 19's validated threshold counts therefore
remain the contract fields for the initial aggregate facts.

## 4. Required baseline reconciliation

| Baseline | Expected | Observed | Result |
|---|---:|---:|---|
| Equipment records | 117,662 | 117,662 | PASS |
| Populated charging-point slots | 211,253 | 211,253 | PASS |
| Normal points | 156,155 | 156,155 | PASS |
| Fast points | 55,098 | 55,098 | PASS |
| Points `>=150 kW` | 40,950 | 40,950 | PASS |
| Points `>=350 kW` | 6,950 | 6,950 | PASS |
| Equipment nominal power | 9,215.4173 MW | 9,215.4173 MW | PASS |
| KBA July 16-state BEV | 2,362,218 | 2,362,218 | PASS |
| KBA July Deutschland BEV | 2,365,047 | 2,365,047 | PASS |
| KBA July 16-state PHEV | 1,225,241 | 1,225,241 | PASS |
| KBA July Deutschland PHEV | 1,226,863 | 1,226,863 | PASS |
| Historical BBSR target units | 400 | 400 | PASS |
| Historical BBSR type counts | 68 / 131 / 98 / 103 | 68 / 131 / 98 / 103 | PASS |

National-to-state charging reconciliation passed for equipment, declared and
populated points, all three power bands, unknown-power points, and nominal MW.
The harmonized BBSR district rows reconcile to the same national totals.

## 5. Key and relationship validation

- All nine declared natural keys are unique and non-null in their current
  contract scope.
- KBA registration-region keys contain 400 codes for each of the three dates;
  all 1,200 `(code, date)` keys are unique.
- `07211` appears exactly once per KBA date and remains
  `TRIER-SAARBURG`; no allocation was performed.
- The DuckDB harmonization reference contains 401 source rows and 400 distinct
  historical BBSR target codes. The four target type counts match 68, 131, 98,
  and 103.
- The 16 state charging names match the 16 KBA state names independently for
  each of `2026-01-01`, `2026-04-01`, and `2026-07-01`.
- The match test does not authorize an unconstrained state charging-to-KBA
  relationship: it would produce three KBA rows per state and repeat one
  September charging row. The recommended fixed comparison fact avoids this
  path.
- No direct BBSR-to-KBA relationship was asserted. The corresponding
  relationship is explicitly prohibited and remains unverified.

## 6. KPI mapping validation

`reports/batch20_kpi_model_mapping.csv` was parsed in memory after creation:

- exactly 59 data rows;
- exactly 59 unique IDs;
- every ID from the Batch 18 register appears once;
- existing publication status is copied from the canonical register;
- every row includes a logical fact, dimension contract, grain, formula,
  calculation location, filter behavior, source date, risk, and readiness;
- `NOT_SUPPORTED` KPIs map to `NOT_IMPLEMENTABLE` and are not promoted;
- `CONTEXT_ONLY` and `EXPLORATORY` rows remain labelled as such.

The mapping deliberately separates reusable DuckDB derivations from
Tableau-safe ratios. When a ratio is calculated in Tableau, it is defined as a
ratio of aggregated numerator and denominator fields, never an average of
stored percentages.

## 7. Geographic and date safeguards validated

- 16 German states remain separate from `Deutschland` and `Sonstige`.
- BBSR 2025 historical target geography remains charging-only.
- Hanau/Main-Kinzig historical consolidation, corrected Kassel classification,
  and separate Trier charging components remain part of the documented
  harmonization contract.
- KBA code `07211` is not split.
- BNetzA `2026-09-30`, KBA `2026-01-01`/`04-01`/`07-01`, BBSR `2025-12-31`,
  and commissioning/cohort dates remain separate semantic roles.
- No historical BNetzA panel is inferred from commissioning dates.
- The survivor cohort is explicitly not actual July infrastructure.

## 8. Immutability and hygiene

| Check | Result |
|---|---|
| DuckDB SHA-256 before read-only checks | `5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3` |
| DuckDB SHA-256 after read-only checks | `5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3` |
| DuckDB unchanged | PASS |
| Batch 19 export checksums | All nine MATCH |
| Manifest-listed source/reference fingerprints | MATCH |
| Raw sources/Crosswalks changed | No |
| DuckDB tables/views/schema changed | No |
| New dependencies/datasets downloaded | No |
| Tableau workbook/extract created | No |
| Git remote configured | No |
| Private Persian reference staged | No; it is outside the repository |

## 9. Validation conclusion

The recommended separate-source architecture is implementable from the current
validated aggregate exports and satisfies the approved analytical requirements.
The open risks are semantic rather than failed data checks: no KBA-to-BBSR
vehicle bridge, no genuine historical infrastructure snapshots, provisional
KBA geographic mapping for infrastructure, and the cross-snapshot nature of
state comparison ratios. These remain visible in the relationship design and
KPI mapping.
