# Batch 13.1 — Owner-approved Hanau and Main-Kinzig BBSR-like scenario

## 1. Result

**PASS.** Batch 13.1 adds a separate, reproducible 2026 analytical scenario
for the two owner-approved boundary exceptions. It preserves the official
Batch 13 BBSR 2025 baseline and does not claim that an official BBSR 2026
classification has been published for Hanau.

The scenario is explicitly labelled:

- **OFFICIAL BBSR 2025 BASELINE** — the unchanged five-row
  `analytics.charging_by_bbsr_type_2025` summary, including its two-row
  `UNCLASSIFIED` group.
- **OWNER-APPROVED 2026 ANALYTICAL SCENARIO** — a separate four-category
  charging-only summary that applies two owner overrides. Neither override is
  marked `VERIFIED_COMPATIBLE` or `official_bbsr_verification = true`.

No KBA vehicle stock, BEV/PHEV measure, Tableau object, or Trier stock
allocation was added.

## 2. Backup verification

The primary DuckDB was checked for open handles with `lsof`; no conflicting
handle or WAL was present before the copy. The pre-write database was copied
to the following ignored backup, then opened read-only and reconciled before
the write transaction:

| Item | Result |
|---|---|
| Backup | `data/backups/ev_charging_pre_batch13_1_20261102_224646.duckdb` |
| Size | 40,644,608 bytes |
| Backup SHA-256 | `8fce144f0be067757af19d03a7b81b8f604727e6e3dd4246eae2c6e47b352d58` |
| Source SHA-256 before copy | `8fce144f0be067757af19d03a7b81b8f604727e6e3dd4246eae2c6e47b352d58` |
| Backup WAL | absent |
| Read-only verification | PASS |
| Baseline counts | 117,662 equipment; 211,253 points; 401 source districts |
| Baseline power totals | 156,155 normal; 55,098 fast; 40,950 >=150 kW; 6,950 >=350 kW |
| Baseline nominal power | 9,215.4173 MW |

## 3. New objects and source files

| Artifact | Purpose | Rows/grain |
|---|---|---:|
| `data/reference/bnetza_bbsr_owner_override_2026.csv` | Versioned owner-override input | Exactly 2 BNetzA source-district rows |
| `data/reference/bnetza_bbsr_owner_override_2026_manifest.json` | Deterministic source, vintage, hash, and provenance metadata | Manifest v1 |
| `reference.bnetza_bbsr_owner_override_2026` | DuckDB copy of the override reference | 2 rows |
| `analytics.charging_by_bbsr_district_2026_scenario` | Source-grain overlay of the official Batch 13 charging view | 401 BNetzA source districts |
| `analytics.charging_by_bbsr_type_2026_scenario` | Scenario reporting view | 4 categories |
| `sql/13_1_bbsr_scenario.sql` | Transactional DDL/view definitions | New objects only |
| `scripts/13_1_deploy_bbsr_scenario.py` | Preflight, backup, deployment, and validation | Repeat-safe |

The geographic identifier is the existing Crosswalk `kba_district_code`
column (`KBA_DISTRICT_CODE` in the scenario reference), used only to identify
the two observed source rows. It is not used as proof of a BBSR boundary
equivalence.

The reference CSV SHA-256 is
`1b2e3264a0c7e950a3dbfbca9e5abad581d88158b9322481643fb0505d441aac`.
The scenario version is
`batch13.1-2026-11-02-owner-approved-hanau-main-kinzig`.

## 4. Owner-approved rows and actual charging counts

All measures below are calculated from the BNetzA source rows and the deployed
maximum-per-point declared-power parser; they are not hardcoded in the
reference file.

| Code | BNetzA source district | Analytical category | Method | Official BBSR verification | Equipment | Points | Normal | Fast | >=150 kW | >=350 kW | Declared nominal power |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| `06415` | Hessen — Kreisfreie Stadt Hanau | 1 | `OWNER_APPROVED_SCENARIO` | false | 146 | 251 | 170 | 81 | 76 | 20 | 15.313 MW |
| `06435` | Hessen — Landkreis Main-Kinzig-Kreis | 2 | `HISTORICAL_BBSR_CARRY_FORWARD` | false | 439 | 740 | 443 | 297 | 251 | 57 | 48.169 MW |
| **Total moved from official `UNCLASSIFIED`** |  |  |  |  | **585** | **991** | **613** | **378** | **327** | **77** | **63.482 MW** |

Hanau's category 1 is an owner-approved analytical assumption. It is not an
official BBSR 2025 or 2026 classification. The owner scenario documents the
population context that Hanau's municipal register reports over 107,000
residents while the Hessen April 2026 statement cites approximately 98,000
census-based residents. Those figures explain the documented boundary/context
note; they are not a population-based BBSR classification rule.

Main-Kinzig carries forward official BBSR 2025 type 2 only for this scenario,
with the explicit caveat that the BBSR 2025 row predates Hanau's separation in
2026. It is not promoted to `VERIFIED_COMPATIBLE`.

Evidence links: [Hanau in Zahlen](https://www.hanau.de/wirtschaft/profil-und-standortvorteile/hanau-in-zahlen/), [Hessen press statement](https://innen.hessen.de/presse/stadt-hanau-erhaelt-20-millionen-euro), and [Hessen municipalities and counties](https://innen.hessen.de/kommunales/kommunen/gemeinden-und-landkreise).

## 5. Four-category scenario KPIs

Shares are percentages. Fast and high-power shares use category charging
points as their denominator. National charging-point share uses all 211,253
scenario points. Declared nominal power is equipment-level nominal power, not
delivered energy.

| Code | Category | Districts | Equipment | Points | Normal | Fast | >=150 kW | >=350 kW | Fast share | High-power share | Declared nominal power (MW) | National point share |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | kreisfreie Großstadt | 68 | 39,629 | 69,458 | 56,419 | 13,039 | 9,675 | 1,194 | 18.77% | 13.93% | 2,362.9401 | 32.879060% |
| 2 | städtischer Kreis | 132 | 42,351 | 78,391 | 57,411 | 20,980 | 15,514 | 2,611 | 26.76% | 19.79% | 3,519.6180 | 37.107639% |
| 3 | ländlicher Kreis mit Verdichtungsansätzen | 98 | 18,042 | 32,342 | 21,788 | 10,554 | 7,877 | 1,446 | 32.63% | 24.36% | 1,669.6451 | 15.309605% |
| 4 | dünn besiedelter ländlicher Kreis | 103 | 17,640 | 31,062 | 20,537 | 10,525 | 7,884 | 1,699 | 33.88% | 25.38% | 1,663.2141 | 14.703697% |
| **Total** | **All 401 BNetzA source districts** | **401** | **117,662** | **211,253** | **156,155** | **55,098** | **40,950** | **6,950** | — | — | **9,215.4173** | **100.000001%*** |

Expected scenario `UNCLASSIFIED` districts: **0**. The displayed national
share total is the sum of six-decimal rounded shares; the underlying point
denominator is exactly 211,253.

## 6. Comparison with the official Batch 13 baseline

The official five-row summary remains available in
`analytics.charging_by_bbsr_type_2025` and is unchanged. The scenario moves
only the two previously unclassified rows:

| Category | Official districts | Scenario districts | District delta | Official equipment | Scenario equipment | Equipment delta | Official points | Scenario points | Point delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 67 | 68 | +1 | 39,483 | 39,629 | +146 | 69,207 | 69,458 | +251 |
| 2 | 131 | 132 | +1 | 41,912 | 42,351 | +439 | 77,651 | 78,391 | +740 |
| 3 | 98 | 98 | 0 | 18,042 | 18,042 | 0 | 32,342 | 32,342 | 0 |
| 4 | 103 | 103 | 0 | 17,640 | 17,640 | 0 | 31,062 | 31,062 | 0 |
| **Official `UNCLASSIFIED`** | **2** | **0** | **-2** | **585** | **0** | **-585** | **991** | **0** | **-991** |

The corresponding changes for category 1 are +170 normal points, +81 fast
points, +76 points >=150 kW, +20 points >=350 kW, and +15.313 MW. Category 2
changes are +443, +297, +251, +57, and +48.169 MW respectively. Categories 3
and 4 are unchanged. National totals are unchanged because this is a
reclassification of existing source rows, not a data addition.

Trier remains separate: `Kreisfreie Stadt Trier` retains official BBSR code
`07211000`, scenario category 1, and 201 points; `Landkreis Trier-Saarburg`
retains official BBSR code `07235000`, scenario category 3, and 302 points.
No KBA BEV stock is joined or allocated.

## 7. National reconciliation

| Measure | Scenario result |
|---|---:|
| Equipment | 117,662 |
| Charging points | 211,253 |
| Normal points, maximum declared power <=22 kW | 156,155 |
| Fast points, maximum declared power >22 kW | 55,098 |
| Points >=150 kW | 40,950 |
| Points >=350 kW | 6,950 |
| Unclassifiable power points | 0 |
| Declared equipment nominal power | 9,215.4173 MW |
| Source districts | 401 |
| Scenario `UNCLASSIFIED` districts | 0 |

## 8. Validation results

- Batch 13 commit `a3e3dc8` was present and the pre-change Git worktree was
  clean.
- `py_compile` passed for `scripts/13_1_deploy_bbsr_scenario.py`.
- `git diff --check` passed before handoff.
- Read-only preflight passed before the write.
- Backup checksum, size, no-WAL state, read-only opening, and baseline counts
  passed.
- The deployment transaction passed, and a second execution using the same
  verified backup passed without duplicate rows or objects.
- Independent read-only checks confirmed 2 override rows, 401 scenario
  district rows, 4 category rows, full 401/401 coverage, zero duplicates,
  zero omissions, zero scenario-unclassified districts, and deterministic
  result hashes.
- Official BBSR reference CSV, original BNetzA-to-BBSR bridge CSV, KBA
  Crosswalk CSV, raw/core tables, official Batch 13 views, KBA views, and
  state view were unchanged.
- Scenario SQL contains no KBA vehicle-stock, BEV, or PHEV reference. It
  inherits the official source-aware joins and maximum-per-point
  `connector_power_raw` parsing from the Batch 13 district view.
- No open database handles or WAL files remained after validation.
- Markdown link validation passed for repository-relative links and the three
  supplied external evidence URLs.

## 9. Documentation and private Persian reference

Updated the relevant English documentation, including the README, architecture,
data dictionary, geographic methodology, KPI catalog, analysis findings, data
quality, decisions, reproducibility guide, project status, and changelog. Added
this report and the two source reference artifacts.

Updated the private Persian KPI catalog at
`../germany-ev-charging-analytics-private/Germany_EV_Charging_KPI_Catalog_FA.md`.
That file remains outside the Git repository and is not staged or committed.

## 10. Local Git commit

The final local commit is recorded in Git history with message
`feat: add owner-approved BBSR classification scenario (Batch 13.1)`. No remote
was added, and nothing was pushed, uploaded, or published.

## 11. Remaining limitations

- Hanau category 1 remains a user-approved analytical assumption, not an
  official BBSR 2025 or 2026 classification.
- Main-Kinzig category 2 is a historical BBSR 2025 carry-forward with the
  explicit 2026 Hanau-separation caveat; it is not `VERIFIED_COMPATIBLE`.
- The BBSR 2025 geographic stand and BNetzA 2026-09-30 infrastructure snapshot
  are different vintages; the scenario is source-grain descriptive analysis.
- The BNetzA register is not exhaustive, and declared power is not utilization
  or delivered energy.
- This batch does not implement KBA–BBSR integration, vehicle-stock KPIs by
  scenario category, Tableau work, or any new source download.
