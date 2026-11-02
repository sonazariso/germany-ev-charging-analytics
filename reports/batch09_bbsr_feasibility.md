# Batch 09 — BBSR Urban/Rural Classification Feasibility Study

**Review date:** 2026-11-02
**Scope:** research and documentation only
**Starting commit:** `ff54d744109d852d408c8e5b9ef5eefa4f53fe48`

## 1. Executive summary

The official BBSR settlement-structural district typology is technically relevant to
this project, but it is not safe to attach one BBSR class directly to every current
KBA registration code.

The smallest suitable current BBSR reference artifact identified in this review is
the BBSR workbook **`raumgliederungen-referenzen-2025.xlsx`**, specifically its
`Kreisreferenz` worksheet. It is a reference table rather than the complete INKAR
database. The workbook has 400 Kreis rows, 362 Kreisregion keys, and a compact
four-class field. The four-class values are available as codes 1–4 and the German
labels required for a dashboard.

The main compatibility constraints are:

- BBSR classifies 362 Kreisregionen, not simply 400 independent KBA registration
  regions. Smaller independent cities can be grouped with their associated county.
- BBSR uses administrative Kreis keys; KBA FZ 27.15 uses a product-specific
  `Statistische Kennziffer` and `Zulassungsbezirk` presentation. No official KBA
  statement establishing a universal KBA = AGS or KBA = ARS relationship was found.
- The 2025 BBSR reference vintage predates Hanau becoming a kreisfreie Stadt on
  2026-01-01. It contains Main-Kinzig-Kreis but no separate Hanau row.
- BBSR assigns Trier city to class 1 and Trier-Saarburg to class 3 in the 2025
  reference. KBA reports both in one district-level registration row, `07211
  TRIER-SAARBURG`. The combined stock must not be duplicated or allocated.

**Recommendation: CONDITIONAL GO for a separate, versioned BBSR reference and
controlled aggregation workflow; NO-GO for direct BBSR assignment to the current
KBA codes without a validated bridge.** Strategy C below is recommended: preserve
BBSR administrative/Kreisregion detail separately and aggregate only where the
component geography, vintage, and classification are compatible. BBSR integration
remains **NOT IMPLEMENTED**.

The four owner-approved controls are retained: the 22 aliases remain operationally
provisional; the combined label is **“Trier / Trier-Saarburg (gemeinsamer
Zulassungsbezirk)”**; no shared Trier stock is allocated without a separately
approved method; and historical/cross-source boundary-vintage limitations must be
shown. No BBSR data, DuckDB object, Crosswalk row, or KPI value was changed.

## 2. Scope and evidence controls

This batch:

- researched official BBSR, INKAR, Destatis, and KBA reference paths;
- inspected the current DuckDB schemas and deployed geographic views read-only;
- downloaded one small official BBSR reference workbook to temporary storage for
  inspection only;
- compared current KBA codes with BBSR 2025 Kreis prefixes as an audit screen;
- created this feasibility report and updated project documentation.

This batch did **not**:

- download the complete INKAR database;
- add BBSR to `config/sources.json`;
- copy BBSR data into the repository, DuckDB, Crosswalk, or Tableau extract;
- create a BBSR table, view, KPI formula, allocation, or classification value;
- modify the BNetzA/KBA source workbooks or the private Persian KPI document.

The BBSR and Destatis pages were intermittently unavailable to the web reader
(HTTP 403/503), but the official HTML pages and the BBSR reference workbook were
retrievable directly on 2026-11-02. The inaccessible-reader limitation does not
change the source conclusions below; direct source URLs are retained for
reproducibility.

## 3. Official datasets and versions investigated

| Source | Version or reference date | Role in the assessment |
|---|---|---|
| [BBSR: Siedlungsstruktureller Kreistyp](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/deutschland/kreise/siedlungsstrukturelle-kreistypen/kreistypen.html) | Current page accessed 2026-11-02; annual classification page | Definitions, criteria, annual-update behavior, and distinction between 400 Kreise and 362 Kreisregionen. |
| [BBSR reference download page](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/downloads/download-referenzen.html) | Current page accessed 2026-11-02 | Official current reference-table inventory. |
| [BBSR `raumgliederungen-referenzen-2025.xlsx`](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/downloads/raumgliederungen-referenzen-2025.xlsx?__blob=publicationFile&v=3) | Geographic stand 31.12.2025; workbook stand 11.09.2026 | `Kreisreferenz` sheet with `KRS2025`, Kreisregion, and four-class BBSR fields. Temporary inspection hash: `083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525`. |
| [BBSR: Kreise und Kreisregionen](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/deutschland/kreise/Kreise_Kreisregionen/Kreise.html) | Current page accessed 2026-11-02 | Explains that smaller independent cities under 100,000 inhabitants are combined with associated counties to form Kreisregionen. |
| [BBSR: Umsteigeschlüssel](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/umstiegsschluessel/umsteigeschluessel.html) | Current page accessed 2026-11-02; Kreis keys listed for 1990–2025 | Historical and current Kreis conversion keys; explains forward conversion, aggregation, and estimation limits. |
| [INKAR](https://www.inkar.de/Default) | Edition 07/2025; data on uniform stand 31.12.2023 | Official online atlas and context only. The complete INKAR download was not used. |
| [Destatis Gemeindeverzeichnis / GV-ISys](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/_inhalt.html) | Current Q3 2026 page; 30.09.2026 quarterly files and 31.12.2025 annual files listed | AGS/ARS definitions, administrative hierarchy, and dated official Kreis reference paths. |
| [KBA FZ 27 metadata](https://www.govdata.de/suche/daten/fz-27-2026-bestand-an-kraftfahrzeugen-und-kraftfahrzeuganhangern-nach-ausgewahlten-merkmalen-bu) and [July 2026 FZ 27 workbook](https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/fz27_202607.xlsx?__blob=publicationFile&v=3) | FZ 27.15 reference date 2026-07-01 | Current KBA registration-district rows, codes, labels, and BEV/PHEV stock grain. |

### Smallest suitable official BBSR artifact

The current BBSR reference download page lists a combined workbook for each recent
geographic stand. The 2025 workbook is approximately 8 MB and contains the
`Kreisreferenz` worksheet with the required fields:

- `KRS2025` and `KRS_NAME`;
- `W`/`X`: Kreisregion code and name;
- `AS`/`AT`: the compact four-category code and German label;
- the associated administrative and BBSR reference fields.

No smaller current standalone four-category download was listed on the current
BBSR page. The historical archive contains separate 2017–2020 files, but they are
not an appropriate substitute for the current 2025 reference. The old GovData
entry [Siedlungsstrukturelle Kreistypen](https://www.govdata.de/suche/daten/siedlungsstrukturelle-kreistypen)
describes a 2012 nine-category dataset and is deliberately not selected.

## 4. Four-category classification and definitions

The BBSR workbook's compact fields `AS`/`AT` provide the requested four classes.
The differentiated fields `AM`/`AN` contain five categories because they split
large and small kreisfreie Großstädte. They must not be used when the analysis
requires the official four-category result.

| Code | Official German label | English interpretation | Definition used by BBSR |
|---:|---|---|---|
| 1 | Kreisfreie Großstädte (row label: `kreisfreie Großstadt`) | Independent large cities | A kreisfreie Stadt with at least 100,000 inhabitants. |
| 2 | Städtische Kreise (row label: `städtischer Kreis`) | Urban districts | Either at least 50% of the population lives in large or medium-sized cities and overall density is at least 150 inhabitants/km², or density outside those cities is at least 150 inhabitants/km². |
| 3 | Ländliche Kreise mit Verdichtungsansätzen (row label: `ländlicher Kreis mit Verdichtungsansätzen`) | Rural districts with agglomeration tendencies | Either at least 50% of the population lives in large or medium-sized cities but overall density is below 150 inhabitants/km², or the share is below 50% and density outside those cities is at least 100 inhabitants/km². |
| 4 | Dünn besiedelte ländliche Kreise (row label: `dünn besiedelter ländlicher Kreis`) | Sparsely populated rural districts | Less than 50% of the population lives in large or medium-sized cities and density outside those cities is below 100 inhabitants/km². |

The classification uses population share in large/medium cities, Kreisregion
population density, and population density excluding large/medium cities. It is a
settlement-structure typology; the BBSR page says that locational advantages or
disadvantages are a separate dimension and are not part of this four-class type.

### Level, publisher, and current distribution

- **Publisher:** Bundesinstitut für Bau-, Stadt- und Raumforschung (BBSR).
- **Geographic level:** administrative Kreise and kreisfreie Städte represented
  through 362 Kreisregionen; not municipalities, charging points, or KBA
  registration areas.
- **Reference vintage:** geographic stand 31.12.2025 in the current reference
  workbook.
- **Source version:** `raumgliederungen-referenzen-2025.xlsx`, `Kreisreferenz`;
  workbook stand 11.09.2026.
- **Rows:** 400 Kreis rows and 362 distinct Kreisregion keys.
- **Four-class row counts:** code 1 = 68, code 2 = 131, code 3 = 98, code 4 =
  103. These are reference-row counts, not population or charging counts.

The BBSR table also shows 36 multi-row Kreisregion groups in which a smaller
independent city is represented with an associated county. Examples include
Flensburg with Schleswig-Flensburg, Neumünster with Rendsburg-Eckernförde, and
Delmenhorst with Diepholz. The component rows carry the same compact class in the
2025 table. This grouping must not be generalized to all independent cities:
Trier city and Trier-Saarburg remain separate BBSR rows.

## 5. Geographic reference dates, keys, and compatibility

### Key-system distinction

The key systems must remain separate:

| System | Field or concept | Meaning for this project |
|---|---|---|
| BBSR/Destatis | `KRS2025` / Kreis-level administrative key | Eight-digit administrative Kreis or city row in the BBSR reference table. It is not labelled as a KBA registration code. |
| Destatis | AGS | Eight-digit municipality key. Destatis defines its components as state, Regierungsbezirk where applicable, Kreis, and municipality. |
| Destatis | ARS | Twelve-digit hierarchical regional key containing state, Regierungsbezirk, Kreis, Gemeindeverband, and municipality components. |
| KBA FZ 27.15 | `Statistische Kennziffer` and `Zulassungsbezirk` | Product-specific registration-district code and label. The local KBA workbook does not by itself establish that this field is AGS, ARS, or a fixed conversion of either. |
| BNetzA | State and district text | Current charging source has names, not a BBSR, AGS, ARS, or KBA code in the normalized geography fields. |

The repeated five-digit prefix pattern is useful evidence for row-level checks, but
it is not a universal code-system equivalence. A safe future bridge must preserve
the original code system, effective date, source version, and evidence URL in
separate fields. Name similarity alone is prohibited.

### Current model inspected read-only

| Object or source | Observed result |
|---|---:|
| BNetzA source geography combinations | 401 |
| KBA FZ 27.15 district codes per snapshot | 400 |
| Crosswalk rows / distinct KBA codes | 401 / 400 |
| Deployed regional charging rows | 400 |
| Deployed combined charging/stock rows | 1,200 = 400 × 3 KBA dates |
| Explicit provisional source mappings | 24 = 22 aliases + 2 Trier rows |
| Shared KBA target | `07211`, used by both Trier source rows |

### Controlled BBSR-prefix screen

As a read-only compatibility screen, each July 2026 KBA code was compared with
the first five digits of BBSR `KRS2025`. The result was:

- 400 KBA codes inspected;
- 400 unique five-digit prefixes in the BBSR 2025 Kreis table;
- 399 prefix intersections;
- KBA-only code `06415` (`HANAU,STADT`);
- BBSR-only code `07235` (`Trier-Saarburg`);
- `07211` present in both, but BBSR `07211` is Trier city while KBA `07211` is
  the combined `TRIER-SAARBURG` registration row.

This is **not** a validated mapping-coverage estimate. It is a bounded screen that
shows why direct assignment is unsafe: it uses a five-digit pattern, not a
published KBA-to-BBSR equivalence, and it exposes the two known vintage/aggregation
exceptions.

### Mapping cases

| Case | Current evidence | Feasibility treatment |
|---|---|---|
| One KBA code to one current BBSR Kreis row | Often screen-compatible by five-digit prefix; the current KBA product does not publish a universal code-system rule | Eligible only after a dated, key-based bridge validates the KBA product geography. |
| Many BNetzA source rows to one KBA code | Trier city and Trier-Saarburg both map to KBA `07211` | Aggregate charging measures by KBA code before stock join; retain both source rows and never duplicate stock. |
| One KBA code to multiple BBSR component types | `07211` corresponds to BBSR type 1 for Trier city and type 3 for Trier-Saarburg | Use `mixed_or_unresolved`; do not force one BBSR class onto the KBA row. |
| One-to-many KBA mapping | No supported one-to-many mapping was found in the current local evidence | Do not invent one; require an official bridge or an approved allocation method. |
| Missing BBSR vintage | KBA `06415` exists in 2026, but BBSR 2025 has no Hanau row | Mark `vintage_mismatch`/unresolved until a post-2026 BBSR reference or approved bridge exists. |

## 6. Confirmed geographic exceptions

### Hanau / Main-Kinzig-Kreis

The Hessian sources used in Batch 08 establish that Hanau became a kreisfreie
Stadt on 2026-01-01. The 2026-09-30 BNetzA source has separate rows for Hanau and
Main-Kinzig-Kreis, and all three local FZ 27.15 snapshots have separate KBA rows
`06415` and `06435`.

The BBSR 2025 reference table reflects the earlier vintage: it contains
`06435000 Main-Kinzig-Kreis` with compact type 2, but no `06415000 Hanau` row.
Therefore:

1. Main-Kinzig-Kreis's 2025 type cannot simply be copied to Hanau after the
   2026 separation.
2. The existing 2026 BNetzA/KBA separation is not evidence that the BBSR 2025
   classification has already been recomputed for Hanau.
3. A future integration requires a BBSR reference at a compatible post-change
   geographic stand or an explicitly approved crosswalk/conversion method.

Relevant administrative references are the [Hessian Ministry information on
municipalities and counties](https://innen.hessen.de/kommunales/kommunen/gemeinden-und-landkreise)
and the [Hessian January 2026 administrative key directory](https://statistik.hessen.de/sites/statistik.hessen.de/files/2026-01/verz-2_26-01.pdf).

### Trier / Trier-Saarburg

The BBSR 2025 table contains two separate rows:

| Administrative row | BBSR key | BBSR four-class code | German label |
|---|---|---:|---|
| Trier, kreisfreie Stadt | `07211000` | 1 | kreisfreie Großstadt |
| Trier-Saarburg | `07235000` | 3 | ländlicher Kreis mit Verdichtungsansätzen |

KBA FZ 27.15 instead reports one July 2026 row, `07211 TRIER-SAARBURG`, with
7,869 BEVs. The stock is a combined KBA registration-region value. It is not a
Trier-city-only or Trier-Saarburg-county-only value and must not be counted twice.

The approved display label is **Trier / Trier-Saarburg (gemeinsamer
Zulassungsbezirk)**. The correct future status for the KBA-level typology is
`mixed_or_unresolved` unless an approved method can preserve both component types
without allocating the shared vehicle stock. A common registration district does
not establish identical administrative boundaries.

### Berlin, Hamburg, Bremen, and Bremerhaven

The BBSR 2025 reference and local KBA rows are separate for Berlin (`11000`),
Hamburg (`02000`), Bremen (`04011`), and Bremerhaven (`04012`). Each has compact
four-class code 1. Bremerhaven is a small kreisfreie Großstadt in the
differentiated five-class field, but it remains class 1 in the required compact
four-class field. No additional mixed treatment is indicated for these rows.

### Regional authorities and special administrative structures

The BBSR reference explicitly contains Region Hannover (`03241`), Städteregion
Aachen (`05334`), and Regionalverband Saarbrücken (`10041`) as Kreis-level rows;
each is compact type 2 in the 2025 table. The legal or statistical type wording
must remain explicit. KBA short labels such as `HANNOVER`, `AACHEN, STAEDTEREGION`,
or `SAARBRUECKEN,STADTVERB.` must not be used as name-only keys.

## 7. Integration strategies

| Strategy | Geographic correctness | Information loss | Double-counting risk | Completeness and reproducibility | Tableau usability | Mixed-type handling |
|---|---|---|---|---|---|---|
| **A. Direct BBSR type → KBA code** | Low for current evidence; fails on Hanau vintage and Trier mixed geography | High; hides administrative components | High if the 401 source rows are joined before aggregation | Simple but not defensible; depends on an undocumented code pattern | Simple filter, misleading when mixed | Cannot represent mixed/unresolved without a hidden exception |
| **B. Administrative BBSR/Destatis bridge → controlled KBA aggregation** | Highest if the bridge is authoritative and dated | Moderate; KBA detail can be retained, but category rollups need a rule | Manageable if component rows are aggregated before stock joins | Reproducible after source/effective-date validation; more complex | Usable with bridge/status fields | Can retain component types and suppress incompatible KBA rollups |
| **C. Preserve BBSR detail separately; allow only compatible aggregations** | Highest auditability and safest current behavior | Lowest; preserves KRS and Kreisregion grain | Lowest; no stock allocation is required | Most reproducible because every bridge and aggregation is explicit | Requires a separate BBSR view and quality/status filters | First-class `mixed_or_unresolved`, `vintage_mismatch`, and `not_mapped` statuses |

**Recommendation: Strategy C.** Strategy B can be a later controlled aggregation
inside that design. Strategy A is not approved for implementation.

## 8. KPI suitability

No BBSR-based KPI value was calculated. The following assesses future descriptive
analyses only.

| Candidate | Suitable grain if validated | Current KBA-grain status | Required control |
|---|---|---|---|
| Charging points by BBSR category | BBSR KRS/Kreisregion, or KBA only when every component is one compatible class | **Not ready** for blanket KBA assignment | Sum point numerators and denominators at one validated geography; retain mixed/unresolved rows. |
| Fast charging share by BBSR category | Same as charging points; calculate from counts, not averages of regional percentages | **Not ready** for mixed KBA regions | Preserve declared-power definition and BNetzA reference date. |
| High-power (≥150 kW) share by BBSR category | Same as charging points | **Not ready** for mixed KBA regions | Use the maximum declared power per point and an explicit point denominator. |
| BEV stock by BBSR category | BBSR administrative/Kreisregion grain or compatible one-to-one KBA aggregation | **Not ready** for `07211` or Hanau under the 2025 vintage | Never allocate shared Trier stock without a separately approved method; do not reuse Main-Kinzig's 2025 type for Hanau. |
| BEV per charging point by BBSR category | Compatible category grain after both source measures are aggregated | **Proposed only** | Retain the 2026-09-30 BNetzA date and actual KBA stock date; treat as descriptive, not utilization. |
| BEV stock growth by BBSR category | A fixed, compatible BBSR vintage across both KBA dates, or an approved historical conversion | **Proposed only** | Check boundary-vintage stability before comparing dates; stock change is not sales and does not establish causality. |

The current 400-code combined view can support descriptive KBA-registration-region
measures, but it cannot by itself support a four-category BBSR measure where a KBA
row contains incompatible BBSR components. The BBSR class must never be used to
imply a causal relationship between settlement structure, charging, and BEV stock.

## 9. Recommended minimal data model (not implemented)

The minimum future model should preserve source systems instead of replacing the
current Crosswalk:

### `reference.bbsr_kreis_typology` (proposed)

One row per BBSR source version and BBSR Kreis row, with at least:

- `bbsr_source_version`, `bbsr_reference_date`, and retrieval date;
- `code_system = 'BBSR_KRS2025'` or the exact published code-system name;
- `krs_code`, `krs_name`, `kreisregion_code`, and `kreisregion_name`;
- `bbsr_type_code` 1–4 and the exact German `bbsr_type_name`;
- publisher, source URL, license, and attribution text.

### `reference.kba_bbsr_compatibility` (proposed)

One row per KBA code/date and component reference, with:

- KBA code, KBA label, KBA reference date, and KBA product/worksheet;
- BBSR code, BBSR version, BBSR reference date, and component role;
- `compatibility_status`: `compatible`, `mixed_or_unresolved`,
  `vintage_mismatch`, or `not_mapped`;
- mapping method, evidence URL, effective date, and reviewer note;
- an explicit `allocation_applied` flag, which must remain false for Trier unless
  an owner-approved method exists.

### Derived reporting layer (proposed)

A future BBSR-category summary should expose source dates, geographic grain,
component count, compatibility status, and allocation status beside every measure.
It should not overwrite `kba_district_code`, `AGS`, `ARS`, `KRS`, or
`kreisregion_code` with a generic `region_id`.

## 10. Suggested validation rules

Before any approved implementation:

1. Require an exact BBSR source version, geographic reference date, publisher,
   license, and code-system label.
2. Validate one row per `(bbsr_source_version, krs_code)` and restrict the type
   code to 1, 2, 3, or 4 with matching German labels.
3. Preserve `Kreis` and `Kreisregion` as separate fields. Do not infer a
   one-to-one relationship from a shared name.
4. Require a key-based KBA bridge; reject name-only matches and document any
   five-digit prefix comparison as non-authoritative.
5. Verify KBA code uniqueness per KBA product and reference date before any join.
6. Aggregate BNetzA charging measures by KBA code before joining KBA stock; retain
   all source rows and expose source-row counts.
7. Assign a single BBSR class to a KBA code only when all mapped BBSR components
   are compatible and share the same class. Otherwise assign `mixed_or_unresolved`
   and suppress category-level rollups that require a single class.
8. Treat Hanau as `vintage_mismatch` for the 2025 BBSR table until a compatible
   post-2026 BBSR reference or approved conversion is available.
9. Treat Trier `07211` as the combined registration region labelled
   `Trier / Trier-Saarburg (gemeinsamer Zulassungsbezirk)`; join its stock once and
   never allocate it by assumption.
10. Reconcile category totals to the source-grain totals without summing repeated
    infrastructure values across KBA dates.
11. Test Berlin, Hamburg, Bremen, Bremerhaven, regional authorities, and the
    smaller-city Kreisregion groups as explicit fixtures.
12. Require the BBSR attribution and an indication of changes for any derived or
    altered extract.

## 11. Licensing and attribution

The BBSR workbook's usage sheet states **Datenlizenz Deutschland – Namensnennung
– Version 2.0** and recommends the source attribution:

> Bundesinstitut für Bau-, Stadt- und Raumforschung: Laufende Raumbeobachtung des BBSR

The [official license text](https://www.govdata.de/dl-de/by-2-0) requires the
provider name, license notice/link, and dataset URI where those details are
provided. Changes or derived work must be identified as changed. Any future
Tableau extract or public report must also retain the existing BNetzA and KBA
attributions and review combined-source redistribution terms before publication.

## 12. Tableau benefits and limitations

### Benefits

- Four classes are understandable as a dashboard filter and can support a clear
  urban/rural comparison.
- The BBSR reference table provides explicit versions, Kreisregion keys, and
  German labels rather than requiring a name-normalization heuristic.
- A separate BBSR dimension can preserve classification detail while the existing
  KBA registration-region model remains auditable.

### Limitations

- A KBA registration region is not automatically a BBSR Kreis or Kreisregion.
- The current BBSR 2025 vintage is not compatible with the 2026 Hanau boundary
  without a new reference or conversion.
- Trier must display as a combined registration region with mixed BBSR components;
  a single category color would be misleading.
- BNetzA is a published register and KBA stock dates are not contemporaneous with
  the 2026-09-30 infrastructure snapshot.
- Historical trends require a fixed typology vintage or approved Umsteigeschlüssel;
  annual BBSR revisions can change the reference dimension.

## 13. Recommendation and implementation gate

**Overall recommendation: CONDITIONAL GO.**

The BBSR four-category typology is suitable for a future analytical enrichment if
it is preserved at its official administrative/Kreisregion grain and connected to
KBA only through an explicit, dated, code-based compatibility bridge. It is not
ready for direct KBA assignment in the current project.

Implementation remains blocked by evidence/design gates, not by a need to download
the full INKAR database:

- obtain or approve a BBSR reference vintage compatible with the 2026 Hanau change;
- approve the code-system bridge between BBSR/Destatis and KBA FZ 27.15;
- approve the mixed/unresolved treatment and exact Trier display label;
- approve whether any category-level vehicle measure may use an allocation method;
- approve the proposed reference/compatibility model and validation suite;
- approve the planned BBSR KPI candidates and Tableau presentation.

## 14. Owner approvals required before implementation

The following are implementation gates for a future batch:

1. Approve the BBSR source/version and whether the 2025 reference is acceptable
   for any non-Hanau analysis.
2. Approve an authoritative, dated KBA-to-BBSR/Destatis bridge or a documented
   evidence standard that goes beyond prefix coincidence.
3. Approve `mixed_or_unresolved` and `vintage_mismatch` as visible statuses and
   the rule that unresolved rows are excluded from single-category KPI rollups.
4. Approve the treatment of Hanau and any historical/cross-source boundary-vintage
   comparison.
5. Approve any allocation method before it is used; absent that approval, the
   shared Trier stock remains one combined KBA value.
6. Approve the minimal data model, source attribution, and Tableau display behavior.

## 15. Batch 09 conclusion

The official BBSR four-category source exists and is well documented. It can add
analytical value, but the current KBA model is a registration-region model, not a
validated BBSR administrative model. The evidence supports a separate, controlled
reference layer and conditional future aggregation. It does not support direct
classification of all 400 KBA codes today.

No BBSR ingestion, database modification, Crosswalk change, KPI formula change,
stock allocation, or publication occurred in Batch 09.
