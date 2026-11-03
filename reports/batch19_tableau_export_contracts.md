# Batch 19 — Tableau export contracts

**Export version:** `batch19-tableau-exports-2026-11-03-v1`
**Validation status:** `PASS`
**Export directory:** `data/exports/tableau/`

These contracts define the CSV interfaces prepared from the existing local
analytical data. They do not implement a Tableau workbook or prescribe a
physical Tableau data model. Every file is UTF-8, LF-terminated, ordered
deterministically, and contains no generation timestamp.

## Shared conventions

- Blank CSV cells represent source or calculation `NULL`; missing measurements
  are never replaced with zero. Current headline count fields are non-null and
  validated. January baseline-change fields are blank because no earlier
  snapshot exists in the extract.
- Dates are ISO 8601 `YYYY-MM-DD`. Counts are integer numeric fields. Shares
  are numeric percentage-point values expressed from 0 to 100, not formatted
  strings. Ratios are numeric. Nominal equipment power is MW, rounded to four
  decimal places; other numeric calculations use up to ten decimal places.
- Natural keys are unique within each file. Geographic names are source labels;
  no unvalidated state code was invented because the state-level source objects
  expose validated names but no state identifier.
- BNetzA `charging_point_count` means populated charging-point slots. It is
  distinct from equipment records and from connector count. Point power bands
  use the maximum numeric token in `connector_power_raw` for each point:
  `<=22 kW` normal, `>22 kW` fast, with nested `>=150 kW` and `>=350 kW`
  thresholds.
- `equipment_nominal_power_mw` is the sum of equipment-level declared nominal
  power. It is not simultaneously deliverable charging power, energy delivered,
  utilization, or availability.
- KBA values are registered passenger-car stock. They are not new registrations
  or sales. `phev_passenger_car_stock` comes from the nested `darunter
  Plug-in` field and is never added to the mutually exclusive `Hybrid insgesamt`
  row.

## Export inventory and contracts

### A — `national_charging_2026_09_30.csv`

| Contract item | Definition |
|---|---|
| Purpose | Germany-wide BNetzA infrastructure snapshot |
| Grain | One row for Germany |
| Primary key | `geography_name` |
| Rows / columns | 1 / 14 |
| Source objects | `core.charging_equipment`, `core.charging_point` |
| Source date | BNetzA `2026-09-30` |
| KPI status | Counts, shares and declared nominal power: `HEADLINE_READY_WITH_DATES` |

| Column | Definition / unit |
|---|---|
| `geography_name` | Fixed display geography `Germany` |
| `bnetza_reference_date` | BNetzA snapshot date |
| `equipment_count` | Equipment records |
| `declared_charging_point_count` | Sum of equipment-declared point counts |
| `charging_point_count` | Populated point slots |
| `normal_charging_point_count` | Point slots with maximum parsed power <=22 kW |
| `fast_charging_point_count` | Point slots with maximum parsed power >22 kW |
| `points_ge_150_kw` | Point slots with maximum parsed power >=150 kW |
| `points_ge_350_kw` | Point slots with maximum parsed power >=350 kW |
| `unclassifiable_power_point_count` | Point slots with no valid parsed power; currently 0 |
| `equipment_nominal_power_mw` | Sum of equipment nominal kW / 1,000 |
| `fast_point_share_pct` | Fast point slots / all point slots × 100 |
| `points_ge_150_share_pct` | >=150 kW point slots / all point slots × 100 |
| `points_ge_350_share_pct` | >=350 kW point slots / all point slots × 100 |

Do not union this row with state rows and then sum measures. It is the national
aggregate, not a seventeenth state.

### B — `state_charging_2026_09_30.csv`

| Contract item | Definition |
|---|---|
| Purpose | BNetzA infrastructure profile by Bundesland |
| Grain | One named federal state |
| Primary key | `state_name` |
| Rows / columns | 16 / 15 |
| Source objects | `analytics.charging_by_state`, `core.charging_equipment`, `core.charging_point` |
| Source date | BNetzA `2026-09-30` |
| KPI status | Single-source counts, shares and declared nominal power: `HEADLINE_READY_WITH_DATES` |

The columns are `state_name`, `bnetza_reference_date`, `equipment_count`,
`declared_charging_point_count`, `charging_point_count`,
`normal_charging_point_count`, `fast_charging_point_count`, `points_ge_150_kw`,
`points_ge_350_kw`, `unclassifiable_power_point_count`,
`equipment_nominal_power_mw`, `fast_point_share_pct`,
`points_ge_150_share_pct`, `points_ge_350_share_pct`, and
`charging_point_national_share_pct`. Their definitions and units are the same
as Export A, except the last field is the state's populated point slots divided
by all 211,253 registered point slots.

The existing state view was inspected and not altered. It pre-aggregates point
rows by `(source_id, equipment_excel_row)` before joining to equipment. The
export independently recomputes state point power bands and reconciles the
state sum to Export A.

### C — `bbsr_district_charging_2025_geography.csv`

| Contract item | Definition |
|---|---|
| Purpose | Charging-only infrastructure on the Batch 13.2 historical BBSR geography |
| Grain | One historical BBSR 2025 administrative geographic unit |
| Primary key | `historical_bbsr_administrative_district_code` |
| Rows / columns | 400 / 27 |
| Source object | `analytics.charging_by_bbsr_district_2025_harmonized` |
| Source dates | BBSR geographic stand `2025-12-31`; BNetzA infrastructure `2026-09-30` |
| KPI status | Charging-only counts, shares and declared nominal power: `HEADLINE_READY_WITH_DATES` |

| Column group | Columns and definition |
|---|---|
| Geography | `historical_bbsr_administrative_district_code`, `historical_bbsr_administrative_district_name`, `historical_bbsr_federal_state_code`, `historical_bbsr_federal_state_name`, `historical_bbsr_settlement_type_code`, `historical_bbsr_settlement_type_name_de` — validated BBSR identifiers and source labels |
| Dates | `bbsr_reference_date`, `bnetza_reference_date` |
| Harmonization provenance | `source_component_count`, `source_component_names`, `historical_boundary_basis`, `mapping_method`, `boundary_compatibility_status` |
| Equipment / point counts | `equipment_count`, `declared_charging_point_count`, `charging_point_count`, `normal_charging_point_count`, `fast_charging_point_count`, `points_ge_150_kw`, `points_ge_350_kw`, `unclassifiable_power_point_count` |
| Power | `equipment_nominal_power_mw` — MW at equipment grain |
| Within-unit shares | `fast_point_share_pct`, `points_ge_150_share_pct`, `points_ge_350_share_pct` — percentage of that unit's point slots |
| National shares | `equipment_national_share_pct`, `charging_point_national_share_pct` — share of the national BNetzA total |

The 401 source components form 400 historical target units. Hanau and the
remaining Main-Kinzig-Kreis component consolidate to historical BBSR code
`06435000`, type 2. Kassel city is `06611000`, type 1. Trier city (`07211000`,
type 1) and Trier-Saarburg (`07235000`, type 3) remain separate BNetzA charging
components. This export contains no KBA stock and does not use the owner-
approved Hanau scenario as the official baseline. A 2026 infrastructure count
must not be described as infrastructure observed in 2025.

### D — `bbsr_type_charging_2025_geography.csv`

| Contract item | Definition |
|---|---|
| Purpose | Four-category charging-only summary of the 400 historical BBSR units |
| Grain | One BBSR settlement type |
| Primary key | `bbsr_settlement_type_code` |
| Rows / columns | 4 / 23 |
| Source objects | `analytics.charging_by_bbsr_type_2025_harmonized`, reconciled to `analytics.charging_by_bbsr_district_2025_harmonized` |
| Source dates | BBSR `2025-12-31`; BNetzA `2026-09-30` |
| KPI status | Charging-only type counts/shares: `HEADLINE_READY_WITH_DATES`; distribution interpretation remains descriptive |

Columns are `bbsr_settlement_type_code`, `bbsr_settlement_type_name_de`,
`bbsr_reference_date`, `bnetza_reference_date`,
`historical_bbsr_unit_count`, `source_component_count`, `equipment_count`,
`charging_point_count`, `normal_charging_point_count`,
`fast_charging_point_count`, `points_ge_150_kw`, `points_ge_350_kw`,
`equipment_nominal_power_mw`, `fast_point_share_pct`,
`points_ge_150_share_pct`, `points_ge_350_share_pct`,
`equipment_national_share_pct`, `charging_point_national_share_pct`,
`fast_point_national_share_pct`, `points_ge_150_national_share_pct`,
`points_ge_350_national_share_pct`,
`equipment_nominal_power_national_share_pct`, and `classification_scope`.
Counts are counts of units, equipment or point slots as named; all `_pct`
fields are calculated from aggregated numerators and denominators and must not
be summed. The validated unit counts are type 1 = 68, type 2 = 131, type 3 =
98, type 4 = 103. Only the validated German label is exported; no unvalidated
English translation is supplied.

### E — `kba_state_ev_stock_2026.csv`

| Contract item | Definition |
|---|---|
| Purpose | Registered KBA passenger-car stock by named federal state and snapshot |
| Grain | One Bundesland × KBA stock date |
| Primary key | `state_name, kba_reference_date` |
| Rows / columns | 48 / 13 |
| Source object | `core.kba_state_fuel_stock` |
| Source dates | `2026-01-01`, `2026-04-01`, `2026-07-01` |
| KPI status | Stock, penetration and snapshot change: `HEADLINE_READY_WITH_DATES` |

| Column | Definition / unit |
|---|---|
| `state_name`, `kba_reference_date` | KBA state label and stock date |
| `passenger_car_stock` | Sum of six mutually exclusive FZ 27.2 fuel rows |
| `bev_passenger_car_stock` | `Elektro (BEV)` passenger-car stock |
| `phev_passenger_car_stock` | Nested `darunter Plug-in` passenger-car stock |
| `combined_plugin_passenger_car_stock` | BEV + PHEV stock; descriptive combined count |
| `bev_penetration_pct`, `phev_penetration_pct` | Stock / same-state passenger-car stock × 100 |
| `combined_plugin_penetration_pct` | Combined plug-in stock / passenger-car stock × 100 |
| `bev_stock_change_from_2026_01_01` | Current BEV stock minus January BEV stock |
| `bev_stock_growth_pct_from_2026_01_01` | January-baselined BEV stock change × 100 |
| `phev_stock_change_from_2026_01_01` | Current PHEV stock minus January PHEV stock |
| `phev_stock_growth_pct_from_2026_01_01` | January-baselined PHEV stock change × 100 |

`Deutschland` and `Sonstige` are deliberately excluded from the export and are
retained as separate residual reconciliation scopes in the validation report.
Stock changes are not registrations or sales.

### F — `kba_registration_region_ev_stock_2026.csv`

| Contract item | Definition |
|---|---|
| Purpose | KBA registration-region passenger-car stock without BBSR assignment |
| Grain | One KBA registration region × KBA stock date |
| Primary key | `kba_registration_region_code, kba_reference_date` |
| Rows / columns | 1,200 / 15 |
| Source object | `core.kba_district_ev_stock` |
| Source dates | `2026-01-01`, `2026-04-01`, `2026-07-01` |
| KPI status | Stock, penetration and snapshot change: `HEADLINE_READY_WITH_DATES`; growth ranking is not promoted here |

Columns are `kba_registration_region_code` (string, preserving leading zeros),
`registration_region_name`, `state_name`, `kba_reference_date`,
`passenger_car_stock`, `bev_passenger_car_stock`,
`phev_passenger_car_stock`, `combined_plugin_passenger_car_stock`,
`bev_penetration_pct`, `phev_penetration_pct`,
`combined_plugin_penetration_pct`, `bev_stock_change_from_2026_01_01`,
`bev_stock_growth_pct_from_2026_01_01`,
`phev_stock_change_from_2026_01_01`, and
`phev_stock_growth_pct_from_2026_01_01`. Units and formulas match Export E,
with KBA registration-region scope.

Code `07211` remains `TRIER-SAARBURG` as one region on all three dates. Its
stock is not allocated between Trier city and Trier-Saarburg. These 400 KBA
registration regions are not assumed to be the 400 historical BBSR units.

### G — `state_ev_charging_comparison_2026.csv`

| Contract item | Definition |
|---|---|
| Purpose | Validated Batch 16 descriptive comparison at the 16-state scope |
| Grain | One Bundesland |
| Primary key | `state_name` |
| Rows / columns | 16 / 28 |
| Source | `reports/batch16_state_comparison.csv` |
| Source dates | KBA `2026-07-01`; BNetzA `2026-09-30` |
| KPI status | Single-source fields `HEADLINE_READY_WITH_DATES`; BEVs/point and inverse `CONTEXT_ONLY`; fast/HPC per-1,000 and share gap `EXPLORATORY_SENSITIVITY` |

| Column group | Columns |
|---|---|
| Identity/dates | `state_name`, `kba_reference_date`, `bnetza_reference_date`, `comparison_scope`, `cross_source_temporal_label`, `cross_source_date_note` |
| KBA stock | `passenger_car_stock`, `bev_passenger_car_stock`, `phev_passenger_car_stock`, `bev_penetration_pct` |
| BNetzA counts | `charging_point_count`, `fast_point_count`, `points_ge_150_kw`, `points_ge_350_kw` |
| Ratios | `bevs_per_charging_point`, `registered_charging_points_per_1000_bevs`, `fast_points_per_1000_bevs`, `points_ge_150_per_1000_bevs`, `points_ge_350_per_1000_bevs` |
| Compositional shares | `bev_stock_share_pct`, `charging_point_share_pct`, `bev_stock_minus_charging_point_share_pp` |
| Status flags | `bevs_per_charging_point_publication_status`, `registered_charging_points_per_1000_bevs_publication_status`, `fast_points_per_1000_bevs_publication_status`, `points_ge_150_per_1000_bevs_publication_status`, `points_ge_350_per_1000_bevs_publication_status`, `bev_stock_minus_charging_point_share_publication_status` |

This file is not a same-day adequacy, shortage or surplus table. September
charging values must not be repeated across multiple KBA dates; this file has
one explicit KBA date only.

### H — `state_temporal_sensitivity_2026.csv`

| Contract item | Definition |
|---|---|
| Purpose | Batch 17 published-versus-survivor sensitivity disclosure |
| Grain | One Bundesland; one KBA July denominator and one September published/survivor comparison |
| Primary key | `state_name` |
| Rows / columns | 16 / 80 |
| Source | `reports/batch17_state_temporal_sensitivity.csv`, with `publication_status` appended |
| Source dates | KBA `2026-07-01`; BNetzA `2026-09-30`; inclusive survivor cutoff `2026-07-01` |
| KPI status | `EXPLORATORY_SENSITIVITY` |

The first 79 columns preserve the validated Batch 17 header exactly:

`state_name`, `kba_reference_date`, `bnetza_reference_date`,
`survivor_cutoff_date`, `bev_stock`, `phev_stock`, `passenger_car_stock`,
`bev_penetration_pct`, `bev_stock_share_of_16_state_stock_pct`,
`published_equipment_count`, `published_charging_point_count`,
`published_normal_point_count`, `published_fast_point_count`,
`published_points_ge_150`, `published_points_ge_350`,
`published_fast_point_share_pct`, `published_points_ge_150_share_pct`,
`published_points_ge_350_share_pct`, `published_equipment_nominal_power_mw`,
`published_point_share_of_16_state_points_pct`, `survivor_equipment_count`,
`survivor_charging_point_count`, `survivor_normal_point_count`,
`survivor_fast_point_count`, `survivor_points_ge_150`,
`survivor_points_ge_350`, `survivor_fast_point_share_pct`,
`survivor_points_ge_150_share_pct`, `survivor_points_ge_350_share_pct`,
`survivor_equipment_nominal_power_mw`, `published_bevs_per_point`,
`survivor_bevs_per_point`, `published_points_per_1000_bevs`,
`survivor_points_per_1000_bevs`, `published_fast_points_per_1000_bevs`,
`survivor_fast_points_per_1000_bevs`, `published_ge150_points_per_1000_bevs`,
`survivor_ge150_points_per_1000_bevs`, `published_ge350_points_per_1000_bevs`,
`survivor_ge350_points_per_1000_bevs`, `later_equipment_count`,
`later_charging_point_count`, `later_normal_point_count`,
`later_fast_point_count`, `later_points_ge_150`, `later_points_ge_350`,
`later_invalid_power_points`, `later_point_share_of_state_published_pct`,
`published_minus_survivor_equipment_count`,
`published_minus_survivor_charging_point_count`,
`published_minus_survivor_fast_point_count`,
`published_minus_survivor_points_ge_150`,
`published_minus_survivor_points_ge_350`,
`survivor_minus_published_bevs_per_point`,
`survivor_minus_published_bevs_per_point_pct`,
`survivor_minus_published_points_per_1000_bevs`,
`survivor_minus_published_points_per_1000_bevs_pct`,
`survivor_minus_published_fast_points_per_1000_bevs`,
`survivor_minus_published_fast_points_per_1000_bevs_pct`,
`survivor_minus_published_ge150_points_per_1000_bevs`,
`survivor_minus_published_ge150_points_per_1000_bevs_pct`,
`survivor_minus_published_ge350_points_per_1000_bevs`,
`survivor_minus_published_ge350_points_per_1000_bevs_pct`,
`survivor_minus_published_fast_point_share_pp`,
`published_bevs_per_point_rank`, `survivor_bevs_per_point_rank`,
`bevs_per_point_rank_change_survivor_minus_published`,
`published_fast_points_per_1000_rank`, `survivor_fast_points_per_1000_rank`,
`fast_points_per_1000_rank_change_survivor_minus_published`,
`published_ge150_points_per_1000_rank`, `survivor_ge150_points_per_1000_rank`,
`ge150_points_per_1000_rank_change_survivor_minus_published`,
`published_ge350_points_per_1000_rank`, `survivor_ge350_points_per_1000_rank`,
`ge350_points_per_1000_rank_change_survivor_minus_published`, `status_labels`,
`temporal_label_published`, and `temporal_label_survivor`.

The final `publication_status` field is `EXPLORATORY_SENSITIVITY` for every
row. The survivor label explicitly says `NOT ACTUAL JULY INFRASTRUCTURE`.
The cohort retains September point attributes for currently represented
equipment commissioned on or before the cutoff; it is not a historical July
stock and cannot be used to claim additions, removals, availability or
adequacy.

### Optional national history — `kba_national_stock_history.csv`

| Contract item | Definition |
|---|---|
| Purpose | Validated national KBA quarterly stock history |
| Grain | One deduplicated national row per `stock_date` |
| Primary key | `stock_date` |
| Rows / columns | 33 / 10 |
| Source object | `analytics.kba_national_quarterly_stock` |
| Source range | `2018-07-01` through `2026-07-01`; source report snapshot retained |
| KPI status | National stock trajectory: `HEADLINE_READY_WITH_DATES` |

Columns are `stock_date`, `source_report_snapshot`,
`bev_passenger_car_stock`, `phev_passenger_car_stock`,
`passenger_car_stock`, `combined_plugin_passenger_car_stock`,
`bev_penetration_pct`, `phev_penetration_pct`,
`combined_plugin_penetration_pct`, and `source_object`. This is national
history only; no regional history is inferred from it.

## Tableau relationship recommendations

Safe relationships, only at the stated grain:

- Export B to Export E on `state_name` only after selecting one KBA
  `kba_reference_date`; retain both source dates and do not sum repeated
  charging rows across KBA dates.
- Export E to itself on `(state_name, kba_reference_date)` when comparing
  snapshots.
- Export F to itself on
  `(kba_registration_region_code, kba_reference_date)`.
- Export C to Export D on the validated mapping
  `C.historical_bbsr_settlement_type_code = D.bbsr_settlement_type_code`;
  aggregate C numerators before recalculating D shares.
- Export G is already a one-row-per-state cross-source comparison and should
  not be joined to multiple KBA dates.

Prohibited or unsafe relationships:

- Export C or D to Export F: the 400 historical BBSR units are not the 400 KBA
  registration regions.
- Any allocation of KBA code `07211` between Trier city and Trier-Saarburg.
- Joining national Export A to state Export B and summing both.
- Summing precomputed percentages or treating a percentage as a count.
- Treating BBSR `2025-12-31` geography as a 2026 geography.
- Treating the Batch 17 survivor cohort as observed July infrastructure.
- Using any cross-source ratio as infrastructure adequacy, shortage, surplus,
  utilization, accessibility, demand or causal evidence.

The complete file-level checksums and source-object inventory are in
[`data/exports/tableau/export_manifest.json`](../data/exports/tableau/export_manifest.json).
Measured validation is in
[`batch19_tableau_data_validation.md`](batch19_tableau_data_validation.md).
