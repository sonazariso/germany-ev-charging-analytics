# Batch 18 — Tableau analysis candidates and readiness

**Scope:** analytical recommendations only. No Tableau workbook, extract,
dashboard or persistent SQL object was created.

## How to read this review

“Ready now” means that the existing source grain and arithmetic support a
descriptive Tableau analysis after an approved extract-preparation step. It
does not mean that the source is exhaustive, that dates are contemporaneous,
or that a chart can support an adequacy, demand, accessibility or causal
claim.

Every source-date-dependent view must retain its infrastructure date, vehicle
date, BBSR geographic stand where applicable, scope label and mapping status.
The current Tableau candidates are therefore a portfolio of questions and
interpretation controls, not a set of approved dashboard designs.

## Candidate portfolio

### 1. Urban versus rural charging composition

**Core question:** How does the composition of the published charging
register differ across the four BBSR settlement-structural types when the
same infrastructure snapshot is aggregated to the historical BBSR target
geography?

**Existing evidence:** The harmonized Batch 13.2 layer contains 400 historical
BBSR target units formed from 401 BNetzA source components. Type 2 has the
largest absolute point count (77,986) and type 4 has the largest within-type
fast share (33.88%). Type 1 has 69,863 points but an 18.75% fast share. These
are distinct scale and composition findings.

**Proposed metrics:** equipment count, populated point-slot count, point share,
fast count/share (`>22 kW`), nested `>=150 kW` and `>=350 kW` counts/shares,
nominal equipment MW, points per equipment unit, and unit-level P10/median/P90.

**Visual concept:** Paired absolute-count and within-type-share bars, followed
by a distribution panel for unit medians and percentiles. A selector can
switch between total points, fast points, and high-power points without
relabeling the denominator.

**New insight:** It separates “where most registered points are” from “which
types have a larger declared fast/HPC mix.” This is more informative than a
single charger-count bar.

**Limitations:** The BBSR stand is `2025-12-31` while infrastructure is
`2026-09-30`; the layer is a historical target reconstruction, not an official
2026 BBSR classification. No population, area, traffic, EV-stock or demand
denominator exists in this layer.

**Ready now:** Yes, as a charging-only descriptive analysis with mandatory
date/vintage caveats. Do not add KBA vehicle stock.

**What would strengthen it:** Same-vintage population/area or EV-stock data,
operational availability/session measures, and an approved current BBSR
reference. These are future data requirements, not Batch 18 changes.

### 2. Regional concentration of HPC infrastructure

**Core question:** Is declared high-power infrastructure concentrated in a
small number of historical units, and does the concentration differ between
all points and `>=150`/`>=350 kW` points?

**Existing evidence:** The harmonized district output supports top-1/top-5/
top-10 shares, descriptive HHI, ranks and point-level power bands. Berlin and
Hamburg lead absolute totals, while rural outlier units can have a high
within-unit fast/HPC share. The report documents the descriptive HHI values
for total points and fast points.

**Proposed metrics:** top-k share of national points, fast points, `>=150 kW`
points and `>=350 kW` points; rank; HHI; unit-level fast/HPC share; and
absolute-versus-share rank differences.

**Visual concept:** Pareto bars for top-k concentration, a ranked table with
absolute counts beside shares, and a scatter of total points versus HPC share.
Avoid a map unless an approved geometry source is added; the current data
provide keys and names, not a new geometry asset.

**New insight:** It distinguishes concentration of absolute infrastructure
from concentration of declared power mix, exposing outliers without calling
them underserved or overprovided.

**Limitations:** A rank is not a service-quality, market-power, coverage or
need measure. The BNetzA register is not a complete census, and declared power
is not delivered energy or availability.

**Ready now:** Yes, as `EXPLORATORY` descriptive concentration analysis.

**What would strengthen it:** Dated traffic, population/area, EV-stock and
operational-use denominators at compatible geography and vintage.

### 3. Absolute charging supply versus fast-point share

**Core question:** Which states or historical units combine a large absolute
registered point stock with a high or low declared fast-point share?

**Existing evidence:** Nordrhein-Westfalen has the largest state point stock
(41,536), while Sachsen-Anhalt has the highest state fast-point share
(39.89%). At BBSR type grain, type 2 has the largest absolute fast-point count
(20,917) while type 4 has the highest within-type fast share (33.88%).

**Proposed metrics:** point count, equipment count, fast count/share,
`>=150`/`>=350 kW` count/share, and nominal MW. Show the denominator beside
every share.

**Visual concept:** A quadrant or scatter with absolute points on one axis and
fast share on the other, accompanied by count labels and a date subtitle.
Use separate state and historical-BBSR views; do not mix the grains in one
ranking.

**New insight:** It prevents large regions from being mistaken for fast-mix
leaders and fast-mix leaders from being mistaken for absolute supply leaders.

**Limitations:** Cross-source state comparisons use KBA `2026-07-01` only when
vehicle measures are shown; BNetzA infrastructure is `2026-09-30`. Power is a
declared classification, not capacity or utilization.

**Ready now:** Yes. The infrastructure-only version is headline-capable with
dates; the vehicle comparison remains descriptive and date-labelled.

**What would strengthen it:** Contemporaneous infrastructure/vehicle dates,
plus a validated demand or operational denominator.

### 4. EV penetration and state-level charging composition

**Core question:** How do registered BEV/PHEV penetration and the composition
of the published charging register vary across the 16 federal states?

**Existing evidence:** The state layer reconciles exactly to 16 states and the
400 KBA registration-region scope. Hamburg has the highest July BEV
penetration (5.97%), Nordrhein-Westfalen the largest BEV stock (527,377) and
point stock (41,536), and power-mix shares vary materially by state.

**Proposed metrics:** BEV/PHEV stock, passenger-car stock, BEV/PHEV/combined
penetration, point count, fast/HPC count/share, equipment count and nominal
MW. Keep `Deutschland` and `Sonstige` as separate reconciliation rows.

**Visual concept:** A state profile table with linked rank bars, paired stock
and penetration views, and a separate infrastructure power-mix panel. A
scatter can show association, but it must be labelled descriptive and n=16.

**New insight:** It combines adoption composition with infrastructure
composition at the common state grain without pretending that the sources
share a date or a causal mechanism.

**Limitations:** KBA stock is registered stock, not demand or sales; the two
source dates are 91 days apart; correlations are scale- and denominator-
sensitive; no population, traffic, utilization or availability denominator is
validated.

**Ready now:** Yes, as a date-labelled state comparison. Do not use its ratios
as adequacy thresholds.

**What would strengthen it:** Same-date infrastructure and vehicle snapshots,
population/traffic controls, and operational charging data.

### 5. EV stock versus registered public charging points

**Core question:** What descriptive relationship is visible between registered
vehicle stock and the published point register at state or KBA registration-
region grain?

**Existing evidence:** The comparable 16-state July BEV total is 2,362,218 and
the September point total is 211,253, yielding 11.181938 BEVs per point. The
retrospective September-survivor sensitivity is 11.446796 (+2.37%), but it is
not actual July infrastructure.

**Proposed metrics:** absolute BEV and point counts, BEVs per registered point,
points per 1,000 BEVs, optional combined plug-in ratio, and the published vs
survivor sensitivity.

**Visual concept:** Count-versus-count scatter and a secondary ratio table with
both source dates. Do not use a gauge, red/green adequacy color, threshold or
“shortage/surplus” label.

**New insight:** It makes denominator and date sensitivity visible and shows
why a technically reconciling ratio can still be weak as a service measure.

**Limitations:** The register is not exhaustive, dates are not contemporaneous,
PHEV stock is not charging demand, and the survivor cohort cannot recover
removed assets or point activation.

**Ready now:** Only as `CONTEXT_ONLY` secondary context.

**What would strengthen it:** A genuinely dated infrastructure panel paired
with compatible KBA dates, plus demand/availability/service-standard evidence.

### 6. Geographic outliers and distribution inequality

**Core question:** How skewed are point totals, fast shares and high-power
shares across the 400 historical BBSR target units or 400 KBA registration
regions when each unit's denominator is kept visible?

**Existing evidence:** Batch 14 reports P10, median, mean, P90, maximum,
mean/median ratios, weighted versus unweighted shares, rank screens and
concentration measures. Batch 15 provides a separate 400-code KBA stock and
penetration distribution.

**Proposed metrics:** unit-level P10/median/P90, mean/median ratio, top-k share,
fast/HPC share, points per equipment unit, and KBA stock penetration. Apply
the existing 30-point exploratory stability filter only where stated.

**Visual concept:** Box plots or percentile bands with a linked ranked table;
separate BBSR charging and KBA vehicle panels. Use annotations to identify
small denominators and vintage differences.

**New insight:** It shows whether category averages hide a long tail of units
and whether weighted national shares differ from an equal-unit average.

**Limitations:** No population/area/traffic denominator, no BBSR/KBA vehicle
bridge, no service-quality measurement, and no causal interpretation.

**Ready now:** Yes, as `EXPLORATORY` distribution analysis.

**What would strengthen it:** Compatible population/area/traffic/EV-stock
denominators and validated geometry for map-based interpretation.

### 7. Private versus commercial EV ownership patterns

**Core question:** How does the published commercial/private holder composition
of BEV and PHEV stock differ across states and over the three KBA snapshots?

**Existing evidence:** FZ 27.5 provides state, `Sonstige` and national rows.
In July 2026, private holders account for 61.49% of observed-owner BEVs and
54.31% of observed-owner PHEVs; owner-row coverage of published totals is
99.85% nationally. The publisher retains unknown/implausible holder residuals.

**Proposed metrics:** commercial/private counts, shares of observed owner rows,
coverage versus published totals, and January-to-July composition changes.

**Visual concept:** 100% stacked bars with the unallocated residual shown
separately, plus a line or slope view for the three dates.

**New insight:** It adds a source-supported ownership dimension without
pretending that a postcode or municipality table provides district ownership.

**Limitations:** FZ 27.5 does not support district ownership in this project;
owner totals include unknown/implausible holder groups; ownership share is not
charging demand or behavior.

**Ready now:** Yes, as `CONTEXT_ONLY` supporting analysis at its published
state/residual/national grain.

**What would strengthen it:** A validated district-level owner product with
stable geographic keys and an approved denominator treatment.

### 8. Temporal mismatch and sensitivity of cross-source comparisons

**Core question:** How much do descriptive cross-source ratios and rankings
change when the September register is compared with its retrospective
commissioning-date survivor cohort?

**Existing evidence:** All 117,662 commissioning values parse; 2,762 equipment
records and 4,888 point rows are after the July cutoff. The 16-state BEVs-per-
point ratio changes from 11.181938 to 11.446796. The BEVs-per-point ranking is
stable across states, while several power-normalized rankings change.

**Proposed metrics:** published vs survivor equipment/point/power counts,
BEVs per point, points per 1,000 BEVs, fast/HPC points per 1,000 BEVs, rank
changes and later-commissioned shares.

**Visual concept:** Slope charts for published-to-survivor ratios, paired bars
for count differences, and a clearly labelled sensitivity table.

**New insight:** It makes the temporal limitation a visible analytical result
instead of hiding it in a footnote.

**Limitations:** Survivor selection is not a historical stock; it excludes
assets removed before September and retains current September point/status
attributes. It cannot establish July operation or point activation.

**Ready now:** Yes, as `EXPLORATORY` methodological sensitivity only.

**What would strengthen it:** Multiple dated infrastructure snapshots with
stable equipment/point identity and source revision metadata.

### 9. Genuine historical infrastructure evolution

**Core question:** How did public infrastructure stock, additions, removals,
power mix and status change over time?

**Existing evidence:** Only the September 2026 BNetzA snapshot is available.
Commissioning dates describe current survivors, not historical stock; there is
no point activation date or removal history.

**Proposed metrics:** dated equipment/point stock, new appearances, removals,
net change, power-band changes, status transitions and completeness diagnostics
after the prerequisites in the [historical feasibility decision](batch18_historical_data_feasibility.md).

**Visual concept:** Time series and event-flow views only after an identity-
aware panel exists.

**New insight:** None can be defended from the current source without
inventing historical observations.

**Limitations:** All historical-stock and observed-snapshot-change claims are
currently unsupported.

**Ready now:** No. Status is `NOT_SUPPORTED` with current data.

**What would strengthen it:** Multiple independent snapshots, stable IDs,
additions/removals, dated attributes/statuses, source-revision metadata and a
completeness/survival-bias review.

## Candidate comparison

The following comparison makes the selection criteria explicit. “High
reliability” refers to reproducible arithmetic and source-grain evidence; it
does not mean that the underlying register is exhaustive or that the analysis
measures service quality.

| Candidate | Analytical depth | Reliability and interpretability | Distinctiveness | Geographic detail | Ability to explain findings | Tableau suitability | Reproducibility | Additional data needed |
|---|---|---|---|---|---|---|---|---|
| Urban/rural charging composition | High: absolute scale, within-type mix and unit distributions | High arithmetic; historical-vintage interpretation is conditional | High | 400 historical target units and four types | High | High | High | Same-vintage population/area or EV stock and operational measures would strengthen it |
| Regional HPC concentration | Medium-high: concentration, rank and outlier diagnostics | High arithmetic; concentration is not need or quality | High | 400 historical target units; KBA vehicle geography kept separate | High | High | High | Compatible denominators and approved geometry would strengthen it |
| Absolute supply versus fast-point share | Medium: scale-versus-composition comparison | High for the current register; declared power only | Medium-high | 16 states and BBSR types, shown separately | High | High | High | Same-date vehicle/charging data and operational evidence |
| EV penetration and state charging composition | High: stock, denominator, power mix and association | High source reconciliation; 91-day date gap limits interpretation | High | 16 states plus separate KBA scopes | High | High | High | Contemporaneous dates and population/traffic controls |
| EV stock versus registered points | Medium: counts, ratios and sensitivity | High arithmetic but low service interpretation | Medium | 16 states or 400 KBA regions, without BBSR joins | Medium-high | Medium; context-only | High | Dated infrastructure panel and demand/availability evidence |
| Geographic outliers and distribution inequality | Medium-high: percentiles, weighted/unweighted shares and concentration | High descriptive arithmetic; denominators remain incomplete | High | 400 BBSR targets or 400 KBA regions in separate views | High | High | High | Compatible population/area/traffic/EV denominators and geometry |
| Private versus commercial ownership | Medium: holder mix, residuals and snapshot comparison | High at published FZ 27.5 grain; residuals need disclosure | Medium | State, `Sonstige` and national only | Medium | High as optional context | High | Validated district-level ownership product |
| Temporal mismatch and survivor sensitivity | High methodological depth; makes uncertainty visible | High for the current evidence; explicitly not historical stock | High | National and 16-state sensitivity | High | High as a methods page | High | Multiple dated snapshots and stable identity/change metadata |
| Genuine historical infrastructure evolution | Potentially very high, but no current result is supported | Not supported with current source | Very high future value | Future identity-aware panel | None defensible now | Deferred | Design is documented; implementation is blocked | Snapshots, identities, additions/removals, dated attributes and completeness evidence |

## Recommended page structure

The page plan below is a recommendation, not approval to create a workbook or
extract. Each page keeps source families separate and exposes the dates and
geographic vintage that define its measures.

### Page 1 — Published register: scale and declared power

- **Main question:** How large is the published German public-charging register, and how is its declared power distributed?
- **Validated KPIs:** `INF-001`–`INF-010`: equipment records, point slots, normal/fast points and share, `>=150 kW`/`>=350 kW` points and shares, nominal MW and snapshot status.
- **Visual concepts:** KPI cards for equipment versus point slots; threshold bars for power bands; a national/state table with count and share denominators; status composition as a dated secondary view.
- **Geographic grain:** National headline with optional 16-state breakdown; equipment and point grains remain visibly distinct.
- **Filters:** State, equipment-versus-point measure, power threshold and source status; no filter should imply availability or service level.
- **Primary source:** `core.charging_equipment`, `core.charging_point` and `analytics.charging_by_state` / `reports/batch16_state_comparison.csv`.
- **Mandatory caveats:** BNetzA snapshot `2026-09-30`; point-slot is not connector count; maximum declared power is not delivered energy; the register is not necessarily a complete census; status is not uptime.
- **Portfolio value:** Establishes the strongest current headline story before any cross-source comparison.

### Page 2 — Geographic composition: settlement type and concentration

- **Main question:** How does charging scale and declared fast/HPC composition differ across historical BBSR settlement types and target units?
- **Validated KPIs:** `BBSR-015`–`BBSR-021`: target-unit and type equipment/point totals, shares, fast/HPC mix, percentiles, concentration and descriptive distribution diagnostics.
- **Visual concepts:** Paired absolute-count and within-type-share bars; unit-level percentile/box plots; Pareto or ranked concentration view; linked table with mapping status.
- **Geographic grain:** Batch 13.2's 400 historical BBSR target units and four compact types; do not mix with KBA registration regions.
- **Filters:** BBSR type, target unit, measure family, absolute-versus-share mode and mapping-status flag.
- **Primary source:** `analytics.charging_by_bbsr_district_2025_harmonized`, `analytics.charging_by_bbsr_type_2025_harmonized`, `reports/batch14_bbsr_district_metrics.csv` and `reports/batch14_bbsr_type_metrics.csv`.
- **Mandatory caveats:** BBSR stand `2025-12-31` is applied to BNetzA `2026-09-30`; this is charging-only historical-target harmonization, not an official 2026 classification; no vehicle, population or demand denominator is present.
- **Portfolio value:** Provides a distinctive urban/rural and concentration story without turning absolute scale into adequacy.

### Page 3 — Registered EV stock and penetration

- **Main question:** How is registered BEV/PHEV stock and passenger-car penetration distributed and changing across the supported KBA grains?
- **Validated KPIs:** `KBA-023`–`KBA-033`: BEV/PHEV/passenger-car stock, same-grain BEV/PHEV/combined penetration, absolute and percentage stock change, and national quarterly stock history.
- **Visual concepts:** National time-series lines; date-selected state and KBA registration-region rank bars/tables; penetration composition bars; reconciliation cards for `Deutschland`, 16-state scope and `Sonstige`.
- **Geographic grain:** National, 16 named states and 400 KBA registration regions, each kept as its own scope.
- **Filters:** KBA reference date, vehicle category, geography scope and change interval; never blend national `Deutschland` with the 400-region sum.
- **Primary source:** `reports/batch15_kba_national_trends.csv`, `reports/batch15_kba_state_metrics.csv`, `reports/batch15_kba_district_metrics.csv` and `analytics.kba_national_quarterly_stock`.
- **Mandatory caveats:** Dates are `2026-01-01`, `2026-04-01` and `2026-07-01`; stock is registered passenger-car stock, not sales, demand or charging use; `07211` remains a combined Trier-Saarburg registration region.
- **Portfolio value:** Gives the portfolio a properly scoped EV-adoption baseline independent of charging adequacy claims.

### Page 4 — State comparison: what the two sources can show together

- **Main question:** What descriptive relationship is visible when 16-state registered EV stock is placed beside the published charging register?
- **Validated KPIs:** `GEO-012`, `KBA-023`–`KBA-028` and `X-038`–`X-045`, with cross-source ratios marked `CONTEXT_ONLY` or `EXPLORATORY`.
- **Visual concepts:** Paired state profile table; count-versus-count scatter; declared-power composition panel; secondary ratio/sensitivity table; association annotation with `n=16`.
- **Geographic grain:** The 16 named federal states only; national and `Sonstige` rows remain reconciliation context, not state rows.
- **Filters:** State, stock category, charging-power threshold and published-versus-survivor sensitivity; keep the source dates fixed and visible.
- **Primary source:** `reports/batch16_state_comparison.csv`, `reports/batch16_state_associations.csv`, `reports/batch17_state_temporal_sensitivity.csv` and the underlying KBA/BNetzA state aggregates.
- **Mandatory caveats:** KBA `2026-07-01` and BNetzA `2026-09-30` are 91 days apart; the register is not exhaustive; ratios are not service standards; association is descriptive and not causal.
- **Portfolio value:** Demonstrates disciplined cross-source analysis while making the limits of denominator comparisons visible.

### Page 5 — Methods and limits: temporal sensitivity

- **Main question:** How much does the interpretation change when the current September register is filtered to a commissioning-date survivor cohort, and why is that not a historical panel?
- **Validated KPIs:** `INF-011`, `T-046` and `T-047`; `T-048` and `T-049` appear as explicit unsupported-data guardrails, not as plotted results.
- **Visual concepts:** Published-versus-survivor slope charts, count-difference bars, rank-change table and a prerequisite checklist for a future identity-aware panel.
- **Geographic grain:** National and 16-state sensitivity; equipment cohort grain remains separate from point activation.
- **Filters:** Published/survivor perspective, inclusive cutoff `2026-07-01`, state and measure family.
- **Primary source:** `reports/batch17_state_temporal_sensitivity.csv`, `reports/batch17_equipment_commissioning_cohorts.csv` and `reports/batch17_temporal_kpi_validity.md`.
- **Mandatory caveats:** Survivor records are current September survivors, not actual July infrastructure; commissioning is equipment-level; removed assets and point activation are unobserved; historical change remains `NOT_SUPPORTED`.
- **Portfolio value:** Converts a common overclaim risk into a transparent, reproducible methods page and protects the headline narrative.

**Optional page:** Private/commercial ownership context using `reports/batch15_kba_ownership_metrics.csv` at its published state/residual/national grain, with unknown/implausible residuals shown separately.

**Deferred pages:** Genuine infrastructure evolution, a BBSR vehicle-stock page, utilization/demand, accessibility, adequacy or shortage scorecards. These require new evidence and explicit owner approval.

## Tableau-ready source assessment

Tableau Public cannot query the local DuckDB file as a live published source.
The objects below are analytically suitable inputs, but any external extract
requires a separate approved preparation and licensing review. “Ready as-is”
means ready as a source-grain analytical output, not ready for publication
without dates and caveats.

| Source object or output | Row grain | Dimensions | Measures | Geographic keys | Reference-date semantics | Join risks | Ready as-is? | Preparation needed |
|---|---|---|---|---|---|---|---|---|
| `analytics.charging_by_state` / `reports/batch16_state_comparison.csv` | One row per federal state | State, source status labels, KBA/BNetzA dates | Equipment, points, power bands, nominal MW, KBA stock/penetration and labelled cross-source context in the CSV | `state_name` | KBA `2026-07-01`; BNetzA `2026-09-30` | Do not join `Deutschland` or `Sonstige` as states; do not average state ratios | Yes for a state profile | Preserve both dates, scope note and context-only/exploratory labels |
| `reports/batch15_kba_state_metrics.csv` | Geography × KBA snapshot date | State, `Sonstige`/national reporting rows, date | Passenger cars, BEV/PHEV stock, penetration, changes/growth | Published FZ 27.2 geography labels | `2026-01-01`, `2026-04-01`, `2026-07-01` | National/residual rows are not states; PHEV is nested under `Hybrid insgesamt` | Yes for vehicle-only trends | Filter scope explicitly and preserve denominator definition |
| `reports/batch15_kba_national_trends.csv` | One national reconciliation row per KBA date | Scope reconciliation, date | National/16-state/`Sonstige`/400-region stock and changes | Scope labels, not map keys | Three KBA stock dates | Do not join repeated infrastructure to these rows as historical infrastructure | Yes for national stock narrative | Use as a reconciliation/source-date panel only |
| `reports/batch15_kba_district_metrics.csv` | One row per KBA registration code with three date columns | KBA code, name, state, eligibility flags | Passenger cars, BEV/PHEV stock, penetration, change/growth | Five-digit KBA registration code | Three KBA stock dates | KBA code is not proven BBSR/Kreis; `07211` is mixed Trier/Trier-Saarburg | Yes for vehicle-only registration-region analysis | Keep one wide source or reshape deliberately; no BBSR join |
| `reports/batch15_kba_ownership_metrics.csv` | Published geography × date | State/residual/national, holder group coverage | Commercial/private/unknown BEV/PHEV counts and shares | Published FZ 27.5 labels | Three KBA dates | Unknown/implausible holder residuals; no district ownership | Yes for context | Show observed-owner denominator and residual separately |
| `analytics.charging_by_bbsr_district_2025_harmonized` / `reports/batch14_bbsr_district_metrics.csv` | One historical BBSR 2025 target unit | BBSR KRS, name, type, mapping status | Equipment, points, declared-power bands, nominal MW | Eight-digit historical BBSR KRS2025 | BNetzA `2026-09-30`; BBSR stand `2025-12-31` | Historical target is not official 2026 classification; 401 source components → 400 targets | Yes for charging-only historical BBSR analysis | Preserve source component count, dates, boundary status and no-KBA warning |
| `analytics.charging_by_bbsr_type_2025_harmonized` / `reports/batch14_bbsr_type_metrics.csv` | One row per BBSR type 1–4 | Type code/name | Equipment/points/power counts and shares | Type code, not an administrative key | Same BNetzA/BBSR pair | Absolute counts and within-type shares answer different questions | Yes for category composition | Use paired count/share views and visible vintage note |
| `analytics.charging_by_kba_district_2026_09_30` | One row per unique KBA registration code | KBA code, mapping flags, source geography | Equipment, point and declared-power measures | Five-digit KBA code | BNetzA `2026-09-30` | 401 BNetzA source combinations map to 400 KBA codes; 24 operational mappings remain provisional; Trier shared code | Conditional | Extract only with mapping flags and no BBSR interpretation |
| `analytics.kba_district_charging_vs_bev_2026` | KBA code × three KBA dates | KBA code, dates, mapping flags | Repeated infrastructure plus KBA stock and cross-source ratios | KBA registration code | Infrastructure fixed at `2026-09-30`; KBA dates vary | Repeated infrastructure is not additive; do not sum across dates; no BBSR equivalence | Conditional | Prefer separate vehicle and infrastructure tables or filter exactly one KBA date |
| `reports/batch17_state_temporal_sensitivity.csv` | One federal state | State, published/survivor labels, two dates | Published/survivor counts, power bands, ratios and rank changes | `state_name` | KBA `2026-07-01`; BNetzA `2026-09-30`; cutoff `2026-07-01` | Survivor is not actual July infrastructure; point activation/removal unavailable | Exploratory only | Use as a sensitivity sheet, never a historical stock source |
| `reports/batch17_equipment_commissioning_cohorts.csv` | Distribution type × period × optional state/status | Cohort perspective, year/month, state/status | Equipment/point/power counts and survivor/post-cutoff partitions | State only where populated | September publication; inclusive July cutoff | Current survivors only; no historical stock or event identity | Exploratory only | Label as cohort profile and retain warning text |

### Relationship rules

- The valid state-level relationship is one pre-aggregated KBA state row joined
  to one pre-aggregated BNetzA state row on the 16 named state labels. Carry
  both source dates and never blend `Deutschland` or `Sonstige` into the state
  table.
- The existing BNetzA-to-KBA Crosswalk is a reproducible local mapping with
  unresolved verification limitations. It is not a universal KBA = AGS/ARS or
  KBA = BBSR key. Preserve the shared `07211` Trier registration region and do
  not allocate its 7,869 July BEVs.
- The BBSR 2025 harmonized layer is charging-only. It can support a historical
  target-unit composition view, but there is no validated KBA-to-BBSR vehicle
  relationship. Do not calculate BBSR BEV/PHEV ratios.
- Do not repeat September infrastructure beside January or April KBA stock and
  call it historical infrastructure. Batch 17's fixed-denominator table is a
  vehicle-numerator sensitivity only.

## Recommended analytical priority

1. Lead with the BBSR charging-composition story: absolute point scale versus
   declared fast/HPC mix, with the historical-vintage caveat.
2. Add the state EV-penetration and charging-composition profile as a separate
   dated source comparison.
3. Use concentration/outlier and temporal-sensitivity views as explanatory
   analysis, not headline adequacy panels.
4. Keep ownership as a supporting context page.
5. Defer genuine historical infrastructure evolution and any BBSR vehicle
   integration until the stated prerequisites are met.
