# Batch 12 — Two-path BBSR geographic compatibility investigation

**Review date:** 2026-11-02
**Scope:** read-only research, deterministic audit, and documentation
**Starting commit:** `a31950f07f07d6a2ed1658bfb6c66772f131e950`
**Operational result:** BBSR integration remains **NOT IMPLEMENTED**

## 1. Executive summary

Batch 12 is **PASS for the requested investigation** and **NO-GO for current
production BBSR classification of KBA regions**. It evaluates two separate
paths and does not treat them as interchangeable:

- **PATH A — BNetzA administrative charging geography → BBSR:** 400 of 401
  BNetzA source districts have a unique source-grain identity in the BBSR 2025
  Kreis reference. After preserving the known vintage exception, 399 districts
  are `VERIFIED_COMPATIBLE`, one Main-Kinzig-Kreis row is
  `CONDITIONAL_VINTAGE`, and Hanau is `UNRESOLVED` because the BBSR 2025
  reference has no separate Hanau row. The verified rows represent 117,077 of
  117,662 equipment records (99.502813%) and 210,262 of 211,253 charging points
  (99.530894%). This is sufficient for a **conditional, charging-only
  descriptive path at BNetzA source geography**, with dates and BBSR vintage
  visible.
- **PATH B — KBA registration geography → authoritative administrative
  geography → BBSR:** strict verified coverage remains **0 of 400 KBA regions,
  0.000000% of charging points, and 0.000000% of July 2026 BEVs**. One region is
  `MIXED` (Trier), two are `VINTAGE_CONFLICT` (Hanau/Main-Kinzig-Kreis), and
  397 remain `UNRESOLVED`. A 399-row five-digit prefix intersection is still a
  diagnostic screen, not a geographic bridge. Current KBA-to-BBSR assignment
  and BBSR-based BEV ratios are **NO-GO**.

The result is intentionally asymmetric. Path A starts from an administrative
source geography and can support a carefully labelled charging description.
Path B starts from a KBA registration region whose relationship to AGS, ARS,
KRS, and BBSR Kreis rows is not published as a universal dated equivalence.

No DuckDB object, Crosswalk row, BBSR reference row, KPI definition, vehicle
stock value, or production geographic mapping was changed.

## 2. Scope and controls

The owner-approved scope allowed read-only geographic research, two independent
integration investigations, reproducible audit scripts, diagnostic reports,
documentation, and one local commit. It prohibited permanent BBSR integration,
DuckDB writes, Crosswalk or BBSR CSV changes, new production mappings, KPI
changes, new downloads, dependency installation, and remote publication.

The audit therefore:

1. read the existing BBSR 2025 CSV and existing BNetzA-to-KBA Crosswalk;
2. inspected actual DuckDB columns and analytics views through a
   `read_only=True` connection;
3. rebuilt BNetzA source-grain equipment and point counts from the core tables;
4. used the existing aggregate-before-join KBA regional view and one July KBA
   stock row per KBA code;
5. kept candidate BBSR identifiers separate from evidence status;
6. preserved all 401 BNetzA source districts and all 400 KBA regions in one
   non-operational CSV; and
7. did not download or import an additional dataset.

The reproducible implementation is
[`scripts/12_audit_bbsr_integration_paths.py`](../scripts/12_audit_bbsr_integration_paths.py).
Its output is
[`batch12_bbsr_integration_paths_audit.csv`](batch12_bbsr_integration_paths_audit.csv).
The CSV is diagnostic only and has the scope label
`NON_OPERATIONAL_BBSR_INTEGRATION_PATH_AUDIT`.

## 3. Baselines and actual source grains

| Baseline | Validated value | Audit treatment |
|---|---:|---|
| BNetzA equipment records | 117,662 | Counted once from `core.charging_equipment`. |
| BNetzA populated charging-point slots | 211,253 | Counted once from `core.charging_point` through the source-aware equipment key. |
| BNetzA state/district combinations | 401 | Path A denominator; no source geography silently dropped. |
| Existing Crosswalk rows | 401 | Read only; the intentional duplicate KBA target is `07211`. |
| KBA codes | 400 | Path B denominator; one row per unique registration-region code. |
| KBA district/date rows | 1,200 | Three dates × 400 codes; infrastructure is not summed across dates. |
| July 2026 district BEV stock | 2,362,218 | One July row per KBA code; no Trier allocation. |
| BBSR administrative rows | 400 | Existing 2025 `Kreisreferenz`-derived CSV. |
| BBSR Kreisregion keys | 362 | Separate BBSR aggregation concept; not treated as KBA geography. |
| BBSR multi-district Kreisregion groups | 36 | 74 component rows; all groups are homogeneous in the compact four-class field. |

The actual inspected DuckDB fields remain as documented in Batch 11:

- `core.charging_equipment`: one BNetzA equipment row, with `state_name`,
  `district_name`, and `declared_point_count`;
- `core.charging_point`: one populated point slot linked by
  `(source_id, equipment_excel_row)`;
- `core.kba_district_ev_stock`: one KBA `district_code` and `reference_date`
  row, with `bev_cars`;
- `analytics.charging_by_kba_district_2026_09_30`: one aggregate-before-join row
  per unique KBA code; and
- `analytics.kba_district_charging_vs_bev_2026`: one KBA code/date row, with
  infrastructure values repeated beside each stock date and therefore not
  additive across dates.

## 4. PATH A methodology — BNetzA administrative geography → BBSR

### 4.1 Identity rule

Path A does not use the KBA code as proof of a BBSR match. For every BNetzA
state/district source row, the script resolves a BBSR candidate using:

- the BNetzA federal state;
- the BNetzA administrative type (`city` or `county`); and
- a deterministic normalization of administrative prefixes/suffixes and
  official name descriptors such as `Stadtkreis`, `Landkreis`, `Stadt`, and
  state/city honorifics.

The administrative type is used to resolve city/county collisions such as
Heilbronn, Karlsruhe, Ansbach, Rostock, Osnabrück, Kaiserslautern, and Leipzig.
Names alone are not accepted. The BNetzA core geography has no AGS or ARS field,
so the result is an identity-level source-grain compatibility assessment, not a
claim that a BNetzA field is AGS, ARS, KBA, or BBSR KRS.

The audit keeps these concepts in separate fields:

| Field family | Meaning |
|---|---|
| BNetzA state/district/type | The observed charging-source geography and its source date. |
| BBSR candidate KRS code/name/type | The candidate administrative BBSR row and its 2025 classification. |
| Crosswalk KBA code/name | Existing local BNetzA-to-KBA context only; not used as Path A proof. |
| Evidence status | What the dated evidence supports for this path. |
| Charging-only safety | Whether a category can be used for source-grain descriptive charging counts without vehicle allocation. |

### 4.2 Status rules

| Status | Rule in this audit |
|---|---|
| `VERIFIED_COMPATIBLE` | One unique BBSR administrative Kreis row is identified from BNetzA state, administrative type, and identity; no specific boundary change was identified for the row in the reviewed official evidence. Safe only with BNetzA/BBSR dates and source-grain caveats. |
| `CONDITIONAL_VINTAGE` | The source identity is clear, but a dated boundary change makes the 2025 BBSR classification conditional. Applied to current Main-Kinzig-Kreis. |
| `MIXED` | A single BNetzA source row would contain incompatible BBSR components. No Path A source row met this condition because Trier city and Trier-Saarburg remain separate BNetzA rows. |
| `UNRESOLVED` | No BBSR row exists or a unique source identity cannot be established. Applied to current Hanau because the BBSR 2025 table has no Hanau row. |
| `CONFLICTING` | Independently supported evidence contradicts the candidate. No Path A row met this condition. |

`VERIFIED_COMPATIBLE` is deliberately narrower than a production approval. It
means the administrative source row can be described with the BBSR 2025 type at
the named source grain. It does not approve a DuckDB join, Crosswalk change,
KBA stock join, or category KPI.

### 4.3 Path A coverage

The denominator includes all 117,662 equipment records and all 211,253 populated
charging points. Equipment is counted from equipment rows; points are counted
from point rows. A source district is counted once.

| Path A evidence status | Districts | % of 401 | Equipment rows | % of equipment | Charging points | % of points |
|---|---:|---:|---:|---:|---:|---:|
| `VERIFIED_COMPATIBLE` | 399 | 99.501247% | 117,077 | 99.502813% | 210,262 | 99.530894% |
| `CONDITIONAL_VINTAGE` | 1 | 0.249377% | 439 | 0.373103% | 740 | 0.350291% |
| `UNRESOLVED` | 1 | 0.249377% | 146 | 0.124084% | 251 | 0.118815% |
| `MIXED` | 0 | 0.000000% | 0 | 0.000000% | 0 | 0.000000% |
| `CONFLICTING` | 0 | 0.000000% | 0 | 0.000000% | 0 | 0.000000% |
| **Total** | **401** | **100.000000%** | **117,662** | **100.000000%** | **211,253** | **100.000000%** |

The 399 verified rows are sufficient for a defensible **charging-only
descriptive** analysis if the output remains at BNetzA administrative source
grain, preserves `2026-09-30` and `2025-12-31`, labels the result as a BBSR
reference enrichment, and keeps the conditional/unresolved rows visible. No
vehicle-stock denominator is needed for this path, and no vehicle stock was
allocated.

## 5. PATH B methodology — KBA → authoritative administration → BBSR

### 5.1 Bridge rule

Path B requires an authoritative, dated relationship from the KBA product's
`Statistische Kennziffer` / `Zulassungsbezirk` geography to an administrative
Kreis key before a BBSR type can be assigned. The existing Crosswalk is a local
source crosswalk and remains operationally provisional where documented; it is
not treated as a universal KBA = AGS, KBA = ARS, or KBA = BBSR KRS statement.

The audit reuses the prior Batch 11 row evidence and independently verifies that
the current sources still produce the same non-operational statuses. It does
not promote any operational Crosswalk `verification_status`.

For each KBA region, the output preserves:

- KBA code, label, state, and all three KBA reference dates;
- all contributing BNetzA source identities and their Crosswalk evidence types;
- direct BBSR component candidates where the BNetzA source identity resolves;
- the separate five-digit BBSR prefix candidate screen;
- BBSR type and Kreisregion fields;
- geographic reference dates and boundary assessment;
- composite/mixed/allocation flags; and
- January, April, and July BEVs, with July stock counted once.

### 5.2 Path B coverage

The denominator is 400 unique KBA regions, 211,253 charging points, and
2,362,218 July 2026 district BEVs. The charging measure comes from the unique
KBA-code regional view. KBA stock comes from one July row per KBA code. No
infrastructure value is summed across the three repeated KBA dates.

| Path B audit status | KBA regions | % of 400 | Charging points | % of points | July BEVs | % of July BEVs |
|---|---:|---:|---:|---:|---:|---:|
| `EXACT` | 0 | 0.000000% | 0 | 0.000000% | 0 | 0.000000% |
| `HOMOGENEOUS_COMPOSITE` | 0 | 0.000000% | 0 | 0.000000% | 0 | 0.000000% |
| `MIXED` | 1 | 0.250000% | 503 | 0.238103% | 7,869 | 0.333119% |
| `VINTAGE_CONFLICT` | 2 | 0.500000% | 991 | 0.469106% | 11,168 | 0.472776% |
| `UNRESOLVED` | 397 | 99.250000% | 209,759 | 99.292791% | 2,343,181 | 99.194105% |
| `CONFLICTING` | 0 | 0.000000% | 0 | 0.000000% | 0 | 0.000000% |
| **Total** | **400** | **100.000000%** | **211,253** | **100.000000%** | **2,362,218** | **100.000000%** |

Strict verified coverage is the sum of `EXACT` and
`HOMOGENEOUS_COMPOSITE`: **0 regions, 0 charging points, and 0 July BEVs**.
The 399 five-digit prefix intersections remain candidate evidence only. The
unresolved regions are retained in the denominator instead of being silently
excluded or assigned a type to increase coverage.

## 6. Official evidence and conversion resources

The research used official online documentation and the already-preserved local
source artifacts. No additional dataset was downloaded or imported in Batch 12.

### 6.1 Sources used or directly inspected

| Official resource | Role | Batch 12 treatment |
|---|---|---|
| [Destatis GV-ISys overview](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/_inhalt.html) and [GV-ISys introduction](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/gemeindeverzeichnis-einleitung.html) | Defines administrative units, AGS, ARS, and dated GV-ISys releases. | Used as the authoritative key-system definition. The landing page can return HTTP 403 to automated readers; the official URL is retained. |
| [Destatis Q3 2026 extract page](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GVAuszugQ/AuszugGV3QAktuell.html) and [GV100AD Q3 2026 page](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GV100ADQ/GV100AD3QAktuell.html) | Dated administrative Kreis/name/key evidence. | Previously inspected in Batch 07/08 and reused as evidence context; not downloaded again in Batch 12. |
| [BBSR reference-download page](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/downloads/download-referenzen.html) and [2025 workbook](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/downloads/raumgliederungen-referenzen-2025.xlsx?__blob=publicationFile&v=3) | Official BBSR reference-table inventory and selected 2025 source. | Existing local BBSR CSV was read without modification; its source manifest and Batch 10 report preserve workbook provenance and hash. |
| [BBSR Kreis/Kreisregion information](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/deutschland/kreise/Kreise_Kreisregionen/Kreise.html) and [siedlungsstrukturelle Kreistypen](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/deutschland/kreise/siedlungsstrukturelle-kreistypen/kreistypen.html) | Explains BBSR Kreis/Kreisregion grains and the typology. | Used to keep BBSR classification separate from KBA registration regions. |
| [KBA FZ 27 metadata at GovData](https://www.govdata.de/suche/daten/fz-27-2026-bestand-an-kraftfahrzeugen-und-kraftfahrzeuganhangern-nach-ausgewahlten-merkmalen-bu) and [KBA July FZ 27 workbook](https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/fz27_202607.xlsx?__blob=publicationFile&v=3) | Establishes the KBA product, its stock dates, and `Zulassungsbezirke` grain; the local workbook supplies the observed rows. | Existing local KBA rows and official product metadata were reused. No new KBA workbook was downloaded. |
| [BA political-administrative structure](https://statistik.arbeitsagentur.de/DE/Navigation/Grundlagen/Klassifikationen/Regionale-Gliederungen/Politische-Gebietsstruktur-Nav.html) | Current political structure and boundary-change warnings. | Used as an independent current-structure resource; no KBA bridge was inferred from it. |
| [Hessen administrative information](https://innen.hessen.de/kommunales/kommunen/gemeinden-und-landkreise) and [January 2026 key directory](https://statistik.hessen.de/sites/statistik.hessen.de/files/2026-01/verz-2_26-01.pdf) | Hanau/Main-Kinzig boundary and dated key evidence. | Used for the explicit 2026 vintage conflict. |
| [Official Trier-Saarburg registration-office page](https://trier-saarburg.de/ihr-anliegen/zulassungsstelle/) | Confirms shared registration administration for Trier city and Trier-Saarburg. | Used for the mixed-region rule; it does not provide a BEV allocation. |

### 6.2 Resources discovered but not verified as a KBA conversion

| Resource | What it may provide | What it does not establish |
|---|---|---|
| [BBSR Umsteigeschlüssel](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/umstiegsschluessel/umsteigeschluessel.html) | BBSR conversion keys between BBSR geographic stands and related historical/current BBSR references. | It is not a KBA `Zulassungsbezirk` → AGS/ARS/KRS bridge. It was not imported or treated as a verified KBA mapping in this batch. |
| Destatis GV-ISys quarterly/annual releases | Dated administrative hierarchy, AGS/ARS, Kreis identifiers, and change history. | They do not, by themselves, state that a KBA FZ 27 `Statistische Kennziffer` is AGS, ARS, or a universal KRS key. |
| BA political-structure overview, XLSX, SHP, and historical reform resources | Current Kreis/city inventory and boundary-vintage context. | The BA political structure is a separate administrative reference, not a KBA product bridge. |
| INKAR | Online regional indicators and BBSR-related context. | The online atlas is not a verified KBA-to-BBSR conversion table; the complete database was not downloaded. |

No definitive KBA-to-BBSR conversion resource was found. A future attempt to
inspect additional dated Destatis, BA, or KBA files would require explicit owner
approval if it involves a new dataset download; it must record the exact URL,
file size where available, purpose, source date, and resulting code-system
evidence before any status promotion.

## 7. Dated compatibility findings

### 7.1 Path A administrative identity

The BNetzA source has 401 current state/district combinations. The BBSR 2025
reference has 400 administrative rows because it predates Hanau's separation.
The audit found:

- 400 BNetzA rows with a unique direct source-grain BBSR identity;
- 399 rows that are usable for charging-only descriptive BBSR enrichment under
  the `VERIFIED_COMPATIBLE` rule;
- one Main-Kinzig-Kreis row that is `CONDITIONAL_VINTAGE`; and
- one Hanau row that is `UNRESOLVED` because no BBSR 2025 Hanau row exists.

The source-grain identity is not a universal code-system result. The existing
Crosswalk context contains 22 previously reviewed row-level aliases, two
state/city naming conventions, and two shared Trier rows. Those evidence types
remain visible in the output and no operational `verification_status` changes.

### 7.2 Kreisregion complications

The BBSR reference has 36 multi-district Kreisregion groups covering 74 BBSR
administrative rows. The compact BBSR type is homogeneous inside every group in
the 2025 reference, but a Kreisregion is still not a KBA registration region.

For Path A, a BNetzA source row can retain its BBSR administrative type at its
own source grain. A later Kreisregion roll-up would need to aggregate source
rows explicitly and retain both KRS and Kreisregion keys. The audit does not
collapse these rows or create a production roll-up.

For Path B, the homogeneous BBSR Kreisregion property does not repair the
missing KBA bridge. It cannot turn a five-digit prefix intersection into a
verified KBA assignment.

### 7.3 Berlin, Hamburg, Bremen, and Bremerhaven

The BBSR 2025 reference contains separate rows for Berlin, Hamburg, Bremen, and
Bremerhaven, each in compact type 1. Path A preserves them as separate source
administrative rows. Path B does not use their equal-looking or shortened KBA
labels as a universal code rule.

### 7.4 Other administrative exceptions

Region Hannover, Städteregion Aachen, and Regionalverband Saarbrücken remain
named administrative structures with their own official wording. Their BBSR
candidate type is retained as published; the audit does not replace those
structures with a generic county or KBA label.

## 8. Hanau / Main-Kinzig-Kreis

The official Hessian evidence records that Hanau became a kreisfreie Stadt and
was removed from Main-Kinzig-Kreis effective **2026-01-01**. The local BNetzA
source and all three local KBA FZ 27.15 snapshots contain separate rows:

| Region | KBA code | BBSR 2025 row | July 2026 BEVs | BNetzA points | Path A | Path B |
|---|---|---|---:|---:|---|---|
| Hanau | `06415` | Missing | 2,394 | 251 | `UNRESOLVED` | `VINTAGE_CONFLICT` |
| Main-Kinzig-Kreis | `06435` | `06435000`, type 2 | 8,774 | 740 | `CONDITIONAL_VINTAGE` | `VINTAGE_CONFLICT` |

The Main-Kinzig type 2 classification is not copied to Hanau. It is also not
called exact for the current post-separation Main-Kinzig remainder. No stock or
charging measure is estimated, reallocated, or combined for BBSR purposes.

## 9. Trier / Trier-Saarburg

The BBSR 2025 reference keeps the administrative rows separate:

| BBSR row | BBSR code | Compact type |
|---|---|---:|
| Trier, kreisfreie Stadt | `07211000` | 1 — kreisfreie Großstadt |
| Trier-Saarburg | `07235000` | 3 — ländlicher Kreis mit Verdichtungsansätzen |

KBA FZ 27.15 reports one combined registration-region row `07211
TRIER-SAARBURG`. The current July values are:

- 503 charging points after aggregating the two BNetzA source rows;
- 7,869 July 2026 BEVs in the one KBA row; and
- no allocation between Trier city and Trier-Saarburg.

Path A treats the two BNetzA source rows separately and can use their respective
BBSR types for charging-only source descriptions, subject to the visible
2026/2025 dates. Path B treats `07211` as `MIXED` and does not assign one BBSR
class. The established display label remains:

> Trier / Trier-Saarburg (gemeinsamer Zulassungsbezirk)

The label describes the KBA registration region. It is not an administrative
BBSR Kreis and does not authorize a city/county vehicle-stock split.

## 10. Confirmed code relationships and remaining uncertainty

Confirmed or independently supported relationships are deliberately limited:

1. Destatis defines AGS and ARS as administrative/statistical key systems;
   their components include the federal state and Kreis levels.
2. The BBSR CSV preserves eight-digit administrative KRS2025-derived rows and
   separate Kreisregion keys at the 2025 geographic stand.
3. KBA FZ 27 publishes alternative-drive stock by `Zulassungsbezirke` and the
   local FZ 27.15 rows contain the observed five-digit product keys and labels.
4. The existing local Crosswalk provides a reproducible BNetzA source-to-KBA
   identity context, including the two Trier source rows under `07211`.
5. Official dated evidence supports the 2026 Hanau separation and the shared
   Trier registration administration.

Not confirmed:

- a universal KBA `Statistische Kennziffer` = Destatis AGS rule;
- a universal KBA `Statistische Kennziffer` = Destatis ARS rule;
- a universal KBA registration-region = BBSR KRS rule;
- a dated KBA-to-BBSR conversion table covering all 400 KBA regions; or
- a defensible allocation of the 7,869 Trier BEVs between the two BBSR rows.

The 399 KBA/BBSR five-digit prefix intersections therefore remain a diagnostic
candidate screen. They are not evidence of 399 verified BBSR classifications.

## 11. Path comparison matrix

| Criterion | PATH A — BNetzA administrative source → BBSR | PATH B — KBA registration → administration → BBSR |
|---|---|---|
| Authoritative evidence coverage | 399 source districts are verified at named administrative source grain; one conditional and one unresolved. Formal AGS/ARS fields are absent from BNetzA. | 0 strict verified KBA regions; 1 mixed, 2 vintage conflicts, 397 unresolved. |
| Geographic compatibility | Direct source identity is compatible with one BBSR Kreis row for charging-only descriptions, with dates visible. | KBA registration geography is not proven equivalent to BBSR administrative geography. |
| Boundary vintage issues | BNetzA 2026-09-30 versus BBSR 2025-12-31; Main-Kinzig is conditional and Hanau is missing. | Same vintage gap plus the KBA-to-administration bridge gap; Hanau/Main-Kinzig cannot be assigned. |
| Composite region issues | BBSR Kreisregion components can be retained separately; 2025 component types are homogeneous. | KBA 07211 is a mixed registration region; BBSR Kreisregion structure does not repair the bridge. |
| Data-loss risk | Low for source-grain charging counts if unresolved/conditional rows remain visible; no vehicle stock is required. | High if prefix candidates are promoted; would hide mixed geography and vintage breaks. |
| Double-counting risk | Low at BNetzA source grain; risk returns if KBA stock is joined before aggregating shared code 07211. | High without aggregate-before-join; Trier stock must remain one KBA row. |
| Reproducibility | High: local source tables, BBSR CSV, explicit identity rule, dates, and deterministic audit output. | Reproducible as a no-go audit, but a production bridge remains missing. |
| Analytical value | Useful for descriptive charging counts by administrative source geography and BBSR reference type. | Useful for gap analysis and future bridge validation; not ready for BBSR KPIs. |
| Complexity | Moderate; requires a separate source-grain enrichment and vintage flags. | High; requires a product-specific dated bridge and mixed/composite rules. |
| Tableau suitability | Conditional for an internal/non-operational source-grain view; no production BBSR filter yet. | Not suitable for a production BBSR category view; show audit status only. |
| Remaining approval requirements | Approve the non-operational charging-only use and whether a future source-grain reference may be designed. | Approve a dated KBA bridge, post-2026 BBSR vintage treatment, Hanau rule, and Trier no-allocation rule before any integration. |

## 12. Recommendations

### PATH A — CONDITIONAL GO

Proceed only with a separate, non-operational charging-only descriptive path at
BNetzA administrative source grain. The minimum safeguards are:

- keep BNetzA and BBSR source dates visible;
- retain the BNetzA state, district, and administrative type;
- retain BBSR KRS and Kreisregion identifiers in separate fields;
- expose `VERIFIED_COMPATIBLE`, `CONDITIONAL_VINTAGE`, and `UNRESOLVED` rows;
- do not infer AGS, ARS, or KBA equivalence from the candidate fields;
- do not join vehicle stock or calculate BBSR BEV ratios through this path; and
- obtain owner approval before creating any permanent DuckDB view or Tableau
  enrichment.

The safe current interpretation is **descriptive charging infrastructure by
administrative source geography, enriched with a dated BBSR reference type**.
It is not a completed BBSR integration.

### PATH B — NO-GO

Do not assign BBSR types to current KBA regions, calculate BBSR-based BEV
ratios, or add a production BBSR filter from the current evidence. A future
conditional path would require:

1. an authoritative dated KBA product-specific bridge to administrative Kreis
   geography, with the code system explicitly named;
2. a compatible post-2026 BBSR reference or approved conversion for
   Hanau/Main-Kinzig-Kreis;
3. a first-class mixed status for Trier `07211` and no stock allocation unless
   separately approved; and
4. independent validation of one-to-one/composite coverage and denominators.

## 13. Minimal proposed integration approach (not implemented)

If the owner approves a future design, use two separate relations rather than a
generic geographic key:

1. **BBSR reference dimension:** one row per BBSR source version and KRS row,
   with source URL, license, geographic stand, Kreisregion, type code, and
   original names.
2. **Path A source-grain relation:** BNetzA source geography to BBSR KRS,
   retaining direct identity evidence, source dates, status, and a charging-only
   safety flag. This relation must not replace the existing Crosswalk.
3. **Path B compatibility relation:** KBA product/date/code/label to the
   authoritative administrative key and then to BBSR KRS, with component role,
   evidence URL, effective date, status, and `allocation_applied`.
4. **Reporting controls:** aggregate BNetzA charging measures to unique KBA code
   before any KBA stock join; preserve `07211` as one mixed KBA region; suppress
   only unsupported single-category rollups; never allocate Trier stock by an
   unapproved estimate.

No part of this proposed model was created in Batch 12.

## 14. Decisions requiring owner approval for Batch 13

1. Approve or defer the Path A charging-only descriptive use of the 399 verified
   source-grain rows, including the visible BNetzA 2026/BBSR 2025 vintage note.
2. Decide whether a compatible post-2026 BBSR reference is required before any
   Hanau/Main-Kinzig category comparison.
3. Approve or reject commissioning a product-specific, dated KBA-to-AGS/ARS/KRS
   bridge investigation. No universal code-prefix rule should be approved.
4. Reaffirm that KBA `07211` remains the combined display region and that its
   7,869 July BEVs are not allocated between Trier and Trier-Saarburg.
5. Decide whether historical KBA snapshots are required before publishing any
   pre-2026 or cross-vintage regional trend.
6. Approve any new source download, including exact URL, size, purpose, source
   date, and owner approval, before it is added to the evidence set.
7. Approve any future DuckDB object, Tableau enrichment, or BBSR KPI separately;
   none is authorized by this batch.

## 15. Validation and reproducibility

Commands run from the project root:

```text
.venv/bin/python -m py_compile scripts/12_audit_bbsr_integration_paths.py
.venv/bin/python scripts/12_audit_bbsr_integration_paths.py
```

Results:

| Check | Result |
|---|---:|
| Python syntax check | PASS |
| DuckDB opened read-only | PASS |
| Actual core/view columns inspected | PASS |
| BBSR rows / Kreisregion keys | 400 / 362 |
| BNetzA source geographies | 401 |
| KBA codes / district-date rows | 400 / 1,200 |
| Equipment / charging points / declared points | 117,662 / 211,253 / 211,253 |
| July 2026 BEV total | 2,362,218 |
| Path A audit rows / duplicate source keys | 401 / 0 |
| Path B audit rows / duplicate KBA keys | 400 / 0 |
| Path A coverage denominators | PASS |
| Path B coverage denominators | PASS |
| Hanau and Main-Kinzig vintage rules | PASS |
| Trier 503 points and 7,869 BEVs counted once | PASS |
| Existing operational statuses changed | NO |
| Source fingerprints unchanged during audit | PASS |
| New dataset downloaded/imported | NO |
| BBSR DuckDB/Crosswalk/KPI changes | NO |

Source fingerprints recorded by the audit:

| Artifact | SHA-256 |
|---|---|
| `data/reference/bbsr_settlement_types_2025.csv` | `e35c57da8d8f675fa132b629e6dda43180a18e5b78b95e1e72de30069a062e65` |
| `data/reference/bnetza_kba_district_crosswalk_2026.csv` | `fdf139c5057250184358e3014267a4a4c4259749113273f6bd48206f6a64fe6a` |
| `data/analytics/ev_charging.duckdb` | `19753969b21a581fba79cd4fcff8d46cf7afa3354c27cb0bfce33db0f6ad4d43` |
| `reports/batch11_bbsr_kba_compatibility_audit.csv` | `746087fdeab0fd5f18e354adb1ed93374248c83b45af6b19346c152244067337` |

The audit output is deterministic: repeating the script with the same local
inputs produces the same CSV and the same status/coverage summary apart from no
runtime timestamp fields. It does not create a permanent BBSR bridge or a
production geographic classification.
