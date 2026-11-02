# Data quality and validation

This document separates measured checks from recommendations. The original reports remain the detailed evidence:

- [Phase 01 source profile](../reports/phase01_data_profile.md)
- [Phase 02 schema inspection](../reports/phase02_schema_inspection.md)
- [Phase 03 DuckDB validation](../reports/phase03_duckdb_validation.md)
- [Batch 03 crosswalk validation](../reports/batch03_crosswalk_validation.md)
- [Batch 03 batch-runner demonstration](../reports/batch03_batch_runner_demo.md)

## Verified checks

### Source preservation

- Four source workbooks are present locally and match the source manifest.
- The download inventory records file sizes and SHA-256 hashes.
- Workbook profiling streamed every worksheet row and retained only a capped preview in the profile artifacts.
- The DuckDB raw schema retains 117,670 populated BNetzA rows and 61,797 populated KBA rows.
- No source workbook was changed in Batch 04.

### Row-count reconciliation

| Check | Expected/current result | Status |
|---|---:|---|
| BNetzA populated source rows | 117,670 | PASS |
| Normalized equipment rows | 117,662 | PASS |
| Populated point slots | 211,253 | PASS |
| Declared point count sum | 211,253 | PASS |
| KBA district rows | 1,200 = 400 per date | PASS |
| KBA state fuel rows | 378 | PASS |
| KBA postcode rows | 24,586 | PASS |
| KBA municipality rows | 32,229 | PASS |
| Distinct BNetzA state values | 16 | PASS |

The eight-row difference between all populated BNetzA rows and normalized equipment rows is the workbook title, notes, update metadata, and header region; it is not silently treated as equipment.

### Equipment and point relationships

- Every current equipment row has a source equipment ID.
- Equipment IDs are unique in the current snapshot.
- The sum of declared points equals the number of populated point slots.
- No equipment-level declared/slot mismatch was observed.
- No orphan point rows were observed.
- No duplicate point identity of source_id, equipment_excel_row, and point_number was observed.
- The relationship uses source_id plus Excel row, not equipment ID alone.

### Connector-power parsing

The source contains point-level connector-power text, including semicolon-separated values such as 22; 22 or 150; 150. The normalized connector_power_kw_single helper is null for multi-value raw text by design. A read-only maximum-per-point parser over connector_power_raw classified all 211,253 point rows in the current snapshot and reconciled the bands:

| Band | Point slots |
|---|---:|
| Maximum declared power <=22 kW | 156,155 |
| Maximum declared power >22 kW | 55,098 |
| Maximum declared power >=150 kW | 40,950 |
| Maximum declared power >=350 kW | 6,950 |
| Sum of normal and fast bands | 211,253 |

These are declared-power classifications. They are not connector counts, simultaneous output, utilization, or energy delivery.

### State and national totals

- The state infrastructure totals reconcile to 117,662 equipment rows and 211,253 point slots.
- The state-level power analysis reconciles to the national point count when each point is classified once by its maximum declared power.
- Equipment nominal power is summed from core.charging_equipment only. Summing it after joining to point rows would multiply equipment power and is prohibited.
- Current equipment status counts are 117,642 In Betrieb and 20 In Wartung.

### KBA coverage and uniqueness

- core.kba_district_ev_stock contains 400 district codes for each of 2026-01-01, 2026-04-01, and 2026-07-01.
- District codes are unique within each reference date.
- core.kba_state_fuel_stock contains 18 labels per date: the 16 states plus Deutschland and Sonstige.
- The district total and state-level Deutschland total differ because they are different reporting structures. For July 2026, the district BEV sum is 2,362,218 and the state-level Deutschland BEV total is 2,365,047; Sonstige accounts for 2,829 in the current state-level structure.
- No KBA district, postcode, municipality, and state tables are added together as if they were additive partitions.

### Crosswalk coverage

- 401 BNetzA state/district combinations are retained.
- 401 crosswalk rows are present and mapped in the current snapshot.
- 400 distinct KBA codes are covered.
- Only 07211 is assigned to two BNetzA source rows.
- No BNetzA combination is multiply assigned.
- The aggregate-before-join check preserves 2,362,218 KBA district BEVs and 211,253 point slots.
- The 22 aliases and two Trier rows are explicitly marked provisional or local-snapshot conventions.

These assertions validate coverage, retention, and join arithmetic. They do not establish official geographic correctness.

### Known coordinate exception

All current equipment rows have non-null coordinates. One row falls outside a broad Germany check because its longitude is 4.0. The source record is not corrected or removed; it remains an exception for future coordinate review.

## Existing source-aware JOIN issue

analytics.charging_by_state calculates point counts in a subquery grouped only by equipment_excel_row and joins it to equipment on Excel row alone. It omits source_id. With one BNetzA snapshot the current totals reconcile, but the view is unsafe for multiple BNetzA source IDs because equal Excel row numbers could cross-match. Batch 04 documents this issue and does not modify the view.

## Meaning of the existing PASS results

The Batch 03 report’s PASS results are meaningful when read as:

- row and code coverage assertions;
- source-to-core retention and declared-point reconciliation;
- uniqueness and aggregate-before-join arithmetic;
- local state/type/name matching against the July workbook.

They are not proof that a provisional alias is an official boundary mapping, and they are not an independent audit of the authority’s geographic definitions. That distinction is carried into the geographic methodology and KPI statuses.

## Recommendations and open quality work

- Obtain an authoritative administrative crosswalk or independent human review for all provisional aliases and the shared Trier registration region.
- Repair or replace the source-aware state view before loading multiple BNetzA snapshots.
- Decide whether point-power parsing should become a documented reusable SQL view or a new approved core field. Do not overwrite the raw text.
- Reconcile the 2,829 state-level Sonstige BEVs and the passenger-car denominator difference before a national cross-grain KPI is published.
- Review the one coordinate exception without altering the source record.
- Re-run the same validation suite after any approved schema or source-date change.
