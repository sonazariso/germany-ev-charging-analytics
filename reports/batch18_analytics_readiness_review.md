# Batch 18 — analytics readiness review

**Batch status:** `PASS` — source readiness, KPI publication decisions,
historical feasibility, Tableau candidates and decision register completed.

**Review date:** `2026-11-03`

**Scope:** read-only evidence review and documentation. No DuckDB object, raw
workbook, reference crosswalk, Tableau asset, dependency, download or remote
was added or changed.

## 1. Executive conclusion

The project is ready for a carefully bounded descriptive Tableau portfolio, not
for an adequacy dashboard or a historical infrastructure panel. The strongest
current story is the contrast between absolute registered charging supply and
declared-power composition, supported by a separate state-level EV-stock
profile and an explicitly exploratory temporal-sensitivity view.

The publication decision is deliberately stricter than arithmetic
reconciliation:

- Core single-source infrastructure and KBA stock/penetration measures are
  ready for headline use when their source date and grain are retained.
- Measures that combine the July KBA stock with the September BNetzA register
  are context-only or exploratory because the dates are 91 days apart and the
  register is not exhaustive.
- BBSR charging composition is ready only as a charging-only, historical-target
  analysis. It is not a BBSR vehicle-stock integration and does not create an
  official 2026 Hanau classification.
- A genuine historical infrastructure panel is `BLOCKED` by the absence of
  multiple dated snapshots, stable cross-snapshot identity evidence and
  removal/attribute history.
- Infrastructure adequacy, shortage, surplus, utilization, demand,
  accessibility and causality remain `NOT_SUPPORTED`.

The machine-readable register in
[`batch18_kpi_readiness_register.csv`](batch18_kpi_readiness_register.csv) is
the deterministic Batch 18 publication-status register. It contains 59 rows:

| Status | Count | Meaning in this batch |
|---|---:|---|
| `HEADLINE_READY` | 16 | Single-source measures with validated formula, grain and reconciliation. Standard source-date metadata remains mandatory. |
| `HEADLINE_READY_WITH_DATES` | 11 | Suitable for primary presentation only when the relevant snapshot/vintage dates are visible beside the measure. |
| `CONTEXT_ONLY` | 8 | Useful supporting measures whose source coverage, geographic meaning or interpretation requires a prominent caveat. |
| `EXPLORATORY` | 17 | Descriptive comparison, ranking, sensitivity or source-field analysis; not a headline conclusion. |
| `NOT_SUPPORTED` | 7 | No defensible current formula or validated integration for the requested interpretation. |

## 2. Authoritative analytical baseline

### BNetzA published register — `2026-09-30`

| Measure | Value | Publication meaning |
|---|---:|---|
| Equipment records | 117,662 | Equipment grain; one equipment can contain multiple point slots. |
| Populated charging-point slots | 211,253 | Point-slot grain; not connector count or simultaneous capacity. |
| Normal points | 156,155 | Maximum declared point power `<=22 kW`. |
| Fast points | 55,098 | Maximum declared point power `>22 kW`. |
| Points `>=150 kW` | 40,950 | Nested maximum-per-point declared-power classification. |
| Points `>=350 kW` | 6,950 | Nested maximum-per-point declared-power classification. |
| Equipment nominal power | 9,215.4173 MW | Equipment-level declared nominal power; not energy delivered or grid capacity. |

The power bands use the maximum numeric token in each point's
`connector_power_raw` value. The helper field that parses only one numeric
value is not the headline band source. All current point rows have a valid
maximum classification, but this must be rechecked for a future snapshot.

The BNetzA list is a published registry, not necessarily a complete census of
all public charging infrastructure in Germany. The source status field is a
current snapshot label, not an uptime or availability history.

### KBA stock — three reference dates

| Scope | `2026-01-01` | `2026-04-01` | `2026-07-01` |
|---|---:|---:|---:|
| National BEV (`Deutschland`) | 2,034,260 | 2,169,717 | 2,365,047 |
| 16-state BEV sum | 2,031,870 | 2,167,111 | 2,362,218 |
| National PHEV (`Deutschland`) | 1,122,958 | 1,167,434 | 1,226,863 |
| 16-state PHEV sum | 1,121,516 | 1,165,933 | 1,225,241 |

For July, `Deutschland` includes `Sonstige` (2,829 BEVs and 1,622 PHEVs).
The 400 KBA registration-region table equals the 16 named states, not the
published national row. KBA values are registered passenger-car stock, not
sales, registrations during the interval, charging demand or utilization.

### BBSR historical reference

The selected BBSR reference has geographic stand `2025-12-31`, 400 historical
administrative units and compact type counts 68/131/98/103 for types 1–4.
Batch 13.2 maps 401 current BNetzA source components to 400 historical target
units, combines Hanau with remaining Main-Kinzig-Kreis for the historical target
`06435000` type 2, and corrects Kassel city only in the new harmonized layer.
This is a dated historical harmonization, not an official 2026 BBSR
classification.

## 3. Evidence status by analytical domain

| Domain | Current readiness | Defensible use | Explicit boundary |
|---|---|---|---|
| Charging infrastructure | Ready | National/state counts, point-power composition and nominal MW | Published register; point slots are not connectors or availability. |
| Geographic distribution | Conditional by grain | State profile; KBA registration-region descriptions with flags; BBSR charging-only historical target | KBA registration regions are not proven BBSR/Kreis units; provisional mappings remain visible. |
| BBSR settlement types | Ready for charging-only historical comparison | Type-level counts, shares, distributions and concentration | BBSR stand 2025-12-31 applied to BNetzA 2026-09-30; no vehicle stock join. |
| BEV/PHEV stock | Ready | National, state and 400 KBA registration-region stock, penetration and stock change | Keep national/16-state/`Sonstige` scopes separate; stock is not sales. |
| EV penetration | Ready | Same-grain KBA BEV/PHEV/combined shares of passenger cars | Passenger-car denominator and date must be visible. |
| Ownership | Context-only | FZ 27.5 commercial/private composition at its published grain | Unknown/implausible residuals are not allocated; no district ownership. |
| State EV/charging comparison | Ready with dates | Paired state profile with absolute counts and power mix | Cross-source ratios are context/exploratory; dates are not contemporaneous. |
| Temporal sensitivity | Exploratory | Published versus retrospective survivor comparison | Survivor is not actual July infrastructure. |
| Historical infrastructure evolution | Blocked | None beyond current snapshot/cohort profile | Multiple snapshots and identity/change evidence are absent. |
| Adequacy/demand/utilization | Not supported | None | Sessions, energy, availability, queue, traffic and a service standard are absent. |

## 4. Recommended headline KPI set

The following are the most defensible primary measures for the portfolio. The
register contains the exact formulas, numerators, denominators, fields, scope,
limitations and Tableau treatments.

### Infrastructure headline group

- Registered equipment records.
- Populated charging-point slots.
- Normal and fast point counts and fast-point share.
- Points at least 150 kW and at least 350 kW, with threshold definitions.
- Declared equipment nominal power in MW as a capacity-context measure.
- 16-state infrastructure distribution with the BNetzA date.

### Vehicle-stock headline group

- National, state and 400-region BEV stock.
- National, state and 400-region PHEV stock.
- Passenger-car denominator.
- BEV, PHEV and combined plug-in penetration at the same KBA grain and date.

### Dated change and BBSR headline-with-dates group

- BEV and PHEV stock changes and percentage changes between the three KBA
  snapshots.
- The national KBA quarterly stock trajectory, with stock-date labels.
- BBSR historical-target point/equipment totals and declared-power mix, only
  with `2025-12-31` BBSR and `2026-09-30` BNetzA labels.

Do not place a cross-source ratio in the primary headline group. A headline
tile must not imply a same-day service standard.

## 5. Important context-only and exploratory measures

### Context-only

- BEVs per registered charging point and its inverse. The primary comparable
  16-state result is 11.181938 BEVs per point; the survivor sensitivity is
  11.446796. Both dates and scope must appear.
- Combined plug-in vehicles per registered point, only if BEV and PHEV stock
  are shown separately and the measure is not described as demand.
- Commissioning-year distribution as a current-register profile.
- KBA registration-region and official BNetzA-to-BBSR source-grain outputs with
  mapping/vintage flags.
- FZ 27.5 private/commercial ownership composition.

### Exploratory

- Fast/HPC points per 1,000 BEVs.
- BEV-share minus point-share composition gap.
- State correlations and rankings.
- BBSR unit percentiles, weighted versus unweighted shares and concentration.
- KBA percentage-growth rankings with the 1,000-BEV January threshold.
- Postcode and municipality descriptive distributions.
- Operator, city/county, payment, opening-hours and connector-type field
  analyses, pending their own tokenization/normalization validation.
- Published versus survivor-cohort sensitivity.

## 6. Unsupported claims and integration blockers

The following claims must not be published as factual conclusions from the
current evidence:

- infrastructure adequacy, shortage, surplus or sufficient supply;
- charger utilization, occupancy, energy delivered, queues, reliability,
  uptime, real-time availability or accessibility;
- causal effects of chargers on EV adoption or stock growth;
- a July infrastructure total inferred from September commissioning dates;
- actual historical infrastructure growth from the current survivor cohort;
- a BBSR-based BEV/PHEV-to-charger ratio;
- an official 2026 BBSR classification for Hanau from the 2025 reference;
- a city/county allocation of the 7,869 July BEVs in KBA registration region
  `07211` Trier-Saarburg;
- a universal KBA registration-code = AGS/ARS/KRS/BBSR equivalence.

## 7. Source readiness for Tableau

The detailed source matrix, grain and join rules are in
[`batch18_tableau_analysis_candidates.md`](batch18_tableau_analysis_candidates.md).
The immediately useful source families are:

1. `reports/batch16_state_comparison.csv` for one-row-per-state paired
   profiles, with both source dates.
2. `reports/batch15_kba_national_trends.csv` and
   `reports/batch15_kba_state_metrics.csv` for KBA-only stock and penetration
   trends.
3. `reports/batch15_kba_district_metrics.csv` for KBA registration-region
   vehicle analysis, without BBSR joins.
4. `reports/batch14_bbsr_district_metrics.csv` and
   `reports/batch14_bbsr_type_metrics.csv` for charging-only historical BBSR
   composition.
5. `reports/batch15_kba_ownership_metrics.csv` for context-only ownership
   composition.
6. `reports/batch17_state_temporal_sensitivity.csv` and
   `reports/batch17_equipment_commissioning_cohorts.csv` for exploratory
   temporal sensitivity, not historical stock.

These outputs are suitable for extract design. They still require an approved
Tableau preparation step, license/attribution review, source-date metadata and
deliberate separation of relationships. No dashboard or extract was created
in Batch 18.

## 8. Proposed Tableau narrative

The recommended story is question-led:

1. **How large is the published German public-charging register?** Show
   equipment versus point-slot counts and declared-power bands at the
   September snapshot.
2. **How does declared charging composition vary by geography?** Show the
   state profile and the BBSR historical-target composition, keeping absolute
   volume separate from within-group power shares.
3. **How is registered EV ownership distributed?** Show KBA BEV/PHEV stock,
   passenger-car penetration and stock change at the national/state/KBA
   registration-region grains.
4. **What can a state-level comparison legitimately show?** Pair counts and
   date-labelled composition; keep ratios contextual and associations
   exploratory.
5. **Why can the portfolio not claim adequacy or historical evolution?** Show
   the temporal sensitivity and the missing evidence required for a panel.

The page-level recommendation and optional/deferred pages are recorded in the
[Batch 18 decision register](batch18_readiness_decisions.md), so the current
batch does not silently approve a dashboard design.

## 9. Validation and invariants

The Batch 18 read-only verification found:

- HEAD `ed0320fc956ad5da733bf933c88dec22dcb7f4c7`, which contains the required
  Batch 17 commit;
- clean initial worktree and no configured Git remote;
- source/reference fingerprints unchanged from the Batch 16/17 evidence;
- read-only DuckDB access with 117,662 equipment rows, 211,253 point rows, 16
  state rows, and 400 July KBA regions;
- database hash `5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3`
  matching the prior validation; and
- no source or database write during the review.

The remaining validation for the Batch 18 artifacts is documented in
[`reports/batch18_readiness_decisions.md`](batch18_readiness_decisions.md) and
includes CSV parsing, register/report count reconciliation, Markdown link
resolution, source-fingerprint recheck and `git diff --check`.

## 10. Most defensible next implementation step

After explicit owner approval, prepare compact, source-date-labelled Tableau
extracts from the existing state, KBA-only, BBSR charging-only and temporal
sensitivity outputs. Keep the extract families separate and do not create a
historical panel or BBSR vehicle join. A future Batch 19 should first validate
the extract contract and caveat rendering before any public publication.
