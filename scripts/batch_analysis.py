#!/usr/bin/env python3
"""Run named read-only DuckDB SELECT queries and write one Markdown report.

Examples from the project root:

    .venv/bin/python scripts/batch_analysis.py --demo \
        --report reports/batch03_batch_runner_demo.md

    .venv/bin/python scripts/batch_analysis.py \
        --query equipment_count="SELECT COUNT(*) AS rows FROM core.charging_equipment" \
        --query point_count="SELECT COUNT(*) AS rows FROM core.charging_point" \
        --report reports/my_batch.md

For reusable query files, pass a JSON object mapping query names to SQL or a
JSON list of objects with ``name`` and ``sql``.  SQL may use the placeholder
``{{CROSSWALK_CSV}}``; it is replaced with a quoted absolute path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_CROSSWALK = ROOT / "data/reference/bnetza_kba_district_crosswalk_2026.csv"


@dataclass(frozen=True)
class QuerySpec:
    name: str
    sql: str


@dataclass
class QueryResult:
    name: str
    sql: str
    status: str
    row_count: int = 0
    columns: list[str] | None = None
    preview_rows: list[list[Any]] | None = None
    elapsed_seconds: float = 0.0
    error_type: str = ""
    error: str = ""


@dataclass
class BatchResult:
    database: Path
    generated_at_utc: str
    connection_status: str
    connection_error: str
    connection_closed: bool
    query_results: list[QueryResult]


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def render_sql(sql: str, crosswalk_path: Path) -> str:
    return sql.replace("{{CROSSWALK_CSV}}", sql_literal(str(crosswalk_path.resolve())))


def validate_select(sql: str) -> tuple[bool, str]:
    """Reject obvious non-SELECT/multi-statement input before execution."""

    cleaned = re.sub(r"^\s*(?:--[^\n]*\n|/\*.*?\*/\s*)*", "", sql, flags=re.DOTALL)
    cleaned = cleaned.strip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].rstrip()
    if ";" in cleaned:
        return False, "Only one SQL statement is allowed"
    if not re.match(r"^(?:SELECT|WITH)\b", cleaned, flags=re.IGNORECASE):
        return False, "Only SELECT or WITH queries are allowed"
    return True, ""


def parse_query_file(path: Path, crosswalk_path: Path) -> list[QuerySpec]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    specs: list[QuerySpec] = []
    if isinstance(payload, dict):
        for name, sql in payload.items():
            specs.append(QuerySpec(str(name), render_sql(str(sql), crosswalk_path)))
    elif isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict) or "name" not in item or "sql" not in item:
                raise ValueError(f"Each query-file item needs name and sql: {item!r}")
            specs.append(
                QuerySpec(
                    str(item["name"]),
                    render_sql(str(item["sql"]), crosswalk_path),
                )
            )
    else:
        raise ValueError("Query file must contain a JSON object or list")
    return specs


def parse_query_argument(value: str) -> QuerySpec:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Use NAME=SQL for --query")
    name, sql = value.split("=", 1)
    if not name.strip() or not sql.strip():
        raise argparse.ArgumentTypeError("Query name and SQL must both be non-empty")
    return QuerySpec(name.strip(), sql.strip())


def demo_queries(crosswalk_path: Path) -> list[QuerySpec]:
    csv_relation = (
        "read_csv_auto("
        + sql_literal(str(crosswalk_path.resolve()))
        + ", types={'kba_district_code': 'VARCHAR'})"
    )
    return [
        QuerySpec(
            "baseline_row_counts",
            """
            SELECT * FROM (VALUES
                ('core.charging_equipment', (SELECT COUNT(*) FROM core.charging_equipment)),
                ('core.charging_point', (SELECT COUNT(*) FROM core.charging_point)),
                ('core.kba_district_ev_stock_july', (
                    SELECT COUNT(*) FROM core.kba_district_ev_stock
                    WHERE reference_date = DATE '2026-07-01'
                ))
            ) AS counts(entity, row_count)
            """,
        ),
        QuerySpec(
            "crosswalk_coverage",
            f"""
            SELECT
                COUNT(*) AS crosswalk_rows,
                COUNT(DISTINCT bnetza_state_name || '|' || bnetza_district_name) AS bnetza_combinations,
                COUNT(*) FILTER (WHERE mapping_status = 'mapped') AS mapped_rows,
                COUNT(*) FILTER (WHERE mapping_status <> 'mapped') AS unmapped_rows,
                COUNT(DISTINCT kba_district_code) FILTER (WHERE mapping_status = 'mapped') AS mapped_kba_codes,
                COUNT(*) FILTER (WHERE kba_district_code = '07211') AS trier_shared_rows
            FROM {csv_relation}
            """,
        ),
        QuerySpec(
            "equipment_point_reconciliation",
            """
            WITH point_counts AS (
                SELECT source_id, equipment_excel_row, COUNT(*) AS point_slots
                FROM core.charging_point
                GROUP BY source_id, equipment_excel_row
            )
            SELECT
                COUNT(*) AS equipment_rows,
                COALESCE(SUM(e.declared_point_count), 0) AS declared_point_count,
                COALESCE(SUM(COALESCE(p.point_slots, 0)), 0) AS charging_point_slots,
                COUNT(*) FILTER (
                    WHERE e.declared_point_count IS DISTINCT FROM COALESCE(p.point_slots, 0)
                ) AS equipment_point_mismatches
            FROM core.charging_equipment e
            LEFT JOIN point_counts p
              ON p.source_id = e.source_id
             AND p.equipment_excel_row = e.excel_row
            """,
        ),
        QuerySpec(
            "aggregate_before_kba_join",
            f"""
            WITH crosswalk AS (
                SELECT * FROM {csv_relation}
            ),
            charging_by_kba AS (
                SELECT kba_district_code,
                       SUM(CAST(equipment_rows AS BIGINT)) AS equipment_rows,
                       SUM(CAST(charging_point_slots AS BIGINT)) AS charging_point_slots
                FROM crosswalk
                WHERE mapping_status = 'mapped'
                GROUP BY kba_district_code
            ),
            kba AS (
                SELECT district_code,
                       SUM(bev_cars) AS bev_cars
                FROM core.kba_district_ev_stock
                WHERE reference_date = DATE '2026-07-01'
                GROUP BY district_code
            ),
            joined AS (
                SELECT c.*, k.bev_cars
                FROM charging_by_kba c
                LEFT JOIN kba k ON k.district_code = c.kba_district_code
            )
            SELECT
                COUNT(*) AS joined_kba_codes,
                COUNT(*) FILTER (WHERE bev_cars IS NULL) AS missing_kba_codes,
                (SELECT COUNT(*) FROM kba) AS source_kba_codes,
                COALESCE(SUM(bev_cars), 0) AS joined_bev_cars,
                (SELECT COALESCE(SUM(bev_cars), 0) FROM kba) AS source_bev_cars,
                COALESCE(SUM(charging_point_slots), 0) AS charging_point_slots_after_aggregation
            FROM joined
            """,
        ),
    ]


def ensure_unique_names(specs: Iterable[QuerySpec]) -> list[QuerySpec]:
    output: list[QuerySpec] = []
    seen: set[str] = set()
    for spec in specs:
        if spec.name in seen:
            raise ValueError(f"Duplicate query name: {spec.name}")
        seen.add(spec.name)
        output.append(spec)
    if not output:
        raise ValueError("No queries were supplied; use --demo, --query, or --query-file")
    return output


def execute_batch(
    database: Path,
    queries: list[QuerySpec],
    preview_rows: int = 25,
) -> BatchResult:
    """Execute all named SELECTs on one read-only connection."""

    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    results: list[QueryResult] = []
    connection = None
    connection_status = "failed"
    connection_error = ""
    connection_closed = False
    try:
        import duckdb

        connection = duckdb.connect(str(database), read_only=True)
        connection_status = "connected_read_only"
    except Exception as exc:
        connection_error = f"{type(exc).__name__}: {exc}"
        return BatchResult(
            database, generated_at, connection_status, connection_error, False, results
        )

    try:
        for spec in queries:
            valid, validation_error = validate_select(spec.sql)
            if not valid:
                results.append(
                    QueryResult(
                        name=spec.name,
                        sql=spec.sql,
                        status="failed",
                        error_type="QueryValidationError",
                        error=validation_error,
                    )
                )
                continue
            started = time.perf_counter()
            try:
                cursor = connection.execute(spec.sql)
                columns = [description[0] for description in (cursor.description or [])]
                captured: list[list[Any]] = []
                row_count = 0
                while True:
                    batch = cursor.fetchmany(1000)
                    if not batch:
                        break
                    row_count += len(batch)
                    if len(captured) < preview_rows:
                        captured.extend(
                            [list(row) for row in batch[: preview_rows - len(captured)]]
                        )
                results.append(
                    QueryResult(
                        name=spec.name,
                        sql=spec.sql,
                        status="passed",
                        row_count=row_count,
                        columns=columns,
                        preview_rows=captured,
                        elapsed_seconds=time.perf_counter() - started,
                    )
                )
            except Exception as exc:
                results.append(
                    QueryResult(
                        name=spec.name,
                        sql=spec.sql,
                        status="failed",
                        elapsed_seconds=time.perf_counter() - started,
                        error_type=type(exc).__name__,
                        error=str(exc),
                    )
                )
    finally:
        try:
            connection.close()
        finally:
            connection_closed = True

    return BatchResult(
        database,
        generated_at,
        connection_status,
        connection_error,
        connection_closed,
        results,
    )


def markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dt.date, dt.datetime)):
        value = value.isoformat()
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def display_sql(sql: str) -> str:
    """Render repository-relative paths in Markdown reports."""

    return sql.replace(str(ROOT.resolve()), ".")


def render_report(batch: BatchResult) -> str:
    passed = sum(result.status == "passed" for result in batch.query_results)
    failed = sum(result.status != "passed" for result in batch.query_results)
    database_display = (
        str(batch.database.relative_to(ROOT))
        if batch.database.is_relative_to(ROOT)
        else str(batch.database)
    )
    lines = [
        "# Read-only DuckDB batch analysis report",
        "",
        f"Generated at (UTC): `{batch.generated_at_utc}`",
        "",
        "## Batch status",
        "",
        f"- Database: `{database_display}`",
        f"- Connection: `{batch.connection_status}`",
        f"- Connection closed: `{batch.connection_closed}`",
        f"- Queries passed: `{passed}`; queries failed: `{failed}`",
    ]
    if batch.connection_error:
        lines.append(f"- Connection error: `{batch.connection_error}`")
    lines.extend(["", "## Query summary", "", "| Query | Status | Rows returned | Elapsed (s) | Error |", "|---|---|---:|---:|---|"])
    for result in batch.query_results:
        lines.append(
            f"| `{result.name}` | `{result.status}` | {result.row_count:,} | {result.elapsed_seconds:.6f} | {markdown_cell(result.error)} |"
        )

    for result in batch.query_results:
        lines.extend(
            [
                "",
                f"## Query: `{result.name}`",
                "",
                "```sql",
                display_sql(result.sql.strip()),
                "```",
                "",
            ]
        )
        lines.append(
            f"Status: `{result.status}`; rows returned: `{result.row_count:,}`; elapsed: `{result.elapsed_seconds:.6f}` seconds."
        )
        if result.status != "passed":
            lines.extend(["", f"Error type: `{result.error_type}`", "", "```text", result.error, "```"])
            continue
        columns = result.columns or []
        preview = result.preview_rows or []
        if columns:
            lines.extend(["", "Preview:", "", "| " + " | ".join(markdown_cell(column) for column in columns) + " |"])
            lines.append("| " + " | ".join("---" for _ in columns) + " |")
            for row in preview:
                lines.append("| " + " | ".join(markdown_cell(value) for value in row) + " |")
            if result.row_count > len(preview):
                lines.append("")
                lines.append(f"Preview capped at {len(preview):,} rows; all {result.row_count:,} rows were consumed for the row count.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This runner executes the supplied SELECT/WITH statements on one DuckDB connection opened with `read_only=True`.",
            "- CSV references such as `read_csv_auto({{CROSSWALK_CSV}})` are read as query-scoped relations; no permanent DuckDB table or view is created.",
            "- SQL errors and validation failures are recorded per query and produce a non-zero process status.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--query", action="append", type=parse_query_argument, default=[])
    parser.add_argument("--query-file", type=Path)
    parser.add_argument("--demo", action="store_true", help="Run a small set of project validation queries")
    parser.add_argument("--preview-rows", type=int, default=25)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.preview_rows < 0:
        print("ERROR: --preview-rows cannot be negative", file=sys.stderr)
        return 2
    database = args.database if args.database.is_absolute() else ROOT / args.database
    crosswalk = args.crosswalk if args.crosswalk.is_absolute() else ROOT / args.crosswalk
    report_path = args.report
    if report_path is None:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = ROOT / "reports" / f"batch_analysis_{stamp}.md"
    elif not report_path.is_absolute():
        report_path = ROOT / report_path

    try:
        specs: list[QuerySpec] = []
        if args.demo:
            specs.extend(demo_queries(crosswalk))
        if args.query_file:
            query_file = args.query_file if args.query_file.is_absolute() else ROOT / args.query_file
            specs.extend(parse_query_file(query_file, crosswalk))
        specs.extend(args.query)
        specs = ensure_unique_names(specs)
    except Exception as exc:
        print(f"ERROR: Could not load queries: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    batch = execute_batch(database, specs, preview_rows=args.preview_rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(batch), encoding="utf-8")
    print(f"Created: {report_path.relative_to(ROOT) if report_path.is_relative_to(ROOT) else report_path}")
    print(
        f"Connection: {batch.connection_status}; passed={sum(r.status == 'passed' for r in batch.query_results)}, "
        f"failed={sum(r.status != 'passed' for r in batch.query_results)}; closed={batch.connection_closed}"
    )
    return 0 if batch.connection_status == "connected_read_only" and all(
        result.status == "passed" for result in batch.query_results
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
