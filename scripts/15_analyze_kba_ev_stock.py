#!/usr/bin/env python3
"""Batch 15: read-only analysis of the KBA FZ 27 vehicle-stock workbooks.

The script reads the existing DuckDB raw/core/history objects with
``read_only=True``.  It does not create or modify database objects, source
workbooks, reference files, or Crosswalks.  It writes deterministic analytical
CSV diagnostics and a Markdown report for the three local KBA FZ 27 releases:

* 2026-01-01
* 2026-04-01
* 2026-07-01

Run from the repository root::

    .venv/bin/python scripts/15_analyze_kba_ev_stock.py --json

The output deliberately keeps national, 16-state, ``Sonstige`` and 400-code
registration-region reporting scopes separate.  It does not join BBSR or
charging infrastructure data and it does not allocate the shared KBA Trier
region (07211).
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
DEFAULT_REPORT = ROOT / "reports/batch15_kba_ev_stock_analysis.md"
DEFAULT_OUTPUT_DIR = ROOT / "reports"

DATES = ("2026-01-01", "2026-04-01", "2026-07-01")
SOURCE_IDS = {
    "2026-01-01": "kba_fz27_2026_01",
    "2026-04-01": "kba_fz27_2026_04",
    "2026-07-01": "kba_fz27_2026_07",
}

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
RESIDUAL_GEOGRAPHY = "Sonstige"
NATIONAL_GEOGRAPHY = "Deutschland"
MUTUALLY_EXCLUSIVE_TOTAL_FUELS = (
    "Benzin",
    "Diesel",
    "Gas insgesamt",
    "Elektro (BEV)",
    "Hybrid insgesamt",
    "Sonstige",
)
EXPECTED_FUEL_TYPES = MUTUALLY_EXCLUSIVE_TOTAL_FUELS + ("darunter Plug-in",)
EXPECTED_SHEETS = (
    "Deckblatt",
    "Impressum",
    "Inhaltsverzeichnis",
    "FZ 27.1",
    "FZ 27.2",
    "FZ 27.3",
    "FZ 27.4",
    "FZ 27.5",
    "FZ 27.6",
    "FZ 27.7",
    "FZ 27.8",
    "FZ 27.9",
    "FZ 27.10",
    "FZ 27.11",
    "FZ 27.12",
    "FZ 27.13",
    "FZ 27.14",
    "FZ 27.15",
    "FZ 27.16",
    "FZ 27.17",
)

EXPECTED_NATIONAL_BEV = {
    "2026-01-01": 2_034_260,
    "2026-04-01": 2_169_717,
    "2026-07-01": 2_365_047,
}
EXPECTED_DISTRICT_BEV = {
    "2026-01-01": 2_031_870,
    "2026-04-01": 2_167_111,
    "2026-07-01": 2_362_218,
}
EXPECTED_NATIONAL_PHEV = {
    "2026-01-01": 1_122_958,
    "2026-04-01": 1_167_434,
    "2026-07-01": 1_226_863,
}
EXPECTED_NATIONAL_PASSENGER_CARS = {
    "2026-01-01": 49_486_487,
    "2026-04-01": 49_546_014,
    "2026-07-01": 49_696_710,
}

# The source files are part of the local Batch 15 evidence chain.  A changed
# workbook must be investigated before the analysis is allowed to proceed.
EXPECTED_FINGERPRINTS = {
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
}

MIN_BASELINE_BEV_FOR_PERCENT_RANKING = 1_000


class AnalysisError(RuntimeError):
    """Raised when a reproducibility or reconciliation check fails."""


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


def as_date_string(value: Any) -> str:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()[:10]
    return str(value)[:10]


def as_int(value: Any, label: str) -> int:
    require(value is not None, f"Unexpected NULL for {label}")
    return int(value)


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


def quantile(values: Sequence[float], probability: float) -> Optional[float]:
    clean = sorted(float(value) for value in values if value is not None and math.isfinite(float(value)))
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    position = (len(clean) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return clean[lower]
    fraction = position - lower
    return clean[lower] + (clean[upper] - clean[lower]) * fraction


def distribution(values: Sequence[float]) -> Dict[str, Optional[float]]:
    clean = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not clean:
        return {"count": 0, "min": None, "p10": None, "median": None, "mean": None, "p90": None, "max": None, "stddev": None}
    return {
        "count": len(clean),
        "min": min(clean),
        "p10": quantile(clean, 0.10),
        "median": statistics.median(clean),
        "mean": statistics.mean(clean),
        "p90": quantile(clean, 0.90),
        "max": max(clean),
        "stddev": statistics.pstdev(clean) if len(clean) > 1 else 0.0,
    }


def pearson(values_x: Sequence[float], values_y: Sequence[float]) -> Optional[float]:
    pairs = [
        (float(x), float(y))
        for x, y in zip(values_x, values_y)
        if x is not None and y is not None and math.isfinite(float(x)) and math.isfinite(float(y))
    ]
    if len(pairs) < 2:
        return None
    mean_x = statistics.mean(x for x, _ in pairs)
    mean_y = statistics.mean(y for _, y in pairs)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denominator_x = math.sqrt(sum((x - mean_x) ** 2 for x, _ in pairs))
    denominator_y = math.sqrt(sum((y - mean_y) ** 2 for _, y in pairs))
    if denominator_x == 0 or denominator_y == 0:
        return None
    return numerator / (denominator_x * denominator_y)


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
    return value


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field)) for field in fieldnames})


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> List[str]:
    lines = [
        "| " + " | ".join(str(item) for item in headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines


SHEET_METADATA: Dict[str, Dict[str, str]] = {
    "Deckblatt": {
        "analytical_grain": "Workbook cover / metadata",
        "geographic_level": "None",
        "vehicle_categories": "None; publication metadata only",
        "owner_groups": "None",
        "coverage_limitations": "Cover text and release context, not a measurement table",
        "row_role": "Metadata",
        "aggregation_suitability": "Not suitable for aggregation",
        "source_columns": "Published cover text",
    },
    "Impressum": {
        "analytical_grain": "Publication metadata",
        "geographic_level": "None",
        "vehicle_categories": "None; publication date and legal notice",
        "owner_groups": "None",
        "coverage_limitations": "Publication and copyright notes only",
        "row_role": "Metadata",
        "aggregation_suitability": "Not suitable for aggregation",
        "source_columns": "Published imprint text",
    },
    "Inhaltsverzeichnis": {
        "analytical_grain": "Worksheet index",
        "geographic_level": "None",
        "vehicle_categories": "Worksheet titles only",
        "owner_groups": "None",
        "coverage_limitations": "Index of tables; not a data table",
        "row_role": "Metadata",
        "aggregation_suitability": "Not suitable for aggregation",
        "source_columns": "Published table titles",
    },
    "FZ 27.1": {
        "analytical_grain": "Federal state × vehicle type, with subtotals",
        "geographic_level": "16 states, Sonstige, Deutschland",
        "vehicle_categories": "Vehicle types and passenger cars",
        "owner_groups": "Not published",
        "coverage_limitations": "State-level vehicle-type table; subtotal and national rows are also present",
        "row_role": "Detail plus subtotal/national total",
        "aggregation_suitability": "Suitable only after filtering one reporting grain",
        "source_columns": "Vehicle type × vehicle counts",
    },
    "FZ 27.2": {
        "analytical_grain": "Federal state × fuel type × vehicle type, with subtotals",
        "geographic_level": "16 states, Sonstige, Deutschland",
        "vehicle_categories": "BEV, Hybrid insgesamt, darunter Plug-in, fuel categories and others",
        "owner_groups": "Not published",
        "coverage_limitations": "PHEV is a nested detail under Hybrid insgesamt; do not add it to the mutually exclusive total",
        "row_role": "Detail plus subtotal/national total",
        "aggregation_suitability": "Suitable for controlled aggregation using mutually exclusive fuel rows",
        "source_columns": "Fuel type × vehicle type counts",
    },
    "FZ 27.3": {
        "analytical_grain": "Federal state × emissions group × vehicle type",
        "geographic_level": "Federal state and national reporting rows",
        "vehicle_categories": "Emission groups and vehicle types",
        "owner_groups": "Not published",
        "coverage_limitations": "Emissions classification is an alternative breakdown to fuel/owner tables",
        "row_role": "Detail plus subtotal/national total",
        "aggregation_suitability": "Suitable only within one emissions definition and reporting grain",
        "source_columns": "Emissions group × vehicle counts",
    },
    "FZ 27.4": {
        "analytical_grain": "Passenger-car fuel type × emissions group",
        "geographic_level": "National/state table as published",
        "vehicle_categories": "Fuel/energy source and emissions groups",
        "owner_groups": "Not published",
        "coverage_limitations": "Alternative emissions breakdown; not a replacement for FZ 27.2 or FZ 27.15",
        "row_role": "Detail plus subtotal/national total",
        "aggregation_suitability": "Suitable only within the published emissions table",
        "source_columns": "Fuel type × emissions group counts",
    },
    "FZ 27.5": {
        "analytical_grain": "Federal state/residual/national × holder group × fuel type",
        "geographic_level": "16 states, Sonstige, Deutschland",
        "vehicle_categories": "BEV, Hybrid insgesamt, Plug-in, fuel categories and total passenger cars",
        "owner_groups": "Commercial and private; published totals include missing/implausible holder groups",
        "coverage_limitations": "Owner rows are directly supported at state/residual/national grain; no district ownership is published",
        "row_role": "Owner detail plus subtotal/national total",
        "aggregation_suitability": "Suitable when owner rows and published totals are kept separate",
        "source_columns": "Holder group × fuel type × passenger cars",
    },
    "FZ 27.6": {
        "analytical_grain": "Vehicle class/weight × emissions group",
        "geographic_level": "As published; no registration-district grain",
        "vehicle_categories": "Commercial vehicle classes and emissions groups",
        "owner_groups": "Not published",
        "coverage_limitations": "Non-passenger-car emissions/weight breakdown",
        "row_role": "Detail plus totals",
        "aggregation_suitability": "Suitable only for its own vehicle-class measures",
        "source_columns": "Weight class × emissions group counts",
    },
    "FZ 27.7": {
        "analytical_grain": "Vehicle age × fuel type × vehicle type",
        "geographic_level": "National reporting table",
        "vehicle_categories": "Fuel/energy source and age bands",
        "owner_groups": "Not published",
        "coverage_limitations": "Age profile is a national alternative breakdown, not a regional time series",
        "row_role": "Detail plus totals",
        "aggregation_suitability": "Suitable only within the age table; do not combine with regional rows",
        "source_columns": "Age band × fuel/vehicle counts",
    },
    "FZ 27.8": {
        "analytical_grain": "Vehicle type × selected energy source",
        "geographic_level": "National reporting table",
        "vehicle_categories": "BEV, fuel-cell, PHEV, hybrid and alternative-drive totals",
        "owner_groups": "Not published",
        "coverage_limitations": "National vehicle-type view; alternative-drive categories contain nested measures",
        "row_role": "Detail plus totals",
        "aggregation_suitability": "Suitable only with explicit category-overlap handling",
        "source_columns": "Vehicle type × energy-source counts",
    },
    "FZ 27.9": {
        "analytical_grain": "National passenger-car stock × stock quarter × energy source",
        "geographic_level": "National",
        "vehicle_categories": "BEV, PHEV, other alternative drives and passenger-car total",
        "owner_groups": "Not published",
        "coverage_limitations": "Historical quarterly series; releases overlap and must be deduplicated by stock date",
        "row_role": "Historical detail",
        "aggregation_suitability": "Suitable for national history after deterministic overlap deduplication",
        "source_columns": "Quarter × energy-source stock counts",
    },
    "FZ 27.10": {
        "analytical_grain": "Passenger-car segment × energy source",
        "geographic_level": "National reporting table",
        "vehicle_categories": "Segments and selected energy sources",
        "owner_groups": "Not published",
        "coverage_limitations": "Segment table is an alternative national breakdown",
        "row_role": "Detail plus totals",
        "aggregation_suitability": "Suitable only within complete segment universe and selected measures",
        "source_columns": "Segment × energy-source counts",
    },
    "FZ 27.11": {
        "analytical_grain": "Make × energy source",
        "geographic_level": "National reporting table",
        "vehicle_categories": "Makes and selected energy sources",
        "owner_groups": "Not published",
        "coverage_limitations": "Make-level alternative breakdown; category totals must not be combined with other tables",
        "row_role": "Detail plus totals",
        "aggregation_suitability": "Suitable for make-level description when all published rows are retained",
        "source_columns": "Make × energy-source counts",
    },
    "FZ 27.12": {
        "analytical_grain": "Make × current/prior alternative-drive and BEV stock/change",
        "geographic_level": "National reporting table",
        "vehicle_categories": "Alternative drive and BEV current/prior values",
        "owner_groups": "Not published",
        "coverage_limitations": "Published change table is not a complete three-snapshot regional series",
        "row_role": "Detail plus change columns",
        "aggregation_suitability": "Suitable for its selected make/change measures only",
        "source_columns": "Make × current/prior/change measures",
    },
    "FZ 27.13": {
        "analytical_grain": "Selected top-15 make chart",
        "geographic_level": "National",
        "vehicle_categories": "Alternative-drive makes",
        "owner_groups": "Not published",
        "coverage_limitations": "Chart/selected top list, not a complete stock universe",
        "row_role": "Derived presentation table",
        "aggregation_suitability": "Not suitable for national stock aggregation",
        "source_columns": "Chart labels and selected values",
    },
    "FZ 27.14": {
        "analytical_grain": "Selected top-10 model series × energy source",
        "geographic_level": "National",
        "vehicle_categories": "Selected models and alternative drives",
        "owner_groups": "Not published",
        "coverage_limitations": "Selected models only; not a complete model universe",
        "row_role": "Selected detail plus total",
        "aggregation_suitability": "Not suitable for complete national stock aggregation",
        "source_columns": "Selected model × current/prior values",
    },
    "FZ 27.15": {
        "analytical_grain": "KBA registration region × snapshot date",
        "geographic_level": "400 registration-region codes",
        "vehicle_categories": "Passenger-car total, BEV, PHEV and alternative-drive fields",
        "owner_groups": "Not published",
        "coverage_limitations": "400-code KBA registration-region coverage; Trier city and Trier-Saarburg are one shared code 07211",
        "row_role": "Detail rows",
        "aggregation_suitability": "Suitable for 400-region snapshot aggregation; no BBSR equivalence is implied",
        "source_columns": "KBA code/name × passenger-car/BEV/PHEV counts",
    },
    "FZ 27.16": {
        "analytical_grain": "Postcode × holder group × BEV/PHEV × snapshot date",
        "geographic_level": "Postcodes; no district/state identifier in normalized fields",
        "vehicle_categories": "BEV, PHEV and total passenger cars",
        "owner_groups": "Commercial and private",
        "coverage_limitations": "Postcode coverage varies slightly; numeric cells contain NULL after parsing source dots",
        "row_role": "Detail rows",
        "aggregation_suitability": "Descriptive at postcode grain with missing-cell audit; not a district crosswalk",
        "source_columns": "Postcode × commercial/private total/BEV/PHEV",
    },
    "FZ 27.17": {
        "analytical_grain": "Municipality × KBA registration district × holder group × snapshot date",
        "geographic_level": "Municipality rows nested under 400 KBA registration districts",
        "vehicle_categories": "BEV, PHEV and total passenger cars",
        "owner_groups": "Commercial and private",
        "coverage_limitations": "No municipality code; names repeat across districts and numeric cells contain NULL after parsing source dots",
        "row_role": "Detail rows",
        "aggregation_suitability": "Use source key (district code plus municipality name) only; do not aggregate names globally",
        "source_columns": "District × municipality × commercial/private total/BEV/PHEV",
    },
}


def fingerprint_sources() -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for relative, (expected, purpose) in EXPECTED_FINGERPRINTS.items():
        path = ROOT / relative
        require(path.is_file(), f"Missing source workbook: {relative}")
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


def validate_database_contract(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    required = {
        "raw.kba_rows": "BASE TABLE",
        "core.kba_state_fuel_stock": "BASE TABLE",
        "core.kba_district_ev_stock": "BASE TABLE",
        "core.kba_postcode_ev_stock": "BASE TABLE",
        "core.kba_municipality_ev_stock": "BASE TABLE",
        "analytics.kba_national_quarterly_stock": "VIEW",
    }
    result: Dict[str, Any] = {}
    for name, expected_type in required.items():
        actual_type = table_type(conn, name)
        require(actual_type == expected_type, f"Unexpected database object contract for {name}: {actual_type}")
        result[name] = actual_type
    require(conn.execute("SELECT 1").fetchone()[0] == 1, "Read-only DuckDB connectivity check failed")

    source_rows = query_dicts(
        conn,
        """
        SELECT source_id, reference_date, COUNT(*) AS row_count,
               COUNT(DISTINCT sheet_name) AS sheet_count
        FROM raw.kba_rows
        WHERE source_id IN (?, ?, ?)
        GROUP BY source_id, reference_date
        ORDER BY source_id
        """,
        [SOURCE_IDS[date] for date in DATES],
    )
    require(len(source_rows) == 3, f"Expected three KBA source groups, found {len(source_rows)}")
    require(all(int(row["sheet_count"]) == 20 for row in source_rows), "One or more KBA releases does not contain 20 worksheets")
    result["source_groups"] = source_rows
    return result


def collect_worksheet_inventory(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    counts = query_dicts(
        conn,
        """
        SELECT source_id, reference_date, sheet_name, COUNT(*) AS raw_nonempty_rows,
               MIN(excel_row) AS first_excel_row, MAX(excel_row) AS last_excel_row
        FROM raw.kba_rows
        WHERE source_id IN (?, ?, ?)
        GROUP BY source_id, reference_date, sheet_name
        ORDER BY source_id, sheet_name
        """,
        [SOURCE_IDS[date] for date in DATES],
    )
    require(len(counts) == 60, f"Expected 60 source-release worksheet rows, found {len(counts)}")
    inventory: List[Dict[str, Any]] = []
    columns = [f"col_{letter}" for letter in "abcdefghijklmno"]
    for item in counts:
        source_id = str(item["source_id"])
        sheet = str(item["sheet_name"])
        require(sheet in EXPECTED_SHEETS, f"Unexpected worksheet in raw KBA data: {sheet}")
        rows = query_dicts(
            conn,
            """
            SELECT excel_row, col_a, col_b, col_c, col_d, col_e, col_f, col_g,
                   col_h, col_i, col_j, col_k, col_l, col_m, col_n, col_o
            FROM raw.kba_rows
            WHERE source_id = ? AND sheet_name = ? AND excel_row IN (6, 7)
            ORDER BY excel_row
            """,
            [source_id, sheet],
        )
        title_parts: List[str] = []
        for row in rows:
            for column in columns:
                value = row.get(column)
                if value is not None and str(value).strip():
                    title_parts.append(" ".join(str(value).split()))
                    break
        metadata = SHEET_METADATA[sheet]
        inventory.append(
            {
                "source_id": source_id,
                "reference_date": as_date_string(item["reference_date"]),
                "sheet_name": sheet,
                "published_title": " ".join(title_parts),
                "raw_nonempty_rows": int(item["raw_nonempty_rows"]),
                "first_excel_row": int(item["first_excel_row"]),
                "last_excel_row": int(item["last_excel_row"]),
                **metadata,
            }
        )
    require({row["sheet_name"] for row in inventory if row["reference_date"] == DATES[0]} == set(EXPECTED_SHEETS), "Worksheet inventory is incomplete")
    return inventory


def load_state_fuel(conn: duckdb.DuckDBPyConnection) -> Dict[Tuple[str, str, str], int]:
    rows = query_dicts(
        conn,
        """
        SELECT reference_date, state_name, fuel_type, passenger_cars
        FROM core.kba_state_fuel_stock
        WHERE source_id IN (?, ?, ?)
        ORDER BY reference_date, state_name, fuel_type
        """,
        [SOURCE_IDS[date] for date in DATES],
    )
    values: Dict[Tuple[str, str, str], int] = {}
    for row in rows:
        key = (as_date_string(row["reference_date"]), str(row["state_name"]), str(row["fuel_type"]))
        require(key not in values, f"Duplicate state/fuel row: {key}")
        values[key] = as_int(row["passenger_cars"], str(key))
    for date in DATES:
        for geography in (*FEDERAL_STATES, RESIDUAL_GEOGRAPHY, NATIONAL_GEOGRAPHY):
            for fuel in EXPECTED_FUEL_TYPES:
                require((date, geography, fuel) in values, f"Missing state fuel row: {date}/{geography}/{fuel}")
    return values


def total_passenger_cars(state_fuel: Mapping[Tuple[str, str, str], int], date: str, geography: str) -> int:
    return sum(state_fuel[(date, geography, fuel)] for fuel in MUTUALLY_EXCLUSIVE_TOTAL_FUELS)


def national_reconciliation(
    conn: duckdb.DuckDBPyConnection,
    state_fuel: Mapping[Tuple[str, str, str], int],
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, int]]]:
    district_rows = query_dicts(
        conn,
        """
        SELECT reference_date, district_code, district_name, state_name,
               passenger_cars, bev_cars, phev_cars
        FROM core.kba_district_ev_stock
        WHERE source_id IN (?, ?, ?)
        ORDER BY reference_date, district_code
        """,
        [SOURCE_IDS[date] for date in DATES],
    )
    district_summary: Dict[str, Dict[str, int]] = {}
    for date in DATES:
        current = [row for row in district_rows if as_date_string(row["reference_date"]) == date]
        require(len(current) == 400, f"Expected 400 KBA districts for {date}, found {len(current)}")
        district_summary[date] = {
            "rows": len(current),
            "codes": len({str(row["district_code"]) for row in current}),
            "passenger_cars": sum(as_int(row["passenger_cars"], "district passenger cars") for row in current),
            "bev": sum(as_int(row["bev_cars"], "district BEV") for row in current),
            "phev": sum(as_int(row["phev_cars"], "district PHEV") for row in current),
        }
        require(district_summary[date]["codes"] == 400, f"Duplicate/missing district code for {date}")

    expected_rows: List[Dict[str, Any]] = []
    for date in DATES:
        national_total = total_passenger_cars(state_fuel, date, NATIONAL_GEOGRAPHY)
        state_total = sum(total_passenger_cars(state_fuel, date, state) for state in FEDERAL_STATES)
        residual_total = total_passenger_cars(state_fuel, date, RESIDUAL_GEOGRAPHY)
        national_bev = state_fuel[(date, NATIONAL_GEOGRAPHY, "Elektro (BEV)")]
        state_bev = sum(state_fuel[(date, state, "Elektro (BEV)")] for state in FEDERAL_STATES)
        residual_bev = state_fuel[(date, RESIDUAL_GEOGRAPHY, "Elektro (BEV)")]
        national_phev = state_fuel[(date, NATIONAL_GEOGRAPHY, "darunter Plug-in")]
        state_phev = sum(state_fuel[(date, state, "darunter Plug-in")] for state in FEDERAL_STATES)
        residual_phev = state_fuel[(date, RESIDUAL_GEOGRAPHY, "darunter Plug-in")]
        district = district_summary[date]

        require(national_bev == EXPECTED_NATIONAL_BEV[date], f"National BEV mismatch for {date}: {national_bev}")
        require(district["bev"] == EXPECTED_DISTRICT_BEV[date], f"District BEV mismatch for {date}: {district['bev']}")
        require(national_phev == EXPECTED_NATIONAL_PHEV[date], f"National PHEV mismatch for {date}: {national_phev}")
        require(national_total == EXPECTED_NATIONAL_PASSENGER_CARS[date], f"National passenger-car total mismatch for {date}: {national_total}")
        require(state_bev == district["bev"], f"16-state and district BEV totals differ for {date}")
        require(state_phev == district["phev"], f"16-state and district PHEV totals differ for {date}")
        require(state_total == district["passenger_cars"], f"16-state and district passenger-car totals differ for {date}")
        require(national_bev == state_bev + residual_bev, f"National/state/Sonstige BEV reconciliation failed for {date}")
        require(national_phev == state_phev + residual_phev, f"National/state/Sonstige PHEV reconciliation failed for {date}")
        require(national_total == state_total + residual_total, f"National/state/Sonstige passenger-car reconciliation failed for {date}")

        expected_rows.append(
            {
                "reference_date": date,
                "national_passenger_cars": national_total,
                "sixteen_state_passenger_cars": state_total,
                "sonstige_passenger_cars": residual_total,
                "four_hundred_region_passenger_cars": district["passenger_cars"],
                "national_bev": national_bev,
                "sixteen_state_bev": state_bev,
                "sonstige_bev": residual_bev,
                "four_hundred_region_bev": district["bev"],
                "national_phev": national_phev,
                "sixteen_state_phev": state_phev,
                "sonstige_phev": residual_phev,
                "four_hundred_region_phev": district["phev"],
                "national_minus_four_hundred_region_passenger_cars": national_total - district["passenger_cars"],
                "national_minus_four_hundred_region_bev": national_bev - district["bev"],
                "national_minus_four_hundred_region_phev": national_phev - district["phev"],
                "reconciliation_status": "PASS",
            }
        )
    return expected_rows, district_summary


def build_national_trends(
    reconciliation: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    previous: Optional[Mapping[str, Any]] = None
    for current in reconciliation:
        row = dict(current)
        row.update(
            {
                "bev_share_of_national_passenger_cars_pct": pct(current["national_bev"], current["national_passenger_cars"]),
                "phev_share_of_national_passenger_cars_pct": pct(current["national_phev"], current["national_passenger_cars"]),
                "combined_plugin_stock": int(current["national_bev"]) + int(current["national_phev"]),
                "combined_plugin_share_of_national_passenger_cars_pct": pct(
                    int(current["national_bev"]) + int(current["national_phev"]),
                    current["national_passenger_cars"],
                ),
                "bev_change_from_previous_snapshot": None,
                "bev_pct_change_from_previous_snapshot": None,
                "phev_change_from_previous_snapshot": None,
                "phev_pct_change_from_previous_snapshot": None,
            }
        )
        if previous is not None:
            bev_change = int(current["national_bev"]) - int(previous["national_bev"])
            phev_change = int(current["national_phev"]) - int(previous["national_phev"])
            row["bev_change_from_previous_snapshot"] = bev_change
            row["bev_pct_change_from_previous_snapshot"] = pct(bev_change, previous["national_bev"])
            row["phev_change_from_previous_snapshot"] = phev_change
            row["phev_pct_change_from_previous_snapshot"] = pct(phev_change, previous["national_phev"])
        rows.append(row)
        previous = current
    return rows


def build_state_metrics(
    state_fuel: Mapping[Tuple[str, str, str], int],
) -> List[Dict[str, Any]]:
    geographies = [(*FEDERAL_STATES, RESIDUAL_GEOGRAPHY)]
    geographies = list(geographies[0])
    rows: List[Dict[str, Any]] = []
    jan = DATES[0]
    for geography in geographies:
        scope = "federal_state" if geography in FEDERAL_STATES else "residual_non_state"
        jan_bev = state_fuel[(jan, geography, "Elektro (BEV)")]
        jan_phev = state_fuel[(jan, geography, "darunter Plug-in")]
        for date in DATES:
            total_cars = total_passenger_cars(state_fuel, date, geography)
            bev = state_fuel[(date, geography, "Elektro (BEV)")]
            phev = state_fuel[(date, geography, "darunter Plug-in")]
            national_delta = EXPECTED_NATIONAL_BEV[DATES[-1]] - EXPECTED_NATIONAL_BEV[jan]
            bev_delta = bev - jan_bev
            phev_delta = phev - jan_phev
            rows.append(
                {
                    "reference_date": date,
                    "geography": geography,
                    "geographic_scope": scope,
                    "passenger_car_stock": total_cars,
                    "bev_stock": bev,
                    "phev_stock": phev,
                    "combined_plugin_stock": bev + phev,
                    "bev_penetration_pct": pct(bev, total_cars),
                    "phev_penetration_pct": pct(phev, total_cars),
                    "combined_plugin_penetration_pct": pct(bev + phev, total_cars),
                    "bev_change_jan_to_date": None if date == jan else bev_delta,
                    "bev_growth_pct_jan_to_date": None if date == jan else pct(bev_delta, jan_bev),
                    "phev_change_jan_to_date": None if date == jan else phev_delta,
                    "phev_growth_pct_jan_to_date": None if date == jan else pct(phev_delta, jan_phev),
                    "contribution_to_national_bev_growth_pct": None if date == jan else pct(bev_delta, national_delta),
                    "denominator_definition": "Mutually exclusive FZ 27.2 passenger-car fuel rows; PHEV is not added to Hybrid insgesamt",
                }
            )
    require(len(rows) == 51, f"Expected 51 state/residual/date rows, found {len(rows)}")
    return rows


def build_district_metrics(
    conn: duckdb.DuckDBPyConnection,
    reconciliation: Sequence[Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    raw_rows = query_dicts(
        conn,
        """
        SELECT reference_date, district_code, district_name, state_name,
               passenger_cars, bev_cars, phev_cars
        FROM core.kba_district_ev_stock
        WHERE source_id IN (?, ?, ?)
        ORDER BY district_code, reference_date
        """,
        [SOURCE_IDS[date] for date in DATES],
    )
    by_code_date: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in raw_rows:
        date = as_date_string(row["reference_date"])
        code = str(row["district_code"])
        key = (code, date)
        require(key not in by_code_date, f"Duplicate district/date row: {key}")
        for field in ("passenger_cars", "bev_cars", "phev_cars"):
            require(row[field] is not None, f"NULL district metric {field}: {key}")
        require(int(row["passenger_cars"]) > 0, f"Zero passenger-car denominator: {key}")
        by_code_date[key] = {
            "district_code": code,
            "district_name": str(row["district_name"]),
            "state_name": str(row["state_name"]),
            "passenger_cars": int(row["passenger_cars"]),
            "bev": int(row["bev_cars"]),
            "phev": int(row["phev_cars"]),
        }

    codes = sorted({code for code, _ in by_code_date})
    require(len(codes) == 400, f"Expected 400 district codes, found {len(codes)}")
    identity_changes: List[Dict[str, Any]] = []
    for code in codes:
        identities = {(by_code_date[(code, date)]["district_name"], by_code_date[(code, date)]["state_name"]) for date in DATES}
        if len(identities) != 1:
            identity_changes.append({"district_code": code, "identities": sorted(identities)})
    require(not identity_changes, f"District identity changed over time: {identity_changes[:3]}")

    recon_by_date = {str(row["reference_date"]): row for row in reconciliation}
    rows: List[Dict[str, Any]] = []
    for code in codes:
        jan = by_code_date[(code, DATES[0])]
        jul = by_code_date[(code, DATES[-1])]
        bev_change = jul["bev"] - jan["bev"]
        phev_change = jul["phev"] - jan["phev"]
        row: Dict[str, Any] = {
            "district_code": code,
            "district_name": jan["district_name"],
            "state_name": jan["state_name"],
            "baseline_bev_threshold_for_pct_ranking": MIN_BASELINE_BEV_FOR_PERCENT_RANKING,
            "bev_growth_pct_ranking_eligible": jan["bev"] >= MIN_BASELINE_BEV_FOR_PERCENT_RANKING,
            "bev_growth_pct_exclusion_reason": "" if jan["bev"] >= MIN_BASELINE_BEV_FOR_PERCENT_RANKING else "baseline BEV below exploratory threshold",
            "bev_change_jan_to_jul": bev_change,
            "bev_growth_pct_jan_to_jul": pct(bev_change, jan["bev"]),
            "phev_change_jan_to_jul": phev_change,
            "phev_growth_pct_jan_to_jul": pct(phev_change, jan["phev"]),
        }
        for date in DATES:
            value = by_code_date[(code, date)]
            suffix = date.replace("-", "_")
            national = recon_by_date[date]
            row.update(
                {
                    f"passenger_car_stock_{suffix}": value["passenger_cars"],
                    f"bev_stock_{suffix}": value["bev"],
                    f"phev_stock_{suffix}": value["phev"],
                    f"combined_plugin_stock_{suffix}": value["bev"] + value["phev"],
                    f"bev_penetration_pct_{suffix}": pct(value["bev"], value["passenger_cars"]),
                    f"phev_penetration_pct_{suffix}": pct(value["phev"], value["passenger_cars"]),
                    f"combined_plugin_penetration_pct_{suffix}": pct(value["bev"] + value["phev"], value["passenger_cars"]),
                    f"bev_share_of_national_stock_pct_{suffix}": pct(value["bev"], national["national_bev"]),
                    f"phev_share_of_national_stock_pct_{suffix}": pct(value["phev"], national["national_phev"]),
                    f"bev_share_of_400_region_stock_pct_{suffix}": pct(value["bev"], national["four_hundred_region_bev"]),
                    f"phev_share_of_400_region_stock_pct_{suffix}": pct(value["phev"], national["four_hundred_region_phev"]),
                }
            )
        rows.append(row)

    require(len(rows) == 400, f"Expected 400 district metric rows, found {len(rows)}")
    eligible = [row for row in rows if row["bev_growth_pct_ranking_eligible"]]
    checks = {
        "rows": len(rows),
        "codes_per_snapshot": {date: sum(1 for key in by_code_date if key[1] == date) for date in DATES},
        "identity_changes": identity_changes,
        "missing_codes": [],
        "numeric_nulls": 0,
        "zero_denominators": 0,
        "pct_growth_eligible_count": len(eligible),
        "pct_growth_excluded_count": len(rows) - len(eligible),
        "trier_row": next(row for row in rows if row["district_code"] == "07211"),
    }
    require(checks["codes_per_snapshot"] == {date: 400 for date in DATES}, "District snapshot code coverage changed")
    require(checks["trier_row"]["district_name"] == "TRIER-SAARBURG", "Unexpected Trier shared KBA region identity")
    return rows, checks


def build_ownership_metrics(conn: duckdb.DuckDBPyConnection) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    owner_rows = query_dicts(
        conn,
        """
        WITH raw_values AS (
          SELECT source_id, reference_date, excel_row,
                 NULLIF(TRIM(col_b), '') AS geography_raw,
                 NULLIF(TRIM(col_c), '') AS holder_group,
                 TRY_CAST(col_g AS BIGINT) AS bev,
                 TRY_CAST(col_i AS BIGINT) AS phev,
                 TRY_CAST(col_k AS BIGINT) AS passenger_cars
          FROM raw.kba_rows
          WHERE sheet_name = 'FZ 27.5'
        ), filled AS (
          SELECT *,
                 LAST_VALUE(
                   CASE WHEN geography_raw IS NOT NULL
                              AND geography_raw NOT ILIKE '% zusammen'
                              AND geography_raw NOT ILIKE '% insgesamt'
                        THEN geography_raw END
                 IGNORE NULLS) OVER (
                   PARTITION BY source_id ORDER BY excel_row
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                 ) AS geography
          FROM raw_values
        )
        SELECT source_id, reference_date, excel_row, geography, holder_group,
               bev, phev, passenger_cars
        FROM filled
        WHERE holder_group IN ('Gewerbliche Halterinnen und Halter', 'Private Halterinnen und Halter')
        ORDER BY reference_date, excel_row
        """,
    )
    total_rows = query_dicts(
        conn,
        """
        SELECT source_id, reference_date, excel_row,
               REGEXP_REPLACE(TRIM(col_b), '\\s+(zusammen|insgesamt)$', '') AS geography,
               TRY_CAST(col_g AS BIGINT) AS bev,
               TRY_CAST(col_i AS BIGINT) AS phev,
               TRY_CAST(col_k AS BIGINT) AS passenger_cars
        FROM raw.kba_rows
        WHERE sheet_name = 'FZ 27.5'
          AND NULLIF(TRIM(col_c), '') IS NULL
          AND (TRIM(col_b) ILIKE '% zusammen' OR TRIM(col_b) ILIKE '% insgesamt')
        ORDER BY reference_date, excel_row
        """,
    )
    require(len(owner_rows) == 108, f"Expected 108 owner rows, found {len(owner_rows)}")
    require(len(total_rows) == 54, f"Expected 54 published ownership total rows, found {len(total_rows)}")

    owners: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for row in owner_rows:
        key = (as_date_string(row["reference_date"]), str(row["geography"]), str(row["holder_group"]))
        require(key not in owners, f"Duplicate ownership row: {key}")
        require(row["bev"] is not None and row["phev"] is not None and row["passenger_cars"] is not None, f"NULL owner metric: {key}")
        owners[key] = {
            "bev": int(row["bev"]),
            "phev": int(row["phev"]),
            "passenger_cars": int(row["passenger_cars"]),
        }
    totals: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in total_rows:
        key = (as_date_string(row["reference_date"]), str(row["geography"]))
        require(key not in totals, f"Duplicate ownership total row: {key}")
        require(row["bev"] is not None and row["phev"] is not None and row["passenger_cars"] is not None, f"NULL ownership total: {key}")
        totals[key] = {
            "bev": int(row["bev"]),
            "phev": int(row["phev"]),
            "passenger_cars": int(row["passenger_cars"]),
        }

    expected_geographies = set(FEDERAL_STATES) | {RESIDUAL_GEOGRAPHY, NATIONAL_GEOGRAPHY}
    require({geography for _, geography in totals} == expected_geographies, "FZ 27.5 total geography coverage changed")
    require({geography for _, geography, _ in owners} == expected_geographies, "FZ 27.5 owner geography coverage changed")

    rows: List[Dict[str, Any]] = []
    for date in DATES:
        for geography in (*FEDERAL_STATES, RESIDUAL_GEOGRAPHY, NATIONAL_GEOGRAPHY):
            total = totals[(date, geography)]
            commercial = owners[(date, geography, "Gewerbliche Halterinnen und Halter")]
            private = owners[(date, geography, "Private Halterinnen und Halter")]
            unknown_bev = total["bev"] - commercial["bev"] - private["bev"]
            unknown_phev = total["phev"] - commercial["phev"] - private["phev"]
            unknown_cars = total["passenger_cars"] - commercial["passenger_cars"] - private["passenger_cars"]
            require(unknown_bev >= 0 and unknown_phev >= 0 and unknown_cars >= 0, f"Negative unallocated ownership residual: {date}/{geography}")
            observed_bev = commercial["bev"] + private["bev"]
            observed_phev = commercial["phev"] + private["phev"]
            scope = "federal_state" if geography in FEDERAL_STATES else ("residual_non_state" if geography == RESIDUAL_GEOGRAPHY else "national")
            rows.append(
                {
                    "reference_date": date,
                    "geography": geography,
                    "geographic_scope": scope,
                    "published_total_passenger_cars": total["passenger_cars"],
                    "published_total_bev": total["bev"],
                    "commercial_bev": commercial["bev"],
                    "private_bev": private["bev"],
                    "unallocated_or_unknown_bev": unknown_bev,
                    "owner_observed_bev": observed_bev,
                    "commercial_bev_share_of_observed_pct": pct(commercial["bev"], observed_bev),
                    "private_bev_share_of_observed_pct": pct(private["bev"], observed_bev),
                    "commercial_bev_share_of_published_total_pct": pct(commercial["bev"], total["bev"]),
                    "private_bev_share_of_published_total_pct": pct(private["bev"], total["bev"]),
                    "owner_observed_bev_coverage_pct": pct(observed_bev, total["bev"]),
                    "published_total_phev": total["phev"],
                    "commercial_phev": commercial["phev"],
                    "private_phev": private["phev"],
                    "unallocated_or_unknown_phev": unknown_phev,
                    "owner_observed_phev": observed_phev,
                    "commercial_phev_share_of_observed_pct": pct(commercial["phev"], observed_phev),
                    "private_phev_share_of_observed_pct": pct(private["phev"], observed_phev),
                    "commercial_phev_share_of_published_total_pct": pct(commercial["phev"], total["phev"]),
                    "private_phev_share_of_published_total_pct": pct(private["phev"], total["phev"]),
                    "owner_observed_phev_coverage_pct": pct(observed_phev, total["phev"]),
                    "publisher_note": "Published zusammen/insgesamt rows include vehicles with missing or implausible holder-group data",
                }
            )
    require(len(rows) == 54, f"Expected 54 ownership metric rows, found {len(rows)}")
    return rows, {
        "owner_rows": len(owner_rows),
        "published_total_rows": len(total_rows),
        "geographies_per_snapshot": len(expected_geographies),
        "supported_combinations": "commercial/private × BEV/PHEV × state/residual/national",
        "district_owner_metrics_supported": False,
    }


def inspect_postcode_municipality(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    postcode = query_dicts(
        conn,
        """
        SELECT reference_date,
               COUNT(*) AS row_count,
               COUNT(DISTINCT postal_code) AS distinct_postal_codes,
               COUNT(*) - COUNT(DISTINCT postal_code) AS duplicate_rows,
               COUNT(*) FILTER (WHERE commercial_total_cars IS NULL OR commercial_bev IS NULL OR commercial_phev IS NULL OR private_total_cars IS NULL OR private_bev IS NULL OR private_phev IS NULL) AS rows_with_nulls,
               SUM(CASE WHEN commercial_total_cars IS NULL THEN 1 ELSE 0 END
                 + CASE WHEN commercial_bev IS NULL THEN 1 ELSE 0 END
                 + CASE WHEN commercial_phev IS NULL THEN 1 ELSE 0 END
                 + CASE WHEN private_total_cars IS NULL THEN 1 ELSE 0 END
                 + CASE WHEN private_bev IS NULL THEN 1 ELSE 0 END
                 + CASE WHEN private_phev IS NULL THEN 1 ELSE 0 END) AS null_measure_cells,
               COUNT(*) FILTER (WHERE commercial_total_cars IS NOT NULL AND commercial_bev IS NOT NULL AND commercial_phev IS NOT NULL AND private_total_cars IS NOT NULL AND private_bev IS NOT NULL AND private_phev IS NOT NULL) AS fully_observed_rows
        FROM core.kba_postcode_ev_stock
        GROUP BY reference_date ORDER BY reference_date
        """,
    )
    postcode_duplicate_groups = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM (
              SELECT reference_date, postal_code
              FROM core.kba_postcode_ev_stock
              GROUP BY reference_date, postal_code
              HAVING COUNT(*) <> 1
            )
            """
        ).fetchone()[0]
    )
    municipality = query_dicts(
        conn,
        """
        SELECT reference_date,
               COUNT(*) AS row_count,
               COUNT(DISTINCT district_code) AS district_codes,
               COUNT(DISTINCT municipality_name) AS distinct_municipality_names,
               COUNT(*) FILTER (WHERE possible_total_row) AS possible_total_rows,
               COUNT(*) FILTER (WHERE commercial_total_cars IS NULL OR commercial_bev IS NULL OR commercial_phev IS NULL OR private_total_cars IS NULL OR private_bev IS NULL OR private_phev IS NULL) AS rows_with_nulls,
               SUM(CASE WHEN commercial_total_cars IS NULL THEN 1 ELSE 0 END
                 + CASE WHEN commercial_bev IS NULL THEN 1 ELSE 0 END
                 + CASE WHEN commercial_phev IS NULL THEN 1 ELSE 0 END
                 + CASE WHEN private_total_cars IS NULL THEN 1 ELSE 0 END
                 + CASE WHEN private_bev IS NULL THEN 1 ELSE 0 END
                 + CASE WHEN private_phev IS NULL THEN 1 ELSE 0 END) AS null_measure_cells,
               COUNT(*) FILTER (WHERE commercial_total_cars IS NOT NULL AND commercial_bev IS NOT NULL AND commercial_phev IS NOT NULL AND private_total_cars IS NOT NULL AND private_bev IS NOT NULL AND private_phev IS NOT NULL) AS fully_observed_rows
        FROM core.kba_municipality_ev_stock
        GROUP BY reference_date ORDER BY reference_date
        """,
    )
    municipality_duplicate_groups = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM (
              SELECT reference_date, district_code, municipality_name
              FROM core.kba_municipality_ev_stock
              GROUP BY reference_date, district_code, municipality_name
              HAVING COUNT(*) <> 1
            )
            """
        ).fetchone()[0]
    )
    repeated_names_across_districts = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM (
              SELECT municipality_name
              FROM core.kba_municipality_ev_stock
              GROUP BY municipality_name
              HAVING COUNT(DISTINCT district_code) > 1
            )
            """
        ).fetchone()[0]
    )
    require(postcode_duplicate_groups == 0, "Duplicate postcode/date rows found")
    require(municipality_duplicate_groups == 0, "Duplicate municipality/district/date rows found")
    require(all(int(row["district_codes"]) == 400 for row in municipality), "Municipality table does not cover 400 KBA district codes")
    return {
        "postcode": postcode,
        "postcode_duplicate_groups": postcode_duplicate_groups,
        "municipality": municipality,
        "municipality_duplicate_groups": municipality_duplicate_groups,
        "municipality_names_repeated_across_districts": repeated_names_across_districts,
        "postcode_interpretation": "Descriptive postcode grain only; no district/state identifiers are present",
        "municipality_interpretation": "District code plus municipality name is the source key; municipality names are not globally unique",
    }


def load_history(conn: duckdb.DuckDBPyConnection) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = query_dicts(
        conn,
        """
        SELECT stock_date, report_snapshot, passenger_cars_total, passenger_bev, passenger_phev
        FROM analytics.kba_national_quarterly_stock
        ORDER BY stock_date
        """,
    )
    require(len(rows) >= 7, "Historical quarterly view is unexpectedly short")
    normalized: List[Dict[str, Any]] = []
    by_date: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        date = as_date_string(row["stock_date"])
        require(date not in by_date, f"Duplicate deduplicated historical stock date: {date}")
        normalized_row = {
            "stock_date": date,
            "report_snapshot": as_date_string(row["report_snapshot"]),
            "passenger_cars_total": as_int(row["passenger_cars_total"], f"history total {date}"),
            "passenger_bev": as_int(row["passenger_bev"], f"history BEV {date}"),
            "passenger_phev": as_int(row["passenger_phev"], f"history PHEV {date}"),
        }
        normalized.append(normalized_row)
        by_date[date] = normalized_row
    for date in DATES:
        require(date in by_date, f"Missing current national history date: {date}")
        require(by_date[date]["passenger_bev"] == EXPECTED_NATIONAL_BEV[date], f"Historical BEV mismatch for {date}")
        require(by_date[date]["passenger_phev"] == EXPECTED_NATIONAL_PHEV[date], f"Historical PHEV mismatch for {date}")
        require(by_date[date]["passenger_cars_total"] == EXPECTED_NATIONAL_PASSENGER_CARS[date], f"Historical passenger-car mismatch for {date}")
    selected_dates = {normalized[0]["stock_date"]}
    selected_dates.update(row["stock_date"] for row in normalized if row["stock_date"].endswith("-01-01"))
    selected_dates.update(row["stock_date"] for row in normalized if row["stock_date"].endswith("-07-01"))
    selected = [row for row in normalized if row["stock_date"] in selected_dates]
    return normalized, {
        "row_count": len(normalized),
        "earliest_stock_date": normalized[0]["stock_date"],
        "latest_stock_date": normalized[-1]["stock_date"],
        "distinct_report_snapshots": sorted({row["report_snapshot"] for row in normalized}),
        "selected_rows": selected,
        "deduplication_rule": "For overlapping releases, keep one observation per stock_date, preferring the latest report snapshot and then the earliest source row",
    }


def top_rows(rows: Sequence[Mapping[str, Any]], field: str, limit: int = 10, reverse: bool = True, eligible_field: Optional[str] = None) -> List[Mapping[str, Any]]:
    selected = [row for row in rows if row.get(field) is not None and (eligible_field is None or bool(row.get(eligible_field)))]
    return sorted(selected, key=lambda row: (float(row[field]), str(row.get("district_code", ""))), reverse=reverse)[:limit]


def concentration(rows: Sequence[Mapping[str, Any]], field: str, denominator: float, limits: Sequence[int] = (1, 5, 10)) -> Dict[int, Optional[float]]:
    values = sorted((float(row[field]) for row in rows if row.get(field) is not None), reverse=True)
    return {limit: pct(sum(values[:limit]), denominator) for limit in limits}


def build_analysis_summary(
    national_trends: Sequence[Mapping[str, Any]],
    state_metrics: Sequence[Mapping[str, Any]],
    district_metrics: Sequence[Mapping[str, Any]],
    ownership_metrics: Sequence[Mapping[str, Any]],
    geography: Mapping[str, Any],
) -> Dict[str, Any]:
    jan = national_trends[0]
    apr = national_trends[1]
    jul = national_trends[2]
    periods = {
        "2026-01-01_to_2026-04-01": (jan, apr),
        "2026-04-01_to_2026-07-01": (apr, jul),
        "2026-01-01_to_2026-07-01": (jan, jul),
    }
    growth: Dict[str, Dict[str, Any]] = {}
    for label, (start, end) in periods.items():
        bev_change = int(end["national_bev"]) - int(start["national_bev"])
        phev_change = int(end["national_phev"]) - int(start["national_phev"])
        growth[label] = {
            "bev_change": bev_change,
            "bev_pct_change": pct(bev_change, start["national_bev"]),
            "phev_change": phev_change,
            "phev_pct_change": pct(phev_change, start["national_phev"]),
            "bev_to_phev_relative_growth_ratio": ratio(pct(bev_change, start["national_bev"]), pct(phev_change, start["national_phev"])),
        }

    latest_states = [row for row in state_metrics if row["reference_date"] == DATES[-1] and row["geographic_scope"] == "federal_state"]
    largest_state_stock = top_rows(latest_states, "bev_stock", 5)
    highest_state_penetration = sorted(latest_states, key=lambda row: (-float(row["bev_penetration_pct"]), str(row["geography"])))[:5]
    largest_state_growth = sorted(latest_states, key=lambda row: (-int(row["bev_change_jan_to_date"]), str(row["geography"])))[:5]
    highest_state_growth_pct = sorted(latest_states, key=lambda row: (-float(row["bev_growth_pct_jan_to_date"]), str(row["geography"])))[:5]
    district_july_bev_field = "bev_stock_2026_07_01"
    district_july_phev_field = "phev_stock_2026_07_01"
    district_july_bev_total = int(jul["four_hundred_region_bev"])
    district_july_phev_total = int(jul["four_hundred_region_phev"])
    district_growth = [row["bev_growth_pct_jan_to_jul"] for row in district_metrics]
    phev_growth = [row["phev_growth_pct_jan_to_jul"] for row in district_metrics]
    bev_growth_values = [float(value) for value in district_growth if value is not None]
    phev_growth_values = [float(value) for value in phev_growth if value is not None]
    ownership_july = [row for row in ownership_metrics if row["reference_date"] == DATES[-1] and row["geographic_scope"] == "national"]
    require(len(ownership_july) == 1, "National ownership July row missing")
    return {
        "growth": growth,
        "latest_state_rankings": {
            "largest_bev_stock": largest_state_stock,
            "highest_bev_penetration": highest_state_penetration,
            "largest_bev_growth": largest_state_growth,
            "highest_bev_growth_pct": highest_state_growth_pct,
        },
        "district_distributions": {
            "bev_growth_pct_jan_to_jul": distribution(bev_growth_values),
            "phev_growth_pct_jan_to_jul": distribution(phev_growth_values),
            "bev_penetration_pct_july": distribution([row["bev_penetration_pct_2026_07_01"] for row in district_metrics]),
            "phev_penetration_pct_july": distribution([row["phev_penetration_pct_2026_07_01"] for row in district_metrics]),
            "combined_plugin_penetration_pct_july": distribution([row["combined_plugin_penetration_pct_2026_07_01"] for row in district_metrics]),
        },
        "weighted_unweighted_growth": {
            "bev_weighted_pct": pct(jul["four_hundred_region_bev"] - jan["four_hundred_region_bev"], jan["four_hundred_region_bev"]),
            "bev_unweighted_mean_pct": statistics.mean(bev_growth_values),
            "phev_weighted_pct": pct(jul["four_hundred_region_phev"] - jan["four_hundred_region_phev"], jan["four_hundred_region_phev"]),
            "phev_unweighted_mean_pct": statistics.mean(phev_growth_values),
        },
        "district_concentration": {
            "bev_stock_july": concentration(district_metrics, district_july_bev_field, district_july_bev_total),
            "phev_stock_july": concentration(district_metrics, district_july_phev_field, district_july_phev_total),
        },
        "district_growth_correlation_bev_phev": pearson(bev_growth_values, phev_growth_values),
        "ownership_national_july": ownership_july[0],
        "postcode_municipality": geography,
    }


def render_report(
    inventory: Sequence[Mapping[str, Any]],
    fingerprints: Sequence[Mapping[str, Any]],
    database_contract: Mapping[str, Any],
    reconciliation: Sequence[Mapping[str, Any]],
    national_trends: Sequence[Mapping[str, Any]],
    state_metrics: Sequence[Mapping[str, Any]],
    district_metrics: Sequence[Mapping[str, Any]],
    district_checks: Mapping[str, Any],
    ownership_metrics: Sequence[Mapping[str, Any]],
    ownership_checks: Mapping[str, Any],
    geography: Mapping[str, Any],
    history: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> str:
    lines: List[str] = [
        "# Batch 15 — KBA FZ 27 EV stock, growth, geography and ownership analysis",
        "",
        "**Batch status: PASS**",
        "",
        "This is a deterministic, read-only statistical analysis of the three locally preserved KBA FZ 27 releases. It does not change DuckDB objects, raw workbooks, existing Crosswalks, BBSR objects, or charging analytics.",
        "",
        "## Scope and analytical rules",
        "",
        "- KBA snapshots: `2026-01-01`, `2026-04-01`, and `2026-07-01`.",
        "- National/state stock uses `core.kba_state_fuel_stock` and the published `Deutschland`, 16-state, and `Sonstige` rows.",
        "- Registration-region analysis uses `core.kba_district_ev_stock` at KBA registration-region × reference-date grain: 400 codes per snapshot and 1,200 rows in total.",
        "- Passenger-car denominators use mutually exclusive FZ 27.2 fuel rows. `darunter Plug-in` is nested under `Hybrid insgesamt` and is never added to the total a second time.",
        "- The shared KBA registration region `07211 TRIER-SAARBURG` remains one row. No allocation to Trier city or Trier-Saarburg administrative units is performed.",
        "- Percentage-growth rankings use an exploratory minimum January BEV baseline of **1,000 vehicles**. This is a stability filter, not an official standard; excluded rows remain in the diagnostic CSV.",
        "- Stock changes are changes in registered stock between snapshots, not registrations, sales, gross inflows, charging demand, utilization, or causality.",
        "",
        "## Read-only validation contract",
        "",
    ]
    contract_rows = [[name, value] for name, value in database_contract.items() if isinstance(value, str)]
    lines.extend(markdown_table(["Object/check", "Result"], contract_rows))
    lines.extend(
        [
            "",
            "The analysis opened DuckDB with `read_only=True` and issued no DDL/DML. The script is compatible with the existing local Python environment and installs no dependencies.",
            "",
            "## Source worksheet inventory",
            "",
            "The full 60-row inventory is in [`batch15_kba_worksheet_capabilities.csv`](batch15_kba_worksheet_capabilities.csv). It records the actual worksheet title, source row span, analytical grain, geographic level, vehicle/owner dimensions, subtotal behavior, and aggregation suitability for each release. The three workbooks each contain all 20 expected worksheets.",
            "",
        ]
    )
    relevant = [row for row in inventory if row["sheet_name"] in {"FZ 27.2", "FZ 27.5", "FZ 27.9", "FZ 27.15", "FZ 27.16", "FZ 27.17"} and row["reference_date"] == DATES[-1]]
    lines.extend(
        markdown_table(
            ["Sheet", "Published title", "Raw rows", "Grain", "Aggregation status"],
            [[row["sheet_name"], row["published_title"], fmt_int(row["raw_nonempty_rows"]), row["analytical_grain"], row["aggregation_suitability"]] for row in relevant],
        )
    )
    lines.extend(
        [
            "",
            "FZ 27.15 is the appropriate regional stock source for the 400 KBA registration-region analysis. FZ 27.16 and FZ 27.17 are separate postcode/municipality breakdowns with different keys and should not be summed into FZ 27.15 or treated as unique administrative-unit inventories without validation.",
            "",
            "## National stock reconciliation",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Date", "National cars", "16 states", "Sonstige", "400 regions", "National BEV", "16-state BEV", "Sonstige BEV", "400-region BEV", "National PHEV", "400-region PHEV"],
            [
                [
                    row["reference_date"],
                    fmt_int(row["national_passenger_cars"]),
                    fmt_int(row["sixteen_state_passenger_cars"]),
                    fmt_int(row["sonstige_passenger_cars"]),
                    fmt_int(row["four_hundred_region_passenger_cars"]),
                    fmt_int(row["national_bev"]),
                    fmt_int(row["sixteen_state_bev"]),
                    fmt_int(row["sonstige_bev"]),
                    fmt_int(row["four_hundred_region_bev"]),
                    fmt_int(row["national_phev"]),
                    fmt_int(row["four_hundred_region_phev"]),
                ]
                for row in reconciliation
            ],
        )
    )
    lines.extend(
        [
            "",
            "The 16-state sums reconcile exactly to the 400-region table for passenger cars, BEVs and PHEVs. National totals reconcile as 16 states plus `Sonstige`. The remaining passenger cars and EVs are therefore reporting residuals, not unexplained missing vehicle records in this source comparison:",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Date", "National − 400-region cars", "National − 400-region BEV", "National − 400-region PHEV"],
            [[row["reference_date"], fmt_int(row["national_minus_four_hundred_region_passenger_cars"]), fmt_int(row["national_minus_four_hundred_region_bev"]), fmt_int(row["national_minus_four_hundred_region_phev"])] for row in reconciliation],
        )
    )
    lines.extend(
        [
            "",
            "The BEV residuals are `Sonstige`: 2,390 in January, 2,606 in April, and 2,829 in July. The same reporting structure produces PHEV residuals of 1,442, 1,501 and 1,622. Passenger-car residuals are 50,467, 51,367 and 51,855.",
            "",
            "## Analysis A — BEV and PHEV stock growth",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Date", "National cars", "BEV", "BEV share", "PHEV", "PHEV share", "Combined plug-in", "Combined share", "BEV change", "BEV change %", "PHEV change", "PHEV change %"],
            [
                [
                    row["reference_date"],
                    fmt_int(row["national_passenger_cars"]),
                    fmt_int(row["national_bev"]),
                    fmt_pct(row["bev_share_of_national_passenger_cars_pct"]),
                    fmt_int(row["national_phev"]),
                    fmt_pct(row["phev_share_of_national_passenger_cars_pct"]),
                    fmt_int(row["combined_plugin_stock"]),
                    fmt_pct(row["combined_plugin_share_of_national_passenger_cars_pct"]),
                    fmt_int(row["bev_change_from_previous_snapshot"]),
                    fmt_pct(row["bev_pct_change_from_previous_snapshot"]),
                    fmt_int(row["phev_change_from_previous_snapshot"]),
                    fmt_pct(row["phev_pct_change_from_previous_snapshot"]),
                ]
                for row in national_trends
            ],
        )
    )
    lines.extend(["", "### Period changes", ""])
    period_rows = []
    for label, values in summary["growth"].items():
        period_rows.append(
            [
                label.replace("_", " "),
                fmt_int(values["bev_change"]),
                fmt_pct(values["bev_pct_change"]),
                fmt_int(values["phev_change"]),
                fmt_pct(values["phev_pct_change"]),
                fmt_num(values["bev_to_phev_relative_growth_ratio"], 2),
            ]
        )
    lines.extend(markdown_table(["Period", "BEV absolute", "BEV %", "PHEV absolute", "PHEV %", "BEV/PHEV relative-growth ratio"], period_rows))
    lines.extend(
        [
            "",
            "National BEV stock grew faster than PHEV stock in all three periods. The combined plug-in share is calculated as BEV plus PHEV because those published categories are mutually exclusive passenger-car powertrain categories. `Hybrid insgesamt` is not added to that measure because it already contains PHEV.",
            "",
            "## Analysis B — Federal-state comparison",
            "",
            "The complete state/residual metric table is in [`batch15_kba_state_metrics.csv`](batch15_kba_state_metrics.csv). The following July 2026 rankings intentionally separate stock size, penetration, absolute change and percentage growth.",
            "",
        ]
    )
    rankings = summary["latest_state_rankings"]
    lines.extend(["### Largest July BEV stocks", ""])
    lines.extend(markdown_table(["Rank", "State", "BEV", "Passenger cars", "BEV penetration"], [[i, row["geography"], fmt_int(row["bev_stock"]), fmt_int(row["passenger_car_stock"]), fmt_pct(row["bev_penetration_pct"])] for i, row in enumerate(rankings["largest_bev_stock"], 1)]))
    lines.extend(["", "### Highest July BEV penetration", ""])
    lines.extend(markdown_table(["Rank", "State", "BEV", "Passenger cars", "BEV penetration"], [[i, row["geography"], fmt_int(row["bev_stock"]), fmt_int(row["passenger_car_stock"]), fmt_pct(row["bev_penetration_pct"])] for i, row in enumerate(rankings["highest_bev_penetration"], 1)]))
    lines.extend(["", "### Largest January–July absolute BEV increases", ""])
    lines.extend(markdown_table(["Rank", "State", "BEV increase", "BEV growth", "Contribution to national growth"], [[i, row["geography"], fmt_int(row["bev_change_jan_to_date"]), fmt_pct(row["bev_growth_pct_jan_to_date"]), fmt_pct(row["contribution_to_national_bev_growth_pct"])] for i, row in enumerate(rankings["largest_bev_growth"], 1)]))
    lines.extend(["", "### Highest January–July BEV percentage growth", ""])
    lines.extend(markdown_table(["Rank", "State", "BEV increase", "BEV growth", "July BEV"], [[i, row["geography"], fmt_int(row["bev_change_jan_to_date"]), fmt_pct(row["bev_growth_pct_jan_to_date"]), fmt_int(row["bev_stock"])] for i, row in enumerate(rankings["highest_bev_growth_pct"], 1)]))
    lines.extend(
        [
            "",
            "`Sonstige` is reported separately in the CSV and is not blended into any Bundesland. State-level totals are sourced from FZ 27.2 and reconcile to the 400-region table for the 16 named states. The ranking differences are substantive: large states tend to lead absolute stock and change, while smaller states can lead penetration or percentage growth.",
            "",
            "## Analysis C — 400 KBA registration regions",
            "",
            "The full one-row-per-KBA-code metrics are in [`batch15_kba_district_metrics.csv`](batch15_kba_district_metrics.csv).",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Check", "Result"],
            [
                ["Rows", fmt_int(district_checks["rows"])],
                ["Codes per snapshot", ", ".join(f"{date}: {value}" for date, value in district_checks["codes_per_snapshot"].items())],
                ["Identity changes", fmt_int(len(district_checks["identity_changes"]))],
                ["Numeric NULLs", fmt_int(district_checks["numeric_nulls"])],
                ["Zero denominators", fmt_int(district_checks["zero_denominators"])],
                ["Percentage-growth eligible", fmt_int(district_checks["pct_growth_eligible_count"])],
                ["Percentage-growth excluded", fmt_int(district_checks["pct_growth_excluded_count"])],
                ["Trier shared region", f"{district_checks['trier_row']['district_code']} {district_checks['trier_row']['district_name']} — one KBA row; no allocation"],
            ],
        )
    )
    lines.extend(["", "### Regional growth distributions", ""])
    distributions = summary["district_distributions"]
    lines.extend(
        markdown_table(
            ["Metric", "N", "Min", "P10", "Median", "Mean", "P90", "Max", "Std. dev."],
            [
                [
                    "BEV growth Jan–Jul (%)",
                    fmt_int(values["count"]),
                    fmt_num(values["min"]),
                    fmt_num(values["p10"]),
                    fmt_num(values["median"]),
                    fmt_num(values["mean"]),
                    fmt_num(values["p90"]),
                    fmt_num(values["max"]),
                    fmt_num(values["stddev"]),
                ]
                for values in [distributions["bev_growth_pct_jan_to_jul"]]
            ]
            + [
                [
                    "PHEV growth Jan–Jul (%)",
                    fmt_int(values["count"]),
                    fmt_num(values["min"]),
                    fmt_num(values["p10"]),
                    fmt_num(values["median"]),
                    fmt_num(values["mean"]),
                    fmt_num(values["p90"]),
                    fmt_num(values["max"]),
                    fmt_num(values["stddev"]),
                ]
                for values in [distributions["phev_growth_pct_jan_to_jul"]]
            ]
            + [
                [
                    "BEV penetration July (%)",
                    fmt_int(values["count"]),
                    fmt_num(values["min"]),
                    fmt_num(values["p10"]),
                    fmt_num(values["median"]),
                    fmt_num(values["mean"]),
                    fmt_num(values["p90"]),
                    fmt_num(values["max"]),
                    fmt_num(values["stddev"]),
                ]
                for values in [distributions["bev_penetration_pct_july"]]
            ]
            + [
                [
                    "PHEV penetration July (%)",
                    fmt_int(values["count"]),
                    fmt_num(values["min"]),
                    fmt_num(values["p10"]),
                    fmt_num(values["median"]),
                    fmt_num(values["mean"]),
                    fmt_num(values["p90"]),
                    fmt_num(values["max"]),
                    fmt_num(values["stddev"]),
                ]
                for values in [distributions["phev_penetration_pct_july"]]
            ]
            + [
                [
                    "Combined plug-in penetration July (%)",
                    fmt_int(values["count"]),
                    fmt_num(values["min"]),
                    fmt_num(values["p10"]),
                    fmt_num(values["median"]),
                    fmt_num(values["mean"]),
                    fmt_num(values["p90"]),
                    fmt_num(values["max"]),
                    fmt_num(values["stddev"]),
                ]
                for values in [distributions["combined_plugin_penetration_pct_july"]]
            ],
        )
    )
    weighted = summary["weighted_unweighted_growth"]
    lines.extend(
        [
            "",
            "The 400-region weighted BEV growth is " + fmt_pct(weighted["bev_weighted_pct"]) + " versus an unweighted mean of region-level growth rates of " + fmt_pct(weighted["bev_unweighted_mean_pct"]) + ". For PHEVs the corresponding values are " + fmt_pct(weighted["phev_weighted_pct"]) + " and " + fmt_pct(weighted["phev_unweighted_mean_pct"]) + ". The weighted result answers how the covered stock changed in aggregate; the unweighted mean gives each region equal influence and is more sensitive to small starting stocks.",
            "",
            "### Largest absolute July stock and January–July change",
            "",
        ]
    )
    largest_bev_stock = top_rows(district_metrics, "bev_stock_2026_07_01", 10)
    largest_phev_stock = top_rows(district_metrics, "phev_stock_2026_07_01", 10)
    largest_bev_change = top_rows(district_metrics, "bev_change_jan_to_jul", 10)
    largest_phev_change = top_rows(district_metrics, "phev_change_jan_to_jul", 10)
    lines.extend(["**BEV stock:**", ""])
    lines.extend(markdown_table(["Rank", "Code", "Region", "State", "July BEV", "July penetration"], [[i, row["district_code"], row["district_name"], row["state_name"], fmt_int(row["bev_stock_2026_07_01"]), fmt_pct(row["bev_penetration_pct_2026_07_01"])] for i, row in enumerate(largest_bev_stock, 1)]))
    lines.extend(["", "**PHEV stock:**", ""])
    lines.extend(markdown_table(["Rank", "Code", "Region", "State", "July PHEV", "July penetration"], [[i, row["district_code"], row["district_name"], row["state_name"], fmt_int(row["phev_stock_2026_07_01"]), fmt_pct(row["phev_penetration_pct_2026_07_01"])] for i, row in enumerate(largest_phev_stock, 1)]))
    lines.extend(["", "**BEV absolute increase:**", ""])
    lines.extend(markdown_table(["Rank", "Code", "Region", "BEV increase", "BEV growth"], [[i, row["district_code"], row["district_name"], fmt_int(row["bev_change_jan_to_jul"]), fmt_pct(row["bev_growth_pct_jan_to_jul"])] for i, row in enumerate(largest_bev_change, 1)]))
    lines.extend(["", "**PHEV absolute increase:**", ""])
    lines.extend(markdown_table(["Rank", "Code", "Region", "PHEV increase", "PHEV growth"], [[i, row["district_code"], row["district_name"], fmt_int(row["phev_change_jan_to_jul"]), fmt_pct(row["phev_growth_pct_jan_to_jul"])] for i, row in enumerate(largest_phev_change, 1)]))
    lines.extend(["", "### Percentage-growth and penetration extremes", ""])
    pct_growth_rows = top_rows(district_metrics, "bev_growth_pct_jan_to_jul", 10, eligible_field="bev_growth_pct_ranking_eligible")
    penetration_rows = top_rows(district_metrics, "bev_penetration_pct_2026_07_01", 10)
    lines.extend(["**Highest BEV growth among regions with January BEV stock ≥ 1,000:**", ""])
    lines.extend(markdown_table(["Rank", "Code", "Region", "Jan BEV", "Jul BEV", "Growth"], [[i, row["district_code"], row["district_name"], fmt_int(row["bev_stock_2026_01_01"]), fmt_int(row["bev_stock_2026_07_01"]), fmt_pct(row["bev_growth_pct_jan_to_jul"])] for i, row in enumerate(pct_growth_rows, 1)]))
    lines.extend(["", "**Highest July BEV penetration:**", ""])
    lines.extend(markdown_table(["Rank", "Code", "Region", "BEV", "Passenger cars", "Penetration"], [[i, row["district_code"], row["district_name"], fmt_int(row["bev_stock_2026_07_01"]), fmt_int(row["passenger_car_stock_2026_07_01"]), fmt_pct(row["bev_penetration_pct_2026_07_01"])] for i, row in enumerate(penetration_rows, 1)]))
    lines.extend(
        [
            "",
            "Regions below the 1,000-vehicle baseline remain in the CSV with `bev_growth_pct_ranking_eligible=false`; they are not treated as automatically important because small denominators can create large percentages. All 400 regions have valid passenger-car denominators for penetration metrics.",
            "",
            "## Analysis D — Ownership structure",
            "",
            "FZ 27.5 supports commercial/private ownership crossed with BEV, PHEV and passenger-car totals at 16-state, `Sonstige` and national grain. It does not support district-level ownership. The complete table is in [`batch15_kba_ownership_metrics.csv`](batch15_kba_ownership_metrics.csv).",
            "",
        ]
    )
    owner = summary["ownership_national_july"]
    lines.extend(
        markdown_table(
            ["July 2026 national measure", "BEV", "PHEV"],
            [
                ["Published total", fmt_int(owner["published_total_bev"]), fmt_int(owner["published_total_phev"])],
                ["Commercial", fmt_int(owner["commercial_bev"]), fmt_int(owner["commercial_phev"])],
                ["Private", fmt_int(owner["private_bev"]), fmt_int(owner["private_phev"])],
                ["Unallocated/unknown residual", fmt_int(owner["unallocated_or_unknown_bev"]), fmt_int(owner["unallocated_or_unknown_phev"])],
                ["Commercial share of observed owner rows", fmt_pct(owner["commercial_bev_share_of_observed_pct"]), fmt_pct(owner["commercial_phev_share_of_observed_pct"])],
                ["Private share of observed owner rows", fmt_pct(owner["private_bev_share_of_observed_pct"]), fmt_pct(owner["private_phev_share_of_observed_pct"])],
                ["Observed owner-row coverage of published total", fmt_pct(owner["owner_observed_bev_coverage_pct"]), fmt_pct(owner["owner_observed_phev_coverage_pct"])],
            ],
        )
    )
    national_owner_rows = [row for row in ownership_metrics if row["geography"] == NATIONAL_GEOGRAPHY]
    jan_owner = next(row for row in national_owner_rows if row["reference_date"] == DATES[0])
    jul_owner = next(row for row in national_owner_rows if row["reference_date"] == DATES[-1])
    lines.extend(
        [
            "",
            f"At the national grain, the private share of observed-owner BEV stock changed from {fmt_pct(jan_owner['private_bev_share_of_observed_pct'])} to {fmt_pct(jul_owner['private_bev_share_of_observed_pct'])} between January and July ({fmt_num(float(jul_owner['private_bev_share_of_observed_pct']) - float(jan_owner['private_bev_share_of_observed_pct']))} percentage points). The corresponding PHEV share changed from {fmt_pct(jan_owner['private_phev_share_of_observed_pct'])} to {fmt_pct(jul_owner['private_phev_share_of_observed_pct'])} ({fmt_num(float(jul_owner['private_phev_share_of_observed_pct']) - float(jan_owner['private_phev_share_of_observed_pct']))} percentage points). These are composition changes in published owner rows, not changes in individual ownership behavior.",
            "",
            f"The source contains {fmt_int(ownership_checks['owner_rows'])} owner rows and {fmt_int(ownership_checks['published_total_rows'])} published total rows across the three snapshots. The publisher states that `zusammen` and `Deutschland insgesamt` include vehicles with missing or implausible holder-group data; those residuals are preserved rather than allocated to private or commercial ownership.",
            "",
            "FZ 27.16 and FZ 27.17 also publish commercial/private BEV/PHEV fields at postcode and municipality grains. Their different geography, missing-cell patterns and municipality-key limitations are documented below; no district ownership is inferred from them.",
            "",
            "## Analysis E — Postcode and municipality capabilities",
            "",
            "The current normalized tables support descriptive inspection, but not a new geographic Crosswalk or BBSR join.",
            "",
        ]
    )
    geography_rows = []
    for row in geography["postcode"]:
        geography_rows.append(["FZ 27.16 postcode", row["reference_date"], fmt_int(row["row_count"]), fmt_int(row["distinct_postal_codes"]), fmt_int(row["duplicate_rows"]), fmt_int(row["rows_with_nulls"]), fmt_int(row["null_measure_cells"]), geography["postcode_interpretation"]])
    for row in geography["municipality"]:
        geography_rows.append(["FZ 27.17 municipality", row["reference_date"], fmt_int(row["row_count"]), fmt_int(row["district_codes"]), fmt_int(row["possible_total_rows"]), fmt_int(row["rows_with_nulls"]), fmt_int(row["null_measure_cells"]), geography["municipality_interpretation"]])
    lines.extend(markdown_table(["Source/grain", "Date", "Rows", "Distinct units/codes", "Duplicate/total-row check", "Rows with NULLs", "NULL measure cells", "Interpretation"], geography_rows))
    lines.extend(
        [
            "",
            f"Postcode rows are unique by `(reference_date, postal_code)` and have no district or state identifiers in the normalized table. The July release has one more postcode row than January/April, and missing source cells are retained as NULL. Municipality rows are unique by `(reference_date, district_code, municipality_name)`, cover all 400 KBA district codes, and contain {fmt_int(geography['municipality_names_repeated_across_districts'])} municipality names that occur in more than one district; names therefore cannot be treated as national unique IDs. Neither table is used to force a regional reconciliation with FZ 27.15.",
            "",
            "## Analysis F — Historical quarterly series",
            "",
            f"`analytics.kba_national_quarterly_stock` contains {fmt_int(history['row_count'])} deduplicated national stock observations from {history['earliest_stock_date']} through {history['latest_stock_date']}. The releases overlap in historical dates; the deterministic rule is: one row per stock date, prefer the latest report snapshot, then the earliest source row. No historical national observation is treated as a regional observation.",
            "",
        ]
    )
    lines.extend(markdown_table(["Stock date", "Report snapshot", "Passenger cars", "BEV", "PHEV", "BEV share", "PHEV share"], [[row["stock_date"], row["report_snapshot"], fmt_int(row["passenger_cars_total"]), fmt_int(row["passenger_bev"]), fmt_int(row["passenger_phev"]), fmt_pct(pct(row["passenger_bev"], row["passenger_cars_total"])), fmt_pct(pct(row["passenger_phev"], row["passenger_cars_total"]))] for row in history["selected_rows"]]))
    lines.extend(
        [
            "",
            "The historical series supports national BEV/PHEV trajectory description and provides a consistency check for the three current snapshots. It does not support district ownership, district history, sales-flow inference, or an older regional comparison without compatible source tables.",
            "",
            "## Analysis G — Statistical findings",
            "",
        ]
    )
    concentration_data = summary["district_concentration"]
    lines.extend(
        [
            f"**OBSERVED:** The largest 10 of 400 KBA regions account for {fmt_pct(concentration_data['bev_stock_july'][10])} of July 2026 covered-region BEV stock and {fmt_pct(concentration_data['phev_stock_july'][10])} of covered-region PHEV stock. The largest absolute-stock regions are not necessarily the regions with the highest penetration or percentage growth.",
            "",
            f"**OBSERVED:** July district BEV penetration has a median of {fmt_pct(distributions['bev_penetration_pct_july']['median'])}, while the PHEV penetration median is {fmt_pct(distributions['phev_penetration_pct_july']['median'])}. The P10/P90 ranges show substantial regional variation without requiring a causal explanation.",
            "",
            f"**SUPPORTED ASSOCIATION:** Across the 400 regions, January–July BEV and PHEV percentage growth have a descriptive Pearson correlation of {fmt_num(summary['district_growth_correlation_bev_phev'], 3)}. This summarizes co-movement in the observed stock changes; it does not show that one powertrain caused the other or that infrastructure explains either change.",
            "",
            "**PLAUSIBLE HYPOTHESIS:** Differences may reflect regional vehicle mix, registration composition, fleet turnover, reporting coverage and other unmeasured factors. The current source can describe the patterns but cannot identify their causes.",
            "",
            "**NOT TESTABLE WITH CURRENT DATA:** The analysis cannot test charging demand, charger utilization, traffic corridors, population, area, income, grid constraints, vehicle sales flows, migration, or causal infrastructure effects. It also cannot equate a KBA registration region with a BBSR Kreis or allocate the shared Trier region.",
            "",
            "## KPI evaluation",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Candidate", "Status", "Definition and denominator", "Grain/date", "Main limitation"],
            [
                ["National BEV stock", "VALIDATED", "Published FZ 27.2 `Deutschland / Elektro (BEV)`", "National × snapshot", "Registered stock, not sales"],
                ["National PHEV stock", "VALIDATED", "Published FZ 27.2 `Deutschland / darunter Plug-in`", "National × snapshot", "Nested under Hybrid insgesamt for total-category logic"],
                ["BEV/PHEV stock growth", "VALIDATED", "End stock minus start stock; change divided by start stock", "National/state/KBA region × snapshots", "Descriptive stock change, not flow"],
                ["BEV/PHEV passenger-car penetration", "VALIDATED", "Powertrain stock divided by same-grain passenger-car total", "State or 400 KBA region × snapshot", "Coverage differs between national and 400-region scopes"],
                ["Combined plug-in penetration", "VALIDATED", "BEV + PHEV divided by passenger cars", "Same-grain snapshot", "Only valid because BEV/PHEV are mutually exclusive here"],
                ["State stock/penetration/change table", "VALIDATED", "FZ 27.2 mutually exclusive denominator rows", "16 states + separate Sonstige × snapshot", "Absolute and percentage rankings answer different questions"],
                ["KBA-region stock/penetration/change table", "VALIDATED", "FZ 27.15 district rows and passenger-car denominator", "400 KBA codes × snapshot", "No BBSR equivalence; Trier remains one shared code"],
                ["KBA-region percentage-growth ranking", "EXPLORATORY", "January–July growth with ≥1,000 January BEVs", "400 KBA codes", "Threshold is exploratory; small-baseline regions excluded from ranking only"],
                ["FZ 27.5 ownership composition", "EXPLORATORY", "Commercial/private shares of observed owner rows plus published-total coverage", "State/residual/national × snapshot", "Publisher totals include unknown/implausible holder groups"],
                ["Postcode/municipality descriptive aggregates", "EXPLORATORY", "Source-grain rows with NULL-cell and key checks", "Postcode or district+municipality × snapshot", "No district/state crosswalk for postcodes; no municipality code"],
                ["BBSR-based vehicle-stock ratio", "UNSUPPORTED", "No approved dated KBA-to-BBSR bridge", "Not deployed", "Do not create or infer in Batch 15"],
            ],
        )
    )
    lines.extend(
        [
            "",
            "Recommended portfolio KPI set: national/state/KBA-region BEV and PHEV stock, same-grain penetration, combined plug-in penetration, absolute stock changes, and clearly labelled exploratory percentage-growth distributions. Keep ownership mix and postcode/municipality outputs as descriptive supporting analysis. Do not deploy new DuckDB KPI objects in this batch.",
            "",
            "## Reproducible outputs",
            "",
            "- [`scripts/15_analyze_kba_ev_stock.py`](../scripts/15_analyze_kba_ev_stock.py)",
            "- [`batch15_kba_national_trends.csv`](batch15_kba_national_trends.csv)",
            "- [`batch15_kba_state_metrics.csv`](batch15_kba_state_metrics.csv)",
            "- [`batch15_kba_district_metrics.csv`](batch15_kba_district_metrics.csv)",
            "- [`batch15_kba_ownership_metrics.csv`](batch15_kba_ownership_metrics.csv)",
            "- [`batch15_kba_worksheet_capabilities.csv`](batch15_kba_worksheet_capabilities.csv)",
            "",
            "Run from the repository root:",
            "",
            "```bash",
            ".venv/bin/python scripts/15_analyze_kba_ev_stock.py --json",
            "```",
            "",
            "## Validation results",
            "",
        ]
    )
    validation_rows = [
        ["Source workbook fingerprints", "PASS — all three expected SHA-256 values match"],
        ["Worksheet inventory", "PASS — 20 worksheets × 3 releases; 60 inventory rows"],
        ["National BEV/PHEV/passenger-car reconciliation", "PASS — 16 states + Sonstige = Deutschland; 16 states = 400-region table"],
        ["KBA region coverage", "PASS — 400 codes per snapshot, 1,200 source rows"],
        ["District identity consistency", "PASS — no code/name/state identity changes"],
        ["District numeric nulls/zero denominators", "PASS — none"],
        ["PHEV category-overlap handling", "PASS — PHEV not added to Hybrid insgesamt"],
        ["Ownership grain", "PASS — 18 geographies × 2 owner groups plus published totals per snapshot"],
        ["Historical series", "PASS — current 2026 observations reconcile to national FZ 27.2 values"],
        ["DuckDB/source mutation", "PASS — read-only connection; no source/reference writes"],
    ]
    lines.extend(markdown_table(["Check", "Result"], validation_rows))
    lines.extend(
        [
            "",
            "### Source fingerprints",
            "",
        ]
    )
    lines.extend(markdown_table(["Path", "Bytes", "SHA-256", "Result"], [[row["path"], fmt_int(row["bytes"]), row["actual_sha256"], "MATCH" if row["match"] else "MISMATCH"] for row in fingerprints]))
    lines.extend(
        [
            "",
            "## Limitations and next analytical step",
            "",
            "The KBA tables are published stock aggregates with alternative worksheet grains. The FZ 27.15 region is a KBA registration region, not automatically a Kreis; the 400-region passenger-car denominator excludes the national `Sonstige` residual. FZ 27.16/27.17 ownership fields contain missing numeric cells after parsing source dots, and municipality names are not global IDs. No BBSR integration, Trier allocation, charging-demand interpretation, or causal analysis was performed.",
            "",
            "The next approved analytical step should be review of the Batch 15 findings and denominator choices, followed by an owner-approved decision on whether a dated, product-specific KBA compatibility bridge is warranted. Batch 16 and Tableau work remain outside this batch.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the read-only Batch 15 KBA FZ 27 analysis")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--json", action="store_true", help="Print a compact JSON completion summary")
    args = parser.parse_args()

    database = resolve_path(args.database)
    report_path = resolve_path(args.report)
    output_dir = resolve_path(args.output_dir)
    require(database.is_file(), f"Missing DuckDB database: {database}")

    fingerprints = fingerprint_sources()
    conn = duckdb.connect(str(database), read_only=True)
    try:
        database_contract = validate_database_contract(conn)
        inventory = collect_worksheet_inventory(conn)
        state_fuel = load_state_fuel(conn)
        reconciliation, _ = national_reconciliation(conn, state_fuel)
        national_trends = build_national_trends(reconciliation)
        state_metrics = build_state_metrics(state_fuel)
        district_metrics, district_checks = build_district_metrics(conn, reconciliation)
        ownership_metrics, ownership_checks = build_ownership_metrics(conn)
        geography = inspect_postcode_municipality(conn)
        _, history = load_history(conn)
    finally:
        conn.close()

    summary = build_analysis_summary(national_trends, state_metrics, district_metrics, ownership_metrics, geography)

    national_fields = [
        "reference_date", "national_passenger_cars", "sixteen_state_passenger_cars", "sonstige_passenger_cars", "four_hundred_region_passenger_cars", "national_bev", "sixteen_state_bev", "sonstige_bev", "four_hundred_region_bev", "national_phev", "sixteen_state_phev", "sonstige_phev", "four_hundred_region_phev", "national_minus_four_hundred_region_passenger_cars", "national_minus_four_hundred_region_bev", "national_minus_four_hundred_region_phev", "bev_share_of_national_passenger_cars_pct", "phev_share_of_national_passenger_cars_pct", "combined_plugin_stock", "combined_plugin_share_of_national_passenger_cars_pct", "bev_change_from_previous_snapshot", "bev_pct_change_from_previous_snapshot", "phev_change_from_previous_snapshot", "phev_pct_change_from_previous_snapshot", "reconciliation_status"
    ]
    state_fields = [
        "reference_date", "geography", "geographic_scope", "passenger_car_stock", "bev_stock", "phev_stock", "combined_plugin_stock", "bev_penetration_pct", "phev_penetration_pct", "combined_plugin_penetration_pct", "bev_change_jan_to_date", "bev_growth_pct_jan_to_date", "phev_change_jan_to_date", "phev_growth_pct_jan_to_date", "contribution_to_national_bev_growth_pct", "denominator_definition"
    ]
    district_fields = [
        "district_code", "district_name", "state_name", "baseline_bev_threshold_for_pct_ranking", "bev_growth_pct_ranking_eligible", "bev_growth_pct_exclusion_reason", "bev_change_jan_to_jul", "bev_growth_pct_jan_to_jul", "phev_change_jan_to_jul", "phev_growth_pct_jan_to_jul"
    ]
    for date in DATES:
        suffix = date.replace("-", "_")
        district_fields.extend(
            [
                f"passenger_car_stock_{suffix}", f"bev_stock_{suffix}", f"phev_stock_{suffix}", f"combined_plugin_stock_{suffix}", f"bev_penetration_pct_{suffix}", f"phev_penetration_pct_{suffix}", f"combined_plugin_penetration_pct_{suffix}", f"bev_share_of_national_stock_pct_{suffix}", f"phev_share_of_national_stock_pct_{suffix}", f"bev_share_of_400_region_stock_pct_{suffix}", f"phev_share_of_400_region_stock_pct_{suffix}",
            ]
        )
    ownership_fields = [
        "reference_date", "geography", "geographic_scope", "published_total_passenger_cars", "published_total_bev", "commercial_bev", "private_bev", "unallocated_or_unknown_bev", "owner_observed_bev", "commercial_bev_share_of_observed_pct", "private_bev_share_of_observed_pct", "commercial_bev_share_of_published_total_pct", "private_bev_share_of_published_total_pct", "owner_observed_bev_coverage_pct", "published_total_phev", "commercial_phev", "private_phev", "unallocated_or_unknown_phev", "owner_observed_phev", "commercial_phev_share_of_observed_pct", "private_phev_share_of_observed_pct", "commercial_phev_share_of_published_total_pct", "private_phev_share_of_published_total_pct", "owner_observed_phev_coverage_pct", "publisher_note"
    ]
    inventory_fields = [
        "source_id", "reference_date", "sheet_name", "published_title", "raw_nonempty_rows", "first_excel_row", "last_excel_row", "analytical_grain", "geographic_level", "vehicle_categories", "owner_groups", "coverage_limitations", "row_role", "aggregation_suitability", "source_columns"
    ]

    write_csv(output_dir / "batch15_kba_national_trends.csv", national_fields, national_trends)
    write_csv(output_dir / "batch15_kba_state_metrics.csv", state_fields, state_metrics)
    write_csv(output_dir / "batch15_kba_district_metrics.csv", district_fields, district_metrics)
    write_csv(output_dir / "batch15_kba_ownership_metrics.csv", ownership_fields, ownership_metrics)
    write_csv(output_dir / "batch15_kba_worksheet_capabilities.csv", inventory_fields, inventory)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_report(
            inventory,
            fingerprints,
            database_contract,
            reconciliation,
            national_trends,
            state_metrics,
            district_metrics,
            district_checks,
            ownership_metrics,
            ownership_checks,
            geography,
            history,
            summary,
        ),
        encoding="utf-8",
    )

    output_summary = {
        "status": "PASS",
        "database": str(database.relative_to(ROOT) if database.is_relative_to(ROOT) else database),
        "report": str(report_path.relative_to(ROOT) if report_path.is_relative_to(ROOT) else report_path),
        "outputs": [
            "reports/batch15_kba_national_trends.csv",
            "reports/batch15_kba_state_metrics.csv",
            "reports/batch15_kba_district_metrics.csv",
            "reports/batch15_kba_ownership_metrics.csv",
            "reports/batch15_kba_worksheet_capabilities.csv",
        ],
        "district_rows": len(district_metrics),
        "district_pct_growth_eligible": district_checks["pct_growth_eligible_count"],
        "district_pct_growth_excluded": district_checks["pct_growth_excluded_count"],
        "history_rows": history["row_count"],
        "ownership_rows": len(ownership_metrics),
        "source_fingerprints_match": all(bool(row["match"]) for row in fingerprints),
    }
    if args.json:
        print(json.dumps(output_summary, ensure_ascii=False, indent=2))
    else:
        print("Batch 15 analysis PASS")
        print(f"Report: {output_summary['report']}")
        print(f"District rows: {output_summary['district_rows']}")
        print(f"History rows: {output_summary['history_rows']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AnalysisError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
