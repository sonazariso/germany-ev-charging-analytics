#!/usr/bin/env python3
"""Batch 21: prepare the approved two-page Tableau executive overview.

The script reads the nine validated Batch 19 exports and inspects the existing
DuckDB database read-only for the published equipment-status breakdown.  It
creates only two small presentation-shaped CSVs:

* ``power_band_distribution_2026_09_30.csv`` with four mutually exclusive
  charging-power bands; and
* ``equipment_status_breakdown_2026_09_30.csv`` with the two published
  equipment-status categories.

It also writes a deterministic validation report.  The nine Batch 19 exports,
DuckDB file, raw workbooks, reference files and crosswalk are never written.

Run from the repository root::

    .venv/bin/python scripts/21_prepare_tableau_overview.py

No execution timestamp is written, so repeated runs can be compared by hash.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_EXPORT_DIR = ROOT / "data/exports/tableau"
DEFAULT_PREPARATION_DIR = DEFAULT_EXPORT_DIR / "preparation"
DEFAULT_REPORT = ROOT / "reports/batch21_tableau_overview_validation.md"
EXPECTED_EXPORT_VERSION = "batch19-tableau-exports-2026-11-03-v1"
INFRASTRUCTURE_DATE = "2026-09-30"
KBA_PRIMARY_DATE = "2026-07-01"
NATIONAL_HISTORY_FILE = "kba_national_stock_history.csv"
STATE_CHARGING_FILE = "state_charging_2026_09_30.csv"
STATE_COMPARISON_FILE = "state_ev_charging_comparison_2026.csv"
NATIONAL_CHARGING_FILE = "national_charging_2026_09_30.csv"
KBA_STATE_FILE = "kba_state_ev_stock_2026.csv"

EXPECTED_INFRASTRUCTURE = {
    "equipment_count": 117_662,
    "charging_point_count": 211_253,
    "normal_charging_point_count": 156_155,
    "fast_charging_point_count": 55_098,
    "points_ge_150_kw": 40_950,
    "points_ge_350_kw": 6_950,
    "equipment_nominal_power_mw": 9_215.4173,
}
EXPECTED_KBA = {
    "national_bev": 2_365_047,
    "national_phev": 1_226_863,
    "sixteen_state_bev": 2_362_218,
    "sixteen_state_phev": 1_225_241,
}
EXPECTED_STATUS = {
    "In Betrieb": 117_642,
    "In Wartung": 20,
}
FEDERAL_STATES = {
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
}


class ValidationError(RuntimeError):
    """Raised when an approved input contract is not satisfied."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def format_decimal(value: float) -> str:
    text = f"{value:.10f}".rstrip("0").rstrip(".")
    return text if text else "0"


def format_pct(numerator: int, denominator: int) -> str:
    require(denominator > 0, "Percentage denominator must be positive")
    return format_decimal(numerator / denominator * 100.0)


def int_value(row: Mapping[str, str], field: str) -> int:
    try:
        return int(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError(f"Expected integer field {field!r}: {row!r}") from exc


def float_value(row: Mapping[str, str], field: str) -> float:
    try:
        return float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError(f"Expected numeric field {field!r}: {row!r}") from exc


def check_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    require(
        math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance),
        f"{label}: expected {expected}, observed {actual}",
    )


def unique(rows: Iterable[Mapping[str, str]], fields: Sequence[str], label: str) -> None:
    keys = [tuple(row.get(field, "") for field in fields) for row in rows]
    require(all(all(value != "" for value in key) for key in keys), f"{label}: null/blank key")
    require(len(keys) == len(set(keys)), f"{label}: duplicate key")


def write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row[field] for field in fieldnames} for row in rows)


def load_and_validate_manifest(export_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Tuple[List[str], List[Dict[str, str]]]]]:
    manifest_path = export_dir / "export_manifest.json"
    require(manifest_path.is_file(), f"Missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("export_version") == EXPECTED_EXPORT_VERSION, "Unexpected Batch 19 export version")
    require(manifest.get("database_access") == "read_only", "Manifest is not marked read_only")

    loaded: Dict[str, Tuple[List[str], List[Dict[str, str]]]] = {}
    for item in manifest.get("exports", []):
        filename = item["filename"]
        path = export_dir / filename
        require(path.is_file(), f"Missing manifest export: {path}")
        observed_hash = sha256(path)
        require(observed_hash == item["sha256"], f"Batch 19 export checksum mismatch: {filename}")
        fieldnames, rows = read_csv(path)
        require(len(rows) == item["row_count"], f"Batch 19 row-count mismatch: {filename}")
        require(len(fieldnames) == item["column_count"], f"Batch 19 column-count mismatch: {filename}")
        loaded[filename] = (fieldnames, rows)

    require(len(loaded) == 9, f"Expected nine Batch 19 exports, observed {len(loaded)}")
    for item in manifest.get("source_dataset_versions", []):
        path = ROOT / item["path"]
        require(path.is_file(), f"Missing fingerprinted source/reference: {path}")
        require(sha256(path) == item["sha256"], f"Source/reference checksum mismatch: {item['path']}")
    return manifest, loaded


def validate_national(
    rows: Sequence[Mapping[str, str]], history: Sequence[Mapping[str, str]]
) -> Dict[str, Any]:
    require(len(rows) == 1, "National charging export must contain exactly one row")
    row = rows[0]
    require(row["geography_name"] == "Germany", "National geography must be Germany")
    require(row["bnetza_reference_date"] == INFRASTRUCTURE_DATE, "Unexpected BNetzA date")
    for field, expected in EXPECTED_INFRASTRUCTURE.items():
        actual = float_value(row, field) if isinstance(expected, float) else int_value(row, field)
        check_close(actual, expected, f"national {field}")

    require(len(history) == 33, "National KBA history must contain 33 actual observations")
    unique(history, ["stock_date"], "National KBA history")
    history_dates = [row["stock_date"] for row in history]
    require(history_dates == sorted(history_dates), "National history must be ordered by stock_date")
    july = next((row for row in history if row["stock_date"] == KBA_PRIMARY_DATE), None)
    require(july is not None, "National history is missing 2026-07-01")
    require(int_value(july, "bev_passenger_car_stock") == EXPECTED_KBA["national_bev"], "National July BEV mismatch")
    require(int_value(july, "phev_passenger_car_stock") == EXPECTED_KBA["national_phev"], "National July PHEV mismatch")
    return {
        "equipment_count": int_value(row, "equipment_count"),
        "charging_point_count": int_value(row, "charging_point_count"),
        "history_rows": len(history),
        "history_first_date": history_dates[0],
        "history_last_date": history_dates[-1],
        "national_july_bev": int_value(july, "bev_passenger_car_stock"),
        "national_july_phev": int_value(july, "phev_passenger_car_stock"),
    }


def validate_states(
    charging_rows: Sequence[Mapping[str, str]],
    comparison_rows: Sequence[Mapping[str, str]],
    state_stock_rows: Sequence[Mapping[str, str]],
    national_row: Mapping[str, str],
) -> Dict[str, Any]:
    require(len(charging_rows) == 16, "State charging export must contain exactly 16 states")
    require(len(comparison_rows) == 16, "State comparison export must contain exactly 16 states")
    unique(charging_rows, ["state_name"], "State charging")
    unique(comparison_rows, ["state_name"], "State comparison")
    charging_names = {row["state_name"] for row in charging_rows}
    comparison_names = {row["state_name"] for row in comparison_rows}
    require(charging_names == FEDERAL_STATES, "State charging names do not equal the approved 16-state scope")
    require(comparison_names == FEDERAL_STATES, "State comparison names do not equal the approved 16-state scope")
    require(len(state_stock_rows) == 48, "State KBA export must contain 48 state/date rows")
    unique(state_stock_rows, ["state_name", "kba_reference_date"], "State KBA stock")
    require(
        {row["state_name"] for row in state_stock_rows} == FEDERAL_STATES,
        "State KBA stock names do not equal the approved 16-state scope",
    )
    require(
        {row["kba_reference_date"] for row in state_stock_rows}
        == {"2026-01-01", "2026-04-01", KBA_PRIMARY_DATE},
        "State KBA stock dates are not the approved three dates",
    )

    sums = {
        field: sum(int_value(row, field) for row in charging_rows)
        for field in (
            "equipment_count",
            "declared_charging_point_count",
            "charging_point_count",
            "normal_charging_point_count",
            "fast_charging_point_count",
            "points_ge_150_kw",
            "points_ge_350_kw",
        )
    }
    for field, observed in sums.items():
        require(observed == int_value(national_row, field), f"State-to-national reconciliation failed: {field}")
    check_close(
        sum(float_value(row, "equipment_nominal_power_mw") for row in charging_rows),
        float_value(national_row, "equipment_nominal_power_mw"),
        "state-to-national nominal MW",
        tolerance=0.0001,
    )

    comparison_july = [row for row in comparison_rows if row["kba_reference_date"] == KBA_PRIMARY_DATE]
    require(len(comparison_july) == 16, "State comparison must have one July row per state")
    require({row["bnetza_reference_date"] for row in comparison_july} == {INFRASTRUCTURE_DATE}, "Unexpected comparison BNetzA date")
    state_bev = sum(int_value(row, "bev_passenger_car_stock") for row in comparison_july)
    state_phev = sum(int_value(row, "phev_passenger_car_stock") for row in comparison_july)
    require(state_bev == EXPECTED_KBA["sixteen_state_bev"], "Sixteen-state July BEV mismatch")
    require(state_phev == EXPECTED_KBA["sixteen_state_phev"], "Sixteen-state July PHEV mismatch")
    stock_july_by_state = {
        row["state_name"]: row
        for row in state_stock_rows
        if row["kba_reference_date"] == KBA_PRIMARY_DATE
    }
    require(len(stock_july_by_state) == 16, "State KBA stock must have one July row per state")
    for row in comparison_july:
        stock_row = stock_july_by_state[row["state_name"]]
        require(
            int_value(stock_row, "bev_passenger_car_stock") == int_value(row, "bev_passenger_car_stock"),
            f"July BEV mismatch between state stock and comparison for {row['state_name']}",
        )
        require(
            int_value(stock_row, "phev_passenger_car_stock") == int_value(row, "phev_passenger_car_stock"),
            f"July PHEV mismatch between state stock and comparison for {row['state_name']}",
        )

    state_rows_by_name = {row["state_name"]: row for row in charging_rows}
    top_points = max(charging_rows, key=lambda row: int_value(row, "charging_point_count"))
    top_fast_share = max(charging_rows, key=lambda row: float_value(row, "fast_point_share_pct"))
    top_penetration = max(comparison_july, key=lambda row: float_value(row, "bev_penetration_pct"))
    require(top_points["state_name"] == "Nordrhein-Westfalen", "Unexpected top state by charging points")
    require(int_value(top_points, "charging_point_count") == 41_536, "Unexpected Nordrhein-Westfalen point count")
    require(top_fast_share["state_name"] == "Sachsen-Anhalt", "Unexpected top state by fast-point share")
    check_close(float_value(top_fast_share, "fast_point_share_pct"), 39.894319683, "Sachsen-Anhalt fast share")
    require(top_penetration["state_name"] == "Hamburg", "Unexpected top state by BEV penetration")
    check_close(float_value(top_penetration, "bev_penetration_pct"), 5.9735169262, "Hamburg BEV penetration")

    return {
        "state_count": len(charging_rows),
        "sixteen_state_bev": state_bev,
        "sixteen_state_phev": state_phev,
        "sonstige_bev": EXPECTED_KBA["national_bev"] - state_bev,
        "top_points_state": top_points["state_name"],
        "top_points": int_value(top_points, "charging_point_count"),
        "top_bev_penetration_state": top_penetration["state_name"],
        "top_bev_penetration_pct": format_decimal(float_value(top_penetration, "bev_penetration_pct")),
        "top_fast_share_state": top_fast_share["state_name"],
        "top_fast_share_pct": format_decimal(float_value(top_fast_share, "fast_point_share_pct")),
        "state_charging_sum": sums,
        "unused_state_names_check": len(state_rows_by_name),
    }


def validate_comparison_scope(comparison_rows: Sequence[Mapping[str, str]]) -> None:
    for row in comparison_rows:
        require(row["comparison_scope"] == "16 federal states", "Comparison scope drifted from 16 federal states")
        require(row["cross_source_temporal_label"] == "CROSS-SNAPSHOT DESCRIPTIVE COMPARISON", "Comparison warning label missing")
        require(row["kba_reference_date"] == KBA_PRIMARY_DATE, "Comparison KBA date is not July 2026")
        require(row["bnetza_reference_date"] == INFRASTRUCTURE_DATE, "Comparison BNetzA date is not September 2026")


def fetch_status_rows(database: Path) -> Tuple[List[Dict[str, Any]], str]:
    before = sha256(database)
    connection = duckdb.connect(str(database), read_only=True)
    try:
        rows = connection.execute(
            """
            SELECT status, COUNT(*) AS equipment_count
            FROM core.charging_equipment
            GROUP BY status
            ORDER BY status
            """
        ).fetchall()
        total = connection.execute("SELECT COUNT(*) FROM core.charging_equipment").fetchone()[0]
    finally:
        connection.close()
    after = sha256(database)
    require(before == after, "DuckDB SHA-256 changed during read-only status inspection")
    require(total == EXPECTED_INFRASTRUCTURE["equipment_count"], "DuckDB equipment count mismatch")
    status_rows = [{"status": status, "equipment_count": int(count)} for status, count in rows]
    observed = {row["status"]: row["equipment_count"] for row in status_rows}
    require(observed == EXPECTED_STATUS, f"Unexpected equipment statuses: {observed!r}")
    return status_rows, before


def build_power_bands(national_row: Mapping[str, str]) -> List[Dict[str, str]]:
    total = int_value(national_row, "charging_point_count")
    normal = int_value(national_row, "normal_charging_point_count")
    fast = int_value(national_row, "fast_charging_point_count")
    ge150 = int_value(national_row, "points_ge_150_kw")
    ge350 = int_value(national_row, "points_ge_350_kw")
    counts = [normal, fast - ge150, ge150 - ge350, ge350]
    require(all(count >= 0 for count in counts), "Power-band derivation produced a negative count")
    require(sum(counts) == total, "Mutually exclusive power bands do not total national points")
    labels = (
        "Normal ≤22 kW",
        "Fast >22 and <150 kW",
        "High power ≥150 and <350 kW",
        "Ultra-fast ≥350 kW",
    )
    return [
        {
            "power_band_order": str(index),
            "power_band": label,
            "bnetza_reference_date": INFRASTRUCTURE_DATE,
            "charging_point_count": str(count),
            "charging_point_share_pct": format_pct(count, total),
        }
        for index, (label, count) in enumerate(zip(labels, counts), start=1)
    ]


def build_status_rows(status_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, str]]:
    total = sum(int(row["equipment_count"]) for row in status_rows)
    require(total == EXPECTED_INFRASTRUCTURE["equipment_count"], "Equipment-status counts do not total equipment")
    order = {"In Betrieb": 1, "In Wartung": 2}
    return [
        {
            "status_order": str(order[row["status"]]),
            "equipment_status": str(row["status"]),
            "bnetza_reference_date": INFRASTRUCTURE_DATE,
            "equipment_count": str(row["equipment_count"]),
            "equipment_share_pct": format_pct(int(row["equipment_count"]), total),
        }
        for row in sorted(status_rows, key=lambda item: order[item["status"]])
    ]


def build_report(
    manifest: Mapping[str, Any],
    export_hashes: Mapping[str, str],
    source_count: int,
    database_hash: str,
    national: Mapping[str, Any],
    states: Mapping[str, Any],
    power_bands: Sequence[Mapping[str, str]],
    status_rows: Sequence[Mapping[str, str]],
    output_hashes: Mapping[str, str],
) -> str:
    lines = [
        "# Batch 21 — Tableau executive overview validation",
        "",
        "**Status: DATA_PREPARATION_PASS**",
        "",
        "This report records the deterministic presentation preparation for the approved two-page Tableau executive overview. It does not claim that a Tableau workbook was created.",
        "",
        "## Scope and implementation capability",
        "",
        "- Approved pages: `01 — National Summary` and `02 — Geographic View`.",
        "- Tableau Desktop 2026.3 is installed locally, but no approved Tableau authoring MCP, computer-use bridge, `tableau` CLI or `tabcmd` executable was available to this session.",
        "- The workbook remains **TABLEAU_WORKBOOK_NOT_YET_CREATED**. Native Desktop worksheet and dashboard instructions are in `docs/tableau-executive-overview.md`.",
        "- No workbook XML, `.twb`, `.twbx`, extract, remote, upload or publication was created.",
        "",
        "## Inputs and immutability",
        "",
        f"- Batch 19 export version: `{manifest['export_version']}`.",
        f"- Batch 19 exports checked: {len(export_hashes)}; all manifest row counts, column counts and SHA-256 values matched.",
        f"- Manifest-listed raw/reference/report fingerprints checked: {source_count}; all matched.",
        f"- DuckDB opened read-only; SHA-256 before/after status inspection: `{database_hash}` / `{database_hash}`.",
        "- Existing Batch 19 CSVs, DuckDB, raw workbooks, reference crosswalks and backups were not written.",
        "",
        "### Batch 19 export hashes",
        "",
        "| File | SHA-256 |",
        "|---|---|",
    ]
    lines.extend(f"| `{filename}` | `{digest}` |" for filename, digest in sorted(export_hashes.items()))
    lines.extend(
        [
            "",
            "## National validation",
            "",
            "| Measure | Observed |",
            "|---|---:|",
            f"| Equipment records | {national['equipment_count']:,} |",
            f"| Populated charging-point slots | {national['charging_point_count']:,} |",
            f"| National July 2026 BEV stock | {national['national_july_bev']:,} |",
            f"| National July 2026 PHEV stock | {national['national_july_phev']:,} |",
            f"| National history observations | {national['history_rows']} ({national['history_first_date']} to {national['history_last_date']}) |",
            "",
            "All requested national infrastructure measures matched: 117,662 equipment; 211,253 points; 156,155 normal points; 55,098 fast points; 40,950 points at least 150 kW; 6,950 points at least 350 kW; and 9,215.4173 MW declared nominal equipment power.",
            "",
            "## Geographic validation",
            "",
            "| Measure | Observed |",
            "|---|---:|",
            f"| State records | {states['state_count']} |",
            f"| Sixteen-state July 2026 BEV stock | {states['sixteen_state_bev']:,} |",
            f"| National-minus-sixteen-state Sonstige BEV stock | {states['sonstige_bev']:,} |",
            f"| Sixteen-state July 2026 PHEV stock | {states['sixteen_state_phev']:,} |",
            f"| Most charging points | {states['top_points_state']}: {states['top_points']:,} |",
            f"| Highest BEV penetration | {states['top_bev_penetration_state']}: {states['top_bev_penetration_pct']}% |",
            f"| Highest fast-point share | {states['top_fast_share_state']}: {states['top_fast_share_pct']}% |",
            "",
            "The state comparison remains a fixed, pre-combined 16-state fact at KBA 2026-07-01 versus BNetzA 2026-09-30. No state charging row was joined to multiple KBA dates. `Deutschland` and `Sonstige` remain outside the 16-state geographic view.",
            "",
            "## Derived presentation contracts",
            "",
            "### Mutually exclusive charging-power bands",
            "",
            "| Order | Band | Points | Share |",
            "|---:|---|---:|---:|",
        ]
    )
    lines.extend(
        f"| {row['power_band_order']} | {row['power_band']} | {int(row['charging_point_count']):,} | {row['charging_point_share_pct']}% |"
        for row in power_bands
    )
    lines.extend(
        [
            "",
            f"The four bands total exactly {sum(int(row['charging_point_count']) for row in power_bands):,} points. The derived rows use the national export's nested thresholds as: normal; fast minus >=150; >=150 minus >=350; and >=350.",
            "",
            "### Published equipment status",
            "",
            "| Order | Status | Equipment | Share |",
            "|---:|---|---:|---:|",
        ]
    )
    lines.extend(
        f"| {row['status_order']} | {row['equipment_status']} | {int(row['equipment_count']):,} | {row['equipment_share_pct']}% |"
        for row in status_rows
    )
    lines.extend(
        [
            "",
            "The small `In Wartung` category remains visible as a labelled row; any Tableau bar axis must start at zero and must not use a truncated axis or broken scale.",
            "",
            "## Derived output hashes",
            "",
            "| File | SHA-256 |",
            "|---|---|",
        ]
    )
    lines.extend(f"| `{filename}` | `{digest}` |" for filename, digest in sorted(output_hashes.items()))
    lines.extend(
        [
            "",
            "## Remaining verification",
            "",
            "- Native Tableau Desktop assembly, official geographic recognition of all 16 states, dashboard screenshots and visual clipping checks remain manual because no approved authoring bridge was available.",
            "- The owner must save the verified workbook as a real `.twb` and optionally `.twbx`; the repository must not receive a claimed workbook path until Tableau Desktop opens and verifies it.",
            "- No external publication was attempted or authorized.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Batch 21 Tableau overview data contracts")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--preparation-dir", type=Path, default=DEFAULT_PREPARATION_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    database = args.database if args.database.is_absolute() else ROOT / args.database
    export_dir = args.export_dir if args.export_dir.is_absolute() else ROOT / args.export_dir
    preparation_dir = args.preparation_dir if args.preparation_dir.is_absolute() else ROOT / args.preparation_dir
    report_path = args.report if args.report.is_absolute() else ROOT / args.report

    require(database.is_file(), f"Missing DuckDB database: {database}")
    database_before = sha256(database)
    manifest, exports = load_and_validate_manifest(export_dir)
    national_fields, national_rows = exports[NATIONAL_CHARGING_FILE]
    charging_fields, charging_rows = exports[STATE_CHARGING_FILE]
    comparison_fields, comparison_rows = exports[STATE_COMPARISON_FILE]
    state_stock_fields, state_stock_rows = exports[KBA_STATE_FILE]
    history_fields, history_rows = exports[NATIONAL_HISTORY_FILE]
    del national_fields, charging_fields, comparison_fields, state_stock_fields, history_fields

    national = validate_national(national_rows, history_rows)
    validate_comparison_scope(comparison_rows)
    states = validate_states(charging_rows, comparison_rows, state_stock_rows, national_rows[0])
    raw_status_rows, status_database_hash = fetch_status_rows(database)
    require(status_database_hash == database_before, "DuckDB hash changed between validation stages")

    power_bands = build_power_bands(national_rows[0])
    status_rows = build_status_rows(raw_status_rows)
    power_path = preparation_dir / "power_band_distribution_2026_09_30.csv"
    status_path = preparation_dir / "equipment_status_breakdown_2026_09_30.csv"
    power_fields = [
        "power_band_order",
        "power_band",
        "bnetza_reference_date",
        "charging_point_count",
        "charging_point_share_pct",
    ]
    status_fields = [
        "status_order",
        "equipment_status",
        "bnetza_reference_date",
        "equipment_count",
        "equipment_share_pct",
    ]
    write_csv(power_path, power_fields, power_bands)
    write_csv(status_path, status_fields, status_rows)

    database_after = sha256(database)
    require(database_before == database_after, "DuckDB SHA-256 changed during Batch 21 preparation")
    export_hashes = {filename: sha256(export_dir / filename) for filename in exports}
    output_hashes = {str(path.relative_to(ROOT)): sha256(path) for path in (power_path, status_path)}
    report = build_report(
        manifest,
        export_hashes,
        len(manifest.get("source_dataset_versions", [])),
        database_before,
        national,
        states,
        power_bands,
        status_rows,
        output_hashes,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)
    print("DATA_PREPARATION_PASS")
    print(f"power_bands={power_path.relative_to(ROOT)} sha256={output_hashes[str(power_path.relative_to(ROOT))]}")
    print(f"equipment_status={status_path.relative_to(ROOT)} sha256={output_hashes[str(status_path.relative_to(ROOT))]}")
    print(f"validation_report={report_path.relative_to(ROOT)}")
    print(f"duckdb_sha256={database_before}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"DATA_PREPARATION_FAIL: {exc}")
        raise SystemExit(1)
