# Batch 10 — BBSR reference acquisition, build, and validation

Scope: acquire the latest suitable official BBSR reference, preserve its provenance, derive the four-category Kreis reference, and validate it. DuckDB, the existing Crosswalk, and analytical KPIs are out of scope.

## Executive summary

Batch 10 is PASS for an independent, versioned BBSR reference. The official 2025 workbook was acquired and hashed, its six worksheets and source headers were inspected, and 400 Kreis rows were extracted without assigning BBSR categories to KBA records. The raw workbook remains outside Git; the small derived reference, manifest, profile, script, and validation report are tracked.

## Source selection and provenance

- Publisher: Bundesinstitut für Bau-, Stadt- und Raumforschung
- Official reference page: https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/downloads/download-referenzen.html
- Selected workbook: https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/downloads/raumgliederungen-referenzen-2025.xlsx?__blob=publicationFile&v=3
- Observed current-page vintages: 2021, 2022, 2023, 2024, 2025
- Selected latest available suitable vintage: 2025
- Geographic reference date: 2025-12-31
- Workbook stand / publication date: 2026-09-11
- Download timestamp UTC: 2026-11-02T20:22:53Z
- HTTP status: 200
- HTTP Last-Modified: 2026-09-23T14:44:13Z
- Actual file size: 8,768,335 bytes
- Source SHA-256: 083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525
- License: Datenlizenz Deutschland – Namensnennung – Version 2.0
- License text: https://www.govdata.de/dl-de/by-2-0
- Required attribution: Bundesinstitut für Bau-, Stadt- und Raumforschung: Laufende Raumbeobachtung des BBSR

The page listed no 2026 workbook at the time of the check. The older nine-category 2012 dataset and complete INKAR database were not used.

The workbook's Nutzungshinweise names this license, and the linked license text permits copying, processing, transmission to third parties, and creation of new datasets when the provider, license, dataset URI, and a change notice are retained. This makes the small derived CSV suitable for Git tracking with the required attribution and change notice. It does not pre-approve a future BBSR/KBA enrichment or public KPI publication.

The official download page exposed the reference workbooks as the current structured resource. This 2025 workbook is the smallest suitable official resource inspected that contains both Kreis and Kreisregion identifiers and the compact four-category classification in one source; only its Kreisreferenz sheet is needed for the derived file. The descriptive typology page does not replace the identifiers, while the older 2012 resource and the complete INKAR database were not suitable substitutes.

## Workbook inspection

The workbook contains 6 worksheets. Every worksheet was inspected for its original header rows and row inventory. Only Kreisreferenz is used for the derived reference.

| Worksheet | Physical rows | Non-empty rows | Original columns |
|---|---:|---:|---:|
| Nutzungshinweise | 14 | 10 | 1 |
| Administrativ | 10,951 | 10,951 | 16 |
| Gemeindereferenz (inkl. Kreise) | 10,951 | 10,951 | 150 |
| Kreisreferenz | 402 | 402 | 76 |
| Metropolregionen | 450 | 450 | 4 |
| Grenzregionen | 410 | 410 | 4 |

### Selected source fields

| Output field | Original field | Original description |
|---|---|---|
| administrative_district_code | KRS2025 | Kreise (2025) Kennziffer |
| administrative_district_name | KRS_NAME | Kreise (2025) Name |
| federal_state_code | BLD2025 | Bundesländer (2025) Kennziffer |
| federal_state_name | BLD_NAME | Bundesländer (2025) Name |
| kreisregion_code | KKR2025 | Kreisregionen (2025) Kennziffer |
| kreisregion_name | KKR_NAME | Kreisregionen (2025) Name |
| settlement_type_code | KTU2025 | Siedlungsstruktureller Kreistyp (2025) Kennziffer |
| settlement_type_name_de | KTU_NAME | Siedlungsstruktureller Kreistyp (2025) Name |

KTU2025 and KTU_NAME were selected because their original description is Siedlungsstruktureller Kreistyp (2025). The differentiated five-category fields were not selected.

The complete original column inventory for all six worksheets is in data/reference/bbsr_source_manifest.json.

## Derived reference

- Output: data/reference/bbsr_settlement_types_2025.csv
- Rows: 400
- UTF-8 CSV SHA-256: e35c57da8d8f675fa132b629e6dda43180a18e5b78b95e1e72de30069a062e65
- Columns: source_version, bbsr_reference_date, source_sheet_name, source_excel_row, administrative_district_code, administrative_district_name, federal_state_code, federal_state_name, kreisregion_code, kreisregion_name, settlement_type_code, settlement_type_name_de
- Grain: one row per BBSR KRS2025 administrative Kreis row; Kreisregion relationships remain at the original component-row grain.
- No KBA code, AGS/ARS conversion, allocation, or KPI value is added.

## Validation results

| Check | Observed result |
|---|---:|
| Source Kreisreferenz rows read | 400 |
| Derived rows emitted | 400 |
| Source rows not emitted | 0 |
| Distinct administrative district codes | 400 |
| Distinct federal-state codes | 16 |
| Federal-state code/name inconsistencies | 0 |
| Distinct Kreisregion codes | 362 |
| Duplicate primary-grain keys | 0 |
| Classification codes selected | 1, 2, 3, 4 |
| Classification code/label inconsistencies | 0 |
| Kreisregion name inconsistencies | 0 |
| Kreisregion mixed-type groups | 0 |
| Multi-district Kreisregion groups preserved | 36 |

### Compact four-category counts

| Code | German label | Rows |
|---:|---|---:|
| 1 | kreisfreie Großstadt | 68 |
| 2 | städtischer Kreis | 131 |
| 3 | ländlicher Kreis mit Verdichtungsansätzen | 98 |
| 4 | dünn besiedelter ländlicher Kreis | 103 |

The generator fails if required fields/categories are missing, source rows cannot be represented, source codes lose their expected string shape, or code/label and geographic relationships are inconsistent.
The observed 400 Kreis rows, 362 Kreisregion keys, and compact type counts match the Batch 09 feasibility findings. The Batch 10 change is the preserved source/provenance and reproducible derived reference, not a new geographic vintage or a changed classification grain.

## Compatibility review

### Hanau and Main-Kinzig-Kreis

The 2025 workbook contains 0 Hanau row(s) and 1 Main-Kinzig-Kreis row(s). This confirms that the selected vintage predates the January 2026 Hanau administrative separation for this reference. No classification is copied to the current Hanau KBA row.

### Trier and Trier-Saarburg

| Administrative row | BBSR code | BBSR type code | BBSR type label |
|---|---|---:|---|
| Trier, kreisfreie Stadt | 07211000 | 1 | kreisfreie Großstadt |
| Trier-Saarburg | 07235000 | 3 | ländlicher Kreis mit Verdichtungsansätzen |

The two administrative rows remain separate. Shared KBA registration region 07211 stock is not allocated and no single BBSR category is assigned to it.

### Other special cases

| Area | BBSR row(s) | Type result |
|---|---:|---|
| Berlin | 1 | 1 |
| Hamburg | 1 | 1 |
| Bremen | 1 | 1 |
| Bremerhaven | 1 | 1 |

Small independent cities grouped into Kreisregionen remain as multiple administrative rows where provided. The generator preserves those relationships and does not collapse them. No mixed compact classification was observed within a Kreisregion in this workbook.

## Integration boundary and next strategy

The 2025 BBSR reference cannot be treated as a direct 2026 KBA lookup. The selected vintage has no Hanau row, and Trier plus Trier-Saarburg have different BBSR rows and types while the KBA layer combines stock under 07211. The next approved step would be a separate compatibility study that documents any KRS-to-KBA relationship, tests boundary cases, and gets owner approval before any production join or KPI use. No Trier stock allocation or KBA classification is proposed by this batch.

Remaining owner decisions: approve the future compatibility methodology and vintage-alignment rule; approve treatment of Hanau, Kreisregion groups, and Trier if integration is pursued; and separately review any public BBSR/KBA-derived output or KPI publication.

## Reproduction

Run: python3 scripts/10_build_bbsr_reference.py

The raw workbook is excluded from Git under data/raw/. The derived CSV, source manifest, profile, and validation report are versioned. No DuckDB object, Crosswalk row, KPI, or shared Trier stock value changed.
