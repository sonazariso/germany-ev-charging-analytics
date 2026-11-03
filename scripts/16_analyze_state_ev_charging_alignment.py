#!/usr/bin/env python3
"""Batch 16: compare German state EV stock with registered charging infrastructure.

The analysis is deliberately read-only with respect to DuckDB and the source
artifacts.  It reads the validated KBA FZ 27.2 state fuel table for
2026-07-01, the source-aware BNetzA state view, and the normalized charging
tables for 2026-09-30.  Charging equipment and point measures are aggregated
separately from KBA stock before the two one-row-per-state results are joined.

Run from the repository root::

    .venv/bin/python scripts/16_analyze_state_ev_charging_alignment.py --json

The script writes the approved Batch 16 report and CSV diagnostics only.  It
does not create or modify DuckDB objects, source workbooks, or geographic
crosswalks.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_REPORT = ROOT / "reports/batch16_state_ev_charging_alignment.md"
DEFAULT_OUTPUT_DIR = ROOT / "reports"

INFRASTRUCTURE_SOURCE_ID = "bnetza_charging_2026_09_30"
INFRASTRUCTURE_REFERENCE_DATE = "2026-09-30"
KBA_SOURCE_ID = "kba_fz27_2026_07"
KBA_REFERENCE_DATE = "2026-07-01"

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

EXPECTED = {
    "equipment": 117_662,
    "declared_points": 211_253,
    "charging_points": 211_253,
    "normal_points": 156_155,
    "fast_points": 55_098,
    "points_ge_150": 40_950,
    "points_ge_350": 6_950,
    "unclassifiable_points": 0,
    "nominal_power_mw": 9_215.4173,
    "national_passenger_cars": 49_696_710,
    "sixteen_state_passenger_cars": 49_644_855,
    "sonstige_passenger_cars": 51_855,
    "national_bev": 2_365_047,
    "sixteen_state_bev": 2_362_218,
    "sonstige_bev": 2_829,
    "national_phev": 1_226_863,
    "sixteen_state_phev": 1_225_241,
    "sonstige_phev": 1_622,
    "district_rows": 400,
}

# These are the source fingerprints established by the earlier batches.  The
# BBSR workbook is not used in Batch 16, but is included to prove that all
# preserved original workbooks stayed unchanged during the run.
EXPECTED_FINGERPRINTS = {
    "data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx": (
        "1e82c1734b17e17e51092a0f9460a5e204888569fb12aa5940b30e9cdb726342",
        "BNetzA source workbook",
    ),
    "data/raw/kba/fz27_202601.xlsx": (
        "29ab2eaa178a1c6a3463d5cad707fee1e762241304ae6bb08c29702d6e6aea31",
        "KBA FZ 27 source workbook, 2026-01-01",
    ),
    "data/raw/kba/fz27_202604.xlsx": (
        "28fffaa7d2f21ede6d7f6988a717b749b759a308755c472df4d391c73a0653e7",
        "KBA FZ 27 source workbook, 2026-04-01",
    ),
    "data/raw/kba/fz27_202607.xlsx": (
        "d6a26702fa6f8358cc5f0e15e88c04ac6c36527be404058674138dd9571bc803",
        "KBA FZ 27 source workbook, 2026-07-01",
    ),
    "data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx": (
        "083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525",
        "BBSR reference workbook, 2025 geographic stand",
    ),
    "data/reference/bnetza_kba_district_crosswalk_2026.csv": (
        "fdf139c5057250184358e3014267a4a4c4259749113273f6bd48206f6a64fe6a",
        "BNetzA-to-KBA geographic crosswalk",
    ),
}


class AnalysisError(RuntimeError):
    """Raised when a reproducibility or reconciliation check fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisError(message)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def relative_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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


def pct(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return 100.0 * float(numerator) / float(denominator)


def ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator) / float(denominator)


def fmt_int(value: Any) -> str:
    if value is None:
        return "—"
    return f"{int(value):,}"


def fmt_num(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{float(value):,.{decimals}f}"


def fmt_pct(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{float(value):,.{decimals}f}%"


def fmt_ratio(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{float(value):,.{decimals}f}"


def fmt_pp(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{float(value):+,.{decimals}f} pp"


def query_dicts(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: Sequence[Any] = (),
) -> List[Dict[str, Any]]:
    result = conn.execute(sql, params)
    names = [item[0] for item in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def table_type(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> Optional[str]:
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


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.10f}".rstrip("0").rstrip(".") or "0"
    if isinstance(value, (list, tuple)):
        return "; ".join(str(item) for item in value)
    return value


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field)) for field in fieldnames})


def markdown_table(headers: Sequence[Any], rows: Sequence[Sequence[Any]]) -> List[str]:
    lines = [
        "| " + " | ".join(str(item) for item in headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines


def fingerprint_sources() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for relative, (expected, purpose) in EXPECTED_FINGERPRINTS.items():
        path = ROOT / relative
        require(path.is_file(), f"Missing fingerprint source: {relative}")
        actual = sha256(path)
        rows.append(
            {
                "path": relative,
                "purpose": purpose,
                "bytes": path.stat().st_size,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "match": actual == expected,
            }
        )
    require(all(bool(row["match"]) for row in rows), "One or more source fingerprints changed")
    return rows


def validate_database_contract(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    expected_objects = {
        "core.charging_equipment": "BASE TABLE",
        "core.charging_point": "BASE TABLE",
        "core.kba_state_fuel_stock": "BASE TABLE",
        "core.kba_district_ev_stock": "BASE TABLE",
        "analytics.charging_by_state": "VIEW",
    }
    actual_objects: Dict[str, str] = {}
    for qualified, expected_type in expected_objects.items():
        actual = table_type(conn, qualified)
        require(actual == expected_type, f"Unexpected or missing object {qualified}: {actual}")
        actual_objects[qualified] = actual

    required_columns = {
        "core.charging_equipment": {
            "source_id",
            "excel_row",
            "state_name",
            "declared_point_count",
            "equipment_nominal_power_kw",
            "status",
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
    }
    for qualified, required in required_columns.items():
        actual = set(object_columns(conn, qualified))
        require(required <= actual, f"Missing columns in {qualified}: {sorted(required - actual)}")

    view_rows = query_dicts(conn, "SELECT * FROM analytics.charging_by_state ORDER BY state_name")
    require(len(view_rows) == 16, f"Expected 16 state rows in analytics.charging_by_state, found {len(view_rows)}")
    require(
        {str(row["state_name"]) for row in view_rows} == set(FEDERAL_STATES),
        "analytics.charging_by_state does not contain exactly the 16 federal states",
    )
    return {
        "read_only": True,
        "objects": actual_objects,
        "charging_by_state_rows": len(view_rows),
        "charging_by_state_state_count": len({str(row["state_name"]) for row in view_rows}),
    }


def load_state_vehicle_stock(conn: duckdb.DuckDBPyConnection) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    raw_rows = query_dicts(
        conn,
        """
        SELECT state_name, fuel_type, passenger_cars
        FROM core.kba_state_fuel_stock
        WHERE source_id = ? AND reference_date = CAST(? AS DATE)
        ORDER BY state_name, fuel_type
        """,
        [KBA_SOURCE_ID, KBA_REFERENCE_DATE],
    )
    require(len(raw_rows) == 18 * 7, f"Expected 126 July KBA state-fuel rows, found {len(raw_rows)}")
    expected_fuels = set(MUTUALLY_EXCLUSIVE_TOTAL_FUELS) | {PHEV_FUEL}
    values: Dict[Tuple[str, str], int] = {}
    for row in raw_rows:
        geography = str(row["state_name"])
        fuel = str(row["fuel_type"])
        key = (geography, fuel)
        require(key not in values, f"Duplicate KBA state/fuel row: {key}")
        require(geography in ALL_KBA_STATE_GEOGRAPHIES, f"Unexpected KBA state label: {geography}")
        require(fuel in expected_fuels, f"Unexpected KBA fuel label: {fuel}")
        require(row["passenger_cars"] is not None, f"NULL KBA passenger-car count: {key}")
        value = int(row["passenger_cars"])
        require(value >= 0, f"Negative KBA passenger-car count: {key}")
        values[key] = value

    for geography in ALL_KBA_STATE_GEOGRAPHIES:
        fuels = {fuel for (geo, fuel) in values if geo == geography}
        require(fuels == expected_fuels, f"Incomplete KBA fuel coverage for {geography}: {sorted(fuels)}")

    by_geography: Dict[str, Dict[str, int]] = {}
    for geography in ALL_KBA_STATE_GEOGRAPHIES:
        total_cars = sum(values[(geography, fuel)] for fuel in MUTUALLY_EXCLUSIVE_TOTAL_FUELS)
        bev = values[(geography, BEV_FUEL)]
        phev = values[(geography, PHEV_FUEL)]
        hybrid_total = values[(geography, "Hybrid insgesamt")]
        require(hybrid_total >= phev, f"PHEV exceeds Hybrid insgesamt for {geography}")
        require(bev + phev <= total_cars, f"Combined BEV/PHEV exceeds passenger cars for {geography}")
        by_geography[geography] = {
            "passenger_car_stock": total_cars,
            "bev_stock": bev,
            "phev_stock": phev,
            "combined_plugin_stock": bev + phev,
        }

    state_sum = {
        field: sum(by_geography[state][field] for state in FEDERAL_STATES)
        for field in ("passenger_car_stock", "bev_stock", "phev_stock", "combined_plugin_stock")
    }
    national = by_geography[NATIONAL_GEOGRAPHY]
    sonstige = by_geography[RESIDUAL_GEOGRAPHY]
    for field in ("passenger_car_stock", "bev_stock", "phev_stock"):
        require(
            national[field] == state_sum[field] + sonstige[field],
            f"KBA Deutschland != 16 states + Sonstige for {field}",
        )

    district_rows = query_dicts(
        conn,
        """
        SELECT district_code, state_name, passenger_cars, bev_cars, phev_cars
        FROM core.kba_district_ev_stock
        WHERE source_id = ? AND reference_date = CAST(? AS DATE)
        ORDER BY district_code
        """,
        [KBA_SOURCE_ID, KBA_REFERENCE_DATE],
    )
    require(len(district_rows) == EXPECTED["district_rows"], f"Expected 400 KBA district rows, found {len(district_rows)}")
    district_codes = [str(row["district_code"]) for row in district_rows]
    require(len(set(district_codes)) == EXPECTED["district_rows"], "Duplicate KBA district codes in July stock")
    for row in district_rows:
        for field in ("passenger_cars", "bev_cars", "phev_cars"):
            require(row[field] is not None, f"NULL KBA district metric {field}: {row['district_code']}")
            require(int(row[field]) >= 0, f"Negative KBA district metric {field}: {row['district_code']}")
    district_sum = {
        "passenger_car_stock": sum(int(row["passenger_cars"]) for row in district_rows),
        "bev_stock": sum(int(row["bev_cars"]) for row in district_rows),
        "phev_stock": sum(int(row["phev_cars"]) for row in district_rows),
    }
    district_sum["combined_plugin_stock"] = district_sum["bev_stock"] + district_sum["phev_stock"]
    for field in district_sum:
        require(district_sum[field] == state_sum[field], f"KBA 400-region total does not equal 16-state sum for {field}")

    require(national["passenger_car_stock"] == EXPECTED["national_passenger_cars"], "Unexpected national passenger-car total")
    require(state_sum["passenger_car_stock"] == EXPECTED["sixteen_state_passenger_cars"], "Unexpected 16-state passenger-car total")
    require(sonstige["passenger_car_stock"] == EXPECTED["sonstige_passenger_cars"], "Unexpected Sonstige passenger-car total")
    require(national["bev_stock"] == EXPECTED["national_bev"], "Unexpected national BEV total")
    require(state_sum["bev_stock"] == EXPECTED["sixteen_state_bev"], "Unexpected 16-state BEV total")
    require(sonstige["bev_stock"] == EXPECTED["sonstige_bev"], "Unexpected Sonstige BEV total")
    require(national["phev_stock"] == EXPECTED["national_phev"], "Unexpected national PHEV total")
    require(state_sum["phev_stock"] == EXPECTED["sixteen_state_phev"], "Unexpected 16-state PHEV total")
    require(sonstige["phev_stock"] == EXPECTED["sonstige_phev"], "Unexpected Sonstige PHEV total")

    rows: List[Dict[str, Any]] = []
    for state in FEDERAL_STATES:
        value = by_geography[state]
        rows.append(
            {
                "state_name": state,
                "passenger_car_stock": value["passenger_car_stock"],
                "bev_stock": value["bev_stock"],
                "phev_stock": value["phev_stock"],
                "combined_plugin_stock": value["combined_plugin_stock"],
                "bev_penetration_pct": pct(value["bev_stock"], value["passenger_car_stock"]),
                "phev_penetration_pct": pct(value["phev_stock"], value["passenger_car_stock"]),
                "combined_plugin_penetration_pct": pct(value["combined_plugin_stock"], value["passenger_car_stock"]),
            }
        )

    checks = {
        "source_id": KBA_SOURCE_ID,
        "reference_date": KBA_REFERENCE_DATE,
        "state_rows": len(rows),
        "state_fuel_rows": len(raw_rows),
        "national": national,
        "sixteen_state_sum": state_sum,
        "sonstige": sonstige,
        "four_hundred_region_sum": district_sum,
        "four_hundred_region_rows": len(district_rows),
        "fuel_category_reconciliation": "PASS — six mutually exclusive FZ 27.2 rows; PHEV kept as nested detail",
    }
    require(len(rows) == 16, f"Expected 16 federal-state stock rows, found {len(rows)}")
    return rows, {"by_geography": by_geography, "checks": checks}


def load_charging_state_metrics(conn: duckdb.DuckDBPyConnection) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    view_rows = query_dicts(
        conn,
        """
        SELECT state_name, equipment_rows, declared_points, populated_point_slots
        FROM analytics.charging_by_state
        ORDER BY state_name
        """,
    )
    view_by_state = {str(row["state_name"]): row for row in view_rows}
    require(set(view_by_state) == set(FEDERAL_STATES), "State charging view does not match the 16 federal states")

    equipment_rows = query_dicts(
        conn,
        """
        SELECT state_name,
               COUNT(*) AS equipment_count,
               SUM(COALESCE(declared_point_count, 0)) AS declared_charging_point_count,
               SUM(COALESCE(equipment_nominal_power_kw, 0.0)) AS equipment_nominal_power_kw,
               COUNT(*) FILTER (WHERE status = 'In Betrieb') AS equipment_in_operation,
               COUNT(*) FILTER (WHERE status = 'In Wartung') AS equipment_in_maintenance,
               COUNT(*) FILTER (WHERE status NOT IN ('In Betrieb', 'In Wartung') OR status IS NULL) AS equipment_other_status,
               LIST(DISTINCT COALESCE(status, '<NULL>') ORDER BY COALESCE(status, '<NULL>')) AS status_labels
        FROM core.charging_equipment
        WHERE source_id = ?
        GROUP BY state_name
        ORDER BY state_name
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    )
    equipment_by_state = {str(row["state_name"]): row for row in equipment_rows}
    require(set(equipment_by_state) == set(FEDERAL_STATES), "Charging equipment does not match the 16 federal states")

    point_rows = query_dicts(
        conn,
        """
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
        SELECT p.state_name,
               COUNT(*) AS charging_point_count,
               COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw <= 22) AS normal_charging_point_count,
               COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw > 22) AS fast_charging_point_count,
               COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw >= 150) AS points_ge_150_kw,
               COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw >= 350) AS points_ge_350_kw,
               COUNT(*) FILTER (WHERE pp.max_declared_point_power_kw IS NULL) AS points_without_valid_power
        FROM source_points AS p
        LEFT JOIN point_power AS pp
          ON pp.source_id = p.source_id
         AND pp.equipment_excel_row = p.equipment_excel_row
         AND pp.point_number = p.point_number
        GROUP BY p.state_name
        ORDER BY p.state_name
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    )
    points_by_state = {str(row["state_name"]): row for row in point_rows}
    require(set(points_by_state) == set(FEDERAL_STATES), "Charging points do not match the 16 federal states")

    duplicate_point_rows = conn.execute(
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
    orphan_point_rows = conn.execute(
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
    equipment_point_mismatches = conn.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT e.source_id,
                   e.excel_row,
                   COALESCE(e.declared_point_count, 0) AS declared_point_count,
                   COUNT(p.point_number) AS populated_point_slots
            FROM core.charging_equipment AS e
            LEFT JOIN core.charging_point AS p
              ON p.source_id = e.source_id
             AND p.equipment_excel_row = e.excel_row
            WHERE e.source_id = ?
            GROUP BY e.source_id, e.excel_row, e.declared_point_count
            HAVING COALESCE(e.declared_point_count, 0) <> COUNT(p.point_number)
        ) AS mismatches
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    ).fetchone()[0]
    require(int(duplicate_point_rows) == 0, f"Duplicate point identities: {duplicate_point_rows}")
    require(int(orphan_point_rows) == 0, f"Orphan charging points: {orphan_point_rows}")
    require(int(equipment_point_mismatches) == 0, f"Equipment/point count mismatches: {equipment_point_mismatches}")

    rows: List[Dict[str, Any]] = []
    for state in FEDERAL_STATES:
        equipment = equipment_by_state[state]
        points = points_by_state[state]
        view = view_by_state[state]
        equipment_count = int(equipment["equipment_count"])
        declared_points = int(equipment["declared_charging_point_count"])
        point_count = int(points["charging_point_count"])
        require(equipment_count == int(view["equipment_rows"]), f"State view equipment mismatch: {state}")
        require(declared_points == int(view["declared_points"]), f"State view declared-point mismatch: {state}")
        require(point_count == int(view["populated_point_slots"]), f"State view populated-point mismatch: {state}")
        require(declared_points == point_count, f"Declared/populated points differ: {state}")
        normal = int(points["normal_charging_point_count"])
        fast = int(points["fast_charging_point_count"])
        ge150 = int(points["points_ge_150_kw"])
        ge350 = int(points["points_ge_350_kw"])
        invalid_power = int(points["points_without_valid_power"])
        require(normal + fast + invalid_power == point_count, f"Power-band denominator mismatch: {state}")
        rows.append(
            {
                "state_name": state,
                "equipment_count": equipment_count,
                "declared_charging_point_count": declared_points,
                "charging_point_count": point_count,
                "normal_charging_point_count": normal,
                "fast_charging_point_count": fast,
                "points_ge_150_kw": ge150,
                "points_ge_350_kw": ge350,
                "points_without_valid_power": invalid_power,
                "equipment_nominal_power_kw": float(equipment["equipment_nominal_power_kw"] or 0.0),
                "equipment_nominal_power_mw": float(equipment["equipment_nominal_power_kw"] or 0.0) / 1000.0,
                "equipment_in_operation": int(equipment["equipment_in_operation"] or 0),
                "equipment_in_maintenance": int(equipment["equipment_in_maintenance"] or 0),
                "equipment_other_status": int(equipment["equipment_other_status"] or 0),
                "equipment_status_labels": "; ".join(str(item) for item in (equipment["status_labels"] or [])),
                "fast_point_share_pct": pct(fast, point_count),
                "points_ge_150_share_pct": pct(ge150, point_count),
                "points_ge_350_share_pct": pct(ge350, point_count),
            }
        )

    totals = {
        field: sum(int(row[field]) for row in rows)
        for field in (
            "equipment_count",
            "declared_charging_point_count",
            "charging_point_count",
            "normal_charging_point_count",
            "fast_charging_point_count",
            "points_ge_150_kw",
            "points_ge_350_kw",
            "points_without_valid_power",
        )
    }
    nominal_power_kw = sum(float(row["equipment_nominal_power_kw"]) for row in rows)
    totals["equipment_nominal_power_kw"] = nominal_power_kw
    totals["equipment_nominal_power_mw"] = nominal_power_kw / 1000.0
    for field, expected in (
        ("equipment_count", EXPECTED["equipment"]),
        ("declared_charging_point_count", EXPECTED["declared_points"]),
        ("charging_point_count", EXPECTED["charging_points"]),
        ("normal_charging_point_count", EXPECTED["normal_points"]),
        ("fast_charging_point_count", EXPECTED["fast_points"]),
        ("points_ge_150_kw", EXPECTED["points_ge_150"]),
        ("points_ge_350_kw", EXPECTED["points_ge_350"]),
        ("points_without_valid_power", EXPECTED["unclassifiable_points"]),
    ):
        require(totals[field] == expected, f"Unexpected BNetzA total for {field}: {totals[field]}")
    require(
        math.isclose(float(totals["equipment_nominal_power_mw"]), EXPECTED["nominal_power_mw"], rel_tol=0, abs_tol=1e-9),
        f"Unexpected BNetzA nominal power: {totals['equipment_nominal_power_mw']}",
    )

    checks = {
        "source_id": INFRASTRUCTURE_SOURCE_ID,
        "reference_date": INFRASTRUCTURE_REFERENCE_DATE,
        "state_rows": len(rows),
        "totals": totals,
        "duplicate_point_identities": int(duplicate_point_rows),
        "orphan_point_rows": int(orphan_point_rows),
        "equipment_point_mismatches": int(equipment_point_mismatches),
        "power_definition": "Maximum numeric token in semicolon-separated connector_power_raw; <=22 kW normal, >22 kW fast, >=150/350 kW nested thresholds",
        "equipment_status_definition": "Statuses retained at equipment grain; no status filter applied to headline totals",
    }
    require(len(rows) == 16, f"Expected 16 federal-state charging rows, found {len(rows)}")
    return rows, checks


def join_state_metrics(
    vehicle_rows: Sequence[Mapping[str, Any]],
    charging_rows: Sequence[Mapping[str, Any]],
    vehicle_checks: Mapping[str, Any],
    charging_checks: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    vehicle_by_state = {str(row["state_name"]): row for row in vehicle_rows}
    charging_by_state = {str(row["state_name"]): row for row in charging_rows}
    require(set(vehicle_by_state) == set(FEDERAL_STATES), "Vehicle state join is not exactly 16 states")
    require(set(charging_by_state) == set(FEDERAL_STATES), "Charging state join is not exactly 16 states")
    total_state_bev = int(vehicle_checks["sixteen_state_sum"]["bev_stock"])
    total_points = int(charging_checks["totals"]["charging_point_count"])

    rows: List[Dict[str, Any]] = []
    for state in FEDERAL_STATES:
        vehicle = vehicle_by_state[state]
        charging = charging_by_state[state]
        bev = int(vehicle["bev_stock"])
        phev = int(vehicle["phev_stock"])
        points = int(charging["charging_point_count"])
        bev_share = pct(bev, total_state_bev)
        point_share = pct(points, total_points)
        rows.append(
            {
                "state_name": state,
                "kba_reference_date": KBA_REFERENCE_DATE,
                "bnetza_reference_date": INFRASTRUCTURE_REFERENCE_DATE,
                "passenger_car_stock": int(vehicle["passenger_car_stock"]),
                "bev_stock": bev,
                "phev_stock": phev,
                "combined_plugin_stock": int(vehicle["combined_plugin_stock"]),
                "bev_penetration_pct": vehicle["bev_penetration_pct"],
                "phev_penetration_pct": vehicle["phev_penetration_pct"],
                "combined_plugin_penetration_pct": vehicle["combined_plugin_penetration_pct"],
                "bev_stock_share_of_16_state_bev_stock_pct": bev_share,
                "equipment_count": int(charging["equipment_count"]),
                "declared_charging_point_count": int(charging["declared_charging_point_count"]),
                "charging_point_count": points,
                "normal_charging_point_count": int(charging["normal_charging_point_count"]),
                "fast_charging_point_count": int(charging["fast_charging_point_count"]),
                "points_ge_150_kw": int(charging["points_ge_150_kw"]),
                "points_ge_350_kw": int(charging["points_ge_350_kw"]),
                "points_without_valid_power": int(charging["points_without_valid_power"]),
                "fast_point_share_pct": charging["fast_point_share_pct"],
                "points_ge_150_share_pct": charging["points_ge_150_share_pct"],
                "points_ge_350_share_pct": charging["points_ge_350_share_pct"],
                "equipment_nominal_power_kw": charging["equipment_nominal_power_kw"],
                "equipment_nominal_power_mw": charging["equipment_nominal_power_mw"],
                "share_of_national_registered_charging_points_pct": point_share,
                "bevs_per_registered_charging_point": ratio(bev, points),
                "registered_charging_points_per_1000_bevs": ratio(points * 1000.0, bev),
                "fast_points_per_1000_bevs": ratio(int(charging["fast_charging_point_count"]) * 1000.0, bev),
                "points_ge_150_per_1000_bevs": ratio(int(charging["points_ge_150_kw"]) * 1000.0, bev),
                "points_ge_350_per_1000_bevs": ratio(int(charging["points_ge_350_kw"]) * 1000.0, bev),
                "bev_stock_share_minus_charging_point_share_pp": (
                    None if bev_share is None or point_share is None else bev_share - point_share
                ),
                "combined_plugin_per_registered_charging_point": ratio(int(vehicle["combined_plugin_stock"]), points),
                "registered_charging_points_per_1000_combined_plugins": ratio(
                    points * 1000.0, int(vehicle["combined_plugin_stock"])
                ),
                "equipment_in_operation": int(charging["equipment_in_operation"]),
                "equipment_in_maintenance": int(charging["equipment_in_maintenance"]),
                "equipment_other_status": int(charging["equipment_other_status"]),
                "equipment_status_labels": charging["equipment_status_labels"],
                "cross_source_date_note": "KBA stock 2026-07-01 versus BNetzA infrastructure 2026-09-30; not contemporaneous",
            }
        )
    require(len(rows) == 16, f"Expected 16 joined state rows, found {len(rows)}")
    require({row["state_name"] for row in rows} == set(FEDERAL_STATES), "Missing or duplicated state join")
    return rows


def make_reconciliation_rows(
    vehicle_checks: Mapping[str, Any],
    charging_checks: Mapping[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    national = vehicle_checks["national"]
    states = vehicle_checks["sixteen_state_sum"]
    sonstige = vehicle_checks["sonstige"]
    district = vehicle_checks["four_hundred_region_sum"]
    charging = charging_checks["totals"]

    fieldnames = (
        "scope",
        "scope_definition",
        "kba_geography",
        "bnetza_geography",
        "kba_reference_date",
        "bnetza_reference_date",
        "passenger_car_stock",
        "bev_stock",
        "phev_stock",
        "combined_plugin_stock",
        "equipment_count",
        "charging_point_count",
        "normal_charging_point_count",
        "fast_charging_point_count",
        "points_ge_150_kw",
        "points_ge_350_kw",
        "equipment_nominal_power_mw",
        "bevs_per_registered_charging_point",
        "registered_charging_points_per_1000_bevs",
        "fast_points_per_1000_bevs",
        "bev_stock_share_of_scope_pct",
        "charging_point_share_of_scope_pct",
        "bev_stock_share_minus_charging_point_share_pp",
        "reconciliation_status",
        "note",
    )

    def row(
        scope: str,
        definition: str,
        kba_geography: Optional[str],
        bnetza_geography: Optional[str],
        vehicle: Optional[Mapping[str, Any]],
        infrastructure: Optional[Mapping[str, Any]],
        note: str,
    ) -> Dict[str, Any]:
        output: Dict[str, Any] = {field: None for field in fieldnames}
        output.update(
            {
                "scope": scope,
                "scope_definition": definition,
                "kba_geography": kba_geography,
                "bnetza_geography": bnetza_geography,
                "kba_reference_date": KBA_REFERENCE_DATE if vehicle is not None else None,
                "bnetza_reference_date": INFRASTRUCTURE_REFERENCE_DATE if infrastructure is not None else None,
                "reconciliation_status": "PASS",
                "note": note,
            }
        )
        if vehicle is not None:
            output.update(
                {
                    "passenger_car_stock": vehicle["passenger_car_stock"],
                    "bev_stock": vehicle["bev_stock"],
                    "phev_stock": vehicle["phev_stock"],
                    "combined_plugin_stock": vehicle["combined_plugin_stock"],
                }
            )
        if infrastructure is not None:
            output.update(
                {
                    "equipment_count": infrastructure["equipment_count"],
                    "charging_point_count": infrastructure["charging_point_count"],
                    "normal_charging_point_count": infrastructure["normal_charging_point_count"],
                    "fast_charging_point_count": infrastructure["fast_charging_point_count"],
                    "points_ge_150_kw": infrastructure["points_ge_150_kw"],
                    "points_ge_350_kw": infrastructure["points_ge_350_kw"],
                    "equipment_nominal_power_mw": infrastructure["equipment_nominal_power_mw"],
                }
            )
        if vehicle is not None and infrastructure is not None:
            output["bevs_per_registered_charging_point"] = ratio(vehicle["bev_stock"], infrastructure["charging_point_count"])
            output["registered_charging_points_per_1000_bevs"] = ratio(
                infrastructure["charging_point_count"] * 1000.0, vehicle["bev_stock"]
            )
            output["fast_points_per_1000_bevs"] = ratio(
                infrastructure["fast_charging_point_count"] * 1000.0, vehicle["bev_stock"]
            )
            output["bev_stock_share_of_scope_pct"] = pct(vehicle["bev_stock"], states["bev_stock"])
            output["charging_point_share_of_scope_pct"] = pct(
                infrastructure["charging_point_count"], charging["charging_point_count"]
            )
            output["bev_stock_share_minus_charging_point_share_pp"] = (
                output["bev_stock_share_of_scope_pct"] - output["charging_point_share_of_scope_pct"]
            )
        return output

    rows = [
        row(
            "kba_published_national_deutschland",
            "Published KBA state-fuel row labelled Deutschland",
            NATIONAL_GEOGRAPHY,
            None,
            national,
            None,
            "Official national KBA scope; not added to 16-state rows as a second geographic unit.",
        ),
        row(
            "kba_sixteen_state_sum",
            "Sum of the 16 named federal-state KBA rows",
            "16 federal states",
            None,
            states,
            None,
            "Comparable vehicle scope for the BNetzA state infrastructure rows.",
        ),
        row(
            "kba_sonstige",
            "Published KBA residual row labelled Sonstige",
            RESIDUAL_GEOGRAPHY,
            None,
            sonstige,
            None,
            "Residual reporting category; not a 17th federal state.",
        ),
        row(
            "kba_400_registration_regions",
            "Sum of 400 KBA registration-region rows",
            "400 KBA registration regions",
            None,
            district,
            None,
            "Matches the 16-state sum for July 2026; KBA registration regions are not assumed to be administrative districts.",
        ),
        row(
            "bnetza_registered_infrastructure_all_16_states",
            "All published BNetzA equipment and point rows grouped to the 16 states",
            None,
            "16 federal states",
            None,
            charging,
            "BNetzA state view contains all 16 states; no infrastructure Sonstige row exists in this model.",
        ),
        row(
            "benchmark_16_state_comparable_scope",
            "16-state KBA BEV stock divided by BNetzA points in the 16 states",
            "16 federal states",
            "16 federal states",
            states,
            charging,
            "Primary cross-source benchmark; KBA 2026-07-01 and BNetzA 2026-09-30 remain date-mismatched.",
        ),
        row(
            "benchmark_published_national_bev_scope",
            "Published Deutschland KBA BEV stock divided by published BNetzA points",
            NATIONAL_GEOGRAPHY,
            "16 federal states",
            national,
            charging,
            "Secondary benchmark includes 2,829 Sonstige BEVs in the numerator but no corresponding BNetzA state row in the denominator.",
        ),
    ]
    require(len(rows) == 7, "Unexpected reconciliation row count")
    return rows, {"fieldnames": fieldnames, "charging": charging, "national": national, "states": states, "sonstige": sonstige, "district": district}


def rankdata(values: Sequence[float]) -> List[float]:
    indexed = sorted(enumerate(float(value) for value in values), key=lambda pair: pair[1])
    ranks = [0.0] * len(indexed)
    position = 0
    while position < len(indexed):
        end = position + 1
        while end < len(indexed) and indexed[end][1] == indexed[position][1]:
            end += 1
        rank = (position + 1 + end) / 2.0
        for index in range(position, end):
            ranks[indexed[index][0]] = rank
        position = end
    return ranks


def pearson(values_x: Sequence[float], values_y: Sequence[float]) -> Optional[float]:
    if len(values_x) != len(values_y) or len(values_x) < 2:
        return None
    mean_x = statistics.mean(float(value) for value in values_x)
    mean_y = statistics.mean(float(value) for value in values_y)
    numerator = sum((float(x) - mean_x) * (float(y) - mean_y) for x, y in zip(values_x, values_y))
    denominator_x = math.sqrt(sum((float(x) - mean_x) ** 2 for x in values_x))
    denominator_y = math.sqrt(sum((float(y) - mean_y) ** 2 for y in values_y))
    if denominator_x == 0 or denominator_y == 0:
        return None
    return numerator / (denominator_x * denominator_y)


def correlation_pair(rows: Sequence[Mapping[str, Any]], x_field: str, y_field: str) -> Dict[str, Any]:
    x_values = [float(row[x_field]) for row in rows]
    y_values = [float(row[y_field]) for row in rows]
    return {
        "n": len(rows),
        "pearson_r": pearson(x_values, y_values),
        "spearman_r": pearson(rankdata(x_values), rankdata(y_values)),
    }


def build_associations(state_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    large_states = {
        str(row["state_name"])
        for row in sorted(state_rows, key=lambda item: int(item["passenger_car_stock"]), reverse=True)[:3]
    }
    reduced_rows = [row for row in state_rows if str(row["state_name"]) not in large_states]
    specifications = (
        (
            "BEV stock vs total charging points",
            "bev_stock",
            "charging_point_count",
            "absolute registered BEV stock",
            "absolute populated charging-point slots",
            "Absolute-size association can be driven by state scale and does not measure charger adequacy.",
        ),
        (
            "BEV penetration vs fast-point share",
            "bev_penetration_pct",
            "fast_point_share_pct",
            "BEV stock / total passenger cars",
            "fast points / all charging points",
            "Ratio-versus-ratio association; denominators and declared-power mix can drive the pattern.",
        ),
        (
            "BEV stock share vs charging-point share",
            "bev_stock_share_of_16_state_bev_stock_pct",
            "share_of_national_registered_charging_points_pct",
            "state BEV stock / 16-state BEV stock",
            "state points / all registered points",
            "Compositional comparison with fixed national denominators; closely related to absolute scale.",
        ),
        (
            "Total passenger cars vs total charging points",
            "passenger_car_stock",
            "charging_point_count",
            "absolute registered passenger-car stock",
            "absolute populated charging-point slots",
            "Absolute-size association can be driven by state scale; it is not a supply or demand test.",
        ),
        (
            "BEVs per point vs fast-point share",
            "bevs_per_registered_charging_point",
            "fast_point_share_pct",
            "BEV stock / registered charging points",
            "fast points / all charging points",
            "Exploratory denominator-driven comparison; both dates and source coverage limitations matter.",
        ),
    )
    rows: List[Dict[str, Any]] = []
    for name, x_field, y_field, x_basis, y_basis, interpretation in specifications:
        full = correlation_pair(state_rows, x_field, y_field)
        reduced = correlation_pair(reduced_rows, x_field, y_field)
        loo_pearson: List[float] = []
        loo_spearman: List[float] = []
        for index in range(len(state_rows)):
            subset = list(state_rows[:index]) + list(state_rows[index + 1 :])
            values = correlation_pair(subset, x_field, y_field)
            if values["pearson_r"] is not None:
                loo_pearson.append(float(values["pearson_r"]))
            if values["spearman_r"] is not None:
                loo_spearman.append(float(values["spearman_r"]))
        rows.append(
            {
                "association": name,
                "x_metric": x_field,
                "y_metric": y_field,
                "x_basis": x_basis,
                "y_basis": y_basis,
                "n_all_16_states": full["n"],
                "pearson_r_all_16": full["pearson_r"],
                "spearman_r_all_16": full["spearman_r"],
                "large_state_exclusion_rule": "Exclude the three states with the largest passenger-car stock",
                "excluded_large_states": "; ".join(sorted(large_states)),
                "n_excluding_large_states": reduced["n"],
                "pearson_r_excluding_large_states": reduced["pearson_r"],
                "spearman_r_excluding_large_states": reduced["spearman_r"],
                "pearson_leave_one_out_min": min(loo_pearson) if loo_pearson else None,
                "pearson_leave_one_out_max": max(loo_pearson) if loo_pearson else None,
                "spearman_leave_one_out_min": min(loo_spearman) if loo_spearman else None,
                "spearman_leave_one_out_max": max(loo_spearman) if loo_spearman else None,
                "status": "EXPLORATORY",
                "interpretation": interpretation,
                "statistical_safeguard": "Descriptive Pearson/Spearman only; n=16; no significance test or causal inference.",
            }
        )
    return rows


def select_extreme(rows: Sequence[Mapping[str, Any]], field: str, reverse: bool) -> Mapping[str, Any]:
    ordered = sorted(rows, key=lambda row: float(row[field]), reverse=reverse)
    require(ordered and ordered[0][field] is not None, f"Cannot rank empty/null metric: {field}")
    return ordered[0]


def build_outlier_summary(state_rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    largest_gap = sorted(
        state_rows,
        key=lambda row: abs(float(row["bev_stock_share_minus_charging_point_share_pp"])),
        reverse=True,
    )
    return {
        "largest_bev_stock": select_extreme(state_rows, "bev_stock", True),
        "highest_bev_penetration": select_extreme(state_rows, "bev_penetration_pct", True),
        "largest_charging_point_stock": select_extreme(state_rows, "charging_point_count", True),
        "highest_fast_point_share": select_extreme(state_rows, "fast_point_share_pct", True),
        "highest_ge150_point_share": select_extreme(state_rows, "points_ge_150_share_pct", True),
        "lowest_bevs_per_point": select_extreme(state_rows, "bevs_per_registered_charging_point", False),
        "highest_bevs_per_point": select_extreme(state_rows, "bevs_per_registered_charging_point", True),
        "lowest_fast_per_1000_bevs": select_extreme(state_rows, "fast_points_per_1000_bevs", False),
        "highest_fast_per_1000_bevs": select_extreme(state_rows, "fast_points_per_1000_bevs", True),
        "largest_share_gaps": largest_gap[:5],
        "smallest_point_denominators": sorted(state_rows, key=lambda row: int(row["charging_point_count"]))[:5],
        "largest_passenger_car_states": sorted(state_rows, key=lambda row: int(row["passenger_car_stock"]), reverse=True)[:3],
    }


def render_report(
    database: Path,
    database_before_sha256: str,
    database_after_sha256: str,
    fingerprints: Sequence[Mapping[str, Any]],
    database_contract: Mapping[str, Any],
    vehicle_checks: Mapping[str, Any],
    charging_checks: Mapping[str, Any],
    reconciliation_rows: Sequence[Mapping[str, Any]],
    state_rows: Sequence[Mapping[str, Any]],
    associations: Sequence[Mapping[str, Any]],
    outliers: Mapping[str, Any],
) -> str:
    national = vehicle_checks["national"]
    states = vehicle_checks["sixteen_state_sum"]
    sonstige = vehicle_checks["sonstige"]
    district = vehicle_checks["four_hundred_region_sum"]
    charging = charging_checks["totals"]
    recon_by_scope = {str(row["scope"]): row for row in reconciliation_rows}
    comparable = recon_by_scope["benchmark_16_state_comparable_scope"]
    published = recon_by_scope["benchmark_published_national_bev_scope"]

    largest_bev = outliers["largest_bev_stock"]
    highest_pen = outliers["highest_bev_penetration"]
    largest_points = outliers["largest_charging_point_stock"]
    highest_fast = outliers["highest_fast_point_share"]
    highest_ge150 = outliers["highest_ge150_point_share"]

    lines: List[str] = [
        "# Batch 16 — state-level EV stock versus charging infrastructure",
        "",
        "**Batch status: PASS**",
        "",
        "This report is a deterministic, read-only comparison of the 16 German federal states. It uses KBA FZ 27.2 passenger-car stock as of **2026-07-01** and the BNetzA Ladesäulenregister as of **2026-09-30**. The dates are intentionally visible because every cross-source KPI is a date-mismatched descriptive comparison.",
        "",
        "## 1. Executive summary",
        "",
        f"**OBSERVED:** The BNetzA snapshot contains {fmt_int(charging['equipment_count'])} registered equipment records and {fmt_int(charging['charging_point_count'])} populated charging-point slots across the 16 states. The declared-power parser classifies {fmt_int(charging['normal_charging_point_count'])} points at or below 22 kW, {fmt_int(charging['fast_charging_point_count'])} above 22 kW, {fmt_int(charging['points_ge_150_kw'])} at or above 150 kW, and {fmt_int(charging['points_ge_350_kw'])} at or above 350 kW. Declared equipment nominal power is {fmt_num(charging['equipment_nominal_power_mw'], 4)} MW.",
        "",
        f"Equipment statuses are preserved without filtering: {fmt_int(sum(int(row['equipment_in_operation']) for row in state_rows))} records are `In Betrieb`, {fmt_int(sum(int(row['equipment_in_maintenance']) for row in state_rows))} are `In Wartung`, and {fmt_int(sum(int(row['equipment_other_status']) for row in state_rows))} have another or NULL status.",
        "",
        f"**OBSERVED:** The July KBA state-level total is {fmt_int(national['bev_stock'])} BEVs, {fmt_int(national['phev_stock'])} PHEVs, and {fmt_int(national['passenger_car_stock'])} passenger cars. The 16 states contain {fmt_int(states['bev_stock'])} BEVs and {fmt_int(states['phev_stock'])} PHEVs; `Sonstige` contains {fmt_int(sonstige['bev_stock'])} BEVs and {fmt_int(sonstige['phev_stock'])} PHEVs. The 400 KBA registration-region totals equal the 16-state sums.",
        "",
        f"**OBSERVED:** The primary 16-state benchmark is {fmt_ratio(comparable['bevs_per_registered_charging_point'])} registered BEVs per registered charging point, or {fmt_ratio(comparable['registered_charging_points_per_1000_bevs'])} points per 1,000 BEVs. Using the published `Deutschland` BEV numerator instead gives {fmt_ratio(published['bevs_per_registered_charging_point'])} BEVs per point because it includes {fmt_int(sonstige['bev_stock'])} `Sonstige` BEVs without adding an infrastructure row.",
        "",
        f"**OBSERVED:** {largest_bev['state_name']} has the largest absolute BEV stock ({fmt_int(largest_bev['bev_stock'])}); {highest_pen['state_name']} has the highest BEV penetration ({fmt_pct(highest_pen['bev_penetration_pct'])}); and {largest_points['state_name']} has the largest point stock ({fmt_int(largest_points['charging_point_count'])}). {highest_fast['state_name']} has the highest fast-point share ({fmt_pct(highest_fast['fast_point_share_pct'])}), while {highest_ge150['state_name']} has the highest >=150 kW point share ({fmt_pct(highest_ge150['points_ge_150_share_pct'])}).",
        "",
        "These are descriptive counts, shares and ratios. They do not establish infrastructure adequacy, shortage, surplus, demand, utilization, accessibility, or causality.",
        "",
        "## 2. Review of Batch 15 findings relevant to Batch 16",
        "",
        "Batch 15 established a compatible KBA baseline rather than a blocker for this state-level comparison:",
        "",
        f"- **National stock:** January–July 2026 national BEV stock increased by 330,787 ({fmt_pct(pct(330_787, 2_034_260))}) to 2,365,047; PHEV stock increased by 103,905 ({fmt_pct(pct(103_905, 1_122_958))}) to 1,226,863. The national combined plug-in share reached 7.23%.",
        f"- **Regional stock:** Nordrhein-Westfalen had the largest July BEV stock (527,377); Hamburg had the highest BEV penetration (5.97%); Mecklenburg-Vorpommern had the highest January–July state BEV growth (20.98%). These rankings distinguish absolute scale from percentage indicators.",
        "- **Ownership:** Batch 15 found that private ownership represented 61.49% of observed-owner BEV stock and 54.31% of observed-owner PHEV stock nationally in July. Published totals retain unknown or unallocated owner residuals; district ownership was not inferred.",
        "- **Completeness and limits:** FZ 27.15 contains 400 stable KBA registration-region codes per snapshot and the 16-state sum reconciles to the 400-region table. The `Deutschland` row includes `Sonstige`; it must not be added to the state or district rows. The shared Trier registration region `07211` remains one row, with no allocation.",
        "- **Validated versus exploratory:** Batch 15 validated stock, penetration, same-grain reconciliation and source-grain ownership arithmetic. Percentage-growth thresholds, ownership composition and alternative postcode/municipality analyses remain descriptive or exploratory. No BNetzA charging join was present in Batch 15, so this batch performs that cross-source comparison with both dates explicit.",
        "",
        "The residual and grain differences are manageable because Batch 16 keeps `Deutschland`, the 16 states, `Sonstige`, and the 400 KBA registration-region scope separate. No BBSR integration or district crosswalk is needed for this batch.",
        "",
        "## 3. Data sources and analytical grain",
        "",
        *markdown_table(
            ["Source/object", "Use", "Grain", "Reference date", "Controls"],
            [
                ["`core.kba_state_fuel_stock`", "BEV, PHEV and passenger-car stock", "FZ 27.2 state/residual/national × fuel type", KBA_REFERENCE_DATE, "Six mutually exclusive fuel rows form passenger-car total; `darunter Plug-in` is nested detail."],
                ["`core.kba_district_ev_stock`", "Independent KBA reconciliation", "400 KBA registration regions", KBA_REFERENCE_DATE, "One row per code; no BBSR equivalence or Trier allocation."],
                ["`analytics.charging_by_state`", "Validated equipment/declared/populated point baseline", "16 federal states", INFRASTRUCTURE_REFERENCE_DATE, "Existing source-aware `(source_id, excel_row)` point join."],
                ["`core.charging_equipment`", "Equipment, status and nominal power", "BNetzA equipment row × state", INFRASTRUCTURE_REFERENCE_DATE, "Equipment power summed before any point-level aggregation."],
                ["`core.charging_point`", "Point counts and power bands", "Populated point slot × equipment", INFRASTRUCTURE_REFERENCE_DATE, "Maximum parsed token per point; no connector multiplication."],
            ],
        ),
        "",
        "The primary join is one validated charging row per state joined to one validated KBA stock row per state. Raw equipment, raw points and KBA fuel rows are not joined together before aggregation.",
        "",
        "## 4. National and 16-state reconciliation",
        "",
        *markdown_table(
            ["Scope", "Passenger cars", "BEV", "PHEV", "Equipment", "Points", "BEVs/point", "Interpretation"],
            [
                ["Published KBA `Deutschland`", fmt_int(national["passenger_car_stock"]), fmt_int(national["bev_stock"]), fmt_int(national["phev_stock"]), "—", "—", "—", "Official national KBA row."],
                ["16-state KBA sum", fmt_int(states["passenger_car_stock"]), fmt_int(states["bev_stock"]), fmt_int(states["phev_stock"]), "—", "—", "—", "Comparable vehicle scope for the state infrastructure rows."],
                ["KBA `Sonstige`", fmt_int(sonstige["passenger_car_stock"]), fmt_int(sonstige["bev_stock"]), fmt_int(sonstige["phev_stock"]), "—", "—", "—", "Residual reporting category; not a state."],
                ["400 KBA regions", fmt_int(district["passenger_car_stock"]), fmt_int(district["bev_stock"]), fmt_int(district["phev_stock"]), "—", "—", "—", "Matches the 16-state sum exactly."],
                ["BNetzA all 16 states", "—", "—", "—", fmt_int(charging["equipment_count"]), fmt_int(charging["charging_point_count"]), "—", "All registered infrastructure in the current state view."],
                ["16-state comparable benchmark", "—", fmt_int(states["bev_stock"]), "—", fmt_int(charging["equipment_count"]), fmt_int(charging["charging_point_count"]), fmt_ratio(comparable["bevs_per_registered_charging_point"]), "Use for state-ratio recomputation from summed numerators/denominators."],
                ["Published-national benchmark", "—", fmt_int(national["bev_stock"]), "—", fmt_int(charging["equipment_count"]), fmt_int(charging["charging_point_count"]), fmt_ratio(published["bevs_per_registered_charging_point"]), "Includes `Sonstige` BEVs but no separate infrastructure row."],
            ],
        ),
        "",
        f"The reconciliation is exact: `Deutschland = 16 states + Sonstige` for passenger cars, BEVs and PHEVs; the 400-region KBA total equals the 16-state sum; and the BNetzA state totals equal {fmt_int(EXPECTED['equipment'])} equipment, {fmt_int(EXPECTED['declared_points'])} declared points, {fmt_int(EXPECTED['charging_points'])} populated points and {fmt_num(EXPECTED['nominal_power_mw'], 4)} MW. `Deutschland` and `Sonstige` are reporting rows, not additional independent federal states.",
        "",
        "The two national benchmarks differ only in the KBA numerator scope here: the published-national numerator includes 2,829 `Sonstige` BEVs. A national BEV total must not be compared with a sum or average of state-level ratios without first choosing the scope and recomputing from summed counts. State-level BEV-per-point ratios were not averaged to obtain either benchmark.",
        "",
        "## 5. Complete 16-state KPI comparison",
        "",
        "### Vehicle stock and penetration",
        "",
        *markdown_table(
            ["State", "Passenger cars", "BEV", "PHEV", "BEV penetration", "PHEV penetration", "Combined penetration", "BEV share of 16-state stock"],
            [
                [row["state_name"], fmt_int(row["passenger_car_stock"]), fmt_int(row["bev_stock"]), fmt_int(row["phev_stock"]), fmt_pct(row["bev_penetration_pct"]), fmt_pct(row["phev_penetration_pct"]), fmt_pct(row["combined_plugin_penetration_pct"]), fmt_pct(row["bev_stock_share_of_16_state_bev_stock_pct"])]
                for row in state_rows
            ],
        ),
        "",
        "### Infrastructure stock and power mix",
        "",
        *markdown_table(
            ["State", "Equipment", "Declared points", "Populated points", "Normal <=22 kW", "Fast >22 kW", "Fast share", ">=150 kW", ">=150 share", ">=350 kW", ">=350 share", "Nominal MW", "Point share"],
            [
                [row["state_name"], fmt_int(row["equipment_count"]), fmt_int(row["declared_charging_point_count"]), fmt_int(row["charging_point_count"]), fmt_int(row["normal_charging_point_count"]), fmt_int(row["fast_charging_point_count"]), fmt_pct(row["fast_point_share_pct"]), fmt_int(row["points_ge_150_kw"]), fmt_pct(row["points_ge_150_share_pct"]), fmt_int(row["points_ge_350_kw"]), fmt_pct(row["points_ge_350_share_pct"]), fmt_num(row["equipment_nominal_power_mw"], 4), fmt_pct(row["share_of_national_registered_charging_points_pct"])]
                for row in state_rows
            ],
        ),
        "",
        "### Cross-dataset indicators",
        "",
        *markdown_table(
            ["State", "BEVs/point", "Points/1,000 BEVs", "Fast/1,000 BEVs", ">=150/1,000 BEVs", ">=350/1,000 BEVs", "BEV share − point share", "BEV+PHEV/point"],
            [
                [row["state_name"], fmt_ratio(row["bevs_per_registered_charging_point"]), fmt_ratio(row["registered_charging_points_per_1000_bevs"]), fmt_ratio(row["fast_points_per_1000_bevs"]), fmt_ratio(row["points_ge_150_per_1000_bevs"]), fmt_ratio(row["points_ge_350_per_1000_bevs"]), fmt_pp(row["bev_stock_share_minus_charging_point_share_pp"]), fmt_ratio(row["combined_plugin_per_registered_charging_point"])]
                for row in state_rows
            ],
        ),
        "",
        "The BEV-only ratios use July 2026 registered BEVs as the denominator. The optional combined plug-in ratio uses BEV + PHEV in the numerator and is not mixed into the BEV-only rankings. All ratio calculations use safe zero-denominator handling; no state has a zero BEV or point denominator in this snapshot.",
        "",
        "## 6. BEV stock versus charging-point comparison",
        "",
        "State size and state share are different views. The following states have the largest absolute BEV stock and charging-point stock:",
        "",
        *markdown_table(
            ["Rank", "State", "BEVs", "BEV penetration", "Points", "Point share", "BEVs/point", "Share gap"],
            [
                [index, row["state_name"], fmt_int(row["bev_stock"]), fmt_pct(row["bev_penetration_pct"]), fmt_int(row["charging_point_count"]), fmt_pct(row["share_of_national_registered_charging_points_pct"]), fmt_ratio(row["bevs_per_registered_charging_point"]), fmt_pp(row["bev_stock_share_minus_charging_point_share_pp"])]
                for index, row in enumerate(sorted(state_rows, key=lambda item: int(item["bev_stock"]), reverse=True)[:5], 1)
            ],
        ),
        "",
        "A positive share gap means the state's share of 16-state BEVs is larger than its share of registered points; a negative gap means the reverse. This is a compositional comparison, not a shortage/surplus measure.",
        "",
        "## 7. Fast and HPC infrastructure comparison",
        "",
        *markdown_table(
            ["Metric", "State", "Underlying BEVs", "Passenger cars", "Points", "Fast points", ">=150 kW points", ">=350 kW points", "Reported value"],
            [
                ["Largest point stock", largest_points["state_name"], fmt_int(largest_points["bev_stock"]), fmt_int(largest_points["passenger_car_stock"]), fmt_int(largest_points["charging_point_count"]), fmt_int(largest_points["fast_charging_point_count"]), fmt_int(largest_points["points_ge_150_kw"]), fmt_int(largest_points["points_ge_350_kw"]), fmt_int(largest_points["charging_point_count"])],
                ["Highest fast-point share", highest_fast["state_name"], fmt_int(highest_fast["bev_stock"]), fmt_int(highest_fast["passenger_car_stock"]), fmt_int(highest_fast["charging_point_count"]), fmt_int(highest_fast["fast_charging_point_count"]), fmt_int(highest_fast["points_ge_150_kw"]), fmt_int(highest_fast["points_ge_350_kw"]), fmt_pct(highest_fast["fast_point_share_pct"])],
                ["Highest >=150 kW share", highest_ge150["state_name"], fmt_int(highest_ge150["bev_stock"]), fmt_int(highest_ge150["passenger_car_stock"]), fmt_int(highest_ge150["charging_point_count"]), fmt_int(highest_ge150["fast_charging_point_count"]), fmt_int(highest_ge150["points_ge_150_kw"]), fmt_int(highest_ge150["points_ge_350_kw"]), fmt_pct(highest_ge150["points_ge_150_share_pct"])],
            ],
        ),
        "",
        "Fast and >=150 kW are nested declared-power classifications. A higher fast or HPC share does not show that points are available, used, reliable, simultaneously deliverable, or suitable for every vehicle.",
        "",
        "## 8. Geographic differences, outliers and denominator stability",
        "",
        *markdown_table(
            ["Comparison", "State", "Underlying counts", "Value"],
            [
                ["Largest absolute BEV stock", largest_bev["state_name"], f"{fmt_int(largest_bev['bev_stock'])} BEVs; {fmt_int(largest_bev['passenger_car_stock'])} passenger cars", fmt_int(largest_bev["bev_stock"])],
                ["Highest BEV penetration", highest_pen["state_name"], f"{fmt_int(highest_pen['bev_stock'])} BEVs / {fmt_int(highest_pen['passenger_car_stock'])} passenger cars", fmt_pct(highest_pen["bev_penetration_pct"])],
                ["Lowest BEVs per point", outliers["lowest_bevs_per_point"]["state_name"], f"{fmt_int(outliers['lowest_bevs_per_point']['bev_stock'])} BEVs / {fmt_int(outliers['lowest_bevs_per_point']['charging_point_count'])} points", fmt_ratio(outliers["lowest_bevs_per_point"]["bevs_per_registered_charging_point"])],
                ["Highest BEVs per point", outliers["highest_bevs_per_point"]["state_name"], f"{fmt_int(outliers['highest_bevs_per_point']['bev_stock'])} BEVs / {fmt_int(outliers['highest_bevs_per_point']['charging_point_count'])} points", fmt_ratio(outliers["highest_bevs_per_point"]["bevs_per_registered_charging_point"])],
                ["Lowest fast points per 1,000 BEVs", outliers["lowest_fast_per_1000_bevs"]["state_name"], f"{fmt_int(outliers['lowest_fast_per_1000_bevs']['fast_charging_point_count'])} fast points / {fmt_int(outliers['lowest_fast_per_1000_bevs']['bev_stock'])} BEVs", fmt_ratio(outliers["lowest_fast_per_1000_bevs"]["fast_points_per_1000_bevs"])],
                ["Highest fast points per 1,000 BEVs", outliers["highest_fast_per_1000_bevs"]["state_name"], f"{fmt_int(outliers['highest_fast_per_1000_bevs']['fast_charging_point_count'])} fast points / {fmt_int(outliers['highest_fast_per_1000_bevs']['bev_stock'])} BEVs", fmt_ratio(outliers["highest_fast_per_1000_bevs"]["fast_points_per_1000_bevs"])],
            ],
        ),
        "",
        "### Largest BEV-share versus charging-point-share differences",
        "",
        *markdown_table(
            ["Rank", "State", "BEV stock", "Points", "BEV share of 16-state stock", "Point share", "Difference"],
            [
                [index, row["state_name"], fmt_int(row["bev_stock"]), fmt_int(row["charging_point_count"]), fmt_pct(row["bev_stock_share_of_16_state_bev_stock_pct"]), fmt_pct(row["share_of_national_registered_charging_points_pct"]), fmt_pp(row["bev_stock_share_minus_charging_point_share_pp"])]
                for index, row in enumerate(outliers["largest_share_gaps"], 1)
            ],
        ),
        "",
        "### Small point denominators",
        "",
        *markdown_table(
            ["State", "Points", "BEVs", "Fast points", "BEVs/point", "Fast/1,000 BEVs", "Interpretation"],
            [
                [row["state_name"], fmt_int(row["charging_point_count"]), fmt_int(row["bev_stock"]), fmt_int(row["fast_charging_point_count"]), fmt_ratio(row["bevs_per_registered_charging_point"]), fmt_ratio(row["fast_points_per_1000_bevs"]), "Small denominator; inspect counts with the ratio"]
                for row in outliers["smallest_point_denominators"]
            ],
        ),
        "",
        "Small state point counts make shares and per-1,000 ratios more sensitive to a small number of points. That is a stability warning, not evidence that a state is adequately or inadequately supplied. State averages also conceal urban/rural and district-level variation.",
        "",
        "## 9. Statistical associations",
        "",
        "The following Pearson and Spearman correlations are descriptive summaries of 16 states. No p-values or significance claims are used. The sensitivity columns exclude the three states with the largest passenger-car stock (Nordrhein-Westfalen, Bayern and Baden-Württemberg); leave-one-out ranges show how much one state can affect the result.",
        "",
        *markdown_table(
            ["Association", "n", "Pearson", "Spearman", "Pearson excl. 3 large", "Spearman excl. 3 large", "Leave-one-out Pearson", "Interpretation"],
            [
                [row["association"], row["n_all_16_states"], fmt_num(row["pearson_r_all_16"], 3), fmt_num(row["spearman_r_all_16"], 3), fmt_num(row["pearson_r_excluding_large_states"], 3), fmt_num(row["spearman_r_excluding_large_states"], 3), f"{fmt_num(row['pearson_leave_one_out_min'], 3)} to {fmt_num(row['pearson_leave_one_out_max'], 3)}", row["interpretation"]]
                for row in associations
            ],
        ),
        "",
        "**SUPPORTED ASSOCIATION:** Absolute BEV stock and absolute charging-point count move together descriptively, but the strength of that relationship must be read as a state-size association. The stock-share versus point-share comparison has fixed denominators and is therefore compositional rather than an independent test. Passenger-car stock versus point count has the same scale effect. Penetration, BEVs-per-point and fast-share correlations compare ratios with different denominators and should not be treated as causal drivers.",
        "",
        "**PLAUSIBLE HYPOTHESIS:** State size, urban form, fleet composition, public-sector or commercial siting and travel patterns could contribute to the observed differences. The available 16-state cross-section cannot identify which mechanism explains them.",
        "",
        "## 10. Limitations and interpretation safeguards",
        "",
        "- **OBSERVED:** KBA registered passenger-car stock and BNetzA registered charging infrastructure reconcile at their respective source grains and reference dates.",
        "- **SUPPORTED ASSOCIATION:** Correlations describe co-movement across 16 states only; they do not establish a causal driver or statistical generalization.",
        "- **PLAUSIBLE HYPOTHESIS:** Large states can dominate absolute totals, while denominators and composition can change ratios and shares. This is a reason to report both counts and normalized measures.",
        "- **NOT TESTABLE WITH AVAILABLE DATA:** Charging demand, sessions, utilization, queues, reliability, real-time availability, traffic flow, energy delivery, population-adjusted need, accessibility, and causal infrastructure effects.",
        "",
        "Additional safeguards:",
        "",
        "- BNetzA infrastructure is dated 2026-09-30 and KBA stock is dated 2026-07-01. The cross-source KPIs are not contemporaneous.",
        "- The BNetzA register is a published register, not a complete census of every public charging asset.",
        "- BEV stock is registered stock, not charging demand, sales or registrations during the interval.",
        "- One charging point does not imply a fixed amount of simultaneous usable power; nominal equipment power is not simultaneously deliverable power.",
        "- The KBA state table uses passenger-car counts. PHEV is not added to `Hybrid insgesamt` when reconstructing total passenger cars.",
        "- State comparisons are not district-level geographic harmonization. No BBSR classification, Trier allocation or KBA district crosswalk is used here.",
        "- January/April/July KBA trends from Batch 15 are background only. This report does not repeat September infrastructure across those dates to claim infrastructure growth.",
        "",
        "## 11. KPI evaluation for Tableau",
        "",
        "The statuses below apply to the state-level candidate KPI as used in this batch. `VALIDATED` means the source fields, formula, grain and reconciliation passed the local checks; it does not mean the source is exhaustive. Cross-source ratios are `EXPLORATORY` because the snapshot dates differ and the register is not a census.",
        "",
        *markdown_table(
            ["KPI", "Status", "Formula / numerator / denominator", "Unit", "Source", "Grain", "Reference dates", "Interpretation", "Known limitation", "Tableau suitability"],
            [
                ["BEV stock", "VALIDATED", "SUM `Elektro (BEV)` passenger cars", "Registered vehicles", "KBA FZ 27.2 / `core.kba_state_fuel_stock`", "State", KBA_REFERENCE_DATE, "Observed registered BEV stock", "Not sales, demand or utilization", "Recommended primary KPI"],
                ["PHEV stock", "VALIDATED", "SUM `darunter Plug-in` passenger cars", "Registered vehicles", "KBA FZ 27.2 / `core.kba_state_fuel_stock`", "State", KBA_REFERENCE_DATE, "Observed registered PHEV stock", "Nested detail under Hybrid insgesamt", "Recommended supporting KPI"],
                ["Total passenger cars", "VALIDATED", "Sum six mutually exclusive FZ 27.2 fuel rows", "Registered vehicles", "KBA FZ 27.2 / `core.kba_state_fuel_stock`", "State", KBA_REFERENCE_DATE, "Denominator for penetration", "Must not add PHEV to Hybrid insgesamt", "Recommended denominator"],
                ["BEV penetration", "VALIDATED", "BEV stock / total passenger cars", "%", "KBA FZ 27.2", "State", KBA_REFERENCE_DATE, "BEV share of registered passenger cars", "Stock share, not demand", "Recommended primary KPI"],
                ["PHEV penetration", "VALIDATED", "PHEV stock / total passenger cars", "%", "KBA FZ 27.2", "State", KBA_REFERENCE_DATE, "PHEV share of registered passenger cars", "Stock share, not demand", "Recommended supporting KPI"],
                ["Combined plug-in penetration", "VALIDATED", "(BEV + PHEV) / total passenger cars", "%", "KBA FZ 27.2", "State", KBA_REFERENCE_DATE, "Combined mutually exclusive plug-in stock share", "Do not substitute Hybrid insgesamt", "Recommended supporting KPI"],
                ["Charging equipment count", "VALIDATED", "COUNT equipment rows", "Equipment records", "BNetzA / `core.charging_equipment`", "State", INFRASTRUCTURE_REFERENCE_DATE, "Published equipment stock", "One equipment row may contain multiple points; register not exhaustive", "Recommended context KPI"],
                ["Charging-point count", "VALIDATED", "COUNT populated point slots", "Point slots", "BNetzA / `core.charging_point`", "State", INFRASTRUCTURE_REFERENCE_DATE, "Published point-slot stock", "Not connector count, capacity or availability", "Recommended primary infrastructure KPI"],
                ["Fast and HPC counts/shares", "VALIDATED", "Point count by max declared power: >22, >=150, >=350 kW; denominator all points", "Points / %", "BNetzA / `connector_power_raw`", "State", INFRASTRUCTURE_REFERENCE_DATE, "Declared-power mix", "Not utilization or simultaneous delivery", "Recommended mix KPI with definitions visible"],
                ["Nominal equipment power", "VALIDATED", "SUM equipment nominal kW / 1,000", "MW", "BNetzA / `core.charging_equipment`", "State", INFRASTRUCTURE_REFERENCE_DATE, "Declared equipment nominal power", "Not energy delivery or grid capacity", "Context only"],
                ["BEVs per registered point", "EXPLORATORY", "BEV stock / populated charging points", "BEVs per point", "KBA + BNetzA", "State", f"KBA {KBA_REFERENCE_DATE}; BNetzA {INFRASTRUCTURE_REFERENCE_DATE}", "Date-mismatched stock-to-register ratio", "Register coverage and dates differ; not adequacy/accessibility", "Use only as clearly labelled exploratory view"],
                ["Points per 1,000 BEVs", "EXPLORATORY", "Populated points × 1,000 / BEV stock", "Points per 1,000 BEVs", "KBA + BNetzA", "State", f"KBA {KBA_REFERENCE_DATE}; BNetzA {INFRASTRUCTURE_REFERENCE_DATE}", "Inverse date-mismatched ratio", "Not a service standard or adequacy measure", "Exploratory context only"],
                ["Fast/HPC points per 1,000 BEVs", "EXPLORATORY", "Fast or threshold points × 1,000 / BEV stock", "Points per 1,000 BEVs", "KBA + BNetzA", "State", f"KBA {KBA_REFERENCE_DATE}; BNetzA {INFRASTRUCTURE_REFERENCE_DATE}", "Power-mix ratio relative to registered BEVs", "Denominator/date/register limitations", "Exploratory context only"],
                ["BEV-share minus point-share gap", "EXPLORATORY", "BEV share of 16-state stock − point share of registered points", "Percentage points", "KBA + BNetzA", "State", f"KBA {KBA_REFERENCE_DATE}; BNetzA {INFRASTRUCTURE_REFERENCE_DATE}", "Compositional allocation difference", "Not a shortage/surplus indicator", "Useful comparison annotation, not standalone KPI"],
                ["State correlations", "EXPLORATORY", "Pearson/Spearman across 16 state rows", "Correlation coefficient", "KBA + BNetzA", "16-state cross-section", f"KBA {KBA_REFERENCE_DATE}; BNetzA {INFRASTRUCTURE_REFERENCE_DATE}", "Descriptive association", "Small n, scale/denominator effects, no causality", "Analyst diagnostic; not a headline tile"],
                ["Adequacy, shortage or surplus", "UNSUPPORTED", "No defensible numerator/denominator from current sources", "Not defined", "No sessions, demand, availability or service standard", "Not supported", "Not supported", "Cannot be measured here", "Requires new approved data and a standard", "Do not deploy"],
            ],
        ),
        "",
        "Recommended concise Tableau set: state BEV stock, total passenger cars, BEV penetration, registered charging points, fast-point share/count, >=150 kW count/share and nominal MW as context. If cross-source ratios are shown, expose both reference dates and label them exploratory; do not label any state adequately or inadequately supplied from these ratios alone.",
        "",
        "## 12. Future analytical opportunities",
        "",
        "- Obtain a contemporaneous BNetzA/KBA pair or construct a dated infrastructure panel before presenting temporal coverage trends.",
        "- Add an owner-approved, product-specific geographic bridge only if a compatible KBA administrative geography is required; preserve the no-allocation rule for Trier.",
        "- Evaluate population, employment, traffic, motorway and fleet denominators at compatible dates and geography, with separate validation for each.",
        "- Add charging sessions, energy, availability or utilization data before discussing demand or access.",
        "- Revisit Tableau extracts only after the denominator/date and source-licensing review is complete.",
        "",
        "Batch 17 and any Tableau dashboard implementation remain outside this batch and require owner approval.",
        "",
        "## 13. Validation results",
        "",
        *markdown_table(
            ["Check", "Result"],
            [
                ["DuckDB access", "PASS — opened with `read_only=True`; no DDL/DML issued"],
                ["Database object/schema contract", f"PASS — {len(database_contract['objects'])} required objects and required columns present"],
                ["Source fingerprints", f"PASS — {len(fingerprints)} preserved workbook/reference fingerprints match"],
                ["BNetzA baseline reconciliation", f"PASS — {fmt_int(charging['equipment_count'])} equipment; {fmt_int(charging['charging_point_count'])} points; power bands and {fmt_num(charging['equipment_nominal_power_mw'], 4)} MW match"],
                ["KBA state coverage", "PASS — 16 states × 7 July FZ 27.2 rows; no duplicate or missing state/fuel keys"],
                ["KBA national/residual reconciliation", "PASS — Deutschland = 16 states + Sonstige for passenger cars, BEVs and PHEVs"],
                ["KBA 400-region reconciliation", "PASS — 400 unique KBA codes and totals equal the 16-state sum"],
                ["Vehicle category handling", "PASS — passenger-car total uses six mutually exclusive rows; PHEV is not double-counted in Hybrid insgesamt"],
                ["Charging point integrity", f"PASS — {charging_checks['duplicate_point_identities']} duplicate point identities; {charging_checks['orphan_point_rows']} orphan points; {charging_checks['equipment_point_mismatches']} equipment mismatches"],
                ["Power-band denominator", f"PASS — {fmt_int(charging['points_without_valid_power'])} points without valid parsed maximum; normal + fast + unknown = total"],
                ["State join", "PASS — exactly 16 distinct states; no missing or duplicated state joins"],
                ["Date safeguard", f"PASS — every combined KPI carries KBA {KBA_REFERENCE_DATE} and BNetzA {INFRASTRUCTURE_REFERENCE_DATE}"],
                ["Database byte check", f"PASS — start/end SHA-256 match ({database_before_sha256})"],
                ["Ratio safety", "PASS — NULLIF-equivalent handling; no zero BEV or charging-point denominator"],
                ["Determinism", "PASS — script writes no run timestamp and was checked for identical second-run outputs during Batch 16 validation"],
            ],
        ),
        "",
        "### Source fingerprints",
        "",
        *markdown_table(
            ["Path", "Bytes", "SHA-256", "Result"],
            [[row["path"], fmt_int(row["bytes"]), row["actual_sha256"], "MATCH" if row["match"] else "MISMATCH"] for row in fingerprints],
        ),
        "",
        "## 14. Reproducible outputs and recommended next step",
        "",
        "- [`scripts/16_analyze_state_ev_charging_alignment.py`](../scripts/16_analyze_state_ev_charging_alignment.py)",
        "- [`batch16_state_comparison.csv`](batch16_state_comparison.csv)",
        "- [`batch16_national_reconciliation.csv`](batch16_national_reconciliation.csv)",
        "- [`batch16_state_associations.csv`](batch16_state_associations.csv)",
        "",
        "Run from the repository root:",
        "",
        "```bash",
        ".venv/bin/python scripts/16_analyze_state_ev_charging_alignment.py --json",
        "```",
        "",
        "The recommended next step is owner review of the state-level denominator and date treatment, followed by a decision on whether a same-date infrastructure panel or a product-specific geographic bridge is worth pursuing. Do not treat the current ratios as adequacy measures and do not begin Tableau implementation until those choices are approved.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the read-only Batch 16 state EV/changing alignment analysis")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--json", action="store_true", help="Print a compact JSON completion summary")
    args = parser.parse_args()

    database = resolve_path(args.database)
    report_path = resolve_path(args.report)
    output_dir = resolve_path(args.output_dir)
    require(database.is_file(), f"Missing DuckDB database: {database}")
    database_before_sha256 = sha256(database)
    fingerprints = fingerprint_sources()

    conn = duckdb.connect(str(database), read_only=True)
    try:
        database_contract = validate_database_contract(conn)
        vehicle_rows, vehicle_bundle = load_state_vehicle_stock(conn)
        charging_rows, charging_checks = load_charging_state_metrics(conn)
    finally:
        conn.close()

    database_after_sha256 = sha256(database)
    require(database_after_sha256 == database_before_sha256, "DuckDB file changed during read-only analysis")

    vehicle_checks = vehicle_bundle["checks"]
    state_rows = join_state_metrics(vehicle_rows, charging_rows, vehicle_checks, charging_checks)
    associations = build_associations(state_rows)
    outliers = build_outlier_summary(state_rows)
    reconciliation_rows, reconciliation_bundle = make_reconciliation_rows(vehicle_checks, charging_checks)

    state_fields = [
        "state_name",
        "kba_reference_date",
        "bnetza_reference_date",
        "passenger_car_stock",
        "bev_stock",
        "phev_stock",
        "combined_plugin_stock",
        "bev_penetration_pct",
        "phev_penetration_pct",
        "combined_plugin_penetration_pct",
        "bev_stock_share_of_16_state_bev_stock_pct",
        "equipment_count",
        "declared_charging_point_count",
        "charging_point_count",
        "normal_charging_point_count",
        "fast_charging_point_count",
        "points_ge_150_kw",
        "points_ge_350_kw",
        "points_without_valid_power",
        "fast_point_share_pct",
        "points_ge_150_share_pct",
        "points_ge_350_share_pct",
        "equipment_nominal_power_kw",
        "equipment_nominal_power_mw",
        "share_of_national_registered_charging_points_pct",
        "bevs_per_registered_charging_point",
        "registered_charging_points_per_1000_bevs",
        "fast_points_per_1000_bevs",
        "points_ge_150_per_1000_bevs",
        "points_ge_350_per_1000_bevs",
        "bev_stock_share_minus_charging_point_share_pp",
        "combined_plugin_per_registered_charging_point",
        "registered_charging_points_per_1000_combined_plugins",
        "equipment_in_operation",
        "equipment_in_maintenance",
        "equipment_other_status",
        "equipment_status_labels",
        "cross_source_date_note",
    ]
    reconciliation_fields = list(reconciliation_bundle["fieldnames"])
    association_fields = [
        "association",
        "x_metric",
        "y_metric",
        "x_basis",
        "y_basis",
        "n_all_16_states",
        "pearson_r_all_16",
        "spearman_r_all_16",
        "large_state_exclusion_rule",
        "excluded_large_states",
        "n_excluding_large_states",
        "pearson_r_excluding_large_states",
        "spearman_r_excluding_large_states",
        "pearson_leave_one_out_min",
        "pearson_leave_one_out_max",
        "spearman_leave_one_out_min",
        "spearman_leave_one_out_max",
        "status",
        "interpretation",
        "statistical_safeguard",
    ]

    write_csv(output_dir / "batch16_state_comparison.csv", state_fields, state_rows)
    write_csv(output_dir / "batch16_national_reconciliation.csv", reconciliation_fields, reconciliation_rows)
    write_csv(output_dir / "batch16_state_associations.csv", association_fields, associations)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_report(
            database,
            database_before_sha256,
            database_after_sha256,
            fingerprints,
            database_contract,
            vehicle_checks,
            charging_checks,
            reconciliation_rows,
            state_rows,
            associations,
            outliers,
        ),
        encoding="utf-8",
    )

    output_summary = {
        "status": "PASS",
        "database": relative_label(database),
        "report": relative_label(report_path),
        "outputs": [
            relative_label(output_dir / "batch16_state_comparison.csv"),
            relative_label(output_dir / "batch16_national_reconciliation.csv"),
            relative_label(output_dir / "batch16_state_associations.csv"),
        ],
        "state_rows": len(state_rows),
        "association_rows": len(associations),
        "reconciliation_rows": len(reconciliation_rows),
        "bnetza_totals": charging_checks["totals"],
        "kba_national": vehicle_checks["national"],
        "kba_sixteen_state_sum": vehicle_checks["sixteen_state_sum"],
        "kba_sonstige": vehicle_checks["sonstige"],
        "database_sha256": database_after_sha256,
        "source_fingerprints_match": all(bool(row["match"]) for row in fingerprints),
    }
    if args.json:
        print(json.dumps(output_summary, ensure_ascii=False, indent=2))
    else:
        print("Batch 16 analysis PASS")
        print(f"Report: {output_summary['report']}")
        print(f"State rows: {output_summary['state_rows']}")
        print(f"Database SHA-256: {output_summary['database_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AnalysisError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
