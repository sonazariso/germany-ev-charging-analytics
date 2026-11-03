# Batch 17 — temporal validity and sensitivity of cross-source EV charging KPIs

**Batch status: PASS**

This report is a deterministic, read-only analysis of temporal compatibility between KBA registered passenger-car stock and the BNetzA charging register. It distinguishes the observed September publication from a retrospective equipment-commissioning cohort; the latter is not a historical July infrastructure snapshot.

## 1. Executive summary

**OBSERVED:** The BNetzA register snapshot dated **2026-09-30** contains 117,662 equipment records and 211,253 populated point slots. The maximum-per-point parser classifies 156,155 normal (<=22 kW), 55,098 fast (>22 kW), 40,950 at >=150 kW and 6,950 at >=350 kW. Declared equipment nominal power is 9,215.4173 MW.

**OBSERVED:** The July KBA state-fuel snapshot contains 2,365,047 national BEVs, 1,226,863 national PHEVs and 49,696,710 passenger cars. The 16 named states contain 2,362,218 BEVs and 1,225,241 PHEVs; `Sonstige` contains 2,829 BEVs and 1,622 PHEVs. The state and 400-region totals are not double-counted.

**QUALITY:** All 117,662 commissioning raw values are nonblank and parse successfully; no equipment is dated after the September snapshot. 2,762 equipment records and 4,888 point rows were commissioned after the July 1 cutoff, representing 2.35% of equipment and 2.31% of points.

**SENSITIVITY:** The retrospective September-survivor cohort contains 114,900 equipment records and 206,365 currently associated point rows. The 16-state BEVs-per-point ratio changes from 11.181938 in the published September comparison to 11.446796 in the survivor cohort (+2.37%); this is a cohort sensitivity, not observed July infrastructure.

**RECOMMENDATION:** BEVs per registered point is **CONTEXT_ONLY**: a secondary contextual measure with both dates visible, not a headline adequacy KPI. Power-normalized ratios, share gaps, rank comparisons and correlations remain **EXPLORATORY_SENSITIVITY**. No adequacy, shortage or surplus KPI is supported.

## 2. Data-source vintages and definitions

| Concept | Value | Meaning | Do not substitute |
|---|---|---|---|
| KBA vehicle-stock reference date | 2026-01-01 / 2026-04-01 / 2026-07-01 | Registered passenger-car stock reported by KBA at each snapshot | New registrations, sales, charging demand, or a BNetzA date |
| Primary KBA date | 2026-07-01 | Vehicle denominator used for the primary comparison | An observed July infrastructure stock |
| BNetzA publication/snapshot date | 2026-09-30 | Register rows and statuses represented in the source workbook | Equipment commissioning date or point activation date |
| Equipment commissioning date | Equipment-level parsed DATE | Source value retained in commissioning_date_raw and parsed into commissioning_date | The date each individual point became accessible |
| Point-level activation date | Not available | core.charging_point has no activation-date field | Equipment commissioning date |
| Equipment status | Observed in September | Current register label such as In Betrieb or In Wartung | Verified historical operational availability or uptime |
| July cutoff | 2026-07-01 inclusive | Cohort selection boundary for equipment commissioning dates | A historical July registry snapshot |

The July 1 KBA stock and September 30 BNetzA snapshot are **91 days apart**. Perspective A is labelled **CROSS-SNAPSHOT DESCRIPTIVE COMPARISON**. Perspective B is labelled **RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE**.

## 3. Commissioning-date quality audit

| Check | Result | Interpretation |
|---|---|---|
| Equipment rows | 117,662 | All normalized BNetzA equipment rows in the September source |
| NULL raw values | 0 | No missing source value observed |
| Blank raw values | 0 | No blank source value observed |
| Parsed NULL dates | 0 | No parsed-date NULL |
| Parsing failures | 0 | Nonblank raw value with no parsed date |
| Non-numeric raw values | 0 | Current raw values are Excel-style numeric serial strings |
| Dates after 2026-09-30 | 0 | No future commissioning date relative to the source snapshot |
| Dates after 2026-07-01 | 2,762 | Later commissioning records excluded from the survivor cohort |
| Dates exactly 2026-07-01 | 80 | Boundary rows are included by the <= cutoff rule |
| Minimum / maximum parsed date | 1992-10-01 / 2026-09-30 | Historical values are retained; a very old date is not silently changed |

The earliest parsed commissioning date is 1992-10-01; 0 dates precede 1900 and 21 equipment records fall in years before 2010. These are unusual historical source values for audit, not evidence that all points were accessible continuously since commissioning.

### Distribution by commissioning year

| Year | Equipment | Point rows | Fast points | >=150 kW | >=350 kW |
|---|---|---|---|---|---|
| 1992 | 1 | 1 | 0 | 0 | 0 |
| 2001 | 2 | 5 | 0 | 0 | 0 |
| 2003 | 1 | 3 | 2 | 0 | 0 |
| 2004 | 8 | 16 | 16 | 16 | 0 |
| 2005 | 1 | 2 | 0 | 0 | 0 |
| 2007 | 4 | 5 | 0 | 0 | 0 |
| 2008 | 1 | 2 | 0 | 0 | 0 |
| 2009 | 3 | 6 | 0 | 0 | 0 |
| 2010 | 32 | 64 | 0 | 0 | 0 |
| 2011 | 93 | 185 | 2 | 2 | 0 |
| 2012 | 130 | 262 | 4 | 4 | 0 |
| 2013 | 99 | 195 | 0 | 0 | 0 |
| 2014 | 166 | 324 | 2 | 0 | 0 |
| 2015 | 388 | 768 | 39 | 2 | 0 |
| 2016 | 879 | 1,722 | 183 | 2 | 0 |
| 2017 | 1,596 | 3,115 | 425 | 9 | 0 |
| 2018 | 3,531 | 6,892 | 636 | 135 | 108 |
| 2019 | 4,898 | 9,353 | 958 | 558 | 258 |
| 2020 | 6,447 | 11,848 | 1,512 | 899 | 65 |
| 2021 | 9,676 | 17,515 | 2,909 | 2,175 | 57 |
| 2022 | 15,361 | 27,450 | 5,085 | 4,089 | 123 |
| 2023 | 23,794 | 41,241 | 10,734 | 8,064 | 449 |
| 2024 | 19,785 | 36,145 | 11,830 | 8,835 | 985 |
| 2025 | 19,962 | 35,090 | 14,084 | 10,913 | 2,912 |
| 2026 | 10,804 | 19,044 | 6,677 | 5,247 | 1,993 |

### 2026 monthly distribution

| Month | Equipment | Point rows | Fast points | >=150 kW | >=350 kW |
|---|---|---|---|---|---|
| 2026-01 | 957 | 1,665 | 509 | 403 | 156 |
| 2026-02 | 1,519 | 2,779 | 670 | 458 | 110 |
| 2026-03 | 1,495 | 2,608 | 1,102 | 842 | 300 |
| 2026-04 | 1,427 | 2,401 | 936 | 757 | 263 |
| 2026-05 | 1,250 | 2,171 | 772 | 604 | 236 |
| 2026-06 | 1,314 | 2,396 | 940 | 748 | 307 |
| 2026-07 | 1,221 | 2,229 | 954 | 780 | 281 |
| 2026-08 | 974 | 1,657 | 499 | 419 | 218 |
| 2026-09 | 647 | 1,138 | 295 | 236 | 122 |

### Status and geographic distribution of later-commissioned records

| Status | All equipment | All declared points | After cutoff equipment | After cutoff declared points |
|---|---|---|---|---|
| In Betrieb | 117,642 | 211,214 | 2,762 | 4,888 |
| In Wartung | 20 | 39 | 0 | 0 |

| State | Later equipment | Later points | % of state points | % of national later points |
|---|---|---|---|---|
| Nordrhein-Westfalen | 539 | 978 | 2.35% | 20.01% |
| Bayern | 518 | 916 | 2.28% | 18.74% |
| Niedersachsen | 352 | 682 | 3.23% | 13.95% |
| Baden-Württemberg | 273 | 465 | 1.31% | 9.51% |
| Hamburg | 198 | 355 | 5.78% | 7.26% |
| Hessen | 166 | 287 | 1.77% | 5.87% |
| Schleswig-Holstein | 119 | 223 | 2.75% | 4.56% |
| Rheinland-Pfalz | 132 | 216 | 2.67% | 4.42% |
| Berlin | 143 | 210 | 2.75% | 4.30% |
| Mecklenburg-Vorpommern | 107 | 171 | 5.18% | 3.50% |
| Sachsen | 75 | 135 | 1.87% | 2.76% |
| Thüringen | 54 | 98 | 2.30% | 2.00% |
| Brandenburg | 38 | 67 | 1.33% | 1.37% |
| Sachsen-Anhalt | 35 | 57 | 1.51% | 1.17% |
| Bremen | 10 | 20 | 1.25% | 0.41% |
| Saarland | 3 | 8 | 0.53% | 0.16% |

## 4. September equipment/point commissioning cohorts

| Perspective | Equipment | Point rows | Normal | Fast | >=150 kW | >=350 kW | Nominal MW | Status |
|---|---|---|---|---|---|---|---|---|
| Published September snapshot | 117,662 | 211,253 | 156,155 | 55,098 | 40,950 | 6,950 | 9,215.4173 | Observed BNetzA snapshot; all statuses retained |
| Retrospective September-survivor cohort (commissioned <= 2026-07-01) | 114,900 | 206,365 | 152,981 | 53,384 | 39,543 | 6,335 | 8,924.3549 | September status retained; not July operational status |
| Post-cutoff complement (commissioned > 2026-07-01) | 2,762 | 4,888 | 3,174 | 1,714 | 1,407 | 615 | 291.0624 | All currently In Betrieb in this snapshot; not proof of July absence/accessibility |

The survivor calculation uses only equipment present in the September source and keeps their currently reported point rows. Equipment removed before September is absent; point slots may have been added or modified after commissioning; the September status does not establish July operation; and no historical opening-hours or availability state can be reconstructed. The cohort is neither a mathematical upper nor lower bound on actual July infrastructure.

The commissioning-date quality is sufficient for a reproducible equipment-level survivor calculation in this snapshot, but it is not sufficient to reconstruct point-level historical existence, activation, accessibility or operational status.

## 5. Published snapshot KPI results

Perspective A uses the July KBA vehicle denominator and the full September BNetzA infrastructure denominator. It is a descriptive cross-snapshot comparison, not a same-day infrastructure adequacy measure.

| State | BEV stock | Sep points | Fast | >=150 | >=350 | BEVs/point | Points/1,000 BEVs | Fast/1,000 BEVs |
|---|---|---|---|---|---|---|---|---|
| Baden-Württemberg | 369,574 | 35,437 | 6,264 | 4,525 | 689 | 10.43 | 95.89 | 16.95 |
| Bayern | 459,811 | 40,215 | 10,490 | 7,694 | 1,327 | 11.43 | 87.46 | 22.81 |
| Berlin | 54,437 | 7,644 | 1,256 | 1,000 | 136 | 7.12 | 140.42 | 23.07 |
| Brandenburg | 49,103 | 5,035 | 1,752 | 1,340 | 220 | 9.75 | 102.54 | 35.68 |
| Bremen | 12,394 | 1,600 | 347 | 219 | 32 | 7.75 | 129.09 | 28.00 |
| Hamburg | 49,560 | 6,141 | 959 | 850 | 119 | 8.07 | 123.91 | 19.35 |
| Hessen | 208,073 | 16,240 | 4,368 | 3,456 | 510 | 12.81 | 78.05 | 20.99 |
| Mecklenburg-Vorpommern | 22,196 | 3,298 | 1,291 | 1,065 | 282 | 6.73 | 148.59 | 58.16 |
| Niedersachsen | 259,973 | 21,113 | 6,807 | 4,873 | 985 | 12.31 | 81.21 | 26.18 |
| Nordrhein-Westfalen | 527,377 | 41,536 | 10,306 | 7,432 | 1,212 | 12.70 | 78.76 | 19.54 |
| Rheinland-Pfalz | 119,839 | 8,092 | 3,042 | 2,316 | 387 | 14.81 | 67.52 | 25.38 |
| Saarland | 25,038 | 1,519 | 466 | 362 | 40 | 16.48 | 60.67 | 18.61 |
| Sachsen | 56,074 | 7,223 | 2,263 | 1,658 | 262 | 7.76 | 128.81 | 40.36 |
| Sachsen-Anhalt | 29,116 | 3,785 | 1,510 | 1,145 | 160 | 7.69 | 130.00 | 51.86 |
| Schleswig-Holstein | 87,627 | 8,120 | 2,308 | 1,710 | 364 | 10.79 | 92.67 | 26.34 |
| Thüringen | 32,026 | 4,255 | 1,669 | 1,305 | 225 | 7.53 | 132.86 | 52.11 |

The published point counts are current September register rows. Equipment count, point count, connector count, status, nominal power and operational availability remain different concepts; the point denominator does not explode connector text.

## 6. Retrospective survivor-cohort results

Perspective B retains September point rows attached to equipment commissioned on or before 2026-07-01. It is useful only as a transparent sensitivity analysis of retrospective selection, not as a true July snapshot.

| State | Survivor equipment | Survivor points | Fast | >=150 | >=350 | BEVs/point | Points/1,000 BEVs | Fast/1,000 BEVs |
|---|---|---|---|---|---|---|---|---|
| Baden-Württemberg | 18,745 | 34,972 | 6,122 | 4,415 | 637 | 10.57 | 94.63 | 16.57 |
| Bayern | 22,545 | 39,299 | 10,065 | 7,359 | 1,147 | 11.70 | 85.47 | 21.89 |
| Berlin | 4,856 | 7,434 | 1,242 | 986 | 136 | 7.32 | 136.56 | 22.82 |
| Brandenburg | 3,012 | 4,968 | 1,722 | 1,314 | 210 | 9.88 | 101.18 | 35.07 |
| Bremen | 882 | 1,580 | 345 | 217 | 32 | 7.84 | 127.48 | 27.84 |
| Hamburg | 3,221 | 5,786 | 921 | 820 | 119 | 8.57 | 116.75 | 18.58 |
| Hessen | 8,874 | 15,953 | 4,280 | 3,378 | 474 | 13.04 | 76.67 | 20.57 |
| Mecklenburg-Vorpommern | 1,768 | 3,127 | 1,213 | 991 | 236 | 7.10 | 140.88 | 54.65 |
| Niedersachsen | 11,302 | 20,431 | 6,521 | 4,649 | 891 | 12.72 | 78.59 | 25.08 |
| Nordrhein-Westfalen | 22,127 | 40,558 | 10,005 | 7,185 | 1,123 | 13.00 | 76.91 | 18.97 |
| Rheinland-Pfalz | 4,440 | 7,876 | 2,972 | 2,256 | 353 | 15.22 | 65.72 | 24.80 |
| Saarland | 798 | 1,511 | 466 | 362 | 40 | 16.57 | 60.35 | 18.61 |
| Sachsen | 3,800 | 7,088 | 2,193 | 1,592 | 236 | 7.91 | 126.40 | 39.11 |
| Sachsen-Anhalt | 1,966 | 3,728 | 1,489 | 1,129 | 156 | 7.81 | 128.04 | 51.14 |
| Schleswig-Holstein | 4,276 | 7,897 | 2,213 | 1,627 | 338 | 11.10 | 90.12 | 25.25 |
| Thüringen | 2,288 | 4,157 | 1,615 | 1,263 | 207 | 7.70 | 129.80 | 50.43 |

A point associated with an equipment record commissioned before July is not proof that that same point existed, was accessible, or was operational in July. The cohort should not be labelled `July infrastructure` in Tableau or future extracts.

## 7. State-level sensitivity comparisons

| State | BEV | Sep points | Survivor points | Point difference | Fast difference | >=150 difference | >=350 difference | BEVs/point Sep | BEVs/point survivor | % ratio change | Rank Sep→survivor |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Baden-Württemberg | 369,574 | 35,437 | 34,972 | 465 | 142 | 110 | 52 | 10.429 | 10.568 | +1.33% | 9 → 9 (+0) |
| Bayern | 459,811 | 40,215 | 39,299 | 916 | 425 | 335 | 180 | 11.434 | 11.700 | +2.33% | 11 → 11 (+0) |
| Berlin | 54,437 | 7,644 | 7,434 | 210 | 14 | 14 | 0 | 7.122 | 7.323 | +2.82% | 2 → 2 (+0) |
| Brandenburg | 49,103 | 5,035 | 4,968 | 67 | 30 | 26 | 10 | 9.752 | 9.884 | +1.35% | 8 → 8 (+0) |
| Bremen | 12,394 | 1,600 | 1,580 | 20 | 2 | 2 | 0 | 7.746 | 7.844 | +1.27% | 5 → 5 (+0) |
| Hamburg | 49,560 | 6,141 | 5,786 | 355 | 38 | 30 | 0 | 8.070 | 8.566 | +6.14% | 7 → 7 (+0) |
| Hessen | 208,073 | 16,240 | 15,953 | 287 | 88 | 78 | 36 | 12.812 | 13.043 | +1.80% | 14 → 14 (+0) |
| Mecklenburg-Vorpommern | 22,196 | 3,298 | 3,127 | 171 | 78 | 74 | 46 | 6.730 | 7.098 | +5.47% | 1 → 1 (+0) |
| Niedersachsen | 259,973 | 21,113 | 20,431 | 682 | 286 | 224 | 94 | 12.313 | 12.724 | +3.34% | 12 → 12 (+0) |
| Nordrhein-Westfalen | 527,377 | 41,536 | 40,558 | 978 | 301 | 247 | 89 | 12.697 | 13.003 | +2.41% | 13 → 13 (+0) |
| Rheinland-Pfalz | 119,839 | 8,092 | 7,876 | 216 | 70 | 60 | 34 | 14.810 | 15.216 | +2.74% | 15 → 15 (+0) |
| Saarland | 25,038 | 1,519 | 1,511 | 8 | 0 | 0 | 0 | 16.483 | 16.570 | +0.53% | 16 → 16 (+0) |
| Sachsen | 56,074 | 7,223 | 7,088 | 135 | 70 | 66 | 26 | 7.763 | 7.911 | +1.90% | 6 → 6 (+0) |
| Sachsen-Anhalt | 29,116 | 3,785 | 3,728 | 57 | 21 | 16 | 4 | 7.692 | 7.810 | +1.53% | 4 → 4 (+0) |
| Schleswig-Holstein | 87,627 | 8,120 | 7,897 | 223 | 95 | 83 | 26 | 10.792 | 11.096 | +2.82% | 10 → 10 (+0) |
| Thüringen | 32,026 | 4,255 | 4,157 | 98 | 54 | 42 | 18 | 7.527 | 7.704 | +2.36% | 3 → 3 (+0) |

Differences in the table are **published September minus survivor cohort** for counts and **survivor minus published** for ratios. The survivor cohort removes 4,888 point rows nationally, including 1,714 fast, 1,407 >=150 kW and 615 >=350 kW point rows.

## 8. Rankings and outlier stability

| Metric | Published lowest | Survivor lowest | Low stable | Published highest | Survivor highest | High stable |
|---|---|---|---|---|---|---|
| BEVs per charging point | Mecklenburg-Vorpommern (6.73) | Mecklenburg-Vorpommern (7.10) | yes | Saarland (16.48) | Saarland (16.57) | yes |
| Fast points per 1,000 BEVs | Baden-Württemberg (16.95) | Baden-Württemberg (16.57) | yes | Mecklenburg-Vorpommern (58.16) | Mecklenburg-Vorpommern (54.65) | yes |
| >=150 kW points per 1,000 BEVs | Baden-Württemberg (12.24) | Baden-Württemberg (11.95) | yes | Mecklenburg-Vorpommern (47.98) | Mecklenburg-Vorpommern (44.65) | yes |
| >=350 kW points per 1,000 BEVs | Saarland (1.60) | Saarland (1.60) | yes | Mecklenburg-Vorpommern (12.70) | Mecklenburg-Vorpommern (10.63) | yes |
| Fast point share | Hamburg (15.62) | Hamburg (15.92) | yes | Sachsen-Anhalt (39.89) | Sachsen-Anhalt (39.94) | yes |
| >=150 kW point share | Baden-Württemberg (12.77) | Baden-Württemberg (12.62) | yes | Mecklenburg-Vorpommern (32.29) | Mecklenburg-Vorpommern (31.69) | yes |
| >=350 kW point share | Berlin (1.78) | Baden-Württemberg (1.82) | no | Mecklenburg-Vorpommern (8.55) | Mecklenburg-Vorpommern (7.55) | yes |

The BEVs-per-point ranking changes for 0 of 16 states; the fast-points-per-1,000-BEVs ranking changes for 4 of 16 states. Rank stability is empirical descriptive evidence only; it does not establish that the retrospective cohort matches July infrastructure or that the ratio measures adequacy.

Important outlier interpretation: state size, denominator size, register coverage and declared-power composition can drive the extremes. A high or low ratio is not evidence of shortage, surplus, accessibility, demand or quality.

## 9. Sources of retrospective selection bias

- The September source contains only equipment still represented in the September register; equipment removed before September cannot be recovered.
- Equipment commissioning date is equipment-level. The current point table has no individual point activation date, and later point additions or modifications cannot be separated from the equipment row using this snapshot alone.
- September addresses, declared characteristics and status labels are carried into the cohort; they are not historical July observations.
- The after-cutoff share is geographically uneven in absolute counts: Nordrhein-Westfalen and Bayern contribute the largest later point counts, followed by Niedersachsen. This is a distribution finding, not a causal explanation.
- The register is not an exhaustive census of all publicly accessible charging infrastructure, so a cohort within the register cannot measure total public availability.

## 10. Unsupported historical interpretations

The following interpretations are not supported by the current data:

- Treating the September published register as if it were observed on 2026-07-01.
- Calling the survivor cohort a true July snapshot, a guaranteed upper/lower bound, or observed infrastructure growth from July to September.
- Inferring point-level activation, opening date, July operational status, historical opening hours, uptime, queue time, utilization, sessions, energy delivery, or simultaneous deliverable power.
- Interpreting the January/April fixed-denominator illustration as January/April infrastructure. It changes the KBA vehicle numerator while intentionally holding the September denominator fixed.
- Interpreting stock changes as new registrations or sales, or assigning causal explanations to state differences without additional approved evidence.

## 11. Evaluation of candidate Tableau KPIs

The decisions below use the requested statuses `HEADLINE_READY_WITH_DATES`, `CONTEXT_ONLY`, `EXPLORATORY_SENSITIVITY` and `NOT_SUPPORTED`. No cross-source ratio is promoted to a same-day adequacy metric. The observed single-source counts remain valid with their source dates, but that does not transfer to a demand or adequacy interpretation.

| KPI | Status | Temporal validity | Recommended visualization | Required label / key evidence |
|---|---|---|---|---|
| BEVs per registered charging point | CONTEXT_ONLY | Published numerator and denominator are 91 days apart; survivor alternative is not a historical July registry | Secondary contextual KPI/table with both dates, denominator scope, and a warning note; no gauge or adequacy threshold | CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — KBA stock 2026-07-01; BNetzA published snapshot 2026-09-30 (91-day separation); survivor sensitivity, if shown, must use: RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE; equipment commissioned on or before 2026-07-01 with September point rows retained |
| Registered charging points per 1,000 BEVs | CONTEXT_ONLY | Inverse of the date-mismatched BEVs-per-point comparison; survivor denominator is reconstructed, not historical July | Secondary context table only, paired with absolute stock and point counts | CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — KBA stock 2026-07-01; BNetzA published snapshot 2026-09-30 (91-day separation); survivor sensitivity, if shown, must use: RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE; equipment commissioned on or before 2026-07-01 with September point rows retained |
| Fast points per 1,000 BEVs | EXPLORATORY_SENSITIVITY | Cross-snapshot and power-declaration dependent; survivor sensitivity removes later-commissioned point rows but does not reconstruct July operation | Exploratory sensitivity dot plot or table with point counts, dates, and declared-power caveat | CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — KBA stock 2026-07-01; BNetzA published snapshot 2026-09-30 (91-day separation); survivor sensitivity, if shown, must use: RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE; equipment commissioned on or before 2026-07-01 with September point rows retained |
| >=150 kW points per 1,000 BEVs | EXPLORATORY_SENSITIVITY | Cross-snapshot; survivor result is a September survivor cohort, not actual July high-power stock | Exploratory sensitivity table with threshold definition shown in the subtitle | CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — KBA stock 2026-07-01; BNetzA published snapshot 2026-09-30 (91-day separation); survivor sensitivity, if shown, must use: RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE; equipment commissioned on or before 2026-07-01 with September point rows retained |
| >=350 kW points per 1,000 BEVs | EXPLORATORY_SENSITIVITY | Cross-snapshot; survivor result is reconstructed from September records | Exploratory threshold comparison only | CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — KBA stock 2026-07-01; BNetzA published snapshot 2026-09-30 (91-day separation); survivor sensitivity, if shown, must use: RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE; equipment commissioned on or before 2026-07-01 with September point rows retained |
| Combined plug-in vehicles per registered point | CONTEXT_ONLY | Same cross-snapshot limitation; PHEV stock is not charging demand | Context-only table, never a headline adequacy tile | CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — KBA stock 2026-07-01; BNetzA published snapshot 2026-09-30 (91-day separation); survivor sensitivity, if shown, must use: RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE; equipment commissioned on or before 2026-07-01 with September point rows retained |
| BEV-share minus charging-point-share gap | EXPLORATORY_SENSITIVITY | Compositional cross-snapshot comparison; survivor variant changes point shares but is not July observed | Annotated composition chart with zero line and a non-adequacy warning | CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — KBA stock 2026-07-01; BNetzA published snapshot 2026-09-30 (91-day separation); survivor sensitivity, if shown, must use: RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE; equipment commissioned on or before 2026-07-01 with September point rows retained |
| State correlations between EV stock and infrastructure | EXPLORATORY_SENSITIVITY | Cross-sectional and cross-snapshot; survivor re-estimation is sensitivity only | Analyst diagnostic scatter plot, not a dashboard headline | CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — KBA stock 2026-07-01; BNetzA published snapshot 2026-09-30 (91-day separation); survivor sensitivity, if shown, must use: RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE; equipment commissioned on or before 2026-07-01 with September point rows retained |
| Infrastructure adequacy, shortage, or surplus | NOT_SUPPORTED | Not supported | Do not visualize as a KPI | CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — KBA stock 2026-07-01; BNetzA published snapshot 2026-09-30 (91-day separation); survivor sensitivity, if shown, must use: RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE; equipment commissioned on or before 2026-07-01 with September point rows retained |

BEVs-per-point decision: show, if at all, as a **secondary contextual KPI**, with both dates and the 16-state denominator scope exposed. Do not show it as a headline tile, adequacy gauge, service standard or red/green state classification. The survivor comparison belongs in an exploratory sensitivity view.

## 12. Recommended chart labels and warning notes

Recommended published-snapshot label:

> CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — Registered BEVs at 2026-07-01 / BNetzA charging points published at 2026-09-30. Not a same-day infrastructure adequacy measure.

Recommended survivor label:

> RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE. Equipment present in the 2026-09-30 register with commissioning date <= 2026-07-01; current September point rows retained.

Recommended warning note:

> Commissioning date is equipment-level; point activation date and historical availability are unavailable. Counts use point slots, not connector counts. Maximum declared power is a source classification, not utilization or simultaneous deliverable power. KBA values are registered stock, not demand or sales.

## 13. National and regional reconciliation

| Scope | KBA reference | KBA BEV | KBA PHEV | Equipment | Points | BEVs/point | Reconciliation |
|---|---|---|---|---|---|---|---|
| Published Deutschland KBA row | 2026-07-01 | 2,365,047 | 1,226,863 | — | — | — | PASS — includes Sonstige |
| 16-state KBA sum | 2026-07-01 | 2,362,218 | 1,225,241 | — | — | — | PASS — comparable vehicle scope |
| Sonstige KBA row | 2026-07-01 | 2,829 | 1,622 | — | — | — | PASS — residual, not a state |
| 400 KBA registration regions | 2026-07-01 | 2,362,218 | 1,225,241 | — | — | — | PASS — equals 16-state sum |
| Published September infrastructure | — | — | — | 117,662 | 211,253 | 11.181938 | PASS — all 16 states |
| Survivor cohort infrastructure | — | — | — | 114,900 | 206,365 | 11.446796 | PASS — reconstructed sensitivity only |

The July national relationship is exact: Deutschland = 16 named states + Sonstige for passenger cars, BEVs and PHEVs. The 400-region KBA total equals the 16-state sum. The published BNetzA infrastructure total is 117,662 equipment and 211,253 points; the survivor total is kept separate and is never added to the published total.

### Vehicle-stock sensitivity with a fixed September denominator

| KBA date | Scope | BEV stock | Fixed Sep points | BEVs/fixed Sep point | Fixed Sep points/1,000 BEVs |
|---|---|---|---|---|---|
| 2026-01-01 | 16-state sum | 2,031,870 | 211,253 | 9.618183 | 103.969742 |
| 2026-01-01 | published Deutschland | 2,034,260 | 211,253 | 9.629496 | 103.847591 |
| 2026-04-01 | 16-state sum | 2,167,111 | 211,253 | 10.258368 | 97.481393 |
| 2026-04-01 | published Deutschland | 2,169,717 | 211,253 | 10.270704 | 97.364311 |
| 2026-07-01 | 16-state sum | 2,362,218 | 211,253 | 11.181938 | 89.429934 |
| 2026-07-01 | published Deutschland | 2,365,047 | 211,253 | 11.195330 | 89.322961 |

This is a vehicle-numerator sensitivity illustration only. The September point denominator is held fixed to show how KBA stock date changes the ratio; it must not be narrated as observed unchanged infrastructure in January or April.

## 14. Validation evidence

| Check | Result |
|---|---|
| DuckDB access | PASS — opened with read_only=True; no DDL/DML issued |
| Database contract | PASS — 4 required base tables and commissioning/point/KBA columns present |
| Source fingerprints | PASS — 6 preserved workbook/reference fingerprints match |
| BNetzA baseline | PASS — 117,662 equipment; 211,253 points; power bands and 9,215.4173 MW match |
| Commissioning-date parsing | PASS — 0 failures; 0 parsed NULL; 0 future dates |
| Cutoff boundary | PASS — 80 equipment records on 2026-07-01 included; published = survivor + post-cutoff |
| Point integrity | PASS — 0 duplicate point keys; 0 orphan points; 0 equipment/point mismatches |
| Power-band denominator | PASS — 0 invalid-power points; normal + fast + unknown = total |
| KBA dates | PASS — January, April and July each have 18 × 7 state-fuel rows and 400 district rows |
| KBA July reconciliation | PASS — Deutschland = 16 states + Sonstige; 400-region BEV total = 2,362,218 = 16-state total |
| Vehicle denominator | PASS — six mutually exclusive fuel rows form passenger-car total; PHEV remains nested detail |
| State join | PASS — exactly 16 states; one vehicle row and one infrastructure row per state before joining |
| Date labels | PASS — both source dates and both perspective labels are carried into outputs |
| Database immutability | PASS — start/end SHA-256 5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3 |
| Ratio safety | PASS — NULL/zero denominators return blank; no zero denominators in current state rows |

### Source fingerprints

| Path | Bytes | SHA-256 | Result |
|---|---|---|---|
| data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx | 31,722,320 | 1e82c1734b17e17e51092a0f9460a5e204888569fb12aa5940b30e9cdb726342 | MATCH |
| data/raw/kba/fz27_202601.xlsx | 1,474,738 | 29ab2eaa178a1c6a3463d5cad707fee1e762241304ae6bb08c29702d6e6aea31 | MATCH |
| data/raw/kba/fz27_202604.xlsx | 1,482,694 | 28fffaa7d2f21ede6d7f6988a717b749b759a308755c472df4d391c73a0653e7 | MATCH |
| data/raw/kba/fz27_202607.xlsx | 1,478,376 | d6a26702fa6f8358cc5f0e15e88c04ac6c36527be404058674138dd9571bc803 | MATCH |
| data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx | 8,768,335 | 083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525 | MATCH |
| data/reference/bnetza_kba_district_crosswalk_2026.csv | 202,069 | fdf139c5057250184358e3014267a4a4c4259749113273f6bd48206f6a64fe6a | MATCH |

## 15. Recommended next analytical step

If the owner wants a stronger temporal KPI, obtain or approve a genuinely dated infrastructure panel with historical point/equipment identity, activation/retirement semantics and operational availability fields, then pair it with a compatible KBA stock date. Until then, keep the published cross-snapshot comparison contextual and the survivor cohort exploratory. Do not begin Tableau development or Batch 18 without owner approval.

## Reproducible outputs

- [`scripts/17_analyze_temporal_kpi_validity.py`](../scripts/17_analyze_temporal_kpi_validity.py)
- [`batch17_temporal_kpi_validity.md`](batch17_temporal_kpi_validity.md)
- [`batch17_equipment_commissioning_cohorts.csv`](batch17_equipment_commissioning_cohorts.csv)
- [`batch17_state_temporal_sensitivity.csv`](batch17_state_temporal_sensitivity.csv)
- [`batch17_kpi_publication_decisions.csv`](batch17_kpi_publication_decisions.csv)
- [`batch17_vehicle_stock_denominator_sensitivity.csv`](batch17_vehicle_stock_denominator_sensitivity.csv)

Run from the repository root:

```bash
.venv/bin/python scripts/17_analyze_temporal_kpi_validity.py --json
```
