# Project charter

## Motivation and problem statement

Germany needs a transparent way to compare the development of registered electric vehicles with the public charging infrastructure visible in the official register. The two sources describe different things: BNetzA describes published charging equipment and point records, while KBA describes aggregated registered vehicle stock. They also use different geographic labels and snapshot dates.

The project therefore focuses on a defensible analytical foundation rather than a single headline ratio. It preserves source detail, makes the equipment-to-point relationship explicit, prevents KBA double-counting, and labels every geographic and temporal limitation.

## Intended users and analytical value

Intended users are:

- Data and BI analysts learning reproducible source-to-dashboard workflows.
- Analysts assessing regional charging infrastructure readiness.
- Portfolio reviewers evaluating data modeling, validation, and communication quality.
- Future Tableau users who need a compact, well-documented extract rather than a live local database.

The analytical value is a traceable bridge from official workbooks to validated measures, with enough raw detail to investigate exceptions without rebuilding the sources.

## Portfolio and learning objectives

- Practice source inventory, checksums, and full-workbook profiling.
- Model one-to-many equipment and charging-point data without losing source detail.
- Use DuckDB schemas to separate raw, core, and analytical layers.
- Validate row counts, keys, point-power parsing, and alternate KBA breakdowns.
- Build a state-aware, administrative-type-aware geographic crosswalk.
- Design KPIs with explicit grains, denominators, dates, and limitations.
- Prepare a professional, reproducible repository for a later dashboard and publication review.

## Approved scope

- Germany-wide coverage across all 16 federal states.
- BNetzA Ladesäulenregister snapshot dated 2026-09-30.
- KBA FZ 27 snapshots dated 2026-01-01, 2026-04-01, and 2026-07-01.
- Complete source preservation in local raw workbooks and the DuckDB raw schema.
- Normalized charging equipment and charging-point tables.
- KBA state, district, postcode, municipality, and national-history structures already supported by the current build.
- A versioned BNetzA-to-KBA district crosswalk in CSV form.
- Read-only batch analysis and documentation.
- Future Tableau Public reporting after the model and KPIs are approved.

## Explicit exclusions

- No modification of official source workbooks.
- No rebuild, migration, or schema change to DuckDB in Batch 04.
- No Destatis or BBSR data integration in the current implementation.
- No charging-session, energy-delivery, utilization, queue, reliability, or real-time availability measures.
- No vehicle-level data; KBA values are aggregate stock.
- No causal claim that infrastructure causes vehicle-stock growth.
- No official geographic verification claim for the provisional aliases.
- No GitHub repository, remote, upload, synchronization, or publication during this batch.

## Key analytical questions

1. What is the published count of charging equipment and charging-point slots?
2. How are normal, fast, high-power, and ultra-high-power point bands distributed?
3. How does registered BEV and PHEV stock vary across the three KBA snapshots?
4. How do state and district-registration-region measures differ?
5. Which results are descriptive and validated, and which remain provisional because of geography, dates, or source coverage?

## Deliverables

- English project landing page and documentation index.
- Project charter, architecture, data sources, data dictionary, KPI catalog, geographic methodology, data quality, findings, reproducibility, roadmap, decision log, and publication checklist.
- Persistent AGENTS.md project instructions.
- PROJECT_STATUS.md and CHANGELOG.md tracking files.
- Safe local .gitignore configuration.
- Local Git repository and reviewed Batch 04 baseline commit.

## Success criteria

- Source paths, dates, checksums, schemas, and measured headline values are traceable to local artifacts.
- Equipment, point, and vehicle grains are not conflated.
- Every KPI has a formula, denominator, date, grain, status, and limitation.
- Provisional mappings are visibly separated from local-snapshot observations.
- Documentation does not claim Tableau or BBSR completion.
- No raw workbook, DuckDB database, virtual environment, secret, remote, or upload is included in the local baseline commit.
- Validation failures and unresolved issues remain visible.

## Current phase versus planned features

Batch 04 is the documentation and local-Git phase. The current database and crosswalk are read-only inputs to the documentation; no permanent geographic DuckDB objects are created here.

Planned features are approval of the minimum geographic analytics layer, implementation of any separately approved BBSR compatibility layer, further KPI validation, Tableau extract preparation, dashboard development, final licensing review, and eventual publication after explicit approval. Batch 09 completed the BBSR suitability assessment as research/documentation only; BBSR remains excluded from the current implementation.
