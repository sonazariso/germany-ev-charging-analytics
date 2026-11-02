#!/usr/bin/env python3
"""Read-only, low-memory inventory of EVERY worksheet of original XLSX workbooks.

No row sampling for counts: all spreadsheet rows are streamed from the XLSX XML.
Only examples in the JSON report are capped to the first 6 populated rows.
No external Python modules; suited to macOS Intel and 16 GB RAM.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
X = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
COL_PATTERN = re.compile(r"([A-Z]+)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def col_number(cell_ref: str) -> int:
    match = COL_PATTERN.match(cell_ref)
    if not match:
        return 0
    result = 0
    for letter in match.group(1):
        result = result * 26 + ord(letter) - 64
    return result


def shared_strings(zf: zipfile.ZipFile) -> list[str]:
    """Decode XLSX string table with streaming XML, including rich text runs."""
    path = "xl/sharedStrings.xml"
    if path not in zf.namelist():
        return []
    result: list[str] = []
    with zf.open(path) as stream:
        context = ET.iterparse(stream, events=("start", "end"))
        root = None
        for event, item in context:
            if root is None:
                root = item
            if event == "end" and item.tag == X + "si":
                result.append("".join(t.text or "" for t in item.iter(X + "t")))
                root.clear()
    return result


def workbook_sheet_paths(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    relations = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.get("Id"): rel.get("Target") for rel in relations.findall(REL + "Relationship")}
    result = []
    for sh in workbook.findall("." + "/" + X + "sheets/" + X + "sheet"):
        sheet_name = sh.get("name", "[untitled]")
        rid = sh.get(R + "id")
        target = rel_map.get(rid)
        if target is None:
            continue
        normalized = posixpath.normpath(
            target.lstrip("/") if target.startswith("/") else posixpath.join("xl", target)
        )
        if normalized not in zf.namelist():
            raise ValueError(f"Missing sheet member {normalized!r} ({sheet_name})")
        result.append((sheet_name, normalized))
    return result


def display_cell(cell: ET.Element, shared: list[str]) -> tuple[str | None, str]:
    typ = cell.get("t", "n")
    raw = cell.find(X + "v")
    formula = cell.find(X + "f")
    if typ == "inlineStr":
        inline = cell.find(X + "is")
        value = "".join(e.text or "" for e in inline.iter(X + "t")) if inline is not None else ""
    elif raw is not None and raw.text is not None:
        if typ == "s":
            idx = int(raw.text)
            value = shared[idx] if idx < len(shared) else f"[INVALID_SHARED_STRING:{idx}]"
        else:
            value = raw.text
    elif formula is not None and formula.text:
        value = "=" + formula.text
    else:
        value = None
    return value, typ


def profile_sheet(zf: zipfile.ZipFile, sheet_name: str, path: str, shared: list[str]) -> dict:
    rows_seen = 0
    rows_nonempty = 0
    last_excel_row = 0
    max_col = 0
    values_seen = 0
    data_type_counts: Counter = Counter()
    preview = []
    with zf.open(path) as stream:
        context = ET.iterparse(stream, events=("start", "end"))
        sheet_data = None
        for event, element in context:
            if event == "start" and element.tag == X + "sheetData":
                sheet_data = element
            if event != "end" or element.tag != X + "row":
                continue
            rows_seen += 1
            excel_row = int(element.get("r", rows_seen))
            last_excel_row = max(last_excel_row, excel_row)
            current_preview: dict[str, str] = {}
            found_in_row = False
            for cell in element.findall(X + "c"):
                value, typ = display_cell(cell, shared)
                if value is None or value == "":
                    continue
                found_in_row = True
                values_seen += 1
                data_type_counts[typ] += 1
                col = col_number(cell.get("r", ""))
                max_col = max(col, max_col)
                if len(preview) < 6 and len(current_preview) < 16:
                    current_preview[cell.get("r", "?")] = value[:100] + ("…" if len(value) > 100 else "")
            if found_in_row:
                rows_nonempty += 1
                if len(preview) < 6:
                    preview.append({"excel_row": excel_row, "cells": current_preview})
            # Clearing the sheetData parent after every row avoids accumulating
            # prior worksheet rows as XML elements (especially on BNetzA).
            if sheet_data is not None:
                sheet_data.clear()
    return {
        "sheet": sheet_name,
        "xml_member": path,
        "physical_excel_rows": rows_seen,
        "populated_rows": rows_nonempty,
        "last_excel_row_number": last_excel_row,
        "max_populated_column_index": max_col,
        "nonempty_cells": values_seen,
        "value_type_counts": dict(data_type_counts),
        "first_populated_rows_preview": preview,
    }


def analyze(source: dict) -> dict:
    path = ROOT / source["path"]
    if not path.exists():
        return {"source_id": source["id"], "reference_date": source["reference_date"],
                "status": "missing", "path": source["path"], "official_page": source["source_page"]}
    if not zipfile.is_zipfile(path):
        return {"source_id": source["id"], "status": "invalid_xlsx", "path": source["path"]}
    with zipfile.ZipFile(path) as zf:
        strings = shared_strings(zf)
        sheets = workbook_sheet_paths(zf)
        print(f"  {source['id']}: {len(sheets)} worksheets, {len(strings):,} shared strings", flush=True)
        items = []
        for name, xml_path in sheets:
            result = profile_sheet(zf, name, xml_path, strings)
            items.append(result)
            print(f"    {name[:34]:34s} | {result['populated_rows']:>8,} rows | {result['nonempty_cells']:>10,} populated cells", flush=True)
    return {
        "source_id": source["id"], "reference_date": source["reference_date"],
        "status": "verified_and_profiled", "path": source["path"],
        "official_page": source["source_page"],
        "size_bytes": path.stat().st_size, "sha256": sha256(path),
        "shared_string_count": len(strings), "worksheet_count": len(items), "sheets": items,
    }


def report(profiles: list[dict]) -> str:
    lines = ["# Phase 01 — Source profiling report", "",
             "Full Germany coverage; raw originals kept; no sample rows excluded from analysis.", "",
             f"Generated on: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", "",
             "| Source | Date | Status | Original XLSX | Sheets | Populated rows across sheets |",
             "|---|---|---|---:|---:|---:|"]
    for p in profiles:
        lines.append("| {source_id} | {reference_date} | {status} | {size} | {sheets} | {rows} |".format(
            source_id=p["source_id"], reference_date=p.get("reference_date", "–"),
            status=p["status"], size=f"{p.get('size_bytes',0)/1024**2:.2f} MiB" if p.get('size_bytes') else "—",
            sheets=p.get("worksheet_count", "—"),
            rows=f"{sum(s['populated_rows'] for s in p.get('sheets', [])):,}" if "sheets" in p else "—"))
    lines.extend(["", "## Worksheets", "", "Counted rows are physical non-empty Excel rows, NOT distinct charging points or vehicle counts.", ""])
    for p in profiles:
        if p["status"] != "verified_and_profiled":
            lines.append(f"- **{p['source_id']}**: {p['status']} — {p.get('official_page', '')}")
            continue
        lines.extend([f"### {p['source_id']}", "", "| Sheet | Populated rows | Populated cells | Max column |", "|---|---:|---:|---:|"])
        for s in p["sheets"]:
            clean_name = s["sheet"].replace("|", "\\|")
            lines.append(f"| {clean_name} | {s['populated_rows']:,} | {s['nonempty_cells']:,} | {s['max_populated_column_index']} |")
        lines.append("")
    lines += ["## Cautions before building analytics", "",
              "- BNetzA: one Excel row can describe an equipment unit with multiple charging points; do not use worksheet row count as charging point count.",
              "- KBA FZ27: statistics are aggregates, not one row per vehicle. Preserve table titles, footnotes and snapshot dates before identifying fact tables.",
              "- Charging snapshot and quarterly vehicle-stock dates differ. Label cross-dataset comparisons with both dates.",
              "- Do not sum KBA subtotal and detail lines; identify table definitions first.",
              "- Full source retention is in original XLSX files. Profiling does not modify, filter, or import the raw data.",
              "", "## Next", "", "Inspect sample headers from data/profiles/workbook_profiles.json, then approve normalized column mapping and create charging equipment and charging point tables with full preservation.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", help="Profile selected IDs (default: all)")
    args = parser.parse_args()
    sources = json.loads((ROOT / "config/sources.json").read_text(encoding="utf-8"))["sources"]
    if args.source:
        sources = [s for s in sources if s["id"] in args.source]
        if len(sources) != len(set(args.source)):
            parser.error("Unknown source ID")
    print("Streaming all available XLSX sheets (no row sampling)...", flush=True)
    profiles = []
    for s in sources:
        try:
            profiles.append(analyze(s))
        except Exception as exc:
            profiles.append({"source_id": s["id"], "reference_date": s["reference_date"],
                             "status": "profile_error", "path": s["path"], "reason": str(exc)})
            print(f"[ERROR] {s['id']}: {exc}", file=sys.stderr)
    output_json = ROOT / "data/profiles/workbook_profiles.json"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = ROOT / "reports/phase01_data_profile.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report(profiles), encoding="utf-8")
    ok = sum(p["status"] == "verified_and_profiled" for p in profiles)
    print(f"Done: {ok}/{len(profiles)} workbooks; reports: {report_path.relative_to(ROOT)}")
    return 0 if ok == len(profiles) else 1


if __name__ == "__main__":
    raise SystemExit(main())
