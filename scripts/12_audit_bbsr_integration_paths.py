#!/usr/bin/env python3
"""Audit two non-operational paths from the project geographies to BBSR.

Path A starts with the BNetzA state/district geography and tests whether the
source district itself can be identified in the BBSR 2025 Kreis reference.
Path B starts with a KBA registration region and tests whether the existing
source identities provide an authoritative administrative bridge before any
BBSR classification is considered.

The script deliberately does not create a bridge, change the existing
Crosswalk or BBSR reference, write to DuckDB, allocate Trier stock, or produce
a production KPI.  It writes one clearly non-operational CSV containing both
paths so every source geography remains visible.

Run from the repository root:

    .venv/bin/python scripts/12_audit_bbsr_integration_paths.py

DuckDB is opened with ``read_only=True``.  The script fails visibly when a
source shape, baseline, key, or coverage reconciliation is invalid.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    import duckdb
except ImportError as exc:  # pragma: no cover - exercised outside the venv
    raise SystemExit("duckdb is required; use the existing project environment") from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_BBSR = ROOT / "data/reference/bbsr_settlement_types_2025.csv"
DEFAULT_CROSSWALK = ROOT / "data/reference/bnetza_kba_district_crosswalk_2026.csv"
DEFAULT_PRIOR_AUDIT = ROOT / "reports/batch11_bbsr_kba_compatibility_audit.csv"
DEFAULT_OUTPUT = ROOT / "reports/batch12_bbsr_integration_paths_audit.csv"

SOURCE_ID = "bnetza_charging_2026_09_30"
BNETZA_REFERENCE_DATE = "2026-09-30"
KBA_REFERENCE_DATES = (
    dt.date(2026, 1, 1),
    dt.date(2026, 4, 1),
    dt.date(2026, 7, 1),
)
BBSR_REFERENCE_DATE = "2025-12-31"
BBSR_SOURCE_VERSION = (
    "raumgliederungen-referenzen-2025.xlsx | Kreisreferenz | "
    "geographic stand 2025-12-31"
)
BBSR_ALLOWED_TYPES = ("1", "2", "3", "4")
BBSR_TYPE_LABELS = {
    "1": "kreisfreie Großstadt",
    "2": "städtischer Kreis",
    "3": "ländlicher Kreis mit Verdichtungsansätzen",
    "4": "dünn besiedelter ländlicher Kreis",
}
KBA_CODE_RE = re.compile(r"^[0-9]{5}$")
BBSR_CODE_RE = re.compile(r"^[0-9]{8}$")

EXPECTED = {
    "equipment_rows": 117_662,
    "charging_points": 211_253,
    "declared_points": 211_253,
    "bnetza_source_geographies": 401,
    "crosswalk_rows": 401,
    "kba_regions": 400,
    "combined_rows": 1_200,
    "july_bev": 2_362_218,
    "bbsr_rows": 400,
    "bbsr_kreisregions": 362,
    "bbsr_multi_kreisregions": 36,
}

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

CROSSWALK_COLUMNS = (
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

AUDIT_COLUMNS = (
    "audit_output_scope",
    "audit_version",
    "path",
    "source_record_key",
    "source_geography_grain",
    "source_reference_product",
    "source_reference_date",
    "bnetza_source_id",
    "bnetza_reference_date",
    "bnetza_state_name",
    "bnetza_district_name",
    "bnetza_admin_type",
    "kba_reference_product",
    "kba_reference_dates",
    "kba_district_code",
    "kba_district_name",
    "kba_state_name",
    "kba_admin_type",
    "crosswalk_source_geography_rows",
    "crosswalk_kba_candidate_code",
    "crosswalk_kba_candidate_name",
    "crosswalk_evidence_types",
    "crosswalk_operational_statuses",
    "bbsr_reference_date",
    "bbsr_source_version",
    "bbsr_candidate_codes",
    "bbsr_candidate_names",
    "bbsr_candidate_types",
    "bbsr_candidate_kreisregion_codes",
    "bbsr_candidate_kreisregion_names",
    "bbsr_candidate_count",
    "bbsr_components_complete",
    "bbsr_components_share_type",
    "kreisregion_component_counts",
    "candidate_resolution",
    "candidate_mapping_relation",
    "identifier_support",
    "geographic_coverage_evidence",
    "administrative_boundary_alignment",
    "source_vintage_assessment",
    "allocation_or_estimation_required",
    "charging_only_descriptive_safe",
    "evidence_confidence",
    "audit_status",
    "strict_bbsr_classification_supported",
    "prior_batch11_status",
    "issue_flags",
    "audit_reason",
    "equipment_rows",
    "declared_point_count",
    "charging_point_total",
    "january_2026_bev_cars",
    "april_2026_bev_cars",
    "july_2026_bev_cars",
)

OFFICIAL_SOURCE_URLS = {
    "destatis_gv_isys": (
        "https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/"
        "Gemeindeverzeichnis/_inhalt.html"
    ),
    "destatis_gv_isys_definition": (
        "https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/"
        "Gemeindeverzeichnis/gemeindeverzeichnis-einleitung.html"
    ),
    "destatis_q3_2026": (
        "https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/"
        "Gemeindeverzeichnis/Administrativ/Archiv/GVAuszugQ/AuszugGV3QAktuell.html"
    ),
    "destatis_gv100ad_q3_2026": (
        "https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/"
        "Gemeindeverzeichnis/Administrativ/Archiv/GV100ADQ/GV100AD3QAktuell.html"
    ),
    "bbsr_downloads": (
        "https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/"
        "Raumabgrenzungen/downloads/download-referenzen.html"
    ),
    "bbsr_umsteigeschluessel": (
        "https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/"
        "Raumabgrenzungen/umstiegsschluessel/umsteigeschluessel.html"
    ),
    "bbsr_kreise_kreisregionen": (
        "https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/"
        "Raumabgrenzungen/deutschland/kreise/Kreise_Kreisregionen/Kreise.html"
    ),
    "bbsr_kreistypen": (
        "https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/"
        "Raumabgrenzungen/deutschland/kreise/siedlungsstrukturelle-kreistypen/"
        "kreistypen.html"
    ),
    "bbsr_workbook": (
        "https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/"
        "Raumabgrenzungen/downloads/raumgliederungen-referenzen-2025.xlsx?"
        "__blob=publicationFile&v=3"
    ),
    "inkar": "https://www.inkar.de/Default",
    "ba_political_structure": (
        "https://statistik.arbeitsagentur.de/DE/Navigation/Grundlagen/"
        "Klassifikationen/Regionale-Gliederungen/Politische-Gebietsstruktur-Nav.html"
    ),
    "kba_fz27_metadata": (
        "https://www.govdata.de/suche/daten/fz-27-2026-bestand-an-"
        "kraftfahrzeugen-und-kraftfahrzeuganhangern-nach-ausgewahlten-merkmalen-bu"
    ),
    "kba_fz27_july": (
        "https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/"
        "fz27_202607.xlsx?__blob=publicationFile&v=3"
    ),
    "hessen_hanau": "https://innen.hessen.de/kommunales/kommunen/gemeinden-und-landkreise",
    "hessen_january_2026_keys": (
        "https://statistik.hessen.de/sites/statistik.hessen.de/files/2026-01/"
        "verz-2_26-01.pdf"
    ),
    "trier_registration_office": "https://trier-saarburg.de/ihr-anliegen/zulassungsstelle/",
}


class AuditError(RuntimeError):
    """Raised when a source or acceptance check fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def query_dicts(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    result = conn.execute(sql)
    names = [item[0] for item in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def db_columns(
    conn: duckdb.DuckDBPyConnection, qualified_name: str
) -> list[tuple[str, str]]:
    schema, name = qualified_name.split(".", 1)
    rows = conn.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = ? AND table_name = ?
        ORDER BY ordinal_position
        """,
        [schema, name],
    ).fetchall()
    return [(str(row[0]), str(row[1])) for row in rows]


def require_db_columns(
    conn: duckdb.DuckDBPyConnection,
    qualified_name: str,
    required: Mapping[str, str],
) -> None:
    actual = dict(db_columns(conn, qualified_name))
    require(actual, f"Missing or inaccessible DuckDB object: {qualified_name}")
    for column, data_type in required.items():
        require(column in actual, f"{qualified_name} is missing {column!r}")
        require(
            actual[column] == data_type,
            f"{qualified_name}.{column} type {actual[column]!r} != {data_type!r}",
        )


def read_csv_rows(path: Path, expected_columns: Sequence[str]) -> list[dict[str, str]]:
    require(path.is_file(), f"Missing CSV source: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(
            tuple(reader.fieldnames or ()) == tuple(expected_columns),
            f"Unexpected CSV schema in {path}: {reader.fieldnames}",
        )
        return [dict(row) for row in reader]


def read_prior_audit(path: Path) -> dict[str, dict[str, str]]:
    require(path.is_file(), f"Missing prior Batch 11 audit: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "kba_district_code",
            "audit_status",
            "audit_reason",
            "bbsr_prefix_candidate_codes",
            "bbsr_component_codes",
        }
        require(required <= set(reader.fieldnames or ()), "Batch 11 audit schema is incomplete")
        rows = [dict(row) for row in reader]
    require(len(rows) == EXPECTED["kba_regions"], f"Batch 11 audit rows: {len(rows)}")
    codes = [row["kba_district_code"] for row in rows]
    require(len(set(codes)) == len(codes), "Duplicate KBA code in Batch 11 audit")
    allowed = {
        "EXACT",
        "HOMOGENEOUS_COMPOSITE",
        "MIXED",
        "VINTAGE_CONFLICT",
        "UNRESOLVED",
        "CONFLICTING",
    }
    require(set(row["audit_status"] for row in rows) <= allowed, "Unexpected Batch 11 audit status")
    return {row["kba_district_code"]: row for row in rows}


def parse_int(value: Any, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise AuditError(f"Expected integer for {label}: {value!r}") from exc


def normalise_text(value: str) -> str:
    """Normalize spelling for identity comparison without creating a key system."""

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
    """Remove administrative/name honorifics while retaining the place identity."""

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
    """Infer only the administrative form expressed in the BBSR row label."""

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


def bbsr_type_is_compatible(row: Mapping[str, str], source_admin_type: str) -> bool:
    """Reject an explicit BBSR city/county contradiction in a source match."""

    observed_form = bbsr_admin_form(row["administrative_district_name"])
    return observed_form == "unknown" or observed_form == source_admin_type


def join_values(values: Iterable[Any]) -> str:
    return ";".join(sorted({str(value) for value in values if value not in (None, "")}))


def relative_or_absolute(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def validate_bbsr(rows: list[dict[str, str]]) -> dict[str, Any]:
    require(len(rows) == EXPECTED["bbsr_rows"], f"BBSR rows: {len(rows)}")
    require(
        all(row["source_version"] == BBSR_SOURCE_VERSION for row in rows),
        "BBSR source_version is inconsistent",
    )
    require(
        all(row["bbsr_reference_date"] == BBSR_REFERENCE_DATE for row in rows),
        "BBSR reference date is inconsistent",
    )
    codes = [row["administrative_district_code"] for row in rows]
    require(all(BBSR_CODE_RE.fullmatch(code or "") for code in codes), "Invalid BBSR administrative code")
    require(len(set(codes)) == len(codes), "Duplicate BBSR administrative district code")
    require(
        all(
            row["federal_state_code"]
            and row["federal_state_name"]
            and row["kreisregion_code"]
            and row["kreisregion_name"]
            and row["settlement_type_code"] in BBSR_ALLOWED_TYPES
            and row["settlement_type_name_de"]
            for row in rows
        ),
        "Missing or invalid BBSR geography/classification fields",
    )
    require(
        all(
            BBSR_TYPE_LABELS[row["settlement_type_code"]] == row["settlement_type_name_de"]
            for row in rows
        ),
        "BBSR classification code/label mismatch",
    )
    by_kreisregion: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_state_identity: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    by_prefix: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_kreisregion[row["kreisregion_code"]].append(row)
        by_state_identity[
            (row["federal_state_name"], administrative_identity_key(row["administrative_district_name"]))
        ].append(row)
        by_prefix[row["administrative_district_code"][:5]].append(row)
    require(len(by_kreisregion) == EXPECTED["bbsr_kreisregions"], "Unexpected BBSR Kreisregion count")
    for code, group in by_kreisregion.items():
        require(len({row["kreisregion_name"] for row in group}) == 1, f"Inconsistent Kreisregion {code}")
        require(
            len({row["settlement_type_code"] for row in group}) == 1,
            f"Mixed BBSR type inside Kreisregion {code}",
        )
    multi = {code: group for code, group in by_kreisregion.items() if len(group) > 1}
    require(len(multi) == EXPECTED["bbsr_multi_kreisregions"], "Unexpected BBSR multi-Kreisregion count")
    require(
        Counter(row["settlement_type_code"] for row in rows)
        == Counter({"1": 68, "2": 131, "3": 98, "4": 103}),
        "Unexpected BBSR type distribution",
    )
    return {
        "by_code": {row["administrative_district_code"]: row for row in rows},
        "by_state_identity": dict(by_state_identity),
        "by_prefix": dict(by_prefix),
        "by_kreisregion": dict(by_kreisregion),
        "multi_kreisregions": multi,
    }


def validate_crosswalk(rows: list[dict[str, str]]) -> dict[str, Any]:
    require(len(rows) == EXPECTED["crosswalk_rows"], f"Crosswalk rows: {len(rows)}")
    source_keys = [
        (row["bnetza_state_name"], row["bnetza_district_name"]) for row in rows
    ]
    require(len(set(source_keys)) == len(source_keys), "Duplicate Crosswalk source key")
    codes = [row["kba_district_code"] for row in rows]
    require(all(KBA_CODE_RE.fullmatch(code or "") for code in codes), "Invalid Crosswalk KBA code")
    require(set(code for code in codes if codes.count(code) > 1) == {"07211"}, "Unexpected duplicate KBA target")
    require(codes.count("07211") == 2, "Trier shared KBA target is not represented twice")
    require(all(row["mapping_status"] == "mapped" for row in rows), "Unmapped Crosswalk row")
    require(
        all(row["bnetza_admin_type"] in {"city", "county"} for row in rows),
        "Crosswalk has an invalid BNetzA administrative type",
    )
    require(
        all(row["bnetza_reference_date"] == BNETZA_REFERENCE_DATE for row in rows),
        "Crosswalk BNetzA reference date changed",
    )
    require(
        all(row["kba_state_name"] == row["bnetza_state_name"] for row in rows),
        "Crosswalk contains a cross-state mapping",
    )
    by_source = {key: row for key, row in zip(source_keys, rows)}
    by_kba: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_kba[row["kba_district_code"]].append(row)
    return {"by_source": by_source, "by_kba": dict(by_kba)}


def resolve_bbsr_component(
    source_row: Mapping[str, str],
    bbsr: Mapping[str, Any],
) -> tuple[list[dict[str, str]], str, list[dict[str, str]], list[dict[str, str]]]:
    """Resolve a BNetzA source identity to BBSR candidates without using KBA as proof."""

    state = source_row["bnetza_state_name"]
    identity = administrative_identity_key(source_row["bnetza_district_name"])
    direct = list(bbsr["by_state_identity"].get((state, identity), []))
    prefix = list(bbsr["by_prefix"].get(source_row.get("kba_district_code", ""), []))
    direct = [
        row
        for row in direct
        if bbsr_type_is_compatible(row, source_row["bnetza_admin_type"])
    ]
    if len(direct) == 1:
        return direct, "direct_state_identity", direct, prefix
    if len(direct) > 1:
        typed = [
            row
            for row in direct
            if bbsr_admin_form(row["administrative_district_name"])
            == source_row["bnetza_admin_type"]
        ]
        if len(typed) == 1:
            return typed, "direct_state_identity_plus_admin_type", direct, prefix
        if source_row["bnetza_admin_type"] == "city":
            weak = [
                row
                for row in direct
                if bbsr_admin_form(row["administrative_district_name"]) != "county"
            ]
        else:
            weak = [
                row
                for row in direct
                if bbsr_admin_form(row["administrative_district_name"]) != "city"
            ]
        if len(weak) == 1:
            return weak, "direct_state_identity_plus_admin_type", direct, prefix
        return [], "ambiguous_direct_identity", direct, prefix
    if len(prefix) == 1:
        return prefix, "prefix_candidate_only", direct, prefix
    if prefix:
        return prefix, "ambiguous_prefix_candidate", direct, prefix
    return [], "unresolved_identity", direct, prefix


def source_evidence_type(crosswalk_row: Mapping[str, str]) -> str:
    method = crosswalk_row["mapping_method"]
    if method == "explicit_provisional_alias":
        return "prior_official_row_level_identity_evidence"
    if method == "explicit_state_city_naming_convention":
        return "state_city_naming_convention"
    if method == "shared_kba_registration_region":
        return "official_shared_registration_region_evidence"
    return "local_state_admin_type_name_crosswalk"


def status_percent(value: int, denominator: int) -> float:
    return round(value / denominator * 100, 6)


def coverage_by_status(
    rows: Sequence[Mapping[str, Any]],
    statuses: Sequence[str],
    denominator_regions: int,
    denominator_equipment: int | None = None,
    denominator_points: int = EXPECTED["charging_points"],
    denominator_bev: int | None = None,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for status in statuses:
        group = [row for row in rows if row["audit_status"] == status]
        equipment = sum(parse_int(row.get("equipment_rows", 0) or 0, "equipment_rows") for row in group)
        points = sum(parse_int(row.get("charging_point_total", 0) or 0, "charging_point_total") for row in group)
        bevs = sum(parse_int(row.get("july_2026_bev_cars", 0) or 0, "july_2026_bev_cars") for row in group)
        item = {
            "regions": len(group),
            "regions_pct": status_percent(len(group), denominator_regions),
            "equipment_rows": equipment,
            "charging_points": points,
            "charging_points_pct": status_percent(points, denominator_points),
        }
        if denominator_equipment is not None:
            item["equipment_rows_pct"] = status_percent(equipment, denominator_equipment)
        if denominator_bev is not None:
            item["july_bev_cars"] = bevs
            item["july_bev_pct"] = status_percent(bevs, denominator_bev)
        result[status] = item
    return result


def base_row(path: str, source_key: str, grain: str) -> dict[str, Any]:
    return {
        "audit_output_scope": "NON_OPERATIONAL_BBSR_INTEGRATION_PATH_AUDIT",
        "audit_version": "batch12-2026-11-02-two-path-strict-evidence",
        "path": path,
        "source_record_key": source_key,
        "source_geography_grain": grain,
        "source_reference_product": "",
        "source_reference_date": "",
        "bnetza_source_id": SOURCE_ID,
        "bnetza_reference_date": BNETZA_REFERENCE_DATE,
        "bnetza_state_name": "",
        "bnetza_district_name": "",
        "bnetza_admin_type": "",
        "kba_reference_product": "KBA FZ 27.15",
        "kba_reference_dates": ";".join(date.isoformat() for date in KBA_REFERENCE_DATES),
        "kba_district_code": "",
        "kba_district_name": "",
        "kba_state_name": "",
        "kba_admin_type": "",
        "crosswalk_source_geography_rows": 0,
        "crosswalk_kba_candidate_code": "",
        "crosswalk_kba_candidate_name": "",
        "crosswalk_evidence_types": "",
        "crosswalk_operational_statuses": "",
        "bbsr_reference_date": BBSR_REFERENCE_DATE,
        "bbsr_source_version": BBSR_SOURCE_VERSION,
        "bbsr_candidate_codes": "",
        "bbsr_candidate_names": "",
        "bbsr_candidate_types": "",
        "bbsr_candidate_kreisregion_codes": "",
        "bbsr_candidate_kreisregion_names": "",
        "bbsr_candidate_count": 0,
        "bbsr_components_complete": "no",
        "bbsr_components_share_type": "not_observed",
        "kreisregion_component_counts": "",
        "candidate_resolution": "",
        "candidate_mapping_relation": "",
        "identifier_support": "",
        "geographic_coverage_evidence": "",
        "administrative_boundary_alignment": "",
        "source_vintage_assessment": "",
        "allocation_or_estimation_required": "",
        "charging_only_descriptive_safe": "not_applicable",
        "evidence_confidence": "",
        "audit_status": "",
        "strict_bbsr_classification_supported": "no",
        "prior_batch11_status": "",
        "issue_flags": "",
        "audit_reason": "",
        "equipment_rows": 0,
        "declared_point_count": 0,
        "charging_point_total": 0,
        "january_2026_bev_cars": "",
        "april_2026_bev_cars": "",
        "july_2026_bev_cars": "",
    }


def add_bbsr_fields(row: dict[str, Any], components: Sequence[Mapping[str, str]], bbsr: Mapping[str, Any]) -> None:
    ordered = sorted(components, key=lambda item: item["administrative_district_code"])
    types = sorted({item["settlement_type_code"] for item in ordered})
    row["bbsr_candidate_codes"] = join_values(item["administrative_district_code"] for item in ordered)
    row["bbsr_candidate_names"] = join_values(item["administrative_district_name"] for item in ordered)
    row["bbsr_candidate_types"] = join_values(
        f"{item['settlement_type_code']}:{item['settlement_type_name_de']}" for item in ordered
    )
    row["bbsr_candidate_kreisregion_codes"] = join_values(item["kreisregion_code"] for item in ordered)
    row["bbsr_candidate_kreisregion_names"] = join_values(item["kreisregion_name"] for item in ordered)
    row["bbsr_candidate_count"] = len(ordered)
    row["bbsr_components_complete"] = "yes" if ordered else "no"
    row["bbsr_components_share_type"] = "yes" if len(types) == 1 and ordered else "no" if ordered else "not_observed"
    row["kreisregion_component_counts"] = join_values(
        f"{item['kreisregion_code']}:{len(bbsr['by_kreisregion'][item['kreisregion_code']])}"
        for item in ordered
    )


def build_path_a(
    source_rows: Mapping[tuple[str, str], Mapping[str, Any]],
    crosswalk: Mapping[str, Any],
    bbsr: Mapping[str, Any],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for source_key in sorted(source_rows):
        source = source_rows[source_key]
        crosswalk_row = crosswalk["by_source"].get(source_key)
        require(crosswalk_row is not None, f"Missing Crosswalk row for BNetzA source {source_key}")
        components, resolution, direct, prefix = resolve_bbsr_component(crosswalk_row, bbsr)
        row = base_row(
            "PATH_A",
            f"{source_key[0]}|{source_key[1]}",
            "BNetzA administrative state/district",
        )
        row.update(
            {
                "source_reference_product": "BNetzA Ladesäulenregister",
                "source_reference_date": BNETZA_REFERENCE_DATE,
                "bnetza_state_name": source["bnetza_state_name"],
                "bnetza_district_name": source["bnetza_district_name"],
                "bnetza_admin_type": crosswalk_row["bnetza_admin_type"],
                "kba_district_code": crosswalk_row["kba_district_code"],
                "kba_district_name": crosswalk_row["kba_district_name"],
                "kba_state_name": crosswalk_row["kba_state_name"],
                "kba_admin_type": crosswalk_row["kba_admin_type"],
                "crosswalk_source_geography_rows": 1,
                "crosswalk_kba_candidate_code": crosswalk_row["kba_district_code"],
                "crosswalk_kba_candidate_name": crosswalk_row["kba_district_name"],
                "crosswalk_evidence_types": source_evidence_type(crosswalk_row),
                "crosswalk_operational_statuses": crosswalk_row["verification_status"],
                "equipment_rows": parse_int(source["equipment_rows"], "equipment_rows"),
                "declared_point_count": parse_int(source["declared_point_count"], "declared_point_count"),
                "charging_point_total": parse_int(source["charging_point_count"], "charging_point_count"),
                "candidate_resolution": resolution,
            }
        )
        add_bbsr_fields(row, components, bbsr)
        direct_candidate = len(components) == 1 and resolution.startswith("direct_")
        row["bbsr_components_complete"] = "yes" if direct_candidate else "no"
        is_hanau = source["bnetza_district_name"] == "Kreisfreie Stadt Hanau"
        is_main_kinzig = source["bnetza_district_name"] == "Landkreis Main-Kinzig-Kreis"
        if is_hanau:
            status = "UNRESOLVED"
            row.update(
                {
                    "candidate_mapping_relation": "missing_BBSR_2025_component",
                    "identifier_support": "official_Hessen_2026_boundary_evidence; no_BBSR_2025_Hanau_row",
                    "geographic_coverage_evidence": "BNetzA source row is separately present after the 2026 administrative change; BBSR 2025 has no Hanau administrative row.",
                    "administrative_boundary_alignment": "not_established_across_2025_2026_boundary",
                    "source_vintage_assessment": "Hanau became kreisfreie Stadt on 2026-01-01; BBSR geographic stand is 2025-12-31.",
                    "allocation_or_estimation_required": "no_estimation_or_inheritance_allowed",
                    "charging_only_descriptive_safe": "no_BBSR_category",
                    "evidence_confidence": "high_for_vintage_exception",
                    "issue_flags": "boundary_vintage_conflict;missing_BBSR_Hanau_row;no_estimation_or_allocation",
                    "audit_reason": "The BNetzA district is current and identifiable, but the BBSR 2025 reference has no Hanau row. Main-Kinzig type 2 cannot be inherited.",
                }
            )
        elif is_main_kinzig:
            require(direct_candidate, "Main-Kinzig direct BBSR candidate disappeared")
            status = "CONDITIONAL_VINTAGE"
            row.update(
                {
                    "candidate_mapping_relation": "direct_identity_pre_change_BBSR_component",
                    "identifier_support": "state_admin_type_identity_plus_official_Hessen_2026_boundary_evidence",
                    "geographic_coverage_evidence": "BNetzA and BBSR both identify Main-Kinzig-Kreis, but the BBSR row predates Hanau's 2026 separation.",
                    "administrative_boundary_alignment": "conditional_pre_change_boundary",
                    "source_vintage_assessment": "BBSR 2025 Main-Kinzig row predates the 2026-01-01 Hanau separation; current remainder is not proven identical.",
                    "allocation_or_estimation_required": "no_estimation_or_allocation_allowed",
                    "charging_only_descriptive_safe": "conditional_observed_charging_only",
                    "evidence_confidence": "high_for_vintage_exception",
                    "issue_flags": "boundary_vintage_conflict;bbsr_main_kinzig_pre_change_boundary;no_exact_current_class",
                    "audit_reason": "The source district identity is clear, but the BBSR type 2 row is from before Hanau became independent and cannot be treated as exact for the current remainder.",
                }
            )
        elif direct_candidate:
            status = "VERIFIED_COMPATIBLE"
            row.update(
                {
                    "candidate_mapping_relation": "direct_BNetzA_administrative_identity_to_BBSR_Kreis",
                    "identifier_support": "state_admin_type_name_identity;BNetzA_has_no_AGS_or_ARS_field",
                    "geographic_coverage_evidence": "Unique state + BNetzA administrative type + normalized administrative identity resolves to one BBSR KRS row; no KBA code is used as proof.",
                    "administrative_boundary_alignment": "compatible_at_named_source_administrative_grain;KBA_equivalence_not_claimed",
                    "source_vintage_assessment": "BNetzA 2026-09-30 versus BBSR geographic stand 2025-12-31; no additional boundary change identified for this row in reviewed official evidence.",
                    "allocation_or_estimation_required": "no_vehicle_stock_or_allocation_used",
                    "charging_only_descriptive_safe": "yes_with_source_dates_and_BBSR_vintage",
                    "evidence_confidence": "high_for_source_identity_conditional_for_vintage",
                    "issue_flags": "BNetzA_source_has_no_formal_BBSR_key;preserve_BBSR_vintage",
                    "audit_reason": "The BNetzA administrative source row can be identified as one BBSR Kreis row for charging-only descriptive analysis. This is not a KBA-to-BBSR bridge and does not authorize production integration.",
                }
            )
        else:
            status = "UNRESOLVED"
            row.update(
                {
                    "candidate_mapping_relation": "prefix_or_ambiguous_candidate_only",
                    "identifier_support": "BBSR_candidate_not_independently_supported",
                    "geographic_coverage_evidence": "No unique direct BNetzA administrative identity was established without relying on an unverified code candidate.",
                    "administrative_boundary_alignment": "not_established",
                    "source_vintage_assessment": "BNetzA 2026-09-30 versus BBSR geographic stand 2025-12-31; identity is unresolved.",
                    "allocation_or_estimation_required": "no_estimation_or_allocation_allowed",
                    "charging_only_descriptive_safe": "no_BBSR_category",
                    "evidence_confidence": "low_for_BBSR_assignment",
                    "issue_flags": "unresolved_source_identity;prefix_match_not_geographic_equivalence",
                    "audit_reason": "The source geography does not have a uniquely supported BBSR administrative identity in the inspected reference.",
                }
            )
        row["audit_status"] = status
        result.append(row)
    require(len(result) == EXPECTED["bnetza_source_geographies"], "Path A row count mismatch")
    require(
        len({row["source_record_key"] for row in result}) == EXPECTED["bnetza_source_geographies"],
        "Duplicate Path A source geography",
    )
    return result


def build_path_b(
    database: Mapping[str, Any],
    crosswalk: Mapping[str, Any],
    bbsr: Mapping[str, Any],
    prior_audit: Mapping[str, Mapping[str, str]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for code in sorted(database["kba_by_code"]):
        date_rows = database["kba_by_code"][code]
        july = next(row for row in date_rows if row["reference_date"] == KBA_REFERENCE_DATES[-1])
        source_rows = sorted(
            crosswalk["by_kba"].get(code, []),
            key=lambda row: (row["bnetza_state_name"], row["bnetza_district_name"]),
        )
        require(source_rows, f"KBA code {code} has no existing Crosswalk source row")
        components: dict[str, dict[str, str]] = {}
        resolutions: list[str] = []
        direct_candidates: list[dict[str, str]] = []
        prefix_candidates = list(bbsr["by_prefix"].get(code, []))
        for source_row in source_rows:
            resolved, resolution, _direct, _prefix = resolve_bbsr_component(source_row, bbsr)
            resolutions.append(resolution)
            for component in resolved:
                components[component["administrative_district_code"]] = component
            if resolution.startswith("direct_"):
                direct_candidates.extend(resolved)
        component_rows = [components[key] for key in sorted(components)]
        prior = prior_audit.get(code)
        require(prior is not None, f"Missing Batch 11 audit row for KBA code {code}")
        if code == "07211":
            status = "MIXED"
            require(prior["audit_status"] == status, "Batch 11 Trier status changed unexpectedly")
            relation = "verified_shared_registration_region_with_two_BBSR_components"
            identifier_support = "official_Trier_shared_registration_evidence;BBSR_components_are_separate"
            coverage_evidence = "KBA FZ 27.15 reports one registration-region row; official Trier registration-office material covers both city and county; BBSR has two rows with types 1 and 3."
            boundary_alignment = "not_equivalent_shared_registration_region"
            vintage = "BBSR 2025 rows are separate; KBA 2026 stock combines the registration region."
            allocation = "yes_for_single_BBSR_class;no_allocation_applied"
            safe = "no_single_BBSR_class"
            confidence = "high_for_mixed_exception"
            issues = "shared_kba_registration_region;multiple_BBSR_components;mixed_BBSR_types;allocation_required_for_single_class;no_authoritative_KBA_BBSR_bridge"
            reason = "KBA 07211 contains BBSR type 1 Trier city and type 3 Trier-Saarburg. The combined 7,869 July BEVs and 503 charging points remain one KBA registration-region value and are not allocated."
        elif code in {"06415", "06435"}:
            status = "VINTAGE_CONFLICT"
            require(prior["audit_status"] == status, f"Batch 11 Hanau status changed unexpectedly for {code}")
            relation = "dated_boundary_exception_without_current_BBSR_compatible_vintage"
            identifier_support = "official_Hessen_2026_boundary_evidence;BBSR_2025_vintage"
            coverage_evidence = "Hessen's official administrative evidence records Hanau's 2026-01-01 separation; KBA has separate 06415/06435 rows, while the BBSR 2025 reference does not contain a post-change Hanau component."
            boundary_alignment = "not_equivalent_across_2025_2026_boundary_vintages"
            vintage = "BBSR geographic stand 2025-12-31 predates the 2026-01-01 Hanau separation."
            allocation = "no_inheritance_or_estimation_allowed"
            safe = "no_single_BBSR_class"
            confidence = "high_for_vintage_exception"
            issues = "boundary_vintage_conflict;no_post_change_BBSR_reference;no_estimation_or_allocation"
            if code == "06415":
                issues += ";missing_BBSR_Hanau_row"
                reason = "KBA Hanau is present after the 2026 separation, but the BBSR 2025 reference has no Hanau row; Main-Kinzig type 2 cannot be inherited."
            else:
                issues += ";BBSR_Main_Kinzig_pre_change_boundary"
                reason = "The BBSR Main-Kinzig type 2 row predates Hanau's separation and cannot be treated as an exact type for the current KBA remainder."
        else:
            status = "UNRESOLVED"
            require(prior["audit_status"] == status, f"Batch 11 ordinary status changed unexpectedly for {code}")
            relation = "candidate_component_without_authoritative_KBA_to_administrative_bridge"
            identifier_support = "BNetzA_source_identity_and_BBSR_candidate;KBA_code_system_equivalence_not_proven"
            coverage_evidence = "The existing BNetzA-to-KBA Crosswalk and BBSR reference expose a candidate component, but no official dated KBA-to-AGS/ARS/BBSR bridge was inspected."
            boundary_alignment = "not_established_for_KBA_registration_region"
            vintage = "KBA 2026 registration-region observations versus BBSR geographic stand 2025-12-31; a dated bridge is missing."
            allocation = "no_single_BBSR_class_supported"
            safe = "no_single_BBSR_class"
            confidence = "low_for_KBA_BBSR_assignment"
            issues = "no_authoritative_KBA_BBSR_bridge;prefix_match_not_geographic_equivalence;operational_status_not_changed"
            reason = "A BBSR component candidate is visible, but the official evidence reviewed does not establish that this KBA registration region has the same boundary as the BBSR administrative row."
        row = base_row("PATH_B", code, "KBA FZ 27.15 registration region")
        row.update(
            {
                "source_reference_product": "KBA FZ 27.15",
                "source_reference_date": KBA_REFERENCE_DATES[-1].isoformat(),
                "kba_district_code": code,
                "kba_district_name": july["district_name"],
                "kba_state_name": july["state_name"],
                "kba_admin_type": join_values(row["kba_admin_type"] for row in source_rows),
                "crosswalk_source_geography_rows": len(source_rows),
                "crosswalk_kba_candidate_code": code,
                "crosswalk_kba_candidate_name": july["district_name"],
                "crosswalk_evidence_types": join_values(source_evidence_type(row) for row in source_rows),
                "crosswalk_operational_statuses": join_values(row["verification_status"] for row in source_rows),
                "bbsr_candidate_count": len(component_rows),
                "candidate_resolution": join_values(resolutions),
                "candidate_mapping_relation": relation,
                "identifier_support": identifier_support,
                "geographic_coverage_evidence": coverage_evidence,
                "administrative_boundary_alignment": boundary_alignment,
                "source_vintage_assessment": vintage,
                "allocation_or_estimation_required": allocation,
                "charging_only_descriptive_safe": safe,
                "evidence_confidence": confidence,
                "audit_status": status,
                "strict_bbsr_classification_supported": "yes" if status in {"EXACT", "HOMOGENEOUS_COMPOSITE"} else "no",
                "prior_batch11_status": prior["audit_status"],
                "issue_flags": issues,
                "audit_reason": reason,
                "equipment_rows": sum(parse_int(source["equipment_rows"], "Crosswalk equipment_rows") for source in source_rows),
                "declared_point_count": sum(parse_int(source["declared_point_count"], "Crosswalk declared_point_count") for source in source_rows),
                "charging_point_total": parse_int(database["regional_by_code"][code]["charging_point_count"], "regional charging points"),
                "january_2026_bev_cars": parse_int(next(row["bev_cars"] for row in date_rows if row["reference_date"] == KBA_REFERENCE_DATES[0]), "January BEVs"),
                "april_2026_bev_cars": parse_int(next(row["bev_cars"] for row in date_rows if row["reference_date"] == KBA_REFERENCE_DATES[1]), "April BEVs"),
                "july_2026_bev_cars": parse_int(july["bev_cars"], "July BEVs"),
            }
        )
        # The BBSR prefix is intentionally a separate candidate field.  It is
        # not promoted into bbsr_candidate_codes unless a component identity
        # was independently resolved from the BNetzA source rows.
        if not component_rows and prefix_candidates:
            row["bbsr_candidate_codes"] = join_values(item["administrative_district_code"] for item in prefix_candidates)
            row["bbsr_candidate_names"] = join_values(item["administrative_district_name"] for item in prefix_candidates)
            row["bbsr_candidate_types"] = join_values(
                f"{item['settlement_type_code']}:{item['settlement_type_name_de']}" for item in prefix_candidates
            )
            row["bbsr_candidate_kreisregion_codes"] = join_values(item["kreisregion_code"] for item in prefix_candidates)
            row["bbsr_candidate_kreisregion_names"] = join_values(item["kreisregion_name"] for item in prefix_candidates)
            row["bbsr_candidate_count"] = len(prefix_candidates)
            row["candidate_mapping_relation"] = "prefix_candidate_only_without_authoritative_bridge"
        else:
            add_bbsr_fields(row, component_rows, bbsr)
            row["bbsr_components_complete"] = (
                "yes"
                if len(component_rows) == len(source_rows)
                and all(resolution.startswith("direct_") for resolution in resolutions)
                else "no"
            )
        result.append(row)
    require(len(result) == EXPECTED["kba_regions"], "Path B row count mismatch")
    require(len({row["kba_district_code"] for row in result}) == EXPECTED["kba_regions"], "Duplicate Path B KBA code")
    return result


def load_database(database: Path, crosswalk_rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    require(database.is_file(), f"Missing DuckDB database: {database}")
    conn = duckdb.connect(str(database), read_only=True)
    try:
        require_db_columns(
            conn,
            "core.charging_equipment",
            {
                "source_id": "VARCHAR",
                "excel_row": "INTEGER",
                "declared_point_count": "INTEGER",
                "state_name": "VARCHAR",
                "district_name": "VARCHAR",
            },
        )
        require_db_columns(
            conn,
            "core.charging_point",
            {"source_id": "VARCHAR", "equipment_excel_row": "INTEGER"},
        )
        require_db_columns(
            conn,
            "core.kba_district_ev_stock",
            {
                "reference_date": "DATE",
                "district_code": "VARCHAR",
                "district_name": "VARCHAR",
                "state_name": "VARCHAR",
                "bev_cars": "BIGINT",
            },
        )
        require_db_columns(
            conn,
            "analytics.charging_by_kba_district_2026_09_30",
            {"kba_district_code": "VARCHAR", "charging_point_count": "BIGINT"},
        )

        equipment_total = conn.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(declared_point_count), 0)
            FROM core.charging_equipment
            WHERE source_id = ?
            """,
            [SOURCE_ID],
        ).fetchone()
        point_total = conn.execute(
            "SELECT COUNT(*) FROM core.charging_point WHERE source_id = ?",
            [SOURCE_ID],
        ).fetchone()[0]
        require(int(equipment_total[0]) == EXPECTED["equipment_rows"], f"Equipment rows: {equipment_total[0]}")
        require(int(equipment_total[1]) == EXPECTED["declared_points"], f"Declared points: {equipment_total[1]}")
        require(int(point_total) == EXPECTED["charging_points"], f"Charging points: {point_total}")

        source_rows = query_dicts(
            conn,
            """
            WITH equipment AS (
                SELECT state_name AS bnetza_state_name,
                       district_name AS bnetza_district_name,
                       COUNT(*) AS equipment_rows,
                       SUM(declared_point_count) AS declared_point_count
                FROM core.charging_equipment
                WHERE source_id = 'bnetza_charging_2026_09_30'
                GROUP BY state_name, district_name
            ), points AS (
                SELECT e.state_name AS bnetza_state_name,
                       e.district_name AS bnetza_district_name,
                       COUNT(*) AS charging_point_count
                FROM core.charging_point p
                JOIN core.charging_equipment e
                  ON e.source_id = p.source_id
                 AND e.excel_row = p.equipment_excel_row
                WHERE p.source_id = 'bnetza_charging_2026_09_30'
                GROUP BY e.state_name, e.district_name
            )
            SELECT e.bnetza_state_name,
                   e.bnetza_district_name,
                   e.equipment_rows,
                   e.declared_point_count,
                   p.charging_point_count
            FROM equipment e
            JOIN points p USING (bnetza_state_name, bnetza_district_name)
            ORDER BY e.bnetza_state_name, e.bnetza_district_name
            """,
        )
        require(len(source_rows) == EXPECTED["bnetza_source_geographies"], f"BNetzA source geographies: {len(source_rows)}")
        require(
            sum(parse_int(row["equipment_rows"], "source equipment rows") for row in source_rows)
            == EXPECTED["equipment_rows"],
            "BNetzA source equipment coverage does not reconcile",
        )
        require(
            sum(parse_int(row["charging_point_count"], "source charging points") for row in source_rows)
            == EXPECTED["charging_points"],
            "BNetzA source charging-point coverage does not reconcile",
        )
        source_key_rows = {
            (row["bnetza_state_name"], row["bnetza_district_name"]): row for row in source_rows
        }
        require(len(source_key_rows) == len(source_rows), "Duplicate BNetzA source geography")
        require(
            set(source_key_rows) == {
                (row["bnetza_state_name"], row["bnetza_district_name"]) for row in crosswalk_rows
            },
            "BNetzA source geographies do not equal Crosswalk source geographies",
        )

        regional_rows = query_dicts(
            conn,
            """
            SELECT kba_district_code, charging_point_count, equipment_count
            FROM analytics.charging_by_kba_district_2026_09_30
            ORDER BY kba_district_code
            """,
        )
        require(len(regional_rows) == EXPECTED["kba_regions"], f"Regional analytics rows: {len(regional_rows)}")
        require(
            len({row["kba_district_code"] for row in regional_rows}) == EXPECTED["kba_regions"],
            "Duplicate KBA code in regional analytics view",
        )
        require(
            sum(parse_int(row["charging_point_count"], "regional charging points") for row in regional_rows)
            == EXPECTED["charging_points"],
            "Regional charging points do not reconcile",
        )
        regional_by_code = {row["kba_district_code"]: row for row in regional_rows}

        kba_rows = query_dicts(
            conn,
            """
            SELECT reference_date, district_code, district_name, state_name, bev_cars
            FROM core.kba_district_ev_stock
            ORDER BY reference_date, district_code
            """,
        )
        require(len(kba_rows) == EXPECTED["combined_rows"], f"KBA district/date rows: {len(kba_rows)}")
        keys = [(row["reference_date"], row["district_code"]) for row in kba_rows]
        require(len(set(keys)) == len(keys), "Duplicate KBA district/date key")
        require(all(KBA_CODE_RE.fullmatch(row["district_code"] or "") for row in kba_rows), "Invalid KBA code shape")
        require(set(row["reference_date"] for row in kba_rows) == set(KBA_REFERENCE_DATES), "Unexpected KBA dates")
        by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in kba_rows:
            by_code[row["district_code"]].append(row)
        require(len(by_code) == EXPECTED["kba_regions"], "Unexpected distinct KBA code count")
        require(all(len(rows) == len(KBA_REFERENCE_DATES) for rows in by_code.values()), "KBA code/date coverage gap")
        july_rows = [row for row in kba_rows if row["reference_date"] == KBA_REFERENCE_DATES[-1]]
        require(len(july_rows) == EXPECTED["kba_regions"], "July KBA row count mismatch")
        require(sum(parse_int(row["bev_cars"], "July BEVs") for row in july_rows) == EXPECTED["july_bev"], "July BEVs do not reconcile")
        require("07211" in regional_by_code, "Missing Trier regional row")
        require(parse_int(regional_by_code["07211"]["charging_point_count"], "Trier points") == 503, "Trier points changed")
        trier_july = next(row for row in july_rows if row["district_code"] == "07211")
        require(parse_int(trier_july["bev_cars"], "Trier July BEVs") == 7_869, "Trier July BEVs changed")
        return {
            "source_rows": source_key_rows,
            "regional_by_code": regional_by_code,
            "kba_by_code": dict(by_code),
            "baselines": {
                "equipment_rows": int(equipment_total[0]),
                "declared_points": int(equipment_total[1]),
                "charging_points": int(point_total),
                "bnetza_source_geographies": len(source_rows),
                "kba_regions": len(by_code),
                "combined_rows": len(kba_rows),
                "july_bev": sum(parse_int(row["bev_cars"], "July BEVs") for row in july_rows),
            },
        }
    finally:
        conn.close()


def audit_summary(
    path_a: Sequence[Mapping[str, Any]],
    path_b: Sequence[Mapping[str, Any]],
    bbsr: Mapping[str, Any],
    database: Mapping[str, Any],
    output_path: Path,
    fingerprints: Mapping[str, str],
) -> dict[str, Any]:
    path_a_statuses = ("VERIFIED_COMPATIBLE", "CONDITIONAL_VINTAGE", "MIXED", "UNRESOLVED", "CONFLICTING")
    path_b_statuses = ("EXACT", "HOMOGENEOUS_COMPOSITE", "MIXED", "VINTAGE_CONFLICT", "UNRESOLVED", "CONFLICTING")
    require(sum(parse_int(row["equipment_rows"], "Path A equipment") for row in path_a) == EXPECTED["equipment_rows"], "Path A equipment denominator failed")
    require(sum(parse_int(row["charging_point_total"], "Path A points") for row in path_a) == EXPECTED["charging_points"], "Path A point denominator failed")
    require(sum(parse_int(row["charging_point_total"], "Path B points") for row in path_b) == EXPECTED["charging_points"], "Path B point denominator failed")
    require(sum(parse_int(row["july_2026_bev_cars"], "Path B July BEVs") for row in path_b) == EXPECTED["july_bev"], "Path B BEV denominator failed")
    require(
        sum(1 for row in path_b if row["strict_bbsr_classification_supported"] == "yes") == 0,
        "A strict Path B BBSR classification was unexpectedly promoted",
    )
    path_a_coverage = coverage_by_status(
        path_a,
        path_a_statuses,
        EXPECTED["bnetza_source_geographies"],
        denominator_equipment=EXPECTED["equipment_rows"],
    )
    path_b_coverage = coverage_by_status(
        path_b,
        path_b_statuses,
        EXPECTED["kba_regions"],
        denominator_points=EXPECTED["charging_points"],
        denominator_bev=EXPECTED["july_bev"],
    )
    require(sum(item["regions"] for item in path_a_coverage.values()) == EXPECTED["bnetza_source_geographies"], "Path A region statuses do not reconcile")
    require(sum(item["equipment_rows"] for item in path_a_coverage.values()) == EXPECTED["equipment_rows"], "Path A equipment statuses do not reconcile")
    require(sum(item["charging_points"] for item in path_a_coverage.values()) == EXPECTED["charging_points"], "Path A point statuses do not reconcile")
    require(sum(item["regions"] for item in path_b_coverage.values()) == EXPECTED["kba_regions"], "Path B region statuses do not reconcile")
    require(sum(item["charging_points"] for item in path_b_coverage.values()) == EXPECTED["charging_points"], "Path B point statuses do not reconcile")
    require(sum(item.get("july_bev_cars", 0) for item in path_b_coverage.values()) == EXPECTED["july_bev"], "Path B BEV statuses do not reconcile")
    verified_a = path_a_coverage["VERIFIED_COMPATIBLE"]
    strict_b = path_b_coverage["EXACT"]["regions"] + path_b_coverage["HOMOGENEOUS_COMPOSITE"]["regions"]
    return {
        "validation": "PASS",
        "output": relative_or_absolute(output_path),
        "audit_scope": "read_only_two_path_BBSR_compatibility_investigation",
        "baselines": database["baselines"] | {
            "bbsr_rows": EXPECTED["bbsr_rows"],
            "bbsr_kreisregions": EXPECTED["bbsr_kreisregions"],
        },
        "bbsr": {
            "rows": EXPECTED["bbsr_rows"],
            "kreisregions": EXPECTED["bbsr_kreisregions"],
            "multi_kreisregions": EXPECTED["bbsr_multi_kreisregions"],
        },
        "path_a": {
            "status_counts": dict(sorted(Counter(row["audit_status"] for row in path_a).items())),
            "coverage_by_status": path_a_coverage,
            "verified_districts": verified_a["regions"],
            "verified_equipment_pct": verified_a["equipment_rows_pct"],
            "verified_charging_point_pct": verified_a["charging_points_pct"],
            "charging_only_descriptive_feasible": verified_a["regions"] > 0,
        },
        "path_b": {
            "status_counts": dict(sorted(Counter(row["audit_status"] for row in path_b).items())),
            "coverage_by_status": path_b_coverage,
            "strict_verified_regions": strict_b,
            "strict_verified_charging_point_pct": round(
                (path_b_coverage["EXACT"]["charging_points"] + path_b_coverage["HOMOGENEOUS_COMPOSITE"]["charging_points"])
                / EXPECTED["charging_points"]
                * 100,
                6,
            ),
            "strict_verified_july_bev_pct": round(
                (path_b_coverage["EXACT"].get("july_bev_cars", 0) + path_b_coverage["HOMOGENEOUS_COMPOSITE"].get("july_bev_cars", 0))
                / EXPECTED["july_bev"]
                * 100,
                6,
            ),
            "prefix_screen_intersection_count": 399,
            "production_bbsr_classification": "NO-GO",
        },
        "source_fingerprints": dict(sorted(fingerprints.items())),
        "official_sources": OFFICIAL_SOURCE_URLS,
    }


def write_audit_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in AUDIT_COLUMNS})


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--bbsr", type=Path, default=DEFAULT_BBSR)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--prior-audit", type=Path, default=DEFAULT_PRIOR_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    database_path = resolve_path(args.database)
    bbsr_path = resolve_path(args.bbsr)
    crosswalk_path = resolve_path(args.crosswalk)
    prior_audit_path = resolve_path(args.prior_audit)
    output_path = resolve_path(args.output)
    try:
        bbsr_rows = read_csv_rows(bbsr_path, BBSR_COLUMNS)
        bbsr = validate_bbsr(bbsr_rows)
        crosswalk_rows = read_csv_rows(crosswalk_path, CROSSWALK_COLUMNS)
        crosswalk = validate_crosswalk(crosswalk_rows)
        prior_audit = read_prior_audit(prior_audit_path)
        database = load_database(database_path, crosswalk_rows)
        path_a = build_path_a(database["source_rows"], crosswalk, bbsr)
        path_b = build_path_b(database, crosswalk, bbsr, prior_audit)
        all_rows = sorted(path_a + path_b, key=lambda row: (row["path"], row["source_record_key"]))
        require(len(all_rows) == EXPECTED["bnetza_source_geographies"] + EXPECTED["kba_regions"], "Combined audit row count mismatch")
        write_audit_csv(output_path, all_rows)
        fingerprints = {
            "bbsr_csv_sha256": sha256(bbsr_path),
            "crosswalk_csv_sha256": sha256(crosswalk_path),
            "duckdb_sha256": sha256(database_path),
            "prior_batch11_audit_sha256": sha256(prior_audit_path),
        }
        summary = audit_summary(path_a, path_b, bbsr, database, output_path, fingerprints)
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (AuditError, OSError, ValueError) as exc:
        print(f"Batch 12 audit failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
