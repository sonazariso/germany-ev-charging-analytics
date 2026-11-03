#!/usr/bin/env python3
"""Analyze charging infrastructure patterns in the harmonized BBSR layer.

Batch 14 is a read-only statistical analysis.  Its primary inputs are the
Batch 13.2 historical BBSR target-unit and type-summary views:

    analytics.charging_by_bbsr_district_2025_harmonized
    analytics.charging_by_bbsr_type_2025_harmonized

The script deliberately does not create, replace, or mutate DuckDB objects.
It validates the harmonized layer against the current BNetzA source totals,
calculates category and district descriptive statistics, writes two
diagnostic CSVs, and renders the analytical report.

Run from the repository root::

    .venv/bin/python scripts/14_analyze_bbsr_charging_patterns.py --json

The output is deterministic for a fixed database and fixed reference files;
no run timestamp is written to the report or CSVs.
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
DEFAULT_REPORT = ROOT / "reports/batch14_bbsr_charging_analysis.md"
DEFAULT_TYPE_CSV = ROOT / "reports/batch14_bbsr_type_metrics.csv"
DEFAULT_DISTRICT_CSV = ROOT / "reports/batch14_bbsr_district_metrics.csv"

SOURCE_ID = "bnetza_charging_2026_09_30"
INFRASTRUCTURE_REFERENCE_DATE = "2026-09-30"
BBSR_REFERENCE_DATE = "2025-12-31"
HARMONIZATION_VERSION = "batch13.2-2026-11-02-bbsr-2025-historical-boundary"
MIN_SHARE_POINTS = 30

DISTRICT_VIEW = "analytics.charging_by_bbsr_district_2025_harmonized"
TYPE_VIEW = "analytics.charging_by_bbsr_type_2025_harmonized"

CATEGORY_LABELS = {
    "1": "kreisfreie Großstadt",
    "2": "städtischer Kreis",
    "3": "ländlicher Kreis mit Verdichtungsansätzen",
    "4": "dünn besiedelter ländlicher Kreis",
}
CATEGORY_ORDER = ("1", "2", "3", "4")

EXPECTED = {
    "equipment": 117_662,
    "points": 211_253,
    "normal_points": 156_155,
    "fast_points": 55_098,
    "points_ge_150": 40_950,
    "points_ge_350": 6_950,
    "unclassifiable_points": 0,
    "historical_units": 400,
    "source_components": 401,
    "nominal_power_mw": 9_215.4173,
}
EXPECTED_CATEGORY_UNITS = {"1": 68, "2": 131, "3": 98, "4": 103}

# These fingerprints are part of the Batch 13.2 evidence chain.  The current
# analysis may read these files for provenance, but it never uses them as a
# substitute for the deployed harmonized analytical views.
EXPECTED_FINGERPRINTS = {
    "data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx": (
        "1e82c1734b17e17e51092a0f9460a5e204888569fb12aa5940b30e9cdb726342",
        "BNetzA source workbook",
    ),
    "data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx": (
        "083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525",
        "BBSR raw reference workbook",
    ),
    "data/reference/bbsr_settlement_types_2025.csv": (
        "e35c57da8d8f675fa132b629e6dda43180a18e5b78b95e1e72de30069a062e65",
        "BBSR derived four-category reference",
    ),
    "data/reference/bnetza_bbsr_historical_harmonization_2025.csv": (
        "26b7b177b11f19628d85c7195975d75232804567b43d964f99acb8fcd8f84661",
        "Batch 13.2 source-component harmonization reference",
    ),
}

REQUIRED_DISTRICT_COLUMNS = {
    "harmonization_version",
    "analysis_source_vintage",
    "infrastructure_reference_date",
    "historical_bbsr_reference_date",
    "historical_bbsr_source_version",
    "historical_bbsr_source_sha256",
    "historical_bbsr_administrative_district_code",
    "historical_bbsr_administrative_district_name",
    "historical_bbsr_federal_state_code",
    "historical_bbsr_federal_state_name",
    "historical_bbsr_kreisregion_code",
    "historical_bbsr_kreisregion_name",
    "historical_bbsr_settlement_type_code",
    "historical_bbsr_settlement_type_name_de",
    "historical_boundary_basis",
    "source_component_count",
    "source_component_names",
    "mapping_method",
    "boundary_compatibility_status",
    "evidence_source_reference",
    "validation_notes",
    "equipment_count",
    "charging_point_count",
    "declared_charging_point_count",
    "normal_charging_point_count",
    "fast_charging_point_count",
    "points_ge_150_kw",
    "points_ge_350_kw",
    "unclassifiable_power_point_count",
    "fast_point_share_pct",
    "high_power_point_share_pct",
    "total_equipment_nominal_power_kw",
    "total_equipment_nominal_power_mw",
    "equipment_statuses_present",
}
REQUIRED_TYPE_COLUMNS = {
    "harmonization_version",
    "analysis_source_vintage",
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
    "unclassifiable_power_point_count",
    "fast_charging_share_pct",
    "high_power_share_pct",
    "declared_equipment_nominal_power_kw",
    "declared_equipment_nominal_power_mw",
    "national_charging_point_share_pct",
    "all_historical_district_count",
    "all_source_component_count",
    "classification_scope",
    "point_share_denominator_scope",
}

DISTRICT_NUMERIC_FIELDS = (
    "source_component_count",
    "equipment_count",
    "charging_point_count",
    "declared_charging_point_count",
    "normal_charging_point_count",
    "fast_charging_point_count",
    "points_ge_150_kw",
    "points_ge_350_kw",
    "unclassifiable_power_point_count",
    "fast_point_share_pct",
    "high_power_point_share_pct",
    "total_equipment_nominal_power_kw",
    "total_equipment_nominal_power_mw",
)

TYPE_NUMERIC_FIELDS = (
    "historical_district_count",
    "source_component_count",
    "equipment_count",
    "charging_point_count",
    "normal_charging_point_count",
    "fast_charging_point_count",
    "points_ge_150_kw",
    "points_ge_350_kw",
    "unclassifiable_power_point_count",
    "fast_charging_share_pct",
    "high_power_share_pct",
    "declared_equipment_nominal_power_kw",
    "declared_equipment_nominal_power_mw",
    "national_charging_point_share_pct",
    "all_historical_district_count",
    "all_source_component_count",
)


class AnalysisError(RuntimeError):
    """Raised when the read-only Batch 14 analysis cannot be validated."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisError(message)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_default(value: Any) -> str:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return str(value)


def as_int(value: Any) -> int:
    require(value is not None, "Unexpected NULL in an integer metric")
    return int(value)


def as_float(value: Any) -> float:
    require(value is not None, "Unexpected NULL in a numeric metric")
    return float(value)


def pct(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0:
        return None
    return 100.0 * numerator / denominator


def ratio(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0:
        return None
    return numerator / denominator


def fmt(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.{decimals}f}"
    return str(value)


def fmt_pct(value: Optional[float], decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}%"


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


def columns(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> List[str]:
    return [row[0] for row in conn.execute(f"DESCRIBE {qualified_name}").fetchall()]


def query_dicts(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: Sequence[Any] = (),
) -> List[Dict[str, Any]]:
    result = conn.execute(sql, params)
    names = [item[0] for item in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


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
    require(row is not None and row[0], f"Could not read SQL for {qualified_name}")
    return str(row[0])


def fingerprint_files() -> List[Dict[str, Any]]:
    result = []
    for relative, (expected, purpose) in EXPECTED_FINGERPRINTS.items():
        path = ROOT / relative
        require(path.is_file(), f"Missing fingerprint source: {relative}")
        actual = sha256(path)
        result.append(
            {
                "path": relative,
                "purpose": purpose,
                "bytes": path.stat().st_size,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "match": actual == expected,
            }
        )
        require(actual == expected, f"Source fingerprint changed: {relative}")
    return result


def quantile(values: Sequence[float], probability: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def distribution(values: Sequence[float]) -> Dict[str, Optional[float]]:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not clean:
        return {
            "min": None,
            "p10": None,
            "median": None,
            "mean": None,
            "p90": None,
            "max": None,
            "stddev": None,
            "mean_median_ratio": None,
            "count": 0,
        }
    median_value = statistics.median(clean)
    mean_value = statistics.mean(clean)
    return {
        "min": min(clean),
        "p10": quantile(clean, 0.10),
        "median": median_value,
        "mean": mean_value,
        "p90": quantile(clean, 0.90),
        "max": max(clean),
        "stddev": statistics.pstdev(clean) if len(clean) > 1 else 0.0,
        "mean_median_ratio": (mean_value / median_value) if median_value else None,
        "count": len(clean),
    }


def numeric_row(row: Mapping[str, Any], fields: Iterable[str]) -> Dict[str, Any]:
    result = dict(row)
    for field in fields:
        value = result.get(field)
        if field.endswith("_count") or field in {
            "source_component_count",
            "equipment_count",
            "charging_point_count",
            "declared_charging_point_count",
            "normal_charging_point_count",
            "fast_charging_point_count",
            "points_ge_150_kw",
            "points_ge_350_kw",
            "unclassifiable_power_point_count",
            "historical_district_count",
            "all_historical_district_count",
            "all_source_component_count",
        }:
            result[field] = as_int(value)
        elif value is not None:
            result[field] = as_float(value)
    return result


def validate_view_contract(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    for name in (DISTRICT_VIEW, TYPE_VIEW):
        require(table_type(conn, name) == "VIEW", f"Required object is not a view: {name}")
    district_columns = set(columns(conn, DISTRICT_VIEW))
    type_columns = set(columns(conn, TYPE_VIEW))
    require(REQUIRED_DISTRICT_COLUMNS <= district_columns, "Harmonized district view columns changed")
    require(REQUIRED_TYPE_COLUMNS <= type_columns, "Harmonized type view columns changed")

    sql_text = (view_sql(conn, DISTRICT_VIEW) + "\n" + view_sql(conn, TYPE_VIEW)).lower()
    for forbidden in ("kba", "bev", "phev"):
        require(forbidden not in sql_text, f"Forbidden vehicle/geography reference found in harmonized view SQL: {forbidden}")

    return {
        "district_view": DISTRICT_VIEW,
        "district_view_type": table_type(conn, DISTRICT_VIEW),
        "district_columns": sorted(district_columns),
        "type_view": TYPE_VIEW,
        "type_view_type": table_type(conn, TYPE_VIEW),
        "type_columns": sorted(type_columns),
        "vehicle_reference_terms_found": [],
    }


def direct_core_validation(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    equipment = as_int(
        conn.execute(
            "SELECT COUNT(*) FROM core.charging_equipment WHERE source_id = ?",
            [SOURCE_ID],
        ).fetchone()[0]
    )
    points = as_int(
        conn.execute(
            "SELECT COUNT(*) FROM core.charging_point WHERE source_id = ?",
            [SOURCE_ID],
        ).fetchone()[0]
    )
    declared_points = as_int(
        conn.execute(
            "SELECT SUM(declared_point_count) FROM core.charging_equipment WHERE source_id = ?",
            [SOURCE_ID],
        ).fetchone()[0]
    )
    nominal_mw = as_float(
        conn.execute(
            """
            SELECT SUM(equipment_nominal_power_kw) / 1000.0
            FROM core.charging_equipment
            WHERE source_id = ?
            """,
            [SOURCE_ID],
        ).fetchone()[0]
    )
    duplicate_equipment = as_int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT source_id, excel_row
                FROM core.charging_equipment
                WHERE source_id = ?
                GROUP BY source_id, excel_row
                HAVING COUNT(*) <> 1
            )
            """,
            [SOURCE_ID],
        ).fetchone()[0]
    )
    duplicate_points = as_int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT source_id, equipment_excel_row, point_number
                FROM core.charging_point
                WHERE source_id = ?
                GROUP BY source_id, equipment_excel_row, point_number
                HAVING COUNT(*) <> 1
            )
            """,
            [SOURCE_ID],
        ).fetchone()[0]
    )
    orphan_points = as_int(
        conn.execute(
            """
            SELECT COUNT(*)
            FROM core.charging_point p
            LEFT JOIN core.charging_equipment e
              ON e.source_id = p.source_id
             AND e.excel_row = p.equipment_excel_row
            WHERE p.source_id = ? AND e.source_id IS NULL
            """,
            [SOURCE_ID],
        ).fetchone()[0]
    )
    power_row = conn.execute(
        """
        WITH point_power_tokens AS (
            SELECT
                p.source_id,
                p.equipment_excel_row,
                p.point_number,
                TRY_CAST(REPLACE(TRIM(token), ',', '.') AS DOUBLE) AS power_kw
            FROM core.charging_point p
            CROSS JOIN LATERAL UNNEST(
                STRING_SPLIT(COALESCE(p.connector_power_raw, ''), ';')
            ) AS tokens(token)
            WHERE p.source_id = ?
        ), point_power AS (
            SELECT
                source_id,
                equipment_excel_row,
                point_number,
                MAX(power_kw) AS max_kw
            FROM point_power_tokens
            GROUP BY source_id, equipment_excel_row, point_number
        )
        SELECT
            COUNT(*) AS points,
            COUNT(*) FILTER (WHERE pp.max_kw <= 22) AS normal_points,
            COUNT(*) FILTER (WHERE pp.max_kw > 22) AS fast_points,
            COUNT(*) FILTER (WHERE pp.max_kw >= 150) AS points_ge_150,
            COUNT(*) FILTER (WHERE pp.max_kw >= 350) AS points_ge_350,
            COUNT(*) FILTER (WHERE pp.max_kw IS NULL) AS unclassifiable_points
        FROM core.charging_point p
        LEFT JOIN point_power pp
          ON pp.source_id = p.source_id
         AND pp.equipment_excel_row = p.equipment_excel_row
         AND pp.point_number = p.point_number
        WHERE p.source_id = ?
        """,
        [SOURCE_ID, SOURCE_ID],
    ).fetchone()
    power = {
        "points": as_int(power_row[0]),
        "normal_points": as_int(power_row[1]),
        "fast_points": as_int(power_row[2]),
        "points_ge_150": as_int(power_row[3]),
        "points_ge_350": as_int(power_row[4]),
        "unclassifiable_points": as_int(power_row[5]),
    }
    require((equipment, points) == (EXPECTED["equipment"], EXPECTED["points"]), "Core equipment/point counts changed")
    require(declared_points == EXPECTED["points"], "Declared equipment point count does not reconcile")
    require(abs(nominal_mw - EXPECTED["nominal_power_mw"]) < 0.00001, "Core nominal power changed")
    require(duplicate_equipment == 0, "Duplicate equipment keys found")
    require(duplicate_points == 0, "Duplicate point keys found")
    require(orphan_points == 0, "Orphan charging points found")
    require(power == {
        "points": EXPECTED["points"],
        "normal_points": EXPECTED["normal_points"],
        "fast_points": EXPECTED["fast_points"],
        "points_ge_150": EXPECTED["points_ge_150"],
        "points_ge_350": EXPECTED["points_ge_350"],
        "unclassifiable_points": EXPECTED["unclassifiable_points"],
    }, f"Maximum-per-point power reconciliation failed: {power}")
    return {
        "equipment": equipment,
        "points": points,
        "declared_points": declared_points,
        "nominal_power_mw": nominal_mw,
        "duplicate_equipment_keys": duplicate_equipment,
        "duplicate_point_keys": duplicate_points,
        "orphan_points": orphan_points,
        "maximum_per_point_power": power,
    }


def load_harmonized_rows(conn: duckdb.DuckDBPyConnection) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    district_rows = [
        numeric_row(row, DISTRICT_NUMERIC_FIELDS)
        for row in query_dicts(
            conn,
            f"""
            SELECT *
            FROM {DISTRICT_VIEW}
            ORDER BY historical_bbsr_administrative_district_code
            """,
        )
    ]
    type_rows = [
        numeric_row(row, TYPE_NUMERIC_FIELDS)
        for row in query_dicts(
            conn,
            f"""
            SELECT *
            FROM {TYPE_VIEW}
            ORDER BY settlement_type_code
            """,
        )
    ]
    require(len(district_rows) == EXPECTED["historical_units"], "Harmonized district row count changed")
    require(len(type_rows) == len(CATEGORY_ORDER), "Harmonized type row count changed")
    return district_rows, type_rows


def validate_harmonized_data(
    district_rows: Sequence[Mapping[str, Any]],
    type_rows: Sequence[Mapping[str, Any]],
    direct: Mapping[str, Any],
) -> Dict[str, Any]:
    codes = [str(row["historical_bbsr_administrative_district_code"]) for row in district_rows]
    require(len(codes) == len(set(codes)), "Duplicate historical BBSR geographic units found")
    categories = [str(row["historical_bbsr_settlement_type_code"]) for row in district_rows]
    require(set(categories) == set(CATEGORY_ORDER), "Unexpected harmonized category code")
    category_counts = {code: categories.count(code) for code in CATEGORY_ORDER}
    require(category_counts == EXPECTED_CATEGORY_UNITS, f"Unexpected category unit counts: {category_counts}")
    require(all(row["harmonization_version"] == HARMONIZATION_VERSION for row in district_rows), "Harmonization version changed")
    require(all(row["infrastructure_reference_date"].isoformat() == INFRASTRUCTURE_REFERENCE_DATE for row in district_rows), "Infrastructure reference date changed")
    require(all(row["historical_bbsr_reference_date"].isoformat() == BBSR_REFERENCE_DATE for row in district_rows), "BBSR reference date changed")
    require(all(str(row["historical_bbsr_settlement_type_name_de"]) == CATEGORY_LABELS[str(row["historical_bbsr_settlement_type_code"])] for row in district_rows), "Category labels changed")
    require(all(as_int(row["unclassifiable_power_point_count"]) == 0 for row in district_rows), "Unclassifiable points remain in the harmonized view")

    totals = {
        "equipment": sum(as_int(row["equipment_count"]) for row in district_rows),
        "points": sum(as_int(row["charging_point_count"]) for row in district_rows),
        "normal_points": sum(as_int(row["normal_charging_point_count"]) for row in district_rows),
        "fast_points": sum(as_int(row["fast_charging_point_count"]) for row in district_rows),
        "points_ge_150": sum(as_int(row["points_ge_150_kw"]) for row in district_rows),
        "points_ge_350": sum(as_int(row["points_ge_350_kw"]) for row in district_rows),
        "unclassifiable_points": sum(as_int(row["unclassifiable_power_point_count"]) for row in district_rows),
        "source_components": sum(as_int(row["source_component_count"]) for row in district_rows),
        "nominal_power_mw": sum(as_float(row["total_equipment_nominal_power_mw"]) for row in district_rows),
    }
    for field in ("equipment", "points", "normal_points", "fast_points", "points_ge_150", "points_ge_350", "unclassifiable_points", "source_components"):
        require(totals[field] == EXPECTED[field], f"Harmonized total changed for {field}: {totals[field]}")
    require(abs(totals["nominal_power_mw"] - EXPECTED["nominal_power_mw"]) < 0.00001, "Harmonized nominal power changed")
    require(totals["points"] == direct["points"], "Harmonized points do not match core")

    type_codes = [str(row["settlement_type_code"]) for row in type_rows]
    require(type_codes == list(CATEGORY_ORDER), "Type summary ordering or codes changed")
    require(all(row["harmonization_version"] == HARMONIZATION_VERSION for row in type_rows), "Type summary version changed")
    require(all(row["all_historical_district_count"] == EXPECTED["historical_units"] for row in type_rows), "Type summary all-unit count changed")
    require(all(row["all_source_component_count"] == EXPECTED["source_components"] for row in type_rows), "Type summary all-source count changed")
    require(all(row["unclassifiable_power_point_count"] == 0 for row in type_rows), "Type summary has unclassifiable points")

    return {
        "district_row_count": len(district_rows),
        "category_unit_counts": category_counts,
        "totals": totals,
        "type_row_count": len(type_rows),
        "unclassified_rows": 0,
    }


def category_metrics(
    district_rows: Sequence[Mapping[str, Any]],
    type_rows: Sequence[Mapping[str, Any]],
    totals: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    by_type_view = {str(row["settlement_type_code"]): row for row in type_rows}
    output: List[Dict[str, Any]] = []
    for code in CATEGORY_ORDER:
        rows = [row for row in district_rows if str(row["historical_bbsr_settlement_type_code"]) == code]
        equipment = sum(as_int(row["equipment_count"]) for row in rows)
        points = sum(as_int(row["charging_point_count"]) for row in rows)
        normal = sum(as_int(row["normal_charging_point_count"]) for row in rows)
        fast = sum(as_int(row["fast_charging_point_count"]) for row in rows)
        ge150 = sum(as_int(row["points_ge_150_kw"]) for row in rows)
        ge350 = sum(as_int(row["points_ge_350_kw"]) for row in rows)
        nominal_kw = sum(as_float(row["total_equipment_nominal_power_kw"]) for row in rows)
        point_per_unit = [as_float(row["charging_point_count"]) / as_float(row["equipment_count"]) for row in rows if as_int(row["equipment_count"]) > 0]
        points_per_geo = [float(row["charging_point_count"]) for row in rows]
        row = {
            "settlement_type_code": code,
            "settlement_type_name_de": CATEGORY_LABELS[code],
            "historical_district_count": len(rows),
            "source_component_count": sum(as_int(item["source_component_count"]) for item in rows),
            "equipment_count": equipment,
            "charging_point_count": points,
            "normal_charging_point_count": normal,
            "fast_charging_point_count": fast,
            "points_ge_150_kw": ge150,
            "points_ge_350_kw": ge350,
            "unclassifiable_power_point_count": sum(as_int(item["unclassifiable_power_point_count"]) for item in rows),
            "equipment_national_share_pct": pct(equipment, float(totals["equipment"])),
            "charging_point_national_share_pct": pct(points, float(totals["points"])),
            "fast_charging_share_pct": pct(fast, float(points)),
            "fast_share_of_national_fast_points_pct": pct(fast, float(totals["fast_points"])),
            "points_ge_150_within_category_share_pct": pct(ge150, float(points)),
            "points_ge_150_national_share_pct": pct(ge150, float(totals["points"])),
            "points_ge_350_within_category_share_pct": pct(ge350, float(points)),
            "points_ge_350_national_share_pct": pct(ge350, float(totals["points"])),
            "declared_equipment_nominal_power_kw": nominal_kw,
            "declared_equipment_nominal_power_mw": nominal_kw / 1000.0,
            "nominal_power_national_share_pct": pct(nominal_kw, float(totals["nominal_power_mw"]) * 1000.0),
            "average_points_per_historical_unit": statistics.mean(points_per_geo),
            "median_points_per_historical_unit": statistics.median(points_per_geo),
            "weighted_points_per_equipment_unit": ratio(points, float(equipment)),
            "average_points_per_equipment_unit": statistics.mean(point_per_unit) if point_per_unit else None,
            "median_points_per_equipment_unit": statistics.median(point_per_unit) if point_per_unit else None,
            "weighted_fast_share_pct": pct(fast, float(points)),
            "unweighted_mean_fast_share_pct": statistics.mean([as_float(row["fast_point_share_pct"]) for row in rows]),
            "weighted_ge_150_share_pct": pct(ge150, float(points)),
            "unweighted_mean_ge_150_share_pct": statistics.mean([as_float(row["high_power_point_share_pct"]) for row in rows]),
            "weighted_ge_350_share_pct": pct(ge350, float(points)),
            "unweighted_mean_ge_350_share_pct": statistics.mean([pct(as_int(row["points_ge_350_kw"]), float(as_int(row["charging_point_count"]))) or 0.0 for row in rows]),
            "weighted_unweighted_fast_share_gap_pct_points": pct(fast, float(points)) - statistics.mean([as_float(row["fast_point_share_pct"]) for row in rows]),
            "weighted_unweighted_ge_150_gap_pct_points": pct(ge150, float(points)) - statistics.mean([as_float(row["high_power_point_share_pct"]) for row in rows]),
            "weighted_unweighted_ge_350_gap_pct_points": pct(ge350, float(points)) - statistics.mean([pct(as_int(row["points_ge_350_kw"]), float(as_int(row["charging_point_count"]))) or 0.0 for row in rows]),
        }
        summary_row = by_type_view[code]
        require(summary_row["historical_district_count"] == row["historical_district_count"], f"Type view district count mismatch for category {code}")
        require(summary_row["source_component_count"] == row["source_component_count"], f"Type view source component mismatch for category {code}")
        for local, view_field in (
            ("equipment_count", "equipment_count"),
            ("charging_point_count", "charging_point_count"),
            ("normal_charging_point_count", "normal_charging_point_count"),
            ("fast_charging_point_count", "fast_charging_point_count"),
            ("points_ge_150_kw", "points_ge_150_kw"),
            ("points_ge_350_kw", "points_ge_350_kw"),
        ):
            require(summary_row[view_field] == row[local], f"Type view metric mismatch for category {code}: {local}")
        require(abs(as_float(summary_row["declared_equipment_nominal_power_mw"]) - row["declared_equipment_nominal_power_mw"]) < 0.00001, f"Type view nominal power mismatch for category {code}")
        output.append(row)
    return output


def build_district_metrics(district_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for source in district_rows:
        points = as_int(source["charging_point_count"])
        equipment = as_int(source["equipment_count"])
        fast = as_int(source["fast_charging_point_count"])
        ge150 = as_int(source["points_ge_150_kw"])
        ge350 = as_int(source["points_ge_350_kw"])
        item = {
            "historical_bbsr_administrative_district_code": source["historical_bbsr_administrative_district_code"],
            "historical_bbsr_administrative_district_name": source["historical_bbsr_administrative_district_name"],
            "historical_bbsr_federal_state_name": source["historical_bbsr_federal_state_name"],
            "historical_bbsr_kreisregion_code": source["historical_bbsr_kreisregion_code"],
            "historical_bbsr_settlement_type_code": str(source["historical_bbsr_settlement_type_code"]),
            "historical_bbsr_settlement_type_name_de": source["historical_bbsr_settlement_type_name_de"],
            "source_component_count": as_int(source["source_component_count"]),
            "source_component_names": source["source_component_names"],
            "mapping_method": source["mapping_method"],
            "boundary_compatibility_status": source["boundary_compatibility_status"],
            "infrastructure_reference_date": source["infrastructure_reference_date"].isoformat(),
            "historical_bbsr_reference_date": source["historical_bbsr_reference_date"].isoformat(),
            "equipment_count": equipment,
            "charging_point_count": points,
            "normal_charging_point_count": as_int(source["normal_charging_point_count"]),
            "fast_charging_point_count": fast,
            "points_ge_150_kw": ge150,
            "points_ge_350_kw": ge350,
            "unclassifiable_power_point_count": as_int(source["unclassifiable_power_point_count"]),
            "declared_equipment_nominal_power_mw": as_float(source["total_equipment_nominal_power_mw"]),
            "fast_point_share_pct": pct(fast, float(points)),
            "points_ge_150_share_pct": pct(ge150, float(points)),
            "points_ge_350_share_pct": pct(ge350, float(points)),
            "points_per_equipment_unit": ratio(points, float(equipment)),
            "share_rank_eligible": points >= MIN_SHARE_POINTS,
        }
        rows.append(item)

    def rank(field: str, reverse: bool = True) -> Dict[str, int]:
        ordered = sorted(rows, key=lambda row: (-(row[field] or 0.0) if reverse else (row[field] if row[field] is not None else math.inf), row["historical_bbsr_administrative_district_code"]))
        return {str(row["historical_bbsr_administrative_district_code"]): index for index, row in enumerate(ordered, 1)}

    for field, name in (
        ("charging_point_count", "rank_points"),
        ("fast_charging_point_count", "rank_fast_points"),
        ("points_ge_150_kw", "rank_points_ge_150"),
        ("points_ge_350_kw", "rank_points_ge_350"),
    ):
        ranks = rank(field)
        for row in rows:
            row[name] = ranks[str(row["historical_bbsr_administrative_district_code"])]

    eligible = [row for row in rows if row["share_rank_eligible"] and row["fast_point_share_pct"] is not None]
    high = sorted(eligible, key=lambda row: (-row["fast_point_share_pct"], row["historical_bbsr_administrative_district_code"]))
    low = sorted(eligible, key=lambda row: (row["fast_point_share_pct"], row["historical_bbsr_administrative_district_code"]))
    for index, row in enumerate(high, 1):
        row["rank_fast_share_high"] = index
    for index, row in enumerate(low, 1):
        row["rank_fast_share_low"] = index
    for row in rows:
        row.setdefault("rank_fast_share_high", None)
        row.setdefault("rank_fast_share_low", None)
    return sorted(rows, key=lambda row: row["historical_bbsr_administrative_district_code"])


def distribution_metrics(
    district_metrics: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    metric_definitions = (
        ("charging_point_count", "Charging points per historical unit", False),
        ("equipment_count", "Equipment records per historical unit", False),
        ("fast_point_share_pct", "Fast-point share", True),
        ("points_ge_150_share_pct", ">=150 kW point share", True),
        ("points_ge_350_share_pct", ">=350 kW point share", True),
        ("declared_equipment_nominal_power_mw", "Declared equipment nominal power (MW)", False),
        ("points_per_equipment_unit", "Charging points per equipment unit", False),
    )
    result = []
    for code in CATEGORY_ORDER:
        category_rows = [row for row in district_metrics if row["historical_bbsr_settlement_type_code"] == code]
        for field, label, is_share in metric_definitions:
            stats = distribution([row[field] for row in category_rows if row[field] is not None])
            result.append(
                {
                    "settlement_type_code": code,
                    "settlement_type_name_de": CATEGORY_LABELS[code],
                    "metric": field,
                    "metric_label": label,
                    "unit": "percent" if is_share else ("MW" if field.endswith("_mw") else "ratio" if field == "points_per_equipment_unit" else "count"),
                    "denominator_note": "All historical target units" if field not in {"fast_point_share_pct", "points_ge_150_share_pct", "points_ge_350_share_pct", "points_per_equipment_unit"} else "Units with a non-zero relevant denominator",
                    **stats,
                }
            )
    return result


def weighted_unweighted_rows(
    district_metrics: Sequence[Mapping[str, Any]],
    totals: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    groups: List[Tuple[str, str, List[Mapping[str, Any]]]] = [(code, CATEGORY_LABELS[code], [row for row in district_metrics if row["historical_bbsr_settlement_type_code"] == code]) for code in CATEGORY_ORDER]
    groups.append(("ALL", "All 400 historical units", list(district_metrics)))
    result = []
    for code, label, rows in groups:
        points = sum(as_int(row["charging_point_count"]) for row in rows)
        fast = sum(as_int(row["fast_charging_point_count"]) for row in rows)
        ge150 = sum(as_int(row["points_ge_150_kw"]) for row in rows)
        ge350 = sum(as_int(row["points_ge_350_kw"]) for row in rows)
        mean_fast = statistics.mean([as_float(row["fast_point_share_pct"]) for row in rows])
        mean_ge150 = statistics.mean([as_float(row["points_ge_150_share_pct"]) for row in rows])
        mean_ge350 = statistics.mean([as_float(row["points_ge_350_share_pct"]) for row in rows])
        weighted_fast = pct(fast, float(points))
        weighted_ge150 = pct(ge150, float(points))
        weighted_ge350 = pct(ge350, float(points))
        result.append(
            {
                "group_code": code,
                "group_label": label,
                "historical_unit_count": len(rows),
                "weighted_fast_share_pct": weighted_fast,
                "unweighted_mean_fast_share_pct": mean_fast,
                "fast_share_gap_weighted_minus_unweighted_pct_points": weighted_fast - mean_fast,
                "weighted_ge_150_share_pct": weighted_ge150,
                "unweighted_mean_ge_150_share_pct": mean_ge150,
                "ge_150_share_gap_weighted_minus_unweighted_pct_points": weighted_ge150 - mean_ge150,
                "weighted_ge_350_share_pct": weighted_ge350,
                "unweighted_mean_ge_350_share_pct": mean_ge350,
                "ge_350_share_gap_weighted_minus_unweighted_pct_points": weighted_ge350 - mean_ge350,
            }
        )
    return result


def ranked_rows(
    district_metrics: Sequence[Mapping[str, Any]],
    field: str,
    top_n: int = 10,
    reverse: bool = True,
    eligible_only: bool = False,
) -> List[Dict[str, Any]]:
    rows = [row for row in district_metrics if (not eligible_only or row["share_rank_eligible"]) and row[field] is not None]
    rows = sorted(rows, key=lambda row: ((-row[field] if reverse else row[field]), row["historical_bbsr_administrative_district_code"]))
    result = []
    for rank_number, row in enumerate(rows[:top_n], 1):
        result.append(
            {
                "rank": rank_number,
                "geographic_code": row["historical_bbsr_administrative_district_code"],
                "geographic_name": row["historical_bbsr_administrative_district_name"],
                "category_code": row["historical_bbsr_settlement_type_code"],
                "category_name": row["historical_bbsr_settlement_type_name_de"],
                "equipment_count": row["equipment_count"],
                "charging_point_count": row["charging_point_count"],
                "fast_charging_point_count": row["fast_charging_point_count"],
                "points_ge_150_kw": row["points_ge_150_kw"],
                "points_ge_350_kw": row["points_ge_350_kw"],
                "fast_point_share_pct": row["fast_point_share_pct"],
                "points_ge_150_share_pct": row["points_ge_150_share_pct"],
                "points_ge_350_share_pct": row["points_ge_350_share_pct"],
                "ranking_metric": field,
                "ranking_value": row[field],
                "minimum_denominator": MIN_SHARE_POINTS if eligible_only else None,
            }
        )
    return result


def concentration_metrics(
    district_metrics: Sequence[Mapping[str, Any]],
    totals: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    metrics = (
        ("charging_point_count", "Charging points", float(totals["points"])),
        ("fast_charging_point_count", "Fast points", float(totals["fast_points"])),
        ("points_ge_150_kw", ">=150 kW points", float(totals["points_ge_150"])),
        ("points_ge_350_kw", ">=350 kW points", float(totals["points_ge_350"])),
    )
    result = []
    for field, label, denominator in metrics:
        ordered = sorted(district_metrics, key=lambda row: (-row[field], row["historical_bbsr_administrative_district_code"]))
        result.append(
            {
                "metric": field,
                "metric_label": label,
                "top_1_share_pct": pct(sum(row[field] for row in ordered[:1]), denominator),
                "top_5_share_pct": pct(sum(row[field] for row in ordered[:5]), denominator),
                "top_10_share_pct": pct(sum(row[field] for row in ordered[:10]), denominator),
                "largest_unit_code": ordered[0]["historical_bbsr_administrative_district_code"],
                "largest_unit_name": ordered[0]["historical_bbsr_administrative_district_name"],
                "largest_unit_category": ordered[0]["historical_bbsr_settlement_type_code"],
                "largest_unit_value": ordered[0][field],
            }
        )
    point_shares = [row["charging_point_count"] / float(totals["points"]) for row in district_metrics]
    fast_shares = [row["fast_charging_point_count"] / float(totals["fast_points"]) for row in district_metrics]
    result.append(
        {
            "metric": "hhi",
            "metric_label": "Herfindahl-Hirschman index (district shares)",
            "top_1_share_pct": None,
            "top_5_share_pct": None,
            "top_10_share_pct": None,
            "largest_unit_code": None,
            "largest_unit_name": None,
            "largest_unit_category": None,
            "largest_unit_value": None,
            "point_hhi_0_10000": 10_000.0 * sum(value * value for value in point_shares),
            "fast_point_hhi_0_10000": 10_000.0 * sum(value * value for value in fast_shares),
        }
    )
    return result


def validation_checks(
    direct: Mapping[str, Any],
    harmonized: Mapping[str, Any],
    fingerprints: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    power = direct["maximum_per_point_power"]
    checks = [
        ("national equipment total", direct["equipment"] == EXPECTED["equipment"], f"{direct['equipment']:,}"),
        ("national point total", direct["points"] == EXPECTED["points"], f"{direct['points']:,}"),
        ("normal point total", power["normal_points"] == EXPECTED["normal_points"], f"{power['normal_points']:,}"),
        ("fast point total", power["fast_points"] == EXPECTED["fast_points"], f"{power['fast_points']:,}"),
        (">=150 kW point total", power["points_ge_150"] == EXPECTED["points_ge_150"], f"{power['points_ge_150']:,}"),
        (">=350 kW point total", power["points_ge_350"] == EXPECTED["points_ge_350"], f"{power['points_ge_350']:,}"),
        ("unclassifiable point total", power["unclassifiable_points"] == 0, f"{power['unclassifiable_points']:,}"),
        ("declared point reconciliation", direct["declared_points"] == EXPECTED["points"], f"{direct['declared_points']:,}"),
        ("nominal equipment power", abs(direct["nominal_power_mw"] - EXPECTED["nominal_power_mw"]) < 0.00001, f"{direct['nominal_power_mw']:.4f} MW"),
        ("historical unit count", harmonized["district_row_count"] == EXPECTED["historical_units"], f"{harmonized['district_row_count']:,}"),
        ("source component count", harmonized["totals"]["source_components"] == EXPECTED["source_components"], f"{harmonized['totals']['source_components']:,}"),
        ("zero unclassified infrastructure", harmonized["unclassified_rows"] == 0, "0 rows"),
        ("duplicate equipment keys", direct["duplicate_equipment_keys"] == 0, "0"),
        ("duplicate point keys", direct["duplicate_point_keys"] == 0, "0"),
        ("orphan points", direct["orphan_points"] == 0, "0"),
        ("source fingerprints", all(item["match"] for item in fingerprints), f"{len(fingerprints)} matched"),
    ]
    return [{"check": label, "passed": passed, "evidence": evidence} for label, passed, evidence in checks]


def csv_value(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, float):
        return f"{value:.8f}".rstrip("0").rstrip(".")
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return value


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field)) for field in fieldnames})


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def category_table(category_rows: Sequence[Mapping[str, Any]]) -> str:
    rows = []
    for row in category_rows:
        rows.append(
            [
                row["settlement_type_code"],
                row["settlement_type_name_de"],
                fmt(row["historical_district_count"]),
                fmt(row["source_component_count"]),
                fmt(row["equipment_count"]),
                fmt(row["charging_point_count"]),
                fmt_pct(row["equipment_national_share_pct"]),
                fmt_pct(row["charging_point_national_share_pct"]),
                fmt_pct(row["fast_charging_share_pct"]),
                fmt_pct(row["points_ge_150_within_category_share_pct"]),
                fmt_pct(row["points_ge_350_within_category_share_pct"]),
                fmt(row["declared_equipment_nominal_power_mw"], 4),
                fmt_pct(row["nominal_power_national_share_pct"]),
                fmt(row["average_points_per_historical_unit"], 2),
                fmt(row["median_points_per_historical_unit"], 2),
                fmt(row["average_points_per_equipment_unit"], 3),
                fmt(row["median_points_per_equipment_unit"], 3),
            ]
        )
    return markdown_table(
        [
            "Type",
            "BBSR category",
            "Units",
            "Source components",
            "Equipment",
            "Points",
            "Equipment share",
            "Point share",
            "Fast share",
            ">=150 share",
            ">=350 share",
            "Nominal MW",
            "Nominal power share",
            "Mean points/unit",
            "Median points/unit",
            "Mean points/equipment",
            "Median points/equipment",
        ],
        rows,
    )


def distribution_table(rows: Sequence[Mapping[str, Any]]) -> str:
    result = []
    for row in rows:
        result.append(
            [
                row["metric_label"],
                row["settlement_type_code"],
                fmt(row["min"], 2),
                fmt(row["p10"], 2),
                fmt(row["median"], 2),
                fmt(row["mean"], 2),
                fmt(row["p90"], 2),
                fmt(row["max"], 2),
                fmt(row["stddev"], 2),
                fmt(row["mean_median_ratio"], 2),
            ]
        )
    return markdown_table(
        ["Measure", "Type", "Min", "P10", "Median", "Mean", "P90", "Max", "Std. dev.", "Mean/median"],
        result,
    )


def weighted_table(rows: Sequence[Mapping[str, Any]]) -> str:
    result = []
    for row in rows:
        result.append(
            [
                row["group_code"],
                row["group_label"],
                fmt(row["historical_unit_count"]),
                fmt_pct(row["weighted_fast_share_pct"]),
                fmt_pct(row["unweighted_mean_fast_share_pct"]),
                fmt(row["fast_share_gap_weighted_minus_unweighted_pct_points"], 2),
                fmt_pct(row["weighted_ge_150_share_pct"]),
                fmt_pct(row["unweighted_mean_ge_150_share_pct"]),
                fmt(row["ge_150_share_gap_weighted_minus_unweighted_pct_points"], 2),
                fmt_pct(row["weighted_ge_350_share_pct"]),
                fmt_pct(row["unweighted_mean_ge_350_share_pct"]),
                fmt(row["ge_350_share_gap_weighted_minus_unweighted_pct_points"], 2),
            ]
        )
    return markdown_table(
        ["Group", "Definition", "Units", "Weighted fast", "Mean unit fast", "Fast gap (pp)", "Weighted >=150", "Mean unit >=150", ">=150 gap (pp)", "Weighted >=350", "Mean unit >=350", ">=350 gap (pp)"],
        result,
    )


def ranking_table(rows: Sequence[Mapping[str, Any]], metric: str, value_field: str = "ranking_value") -> str:
    result = []
    for row in rows:
        result.append(
            [
                row["rank"],
                row["geographic_code"],
                row["geographic_name"],
                row["category_code"],
                fmt(row["equipment_count"]),
                fmt(row["charging_point_count"]),
                fmt(row["fast_charging_point_count"]),
                fmt(row["points_ge_150_kw"]),
                fmt(row["points_ge_350_kw"]),
                fmt_pct(row["fast_point_share_pct"]),
                fmt(row[value_field], 2) if isinstance(row[value_field], float) else fmt(row[value_field]),
            ]
        )
    return markdown_table(
        ["Rank", "Code", "Historical unit", "Type", "Equipment", "Points", "Fast", ">=150", ">=350", "Fast share", metric],
        result,
    )


def render_report(result: Mapping[str, Any]) -> str:
    category_rows = result["category_metrics"]
    totals = result["harmonized_validation"]["totals"]
    direct = result["direct_core_validation"]
    rankings = result["rankings"]
    concentration = result["concentration"]
    checks = result["validation_checks"]
    fingerprints = result["source_fingerprints"]
    weighted = result["weighted_unweighted"]
    high_share = rankings["highest_fast_share"]
    low_share = rankings["lowest_fast_share"]
    excluded = result["share_filter"]
    type1 = next(row for row in category_rows if row["settlement_type_code"] == "1")
    type2 = next(row for row in category_rows if row["settlement_type_code"] == "2")
    type3 = next(row for row in category_rows if row["settlement_type_code"] == "3")
    type4 = next(row for row in category_rows if row["settlement_type_code"] == "4")
    concentration_rows = [
        [
            row["metric_label"],
            fmt_pct(row.get("top_1_share_pct")),
            fmt_pct(row.get("top_5_share_pct")),
            fmt_pct(row.get("top_10_share_pct")),
            row.get("largest_unit_code") or "—",
            row.get("largest_unit_name") or "—",
            fmt(row.get("largest_unit_value")) if row.get("largest_unit_value") is not None else "—",
        ]
        for row in concentration
        if row["metric"] != "hhi"
    ]
    hhi = next(row for row in concentration if row["metric"] == "hhi")
    check_rows = [[item["check"], "PASS" if item["passed"] else "FAIL", item["evidence"]] for item in checks]
    fingerprint_rows = [[item["path"], item["purpose"], fmt(item["bytes"]), "MATCH" if item["match"] else "MISMATCH"] for item in fingerprints]
    validation_status = "PASS" if all(item["passed"] for item in checks) else "FAIL"

    lines = [
        "# Batch 14 — BBSR charging infrastructure statistical analysis",
        "",
        f"Status: **{validation_status}** — read-only analysis of the harmonized BBSR 2025 target-unit layer.",
        "",
        "## Executive summary",
        "",
        f"The primary analytical source is `{DISTRICT_VIEW}` with `{TYPE_VIEW}` as its four-category reconciliation view. It contains {fmt(result['harmonized_validation']['district_row_count'])} historical BBSR target units formed from {fmt(result['harmonized_validation']['totals']['source_components'])} current BNetzA source components. The infrastructure snapshot is dated `{INFRASTRUCTURE_REFERENCE_DATE}` and the historical BBSR geographic stand is `{BBSR_REFERENCE_DATE}`.",
        "",
        f"All four categories reconcile to {fmt(totals['equipment'])} equipment records, {fmt(totals['points'])} charging points, {fmt(totals['normal_points'])} normal points, {fmt(totals['fast_points'])} fast points, {fmt(totals['points_ge_150'])} points at least 150 kW, {fmt(totals['points_ge_350'])} points at least 350 kW, and {fmt(totals['nominal_power_mw'], 4)} MW of declared equipment nominal power. No unclassified infrastructure remains in the harmonized view.",
        "",
        f"Type 2 has the largest absolute infrastructure totals ({fmt(type2['charging_point_count'])} points and {fmt(type2['fast_charging_point_count'])} fast points), while type 4 has the highest within-category fast share ({fmt_pct(type4['fast_charging_share_pct'])}). These are different statements: absolute scale and relative mix should not be conflated.",
        "",
        f"The current data show declared-power composition, not accessibility, demand, utilization, coverage, or causal performance. The historical target geography intentionally combines Hanau and the remaining Main-Kinzig-Kreis; it does not assign an official 2026 BBSR type to Hanau.",
        "",
        "## Dataset and geographic reference dates",
        "",
        markdown_table(
            ["Item", "Value"],
            [
                ["Primary district view", f"`{DISTRICT_VIEW}`"],
                ["Primary category view", f"`{TYPE_VIEW}`"],
                ["BNetzA source ID", f"`{SOURCE_ID}`"],
                ["Infrastructure reference date", f"`{INFRASTRUCTURE_REFERENCE_DATE}`"],
                ["BBSR geographic reference date", f"`{BBSR_REFERENCE_DATE}`"],
                ["Harmonization version", f"`{HARMONIZATION_VERSION}`"],
                ["Historical target units", fmt(result["harmonized_validation"]["district_row_count"])],
                ["BNetzA source components", fmt(result["harmonized_validation"]["totals"]["source_components"])],
                ["KBA/vehicle stock used", "No"],
            ],
        ),
        "",
        "The 400-unit target grain is not a new 2025 infrastructure snapshot. It is the BNetzA 2026-09-30 register aggregated to the BBSR 2025 historical geography. Hanau and remaining Main-Kinzig-Kreis form one historical target; Kassel city remains distinct from Kassel county; Trier city and Trier-Saarburg remain separate source components.",
        "",
        "## National reconciliation",
        "",
        markdown_table(
            ["Measure", "Harmonized view", "Direct core / parser", "Expected"],
            [
                ["Equipment records", fmt(totals["equipment"]), fmt(direct["equipment"]), fmt(EXPECTED["equipment"])],
                ["Charging points", fmt(totals["points"]), fmt(direct["points"]), fmt(EXPECTED["points"])],
                ["Normal points (<=22 kW)", fmt(totals["normal_points"]), fmt(direct["maximum_per_point_power"]["normal_points"]), fmt(EXPECTED["normal_points"])],
                ["Fast points (>22 kW)", fmt(totals["fast_points"]), fmt(direct["maximum_per_point_power"]["fast_points"]), fmt(EXPECTED["fast_points"])],
                ["Points >=150 kW", fmt(totals["points_ge_150"]), fmt(direct["maximum_per_point_power"]["points_ge_150"]), fmt(EXPECTED["points_ge_150"])],
                ["Points >=350 kW", fmt(totals["points_ge_350"]), fmt(direct["maximum_per_point_power"]["points_ge_350"]), fmt(EXPECTED["points_ge_350"])],
                ["Unclassifiable power points", fmt(totals["unclassifiable_points"]), fmt(direct["maximum_per_point_power"]["unclassifiable_points"]), "0"],
                ["Declared equipment nominal power", fmt(totals["nominal_power_mw"], 4) + " MW", fmt(direct["nominal_power_mw"], 4) + " MW", fmt(EXPECTED["nominal_power_mw"], 4) + " MW"],
            ],
        ),
        "",
        "Power classes are overlapping nested classifications: every >=150 kW point is fast, and every >=350 kW point is also >=150 kW. Normal and fast are mutually exclusive only because the fast threshold is defined as strictly above 22 kW.",
        "",
        "## Category-level KPI comparison",
        "",
        category_table(category_rows),
        "",
        "Equipment and point shares are shares of national totals. Mean and median points per historical unit are unweighted across units. Mean and median points per equipment unit are the distributions of each unit's `charging_point_count / equipment_count`; the weighted ratio is available in the diagnostic CSV. None of these absolute or relative measures is an accessibility or quality score.",
        "",
        "### Type 1 versus types 2–4",
        "",
        f"- Type 1 has {fmt(type1['charging_point_count'])} points, more than type 3 ({fmt(type3['charging_point_count'])}) and type 4 ({fmt(type4['charging_point_count'])}), but fewer than type 2 ({fmt(type2['charging_point_count'])}).",
        f"- Type 1's fast share is {fmt_pct(type1['fast_charging_share_pct'])}; type 2 is {fmt_pct(type2['fast_charging_share_pct'])}, type 3 is {fmt_pct(type3['fast_charging_share_pct'])}, and type 4 is {fmt_pct(type4['fast_charging_share_pct'])}.",
        f"- Type 1 contributes {fmt_pct(type1['fast_share_of_national_fast_points_pct'])} of national fast points, whereas type 2 contributes {fmt_pct(type2['fast_share_of_national_fast_points_pct'])}. The latter is an absolute national contribution, not a within-category percentage.",
        f"- The type 1 within-category >=150 kW share is {fmt_pct(type1['points_ge_150_within_category_share_pct'])}; the corresponding >=350 kW share is {fmt_pct(type1['points_ge_350_within_category_share_pct'])}. These are declared-power mix measures.",
        "",
        "## Fast-charging and high-power structure",
        "",
        markdown_table(
            ["Type", "Normal points", "Fast points", "Fast share", "National fast share", ">=150 points", ">=150 within", ">=150 national", ">=350 points", ">=350 within", ">=350 national"],
            [
                [row["settlement_type_code"], fmt(row["normal_charging_point_count"]), fmt(row["fast_charging_point_count"]), fmt_pct(row["fast_charging_share_pct"]), fmt_pct(row["fast_share_of_national_fast_points_pct"]), fmt(row["points_ge_150_kw"]), fmt_pct(row["points_ge_150_within_category_share_pct"]), fmt_pct(row["points_ge_150_national_share_pct"]), fmt(row["points_ge_350_kw"]), fmt_pct(row["points_ge_350_within_category_share_pct"]), fmt_pct(row["points_ge_350_national_share_pct"])]
                for row in category_rows
            ],
        ),
        "",
        "The report preserves the exact thresholds `fast >22 kW`, `high-power >=150 kW`, and `high-power >=350 kW`. A high fast or HPC share means a larger declared-power mix within the registered points; it does not establish better access for residents or drivers.",
        "",
        "## Within-category geographic variation",
        "",
        distribution_table(result["distribution_metrics"]),
        "",
        "Percentiles use deterministic linear interpolation over the 400 historical target units within each category. Standard deviation is the population standard deviation of the displayed unit-level distribution. For share metrics, the denominator is the unit's own charging-point count; for points per equipment, units with zero equipment would be excluded rather than assigned an artificial ratio. The current harmonized data have valid denominators for all reported rows.",
        "",
        "A mean/median ratio above 1 indicates right-skew in the unit distribution: a small number of larger units pull the mean above the median. Share metrics can also be unstable for small point denominators, which is why share-based rankings below apply an exploratory 30-point minimum.",
        "",
        "## Weighted versus unweighted shares",
        "",
        weighted_table(weighted),
        "",
        "The weighted share gives every charging point one weight. The unweighted mean gives every historical unit one weight. When the values differ, smaller units can influence the unweighted mean more than their point volume would influence the national mix; this is a descriptive weighting effect, not evidence of better or worse access.",
        "",
        "## Concentration and district-level outliers",
        "",
        markdown_table(["Measure", "Top 1", "Top 5", "Top 10", "Largest unit code", "Largest unit", "Largest value"], concentration_rows),
        "",
        f"The district-share HHI is {fmt(hhi['point_hhi_0_10000'], 2)} for total points and {fmt(hhi['fast_point_hhi_0_10000'], 2)} for fast points on the 0–10,000 descriptive scale. This summarizes concentration only; it is not a market-power or service-quality measure.",
        "",
        "### Largest absolute point totals",
        "",
        ranking_table(rankings["largest_points"], "Points"),
        "",
        "### Largest absolute fast-point totals",
        "",
        ranking_table(rankings["largest_fast_points"], "Fast points"),
        "",
        "### Largest >=150 kW totals",
        "",
        ranking_table(rankings["largest_ge_150"], ">=150 kW points"),
        "",
        "### Largest >=350 kW totals",
        "",
        ranking_table(rankings["largest_ge_350"], ">=350 kW points"),
        "",
        "### Highest and lowest fast shares among stable denominators",
        "",
        f"The share-ranking filter is `{MIN_SHARE_POINTS}` charging points. It is an exploratory stability filter, not an official standard. It excludes {fmt(excluded['excluded_unit_count'])} of {fmt(excluded['total_unit_count'])} units with fewer than {MIN_SHARE_POINTS} points ({fmt_pct(excluded['excluded_unit_pct'])} of units; {fmt(excluded['excluded_points'])} points, {fmt_pct(excluded['excluded_points_pct'])} of national points).",
        "",
        "Highest fast shares:",
        "",
        ranking_table(high_share, "Fast share", "fast_point_share_pct"),
        "",
        "Lowest fast shares:",
        "",
        ranking_table(low_share, "Fast share", "fast_point_share_pct"),
        "",
        "The rankings are descriptive outlier screens. They do not rank district quality, need, coverage, reliability, or accessibility.",
        "",
        "## Evidence-supported interpretations and unresolved hypotheses",
        "",
        f"**OBSERVED:** Type 4 has the highest within-category fast share ({fmt_pct(type4['fast_charging_share_pct'])}), while type 2 has the largest absolute fast-point count ({fmt(type2['fast_charging_point_count'])}). The ranking reverses because type 2 has more total points.",
        "",
        f"**OBSERVED:** The category ordering for fast share ({fmt_pct(type1['fast_charging_share_pct'])}, {fmt_pct(type2['fast_charging_share_pct'])}, {fmt_pct(type3['fast_charging_share_pct'])}, {fmt_pct(type4['fast_charging_share_pct'])}) is also the ordering for >=150 kW share ({fmt_pct(type1['points_ge_150_within_category_share_pct'])}, {fmt_pct(type2['points_ge_150_within_category_share_pct'])}, {fmt_pct(type3['points_ge_150_within_category_share_pct'])}, {fmt_pct(type4['points_ge_150_within_category_share_pct'])}). This is an association across four aggregate groups, not a causal result.",
        "",
        f"**SUPPORTED ASSOCIATION:** In this four-category table, higher fast-point shares coincide with higher high-power shares. The result is consistent with category-level differences in declared-power mix, but the analysis cannot separate category composition from other correlated geography or reporting factors.",
        "",
        f"**OBSERVED:** The all-unit weighted fast share is {fmt_pct(weighted[-1]['weighted_fast_share_pct'])}, compared with an unweighted historical-unit mean of {fmt_pct(weighted[-1]['unweighted_mean_fast_share_pct'])}; the difference is {fmt(weighted[-1]['fast_share_gap_weighted_minus_unweighted_pct_points'], 2)} percentage points. This demonstrates why a national point-weighted share and an average district share answer different questions.",
        "",
        "**PLAUSIBLE HYPOTHESIS:** Differences may reflect a combination of normal-versus-fast mix, concentration of high-power equipment, and the size/composition of individual historical units. The current descriptive fields can show these patterns but cannot identify a cause.",
        "",
        "**NOT TESTABLE WITH CURRENT DATA:** The analysis cannot test whether motorway corridors, residents, traffic flows, EV ownership, demand, utilization, queueing, reliability, or actual delivered energy explain the observed differences. It also cannot claim that a higher fast share means better accessibility.",
        "",
        markdown_table(
            ["Hypothesis or question", "Current evidence", "Status", "Additional data needed"],
            [
                ["Different normal/fast mix explains category differences", "Counts and shares are present in the harmonized layer", "OBSERVED / descriptive", "None for description; demand or utilization data for explanation"],
                ["High-power concentration drives category differences", ">=150 and >=350 kW counts/shares and outliers are present", "OBSERVED / descriptive", "Availability, sessions, energy, or capacity data"],
                ["Population or resident density explains infrastructure mix", "No population denominator in the analytical layer", "NOT TESTABLE", "Dated population and area data at the same historical geography"],
                ["Motorway/traffic corridors explain fast concentration", "No traffic or corridor field used", "NOT TESTABLE", "Dated traffic flow, road-network, and site-location data"],
                ["EV stock or demand explains infrastructure mix", "KBA stock is intentionally excluded from this batch", "NOT TESTABLE", "Approved, date-compatible vehicle and demand data with a valid geography bridge"],
                ["Higher fast share means better accessibility", "No utilization, queue, uptime, or service-coverage measure", "UNSUPPORTED", "Availability, sessions, queue time, reliability, and accessibility denominators"],
            ],
        ),
        "",
        "## KPI evaluation for future Tableau work",
        "",
        "The candidates below are evaluated for a future Tableau layer only. Batch 14 deploys no KPI views and no dashboard. BBSR-based BEV-to-charger ratios are intentionally excluded.",
        "",
        markdown_table(
            ["Candidate", "Status", "Definition / numerator / denominator", "Source", "Grain and time", "Added value and Tableau suitability", "Main risk"],
            [
                ["BBSR category point count and national share", "VALIDATED", "Charging points; points / all 211,253 points", "Harmonized district/type views over core point rows", "BBSR 2025 target; BNetzA 2026-09-30", "High; simple bars/maps and tooltips", "Absolute scale can be mistaken for access"],
                ["BBSR category equipment count and national share", "VALIDATED", "Equipment rows; equipment / all 117,662 rows", "Harmonized district/type views over core equipment rows", "BBSR 2025 target; BNetzA 2026-09-30", "High as a separate equipment-grain context", "Equipment is not point count"],
                ["Fast point count and within-category fast share", "VALIDATED", "Fast points (>22 kW); fast / category points", "Harmonized district/type views; maximum `connector_power_raw` parser", "BBSR target and BNetzA snapshot", "High; paired count-plus-share view", "Declared power is not utilization"],
                [">=150 and >=350 kW point counts/shares", "VALIDATED", "Nested high-power counts; each / category points", "Harmonized district/type views; maximum `connector_power_raw` parser", "BBSR target and BNetzA snapshot", "High; nested threshold comparison", "Thresholds are overlapping and not accessibility measures"],
                ["Unit distribution percentiles", "EXPLORATORY", "P10, median, P90 of points, equipment, shares, power, ratios", "Harmonized district view", "400 historical units; BNetzA snapshot", "High for box plots and distribution context", "Small denominators and skew"],
                ["Weighted versus unweighted fast/HPC shares", "EXPLORATORY", "Point-weighted share versus mean unit share", "Harmonized district view", "BBSR category or all units", "Medium-high; exposes denominator sensitivity", "Can be overread as performance"],
                ["Top-1/top-5/top-10 concentration share", "EXPLORATORY", "Points in top k units / national points", "Harmonized district view", "400 historical units; BNetzA snapshot", "Medium; compact concentration story", "Ranking is not quality or need"],
                ["Declared nominal equipment power", "VALIDATED", "Sum equipment nominal kW / 1,000", "Harmonized district view over core equipment rows", "BBSR target and BNetzA snapshot", "Medium as capacity context", "Not delivered energy or simultaneous capacity"],
                ["BBSR-based BEV-to-charger ratio", "UNSUPPORTED", "Would require KBA-to-BBSR classification and compatible dates", "No approved BBSR/KBA source bridge", "No approved current grain", "Do not include", "No valid BBSR/KBA bridge in this batch"],
            ],
        ),
        "",
        "Recommended small Tableau set: category point count/share, fast count/share, nested >=150 and >=350 kW count/share, and a distribution view showing median/P10/P90 unit metrics. Keep nominal power and concentration as context panels and show the source dates and historical-boundary caveat on every sheet.",
        "",
        "## Limitations and analytical opportunities",
        "",
        "- The BNetzA register is a published register and is not an exhaustive census of every publicly accessible charger.",
        "- A point slot is not necessarily a connector count, simultaneous service capacity, or an available point at every moment.",
        "- Declared nominal and connector power are not delivered energy, utilization, uptime, queue time, or reliability.",
        "- The BBSR target is historical 2025 geography applied to a 2026 infrastructure snapshot; it is not an official 2026 BBSR reclassification.",
        "- Absolute counts and shares lack population, area, traffic, EV-stock, and demand denominators in this batch.",
        "- Future phases could add approved same-vintage population/area denominators, traffic and corridor evidence, and operational utilization data. No additional dataset was downloaded for Batch 14.",
        "",
        "## Validation results",
        "",
        markdown_table(["Check", "Result", "Evidence"], check_rows),
        "",
        "### Source fingerprints",
        "",
        markdown_table(["Path", "Purpose", "Bytes", "Result"], fingerprint_rows),
        "",
        "The script opened DuckDB with `read_only=True`, read only the existing harmonized analytical views plus core tables for independent reconciliation, and did not create or alter any database object. No raw data, BBSR reference, Crosswalk, KBA object, or vehicle-stock table was changed.",
        "",
        "## Reproducibility and next step",
        "",
        "Run from the repository root:",
        "",
        "```bash",
        ".venv/bin/python scripts/14_analyze_bbsr_charging_patterns.py --json",
        "```",
        "",
        "The next approved step should be review of the analytical findings and KPI definitions. Tableau dashboard development or BBSR/KBA vehicle-stock integration remains outside Batch 14.",
        "",
    ]
    return "\n".join(lines)


def analyze(database: Path) -> Dict[str, Any]:
    require(database.is_file(), f"Database not found: {database}")
    fingerprints = fingerprint_files()
    conn = duckdb.connect(str(database), read_only=True)
    try:
        contract = validate_view_contract(conn)
        direct = direct_core_validation(conn)
        district_rows, type_rows = load_harmonized_rows(conn)
        harmonized = validate_harmonized_data(district_rows, type_rows, direct)
        district_metrics = build_district_metrics(district_rows)
        category_rows = category_metrics(district_rows, type_rows, harmonized["totals"])
        distributions = distribution_metrics(district_metrics)
        weighted = weighted_unweighted_rows(district_metrics, harmonized["totals"])
        rankings = {
            "largest_points": ranked_rows(district_metrics, "charging_point_count"),
            "largest_fast_points": ranked_rows(district_metrics, "fast_charging_point_count"),
            "largest_ge_150": ranked_rows(district_metrics, "points_ge_150_kw"),
            "largest_ge_350": ranked_rows(district_metrics, "points_ge_350_kw"),
            "highest_fast_share": ranked_rows(district_metrics, "fast_point_share_pct", eligible_only=True),
            "lowest_fast_share": ranked_rows(district_metrics, "fast_point_share_pct", reverse=False, eligible_only=True),
        }
        excluded_units = [row for row in district_metrics if not row["share_rank_eligible"]]
        share_filter = {
            "minimum_points": MIN_SHARE_POINTS,
            "total_unit_count": len(district_metrics),
            "excluded_unit_count": len(excluded_units),
            "excluded_unit_pct": pct(len(excluded_units), float(len(district_metrics))),
            "excluded_points": sum(row["charging_point_count"] for row in excluded_units),
            "excluded_points_pct": pct(sum(row["charging_point_count"] for row in excluded_units), float(harmonized["totals"]["points"])),
        }
        concentration = concentration_metrics(district_metrics, harmonized["totals"])
        checks = validation_checks(direct, harmonized, fingerprints)
        return {
            "analysis_version": "batch14-2026-11-03-bbsr-charging-patterns",
            "database": str(database.relative_to(ROOT)) if database.is_relative_to(ROOT) else str(database),
            "source_fingerprints": fingerprints,
            "view_contract": contract,
            "direct_core_validation": direct,
            "harmonized_validation": harmonized,
            "category_metrics": category_rows,
            "district_metrics": district_metrics,
            "distribution_metrics": distributions,
            "weighted_unweighted": weighted,
            "rankings": rankings,
            "share_filter": share_filter,
            "concentration": concentration,
            "validation_checks": checks,
        }
    finally:
        conn.close()


def write_outputs(result: Mapping[str, Any], report_path: Path, type_csv: Path, district_csv: Path) -> None:
    type_fields = list(result["category_metrics"][0].keys())
    district_fields = list(result["district_metrics"][0].keys())
    write_csv(type_csv, result["category_metrics"], type_fields)
    write_csv(district_csv, result["district_metrics"], district_fields)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result), encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--type-csv", type=Path, default=DEFAULT_TYPE_CSV)
    parser.add_argument("--district-csv", type=Path, default=DEFAULT_DISTRICT_CSV)
    parser.add_argument("--json", action="store_true", help="Print a compact JSON validation summary")
    args = parser.parse_args(argv)
    try:
        result = analyze(resolve_path(args.database))
        write_outputs(
            result,
            resolve_path(args.report),
            resolve_path(args.type_csv),
            resolve_path(args.district_csv),
        )
        if args.json:
            compact = {
                "status": "PASS" if all(item["passed"] for item in result["validation_checks"]) else "FAIL",
                "analysis_version": result["analysis_version"],
                "report": str(resolve_path(args.report).relative_to(ROOT)),
                "type_csv": str(resolve_path(args.type_csv).relative_to(ROOT)),
                "district_csv": str(resolve_path(args.district_csv).relative_to(ROOT)),
                "national": result["harmonized_validation"]["totals"],
                "category_unit_counts": result["harmonized_validation"]["category_unit_counts"],
                "share_filter": result["share_filter"],
                "validation_checks": result["validation_checks"],
            }
            print(json.dumps(compact, ensure_ascii=False, sort_keys=True, indent=2, default=json_default))
        else:
            print(f"PASS: {result['harmonized_validation']['district_row_count']} harmonized BBSR units analyzed")
            print(f"Created: {resolve_path(args.report).relative_to(ROOT)}")
            print(f"Created: {resolve_path(args.type_csv).relative_to(ROOT)}")
            print(f"Created: {resolve_path(args.district_csv).relative_to(ROOT)}")
        return 0 if all(item["passed"] for item in result["validation_checks"]) else 1
    except (AnalysisError, duckdb.Error, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
