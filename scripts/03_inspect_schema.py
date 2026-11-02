#!/usr/bin/env python3
"""Germany EV Charging Analytics — Phase 02: inspect XLSX headers safely.

Use from the repository root:
    python3 scripts/03_inspect_schema.py

Reads all 4 locally downloaded workbooks in streaming mode, previewing only their
first Excel rows (the full source workbooks remain untouched). Uses standard
Python 3 libraries only; does not require DuckDB, Pandas, or Excel on macOS.

Outputs:
    data/profiles/schema_inspection.json
    reports/phase02_schema_inspection.md
"""

from __future__ import annotations

import json
import posixpath
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
X = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    member = "xl/sharedStrings.xml"
    if member not in archive.namelist():
        return []
    strings = []
    with archive.open(member) as stream:
        events = ET.iterparse(stream, events=("start", "end"))
        root = None
        for event, elem in events:
            if root is None:
                root = elem
            if event == "end" and elem.tag == X + "si":
                strings.append("".join((t.text or "") for t in elem.iter(X + "t")))
                root.clear()
    return strings


def sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rels = {
        elem.attrib["Id"]: elem.attrib["Target"]
        for elem in relationships.findall(REL + "Relationship")
    }
    output = []
    for sh in workbook.findall("./" + X + "sheets/" + X + "sheet"):
        rid = sh.get(R + "id")
        path = rels.get(rid)
        if not path:
            continue
        full_path = posixpath.normpath(
            path.lstrip("/") if path.startswith("/") else posixpath.join("xl", path)
        )
        if full_path not in archive.namelist():
            raise ValueError(f"Missing worksheet {full_path} in archive")
        output.append((sh.attrib.get("name", "unnamed"), full_path))
    return output


def cell_value(cell: ET.Element, strings: list[str]) -> str | None:
    cell_type = cell.get("t", "n")
    val = cell.find(X + "v")
    formula = cell.find(X + "f")
    if cell_type == "inlineStr":
        el = cell.find(X + "is")
        return "".join((t.text or "") for t in el.iter(X + "t")) if el is not None else None
    if val is not None and val.text is not None:
        if cell_type == "s":
            index = int(val.text)
            return strings[index] if 0 <= index < len(strings) else "[INVALID_SHARED_STRING]"
        return val.text
    if formula is not None and formula.text is not None:
        return "=" + formula.text
    return None


def preview_sheet(archive: zipfile.ZipFile, path: str, strings: list[str], first_excel_rows: int) -> list[dict]:
    found = []
    with archive.open(path) as stream:
        events = ET.iterparse(stream, events=("start", "end"))
        sheet_data = None
        for event, elem in events:
            if event == "start" and elem.tag == X + "sheetData":
                sheet_data = elem
            if event != "end" or elem.tag != X + "row":
                continue
            row_num = int(elem.get("r", "0"))
            if row_num > first_excel_rows:
                break
            values = {}
            for cell in elem.findall(X + "c"):
                value = cell_value(cell, strings)
                if value is not None and value.strip() != "":
                    values[cell.get("r", "?")] = value
            if values:
                found.append({"excel_row": row_num, "cells": values})
            if sheet_data is not None:
                sheet_data.clear()
    return found


def htmlsafe(s: str) -> str:
    return s.replace("`", "'").replace("\n", " ").replace("\r", " ")


def render_md(items: list[dict]) -> str:
    lines = [
        "# Phase 02 — Excel schema inspection",
        "",
        "**Scope:** complete BNetzA September 2026 + all 3 KBA FZ 27 releases in 2026.",
        "",
        "This report shows ONLY early Excel rows to identify title/header/subheader positions.",
        "The full source workbooks are untouched and no records are discarded.",
        "",
        "Do not interpret these preview row counts as equipment/point/vehicle totals.",
        "",
        "## Source inventory",
        "",
        "| Source | Sheets inspected | Status |",
        "|---|---:|---|",
    ]
    for item in items:
        lines.append(f"| {item['source_id']} | {len(item.get('sheets', []))} | {item['status']} |")
    lines.append("")
    for item in items:
        if item["status"] != "ok":
            lines.extend([f"## {item['source_id']}", "", f"ERROR: {item.get('reason')}", ""])
            continue
        # Full detailed header previews for BNetzA and only the most relevant July KBA tables.
        if item["source_id"].startswith("kba") and not item["source_id"].endswith("_07"):
            continue
        lines.extend([f"## {item['source_id']}", ""])
        important = {"FZ 27.1", "FZ 27.2", "FZ 27.5", "FZ 27.9", "FZ 27.15", "FZ 27.16", "FZ 27.17"}
        for sh in item["sheets"]:
            if item["source_id"].startswith("kba") and sh["sheet"] not in important:
                continue
            lines.extend([f"### {sh['sheet']}", "", "```text"])
            for row in sh["preview_rows"]:
                pairs = [f"{k} = {htmlsafe(str(v))[:160]}" for k, v in row["cells"].items()]
                lines.append(" | ".join(pairs)[:2500])
            lines.extend(["```", ""])
    lines.extend([
        "## Review needed before ETL",
        "",
        "- Locate the actual BNetzA header row; do not treat title and legal notes as data.",
        "- Identify repeated charging-point field groups; one equipment row may hold multiple points.",
        "- Retain all original data and distinguish raw, normalized, and dashboard layers.",
        "- Treat KBA table subtotals and district/ZIP/municipality reports as ALTERNATIVE breakdowns (never blindly sum them together).",
        "- Match geography and snapshot dates before comparing vehicles to charging points.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    manifest = ROOT / "config/sources.json"
    if not manifest.exists():
        print(f"ERROR: {manifest} not found. Run this from the extracted full project.", file=sys.stderr)
        return 2
    sources = json.loads(manifest.read_text(encoding="utf-8"))["sources"]
    result = []
    for source in sources:
        path = ROOT / source["path"]
        item = {"source_id": source["id"], "reference_date": source["reference_date"], "path": source["path"]}
        try:
            if not path.is_file() or not zipfile.is_zipfile(path):
                raise FileNotFoundError(f"Missing or invalid Excel workbook: {path}")
            with zipfile.ZipFile(path) as archive:
                shared = shared_strings(archive)
                item["sheets"] = []
                for name, member in sheets(archive):
                    cutoff = 50 if source["id"].startswith("bnetza") else 20
                    rows = preview_sheet(archive, member, shared, cutoff)
                    item["sheets"].append({"sheet": name, "preview_rows": rows, "preview_excel_rows_limit": cutoff})
            item["status"] = "ok"
            print(f"[OK] {source['id']}: {len(item['sheets'])} sheets", flush=True)
        except Exception as ex:
            item["status"] = "error"
            item["reason"] = str(ex)
            print(f"[ERROR] {source['id']}: {ex}", file=sys.stderr, flush=True)
        result.append(item)
    json_path = ROOT / "data/profiles/schema_inspection.json"
    md_path = ROOT / "reports/phase02_schema_inspection.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_md(result), encoding="utf-8")
    print(f"Created: {json_path.relative_to(ROOT)}")
    print(f"Created: {md_path.relative_to(ROOT)}")
    return 0 if all(x["status"] == "ok" for x in result) else 1


if __name__ == "__main__":
    sys.exit(main())
