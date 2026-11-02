-- Batch 13.2: historical BBSR 2025 boundary harmonization for Hanau.
--
-- This is a new, versioned layer.  It preserves the official Batch 13
-- bridge/views and the owner-approved Batch 13.1 scenario unchanged.  The
-- source grain remains the BNetzA 2026-09-30 state/district grain; only the
-- analytical target geography is harmonized to the BBSR 2025 stand.

-- name: create_reference_schema
CREATE SCHEMA IF NOT EXISTS reference;

-- name: create_analytics_schema
CREATE SCHEMA IF NOT EXISTS analytics;

-- name: create_harmonization_table
CREATE TABLE IF NOT EXISTS reference.bnetza_bbsr_historical_harmonization_2025 (
    harmonization_version VARCHAR NOT NULL,
    bnetza_source_id VARCHAR NOT NULL,
    bnetza_reference_date DATE NOT NULL,
    bnetza_state_name VARCHAR NOT NULL,
    bnetza_district_name VARCHAR NOT NULL,
    bnetza_admin_type VARCHAR NOT NULL,
    historical_bbsr_reference_date DATE NOT NULL,
    historical_bbsr_source_version VARCHAR NOT NULL,
    historical_bbsr_source_sha256 VARCHAR NOT NULL,
    historical_bbsr_administrative_district_code VARCHAR NOT NULL,
    historical_bbsr_administrative_district_name VARCHAR NOT NULL,
    historical_bbsr_federal_state_code VARCHAR NOT NULL,
    historical_bbsr_federal_state_name VARCHAR NOT NULL,
    historical_bbsr_kreisregion_code VARCHAR NOT NULL,
    historical_bbsr_kreisregion_name VARCHAR NOT NULL,
    historical_bbsr_settlement_type_code VARCHAR NOT NULL,
    historical_bbsr_settlement_type_name_de VARCHAR NOT NULL,
    source_component_role VARCHAR NOT NULL,
    mapping_method VARCHAR NOT NULL,
    boundary_compatibility_status VARCHAR NOT NULL,
    evidence_source_reference VARCHAR NOT NULL,
    validation_notes VARCHAR NOT NULL,
    UNIQUE (
        harmonization_version,
        bnetza_source_id,
        bnetza_state_name,
        bnetza_district_name
    )
);

-- name: replace_harmonization_rows
DELETE FROM reference.bnetza_bbsr_historical_harmonization_2025
WHERE harmonization_version = '{{HARMONIZATION_VERSION}}';

INSERT INTO reference.bnetza_bbsr_historical_harmonization_2025 (
    harmonization_version,
    bnetza_source_id,
    bnetza_reference_date,
    bnetza_state_name,
    bnetza_district_name,
    bnetza_admin_type,
    historical_bbsr_reference_date,
    historical_bbsr_source_version,
    historical_bbsr_source_sha256,
    historical_bbsr_administrative_district_code,
    historical_bbsr_administrative_district_name,
    historical_bbsr_federal_state_code,
    historical_bbsr_federal_state_name,
    historical_bbsr_kreisregion_code,
    historical_bbsr_kreisregion_name,
    historical_bbsr_settlement_type_code,
    historical_bbsr_settlement_type_name_de,
    source_component_role,
    mapping_method,
    boundary_compatibility_status,
    evidence_source_reference,
    validation_notes
)
SELECT
    NULLIF(TRIM(harmonization_version), ''),
    NULLIF(TRIM(bnetza_source_id), ''),
    TRY_CAST(NULLIF(TRIM(bnetza_reference_date), '') AS DATE),
    NULLIF(bnetza_state_name, ''),
    NULLIF(bnetza_district_name, ''),
    NULLIF(TRIM(bnetza_admin_type), ''),
    TRY_CAST(NULLIF(TRIM(historical_bbsr_reference_date), '') AS DATE),
    NULLIF(historical_bbsr_source_version, ''),
    NULLIF(TRIM(historical_bbsr_source_sha256), ''),
    NULLIF(TRIM(historical_bbsr_administrative_district_code), ''),
    NULLIF(historical_bbsr_administrative_district_name, ''),
    NULLIF(TRIM(historical_bbsr_federal_state_code), ''),
    NULLIF(historical_bbsr_federal_state_name, ''),
    NULLIF(TRIM(historical_bbsr_kreisregion_code), ''),
    NULLIF(historical_bbsr_kreisregion_name, ''),
    NULLIF(TRIM(historical_bbsr_settlement_type_code), ''),
    NULLIF(historical_bbsr_settlement_type_name_de, ''),
    NULLIF(TRIM(source_component_role), ''),
    NULLIF(TRIM(mapping_method), ''),
    NULLIF(TRIM(boundary_compatibility_status), ''),
    NULLIF(evidence_source_reference, ''),
    NULLIF(validation_notes, '')
FROM read_csv(
    {{HARMONIZATION_CSV}},
    header = true,
    all_varchar = true,
    nullstr = ''
);

-- name: charging_by_historical_bbsr_district_view
CREATE OR REPLACE VIEW analytics.charging_by_bbsr_district_2025_harmonized AS
WITH mapping AS (
    SELECT *
    FROM reference.bnetza_bbsr_historical_harmonization_2025
    WHERE harmonization_version = '{{HARMONIZATION_VERSION}}'
      AND bnetza_source_id = '{{SOURCE_ID}}'
      AND bnetza_reference_date = DATE '{{BNETZA_DATE}}'
),
source_equipment AS (
    SELECT
        e.source_id,
        e.excel_row AS equipment_excel_row,
        e.state_name,
        e.district_name,
        e.status,
        COALESCE(NULLIF(TRIM(e.status), ''), '[NULL]') AS equipment_status,
        e.declared_point_count,
        e.equipment_nominal_power_kw
    FROM core.charging_equipment e
    WHERE e.source_id = '{{SOURCE_ID}}'
),
source_points AS (
    SELECT
        p.source_id,
        p.equipment_excel_row,
        p.point_number,
        p.connector_power_raw,
        e.state_name,
        e.district_name
    FROM core.charging_point p
    INNER JOIN source_equipment e
      ON e.source_id = p.source_id
     AND e.equipment_excel_row = p.equipment_excel_row
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
equipment_by_source AS (
    SELECT
        source_id,
        state_name,
        district_name,
        COUNT(*) AS equipment_count,
        SUM(COALESCE(declared_point_count, 0))
            AS declared_charging_point_count,
        SUM(COALESCE(equipment_nominal_power_kw, 0.0))
            AS total_equipment_nominal_power_kw,
        STRING_AGG(
            DISTINCT equipment_status,
            '; ' ORDER BY equipment_status
        ) AS equipment_statuses_present
    FROM source_equipment
    GROUP BY source_id, state_name, district_name
),
points_by_source AS (
    SELECT
        p.source_id,
        p.state_name,
        p.district_name,
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
        ) AS unclassifiable_power_point_count
    FROM source_points p
    LEFT JOIN point_power pp
      ON pp.source_id = p.source_id
     AND pp.equipment_excel_row = p.equipment_excel_row
     AND pp.point_number = p.point_number
    GROUP BY p.source_id, p.state_name, p.district_name
),
source_metrics AS (
    SELECT
        COALESCE(e.source_id, p.source_id) AS source_id,
        COALESCE(e.state_name, p.state_name) AS state_name,
        COALESCE(e.district_name, p.district_name) AS district_name,
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
        COALESCE(p.unclassifiable_power_point_count, 0)
            AS unclassifiable_power_point_count,
        COALESCE(e.total_equipment_nominal_power_kw, 0.0)
            AS total_equipment_nominal_power_kw,
        COALESCE(e.equipment_statuses_present, '')
            AS equipment_statuses_present
    FROM equipment_by_source e
    FULL OUTER JOIN points_by_source p
      ON e.source_id = p.source_id
     AND e.state_name = p.state_name
     AND e.district_name = p.district_name
),
historical_targets AS (
    SELECT
        m.harmonization_version,
        MIN(m.bnetza_reference_date) AS infrastructure_reference_date,
        MIN(m.historical_bbsr_reference_date) AS historical_bbsr_reference_date,
        MIN(m.historical_bbsr_source_version) AS historical_bbsr_source_version,
        MIN(m.historical_bbsr_source_sha256) AS historical_bbsr_source_sha256,
        m.historical_bbsr_administrative_district_code,
        MIN(m.historical_bbsr_administrative_district_name)
            AS historical_bbsr_administrative_district_name,
        MIN(m.historical_bbsr_federal_state_code)
            AS historical_bbsr_federal_state_code,
        MIN(m.historical_bbsr_federal_state_name)
            AS historical_bbsr_federal_state_name,
        MIN(m.historical_bbsr_kreisregion_code)
            AS historical_bbsr_kreisregion_code,
        MIN(m.historical_bbsr_kreisregion_name)
            AS historical_bbsr_kreisregion_name,
        m.historical_bbsr_settlement_type_code,
        MIN(m.historical_bbsr_settlement_type_name_de)
            AS historical_bbsr_settlement_type_name_de,
        CASE
            WHEN COUNT(*) FILTER (
                WHERE m.source_component_role IN (
                    'HISTORICAL_COMPONENT_HANAU',
                    'HISTORICAL_COMPONENT_REMAINING_MKK'
                )
            ) > 0
                THEN 'HISTORICAL_MKK_PRE_2026_BOUNDARY_RECONSTRUCTION'
            ELSE 'DIRECT_BBSR_2025_ADMINISTRATIVE_UNIT'
        END AS historical_boundary_basis,
        STRING_AGG(
            m.bnetza_district_name,
            '; ' ORDER BY m.bnetza_district_name
        ) AS source_component_names,
        COUNT(*) AS source_component_count,
        MIN(m.mapping_method) AS mapping_method,
        MIN(m.boundary_compatibility_status)
            AS boundary_compatibility_status,
        MIN(m.evidence_source_reference) AS evidence_source_reference,
        STRING_AGG(
            DISTINCT m.validation_notes,
            ' | ' ORDER BY m.validation_notes
        ) AS validation_notes,
        SUM(COALESCE(s.equipment_count, 0)) AS equipment_count,
        SUM(COALESCE(s.charging_point_count, 0)) AS charging_point_count,
        SUM(COALESCE(s.declared_charging_point_count, 0))
            AS declared_charging_point_count,
        SUM(COALESCE(s.normal_charging_point_count, 0))
            AS normal_charging_point_count,
        SUM(COALESCE(s.fast_charging_point_count, 0))
            AS fast_charging_point_count,
        SUM(COALESCE(s.points_ge_150_kw, 0)) AS points_ge_150_kw,
        SUM(COALESCE(s.points_ge_350_kw, 0)) AS points_ge_350_kw,
        SUM(COALESCE(s.unclassifiable_power_point_count, 0))
            AS unclassifiable_power_point_count,
        SUM(COALESCE(s.total_equipment_nominal_power_kw, 0.0))
            AS total_equipment_nominal_power_kw,
        STRING_AGG(
            DISTINCT COALESCE(s.equipment_statuses_present, ''),
            '; ' ORDER BY COALESCE(s.equipment_statuses_present, '')
        ) AS equipment_statuses_present
    FROM mapping m
    LEFT JOIN source_metrics s
      ON s.source_id = m.bnetza_source_id
     AND s.state_name = m.bnetza_state_name
     AND s.district_name = m.bnetza_district_name
    GROUP BY
        m.harmonization_version,
        m.historical_bbsr_administrative_district_code,
        m.historical_bbsr_settlement_type_code
)
SELECT
    harmonization_version,
    'BNetzA infrastructure 2026-09-30; historical BBSR geographic stand 2025-12-31'
        AS analysis_source_vintage,
    infrastructure_reference_date,
    historical_bbsr_reference_date,
    historical_bbsr_source_version,
    historical_bbsr_source_sha256,
    historical_bbsr_administrative_district_code,
    historical_bbsr_administrative_district_name,
    historical_bbsr_federal_state_code,
    historical_bbsr_federal_state_name,
    historical_bbsr_kreisregion_code,
    historical_bbsr_kreisregion_name,
    historical_bbsr_settlement_type_code,
    historical_bbsr_settlement_type_name_de,
    historical_boundary_basis,
    source_component_count,
    source_component_names,
    mapping_method,
    boundary_compatibility_status,
    evidence_source_reference,
    validation_notes,
    equipment_count,
    charging_point_count,
    declared_charging_point_count,
    normal_charging_point_count,
    fast_charging_point_count,
    points_ge_150_kw,
    points_ge_350_kw,
    unclassifiable_power_point_count,
    ROUND(
        100.0 * fast_charging_point_count
        / NULLIF(charging_point_count, 0),
        2
    ) AS fast_point_share_pct,
    ROUND(
        100.0 * points_ge_150_kw
        / NULLIF(charging_point_count, 0),
        2
    ) AS high_power_point_share_pct,
    total_equipment_nominal_power_kw,
    total_equipment_nominal_power_kw / 1000.0
        AS total_equipment_nominal_power_mw,
    equipment_statuses_present
FROM historical_targets;

-- name: charging_by_historical_bbsr_type_view
CREATE OR REPLACE VIEW analytics.charging_by_bbsr_type_2025_harmonized AS
WITH category_labels (settlement_type_code, settlement_type_name_de) AS (
    VALUES
        ('1', 'kreisfreie Großstadt'),
        ('2', 'städtischer Kreis'),
        ('3', 'ländlicher Kreis mit Verdichtungsansätzen'),
        ('4', 'dünn besiedelter ländlicher Kreis')
),
aggregated AS (
    SELECT
        historical_bbsr_settlement_type_code AS settlement_type_code,
        historical_bbsr_settlement_type_name_de AS settlement_type_name_de,
        COUNT(*) AS historical_district_count,
        SUM(source_component_count) AS source_component_count,
        SUM(equipment_count) AS equipment_count,
        SUM(charging_point_count) AS charging_point_count,
        SUM(normal_charging_point_count) AS normal_charging_point_count,
        SUM(fast_charging_point_count) AS fast_charging_point_count,
        SUM(points_ge_150_kw) AS points_ge_150_kw,
        SUM(points_ge_350_kw) AS points_ge_350_kw,
        SUM(unclassifiable_power_point_count)
            AS unclassifiable_power_point_count,
        SUM(total_equipment_nominal_power_kw)
            AS total_equipment_nominal_power_kw
    FROM analytics.charging_by_bbsr_district_2025_harmonized
    GROUP BY
        historical_bbsr_settlement_type_code,
        historical_bbsr_settlement_type_name_de
),
national AS (
    SELECT
        SUM(charging_point_count) AS all_registered_charging_points,
        SUM(source_component_count) AS all_source_components,
        COUNT(*) AS all_historical_districts
    FROM analytics.charging_by_bbsr_district_2025_harmonized
)
SELECT
    '{{HARMONIZATION_VERSION}}' AS harmonization_version,
    'BNetzA infrastructure 2026-09-30; historical BBSR geographic stand 2025-12-31'
        AS analysis_source_vintage,
    labels.settlement_type_code,
    labels.settlement_type_name_de,
    COALESCE(a.historical_district_count, 0) AS historical_district_count,
    COALESCE(a.source_component_count, 0) AS source_component_count,
    COALESCE(a.equipment_count, 0) AS equipment_count,
    COALESCE(a.charging_point_count, 0) AS charging_point_count,
    COALESCE(a.normal_charging_point_count, 0)
        AS normal_charging_point_count,
    COALESCE(a.fast_charging_point_count, 0)
        AS fast_charging_point_count,
    COALESCE(a.points_ge_150_kw, 0) AS points_ge_150_kw,
    COALESCE(a.points_ge_350_kw, 0) AS points_ge_350_kw,
    COALESCE(a.unclassifiable_power_point_count, 0)
        AS unclassifiable_power_point_count,
    ROUND(
        100.0 * COALESCE(a.fast_charging_point_count, 0)
        / NULLIF(COALESCE(a.charging_point_count, 0), 0),
        2
    ) AS fast_charging_share_pct,
    ROUND(
        100.0 * COALESCE(a.points_ge_150_kw, 0)
        / NULLIF(COALESCE(a.charging_point_count, 0), 0),
        2
    ) AS high_power_share_pct,
    COALESCE(a.total_equipment_nominal_power_kw, 0.0)
        AS declared_equipment_nominal_power_kw,
    COALESCE(a.total_equipment_nominal_power_kw, 0.0) / 1000.0
        AS declared_equipment_nominal_power_mw,
    ROUND(
        100.0 * COALESCE(a.charging_point_count, 0)
        / NULLIF(national.all_registered_charging_points, 0),
        6
    ) AS national_charging_point_share_pct,
    national.all_historical_districts AS all_historical_district_count,
    national.all_source_components AS all_source_component_count,
    'HISTORICAL_BBSR_2025_TARGET_UNITS_FROM_BNETZA_2026_SOURCE'
        AS classification_scope,
    'ALL_REGISTERED_CHARGING_POINTS_INCLUDING_ALL_HISTORICAL_TARGET_UNITS'
        AS point_share_denominator_scope
FROM category_labels labels
LEFT JOIN aggregated a
  ON a.settlement_type_code = labels.settlement_type_code
CROSS JOIN national;
