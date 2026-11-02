#!/usr/bin/env python3
"""Deploy the Batch 13 BBSR charging-only analytical layer.

The script builds a deterministic BNetzA-source-grain bridge from the local
Batch 12 Path A evidence and the preserved BBSR 2025 reference.  It validates
the source and existing KBA layer read-only, verifies or creates a timestamped
DuckDB backup, then deploys only the new BBSR reference table and charging
analytics views in one transaction.

No KBA vehicle stock is read by the generated BBSR views.  The existing KBA
Crosswalk and KBA analytics objects are treated as integrity baselines and
must remain byte-for-byte equivalent at the SQL/data snapshot level.

Run from the repository root:

    .venv/bin/python scripts/13_deploy_bbsr_charging_layer.py --json

For a repeat-safe execution against an already verified backup, pass the
backup explicitly with ``--backup-path``.
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
import unicodedata
from collections import Counter
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_BBSR = ROOT / "data/reference/bbsr_settlement_types_2025.csv"
DEFAULT_BBSR_MANIFEST = ROOT / "data/reference/bbsr_source_manifest.json"
DEFAULT_PATH_AUDIT = ROOT / "reports/batch12_bbsr_integration_paths_audit.csv"
DEFAULT_BRIDGE = ROOT / "data/reference/bnetza_bbsr_bridge_2025.csv"
DEFAULT_BRIDGE_MANIFEST = ROOT / "data/reference/bnetza_bbsr_bridge_2025_manifest.json"
DEFAULT_SQL = ROOT / "sql/13_bbsr_charging_layer.sql"
DEFAULT_BACKUP_DIR = ROOT / "data/backups"

SOURCE_ID = "bnetza_charging_2026_09_30"
BNETZA_REFERENCE_DATE = dt.date(2026, 9, 30)
BBSR_REFERENCE_DATE = dt.date(2025, 12, 31)
BRIDGE_VERSION = "batch13-2026-11-02-path-a-bbsr-2025"
EXPECTED_AUDIT_VERSION = "batch12-2026-11-02-two-path-strict-evidence"
BBSR_SOURCE_VERSION = (
    "raumgliederungen-referenzen-2025.xlsx | Kreisreferenz | "
    "geographic stand 2025-12-31"
)

BBSR_TYPE_LABELS = {
    "1": "kreisfreie Großstadt",
    "2": "städtischer Kreis",
    "3": "ländlicher Kreis mit Verdichtungsansätzen",
    "4": "dünn besiedelter ländlicher Kreis",
}
BBSR_TYPE_CODES = tuple(BBSR_TYPE_LABELS)
STATUS_CODES = ("VERIFIED_COMPATIBLE", "CONDITIONAL_VINTAGE", "UNRESOLVED")

EXPECTED = {
    "equipment": 117_662,
    "points": 211_253,
    "bnetza_geographies": 401,
    "kba_reference_rows": 401,
    "kba_regional_rows": 400,
    "kba_combined_rows": 1_200,
    "bbsr_rows": 400,
    "bbsr_kreisregions": 362,
    "normal_points": 156_155,
    "fast_points": 55_098,
    "points_ge_150": 40_950,
    "points_ge_350": 6_950,
    "unclassifiable_points": 0,
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

BRIDGE_COLUMNS = (
    "bridge_version",
    "source_audit_version",
    "source_audit_sha256",
    "bnetza_source_id",
    "bnetza_reference_date",
    "bnetza_state_name",
    "bnetza_district_name",
    "bnetza_admin_type",
    "bbsr_reference_date",
    "bbsr_source_version",
    "bbsr_source_sha256",
    "bbsr_administrative_district_code",
    "bbsr_administrative_district_name",
    "bbsr_federal_state_code",
    "bbsr_federal_state_name",
    "bbsr_kreisregion_code",
    "bbsr_kreisregion_name",
    "bbsr_settlement_type_code",
    "bbsr_settlement_type_name_de",
    "geographic_compatibility_status",
    "evidence_method",
    "evidence_source_reference",
    "validation_notes",
)

AUDIT_REQUIRED_COLUMNS = {
    "audit_output_scope",
    "audit_version",
    "path",
    "source_record_key",
    "bnetza_state_name",
    "bnetza_district_name",
    "bnetza_admin_type",
    "bbsr_candidate_codes",
    "bbsr_candidate_names",
    "bbsr_candidate_types",
    "bbsr_candidate_kreisregion_codes",
    "bbsr_candidate_kreisregion_names",
    "bbsr_candidate_count",
    "candidate_resolution",
    "audit_status",
    "audit_reason",
    "equipment_rows",
    "charging_point_total",
}

EXISTING_KBA_OBJECTS = (
    "reference.bnetza_kba_district_crosswalk_2026",
    "analytics.charging_by_kba_district_2026_09_30",
    "analytics.kba_district_charging_vs_bev_2026",
    "analytics.charging_by_state",
)

MAX_POWER_SQL = """
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
WHERE core.charging_point.source_id = 'bnetza_charging_2026_09_30'
"""


class DeploymentError(RuntimeError):
    """Raised when a safe Batch 13 deployment cannot proceed."""


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


def query_dicts(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    result = conn.execute(sql)
    names = [item[0] for item in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def normalise_text(value: str) -> str:
    text = (value or "").upper()
    text = (
        text.replace("Ä", "AE")
        .replace("Ö", "OE")
        .replace("Ü", "UE")
        .replace("ẞ", "SS")
        .replace("ß", "SS")
    )
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", text)).strip()


def administrative_identity_key(value: str) -> str:
    text = normalise_text(value)
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


def bbsr_admin_form(value: str) -> str:
    text = normalise_text(value)
    if "LANDKREIS" in text:
        return "county"
    city_tokens = (
        "KREISFREIESTADT",
        "STADTKREIS",
        "LANDESHAUPTSTADT",
        "HANSESTADT",
        "WISSENSCHAFTSSTADT",
        "KLINGENSTADT",
        "FERNUNIVERSITAET",
    )
    if any(token in text for token in city_tokens) or re.search(r"(?:^| )STADT(?:$| )", text):
        return "city"
    return "unknown"


def source_admin_type(value: str) -> str:
    text = normalise_text(value)
    if text.startswith("KREISFREIE STADT ") or text.startswith("STADTKREIS "):
        return "city"
    if text.startswith("LANDKREIS ") or text.startswith("KREIS "):
        return "county"
    raise DeploymentError(f"Cannot derive BNetzA administrative form from {value!r}")


def bbsr_type_compatible(row: Mapping[str, str], source_admin_type: str) -> bool:
    observed = bbsr_admin_form(row["administrative_district_name"])
    return observed == "unknown" or observed == source_admin_type


def read_csv_rows(path: Path, expected_columns: Sequence[str]) -> list[dict[str, str]]:
    require(path.is_file(), f"Missing CSV source: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(
            tuple(reader.fieldnames or ()) == tuple(expected_columns),
            f"Unexpected CSV schema in {path}: {reader.fieldnames}",
        )
        return [dict(row) for row in reader]


def load_bbsr(path: Path) -> tuple[list[dict[str, str]], dict[tuple[str, str], list[dict[str, str]]]]:
    rows = read_csv_rows(path, BBSR_COLUMNS)
    require(len(rows) == EXPECTED["bbsr_rows"], f"BBSR rows: {len(rows)}")
    require(
        all(row["source_version"] == BBSR_SOURCE_VERSION for row in rows),
        "BBSR source version changed",
    )
    require(
        all(row["bbsr_reference_date"] == BBSR_REFERENCE_DATE.isoformat() for row in rows),
        "BBSR reference date changed",
    )
    codes = [row["administrative_district_code"] for row in rows]
    require(all(re.fullmatch(r"[0-9]{8}", code or "") for code in codes), "Invalid BBSR administrative code")
    require(len(set(codes)) == len(codes), "Duplicate BBSR administrative code")
    require(
        all(row["settlement_type_code"] in BBSR_TYPE_CODES for row in rows),
        "Invalid BBSR settlement type code",
    )
    require(
        all(BBSR_TYPE_LABELS[row["settlement_type_code"]] == row["settlement_type_name_de"] for row in rows),
        "BBSR settlement type label mismatch",
    )
    require(
        len({row["kreisregion_code"] for row in rows}) == EXPECTED["bbsr_kreisregions"],
        "Unexpected BBSR Kreisregion count",
    )
    by_identity: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (
            row["federal_state_name"],
            administrative_identity_key(row["administrative_district_name"]),
        )
        by_identity.setdefault(key, []).append(row)
    return rows, by_identity


def load_path_a_audit(path: Path) -> dict[str, dict[str, str]]:
    require(path.is_file(), f"Missing Batch 12 audit: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or ())
        require(AUDIT_REQUIRED_COLUMNS <= fields, "Batch 12 audit schema is incomplete")
        rows = [dict(row) for row in reader]
    require(len(rows) == 801, f"Batch 12 audit row count changed: {len(rows)}")
    path_a = [row for row in rows if row["path"] == "PATH_A"]
    require(len(path_a) == EXPECTED["bnetza_geographies"], "Batch 12 Path A row count changed")
    require(all(row["audit_version"] == EXPECTED_AUDIT_VERSION for row in path_a), "Batch 12 audit version changed")
    keys = [row["source_record_key"] for row in path_a]
    require(len(set(keys)) == len(keys), "Duplicate Batch 12 Path A source key")
    counts = Counter(row["audit_status"] for row in path_a)
    require(
        counts == Counter({"VERIFIED_COMPATIBLE": 399, "CONDITIONAL_VINTAGE": 1, "UNRESOLVED": 1}),
        f"Unexpected Batch 12 Path A statuses: {counts}",
    )
    return {row["source_record_key"]: row for row in path_a}


def source_rows(conn: duckdb.DuckDBPyConnection) -> dict[tuple[str, str], dict[str, Any]]:
    rows = query_dicts(
        conn,
        """
        WITH equipment AS (
            SELECT
                state_name AS bnetza_state_name,
                district_name AS bnetza_district_name,
                COUNT(*) AS equipment_rows,
                SUM(declared_point_count) AS declared_point_count
            FROM core.charging_equipment
            WHERE source_id = 'bnetza_charging_2026_09_30'
            GROUP BY state_name, district_name
        ), points AS (
            SELECT
                e.state_name AS bnetza_state_name,
                e.district_name AS bnetza_district_name,
                COUNT(*) AS charging_point_count
            FROM core.charging_point p
            INNER JOIN core.charging_equipment e
              ON e.source_id = p.source_id
             AND e.excel_row = p.equipment_excel_row
            WHERE p.source_id = 'bnetza_charging_2026_09_30'
            GROUP BY e.state_name, e.district_name
        )
        SELECT
            e.bnetza_state_name,
            e.bnetza_district_name,
            e.equipment_rows,
            e.declared_point_count,
            p.charging_point_count
        FROM equipment e
        INNER JOIN points p USING (bnetza_state_name, bnetza_district_name)
        ORDER BY e.bnetza_state_name, e.bnetza_district_name
        """,
    )
    require(len(rows) == EXPECTED["bnetza_geographies"], f"BNetzA source geography rows: {len(rows)}")
    result = {
        (row["bnetza_state_name"], row["bnetza_district_name"]): row
        for row in rows
    }
    require(len(result) == len(rows), "Duplicate BNetzA source geography")
    require(sum(int(row["equipment_rows"]) for row in rows) == EXPECTED["equipment"], "Source equipment does not reconcile")
    require(sum(int(row["charging_point_count"]) for row in rows) == EXPECTED["points"], "Source points do not reconcile")
    return result


def bbsr_candidate(
    state: str,
    district: str,
    admin_type: str,
    by_identity: Mapping[tuple[str, str], list[dict[str, str]]],
) -> list[dict[str, str]]:
    direct = list(by_identity.get((state, administrative_identity_key(district)), []))
    direct = [row for row in direct if bbsr_type_compatible(row, admin_type)]
    if len(direct) <= 1:
        return direct
    typed = [
        row for row in direct
        if bbsr_admin_form(row["administrative_district_name"]) == admin_type
    ]
    if len(typed) == 1:
        return typed
    if admin_type == "city":
        weak = [
            row for row in direct
            if bbsr_admin_form(row["administrative_district_name"]) != "county"
        ]
    else:
        weak = [
            row for row in direct
            if bbsr_admin_form(row["administrative_district_name"]) != "city"
        ]
    return weak if len(weak) == 1 else []


def bridge_records(
    conn: duckdb.DuckDBPyConnection,
    bbsr_path: Path,
    audit_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bbsr_rows, by_identity = load_bbsr(bbsr_path)
    audit_by_key = load_path_a_audit(audit_path)
    source = source_rows(conn)
    audit_hash = sha256(audit_path)
    bbsr_hash = sha256(bbsr_path)
    source_version = bbsr_rows[0]["source_version"]
    evidence_reference = (
        "reports/batch12_bbsr_integration_paths_audit.csv (PATH_A); "
        "data/reference/bbsr_settlement_types_2025.csv; "
        "data/reference/bbsr_source_manifest.json"
    )
    result: list[dict[str, Any]] = []

    for key in sorted(source):
        state, district = key
        audit = audit_by_key.get(f"{state}|{district}")
        require(audit is not None, f"Batch 12 Path A evidence missing for {state}|{district}")
        admin_type = source_admin_type(district)
        require(audit["bnetza_admin_type"] == admin_type, f"Admin type changed for {state}|{district}")
        candidates = bbsr_candidate(state, district, admin_type, by_identity)
        is_hanau = district == "Kreisfreie Stadt Hanau"
        is_main_kinzig = district == "Landkreis Main-Kinzig-Kreis"

        if is_hanau:
            require(not candidates, "Hanau unexpectedly resolved to a BBSR 2025 row")
            expected_status = "UNRESOLVED"
        elif is_main_kinzig:
            require(len(candidates) == 1, "Main-Kinzig direct BBSR candidate is not unique")
            expected_status = "CONDITIONAL_VINTAGE"
        else:
            require(len(candidates) == 1, f"BBSR direct identity is not unique for {state}|{district}")
            expected_status = "VERIFIED_COMPATIBLE"

        require(audit["audit_status"] == expected_status, f"Batch 12 status changed for {state}|{district}")
        if candidates:
            candidate = candidates[0]
            require(
                audit["bbsr_candidate_codes"] == candidate["administrative_district_code"],
                f"Batch 12 BBSR candidate changed for {state}|{district}",
            )
            require(
                audit["bbsr_candidate_kreisregion_codes"] == candidate["kreisregion_code"],
                f"Batch 12 Kreisregion candidate changed for {state}|{district}",
            )
        else:
            candidate = None
            require(not audit["bbsr_candidate_codes"], f"Unexpected Hanau BBSR candidate in audit")

        # Main-Kinzig's pre-separation BBSR row is retained as evidence, but
        # its type is intentionally withheld from charging-only categories.
        classified_candidate = candidate if expected_status == "VERIFIED_COMPATIBLE" else None
        if candidate:
            bbsr_code = candidate["administrative_district_code"]
            bbsr_name = candidate["administrative_district_name"]
            bbsr_state_code = candidate["federal_state_code"]
            bbsr_state_name = candidate["federal_state_name"]
            kreisregion_code = candidate["kreisregion_code"]
            kreisregion_name = candidate["kreisregion_name"]
        else:
            bbsr_code = bbsr_name = bbsr_state_code = bbsr_state_name = None
            kreisregion_code = kreisregion_name = None

        if classified_candidate:
            type_code = classified_candidate["settlement_type_code"]
            type_name = classified_candidate["settlement_type_name_de"]
        else:
            type_code = type_name = None

        if expected_status == "VERIFIED_COMPATIBLE":
            evidence_method = "direct_state_admin_type_name_identity"
            notes = (
                "Unique state + administrative-form + normalized administrative identity; "
                "no KBA code used as assignment proof; BNetzA 2026-09-30 versus "
                "BBSR geographic stand 2025-12-31."
            )
        elif expected_status == "CONDITIONAL_VINTAGE":
            evidence_method = "direct_state_admin_type_name_identity_conditional_vintage"
            notes = (
                "BBSR Main-Kinzig row retained as pre-change identity evidence; "
                "settlement type intentionally NULL because the BBSR 2025 row predates "
                "Hanau's 2026-01-01 separation; no exact current type asserted."
            )
        else:
            evidence_method = "unresolved_source_identity_missing_bbsr_2025_component"
            notes = (
                "BBSR 2025 has no Hanau administrative row after the 2026 separation; "
                "BBSR fields are NULL and no type is inherited from Main-Kinzig-Kreis."
            )

        if district in {"Kreisfreie Stadt Trier", "Landkreis Trier-Saarburg"}:
            notes += " Trier city and county remain separate source rows; no KBA stock is joined or allocated."

        result.append(
            {
                "bridge_version": BRIDGE_VERSION,
                "source_audit_version": audit["audit_version"],
                "source_audit_sha256": audit_hash,
                "bnetza_source_id": SOURCE_ID,
                "bnetza_reference_date": BNETZA_REFERENCE_DATE.isoformat(),
                "bnetza_state_name": state,
                "bnetza_district_name": district,
                "bnetza_admin_type": admin_type,
                "bbsr_reference_date": BBSR_REFERENCE_DATE.isoformat(),
                "bbsr_source_version": source_version,
                "bbsr_source_sha256": bbsr_hash,
                "bbsr_administrative_district_code": bbsr_code,
                "bbsr_administrative_district_name": bbsr_name,
                "bbsr_federal_state_code": bbsr_state_code,
                "bbsr_federal_state_name": bbsr_state_name,
                "bbsr_kreisregion_code": kreisregion_code,
                "bbsr_kreisregion_name": kreisregion_name,
                "bbsr_settlement_type_code": type_code,
                "bbsr_settlement_type_name_de": type_name,
                "geographic_compatibility_status": expected_status,
                "evidence_method": evidence_method,
                "evidence_source_reference": evidence_reference,
                "validation_notes": notes,
            }
        )

    require(len(result) == EXPECTED["bnetza_geographies"], "Bridge row count failed")
    require(
        len({(row["bnetza_state_name"], row["bnetza_district_name"]) for row in result})
        == EXPECTED["bnetza_geographies"],
        "Bridge source key uniqueness failed",
    )
    require(Counter(row["geographic_compatibility_status"] for row in result) == Counter({
        "VERIFIED_COMPATIBLE": 399,
        "CONDITIONAL_VINTAGE": 1,
        "UNRESOLVED": 1,
    }), "Bridge status counts failed")
    require(sum(row["bbsr_settlement_type_code"] is not None for row in result) == 399, "Classifiable bridge count failed")
    require(
        all(
            row["bbsr_settlement_type_code"] in BBSR_TYPE_CODES
            and row["bbsr_settlement_type_name_de"] == BBSR_TYPE_LABELS[row["bbsr_settlement_type_code"]]
            for row in result
            if row["bbsr_settlement_type_code"] is not None
        ),
        "Bridge classification domain failed",
    )
    for row in result:
        if row["bbsr_settlement_type_code"] is None:
            require(row["bbsr_settlement_type_name_de"] is None, "Null bridge type has a non-null name")
    return result, {
        "source_audit_version": EXPECTED_AUDIT_VERSION,
        "source_audit_sha256": audit_hash,
        "bbsr_csv_sha256": bbsr_hash,
        "bbsr_source_version": source_version,
        "status_counts": dict(sorted(Counter(row["geographic_compatibility_status"] for row in result).items())),
        "classifiable_districts": 399,
        "unclassified_source_keys": [
            f"{row['bnetza_state_name']}|{row['bnetza_district_name']}"
            for row in result
            if row["bbsr_settlement_type_code"] is None
        ],
    }


def serialized_bridge_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            column: "" if row.get(column) is None else str(row.get(column))
            for column in BRIDGE_COLUMNS
        }
        for row in rows
    ]


def write_or_validate_bridge(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    expected_rows = serialized_bridge_rows(rows)
    if path.exists():
        actual_rows = read_csv_rows(path, BRIDGE_COLUMNS)
        require(actual_rows == expected_rows, f"Existing bridge differs from reproducible evidence: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BRIDGE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(expected_rows)


def write_or_validate_manifest(
    path: Path,
    bridge_path: Path,
    bbsr_path: Path,
    bbsr_manifest_path: Path,
    audit_path: Path,
    bridge_info: Mapping[str, Any],
) -> None:
    manifest = {
        "manifest_version": 1,
        "bridge_version": BRIDGE_VERSION,
        "bridge_file": str(bridge_path.relative_to(ROOT)),
        "bridge_sha256": sha256(bridge_path),
        "source_audit": {
            "path": str(audit_path.relative_to(ROOT)),
            "sha256": bridge_info["source_audit_sha256"],
            "version": bridge_info["source_audit_version"],
            "scope": "Batch 12 PATH_A only",
        },
        "bbsr_reference": {
            "path": str(bbsr_path.relative_to(ROOT)),
            "sha256": bridge_info["bbsr_csv_sha256"],
            "source_version": bridge_info["bbsr_source_version"],
            "reference_date": BBSR_REFERENCE_DATE.isoformat(),
        },
        "bbsr_source_manifest_sha256": sha256(bbsr_manifest_path),
        "rules": {
            "grain": "one original BNetzA state/district combination",
            "assignment_basis": "direct state + administrative form + normalized administrative identity",
            "kba_code_used_as_assignment_proof": False,
            "main_kinzig_settlement_type": None,
            "hanau_settlement_type": None,
            "trier_stock_allocated": False,
        },
        "validation": {
            "source_rows": EXPECTED["bnetza_geographies"],
            "verified_compatible_rows": 399,
            "conditional_vintage_rows": 1,
            "unresolved_rows": 1,
            "classifiable_rows": bridge_info["classifiable_districts"],
            "unclassified_source_keys": bridge_info["unclassified_source_keys"],
        },
    }
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        require(path.read_text(encoding="utf-8") == serialized, f"Existing bridge manifest differs: {path}")
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
    equipment = int(scalar(conn, "SELECT COUNT(*) FROM core.charging_equipment"))
    points = int(scalar(conn, "SELECT COUNT(*) FROM core.charging_point"))
    geographies = int(scalar(conn, "SELECT COUNT(*) FROM (SELECT DISTINCT state_name, district_name FROM core.charging_equipment)"))
    declared = int(scalar(conn, "SELECT SUM(declared_point_count) FROM core.charging_equipment"))
    nominal_mw = float(scalar(conn, "SELECT SUM(equipment_nominal_power_kw) / 1000.0 FROM core.charging_equipment"))
    power = tuple(int(value) for value in conn.execute(MAX_POWER_SQL).fetchone())
    require((equipment, points, geographies) == (EXPECTED["equipment"], EXPECTED["points"], EXPECTED["bnetza_geographies"]), "Core row baseline failed")
    require(declared == EXPECTED["points"], "Declared point total failed")
    require(abs(nominal_mw - EXPECTED_NOMINAL_POWER_MW) < 0.00001, "Nominal power baseline failed")
    require(power == (
        EXPECTED["points"],
        EXPECTED["normal_points"],
        EXPECTED["fast_points"],
        EXPECTED["points_ge_150"],
        EXPECTED["points_ge_350"],
        EXPECTED["unclassifiable_points"],
    ), f"Maximum-per-point power baseline failed: {power}")
    equipment_key_issues = int(scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT source_id, excel_row FROM core.charging_equipment
            GROUP BY source_id, excel_row HAVING COUNT(*) <> 1
        )
    """))
    point_key_issues = int(scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT source_id, equipment_excel_row, point_number FROM core.charging_point
            GROUP BY source_id, equipment_excel_row, point_number HAVING COUNT(*) <> 1
        )
    """))
    orphan_points = int(scalar(conn, """
        SELECT COUNT(*)
        FROM core.charging_point p
        LEFT JOIN core.charging_equipment e
          ON e.source_id = p.source_id AND e.excel_row = p.equipment_excel_row
        WHERE e.source_id IS NULL
    """))
    mismatches = int(scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT e.source_id, e.excel_row,
                   COALESCE(e.declared_point_count, 0) AS declared_points,
                   COUNT(p.point_number) AS actual_points
            FROM core.charging_equipment e
            LEFT JOIN core.charging_point p
              ON p.source_id = e.source_id AND p.equipment_excel_row = e.excel_row
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


def baseline_state(conn: duckdb.DuckDBPyConnection, bbsr_rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    metrics = core_metrics(conn)
    required_counts = {
        "reference.bnetza_kba_district_crosswalk_2026": EXPECTED["kba_reference_rows"],
        "analytics.charging_by_kba_district_2026_09_30": EXPECTED["kba_regional_rows"],
        "analytics.kba_district_charging_vs_bev_2026": EXPECTED["kba_combined_rows"],
    }
    for name, expected_count in required_counts.items():
        require(object_type(conn, name) in {"BASE TABLE", "VIEW"}, f"Existing KBA object missing: {name}")
        require(int(scalar(conn, f"SELECT COUNT(*) FROM {name}")) == expected_count, f"Existing KBA object count changed: {name}")
    require(object_type(conn, "analytics.charging_by_state") == "VIEW", "Existing state view missing")
    require(int(scalar(conn, "SELECT COUNT(*) FROM analytics.charging_by_state")) == 16, "Existing state view count changed")
    require(len(bbsr_rows) == EXPECTED["bbsr_rows"], "BBSR source count failed")
    require(len({row["kreisregion_code"] for row in bbsr_rows}) == EXPECTED["bbsr_kreisregions"], "BBSR Kreisregion baseline failed")
    existing = {name: object_snapshot(conn, name) for name in EXISTING_KBA_OBJECTS}
    return {"metrics": metrics, "existing_objects": existing}


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


def validate_backup(path: Path, expected_metrics: Mapping[str, Any]) -> dict[str, Any]:
    require(path.is_file(), f"Missing verified backup: {path}")
    require(path.resolve() != DEFAULT_DATABASE.resolve(), "Backup path equals primary database")
    require(not Path(str(path) + ".wal").exists(), f"Backup WAL exists: {path}.wal")
    conn = duckdb.connect(str(path), read_only=True)
    try:
        actual = core_metrics(conn)
    finally:
        conn.close()
    for key in (
        "equipment",
        "points",
        "bnetza_geographies",
        "declared_points",
        "normal_points",
        "fast_points",
        "points_ge_150",
        "points_ge_350",
        "unclassifiable_points",
    ):
        require(actual[key] == expected_metrics[key], f"Backup baseline differs for {key}")
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "validated_read_only": True,
        "metrics": actual,
    }


def create_backup(database: Path, backup_dir: Path, expected_metrics: Mapping[str, Any]) -> dict[str, Any]:
    require(database.is_file(), f"Missing database: {database}")
    no_open_database_handles(database)
    wal = Path(str(database) + ".wal")
    require(not wal.exists(), f"Refusing to copy while a WAL exists: {wal}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"ev_charging_pre_batch13_{timestamp}.duckdb"
    require(not backup.exists(), f"Backup target already exists: {backup}")
    source_size_before = database.stat().st_size
    source_hash_before = sha256(database)
    shutil.copy2(database, backup)
    source_size_after = database.stat().st_size
    source_hash_after = sha256(database)
    require((source_size_before, source_hash_before) == (source_size_after, source_hash_after), "Database changed during backup")
    require(sha256(backup) == source_hash_after, "Backup checksum differs from source")
    evidence = validate_backup(backup, expected_metrics)
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


def render_sql(sql: str, bridge_path: Path) -> str:
    replacements = {
        "{{BRIDGE_CSV}}": sql_literal(str(bridge_path.resolve())),
        "{{BRIDGE_VERSION}}": BRIDGE_VERSION,
        "{{SOURCE_ID}}": SOURCE_ID,
        "{{BNETZA_DATE}}": BNETZA_REFERENCE_DATE.isoformat(),
        "{{BBSR_DATE}}": BBSR_REFERENCE_DATE.isoformat(),
    }
    for token, value in replacements.items():
        sql = sql.replace(token, value)
    return sql


def bridge_row_values(row: Mapping[str, Any]) -> tuple[Any, ...]:
    date_fields = {"bnetza_reference_date", "bbsr_reference_date"}
    values: list[Any] = []
    for column in BRIDGE_COLUMNS:
        value = row.get(column)
        if value is None or value == "":
            values.append(None)
        elif column in date_fields:
            values.append(dt.date.fromisoformat(str(value)))
        else:
            values.append(value)
    return tuple(values)


def create_expected_bridge(conn: duckdb.DuckDBPyConnection, rows: Sequence[Mapping[str, Any]]) -> None:
    conn.execute("DROP TABLE IF EXISTS batch13_expected_bridge")
    conn.execute("""
        CREATE TEMP TABLE batch13_expected_bridge (
            bridge_version VARCHAR,
            source_audit_version VARCHAR,
            source_audit_sha256 VARCHAR,
            bnetza_source_id VARCHAR,
            bnetza_reference_date DATE,
            bnetza_state_name VARCHAR,
            bnetza_district_name VARCHAR,
            bnetza_admin_type VARCHAR,
            bbsr_reference_date DATE,
            bbsr_source_version VARCHAR,
            bbsr_source_sha256 VARCHAR,
            bbsr_administrative_district_code VARCHAR,
            bbsr_administrative_district_name VARCHAR,
            bbsr_federal_state_code VARCHAR,
            bbsr_federal_state_name VARCHAR,
            bbsr_kreisregion_code VARCHAR,
            bbsr_kreisregion_name VARCHAR,
            bbsr_settlement_type_code VARCHAR,
            bbsr_settlement_type_name_de VARCHAR,
            geographic_compatibility_status VARCHAR,
            evidence_method VARCHAR,
            evidence_source_reference VARCHAR,
            validation_notes VARCHAR
        )
    """)
    conn.executemany(
        "INSERT INTO batch13_expected_bridge VALUES (" + ",".join("?" for _ in BRIDGE_COLUMNS) + ")",
        [bridge_row_values(row) for row in rows],
    )


def bridge_table_matches(conn: duckdb.DuckDBPyConnection, rows: Sequence[Mapping[str, Any]]) -> bool:
    if object_type(conn, "reference.bnetza_bbsr_district_bridge_2025") != "BASE TABLE":
        return False
    create_expected_bridge(conn, rows)
    columns = ", ".join(BRIDGE_COLUMNS)
    left = int(scalar(conn, f"SELECT COUNT(*) FROM (SELECT {columns} FROM reference.bnetza_bbsr_district_bridge_2025 EXCEPT ALL SELECT {columns} FROM batch13_expected_bridge)"))
    right = int(scalar(conn, f"SELECT COUNT(*) FROM (SELECT {columns} FROM batch13_expected_bridge EXCEPT ALL SELECT {columns} FROM reference.bnetza_bbsr_district_bridge_2025)"))
    return left == 0 and right == 0


def assert_existing_unchanged(conn: duckdb.DuckDBPyConnection, baseline: Mapping[str, Any]) -> None:
    for name, before in baseline["existing_objects"].items():
        after = object_snapshot(conn, name)
        require(after == before, f"Existing KBA object changed: {name}")


def validate_new_layer(
    conn: duckdb.DuckDBPyConnection,
    rows: Sequence[Mapping[str, Any]],
    baseline_metrics: Mapping[str, Any],
) -> dict[str, Any]:
    bridge_name = "reference.bnetza_bbsr_district_bridge_2025"
    district_name = "analytics.charging_by_bbsr_district_2025"
    type_name = "analytics.charging_by_bbsr_type_2025"
    require(object_type(conn, bridge_name) == "BASE TABLE", "BBSR bridge table was not deployed")
    require(object_type(conn, district_name) == "VIEW", "BBSR district view was not deployed")
    require(object_type(conn, type_name) == "VIEW", "BBSR type view was not deployed")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {bridge_name}")) == 401, "BBSR bridge row count failed")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {district_name}")) == 401, "BBSR district view row count failed")
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {type_name}")) == 5, "BBSR type view row count failed")

    bridge_statuses = query_dicts(conn, f"SELECT geographic_compatibility_status, COUNT(*) AS rows FROM {bridge_name} GROUP BY 1 ORDER BY 1")
    require(
        {row["geographic_compatibility_status"]: int(row["rows"]) for row in bridge_statuses}
        == {"CONDITIONAL_VINTAGE": 1, "UNRESOLVED": 1, "VERIFIED_COMPATIBLE": 399},
        "Deployed BBSR bridge statuses failed",
    )
    require(int(scalar(conn, f"SELECT COUNT(*) FROM {bridge_name} WHERE bbsr_settlement_type_code IS NOT NULL")) == 399, "Deployed classifiable count failed")
    require(
        int(scalar(conn, f"SELECT COUNT(*) FROM {bridge_name} WHERE bbsr_settlement_type_code IS NULL")) == 2,
        "Deployed unclassified count failed",
    )
    require(
        int(scalar(conn, f"SELECT COUNT(*) FROM {bridge_name} WHERE bbsr_settlement_type_code IS NOT NULL AND bbsr_settlement_type_code NOT IN ('1','2','3','4')")) == 0,
        "Invalid deployed BBSR type code",
    )
    require(
        int(scalar(conn, f"SELECT COUNT(*) FROM {bridge_name} WHERE bnetza_district_name IN ('Kreisfreie Stadt Hanau','Landkreis Main-Kinzig-Kreis') AND bbsr_settlement_type_code IS NOT NULL")) == 0,
        "Hanau/Main-Kinzig received an unintended BBSR type",
    )

    totals = query_dicts(conn, f"""
        SELECT
            SUM(equipment_count) AS equipment,
            SUM(charging_point_count) AS points,
            SUM(normal_charging_point_count) AS normal_points,
            SUM(fast_charging_point_count) AS fast_points,
            SUM(points_ge_150_kw) AS points_ge_150,
            SUM(points_ge_350_kw) AS points_ge_350,
            SUM(unclassifiable_power_point_count) AS unclassifiable_points,
            SUM(total_equipment_nominal_power_kw) AS nominal_power_kw
        FROM {district_name}
    """)[0]
    actual_totals = {
        key: int(totals[key])
        for key in ("equipment", "points", "normal_points", "fast_points", "points_ge_150", "points_ge_350", "unclassifiable_points")
    }
    require(
        actual_totals == {
            "equipment": EXPECTED["equipment"],
            "points": EXPECTED["points"],
            "normal_points": EXPECTED["normal_points"],
            "fast_points": EXPECTED["fast_points"],
            "points_ge_150": EXPECTED["points_ge_150"],
            "points_ge_350": EXPECTED["points_ge_350"],
            "unclassifiable_points": EXPECTED["unclassifiable_points"],
        },
        f"BBSR district charging totals failed: {actual_totals}",
    )
    require(actual_totals["normal_points"] + actual_totals["fast_points"] + actual_totals["unclassifiable_points"] == actual_totals["points"], "Point classifications do not reconcile")
    nominal_mw = float(totals["nominal_power_kw"]) / 1000.0
    require(abs(nominal_mw - EXPECTED_NOMINAL_POWER_MW) < 0.00001, "BBSR nominal power total failed")
    require(int(scalar(conn, f"SELECT COALESCE(SUM(equipment_count), 0) FROM {district_name} WHERE equipment_statuses_present = ''")) == 0, "Equipment statuses were dropped")

    summary_rows = query_dicts(conn, f"SELECT * FROM {type_name} ORDER BY settlement_type_code")
    summary_codes = [row["settlement_type_code"] for row in summary_rows]
    require(summary_codes == ["1", "2", "3", "4", "UNCLASSIFIED"], f"Unexpected BBSR category rows: {summary_codes}")
    summary_totals = {
        key: sum(int(row[key]) for row in summary_rows)
        for key in ("equipment_count", "charging_point_count", "normal_charging_point_count", "fast_charging_point_count", "points_ge_150_kw", "points_ge_350_kw", "unclassifiable_power_point_count")
    }
    require(summary_totals["equipment_count"] == EXPECTED["equipment"], "Category equipment totals do not reconcile")
    require(summary_totals["charging_point_count"] == EXPECTED["points"], "Category point totals do not reconcile")
    require(summary_totals["normal_charging_point_count"] == EXPECTED["normal_points"], "Category normal totals do not reconcile")
    require(summary_totals["fast_charging_point_count"] == EXPECTED["fast_points"], "Category fast totals do not reconcile")
    require(summary_totals["points_ge_150_kw"] == EXPECTED["points_ge_150"], "Category >=150 totals do not reconcile")
    require(summary_totals["points_ge_350_kw"] == EXPECTED["points_ge_350"], "Category >=350 totals do not reconcile")
    require(summary_totals["unclassifiable_power_point_count"] == 0, "Category unclassifiable totals do not reconcile")
    require(abs(sum(float(row["share_of_all_registered_charging_points_pct"]) for row in summary_rows) - 100.0) < 0.0001, "Category national share does not sum to 100%")
    require(all(row["point_share_denominator_scope"] == "ALL_REGISTERED_CHARGING_POINTS_INCLUDING_UNCLASSIFIED" for row in summary_rows), "Category denominator scope changed")

    unclassified = query_dicts(conn, f"SELECT bnetza_state_name, bnetza_district_name, geographic_compatibility_status, equipment_count, charging_point_count FROM {district_name} WHERE bbsr_settlement_type_code IS NULL ORDER BY 1,2")
    require({(row["bnetza_state_name"], row["bnetza_district_name"]) for row in unclassified} == {("Hessen", "Kreisfreie Stadt Hanau"), ("Hessen", "Landkreis Main-Kinzig-Kreis")}, "Unexpected unclassified districts")
    require(sum(int(row["equipment_count"]) for row in unclassified) == 585, "Unclassified equipment total failed")
    require(sum(int(row["charging_point_count"]) for row in unclassified) == 991, "Unclassified point total failed")

    trier = query_dicts(conn, f"""
        SELECT bnetza_district_name, bbsr_administrative_district_code,
               bbsr_settlement_type_code, charging_point_count
        FROM {district_name}
        WHERE bnetza_district_name IN ('Kreisfreie Stadt Trier', 'Landkreis Trier-Saarburg')
        ORDER BY bnetza_district_name
    """)
    require(len(trier) == 2, "Trier city/county were not kept separate")
    require([(row["bbsr_administrative_district_code"], row["bbsr_settlement_type_code"]) for row in trier] == [("07211000", "1"), ("07235000", "3")], "Trier BBSR classifications changed")
    require(sum(int(row["charging_point_count"]) for row in trier) == 503, "Trier charging points changed")

    district_sql = (view_sql(conn, district_name) or "").lower()
    type_sql = (view_sql(conn, type_name) or "").lower()
    for name, sql in ((district_name, district_sql), (type_name, type_sql)):
        require("kba" not in sql and "bev" not in sql and "phev" not in sql, f"{name} unexpectedly references KBA stock")
    require("string_split" in district_sql and "equipment_excel_row" in district_sql and "max(power_kw)" in district_sql, "District view does not contain the required point-power parser")

    district_columns = [name for name, _ in describe_columns(conn, district_name)]
    required_district_columns = {
        "bnetza_state_name", "bnetza_district_name", "infrastructure_reference_date", "bbsr_reference_date",
        "bbsr_administrative_district_code", "bbsr_kreisregion_code", "bbsr_settlement_type_code",
        "geographic_compatibility_status", "equipment_count", "charging_point_count",
        "normal_charging_point_count", "fast_charging_point_count", "points_ge_150_kw",
        "points_ge_350_kw", "unclassifiable_power_point_count", "total_equipment_nominal_power_mw",
        "fast_point_share_pct", "high_power_point_share_pct",
    }
    require(required_district_columns <= set(district_columns), "District view columns are incomplete")
    return {
        "bridge_rows": int(scalar(conn, f"SELECT COUNT(*) FROM {bridge_name}")),
        "district_rows": int(scalar(conn, f"SELECT COUNT(*) FROM {district_name}")),
        "type_rows": int(scalar(conn, f"SELECT COUNT(*) FROM {type_name}")),
        "totals": actual_totals | {"nominal_power_mw": nominal_mw},
        "unclassified": {
            "districts": len(unclassified),
            "equipment": sum(int(row["equipment_count"]) for row in unclassified),
            "charging_points": sum(int(row["charging_point_count"]) for row in unclassified),
            "equipment_pct": round(100.0 * sum(int(row["equipment_count"]) for row in unclassified) / EXPECTED["equipment"], 6),
            "charging_points_pct": round(100.0 * sum(int(row["charging_point_count"]) for row in unclassified) / EXPECTED["points"], 6),
        },
        "category_kpis": summary_rows,
        "trier_rows": trier,
    }


def json_default(value: Any) -> str:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return str(value)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--bbsr", type=Path, default=DEFAULT_BBSR)
    parser.add_argument("--bbsr-manifest", type=Path, default=DEFAULT_BBSR_MANIFEST)
    parser.add_argument("--path-audit", type=Path, default=DEFAULT_PATH_AUDIT)
    parser.add_argument("--bridge", type=Path, default=DEFAULT_BRIDGE)
    parser.add_argument("--bridge-manifest", type=Path, default=DEFAULT_BRIDGE_MANIFEST)
    parser.add_argument("--sql", type=Path, default=DEFAULT_SQL)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--backup-path", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="Print deployment evidence as JSON")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict[str, Any]:
    database = resolve_path(args.database)
    bbsr_path = resolve_path(args.bbsr)
    bbsr_manifest_path = resolve_path(args.bbsr_manifest)
    audit_path = resolve_path(args.path_audit)
    bridge_path = resolve_path(args.bridge)
    bridge_manifest_path = resolve_path(args.bridge_manifest)
    sql_path = resolve_path(args.sql)
    backup_dir = resolve_path(args.backup_dir)
    require(database.is_file(), f"Missing database: {database}")
    require(bbsr_manifest_path.is_file(), f"Missing BBSR source manifest: {bbsr_manifest_path}")

    bbsr_rows, _ = load_bbsr(bbsr_path)
    read_conn = duckdb.connect(str(database), read_only=True)
    try:
        bridge_rows, bridge_info = bridge_records(read_conn, bbsr_path, audit_path)
        baseline = baseline_state(read_conn, bbsr_rows)
        database_hash_before = sha256(database)
    finally:
        read_conn.close()

    write_or_validate_bridge(bridge_path, bridge_rows)
    write_or_validate_manifest(
        bridge_manifest_path,
        bridge_path,
        bbsr_path,
        bbsr_manifest_path,
        audit_path,
        bridge_info,
    )

    backup_arg = resolve_path(args.backup_path) if args.backup_path is not None else None
    if backup_arg is not None:
        backup = validate_backup(backup_arg, baseline["metrics"])
    else:
        backup = create_backup(database, backup_dir, baseline["metrics"])

    no_open_database_handles(database)
    sections = read_sql_sections(sql_path)
    required_sections = {
        "create_reference_schema",
        "create_analytics_schema",
        "create_bridge_table",
        "insert_bridge_rows",
        "charging_by_bbsr_district_view",
        "charging_by_bbsr_type_view",
    }
    require(required_sections <= sections.keys(), "Batch 13 SQL deployment sections are incomplete")

    conn = duckdb.connect(str(database))
    committed = False
    try:
        conn.execute("BEGIN")
        conn.execute(render_sql(sections["create_reference_schema"], bridge_path))
        conn.execute(render_sql(sections["create_analytics_schema"], bridge_path))
        bridge_name = "reference.bnetza_bbsr_district_bridge_2025"
        existing_type = object_type(conn, bridge_name)
        if existing_type is None:
            conn.execute(render_sql(sections["create_bridge_table"], bridge_path))
            conn.execute(render_sql(sections["insert_bridge_rows"], bridge_path))
        else:
            require(existing_type == "BASE TABLE", f"Existing BBSR bridge has wrong type: {existing_type}")
        require(bridge_table_matches(conn, bridge_rows), "Deployed bridge differs from reproducible bridge CSV")
        conn.execute(render_sql(sections["charging_by_bbsr_district_view"], bridge_path))
        conn.execute(render_sql(sections["charging_by_bbsr_type_view"], bridge_path))
        new_layer = validate_new_layer(conn, bridge_rows, baseline["metrics"])
        assert_existing_unchanged(conn, baseline)
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
        final_layer = validate_new_layer(final_conn, bridge_rows, baseline["metrics"])
        assert_existing_unchanged(final_conn, baseline)
    finally:
        final_conn.close()

    return {
        "validation": "PASS",
        "database": str(database),
        "backup": backup,
        "bridge": {
            "path": str(bridge_path),
            "sha256": sha256(bridge_path),
            **bridge_info,
        },
        "bridge_manifest": {
            "path": str(bridge_manifest_path),
            "sha256": sha256(bridge_manifest_path),
        },
        "baseline": baseline["metrics"],
        "new_layer": final_layer,
        "source_fingerprints": {
            "database_sha256_before_deployment": database_hash_before,
            "bbsr_csv_sha256": sha256(bbsr_path),
            "bbsr_source_manifest_sha256": sha256(bbsr_manifest_path),
            "batch12_path_a_audit_sha256": sha256(audit_path),
            "bridge_csv_sha256": sha256(bridge_path),
            "sql_sha256": sha256(sql_path),
        },
        "existing_kba_objects_unchanged": True,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        evidence = run(args)
    except (DeploymentError, OSError, ValueError, TypeError, duckdb.Error) as exc:
        print(f"[FAIL] Batch 13 deployment: {exc}", file=sys.stderr)
        return 1
    print("[PASS] Batch 13 BBSR charging-only deployment transaction committed")
    print(f"[INFO] Verified backup: {evidence['backup']['path']}")
    print(f"[INFO] Bridge: {evidence['bridge']['path']}")
    if args.json:
        print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True, default=json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
