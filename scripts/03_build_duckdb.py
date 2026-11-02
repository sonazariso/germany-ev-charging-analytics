#!/usr/bin/env python3
"""Phase 03: full-source ingest, lossless raw layers, safe initial normalization.

Runs on macOS without Excel, Docker or Windows. Raw XLSX files remain untouched.
Uses low-memory streaming ZIP/XML XLSX reader and bounded DuckDB batch inserts.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
OFFICE_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PACKAGE_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
COL_REGEX = re.compile(r"^([A-Z]+)")
SOURCE_NAMES = ["bnetza_charging_2026_09_30", "kba_fz27_2026_01", "kba_fz27_2026_04", "kba_fz27_2026_07"]


def column_number(cell_reference: str) -> int:
    match = COL_REGEX.match(cell_reference)
    if not match:
        return 0
    value = 0
    for ch in match.group(1):
        value = value * 26 + ord(ch) - 64
    return value


def excel_column(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in zf.namelist():
        return []
    values = []
    with zf.open(name) as stream:
        context = ET.iterparse(stream, events=("start", "end"))
        root = None
        for event, item in context:
            if root is None:
                root = item
            if event == "end" and item.tag == MAIN + "si":
                values.append("".join(part.text or "" for part in item.iter(MAIN + "t")))
                root.clear()
    return values


def sheet_members(zf: zipfile.ZipFile):
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    mapping = {item.get("Id"): item.get("Target") for item in rels.findall(PACKAGE_REL + "Relationship")}
    names = set(zf.namelist())
    for sheet in workbook.findall(MAIN + "sheets/" + MAIN + "sheet"):
        rid = sheet.get(OFFICE_REL + "id")
        target = mapping.get(rid)
        if not target:
            raise ValueError("Missing relationship for sheet: " + sheet.get("name", "?"))
        path = posixpath.normpath(target.lstrip("/") if target.startswith("/") else "xl/" + target)
        if path not in names:
            raise ValueError("Missing workbook XML member: " + path)
        yield sheet.get("name", "?"), path


def read_value(cell: ET.Element, strings: list[str]) -> str | None:
    kind = cell.get("t", "n")
    raw = cell.find(MAIN + "v")
    if kind == "inlineStr":
        inline = cell.find(MAIN + "is")
        value = "".join(n.text or "" for n in inline.iter(MAIN + "t")) if inline is not None else ""
    elif raw is not None and raw.text is not None:
        if kind == "s":
            idx = int(raw.text)
            if idx < 0 or idx >= len(strings):
                raise ValueError(f"Shared-string reference outside table: {idx}")
            value = strings[idx]
        else:
            value = raw.text
    else:
        formula = cell.find(MAIN + "f")
        value = "=" + formula.text if formula is not None and formula.text else None
    return value or None


def iter_sheet_rows(zf: zipfile.ZipFile, name: str, strings: list[str], max_columns: int):
    with zf.open(name) as stream:
        sheet_data = None
        for event, node in ET.iterparse(stream, events=("start", "end")):
            if event == "start" and node.tag == MAIN + "sheetData":
                sheet_data = node
            if event != "end" or node.tag != MAIN + "row":
                continue
            row_number = int(node.attrib["r"])
            cells = [None] * max_columns
            found = False
            for cell in node.findall(MAIN + "c"):
                value = read_value(cell, strings)
                if value is None:
                    continue
                index = column_number(cell.get("r", ""))
                if index > max_columns:
                    raise ValueError(f"Unexpected Excel column #{index} in row {row_number}; original not fully represented")
                if index == 0:
                    raise ValueError(f"Invalid Excel cell coordinate in row {row_number}")
                cells[index - 1] = value
                found = True
            if found:
                yield row_number, cells
            if sheet_data is not None:
                sheet_data.clear()


def setup_db(conn):
    conn.execute("CREATE SCHEMA raw")
    conn.execute("CREATE SCHEMA core")
    conn.execute("CREATE SCHEMA analytics")
    bcols = ["col_" + excel_column(i).lower() for i in range(1, 48)]
    kcols = ["col_" + excel_column(i).lower() for i in range(1, 16)]
    conn.execute("CREATE TABLE raw.bnetza_rows (source_id VARCHAR, excel_row INTEGER, " + ", ".join(x + " VARCHAR" for x in bcols) + ")")
    conn.execute("CREATE TABLE raw.kba_rows (source_id VARCHAR, reference_date DATE, sheet_name VARCHAR, excel_row INTEGER, " + ", ".join(x + " VARCHAR" for x in kcols) + ")")
    return bcols, kcols


def insert_batches(conn, query: str, iterator, batch_size: int = 600):
    batch = []
    total = 0
    for row in iterator:
        batch.append(row)
        if len(batch) == batch_size:
            conn.executemany(query, batch)
            total += len(batch)
            batch.clear()
    if batch:
        conn.executemany(query, batch)
        total += len(batch)
    return total


def ingest_one(conn, profile: dict):
    source_id = profile["source_id"]
    path = ROOT / profile["path"]
    if not path.is_file():
        raise FileNotFoundError(f"Missing original source file: {path}")
    if sha256(path) != profile.get("sha256"):
        raise ValueError(f"SHA256 mismatch: {path}; don't mix versions of source files")
    is_charger = source_id.startswith("bnetza_")
    cols = 47 if is_charger else 15
    bind_count = cols + (2 if is_charger else 4)
    insert_sql = ("INSERT INTO raw.bnetza_rows VALUES (" if is_charger else "INSERT INTO raw.kba_rows VALUES (") + ",".join("?" for _ in range(bind_count)) + ")"
    expected = {x["sheet"]: x["populated_rows"] for x in profile["sheets"]}
    rows_total = 0
    with zipfile.ZipFile(path) as zf:
        strings = get_shared_strings(zf)
        members = list(sheet_members(zf))
        if {name for name, _ in members} != set(expected):
            raise ValueError(f"Worksheet list changed for {source_id}")
        for sheet_name, xml_member in members:
            if is_charger:
                if sheet_name != "Ladesäulenregister":
                    raise ValueError(f"Unexpected BNetzA worksheet: {sheet_name}")
                rows = ((source_id, rownum, *cells) for rownum, cells in iter_sheet_rows(zf, xml_member, strings, cols))
            else:
                rows = ((source_id, profile["reference_date"], sheet_name, rownum, *cells) for rownum, cells in iter_sheet_rows(zf, xml_member, strings, cols))
            count = insert_batches(conn, insert_sql, rows)
            if count != expected[sheet_name]:
                raise ValueError(f"Row count mismatch in {source_id}:{sheet_name}: imported {count}, profiled {expected[sheet_name]}")
            rows_total += count
            print(f"  {sheet_name:<22} {count:>7,} rows", flush=True)
    print(f"[OK] {source_id}: {rows_total:,} raw nonempty rows", flush=True)
    return rows_total


def normalize_bnetza(conn):
    print("[NORMALIZE] Charging equipment and individual point slots", flush=True)
    conn.execute("""
    CREATE TABLE core.charging_equipment AS
    SELECT source_id, excel_row, col_a AS equipment_id, col_b AS operator_name,
      col_c AS display_name, col_d AS status, col_e AS equipment_type,
      TRY_CAST(NULLIF(TRIM(col_f), '') AS INTEGER) AS declared_point_count,
      TRY_CAST(REPLACE(col_g, ',', '.') AS DOUBLE) AS equipment_nominal_power_kw,
      col_h AS commissioning_date_raw,
      CASE WHEN TRY_CAST(col_h AS DOUBLE) BETWEEN 1 AND 100000
           THEN DATE '1899-12-30' + CAST(FLOOR(TRY_CAST(col_h AS DOUBLE)) AS INTEGER)
           ELSE TRY_CAST(col_h AS DATE) END AS commissioning_date,
      col_i AS street, col_j AS house_number, col_k AS address_addition,
      col_l AS postal_code, col_m AS city_name, col_n AS district_name, col_o AS state_name,
      TRY_CAST(REPLACE(col_p, ',', '.') AS DOUBLE) AS latitude,
      TRY_CAST(REPLACE(col_q, ',', '.') AS DOUBLE) AS longitude,
      col_r AS site_name, col_s AS parking_information, col_t AS payment_methods,
      col_u AS opening_hours, col_v AS opening_weekdays, col_w AS opening_times
    FROM raw.bnetza_rows WHERE excel_row >= 12
    """)
    conn.execute("""
    CREATE TABLE core.charging_point AS
    SELECT r.source_id, r.excel_row AS equipment_excel_row, r.col_a AS equipment_id,
      p.point_number, p.connector_types, p.connector_power_raw,
      TRY_CAST(REPLACE(p.connector_power_raw, ',', '.') AS DOUBLE) AS connector_power_kw_single,
      p.evse_id, p.public_key
    FROM raw.bnetza_rows r
    CROSS JOIN LATERAL (VALUES
      (1, r.col_x, r.col_y, r.col_z, r.col_aa),
      (2, r.col_ab, r.col_ac, r.col_ad, r.col_ae),
      (3, r.col_af, r.col_ag, r.col_ah, r.col_ai),
      (4, r.col_aj, r.col_ak, r.col_al, r.col_am),
      (5, r.col_an, r.col_ao, r.col_ap, r.col_aq),
      (6, r.col_ar, r.col_as, r.col_at, r.col_au)
    ) p(point_number, connector_types, connector_power_raw, evse_id, public_key)
    WHERE r.excel_row >= 12
      AND (NULLIF(TRIM(COALESCE(p.connector_types, '')), '') IS NOT NULL
       OR NULLIF(TRIM(COALESCE(p.connector_power_raw, '')), '') IS NOT NULL
       OR NULLIF(TRIM(COALESCE(p.evse_id, '')), '') IS NOT NULL
       OR NULLIF(TRIM(COALESCE(p.public_key, '')), '') IS NOT NULL)
    """)
    conn.execute("""
    CREATE VIEW analytics.charging_point_public AS
    SELECT p.equipment_id, p.point_number,
      e.state_name, e.district_name, e.city_name, e.postal_code,
      e.latitude, e.longitude, e.operator_name, e.status, e.equipment_type,
      e.commissioning_date, e.equipment_nominal_power_kw,
      p.connector_types, p.connector_power_raw, p.connector_power_kw_single
    FROM core.charging_point p
    JOIN core.charging_equipment e
      ON p.source_id=e.source_id AND p.equipment_excel_row=e.excel_row
    """)
    conn.execute("""
    CREATE VIEW analytics.charging_by_state AS
    SELECT e.state_name,
      COUNT(*) AS equipment_rows,
      SUM(e.declared_point_count) AS declared_points,
      SUM(COALESCE(p.point_slots, 0)) AS populated_point_slots
    FROM core.charging_equipment e
    LEFT JOIN (SELECT equipment_excel_row, COUNT(*) AS point_slots
               FROM core.charging_point GROUP BY equipment_excel_row) p
      ON e.excel_row=p.equipment_excel_row
    GROUP BY e.state_name
    """)


def normalize_kba(conn):
    print("[NORMALIZE] KBA state-level fuel stocks", flush=True)
    conn.execute("""
    CREATE TABLE core.kba_state_fuel_stock AS
    WITH filled AS (
      SELECT source_id, reference_date, excel_row,
        LAST_VALUE(CASE WHEN NULLIF(TRIM(col_b), '') IS NOT NULL
                           AND col_b NOT ILIKE '% zusammen'
                        THEN col_b ELSE NULL END IGNORE NULLS)
          OVER (PARTITION BY source_id ORDER BY excel_row
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS state_name,
        TRIM(col_c) AS fuel_type, TRY_CAST(col_e AS BIGINT) AS passenger_cars
      FROM raw.kba_rows WHERE sheet_name = 'FZ 27.2'
    )
    SELECT * FROM filled
    WHERE fuel_type IN ('Benzin','Diesel','Gas insgesamt','Elektro (BEV)',
                        'Hybrid insgesamt','darunter Plug-in','Sonstige')
      AND passenger_cars IS NOT NULL AND state_name IS NOT NULL
    """)
    print("[NORMALIZE] KBA district-level BEV/PHEV stocks", flush=True)
    conn.execute("""
    CREATE TABLE core.kba_district_ev_stock AS
    WITH filled AS (
      SELECT source_id, reference_date, excel_row,
        LAST_VALUE(CASE WHEN NULLIF(TRIM(col_b), '') IS NOT NULL
                           AND col_b NOT ILIKE '% zusammen'
                        THEN col_b ELSE NULL END IGNORE NULLS)
          OVER (PARTITION BY source_id ORDER BY excel_row
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS state_name,
        col_c AS district_code, col_d AS district_name,
        TRY_CAST(col_e AS BIGINT) AS passenger_cars,
        TRY_CAST(col_j AS BIGINT) AS bev_cars,
        TRY_CAST(col_k AS BIGINT) AS phev_cars
      FROM raw.kba_rows WHERE sheet_name = 'FZ 27.15'
    )
    SELECT * FROM filled
    WHERE REGEXP_FULL_MATCH(TRIM(district_code), '[0-9]{5}')
      AND district_name IS NOT NULL
    """)
    print("[NORMALIZE] KBA postal-code-level BEV/PHEV stocks", flush=True)
    conn.execute("""
    CREATE TABLE core.kba_postcode_ev_stock AS
    SELECT source_id, reference_date, excel_row,
      LPAD(TRIM(col_b), 5, '0') AS postal_code,
      TRY_CAST(col_c AS BIGINT) AS commercial_total_cars,
      TRY_CAST(col_d AS BIGINT) AS commercial_bev,
      TRY_CAST(col_e AS BIGINT) AS commercial_phev,
      TRY_CAST(col_f AS BIGINT) AS private_total_cars,
      TRY_CAST(col_g AS BIGINT) AS private_bev,
      TRY_CAST(col_h AS BIGINT) AS private_phev
    FROM raw.kba_rows WHERE sheet_name = 'FZ 27.16'
      AND REGEXP_FULL_MATCH(TRIM(col_b), '[0-9]{1,5}')
      AND excel_row >= 12
    """)
    print("[NORMALIZE] KBA municipality-level BEV/PHEV stocks", flush=True)
    conn.execute("""
    CREATE TABLE core.kba_municipality_ev_stock AS
    WITH filled AS (
      SELECT source_id, reference_date, excel_row,
        LAST_VALUE(CASE WHEN NULLIF(TRIM(col_b), '') IS NOT NULL
                           AND col_b NOT ILIKE '% zusammen'
                        THEN col_b ELSE NULL END IGNORE NULLS)
          OVER (PARTITION BY source_id ORDER BY excel_row
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS state_name,
        LAST_VALUE(CASE WHEN REGEXP_MATCHES(COALESCE(col_c,''), '^[0-9]{5} ')
                        THEN col_c ELSE NULL END IGNORE NULLS)
          OVER (PARTITION BY source_id ORDER BY excel_row
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS district_label,
        col_d AS municipality_name,
        TRY_CAST(col_e AS BIGINT) AS commercial_total_cars,
        TRY_CAST(col_f AS BIGINT) AS commercial_bev,
        TRY_CAST(col_g AS BIGINT) AS commercial_phev,
        TRY_CAST(col_h AS BIGINT) AS private_total_cars,
        TRY_CAST(col_i AS BIGINT) AS private_bev,
        TRY_CAST(col_j AS BIGINT) AS private_phev
      FROM raw.kba_rows WHERE sheet_name='FZ 27.17'
    )
    SELECT *, SUBSTR(district_label, 1, 5) AS district_code,
      (LOWER(COALESCE(municipality_name,'')) LIKE '%zusammen%'
       OR LOWER(COALESCE(municipality_name,'')) LIKE '%insgesamt%') AS possible_total_row
    FROM filled WHERE excel_row >= 12 AND municipality_name IS NOT NULL
      AND district_label IS NOT NULL
    """)
    print("[NORMALIZE] KBA national quarterly history (deduplicate overlapping snapshots)", flush=True)
    conn.execute("""
    CREATE VIEW analytics.kba_national_quarterly_stock AS
    WITH observations AS (
      SELECT source_id, reference_date AS report_snapshot, excel_row,
        TRY_STRPTIME(col_b, '%d.%m.%Y')::DATE AS stock_date,
        TRY_CAST(col_h AS BIGINT) AS passenger_bev,
        TRY_CAST(col_j AS BIGINT) AS passenger_phev,
        TRY_CAST(col_c AS BIGINT) AS passenger_cars_total
      FROM raw.kba_rows WHERE sheet_name='FZ 27.9'
    ), ranked AS (
      SELECT *, ROW_NUMBER() OVER
        (PARTITION BY stock_date ORDER BY report_snapshot DESC, excel_row ASC) AS rn
      FROM observations WHERE stock_date IS NOT NULL
    )
    SELECT * EXCLUDE (rn) FROM ranked WHERE rn=1
    """)


def scalar(conn, query):
    return conn.execute(query).fetchone()[0]


def generate_report(conn, expected_profiles, counts):
    equipment = scalar(conn, 'SELECT COUNT(*) FROM core.charging_equipment')
    points = scalar(conn, 'SELECT COUNT(*) FROM core.charging_point')
    declared = scalar(conn, 'SELECT SUM(declared_point_count) FROM core.charging_equipment')
    mismatch = conn.execute("""
      SELECT COUNT(*) FROM core.charging_equipment e
      LEFT JOIN (SELECT equipment_excel_row, COUNT(*) actual FROM core.charging_point GROUP BY equipment_excel_row) p
        ON e.excel_row = p.equipment_excel_row
      WHERE e.declared_point_count IS DISTINCT FROM COALESCE(p.actual,0)
    """).fetchone()[0]
    missing_id = scalar(conn, "SELECT COUNT(*) FROM core.charging_equipment WHERE equipment_id IS NULL OR TRIM(equipment_id)='' ")
    duplicate_ids = scalar(conn, "SELECT COUNT(*) FROM (SELECT equipment_id FROM core.charging_equipment WHERE equipment_id IS NOT NULL GROUP BY equipment_id HAVING COUNT(*) > 1)")
    state_rows = scalar(conn, 'SELECT COUNT(*) FROM analytics.charging_by_state')
    num_statuses = conn.execute('SELECT status, COUNT(*) FROM core.charging_equipment GROUP BY status ORDER BY COUNT(*) DESC').fetchall()
    kba_counts = {name:scalar(conn,f'SELECT COUNT(*) FROM core.{name}') for name in ('kba_state_fuel_stock','kba_district_ev_stock','kba_postcode_ev_stock','kba_municipality_ev_stock')}
    state_distinct = conn.execute("SELECT reference_date, COUNT(DISTINCT state_name) FROM core.kba_state_fuel_stock WHERE fuel_type='Elektro (BEV)' GROUP BY reference_date ORDER BY reference_date").fetchall()
    db_size = (ROOT / 'data/analytics/ev_charging.build.duckdb').stat().st_size
    report = {
      'generated_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'raw_nonempty_rows':counts,
      'equipment_rows':equipment,
      'populated_point_slots':points,
      'declared_point_count':declared,
      'equipment_with_point_count_mismatch':mismatch,
      'equipment_with_missing_id':missing_id,
      'duplicate_equipment_ids':duplicate_ids,
      'distinct_state_names_from_charging':state_rows,
      'equipment_status_breakdown':[{'status':status,'rows':n} for status,n in num_statuses],
      'kba_normalized_rows':kba_counts,
      'kba_bev_state_coverage':[{'reference_date':str(day),'states':n} for day,n in state_distinct],
      'duckdb_size_bytes_before_checkpoint':db_size,
      'notes':['Point slots are NOT connector count; semicolon-separated connectors stay in one point.',
               'Differences between declared number of points and populated slots are flagged, not fabricated.',
               'KBA subtotals and alternate breakdowns remain in raw but are not added as separate vehicles.',
               'BNetzA published registry is incomplete relative to all German public chargers.',
               'KBA snapshot dates differ from BNetzA charging snapshot; do not imply same-date ratio.']
    }
    lines = ["# Phase 03 — DuckDB ingest and validation", "", "All source originals remain untouched; raw worksheet rows are retained in DuckDB.", "",
      "## BNetzA", "", "| Metric | Count |", "|---|---:|",
      f"| All nonempty source rows (including metadata) | {counts[SOURCE_NAMES[0]]:,} |",
      f"| Equipment rows (Excel row >=12) | {equipment:,} |",
      f"| Populated charging-point slots | {points:,} |",
      f"| Declared charging points (sum source field) | {declared:,} |",
      f"| Equipment with declared/slot mismatch | {mismatch:,} |",
      f"| Equipment IDs missing | {missing_id:,} |",
      f"| Duplicated equipment IDs | {duplicate_ids:,} |",
      f"| Distinct published states/region values | {state_rows:,} |", "",
      "## KBA normalized analytical tables", "", "| Table | Rows |", "|---|---:|",
    ]
    for name,value in kba_counts.items():lines.append(f'| `{name}` | {value:,} |')
    lines += ['', '## KBA BEV coverage by quarter', '', '| Reference date | States |', '|---|---:|']
    for date,n in state_distinct:lines.append(f'| {date} | {n} |')
    lines += ['', '## Equipment status (never silently filtered)', '', '| Status | Equipment rows |','|---|---:|']
    for status,n in num_statuses:lines.append(f'| {status or "[null]"} | {n:,} |')
    lines += ['', '## Methodological cautions', '']
    for note in report['notes']:lines.append('- '+note)
    lines += ['', 'This phase creates a preliminary canonical model. Further district, postcode, municipality and value reconciliation is required before final BI KPIs.', '']
    return report, '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Build DuckDB database from fully downloaded, profiled XLSX sources')
    parser.parse_args()
    try:
        import duckdb
    except ImportError:
        raise SystemExit('Missing Python package duckdb. Run: .venv/bin/python -m pip install -r requirements-phase03.txt')
    profile_path = ROOT / 'data/profiles/workbook_profiles.json'
    if not profile_path.is_file():
        raise SystemExit('Missing Phase 01 profile: data/profiles/workbook_profiles.json')
    profiles = json.loads(profile_path.read_text(encoding='utf-8'))
    profile_map = {p['source_id']:p for p in profiles}
    missing = [name for name in SOURCE_NAMES if name not in profile_map]
    if missing:
        raise SystemExit('Missing expected BNetzA/KBA source profiles: ' + ', '.join(missing))
    reference_profiles = sorted(set(profile_map) - set(SOURCE_NAMES))
    if reference_profiles:
        print('[INFO] Ignoring separately profiled reference sources: ' + ', '.join(reference_profiles), flush=True)
    if any(profile_map[name].get('status')!='verified_and_profiled' for name in SOURCE_NAMES):
        raise SystemExit('All four primary BNetzA/KBA source files must be verified_and_profiled in Phase 01')
    dest = ROOT / 'data/analytics/ev_charging.duckdb'
    build = ROOT / 'data/analytics/ev_charging.build.duckdb'
    dest.parent.mkdir(parents=True,exist_ok=True)
    (ROOT/'data/tmp/duckdb').mkdir(parents=True,exist_ok=True)
    for extra in (build,Path(str(build)+'.wal')):
        if extra.exists():
            print(f'[INFO] Removing unfinished prior build {extra.name}', flush=True)
            extra.unlink()
    conn = duckdb.connect(str(build))
    try:
        setup_db(conn)
        counts = {}
        for source in SOURCE_NAMES:
            print(f'[LOAD] {source}',flush=True)
            counts[source]=ingest_one(conn, profile_map[source])
        normalize_bnetza(conn)
        normalize_kba(conn)
        (ROOT/'data/profiles').mkdir(parents=True,exist_ok=True)
        (ROOT/'reports').mkdir(parents=True,exist_ok=True)
        report, markdown = generate_report(conn, profiles, counts)
        conn.execute('CHECKPOINT')
    except BaseException:
        conn.close()
        raise
    else:
        conn.close()
        tmp_report = ROOT/'data/profiles/phase03_validation.json'
        tmp_md = ROOT/'reports/phase03_duckdb_validation.md'
        tmp_report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        tmp_md.write_text(markdown,encoding='utf-8')
        os.replace(build, dest)
        print(f'[SUCCESS] DuckDB: {dest.relative_to(ROOT)} | {dest.stat().st_size/1024**2:.1f} MiB',flush=True)
        print(f'[SUCCESS] Report: {tmp_md.relative_to(ROOT)}',flush=True)
        print(f'[SUCCESS] JSON: {tmp_report.relative_to(ROOT)}',flush=True)
        print('Send the two report files back for reconciliation and final modeling.',flush=True)

if __name__ == '__main__':
    main()
