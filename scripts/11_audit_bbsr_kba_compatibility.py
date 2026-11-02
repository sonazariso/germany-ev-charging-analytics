#!/usr/bin/env python3
"""Audit BBSR four-category compatibility with KBA registration regions.

This is a read-only, non-operational audit.  It deliberately does not create
an operational KBA-to-BBSR bridge, modify the existing Crosswalk, or write to
DuckDB.  The default output is an audit CSV under ``reports/`` so every KBA
registration region remains visible, including regions whose BBSR candidate
is only a five-digit prefix screen.

Run from the repository root:

    .venv/bin/python scripts/11_audit_bbsr_kba_compatibility.py

The script uses the existing Python environment and opens DuckDB with
``read_only=True``.  It prints a deterministic JSON summary and writes a
deterministic, clearly non-operational audit output.
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
except ImportError as exc:  # pragma: no cover - exercised only outside the venv
    raise SystemExit("duckdb is required; use the existing project environment") from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_BBSR = ROOT / "data/reference/bbsr_settlement_types_2025.csv"
DEFAULT_CROSSWALK = ROOT / "data/reference/bnetza_kba_district_crosswalk_2026.csv"
DEFAULT_OUTPUT = ROOT / "reports/batch11_bbsr_kba_compatibility_audit.csv"

SOURCE_ID = "bnetza_charging_2026_09_30"
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
KBA_DATES = (
    dt.date(2026, 1, 1),
    dt.date(2026, 4, 1),
    dt.date(2026, 7, 1),
)
KBA_CODE_RE = re.compile(r"^[0-9]{5}$")
BBSR_CODE_RE = re.compile(r"^[0-9]{8}$")

EXPECTED = {
    "equipment_rows": 117_662,
    "charging_points": 211_253,
    "declared_points": 211_253,
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
    "kba_reference_product",
    "kba_reference_dates",
    "kba_district_code",
    "kba_district_name",
    "kba_state_name",
    "kba_admin_type",
    "bnetza_source_id",
    "bnetza_source_geography_rows",
    "bnetza_component_names",
    "crosswalk_evidence_types",
    "bbsr_prefix_candidate_codes",
    "bbsr_prefix_candidate_names",
    "bbsr_prefix_candidate_types",
    "bbsr_component_codes",
    "bbsr_component_names",
    "bbsr_component_types",
    "bbsr_component_kreisregion_codes",
    "bbsr_component_kreisregion_names",
    "bbsr_component_count",
    "bbsr_components_complete",
    "bbsr_components_share_type",
    "kreisregion_component_counts",
    "geographic_coverage_evidence",
    "administrative_boundary_alignment",
    "source_vintage_assessment",
    "allocation_or_estimation_required",
    "evidence_confidence",
    "audit_status",
    "issue_flags",
    "audit_reason",
    "january_2026_bev_cars",
    "april_2026_bev_cars",
    "july_2026_bev_cars",
    "charging_point_total",
)


class AuditError(RuntimeError):
    """Raised when a source or audit acceptance check fails."""


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
        require(
            column in actual,
            f"{qualified_name} is missing required field {column!r}",
        )
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


def parse_int(value: Any, label: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise AuditError(f"Expected integer for {label}: {value!r}") from exc


def normalise_text(value: str) -> str:
    value = (value or "").replace("ß", "ss")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = value.upper()
    return re.sub(r"[^A-Z0-9]+", "", value)


def administrative_identity_key(value: str) -> str:
    result = normalise_text(value)
    for token in (
        "KREISFREIESTADT",
        "KREISFREIE",
        "STADTKREIS",
        "LANDKREIS",
        "KREIS",
        "STADT",
    ):
        result = result.replace(token, "")
    return result


def join_values(values: Iterable[str]) -> str:
    return ";".join(sorted({value for value in values if value}))


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

    administrative_codes = [row["administrative_district_code"] for row in rows]
    require(
        all(BBSR_CODE_RE.fullmatch(code or "") for code in administrative_codes),
        "BBSR administrative codes must remain eight-character strings",
    )
    require(
        len(set(administrative_codes)) == len(administrative_codes),
        "Duplicate BBSR administrative district key",
    )
    require(
        all(
            row["federal_state_code"]
            and row["federal_state_name"]
            and row["kreisregion_code"]
            and row["kreisregion_name"]
            and row["settlement_type_code"]
            and row["settlement_type_name_de"]
            for row in rows
        ),
        "Missing BBSR geographic or classification key",
    )
    require(
        all(
            BBSR_CODE_RE.fullmatch(row["kreisregion_code"] or "")
            and re.fullmatch(r"^[0-9]{2}$", row["federal_state_code"] or "")
            for row in rows
        ),
        "Invalid BBSR state or Kreisregion code shape",
    )
    require(
        all(row["settlement_type_code"] in BBSR_ALLOWED_TYPES for row in rows),
        "BBSR classification outside compact four-category domain",
    )
    require(
        all(
            BBSR_TYPE_LABELS[row["settlement_type_code"]]
            == row["settlement_type_name_de"]
            for row in rows
        ),
        "BBSR classification code/label inconsistency",
    )

    by_kreisregion: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_kreisregion[row["kreisregion_code"]].append(row)
    require(
        len(by_kreisregion) == EXPECTED["bbsr_kreisregions"],
        f"BBSR Kreisregion keys: {len(by_kreisregion)}",
    )
    for group_code, group in by_kreisregion.items():
        require(
            len({row["kreisregion_name"] for row in group}) == 1,
            f"Inconsistent Kreisregion name for {group_code}",
        )
    multi_groups = {
        code: group for code, group in by_kreisregion.items() if len(group) > 1
    }
    require(
        len(multi_groups) == EXPECTED["bbsr_multi_kreisregions"],
        f"BBSR multi-district Kreisregion groups: {len(multi_groups)}",
    )
    mixed_kreisregions = {
        code: group
        for code, group in by_kreisregion.items()
        if len({row["settlement_type_code"] for row in group}) > 1
    }
    require(
        not mixed_kreisregions,
        "BBSR Kreisregion contains multiple compact classification codes: "
        + ", ".join(sorted(mixed_kreisregions)),
    )
    type_counts = Counter(row["settlement_type_code"] for row in rows)
    require(type_counts == Counter({"1": 68, "2": 131, "3": 98, "4": 103}),
            f"Unexpected BBSR type counts: {type_counts}")

    return {
        "by_admin_code": {row["administrative_district_code"]: row for row in rows},
        "by_prefix": _group_by_prefix(rows),
        "by_name": _group_by_name(rows),
        "by_kreisregion": by_kreisregion,
        "multi_kreisregions": multi_groups,
        "mixed_kreisregions": mixed_kreisregions,
        "type_counts": dict(sorted(type_counts.items())),
    }


def _group_by_prefix(rows: Iterable[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        result[row["administrative_district_code"][:5]].append(row)
    return dict(result)


def _group_by_name(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    result: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        result[(row["federal_state_name"], administrative_identity_key(row["administrative_district_name"]))].append(row)
    return dict(result)


def validate_crosswalk(rows: list[dict[str, str]]) -> dict[str, Any]:
    require(len(rows) == EXPECTED["crosswalk_rows"], f"Crosswalk rows: {len(rows)}")
    source_keys = [
        (row["bnetza_state_name"], row["bnetza_district_name"]) for row in rows
    ]
    require(len(set(source_keys)) == len(source_keys), "Duplicate Crosswalk source key")
    kba_codes = [row["kba_district_code"] for row in rows]
    require(all(KBA_CODE_RE.fullmatch(code or "") for code in kba_codes), "Invalid KBA code")
    require(set(code for code in kba_codes if kba_codes.count(code) > 1) == {"07211"},
            "Unexpected duplicate KBA target code")
    require(kba_codes.count("07211") == 2, "Trier shared code is not represented twice")
    require(all(row["mapping_status"] == "mapped" for row in rows), "Unmapped Crosswalk row")
    require(
        sum(row["verification_status"].startswith("provisional") for row in rows) == 24,
        "Unexpected Crosswalk provisional-row count",
    )
    require(
        all(row["bnetza_state_name"] == row["kba_state_name"] for row in rows),
        "Crosswalk contains a cross-state mapping",
    )
    by_kba: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_kba[row["kba_district_code"]].append(row)
    return {"by_kba": dict(by_kba), "source_keys": set(source_keys)}


def load_database(
    database: Path,
    crosswalk_rows: list[dict[str, str]],
) -> dict[str, Any]:
    require(database.is_file(), f"Missing DuckDB database: {database}")
    conn = duckdb.connect(str(database), read_only=True)
    try:
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
            "reference.bnetza_kba_district_crosswalk_2026",
            {
                "bnetza_source_id": "VARCHAR",
                "bnetza_state_name": "VARCHAR",
                "bnetza_district_name": "VARCHAR",
                "kba_district_code": "VARCHAR",
            },
        )
        require_db_columns(
            conn,
            "analytics.charging_by_kba_district_2026_09_30",
            {"kba_district_code": "VARCHAR", "charging_point_count": "BIGINT"},
        )
        require_db_columns(
            conn,
            "analytics.kba_district_charging_vs_bev_2026",
            {
                "kba_district_code": "VARCHAR",
                "kba_reference_date": "DATE",
                "bev_cars": "BIGINT",
                "charging_point_count": "BIGINT",
            },
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
            """
            SELECT COUNT(*)
            FROM core.charging_point
            WHERE source_id = ?
            """,
            [SOURCE_ID],
        ).fetchone()[0]
        require(int(equipment_total[0]) == EXPECTED["equipment_rows"],
                f"Equipment rows: {equipment_total[0]}")
        require(int(equipment_total[1]) == EXPECTED["declared_points"],
                f"Declared points: {equipment_total[1]}")
        require(int(point_total) == EXPECTED["charging_points"],
                f"Charging point rows: {point_total}")

        source_rows = query_dicts(
            conn,
            """
            SELECT state_name AS bnetza_state_name,
                   district_name AS bnetza_district_name,
                   COUNT(*) AS equipment_rows,
                   SUM(declared_point_count) AS declared_point_count
            FROM core.charging_equipment
            WHERE source_id = 'bnetza_charging_2026_09_30'
            GROUP BY state_name, district_name
            ORDER BY state_name, district_name
            """,
        )
        require(len(source_rows) == EXPECTED["crosswalk_rows"],
                f"BNetzA source geography rows: {len(source_rows)}")
        require(
            {
                (row["bnetza_state_name"], row["bnetza_district_name"])
                for row in source_rows
            }
            == {
                (row["bnetza_state_name"], row["bnetza_district_name"])
                for row in crosswalk_rows
            },
            "Crosswalk source keys do not equal current BNetzA source keys",
        )

        db_crosswalk = query_dicts(
            conn,
            """
            SELECT bnetza_source_id, bnetza_state_name, bnetza_district_name,
                   bnetza_admin_type, kba_state_name, kba_district_code,
                   kba_district_name, kba_admin_type, mapping_method,
                   verification_status
            FROM reference.bnetza_kba_district_crosswalk_2026
            ORDER BY bnetza_state_name, bnetza_district_name
            """,
        )
        require(len(db_crosswalk) == EXPECTED["crosswalk_rows"],
                f"DuckDB Crosswalk rows: {len(db_crosswalk)}")
        require(
            {row["bnetza_source_id"] for row in db_crosswalk} == {SOURCE_ID},
            "Unexpected BNetzA source ID in deployed Crosswalk",
        )
        require(
            {
                (
                    row["bnetza_state_name"],
                    row["bnetza_district_name"],
                    row["kba_district_code"],
                )
                for row in db_crosswalk
            }
            == {
                (
                    row["bnetza_state_name"],
                    row["bnetza_district_name"],
                    row["kba_district_code"],
                )
                for row in crosswalk_rows
            },
            "CSV and deployed Crosswalk identity differs",
        )

        kba_rows = query_dicts(
            conn,
            """
            SELECT reference_date, district_code, district_name, state_name,
                   passenger_cars, bev_cars, phev_cars
            FROM core.kba_district_ev_stock
            ORDER BY reference_date, district_code
            """,
        )
        require(len(kba_rows) == EXPECTED["combined_rows"],
                f"KBA district stock rows: {len(kba_rows)}")
        kba_keys = [
            (row["reference_date"], row["district_code"]) for row in kba_rows
        ]
        require(len(set(kba_keys)) == len(kba_keys), "Duplicate KBA code/date key")
        require(all(KBA_CODE_RE.fullmatch(row["district_code"] or "") for row in kba_rows),
                "KBA district codes lost their five-character string shape")
        require(
            set(row["reference_date"] for row in kba_rows) == set(KBA_DATES),
            "Unexpected KBA reference-date set",
        )
        date_counts = Counter(row["reference_date"] for row in kba_rows)
        require(
            all(count == EXPECTED["kba_regions"] for count in date_counts.values()),
            f"KBA district count by date: {date_counts}",
        )
        kba_by_code_date = {
            (row["district_code"], row["reference_date"]): row for row in kba_rows
        }
        kba_by_code = {
            code: [
                kba_by_code_date[(code, reference_date)]
                for reference_date in KBA_DATES
            ]
            for code in sorted({row["district_code"] for row in kba_rows})
        }
        require(len(kba_by_code) == EXPECTED["kba_regions"],
                f"Distinct KBA regions: {len(kba_by_code)}")
        crosswalk_codes = {row["kba_district_code"] for row in crosswalk_rows}
        require(
            crosswalk_codes == set(kba_by_code),
            "Crosswalk KBA keys do not equal the 400 current KBA region keys",
        )

        regional_rows = query_dicts(
            conn,
            """
            SELECT kba_district_code, charging_point_count,
                   source_geography_rows, provisional_mapping_rows,
                   unmapped_source_geography_rows
            FROM analytics.charging_by_kba_district_2026_09_30
            ORDER BY kba_district_code
            """,
        )
        require(len(regional_rows) == EXPECTED["kba_regions"],
                f"Regional analytics rows: {len(regional_rows)}")
        require(
            len({row["kba_district_code"] for row in regional_rows})
            == EXPECTED["kba_regions"],
            "Duplicate KBA key in regional analytics view",
        )
        require(
            sum(int(row["charging_point_count"]) for row in regional_rows)
            == EXPECTED["charging_points"],
            "Regional charging-point total does not reconcile",
        )
        regional_by_code = {row["kba_district_code"]: row for row in regional_rows}

        combined_rows = query_dicts(
            conn,
            """
            SELECT kba_district_code, kba_reference_date, bev_cars,
                   charging_point_count
            FROM analytics.kba_district_charging_vs_bev_2026
            ORDER BY kba_district_code, kba_reference_date
            """,
        )
        require(len(combined_rows) == EXPECTED["combined_rows"],
                f"Combined analytics rows: {len(combined_rows)}")
        combined_keys = [
            (row["kba_district_code"], row["kba_reference_date"])
            for row in combined_rows
        ]
        require(len(set(combined_keys)) == len(combined_keys),
                "Duplicate combined KBA code/date key")
        july_combined = [
            row for row in combined_rows if row["kba_reference_date"] == KBA_DATES[-1]
        ]
        require(len(july_combined) == EXPECTED["kba_regions"],
                "Combined July KBA row count does not equal 400")
        require(
            sum(int(row["bev_cars"]) for row in july_combined) == EXPECTED["july_bev"],
            "July BEV total does not reconcile",
        )
        require(
            sum(int(row["charging_point_count"]) for row in july_combined)
            == EXPECTED["charging_points"],
            "July combined charging points duplicate or lose regions",
        )

        trier_regional = regional_by_code.get("07211")
        require(trier_regional is not None, "Missing Trier regional row")
        require(int(trier_regional["charging_point_count"]) == 503,
                "Trier charging points are not aggregated to 503")
        trier_july = next(
            row for row in july_combined if row["kba_district_code"] == "07211"
        )
        require(int(trier_july["bev_cars"]) == 7_869,
                "Trier July BEV stock is not 7,869")
        require(
            sum(
                1
                for row in combined_rows
                if row["kba_district_code"] == "07211"
            )
            == len(KBA_DATES),
            "Trier stock is duplicated by raw BNetzA source rows",
        )

        return {
            "kba_by_code": kba_by_code,
            "regional_by_code": regional_by_code,
            "source_rows": source_rows,
            "db_crosswalk": db_crosswalk,
            "baselines": {
                "equipment_rows": int(equipment_total[0]),
                "charging_points": int(point_total),
                "declared_points": int(equipment_total[1]),
                "crosswalk_rows": len(db_crosswalk),
                "kba_regions": len(kba_by_code),
                "combined_rows": len(combined_rows),
                "july_bev": sum(int(row["bev_cars"]) for row in july_combined),
            },
        }
    finally:
        conn.close()


def resolve_bbsr_component(
    source_row: Mapping[str, str],
    kba_code: str,
    bbsr: Mapping[str, Any],
) -> tuple[list[dict[str, str]], str]:
    state = source_row["bnetza_state_name"]
    name_key = (state, administrative_identity_key(source_row["bnetza_district_name"]))
    name_candidates = list(bbsr["by_name"].get(name_key, []))
    prefix_candidates = list(bbsr["by_prefix"].get(kba_code, []))

    if len(name_candidates) == 1:
        return name_candidates, "state_and_identity_name"
    if len(name_candidates) > 1:
        narrowed = [
            row for row in name_candidates
            if row["administrative_district_code"][:5] == kba_code
        ]
        if len(narrowed) == 1:
            return narrowed, "state_identity_plus_prefix_disambiguation"
        return name_candidates, "ambiguous_identity_name"
    if len(prefix_candidates) == 1:
        return prefix_candidates, "prefix_candidate_only"
    return prefix_candidates, "missing_or_ambiguous_component"


def classify_region(
    kba_code: str,
    kba_row: Mapping[str, Any],
    crosswalk_rows: Sequence[Mapping[str, str]],
    bbsr: Mapping[str, Any],
    regional_row: Mapping[str, Any],
) -> dict[str, Any]:
    source_rows = sorted(
        crosswalk_rows,
        key=lambda row: (row["bnetza_state_name"], row["bnetza_district_name"]),
    )
    components: dict[str, dict[str, str]] = {}
    resolutions: list[str] = []
    for source_row in source_rows:
        resolved, resolution = resolve_bbsr_component(source_row, kba_code, bbsr)
        resolutions.append(resolution)
        for row in resolved:
            components[row["administrative_district_code"]] = row

    prefix_candidates = sorted(
        bbsr["by_prefix"].get(kba_code, []),
        key=lambda row: row["administrative_district_code"],
    )
    component_rows = [components[code] for code in sorted(components)]
    component_types = sorted({row["settlement_type_code"] for row in component_rows})
    component_groups = sorted({row["kreisregion_code"] for row in component_rows})
    complete = bool(component_rows) and len(component_rows) == len(source_rows)
    source_methods = sorted({row["mapping_method"] for row in source_rows})
    source_verifications = sorted({row["verification_status"] for row in source_rows})

    # The input set contains no KBA-to-BBSR bridge whose code system and
    # effective geography are authoritative.  BBSR prefix candidates and the
    # existing local Crosswalk therefore cannot satisfy the EXACT rule.
    has_authoritative_bridge = False
    issue_flags: list[str] = []
    evidence_types: list[str] = []
    geographic_evidence = ""
    boundary_alignment = "not_established"
    vintage_assessment = (
        "BBSR 2025 versus KBA/BNetzA 2026; no known boundary change identified in local evidence"
    )
    allocation_required = "no_single_class_assignment_supported"
    confidence = "low_for_bbsr_assignment"

    if kba_code == "07211":
        status = "MIXED"
        geographic_evidence = "verified shared KBA registration region with two BBSR administrative identities"
        boundary_alignment = "not_equivalent_shared_registration_region"
        vintage_assessment = "Separate BBSR 2025 Trier rows; KBA 2026 combines the registration region"
        allocation_required = "yes_for_single_bbsr_class; no_allocation_applied"
        confidence = "high_for_mixed_exception"
        evidence_types.extend(
            ["shared_kba_registration_region", "two_verified_bbsr_components"]
        )
        issue_flags.extend(
            [
                "shared_kba_registration_region",
                "multiple_bbsr_components",
                "mixed_bbsr_classifications",
                "allocation_required_for_single_class",
                "no_authoritative_kba_bbsr_bridge",
            ]
        )
        reason = (
            "KBA 07211 contains Trier city (BBSR type 1) and Trier-Saarburg "
            "(BBSR type 3); the combined July stock must not be allocated."
        )
    elif kba_code in {"06415", "06435"}:
        status = "VINTAGE_CONFLICT"
        geographic_evidence = "dated Hanau/Main-Kinzig separation is present in KBA and BNetzA"
        boundary_alignment = "not_equivalent_across_2025_2026_boundary_vintages"
        vintage_assessment = (
            "Hanau became independent on 2026-01-01; BBSR geographic stand 2025-12-31 predates the change"
        )
        allocation_required = "no_estimation_or_inheritance_allowed"
        confidence = "high_for_vintage_exception"
        evidence_types.append("hanau_main_kinzig_boundary_change")
        issue_flags.extend(
            [
                "boundary_vintage_conflict",
                "no_post_change_bbsr_reference",
                "no_estimation_or_allocation",
            ]
        )
        if kba_code == "06415":
            issue_flags.append("missing_bbsr_hanau_row")
            reason = (
                "KBA Hanau is present after the 2026 separation, but the BBSR 2025 "
                "reference has no Hanau row; Main-Kinzig type 2 cannot be inherited."
            )
        else:
            issue_flags.append("bbsr_main_kinzig_pre_change_boundary")
            reason = (
                "The BBSR Main-Kinzig type 2 row predates Hanau's separation and "
                "cannot be treated as an exact type for the current KBA remainder."
            )
    else:
        if source_methods == ["explicit_provisional_alias"]:
            evidence_types.append("row_level_kba_destatis_identity_evidence")
            issue_flags.append("operational_crosswalk_alias_remains_provisional")
            confidence = "medium_for_source_identity_low_for_bbsr_assignment"
        elif source_methods == ["explicit_state_city_naming_convention"]:
            evidence_types.append("explicit_kba_state_city_naming_convention")
            issue_flags.append("naming_convention_not_boundary_bridge")
        else:
            evidence_types.append("local_kba_bnetza_state_type_name_crosswalk")
            confidence = "low_for_bbsr_assignment"
        if prefix_candidates:
            evidence_types.append("bbsr_five_digit_prefix_screen")
            issue_flags.append("prefix_match_not_geographic_equivalence")
        if component_rows:
            evidence_types.append("component_identity_candidate")
        else:
            issue_flags.append("bbsr_component_unresolved")
        issue_flags.extend(
            [
                "no_authoritative_kba_bbsr_bridge",
                "not_safe_for_single_bbsr_class",
            ]
        )
        status = "UNRESOLVED"
        geographic_evidence = (
            "KBA/BNetzA identity evidence and, where present, a BBSR prefix candidate; "
            "equivalent geographic coverage is not authoritative"
        )
        reason = (
            "A BBSR administrative candidate may be visible, but the available sources "
            "do not publish a dated KBA-to-BBSR equivalence."
        )

    if len(component_rows) > 1:
        issue_flags.append("multiple_bbsr_components")
    if len(component_types) > 1 and status != "MIXED":
        status = "CONFLICTING"
        issue_flags.append("component_type_conflict")
        reason = "Resolved component evidence contains incompatible BBSR types outside the Trier rule."
    if len(component_types) > 1 and status == "MIXED":
        issue_flags.append("component_types_not_homogeneous")
    if len(component_rows) > 1 and len(component_types) == 1 and status == "UNRESOLVED":
        issue_flags.append("homogeneous_components_but_bridge_missing")
    if not has_authoritative_bridge and status == "UNRESOLVED":
        issue_flags.append("exact_status_not_permitted_without_authoritative_bridge")

    # A repeated flag is a data-quality smell in the audit itself; de-duplicate
    # while retaining deterministic lexical order.
    issue_flags = sorted(set(issue_flags))
    evidence_types = sorted(set(evidence_types))
    component_rows = sorted(component_rows, key=lambda row: row["administrative_district_code"])

    date_rows = {
        row["reference_date"]: row for row in kba_row["date_rows"]
    }
    return {
        "audit_output_scope": "NON_OPERATIONAL_BBSR_KBA_COMPATIBILITY_AUDIT",
        "audit_version": "batch11-2026-11-02-strict-evidence",
        "kba_reference_product": "KBA FZ 27.15",
        "kba_reference_dates": ";".join(date.isoformat() for date in KBA_DATES),
        "kba_district_code": kba_code,
        "kba_district_name": kba_row["date_rows"][-1]["district_name"],
        "kba_state_name": kba_row["date_rows"][-1]["state_name"],
        "kba_admin_type": join_values(row["kba_admin_type"] for row in source_rows),
        "bnetza_source_id": SOURCE_ID,
        "bnetza_source_geography_rows": len(source_rows),
        "bnetza_component_names": join_values(
            row["bnetza_district_name"] for row in source_rows
        ),
        "crosswalk_evidence_types": join_values(evidence_types),
        "bbsr_prefix_candidate_codes": join_values(
            row["administrative_district_code"] for row in prefix_candidates
        ),
        "bbsr_prefix_candidate_names": join_values(
            row["administrative_district_name"] for row in prefix_candidates
        ),
        "bbsr_prefix_candidate_types": join_values(
            f"{row['settlement_type_code']}:{row['settlement_type_name_de']}"
            for row in prefix_candidates
        ),
        "bbsr_component_codes": join_values(
            row["administrative_district_code"] for row in component_rows
        ),
        "bbsr_component_names": join_values(
            row["administrative_district_name"] for row in component_rows
        ),
        "bbsr_component_types": join_values(
            f"{row['settlement_type_code']}:{row['settlement_type_name_de']}"
            for row in component_rows
        ),
        "bbsr_component_kreisregion_codes": join_values(
            row["kreisregion_code"] for row in component_rows
        ),
        "bbsr_component_kreisregion_names": join_values(
            row["kreisregion_name"] for row in component_rows
        ),
        "bbsr_component_count": len(component_rows),
        "bbsr_components_complete": "yes" if complete else "no",
        "bbsr_components_share_type": (
            "yes" if len(component_types) == 1 and component_rows else "no"
            if component_rows
            else "not_observed"
        ),
        "kreisregion_component_counts": join_values(
            f"{row['kreisregion_code']}:{len(bbsr['by_kreisregion'][row['kreisregion_code']])}"
            for row in component_rows
        ),
        "geographic_coverage_evidence": geographic_evidence,
        "administrative_boundary_alignment": boundary_alignment,
        "source_vintage_assessment": vintage_assessment,
        "allocation_or_estimation_required": allocation_required,
        "evidence_confidence": confidence,
        "audit_status": status,
        "issue_flags": ";".join(issue_flags),
        "audit_reason": reason,
        "january_2026_bev_cars": int(date_rows[KBA_DATES[0]]["bev_cars"]),
        "april_2026_bev_cars": int(date_rows[KBA_DATES[1]]["bev_cars"]),
        "july_2026_bev_cars": int(date_rows[KBA_DATES[2]]["bev_cars"]),
        "charging_point_total": int(regional_row["charging_point_count"]),
    }


def build_audit(
    bbsr: Mapping[str, Any],
    crosswalk: Mapping[str, Any],
    database: Mapping[str, Any],
) -> list[dict[str, Any]]:
    audit_rows = []
    for code in sorted(database["kba_by_code"]):
        audit_rows.append(
            classify_region(
                code,
                {"date_rows": database["kba_by_code"][code]},
                crosswalk["by_kba"].get(code, []),
                bbsr,
                database["regional_by_code"][code],
            )
        )
    require(len(audit_rows) == EXPECTED["kba_regions"],
            f"Audit rows: {len(audit_rows)}")
    require(
        len({row["kba_district_code"] for row in audit_rows}) == EXPECTED["kba_regions"],
        "Duplicate or missing audit KBA keys",
    )
    require(
        {row["kba_district_code"] for row in audit_rows}
        == set(database["kba_by_code"]),
        "Audit output does not cover every KBA region",
    )
    return audit_rows


def coverage_summary(
    audit_rows: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for status in (
        "EXACT",
        "HOMOGENEOUS_COMPOSITE",
        "MIXED",
        "VINTAGE_CONFLICT",
        "UNRESOLVED",
        "CONFLICTING",
    ):
        rows = [row for row in audit_rows if row["audit_status"] == status]
        result[status] = {
            "regions": len(rows),
            "regions_pct": round(len(rows) / EXPECTED["kba_regions"] * 100, 6),
            "charging_points": sum(int(row["charging_point_total"]) for row in rows),
            "charging_points_pct": round(
                sum(int(row["charging_point_total"]) for row in rows)
                / EXPECTED["charging_points"]
                * 100,
                6,
            ),
            "july_bev_cars": sum(int(row["july_2026_bev_cars"]) for row in rows),
            "july_bev_pct": round(
                sum(int(row["july_2026_bev_cars"]) for row in rows)
                / EXPECTED["july_bev"]
                * 100,
                6,
            ),
        }
    return result


def write_audit_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in AUDIT_COLUMNS})


def audit_summary(
    audit_rows: Sequence[Mapping[str, Any]],
    bbsr: Mapping[str, Any],
    database: Mapping[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    statuses = Counter(row["audit_status"] for row in audit_rows)
    expected_statuses = {
        "EXACT",
        "HOMOGENEOUS_COMPOSITE",
        "MIXED",
        "VINTAGE_CONFLICT",
        "UNRESOLVED",
        "CONFLICTING",
    }
    require(set(statuses) <= expected_statuses, f"Unexpected audit status: {statuses}")
    require(sum(statuses.values()) == EXPECTED["kba_regions"], "Status totals do not reconcile")
    coverage = coverage_summary(audit_rows)
    require(sum(item["regions"] for item in coverage.values()) == EXPECTED["kba_regions"],
            "Coverage region totals do not reconcile")
    require(sum(item["charging_points"] for item in coverage.values()) == EXPECTED["charging_points"],
            "Coverage charging-point totals do not reconcile")
    require(sum(item["july_bev_cars"] for item in coverage.values()) == EXPECTED["july_bev"],
            "Coverage July BEV totals do not reconcile")
    return {
        "validation": "PASS",
        "output": str(output_path.relative_to(ROOT) if output_path.is_relative_to(ROOT) else output_path),
        "baselines": database["baselines"],
        "bbsr": {
            "rows": EXPECTED["bbsr_rows"],
            "kreisregions": EXPECTED["bbsr_kreisregions"],
            "multi_kreisregions": EXPECTED["bbsr_multi_kreisregions"],
            "mixed_kreisregions": len(bbsr["mixed_kreisregions"]),
            "type_counts": bbsr["type_counts"],
        },
        "status_counts": dict(sorted(statuses.items())),
        "coverage_by_status": coverage,
        "operational_bbsr_classification_coverage": coverage["EXACT"]["regions"]
        + coverage["HOMOGENEOUS_COMPOSITE"]["regions"],
        "operational_bbsr_classification_point_coverage_pct": round(
            (
                coverage["EXACT"]["charging_points"]
                + coverage["HOMOGENEOUS_COMPOSITE"]["charging_points"]
            )
            / EXPECTED["charging_points"]
            * 100,
            6,
        ),
        "operational_bbsr_classification_july_bev_coverage_pct": round(
            (
                coverage["EXACT"]["july_bev_cars"]
                + coverage["HOMOGENEOUS_COMPOSITE"]["july_bev_cars"]
            )
            / EXPECTED["july_bev"]
            * 100,
            6,
        ),
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--bbsr", type=Path, default=DEFAULT_BBSR)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    database_path = resolve_path(args.database)
    bbsr_path = resolve_path(args.bbsr)
    crosswalk_path = resolve_path(args.crosswalk)
    output_path = resolve_path(args.output)
    try:
        bbsr_rows = read_csv_rows(bbsr_path, BBSR_COLUMNS)
        bbsr = validate_bbsr(bbsr_rows)
        crosswalk_rows = read_csv_rows(crosswalk_path, CROSSWALK_COLUMNS)
        crosswalk = validate_crosswalk(crosswalk_rows)
        database = load_database(database_path, crosswalk_rows)
        audit_rows = build_audit(bbsr, crosswalk, database)
        write_audit_csv(output_path, audit_rows)
        summary = audit_summary(audit_rows, bbsr, database, output_path)
        summary["source_fingerprints"] = {
            "bbsr_csv_sha256": sha256(bbsr_path),
            "crosswalk_csv_sha256": sha256(crosswalk_path),
            "duckdb_sha256": sha256(database_path),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (AuditError, OSError, ValueError) as exc:
        print(f"Batch 11 audit failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
