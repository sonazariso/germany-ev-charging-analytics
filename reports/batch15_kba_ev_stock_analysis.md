# Batch 15 — KBA FZ 27 EV stock, growth, geography and ownership analysis

**Batch status: PASS**

This is a deterministic, read-only statistical analysis of the three locally preserved KBA FZ 27 releases. It does not change DuckDB objects, raw workbooks, existing Crosswalks, BBSR objects, or charging analytics.

## Scope and analytical rules

- KBA snapshots: `2026-01-01`, `2026-04-01`, and `2026-07-01`.
- National/state stock uses `core.kba_state_fuel_stock` and the published `Deutschland`, 16-state, and `Sonstige` rows.
- Registration-region analysis uses `core.kba_district_ev_stock` at KBA registration-region × reference-date grain: 400 codes per snapshot and 1,200 rows in total.
- Passenger-car denominators use mutually exclusive FZ 27.2 fuel rows. `darunter Plug-in` is nested under `Hybrid insgesamt` and is never added to the total a second time.
- The shared KBA registration region `07211 TRIER-SAARBURG` remains one row. No allocation to Trier city or Trier-Saarburg administrative units is performed.
- Percentage-growth rankings use an exploratory minimum January BEV baseline of **1,000 vehicles**. This is a stability filter, not an official standard; excluded rows remain in the diagnostic CSV.
- Stock changes are changes in registered stock between snapshots, not registrations, sales, gross inflows, charging demand, utilization, or causality.

## Read-only validation contract

| Object/check | Result |
|---|---|
| raw.kba_rows | BASE TABLE |
| core.kba_state_fuel_stock | BASE TABLE |
| core.kba_district_ev_stock | BASE TABLE |
| core.kba_postcode_ev_stock | BASE TABLE |
| core.kba_municipality_ev_stock | BASE TABLE |
| analytics.kba_national_quarterly_stock | VIEW |

The analysis opened DuckDB with `read_only=True` and issued no DDL/DML. The script is compatible with the existing local Python environment and installs no dependencies.

## Source worksheet inventory

The full 60-row inventory is in [`batch15_kba_worksheet_capabilities.csv`](batch15_kba_worksheet_capabilities.csv). It records the actual worksheet title, source row span, analytical grain, geographic level, vehicle/owner dimensions, subtotal behavior, and aggregation suitability for each release. The three workbooks each contain all 20 expected worksheets.

| Sheet | Published title | Raw rows | Grain | Aggregation status |
|---|---|---|---|---|
| FZ 27.15 | FZ 27.15 Bestand an Personenkraftwagen am 1. Juli 2026 nach Bundesländern und Zulassungsbezirken sowie nach ausgewählten Kraftstoffarten bzw. Energiequellen | 431 | KBA registration region × snapshot date | Suitable for 400-region snapshot aggregation; no BBSR equivalence is implied |
| FZ 27.16 | FZ 27.16 Bestand an Personenkraftwagen am 1. Juli 2026 nach Postleitzahlen sowie nach gewerblichen und privaten Halterinnen und Haltern und den Antriebsarten Elektro (BEV) und Plug-in-Hybrid | 8,209 | Postcode × holder group × BEV/PHEV × snapshot date | Descriptive at postcode grain with missing-cell audit; not a district crosswalk |
| FZ 27.17 | FZ 27.17 Bestand an Personenkraftwagen am 1. Juli 2026 nach Bundesländern, Zulassungsbezirken und Gemeinden sowie nach gewerblichen und privaten Halterinnen und Haltern und den Antriebsarten Elektro (BEV) und Plug-in-Hybrid | 10,756 | Municipality × KBA registration district × holder group × snapshot date | Use source key (district code plus municipality name) only; do not aggregate names globally |
| FZ 27.2 | FZ 27.2 Bestand an Kraftfahrzeugen am 1. Juli 2026 nach Bundesländern, Kraftstoffarten und Fahrzeugarten | 150 | Federal state × fuel type × vehicle type, with subtotals | Suitable for controlled aggregation using mutually exclusive fuel rows |
| FZ 27.5 | FZ 27.5 Bestand an Personenkraftwagen am 1. Juli 2026 nach Bundesländern, gewerblichen und privaten Halterinnen und Haltern und Kraftstoffarten | 62 | Federal state/residual/national × holder group × fuel type | Suitable when owner rows and published totals are kept separate |
| FZ 27.9 | FZ 27.9 Bestand an Personenkraftwagen nach Quartalen sowie nach ausgewählten Kraftstoffarten bzw. Energiequellen | 43 | National passenger-car stock × stock quarter × energy source | Suitable for national history after deterministic overlap deduplication |

FZ 27.15 is the appropriate regional stock source for the 400 KBA registration-region analysis. FZ 27.16 and FZ 27.17 are separate postcode/municipality breakdowns with different keys and should not be summed into FZ 27.15 or treated as unique administrative-unit inventories without validation.

## National stock reconciliation

| Date | National cars | 16 states | Sonstige | 400 regions | National BEV | 16-state BEV | Sonstige BEV | 400-region BEV | National PHEV | 400-region PHEV |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-01 | 49,486,487 | 49,436,020 | 50,467 | 49,436,020 | 2,034,260 | 2,031,870 | 2,390 | 2,031,870 | 1,122,958 | 1,121,516 |
| 2026-04-01 | 49,546,014 | 49,494,647 | 51,367 | 49,494,647 | 2,169,717 | 2,167,111 | 2,606 | 2,167,111 | 1,167,434 | 1,165,933 |
| 2026-07-01 | 49,696,710 | 49,644,855 | 51,855 | 49,644,855 | 2,365,047 | 2,362,218 | 2,829 | 2,362,218 | 1,226,863 | 1,225,241 |

The 16-state sums reconcile exactly to the 400-region table for passenger cars, BEVs and PHEVs. National totals reconcile as 16 states plus `Sonstige`. The remaining passenger cars and EVs are therefore reporting residuals, not unexplained missing vehicle records in this source comparison:

| Date | National − 400-region cars | National − 400-region BEV | National − 400-region PHEV |
|---|---|---|---|
| 2026-01-01 | 50,467 | 2,390 | 1,442 |
| 2026-04-01 | 51,367 | 2,606 | 1,501 |
| 2026-07-01 | 51,855 | 2,829 | 1,622 |

The BEV residuals are `Sonstige`: 2,390 in January, 2,606 in April, and 2,829 in July. The same reporting structure produces PHEV residuals of 1,442, 1,501 and 1,622. Passenger-car residuals are 50,467, 51,367 and 51,855.

## Analysis A — BEV and PHEV stock growth

| Date | National cars | BEV | BEV share | PHEV | PHEV share | Combined plug-in | Combined share | BEV change | BEV change % | PHEV change | PHEV change % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-01-01 | 49,486,487 | 2,034,260 | 4.11% | 1,122,958 | 2.27% | 3,157,218 | 6.38% | — | — | — | — |
| 2026-04-01 | 49,546,014 | 2,169,717 | 4.38% | 1,167,434 | 2.36% | 3,337,151 | 6.74% | 135,457 | 6.66% | 44,476 | 3.96% |
| 2026-07-01 | 49,696,710 | 2,365,047 | 4.76% | 1,226,863 | 2.47% | 3,591,910 | 7.23% | 195,330 | 9.00% | 59,429 | 5.09% |

### Period changes

| Period | BEV absolute | BEV % | PHEV absolute | PHEV % | BEV/PHEV relative-growth ratio |
|---|---|---|---|---|---|
| 2026-01-01 to 2026-04-01 | 135,457 | 6.66% | 44,476 | 3.96% | 1.68 |
| 2026-04-01 to 2026-07-01 | 195,330 | 9.00% | 59,429 | 5.09% | 1.77 |
| 2026-01-01 to 2026-07-01 | 330,787 | 16.26% | 103,905 | 9.25% | 1.76 |

National BEV stock grew faster than PHEV stock in all three periods. The combined plug-in share is calculated as BEV plus PHEV because those published categories are mutually exclusive passenger-car powertrain categories. `Hybrid insgesamt` is not added to that measure because it already contains PHEV.

## Analysis B — Federal-state comparison

The complete state/residual metric table is in [`batch15_kba_state_metrics.csv`](batch15_kba_state_metrics.csv). The following July 2026 rankings intentionally separate stock size, penetration, absolute change and percentage growth.

### Largest July BEV stocks

| Rank | State | BEV | Passenger cars | BEV penetration |
|---|---|---|---|---|
| 1 | Nordrhein-Westfalen | 527,377 | 10,694,681 | 4.93% |
| 2 | Bayern | 459,811 | 8,527,085 | 5.39% |
| 3 | Baden-Württemberg | 369,574 | 7,015,759 | 5.27% |
| 4 | Niedersachsen | 259,973 | 5,025,325 | 5.17% |
| 5 | Hessen | 208,073 | 3,937,917 | 5.28% |

### Highest July BEV penetration

| Rank | State | BEV | Passenger cars | BEV penetration |
|---|---|---|---|---|
| 1 | Hamburg | 49,560 | 829,662 | 5.97% |
| 2 | Bayern | 459,811 | 8,527,085 | 5.39% |
| 3 | Hessen | 208,073 | 3,937,917 | 5.28% |
| 4 | Baden-Württemberg | 369,574 | 7,015,759 | 5.27% |
| 5 | Niedersachsen | 259,973 | 5,025,325 | 5.17% |

### Largest January–July absolute BEV increases

| Rank | State | BEV increase | BEV growth | Contribution to national growth |
|---|---|---|---|---|
| 1 | Nordrhein-Westfalen | 72,595 | 15.96% | 21.95% |
| 2 | Bayern | 64,540 | 16.33% | 19.51% |
| 3 | Baden-Württemberg | 47,514 | 14.75% | 14.36% |
| 4 | Niedersachsen | 38,150 | 17.20% | 11.53% |
| 5 | Hessen | 28,860 | 16.10% | 8.72% |

### Highest January–July BEV percentage growth

| Rank | State | BEV increase | BEV growth | July BEV |
|---|---|---|---|---|
| 1 | Mecklenburg-Vorpommern | 3,849 | 20.98% | 22,196 |
| 2 | Sachsen-Anhalt | 4,869 | 20.08% | 29,116 |
| 3 | Saarland | 3,982 | 18.91% | 25,038 |
| 4 | Thüringen | 5,089 | 18.89% | 32,026 |
| 5 | Brandenburg | 7,450 | 17.89% | 49,103 |

`Sonstige` is reported separately in the CSV and is not blended into any Bundesland. State-level totals are sourced from FZ 27.2 and reconcile to the 400-region table for the 16 named states. The ranking differences are substantive: large states tend to lead absolute stock and change, while smaller states can lead penetration or percentage growth.

## Analysis C — 400 KBA registration regions

The full one-row-per-KBA-code metrics are in [`batch15_kba_district_metrics.csv`](batch15_kba_district_metrics.csv).

| Check | Result |
|---|---|
| Rows | 400 |
| Codes per snapshot | 2026-01-01: 400, 2026-04-01: 400, 2026-07-01: 400 |
| Identity changes | 0 |
| Numeric NULLs | 0 |
| Zero denominators | 0 |
| Percentage-growth eligible | 377 |
| Percentage-growth excluded | 23 |
| Trier shared region | 07211 TRIER-SAARBURG — one KBA row; no allocation |

### Regional growth distributions

| Metric | N | Min | P10 | Median | Mean | P90 | Max | Std. dev. |
|---|---|---|---|---|---|---|---|---|
| BEV growth Jan–Jul (%) | 400 | 3.90 | 13.77 | 17.38 | 17.36 | 21.03 | 30.30 | 3.03 |
| PHEV growth Jan–Jul (%) | 400 | -16.34 | 6.99 | 10.48 | 10.37 | 13.69 | 33.72 | 3.81 |
| BEV penetration July (%) | 400 | 1.45 | 2.47 | 4.53 | 4.46 | 5.83 | 13.20 | 1.35 |
| PHEV penetration July (%) | 400 | 1.24 | 1.62 | 2.13 | 2.24 | 2.89 | 7.06 | 0.68 |
| Combined plug-in penetration July (%) | 400 | 2.69 | 4.21 | 6.71 | 6.70 | 8.50 | 20.26 | 1.91 |

The 400-region weighted BEV growth is 16.26% versus an unweighted mean of region-level growth rates of 17.36%. For PHEVs the corresponding values are 9.25% and 10.37%. The weighted result answers how the covered stock changed in aggregate; the unweighted mean gives each region equal influence and is more sensitive to small starting stocks.

### Largest absolute July stock and January–July change

**BEV stock:**

| Rank | Code | Region | State | July BEV | July penetration |
|---|---|---|---|---|---|
| 1 | 09162 | MUENCHEN,STADT | Bayern | 62,153 | 7.84% |
| 2 | 11000 | BERLIN | Berlin | 54,437 | 4.47% |
| 3 | 02000 | HAMBURG | Hamburg | 49,560 | 5.97% |
| 4 | 03241 | HANNOVER | Niedersachsen | 31,938 | 5.28% |
| 5 | 05315 | KOELN,STADT | Nordrhein-Westfalen | 28,871 | 5.77% |
| 6 | 06412 | FRANKFURT AM MAIN,STADT | Hessen | 25,871 | 7.34% |
| 7 | 05111 | DUESSELDORF, STADT | Nordrhein-Westfalen | 25,112 | 7.60% |
| 8 | 08111 | STUTTGART,STADT | Baden-Württemberg | 25,035 | 8.30% |
| 9 | 08226 | RHEIN-NECKAR-KREIS | Baden-Württemberg | 24,353 | 6.66% |
| 10 | 09184 | MUENCHEN | Bayern | 21,910 | 8.44% |

**PHEV stock:**

| Rank | Code | Region | State | July PHEV | July penetration |
|---|---|---|---|---|---|
| 1 | 09162 | MUENCHEN,STADT | Bayern | 36,677 | 4.63% |
| 2 | 02000 | HAMBURG | Hamburg | 34,970 | 4.21% |
| 3 | 11000 | BERLIN | Berlin | 34,743 | 2.85% |
| 4 | 05315 | KOELN,STADT | Nordrhein-Westfalen | 19,615 | 3.92% |
| 5 | 06412 | FRANKFURT AM MAIN,STADT | Hessen | 17,946 | 5.09% |
| 6 | 08111 | STUTTGART,STADT | Baden-Württemberg | 17,123 | 5.67% |
| 7 | 05111 | DUESSELDORF, STADT | Nordrhein-Westfalen | 16,849 | 5.10% |
| 8 | 03241 | HANNOVER | Niedersachsen | 15,042 | 2.49% |
| 9 | 09184 | MUENCHEN | Bayern | 13,488 | 5.19% |
| 10 | 08115 | BOEBLINGEN | Baden-Württemberg | 13,016 | 4.86% |

**BEV absolute increase:**

| Rank | Code | Region | BEV increase | BEV growth |
|---|---|---|---|---|
| 1 | 09162 | MUENCHEN,STADT | 7,458 | 13.64% |
| 2 | 02000 | HAMBURG | 6,886 | 16.14% |
| 3 | 11000 | BERLIN | 5,549 | 11.35% |
| 4 | 03241 | HANNOVER | 4,220 | 15.22% |
| 5 | 06412 | FRANKFURT AM MAIN,STADT | 3,961 | 18.08% |
| 6 | 08226 | RHEIN-NECKAR-KREIS | 3,323 | 15.80% |
| 7 | 08111 | STUTTGART,STADT | 3,198 | 14.64% |
| 8 | 05111 | DUESSELDORF, STADT | 3,023 | 13.69% |
| 9 | 09184 | MUENCHEN | 2,907 | 15.30% |
| 10 | 05315 | KOELN,STADT | 2,875 | 11.06% |

**PHEV absolute increase:**

| Rank | Code | Region | PHEV increase | PHEV growth |
|---|---|---|---|---|
| 1 | 02000 | HAMBURG | 6,912 | 24.63% |
| 2 | 11000 | BERLIN | 2,347 | 7.24% |
| 3 | 09184 | MUENCHEN | 1,847 | 15.87% |
| 4 | 06412 | FRANKFURT AM MAIN,STADT | 1,218 | 7.28% |
| 5 | 09162 | MUENCHEN,STADT | 1,178 | 3.32% |
| 6 | 03241 | HANNOVER | 1,175 | 8.47% |
| 7 | 06433 | GROSS-GERAU | 1,074 | 23.44% |
| 8 | 08226 | RHEIN-NECKAR-KREIS | 937 | 7.98% |
| 9 | 05315 | KOELN,STADT | 800 | 4.25% |
| 10 | 05111 | DUESSELDORF, STADT | 767 | 4.77% |

### Percentage-growth and penetration extremes

**Highest BEV growth among regions with January BEV stock ≥ 1,000:**

| Rank | Code | Region | Jan BEV | Jul BEV | Growth |
|---|---|---|---|---|---|
| 1 | 06439 | RHEINGAU-TAUNUS-KREIS | 5,597 | 7,293 | 30.30% |
| 2 | 03462 | WITTMUND | 1,083 | 1,354 | 25.02% |
| 3 | 03457 | LEER | 3,682 | 4,591 | 24.69% |
| 4 | 03352 | CUXHAVEN | 4,049 | 5,042 | 24.52% |
| 5 | 13076 | LUDWIGSLUST-PARCHIM | 2,419 | 3,005 | 24.22% |
| 6 | 03453 | CLOPPENBURG | 4,738 | 5,884 | 24.19% |
| 7 | 15089 | SALZLANDKREIS | 1,704 | 2,114 | 24.06% |
| 8 | 13074 | NORDWESTMECKLENBURG | 2,256 | 2,794 | 23.85% |
| 9 | 03255 | HOLZMINDEN | 1,390 | 1,718 | 23.60% |
| 10 | 07233 | VULKANEIFEL | 1,390 | 1,716 | 23.45% |

**Highest July BEV penetration:**

| Rank | Code | Region | BEV | Passenger cars | Penetration |
|---|---|---|---|---|---|
| 1 | 03103 | WOLFSBURG,STADT | 16,798 | 127,226 | 13.20% |
| 2 | 09161 | INGOLSTADT,STADT | 11,266 | 109,199 | 10.32% |
| 3 | 06414 | WIESBADEN,STADT | 19,770 | 220,762 | 8.96% |
| 4 | 05314 | BONN,STADT | 15,644 | 175,000 | 8.94% |
| 5 | 09184 | MUENCHEN | 21,910 | 259,660 | 8.44% |
| 6 | 08111 | STUTTGART,STADT | 25,035 | 301,767 | 8.30% |
| 7 | 08115 | BOEBLINGEN | 21,110 | 267,836 | 7.88% |
| 8 | 09162 | MUENCHEN,STADT | 62,153 | 792,903 | 7.84% |
| 9 | 05111 | DUESSELDORF, STADT | 25,112 | 330,572 | 7.60% |
| 10 | 05366 | EUSKIRCHEN | 12,312 | 164,020 | 7.51% |

Regions below the 1,000-vehicle baseline remain in the CSV with `bev_growth_pct_ranking_eligible=false`; they are not treated as automatically important because small denominators can create large percentages. All 400 regions have valid passenger-car denominators for penetration metrics.

## Analysis D — Ownership structure

FZ 27.5 supports commercial/private ownership crossed with BEV, PHEV and passenger-car totals at 16-state, `Sonstige` and national grain. It does not support district-level ownership. The complete table is in [`batch15_kba_ownership_metrics.csv`](batch15_kba_ownership_metrics.csv).

| July 2026 national measure | BEV | PHEV |
|---|---|---|
| Published total | 2,365,047 | 1,226,863 |
| Commercial | 909,485 | 559,761 |
| Private | 1,452,040 | 665,252 |
| Unallocated/unknown residual | 3,522 | 1,850 |
| Commercial share of observed owner rows | 38.51% | 45.69% |
| Private share of observed owner rows | 61.49% | 54.31% |
| Observed owner-row coverage of published total | 99.85% | 99.85% |

At the national grain, the private share of observed-owner BEV stock changed from 60.02% to 61.49% between January and July (1.46 percentage points). The corresponding PHEV share changed from 52.88% to 54.31% (1.43 percentage points). These are composition changes in published owner rows, not changes in individual ownership behavior.

The source contains 108 owner rows and 54 published total rows across the three snapshots. The publisher states that `zusammen` and `Deutschland insgesamt` include vehicles with missing or implausible holder-group data; those residuals are preserved rather than allocated to private or commercial ownership.

FZ 27.16 and FZ 27.17 also publish commercial/private BEV/PHEV fields at postcode and municipality grains. Their different geography, missing-cell patterns and municipality-key limitations are documented below; no district ownership is inferred from them.

## Analysis E — Postcode and municipality capabilities

The current normalized tables support descriptive inspection, but not a new geographic Crosswalk or BBSR join.

| Source/grain | Date | Rows | Distinct units/codes | Duplicate/total-row check | Rows with NULLs | NULL measure cells | Interpretation |
|---|---|---|---|---|---|---|---|
| FZ 27.16 postcode | 2026-01-01 | 8,195 | 8,195 | 0 | 1,429 | 2,492 | Descriptive postcode grain only; no district/state identifiers are present |
| FZ 27.16 postcode | 2026-04-01 | 8,195 | 8,195 | 0 | 1,378 | 2,386 | Descriptive postcode grain only; no district/state identifiers are present |
| FZ 27.16 postcode | 2026-07-01 | 8,196 | 8,196 | 0 | 1,321 | 2,300 | Descriptive postcode grain only; no district/state identifiers are present |
| FZ 27.17 municipality | 2026-01-01 | 10,743 | 400 | 0 | 5,371 | 14,842 | District code plus municipality name is the source key; municipality names are not globally unique |
| FZ 27.17 municipality | 2026-04-01 | 10,743 | 400 | 0 | 5,296 | 14,492 | District code plus municipality name is the source key; municipality names are not globally unique |
| FZ 27.17 municipality | 2026-07-01 | 10,743 | 400 | 0 | 5,229 | 14,114 | District code plus municipality name is the source key; municipality names are not globally unique |

Postcode rows are unique by `(reference_date, postal_code)` and have no district or state identifiers in the normalized table. The July release has one more postcode row than January/April, and missing source cells are retained as NULL. Municipality rows are unique by `(reference_date, district_code, municipality_name)`, cover all 400 KBA district codes, and contain 305 municipality names that occur in more than one district; names therefore cannot be treated as national unique IDs. Neither table is used to force a regional reconciliation with FZ 27.15.

## Analysis F — Historical quarterly series

`analytics.kba_national_quarterly_stock` contains 33 deduplicated national stock observations from 2018-07-01 through 2026-07-01. The releases overlap in historical dates; the deterministic rule is: one row per stock date, prefer the latest report snapshot, then the earliest source row. No historical national observation is treated as a regional observation.

| Stock date | Report snapshot | Passenger cars | BEV | PHEV | BEV share | PHEV share |
|---|---|---|---|---|---|---|
| 2018-07-01 | 2026-07-01 | 46,976,537 | 67,765 | 56,667 | 0.14% | 0.12% |
| 2019-01-01 | 2026-07-01 | 47,095,784 | 83,175 | 66,997 | 0.18% | 0.14% |
| 2019-07-01 | 2026-07-01 | 47,601,286 | 110,295 | 79,592 | 0.23% | 0.17% |
| 2020-01-01 | 2026-07-01 | 47,715,977 | 136,617 | 102,175 | 0.29% | 0.21% |
| 2020-07-01 | 2026-07-01 | 47,878,709 | 173,435 | 143,807 | 0.36% | 0.30% |
| 2021-01-01 | 2026-07-01 | 48,248,584 | 309,083 | 279,861 | 0.64% | 0.58% |
| 2021-07-01 | 2026-07-01 | 48,561,301 | 438,950 | 426,192 | 0.90% | 0.88% |
| 2022-01-01 | 2026-07-01 | 48,540,878 | 618,460 | 565,956 | 1.27% | 1.17% |
| 2022-07-01 | 2026-07-01 | 48,692,227 | 756,517 | 684,057 | 1.55% | 1.40% |
| 2023-01-01 | 2026-07-01 | 48,763,036 | 1,013,009 | 864,712 | 2.08% | 1.77% |
| 2023-07-01 | 2026-07-01 | 49,038,145 | 1,170,632 | 887,335 | 2.39% | 1.81% |
| 2024-01-01 | 2026-07-01 | 49,098,685 | 1,408,681 | 921,886 | 2.87% | 1.88% |
| 2024-07-01 | 2026-07-01 | 49,388,212 | 1,528,150 | 947,720 | 3.09% | 1.92% |
| 2025-01-01 | 2026-07-01 | 49,339,166 | 1,651,643 | 967,423 | 3.35% | 1.96% |
| 2025-07-01 | 2026-07-01 | 49,525,608 | 1,835,578 | 1,041,473 | 3.71% | 2.10% |
| 2026-01-01 | 2026-07-01 | 49,486,487 | 2,034,260 | 1,122,958 | 4.11% | 2.27% |
| 2026-07-01 | 2026-07-01 | 49,696,710 | 2,365,047 | 1,226,863 | 4.76% | 2.47% |

The historical series supports national BEV/PHEV trajectory description and provides a consistency check for the three current snapshots. It does not support district ownership, district history, sales-flow inference, or an older regional comparison without compatible source tables.

## Analysis G — Statistical findings

**OBSERVED:** The largest 10 of 400 KBA regions account for 14.78% of July 2026 covered-region BEV stock and 17.91% of covered-region PHEV stock. The largest absolute-stock regions are not necessarily the regions with the highest penetration or percentage growth.

**OBSERVED:** July district BEV penetration has a median of 4.53%, while the PHEV penetration median is 2.13%. The P10/P90 ranges show substantial regional variation without requiring a causal explanation.

**SUPPORTED ASSOCIATION:** Across the 400 regions, January–July BEV and PHEV percentage growth have a descriptive Pearson correlation of 0.464. This summarizes co-movement in the observed stock changes; it does not show that one powertrain caused the other or that infrastructure explains either change.

**PLAUSIBLE HYPOTHESIS:** Differences may reflect regional vehicle mix, registration composition, fleet turnover, reporting coverage and other unmeasured factors. The current source can describe the patterns but cannot identify their causes.

**NOT TESTABLE WITH CURRENT DATA:** The analysis cannot test charging demand, charger utilization, traffic corridors, population, area, income, grid constraints, vehicle sales flows, migration, or causal infrastructure effects. It also cannot equate a KBA registration region with a BBSR Kreis or allocate the shared Trier region.

## KPI evaluation

| Candidate | Status | Definition and denominator | Grain/date | Main limitation |
|---|---|---|---|---|
| National BEV stock | VALIDATED | Published FZ 27.2 `Deutschland / Elektro (BEV)` | National × snapshot | Registered stock, not sales |
| National PHEV stock | VALIDATED | Published FZ 27.2 `Deutschland / darunter Plug-in` | National × snapshot | Nested under Hybrid insgesamt for total-category logic |
| BEV/PHEV stock growth | VALIDATED | End stock minus start stock; change divided by start stock | National/state/KBA region × snapshots | Descriptive stock change, not flow |
| BEV/PHEV passenger-car penetration | VALIDATED | Powertrain stock divided by same-grain passenger-car total | State or 400 KBA region × snapshot | Coverage differs between national and 400-region scopes |
| Combined plug-in penetration | VALIDATED | BEV + PHEV divided by passenger cars | Same-grain snapshot | Only valid because BEV/PHEV are mutually exclusive here |
| State stock/penetration/change table | VALIDATED | FZ 27.2 mutually exclusive denominator rows | 16 states + separate Sonstige × snapshot | Absolute and percentage rankings answer different questions |
| KBA-region stock/penetration/change table | VALIDATED | FZ 27.15 district rows and passenger-car denominator | 400 KBA codes × snapshot | No BBSR equivalence; Trier remains one shared code |
| KBA-region percentage-growth ranking | EXPLORATORY | January–July growth with ≥1,000 January BEVs | 400 KBA codes | Threshold is exploratory; small-baseline regions excluded from ranking only |
| FZ 27.5 ownership composition | EXPLORATORY | Commercial/private shares of observed owner rows plus published-total coverage | State/residual/national × snapshot | Publisher totals include unknown/implausible holder groups |
| Postcode/municipality descriptive aggregates | EXPLORATORY | Source-grain rows with NULL-cell and key checks | Postcode or district+municipality × snapshot | No district/state crosswalk for postcodes; no municipality code |
| BBSR-based vehicle-stock ratio | UNSUPPORTED | No approved dated KBA-to-BBSR bridge | Not deployed | Do not create or infer in Batch 15 |

Recommended portfolio KPI set: national/state/KBA-region BEV and PHEV stock, same-grain penetration, combined plug-in penetration, absolute stock changes, and clearly labelled exploratory percentage-growth distributions. Keep ownership mix and postcode/municipality outputs as descriptive supporting analysis. Do not deploy new DuckDB KPI objects in this batch.

## Reproducible outputs

- [`scripts/15_analyze_kba_ev_stock.py`](../scripts/15_analyze_kba_ev_stock.py)
- [`batch15_kba_national_trends.csv`](batch15_kba_national_trends.csv)
- [`batch15_kba_state_metrics.csv`](batch15_kba_state_metrics.csv)
- [`batch15_kba_district_metrics.csv`](batch15_kba_district_metrics.csv)
- [`batch15_kba_ownership_metrics.csv`](batch15_kba_ownership_metrics.csv)
- [`batch15_kba_worksheet_capabilities.csv`](batch15_kba_worksheet_capabilities.csv)

Run from the repository root:

```bash
.venv/bin/python scripts/15_analyze_kba_ev_stock.py --json
```

## Validation results

| Check | Result |
|---|---|
| Source workbook fingerprints | PASS — all three expected SHA-256 values match |
| Worksheet inventory | PASS — 20 worksheets × 3 releases; 60 inventory rows |
| National BEV/PHEV/passenger-car reconciliation | PASS — 16 states + Sonstige = Deutschland; 16 states = 400-region table |
| KBA region coverage | PASS — 400 codes per snapshot, 1,200 source rows |
| District identity consistency | PASS — no code/name/state identity changes |
| District numeric nulls/zero denominators | PASS — none |
| PHEV category-overlap handling | PASS — PHEV not added to Hybrid insgesamt |
| Ownership grain | PASS — 18 geographies × 2 owner groups plus published totals per snapshot |
| Historical series | PASS — current 2026 observations reconcile to national FZ 27.2 values |
| DuckDB/source mutation | PASS — read-only connection; no source/reference writes |

### Source fingerprints

| Path | Bytes | SHA-256 | Result |
|---|---|---|---|
| data/raw/kba/fz27_202601.xlsx | 1,474,738 | 29ab2eaa178a1c6a3463d5cad707fee1e762241304ae6bb08c29702d6e6aea31 | MATCH |
| data/raw/kba/fz27_202604.xlsx | 1,482,694 | 28fffaa7d2f21ede6d7f6988a717b749b759a308755c472df4d391c73a0653e7 | MATCH |
| data/raw/kba/fz27_202607.xlsx | 1,478,376 | d6a26702fa6f8358cc5f0e15e88c04ac6c36527be404058674138dd9571bc803 | MATCH |

## Limitations and next analytical step

The KBA tables are published stock aggregates with alternative worksheet grains. The FZ 27.15 region is a KBA registration region, not automatically a Kreis; the 400-region passenger-car denominator excludes the national `Sonstige` residual. FZ 27.16/27.17 ownership fields contain missing numeric cells after parsing source dots, and municipality names are not global IDs. No BBSR integration, Trier allocation, charging-demand interpretation, or causal analysis was performed.

The next approved analytical step should be review of the Batch 15 findings and denominator choices, followed by an owner-approved decision on whether a dated, product-specific KBA compatibility bridge is warranted. Batch 16 and Tableau work remain outside this batch.
