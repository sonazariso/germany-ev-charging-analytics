# Analysis findings

This document records findings supported by the current local database and validation artifacts. It separates descriptive results from exploratory comparisons and does not infer causality.

## Verified descriptive findings

### Published charging infrastructure

- The 2026-09-30 BNetzA snapshot contains 117,662 normalized equipment records and 211,253 populated charging-point slots.
- The source-declared point count reconciles exactly to the populated point-slot count. This confirms retention for the current snapshot; it does not turn the published register into a census.
- Current equipment statuses are 117,642 In Betrieb and 20 In Wartung.
- Equipment-level type labels contain 86,154 Normalladeeinrichtung rows and 31,508 Schnellladeeinrichtung rows. Point-level power bands are a separate measure.
- Declared equipment nominal power sums to 9,215.42 MW. This is nominal source power, not actual energy delivery.

### Point-level declared power

Using the retained connector-power text and classifying each point once by the maximum numeric token:

| Measure | Point slots | Share of 211,253 |
|---|---:|---:|
| Maximum declared power <=22 kW | 156,155 | 73.92% |
| Maximum declared power >22 kW | 55,098 | 26.08% |
| Maximum declared power >=150 kW | 40,950 | 19.38% |
| Maximum declared power >=350 kW | 6,950 | 3.29% |

The parser keeps semicolon-separated power entries inside the point row. It does not treat a multi-value string as multiple points or as simultaneous power.

### Registered vehicle stock

For the 400-code district table:

| KBA reference date | Passenger cars | BEVs | PHEVs | BEV share |
|---|---:|---:|---:|---:|
| 2026-01-01 | 49,436,020 | 2,031,870 | 1,121,516 | 4.11% |
| 2026-04-01 | 49,494,647 | 2,167,111 | 1,165,933 | 4.38% |
| 2026-07-01 | 49,644,855 | 2,362,218 | 1,225,241 | 4.76% |

The district BEV stock increased by 330,348, or 16.26%, from January to July. This is a stock change between snapshots, not new vehicle sales.

The state-level KBA FZ 27.2 row labelled Deutschland reports 2,365,047 BEVs and 1,226,863 plug-in hybrids on 2026-07-01. That national row is a different reporting structure from the 400 district rows and is not substituted into the district join.

### State-level descriptive patterns

- The largest point-slot counts are in Nordrhein-Westfalen (41,536), Bayern (40,215), and Baden-Württemberg (35,437).
- The largest absolute district-table BEV stock increases from January to July are in Nordrhein-Westfalen (+72,595), Bayern (+64,540), and Baden-Württemberg (+47,514).
- The highest relative BEV growth in the 400-district state aggregation is Mecklenburg-Vorpommern (+20.98%), followed by Sachsen-Anhalt (+20.08%). Berlin is lowest in this snapshot comparison (+11.35%).

These rankings describe the observed source aggregates. They do not indicate that infrastructure caused vehicle-stock changes or that a lower count means poor infrastructure.

## Geographic verification findings

- The 22 explicit aliases have direct row-level five-digit key evidence against the dated Destatis Kreis components and local KBA FZ 27.15 rows. This is not a universal KBA-to-AGS/ARS equivalence, and all 22 remain operationally provisional.
- Hanau and Main-Kinzig-Kreis are separate in the 2026-09-30 BNetzA source and in KBA FZ 27.15 on 2026-01-01, 2026-04-01, and 2026-07-01. No current 2026 coverage mismatch was measured.
- Trier remains one combined KBA registration region. The July `07211 TRIER-SAARBURG` stock is 7,869 BEVs and is counted once after the two BNetzA source rows are aggregated to KBA code.
- The 400-region model is defensible for the current KBA registration-region grain, not as proof that all 400 KBA regions are identical to administrative regions. Historical boundary compatibility remains an open note for future time series.

### BBSR feasibility

- The official BBSR 2025 reference contains 400 Kreis rows and 362 Kreisregion
  keys with compact four-class codes 1–4. Smaller independent cities can be
  grouped with associated counties, so the BBSR grain is not automatically the
  KBA registration-region grain.
- A read-only five-digit prefix screen found 399 intersections between the 400
  July 2026 KBA codes and BBSR 2025 Kreis prefixes. KBA `06415` Hanau is absent
  from the 2025 BBSR table, and BBSR `07235` Trier-Saarburg is absent from the
  KBA 400-code table. This is not a validated crosswalk.
- BBSR assigns Trier city and Trier-Saarburg different four-class types while KBA
  combines their stock under `07211`; a future KBA-level category must remain
  mixed/unresolved unless an approved method is introduced.
- Batch 10 implemented the separate BBSR reference layer with 400 Kreis rows and
  362 Kreisregion keys. It remains separate from current BBSR enrichment and does
  not directly classify KBA codes.

## Preliminary exploratory results

The data can support exploratory comparisons of state or KBA-region point-power mix, BEV stock growth, and BEVs per published point. Those comparisons remain provisional because:

- BNetzA infrastructure is dated 2026-09-30 and KBA stock is dated 2026-07-01.
- The BNetzA register is incomplete relative to every publicly accessible charger.
- The 22 aliases and two Trier rows have completed the Batch 08 evidence review, but operational promotion remains owner-controlled and the KBA-versus-AGS/ARS distinction must be retained.
- A point count is not a utilization or energy-delivery measure.
- KBA stock growth is not a sales flow.

The correct exploratory workflow aggregates charging measures to KBA code before joining vehicle stock. The two Trier source rows must not be joined independently to the one 07211 KBA stock row.

## Methodological limitations

- Current data are snapshots, not a full historical infrastructure panel.
- The published register contains source status and commissioning dates but no sessions, energy, uptime, or queue data.
- Connector-power parsing is derived from raw text; the helper column connector_power_kw_single is intentionally incomplete for multi-value strings.
- KBA worksheets contain alternative breakdowns and subtotal rows. Only the approved normalized tables are used for the current findings.
- The existing analytics.charging_by_state view is source-aware after the Batch 06 correction; any future multi-snapshot loading must retain the `(source_id, excel_row)` key.
- One source coordinate is outside a broad Germany bounding check and remains uncorrected.

## Open analytical questions

1. Which owner-approved status vocabulary should be used if any of the 22 row-level-supported aliases are promoted?
2. Should the shared Trier/Trier-Saarburg registration-region treatment be the permanent display geography for every final KPI?
3. Which historical KBA vintages and product-specific boundary notes are required before older comparisons are shown, especially after the Hanau change?
4. Should maximum-per-point power parsing become a reusable approved view or core field?
5. How should the 2,829 Sonstige BEVs and the different national passenger-car totals be presented in the final dashboard?
6. Which BBSR settlement typology, if any, would add value without replacing administrative geography?
7. Which compact Tableau extract can be published while respecting source licensing and field-level disclosure review?

## Batch 13 BBSR charging-only findings

Batch 13 deployed the approved Path A enrichment at the original BNetzA
state/district grain. The result contains 401 districts: 399 verified,
one conditional-vintage Main-Kinzig-Kreis row, and one unresolved Hanau row.
The BBSR settlement type is populated only for the 399 verified rows.

The five reporting groups reconcile to 117,662 equipment records, 211,253
charging points, 156,155 normal points, 55,098 fast points, 40,950 points at
least 150 kW, 6,950 points at least 350 kW, and 9,215.4173 MW of declared
equipment nominal power. The `UNCLASSIFIED` group contains 585 equipment rows
and 991 points. Category point shares use all registered points, including that
unclassified group.

The descriptive category results are not a KBA classification and contain no
BEV/PHEV stock. Hanau does not inherit Main-Kinzig's type; Main-Kinzig's
pre-change BBSR administrative/Kreisregion code is retained without a type.
Trier city and Trier-Saarburg remain separate source rows with types 1 and 3;
their shared KBA vehicle stock is neither joined nor allocated.
