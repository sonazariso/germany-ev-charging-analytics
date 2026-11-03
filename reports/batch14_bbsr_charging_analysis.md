# Batch 14 — BBSR charging infrastructure statistical analysis

Status: **PASS** — read-only analysis of the harmonized BBSR 2025 target-unit layer.

## Executive summary

The primary analytical source is `analytics.charging_by_bbsr_district_2025_harmonized` with `analytics.charging_by_bbsr_type_2025_harmonized` as its four-category reconciliation view. It contains 400 historical BBSR target units formed from 401 current BNetzA source components. The infrastructure snapshot is dated `2026-09-30` and the historical BBSR geographic stand is `2025-12-31`.

All four categories reconcile to 117,662 equipment records, 211,253 charging points, 156,155 normal points, 55,098 fast points, 40,950 points at least 150 kW, 6,950 points at least 350 kW, and 9,215.4173 MW of declared equipment nominal power. No unclassified infrastructure remains in the harmonized view.

Type 2 has the largest absolute infrastructure totals (77,986 points and 20,917 fast points), while type 4 has the highest within-category fast share (33.88%). These are different statements: absolute scale and relative mix should not be conflated.

The current data show declared-power composition, not accessibility, demand, utilization, coverage, or causal performance. The historical target geography intentionally combines Hanau and the remaining Main-Kinzig-Kreis; it does not assign an official 2026 BBSR type to Hanau.

## Dataset and geographic reference dates

| Item | Value |
|---|---|
| Primary district view | `analytics.charging_by_bbsr_district_2025_harmonized` |
| Primary category view | `analytics.charging_by_bbsr_type_2025_harmonized` |
| BNetzA source ID | `bnetza_charging_2026_09_30` |
| Infrastructure reference date | `2026-09-30` |
| BBSR geographic reference date | `2025-12-31` |
| Harmonization version | `batch13.2-2026-11-02-bbsr-2025-historical-boundary` |
| Historical target units | 400 |
| BNetzA source components | 401 |
| KBA/vehicle stock used | No |

The 400-unit target grain is not a new 2025 infrastructure snapshot. It is the BNetzA 2026-09-30 register aggregated to the BBSR 2025 historical geography. Hanau and remaining Main-Kinzig-Kreis form one historical target; Kassel city remains distinct from Kassel county; Trier city and Trier-Saarburg remain separate source components.

## National reconciliation

| Measure | Harmonized view | Direct core / parser | Expected |
|---|---|---|---|
| Equipment records | 117,662 | 117,662 | 117,662 |
| Charging points | 211,253 | 211,253 | 211,253 |
| Normal points (<=22 kW) | 156,155 | 156,155 | 156,155 |
| Fast points (>22 kW) | 55,098 | 55,098 | 55,098 |
| Points >=150 kW | 40,950 | 40,950 | 40,950 |
| Points >=350 kW | 6,950 | 6,950 | 6,950 |
| Unclassifiable power points | 0 | 0 | 0 |
| Declared equipment nominal power | 9,215.4173 MW | 9,215.4173 MW | 9,215.4173 MW |

Power classes are overlapping nested classifications: every >=150 kW point is fast, and every >=350 kW point is also >=150 kW. Normal and fast are mutually exclusive only because the fast threshold is defined as strictly above 22 kW.

## Category-level KPI comparison

| Type | BBSR category | Units | Source components | Equipment | Points | Equipment share | Point share | Fast share | >=150 share | >=350 share | Nominal MW | Nominal power share | Mean points/unit | Median points/unit | Mean points/equipment | Median points/equipment |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kreisfreie Großstadt | 68 | 68 | 39,789 | 69,863 | 33.82% | 33.07% | 18.75% | 13.87% | 1.69% | 2,373.0481 | 25.75% | 1,027.40 | 588.00 | 1.822 | 1.828 |
| 2 | städtischer Kreis | 131 | 132 | 42,191 | 77,986 | 35.86% | 36.92% | 26.82% | 19.87% | 3.37% | 3,509.5100 | 38.08% | 595.31 | 498.00 | 1.849 | 1.841 |
| 3 | ländlicher Kreis mit Verdichtungsansätzen | 98 | 98 | 18,042 | 32,342 | 15.33% | 15.31% | 32.63% | 24.36% | 4.47% | 1,669.6451 | 18.12% | 330.02 | 300.50 | 1.809 | 1.813 |
| 4 | dünn besiedelter ländlicher Kreis | 103 | 103 | 17,640 | 31,062 | 14.99% | 14.70% | 33.88% | 25.38% | 5.47% | 1,663.2141 | 18.05% | 301.57 | 263.00 | 1.819 | 1.819 |

Equipment and point shares are shares of national totals. Mean and median points per historical unit are unweighted across units. Mean and median points per equipment unit are the distributions of each unit's `charging_point_count / equipment_count`; the weighted ratio is available in the diagnostic CSV. None of these absolute or relative measures is an accessibility or quality score.

### Type 1 versus types 2–4

- Type 1 has 69,863 points, more than type 3 (32,342) and type 4 (31,062), but fewer than type 2 (77,986).
- Type 1's fast share is 18.75%; type 2 is 26.82%, type 3 is 32.63%, and type 4 is 33.88%.
- Type 1 contributes 23.78% of national fast points, whereas type 2 contributes 37.96%. The latter is an absolute national contribution, not a within-category percentage.
- The type 1 within-category >=150 kW share is 13.87%; the corresponding >=350 kW share is 1.69%. These are declared-power mix measures.

## Fast-charging and high-power structure

| Type | Normal points | Fast points | Fast share | National fast share | >=150 points | >=150 within | >=150 national | >=350 points | >=350 within | >=350 national |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 56,761 | 13,102 | 18.75% | 23.78% | 9,693 | 13.87% | 4.59% | 1,178 | 1.69% | 0.56% |
| 2 | 57,069 | 20,917 | 26.82% | 37.96% | 15,496 | 19.87% | 7.34% | 2,627 | 3.37% | 1.24% |
| 3 | 21,788 | 10,554 | 32.63% | 19.15% | 7,877 | 24.36% | 3.73% | 1,446 | 4.47% | 0.68% |
| 4 | 20,537 | 10,525 | 33.88% | 19.10% | 7,884 | 25.38% | 3.73% | 1,699 | 5.47% | 0.80% |

The report preserves the exact thresholds `fast >22 kW`, `high-power >=150 kW`, and `high-power >=350 kW`. A high fast or HPC share means a larger declared-power mix within the registered points; it does not establish better access for residents or drivers.

## Within-category geographic variation

| Measure | Type | Min | P10 | Median | Mean | P90 | Max | Std. dev. | Mean/median |
|---|---|---|---|---|---|---|---|---|---|
| Charging points per historical unit | 1 | 172.00 | 270.90 | 588.00 | 1,027.40 | 1,854.90 | 7,644.00 | 1,283.51 | 1.75 |
| Equipment records per historical unit | 1 | 89.00 | 147.40 | 320.50 | 585.13 | 1,035.40 | 4,999.00 | 787.89 | 1.83 |
| Fast-point share | 1 | 4.98 | 12.18 | 21.91 | 23.71 | 37.69 | 47.27 | 9.95 | 1.08 |
| >=150 kW point share | 1 | 3.63 | 9.26 | 16.51 | 17.51 | 27.79 | 38.10 | 7.70 | 1.06 |
| >=350 kW point share | 1 | 0.00 | 0.00 | 1.41 | 2.03 | 4.85 | 8.78 | 1.99 | 1.45 |
| Declared equipment nominal power (MW) | 1 | 5.03 | 10.23 | 24.96 | 34.90 | 54.42 | 215.42 | 36.38 | 1.40 |
| Charging points per equipment unit | 1 | 1.46 | 1.64 | 1.83 | 1.82 | 2.00 | 2.14 | 0.14 | 1.00 |
| Charging points per historical unit | 2 | 77.00 | 168.00 | 498.00 | 595.31 | 1,091.00 | 3,635.00 | 462.15 | 1.20 |
| Equipment records per historical unit | 2 | 42.00 | 90.00 | 271.00 | 322.07 | 619.00 | 1,972.00 | 249.79 | 1.19 |
| Fast-point share | 2 | 4.99 | 16.98 | 28.44 | 30.03 | 46.04 | 62.58 | 11.08 | 1.06 |
| >=150 kW point share | 2 | 2.27 | 11.10 | 20.41 | 22.29 | 35.38 | 52.54 | 9.36 | 1.09 |
| >=350 kW point share | 2 | 0.00 | 0.00 | 3.08 | 3.78 | 7.92 | 22.43 | 3.43 | 1.23 |
| Declared equipment nominal power (MW) | 2 | 3.42 | 7.57 | 24.67 | 26.79 | 47.25 | 155.11 | 19.17 | 1.09 |
| Charging points per equipment unit | 2 | 1.52 | 1.70 | 1.84 | 1.85 | 1.98 | 2.59 | 0.13 | 1.00 |
| Charging points per historical unit | 3 | 56.00 | 140.30 | 300.50 | 330.02 | 580.30 | 849.00 | 169.03 | 1.10 |
| Equipment records per historical unit | 3 | 30.00 | 70.80 | 172.00 | 184.10 | 319.60 | 610.00 | 98.45 | 1.07 |
| Fast-point share | 3 | 15.14 | 20.30 | 33.33 | 34.53 | 49.22 | 68.99 | 11.27 | 1.04 |
| >=150 kW point share | 3 | 6.99 | 13.25 | 24.47 | 25.84 | 39.71 | 58.86 | 10.60 | 1.06 |
| >=350 kW point share | 3 | 0.00 | 0.00 | 3.83 | 4.77 | 9.56 | 19.80 | 3.88 | 1.25 |
| Declared equipment nominal power (MW) | 3 | 1.91 | 6.64 | 16.14 | 17.04 | 28.53 | 38.57 | 8.60 | 1.06 |
| Charging points per equipment unit | 3 | 1.39 | 1.64 | 1.81 | 1.81 | 1.97 | 2.12 | 0.13 | 1.00 |
| Charging points per historical unit | 4 | 44.00 | 99.00 | 263.00 | 301.57 | 488.20 | 1,147.00 | 184.68 | 1.15 |
| Equipment records per historical unit | 4 | 23.00 | 54.20 | 153.00 | 171.26 | 271.00 | 717.00 | 118.23 | 1.12 |
| Fast-point share | 4 | 11.66 | 20.77 | 33.92 | 34.66 | 50.23 | 69.43 | 11.84 | 1.02 |
| >=150 kW point share | 4 | 2.82 | 11.62 | 22.12 | 25.53 | 42.32 | 61.15 | 11.64 | 1.15 |
| >=350 kW point share | 4 | 0.00 | 0.00 | 4.42 | 5.18 | 10.94 | 19.35 | 4.75 | 1.17 |
| Declared equipment nominal power (MW) | 4 | 2.15 | 4.09 | 13.11 | 16.15 | 29.78 | 61.42 | 12.14 | 1.23 |
| Charging points per equipment unit | 4 | 1.16 | 1.67 | 1.82 | 1.82 | 1.98 | 2.32 | 0.16 | 1.00 |

Percentiles use deterministic linear interpolation over the 400 historical target units within each category. Standard deviation is the population standard deviation of the displayed unit-level distribution. For share metrics, the denominator is the unit's own charging-point count; for points per equipment, units with zero equipment would be excluded rather than assigned an artificial ratio. The current harmonized data have valid denominators for all reported rows.

A mean/median ratio above 1 indicates right-skew in the unit distribution: a small number of larger units pull the mean above the median. Share metrics can also be unstable for small point denominators, which is why share-based rankings below apply an exploratory 30-point minimum.

## Weighted versus unweighted shares

| Group | Definition | Units | Weighted fast | Mean unit fast | Fast gap (pp) | Weighted >=150 | Mean unit >=150 | >=150 gap (pp) | Weighted >=350 | Mean unit >=350 | >=350 gap (pp) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kreisfreie Großstadt | 68 | 18.75% | 23.71% | -4.95 | 13.87% | 17.51% | -3.64 | 1.69% | 2.03% | -0.35 |
| 2 | städtischer Kreis | 131 | 26.82% | 30.03% | -3.21 | 19.87% | 22.29% | -2.42 | 3.37% | 3.78% | -0.42 |
| 3 | ländlicher Kreis mit Verdichtungsansätzen | 98 | 32.63% | 34.53% | -1.90 | 24.36% | 25.84% | -1.49 | 4.47% | 4.77% | -0.30 |
| 4 | dünn besiedelter ländlicher Kreis | 103 | 33.88% | 34.66% | -0.78 | 25.38% | 25.53% | -0.15 | 5.47% | 5.18% | 0.29 |
| ALL | All 400 historical units | 400 | 26.08% | 31.25% | -5.17 | 19.38% | 23.18% | -3.80 | 3.29% | 4.09% | -0.80 |

The weighted share gives every charging point one weight. The unweighted mean gives every historical unit one weight. When the values differ, smaller units can influence the unweighted mean more than their point volume would influence the national mix; this is a descriptive weighting effect, not evidence of better or worse access.

## Concentration and district-level outliers

| Measure | Top 1 | Top 5 | Top 10 | Largest unit code | Largest unit | Largest value |
|---|---|---|---|---|---|---|
| Charging points | 3.62% | 12.06% | 17.38% | 11000000 | Berlin, Stadt | 7,644 |
| Fast points | 2.28% | 7.46% | 11.22% | 11000000 | Berlin, Stadt | 1,256 |
| >=150 kW points | 2.44% | 7.58% | 11.22% | 11000000 | Berlin, Stadt | 1,000 |
| >=350 kW points | 1.96% | 7.86% | 12.83% | 11000000 | Berlin, Stadt | 136 |

The district-share HHI is 63.76 for total points and 42.17 for fast points on the 0–10,000 descriptive scale. This summarizes concentration only; it is not a market-power or service-quality measure.

### Largest absolute point totals

| Rank | Code | Historical unit | Type | Equipment | Points | Fast | >=150 | >=350 | Fast share | Points |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 11000000 | Berlin, Stadt | 1 | 4,999 | 7,644 | 1,256 | 1,000 | 136 | 16.43% | 7,644 |
| 2 | 02000000 | Hamburg, Freie und Hansestadt | 1 | 3,419 | 6,141 | 959 | 850 | 119 | 15.62% | 6,141 |
| 3 | 08111000 | Stuttgart, Stadtkreis | 1 | 2,421 | 4,381 | 218 | 159 | 10 | 4.98% | 4,381 |
| 4 | 09162000 | München, Landeshauptstadt | 1 | 2,393 | 3,672 | 451 | 265 | 24 | 12.28% | 3,672 |
| 5 | 03241000 | Region Hannover | 2 | 1,972 | 3,635 | 853 | 605 | 108 | 23.47% | 3,635 |
| 6 | 05315000 | Köln, Stadt | 1 | 1,477 | 2,711 | 593 | 321 | 12 | 21.87% | 2,711 |
| 7 | 05111000 | Düsseldorf, Stadt | 1 | 1,458 | 2,554 | 230 | 181 | 36 | 9.01% | 2,554 |
| 8 | 06412000 | Frankfurt am Main, Stadt | 1 | 1,321 | 2,165 | 248 | 198 | 32 | 11.45% | 2,165 |
| 9 | 08115000 | Böblingen | 2 | 1,119 | 2,033 | 259 | 195 | 18 | 12.74% | 2,033 |
| 10 | 05334000 | Städteregion Aachen | 2 | 986 | 1,786 | 441 | 289 | 68 | 24.69% | 1,786 |

### Largest absolute fast-point totals

| Rank | Code | Historical unit | Type | Equipment | Points | Fast | >=150 | >=350 | Fast share | Fast points |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 11000000 | Berlin, Stadt | 1 | 4,999 | 7,644 | 1,256 | 1,000 | 136 | 16.43% | 1,256 |
| 2 | 02000000 | Hamburg, Freie und Hansestadt | 1 | 3,419 | 6,141 | 959 | 850 | 119 | 15.62% | 959 |
| 3 | 03241000 | Region Hannover | 2 | 1,972 | 3,635 | 853 | 605 | 108 | 23.47% | 853 |
| 4 | 05315000 | Köln, Stadt | 1 | 1,477 | 2,711 | 593 | 321 | 12 | 21.87% | 593 |
| 5 | 09162000 | München, Landeshauptstadt | 1 | 2,393 | 3,672 | 451 | 265 | 24 | 12.28% | 451 |
| 6 | 08226000 | Rhein-Neckar-Kreis | 2 | 639 | 1,195 | 445 | 314 | 24 | 37.24% | 445 |
| 7 | 05334000 | Städteregion Aachen | 2 | 986 | 1,786 | 441 | 289 | 68 | 24.69% | 441 |
| 8 | 03454000 | Emsland | 4 | 640 | 1,147 | 434 | 307 | 75 | 37.84% | 434 |
| 9 | 06435000 | Main-Kinzig-Kreis | 2 | 585 | 991 | 378 | 327 | 77 | 38.14% | 378 |
| 10 | 08317000 | Ortenaukreis | 2 | 737 | 1,458 | 371 | 294 | 64 | 25.45% | 371 |

### Largest >=150 kW totals

| Rank | Code | Historical unit | Type | Equipment | Points | Fast | >=150 | >=350 | Fast share | >=150 kW points |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 11000000 | Berlin, Stadt | 1 | 4,999 | 7,644 | 1,256 | 1,000 | 136 | 16.43% | 1,000 |
| 2 | 02000000 | Hamburg, Freie und Hansestadt | 1 | 3,419 | 6,141 | 959 | 850 | 119 | 15.62% | 850 |
| 3 | 03241000 | Region Hannover | 2 | 1,972 | 3,635 | 853 | 605 | 108 | 23.47% | 605 |
| 4 | 06435000 | Main-Kinzig-Kreis | 2 | 585 | 991 | 378 | 327 | 77 | 38.14% | 327 |
| 5 | 05315000 | Köln, Stadt | 1 | 1,477 | 2,711 | 593 | 321 | 12 | 21.87% | 321 |
| 6 | 08226000 | Rhein-Neckar-Kreis | 2 | 639 | 1,195 | 445 | 314 | 24 | 37.24% | 314 |
| 7 | 03454000 | Emsland | 4 | 640 | 1,147 | 434 | 307 | 75 | 37.84% | 307 |
| 8 | 08317000 | Ortenaukreis | 2 | 737 | 1,458 | 371 | 294 | 64 | 25.45% | 294 |
| 9 | 05334000 | Städteregion Aachen | 2 | 986 | 1,786 | 441 | 289 | 68 | 24.69% | 289 |
| 10 | 14612000 | Dresden, Stadt | 1 | 575 | 1,143 | 356 | 286 | 44 | 31.15% | 286 |

### Largest >=350 kW totals

| Rank | Code | Historical unit | Type | Equipment | Points | Fast | >=150 | >=350 | Fast share | >=350 kW points |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 11000000 | Berlin, Stadt | 1 | 4,999 | 7,644 | 1,256 | 1,000 | 136 | 16.43% | 136 |
| 2 | 02000000 | Hamburg, Freie und Hansestadt | 1 | 3,419 | 6,141 | 959 | 850 | 119 | 15.62% | 119 |
| 3 | 03241000 | Region Hannover | 2 | 1,972 | 3,635 | 853 | 605 | 108 | 23.47% | 108 |
| 4 | 03358000 | Heidekreis | 4 | 321 | 555 | 305 | 271 | 106 | 54.95% | 106 |
| 5 | 06435000 | Main-Kinzig-Kreis | 2 | 585 | 991 | 378 | 327 | 77 | 38.14% | 77 |
| 6 | 03454000 | Emsland | 4 | 640 | 1,147 | 434 | 307 | 75 | 37.84% | 75 |
| 7 | 05170000 | Wesel | 2 | 651 | 1,180 | 355 | 277 | 73 | 30.08% | 73 |
| 8 | 05334000 | Städteregion Aachen | 2 | 986 | 1,786 | 441 | 289 | 68 | 24.69% | 68 |
| 9 | 13076000 | Ludwigslust-Parchim | 4 | 187 | 341 | 186 | 155 | 66 | 54.55% | 66 |
| 10 | 08317000 | Ortenaukreis | 2 | 737 | 1,458 | 371 | 294 | 64 | 25.45% | 64 |

### Highest and lowest fast shares among stable denominators

The share-ranking filter is `30` charging points. It is an exploratory stability filter, not an official standard. It excludes 0 of 400 units with fewer than 30 points (0.00% of units; 0 points, 0.00% of national points).

Highest fast shares:

| Rank | Code | Historical unit | Type | Equipment | Points | Fast | >=150 | >=350 | Fast share | Fast share |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 06632000 | Hersfeld-Rotenburg | 4 | 187 | 314 | 218 | 192 | 60 | 69.43% | 69.43 |
| 2 | 16062000 | Nordhausen | 3 | 87 | 158 | 109 | 93 | 8 | 68.99% | 68.99 |
| 3 | 16075000 | Saale-Orla-Kreis | 4 | 133 | 223 | 143 | 133 | 38 | 64.13% | 64.13 |
| 4 | 07334000 | Germersheim | 2 | 81 | 155 | 97 | 63 | 14 | 62.58% | 62.58 |
| 5 | 07138000 | Neuwied | 2 | 199 | 335 | 206 | 176 | 12 | 61.49% | 61.49 |
| 6 | 07319000 | Worms, kreisfreie Stadt | 2 | 60 | 105 | 63 | 54 | 4 | 60.00% | 60.00 |
| 7 | 03154000 | Helmstedt | 3 | 99 | 179 | 107 | 98 | 16 | 59.78% | 59.78 |
| 8 | 12061000 | Dahme-Spreewald | 4 | 250 | 401 | 238 | 191 | 42 | 59.35% | 59.35 |
| 9 | 16074000 | Saale-Holzland-Kreis | 3 | 114 | 211 | 123 | 96 | 2 | 58.29% | 58.29 |
| 10 | 03457000 | Leer | 3 | 172 | 317 | 184 | 127 | 34 | 58.04% | 58.04 |

Lowest fast shares:

| Rank | Code | Historical unit | Type | Equipment | Points | Fast | >=150 | >=350 | Fast share | Fast share |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 08111000 | Stuttgart, Stadtkreis | 1 | 2,421 | 4,381 | 218 | 159 | 10 | 4.98% | 4.98 |
| 2 | 08235000 | Calw | 2 | 265 | 441 | 22 | 10 | 0 | 4.99% | 4.99 |
| 3 | 08221000 | Heidelberg, Stadtkreis | 1 | 411 | 784 | 60 | 46 | 0 | 7.65% | 7.65 |
| 4 | 08121000 | Heilbronn, Stadtkreis | 1 | 396 | 834 | 67 | 51 | 5 | 8.03% | 8.03 |
| 5 | 05111000 | Düsseldorf, Stadt | 1 | 1,458 | 2,554 | 230 | 181 | 36 | 9.01% | 9.01 |
| 6 | 08316000 | Emmendingen | 2 | 264 | 684 | 67 | 54 | 0 | 9.80% | 9.80 |
| 7 | 06413000 | Offenbach am Main, Stadt | 1 | 113 | 172 | 18 | 16 | 0 | 10.47% | 10.47 |
| 8 | 06437000 | Odenwaldkreis | 2 | 77 | 149 | 17 | 10 | 0 | 11.41% | 11.41 |
| 9 | 06412000 | Frankfurt am Main, Stadt | 1 | 1,321 | 2,165 | 248 | 198 | 32 | 11.45% | 11.45 |
| 10 | 06433000 | Groß-Gerau | 2 | 660 | 1,274 | 148 | 132 | 2 | 11.62% | 11.62 |

The rankings are descriptive outlier screens. They do not rank district quality, need, coverage, reliability, or accessibility.

## Evidence-supported interpretations and unresolved hypotheses

**OBSERVED:** Type 4 has the highest within-category fast share (33.88%), while type 2 has the largest absolute fast-point count (20,917). The ranking reverses because type 2 has more total points.

**OBSERVED:** The category ordering for fast share (18.75%, 26.82%, 32.63%, 33.88%) is also the ordering for >=150 kW share (13.87%, 19.87%, 24.36%, 25.38%). This is an association across four aggregate groups, not a causal result.

**SUPPORTED ASSOCIATION:** In this four-category table, higher fast-point shares coincide with higher high-power shares. The result is consistent with category-level differences in declared-power mix, but the analysis cannot separate category composition from other correlated geography or reporting factors.

**OBSERVED:** The all-unit weighted fast share is 26.08%, compared with an unweighted historical-unit mean of 31.25%; the difference is -5.17 percentage points. This demonstrates why a national point-weighted share and an average district share answer different questions.

**PLAUSIBLE HYPOTHESIS:** Differences may reflect a combination of normal-versus-fast mix, concentration of high-power equipment, and the size/composition of individual historical units. The current descriptive fields can show these patterns but cannot identify a cause.

**NOT TESTABLE WITH CURRENT DATA:** The analysis cannot test whether motorway corridors, residents, traffic flows, EV ownership, demand, utilization, queueing, reliability, or actual delivered energy explain the observed differences. It also cannot claim that a higher fast share means better accessibility.

| Hypothesis or question | Current evidence | Status | Additional data needed |
|---|---|---|---|
| Different normal/fast mix explains category differences | Counts and shares are present in the harmonized layer | OBSERVED / descriptive | None for description; demand or utilization data for explanation |
| High-power concentration drives category differences | >=150 and >=350 kW counts/shares and outliers are present | OBSERVED / descriptive | Availability, sessions, energy, or capacity data |
| Population or resident density explains infrastructure mix | No population denominator in the analytical layer | NOT TESTABLE | Dated population and area data at the same historical geography |
| Motorway/traffic corridors explain fast concentration | No traffic or corridor field used | NOT TESTABLE | Dated traffic flow, road-network, and site-location data |
| EV stock or demand explains infrastructure mix | KBA stock is intentionally excluded from this batch | NOT TESTABLE | Approved, date-compatible vehicle and demand data with a valid geography bridge |
| Higher fast share means better accessibility | No utilization, queue, uptime, or service-coverage measure | UNSUPPORTED | Availability, sessions, queue time, reliability, and accessibility denominators |

## KPI evaluation for future Tableau work

The candidates below are evaluated for a future Tableau layer only. Batch 14 deploys no KPI views and no dashboard. BBSR-based BEV-to-charger ratios are intentionally excluded.

| Candidate | Status | Definition / numerator / denominator | Source | Grain and time | Added value and Tableau suitability | Main risk |
|---|---|---|---|---|---|---|
| BBSR category point count and national share | VALIDATED | Charging points; points / all 211,253 points | Harmonized district/type views over core point rows | BBSR 2025 target; BNetzA 2026-09-30 | High; simple bars/maps and tooltips | Absolute scale can be mistaken for access |
| BBSR category equipment count and national share | VALIDATED | Equipment rows; equipment / all 117,662 rows | Harmonized district/type views over core equipment rows | BBSR 2025 target; BNetzA 2026-09-30 | High as a separate equipment-grain context | Equipment is not point count |
| Fast point count and within-category fast share | VALIDATED | Fast points (>22 kW); fast / category points | Harmonized district/type views; maximum `connector_power_raw` parser | BBSR target and BNetzA snapshot | High; paired count-plus-share view | Declared power is not utilization |
| >=150 and >=350 kW point counts/shares | VALIDATED | Nested high-power counts; each / category points | Harmonized district/type views; maximum `connector_power_raw` parser | BBSR target and BNetzA snapshot | High; nested threshold comparison | Thresholds are overlapping and not accessibility measures |
| Unit distribution percentiles | EXPLORATORY | P10, median, P90 of points, equipment, shares, power, ratios | Harmonized district view | 400 historical units; BNetzA snapshot | High for box plots and distribution context | Small denominators and skew |
| Weighted versus unweighted fast/HPC shares | EXPLORATORY | Point-weighted share versus mean unit share | Harmonized district view | BBSR category or all units | Medium-high; exposes denominator sensitivity | Can be overread as performance |
| Top-1/top-5/top-10 concentration share | EXPLORATORY | Points in top k units / national points | Harmonized district view | 400 historical units; BNetzA snapshot | Medium; compact concentration story | Ranking is not quality or need |
| Declared nominal equipment power | VALIDATED | Sum equipment nominal kW / 1,000 | Harmonized district view over core equipment rows | BBSR target and BNetzA snapshot | Medium as capacity context | Not delivered energy or simultaneous capacity |
| BBSR-based BEV-to-charger ratio | UNSUPPORTED | Would require KBA-to-BBSR classification and compatible dates | No approved BBSR/KBA source bridge | No approved current grain | Do not include | No valid BBSR/KBA bridge in this batch |

Recommended small Tableau set: category point count/share, fast count/share, nested >=150 and >=350 kW count/share, and a distribution view showing median/P10/P90 unit metrics. Keep nominal power and concentration as context panels and show the source dates and historical-boundary caveat on every sheet.

## Limitations and analytical opportunities

- The BNetzA register is a published register and is not an exhaustive census of every publicly accessible charger.
- A point slot is not necessarily a connector count, simultaneous service capacity, or an available point at every moment.
- Declared nominal and connector power are not delivered energy, utilization, uptime, queue time, or reliability.
- The BBSR target is historical 2025 geography applied to a 2026 infrastructure snapshot; it is not an official 2026 BBSR reclassification.
- Absolute counts and shares lack population, area, traffic, EV-stock, and demand denominators in this batch.
- Future phases could add approved same-vintage population/area denominators, traffic and corridor evidence, and operational utilization data. No additional dataset was downloaded for Batch 14.

## Validation results

| Check | Result | Evidence |
|---|---|---|
| national equipment total | PASS | 117,662 |
| national point total | PASS | 211,253 |
| normal point total | PASS | 156,155 |
| fast point total | PASS | 55,098 |
| >=150 kW point total | PASS | 40,950 |
| >=350 kW point total | PASS | 6,950 |
| unclassifiable point total | PASS | 0 |
| declared point reconciliation | PASS | 211,253 |
| nominal equipment power | PASS | 9215.4173 MW |
| historical unit count | PASS | 400 |
| source component count | PASS | 401 |
| zero unclassified infrastructure | PASS | 0 rows |
| duplicate equipment keys | PASS | 0 |
| duplicate point keys | PASS | 0 |
| orphan points | PASS | 0 |
| source fingerprints | PASS | 4 matched |

### Source fingerprints

| Path | Purpose | Bytes | Result |
|---|---|---|---|
| data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx | BNetzA source workbook | 31,722,320 | MATCH |
| data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx | BBSR raw reference workbook | 8,768,335 | MATCH |
| data/reference/bbsr_settlement_types_2025.csv | BBSR derived four-category reference | 84,864 | MATCH |
| data/reference/bnetza_bbsr_historical_harmonization_2025.csv | Batch 13.2 source-component harmonization reference | 354,503 | MATCH |

The script opened DuckDB with `read_only=True`, read only the existing harmonized analytical views plus core tables for independent reconciliation, and did not create or alter any database object. No raw data, BBSR reference, Crosswalk, KBA object, or vehicle-stock table was changed.

## Reproducibility and next step

Run from the repository root:

```bash
.venv/bin/python scripts/14_analyze_bbsr_charging_patterns.py --json
```

The next approved step should be review of the analytical findings and KPI definitions. Tableau dashboard development or BBSR/KBA vehicle-stock integration remains outside Batch 14.
