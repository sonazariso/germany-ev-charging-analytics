# Data dictionary

## Tracked BBSR reference (outside DuckDB)

Batch 10 adds a separately versioned, source-derived CSV reference. The CSV
remains outside DuckDB and does not replace the BNetzA-to-KBA Crosswalk. Batch
13 consumes it only through a separate BNetzA-source-grain bridge for
charging-only descriptive KPIs; it is not a KBA enrichment.

| Artifact | Grain | Rows | Reference |
|---|---|---:|---|
| data/reference/bbsr_settlement_types_2025.csv | One row per BBSR KRS2025 administrative Kreis row | 400 | Geographic stand 2025-12-31; 362 distinct Kreisregion keys |

| CSV column | Meaning and source | Rule |
|---|---|---|
| source_version | Preserved workbook/sheet/version description | Keep beside every derived row |
| bbsr_reference_date | BBSR geographic stand | Do not overwrite with a KBA or BNetzA date |
| source_sheet_name, source_excel_row | Original worksheet lineage | Retain for reproducibility; source row is not a geographic key |
| administrative_district_code, administrative_district_name | Original KRS2025 / KRS_NAME | Codes remain strings; names are original BBSR text |
| federal_state_code, federal_state_name | Original BLD2025 / BLD_NAME | Two-digit state codes remain strings; names are original BBSR text |
| kreisregion_code, kreisregion_name | Original KKR2025 / KKR_NAME | Multiple administrative rows may share one Kreisregion; do not collapse them silently |
| settlement_type_code, settlement_type_name_de | Original KTU2025 / KTU_NAME compact four-category classification | Code domain is 1–4; differentiated five-category fields are not used |

The source workbook, response metadata, complete original sheet/column inventory,
source checksum, derived checksum, and validation evidence are recorded in
data/reference/bbsr_source_manifest.json. The raw workbook is intentionally
excluded from Git.

## Batch 13 BNetzA-to-BBSR bridge

`data/reference/bnetza_bbsr_bridge_2025.csv` and
`reference.bnetza_bbsr_district_bridge_2025` have one row per original BNetzA
state/district combination. The bridge preserves source dates, BBSR KRS and
Kreisregion identifiers, evidence references, and the Path A compatibility
status. The database table uses a unique composite BNetzA source key; BBSR
codes are VARCHAR and are deliberately not globally unique.

| Column | Meaning | Rule |
|---|---|---|
| bridge_version | Batch 13 bridge version | Keep fixed for repeat-safe deployment |
| bnetza_source_id / bnetza_reference_date | BNetzA source lineage | Current source is `bnetza_charging_2026_09_30`, dated `2026-09-30` |
| bnetza_state_name / bnetza_district_name / bnetza_admin_type | Original source geography | Grain and join key; no KBA code is used as proof |
| bbsr_reference_date / bbsr_source_version | BBSR vintage and source | `2025-12-31` geographic stand remains visible |
| bbsr_administrative_district_code / bbsr_kreisregion_code | BBSR identifiers | VARCHAR; leading zeroes retained; multiple source rows may share a Kreisregion |
| bbsr_settlement_type_code / bbsr_settlement_type_name_de | Four-category type | Populated only for 399 verified rows; NULL for Main-Kinzig and Hanau |
| geographic_compatibility_status | Path A status | 399 `VERIFIED_COMPATIBLE`, one `CONDITIONAL_VINTAGE`, one `UNRESOLVED` |
| evidence_method / evidence_source_reference / validation_notes | Provenance and safeguards | Preserve the independent Batch 12 evidence and explicit no-allocation rules |

Main-Kinzig retains its pre-change BBSR administrative/Kreisregion code as
evidence but no settlement type. Hanau has no separate BBSR 2025 row. Neither
row may inherit a type from the other.

## Batch 13.1 owner-override reference

`data/reference/bnetza_bbsr_owner_override_2026.csv` and
`reference.bnetza_bbsr_owner_override_2026` contain exactly two rows at the
original BNetzA source state/district grain. They are a versioned analytical
scenario, not an official BBSR reference.

| Column | Meaning and rule |
|---|---|
| scenario_version | Fixed owner-scenario identifier; current value is `batch13.1-2026-11-02-owner-approved-hanau-main-kinzig` |
| scenario_source_vintage | Visible BNetzA, KBA-code, and BBSR source vintages; do not collapse them into one date |
| bnetza_source_id / bnetza_reference_date | Actual normalized BNetzA source identifier and `2026-09-30` date |
| bnetza_state_name / bnetza_district_name / bnetza_admin_type | Actual source columns and source-grain identity used for the overlay join |
| geographic_code_system / geographic_code | Existing Crosswalk `kba_district_code` identifier (`KBA_DISTRICT_CODE`), `06415` or `06435`; identifier only, not BBSR proof |
| kba_reference_date | Crosswalk code snapshot date `2026-07-01`; no KBA stock is joined |
| analytical_category_code / analytical_category_name_de | Owner scenario category 1–4; only 1 for Hanau and 2 for Main-Kinzig |
| classification_method | `OWNER_APPROVED_SCENARIO` for Hanau; `HISTORICAL_BBSR_CARRY_FORWARD` for Main-Kinzig |
| official_bbsr_verification | Boolean false for both owner rows; neither is `VERIFIED_COMPATIBLE` |
| official_bbsr_2025_type | NULL for Hanau; `2` for the Main-Kinzig historical BBSR row |
| boundary_vintage / boundary_compatibility_caveat | Explicit `2026` scenario vintage and Hanau-separation caveat |
| override_provenance / population_evidence_note | Owner approval, non-official status, and Hanau population-context note |
| evidence_source_urls | Semicolon-separated evidence URLs retained with each row |
| source_audit_version / source_audit_sha256 | Batch 12 Path A lineage and immutable audit checksum |

The official `data/reference/bbsr_settlement_types_2025.csv` and the Batch 13
bridge remain separate and unchanged. The complete manifest records the CSV
checksum and the distinction between the official baseline and this scenario.

## Database inventory

The current local database is data/analytics/ev_charging.duckdb. It contains four schemas and the following objects. Counts are read-only observations from the current file.

| Schema | Object | Type | Current rows |
|---|---|---|---:|
| raw | bnetza_rows | table | 117,670 |
| raw | kba_rows | table | 61,797 |
| core | charging_equipment | table | 117,662 |
| core | charging_point | table | 211,253 |
| core | kba_state_fuel_stock | table | 378 |
| core | kba_district_ev_stock | table | 1,200 |
| core | kba_postcode_ev_stock | table | 24,586 |
| core | kba_municipality_ev_stock | table | 32,229 |
| reference | bnetza_kba_district_crosswalk_2026 | table | 401 |
| reference | bnetza_bbsr_district_bridge_2025 | table | 401 |
| analytics | charging_by_state | view | 16 state rows |
| analytics | charging_point_public | view | 211,253 joined point rows |
| analytics | kba_national_quarterly_stock | view | historical observations |
| analytics | charging_by_kba_district_2026_09_30 | view | 400 KBA district rows |
| analytics | kba_district_charging_vs_bev_2026 | view | 1,200 KBA code/date rows |
| analytics | charging_by_bbsr_district_2025 | view | 401 BNetzA source districts |
| analytics | charging_by_bbsr_type_2025 | view | 5 settlement/reporting groups |

All columns are nullable according to the current DuckDB information schema. Nullability in this document therefore describes the database definition; the quality section reports observed null or exception counts.

## Raw schemas

### raw.bnetza_rows

Grain: one populated physical row from the one BNetzA worksheet, identified by source_id and excel_row. The table has source_id VARCHAR, excel_row INTEGER, and col_a through col_au VARCHAR. The generic columns preserve the workbook layout before header mapping:

- col_a through col_w: equipment-level fields from equipment ID through opening times.
- col_x through col_au: six repeated charging-point groups, each with connector types, connector power, EVSE ID, and Public Key.

The raw table includes title, legal-note, update-date, header, and equipment rows. The normalized equipment table keeps rows with Excel row number at least 12.

### raw.kba_rows

Grain: one populated physical row from any KBA worksheet and source snapshot. Columns are source_id VARCHAR, reference_date DATE, sheet_name VARCHAR, excel_row INTEGER, and col_a through col_o VARCHAR. The generic fields are deliberate: KBA worksheets use different headers and column meanings. Sheet name and source row must be retained when interpreting a value.

## Core tables

### core.charging_equipment

Grain: one BNetzA equipment record from the 2026-09-30 snapshot. Source-local identity is source_id plus excel_row; equipment_id is the source identifier.

| Column | Type | Meaning and source | Quality, relationship, and business rule |
|---|---|---|---|
| source_id | VARCHAR | Manifest source identifier | Required for source-aware joins; one current BNetzA snapshot |
| excel_row | INTEGER | Original BNetzA worksheet row | Preserves source lineage; part of equipment row identity |
| equipment_id | VARCHAR | Ladeeinrichtungs-ID | No missing or duplicate values observed in the current snapshot |
| operator_name | VARCHAR | Betreiber | Source text; may contain spelling or legal-name variation |
| display_name | VARCHAR | Map display name | Source text; not a geographic key |
| status | VARCHAR | BNetzA equipment status | Current values are In Betrieb and In Wartung; no status is silently filtered |
| equipment_type | VARCHAR | Normalladeeinrichtung or Schnellladeeinrichtung | Equipment-level classification; not a substitute for point-level power parsing |
| declared_point_count | INTEGER | BNetzA Anzahl Ladepunkte | Sums to 211,253 and reconciles to populated point rows in the current snapshot |
| equipment_nominal_power_kw | DOUBLE | BNetzA Nennleistung Ladeeinrichtung [kW] | Sum is 9,215.42 MW when aggregated from equipment rows; not delivered energy |
| commissioning_date_raw | VARCHAR | Original date/serial text | Retained for traceability |
| commissioning_date | DATE | Parsed commissioning date | Parsed from Excel serial or date text; all current rows are populated and within the snapshot range |
| street, house_number, address_addition | VARCHAR | Source address fields | Address detail; not used as a primary join key |
| postal_code | VARCHAR | Source postal code | All current equipment rows populated; codes are source text |
| city_name | VARCHAR | Source locality | Display and quality field; not the KBA district key |
| district_name | VARCHAR | BNetzA Kreis/kreisfreie Stadt | Input to the state-aware crosswalk; name normalization never replaces administrative-type checks |
| state_name | VARCHAR | BNetzA Bundesland | Sixteen distinct current values; input to the crosswalk |
| latitude, longitude | DOUBLE | Parsed source coordinates | All current rows populated; one row is outside a broad Germany bounding check and remains uncorrected |
| site_name | VARCHAR | Standortbezeichnung | Source text |
| parking_information | VARCHAR | Information zum Parkraum | Source text |
| payment_methods | VARCHAR | Bezahlsysteme | Source text; no payment KPI is currently approved |
| opening_hours, opening_weekdays, opening_times | VARCHAR | Availability and schedule text | Descriptive only; does not establish real-time availability |

### core.charging_point

Grain: one populated charging-point slot from one equipment row. Point identity for validation is source_id, equipment_excel_row, and point_number.

| Column | Type | Meaning and source | Quality, relationship, and business rule |
|---|---|---|---|
| source_id | VARCHAR | Manifest source identifier | Joins to the equipment source |
| equipment_excel_row | INTEGER | Original equipment row number | Foreign-key-like relationship to charging_equipment source_id plus excel_row |
| equipment_id | VARCHAR | Copied source equipment ID | Retained for traceability; not sufficient alone for multi-source joins |
| point_number | INTEGER | Repeated BNetzA slot number 1 through 6 | Slot number within one equipment row |
| connector_types | VARCHAR | Steckertypen text | A semicolon-separated connector description remains one point value |
| connector_power_raw | VARCHAR | Original Nennleistung Stecker text | Can contain several semicolon-separated numeric values within one point |
| connector_power_kw_single | DOUBLE | Parsed only when the raw text is a single numeric value | Null for the current multi-value strings; not the complete power-classification field |
| evse_id | VARCHAR | EVSE-ID for the slot | Source identifier; not used as the equipment foreign key |
| public_key | VARCHAR | Public Key for the slot | Preserved in core, excluded from charging_point_public |

The complete point-power classification uses connector_power_raw, splits within the point row, parses each token, and uses the maximum declared numeric value. It does not explode the point into connector rows.

### core.kba_district_ev_stock

Grain: one KBA district code and reference date from FZ 27.15. There are 400 rows for each of the three dates.

| Column | Type | Meaning and source | Quality, relationship, and business rule |
|---|---|---|---|
| source_id | VARCHAR | KBA workbook identifier | Preserves snapshot lineage |
| reference_date | DATE | 2026-01-01, 2026-04-01, or 2026-07-01 | Must be carried into every vehicle KPI |
| excel_row | INTEGER | FZ 27.15 source row | Source lineage |
| state_name | VARCHAR | KBA state label | State grouping field |
| district_code | VARCHAR | Five-digit KBA statistical registration code | Unique within each reference date; join key to the crosswalk |
| district_name | VARCHAR | KBA Zulassungsbezirk label | Display and local-snapshot validation field |
| passenger_cars | BIGINT | FZ 27.15 Anzahl insgesamt | Confirmed denominator for district BEV share |
| bev_cars | BIGINT | FZ 27.15 davon Elektro (BEV) | Registered BEV stock, not new sales |
| phev_cars | BIGINT | FZ 27.15 Plug-in-Hybrid | Registered PHEV stock |

### core.kba_state_fuel_stock

Grain: one KBA state or aggregate label, fuel category, and reference date from FZ 27.2. The current table has 378 rows: 18 labels, 7 categories, and 3 dates.

| Column | Type | Meaning and source | Quality, relationship, and business rule |
|---|---|---|---|
| source_id | VARCHAR | KBA workbook identifier | Preserves snapshot lineage |
| reference_date | DATE | KBA stock date | Must not be treated as the BNetzA date |
| excel_row | INTEGER | FZ 27.2 source row | Source lineage |
| state_name | VARCHAR | State, Deutschland, or Sonstige | Deutschland includes the KBA national total; Sonstige is not a normal federal state |
| fuel_type | VARCHAR | Benzin, Diesel, Gas insgesamt, Elektro (BEV), Hybrid insgesamt, darunter Plug-in, or Sonstige | Category is not a mutually additive vehicle table across all worksheets |
| passenger_cars | BIGINT | FZ 27.2 passenger-car count for the category | Use the precise fuel label and geography filter; do not add alternate KBA tables |

### core.kba_postcode_ev_stock

Grain: one source postcode and reference date from FZ 27.16.

Columns are source_id, reference_date, excel_row, postal_code, commercial_total_cars, commercial_bev, commercial_phev, private_total_cars, private_bev, and private_phev. Counts are BIGINT except the identifiers, which are VARCHAR. Commercial and private totals are alternative ownership breakdowns; they must not be added to an unrelated district total without a defined reconciliation.

### core.kba_municipality_ev_stock

Grain: one municipality source row and reference date from FZ 27.17. Columns are source_id, reference_date, excel_row, state_name, district_label, municipality_name, commercial_total_cars, commercial_bev, commercial_phev, private_total_cars, private_bev, private_phev, district_code, and possible_total_row.

possible_total_row flags municipality labels containing zusammen or insgesamt. It is a quality flag, not permission to sum every row. The district code is carried from the source district label and is not an independently verified spatial join.

## Analytics views

### analytics.charging_point_public

Grain: one joined charging-point slot. It exposes equipment_id, point_number, state_name, district_name, city_name, postal_code, latitude, longitude, operator_name, status, equipment_type, commissioning_date, equipment_nominal_power_kw, connector_types, connector_power_raw, and connector_power_kw_single. It intentionally does not expose public_key.

### analytics.charging_by_state

Grain: one row per current BNetzA state_name. Columns are state_name VARCHAR, equipment_rows BIGINT, declared_points HUGEINT, and populated_point_slots HUGEINT.

Batch 06 corrected the point subquery to group by `(source_id, equipment_excel_row)` and to join on both fields. The output column names, order, 16-state grain, and current metrics remain unchanged.

### reference.bnetza_kba_district_crosswalk_2026

Grain: one row per BNetzA source snapshot, state/district combination, and crosswalk version. The 401-row table preserves every CSV field and adds `bnetza_source_id` for source lineage. `kba_district_code` is VARCHAR so leading zeroes are preserved. The source-geography key is unique across `(crosswalk_version, bnetza_source_id, bnetza_state_name, bnetza_district_name)`; KBA code `07211` intentionally occurs twice for Trier and Trier-Saarburg. `mapping_status`, `mapping_method`, `verification_status`, `mapping_note`, and `evidence_url` are audit fields; provisional rows remain provisional.

### analytics.charging_by_kba_district_2026_09_30

Grain: one row per KBA district code after aggregating the BNetzA 2026-09-30 equipment and point relations. Equipment and point metrics are aggregated separately before they are combined. The view retains `bnetza_reference_date`, equipment count, populated and declared point counts, maximum-per-point power bands, percentage fields, equipment nominal power in kW and MW, and mapping-quality fields (`mapping_status`, `mapping_verification_status`, `source_geography_rows`, `provisional_mapping_rows`, and `unmapped_source_geography_rows`). `points_without_valid_power` is an explicit unknown-power count and is not silently placed in a power band.

### analytics.kba_district_charging_vs_bev_2026

Grain: one KBA district code per actual KBA stock reference date. The view joins the unique KBA-code charging result to `core.kba_district_ev_stock` by district code after charging aggregation. It exposes KBA state/district names, `kba_reference_date`, `bnetza_reference_date`, passenger-car/BEV/PHEV stock, infrastructure metrics, `bev_per_registered_charging_point`, and the geographic quality fields. The current grain is 400 codes × three dates = 1,200 rows. Infrastructure measures repeat beside each KBA date and must not be summed across dates.

### analytics.charging_by_bbsr_district_2025

Grain: one original BNetzA state/district combination. The view carries the
BNetzA infrastructure date, BBSR 2025 reference date, BBSR administrative and
Kreisregion identifiers, settlement type fields, geographic compatibility
status, provenance, equipment/point counts, maximum-per-point power bands,
nominal equipment power in kW/MW, and within-district fast/high-power shares.

Equipment metrics are aggregated from `core.charging_equipment` before points
are joined. Point metrics are aggregated from `core.charging_point` using
`source_id + equipment_excel_row + point_number`; semicolon-separated
`connector_power_raw` tokens are parsed with decimal-comma normalization and the
maximum valid value is used once per point. `unclassifiable_power_point_count`
is explicit. All equipment statuses remain included and are exposed in
`equipment_statuses_present`.

This view never joins `core.kba_district_ev_stock`, the KBA Crosswalk, BEV, or
PHEV measures. Hanau and Main-Kinzig remain visible with NULL BBSR settlement
type fields.

### analytics.charging_by_bbsr_type_2025

Grain: one settlement category. It emits codes 1–4 and `UNCLASSIFIED`.
Category fast/high-power shares are within-category percentages. The
`share_of_all_registered_charging_points_pct` field uses all 211,253 charging
points, including unclassified source districts, and
`point_share_denominator_scope` states that denominator explicitly. The view
contains no KBA vehicle-stock measures and does not calculate BEV-per-point.

### reference.bnetza_bbsr_owner_override_2026

This is the two-row owner-approved scenario reference described above. It is a
new table and does not overwrite `reference.bnetza_bbsr_district_bridge_2025`.
Its `geographic_code` values are Crosswalk identifiers for the observed
BNetzA rows; they do not turn the scenario into a KBA-to-BBSR bridge.

### analytics.charging_by_bbsr_district_2026_scenario

Grain: one original BNetzA state/district combination. The view retains the
official Batch 13 baseline category/status fields and adds the scenario
category, version, source vintage, boundary vintage, override provenance,
official-verification flag, evidence URLs, and audit hash. It has 401 rows and
zero rows with a NULL scenario category.

Charging measures are inherited from the validated Batch 13 source-aware view:
equipment rows and point rows remain separate, and each point is classified
once using the maximum valid semicolon-separated `connector_power_raw` token.
No KBA stock or BEV/PHEV measure is present.

### analytics.charging_by_bbsr_type_2026_scenario

Grain: one owner-scenario analytical category, codes 1–4. The four-row view
reports district/equipment/point counts, normal and fast points, points at
least 150/350 kW, fast/high-power shares, declared nominal equipment power,
national point share, owner-override counts, and the explicit zero
`unclassified_district_count`. Its scenario version and source-vintage fields
remain visible in every row.

### reference.bnetza_bbsr_historical_harmonization_2025

Grain: one current BNetzA 2026-09-30 source state/district component per row,
mapped to one historical BBSR 2025 administrative target. The table preserves
the infrastructure and BBSR reference dates, source/target names and codes,
raw BBSR city/county form evidence, source-component role, mapping method,
boundary-compatibility status, evidence reference, and validation notes.

Hanau and the remaining Main-Kinzig source row both target historical BBSR
`06435000` type 2. The table does not assert a 2026 BBSR type for Hanau. City
Kassel targets `06611000 Kassel, documenta-Stadt` type 1; Landkreis Kassel
targets `06633000 Kassel` type 2. The versioned unique key is
`(harmonization_version, bnetza_source_id, bnetza_state_name,
bnetza_district_name)`.

### analytics.charging_by_bbsr_district_2025_harmonized

Grain: one historical BBSR 2025 target administrative unit after aggregating
the current BNetzA source components. It exposes `source_component_count` and
`source_component_names`, `historical_boundary_basis`, mapping/evidence fields,
both source dates, equipment and charging-point measures, maximum-per-point
power bands, equipment nominal power, and status metadata. It has 400 rows from
401 source components. Hanau plus remaining Main-Kinzig is one target with 585
equipment and 991 points.

The view is charging-only. It does not read KBA vehicle stock, the KBA
Crosswalk, BEV, or PHEV measures. Source rows remain unchanged in the core
tables and original Batch 13/13.1 views.

### analytics.charging_by_bbsr_type_2025_harmonized

Grain: one historical BBSR compact settlement type, codes 1–4. It reports the
historical target count separately from the current source-component count and
reconciles to the national BNetzA totals. The target counts are 68 / 131 / 98 /
103; source components are 68 / 132 / 98 / 103 because Hanau and remaining
Main-Kinzig are two current components of one historical type-2 target. There
is no unclassified target row. National point shares use all 211,253 charging
points.

### analytics.kba_national_quarterly_stock

Grain: one retained national historical stock observation per stock_date after de-duplicating overlapping report snapshots. Columns are source_id, report_snapshot, excel_row, stock_date, passenger_bev, passenger_phev, and passenger_cars_total.

## Keys and business rules

- Preserve source_id and source row identifiers in all joins.
- Aggregate BNetzA metrics by KBA district code before joining KBA stock.
- Use district_code and reference_date together for KBA district facts.
- Treat equipment counts, populated point slots, connector-power classes, and declared equipment power as different measures.
- Treat KBA district, postcode, municipality, state, and national tables as alternative grains, not additive partitions.
- Keep the 2026-09-30 BNetzA date and KBA dates in every combined output.
- Keep BBSR `KRS` and `Kreisregion` codes as strings and do not require BBSR codes to be globally unique across BNetzA source rows.
- Treat the official Batch 13 BBSR category KPIs as descriptive measures of 399 verified-compatible BNetzA source districts; keep Main-Kinzig and Hanau in the official baseline `UNCLASSIFIED` group.
- Treat Batch 13.1 scenario category KPIs as a separate owner-approved analytical scenario. Hanau category 1 is not an official BBSR 2025/2026 classification; Main-Kinzig category 2 is a historical carry-forward with a 2026 boundary caveat; both override rows have `official_bbsr_verification = false`.
- Treat Batch 13.2 as a separate historical BBSR 2025 target-unit harmonization. It corrects Kassel city only in the new layer and combines current Hanau with remaining Main-Kinzig to historical BBSR `06435000` type 2; it is not an official 2026 Hanau classification.
- Preserve both BNetzA `2026-09-30` and BBSR `2025-12-31` dates in Batch 13.2 outputs, and retain source-component names/counts so target-unit aggregation is auditable.
- Do not join BBSR views to KBA vehicle stock or infer a BBSR type for KBA registration regions.
- Do not infer utilization, energy delivery, or causality from these tables.
