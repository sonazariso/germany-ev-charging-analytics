# Batch 13.2 — Hanau geographic correction and BBSR classification audit

Status: **PASS**. The full evidence and deployment record is in
[`batch13_2_hanau_geographic_harmonization.md`](batch13_2_hanau_geographic_harmonization.md).

## Result

The BBSR 68-versus-67 discrepancy is resolved by two independent findings:

1. BNetzA `Kreisfreie Stadt Kassel` was incorrectly matched by the preserved
   Batch 13 bridge to BBSR `06633000 Kassel` (county, type 2). The BBSR raw
   `SLK2025` field and semantic alias audit identify `06611000 Kassel,
   documenta-Stadt` as the city row (type 1). This correction is applied only
   in Batch 13.2.
2. Hanau is the genuine vintage difference: it is current in BNetzA 2026 but
   absent from the BBSR 2025 geographic stand. `Kreis` versus `Kreisregion`
   does not explain the missing type-1 row; 36 multi-district groups are
   compact-type homogeneous and type 1 has no duplicated group.

The strict anti-join is BBSR-only `06611000 Kassel, documenta-Stadt` versus
BNetzA-only `Kreisfreie Stadt Kassel` and `Kreisfreie Stadt Hanau`. After
semantic alias normalization, only Hanau remains unmatched.

## Hanau methodology

The official Hessian boundary law makes Hanau independent and removes it from
Main-Kinzig-Kreis effective `2026-01-01`, and lists the remaining Main-Kinzig
municipalities. The defensible historical method is therefore to aggregate
current Hanau and the remaining Main-Kinzig source row to historical BBSR
`06435000 Main-Kinzig-Kreis`, then apply its actual BBSR 2025 type 2. This is a
historical target-unit result, **not an official 2026 Hanau BBSR type**.

Official population series are context only: census-based Hessian population
and the Hanau municipal register use different statistical concepts. They are
not substituted for the BBSR `KTU2025` classification or its `bev25` reference
population field. The BBSR `06435000` row records `SLK2025=2`, `KTU2025=2`, and
`bev25=421,175`; the published compact type is used directly.

Evidence: [Hessian boundary law](https://starweb.hessen.de/cache/DRS/21/9/01419.pdf),
[Hessen Interior Ministry](https://innen.hessen.de/kommunales/kommunen/gemeinden-und-landkreise),
[Hessian population table](https://statistik.hessen.de/sites/statistik.hessen.de/files/2025-11/ai2_aii_aiii_av_25-1hj.pdf),
and [Hanau official statistics](https://relaunch2018.hanau.de/wirtschaft/profil-und-standortvorteile/hanau-in-zahlen/index.html).

## Deployed harmonized result

New objects:

- `reference.bnetza_bbsr_historical_harmonization_2025` — 401 source components.
- `analytics.charging_by_bbsr_district_2025_harmonized` — 400 historical target units.
- `analytics.charging_by_bbsr_type_2025_harmonized` — four historical BBSR types.

Target type counts are `68 / 131 / 98 / 103`; source component counts are
`68 / 132 / 98 / 103` because Hanau and remaining Main-Kinzig are two current
components of one historical type-2 target.

| Layer | Type 1 | Type 2 | Type 3 | Type 4 | Unclassified |
|---|---:|---:|---:|---:|---:|
| Official Batch 13 | 39,483 / 69,207 pts | 41,912 / 77,651 pts | 18,042 / 32,342 pts | 17,640 / 31,062 pts | 585 / 991 pts |
| Batch 13.1 owner scenario | 39,629 / 69,458 pts | 42,351 / 78,391 pts | 18,042 / 32,342 pts | 17,640 / 31,062 pts | 0 |
| Batch 13.2 historical | 39,789 / 69,863 pts | 42,191 / 77,986 pts | 18,042 / 32,342 pts | 17,640 / 31,062 pts | 0 |

Each cell is equipment / charging points. Batch 13.2 retains the official and
owner-scenario views for side-by-side comparison. The Hanau/Main-Kinzig target
is 146 + 439 = 585 equipment and 251 + 740 = 991 points.

All layers reconcile to 117,662 equipment, 211,253 points, 156,155 normal,
55,098 fast, 40,950 points >=150 kW, 6,950 points >=350 kW, and approximately
9,215.4173 MW nominal equipment power. No KBA stock, Crosswalk, Trier
allocation, raw source, or existing Batch 13/13.1 object changed.

## Backup and validation

The verified pre-write backup is
`data/backups/ev_charging_pre_batch13_2_20261102_231615.duckdb`, SHA-256
`9a6d936349316a8cb451c3cb9f1ed3ddb7c1fb16a61582ed40aa397089a1a52e`.
Read-only preflight, transactional deployment, protected-object snapshots, and
a repeat-safe deployment using that backup all passed. The private Persian KPI
reference was updated outside the Git worktree.
