# Batch 20 — Tableau Architecture Decision

**Decision:** select **A — separate Tableau data sources backed by the existing
validated Batch 19 exports** for the first Tableau implementation.

**Decision status:** approved for design specification only. No Tableau asset,
physical mart, DuckDB object, or ETL migration is implemented in Batch 20.

## 1. Context

The project has nine deterministic CSV exports with validated aggregate grains,
the existing read-only DuckDB analytical layer, and a canonical 59-KPI
readiness register. The exports cover five distinct analytical subjects:

1. BNetzA national/state charging infrastructure;
2. charging-only historical BBSR target geography;
3. KBA state, registration-region, and national stock;
4. one fixed state EV/charging cross-snapshot comparison; and
5. one fixed temporal sensitivity context.

These subjects do not share one geography or one date. A semantic model must
therefore protect grain and date roles rather than maximize the number of
relationships.

## 2. Alternatives considered

### A — Domain-specific source models

Use the nine Batch 19 files as separate logical data sources. Each source maps
to one or more documented logical facts, and shared dimensions are used only
inside a subject where their keys and dates are validated.

**Advantages:**

- matches the validated source grains directly;
- requires no new physical schema or data movement;
- keeps national, state, BBSR, KBA, comparison, and temporal scopes visible;
- makes date mismatch and publication status easy to display;
- limits repeated-measure risk and keeps initial Tableau development small;
- is reproducible from the manifest and existing contracts.

**Trade-off:**

- cross-subject dashboards require a deliberate pre-combined fact or separate
  worksheets rather than a universal drag-and-drop model;
- a future source addition may require a new data source and relationship
  contract.

### B — Multi-fact relationship model with shared dimensions

Use shared `DimState`, date dimensions, and multiple base facts in one Tableau
logical model.

**Advantages:**

- a common state filter could serve several subject facts;
- the pattern can scale if future facts share stable keys and exact date roles;
- Tableau can protect some aggregate behavior when relationships are correctly
  defined.

**Risks:**

- state charging has one September row while KBA stock has three date rows;
  an unconstrained relationship repeats charging measures;
- BBSR's 400 historical units and KBA's 400 registration regions are unrelated;
- national aggregates and state details can coexist but must not be summed;
- pre-combined state comparison and temporal facts duplicate component measures
  by design and must not be related back to them;
- current exports do not carry physical surrogate keys or a shared dimension;
- safe Tableau settings cannot make an unverified geographic relationship valid;
- relationship query plans and filter propagation are harder to audit.

**Conclusion:** Alternative B offers no meaningful advantage for the current
approved questions. It is rejected for the initial implementation, not
permanently prohibited.

## 3. Decision matrix

Scores are qualitative design assessments, where 5 is strongest for the
criterion and no score implies that an implementation has been performed.

| Criterion | A: separate sources | B: multi-fact relationships | Decision evidence |
|---|---:|---:|---|
| Analytical correctness | 5 | 3 | A preserves validated grains; B needs date and relationship guardrails |
| Tableau development effort | 5 | 2 | A uses existing CSV contracts; B needs shared-key setup and tests |
| Maintainability | 4 | 3 | A has clear subject ownership; B centralizes relationships that are not yet approved |
| Performance | 4 | 3 | A uses small aggregate files; B may query multiple facts and repeated contexts |
| Reproducibility | 5 | 3 | A is directly tied to the manifest and checksums |
| Portfolio quality | 5 | 4 | A demonstrates grain discipline; B would be valuable only with proven shared keys |
| Future source additions | 4 | 4 | Both can extend, but B requires a stable conformed dimension contract |
| Duplicate-aggregation risk | 5 | 2 | A makes cross-source joins explicit; B exposes repeated-date risks |
| Required effort now | 5 | 2 | A needs no new marts; B needs additional implementation and validation |

## 4. Chosen logical facts

| Fact | Exact grain | Initial source |
|---|---|---|
| `FactNationalCharging` | Germany × BNetzA snapshot | `national_charging_2026_09_30.csv` |
| `FactStateCharging` | Bundesland × BNetzA snapshot | `state_charging_2026_09_30.csv` |
| `FactBBSRCharging` | Historical BBSR target unit × BNetzA snapshot × BBSR vintage | `bbsr_district_charging_2025_geography.csv` |
| `FactBBSRTypeCharging` | BBSR type × BNetzA snapshot × BBSR vintage | `bbsr_type_charging_2025_geography.csv` |
| `FactKBAStateStock` | Bundesland × KBA reference date | `kba_state_ev_stock_2026.csv` |
| `FactKBARegistrationRegionStock` | KBA registration region × KBA reference date | `kba_registration_region_ev_stock_2026.csv` |
| `FactKBANationalHistory` | National stock date | `kba_national_stock_history.csv` |
| `FactStateEVChargingComparison` | Bundesland × fixed KBA July/BNetzA September pair | `state_ev_charging_comparison_2026.csv` |
| `FactTemporalSensitivity` | Bundesland × fixed KBA/BNetzA dates × survivor cutoff | `state_temporal_sensitivity_2026.csv` |

The 401-row source-grain BBSR fact and equipment/detail facts remain
conceptual future facts because they are not among the nine Batch 19 exports.

## 5. Required relationship decisions

- Share `DimState` only across state charging, KBA state stock, state
  comparison, and temporal sensitivity where the selected date/context is
  explicit.
- Use `DimChargingSnapshot` only for BNetzA infrastructure dates.
- Use `DimKBAStockDate` only for KBA stock dates, including a role-specific
  national-history date.
- Use `DimBBSRRegion` and `DimBBSRSettlementType` only inside the historical
  charging subject.
- Keep KBA registration-region geography separate from BBSR geography.
- Do not create a direct Fact-to-Fact physical join.
- When a future Tableau relationship is configured, do not assert `All Records
  Match` until the actual key and scope have been proven. The complete matrix
  is in `docs/tableau-relationship-design.md`.

## 6. Future implementation prerequisites

The first implementation can use the nine existing exports without new tables.
Before considering Alternative B or a physical star-schema mart, a future
owner-approved batch must:

1. create versioned dimensions or equivalent stable keys for state, BBSR,
   KBA registration region, KBA stock date, and BNetzA snapshot;
2. carry the source/vintage/version fields into every fact;
3. add controlled source-grain/detail exports only for approved KPIs;
4. prove every relationship's uniqueness, matching scope, and filter direction;
5. test national/state and multi-date duplication with aggregate reconciliation;
6. keep the state comparison and temporal sensitivity facts standalone unless
   their formulas are deliberately reimplemented from components; and
7. obtain a dated KBA-to-BBSR bridge before any BBSR vehicle-stock analysis.

No KBA-to-BBSR bridge, historical infrastructure panel, or adequacy metric is
part of the next implementation scope by default.

## 7. Open risks

- The current state business key is a validated name, not an approved stable
  state code.
- The BBSR layer is a historical 2025 geography applied to a 2026 BNetzA
  snapshot and is charging-only.
- KBA `07211` is intentionally one registration region and cannot be allocated.
- A single BNetzA snapshot cannot support observed infrastructure change or an
  actual historical stock panel.
- Cross-source ratios carry a 91-day date gap and remain contextual or
  exploratory according to the Batch 18 register.
- Aggregate exports do not support status, operator, payment, opening-hours,
  connector-token, ownership, postcode, or municipality detail without future
  controlled facts.

## 8. Handoff

Batch 20 delivers the implementation specification, relationship contract,
validation evidence, and complete KPI mapping. A future Batch 21 may implement
the chosen separate sources after owner approval; it must not silently broaden
scope to physical marts, BBSR/KBA vehicle integration, historical
infrastructure, or remote publication.
