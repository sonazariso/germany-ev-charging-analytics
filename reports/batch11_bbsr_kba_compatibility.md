# Batch 11 — BBSR–KBA geographic compatibility and coverage audit

Review date: **2026-11-02**

Starting Git HEAD: **`3009a4b`** (`feat: add versioned BBSR reference preparation (Batch 10)`)

Scope: read-only compatibility audit; no operational BBSR-to-KBA integration.

## 1. Executive summary

Batch 11 is **PASS for the requested audit** and **NO-GO for production BBSR
classification**. All 400 KBA FZ 27.15 registration regions were audited with
the existing BNetzA source identities, the deployed DuckDB geography, and the
separate BBSR 2025 reference. No Crosswalk row, BBSR CSV row, DuckDB object, or
KPI formula was changed.

The strict non-operational audit recommendation is:

| Audit status | KBA regions | Share | Charging points | July 2026 BEVs |
|---|---:|---:|---:|---:|
| EXACT | 0 | 0.00% | 0 | 0 |
| HOMOGENEOUS_COMPOSITE | 0 | 0.00% | 0 | 0 |
| MIXED | 1 | 0.25% | 503 | 7,869 |
| VINTAGE_CONFLICT | 2 | 0.50% | 991 | 11,168 |
| UNRESOLVED | 397 | 99.25% | 209,759 | 2,343,181 |
| CONFLICTING | 0 | 0.00% | 0 | 0 |
| **Total** | **400** | **100.00%** | **211,253** | **2,362,218** |

The 397 unresolved rows are not missing from the audit. They have visible
five-digit BBSR prefix candidates in the non-operational output, but the
available sources do not publish an authoritative, dated KBA-to-BBSR bridge.
The existing KBA-to-BNetzA Crosswalk is a local source crosswalk and remains
operationally provisional where documented; it does not establish universal
KBA = AGS/ARS = BBSR equivalence.

Therefore, strict BBSR classification coverage is **0 of 400 regions, 0.00% of
charging points, and 0.00% of July BEV stock**. General KBA geography coverage
remains 400 regions, 211,253 charging points, and 2,362,218 July BEVs; that is
not BBSR classification coverage and must not be presented as a BBSR KPI.

The detailed non-operational row-level output is
[`batch11_bbsr_kba_compatibility_audit.csv`](batch11_bbsr_kba_compatibility_audit.csv).
It is an audit artifact, not a production mapping table.

## 2. Sources, identifiers, and vintages

### BBSR reference

The audit read [`data/reference/bbsr_settlement_types_2025.csv`](../data/reference/bbsr_settlement_types_2025.csv)
without modifying it. Its fields preserve the actual BBSR source concepts:

| CSV field | Source meaning | Audit use |
|---|---|---|
| `administrative_district_code` | BBSR `KRS2025` administrative Kreis key | BBSR administrative component; retained as an eight-character string |
| `administrative_district_name` | BBSR `KRS_NAME` | Component identity evidence, not a name-only join |
| `kreisregion_code` / `kreisregion_name` | BBSR `KKR2025` Kreisregion | Separate aggregation concept; never treated as a KBA code |
| `settlement_type_code` / `settlement_type_name_de` | BBSR `KTU2025` four-category typology | Candidate classification only; never written to KBA data |
| `bbsr_reference_date` | BBSR geographic stand | `2025-12-31` |

Validation found:

- 400 administrative Kreis rows;
- 362 distinct Kreisregion keys;
- 36 multi-district Kreisregion groups covering 74 component rows;
- 34 two-component groups and 2 three-component groups;
- zero duplicate administrative keys, missing required keys, or mixed-type Kreisregion groups;
- exactly four valid compact classification codes;
- type distribution: code 1 = 68, code 2 = 131, code 3 = 98, code 4 = 103.

The official source/workbook provenance and BBSR attribution are documented in
[`reports/batch10_bbsr_reference_validation.md`](batch10_bbsr_reference_validation.md)
and [`docs/data-sources.md`](../docs/data-sources.md).

### KBA and BNetzA model

The audit inspected the deployed DuckDB schema before constructing any join.
The relevant actual fields are:

| Object | Relevant fields and grain |
|---|---|
| `core.kba_district_ev_stock` | `district_code` (`VARCHAR`), `district_name`, `state_name`, `reference_date` (`DATE`), and `bev_cars`; one KBA district/date row |
| `core.charging_equipment` | `source_id`, `excel_row`, `state_name`, `district_name`, `declared_point_count`; one source equipment row |
| `core.charging_point` | `source_id`, `equipment_excel_row`; one populated charging-point slot |
| `reference.bnetza_kba_district_crosswalk_2026` | Original BNetzA district identities, KBA registration code/name, admin-type fields, mapping method, verification status, and source aggregates |
| `analytics.charging_by_kba_district_2026_09_30` | One already aggregate-before-join row per unique KBA code; `charging_point_count` is the infrastructure measure used here |
| `analytics.kba_district_charging_vs_bev_2026` | One row per unique KBA code and actual KBA stock date; infrastructure values repeat by date and are not summed across dates |

The KBA product is FZ 27.15, with 400 `district_code` values for each of:

- 2026-01-01;
- 2026-04-01;
- 2026-07-01.

The BNetzA infrastructure snapshot is 2026-09-30. These dates are retained as
separate source vintages. The KBA five-digit code is treated as a
product-specific `Zulassungsbezirk`/registration-region key. It is not silently
renamed to AGS, ARS, KRS, or Kreisregion.

### Fingerprints checked

The following fingerprints were unchanged across the read-only validation and
final review:

| Artifact | SHA-256 |
|---|---|
| `data/reference/bbsr_settlement_types_2025.csv` | `e35c57da8d8f675fa132b629e6dda43180a18e5b78b95e1e72de30069a062e65` |
| `data/reference/bnetza_kba_district_crosswalk_2026.csv` | `fdf139c5057250184358e3014267a4a4c4259749113273f6bd48206f6a64fe6a` |
| `data/analytics/ev_charging.duckdb` | `19753969b21a581fba79cd4fcff8d46cf7afa3354c27cb0bfce33db0f6ad4d43` |
| `data/raw/bbsr/raumgliederungen-referenzen-2025.xlsx` | `083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525` |
| `data/raw/bnetza/Ladesaeulenregister_BNetzA_2026-09-30.xlsx` | `1e82c1734b17e17e51092a0f9460a5e204888569fb12aa5940b30e9cdb726342` |
| `data/raw/kba/fz27_202601.xlsx` | `29ab2eaa178a1c6a3463d5cad707fee1e762241304ae6bb08c29702d6e6aea31` |
| `data/raw/kba/fz27_202604.xlsx` | `28fffaa7d2f21ede6d7f6988a717b749b759a308755c472df4d391c73a0653e7` |
| `data/raw/kba/fz27_202607.xlsx` | `d6a26702fa6f8358cc5f0e15e88c04ac6c36527be404058674138dd9571bc803` |

## 3. Methodology

The reproducible implementation is
[`scripts/11_audit_bbsr_kba_compatibility.py`](../scripts/11_audit_bbsr_kba_compatibility.py).
It:

1. reads the BBSR CSV and validates its exact header, string-code shape, required fields, four-code domain, code/label pairs, duplicate keys, source row count, Kreisregion count, and classification distribution;
2. reads the existing Crosswalk and validates its 401 source rows, 400 unique KBA codes, single intentional duplicate target `07211`, source-key coverage, and provisional statuses;
3. opens DuckDB with `read_only=True`, checks the deployed field definitions, and closes the connection in a `finally` block;
4. validates the BNetzA source geography against the original Crosswalk identities;
5. validates KBA uniqueness at `(district_code, reference_date)` and preserves all five-digit codes as strings;
6. uses the existing aggregate-before-join regional view for charging points and the combined view for one KBA code/date row, with no sum across repeated infrastructure dates;
7. investigates BBSR administrative candidates through original source identities, exact administrative identity keys where available, and a separately labelled five-digit prefix screen;
8. assigns one audit status per KBA code without writing it to DuckDB, the Crosswalk, or the BBSR CSV;
9. emits all 400 KBA rows in a deterministic, non-operational CSV and prints a deterministic JSON summary.

The five-digit prefix screen is diagnostic evidence only. A prefix intersection
does not prove equivalent geographic coverage, an administrative boundary match,
or a valid classification assignment. This is the central control that prevents
the audit from turning the 399 observed prefix intersections into a production
mapping.

### Audit status rules

| Status | Strict rule used in this audit |
|---|---|
| EXACT | Requires authoritative, dated KBA-to-BBSR evidence for one complete equivalent component. No such bridge is present in the approved input set, so the result is zero. |
| HOMOGENEOUS_COMPOSITE | Requires multiple verified KBA components, complete coverage, and the same BBSR type under an authoritative bridge. No current KBA composite meets this rule. |
| MIXED | Verified KBA components have different BBSR types. Applied to `07211`. |
| VINTAGE_CONFLICT | A documented 2025–2026 boundary change prevents direct equivalence. Applied to `06415` and `06435`. |
| UNRESOLVED | Identity/prefix evidence exists, but boundary equivalence or an authoritative KBA-to-BBSR bridge is insufficient. Applied to the other 397 regions. |
| CONFLICTING | Source evidence contradicts a proposed mapping. No separate row met this condition; Trier is preserved as the required `MIXED` case. |

The output keeps evidence type, component count, component type set, Kreisregion
membership, boundary alignment, vintage assessment, allocation requirement,
confidence limitation, and issue flags beside each status. `UNRESOLVED` does not
mean the KBA row is absent; it means a BBSR classification must not be assigned.

## 4. Compatibility classifications

The controlled prefix screen reproduces the Batch 09/10 result:

- 400 KBA codes inspected;
- 400 unique BBSR five-digit prefixes;
- 399 prefix intersections;
- KBA-only `06415` = Hanau;
- BBSR-only `07235` = Trier-Saarburg;
- KBA `07211` has a prefix candidate for Trier city (`07211000`), but the
  original source identities also establish the separate Trier-Saarburg BBSR
  component (`07235000`).

The 399 intersections remain a screening result. The existing source evidence
does not supply a universal KBA registration-region to BBSR administrative
boundary equivalence, so the normal one-component rows remain `UNRESOLVED`.

The 397 unresolved rows break down into 373 ordinary local
state/type/name-crosswalk candidates, 22 rows with the previously documented
row-level KBA/Destatis identity evidence, and 2 explicit state/city naming
convention rows. The distinction is visible in the CSV, but none of these
evidence types is promoted to `EXACT` without the missing authoritative bridge.

No permanent compatibility status was created in the operational model.

## 5. Coverage by status

The denominator is always the full current KBA model: 400 regions, 211,253
charging points, and 2,362,218 July 2026 district BEVs. Charging points are
counted once from the unique KBA-code regional view. July BEVs are counted once
from the unique `(kba_district_code, kba_reference_date)` combined view.

| Status | Regions | % of 400 | Charging points | % of 211,253 | July BEVs | % of 2,362,218 |
|---|---:|---:|---:|---:|---:|---:|
| EXACT | 0 | 0.00% | 0 | 0.000000% | 0 | 0.000000% |
| HOMOGENEOUS_COMPOSITE | 0 | 0.00% | 0 | 0.000000% | 0 | 0.000000% |
| MIXED | 1 | 0.25% | 503 | 0.238103% | 7,869 | 0.333119% |
| VINTAGE_CONFLICT | 2 | 0.50% | 991 | 0.469106% | 11,168 | 0.472776% |
| UNRESOLVED | 397 | 99.25% | 209,759 | 99.292791% | 2,343,181 | 99.194105% |
| CONFLICTING | 0 | 0.00% | 0 | 0.000000% | 0 | 0.000000% |
| **Total** | **400** | **100.00%** | **211,253** | **100.000000%** | **2,362,218** | **100.000000%** |

### Charging-point coverage

The 211,253 point denominator reconciles to both the populated
`core.charging_point` rows and the deployed KBA-code regional view. The Trier
region contributes 503 points after the two original BNetzA source identities
are aggregated to KBA code `07211`. No point total is added once per KBA stock
date.

The only nonzero caution-status charging coverage is 503 points for the mixed
Trier region and 991 points for the two Hanau/Main-Kinzig vintage-conflict
regions. The remaining 209,759 points belong to unresolved BBSR assignment
candidates, not to a verified BBSR category.

### BEV-stock coverage

The July denominator of 2,362,218 reconciles to the 400 KBA district rows. The
combined view contains exactly 1,200 rows (400 codes × 3 dates) and exactly one
July row for Trier code `07211`. The 7,869 Trier BEVs are not split between the
two BBSR components. The same no-allocation rule applies to all status results;
the coverage table reports KBA-region stock, not an estimated BBSR component
stock.

## 6. Hanau and Main-Kinzig-Kreis

### Evidence

The BBSR 2025 reference contains:

- no `06415000` Hanau row;
- `06435000 Main-Kinzig-Kreis`, compact type 2 (`städtischer Kreis`).

The local BNetzA 2026-09-30 source and all three local KBA FZ 27.15 snapshots
contain separate source/registration rows:

| KBA code | Region | Jan 2026 BEVs | Apr 2026 BEVs | Jul 2026 BEVs | Charging points |
|---|---|---:|---:|---:|---:|
| `06415` | Hanau, Stadt | 2,022 | 2,215 | 2,394 | 251 |
| `06435` | Main-Kinzig-Kreis | 7,483 | 8,034 | 8,774 | 740 |

The separation is effective 2026-01-01. The BBSR geographic stand is
2025-12-31, so its Main-Kinzig type predates the separation and its table has no
current Hanau component. Both KBA rows are therefore `VINTAGE_CONFLICT` in this
audit.

### District-level implication

The current KBA and BNetzA products support separate descriptive district-level
comparisons for Hanau and Main-Kinzig-Kreis, with source dates shown. They do
not support assigning a BBSR category to the current KBA rows from the 2025
reference. In particular, Main-Kinzig's type 2 must not be copied to Hanau, and
the pre-change type 2 must not be silently treated as exact for the current
post-change Main-Kinzig remainder.

### Historical-comparability implication

The local project contains only the three 2026 KBA FZ 27.15 snapshots. It cannot
measure the size or direction of a pre-2026 historical discontinuity. Any older
series that placed Hanau inside Main-Kinzig-Kreis would not be directly
comparable to the current split without product-specific historical KBA and BBSR
evidence. No stock or classification is estimated here.

## 7. Trier and Trier-Saarburg

The BBSR rows are separate:

| BBSR administrative row | BBSR code | Type |
|---|---|---:|
| Trier, kreisfreie Stadt | `07211000` | 1 — kreisfreie Großstadt |
| Trier-Saarburg | `07235000` | 3 — ländlicher Kreis mit Verdichtungsansätzen |

KBA FZ 27.15 reports one registration-region row, `07211 TRIER-SAARBURG`:

| KBA stock date | Combined KBA BEVs |
|---|---:|
| 2026-01-01 | 6,799 |
| 2026-04-01 | 7,250 |
| 2026-07-01 | **7,869** |

The BNetzA source identities contributing to the same KBA code contain 201
charging points for Trier city and 302 for Trier-Saarburg, aggregated to 503.
The KBA stock remains one combined value. The audit status is **MIXED** because
the verified BBSR components have types 1 and 3; no single BBSR category is
applied and no BEV stock is allocated.

The established display label remains:

> Trier / Trier-Saarburg (gemeinsamer Zulassungsbezirk)

This label describes the KBA registration region. It must not be interpreted as
an administrative BBSR Kreis, a Kreisregion, or a city/county allocation.

## 8. Kreisregion consistency and relationship audit

All 36 multi-district BBSR Kreisregion groups were inspected. They contain 74
administrative BBSR rows: 34 groups have two components and 2 groups have three.
Every group has one compact BBSR type across its components; no mixed BBSR type
was observed inside a BBSR Kreisregion in this vintage.

This does **not** make a Kreisregion a KBA region. The relationship is generally
one BBSR Kreisregion to multiple BBSR administrative Kreis rows, while the
current KBA product keeps those registration codes as separate rows. Examples:

| Kreisregion | BBSR type | Component KRS rows |
|---|---:|---|
| `01059000` Schleswig-Flensburg/Flensburg | 4 | `01001000` Flensburg; `01059000` Schleswig-Flensburg |
| `03251000` Diepholz/Delmenhorst | 3 | `03251000` Diepholz; `03401000` Delmenhorst |
| `07338000` Rhein-Pfalz-Kreis/Frankenthal/Speyer | 2 | `07311000` Frankenthal; `07318000` Speyer; `07338000` Rhein-Pfalz-Kreis |
| `07340000` Südwestpfalz/Pirmasens/Zweibrücken | 4 | `07317000` Pirmasens; `07320000` Zweibrücken; `07340000` Südwestpfalz |
| `09274000` Kreis u. Stadt Landshut | 3 | `09261000` Landshut city; `09274000` Landshut county |
| `12069000` Potsdam-Mittelmark/Brandenburg an der Havel | 4 | `12051000` Brandenburg; `12069000` Potsdam-Mittelmark |
| `16071000` Weimarer Land/Weimar | 2 | `16055000` Weimar; `16071000` Weimarer Land |
| `16076000` Greiz/Gera | 2 | `16052000` Gera; `16076000` Greiz |

The full row-level component and Kreisregion fields are retained in the audit
CSV. These relationships are evidence that BBSR `Kreisregion` and KBA
`Zulassungsbezirk` are different grains; they are not permission to aggregate
KBA stock or infrastructure into BBSR categories.

The important many-to-one relationship in the current operational model is
KBA `07211`: two BNetzA source identities and two separate BBSR administrative
identities contribute to one KBA registration-region code. It is not a BBSR
Kreisregion group. No supported one-to-many KBA-to-BBSR bridge was found.

## 9. Unresolved and conflicting regions

All 397 unresolved regions are explicitly present in the audit CSV with their
KBA code, KBA label, BNetzA source identity, candidate BBSR code/name/type when
available, Kreisregion membership, source-vintage assessment, and issue flags.
No unresolved region is dropped from the coverage denominator.

The unresolved condition is primarily the absence of a published, dated
KBA-to-BBSR equivalence. It is not a claim that every candidate is wrong. It is
the correct non-operational result when the available evidence cannot prove
equivalent boundaries.

There are zero separate `CONFLICTING` rows. The known Trier contradiction
between a simple prefix candidate and the two verified source components is
represented by the required `MIXED` status, preserving both component types.

## 10. Risks of excluding incompatible regions

Excluding the 397 unresolved regions from a future BBSR analysis would exclude
99.25% of KBA regions, 99.29% of charging points, and 99.19% of July BEVs. That
would leave a small, non-representative subset dominated by known exceptions
and would not be a national settlement-type KPI.

Including them by assigning a prefix-derived class would create a different
risk: it would turn an unverified product-specific registration geography into
an administrative BBSR classification, hide the Hanau boundary break, and
misstate the combined Trier row. Neither treatment is approved.

## 11. Recommended future data model

The safest next design remains a separate, versioned model rather than a change
to the operational Crosswalk:

1. Preserve a BBSR typology dimension at one row per BBSR source version and
   `KRS2025` administrative row, including source URL, publisher, license,
   reference date, exact code-system label, and `KKR2025` fields.
2. Add a future compatibility relation only after owner approval and an
   authoritative dated bridge. It should retain KBA product/date/code/label,
   BBSR KRS code/name/type, component role, evidence URL, effective date,
   compatibility status, and an explicit `allocation_applied` flag.
3. Keep `Kreis`, `Kreisregion`, `Zulassungsbezirk`, `AGS`, and `ARS` in separate
   named fields. Do not replace them with a generic `region_id`.
4. Keep `MIXED`, `VINTAGE_CONFLICT`, `UNRESOLVED`, and any future
   `CONFLICTING` rows visible. Suppress only the category rollups that require
   a single unsupported class.
5. Aggregate BNetzA charging measures to unique KBA code before joining KBA
   stock. Never allocate Trier stock without an independently approved method.

This model is recommended only; it is not implemented by Batch 11.

## 12. Limitations for Tableau reporting

- Do not add a BBSR urban/rural filter or category KPI to the current Tableau
  layer.
- The 2025 BBSR CSV may be shown as a separate reference artifact, but it must
  not be joined to KBA rows through the prefix candidate fields.
- If the audit is exposed for internal review, label it
  `NON_OPERATIONAL_BBSR_KBA_COMPATIBILITY_AUDIT` and show source vintages and
  issue flags beside every row.
- Do not present the coverage table as a production BBSR KPI; it is an audit of
  whether such a KPI could be supported.
- Preserve the current KBA label
  `Trier / Trier-Saarburg (gemeinsamer Zulassungsbezirk)` and keep its 7,869
  July BEVs and 503 points at combined KBA-registration-region grain.
- Any future category comparison needs a compatible post-change BBSR vintage
  or owner-approved conversion for Hanau/Main-Kinzig, plus a defensible
  treatment of shared Trier stock.

No formula or denominator in [`docs/kpi-catalog.md`](../docs/kpi-catalog.md) was
rewritten or promoted by this audit.

## 13. Decisions requiring owner approval

Before production geographic integration, the owner must approve:

- an authoritative, dated KBA-to-BBSR compatibility bridge and its code-system
  semantics;
- whether the 2025 BBSR vintage may be used for any 2026 KBA comparison;
- the Hanau/Main-Kinzig treatment after the 2026-01-01 boundary change;
- continued exclusion of shared Trier stock from single-category rollups unless
  an independently supported allocation method is approved;
- whether any `EXACT` or `HOMOGENEOUS_COMPOSITE` promotion is allowed after new
  evidence is supplied;
- any BBSR category KPI, Tableau enrichment, or public reporting.

BBSR-to-KBA integration is **NOT IMPLEMENTED**.

## 14. Validation and reproducibility

Commands run from the project root:

```text
.venv/bin/python -m py_compile scripts/11_audit_bbsr_kba_compatibility.py
.venv/bin/python scripts/11_audit_bbsr_kba_compatibility.py
```

Validation results:

| Check | Result |
|---|---:|
| Python syntax check | PASS |
| DuckDB opened read-only | PASS |
| DuckDB schemas and actual field types inspected | PASS |
| Equipment rows / charging points / declared points | 117,662 / 211,253 / 211,253 |
| Crosswalk rows / unique KBA codes | 401 / 400 |
| KBA district rows / unique codes per date | 1,200 / 400 |
| Combined region/date rows | 1,200 |
| July BEV total | 2,362,218 |
| BBSR rows / Kreisregion keys | 400 / 362 |
| BBSR type codes and distribution | 1–4 / 68-131-98-103 |
| Audit rows / duplicate audit keys | 400 / 0 |
| Coverage totals reconcile | PASS |
| Trier stock duplication check | PASS; 7,869 once in July |
| Deterministic repeat | PASS; two consecutive outputs identical |
| Existing source/database fingerprints | PASS; unchanged |

The script does not install dependencies, download sources, create a DuckDB
table, create a permanent bridge, modify a source CSV, or access a Git remote.

## 15. Recommended next Batch

The recommended next stage is **Batch 12 — authoritative bridge and vintage
decision**, subject to explicit owner approval before implementation. It should
first obtain or validate a dated product-specific KBA-to-administrative/BBSR
reference, then decide whether a compatible post-2026 BBSR vintage is required.
It must retain the current source keys, mixed and vintage-conflict statuses, and
aggregate-before-join rule. Only after that approval should a separate bridge or
reporting layer be designed; no production BBSR category KPI should begin from
the Batch 11 prefix candidates.
