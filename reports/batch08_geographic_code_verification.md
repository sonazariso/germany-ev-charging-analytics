# Batch 08 — Geographic Code and Boundary Verification

## Scope and outcome

Batch 08 independently checked the relationship between the BNetzA district names, KBA registration districts, Destatis administrative keys, and the 2026 administrative boundary changes requested by the project owner. The review date is **2026-11-02**. The expected starting commit was `1b0aafbe32fcbf1a031dd1ac5b2c5b24d1991517`; the repository was clean at that commit before work began.

This was a documentation and validation batch. It used the existing local source workbooks and DuckDB database in read-only mode. It did not download or integrate a new dataset, modify the Crosswalk CSV, change DuckDB objects, alter source rows, change KPI formulas, or allocate vehicle stock between administrative units.

**Batch 08 result: PASS — documentation-only geographic verification completed.**

### Executive findings

| Question | Finding |
|---|---|
| 22 identity-supported aliases | All 22 have direct row-level code evidence: the KBA five-digit key matches the dated Destatis five-digit Kreis component, and state, administrative type, and entity identity agree. This does not prove a universal KBA-code = AGS/ARS rule. |
| Aliases supported only by entity-level evidence | 0 of 22. The two separate Trier source rows are a different case: both are supported only as one combined KBA registration region, not as two code-equivalent administrative mappings. |
| Unresolved or conflicting alias identities | 0. The universal code-system relationship remains unresolved. |
| Hanau | BNetzA, Destatis, and all three local FZ 27.15 snapshots represent Hanau and Main-Kinzig-Kreis separately. No current 2026 coverage mismatch was found. |
| Trier | Destatis separates Trier city (`07211`) and Trier-Saarburg (`07235`); KBA FZ 27.15 reports one combined `07211 TRIER-SAARBURG` registration row. July 2026 BEV stock `7,869` is counted once. |
| 400-region model | Defensible as a KBA registration-region model for the current snapshots, not as proof of 400 administrative boundary equivalences. The 401-to-400 relationship is caused by the shared Trier registration region. |
| Operational status | All 24 existing provisional statuses remain unchanged pending owner approval. |

## Scope, terminology, and evidence rules

The local evidence set was:

- `data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx`, represented in DuckDB as source `bnetza_charging_2026_09_30`;
- `data/raw/kba/fz27_202601.xlsx`, `data/raw/kba/fz27_202604.xlsx`, and `data/raw/kba/fz27_202607.xlsx`, with the district rows taken from worksheet **FZ 27.15**;
- `data/reference/bnetza_kba_district_crosswalk_2026.csv`;
- the deployed `reference.bnetza_kba_district_crosswalk_2026`, `analytics.charging_by_kba_district_2026_09_30`, and `analytics.kba_district_charging_vs_bev_2026` objects.

The terminology is intentionally conservative:

- Destatis defines the **AGS** as an eight-digit municipality key and the **ARS** as a twelve-digit hierarchical regional key. The first five positions identify the state and Kreis-level component.
- FZ 27.15 labels its KBA geography with **Statistische Kennziffer** and **Zulassungsbezirk**. The KBA five-digit field is therefore retained as a KBA registration-district key, even where its digits match the five-digit Destatis Kreis component.
- “Direct code-level evidence” in this report means a row-specific match of the five-digit KBA key to the dated Destatis Kreis component, together with a state and entity/type match. It does **not** mean that KBA has documented a universal AGS or ARS correspondence.
- “Entity-level evidence” means that the administrative entity and KBA reporting region are supported, but the KBA row cannot be treated as the same administrative unit. This is the Trier treatment.

### Official source register

| ID | Official source | Reference date or access date | Use in this review |
|---|---|---|---|
| D1 | [Destatis GV-ISys quarterly extract](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GVAuszugQ/AuszugGV3QAktuell.html) and [direct quarterly workbook](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GVAuszugQ/AuszugGV3QAktuell.xlsx?__blob=publicationFile&v=22) | 2026-09-30 | Official names and administrative unit types. |
| D2 | [Destatis GV100AD quarterly classification](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GV100ADQ/GV100AD3QAktuell.html) and [direct classification archive](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GV100ADQ/GV100AD3QAktuell.zip?__blob=publicationFile&v=17) | 2026-09-30 | Administrative hierarchy and Kreis-level key components. |
| D3 | [Destatis Gemeindeverzeichnis overview and code definitions](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/_inhalt.html) | Accessed 2026-11-02 | AGS/ARS definitions and distinction from other regional classifications. |
| H1 | [Hessian Ministry: Gemeinden und Landkreise](https://innen.hessen.de/kommunales/kommunen/gemeinden-und-landkreise) | Current page accessed 2026-11-02 | Hanau became a kreisfreie Stadt on 2026-01-01 and was removed from Main-Kinzig-Kreis. |
| H2 | [Hessian Statistical Office: January 2026 administrative key directory](https://statistik.hessen.de/sites/statistik.hessen.de/files/2026-01/verz-2_26-01.pdf) | January 2026 | Hanau `06 415 000` / `06 415 0000 000` and Main-Kinzig-Kreis `06 435 000` / `06 435 0000 000`; the boundary change is recorded as effective 2026-01-01. |
| K1 | [GovData metadata for KBA FZ 27 — 2026](https://www.govdata.de/suche/daten/fz-27-2026-bestand-an-kraftfahrzeugen-und-kraftfahrzeuganhangern-nach-ausgewahlten-merkmalen-bu) | Published 2026-03-30; metadata updated 2026-08-31 | FZ 27 stock scope, quarterly dates, alternative-drive coverage, and Zulassungsbezirk grain. |
| K2 | [KBA FZ 27 July 2026 workbook](https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/fz27_202607.xlsx?__blob=publicationFile&v=3) | 2026-07-01 | Official FZ 27.15 district rows and alternative-drive stock. The January and April local workbooks are the corresponding primary evidence for those dates. |
| T1 | [Landkreis Trier-Saarburg registration office](https://trier-saarburg.de/ihr-anliegen/zulassungsstelle/) | Current page accessed 2026-11-02 | Shared registration administration for Trier and Trier-Saarburg. |
| T3 | [Energieatlas Rheinland-Pfalz method note](https://www.energieatlas.rlp.de/earp/daten/datenquellen-und-methodik/methodik-nachhaltige-pkw-antriebe) | Page accessed 2026-11-02; data retrieval noted as June 2026 | States that the Trier-Saarburg registration district also includes the kreisfreie Stadt Trier. |

The Destatis landing page returned HTTP 403 to the web reader during this run; the official dated direct-file links and the existing Batch 07 row-level review were retained, and no new file was downloaded. The public-law agreement URL recorded in Batch 07 was not re-fetched because it returned 404 in the current web access; the Trier conclusion below does not rely on that URL as sole evidence.

## Evidence matrix — all 22 identity-supported aliases

All rows below use D1/D2 (`2026-09-30`) and K2 (`2026-07-01`) as the dated administrative and KBA evidence. The local KBA workbook is the primary observation of the actual label and code. For kreisfreie Städte, a full city-level AGS/ARS is shown. For counties and the Regionalverband, only the five-digit Kreis or association component is shown; no full municipality AGS/ARS is substituted for the county.

| # | Original BNetzA state and district | Current KBA code and label | Destatis code evidence | Classification and strength |
|---:|---|---|---|---|
| 1 | Baden-Württemberg — Stadtkreis Freiburg im Breisgau (`city`) | `08311` — `FREIBURG I.BREISG.STADT` | Same five-digit Kreis component; city AGS `08311000`, ARS `083110000000`. | **Direct code-level, strong.** Abbreviation and suffix are display variants; KBA remains a registration-district key. |
| 2 | Bayern — Landkreis Neustadt a.d. Aisch-Bad Windsheim (`county`) | `09575` — `NEUSTADT/AISCH-WINDSHEIM` | Same five-digit Kreis component `09575`; no full county AGS/ARS asserted. | **Direct code-level, strong.** Slash and abbreviation are label variants; code and state disambiguate the entity. |
| 3 | Bayern — Landkreis Wunsiedel i. Fichtelgebirge (`county`) | `09479` — `WUNSIEDEL I.FICHTELGEB.` | Same five-digit Kreis component `09479`; no full county AGS/ARS asserted. | **Direct code-level, strong.** Abbreviated name is identifiable only with the code and state. |
| 4 | Brandenburg — Kreisfreie Stadt Brandenburg an der Havel (`city`) | `12051` — `BRANDENBURG/HAVEL,STADT` | Same five-digit Kreis component; city AGS `12051000`, ARS `120510000000`. | **Direct code-level, strong.** Slash form and city suffix are display variants. |
| 5 | Hessen — Landkreis Kassel (`county`) | `06633` — `KASSEL, LAND` | Same five-digit Kreis component `06633`; no full county AGS/ARS asserted. | **Direct code-level, strong.** The city/county collision is resolved by official type and key, not name alone. |
| 6 | Mecklenburg-Vorpommern — Landkreis Mecklenburgische Seenplatte (`county`) | `13071` — `MECKLENBURGISCHE SEENPLA` | Same five-digit Kreis component `13071`; no full county AGS/ARS asserted. | **Direct code-level, strong.** The KBA display is truncated; the code is decisive. |
| 7 | Niedersachsen — Kreisfreie Stadt Oldenburg (Oldb) (`city`) | `03403` — `OLDENBURG(OLDENB),STADT` | Same five-digit Kreis component; city AGS `03403000`, ARS `034030000000`. | **Direct code-level, strong.** The separate Oldenburg county has a different key. |
| 8 | Niedersachsen — Landkreis Oldenburg (`county`) | `03458` — `OLDENBURG(OLDENBURG)` | Same five-digit Kreis component `03458`; no full county AGS/ARS asserted. | **Direct code-level, strong.** City/county collision is resolved by key and type. |
| 9 | Niedersachsen — Landkreis Region Hannover (`county`) | `03241` — `HANNOVER` | Same five-digit Kreis component `03241`; no full county AGS/ARS asserted. | **Direct code-level, strong.** KBA omits the administrative prefix; name-only matching would be unsafe. |
| 10 | Nordrhein-Westfalen — Kreis Rhein-Kreis Neuss (`county`) | `05162` — `NEUSS` | Same five-digit Kreis component `05162`; no full county AGS/ARS asserted. | **Direct code-level, strong.** Short KBA label is supported by the key and state. |
| 11 | Nordrhein-Westfalen — Kreis Rheinisch-Bergischer Kreis (`county`) | `05378` — `RHEIN.-BERGISCHER KREIS` | Same five-digit Kreis component `05378`; no full county AGS/ARS asserted. | **Direct code-level, strong.** Abbreviation expands unambiguously with the official key. |
| 12 | Nordrhein-Westfalen — Kreis Städteregion Aachen (`county`) | `05334` — `AACHEN, STAEDTEREGION` | Same five-digit Kreis component `05334`; no full county AGS/ARS asserted. | **Direct code-level, strong.** KBA reverses the name order and transliterates the label. |
| 13 | Nordrhein-Westfalen — Kreisfreie Stadt Mülheim an der Ruhr (`city`) | `05117` — `MUELHEIM A.D.RUHR,STADT` | Same five-digit Kreis component; city AGS `05117000`, ARS `051170000000`. | **Direct code-level, strong.** Abbreviation and transliteration are display variants. |
| 14 | Rheinland-Pfalz — Kreisfreie Stadt Landau in der Pfalz (`city`) | `07313` — `LANDAU I.D.PFALZ,STADT` | Same five-digit Kreis component; city AGS `07313000`, ARS `073130000000`. | **Direct code-level, strong.** KBA abbreviation is identifiable from the official name and key. |
| 15 | Rheinland-Pfalz — Kreisfreie Stadt Ludwigshafen am Rhein (`city`) | `07314` — `LUDWIGSHAFEN A.RH.,STADT` | Same five-digit Kreis component; city AGS `07314000`, ARS `073140000000`. | **Direct code-level, strong.** KBA abbreviation is identifiable from the official name and key. |
| 16 | Rheinland-Pfalz — Kreisfreie Stadt Neustadt an der Weinstraße (`city`) | `07316` — `NEUSTADT A.D.WSTR.,STADT` | Same five-digit Kreis component; city AGS `07316000`, ARS `073160000000`. | **Direct code-level, strong.** The full official name is needed to distinguish this city from other Neustadt units. |
| 17 | Rheinland-Pfalz — Landkreis Altenkirchen (Westerwald) (`county`) | `07132` — `ALTENKIRCHEN(WESTWLD.)` | Same five-digit Kreis component `07132`; no full county AGS/ARS asserted. | **Direct code-level, strong.** Compressed punctuation and abbreviation are label variants. |
| 18 | Saarland — Landkreis Regionalverband Saarbrücken (`county` in BNetzA) | `10041` — `SAARBRUECKEN,STADTVERB.` | Same five-digit association/Kreis component `10041`; no full county AGS/ARS asserted. | **Direct code-level, moderate.** Entity and key agree, but Regionalverband and `Stadtverb.` are not interchangeable generic county types. |
| 19 | Saarland — Landkreis Saarpfalz-Kreis (`county`) | `10045` — `SAAR-PFALZ-KREIS` | Same five-digit Kreis component `10045`; no full county AGS/ARS asserted. | **Direct code-level, strong.** Hyphenation is a display variant. |
| 20 | Saarland — Landkreis St. Wendel (`county`) | `10046` — `SANKT WENDEL` | Same five-digit Kreis component `10046`; no full county AGS/ARS asserted. | **Direct code-level, strong.** `St.` and `Sankt` are identifiable spelling variants. |
| 21 | Sachsen — Landkreis Sächsische Schweiz-Osterzgebirge (`county`) | `14628` — `SAECHS.SCHWEIZ-OSTERZGEB` | Same five-digit Kreis component `14628`; no full county AGS/ARS asserted. | **Direct code-level, strong.** KBA abbreviates both major name components. |
| 22 | Thüringen — Landkreis Saale-Holzland-Kreis (`county`) | `16074` — `SAALE-HOLZLANDKREIS` | Same five-digit Kreis component `16074`; no full county AGS/ARS asserted. | **Direct code-level, strong.** Joined wording is a KBA display variant. |

### Matrix conclusion

The 22 aliases are safe to retain as explicit operational rows for the current local snapshot because each has a unique state/type/key/entity match. They are **not** safe to relabel as universally AGS- or ARS-verified without a KBA metadata statement or an authoritative product-specific crosswalk. The operational `verification_status` for all 22 therefore remains `provisional_alias_requires_authoritative_review`.

## Special investigation — Hanau and Main-Kinzig-Kreis

### Administrative boundary and candidate identifiers

The Hessian Ministry states that Hanau was removed from Main-Kinzig-Kreis and became a kreisfreie Stadt with effect from **2026-01-01**. The Hessian January 2026 key directory lists:

| Administrative unit | Official January 2026 key-directory entry | KBA FZ 27.15 key in the local workbooks |
|---|---|---|
| Hanau, Brüder-Grimm-Stadt | `06 415 000` (AGS-style administrative key row); `06 415 0000 000` (ARS) | `06415 HANAU,STADT` |
| Main-Kinzig-Kreis | `06 435 000`; `06 435 0000 000` | `06435 MAIN-KINZIG-KREIS` |

The matching five-digit prefixes are direct row-level evidence for these two units in the dated records. They are not evidence that every KBA product uses the same administrative boundary or that the KBA field is itself an AGS or ARS.

### BNetzA September 30, 2026

The local BNetzA source contains two distinct district names and the Crosswalk maps them one-to-one:

| BNetzA district name | Equipment rows | Point slots | Current KBA target | Crosswalk status |
|---|---:|---:|---|---|
| Kreisfreie Stadt Hanau | 146 | 251 | `06415 HANAU,STADT` | `observed_local_snapshot_match` |
| Landkreis Main-Kinzig-Kreis | 439 | 740 | `06435 MAIN-KINZIG-KREIS` | `observed_local_snapshot_match` |

BNetzA contributes names rather than AGS/ARS fields in the current core schema. The separate names confirm source-grain separation after the boundary change; they do not independently prove an official geometry-level crosswalk.

### KBA FZ 27.15 snapshots

The local FZ 27.15 workbook rows are separate in all three snapshots. The row positions are stable in the local files: Hanau is row 183, Main-Kinzig-Kreis row 188, and Trier row 327.

| KBA stock date | Hanau `06415` (passenger cars / BEV / PHEV) | Main-Kinzig-Kreis `06435` (passenger cars / BEV / PHEV) | Combined BEVs, arithmetic only |
|---|---:|---:|---:|
| 2026-01-01 | 53,997 / 2,022 / 1,159 | 215,580 / 7,483 / 4,342 | 9,505 |
| 2026-04-01 | 53,944 / 2,215 / 1,199 | 215,609 / 8,034 / 4,551 | 10,249 |
| 2026-07-01 | 53,920 / 2,394 / 1,247 | 215,982 / 8,774 / 4,781 | 11,168 |

The answer to whether the 2026 administrative separation is reflected in the KBA stock publication used by this project is **yes for FZ 27.15**. The observation is product-specific: it should not be generalized to other KBA products without checking their own geography and date.

### Hanau conclusions

1. **KBA separation:** reflected in all three local FZ 27.15 snapshots.
2. **BNetzA boundary vintage:** the 2026-09-30 source uses separate Hanau and Main-Kinzig-Kreis names, consistent with the effective 2026 administrative structure. Exact spatial boundary equivalence is not available from the BNetzA name-only fields.
3. **Crosswalk coverage:** no mismatch. Both source rows have unique, non-provisional local state/type/name matches to distinct KBA keys; neither is the intentional duplicate target `07211`.
4. **Comparability:** region-level charging and BEV comparisons are geographically comparable within the current FZ 27.15 KBA-registration-region model, with the BNetzA/KBA date difference retained. They must not be labelled as same-date administrative statistics.
5. **Historical series:** the current database contains only 2026 FZ 27.15 snapshots, so no within-project pre-2026 discontinuity can be measured. A historical series that previously placed Hanau inside Main-Kinzig-Kreis would shift the MKK value by the Hanau row's stock, but the effect on older series is **unknown** without those historical product-specific snapshots. A boundary-vintage note is required before such a series is presented.

No vehicle counts were reallocated. The combined BEV figures above are shown only as a transparent sum of two separately reported KBA rows.

## Special investigation — Trier

### Administrative versus registration geography

Destatis distinguishes **kreisfreie Stadt Trier** (five-digit Kreis component `07211`; city AGS/ARS are separate municipality-level keys) from **Landkreis Trier-Saarburg** (five-digit Kreis component `07235`). The local Crosswalk intentionally maps both BNetzA names to KBA registration key `07211`.

The current official Trier-Saarburg registration-office page and the Rheinland-Pfalz Energyatlas method note support a shared registration region: the Trier-Saarburg registration district also includes the city of Trier. This supports the combined KBA interpretation but does not turn `07211` into the county's Destatis code and does not provide a city/county allocation of stock.

### Local stock and charging evidence

| KBA stock date | Local FZ 27.15 row | Passenger cars | BEVs | PHEVs |
|---|---|---:|---:|---:|
| 2026-01-01 | `07211 TRIER-SAARBURG` | 159,729 | 6,799 | 3,239 |
| 2026-04-01 | `07211 TRIER-SAARBURG` | 159,978 | 7,250 | 3,380 |
| 2026-07-01 | `07211 TRIER-SAARBURG` | 160,422 | **7,869** | 3,516 |

The BNetzA snapshot has two source rows:

| BNetzA district | Equipment rows | Point slots | Nominal power |
|---|---:|---:|---:|
| Kreisfreie Stadt Trier | 113 | 201 | 11,040.4 kW |
| Landkreis Trier-Saarburg | 163 | 302 | 13,782.0 kW |
| Aggregate to KBA `07211` | 276 | **503** | 24,822.4 kW |

The deployed regional view has one row for KBA code `07211`, with `source_geography_rows = 2` and `provisional_mapping_rows = 2`. The combined view has three rows for `07211`, one for each KBA stock date, not six rows. July 2026 stock `7,869` is therefore joined once. A raw source-row join would incorrectly repeat that stock; the prohibited duplicate would be 7,869 BEVs, or 0.3331% of the 2,362,218-code July district total.

### Trier recommendation

The mapping is **supported by combined KBA stock evidence and entity-level registration evidence**, but it is not officially proven as an AGS/ARS equivalence. Dashboards should label the geography as **“Trier/Trier-Saarburg KBA registration region (07211)”** or equivalent. They should not call the 7,869 BEVs Trier-city-only, Trier-Saarburg-county-only, or allocate them between the two source rows.

The current aggregate-before-join strategy is correct and should remain unchanged.

## Structural consistency and independent geographic checks

Structural checks establish retention and join arithmetic. Independent geographic checks establish only the dated row/entity evidence described above; they do not promote operational statuses.

| Check | Observed result | Status |
|---|---:|---|
| BNetzA state/district combinations | 401 | PASS |
| Crosswalk rows | 401 | PASS |
| Distinct mapped KBA codes | 400 | PASS |
| Explicit provisional statuses | 24 = 22 aliases + 2 Trier rows | PASS; unchanged |
| Equipment records | 117,662 | PASS |
| Charging-point slots | 211,253 | PASS |
| KBA district charging rows | 400 | PASS |
| Combined KBA code/date rows | 1,200 = 400 × 3 | PASS |
| July 2026 district BEV stock | 2,362,218 | PASS |
| July `07211` stock multiplicity | 1 row for the code/date; 7,869 BEVs once | PASS |
| DuckDB access mode | `read_only=True` | PASS |

The existing independent validator completed with:

```text
[PASS] Batch 06 independent read-only validation
```

No unexpected code inconsistency was found. The 401-to-400 reduction remains the documented Trier duplicate target, not a Hanau coverage issue.

## Final methodological recommendation

- Retain all 22 aliases operationally for the current snapshot, with explicit state/type constraints and the existing evidence notes. Do not promote their status automatically.
- Count **22 aliases with direct row-level code evidence**, **0 aliases supported only at entity level**, **0 unresolved aliases**, and **0 conflicting aliases**. Separately classify the two Trier rows as entity-level combined-region evidence.
- Keep all 24 operational statuses provisional until the owner approves a status change and the project retains the distinction between KBA registration keys and Destatis AGS/ARS.
- Preserve the Trier aggregate-before-join rule and use a combined-region dashboard label.
- Treat Hanau as two ordinary separate 2026 KBA-registration regions in the current model. Add a boundary-vintage note when historical periods or other KBA products are introduced; no special allocation is required for the current three FZ 27.15 dates.
- Retain the 400-region model as defensible for KBA-registration-region analysis of the current snapshots. Do not describe it as an authoritative 400-region administrative model.
- No current KPI formula or verified numerical metric changes are required. Current measurable impact is zero; the prohibited Trier duplication would have added 7,869 July BEVs, but it is not present in the deployed view.

### Evidence required to close remaining gaps

1. A KBA product-specific code list or metadata statement that explicitly defines `Statistische Kennziffer`, its effective date, and its relationship—or non-relationship—to AGS and ARS.
2. Historical KBA product snapshots and boundary notes covering the Hanau transition, if pre-2026 comparisons are required.
3. A KBA or owner-approved authoritative allocation source for Trier city versus Trier-Saarburg, if a split KPI is ever required.
4. A versioned administrative-to-KBA crosswalk for the relevant product/date, rather than a universal rule inferred from repeated five-digit matches.
5. Owner approval before any operational `verification_status` is promoted.

## Validation, fingerprints, and scope controls

- `.venv/bin/python scripts/06_validate_geographic_layer.py` — PASS.
- Read-only DuckDB evidence queries — PASS for all counts and Hanau/Trier checks above.
- Crosswalk SHA-256 before/after documentation work: `fdf139c5057250184358e3014267a4a4c4259749113273f6bd48206f6a64fe6a` — unchanged.
- DuckDB SHA-256 before/after documentation work: `19753969b21a581fba79cd4fcff8d46cf7afa3354c27cb0bfce33db0f6ad4d43` — unchanged.
- Source workbook hashes were inspected before work and no source file was modified.
- `git diff --check` and staged-file review were required before the local commit.
- No raw workbook, DuckDB file, backup, secret, private Persian document, or ignored machine-local file was staged.
- No Git remote was added; nothing was pushed or published.

## Owner decisions required

- Approve or defer promotion of the 22 row-level-supported aliases; retain explicit KBA-versus-AGS/ARS terminology either way.
- Approve the final dashboard label and display treatment for the combined Trier registration region.
- Approve whether historical KBA vintages should be added before any pre-2026 or cross-product trend is shown.
- Approve any future evidence source that would allocate Trier stock or define a product-specific KBA-to-administrative crosswalk.

## Local evidence fingerprints

The local source workbook paths and current hashes used during this review were:

| File | SHA-256 |
|---|---|
| `data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx` | `1e82c1734b17e17e51092a0f9460a5e204888569fb12aa5940b30e9cdb726342` |
| `data/raw/kba/fz27_202601.xlsx` | `29ab2eaa178a1c6a3463d5cad707fee1e762241304ae6bb08c29702d6e6aea31` |
| `data/raw/kba/fz27_202604.xlsx` | `28fffaa7d2f21ede6d7f6988a717b749b759a308755c472df4d391c73a0653e7` |
| `data/raw/kba/fz27_202607.xlsx` | `d6a26702fa6f8358cc5f0e15e88c04ac6c36527be404058674138dd9571bc803` |
