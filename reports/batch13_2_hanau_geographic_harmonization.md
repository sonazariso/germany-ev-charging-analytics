# Batch 13.2 — Hanau historical BBSR geography harmonization

Status: **PASS — deployed, repeat-safe, and independently validated locally**
Deployment date: `2026-11-02`
Infrastructure source: BNetzA register, reference date `2026-09-30`
Historical geographic reference: BBSR `Raumgliederungen-Referenzen 2025`, geographic stand `2025-12-31`

## Decision and scope

Batch 13.2 adds a new, versioned historical harmonization layer. It does not
change the official Batch 13 BBSR baseline, the owner-approved Batch 13.1
scenario, the existing BNetzA-to-KBA Crosswalk, raw/core data, or any KBA
analytics object.

The deployed layer answers this narrower question:

> What do the BNetzA `2026-09-30` charging records look like when the current
> Hanau and remaining Main-Kinzig source rows are aggregated to the BBSR
> `2025-12-31` historical administrative target, while correcting the Kassel
> city/county join error?

This is a historical BBSR 2025 target-unit analysis. It does **not** claim an
official 2026 BBSR type for Hanau.

## Independent explanation of the 68-versus-67 discrepancy

The official BBSR CSV contains 400 administrative `Kreis` rows with compact
type counts `68 / 131 / 98 / 103` for types `1 / 2 / 3 / 4`. The BNetzA source
contains 401 current state/district combinations. The original Batch 13
bridge has 399 typed rows plus two unclassified rows.

The audit was run in both directions and at two normalization levels:

| Audit | BBSR-only | BNetzA-only | Interpretation |
|---|---|---|---|
| Strict state + administrative form + normalized name | `06611000 Kassel, documenta-Stadt` | `Kreisfreie Stadt Kassel`; `Kreisfreie Stadt Hanau` | Kassel is a label/alias mismatch; Hanau is a genuine vintage difference |
| Semantic alias normalization | none | `Kreisfreie Stadt Hanau` | Kassel reconciles to the same city; only Hanau is absent from the BBSR 2025 stand |

The existing Batch 13 join made the independent-city Kassel source row match
BBSR `06633000 Kassel` (type 2), the county row, because the candidate logic
accepted the plain `Kassel` county row and did not recognize the official BBSR
city label `Kassel, documenta-Stadt`. The local KBA Crosswalk confirms the
source distinction (`06611` city versus `06633` county), but the Crosswalk is
not used as BBSR assignment proof. Batch 13.2 corrects this only in its new
layer: city Kassel → BBSR `06611000`, type 1; county Kassel → `06633000`, type 2.

The `Kreis` versus `Kreisregion` distinction changes the grain and can reduce
row counts when multiple administrative districts share a Kreisregion. It does
not explain this discrepancy: the BBSR reference has 36 multi-district
Kreisregion groups, all are homogeneous in compact type, and type 1 has no
duplicated Kreisregion group. The missing type-1 row is the Kassel identity
error; the extra current BNetzA unit is Hanau after a boundary change.

## Official Hanau boundary evidence

The official Hessian law declares Hanau an independent city and removes it from
Main-Kinzig-Kreis effective `2026-01-01`. The same law lists the remaining
Main-Kinzig towns and municipalities after the separation, so the historical
pre-change district is reconstructed as the union of the Hanau component and
the remaining Main-Kinzig component. The Hessian Interior Ministry describes
the same effective date and two resulting independent public bodies; Hanau's
official page records approval of the boundary-change contract.

- [Hessian Hanau boundary law (PDF)](https://starweb.hessen.de/cache/DRS/21/9/01419.pdf)
- [Hessian Interior Ministry — municipalities and districts](https://innen.hessen.de/kommunales/kommunen/gemeinden-und-landkreise)
- [Hessian Interior Ministry — Hanau separation law](https://innen.hessen.de/presse/gesetz-ueber-die-ausgliederung-hanaus-aus-dem-main-kinzig-kreis-beschlossen)
- [Hanau official boundary-change page](https://www.hanau.de/rathaus/politik/kreisfreiheit/149702.html)

The BBSR 2025 workbook retains `06435000 Main-Kinzig-Kreis` as compact type 2
and has no separate Hanau row. Its raw `Kreisreferenz` row records
`SLK2025=2` (`Landkreis`), `KTU2025=2`, and `bev25=421,175`; the published
`KTU2025`/`KTU_NAME` value is used as the classification rather than
recomputed from population. The raw workbook's `bev25` field is labelled
`Einwohner 2025`. The workbook usage notes identify the administrative basis as
the Destatis GV-ISys and the geographic stand as `31.12.2025`.

Population evidence is documented for vintage context only, not as a new
classification rule. The official Hessian population table reports Hanau at
97,956 on `2025-01-01` and 98,299 on `2025-06-30`; Hanau's municipal register
reports 107,041 main-residence records on `2025-12-31`. These figures are
different statistical concepts and are not substituted for the BBSR type.

- [Hessian Statistics population table, 1 January / 30 June 2025](https://statistik.hessen.de/sites/statistik.hessen.de/files/2025-11/ai2_aii_aiii_av_25-1hj.pdf)
- [Hanau in Zahlen — official municipal statistics](https://relaunch2018.hanau.de/wirtschaft/profil-und-standortvorteile/hanau-in-zahlen/index.html)
- [BBSR official reference-download page](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/downloads/download-referenzen.html)
- [BBSR official district/Kreis reference page](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/deutschland/kreise/Kreise_Kreisregionen/Kreise.html)
- [BBSR official settlement-structural district types](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/deutschland/kreise/siedlungsstrukturelle-kreistypen/kreistypen.html)

## Historical harmonization rule

The new reference table contains one row per current BNetzA source component.
It maps:

- `Hessen | Kreisfreie Stadt Hanau` → historical BBSR `06435000 Main-Kinzig-Kreis`, type 2, role `HISTORICAL_COMPONENT_HANAU`.
- `Hessen | Landkreis Main-Kinzig-Kreis` → the same historical target, type 2, role `HISTORICAL_COMPONENT_REMAINING_MKK`.
- `Hessen | Kreisfreie Stadt Kassel` → BBSR `06611000 Kassel, documenta-Stadt`, type 1, using the raw BBSR `SLK2025` city form and a documented semantic alias correction.
- `Hessen | Landkreis Kassel` → BBSR `06633000 Kassel`, type 2.
- All other source rows → one unique BBSR 2025 administrative identity after state, administrative form, and semantic-name normalization.

The historical target view aggregates Hanau plus the remaining Main-Kinzig
source row into one target unit. Source component names, component count,
mapping method, boundary status, BNetzA date, BBSR date, and evidence notes
remain visible. Original 2026 source-grain data is not rewritten.

## Deployed objects and reference artifacts

| Object/artifact | Purpose | Result |
|---|---|---:|
| `reference.bnetza_bbsr_historical_harmonization_2025` | Versioned 2026-source → historical BBSR target mapping | 401 source rows |
| `analytics.charging_by_bbsr_district_2025_harmonized` | Historical BBSR target-unit charging view | 400 rows |
| `analytics.charging_by_bbsr_type_2025_harmonized` | Four-category historical summary | 4 rows |
| `data/reference/bnetza_bbsr_historical_harmonization_2025.csv` | Reproducible mapping reference | 401 rows |
| `data/reference/bnetza_bbsr_historical_harmonization_2025_manifest.json` | Hashes, anti-join audit, evidence, scope controls | written |

The BBSR derived CSV SHA-256 remains
`e35c57da8d8f675fa132b629e6dda43180a18e5b78b95e1e72de30069a062e65`; the raw
workbook SHA-256 remains
`083f7740c3cf2d858c79482e63ca6c7e4680248c5bd6e207ebc9df6ede953525`.

## KPI comparison

The following rows compare the official Batch 13 baseline, the Batch 13.1
owner-approved scenario, and the Batch 13.2 historical harmonization. All
layers use the same BNetzA equipment and point measures and the same
maximum-per-point parser over `connector_power_raw`.

| Layer | Category | District/target count | Source components | Equipment | Points | Normal | Fast | >=150 kW | >=350 kW | Nominal MW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Batch 13 official | 1 | 67 | 67 | 39,483 | 69,207 | 56,249 | 12,958 | 9,599 | 1,174 | 2,347.6271 |
| Batch 13 official | 2 | 131 | 131 | 41,912 | 77,651 | 56,968 | 20,683 | 15,263 | 2,554 | 3,471.4490 |
| Batch 13 official | 3 | 98 | 98 | 18,042 | 32,342 | 21,788 | 10,554 | 7,877 | 1,446 | 1,669.6451 |
| Batch 13 official | 4 | 103 | 103 | 17,640 | 31,062 | 20,537 | 10,525 | 7,884 | 1,699 | 1,663.2141 |
| Batch 13 official | UNCLASSIFIED | 2 | 2 | 585 | 991 | 613 | 378 | 327 | 77 | 63.4820 |
| Batch 13.1 owner scenario | 1 | 68 | 68 | 39,629 | 69,458 | 56,419 | 13,039 | 9,675 | 1,194 | 2,362.9401 |
| Batch 13.1 owner scenario | 2 | 132 | 132 | 42,351 | 78,391 | 57,411 | 20,980 | 15,514 | 2,611 | 3,519.6180 |
| Batch 13.1 owner scenario | 3 | 98 | 98 | 18,042 | 32,342 | 21,788 | 10,554 | 7,877 | 1,446 | 1,669.6451 |
| Batch 13.1 owner scenario | 4 | 103 | 103 | 17,640 | 31,062 | 20,537 | 10,525 | 7,884 | 1,699 | 1,663.2141 |
| Batch 13.2 historical | 1 | 68 | 68 | 39,789 | 69,863 | 56,761 | 13,102 | 9,693 | 1,178 | 2,373.0481 |
| Batch 13.2 historical | 2 | 131 | 132 | 42,191 | 77,986 | 57,069 | 20,917 | 15,496 | 2,627 | 3,509.5100 |
| Batch 13.2 historical | 3 | 98 | 98 | 18,042 | 32,342 | 21,788 | 10,554 | 7,877 | 1,446 | 1,669.6451 |
| Batch 13.2 historical | 4 | 103 | 103 | 17,640 | 31,062 | 20,537 | 10,525 | 7,884 | 1,699 | 1,663.2141 |

The official baseline and the owner scenario remain available for direct
comparison. The harmonized type-2 summary has 131 historical target units but
132 current source components because Hanau and the remaining Main-Kinzig row
are intentionally aggregated into one historical BBSR target.

### Hanau/Main-Kinzig and Kassel checks

| Target/source | Equipment | Points | Normal | Fast | >=150 kW | >=350 kW | Nominal MW |
|---|---:|---:|---:|---:|---:|---:|---:|
| Historical BBSR `06435000 Main-Kinzig-Kreis` = Hanau + remaining MKK | 585 | 991 | 613 | 378 | 327 | 77 | 63.4820 |
| BBSR `06611000 Kassel, documenta-Stadt` = Kreisfreie Stadt Kassel | 306 | 656 | 512 | 144 | 94 | 4 | 25.4210 |
| BBSR `06633000 Kassel` = Landkreis Kassel | 340 | 673 | 437 | 236 | 182 | 22 | 35.6064 |

## National reconciliation

The harmonized district view reconciles exactly to the source baseline:

| Measure | Harmonized total |
|---|---:|
| Equipment | 117,662 |
| Charging points | 211,253 |
| Normal points | 156,155 |
| Fast points | 55,098 |
| Points >=150 kW | 40,950 |
| Points >=350 kW | 6,950 |
| Unclassifiable power points | 0 |
| Declared equipment nominal power | 9,215.4173 MW |
| Current BNetzA source components | 401 |
| Historical BBSR target units | 400 |

Normal + fast + unclassifiable equals all points. The type summary has no
unclassified target row; its point-share denominator remains all 211,253
registered charging points.

## Validation and backup evidence

The deployment script performed:

1. raw/derived BBSR checksum and schema checks;
2. independent strict and semantic bidirectional anti-joins;
3. raw BBSR `SLK2025` city/county-form validation;
4. BNetzA source row, equipment, point, key, orphan, and power-band checks;
5. SQL section and forbidden KBA/BEV/PHEV-reference checks;
6. read-only snapshots of the official Batch 13, Batch 13.1, Crosswalk, KBA,
   and state objects;
7. timestamped backup creation and read-only backup validation;
8. one transactional write followed by read-only post-deployment validation;
9. a repeat-safe deployment using the first verified backup.

The pre-write backup is ignored by Git and stored at:

`data/backups/ev_charging_pre_batch13_2_20261102_231615.duckdb`

Its SHA-256 is
`9a6d936349316a8cb451c3cb9f1ed3ddb7c1fb16a61582ed40aa397089a1a52e`.

Commands used:

```text
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py --build-reference-only --json
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py --dry-run --json
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py --json
.venv/bin/python scripts/13_2_deploy_hanau_geographic_harmonization.py --backup-path data/backups/ev_charging_pre_batch13_2_20261102_231615.duckdb --json
```

The existing official and scenario objects, KBA objects, Crosswalk, raw data,
and KBA vehicle stock remain unchanged. No remote, upload, Tableau enrichment,
KBA stock join, or Trier stock allocation was performed.

## Remaining limitations

- This is a historical BBSR 2025 target reconstruction, not an official 2026
  Hanau BBSR classification.
- The exact Hanau-plus-remaining-Main-Kinzig union is supported by the official
  2026 legal boundary definition; BBSR's 2025 typology remains the applied
  target classification.
- Population values are contextual evidence and are not substituted into the
  BBSR type rule.
- The BNetzA register is not an exhaustive measure of all charging
  infrastructure, and declared power is not utilization or energy delivery.
- This layer is charging-only and remains separate from KBA registration
  regions and vehicle-stock KPIs.
