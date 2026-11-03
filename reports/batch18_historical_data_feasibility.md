# Batch 18 — historical infrastructure data feasibility

**Decision:** `BLOCKED` with current data

**Review date:** `2026-11-03`

## Decision summary

The project has one BNetzA infrastructure snapshot, dated `2026-09-30`. It has
an equipment-level commissioning date and stable local source-row keys for the
current file, but it does not contain the observations needed to reconstruct a
dated historical stock. A genuine infrastructure panel is therefore blocked
until multiple independently dated snapshots and identity-preserving change
evidence are available.

The current data support four distinct analytical objects:

| Object | Supported now | Correct interpretation |
|---|---|---|
| `OBSERVED_SNAPSHOT` | Yes | The published BNetzA equipment/point register at `2026-09-30`. |
| `COMMISSIONING_COHORT` | Yes | A descriptive distribution of current September equipment by commissioning date/year. |
| `RETROSPECTIVE_SURVIVOR_COHORT` | Yes, exploratory | September records whose equipment commissioning date is on or before `2026-07-01`; not July infrastructure. |
| `OBSERVED_SNAPSHOT_CHANGE` | No | No second dated BNetzA snapshot is present in the project. |
| `ACTUAL_HISTORICAL_STOCK` | No | Removed records, point-level additions/removals, historical attributes and historical availability are not recoverable from one snapshot. |

The retrospective cohort is useful for sensitivity disclosure only. The
published September comparison contains 117,662 equipment records and 211,253
point rows. The survivor cohort contains 114,900 equipment records and
206,365 currently associated September point rows; it does not establish what
existed or operated in July.

## Evidence reviewed

- [Batch 17 temporal-validity report](batch17_temporal_kpi_validity.md)
- [Batch 17 cohort output](batch17_equipment_commissioning_cohorts.csv)
- [Batch 17 state sensitivity output](batch17_state_temporal_sensitivity.csv)
- [Data sources](../docs/data-sources.md)
- [Data quality](../docs/data-quality.md)
- [Reproducibility rules](../docs/reproducibility.md)

The commissioning-date audit found 0 raw NULL/blank values, 0 parsing
failures, 0 dates after the September snapshot, and 80 equipment records on
the inclusive `2026-07-01` cutoff. These are quality results for the current
field, not evidence of historical completeness.

## What the current source can and cannot establish

### Supported

- Current equipment and populated point counts at the BNetzA September
  snapshot.
- Current declared-power classifications using the maximum numeric token in
  each point's `connector_power_raw` value.
- Current equipment status distribution, with `In Betrieb` and `In Wartung`
  retained as snapshot labels.
- A commissioning-year/month profile for records surviving into the September
  publication.
- A reproducible retrospective equipment-survivor sensitivity using the
  inclusive commissioning-date cutoff.

### Not supported

- July 2026 infrastructure stock.
- Month-by-month or quarter-by-quarter infrastructure additions.
- Equipment removals before September.
- Point-level activation, deactivation or retirement dates.
- Point additions or removals within an existing equipment record.
- Historical connector-type or declared-power values.
- Historical status, opening hours, operational availability, uptime, queues,
  sessions, energy delivery or simultaneous deliverable power.
- An upper or lower bound on actual July infrastructure.
- Observed infrastructure growth from July to September.

The equipment commissioning field is not a point activation field. The
September file also contains only equipment that survived into that
publication, so a current commissioning date cannot recover assets removed
before the snapshot. Point rows inherit the current September record context;
they do not supply a historical point panel.

## Minimum data prerequisites for a genuine panel

The next source-acquisition phase would require owner approval and should not
be treated as satisfied by the current workbook. At minimum it needs:

1. Multiple independently dated BNetzA snapshots covering the analysis period,
   with publication/snapshot dates and source fingerprints.
2. A stable equipment identity across snapshots, including a documented rule
   for ID changes, merges, splits, corrections and duplicate records.
3. A stable charging-point identity if feasible. If point identity is not
   stable, the limitation and a conservative reconciliation rule must be
   explicit.
4. New equipment appearances and point additions, not only records surviving
   into the latest snapshot.
5. Equipment and point removals, including whether removal means delisting,
   closure, relocation, reporting correction or source delay.
6. Equipment commissioning dates and, where available, point-level activation
   dates, retirement dates and effective dates.
7. Status changes with effective dates, rather than only the current status
   label.
8. Historical reported nominal power, connector types and connector-power
   values, with change detection at the appropriate grain.
9. Source revision, correction and reporting-delay metadata so that a changed
   row is not automatically interpreted as a physical installation change.
10. Evidence about historical completeness, survivor bias and the population
    of operators represented in each snapshot.

KBA vehicle snapshots should be paired to an infrastructure snapshot with a
compatible reference date. The present KBA releases (`2026-01-01`,
`2026-04-01`, `2026-07-01`) do not make the September infrastructure file an
observed denominator for those earlier dates.

## Proposed methodology if prerequisites are obtained

This is a design recommendation, not an implementation in Batch 18.

### 1. Preserve immutable snapshot layers

Store each dated source snapshot as a separately fingerprinted, source-grain
observation. Do not overwrite an earlier release. Keep publication date,
source-file version, extraction timestamp, and any source correction note.

### 2. Build identity-aware event tables

Create an analytical event table with one record per stable equipment identity
and one record per stable point identity where the source supports it. Record
first appearance, last appearance, additions, removals, attribute changes,
status changes, commissioning date, and effective snapshot dates. Keep an
`identity_confidence` or equivalent exception flag for unresolved changes.

### 3. Separate physical and reporting events

Classify changes into at least `NEWLY_OBSERVED`, `REMOVED_FROM_SNAPSHOT`,
`ATTRIBUTE_CHANGE`, `STATUS_CHANGE`, `IDENTITY_RECONCILIATION`, and
`SOURCE_CORRECTION`. A row appearing for the first time is not automatically a
new installation, and a row disappearing is not automatically a physical
removal.

### 4. Reconstruct dated stocks conservatively

For each requested reference date, use the snapshot observed closest to that
date under an approved rule. Report additions/removals only when identity and
source semantics support them. Do not backcast a point's existence from an
equipment commissioning date alone.

### 5. Validate every panel slice

Reconcile equipment-to-point relationships, declared point counts, power-band
totals, status totals, source scope, and identity exceptions for each snapshot.
Keep completeness and survival-bias diagnostics beside the panel rather than
burying them in a note.

### 6. Pair with KBA using explicit date and geography keys

Use one KBA stock row per selected date and one infrastructure stock row per
matching date. Keep `Deutschland`, the 16 named states, `Sonstige`, and the
400 KBA registration-region scope separate. Do not create a BBSR vehicle-stock
panel without a separately validated dated KBA-to-BBSR bridge.

## Readiness gate

| Gate | Current result | Required before a `READY` decision |
|---|---|---|
| At least two independent infrastructure snapshots | `FAIL` | Multiple dated snapshots |
| Stable equipment identity across snapshots | `NOT TESTABLE` | Cross-snapshot identity evidence |
| Stable point identity | `NOT AVAILABLE` | Point IDs or an approved conservative alternative |
| Additions and removals observable | `FAIL` | New-appearance and disappearance records |
| Historical attributes/statuses observable | `FAIL` | Dated attribute/status observations |
| Completeness and reporting-delay metadata | `FAIL` | Source metadata and coverage assessment |
| KBA date compatibility | `CONDITIONAL` | Matching or explicitly modelled reference dates |
| BBSR vehicle integration | `BLOCKED` | Product-specific dated KBA-to-BBSR bridge |

The correct current conclusion is `BLOCKED`, not `READY`. A future review can
promote the panel to `CONDITIONAL` after the minimum snapshots and identity
evidence exist, but that would still require a separate validation before
publication.

## Batch 18 recommendation

Do not build a historical infrastructure panel in Batch 19 from the current
commissioning dates. Keep the published September snapshot as the only
observed infrastructure stock, show the commissioning distribution as a
descriptive cohort profile, and retain the survivor cohort only as an
`EXPLORATORY` sensitivity with its full warning label.
