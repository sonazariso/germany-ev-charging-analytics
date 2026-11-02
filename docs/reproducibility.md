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
