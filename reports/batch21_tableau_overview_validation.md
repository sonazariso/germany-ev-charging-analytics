# Batch 21 — Tableau executive overview validation

**Status: DATA_PREPARATION_PASS**

This report records the deterministic presentation preparation for the approved two-page Tableau executive overview. It does not claim that a Tableau workbook was created.

## Scope and implementation capability

- Approved pages: `01 — National Summary` and `02 — Geographic View`.
- Tableau Desktop 2026.3 is installed locally, but no approved Tableau authoring MCP, computer-use bridge, `tableau` CLI or `tabcmd` executable was available to this session.
- The workbook remains **TABLEAU_WORKBOOK_NOT_YET_CREATED**. Native Desktop worksheet and dashboard instructions are in `docs/tableau-executive-overview.md`.
- No workbook XML, `.twb`, `.twbx`, extract, remote, upload or publication was created.

## Inputs and immutability

- Batch 19 export version: `batch19-tableau-exports-2026-11-03-v1`.
- Batch 19 exports checked: 9; all manifest row counts, column counts and SHA-256 values matched.
- Manifest-listed raw/reference/report fingerprints checked: 12; all matched.
- DuckDB opened read-only; SHA-256 before/after status inspection: `5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3` / `5d2dc0b3c5800499bf3d2e41fd82a899315bcb713c267572ade7dc1b4c6a66d3`.
- Existing Batch 19 CSVs, DuckDB, raw workbooks, reference crosswalks and backups were not written.

### Batch 19 export hashes

| File | SHA-256 |
|---|---|
| `bbsr_district_charging_2025_geography.csv` | `ae1f80513f071afdde2ac1fc3b885881cef296a22180769ecd09a62eb66288bc` |
| `bbsr_type_charging_2025_geography.csv` | `0f61f86cccbeb254027b8aed7ae5a29ad12a64d8cc91b6be7ee843d32d54b589` |
| `kba_national_stock_history.csv` | `48bc403b70954366eec1977a7e3c025b54cf69b601cd0902e4630978ff0dd024` |
| `kba_registration_region_ev_stock_2026.csv` | `3a9fc7f3a77390d2dfec98702812c344805af0ba7b821a031373e6803715e6c6` |
| `kba_state_ev_stock_2026.csv` | `d41bf606ff2aaeb82580555879a009d9aca0bab70167afe6db526e299609122b` |
| `national_charging_2026_09_30.csv` | `df9cd80325ec8faa7829aeb46ad3a755ff50d60c5872d97842a517af7508bf41` |
| `state_charging_2026_09_30.csv` | `df36137c44e61b0da8fb9c20e80ff6ce59abb6d2cd0891e5da9ed6daefd202e5` |
| `state_ev_charging_comparison_2026.csv` | `8c2102cc3f32221f06f8f21eebe93039a4b42070cf65eda6f18e35187f9b9d62` |
| `state_temporal_sensitivity_2026.csv` | `9ba06577ccf84c8e9465b6b87866f4b592c4671208371b53d6e59353b4f60aa0` |

## National validation

| Measure | Observed |
|---|---:|
| Equipment records | 117,662 |
| Populated charging-point slots | 211,253 |
| National July 2026 BEV stock | 2,365,047 |
| National July 2026 PHEV stock | 1,226,863 |
| National history observations | 33 (2018-07-01 to 2026-07-01) |

All requested national infrastructure measures matched: 117,662 equipment; 211,253 points; 156,155 normal points; 55,098 fast points; 40,950 points at least 150 kW; 6,950 points at least 350 kW; and 9,215.4173 MW declared nominal equipment power.

## Geographic validation

| Measure | Observed |
|---|---:|
| State records | 16 |
| Sixteen-state July 2026 BEV stock | 2,362,218 |
| National-minus-sixteen-state Sonstige BEV stock | 2,829 |
| Sixteen-state July 2026 PHEV stock | 1,225,241 |
| Most charging points | Nordrhein-Westfalen: 41,536 |
| Highest BEV penetration | Hamburg: 5.9735169262% |
| Highest fast-point share | Sachsen-Anhalt: 39.894319683% |

The state comparison remains a fixed, pre-combined 16-state fact at KBA 2026-07-01 versus BNetzA 2026-09-30. No state charging row was joined to multiple KBA dates. `Deutschland` and `Sonstige` remain outside the 16-state geographic view.

## Derived presentation contracts

### Mutually exclusive charging-power bands

| Order | Band | Points | Share |
|---:|---|---:|---:|
| 1 | Normal ≤22 kW | 156,155 | 73.9184768974% |
| 2 | Fast >22 and <150 kW | 14,148 | 6.6971829986% |
| 3 | High power ≥150 and <350 kW | 34,000 | 16.094445996% |
| 4 | Ultra-fast ≥350 kW | 6,950 | 3.289894108% |

The four bands total exactly 211,253 points. The derived rows use the national export's nested thresholds as: normal; fast minus >=150; >=150 minus >=350; and >=350.

### Published equipment status

| Order | Status | Equipment | Share |
|---:|---|---:|---:|
| 1 | In Betrieb | 117,642 | 99.9830021587% |
| 2 | In Wartung | 20 | 0.0169978413% |

The small `In Wartung` category remains visible as a labelled row; any Tableau bar axis must start at zero and must not use a truncated axis or broken scale.

## Derived output hashes

| File | SHA-256 |
|---|---|
| `data/exports/tableau/preparation/equipment_status_breakdown_2026_09_30.csv` | `35c58ab18e1c7e1e04c3893bf22f75633f26a6b186f48c9deb589f29eae1a0ff` |
| `data/exports/tableau/preparation/power_band_distribution_2026_09_30.csv` | `95df11bca202a77ff4fc092f8d6f2588c5f5bf821837ae976a7fb75d9a437016` |

## Remaining verification

- Native Tableau Desktop assembly, official geographic recognition of all 16 states, dashboard screenshots and visual clipping checks remain manual because no approved authoring bridge was available.
- The owner must save the verified workbook as a real `.twb` and optionally `.twbx`; the repository must not receive a claimed workbook path until Tableau Desktop opens and verifies it.
- No external publication was attempted or authorized.
