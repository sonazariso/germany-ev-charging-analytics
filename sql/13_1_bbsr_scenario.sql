-- Batch 13.1: owner-approved 2026 BBSR-like analytical scenario.
--
-- This layer is deliberately separate from the official Batch 13 baseline.
-- It overlays exactly two owner-approved category assignments on the existing
-- source-grain charging view. It never changes the official BBSR reference,
-- the original bridge, the KBA Crosswalk, raw/core data, or KBA stock.

-- name: create_reference_schema
CREATE SCHEMA IF NOT EXISTS reference;

-- name: create_analytics_schema
CREATE SCHEMA IF NOT EXISTS analytics;

-- name: create_override_table
CREATE TABLE IF NOT EXISTS reference.bnetza_bbsr_owner_override_2026 (
    scenario_version VARCHAR NOT NULL,
    scenario_source_vintage VARCHAR NOT NULL,
    bnetza_source_id VARCHAR NOT NULL,
    bnetza_reference_date DATE NOT NULL,
    bnetza_state_name VARCHAR NOT NULL,
    bnetza_district_name VARCHAR NOT NULL,
    bnetza_admin_type VARCHAR NOT NULL,
    geographic_code_system VARCHAR NOT NULL,
    geographic_code VARCHAR NOT NULL,
    kba_reference_date DATE NOT NULL,
    analytical_category_code VARCHAR NOT NULL,
    analytical_category_name_de VARCHAR NOT NULL,
    classification_method VARCHAR NOT NULL,
    official_bbsr_verification BOOLEAN NOT NULL,
    official_bbsr_2025_type VARCHAR,
    boundary_vintage VARCHAR NOT NULL,
    boundary_compatibility_caveat VARCHAR NOT NULL,
    override_provenance VARCHAR NOT NULL,
    population_evidence_note VARCHAR NOT NULL,
    evidence_source_urls VARCHAR NOT NULL,
    source_audit_version VARCHAR NOT NULL,
    source_audit_sha256 VARCHAR NOT NULL,
    UNIQUE (
        scenario_version,
        bnetza_source_id,
        bnetza_state_name,
        bnetza_district_name
    )
);

-- name: insert_override_rows
INSERT INTO reference.bnetza_bbsr_owner_override_2026 (
    scenario_version,
    scenario_source_vintage,
    bnetza_source_id,
    bnetza_reference_date,
    bnetza_state_name,
    bnetza_district_name,
    bnetza_admin_type,
    geographic_code_system,
    geographic_code,
    kba_reference_date,
    analytical_category_code,
    analytical_category_name_de,
    classification_method,
    official_bbsr_verification,
    official_bbsr_2025_type,
    boundary_vintage,
    boundary_compatibility_caveat,
    override_provenance,
    population_evidence_note,
    evidence_source_urls,
    source_audit_version,
    source_audit_sha256
)
SELECT
    NULLIF(TRIM(scenario_version), ''),
    NULLIF(scenario_source_vintage, ''),
    NULLIF(TRIM(bnetza_source_id), ''),
    TRY_CAST(NULLIF(TRIM(bnetza_reference_date), '') AS DATE),
    NULLIF(bnetza_state_name, ''),
    NULLIF(bnetza_district_name, ''),
    NULLIF(TRIM(bnetza_admin_type), ''),
    NULLIF(TRIM(geographic_code_system), ''),
    NULLIF(TRIM(geographic_code), ''),
    TRY_CAST(NULLIF(TRIM(kba_reference_date), '') AS DATE),
    NULLIF(TRIM(analytical_category_code), ''),
    NULLIF(analytical_category_name_de, ''),
    NULLIF(TRIM(classification_method), ''),
    TRY_CAST(NULLIF(TRIM(official_bbsr_verification), '') AS BOOLEAN),
    NULLIF(TRIM(official_bbsr_2025_type), ''),
    NULLIF(TRIM(boundary_vintage), ''),
    NULLIF(boundary_compatibility_caveat, ''),
    NULLIF(override_provenance, ''),
    NULLIF(population_evidence_note, ''),
    NULLIF(evidence_source_urls, ''),
    NULLIF(TRIM(source_audit_version), ''),
    NULLIF(TRIM(source_audit_sha256), '')
FROM read_csv(
    {{OVERRIDE_CSV}},
    header = true,
    all_varchar = true,
    nullstr = ''
);

-- name: charging_by_bbsr_district_view
CREATE OR REPLACE VIEW analytics.charging_by_bbsr_district_2026_scenario AS
WITH overrides AS (
    SELECT *
    FROM reference.bnetza_bbsr_owner_override_2026
    WHERE scenario_version = '{{SCENARIO_VERSION}}'
      AND bnetza_source_id = '{{SOURCE_ID}}'
      AND bnetza_reference_date = DATE '{{BNETZA_DATE}}'
),
baseline AS (
    SELECT *
    FROM analytics.charging_by_bbsr_district_2025
)
SELECT
    '{{SCENARIO_VERSION}}' AS scenario_version,
    CASE
        WHEN o.geographic_code IS NOT NULL THEN o.scenario_source_vintage
        ELSE 'BNetzA infrastructure 2026-09-30; official BBSR geographic stand 2025-12-31'
    END AS scenario_source_vintage,
    b.bridge_version AS official_baseline_bridge_version,
    b.bnetza_source_id,
    b.infrastructure_reference_date,
    b.bnetza_state_name,
    b.bnetza_district_name,
    b.bnetza_admin_type,
    o.geographic_code_system,
    o.geographic_code,
    o.kba_reference_date,
    b.bbsr_reference_date AS official_bbsr_reference_date,
    b.bbsr_source_version AS official_bbsr_source_version,
    b.bbsr_administrative_district_code AS official_bbsr_administrative_district_code,
    b.bbsr_administrative_district_name AS official_bbsr_administrative_district_name,
    b.bbsr_federal_state_code AS official_bbsr_federal_state_code,
    b.bbsr_federal_state_name AS official_bbsr_federal_state_name,
    b.bbsr_kreisregion_code AS official_bbsr_kreisregion_code,
    b.bbsr_kreisregion_name AS official_bbsr_kreisregion_name,
    b.bbsr_settlement_type_code AS official_baseline_category_code,
    b.bbsr_settlement_type_name_de AS official_baseline_category_name_de,
    b.geographic_compatibility_status AS official_baseline_compatibility_status,
    COALESCE(o.official_bbsr_2025_type, b.bbsr_settlement_type_code)
        AS official_bbsr_2025_type,
    COALESCE(o.analytical_category_code, b.bbsr_settlement_type_code)
        AS scenario_category_code,
    COALESCE(o.analytical_category_name_de, b.bbsr_settlement_type_name_de)
        AS scenario_category_name_de,
    CASE
        WHEN o.geographic_code IS NOT NULL THEN o.classification_method
        ELSE 'OFFICIAL_BBSR_2025_BASELINE'
    END AS scenario_classification_method,
    CASE
        WHEN o.geographic_code IS NOT NULL THEN o.official_bbsr_verification
        ELSE b.geographic_compatibility_status = 'VERIFIED_COMPATIBLE'
    END AS scenario_official_bbsr_verification,
    CASE
        WHEN o.geographic_code IS NOT NULL THEN o.boundary_vintage
        ELSE '2025'
    END AS scenario_boundary_vintage,
    CASE
        WHEN o.geographic_code IS NOT NULL
            THEN o.boundary_compatibility_caveat
        ELSE 'Official Batch 13 BBSR 2025 baseline row; no owner override applied.'
    END AS scenario_boundary_compatibility_caveat,
    CASE
        WHEN o.geographic_code IS NOT NULL THEN o.override_provenance
        ELSE 'OFFICIAL_BBSR_2025_BASELINE_REFERENCE'
    END AS scenario_override_provenance,
    CASE
        WHEN o.geographic_code IS NOT NULL THEN o.population_evidence_note
        ELSE 'Not applicable to the official baseline row.'
    END AS scenario_population_evidence_note,
    CASE
        WHEN o.geographic_code IS NOT NULL THEN o.evidence_source_urls
        ELSE 'data/reference/bbsr_settlement_types_2025.csv; reports/batch13_bbsr_charging_deployment.md'
    END AS scenario_evidence_source_urls,
    b.evidence_method AS official_baseline_evidence_method,
    b.evidence_source_reference AS official_baseline_evidence_source_reference,
    b.validation_notes AS official_baseline_validation_notes,
    b.equipment_count,
    b.charging_point_count,
    b.declared_charging_point_count,
    b.normal_charging_point_count,
    b.fast_charging_point_count,
    b.points_ge_150_kw,
    b.points_ge_350_kw,
    b.unclassifiable_power_point_count,
    b.fast_point_share_pct,
    b.high_power_point_share_pct,
    b.total_equipment_nominal_power_kw AS declared_equipment_nominal_power_kw,
    b.total_equipment_nominal_power_mw AS declared_equipment_nominal_power_mw,
    b.equipment_statuses_present,
    o.source_audit_version AS override_source_audit_version,
    o.source_audit_sha256 AS override_source_audit_sha256
FROM baseline b
LEFT JOIN overrides o
  ON o.bnetza_source_id = b.bnetza_source_id
 AND o.bnetza_state_name = b.bnetza_state_name
 AND o.bnetza_district_name = b.bnetza_district_name;

-- name: charging_by_bbsr_type_view
CREATE OR REPLACE VIEW analytics.charging_by_bbsr_type_2026_scenario AS
WITH category_labels (scenario_category_code, scenario_category_name_de) AS (
    VALUES
        ('1', 'kreisfreie Großstadt'),
        ('2', 'städtischer Kreis'),
        ('3', 'ländlicher Kreis mit Verdichtungsansätzen'),
        ('4', 'dünn besiedelter ländlicher Kreis')
),
district_categories AS (
    SELECT
        scenario_category_code,
        scenario_category_name_de,
        scenario_classification_method,
        scenario_official_bbsr_verification,
        equipment_count,
        charging_point_count,
        normal_charging_point_count,
        fast_charging_point_count,
        points_ge_150_kw,
        points_ge_350_kw,
        unclassifiable_power_point_count,
        declared_equipment_nominal_power_kw
    FROM analytics.charging_by_bbsr_district_2026_scenario
),
aggregated AS (
    SELECT
        scenario_category_code,
        scenario_category_name_de,
        COUNT(*) AS district_count,
        COUNT(*) FILTER (
            WHERE scenario_classification_method IN (
                'OWNER_APPROVED_SCENARIO',
                'HISTORICAL_BBSR_CARRY_FORWARD'
            )
        ) AS owner_override_district_count,
        COUNT(*) FILTER (
            WHERE scenario_official_bbsr_verification = false
        ) AS not_officially_verified_district_count,
        SUM(equipment_count) AS equipment_count,
        SUM(charging_point_count) AS charging_point_count,
        SUM(normal_charging_point_count) AS normal_charging_point_count,
        SUM(fast_charging_point_count) AS fast_charging_point_count,
        SUM(points_ge_150_kw) AS points_ge_150_kw,
        SUM(points_ge_350_kw) AS points_ge_350_kw,
        SUM(unclassifiable_power_point_count)
            AS unclassifiable_power_point_count,
        SUM(declared_equipment_nominal_power_kw)
            AS declared_equipment_nominal_power_kw
    FROM district_categories
    WHERE scenario_category_code IN ('1', '2', '3', '4')
    GROUP BY scenario_category_code, scenario_category_name_de
),
national AS (
    SELECT
        SUM(charging_point_count) AS all_registered_charging_points,
        COUNT(*) FILTER (WHERE scenario_category_code IS NULL)
            AS unclassified_district_count
    FROM analytics.charging_by_bbsr_district_2026_scenario
)
SELECT
    '{{SCENARIO_VERSION}}' AS scenario_version,
    'BNetzA infrastructure 2026-09-30; official BBSR geographic stand 2025-12-31; owner boundary scenario 2026'
        AS scenario_source_vintage,
    labels.scenario_category_code,
    labels.scenario_category_name_de,
    COALESCE(a.district_count, 0) AS district_count,
    COALESCE(a.owner_override_district_count, 0)
        AS owner_override_district_count,
    COALESCE(a.not_officially_verified_district_count, 0)
        AS not_officially_verified_district_count,
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
    COALESCE(a.declared_equipment_nominal_power_kw, 0.0)
        AS declared_equipment_nominal_power_kw,
    COALESCE(a.declared_equipment_nominal_power_kw, 0.0) / 1000.0
        AS declared_equipment_nominal_power_mw,
    ROUND(
        100.0 * COALESCE(a.charging_point_count, 0)
        / NULLIF(national.all_registered_charging_points, 0),
        6
    ) AS national_charging_point_share_pct,
    national.unclassified_district_count,
    'OWNER_APPROVED_2026_ANALYTICAL_SCENARIO'
        AS classification_scope,
    'ALL_REGISTERED_CHARGING_POINTS_INCLUDING_ALL_SCENARIO_DISTRICTS'
        AS point_share_denominator_scope
FROM category_labels labels
LEFT JOIN aggregated a
  ON a.scenario_category_code = labels.scenario_category_code
CROSS JOIN national;
