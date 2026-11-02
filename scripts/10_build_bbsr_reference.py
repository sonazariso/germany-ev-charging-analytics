#!/usr/bin/env python3
"""Build the versioned BBSR four-category reference from the official XLSX.

The original workbook is never rewritten. The script uses only the Python
standard library, validates the published workbook structure and classification
domain, writes a deterministic UTF-8 CSV, and records provenance.

Run from the repository root:

    python3 scripts/10_build_bbsr_reference.py

The result is a separate BBSR reference. It does not alter DuckDB, the
BNetzA-to-KBA Crosswalk, or analytical KPIs.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import posixpath
import re
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/sources.json"
DEFAULT_SOURCE_ID = "bbsr_raumgliederungen_2025"
SELECTED_SHEET = "Kreisreferenz"
USAGE_SHEET = "Nutzungshinweise"
MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
OFFICE_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PACKAGE_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
FOUR_CATEGORY_CODES = ("1", "2", "3", "4")

REQUIRED_SOURCE_FIELDS = {
    "KRS2025": "Kreise (2025) Kennziffer",
    "KRS_NAME": "Kreise (2025) Name",
    "BLD2025": "Bundesländer (2025) Kennziffer",
    "BLD_NAME": "Bundesländer (2025) Name",
    "KKR2025": "Kreisregionen (2025) Kennziffer",
    "KKR_NAME": "Kreisregionen (2025) Name",
    "KTU2025": "Siedlungsstruktureller Kreistyp (2025) Kennziffer",
    "KTU_NAME": "Siedlungsstruktureller Kreistyp (2025) Name",
}

OUTPUT_COLUMNS = [
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
]


class BbsrValidationError(ValueError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def excel_column_number(reference: str) -> int:
    match = re.match(r"^([A-Z]+)", reference or "")
    if not match:
        raise BbsrValidationError(f"Invalid Excel cell reference: {reference!r}")
    number = 0
    for letter in match.group(1):
        number = number * 26 + ord(letter) - ord("A") + 1
    return number


def excel_column_name(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def load_shared_strings(archive: zipfile.ZipFile) -> List[str]:
    member = "xl/sharedStrings.xml"
    if member not in archive.namelist():
        return []
    root = ET.fromstring(archive.read(member))
    return [
        "".join(item.text or "" for item in si.iter(MAIN_NS + "t"))
        for si in root.findall(MAIN_NS + "si")
    ]


def workbook_sheets(archive: zipfile.ZipFile) -> List[Tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relation_map = {
        relation.get("Id"): relation.get("Target")
        for relation in relationships.findall(PACKAGE_REL_NS + "Relationship")
    }
    members = set(archive.namelist())
    result = []
    for sheet in workbook.findall("./" + MAIN_NS + "sheets/" + MAIN_NS + "sheet"):
        target = relation_map.get(sheet.get(OFFICE_REL_NS + "id"))
        if not target:
            raise BbsrValidationError(
                f"Missing worksheet relationship for {sheet.get('name', '?')!r}"
            )
        member = posixpath.normpath(
            target.lstrip("/")
            if target.startswith("/")
            else posixpath.join("xl", target)
        )
        if member not in members:
            raise BbsrValidationError(
                f"Missing worksheet XML member {member!r} for "
                f"{sheet.get('name', '?')!r}"
            )
        result.append((sheet.get("name", "[untitled]"), member))
    return result


def cell_value(cell: ET.Element, shared_strings: Sequence[str]) -> Optional[str]:
    cell_type = cell.get("t", "n")
    raw = cell.find(MAIN_NS + "v")
    if cell_type == "inlineStr":
        inline = cell.find(MAIN_NS + "is")
        return (
            "".join(item.text or "" for item in inline.iter(MAIN_NS + "t"))
            if inline is not None
            else ""
        )
    if raw is not None and raw.text is not None:
        if cell_type == "s":
            index = int(raw.text)
            if not 0 <= index < len(shared_strings):
                raise BbsrValidationError(f"Invalid shared-string index {index}")
            return shared_strings[index]
        if cell_type == "b":
            return "TRUE" if raw.text == "1" else "FALSE"
        return raw.text
    formula = cell.find(MAIN_NS + "f")
    if formula is not None and formula.text:
        return "=" + formula.text
    return None


def iter_sheet_rows(
    archive: zipfile.ZipFile,
    member: str,
    shared_strings: Sequence[str],
) -> Iterator[Tuple[int, Dict[int, str]]]:
    with archive.open(member) as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag != MAIN_NS + "row":
                continue
            row_number = int(element.get("r", "0"))
            values: Dict[int, str] = {}
            for cell in element.findall(MAIN_NS + "c"):
                value = cell_value(cell, shared_strings)
                if value is not None:
                    values[excel_column_number(cell.get("r", ""))] = value
            yield row_number, values
            element.clear()


def row_text(values: Dict[int, str]) -> str:
    return " ".join(
        value for _, value in sorted(values.items()) if value and value.strip()
    )


def parse_date_from_usage(text: str, label: str) -> str:
    match = re.search(r"\b" + label + r"\s+(\d{2}\.\d{2}\.\d{4})", text)
    if not match:
        raise BbsrValidationError(
            f"Could not find {label!r} date in workbook usage sheet"
        )
    return dt.datetime.strptime(match.group(1), "%d.%m.%Y").date().isoformat()


def source_columns(
    row_one: Dict[int, str], row_two: Dict[int, str]
) -> List[Dict[str, str]]:
    return [
        {
            "excel_column": excel_column_name(number),
            "field_name": row_one.get(number, ""),
            "description": row_two.get(number, ""),
        }
        for number in sorted(set(row_one) | set(row_two))
    ]


def inspect_workbook(
    path: Path,
) -> Tuple[dict, List[Tuple[int, Dict[int, str]]]]:
    if not path.is_file():
        raise BbsrValidationError(f"Missing BBSR source workbook: {path}")
    if not zipfile.is_zipfile(path):
        raise BbsrValidationError(f"BBSR source is not a valid XLSX/ZIP: {path}")

    with zipfile.ZipFile(path) as archive:
        shared_strings = load_shared_strings(archive)
        sheet_inventory = []
        selected_rows: List[Tuple[int, Dict[int, str]]] = []
        usage_rows: Dict[int, Dict[int, str]] = {}

        for sheet_name, member in workbook_sheets(archive):
            row_one: Optional[Dict[int, str]] = None
            row_two: Optional[Dict[int, str]] = None
            physical_rows = 0
            nonempty_rows = 0
            first_nonempty: Optional[int] = None
            last_nonempty: Optional[int] = None
            for row_number, values in iter_sheet_rows(
                archive, member, shared_strings
            ):
                physical_rows += 1
                if values:
                    nonempty_rows += 1
                    if first_nonempty is None:
                        first_nonempty = row_number
                    last_nonempty = row_number
                if row_number == 1:
                    row_one = values
                elif row_number == 2:
                    row_two = values
                if (
                    sheet_name == SELECTED_SHEET
                    and row_number >= 3
                    and values
                ):
                    selected_rows.append((row_number, values))
                if sheet_name == USAGE_SHEET and values:
                    usage_rows[row_number] = values
            if row_one is None or row_two is None:
                raise BbsrValidationError(
                    f"Sheet {sheet_name!r} does not have both original "
                    "header rows 1 and 2"
                )
            sheet_inventory.append(
                {
                    "sheet_name": sheet_name,
                    "xml_member": member,
                    "physical_excel_rows": physical_rows,
                    "nonempty_rows": nonempty_rows,
                    "first_nonempty_row": first_nonempty,
                    "last_nonempty_row": last_nonempty,
                    "original_columns": source_columns(row_one, row_two),
                }
            )

        if not selected_rows:
            raise BbsrValidationError(
                f"Selected worksheet {SELECTED_SHEET!r} has no data rows"
            )
        usage_text = "\n".join(
            row_text(usage_rows[row]) for row in sorted(usage_rows)
        )
        return (
            {
                "sheet_count": len(sheet_inventory),
                "shared_string_count": len(shared_strings),
                "sheets": sheet_inventory,
                "reference_date_from_workbook": parse_date_from_usage(
                    usage_text, "Gebietsstand"
                ),
                "workbook_stand_from_workbook": parse_date_from_usage(
                    usage_text, "Stand"
                ),
                "license_text_from_workbook": next(
                    (
                        line
                        for line in usage_text.splitlines()
                        if "Datenlizenz Deutschland" in line
                    ),
                    "",
                ),
                "attribution_text_from_workbook": next(
                    (
                        line
                        for line in usage_text.splitlines()
                        if "Empfohlene Quellenangabe" in line
                    ),
                    "",
                ),
            },
            selected_rows,
        )


def get_source_config(source_id: str) -> dict:
    if not CONFIG_PATH.is_file():
        raise BbsrValidationError(f"Missing source manifest: {CONFIG_PATH}")
    manifest = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for source in manifest.get("sources", []):
        if source.get("id") == source_id:
            return source
    raise BbsrValidationError(
        f"Source ID {source_id!r} not found in {CONFIG_PATH}"
    )


def validate_source_file(source: dict, path: Path) -> dict:
    actual_bytes = path.stat().st_size
    actual_sha256 = sha256(path)
    if source.get("file_size_bytes") is not None and actual_bytes != source["file_size_bytes"]:
        raise BbsrValidationError(
            f"Source size mismatch: expected {source['file_size_bytes']}, "
            f"observed {actual_bytes}"
        )
    if source.get("sha256") and actual_sha256 != source["sha256"]:
        raise BbsrValidationError(
            f"Source SHA-256 mismatch: expected {source['sha256']}, "
            f"observed {actual_sha256}"
        )
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": actual_bytes,
        "sha256": actual_sha256,
    }


def required_header_indexes(sheet_inventory: dict) -> Dict[str, int]:
    by_name = {
        column["field_name"]: column
        for column in sheet_inventory["original_columns"]
        if column.get("field_name")
    }
    indexes: Dict[str, int] = {}
    for field_name, expected_description in REQUIRED_SOURCE_FIELDS.items():
        column = by_name.get(field_name)
        if column is None:
            raise BbsrValidationError(
                f"Required source field {field_name!r} is missing from "
                f"{SELECTED_SHEET!r}"
            )
        if column.get("description") != expected_description:
            raise BbsrValidationError(
                f"Unexpected description for {field_name}: "
                f"{column.get('description')!r}; expected "
                f"{expected_description!r}"
            )
        indexes[field_name] = excel_column_number(column["excel_column"])
    return indexes


def clean_required_value(
    values: Dict[int, str], index: int, field_name: str, row_number: int
) -> str:
    value = values.get(index)
    if value is None or not value.strip():
        raise BbsrValidationError(
            f"Missing required value {field_name!r} at {SELECTED_SHEET}!"
            f"{excel_column_name(index)}{row_number}"
        )
    return value


def build_records(
    source: dict,
    workbook_metadata: dict,
    selected_rows: List[Tuple[int, Dict[int, str]]],
) -> Tuple[List[dict], dict]:
    selected_sheet = next(
        sheet
        for sheet in workbook_metadata["sheets"]
        if sheet["sheet_name"] == SELECTED_SHEET
    )
    indexes = required_header_indexes(selected_sheet)
    row_numbers = [number for number, _ in selected_rows]
    if row_numbers != list(range(3, max(row_numbers) + 1)):
        raise BbsrValidationError(
            f"{SELECTED_SHEET} data rows are not contiguous from Excel row 3"
        )

    reference_date = workbook_metadata["reference_date_from_workbook"]
    workbook_stand = workbook_metadata["workbook_stand_from_workbook"]
    if reference_date != source.get("reference_date"):
        raise BbsrValidationError(
            f"Configured reference date {source.get('reference_date')!r} "
            f"does not match workbook geographic stand {reference_date!r}"
        )
    if source.get("publication_date") and workbook_stand != source["publication_date"]:
        raise BbsrValidationError(
            f"Configured workbook stand {source['publication_date']!r} "
            f"does not match workbook stand {workbook_stand!r}"
        )

    source_version = (
        f"{source['filename']} | {SELECTED_SHEET} | "
        f"geographic stand {reference_date}"
    )
    records = []
    for row_number, values in selected_rows:
        raw = {
            field: clean_required_value(values, index, field, row_number)
            for field, index in indexes.items()
        }
        for field_name in ("KRS2025", "KKR2025"):
            if not re.fullmatch(r"\d{8}", raw[field_name]):
                raise BbsrValidationError(
                    f"{field_name} is not an eight-digit source code at row "
                    f"{row_number}: {raw[field_name]!r}"
                )
        if not re.fullmatch(r"\d{2}", raw["BLD2025"]):
            raise BbsrValidationError(
                f"BLD2025 is not a two-digit source code at row "
                f"{row_number}: {raw['BLD2025']!r}"
            )
        if raw["KTU2025"] not in FOUR_CATEGORY_CODES:
            raise BbsrValidationError(
                f"Unexpected four-category KTU2025 code at row "
                f"{row_number}: {raw['KTU2025']!r}"
            )
        records.append(
            {
                "source_version": source_version,
                "bbsr_reference_date": reference_date,
                "source_sheet_name": SELECTED_SHEET,
                "source_excel_row": str(row_number),
                "administrative_district_code": raw["KRS2025"],
                "administrative_district_name": raw["KRS_NAME"],
                "federal_state_code": raw["BLD2025"],
                "federal_state_name": raw["BLD_NAME"],
                "kreisregion_code": raw["KKR2025"],
                "kreisregion_name": raw["KKR_NAME"],
                "settlement_type_code": raw["KTU2025"],
                "settlement_type_name_de": raw["KTU_NAME"],
            }
        )

    return records, {
        "selected_source_fields": {
            "administrative_district_code": {
                "source_field": "KRS2025",
                "source_description": REQUIRED_SOURCE_FIELDS["KRS2025"],
            },
            "administrative_district_name": {
                "source_field": "KRS_NAME",
                "source_description": REQUIRED_SOURCE_FIELDS["KRS_NAME"],
            },
            "federal_state_code": {
                "source_field": "BLD2025",
                "source_description": REQUIRED_SOURCE_FIELDS["BLD2025"],
            },
            "federal_state_name": {
                "source_field": "BLD_NAME",
                "source_description": REQUIRED_SOURCE_FIELDS["BLD_NAME"],
            },
            "kreisregion_code": {
                "source_field": "KKR2025",
                "source_description": REQUIRED_SOURCE_FIELDS["KKR2025"],
            },
            "kreisregion_name": {
                "source_field": "KKR_NAME",
                "source_description": REQUIRED_SOURCE_FIELDS["KKR_NAME"],
            },
            "settlement_type_code": {
                "source_field": "KTU2025",
                "source_description": REQUIRED_SOURCE_FIELDS["KTU2025"],
            },
            "settlement_type_name_de": {
                "source_field": "KTU_NAME",
                "source_description": REQUIRED_SOURCE_FIELDS["KTU_NAME"],
            },
        },
        "source_rows_read": len(selected_rows),
    }


def group_values(records: Iterable[dict], key: str, value: str) -> Dict[str, set]:
    result: Dict[str, set] = {}
    for record in records:
        result.setdefault(record[key], set()).add(record[value])
    return result


def rows_for_code(records: Sequence[dict], code: str) -> List[dict]:
    return [
        record
        for record in records
        if record["administrative_district_code"] == code
    ]


def validate_records(records: List[dict]) -> dict:
    if not records:
        raise BbsrValidationError("No records were extracted from the selected sheet")
    primary_keys = [record["administrative_district_code"] for record in records]
    duplicate_primary = sorted(
        {key for key in primary_keys if primary_keys.count(key) > 1}
    )
    if duplicate_primary:
        raise BbsrValidationError(
            f"Duplicate primary-grain KRS2025 keys: {duplicate_primary[:10]}"
        )

    federal_state_names = group_values(
        records, "federal_state_code", "federal_state_name"
    )
    federal_state_name_inconsistencies = {
        code: sorted(names)
        for code, names in federal_state_names.items()
        if len(names) != 1
    }
    if federal_state_name_inconsistencies:
        raise BbsrValidationError(
            "Federal-state code/name inconsistency: "
            f"{federal_state_name_inconsistencies}"
        )

    type_labels = group_values(
        records, "settlement_type_code", "settlement_type_name_de"
    )
    if set(type_labels) != set(FOUR_CATEGORY_CODES):
        raise BbsrValidationError(
            f"Expected exactly four compact settlement-type codes "
            f"{FOUR_CATEGORY_CODES}; observed {sorted(type_labels)}"
        )
    type_label_inconsistencies = {
        code: sorted(labels)
        for code, labels in type_labels.items()
        if len(labels) != 1
    }
    if type_label_inconsistencies:
        raise BbsrValidationError(
            f"Settlement code/label inconsistency: {type_label_inconsistencies}"
        )

    kreisregion_names = group_values(
        records, "kreisregion_code", "kreisregion_name"
    )
    kreisregion_types = group_values(
        records, "kreisregion_code", "settlement_type_code"
    )
    name_inconsistencies = {
        code: sorted(names)
        for code, names in kreisregion_names.items()
        if len(names) != 1
    }
    type_inconsistencies = {
        code: sorted(types)
        for code, types in kreisregion_types.items()
        if len(types) != 1
    }
    if name_inconsistencies:
        raise BbsrValidationError(
            f"Kreisregion code/name inconsistency: {name_inconsistencies}"
        )
    if type_inconsistencies:
        raise BbsrValidationError(
            f"Kreisregion compact-type inconsistency: {type_inconsistencies}"
        )

    multi_row_groups = {
        code: [
            record["administrative_district_code"]
            for record in records
            if record["kreisregion_code"] == code
        ]
        for code in sorted(kreisregion_names)
        if sum(record["kreisregion_code"] == code for record in records) > 1
    }
    category_counts = {
        code: sum(record["settlement_type_code"] == code for record in records)
        for code in FOUR_CATEGORY_CODES
    }

    main_kinzig = rows_for_code(records, "06435000")
    hanau = rows_for_code(records, "06415000")
    trier_city = rows_for_code(records, "07211000")
    trier_saarburg = rows_for_code(records, "07235000")
    special_codes = {
        "Berlin": "11000000",
        "Hamburg": "02000000",
        "Bremen": "04011000",
        "Bremerhaven": "04012000",
    }
    special_cases = {
        name: rows_for_code(records, code)
        for name, code in special_codes.items()
    }

    if len(hanau) != 0 or len(main_kinzig) != 1:
        raise BbsrValidationError(
            "The 2025 BBSR vintage does not show the expected "
            "Hanau/Main-Kinzig-Kreis split: "
            f"Hanau rows={len(hanau)}, Main-Kinzig-Kreis rows={len(main_kinzig)}"
        )
    if (
        len(trier_city) != 1
        or len(trier_saarburg) != 1
        or trier_city[0]["settlement_type_code"] != "1"
        or trier_saarburg[0]["settlement_type_code"] != "3"
    ):
        raise BbsrValidationError(
            "The expected separate 2025 Trier and Trier-Saarburg "
            "BBSR rows/types are missing"
        )
    for name, rows in special_cases.items():
        if len(rows) != 1 or rows[0]["settlement_type_code"] != "1":
            raise BbsrValidationError(
                f"Unexpected {name} fixture: rows={len(rows)}, "
                f"types={sorted({row['settlement_type_code'] for row in rows})}"
            )

    return {
        "source_rows_read": len(records),
        "derived_rows_emitted": len(records),
        "source_rows_not_emitted": 0,
        "distinct_administrative_district_codes": len(set(primary_keys)),
        "distinct_federal_state_codes": len(federal_state_names),
        "federal_state_name_inconsistency_count": len(
            federal_state_name_inconsistencies
        ),
        "distinct_kreisregion_codes": len(kreisregion_names),
        "duplicate_primary_grain_keys": len(duplicate_primary),
        "null_or_blank_classification_codes": sum(
            not record["settlement_type_code"].strip() for record in records
        ),
        "classification_codes": list(FOUR_CATEGORY_CODES),
        "classification_code_label_map": {
            code: sorted(type_labels[code])[0] for code in FOUR_CATEGORY_CODES
        },
        "classification_row_counts": category_counts,
        "classification_code_label_inconsistency_count": len(
            type_label_inconsistencies
        ),
        "kreisregion_name_inconsistency_count": len(name_inconsistencies),
        "kreisregion_type_inconsistency_count": len(type_inconsistencies),
        "multi_row_kreisregion_group_count": len(multi_row_groups),
        "multi_row_kreisregion_examples": [
            {
                "kreisregion_code": code,
                "administrative_district_codes": codes,
            }
            for code, codes in list(multi_row_groups.items())[:10]
        ],
        "hanau_rows": hanau,
        "main_kinzig_rows": main_kinzig,
        "trier_city_rows": trier_city,
        "trier_saarburg_rows": trier_saarburg,
        "special_case_rows": special_cases,
        "district_to_kreisregion_relationships_preserved": True,
        "allocation_applied": False,
        "kba_assignment_applied": False,
        "kba_crosswalk_changed": False,
    }


def write_csv(path: Path, records: Sequence[dict]) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(
        records,
        key=lambda record: (
            record["administrative_district_code"],
            record["source_excel_row"],
        ),
    )
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=OUTPUT_COLUMNS,
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(ordered)
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def json_safe(value):
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def write_report(
    path: Path,
    source: dict,
    source_file: dict,
    workbook: dict,
    extract: dict,
    validation: dict,
    derived_file: dict,
) -> None:
    lines = [
        "# Batch 10 — BBSR reference acquisition, build, and validation",
        "",
        "Scope: acquire the latest suitable official BBSR reference, preserve its "
        "provenance, derive the four-category Kreis reference, and validate it. "
        "DuckDB, the existing Crosswalk, and analytical KPIs are out of scope.",
        "",
        "## Executive summary",
        "",
        "Batch 10 is PASS for an independent, versioned BBSR reference. The official "
        "2025 workbook was acquired and hashed, its six worksheets and source headers "
        "were inspected, and 400 Kreis rows were extracted without assigning BBSR "
        "categories to KBA records. The raw workbook remains outside Git; the small "
        "derived reference, manifest, profile, script, and validation report are "
        "tracked.",
        "",
        "## Source selection and provenance",
        "",
        f"- Publisher: {source['organization']}",
        f"- Official reference page: {source['source_page']}",
        f"- Selected workbook: {source['url']}",
        f"- Observed current-page vintages: "
        f"{', '.join(source.get('available_reference_vintages_observed', []))}",
        f"- Selected latest available suitable vintage: "
        f"{source.get('selected_latest_available_vintage', 'not recorded')}",
        f"- Geographic reference date: {workbook['reference_date_from_workbook']}",
        f"- Workbook stand / publication date: "
        f"{workbook['workbook_stand_from_workbook']}",
        f"- Download timestamp UTC: {source.get('downloaded_at_utc', 'not recorded')}",
        f"- HTTP status: {source.get('http_response', {}).get('status', 'not recorded')}",
        f"- HTTP Last-Modified: "
        f"{source.get('http_response', {}).get('last_modified', 'not recorded')}",
        f"- Actual file size: {source_file['bytes']:,} bytes",
        f"- Source SHA-256: {source_file['sha256']}",
        f"- License: {source['license']}",
        f"- License text: {source.get('license_url', 'not recorded')}",
        f"- Required attribution: {source['required_attribution']}",
        "",
        "The page listed no 2026 workbook at the time of the check. The older "
        "nine-category 2012 dataset and complete INKAR database were not used.",
        "",
        "The workbook's Nutzungshinweise names this license, and the linked "
        "license text permits copying, processing, transmission to third parties, "
        "and creation of new datasets when the provider, license, dataset URI, and "
        "a change notice are retained. This makes the small derived CSV suitable "
        "for Git tracking with the required attribution and change notice. It does "
        "not pre-approve a future BBSR/KBA enrichment or public KPI publication.",
        "",
        "The official download page exposed the reference workbooks as the current "
        "structured resource. This 2025 workbook is the smallest suitable official "
        "resource inspected that contains both Kreis and Kreisregion identifiers and "
        "the compact four-category classification in one source; only its "
        "Kreisreferenz sheet is needed for the derived file. The descriptive typology "
        "page does not replace the identifiers, while the older 2012 resource and the "
        "complete INKAR database were not suitable substitutes.",
        "",
        "## Workbook inspection",
        "",
        f"The workbook contains {workbook['sheet_count']} worksheets. Every worksheet "
        "was inspected for its original header rows and row inventory. Only "
        f"{SELECTED_SHEET} is used for the derived reference.",
        "",
        "| Worksheet | Physical rows | Non-empty rows | Original columns |",
        "|---|---:|---:|---:|",
    ]
    for sheet in workbook["sheets"]:
        lines.append(
            f"| {sheet['sheet_name']} | {sheet['physical_excel_rows']:,} | "
            f"{sheet['nonempty_rows']:,} | {len(sheet['original_columns']):,} |"
        )
    lines.extend(
        [
            "",
            "### Selected source fields",
            "",
            "| Output field | Original field | Original description |",
            "|---|---|---|",
        ]
    )
    for output_field, mapping in extract["selected_source_fields"].items():
        lines.append(
            f"| {output_field} | {mapping['source_field']} | "
            f"{mapping['source_description']} |"
        )
    lines.extend(
        [
            "",
            "KTU2025 and KTU_NAME were selected because their original description "
            "is Siedlungsstruktureller Kreistyp (2025). The differentiated "
            "five-category fields were not selected.",
            "",
            "The complete original column inventory for all six worksheets is in "
            "data/reference/bbsr_source_manifest.json.",
            "",
            "## Derived reference",
            "",
            f"- Output: {derived_file['path']}",
            f"- Rows: {validation['derived_rows_emitted']:,}",
            f"- UTF-8 CSV SHA-256: {derived_file['sha256']}",
            f"- Columns: {', '.join(OUTPUT_COLUMNS)}",
            "- Grain: one row per BBSR KRS2025 administrative Kreis row; "
            "Kreisregion relationships remain at the original component-row grain.",
            "- No KBA code, AGS/ARS conversion, allocation, or KPI value is added.",
            "",
            "## Validation results",
            "",
            "| Check | Observed result |",
            "|---|---:|",
            f"| Source Kreisreferenz rows read | {validation['source_rows_read']:,} |",
            f"| Derived rows emitted | {validation['derived_rows_emitted']:,} |",
            f"| Source rows not emitted | {validation['source_rows_not_emitted']:,} |",
            f"| Distinct administrative district codes | "
            f"{validation['distinct_administrative_district_codes']:,} |",
            f"| Distinct federal-state codes | "
            f"{validation['distinct_federal_state_codes']:,} |",
            f"| Federal-state code/name inconsistencies | "
            f"{validation['federal_state_name_inconsistency_count']:,} |",
            f"| Distinct Kreisregion codes | {validation['distinct_kreisregion_codes']:,} |",
            f"| Duplicate primary-grain keys | "
            f"{validation['duplicate_primary_grain_keys']:,} |",
            f"| Classification codes selected | "
            f"{', '.join(validation['classification_codes'])} |",
            f"| Classification code/label inconsistencies | "
            f"{validation['classification_code_label_inconsistency_count']:,} |",
            f"| Kreisregion name inconsistencies | "
            f"{validation['kreisregion_name_inconsistency_count']:,} |",
            f"| Kreisregion mixed-type groups | "
            f"{validation['kreisregion_type_inconsistency_count']:,} |",
            f"| Multi-district Kreisregion groups preserved | "
            f"{validation['multi_row_kreisregion_group_count']:,} |",
            "",
            "### Compact four-category counts",
            "",
            "| Code | German label | Rows |",
            "|---:|---|---:|",
        ]
    )
    for code in FOUR_CATEGORY_CODES:
        lines.append(
            f"| {code} | {validation['classification_code_label_map'][code]} | "
            f"{validation['classification_row_counts'][code]:,} |"
        )
    lines.extend(
        [
            "",
            "The generator fails if required fields/categories are missing, source "
            "rows cannot be represented, source codes lose their expected string "
            "shape, or code/label and geographic relationships are inconsistent.",
            "The observed 400 Kreis rows, 362 Kreisregion keys, and compact type "
            "counts match the Batch 09 feasibility findings. The Batch 10 change "
            "is the preserved source/provenance and reproducible derived reference, "
            "not a new geographic vintage or a changed classification grain.",
            "",
            "## Compatibility review",
            "",
            "### Hanau and Main-Kinzig-Kreis",
            "",
            f"The 2025 workbook contains {len(validation['hanau_rows'])} Hanau row(s) "
            f"and {len(validation['main_kinzig_rows'])} Main-Kinzig-Kreis row(s). "
            "This confirms that the selected vintage predates the January 2026 "
            "Hanau administrative separation for this reference. No classification "
            "is copied to the current Hanau KBA row.",
            "",
            "### Trier and Trier-Saarburg",
            "",
            "| Administrative row | BBSR code | BBSR type code | BBSR type label |",
            "|---|---|---:|---|",
        ]
    )
    for row in validation["trier_city_rows"] + validation["trier_saarburg_rows"]:
        lines.append(
            f"| {row['administrative_district_name']} | "
            f"{row['administrative_district_code']} | "
            f"{row['settlement_type_code']} | {row['settlement_type_name_de']} |"
        )
    lines.extend(
        [
            "",
            "The two administrative rows remain separate. Shared KBA registration "
            "region 07211 stock is not allocated and no single BBSR category is "
            "assigned to it.",
            "",
            "### Other special cases",
            "",
            "| Area | BBSR row(s) | Type result |",
            "|---|---:|---|",
        ]
    )
    for name in ("Berlin", "Hamburg", "Bremen", "Bremerhaven"):
        rows = validation["special_case_rows"][name]
        types = ", ".join(
            sorted({row["settlement_type_code"] for row in rows})
        ) or "—"
        lines.append(f"| {name} | {len(rows)} | {types} |")
    lines.extend(
        [
            "",
            "Small independent cities grouped into Kreisregionen remain as multiple "
            "administrative rows where provided. The generator preserves those "
            "relationships and does not collapse them. No mixed compact classification "
            "was observed within a Kreisregion in this workbook.",
            "",
            "## Integration boundary and next strategy",
            "",
            "The 2025 BBSR reference cannot be treated as a direct 2026 KBA lookup. "
            "The selected vintage has no Hanau row, and Trier plus Trier-Saarburg have "
            "different BBSR rows and types while the KBA layer combines stock under "
            "07211. The next approved step would be a separate compatibility study "
            "that documents any KRS-to-KBA relationship, tests boundary cases, and "
            "gets owner approval before any production join or KPI use. No Trier stock "
            "allocation or KBA classification is proposed by this batch.",
            "",
            "Remaining owner decisions: approve the future compatibility methodology "
            "and vintage-alignment rule; approve treatment of Hanau, Kreisregion "
            "groups, and Trier if integration is pursued; and separately review any "
            "public BBSR/KBA-derived output or KPI publication.",
            "",
            "## Reproduction",
            "",
            "Run: python3 scripts/10_build_bbsr_reference.py",
            "",
            "The raw workbook is excluded from Git under data/raw/. The derived CSV, "
            "source manifest, profile, and validation report are versioned. No "
            "DuckDB object, Crosswalk row, KPI, or shared Trier stock value changed.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the official BBSR four-category reference"
    )
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    args = parser.parse_args()
    try:
        source = get_source_config(args.source_id)
        if source.get("role") != "reference":
            raise BbsrValidationError(
                f"Source {args.source_id!r} is not marked as a reference source"
            )
        source_path = ROOT / source["path"]
        source_file = validate_source_file(source, source_path)
        workbook, selected_rows = inspect_workbook(source_path)
        records, extract = build_records(source, workbook, selected_rows)
        validation = validate_records(records)
        if validation["source_rows_read"] != validation["derived_rows_emitted"]:
            raise BbsrValidationError(
                "Source and derived row counts differ; refusing silent loss"
            )

        vintage = workbook["reference_date_from_workbook"][:4]
        derived_path = (
            ROOT / "data/reference" / f"bbsr_settlement_types_{vintage}.csv"
        )
        derived_file = write_csv(derived_path, records)

        metadata = {
            "manifest_version": 1,
            "source": source,
            "source_file": source_file,
            "workbook": workbook,
            "extract": extract,
            "derived_output": {
                **derived_file,
                "columns": OUTPUT_COLUMNS,
                "row_count": len(records),
                "grain": "one row per BBSR KRS2025 administrative Kreis row",
            },
            "validation": json_safe(validation),
            "scope_controls": {
                "complete_inkar_downloaded": False,
                "older_nine_category_2012_substitute_used": False,
                "kba_crosswalk_changed": False,
                "duckdb_changed": False,
                "kpi_values_calculated": False,
                "trier_stock_allocated": False,
            },
        }
        manifest_path = ROOT / "data/reference/bbsr_source_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(json_safe(metadata), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        profile_path = ROOT / "data/profiles/bbsr_reference_profile.json"
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(
            json.dumps(
                json_safe(
                    {
                        "source_file": source_file,
                        "reference_date": workbook["reference_date_from_workbook"],
                        "workbook_stand": workbook["workbook_stand_from_workbook"],
                        "sheet_count": workbook["sheet_count"],
                        "sheets": workbook["sheets"],
                        "selected_sheet": SELECTED_SHEET,
                        "selected_source_fields": extract["selected_source_fields"],
                        "validation": validation,
                        "derived_output": derived_file,
                    }
                ),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        report_path = ROOT / "reports/batch10_bbsr_reference_validation.md"
        write_report(
            report_path,
            source,
            source_file,
            workbook,
            extract,
            validation,
            derived_file,
        )
        print(
            f"[OK] Source: {source_file['bytes']:,} bytes | "
            f"SHA256 {source_file['sha256']}"
        )
        print(
            f"[OK] Workbook: {workbook['sheet_count']} sheets | "
            f"{validation['source_rows_read']:,} Kreis rows"
        )
        print(
            f"[OK] Derived: {derived_file['path']} | "
            f"{derived_file['sha256']}"
        )
        print(f"[OK] Manifest: {manifest_path.relative_to(ROOT)}")
        print(f"[OK] Profile: {profile_path.relative_to(ROOT)}")
        print(f"[OK] Report: {report_path.relative_to(ROOT)}")
        return 0
    except (
        BbsrValidationError,
        OSError,
        KeyError,
        json.JSONDecodeError,
        zipfile.BadZipFile,
    ) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
