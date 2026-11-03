# Reproducibility

## Environment

The current verified local environment is:

- Python 3.9.6
- DuckDB 1.4.5
- DuckDB requirement declared in requirements-phase03.txt: duckdb >=1.3 and <3
- macOS local filesystem workflow

The Phase 01 profiling scripts use Python standard-library modules only. DuckDB is needed for the database, crosswalk, batch-runner, deployment, and validation stages. Batch 06 used the existing `.venv` environment and did not install packages or change DuckDB memory or thread settings.

## Local relocation

The complete project is kept under the established local `dev` development root. Run the commands in this document from the repository root so that all database, source, report, and configuration paths remain repository-relative.

The private Persian KPI catalog is kept in the sibling directory `../germany-ev-charging-analytics-private/`. It is deliberately outside the Git repository and must never be staged or published.

The local DBeaver DuckDB connection/output settings and VS Code workspace record were updated to the relocated project outside Git. Historical DBeaver logs and UI-state text may retain old paths, but they are not active source or connection definitions.

Batch 06.2 preserved the existing ignored `.venv` without installing or recreating dependencies. `.venv/bin/python` and `.venv/bin/python -m pip` run successfully after relocation, but the generated activation scripts and `pip` entry-point wrappers retain historical absolute paths from an earlier location. Use the working Python entry point directly until an environment repair or recreation is explicitly approved.

## Source acquisition and verification

Run from the repository root:

~~~bash
python3 scripts/00_storage_check.py
python3 scripts/01_download.py
python3 scripts/02_profile_xlsx.py
python3 scripts/03_inspect_schema.py
python3 scripts/10_build_bbsr_reference.py
~~~

The source manifest is config/sources.json. scripts/01_download.py validates the XLSX container and writes data/profiles/download_inventory.json. scripts/02_profile_xlsx.py streams every physical row in every worksheet and writes data/profiles/workbook_profiles.json and reports/phase01_data_profile.md.

If an official page blocks scripted downloads, download the original workbook from the source_page in the manifest into its exact configured path, then run:

~~~bash
python3 scripts/01_download.py --verify-only
python3 scripts/02_profile_xlsx.py
~~~

Do not rename, rewrite, trim, or modify the original workbooks.

The BBSR command reads data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx and
writes data/reference/bbsr_settlement_types_2025.csv,
data/reference/bbsr_source_manifest.json,
data/profiles/bbsr_reference_profile.json, and
reports/batch10_bbsr_reference_validation.md. It records the source and derived
SHA-256 values, inspects every workbook sheet, validates the exact four-category
fields, and does not write to DuckDB. Re-running it must produce the same CSV
checksum.

## DuckDB build

The existing build script uses the four verified primary BNetzA/KBA source profiles, creates a temporary build database, validates profiled row counts and hashes, and replaces the target only after a successful checkpoint. Separately profiled reference sources such as BBSR are ignored by that builder. Its command is:

~~~bash
.venv/bin/python scripts/03_build_duckdb.py
~~~

This command is a read-write rebuild workflow. It is not part of normal read-only analysis and must not be run during a review unless a database rebuild is explicitly approved. The current database was not rebuilt in Batch 04.

The current database contains raw, core, reference, and analytics objects described in [the data dictionary](data-dictionary.md). The original source files and local DuckDB file remain outside the Git baseline.

## Validation

The existing reports provide the established checks:

~~~bash
.venv/bin/python scripts/04_build_geographic_crosswalk.py
.venv/bin/python scripts/batch_analysis.py --demo \
  --report reports/batch03_batch_runner_demo.md
~~~

The crosswalk script opens DuckDB with read_only=True and writes the curated reference CSV and its Markdown validation report. The batch runner opens one read-only connection, accepts multiple named SELECT or WITH queries, consumes every result to record row counts, and closes the connection.

## Batch 06 geographic deployment

The approved deployment command opens the existing DuckDB file read-only for preflight, verifies the Crosswalk CSV and source-key coverage, checks for open DuckDB handles and WAL state, creates a timestamped ignored backup under `data/backups/`, validates that backup through a separate read-only connection, and then applies `sql/06_geographic_layer.sql` in one transaction:

~~~bash
.venv/bin/python scripts/06_deploy_geographic_layer.py --json
~~~

The deployment never rebuilds or overwrites the database. It creates or validates the permanent crosswalk table and two geographic views, and corrects `analytics.charging_by_state` only after recording its current output. A failed in-transaction acceptance check rolls back the uncommitted database changes.

Run the independent post-deployment suite with a read-only connection:

~~~bash
.venv/bin/python scripts/06_validate_geographic_layer.py --json
~~~

The validator checks source retention, exact crosswalk equality, mapping uniqueness, maximum-per-point power bands, aggregate-before-join totals, KBA date keys, Trier treatment, the combined view, and the source-aware state-view output. Backups, the DuckDB file, WALs, and temporary analytical artifacts are ignored and must not be committed.

## Batch 13 BBSR charging-only deployment

The approved Batch 13 command builds or validates the deterministic source-grain
bridge, verifies the Batch 12 Path A evidence and BBSR reference, validates a
read-only backup before writing, and deploys the new objects transactionally:

~~~bash
.venv/bin/python scripts/13_deploy_bbsr_charging_layer.py --json
~~~

For a repeat-safe run using the verified Batch 13 backup:

~~~bash
.venv/bin/python scripts/13_deploy_bbsr_charging_layer.py \
  --backup-path data/backups/ev_charging_pre_batch13_20261102_222612.duckdb \
  --json
~~~

The script uses no new dependency or dataset. It writes the approved bridge
CSV and manifest, creates `reference.bnetza_bbsr_district_bridge_2025`, and
creates `analytics.charging_by_bbsr_district_2025` plus
`analytics.charging_by_bbsr_type_2025`. It does not modify the KBA Crosswalk,
join KBA stock, classify KBA registration regions, or allocate Trier stock.
Run the command a second time and inspect the JSON evidence; the existing
bridge must match exactly and no duplicate rows may appear.

## Batch 13.1 owner-approved scenario deployment

Run the read-only preflight first:

~~~bash
.venv/bin/python scripts/13_1_deploy_bbsr_scenario.py --dry-run --json
~~~

The preflight validates the exact two-row reference, the manifest checksum,
the actual `bnetza_source_id`/state/district columns, and the existing
Crosswalk `kba_district_code` values `06415` and `06435`. It also checks the
official five-row Batch 13 summary and all national charging baselines.

Deploy the separate scenario only after the preflight passes:

~~~bash
.venv/bin/python scripts/13_1_deploy_bbsr_scenario.py --json
~~~

The script checks for open handles and WALs, creates an ignored timestamped
`ev_charging_pre_batch13_1_*.duckdb` backup, opens that backup read-only, and
compares baseline object snapshots before the transaction. It creates only
`reference.bnetza_bbsr_owner_override_2026`,
`analytics.charging_by_bbsr_district_2026_scenario`, and
`analytics.charging_by_bbsr_type_2026_scenario`. The official BBSR CSV,
original bridge, Crosswalk, raw/core tables, official Batch 13 views, KBA
views, and state view are acceptance baselines.

For idempotency validation, reuse the verified backup:

~~~bash
.venv/bin/python scripts/13_1_deploy_bbsr_scenario.py \
  --backup-path data/backups/ev_charging_pre_batch13_1_20261102_224646.duckdb \
  --json
~~~

The scenario remains a charging-only source-grain analysis. Hanau category 1
is an owner-approved assumption, not an official BBSR 2025/2026 classification;
Main-Kinzig category 2 is a historical BBSR 2025 carry-forward with a 2026
Hanau-separation caveat. Neither override is `VERIFIED_COMPATIBLE`, and no KBA
vehicle stock or Trier allocation is introduced. Full evidence is in
[`reports/batch13_1_bbsr_scenario_classification.md`](../reports/batch13_1_bbsr_scenario_classification.md).

## Batch 13.2 historical BBSR boundary harmonization

Run the reproducible reference/audit build first:

~~~bash
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py \
  --build-reference-only --json
~~~

Run the read-only preflight, then deploy the separate historical target-unit
objects:

~~~bash
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py \
  --dry-run --json
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py \
  --json
~~~

For the repeat-safe check, reuse the verified ignored backup from the first
deployment:

~~~bash
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py \
  --backup-path data/backups/ev_charging_pre_batch13_2_20261102_231615.duckdb \
  --json
~~~

The script validates the raw BBSR `SLK2025` administrative form, performs strict
and semantic bidirectional anti-joins, records the Hanau legal boundary
evidence, and maps 401 BNetzA source components to 400 historical BBSR target
units. It creates only
`reference.bnetza_bbsr_historical_harmonization_2025`,
`analytics.charging_by_bbsr_district_2025_harmonized`, and
`analytics.charging_by_bbsr_type_2025_harmonized`. The transaction is preceded
by a lock/WAL check and a read-only backup validation; post-deployment checks
snapshot the official Batch 13/13.1, Crosswalk, KBA, and state objects. No KBA
vehicle stock, Crosswalk assignment, or Trier allocation is introduced. See
[`reports/batch13_2_hanau_geographic_harmonization.md`](../reports/batch13_2_hanau_geographic_harmonization.md)
for the evidence and expected totals.

For a custom query:

~~~bash
.venv/bin/python scripts/batch_analysis.py \
  --query equipment_count="SELECT COUNT(*) AS rows FROM core.charging_equipment" \
  --query point_count="SELECT COUNT(*) AS rows FROM core.charging_point" \
  --report reports/my_batch.md
~~~

For reusable JSON query definitions, use query-file with either an object mapping names to SQL or a list of objects containing name and sql. The placeholder {{CROSSWALK_CSV}} can be used in a query-file and is resolved by the runner. Queries are restricted to one SELECT or WITH statement and no permanent tables or views are created.

## Geographic crosswalk

The crosswalk generator reads:

- core.charging_equipment
- core.charging_point
- core.kba_district_ev_stock at 2026-07-01

It writes data/reference/bnetza_kba_district_crosswalk_2026.csv and reports/batch03_crosswalk_validation.md. It preserves all 401 source combinations and records provisional statuses rather than inventing missing mappings.

## Read-only database inspection

Use a read-only Python connection for analysis:

~~~python
import duckdb

connection = duckdb.connect(
    "data/analytics/ev_charging.duckdb",
    read_only=True,
)
try:
    rows = connection.execute(
        "SELECT COUNT(*) FROM core.charging_point"
    ).fetchone()
finally:
    connection.close()
~~~

Do not kill processes to clear a lock. If a read-only connection fails because another process holds the DuckDB file, close the other client or use an existing verified report and mark the evidence historical. Do not rebuild the database to work around a lock.

## DBeaver

DBeaver is optional. If used, create a DuckDB connection to data/analytics/ev_charging.duckdb and inspect raw, core, reference, and analytics schemas. Keep the Python build and analysis processes closed when DBeaver needs exclusive access. Prefer a read-only connection for inspection and do not run DDL from the client unless the database change has been separately approved.

## Tableau Public

Tableau Public cannot query a local DuckDB file as a live published source. The planned workflow is to create a compact, validated extract from approved analytics relations, record both source dates and the extract generation time, and keep detailed point data available locally where performance and licensing permit. No Tableau dashboard or public extract has been completed.

## Batch 14 read-only BBSR statistical analysis

Run the deterministic analyzer from the repository root:

~~~bash
.venv/bin/python scripts/14_analyze_bbsr_charging_patterns.py --json
~~~

The script opens the existing DuckDB file with `read_only=True`, validates the
Batch 13.2 harmonized district/type view contract, independently reconciles
the core equipment/point and maximum-per-point power totals, checks source-file
fingerprints, and writes only these Git-tracked analytical artifacts:

- `reports/batch14_bbsr_charging_analysis.md`
- `reports/batch14_bbsr_type_metrics.csv`
- `reports/batch14_bbsr_district_metrics.csv`

It does not create or replace a DuckDB object, modify a source/reference file,
read KBA vehicle stock for the analysis, or deploy a KPI. Repeated execution
with the same database and reference files is deterministic.

## Batch 15 KBA FZ 27 analysis

Run the deterministic read-only analyzer from the repository root:

~~~bash
.venv/bin/python scripts/15_analyze_kba_ev_stock.py --json
~~~

The script opens `data/analytics/ev_charging.duckdb` with `read_only=True`,
checks the three KBA workbook SHA-256 fingerprints, validates the 20-sheet
inventory for each release, reconciles national/state/`Sonstige`/400-region
scopes, checks FZ 27.5 ownership grain, inspects postcode/municipality keys,
and validates the deduplicated FZ 27.9 history. It writes only:

- `reports/batch15_kba_ev_stock_analysis.md`
- `reports/batch15_kba_national_trends.csv`
- `reports/batch15_kba_state_metrics.csv`
- `reports/batch15_kba_district_metrics.csv`
- `reports/batch15_kba_ownership_metrics.csv`
- `reports/batch15_kba_worksheet_capabilities.csv`

The script does not create or replace a DuckDB object, modify a source or
reference file, build a BBSR join, allocate Trier stock, or deploy a KPI.
Repeated execution with the same database and fingerprints is deterministic.

## Batch 17 temporal KPI validity analysis

Run the deterministic read-only analyzer from the repository root:

~~~bash
.venv/bin/python scripts/17_analyze_temporal_kpi_validity.py --json
~~~

The script opens `data/analytics/ev_charging.duckdb` with `read_only=True`,
checks the actual equipment commissioning-date field and preserved raw value,
validates source-aware equipment/point identities and maximum-per-point power
bands, reconciles KBA January/April/July state and 400-region scopes, checks
all six preserved source/reference fingerprints, and verifies that the
database hash is unchanged. It writes only:

- `reports/batch17_temporal_kpi_validity.md`
- `reports/batch17_equipment_commissioning_cohorts.csv`
- `reports/batch17_state_temporal_sensitivity.csv`
- `reports/batch17_kpi_publication_decisions.csv`
- `reports/batch17_vehicle_stock_denominator_sensitivity.csv`

Perspective A is the full BNetzA `2026-09-30` published snapshot compared with
KBA `2026-07-01` stock and is labelled **CROSS-SNAPSHOT DESCRIPTIVE
COMPARISON**. Perspective B retains September point rows attached to equipment
commissioned on or before `2026-07-01` and is labelled **RETROSPECTIVE
SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE**. The script does
not treat commissioning as point activation, does not infer historical status,
does not modify DuckDB/source files, and does not deploy a KPI. Repeated
execution with unchanged inputs is deterministic.

## Batch 18 readiness review

Batch 18 is documentation-only and has no analysis script or database
deployment. The independent read-only check used the following commands from
the repository root:

~~~bash
git status --porcelain=v1
git rev-parse HEAD
git remote -v
shasum -a 256 \
  data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx \
  data/raw/kba/fz27_202601.xlsx data/raw/kba/fz27_202604.xlsx \
  data/raw/kba/fz27_202607.xlsx \
  data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx \
  data/reference/bbsr_settlement_types_2025.csv \
  data/reference/bnetza_kba_district_crosswalk_2026.csv
~~~

The DuckDB check must use `read_only=True` and only SELECT statements. Batch 18
observed 117,662 equipment rows, 211,253 point rows, 16 state rows and 400
July KBA registration regions. The database hash remained
`5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3`.

The deterministic readiness artifacts are
`reports/batch18_analytics_readiness_review.md`,
`reports/batch18_kpi_readiness_register.csv`,
`reports/batch18_historical_data_feasibility.md`,
`reports/batch18_tableau_analysis_candidates.md` and
`reports/batch18_readiness_decisions.md`. No Tableau asset, extract, SQL
object, source workbook, reference crosswalk or private file is generated by
this batch.

## Batch 19 Tableau export preparation

From the repository root, run:

~~~bash
.venv/bin/python scripts/19_prepare_tableau_data.py
~~~

The exporter opens `data/analytics/ev_charging.duckdb` with
`read_only=True`, checks the required schemas and views, verifies 12 approved
input fingerprints, and writes only the following controlled artifacts:

- Nine UTF-8/LF CSVs under `data/exports/tableau/`.
- `data/exports/tableau/export_manifest.json` with source/object identifiers,
  row/column counts and SHA-256 checksums.
- `reports/batch19_tableau_export_contracts.md` (maintained contract).
- `reports/batch19_tableau_data_validation.md` with measured results.

The current successful run measured a database SHA-256 of
`5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3` before and
after export. The second execution produced byte-identical CSVs, manifest and
validation report. Output row counts are 1 national, 16 state charging, 400
BBSR districts, 4 BBSR types, 48 KBA state/date rows, 1,200 KBA
registration-region/date rows, 16 state comparison rows, 16 temporal rows and
33 national-history rows.

The exports are not Tableau workbooks or proprietary extracts. Keep national,
state, KBA registration-region and historical BBSR sources separate unless the
relationships in the Batch 19 contract are selected deliberately. No remote,
upload or publication is part of this workflow.

## Batch 20 semantic-model validation

Batch 20 is documentation and validation only. The validation workflow used:

~~~bash
git rev-parse HEAD
git status --porcelain=v1
git remote -v
shasum -a 256 data/analytics/ev_charging.duckdb
.venv/bin/python -c "import duckdb; duckdb.connect('data/analytics/ev_charging.duckdb', read_only=True)"
~~~

The read-only checks inspected `information_schema`, the manifest-listed CSVs,
their SHA-256 values, natural keys, dates, relationship matches, and baseline
reconciliations in memory. The database hash before and after was
`5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3`.
The validation transcript is
[`reports/batch20_semantic_model_validation.md`](../reports/batch20_semantic_model_validation.md).

The 59-row mapping is
[`reports/batch20_kpi_model_mapping.csv`](../reports/batch20_kpi_model_mapping.csv).
No command in this batch writes to DuckDB, exports, raw sources, Crosswalks or
Tableau assets. The private Persian reference remains in the sibling directory
`../germany-ev-charging-analytics-private/` and is outside Git.

## Batch 21 Tableau executive overview preparation

Run from the repository root:

~~~bash
./.venv/bin/python scripts/21_prepare_tableau_overview.py
~~~

The script reads the Batch 19 manifest and nine existing CSVs, verifies all
manifest-listed raw/reference/report fingerprints, opens
`data/analytics/ev_charging.duckdb` with `read_only=True`, queries only the
equipment-status grouping, and checks the database hash before and after. It
writes only:

- `data/exports/tableau/preparation/power_band_distribution_2026_09_30.csv`;
- `data/exports/tableau/preparation/equipment_status_breakdown_2026_09_30.csv`;
- `reports/batch21_tableau_overview_validation.md`.

The first derived file contains four mutually exclusive bands totalling
211,253 points. The second contains `In Betrieb` 117,642 and `In Wartung` 20.
The validation report records the nine unchanged Batch 19 hashes, the 12
manifest-listed fingerprints, the unchanged DuckDB SHA-256
`5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3`, and the
fact that no Tableau workbook or screenshot exists yet. Tableau Desktop
assembly remains a manual step in
[`docs/tableau-executive-overview.md`](tableau-executive-overview.md).

## Batch 22.6 Tableau worksheet visual capture

Batch 22.6 was a read-only macOS capture diagnostic. It activated the
existing Tableau Desktop window through System Events, enumerated the native
window metadata, and wrote temporary images outside the repository. The
full-display command was:

~~~bash
/usr/sbin/screencapture -x <temporary-dir>/full-screen.png
~~~

It produced a valid 2560 × 1600 PNG. The native window-targeted command was
also attempted:

~~~bash
/usr/sbin/screencapture -x -l <tableau-window-id> <temporary-dir>/tableau-window.png
~~~

For the existing window, CoreGraphics reported ID `8660`, bounds
`188,76,960,628`, on-screen status `true` and sharing state `0`
(`kCGWindowSharingNone`). The window-targeted command returned
`could not create image from window`; the exact-bounds control capture showed
only desktop wallpaper. The full report is
[`reports/batch22_6_tableau_worksheet_visual_capture.md`](../reports/batch22_6_tableau_worksheet_visual_capture.md).

Menu metadata indicated `Window → Sheet 1` and listed data source
`national_charging_2026_09_30`, but the worksheet canvas, shelves, Marks card,
Data pane, fields and worksheet tabs were not visually visible or exposed by
Accessibility. The result is `CANVAS_VISIBLE: NO` and `NO-GO` for screenshot-
based local GUI interaction. No workbook, source, export, database,
permission, preference or MCP configuration changed.

## Batch 23 local web dashboard

The web dashboard is a static presentation layer over the validated Batch 19
and Batch 21 CSV contracts. It does not rebuild DuckDB and does not require a
database connection at runtime. Use Node.js 22 or a compatible current LTS
runtime from the `web/` directory:

~~~bash
cd web
npm install
npm run check
npm run build
# Choose one local server:
npm run dev -- --host 127.0.0.1
# npm run preview
~~~

`npm run check` first runs `scripts/prepare-data.mjs`. The script reads the
national charging, state charging, state comparison, KBA national history,
power-band preparation and equipment-status preparation CSVs; verifies the
Batch 19 manifest checksums and expected row/column contracts; validates the
16-state membership, 33 history observations, national/state totals and the
four mutually exclusive power bands; then writes the deterministic
`web/public/data/dashboard.json` artifact. It records source checksums, roles,
dates and map provenance in that artifact.

The browser routes are `/#national` and `/#geographic`. The map uses the
versioned local asset `web/public/data/germany-states.geo.json`; its source and
license metadata are in `web/public/data/geo-attribution.md`. `web/node_modules`
and `web/dist` are ignored. The dashboard preparation script does not write
DuckDB, raw workbooks, reference data, Batch 19 exports or Tableau assets.
