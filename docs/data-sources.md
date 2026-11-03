# Data sources

The source inventory is maintained in config/sources.json. It contains four primary BNetzA/KBA sources and one separately handled BBSR reference source. The local inventory and workbook profiles are generated artifacts in data/profiles and are the evidence for the file sizes, hashes, worksheet counts, and row counts below.

## BNetzA Ladesäulenregister

| Field | Observed value |
|---|---|
| Publisher | Bundesnetzagentur |
| Dataset | Ladesäulenregister / Liste der Ladesäulen |
| Official source page | [BNetzA E-Mobilität](https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/start.htm) |
| Direct URL in manifest | [Ladesaeulenregister_BNetzA_2026-09-30.xlsx](https://data.bundesnetzagentur.de/Bundesnetzagentur/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/Ladesaeulenregister_BNetzA_2026-09-30.xlsx) |
| Local filename | data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx |
| Format and reference date | XLSX; 2026-09-30 |
| File size | 31,722,320 bytes, approximately 30.25 MiB |
| SHA-256 | 1e82c1734b17e17e51092a0f9460a5e204888569fb12aa5940b30e9cdb726342 |
| Worksheets | 1: Ladesäulenregister |
| Profiled rows | 117,673 physical worksheet rows; 117,670 populated rows |
| Width | 47 populated columns through AU |
| Analytical record count | 117,662 equipment rows after excluding the title and metadata region |
| Geographic coverage | All 16 German federal states; BNetzA state/district labels |
| Granularity | One equipment row may represent multiple charging-point slots |
| Major fields | Equipment ID, operator, status, equipment type, declared point count, equipment nominal power, commissioning date, address, district, state, coordinates, point groups, connector text, EVSE ID, and Public Key |

The published register itself warns that the list contains operators who completed the applicable notification process at the update date and that the number of publicly accessible charging facilities in Germany is therefore higher than the list shown. The register is consequently a published-register measure, not an exhaustive census.

The ingestion keeps the source row in raw.bnetza_rows, creates one normalized row per equipment record in core.charging_equipment, and creates one normalized row per populated point slot in core.charging_point. A point slot is not a connector count. Connector types and semicolon-separated power values remain text within the point row.

The manifest declares CC BY 4.0 for this source and requires attribution to bundesnetzagentur.de. The attribution and license should be rechecked before any external publication or redistribution of source-derived extracts.

## KBA FZ 27

All three KBA workbooks are the same product family and preserve all 20 worksheets locally. FZ 27 contains aggregate stock, not vehicle-level records.

| Reference date | Local filename | Size | SHA-256 | Worksheets | Populated rows |
|---|---|---:|---|---:|---:|
| 2026-01-01 | data/raw/kba/fz27_202601.xlsx | 1,474,738 bytes | 29ab2eaa178a1c6a3463d5cad707fee1e762241304ae6bb08c29702d6e6aea31 | 20 | 20,588 |
| 2026-04-01 | data/raw/kba/fz27_202604.xlsx | 1,482,694 bytes | 28fffaa7d2f21ede6d7f6988a717b749b759a308755c472df4d391c73a0653e7 | 20 | 20,597 |
| 2026-07-01 | data/raw/kba/fz27_202607.xlsx | 1,478,376 bytes | d6a26702fa6f8358cc5f0e15e88c04ac6c36527be404058674138dd9571bc803 | 20 | 20,612 |

The direct URLs are recorded in the manifest:

- [FZ 27 January 2026](https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/fz27_202601.xlsx?__blob=publicationFile&v=3)
- [FZ 27 April 2026](https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/fz27_202604.xlsx?__blob=publicationFile&v=3)
- [FZ 27 July 2026](https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/fz27_202607.xlsx?__blob=publicationFile&v=3)

The manifest points to the [GovData dataset page](https://www.govdata.de/suche/daten/fz-27-2026-bestand-an-kraftfahrzeugen-und-kraftfahrzeuganhangern-nach-ausgewahlten-merkmalen-bu) as the official source page. The declared license is Datenlizenz Deutschland – Namensnennung 2.0, with attribution to the Kraftfahrt-Bundesamt.

## KBA worksheet roles used by the model

- FZ 27.2: state-level fuel-category values, including Elektro (BEV), Hybrid insgesamt, darunter Plug-in, and passenger-car counts.
- FZ 27.9: national quarterly history used by the current analytics.kba_national_quarterly_stock view.
- FZ 27.15: district-level passenger-car totals, BEV, and PHEV values; 400 district codes per reference date.
- FZ 27.16: postcode-level commercial/private passenger-car, BEV, and PHEV values.
- FZ 27.17: municipality-level commercial/private passenger-car, BEV, and PHEV values.

The remaining worksheets, including title, imprint, contents, alternate vehicle categories, and footnotes, are retained in raw.kba_rows even when they are not currently normalized into a core table.

## Geography and granularity

BNetzA supplies state and district names as part of each equipment record. KBA FZ 27.15 supplies KBA district codes and names. The current crosswalk retains 401 BNetzA state/district combinations and maps them to 400 distinct KBA codes. Trier city and Trier-Saarburg intentionally share code 07211 at the KBA registration-region level.

State-level KBA data contain 18 labels per date in the current normalization: the 16 states plus Germany and an additional Sonstige category. The district model contains 400 codes per date and is the appropriate grain for the crosswalk-based regional join.

## Reproduction and verification

The standard-library download and profiling sequence is:

~~~bash
python3 scripts/01_download.py
python3 scripts/02_profile_xlsx.py
~~~

If an official site blocks scripted retrieval, download the original workbook from its source page into the exact manifest path and run:

~~~bash
python3 scripts/01_download.py --verify-only
python3 scripts/02_profile_xlsx.py
~~~

The download script validates the XLSX container and writes the hash inventory. The profiling script streams every physical row and does not rewrite the source.

## Licensing and publication considerations

The source licenses and required attributions are metadata in the local manifest, not a blanket permission to publish every source-derived export. Before GitHub or Tableau publication:

- Preserve the required BNetzA and KBA attribution.
- Preserve the BBSR attribution and identify the tracked CSV as a changed/derived reference under Datenlizenz Deutschland – Namensnennung – Version 2.0.
- Review the applicable license terms for source-derived extracts and screenshots.
- Do not commit the original XLSX workbooks or the DuckDB database.
- Review whether any field-level source content, including identifiers or Public Keys, is appropriate for a public extract.
- Keep the code license separate from official-data licenses.

## BBSR reference acquisition and provenance

Batch 09 identified the official BBSR four-category settlement-structural district
typology. Batch 10 acquired the latest suitable official workbook, preserved it
locally under data/raw/bbsr/ (ignored by Git), and built a versioned derived
reference. Batch 13 uses that reference in a separate BNetzA-source-grain,
charging-only KPI path; it is not assigned to KBA registration regions.

| Field | Investigated value |
|---|---|
| Publisher | Bundesinstitut für Bau-, Stadt- und Raumforschung (BBSR) |
| Typology page | [Siedlungsstruktureller Kreistyp](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/deutschland/kreise/siedlungsstrukturelle-kreistypen/kreistypen.html) |
| Current reference download | [BBSR reference tables](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/downloads/download-referenzen.html) |
| Smallest suitable current artifact identified | `raumgliederungen-referenzen-2025.xlsx`, `Kreisreferenz` worksheet |
| Geographic reference date | 31.12.2025 |
| Workbook stand | 11.09.2026 |
| Local filename | data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx (ignored by Git) |
| File size | 8,768,335 bytes |
| SHA-256 | 083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525 |
| Download timestamp | 2026-11-02T20:22:53Z |
| Relevant fields | `KRS2025`, `KRS_NAME`, federal state (`BLD2025`/`BLD_NAME`), `KKR2025`, `KKR_NAME`, compact BBSR type code/label (`KTU2025`/`KTU_NAME`) |
| Observed reference rows | 400 Kreis rows; 362 distinct Kreisregion keys |
| License | Datenlizenz Deutschland – Namensnennung – Version 2.0 |
| Recommended attribution | Bundesinstitut für Bau-, Stadt- und Raumforschung: Laufende Raumbeobachtung des BBSR |
| License text | [DL-DE/by-2.0](https://www.govdata.de/dl-de/by-2-0) |

The selected workbook contains six worksheets: Nutzungshinweise, Administrativ,
Gemeindereferenz (inkl. Kreise), Kreisreferenz, Metropolregionen, and
Grenzregionen. The relevant Kreisreferenz sheet has 76 original columns. The
derived file is data/reference/bbsr_settlement_types_2025.csv with one row per
KRS2025 administrative Kreis row and these stable fields:

- source_version
- bbsr_reference_date
- source_sheet_name
- source_excel_row
- administrative_district_code / administrative_district_name

## Batch 13 source-grain bridge

The Batch 13 bridge at
`data/reference/bnetza_bbsr_bridge_2025.csv` is generated only from the local
BNetzA source identities, the Batch 12 Path A evidence, and the BBSR 2025
reference. Its metadata sidecar is
`data/reference/bnetza_bbsr_bridge_2025_manifest.json`.

The BNetzA infrastructure source is the preserved
`Ladesaeulenregister_BNetzA_2026-09-30.xlsx` snapshot. The bridge has 401 source
rows: 399 verified-compatible, one conditional-vintage Main-Kinzig-Kreis row,
and one unresolved Hanau row. It does not use a KBA code as geographic proof,
does not change `bnetza_kba_district_crosswalk_2026`, and does not use KBA stock.

For exact deployment provenance and checksums, see
[`reports/batch13_bbsr_charging_deployment.md`](../reports/batch13_bbsr_charging_deployment.md).
- federal_state_code / federal_state_name
- kreisregion_code / kreisregion_name
- settlement_type_code / settlement_type_name_de

The complete original sheet/column inventory, source checksum, derived checksum,
download timestamp, response metadata, and validation results are in
data/reference/bbsr_source_manifest.json. The reproducible generator is
scripts/10_build_bbsr_reference.py and its evidence is in
reports/batch10_bbsr_reference_validation.md.

The current reference workbook is preferred over the historical GovData entry that
describes a nine-category 2012 dataset. The full [INKAR](https://www.inkar.de/Default)
database was not downloaded; the current online edition is described as edition
07/2025 on the uniform geographic stand 31.12.2023 and is not required for the
four-category reference lookup.

BBSR keys and KBA registration codes remain separate. Any future use requires a
dated code-based compatibility bridge, an explicit boundary-vintage check, and
preservation of the existing BNetzA-to-KBA crosswalk. The owner-approved Trier
label is **Trier / Trier-Saarburg (gemeinsamer Zulassungsbezirk)**; shared KBA stock
must not be allocated without a separately approved method.

## Batch 13.1 owner-scenario evidence

The owner-approved scenario records the following external evidence URLs with
the two-row override reference:

- [Hanau in Zahlen](https://www.hanau.de/wirtschaft/profil-und-standortvorteile/hanau-in-zahlen/)
- [Hessen press statement: Stadt Hanau erhält 20 Millionen Euro](https://innen.hessen.de/presse/stadt-hanau-erhaelt-20-millionen-euro)
- [Hessen municipalities and counties](https://innen.hessen.de/kommunales/kommunen/gemeinden-und-landkreise)

The Hessen statement describes Hanau's separation from Main-Kinzig-Kreis with
effect from 1 January 2026 and gives the contrasting context of approximately
98,000 residents versus about 107,000 reported by the municipal register. The
scenario stores that difference as provenance context only; it is not a BBSR
classification rule. Hanau category 1 is an owner-approved analytical
assumption, not an official BBSR 2025 or 2026 classification. Main-Kinzig type
2 is carried forward from the BBSR 2025 row with an explicit 2026
boundary-vintage caveat.

## Batch 15 KBA FZ 27 analytical inventory

Batch 15 uses the three locally preserved KBA FZ 27 releases already listed in
the project manifest:

| Reference date | Local source | Worksheets | Scope used in Batch 15 |
|---|---|---:|---|
| 2026-01-01 | `data/raw/kba/fz27_202601.xlsx` | 20 | National/state, ownership, history, 400 KBA registration regions, postcode and municipality checks |
| 2026-04-01 | `data/raw/kba/fz27_202604.xlsx` | 20 | National/state, ownership, history, 400 KBA registration regions, postcode and municipality checks |
| 2026-07-01 | `data/raw/kba/fz27_202607.xlsx` | 20 | National/state, ownership, history, 400 KBA registration regions, postcode and municipality checks |

The complete release-by-release worksheet inventory is in
[`reports/batch15_kba_worksheet_capabilities.csv`](../reports/batch15_kba_worksheet_capabilities.csv).
The primary analytical roles are:

- FZ 27.2: federal-state fuel/vehicle stock, including BEV and nested PHEV.
- FZ 27.5: commercial/private holder groups at federal-state, `Sonstige` and national grain.
- FZ 27.9: national quarterly stock history; overlapping releases are deduplicated by stock date.
- FZ 27.15: 400 KBA registration-region rows per snapshot with passenger-car, BEV and PHEV counts.
- FZ 27.16: postcode-level commercial/private BEV/PHEV detail without district/state identifiers.
- FZ 27.17: municipality detail nested under KBA districts, without a municipality code and with missing numeric cells after source-dot parsing.

Batch 15 verified SHA-256 fingerprints for all three KBA workbooks before
analysis. It used only existing local sources, did not download another
dataset, and did not modify any source workbook or Crosswalk.
