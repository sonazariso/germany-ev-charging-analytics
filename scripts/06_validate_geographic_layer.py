#!/usr/bin/env python3
"""Independent, read-only validation for the Batch 06 geographic layer."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data/analytics/ev_charging.duckdb"
DEFAULT_CROSSWALK = ROOT / "data/reference/bnetza_kba_district_crosswalk_2026.csv"
SOURCE_ID = "bnetza_charging_2026_09_30"
CROSSWALK_VERSION = "2026-07-01"
BNETZA_DATE = dt.date(2026, 9, 30)
KBA_DATES = (
    dt.date(2026, 1, 1),
    dt.date(2026, 4, 1),
    dt.date(2026, 7, 1),
)

CSV_COLUMNS = (
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
TARGET_COLUMNS = (
    "crosswalk_version",
    "bnetza_source_id",
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
REFERENCE_TABLE = "reference.bnetza_kba_district_crosswalk_2026"
REGIONAL_VIEW = "analytics.charging_by_kba_district_2026_09_30"
COMBINED_VIEW = "analytics.kba_district_charging_vs_bev_2026"

EXPECTED = {
    "equipment": 117_662,
    "points": 211_253,
    "declared_points": 211_253,
    "normal_points": 156_155,
    "fast_points": 55_098,
    "points_ge_150": 40_950,
    "points_ge_350": 6_950,
    "regional_rows": 400,
    "combined_rows": 1_200,
    "crosswalk_rows": 401,
    "crosswalk_codes": 400,
    "provisional_rows": 24,
}
EXPECTED_BEV = {
    dt.date(2026, 1, 1): 2_031_870,
    dt.date(2026, 4, 1): 2_167_111,
    dt.date(2026, 7, 1): 2_362_218,
}
EXPECTED_PHEV_JULY = 1_225_241
EXPECTED_TRIER_JULY_BEV = 7_869
EXPECTED_NOMINAL_MW = 9_215.4173


class ValidationError(RuntimeError):
    """Raised when a Batch 06 acceptance check fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def scalar(conn: duckdb.DuckDBPyConnection, sql: str, params: tuple[Any, ...] = ()) -> Any:
    return conn.execute(sql, params).fetchone()[0]


def read_crosswalk(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"Missing crosswalk CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(tuple(reader.fieldnames or ()) == CSV_COLUMNS, "Crosswalk CSV schema changed")
        rows = list(reader)
    require(len(rows) == EXPECTED["crosswalk_rows"], f"Crosswalk rows: {len(rows)}")
    keys = [
        (row["bnetza_state_name"], row["bnetza_district_name"])
        for row in rows
    ]
    require(len(set(keys)) == EXPECTED["crosswalk_rows"], "Duplicate BNetzA crosswalk key")
    require(
        all(row["crosswalk_version"] == CROSSWALK_VERSION for row in rows),
        "Unexpected crosswalk version",
    )
    require(
        all(row["bnetza_reference_date"] == BNETZA_DATE.isoformat() for row in rows),
        "Unexpected BNetzA reference date in crosswalk",
    )
    require(
        all(row["kba_reference_date"] == KBA_DATES[-1].isoformat() for row in rows),
        "Unexpected KBA reference date in crosswalk",
    )
    require(all(row["mapping_status"] == "mapped" for row in rows), "Unmapped CSV row")
    require(
        sum(row["verification_status"].startswith("provisional") for row in rows)
        == EXPECTED["provisional_rows"],
        "Unexpected provisional mapping count",
    )
    codes = [row["kba_district_code"] for row in rows]
    require(all(re.fullmatch(r"[0-9]{5}", code or "") for code in codes), "Invalid KBA code")
    duplicate_codes = {code for code in codes if codes.count(code) > 1}
    require(duplicate_codes == {"07211"}, f"Unexpected duplicate KBA codes: {duplicate_codes}")
    require(codes.count("07211") == 2, "Trier shared code is not represented twice")
    require(
        sum(row["bnetza_state_name"] != row["kba_state_name"] for row in rows) == 0,
        "Unexpected cross-state crosswalk mapping",
    )
    return rows


def row_values(row: dict[str, str]) -> tuple[Any, ...]:
    return (
        row["crosswalk_version"],
        SOURCE_ID,
        dt.date.fromisoformat(row["bnetza_reference_date"]),
        dt.date.fromisoformat(row["kba_reference_date"]),
        row["bnetza_state_name"],
        row["bnetza_district_name"],
        row["bnetza_admin_type"] or None,
        row["kba_state_name"] or None,
        row["kba_district_code"] or None,
        row["kba_district_name"] or None,
        row["kba_admin_type"] or None,
        row["mapping_status"],
        row["mapping_method"],
        row["verification_status"],
        row["mapping_note"] or None,
        row["evidence_url"] or None,
        int(row["equipment_rows"]) if row["equipment_rows"] else None,
        int(row["declared_point_count"]) if row["declared_point_count"] else None,
        int(row["charging_point_slots"]) if row["charging_point_slots"] else None,
        float(row["equipment_nominal_power_kw"])
        if row["equipment_nominal_power_kw"]
        else None,
    )


def create_expected_crosswalk(
    conn: duckdb.DuckDBPyConnection,
    rows: list[dict[str, str]],
) -> None:
    columns = """
        crosswalk_version VARCHAR,
        bnetza_source_id VARCHAR,
        bnetza_reference_date DATE,
        kba_reference_date DATE,
        bnetza_state_name VARCHAR,
        bnetza_district_name VARCHAR,
        bnetza_admin_type VARCHAR,
        kba_state_name VARCHAR,
        kba_district_code VARCHAR,
        kba_district_name VARCHAR,
        kba_admin_type VARCHAR,
        mapping_status VARCHAR,
        mapping_method VARCHAR,
        verification_status VARCHAR,
        mapping_note VARCHAR,
        evidence_url VARCHAR,
        equipment_rows BIGINT,
        declared_point_count BIGINT,
        charging_point_slots BIGINT,
        equipment_nominal_power_kw DOUBLE
    """
    conn.execute(f"CREATE OR REPLACE TEMP TABLE batch06_expected_crosswalk ({columns})")
    conn.executemany(
        "INSERT INTO batch06_expected_crosswalk VALUES (" + ",".join("?" for _ in TARGET_COLUMNS) + ")",
        [row_values(row) for row in rows],
    )


def object_type(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> str | None:
    schema, name = qualified_name.split(".", 1)
    result = conn.execute(
        """
        SELECT table_type
        FROM information_schema.tables
        WHERE table_schema = ? AND table_name = ?
        """,
        (schema, name),
    ).fetchone()
    return result[0] if result else None


def describe(conn: duckdb.DuckDBPyConnection, qualified_name: str) -> list[tuple[Any, ...]]:
    return conn.execute(f"DESCRIBE {qualified_name}").fetchall()


def validate_reference_table(
    conn: duckdb.DuckDBPyConnection,
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    require(object_type(conn, REFERENCE_TABLE) == "BASE TABLE", "Reference table is missing or not a table")
    columns = describe(conn, REFERENCE_TABLE)
    actual_columns = [(row[0], row[1]) for row in columns]
    expected_types = {
        "crosswalk_version": "VARCHAR",
        "bnetza_source_id": "VARCHAR",
        "bnetza_reference_date": "DATE",
        "kba_reference_date": "DATE",
        "bnetza_state_name": "VARCHAR",
        "bnetza_district_name": "VARCHAR",
        "bnetza_admin_type": "VARCHAR",
        "kba_state_name": "VARCHAR",
        "kba_district_code": "VARCHAR",
        "kba_district_name": "VARCHAR",
        "kba_admin_type": "VARCHAR",
        "mapping_status": "VARCHAR",
        "mapping_method": "VARCHAR",
        "verification_status": "VARCHAR",
        "mapping_note": "VARCHAR",
        "evidence_url": "VARCHAR",
        "equipment_rows": "BIGINT",
        "declared_point_count": "BIGINT",
        "charging_point_slots": "BIGINT",
        "equipment_nominal_power_kw": "DOUBLE",
    }
    require(
        actual_columns == [(name, expected_types[name]) for name in TARGET_COLUMNS],
        f"Reference table schema changed: {actual_columns}",
    )
    create_expected_crosswalk(conn, rows)
    select_columns = ", ".join(TARGET_COLUMNS)
    forward_diff = scalar(
        conn,
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT {select_columns} FROM {REFERENCE_TABLE}
            EXCEPT ALL
            SELECT {select_columns} FROM batch06_expected_crosswalk
        )
        """,
    )
    reverse_diff = scalar(
        conn,
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT {select_columns} FROM batch06_expected_crosswalk
            EXCEPT ALL
            SELECT {select_columns} FROM {REFERENCE_TABLE}
        )
        """,
    )
    require(forward_diff == 0 and reverse_diff == 0, "Reference table does not exactly match the CSV")
    duplicate_keys = scalar(
        conn,
        f"""
        SELECT COUNT(*) FROM (
            SELECT crosswalk_version, bnetza_source_id,
                   bnetza_state_name, bnetza_district_name
            FROM {REFERENCE_TABLE}
            GROUP BY 1, 2, 3, 4
            HAVING COUNT(*) <> 1
        )
        """,
    )
    duplicate_code_groups = conn.execute(
        f"""
        SELECT kba_district_code, COUNT(*)
        FROM {REFERENCE_TABLE}
        GROUP BY kba_district_code
        HAVING COUNT(*) > 1
        ORDER BY kba_district_code
        """
    ).fetchall()
    require(duplicate_keys == 0, "Duplicate source geography key in reference table")
    require(duplicate_code_groups == [("07211", 2)], f"Unexpected duplicate KBA code groups: {duplicate_code_groups}")
    provisional = scalar(
        conn,
        f"SELECT COUNT(*) FROM {REFERENCE_TABLE} WHERE verification_status LIKE 'provisional%'",
    )
    require(provisional == EXPECTED["provisional_rows"], f"Reference provisional rows: {provisional}")
    return {
        "rows": scalar(conn, f"SELECT COUNT(*) FROM {REFERENCE_TABLE}"),
        "unique_bnetza_keys": scalar(
            conn,
            f"""
            SELECT COUNT(*) FROM (
                SELECT bnetza_state_name, bnetza_district_name
                FROM {REFERENCE_TABLE}
                GROUP BY 1, 2
            )
            """,
        ),
        "unique_kba_codes": scalar(
            conn,
            f"SELECT COUNT(DISTINCT kba_district_code) FROM {REFERENCE_TABLE}",
        ),
        "provisional_rows": provisional,
    }


def validate_source_integrity(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    required_tables = {
        "core.charging_equipment",
        "core.charging_point",
        "core.kba_district_ev_stock",
    }
    actual_tables = {
        f"{row[0]}.{row[1]}"
        for row in conn.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            """
        ).fetchall()
    }
    require(required_tables <= actual_tables, "Required core tables are missing")
    equipment = scalar(conn, "SELECT COUNT(*) FROM core.charging_equipment")
    points = scalar(conn, "SELECT COUNT(*) FROM core.charging_point")
    require(equipment == EXPECTED["equipment"], f"Equipment rows: {equipment}")
    require(points == EXPECTED["points"], f"Charging points: {points}")
    source_ids = conn.execute(
        "SELECT source_id, COUNT(*) FROM core.charging_equipment GROUP BY source_id ORDER BY source_id"
    ).fetchall()
    require(source_ids == [(SOURCE_ID, EXPECTED["equipment"])], f"Unexpected BNetzA sources: {source_ids}")
    duplicate_equipment_keys = scalar(
        conn,
        """
        SELECT COUNT(*) FROM (
            SELECT source_id, excel_row
            FROM core.charging_equipment
            GROUP BY 1, 2
            HAVING COUNT(*) <> 1
        )
        """,
    )
    duplicate_point_keys = scalar(
        conn,
        """
        SELECT COUNT(*) FROM (
            SELECT source_id, equipment_excel_row, point_number
            FROM core.charging_point
            GROUP BY 1, 2, 3
            HAVING COUNT(*) <> 1
        )
        """,
    )
    orphan_points = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM core.charging_point p
        LEFT JOIN core.charging_equipment e
          ON e.source_id = p.source_id
         AND e.excel_row = p.equipment_excel_row
        WHERE e.source_id IS NULL
        """,
    )
    mismatch_equipment = scalar(
        conn,
        """
        SELECT COUNT(*) FROM (
            SELECT e.source_id, e.excel_row,
                   COALESCE(e.declared_point_count, 0) AS declared_points,
                   COUNT(p.point_number) AS point_slots
            FROM core.charging_equipment e
            LEFT JOIN core.charging_point p
              ON p.source_id = e.source_id
             AND p.equipment_excel_row = e.excel_row
            GROUP BY 1, 2, 3
            HAVING COALESCE(e.declared_point_count, 0) <> COUNT(p.point_number)
        )
        """,
    )
    require(duplicate_equipment_keys == 0, "Duplicate equipment source keys")
    require(duplicate_point_keys == 0, "Duplicate charging-point source keys")
    require(orphan_points == 0, f"Orphan charging points: {orphan_points}")
    require(mismatch_equipment == 0, f"Equipment/point count mismatches: {mismatch_equipment}")

    equipment_mapping = conn.execute(
        f"""
        SELECT
            COUNT(*) AS rows,
            COUNT(*) FILTER (WHERE matches = 0) AS unmatched,
            COUNT(*) FILTER (WHERE matches <> 1) AS not_exact
        FROM (
            SELECT e.source_id, e.excel_row,
                   COUNT(c.bnetza_state_name) AS matches
            FROM core.charging_equipment e
            LEFT JOIN {REFERENCE_TABLE} c
              ON c.bnetza_source_id = e.source_id
             AND c.bnetza_state_name = e.state_name
             AND c.bnetza_district_name = e.district_name
            GROUP BY e.source_id, e.excel_row
        )
        """
    ).fetchone()
    point_mapping = conn.execute(
        f"""
        SELECT
            COUNT(*) AS rows,
            COUNT(*) FILTER (WHERE matches = 0) AS unmatched,
            COUNT(*) FILTER (WHERE matches <> 1) AS not_exact
        FROM (
            SELECT p.source_id, p.equipment_excel_row, p.point_number,
                   COUNT(c.bnetza_state_name) AS matches
            FROM core.charging_point p
            LEFT JOIN core.charging_equipment e
              ON e.source_id = p.source_id
             AND e.excel_row = p.equipment_excel_row
            LEFT JOIN {REFERENCE_TABLE} c
              ON c.bnetza_source_id = e.source_id
             AND c.bnetza_state_name = e.state_name
             AND c.bnetza_district_name = e.district_name
            GROUP BY p.source_id, p.equipment_excel_row, p.point_number
        )
        """
    ).fetchone()
    require(equipment_mapping == (EXPECTED["equipment"], 0, 0), f"Equipment mapping: {equipment_mapping}")
    require(point_mapping == (EXPECTED["points"], 0, 0), f"Point mapping: {point_mapping}")
    source_geographies = scalar(
        conn,
        """
        SELECT COUNT(*) FROM (
            SELECT DISTINCT state_name, district_name
            FROM core.charging_equipment
        )
        """,
    )
    require(source_geographies == EXPECTED["crosswalk_rows"], f"Source geographies: {source_geographies}")
    kba_dates = conn.execute(
        """
        SELECT reference_date, COUNT(*), COUNT(DISTINCT district_code)
        FROM core.kba_district_ev_stock
        GROUP BY reference_date
        ORDER BY reference_date
        """
    ).fetchall()
    require(
        kba_dates == [(date, 400, 400) for date in KBA_DATES],
        f"KBA district date counts: {kba_dates}",
    )
    return {
        "equipment_rows": equipment,
        "charging_points": points,
        "orphan_points": orphan_points,
        "duplicate_equipment_keys": duplicate_equipment_keys,
        "duplicate_point_keys": duplicate_point_keys,
        "equipment_point_mismatches": mismatch_equipment,
        "equipment_mapping": equipment_mapping,
        "point_mapping": point_mapping,
        "source_geographies": source_geographies,
        "kba_rows_by_date": kba_dates,
    }


def validate_regional_view(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    require(object_type(conn, REGIONAL_VIEW) == "VIEW", "Regional view is missing")
    rows = scalar(conn, f"SELECT COUNT(*) FROM {REGIONAL_VIEW}")
    unique_codes = scalar(conn, f"SELECT COUNT(DISTINCT kba_district_code) FROM {REGIONAL_VIEW}")
    null_codes = scalar(conn, f"SELECT COUNT(*) FROM {REGIONAL_VIEW} WHERE kba_district_code IS NULL")
    duplicate_codes = scalar(
        conn,
        f"""
        SELECT COUNT(*) FROM (
            SELECT kba_district_code
            FROM {REGIONAL_VIEW}
            GROUP BY kba_district_code
            HAVING COUNT(*) <> 1
        )
        """,
    )
    require(rows == EXPECTED["regional_rows"], f"Regional rows: {rows}")
    require(unique_codes == EXPECTED["crosswalk_codes"], f"Regional KBA codes: {unique_codes}")
    require(null_codes == 0, f"Unmapped regional rows: {null_codes}")
    require(duplicate_codes == 0, f"Duplicate regional KBA codes: {duplicate_codes}")
    band_issues = scalar(
        conn,
        f"""
        SELECT COUNT(*)
        FROM {REGIONAL_VIEW}
        WHERE normal_charging_point_count
              + fast_charging_point_count
              + points_without_valid_power <> charging_point_count
           OR points_ge_150_kw > fast_charging_point_count
           OR points_ge_350_kw > points_ge_150_kw
        """,
    )
    require(band_issues == 0, f"Regional power-band identity issues: {band_issues}")
    totals = conn.execute(
        f"""
        SELECT
            SUM(equipment_count),
            SUM(charging_point_count),
            SUM(declared_charging_point_count),
            SUM(normal_charging_point_count),
            SUM(fast_charging_point_count),
            SUM(points_ge_150_kw),
            SUM(points_ge_350_kw),
            SUM(points_without_valid_power),
            SUM(equipment_nominal_power_mw),
            SUM(source_geography_rows),
            SUM(provisional_mapping_rows)
        FROM {REGIONAL_VIEW}
        """
    ).fetchone()
    require(totals[0] == EXPECTED["equipment"], f"Regional equipment total: {totals[0]}")
    require(totals[1] == EXPECTED["points"], f"Regional point total: {totals[1]}")
    require(totals[2] == EXPECTED["declared_points"], f"Regional declared point total: {totals[2]}")
    require(totals[3] == EXPECTED["normal_points"], f"Regional normal point total: {totals[3]}")
    require(totals[4] == EXPECTED["fast_points"], f"Regional fast point total: {totals[4]}")
    require(totals[5] == EXPECTED["points_ge_150"], f"Regional >=150 kW total: {totals[5]}")
    require(totals[6] == EXPECTED["points_ge_350"], f"Regional >=350 kW total: {totals[6]}")
    require(totals[7] == 0, f"Unclassifiable point total: {totals[7]}")
    require(abs(float(totals[8]) - EXPECTED_NOMINAL_MW) < 1e-6, f"Regional nominal MW: {totals[8]}")
    require(totals[9] == EXPECTED["crosswalk_rows"], f"Regional source geography rows: {totals[9]}")
    require(totals[10] == EXPECTED["provisional_rows"], f"Regional provisional rows: {totals[10]}")
    bad_date = scalar(
        conn,
        f"SELECT COUNT(*) FROM {REGIONAL_VIEW} WHERE bnetza_reference_date <> ?",
        (BNETZA_DATE,),
    )
    require(bad_date == 0, f"Unexpected BNetzA regional reference dates: {bad_date}")
    trier = conn.execute(
        f"""
        SELECT source_geography_rows, provisional_mapping_rows, equipment_count,
               charging_point_count
        FROM {REGIONAL_VIEW}
        WHERE kba_district_code = '07211'
        """
    ).fetchall()
    require(trier == [(2, 2, 276, 503)], f"Trier regional reconciliation: {trier}")
    return {
        "rows": rows,
        "unique_codes": unique_codes,
        "totals": totals,
        "trier_row": trier[0],
    }


def validate_combined_view(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    require(object_type(conn, COMBINED_VIEW) == "VIEW", "Combined view is missing")
    rows = scalar(conn, f"SELECT COUNT(*) FROM {COMBINED_VIEW}")
    duplicate_keys = scalar(
        conn,
        f"""
        SELECT COUNT(*) FROM (
            SELECT kba_district_code, kba_reference_date
            FROM {COMBINED_VIEW}
            GROUP BY 1, 2
            HAVING COUNT(*) <> 1
        )
        """,
    )
    by_date = conn.execute(
        f"""
        SELECT kba_reference_date, COUNT(*), COUNT(DISTINCT kba_district_code),
               SUM(bev_cars), SUM(phev_cars)
        FROM {COMBINED_VIEW}
        GROUP BY kba_reference_date
        ORDER BY kba_reference_date
        """
    ).fetchall()
    expected_by_date = [
        (date, 400, 400, EXPECTED_BEV[date], EXPECTED_PHEV_JULY if date == KBA_DATES[-1] else None)
        for date in KBA_DATES
    ]
    require(rows == EXPECTED["combined_rows"], f"Combined rows: {rows}")
    require(duplicate_keys == 0, f"Combined duplicate keys: {duplicate_keys}")
    require(
        [(row[0], row[1], row[2], row[3]) for row in by_date]
        == [(row[0], row[1], row[2], row[3]) for row in expected_by_date],
        f"Combined KBA BEV reconciliation: {by_date}",
    )
    require(by_date[-1][4] == EXPECTED_PHEV_JULY, f"July PHEV total: {by_date[-1][4]}")
    unmatched_stock = scalar(
        conn,
        f"SELECT COUNT(*) FROM {COMBINED_VIEW} WHERE kba_reference_date IS NULL",
    )
    bad_infrastructure_date = scalar(
        conn,
        f"SELECT COUNT(*) FROM {COMBINED_VIEW} WHERE bnetza_reference_date <> ?",
        (BNETZA_DATE,),
    )
    require(unmatched_stock == 0, f"Unmatched KBA stock rows: {unmatched_stock}")
    require(bad_infrastructure_date == 0, f"Unexpected combined BNetzA dates: {bad_infrastructure_date}")
    repeated_infrastructure = scalar(
        conn,
        f"""
        SELECT COUNT(*) FROM (
            SELECT kba_district_code
            FROM {COMBINED_VIEW}
            GROUP BY kba_district_code
            HAVING COUNT(DISTINCT equipment_count) > 1
                OR COUNT(DISTINCT charging_point_count) > 1
                OR COUNT(DISTINCT equipment_nominal_power_kw) > 1
        )
        """,
    )
    require(repeated_infrastructure == 0, "Infrastructure measures vary across repeated KBA dates")
    trier_july = conn.execute(
        f"""
        SELECT COUNT(*), SUM(bev_cars)
        FROM {COMBINED_VIEW}
        WHERE kba_district_code = '07211'
          AND kba_reference_date = DATE '2026-07-01'
        """
    ).fetchone()
    require(trier_july == (1, EXPECTED_TRIER_JULY_BEV), f"July Trier stock: {trier_july}")
    return {
        "rows": rows,
        "duplicate_keys": duplicate_keys,
        "by_date": by_date,
        "trier_july": trier_july,
    }


def validate_direct_core_reconciliation(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    result = conn.execute(
        f"""
        WITH current_crosswalk AS (
            SELECT *
            FROM {REFERENCE_TABLE}
            WHERE crosswalk_version = '{CROSSWALK_VERSION}'
              AND bnetza_source_id = '{SOURCE_ID}'
              AND bnetza_reference_date = DATE '{BNETZA_DATE.isoformat()}'
        ),
        source_equipment AS (
            SELECT e.*, c.kba_district_code
            FROM core.charging_equipment e
            LEFT JOIN current_crosswalk c
              ON c.bnetza_source_id = e.source_id
             AND c.bnetza_state_name = e.state_name
             AND c.bnetza_district_name = e.district_name
            WHERE e.source_id = '{SOURCE_ID}'
        ),
        source_points AS (
            SELECT p.source_id, p.equipment_excel_row, p.point_number,
                   p.connector_power_raw, e.kba_district_code
            FROM core.charging_point p
            LEFT JOIN source_equipment e
              ON e.source_id = p.source_id
             AND e.excel_row = p.equipment_excel_row
            WHERE p.source_id = '{SOURCE_ID}'
        ),
        point_power_tokens AS (
            SELECT source_id, equipment_excel_row, point_number,
                   TRY_CAST(REPLACE(TRIM(token), ',', '.') AS DOUBLE) AS power_kw
            FROM source_points
            CROSS JOIN LATERAL UNNEST(
                STRING_SPLIT(COALESCE(connector_power_raw, ''), ';')
            ) AS tokens(token)
        ),
        point_power AS (
            SELECT source_id, equipment_excel_row, point_number,
                   MAX(power_kw) AS max_power_kw
            FROM point_power_tokens
            GROUP BY 1, 2, 3
        ),
        equipment_total AS (
            SELECT COUNT(*) AS equipment_count,
                   SUM(COALESCE(declared_point_count, 0)) AS declared_points,
                   SUM(COALESCE(equipment_nominal_power_kw, 0.0)) / 1000.0
                       AS nominal_mw,
                   COUNT(DISTINCT kba_district_code) AS kba_codes
            FROM source_equipment
        ),
        point_total AS (
            SELECT COUNT(*) AS point_count,
                   COUNT(*) FILTER (WHERE pp.max_power_kw <= 22) AS normal_points,
                   COUNT(*) FILTER (WHERE pp.max_power_kw > 22) AS fast_points,
                   COUNT(*) FILTER (WHERE pp.max_power_kw >= 150) AS points_ge_150,
                   COUNT(*) FILTER (WHERE pp.max_power_kw >= 350) AS points_ge_350,
                   COUNT(*) FILTER (WHERE pp.max_power_kw IS NULL) AS unclassifiable_points,
                   COUNT(DISTINCT sp.kba_district_code) AS kba_codes
            FROM source_points sp
            LEFT JOIN point_power pp
              ON pp.source_id = sp.source_id
             AND pp.equipment_excel_row = sp.equipment_excel_row
             AND pp.point_number = sp.point_number
        )
        SELECT * FROM equipment_total CROSS JOIN point_total
        """
    ).fetchone()
    require(result[0] == EXPECTED["equipment"], f"Direct equipment count: {result[0]}")
    require(result[1] == EXPECTED["declared_points"], f"Direct declared points: {result[1]}")
    require(abs(float(result[2]) - EXPECTED_NOMINAL_MW) < 1e-6, f"Direct nominal MW: {result[2]}")
    require(result[3] == EXPECTED["crosswalk_codes"], f"Direct equipment KBA codes: {result[3]}")
    require(result[4] == EXPECTED["points"], f"Direct point count: {result[4]}")
    require(result[5] == EXPECTED["normal_points"], f"Direct normal points: {result[5]}")
    require(result[6] == EXPECTED["fast_points"], f"Direct fast points: {result[6]}")
    require(result[7] == EXPECTED["points_ge_150"], f"Direct >=150 kW points: {result[7]}")
    require(result[8] == EXPECTED["points_ge_350"], f"Direct >=350 kW points: {result[8]}")
    require(result[9] == 0, f"Direct unclassifiable points: {result[9]}")
    require(result[10] == EXPECTED["crosswalk_codes"], f"Direct point KBA codes: {result[10]}")
    regional_totals = conn.execute(
        f"""
        SELECT SUM(equipment_count), SUM(declared_charging_point_count),
               SUM(equipment_nominal_power_mw), SUM(charging_point_count),
               SUM(normal_charging_point_count), SUM(fast_charging_point_count),
               SUM(points_ge_150_kw), SUM(points_ge_350_kw)
        FROM {REGIONAL_VIEW}
        """
    ).fetchone()
    require(regional_totals[0] == result[0], "Regional equipment differs from direct core reconciliation")
    require(regional_totals[1] == result[1], "Regional declared points differ from direct reconciliation")
    require(abs(float(regional_totals[2]) - float(result[2])) < 1e-9, "Regional nominal power differs from direct reconciliation")
    require(tuple(regional_totals[3:]) == tuple(result[4:9]), "Regional point bands differ from direct reconciliation")
    return {"direct_totals": result, "regional_totals": regional_totals}


def validate_state_view(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    expected_columns = ["state_name", "equipment_rows", "declared_points", "populated_point_slots"]
    actual_columns = [row[0] for row in describe(conn, "analytics.charging_by_state")]
    require(actual_columns == expected_columns, f"State-view columns changed: {actual_columns}")
    view_rows = conn.execute(
        "SELECT state_name, equipment_rows, declared_points, populated_point_slots "
        "FROM analytics.charging_by_state ORDER BY state_name"
    ).fetchall()
    direct_rows = conn.execute(
        """
        SELECT e.state_name,
               COUNT(*) AS equipment_rows,
               SUM(e.declared_point_count) AS declared_points,
               SUM(COALESCE(p.point_slots, 0)) AS populated_point_slots
        FROM core.charging_equipment e
        LEFT JOIN (
            SELECT source_id, equipment_excel_row, COUNT(*) AS point_slots
            FROM core.charging_point
            GROUP BY source_id, equipment_excel_row
        ) p
          ON e.source_id = p.source_id
         AND e.excel_row = p.equipment_excel_row
        GROUP BY e.state_name
        ORDER BY e.state_name
        """
    ).fetchall()
    require(len(view_rows) == 16, f"State rows: {len(view_rows)}")
    require(view_rows == direct_rows, "State view differs from independent source-aware aggregation")
    return {"rows": view_rows, "state_count": len(view_rows)}


def validate_database(database: Path, crosswalk: Path) -> dict[str, Any]:
    rows = read_crosswalk(crosswalk)
    conn = duckdb.connect(str(database), read_only=True)
    try:
        reference = validate_reference_table(conn, rows)
        source = validate_source_integrity(conn)
        regional = validate_regional_view(conn)
        combined = validate_combined_view(conn)
        direct = validate_direct_core_reconciliation(conn)
        state = validate_state_view(conn)
        return {
            "database": str(database),
            "reference": reference,
            "source": source,
            "regional": regional,
            "combined": combined,
            "direct_core_reconciliation": direct,
            "state_view": state,
        }
    finally:
        conn.close()


def json_default(value: Any) -> str:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--json", action="store_true", help="Print the result as JSON")
    args = parser.parse_args()
    database = args.database if args.database.is_absolute() else ROOT / args.database
    crosswalk = args.crosswalk if args.crosswalk.is_absolute() else ROOT / args.crosswalk
    try:
        result = validate_database(database, crosswalk)
    except Exception as exc:
        print(f"[FAIL] Batch 06 validation: {exc}")
        return 1
    print("[PASS] Batch 06 independent read-only validation")
    if args.json:
        print(json.dumps(result, indent=2, default=json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
