# Data quality and validation

This document separates measured checks from recommendations. The original reports remain the detailed evidence:

- [Phase 01 source profile](../reports/phase01_data_profile.md)
- [Phase 02 schema inspection](../reports/phase02_schema_inspection.md)
- [Phase 03 DuckDB validation](../reports/phase03_duckdb_validation.md)
- [Batch 03 crosswalk validation](../reports/batch03_crosswalk_validation.md)
- [Batch 03 batch-runner demonstration](../reports/batch03_batch_runner_demo.md)

## Verified checks

### Source preservation

- Four primary BNetzA/KBA workbooks and one separately handled BBSR reference workbook are present locally and match the source manifest.
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

## Batch 23 web-dashboard validation boundary

The web dashboard consumes the validated Batch 19/21 export contracts rather
than opening DuckDB in the browser. Its preparation script repeats the
presentation-layer checks for six inputs, including source checksums, expected
rows/columns, 16-state membership, national/state totals, 33 history rows and
the four mutually exclusive power bands. The output preserves source dates,
roles and validation metadata in `web/public/data/dashboard.json`.

This is a rendering validation, not a new source-quality claim. It does not
turn the published BNetzA register into a complete utilization feed, does not
resolve the KBA/BBSR boundary limitations, and does not change the canonical
KPI statuses. Details are in
[`reports/batch23_web_dashboard_validation.md`](../reports/batch23_web_dashboard_validation.md).

### Batch 05 pre-integration geographic validation

Batch 05 repeated the geographic checks with one DuckDB connection opened read-only and SELECT/CTE queries only. No `CREATE`, `ALTER`, `DROP`, `INSERT`, `UPDATE`, or `DELETE` statement was executed.

| Check | Observed result | Status |
|---|---:|---|
| BNetzA source geographies | 401 | PASS |
| Crosswalk rows / mapped source geographies | 401 / 401 | PASS |
| Distinct mapped KBA codes | 400 | PASS |
| Explicit provisional mappings | 24 = 22 aliases + 2 Trier rows | PASS; still provisional |
| Equipment rows retained through mapping | 117,662 | PASS |
| Point rows after source-aware equipment join | 211,253 | PASS |
| Orphan point rows on source-aware key | 0 | PASS |
| Point rows without a valid maximum parsed power | 0 | PASS |
| Regional rows | 400 | PASS |
| Combined KBA code/date rows | 1,200 = 400 × 3 | PASS |
| Duplicate KBA code/date keys | 0 | PASS |
| July district BEV stock after aggregate-before-join | 2,362,218 | PASS |

The regional query classified each point from all semicolon-separated `connector_power_raw` tokens after decimal-comma normalization and used `MAX` within the point. It did not use `connector_power_kw_single` as the headline parser and did not sum connector powers. The resulting bands were 156,155 points at or below 22 kW, 55,098 above 22 kW, 40,950 at or above 150 kW, and 6,950 at or above 350 kW. Equipment nominal power was aggregated from the equipment relation separately and totalled 9,215.4173 MW.

The 2026-09-30 infrastructure measures were kept separate from KBA stock dates 2026-01-01, 2026-04-01, and 2026-07-01. Infrastructure values repeat beside each KBA date in the 1,200-row combined grain; they are not summed across the three dates. January and April BEV-to-point ratios must not be described as contemporaneous infrastructure coverage, and the July comparison is still cross-snapshot because the infrastructure date is September.

The design proposal and deployment history are in [geographic-layer-design.md](geographic-layer-design.md). The Crosswalk CSV was not modified.

### Batch 06 deployed geographic validation

Batch 06 created a verified pre-change backup, deployed the permanent reference and analytics objects in one DuckDB transaction, and ran an independent read-only validation process. The backup was byte-preserving and readable from a separate read-only connection; its equipment, point, KBA, and state-view counts matched the pre-deployment baseline. The deployment script is repeat-safe: a second run inspected and validated existing objects rather than duplicating the table or blindly replacing validated geographic views.

| Check | Observed result | Status |
|---|---:|---|
| Reference table rows / unique BNetzA keys | 401 / 401 | PASS |
| Unique KBA codes / provisional rows | 400 / 24 | PASS; provisional retained |
| Regional view rows | 400 | PASS |
| Regional equipment / point / declared point totals | 117,662 / 211,253 / 211,253 | PASS |
| Normal / fast points | 156,155 / 55,098 | PASS |
| Points at least 150 / 350 kW | 40,950 / 6,950 | PASS |
| Points without valid maximum parsed power | 0 | PASS |
| Combined KBA code/date rows | 1,200 | PASS |
| Duplicate combined `(kba_district_code, kba_reference_date)` keys | 0 | PASS |
| July district BEV stock | 2,362,218 | PASS |
| July shared Trier code 07211 BEV stock | 7,869 counted once | PASS |

The direct core recomputation matched the deployed regional view. The state-view comparison retained all 16 states and every baseline equipment, declared-point, and populated-point value. The exact backup path, hash, and validation evidence are recorded in [reports/batch06_geographic_deployment.md](../reports/batch06_geographic_deployment.md).

### Batch 07 authoritative crosswalk review

Batch 07 reviewed all 24 provisional Crosswalk rows against the Destatis GV-ISys Q3 2026 administrative classification and the official KBA FZ 27.15 July 2026 workbook. The detailed matrix and source URLs are in [reports/batch07_authoritative_crosswalk_review.md](../reports/batch07_authoritative_crosswalk_review.md).

| Review result | Rows | Quality interpretation |
|---|---:|---|
| Independently supported at row/entity level | 22 | Same state, official district identity, five-digit key, and identifiable KBA label variant. This is not a universal KBA-code = AGS/ARS claim. |
| Partially supported shared-region mappings | 2 | Trier city and Trier-Saarburg are distinct Destatis units but one KBA FZ 27.15 registration-region row. |
| Unresolved row identities | 0 | No reviewed row lacked an identifiable official target. |

All 24 operational rows remain provisional. The review did not modify the CSV or DuckDB table. Destatis separates Trier city `07211` from Trier-Saarburg `07235`; KBA FZ 27.15 reports `07211 TRIER-SAARBURG` and 7,869 July 2026 BEVs for the combined KBA row. A common registration office confirms shared administration, but not a city/county allocation of that stock. The local KBA FZ 27.17 presentation also uses `07211 TRIER,STADT` for municipality rows, so KBA display labels must not be used alone as administrative definitions.

This review resolves the evidence classification, not the owner decision to promote any mapping. Future changes must keep AGS, ARS, and KBA registration-region keys in explicitly named fields and preserve the aggregate-before-join rule.

### Batch 08 code and boundary verification

Batch 08 added an independent evidence review without changing operational data or statuses. The full matrix and source register are in [reports/batch08_geographic_code_verification.md](../reports/batch08_geographic_code_verification.md).

| Review result | Rows / result | Quality interpretation |
|---|---:|---|
| Alias rows with direct row-level code evidence | 22 | Same dated five-digit KBA key and Destatis Kreis component, state, type, and identifiable entity; not a universal AGS/ARS equivalence. |
| Aliases supported only at entity level | 0 | The two Trier rows are instead combined-region evidence. |
| Unresolved or conflicting alias identities | 0 | No identity gap was found; the universal code-system relationship remains unproven. |
| Hanau BNetzA source rows | 2 | Separate `Kreisfreie Stadt Hanau` and `Landkreis Main-Kinzig-Kreis` rows in the 2026-09-30 source. |
| Hanau KBA FZ 27.15 rows | 2 per snapshot | Separate `06415` and `06435` rows on all three 2026 dates. |
| Trier KBA July BEV stock | 7,869 once | Combined `07211 TRIER-SAARBURG` registration-region stock; no city/county allocation. |

Hanau therefore has no observed current-snapshot coverage mismatch. Historical impact is unknown because the current model contains only the three 2026 FZ 27.15 snapshots. The 400-code model remains defensible only when described as a KBA registration-region model. A historical boundary-vintage note is required for any older or cross-product comparison.

### Batch 09 BBSR feasibility screen

Batch 09 inspected the official BBSR `raumgliederungen-referenzen-2025.xlsx`
reference workbook outside the repository and compared its `Kreisreferenz` keys
with the local KBA FZ 27.15 July 2026 codes. This was a read-only documentation
check; no BBSR rows were loaded into DuckDB.

| Check | Observed result | Quality interpretation |
|---|---:|---|
| BBSR 2025 Kreis rows | 400 | Official reference-table rows at geographic stand 31.12.2025. |
| BBSR Kreisregion keys | 362 | Classification basis is not identical to 400 KBA registration codes. |
| Compact BBSR class domain | 1–4 | Use source fields `KTU2025`/`KTU_NAME`; the differentiated five-category fields are not the target. |
| KBA/BBSR five-digit prefix intersections | 399 of 400 KBA codes | Audit screen only; not an official code-system equivalence. |
| KBA-only code | `06415` Hanau | 2025 BBSR vintage has no separate Hanau row after the 2026 boundary change. |
| BBSR-only code | `07235` Trier-Saarburg | KBA combines the source area with Trier city under registration code `07211`. |
| Mixed BBSR type at a KBA code | `07211`: BBSR type 1 and type 3 components | Future KBA-level category must be `mixed_or_unresolved`; do not duplicate or allocate stock. |

The prefix comparison is not a coverage KPI. It must not promote the 22 aliases,
convert a KBA code into AGS/ARS, or permit name-only joins. Future validation must
store the BBSR version, effective date, code system, compatibility status, and
source URL, and must reject a single category for mixed or incompatible vintages.
The full evidence and proposed checks are in
[reports/batch09_bbsr_feasibility.md](../reports/batch09_bbsr_feasibility.md).

### Batch 10 BBSR reference validation

Batch 10 read all six worksheets in the official BBSR workbook and built the
separate deterministic reference CSV without changing DuckDB, the existing
Crosswalk, or KPI logic.

| Check | Observed result | Status |
|---|---:|---|
| Source file size / SHA-256 | 8,768,335 bytes / 083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525 | PASS |
| Geographic reference date / workbook stand | 2025-12-31 / 2026-09-11 | PASS |
| Worksheets inspected | 6 | PASS |
| Kreisreferenz source rows / derived rows | 400 / 400 | PASS |
| Distinct administrative district codes | 400 | PASS |
| Distinct Kreisregion keys | 362 | PASS |
| Compact classification domain | 1, 2, 3, 4 | PASS |
| Compact type row counts | 68 / 131 / 98 / 103 | PASS |
| Duplicate primary-grain keys | 0 | PASS |
| Source rows not emitted | 0 | PASS |
| Code/label or Kreisregion inconsistencies | 0 | PASS |
| Multi-district Kreisregion groups preserved | 36 | PASS |

The raw workbook remains ignored under data/raw/bbsr/. The derived checksum,
original sheet/column inventory, and special-case evidence are recorded in
data/reference/bbsr_source_manifest.json and the full report is
reports/batch10_bbsr_reference_validation.md. The 2025 BBSR vintage has no
Hanau row, retains Main-Kinzig-Kreis as type 2, and keeps Trier city type 1 and
Trier-Saarburg type 3 as separate rows. No BBSR type is assigned to KBA 07211.

### Batch 11 BBSR–KBA compatibility audit

The read-only Batch 11 audit is documented in
[reports/batch11_bbsr_kba_compatibility.md](../reports/batch11_bbsr_kba_compatibility.md)
and reproduced by
[scripts/11_audit_bbsr_kba_compatibility.py](../scripts/11_audit_bbsr_kba_compatibility.py).
The detailed 400-row output is explicitly non-operational:
[reports/batch11_bbsr_kba_compatibility_audit.csv](../reports/batch11_bbsr_kba_compatibility_audit.csv).

| Check | Result | Quality interpretation |
|---|---:|---|
| KBA regions audited | 400 | Every current KBA code is present once in the audit output. |
| BBSR administrative rows / Kreisregion keys | 400 / 362 | BBSR grain remains separate from KBA registration regions. |
| BBSR multi-district groups / mixed-type groups | 36 / 0 | 74 component rows; all groups are homogeneous within the 2025 BBSR source. |
| Audit statuses | 0 exact / 0 homogeneous / 1 mixed / 2 vintage / 397 unresolved / 0 conflicting | No unsupported status is promoted to the operational model. |
| Strict BBSR classification coverage | 0 regions / 0 points / 0 July BEVs | No authoritative dated KBA-to-BBSR bridge is present. |
| General KBA coverage denominator | 400 / 211,253 / 2,362,218 | Regions / charging points / July BEVs reconcile independently of BBSR classification. |

The 399 five-digit prefix intersections are retained as screening evidence only;
they are not a coverage KPI. Hanau `06415` and current Main-Kinzig-Kreis `06435`
are `VINTAGE_CONFLICT` because BBSR 2025 predates the 2026-01-01 boundary
change. Trier `07211` is `MIXED` because its shared KBA registration region
contains BBSR type 1 and type 3 components. Its 503 charging points and 7,869
July BEVs are counted once at the KBA code grain.

This audit does not change the Crosswalk, BBSR CSV, DuckDB, KPI formulas, or
Tableau readiness. Unresolved regions remain in every denominator, and no
classification or vehicle stock is estimated or allocated.

### Batch 12 two-path BBSR integration investigation

Batch 12 added a deterministic, read-only audit for the separate BNetzA-to-BBSR
and KBA-to-administration-to-BBSR paths. The detailed evidence is in
[reports/batch12_bbsr_integration_paths.md](../reports/batch12_bbsr_integration_paths.md),
the implementation is in
[scripts/12_audit_bbsr_integration_paths.py](../scripts/12_audit_bbsr_integration_paths.py),
and the 801-row output is explicitly non-operational:
[reports/batch12_bbsr_integration_paths_audit.csv](../reports/batch12_bbsr_integration_paths_audit.csv).

| Check | Observed result | Status / quality interpretation |
|---|---:|---|
| Path A source districts audited | 401 | Every BNetzA state/district combination is represented once. |
| Path A statuses | 399 verified / 1 conditional vintage / 1 unresolved / 0 mixed / 0 conflicting | Charging-only source-grain compatibility assessment; no production mapping. |
| Path A verified equipment coverage | 117,077 / 117,662 = 99.502813% | Conditional descriptive coverage with BNetzA/BBSR dates visible. |
| Path A verified point coverage | 210,262 / 211,253 = 99.530894% | Charging points counted at point grain; unresolved rows remain in denominator. |
| Path B KBA regions audited | 400 | Every unique KBA registration code is represented once. |
| Path B statuses | 0 exact / 0 homogeneous / 1 mixed / 2 vintage / 397 unresolved / 0 conflicting | No authoritative dated KBA-to-BBSR bridge was verified. |
| Path B strict verified coverage | 0 regions / 0 points / 0 July BEVs | No BBSR category or BBSR-based vehicle ratio is production-ready. |
| Path B denominator | 400 / 211,253 / 2,362,218 | KBA regions / charging points / July 2026 BEVs reconcile independently of classification. |

The Path A `UNRESOLVED` row is current Hanau because the BBSR 2025 reference has
no separate Hanau row; current Main-Kinzig-Kreis is `CONDITIONAL_VINTAGE` because
the 2025 BBSR stand predates the 2026-01-01 separation. Path B keeps KBA
`07211` as a mixed Trier/Trier-Saarburg registration region, counts its 503
charging points and 7,869 July BEVs once, and applies no allocation. The audit
preserves the BBSR 400-row / 362-Kreisregion baseline and does not treat
five-digit prefix similarity as code-system evidence.

The script opened DuckDB read-only, inspected actual columns, verified source
fingerprints, and produced deterministic output. No DuckDB, Crosswalk, BBSR
CSV, KPI, or operational status changed; no dataset was downloaded or imported.

### Batch 13 BBSR charging-only deployment

Batch 13 deployed the approved source-grain Path A layer with a verified backup
and transaction. The bridge and both views passed the following checks:

| Check | Result | Interpretation |
|---|---:|---|
| BNetzA bridge rows / unique source keys | 401 / 401 | Every source district remains represented once. |
| Bridge statuses | 399 verified / 1 conditional vintage / 1 unresolved | Main-Kinzig and Hanau remain visible exceptions. |
| Classifiable / unclassified districts | 399 / 2 | Only verified rows receive a BBSR type; unclassified is Hanau + Main-Kinzig. |
| Unclassified equipment / points | 585 / 991 | 0.497187% / 0.469106% of national totals. |
| BBSR district analytics rows | 401 | One row per original BNetzA state/district. |
| BBSR type summary rows | 5 | Types 1–4 plus `UNCLASSIFIED`; national point-share denominator includes all rows. |
| Point-power parse coverage | 211,253 / 211,253 | Maximum valid semicolon-token parser; 0 unclassifiable points. |
| National charging reconciliation | PASS | Equipment, points, bands, and 9,215.4173 MW reconcile. |
| Existing KBA object integrity | PASS | Crosswalk, KBA regional/combined views, and state view unchanged. |

The deployment was executed twice with the same bridge and verified backup; the
second execution did not duplicate objects or bridge rows. New BBSR views do
not reference KBA, BEV, or PHEV measures. Hanau does not inherit Main-Kinzig's
type, Main-Kinzig's pre-change code is retained without a type, and Trier city
and Trier-Saarburg remain separate without stock allocation.

### Batch 13.1 owner-approved scenario validation

Batch 13.1 adds a separate two-row reference and four-category scenario; it
does not alter the official Batch 13 baseline. The new deployment passed the
following additional controls:

| Check | Result | Interpretation |
|---|---:|---|
| Override CSV rows / scenario table rows | 2 / 2 | Exactly Hanau `06415` and Main-Kinzig `06435`. |
| Owner verification flags | 2 false / 0 true | Neither override is silently promoted to official verification. |
| Scenario district rows / source districts | 401 / 401 | Full source coverage with no omitted districts. |
| Duplicate scenario source districts | 0 | One row per BNetzA source state/district. |
| Scenario unclassified districts | 0 | All four analytical categories are populated. |
| Scenario category rows | 4 | Category district counts are 68 / 132 / 98 / 103. |
| Scenario national reconciliation | PASS | 117,662 equipment; 211,253 points; 156,155 normal; 55,098 fast; 40,950 >=150 kW; 6,950 >=350 kW; 9,215.4173 MW. |
| Hanau/Main-Kinzig moved coverage | 585 equipment / 991 points | Exact sum of the two database-derived source rows. |
| Trier treatment | PASS | Separate BBSR codes/types retained; 201 + 302 points; no KBA stock allocation. |
| Official/KBA baseline snapshots | PASS | Official Batch 13 views, Crosswalk, KBA views, and state view match the verified backup. |
| Repeat execution / deterministic result | PASS | Second deployment is idempotent; independent result hashes repeat. |

The official BBSR CSV and original bridge CSV remain checksum-stable. The
scenario reuses the validated Batch 13 source-aware joins and maximum-per-point
power parser; it contains no KBA vehicle-stock, BEV, or PHEV reference. Hanau
category 1 is an owner-approved analytical assumption, not an official BBSR
2025/2026 classification. Main-Kinzig category 2 is a historical carry-forward
with the 2026 Hanau-separation caveat.

### Batch 13.2 historical BBSR boundary harmonization validation

Batch 13.2 adds a separate historical target-unit layer after an independent
two-way audit of the 68-versus-67 discrepancy. The strict anti-join identifies
one BBSR-only Kassel city label and two BNetzA-only labels (Kassel city alias
and current Hanau); semantic alias normalization reconciles Kassel and leaves
Hanau as the genuine 2025/2026 vintage difference. Kreis versus Kreisregion
does not explain the discrepancy: 36 multi-district groups are type-homogeneous
and type 1 has no duplicated Kreisregion group.

| Check | Result | Interpretation |
|---|---:|---|
| Harmonization reference rows / unique source keys | 401 / 401 | Every BNetzA 2026 source component is represented once. |
| Historical BBSR target rows / distinct target codes | 400 / 400 | One target row per BBSR 2025 administrative unit after aggregation. |
| Historical type counts | 68 / 131 / 98 / 103 | Exact BBSR 2025 counts for compact types 1–4. |
| Hanau + remaining Main-Kinzig target | 2 components; 585 equipment / 991 points | Reconstructed to BBSR `06435000`, historical type 2 only. |
| Kassel city correction | `06611000`, type 1 | Preserved Batch 13 bridge remains unchanged; correction is new-layer only. |
| National charging reconciliation | PASS | 117,662 equipment; 211,253 points; all power bands and 9,215.4173 MW reconcile. |
| Existing Batch 13 / 13.1 / KBA snapshots | PASS | Protected object snapshots match pre-deployment state. |
| SQL KBA/BEV/PHEV reference check | PASS | New layer is charging-only and does not join vehicle stock. |
| Repeat deployment | PASS | Same verified reference and backup produce the same object results. |

The official Hessian law supports the exact historical boundary union effective
`2026-01-01`; official population series are context only. The new layer does
not manufacture an official 2026 Hanau BBSR classification. Full evidence,
population-vintage notes, comparison tables, and backup provenance are in
[`reports/batch13_2_hanau_geographic_harmonization.md`](../reports/batch13_2_hanau_geographic_harmonization.md).

### Known coordinate exception

All current equipment rows have non-null coordinates. One row falls outside a broad Germany check because its longitude is 4.0. The source record is not corrected or removed; it remains an exception for future coordinate review.

## Resolved source-aware JOIN issue

Before Batch 06, analytics.charging_by_state calculated point counts in a subquery grouped only by equipment_excel_row and joined on Excel row alone. Batch 06 corrected the subquery to group by `(source_id, equipment_excel_row)` and joined on both fields. The post-deployment result matches the independent source-aware aggregation and the recorded 16-state baseline. Future multi-snapshot loading must retain this key.

## Meaning of the existing PASS results

The Batch 03 report’s PASS results are meaningful when read as:

- row and code coverage assertions;
- source-to-core retention and declared-point reconciliation;
- uniqueness and aggregate-before-join arithmetic;
- local state/type/name matching against the July workbook.

They are not proof that a provisional alias is an official boundary mapping, and they are not an independent audit of the authority’s geographic definitions. That distinction is carried into the geographic methodology and KPI statuses.

## Recommendations and open quality work

- Obtain an authoritative administrative crosswalk or independent human review for all provisional aliases and the shared Trier registration region.
- Re-run the source-aware state-view validation if another BNetzA snapshot is added.
- Decide whether point-power parsing should become a documented reusable SQL view or a new approved core field. Do not overwrite the raw text.
- Reconcile the 2,829 state-level Sonstige BEVs and the passenger-car denominator difference before a national cross-grain KPI is published.
- Review the one coordinate exception without altering the source record.
- Re-run the same validation suite after any approved schema or source-date change.

## Batch 14 read-only analysis validation

Batch 14 uses only the harmonized BBSR analytical layer as its primary source:

- `analytics.charging_by_bbsr_district_2025_harmonized`: 400 unique historical
  target units.
- `analytics.charging_by_bbsr_type_2025_harmonized`: four category rows with
  target counts 68 / 131 / 98 / 103.
- The 400 target units represent 401 current BNetzA source components.

The read-only analyzer independently reconciled 117,662 equipment rows,
211,253 point rows, 156,155 normal points, 55,098 fast points, 40,950 points
at least 150 kW, 6,950 points at least 350 kW, and 9,215.4173 MW nominal
equipment power. It found zero unclassifiable points, zero duplicate equipment
keys, zero duplicate point keys, and zero orphan points. The harmonized view
contains no `UNCLASSIFIED` infrastructure and its SQL contains no KBA, BEV, or
PHEV dependency.

The Batch 14 fingerprint check matched the local BNetzA source workbook, BBSR
raw workbook, BBSR derived reference CSV, and Batch 13.2 harmonization CSV.
The script opened DuckDB with `read_only=True`; it created no database object
and did not change raw data, references, the Crosswalk, KBA objects, or vehicle
stock. Full evidence is in
[`reports/batch14_bbsr_charging_analysis.md`](../reports/batch14_bbsr_charging_analysis.md).

## Batch 15 KBA FZ 27 validation

Batch 15 independently checked the existing KBA raw/core objects and local
workbook fingerprints with a read-only DuckDB connection. All three releases
contain the expected 20 worksheets. The national/state reconciliation passed:
the 16 named states equal the 400 KBA registration-region rows for passenger
cars, BEVs and PHEVs, and adding `Sonstige` reproduces the national totals.

| Check | Result |
|---|---|
| KBA registration-region rows | 1,200 = 400 × 3 snapshots |
| Duplicate region/date rows | 0 |
| Region identity changes across snapshots | 0 |
| District numeric NULLs / zero denominators | 0 / 0 |
| January BEV baseline ≥1,000 for percentage ranking | 377 eligible / 23 disclosed exclusions |
| FZ 27.5 owner rows | 108 commercial/private rows; 54 published totals |
| Historical national observations | 33 deduplicated rows, 2018-07-01 to 2026-07-01 |
| KBA workbook fingerprint mismatches | 0 |

The three national residuals are explicit `Sonstige` reporting rows: BEV
2,390 / 2,606 / 2,829 and PHEV 1,442 / 1,501 / 1,622 for January / April /
July. FZ 27.5 totals retain an unallocated/unknown holder-group residual,
consistent with the publisher footnote; it is not silently assigned to private
or commercial ownership.

FZ 27.16 has unique postcode/date rows but missing numeric source cells and a
small July coverage change. FZ 27.17 has unique district-code/municipality-name
rows and all 400 district codes, but no municipality code, repeated names
across districts, and many missing numeric cells after source-dot parsing. The
two tables are therefore descriptive alternative grains, not replacement
denominators for FZ 27.15. Full evidence is in
[`reports/batch15_kba_ev_stock_analysis.md`](../reports/batch15_kba_ev_stock_analysis.md).

## Batch 16 state EV/charging validation

Batch 16 opened DuckDB with `read_only=True` and created no database object.
It calculated one charging row per federal state and one KBA vehicle row per
federal state before joining them. The KBA stock date is `2026-07-01`; the
BNetzA infrastructure date is `2026-09-30`.

| Check | Result | Status |
|---|---:|---|
| BNetzA equipment rows | 117,662 | PASS |
| Declared/populated points | 211,253 / 211,253 | PASS |
| Normal / fast points | 156,155 / 55,098 | PASS |
| Points >=150 / >=350 kW | 40,950 / 6,950 | PASS |
| Unclassifiable maximum point power | 0 | PASS |
| Declared equipment nominal power | 9,215.4173 MW | PASS |
| Equipment statuses | 117,642 `In Betrieb`; 20 `In Wartung`; 0 other/NULL | PASS; statuses retained without filtering |
| State charging rows | 16 distinct states | PASS |
| KBA FZ 27.2 rows | 126 = 18 geographies × 7 fuel rows | PASS |
| National / 16-state / Sonstige reconciliation | Exact for passenger cars, BEVs and PHEVs | PASS |
| KBA 400-region rows | 400 unique July codes; totals equal 16-state sum | PASS |
| Vehicle category control | Six mutually exclusive total rows; PHEV not added to `Hybrid insgesamt` | PASS |
| Duplicate/orphan/mismatched charging points | 0 / 0 / 0 | PASS |
| State join | 16 distinct states; no missing or duplicated join keys | PASS |
| Zero ratio denominators | 0 BEV or point denominators | PASS |
| Source fingerprints | 6 preserved workbook/reference fingerprints match | PASS |
| DuckDB byte hash | Start/end `5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3` | PASS |
| Deterministic repeat | Report and 3 CSV hashes identical on second execution | PASS |

The charging parser preserves the established definition: split each
semicolon-separated `connector_power_raw` value, parse numeric tokens, take the
maximum within one point, and classify that point once as normal (`<=22 kW`),
fast (`>22 kW`), >=150 kW or >=350 kW. Equipment nominal power is aggregated
from the equipment table separately from point rows. The full evidence is in
[`reports/batch16_state_ev_charging_alignment.md`](../reports/batch16_state_ev_charging_alignment.md).

## Batch 17 temporal and commissioning-date validation

Batch 17 opened DuckDB with `read_only=True` and did not create a table, view or
other database object. It audited the actual equipment-level
`commissioning_date_raw` and parsed `commissioning_date` fields, then joined
points to equipment with the source-aware key `(source_id, excel_row)` ↔
`(source_id, equipment_excel_row)`. No connector explosion was used.

| Check | Result | Status |
|---|---:|---|
| Commissioning equipment rows | 117,662 | PASS |
| Raw NULL / blank values | 0 / 0 | PASS |
| Parsed NULL / parsing failures | 0 / 0 | PASS |
| Non-numeric raw values | 0 | PASS; current values are retained Excel-style serial strings |
| Dates after BNetzA snapshot `2026-09-30` | 0 | PASS |
| Dates after survivor cutoff `2026-07-01` | 2,762 equipment; 4,888 points | PASS; complement disclosed |
| Dates exactly on cutoff | 80 equipment; 136 points | PASS; included by the inclusive cutoff |
| Minimum / maximum commissioning date | `1992-10-01` / `2026-09-30` | PASS; unusual early values retained |
| Duplicate equipment / point keys | 0 / 0 | PASS |
| Orphan points / equipment-point mismatches | 0 / 0 | PASS |
| Published point power unknowns | 0 | PASS |
| Published / survivor / later point partition | 211,253 = 206,365 + 4,888 | PASS |
| Published / survivor / later equipment partition | 117,662 = 114,900 + 2,762 | PASS |
| Equipment status filter | None | PASS; 20 `In Wartung` rows retained |
| Point-level activation date | Not available | Limitation; equipment commissioning is not point activation |

The retrospective cohort is reproducible at equipment grain but is not a
historical July point registry. Equipment removed before September is absent;
point additions or modifications after commissioning are not observable;
September status is not July operational availability; and historical opening
hours cannot be reconstructed. The cohort is not assumed to be an upper or
lower bound on actual July infrastructure.

The published September cohort contains 117,662 equipment and 211,253 points;
the survivor cohort contains 114,900 equipment and 206,365 points. Its power
bands are 152,981 normal, 53,384 fast, 39,543 at least 150 kW and 6,335 at
least 350 kW. Full year/month, state/status and sensitivity evidence is in
[`reports/batch17_temporal_kpi_validity.md`](../reports/batch17_temporal_kpi_validity.md)
and [`reports/batch17_equipment_commissioning_cohorts.csv`](../reports/batch17_equipment_commissioning_cohorts.csv).

## Batch 18 readiness validation

Batch 18 performed independent read-only checks before documenting publication
decisions. No DuckDB object, raw workbook, reference CSV or Crosswalk row was
written.

| Check | Result | Status |
|---|---:|---|
| Required Batch 17 commit present | `ed0320fc956ad5da733bf933c88dec22dcb7f4c7` | PASS |
| Initial worktree | Clean | PASS |
| Git remote | None configured | PASS |
| DuckDB access | `read_only=True` | PASS |
| Equipment / point counts | 117,662 / 211,253 | PASS |
| State / July KBA region counts | 16 / 400 | PASS |
| Source/reference fingerprints | Match prior Batch 16/17 evidence | PASS |
| DuckDB hash | `5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3` | PASS |
| KPI register rows / columns | 59 / 19 | PASS |
| KPI register field widths | Every row has 19 CSV fields | PASS |
| KPI register statuses | 16 / 11 / 8 / 17 / 7 in canonical order | PASS |
| Historical-panel readiness | `BLOCKED` with current data | PASS; limitation recorded |

The canonical register and the evidence-based decisions are in
[`reports/batch18_kpi_readiness_register.csv`](../reports/batch18_kpi_readiness_register.csv),
[`reports/batch18_historical_data_feasibility.md`](../reports/batch18_historical_data_feasibility.md)
and [`reports/batch18_readiness_decisions.md`](../reports/batch18_readiness_decisions.md).

## Batch 19 export validation

The Batch 19 exporter performed an independent output-layer validation after
opening DuckDB read-only:

| Check | Measured result | Status |
|---|---:|---|
| National equipment / point totals | 117,662 / 211,253 | PASS |
| Normal / fast / >=150 / >=350 kW points | 156,155 / 55,098 / 40,950 / 6,950 | PASS |
| Declared equipment nominal power | 9,215.4173 MW | PASS |
| Duplicate point keys / orphan points / equipment-point mismatches | 0 / 0 / 0 | PASS |
| State charging rows | 16 | PASS |
| BBSR historical units / source components | 400 / 401 | PASS |
| BBSR type unit counts | 68 / 131 / 98 / 103 | PASS |
| KBA state rows / region-date rows | 48 / 1,200 | PASS |
| KBA national, state, `Sonstige` and 400-region reconciliation | All three dates | PASS |
| National KBA history | 33 unique stock dates | PASS |
| Source fingerprints | 12 approved inputs matched | PASS |
| DuckDB SHA-256 | `5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3` before/after | PASS |
| Second execution | CSVs, manifest and validation report byte-identical | PASS |

The detailed measured report is
[`reports/batch19_tableau_data_validation.md`](../reports/batch19_tableau_data_validation.md).
NULL handling, field units, natural keys and relationship prohibitions are in
[`reports/batch19_tableau_export_contracts.md`](../reports/batch19_tableau_export_contracts.md).
