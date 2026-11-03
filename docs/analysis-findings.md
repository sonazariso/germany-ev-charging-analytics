# Analysis findings

This document records findings supported by the current local database and validation artifacts. It separates descriptive results from exploratory comparisons and does not infer causality.

## Verified descriptive findings

### Published charging infrastructure

- The 2026-09-30 BNetzA snapshot contains 117,662 normalized equipment records and 211,253 populated charging-point slots.
- The source-declared point count reconciles exactly to the populated point-slot count. This confirms retention for the current snapshot; it does not turn the published register into a census.
- Current equipment statuses are 117,642 In Betrieb and 20 In Wartung.
- Equipment-level type labels contain 86,154 Normalladeeinrichtung rows and 31,508 Schnellladeeinrichtung rows. Point-level power bands are a separate measure.
- Declared equipment nominal power sums to 9,215.42 MW. This is nominal source power, not actual energy delivery.

### Point-level declared power

Using the retained connector-power text and classifying each point once by the maximum numeric token:

| Measure | Point slots | Share of 211,253 |
|---|---:|---:|
| Maximum declared power <=22 kW | 156,155 | 73.92% |
| Maximum declared power >22 kW | 55,098 | 26.08% |
| Maximum declared power >=150 kW | 40,950 | 19.38% |
| Maximum declared power >=350 kW | 6,950 | 3.29% |

The parser keeps semicolon-separated power entries inside the point row. It does not treat a multi-value string as multiple points or as simultaneous power.

### Registered vehicle stock

For the 400-code district table:

| KBA reference date | Passenger cars | BEVs | PHEVs | BEV share |
|---|---:|---:|---:|---:|
| 2026-01-01 | 49,436,020 | 2,031,870 | 1,121,516 | 4.11% |
| 2026-04-01 | 49,494,647 | 2,167,111 | 1,165,933 | 4.38% |
| 2026-07-01 | 49,644,855 | 2,362,218 | 1,225,241 | 4.76% |

The district BEV stock increased by 330,348, or 16.26%, from January to July. This is a stock change between snapshots, not new vehicle sales.

The state-level KBA FZ 27.2 row labelled Deutschland reports 2,365,047 BEVs and 1,226,863 plug-in hybrids on 2026-07-01. That national row is a different reporting structure from the 400 district rows and is not substituted into the district join.

### State-level descriptive patterns

- The largest point-slot counts are in Nordrhein-Westfalen (41,536), Bayern (40,215), and Baden-Württemberg (35,437).
- The largest absolute district-table BEV stock increases from January to July are in Nordrhein-Westfalen (+72,595), Bayern (+64,540), and Baden-Württemberg (+47,514).
- The highest relative BEV growth in the 400-district state aggregation is Mecklenburg-Vorpommern (+20.98%), followed by Sachsen-Anhalt (+20.08%). Berlin is lowest in this snapshot comparison (+11.35%).

These rankings describe the observed source aggregates. They do not indicate that infrastructure caused vehicle-stock changes or that a lower count means poor infrastructure.

## Geographic verification findings

- The 22 explicit aliases have direct row-level five-digit key evidence against the dated Destatis Kreis components and local KBA FZ 27.15 rows. This is not a universal KBA-to-AGS/ARS equivalence, and all 22 remain operationally provisional.
- Hanau and Main-Kinzig-Kreis are separate in the 2026-09-30 BNetzA source and in KBA FZ 27.15 on 2026-01-01, 2026-04-01, and 2026-07-01. No current 2026 coverage mismatch was measured.
- Trier remains one combined KBA registration region. The July `07211 TRIER-SAARBURG` stock is 7,869 BEVs and is counted once after the two BNetzA source rows are aggregated to KBA code.
- The 400-region model is defensible for the current KBA registration-region grain, not as proof that all 400 KBA regions are identical to administrative regions. Historical boundary compatibility remains an open note for future time series.

### BBSR feasibility

- The official BBSR 2025 reference contains 400 Kreis rows and 362 Kreisregion
  keys with compact four-class codes 1–4. Smaller independent cities can be
  grouped with associated counties, so the BBSR grain is not automatically the
  KBA registration-region grain.
- A read-only five-digit prefix screen found 399 intersections between the 400
  July 2026 KBA codes and BBSR 2025 Kreis prefixes. KBA `06415` Hanau is absent
  from the 2025 BBSR table, and BBSR `07235` Trier-Saarburg is absent from the
  KBA 400-code table. This is not a validated crosswalk.
- BBSR assigns Trier city and Trier-Saarburg different four-class types while KBA
  combines their stock under `07211`; a future KBA-level category must remain
  mixed/unresolved unless an approved method is introduced.
- Batch 10 implemented the separate BBSR reference layer with 400 Kreis rows and
  362 Kreisregion keys. It remains separate from current BBSR enrichment and does
  not directly classify KBA codes.

## Preliminary exploratory results

The data can support exploratory comparisons of state or KBA-region point-power mix, BEV stock growth, and BEVs per published point. Those comparisons remain provisional because:

- BNetzA infrastructure is dated 2026-09-30 and KBA stock is dated 2026-07-01.
- The BNetzA register is incomplete relative to every publicly accessible charger.
- The 22 aliases and two Trier rows have completed the Batch 08 evidence review, but operational promotion remains owner-controlled and the KBA-versus-AGS/ARS distinction must be retained.
- A point count is not a utilization or energy-delivery measure.
- KBA stock growth is not a sales flow.

The correct exploratory workflow aggregates charging measures to KBA code before joining vehicle stock. The two Trier source rows must not be joined independently to the one 07211 KBA stock row.

## Methodological limitations

- Current data are snapshots, not a full historical infrastructure panel.
- The published register contains source status and commissioning dates but no sessions, energy, uptime, or queue data.
- Connector-power parsing is derived from raw text; the helper column connector_power_kw_single is intentionally incomplete for multi-value strings.
- KBA worksheets contain alternative breakdowns and subtotal rows. Only the approved normalized tables are used for the current findings.
- The existing analytics.charging_by_state view is source-aware after the Batch 06 correction; any future multi-snapshot loading must retain the `(source_id, excel_row)` key.
- One source coordinate is outside a broad Germany bounding check and remains uncorrected.

## Open analytical questions

1. Which owner-approved status vocabulary should be used if any of the 22 row-level-supported aliases are promoted?
2. Should the shared Trier/Trier-Saarburg registration-region treatment be the permanent display geography for every final KPI?
3. Which historical KBA vintages and product-specific boundary notes are required before older comparisons are shown, especially after the Hanau change?
4. Should maximum-per-point power parsing become a reusable approved view or core field?
5. How should the 2,829 Sonstige BEVs and the different national passenger-car totals be presented in the final dashboard?
6. Which BBSR settlement typology, if any, would add value without replacing administrative geography?
7. Which compact Tableau extract can be published while respecting source licensing and field-level disclosure review?

## Batch 13 BBSR charging-only findings

Batch 13 deployed the approved Path A enrichment at the original BNetzA
state/district grain. The result contains 401 districts: 399 verified,
one conditional-vintage Main-Kinzig-Kreis row, and one unresolved Hanau row.
The BBSR settlement type is populated only for the 399 verified rows.

The five reporting groups reconcile to 117,662 equipment records, 211,253
charging points, 156,155 normal points, 55,098 fast points, 40,950 points at
least 150 kW, 6,950 points at least 350 kW, and 9,215.4173 MW of declared
equipment nominal power. The `UNCLASSIFIED` group contains 585 equipment rows
and 991 points. Category point shares use all registered points, including that
unclassified group.

The descriptive category results are not a KBA classification and contain no
BEV/PHEV stock. Hanau does not inherit Main-Kinzig's type; Main-Kinzig's
pre-change BBSR administrative/Kreisregion code is retained without a type.
Trier city and Trier-Saarburg remain separate source rows with types 1 and 3;
their shared KBA vehicle stock is neither joined nor allocated.

## Batch 13.1 owner-approved scenario findings

The official five-row Batch 13 summary remains unchanged as the **OFFICIAL
BBSR 2025 BASELINE**. Batch 13.1 adds the separate **OWNER-APPROVED 2026
ANALYTICAL SCENARIO**. It applies exactly two rows from the versioned override
reference:

- Hanau `06415` is category 1 by `OWNER_APPROVED_SCENARIO`. This is an owner
  assumption, not an official BBSR 2025 or 2026 classification.
- Main-Kinzig-Kreis `06435` is category 2 by
  `HISTORICAL_BBSR_CARRY_FORWARD`, based on official BBSR 2025 type 2 with a
  caveat that Hanau separated in 2026.

Both rows have `official_bbsr_verification = false`. The actual database
contribution is 146 equipment and 251 points for Hanau, and 439 equipment and
740 points for Main-Kinzig-Kreis. Together they move 585 equipment records and
991 points from the official baseline `UNCLASSIFIED` group into categories 1
and 2. The move also transfers 613 normal points, 378 fast points, 327 points
>=150 kW, 77 points >=350 kW, and 63.482 MW of declared nominal equipment
power. No national total changes.

The resulting scenario covers all 401 original BNetzA districts with zero
scenario-unclassified districts. Category district counts are 68, 132, 98,
and 103 for types 1–4. Trier city remains category 1 and Trier-Saarburg
category 3 as separate source rows with 201 and 302 points; no KBA stock is
integrated. The scenario is charging-only and source-grain, not a KBA-level
BBSR integration.

## Batch 13.2 historical BBSR geography finding

The independent 68-versus-67 audit found two distinct causes. First, the
preserved Batch 13 identity logic matched BNetzA `Kreisfreie Stadt Kassel` to
BBSR `06633000 Kassel` (county, type 2) instead of BBSR's official city row
`06611000 Kassel, documenta-Stadt` (type 1). Second, Hanau is a current
independent city that is absent from the BBSR 2025 stand because its separation
from Main-Kinzig-Kreis took effect on `2026-01-01`. Strict and semantic
bidirectional anti-joins make the two effects explicit. The 400 BBSR
`Kreis`/362 `Kreisregion` grain distinction does not explain the missing type-1
row; the 36 multi-district groups are compact-type homogeneous.

The official Hessian boundary law lists Hanau's separation and the remaining
Main-Kinzig municipalities, supporting the historical union of Hanau plus the
remaining current Main-Kinzig row for the former BBSR 2025 target. Batch 13.2
therefore applies the actual BBSR 2025 Main-Kinzig type 2 to the reconstructed
historical target. It does not infer a type for current Hanau in 2026, and
official census-based and municipal-register population numbers are kept as
different context measures rather than used as a classification formula.

The new layer maps 401 current source components to 400 historical BBSR target
units, with target type counts 68 / 131 / 98 / 103. It reconciles to 117,662
equipment, 211,253 points, 156,155 normal points, 55,098 fast points, 40,950
points >=150 kW, 6,950 points >=350 kW, and 9,215.4173 MW. The combined
Hanau/Main-Kinzig target is 585 equipment and 991 points. The official Batch 13
baseline and Batch 13.1 scenario remain separate comparison layers; KBA stock,
the Crosswalk, and Trier allocation are unchanged. Full evidence is in
[`reports/batch13_2_hanau_geographic_harmonization.md`](../reports/batch13_2_hanau_geographic_harmonization.md).

## Batch 14 BBSR charging-pattern analysis

Batch 14 performs a read-only statistical analysis using only the harmonized
Batch 13.2 analytical layer:

- `analytics.charging_by_bbsr_district_2025_harmonized` is the 400-unit
  historical target-unit grain.
- `analytics.charging_by_bbsr_type_2025_harmonized` is the four-category
  reconciliation view.
- The source infrastructure date is `2026-09-30`; the historical BBSR
  geographic stand is `2025-12-31`.
- The 400 historical units represent 401 current BNetzA source components.
  Hanau and remaining Main-Kinzig-Kreis are one historical target; Kassel city
  remains type 1 and Kassel county remains type 2.

### Validated category results

| BBSR type | Historical units | Equipment | Points | Equipment share | Point share | Fast share | >=150 kW share | >=350 kW share | Nominal MW | Nominal-power share |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 68 | 39,789 | 69,863 | 33.82% | 33.07% | 18.75% | 13.87% | 1.69% | 2,373.0481 | 25.75% |
| 2 | 131 | 42,191 | 77,986 | 35.86% | 36.92% | 26.82% | 19.87% | 3.37% | 3,509.5100 | 38.08% |
| 3 | 98 | 18,042 | 32,342 | 15.33% | 15.31% | 32.63% | 24.36% | 4.47% | 1,669.6451 | 18.12% |
| 4 | 103 | 17,640 | 31,062 | 14.99% | 14.70% | 33.88% | 25.38% | 5.47% | 1,663.2141 | 18.05% |

National reconciliation is exact: 117,662 equipment records, 211,253 points,
156,155 normal points, 55,098 fast points, 40,950 points at least 150 kW,
6,950 points at least 350 kW, and 9,215.4173 MW of declared equipment nominal
power. No unclassified infrastructure remains. Fast (`>22 kW`), >=150 kW,
and >=350 kW are nested declared-power classifications, not mutually exclusive
accessibility bands.

### Distribution, weighting, and concentration findings

- The all-unit point-weighted fast share is 26.08%, while the unweighted mean
  of unit fast shares is 31.25% (a -5.17 percentage-point difference). The
  corresponding weighted/unweighted differences are -3.80 points for >=150 kW
  and -0.80 points for >=350 kW. Small units therefore have more influence on
  the unweighted mean than on the national point mix.
- Type 1 has more points than types 3 and 4 but fewer than type 2. Type 4 has
  the highest within-category fast share, whereas type 2 has the largest
  absolute fast-point count. Absolute scale and relative mix are different
  statements.
- Berlin is the largest unit for total points (7,644; 3.62% of national
  points), fast points (1,256), >=150 kW points (1,000), and >=350 kW points
  (136). The top 10 units account for 17.38% of points, 11.22% of fast points,
  11.22% of >=150 kW points, and 12.83% of >=350 kW points.
- The exploratory 30-point minimum for fast-share rankings excludes no unit in
  this snapshot. The filter remains documented because small denominators can
  make percentages unstable in future snapshots.
- Highest fast-share examples are Hersfeld-Rotenburg (69.43% of 314 points),
  Nordhausen (68.99% of 158), and Saale-Orla-Kreis (64.13% of 223). Lowest
  examples are Stuttgart (4.98% of 4,381), Calw (4.99% of 441), and Heidelberg
  (7.65% of 784). These are descriptive outlier screens, not quality rankings.

### Interpretation controls

- **OBSERVED:** Type 4 has the highest fast-point share, while type 2 has the
  largest absolute fast-point count.
- **SUPPORTED ASSOCIATION:** Across the four category aggregates, fast-share
  ordering and high-power-share ordering are the same. This is descriptive
  association across four groups, not a causal finding.
- **PLAUSIBLE HYPOTHESIS:** Normal/fast mix, high-power concentration, and the
  size and composition of individual historical units may contribute to the
  observed differences. Current data cannot identify a cause.
- **NOT TESTABLE WITH CURRENT DATA:** Resident population, area, traffic or
  motorway corridors, EV ownership, demand, utilization, queueing, reliability,
  delivered energy, and accessibility cannot explain these results without
  additional same-grain evidence. No KBA vehicle-stock data were used.

The recommended future Tableau set is small: category point counts/shares,
fast counts/shares, nested >=150 and >=350 kW counts/shares, and unit-level
P10/median/P90 distributions. Nominal power and top-k concentration are useful
context measures. BBSR-based BEV-to-charger ratios remain unsupported because
there is no approved dated BBSR/KBA bridge.

Full tables, outlier rankings, KPI assessment, validation evidence, source
fingerprints, and reproducibility instructions are in
[`reports/batch14_bbsr_charging_analysis.md`](../reports/batch14_bbsr_charging_analysis.md).
The reproducible diagnostics are
[`reports/batch14_bbsr_type_metrics.csv`](../reports/batch14_bbsr_type_metrics.csv)
and
[`reports/batch14_bbsr_district_metrics.csv`](../reports/batch14_bbsr_district_metrics.csv).

## Batch 15 KBA EV-stock findings

Batch 15 is a separate read-only KBA analysis. It does not combine vehicle
stock with the BNetzA charging register or any BBSR layer.

### National and state findings

National passenger-car stock rose from 49,486,487 on 2026-01-01 to 49,696,710
on 2026-07-01. BEV stock rose from 2,034,260 to 2,365,047 (+330,787; +16.26%),
while PHEV stock rose from 1,122,958 to 1,226,863 (+103,905; +9.25%). BEV
share increased from 4.11% to 4.76% of national passenger cars; PHEV share
increased from 2.27% to 2.47%; combined BEV + PHEV share reached 7.23%.
These are registered-stock changes, not new registrations or sales.

Nordrhein-Westfalen had the largest July BEV stock (527,377) and the largest
January–July absolute increase (+72,595). Hamburg had the highest July BEV
penetration among the 16 named states (5.97%). Mecklenburg-Vorpommern had the
highest January–July state BEV growth (+20.98%). `Sonstige` remains a separate
residual and is not blended into a state.

### Registration-region findings

FZ 27.15 contains 400 stable KBA registration-region codes at each snapshot.
The July 2026 BEV penetration median is 4.53% and the PHEV penetration median
is 2.13%. The ten largest covered regions account for 14.78% of July
400-region BEV stock and 17.91% of 400-region PHEV stock. Weighted January–July
BEV growth is 16.26%, compared with an unweighted mean of regional growth rates
of 17.36%; for PHEVs the values are 9.25% and 10.37%.

The percentage-growth ranking uses a documented January BEV baseline of 1,000
vehicles: 377 regions are eligible and 23 are disclosed as excluded. The
threshold is exploratory and does not remove excluded regions from the CSV.
KBA `07211 TRIER-SAARBURG` stays one shared registration region; no stock is
allocated between Trier city and Trier-Saarburg.

### Ownership and alternative grains

FZ 27.5 supports commercial/private BEV and PHEV composition at state,
`Sonstige` and national grain. In July, private ownership represented 61.49%
of observed-owner BEV stock and 54.31% of observed-owner PHEV stock nationally;
published totals retain 3,522 BEV and 1,850 PHEV unallocated/unknown residuals.
The source footnote explains that `zusammen` and `Deutschland insgesamt`
include missing or implausible holder-group values. District-level ownership is
not inferred.

FZ 27.16 is a postcode breakdown without district/state identifiers. FZ 27.17
is nested under KBA districts but has no municipality code and repeated names
across districts. Both have missing numeric cells after parsing source dots and
remain descriptive future-use inputs rather than new Crosswalks.

### Historical and interpretation controls

FZ 27.9 supports a 33-observation national quarterly history from 2018-07-01
through 2026-07-01 after deterministic overlap deduplication. Across 400
regions, January–July BEV and PHEV percentage growth have a descriptive
Pearson correlation of 0.464. This is a supported association in the observed
stock changes, not a causal finding. Population, traffic, demand, charging
utilization, sales flows, migration, accessibility and causal infrastructure
effects remain not testable with the current sources.

Complete tables, worksheet capabilities, formulas, KPI statuses, fingerprints
and validation evidence are in
[`reports/batch15_kba_ev_stock_analysis.md`](../reports/batch15_kba_ev_stock_analysis.md).

## Batch 16 state EV stock versus charging infrastructure

Batch 16 is a separate read-only state-level comparison. It uses KBA FZ 27.2
passenger-car stock dated `2026-07-01` and the BNetzA Ladesäulenregister dated
`2026-09-30`. It aggregates equipment, point, status and declared-power
measures to one row per state before joining one KBA vehicle row per state. It
does not use BBSR, the KBA district Crosswalk, a Trier allocation, a new
DuckDB object or a Tableau asset.

### Reconciliation and benchmarks

| Scope | Passenger cars | BEV | PHEV | Infrastructure scope |
|---|---:|---:|---:|---|
| Published `Deutschland` | 49,696,710 | 2,365,047 | 1,226,863 | KBA national row |
| 16-state sum | 49,644,855 | 2,362,218 | 1,225,241 | Comparable to all 16 BNetzA state rows |
| `Sonstige` | 51,855 | 2,829 | 1,622 | KBA residual, not a federal state |
| 400 KBA registration regions | 49,644,855 | 2,362,218 | 1,225,241 | Exact match to 16-state sum |
| BNetzA 16-state infrastructure | — | — | — | 117,662 equipment; 211,253 points |

The primary comparable cross-source benchmark is **11.18 registered BEVs per
registered point**, or **89.43 points per 1,000 BEVs**, calculated from the
16-state sums. The published-national numerator gives **11.20 BEVs per point**
because it adds 2,829 `Sonstige` BEVs without adding a corresponding
infrastructure row. State ratios are not averaged to create either benchmark.

### State-level findings

- **OBSERVED:** Nordrhein-Westfalen has the largest July BEV stock (527,377),
  Hamburg the highest BEV penetration (5.97%), and Nordrhein-Westfalen the
  largest charging-point stock (41,536).
- **OBSERVED:** Sachsen-Anhalt has the highest fast-point share (39.89%), while
  Mecklenburg-Vorpommern has the highest >=150 kW point share (32.29%).
  These are maximum declared-power classifications, not availability or
  utilization measures.
- **OBSERVED:** The largest absolute BEV-share/point-share gap is Nordrhein-
  Westfalen (+2.66 percentage points), followed by Berlin (-1.31 points) and
  Rheinland-Pfalz (+1.24 points). The gap is compositional, not a shortage or
  surplus measure.
- **OBSERVED:** The lowest and highest BEV-per-point ratios are Mecklenburg-
  Vorpommern (6.73) and Saarland (16.48). The lowest and highest fast points
  per 1,000 BEVs are Baden-Württemberg (16.95) and Mecklenburg-Vorpommern
  (58.16). Counts remain the primary evidence beside each ratio.

The complete 16-state table, including BEV/PHEV stock, passenger-car
denominators, charging counts, power bands, nominal MW, all cross-source
ratios, equipment statuses and both dates, is in
[`reports/batch16_state_ev_charging_alignment.md`](../reports/batch16_state_ev_charging_alignment.md)
and [`reports/batch16_state_comparison.csv`](../reports/batch16_state_comparison.csv).

### Associations and interpretation

The descriptive Pearson/Spearman association between absolute BEV stock and
absolute charging points is `0.991 / 0.985`; excluding the three largest
passenger-car states gives `0.977 / 0.973`. Passenger cars versus charging
points is `0.983 / 0.926`, while BEV penetration versus fast-point share is
`-0.715 / -0.688`. These are 16-state descriptive summaries, not significance
tests or causal findings. The absolute and share associations are strongly
scale/composition-driven; ratio-versus-ratio measures have denominator-driven
interpretation.

- **SUPPORTED ASSOCIATION:** Absolute stock and infrastructure counts
  co-vary descriptively across states, with the association remaining high
  after excluding the three largest states.
- **PLAUSIBLE HYPOTHESIS:** State size, urban form, fleet composition, siting
  patterns and travel may contribute to the observed differences, but the
  current cross-section cannot identify the mechanism.
- **NOT TESTABLE WITH AVAILABLE DATA:** Demand, utilization, sessions, queues,
  reliability, traffic flow, delivered energy, accessibility and causal
  infrastructure effects.

The full report contains the validation matrix, source fingerprints, formulas,
Tableau suitability assessment and reproducibility command.

## Batch 17 temporal validity and cross-source KPI sensitivity

Batch 17 audits the temporal meaning of the Batch 16 state comparison without
changing DuckDB or the source artifacts. The primary vehicle denominator is
KBA registered passenger-car stock on `2026-07-01`; the published infrastructure
denominator is the BNetzA register snapshot on `2026-09-30`, a 91-day separation.
The source dates are not interchangeable with equipment commissioning dates,
point activation dates, or observed operational availability.

### Commissioning-date quality

The real field is `core.charging_equipment.commissioning_date`, with the
original `commissioning_date_raw` retained. All 117,662 raw values are
nonblank and parse successfully; there are zero parsed NULLs, zero parsing
failures, zero dates after the September snapshot, and zero dates before 1900.
The minimum parsed date is `1992-10-01`; 21 equipment records fall before 2010
and remain visible as unusual historical values. The point table has no
individual activation-date column. The date quality supports a reproducible
equipment-level cohort calculation, not reconstruction of point-level
historical existence or availability.

### Published and retrospective perspectives

Perspective A is labelled **CROSS-SNAPSHOT DESCRIPTIVE COMPARISON**. It uses
the full September BNetzA publication and July KBA stock. The published
infrastructure totals are 117,662 equipment, 211,253 point rows, 156,155
normal points, 55,098 fast points, 40,950 points at least 150 kW and 6,950
points at least 350 kW.

Perspective B is labelled **RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT
ACTUAL JULY INFRASTRUCTURE**. It retains September point rows attached to
equipment commissioned on or before `2026-07-01`: 114,900 equipment, 206,365
points, 152,981 normal points, 53,384 fast points, 39,543 points at least 150
kW and 6,335 points at least 350 kW. The complement contains 2,762 equipment
and 4,888 points commissioned after the cutoff; 80 equipment records are dated
exactly on the cutoff and are included. All post-cutoff equipment is currently
labelled `In Betrieb`, while the 20 `In Wartung` records are pre-cutoff; no
status filter was applied.

### State sensitivity and KPI decisions

The 16-state July BEV denominator is 2,362,218. The primary BEVs-per-point
ratio changes from `11.181938` in the published September comparison to
`11.446796` in the survivor cohort, a `+2.37%` survivor-minus-published change.
The BEVs-per-point ranking is unchanged for all 16 states; the fast-points per
1,000 BEVs ranking changes for four states. The highest/lowest ratio and
power-mix outliers are reported separately for both perspectives, with the
>=350 kW point-share low outlier changing from Berlin to Baden-Württemberg.
These empirical ranking results do not prove that the survivor cohort matches
July infrastructure or that any ratio measures adequacy.

The recommended publication statuses are:

- `CONTEXT_ONLY` for BEVs per registered point, its inverse, and the optional
  combined plug-in ratio; BEVs per point may appear as a secondary contextual
  KPI with both dates and no adequacy threshold, not as a headline tile.
- `EXPLORATORY_SENSITIVITY` for fast/HPC points per 1,000 BEVs, share gaps,
  rank comparisons and state correlations.
- `NOT_SUPPORTED` for infrastructure adequacy, shortage or surplus because
  no demand, sessions, availability or approved service standard is observed.

The fixed-September-denominator January/April illustration is a vehicle-stock
sensitivity only: 16-state BEVs per fixed September point are `9.618183` on
2026-01-01, `10.258368` on 2026-04-01 and `11.181938` on 2026-07-01. It does
not imply that September infrastructure existed unchanged in January or April.

Full state values, cohort distributions, publication decisions, validation
evidence and warning labels are in
[`reports/batch17_temporal_kpi_validity.md`](../reports/batch17_temporal_kpi_validity.md),
[`reports/batch17_state_temporal_sensitivity.csv`](../reports/batch17_state_temporal_sensitivity.csv),
[`reports/batch17_equipment_commissioning_cohorts.csv`](../reports/batch17_equipment_commissioning_cohorts.csv),
and [`reports/batch17_kpi_publication_decisions.csv`](../reports/batch17_kpi_publication_decisions.csv).

## Batch 18 consolidated readiness findings

Batch 18 converts the validated findings into a publication-readiness
decision. The strongest current analytical story is not a charger adequacy
score; it is the contrast between absolute registered point scale and declared
power composition, supported by a separate registered-EV stock profile.

### Verified findings

- The September BNetzA register contains 117,662 equipment records and
  211,253 populated point slots. Maximum-per-point declared-power parsing gives
  156,155 normal, 55,098 fast, 40,950 at least 150 kW and 6,950 at least
  350 kW points; declared equipment nominal power is 9,215.4173 MW.
- July 2026 KBA national totals are 2,365,047 BEVs and 1,226,863 PHEVs. The
  comparable 16-state/400-region scope is 2,362,218 BEVs and 1,225,241 PHEVs;
  `Sonstige` remains separate.
- The historical BBSR harmonized charging layer reconciles 401 current source
  components to 400 BBSR 2025 target units. It is charging-only and retains
  the `2025-12-31` BBSR stand beside the `2026-09-30` BNetzA date.
- The canonical Batch 18 register contains 59 KPI/candidate rows with status
  counts `HEADLINE_READY` 16, `HEADLINE_READY_WITH_DATES` 11,
  `CONTEXT_ONLY` 8, `EXPLORATORY` 17 and `NOT_SUPPORTED` 7.

### Methodological decisions

- BEVs per registered point is `CONTEXT_ONLY`; its comparable 16-state value is
  11.181938 and the retrospective survivor sensitivity is 11.446796. Neither
  is an adequacy, accessibility, utilization or demand measure.
- Temporal survivor-cohort metrics are `EXPLORATORY`; the survivor cohort is
  not actual July infrastructure. A genuine historical infrastructure panel is
  `BLOCKED` with current data.
- Infrastructure adequacy, shortage, surplus, utilization, energy delivery,
  queueing, reliability, real-time availability and causal adoption effects
  are `NOT_SUPPORTED`.
- No KBA-to-BBSR vehicle-stock integration is published. No BBSR ratio is
  calculated and no `07211` Trier BEV stock is allocated.

### Recommended portfolio analyses

Prioritize the BBSR historical charging-only composition story, regional
declared-HPC concentration, the date-labelled 16-state EV/charging profile,
and temporal sensitivity as an explanatory methods view. Keep ownership
composition as supporting context. Defer genuine historical evolution and
BBSR vehicle-stock integration until their prerequisites are approved and
available.

The complete candidate assessments, source grains and join risks are in
[`reports/batch18_tableau_analysis_candidates.md`](../reports/batch18_tableau_analysis_candidates.md);
the decision register is in
[`reports/batch18_readiness_decisions.md`](../reports/batch18_readiness_decisions.md).
