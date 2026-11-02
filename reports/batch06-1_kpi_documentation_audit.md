# Batch 06.1 — KPI documentation audit

## Objective and scope

The objective was to compare the English KPI catalog with the agreed project metric domains and the validated local evidence, repair missing documentation without changing analytical objects, and create a separate Persian reference for the project owner.

Scope was documentation only:

- Read the governing instructions, project status, English project documents, prior batch reports, and local source-derived validation evidence.
- Review the 20 existing numbered KPI definitions and 21 grouped coverage entries across the 16 requested domains.
- Check formulas, numerators, denominators, geographic grain, source/reference dates, limitations, and status labels.
- Add explicit definitions for validated state/district distribution and data-quality measures.
- Record candidate domains as `DEFINED BUT NOT VALIDATED`, `EXPLORATORY`, or `PROPOSED — REQUIRES APPROVAL` rather than presenting them as approved KPIs.
- Create the Persian document outside the Git worktree.

No source workbook, DuckDB object, Crosswalk CSV, raw data file, or database value was modified.

## Evidence basis

The review used:

- `docs/kpi-catalog.md`
- `docs/analysis-findings.md`
- `docs/geographic-methodology.md`
- `docs/data-quality.md`
- `docs/data-dictionary.md`
- `docs/decisions.md`
- `PROJECT_STATUS.md`
- `reports/phase03_duckdb_validation.md`
- `reports/batch03_crosswalk_validation.md`
- `reports/batch05_preintegration_review.md`
- `reports/batch06_geographic_deployment.md`
- The local DuckDB file opened with `read_only=True` for a descriptive field inventory.

The read-only inventory confirmed source support for operator, payment, opening-hours, connector, postcode, and municipality fields. These observations are evidence of field availability, not approval or independent KPI validation.

| Field or table | Read-only observation |
|---|---:|
| `core.charging_equipment` rows | 117,662 |
| Distinct non-null `operator_name` values | 11,790 |
| `core.charging_equipment` rows with a non-empty `payment_methods` value | 117,662; source placeholders remain possible |
| Distinct non-empty `payment_methods` raw strings | 1,414 |
| Distinct `connector_types` raw values | 64 point-level values |
| Distinct equipment `postal_code` values | 7,315 |
| KBA postcode rows across three dates | 24,586 |
| KBA municipality rows across three dates | 32,229 |
| KBA municipality rows flagged `possible_total_row` | 0 in the current normalized table |

## Coverage comparison

| KPI or domain | English catalog status | Evidence | Missing definition or control | Recommended action |
|---|---|---|---|---|
| Equipment and point counts | VALIDATED | Core tables; Batch 06 | None | Retain separate grains |
| Normal, fast, >=150 kW, and >=350 kW points/shares | VALIDATED | Batch 05/06 regional validation | None | Recheck parser for future snapshots |
| Nominal power and equipment status | VALIDATED | Phase 03 and Batch 06 | None | Aggregate nominal power at equipment grain |
| State distribution | VALIDATED | 16-state `analytics.charging_by_state` result | Definition was implicit | Use new explicit catalog entry |
| KBA district distribution | VALIDATED arithmetic; PROVISIONAL geography | 400-row deployed regional view | Official review of 24 provisional mappings | Keep flags and review before public ranking |
| BEV stock, change, and growth | VALIDATED | Existing catalog definitions 12, 14, 15 | None at approved 400-district grain | Retain same-grain/date controls |
| PHEV stock | VALIDATED | Existing catalog definition 13; Batch 06 | None for stock | Retain |
| PHEV change and growth | DEFINED BUT NOT VALIDATED | Same KBA fields and dates | No independent approved validation | Owner approval and like-for-like validation |
| BEV passenger-car penetration | VALIDATED | FZ 27.15 denominator | None where `passenger_cars` is used | Retain denominator warning |
| PHEV passenger-car penetration | DEFINED BUT NOT VALIDATED | FZ 27.15 fields exist | No approved catalog entry or result | Treat as candidate |
| BEVs per charging point | PROVISIONAL | Deployed combined view | Cross-snapshot dates and provisional geography | Descriptive only; not utilization |
| Fast/HPC mix versus BEV growth | EXPLORATORY (PROVISIONAL) | Existing definitions 18/19 | Paired measures, not causal KPI | Keep exploratory |
| City/county comparison | PROPOSED — REQUIRES APPROVAL | Crosswalk admin-type fields | Comparison grain and collision handling | Approve and validate separately |
| Operator breakdown | PROPOSED — REQUIRES APPROVAL | `operator_name` field | Normalization and denominator | Approve raw versus normalized names |
| Commissioning history | VALIDATED descriptive distribution | Existing definition 11 | None for cohort profile | Do not call installation flow |
| Payment/opening/connector distributions | PROPOSED — REQUIRES APPROVAL | Core descriptive fields | Tokenization and multi-label denominator | Approve descriptive treatment |
| Ownership/postcode/municipality analyses | PROPOSED — REQUIRES APPROVAL | KBA FZ 27.16/27.17 tables | Ownership denominator and alternative-grain controls | Define one grain and validate |
| Crosswalk verification and Trier treatment | VALIDATED arithmetic; PROVISIONAL official geography | Batch 03/05/06 | Authoritative review outstanding | Aggregate to code before stock join |
| BBSR enrichment | PROPOSED — REQUIRES APPROVAL | Roadmap/methodology only | No source, vintage, method, or license decision | Do not download yet |
| Data-quality metrics | VALIDATED | Data-quality and deployment reports | Not previously grouped in catalog | Use new quality section |
| Real-time/causal KPIs | UNSUPPORTED BY CURRENT SOURCES | Charter, data dictionary, Batch 06 | Required fields do not exist | Keep excluded |

The catalog’s existing 20 numbered KPI definitions remain unchanged in formula and current validation status, except that the two comparison definitions and the combined-ranking qualifier now explicitly use the `EXPLORATORY (PROVISIONAL)` label.

## Changes made

- Expanded the status vocabulary in `docs/kpi-catalog.md` to distinguish `VALIDATED`, `PROVISIONAL`, `EXPLORATORY`, `DEFINED BUT NOT VALIDATED`, `PROPOSED — REQUIRES APPROVAL`, and `UNSUPPORTED BY CURRENT SOURCES`.
- Added the Batch 06.1 coverage audit matrix to the English catalog.
- Added explicit validated definitions for state infrastructure distribution and KBA district infrastructure distribution.
- Added a catalog section for equipment/point reconciliation, key uniqueness, power-parser coverage, crosswalk coverage, KBA key uniqueness, and the known coordinate exception.
- Added candidate definitions with formulas and controls for PHEV change/growth, PHEV passenger-car share, administrative city/county comparison, operator, descriptive source fields, and KBA ownership/postcode/municipality analyses.
- Preserved the BBSR item as an optional, unintegrated future enrichment requiring approval.
- Expanded the unsupported-metrics section so static status/opening fields are not confused with uptime or real-time availability.

No KPI definition was promoted to VALIDATED solely because its source field exists.

## Remaining decisions and unresolved issues

- Owner approval is required before PHEV change/growth or PHEV passenger-car share becomes a published KPI.
- Owner approval is required for city/county display grain, operator-name normalization, payment/opening/connector tokenization, and KBA ownership/postcode/municipality denominators.
- The 22 alias mappings and two shared Trier mappings still need authoritative geographic review.
- BBSR remains outside the current source inventory and implementation.
- Utilization, energy, sessions, queue, reliability, real-time availability, sales, and causal adoption remain unsupported.

## Validation status

Validation commands and their results are recorded in the Batch handoff. Documentation checks must include Markdown link resolution, `git diff --check`, a read-only database inventory, `git status`, and a review of unstaged/staged paths. No remote was added and nothing was uploaded or published.
