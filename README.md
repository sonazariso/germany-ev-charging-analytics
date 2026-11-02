# Germany EV Charging Analytics

## Nationwide public-charging infrastructure versus registered electric-vehicle stock

This portfolio project builds a reproducible, Germany-wide analytical foundation for comparing the published public-charging register with registered passenger-car stock. It preserves the original BNetzA and KBA workbooks, separates charging equipment from charging points, and keeps snapshot dates visible throughout the workflow.

The current implementation is a validated local DuckDB model plus a deployed, still-provisional geographic analytics layer. Tableau Public reporting and BBSR enrichment are not complete.

## Why this matters

Electric-vehicle adoption and charging infrastructure are measured by different official sources, at different grains, and on different dates. A useful analysis must therefore answer both “how much infrastructure is published?” and “how many vehicles are registered?”, while avoiding common errors such as counting equipment rows as charging points, summing KBA subtotals twice, or duplicating vehicle stock for the shared Trier registration region.

## Scope

- All 16 German federal states.
- BNetzA Ladesäulenregister snapshot dated 2026-09-30.
- KBA FZ 27 snapshots dated 2026-01-01, 2026-04-01, and 2026-07-01.
- Complete locally downloaded source workbooks are preserved under data/raw and are not committed to Git.
- Every BNetzA equipment row and populated charging-point slot is retained in DuckDB.
- KBA worksheets, footnotes, alternate breakdowns, and source rows are retained in the raw schema.

The project does not currently include Destatis, BBSR, charging sessions, energy delivery, utilization, queue times, reliability, real-time availability, or causal impact analysis.

## Verified local baseline

The values below are measured from the local DuckDB file and source-aware validation queries. They are not claims about all chargers in Germany.

| Measure | Value | Reference |
|---|---:|---|
| BNetzA equipment records | 117,662 | BNetzA snapshot, 2026-09-30 |
| Populated charging-point slots | 211,253 | BNetzA snapshot, 2026-09-30 |
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
    B --> C[Streaming workbook profiling]
    C --> D[Read-only schema inspection]
    D --> E[DuckDB raw schema]
    E --> F[DuckDB core schema]
    F --> G[Existing analytics views]
    F --> H[Read-only batch analysis runner]
    H --> I[Versioned geographic crosswalk CSV]
    I --> J[Deployed geographic reference and analytics views]
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

Completed local work includes source discovery and profiling, schema inspection, lossless raw ingestion, initial core normalization, read-only validation, charging-power exploration, a 401-row BNetzA-to-KBA crosswalk, a reusable read-only batch runner, and the validated Batch 06 geographic layer.

Batch 04 established the English project documentation, persistent project instructions, tracking files, safe local Git configuration, and the first local baseline commit. Batch 05 validated the pre-integration geographic model. Batch 06 deployed the approved permanent objects after a verified backup and independent validation; source workbooks and the Crosswalk CSV remained unchanged.

Not complete: authoritative geographic verification, independent crosswalk review, BBSR suitability assessment, Tableau data preparation, dashboard development, final license review, and GitHub publication.

## Reproducibility

Run commands from the repository root. The source workbooks are downloaded or manually placed according to config/sources.json.

~~~bash
python3 scripts/00_storage_check.py
python3 scripts/01_download.py
python3 scripts/02_profile_xlsx.py
python3 scripts/03_inspect_schema.py

.venv/bin/python scripts/04_build_geographic_crosswalk.py
.venv/bin/python scripts/batch_analysis.py --demo \
  --report reports/batch03_batch_runner_demo.md

# Approved Batch 06 deployment and independent validation
.venv/bin/python scripts/06_deploy_geographic_layer.py --json
.venv/bin/python scripts/06_validate_geographic_layer.py --json
~~~

The DuckDB build command is documented in [docs/reproducibility.md](docs/reproducibility.md) and must only be run when a database rebuild is explicitly approved. The Batch 06 deployment is the approved exception for the permanent geographic objects and creates an ignored local backup before modification.

## Repository structure

~~~text
config/       Official source manifest
data/raw/     Local original XLSX files; ignored by Git
data/reference/
              Curated BNetzA-to-KBA crosswalk CSV
data/profiles/
              Source inventories and validation JSON artifacts
docs/         English project documentation
reports/      Human-readable validation reports
scripts/      Download, profile, ingest, crosswalk, deployment, and validation code
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
- [Phase validation reports](reports/phase01_data_profile.md), [Phase 02 schema inspection](reports/phase02_schema_inspection.md), [Phase 03 DuckDB validation](reports/phase03_duckdb_validation.md), [Batch 03 crosswalk validation](reports/batch03_crosswalk_validation.md), [Batch 06 geographic deployment](reports/batch06_geographic_deployment.md), and [Batch 06.1 KPI documentation audit](reports/batch06-1_kpi_documentation_audit.md)

## Important limitations

- The BNetzA published register explicitly warns that it does not represent every publicly accessible charger in Germany.
- An equipment row may contain several charging points. A charging-point slot is not a connector count.
- BNetzA infrastructure is dated 2026-09-30; the latest KBA stock snapshot is dated 2026-07-01. Ratios are not contemporaneous.
- The crosswalk has 401 BNetzA combinations and 400 KBA codes because Trier city and Trier-Saarburg share code 07211. Charging metrics must be aggregated by KBA code before joining vehicle stock.
- Twenty-two aliases and the two shared Trier source mappings (24 provisional mappings total) are provisional local-snapshot mappings pending authoritative review.
- The deployed analytics.charging_by_state view uses source_id and equipment Excel row in both the point aggregation and join. The current database still contains one BNetzA infrastructure snapshot; future multi-snapshot loads require re-running the same source-aware validations.
- No source supports utilization, sessions, energy delivered, queue times, reliability, or causality.

## Roadmap

The next stages are independent crosswalk review, final geographic-layer approval, optional BBSR suitability work, KPI hardening, Tableau extract preparation, dashboard development, final quality and licensing review, and only then an explicitly approved GitHub publication.

Code is covered by the existing MIT LICENSE. Official source data retain the licenses and attribution requirements declared in the source manifest; redistribution and final publication rights require a separate review.
