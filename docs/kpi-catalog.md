# KPI catalog

## Status vocabulary

- VALIDATED: the current source fields, grain, formula, and reconciliation have been checked against the local artifacts. This is descriptive validation, not a claim that the source is exhaustive.
- PROVISIONAL: calculable from current data, but affected by a documented date, coverage, geographic, parsing, or interpretation limitation.
- PROPOSED: useful for a future model or dashboard, but not yet implemented or sufficiently validated.

All KPIs must carry the source reference date and the geographic grain in the output. A KBA stock value is registered stock, not new vehicle sales.

## Current national baseline

| KPI | Current observed value | Grain and date | Status |
|---|---:|---|---|
| Registered charging equipment count | 117,662 | BNetzA equipment, 2026-09-30 | VALIDATED |
| Charging-point slot count | 211,253 | BNetzA point slots, 2026-09-30 | VALIDATED |
| Normal point count | 156,155 | Maximum declared point power <=22 kW | VALIDATED |
| Fast point count | 55,098 | Maximum declared point power >22 kW | VALIDATED |
| Fast charging share | 26.08% | 55,098 / 211,253 | VALIDATED |
| High-power point count | 40,950 | Maximum declared point power >=150 kW | VALIDATED |
| High-power charging share | 19.38% | 40,950 / 211,253 | VALIDATED |
| Point count >=350 kW | 6,950 | Maximum declared point power >=350 kW | VALIDATED |
| Declared equipment nominal power | 9,215.42 MW | Sum of equipment kW / 1,000 | VALIDATED |
| District BEV stock | 2,362,218 | KBA 400 district rows, 2026-07-01 | VALIDATED |
| District PHEV stock | 1,225,241 | KBA 400 district rows, 2026-07-01 | VALIDATED |
| District BEV growth January to July | +330,348 / +16.26% | Same 400 district rows | VALIDATED |

Power KPIs use a read-only derivation from connector_power_raw: split each point's semicolon-separated text, parse numeric tokens, and classify by the maximum token in that point row. This is distinct from connector_power_kw_single, which is populated only for a single numeric raw value.

### Batch 05/06 regional validation and deployed-layer note

The same definitions were recomputed at KBA district-code grain after mapping the 401 BNetzA source geographies and aggregating to 400 KBA codes. The regional result retained 117,662 equipment rows and 211,253 point slots, with 156,155 normal points, 55,098 fast points, 40,950 points at least 150 kW, 6,950 points at least 350 kW, and 9,215.4173 MW of declared equipment nominal power. Percentages use the point-slot denominator within each KBA code. All regional outputs must carry `bnetza_reference_date = 2026-09-30`, the actual KBA `reference_date`, and the mapping verification flags.

The combined validation grain is one KBA district code per KBA stock date: 400 codes × three dates = 1,200 rows. Infrastructure measures are repeated beside the three KBA snapshots for comparison and must never be summed across dates. The 24 provisional source mappings remain visible as quality flags; they are not promoted to officially verified mappings.

Batch 06 deployed these definitions in `analytics.charging_by_kba_district_2026_09_30` and `analytics.kba_district_charging_vs_bev_2026`. The regional view exposes `normal_charging_point_count`, `fast_charging_point_count`, `points_ge_150_kw`, `points_ge_350_kw`, `fast_charging_share_pct`, `high_power_charging_share_pct`, `equipment_nominal_power_kw`, `equipment_nominal_power_mw`, and `points_without_valid_power`. The combined view adds KBA state/district names, the actual `kba_reference_date`, `bev_per_registered_charging_point`, passenger-car/BEV/PHEV stock, and the same mapping-quality flags. The BEV-per-point ratio remains PROVISIONAL because the infrastructure and vehicle dates differ, the BNetzA register is not exhaustive, and the crosswalk remains partly provisional.

## Charging infrastructure KPIs

### 1. Registered charging equipment count

- Business question: How many equipment records are present in the published register?
- Definition: Count rows in core.charging_equipment.
- Formula: COUNT(*) at BNetzA source and snapshot.
- Units: Equipment records.
- Source tables: core.charging_equipment; BNetzA source file.
- Grain: Germany, state, or BNetzA district; BNetzA reference date 2026-09-30.
- Filters and exclusions: No status filter for the headline total. Metadata rows are already excluded by the normalized table.
- Interpretation: One registered equipment record may contain several charging-point slots.
- Known limitations: The published register is not exhaustive of every publicly accessible charger in Germany.
- Status: VALIDATED.

### 2. Charging-point slot count

- Business question: How many populated charging-point slots are represented by the equipment records?
- Definition: Count rows in core.charging_point.
- Formula: COUNT(*) by geography.
- Units: Populated point slots.
- Source tables: core.charging_point joined to core.charging_equipment for geography.
- Grain: Point slot, geography, and BNetzA snapshot.
- Filters and exclusions: A slot is retained when one of its repeated point fields is populated. No connector explosion.
- Interpretation: This is the project’s point-level infrastructure measure.
- Known limitations: A slot is not a connector count and does not measure simultaneous service capacity.
- Status: VALIDATED.

### 3. Normal charging points

- Business question: How many point slots have a maximum declared power at or below 22 kW?
- Definition: A point is normal when the maximum numeric token in connector_power_raw is <=22.
- Formula: COUNT(point rows WHERE MAX(parsed connector_power_raw tokens) <= 22).
- Units: Point slots.
- Source tables: core.charging_point.
- Grain: Point slot, geography, and BNetzA snapshot.
- Filters and exclusions: Semicolon-separated values stay within one point; the maximum token is used. No point is counted more than once.
- Interpretation: A threshold classification of declared point power, not measured delivered power.
- Known limitations: The source text and the parser do not describe utilization or actual output.
- Status: VALIDATED.

### 4. Fast charging points

- Business question: How many point slots exceed 22 kW?
- Definition: A point is fast when its maximum parsed connector-power token is >22 kW.
- Formula: COUNT(point rows WHERE MAX(parsed power) >22).
- Units: Point slots.
- Source tables: core.charging_point.
- Grain: Point slot, geography, and BNetzA snapshot.
- Filters and exclusions: Same maximum-per-point parser as the normal-point KPI.
- Interpretation: 55,098 of 211,253 current point slots meet the threshold.
- Known limitations: Fast is a project threshold, not a claim about charging time or vehicle compatibility.
- Status: VALIDATED.

### 5. Fast charging share

- Business question: What share of the registered point slots are above 22 kW?
- Definition: Fast point count divided by all populated point slots.
- Formula: 100 * COUNT(MAX(parsed power) >22) / COUNT(point rows).
- Units: Percent.
- Source tables: core.charging_point.
- Grain: Germany, state, or BNetzA district; 2026-09-30.
- Filters and exclusions: The denominator is all point slots; current raw power parsing classified all 211,253 rows.
- Interpretation: A descriptive mix measure.
- Known limitations: It is based on declared source power, not operating performance; future source rows with unclassifiable power must be shown as unknown rather than forced into a band.
- Status: VALIDATED for the current snapshot; PROVISIONAL for future snapshots until parsing quality is rechecked.

### 6. High-power charging points, at least 150 kW

- Business question: How many point slots meet the 150 kW threshold?
- Definition: A point is high-power when its maximum parsed connector-power token is >=150 kW.
- Formula: COUNT(point rows WHERE MAX(parsed power) >=150).
- Units: Point slots.
- Source tables: core.charging_point.
- Grain: Point slot and geography.
- Filters and exclusions: Maximum-per-point parser; no connector multiplication.
- Interpretation: 40,950 current point slots meet the threshold.
- Known limitations: The threshold does not establish actual power delivery or availability.
- Status: VALIDATED.

### 7. High-power charging share

- Business question: What share of point slots meet the 150 kW threshold?
- Definition: High-power point count divided by all populated point slots.
- Formula: 100 * COUNT(MAX(parsed power) >=150) / COUNT(point rows).
- Units: Percent.
- Source tables: core.charging_point.
- Grain: Germany, state, or district.
- Filters and exclusions: All current point slots are in the denominator.
- Interpretation: 19.38% of current point slots meet the threshold.
- Known limitations: It is a declared-power mix measure and is not an availability or utilization metric.
- Status: VALIDATED for the current snapshot.

### 8. Charging points at least 350 kW

- Business question: How many point slots meet the 350 kW threshold?
- Definition: A point is in the >=350 kW band when its maximum parsed power is at least 350 kW.
- Formula: COUNT(point rows WHERE MAX(parsed power) >=350).
- Units: Point slots.
- Source tables: core.charging_point.
- Grain: Point slot and geography.
- Filters and exclusions: Maximum-per-point parser.
- Interpretation: 6,950 current point slots meet the threshold.
- Known limitations: No inference about sustained delivery, vehicle acceptance, or queue time.
- Status: VALIDATED.

### 9. Total declared equipment nominal power

- Business question: What is the sum of the equipment-level nominal-power field?
- Definition: Sum equipment_nominal_power_kw over equipment rows, divided by 1,000.
- Formula: SUM(core.charging_equipment.equipment_nominal_power_kw) / 1000.
- Units: MW of declared equipment nominal power.
- Source tables: core.charging_equipment.
- Grain: Germany, state, or district.
- Filters and exclusions: Aggregate from the equipment table only; never join equipment to point rows before summing this field.
- Interpretation: 9,215.42 MW in the current snapshot.
- Known limitations: Nominal power is not energy delivered, simultaneous capacity, or network utilization.
- Status: VALIDATED.

### 10. Equipment status analysis

- Business question: How many equipment records are in each published status?
- Definition: Count equipment rows by status.
- Formula: COUNT(*) GROUP BY status.
- Units: Equipment records.
- Source tables: core.charging_equipment.
- Grain: Equipment status and geography.
- Filters and exclusions: No status is silently filtered from headline counts.
- Interpretation: Current values are 117,642 In Betrieb and 20 In Wartung.
- Known limitations: Status is a source snapshot label; it does not provide uptime or historical availability.
- Status: VALIDATED.

### 11. Commissioning-year analysis

- Business question: How are registered equipment records distributed by parsed commissioning year?
- Definition: Count equipment rows by YEAR(commissioning_date).
- Formula: COUNT(*) GROUP BY EXTRACT(YEAR FROM commissioning_date).
- Units: Equipment records by year.
- Source tables: core.charging_equipment.
- Grain: Commissioning year, geography, and BNetzA snapshot.
- Filters and exclusions: Use parsed date; retain raw date text for audit. Do not treat a commissioning year as an observed installation flow without checking source semantics.
- Interpretation: A descriptive age/cohort profile of the published equipment register.
- Known limitations: It is not a time series of all installations and does not prove when a point became publicly usable.
- Status: VALIDATED as a descriptive distribution.

## Vehicle-stock KPIs

### 12. BEV stock

- Business question: How many battery-electric passenger cars are registered at a given KBA snapshot?
- Definition: Use bev_cars from core.kba_district_ev_stock for district analysis, or the Deutschland / Elektro (BEV) row of core.kba_state_fuel_stock for the national total.
- Formula: SUM(bev_cars) by district_code and reference_date, or the explicitly filtered national state-fuel row.
- Units: Registered BEVs.
- Source tables: core.kba_district_ev_stock and core.kba_state_fuel_stock.
- Grain: District code, state, or national total plus reference_date.
- Filters and exclusions: Do not add district rows to the Deutschland row; choose one reporting grain.
- Interpretation: The district model totals 2,031,870 on 2026-01-01, 2,167,111 on 2026-04-01, and 2,362,218 on 2026-07-01. The state-level Deutschland total is 2,365,047 in July.
- Known limitations: KBA reports stock, not sales, registrations during the interval, or vehicle miles.
- Status: VALIDATED.

### 13. PHEV stock

- Business question: How many plug-in-hybrid passenger cars are registered?
- Definition: Use phev_cars from core.kba_district_ev_stock for district analysis, or the explicitly labelled KBA plug-in row for the national state-level view.
- Formula: SUM(phev_cars) by district_code and reference_date.
- Units: Registered PHEVs.
- Source tables: core.kba_district_ev_stock and core.kba_state_fuel_stock.
- Grain: District, state, or national plus reference_date.
- Filters and exclusions: Do not combine the district and state-level totals in one aggregation.
- Interpretation: The 400-code district total is 1,225,241 on 2026-07-01.
- Known limitations: PHEV is a stock category and is not an energy-use or charging-demand measure.
- Status: VALIDATED.

### 14. BEV absolute stock change between snapshots

- Business question: How much did registered BEV stock change between two KBA snapshots?
- Definition: Later BEV stock minus earlier BEV stock using the same geography and table grain.
- Formula: BEV_t2 - BEV_t1.
- Units: Registered vehicles.
- Source tables: core.kba_district_ev_stock or the national state-fuel total.
- Grain: Same district/state/national geography and two reference dates.
- Filters and exclusions: Compare like-for-like rows and never mix 400-district totals with the Deutschland total.
- Interpretation: The 400-district model increased by 135,241 from January to April and 195,107 from April to July.
- Known limitations: BEV stock growth is not the same as new vehicle sales; it can reflect multiple stock movements and reporting effects.
- Status: VALIDATED as a descriptive stock change.

### 15. BEV percentage stock growth

- Business question: What percentage did registered BEV stock change between two snapshots?
- Definition: Absolute stock change divided by the earlier stock.
- Formula: 100 * (BEV_t2 - BEV_t1) / BEV_t1.
- Units: Percent.
- Source tables: Same KBA table at both dates.
- Grain: Same geography and two reference dates.
- Filters and exclusions: Previous-period BEV stock is the denominator; no sales interpretation.
- Interpretation: The 400-district model grew 16.26% from 2,031,870 on January 1 to 2,362,218 on July 1, 2026.
- Known limitations: It is not a flow measure and cannot alone explain infrastructure demand.
- Status: VALIDATED as a descriptive stock change.

### 16. BEV share of passenger cars

- Business question: What share of the KBA district passenger-car stock is BEV?
- Definition: BEV stock divided by passenger_cars from the same FZ 27.15 district row and date.
- Formula: 100 * SUM(bev_cars) / SUM(passenger_cars).
- Units: Percent.
- Source tables: core.kba_district_ev_stock.
- Grain: District, state aggregate, or Germany-wide 400-district aggregate plus reference_date.
- Filters and exclusions: The denominator must be the confirmed FZ 27.15 passenger-car field at the same grain and date.
- Interpretation: The 400-district July 2026 value is 2,362,218 / 49,644,855 = 4.76%.
- Known limitations: The 400-district aggregate is not exactly the FZ 27.2 Deutschland total; the difference must remain visible.
- Status: VALIDATED where the FZ 27.15 denominator is used.

## Combined regional indicators

### 17. BEVs per registered public charging point

- Business question: How many registered BEVs correspond to each published charging-point slot?
- Definition: KBA district BEV stock divided by BNetzA charging-point slots after mapping and aggregation to KBA district code.
- Formula: SUM(bev_cars at KBA date) / SUM(charging_point_slots at BNetzA date).
- Units: Registered BEVs per published point slot.
- Source tables: core.kba_district_ev_stock, core.charging_point, core.charging_equipment, and the crosswalk CSV.
- Grain: KBA district code; BNetzA 2026-09-30 and one explicit KBA stock date from 2026-01-01, 2026-04-01, or 2026-07-01.
- Filters and exclusions: Aggregate charging metrics by KBA code before the vehicle join; retain provisional mappings and expose unmapped rows.
- Interpretation: A descriptive pressure or coverage indicator, not a utilization ratio.
- Known limitations: Dates are not contemporaneous; January and April ratios must not be described as contemporaneous infrastructure coverage; the BNetzA register is not exhaustive; and the crosswalk is provisional. Trier must not duplicate stock, and infrastructure rows must not be summed across KBA dates.
- Status: PROVISIONAL.

### 18. Fast charging share versus BEV stock growth

- Business question: How do regional fast-power mix and registered BEV stock growth appear together?
- Definition: Compare the point-level fast share with BEV percentage stock growth for the same regional grouping.
- Formula: Plot or tabulate fast_points / point_slots against (BEV_t2 - BEV_t1) / BEV_t1.
- Units: Two percentages, not one causal KPI.
- Source tables: BNetzA point data, KBA district data, and crosswalk.
- Grain: State or KBA district; infrastructure snapshot 2026-09-30; vehicle snapshots 2026-01-01 and 2026-07-01.
- Filters and exclusions: Use maximum declared power per point; do not compare unaggregated Trier source rows with KBA stock.
- Interpretation: An exploratory descriptive comparison.
- Known limitations: Different dates, incomplete published infrastructure, provisional geography, and confounding factors prohibit causal interpretation.
- Status: PROVISIONAL.

### 19. High-power charging share versus BEV stock growth

- Business question: How do the >=150 kW point mix and registered BEV stock growth appear together?
- Definition: Compare high-power share with same-grain BEV stock growth.
- Formula: high_power_points / point_slots versus BEV growth percentage.
- Units: Two percentages.
- Source tables: BNetzA point data, KBA district data, and crosswalk.
- Grain: State or KBA district with explicit dates.
- Filters and exclusions: Maximum-per-point power parser; aggregate before joining; preserve provisional flags.
- Interpretation: An exploratory descriptive comparison.
- Known limitations: No utilization, demand, or causal mechanism is observed.
- Status: PROVISIONAL.

### 20. Regional and state differences or rankings

- Business question: Which states or KBA registration regions have higher or lower observed counts, shares, or growth?
- Definition: Rank a specified KPI only after fixing its grain, denominator, date, and quality flags.
- Formula: Standard sort or rank over a validated KPI; no composite score is implied.
- Units: Depends on the ranked KPI.
- Source tables: Relevant BNetzA and KBA core tables, plus crosswalk for district comparisons.
- Grain: State or KBA district code.
- Filters and exclusions: Do not rank mixed dates or alternate KBA grains; do not hide provisional mappings or unknown power values.
- Interpretation: A descriptive prioritization aid.
- Known limitations: Rankings can reflect population, reporting coverage, administrative boundaries, and source completeness rather than infrastructure quality or need.
- Status: PROVISIONAL for combined regional rankings; VALIDATED for single-source descriptive counts.

## Metrics not supported by current data

The current sources and schema do not support charging utilization, sessions, actual energy delivery, queue times, reliability, real-time availability, or charger-caused vehicle adoption. These remain outside the KPI catalog until suitable sources and definitions are approved.
