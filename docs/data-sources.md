# Data sources

The source inventory is maintained in config/sources.json. The local inventory and workbook profiles are generated artifacts in data/profiles and are the evidence for the file sizes, hashes, worksheet counts, and row counts below.

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
- Review the applicable license terms for source-derived extracts and screenshots.
- Do not commit the original XLSX workbooks or the DuckDB database.
- Review whether any field-level source content, including identifiers or Public Keys, is appropriate for a public extract.
- Keep the code license separate from official-data licenses.

## BBSR feasibility reference — not integrated

Batch 09 investigated the official BBSR four-category settlement-structural district
typology for feasibility only. It is **not** in `config/sources.json`, was not
copied into the repository or DuckDB, and is not used in a current KPI.

| Field | Investigated value |
|---|---|
| Publisher | Bundesinstitut für Bau-, Stadt- und Raumforschung (BBSR) |
| Typology page | [Siedlungsstruktureller Kreistyp](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/deutschland/kreise/siedlungsstrukturelle-kreistypen/kreistypen.html) |
| Current reference download | [BBSR reference tables](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/downloads/download-referenzen.html) |
| Smallest suitable current artifact identified | `raumgliederungen-referenzen-2025.xlsx`, `Kreisreferenz` worksheet |
| Geographic reference date | 31.12.2025 |
| Workbook stand | 11.09.2026 |
| Relevant fields | `KRS2025`, `KRS_NAME`, Kreisregion code/name, compact BBSR type code/label (`AS`/`AT`) |
| Observed reference rows | 400 Kreis rows; 362 distinct Kreisregion keys |
| License | Datenlizenz Deutschland – Namensnennung – Version 2.0 |
| Recommended attribution | `Bundesinstitut für Bau-, Stadt- und Raumforschung: Laufende Raumbeobachtung des BBSR` |
| License text | [DL-DE/by-2.0](https://www.govdata.de/dl-de/by-2-0) |

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
