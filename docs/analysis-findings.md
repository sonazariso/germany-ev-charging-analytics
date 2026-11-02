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

## Preliminary exploratory results

The data can support exploratory comparisons of state or KBA-region point-power mix, BEV stock growth, and BEVs per published point. Those comparisons remain provisional because:

- BNetzA infrastructure is dated 2026-09-30 and KBA stock is dated 2026-07-01.
- The BNetzA register is incomplete relative to every publicly accessible charger.
- Twenty-two aliases and both Trier rows require authoritative geographic review.
- A point count is not a utilization or energy-delivery measure.
- KBA stock growth is not a sales flow.

The correct exploratory workflow aggregates charging measures to KBA code before joining vehicle stock. The two Trier source rows must not be joined independently to the one 07211 KBA stock row.

## Methodological limitations

- Current data are snapshots, not a full historical infrastructure panel.
- The published register contains source status and commissioning dates but no sessions, energy, uptime, or queue data.
- Connector-power parsing is derived from raw text; the helper column connector_power_kw_single is intentionally incomplete for multi-value strings.
- KBA worksheets contain alternative breakdowns and subtotal rows. Only the approved normalized tables are used for the current findings.
- The existing analytics.charging_by_state view omits source_id in one point aggregation join and requires a design decision before multi-snapshot use.
- One source coordinate is outside a broad Germany bounding check and remains uncorrected.

## Open analytical questions

1. Which authoritative administrative reference should approve or replace the 22 alias rules?
2. Is the shared Trier/Trier-Saarburg registration-region treatment appropriate for every final KPI, or should a separate display geography be retained?
3. Should maximum-per-point power parsing become a reusable approved view or core field?
4. How should the 2,829 Sonstige BEVs and the different national passenger-car totals be presented in the final dashboard?
5. Which BBSR settlement typology, if any, would add value without replacing administrative geography?
6. Which compact Tableau extract can be published while respecting source licensing and field-level disclosure review?
