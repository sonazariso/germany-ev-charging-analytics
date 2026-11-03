# KPI catalog

## Status vocabulary

Batch 18 establishes the project publication vocabulary. The historical batch
sections below retain earlier labels where they are part of the audit trail;
the [Batch 18 KPI readiness register](../reports/batch18_kpi_readiness_register.csv)
is authoritative for current publication status.

- `HEADLINE_READY`: the formula, numerator, denominator, grain, scope and reconciliation are validated for a primary descriptive presentation. Standard source-date metadata remains mandatory.
- `HEADLINE_READY_WITH_DATES`: suitable for primary presentation only when the relevant snapshot dates or geographic vintage are visible beside the value.
- `CONTEXT_ONLY`: useful supporting context whose coverage, geography or interpretation needs a prominent caveat; not a headline conclusion.
- `EXPLORATORY`: descriptive comparison, ranking, sensitivity or source-field analysis; not an approved causal, performance or adequacy KPI.
- `NOT_SUPPORTED`: the current sources do not supply a defensible formula or validated integration for the requested interpretation.

For Batch 18, earlier `VALIDATED` labels map to one of the two headline
statuses when publication-ready, earlier `PROVISIONAL` labels map to
`CONTEXT_ONLY`, `EXPLORATORY` or `NOT_SUPPORTED` according to the documented
risk, and earlier `DEFINED BUT NOT VALIDATED`/`PROPOSED` labels remain
`EXPLORATORY` or `NOT_SUPPORTED` until their evidence exists.

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

## Batch 06.1 coverage audit

This audit reviewed the existing numbered definitions and the requested coverage domains against the [data dictionary](data-dictionary.md), [analysis findings](analysis-findings.md), [geographic methodology](geographic-methodology.md), [data-quality record](data-quality.md), [decision log](decisions.md), and the Batch 03/05/06/08 validation reports. The table distinguishes documented and validated measures from candidate analyses. A row marked PROPOSED — REQUIRES APPROVAL records source capability and a possible definition; it does not approve a dashboard KPI or a database change.

| KPI or domain | English catalog status | Evidence | Missing definition or control | Recommended action |
|---|---|---|---|---|
| Registered equipment and charging-point slot counts | VALIDATED | Current baseline; `core.charging_equipment`, `core.charging_point`; Batch 06 report | None; equipment and point grains are separate | Retain the existing formulas and reconciliation |
| Normal, fast, >=150 kW, and >=350 kW points and shares | VALIDATED | Current baseline; Batch 05/06 regional validation | None; maximum declared power per point and point-slot denominator are documented | Retain the parser and recheck it for every future snapshot |
| Equipment nominal power and published status | VALIDATED | `core.charging_equipment`; Phase 03 and Batch 06 reports | None; nominal power is aggregated before any point join | Retain separate equipment-grain aggregation |
| State infrastructure distribution | VALIDATED | `analytics.charging_by_state`; 16-state baseline in Batch 06 | Standalone state-distribution definition was implicit rather than named | Add the explicit definition below; do not population-normalize without approval |
| KBA district infrastructure distribution | VALIDATED for observed local arithmetic; PROVISIONAL for official boundary meaning | `analytics.charging_by_kba_district_2026_09_30`; 400 rows in Batch 06/08 | Batch 08 completed row-level evidence review, but no universal KBA-to-AGS/ARS rule was found and all 24 operational mappings remain provisional | Use the deployed view with mapping flags; retain the KBA-registration-region and historical-vintage caveats |
| BEV stock, absolute change, and percentage growth | VALIDATED | `core.kba_district_ev_stock`; existing definitions 12, 14, and 15 | None for the approved 400-district grain | Retain same-grain/date controls and the stock-not-sales warning |
| PHEV stock | VALIDATED | `core.kba_district_ev_stock`; Batch 06 July total | None for the current stock measure | Retain the existing definition |
| PHEV absolute change and percentage growth | DEFINED BUT NOT VALIDATED | Same KBA fields and snapshot dates as the BEV measures | No independent project validation result or explicit approved catalog entry | Obtain owner approval and run a like-for-like validation before publishing |
| BEV share of passenger cars | VALIDATED | FZ 27.15 `bev_cars / passenger_cars`; existing definition 16 | None where the FZ 27.15 denominator is used | Keep the district/state/national-grain warning |
| PHEV share of passenger cars | VALIDATED at current state/FZ 27.15 grains | FZ 27.2 `darunter Plug-in` or FZ 27.15 `phev_cars` divided by same-grain passenger cars | Batch 15/16 independently reconcile state and 400-region passenger-car denominators; national `Deutschland` remains a separate scope | Keep the source grain, date and nested PHEV definition visible |
| BEVs per registered charging point and related ratios | PROVISIONAL | Deployed combined view; existing definition 17 | Formula is complete; dates, source coverage, and provisional geography limit interpretation | Keep as a cross-snapshot descriptive ratio, never a utilization KPI |
| Fast/HPC share versus BEV growth | EXPLORATORY (PROVISIONAL) | Existing definitions 18 and 19; Batch 05/06 dates and limitations | These are paired measures, not one causal KPI | Keep exploratory and do not infer demand, impact, or causality |
| Administrative city/county comparisons | PROPOSED — REQUIRES APPROVAL | BNetzA admin type and crosswalk fields; 401 source geographies | Display geography, aggregation rule, and treatment of city-to-county and Trier cases are not approved | Decide the comparison grain and validate it separately |
| Operator breakdowns | PROPOSED — REQUIRES APPROVAL | `core.charging_equipment.operator_name`; data dictionary | Operator-name normalization, primary measure, and denominator are not approved | Approve raw-name versus normalized-operator treatment before use |
| Commissioning history | VALIDATED as a descriptive distribution | `core.charging_equipment.commissioning_date`; existing definition 11 | None for a snapshot cohort profile; it is not an installation flow | Retain the cohort/profile limitation |
| Payment methods, opening hours, and connector types | PROPOSED — REQUIRES APPROVAL | `payment_methods`, `opening_*`, and `connector_types` are preserved in core | Tokenization, multi-label denominators, and display treatment are not approved; opening text is not real-time availability | Approve descriptive field distributions before validation |
| KBA ownership, postcode, and municipality analyses | PROPOSED — REQUIRES APPROVAL | `core.kba_postcode_ev_stock` and `core.kba_municipality_ev_stock`; 24,586 and 32,229 rows | Ownership denominator, possible total-row handling, and separation from district grain need approval | Define one-grain analyses and validate alternative-grain reconciliation |
| Crosswalk verification and Trier treatment | VALIDATED for coverage and join arithmetic; PROVISIONAL for official geography | Batch 03/05/06/08 reports; 401 rows, 400 codes, 24 provisional mappings | Batch 08 found 22 direct row-level key matches and two entity-level combined Trier mappings, but no universal KBA-to-AGS/ARS rule | Keep all flags visible and aggregate to KBA code before the stock join |
| BBSR/KBA or vehicle-stock spatial enrichment | PROPOSED — REQUIRES APPROVAL | Batch 09 feasibility plus Batch 10 reference; Batch 13/13.1 source-grain charging-only layers are separate approved exceptions | Dated KBA bridge, boundary vintage, mixed-region treatment, licensing, and intended KPI require approval | Keep the official baseline and owner scenario separate; do not assign types to KBA or calculate vehicle-stock category KPIs |
| Data-quality and coverage metrics | VALIDATED | `docs/data-quality.md`, Phase 03, Batch 03/05/06 reports | The metrics were documented as checks but not grouped in the catalog | Use the explicit quality measures below; keep exceptions visible |
| Utilization, sessions, energy, queue time, reliability, real-time availability, sales, or causal adoption claims | UNSUPPORTED BY CURRENT SOURCES | Project charter, data dictionary, and Batch 06 limitations | No source fields measure these concepts | Keep outside the KPI catalog until a suitable source and definition are approved |

The audit found no reason to change the formulas or current validation status of the existing 20 numbered KPI definitions. The additions below make previously implicit validated coverage explicit and record candidate domains without promoting them to approved results.

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
- Status: EXPLORATORY (PROVISIONAL).

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
- Status: EXPLORATORY (PROVISIONAL).

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
- Status: EXPLORATORY (PROVISIONAL) for combined regional rankings; VALIDATED for single-source descriptive counts.

### 21. State infrastructure distribution

- Business question: How are registered equipment records and charging-point slots distributed across the 16 German states?
- Definition: Report equipment rows, declared point counts, and populated point slots by `state_name`, keeping each measure at its own grain.
- Formula: `COUNT(*)` equipment rows; `SUM(declared_point_count)` declared points; source-aware `COUNT(*)` point rows.
- Units: Equipment records and point slots.
- Source tables: `analytics.charging_by_state`, `core.charging_equipment`, and `core.charging_point`.
- Grain: State and BNetzA reference date `2026-09-30`.
- Filters and exclusions: Preserve all equipment statuses; use `(source_id, excel_row)` / `(source_id, equipment_excel_row)` for the equipment-to-point relationship; do not divide by population without an approved denominator.
- Interpretation: A descriptive state distribution of the published register. The current view contains all 16 states.
- Known limitations: The BNetzA register is not exhaustive, and absolute counts reflect state size and source coverage.
- Status: VALIDATED for the current snapshot.

### 22. KBA district infrastructure distribution

- Business question: How are the registered charging measures distributed across KBA district codes?
- Definition: Aggregate equipment and point measures by KBA code after mapping each BNetzA state/district combination, then expose the mapping-quality fields.
- Formula: Sum equipment measures and count point rows by `kba_district_code` after source-geography aggregation; calculate shares with the point-slot denominator within the same KBA code.
- Units: Equipment records, point slots, declared-power bands, nominal MW, and percentages.
- Source tables: `analytics.charging_by_kba_district_2026_09_30`, `reference.bnetza_kba_district_crosswalk_2026`, `core.charging_equipment`, and `core.charging_point`.
- Grain: KBA district code and BNetzA reference date `2026-09-30`; the combined view adds one explicit KBA `reference_date`.
- Filters and exclusions: Aggregate before the vehicle join; keep the 24 provisional mappings and `points_without_valid_power`; never sum infrastructure values repeated beside multiple KBA dates.
- Interpretation: Batch 06 validated 400 KBA district rows and retained the national totals.
- Known limitations: The local arithmetic is validated, and Batch 08 completed the evidence review, but 22 aliases remain operationally provisional and the two Trier source mappings remain combined-region evidence. KBA stock dates are not contemporaneous with the infrastructure date, and historical boundary compatibility is not yet measured.
- Status: VALIDATED for observed row and aggregate arithmetic; PROVISIONAL for official geographic interpretation.

## Data-quality and coverage measures

These are validation measures rather than new business KPIs. They should be shown as quality metadata beside analytical outputs, not interpreted as utilization or performance measures.

| Measure | Formula | Current validated result | Grain and source | Limitation |
|---|---|---:|---|---|
| Equipment-to-point count mismatch | Count equipment rows where `declared_point_count` differs from matched populated point rows | 0 | Equipment row; `core.charging_equipment` + `core.charging_point` | A zero mismatch confirms current retention, not source completeness |
| Orphan charging-point rows | Point rows without a matching `(source_id, equipment_excel_row)` equipment row | 0 | Point row; source-aware join | A future source change requires rerunning the key check |
| Duplicate equipment and point keys | Duplicate `(source_id, excel_row)` and `(source_id, equipment_excel_row, point_number)` counts | 0 / 0 | Current BNetzA snapshot | Uniqueness is local to the current source snapshot |
| Declared-power parse coverage | `points_without_valid_power / populated_point_slots` | 0 / 211,253 | Point row and KBA district; deployed geographic view | The parser remains a derived read-only expression over raw text |
| Crosswalk coverage and provisional mapping count | Mapped source geographies / source geographies; count of provisional flags | 401 / 401; 24 provisional | BNetzA source geography and crosswalk | Coverage does not prove official boundary equivalence |
| KBA code/date key uniqueness | Duplicate `(kba_district_code, kba_reference_date)` keys | 0; 1,200 rows | Combined KBA view | Infrastructure values repeat across dates and must not be summed |
| Coordinate exception | Equipment rows outside the broad Germany check | 1 | Equipment row; source coordinates | The source coordinate is retained and is not corrected by this documentation batch |

Evidence for these results is consolidated in [docs/data-quality.md](data-quality.md), [reports/batch03_crosswalk_validation.md](../reports/batch03_crosswalk_validation.md), [reports/batch05_preintegration_review.md](../reports/batch05_preintegration_review.md), and [reports/batch06_geographic_deployment.md](../reports/batch06_geographic_deployment.md).

## Candidate source-supported analyses requiring approval

The following definitions document gaps identified by the audit. They are deliberately not added to the current baseline and do not authorize database changes or dashboard publication.

### PHEV absolute stock change and PHEV percentage stock growth

- Definition: Compare `phev_cars` at two KBA snapshots for the same geography and table grain.
- Formulas: `PHEV_t2 - PHEV_t1`; `100 * (PHEV_t2 - PHEV_t1) / PHEV_t1`.
- Units: Registered vehicles and percent.
- Source and grain: `core.kba_district_ev_stock`, same district/state/national geography plus two explicit `reference_date` values.
- Required controls: Do not mix the 400-district total with the KBA `Deutschland` row; do not interpret stock change as sales.
- Status: DEFINED BUT NOT VALIDATED. The formulas mirror the validated BEV change measures, but no independent result has been approved for this catalog.

### PHEV share of passenger cars

- Definition: PHEV stock divided by `passenger_cars` from the same FZ 27.15 row and date, or by the same-grain FZ 27.2 state passenger-car total.
- Formula: `100 * SUM(phev_cars) / SUM(passenger_cars)` or `100 * darunter Plug-in / total passenger cars`.
- Units: Percent.
- Source and grain: `core.kba_district_ev_stock` or `core.kba_state_fuel_stock`; 400-region or 16-state grain plus `reference_date`.
- Required controls: Use the confirmed same-grain denominator and keep the district/state-versus-Deutschland reconciliation visible.
- Status: VALIDATED for the current state and 400-region source grains after Batch 15/16 reconciliation. National `Deutschland` and `Sonstige` remain separate reporting scopes.

### Administrative city/county comparison

- Definition: Compare a specified registered infrastructure measure by the source `bnetza_admin_type` or an explicitly approved KBA administrative type.
- Formula: For each approved type, `COUNT(*)` equipment rows, `COUNT(*)` point slots, or another already validated measure; no composite score.
- Units: Depends on the selected measure.
- Source and grain: BNetzA equipment/point tables plus `reference.bnetza_kba_district_crosswalk_2026`; source geography or KBA code and BNetzA date.
- Required controls: Decide whether the comparison is at BNetzA source geography or KBA code, preserve city/county collisions, and handle Trier only after aggregation to code `07211`.
- Status: PROPOSED — REQUIRES APPROVAL. The local crosswalk has 107 source rows classified as city and 294 as county, but this is not an official boundary review.

### Operator breakdown

- Definition: Group registered equipment by the raw `operator_name`; optionally report declared point counts as a separate equipment-level measure.
- Formula: `COUNT(*)` equipment rows and `SUM(declared_point_count)` by raw operator value.
- Units: Equipment records and declared point slots.
- Source and grain: `core.charging_equipment`; operator and BNetzA reference date.
- Required controls: Decide whether legal-name normalization is allowed; do not treat raw spelling variants as one operator without an approved crosswalk; never infer market share or ownership.
- Status: PROPOSED — REQUIRES APPROVAL. The current field has 11,790 distinct non-null values, but no operator normalization or validation report exists.

### Payment-method, opening-hours, and connector-type distributions

- Definition: Descriptive field distributions from the source text. Payment methods and connector types may be multi-valued; opening fields describe the published schedule text.
- Formula: For a token-presence view, `COUNT(*)` equipment or point rows containing each token divided by the relevant equipment or point-row denominator. Multi-label shares may overlap. A raw-string distribution uses `COUNT(*) GROUP BY` the unmodified source text.
- Units: Equipment-row share, point-row share, or raw value counts.
- Source and grain: `core.charging_equipment.payment_methods`, `opening_hours`, `opening_weekdays`, `opening_times`; `core.charging_point.connector_types`; BNetzA snapshot.
- Required controls: Preserve raw text, define tokenization and placeholder handling such as `Keine Angabe`, and do not treat opening hours as real-time availability or connector text as a connector count.
- Status: PROPOSED — REQUIRES APPROVAL. The fields are present, but the token-level denominator and display treatment have not been approved or independently validated.

### KBA ownership, postcode, and municipality analyses

- Definition: Report commercial/private BEV and PHEV stock at KBA postcode or municipality grain; ownership shares may be calculated only after a denominator is approved.
- Formula: Counts are `SUM(commercial_bev)`, `SUM(private_bev)`, `SUM(commercial_phev)`, and `SUM(private_phev)` by geography and date. A candidate ownership share is `commercial_bev / (commercial_bev + private_bev)` or the analogous PHEV formula.
- Units: Registered vehicles and percentage shares.
- Source and grain: `core.kba_postcode_ev_stock` at `postal_code` and `reference_date`; `core.kba_municipality_ev_stock` at `municipality_name`/`district_code` and `reference_date`.
- Required controls: Treat postcode, municipality, district, state, and national tables as alternative grains; inspect `possible_total_row`; do not add commercial and private values to unrelated totals or stack postcode and municipality rows.
- Status: PROPOSED — REQUIRES APPROVAL. The source tables are available, but no final ownership denominator or alternative-grain validation has been approved.

## Batch 13 BBSR charging-only KPIs

Batch 13 adds a separate, validated descriptive path at the original BNetzA
state/district grain. It is not a BBSR-to-KBA integration and it does not use
KBA vehicle stock.

### 23. Charging infrastructure by BBSR district

- Definition: One row per BNetzA state/district enriched with the BBSR 2025 administrative/Kreisregion reference where the Path A identity is verified.
- Measures: Equipment count, charging-point count, normal/fast point counts, points >=150 kW, points >=350 kW, unclassifiable power points, nominal equipment power, fast-point share, and high-power share.
- Formula: Equipment metrics are aggregated from equipment rows; point metrics are aggregated from point rows after maximum-per-point parsing of semicolon-separated connector-power tokens. Shares use point counts in the same source district.
- Grain and dates: BNetzA state/district; infrastructure `2026-09-30`; BBSR geographic stand `2025-12-31`.
- Coverage: 401 rows; 399 `VERIFIED_COMPATIBLE`, one conditional Main-Kinzig row, and one unresolved Hanau row. All 401 remain in the denominator.
- Controls: Use `(source_id, excel_row)` and `(source_id, equipment_excel_row)` joins; preserve all equipment statuses; do not join KBA stock or use the Crosswalk as BBSR proof.
- Status: VALIDATED for source-grain arithmetic and coverage; geographic interpretation is conditional on the visible BBSR vintage/status.

### 24. Charging infrastructure by BBSR settlement type

- Definition: Aggregate the district view into BBSR codes 1–4 plus `UNCLASSIFIED`.
- Measures: Districts, equipment, points, power bands, within-category fast/high-power shares, nominal power in MW, and each category's share of all registered charging points.
- Denominators: Within-category shares use that category's charging points. National point share uses all 211,253 points, explicitly including `UNCLASSIFIED`.
- Coverage: Four valid categories cover 399 verified source districts; `UNCLASSIFIED` contains Hanau and Main-Kinzig (585 equipment, 991 points).
- Controls: Do not include BEV/PHEV stock, calculate BEV-per-point, or infer a category for a KBA registration region. Keep the BNetzA and BBSR dates visible.
- Status: VALIDATED descriptive infrastructure KPI; not a vehicle or utilization KPI.

## Batch 13.1 owner-approved scenario KPIs

Batch 13.1 adds a separate scenario path; it does not revise the official
Batch 13 five-row summary. The official baseline remains the source of record
for the BBSR 2025 classification status, with Hanau and Main-Kinzig in
`UNCLASSIFIED`. The scenario view is explicitly labelled
`OWNER_APPROVED_2026_ANALYTICAL_SCENARIO`.

### 25. Charging infrastructure by owner-approved BBSR-like category

- Definition: Aggregate the 401 original BNetzA source-district rows after applying exactly two owner overrides: Hanau `06415` → category 1 and Main-Kinzig-Kreis `06435` → category 2.
- Scenario reference: `data/reference/bnetza_bbsr_owner_override_2026.csv`; version `batch13.1-2026-11-02-owner-approved-hanau-main-kinzig`.
- Grain and dates: BNetzA source state/district; infrastructure `2026-09-30`; Crosswalk code identifier snapshot `2026-07-01`; official BBSR source stand `2025-12-31`; scenario boundary vintage `2026`.
- Measures: District count, equipment count, charging-point count, normal points, fast points, points >=150 kW, points >=350 kW, fast charging share, high-power share, declared equipment nominal power, and national charging-point share.
- Denominators: Fast/high-power shares use category charging points. National point share uses all 211,253 scenario charging points. The scenario has four category rows and zero `UNCLASSIFIED` districts.
- Provenance: Hanau uses `OWNER_APPROVED_SCENARIO`; Main-Kinzig uses `HISTORICAL_BBSR_CARRY_FORWARD`. Both rows expose `official_bbsr_verification = false`; neither is `VERIFIED_COMPATIBLE`.
- Controls: Reuse the validated source-aware equipment/point joins and maximum-per-point `connector_power_raw` parser. Do not join KBA stock, calculate BEV/PHEV ratios, allocate Trier stock, or describe Hanau category 1 as an official BBSR 2026 classification.
- Status: `VALIDATED` as a reproducible owner-approved analytical scenario; `PROVISIONAL` for geographic interpretation because the owner overrides are not official BBSR verification.

The deployed relations are `analytics.charging_by_bbsr_district_2026_scenario`
and `analytics.charging_by_bbsr_type_2026_scenario`. The detailed four-category
result, comparison with the official baseline, evidence URLs, and limitations
are in
[`reports/batch13_1_bbsr_scenario_classification.md`](../reports/batch13_1_bbsr_scenario_classification.md).

## Batch 13.2 historical BBSR boundary harmonization KPIs

Batch 13.2 adds a third, versioned charging-only path. It preserves the
official Batch 13 baseline and the Batch 13.1 owner scenario, while mapping
the BNetzA `2026-09-30` source components to the BBSR `2025-12-31` historical
target geography. It is a historical target-unit harmonization, not an
official 2026 Hanau BBSR classification.

### 26. Charging infrastructure by historical BBSR district

- Definition: Aggregate current BNetzA source rows to one BBSR 2025 `KRS2025` target unit. Hanau and the remaining Main-Kinzig source row are combined into historical BBSR `06435000`; Kassel city is corrected to `06611000 Kassel, documenta-Stadt`, type 1, while Landkreis Kassel remains `06633000`, type 2.
- Grain and dates: target BBSR administrative district; source infrastructure `2026-09-30`; historical BBSR stand `2025-12-31`. The view exposes both dates, source-component names/count, mapping method, boundary status, and validation notes.
- Coverage: 401 source components aggregate to 400 historical target rows with type counts 68 / 131 / 98 / 103. Type 2 has 131 historical targets and 132 current source components because Hanau and remaining Main-Kinzig are one historical target.
- Hanau/Main-Kinzig target: 585 equipment, 991 points, 613 normal, 378 fast, 327 points >=150 kW, 77 points >=350 kW, and 63.4820 MW.
- Controls: the raw BBSR `SLK2025` field independently supplies city/county form; strict and semantic bidirectional anti-joins are recorded; the KBA Crosswalk is not used as BBSR assignment proof; original BNetzA source data remains unchanged.
- Status: `VALIDATED` for reproducible charging arithmetic and historical target reconstruction; `PROVISIONAL` for any interpretation beyond the documented boundary vintage. The layer does not assign a 2026 BBSR type to Hanau.

### 27. Charging infrastructure by historical BBSR settlement type

- Definition: Aggregate the historical BBSR target-unit view into compact BBSR types 1–4. There is no `UNCLASSIFIED` target row after the documented Hanau/Main-Kinzig reconstruction.
- National reconciliation: 117,662 equipment, 211,253 points, 156,155 normal, 55,098 fast, 40,950 points >=150 kW, 6,950 points >=350 kW, and 9,215.4173 MW.
- Comparison: the official Batch 13 five-row baseline and the Batch 13.1 four-row owner scenario remain deployed and unchanged so downstream users can compare official, scenario, and historical-harmonized outputs.
- Controls: retain source component count and names, use the maximum valid declared-power token per point, keep all source dates visible, and do not join KBA BEV/PHEV stock or allocate Trier stock.
- Status: `VALIDATED` for the charging-only historical comparison; not a vehicle-stock KPI and not evidence of an official post-2025 BBSR publication.

The deployed relations are `reference.bnetza_bbsr_historical_harmonization_2025`,
`analytics.charging_by_bbsr_district_2025_harmonized`, and
`analytics.charging_by_bbsr_type_2025_harmonized`. The detailed anti-join
audit, official boundary evidence, layer comparison, and backup provenance are
in
[`reports/batch13_2_hanau_geographic_harmonization.md`](../reports/batch13_2_hanau_geographic_harmonization.md).

## Batch 14 statistical KPI evaluation

Batch 14 evaluates future Tableau candidates from the harmonized layer without
deploying new database views. All candidates retain the BNetzA infrastructure
date `2026-09-30`, the BBSR historical stand `2025-12-31`, and the 400-unit
historical target grain unless stated otherwise.

| Candidate | Status | Numerator / denominator | Source | Unit and grain | Limitation |
|---|---|---|---|---|---|
| BBSR category point count and national share | `VALIDATED` | Category charging points / all 211,253 points | Harmonized district/type views over core point rows | Points and percent; four BBSR types | Absolute counts are not accessibility or need |
| BBSR category equipment count and national share | `VALIDATED` | Category equipment rows / all 117,662 rows | Harmonized district/type views over core equipment rows | Equipment rows and percent; four BBSR types | Equipment is not point count |
| Fast point count and within-category fast share | `VALIDATED` | Points with maximum declared power >22 kW / category points | Harmonized views with maximum `connector_power_raw` parser | Points and percent; category | Declared power is not utilization |
| >=150 and >=350 kW counts/shares | `VALIDATED` | Nested threshold counts / category points | Harmonized views with maximum `connector_power_raw` parser | Points and percent; category | Thresholds overlap and do not establish access |
| Unit distribution percentiles | `EXPLORATORY` | P10, median, P90 of counts, shares, nominal power, and points/equipment | Harmonized district view | Historical BBSR unit; category | Skew and small denominators require context |
| Weighted versus unweighted shares | `EXPLORATORY` | Point-weighted share versus mean unit share | Harmonized district view | Category or all 400 units | Weighting differences are not performance evidence |
| Top-1/top-5/top-10 concentration share | `EXPLORATORY` | Points in top k units / national points | Harmonized district view | Historical BBSR unit | Ranking is not quality or need |
| Declared equipment nominal power | `VALIDATED` | Sum equipment nominal kW / 1,000 | Harmonized district view over core equipment rows | MW; category or unit | Nominal power is not delivered energy or simultaneous capacity |
| BBSR-based BEV-to-charger ratio | `UNSUPPORTED` | Would require a valid dated BBSR/KBA bridge | No approved BBSR/KBA source bridge | No approved current grain | KBA stock is intentionally excluded from Batch 14 |

The recommended initial Tableau set is category point count/share, fast
count/share, nested high-power count/share, and a distribution view with
P10/median/P90 context. The descriptive metrics must not be labelled as
coverage, demand, utilization, accessibility, or causality measures.

## Optional future BBSR/KBA enrichment

BBSR settlement or spatial typology remains a separate, versioned reference for
the current charging-only KPIs. Future KBA-level enrichment or any BBSR-based
vehicle ratio still requires approval of a dated KBA compatibility bridge,
boundary vintage, mixed-region treatment, licensing, and intended
interpretation. No current Batch 13 KPI assigns a BBSR type to a KBA code.

| Planned analytical candidate | Suitable future grain | Current status and control |
|---|---|---|
| Charging points by BBSR category | BBSR Kreis/Kreisregion, or homogeneous KBA regions after a validated bridge | PROPOSED — REQUIRES APPROVAL; do not force a single class onto mixed KBA `07211`. |
| Fast charging share by BBSR category | Same BBSR-compatible grain; numerator and denominator aggregated before the share | PROPOSED — REQUIRES APPROVAL; retain the declared-power and BNetzA-date caveats. |
| High-power (>=150 kW) charging share by BBSR category | Same BBSR-compatible grain | PROPOSED — REQUIRES APPROVAL; use the existing maximum-per-point classification only after geography is validated. |
| BEV stock by BBSR category | BBSR administrative/Kreisregion grain or compatible one-to-one KBA aggregation | PROPOSED — REQUIRES APPROVAL; no Hanau assignment from the 2025 BBSR vintage and no Trier stock allocation. |
| BEV per charging point by BBSR category | Same validated category grain with explicit BNetzA and KBA dates | PROPOSED — REQUIRES APPROVAL; descriptive only, not utilization. |
| BEV stock growth by BBSR category | Fixed compatible BBSR vintage across both KBA dates or an approved historical conversion | PROPOSED — REQUIRES APPROVAL; stock change is not sales or causality. |

The Batch 09 feasibility result is **CONDITIONAL GO** for a separate versioned BBSR
reference and controlled compatibility layer, but **NO-GO** for direct assignment
of one BBSR class to all current KBA codes. The owner-approved Trier display label
is **Trier / Trier-Saarburg (gemeinsamer Zulassungsbezirk)**, and shared stock must
not be allocated without a separately approved method. See
[reports/batch09_bbsr_feasibility.md](../reports/batch09_bbsr_feasibility.md).

## Metrics not supported by current data

| Concept | Status | Why it is unsupported | What may be reported instead |
|---|---|---|---|
| Charging utilization or occupancy | UNSUPPORTED BY CURRENT SOURCES | No sessions, dwell time, or utilization observations exist | Declared point counts and power mix only |
| Charging sessions or actual energy delivery | UNSUPPORTED BY CURRENT SOURCES | The sources contain no session or kWh fields | Declared equipment nominal power, clearly labelled as nominal |
| Queue time or customer waiting | UNSUPPORTED BY CURRENT SOURCES | No queue or arrival observations exist | No substitute KPI |
| Reliability, uptime, or real-time availability | UNSUPPORTED BY CURRENT SOURCES | Published status and opening schedule are snapshots/text, not event or availability histories | Equipment status and opening text only as descriptive source fields |
| Vehicle sales or charger-caused adoption | UNSUPPORTED BY CURRENT SOURCES | KBA values are stock snapshots and the project has no causal design | Descriptive stock change and explicitly exploratory comparisons |

These exclusions are analytical controls. Declared power is not delivered energy, the equipment `status` field is not uptime, opening hours are not real-time availability, and BEV/PHEV stock growth is not new vehicle sales.

## Batch 15 KBA stock KPIs

Batch 15 validates the following descriptive KBA measures without deploying
new DuckDB KPI objects:

| KPI | Status | Numerator / denominator | Grain and date | Interpretation control |
|---|---|---|---|---|
| National BEV stock | VALIDATED | `Deutschland / Elektro (BEV)` | National × 2026-01-01, 2026-04-01, 2026-07-01 | Registered stock, not sales |
| National PHEV stock | VALIDATED | `Deutschland / darunter Plug-in` | National × release date | PHEV is nested under `Hybrid insgesamt` for total-category logic |
| BEV/PHEV stock change and growth | VALIDATED | End stock − start stock; change / start stock | National, state or KBA region × snapshots | Snapshot stock change, not registration flow |
| BEV/PHEV passenger-car penetration | VALIDATED | Powertrain stock / same-grain passenger-car total | State or 400 KBA region × snapshot | Denominator and reporting scope must stay visible |
| Combined plug-in penetration | VALIDATED | `(BEV + PHEV) / passenger cars` | Same-grain snapshot | Valid here because BEV and PHEV are mutually exclusive |
| FZ 27.5 ownership composition | EXPLORATORY | Commercial/private BEV or PHEV / observed owner rows; published-total coverage shown separately | State, `Sonstige` or national × snapshot | Unknown/implausible holder-group residuals are not allocated |
| KBA-region percentage-growth ranking | EXPLORATORY | January–July BEV growth with January BEV ≥1,000 | 400 KBA codes | The threshold stabilizes the ranking; it is not an official standard |
| BBSR-based vehicle-stock ratio | UNSUPPORTED | No approved dated KBA-to-BBSR bridge | Not deployed | Do not infer or create in Batch 15 |

The complete formulas, columns, reconciliation fields and limitations are in
[`reports/batch15_kba_ev_stock_analysis.md`](../reports/batch15_kba_ev_stock_analysis.md).
The recommended Tableau set is limited to validated stock/penetration/change
measures plus clearly labelled exploratory distributions. No measure implies
charging demand, utilization, access, quality, or causality.

## Batch 16 state EV/charging alignment KPIs

Batch 16 adds a state-level candidate set without creating permanent DuckDB
KPI views. KBA values use `2026-07-01`; BNetzA values use `2026-09-30`.

| KPI | Formula | Numerator | Denominator | Unit | Source | Grain | Status | Interpretation / limitation | Tableau suitability |
|---|---|---|---|---|---|---|---|---|---|
| State BEV stock | `SUM(Elektro (BEV))` | Registered BEV passenger cars | None | Vehicles | KBA FZ 27.2 | 16 states | VALIDATED | Stock, not sales or demand | Recommended |
| State PHEV stock | `SUM(darunter Plug-in)` | Registered PHEV passenger cars | None | Vehicles | KBA FZ 27.2 | 16 states | VALIDATED | Nested under `Hybrid insgesamt`; never add to the total fuel rows | Recommended |
| Total registered passenger cars | Sum six mutually exclusive fuel rows | Benzin, Diesel, Gas, BEV, Hybrid insgesamt, Sonstige | None | Vehicles | KBA FZ 27.2 | 16 states | VALIDATED | Passenger-car denominator; PHEV is not added a second time | Recommended denominator |
| BEV penetration | `BEV / total passenger cars` | State BEV stock | Same-state passenger cars | % | KBA FZ 27.2 | 16 states | VALIDATED | Registered-stock share | Recommended |
| PHEV penetration | `PHEV / total passenger cars` | State PHEV stock | Same-state passenger cars | % | KBA FZ 27.2 | 16 states | VALIDATED | Registered-stock share | Recommended |
| Combined plug-in penetration | `(BEV + PHEV) / total passenger cars` | BEV + PHEV stock | Same-state passenger cars | % | KBA FZ 27.2 | 16 states | VALIDATED | Valid only for mutually exclusive BEV/PHEV categories | Recommended |
| Charging-point count | `COUNT(core.charging_point)` | Populated point slots | None | Points | BNetzA | 16 states | VALIDATED | Register stock; not connectors, availability or capacity | Recommended |
| Fast/HPC point counts and shares | Count by maximum declared point power; divide by all points | Points >22, >=150, >=350 kW | All point slots | Points / % | BNetzA `connector_power_raw` | 16 states | VALIDATED | Nested declared-power mix; not utilization or simultaneous delivery | Recommended with definitions |
| Nominal equipment power | `SUM(equipment_nominal_power_kw) / 1,000` | Equipment nominal kW | None | MW | BNetzA | 16 states | VALIDATED | Nominal power, not energy or grid capacity | Context |
| BEVs per registered point | `BEV / points` | July state BEV stock | September registered points | BEVs/point | KBA + BNetzA | 16 states | EXPLORATORY | Date-mismatched and register-coverage dependent; not adequacy/accessibility | Clearly labelled exploratory only |
| Points per 1,000 BEVs | `points * 1,000 / BEV` | September registered points | July state BEV stock | Points / 1,000 BEVs | KBA + BNetzA | 16 states | EXPLORATORY | Inverse date-mismatched ratio; not a service standard | Exploratory context |
| Fast/HPC points per 1,000 BEVs | `threshold points * 1,000 / BEV` | Fast or >=150/350 kW points | July state BEV stock | Points / 1,000 BEVs | KBA + BNetzA | 16 states | EXPLORATORY | Denominator, date and source-coverage limitations | Exploratory context |
| BEV share minus point share | `BEV share − point share` | State share of 16-state BEVs | State share of all registered points | Percentage points | KBA + BNetzA | 16 states | EXPLORATORY | Compositional gap; not shortage/surplus | Annotation, not standalone KPI |
| State Pearson/Spearman associations | Correlation across state rows | Selected state metric | Selected state metric | Coefficient | KBA + BNetzA | 16 states | EXPLORATORY | Small cross-section; scale and denominators; no causality | Analyst diagnostic |
| Adequacy/shortage/surplus | No defensible formula | — | — | Unsupported | Requires sessions/demand/availability/service standard | Not supported | UNSUPPORTED | Current sources cannot measure the concept | Do not deploy |

The recommended concise Tableau set is state BEV stock, passenger-car stock,
BEV penetration, registered points, fast/HPC counts and shares, and nominal MW
as context. Any cross-source ratio must show both reference dates and remain
exploratory. A ratio must not be used to label a state adequately or
inadequately supplied.

## Batch 17 temporal-validity decisions

Batch 17 keeps the Batch 16 formulas but distinguishes the observed published
September denominator from a retrospective equipment-level cohort. The primary
KBA stock date is `2026-07-01`; the BNetzA publication date is `2026-09-30`.
They are 91 days apart. The published comparison is labelled
**CROSS-SNAPSHOT DESCRIPTIVE COMPARISON**. The cohort is labelled
**RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE**.

| Candidate cross-source KPI | Formula | Published denominator | Survivor sensitivity | Batch 17 status | Tableau recommendation |
|---|---|---|---|---|---|
| BEVs per registered charging point | KBA BEV stock / BNetzA populated point rows | September 2026 BNetzA points | 11.181938 → 11.446796 BEVs/point; +2.37% | `CONTEXT_ONLY` | Secondary contextual KPI with both dates; not a headline or adequacy gauge |
| Registered points per 1,000 BEVs | 1,000 × points / KBA BEV stock | July 2026 KBA BEVs | Inverse date/cohort sensitivity | `CONTEXT_ONLY` | Context table paired with absolute counts |
| Fast points per 1,000 BEVs | 1,000 × points >22 kW / KBA BEV stock | July KBA BEVs and September fast points | State ratios and rankings change under survivor selection | `EXPLORATORY_SENSITIVITY` | Dot plot/table with declared-power and date warnings |
| >=150 / >=350 kW points per 1,000 BEVs | 1,000 × threshold points / KBA BEV stock | July KBA BEVs and September threshold points | Survivor counts are not observed July high-power stock | `EXPLORATORY_SENSITIVITY` | Threshold sensitivity table only |
| Combined plug-in vehicles per registered point | (BEV + PHEV stock) / point rows | July KBA stock and September points | Same date mismatch; PHEV stock is not demand | `CONTEXT_ONLY` | Optional context only, never adequacy |
| BEV-share minus point-share gap | BEV share − point share | 16-state source totals | Survivor point shares are reconstructed sensitivity | `EXPLORATORY_SENSITIVITY` | Annotated composition chart, not shortage/surplus |
| State correlations | Pearson/Spearman across 16 state rows | Cross-sectional | Stable association can reflect state size and denominators | `EXPLORATORY_SENSITIVITY` | Analyst diagnostic, not a headline |
| Infrastructure adequacy/shortage/surplus | No defensible current formula | No demand/availability/service standard | Cohort selection cannot supply missing evidence | `NOT_SUPPORTED` | Do not deploy |

The commissioning-date audit found 0 raw NULLs/blanks, 0 parsing failures, 0
future dates relative to the September source, and no point-level activation
date field. The full formula, numerator, denominator, grain, date treatment,
sensitivity, risk, label and visualization recommendation for each row is in
[`reports/batch17_kpi_publication_decisions.csv`](../reports/batch17_kpi_publication_decisions.csv).

The BEVs-per-point measure may therefore appear only as a dated secondary
context measure. It must not be framed as a contemporaneous adequacy or
accessibility KPI, regardless of ranking stability.

## Batch 18 final publication readiness

Batch 18 consolidates the definitions across the infrastructure, power,
geographic, BBSR, vehicle-stock, ownership, state-comparison and temporal
domains. The machine-readable register contains 59 deterministic rows and
stores, for each row, the English/German name, exact formula, numerator,
denominator, unit, datasets, fields/objects, geographic grain, dates, source
scope, limitations, interpretation controls, publication status and Tableau
treatment.

| Publication status | Count | Practical meaning |
|---|---:|---|
| `HEADLINE_READY` | 16 | Single-source infrastructure and same-grain KBA descriptive measures. |
| `HEADLINE_READY_WITH_DATES` | 11 | Dated stock changes, national history and historical BBSR charging measures. |
| `CONTEXT_ONLY` | 8 | Cross-source ratios, provisional geography, source-grain BBSR context and ownership. |
| `EXPLORATORY` | 17 | Distribution, concentration, rankings, correlations, source-field and temporal sensitivity analyses. |
| `NOT_SUPPORTED` | 7 | Historical stock change, BBSR vehicle ratios, adequacy, utilization and unvalidated denominators/integrations. |

The recommended headline families are registered equipment and point-slot
counts; normal/fast and declared-power threshold counts/shares; declared
nominal MW; 16-state infrastructure distribution; KBA BEV/PHEV/passenger-car
stock and same-grain penetration; KBA stock changes; the national stock
trajectory; and historical BBSR charging-only composition with both
`2026-09-30` BNetzA and `2025-12-31` BBSR dates. BEVs per registered point is
`CONTEXT_ONLY`; temporal survivor-cohort metrics are `EXPLORATORY`; adequacy,
shortage and surplus are `NOT_SUPPORTED`.

The full formulas and source objects are in
[`reports/batch18_kpi_readiness_register.csv`](../reports/batch18_kpi_readiness_register.csv).
The decision rationale, Tableau page recommendation and unresolved blockers
are in [`reports/batch18_readiness_decisions.md`](../reports/batch18_readiness_decisions.md).

## Batch 19 export publication map

Batch 19 materializes existing validated KPI families into separate CSV
contracts; it does not change the canonical readiness register or its counts.

| Export family | Source/date scope | Publication treatment |
|---|---|---|
| National/state BNetzA counts, power bands, shares and nominal MW | BNetzA `2026-09-30` | `HEADLINE_READY_WITH_DATES` |
| Historical BBSR district/type charging-only counts and shares | BBSR `2025-12-31` + BNetzA `2026-09-30` | `HEADLINE_READY_WITH_DATES`; historical geography caveat required |
| KBA state and registration-region stock, penetration and snapshot changes | KBA `2026-01-01`, `2026-04-01`, `2026-07-01` | `HEADLINE_READY_WITH_DATES` |
| National KBA quarterly stock history | 33 deduplicated national stock dates | `HEADLINE_READY_WITH_DATES` |
| State EV/charging comparison | KBA `2026-07-01` + BNetzA `2026-09-30` | Absolute source measures dated; BEVs/point `CONTEXT_ONLY`; power-normalized/share-gap fields `EXPLORATORY_SENSITIVITY` |
| Published-versus-survivor state sensitivity | KBA July denominator + September register and inclusive July cutoff | `EXPLORATORY_SENSITIVITY`; survivor is not actual July infrastructure |

All exported shares are numeric calculations from aggregated numerators and
denominators; Tableau must not sum them. Cross-source ratios remain descriptive
and cannot be presented as adequacy, shortage, surplus, demand, utilization or
accessibility measures. The full field contracts and permitted relationships
are in [`reports/batch19_tableau_export_contracts.md`](../reports/batch19_tableau_export_contracts.md).

## Batch 20 semantic-model mapping

Batch 20 does not change the canonical definitions or publication statuses. It
maps every one of the 59 Batch 18 IDs to a logical fact, dimension contract,
exact grain, formula, calculation location, filter behavior, source date, risk,
and implementation-readiness state:

[`reports/batch20_kpi_model_mapping.csv`](../reports/batch20_kpi_model_mapping.csv)

The mapping keeps `HEADLINE_READY`, `HEADLINE_READY_WITH_DATES`,
`CONTEXT_ONLY`, `EXPLORATORY`, and `NOT_SUPPORTED` unchanged. It also applies
the Batch 20 rule that ratios and shares use aggregated numerator and
denominator fields rather than averaged percentages. Unsupported KPIs remain
`NOT_IMPLEMENTABLE`; a source field's existence does not promote an
unsupported interpretation.
