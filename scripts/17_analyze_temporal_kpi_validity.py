#!/usr/bin/env python3
"""Batch 17: assess temporal validity and sensitivity of cross-source EV KPIs.

The analysis is deliberately read-only with respect to DuckDB and the source
artifacts.  It compares KBA passenger-car stock on 2026-07-01 with the
published BNetzA register snapshot on 2026-09-30 and, separately, with a
retrospective September-survivor cohort of equipment commissioned on or before
2026-07-01.  The survivor cohort retains the point rows currently associated
with those September equipment records; it is not a historical July snapshot.

Run from the repository root::

    .venv/bin/python scripts/17_analyze_temporal_kpi_validity.py --json

Only analytical reports and CSV diagnostics are written.  No DuckDB object,
source workbook, reference CSV, or Crosswalk is created or modified.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_REPORT = ROOT / "reports/batch17_temporal_kpi_validity.md"
DEFAULT_OUTPUT_DIR = ROOT / "reports"

INFRASTRUCTURE_SOURCE_ID = "bnetza_charging_2026_09_30"
INFRASTRUCTURE_REFERENCE_DATE = "2026-09-30"
KBA_PRIMARY_SOURCE_ID = "kba_fz27_2026_07"
KBA_PRIMARY_REFERENCE_DATE = "2026-07-01"
KBA_SURVIVOR_CUTOFF_DATE = "2026-07-01"
KBA_SNAPSHOT_SPECS = (
    ("kba_fz27_2026_01", "2026-01-01"),
    ("kba_fz27_2026_04", "2026-04-01"),
    ("kba_fz27_2026_07", "2026-07-01"),
)

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
ALL_KBA_GEOGRAPHIES = (*FEDERAL_STATES, RESIDUAL_GEOGRAPHY, NATIONAL_GEOGRAPHY)

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
    "invalid_power_points": 0,
    "nominal_power_mw": 9_215.4173,
    "national_bev_july": 2_365_047,
    "sixteen_state_bev_july": 2_362_218,
    "sonstige_bev_july": 2_829,
    "national_phev_july": 1_226_863,
    "sixteen_state_phev_july": 1_225_241,
    "sonstige_phev_july": 1_622,
    "district_rows_per_date": 400,
}

# Fingerprints established by earlier batches.  The BBSR workbook and the
# Crosswalk are included because this batch must prove that preserved original
# and reference artifacts stayed unchanged even though neither is queried for
# the temporal comparison.
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


def pct(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return 100.0 * float(numerator) / float(denominator)


def ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator) / float(denominator)


def pct_change(new_value: Optional[float], old_value: Optional[float]) -> Optional[float]:
    if new_value is None or old_value in (None, 0):
        return None
    return 100.0 * (float(new_value) - float(old_value)) / float(old_value)


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


def fmt_signed(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{float(value):+,.{decimals}f}"


def fmt_signed_pct(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{float(value):+,.{decimals}f}%"


def fmt_date(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()[:10]
    return str(value)[:10]


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
        lines.append("| " + " | ".join(str(item).replace("|", "\\|") for item in row) + " |")
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
            "commissioning_date_raw",
            "commissioning_date",
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
    }
    actual_columns: Dict[str, List[str]] = {}
    for qualified, required in required_columns.items():
        actual = set(object_columns(conn, qualified))
        require(required <= actual, f"Missing columns in {qualified}: {sorted(required - actual)}")
        actual_columns[qualified] = sorted(actual)

    return {
        "read_only": True,
        "objects": actual_objects,
        "columns_checked": {key: sorted(value) for key, value in required_columns.items()},
        "point_activation_date_available": False,
        "point_activation_date_note": "No point-level activation-date column exists in core.charging_point.",
    }


def _stock_record(values: Mapping[Tuple[str, str], int], geography: str) -> Dict[str, int]:
    total = sum(values[(geography, fuel)] for fuel in MUTUALLY_EXCLUSIVE_TOTAL_FUELS)
    bev = values[(geography, BEV_FUEL)]
    phev = values[(geography, PHEV_FUEL)]
    hybrid_total = values[(geography, "Hybrid insgesamt")]
    require(hybrid_total >= phev, f"PHEV exceeds Hybrid insgesamt for {geography}")
    require(bev + phev <= total, f"BEV/PHEV exceeds total passenger cars for {geography}")
    return {
        "passenger_car_stock": total,
        "bev_stock": bev,
        "phev_stock": phev,
        "combined_plugin_stock": bev + phev,
    }


def load_kba_snapshot(
    conn: duckdb.DuckDBPyConnection,
    source_id: str,
    reference_date: str,
    validate_july_expected: bool = False,
) -> Dict[str, Any]:
    raw_rows = query_dicts(
        conn,
        """
        SELECT state_name, fuel_type, passenger_cars
        FROM core.kba_state_fuel_stock
        WHERE source_id = ? AND reference_date = CAST(? AS DATE)
        ORDER BY state_name, fuel_type
        """,
        [source_id, reference_date],
    )
    expected_fuels = set(MUTUALLY_EXCLUSIVE_TOTAL_FUELS) | {PHEV_FUEL}
    require(len(raw_rows) == 18 * 7, f"Expected 126 KBA rows for {reference_date}, found {len(raw_rows)}")
    values: Dict[Tuple[str, str], int] = {}
    for row in raw_rows:
        geography = str(row["state_name"])
        fuel = str(row["fuel_type"])
        key = (geography, fuel)
        require(geography in ALL_KBA_GEOGRAPHIES, f"Unexpected KBA geography: {geography}")
        require(fuel in expected_fuels, f"Unexpected KBA fuel label: {fuel}")
        require(key not in values, f"Duplicate KBA state/fuel row: {key}")
        require(row["passenger_cars"] is not None, f"NULL KBA stock value: {key}")
        value = int(row["passenger_cars"])
        require(value >= 0, f"Negative KBA stock value: {key}")
        values[key] = value

    by_geography = {
        geography: _stock_record(values, geography) for geography in ALL_KBA_GEOGRAPHIES
    }
    for geography in ALL_KBA_GEOGRAPHIES:
        fuels = {fuel for geo, fuel in values if geo == geography}
        require(fuels == expected_fuels, f"Incomplete KBA rows for {geography}: {sorted(fuels)}")

    state_sum = {
        field: sum(by_geography[state][field] for state in FEDERAL_STATES)
        for field in ("passenger_car_stock", "bev_stock", "phev_stock", "combined_plugin_stock")
    }
    national = by_geography[NATIONAL_GEOGRAPHY]
    sonstige = by_geography[RESIDUAL_GEOGRAPHY]
    for field in ("passenger_car_stock", "bev_stock", "phev_stock", "combined_plugin_stock"):
        require(
            national[field] == state_sum[field] + sonstige[field],
            f"KBA Deutschland != 16 states + Sonstige for {reference_date}, {field}",
        )

    district_rows = query_dicts(
        conn,
        """
        SELECT district_code, state_name, passenger_cars, bev_cars, phev_cars
        FROM core.kba_district_ev_stock
        WHERE source_id = ? AND reference_date = CAST(? AS DATE)
        ORDER BY district_code
        """,
        [source_id, reference_date],
    )
    require(
        len(district_rows) == EXPECTED["district_rows_per_date"],
        f"Expected 400 KBA district rows for {reference_date}, found {len(district_rows)}",
    )
    district_codes = [str(row["district_code"]) for row in district_rows]
    require(len(set(district_codes)) == len(district_codes), f"Duplicate KBA district codes for {reference_date}")
    district_sum = {
        "passenger_car_stock": sum(int(row["passenger_cars"]) for row in district_rows),
        "bev_stock": sum(int(row["bev_cars"]) for row in district_rows),
        "phev_stock": sum(int(row["phev_cars"]) for row in district_rows),
    }
    district_sum["combined_plugin_stock"] = district_sum["bev_stock"] + district_sum["phev_stock"]
    for field in district_sum:
        require(
            district_sum[field] == state_sum[field],
            f"KBA 400-region total does not equal 16-state total for {reference_date}, {field}",
        )

    if validate_july_expected:
        require(national["bev_stock"] == EXPECTED["national_bev_july"], "Unexpected July national BEV total")
        require(state_sum["bev_stock"] == EXPECTED["sixteen_state_bev_july"], "Unexpected July 16-state BEV total")
        require(sonstige["bev_stock"] == EXPECTED["sonstige_bev_july"], "Unexpected July Sonstige BEV total")
        require(national["phev_stock"] == EXPECTED["national_phev_july"], "Unexpected July national PHEV total")
        require(state_sum["phev_stock"] == EXPECTED["sixteen_state_phev_july"], "Unexpected July 16-state PHEV total")
        require(sonstige["phev_stock"] == EXPECTED["sonstige_phev_july"], "Unexpected July Sonstige PHEV total")

    state_rows: List[Dict[str, Any]] = []
    for state in FEDERAL_STATES:
        record = by_geography[state]
        state_rows.append(
            {
                "state_name": state,
                "reference_date": reference_date,
                **record,
                "bev_penetration_pct": pct(record["bev_stock"], record["passenger_car_stock"]),
                "phev_penetration_pct": pct(record["phev_stock"], record["passenger_car_stock"]),
                "combined_plugin_penetration_pct": pct(
                    record["combined_plugin_stock"], record["passenger_car_stock"]
                ),
            }
        )
    return {
        "source_id": source_id,
        "reference_date": reference_date,
        "state_rows": state_rows,
        "by_geography": by_geography,
        "national": national,
        "sixteen_state_sum": state_sum,
        "sonstige": sonstige,
        "four_hundred_region_sum": district_sum,
        "district_row_count": len(district_rows),
    }


POINT_POWER_CTE = """
WITH source_points AS (
    SELECT p.source_id,
           p.equipment_excel_row,
           p.point_number,
           p.connector_power_raw,
           e.state_name,
           e.commissioning_date,
           e.status
    FROM core.charging_point AS p
    INNER JOIN core.charging_equipment AS e
      ON e.source_id = p.source_id
     AND e.excel_row = p.equipment_excel_row
    WHERE p.source_id = ?
), point_power_tokens AS (
    SELECT p.source_id,
           p.equipment_excel_row,
           p.point_number,
           p.state_name,
           p.commissioning_date,
           p.status,
           TRY_CAST(REPLACE(TRIM(token), ',', '.') AS DOUBLE) AS power_kw
    FROM source_points AS p,
         UNNEST(STRING_SPLIT(COALESCE(p.connector_power_raw, ''), ';')) AS tokens(token)
), point_power AS (
    SELECT source_id,
           equipment_excel_row,
           point_number,
           state_name,
           commissioning_date,
           status,
           MAX(power_kw) AS max_declared_point_power_kw
    FROM point_power_tokens
    GROUP BY source_id, equipment_excel_row, point_number, state_name, commissioning_date, status
)
"""


def load_infrastructure(
    conn: duckdb.DuckDBPyConnection,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    equipment_quality = query_dicts(
        conn,
        """
        SELECT
          COUNT(*) AS equipment_rows,
          COUNT(*) FILTER (WHERE commissioning_date_raw IS NULL) AS raw_null,
          COUNT(*) FILTER (WHERE commissioning_date_raw IS NOT NULL AND TRIM(commissioning_date_raw) = '') AS raw_blank,
          COUNT(*) FILTER (WHERE commissioning_date IS NULL) AS parsed_null,
          COUNT(*) FILTER (WHERE commissioning_date_raw IS NOT NULL
                                AND TRIM(commissioning_date_raw) <> ''
                                AND commissioning_date IS NULL) AS parsing_failures,
          COUNT(*) FILTER (WHERE commissioning_date < DATE '1900-01-01') AS before_1900,
          COUNT(*) FILTER (WHERE commissioning_date > CAST(? AS DATE)) AS after_snapshot,
          COUNT(*) FILTER (WHERE commissioning_date > CAST(? AS DATE)) AS after_cutoff,
          COUNT(*) FILTER (WHERE commissioning_date = CAST(? AS DATE)) AS exactly_on_cutoff,
          COUNT(*) FILTER (WHERE commissioning_date IS NOT NULL
                                AND NOT regexp_matches(TRIM(commissioning_date_raw), '^[0-9]+$')) AS non_numeric_raw,
          MIN(commissioning_date) AS minimum_date,
          MAX(commissioning_date) AS maximum_date,
          COUNT(DISTINCT commissioning_date_raw) AS distinct_raw_values,
          COUNT(DISTINCT commissioning_date) AS distinct_parsed_dates
        FROM core.charging_equipment
        WHERE source_id = ?
        """,
        [INFRASTRUCTURE_REFERENCE_DATE, KBA_SURVIVOR_CUTOFF_DATE, KBA_SURVIVOR_CUTOFF_DATE, INFRASTRUCTURE_SOURCE_ID],
    )[0]
    require(int(equipment_quality["equipment_rows"]) == EXPECTED["equipment"], "Unexpected BNetzA equipment row count")
    require(int(equipment_quality["raw_null"]) == 0, "NULL commissioning_date_raw values found")
    require(int(equipment_quality["raw_blank"]) == 0, "Blank commissioning_date_raw values found")
    require(int(equipment_quality["parsed_null"]) == 0, "NULL parsed commissioning dates found")
    require(int(equipment_quality["parsing_failures"]) == 0, "Commissioning-date parsing failures found")
    require(int(equipment_quality["after_snapshot"]) == 0, "Equipment commissioned after the September snapshot")
    require(int(equipment_quality["non_numeric_raw"]) == 0, "Unexpected non-numeric raw commissioning values found")

    equipment_rows = query_dicts(
        conn,
        """
        SELECT state_name,
               COUNT(*) AS equipment_count,
               SUM(COALESCE(declared_point_count, 0)) AS declared_point_count,
               SUM(COALESCE(equipment_nominal_power_kw, 0.0)) AS equipment_nominal_power_kw,
               COUNT(*) FILTER (WHERE declared_point_count IS NULL) AS null_declared_point_count,
               COUNT(*) FILTER (WHERE equipment_nominal_power_kw IS NULL) AS null_nominal_power,
               COUNT(*) FILTER (WHERE status = 'In Betrieb') AS equipment_in_operation,
               COUNT(*) FILTER (WHERE status = 'In Wartung') AS equipment_in_maintenance,
               COUNT(*) FILTER (WHERE status NOT IN ('In Betrieb', 'In Wartung') OR status IS NULL) AS equipment_other_status,
               COUNT(*) FILTER (WHERE commissioning_date <= CAST(? AS DATE)) AS survivor_equipment_count,
               SUM(CASE WHEN commissioning_date <= CAST(? AS DATE) THEN COALESCE(declared_point_count, 0) ELSE 0 END) AS survivor_declared_point_count,
               SUM(CASE WHEN commissioning_date <= CAST(? AS DATE) THEN COALESCE(equipment_nominal_power_kw, 0.0) ELSE 0.0 END) AS survivor_nominal_power_kw,
               COUNT(*) FILTER (WHERE commissioning_date > CAST(? AS DATE)) AS later_equipment_count,
               SUM(CASE WHEN commissioning_date > CAST(? AS DATE) THEN COALESCE(declared_point_count, 0) ELSE 0 END) AS later_declared_point_count
        FROM core.charging_equipment
        WHERE source_id = ?
        GROUP BY state_name
        ORDER BY state_name
        """,
        [
            KBA_SURVIVOR_CUTOFF_DATE,
            KBA_SURVIVOR_CUTOFF_DATE,
            KBA_SURVIVOR_CUTOFF_DATE,
            KBA_SURVIVOR_CUTOFF_DATE,
            KBA_SURVIVOR_CUTOFF_DATE,
            INFRASTRUCTURE_SOURCE_ID,
        ],
    )
    equipment_by_state = {str(row["state_name"]): row for row in equipment_rows}
    require(set(equipment_by_state) == set(FEDERAL_STATES), "BNetzA equipment does not cover exactly 16 states")
    require(sum(int(row["null_declared_point_count"]) for row in equipment_rows) == 0, "NULL declared point counts found")
    require(sum(int(row["null_nominal_power"]) for row in equipment_rows) == 0, "NULL nominal power values found")

    point_rows = query_dicts(
        conn,
        POINT_POWER_CTE
        + """
        SELECT state_name,
               COUNT(*) AS published_point_count,
               COUNT(*) FILTER (WHERE commissioning_date <= CAST(? AS DATE)) AS survivor_point_count,
               COUNT(*) FILTER (WHERE commissioning_date = CAST(? AS DATE)) AS cutoff_point_count,
               COUNT(*) FILTER (WHERE commissioning_date > CAST(? AS DATE)) AS later_point_count,
               COUNT(*) FILTER (WHERE max_declared_point_power_kw <= 22) AS published_normal_point_count,
               COUNT(*) FILTER (WHERE max_declared_point_power_kw > 22) AS published_fast_point_count,
               COUNT(*) FILTER (WHERE max_declared_point_power_kw >= 150) AS published_points_ge_150,
               COUNT(*) FILTER (WHERE max_declared_point_power_kw >= 350) AS published_points_ge_350,
               COUNT(*) FILTER (WHERE max_declared_point_power_kw IS NULL) AS published_invalid_power_points,
               COUNT(*) FILTER (WHERE commissioning_date <= CAST(? AS DATE)
                                      AND max_declared_point_power_kw <= 22) AS survivor_normal_point_count,
               COUNT(*) FILTER (WHERE commissioning_date <= CAST(? AS DATE)
                                      AND max_declared_point_power_kw > 22) AS survivor_fast_point_count,
               COUNT(*) FILTER (WHERE commissioning_date <= CAST(? AS DATE)
                                      AND max_declared_point_power_kw >= 150) AS survivor_points_ge_150,
               COUNT(*) FILTER (WHERE commissioning_date <= CAST(? AS DATE)
                                      AND max_declared_point_power_kw >= 350) AS survivor_points_ge_350,
               COUNT(*) FILTER (WHERE commissioning_date <= CAST(? AS DATE)
                                      AND max_declared_point_power_kw IS NULL) AS survivor_invalid_power_points,
               COUNT(*) FILTER (WHERE commissioning_date > CAST(? AS DATE)
                                      AND max_declared_point_power_kw <= 22) AS later_normal_point_count,
               COUNT(*) FILTER (WHERE commissioning_date > CAST(? AS DATE)
                                      AND max_declared_point_power_kw > 22) AS later_fast_point_count,
               COUNT(*) FILTER (WHERE commissioning_date > CAST(? AS DATE)
                                      AND max_declared_point_power_kw >= 150) AS later_points_ge_150,
               COUNT(*) FILTER (WHERE commissioning_date > CAST(? AS DATE)
                                      AND max_declared_point_power_kw >= 350) AS later_points_ge_350,
               COUNT(*) FILTER (WHERE commissioning_date > CAST(? AS DATE)
                                      AND max_declared_point_power_kw IS NULL) AS later_invalid_power_points
        FROM point_power
        GROUP BY state_name
        ORDER BY state_name
        """,
        [INFRASTRUCTURE_SOURCE_ID] + [KBA_SURVIVOR_CUTOFF_DATE] * 13,
    )
    point_by_state = {str(row["state_name"]): row for row in point_rows}
    require(set(point_by_state) == set(FEDERAL_STATES), "BNetzA points do not cover exactly 16 states")

    duplicate_equipment_rows = conn.execute(
        """
        SELECT COUNT(*)
        FROM (
          SELECT source_id, excel_row
          FROM core.charging_equipment
          WHERE source_id = ?
          GROUP BY source_id, excel_row
          HAVING COUNT(*) > 1
        ) AS duplicates
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    ).fetchone()[0]
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
    require(int(duplicate_equipment_rows) == 0, f"Duplicate equipment identities: {duplicate_equipment_rows}")
    require(int(duplicate_point_rows) == 0, f"Duplicate point identities: {duplicate_point_rows}")
    require(int(orphan_point_rows) == 0, f"Orphan charging points: {orphan_point_rows}")
    require(int(equipment_point_mismatches) == 0, f"Equipment/point mismatches: {equipment_point_mismatches}")

    rows: List[Dict[str, Any]] = []
    for state in FEDERAL_STATES:
        equipment = equipment_by_state[state]
        points = point_by_state[state]
        published_points = int(points["published_point_count"])
        survivor_points = int(points["survivor_point_count"])
        later_points = int(points["later_point_count"])
        require(
            int(equipment["declared_point_count"]) == published_points,
            f"Declared/populated point mismatch for {state}",
        )
        require(
            int(equipment["survivor_declared_point_count"]) == survivor_points,
            f"Survivor declared/populated point mismatch for {state}",
        )
        require(published_points == survivor_points + later_points, f"Cohort partition mismatch for {state}")
        require(
            int(points["published_normal_point_count"])
            + int(points["published_fast_point_count"])
            + int(points["published_invalid_power_points"])
            == published_points,
            f"Published power-band denominator mismatch for {state}",
        )
        require(
            int(points["survivor_normal_point_count"])
            + int(points["survivor_fast_point_count"])
            + int(points["survivor_invalid_power_points"])
            == survivor_points,
            f"Survivor power-band denominator mismatch for {state}",
        )
        require(
            int(points["later_normal_point_count"])
            + int(points["later_fast_point_count"])
            + int(points["later_invalid_power_points"])
            == later_points,
            f"Later power-band denominator mismatch for {state}",
        )
        rows.append(
            {
                "state_name": state,
                "published_equipment_count": int(equipment["equipment_count"]),
                "published_declared_point_count": int(equipment["declared_point_count"]),
                "published_charging_point_count": published_points,
                "published_normal_point_count": int(points["published_normal_point_count"]),
                "published_fast_point_count": int(points["published_fast_point_count"]),
                "published_points_ge_150": int(points["published_points_ge_150"]),
                "published_points_ge_350": int(points["published_points_ge_350"]),
                "published_invalid_power_points": int(points["published_invalid_power_points"]),
                "published_equipment_nominal_power_kw": float(equipment["equipment_nominal_power_kw"] or 0.0),
                "published_equipment_nominal_power_mw": float(equipment["equipment_nominal_power_kw"] or 0.0) / 1000.0,
                "survivor_equipment_count": int(equipment["survivor_equipment_count"]),
                "survivor_declared_point_count": int(equipment["survivor_declared_point_count"]),
                "survivor_charging_point_count": survivor_points,
                "survivor_normal_point_count": int(points["survivor_normal_point_count"]),
                "survivor_fast_point_count": int(points["survivor_fast_point_count"]),
                "survivor_points_ge_150": int(points["survivor_points_ge_150"]),
                "survivor_points_ge_350": int(points["survivor_points_ge_350"]),
                "survivor_invalid_power_points": int(points["survivor_invalid_power_points"]),
                "survivor_equipment_nominal_power_kw": float(equipment["survivor_nominal_power_kw"] or 0.0),
                "survivor_equipment_nominal_power_mw": float(equipment["survivor_nominal_power_kw"] or 0.0) / 1000.0,
                "later_equipment_count": int(equipment["later_equipment_count"]),
                "later_charging_point_count": later_points,
                "later_normal_point_count": int(points["later_normal_point_count"]),
                "later_fast_point_count": int(points["later_fast_point_count"]),
                "later_points_ge_150": int(points["later_points_ge_150"]),
                "later_points_ge_350": int(points["later_points_ge_350"]),
                "later_invalid_power_points": int(points["later_invalid_power_points"]),
                "equipment_in_operation": int(equipment["equipment_in_operation"] or 0),
                "equipment_in_maintenance": int(equipment["equipment_in_maintenance"] or 0),
                "equipment_other_status": int(equipment["equipment_other_status"] or 0),
                "status_labels": "In Betrieb; In Wartung" if int(equipment["equipment_in_maintenance"] or 0) else "In Betrieb",
                "cutoff_boundary_point_count": int(points["cutoff_point_count"]),
            }
        )

    totals: Dict[str, Any] = {}
    count_fields = (
        "published_equipment_count",
        "published_declared_point_count",
        "published_charging_point_count",
        "published_normal_point_count",
        "published_fast_point_count",
        "published_points_ge_150",
        "published_points_ge_350",
        "published_invalid_power_points",
        "survivor_equipment_count",
        "survivor_declared_point_count",
        "survivor_charging_point_count",
        "survivor_normal_point_count",
        "survivor_fast_point_count",
        "survivor_points_ge_150",
        "survivor_points_ge_350",
        "survivor_invalid_power_points",
        "later_equipment_count",
        "later_charging_point_count",
        "later_normal_point_count",
        "later_fast_point_count",
        "later_points_ge_150",
        "later_points_ge_350",
        "later_invalid_power_points",
        "cutoff_boundary_point_count",
    )
    for field in count_fields:
        totals[field] = sum(int(row[field]) for row in rows)
    totals["published_equipment_nominal_power_kw"] = sum(float(row["published_equipment_nominal_power_kw"]) for row in rows)
    totals["published_equipment_nominal_power_mw"] = totals["published_equipment_nominal_power_kw"] / 1000.0
    totals["survivor_equipment_nominal_power_kw"] = sum(float(row["survivor_equipment_nominal_power_kw"]) for row in rows)
    totals["survivor_equipment_nominal_power_mw"] = totals["survivor_equipment_nominal_power_kw"] / 1000.0
    totals["equipment_in_operation"] = sum(int(row["equipment_in_operation"]) for row in rows)
    totals["equipment_in_maintenance"] = sum(int(row["equipment_in_maintenance"]) for row in rows)
    totals["equipment_other_status"] = sum(int(row["equipment_other_status"]) for row in rows)
    require(totals["published_equipment_count"] == EXPECTED["equipment"], "Unexpected BNetzA equipment total")
    require(totals["published_declared_point_count"] == EXPECTED["declared_points"], "Unexpected declared point total")
    require(totals["published_charging_point_count"] == EXPECTED["charging_points"], "Unexpected point total")
    require(totals["published_normal_point_count"] == EXPECTED["normal_points"], "Unexpected normal-point total")
    require(totals["published_fast_point_count"] == EXPECTED["fast_points"], "Unexpected fast-point total")
    require(totals["published_points_ge_150"] == EXPECTED["points_ge_150"], "Unexpected >=150 kW point total")
    require(totals["published_points_ge_350"] == EXPECTED["points_ge_350"], "Unexpected >=350 kW point total")
    require(totals["published_invalid_power_points"] == EXPECTED["invalid_power_points"], "Unexpected invalid-power total")
    require(
        abs(float(totals["published_equipment_nominal_power_mw"]) - EXPECTED["nominal_power_mw"]) < 1e-9,
        "Unexpected BNetzA nominal power total",
    )
    require(
        totals["published_charging_point_count"]
        == totals["survivor_charging_point_count"] + totals["later_charging_point_count"],
        "Published point total does not partition into survivor and later cohorts",
    )
    require(
        totals["published_equipment_count"]
        == totals["survivor_equipment_count"] + totals["later_equipment_count"],
        "Published equipment total does not partition into survivor and later cohorts",
    )

    quality = {
        **equipment_quality,
        "duplicate_equipment_identities": int(duplicate_equipment_rows),
        "duplicate_point_identities": int(duplicate_point_rows),
        "orphan_point_rows": int(orphan_point_rows),
        "equipment_point_mismatches": int(equipment_point_mismatches),
        "power_definition": "Maximum valid numeric token in semicolon-separated connector_power_raw per point; <=22 normal, >22 fast, >=150/350 nested thresholds.",
        "status_definition": "Equipment status is retained as observed in the September register; no status filter is applied.",
        "commissioning_date_definition": "Equipment-level parsed date with commissioning_date_raw preserved; no point-level activation date is available.",
    }
    return rows, totals, [quality]


def commissioning_distribution(
    conn: duckdb.DuckDBPyConnection,
) -> List[Dict[str, Any]]:
    equipment = query_dicts(
        conn,
        """
        SELECT EXTRACT(YEAR FROM commissioning_date)::INTEGER AS year,
               EXTRACT(MONTH FROM commissioning_date)::INTEGER AS month,
               COUNT(*) AS equipment_count,
               SUM(COALESCE(declared_point_count, 0)) AS declared_point_count
        FROM core.charging_equipment
        WHERE source_id = ?
        GROUP BY 1, 2
        ORDER BY 1, 2
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    )
    point_rows = query_dicts(
        conn,
        POINT_POWER_CTE
        + """
        SELECT EXTRACT(YEAR FROM commissioning_date)::INTEGER AS year,
               EXTRACT(MONTH FROM commissioning_date)::INTEGER AS month,
               COUNT(*) AS charging_point_count,
               COUNT(*) FILTER (WHERE max_declared_point_power_kw <= 22) AS normal_point_count,
               COUNT(*) FILTER (WHERE max_declared_point_power_kw > 22) AS fast_point_count,
               COUNT(*) FILTER (WHERE max_declared_point_power_kw >= 150) AS points_ge_150,
               COUNT(*) FILTER (WHERE max_declared_point_power_kw >= 350) AS points_ge_350,
               COUNT(*) FILTER (WHERE max_declared_point_power_kw IS NULL) AS invalid_power_points
        FROM point_power
        GROUP BY 1, 2
        ORDER BY 1, 2
        """,
        [INFRASTRUCTURE_SOURCE_ID],
    )
    point_by_period = {(int(row["year"]), int(row["month"])): row for row in point_rows}
    rows: List[Dict[str, Any]] = []
    for equipment_row in equipment:
        period = (int(equipment_row["year"]), int(equipment_row["month"]))
        point_row = point_by_period[period]
        rows.append(
            {
                "distribution_type": "COMMISSIONING_MONTH",
                "period": f"{period[0]:04d}-{period[1]:02d}",
                "state_name": "",
                "status": "",
                "equipment_count": int(equipment_row["equipment_count"]),
                "charging_point_count": int(point_row["charging_point_count"]),
                "declared_point_count": int(equipment_row["declared_point_count"]),
                "normal_point_count": int(point_row["normal_point_count"]),
                "fast_point_count": int(point_row["fast_point_count"]),
                "points_ge_150": int(point_row["points_ge_150"]),
                "points_ge_350": int(point_row["points_ge_350"]),
                "invalid_power_points": int(point_row["invalid_power_points"]),
            }
        )
    by_year: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        year = int(row["period"][:4])
        target = by_year.setdefault(
            year,
            {
                "distribution_type": "COMMISSIONING_YEAR",
                "period": str(year),
                "state_name": "",
                "status": "",
                "equipment_count": 0,
                "charging_point_count": 0,
                "declared_point_count": 0,
                "normal_point_count": 0,
                "fast_point_count": 0,
                "points_ge_150": 0,
                "points_ge_350": 0,
                "invalid_power_points": 0,
            },
        )
        for field in (
            "equipment_count",
            "charging_point_count",
            "declared_point_count",
            "normal_point_count",
            "fast_point_count",
            "points_ge_150",
            "points_ge_350",
            "invalid_power_points",
        ):
            target[field] += int(row[field])
    return sorted(list(by_year.values()) + rows, key=lambda row: (row["distribution_type"], row["period"]))


def status_distribution(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    rows = query_dicts(
        conn,
        """
        SELECT COALESCE(status, '<NULL>') AS status,
               COUNT(*) AS equipment_count,
               SUM(COALESCE(declared_point_count, 0)) AS declared_point_count,
               COUNT(*) FILTER (WHERE commissioning_date <= CAST(? AS DATE)) AS survivor_equipment_count,
               SUM(CASE WHEN commissioning_date <= CAST(? AS DATE) THEN COALESCE(declared_point_count, 0) ELSE 0 END) AS survivor_declared_point_count,
               COUNT(*) FILTER (WHERE commissioning_date > CAST(? AS DATE)) AS later_equipment_count,
               SUM(CASE WHEN commissioning_date > CAST(? AS DATE) THEN COALESCE(declared_point_count, 0) ELSE 0 END) AS later_declared_point_count
        FROM core.charging_equipment
        WHERE source_id = ?
        GROUP BY status
        ORDER BY equipment_count DESC, status
        """,
        [
            KBA_SURVIVOR_CUTOFF_DATE,
            KBA_SURVIVOR_CUTOFF_DATE,
            KBA_SURVIVOR_CUTOFF_DATE,
            KBA_SURVIVOR_CUTOFF_DATE,
            INFRASTRUCTURE_SOURCE_ID,
        ],
    )
    return [
        {
            "distribution_type": "STATUS_ALL",
            "period": "",
            "state_name": "",
            "status": str(row["status"]),
            "equipment_count": int(row["equipment_count"]),
            "charging_point_count": int(row["declared_point_count"]),
            "declared_point_count": int(row["declared_point_count"]),
            "normal_point_count": None,
            "fast_point_count": None,
            "points_ge_150": None,
            "points_ge_350": None,
            "invalid_power_points": None,
            "survivor_equipment_count": int(row["survivor_equipment_count"]),
            "survivor_declared_point_count": int(row["survivor_declared_point_count"]),
            "later_equipment_count": int(row["later_equipment_count"]),
            "later_declared_point_count": int(row["later_declared_point_count"]),
        }
        for row in rows
    ]


def add_ranks(rows: List[Dict[str, Any]], field: str, output_field: str) -> None:
    ordered = sorted(rows, key=lambda row: float(row[field]))
    for index, row in enumerate(ordered, 1):
        row[output_field] = index


def build_state_sensitivity(
    vehicle_snapshot: Mapping[str, Any],
    infrastructure_rows: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    vehicle_by_state = {str(row["state_name"]): row for row in vehicle_snapshot["state_rows"]}
    require(set(vehicle_by_state) == set(FEDERAL_STATES), "July KBA vehicle rows do not cover exactly 16 states")
    total_bev = int(vehicle_snapshot["sixteen_state_sum"]["bev_stock"])
    total_published_points = sum(int(row["published_charging_point_count"]) for row in infrastructure_rows)
    rows: List[Dict[str, Any]] = []
    for infrastructure in infrastructure_rows:
        state = str(infrastructure["state_name"])
        vehicle = vehicle_by_state[state]
        bev = int(vehicle["bev_stock"])
        published_points = int(infrastructure["published_charging_point_count"])
        survivor_points = int(infrastructure["survivor_charging_point_count"])
        published_fast = int(infrastructure["published_fast_point_count"])
        survivor_fast = int(infrastructure["survivor_fast_point_count"])
        published_ge150 = int(infrastructure["published_points_ge_150"])
        survivor_ge150 = int(infrastructure["survivor_points_ge_150"])
        published_ge350 = int(infrastructure["published_points_ge_350"])
        survivor_ge350 = int(infrastructure["survivor_points_ge_350"])
        published_bevs_per_point = ratio(bev, published_points)
        survivor_bevs_per_point = ratio(bev, survivor_points)
        published_points_per_1000 = ratio(published_points * 1000.0, bev)
        survivor_points_per_1000 = ratio(survivor_points * 1000.0, bev)
        published_fast_per_1000 = ratio(published_fast * 1000.0, bev)
        survivor_fast_per_1000 = ratio(survivor_fast * 1000.0, bev)
        published_ge150_per_1000 = ratio(published_ge150 * 1000.0, bev)
        survivor_ge150_per_1000 = ratio(survivor_ge150 * 1000.0, bev)
        published_ge350_per_1000 = ratio(published_ge350 * 1000.0, bev)
        survivor_ge350_per_1000 = ratio(survivor_ge350 * 1000.0, bev)
        row: Dict[str, Any] = {
            "state_name": state,
            "kba_reference_date": KBA_PRIMARY_REFERENCE_DATE,
            "bnetza_reference_date": INFRASTRUCTURE_REFERENCE_DATE,
            "survivor_cutoff_date": KBA_SURVIVOR_CUTOFF_DATE,
            "bev_stock": bev,
            "phev_stock": int(vehicle["phev_stock"]),
            "passenger_car_stock": int(vehicle["passenger_car_stock"]),
            "bev_penetration_pct": vehicle["bev_penetration_pct"],
            "bev_stock_share_of_16_state_stock_pct": pct(bev, total_bev),
            "published_equipment_count": int(infrastructure["published_equipment_count"]),
            "published_charging_point_count": published_points,
            "published_normal_point_count": int(infrastructure["published_normal_point_count"]),
            "published_fast_point_count": published_fast,
            "published_points_ge_150": published_ge150,
            "published_points_ge_350": published_ge350,
            "published_fast_point_share_pct": pct(published_fast, published_points),
            "published_points_ge_150_share_pct": pct(published_ge150, published_points),
            "published_points_ge_350_share_pct": pct(published_ge350, published_points),
            "published_equipment_nominal_power_mw": infrastructure["published_equipment_nominal_power_mw"],
            "published_point_share_of_16_state_points_pct": pct(published_points, total_published_points),
            "survivor_equipment_count": int(infrastructure["survivor_equipment_count"]),
            "survivor_charging_point_count": survivor_points,
            "survivor_normal_point_count": int(infrastructure["survivor_normal_point_count"]),
            "survivor_fast_point_count": survivor_fast,
            "survivor_points_ge_150": survivor_ge150,
            "survivor_points_ge_350": survivor_ge350,
            "survivor_fast_point_share_pct": pct(survivor_fast, survivor_points),
            "survivor_points_ge_150_share_pct": pct(survivor_ge150, survivor_points),
            "survivor_points_ge_350_share_pct": pct(survivor_ge350, survivor_points),
            "survivor_equipment_nominal_power_mw": infrastructure["survivor_equipment_nominal_power_mw"],
            "published_bevs_per_point": published_bevs_per_point,
            "survivor_bevs_per_point": survivor_bevs_per_point,
            "published_points_per_1000_bevs": published_points_per_1000,
            "survivor_points_per_1000_bevs": survivor_points_per_1000,
            "published_fast_points_per_1000_bevs": published_fast_per_1000,
            "survivor_fast_points_per_1000_bevs": survivor_fast_per_1000,
            "published_ge150_points_per_1000_bevs": published_ge150_per_1000,
            "survivor_ge150_points_per_1000_bevs": survivor_ge150_per_1000,
            "published_ge350_points_per_1000_bevs": published_ge350_per_1000,
            "survivor_ge350_points_per_1000_bevs": survivor_ge350_per_1000,
            "later_equipment_count": int(infrastructure["later_equipment_count"]),
            "later_charging_point_count": int(infrastructure["later_charging_point_count"]),
            "later_normal_point_count": int(infrastructure["later_normal_point_count"]),
            "later_fast_point_count": int(infrastructure["later_fast_point_count"]),
            "later_points_ge_150": int(infrastructure["later_points_ge_150"]),
            "later_points_ge_350": int(infrastructure["later_points_ge_350"]),
            "later_invalid_power_points": int(infrastructure["later_invalid_power_points"]),
            "later_point_share_of_state_published_pct": pct(
                infrastructure["later_charging_point_count"], published_points
            ),
            "published_minus_survivor_equipment_count": int(infrastructure["published_equipment_count"])
            - int(infrastructure["survivor_equipment_count"]),
            "published_minus_survivor_charging_point_count": published_points - survivor_points,
            "published_minus_survivor_fast_point_count": published_fast - survivor_fast,
            "published_minus_survivor_points_ge_150": published_ge150 - survivor_ge150,
            "published_minus_survivor_points_ge_350": published_ge350 - survivor_ge350,
            "survivor_minus_published_bevs_per_point": None
            if published_bevs_per_point is None or survivor_bevs_per_point is None
            else survivor_bevs_per_point - published_bevs_per_point,
            "survivor_minus_published_bevs_per_point_pct": pct_change(
                survivor_bevs_per_point, published_bevs_per_point
            ),
            "survivor_minus_published_points_per_1000_bevs": None
            if published_points_per_1000 is None or survivor_points_per_1000 is None
            else survivor_points_per_1000 - published_points_per_1000,
            "survivor_minus_published_points_per_1000_bevs_pct": pct_change(
                survivor_points_per_1000, published_points_per_1000
            ),
            "survivor_minus_published_fast_points_per_1000_bevs": None
            if published_fast_per_1000 is None or survivor_fast_per_1000 is None
            else survivor_fast_per_1000 - published_fast_per_1000,
            "survivor_minus_published_fast_points_per_1000_bevs_pct": pct_change(
                survivor_fast_per_1000, published_fast_per_1000
            ),
            "survivor_minus_published_ge150_points_per_1000_bevs": None
            if published_ge150_per_1000 is None or survivor_ge150_per_1000 is None
            else survivor_ge150_per_1000 - published_ge150_per_1000,
            "survivor_minus_published_ge150_points_per_1000_bevs_pct": pct_change(
                survivor_ge150_per_1000, published_ge150_per_1000
            ),
            "survivor_minus_published_ge350_points_per_1000_bevs": None
            if published_ge350_per_1000 is None or survivor_ge350_per_1000 is None
            else survivor_ge350_per_1000 - published_ge350_per_1000,
            "survivor_minus_published_ge350_points_per_1000_bevs_pct": pct_change(
                survivor_ge350_per_1000, published_ge350_per_1000
            ),
            "survivor_minus_published_fast_point_share_pp": None
            if pct(survivor_fast, survivor_points) is None or pct(published_fast, published_points) is None
            else pct(survivor_fast, survivor_points) - pct(published_fast, published_points),
            "status_labels": infrastructure["status_labels"],
            "temporal_label_published": "CROSS-SNAPSHOT DESCRIPTIVE COMPARISON",
            "temporal_label_survivor": "RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE",
        }
        rows.append(row)

    add_ranks(rows, "published_bevs_per_point", "published_bevs_per_point_rank")
    add_ranks(rows, "survivor_bevs_per_point", "survivor_bevs_per_point_rank")
    add_ranks(rows, "published_fast_points_per_1000_bevs", "published_fast_points_per_1000_rank")
    add_ranks(rows, "survivor_fast_points_per_1000_bevs", "survivor_fast_points_per_1000_rank")
    add_ranks(rows, "published_ge150_points_per_1000_bevs", "published_ge150_points_per_1000_rank")
    add_ranks(rows, "survivor_ge150_points_per_1000_bevs", "survivor_ge150_points_per_1000_rank")
    add_ranks(rows, "published_ge350_points_per_1000_bevs", "published_ge350_points_per_1000_rank")
    add_ranks(rows, "survivor_ge350_points_per_1000_bevs", "survivor_ge350_points_per_1000_rank")
    for row in rows:
        row["bevs_per_point_rank_change_survivor_minus_published"] = (
            int(row["survivor_bevs_per_point_rank"]) - int(row["published_bevs_per_point_rank"])
        )
        row["fast_points_per_1000_rank_change_survivor_minus_published"] = (
            int(row["survivor_fast_points_per_1000_rank"])
            - int(row["published_fast_points_per_1000_rank"])
        )
        row["ge150_points_per_1000_rank_change_survivor_minus_published"] = (
            int(row["survivor_ge150_points_per_1000_rank"])
            - int(row["published_ge150_points_per_1000_rank"])
        )
        row["ge350_points_per_1000_rank_change_survivor_minus_published"] = (
            int(row["survivor_ge350_points_per_1000_rank"])
            - int(row["published_ge350_points_per_1000_rank"])
        )
    return sorted(rows, key=lambda row: FEDERAL_STATES.index(str(row["state_name"])))


def rank_correlation(rows: Sequence[Mapping[str, Any]], field_a: str, field_b: str) -> Optional[float]:
    values_a = [float(row[field_a]) for row in rows]
    values_b = [float(row[field_b]) for row in rows]
    return pearson(rankdata(values_a), rankdata(values_b))


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


def extreme(rows: Sequence[Mapping[str, Any]], field: str, reverse: bool) -> Mapping[str, Any]:
    ordered = sorted(rows, key=lambda row: float(row[field]), reverse=reverse)
    require(bool(ordered), f"Cannot rank empty rows for {field}")
    return ordered[0]


def ranking_summary(state_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    specifications = (
        ("BEVs per charging point", "published_bevs_per_point", "survivor_bevs_per_point", False),
        (
            "Fast points per 1,000 BEVs",
            "published_fast_points_per_1000_bevs",
            "survivor_fast_points_per_1000_bevs",
            False,
        ),
        (
            ">=150 kW points per 1,000 BEVs",
            "published_ge150_points_per_1000_bevs",
            "survivor_ge150_points_per_1000_bevs",
            False,
        ),
        (
            ">=350 kW points per 1,000 BEVs",
            "published_ge350_points_per_1000_bevs",
            "survivor_ge350_points_per_1000_bevs",
            False,
        ),
        ("Fast point share", "published_fast_point_share_pct", "survivor_fast_point_share_pct", True),
        (
            ">=150 kW point share",
            "published_points_ge_150_share_pct",
            "survivor_points_ge_150_share_pct",
            True,
        ),
        (
            ">=350 kW point share",
            "published_points_ge_350_share_pct",
            "survivor_points_ge_350_share_pct",
            True,
        ),
    )
    output: List[Dict[str, Any]] = []
    for name, published_field, survivor_field, high_is_extreme in specifications:
        published_low = extreme(state_rows, published_field, False)
        published_high = extreme(state_rows, published_field, True)
        survivor_low = extreme(state_rows, survivor_field, False)
        survivor_high = extreme(state_rows, survivor_field, True)
        output.append(
            {
                "metric": name,
                "published_low_state": published_low["state_name"],
                "published_low_value": published_low[published_field],
                "published_high_state": published_high["state_name"],
                "published_high_value": published_high[published_field],
                "survivor_low_state": survivor_low["state_name"],
                "survivor_low_value": survivor_low[survivor_field],
                "survivor_high_state": survivor_high["state_name"],
                "survivor_high_value": survivor_high[survivor_field],
                "low_state_stable": published_low["state_name"] == survivor_low["state_name"],
                "high_state_stable": published_high["state_name"] == survivor_high["state_name"],
                "published_extreme_direction": "highest/lowest as shown",
                "note": (
                    "Ranking is descriptive; survivor values use currently reported September point rows "
                    "attached to equipment commissioned on or before 2026-07-01."
                ),
            }
        )
    return output


def fixed_denominator_sensitivity(
    snapshots: Mapping[str, Mapping[str, Any]],
    published_points: int,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for source_id, reference_date in KBA_SNAPSHOT_SPECS:
        snapshot = snapshots[reference_date]
        state_bev = int(snapshot["sixteen_state_sum"]["bev_stock"])
        national_bev = int(snapshot["national"]["bev_stock"])
        rows.append(
            {
                "kba_source_id": source_id,
                "kba_reference_date": reference_date,
                "infrastructure_reference_date": INFRASTRUCTURE_REFERENCE_DATE,
                "infrastructure_denominator": published_points,
                "kba_scope": "16-state sum",
                "bev_stock": state_bev,
                "bevs_per_fixed_september_point": ratio(state_bev, published_points),
                "fixed_september_points_per_1000_bevs": ratio(published_points * 1000.0, state_bev),
                "interpretation_label": "VEHICLE-STOCK SENSITIVITY WITH FIXED SEPTEMBER DENOMINATOR — NOT JANUARY/APRIL INFRASTRUCTURE",
            }
        )
        rows.append(
            {
                "kba_source_id": source_id,
                "kba_reference_date": reference_date,
                "infrastructure_reference_date": INFRASTRUCTURE_REFERENCE_DATE,
                "infrastructure_denominator": published_points,
                "kba_scope": "published Deutschland",
                "bev_stock": national_bev,
                "bevs_per_fixed_september_point": ratio(national_bev, published_points),
                "fixed_september_points_per_1000_bevs": ratio(published_points * 1000.0, national_bev),
                "interpretation_label": "VEHICLE-STOCK SENSITIVITY WITH FIXED SEPTEMBER DENOMINATOR — NOT JANUARY/APRIL INFRASTRUCTURE",
            }
        )
    return rows


def kpi_decisions(
    state_rows: Sequence[Mapping[str, Any]],
    totals: Mapping[str, Any],
    ranking_rows: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    pub_bev_per_point = ratio(
        sum(int(row["bev_stock"]) for row in state_rows),
        int(totals["published_charging_point_count"]),
    )
    survivor_bev_per_point = ratio(
        sum(int(row["bev_stock"]) for row in state_rows),
        int(totals["survivor_charging_point_count"]),
    )
    ratio_change = pct_change(survivor_bev_per_point, pub_bev_per_point)
    stable_bev_rank = next(row for row in ranking_rows if row["metric"] == "BEVs per charging point")
    stable_fast_rank = next(row for row in ranking_rows if row["metric"] == "Fast points per 1,000 BEVs")
    date_label = (
        "CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — KBA stock 2026-07-01; "
        "BNetzA published snapshot 2026-09-30 (91-day separation)"
    )
    survivor_label = (
        "RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE; "
        "equipment commissioned on or before 2026-07-01 with September point rows retained"
    )
    common = {
        "geographic_grain": "16 federal states; primary national scope is the comparable 16-state sum",
        "vehicle_reference_date": KBA_PRIMARY_REFERENCE_DATE,
        "infrastructure_reference_date": INFRASTRUCTURE_REFERENCE_DATE,
        "observed_or_reconstructed_status": "KBA stock observed; published infrastructure observed in September; survivor infrastructure reconstructed from equipment commissioning date",
        "required_explanatory_label": date_label + "; survivor sensitivity, if shown, must use: " + survivor_label,
    }
    rows = [
        {
            **common,
            "kpi_name": "BEVs per registered charging point",
            "formula": "KBA BEV passenger-car stock / BNetzA populated charging-point slots",
            "numerator": "KBA FZ 27.2 Elektro (BEV), 2026-07-01",
            "denominator": "BNetzA point rows, 2026-09-30; survivor alternative retains point rows attached to equipment commissioned <= 2026-07-01",
            "temporal_validity": "Published numerator and denominator are 91 days apart; survivor alternative is not a historical July registry",
            "published_snapshot_sensitivity": f"16-state {fmt_num(pub_bev_per_point, 6)} BEVs/point; survivor {fmt_num(survivor_bev_per_point, 6)}; change {fmt_signed_pct(ratio_change)}",
            "risk_of_misinterpretation": "High if read as adequacy, accessibility, demand, utilization, or a same-day ratio; BNetzA is not exhaustive",
            "recommended_visualization": "Secondary contextual KPI/table with both dates, denominator scope, and a warning note; no gauge or adequacy threshold",
            "publication_status": "CONTEXT_ONLY",
            "recommendation": "Do not use as headline. It can appear as a dated secondary context measure because the sensitivity result is measurable but interpretation remains limited.",
            "evidence": f"Published-to-survivor change is {fmt_signed_pct(ratio_change)}; lowest-state stability: {stable_bev_rank['low_state_stable']}; highest-state stability: {stable_bev_rank['high_state_stable']}; these do not establish July infrastructure.",
        },
        {
            **common,
            "kpi_name": "Registered charging points per 1,000 BEVs",
            "formula": "1,000 × BNetzA populated charging-point slots / KBA BEV stock",
            "numerator": "BNetzA populated point rows, 2026-09-30",
            "denominator": "KBA FZ 27.2 Elektro (BEV), 2026-07-01",
            "temporal_validity": "Inverse of the date-mismatched BEVs-per-point comparison; survivor denominator is reconstructed, not historical July",
            "published_snapshot_sensitivity": "Inverse ratio; use the same date label and survivor warning as BEVs per point",
            "risk_of_misinterpretation": "High if read as a service standard or adequacy/surplus measure",
            "recommended_visualization": "Secondary context table only, paired with absolute stock and point counts",
            "publication_status": "CONTEXT_ONLY",
            "recommendation": "Do not show as a standalone headline or threshold comparison.",
            "evidence": "Same dates, source coverage and cohort limitations as BEVs per registered point.",
        },
        {
            **common,
            "kpi_name": "Fast points per 1,000 BEVs",
            "formula": "1,000 × point rows with maximum declared power >22 kW / KBA BEV stock",
            "numerator": "BNetzA point-level maximum-power classification",
            "denominator": "KBA registered BEV stock",
            "temporal_validity": "Cross-snapshot and power-declaration dependent; survivor sensitivity removes later-commissioned point rows but does not reconstruct July operation",
            "published_snapshot_sensitivity": "State-level counts and differences are in batch17_state_temporal_sensitivity.csv",
            "risk_of_misinterpretation": "Very high if treated as fast-charging access, capacity, utilization, or demand coverage",
            "recommended_visualization": "Exploratory sensitivity dot plot or table with point counts, dates, and declared-power caveat",
            "publication_status": "EXPLORATORY_SENSITIVITY",
            "recommendation": "Keep out of headline tiles; show only as a sensitivity comparison if the owner wants the descriptive power mix.",
            "evidence": f"Fast-point ranking low/high state stability: {stable_fast_rank['low_state_stable']} / {stable_fast_rank['high_state_stable']}; ranking stability is not a validity proof.",
        },
        {
            **common,
            "kpi_name": ">=150 kW points per 1,000 BEVs",
            "formula": "1,000 × point rows with maximum declared power >=150 kW / KBA BEV stock",
            "numerator": "BNetzA point-level maximum-power classification",
            "denominator": "KBA registered BEV stock",
            "temporal_validity": "Cross-snapshot; survivor result is a September survivor cohort, not actual July high-power stock",
            "published_snapshot_sensitivity": "Compare published and survivor counts/ratios in the state sensitivity CSV",
            "risk_of_misinterpretation": "High; declared threshold is not simultaneous deliverable power, availability, or vehicle suitability",
            "recommended_visualization": "Exploratory sensitivity table with threshold definition shown in the subtitle",
            "publication_status": "EXPLORATORY_SENSITIVITY",
            "recommendation": "Do not publish as an adequacy or HPC-access KPI.",
            "evidence": "Maximum-per-point parser and date mismatch are both material; no utilization or activation history exists.",
        },
        {
            **common,
            "kpi_name": ">=350 kW points per 1,000 BEVs",
            "formula": "1,000 × point rows with maximum declared power >=350 kW / KBA BEV stock",
            "numerator": "BNetzA point-level maximum-power classification",
            "denominator": "KBA registered BEV stock",
            "temporal_validity": "Cross-snapshot; survivor result is reconstructed from September records",
            "published_snapshot_sensitivity": "Compare published and survivor counts/ratios in the state sensitivity CSV",
            "risk_of_misinterpretation": "High; no evidence of simultaneous delivery, availability, queue times, or demand",
            "recommended_visualization": "Exploratory threshold comparison only",
            "publication_status": "EXPLORATORY_SENSITIVITY",
            "recommendation": "Do not publish as a headline or service-level measure.",
            "evidence": "No point activation date or operational history is available.",
        },
        {
            **common,
            "kpi_name": "Combined plug-in vehicles per registered point",
            "formula": "(KBA BEV + PHEV passenger-car stock) / BNetzA populated point rows",
            "numerator": "KBA BEV + nested PHEV stock, 2026-07-01",
            "denominator": "BNetzA populated point rows, 2026-09-30",
            "temporal_validity": "Same cross-snapshot limitation; PHEV stock is not charging demand",
            "published_snapshot_sensitivity": "Use only with the BEV-only metric and explicit PHEV stock—not demand—label",
            "risk_of_misinterpretation": "High; vehicle stock does not identify charging demand or plug-in behavior",
            "recommended_visualization": "Context-only table, never a headline adequacy tile",
            "publication_status": "CONTEXT_ONLY",
            "recommendation": "Retain only as optional context if PHEV scope is clearly shown.",
            "evidence": "PHEV is a nested KBA stock detail and infrastructure dates remain mismatched.",
        },
        {
            **common,
            "kpi_name": "BEV-share minus charging-point-share gap",
            "formula": "State BEV share of 16-state stock − state share of published BNetzA points",
            "numerator": "State BEV stock and state point count shares",
            "denominator": "16-state totals within each source",
            "temporal_validity": "Compositional cross-snapshot comparison; survivor variant changes point shares but is not July observed",
            "published_snapshot_sensitivity": "Ranking and sign may be compared, but gap is not a shortage/surplus indicator",
            "risk_of_misinterpretation": "Very high if described as under-supply, over-supply, or need",
            "recommended_visualization": "Annotated composition chart with zero line and a non-adequacy warning",
            "publication_status": "EXPLORATORY_SENSITIVITY",
            "recommendation": "Use only as an exploratory allocation comparison, not as a standalone KPI.",
            "evidence": "Fixed-scope shares are arithmetic; temporal mismatch and register completeness still limit interpretation.",
        },
        {
            **common,
            "kpi_name": "State correlations between EV stock and infrastructure",
            "formula": "Descriptive Pearson/Spearman correlations across 16 state rows",
            "numerator": "One state-level source aggregate per variable",
            "denominator": "Not a ratio denominator; n=16 cross-sectional rows",
            "temporal_validity": "Cross-sectional and cross-snapshot; survivor re-estimation is sensitivity only",
            "published_snapshot_sensitivity": "Correlations can remain stable because state size dominates; this does not validate causality or July alignment",
            "risk_of_misinterpretation": "Very high; association is not demand, causality, adequacy, or generalization",
            "recommended_visualization": "Analyst diagnostic scatter plot, not a dashboard headline",
            "publication_status": "EXPLORATORY_SENSITIVITY",
            "recommendation": "Keep as an internal diagnostic or clearly footnoted exploratory chart.",
            "evidence": "Small n, scale effects, denominator effects, non-exhaustive register, and no causal design.",
        },
        {
            **common,
            "kpi_name": "Infrastructure adequacy, shortage, or surplus",
            "formula": "No defensible formula from current sources",
            "numerator": "No observed demand, sessions, availability, or service standard",
            "denominator": "No approved need or capacity denominator",
            "temporal_validity": "Not supported",
            "published_snapshot_sensitivity": "Cohort sensitivity cannot supply the missing demand/availability evidence",
            "risk_of_misinterpretation": "Directly unsupported by the available source fields",
            "recommended_visualization": "Do not visualize as a KPI",
            "publication_status": "NOT_SUPPORTED",
            "recommendation": "Do not deploy; obtain approved contemporaneous infrastructure and demand/availability evidence first.",
            "evidence": "KBA stock, BNetzA register, commissioning date and status do not measure demand, utilization or verified operational availability.",
        },
    ]
    return rows


def render_report(
    database: Path,
    database_sha256: str,
    fingerprints: Sequence[Mapping[str, Any]],
    database_contract: Mapping[str, Any],
    snapshots: Mapping[str, Mapping[str, Any]],
    infrastructure_rows: Sequence[Mapping[str, Any]],
    infrastructure_totals: Mapping[str, Any],
    quality: Mapping[str, Any],
    distribution_rows: Sequence[Mapping[str, Any]],
    status_rows: Sequence[Mapping[str, Any]],
    state_rows: Sequence[Mapping[str, Any]],
    ranking_rows: Sequence[Mapping[str, Any]],
    decisions: Sequence[Mapping[str, Any]],
    fixed_denominator_rows: Sequence[Mapping[str, Any]],
) -> str:
    july = snapshots[KBA_PRIMARY_REFERENCE_DATE]
    latest_year_rows = [row for row in distribution_rows if row["distribution_type"] == "COMMISSIONING_YEAR"]
    latest_month_rows = [row for row in distribution_rows if row["distribution_type"] == "COMMISSIONING_MONTH" and row["period"].startswith("2026-")]
    later_states = sorted(
        state_rows,
        key=lambda row: int(row["later_charging_point_count"]),
        reverse=True,
    )
    later_status = [row for row in status_rows]
    survivor_ratio = ratio(
        int(july["sixteen_state_sum"]["bev_stock"]),
        int(infrastructure_totals["survivor_charging_point_count"]),
    )
    published_ratio = ratio(
        int(july["sixteen_state_sum"]["bev_stock"]),
        int(infrastructure_totals["published_charging_point_count"]),
    )
    ranking_by_metric = {row["metric"]: row for row in ranking_rows}
    changed_bev_rank = sum(
        1 for row in state_rows if int(row["bevs_per_point_rank_change_survivor_minus_published"]) != 0
    )
    changed_fast_rank = sum(
        1 for row in state_rows if int(row["fast_points_per_1000_rank_change_survivor_minus_published"]) != 0
    )
    lines: List[str] = [
        "# Batch 17 — temporal validity and sensitivity of cross-source EV charging KPIs",
        "",
        "**Batch status: PASS**",
        "",
        "This report is a deterministic, read-only analysis of temporal compatibility between KBA registered passenger-car stock and the BNetzA charging register. It distinguishes the observed September publication from a retrospective equipment-commissioning cohort; the latter is not a historical July infrastructure snapshot.",
        "",
        "## 1. Executive summary",
        "",
        f"**OBSERVED:** The BNetzA register snapshot dated **{INFRASTRUCTURE_REFERENCE_DATE}** contains {fmt_int(infrastructure_totals['published_equipment_count'])} equipment records and {fmt_int(infrastructure_totals['published_charging_point_count'])} populated point slots. The maximum-per-point parser classifies {fmt_int(infrastructure_totals['published_normal_point_count'])} normal (<=22 kW), {fmt_int(infrastructure_totals['published_fast_point_count'])} fast (>22 kW), {fmt_int(infrastructure_totals['published_points_ge_150'])} at >=150 kW and {fmt_int(infrastructure_totals['published_points_ge_350'])} at >=350 kW. Declared equipment nominal power is {fmt_num(infrastructure_totals['published_equipment_nominal_power_mw'], 4)} MW.",
        "",
        f"**OBSERVED:** The July KBA state-fuel snapshot contains {fmt_int(july['national']['bev_stock'])} national BEVs, {fmt_int(july['national']['phev_stock'])} national PHEVs and {fmt_int(july['national']['passenger_car_stock'])} passenger cars. The 16 named states contain {fmt_int(july['sixteen_state_sum']['bev_stock'])} BEVs and {fmt_int(july['sixteen_state_sum']['phev_stock'])} PHEVs; `Sonstige` contains {fmt_int(july['sonstige']['bev_stock'])} BEVs and {fmt_int(july['sonstige']['phev_stock'])} PHEVs. The state and 400-region totals are not double-counted.",
        "",
        f"**QUALITY:** All {fmt_int(quality['equipment_rows'])} commissioning raw values are nonblank and parse successfully; no equipment is dated after the September snapshot. {fmt_int(quality['after_cutoff'])} equipment records and {fmt_int(infrastructure_totals['later_charging_point_count'])} point rows were commissioned after the July 1 cutoff, representing {fmt_pct(pct(infrastructure_totals['later_equipment_count'], infrastructure_totals['published_equipment_count']))} of equipment and {fmt_pct(pct(infrastructure_totals['later_charging_point_count'], infrastructure_totals['published_charging_point_count']))} of points.",
        "",
        f"**SENSITIVITY:** The retrospective September-survivor cohort contains {fmt_int(infrastructure_totals['survivor_equipment_count'])} equipment records and {fmt_int(infrastructure_totals['survivor_charging_point_count'])} currently associated point rows. The 16-state BEVs-per-point ratio changes from {fmt_num(published_ratio, 6)} in the published September comparison to {fmt_num(survivor_ratio, 6)} in the survivor cohort ({fmt_signed_pct(pct_change(survivor_ratio, published_ratio))}); this is a cohort sensitivity, not observed July infrastructure.",
        "",
        f"**RECOMMENDATION:** BEVs per registered point is **CONTEXT_ONLY**: a secondary contextual measure with both dates visible, not a headline adequacy KPI. Power-normalized ratios, share gaps, rank comparisons and correlations remain **EXPLORATORY_SENSITIVITY**. No adequacy, shortage or surplus KPI is supported.",
        "",
        "## 2. Data-source vintages and definitions",
        "",
        *markdown_table(
            ["Concept", "Value", "Meaning", "Do not substitute"],
            [
                ["KBA vehicle-stock reference date", "2026-01-01 / 2026-04-01 / 2026-07-01", "Registered passenger-car stock reported by KBA at each snapshot", "New registrations, sales, charging demand, or a BNetzA date"],
                ["Primary KBA date", "2026-07-01", "Vehicle denominator used for the primary comparison", "An observed July infrastructure stock"],
                ["BNetzA publication/snapshot date", "2026-09-30", "Register rows and statuses represented in the source workbook", "Equipment commissioning date or point activation date"],
                ["Equipment commissioning date", "Equipment-level parsed DATE", "Source value retained in commissioning_date_raw and parsed into commissioning_date", "The date each individual point became accessible"],
                ["Point-level activation date", "Not available", "core.charging_point has no activation-date field", "Equipment commissioning date"],
                ["Equipment status", "Observed in September", "Current register label such as In Betrieb or In Wartung", "Verified historical operational availability or uptime"],
                ["July cutoff", "2026-07-01 inclusive", "Cohort selection boundary for equipment commissioning dates", "A historical July registry snapshot"],
            ],
        ),
        "",
        f"The July 1 KBA stock and September 30 BNetzA snapshot are **91 days apart**. Perspective A is labelled **CROSS-SNAPSHOT DESCRIPTIVE COMPARISON**. Perspective B is labelled **RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE**.",
        "",
        "## 3. Commissioning-date quality audit",
        "",
        *markdown_table(
            ["Check", "Result", "Interpretation"],
            [
                ["Equipment rows", fmt_int(quality["equipment_rows"]), "All normalized BNetzA equipment rows in the September source"],
                ["NULL raw values", fmt_int(quality["raw_null"]), "No missing source value observed"],
                ["Blank raw values", fmt_int(quality["raw_blank"]), "No blank source value observed"],
                ["Parsed NULL dates", fmt_int(quality["parsed_null"]), "No parsed-date NULL"],
                ["Parsing failures", fmt_int(quality["parsing_failures"]), "Nonblank raw value with no parsed date"],
                ["Non-numeric raw values", fmt_int(quality["non_numeric_raw"]), "Current raw values are Excel-style numeric serial strings"],
                ["Dates after 2026-09-30", fmt_int(quality["after_snapshot"]), "No future commissioning date relative to the source snapshot"],
                ["Dates after 2026-07-01", fmt_int(quality["after_cutoff"]), "Later commissioning records excluded from the survivor cohort"],
                ["Dates exactly 2026-07-01", fmt_int(quality["exactly_on_cutoff"]), "Boundary rows are included by the <= cutoff rule"],
                ["Minimum / maximum parsed date", f"{fmt_date(quality['minimum_date'])} / {fmt_date(quality['maximum_date'])}", "Historical values are retained; a very old date is not silently changed"],
            ],
        ),
        "",
        f"The earliest parsed commissioning date is {fmt_date(quality['minimum_date'])}; {fmt_int(quality['before_1900'])} dates precede 1900 and {fmt_int(sum(int(row['equipment_count']) for row in latest_year_rows if int(row['period']) < 2010))} equipment records fall in years before 2010. These are unusual historical source values for audit, not evidence that all points were accessible continuously since commissioning.",
        "",
        "### Distribution by commissioning year",
        "",
        *markdown_table(
            ["Year", "Equipment", "Point rows", "Fast points", ">=150 kW", ">=350 kW"],
            [
                [row["period"], fmt_int(row["equipment_count"]), fmt_int(row["charging_point_count"]), fmt_int(row["fast_point_count"]), fmt_int(row["points_ge_150"]), fmt_int(row["points_ge_350"])]
                for row in latest_year_rows
            ],
        ),
        "",
        "### 2026 monthly distribution",
        "",
        *markdown_table(
            ["Month", "Equipment", "Point rows", "Fast points", ">=150 kW", ">=350 kW"],
            [
                [row["period"], fmt_int(row["equipment_count"]), fmt_int(row["charging_point_count"]), fmt_int(row["fast_point_count"]), fmt_int(row["points_ge_150"]), fmt_int(row["points_ge_350"])]
                for row in latest_month_rows
            ],
        ),
        "",
        "### Status and geographic distribution of later-commissioned records",
        "",
        *markdown_table(
            ["Status", "All equipment", "All declared points", "After cutoff equipment", "After cutoff declared points"],
            [
                [row["status"], fmt_int(row["equipment_count"]), fmt_int(row["declared_point_count"]), fmt_int(row["later_equipment_count"]), fmt_int(row["later_declared_point_count"])]
                for row in later_status
            ],
        ),
        "",
        *markdown_table(
            ["State", "Later equipment", "Later points", "% of state points", "% of national later points"],
            [
                [
                    row["state_name"],
                    fmt_int(row["later_equipment_count"]),
                    fmt_int(row["later_charging_point_count"]),
                    fmt_pct(row["later_point_share_of_state_published_pct"]),
                    fmt_pct(pct(row["later_charging_point_count"], infrastructure_totals["later_charging_point_count"])),
                ]
                for row in later_states
            ],
        ),
        "",
        "## 4. September equipment/point commissioning cohorts",
        "",
        *markdown_table(
            ["Perspective", "Equipment", "Point rows", "Normal", "Fast", ">=150 kW", ">=350 kW", "Nominal MW", "Status"],
            [
                [
                    "Published September snapshot",
                    fmt_int(infrastructure_totals["published_equipment_count"]),
                    fmt_int(infrastructure_totals["published_charging_point_count"]),
                    fmt_int(infrastructure_totals["published_normal_point_count"]),
                    fmt_int(infrastructure_totals["published_fast_point_count"]),
                    fmt_int(infrastructure_totals["published_points_ge_150"]),
                    fmt_int(infrastructure_totals["published_points_ge_350"]),
                    fmt_num(infrastructure_totals["published_equipment_nominal_power_mw"], 4),
                    "Observed BNetzA snapshot; all statuses retained",
                ],
                [
                    "Retrospective September-survivor cohort (commissioned <= 2026-07-01)",
                    fmt_int(infrastructure_totals["survivor_equipment_count"]),
                    fmt_int(infrastructure_totals["survivor_charging_point_count"]),
                    fmt_int(infrastructure_totals["survivor_normal_point_count"]),
                    fmt_int(infrastructure_totals["survivor_fast_point_count"]),
                    fmt_int(infrastructure_totals["survivor_points_ge_150"]),
                    fmt_int(infrastructure_totals["survivor_points_ge_350"]),
                    fmt_num(infrastructure_totals["survivor_equipment_nominal_power_mw"], 4),
                    "September status retained; not July operational status",
                ],
                [
                    "Post-cutoff complement (commissioned > 2026-07-01)",
                    fmt_int(infrastructure_totals["later_equipment_count"]),
                    fmt_int(infrastructure_totals["later_charging_point_count"]),
                    fmt_int(infrastructure_totals["later_normal_point_count"]),
                    fmt_int(infrastructure_totals["later_fast_point_count"]),
                    fmt_int(infrastructure_totals["later_points_ge_150"]),
                    fmt_int(infrastructure_totals["later_points_ge_350"]),
                    fmt_num(float(infrastructure_totals["published_equipment_nominal_power_mw"]) - float(infrastructure_totals["survivor_equipment_nominal_power_mw"]), 4),
                    "All currently In Betrieb in this snapshot; not proof of July absence/accessibility",
                ],
            ],
        ),
        "",
        "The survivor calculation uses only equipment present in the September source and keeps their currently reported point rows. Equipment removed before September is absent; point slots may have been added or modified after commissioning; the September status does not establish July operation; and no historical opening-hours or availability state can be reconstructed. The cohort is neither a mathematical upper nor lower bound on actual July infrastructure.",
        "",
        "The commissioning-date quality is sufficient for a reproducible equipment-level survivor calculation in this snapshot, but it is not sufficient to reconstruct point-level historical existence, activation, accessibility or operational status.",
        "",
        "## 5. Published snapshot KPI results",
        "",
        "Perspective A uses the July KBA vehicle denominator and the full September BNetzA infrastructure denominator. It is a descriptive cross-snapshot comparison, not a same-day infrastructure adequacy measure.",
        "",
        *markdown_table(
            ["State", "BEV stock", "Sep points", "Fast", ">=150", ">=350", "BEVs/point", "Points/1,000 BEVs", "Fast/1,000 BEVs"],
            [
                [
                    row["state_name"],
                    fmt_int(row["bev_stock"]),
                    fmt_int(row["published_charging_point_count"]),
                    fmt_int(row["published_fast_point_count"]),
                    fmt_int(row["published_points_ge_150"]),
                    fmt_int(row["published_points_ge_350"]),
                    fmt_num(row["published_bevs_per_point"], 2),
                    fmt_num(row["published_points_per_1000_bevs"], 2),
                    fmt_num(row["published_fast_points_per_1000_bevs"], 2),
                ]
                for row in state_rows
            ],
        ),
        "",
        "The published point counts are current September register rows. Equipment count, point count, connector count, status, nominal power and operational availability remain different concepts; the point denominator does not explode connector text.",
        "",
        "## 6. Retrospective survivor-cohort results",
        "",
        "Perspective B retains September point rows attached to equipment commissioned on or before 2026-07-01. It is useful only as a transparent sensitivity analysis of retrospective selection, not as a true July snapshot.",
        "",
        *markdown_table(
            ["State", "Survivor equipment", "Survivor points", "Fast", ">=150", ">=350", "BEVs/point", "Points/1,000 BEVs", "Fast/1,000 BEVs"],
            [
                [
                    row["state_name"],
                    fmt_int(row["survivor_equipment_count"]),
                    fmt_int(row["survivor_charging_point_count"]),
                    fmt_int(row["survivor_fast_point_count"]),
                    fmt_int(row["survivor_points_ge_150"]),
                    fmt_int(row["survivor_points_ge_350"]),
                    fmt_num(row["survivor_bevs_per_point"], 2),
                    fmt_num(row["survivor_points_per_1000_bevs"], 2),
                    fmt_num(row["survivor_fast_points_per_1000_bevs"], 2),
                ]
                for row in state_rows
            ],
        ),
        "",
        "A point associated with an equipment record commissioned before July is not proof that that same point existed, was accessible, or was operational in July. The cohort should not be labelled `July infrastructure` in Tableau or future extracts.",
        "",
        "## 7. State-level sensitivity comparisons",
        "",
        *markdown_table(
            ["State", "BEV", "Sep points", "Survivor points", "Point difference", "Fast difference", ">=150 difference", ">=350 difference", "BEVs/point Sep", "BEVs/point survivor", "% ratio change", "Rank Sep→survivor"],
            [
                [
                    row["state_name"],
                    fmt_int(row["bev_stock"]),
                    fmt_int(row["published_charging_point_count"]),
                    fmt_int(row["survivor_charging_point_count"]),
                    fmt_int(row["published_minus_survivor_charging_point_count"]),
                    fmt_int(row["published_minus_survivor_fast_point_count"]),
                    fmt_int(row["published_minus_survivor_points_ge_150"]),
                    fmt_int(row["published_minus_survivor_points_ge_350"]),
                    fmt_num(row["published_bevs_per_point"], 3),
                    fmt_num(row["survivor_bevs_per_point"], 3),
                    fmt_signed_pct(row["survivor_minus_published_bevs_per_point_pct"]),
                    f"{row['published_bevs_per_point_rank']} → {row['survivor_bevs_per_point_rank']} ({fmt_signed(row['bevs_per_point_rank_change_survivor_minus_published'], 0)})",
                ]
                for row in state_rows
            ],
        ),
        "",
        f"Differences in the table are **published September minus survivor cohort** for counts and **survivor minus published** for ratios. The survivor cohort removes {fmt_int(infrastructure_totals['later_charging_point_count'])} point rows nationally, including {fmt_int(infrastructure_totals['later_fast_point_count'])} fast, {fmt_int(infrastructure_totals['later_points_ge_150'])} >=150 kW and {fmt_int(infrastructure_totals['later_points_ge_350'])} >=350 kW point rows.",
        "",
        "## 8. Rankings and outlier stability",
        "",
        *markdown_table(
            ["Metric", "Published lowest", "Survivor lowest", "Low stable", "Published highest", "Survivor highest", "High stable"],
            [
                [
                    row["metric"],
                    f"{row['published_low_state']} ({fmt_num(row['published_low_value'], 2)})",
                    f"{row['survivor_low_state']} ({fmt_num(row['survivor_low_value'], 2)})",
                    "yes" if row["low_state_stable"] else "no",
                    f"{row['published_high_state']} ({fmt_num(row['published_high_value'], 2)})",
                    f"{row['survivor_high_state']} ({fmt_num(row['survivor_high_value'], 2)})",
                    "yes" if row["high_state_stable"] else "no",
                ]
                for row in ranking_rows
            ],
        ),
        "",
        f"The BEVs-per-point ranking changes for {changed_bev_rank} of 16 states; the fast-points-per-1,000-BEVs ranking changes for {changed_fast_rank} of 16 states. Rank stability is empirical descriptive evidence only; it does not establish that the retrospective cohort matches July infrastructure or that the ratio measures adequacy.",
        "",
        "Important outlier interpretation: state size, denominator size, register coverage and declared-power composition can drive the extremes. A high or low ratio is not evidence of shortage, surplus, accessibility, demand or quality.",
        "",
        "## 9. Sources of retrospective selection bias",
        "",
        "- The September source contains only equipment still represented in the September register; equipment removed before September cannot be recovered.",
        "- Equipment commissioning date is equipment-level. The current point table has no individual point activation date, and later point additions or modifications cannot be separated from the equipment row using this snapshot alone.",
        "- September addresses, declared characteristics and status labels are carried into the cohort; they are not historical July observations.",
        "- The after-cutoff share is geographically uneven in absolute counts: Nordrhein-Westfalen and Bayern contribute the largest later point counts, followed by Niedersachsen. This is a distribution finding, not a causal explanation.",
        "- The register is not an exhaustive census of all publicly accessible charging infrastructure, so a cohort within the register cannot measure total public availability.",
        "",
        "## 10. Unsupported historical interpretations",
        "",
        "The following interpretations are not supported by the current data:",
        "",
        "- Treating the September published register as if it were observed on 2026-07-01.",
        "- Calling the survivor cohort a true July snapshot, a guaranteed upper/lower bound, or observed infrastructure growth from July to September.",
        "- Inferring point-level activation, opening date, July operational status, historical opening hours, uptime, queue time, utilization, sessions, energy delivery, or simultaneous deliverable power.",
        "- Interpreting the January/April fixed-denominator illustration as January/April infrastructure. It changes the KBA vehicle numerator while intentionally holding the September denominator fixed.",
        "- Interpreting stock changes as new registrations or sales, or assigning causal explanations to state differences without additional approved evidence.",
        "",
        "## 11. Evaluation of candidate Tableau KPIs",
        "",
        "The decisions below use the requested statuses `HEADLINE_READY_WITH_DATES`, `CONTEXT_ONLY`, `EXPLORATORY_SENSITIVITY` and `NOT_SUPPORTED`. No cross-source ratio is promoted to a same-day adequacy metric. The observed single-source counts remain valid with their source dates, but that does not transfer to a demand or adequacy interpretation.",
        "",
        *markdown_table(
            ["KPI", "Status", "Temporal validity", "Recommended visualization", "Required label / key evidence"],
            [
                [
                    row["kpi_name"],
                    row["publication_status"],
                    row["temporal_validity"],
                    row["recommended_visualization"],
                    row["required_explanatory_label"],
                ]
                for row in decisions
            ],
        ),
        "",
        "BEVs-per-point decision: show, if at all, as a **secondary contextual KPI**, with both dates and the 16-state denominator scope exposed. Do not show it as a headline tile, adequacy gauge, service standard or red/green state classification. The survivor comparison belongs in an exploratory sensitivity view.",
        "",
        "## 12. Recommended chart labels and warning notes",
        "",
        "Recommended published-snapshot label:",
        "",
        "> CROSS-SNAPSHOT DESCRIPTIVE COMPARISON — Registered BEVs at 2026-07-01 / BNetzA charging points published at 2026-09-30. Not a same-day infrastructure adequacy measure.",
        "",
        "Recommended survivor label:",
        "",
        "> RETROSPECTIVE SEPTEMBER-SURVIVOR COHORT — NOT ACTUAL JULY INFRASTRUCTURE. Equipment present in the 2026-09-30 register with commissioning date <= 2026-07-01; current September point rows retained.",
        "",
        "Recommended warning note:",
        "",
        "> Commissioning date is equipment-level; point activation date and historical availability are unavailable. Counts use point slots, not connector counts. Maximum declared power is a source classification, not utilization or simultaneous deliverable power. KBA values are registered stock, not demand or sales.",
        "",
        "## 13. National and regional reconciliation",
        "",
        *markdown_table(
            ["Scope", "KBA reference", "KBA BEV", "KBA PHEV", "Equipment", "Points", "BEVs/point", "Reconciliation"],
            [
                ["Published Deutschland KBA row", KBA_PRIMARY_REFERENCE_DATE, fmt_int(july["national"]["bev_stock"]), fmt_int(july["national"]["phev_stock"]), "—", "—", "—", "PASS — includes Sonstige"],
                ["16-state KBA sum", KBA_PRIMARY_REFERENCE_DATE, fmt_int(july["sixteen_state_sum"]["bev_stock"]), fmt_int(july["sixteen_state_sum"]["phev_stock"]), "—", "—", "—", "PASS — comparable vehicle scope"],
                ["Sonstige KBA row", KBA_PRIMARY_REFERENCE_DATE, fmt_int(july["sonstige"]["bev_stock"]), fmt_int(july["sonstige"]["phev_stock"]), "—", "—", "—", "PASS — residual, not a state"],
                ["400 KBA registration regions", KBA_PRIMARY_REFERENCE_DATE, fmt_int(july["four_hundred_region_sum"]["bev_stock"]), fmt_int(july["four_hundred_region_sum"]["phev_stock"]), "—", "—", "—", "PASS — equals 16-state sum"],
                ["Published September infrastructure", "—", "—", "—", fmt_int(infrastructure_totals["published_equipment_count"]), fmt_int(infrastructure_totals["published_charging_point_count"]), fmt_num(published_ratio, 6), "PASS — all 16 states"],
                ["Survivor cohort infrastructure", "—", "—", "—", fmt_int(infrastructure_totals["survivor_equipment_count"]), fmt_int(infrastructure_totals["survivor_charging_point_count"]), fmt_num(survivor_ratio, 6), "PASS — reconstructed sensitivity only"],
            ],
        ),
        "",
        f"The July national relationship is exact: Deutschland = 16 named states + Sonstige for passenger cars, BEVs and PHEVs. The 400-region KBA total equals the 16-state sum. The published BNetzA infrastructure total is {fmt_int(infrastructure_totals['published_equipment_count'])} equipment and {fmt_int(infrastructure_totals['published_charging_point_count'])} points; the survivor total is kept separate and is never added to the published total.",
        "",
        "### Vehicle-stock sensitivity with a fixed September denominator",
        "",
        *markdown_table(
            ["KBA date", "Scope", "BEV stock", "Fixed Sep points", "BEVs/fixed Sep point", "Fixed Sep points/1,000 BEVs"],
            [
                [row["kba_reference_date"], row["kba_scope"], fmt_int(row["bev_stock"]), fmt_int(row["infrastructure_denominator"]), fmt_num(row["bevs_per_fixed_september_point"], 6), fmt_num(row["fixed_september_points_per_1000_bevs"], 6)]
                for row in fixed_denominator_rows
            ],
        ),
        "",
        "This is a vehicle-numerator sensitivity illustration only. The September point denominator is held fixed to show how KBA stock date changes the ratio; it must not be narrated as observed unchanged infrastructure in January or April.",
        "",
        "## 14. Validation evidence",
        "",
        *markdown_table(
            ["Check", "Result"],
            [
                ["DuckDB access", "PASS — opened with read_only=True; no DDL/DML issued"],
                ["Database contract", f"PASS — {len(database_contract['objects'])} required base tables and commissioning/point/KBA columns present"],
                ["Source fingerprints", f"PASS — {len(fingerprints)} preserved workbook/reference fingerprints match"],
                ["BNetzA baseline", f"PASS — {fmt_int(infrastructure_totals['published_equipment_count'])} equipment; {fmt_int(infrastructure_totals['published_charging_point_count'])} points; power bands and {fmt_num(infrastructure_totals['published_equipment_nominal_power_mw'], 4)} MW match"],
                ["Commissioning-date parsing", f"PASS — {fmt_int(quality['parsing_failures'])} failures; {fmt_int(quality['parsed_null'])} parsed NULL; {fmt_int(quality['after_snapshot'])} future dates"],
                ["Cutoff boundary", f"PASS — {fmt_int(quality['exactly_on_cutoff'])} equipment records on 2026-07-01 included; published = survivor + post-cutoff"],
                ["Point integrity", f"PASS — {fmt_int(quality['duplicate_point_identities'])} duplicate point keys; {fmt_int(quality['orphan_point_rows'])} orphan points; {fmt_int(quality['equipment_point_mismatches'])} equipment/point mismatches"],
                ["Power-band denominator", f"PASS — {fmt_int(infrastructure_totals['published_invalid_power_points'])} invalid-power points; normal + fast + unknown = total"],
                ["KBA dates", "PASS — January, April and July each have 18 × 7 state-fuel rows and 400 district rows"],
                ["KBA July reconciliation", f"PASS — Deutschland = 16 states + Sonstige; 400-region BEV total = {fmt_int(july['four_hundred_region_sum']['bev_stock'])} = 16-state total"],
                ["Vehicle denominator", "PASS — six mutually exclusive fuel rows form passenger-car total; PHEV remains nested detail"],
                ["State join", "PASS — exactly 16 states; one vehicle row and one infrastructure row per state before joining"],
                ["Date labels", "PASS — both source dates and both perspective labels are carried into outputs"],
                ["Database immutability", f"PASS — start/end SHA-256 {database_sha256}"],
                ["Ratio safety", "PASS — NULL/zero denominators return blank; no zero denominators in current state rows"],
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
        "## 15. Recommended next analytical step",
        "",
        "If the owner wants a stronger temporal KPI, obtain or approve a genuinely dated infrastructure panel with historical point/equipment identity, activation/retirement semantics and operational availability fields, then pair it with a compatible KBA stock date. Until then, keep the published cross-snapshot comparison contextual and the survivor cohort exploratory. Do not begin Tableau development or Batch 18 without owner approval.",
        "",
        "## Reproducible outputs",
        "",
        "- [`scripts/17_analyze_temporal_kpi_validity.py`](../scripts/17_analyze_temporal_kpi_validity.py)",
        "- [`batch17_temporal_kpi_validity.md`](batch17_temporal_kpi_validity.md)",
        "- [`batch17_equipment_commissioning_cohorts.csv`](batch17_equipment_commissioning_cohorts.csv)",
        "- [`batch17_state_temporal_sensitivity.csv`](batch17_state_temporal_sensitivity.csv)",
        "- [`batch17_kpi_publication_decisions.csv`](batch17_kpi_publication_decisions.csv)",
        "- [`batch17_vehicle_stock_denominator_sensitivity.csv`](batch17_vehicle_stock_denominator_sensitivity.csv)",
        "",
        "Run from the repository root:",
        "",
        "```bash",
        ".venv/bin/python scripts/17_analyze_temporal_kpi_validity.py --json",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the read-only Batch 17 temporal KPI validity analysis")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--json", action="store_true", help="Print a compact JSON-like completion summary")
    args = parser.parse_args()

    database = resolve_path(args.database)
    report_path = resolve_path(args.report)
    output_dir = resolve_path(args.output_dir)
    require(database.is_file(), f"Missing DuckDB database: {database}")
    database_before_sha256 = sha256(database)
    fingerprints_before = fingerprint_sources()

    conn = duckdb.connect(str(database), read_only=True)
    try:
        database_contract = validate_database_contract(conn)
        snapshots: Dict[str, Dict[str, Any]] = {}
        for source_id, reference_date in KBA_SNAPSHOT_SPECS:
            snapshots[reference_date] = load_kba_snapshot(
                conn,
                source_id,
                reference_date,
                validate_july_expected=reference_date == KBA_PRIMARY_REFERENCE_DATE,
            )
        infrastructure_rows, infrastructure_totals, quality_rows = load_infrastructure(conn)
        quality = quality_rows[0]
        distribution_rows = commissioning_distribution(conn)
        status_rows = status_distribution(conn)
    finally:
        conn.close()

    database_after_sha256 = sha256(database)
    require(database_after_sha256 == database_before_sha256, "DuckDB file changed during read-only analysis")
    fingerprints_after = fingerprint_sources()
    require(
        [(row["path"], row["actual_sha256"]) for row in fingerprints_before]
        == [(row["path"], row["actual_sha256"]) for row in fingerprints_after],
        "Source fingerprint changed during analysis",
    )

    state_rows = build_state_sensitivity(snapshots[KBA_PRIMARY_REFERENCE_DATE], infrastructure_rows)
    ranking_rows = ranking_summary(state_rows)
    decisions = kpi_decisions(state_rows, infrastructure_totals, ranking_rows)
    fixed_denominator_rows = fixed_denominator_sensitivity(
        snapshots,
        int(infrastructure_totals["published_charging_point_count"]),
    )

    cohort_rows: List[Dict[str, Any]] = []
    perspective_specs = (
        (
            "PERSPECTIVE_TOTAL",
            "PUBLISHED_SEPTEMBER_SNAPSHOT",
            infrastructure_totals["published_equipment_count"],
            infrastructure_totals["published_charging_point_count"],
            infrastructure_totals["published_declared_point_count"],
            infrastructure_totals["published_normal_point_count"],
            infrastructure_totals["published_fast_point_count"],
            infrastructure_totals["published_points_ge_150"],
            infrastructure_totals["published_points_ge_350"],
            infrastructure_totals["published_invalid_power_points"],
        ),
        (
            "PERSPECTIVE_TOTAL",
            "RETROSPECTIVE_SEPTEMBER_SURVIVOR_COHORT__COMMISSIONED_ON_OR_BEFORE_2026-07-01",
            infrastructure_totals["survivor_equipment_count"],
            infrastructure_totals["survivor_charging_point_count"],
            infrastructure_totals["survivor_declared_point_count"],
            infrastructure_totals["survivor_normal_point_count"],
            infrastructure_totals["survivor_fast_point_count"],
            infrastructure_totals["survivor_points_ge_150"],
            infrastructure_totals["survivor_points_ge_350"],
            infrastructure_totals["survivor_invalid_power_points"],
        ),
        (
            "PERSPECTIVE_TOTAL",
            "POST_CUTOFF_COMPLEMENT__COMMISSIONED_AFTER_2026-07-01",
            infrastructure_totals["later_equipment_count"],
            infrastructure_totals["later_charging_point_count"],
            infrastructure_totals["later_charging_point_count"],
            infrastructure_totals["later_normal_point_count"],
            infrastructure_totals["later_fast_point_count"],
            infrastructure_totals["later_points_ge_150"],
            infrastructure_totals["later_points_ge_350"],
            infrastructure_totals["later_invalid_power_points"],
        ),
    )
    for scope_type, label, equipment_count, point_count, declared_count, normal, fast, ge150, ge350, invalid in perspective_specs:
        cohort_rows.append(
            {
                "distribution_type": scope_type,
                "period": label,
                "state_name": "",
                "status": "",
                "equipment_count": equipment_count,
                "charging_point_count": point_count,
                "declared_point_count": declared_count,
                "normal_point_count": normal,
                "fast_point_count": fast,
                "points_ge_150": ge150,
                "points_ge_350": ge350,
                "invalid_power_points": invalid,
                "cutoff_date": KBA_SURVIVOR_CUTOFF_DATE,
                "note": "Published September snapshot, survivor cohort, or complement as labelled; survivor is not actual July infrastructure.",
            }
        )
    for row in distribution_rows:
        cohort_rows.append(
            {
                **row,
                "cutoff_date": KBA_SURVIVOR_CUTOFF_DATE,
                "note": "Equipment and currently associated point rows grouped by parsed commissioning year/month.",
            }
        )
    for row in status_rows:
        cohort_rows.append(
            {
                **row,
                "cutoff_date": KBA_SURVIVOR_CUTOFF_DATE,
                "note": "Equipment status observed in September; no status filter applied.",
            }
        )
    for row in state_rows:
        cohort_rows.append(
            {
                "distribution_type": "STATE_POST_CUTOFF",
                "period": "",
                "state_name": row["state_name"],
                "status": "",
                "equipment_count": row["later_equipment_count"],
                "charging_point_count": row["later_charging_point_count"],
                "declared_point_count": row["later_charging_point_count"],
                "normal_point_count": row["later_normal_point_count"] if "later_normal_point_count" in row else None,
                "fast_point_count": row["later_fast_point_count"],
                "points_ge_150": row["later_points_ge_150"],
                "points_ge_350": row["later_points_ge_350"],
                "invalid_power_points": row["later_invalid_power_points"] if "later_invalid_power_points" in row else None,
                "cutoff_date": KBA_SURVIVOR_CUTOFF_DATE,
                "note": "Later-commissioned state distribution; all September statuses retained.",
            }
        )

    cohort_fields = [
        "distribution_type",
        "period",
        "state_name",
        "status",
        "equipment_count",
        "charging_point_count",
        "declared_point_count",
        "normal_point_count",
        "fast_point_count",
        "points_ge_150",
        "points_ge_350",
        "invalid_power_points",
        "survivor_equipment_count",
        "survivor_declared_point_count",
        "later_equipment_count",
        "later_declared_point_count",
        "cutoff_date",
        "note",
    ]
    state_fields = [
        "state_name",
        "kba_reference_date",
        "bnetza_reference_date",
        "survivor_cutoff_date",
        "bev_stock",
        "phev_stock",
        "passenger_car_stock",
        "bev_penetration_pct",
        "bev_stock_share_of_16_state_stock_pct",
        "published_equipment_count",
        "published_charging_point_count",
        "published_normal_point_count",
        "published_fast_point_count",
        "published_points_ge_150",
        "published_points_ge_350",
        "published_fast_point_share_pct",
        "published_points_ge_150_share_pct",
        "published_points_ge_350_share_pct",
        "published_equipment_nominal_power_mw",
        "published_point_share_of_16_state_points_pct",
        "survivor_equipment_count",
        "survivor_charging_point_count",
        "survivor_normal_point_count",
        "survivor_fast_point_count",
        "survivor_points_ge_150",
        "survivor_points_ge_350",
        "survivor_fast_point_share_pct",
        "survivor_points_ge_150_share_pct",
        "survivor_points_ge_350_share_pct",
        "survivor_equipment_nominal_power_mw",
        "published_bevs_per_point",
        "survivor_bevs_per_point",
        "published_points_per_1000_bevs",
        "survivor_points_per_1000_bevs",
        "published_fast_points_per_1000_bevs",
        "survivor_fast_points_per_1000_bevs",
        "published_ge150_points_per_1000_bevs",
        "survivor_ge150_points_per_1000_bevs",
        "published_ge350_points_per_1000_bevs",
        "survivor_ge350_points_per_1000_bevs",
        "later_equipment_count",
        "later_charging_point_count",
        "later_normal_point_count",
        "later_fast_point_count",
        "later_points_ge_150",
        "later_points_ge_350",
        "later_invalid_power_points",
        "later_point_share_of_state_published_pct",
        "published_minus_survivor_equipment_count",
        "published_minus_survivor_charging_point_count",
        "published_minus_survivor_fast_point_count",
        "published_minus_survivor_points_ge_150",
        "published_minus_survivor_points_ge_350",
        "survivor_minus_published_bevs_per_point",
        "survivor_minus_published_bevs_per_point_pct",
        "survivor_minus_published_points_per_1000_bevs",
        "survivor_minus_published_points_per_1000_bevs_pct",
        "survivor_minus_published_fast_points_per_1000_bevs",
        "survivor_minus_published_fast_points_per_1000_bevs_pct",
        "survivor_minus_published_ge150_points_per_1000_bevs",
        "survivor_minus_published_ge150_points_per_1000_bevs_pct",
        "survivor_minus_published_ge350_points_per_1000_bevs",
        "survivor_minus_published_ge350_points_per_1000_bevs_pct",
        "survivor_minus_published_fast_point_share_pp",
        "published_bevs_per_point_rank",
        "survivor_bevs_per_point_rank",
        "bevs_per_point_rank_change_survivor_minus_published",
        "published_fast_points_per_1000_rank",
        "survivor_fast_points_per_1000_rank",
        "fast_points_per_1000_rank_change_survivor_minus_published",
        "published_ge150_points_per_1000_rank",
        "survivor_ge150_points_per_1000_rank",
        "ge150_points_per_1000_rank_change_survivor_minus_published",
        "published_ge350_points_per_1000_rank",
        "survivor_ge350_points_per_1000_rank",
        "ge350_points_per_1000_rank_change_survivor_minus_published",
        "status_labels",
        "temporal_label_published",
        "temporal_label_survivor",
    ]
    decision_fields = [
        "kpi_name",
        "publication_status",
        "formula",
        "numerator",
        "denominator",
        "geographic_grain",
        "vehicle_reference_date",
        "infrastructure_reference_date",
        "temporal_validity",
        "observed_or_reconstructed_status",
        "published_snapshot_sensitivity",
        "risk_of_misinterpretation",
        "recommended_visualization",
        "required_explanatory_label",
        "recommendation",
        "evidence",
    ]
    fixed_fields = [
        "kba_source_id",
        "kba_reference_date",
        "infrastructure_reference_date",
        "infrastructure_denominator",
        "kba_scope",
        "bev_stock",
        "bevs_per_fixed_september_point",
        "fixed_september_points_per_1000_bevs",
        "interpretation_label",
    ]

    write_csv(output_dir / "batch17_equipment_commissioning_cohorts.csv", cohort_fields, cohort_rows)
    write_csv(output_dir / "batch17_state_temporal_sensitivity.csv", state_fields, state_rows)
    write_csv(output_dir / "batch17_kpi_publication_decisions.csv", decision_fields, decisions)
    write_csv(output_dir / "batch17_vehicle_stock_denominator_sensitivity.csv", fixed_fields, fixed_denominator_rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_report(
            database,
            database_before_sha256,
            fingerprints_before,
            database_contract,
            snapshots,
            infrastructure_rows,
            infrastructure_totals,
            quality,
            distribution_rows,
            status_rows,
            state_rows,
            ranking_rows,
            decisions,
            fixed_denominator_rows,
        ),
        encoding="utf-8",
    )

    summary = {
        "status": "PASS",
        "database": relative_label(database),
        "report": relative_label(report_path),
        "outputs": [
            relative_label(output_dir / "batch17_equipment_commissioning_cohorts.csv"),
            relative_label(output_dir / "batch17_state_temporal_sensitivity.csv"),
            relative_label(output_dir / "batch17_kpi_publication_decisions.csv"),
            relative_label(output_dir / "batch17_vehicle_stock_denominator_sensitivity.csv"),
        ],
        "state_rows": len(state_rows),
        "commissioning_quality": quality,
        "published_infrastructure_totals": infrastructure_totals,
        "july_kba": snapshots[KBA_PRIMARY_REFERENCE_DATE]["national"],
        "july_kba_sixteen_state": snapshots[KBA_PRIMARY_REFERENCE_DATE]["sixteen_state_sum"],
        "july_kba_sonstige": snapshots[KBA_PRIMARY_REFERENCE_DATE]["sonstige"],
        "database_sha256": database_after_sha256,
        "source_fingerprints_match": all(bool(row["match"]) for row in fingerprints_before),
    }
    if args.json:
        import json

        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    else:
        print("Batch 17 analysis PASS")
        print(f"Report: {summary['report']}")
        print(f"State rows: {summary['state_rows']}")
        print(f"Database SHA-256: {summary['database_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AnalysisError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
