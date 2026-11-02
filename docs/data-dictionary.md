# Data dictionary

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
| analytics | charging_by_state | view | 16 state rows |
| analytics | charging_point_public | view | 211,253 joined point rows |
| analytics | kba_national_quarterly_stock | view | historical observations |
| analytics | charging_by_kba_district_2026_09_30 | view | 400 KBA district rows |
| analytics | kba_district_charging_vs_bev_2026 | view | 1,200 KBA code/date rows |

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

### analytics.kba_national_quarterly_stock

Grain: one retained national historical stock observation per stock_date after de-duplicating overlapping report snapshots. Columns are source_id, report_snapshot, excel_row, stock_date, passenger_bev, passenger_phev, and passenger_cars_total.

## Keys and business rules

- Preserve source_id and source row identifiers in all joins.
- Aggregate BNetzA metrics by KBA district code before joining KBA stock.
- Use district_code and reference_date together for KBA district facts.
- Treat equipment counts, populated point slots, connector-power classes, and declared equipment power as different measures.
- Treat KBA district, postcode, municipality, state, and national tables as alternative grains, not additive partitions.
- Keep the 2026-09-30 BNetzA date and KBA dates in every combined output.
- Do not infer utilization, energy delivery, or causality from these tables.
