# Batch 23 web dashboard validation

## Result

`WEB_DASHBOARD_PASS`

The local two-page React/TypeScript/Vite dashboard was built from validated
Batch 19 and Batch 21 exports. The deterministic data-preparation step passed,
TypeScript passed, the production Vite build passed, and both local routes
were inspected in Chrome at:

- `http://127.0.0.1:4173/#national`
- `http://127.0.0.1:4173/#geographic`

No remote publication, upload, Tableau workbook, DuckDB write, source change,
or reference-crosswalk change was performed.

## Inputs and provenance

The preparation script reads exactly six approved CSV inputs:

| Input | Role | Rows | SHA-256 |
|---|---|---:|---|
| `national_charging_2026_09_30.csv` | Batch 19 national charging fact | 1 | `df9cd80325ec8faa7829aeb46ad3a755ff50d60c5872d97842a517af7508bf41` |
| `state_charging_2026_09_30.csv` | Batch 19 state charging fact | 16 | `df36137c44e61b0da8fb9c20e80ff6ce59abb6d2cd0891e5da9ed6daefd202e5` |
| `state_ev_charging_comparison_2026.csv` | Batch 19 pre-combined state comparison | 16 | `8c2102cc3f32221f06f8f21eebe93039a4b42070cf65eda6f18e35187f9b9d62` |
| `kba_national_stock_history.csv` | Batch 19 national KBA history | 33 | `48bc403b70954366eec1977a7e3c025b54cf69b601cd0902e4630978ff0dd024` |
| `preparation/power_band_distribution_2026_09_30.csv` | Batch 21 power-band presentation fact | 4 | `95df11bca202a77ff4fc092f8d6f2588c5f5bf821837ae976a7fb75d9a437016` |
| `preparation/equipment_status_breakdown_2026_09_30.csv` | Batch 21 status presentation fact | 2 | `35c58ab18e1c7e1e04c3893bf22f75633f26a6b186f48c9deb589f29eae1a0ff` |

The output is `web/public/data/dashboard.json`. It retains the input hashes,
source dates, validation metadata, roles, and the map provenance. The local
map is a 16-feature GeoJSON asset; its SHA-256 is
`9d5f5b14b48e262d2ce916cf7ab249f1342196e4dd0fde55a0af6132f995a54f`.

## Reconciliations

| Check | Result |
|---|---:|
| Equipment records | 117,662 |
| Declared/populated charging points | 211,253 / 211,253 |
| Normal points | 156,155 |
| Fast points | 55,098 |
| Points at least 150 kW | 40,950 |
| Points at least 350 kW | 6,950 |
| Declared equipment nominal power | 9,215.4173 MW |
| National KBA July BEV / PHEV stock | 2,365,047 / 1,226,863 |
| 16-state KBA July BEV stock | 2,362,218 |
| National history observations | 33 |
| Federal states | 16 |
| Mutually exclusive power bands | PASS |

The geographic view additionally validates all 16 state keys and uses the
pre-combined state export for the BEV/charging comparison. Hamburg's displayed
BEV penetration is 5.9735169262%; Sachsen-Anhalt's displayed fast share is
39.894319683%; NRW's displayed charging-point count is 41,536.

## Checks run

From `web/`, using Node.js 22.23.4 during local validation:

```bash
npm run check
npm run build
```

Observed results:

- `npm run check`: PASS — data preparation, 16-state validation, 33 KBA
  history observations, four power bands, and `tsc --noEmit`.
- `npm run build`: PASS — Vite production bundle generated successfully.
- Build emitted only the non-blocking Vite advisory that the ECharts bundle is
  above the default 500 kB chunk warning threshold.

## Browser QA

The local dev server rendered both routes in Chrome. The national route was
checked for KPI values, date pills, donut, history line, power-band bars and
equipment-status bars. The geographic route was checked for the local map,
highlight cards, top-10 ranking, all 16 comparison rows, data bars, BEV
penetration chart, attribution, methodology note and responsive lower-page
layout. The browser console was rechecked after the fixes and showed no
application or ECharts/map errors.

Screenshots were inspected live during browser QA but were not saved as
repository artifacts. The final deliverable is the deterministic local web
app, not a remote deployment or a screenshot-only result.

## Source and database safety

The Batch 19 export checksums and the existing DuckDB baseline remain the
inputs to the dashboard. The preparation script does not import DuckDB and
does not write source, reference, export, or database files. `node_modules/`
and `web/dist/` are ignored by Git; only the source, lockfile, deterministic
JSON, local map asset, attribution, and documentation are deliverables.
