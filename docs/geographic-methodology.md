# Geographic methodology

## Purpose and scope

The geographic layer aligns BNetzA charging records with KBA district stock without changing the source geography. It is a local-snapshot crosswalk, not an official boundary gazetteer. The current version is crosswalk_version 2026-07-01: it uses the BNetzA 2026-09-30 geography and the KBA 2026-07-01 district snapshot.

## Observed geography

- BNetzA contains 401 distinct state/district combinations in the current charging snapshot.
- KBA FZ 27.15 contains 400 distinct five-digit district codes for each of the three dates.
- The crosswalk CSV retains all 401 BNetzA combinations and maps them to 400 distinct KBA codes.
- The only intentionally duplicated KBA code is 07211, shared by Kreisfreie Stadt Trier and Landkreis Trier-Saarburg.
- Berlin and Hamburg use state/city naming conventions in the KBA file rather than ordinary city-suffix labels.

Coverage validation is not geographic correctness. The fact that all 401 source combinations have a local KBA target proves row coverage in this snapshot; it does not prove official boundary equivalence.

## Matching method

The generator in scripts/04_build_geographic_crosswalk.py applies the following sequence:

1. Read BNetzA state and district labels from core.charging_equipment and aggregate source metrics by the exact state/district pair.
2. Read the 400 KBA district rows for 2026-07-01 from core.kba_district_ev_stock.
3. Classify BNetzA labels as city, county, or unknown from their administrative prefix.
4. Classify KBA labels as city for Berlin, Hamburg, or a label ending in Stadt; otherwise treat them as county for this local matching rule.
5. Normalize case, German diacritics, punctuation, spacing, and common transliteration without using normalized names alone to resolve ambiguous geography.
6. Apply explicit full-state/full-district rules for documented aliases and special cases.
7. Accept an ordinary mapping only when state, administrative type, and normalized name produce one unique KBA candidate.
8. Record mapping method, verification status, note, evidence URL, and source aggregates in the output.
9. Fail the validation report if rows are unmapped, multiply assigned, missing from the KBA code set, or inconsistent with the expected source counts.

The result is deterministic for the observed source snapshot. Determinism is a reproducibility property, not official verification.

## Mapping status and verification

| Mapping method | Rows | Verification status |
|---|---:|---|
| state_and_admin_type_name_match | 375 | observed_local_snapshot_match |
| explicit_provisional_alias | 22 | provisional_alias_requires_authoritative_review |
| explicit_state_city_naming_convention | 2 | observed_local_snapshot_naming_convention |
| shared_kba_registration_region | 2 | provisional_shared_region_requires_authoritative_review |

The 375 ordinary matches were checked against the local July KBA snapshot. The 22 aliases and two Trier rows remain provisional. No row is labelled officially verified.

## Provisional aliases

These rules are explicit candidates for the local KBA release. They are not proof that the source boundaries are officially equivalent.

| BNetzA state | BNetzA district | KBA code | KBA label observed | Reason for review |
|---|---|---:|---|---|
| Baden-Württemberg | Stadtkreis Freiburg im Breisgau | 08311 | FREIBURG I.BREISG.STADT | Abbreviation and city label |
| Bayern | Landkreis Neustadt a.d. Aisch-Bad Windsheim | 09575 | NEUSTADT/AISCH-WINDSHEIM | Slash and abbreviation |
| Bayern | Landkreis Wunsiedel i. Fichtelgebirge | 09479 | WUNSIEDEL I.FICHTELGEB. | Multiple abbreviations |
| Brandenburg | Kreisfreie Stadt Brandenburg an der Havel | 12051 | BRANDENBURG/HAVEL,STADT | Slash-form city label |
| Hessen | Landkreis Kassel | 06633 | KASSEL, LAND | City/county name collision |
| Mecklenburg-Vorpommern | Landkreis Mecklenburgische Seenplatte | 13071 | MECKLENBURGISCHE SEENPLA | Truncated KBA display label |
| Niedersachsen | Kreisfreie Stadt Oldenburg (Oldb) | 03403 | OLDENBURG(OLDENB),STADT | City/county name collision |
| Niedersachsen | Landkreis Oldenburg | 03458 | OLDENBURG(OLDENBURG) | City/county name collision |
| Niedersachsen | Landkreis Region Hannover | 03241 | HANNOVER | Administrative prefix omitted by KBA |
| Nordrhein-Westfalen | Kreis Rhein-Kreis Neuss | 05162 | NEUSS | Short KBA label |
| Nordrhein-Westfalen | Kreis Rheinisch-Bergischer Kreis | 05378 | RHEIN.-BERGISCHER KREIS | Abbreviation |
| Nordrhein-Westfalen | Kreis Städteregion Aachen | 05334 | AACHEN, STAEDTEREGION | Reordered KBA label |
| Nordrhein-Westfalen | Kreisfreie Stadt Mülheim an der Ruhr | 05117 | MUELHEIM A.D.RUHR,STADT | Abbreviation |
| Rheinland-Pfalz | Kreisfreie Stadt Landau in der Pfalz | 07313 | LANDAU I.D.PFALZ,STADT | Abbreviation |
| Rheinland-Pfalz | Kreisfreie Stadt Ludwigshafen am Rhein | 07314 | LUDWIGSHAFEN A.RH.,STADT | Abbreviation |
| Rheinland-Pfalz | Kreisfreie Stadt Neustadt an der Weinstraße | 07316 | NEUSTADT A.D.WSTR.,STADT | Abbreviation |
| Rheinland-Pfalz | Landkreis Altenkirchen (Westerwald) | 07132 | ALTENKIRCHEN(WESTWLD.) | Abbreviation and spacing |
| Saarland | Landkreis Regionalverband Saarbrücken | 10041 | SAARBRUECKEN,STADTVERB. | Administrative-type wording differs |
| Saarland | Landkreis Saarpfalz-Kreis | 10045 | SAAR-PFALZ-KREIS | Hyphenated KBA label |
| Saarland | Landkreis St. Wendel | 10046 | SANKT WENDEL | Expanded abbreviation |
| Sachsen | Landkreis Sächsische Schweiz-Osterzgebirge | 14628 | SAECHS.SCHWEIZ-OSTERZGEB | Multiple abbreviations |
| Thüringen | Landkreis Saale-Holzland-Kreis | 16074 | SAALE-HOLZLANDKREIS | Joined KBA wording |

The target state, local administrative type, and KBA display label were checked for each candidate against the local July workbook. An authoritative administrative source or independent review is still required.

## City/county collisions and special conventions

### Berlin and Hamburg

The crosswalk explicitly maps Kreisfreie Stadt Berlin to KBA code 11000 and Kreisfreie Stadt Hamburg to KBA code 02000. The KBA labels are simply BERLIN and HAMBURG. These are explicit state/city naming conventions, not normalized-name matches.

### Trier and Trier-Saarburg

KBA FZ 27.15 reports Trier city and Trier-Saarburg together under registration-region code 07211. Both original BNetzA rows are retained:

| BNetzA district | KBA code | Consequence |
|---|---:|---|
| Kreisfreie Stadt Trier | 07211 | Keep as a source geography row |
| Landkreis Trier-Saarburg | 07211 | Keep as a source geography row |

The correct downstream order is:

~~~text
BNetzA equipment and point rows
  -> aggregate by BNetzA state/district
  -> map to KBA code
  -> aggregate again by KBA code
  -> join one KBA stock row per code and reference date
~~~

Joining the raw 401-row crosswalk directly to KBA stock would duplicate the 07211 vehicle stock. The Batch 03 validation measured 2,362,218 BEVs after aggregate-before-join and 2,370,087 in the intentionally demonstrated raw 401-row join.

## Crosswalk output

The curated file is data/reference/bnetza_kba_district_crosswalk_2026.csv. Its columns are:

- crosswalk_version
- bnetza_reference_date and kba_reference_date
- bnetza_state_name, bnetza_district_name, and bnetza_admin_type
- kba_state_name, kba_district_code, kba_district_name, and kba_admin_type
- mapping_status, mapping_method, and verification_status
- mapping_note and evidence_url
- equipment_rows, declared_point_count, charging_point_slots, and equipment_nominal_power_kw

The current validation report records 401 rows, 401 mapped rows, 400 distinct codes, no unmapped combinations, no multiply assigned BNetzA combinations, and only code 07211 assigned twice.

## Validation strategy

Before any geographic DuckDB integration is approved, repeat these checks:

1. Recount source state/district combinations and KBA codes by reference date.
2. Assert one crosswalk row per BNetzA state/district combination.
3. Assert one KBA stock row per code and date.
4. Check state and administrative-type consistency for every row.
5. List every alias, provisional status, missing evidence URL, and duplicate target code.
6. Reconcile equipment, declared points, point slots, and nominal power before and after mapping.
7. Aggregate by KBA code before the KBA join and reconcile vehicle totals to the source KBA district table.
8. Review the Trier treatment and every provisional alias with an authoritative administrative reference.

## Relationship to future BBSR settlement types

BBSR settlement or spatial typologies would be an enrichment dimension, not a replacement for administrative districts or KBA registration regions. A future integration must validate boundary vintages, choose an explicit point-to-area method, preserve the administrative crosswalk, and avoid implying that a settlement type is a KBA registration district. BBSR is not currently downloaded or integrated.
