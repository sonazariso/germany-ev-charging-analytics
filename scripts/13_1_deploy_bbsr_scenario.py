#!/usr/bin/env python3
"""Deploy the owner-approved Batch 13.1 BBSR-like charging scenario.

The scenario is a separate, versioned analytical layer.  It keeps the
official Batch 13 BBSR 2025 bridge and views unchanged, adds exactly two
owner-override reference rows, and overlays those rows on the existing
source-grain charging view.  No KBA vehicle stock is integrated.

Run a read-only preflight with::

    .venv/bin/python scripts/13_1_deploy_bbsr_scenario.py --dry-run --json

Deploy after preflight with::

    .venv/bin/python scripts/13_1_deploy_bbsr_scenario.py --json

The deployment creates and verifies an ignored timestamped backup before the
DuckDB write.  A later idempotency run can pass that verified backup through
``--backup-path``.
"""
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
import sys
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_OVERRIDE = ROOT / "data/reference/bnetza_bbsr_owner_override_2026.csv"
DEFAULT_MANIFEST = ROOT / "data/reference/bnetza_bbsr_owner_override_2026_manifest.json"
DEFAULT_CROSSWALK = ROOT / "data/reference/bnetza_kba_district_crosswalk_2026.csv"
DEFAULT_BBSR = ROOT / "data/reference/bbsr_settlement_types_2025.csv"
DEFAULT_AUDIT = ROOT / "reports/batch12_bbsr_integration_paths_audit.csv"
DEFAULT_SQL = ROOT / "sql/13_1_bbsr_scenario.sql"
DEFAULT_BACKUP_DIR = ROOT / "data/backups"

SOURCE_ID = "bnetza_charging_2026_09_30"
BNETZA_REFERENCE_DATE = dt.date(2026, 9, 30)
KBA_REFERENCE_DATE = dt.date(2026, 7, 1)
SCENARIO_VERSION = "batch13.1-2026-11-02-owner-approved-hanau-main-kinzig"
SOURCE_AUDIT_VERSION = "batch12-2026-11-02-two-path-strict-evidence"
SOURCE_AUDIT_SHA256 = "f4d681fc81ac700b73521b9da81689073df183f6664866e2dcb9397a89d9d644"
EXPECTED_BBSR_SHA256 = "e35c57da8d8f675fa132b629e6dda43180a18e5b78b95e1e72de30069a062e65"
EXPECTED_CROSSWALK_SHA256 = "fdf139c5057250184358e3014267a4a4c4259749113273f6bd48206f6a64fe6a"

CATEGORY_LABELS = {
    "1": "kreisfreie Großstadt",
    "2": "städtischer Kreis",
    "3": "ländlicher Kreis mit Verdichtungsansätzen",
    "4": "dünn besiedelter ländlicher Kreis",
}

EXPECTED = {
    "equipment": 117_662,
    "points": 211_253,
    "geographies": 401,
    "normal_points": 156_155,
    "fast_points": 55_098,
    "points_ge_150": 40_950,
    "points_ge_350": 6_950,
    "nominal_power_mw": 9_215.4173,
}

EXPECTED_SCENARIO_DISTRICTS = {"1": 68, "2": 132, "3": 98, "4": 103}

OVERRIDE_COLUMNS = (
    "scenario_version",
    "scenario_source_vintage",
    "bnetza_source_id",
    "bnetza_reference_date",
    "bnetza_state_name",
    "bnetza_district_name",
    "bnetza_admin_type",
    "geographic_code_system",
    "geographic_code",
    "kba_reference_date",
    "analytical_category_code",
    "analytical_category_name_de",
    "classification_method",
    "official_bbsr_verification",
    "official_bbsr_2025_type",
    "boundary_vintage",
    "boundary_compatibility_caveat",
    "override_provenance",
    "population_evidence_note",
    "evidence_source_urls",
    "source_audit_version",
    "source_audit_sha256",
)

SCENARIO_OBJECTS = (
    "reference.bnetza_bbsr_owner_override_2026",
    "analytics.charging_by_bbsr_district_2026_scenario",
    "analytics.charging_by_bbsr_type_2026_scenario",
)

BASELINE_OBJECTS = (
    "reference.bnetza_bbsr_district_bridge_2025",
    "analytics.charging_by_bbsr_district_2025",
    "analytics.charging_by_bbsr_type_2025",
    "reference.bnetza_kba_district_crosswalk_2026",
    "analytics.charging_by_kba_district_2026_09_30",
    "analytics.kba_district_charging_vs_bev_2026",
    "analytics.charging_by_state",
)

MAX_POWER_SQL = f"""
WITH tokens AS (
    SELECT
        source_id,
        equipment_excel_row,
        point_number,
        TRY_CAST(REPLACE(TRIM(token), ',', '.') AS DOUBLE) AS power_kw
    FROM core.charging_point
    CROSS JOIN LATERAL UNNEST(
        STRING_SPLIT(COALESCE(connector_power_raw, ''), ';')
    ) AS tokens(token)
), max_power AS (
    SELECT
        source_id,
        equipment_excel_row,
        point_number,
        MAX(power_kw) AS max_kw
    FROM tokens
    GROUP BY source_id, equipment_excel_row, point_number
)
SELECT
    COUNT(*) AS points,
    COUNT(*) FILTER (WHERE max_power.max_kw <= 22) AS normal_points,
    COUNT(*) FILTER (WHERE max_power.max_kw > 22) AS fast_points,
    COUNT(*) FILTER (WHERE max_power.max_kw >= 150) AS points_ge_150,
    COUNT(*) FILTER (WHERE max_power.max_kw >= 350) AS points_ge_350,
    COUNT(*) FILTER (WHERE max_power.max_kw IS NULL) AS unclassifiable_points
FROM core.charging_point
LEFT JOIN max_power USING (source_id, equipment_excel_row, point_number)
WHERE core.charging_point.source_id = '{SOURCE_ID}'
"""


class DeploymentError(RuntimeError):
    """Raised when a safe scenario deployment cannot proceed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DeploymentError(message)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scalar(conn: duckdb.DuckDBPyConnection, sql: str, params: Sequence[Any] = ()) -> Any:
    return conn.execute(sql, params).fetchone()[0]


def query_dicts(conn: duckdb.DuckDBPyConnection, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    result = conn.execute(sql, params)
    names = [item[0] for item in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"Missing CSV source: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(tuple(reader.fieldnames or ()) == OVERRIDE_COLUMNS, f"Unexpected scenario CSV schema: {reader.fieldnames}")
        return [dict(row) for row in reader]


def load_overrides(path: Path) -> list[dict[str, str]]:
    rows = read_csv_rows(path)
    require(len(rows) == 2, f"Owner-override row count must be exactly 2, got {len(rows)}")
    require({row["scenario_version"] for row in rows} == {SCENARIO_VERSION}, "Scenario version changed")
    require({row["bnetza_source_id"] for row in rows} == {SOURCE_ID}, "Unexpected BNetzA source identifier")
    require({row["bnetza_reference_date"] for row in rows} == {BNETZA_REFERENCE_DATE.isoformat()}, "Unexpected BNetzA reference date")
    require({row["kba_reference_date"] for row in rows} == {KBA_REFERENCE_DATE.isoformat()}, "Unexpected KBA code reference date")
    require({row["source_audit_version"] for row in rows} == {SOURCE_AUDIT_VERSION}, "Scenario source-audit version changed")
    require({row["source_audit_sha256"] for row in rows} == {SOURCE_AUDIT_SHA256}, "Scenario source-audit hash changed")
    require({row["geographic_code_system"] for row in rows} == {"KBA_DISTRICT_CODE"}, "Unexpected geographic code system")
    require({row["geographic_code"] for row in rows} == {"06415", "06435"}, "Unexpected scenario geographic codes")
    require({row["analytical_category_code"] for row in rows} == {"1", "2"}, "Unexpected scenario category codes")
    require(all(row["analytical_category_name_de"] == CATEGORY_LABELS[row["analytical_category_code"]] for row in rows), "Scenario category labels changed")
    require(all(row["official_bbsr_verification"].lower() == "false" for row in rows), "Owner overrides must not be officially verified")
    require(all(row["boundary_vintage"] == "2026" for row in rows), "Scenario boundary vintage changed")
    by_code = {row["geographic_code"]: row for row in rows}
    require(by_code["06415"]["bnetza_district_name"] == "Kreisfreie Stadt Hanau", "Hanau source identity changed")
    require(by_code["06415"]["classification_method"] == "OWNER_APPROVED_SCENARIO", "Hanau classification method changed")
    require(by_code["06415"]["official_bbsr_2025_type"] == "", "Hanau must have no official BBSR 2025 type")
    require(by_code["06435"]["bnetza_district_name"] == "Landkreis Main-Kinzig-Kreis", "Main-Kinzig source identity changed")
    require(by_code["06435"]["classification_method"] == "HISTORICAL_BBSR_CARRY_FORWARD", "Main-Kinzig classification method changed")
    require(by_code["06435"]["official_bbsr_2025_type"] == "2", "Main-Kinzig official BBSR 2025 type changed")
    require(all("not VERIFIED_COMPATIBLE" in row["override_provenance"] for row in rows), "Override provenance must not promote status")
    return rows


def validate_manifest(path: Path, override_path: Path, rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    require(path.is_file(), f"Missing scenario manifest: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    require(manifest["scenario_version"] == SCENARIO_VERSION, "Scenario manifest version changed")
    require(manifest["reference_file"] == "data/reference/bnetza_bbsr_owner_override_2026.csv", "Scenario manifest reference path changed")
    require(manifest["reference_sha256"] == sha256(override_path), "Scenario CSV hash differs from manifest")
    require(manifest["row_count"] == len(rows) == 2, "Scenario manifest row count failed")
    require(manifest["source_vintage"]["bnetza_source_id"] == SOURCE_ID, "Scenario manifest source ID changed")
    require(manifest["source_vintage"]["bnetza_reference_date"] == BNETZA_REFERENCE_DATE.isoformat(), "Scenario manifest BNetzA date changed")
    require(manifest["source_vintage"]["kba_reference_date"] == KBA_REFERENCE_DATE.isoformat(), "Scenario manifest KBA date changed")
    require(manifest["source_vintage"]["boundary_vintage"] == "2026", "Scenario manifest boundary vintage changed")
    require(manifest["source_audit"]["sha256"] == SOURCE_AUDIT_SHA256, "Scenario manifest audit hash changed")
    require(manifest["geographic_code"]["source_column"] == "kba_district_code", "Scenario geographic-code lineage changed")
    return manifest


def object_type(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> str | None:
    schema, name = qualified_name.split(".", 1)
    row = conn.execute(
        """
        SELECT table_type
        FROM information_schema.tables
        WHERE table_schema = ? AND table_name = ?
        """,
        [schema, name],
    ).fetchone()
    return row[0] if row else None


def describe_columns(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> list[tuple[str, str]]:
    return [(row[0], row[1]) for row in conn.execute(f"DESCRIBE {qualified_name}").fetchall()]


def view_sql(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> str | None:
    schema, name = qualified_name.split(".", 1)
    row = conn.execute(
        "SELECT sql FROM duckdb_views() WHERE schema_name = ? AND view_name = ?",
        [schema, name],
    ).fetchone()
    return row[0] if row else None


def stable_snapshot_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 8)
    if isinstance(value, (list, tuple)):
        return [stable_snapshot_value(item) for item in value]
    return value


def object_snapshot(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> dict[str, Any]:
    kind = object_type(conn, qualified_name)
    require(kind is not None, f"Baseline object is missing: {qualified_name}")
    try:
        rows = conn.execute(f"SELECT * FROM {qualified_name} ORDER BY ALL").fetchall()
    except duckdb.Error:
        rows = conn.execute(f"SELECT * FROM {qualified_name}").fetchall()
    payload = json.dumps(
        [stable_snapshot_value(row) for row in rows],
        ensure_ascii=False,
        default=str,
        separators=(",", ":"),
    )
    return {
        "type": kind,
        "columns": describe_columns(conn, qualified_name),
        "row_count": len(rows),
        "rows_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "view_sql": view_sql(conn, qualified_name) if kind == "VIEW" else None,
    }


def core_metrics(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    require(object_type(conn, "core.charging_equipment") == "BASE TABLE", "Equipment table is missing")
    require(object_type(conn, "core.charging_point") == "BASE TABLE", "Point table is missing")
    equipment = int(scalar(conn, "SELECT COUNT(*) FROM core.charging_equipment WHERE source_id = ?", [SOURCE_ID]))
    points = int(scalar(conn, "SELECT COUNT(*) FROM core.charging_point WHERE source_id = ?", [SOURCE_ID]))
    geographies = int(scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT DISTINCT state_name, district_name
            FROM core.charging_equipment
            WHERE source_id = ?
        )
    """, [SOURCE_ID]))
    declared = int(scalar(conn, "SELECT SUM(declared_point_count) FROM core.charging_equipment WHERE source_id = ?", [SOURCE_ID]))
    nominal_mw = float(scalar(conn, "SELECT SUM(equipment_nominal_power_kw) / 1000.0 FROM core.charging_equipment WHERE source_id = ?", [SOURCE_ID]))
    power = tuple(int(value) for value in conn.execute(MAX_POWER_SQL).fetchone())
    require((equipment, points, geographies) == (EXPECTED["equipment"], EXPECTED["points"], EXPECTED["geographies"]), "Core row baseline failed")
    require(declared == EXPECTED["points"], "Declared point total failed")
    require(abs(nominal_mw - EXPECTED["nominal_power_mw"]) < 0.00001, "Nominal power baseline failed")
    require(power == (
        EXPECTED["points"],
        EXPECTED["normal_points"],
        EXPECTED["fast_points"],
        EXPECTED["points_ge_150"],
        EXPECTED["points_ge_350"],
        0,
    ), f"Maximum-per-point power baseline failed: {power}")
    duplicate_equipment = int(scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT source_id, excel_row FROM core.charging_equipment
            WHERE source_id = ? GROUP BY source_id, excel_row HAVING COUNT(*) <> 1
        )
    """, [SOURCE_ID]))
    duplicate_points = int(scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT source_id, equipment_excel_row, point_number
            FROM core.charging_point WHERE source_id = ?
            GROUP BY source_id, equipment_excel_row, point_number HAVING COUNT(*) <> 1
        )
    """, [SOURCE_ID]))
    orphan_points = int(scalar(conn, """
        SELECT COUNT(*)
        FROM core.charging_point p
        LEFT JOIN core.charging_equipment e
          ON e.source_id = p.source_id AND e.excel_row = p.equipment_excel_row
        WHERE p.source_id = ? AND e.source_id IS NULL
    """, [SOURCE_ID]))
    mismatches = int(scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT e.source_id, e.excel_row,
                   COALESCE(e.declared_point_count, 0) AS declared_points,
                   COUNT(p.point_number) AS actual_points
            FROM core.charging_equipment e
            LEFT JOIN core.charging_point p
              ON p.source_id = e.source_id AND p.equipment_excel_row = e.excel_row
            WHERE e.source_id = ?
            GROUP BY e.source_id, e.excel_row, e.declared_point_count
            HAVING declared_points <> actual_points
        )
    """, [SOURCE_ID]))
    require((duplicate_equipment, duplicate_points, orphan_points, mismatches) == (0, 0, 0, 0), "Core key reconciliation failed")
    return {
        "equipment": equipment,
        "points": points,
        "geographies": geographies,
        "declared_points": declared,
        "nominal_power_mw": nominal_mw,
        "normal_points": power[1],
        "fast_points": power[2],
        "points_ge_150": power[3],
        "points_ge_350": power[4],
        "unclassifiable_points": power[5],
        "duplicate_equipment_keys": duplicate_equipment,
        "duplicate_point_keys": duplicate_points,
        "orphan_points": orphan_points,
        "equipment_point_mismatches": mismatches,
    }


def official_summary(conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    require(object_type(conn, "analytics.charging_by_bbsr_type_2025") == "VIEW", "Official Batch 13 BBSR summary is missing")
    rows = query_dicts(conn, "SELECT * FROM analytics.charging_by_bbsr_type_2025 ORDER BY settlement_type_code")
    require([row["settlement_type_code"] for row in rows] == ["1", "2", "3", "4", "UNCLASSIFIED"], "Official five-row summary changed")
    require(int(sum(row["district_count"] for row in rows)) == EXPECTED["geographies"], "Official district total failed")
    require(int(sum(row["charging_point_count"] for row in rows)) == EXPECTED["points"], "Official summary point total failed")
    require(int(rows[-1]["equipment_count"]) == 585 and int(rows[-1]["charging_point_count"]) == 991, "Official unclassified baseline changed")
    return rows


def baseline_state(conn: duckdb.DuckDBPyConnection, bbsr_path: Path, crosswalk_path: Path) -> dict[str, Any]:
    metrics = core_metrics(conn)
    official = official_summary(conn)
    required_counts = {
        "reference.bnetza_bbsr_district_bridge_2025": 401,
        "analytics.charging_by_bbsr_district_2025": 401,
        "analytics.charging_by_kba_district_2026_09_30": 400,
        "analytics.kba_district_charging_vs_bev_2026": 1_200,
        "analytics.charging_by_state": 16,
    }
    for name, expected_count in required_counts.items():
        require(object_type(conn, name) in {"BASE TABLE", "VIEW"}, f"Baseline object missing: {name}")
        require(int(scalar(conn, f"SELECT COUNT(*) FROM {name}")) == expected_count, f"Baseline object count changed: {name}")
    require(object_type(conn, "reference.bnetza_kba_district_crosswalk_2026") in {"BASE TABLE", "VIEW"}, "Existing Crosswalk table is missing")
    require(int(scalar(conn, "SELECT COUNT(*) FROM reference.bnetza_kba_district_crosswalk_2026")) == 401, "Existing Crosswalk count changed")
    require(sha256(bbsr_path) == EXPECTED_BBSR_SHA256, "Official BBSR reference CSV changed before deployment")
    require(sha256(crosswalk_path) == EXPECTED_CROSSWALK_SHA256, "Existing KBA Crosswalk CSV changed before deployment")
    objects = {name: object_snapshot(conn, name) for name in BASELINE_OBJECTS}
    return {"metrics": metrics, "official_summary": official, "existing_objects": objects}


def crosswalk_identifiers(conn: duckdb.DuckDBPyConnection, rows: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        matches = query_dicts(conn, """
            SELECT bnetza_source_id, bnetza_state_name, bnetza_district_name,
                   kba_reference_date, kba_district_code, kba_district_name
            FROM reference.bnetza_kba_district_crosswalk_2026
            WHERE bnetza_source_id = ?
              AND bnetza_state_name = ?
              AND bnetza_district_name = ?
        """, [row["bnetza_source_id"], row["bnetza_state_name"], row["bnetza_district_name"]])
        require(len(matches) == 1, f"Scenario source row is not uniquely present in the existing Crosswalk: {row['bnetza_district_name']}")
        match = matches[0]
        require(str(match["kba_reference_date"]) == KBA_REFERENCE_DATE.isoformat(), "Crosswalk KBA date changed for scenario row")
        require(match["kba_district_code"] == row["geographic_code"], f"Crosswalk code does not match scenario code for {row['bnetza_district_name']}")
        result.append(match)
    return result


def no_open_database_handles(database: Path) -> None:
    try:
        result = subprocess.run(["lsof", "-t", str(database)], check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise DeploymentError("Cannot verify DuckDB locks because lsof is unavailable") from exc
    handles = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    require(not handles, f"DuckDB has open process handles: {handles}")


def validate_backup(path: Path, baseline: Mapping[str, Any]) -> dict[str, Any]:
    require(path.is_file(), f"Missing verified backup: {path}")
    require(path.resolve() != DEFAULT_DATABASE.resolve(), "Backup path equals primary database")
    require(not Path(str(path) + ".wal").exists(), f"Backup WAL exists: {path}.wal")
    conn = duckdb.connect(str(path), read_only=True)
    try:
        actual = core_metrics(conn)
        for name, before in baseline["existing_objects"].items():
            require(object_snapshot(conn, name) == before, f"Backup baseline object differs: {name}")
    finally:
        conn.close()
    for key in ("equipment", "points", "geographies", "declared_points", "normal_points", "fast_points", "points_ge_150", "points_ge_350", "unclassifiable_points"):
        require(actual[key] == baseline["metrics"].get(key, actual[key]), f"Backup baseline differs for {key}")
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "validated_read_only": True,
        "metrics": actual,
    }


def create_backup(database: Path, backup_dir: Path, baseline: Mapping[str, Any]) -> dict[str, Any]:
    require(database.is_file(), f"Missing database: {database}")
    no_open_database_handles(database)
    wal = Path(str(database) + ".wal")
    require(not wal.exists(), f"Refusing to copy while a WAL exists: {wal}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"ev_charging_pre_batch13_1_{timestamp}.duckdb"
    require(not backup.exists(), f"Backup target already exists: {backup}")
    source_size_before = database.stat().st_size
    source_hash_before = sha256(database)
    shutil.copy2(database, backup)
    require(database.stat().st_size == source_size_before and sha256(database) == source_hash_before, "Database changed during backup")
    require(sha256(backup) == source_hash_before, "Backup checksum differs from source")
    evidence = validate_backup(backup, baseline)
    evidence.update({"source_sha256": source_hash_before, "source_size_bytes": source_size_before, "wal_present": False})
    return evidence


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


def render_sql(sql: str, override_path: Path) -> str:
    replacements = {
        "{{OVERRIDE_CSV}}": sql_literal(str(override_path.resolve())),
        "{{SCENARIO_VERSION}}": SCENARIO_VERSION,
        "{{SOURCE_ID}}": SOURCE_ID,
        "{{BNETZA_DATE}}": BNETZA_REFERENCE_DATE.isoformat(),
    }
    for token, value in replacements.items():
        sql = sql.replace(token, value)
    return sql


def normalized_db_value(column: str, value: Any) -> Any:
    if value == "":
        return None
    if column in {"bnetza_reference_date", "kba_reference_date"} and value is not None:
        return value.isoformat() if isinstance(value, dt.date) else str(value)
    if column == "official_bbsr_verification" and value is not None:
        return bool(value)
    return value


def expected_override_tuple(row: Mapping[str, str]) -> tuple[Any, ...]:
    return tuple(
        normalized_db_value(
            column,
            row[column].lower() == "true" if column == "official_bbsr_verification" and row[column] else row[column],
        )
        for column in OVERRIDE_COLUMNS
    )


def override_table_matches(conn: duckdb.DuckDBPyConnection, rows: Sequence[Mapping[str, str]]) -> bool:
    name = "reference.bnetza_bbsr_owner_override_2026"
    if object_type(conn, name) != "BASE TABLE":
        return False
    columns = ", ".join(OVERRIDE_COLUMNS)
    actual_rows = conn.execute(f"SELECT {columns} FROM {name} ORDER BY geographic_code").fetchall()
    actual = [
        tuple(normalized_db_value(column, value) for column, value in zip(OVERRIDE_COLUMNS, row))
        for row in actual_rows
    ]
    expected = sorted((expected_override_tuple(row) for row in rows), key=lambda value: value[8])
    return actual == expected


def assert_baseline_unchanged(conn: duckdb.DuckDBPyConnection, baseline: Mapping[str, Any]) -> None:
    for name, before in baseline["existing_objects"].items():
        require(object_snapshot(conn, name) == before, f"Existing official/KBA object changed: {name}")


def validate_scenario(
    conn: duckdb.DuckDBPyConnection,
    rows: Sequence[Mapping[str, str]],
    baseline: Mapping[str, Any],
) -> dict[str, Any]:
    override_name, district_name, type_name = SCENARIO_OBJECTS
    require(object_type(conn, override_name) == "BASE TABLE", "Scenario override table was not deployed")
    require(object_type(conn, district_name) == "VIEW", "Scenario district view was not deployed")
    require(object_type(conn, type_name) == "VIEW", "Scenario type view was not deployed")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {override_name}")) == 2, "Scenario override table must contain exactly two rows")
    require(override_table_matches(conn, rows), "Deployed scenario reference differs from the reproducible CSV")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {district_name}")) == EXPECTED["geographies"], "Scenario district coverage failed")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {type_name}")) == 4, "Scenario type view must contain four categories")
    duplicate_districts = int(scalar(conn, f"""
        SELECT COUNT(*) FROM (
            SELECT bnetza_source_id, bnetza_state_name, bnetza_district_name
            FROM {district_name}
            GROUP BY ALL HAVING COUNT(*) <> 1
        )
    """))
    require(duplicate_districts == 0, "Scenario duplicated a source district")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {district_name} WHERE scenario_category_code IS NULL")) == 0, "Scenario has unclassified districts")
    invalid_categories = int(scalar(conn, f"SELECT COUNT(*) FROM {district_name} WHERE scenario_category_code NOT IN ('1','2','3','4')"))
    require(invalid_categories == 0, "Scenario contains an invalid category")

    owner_rows = query_dicts(conn, f"""
        SELECT geographic_code, bnetza_district_name, scenario_category_code,
               scenario_classification_method, scenario_official_bbsr_verification,
               official_bbsr_2025_type, official_baseline_compatibility_status,
               equipment_count, charging_point_count, normal_charging_point_count,
               fast_charging_point_count, points_ge_150_kw, points_ge_350_kw,
               declared_equipment_nominal_power_kw
        FROM {district_name}
        WHERE geographic_code IS NOT NULL
        ORDER BY geographic_code
    """)
    require(len(owner_rows) == 2, "Scenario owner rows did not join to exactly two source districts")
    require({row["geographic_code"] for row in owner_rows} == {"06415", "06435"}, "Scenario owner codes changed")
    by_code = {row["geographic_code"]: row for row in owner_rows}
    require(by_code["06415"]["scenario_category_code"] == "1", "Hanau scenario category failed")
    require(by_code["06415"]["scenario_classification_method"] == "OWNER_APPROVED_SCENARIO", "Hanau scenario method failed")
    require(by_code["06415"]["scenario_official_bbsr_verification"] is False, "Hanau was silently marked official")
    require(by_code["06415"]["official_bbsr_2025_type"] is None, "Hanau received an official BBSR 2025 type")
    require(by_code["06415"]["official_baseline_compatibility_status"] == "UNRESOLVED", "Hanau official baseline status changed")
    require(by_code["06435"]["scenario_category_code"] == "2", "Main-Kinzig scenario category failed")
    require(by_code["06435"]["scenario_classification_method"] == "HISTORICAL_BBSR_CARRY_FORWARD", "Main-Kinzig scenario method failed")
    require(by_code["06435"]["scenario_official_bbsr_verification"] is False, "Main-Kinzig was silently marked official")
    require(by_code["06435"]["official_bbsr_2025_type"] == "2", "Main-Kinzig official BBSR 2025 type was not exposed")
    require(by_code["06435"]["official_baseline_compatibility_status"] == "CONDITIONAL_VINTAGE", "Main-Kinzig official baseline status changed")

    totals = query_dicts(conn, f"""
        SELECT SUM(equipment_count) equipment, SUM(charging_point_count) points,
               SUM(normal_charging_point_count) normal_points,
               SUM(fast_charging_point_count) fast_points,
               SUM(points_ge_150_kw) points_ge_150,
               SUM(points_ge_350_kw) points_ge_350,
               SUM(unclassifiable_power_point_count) unclassifiable_points,
               SUM(declared_equipment_nominal_power_kw) nominal_power_kw
        FROM {district_name}
    """)[0]
    actual_totals = {key: int(totals[key]) for key in ("equipment", "points", "normal_points", "fast_points", "points_ge_150", "points_ge_350", "unclassifiable_points")}
    expected_totals = {
        "equipment": EXPECTED["equipment"],
        "points": EXPECTED["points"],
        "normal_points": EXPECTED["normal_points"],
        "fast_points": EXPECTED["fast_points"],
        "points_ge_150": EXPECTED["points_ge_150"],
        "points_ge_350": EXPECTED["points_ge_350"],
        "unclassifiable_points": 0,
    }
    require(actual_totals == expected_totals, f"Scenario national charging totals failed: {actual_totals}")
    require(actual_totals["normal_points"] + actual_totals["fast_points"] == actual_totals["points"], "Scenario power bands do not reconcile")
    nominal_mw = float(totals["nominal_power_kw"]) / 1000.0
    require(abs(nominal_mw - EXPECTED["nominal_power_mw"]) < 0.00001, "Scenario nominal power total failed")

    summary = query_dicts(conn, f"SELECT * FROM {type_name} ORDER BY scenario_category_code")
    require([row["scenario_category_code"] for row in summary] == ["1", "2", "3", "4"], "Scenario category order failed")
    require({row["scenario_category_code"]: int(row["district_count"]) for row in summary} == EXPECTED_SCENARIO_DISTRICTS, "Scenario district counts failed")
    require(all(int(row["unclassified_district_count"]) == 0 for row in summary), "Scenario UNCLASSIFIED district count is not zero")
    for row in summary:
        require(int(row["normal_charging_point_count"]) + int(row["fast_charging_point_count"]) + int(row["unclassifiable_power_point_count"]) == int(row["charging_point_count"]), f"Scenario category point bands do not reconcile: {row['scenario_category_code']}")
    summary_totals = {key: sum(int(row[key]) for row in summary) for key in ("equipment_count", "charging_point_count", "normal_charging_point_count", "fast_charging_point_count", "points_ge_150_kw", "points_ge_350_kw", "unclassifiable_power_point_count")}
    require(summary_totals["equipment_count"] == EXPECTED["equipment"], "Scenario category equipment total failed")
    require(summary_totals["charging_point_count"] == EXPECTED["points"], "Scenario category point total failed")
    require(abs(sum(float(row["national_charging_point_share_pct"]) for row in summary) - 100.0) < 0.00001, "Scenario national point shares do not reconcile")
    require(all(row["point_share_denominator_scope"] == "ALL_REGISTERED_CHARGING_POINTS_INCLUDING_ALL_SCENARIO_DISTRICTS" for row in summary), "Scenario point-share denominator changed")

    trier = query_dicts(conn, f"""
        SELECT bnetza_district_name, official_bbsr_administrative_district_code,
               scenario_category_code, charging_point_count
        FROM {district_name}
        WHERE bnetza_district_name IN ('Kreisfreie Stadt Trier', 'Landkreis Trier-Saarburg')
        ORDER BY bnetza_district_name
    """)
    require(len(trier) == 2, "Trier city/county were not kept separate")
    require([(row["official_bbsr_administrative_district_code"], row["scenario_category_code"]) for row in trier] == [("07211000", "1"), ("07235000", "3")], "Trier scenario classifications changed")
    require(sum(int(row["charging_point_count"]) for row in trier) == 503, "Trier charging points changed")

    district_sql = (view_sql(conn, district_name) or "").lower()
    type_sql = (view_sql(conn, type_name) or "").lower()
    for name, sql in ((district_name, district_sql), (type_name, type_sql)):
        require("kba_district_ev_stock" not in sql and "bev" not in sql and "phev" not in sql, f"{name} unexpectedly references vehicle stock")
    require("analytics.charging_by_bbsr_district_2025" in district_sql, "Scenario does not preserve the official source-aware charging layer")

    override_counts = {
        code: {key: int(by_code[code][key]) for key in ("equipment_count", "charging_point_count", "normal_charging_point_count", "fast_charging_point_count", "points_ge_150_kw", "points_ge_350_kw")}
        for code in ("06415", "06435")
    }
    official_by_code = {row["settlement_type_code"]: row for row in baseline["official_summary"]}
    scenario_by_code = {row["scenario_category_code"]: row for row in summary}
    comparison = []
    for code in ("1", "2", "3", "4"):
        comparison.append({
            "category_code": code,
            "official_district_count": int(official_by_code[code]["district_count"]),
            "scenario_district_count": int(scenario_by_code[code]["district_count"]),
            "district_delta": int(scenario_by_code[code]["district_count"]) - int(official_by_code[code]["district_count"]),
            "official_equipment_count": int(official_by_code[code]["equipment_count"]),
            "scenario_equipment_count": int(scenario_by_code[code]["equipment_count"]),
            "equipment_delta": int(scenario_by_code[code]["equipment_count"]) - int(official_by_code[code]["equipment_count"]),
            "official_charging_point_count": int(official_by_code[code]["charging_point_count"]),
            "scenario_charging_point_count": int(scenario_by_code[code]["charging_point_count"]),
            "charging_point_delta": int(scenario_by_code[code]["charging_point_count"]) - int(official_by_code[code]["charging_point_count"]),
        })
    return {
        "override_rows": 2,
        "district_rows": int(scalar(conn, f"SELECT COUNT(*) FROM {district_name}")),
        "type_rows": len(summary),
        "scenario_unclassified_districts": int(scalar(conn, f"SELECT COUNT(*) FROM {district_name} WHERE scenario_category_code IS NULL")),
        "totals": actual_totals | {"nominal_power_mw": nominal_mw},
        "owner_override_counts": override_counts,
        "category_kpis": summary,
        "comparison_with_official_baseline": comparison,
        "trier_rows": trier,
    }


def json_default(value: Any) -> str:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return str(value)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--override", type=Path, default=DEFAULT_OVERRIDE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--bbsr", type=Path, default=DEFAULT_BBSR)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--sql", type=Path, default=DEFAULT_SQL)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--backup-path", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Run read-only preflight without backup or DuckDB writes")
    parser.add_argument("--json", action="store_true", help="Print deployment evidence as JSON")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict[str, Any]:
    database = resolve_path(args.database)
    override_path = resolve_path(args.override)
    manifest_path = resolve_path(args.manifest)
    crosswalk_path = resolve_path(args.crosswalk)
    bbsr_path = resolve_path(args.bbsr)
    audit_path = resolve_path(args.audit)
    sql_path = resolve_path(args.sql)
    backup_dir = resolve_path(args.backup_dir)
    require(database.is_file(), f"Missing database: {database}")
    require(crosswalk_path.is_file(), f"Missing Crosswalk CSV: {crosswalk_path}")
    require(bbsr_path.is_file(), f"Missing official BBSR CSV: {bbsr_path}")
    require(audit_path.is_file(), f"Missing Batch 12 audit CSV: {audit_path}")
    rows = load_overrides(override_path)
    manifest = validate_manifest(manifest_path, override_path, rows)
    require(sha256(args.audit if args.audit.is_absolute() else ROOT / args.audit) == SOURCE_AUDIT_SHA256, "Batch 12 audit CSV hash changed")

    read_conn = duckdb.connect(str(database), read_only=True)
    try:
        baseline = baseline_state(read_conn, bbsr_path, crosswalk_path)
        crosswalk_rows = crosswalk_identifiers(read_conn, rows)
        existing_scenario_objects = {
            name: object_snapshot(read_conn, name)
            for name in SCENARIO_OBJECTS
            if object_type(read_conn, name) is not None
        }
        preflight_scenario = None
        if existing_scenario_objects:
            require(len(existing_scenario_objects) == len(SCENARIO_OBJECTS), "Partial scenario deployment detected")
            preflight_scenario = validate_scenario(read_conn, rows, baseline)
        database_hash_before = sha256(database)
    finally:
        read_conn.close()

    evidence: dict[str, Any] = {
        "validation": "PASS",
        "mode": "DRY_RUN" if args.dry_run else "DEPLOY",
        "database": str(database),
        "scenario_reference": {
            "path": str(override_path),
            "sha256": sha256(override_path),
            "manifest_path": str(manifest_path),
            "manifest_sha256": sha256(manifest_path),
            "manifest_version": manifest["manifest_version"],
            "rows": len(rows),
        },
        "crosswalk_identifiers": crosswalk_rows,
        "baseline": {
            "metrics": baseline["metrics"],
            "official_summary": baseline["official_summary"],
            "database_sha256_before": database_hash_before,
        },
        "existing_scenario_before": existing_scenario_objects,
    }
    if preflight_scenario is not None:
        evidence["scenario"] = preflight_scenario
    if args.dry_run:
        return evidence

    backup_arg = resolve_path(args.backup_path) if args.backup_path is not None else None
    if backup_arg is not None:
        backup = validate_backup(backup_arg, baseline)
    else:
        backup = create_backup(database, backup_dir, baseline)
    evidence["backup"] = backup

    no_open_database_handles(database)
    sections = read_sql_sections(sql_path)
    required_sections = {
        "create_reference_schema",
        "create_analytics_schema",
        "create_override_table",
        "insert_override_rows",
        "charging_by_bbsr_district_view",
        "charging_by_bbsr_type_view",
    }
    require(required_sections <= sections.keys(), "Batch 13.1 SQL deployment sections are incomplete")

    conn = duckdb.connect(str(database))
    committed = False
    try:
        conn.execute("BEGIN")
        conn.execute(sections["create_reference_schema"])
        conn.execute(sections["create_analytics_schema"])
        override_name = "reference.bnetza_bbsr_owner_override_2026"
        existing_type = object_type(conn, override_name)
        if existing_type is None:
            conn.execute(render_sql(sections["create_override_table"], override_path))
            conn.execute(render_sql(sections["insert_override_rows"], override_path))
        else:
            require(existing_type == "BASE TABLE", f"Existing scenario override object has wrong type: {existing_type}")
        require(override_table_matches(conn, rows), "Scenario reference table differs from reproducible CSV")
        conn.execute(render_sql(sections["charging_by_bbsr_district_view"], override_path))
        conn.execute(render_sql(sections["charging_by_bbsr_type_view"], override_path))
        scenario = validate_scenario(conn, rows, baseline)
        assert_baseline_unchanged(conn, baseline)
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

    final_conn = duckdb.connect(str(database), read_only=True)
    try:
        final_scenario = validate_scenario(final_conn, rows, baseline)
        assert_baseline_unchanged(final_conn, baseline)
    finally:
        final_conn.close()
    require(sha256(override_path) == evidence["scenario_reference"]["sha256"], "Scenario CSV changed during deployment")
    require(sha256(bbsr_path) == EXPECTED_BBSR_SHA256, "Official BBSR reference CSV changed during deployment")
    require(sha256(crosswalk_path) == EXPECTED_CROSSWALK_SHA256, "Existing Crosswalk CSV changed during deployment")
    evidence["scenario"] = final_scenario
    evidence["existing_official_and_kba_unchanged"] = True
    evidence["source_fingerprints"] = {
        "database_sha256_before": database_hash_before,
        "official_bbsr_csv_sha256": sha256(bbsr_path),
        "crosswalk_csv_sha256": sha256(crosswalk_path),
        "batch12_audit_sha256": sha256(audit_path if audit_path.is_absolute() else ROOT / audit_path),
        "override_csv_sha256": sha256(override_path),
        "sql_sha256": sha256(sql_path),
    }
    return evidence


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        evidence = run(args)
    except (DeploymentError, OSError, ValueError, TypeError, duckdb.Error, json.JSONDecodeError) as exc:
        print(f"[FAIL] Batch 13.1 scenario deployment: {exc}", file=sys.stderr)
        return 1
    if args.dry_run:
        print("[PASS] Batch 13.1 read-only preflight passed")
    else:
        print("[PASS] Batch 13.1 scenario deployment transaction committed")
        print(f"[INFO] Verified backup: {evidence['backup']['path']}")
    if args.json:
        print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True, default=json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
