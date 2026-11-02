# Phase 03 — DuckDB ingest and validation

All source originals remain untouched; raw worksheet rows are retained in DuckDB.

## BNetzA

| Metric | Count |
|---|---:|
| All nonempty source rows (including metadata) | 117,670 |
| Equipment rows (Excel row >=12) | 117,662 |
| Populated charging-point slots | 211,253 |
| Declared charging points (sum source field) | 211,253 |
| Equipment with declared/slot mismatch | 0 |
| Equipment IDs missing | 0 |
| Duplicated equipment IDs | 0 |
| Distinct published states/region values | 16 |

## KBA normalized analytical tables

| Table | Rows |
|---|---:|
| `kba_state_fuel_stock` | 378 |
| `kba_district_ev_stock` | 1,200 |
| `kba_postcode_ev_stock` | 24,586 |
| `kba_municipality_ev_stock` | 32,229 |

## KBA BEV coverage by quarter

| Reference date | States |
|---|---:|
| 2026-01-01 | 18 |
| 2026-04-01 | 18 |
| 2026-07-01 | 18 |

## Equipment status (never silently filtered)

| Status | Equipment rows |
|---|---:|
| In Betrieb | 117,642 |
| In Wartung | 20 |

## Methodological cautions

- Point slots are NOT connector count; semicolon-separated connectors stay in one point.
- Differences between declared number of points and populated slots are flagged, not fabricated.
- KBA subtotals and alternate breakdowns remain in raw but are not added as separate vehicles.
- BNetzA published registry is incomplete relative to all German public chargers.
- KBA snapshot dates differ from BNetzA charging snapshot; do not imply same-date ratio.

This phase creates a preliminary canonical model. Further district, postcode, municipality and value reconciliation is required before final BI KPIs.
