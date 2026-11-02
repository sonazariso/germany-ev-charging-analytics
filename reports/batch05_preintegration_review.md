# Batch 05 — Pre-integration geographic model review

## Objective and scope

This batch validated the proposed geographic analytical model before any permanent DuckDB modification. The scope was limited to the existing BNetzA 2026-09-30 snapshot, the three existing KBA FZ 27.15 snapshots, the approved Crosswalk CSV, read-only SQL validation, and documentation of a minimal permanent-layer design.

The source workbooks, `data/reference/bnetza_kba_district_crosswalk_2026.csv`, and `data/analytics/ev_charging.duckdb` were not modified. No `CREATE`, `ALTER`, `DROP`, `INSERT`, `UPDATE`, or `DELETE` statement was executed.

## 1. Git verification and project state

- The worktree was clean at the start of the batch: `## main`.
- `HEAD` was `83ef56efa0870cf84f48d17f7f9eb3932ee56b9c`, and `git cat-file -t` confirmed that the requested commit exists.
- The Batch 04 documentation baseline was present, including `AGENTS.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, the English `docs/` set, the phase reports, the tracked Crosswalk CSV, and the existing validation scripts.
- No raw XLSX workbook, DuckDB file, WAL, or untracked source export was tracked by Git.
- `git remote -v` returned no remote configuration.

The Batch 05 changes are documentation and this review report only. The final staged-path review is recorded in the handoff after validation.

## 2. Read-only validation method

The checks used one DuckDB connection opened as:

~~~python
duckdb.connect("data/analytics/ev_charging.duckdb", read_only=True)
~~~

The Crosswalk CSV was read as a query-scoped relation with `kba_district_code` forced to `VARCHAR`. The regional query used CTEs for source geography, source-aware equipment-to-point joining, point-power parsing, equipment aggregation, point aggregation, and the final KBA-code relation.

For every charging point, the query:

1. split `connector_power_raw` on semicolons;
2. trimmed each token and replaced decimal commas with decimal points;
3. parsed numeric tokens with a tolerant numeric cast;
4. used the maximum valid token within the point; and
5. classified the point once using that maximum.

Connector powers were never summed. Equipment nominal power was aggregated from `core.charging_equipment` separately from point-level measures. The equipment-to-point join used both `source_id` and Excel row.

The temporary DuckDB 1.4.5 environment used for validation was created outside the repository and is not a project artifact.

## 3. Regional power KPI results

The CTE relation returned exactly 400 mapped KBA district-code rows. The complete result was consumed by the assertions below; the table shows the national reconciliation and selected KBA-code rows for review.

| Measure | Result |
|---|---:|
| KBA district-code rows | 400 |
| Equipment records | 117,662 |
| Charging-point slots | 211,253 |
| Normal points, maximum declared power <=22 kW | 156,155 |
| Fast points, maximum declared power >22 kW | 55,098 |
| Fast-point percentage | 26.08% |
| Points with maximum declared power >=150 kW | 40,950 |
| High-power percentage | 19.38% |
| Points with maximum declared power >=350 kW | 6,950 |
| Declared equipment nominal power | 9,215.4173 MW |
| Points without a valid maximum parsed power | 0 |

The band identities passed for every regional row: normal plus fast equals the point-slot count, the >=150 kW band is nested within fast points, and the >=350 kW band is nested within the >=150 kW band. Regional percentages use the point-slot denominator.

### Selected KBA-code rows

These are selected outputs, not a ranking claim. All 400 rows were included in the validation relation.

| KBA code | Observed KBA label | Equipment | Points | Normal <=22 kW | Fast >22 kW | >=150 kW | >=350 kW | Fast % | High-power % | Nominal MW |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 11000 | BERLIN | 4,999 | 7,644 | 6,388 | 1,256 | 1,000 | 136 | 16.43% | 13.08% | 215.4151 |
| 02000 | HAMBURG | 3,419 | 6,141 | 5,182 | 959 | 850 | 119 | 15.62% | 13.84% | 212.4597 |
| 03241 | HANNOVER | 1,972 | 3,635 | 2,782 | 853 | 605 | 108 | 23.47% | 16.64% | 155.1130 |
| 07211 | Trier shared region | 276 | 503 | 344 | 159 | 127 | 16 | 31.61% | 25.25% | 24.8224 |
| 06632 | HERSFELD-ROTENBURG | 187 | 314 | 96 | 218 | 192 | 60 | 69.43% | 61.15% | 36.5590 |
| 16062 | NORDHAUSEN | 87 | 158 | 49 | 109 | 93 | 8 | 68.99% | 58.86% | 15.0810 |

The two selected high-share rows are included to make the point denominator visible; they are not evidence of utilization, availability, or service quality.

## 4. Geographic and vehicle-stock reconciliation

| Check | Expected | Observed | Status |
|---|---:|---:|---|
| BNetzA source state/district combinations | 401 | 401 | PASS |
| Crosswalk rows | 401 | 401 | PASS |
| Mapped source combinations | 401 | 401 | PASS |
| Distinct mapped KBA codes | 400 | 400 | PASS |
| Explicit provisional mappings | 24 | 24 | PASS; provisional retained |
| Source-aware point join rows | 211,253 | 211,253 | PASS |
| Unmapped equipment rows | 0 | 0 | PASS |
| Unmapped point rows | 0 | 0 | PASS |
| KBA rows per stock date | 400 | 400 | PASS |
| KBA code/date uniqueness | one row per key | 0 duplicate keys | PASS |
| Combined KBA code/date rows | 1,200 | 1,200 | PASS |
| Orphan point rows in source-aware join | 0 | 0 | PASS |
| Shared Trier source rows | 2 | 2 | PASS |
| Shared Trier stock rows | 1 per date | 3 total | PASS |

The 24 provisional mappings are 22 explicit aliases plus the two source rows that share KBA registration-region code `07211`. They remain flagged by `verification_status`; no row was promoted to official verification.

The combined relation retained one infrastructure row per KBA code and one KBA stock row per code/date. The KBA stock totals reconciled as follows:

| KBA stock measure | 2026-01-01 | 2026-04-01 | 2026-07-01 |
|---|---:|---:|---:|
| District BEV stock | 2,031,870 | 2,167,111 | 2,362,218 |
| District PHEV stock | — | — | 1,225,241 |

The January-to-July district BEV change is +330,348 (+16.26%). Vehicle stock was not summed across the three dates. The infrastructure snapshot remains 2026-09-30 beside every KBA date, so January, April, and July BEV-to-point ratios are cross-snapshot descriptive indicators, not contemporaneous coverage measures.

## 5. SQL design corrections and proposed objects

The proposed objects are documented in [docs/geographic-layer-design.md](../docs/geographic-layer-design.md). They are not deployed.

The design requires:

- a permanent, versioned reference relation with one row per BNetzA source geography and explicit mapping/verification fields;
- separate equipment and point aggregates at `(bnetza_source_id, kba_district_code)`;
- maximum-per-point power parsing from all semicolon-separated tokens;
- source-aware joins on `(source_id, excel_row)`;
- aggregate-before-join to KBA stock;
- one combined row per KBA code and actual KBA stock date; and
- visible provisional and unmapped quality flags.

The existing `analytics.charging_by_state` view remains unsafe for multiple BNetzA snapshots because its point subquery groups by `equipment_excel_row` without `source_id` and joins on Excel row alone. Batch 05 documented the minimal correction but did not modify the view.

## 6. Temporal and interpretation rules

- BNetzA infrastructure reference date: `2026-09-30`.
- KBA district stock dates: `2026-01-01`, `2026-04-01`, and `2026-07-01`.
- The Crosswalk CSV's `kba_reference_date` is matching evidence for the local July release; it is not a substitute for the actual KBA stock date.
- Infrastructure measures must not be summed across KBA dates.
- Registered BEV/PHEV stock is not new sales.
- Declared power bands are not utilization, energy delivery, availability, reliability, or queue-time measures.
- The provisional crosswalk does not establish official administrative-boundary equivalence.

## 7. Documentation changes

- Added [docs/geographic-layer-design.md](../docs/geographic-layer-design.md) with proposed object names, grains, keys, SQL, power-band logic, quality flags, acceptance checks, and backup/rollback requirements.
- Updated [docs/geographic-methodology.md](../docs/geographic-methodology.md) with Batch 05 evidence and temporal rules.
- Updated [docs/kpi-catalog.md](../docs/kpi-catalog.md) with the KBA-code regional validation grain and non-contemporaneous-date warning.
- Updated [docs/data-quality.md](../docs/data-quality.md) with the read-only regional validation results and the still-open state-view issue.
- Updated [PROJECT_STATUS.md](../PROJECT_STATUS.md) and [CHANGELOG.md](../CHANGELOG.md).

No data dictionary change was needed because no schema or important field changed. No new decision was approved, so `docs/decisions.md` remains a pending-decision log rather than recording an unapproved deployment.

## 8. Validation commands and results

| Validation | Result |
|---|---|
| `git cat-file -t 83ef56efa0870cf84f48d17f7f9eb3932ee56b9c` | PASS; commit exists |
| Temporary DuckDB CTE assertion harness using `read_only=True` | PASS; all regional, mapping, date, and reconciliation assertions passed |
| `scripts/batch_analysis.py --demo --preview-rows 3` | PASS; 4 passed, 0 failed, connection closed read-only |
| `git diff --check` | PASS |

The DuckDB validation was performed with DuckDB 1.4.5 in a temporary environment outside the repository. No generated report, virtual environment, database, WAL, raw workbook, or uncontrolled export was added to the worktree.

## 9. Validation status and remaining decisions

Batch 05 pre-integration validation is complete. The analytical evidence is sufficient to proceed to an approval decision, not to deploy the layer automatically.

Before Batch 06 deployment work, the project owner still needs to decide:

1. whether to approve the proposed reference schema and analytical view names;
2. how the 24 provisional mappings and shared Trier code should be displayed in final KPIs;
3. whether to create the required backup and deploy the permanent objects in a new database copy;
4. whether to repair `analytics.charging_by_state` as a separate approved change; and
5. whether maximum-per-point power parsing should remain a view expression or become an approved reusable core field.

No remote was added and nothing was uploaded.
