# Germany EV Charging Analytics

## Nationwide public-charging infrastructure versus registered electric-vehicle stock

This portfolio project builds a reproducible, Germany-wide analytical foundation for comparing the published public-charging register with registered passenger-car stock. It preserves the original BNetzA, KBA, and separately versioned BBSR reference workbooks, separates charging equipment from charging points, and keeps snapshot dates visible throughout the workflow.

The current implementation is a validated local DuckDB model, a deployed still-provisional KBA geographic layer, the separate Batch 13 charging-only BNetzA-source-grain BBSR layer, a separate Batch 13.1 owner-approved 2026 analytical scenario, a separate Batch 13.2 historical BBSR 2025 boundary harmonization, the Batch 14 read-only statistical analysis of that harmonized layer, the Batch 15 read-only KBA FZ 27 stock analysis, and the Batch 17 read-only temporal-validity analysis of Batch 16 cross-source KPIs. Batch 13.2 corrects the Kassel city/county join only in its new layer and aggregates Hanau with the remaining Main-Kinzig source row; Batch 14, Batch 15, and Batch 17 do not change the official baseline, assign BBSR categories to KBA registration regions, integrate charging with KBA stock, or allocate Trier stock. Tableau Public reporting remains incomplete.

## Why this matters

Electric-vehicle adoption and charging infrastructure are measured by different official sources, at different grains, and on different dates. A useful analysis must therefore answer both “how much infrastructure is published?” and “how many vehicles are registered?”, while avoiding common errors such as counting equipment rows as charging points, summing KBA subtotals twice, or duplicating vehicle stock for the shared Trier registration region.

## Scope

- All 16 German federal states.
- BNetzA Ladesäulenregister snapshot dated 2026-09-30.
- KBA FZ 27 snapshots dated 2026-01-01, 2026-04-01, and 2026-07-01.
- BBSR Raumgliederungen-Referenzen workbook at geographic stand 2025-12-31, reduced to the four-category Kreisreferenz.
- Complete locally downloaded source workbooks are preserved under data/raw and are not committed to Git.
- Every BNetzA equipment row and populated charging-point slot is retained in DuckDB.
- KBA worksheets, footnotes, alternate breakdowns, and source rows are retained in the raw schema.

The project does not include a BBSR-to-KBA compatibility bridge, Destatis integration, charging sessions, energy delivery, utilization, queue times, reliability, real-time availability, or causal impact analysis. The Batch 13 and Batch 13.2 BNetzA-to-BBSR layers are source-grain and charging-only; they are not KBA bridges. Batch 13.1 remains an explicitly labelled owner override, while Batch 13.2 is a historical BBSR 2025 target reconstruction and does not manufacture an official 2026 Hanau classification.

## Verified local baseline

The values below are measured from the local DuckDB file and source-aware validation queries. They are not claims about all chargers in Germany.

| Measure | Value | Reference |
|---|---:|---|
| BNetzA equipment records | 117,662 | BNetzA snapshot, 2026-09-30 |
| Populated charging-point slots | 211,253 | BNetzA snapshot, 2026-09-30 |
| Retrospective survivor equipment | 114,900 | September records commissioned on or before 2026-07-01; not July infrastructure |
| Retrospective survivor point rows | 206,365 | September point rows attached to that equipment; not a historical July snapshot |
| Post-cutoff equipment / points | 2,762 / 4,888 | Commissioned after 2026-07-01; 2.35% / 2.31% of September totals |
| Declared point count reconciled to populated slots | 211,253 = 211,253 | No equipment-level mismatch in the current snapshot |
| Declared equipment nominal power | 9,215.42 MW | Sum of equipment-level kW field |
| Normal charging points, maximum declared power <=22 kW | 156,155 | 73.92% of point slots |
| Fast charging points, maximum declared power >22 kW | 55,098 | 26.08% of point slots |
| Charging points at least 150 kW | 40,950 | 19.38% of point slots |
| Charging points at least 350 kW | 6,950 | 3.29% of point slots |
| KBA district BEV stock, July 2026 | 2,362,218 | 400 district rows |
| KBA district BEV stock growth, January to July 2026 | +330,348 (+16.26%) | Same 400-district coverage |

Power classifications use the retained connector_power_raw text, split within each point row and classified by the maximum numeric value. The current normalized connector_power_kw_single field intentionally represents only a single numeric value and is null for multi-value text; it must not be used alone for the headline power totals. KBA BEV stock is registered stock, not new sales.

The state-level KBA FZ 27.2 total labelled Deutschland is 2,365,047 BEVs for July 2026. The 2,362,218 district total is the appropriate total for the 400-code district model; the difference is retained as a reconciliation issue rather than silently absorbed.

## Technology stack

- Python 3 standard-library ingestion and profiling scripts
- DuckDB 1.4.5 in the current local environment
- Tableau Public as a planned reporting layer
- Git for local version control
- GitHub as a future publication target, subject to final review and explicit approval

## Architecture and data flow

~~~mermaid
flowchart LR
    A[Official BNetzA and KBA XLSX] --> B[Download manifest and SHA-256 inventory]
    A2[Official BBSR XLSX] --> B
    B --> C[Streaming workbook profiling]
    C --> D[Read-only schema inspection]
    D --> E[DuckDB raw schema]
    E --> F[DuckDB core schema]
    F --> G[Existing analytics views]
    F --> H[Read-only batch analysis runner]
    H --> I[Versioned geographic crosswalk CSV]
    I --> J[Deployed geographic reference and analytics views]
    A2 --> L[scripts/10_build_bbsr_reference.py]
    L --> M[Versioned BBSR reference CSV and provenance]
    M --> N[Batch 13 BNetzA-to-BBSR bridge]
    N --> O[Charging-only BBSR views]
    J -. planned .-> K[Tableau Public extracts and dashboard]
~~~

The current architecture is described in [docs/architecture.md](docs/architecture.md). Batch 06 deployed the approved geographic layer to the local DuckDB file; the crosswalk itself remains provisional.

## Core analytical questions

1. How many charging equipment records and charging-point slots are present in the published BNetzA snapshot?
2. How are point-level power bands distributed across Germany and its states?
3. How has registered BEV and PHEV stock changed between the three 2026 KBA snapshots?
4. How do infrastructure counts and vehicle stock compare at state and district-registration-region level?
5. Which comparisons are supported by the source grain and dates, and which require a provisional flag?

## Current implementation status

Completed local work includes source discovery and profiling, schema inspection, lossless raw ingestion, initial core normalization, read-only validation, charging-power exploration, a 401-row BNetzA-to-KBA crosswalk, a reusable read-only batch runner, the validated Batch 06 geographic layer, the Batch 10 BBSR four-category reference build, the Batch 11 read-only compatibility audit for all 400 KBA regions, and the Batch 12 two-path BBSR compatibility investigation.

Batch 04 established the English project documentation, persistent project instructions, tracking files, safe local Git configuration, and the first local baseline commit. Batch 05 validated the pre-integration geographic model. Batch 06 deployed the approved permanent objects after a verified backup and independent validation; source workbooks and the Crosswalk CSV remained unchanged.

Batch 13 completed the approved charging-only Path A deployment: a 401-row versioned bridge, a 401-row source-grain district view, and a five-row settlement-type summary. It validated 399 verified-compatible districts, retained Main-Kinzig as a conditional-vintage unclassified row, retained Hanau as unresolved, and reconciled all national charging totals. The new layer remains separate from the existing Crosswalk and contains no KBA vehicle stock.

Batch 13.1 added a separate two-row owner-override reference, a 401-row scenario district view, and a four-row scenario category view. The scenario assigns Hanau `06415` to analytical category 1 and carries Main-Kinzig-Kreis `06435` forward as category 2. It moves the existing 585 equipment records and 991 charging points from the official baseline `UNCLASSIFIED` group into categories 1 and 2 without changing national totals. Both overrides remain explicitly non-official and are not labelled `VERIFIED_COMPATIBLE`.

Batch 13.2 independently explained the 68-versus-67 discrepancy, corrected the preserved Kassel city/county join only in a new historical layer, and deployed a versioned mapping of 401 current source components to 400 BBSR 2025 target units. Hanau and remaining Main-Kinzig are aggregated to historical BBSR `06435000` type 2; the layer reconciles to 117,662 equipment, 211,253 points, and 9,215.4173 MW. The official baseline and owner scenario remain deployed for comparison.

Batch 14 adds a read-only statistical analysis of the harmonized BBSR layer. It compares absolute infrastructure totals with within-category shares, reports unit-level distributions and weighted versus unweighted measures, identifies descriptive concentration/outlier patterns, evaluates evidence-supported versus untested explanations, and recommends a small future Tableau KPI set. It does not change DuckDB objects, add a BBSR/KBA vehicle-stock ratio, or claim that any share is accessibility, demand, utilization, or quality.

Batch 15 adds a read-only statistical analysis of the three local KBA FZ 27 releases dated 2026-01-01, 2026-04-01, and 2026-07-01. It reconciles national, 16-state, `Sonstige`, and 400-code registration-region stock; calculates BEV/PHEV growth and same-grain penetration; inspects FZ 27.5 ownership structure; evaluates postcode/municipality capabilities; deduplicates the national quarterly history; and produces a complete worksheet inventory. It uses no BBSR integration, no charging join, no new DuckDB KPI object, and no Trier allocation. January–July national stock growth is +16.26% for BEVs and +9.25% for PHEVs; the 400-region table contains 400 codes per snapshot.

Batch 16 adds a read-only state-level comparison of the July 2026 KBA passenger-car stock and the September 2026 BNetzA charging register. It pre-aggregates one validated vehicle row and one validated infrastructure row per federal state, reconciles all 16 states with `Deutschland`, `Sonstige`, and the 400 KBA registration-region scope, calculates date-labelled cross-source indicators, evaluates descriptive associations with a large-state sensitivity check, and produces deterministic CSV/report outputs. It does not modify DuckDB, raw workbooks, the geographic Crosswalk, BBSR layers, or Tableau assets. The primary comparable benchmark is 2,362,218 16-state BEVs / 211,253 registered points = 11.18 BEVs per point; the published-national benchmark is kept separate because `Deutschland` includes 2,829 `Sonstige` BEVs.

Batch 17 adds a read-only temporal-validity and sensitivity analysis for those cross-source measures. It audits the real equipment-level commissioning-date field, compares the full September publication with a retrospective September-survivor cohort commissioned on or before 2026-07-01, preserves the distinction between observed and reconstructed infrastructure, evaluates state rankings/outliers and January/April fixed-denominator illustrations, and records Tableau publication decisions. All 117,662 commissioning values parse successfully; 2,762 equipment records and 4,888 associated point rows are post-cutoff; the survivor cohort contains 114,900 equipment records and 206,365 point rows. BEVs per point is recommended as `CONTEXT_ONLY`/secondary context, not a headline adequacy KPI. No DuckDB object, raw/reference file, Crosswalk, dependency, remote, upload, or Tableau asset changed.

Not complete: a dated BBSR/KBA compatibility bridge, KBA-level BBSR classification, Tableau data preparation, dashboard development, final license review, and GitHub publication. Batch 12 Path B remains at zero strict verified KBA regions.

## Reproducibility

Run commands from the repository root. The source workbooks are downloaded or manually placed according to config/sources.json.

~~~bash
python3 scripts/00_storage_check.py
python3 scripts/01_download.py
python3 scripts/02_profile_xlsx.py
python3 scripts/03_inspect_schema.py
python3 scripts/10_build_bbsr_reference.py

.venv/bin/python scripts/04_build_geographic_crosswalk.py
.venv/bin/python scripts/batch_analysis.py --demo \
  --report reports/batch03_batch_runner_demo.md

# Approved Batch 06 deployment and independent validation
.venv/bin/python scripts/06_deploy_geographic_layer.py --json
.venv/bin/python scripts/06_validate_geographic_layer.py --json

# Batch 12 read-only two-path BBSR compatibility audit
.venv/bin/python scripts/12_audit_bbsr_integration_paths.py

# Batch 13 charging-only BBSR deployment and repeat-safe validation
.venv/bin/python scripts/13_deploy_bbsr_charging_layer.py --json

# Batch 13.1 owner-approved scenario: read-only preflight, then deployment
.venv/bin/python scripts/13_1_deploy_bbsr_scenario.py --dry-run --json
.venv/bin/python scripts/13_1_deploy_bbsr_scenario.py --json

# Batch 13.2 historical BBSR harmonization: audit, preflight, deployment
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py \
  --build-reference-only --json
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py \
  --dry-run --json
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py \
  --json

# Batch 14 read-only BBSR charging-pattern analysis
.venv/bin/python scripts/14_analyze_bbsr_charging_patterns.py --json

# Batch 15 read-only KBA FZ 27 EV-stock analysis
.venv/bin/python scripts/15_analyze_kba_ev_stock.py --json

# Batch 16 read-only state EV stock versus charging analysis
.venv/bin/python scripts/16_analyze_state_ev_charging_alignment.py --json

# Batch 17 read-only temporal KPI validity and cohort sensitivity analysis
.venv/bin/python scripts/17_analyze_temporal_kpi_validity.py --json
~~~

The DuckDB build command is documented in [docs/reproducibility.md](docs/reproducibility.md) and must only be run when a database rebuild is explicitly approved. The Batch 06 deployment is the approved exception for the permanent geographic objects and creates an ignored local backup before modification.

## Repository structure

~~~text
config/       Official source manifest
data/raw/     Local original XLSX files; ignored by Git
data/reference/
              Curated BNetzA-to-KBA and BNetzA-to-BBSR bridge/reference CSVs
data/profiles/
              Source inventories and validation JSON artifacts
docs/         English project documentation
reports/      Human-readable validation reports
scripts/      Download, profile, ingest, crosswalk, deployment, validation, and analysis code
sql/          DuckDB settings and reproducible deployment SQL
tableau/      Planned Tableau reporting notes
~~~

The local DuckDB database, virtual environment, raw workbooks, temporary files, and uncontrolled CSV exports are excluded from version control. See [.gitignore](.gitignore) and [docs/github-publication-checklist.md](docs/github-publication-checklist.md).

## Documentation index

- [Project charter](docs/project-charter.md)
- [Architecture](docs/architecture.md)
- [Data sources](docs/data-sources.md)
- [Data dictionary](docs/data-dictionary.md)
- [KPI catalog](docs/kpi-catalog.md)
- [Geographic methodology](docs/geographic-methodology.md)
- [Geographic layer design](docs/geographic-layer-design.md)
- [Data quality](docs/data-quality.md)
- [Analysis findings](docs/analysis-findings.md)
- [Reproducibility](docs/reproducibility.md)
- [Roadmap](docs/roadmap.md)
- [Decision log](docs/decisions.md)
- [GitHub publication checklist](docs/github-publication-checklist.md)
- [Phase validation reports](reports/phase01_data_profile.md), [Phase 02 schema inspection](reports/phase02_schema_inspection.md), [Phase 03 DuckDB validation](reports/phase03_duckdb_validation.md), [Batch 03 crosswalk validation](reports/batch03_crosswalk_validation.md), [Batch 06 geographic deployment](reports/batch06_geographic_deployment.md), [Batch 06.1 KPI documentation audit](reports/batch06-1_kpi_documentation_audit.md), [Batch 09 BBSR feasibility](reports/batch09_bbsr_feasibility.md), [Batch 10 BBSR reference validation](reports/batch10_bbsr_reference_validation.md), [Batch 11 BBSR/KBA compatibility audit](reports/batch11_bbsr_kba_compatibility.md), [Batch 12 two-path BBSR investigation](reports/batch12_bbsr_integration_paths.md), [Batch 13 BBSR charging-only deployment](reports/batch13_bbsr_charging_deployment.md), [Batch 13.1 owner-approved scenario](reports/batch13_1_bbsr_scenario_classification.md), [Batch 13.2 historical harmonization](reports/batch13_2_hanau_geographic_harmonization.md), [Batch 14 BBSR charging analysis](reports/batch14_bbsr_charging_analysis.md), [Batch 15 KBA EV stock analysis](reports/batch15_kba_ev_stock_analysis.md), [Batch 16 state EV/charging alignment](reports/batch16_state_ev_charging_alignment.md), and [Batch 17 temporal KPI validity](reports/batch17_temporal_kpi_validity.md)

## Important limitations

- The BNetzA published register explicitly warns that it does not represent every publicly accessible charger in Germany.
- An equipment row may contain several charging points. A charging-point slot is not a connector count.
- BNetzA infrastructure is dated 2026-09-30; the latest KBA stock snapshot is dated 2026-07-01. Ratios are not contemporaneous.
- The crosswalk has 401 BNetzA combinations and 400 KBA codes because Trier city and Trier-Saarburg share code 07211. Charging metrics must be aggregated by KBA code before joining vehicle stock.
- Twenty-two aliases and the two shared Trier source mappings (24 provisional mappings total) are provisional local-snapshot mappings pending authoritative review.
- The BBSR reference uses the 2025 geographic stand and contains 400 Kreis rows / 362 Kreisregion keys. Batch 13 uses it only in a dated source-grain charging enrichment: 399 verified-compatible rows are classifiable, while Main-Kinzig is conditional-vintage and Hanau unresolved in `UNCLASSIFIED`. It is not a KBA registration-region classification; Trier city/Trier-Saarburg retain types 1 and 3 separately, and Path B remains 0 strict verified KBA regions.
- Batch 13.1 is a separate owner-approved analytical scenario, not an official BBSR 2026 publication. Hanau `06415` is category 1 by explicit owner assumption, and Main-Kinzig `06435` carries forward BBSR 2025 type 2 with the 2026 Hanau-separation caveat. The official Batch 13 five-row summary remains unchanged and available for comparison.
- Batch 13.2 is a historical BBSR 2025 target reconstruction, not an official 2026 Hanau classification. It corrects Kassel city to BBSR `06611000` type 1, combines Hanau and remaining Main-Kinzig into historical BBSR `06435000` type 2, preserves both source dates, and leaves the official Batch 13/13.1 and KBA objects unchanged.
- Batch 14 is a descriptive statistical analysis of that harmonized layer. Its category shares, weighted/unweighted comparisons, concentration measures, and outlier rankings are not accessibility, demand, utilization, quality, or causal KPIs. The report uses a 30-point minimum only as an exploratory share-ranking stability filter.
- Batch 15 is a descriptive analysis of registered stock. Its growth measures are snapshot-to-snapshot stock changes, not registrations or sales. The 400-region denominator excludes the national `Sonstige` residual; FZ 27.5 ownership totals preserve unknown/implausible holder-group residuals; FZ 27.16/27.17 contain missing cells; and the exploratory regional percentage-growth ranking excludes 23 regions below a 1,000-January-BEV baseline.
- Batch 16 compares KBA stock dated 2026-07-01 with BNetzA infrastructure dated 2026-09-30. Its BEVs-per-point, points-per-1,000-BEVs, power-mix-per-1,000-BEVs, share-gap and correlation measures are exploratory cross-snapshot descriptions, not adequacy, shortage, surplus, accessibility, utilization, demand, or causal KPIs. The primary benchmark uses the 16-state sum; the published-national benchmark includes `Sonstige` BEVs and is reported separately.
- Batch 17 confirms that all current equipment commissioning dates parse, but commissioning is equipment-level and does not provide point activation or historical availability. The published September denominator and the retrospective survivor cohort are different analytical perspectives; the latter is not actual July infrastructure. The 2.35% equipment / 2.31% point post-cutoff share produces a +2.37% national 16-state BEVs-per-point sensitivity, so the ratio remains secondary context rather than a headline adequacy KPI.
- The deployed analytics.charging_by_state view uses source_id and equipment Excel row in both the point aggregation and join. The current database still contains one BNetzA infrastructure snapshot; future multi-snapshot loads require re-running the same source-aware validations.
- No source supports utilization, sessions, energy delivered, queue times, reliability, or causality.

## Roadmap

The next stages are a dated KBA compatibility bridge and mixed-region treatment, KPI hardening, Tableau extract preparation, dashboard development, final quality and licensing review, and only then an explicitly approved GitHub publication. The current BBSR layer remains source-grain and must not be reinterpreted as KBA integration.

Code is covered by the existing MIT LICENSE. Official source data retain the licenses and attribution requirements declared in the source manifest; redistribution and final publication rights require a separate review.
