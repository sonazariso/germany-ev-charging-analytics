#!/usr/bin/env python3
"""Deploy the Batch 13.2 historical BBSR geography harmonization.

The layer is intentionally separate from the official Batch 13 BBSR baseline
and the owner-approved Batch 13.1 scenario.  It maps the BNetzA 2026 source
rows to the BBSR 2025 historical target geography, combining Hanau with the
remaining Main-Kinzig-Kreis components and correcting the preserved Kassel
city/county administrative join.

The script performs a read-only audit and baseline snapshot before a verified
DuckDB backup and a single transactional write.  It never changes raw files,
the KBA Crosswalk, KBA analytics, or existing Batch 13/13.1 objects.

Examples from the repository root::

    .venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py \
        --build-reference-only --json
    .venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py \
        --dry-run --json
    .venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py \
        --json

For an idempotency check, pass the first verified backup with
``--backup-path`` on a subsequent deployment.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata
from collections import Counter
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_BBSR = ROOT / "data/reference/bbsr_settlement_types_2025.csv"
DEFAULT_BBSR_WORKBOOK = ROOT / "data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx"
DEFAULT_REFERENCE = ROOT / "data/reference/bnetza_bbsr_historical_harmonization_2025.csv"
DEFAULT_MANIFEST = ROOT / "data/reference/bnetza_bbsr_historical_harmonization_2025_manifest.json"
DEFAULT_BRIDGE = ROOT / "data/reference/bnetza_bbsr_bridge_2025.csv"
DEFAULT_SQL = ROOT / "sql/13_2_hanau_geographic_harmonization.sql"
DEFAULT_BACKUP_DIR = ROOT / "data/backups"

SOURCE_ID = "bnetza_charging_2026_09_30"
BNETZA_REFERENCE_DATE = dt.date(2026, 9, 30)
BBSR_REFERENCE_DATE = dt.date(2025, 12, 31)
HARMONIZATION_VERSION = "batch13.2-2026-11-02-bbsr-2025-historical-boundary"
BBSR_SOURCE_VERSION = (
    "raumgliederungen-referenzen-2025.xlsx | Kreisreferenz | "
    "geographic stand 2025-12-31"
)
BBSR_SOURCE_SHA256 = "e35c57da8d8f675fa132b629e6dda43180a18e5b78b95e1e72de30069a062e65"
RAW_BBSR_SHA256 = "083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525"

CATEGORY_LABELS = {
    "1": "kreisfreie Großstadt",
    "2": "städtischer Kreis",
    "3": "ländlicher Kreis mit Verdichtungsansätzen",
    "4": "dünn besiedelter ländlicher Kreis",
}
EXPECTED_TYPE_COUNTS = {"1": 68, "2": 131, "3": 98, "4": 103}

EXPECTED = {
    "equipment": 117_662,
    "points": 211_253,
    "normal_points": 156_155,
    "fast_points": 55_098,
    "points_ge_150": 40_950,
    "points_ge_350": 6_950,
    "unclassifiable_points": 0,
    "bnetza_geographies": 401,
    "historical_bbsr_rows": 400,
}
EXPECTED_NOMINAL_POWER_MW = 9_215.4173

BBSR_COLUMNS = (
    "source_version",
    "bbsr_reference_date",
    "source_sheet_name",
    "source_excel_row",
    "administrative_district_code",
    "administrative_district_name",
    "federal_state_code",
    "federal_state_name",
    "kreisregion_code",
    "kreisregion_name",
    "settlement_type_code",
    "settlement_type_name_de",
)

HARMONIZATION_COLUMNS = (
    "harmonization_version",
    "bnetza_source_id",
    "bnetza_reference_date",
    "bnetza_state_name",
    "bnetza_district_name",
    "bnetza_admin_type",
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
    "source_component_role",
    "mapping_method",
    "boundary_compatibility_status",
    "evidence_source_reference",
    "validation_notes",
)

NEW_OBJECTS = (
    "reference.bnetza_bbsr_historical_harmonization_2025",
    "analytics.charging_by_bbsr_district_2025_harmonized",
    "analytics.charging_by_bbsr_type_2025_harmonized",
)

BASELINE_OBJECTS = (
    "reference.bnetza_bbsr_district_bridge_2025",
    "analytics.charging_by_bbsr_district_2025",
    "analytics.charging_by_bbsr_type_2025",
    "reference.bnetza_bbsr_owner_override_2026",
    "analytics.charging_by_bbsr_district_2026_scenario",
    "analytics.charging_by_bbsr_type_2026_scenario",
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
    """Raised when the safe Batch 13.2 deployment cannot proceed."""


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


def scalar(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: Sequence[Any] = (),
) -> Any:
    return conn.execute(sql, params).fetchone()[0]


def query_dicts(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: Sequence[Any] = (),
) -> list[dict[str, Any]]:
    result = conn.execute(sql, params)
    names = [item[0] for item in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def normalise_text(value: str) -> str:
    text = (value or "").upper()
    text = text.replace("Ä", "AE").replace("Ö", "OE").replace("Ü", "UE")
    text = text.replace("ẞ", "SS").replace("ß", "SS")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", text)).strip()


def administrative_identity_key(value: str, semantic_aliases: bool = False) -> str:
    text = normalise_text(value)
    if semantic_aliases:
        # BBSR's official Kassel city label is ``Kassel, documenta-Stadt``;
        # this is a semantic name alias, not a second administrative unit.
        for alias in (
            "DOCUMENTA STADT",
            "STADT DER FERNUNIVERSITAET",
            "WISSENSCHAFTSSTADT",
            "LANDESHAUPTSTADT",
            "FREIE UND HANSESTADT",
            "KLINGENSTADT",
            "HANSESTADT",
        ):
            text = text.replace(alias, " ")
    patterns = (
        r"^KREISFREIE STADT\s+",
        r"^STADTKREIS\s+",
        r"^LANDKREIS\s+",
        r"^KREIS\s+",
        r"\s+KREISFREIE STADT$",
        r"\s+STADTKREIS$",
        r"\s+LANDKREIS$",
        r"\s+KREIS$",
        r"\s+STADT$",
        r"\s+FREIE UND HANSESTADT$",
        r"\s+HANSESTADT$",
        r"\s+LANDESHAUPTSTADT$",
        r"\s+WISSENSCHAFTSSTADT$",
        r"\s+STADT DER FERNUNIVERSITAET$",
        r"\s+KLINGENSTADT$",
    )
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    return re.sub(r"[^A-Z0-9]+", "", text)


def source_admin_type(value: str) -> str:
    text = normalise_text(value)
    if text.startswith("KREISFREIE STADT ") or text.startswith("STADTKREIS "):
        return "city"
    if text.startswith("LANDKREIS ") or text.startswith("KREIS "):
        return "county"
    raise DeploymentError(f"Cannot derive BNetzA administrative form from {value!r}")


def read_csv_rows(path: Path, expected_columns: Sequence[str]) -> list[dict[str, str]]:
    require(path.is_file(), f"Missing CSV source: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(
            tuple(reader.fieldnames or ()) == tuple(expected_columns),
            f"Unexpected CSV schema in {path}: {reader.fieldnames}",
        )
        return [dict(row) for row in reader]


def load_bbsr_csv(path: Path) -> list[dict[str, str]]:
    rows = read_csv_rows(path, BBSR_COLUMNS)
    require(len(rows) == EXPECTED["historical_bbsr_rows"], f"BBSR row count changed: {len(rows)}")
    require(
        all(row["source_version"] == BBSR_SOURCE_VERSION for row in rows),
        "BBSR source version changed",
    )
    require(
        all(row["bbsr_reference_date"] == BBSR_REFERENCE_DATE.isoformat() for row in rows),
        "BBSR reference date changed",
    )
    codes = [row["administrative_district_code"] for row in rows]
    require(all(re.fullmatch(r"[0-9]{8}", code or "") for code in codes), "Invalid BBSR district code")
    require(len(set(codes)) == len(codes), "Duplicate BBSR district code")
    require(
        all(row["settlement_type_code"] in CATEGORY_LABELS for row in rows),
        "Invalid BBSR category code",
    )
    require(
        all(CATEGORY_LABELS[row["settlement_type_code"]] == row["settlement_type_name_de"] for row in rows),
        "BBSR category label mismatch",
    )
    require(
        Counter(row["settlement_type_code"] for row in rows) == Counter(EXPECTED_TYPE_COUNTS),
        "BBSR category counts changed",
    )
    return rows


def load_bbsr_raw_admin(path: Path, bbsr_rows: Sequence[Mapping[str, str]]) -> dict[str, dict[str, str]]:
    """Read the official workbook's administrative-form fields.

    The derived CSV intentionally keeps the four BBSR analytical fields only.
    The raw workbook's SLK2025 column is therefore read here as the independent
    city/county evidence used to prevent the Kassel join error from recurring.
    """
    require(path.is_file(), f"Missing raw BBSR workbook: {path}")
    module_path = ROOT / "scripts/10_build_bbsr_reference.py"
    spec = importlib.util.spec_from_file_location("batch10_bbsr_reference", module_path)
    require(spec is not None and spec.loader is not None, "Cannot load BBSR workbook parser")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    workbook, selected_rows = module.inspect_workbook(path)
    require(workbook["reference_date_from_workbook"] == BBSR_REFERENCE_DATE.isoformat(), "Raw BBSR geographic stand changed")
    selected = next(sheet for sheet in workbook["sheets"] if sheet["sheet_name"] == "Kreisreferenz")
    by_name = {column["field_name"]: column for column in selected["original_columns"]}
    required = (
        "KRS2025",
        "KRS_NAME",
        "BLD2025",
        "BLD_NAME",
        "SLK2025",
        "SLK_NAME",
    )
    indexes = {
        field: module.excel_column_number(by_name[field]["excel_column"])
        for field in required
    }
    raw_by_code: dict[str, dict[str, str]] = {}
    for row_number, values in selected_rows:
        item = {
            field: values.get(indexes[field], "")
            for field in required
        }
        require(all(item[field].strip() for field in required), f"Missing raw BBSR administrative field at row {row_number}")
        require(item["SLK2025"] in {"1", "2"}, f"Unexpected BBSR administrative form {item['SLK2025']!r} at row {row_number}")
        require(item["KRS2025"] not in raw_by_code, f"Duplicate raw BBSR code {item['KRS2025']}")
        raw_by_code[item["KRS2025"]] = item
    require(len(raw_by_code) == EXPECTED["historical_bbsr_rows"], "Raw BBSR administrative row count changed")
    require(
        set(raw_by_code) == {row["administrative_district_code"] for row in bbsr_rows},
        "Raw and derived BBSR administrative code sets differ",
    )
    return raw_by_code


def source_rows(conn: duckdb.DuckDBPyConnection) -> list[dict[str, str]]:
    rows = query_dicts(
        conn,
        f"""
        SELECT state_name, district_name
        FROM core.charging_equipment
        WHERE source_id = '{SOURCE_ID}'
        GROUP BY state_name, district_name
        ORDER BY state_name, district_name
        """,
    )
    require(len(rows) == EXPECTED["bnetza_geographies"], f"BNetzA source geography count changed: {len(rows)}")
    result = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["state_name"], row["district_name"])
        require(key not in seen, f"Duplicate BNetzA source geography: {key}")
        seen.add(key)
        result.append(
            {
                "bnetza_state_name": row["state_name"],
                "bnetza_district_name": row["district_name"],
                "bnetza_admin_type": source_admin_type(row["district_name"]),
            }
        )
    return result


def bbsr_admin_type(raw_row: Mapping[str, str]) -> str:
    return {"1": "city", "2": "county"}[raw_row["SLK2025"]]


def anti_join_audit(
    bbsr_rows: Sequence[Mapping[str, str]],
    raw_by_code: Mapping[str, Mapping[str, str]],
    sources: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    bbsr_by_code = {row["administrative_district_code"]: row for row in bbsr_rows}
    bbsr_strict = {
        (
            row["federal_state_name"],
            bbsr_admin_type(raw_by_code[row["administrative_district_code"]]),
            administrative_identity_key(row["administrative_district_name"]),
        ): row["administrative_district_code"]
        for row in bbsr_rows
    }
    source_strict = {
        (
            row["bnetza_state_name"],
            row["bnetza_admin_type"],
            administrative_identity_key(row["bnetza_district_name"]),
        ): row
        for row in sources
    }
    bbsr_semantic = {
        (
            row["federal_state_name"],
            bbsr_admin_type(raw_by_code[row["administrative_district_code"]]),
            administrative_identity_key(row["administrative_district_name"], semantic_aliases=True),
        ): row["administrative_district_code"]
        for row in bbsr_rows
    }
    source_semantic = {
        (
            row["bnetza_state_name"],
            row["bnetza_admin_type"],
            administrative_identity_key(row["bnetza_district_name"], semantic_aliases=True),
        ): row
        for row in sources
    }

    def format_bbsr(keys: set[tuple[str, str, str]], mapping: Mapping[tuple[str, str, str], str]) -> list[dict[str, str]]:
        return [
            {
                "state_name": state,
                "administrative_form": admin,
                "identity_key": identity,
                "bbsr_code": mapping[(state, admin, identity)],
                "bbsr_name": bbsr_by_code[mapping[(state, admin, identity)]]["administrative_district_name"],
            }
            for state, admin, identity in sorted(keys)
        ]

    def format_source(keys: set[tuple[str, str, str]], mapping: Mapping[tuple[str, str, str], Mapping[str, str]]) -> list[dict[str, str]]:
        return [
            {
                "state_name": state,
                "administrative_form": admin,
                "identity_key": identity,
                "bnetza_district_name": mapping[(state, admin, identity)]["bnetza_district_name"],
            }
            for state, admin, identity in sorted(keys)
        ]

    strict_bbsr_only = set(bbsr_strict) - set(source_strict)
    strict_source_only = set(source_strict) - set(bbsr_strict)
    semantic_bbsr_only = set(bbsr_semantic) - set(source_semantic)
    semantic_source_only = set(source_semantic) - set(bbsr_semantic)
    require(len(strict_bbsr_only) == 1, f"Unexpected strict BBSR-only anti-join: {strict_bbsr_only}")
    require(len(strict_source_only) == 2, f"Unexpected strict BNetzA-only anti-join: {strict_source_only}")
    require(len(semantic_bbsr_only) == 0, f"Unexpected semantic BBSR-only anti-join: {semantic_bbsr_only}")
    require(len(semantic_source_only) == 1, f"Unexpected semantic BNetzA-only anti-join: {semantic_source_only}")
    return {
        "strict": {
            "bbsr_only": format_bbsr(strict_bbsr_only, bbsr_strict),
            "bnetza_only": format_source(strict_source_only, source_strict),
        },
        "semantic_alias_normalized": {
            "bbsr_only": [],
            "bnetza_only": format_source(semantic_source_only, source_semantic),
        },
        "interpretation": {
            "bbsr_only_code": "06611000",
            "bbsr_only_name": "Kassel, documenta-Stadt",
            "bnetza_only_current_unit": "Hessen | Kreisfreie Stadt Hanau",
            "kassel_alias_reconciled": True,
            "kreis_vs_kreisregion_explains_68_vs_67": False,
        },
    }


def load_existing_bridge_audit(path: Path) -> dict[str, Any]:
    required = {
        "bnetza_state_name",
        "bnetza_district_name",
        "bbsr_administrative_district_code",
        "bbsr_administrative_district_name",
        "bbsr_settlement_type_code",
    }
    require(path.is_file(), f"Missing existing Batch 13 bridge: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(required <= set(reader.fieldnames or ()), "Existing bridge schema is incomplete")
        rows = [dict(row) for row in reader]
    by_name = {(row["bnetza_state_name"], row["bnetza_district_name"]): row for row in rows}
    kassel_city = by_name.get(("Hessen", "Kreisfreie Stadt Kassel"))
    kassel_county = by_name.get(("Hessen", "Landkreis Kassel"))
    require(kassel_city is not None and kassel_county is not None, "Existing bridge Kassel rows are missing")
    require(kassel_city["bbsr_administrative_district_code"] == "06633000", "Preserved Batch 13 Kassel city join unexpectedly changed")
    require(kassel_city["bbsr_settlement_type_code"] == "2", "Preserved Batch 13 Kassel city type unexpectedly changed")
    require(kassel_county["bbsr_administrative_district_code"] == "06633000", "Preserved Batch 13 Kassel county join unexpectedly changed")
    return {
        "rows": len(rows),
        "preserved_kassel_city_join": {
            "bbsr_code": kassel_city["bbsr_administrative_district_code"],
            "bbsr_name": kassel_city["bbsr_administrative_district_name"],
            "type_code": kassel_city["bbsr_settlement_type_code"],
            "classification": "INCORRECT_PRESERVED_BATCH13_JOIN_CORRECTED_ONLY_IN_BATCH13_2",
        },
        "preserved_kassel_county_join": {
            "bbsr_code": kassel_county["bbsr_administrative_district_code"],
            "bbsr_name": kassel_county["bbsr_administrative_district_name"],
            "type_code": kassel_county["bbsr_settlement_type_code"],
        },
    }


def build_reference_rows(
    bbsr_path: Path,
    bbsr_workbook_path: Path,
    bridge_path: Path,
    conn: duckdb.DuckDBPyConnection,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    bbsr_rows = load_bbsr_csv(bbsr_path)
    raw_by_code = load_bbsr_raw_admin(bbsr_workbook_path, bbsr_rows)
    sources = source_rows(conn)
    audit = anti_join_audit(bbsr_rows, raw_by_code, sources)
    bridge_audit = load_existing_bridge_audit(bridge_path)
    by_semantic: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    bbsr_by_code = {row["administrative_district_code"]: row for row in bbsr_rows}
    for row in bbsr_rows:
        code = row["administrative_district_code"]
        raw = raw_by_code[code]
        key = (
            row["federal_state_name"],
            bbsr_admin_type(raw),
            administrative_identity_key(row["administrative_district_name"], semantic_aliases=True),
        )
        by_semantic.setdefault(key, []).append(row)

    evidence_reference = (
        "data/reference/bbsr_settlement_types_2025.csv; "
        "data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx; "
        "official Hessian Hanau boundary law and implementation pages; "
        "reports/batch13_2_hanau_geographic_harmonization.md"
    )
    rows: list[dict[str, str]] = []
    for source in sources:
        state = source["bnetza_state_name"]
        district = source["bnetza_district_name"]
        admin = source["bnetza_admin_type"]
        is_hanau = (state, district) == ("Hessen", "Kreisfreie Stadt Hanau")
        is_main_kinzig = (state, district) == ("Hessen", "Landkreis Main-Kinzig-Kreis")
        if is_hanau or is_main_kinzig:
            target_code = "06435000"
            target = bbsr_by_code[target_code]
            role = (
                "HISTORICAL_COMPONENT_HANAU"
                if is_hanau
                else "HISTORICAL_COMPONENT_REMAINING_MKK"
            )
            method = "HISTORICAL_BOUNDARY_RECONSTRUCTION"
            status = "HISTORICAL_COMPONENT_RECONSTRUCTED"
            notes = (
                "Hanau became an independent city effective 2026-01-01 and was removed "
                "from Main-Kinzig-Kreis. The Hessian boundary law lists Hanau together "
                "with the remaining Main-Kinzig municipalities as the pre-change "
                "district components. This source row contributes to the historical "
                "BBSR 2025 Main-Kinzig target 06435000; it is not assigned an official "
                "2026 Hanau BBSR type."
            )
        else:
            key = (state, admin, administrative_identity_key(district, semantic_aliases=True))
            candidates = by_semantic.get(key, [])
            require(len(candidates) == 1, f"BBSR semantic identity is not unique for {state}|{district}: {candidates}")
            target = candidates[0]
            target_code = target["administrative_district_code"]
            role = "DIRECT_SOURCE_UNIT"
            if target_code == "06611000" and district == "Kreisfreie Stadt Kassel":
                method = "CORRECTED_BBSR_ALIAS_AND_ADMINISTRATIVE_TYPE_IDENTITY"
                status = "DIRECT_2025_SOURCE_IDENTITY_CORRECTED"
                notes = (
                    "Corrects the preserved Batch 13 city/county collision: BNetzA "
                    "Kreisfreie Stadt Kassel is matched to BBSR KRS2025 06611000 "
                    "(Kassel, documenta-Stadt), whose raw BBSR SLK2025 administrative "
                    "form is 1 (kreisfreie Stadt). The preserved Batch 13 bridge is "
                    "intentionally unchanged."
                )
            else:
                method = "DIRECT_STATE_ADMIN_TYPE_SEMANTIC_IDENTITY"
                status = "DIRECT_2025_SOURCE_IDENTITY"
                notes = (
                    "Unique federal-state + administrative-form + semantic administrative "
                    "identity against the BBSR 2025 Kreis reference; the raw BBSR "
                    "SLK2025 field supplies the independent city/county form."
                )

        require(target["settlement_type_code"] in CATEGORY_LABELS, f"Invalid target type for {state}|{district}")
        rows.append(
            {
                "harmonization_version": HARMONIZATION_VERSION,
                "bnetza_source_id": SOURCE_ID,
                "bnetza_reference_date": BNETZA_REFERENCE_DATE.isoformat(),
                "bnetza_state_name": state,
                "bnetza_district_name": district,
                "bnetza_admin_type": admin,
                "historical_bbsr_reference_date": BBSR_REFERENCE_DATE.isoformat(),
                "historical_bbsr_source_version": target["source_version"],
                "historical_bbsr_source_sha256": sha256(bbsr_path),
                "historical_bbsr_administrative_district_code": target_code,
                "historical_bbsr_administrative_district_name": target["administrative_district_name"],
                "historical_bbsr_federal_state_code": target["federal_state_code"],
                "historical_bbsr_federal_state_name": target["federal_state_name"],
                "historical_bbsr_kreisregion_code": target["kreisregion_code"],
                "historical_bbsr_kreisregion_name": target["kreisregion_name"],
                "historical_bbsr_settlement_type_code": target["settlement_type_code"],
                "historical_bbsr_settlement_type_name_de": target["settlement_type_name_de"],
                "source_component_role": role,
                "mapping_method": method,
                "boundary_compatibility_status": status,
                "evidence_source_reference": evidence_reference,
                "validation_notes": notes,
            }
        )

    require(len(rows) == EXPECTED["bnetza_geographies"], "Harmonization source row count failed")
    require(len({(row["bnetza_state_name"], row["bnetza_district_name"]) for row in rows}) == EXPECTED["bnetza_geographies"], "Harmonization source key uniqueness failed")
    target_counts = Counter(row["historical_bbsr_administrative_district_code"] for row in rows)
    require(len(target_counts) == EXPECTED["historical_bbsr_rows"], "Harmonization target row count failed")
    require(
        Counter(
            target["settlement_type_code"]
            for target in bbsr_by_code.values()
        ) == Counter(EXPECTED_TYPE_COUNTS),
        "BBSR target category counts failed",
    )
    require(
        Counter(
            bbsr_by_code[code]["settlement_type_code"]
            for code in target_counts
        ) == Counter(EXPECTED_TYPE_COUNTS),
        "Harmonization target category counts failed",
    )
    require(
        target_counts["06435000"] == 2,
        "Historical Main-Kinzig target does not contain exactly Hanau and remaining MKK components",
    )
    by_source = {(row["bnetza_state_name"], row["bnetza_district_name"]): row for row in rows}
    require(
        by_source[("Hessen", "Kreisfreie Stadt Hanau")]["historical_bbsr_administrative_district_code"] == "06435000",
        "Hanau historical target changed",
    )
    require(
        by_source[("Hessen", "Landkreis Main-Kinzig-Kreis")]["historical_bbsr_administrative_district_code"] == "06435000",
        "Main-Kinzig historical target changed",
    )
    require(
        by_source[("Hessen", "Kreisfreie Stadt Kassel")]["historical_bbsr_administrative_district_code"] == "06611000"
        and by_source[("Hessen", "Kreisfreie Stadt Kassel")]["historical_bbsr_settlement_type_code"] == "1",
        "Kassel city was not corrected to BBSR type 1",
    )
    require(
        by_source[("Hessen", "Landkreis Kassel")]["historical_bbsr_administrative_district_code"] == "06633000"
        and by_source[("Hessen", "Landkreis Kassel")]["historical_bbsr_settlement_type_code"] == "2",
        "Kassel county target changed",
    )
    return rows, {
        "source_rows": len(rows),
        "historical_target_rows": len(target_counts),
        "source_component_counts_by_target": dict(sorted(Counter(target_counts.values()).items())),
        "historical_target_type_counts": dict(sorted(EXPECTED_TYPE_COUNTS.items())),
        "anti_join_audit": audit,
        "preserved_batch13_bridge_audit": bridge_audit,
        "correction": {
            "source": "Hessen | Kreisfreie Stadt Kassel",
            "preserved_batch13_target": "06633000 | Kassel | type 2",
            "batch13_2_target": "06611000 | Kassel, documenta-Stadt | type 1",
        },
        "hanau_boundary": {
            "historical_target": "06435000 | Main-Kinzig-Kreis",
            "source_components": [
                "Hessen | Kreisfreie Stadt Hanau",
                "Hessen | Landkreis Main-Kinzig-Kreis",
            ],
            "boundary_effective": "2026-01-01",
            "classification_claim": "historical BBSR 2025 target only; not an official 2026 Hanau BBSR type",
        },
        "source_hashes": {
            "bbsr_csv_sha256": sha256(bbsr_path),
            "bbsr_raw_workbook_sha256": sha256(bbsr_workbook_path),
            "expected_bbsr_csv_sha256": BBSR_SOURCE_SHA256,
            "expected_bbsr_raw_workbook_sha256": RAW_BBSR_SHA256,
        },
        "scope_controls": {
            "kba_crosswalk_used_for_assignment": False,
            "kba_objects_changed": False,
            "official_batch13_objects_changed": False,
            "batch13_1_scenario_changed": False,
            "historical_target_is_official_2026_hanau_type": False,
        },
    }


def serialized_reference_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {column: "" if row.get(column) is None else str(row.get(column)) for column in HARMONIZATION_COLUMNS}
        for row in rows
    ]


def write_or_validate_reference(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    expected_rows = serialized_reference_rows(rows)
    if path.exists():
        actual_rows = read_csv_rows(path, HARMONIZATION_COLUMNS)
        require(actual_rows == expected_rows, f"Existing harmonization reference differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HARMONIZATION_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(expected_rows)


def write_or_validate_manifest(
    path: Path,
    reference_path: Path,
    bbsr_path: Path,
    bbsr_workbook_path: Path,
    sql_path: Path,
    audit: Mapping[str, Any],
) -> None:
    manifest = {
        "manifest_version": 1,
        "harmonization_version": HARMONIZATION_VERSION,
        "reference_file": str(reference_path.relative_to(ROOT)),
        "reference_sha256": sha256(reference_path),
        "reference_row_count": audit["source_rows"],
        "source_vintage": {
            "bnetza_source_id": SOURCE_ID,
            "bnetza_reference_date": BNETZA_REFERENCE_DATE.isoformat(),
            "bbsr_reference_date": BBSR_REFERENCE_DATE.isoformat(),
            "bbsr_csv": str(bbsr_path.relative_to(ROOT)),
            "bbsr_csv_sha256": sha256(bbsr_path),
            "bbsr_raw_workbook": str(bbsr_workbook_path.relative_to(ROOT)),
            "bbsr_raw_workbook_sha256": sha256(bbsr_workbook_path),
        },
        "sql_file": str(sql_path.relative_to(ROOT)),
        "audit": audit,
        "rules": {
            "grain": "one BNetzA 2026 state/district source component per row",
            "historical_target_grain": "one BBSR 2025 KRS2025 administrative district after source-component aggregation",
            "bbsr_city_county_form_source": "raw workbook SLK2025/SLK_NAME",
            "kba_code_used_for_assignment": False,
            "official_bbsr_reference_preserved": True,
            "official_batch13_and_batch13_1_objects_preserved": True,
            "historical_hanau_type_claimed": False,
        },
    }
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        require(path.read_text(encoding="utf-8") == serialized, f"Existing harmonization manifest differs: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")


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


def stable_snapshot_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 8)
    if isinstance(value, (list, tuple)):
        return [stable_snapshot_value(item) for item in value]
    return value


def object_snapshot(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> dict[str, Any]:
    kind = object_type(conn, qualified_name)
    require(kind is not None, f"Existing object is missing: {qualified_name}")
    try:
        rows = conn.execute(f"SELECT * FROM {qualified_name} ORDER BY ALL").fetchall()
    except duckdb.Error:
        rows = conn.execute(f"SELECT * FROM {qualified_name}").fetchall()
    stable_rows = [stable_snapshot_value(row) for row in rows]
    payload = json.dumps(stable_rows, ensure_ascii=False, default=str, separators=(",", ":"))
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
    equipment = int(scalar(conn, f"SELECT COUNT(*) FROM core.charging_equipment WHERE source_id = '{SOURCE_ID}'"))
    points = int(scalar(conn, f"SELECT COUNT(*) FROM core.charging_point WHERE source_id = '{SOURCE_ID}'"))
    geographies = int(scalar(conn, f"SELECT COUNT(*) FROM (SELECT DISTINCT state_name, district_name FROM core.charging_equipment WHERE source_id = '{SOURCE_ID}')"))
    declared = int(scalar(conn, f"SELECT SUM(declared_point_count) FROM core.charging_equipment WHERE source_id = '{SOURCE_ID}'"))
    nominal_mw = float(scalar(conn, f"SELECT SUM(equipment_nominal_power_kw) / 1000.0 FROM core.charging_equipment WHERE source_id = '{SOURCE_ID}'"))
    power = tuple(int(value) for value in conn.execute(MAX_POWER_SQL).fetchone())
    require((equipment, points, geographies) == (EXPECTED["equipment"], EXPECTED["points"], EXPECTED["bnetza_geographies"]), "Core row baseline failed")
    require(declared == EXPECTED["points"], "Declared charging-point total failed")
    require(abs(nominal_mw - EXPECTED_NOMINAL_POWER_MW) < 0.00001, "Nominal power baseline failed")
    require(power == (
        EXPECTED["points"],
        EXPECTED["normal_points"],
        EXPECTED["fast_points"],
        EXPECTED["points_ge_150"],
        EXPECTED["points_ge_350"],
        EXPECTED["unclassifiable_points"],
    ), f"Maximum-per-point power baseline failed: {power}")
    equipment_key_issues = int(scalar(conn, f"""
        SELECT COUNT(*) FROM (
            SELECT source_id, excel_row FROM core.charging_equipment
            WHERE source_id = '{SOURCE_ID}'
            GROUP BY source_id, excel_row HAVING COUNT(*) <> 1
        )
    """))
    point_key_issues = int(scalar(conn, f"""
        SELECT COUNT(*) FROM (
            SELECT source_id, equipment_excel_row, point_number FROM core.charging_point
            WHERE source_id = '{SOURCE_ID}'
            GROUP BY source_id, equipment_excel_row, point_number HAVING COUNT(*) <> 1
        )
    """))
    orphan_points = int(scalar(conn, f"""
        SELECT COUNT(*)
        FROM core.charging_point p
        LEFT JOIN core.charging_equipment e
          ON e.source_id = p.source_id AND e.excel_row = p.equipment_excel_row
        WHERE p.source_id = '{SOURCE_ID}' AND e.source_id IS NULL
    """))
    mismatches = int(scalar(conn, f"""
        SELECT COUNT(*) FROM (
            SELECT e.source_id, e.excel_row,
                   COALESCE(e.declared_point_count, 0) AS declared_points,
                   COUNT(p.point_number) AS actual_points
            FROM core.charging_equipment e
            LEFT JOIN core.charging_point p
              ON p.source_id = e.source_id AND p.equipment_excel_row = e.excel_row
            WHERE e.source_id = '{SOURCE_ID}'
            GROUP BY e.source_id, e.excel_row, e.declared_point_count
            HAVING declared_points <> actual_points
        )
    """))
    require((equipment_key_issues, point_key_issues, orphan_points, mismatches) == (0, 0, 0, 0), "Core key reconciliation failed")
    return {
        "equipment": equipment,
        "points": points,
        "bnetza_geographies": geographies,
        "declared_points": declared,
        "nominal_power_mw": nominal_mw,
        "normal_points": power[1],
        "fast_points": power[2],
        "points_ge_150": power[3],
        "points_ge_350": power[4],
        "unclassifiable_points": power[5],
        "duplicate_equipment_keys": equipment_key_issues,
        "duplicate_point_keys": point_key_issues,
        "orphan_points": orphan_points,
        "equipment_point_mismatches": mismatches,
    }


def baseline_state(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    metrics = core_metrics(conn)
    for name in BASELINE_OBJECTS:
        require(object_type(conn, name) in {"BASE TABLE", "VIEW"}, f"Existing baseline object missing: {name}")
    require(int(scalar(conn, "SELECT COUNT(*) FROM reference.bnetza_bbsr_district_bridge_2025")) == 401, "Existing Batch 13 bridge row count changed")
    require(int(scalar(conn, "SELECT COUNT(*) FROM analytics.charging_by_bbsr_district_2025")) == 401, "Existing Batch 13 district view row count changed")
    require(int(scalar(conn, "SELECT COUNT(*) FROM analytics.charging_by_bbsr_type_2025")) == 5, "Existing Batch 13 type view row count changed")
    require(int(scalar(conn, "SELECT COUNT(*) FROM reference.bnetza_bbsr_owner_override_2026")) == 2, "Existing Batch 13.1 override count changed")
    require(int(scalar(conn, "SELECT COUNT(*) FROM analytics.charging_by_bbsr_district_2026_scenario")) == 401, "Existing Batch 13.1 district view row count changed")
    require(int(scalar(conn, "SELECT COUNT(*) FROM analytics.charging_by_bbsr_type_2026_scenario")) == 4, "Existing Batch 13.1 type view row count changed")
    return {
        "metrics": metrics,
        "objects": {name: object_snapshot(conn, name) for name in BASELINE_OBJECTS},
    }


def assert_existing_unchanged(conn: duckdb.DuckDBPyConnection, baseline: Mapping[str, Any]) -> None:
    for name, before in baseline["objects"].items():
        after = object_snapshot(conn, name)
        require(after == before, f"Existing protected object changed: {name}")


def no_open_database_handles(database: Path) -> None:
    try:
        result = subprocess.run(
            ["lsof", "-t", str(database)],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise DeploymentError("Cannot verify DuckDB locks because lsof is unavailable") from exc
    handles = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    require(not handles, f"DuckDB has open process handles: {handles}")


def validate_backup(path: Path, expected_baseline: Mapping[str, Any]) -> dict[str, Any]:
    require(path.is_file(), f"Missing verified backup: {path}")
    require(path.resolve() != DEFAULT_DATABASE.resolve(), "Backup path equals primary database")
    require(not Path(str(path) + ".wal").exists(), f"Backup WAL exists: {path}.wal")
    conn = duckdb.connect(str(path), read_only=True)
    try:
        actual_metrics = core_metrics(conn)
        actual_objects = {name: object_snapshot(conn, name) for name in BASELINE_OBJECTS}
    finally:
        conn.close()
    require(actual_metrics == expected_baseline["metrics"], "Backup core baseline differs")
    require(actual_objects == expected_baseline["objects"], "Backup protected-object baseline differs")
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "validated_read_only": True,
        "metrics": actual_metrics,
    }


def create_backup(database: Path, backup_dir: Path, expected_baseline: Mapping[str, Any]) -> dict[str, Any]:
    require(database.is_file(), f"Missing database: {database}")
    no_open_database_handles(database)
    wal = Path(str(database) + ".wal")
    require(not wal.exists(), f"Refusing to copy while a WAL exists: {wal}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"ev_charging_pre_batch13_2_{timestamp}.duckdb"
    require(not backup.exists(), f"Backup target already exists: {backup}")
    source_size_before = database.stat().st_size
    source_hash_before = sha256(database)
    shutil.copy2(database, backup)
    source_size_after = database.stat().st_size
    source_hash_after = sha256(database)
    require((source_size_before, source_hash_before) == (source_size_after, source_hash_after), "Database changed during backup")
    require(sha256(backup) == source_hash_after, "Backup checksum differs from source")
    evidence = validate_backup(backup, expected_baseline)
    evidence.update({"source_sha256": source_hash_after, "source_size_bytes": source_size_before, "wal_present": False})
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


def render_sql(sql: str, reference_path: Path) -> str:
    replacements = {
        "{{HARMONIZATION_CSV}}": sql_literal(str(reference_path.resolve())),
        "{{HARMONIZATION_VERSION}}": HARMONIZATION_VERSION,
        "{{SOURCE_ID}}": SOURCE_ID,
        "{{BNETZA_DATE}}": BNETZA_REFERENCE_DATE.isoformat(),
    }
    for token, value in replacements.items():
        sql = sql.replace(token, value)
    return sql


def validate_sql_source(path: Path, reference_path: Path) -> dict[str, Any]:
    sections = read_sql_sections(path)
    required_sections = {
        "create_reference_schema",
        "create_analytics_schema",
        "create_harmonization_table",
        "replace_harmonization_rows",
        "charging_by_historical_bbsr_district_view",
        "charging_by_historical_bbsr_type_view",
    }
    require(set(sections) == required_sections, f"Unexpected Batch 13.2 SQL sections: {sorted(sections)}")
    rendered = "\n\n".join(render_sql(sections[name], reference_path) for name in sections)
    lowered = rendered.lower()
    for forbidden in ("core.kba", "bev_stock", "phev", "kba_district_ev_stock"):
        require(forbidden not in lowered, f"Batch 13.2 SQL unexpectedly references {forbidden}")
    require(str(reference_path.resolve()).lower() in lowered, "Rendered SQL reference path is missing")
    return {"sections": sorted(sections), "rendered_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest()}


def deploy_sql(conn: duckdb.DuckDBPyConnection, sql_path: Path, reference_path: Path) -> None:
    sections = read_sql_sections(sql_path)
    order = (
        "create_reference_schema",
        "create_analytics_schema",
        "create_harmonization_table",
        "replace_harmonization_rows",
        "charging_by_historical_bbsr_district_view",
        "charging_by_historical_bbsr_type_view",
    )
    conn.execute("BEGIN TRANSACTION")
    try:
        for name in order:
            conn.execute(render_sql(sections[name], reference_path))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def validate_new_layer(
    conn: duckdb.DuckDBPyConnection,
    expected_rows: Sequence[Mapping[str, Any]],
    baseline: Mapping[str, Any],
) -> dict[str, Any]:
    for name in NEW_OBJECTS:
        require(object_type(conn, name) in {"BASE TABLE", "VIEW"}, f"New object was not deployed: {name}")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {NEW_OBJECTS[0]} WHERE harmonization_version = '{HARMONIZATION_VERSION}'")) == EXPECTED["bnetza_geographies"], "Harmonization table row count failed")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {NEW_OBJECTS[1]}")) == EXPECTED["historical_bbsr_rows"], "Harmonized district view row count failed")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {NEW_OBJECTS[2]}")) == 4, "Harmonized type view row count failed")

    reference_rows = query_dicts(conn, f"""
        SELECT {', '.join(HARMONIZATION_COLUMNS)}
        FROM {NEW_OBJECTS[0]}
        WHERE harmonization_version = '{HARMONIZATION_VERSION}'
        ORDER BY bnetza_state_name, bnetza_district_name
    """)
    expected_serialized = serialized_reference_rows(expected_rows)
    actual_serialized = [
        {column: "" if row[column] is None else (row[column].isoformat() if isinstance(row[column], dt.date) else str(row[column])) for column in HARMONIZATION_COLUMNS}
        for row in reference_rows
    ]
    require(actual_serialized == sorted(expected_serialized, key=lambda row: (row["bnetza_state_name"], row["bnetza_district_name"])), "Deployed harmonization table differs from deterministic reference")

    target_counts = query_dicts(conn, f"""
        SELECT historical_bbsr_settlement_type_code AS type_code, COUNT(*) AS rows
        FROM {NEW_OBJECTS[1]}
        GROUP BY 1 ORDER BY 1
    """)
    require({row["type_code"]: int(row["rows"]) for row in target_counts} == EXPECTED_TYPE_COUNTS, "Harmonized BBSR target category counts failed")
    require(int(scalar(conn, f"SELECT COUNT(DISTINCT historical_bbsr_administrative_district_code) FROM {NEW_OBJECTS[1]}")) == 400, "Harmonized target code distinct count failed")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {NEW_OBJECTS[1]} WHERE historical_bbsr_settlement_type_code IS NULL")) == 0, "Harmonized layer has unclassified target rows")

    totals = query_dicts(conn, f"""
        SELECT
            SUM(equipment_count) AS equipment,
            SUM(charging_point_count) AS points,
            SUM(normal_charging_point_count) AS normal_points,
            SUM(fast_charging_point_count) AS fast_points,
            SUM(points_ge_150_kw) AS points_ge_150,
            SUM(points_ge_350_kw) AS points_ge_350,
            SUM(unclassifiable_power_point_count) AS unclassifiable_points,
            SUM(total_equipment_nominal_power_kw) AS nominal_power_kw,
            SUM(source_component_count) AS source_components
        FROM {NEW_OBJECTS[1]}
    """)[0]
    actual_totals = {
        key: int(totals[key])
        for key in ("equipment", "points", "normal_points", "fast_points", "points_ge_150", "points_ge_350", "unclassifiable_points", "source_components")
    }
    require(actual_totals == {
        "equipment": EXPECTED["equipment"],
        "points": EXPECTED["points"],
        "normal_points": EXPECTED["normal_points"],
        "fast_points": EXPECTED["fast_points"],
        "points_ge_150": EXPECTED["points_ge_150"],
        "points_ge_350": EXPECTED["points_ge_350"],
        "unclassifiable_points": EXPECTED["unclassifiable_points"],
        "source_components": EXPECTED["bnetza_geographies"],
    }, f"Harmonized national totals failed: {actual_totals}")
    nominal_mw = float(totals["nominal_power_kw"]) / 1000.0
    require(abs(nominal_mw - EXPECTED_NOMINAL_POWER_MW) < 0.00001, "Harmonized nominal power total failed")
    require(actual_totals["normal_points"] + actual_totals["fast_points"] + actual_totals["unclassifiable_points"] == actual_totals["points"], "Harmonized point classes do not reconcile")

    mkk = query_dicts(conn, f"""
        SELECT historical_bbsr_administrative_district_code,
               historical_bbsr_administrative_district_name,
               historical_bbsr_settlement_type_code,
               source_component_count,
               source_component_names,
               equipment_count,
               charging_point_count
        FROM {NEW_OBJECTS[1]}
        WHERE historical_bbsr_administrative_district_code = '06435000'
    """)
    require(len(mkk) == 1, "Historical Main-Kinzig target is not unique")
    require((mkk[0]["source_component_count"], mkk[0]["equipment_count"], mkk[0]["charging_point_count"]) == (2, 585, 991), "Hanau/Main-Kinzig harmonized totals failed")
    require("Kreisfreie Stadt Hanau" in mkk[0]["source_component_names"] and "Landkreis Main-Kinzig-Kreis" in mkk[0]["source_component_names"], "Historical Main-Kinzig source components are incomplete")
    require(mkk[0]["historical_bbsr_settlement_type_code"] == "2", "Historical Main-Kinzig BBSR type changed")

    kassel = query_dicts(conn, f"""
        SELECT historical_bbsr_administrative_district_code,
               historical_bbsr_administrative_district_name,
               historical_bbsr_settlement_type_code,
               source_component_names,
               equipment_count,
               charging_point_count
        FROM {NEW_OBJECTS[1]}
        WHERE historical_bbsr_administrative_district_code IN ('06611000', '06633000')
        ORDER BY historical_bbsr_administrative_district_code
    """)
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {NEW_OBJECTS[0]} WHERE bnetza_district_name IN ('Kreisfreie Stadt Kassel', 'Landkreis Kassel')")) == 2, "Kassel source rows missing from harmonization table")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {NEW_OBJECTS[1]} WHERE historical_bbsr_administrative_district_code = '06611000'")) == 1, "Kassel city historical target missing")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {NEW_OBJECTS[1]} WHERE historical_bbsr_administrative_district_code = '06633000'")) == 1, "Kassel county historical target missing")
    require(set((row["historical_bbsr_administrative_district_code"], row["historical_bbsr_settlement_type_code"]) for row in kassel) == {("06611000", "1"), ("06633000", "2")}, "Kassel historical target/type correction failed")

    summary = query_dicts(conn, f"SELECT * FROM {NEW_OBJECTS[2]} ORDER BY settlement_type_code")
    require([row["settlement_type_code"] for row in summary] == ["1", "2", "3", "4"], "Harmonized type summary codes failed")
    require(sum(int(row["charging_point_count"]) for row in summary) == EXPECTED["points"], "Harmonized type summary points do not reconcile")
    require(sum(float(row["national_charging_point_share_pct"]) for row in summary) >= 99.999999, "Harmonized type national shares do not reconcile")
    require(all(row["classification_scope"] == "HISTORICAL_BBSR_2025_TARGET_UNITS_FROM_BNETZA_2026_SOURCE" for row in summary), "Harmonized classification scope changed")
    require(all(row["point_share_denominator_scope"] == "ALL_REGISTERED_CHARGING_POINTS_INCLUDING_ALL_HISTORICAL_TARGET_UNITS" for row in summary), "Harmonized denominator scope changed")

    for name in NEW_OBJECTS[1:]:
        sql = (view_sql(conn, name) or "").lower()
        for forbidden in ("kba", "bev_stock", "phev", "kba_district_ev_stock"):
            require(forbidden not in sql, f"New view {name} unexpectedly references {forbidden}")
    assert_existing_unchanged(conn, baseline)
    return {
        "new_objects": {name: object_snapshot(conn, name) for name in NEW_OBJECTS},
        "target_category_counts": EXPECTED_TYPE_COUNTS,
        "national_totals": {**actual_totals, "nominal_power_mw": nominal_mw},
        "hanau_main_kinzig_target": mkk[0],
        "kassel_targets": kassel,
        "protected_objects_unchanged": True,
    }


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Batch 13.2 historical BBSR Hanau harmonization")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--bbsr", type=Path, default=DEFAULT_BBSR)
    parser.add_argument("--bbsr-workbook", type=Path, default=DEFAULT_BBSR_WORKBOOK)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--bridge", type=Path, default=DEFAULT_BRIDGE)
    parser.add_argument("--sql", type=Path, default=DEFAULT_SQL)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--backup-path", type=Path)
    parser.add_argument("--build-reference-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    database = resolve_path(args.database)
    bbsr_path = resolve_path(args.bbsr)
    bbsr_workbook_path = resolve_path(args.bbsr_workbook)
    reference_path = resolve_path(args.reference)
    manifest_path = resolve_path(args.manifest)
    bridge_path = resolve_path(args.bridge)
    sql_path = resolve_path(args.sql)
    backup_dir = resolve_path(args.backup_dir)
    backup_path = resolve_path(args.backup_path) if args.backup_path else None

    try:
        require(database.is_file(), f"Missing DuckDB database: {database}")
        require(sha256(bbsr_path) == BBSR_SOURCE_SHA256, "BBSR derived CSV checksum changed")
        require(sha256(bbsr_workbook_path) == RAW_BBSR_SHA256, "BBSR raw workbook checksum changed")
        sql_audit = validate_sql_source(sql_path, reference_path)
        conn = duckdb.connect(str(database), read_only=True)
        try:
            rows, audit = build_reference_rows(bbsr_path, bbsr_workbook_path, bridge_path, conn)
            baseline = baseline_state(conn)
        finally:
            conn.close()
        write_or_validate_reference(reference_path, rows)
        write_or_validate_manifest(manifest_path, reference_path, bbsr_path, bbsr_workbook_path, sql_path, audit)

        result: dict[str, Any] = {
            "status": "PASS",
            "batch": "13.2",
            "harmonization_version": HARMONIZATION_VERSION,
            "reference": {
                "path": str(reference_path),
                "sha256": sha256(reference_path),
                "manifest": str(manifest_path),
            },
            "audit": audit,
            "sql": sql_audit,
            "baseline": baseline["metrics"],
        }

        if args.build_reference_only:
            result["mode"] = "build_reference_only"
            print(json.dumps(json_safe(result), ensure_ascii=False, indent=2, sort_keys=True) if args.json else "PASS: Batch 13.2 reference built and validated")
            return 0

        present = []
        conn = duckdb.connect(str(database), read_only=True)
        try:
            present = [name for name in NEW_OBJECTS if object_type(conn, name) is not None]
        finally:
            conn.close()
        require(not present or len(present) == len(NEW_OBJECTS), f"Batch 13.2 objects are partially deployed: {present}")

        if args.dry_run:
            result["mode"] = "dry_run"
            if len(present) == len(NEW_OBJECTS):
                conn = duckdb.connect(str(database), read_only=True)
                try:
                    result["existing_new_layer"] = validate_new_layer(conn, rows, baseline)
                finally:
                    conn.close()
            else:
                result["existing_new_layer"] = "not_yet_deployed"
            print(json.dumps(json_safe(result), ensure_ascii=False, indent=2, sort_keys=True) if args.json else "PASS: Batch 13.2 preflight is ready")
            return 0

        if backup_path is None:
            backup_evidence = create_backup(database, backup_dir, baseline)
        else:
            backup_evidence = validate_backup(backup_path, baseline)
        result["backup"] = backup_evidence

        no_open_database_handles(database)
        writer = duckdb.connect(str(database), read_only=False)
        try:
            deploy_sql(writer, sql_path, reference_path)
        finally:
            writer.close()

        conn = duckdb.connect(str(database), read_only=True)
        try:
            post_baseline = baseline_state(conn)
            require(post_baseline["metrics"] == baseline["metrics"], "Core baseline changed during deployment")
            result["deployed_layer"] = validate_new_layer(conn, rows, baseline)
        finally:
            conn.close()
        result["mode"] = "deploy"
        print(json.dumps(json_safe(result), ensure_ascii=False, indent=2, sort_keys=True) if args.json else "PASS: Batch 13.2 historical BBSR harmonization deployed")
        return 0
    except (DeploymentError, OSError, duckdb.Error, ValueError) as exc:
        payload = {"status": "FAIL", "batch": "13.2", "error": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) if args.json else f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
