# Project status

## Current Batch

Batch 22.6 — Tableau worksheet visual capture completed with
`CANVAS_VISIBLE: NO` and `VISUAL_INTERACTION_NO_GO`. The existing
`Tableau - Book10` window can be activated and its menu state gives limited
worksheet-context evidence (`Sheet 1` and the listed charging data source),
but the native display capture contains only the Tableau menu bar over the
desktop wallpaper. The window-targeted capture fails because the on-screen
window reports CoreGraphics sharing state `0`; no canvas, shelves, Marks card,
Data pane or field controls can be visually grounded. No supported API
activation was retried; no Tableau workbook or authoring change was made. No
DuckDB object, raw/reference file, Crosswalk, BBSR layer, charging object,
Batch 19 export or official KPI deployment changed.

## Last completed Batch

Batch 22.6 — Tableau worksheet visual capture completed after Batch 22.5's
local GUI automation capability check and Batch 22.4's Tableau Desktop
External Client API startup-reset diagnosis,
Batch 22.3's controlled preference validation and Batch 21's
approved two-page Tableau executive overview preparation,
Batch 20's semantic model design, Batch 19's data preparation and export validation, Batch 18's
source-readiness review and Batch 17's
temporal-validity audit, Batch 16's state-level EV
stock versus charging infrastructure comparison and Batch 15's KBA FZ 27
stock, growth, geography and ownership analysis and the Batch 14 BBSR
charging infrastructure statistical analysis,
Batch 13.2's historical BBSR 2025 boundary harmonization, the Batch 13.1
owner-approved scenario, the Batch 13 charging-only layer, Batch 12 two-path
BBSR compatibility investigation, Batch 11 BBSR–KBA audit, Batch 10 reference
build, Batch 09 feasibility assessment, and Batch 08 geographic verification.

## Previous completed Batch

Batch 22.5 — Local Tableau GUI automation capability check completed before
Batch 22.6 and after Batch 22.4's Tableau Desktop External Client API
startup-reset diagnosis. It verified the current host's effective
System Events/Accessibility and Screen Recording capabilities but did not
expose a worksheet canvas.

## Earlier completed Batch

Batch 21 — approved two-page Tableau executive overview preparation completed
before Batch 22.1 and after Batch 20's semantic model design. It produced
validated presentation CSVs, a two-page implementation specification and
read-only validation, but no native workbook.

Batch 20 — Tableau semantic model and Fact/Dimension architecture design
completed before Batch 21 and after Batch 19's export validation. It produced
the separate-source architecture, relationship contracts and 59-KPI mapping.

Batch 17 — temporal validity and cross-source KPI sensitivity analysis
completed before Batch 18 and after Batch 16's state-level EV stock versus
charging infrastructure comparison and Batch 15's KBA FZ 27 stock, growth,
geography and ownership analysis.

## Historical completed Batch

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

| Batch 14 analysis outputs | 400 historical units; category counts 68 / 131 / 98 / 103; point-weighted fast share 26.08%; unweighted unit mean 31.25%; 30-point share filter excluded 0 units |
| Batch 15 national stock growth | National BEV +330,787 (+16.26%) and PHEV +103,905 (+9.25%), 2026-01-01 to 2026-07-01 |
| Batch 15 KBA regional coverage | 400 codes per snapshot; 1,200 source rows; 0 identity changes, numeric NULLs, or zero denominators |
| Batch 15 percentage-growth ranking | 377 regions eligible at January BEV >=1,000; 23 disclosed exclusions |
| Batch 15 ownership scope | FZ 27.5: commercial/private × BEV/PHEV at 16 states, Sonstige and national grain; 54 wide diagnostic rows |
| Batch 15 historical series | 33 deduplicated national observations from 2018-07-01 through 2026-07-01 |
| Batch 16 state rows | 16 distinct state rows; 0 missing or duplicated state joins |
| Batch 16 primary benchmark | 2,362,218 16-state BEVs / 211,253 points = 11.181938 BEVs per point |
| Batch 16 published-national benchmark | 2,365,047 Deutschland BEVs / 211,253 points = 11.195330 BEVs per point; includes 2,829 Sonstige BEVs |
| Batch 16 state associations | BEV stock/points Pearson 0.991; Spearman 0.985; descriptive only |
| Batch 16 deterministic outputs | 1 report + 3 CSVs; second execution byte-identical |
| Batch 17 commissioning-date quality | 117,662 rows; 0 raw NULL/blank; 0 parsing failures; 0 dates after 2026-09-30 |
| Batch 17 inclusive cutoff | 80 equipment / 136 points exactly on 2026-07-01; 2,762 equipment / 4,888 points after cutoff |
| Batch 17 survivor cohort | 114,900 equipment / 206,365 points; 152,981 normal / 53,384 fast / 39,543 >=150 / 6,335 >=350 kW |
| Batch 17 16-state ratio sensitivity | 11.181938 published vs 11.446796 survivor BEVs/point; +2.37%; survivor is not actual July infrastructure |
| Batch 17 ranking sensitivity | BEVs/point rank changed for 0 / 16 states; fast points/1,000 BEVs rank changed for 4 / 16 |
| Batch 17 KPI publication decision | BEVs/point `CONTEXT_ONLY`; power/ranking/share/correlation `EXPLORATORY_SENSITIVITY`; adequacy `NOT_SUPPORTED` |
| Batch 17 deterministic outputs | 1 report + 4 CSVs; database/source fingerprints unchanged |
| Batch 18 KPI readiness register | 59 rows; 16 `HEADLINE_READY`, 11 `HEADLINE_READY_WITH_DATES`, 8 `CONTEXT_ONLY`, 17 `EXPLORATORY`, 7 `NOT_SUPPORTED` |
| Batch 18 historical infrastructure feasibility | `BLOCKED` with current single BNetzA snapshot; commissioning cohort retained as exploratory only |
| Batch 18 Tableau readiness | Existing state, KBA-only, BBSR charging-only and temporal outputs suitable for separate extract planning; no Tableau asset created |

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
- Batch 14 read-only analyzer `scripts/14_analyze_bbsr_charging_patterns.py` with deterministic type/district CSVs and analytical report.
- Batch 14 statistical findings: type 2 has the largest absolute point and fast-point totals; type 4 has the highest within-category fast share; all-unit weighted fast share is 26.08% versus a 31.25% unweighted unit mean.
- Batch 14 KPI controls: descriptive shares, distributions, and concentration screens are not accessibility, demand, utilization, quality, or causal measures; BBSR-based BEV-to-charger ratios remain unsupported.
- Batch 15 read-only analyzer: `scripts/15_analyze_kba_ev_stock.py` with worksheet, national, state, district, and ownership diagnostics plus report `reports/batch15_kba_ev_stock_analysis.md`.
- Batch 15 safeguards: DuckDB opened read-only; all three KBA workbook fingerprints matched; no BBSR join, charging join, Crosswalk update, Trier allocation, database write, raw workbook write, or new KPI object was performed.
- Batch 15 finding: national BEV stock grew faster than PHEV stock in January–April, April–July, and January–July; all growth and penetration measures remain explicitly descriptive.
- Batch 16 read-only analyzer: `scripts/16_analyze_state_ev_charging_alignment.py` with complete state, national-reconciliation and association diagnostics plus report `reports/batch16_state_ev_charging_alignment.md`.
- Batch 16 safeguards: one charging row and one KBA vehicle row per state before joining; `Deutschland`, `Sonstige` and 400-region scopes kept separate; PHEV not double-counted inside `Hybrid insgesamt`; equipment statuses retained; maximum-per-point power definitions preserved; both snapshot dates visible.
- Batch 16 validation: exact 16-state coverage, 117,662 equipment, 211,253 points, all power bands, 0 invalid-power points, 0 duplicate/orphan/mismatched point checks, 6 source fingerprints matched, unchanged DuckDB hash, and byte-identical second execution.
- Batch 16 interpretation: cross-source ratios and correlations are exploratory/descriptive only; no infrastructure adequacy, shortage, surplus, accessibility, utilization, demand or causal claim is made.
- Batch 17 read-only analyzer: `scripts/17_analyze_temporal_kpi_validity.py` with commissioning-date audit, published/survivor cohort metrics, 16-state temporal sensitivity, KPI publication matrix and fixed-denominator vehicle-stock diagnostics.
- Batch 17 safeguards: commissioning date remains equipment-level with raw value preserved; no point activation field exists; all September statuses remain in scope; point rows use source-aware keys and maximum-per-point power classification; published and survivor perspectives remain separate.
- Batch 17 validation: 0 commissioning parsing failures, 0 future dates, 0 duplicate/orphan/mismatched points, exact KBA January/April/July and July national/16-state/`Sonstige`/400-region reconciliation, 6 source fingerprints matched, unchanged DuckDB hash, and deterministic outputs.
- Batch 17 interpretation: the full September comparison is cross-snapshot descriptive; the survivor cohort is not actual July infrastructure. BEVs per point is secondary context only, not a headline adequacy metric.
- Batch 18 readiness review: canonical statuses are `HEADLINE_READY`, `HEADLINE_READY_WITH_DATES`, `CONTEXT_ONLY`, `EXPLORATORY` and `NOT_SUPPORTED`; historical infrastructure-panel development is blocked; BBSR vehicle-stock integration remains blocked; Tableau implementation remains approval-gated.
- Batch 18 artifacts: `reports/batch18_analytics_readiness_review.md`, `reports/batch18_kpi_readiness_register.csv`, `reports/batch18_historical_data_feasibility.md`, `reports/batch18_tableau_analysis_candidates.md` and `reports/batch18_readiness_decisions.md`.

## Open issues

- All 24 provisional mappings have completed the Batch 08 evidence review; 22 aliases have direct row-level key evidence and two Trier rows remain entity-level combined-region evidence because KBA combines them. Operational status promotion still requires owner approval, and no universal KBA-code-to-AGS/ARS mapping was found.
- Historical boundary compatibility remains unknown outside the three 2026 FZ 27.15 snapshots. A boundary-vintage note and additional historical evidence are required before older or cross-product regional trends are published.
- The deployed official BBSR layer is intentionally source-grain and charging-only. Its five-row baseline covers 399 verified typed districts plus two `UNCLASSIFIED` rows (Main-Kinzig conditional-vintage and Hanau unresolved). Batch 13.1 adds a separate owner scenario with 401 classified source districts, and Batch 13.2 adds a separate historical BBSR 2025 target reconstruction with 400 target units; neither is an official BBSR 2026 classification and Path B still has no authoritative dated KBA-to-BBSR bridge. Trier code `07211` remains mixed, and no stock is allocated.
- Batch 13.2 resolves the current analytical discrepancy without revising prior layers: Kassel city is `06611000` type 1 only in the new harmonized view, while Hanau and remaining Main-Kinzig are combined to historical BBSR `06435000` type 2. Population figures are contextual evidence, not a replacement for the BBSR type rule.
- The current helper `connector_power_kw_single` does not parse multi-value power strings; the complete bands use the deployed maximum-per-point expression over `connector_power_raw`.
- The 400-district KBA total differs from the state-level Deutschland total because of the current Sonstige/reporting-structure reconciliation.
- One BNetzA coordinate falls outside a broad Germany bounding check and remains uncorrected.
- BNetzA and KBA snapshot dates are not contemporaneous, and the BNetzA register is not exhaustive.
- Batch 16 cross-source measures use KBA `2026-07-01` and BNetzA `2026-09-30`; the 16-state benchmark excludes KBA `Sonstige`, while the separate published-national benchmark includes 2,829 `Sonstige` BEVs. Neither benchmark is an adequacy measure.
- Batch 17 found no point-level activation date or historical availability field. The commissioning-date cohort is reproducible at equipment grain only; the September survivor result is not a true July snapshot, an upper/lower bound, or observed infrastructure growth.
- Batch 17 recommends BEVs per registered point only as `CONTEXT_ONLY` secondary context. Its published 16-state ratio is 11.181938 and the survivor sensitivity is 11.446796 (+2.37%); ranking stability does not establish temporal validity or adequacy.
- Batch 18 confirms that genuine historical infrastructure analysis is `BLOCKED` until multiple independently dated infrastructure snapshots, stable identity/change evidence and completeness metadata are available. The canonical register is the current publication control.
- Batch 15 validates PHEV change/growth and PHEV passenger-car penetration as descriptive source-grain measures; they remain unsuitable for sales, utilization, demand, or causal interpretation.
- Operator, city/county, payment/opening/connector, and KBA ownership/postcode/municipality analyses remain proposed pending denominator, grain, and normalization decisions.
- Tableau reporting, production BBSR/KBA compatibility, final license review, and GitHub publication are incomplete. The Batch 11 and Batch 12 audit CSVs remain non-operational; Batch 13 official category KPIs and Batch 13.1 scenario KPIs are limited to separate BNetzA source-grain charging paths.
- Tableau Desktop native authoring remains `CONDITIONAL_GO` only: Node.js/npm >=22.7.5, an isolated official source build, a local `tableau-desktop` stdio entry, a running Tableau Desktop External Client API session and a live capability/readback smoke test are still required. The official Desktop MCP does not need Accessibility or Screen Recording permissions, but its exact Tableau Desktop 2026.3 compatibility is not proven until that handshake succeeds.
- Batch 22.2 completed the isolated official build and Codex registration, but the live handshake stopped at `list-instances`: Tableau Desktop 2026.3.0 was running with `Settings.ExternalApiEnabled=0`, so no External Client API discovery file or session was available. Enabling that existing preference requires explicit owner approval; no authoring call is authorized until the read-only handshake passes.
- Batch 22.3 used the verified user domain `com.tableau.Tableau-2026.3` and key `Settings.ExternalApiEnabled`; the exact plist backup passed byte/hash validation, the integer write `0 → 1` initially passed, and Tableau reverted it to `0` during startup. Batch 22.4 confirmed that the same startup records `FreeEditionActive` and that the installed External Client API libraries are present. The report treats the startup edition/licensing gate as the confirmed immediate reset mechanism while leaving the undocumented internal product rule explicitly qualified. Both discovery locations remained absent, `list-instances` still failed, and no live fields/workbook metadata were read.
- Batch 22.4 found no matching system, ByHost, managed-preference or MDM setting, no MCP configuration cause, and no official Tableau documentation promising External Client API availability for the current Free Edition state. The supported next step is an owner decision about a paid supported Desktop configuration/support inquiry or an isolated GUI fallback; no further preference retry is authorized.
- Batch 22.5 verified that the actual local automation host is the VS Code OpenAI Codex extension's `/Users/admin/.vscode/extensions/openai.chatgpt-26.1021.22027-darwin-x64/bin/macos-x86_64/codex` process. Effective System Events/Accessibility and Screen Recording tests passed, but the blank Tableau `Book1` start pane exposed no worksheet tabs or field pane; the result is `LOCAL_AUTOMATION_PARTIAL`, not an authoring pass. The TCC database itself remained unreadable, no permission was changed, and no tab selection, field interaction, workbook save or dashboard edit was attempted.
- Batch 22.6 established that the current local screen capture route cannot see the Tableau window body: `/usr/sbin/screencapture` captured a valid display PNG, while `screencapture -l` failed for the on-screen window with CoreGraphics sharing state `0`; the exact-bounds control capture showed only wallpaper. Menu metadata indicates `Sheet 1` and a listed charging data source, but the worksheet canvas, Rows/Columns shelves, Marks card, Data pane, fields and tabs remain unavailable. The visual route is `NO-GO` under the current host; no permission change, workbook edit or API retry was made.
- CSV attachment, official 16-state map recognition, exact dashboard styling and native save/readback remain verification gates. `apply-datasource` does not import new datasource files; the approved path must validate `open-file` attachment and the resulting workbook state before real dashboard authoring.
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

Do not retry the preference write or use an alternate flag, binary edit or
security-bypass/UI route. Batch 22.6 found that the current local GUI capture
route cannot expose the Tableau window body, so screenshot-based interaction is
not safely groundable and is `NO-GO`. Obtain either an owner-approved
supported paid Desktop configuration/support answer or a separately approved
host with verified window capture before reconsidering GUI automation. Only
after `list-instances` and the read-only live workbook handshake pass, or after
a new approved GUI host verifies worksheet controls and native save/reopen,
should the two specified dashboards be authored. Official recognition of all
16 state geometries, visual review and source licensing remain mandatory. Keep
historical infrastructure-panel development, KBA-to-BBSR vehicle integration,
external publication and GitHub publication deferred until their prerequisites
exist.
Keep the official Batch 13 baseline, Batch 13.1 scenario and Batch 13.2
historical layer separate from any future KBA vehicle-stock integration.

## Last local Git commit reference

Local handoff commits are kept on `main`; no remote is configured.

## Batch 19 completed outputs

The exporter `scripts/19_prepare_tableau_data.py` opens DuckDB with
`read_only=True`, validates the source object contract and prior fingerprints,
aggregates equipment and point grains separately, and writes nine CSVs under
`data/exports/tableau/`. The extracts contain 1, 16, 400, 4, 48, 1,200, 16,
16 and 33 rows respectively. The national BNetzA totals are 117,662 equipment,
211,253 point slots, 156,155 normal points, 55,098 fast points, 40,950 points
>=150 kW, 6,950 points >=350 kW and 9,215.4173 MW declared equipment nominal
power.

The BBSR exports preserve 400 historical target units from 401 source
components, consolidate Hanau with remaining Main-Kinzig-Kreis to `06435000`
type 2, retain corrected Kassel city `06611000` type 1, and keep Trier city and
Trier-Saarburg separate. The KBA exports preserve `07211` as one
`TRIER-SAARBURG` registration region without allocation. Batch 16/17 source
outputs are reused with their existing publication statuses; no KPI status was
promoted or downgraded.

Measured validation is recorded in
[`reports/batch19_tableau_data_validation.md`](reports/batch19_tableau_data_validation.md)
and file provenance/checksums in
[`data/exports/tableau/export_manifest.json`](data/exports/tableau/export_manifest.json).

## Batch 20 completed outputs

Batch 20 produced a design-only Tableau semantic specification:

- [`docs/tableau-semantic-model.md`](docs/tableau-semantic-model.md)
- [`docs/tableau-fact-dimension-catalog.md`](docs/tableau-fact-dimension-catalog.md)
- [`docs/tableau-relationship-design.md`](docs/tableau-relationship-design.md)
- [`reports/batch20_semantic_model_validation.md`](reports/batch20_semantic_model_validation.md)
- [`reports/batch20_architecture_decision.md`](reports/batch20_architecture_decision.md)
- [`reports/batch20_kpi_model_mapping.csv`](reports/batch20_kpi_model_mapping.csv)

The recommended architecture is separate Tableau data sources backed by the
existing nine Batch 19 exports. The mapping contains exactly 59 unique KPI IDs.
Read-only validation passed for actual schemas/types, export row counts and
checksums, natural keys, state/date matches, 401-to-400 BBSR harmonization,
required baselines, source fingerprints, and unchanged DuckDB bytes. No
physical Fact/Dimension table, Tableau asset, schema change, source change,
new dataset, remote, upload or publication was created.

## Batch 21 completed outputs

Batch 21 prepared the two approved dashboard contracts from the validated
Batch 19 files. The new power-band file uses normal, fast-but-below-150,
high-power-below-350 and ultra-fast bands, which reconcile to 211,253 points.
The new equipment-status file keeps the 20 `In Wartung` records visible.

The preparation script checks all nine Batch 19 export hashes, all 12
manifest-listed source/reference/report fingerprints, the required national
figures, all 33 national history rows, exactly 16 geographic states, the
sixteen-state BEV/PHEV scope and the validated state rankings. It opens DuckDB
read-only and confirmed the unchanged hash
`5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3`.

The specification is
[`docs/tableau-executive-overview.md`](docs/tableau-executive-overview.md),
and the validation report is
[`reports/batch21_tableau_overview_validation.md`](reports/batch21_tableau_overview_validation.md).
The workbook, screenshots, map recognition result and any `.twb`/`.twbx` path
remain pending manual Tableau Desktop authoring; no public publication was
attempted.

## Batch 22.1 completed outputs

Batch 22.1 investigated the official Tableau Desktop Authoring MCP in
read-only mode and recorded a `CONDITIONAL GO` in
[`reports/batch22_1_tableau_desktop_mcp_feasibility.md`](reports/batch22_1_tableau_desktop_mcp_feasibility.md).
The report confirms that the official Desktop build exposes native worksheet,
dashboard, calculated-field, template, formatting, screenshot and workbook
save/readback tools through Tableau's local External Client API. The current
macOS project environment has Tableau Desktop 2026.3.0 installed, but no
Node.js/npm runtime, Tableau MCP configuration, running Desktop discovery
file or callable MCP tool. The report provides the minimum approval-gated
build, configuration, live smoke-test and dashboard-authoring sequence.

No package, Codex setting, macOS permission, source/reference file, DuckDB
object, export, workbook, screenshot, remote, upload or publication changed.

## Batch 22.2 setup outputs

Batch 22.2 installed the official Tableau MCP source at the isolated path
`/Users/admin/dev/tools/tableau-mcp` at tag `v5.3.0`, revision
`8c0ac37a336cd6c3dcf57f9a3dfc86b6541281f0`, using local Node.js `v22.23.4`.
`npm ci` and `npm run build:desktop` passed and produced
`build/index.desktop.js` plus `build/desktop/data/`. Codex CLI `0.163.0`
registered `tableau-desktop` with the absolute Node entrypoint and
`PRODUCT_TELEMETRY_ENABLED=false`; existing MCP entries were preserved.

The actual MCP initialized and exposed 85 tools, and headless
`list-templates` returned `trend-line-chart`. The required live
`list-instances` call failed because Tableau Desktop 2026.3.0 published no
External Client API discovery file; the read-only preference probe found
`Settings.ExternalApiEnabled=0`. The setup therefore remains
`MCP_SETUP_PARTIAL`. No authoring call, workbook, database, export, source
crosswalk, screenshot, remote, upload or publication was created or modified.
Full evidence is in
[`reports/batch22_2_tableau_mcp_setup.md`](reports/batch22_2_tableau_mcp_setup.md).

## Batch 22.3 External Client API validation outputs

Batch 22.3 performed the owner-approved, read-only/controlled validation in
[`reports/batch22_3_tableau_external_api_validation.md`](reports/batch22_3_tableau_external_api_validation.md).
The exact preference domain was `com.tableau.Tableau-2026.3`, the physical
plist was `/Users/admin/Library/Preferences/com.tableau.Tableau-2026.3.plist`,
and the key was `Settings.ExternalApiEnabled`. A timestamped backup outside
Git passed byte comparison, plist parsing and SHA-256 validation.

The integer value changed from `0` to `1` and passed immediate readback, but
Tableau Desktop 2026.3.0 reset it to `0` on launch. The observed launch PID was
`66196`; it exited gracefully. Both documented discovery directories remained
absent. Official MCP `list-instances` failed, while headless `list-templates`
returned the existing 137-template catalog. No live workbook inspection or
authoring was attempted, and the project remains
`TABLEAU_WORKBOOK_NOT_YET_CREATED`.

## Batch 22.4 External Client API diagnosis outputs

Batch 22.4 completed the required read-only diagnosis in
[`reports/batch22_4_tableau_external_api_diagnosis.md`](reports/batch22_4_tableau_external_api_diagnosis.md).
The local evidence confirms the startup reset sequence and rules out the
readable system/managed-preference and MCP-configuration alternatives. The
official Tableau source and licensing documentation review found no supported
Free Edition method for keeping `Settings.ExternalApiEnabled=1`. The official
MCP build remains unchanged and paused; the GUI fallback is feasible but
approval-gated because computer-use entries and relevant macOS permissions are
disabled. No project data, schema, export, workbook or publication changed.

## Batch 22.5 local GUI automation outputs

Batch 22.5 completed the required local permission and capability check in
[`reports/batch22_5_local_automation_capability_check.md`](reports/batch22_5_local_automation_capability_check.md).
The exact shell host was the VS Code OpenAI Codex extension's native `codex`
app-server (PID `63398` during the probe), with
`codex-code-mode-host` as its child. Read-only System Events and native
Accessibility operations succeeded against Tableau Desktop 2026.3.0, and
`/usr/sbin/screencapture` produced a valid 2560 × 1600 PNG. A TCC database
query was denied by macOS; no bypass or permission change was attempted.

Tableau was launched normally and exposed process PID `69292` and window title
`Tableau - Book1`. The AX tree visited 339 nodes and exposed menus, start-pane
controls, `New Worksheet`, `Clear Sheet` and a `Tables` outline, but no
worksheet-tab or field-pane controls. The screenshot did not show a rendered
worksheet canvas. No tab selection, worksheet creation, field drag, dashboard
edit, workbook save/reopen or data-source change was performed. Tableau was
closed normally, `Settings.ExternalApiEnabled` remained `0`, and the project
remains `TABLEAU_WORKBOOK_NOT_YET_CREATED` with result
`LOCAL_AUTOMATION_PARTIAL`.

## Batch 22.6 Tableau worksheet visual capture outputs

Batch 22.6 completed the read-only visual capture in
[`reports/batch22_6_tableau_worksheet_visual_capture.md`](reports/batch22_6_tableau_worksheet_visual_capture.md).
The existing Tableau Desktop 2026.3 process was activated without opening,
creating or editing a workbook. The current window was `Tableau - Book10`,
CoreGraphics window ID `8660`, with bounds `188,76,960,628` and on-screen
sharing state `0` (`kCGWindowSharingNone`).

The native full-display command produced a valid 2560 × 1600 PNG, but the
image showed only the Tableau menu bar over desktop wallpaper. The
window-targeted `screencapture -l 8660` call returned
`could not create image from window`, and a capture of the exact window
rectangle also contained only wallpaper. Menu metadata provided limited
worksheet-context evidence (`Window → Sheet 1` and listed
`national_charging_2026_09_30` data source), but the actual canvas, Rows and
Columns shelves, Marks card, Data pane, fields and worksheet tabs were neither
visually visible nor exposed by Accessibility. The validated result is
`CANVAS_VISIBLE: NO` and `NO-GO` for screenshot-based local GUI interaction.

No ScreenCaptureKit permission was added, no MCP retry or preference write was
performed, and no workbook, data, source, export, database object, remote,
upload or publication changed.
