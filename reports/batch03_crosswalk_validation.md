# Batch 03 — BNetzA-to-KBA geographic crosswalk validation

Generated at (UTC): `2026-11-02T10:06:51.512173+00:00`

## Scope and method

- Database: `data/analytics/ev_charging.duckdb` (opened read-only).
- BNetzA charging snapshot: `2026-09-30`.
- KBA district stock snapshot: `2026-07-01`.
- Crosswalk version: `2026-07-01`.
- The script reads one row per BNetzA state/district combination and one row per KBA July district code.
- Name matching is constrained by state and administrative type. Explicit aliases are provisional and do not claim official verification.
- Charging metrics are aggregated by KBA code before KBA stock is joined. This is required because Trier city and Trier-Saarburg both use KBA code `07211`.

## Observed schema

- `core.charging_equipment`: `address_addition`, `city_name`, `commissioning_date`, `commissioning_date_raw`, `declared_point_count`, `display_name`, `district_name`, `equipment_id`, `equipment_nominal_power_kw`, `equipment_type`, `excel_row`, `house_number`, `latitude`, `longitude`, `opening_hours`, `opening_times`, `opening_weekdays`, `operator_name`, `parking_information`, `payment_methods`, `postal_code`, `site_name`, `source_id`, `state_name`, `status`, `street`
- `core.charging_point`: `connector_power_kw_single`, `connector_power_raw`, `connector_types`, `equipment_excel_row`, `equipment_id`, `evse_id`, `point_number`, `public_key`, `source_id`
- `core.kba_district_ev_stock`: `bev_cars`, `district_code`, `district_name`, `excel_row`, `passenger_cars`, `phev_cars`, `reference_date`, `source_id`, `state_name`

## Validation summary

| Check | Expected | Actual | Status | Notes |
|---|---:|---:|---|---|
| BNetzA distinct state/district combinations | 401 | 401 | PASS | — |
| Crosswalk rows preserve BNetzA combinations | 401 | 401 | PASS | One CSV row is retained per original state/district combination. |
| July KBA district rows | 400 | 400 | PASS | — |
| Mapped BNetzA combinations | 401 | 401 | PASS | Unmapped rows remain blank rather than receiving an invented code. |
| Unmapped BNetzA combinations | 0 | 0 | PASS | — |
| Distinct mapped KBA district codes | 400 | 400 | PASS | Missing KBA codes: [] |
| Multiply assigned KBA codes | {'07211': 2} | {'07211': 2} | PASS | Only the Trier/Trier-Saarburg shared registration region is intentionally duplicated. |
| Multiply assigned BNetzA combinations | 0 | 0 | PASS | — |
| Equipment assignment completeness | 0 unmapped; 0 multiply-assigned | 0 unmapped; 0 multiply-assigned | PASS | Each equipment row belongs to one retained BNetzA combination and therefore one crosswalk row. |
| Equipment rows retained | 117662 | 117662 | PASS | — |
| Charging-point slots retained | 211253 | 211253 | PASS | — |
| Declared charging points retained | 211253 | 211253 | PASS | — |
| Equipment-to-point reconciliation | 0 | 0 | PASS | The point-count query uses source_id and Excel row as the join key. |
| Trier shared registration region | Kreisfreie Stadt Trier, Landkreis Trier-Saarburg | Kreisfreie Stadt Trier, Landkreis Trier-Saarburg | PASS | Both source entries are kept and map to 07211 before aggregation. |
| KBA BEV stock after aggregate-before-join | 2362218 | 2362218 | PASS | A raw 401-row join would total 2,370,087; the aggregate join avoids the Trier duplicate. |
| Candidate alias rules locally validated | 22 | 22 | PASS | Alias rows are still provisional and require authoritative review. |

## Crosswalk output

- Output CSV: `data/reference/bnetza_kba_district_crosswalk_2026.csv`.
- Rows: `401`; mapped rows: `401`; unmapped rows: `0`.
- Distinct mapped KBA codes: `400`.

### Mapping methods

| Mapping method | Rows |
|---|---:|
| `explicit_provisional_alias` | 22 |
| `explicit_state_city_naming_convention` | 2 |
| `shared_kba_registration_region` | 2 |
| `state_and_admin_type_name_match` | 375 |

### Verification statuses

| Verification status | Rows |
|---|---:|
| `observed_local_snapshot_match` | 375 |
| `observed_local_snapshot_naming_convention` | 2 |
| `provisional_alias_requires_authoritative_review` | 22 |
| `provisional_shared_region_requires_authoritative_review` | 2 |

## Candidate aliases

These mappings are explicit local-snapshot candidates, not official administrative verification.

| BNetzA state | BNetzA district | KBA code | KBA name observed | Note |
|---|---|---:|---|---|
| Baden-Württemberg | Stadtkreis Freiburg im Breisgau | 08311 | FREIBURG I.BREISG.STADT | BNetzA uses Stadtkreis Freiburg im Breisgau; KBA uses the abbreviated city label. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Bayern | Landkreis Neustadt a.d. Aisch-Bad Windsheim | 09575 | NEUSTADT/AISCH-WINDSHEIM | KBA shortens the district name and uses a slash in the local label. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Bayern | Landkreis Wunsiedel i. Fichtelgebirge | 09479 | WUNSIEDEL I.FICHTELGEB. | KBA abbreviates both the in-name and Fichtelgebirge components. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Brandenburg | Kreisfreie Stadt Brandenburg an der Havel | 12051 | BRANDENBURG/HAVEL,STADT | KBA uses the slash form Brandenburg/Havel. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Hessen | Landkreis Kassel | 06633 | KASSEL, LAND | The state contains both Kassel city and Kassel county; the county type selects 06633. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Mecklenburg-Vorpommern | Landkreis Mecklenburgische Seenplatte | 13071 | MECKLENBURGISCHE SEENPLA | The July KBA worksheet truncates the district display name. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Niedersachsen | Kreisfreie Stadt Oldenburg (Oldb) | 03403 | OLDENBURG(OLDENB),STADT | The city and county both use Oldenburg in their labels; city type selects 03403. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Niedersachsen | Landkreis Oldenburg | 03458 | OLDENBURG(OLDENBURG) | The city and county both use Oldenburg in their labels; county type selects 03458. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Niedersachsen | Landkreis Region Hannover | 03241 | HANNOVER | BNetzA includes the administrative-type prefix; KBA reports Hannover as the district label. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Nordrhein-Westfalen | Kreis Rhein-Kreis Neuss | 05162 | NEUSS | KBA uses the shorter district label Neuss. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Nordrhein-Westfalen | Kreis Rheinisch-Bergischer Kreis | 05378 | RHEIN.-BERGISCHER KREIS | KBA abbreviates Rheinisch to Rhein. in the district label. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Nordrhein-Westfalen | Kreis Städteregion Aachen | 05334 | AACHEN, STAEDTEREGION | KBA reverses the order of Aachen and Städteregion. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Nordrhein-Westfalen | Kreisfreie Stadt Mülheim an der Ruhr | 05117 | MUELHEIM A.D.RUHR,STADT | KBA uses an abbreviated an der Ruhr form. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Rheinland-Pfalz | Kreisfreie Stadt Landau in der Pfalz | 07313 | LANDAU I.D.PFALZ,STADT | KBA abbreviates in der Pfalz. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Rheinland-Pfalz | Kreisfreie Stadt Ludwigshafen am Rhein | 07314 | LUDWIGSHAFEN A.RH.,STADT | KBA abbreviates am Rhein. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Rheinland-Pfalz | Kreisfreie Stadt Neustadt an der Weinstraße | 07316 | NEUSTADT A.D.WSTR.,STADT | KBA abbreviates an der Weinstraße. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Rheinland-Pfalz | Landkreis Altenkirchen (Westerwald) | 07132 | ALTENKIRCHEN(WESTWLD.) | KBA abbreviates Westerwald and removes the display-space before the parenthesis. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Saarland | Landkreis Regionalverband Saarbrücken | 10041 | SAARBRUECKEN,STADTVERB. | BNetzA calls the regional association a Landkreis; KBA uses the Stadtverband label. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Saarland | Landkreis Saarpfalz-Kreis | 10045 | SAAR-PFALZ-KREIS | The KBA label separates Saar and Pfalz with a hyphen. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Saarland | Landkreis St. Wendel | 10046 | SANKT WENDEL | KBA expands St. to Sankt. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Sachsen | Landkreis Sächsische Schweiz-Osterzgebirge | 14628 | SAECHS.SCHWEIZ-OSTERZGEB | KBA abbreviates both Sächsische and Osterzgebirge. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |
| Thüringen | Landkreis Saale-Holzland-Kreis | 16074 | SAALE-HOLZLANDKREIS | KBA joins Holzland and Kreis in the district label. The target state, administrative type, and KBA name were checked against the local July snapshot; authoritative boundary verification is not claimed. |

## Trier and state/city naming exceptions

| BNetzA district | KBA code | KBA name | Mapping method |
|---|---:|---|---|
| Kreisfreie Stadt Berlin | 11000 | BERLIN | `explicit_state_city_naming_convention` |
| Kreisfreie Stadt Hamburg | 02000 | HAMBURG | `explicit_state_city_naming_convention` |
| Kreisfreie Stadt Trier | 07211 | TRIER-SAARBURG | `shared_kba_registration_region` |
| Landkreis Trier-Saarburg | 07211 | TRIER-SAARBURG | `shared_kba_registration_region` |

Trier is intentionally represented by two source rows and one KBA registration-region code. Any downstream join must first aggregate charging metrics by `kba_district_code`; joining KBA stock to the raw 401-row crosswalk would duplicate code `07211`.

## Exceptions

No unmapped combinations in the observed snapshot.

## Reproducibility and boundary decisions

- Evidence URL recorded in mapped CSV rows: [https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/fz27_202607.xlsx?__blob=publicationFile&v=3](https://www.kba.de/SharedDocs/Downloads/DE/Statistik/Fahrzeuge/FZ27/fz27_202607.xlsx?__blob=publicationFile&v=3).
- No permanent DuckDB table or view was created.
- Original BNetzA/KBA source data and the original DuckDB file were not modified.
- Before database integration, decide whether the provisional aliases should be replaced or supplemented with an authoritative administrative crosswalk and whether the shared Trier registration-region treatment is suitable for the final KPI definition.
