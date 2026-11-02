# Batch 13 — BBSR charging-only analytics deployment

## Result

**PASS.** Batch 13 deployed a separate, versioned BNetzA-source-grain BBSR
charging layer. It did not modify the BNetzA-to-KBA Crosswalk, join KBA stock,
allocate Trier stock, or assign a BBSR type to a KBA registration region.

The deployment was committed transactionally after read-only preflight, backup
validation, independent reconciliation, and a repeat execution.

## Objects and grains

| Object | Grain | Rows |
|---|---|---:|
| `reference.bnetza_bbsr_district_bridge_2025` | One original BNetzA state/district combination | 401 |
| `analytics.charging_by_bbsr_district_2025` | One original BNetzA state/district combination with charging metrics and BBSR reference enrichment | 401 |
| `analytics.charging_by_bbsr_type_2025` | One BBSR settlement-type category, plus `UNCLASSIFIED` | 5 |

The bridge uses a unique composite source key only. BBSR administrative and
Kreisregion codes are VARCHAR values; leading zeroes are preserved and BBSR
codes are not required to be globally unique.

The district view keeps the BNetzA infrastructure date
(`2026-09-30`) and BBSR reference date (`2025-12-31`) visible. It aggregates
equipment and point rows separately, uses `(source_id, excel_row)` and
`(source_id, equipment_excel_row)` as the equipment-to-point keys, retains all
equipment statuses, and classifies each point once from the maximum valid token
in its semicolon-separated `connector_power_raw` value. Decimal commas are
normalized before parsing.

## Bridge provenance and coverage

The reproducible bridge is [data/reference/bnetza_bbsr_bridge_2025.csv](../data/reference/bnetza_bbsr_bridge_2025.csv), with its deterministic metadata in
[data/reference/bnetza_bbsr_bridge_2025_manifest.json](../data/reference/bnetza_bbsr_bridge_2025_manifest.json).
The generation script independently rechecked the Batch 12 `PATH_A` evidence
against [data/reference/bbsr_settlement_types_2025.csv](../data/reference/bbsr_settlement_types_2025.csv)
using state, administrative form, and normalized administrative identity. KBA
codes were not used as assignment proof.

| Bridge status | Districts | Equipment | Charging points |
|---|---:|---:|---:|
| `VERIFIED_COMPATIBLE` | 399 | 117,077 | 210,262 |
| `CONDITIONAL_VINTAGE` — Main-Kinzig-Kreis | 1 | 439 | 740 |
| `UNRESOLVED` — Hanau | 1 | 146 | 251 |
| **Total** | **401** | **117,662** | **211,253** |

The BBSR settlement type is populated for the 399 verified rows. Main-Kinzig's
pre-change BBSR administrative and Kreisregion code is retained as evidence,
but its settlement type is intentionally NULL. Hanau has no separate row in the
BBSR 2025 vintage, so its BBSR fields and type remain NULL. The two rows form
the `UNCLASSIFIED` reporting group.

Trier city and Trier-Saarburg remain separate BNetzA rows with BBSR types 1 and
3 and 201 and 302 charging points respectively. No KBA stock is joined or
allocated between them.

## National reconciliation

| Measure | Result |
|---|---:|
| Equipment | 117,662 |
| Charging points | 211,253 |
| Normal points, maximum declared power <=22 kW | 156,155 |
| Fast points, maximum declared power >22 kW | 55,098 |
| Points >=150 kW | 40,950 |
| Points >=350 kW | 6,950 |
| Unclassifiable point power | 0 |
| Declared equipment nominal power | 9,215.4173 MW |

All 401 district rows and all five reporting groups reconcile to these totals.
No equipment or charging point was duplicated or silently excluded.

## Settlement-type KPIs

Shares in the `fast_point_share_pct` and `high_power_point_share_pct` columns
are percentages within the category. The
`share_of_all_registered_charging_points_pct` denominator is all 211,253
registered charging points, explicitly including `UNCLASSIFIED`.

| Code | Settlement category | Districts | Equipment | Points | Normal | Fast | >=150 kW | >=350 kW | Fast share | >=150 share | Nominal power (MW) | Share of all points |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | kreisfreie Großstadt | 67 | 39,483 | 69,207 | 56,249 | 12,958 | 9,599 | 1,174 | 18.72% | 13.87% | 2,347.6271 | 32.760245% |
| 2 | städtischer Kreis | 131 | 41,912 | 77,651 | 56,968 | 20,683 | 15,263 | 2,554 | 26.64% | 19.66% | 3,471.4490 | 36.757348% |
| 3 | ländlicher Kreis mit Verdichtungsansätzen | 98 | 18,042 | 32,342 | 21,788 | 10,554 | 7,877 | 1,446 | 32.63% | 24.36% | 1,669.6451 | 15.309605% |
| 4 | dünn besiedelter ländlicher Kreis | 103 | 17,640 | 31,062 | 20,537 | 10,525 | 7,884 | 1,699 | 33.88% | 25.38% | 1,663.2141 | 14.703697% |
| UNCLASSIFIED | Hanau + Main-Kinzig-Kreis | 2 | 585 | 991 | 613 | 378 | 327 | 77 | 38.14% | 33.00% | 63.4820 | 0.469106% |
| **Total** | **All source districts** | **401** | **117,662** | **211,253** | **156,155** | **55,098** | **40,950** | **6,950** | — | — | **9,215.4173** | **100.000001%*** |

\* The displayed total is the sum of six-decimal rounded category shares; the
unrounded denominator is exactly all 211,253 points.

These are descriptive infrastructure measures for BBSR-classifiable BNetzA
source districts. They are not BBSR-to-KBA measures, do not contain BEV/PHEV
stock, and do not support BEV-per-point ratios by BBSR category.

## Backup and deployment evidence

The verified pre-deployment backup is
[data/backups/ev_charging_pre_batch13_20261102_222612.duckdb](../data/backups/ev_charging_pre_batch13_20261102_222612.duckdb)
(ignored by Git), size 39,858,176 bytes, SHA-256
`19753969b21a581fba79cd4fcff8d46cf7afa3354c27cb0bfce33db0f6ad4d43`.
No WAL or conflicting open database handle was detected. The backup was opened
read-only and reconciled to the baseline before the primary database was opened
for writing.

Relevant fingerprints:

| Artifact | SHA-256 |
|---|---|
| BNetzA XLSX, 2026-09-30 | `1e82c1734b17e17e51092a0f9460a5e204888569fb12aa5940b30e9cdb726342` |
| BBSR XLSX, geographic stand 2025-12-31 | `083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525` |
| BBSR derived CSV | `e35c57da8d8f675fa132b629e6dda43180a18e5b78b95e1e72de30069a062e65` |
| Batch 12 Path A audit CSV | `f4d681fc81ac700b73521b9da81689073df183f6664866e2dcb9397a89d9d644` |
| Batch 13 bridge CSV | `b8a5e025fe74b2dfec9b338c7ae79648776bd6150dbf8f979518329c2baa3846` |
| Primary database before deployment | `19753969b21a581fba79cd4fcff8d46cf7afa3354c27cb0bfce33db0f6ad4d43` |

## Validation

- `python -m py_compile scripts/13_deploy_bbsr_charging_layer.py` passed.
- The deployment SQL executed successfully in a transaction.
- The deployment script passed twice; the second run did not duplicate rows or objects.
- Independent read-only queries confirmed bridge 401 rows, district 401 rows,
  category 5 rows, national reconciliation, unclassified totals, Trier
  separation, and absence of KBA/BEV/PHEV references in the new view definitions.
- `reference.bnetza_kba_district_crosswalk_2026`,
  `analytics.charging_by_kba_district_2026_09_30`,
  `analytics.kba_district_charging_vs_bev_2026`, and
  `analytics.charging_by_state` matched the verified pre-deployment backup in
  schema, SQL definition, row count, and normalized data snapshot.
- `git diff --check` passed before handoff.

## Known limitations and next analysis

The BBSR vintage is 2025 while infrastructure is 2026. Main-Kinzig is
therefore deliberately unclassified for category reporting, and Hanau remains
unresolved. The BNetzA register is not exhaustive, declared power is not
delivered energy, and the category shares are not utilization or demand
measures.

The next suitable analysis is a dated post-2026 BBSR reference or an
authoritative product-specific KBA-to-administration bridge. Any future KBA
integration must keep Path A separate, retain mixed/vintage statuses, and keep
Trier stock unallocated. Tableau and KBA–BBSR integration were not implemented
in Batch 13.
