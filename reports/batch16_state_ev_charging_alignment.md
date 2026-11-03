# Batch 16 — state-level EV stock versus charging infrastructure

**Batch status: PASS**

This report is a deterministic, read-only comparison of the 16 German federal states. It uses KBA FZ 27.2 passenger-car stock as of **2026-07-01** and the BNetzA Ladesäulenregister as of **2026-09-30**. The dates are intentionally visible because every cross-source KPI is a date-mismatched descriptive comparison.

## 1. Executive summary

**OBSERVED:** The BNetzA snapshot contains 117,662 registered equipment records and 211,253 populated charging-point slots across the 16 states. The declared-power parser classifies 156,155 points at or below 22 kW, 55,098 above 22 kW, 40,950 at or above 150 kW, and 6,950 at or above 350 kW. Declared equipment nominal power is 9,215.4173 MW.

Equipment statuses are preserved without filtering: 117,642 records are `In Betrieb`, 20 are `In Wartung`, and 0 have another or NULL status.

**OBSERVED:** The July KBA state-level total is 2,365,047 BEVs, 1,226,863 PHEVs, and 49,696,710 passenger cars. The 16 states contain 2,362,218 BEVs and 1,225,241 PHEVs; `Sonstige` contains 2,829 BEVs and 1,622 PHEVs. The 400 KBA registration-region totals equal the 16-state sums.

**OBSERVED:** The primary 16-state benchmark is 11.18 registered BEVs per registered charging point, or 89.43 points per 1,000 BEVs. Using the published `Deutschland` BEV numerator instead gives 11.20 BEVs per point because it includes 2,829 `Sonstige` BEVs without adding an infrastructure row.

**OBSERVED:** Nordrhein-Westfalen has the largest absolute BEV stock (527,377); Hamburg has the highest BEV penetration (5.97%); and Nordrhein-Westfalen has the largest point stock (41,536). Sachsen-Anhalt has the highest fast-point share (39.89%), while Mecklenburg-Vorpommern has the highest >=150 kW point share (32.29%).

These are descriptive counts, shares and ratios. They do not establish infrastructure adequacy, shortage, surplus, demand, utilization, accessibility, or causality.

## 2. Review of Batch 15 findings relevant to Batch 16

Batch 15 established a compatible KBA baseline rather than a blocker for this state-level comparison:

- **National stock:** January–July 2026 national BEV stock increased by 330,787 (16.26%) to 2,365,047; PHEV stock increased by 103,905 (9.25%) to 1,226,863. The national combined plug-in share reached 7.23%.
- **Regional stock:** Nordrhein-Westfalen had the largest July BEV stock (527,377); Hamburg had the highest BEV penetration (5.97%); Mecklenburg-Vorpommern had the highest January–July state BEV growth (20.98%). These rankings distinguish absolute scale from percentage indicators.
- **Ownership:** Batch 15 found that private ownership represented 61.49% of observed-owner BEV stock and 54.31% of observed-owner PHEV stock nationally in July. Published totals retain unknown or unallocated owner residuals; district ownership was not inferred.
- **Completeness and limits:** FZ 27.15 contains 400 stable KBA registration-region codes per snapshot and the 16-state sum reconciles to the 400-region table. The `Deutschland` row includes `Sonstige`; it must not be added to the state or district rows. The shared Trier registration region `07211` remains one row, with no allocation.
- **Validated versus exploratory:** Batch 15 validated stock, penetration, same-grain reconciliation and source-grain ownership arithmetic. Percentage-growth thresholds, ownership composition and alternative postcode/municipality analyses remain descriptive or exploratory. No BNetzA charging join was present in Batch 15, so this batch performs that cross-source comparison with both dates explicit.

The residual and grain differences are manageable because Batch 16 keeps `Deutschland`, the 16 states, `Sonstige`, and the 400 KBA registration-region scope separate. No BBSR integration or district crosswalk is needed for this batch.

## 3. Data sources and analytical grain

| Source/object | Use | Grain | Reference date | Controls |
|---|---|---|---|---|
| `core.kba_state_fuel_stock` | BEV, PHEV and passenger-car stock | FZ 27.2 state/residual/national × fuel type | 2026-07-01 | Six mutually exclusive fuel rows form passenger-car total; `darunter Plug-in` is nested detail. |
| `core.kba_district_ev_stock` | Independent KBA reconciliation | 400 KBA registration regions | 2026-07-01 | One row per code; no BBSR equivalence or Trier allocation. |
| `analytics.charging_by_state` | Validated equipment/declared/populated point baseline | 16 federal states | 2026-09-30 | Existing source-aware `(source_id, excel_row)` point join. |
| `core.charging_equipment` | Equipment, status and nominal power | BNetzA equipment row × state | 2026-09-30 | Equipment power summed before any point-level aggregation. |
| `core.charging_point` | Point counts and power bands | Populated point slot × equipment | 2026-09-30 | Maximum parsed token per point; no connector multiplication. |

The primary join is one validated charging row per state joined to one validated KBA stock row per state. Raw equipment, raw points and KBA fuel rows are not joined together before aggregation.

## 4. National and 16-state reconciliation

| Scope | Passenger cars | BEV | PHEV | Equipment | Points | BEVs/point | Interpretation |
|---|---|---|---|---|---|---|---|
| Published KBA `Deutschland` | 49,696,710 | 2,365,047 | 1,226,863 | — | — | — | Official national KBA row. |
| 16-state KBA sum | 49,644,855 | 2,362,218 | 1,225,241 | — | — | — | Comparable vehicle scope for the state infrastructure rows. |
| KBA `Sonstige` | 51,855 | 2,829 | 1,622 | — | — | — | Residual reporting category; not a state. |
| 400 KBA regions | 49,644,855 | 2,362,218 | 1,225,241 | — | — | — | Matches the 16-state sum exactly. |
| BNetzA all 16 states | — | — | — | 117,662 | 211,253 | — | All registered infrastructure in the current state view. |
| 16-state comparable benchmark | — | 2,362,218 | — | 117,662 | 211,253 | 11.18 | Use for state-ratio recomputation from summed numerators/denominators. |
| Published-national benchmark | — | 2,365,047 | — | 117,662 | 211,253 | 11.20 | Includes `Sonstige` BEVs but no separate infrastructure row. |

The reconciliation is exact: `Deutschland = 16 states + Sonstige` for passenger cars, BEVs and PHEVs; the 400-region KBA total equals the 16-state sum; and the BNetzA state totals equal 117,662 equipment, 211,253 declared points, 211,253 populated points and 9,215.4173 MW. `Deutschland` and `Sonstige` are reporting rows, not additional independent federal states.

The two national benchmarks differ only in the KBA numerator scope here: the published-national numerator includes 2,829 `Sonstige` BEVs. A national BEV total must not be compared with a sum or average of state-level ratios without first choosing the scope and recomputing from summed counts. State-level BEV-per-point ratios were not averaged to obtain either benchmark.

## 5. Complete 16-state KPI comparison

### Vehicle stock and penetration

| State | Passenger cars | BEV | PHEV | BEV penetration | PHEV penetration | Combined penetration | BEV share of 16-state stock |
|---|---|---|---|---|---|---|---|
| Baden-Württemberg | 7,015,759 | 369,574 | 193,186 | 5.27% | 2.75% | 8.02% | 15.65% |
| Bayern | 8,527,085 | 459,811 | 211,656 | 5.39% | 2.48% | 7.87% | 19.47% |
| Berlin | 1,219,191 | 54,437 | 34,743 | 4.47% | 2.85% | 7.31% | 2.30% |
| Brandenburg | 1,507,218 | 49,103 | 29,791 | 3.26% | 1.98% | 5.23% | 2.08% |
| Bremen | 302,050 | 12,394 | 7,874 | 4.10% | 2.61% | 6.71% | 0.52% |
| Hamburg | 829,662 | 49,560 | 34,970 | 5.97% | 4.21% | 10.19% | 2.10% |
| Hessen | 3,937,917 | 208,073 | 113,707 | 5.28% | 2.89% | 8.17% | 8.81% |
| Mecklenburg-Vorpommern | 893,769 | 22,196 | 14,387 | 2.48% | 1.61% | 4.09% | 0.94% |
| Niedersachsen | 5,025,325 | 259,973 | 115,578 | 5.17% | 2.30% | 7.47% | 11.01% |
| Nordrhein-Westfalen | 10,694,681 | 527,377 | 279,299 | 4.93% | 2.61% | 7.54% | 22.33% |
| Rheinland-Pfalz | 2,664,247 | 119,839 | 58,454 | 4.50% | 2.19% | 6.69% | 5.07% |
| Saarland | 654,875 | 25,038 | 14,445 | 3.82% | 2.21% | 6.03% | 1.06% |
| Sachsen | 2,192,631 | 56,074 | 38,028 | 2.56% | 1.73% | 4.29% | 2.37% |
| Sachsen-Anhalt | 1,223,353 | 29,116 | 20,609 | 2.38% | 1.68% | 4.06% | 1.23% |
| Schleswig-Holstein | 1,765,770 | 87,627 | 37,704 | 4.96% | 2.14% | 7.10% | 3.71% |
| Thüringen | 1,191,322 | 32,026 | 20,810 | 2.69% | 1.75% | 4.44% | 1.36% |

### Infrastructure stock and power mix

| State | Equipment | Declared points | Populated points | Normal <=22 kW | Fast >22 kW | Fast share | >=150 kW | >=150 share | >=350 kW | >=350 share | Nominal MW | Point share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Baden-Württemberg | 19,018 | 35,437 | 35,437 | 29,173 | 6,264 | 17.68% | 4,525 | 12.77% | 689 | 1.94% | 1,210.8217 | 16.77% |
| Bayern | 23,063 | 40,215 | 40,215 | 29,725 | 10,490 | 26.08% | 7,694 | 19.13% | 1,327 | 3.30% | 1,809.0598 | 19.04% |
| Berlin | 4,999 | 7,644 | 7,644 | 6,388 | 1,256 | 16.43% | 1,000 | 13.08% | 136 | 1.78% | 215.4151 | 3.62% |
| Brandenburg | 3,050 | 5,035 | 5,035 | 3,283 | 1,752 | 34.80% | 1,340 | 26.61% | 220 | 4.37% | 280.1840 | 2.38% |
| Bremen | 892 | 1,600 | 1,600 | 1,253 | 347 | 21.69% | 219 | 13.69% | 32 | 2.00% | 54.2770 | 0.76% |
| Hamburg | 3,419 | 6,141 | 6,141 | 5,182 | 959 | 15.62% | 850 | 13.84% | 119 | 1.94% | 212.4597 | 2.91% |
| Hessen | 9,040 | 16,240 | 16,240 | 11,872 | 4,368 | 26.90% | 3,456 | 21.28% | 510 | 3.14% | 753.9857 | 7.69% |
| Mecklenburg-Vorpommern | 1,875 | 3,298 | 3,298 | 2,007 | 1,291 | 39.14% | 1,065 | 32.29% | 282 | 8.55% | 206.6743 | 1.56% |
| Niedersachsen | 11,654 | 21,113 | 21,113 | 14,306 | 6,807 | 32.24% | 4,873 | 23.08% | 985 | 4.67% | 1,052.2322 | 9.99% |
| Nordrhein-Westfalen | 22,666 | 41,536 | 41,536 | 31,230 | 10,306 | 24.81% | 7,432 | 17.89% | 1,212 | 2.92% | 1,715.7311 | 19.66% |
| Rheinland-Pfalz | 4,572 | 8,092 | 8,092 | 5,050 | 3,042 | 37.59% | 2,316 | 28.62% | 387 | 4.78% | 458.1144 | 3.83% |
| Saarland | 801 | 1,519 | 1,519 | 1,053 | 466 | 30.68% | 362 | 23.83% | 40 | 2.63% | 68.4864 | 0.72% |
| Sachsen | 3,875 | 7,223 | 7,223 | 4,960 | 2,263 | 31.33% | 1,658 | 22.95% | 262 | 3.63% | 327.5152 | 3.42% |
| Sachsen-Anhalt | 2,001 | 3,785 | 3,785 | 2,275 | 1,510 | 39.89% | 1,145 | 30.25% | 160 | 4.23% | 225.6321 | 1.79% |
| Schleswig-Holstein | 4,395 | 8,120 | 8,120 | 5,812 | 2,308 | 28.42% | 1,710 | 21.06% | 364 | 4.48% | 379.3258 | 3.84% |
| Thüringen | 2,342 | 4,255 | 4,255 | 2,586 | 1,669 | 39.22% | 1,305 | 30.67% | 225 | 5.29% | 245.5028 | 2.01% |

### Cross-dataset indicators

| State | BEVs/point | Points/1,000 BEVs | Fast/1,000 BEVs | >=150/1,000 BEVs | >=350/1,000 BEVs | BEV share − point share | BEV+PHEV/point |
|---|---|---|---|---|---|---|---|
| Baden-Württemberg | 10.43 | 95.89 | 16.95 | 12.24 | 1.86 | -1.13 pp | 15.88 |
| Bayern | 11.43 | 87.46 | 22.81 | 16.73 | 2.89 | +0.43 pp | 16.70 |
| Berlin | 7.12 | 140.42 | 23.07 | 18.37 | 2.50 | -1.31 pp | 11.67 |
| Brandenburg | 9.75 | 102.54 | 35.68 | 27.29 | 4.48 | -0.30 pp | 15.67 |
| Bremen | 7.75 | 129.09 | 28.00 | 17.67 | 2.58 | -0.23 pp | 12.67 |
| Hamburg | 8.07 | 123.91 | 19.35 | 17.15 | 2.40 | -0.81 pp | 13.76 |
| Hessen | 12.81 | 78.05 | 20.99 | 16.61 | 2.45 | +1.12 pp | 19.81 |
| Mecklenburg-Vorpommern | 6.73 | 148.59 | 58.16 | 47.98 | 12.70 | -0.62 pp | 11.09 |
| Niedersachsen | 12.31 | 81.21 | 26.18 | 18.74 | 3.79 | +1.01 pp | 17.79 |
| Nordrhein-Westfalen | 12.70 | 78.76 | 19.54 | 14.09 | 2.30 | +2.66 pp | 19.42 |
| Rheinland-Pfalz | 14.81 | 67.52 | 25.38 | 19.33 | 3.23 | +1.24 pp | 22.03 |
| Saarland | 16.48 | 60.67 | 18.61 | 14.46 | 1.60 | +0.34 pp | 25.99 |
| Sachsen | 7.76 | 128.81 | 40.36 | 29.57 | 4.67 | -1.05 pp | 13.03 |
| Sachsen-Anhalt | 7.69 | 130.00 | 51.86 | 39.33 | 5.50 | -0.56 pp | 13.14 |
| Schleswig-Holstein | 10.79 | 92.67 | 26.34 | 19.51 | 4.15 | -0.13 pp | 15.43 |
| Thüringen | 7.53 | 132.86 | 52.11 | 40.75 | 7.03 | -0.66 pp | 12.42 |

The BEV-only ratios use July 2026 registered BEVs as the denominator. The optional combined plug-in ratio uses BEV + PHEV in the numerator and is not mixed into the BEV-only rankings. All ratio calculations use safe zero-denominator handling; no state has a zero BEV or point denominator in this snapshot.

## 6. BEV stock versus charging-point comparison

State size and state share are different views. The following states have the largest absolute BEV stock and charging-point stock:

| Rank | State | BEVs | BEV penetration | Points | Point share | BEVs/point | Share gap |
|---|---|---|---|---|---|---|---|
| 1 | Nordrhein-Westfalen | 527,377 | 4.93% | 41,536 | 19.66% | 12.70 | +2.66 pp |
| 2 | Bayern | 459,811 | 5.39% | 40,215 | 19.04% | 11.43 | +0.43 pp |
| 3 | Baden-Württemberg | 369,574 | 5.27% | 35,437 | 16.77% | 10.43 | -1.13 pp |
| 4 | Niedersachsen | 259,973 | 5.17% | 21,113 | 9.99% | 12.31 | +1.01 pp |
| 5 | Hessen | 208,073 | 5.28% | 16,240 | 7.69% | 12.81 | +1.12 pp |

A positive share gap means the state's share of 16-state BEVs is larger than its share of registered points; a negative gap means the reverse. This is a compositional comparison, not a shortage/surplus measure.

## 7. Fast and HPC infrastructure comparison

| Metric | State | Underlying BEVs | Passenger cars | Points | Fast points | >=150 kW points | >=350 kW points | Reported value |
|---|---|---|---|---|---|---|---|---|
| Largest point stock | Nordrhein-Westfalen | 527,377 | 10,694,681 | 41,536 | 10,306 | 7,432 | 1,212 | 41,536 |
| Highest fast-point share | Sachsen-Anhalt | 29,116 | 1,223,353 | 3,785 | 1,510 | 1,145 | 160 | 39.89% |
| Highest >=150 kW share | Mecklenburg-Vorpommern | 22,196 | 893,769 | 3,298 | 1,291 | 1,065 | 282 | 32.29% |

Fast and >=150 kW are nested declared-power classifications. A higher fast or HPC share does not show that points are available, used, reliable, simultaneously deliverable, or suitable for every vehicle.

## 8. Geographic differences, outliers and denominator stability

| Comparison | State | Underlying counts | Value |
|---|---|---|---|
| Largest absolute BEV stock | Nordrhein-Westfalen | 527,377 BEVs; 10,694,681 passenger cars | 527,377 |
| Highest BEV penetration | Hamburg | 49,560 BEVs / 829,662 passenger cars | 5.97% |
| Lowest BEVs per point | Mecklenburg-Vorpommern | 22,196 BEVs / 3,298 points | 6.73 |
| Highest BEVs per point | Saarland | 25,038 BEVs / 1,519 points | 16.48 |
| Lowest fast points per 1,000 BEVs | Baden-Württemberg | 6,264 fast points / 369,574 BEVs | 16.95 |
| Highest fast points per 1,000 BEVs | Mecklenburg-Vorpommern | 1,291 fast points / 22,196 BEVs | 58.16 |

### Largest BEV-share versus charging-point-share differences

| Rank | State | BEV stock | Points | BEV share of 16-state stock | Point share | Difference |
|---|---|---|---|---|---|---|
| 1 | Nordrhein-Westfalen | 527,377 | 41,536 | 22.33% | 19.66% | +2.66 pp |
| 2 | Berlin | 54,437 | 7,644 | 2.30% | 3.62% | -1.31 pp |
| 3 | Rheinland-Pfalz | 119,839 | 8,092 | 5.07% | 3.83% | +1.24 pp |
| 4 | Baden-Württemberg | 369,574 | 35,437 | 15.65% | 16.77% | -1.13 pp |
| 5 | Hessen | 208,073 | 16,240 | 8.81% | 7.69% | +1.12 pp |

### Small point denominators

| State | Points | BEVs | Fast points | BEVs/point | Fast/1,000 BEVs | Interpretation |
|---|---|---|---|---|---|---|
| Saarland | 1,519 | 25,038 | 466 | 16.48 | 18.61 | Small denominator; inspect counts with the ratio |
| Bremen | 1,600 | 12,394 | 347 | 7.75 | 28.00 | Small denominator; inspect counts with the ratio |
| Mecklenburg-Vorpommern | 3,298 | 22,196 | 1,291 | 6.73 | 58.16 | Small denominator; inspect counts with the ratio |
| Sachsen-Anhalt | 3,785 | 29,116 | 1,510 | 7.69 | 51.86 | Small denominator; inspect counts with the ratio |
| Thüringen | 4,255 | 32,026 | 1,669 | 7.53 | 52.11 | Small denominator; inspect counts with the ratio |

Small state point counts make shares and per-1,000 ratios more sensitive to a small number of points. That is a stability warning, not evidence that a state is adequately or inadequately supplied. State averages also conceal urban/rural and district-level variation.

## 9. Statistical associations

The following Pearson and Spearman correlations are descriptive summaries of 16 states. No p-values or significance claims are used. The sensitivity columns exclude the three states with the largest passenger-car stock (Nordrhein-Westfalen, Bayern and Baden-Württemberg); leave-one-out ranges show how much one state can affect the result.

| Association | n | Pearson | Spearman | Pearson excl. 3 large | Spearman excl. 3 large | Leave-one-out Pearson | Interpretation |
|---|---|---|---|---|---|---|---|
| BEV stock vs total charging points | 16 | 0.991 | 0.985 | 0.977 | 0.973 | 0.989 to 0.994 | Absolute-size association can be driven by state scale and does not measure charger adequacy. |
| BEV penetration vs fast-point share | 16 | -0.715 | -0.688 | -0.681 | -0.692 | -0.766 to -0.656 | Ratio-versus-ratio association; denominators and declared-power mix can drive the pattern. |
| BEV stock share vs charging-point share | 16 | 0.991 | 0.985 | 0.977 | 0.973 | 0.989 to 0.994 | Compositional comparison with fixed national denominators; closely related to absolute scale. |
| Total passenger cars vs total charging points | 16 | 0.983 | 0.926 | 0.959 | 0.863 | 0.981 to 0.986 | Absolute-size association can be driven by state scale; it is not a supply or demand test. |
| BEVs per point vs fast-point share | 16 | 0.060 | -0.115 | 0.132 | -0.170 | -0.065 to 0.185 | Exploratory denominator-driven comparison; both dates and source coverage limitations matter. |

**SUPPORTED ASSOCIATION:** Absolute BEV stock and absolute charging-point count move together descriptively, but the strength of that relationship must be read as a state-size association. The stock-share versus point-share comparison has fixed denominators and is therefore compositional rather than an independent test. Passenger-car stock versus point count has the same scale effect. Penetration, BEVs-per-point and fast-share correlations compare ratios with different denominators and should not be treated as causal drivers.

**PLAUSIBLE HYPOTHESIS:** State size, urban form, fleet composition, public-sector or commercial siting and travel patterns could contribute to the observed differences. The available 16-state cross-section cannot identify which mechanism explains them.

## 10. Limitations and interpretation safeguards

- **OBSERVED:** KBA registered passenger-car stock and BNetzA registered charging infrastructure reconcile at their respective source grains and reference dates.
- **SUPPORTED ASSOCIATION:** Correlations describe co-movement across 16 states only; they do not establish a causal driver or statistical generalization.
- **PLAUSIBLE HYPOTHESIS:** Large states can dominate absolute totals, while denominators and composition can change ratios and shares. This is a reason to report both counts and normalized measures.
- **NOT TESTABLE WITH AVAILABLE DATA:** Charging demand, sessions, utilization, queues, reliability, real-time availability, traffic flow, energy delivery, population-adjusted need, accessibility, and causal infrastructure effects.

Additional safeguards:

- BNetzA infrastructure is dated 2026-09-30 and KBA stock is dated 2026-07-01. The cross-source KPIs are not contemporaneous.
- The BNetzA register is a published register, not a complete census of every public charging asset.
- BEV stock is registered stock, not charging demand, sales or registrations during the interval.
- One charging point does not imply a fixed amount of simultaneous usable power; nominal equipment power is not simultaneously deliverable power.
- The KBA state table uses passenger-car counts. PHEV is not added to `Hybrid insgesamt` when reconstructing total passenger cars.
- State comparisons are not district-level geographic harmonization. No BBSR classification, Trier allocation or KBA district crosswalk is used here.
- January/April/July KBA trends from Batch 15 are background only. This report does not repeat September infrastructure across those dates to claim infrastructure growth.

## 11. KPI evaluation for Tableau

The statuses below apply to the state-level candidate KPI as used in this batch. `VALIDATED` means the source fields, formula, grain and reconciliation passed the local checks; it does not mean the source is exhaustive. Cross-source ratios are `EXPLORATORY` because the snapshot dates differ and the register is not a census.

| KPI | Status | Formula / numerator / denominator | Unit | Source | Grain | Reference dates | Interpretation | Known limitation | Tableau suitability |
|---|---|---|---|---|---|---|---|---|---|
| BEV stock | VALIDATED | SUM `Elektro (BEV)` passenger cars | Registered vehicles | KBA FZ 27.2 / `core.kba_state_fuel_stock` | State | 2026-07-01 | Observed registered BEV stock | Not sales, demand or utilization | Recommended primary KPI |
| PHEV stock | VALIDATED | SUM `darunter Plug-in` passenger cars | Registered vehicles | KBA FZ 27.2 / `core.kba_state_fuel_stock` | State | 2026-07-01 | Observed registered PHEV stock | Nested detail under Hybrid insgesamt | Recommended supporting KPI |
| Total passenger cars | VALIDATED | Sum six mutually exclusive FZ 27.2 fuel rows | Registered vehicles | KBA FZ 27.2 / `core.kba_state_fuel_stock` | State | 2026-07-01 | Denominator for penetration | Must not add PHEV to Hybrid insgesamt | Recommended denominator |
| BEV penetration | VALIDATED | BEV stock / total passenger cars | % | KBA FZ 27.2 | State | 2026-07-01 | BEV share of registered passenger cars | Stock share, not demand | Recommended primary KPI |
| PHEV penetration | VALIDATED | PHEV stock / total passenger cars | % | KBA FZ 27.2 | State | 2026-07-01 | PHEV share of registered passenger cars | Stock share, not demand | Recommended supporting KPI |
| Combined plug-in penetration | VALIDATED | (BEV + PHEV) / total passenger cars | % | KBA FZ 27.2 | State | 2026-07-01 | Combined mutually exclusive plug-in stock share | Do not substitute Hybrid insgesamt | Recommended supporting KPI |
| Charging equipment count | VALIDATED | COUNT equipment rows | Equipment records | BNetzA / `core.charging_equipment` | State | 2026-09-30 | Published equipment stock | One equipment row may contain multiple points; register not exhaustive | Recommended context KPI |
| Charging-point count | VALIDATED | COUNT populated point slots | Point slots | BNetzA / `core.charging_point` | State | 2026-09-30 | Published point-slot stock | Not connector count, capacity or availability | Recommended primary infrastructure KPI |
| Fast and HPC counts/shares | VALIDATED | Point count by max declared power: >22, >=150, >=350 kW; denominator all points | Points / % | BNetzA / `connector_power_raw` | State | 2026-09-30 | Declared-power mix | Not utilization or simultaneous delivery | Recommended mix KPI with definitions visible |
| Nominal equipment power | VALIDATED | SUM equipment nominal kW / 1,000 | MW | BNetzA / `core.charging_equipment` | State | 2026-09-30 | Declared equipment nominal power | Not energy delivery or grid capacity | Context only |
| BEVs per registered point | EXPLORATORY | BEV stock / populated charging points | BEVs per point | KBA + BNetzA | State | KBA 2026-07-01; BNetzA 2026-09-30 | Date-mismatched stock-to-register ratio | Register coverage and dates differ; not adequacy/accessibility | Use only as clearly labelled exploratory view |
| Points per 1,000 BEVs | EXPLORATORY | Populated points × 1,000 / BEV stock | Points per 1,000 BEVs | KBA + BNetzA | State | KBA 2026-07-01; BNetzA 2026-09-30 | Inverse date-mismatched ratio | Not a service standard or adequacy measure | Exploratory context only |
| Fast/HPC points per 1,000 BEVs | EXPLORATORY | Fast or threshold points × 1,000 / BEV stock | Points per 1,000 BEVs | KBA + BNetzA | State | KBA 2026-07-01; BNetzA 2026-09-30 | Power-mix ratio relative to registered BEVs | Denominator/date/register limitations | Exploratory context only |
| BEV-share minus point-share gap | EXPLORATORY | BEV share of 16-state stock − point share of registered points | Percentage points | KBA + BNetzA | State | KBA 2026-07-01; BNetzA 2026-09-30 | Compositional allocation difference | Not a shortage/surplus indicator | Useful comparison annotation, not standalone KPI |
| State correlations | EXPLORATORY | Pearson/Spearman across 16 state rows | Correlation coefficient | KBA + BNetzA | 16-state cross-section | KBA 2026-07-01; BNetzA 2026-09-30 | Descriptive association | Small n, scale/denominator effects, no causality | Analyst diagnostic; not a headline tile |
| Adequacy, shortage or surplus | UNSUPPORTED | No defensible numerator/denominator from current sources | Not defined | No sessions, demand, availability or service standard | Not supported | Not supported | Cannot be measured here | Requires new approved data and a standard | Do not deploy |

Recommended concise Tableau set: state BEV stock, total passenger cars, BEV penetration, registered charging points, fast-point share/count, >=150 kW count/share and nominal MW as context. If cross-source ratios are shown, expose both reference dates and label them exploratory; do not label any state adequately or inadequately supplied from these ratios alone.

## 12. Future analytical opportunities

- Obtain a contemporaneous BNetzA/KBA pair or construct a dated infrastructure panel before presenting temporal coverage trends.
- Add an owner-approved, product-specific geographic bridge only if a compatible KBA administrative geography is required; preserve the no-allocation rule for Trier.
- Evaluate population, employment, traffic, motorway and fleet denominators at compatible dates and geography, with separate validation for each.
- Add charging sessions, energy, availability or utilization data before discussing demand or access.
- Revisit Tableau extracts only after the denominator/date and source-licensing review is complete.

Batch 17 and any Tableau dashboard implementation remain outside this batch and require owner approval.

## 13. Validation results

| Check | Result |
|---|---|
| DuckDB access | PASS — opened with `read_only=True`; no DDL/DML issued |
| Database object/schema contract | PASS — 5 required objects and required columns present |
| Source fingerprints | PASS — 6 preserved workbook/reference fingerprints match |
| BNetzA baseline reconciliation | PASS — 117,662 equipment; 211,253 points; power bands and 9,215.4173 MW match |
| KBA state coverage | PASS — 16 states × 7 July FZ 27.2 rows; no duplicate or missing state/fuel keys |
| KBA national/residual reconciliation | PASS — Deutschland = 16 states + Sonstige for passenger cars, BEVs and PHEVs |
| KBA 400-region reconciliation | PASS — 400 unique KBA codes and totals equal the 16-state sum |
| Vehicle category handling | PASS — passenger-car total uses six mutually exclusive rows; PHEV is not double-counted in Hybrid insgesamt |
| Charging point integrity | PASS — 0 duplicate point identities; 0 orphan points; 0 equipment mismatches |
| Power-band denominator | PASS — 0 points without valid parsed maximum; normal + fast + unknown = total |
| State join | PASS — exactly 16 distinct states; no missing or duplicated state joins |
| Date safeguard | PASS — every combined KPI carries KBA 2026-07-01 and BNetzA 2026-09-30 |
| Database byte check | PASS — start/end SHA-256 match (5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3) |
| Ratio safety | PASS — NULLIF-equivalent handling; no zero BEV or charging-point denominator |
| Determinism | PASS — script writes no run timestamp and was checked for identical second-run outputs during Batch 16 validation |

### Source fingerprints

| Path | Bytes | SHA-256 | Result |
|---|---|---|---|
| data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx | 31,722,320 | 1e82c1734b17e17e51092a0f9460a5e204888569fb12aa5940b30e9cdb726342 | MATCH |
| data/raw/kba/fz27_202601.xlsx | 1,474,738 | 29ab2eaa178a1c6a3463d5cad707fee1e762241304ae6bb08c29702d6e6aea31 | MATCH |
| data/raw/kba/fz27_202604.xlsx | 1,482,694 | 28fffaa7d2f21ede6d7f6988a717b749b759a308755c472df4d391c73a0653e7 | MATCH |
| data/raw/kba/fz27_202607.xlsx | 1,478,376 | d6a26702fa6f8358cc5f0e15e88c04ac6c36527be404058674138dd9571bc803 | MATCH |
| data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx | 8,768,335 | 083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525 | MATCH |
| data/reference/bnetza_kba_district_crosswalk_2026.csv | 202,069 | fdf139c5057250184358e3014267a4a4c4259749113273f6bd48206f6a64fe6a | MATCH |

## 14. Reproducible outputs and recommended next step

- [`scripts/16_analyze_state_ev_charging_alignment.py`](../scripts/16_analyze_state_ev_charging_alignment.py)
- [`batch16_state_comparison.csv`](batch16_state_comparison.csv)
- [`batch16_national_reconciliation.csv`](batch16_national_reconciliation.csv)
- [`batch16_state_associations.csv`](batch16_state_associations.csv)

Run from the repository root:

```bash
.venv/bin/python scripts/16_analyze_state_ev_charging_alignment.py --json
```

The recommended next step is owner review of the state-level denominator and date treatment, followed by a decision on whether a same-date infrastructure panel or a product-specific geographic bridge is worth pursuing. Do not treat the current ratios as adequacy measures and do not begin Tableau implementation until those choices are approved.
