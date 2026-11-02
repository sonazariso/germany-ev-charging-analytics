-- Batch 13: separate BNetzA-to-BBSR charging-only enrichment.
--
-- The deployment script executes these named statements in one transaction
-- after read-only preflight and backup validation.  This layer stays at the
-- original BNetzA state/district grain and never joins KBA vehicle stock.

-- name: create_reference_schema
CREATE SCHEMA IF NOT EXISTS reference;

-- name: create_analytics_schema
CREATE SCHEMA IF NOT EXISTS analytics;

-- name: create_bridge_table
CREATE TABLE IF NOT EXISTS reference.bnetza_bbsr_district_bridge_2025 (
    bridge_version VARCHAR NOT NULL,
    source_audit_version VARCHAR NOT NULL,
    source_audit_sha256 VARCHAR NOT NULL,
    bnetza_source_id VARCHAR NOT NULL,
    bnetza_reference_date DATE NOT NULL,
    bnetza_state_name VARCHAR NOT NULL,
    bnetza_district_name VARCHAR NOT NULL,
    bnetza_admin_type VARCHAR NOT NULL,
    bbsr_reference_date DATE NOT NULL,
    bbsr_source_version VARCHAR NOT NULL,
    bbsr_source_sha256 VARCHAR NOT NULL,
    bbsr_administrative_district_code VARCHAR,
    bbsr_administrative_district_name VARCHAR,
    bbsr_federal_state_code VARCHAR,
    bbsr_federal_state_name VARCHAR,
    bbsr_kreisregion_code VARCHAR,
    bbsr_kreisregion_name VARCHAR,
    bbsr_settlement_type_code VARCHAR,
    bbsr_settlement_type_name_de VARCHAR,
    geographic_compatibility_status VARCHAR NOT NULL,
    evidence_method VARCHAR NOT NULL,
    evidence_source_reference VARCHAR NOT NULL,
    validation_notes VARCHAR NOT NULL,
    UNIQUE (
        bridge_version,
        bnetza_source_id,
        bnetza_state_name,
        bnetza_district_name
    )
);

-- name: insert_bridge_rows
INSERT INTO reference.bnetza_bbsr_district_bridge_2025 (
    bridge_version,
    source_audit_version,
    source_audit_sha256,
    bnetza_source_id,
    bnetza_reference_date,
    bnetza_state_name,
    bnetza_district_name,
    bnetza_admin_type,
    bbsr_reference_date,
    bbsr_source_version,
    bbsr_source_sha256,
    bbsr_administrative_district_code,
    bbsr_administrative_district_name,
    bbsr_federal_state_code,
    bbsr_federal_state_name,
    bbsr_kreisregion_code,
    bbsr_kreisregion_name,
    bbsr_settlement_type_code,
    bbsr_settlement_type_name_de,
    geographic_compatibility_status,
    evidence_method,
    evidence_source_reference,
    validation_notes
)
SELECT
    NULLIF(TRIM(bridge_version), ''),
    NULLIF(TRIM(source_audit_version), ''),
    NULLIF(TRIM(source_audit_sha256), ''),
    NULLIF(TRIM(bnetza_source_id), ''),
    TRY_CAST(NULLIF(TRIM(bnetza_reference_date), '') AS DATE),
    NULLIF(bnetza_state_name, ''),
    NULLIF(bnetza_district_name, ''),
    NULLIF(TRIM(bnetza_admin_type), ''),
    TRY_CAST(NULLIF(TRIM(bbsr_reference_date), '') AS DATE),
    NULLIF(bbsr_source_version, ''),
    NULLIF(TRIM(bbsr_source_sha256), ''),
    NULLIF(TRIM(bbsr_administrative_district_code), ''),
    NULLIF(bbsr_administrative_district_name, ''),
    NULLIF(TRIM(bbsr_federal_state_code), ''),
    NULLIF(bbsr_federal_state_name, ''),
    NULLIF(TRIM(bbsr_kreisregion_code), ''),
    NULLIF(bbsr_kreisregion_name, ''),
    NULLIF(TRIM(bbsr_settlement_type_code), ''),
    NULLIF(bbsr_settlement_type_name_de, ''),
    NULLIF(TRIM(geographic_compatibility_status), ''),
    NULLIF(TRIM(evidence_method), ''),
    NULLIF(evidence_source_reference, ''),
    NULLIF(validation_notes, '')
FROM read_csv(
    {{BRIDGE_CSV}},
    header = true,
    all_varchar = true,
    nullstr = ''
);

-- name: charging_by_bbsr_district_view
CREATE OR REPLACE VIEW analytics.charging_by_bbsr_district_2025 AS
WITH bridge AS (
    SELECT *
    FROM reference.bnetza_bbsr_district_bridge_2025
    WHERE bridge_version = '{{BRIDGE_VERSION}}'
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
equipment_by_district AS (
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
            ';' ORDER BY equipment_status
        ) AS equipment_statuses_present
    FROM source_equipment
    GROUP BY source_id, state_name, district_name
),
points_by_district AS (
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
district_metrics AS (
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
    FROM equipment_by_district e
    FULL OUTER JOIN points_by_district p
      ON e.source_id = p.source_id
     AND e.state_name = p.state_name
     AND e.district_name = p.district_name
)
SELECT
    b.bridge_version,
    b.bnetza_source_id,
    b.bnetza_reference_date AS infrastructure_reference_date,
    b.bnetza_state_name,
    b.bnetza_district_name,
    b.bnetza_admin_type,
    b.bbsr_reference_date,
    b.bbsr_source_version,
    b.bbsr_administrative_district_code,
    b.bbsr_administrative_district_name,
    b.bbsr_federal_state_code,
    b.bbsr_federal_state_name,
    b.bbsr_kreisregion_code,
    b.bbsr_kreisregion_name,
    b.bbsr_settlement_type_code,
    b.bbsr_settlement_type_name_de,
    b.geographic_compatibility_status,
    b.evidence_method,
    b.evidence_source_reference,
    b.validation_notes,
    COALESCE(m.equipment_count, 0) AS equipment_count,
    COALESCE(m.charging_point_count, 0) AS charging_point_count,
    COALESCE(m.declared_charging_point_count, 0)
        AS declared_charging_point_count,
    COALESCE(m.normal_charging_point_count, 0)
        AS normal_charging_point_count,
    COALESCE(m.fast_charging_point_count, 0)
        AS fast_charging_point_count,
    COALESCE(m.points_ge_150_kw, 0) AS points_ge_150_kw,
    COALESCE(m.points_ge_350_kw, 0) AS points_ge_350_kw,
    COALESCE(m.unclassifiable_power_point_count, 0)
        AS unclassifiable_power_point_count,
    ROUND(
        100.0 * COALESCE(m.fast_charging_point_count, 0)
        / NULLIF(COALESCE(m.charging_point_count, 0), 0),
        2
    ) AS fast_point_share_pct,
    ROUND(
        100.0 * COALESCE(m.points_ge_150_kw, 0)
        / NULLIF(COALESCE(m.charging_point_count, 0), 0),
        2
    ) AS high_power_point_share_pct,
    COALESCE(m.total_equipment_nominal_power_kw, 0.0)
        AS total_equipment_nominal_power_kw,
    COALESCE(m.total_equipment_nominal_power_kw, 0.0) / 1000.0
        AS total_equipment_nominal_power_mw,
    COALESCE(m.equipment_statuses_present, '') AS equipment_statuses_present
FROM bridge b
LEFT JOIN district_metrics m
  ON m.source_id = b.bnetza_source_id
 AND m.state_name = b.bnetza_state_name
 AND m.district_name = b.bnetza_district_name;

-- name: charging_by_bbsr_type_view
CREATE OR REPLACE VIEW analytics.charging_by_bbsr_type_2025 AS
WITH category_labels (settlement_type_code, settlement_type_name_de) AS (
    VALUES
        ('1', 'kreisfreie Großstadt'),
        ('2', 'städtischer Kreis'),
        ('3', 'ländlicher Kreis mit Verdichtungsansätzen'),
        ('4', 'dünn besiedelter ländlicher Kreis'),
        ('UNCLASSIFIED', 'UNCLASSIFIED')
),
district_categories AS (
    SELECT
        CASE
            WHEN bbsr_settlement_type_code IS NULL THEN 'UNCLASSIFIED'
            ELSE bbsr_settlement_type_code
        END AS settlement_type_code,
        CASE
            WHEN bbsr_settlement_type_code IS NULL THEN 'UNCLASSIFIED'
            ELSE bbsr_settlement_type_name_de
        END AS settlement_type_name_de,
        equipment_count,
        charging_point_count,
        normal_charging_point_count,
        fast_charging_point_count,
        points_ge_150_kw,
        points_ge_350_kw,
        unclassifiable_power_point_count,
        total_equipment_nominal_power_kw
    FROM analytics.charging_by_bbsr_district_2025
),
aggregated AS (
    SELECT
        settlement_type_code,
        settlement_type_name_de,
        COUNT(*) AS district_count,
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
    FROM district_categories
    GROUP BY settlement_type_code, settlement_type_name_de
),
national AS (
    SELECT SUM(charging_point_count) AS all_registered_charging_points
    FROM analytics.charging_by_bbsr_district_2025
)
SELECT
    labels.settlement_type_code,
    labels.settlement_type_name_de,
    COALESCE(a.district_count, 0) AS district_count,
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
    ) AS fast_point_share_pct,
    ROUND(
        100.0 * COALESCE(a.points_ge_150_kw, 0)
        / NULLIF(COALESCE(a.charging_point_count, 0), 0),
        2
    ) AS high_power_point_share_pct,
    COALESCE(a.total_equipment_nominal_power_kw, 0.0)
        AS total_equipment_nominal_power_kw,
    COALESCE(a.total_equipment_nominal_power_kw, 0.0) / 1000.0
        AS total_equipment_nominal_power_mw,
    ROUND(
        100.0 * COALESCE(a.charging_point_count, 0)
        / NULLIF(national.all_registered_charging_points, 0),
        6
    ) AS share_of_all_registered_charging_points_pct,
    CASE
        WHEN labels.settlement_type_code = 'UNCLASSIFIED'
            THEN 'UNCLASSIFIED_BNETZA_SOURCE_DISTRICTS'
        ELSE 'BBSR_CLASSIFIABLE_BNETZA_SOURCE_DISTRICTS'
    END AS classification_scope,
    'ALL_REGISTERED_CHARGING_POINTS_INCLUDING_UNCLASSIFIED'
        AS point_share_denominator_scope
FROM category_labels labels
LEFT JOIN aggregated a
  ON a.settlement_type_code = labels.settlement_type_code
CROSS JOIN national;
