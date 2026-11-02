# Project status

## Current Batch

Batch 05 — Pre-integration geographic model validation (complete; read-only design review, no permanent DuckDB changes).

## Last completed Batch

Batch 05 — Pre-integration geographic model validation and proposed permanent-layer design.

## Latest validated metrics

The latest local DuckDB validation uses BNetzA 2026-09-30 and KBA snapshots 2026-01-01, 2026-04-01, and 2026-07-01.

| Metric | Validated value |
|---|---:|
| BNetzA equipment rows | 117,662 |
| BNetzA populated charging-point slots | 211,253 |
| Declared point count | 211,253 |
| Equipment point-count mismatches | 0 |
| Equipment IDs missing or duplicated | 0 / 0 |
| Declared equipment nominal power | 9,215.42 MW |
| KBA district rows | 1,200 |
| KBA district codes per snapshot | 400 |
| July 2026 KBA district BEV stock | 2,362,218 |
| Crosswalk rows / distinct KBA codes | 401 / 400 |
| Explicit provisional mappings | 24 = 22 aliases + 2 Trier rows |
| Combined KBA code/date rows | 1,200 = 400 × 3 |

The raw connector-power parser classifies 156,155 points at or below 22 kW, 55,098 above 22 kW, 40,950 at or above 150 kW, and 6,950 at or above 350 kW. These are declared-power classifications, not utilization measures.

## Implemented components

- Source manifest and four local official XLSX inventories.
- Streaming source profiling and schema inspection.
- DuckDB raw, core, and analytics layers.
- Charging equipment and charging-point normalization.
- KBA state, district, postcode, municipality, and national-history structures.
- Versioned crosswalk CSV and Batch 03 validation report.
- Read-only named-query Batch Analysis Runner.
- English project documentation, KPI catalog, data dictionary, and geographic methodology.
- Batch 05 read-only regional power-band and aggregate-before-join validation.
- Proposed geographic-layer design with non-executed SQL definitions and backup/rollback requirements.
- Persistent AGENTS.md, changelog, and local Git configuration.

## Open issues

- Twenty-two district aliases and the two shared Trier/Trier-Saarburg source mappings (24 provisional mappings total) require authoritative geographic review.
- Permanent geographic DuckDB reference and aggregate objects have not been created.
- analytics.charging_by_state omits source_id in one equipment-to-point aggregation join and is unsafe for multi-source snapshots.
- The current helper connector_power_kw_single does not parse multi-value power strings; the complete bands use a read-only maximum-per-point expression over connector_power_raw.
- The 400-district KBA total differs from the state-level Deutschland total because of the current Sonstige/reporting-structure reconciliation.
- One BNetzA coordinate falls outside a broad Germany bounding check and remains uncorrected.
- BNetzA and KBA snapshot dates are not contemporaneous, and the BNetzA register is not exhaustive.
- Tableau reporting, BBSR enrichment, final license review, and GitHub publication are incomplete.

## Pending decisions

- Approve an authoritative geographic crosswalk or independent review.
- Decide the final display and KPI treatment of shared Trier code 07211.
- Approve any permanent DuckDB geographic layer and backup plan.
- Decide whether point-power parsing becomes a reusable view or core field.
- Approve the proposed object names, grains, source-aware joins, and quality checks in docs/geographic-layer-design.md before Batch 06 deployment work.
- Decide whether BBSR settlement typology adds value and can be reused.
- Complete source-derived extract and publication licensing review.

## Next planned work

Independent geographic review, final geographic-layer design approval, backup creation, approved permanent-layer deployment, KBA reconciliation, KPI hardening, optional BBSR assessment, Tableau extract preparation, dashboard development, and final publication review.

## Last local Git commit reference

HEAD — the local Batch 05 commit. The exact commit hash is returned in the Batch 05 handoff.
