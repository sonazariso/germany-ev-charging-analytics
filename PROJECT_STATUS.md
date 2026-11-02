# Project status

## Current Batch

Batch 13.2 — historical BBSR 2025 boundary harmonization (complete; independent
68-versus-67 audit, official Hanau boundary evidence, corrected Kassel
city/county mapping in a new layer, 401-row source-component reference,
400-row historical target view, and four-row harmonized summary deployed and
independently validated). The official Batch 13 baseline and Batch 13.1
owner-approved scenario remain unchanged; no KBA stock join, KBA
classification, Crosswalk change, or Trier allocation was made.

## Last completed Batch

Batch 13.2 — historical BBSR 2025 boundary harmonization completed after the
Batch 13.1 owner-approved scenario, Batch 13 charging-only layer, Batch 12
two-path compatibility investigation, Batch 11 BBSR–KBA audit, Batch 10
reference build, Batch 09 feasibility assessment, and Batch 08 geographic
verification.

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
| BBSR Kreis rows / distinct Kreisregion keys | 400 / 362 |
| BBSR compact type row counts | 68 / 131 / 98 / 103 for codes 1 / 2 / 3 / 4 |
| Batch 12 Path A statuses | 399 verified / 1 conditional vintage / 1 unresolved / 0 mixed / 0 conflicting |
| Batch 12 Path A verified coverage | 117,077 / 117,662 equipment = 99.502813%; 210,262 / 211,253 points = 99.530894% |
| Batch 12 Path B statuses | 0 exact / 0 homogeneous / 1 mixed / 2 vintage / 397 unresolved / 0 conflicting |
| Strict KBA-to-BBSR classification coverage | 0 KBA regions / 0 charging points / 0 July BEVs |
| Batch 13 BNetzA-to-BBSR bridge | 401 rows = 399 verified / 1 conditional vintage / 1 unresolved; 399 typed / 2 unclassified |
| Batch 13 unclassified charging coverage | 585 equipment / 991 points = 0.497187% / 0.469106% of national totals |
| Batch 13 BBSR category summary | 5 rows; points and all national charging bands reconcile |
| Batch 13.1 scenario category districts | 68 / 132 / 98 / 103 for codes 1 / 2 / 3 / 4; 401 total; 0 unclassified |
| Batch 13.1 owner override contributions | Hanau 146 equipment / 251 points; Main-Kinzig 439 / 740; 585 / 991 moved from official baseline `UNCLASSIFIED` |
| Batch 13.2 historical target units | 400 BBSR 2025 targets from 401 current BNetzA source components; type counts 68 / 131 / 98 / 103 |
| Batch 13.2 Hanau/Main-Kinzig target | Historical BBSR `06435000`, type 2; 585 equipment / 991 points; no official 2026 Hanau type claimed |
| Batch 13.2 Kassel correction | City `06611000`, type 1; county `06633000`, type 2; official Batch 13 bridge preserved unchanged |

The deployed maximum-per-point parser classifies 156,155 points at or below 22 kW, 55,098 above 22 kW, 40,950 at or above 150 kW, and 6,950 at or above 350 kW. These are declared-power classifications, not utilization measures.

## Implemented components

- Source manifest and four primary plus one BBSR reference XLSX inventory.
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
- Batch 07 authoritative evidence review of all 24 provisional crosswalk rows.
- Batch 07 evidence classification: 22 independently supported row/entity mappings, 2 partially supported shared Trier-region mappings, and 0 unresolved row identities; all 24 remain operationally provisional.
- Batch 07 Trier finding: KBA FZ 27.15 reports 7,869 July 2026 BEVs for combined row `07211 TRIER-SAARBURG`; Destatis separately identifies Trier city `07211` and Trier-Saarburg `07235`.
- Batch 08 geographic code verification report with a complete 22-alias evidence matrix, dated Hanau checks, Trier stock treatment, source limitations, and owner decisions.
- Batch 08 finding: all 22 aliases have direct row-level five-digit key evidence, but no universal KBA-to-AGS/ARS equivalence was found; the two Trier rows remain entity-level combined-region evidence and all 24 operational statuses remain provisional.
- Batch 08 finding: Hanau and Main-Kinzig-Kreis are separate in BNetzA 2026-09-30 and KBA FZ 27.15 on all three 2026 dates; no current coverage mismatch was measured.
- Batch 09 BBSR feasibility report: official four-category BBSR reference workbook identified; 400 Kreis rows, 362 Kreisregion keys, compact codes 1–4, licensing, Umsteigeschlüssel, strategy comparison, and KPI suitability documented without integration.
- Batch 09 finding: a read-only five-digit prefix screen found 399 intersections between the 400 July 2026 KBA codes and the BBSR 2025 Kreis table; Hanau `06415` is absent from the 2025 BBSR vintage, Trier-Saarburg `07235` is absent from KBA's 400-code table, and KBA `07211` is a mixed BBSR-type registration region.
- Batch 10 BBSR reference: official 2025 workbook preserved with source/derived checksums; six sheets inspected; deterministic 400-row CSV built from Kreisreferenz with 362 Kreisregion keys and 36 multi-district groups; source rows retained without KBA assignment.
- Batch 10 BBSR compatibility review: Hanau remains absent from the 2025 BBSR vintage; Main-Kinzig-Kreis is type 2; Trier city is type 1 and Trier-Saarburg type 3 in separate rows; no shared KBA stock is allocated.
- Batch 11 BBSR/KBA compatibility audit: all 400 KBA regions are represented in a deterministic non-operational output; no `EXACT` or `HOMOGENEOUS_COMPOSITE` status is supported without an authoritative dated bridge; Trier is `MIXED`, Hanau/Main-Kinzig are `VINTAGE_CONFLICT`, and the remaining 397 regions are `UNRESOLVED`.
- Batch 11 coverage: status denominators reconcile to 211,253 charging points and 2,362,218 July BEVs; unresolved rows remain in the denominator and no BBSR category KPI is calculated.
- Batch 11 reproducibility: read-only DuckDB integrity checks, source fingerprints, syntax checks, deterministic repeat, and audit CSV coverage all passed.
- Batch 12 two-path BBSR investigation: Path A retained all 401 BNetzA source districts and found 399 verified-compatible rows, one Main-Kinzig vintage condition, and one unresolved Hanau row; Path B retained all 400 KBA regions and found no strict verified classification coverage.
- Batch 12 Path A coverage: verified rows represent 117,077 equipment records and 210,262 charging points; the result is conditional, charging-only, source-grain descriptive evidence and not a production BBSR mapping.
- Batch 12 Path B finding: KBA `07211` remains the mixed Trier/Trier-Saarburg registration region with 503 charging points and 7,869 July BEVs counted once; no stock allocation was made.
- Batch 12 official-resource review: Destatis, BBSR, Federal Employment Agency, KBA, Hessen, and Trier documentation was reviewed; no universal dated KBA-to-AGS/ARS/KRS/BBSR bridge was verified.
- Batch 12 reproducibility: read-only DuckDB inspection, source fingerprints, syntax checks, deterministic repeat, denominator reconciliation, and documentation-link checks passed.
- Batch 13 deployment: the separate source-grain bridge, charging district view, and five-row category summary were deployed after a verified ignored backup; a second execution was repeat-safe; national charging totals and all category denominators reconcile.
- Batch 13 safeguards: Main-Kinzig settlement type remains NULL, Hanau remains unresolved/NULL, Trier city and county remain separate, no KBA vehicle-stock join was created, and all four existing KBA/state objects match the pre-deployment backup.
- Batch 13.1 deployment: the two-row owner-override reference, 401-row scenario district view, and four-row category view were deployed after a verified ignored backup; a second execution was idempotent; scenario totals reconcile and no scenario district is unclassified.
- Batch 13.1 safeguards: Hanau category 1 is explicitly an owner-approved analytical assumption, not an official BBSR 2025/2026 classification; Main-Kinzig category 2 is a historical BBSR 2025 carry-forward with a 2026 Hanau-separation caveat; both overrides remain `official_bbsr_verification = false`.
- Batch 13.2 audit and deployment: strict and semantic bidirectional anti-joins identified the Kassel alias/join error and Hanau's true vintage difference; official Hessian boundary evidence supported the historical Hanau-plus-remaining-Main-Kinzig union; the new versioned reference and views passed national reconciliation and repeat-safe deployment.
- Batch 13.2 safeguards: the new layer uses raw BBSR `SLK2025` city/county form, corrects Kassel only in the new layer, keeps BNetzA `2026-09-30` and BBSR `2025-12-31` visible, does not manufacture an official 2026 Hanau type, and does not reference KBA vehicle stock.
- Batch 13.2 artifacts: `reference.bnetza_bbsr_historical_harmonization_2025`, `analytics.charging_by_bbsr_district_2025_harmonized`, `analytics.charging_by_bbsr_type_2025_harmonized`, the deterministic 401-row reference CSV/manifest, and the full deployment report.
- Persistent AGENTS.md, changelog, and local Git configuration.

## Open issues

- All 24 provisional mappings have completed the Batch 08 evidence review; 22 aliases have direct row-level key evidence and two Trier rows remain entity-level combined-region evidence because KBA combines them. Operational status promotion still requires owner approval, and no universal KBA-code-to-AGS/ARS mapping was found.
- Historical boundary compatibility remains unknown outside the three 2026 FZ 27.15 snapshots. A boundary-vintage note and additional historical evidence are required before older or cross-product regional trends are published.
- The deployed official BBSR layer is intentionally source-grain and charging-only. Its five-row baseline covers 399 verified typed districts plus two `UNCLASSIFIED` rows (Main-Kinzig conditional-vintage and Hanau unresolved). Batch 13.1 adds a separate owner scenario with 401 classified source districts, and Batch 13.2 adds a separate historical BBSR 2025 target reconstruction with 400 target units; neither is an official BBSR 2026 classification and Path B still has no authoritative dated KBA-to-BBSR bridge. Trier code `07211` remains mixed, and no stock is allocated.
- Batch 13.2 resolves the current analytical discrepancy without revising prior layers: Kassel city is `06611000` type 1 only in the new harmonized view, while Hanau and remaining Main-Kinzig are combined to historical BBSR `06435000` type 2. Population figures are contextual evidence, not a replacement for the BBSR type rule.
- The current helper `connector_power_kw_single` does not parse multi-value power strings; the complete bands use the deployed maximum-per-point expression over `connector_power_raw`.
- The 400-district KBA total differs from the state-level Deutschland total because of the current Sonstige/reporting-structure reconciliation.
- One BNetzA coordinate falls outside a broad Germany bounding check and remains uncorrected.
- BNetzA and KBA snapshot dates are not contemporaneous, and the BNetzA register is not exhaustive.
- PHEV change/growth and PHEV passenger-car penetration are defined as candidates but remain unvalidated and require owner approval.
- Operator, city/county, payment/opening/connector, and KBA ownership/postcode/municipality analyses remain proposed pending denominator, grain, and normalization decisions.
- Tableau reporting, production BBSR/KBA compatibility, final license review, and GitHub publication are incomplete. The Batch 11 and Batch 12 audit CSVs remain non-operational; Batch 13 official category KPIs and Batch 13.1 scenario KPIs are limited to separate BNetzA source-grain charging paths.
- The preserved ignored `.venv` has historical absolute paths in its activation scripts and `pip` entry-point shebangs; `.venv/bin/python` and `.venv/bin/python -m pip` work, but the environment requires explicit repair or recreation in a future approved task.

## Pending decisions

- Decide whether and how to promote the 22 row/entity-supported aliases while retaining explicit KBA-versus-AGS/ARS terminology.
- Decide the final display treatment of shared Trier code 07211; preserve the combined KBA registration-region interpretation unless direct allocation evidence is approved.
- Decide whether to require a dated historical-boundary compatibility note and additional pre-2026 KBA snapshots before publishing historical or cross-product regional trends.
- Decide whether point-power parsing becomes a reusable core field rather than remaining in the deployed geographic view.
- Approve or defer the candidate KPI domains recorded in the Batch 06.1 audit, including PHEV change/growth, city/county, operator, descriptive source fields, and KBA ownership/postcode/municipality analyses.
- Approve a dated BBSR/KBA compatibility bridge, the `mixed_or_unresolved` and `vintage_mismatch` statuses, Hanau treatment, and any future KBA-level BBSR/Tableau use before integration.
- Approve whether new authoritative evidence can promote any Batch 11 audit rows to `EXACT` or `HOMOGENEOUS_COMPOSITE`; preserve the no-allocation rule for Trier and the vintage-conflict rule for Hanau/Main-Kinzig.
- Preserve the deployed labelled source-grain charging-only view and review whether a later BBSR vintage is needed for Main-Kinzig/Hanau category comparisons.
- Decide whether a post-2026 BBSR reference is required for an official current-boundary classification or public Hanau/Main-Kinzig comparison; the deployed Batch 13.2 historical comparison remains explicitly vintage-labelled. Separately decide whether to commission a product-specific dated KBA-to-AGS/ARS/KRS bridge; do not approve a universal prefix rule.
- Reaffirm that KBA `07211` remains the combined Trier/Trier-Saarburg display region and that its 7,869 July BEVs are not allocated between BBSR rows.
- Decide whether historical KBA snapshots are required before publishing pre-2026 or cross-vintage regional trends.
- Approve any new source download, future DuckDB object, Tableau enrichment, or BBSR KPI separately; none is authorized by Batch 12.
- Complete source-derived extract and publication licensing review.
- Keep the owner-approved scenario visibly separate from the official BBSR 2025 baseline in every downstream report; do not relabel Hanau as an official BBSR 2026 type.

## Next planned work

Owner review of the Path B bridge gap, historical-boundary recommendation, KBA
reconciliation, KPI hardening, Tableau extract preparation, dashboard
development, and final publication review. Keep the official Batch 13 baseline
and Batch 13.1 scenario separate from any future KBA vehicle-stock integration.

## Last local Git commit reference

The Batch 13.2 commit is recorded in Git history. No remote is configured.
