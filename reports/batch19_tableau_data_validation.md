# Batch 19 — Tableau data export validation

**Batch status: PASS**

This report records measured validation of deterministic CSV extracts prepared from the existing local analytical data. The phase creates Tableau-ready files only; it does not build a Tableau workbook, modify DuckDB, alter source workbooks, or join KBA stock to BBSR geography.

## 1. Executive summary

Nine CSV extracts were generated under `data/exports/tableau/`. The BNetzA source reconciles to 117,662 equipment records, 211,253 populated point slots, 156,155 normal points, 55,098 fast points, 40,950 points at or above 150 kW, 6,950 points at or above 350 kW, and 9215.4173 MW of declared equipment nominal power.

The BBSR district export contains 400 historical 2025 target units formed from 401 BNetzA source components. Hanau and the remaining Main-Kinzig-Kreis component aggregate to historical BBSR `06435000` type 2; Kassel city is `06611000` type 1; Trier city and Trier-Saarburg remain separate charging components. No KBA vehicle stock is joined to these rows.

The KBA state and registration-region exports preserve the three validated stock dates. National and `Sonstige` rows are used for reconciliation but are not emitted as federal-state rows. The shared registration region `07211` remains one KBA row per date and is not allocated to Trier city or Trier-Saarburg.

## 2. Export inventory

| File | Rows | Columns | Primary key | SHA-256 |
|---|---:|---:|---|---|
| [`national_charging_2026_09_30.csv`](../data/exports/tableau/national_charging_2026_09_30.csv) | 1 | 14 | `geography_name` | `df9cd80325ec8faa7829aeb46ad3a755ff50d60c5872d97842a517af7508bf41` |
| [`state_charging_2026_09_30.csv`](../data/exports/tableau/state_charging_2026_09_30.csv) | 16 | 15 | `state_name` | `df36137c44e61b0da8fb9c20e80ff6ce59abb6d2cd0891e5da9ed6daefd202e5` |
| [`bbsr_district_charging_2025_geography.csv`](../data/exports/tableau/bbsr_district_charging_2025_geography.csv) | 400 | 27 | `historical_bbsr_administrative_district_code` | `ae1f80513f071afdde2ac1fc3b885881cef296a22180769ecd09a62eb66288bc` |
| [`bbsr_type_charging_2025_geography.csv`](../data/exports/tableau/bbsr_type_charging_2025_geography.csv) | 4 | 23 | `bbsr_settlement_type_code` | `0f61f86cccbeb254027b8aed7ae5a29ad12a64d8cc91b6be7ee843d32d54b589` |
| [`kba_state_ev_stock_2026.csv`](../data/exports/tableau/kba_state_ev_stock_2026.csv) | 48 | 13 | `state_name, kba_reference_date` | `d41bf606ff2aaeb82580555879a009d9aca0bab70167afe6db526e299609122b` |
| [`kba_registration_region_ev_stock_2026.csv`](../data/exports/tableau/kba_registration_region_ev_stock_2026.csv) | 1200 | 15 | `kba_registration_region_code, kba_reference_date` | `3a9fc7f3a77390d2dfec98702812c344805af0ba7b821a031373e6803715e6c6` |
| [`state_ev_charging_comparison_2026.csv`](../data/exports/tableau/state_ev_charging_comparison_2026.csv) | 16 | 28 | `state_name` | `8c2102cc3f32221f06f8f21eebe93039a4b42070cf65eda6f18e35187f9b9d62` |
| [`state_temporal_sensitivity_2026.csv`](../data/exports/tableau/state_temporal_sensitivity_2026.csv) | 16 | 80 | `state_name` | `9ba06577ccf84c8e9465b6b87866f4b592c4671208371b53d6e59353b4f60aa0` |
| [`kba_national_stock_history.csv`](../data/exports/tableau/kba_national_stock_history.csv) | 33 | 10 | `stock_date` | `48bc403b70954366eec1977a7e3c025b54cf69b601cd0902e4630978ff0dd024` |

## 3. Source object and schema inspection

DuckDB was opened with `read_only=True`. Required object types and columns were inspected before any query was executed. `analytics.charging_by_state` was verified to pre-aggregate points by `(source_id, equipment_excel_row)` and to use source-aware equipment/point keys.

| Object | Type | Column count |
|---|---|---:|
| `analytics.charging_by_bbsr_district_2025_harmonized` | VIEW | 34 |
| `analytics.charging_by_bbsr_type_2025_harmonized` | VIEW | 22 |
| `analytics.charging_by_state` | VIEW | 4 |
| `analytics.kba_national_quarterly_stock` | VIEW | 7 |
| `core.charging_equipment` | BASE TABLE | 26 |
| `core.charging_point` | BASE TABLE | 9 |
| `core.kba_district_ev_stock` | BASE TABLE | 9 |
| `core.kba_state_fuel_stock` | BASE TABLE | 6 |

## 4. Expected versus actual row counts

| Export | Expected | Actual | Result |
|---|---:|---:|---|
| National charging | 1 | 1 | PASS |
| State charging | 16 | 16 | PASS |
| BBSR historical districts | 400 | 400 | PASS |
| BBSR settlement types | 4 | 4 | PASS |
| KBA state/date | 48 | 48 | PASS |
| KBA registration-region/date | 1,200 | 1200 | PASS |
| State EV/charging comparison | 16 | 16 | PASS |
| Temporal sensitivity | 16 | 16 | PASS |
| National KBA history | 33 | 33 | PASS |

## 5. Key uniqueness

All natural-key checks passed during export and after CSV serialization: Germany has one row; state charging has one row per `state_name`; BBSR districts have one row per historical BBSR code; BBSR types have one row per type code; KBA state rows have one row per state/date; KBA registration regions have one row per code/date; and temporal sensitivity has one row per state.

## 6. National infrastructure reconciliation

| Measure | Direct source total | State sum | Expected |
|---|---:|---:|---:|
| Equipment records | 117,662 | 117,662 | 117,662 |
| Declared charging points | 211,253 | 211,253 | 211,253 |
| Populated point slots | 211,253 | 211,253 | 211,253 |
| Normal points | 156,155 | 156,155 | 156,155 |
| Fast points | 55,098 | 55,098 | 55,098 |
| Points >=150 kW | 40,950 | 40,950 | 40,950 |
| Points >=350 kW | 6,950 | 6,950 | 6,950 |
| Unknown-power points | 0 | 0 | 0 |
| Declared equipment nominal power (MW) | 9215.4173 | 9215.4173 | 9215.4173 |

Point integrity passed with 0 duplicate point keys, 0 orphan point rows, and 0 equipment/point count mismatches. Power classification uses the maximum numeric token in each semicolon-separated `connector_power_raw`: <=22 kW normal, >22 kW fast, with nested >=150 and >=350 kW thresholds.

## 7. KBA reconciliation

| KBA date | National passenger cars | National BEV | National PHEV | 16-state / 400-region passenger cars | 16-state / 400-region BEV | 16-state / 400-region PHEV | Sonstige BEV | Sonstige PHEV |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-01-01 | 49,486,487 | 2,034,260 | 1,122,958 | 49,436,020 | 2,031,870 | 1,121,516 | 2,390 | 1,442 |
| 2026-04-01 | 49,546,014 | 2,169,717 | 1,167,434 | 49,494,647 | 2,167,111 | 1,165,933 | 2,606 | 1,501 |
| 2026-07-01 | 49,696,710 | 2,365,047 | 1,226,863 | 49,644,855 | 2,362,218 | 1,225,241 | 2,829 | 1,622 |

The state export contains exactly the 16 named federal states. `Deutschland` and `Sonstige` remain separate reconciliation scopes. Passenger-car totals use six mutually exclusive FZ 27.2 fuel rows; `darunter Plug-in` supplies PHEV detail and is never added to `Hybrid insgesamt`.

The optional national history contains 33 unique stock dates from 2018-07-01 through 2026-07-01 from `analytics.kba_national_quarterly_stock`; no regional history was fabricated.

## 8. BBSR harmonization checks

The district export has 400 historical units and 401 source components. Type unit counts are 68, 131, 98 and 103 for types 1–4. All infrastructure measures reconcile to the national BNetzA totals. The source component provenance columns document the 401-to-400 conversion and the Hanau/Main-Kinzig union.

The BBSR rows are historical-geography labels at `2025-12-31` applied to BNetzA infrastructure published at `2026-09-30`. They must not be narrated as infrastructure observed in 2025. The export contains German BBSR labels only; no unvalidated English translation was added.

## 9. Cross-dataset compatibility

Permitted relationships are documented in `reports/batch19_tableau_export_contracts.md`: state charging to KBA state stock only with an explicit selected KBA date and visible date mismatch; KBA state rows to KBA state rows on `(state_name, kba_reference_date)`; KBA registration-region rows only on `(kba_registration_region_code, kba_reference_date)`; and BBSR charging extracts internally on validated BBSR type/code keys. No BBSR-to-KBA relationship is permitted.

The state comparison carries BNetzA `2026-09-30` and KBA `2026-07-01` separately and labels BEVs-per-point `CONTEXT_ONLY`. Fast/HPC per-1,000-BEV measures and the share gap are `EXPLORATORY_SENSITIVITY`; none is an adequacy, shortage, surplus, demand, utilization, or accessibility measure.

## 10. Date and grain safeguards

- BNetzA equipment nominal power is aggregated at equipment grain and is not simultaneously deliverable charging power.
- Charging point counts are populated point slots, not connector counts or verified availability.
- The survivor cohort retains September point attributes for equipment commissioned on or before `2026-07-01`; it is not an actual July infrastructure snapshot.
- KBA stock is registered passenger-car stock, not new registrations or sales.
- Code `07211` remains the single KBA registration geography `TRIER-SAARBURG` for every KBA date and is not split between Trier city and Trier-Saarburg.

## 11. Deterministic rerun checks

PASS — output ordering, column order, UTF-8 encoding, LF line endings, numeric formatting and JSON key ordering are fixed; no generation timestamp is embedded. A second execution was compared byte-for-byte for all CSVs and the manifest after the initial export.

## 12. Source and database immutability

DuckDB SHA-256 before and after read-only export: `5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3`. All 12 approved input fingerprints matched their Batch 13.2/16/17 values. No DuckDB object, raw workbook, reference table, crosswalk or source file was modified.

## 13. Known issues

- The BNetzA register is a published register and is not evidence of a complete census, utilization, uptime or service quality.
- Cross-source ratios have a 91-day KBA/BNetzA snapshot gap and remain contextual or exploratory.
- BBSR historical harmonization is charging-only; the owner-approved Hanau scenario was not used as the official baseline.
- No historical infrastructure panel is available from the current sources.

## 14. Remaining Tableau preparation risks

Keep national, state, BBSR historical and KBA registration-region extracts as separate logical sources unless a specific relationship has been validated. Do not sum a state charging row after relating it to multiple KBA dates, sum national and state aggregates together, sum percentages, or treat the 400 BBSR historical units as the 400 KBA registration regions.

## 15. Recommended next step

Review the contracts and export manifest with the owner, then approve a separate Tableau implementation batch if desired. Batch 20 and dashboard construction were not started by this batch.

## Input fingerprints

| Input | SHA-256 | Result |
|---|---|---|
| `data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx` | `1e82c1734b17e17e51092a0f9460a5e204888569fb12aa5940b30e9cdb726342` | MATCH |
| `data/raw/kba/fz27_202601.xlsx` | `29ab2eaa178a1c6a3463d5cad707fee1e762241304ae6bb08c29702d6e6aea31` | MATCH |
| `data/raw/kba/fz27_202604.xlsx` | `28fffaa7d2f21ede6d7f6988a717b749b759a308755c472df4d391c73a0653e7` | MATCH |
| `data/raw/kba/fz27_202607.xlsx` | `d6a26702fa6f8358cc5f0e15e88c04ac6c36527be404058674138dd9571bc803` | MATCH |
| `data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx` | `083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525` | MATCH |
| `data/reference/bnetza_kba_district_crosswalk_2026.csv` | `fdf139c5057250184358e3014267a4a4c4259749113273f6bd48206f6a64fe6a` | MATCH |
| `data/reference/bnetza_bbsr_historical_harmonization_2025.csv` | `26b7b177b11f19628d85c7195975d75232804567b43d964f99acb8fcd8f84661` | MATCH |
| `data/reference/bnetza_bbsr_historical_harmonization_2025_manifest.json` | `fa2cf4085e36ea7914eb3ce7e51ec56a527d9a7b5cc8a47c1701078a35871a26` | MATCH |
| `data/reference/bbsr_settlement_types_2025.csv` | `e35c57da8d8f675fa132b629e6dda43180a18e5b78b95e1e72de30069a062e65` | MATCH |
| `data/reference/bbsr_source_manifest.json` | `ba3540bf447a5c843a5a9d8fcdf224803edd26556c27e1e80a24b56a3f59a60c` | MATCH |
| `reports/batch16_state_comparison.csv` | `0b3864593dab8a0c760e5e8f175a17d01bdb8f4696e7c89602277bb24c31403a` | MATCH |
| `reports/batch17_state_temporal_sensitivity.csv` | `5b6fc2cbe8f93b5beaf1786ac5ac733b733bc8bb55deacea63dcf46cd4144ab8` | MATCH |
