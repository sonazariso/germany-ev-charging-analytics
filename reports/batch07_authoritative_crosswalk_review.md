# Batch 07 — Authoritative Geographic Crosswalk Review

## Scope and conclusion

This report reviews the 24 rows in `data/reference/bnetza_kba_district_crosswalk_2026.csv` that were marked provisional before Batch 07. The review used the exact CSV rows, the permanent DuckDB reference table, the current official Destatis administrative classification, the official KBA FZ 27.15 July 2026 workbook, and official Trier registration-authority material. No source workbook, Crosswalk CSV, DuckDB object, geographic view, KPI, or operational mapping was changed.

The review date is **2026-11-02**. The administrative reference is the Destatis GV-ISys quarterly classification effective **2026-09-30**. The KBA stock reference is FZ 27.15 effective **2026-07-01**. These dates are reference dates, not a claim that the two datasets are contemporaneous.

### Review result

| Review classification | Rows | Interpretation | Operational treatment |
|---|---:|---|---|
| Fully supported at the row/entity level | 22 | The BNetzA geography has a unique official Destatis district identity, and the KBA FZ 27.15 row has the same state, five-digit key, and an identifiable label variant. | Remain provisional until the owner approves a status change. |
| Partially supported | 2 | Trier city and Trier-Saarburg are separate administrative units but are represented by one KBA registration-region row, `07211 TRIER-SAARBURG`. | Remain provisional; preserve aggregate-before-join. |
| Unresolved at the row-identity level | 0 | No reviewed row lacked an identifiable official target. | No operational change. |

“Fully supported” above means independently supported as an entity-to-row mapping. It does **not** assert that KBA’s five-digit `Statistische Kennziffer` is universally identical to a Destatis AGS or ARS. Destatis defines AGS and ARS as separate administrative/statistical keys, while FZ 27 identifies its geography as `Zulassungsbezirke` and labels the field `Statistische Kennziffer`. The official sources do not provide a universal KBA-code-to-AGS/ARS crosswalk. Accordingly, all 24 CSV and DuckDB rows remain explicitly provisional after this documentation-only batch.

## Sources and evidence standard

The review used the following sources. The URLs are retained here so every matrix row can be traced to the same dated official evidence.

| ID | Source | Effective/publication date | What it establishes |
|---|---|---|---|
| D1 | [Destatis GV-ISys quarterly extract for 30 September 2026](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GVAuszugQ/AuszugGV3QAktuell.html) and [direct XLSX](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GVAuszugQ/AuszugGV3QAktuell.xlsx?__blob=publicationFile&v=22) | 2026-09-30, Q3 2026 | Current official administrative names, Kreis/city types, and AGS/ARS-related geography. |
| D2 | [Destatis GV100AD quarterly classification for 30 September 2026](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GV100ADQ/GV100AD3QAktuell.html) and [direct ZIP](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GV100ADQ/GV100AD3QAktuell.zip?__blob=publicationFile&v=17) | 2026-09-30, Q3 2026 | Administrative hierarchy and the five-digit Kreis component used within the official administrative key structure. |
| D3 | [Destatis Gemeindeverzeichnis overview and code definitions](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/_inhalt.html) | Current page accessed 2026-11-02 | Defines AGS as an eight-digit municipality key and ARS as a twelve-digit regional key; distinguishes these from other regional classifications. |
| K1 | [GovData metadata for KBA FZ 27 — 2026](https://www.govdata.de/suche/daten/fz-27-2026-bestand-an-kraftfahrzeugen-und-kraftfahrzeuganhangern-nach-ausgewahlten-merkmalen-bu) | Published 2026-03-30; metadata updated 2026-08-31 | Identifies KBA as the publishing authority, describes stock in the ZFZR, and states that alternative-drive passenger-car results are available by `Zulassungsbezirke`. |
| K2 | [KBA FZ 27.15 July 2026 workbook](https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/fz27_202607.xlsx?__blob=publicationFile&v=3) | 2026-07-01 stock reference | Provides the official `Statistische Kennziffer`, `Zulassungsbezirk`, district label, and July 2026 BEV/PHEV stock used by the local model. |
| T1 | [Official Landkreis Trier-Saarburg registration-office page](https://trier-saarburg.de/ihr-anliegen/zulassungsstelle/) | Current page accessed 2026-11-02 | States that the registration offices in Trier, Hermeskeil, and Saarburg handle registrations for both the city of Trier and Landkreis Trier-Saarburg. |
| T2 | [Public-law agreement between Trier and Trier-Saarburg](https://buergerinfo.trier-saarburg.de/getfile.php?id=78333&type=do) | Agreement dated 2022-11-29 | Defines the common registration office and its responsibility for the common registration district; it does not define the FZ 27 statistical aggregation rule. |
| T3 | [Energyatlas Rheinland-Pfalz method note](https://www.energieatlas.rlp.de/earp/daten/datenquellen-und-methodik/methodik-nachhaltige-pkw-antriebe) | Page accessed 2026-11-02; source retrieval noted as May 2025 | Independently corroborates that the KBA registration district Trier-Saarburg includes the city of Trier. This is supporting state-level documentation, not a KBA schema definition. |

The review treated a source as direct evidence only for what it actually publishes. A Destatis code/name match and a KBA code/name row support a row-level identity; they do not by themselves establish a general equivalence between KBA registration-region keys and all AGS or ARS values. Name similarity alone was not used as proof.

## 24-row evidence matrix

The CSV line number includes the header as line 1. “Yes, row-level” in the code column means that the same five-digit key and identifiable geography are present in D1/D2 and K2 for this row. It does not mean “KBA code system equals AGS/ARS in every KBA product.”

| CSV line | Original BNetzA state and district (type) | Mapped KBA code and name (CSV type) | Current method | Official evidence, date, and what it establishes | Code-system correspondence proven? | Verification recommendation | Remaining ambiguity |
|---:|---|---|---|---|---|---|---|
| 38 | Baden-Württemberg — Stadtkreis Freiburg im Breisgau (`city`) | `08311` — `FREIBURG I.BREISG.STADT` (`city`) | `explicit_provisional_alias` | [D1]/[D2] identify the official Freiburg district and `08311`; [K2] reports the same key with the abbreviated KBA city label. The difference is a display abbreviation and ordering, not a competing geography. Effective dates: Destatis 2026-09-30; KBA 2026-07-01. | Yes, row-level. | Fully supported alias; owner may consider promotion in a future approved crosswalk batch. | KBA does not publish a universal statement that this field is AGS/ARS; the conclusion is row-specific. |
| 118 | Bayern — Landkreis Neustadt a.d. Aisch-Bad Windsheim (`county`) | `09575` — `NEUSTADT/AISCH-WINDSHEIM` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify Landkreis Neustadt a.d. Aisch-Bad Windsheim and `09575`; [K2] reports `09575` with slash and abbreviation conventions. State, county type, and code are unique. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The KBA label is abbreviated and reordered; no KBA metadata states a universal AGS equivalence. |
| 140 | Bayern — Landkreis Wunsiedel i. Fichtelgebirge (`county`) | `09479` — `WUNSIEDEL I.FICHTELGEB.` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify the official county and `09479`; [K2] reports the same key with abbreviations for the county and Fichtelgebirge. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | Abbreviation expansion is clear, but the KBA code-system semantics are not documented as AGS/ARS. |
| 143 | Brandenburg — Kreisfreie Stadt Brandenburg an der Havel (`city`) | `12051` — `BRANDENBURG/HAVEL,STADT` (`city`) | `explicit_provisional_alias` | [D1]/[D2] identify Brandenburg an der Havel, city, `12051`; [K2] reports the same key with KBA slash and suffix notation. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | KBA display syntax differs; no universal KBA-to-AGS/ARS schema statement was found. |
| 177 | Hessen — Landkreis Kassel (`county`) | `06633` — `KASSEL, LAND` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify Landkreis Kassel as `06633`; [K2] reports `KASSEL, LAND`. The city/county collision is resolved by the official county type and distinct code from Kassel city. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The short KBA label omits the full administrative name; code-system semantics remain product-specific. |
| 194 | Mecklenburg-Vorpommern — Landkreis Mecklenburgische Seenplatte (`county`) | `13071` — `MECKLENBURGISCHE SEENPLA` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify the official county and `13071`; [K2] reports the same key with a truncated display label. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The KBA worksheet truncates the label; the official source does not document whether truncation is a field-width convention. |
| 202 | Niedersachsen — Kreisfreie Stadt Oldenburg (Oldb) (`city`) | `03403` — `OLDENBURG(OLDENB),STADT` (`city`) | `explicit_provisional_alias` | [D1]/[D2] identify Oldenburg city and `03403`; [K2] reports the same city key with the Oldb abbreviation. The separate Oldenburg county row uses a different key. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The KBA label uses a compressed city/county naming convention; no universal code-system crosswalk is published. |
| 230 | Niedersachsen — Landkreis Oldenburg (`county`) | `03458` — `OLDENBURG(OLDENBURG)` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify Landkreis Oldenburg and `03458`; [K2] reports the county key without the full `Landkreis` prefix. The city/county collision is resolved by key and type. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The KBA label is not a full legal name; no universal KBA-to-AGS/ARS documentation was found. |
| 234 | Niedersachsen — Landkreis Region Hannover (`county`) | `03241` — `HANNOVER` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify Region Hannover and `03241`; [K2] reports the same county key as `HANNOVER`. The administrative prefix is omitted in the KBA display label. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The KBA short label could be misleading without the official code; do not map by name alone. |
| 264 | Nordrhein-Westfalen — Kreis Rhein-Kreis Neuss (`county`) | `05162` — `NEUSS` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify Rhein-Kreis Neuss and `05162`; [K2] reports the same key as `NEUSS`. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | `NEUSS` is a short KBA label; the code is the decisive row-level evidence. |
| 266 | Nordrhein-Westfalen — Kreis Rheinisch-Bergischer Kreis (`county`) | `05378` — `RHEIN.-BERGISCHER KREIS` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify Rheinisch-Bergischer Kreis and `05378`; [K2] reports the same key with `RHEIN.-` abbreviation. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | Abbreviation expansion is supported by the official name, but KBA does not state a universal AGS/ARS relationship. |
| 270 | Nordrhein-Westfalen — Kreis Städteregion Aachen (`county`) | `05334` — `AACHEN, STAEDTEREGION` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify Städteregion Aachen and `05334`; [K2] reports the same key with the two name components reversed and transliterated. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The KBA ordering differs from the official name; administrative identity is code-supported, not name-only. |
| 291 | Nordrhein-Westfalen — Kreisfreie Stadt Mülheim an der Ruhr (`city`) | `05117` — `MUELHEIM A.D.RUHR,STADT` (`city`) | `explicit_provisional_alias` | [D1]/[D2] identify Mülheim an der Ruhr city and `05117`; [K2] reports the same key with abbreviation and transliteration. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The KBA label is abbreviated; no product-wide KBA-to-AGS/ARS rule is stated. |
| 300 | Rheinland-Pfalz — Kreisfreie Stadt Landau in der Pfalz (`city`) | `07313` — `LANDAU I.D.PFALZ,STADT` (`city`) | `explicit_provisional_alias` | [D1]/[D2] identify Landau in der Pfalz city and `07313`; [K2] reports the same key with the KBA abbreviation for `in der Pfalz`. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | Abbreviation expansion is clear; KBA key semantics remain limited to the FZ 27 product evidence. |
| 301 | Rheinland-Pfalz — Kreisfreie Stadt Ludwigshafen am Rhein (`city`) | `07314` — `LUDWIGSHAFEN A.RH.,STADT` (`city`) | `explicit_provisional_alias` | [D1]/[D2] identify Ludwigshafen am Rhein city and `07314`; [K2] reports the same key with the KBA abbreviation for `am Rhein`. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The KBA label is abbreviated; no universal KBA-to-AGS/ARS correspondence is documented. |
| 303 | Rheinland-Pfalz — Kreisfreie Stadt Neustadt an der Weinstraße (`city`) | `07316` — `NEUSTADT A.D.WSTR.,STADT` (`city`) | `explicit_provisional_alias` | [D1]/[D2] identify Neustadt an der Weinstraße city and `07316`; [K2] reports the same key with the KBA abbreviation. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The official name must be used to distinguish this city from other Neustadt units; KBA uses a compressed label. |
| 306 | Rheinland-Pfalz — Kreisfreie Stadt Trier (`city`) | `07211` — `TRIER-SAARBURG` (`county` in the CSV) | `shared_kba_registration_region` | [D1]/[D2] distinguish Trier city `07211` from Landkreis Trier-Saarburg `07235`. [K2] has one FZ 27.15 row, `07211 TRIER-SAARBURG`, not a separate `07235` row. [T1]/[T2] establish a common registration office and common registration district; [T3] corroborates the KBA combined-region interpretation. | **No AGS equivalence.** The KBA row-level aggregate is supported, but `07211` is not a proof that Trier-Saarburg has Destatis AGS `07211`. | Keep the shared-region mapping provisional and aggregate charging data to KBA `07211` before joining stock. Do not interpret the KBA stock as Trier-city-only. | The common authority does not by itself prove the exact FZ 27 aggregation rule. KBA FZ 27.15 and FZ 27.17 also use different display labels for the same code. |
| 310 | Rheinland-Pfalz — Landkreis Altenkirchen (Westerwald) (`county`) | `07132` — `ALTENKIRCHEN(WESTWLD.)` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify Landkreis Altenkirchen (Westerwald) and `07132`; [K2] reports the same key with an abbreviated Westerwald label and compressed punctuation. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The compressed label is clear from the code and official name, but KBA does not document a universal AGS/ARS relationship. |
| 330 | Rheinland-Pfalz — Landkreis Trier-Saarburg (`county`) | `07211` — `TRIER-SAARBURG` (`county`) | `shared_kba_registration_region` | [D1]/[D2] identify Trier-Saarburg separately as `07235`. [K2] reports the combined KBA row under `07211 TRIER-SAARBURG`; [T1]/[T2] establish the shared registration authority/district; [T3] corroborates the combined KBA interpretation. | **No AGS equivalence.** The KBA aggregate is supported, but the Destatis county key is `07235`. | Keep the shared-region mapping provisional and aggregate charging data to KBA `07211` before joining stock. Do not interpret the KBA stock as county-only. | FZ 27.15 has no separate `07235` stock row, and shared administration does not establish how KBA apportions the combined stock. |
| 335 | Saarland — Landkreis Regionalverband Saarbrücken (`county` in BNetzA) | `10041` — `SAARBRUECKEN,STADTVERB.` (`county` in the CSV) | `explicit_provisional_alias` | [D1]/[D2] identify Regionalverband Saarbrücken and `10041`; [K2] reports the same key with the historical/short `Stadtverband` display. The code and state disambiguate the region. | Yes, row-level, with an administrative-type caveat. | Fully supported row-level alias; keep operationally provisional pending owner approval. | Destatis describes the unit as a regional association and statistical tables may append `Landkreis`; KBA’s `Stadtverb.` wording is not a generic county label. |
| 337 | Saarland — Landkreis Saarpfalz-Kreis (`county`) | `10045` — `SAAR-PFALZ-KREIS` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify Saarpfalz-Kreis and `10045`; [K2] reports the same key with a hyphenated display label. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | Punctuation differs; no universal KBA-to-AGS/ARS schema statement was found. |
| 338 | Saarland — Landkreis St. Wendel (`county`) | `10046` — `SANKT WENDEL` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify the official county/key `10046` (Sankt Wendel); [K2] reports the same key with the expanded `SANKT` spelling. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | BNetzA abbreviation and KBA expansion are supported by the official name; the product-specific code semantics remain unstated. |
| 349 | Sachsen — Landkreis Sächsische Schweiz-Osterzgebirge (`county`) | `14628` — `SAECHS.SCHWEIZ-OSTERZGEB` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify the official county and `14628`; [K2] reports the same key with abbreviations for both name components. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | The KBA display is truncated/abbreviated; official code and state are required for safe use. |
| 394 | Thüringen — Landkreis Saale-Holzland-Kreis (`county`) | `16074` — `SAALE-HOLZLANDKREIS` (`county`) | `explicit_provisional_alias` | [D1]/[D2] identify Saale-Holzland-Kreis and `16074`; [K2] reports the same key with `Holzlandkreis` joined. | Yes, row-level. | Fully supported alias; keep operationally provisional pending owner approval. | Word joining is a KBA display convention; universal KBA-code semantics remain undocumented. |

## Trier special investigation

### Administrative boundaries and registration administration

Destatis treats the two areas as separate administrative units: Trier city is associated with the five-digit Kreis key `07211`, while Landkreis Trier-Saarburg is associated with `07235`. The current Destatis classification therefore must not be used to infer that the county is AGS `07211`.

The official Landkreis page states that the registration offices in Trier, Hermeskeil, and Saarburg handle registrations for both the city of Trier and Landkreis Trier-Saarburg under a public-law arrangement. The agreement dated 2022-11-29 names the organization the “Gemeinsame Kfz-Zulassungsstelle für die Stadt Trier und den Landkreis Trier-Saarburg” and assigns it responsibility for the “gemeinsamen Zulassungsbezirk.” This proves shared registration administration, not identical municipal/county boundaries and not, on its own, the exact aggregation used by every KBA worksheet.

### What KBA 2026 actually reports

In the local copy of the official KBA FZ 27.15 July 2026 workbook, the district-level row is:

| KBA worksheet | Statistical key | KBA label | Passenger cars | BEV | PHEV |
|---|---:|---|---:|---:|---:|
| FZ 27.15, 2026-07-01 | `07211` | `TRIER-SAARBURG` | 160,422 | **7,869** | 3,516 |

There is no separate FZ 27.15 row for `07235`. The 7,869 July 2026 BEVs are therefore the reported stock for the KBA row `07211 TRIER-SAARBURG`; they cannot be described as Trier-city-only or Trier-Saarburg-county-only stock.

The workbook also exposes a worksheet-level presentation inconsistency: in FZ 27.17, the filled-down registration-district label for the municipality rows is `07211 TRIER,STADT`, while FZ 27.15 uses `07211 TRIER-SAARBURG`. This is a contradiction in labels within the KBA product, not evidence that the district stock can be split. The FZ 27.15 district worksheet remains the correct source for the district-level July stock used by this project.

The Energyatlas Rheinland-Pfalz method note independently says that the KBA registration district Trier-Saarburg also includes the city of Trier. This supports the combined interpretation but is not a substitute for KBA documentation of the internal key definition.

### Analytical treatment retained

The existing method remains correct for the evidence available:

1. Retain the two BNetzA source geographies as separate rows.
2. Aggregate charging equipment and charging-point measures by KBA code.
3. Treat `07211` as one KBA registration-region row.
4. Join KBA stock once per code and reference date.
5. Do not sum the two source rows against the same KBA stock row.

No change to the Crosswalk CSV, permanent reference table, or geographic views is approved by this review.

## Contradictions and insufficient evidence

### Contradictions found

- **Administrative key versus KBA registration key:** Destatis separates Trier `07211` and Trier-Saarburg `07235`; KBA FZ 27.15 combines the region as `07211 TRIER-SAARBURG`.
- **KBA worksheet labels:** FZ 27.15 uses `07211 TRIER-SAARBURG`, while the municipality-grain FZ 27.17 presentation uses `07211 TRIER,STADT`. The label difference prevents using a KBA display name alone as a geographic definition.
- **Administrative type wording:** Regionalverband Saarbrücken is treated as a regional association in administrative material, while the local crosswalk and some Destatis statistical output use county-like wording and KBA uses `STADTVERB.`. The row is identifiable by official key and state, but the type labels are not interchangeable.

### Evidence that remains insufficient

- No KBA metadata located in the official FZ 27 2026 product description states that `Statistische Kennziffer` is the Destatis AGS, the ARS, or a fixed transformation of either.
- Shared registration-office authority is not proof that the underlying administrative boundaries are the same.
- The KBA FZ 27.15 row proves the combined reported stock but does not provide a city/county allocation for the 7,869 BEVs.
- The 22 alias mappings are well-supported at the row/entity level, but a universal code-system crosswalk should not be inferred from the repeated five-digit matches.

## Recommendations requiring owner approval

1. Keep all 24 operational rows provisional until the owner approves a status vocabulary that distinguishes “entity mapping independently supported” from “KBA code-system equivalence formally documented.”
2. If the owner promotes the 22 alias rows in a future batch, preserve the evidence distinction and do not promote either Trier row to a city-only or county-only mapping.
3. Preserve KBA `07211` as a combined registration-region grain unless KBA publishes a direct allocation or an approved source supplies one. Any alternative treatment requires a separate decision and validation.
4. If a future authoritative crosswalk is added, store its source/effective date and code system explicitly; do not overwrite AGS, ARS, and KBA registration keys in one field.
5. Do not modify the current CSV, DuckDB reference table, analytics views, or KPIs as part of this review.

## Validation and scope controls

The post-review validation recorded in the Batch 07 handoff is:

| Check | Result |
|---|---|
| Provisional rows reviewed | 24 |
| Crosswalk row count | 401; unchanged |
| Distinct KBA codes | 400; unchanged |
| Duplicate KBA code groups | Only `07211`, with the two Trier source rows; unchanged |
| Permanent reference rows | 401; unchanged |
| Permanent reference provisional rows | 24; unchanged |
| Core equipment / point / KBA district rows | 117,662 / 211,253 / 1,200; unchanged |
| KBA-code regional / combined view rows | 400 / 1,200; unchanged |
| July 2026 KBA `07211` BEVs | 7,869; interpreted as combined KBA registration-region stock |
| DuckDB access mode | `read_only=True` for inspection and validation |
| New data integration | None |
| Crosswalk CSV or DuckDB modification | None |
| Git remote or upload | None |

The final local checks include the independent read-only geographic validator, CSV/reference-record fingerprints before and after documentation changes, URL accessibility checks, `git diff --check`, and staged-file inspection. The documentation-only local commit is recorded in `PROJECT_STATUS.md` and the final handoff.

[D1]: https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GVAuszugQ/AuszugGV3QAktuell.html
[D2]: https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GV100ADQ/GV100AD3QAktuell.html
[K1]: https://www.govdata.de/suche/daten/fz-27-2026-bestand-an-kraftfahrzeugen-und-kraftfahrzeuganhangern-nach-ausgewahlten-merkmalen-bu
[K2]: https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/fz27_202607.xlsx?__blob=publicationFile&v=3
[T1]: https://trier-saarburg.de/ihr-anliegen/zulassungsstelle/
[T2]: https://buergerinfo.trier-saarburg.de/getfile.php?id=78333&type=do
[T3]: https://www.energieatlas.rlp.de/earp/daten/datenquellen-und-methodik/methodik-nachhaltige-pkw-antriebe
