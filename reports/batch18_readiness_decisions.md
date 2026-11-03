# Batch 18 — readiness decision register

**Decision date:** `2026-11-03`

**Decision scope:** analytical publication readiness and next-step
recommendations. These decisions do not approve a new dashboard design, data
source, DuckDB object, Tableau asset or external publication.

## Decision vocabulary

- `VERIFIED_FINDING`: directly supported by an existing validated source,
  report or read-only check.
- `METHODOLOGICAL_DECISION`: a rule adopted to keep a supported metric
  interpretable and reproducible.
- `RECOMMENDATION`: a proposed portfolio or implementation choice that still
  requires owner approval before execution.
- `OPEN_QUESTION`: unresolved evidence or a choice that cannot be answered by
  the current data.

## Register

### D01 — Approved analytically ready KPI families

**Type:** `METHODOLOGICAL_DECISION`

**Decision:** Approve for headline or headline-with-date presentation the
single-source BNetzA equipment/point/power measures, the 16-state charging
distribution, KBA BEV/PHEV/passenger-car stock and same-grain penetration, KBA
stock changes/growth, the national KBA stock trajectory, and the charging-only
historical BBSR type/district measures when their source dates and geographic
vintage are shown.

**Evidence:** [Batch 14 category analysis](batch14_bbsr_charging_analysis.md),
[Batch 15 KBA stock analysis](batch15_kba_ev_stock_analysis.md),
[Batch 16 state comparison](batch16_state_ev_charging_alignment.md),
[Batch 17 temporal decisions](batch17_temporal_kpi_validity.md), and the
[canonical KPI register](batch18_kpi_readiness_register.csv).

**Control:** Headline-ready means formula/grain/reconciliation readiness, not
source exhaustiveness or service quality.

### D02 — Date-label and vintage rule

**Type:** `METHODOLOGICAL_DECISION`

**Decision:** Every output keeps source reference dates. Cross-source measures
must show KBA `2026-07-01` and BNetzA `2026-09-30` together. BBSR historical
outputs must show BBSR `2025-12-31` beside the BNetzA date. Stock changes must
show both endpoints. The date labels are part of the metric definition, not a
decorative footnote.

**Evidence:** The dates are reconciled in [Batch 16](batch16_state_ev_charging_alignment.md)
and the 91-day limitation is established in [Batch 17](batch17_temporal_kpi_validity.md).

### D03 — Context-only cross-source ratios

**Type:** `METHODOLOGICAL_DECISION`

**Decision:** BEVs per registered charging point, registered points per 1,000
BEVs, and optional combined plug-in vehicles per point are `CONTEXT_ONLY`.
They may appear in a secondary table with absolute counts, scope and dates;
they must not be a headline tile, gauge, threshold, red/green state label or
adequacy conclusion.

**Evidence:** The comparable 16-state ratio is 11.181938 BEVs per point; the
retrospective survivor sensitivity is 11.446796 (+2.37%). [Batch 17's KPI
decision table](batch17_kpi_publication_decisions.csv) documents the formula,
dates, cohort warning and interpretation risk.

### D04 — Exploratory metrics

**Type:** `METHODOLOGICAL_DECISION`

**Decision:** Mark fast/HPC points per 1,000 BEVs, share gaps, state
correlations, rank comparisons, BBSR distribution/concentration, KBA growth
rankings, alternative KBA grains, source-field breakdowns and survivor
sensitivity as `EXPLORATORY`. These are useful explanatory diagnostics but do
not establish demand, causality, accessibility, quality or adequacy.

**Evidence:** [Batch 14](batch14_bbsr_charging_analysis.md),
[Batch 15](batch15_kba_ev_stock_analysis.md), [Batch 16](batch16_state_ev_charging_alignment.md)
and [Batch 17](batch17_temporal_kpi_validity.md).

### D05 — Claims that must not be published

**Type:** `METHODOLOGICAL_DECISION`

**Decision:** Infrastructure adequacy, shortage, surplus, utilization,
occupancy, sessions, energy delivery, queue time, reliability, real-time
availability, accessibility and causal charger/adoption effects are
`NOT_SUPPORTED`. No metric may substitute a registered vehicle denominator or
declared power for the missing demand/availability evidence.

**Evidence:** [Data quality controls](../docs/data-quality.md),
[Batch 17 unsupported interpretations](batch17_temporal_kpi_validity.md),
and the unsupported rows in the [KPI register](batch18_kpi_readiness_register.csv).

### D06 — Geographies currently supported

**Type:** `VERIFIED_FINDING`

**Decision:** The following analytical grains are supported with the stated
controls:

- 16 federal states for separate BNetzA and KBA aggregates and a date-labelled
  state comparison;
- KBA FZ 27.15's 400 registration regions for KBA-only stock, penetration and
  change analysis, keeping `07211` Trier-Saarburg as one combined registration
  region;
- BNetzA source geography for charging-only BBSR Path A descriptions with the
  399 verified-compatible, one conditional-vintage and one unresolved row
  visible; and
- the Batch 13.2 400-unit historical BBSR target layer for charging-only
  composition and distribution analysis.

**Evidence:** [Batch 12 path audit](batch12_bbsr_integration_paths.md),
[Batch 13.2 harmonization](batch13_2_hanau_geographic_harmonization.md),
[Batch 15 registration-region analysis](batch15_kba_ev_stock_analysis.md), and
[geographic methodology](../docs/geographic-methodology.md).

### D07 — Integrations that remain blocked or conditional

**Type:** `METHODOLOGICAL_DECISION`

**Decision:** The existing BNetzA-to-KBA Crosswalk remains operationally
provisional where documented and must not be treated as a universal KBA =
AGS/ARS/KRS rule. KBA-to-BBSR vehicle-stock integration is blocked: strict
verified coverage remains zero; Trier is mixed; Hanau/Main-Kinzig is a vintage
conflict; and 397 KBA regions remain unresolved. No BBSR BEV/PHEV ratio is
published.

**Evidence:** [Batch 12 Path B result](batch12_bbsr_integration_paths.md)
and the [Batch 11 audit CSV](batch11_bbsr_kba_compatibility_audit.csv).

### D08 — Historical infrastructure feasibility

**Type:** `METHODOLOGICAL_DECISION`

**Decision:** Genuine historical infrastructure-panel development is
`BLOCKED` with current data. The commissioning-year profile and retrospective
survivor cohort remain available as descriptive/exploratory analyses only.

**Evidence:** [Batch 17 temporal audit](batch17_temporal_kpi_validity.md) and
the full [historical feasibility report](batch18_historical_data_feasibility.md).

### D09 — Additional data requirements

**Type:** `OPEN_QUESTION`

**Decision:** A future panel would require multiple independently dated BNetzA
snapshots, stable equipment identity, stable point identity if feasible, new
appearances, removals, point changes, dated commissioning/activation/status
fields, historical power/connector values, source-revision/reporting-delay
metadata, and a completeness/survival-bias assessment. A future BBSR vehicle
analysis additionally requires a product-specific dated KBA-to-administration-
to-BBSR bridge and an approved Hanau/Trier rule.

**Evidence:** [Historical feasibility prerequisites](batch18_historical_data_feasibility.md)
and [Batch 12 conversion-resource review](batch12_bbsr_integration_paths.md).

### D10 — Most distinctive portfolio analyses

**Type:** `RECOMMENDATION`

**Decision:** Prioritize (1) absolute charging scale versus declared fast/HPC
composition by historical BBSR type, (2) regional HPC concentration and
outlier distributions, (3) the date-labelled state EV-penetration versus
charging-composition profile, (4) context-only EV stock/point comparison, (5)
ownership composition as supporting context, and (6) temporal sensitivity as
a methods page. Defer genuine historical evolution.

**Evidence:** The candidate-by-candidate assessment is in
[Batch 18 Tableau analysis candidates](batch18_tableau_analysis_candidates.md).

### D11 — Tableau page recommendation

**Type:** `RECOMMENDATION`

**Decision:** If the owner approves implementation, use five practical pages:

1. **Published register:** national/state equipment, point slots and declared
   power mix at `2026-09-30`.
2. **Geographic composition:** state profile plus historical BBSR charging-only
   composition, with separate count/share views.
3. **Registered EV stock:** national/state/KBA registration-region BEV/PHEV
   stock, penetration and change across KBA dates.
4. **Cross-source context:** state count comparison and secondary ratios with
   both dates, no adequacy language.
5. **Methods and limits:** temporal sensitivity, survivor warning, geographic
   caveats and unsupported-claim guardrails.

Optional: a compact ownership-context page. Deferred: historical evolution,
BBSR vehicle-stock page, utilization/demand page, and any adequacy scorecard.

**Evidence:** The source matrix and candidate analysis are in
[Batch 18 Tableau analysis candidates](batch18_tableau_analysis_candidates.md).
This is a recommendation, not owner approval of dashboard designs.

### D12 — Next implementation boundary

**Type:** `RECOMMENDATION`

**Decision:** The most defensible next implementation is an owner-approved,
read-only extract specification and validation pass using the existing state,
KBA-only, BBSR charging-only and temporal-sensitivity outputs. It should
preserve source dates, geographic keys, scope labels and caveats. It must not
create a historical panel, add a BBSR vehicle join, or introduce a new source
without explicit approval.

**Evidence:** [Batch 18 analytics readiness review](batch18_analytics_readiness_review.md)
and [reproducibility guidance](../docs/reproducibility.md).

## Owner approval boundary

Batch 18 records recommendations and publication controls. It does not claim
that the project owner approved the five-page Tableau narrative, any extract,
any new data source or any Batch 19 implementation. Explicit approval is still
required before those actions.

## Recommended Batch 19 scope

Do not implement this scope automatically. If approved, Batch 19 should:

1. confirm the canonical KPI register and page narrative;
2. design and validate separate, source-date-labelled extract files from the
   existing outputs;
3. test grain, join and caveat behavior in a local Tableau proof of concept;
4. perform the pending source-license/attribution review; and
5. leave historical infrastructure and KBA-to-BBSR vehicle integration
   deferred unless their separate prerequisites are approved and met.
