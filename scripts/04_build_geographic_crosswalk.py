#!/usr/bin/env python3
"""Build and validate the versioned BNetzA-to-KBA district crosswalk.

The script reads the existing DuckDB in read-only mode.  It does not create
DuckDB tables or views and does not modify source data.  The output CSV keeps
one row for every distinct BNetzA state/district combination, including both
Trier rows, while KBA vehicle stock is validated only after charging metrics
are aggregated to the KBA code.

Run from the project root with the project virtual environment:

    .venv/bin/python scripts/04_build_geographic_crosswalk.py
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_OUTPUT = ROOT / "data/reference/bnetza_kba_district_crosswalk_2026.csv"
DEFAULT_REPORT = ROOT / "reports/batch03_crosswalk_validation.md"

BNETZA_REFERENCE_DATE = "2026-09-30"
KBA_REFERENCE_DATE = "2026-07-01"
CROSSWALK_VERSION = "2026-07-01"
KBA_EVIDENCE_URL = (
    "https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/"
    "fz27_202607.xlsx?__blob=publicationFile&v=3"
)

EXPECTED_BNETZA_COMBINATIONS = 401
EXPECTED_KBA_DISTRICTS = 400
EXPECTED_EQUIPMENT_ROWS = 117_662
EXPECTED_CHARGING_POINTS = 211_253


@dataclass(frozen=True)
class Rule:
    """An explicit mapping rule that requires a local-snapshot validation."""

    code: str
    expected_kba_name: str
    method: str
    verification_status: str
    note: str
    allows_type_difference: bool = False


# These are candidate aliases, not official administrative proof.  They are
# deliberately keyed by the full observed BNetzA state and district labels so
# that an ambiguous name can never be resolved from a normalized name alone.
PROVISIONAL_ALIASES: dict[tuple[str, str], Rule] = {
    ("Baden-Württemberg", "Stadtkreis Freiburg im Breisgau"): Rule(
        "08311",
        "FREIBURG I.BREISG.STADT",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "BNetzA uses Stadtkreis Freiburg im Breisgau; KBA uses the abbreviated city label.",
    ),
    ("Bayern", "Landkreis Neustadt a.d. Aisch-Bad Windsheim"): Rule(
        "09575",
        "NEUSTADT/AISCH-WINDSHEIM",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA shortens the district name and uses a slash in the local label.",
    ),
    ("Bayern", "Landkreis Wunsiedel i. Fichtelgebirge"): Rule(
        "09479",
        "WUNSIEDEL I.FICHTELGEB.",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA abbreviates both the in-name and Fichtelgebirge components.",
    ),
    ("Brandenburg", "Kreisfreie Stadt Brandenburg an der Havel"): Rule(
        "12051",
        "BRANDENBURG/HAVEL,STADT",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA uses the slash form Brandenburg/Havel.",
    ),
    ("Hessen", "Landkreis Kassel"): Rule(
        "06633",
        "KASSEL, LAND",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "The state contains both Kassel city and Kassel county; the county type selects 06633.",
    ),
    ("Mecklenburg-Vorpommern", "Landkreis Mecklenburgische Seenplatte"): Rule(
        "13071",
        "MECKLENBURGISCHE SEENPLA",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "The July KBA worksheet truncates the district display name.",
    ),
    ("Niedersachsen", "Kreisfreie Stadt Oldenburg (Oldb)"): Rule(
        "03403",
        "OLDENBURG(OLDENB),STADT",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "The city and county both use Oldenburg in their labels; city type selects 03403.",
    ),
    ("Niedersachsen", "Landkreis Oldenburg"): Rule(
        "03458",
        "OLDENBURG(OLDENBURG)",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "The city and county both use Oldenburg in their labels; county type selects 03458.",
    ),
    ("Niedersachsen", "Landkreis Region Hannover"): Rule(
        "03241",
        "HANNOVER",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "BNetzA includes the administrative-type prefix; KBA reports Hannover as the district label.",
    ),
    ("Nordrhein-Westfalen", "Kreis Rhein-Kreis Neuss"): Rule(
        "05162",
        "NEUSS",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA uses the shorter district label Neuss.",
    ),
    ("Nordrhein-Westfalen", "Kreis Rheinisch-Bergischer Kreis"): Rule(
        "05378",
        "RHEIN.-BERGISCHER KREIS",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA abbreviates Rheinisch to Rhein. in the district label.",
    ),
    ("Nordrhein-Westfalen", "Kreis Städteregion Aachen"): Rule(
        "05334",
        "AACHEN, STAEDTEREGION",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA reverses the order of Aachen and Städteregion.",
    ),
    ("Nordrhein-Westfalen", "Kreisfreie Stadt Mülheim an der Ruhr"): Rule(
        "05117",
        "MUELHEIM A.D.RUHR,STADT",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA uses an abbreviated an der Ruhr form.",
    ),
    ("Rheinland-Pfalz", "Kreisfreie Stadt Landau in der Pfalz"): Rule(
        "07313",
        "LANDAU I.D.PFALZ,STADT",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA abbreviates in der Pfalz.",
    ),
    ("Rheinland-Pfalz", "Kreisfreie Stadt Ludwigshafen am Rhein"): Rule(
        "07314",
        "LUDWIGSHAFEN A.RH.,STADT",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA abbreviates am Rhein.",
    ),
    ("Rheinland-Pfalz", "Kreisfreie Stadt Neustadt an der Weinstraße"): Rule(
        "07316",
        "NEUSTADT A.D.WSTR.,STADT",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA abbreviates an der Weinstraße.",
    ),
    ("Rheinland-Pfalz", "Landkreis Altenkirchen (Westerwald)"): Rule(
        "07132",
        "ALTENKIRCHEN(WESTWLD.)",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA abbreviates Westerwald and removes the display-space before the parenthesis.",
    ),
    ("Saarland", "Landkreis Regionalverband Saarbrücken"): Rule(
        "10041",
        "SAARBRUECKEN,STADTVERB.",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "BNetzA calls the regional association a Landkreis; KBA uses the Stadtverband label.",
    ),
    ("Saarland", "Landkreis St. Wendel"): Rule(
        "10046",
        "SANKT WENDEL",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA expands St. to Sankt.",
    ),
    ("Sachsen", "Landkreis Sächsische Schweiz-Osterzgebirge"): Rule(
        "14628",
        "SAECHS.SCHWEIZ-OSTERZGEB",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA abbreviates both Sächsische and Osterzgebirge.",
    ),
    # These two additional aliases are needed to cover this exact KBA release;
    # they are held to the same provisional standard as the requested list.
    ("Saarland", "Landkreis Saarpfalz-Kreis"): Rule(
        "10045",
        "SAAR-PFALZ-KREIS",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "The KBA label separates Saar and Pfalz with a hyphen.",
    ),
    ("Thüringen", "Landkreis Saale-Holzland-Kreis"): Rule(
        "16074",
        "SAALE-HOLZLANDKREIS",
        "explicit_provisional_alias",
        "provisional_alias_requires_authoritative_review",
        "KBA joins Holzland and Kreis in the district label.",
    ),
}


SPECIAL_RULES: dict[tuple[str, str], Rule] = {
    ("Berlin", "Kreisfreie Stadt Berlin"): Rule(
        "11000",
        "BERLIN",
        "explicit_state_city_naming_convention",
        "observed_local_snapshot_naming_convention",
        "KBA names the Berlin state/city simply BERLIN, without a city suffix.",
    ),
    ("Hamburg", "Kreisfreie Stadt Hamburg"): Rule(
        "02000",
        "HAMBURG",
        "explicit_state_city_naming_convention",
        "observed_local_snapshot_naming_convention",
        "KBA names the Hamburg state/city simply HAMBURG, without a city suffix.",
    ),
    ("Rheinland-Pfalz", "Kreisfreie Stadt Trier"): Rule(
        "07211",
        "TRIER-SAARBURG",
        "shared_kba_registration_region",
        "provisional_shared_region_requires_authoritative_review",
        "KBA FZ 27 reports Trier city and Trier-Saarburg together under the shared registration region 07211.",
        allows_type_difference=True,
    ),
    ("Rheinland-Pfalz", "Landkreis Trier-Saarburg"): Rule(
        "07211",
        "TRIER-SAARBURG",
        "shared_kba_registration_region",
        "provisional_shared_region_requires_authoritative_review",
        "KBA FZ 27 reports Trier city and Trier-Saarburg together under the shared registration region 07211.",
        allows_type_difference=True,
    ),
}


CSV_COLUMNS = [
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
]


def normalize_label(value: str | None) -> str:
    """Normalize spelling/diacritics for comparison, retaining no geography."""

    text = (value or "").upper()
    # German transliteration must happen before Unicode decomposition: ö -> OE,
    # not O, because the KBA labels use both umlauts and OE spellings.
    text = (
        text.replace("Ä", "AE")
        .replace("Ö", "OE")
        .replace("Ü", "UE")
        .replace("ẞ", "SS")
        .replace("ß", "SS")
    )
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def bnetza_admin_type(district_name: str) -> str:
    normalized = normalize_label(district_name)
    if normalized.startswith("KREISFREIE STADT ") or normalized.startswith("STADTKREIS "):
        return "city"
    if normalized.startswith("LANDKREIS ") or normalized.startswith("KREIS "):
        return "county"
    return "unknown"


def bnetza_base_name(district_name: str) -> str:
    normalized = normalize_label(district_name)
    return re.sub(
        r"^(?:KREISFREIE STADT|STADTKREIS|LANDKREIS|KREIS)\s+",
        "",
        normalized,
    )


def kba_admin_type(district_name: str) -> str:
    normalized = normalize_label(district_name)
    if normalized in {"BERLIN", "HAMBURG"} or re.search(r"(?:^| )STADT$", normalized):
        return "city"
    return "county"


def kba_base_name(district_name: str) -> str:
    normalized = normalize_label(district_name)
    normalized = re.sub(r"\s+STADT$", "", normalized)
    # Only KASSEL, LAND uses LAND as an administrative suffix in this release.
    # Names such as BERCHTESGADENER LAND and WEIMARER LAND must remain intact.
    if re.search(r",\s*LAND\s*$", district_name, flags=re.IGNORECASE):
        normalized = re.sub(r"\s+LAND$", "", normalized)
    return normalized


def sql_required_columns(conn: Any, table_name: str) -> set[str]:
    schema, table = table_name.split(".", 1)
    rows = conn.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = ? AND table_name = ?
        """,
        [schema, table],
    ).fetchall()
    return {row[0] for row in rows}


def assert_input_schema(conn: Any) -> dict[str, list[str]]:
    required = {
        "core.charging_equipment": [
            "source_id",
            "excel_row",
            "declared_point_count",
            "equipment_nominal_power_kw",
            "state_name",
            "district_name",
        ],
        "core.charging_point": ["source_id", "equipment_excel_row"],
        "core.kba_district_ev_stock": [
            "reference_date",
            "state_name",
            "district_code",
            "district_name",
            "passenger_cars",
            "bev_cars",
            "phev_cars",
        ],
    }
    observed: dict[str, list[str]] = {}
    missing: list[str] = []
    for table_name, columns in required.items():
        actual = sql_required_columns(conn, table_name)
        observed[table_name] = sorted(actual)
        missing.extend(f"{table_name}.{column}" for column in columns if column not in actual)
    if missing:
        raise RuntimeError("Required database columns are missing: " + ", ".join(missing))
    return observed


def load_inputs(conn: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Read one aggregated BNetzA record per geography and one KBA row per code."""

    bnetza_rows = conn.execute(
        """
        WITH point_counts AS (
            SELECT source_id, equipment_excel_row, COUNT(*) AS charging_point_slots
            FROM core.charging_point
            GROUP BY source_id, equipment_excel_row
        )
        SELECT
            e.state_name AS bnetza_state_name,
            e.district_name AS bnetza_district_name,
            COUNT(*) AS equipment_rows,
            COALESCE(SUM(COALESCE(e.declared_point_count, 0)), 0) AS declared_point_count,
            COALESCE(SUM(COALESCE(p.charging_point_slots, 0)), 0) AS charging_point_slots,
            COALESCE(SUM(COALESCE(e.equipment_nominal_power_kw, 0)), 0) AS equipment_nominal_power_kw
        FROM core.charging_equipment e
        LEFT JOIN point_counts p
          ON p.source_id = e.source_id
         AND p.equipment_excel_row = e.excel_row
        GROUP BY e.state_name, e.district_name
        ORDER BY e.state_name, e.district_name
        """
    ).fetchall()
    bnetza_columns = [
        "bnetza_state_name",
        "bnetza_district_name",
        "equipment_rows",
        "declared_point_count",
        "charging_point_slots",
        "equipment_nominal_power_kw",
    ]
    bnetza = [dict(zip(bnetza_columns, row)) for row in bnetza_rows]

    kba_rows = conn.execute(
        """
        SELECT state_name, district_code, district_name,
               passenger_cars, bev_cars, phev_cars
        FROM core.kba_district_ev_stock
        WHERE reference_date = DATE '2026-07-01'
        ORDER BY district_code
        """
    ).fetchall()
    kba_columns = [
        "kba_state_name",
        "kba_district_code",
        "kba_district_name",
        "passenger_cars",
        "bev_cars",
        "phev_cars",
    ]
    kba = [dict(zip(kba_columns, row)) for row in kba_rows]

    reconciliation = conn.execute(
        """
        WITH point_counts AS (
            SELECT source_id, equipment_excel_row, COUNT(*) AS charging_point_slots
            FROM core.charging_point
            GROUP BY source_id, equipment_excel_row
        )
        SELECT
            COUNT(*) AS equipment_rows,
            COALESCE(SUM(declared_point_count), 0) AS declared_point_count,
            COALESCE(SUM(COALESCE(p.charging_point_slots, 0)), 0) AS charging_point_slots,
            COUNT(*) FILTER (
                WHERE e.declared_point_count IS DISTINCT FROM COALESCE(p.charging_point_slots, 0)
            ) AS equipment_point_mismatches
        FROM core.charging_equipment e
        LEFT JOIN point_counts p
          ON p.source_id = e.source_id
         AND p.equipment_excel_row = e.excel_row
        """
    ).fetchone()
    reconciliation_values = dict(
        zip(
            [
                "equipment_rows",
                "declared_point_count",
                "charging_point_slots",
                "equipment_point_mismatches",
            ],
            reconciliation,
        )
    )
    return bnetza, kba, reconciliation_values


def validate_kba_input(kba: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    codes = [str(row["kba_district_code"]) for row in kba]
    if len(kba) != EXPECTED_KBA_DISTRICTS:
        failures.append(f"Expected 400 July KBA rows, found {len(kba)}")
    if len(set(codes)) != len(codes):
        failures.append("July KBA district codes are not unique")
    for row in kba:
        if not re.fullmatch(r"[0-9]{5}", str(row["kba_district_code"])):
            failures.append(f"Invalid KBA district code: {row['kba_district_code']!r}")
    return failures


def validate_rule_target(
    source_state: str,
    source_type: str,
    rule: Rule,
    target: dict[str, Any] | None,
) -> tuple[bool, str]:
    if target is None:
        return False, f"KBA code {rule.code} is absent from the July snapshot"
    if normalize_label(source_state) != normalize_label(str(target["kba_state_name"])):
        return False, "Source and KBA state names differ"
    if not rule.allows_type_difference and source_type != kba_admin_type(str(target["kba_district_name"])):
        return False, (
            "Administrative type differs: "
            f"BNetzA={source_type}, KBA={kba_admin_type(str(target['kba_district_name']))}"
        )
    if normalize_label(rule.expected_kba_name) != normalize_label(str(target["kba_district_name"])):
        return False, (
            "KBA name differs from the expected local-snapshot label: "
            f"expected={rule.expected_kba_name!r}, actual={target['kba_district_name']!r}"
        )
    return True, "State, administrative type, and KBA name checks passed"


def map_bnetza_row(
    source: dict[str, Any],
    kba_by_code: dict[str, dict[str, Any]],
    kba_by_key: dict[tuple[str, str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    state = str(source["bnetza_state_name"])
    district = str(source["bnetza_district_name"])
    source_type = bnetza_admin_type(district)
    key = (state, district)
    rule = SPECIAL_RULES.get(key) or PROVISIONAL_ALIASES.get(key)

    code: str | None = None
    kba: dict[str, Any] | None = None
    method = ""
    verification_status = "unmapped"
    note = "No unique state-aware and administrative-type-aware KBA match was found."
    validation_message = ""

    if rule is not None:
        candidate = kba_by_code.get(rule.code)
        valid, validation_message = validate_rule_target(state, source_type, rule, candidate)
        if valid:
            code = rule.code
            kba = candidate
            method = rule.method
            verification_status = rule.verification_status
            note = (
                rule.note
                + " The target state, administrative type, and KBA name were checked against the local July snapshot; "
                "authoritative boundary verification is not claimed."
            )
        else:
            note = f"Explicit rule rejected: {validation_message}"
    else:
        state_key = normalize_label(state)
        candidate_key = (state_key, source_type, bnetza_base_name(district))
        matches = kba_by_key.get(candidate_key, [])
        if len(matches) == 1:
            kba = matches[0]
            code = str(kba["kba_district_code"])
            method = "state_and_admin_type_name_match"
            verification_status = "observed_local_snapshot_match"
            note = (
                "Unique match after constraining by state and administrative type and normalizing label spelling. "
                "This is a local dataset crosswalk; authoritative boundary verification is not claimed."
            )
            validation_message = "Unique state/type/name match"
        elif len(matches) > 1:
            note = "Ambiguous state/type/name match; no mapping was invented."
            validation_message = f"{len(matches)} candidate KBA rows"
        else:
            validation_message = "No candidate KBA row"

    return {
        "crosswalk_version": CROSSWALK_VERSION,
        "bnetza_reference_date": BNETZA_REFERENCE_DATE,
        "kba_reference_date": KBA_REFERENCE_DATE,
        "bnetza_state_name": state,
        "bnetza_district_name": district,
        "bnetza_admin_type": source_type,
        "kba_state_name": kba["kba_state_name"] if kba else "",
        "kba_district_code": code or "",
        "kba_district_name": kba["kba_district_name"] if kba else "",
        "kba_admin_type": kba_admin_type(str(kba["kba_district_name"])) if kba else "",
        "mapping_status": "mapped" if code else "unmapped",
        "mapping_method": method,
        "verification_status": verification_status,
        "mapping_note": note,
        "evidence_url": KBA_EVIDENCE_URL if code else "",
        "equipment_rows": source["equipment_rows"],
        "declared_point_count": source["declared_point_count"],
        "charging_point_slots": source["charging_point_slots"],
        "equipment_nominal_power_kw": source["equipment_nominal_power_kw"],
        "_validation_message": validation_message,
        "_source_type": source_type,
    }


def build_crosswalk(
    bnetza: list[dict[str, Any]], kba: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    kba_by_code = {str(row["kba_district_code"]): row for row in kba}
    kba_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in kba:
        key = (
            normalize_label(str(row["kba_state_name"])),
            kba_admin_type(str(row["kba_district_name"])),
            kba_base_name(str(row["kba_district_name"])),
        )
        kba_by_key.setdefault(key, []).append(row)

    rows = [map_bnetza_row(source, kba_by_code, kba_by_key) for source in bnetza]
    unmapped = [row for row in rows if row["mapping_status"] != "mapped"]
    mapped_codes = [row["kba_district_code"] for row in rows if row["mapping_status"] == "mapped"]
    duplicate_code_counts = {
        code: count for code, count in Counter(mapped_codes).items() if count > 1
    }
    alias_rows = [
        row
        for row in rows
        if row["mapping_method"] == "explicit_provisional_alias"
    ]
    special_rows = [
        row
        for row in rows
        if row["mapping_method"]
        in {
            "shared_kba_registration_region",
            "explicit_state_city_naming_convention",
        }
    ]
    validation = {
        "unmapped_rows": unmapped,
        "mapped_codes": mapped_codes,
        "duplicate_code_counts": duplicate_code_counts,
        "alias_rows": alias_rows,
        "special_rows": special_rows,
        "source_combo_counts": Counter(
            (row["bnetza_state_name"], row["bnetza_district_name"]) for row in rows
        ),
    }
    return rows, validation


def write_crosswalk(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=CSV_COLUMNS,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            output_row = {column: row[column] for column in CSV_COLUMNS}
            power = output_row["equipment_nominal_power_kw"]
            if power not in (None, ""):
                output_row["equipment_nominal_power_kw"] = (
                    f"{float(power):.6f}".rstrip("0").rstrip(".")
                )
            writer.writerow(output_row)


def check_row(
    checks: list[dict[str, Any]],
    name: str,
    expected: Any,
    actual: Any,
    passed: bool,
    note: str = "",
) -> None:
    checks.append(
        {
            "name": name,
            "expected": expected,
            "actual": actual,
            "status": "PASS" if passed else "FAIL",
            "note": note,
        }
    )


def validate_crosswalk(
    rows: list[dict[str, Any]],
    bnetza: list[dict[str, Any]],
    kba: list[dict[str, Any]],
    reconciliation: dict[str, Any],
    mapping_validation: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    mapped_rows = [row for row in rows if row["mapping_status"] == "mapped"]
    mapped_codes = {row["kba_district_code"] for row in mapped_rows}
    kba_codes = {str(row["kba_district_code"]) for row in kba}
    source_combos = {
        (row["bnetza_state_name"], row["bnetza_district_name"]) for row in bnetza
    }
    output_combos = {
        (row["bnetza_state_name"], row["bnetza_district_name"]) for row in rows
    }

    check_row(
        checks,
        "BNetzA distinct state/district combinations",
        EXPECTED_BNETZA_COMBINATIONS,
        len(bnetza),
        len(bnetza) == EXPECTED_BNETZA_COMBINATIONS,
    )
    check_row(
        checks,
        "Crosswalk rows preserve BNetzA combinations",
        len(source_combos),
        len(rows),
        len(output_combos) == len(source_combos) == len(rows),
        "One CSV row is retained per original state/district combination.",
    )
    check_row(
        checks,
        "July KBA district rows",
        EXPECTED_KBA_DISTRICTS,
        len(kba),
        len(kba) == EXPECTED_KBA_DISTRICTS,
    )
    check_row(
        checks,
        "Mapped BNetzA combinations",
        len(rows),
        len(mapped_rows),
        len(mapped_rows) == len(rows),
        "Unmapped rows remain blank rather than receiving an invented code.",
    )
    check_row(
        checks,
        "Unmapped BNetzA combinations",
        0,
        len(mapping_validation["unmapped_rows"]),
        len(mapping_validation["unmapped_rows"]) == 0,
    )
    check_row(
        checks,
        "Distinct mapped KBA district codes",
        EXPECTED_KBA_DISTRICTS,
        len(mapped_codes),
        mapped_codes == kba_codes,
        f"Missing KBA codes: {sorted(kba_codes - mapped_codes)}",
    )
    check_row(
        checks,
        "Multiply assigned KBA codes",
        {"07211": 2},
        mapping_validation["duplicate_code_counts"],
        mapping_validation["duplicate_code_counts"] == {"07211": 2},
        "Only the Trier/Trier-Saarburg shared registration region is intentionally duplicated.",
    )
    duplicate_source_combos = {
        combo: count
        for combo, count in mapping_validation["source_combo_counts"].items()
        if count > 1
    }
    check_row(
        checks,
        "Multiply assigned BNetzA combinations",
        0,
        len(duplicate_source_combos),
        len(duplicate_source_combos) == 0,
    )
    unmapped_equipment_rows = sum(
        int(row["equipment_rows"])
        for row in rows
        if row["mapping_status"] != "mapped"
    )
    multiply_assigned_equipment_rows = sum(
        int(row["equipment_rows"])
        for row in rows
        if mapping_validation["source_combo_counts"][
            (row["bnetza_state_name"], row["bnetza_district_name"])
        ]
        > 1
    )
    check_row(
        checks,
        "Equipment assignment completeness",
        "0 unmapped; 0 multiply-assigned",
        f"{unmapped_equipment_rows} unmapped; {multiply_assigned_equipment_rows} multiply-assigned",
        unmapped_equipment_rows == 0 and multiply_assigned_equipment_rows == 0,
        "Each equipment row belongs to one retained BNetzA combination and therefore one crosswalk row.",
    )
    check_row(
        checks,
        "Equipment rows retained",
        int(reconciliation["equipment_rows"]),
        sum(int(row["equipment_rows"]) for row in rows),
        sum(int(row["equipment_rows"]) for row in rows)
        == int(reconciliation["equipment_rows"])
        == EXPECTED_EQUIPMENT_ROWS,
    )
    check_row(
        checks,
        "Charging-point slots retained",
        int(reconciliation["charging_point_slots"]),
        sum(int(row["charging_point_slots"]) for row in rows),
        sum(int(row["charging_point_slots"]) for row in rows)
        == int(reconciliation["charging_point_slots"])
        == EXPECTED_CHARGING_POINTS,
    )
    check_row(
        checks,
        "Declared charging points retained",
        int(reconciliation["declared_point_count"]),
        sum(int(row["declared_point_count"]) for row in rows),
        sum(int(row["declared_point_count"]) for row in rows)
        == int(reconciliation["declared_point_count"]),
    )
    check_row(
        checks,
        "Equipment-to-point reconciliation",
        0,
        int(reconciliation["equipment_point_mismatches"]),
        int(reconciliation["equipment_point_mismatches"]) == 0,
        "The point-count query uses source_id and Excel row as the join key.",
    )

    trier_rows = [row for row in rows if row["kba_district_code"] == "07211"]
    trier_names = {row["bnetza_district_name"] for row in trier_rows}
    check_row(
        checks,
        "Trier shared registration region",
        {"Kreisfreie Stadt Trier", "Landkreis Trier-Saarburg"},
        trier_names,
        trier_names == {"Kreisfreie Stadt Trier", "Landkreis Trier-Saarburg"},
        "Both source entries are kept and map to 07211 before aggregation.",
    )

    kba_by_code = {str(row["kba_district_code"]): row for row in kba}
    source_bev_stock = sum(int(row["bev_cars"] or 0) for row in kba)
    aggregated_bev_stock = sum(
        int(kba_by_code[code]["bev_cars"] or 0) for code in mapped_codes
    )
    raw_join_bev_stock = sum(
        int(kba_by_code[row["kba_district_code"]]["bev_cars"] or 0)
        for row in mapped_rows
    )
    check_row(
        checks,
        "KBA BEV stock after aggregate-before-join",
        source_bev_stock,
        aggregated_bev_stock,
        source_bev_stock == aggregated_bev_stock,
        f"A raw 401-row join would total {raw_join_bev_stock:,}; the aggregate join avoids the Trier duplicate.",
    )
    check_row(
        checks,
        "Candidate alias rules locally validated",
        len(PROVISIONAL_ALIASES),
        len(mapping_validation["alias_rows"]),
        len(mapping_validation["alias_rows"]) == len(PROVISIONAL_ALIASES),
        "Alias rows are still provisional and require authoritative review.",
    )
    return checks


def markdown_value(value: Any) -> str:
    if isinstance(value, set):
        return ", ".join(sorted(str(item) for item in value)) or "—"
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(
    database: Path,
    output: Path,
    observed_schema: dict[str, list[str]],
    bnetza: list[dict[str, Any]],
    kba: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    mapping_validation: dict[str, Any],
    checks: list[dict[str, Any]],
) -> str:
    generated = dt.datetime.now(dt.timezone.utc).isoformat()
    lines = [
        "# Batch 03 — BNetzA-to-KBA geographic crosswalk validation",
        "",
        f"Generated at (UTC): `{generated}`",
        "",
        "## Scope and method",
        "",
        f"- Database: `{database.relative_to(ROOT) if database.is_relative_to(ROOT) else database}` (opened read-only).",
        f"- BNetzA charging snapshot: `{BNETZA_REFERENCE_DATE}`.",
        f"- KBA district stock snapshot: `{KBA_REFERENCE_DATE}`.",
        f"- Crosswalk version: `{CROSSWALK_VERSION}`.",
        "- The script reads one row per BNetzA state/district combination and one row per KBA July district code.",
        "- Name matching is constrained by state and administrative type. Explicit aliases are provisional and do not claim official verification.",
        "- Charging metrics are aggregated by KBA code before KBA stock is joined. This is required because Trier city and Trier-Saarburg both use KBA code `07211`.",
        "",
        "## Observed schema",
        "",
    ]
    for table, columns in observed_schema.items():
        lines.append(f"- `{table}`: {', '.join(f'`{column}`' for column in columns)}")
    lines.extend(["", "## Validation summary", "", "| Check | Expected | Actual | Status | Notes |", "|---|---:|---:|---|---|"])
    for check in checks:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_value(check["name"]),
                    markdown_value(check["expected"]),
                    markdown_value(check["actual"]),
                    markdown_value(check["status"]),
                    markdown_value(check["note"]),
                ]
            )
            + " |"
        )

    method_counts = Counter(row["mapping_method"] or "unmapped" for row in rows)
    status_counts = Counter(row["verification_status"] for row in rows)
    lines.extend(
        [
            "",
            "## Crosswalk output",
            "",
            f"- Output CSV: `{output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}`.",
            f"- Rows: `{len(rows):,}`; mapped rows: `{sum(row['mapping_status'] == 'mapped' for row in rows):,}`; unmapped rows: `{sum(row['mapping_status'] != 'mapped' for row in rows):,}`.",
            f"- Distinct mapped KBA codes: `{len({row['kba_district_code'] for row in rows if row['mapping_status'] == 'mapped'}):,}`.",
            "",
            "### Mapping methods",
            "",
            "| Mapping method | Rows |",
            "|---|---:|",
        ]
    )
    for method, count in sorted(method_counts.items()):
        lines.append(f"| `{method}` | {count:,} |")
    lines.extend(["", "### Verification statuses", "", "| Verification status | Rows |", "|---|---:|"])
    for status, count in sorted(status_counts.items()):
        lines.append(f"| `{status}` | {count:,} |")

    lines.extend(["", "## Candidate aliases", "", "These mappings are explicit local-snapshot candidates, not official administrative verification.", "", "| BNetzA state | BNetzA district | KBA code | KBA name observed | Note |", "|---|---|---:|---|---|"])
    for row in mapping_validation["alias_rows"]:
        lines.append(
            f"| {row['bnetza_state_name']} | {row['bnetza_district_name']} | {row['kba_district_code']} | {row['kba_district_name']} | {row['mapping_note']} |"
        )

    lines.extend(
        [
            "",
            "## Trier and state/city naming exceptions",
            "",
            "| BNetzA district | KBA code | KBA name | Mapping method |",
            "|---|---:|---|---|",
        ]
    )
    for row in mapping_validation["special_rows"]:
        lines.append(
            f"| {row['bnetza_district_name']} | {row['kba_district_code']} | {row['kba_district_name']} | `{row['mapping_method']}` |"
        )
    lines.extend(
        [
            "",
            "Trier is intentionally represented by two source rows and one KBA registration-region code. Any downstream join must first aggregate charging metrics by `kba_district_code`; joining KBA stock to the raw 401-row crosswalk would duplicate code `07211`.",
            "",
            "## Exceptions",
            "",
        ]
    )
    if mapping_validation["unmapped_rows"]:
        lines.append("The following combinations were not mapped:")
        for row in mapping_validation["unmapped_rows"]:
            lines.append(f"- `{row['bnetza_state_name']} / {row['bnetza_district_name']}`: {row['mapping_note']}")
    else:
        lines.append("No unmapped combinations in the observed snapshot.")
    lines.extend(
        [
            "",
            "## Reproducibility and boundary decisions",
            "",
            f"- Evidence URL recorded in mapped CSV rows: [{KBA_EVIDENCE_URL}]({KBA_EVIDENCE_URL}).",
            "- No permanent DuckDB table or view was created.",
            "- Original BNetzA/KBA source data and the original DuckDB file were not modified.",
            "- Before database integration, decide whether the provisional aliases should be replaced or supplemented with an authoritative administrative crosswalk and whether the shared Trier registration-region treatment is suitable for the final KPI definition.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    database = args.database if args.database.is_absolute() else ROOT / args.database
    output = args.output if args.output.is_absolute() else ROOT / args.output
    report_path = args.report if args.report.is_absolute() else ROOT / args.report

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - depends on the caller's environment.
        print(f"ERROR: DuckDB is unavailable: {exc}", file=sys.stderr)
        return 2

    if not database.is_file():
        print(f"ERROR: Database not found: {database}", file=sys.stderr)
        return 2

    conn = None
    try:
        conn = duckdb.connect(str(database), read_only=True)
        observed_schema = assert_input_schema(conn)
        bnetza, kba, reconciliation = load_inputs(conn)
        input_failures = validate_kba_input(kba)
        if input_failures:
            for failure in input_failures:
                print(f"ERROR: {failure}", file=sys.stderr)
            return 1
        rows, mapping_validation = build_crosswalk(bnetza, kba)
        checks = validate_crosswalk(
            rows, bnetza, kba, reconciliation, mapping_validation
        )
        write_crosswalk(output, rows)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            render_report(
                database,
                output,
                observed_schema,
                bnetza,
                kba,
                rows,
                mapping_validation,
                checks,
            ),
            encoding="utf-8",
        )
    except Exception as exc:
        print(f"ERROR: Crosswalk build failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if conn is not None:
            conn.close()

    failed = [check for check in checks if check["status"] != "PASS"]
    print(f"Created: {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}")
    print(f"Created: {report_path.relative_to(ROOT) if report_path.is_relative_to(ROOT) else report_path}")
    print(
        f"Checks: {len(checks) - len(failed)} passed, {len(failed)} failed; "
        f"crosswalk rows={len(rows):,}, distinct KBA codes="
        f"{len({row['kba_district_code'] for row in rows if row['mapping_status'] == 'mapped'}):,}"
    )
    if failed:
        for check in failed:
            print(f"FAIL: {check['name']}: {check['actual']}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
