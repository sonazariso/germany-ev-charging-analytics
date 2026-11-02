# Geographic methodology

## Purpose and scope

The geographic layer aligns BNetzA charging records with KBA district stock without changing the source geography. It is a local-snapshot crosswalk, not an official boundary gazetteer. The current version is crosswalk_version 2026-07-01: it uses the BNetzA 2026-09-30 geography and the KBA 2026-07-01 district release for label matching. The KBA stock layer also contains 2026-01-01 and 2026-04-01; those dates remain separate observations in the combined model.

## Observed geography

- BNetzA contains 401 distinct state/district combinations in the current charging snapshot.
- KBA FZ 27.15 contains 400 distinct five-digit district codes for each of the three dates.
- The crosswalk CSV retains all 401 BNetzA combinations and maps them to 400 distinct KBA codes.
- The only intentionally duplicated KBA code is 07211, shared by Kreisfreie Stadt Trier and Landkreis Trier-Saarburg.
- Berlin and Hamburg use state/city naming conventions in the KBA file rather than ordinary city-suffix labels.

Coverage validation is not geographic correctness. The fact that all 401 source combinations have a local KBA target proves row coverage in this snapshot; it does not prove official boundary equivalence.

## Batch 05 pre-integration validation and Batch 06 deployment

The geographic model was validated with one DuckDB connection opened using `read_only=True`. The validation recomputed charging measures from `core.charging_equipment` and `core.charging_point`; it did not use the Crosswalk CSV's pre-aggregated measures as the analytical source.

- The source-aware equipment-to-point join used both `source_id` and Excel row. All 117,662 equipment rows and all 211,253 point rows were retained.
- Point power was parsed from every semicolon-separated token in `connector_power_raw`, with decimal commas normalized to decimal points. The maximum valid token within each point was used for classification; connector powers were never summed.
- The result contained 400 KBA district-code rows. Equipment nominal power was aggregated from equipment rows separately from point measures and totalled 9,215.4173 MW.
- The regional power bands reconciled to 156,155 points at or below 22 kW, 55,098 above 22 kW, 40,950 at or above 150 kW, and 6,950 at or above 350 kW. No point lacked a valid parsed maximum in this snapshot.
- The 401 source combinations mapped to 400 distinct KBA codes. All 24 provisional mappings remained explicitly flagged: 22 aliases and two Trier shared-region rows.
- Joining the 400 aggregated regional rows to the three KBA snapshots produced 1,200 code/date rows. July district BEV stock remained 2,362,218, and the shared Trier code was joined once per date rather than once per source row.

The permanent-object proposal and acceptance checks are in [the geographic layer design](geographic-layer-design.md). Batch 06 implemented that approved design in the local DuckDB file as `reference.bnetza_kba_district_crosswalk_2026`, `analytics.charging_by_kba_district_2026_09_30`, and `analytics.kba_district_charging_vs_bev_2026`. The executable definitions are maintained in [sql/06_geographic_layer.sql](../sql/06_geographic_layer.sql).

Before modification, the deployment checked the 117,662 equipment rows, 211,253 point rows, 1,200 KBA rows, 401 source-geography keys, 400 KBA codes, 24 provisional mappings, exact source-aware mapping coverage, and the 16-state baseline. It then created and read back a byte-preserving ignored backup through a separate read-only connection. The DDL ran in one transaction and the independent validator recomputed the regional totals from core tables.

The deployed regional view retains equipment and point measures at separate aggregation stages, uses the maximum valid semicolon-delimited connector-power token within each point, exposes `points_without_valid_power`, and retains mapping-quality indicators. The combined view has one row per KBA code and actual KBA stock date, with infrastructure values repeated across the three stock dates rather than summed.

## Batch 07 authoritative crosswalk review

Batch 07 reviewed all 24 rows that were explicitly provisional in the Crosswalk CSV and permanent DuckDB reference table. The detailed evidence matrix is in [reports/batch07_authoritative_crosswalk_review.md](../reports/batch07_authoritative_crosswalk_review.md).

- Twenty-two alias rows are independently supported at the row/entity level by the Destatis GV-ISys Q3 2026 administrative classification and the official KBA FZ 27.15 July 2026 row with the same state, five-digit key, and identifiable label variant.
- The two Trier rows are only partially supported: Destatis distinguishes Trier city (`07211`) from Landkreis Trier-Saarburg (`07235`), while KBA FZ 27.15 reports one combined registration-region row, `07211 TRIER-SAARBURG`.
- No reviewed row was unresolved at the row-identity level, but no universal KBA `Statistische Kennziffer` = AGS/ARS rule was found. Destatis AGS/ARS and KBA registration-district keys remain distinct concepts.
- All 24 rows remain operationally provisional. This documentation review does not authorize a Crosswalk CSV, DuckDB reference-table, analytics-view, or KPI change.

The official KBA July 2026 FZ 27.15 row reports **7,869 BEVs** for `07211 TRIER-SAARBURG`. This is combined KBA registration-region stock, not a Trier-city-only or Trier-Saarburg-county-only value. The existing aggregate-before-join method is therefore preserved.

## Batch 08 code-system and boundary verification

Batch 08 independently checked the 22 identity-supported aliases, Hanau's 2026 boundary change, the three local KBA FZ 27.15 snapshots, and the Trier registration-region treatment. The detailed evidence matrix is in [reports/batch08_geographic_code_verification.md](../reports/batch08_geographic_code_verification.md).

- The 22 aliases have direct **row-level** code evidence: the KBA five-digit `Statistische Kennziffer` matches the dated Destatis five-digit Kreis component, and the state, administrative type, and entity identity agree. This does not establish a universal KBA-code = AGS/ARS relationship.
- No alias is supported only by entity-level evidence; no alias identity is unresolved or conflicting. The two Trier rows are separate administrative entities supported only as one combined KBA registration region and are not counted as aliases.
- Hanau became a kreisfreie Stadt on 2026-01-01. The 2026-09-30 BNetzA snapshot has separate Hanau and Main-Kinzig-Kreis rows, and KBA FZ 27.15 has separate `06415 HANAU,STADT` and `06435 MAIN-KINZIG-KREIS` rows on 2026-01-01, 2026-04-01, and 2026-07-01. The current crosswalk has no Hanau coverage mismatch.
- The current 400-code model remains defensible as a KBA registration-region model for these snapshots, not as an authoritative 400-region administrative model. A historical boundary-vintage note is required before older or cross-product series are presented.
- All 24 operational mappings remain provisional. No CSV, reference table, view, KPI formula, source row, or vehicle count was changed.

For display, use the owner-approved label **Trier / Trier-Saarburg (gemeinsamer Zulassungsbezirk)**. The July 2026 value of 7,869 BEVs is joined once after aggregation; it must not be assigned to either administrative unit.

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

The 375 ordinary matches were checked against the local July KBA snapshot. The 22 aliases and two Trier rows make 24 explicitly provisional mappings. Batch 07 adds evidence for 22 row/entity identities and partial support for the two Trier aggregation mappings, but no row is labelled officially verified in the operational data.

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

The target state, local administrative type, and KBA display label were checked for each candidate against the local July workbook and the contemporary Destatis administrative classification. The 22 aliases are supported as row/entity identities, but the KBA product does not publish a universal AGS/ARS crosswalk; they remain provisional until the owner approves the status treatment.

## City/county collisions and special conventions

### Berlin and Hamburg

The crosswalk explicitly maps Kreisfreie Stadt Berlin to KBA code 11000 and Kreisfreie Stadt Hamburg to KBA code 02000. The KBA labels are simply BERLIN and HAMBURG. These are explicit state/city naming conventions, not normalized-name matches.

### Trier and Trier-Saarburg

Destatis distinguishes Trier city (`07211`) from Landkreis Trier-Saarburg (`07235`). The official Landkreis page and the 2022 public-law agreement establish a common Kfz registration office and common registration district for both areas. KBA FZ 27.15 nevertheless reports one district-level row as `07211 TRIER-SAARBURG`; it has no separate `07235` row. An official Rheinland-Pfalz method note also describes the KBA registration district Trier-Saarburg as including the city of Trier.

The July 2026 FZ 27.15 row reports 7,869 BEVs, 160,422 passenger cars, and 3,516 PHEVs for this combined KBA row. FZ 27.17 uses the presentation label `07211 TRIER,STADT` for municipality rows, so KBA worksheet labels are not sufficient to define a separate administrative boundary. The 7,869 BEVs must not be allocated to either source geography without new approved evidence.

Both original BNetzA rows are retained:

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

Joining the raw 401-row crosswalk directly to KBA stock would duplicate the 07211 vehicle stock. The Batch 03 validation measured 2,362,218 BEVs after aggregate-before-join and 2,370,087 in the intentionally demonstrated raw 401-row join. Shared registration administration is not treated as proof that the administrative boundaries or all KBA worksheets are identical.

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

The CSV's `kba_reference_date` identifies the KBA release used for local matching evidence. It must not be used to overwrite the actual `reference_date` of a KBA stock row when the combined model is built.

## Temporal meaning of combined measures

BNetzA infrastructure is dated `2026-09-30`; KBA district stock is dated `2026-01-01`, `2026-04-01`, or `2026-07-01`. A combined row is therefore a cross-snapshot comparison. The infrastructure measures may be repeated beside each KBA date, but they must not be summed across dates.

In particular, January and April BEV-to-charging-point ratios are not contemporaneous infrastructure-coverage ratios. The July ratio is also not contemporaneous in a strict same-date sense because the latest infrastructure snapshot is September. Any BEV-per-point measure remains descriptive and provisional because the BNetzA register is not exhaustive and the geographic mappings remain partly provisional. KBA BEV and PHEV values are registered stock, not vehicle sales.

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
9. Recheck the source-aware equipment-to-point join on `(source_id, excel_row)` and confirm that all source rows are retained.
10. Recompute point bands from the maximum successfully parsed semicolon-separated connector-power token and reconcile every band to the point denominator.
11. Validate one combined row per KBA code and actual KBA stock reference date for every source snapshot; never sum repeated infrastructure rows across stock dates.

## Batch 09 BBSR feasibility findings

Batch 09 assessed the official four-category BBSR siedlungsstruktureller Kreistyp
before implementation. Batch 10 acquired and built the separate reference without
adding it to DuckDB or the existing Crosswalk. The full feasibility evidence is in
[reports/batch09_bbsr_feasibility.md](../reports/batch09_bbsr_feasibility.md);
the build evidence is in [reports/batch10_bbsr_reference_validation.md](../reports/batch10_bbsr_reference_validation.md).

- The current official BBSR reference artifact is `raumgliederungen-referenzen-2025.xlsx`,
  `Kreisreferenz`, with geographic stand `2025-12-31` and workbook stand
  `2026-09-11`. It contains 400 Kreis rows, 362 Kreisregion keys, and compact
  four-class codes 1–4. The five-category differentiated field is not the target
  classification.
- BBSR's classification basis is Kreisregionen: smaller independent cities under
  100,000 inhabitants can be grouped with associated counties. A BBSR Kreis row
  therefore must not be interpreted as an independent KBA registration region.
- A read-only five-digit prefix screen found 399 intersections between the 400
  July 2026 KBA codes and BBSR 2025 Kreis prefixes. KBA-only `06415` is Hanau;
  BBSR-only `07235` is Trier-Saarburg. This is a compatibility screen, not a
  validated KBA-to-BBSR/AGS/ARS crosswalk.
- The 2025 BBSR table has Main-Kinzig-Kreis but no separate Hanau row, so its type
  cannot be copied to the 2026 Hanau KBA row without a compatible post-change
  reference or approved conversion method.
- BBSR assigns Trier city to compact type 1 and Trier-Saarburg to compact type 3,
  while KBA combines both in registration region `07211`. A future KBA-level
  BBSR value must therefore be `mixed_or_unresolved`; the shared vehicle stock
  remains one combined value and is never allocated without approval.
- The owner-approved display label is **Trier / Trier-Saarburg (gemeinsamer
  Zulassungsbezirk)**. Boundary-vintage limitations must remain visible in any
  historical or cross-source comparison.

The recommendation was **CONDITIONAL GO** for a separate, versioned BBSR
reference and controlled compatibility layer, and **NO-GO** for direct
assignment of one BBSR category to all current KBA codes. Batch 10 implemented
only the separate reference; Batch 13 later implemented the approved
source-grain charging-only path without changing the Crosswalk or KBA layer.

## Relationship to future BBSR settlement types

BBSR settlement or spatial typologies are an enrichment dimension, not a
replacement for administrative districts or KBA registration regions. A future
integration must preserve BBSR KRS and Kreisregion keys, use an explicit dated
KBA compatibility bridge, retain source and classification vintages, and expose
`mixed_or_unresolved` and `vintage_mismatch` statuses. It must aggregate charging
before joining KBA stock, never allocate shared Trier stock without approval, and
must not imply that a settlement type is a KBA registration district. The
versioned BBSR reference is available outside the Crosswalk. Batch 13 now
supports source-grain charging-only category KPIs; KBA compatibility and any
vehicle-stock category use remain pending approval.

## Batch 10 BBSR reference validation

The reproducible generator reads the preserved official workbook and emits one
row per KRS2025 administrative Kreis row. It preserves the original KRS2025
and KKR2025 codes as strings, the original names, the source sheet/row lineage,
the 2025-12-31 geographic reference date, and the exact compact four-category
KTU2025/KTU_NAME classification.

Observed results are 400 Kreis rows, 362 distinct Kreisregion keys, 36
multi-district Kreisregion groups, and compact type counts 68/131/98/103 for
codes 1/2/3/4. Hanau has no row in the 2025 vintage; Main-Kinzig-Kreis is
preserved as type 2. Trier city is type 1 and Trier-Saarburg is type 3 in
separate BBSR rows. Neither type is assigned to KBA 07211 and no shared stock
is allocated.

## Batch 11 BBSR–KBA compatibility audit

Batch 11 performed the approved read-only compatibility audit with
[`scripts/11_audit_bbsr_kba_compatibility.py`](../scripts/11_audit_bbsr_kba_compatibility.py).
The complete evidence report is in
[`reports/batch11_bbsr_kba_compatibility.md`](../reports/batch11_bbsr_kba_compatibility.md);
the 400-row non-operational output is in
[`reports/batch11_bbsr_kba_compatibility_audit.csv`](../reports/batch11_bbsr_kba_compatibility_audit.csv).

The audit inspected the actual BBSR `KRS2025`/`KKR2025`/`KTU2025`-derived CSV
fields, the KBA `district_code`/`reference_date`/`bev_cars` fields, the original
BNetzA district identities, and the deployed aggregate-before-join views. It
preserved leading zeroes and opened DuckDB with `read_only=True`. It did not
create a bridge, change the Crosswalk, modify the BBSR CSV, or write to DuckDB.

Under the strict rule that `EXACT` requires an authoritative, dated KBA-to-BBSR
equivalence, the result is 0 `EXACT`, 0 `HOMOGENEOUS_COMPOSITE`, 1 `MIXED`, 2
`VINTAGE_CONFLICT`, 397 `UNRESOLVED`, and 0 `CONFLICTING` regions. The 399
five-digit prefix intersections remain diagnostic candidates, not a BBSR
classification coverage measure. No production KBA region can currently be
assigned a BBSR category from the approved evidence set.

The two boundary-vintage rows are Hanau `06415` and current Main-Kinzig-Kreis
`06435`: BBSR stand 2025-12-31 predates Hanau's 2026-01-01 separation, and the
2025 Main-Kinzig type must not be inherited by Hanau or silently treated as an
exact type for the current remainder. KBA `07211` remains `MIXED` because its
combined registration-region stock covers BBSR type 1 Trier city and type 3
Trier-Saarburg. Its approved display label and aggregate-before-join treatment
remain unchanged.

The general KBA denominator still reconciles to 400 regions, 211,253 charging
points, and 2,362,218 July BEVs. These totals describe KBA registration-region
coverage only; they are not BBSR urban/rural KPIs. BBSR-to-KBA integration is
**NOT IMPLEMENTED** pending owner approval of a dated authoritative bridge,
vintage treatment, mixed-region handling, and any category-level reporting.

## Batch 12 two-path BBSR integration investigation

Batch 12 evaluated two separate, read-only paths in
[`reports/batch12_bbsr_integration_paths.md`](../reports/batch12_bbsr_integration_paths.md),
reproduced by
[`scripts/12_audit_bbsr_integration_paths.py`](../scripts/12_audit_bbsr_integration_paths.py)
with the non-operational output in
[`reports/batch12_bbsr_integration_paths_audit.csv`](../reports/batch12_bbsr_integration_paths_audit.csv).

Path A starts from the 401 BNetzA state/district source combinations and uses
state, administrative type, and normalized administrative identity to identify
a BBSR 2025 Kreis candidate. It does not use the KBA code as proof and does not
claim that a BNetzA field is AGS, ARS, KBA, or BBSR KRS. The result is 399
`VERIFIED_COMPATIBLE`, one `CONDITIONAL_VINTAGE` Main-Kinzig-Kreis row, one
`UNRESOLVED` Hanau row, and no mixed or conflicting source rows. The verified
rows represent 117,077 of 117,662 equipment records and 210,262 of 211,253
charging points. This supports only a conditional, charging-only descriptive
enrichment at BNetzA source geography, with the BNetzA and BBSR dates visible.

Path B starts from the 400 KBA registration regions and requires a dated,
authoritative relationship to administrative Kreis geography before a BBSR
class can be assigned. The result remains 0 strict verified regions, points, or
July BEVs; the statuses are one `MIXED` Trier region, two
`VINTAGE_CONFLICT` Hanau/Main-Kinzig rows, 397 `UNRESOLVED`, and no
`CONFLICTING` rows. The five-digit prefix intersections remain diagnostic
candidate evidence only. KBA `07211` remains the combined Trier /
Trier-Saarburg registration region with 7,869 July BEVs counted once and no
allocation between the two BBSR rows.

The official resources reviewed in Batch 12 include Destatis GV-ISys and dated
administrative extracts, BBSR reference downloads and the Umsteigeschlüssel, the
Federal Employment Agency political-structure reference, KBA FZ 27 metadata,
and official Hanau/Trier administrative pages. None supplied a universal,
dated KBA registration-region to AGS/ARS/KRS/BBSR bridge for all 400 KBA
regions. Accordingly, Path A is **CONDITIONAL GO** for a separate,
non-operational charging-only descriptive path, while Path B is **NO-GO** for
production BBSR assignment or BBSR-based BEV ratios. Batch 13 adds only the
separate, source-grain charging layer described below; it does not change the
Crosswalk, KBA views, or vehicle-stock measures.

## Batch 13 charging-only BBSR deployment

Batch 13 implements Path A at the original BNetzA state/district grain. The
versioned bridge preserves the BNetzA source identity, both source dates, BBSR
administrative/Kreisregion identifiers, settlement type where verified, the
Batch 12 evidence reference, and a visible compatibility status. It contains
401 rows: 399 `VERIFIED_COMPATIBLE`, one `CONDITIONAL_VINTAGE`
Main-Kinzig-Kreis row, and one `UNRESOLVED` Hanau row.

Only the 399 verified rows receive a settlement type. Main-Kinzig's BBSR
administrative and Kreisregion code is retained as pre-change evidence but its
type is NULL; Hanau has no BBSR 2025 row and remains unclassified. The summary
view therefore has four BBSR categories plus `UNCLASSIFIED`, and the latter
contains 585 equipment rows and 991 charging points. Verified coverage remains
399/401 districts, 117,077/117,662 equipment (99.502813%), and
210,262/211,253 points (99.530894%).

The charging views are independent of KBA stock and the existing Crosswalk.
Equipment and point metrics are aggregated separately. Point classification
splits semicolon-separated `connector_power_raw` values, normalizes decimal
commas, takes the maximum valid power per point, and exposes any unclassifiable
power count. Trier city and Trier-Saarburg remain separate source rows with
types 1 and 3; no shared KBA stock is joined or allocated.

## Batch 13.1 owner-approved boundary scenario

Batch 13.1 keeps the official Batch 13 result as the **OFFICIAL BBSR 2025
BASELINE** and adds a separate **OWNER-APPROVED 2026 ANALYTICAL SCENARIO**.
The scenario reference has exactly two rows at the observed BNetzA source
grain:

- Hanau `06415` → analytical category 1 using `OWNER_APPROVED_SCENARIO`.
- Main-Kinzig-Kreis `06435` → category 2 using
  `HISTORICAL_BBSR_CARRY_FORWARD` from official BBSR 2025 type 2.

The code values are the existing Crosswalk `kba_district_code` identifiers for
the BNetzA source rows. They are not used as proof of KBA/BBSR equivalence.
Both rows have `official_bbsr_verification = false` and remain visibly
non-`VERIFIED_COMPATIBLE`. Hanau's category 1 must not be described as an
official BBSR 2025 or 2026 classification. Its municipal population context
(over 107,000 in the municipal register versus approximately 98,000 in the
April 2026 Hessen census-based statement) is documented as provenance context,
not as a BBSR classification formula. Main-Kinzig's carried-forward type has a
boundary-vintage caveat because Hanau separated in 2026.

The scenario view overlays these two rows onto the official Batch 13 charging
view, preserving source-aware equipment/point joins and maximum-per-point power
classification. It covers all 401 BNetzA source districts, moves 585 equipment
records and 991 points out of the official baseline `UNCLASSIFIED` group, and
has zero scenario-unclassified districts. It does not integrate KBA stock or
allocate the shared Trier registration-region stock. Evidence is recorded in
the reference CSV and in
[`reports/batch13_1_bbsr_scenario_classification.md`](../reports/batch13_1_bbsr_scenario_classification.md),
with the [Hanau municipal page](https://www.hanau.de/wirtschaft/profil-und-standortvorteile/hanau-in-zahlen/), [Hessen press statement](https://innen.hessen.de/presse/stadt-hanau-erhaelt-20-millionen-euro), and [Hessen municipalities page](https://innen.hessen.de/kommunales/kommunen/gemeinden-und-landkreise).
