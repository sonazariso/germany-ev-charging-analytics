# Germany EV Charging Analytics — web dashboard

This is the Batch 23 React/TypeScript/Vite implementation of the approved two-page executive overview:

- `#national` — National Summary
- `#geographic` — Geographic View

## Run locally

```bash
npm install
npm run dev
```

The app serves the compact frontend bundle under `public/data/`. To rebuild it
from the approved repository exports:

```bash
npm run prepare:data
npm run check
npm run build
npm run preview
```

Run `npm run preview` after `npm run build` to serve the production bundle
locally for a final browser check.

`prepare:data` reads only these validated inputs:

- `data/exports/tableau/national_charging_2026_09_30.csv`
- `data/exports/tableau/state_charging_2026_09_30.csv`
- `data/exports/tableau/state_ev_charging_comparison_2026.csv`
- `data/exports/tableau/kba_national_stock_history.csv`
- `data/exports/tableau/preparation/power_band_distribution_2026_09_30.csv`
- `data/exports/tableau/preparation/equipment_status_breakdown_2026_09_30.csv`

It verifies the Batch 19 manifest checksums and row/column contracts for the
Batch 19 files, validates the Batch 21 presentation rows, checks the required
national/state/history reconciliations, and writes `public/data/dashboard.json`.
No DuckDB object, raw source workbook, or source export is modified.

## Data and interaction boundaries

- National and state sources remain separate facts; the pre-combined state comparison is used for the fixed KBA July 2026 / BNetzA September 2026 table and penetration chart.
- The four charging power bands are derived as mutually exclusive rows from the validated nested thresholds: normal, fast below 150 kW, high power below 350 kW, and ultra-fast.
- State selection highlights the map, ranking, table, and penetration chart. Sorting changes table order only; it never changes totals.
- The map geometry is local and attribution is in [`public/data/geo-attribution.md`](public/data/geo-attribution.md).

The dashboard is descriptive. It does not present charger adequacy, demand,
utilization, availability, historical infrastructure stock, or causality.
