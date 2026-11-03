# Tableau Fact and Dimension Catalog — Batch 20

This catalog defines logical Tableau facts and dimensions. Names beginning with
`Dim` or `Fact` are semantic names, not newly created DuckDB objects. The
current implementation uses the validated Batch 19 CSV files and existing
DuckDB objects listed in each entry.

## 1. Catalog conventions

- A **fact grain** is the one row meaning that must remain true after every
  filter and aggregation.
- A **business key** is a source or analytical natural key. A **surrogate key**
  is a candidate future implementation key only; no surrogate key is invented
  in the current files.
- `VARCHAR`, `DATE`, `BIGINT`, `HUGEINT`, `DOUBLE`, and `BOOLEAN` below are the
  actual DuckDB types where the source object was inspected. CSV values are
  serialized text and receive types when loaded by a future Tableau connector.
- Percentage and ratio columns are presentation outputs. Their numerator and
  denominator fields remain the authoritative aggregation inputs.

## 2. Dimensions

### DimState

| Contract item | Specification |
|---|---|
| Grain | One of the 16 named German Bundesländer |
| Candidate PK | `state_key` `[CONCEPTUAL]` |
| Business key | Current validated `state_name` (`VARCHAR` in DuckDB facts); no state code is present in the Batch 19 state export |
| Attributes | `state_name`; optional future stable state code `[CONCEPTUAL]`; `state_scope` `[CONCEPTUAL]` |
| Vintage semantics | Current state labels are used as the 2026 BNetzA/KBA reporting labels. No SCD history is implemented. |
| Parent relationship | Germany is a reporting context, not a 17th state row. `Deutschland` and `Sonstige` are not members of the 16-state export. |
| Uniqueness | 16 unique `state_name` values in state charging, KBA state stock, state comparison, and temporal exports; 16-to-16 state matches pass for each KBA date. |
| Null handling | Null state is invalid for state facts; reject or quarantine it. Do not map `Deutschland` or `Sonstige` to a Bundesland. |
| Related facts | `FactStateCharging`, `FactKBAStateStock`, `FactStateEVChargingComparison`, `FactTemporalSensitivity`; optionally registration-region facts through their explicit `state_name` attribute. |

### DimBBSRRegion

| Contract item | Specification |
|---|---|
| Grain | One harmonized BBSR 2025 historical target unit |
| Candidate PK | `bbsr_region_key` `[CONCEPTUAL]` |
| Business key | `historical_bbsr_administrative_district_code` (`VARCHAR`), versioned with `bbsr_reference_date` and `harmonization_version` |
| Attributes | `historical_bbsr_administrative_district_name`, `historical_bbsr_federal_state_code`, `historical_bbsr_federal_state_name`, `historical_bbsr_kreisregion_code`, `historical_bbsr_kreisregion_name`, `historical_bbsr_settlement_type_code`, `historical_bbsr_settlement_type_name_de`, `historical_boundary_basis`, `source_component_count`, `source_component_names`, `mapping_method`, `boundary_compatibility_status` |
| Vintage semantics | `historical_bbsr_reference_date = 2025-12-31`; the dimension labels a historical target geography applied to BNetzA `2026-09-30` charging. It is not a 2026 administrative dimension. |
| Parent relationship | Historical BBSR federal-state attributes are retained. A shared `DimState` relationship requires an explicit validated state-label contract; it does not authorize a BBSR-to-KBA join. |
| Uniqueness | 400 unique target codes in the harmonized export; 401 source components map to those 400 targets. |
| Null handling | Historical target code/name must be non-null in the harmonized fact. Source-grain Batch 13 rows may retain unresolved or unclassified type values. |
| Related facts | `FactBBSRCharging`, `FactBBSRTypeCharging` through the type attribute, and future `FactBBSRSourceCharging` only within BBSR charging analysis. |

### DimBBSRSettlementType

| Contract item | Specification |
|---|---|
| Grain | One BBSR compact four-category settlement type for one BBSR vintage |
| Candidate PK | `bbsr_settlement_type_key` `[CONCEPTUAL]` |
| Business key | `(bbsr_reference_date, bbsr_settlement_type_code)`; current code is `VARCHAR` and values are `1`–`4` |
| Attributes | `bbsr_settlement_type_name_de`, source version, classification scope |
| Vintage semantics | Type labels are tied to the BBSR geographic stand `2025-12-31`. Do not reuse them as current KBA types. |
| Parent relationship | None to KBA geography. Historical BBSR region facts may carry the type key. |
| Uniqueness | Four rows in the Batch 19 type export; target-unit counts are 68, 131, 98, and 103. |
| Null handling | No null type in the 400-unit harmonized export. `UNCLASSIFIED` is a separate allowed value only in the official source-grain Batch 13 layer, not one of the four harmonized target types. |
| Related facts | `FactBBSRCharging`, `FactBBSRTypeCharging`, and the separate scenario fact if explicitly versioned. |

### DimKBARegistrationRegion

| Contract item | Specification |
|---|---|
| Grain | One KBA registration region identified by a stable KBA registration code |
| Candidate PK | `kba_registration_region_key` `[CONCEPTUAL]` |
| Business key | `kba_registration_region_code` (`VARCHAR`); retain leading zeroes |
| Attributes | `registration_region_name`, `state_name`; future source metadata may include KBA admin type, but no field is invented in the Batch 19 export |
| Vintage semantics | Current 2026 KBA codes are stable across the three regional stock dates in the export. If future KBA geography changes, version the dimension rather than overwriting history. |
| Parent relationship | `state_name` is a reporting attribute for KBA regions. It is not evidence that the region is a BBSR unit or a current administrative Kreis. |
| Uniqueness | 400 codes per KBA date and one row per `(kba_registration_region_code, kba_reference_date)`; all 1,200 composite keys are unique. |
| Null handling | Code and date are required. Preserve `07211` as one `TRIER-SAARBURG` region; never allocate it to Trier city or Trier-Saarburg subparts. |
| Related facts | `FactKBARegistrationRegionStock`; optional geographic filtering of a standalone infrastructure fact only after the existing Crosswalk contract is deliberately selected. |

### DimKBAStockDate

| Contract item | Specification |
|---|---|
| Grain | One supported KBA stock reference date |
| Candidate PK | `kba_stock_date_key` `[CONCEPTUAL]` |
| Business key | `kba_reference_date` for regional/state facts; `stock_date` for national history, with a role-specific mapping |
| Attributes | Source report snapshot and source object where present; date role label `[CONCEPTUAL]` |
| Vintage semantics | 2026 regional/state values are `2026-01-01`, `2026-04-01`, and `2026-07-01`. National history contains 33 stock dates from `2018-07-01` through `2026-07-01`. |
| Parent relationship | None to BNetzA snapshot dates. A shared calendar date is not a license to compare or sum different source facts. |
| Uniqueness | One row per supported date in a role-specific date dimension. |
| Null handling | A KBA stock fact without a reference date is invalid. Do not default a missing date to the latest snapshot. |
| Related facts | `FactKBAStateStock`, `FactKBARegistrationRegionStock`, `FactKBANationalHistory`, `FactStateEVChargingComparison`, and `FactTemporalSensitivity` through explicitly named KBA date roles. |

### DimChargingSnapshot

| Contract item | Specification |
|---|---|
| Grain | One BNetzA infrastructure snapshot date and source version |
| Candidate PK | `charging_snapshot_key` `[CONCEPTUAL]` |
| Business key | `bnetza_reference_date` plus `bnetza_source_id` where available |
| Attributes | `bnetza_reference_date`, `bnetza_source_id`, export version, manifest checksum `[CONCEPTUAL metadata]` |
| Vintage semantics | Current snapshot is BNetzA `2026-09-30`. A later snapshot must be a new source version; it must not overwrite the current row. |
| Parent relationship | None to KBA stock dates or BBSR geographic vintages. |
| Uniqueness | One current snapshot in Batch 19; all nine exports carry the same BNetzA date where charging is present. |
| Null handling | Charging facts require a non-null snapshot date. Do not infer an infrastructure date from commissioning year or survivor cutoff. |
| Related facts | All charging facts, `FactStateEVChargingComparison`, and `FactTemporalSensitivity`. |

### DimChargingPowerBand `[ASSESS ONLY]`

The current aggregate facts expose threshold counts, not a power-band row
dimension. `connector_power_raw` is a semicolon-separated point field and
`connector_power_kw_single` is only populated for a single numeric value. A
future point-level fact could add a mutually exclusive `power_class` plus
separate `is_ge_150_kw` and `is_ge_350_kw` flags. The thresholds are nested, so
they must not be represented as four mutually additive categories. No such
dimension is required for the initial Batch 19 aggregate sources.

### DimEquipmentStatus `[ASSESS ONLY]`

The actual equipment status field is `core.charging_equipment.status` (`VARCHAR`)
with current values `In Betrieb` and `In Wartung`. A future equipment-detail
fact may relate to a status dimension at the charging snapshot date. The
current aggregate exports do not carry one row per status, and a status label is
not uptime or historical availability. No status dimension is required for the
initial subject models.

## 3. Facts

### FactNationalCharging

| Contract item | Specification |
|---|---|
| Grain | One Germany aggregate × one BNetzA snapshot; current export has one row |
| Current source | `data/exports/tableau/national_charging_2026_09_30.csv`; source objects `core.charging_equipment` and `core.charging_point` |
| Natural key | Current contract: `geography_name`; future versioned key: `(geography_name, bnetza_reference_date)` |
| Candidate PK | `national_charging_fact_key` `[CONCEPTUAL]`; unnecessary for the current singleton export |
| Foreign keys | `charging_snapshot_key` `[CONCEPTUAL]`; no `state_key` |
| Actual columns | `geography_name`, `bnetza_reference_date`, `equipment_count`, `declared_charging_point_count`, `charging_point_count`, `normal_charging_point_count`, `fast_charging_point_count`, `points_ge_150_kw`, `points_ge_350_kw`, `unclassifiable_power_point_count`, `equipment_nominal_power_mw`, `fast_point_share_pct`, `points_ge_150_share_pct`, `points_ge_350_share_pct` |
| Additive measures | Equipment/point counts, threshold counts, and equipment nominal MW within this snapshot |
| Non-additive measures | Three percentage columns; recalculate from counts when filtering |
| Limitation | Never union with or relate as a seventeenth state. Do not sum national and state rows. |

### FactStateCharging

| Contract item | Specification |
|---|---|
| Grain | One German Bundesland × one BNetzA snapshot |
| Current source | `data/exports/tableau/state_charging_2026_09_30.csv`; state view is source-aware and independently reconciled |
| Natural key | `(state_name, bnetza_reference_date)`; current one-snapshot contract key is `state_name` |
| Candidate PK | `state_charging_fact_key` `[CONCEPTUAL]` |
| Foreign keys | `state_key`, `charging_snapshot_key` `[CONCEPTUAL]` |
| Actual columns | `state_name`, `bnetza_reference_date`, equipment/point/power count columns, `equipment_nominal_power_mw`, three within-state percentage columns, `charging_point_national_share_pct` |
| Additive measures | Equipment, declared/populated points, normal/fast/threshold points, nominal MW within one snapshot |
| Non-additive measures | Within-state shares and national share; calculate from aggregated counts where possible |
| Limitation | A state row related to all three KBA dates repeats charging measures. Select exactly one KBA date or use the pre-combined comparison fact. |

### FactBBSRCharging

| Contract item | Specification |
|---|---|
| Grain | One harmonized historical BBSR target unit × one BNetzA snapshot × one BBSR vintage |
| Current source | `data/exports/tableau/bbsr_district_charging_2025_geography.csv`; `analytics.charging_by_bbsr_district_2025_harmonized` |
| Natural key | `(historical_bbsr_administrative_district_code, bbsr_reference_date, bnetza_reference_date, harmonization_version)`; current export key is the target code |
| Candidate PK | `bbsr_charging_fact_key` `[CONCEPTUAL]` |
| Foreign keys | `bbsr_region_key`, `bbsr_settlement_type_key`, `charging_snapshot_key` `[CONCEPTUAL]` |
| Actual columns | Historical BBSR code/name/state/type, `bbsr_reference_date`, `bnetza_reference_date`, component count/names, boundary/mapping/status provenance, equipment/point/power counts, nominal MW, within-unit and national shares |
| Additive measures | Equipment, declared/populated points, threshold counts, nominal MW within the one BNetzA snapshot |
| Non-additive measures | Unit/national shares and percentages; all provenance/status fields |
| Limitation | 400 historical targets come from 401 source components. This is charging-only and must not be joined to KBA stock. |

### FactBBSRTypeCharging

| Contract item | Specification |
|---|---|
| Grain | One harmonized BBSR settlement type × one BNetzA snapshot × one BBSR vintage |
| Current source | `data/exports/tableau/bbsr_type_charging_2025_geography.csv`; `analytics.charging_by_bbsr_type_2025_harmonized` |
| Natural key | `(bbsr_settlement_type_code, bbsr_reference_date, bnetza_reference_date, harmonization_version)` |
| Candidate PK | `bbsr_type_charging_fact_key` `[CONCEPTUAL]` |
| Foreign keys | `bbsr_settlement_type_key`, `charging_snapshot_key` `[CONCEPTUAL]` |
| Actual columns | Type code/name, both dates, historical unit/component counts, equipment/point/threshold counts, nominal MW, within-type and national share columns, classification scope |
| Additive measures | Category equipment/point/threshold counts and nominal MW for the selected vintage/snapshot |
| Non-additive measures | All `_pct` columns and unit/component counts when mixed with district rows |
| Limitation | This is an aggregate presentation fact. Do not join it to `FactBBSRCharging` and sum both. |

### FactBBSRSourceCharging `[CONCEPTUAL]`

| Contract item | Specification |
|---|---|
| Grain | One BNetzA source geography/component × one BNetzA snapshot × one official Batch 13 bridge vintage |
| Current source | DuckDB `analytics.charging_by_bbsr_district_2025`; no Batch 19 CSV is exported at this 401-row grain |
| Natural key | Source-local BNetzA identity (`bnetza_source_id`, state, district, administrative type, snapshot, bridge version); do not use BBSR code alone |
| Candidate PK | `bbsr_source_charging_fact_key` `[CONCEPTUAL]` |
| Foreign keys | A source-geography key `[CONCEPTUAL]`, `charging_snapshot_key`; optional BBSR type only where status supports it |
| Measures | Existing view fields `equipment_count`, `charging_point_count`, threshold counts, nominal power and shares |
| Limitation | Needed for KPI `BBSR-014` only if source-grain reporting is approved. `UNCLASSIFIED`, `CONDITIONAL_VINTAGE`, and `UNRESOLVED` statuses remain visible. |

### FactKBAStateStock

| Contract item | Specification |
|---|---|
| Grain | One Bundesland × one KBA stock reference date |
| Current source | `data/exports/tableau/kba_state_ev_stock_2026.csv`; `core.kba_state_fuel_stock` |
| Natural key | `(state_name, kba_reference_date)` |
| Candidate PK | `kba_state_stock_fact_key` `[CONCEPTUAL]` |
| Foreign keys | `state_key`, `kba_stock_date_key` `[CONCEPTUAL]` |
| Actual columns | `state_name`, `kba_reference_date`, passenger/BEV/PHEV/combined stock, penetration columns, January-baseline changes and growth columns |
| Additive measures | Passenger, BEV, PHEV, and combined stock across compatible states/regions for one date; combined stock is a derived value, not an additional source category |
| Semi-additive measures | All stock counts across dates; never sum dates |
| Non-additive measures | Penetration, growth, and change percentages; recompute from stock components when filtering |
| Limitation | The exported state fact excludes `Deutschland` and `Sonstige`; national totals are a separate KBA scope. `darunter Plug-in` is nested and is not added to `Hybrid insgesamt`. |

### FactKBARegistrationRegionStock

| Contract item | Specification |
|---|---|
| Grain | One KBA registration region × one KBA stock reference date |
| Current source | `data/exports/tableau/kba_registration_region_ev_stock_2026.csv`; `core.kba_district_ev_stock` |
| Natural key | `(kba_registration_region_code, kba_reference_date)` |
| Candidate PK | `kba_registration_region_stock_fact_key` `[CONCEPTUAL]` |
| Foreign keys | `kba_registration_region_key`, `kba_stock_date_key`, optional explicit `state_key` `[CONCEPTUAL]` |
| Actual columns | Code/name/state/date, passenger/BEV/PHEV/combined stock, penetration, January-baseline changes and growth |
| Additive measures | Stock counts across compatible KBA regions for one date |
| Semi-additive measures | Stock counts across dates; never sum dates |
| Non-additive measures | Penetration, growth, and rank fields |
| Limitation | KBA code `07211` remains one region on all dates. It is not two rows and cannot be allocated to Trier city/Trier-Saarburg. It is not a BBSR region. |

### FactKBANationalHistory

| Contract item | Specification |
|---|---|
| Grain | One deduplicated national KBA stock date |
| Current source | `data/exports/tableau/kba_national_stock_history.csv`; `analytics.kba_national_quarterly_stock` |
| Natural key | `stock_date` |
| Candidate PK | `kba_national_history_fact_key` `[CONCEPTUAL]` |
| Foreign keys | `kba_stock_date_key` in the national-history role |
| Actual columns | `stock_date`, `source_report_snapshot`, BEV/PHEV/passenger/combined stock, penetration percentages, `source_object` |
| Additive measures | None across dates; one national observation per stock date |
| Semi-additive measures | All stock values are point-in-time |
| Non-additive measures | Penetration and source metadata |
| Limitation | National history is not regional history and must not be combined with state or registration-region stock as additive partitions. |

### FactStateEVChargingComparison

| Contract item | Specification |
|---|---|
| Grain | One Bundesland × fixed KBA `2026-07-01` / BNetzA `2026-09-30` comparison context |
| Current source | `data/exports/tableau/state_ev_charging_comparison_2026.csv`; validated Batch 16 source |
| Natural key | `state_name` for the current fixed context; future versioned key includes both source dates and comparison scope |
| Candidate PK | `state_ev_charging_comparison_fact_key` `[CONCEPTUAL]` |
| Foreign keys | `state_key`, `kba_stock_date_key`, `charging_snapshot_key` `[CONCEPTUAL]` |
| Actual columns | Both dates/context labels; KBA stock; BNetzA point counts; ratios per point/1,000 BEVs; shares/gap; publication-status columns |
| Additive measures | Component counts only within the fixed 16-state scope |
| Non-additive measures | All ratios, shares, gaps, ranks and status labels |
| Limitation | This is a pre-combined cross-snapshot descriptive fact. Do not rebuild it by relating state charging to all KBA dates, and do not call it adequacy, shortage, surplus, demand, or utilization. |

### FactTemporalSensitivity

| Contract item | Specification |
|---|---|
| Grain | One Bundesland × fixed KBA date × BNetzA date × survivor cutoff and two explicitly labelled perspectives |
| Current source | `data/exports/tableau/state_temporal_sensitivity_2026.csv`; validated Batch 17 source |
| Natural key | `(state_name, kba_reference_date, bnetza_reference_date, survivor_cutoff_date)` for the current one-row-per-state context |
| Candidate PK | `temporal_sensitivity_fact_key` `[CONCEPTUAL]` |
| Foreign keys | `state_key`, `kba_stock_date_key`, `charging_snapshot_key` `[CONCEPTUAL]` |
| Actual columns | Published/survivor equipment, point, threshold, nominal power and ratios; later complement; deltas; rank changes; labels and `publication_status` |
| Additive measures | Published/survivor counts only within the fixed state/context and within one perspective |
| Non-additive measures | Ratios, deltas expressed as percentages, ranks, labels and status |
| Limitation | Survivor rows retain September attributes and are explicitly **not actual July infrastructure**. Do not relate this fact to raw charging/KBA facts and sum repeated measures. |

## 4. Optional future facts for Batch 21 or later

The following logical facts are not required for the nine initial exports but
are the correct homes for currently exploratory or unsupported detail:

- `FactEquipmentStatusCommissioning` from `core.charging_equipment` for
  `INF-010` and `INF-011`.
- `FactKBAOwnership` from the validated Batch 15 ownership output for
  `KBA-035`.
- `FactKBAPostcodeStock` and `FactKBAMunicipalityStock` from the existing core
  tables for `KBA-036` and `KBA-037`.
- `FactEquipment` and `FactChargingPoint` for city/county, operator, payment,
  opening-hours, and connector descriptions. These must keep equipment and
  point grains separate.
- `FactBBSRScenarioCharging` from the owner-approved scenario view only if a
  clearly separated scenario presentation is approved.

No fact listed in this section is created or exported by Batch 20.
