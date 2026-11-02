-- Batch 06: deployed geographic analytics layer.
--
-- The deployment script executes these named statements in a controlled
-- transaction after read-only preflight and backup validation.  The
-- crosswalk CSV is loaded with explicit casts so KBA codes remain VARCHAR.

-- name: create_reference_schema
CREATE SCHEMA IF NOT EXISTS reference;

-- name: create_reference_table
CREATE TABLE IF NOT EXISTS reference.bnetza_kba_district_crosswalk_2026 (
    crosswalk_version VARCHAR NOT NULL,
    bnetza_source_id VARCHAR NOT NULL,
    bnetza_reference_date DATE NOT NULL,
    kba_reference_date DATE NOT NULL,
    bnetza_state_name VARCHAR NOT NULL,
    bnetza_district_name VARCHAR NOT NULL,
    bnetza_admin_type VARCHAR,
    kba_state_name VARCHAR,
    kba_district_code VARCHAR,
    kba_district_name VARCHAR,
    kba_admin_type VARCHAR,
    mapping_status VARCHAR NOT NULL,
    mapping_method VARCHAR NOT NULL,
    verification_status VARCHAR NOT NULL,
    mapping_note VARCHAR,
    evidence_url VARCHAR,
    equipment_rows BIGINT,
    declared_point_count BIGINT,
    charging_point_slots BIGINT,
    equipment_nominal_power_kw DOUBLE,
    UNIQUE (
        crosswalk_version,
        bnetza_source_id,
        bnetza_state_name,
        bnetza_district_name
    )
);

-- name: insert_reference_rows
INSERT INTO reference.bnetza_kba_district_crosswalk_2026 (
    crosswalk_version,
    bnetza_source_id,
    bnetza_reference_date,
    kba_reference_date,
    bnetza_state_name,
    bnetza_district_name,
    bnetza_admin_type,
    kba_state_name,
    kba_district_code,
    kba_district_name,
    kba_admin_type,
    mapping_status,
    mapping_method,
    verification_status,
    mapping_note,
    evidence_url,
    equipment_rows,
    declared_point_count,
    charging_point_slots,
    equipment_nominal_power_kw
)
SELECT
    NULLIF(TRIM(crosswalk_version), ''),
    '{{SOURCE_ID}}',
    TRY_CAST(NULLIF(TRIM(bnetza_reference_date), '') AS DATE),
    TRY_CAST(NULLIF(TRIM(kba_reference_date), '') AS DATE),
    NULLIF(bnetza_state_name, ''),
    NULLIF(bnetza_district_name, ''),
    NULLIF(bnetza_admin_type, ''),
    NULLIF(kba_state_name, ''),
    NULLIF(TRIM(kba_district_code), ''),
    NULLIF(kba_district_name, ''),
    NULLIF(kba_admin_type, ''),
    NULLIF(mapping_status, ''),
    NULLIF(mapping_method, ''),
    NULLIF(verification_status, ''),
    NULLIF(mapping_note, ''),
    NULLIF(evidence_url, ''),
    TRY_CAST(NULLIF(TRIM(equipment_rows), '') AS BIGINT),
    TRY_CAST(NULLIF(TRIM(declared_point_count), '') AS BIGINT),
    TRY_CAST(NULLIF(TRIM(charging_point_slots), '') AS BIGINT),
    TRY_CAST(REPLACE(NULLIF(TRIM(equipment_nominal_power_kw), ''), ',', '.') AS DOUBLE)
FROM read_csv(
    {{CROSSWALK_CSV}},
    header = true,
    all_varchar = true,
    nullstr = ''
);

-- name: charging_by_kba_district_view
CREATE OR REPLACE VIEW analytics.charging_by_kba_district_2026_09_30 AS
WITH current_crosswalk AS (
    SELECT *
    FROM reference.bnetza_kba_district_crosswalk_2026
    WHERE crosswalk_version = '{{CROSSWALK_VERSION}}'
      AND bnetza_source_id = '{{SOURCE_ID}}'
      AND bnetza_reference_date = DATE '{{BNETZA_DATE}}'
),
source_equipment AS (
    SELECT
        e.source_id,
        e.excel_row,
        e.state_name,
        e.district_name,
        e.declared_point_count,
        e.equipment_nominal_power_kw,
        c.kba_district_code,
        c.mapping_status AS source_mapping_status,
        c.verification_status AS source_verification_status
    FROM core.charging_equipment e
    LEFT JOIN current_crosswalk c
      ON c.bnetza_source_id = e.source_id
     AND c.bnetza_state_name = e.state_name
     AND c.bnetza_district_name = e.district_name
    WHERE e.source_id = '{{SOURCE_ID}}'
),
source_geography AS (
    SELECT DISTINCT
        source_id,
        state_name,
        district_name,
        kba_district_code,
        source_mapping_status,
        source_verification_status
    FROM source_equipment
),
source_points AS (
    SELECT
        p.source_id,
        p.equipment_excel_row,
        p.point_number,
        p.connector_power_raw,
        e.kba_district_code
    FROM core.charging_point p
    LEFT JOIN source_equipment e
      ON e.source_id = p.source_id
     AND e.excel_row = p.equipment_excel_row
    WHERE p.source_id = '{{SOURCE_ID}}'
),
point_power_tokens AS (
    SELECT
        p.source_id,
        p.equipment_excel_row,
        p.point_number,
        TRY_CAST(REPLACE(TRIM(token), ',', '.') AS DOUBLE) AS power_kw
    FROM source_points p
    CROSS JOIN LATERAL UNNEST(
        STRING_SPLIT(COALESCE(p.connector_power_raw, ''), ';')
    ) AS tokens(token)
),
point_power AS (
    SELECT
        source_id,
        equipment_excel_row,
        point_number,
        MAX(power_kw) AS max_declared_point_power_kw
    FROM point_power_tokens
    GROUP BY source_id, equipment_excel_row, point_number
),
equipment_by_code AS (
    SELECT
        source_id,
        kba_district_code,
        COUNT(*) AS equipment_count,
        SUM(COALESCE(declared_point_count, 0)) AS declared_charging_point_count,
        SUM(COALESCE(equipment_nominal_power_kw, 0.0))
            AS equipment_nominal_power_kw
    FROM source_equipment
    GROUP BY source_id, kba_district_code
),
points_by_code AS (
    SELECT
        p.source_id,
        p.kba_district_code,
        COUNT(*) AS charging_point_count,
        COUNT(*) FILTER (
            WHERE pp.max_declared_point_power_kw <= 22
        ) AS normal_charging_point_count,
        COUNT(*) FILTER (
            WHERE pp.max_declared_point_power_kw > 22
        ) AS fast_charging_point_count,
        COUNT(*) FILTER (
            WHERE pp.max_declared_point_power_kw >= 150
        ) AS points_ge_150_kw,
        COUNT(*) FILTER (
            WHERE pp.max_declared_point_power_kw >= 350
        ) AS points_ge_350_kw,
        COUNT(*) FILTER (
            WHERE pp.max_declared_point_power_kw IS NULL
        ) AS points_without_valid_power
    FROM source_points p
    LEFT JOIN point_power pp
      ON pp.source_id = p.source_id
     AND pp.equipment_excel_row = p.equipment_excel_row
     AND pp.point_number = p.point_number
    GROUP BY p.source_id, p.kba_district_code
),
mapping_by_code AS (
    SELECT
        kba_district_code,
        CASE
            WHEN kba_district_code IS NULL THEN 'unmapped'
            ELSE 'mapped'
        END AS mapping_status,
        CASE
            WHEN kba_district_code IS NULL THEN 'unmapped'
            WHEN COUNT(*) FILTER (
                WHERE source_verification_status LIKE 'provisional%'
            ) > 0 THEN 'provisional'
            ELSE 'observed_local_snapshot'
        END AS mapping_verification_status,
        COUNT(*) AS source_geography_rows,
        COUNT(*) FILTER (
            WHERE source_verification_status LIKE 'provisional%'
        ) AS provisional_mapping_rows,
        COUNT(*) FILTER (
            WHERE kba_district_code IS NULL
        ) AS unmapped_source_geography_rows
    FROM source_geography
    GROUP BY kba_district_code
),
regional AS (
    SELECT
        COALESCE(e.source_id, p.source_id) AS bnetza_source_id,
        COALESCE(e.kba_district_code, p.kba_district_code)
            AS kba_district_code,
        COALESCE(
            m.mapping_status,
            CASE
                WHEN COALESCE(e.kba_district_code, p.kba_district_code) IS NULL
                    THEN 'unmapped'
                ELSE 'mapped'
            END
        ) AS mapping_status,
        COALESCE(m.mapping_verification_status, 'unmapped')
            AS mapping_verification_status,
        COALESCE(m.source_geography_rows, 0) AS source_geography_rows,
        COALESCE(m.provisional_mapping_rows, 0)
            AS provisional_mapping_rows,
        COALESCE(m.unmapped_source_geography_rows, 0)
            AS unmapped_source_geography_rows,
        COALESCE(e.equipment_count, 0) AS equipment_count,
        COALESCE(p.charging_point_count, 0) AS charging_point_count,
        COALESCE(e.declared_charging_point_count, 0)
            AS declared_charging_point_count,
        COALESCE(p.normal_charging_point_count, 0)
            AS normal_charging_point_count,
        COALESCE(p.fast_charging_point_count, 0)
            AS fast_charging_point_count,
        COALESCE(p.points_ge_150_kw, 0) AS points_ge_150_kw,
        COALESCE(p.points_ge_350_kw, 0) AS points_ge_350_kw,
        COALESCE(p.points_without_valid_power, 0)
            AS points_without_valid_power,
        COALESCE(e.equipment_nominal_power_kw, 0.0)
            AS equipment_nominal_power_kw
    FROM equipment_by_code e
    FULL OUTER JOIN points_by_code p
      ON e.source_id = p.source_id
     AND e.kba_district_code IS NOT DISTINCT FROM p.kba_district_code
    LEFT JOIN mapping_by_code m
      ON m.kba_district_code IS NOT DISTINCT FROM
         COALESCE(e.kba_district_code, p.kba_district_code)
)
SELECT
    bnetza_source_id,
    kba_district_code,
    DATE '{{BNETZA_DATE}}' AS bnetza_reference_date,
    equipment_count,
    charging_point_count,
    declared_charging_point_count,
    normal_charging_point_count,
    fast_charging_point_count,
    points_ge_150_kw,
    points_ge_350_kw,
    points_without_valid_power,
    ROUND(
        100.0 * fast_charging_point_count
        / NULLIF(charging_point_count, 0),
        2
    ) AS fast_charging_share_pct,
    ROUND(
        100.0 * points_ge_150_kw
        / NULLIF(charging_point_count, 0),
        2
    ) AS high_power_charging_share_pct,
    equipment_nominal_power_kw,
    equipment_nominal_power_kw / 1000.0 AS equipment_nominal_power_mw,
    mapping_status,
    mapping_verification_status,
    source_geography_rows,
    provisional_mapping_rows,
    unmapped_source_geography_rows
FROM regional;

-- name: combined_kba_district_view
CREATE OR REPLACE VIEW analytics.kba_district_charging_vs_bev_2026 AS
SELECT
    c.bnetza_source_id,
    c.kba_district_code,
    k.state_name AS kba_state_name,
    k.district_name AS kba_district_name,
    k.reference_date AS kba_reference_date,
    c.bnetza_reference_date,
    k.source_id AS kba_source_id,
    k.passenger_cars,
    k.bev_cars,
    k.phev_cars,
    c.equipment_count,
    c.charging_point_count,
    c.declared_charging_point_count,
    c.normal_charging_point_count,
    c.fast_charging_point_count,
    c.points_ge_150_kw,
    c.points_ge_350_kw,
    c.points_without_valid_power,
    c.fast_charging_share_pct,
    c.high_power_charging_share_pct,
    c.equipment_nominal_power_kw,
    c.equipment_nominal_power_mw,
    CAST(k.bev_cars AS DOUBLE)
        / NULLIF(c.charging_point_count, 0)
        AS bev_per_registered_charging_point,
    c.mapping_status,
    c.mapping_verification_status,
    c.source_geography_rows,
    c.provisional_mapping_rows,
    c.unmapped_source_geography_rows
FROM analytics.charging_by_kba_district_2026_09_30 c
LEFT JOIN core.kba_district_ev_stock k
  ON k.district_code = c.kba_district_code;

-- name: source_aware_state_view
CREATE OR REPLACE VIEW analytics.charging_by_state AS
SELECT
    e.state_name,
    COUNT(*) AS equipment_rows,
    SUM(e.declared_point_count) AS declared_points,
    SUM(COALESCE(p.point_slots, 0)) AS populated_point_slots
FROM core.charging_equipment e
LEFT JOIN (
    SELECT
        source_id,
        equipment_excel_row,
        COUNT(*) AS point_slots
    FROM core.charging_point
    GROUP BY source_id, equipment_excel_row
) p
  ON e.source_id = p.source_id
 AND e.excel_row = p.equipment_excel_row
GROUP BY e.state_name;
