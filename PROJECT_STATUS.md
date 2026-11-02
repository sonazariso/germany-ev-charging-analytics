# Project status

## Current Batch

Batch 06.2 — local project relocation (complete; the complete project is under the established `dev` root, the private Persian catalog is in a sibling directory outside Git, and post-move integrity validation passed; no data or database changes).

## Last completed Batch

Batch 06.2 — local project relocation completed after the Batch 06.1 KPI documentation audit.

## Latest validated metrics

The latest local DuckDB validation uses BNetzA 2026-09-30 and KBA snapshots 2026-01-01, 2026-04-01, and 2026-07-01.

| Metric | Validated value |
|---|---:|
| BNetzA equipment rows | 117,662 |
| BNetzA populated charging-point slots | 211,253 |
| Declared point count | 211,253 |
| Equipment point-count mismatches | 0 |
| Orphan charging points | 0 |
| Duplicate equipment/point keys | 0 / 0 |
| Declared equipment nominal power | 9,215.4173 MW |
| KBA district rows | 1,200 |
| KBA district codes per snapshot | 400 |
| July 2026 KBA district BEV stock | 2,362,218 |
| Crosswalk rows / distinct KBA codes | 401 / 400 |
| Explicit provisional mappings | 24 = 22 aliases + 2 Trier rows |
| Combined KBA code/date rows | 1,200 = 400 × 3 |

The deployed maximum-per-point parser classifies 156,155 points at or below 22 kW, 55,098 above 22 kW, 40,950 at or above 150 kW, and 6,950 at or above 350 kW. These are declared-power classifications, not utilization measures.

## Implemented components

- Source manifest and four local official XLSX inventories.
- Streaming source profiling and schema inspection.
- DuckDB raw, core, reference, and analytics layers.
- Charging equipment and charging-point normalization.
- KBA state, district, postcode, municipality, and national-history structures.
- Versioned crosswalk CSV and Batch 03 validation report.
- Read-only named-query Batch Analysis Runner.
- English project documentation, KPI catalog, data dictionary, and geographic methodology.
- Batch 05 read-only regional power-band and aggregate-before-join validation.
- Batch 06 permanent `reference.bnetza_kba_district_crosswalk_2026` table.
- Batch 06 `analytics.charging_by_kba_district_2026_09_30` regional view.
- Batch 06 `analytics.kba_district_charging_vs_bev_2026` combined view.
- Source-aware `analytics.charging_by_state` view with unchanged baseline metrics.
- Reproducible deployment SQL, controlled deployment script, independent validator, and verified ignored backup.
- Batch 06.1 English KPI documentation audit and comparison report.
- Batch 06.1 status vocabulary separating validated, provisional, exploratory, not-yet-validated, proposed, and unsupported measures.
- Private Persian KPI reference maintained outside the Git worktree.
- Batch 06.2 complete local relocation with before/after inventory and hash verification.
- Batch 06.2 post-relocation database, backup, crosswalk, Git, and Python/DuckDB runtime checks.
- Local DBeaver connection/output settings and the VS Code workspace record updated to the relocated project outside Git.
- Persistent AGENTS.md, changelog, and local Git configuration.

## Open issues

- Twenty-two district aliases and the two shared Trier/Trier-Saarburg source mappings (24 provisional mappings total) require authoritative geographic review.
- The current helper `connector_power_kw_single` does not parse multi-value power strings; the complete bands use the deployed maximum-per-point expression over `connector_power_raw`.
- The 400-district KBA total differs from the state-level Deutschland total because of the current Sonstige/reporting-structure reconciliation.
- One BNetzA coordinate falls outside a broad Germany bounding check and remains uncorrected.
- BNetzA and KBA snapshot dates are not contemporaneous, and the BNetzA register is not exhaustive.
- PHEV change/growth and PHEV passenger-car penetration are defined as candidates but remain unvalidated and require owner approval.
- Operator, city/county, payment/opening/connector, and KBA ownership/postcode/municipality analyses remain proposed pending denominator, grain, and normalization decisions.
- Tableau reporting, BBSR enrichment, final license review, and GitHub publication are incomplete.
- The preserved ignored `.venv` has historical absolute paths in its activation scripts and `pip` entry-point shebangs; `.venv/bin/python` and `.venv/bin/python -m pip` work, but the environment requires explicit repair or recreation in a future approved task.

## Pending decisions

- Complete authoritative review of the provisional crosswalk and decide the final display treatment of shared Trier code 07211.
- Decide whether point-power parsing becomes a reusable core field rather than remaining in the deployed geographic view.
- Approve or defer the candidate KPI domains recorded in the Batch 06.1 audit, including PHEV change/growth, city/county, operator, descriptive source fields, and KBA ownership/postcode/municipality analyses.
- Decide whether BBSR settlement typology adds value and can be reused.
- Complete source-derived extract and publication licensing review.

## Next planned work

Owner review of candidate KPI domains, independent geographic review, KBA reconciliation, KPI hardening, optional BBSR assessment, Tableau extract preparation, dashboard development, and final publication review.

## Last local Git commit reference

The Batch 06.2 local commit hash is returned in the handoff; no remote is configured.
