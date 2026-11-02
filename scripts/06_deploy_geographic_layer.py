#!/usr/bin/env python3
"""Deploy and preflight the approved Batch 06 geographic DuckDB layer."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_CROSSWALK = ROOT / "data/reference/bnetza_kba_district_crosswalk_2026.csv"
DEFAULT_SQL = ROOT / "sql/06_geographic_layer.sql"
DEFAULT_BACKUP_DIR = ROOT / "data/backups"
SOURCE_ID = "bnetza_charging_2026_09_30"
CROSSWALK_VERSION = "2026-07-01"
BNETZA_DATE = dt.date(2026, 9, 30)
KBA_DATE = dt.date(2026, 7, 1)
REFERENCE_TABLE = "reference.bnetza_kba_district_crosswalk_2026"
REGIONAL_VIEW = "analytics.charging_by_kba_district_2026_09_30"
COMBINED_VIEW = "analytics.kba_district_charging_vs_bev_2026"
STATE_VIEW = "analytics.charging_by_state"

CSV_COLUMNS = (
    "crosswalk_version",
    "bnetza_reference_date",
    "kba_reference_date",
    "bnetza_state_name",
    "bnetza_district_name",
    "bnetza_admin_type",
    "kba_state_name",
    "kba_district_code",
    "kba_district_name",
    "kba_admin_type",
    "mapping_status",
    "mapping_method",
    "verification_status",
    "mapping_note",
    "evidence_url",
    "equipment_rows",
    "declared_point_count",
    "charging_point_slots",
    "equipment_nominal_power_kw",
)
TARGET_COLUMNS = (
    "crosswalk_version",
    "bnetza_source_id",
    "bnetza_reference_date",
    "kba_reference_date",
    "bnetza_state_name",
    "bnetza_district_name",
    "bnetza_admin_type",
    "kba_state_name",
    "kba_district_code",
    "kba_district_name",
    "kba_admin_type",
    "mapping_status",
    "mapping_method",
    "verification_status",
    "mapping_note",
    "evidence_url",
    "equipment_rows",
    "declared_point_count",
    "charging_point_slots",
    "equipment_nominal_power_kw",
)
EXPECTED = {
    "equipment": 117_662,
    "points": 211_253,
    "district_rows": 1_200,
    "district_codes": 400,
    "crosswalk_rows": 401,
    "provisional_rows": 24,
}


class DeploymentError(RuntimeError):
    """Raised when a safe Batch 06 deployment cannot proceed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DeploymentError(message)


def scalar(conn: duckdb.DuckDBPyConnection, sql: str, params: tuple[Any, ...] = ()) -> Any:
    return conn.execute(sql, params).fetchone()[0]


def read_crosswalk(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"Missing crosswalk CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(tuple(reader.fieldnames or ()) == CSV_COLUMNS, "Crosswalk CSV schema changed")
        rows = list(reader)
    require(len(rows) == EXPECTED["crosswalk_rows"], f"Crosswalk rows: {len(rows)}")
    source_keys = [(row["bnetza_state_name"], row["bnetza_district_name"]) for row in rows]
    require(len(set(source_keys)) == EXPECTED["crosswalk_rows"], "Duplicate crosswalk source key")
    require(all(row["mapping_status"] == "mapped" for row in rows), "Crosswalk contains an unmapped row")
    require(
        sum(row["verification_status"].startswith("provisional") for row in rows)
        == EXPECTED["provisional_rows"],
        "Unexpected provisional mapping count",
    )
    codes = [row["kba_district_code"] for row in rows]
    require(all(re.fullmatch(r"[0-9]{5}", code or "") for code in codes), "Invalid KBA code in crosswalk")
    duplicate_codes = {code for code in codes if codes.count(code) > 1}
    require(duplicate_codes == {"07211"} and codes.count("07211") == 2, "Unexpected shared KBA code")
    return rows


def row_values(row: dict[str, str]) -> tuple[Any, ...]:
    return (
        row["crosswalk_version"],
        SOURCE_ID,
        dt.date.fromisoformat(row["bnetza_reference_date"]),
        dt.date.fromisoformat(row["kba_reference_date"]),
        row["bnetza_state_name"],
        row["bnetza_district_name"],
        row["bnetza_admin_type"] or None,
        row["kba_state_name"] or None,
        row["kba_district_code"] or None,
        row["kba_district_name"] or None,
        row["kba_admin_type"] or None,
        row["mapping_status"],
        row["mapping_method"],
        row["verification_status"],
        row["mapping_note"] or None,
        row["evidence_url"] or None,
        int(row["equipment_rows"]) if row["equipment_rows"] else None,
        int(row["declared_point_count"]) if row["declared_point_count"] else None,
        int(row["charging_point_slots"]) if row["charging_point_slots"] else None,
        float(row["equipment_nominal_power_kw"])
        if row["equipment_nominal_power_kw"]
        else None,
    )


def create_expected_crosswalk(conn: duckdb.DuckDBPyConnection, rows: list[dict[str, str]]) -> None:
    conn.execute(
        """
        CREATE OR REPLACE TEMP TABLE batch06_expected_crosswalk (
            crosswalk_version VARCHAR,
            bnetza_source_id VARCHAR,
            bnetza_reference_date DATE,
            kba_reference_date DATE,
            bnetza_state_name VARCHAR,
            bnetza_district_name VARCHAR,
            bnetza_admin_type VARCHAR,
            kba_state_name VARCHAR,
            kba_district_code VARCHAR,
            kba_district_name VARCHAR,
            kba_admin_type VARCHAR,
            mapping_status VARCHAR,
            mapping_method VARCHAR,
            verification_status VARCHAR,
            mapping_note VARCHAR,
            evidence_url VARCHAR,
            equipment_rows BIGINT,
            declared_point_count BIGINT,
            charging_point_slots BIGINT,
            equipment_nominal_power_kw DOUBLE
        )
        """
    )
    conn.executemany(
        "INSERT INTO batch06_expected_crosswalk VALUES (" + ",".join("?" for _ in TARGET_COLUMNS) + ")",
        [row_values(row) for row in rows],
    )


def object_type(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> str | None:
    schema, name = qualified_name.split(".", 1)
    row = conn.execute(
        """
        SELECT table_type
        FROM information_schema.tables
        WHERE table_schema = ? AND table_name = ?
        """,
        (schema, name),
    ).fetchone()
    return row[0] if row else None


def view_sql(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> str | None:
    schema, name = qualified_name.split(".", 1)
    row = conn.execute(
        """
        SELECT sql
        FROM duckdb_views()
        WHERE schema_name = ? AND view_name = ?
        """,
        (schema, name),
    ).fetchone()
    return row[0] if row else None


def describe_columns(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> list[tuple[str, str]]:
    return [(row[0], row[1]) for row in conn.execute(f"DESCRIBE {qualified_name}").fetchall()]


def read_sql_sections(path: Path) -> dict[str, str]:
    require(path.is_file(), f"Missing SQL deployment file: {path}")
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^-- name: ([a-z0-9_]+)\s*$", line)
        if match:
            current = match.group(1)
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def render_sql(sql: str, crosswalk: Path) -> str:
    replacements = {
        "{{CROSSWALK_CSV}}": sql_literal(str(crosswalk.resolve())),
        "{{SOURCE_ID}}": SOURCE_ID,
        "{{CROSSWALK_VERSION}}": CROSSWALK_VERSION,
        "{{BNETZA_DATE}}": BNETZA_DATE.isoformat(),
    }
    for token, value in replacements.items():
        sql = sql.replace(token, value)
    return sql


def assert_core_baseline(conn: duckdb.DuckDBPyConnection, rows: list[dict[str, str]]) -> dict[str, Any]:
    required = {
        "core.charging_equipment",
        "core.charging_point",
        "core.kba_district_ev_stock",
    }
    actual = {
        f"{row[0]}.{row[1]}"
        for row in conn.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            """
        ).fetchall()
    }
    require(required <= actual, "Required core table is missing")
    equipment = scalar(conn, "SELECT COUNT(*) FROM core.charging_equipment")
    points = scalar(conn, "SELECT COUNT(*) FROM core.charging_point")
    district_rows = scalar(conn, "SELECT COUNT(*) FROM core.kba_district_ev_stock")
    district_codes = scalar(conn, "SELECT COUNT(DISTINCT district_code) FROM core.kba_district_ev_stock")
    require(equipment == EXPECTED["equipment"], f"Equipment baseline failed: {equipment}")
    require(points == EXPECTED["points"], f"Point baseline failed: {points}")
    require(district_rows == EXPECTED["district_rows"], f"KBA district baseline failed: {district_rows}")
    require(district_codes == EXPECTED["district_codes"], f"KBA district codes failed: {district_codes}")
    source_ids = conn.execute(
        "SELECT source_id, COUNT(*) FROM core.charging_equipment GROUP BY source_id ORDER BY source_id"
    ).fetchall()
    require(source_ids == [(SOURCE_ID, EXPECTED["equipment"])], f"Unexpected BNetzA source IDs: {source_ids}")
    create_expected_crosswalk(conn, rows)
    source_geographies = scalar(
        conn,
        """
        SELECT COUNT(*) FROM (
            SELECT DISTINCT state_name, district_name
            FROM core.charging_equipment
        )
        """,
    )
    require(source_geographies == EXPECTED["crosswalk_rows"], f"Source geography count: {source_geographies}")
    equipment_mapping = conn.execute(
        """
        SELECT COUNT(*), COUNT(*) FILTER (WHERE matches = 0),
               COUNT(*) FILTER (WHERE matches <> 1)
        FROM (
            SELECT e.source_id, e.excel_row,
                   COUNT(c.bnetza_state_name) AS matches
            FROM core.charging_equipment e
            LEFT JOIN batch06_expected_crosswalk c
              ON c.bnetza_source_id = e.source_id
             AND c.bnetza_state_name = e.state_name
             AND c.bnetza_district_name = e.district_name
            GROUP BY e.source_id, e.excel_row
        )
        """
    ).fetchone()
    point_mapping = conn.execute(
        """
        SELECT COUNT(*), COUNT(*) FILTER (WHERE matches = 0),
               COUNT(*) FILTER (WHERE matches <> 1)
        FROM (
            SELECT p.source_id, p.equipment_excel_row, p.point_number,
                   COUNT(c.bnetza_state_name) AS matches
            FROM core.charging_point p
            LEFT JOIN core.charging_equipment e
              ON e.source_id = p.source_id
             AND e.excel_row = p.equipment_excel_row
            LEFT JOIN batch06_expected_crosswalk c
              ON c.bnetza_source_id = e.source_id
             AND c.bnetza_state_name = e.state_name
             AND c.bnetza_district_name = e.district_name
            GROUP BY p.source_id, p.equipment_excel_row, p.point_number
        )
        """
    ).fetchone()
    require(equipment_mapping == (EXPECTED["equipment"], 0, 0), f"Equipment mapping baseline: {equipment_mapping}")
    require(point_mapping == (EXPECTED["points"], 0, 0), f"Point mapping baseline: {point_mapping}")
    orphan_points = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM core.charging_point p
        LEFT JOIN core.charging_equipment e
          ON e.source_id = p.source_id
         AND e.excel_row = p.equipment_excel_row
        WHERE e.source_id IS NULL
        """,
    )
    duplicate_equipment_keys = scalar(
        conn,
        """
        SELECT COUNT(*) FROM (
            SELECT source_id, excel_row
            FROM core.charging_equipment
            GROUP BY 1, 2
            HAVING COUNT(*) <> 1
        )
        """,
    )
    duplicate_point_keys = scalar(
        conn,
        """
        SELECT COUNT(*) FROM (
            SELECT source_id, equipment_excel_row, point_number
            FROM core.charging_point
            GROUP BY 1, 2, 3
            HAVING COUNT(*) <> 1
        )
        """,
    )
    require(orphan_points == 0, f"Orphan point baseline: {orphan_points}")
    require(duplicate_equipment_keys == 0, f"Duplicate equipment baseline: {duplicate_equipment_keys}")
    require(duplicate_point_keys == 0, f"Duplicate point baseline: {duplicate_point_keys}")
    mismatch_equipment = scalar(
        conn,
        """
        SELECT COUNT(*) FROM (
            SELECT e.source_id, e.excel_row,
                   COALESCE(e.declared_point_count, 0) AS declared_points,
                   COUNT(p.point_number) AS point_slots
            FROM core.charging_equipment e
            LEFT JOIN core.charging_point p
              ON p.source_id = e.source_id
             AND p.equipment_excel_row = e.excel_row
            GROUP BY 1, 2, 3
            HAVING COALESCE(e.declared_point_count, 0) <> COUNT(p.point_number)
        )
        """,
    )
    require(mismatch_equipment == 0, f"Equipment/point mismatch baseline: {mismatch_equipment}")
    kba_dates = conn.execute(
        """
        SELECT reference_date, COUNT(*), COUNT(DISTINCT district_code)
        FROM core.kba_district_ev_stock
        GROUP BY reference_date
        ORDER BY reference_date
        """
    ).fetchall()
    require(
        kba_dates == [(dt.date(2026, 1, 1), 400, 400), (dt.date(2026, 4, 1), 400, 400), (KBA_DATE, 400, 400)],
        f"KBA date baseline: {kba_dates}",
    )
    state_sql = view_sql(conn, STATE_VIEW)
    require(state_sql is not None, "Existing analytics.charging_by_state view is missing")
    state_columns = describe_columns(conn, STATE_VIEW)
    require(
        [name for name, _ in state_columns]
        == ["state_name", "equipment_rows", "declared_points", "populated_point_slots"],
        f"Existing state-view columns changed: {state_columns}",
    )
    state_rows = conn.execute(
        "SELECT state_name, equipment_rows, declared_points, populated_point_slots "
        "FROM analytics.charging_by_state ORDER BY state_name"
    ).fetchall()
    require(len(state_rows) == 16, f"Existing state-view rows: {len(state_rows)}")
    return {
        "equipment_rows": equipment,
        "charging_point_rows": points,
        "kba_district_rows": district_rows,
        "kba_district_codes": district_codes,
        "equipment_mapping": equipment_mapping,
        "point_mapping": point_mapping,
        "orphan_points": orphan_points,
        "duplicate_equipment_keys": duplicate_equipment_keys,
        "duplicate_point_keys": duplicate_point_keys,
        "equipment_point_mismatches": mismatch_equipment,
        "kba_rows_by_date": kba_dates,
        "state_view_sql_before": state_sql,
        "state_view_rows_before": state_rows,
    }


def no_open_database_handles(database: Path) -> None:
    try:
        result = subprocess.run(
            ["lsof", "-t", str(database)],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise DeploymentError("Cannot verify DuckDB locks: lsof is unavailable") from exc
    handles = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    require(not handles, f"DuckDB has open process handles: {handles}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkpoint_if_needed(database: Path) -> dict[str, Any]:
    wal = Path(str(database) + ".wal")
    wal_before = {"exists": wal.exists(), "size": wal.stat().st_size if wal.exists() else 0}
    if wal_before["size"] > 0:
        no_open_database_handles(database)
        conn = duckdb.connect(str(database))
        try:
            conn.execute("CHECKPOINT")
        finally:
            conn.close()
        no_open_database_handles(database)
    wal_after = {"exists": wal.exists(), "size": wal.stat().st_size if wal.exists() else 0}
    require(wal_after["size"] == 0, f"Non-empty WAL remains after checkpoint: {wal_after}")
    return {"before": wal_before, "after": wal_after}


def create_backup(database: Path, backup_dir: Path, baseline: dict[str, Any]) -> dict[str, Any]:
    require(database.is_file(), f"Missing DuckDB database: {database}")
    no_open_database_handles(database)
    wal_state = checkpoint_if_needed(database)
    no_open_database_handles(database)
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"ev_charging_pre_batch06_{timestamp}.duckdb"
    require(not backup.exists(), f"Backup path already exists: {backup}")
    source_hash_before = sha256(database)
    source_size_before = database.stat().st_size
    shutil.copy2(database, backup)
    source_hash_after = sha256(database)
    require(source_hash_before == source_hash_after, "Database changed while creating backup")
    backup_hash = sha256(backup)
    require(backup_hash == source_hash_after, "Backup hash differs from source")
    require(backup.stat().st_size == source_size_before, "Backup size differs from source")
    no_open_database_handles(backup)
    backup_conn = duckdb.connect(str(backup), read_only=True)
    try:
        backup_counts = {
            "equipment_rows": scalar(backup_conn, "SELECT COUNT(*) FROM core.charging_equipment"),
            "charging_point_rows": scalar(backup_conn, "SELECT COUNT(*) FROM core.charging_point"),
            "kba_district_rows": scalar(backup_conn, "SELECT COUNT(*) FROM core.kba_district_ev_stock"),
            "state_view_rows": scalar(backup_conn, "SELECT COUNT(*) FROM analytics.charging_by_state"),
        }
    finally:
        backup_conn.close()
    require(backup_counts["equipment_rows"] == baseline["equipment_rows"], "Backup equipment count differs")
    require(backup_counts["charging_point_rows"] == baseline["charging_point_rows"], "Backup point count differs")
    require(backup_counts["kba_district_rows"] == baseline["kba_district_rows"], "Backup KBA count differs")
    require(backup_counts["state_view_rows"] == len(baseline["state_view_rows_before"]), "Backup state count differs")
    return {
        "path": str(backup),
        "size_bytes": backup.stat().st_size,
        "sha256": backup_hash,
        "wal": wal_state,
        "source_size_bytes": source_size_before,
        "source_sha256": source_hash_after,
        "counts": backup_counts,
    }


def reference_table_matches_csv(conn: duckdb.DuckDBPyConnection, rows: list[dict[str, str]]) -> bool:
    if object_type(conn, REFERENCE_TABLE) != "BASE TABLE":
        return False
    create_expected_crosswalk(conn, rows)
    columns = ", ".join(TARGET_COLUMNS)
    return scalar(
        conn,
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT {columns} FROM {REFERENCE_TABLE}
            EXCEPT ALL
            SELECT {columns} FROM batch06_expected_crosswalk
        )
        """,
    ) == 0 and scalar(
        conn,
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT {columns} FROM batch06_expected_crosswalk
            EXCEPT ALL
            SELECT {columns} FROM {REFERENCE_TABLE}
        )
        """,
    ) == 0


def existing_geographic_objects_are_valid(conn: duckdb.DuckDBPyConnection) -> bool:
    regional_type = object_type(conn, REGIONAL_VIEW)
    combined_type = object_type(conn, COMBINED_VIEW)
    if regional_type is None and combined_type is None:
        return False
    require(regional_type == "VIEW" and combined_type == "VIEW", "Existing geographic object has wrong type")
    regional_rows = scalar(conn, f"SELECT COUNT(*) FROM {REGIONAL_VIEW}")
    combined_rows = scalar(conn, f"SELECT COUNT(*) FROM {COMBINED_VIEW}")
    require(regional_rows == 400, f"Existing regional view is not validated: {regional_rows}")
    require(combined_rows == 1_200, f"Existing combined view is not validated: {combined_rows}")
    regional_sql = (view_sql(conn, REGIONAL_VIEW) or "").lower()
    combined_sql = (view_sql(conn, COMBINED_VIEW) or "").lower()
    required_regional_tokens = ("string_split", "source_id", "equipment_excel_row", "points_ge_150_kw")
    required_combined_tokens = ("kba_reference_date", "bev_per_registered_charging_point", "district_code")
    require(
        all(token in regional_sql for token in required_regional_tokens),
        "Existing regional view definition is not the approved Batch 06 definition",
    )
    require(
        all(token in combined_sql for token in required_combined_tokens),
        "Existing combined view definition is not the approved Batch 06 definition",
    )
    return True


def is_source_aware_state_view(sql: str) -> bool:
    normalized = " ".join(sql.lower().split())
    return (
        "group by source_id, equipment_excel_row" in normalized
        and "e.source_id = p.source_id" in normalized
    )


def run_deployment(
    database: Path,
    crosswalk: Path,
    sql_path: Path,
    backup_dir: Path,
) -> dict[str, Any]:
    rows = read_crosswalk(crosswalk)
    require(database.is_file(), f"Missing DuckDB database: {database}")
    baseline_conn = duckdb.connect(str(database), read_only=True)
    try:
        baseline = assert_core_baseline(baseline_conn, rows)
    finally:
        baseline_conn.close()
    backup = create_backup(database, backup_dir, baseline)
    sections = read_sql_sections(sql_path)
    required_sections = {
        "create_reference_schema",
        "create_reference_table",
        "insert_reference_rows",
        "charging_by_kba_district_view",
        "combined_kba_district_view",
        "source_aware_state_view",
    }
    require(required_sections <= sections.keys(), "SQL deployment file is missing a required section")
    conn = duckdb.connect(str(database))
    committed = False
    try:
        conn.execute("BEGIN")
        conn.execute(render_sql(sections["create_reference_schema"], crosswalk))
        table_exists = object_type(conn, REFERENCE_TABLE) is not None
        if table_exists:
            require(reference_table_matches_csv(conn, rows), "Existing reference table differs from approved CSV")
        else:
            conn.execute(render_sql(sections["create_reference_table"], crosswalk))
            conn.execute(render_sql(sections["insert_reference_rows"], crosswalk))
        require(reference_table_matches_csv(conn, rows), "Loaded reference table failed exact CSV validation")

        geographic_valid = existing_geographic_objects_are_valid(conn)
        if not geographic_valid:
            conn.execute(render_sql(sections["charging_by_kba_district_view"], crosswalk))
            conn.execute(render_sql(sections["combined_kba_district_view"], crosswalk))

        current_state_sql = view_sql(conn, STATE_VIEW)
        require(current_state_sql is not None, "Existing state view disappeared during deployment")
        if not is_source_aware_state_view(current_state_sql):
            conn.execute(render_sql(sections["source_aware_state_view"], crosswalk))
        post_state = conn.execute(
            "SELECT state_name, equipment_rows, declared_points, populated_point_slots "
            "FROM analytics.charging_by_state ORDER BY state_name"
        ).fetchall()
        require(post_state == baseline["state_view_rows_before"], "Source-aware state view changed baseline metrics")
        require(scalar(conn, f"SELECT COUNT(*) FROM {REGIONAL_VIEW}") == 400, "Regional view row check failed in transaction")
        require(scalar(conn, f"SELECT COUNT(*) FROM {COMBINED_VIEW}") == 1_200, "Combined view row check failed in transaction")
        conn.execute("COMMIT")
        committed = True
    except Exception:
        if not committed:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
        raise
    finally:
        conn.close()
    return {"baseline": baseline, "backup": backup}


def json_default(value: Any) -> str:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--sql", type=Path, default=DEFAULT_SQL)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--json", action="store_true", help="Print deployment evidence as JSON")
    args = parser.parse_args()
    database = args.database if args.database.is_absolute() else ROOT / args.database
    crosswalk = args.crosswalk if args.crosswalk.is_absolute() else ROOT / args.crosswalk
    sql_path = args.sql if args.sql.is_absolute() else ROOT / args.sql
    backup_dir = args.backup_dir if args.backup_dir.is_absolute() else ROOT / args.backup_dir
    try:
        evidence = run_deployment(database, crosswalk, sql_path, backup_dir)
    except Exception as exc:
        print(f"[FAIL] Batch 06 deployment: {exc}")
        return 1
    print("[PASS] Batch 06 database deployment transaction committed")
    print(f"[INFO] Verified backup: {evidence['backup']['path']}")
    if args.json:
        print(json.dumps(evidence, indent=2, default=json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
