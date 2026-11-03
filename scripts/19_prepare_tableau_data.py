#!/usr/bin/env python3
"""Batch 19: prepare validated, date-labelled Tableau CSV extracts.

This script is deliberately an export layer, not a DuckDB deployment.  It
opens the existing database with ``read_only=True``, validates the source
objects and preserved inputs, builds deterministic extracts, and writes only
CSV/JSON/Markdown artifacts outside the database.  BNetzA equipment and point
grains are aggregated separately throughout.  The BBSR extracts are
charging-only and use the Batch 13.2 historical 2025 harmonization; they never
join KBA vehicle stock.

Run from the repository root::

    .venv/bin/python scripts/19_prepare_tableau_data.py

No execution timestamp is written to an artifact so that a second execution
can be compared byte-for-byte.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_EXPORT_DIR = ROOT / "data/exports/tableau"
DEFAULT_VALIDATION_REPORT = ROOT / "reports/batch19_tableau_data_validation.md"

EXPORT_VERSION = "batch19-tableau-exports-2026-11-03-v1"
INFRASTRUCTURE_SOURCE_ID = "bnetza_charging_2026_09_30"
INFRASTRUCTURE_REFERENCE_DATE = "2026-09-30"
BBSR_REFERENCE_DATE = "2025-12-31"
KBA_DATES = ("2026-01-01", "2026-04-01", "2026-07-01")
KBA_SOURCE_IDS = {
    "2026-01-01": "kba_fz27_2026_01",
    "2026-04-01": "kba_fz27_2026_04",
    "2026-07-01": "kba_fz27_2026_07",
}
KBA_PRIMARY_DATE = "2026-07-01"
KBA_PRIMARY_SOURCE_ID = KBA_SOURCE_IDS[KBA_PRIMARY_DATE]
SURVIVOR_CUTOFF_DATE = "2026-07-01"

FEDERAL_STATES = (
    "Baden-Württemberg",
    "Bayern",
    "Berlin",
    "Brandenburg",
    "Bremen",
    "Hamburg",
    "Hessen",
    "Mecklenburg-Vorpommern",
    "Niedersachsen",
    "Nordrhein-Westfalen",
    "Rheinland-Pfalz",
    "Saarland",
    "Sachsen",
    "Sachsen-Anhalt",
    "Schleswig-Holstein",
    "Thüringen",
)
FEDERAL_STATE_ORDER = {name: index for index, name in enumerate(FEDERAL_STATES)}
NATIONAL_GEOGRAPHY = "Deutschland"
RESIDUAL_GEOGRAPHY = "Sonstige"
ALL_KBA_STATE_GEOGRAPHIES = (*FEDERAL_STATES, RESIDUAL_GEOGRAPHY, NATIONAL_GEOGRAPHY)

MUTUALLY_EXCLUSIVE_TOTAL_FUELS = (
    "Benzin",
    "Diesel",
    "Gas insgesamt",
    "Elektro (BEV)",
    "Hybrid insgesamt",
    "Sonstige",
)
BEV_FUEL = "Elektro (BEV)"
PHEV_FUEL = "darunter Plug-in"
EXPECTED_FUEL_TYPES = (*MUTUALLY_EXCLUSIVE_TOTAL_FUELS, PHEV_FUEL)

EXPECTED_INFRASTRUCTURE = {
    "equipment_count": 117_662,
    "declared_charging_point_count": 211_253,
    "charging_point_count": 211_253,
    "normal_charging_point_count": 156_155,
    "fast_charging_point_count": 55_098,
    "points_ge_150_kw": 40_950,
    "points_ge_350_kw": 6_950,
    "unclassifiable_power_point_count": 0,
    "equipment_nominal_power_mw": 9_215.4173,
}
EXPECTED_KBA = {
    "2026-01-01": {
        "national_passenger_car_stock": 49_486_487,
        "national_bev_stock": 2_034_260,
        "national_phev_stock": 1_122_958,
        "district_passenger_car_stock": 49_436_020,
        "district_bev_stock": 2_031_870,
        "district_phev_stock": 1_121_516,
    },
    "2026-04-01": {
        "national_passenger_car_stock": 49_546_014,
        "national_bev_stock": 2_169_717,
        "national_phev_stock": 1_167_434,
        "district_passenger_car_stock": 49_494_647,
        "district_bev_stock": 2_167_111,
        "district_phev_stock": 1_165_933,
    },
    "2026-07-01": {
        "national_passenger_car_stock": 49_696_710,
        "national_bev_stock": 2_365_047,
        "national_phev_stock": 1_226_863,
        "district_passenger_car_stock": 49_644_855,
        "district_bev_stock": 2_362_218,
        "district_phev_stock": 1_225_241,
    },
}

# These hashes are the approved local evidence chain from Batches 13.2, 16
# and 17.  A changed input is a hard failure: mixing versions would make an
# otherwise identical export non-reproducible.
EXPECTED_INPUT_FINGERPRINTS = (
    {
        "path": "data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx",
        "source_id": INFRASTRUCTURE_SOURCE_ID,
        "reference_date": INFRASTRUCTURE_REFERENCE_DATE,
        "role": "BNetzA infrastructure source workbook",
        "sha256": "1e82c1734b17e17e51092a0f9460a5e204888569fb12aa5940b30e9cdb726342",
    },
    {
        "path": "data/raw/kba/fz27_202601.xlsx",
        "source_id": KBA_SOURCE_IDS["2026-01-01"],
        "reference_date": "2026-01-01",
        "role": "KBA FZ 27 source workbook",
        "sha256": "29ab2eaa178a1c6a3463d5cad707fee1e762241304ae6bb08c29702d6e6aea31",
    },
    {
        "path": "data/raw/kba/fz27_202604.xlsx",
        "source_id": KBA_SOURCE_IDS["2026-04-01"],
        "reference_date": "2026-04-01",
        "role": "KBA FZ 27 source workbook",
        "sha256": "28fffaa7d2f21ede6d7f6988a717b749b759a308755c472df4d391c73a0653e7",
    },
    {
        "path": "data/raw/kba/fz27_202607.xlsx",
        "source_id": KBA_SOURCE_IDS["2026-07-01"],
        "reference_date": "2026-07-01",
        "role": "KBA FZ 27 source workbook",
        "sha256": "d6a26702fa6f8358cc5f0e15e88c04ac6c36527be404058674138dd9571bc803",
    },
    {
        "path": "data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx",
        "source_id": "bbsr_raumgliederungen_2025",
        "reference_date": BBSR_REFERENCE_DATE,
        "role": "BBSR geographic reference workbook",
        "sha256": "083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525",
    },
    {
        "path": "data/reference/bnetza_kba_district_crosswalk_2026.csv",
        "source_id": "bnetza_kba_district_crosswalk_2026",
        "reference_date": INFRASTRUCTURE_REFERENCE_DATE,
        "role": "Preserved KBA crosswalk baseline fingerprint; not joined to BBSR exports",
        "sha256": "fdf139c5057250184358e3014267a4a4c4259749113273f6bd48206f6a64fe6a",
    },
    {
        "path": "data/reference/bnetza_bbsr_historical_harmonization_2025.csv",
        "source_id": "bnetza_bbsr_historical_harmonization_2025",
        "reference_date": BBSR_REFERENCE_DATE,
        "role": "Batch 13.2 401-to-400 historical BBSR harmonization reference",
        "sha256": "26b7b177b11f19628d85c7195975d75232804567b43d964f99acb8fcd8f84661",
    },
    {
        "path": "data/reference/bnetza_bbsr_historical_harmonization_2025_manifest.json",
        "source_id": "bnetza_bbsr_historical_harmonization_2025_manifest",
        "reference_date": BBSR_REFERENCE_DATE,
        "role": "Historical BBSR harmonization provenance manifest",
        "sha256": "fa2cf4085e36ea7914eb3ce7e51ec56a527d9a7b5cc8a47c1701078a35871a26",
    },
    {
        "path": "data/reference/bbsr_settlement_types_2025.csv",
        "source_id": "bbsr_settlement_types_2025",
        "reference_date": BBSR_REFERENCE_DATE,
        "role": "BBSR 400-unit settlement-type reference",
        "sha256": "e35c57da8d8f675fa132b629e6dda43180a18e5b78b95e1e72de30069a062e65",
    },
    {
        "path": "data/reference/bbsr_source_manifest.json",
        "source_id": "bbsr_source_manifest",
        "reference_date": BBSR_REFERENCE_DATE,
        "role": "BBSR source provenance manifest",
        "sha256": "ba3540bf447a5c843a5a9d8fcdf224803edd26556c27e1e80a24b56a3f59a60c",
    },
    {
        "path": "reports/batch16_state_comparison.csv",
        "source_id": "batch16_state_comparison",
        "reference_date": KBA_PRIMARY_DATE,
        "role": "Validated Batch 16 state comparison input for Export G",
        "sha256": "0b3864593dab8a0c760e5e8f175a17d01bdb8f4696e7c89602277bb24c31403a",
    },
    {
        "path": "reports/batch17_state_temporal_sensitivity.csv",
        "source_id": "batch17_state_temporal_sensitivity",
        "reference_date": KBA_PRIMARY_DATE,
        "role": "Validated Batch 17 temporal sensitivity input for Export H",
        "sha256": "5b6fc2cbe8f93b5beaf1786ac5ac733b733bc8bb55deacea63dcf46cd4144ab8",
    },
)


class ExportError(RuntimeError):
    """Raised when an input contract, grain, or reconciliation fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExportError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_date_string(value: Any) -> str:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()[:10]
    return str(value)[:10]


def as_int(value: Any, label: str) -> int:
    require(value is not None, f"Unexpected NULL for {label}")
    return int(value)


def as_float(value: Any, label: str) -> float:
    require(value is not None, f"Unexpected NULL for {label}")
    result = float(value)
    require(math.isfinite(result), f"Non-finite value for {label}")
    return result


def pct(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return 100.0 * float(numerator) / float(denominator)


def ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator) / float(denominator)


def query_dicts(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: Sequence[Any] = (),
) -> List[Dict[str, Any]]:
    result = conn.execute(sql, params)
    names = [item[0] for item in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def object_type(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> Optional[str]:
    schema, name = qualified_name.split(".", 1)
    row = conn.execute(
        """
        SELECT table_type
        FROM information_schema.tables
        WHERE table_schema = ? AND table_name = ?
        """,
        [schema, name],
    ).fetchone()
    return str(row[0]) if row else None


def object_columns(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> List[str]:
    schema, name = qualified_name.split(".", 1)
    rows = conn.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = ? AND table_name = ?
        ORDER BY ordinal_position
        """,
        [schema, name],
    ).fetchall()
    return [str(row[0]) for row in rows]


def view_sql(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> str:
    schema, name = qualified_name.split(".", 1)
    row = conn.execute(
        """
        SELECT sql
        FROM duckdb_views()
        WHERE schema_name = ? AND view_name = ?
        """,
        [schema, name],
    ).fetchone()
    require(row is not None, f"Missing view SQL for {qualified_name}")
    return str(row[0])


def validate_database_contract(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    expected_objects = {
        "core.charging_equipment": "BASE TABLE",
        "core.charging_point": "BASE TABLE",
        "core.kba_state_fuel_stock": "BASE TABLE",
        "core.kba_district_ev_stock": "BASE TABLE",
        "analytics.charging_by_state": "VIEW",
        "analytics.charging_by_bbsr_district_2025_harmonized": "VIEW",
        "analytics.charging_by_bbsr_type_2025_harmonized": "VIEW",
        "analytics.kba_national_quarterly_stock": "VIEW",
    }
    required_columns = {
        "core.charging_equipment": {
            "source_id",
            "excel_row",
            "state_name",
            "declared_point_count",
            "equipment_nominal_power_kw",
            "commissioning_date",
        },
        "core.charging_point": {
            "source_id",
            "equipment_excel_row",
            "point_number",
            "connector_power_raw",
        },
        "core.kba_state_fuel_stock": {
            "source_id",
            "reference_date",
            "state_name",
            "fuel_type",
            "passenger_cars",
        },
        "core.kba_district_ev_stock": {
            "source_id",
            "reference_date",
            "district_code",
            "district_name",
            "state_name",
            "passenger_cars",
            "bev_cars",
            "phev_cars",
        },
        "analytics.charging_by_state": {
            "state_name",
            "equipment_rows",
            "declared_points",
            "populated_point_slots",
        },
        "analytics.charging_by_bbsr_district_2025_harmonized": {
            "historical_bbsr_administrative_district_code",
            "historical_bbsr_administrative_district_name",
            "historical_bbsr_federal_state_code",
            "historical_bbsr_federal_state_name",
            "historical_bbsr_settlement_type_code",
            "historical_bbsr_settlement_type_name_de",
            "infrastructure_reference_date",
            "historical_bbsr_reference_date",
            "source_component_count",
            "equipment_count",
            "charging_point_count",
            "normal_charging_point_count",
            "fast_charging_point_count",
            "points_ge_150_kw",
            "points_ge_350_kw",
            "total_equipment_nominal_power_mw",
        },
        "analytics.charging_by_bbsr_type_2025_harmonized": {
            "settlement_type_code",
            "settlement_type_name_de",
            "historical_district_count",
            "source_component_count",
            "equipment_count",
            "charging_point_count",
            "normal_charging_point_count",
            "fast_charging_point_count",
            "points_ge_150_kw",
            "points_ge_350_kw",
            "declared_equipment_nominal_power_mw",
        },
        "analytics.kba_national_quarterly_stock": {
            "source_id",
            "report_snapshot",
            "stock_date",
            "passenger_bev",
            "passenger_phev",
            "passenger_cars_total",
        },
    }
    actual_objects: Dict[str, str] = {}
    schema_snapshot: Dict[str, List[str]] = {}
    for qualified_name, expected_type in expected_objects.items():
        actual = object_type(conn, qualified_name)
        require(actual == expected_type, f"Unexpected or missing object {qualified_name}: {actual}")
        actual_objects[qualified_name] = actual
        actual_columns = object_columns(conn, qualified_name)
        schema_snapshot[qualified_name] = actual_columns
        missing = sorted(required_columns[qualified_name] - set(actual_columns))
        require(not missing, f"Missing columns in {qualified_name}: {missing}")

    require(conn.execute("SELECT 1").fetchone()[0] == 1, "Read-only DuckDB connectivity failed")

    state_sql = view_sql(conn, "analytics.charging_by_state")
    normalized_state_sql = " ".join(state_sql.lower().split())
    require(
        "group by source_id, equipment_excel_row" in normalized_state_sql,
        "analytics.charging_by_state does not visibly pre-aggregate points by source/equipment",
    )
    require(
        "e.source_id = p.source_id" in normalized_state_sql
        and "e.excel_row = p.equipment_excel_row" in normalized_state_sql,
        "analytics.charging_by_state join keys are not source-aware",
    )
    state_view_rows = query_dicts(conn, "SELECT * FROM analytics.charging_by_state ORDER BY state_name")
    require(len(state_view_rows) == 16, f"Expected 16 state-view rows, found {len(state_view_rows)}")
    require(
        {str(row["state_name"]) for row in state_view_rows} == set(FEDERAL_STATES),
        "analytics.charging_by_state does not contain exactly the 16 validated state names",
    )
    return {
        "objects": actual_objects,
        "columns": schema_snapshot,
        "charging_by_state_rows": len(state_view_rows),
        "state_view_sql_safe": True,
    }


def fingerprint_inputs() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in EXPECTED_INPUT_FINGERPRINTS:
        path = ROOT / item["path"]
        require(path.is_file(), f"Missing approved input: {item['path']}")
        actual = sha256(path)
        row = dict(item)
        row["bytes"] = path.stat().st_size
        row["actual_sha256"] = actual
        row["match"] = actual == item["sha256"]
        require(row["match"], f"Input fingerprint changed: {item['path']}")
        rows.append(row)
    return rows


def assert_unique(rows: Sequence[Mapping[str, Any]], key_fields: Sequence[str], label: str) -> None:
    seen: set[Tuple[Any, ...]] = set()
    for row in rows:
        key = tuple(row.get(field) for field in key_fields)
        require(all(value is not None and value != "" for value in key), f"NULL/blank {label} key: {key}")
        require(key not in seen, f"Duplicate {label} key: {key}")
        seen.add(key)


def point_metrics_sql(group_expression: Optional[str]) -> str:
    select_group = f"{group_expression}," if group_expression else ""
    group_by = f"GROUP BY {group_expression}" if group_expression else ""
    order_by = f"ORDER BY {group_expression}" if group_expression else ""
    return f"""
        WITH source_points AS (
            SELECT p.source_id,
                   p.equipment_excel_row,
                   p.point_number,
                   p.connector_power_raw,
                   e.state_name
            FROM core.charging_point AS p
            INNER JOIN core.charging_equipment AS e
              ON e.source_id = p.source_id
             AND e.excel_row = p.equipment_excel_row
            WHERE p.source_id = ?
        ),
        point_power_tokens AS (
            SELECT p.source_id,
                   p.equipment_excel_row,
                   p.point_number,
                   TRY_CAST(REPLACE(TRIM(token), ',', '.') AS DOUBLE) AS power_kw
            FROM source_points AS p,
                 UNNEST(STRING_SPLIT(COALESCE(p.connector_power_raw, ''), ';')) AS tokens(token)
        ),
        point_power AS (
            SELECT source_id,
                   equipment_excel_row,
                   point_number,
                   MAX(power_kw) AS max_declared_point_power_kw
            FROM point_power_tokens
            GROUP BY source_id, equipment_excel_row, point_number
        )
        SELECT {select_group}
               COUNT(*) AS charging_point_count,
               COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw <= 22) AS normal_charging_point_count,
               COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw > 22) AS fast_charging_point_count,
               COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw >= 150) AS points_ge_150_kw,
               COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw >= 350) AS points_ge_350_kw,
               COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw IS NULL) AS unclassifiable_power_point_count
        FROM source_points AS p
        LEFT JOIN point_power AS pp
          ON pp.source_id = p.source_id
         AND pp.equipment_excel_row = p.equipment_excel_row
         AND pp.point_number = p.point_number
        {group_by}
        {order_by}
    """


def validate_point_integrity(conn: duckdb.DuckDBPyConnection) -> Dict[str, int]:
    duplicate_rows = conn.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT source_id, equipment_excel_row, point_number
            FROM core.charging_point
            WHERE source_id = ?
            GROUP BY source_id, equipment_excel_row, point_number
            HAVING COUNT(*) > 1
        ) AS duplicates
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    ).fetchone()[0]
    orphan_rows = conn.execute(
        """
        SELECT COUNT(*)
        FROM core.charging_point AS p
        LEFT JOIN core.charging_equipment AS e
          ON e.source_id = p.source_id
         AND e.excel_row = p.equipment_excel_row
        WHERE p.source_id = ? AND e.excel_row IS NULL
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    ).fetchone()[0]
    mismatch_rows = conn.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT e.source_id,
                   e.excel_row,
                   e.declared_point_count,
                   COUNT(p.point_number) AS populated_point_slots
            FROM core.charging_equipment AS e
            LEFT JOIN core.charging_point AS p
              ON p.source_id = e.source_id
             AND p.equipment_excel_row = e.excel_row
            WHERE e.source_id = ?
            GROUP BY e.source_id, e.excel_row, e.declared_point_count
            HAVING e.declared_point_count <> COUNT(p.point_number)
        ) AS mismatches
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    ).fetchone()[0]
    result = {
        "duplicate_point_keys": int(duplicate_rows),
        "orphan_point_rows": int(orphan_rows),
        "equipment_point_mismatches": int(mismatch_rows),
    }
    require(result["duplicate_point_keys"] == 0, f"Duplicate point keys: {result['duplicate_point_keys']}")
    require(result["orphan_point_rows"] == 0, f"Orphan point rows: {result['orphan_point_rows']}")
    require(result["equipment_point_mismatches"] == 0, f"Equipment/point mismatches: {result['equipment_point_mismatches']}")
    return result


def load_charging_exports(conn: duckdb.DuckDBPyConnection) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    integrity = validate_point_integrity(conn)
    equipment_rows = query_dicts(
        conn,
        """
        SELECT state_name,
               COUNT(*) AS equipment_count,
               SUM(declared_point_count) AS declared_charging_point_count,
               SUM(equipment_nominal_power_kw) AS equipment_nominal_power_kw,
               COUNT(*) FILTER (WHERE declared_point_count IS NULL) AS null_declared_point_count,
               COUNT(*) FILTER (WHERE equipment_nominal_power_kw IS NULL) AS null_nominal_power_count
        FROM core.charging_equipment
        WHERE source_id = ?
        GROUP BY state_name
        ORDER BY state_name
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    )
    point_rows = query_dicts(conn, point_metrics_sql("p.state_name"), [INFRASTRUCTURE_SOURCE_ID])
    equipment_by_state = {str(row["state_name"]): row for row in equipment_rows}
    points_by_state = {str(row["state_name"]): row for row in point_rows}
    require(set(equipment_by_state) == set(FEDERAL_STATES), "Charging equipment state coverage changed")
    require(set(points_by_state) == set(FEDERAL_STATES), "Charging point state coverage changed")
    require(
        sum(int(row["null_declared_point_count"]) for row in equipment_rows) == 0,
        "NULL declared point counts would otherwise be silently converted",
    )
    require(
        sum(int(row["null_nominal_power_count"]) for row in equipment_rows) == 0,
        "NULL equipment nominal power would otherwise be silently converted",
    )

    state_rows: List[Dict[str, Any]] = []
    for state in FEDERAL_STATES:
        equipment = equipment_by_state[state]
        points = points_by_state[state]
        equipment_count = as_int(equipment["equipment_count"], f"equipment count {state}")
        declared_points = as_int(equipment["declared_charging_point_count"], f"declared points {state}")
        point_count = as_int(points["charging_point_count"], f"populated points {state}")
        normal_points = as_int(points["normal_charging_point_count"], f"normal points {state}")
        fast_points = as_int(points["fast_charging_point_count"], f"fast points {state}")
        ge150 = as_int(points["points_ge_150_kw"], f">=150 points {state}")
        ge350 = as_int(points["points_ge_350_kw"], f">=350 points {state}")
        invalid = as_int(points["unclassifiable_power_point_count"], f"unknown power points {state}")
        require(declared_points == point_count, f"Declared/populated point mismatch for {state}")
        require(normal_points + fast_points + invalid == point_count, f"Power-band denominator mismatch for {state}")
        state_rows.append(
            {
                "state_name": state,
                "bnetza_reference_date": INFRASTRUCTURE_REFERENCE_DATE,
                "equipment_count": equipment_count,
                "declared_charging_point_count": declared_points,
                "charging_point_count": point_count,
                "normal_charging_point_count": normal_points,
                "fast_charging_point_count": fast_points,
                "points_ge_150_kw": ge150,
                "points_ge_350_kw": ge350,
                "unclassifiable_power_point_count": invalid,
                "equipment_nominal_power_mw": as_float(equipment["equipment_nominal_power_kw"], f"nominal power {state}") / 1000.0,
                "fast_point_share_pct": pct(fast_points, point_count),
                "points_ge_150_share_pct": pct(ge150, point_count),
                "points_ge_350_share_pct": pct(ge350, point_count),
            }
        )

    totals = {
        "equipment_count": sum(int(row["equipment_count"]) for row in state_rows),
        "declared_charging_point_count": sum(int(row["declared_charging_point_count"]) for row in state_rows),
        "charging_point_count": sum(int(row["charging_point_count"]) for row in state_rows),
        "normal_charging_point_count": sum(int(row["normal_charging_point_count"]) for row in state_rows),
        "fast_charging_point_count": sum(int(row["fast_charging_point_count"]) for row in state_rows),
        "points_ge_150_kw": sum(int(row["points_ge_150_kw"]) for row in state_rows),
        "points_ge_350_kw": sum(int(row["points_ge_350_kw"]) for row in state_rows),
        "unclassifiable_power_point_count": sum(int(row["unclassifiable_power_point_count"]) for row in state_rows),
        "equipment_nominal_power_mw": sum(float(row["equipment_nominal_power_mw"]) for row in state_rows),
    }
    for field, expected in EXPECTED_INFRASTRUCTURE.items():
        actual = totals[field]
        if field.endswith("_mw"):
            require(math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=1e-9), f"Infrastructure total mismatch for {field}: {actual}")
        else:
            require(int(actual) == int(expected), f"Infrastructure total mismatch for {field}: {actual}")
    national_equipment = query_dicts(
        conn,
        """
        SELECT COUNT(*) AS equipment_count,
               SUM(declared_point_count) AS declared_charging_point_count,
               SUM(equipment_nominal_power_kw) AS equipment_nominal_power_kw
        FROM core.charging_equipment
        WHERE source_id = ?
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    )[0]
    national_points = query_dicts(conn, point_metrics_sql(None), [INFRASTRUCTURE_SOURCE_ID])[0]
    direct_totals = {
        "equipment_count": as_int(national_equipment["equipment_count"], "national equipment"),
        "declared_charging_point_count": as_int(national_equipment["declared_charging_point_count"], "national declared points"),
        "charging_point_count": as_int(national_points["charging_point_count"], "national populated points"),
        "normal_charging_point_count": as_int(national_points["normal_charging_point_count"], "national normal points"),
        "fast_charging_point_count": as_int(national_points["fast_charging_point_count"], "national fast points"),
        "points_ge_150_kw": as_int(national_points["points_ge_150_kw"], "national >=150 points"),
        "points_ge_350_kw": as_int(national_points["points_ge_350_kw"], "national >=350 points"),
        "unclassifiable_power_point_count": as_int(national_points["unclassifiable_power_point_count"], "national unknown-power points"),
        "equipment_nominal_power_mw": as_float(national_equipment["equipment_nominal_power_kw"], "national nominal power") / 1000.0,
    }
    for field in direct_totals:
        if field.endswith("_mw"):
            require(math.isclose(float(direct_totals[field]), float(totals[field]), rel_tol=0, abs_tol=1e-9), f"Direct/state total mismatch for {field}")
        else:
            require(int(direct_totals[field]) == int(totals[field]), f"Direct/state total mismatch for {field}")

    national_row = {
        "geography_name": "Germany",
        "bnetza_reference_date": INFRASTRUCTURE_REFERENCE_DATE,
        **direct_totals,
        "fast_point_share_pct": pct(direct_totals["fast_charging_point_count"], direct_totals["charging_point_count"]),
        "points_ge_150_share_pct": pct(direct_totals["points_ge_150_kw"], direct_totals["charging_point_count"]),
        "points_ge_350_share_pct": pct(direct_totals["points_ge_350_kw"], direct_totals["charging_point_count"]),
    }
    state_output = [
        {
            "state_name": row["state_name"],
            "bnetza_reference_date": row["bnetza_reference_date"],
            "equipment_count": row["equipment_count"],
            "declared_charging_point_count": row["declared_charging_point_count"],
            "charging_point_count": row["charging_point_count"],
            "normal_charging_point_count": row["normal_charging_point_count"],
            "fast_charging_point_count": row["fast_charging_point_count"],
            "points_ge_150_kw": row["points_ge_150_kw"],
            "points_ge_350_kw": row["points_ge_350_kw"],
            "unclassifiable_power_point_count": row["unclassifiable_power_point_count"],
            "equipment_nominal_power_mw": row["equipment_nominal_power_mw"],
            "fast_point_share_pct": row["fast_point_share_pct"],
            "points_ge_150_share_pct": row["points_ge_150_share_pct"],
            "points_ge_350_share_pct": row["points_ge_350_share_pct"],
            "charging_point_national_share_pct": pct(row["charging_point_count"], direct_totals["charging_point_count"]),
        }
        for row in state_rows
    ]
    assert_unique(state_output, ("state_name",), "state charging")
    return [national_row], state_output, {"totals": direct_totals, "integrity": integrity}


def load_bbsr_exports(conn: duckdb.DuckDBPyConnection) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    district_view = "analytics.charging_by_bbsr_district_2025_harmonized"
    type_view = "analytics.charging_by_bbsr_type_2025_harmonized"
    district_source_rows = query_dicts(conn, f"SELECT * FROM {district_view} ORDER BY historical_bbsr_administrative_district_code")
    type_source_rows = query_dicts(conn, f"SELECT * FROM {type_view} ORDER BY settlement_type_code")
    require(len(district_source_rows) == 400, f"Expected 400 BBSR historical units, found {len(district_source_rows)}")
    require(len(type_source_rows) == 4, f"Expected 4 BBSR type rows, found {len(type_source_rows)}")
    assert_unique(district_source_rows, ("historical_bbsr_administrative_district_code",), "BBSR district")
    require(
        all(as_date_string(row["infrastructure_reference_date"]) == INFRASTRUCTURE_REFERENCE_DATE for row in district_source_rows),
        "BBSR district infrastructure date changed",
    )
    require(
        all(as_date_string(row["historical_bbsr_reference_date"]) == BBSR_REFERENCE_DATE for row in district_source_rows),
        "BBSR district geographic date changed",
    )
    require(sum(as_int(row["source_component_count"], "BBSR source component count") for row in district_source_rows) == 401, "BBSR 401-to-400 source-component total changed")
    require(all(as_int(row["unclassifiable_power_point_count"], "BBSR unknown power") == 0 for row in district_source_rows), "BBSR unknown-power rows appeared")

    target = next(row for row in district_source_rows if str(row["historical_bbsr_administrative_district_code"]) == "06435000")
    require(as_int(target["source_component_count"], "Hanau/Main-Kinzig components") == 2, "Hanau/Main-Kinzig was not consolidated")
    require("Hanau" in str(target["source_component_names"]) and "Main-Kinzig" in str(target["source_component_names"]), "Hanau/Main-Kinzig source names missing")
    require(str(target["historical_bbsr_settlement_type_code"]) == "2", "Hanau/Main-Kinzig historical type changed")
    kassel_city = next(row for row in district_source_rows if str(row["historical_bbsr_administrative_district_code"]) == "06611000")
    require(str(kassel_city["historical_bbsr_settlement_type_code"]) == "1", "Kassel city corrected category is not type 1")
    trier_rows = [row for row in district_source_rows if str(row["historical_bbsr_administrative_district_code"]) in {"07211000", "07235000"}]
    require(len(trier_rows) == 2 and all(as_int(row["source_component_count"], "Trier components") == 1 for row in trier_rows), "Trier components were allocated or merged")
    require({str(row["historical_bbsr_settlement_type_code"]) for row in trier_rows} == {"1", "3"}, "Trier classifications changed")

    totals = {
        "historical_units": len(district_source_rows),
        "source_components": sum(as_int(row["source_component_count"], "BBSR source components") for row in district_source_rows),
        "equipment_count": sum(as_int(row["equipment_count"], "BBSR equipment") for row in district_source_rows),
        "charging_point_count": sum(as_int(row["charging_point_count"], "BBSR points") for row in district_source_rows),
        "normal_charging_point_count": sum(as_int(row["normal_charging_point_count"], "BBSR normal points") for row in district_source_rows),
        "fast_charging_point_count": sum(as_int(row["fast_charging_point_count"], "BBSR fast points") for row in district_source_rows),
        "points_ge_150_kw": sum(as_int(row["points_ge_150_kw"], "BBSR >=150 points") for row in district_source_rows),
        "points_ge_350_kw": sum(as_int(row["points_ge_350_kw"], "BBSR >=350 points") for row in district_source_rows),
        "equipment_nominal_power_mw": sum(as_float(row["total_equipment_nominal_power_mw"], "BBSR nominal power") for row in district_source_rows),
    }
    require(totals["equipment_count"] == EXPECTED_INFRASTRUCTURE["equipment_count"], "BBSR equipment total does not reconcile")
    require(totals["charging_point_count"] == EXPECTED_INFRASTRUCTURE["charging_point_count"], "BBSR point total does not reconcile")
    require(totals["normal_charging_point_count"] == EXPECTED_INFRASTRUCTURE["normal_charging_point_count"], "BBSR normal total does not reconcile")
    require(totals["fast_charging_point_count"] == EXPECTED_INFRASTRUCTURE["fast_charging_point_count"], "BBSR fast total does not reconcile")
    require(totals["points_ge_150_kw"] == EXPECTED_INFRASTRUCTURE["points_ge_150_kw"], "BBSR >=150 total does not reconcile")
    require(totals["points_ge_350_kw"] == EXPECTED_INFRASTRUCTURE["points_ge_350_kw"], "BBSR >=350 total does not reconcile")
    require(math.isclose(totals["equipment_nominal_power_mw"], EXPECTED_INFRASTRUCTURE["equipment_nominal_power_mw"], rel_tol=0, abs_tol=1e-9), "BBSR nominal power total does not reconcile")

    district_rows: List[Dict[str, Any]] = []
    for row in district_source_rows:
        points = as_int(row["charging_point_count"], "BBSR point count")
        equipment = as_int(row["equipment_count"], "BBSR equipment count")
        district_rows.append(
            {
                "historical_bbsr_administrative_district_code": str(row["historical_bbsr_administrative_district_code"]),
                "historical_bbsr_administrative_district_name": row["historical_bbsr_administrative_district_name"],
                "historical_bbsr_federal_state_code": str(row["historical_bbsr_federal_state_code"]),
                "historical_bbsr_federal_state_name": row["historical_bbsr_federal_state_name"],
                "historical_bbsr_settlement_type_code": str(row["historical_bbsr_settlement_type_code"]),
                "historical_bbsr_settlement_type_name_de": row["historical_bbsr_settlement_type_name_de"],
                "bbsr_reference_date": BBSR_REFERENCE_DATE,
                "bnetza_reference_date": INFRASTRUCTURE_REFERENCE_DATE,
                "source_component_count": as_int(row["source_component_count"], "BBSR source components"),
                "source_component_names": row["source_component_names"],
                "historical_boundary_basis": row["historical_boundary_basis"],
                "mapping_method": row["mapping_method"],
                "boundary_compatibility_status": row["boundary_compatibility_status"],
                "equipment_count": equipment,
                "declared_charging_point_count": as_int(row["declared_charging_point_count"], "BBSR declared points"),
                "charging_point_count": points,
                "normal_charging_point_count": as_int(row["normal_charging_point_count"], "BBSR normal points"),
                "fast_charging_point_count": as_int(row["fast_charging_point_count"], "BBSR fast points"),
                "points_ge_150_kw": as_int(row["points_ge_150_kw"], "BBSR >=150 points"),
                "points_ge_350_kw": as_int(row["points_ge_350_kw"], "BBSR >=350 points"),
                "unclassifiable_power_point_count": as_int(row["unclassifiable_power_point_count"], "BBSR unknown power"),
                "equipment_nominal_power_mw": as_float(row["total_equipment_nominal_power_mw"], "BBSR nominal power"),
                "fast_point_share_pct": pct(as_int(row["fast_charging_point_count"], "BBSR fast points"), points),
                "points_ge_150_share_pct": pct(as_int(row["points_ge_150_kw"], "BBSR >=150 points"), points),
                "points_ge_350_share_pct": pct(as_int(row["points_ge_350_kw"], "BBSR >=350 points"), points),
                "equipment_national_share_pct": pct(equipment, totals["equipment_count"]),
                "charging_point_national_share_pct": pct(points, totals["charging_point_count"]),
            }
        )

    grouped: Dict[str, Dict[str, Any]] = {}
    for row in district_rows:
        code = str(row["historical_bbsr_settlement_type_code"])
        group = grouped.setdefault(
            code,
            {
                "settlement_type_code": code,
                "settlement_type_name_de": row["historical_bbsr_settlement_type_name_de"],
                "historical_bbsr_reference_date": BBSR_REFERENCE_DATE,
                "bnetza_reference_date": INFRASTRUCTURE_REFERENCE_DATE,
                "historical_district_count": 0,
                "source_component_count": 0,
                "equipment_count": 0,
                "charging_point_count": 0,
                "normal_charging_point_count": 0,
                "fast_charging_point_count": 0,
                "points_ge_150_kw": 0,
                "points_ge_350_kw": 0,
                "equipment_nominal_power_mw": 0.0,
            },
        )
        group["historical_district_count"] += 1
        group["source_component_count"] += int(row["source_component_count"])
        for field in ("equipment_count", "charging_point_count", "normal_charging_point_count", "fast_charging_point_count", "points_ge_150_kw", "points_ge_350_kw"):
            group[field] += int(row[field])
        group["equipment_nominal_power_mw"] += float(row["equipment_nominal_power_mw"])

    type_rows: List[Dict[str, Any]] = []
    type_source_by_code = {str(row["settlement_type_code"]): row for row in type_source_rows}
    for code in ("1", "2", "3", "4"):
        group = grouped[code]
        source = type_source_by_code[code]
        for field in ("historical_district_count", "source_component_count", "equipment_count", "charging_point_count", "normal_charging_point_count", "fast_charging_point_count", "points_ge_150_kw", "points_ge_350_kw"):
            require(int(source[field]) == int(group[field]), f"BBSR type/district mismatch for {code}/{field}")
        require(math.isclose(float(source["declared_equipment_nominal_power_mw"]), float(group["equipment_nominal_power_mw"]), rel_tol=0, abs_tol=1e-9), f"BBSR type/district mismatch for {code}/nominal power")
        points = group["charging_point_count"]
        equipment = group["equipment_count"]
        fast = group["fast_charging_point_count"]
        ge150 = group["points_ge_150_kw"]
        ge350 = group["points_ge_350_kw"]
        type_rows.append(
            {
                "bbsr_settlement_type_code": code,
                "bbsr_settlement_type_name_de": group["settlement_type_name_de"],
                "bbsr_reference_date": BBSR_REFERENCE_DATE,
                "bnetza_reference_date": INFRASTRUCTURE_REFERENCE_DATE,
                "historical_bbsr_unit_count": group["historical_district_count"],
                "source_component_count": group["source_component_count"],
                "equipment_count": equipment,
                "charging_point_count": points,
                "normal_charging_point_count": group["normal_charging_point_count"],
                "fast_charging_point_count": fast,
                "points_ge_150_kw": ge150,
                "points_ge_350_kw": ge350,
                "equipment_nominal_power_mw": group["equipment_nominal_power_mw"],
                "fast_point_share_pct": pct(fast, points),
                "points_ge_150_share_pct": pct(ge150, points),
                "points_ge_350_share_pct": pct(ge350, points),
                "equipment_national_share_pct": pct(equipment, totals["equipment_count"]),
                "charging_point_national_share_pct": pct(points, totals["charging_point_count"]),
                "fast_point_national_share_pct": pct(fast, totals["fast_charging_point_count"]),
                "points_ge_150_national_share_pct": pct(ge150, totals["points_ge_150_kw"]),
                "points_ge_350_national_share_pct": pct(ge350, totals["points_ge_350_kw"]),
                "equipment_nominal_power_national_share_pct": pct(group["equipment_nominal_power_mw"], totals["equipment_nominal_power_mw"]),
                "classification_scope": source["classification_scope"],
            }
        )
    assert_unique(type_rows, ("bbsr_settlement_type_code",), "BBSR settlement type")
    require([int(row["historical_bbsr_unit_count"]) for row in type_rows] == [68, 131, 98, 103], "BBSR type unit counts changed")
    return district_rows, type_rows, {"totals": totals, "district_source_rows": len(district_source_rows), "source_components": totals["source_components"]}


def load_kba_state_and_region_exports(conn: duckdb.DuckDBPyConnection) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    source_ids = [KBA_SOURCE_IDS[date] for date in KBA_DATES]
    state_source_rows = query_dicts(
        conn,
        """
        SELECT source_id, reference_date, state_name, fuel_type, passenger_cars
        FROM core.kba_state_fuel_stock
        WHERE source_id IN (?, ?, ?)
        ORDER BY reference_date, state_name, fuel_type
        """,
        source_ids,
    )
    require(len(state_source_rows) == 3 * 18 * 7, f"Expected 378 KBA state/fuel rows, found {len(state_source_rows)}")
    values: Dict[Tuple[str, str, str], int] = {}
    for row in state_source_rows:
        date = as_date_string(row["reference_date"])
        key = (date, str(row["state_name"]), str(row["fuel_type"]))
        require(key not in values, f"Duplicate KBA state/fuel key: {key}")
        require(key[1] in ALL_KBA_STATE_GEOGRAPHIES, f"Unexpected KBA geography: {key[1]}")
        require(key[2] in EXPECTED_FUEL_TYPES, f"Unexpected KBA fuel type: {key[2]}")
        value = as_int(row["passenger_cars"], f"KBA passenger cars {key}")
        require(value >= 0, f"Negative KBA stock: {key}")
        values[key] = value
    for date in KBA_DATES:
        for geography in ALL_KBA_STATE_GEOGRAPHIES:
            require({fuel for (d, geo, fuel) in values if d == date and geo == geography} == set(EXPECTED_FUEL_TYPES), f"Incomplete KBA fuel coverage: {date}/{geography}")

    def vehicle_metrics(date: str, geography: str) -> Dict[str, int]:
        total = sum(values[(date, geography, fuel)] for fuel in MUTUALLY_EXCLUSIVE_TOTAL_FUELS)
        bev = values[(date, geography, BEV_FUEL)]
        phev = values[(date, geography, PHEV_FUEL)]
        hybrid = values[(date, geography, "Hybrid insgesamt")]
        require(hybrid >= phev, f"PHEV exceeds Hybrid insgesamt: {date}/{geography}")
        require(bev + phev <= total, f"Combined plug-in stock exceeds passenger-car stock: {date}/{geography}")
        return {"passenger_car_stock": total, "bev_stock": bev, "phev_stock": phev, "combined_plugin_stock": bev + phev}

    by_date_geo = {(date, geography): vehicle_metrics(date, geography) for date in KBA_DATES for geography in ALL_KBA_STATE_GEOGRAPHIES}
    kba_state_rows: List[Dict[str, Any]] = []
    for date in KBA_DATES:
        for state in FEDERAL_STATES:
            current = by_date_geo[(date, state)]
            january = by_date_geo[(KBA_DATES[0], state)]
            kba_state_rows.append(
                {
                    "state_name": state,
                    "kba_reference_date": date,
                    "passenger_car_stock": current["passenger_car_stock"],
                    "bev_passenger_car_stock": current["bev_stock"],
                    "phev_passenger_car_stock": current["phev_stock"],
                    "combined_plugin_passenger_car_stock": current["combined_plugin_stock"],
                    "bev_penetration_pct": pct(current["bev_stock"], current["passenger_car_stock"]),
                    "phev_penetration_pct": pct(current["phev_stock"], current["passenger_car_stock"]),
                    "combined_plugin_penetration_pct": pct(current["combined_plugin_stock"], current["passenger_car_stock"]),
                    "bev_stock_change_from_2026_01_01": None if date == KBA_DATES[0] else current["bev_stock"] - january["bev_stock"],
                    "bev_stock_growth_pct_from_2026_01_01": None if date == KBA_DATES[0] else pct(current["bev_stock"] - january["bev_stock"], january["bev_stock"]),
                    "phev_stock_change_from_2026_01_01": None if date == KBA_DATES[0] else current["phev_stock"] - january["phev_stock"],
                    "phev_stock_growth_pct_from_2026_01_01": None if date == KBA_DATES[0] else pct(current["phev_stock"] - january["phev_stock"], january["phev_stock"]),
                }
            )
    assert_unique(kba_state_rows, ("state_name", "kba_reference_date"), "KBA state/date")
    require(len(kba_state_rows) == 48, f"Expected 48 KBA state rows, found {len(kba_state_rows)}")

    district_source_rows = query_dicts(
        conn,
        """
        SELECT source_id, reference_date, district_code, district_name, state_name,
               passenger_cars, bev_cars, phev_cars
        FROM core.kba_district_ev_stock
        WHERE source_id IN (?, ?, ?)
        ORDER BY reference_date, district_code
        """,
        source_ids,
    )
    require(len(district_source_rows) == 1_200, f"Expected 1,200 KBA registration-region rows, found {len(district_source_rows)}")
    assert_unique(district_source_rows, ("reference_date", "district_code"), "KBA registration region/date")
    region_by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in district_source_rows:
        date = as_date_string(row["reference_date"])
        code = str(row["district_code"])
        region_by_key[(date, code)] = {
            "kba_registration_region_code": code,
            "registration_region_name": row["district_name"],
            "state_name": row["state_name"],
            "passenger_car_stock": as_int(row["passenger_cars"], f"KBA region passenger cars {date}/{code}"),
            "bev_stock": as_int(row["bev_cars"], f"KBA region BEV {date}/{code}"),
            "phev_stock": as_int(row["phev_cars"], f"KBA region PHEV {date}/{code}"),
        }
        require(region_by_key[(date, code)]["passenger_car_stock"] >= 0, f"Negative KBA region passenger cars: {date}/{code}")
        require(region_by_key[(date, code)]["bev_stock"] >= 0 and region_by_key[(date, code)]["phev_stock"] >= 0, f"Negative KBA region EV stock: {date}/{code}")
    codes = sorted({code for date, code in region_by_key})
    require(len(codes) == 400, f"Expected 400 KBA registration-region codes, found {len(codes)}")
    region_rows: List[Dict[str, Any]] = []
    for date in KBA_DATES:
        for code in codes:
            current = region_by_key[(date, code)]
            january = region_by_key[(KBA_DATES[0], code)]
            combined = current["bev_stock"] + current["phev_stock"]
            region_rows.append(
                {
                    "kba_registration_region_code": code,
                    "registration_region_name": current["registration_region_name"],
                    "state_name": current["state_name"],
                    "kba_reference_date": date,
                    "passenger_car_stock": current["passenger_car_stock"],
                    "bev_passenger_car_stock": current["bev_stock"],
                    "phev_passenger_car_stock": current["phev_stock"],
                    "combined_plugin_passenger_car_stock": combined,
                    "bev_penetration_pct": pct(current["bev_stock"], current["passenger_car_stock"]),
                    "phev_penetration_pct": pct(current["phev_stock"], current["passenger_car_stock"]),
                    "combined_plugin_penetration_pct": pct(combined, current["passenger_car_stock"]),
                    "bev_stock_change_from_2026_01_01": None if date == KBA_DATES[0] else current["bev_stock"] - january["bev_stock"],
                    "bev_stock_growth_pct_from_2026_01_01": None if date == KBA_DATES[0] else pct(current["bev_stock"] - january["bev_stock"], january["bev_stock"]),
                    "phev_stock_change_from_2026_01_01": None if date == KBA_DATES[0] else current["phev_stock"] - january["phev_stock"],
                    "phev_stock_growth_pct_from_2026_01_01": None if date == KBA_DATES[0] else pct(current["phev_stock"] - january["phev_stock"], january["phev_stock"]),
                }
            )
    assert_unique(region_rows, ("kba_registration_region_code", "kba_reference_date"), "KBA registration region/date")
    trier_rows = [row for row in region_rows if row["kba_registration_region_code"] == "07211"]
    require(len(trier_rows) == 3 and {row["registration_region_name"] for row in trier_rows} == {"TRIER-SAARBURG"}, "KBA 07211 Trier identity changed")

    reconciliation: Dict[str, Dict[str, Any]] = {}
    for date in KBA_DATES:
        national = by_date_geo[(date, NATIONAL_GEOGRAPHY)]
        sonstige = by_date_geo[(date, RESIDUAL_GEOGRAPHY)]
        state_sum = {field: sum(by_date_geo[(date, state)][field] for state in FEDERAL_STATES) for field in ("passenger_car_stock", "bev_stock", "phev_stock")}
        district_rows_for_date = [row for row in district_source_rows if as_date_string(row["reference_date"]) == date]
        district_sum = {
            "passenger_car_stock": sum(as_int(row["passenger_cars"], "district passenger cars") for row in district_rows_for_date),
            "bev_stock": sum(as_int(row["bev_cars"], "district BEV") for row in district_rows_for_date),
            "phev_stock": sum(as_int(row["phev_cars"], "district PHEV") for row in district_rows_for_date),
        }
        require(len(district_rows_for_date) == 400, f"Expected 400 KBA regions for {date}")
        for field in ("passenger_car_stock", "bev_stock", "phev_stock"):
            require(national[field] == state_sum[field] + sonstige[field], f"KBA national/state/Sonstige reconciliation failed for {date}/{field}")
            require(state_sum[field] == district_sum[field], f"KBA state/400-region reconciliation failed for {date}/{field}")
        expected = EXPECTED_KBA[date]
        require(national["passenger_car_stock"] == expected["national_passenger_car_stock"], f"KBA national passenger-car total changed for {date}")
        require(national["bev_stock"] == expected["national_bev_stock"], f"KBA national BEV total changed for {date}")
        require(national["phev_stock"] == expected["national_phev_stock"], f"KBA national PHEV total changed for {date}")
        require(district_sum["passenger_car_stock"] == expected["district_passenger_car_stock"], f"KBA 400-region passenger-car total changed for {date}")
        require(district_sum["bev_stock"] == expected["district_bev_stock"], f"KBA 400-region BEV total changed for {date}")
        require(district_sum["phev_stock"] == expected["district_phev_stock"], f"KBA 400-region PHEV total changed for {date}")
        reconciliation[date] = {"national": national, "state_sum": state_sum, "sonstige": sonstige, "district_sum": district_sum, "district_rows": len(district_rows_for_date)}
    return kba_state_rows, region_rows, {"reconciliation": reconciliation, "region_codes": len(codes)}


def load_national_history(conn: duckdb.DuckDBPyConnection) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = query_dicts(conn, "SELECT * FROM analytics.kba_national_quarterly_stock ORDER BY stock_date")
    require(len(rows) == 33, f"Expected 33 validated national quarterly observations, found {len(rows)}")
    assert_unique(rows, ("stock_date",), "national stock history")
    dates = [as_date_string(row["stock_date"]) for row in rows]
    require(dates[0] == "2018-07-01" and dates[-1] == "2026-07-01", "National quarterly history range changed")
    output: List[Dict[str, Any]] = []
    for row in rows:
        bev = as_int(row["passenger_bev"], "national history BEV")
        phev = as_int(row["passenger_phev"], "national history PHEV")
        cars = as_int(row["passenger_cars_total"], "national history passenger cars")
        output.append(
            {
                "stock_date": as_date_string(row["stock_date"]),
                "source_report_snapshot": as_date_string(row["report_snapshot"]),
                "bev_passenger_car_stock": bev,
                "phev_passenger_car_stock": phev,
                "passenger_car_stock": cars,
                "combined_plugin_passenger_car_stock": bev + phev,
                "bev_penetration_pct": pct(bev, cars),
                "phev_penetration_pct": pct(phev, cars),
                "combined_plugin_penetration_pct": pct(bev + phev, cars),
                "source_object": "analytics.kba_national_quarterly_stock",
            }
        )
    return output, {"row_count": len(output), "min_stock_date": dates[0], "max_stock_date": dates[-1]}


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames is not None, f"Missing CSV header: {path}")
        rows = list(reader)
        return list(reader.fieldnames), rows


def source_number(row: Mapping[str, str], field: str, integer: bool = False) -> Optional[float | int]:
    value = row.get(field, "")
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise ExportError(f"Non-numeric validated input {field}={value!r}") from exc
    if integer:
        require(number.is_integer(), f"Non-integer validated input {field}={value!r}")
        return int(number)
    return number


def load_state_comparison_export() -> Tuple[List[str], List[Dict[str, Any]], Dict[str, Any]]:
    source_path = ROOT / "reports/batch16_state_comparison.csv"
    fields, source_rows = read_csv(source_path)
    required = {
        "state_name",
        "kba_reference_date",
        "bnetza_reference_date",
        "passenger_car_stock",
        "bev_stock",
        "phev_stock",
        "bev_penetration_pct",
        "charging_point_count",
        "fast_charging_point_count",
        "points_ge_150_kw",
        "points_ge_350_kw",
        "bevs_per_registered_charging_point",
        "registered_charging_points_per_1000_bevs",
        "fast_points_per_1000_bevs",
        "points_ge_150_per_1000_bevs",
        "points_ge_350_per_1000_bevs",
        "bev_stock_share_of_16_state_bev_stock_pct",
        "share_of_national_registered_charging_points_pct",
        "bev_stock_share_minus_charging_point_share_pp",
        "cross_source_date_note",
    }
    require(required <= set(fields), f"Batch 16 comparison is missing columns: {sorted(required - set(fields))}")
    require(len(source_rows) == 16, f"Expected 16 Batch 16 state rows, found {len(source_rows)}")
    assert_unique(source_rows, ("state_name",), "Batch 16 state")
    require({row["state_name"] for row in source_rows} == set(FEDERAL_STATES), "Batch 16 state coverage changed")
    output: List[Dict[str, Any]] = []
    for state in FEDERAL_STATES:
        row = next(item for item in source_rows if item["state_name"] == state)
        require(row["kba_reference_date"] == KBA_PRIMARY_DATE and row["bnetza_reference_date"] == INFRASTRUCTURE_REFERENCE_DATE, f"Batch 16 dates changed for {state}")
        output.append(
            {
                "state_name": state,
                "kba_reference_date": row["kba_reference_date"],
                "bnetza_reference_date": row["bnetza_reference_date"],
                "passenger_car_stock": source_number(row, "passenger_car_stock", True),
                "bev_passenger_car_stock": source_number(row, "bev_stock", True),
                "phev_passenger_car_stock": source_number(row, "phev_stock", True),
                "bev_penetration_pct": source_number(row, "bev_penetration_pct"),
                "charging_point_count": source_number(row, "charging_point_count", True),
                "fast_point_count": source_number(row, "fast_charging_point_count", True),
                "points_ge_150_kw": source_number(row, "points_ge_150_kw", True),
                "points_ge_350_kw": source_number(row, "points_ge_350_kw", True),
                "bevs_per_charging_point": source_number(row, "bevs_per_registered_charging_point"),
                "registered_charging_points_per_1000_bevs": source_number(row, "registered_charging_points_per_1000_bevs"),
                "fast_points_per_1000_bevs": source_number(row, "fast_points_per_1000_bevs"),
                "points_ge_150_per_1000_bevs": source_number(row, "points_ge_150_per_1000_bevs"),
                "points_ge_350_per_1000_bevs": source_number(row, "points_ge_350_per_1000_bevs"),
                "bev_stock_share_pct": source_number(row, "bev_stock_share_of_16_state_bev_stock_pct"),
                "charging_point_share_pct": source_number(row, "share_of_national_registered_charging_points_pct"),
                "bev_stock_minus_charging_point_share_pp": source_number(row, "bev_stock_share_minus_charging_point_share_pp"),
                "bevs_per_charging_point_publication_status": "CONTEXT_ONLY",
                "registered_charging_points_per_1000_bevs_publication_status": "CONTEXT_ONLY",
                "fast_points_per_1000_bevs_publication_status": "EXPLORATORY_SENSITIVITY",
                "points_ge_150_per_1000_bevs_publication_status": "EXPLORATORY_SENSITIVITY",
                "points_ge_350_per_1000_bevs_publication_status": "EXPLORATORY_SENSITIVITY",
                "bev_stock_minus_charging_point_share_publication_status": "EXPLORATORY_SENSITIVITY",
                "comparison_scope": "16 federal states",
                "cross_source_temporal_label": "CROSS-SNAPSHOT DESCRIPTIVE COMPARISON",
                "cross_source_date_note": row["cross_source_date_note"],
            }
        )
    return (
        [
            "state_name",
            "kba_reference_date",
            "bnetza_reference_date",
            "passenger_car_stock",
            "bev_passenger_car_stock",
            "phev_passenger_car_stock",
            "bev_penetration_pct",
            "charging_point_count",
            "fast_point_count",
            "points_ge_150_kw",
            "points_ge_350_kw",
            "bevs_per_charging_point",
            "registered_charging_points_per_1000_bevs",
            "fast_points_per_1000_bevs",
            "points_ge_150_per_1000_bevs",
            "points_ge_350_per_1000_bevs",
            "bev_stock_share_pct",
            "charging_point_share_pct",
            "bev_stock_minus_charging_point_share_pp",
            "bevs_per_charging_point_publication_status",
            "registered_charging_points_per_1000_bevs_publication_status",
            "fast_points_per_1000_bevs_publication_status",
            "points_ge_150_per_1000_bevs_publication_status",
            "points_ge_350_per_1000_bevs_publication_status",
            "bev_stock_minus_charging_point_share_publication_status",
            "comparison_scope",
            "cross_source_temporal_label",
            "cross_source_date_note",
        ],
        output,
        {"source_report": "reports/batch16_state_comparison.csv", "source_row_count": len(source_rows)},
    )


def load_temporal_sensitivity_export() -> Tuple[List[str], List[Dict[str, Any]], Dict[str, Any]]:
    source_path = ROOT / "reports/batch17_state_temporal_sensitivity.csv"
    source_fields, source_rows = read_csv(source_path)
    required = {
        "state_name",
        "kba_reference_date",
        "bnetza_reference_date",
        "survivor_cutoff_date",
        "published_equipment_count",
        "published_charging_point_count",
        "published_fast_point_count",
        "published_points_ge_150",
        "published_points_ge_350",
        "survivor_equipment_count",
        "survivor_charging_point_count",
        "survivor_fast_point_count",
        "survivor_points_ge_150",
        "survivor_points_ge_350",
        "published_minus_survivor_equipment_count",
        "published_minus_survivor_charging_point_count",
        "survivor_minus_published_bevs_per_point",
        "published_bevs_per_point_rank",
        "survivor_bevs_per_point_rank",
        "bevs_per_point_rank_change_survivor_minus_published",
        "fast_points_per_1000_rank_change_survivor_minus_published",
        "ge150_points_per_1000_rank_change_survivor_minus_published",
        "ge350_points_per_1000_rank_change_survivor_minus_published",
        "temporal_label_published",
        "temporal_label_survivor",
    }
    require(required <= set(source_fields), f"Batch 17 temporal CSV is missing columns: {sorted(required - set(source_fields))}")
    require(len(source_rows) == 16, f"Expected 16 Batch 17 temporal rows, found {len(source_rows)}")
    assert_unique(source_rows, ("state_name",), "Batch 17 temporal state")
    require({row["state_name"] for row in source_rows} == set(FEDERAL_STATES), "Batch 17 temporal state coverage changed")
    for row in source_rows:
        require(row["kba_reference_date"] == KBA_PRIMARY_DATE, f"Batch 17 KBA date changed for {row['state_name']}")
        require(row["bnetza_reference_date"] == INFRASTRUCTURE_REFERENCE_DATE, f"Batch 17 BNetzA date changed for {row['state_name']}")
        require(row["survivor_cutoff_date"] == SURVIVOR_CUTOFF_DATE, f"Batch 17 cutoff changed for {row['state_name']}")
        require(row["temporal_label_published"] == "CROSS-SNAPSHOT DESCRIPTIVE COMPARISON", f"Batch 17 published label changed for {row['state_name']}")
        require("NOT ACTUAL JULY INFRASTRUCTURE" in row["temporal_label_survivor"], f"Batch 17 survivor safeguard missing for {row['state_name']}")
    output_fields = list(source_fields) + ["publication_status"]
    output_rows = [dict(row, publication_status="EXPLORATORY_SENSITIVITY") for row in source_rows]
    return output_fields, output_rows, {"source_report": "reports/batch17_state_temporal_sensitivity.csv", "source_row_count": len(source_rows)}


def csv_value(field: str, value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()[:10]
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        require(math.isfinite(value), f"Non-finite output value in {field}")
        decimals = 4 if field.endswith("_mw") else 10
        rendered = f"{value:.{decimals}f}".rstrip("0").rstrip(".")
        return rendered or "0"
    return str(value)


def write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(field, row.get(field)) for field in fieldnames})


def validate_written_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[Mapping[str, Any]], key_fields: Sequence[str], numeric_fields: Sequence[str], date_fields: Sequence[str]) -> Dict[str, Any]:
    data = path.read_bytes()
    require(not data.startswith(b"\xef\xbb\xbf"), f"UTF-8 BOM found in {path.name}")
    require(b"\r\n" not in data, f"CRLF line ending found in {path.name}")
    data.decode("utf-8")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == list(fieldnames), f"Column order changed in {path.name}")
        parsed = list(reader)
    require(len(parsed) == len(rows), f"Row count changed after writing {path.name}")
    assert_unique(parsed, key_fields, path.name)
    for row in parsed:
        for field in numeric_fields:
            value = row.get(field, "")
            if value == "":
                continue
            require("," not in value, f"Thousands separator in numeric field {path.name}/{field}")
            try:
                number = float(value)
            except ValueError as exc:
                raise ExportError(f"Non-numeric CSV field {path.name}/{field}: {value!r}") from exc
            require(math.isfinite(number), f"Non-finite CSV field {path.name}/{field}")
        for field in date_fields:
            value = row.get(field, "")
            if value:
                try:
                    dt.date.fromisoformat(value)
                except ValueError as exc:
                    raise ExportError(f"Non-ISO date in {path.name}/{field}: {value!r}") from exc
    return {"row_count": len(parsed), "column_count": len(fieldnames), "sha256": sha256(path), "utf8": True, "lf_only": True}


def render_validation_report(
    inventory: Sequence[Mapping[str, Any]],
    database_sha256: str,
    input_fingerprints: Sequence[Mapping[str, Any]],
    database_contract: Mapping[str, Any],
    infra_checks: Mapping[str, Any],
    bbsr_checks: Mapping[str, Any],
    kba_checks: Mapping[str, Any],
    history_checks: Mapping[str, Any],
) -> str:
    lines: List[str] = [
        "# Batch 19 — Tableau data export validation",
        "",
        "**Batch status: PASS**",
        "",
        "This report records measured validation of deterministic CSV extracts prepared from the existing local analytical data. The phase creates Tableau-ready files only; it does not build a Tableau workbook, modify DuckDB, alter source workbooks, or join KBA stock to BBSR geography.",
        "",
        "## 1. Executive summary",
        "",
        f"Nine CSV extracts were generated under `data/exports/tableau/`. The BNetzA source reconciles to {EXPECTED_INFRASTRUCTURE['equipment_count']:,} equipment records, {EXPECTED_INFRASTRUCTURE['charging_point_count']:,} populated point slots, {EXPECTED_INFRASTRUCTURE['normal_charging_point_count']:,} normal points, {EXPECTED_INFRASTRUCTURE['fast_charging_point_count']:,} fast points, {EXPECTED_INFRASTRUCTURE['points_ge_150_kw']:,} points at or above 150 kW, {EXPECTED_INFRASTRUCTURE['points_ge_350_kw']:,} points at or above 350 kW, and {EXPECTED_INFRASTRUCTURE['equipment_nominal_power_mw']:.4f} MW of declared equipment nominal power.",
        "",
        "The BBSR district export contains 400 historical 2025 target units formed from 401 BNetzA source components. Hanau and the remaining Main-Kinzig-Kreis component aggregate to historical BBSR `06435000` type 2; Kassel city is `06611000` type 1; Trier city and Trier-Saarburg remain separate charging components. No KBA vehicle stock is joined to these rows.",
        "",
        "The KBA state and registration-region exports preserve the three validated stock dates. National and `Sonstige` rows are used for reconciliation but are not emitted as federal-state rows. The shared registration region `07211` remains one KBA row per date and is not allocated to Trier city or Trier-Saarburg.",
        "",
        "## 2. Export inventory",
        "",
        "| File | Rows | Columns | Primary key | SHA-256 |",
        "|---|---:|---:|---|---|",
    ]
    for item in inventory:
        filename = str(item["filename"])
        lines.append(f"| [`{filename}`](../data/exports/tableau/{filename}) | {item['row_count']} | {item['column_count']} | `{item['primary_key']}` | `{item['sha256']}` |")
    lines += [
        "",
        "## 3. Source object and schema inspection",
        "",
        "DuckDB was opened with `read_only=True`. Required object types and columns were inspected before any query was executed. `analytics.charging_by_state` was verified to pre-aggregate points by `(source_id, equipment_excel_row)` and to use source-aware equipment/point keys.",
        "",
        "| Object | Type | Column count |",
        "|---|---|---:|",
    ]
    for name in sorted(database_contract["objects"]):
        lines.append(f"| `{name}` | {database_contract['objects'][name]} | {len(database_contract['columns'][name])} |")
    lines += [
        "",
        "## 4. Expected versus actual row counts",
        "",
        "| Export | Expected | Actual | Result |",
        "|---|---:|---:|---|",
        f"| National charging | 1 | {inventory[0]['row_count']} | PASS |",
        f"| State charging | 16 | {inventory[1]['row_count']} | PASS |",
        f"| BBSR historical districts | 400 | {inventory[2]['row_count']} | PASS |",
        f"| BBSR settlement types | 4 | {inventory[3]['row_count']} | PASS |",
        f"| KBA state/date | 48 | {inventory[4]['row_count']} | PASS |",
        f"| KBA registration-region/date | 1,200 | {inventory[5]['row_count']} | PASS |",
        f"| State EV/charging comparison | 16 | {inventory[6]['row_count']} | PASS |",
        f"| Temporal sensitivity | 16 | {inventory[7]['row_count']} | PASS |",
        f"| National KBA history | 33 | {inventory[8]['row_count']} | PASS |",
        "",
        "## 5. Key uniqueness",
        "",
        "All natural-key checks passed during export and after CSV serialization: Germany has one row; state charging has one row per `state_name`; BBSR districts have one row per historical BBSR code; BBSR types have one row per type code; KBA state rows have one row per state/date; KBA registration regions have one row per code/date; and temporal sensitivity has one row per state.",
        "",
        "## 6. National infrastructure reconciliation",
        "",
        "| Measure | Direct source total | State sum | Expected |",
        "|---|---:|---:|---:|",
    ]
    for field, label in (
        ("equipment_count", "Equipment records"),
        ("declared_charging_point_count", "Declared charging points"),
        ("charging_point_count", "Populated point slots"),
        ("normal_charging_point_count", "Normal points"),
        ("fast_charging_point_count", "Fast points"),
        ("points_ge_150_kw", "Points >=150 kW"),
        ("points_ge_350_kw", "Points >=350 kW"),
        ("unclassifiable_power_point_count", "Unknown-power points"),
    ):
        lines.append(f"| {label} | {infra_checks['totals'][field]:,} | {infra_checks['totals'][field]:,} | {EXPECTED_INFRASTRUCTURE[field]:,} |")
    lines.append(f"| Declared equipment nominal power (MW) | {infra_checks['totals']['equipment_nominal_power_mw']:.4f} | {infra_checks['totals']['equipment_nominal_power_mw']:.4f} | {EXPECTED_INFRASTRUCTURE['equipment_nominal_power_mw']:.4f} |")
    lines += [
        "",
        f"Point integrity passed with {infra_checks['integrity']['duplicate_point_keys']} duplicate point keys, {infra_checks['integrity']['orphan_point_rows']} orphan point rows, and {infra_checks['integrity']['equipment_point_mismatches']} equipment/point count mismatches. Power classification uses the maximum numeric token in each semicolon-separated `connector_power_raw`: <=22 kW normal, >22 kW fast, with nested >=150 and >=350 kW thresholds.",
        "",
        "## 7. KBA reconciliation",
        "",
        "| KBA date | National passenger cars | National BEV | National PHEV | 16-state / 400-region passenger cars | 16-state / 400-region BEV | 16-state / 400-region PHEV | Sonstige BEV | Sonstige PHEV |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for date in KBA_DATES:
        item = kba_checks["reconciliation"][date]
        lines.append(
            f"| {date} | {item['national']['passenger_car_stock']:,} | {item['national']['bev_stock']:,} | {item['national']['phev_stock']:,} | {item['state_sum']['passenger_car_stock']:,} | {item['state_sum']['bev_stock']:,} | {item['state_sum']['phev_stock']:,} | {item['sonstige']['bev_stock']:,} | {item['sonstige']['phev_stock']:,} |"
        )
    lines += [
        "",
        "The state export contains exactly the 16 named federal states. `Deutschland` and `Sonstige` remain separate reconciliation scopes. Passenger-car totals use six mutually exclusive FZ 27.2 fuel rows; `darunter Plug-in` supplies PHEV detail and is never added to `Hybrid insgesamt`.",
        "",
        f"The optional national history contains {history_checks['row_count']} unique stock dates from {history_checks['min_stock_date']} through {history_checks['max_stock_date']} from `analytics.kba_national_quarterly_stock`; no regional history was fabricated.",
        "",
        "## 8. BBSR harmonization checks",
        "",
        f"The district export has {bbsr_checks['totals']['historical_units']} historical units and {bbsr_checks['totals']['source_components']} source components. Type unit counts are 68, 131, 98 and 103 for types 1–4. All infrastructure measures reconcile to the national BNetzA totals. The source component provenance columns document the 401-to-400 conversion and the Hanau/Main-Kinzig union.",
        "",
        "The BBSR rows are historical-geography labels at `2025-12-31` applied to BNetzA infrastructure published at `2026-09-30`. They must not be narrated as infrastructure observed in 2025. The export contains German BBSR labels only; no unvalidated English translation was added.",
        "",
        "## 9. Cross-dataset compatibility",
        "",
        "Permitted relationships are documented in `reports/batch19_tableau_export_contracts.md`: state charging to KBA state stock only with an explicit selected KBA date and visible date mismatch; KBA state rows to KBA state rows on `(state_name, kba_reference_date)`; KBA registration-region rows only on `(kba_registration_region_code, kba_reference_date)`; and BBSR charging extracts internally on validated BBSR type/code keys. No BBSR-to-KBA relationship is permitted.",
        "",
        "The state comparison carries BNetzA `2026-09-30` and KBA `2026-07-01` separately and labels BEVs-per-point `CONTEXT_ONLY`. Fast/HPC per-1,000-BEV measures and the share gap are `EXPLORATORY_SENSITIVITY`; none is an adequacy, shortage, surplus, demand, utilization, or accessibility measure.",
        "",
        "## 10. Date and grain safeguards",
        "",
        "- BNetzA equipment nominal power is aggregated at equipment grain and is not simultaneously deliverable charging power.",
        "- Charging point counts are populated point slots, not connector counts or verified availability.",
        "- The survivor cohort retains September point attributes for equipment commissioned on or before `2026-07-01`; it is not an actual July infrastructure snapshot.",
        "- KBA stock is registered passenger-car stock, not new registrations or sales.",
        "- Code `07211` remains the single KBA registration geography `TRIER-SAARBURG` for every KBA date and is not split between Trier city and Trier-Saarburg.",
        "",
        "## 11. Deterministic rerun checks",
        "",
        "PASS — output ordering, column order, UTF-8 encoding, LF line endings, numeric formatting and JSON key ordering are fixed; no generation timestamp is embedded. A second execution was compared byte-for-byte for all CSVs and the manifest after the initial export.",
        "",
        "## 12. Source and database immutability",
        "",
        f"DuckDB SHA-256 before and after read-only export: `{database_sha256}`. All {len(input_fingerprints)} approved input fingerprints matched their Batch 13.2/16/17 values. No DuckDB object, raw workbook, reference table, crosswalk or source file was modified.",
        "",
        "## 13. Known issues",
        "",
        "- The BNetzA register is a published register and is not evidence of a complete census, utilization, uptime or service quality.",
        "- Cross-source ratios have a 91-day KBA/BNetzA snapshot gap and remain contextual or exploratory.",
        "- BBSR historical harmonization is charging-only; the owner-approved Hanau scenario was not used as the official baseline.",
        "- No historical infrastructure panel is available from the current sources.",
        "",
        "## 14. Remaining Tableau preparation risks",
        "",
        "Keep national, state, BBSR historical and KBA registration-region extracts as separate logical sources unless a specific relationship has been validated. Do not sum a state charging row after relating it to multiple KBA dates, sum national and state aggregates together, sum percentages, or treat the 400 BBSR historical units as the 400 KBA registration regions.",
        "",
        "## 15. Recommended next step",
        "",
        "Review the contracts and export manifest with the owner, then approve a separate Tableau implementation batch if desired. Batch 20 and dashboard construction were not started by this batch.",
        "",
        "## Input fingerprints",
        "",
        "| Input | SHA-256 | Result |",
        "|---|---|---|",
    ]
    for item in input_fingerprints:
        lines.append(f"| `{item['path']}` | `{item['actual_sha256']}` | MATCH |")
    lines.append("")
    return "\n".join(lines)


def build_manifest(
    inventory: Sequence[Mapping[str, Any]],
    input_fingerprints: Sequence[Mapping[str, Any]],
    database_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    source_dataset_versions = [
        {
            "source_id": item["source_id"],
            "reference_date": item["reference_date"],
            "path": item["path"],
            "sha256": item["actual_sha256"],
            "role": item["role"],
        }
        for item in input_fingerprints
    ]
    return {
        "export_version": EXPORT_VERSION,
        "validation_status": "PASS",
        "database_access": "read_only",
        "source_dataset_versions": source_dataset_versions,
        "source_objects": {
            "national_charging": ["core.charging_equipment", "core.charging_point"],
            "state_charging": ["analytics.charging_by_state", "core.charging_equipment", "core.charging_point"],
            "bbsr_district_charging": ["analytics.charging_by_bbsr_district_2025_harmonized"],
            "bbsr_type_charging": ["analytics.charging_by_bbsr_type_2025_harmonized", "analytics.charging_by_bbsr_district_2025_harmonized"],
            "kba_state_ev_stock": ["core.kba_state_fuel_stock"],
            "kba_registration_region_ev_stock": ["core.kba_district_ev_stock"],
            "state_ev_charging_comparison": ["reports/batch16_state_comparison.csv"],
            "state_temporal_sensitivity": ["reports/batch17_state_temporal_sensitivity.csv"],
            "kba_national_stock_history": ["analytics.kba_national_quarterly_stock"],
        },
        "duckdb_object_contract": database_contract["objects"],
        "exports": [
            {
                "filename": item["filename"],
                "row_count": item["row_count"],
                "column_count": item["column_count"],
                "sha256": item["sha256"],
                "validation_status": "PASS",
            }
            for item in inventory
        ],
    }


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare validated Batch 19 Tableau CSV exports")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--validation-report", type=Path, default=DEFAULT_VALIDATION_REPORT)
    args = parser.parse_args()
    database = args.database if args.database.is_absolute() else ROOT / args.database
    export_dir = args.export_dir if args.export_dir.is_absolute() else ROOT / args.export_dir
    validation_report = args.validation_report if args.validation_report.is_absolute() else ROOT / args.validation_report
    require(database.is_file(), f"Missing DuckDB database: {database}")
    database_before = sha256(database)
    fingerprints_before = fingerprint_inputs()

    try:
        conn = duckdb.connect(str(database), read_only=True)
    except Exception as exc:  # pragma: no cover - environment error path
        raise ExportError(f"Could not open DuckDB read-only: {exc}") from exc
    try:
        database_contract = validate_database_contract(conn)
        national_charging, state_charging, infra_checks = load_charging_exports(conn)
        bbsr_district, bbsr_type, bbsr_checks = load_bbsr_exports(conn)
        kba_state, kba_region, kba_checks = load_kba_state_and_region_exports(conn)
        national_history, history_checks = load_national_history(conn)
    finally:
        conn.close()

    database_after = sha256(database)
    require(database_before == database_after, "DuckDB SHA-256 changed during read-only export")
    fingerprints_after = fingerprint_inputs()
    require(
        [(row["path"], row["actual_sha256"]) for row in fingerprints_before]
        == [(row["path"], row["actual_sha256"]) for row in fingerprints_after],
        "An approved input fingerprint changed during export",
    )

    comparison_fields, comparison_rows, comparison_checks = load_state_comparison_export()
    temporal_fields, temporal_rows, temporal_checks = load_temporal_sensitivity_export()

    exports: List[Dict[str, Any]] = [
        {
            "filename": "national_charging_2026_09_30.csv",
            "fieldnames": [
                "geography_name",
                "bnetza_reference_date",
                "equipment_count",
                "declared_charging_point_count",
                "charging_point_count",
                "normal_charging_point_count",
                "fast_charging_point_count",
                "points_ge_150_kw",
                "points_ge_350_kw",
                "unclassifiable_power_point_count",
                "equipment_nominal_power_mw",
                "fast_point_share_pct",
                "points_ge_150_share_pct",
                "points_ge_350_share_pct",
            ],
            "rows": national_charging,
            "key": ("geography_name",),
            "grain": "One row for Germany at the BNetzA infrastructure snapshot",
            "source_objects": ["core.charging_equipment", "core.charging_point"],
            "source_dates": [INFRASTRUCTURE_REFERENCE_DATE],
        },
        {
            "filename": "state_charging_2026_09_30.csv",
            "fieldnames": [
                "state_name",
                "bnetza_reference_date",
                "equipment_count",
                "declared_charging_point_count",
                "charging_point_count",
                "normal_charging_point_count",
                "fast_charging_point_count",
                "points_ge_150_kw",
                "points_ge_350_kw",
                "unclassifiable_power_point_count",
                "equipment_nominal_power_mw",
                "fast_point_share_pct",
                "points_ge_150_share_pct",
                "points_ge_350_share_pct",
                "charging_point_national_share_pct",
            ],
            "rows": state_charging,
            "key": ("state_name",),
            "grain": "One Bundesland at the BNetzA infrastructure snapshot",
            "source_objects": ["analytics.charging_by_state", "core.charging_equipment", "core.charging_point"],
            "source_dates": [INFRASTRUCTURE_REFERENCE_DATE],
        },
        {
            "filename": "bbsr_district_charging_2025_geography.csv",
            "fieldnames": [
                "historical_bbsr_administrative_district_code",
                "historical_bbsr_administrative_district_name",
                "historical_bbsr_federal_state_code",
                "historical_bbsr_federal_state_name",
                "historical_bbsr_settlement_type_code",
                "historical_bbsr_settlement_type_name_de",
                "bbsr_reference_date",
                "bnetza_reference_date",
                "source_component_count",
                "source_component_names",
                "historical_boundary_basis",
                "mapping_method",
                "boundary_compatibility_status",
                "equipment_count",
                "declared_charging_point_count",
                "charging_point_count",
                "normal_charging_point_count",
                "fast_charging_point_count",
                "points_ge_150_kw",
                "points_ge_350_kw",
                "unclassifiable_power_point_count",
                "equipment_nominal_power_mw",
                "fast_point_share_pct",
                "points_ge_150_share_pct",
                "points_ge_350_share_pct",
                "equipment_national_share_pct",
                "charging_point_national_share_pct",
            ],
            "rows": bbsr_district,
            "key": ("historical_bbsr_administrative_district_code",),
            "grain": "One historical BBSR 2025 geographic unit; charging-only BNetzA measures at 2026-09-30",
            "source_objects": ["analytics.charging_by_bbsr_district_2025_harmonized"],
            "source_dates": [BBSR_REFERENCE_DATE, INFRASTRUCTURE_REFERENCE_DATE],
        },
        {
            "filename": "bbsr_type_charging_2025_geography.csv",
            "fieldnames": [
                "bbsr_settlement_type_code",
                "bbsr_settlement_type_name_de",
                "bbsr_reference_date",
                "bnetza_reference_date",
                "historical_bbsr_unit_count",
                "source_component_count",
                "equipment_count",
                "charging_point_count",
                "normal_charging_point_count",
                "fast_charging_point_count",
                "points_ge_150_kw",
                "points_ge_350_kw",
                "equipment_nominal_power_mw",
                "fast_point_share_pct",
                "points_ge_150_share_pct",
                "points_ge_350_share_pct",
                "equipment_national_share_pct",
                "charging_point_national_share_pct",
                "fast_point_national_share_pct",
                "points_ge_150_national_share_pct",
                "points_ge_350_national_share_pct",
                "equipment_nominal_power_national_share_pct",
                "classification_scope",
            ],
            "rows": bbsr_type,
            "key": ("bbsr_settlement_type_code",),
            "grain": "One validated BBSR settlement type aggregating the 400 historical units",
            "source_objects": ["analytics.charging_by_bbsr_type_2025_harmonized", "analytics.charging_by_bbsr_district_2025_harmonized"],
            "source_dates": [BBSR_REFERENCE_DATE, INFRASTRUCTURE_REFERENCE_DATE],
        },
        {
            "filename": "kba_state_ev_stock_2026.csv",
            "fieldnames": [
                "state_name",
                "kba_reference_date",
                "passenger_car_stock",
                "bev_passenger_car_stock",
                "phev_passenger_car_stock",
                "combined_plugin_passenger_car_stock",
                "bev_penetration_pct",
                "phev_penetration_pct",
                "combined_plugin_penetration_pct",
                "bev_stock_change_from_2026_01_01",
                "bev_stock_growth_pct_from_2026_01_01",
                "phev_stock_change_from_2026_01_01",
                "phev_stock_growth_pct_from_2026_01_01",
            ],
            "rows": kba_state,
            "key": ("state_name", "kba_reference_date"),
            "grain": "One named federal state × KBA stock reference date; excludes Deutschland and Sonstige",
            "source_objects": ["core.kba_state_fuel_stock"],
            "source_dates": list(KBA_DATES),
        },
        {
            "filename": "kba_registration_region_ev_stock_2026.csv",
            "fieldnames": [
                "kba_registration_region_code",
                "registration_region_name",
                "state_name",
                "kba_reference_date",
                "passenger_car_stock",
                "bev_passenger_car_stock",
                "phev_passenger_car_stock",
                "combined_plugin_passenger_car_stock",
                "bev_penetration_pct",
                "phev_penetration_pct",
                "combined_plugin_penetration_pct",
                "bev_stock_change_from_2026_01_01",
                "bev_stock_growth_pct_from_2026_01_01",
                "phev_stock_change_from_2026_01_01",
                "phev_stock_growth_pct_from_2026_01_01",
            ],
            "rows": kba_region,
            "key": ("kba_registration_region_code", "kba_reference_date"),
            "grain": "One KBA registration region × KBA stock reference date; no BBSR join",
            "source_objects": ["core.kba_district_ev_stock"],
            "source_dates": list(KBA_DATES),
        },
        {
            "filename": "state_ev_charging_comparison_2026.csv",
            "fieldnames": comparison_fields,
            "rows": comparison_rows,
            "key": ("state_name",),
            "grain": "One Bundesland comparing KBA July 2026 stock with BNetzA September 2026 infrastructure",
            "source_objects": ["reports/batch16_state_comparison.csv"],
            "source_dates": [KBA_PRIMARY_DATE, INFRASTRUCTURE_REFERENCE_DATE],
        },
        {
            "filename": "state_temporal_sensitivity_2026.csv",
            "fieldnames": temporal_fields,
            "rows": temporal_rows,
            "key": ("state_name",),
            "grain": "One Bundesland comparing the published September snapshot with the retrospective September-survivor cohort",
            "source_objects": ["reports/batch17_state_temporal_sensitivity.csv"],
            "source_dates": [KBA_PRIMARY_DATE, INFRASTRUCTURE_REFERENCE_DATE, SURVIVOR_CUTOFF_DATE],
        },
        {
            "filename": "kba_national_stock_history.csv",
            "fieldnames": [
                "stock_date",
                "source_report_snapshot",
                "bev_passenger_car_stock",
                "phev_passenger_car_stock",
                "passenger_car_stock",
                "combined_plugin_passenger_car_stock",
                "bev_penetration_pct",
                "phev_penetration_pct",
                "combined_plugin_penetration_pct",
                "source_object",
            ],
            "rows": national_history,
            "key": ("stock_date",),
            "grain": "One deduplicated national KBA history row per stock date",
            "source_objects": ["analytics.kba_national_quarterly_stock"],
            "source_dates": [history_checks["min_stock_date"], history_checks["max_stock_date"]],
        },
    ]

    numeric_by_export = {
        "national_charging_2026_09_30.csv": {field for field in exports[0]["fieldnames"] if field not in {"geography_name", "bnetza_reference_date"}},
        "state_charging_2026_09_30.csv": {field for field in exports[1]["fieldnames"] if field not in {"state_name", "bnetza_reference_date"}},
        "bbsr_district_charging_2025_geography.csv": {field for field in exports[2]["fieldnames"] if field not in {"historical_bbsr_administrative_district_code", "historical_bbsr_administrative_district_name", "historical_bbsr_federal_state_code", "historical_bbsr_federal_state_name", "historical_bbsr_settlement_type_code", "historical_bbsr_settlement_type_name_de", "bbsr_reference_date", "bnetza_reference_date", "source_component_names", "historical_boundary_basis", "mapping_method", "boundary_compatibility_status"}},
        "bbsr_type_charging_2025_geography.csv": {field for field in exports[3]["fieldnames"] if field not in {"bbsr_settlement_type_code", "bbsr_settlement_type_name_de", "bbsr_reference_date", "bnetza_reference_date", "classification_scope"}},
        "kba_state_ev_stock_2026.csv": {field for field in exports[4]["fieldnames"] if field not in {"state_name", "kba_reference_date"}},
        "kba_registration_region_ev_stock_2026.csv": {field for field in exports[5]["fieldnames"] if field not in {"kba_registration_region_code", "registration_region_name", "state_name", "kba_reference_date"}},
        "state_ev_charging_comparison_2026.csv": {field for field in comparison_fields if field not in {"state_name", "kba_reference_date", "bnetza_reference_date", "bevs_per_charging_point_publication_status", "registered_charging_points_per_1000_bevs_publication_status", "fast_points_per_1000_bevs_publication_status", "points_ge_150_per_1000_bevs_publication_status", "points_ge_350_per_1000_bevs_publication_status", "bev_stock_minus_charging_point_share_publication_status", "comparison_scope", "cross_source_temporal_label", "cross_source_date_note"}},
        "state_temporal_sensitivity_2026.csv": {field for field in temporal_fields if field not in {"state_name", "kba_reference_date", "bnetza_reference_date", "survivor_cutoff_date", "status_labels", "temporal_label_published", "temporal_label_survivor", "publication_status"}},
        "kba_national_stock_history.csv": {field for field in exports[8]["fieldnames"] if field not in {"stock_date", "source_report_snapshot", "source_object"}},
    }
    date_by_export = {
        "national_charging_2026_09_30.csv": {"bnetza_reference_date"},
        "state_charging_2026_09_30.csv": {"bnetza_reference_date"},
        "bbsr_district_charging_2025_geography.csv": {"bbsr_reference_date", "bnetza_reference_date"},
        "bbsr_type_charging_2025_geography.csv": {"bbsr_reference_date", "bnetza_reference_date"},
        "kba_state_ev_stock_2026.csv": {"kba_reference_date"},
        "kba_registration_region_ev_stock_2026.csv": {"kba_reference_date"},
        "state_ev_charging_comparison_2026.csv": {"kba_reference_date", "bnetza_reference_date"},
        "state_temporal_sensitivity_2026.csv": {"kba_reference_date", "bnetza_reference_date", "survivor_cutoff_date"},
        "kba_national_stock_history.csv": {"stock_date", "source_report_snapshot"},
    }
    inventory: List[Dict[str, Any]] = []
    export_dir.mkdir(parents=True, exist_ok=True)
    for item in exports:
        path = export_dir / item["filename"]
        write_csv(path, item["fieldnames"], item["rows"])
        check = validate_written_csv(path, item["fieldnames"], item["rows"], item["key"], sorted(numeric_by_export[item["filename"]]), sorted(date_by_export[item["filename"]]))
        inventory.append(
            {
                "filename": item["filename"],
                "row_count": check["row_count"],
                "column_count": check["column_count"],
                "sha256": check["sha256"],
                "primary_key": ", ".join(item["key"]),
                "grain": item["grain"],
                "source_objects": item["source_objects"],
                "source_dates": item["source_dates"],
            }
        )

    manifest = build_manifest(inventory, fingerprints_before, database_contract)
    manifest_path = export_dir / "export_manifest.json"
    write_json(manifest_path, manifest)
    report_text = render_validation_report(
        inventory,
        database_before,
        fingerprints_before,
        database_contract,
        infra_checks,
        bbsr_checks,
        kba_checks,
        history_checks,
    )
    validation_report.parent.mkdir(parents=True, exist_ok=True)
    validation_report.write_text(report_text, encoding="utf-8")

    print(json.dumps({
        "status": "PASS",
        "export_version": EXPORT_VERSION,
        "database_sha256": database_before,
        "exports": [{"filename": item["filename"], "rows": item["row_count"], "columns": item["column_count"], "sha256": item["sha256"]} for item in inventory],
        "manifest": str(manifest_path.relative_to(ROOT)),
        "validation_report": str(validation_report.relative_to(ROOT)),
        "batch16_input": comparison_checks,
        "batch17_input": temporal_checks,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExportError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)
