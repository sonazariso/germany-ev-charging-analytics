# Batch 21 — Tableau executive overview implementation specification

**Scope:** exactly two Tableau dashboards: `01 — National Summary` and
`02 — Geographic View`.

**Implementation status:** data preparation passed. The Tableau workbook is
**not yet created**. Batch 22.2 built and registered the official Desktop MCP,
Batch 22.3 performed the owner-approved preference validation, and Batch 22.4
confirmed that Tableau Desktop 2026.3.0 restores
`Settings.ExternalApiEnabled=0` while initializing `FreeEditionActive`. No
supported Free Edition method for keeping the External Client API enabled was
found. This document remains the implementation contract; the diagnosis and
approval gates are in
[`reports/batch22_4_tableau_external_api_diagnosis.md`](../reports/batch22_4_tableau_external_api_diagnosis.md).
It does not describe a generated `.twb` or `.twbx`.

## 1. Approved narrative and source dates

The overview is a centered, desktop executive report with a restrained
navy/teal/slate palette, a slightly darker outer background, white chart cards,
compact KPI strips, and no large sidebar.

| Source | Display label | Date role |
|---|---|---|
| BNetzA charging register | `BNetzA: 30 September 2026` | infrastructure snapshot |
| KBA FZ 27 | `KBA: 1 July 2026` | registered passenger-car stock |
| BBSR | not used on these two pages | historical charging-only geography remains a separate subject |

The national cards use the KBA `Deutschland` aggregate where specified. The
geographic page uses the validated 16-state KBA scope. The national July BEV
total is 2,365,047; the 16-state July total is 2,362,218. Their difference,
2,829, is KBA `Sonstige` and must not be assigned to a Bundesland. The national
PHEV total is 1,226,863; the 16-state PHEV total is 1,225,241.

## 2. Tableau data-source plan

Use separate Tableau data sources. Add each CSV through **Data → New Data
Source → Text File** and do not create relationships or joins between these
subject sources.

| Tableau source name | Repository file | Grain | Worksheets |
|---|---|---|---|
| `DS_NationalCharging` | `data/exports/tableau/national_charging_2026_09_30.csv` | one Germany row | national KPI cards |
| `DS_PowerBands` | `data/exports/tableau/preparation/power_band_distribution_2026_09_30.csv` | one mutually exclusive band | charging donut; power-band bars |
| `DS_NationalKBAHistory` | `data/exports/tableau/kba_national_stock_history.csv` | one actual national stock date | EV stock history; PHEV supplementary label |
| `DS_EquipmentStatus` | `data/exports/tableau/preparation/equipment_status_breakdown_2026_09_30.csv` | one published status | equipment status |
| `DS_StateCharging` | `data/exports/tableau/state_charging_2026_09_30.csv` | one Bundesland | map; top-state ranking; fast-share highlight |
| `DS_StateComparison` | `data/exports/tableau/state_ev_charging_comparison_2026.csv` | one state at fixed KBA July / BNetzA September dates | state table; BEV penetration; BEV highlight |

The Batch 19 manifest and the Batch 21 validation report are the source
contracts. The state comparison is already pre-combined at one row per state;
do not relate it back to `DS_StateCharging` or `DS_KBAStateStock`.

## 3. Centralized design tokens

Keep these values in the workbook color palette and in any dashboard style
notes so the owner can tune them without changing the data contract.

| Token | Hex | Use |
|---|---|---|
| `canvas.outer` | `#E8EEF1` | page background |
| `panel.white` | `#FFFFFF` | chart cards and KPI cards |
| `ink.navy` | `#142B3A` | titles, headings, primary text |
| `accent.navy` | `#163A5F` | ultra-fast band, BEV line, primary emphasis |
| `accent.teal` | `#1C9A9C` | fast band, active status, charging emphasis |
| `accent.blue` | `#367A9E` | high-power band, secondary bars |
| `accent.gold` | `#D6A84F` | PHEV line, maintenance status, small callouts |
| `band.normal` | `#C9D7DE` | normal ≤22 kW |
| `text.muted` | `#6F7C83` | subtitles, source dates, caveats |
| `axis.gray` | `#8997A0` | axes and tick labels |
| `grid.gray` | `#D9E1E5` | subtle gridlines and row rules |

Use one identical heading size and weight across all chart cards. Remove heavy
borders, unnecessary legends, and nonessential filters. Use thin gray row
dividers in the state table and a zero baseline on every bar chart.

## 4. Page 1 — `01 — National Summary`

### Header and KPI strip

Header text:

- Title: `Germany EV Charging Analytics`
- Subtitle: `Executive Overview · National Summary`
- Source labels: `BNetzA: 30 September 2026` and `KBA: 1 July 2026`

Place five equal-width cards in one compact row. Use a simple line icon or
geometric icon; do not use brand assets.

| Worksheet | Source / filter | Mark and fields | Display |
|---|---|---|---:|
| `KPI — Charging equipment` | `DS_NationalCharging`; `geography_name = Germany` | Text mark; `MIN(equipment_count)` | `117,662` |
| `KPI — Charging points` | same | Text mark; `MIN(charging_point_count)` | `211,253` |
| `KPI — Fast points` | same | Text mark; `MIN(fast_charging_point_count)` | `55,098` |
| `KPI — National BEV stock` | `DS_NationalKBAHistory`; `stock_date = 2026-07-01` | Text mark; `MIN(bev_passenger_car_stock)` | `2,365,047` |
| `KPI — Declared nominal power` | `DS_NationalCharging`; `geography_name = Germany` | Text mark; `MIN(equipment_nominal_power_mw)` | `≈9,215.4 MW` |

`MIN` is intentional for the one-row sources and avoids accidental duplicate
aggregation if a worksheet is later reused. Format counts with `#,##0` and
power with `#,##0.0 MW`.

### Worksheet definitions

#### `Charging Point Mix`

- Source: `DS_PowerBands`.
- Marks: Pie; put `power_band` on Color and Detail, `SUM(charging_point_count)`
  on Angle, and `power_band_order` on Detail for deterministic sort.
- Sort `power_band` ascending by `power_band_order` so the order is normal,
  fast, high power, ultra-fast.
- Put `charging_point_count` and `charging_point_share_pct` on Label. Show the
  band name, count, and percentage; format count as `#,##0` and percentage as
  `0.0%` only if the field is divided by 100 in a calculated display field.
  The stored field is a percentage-point number, so do not apply a second
  percentage multiplication.
- Create a dual-axis donut: duplicate the pie measure, synchronize axes, set
  the second Marks card to Circle, color it `panel.white`, and reduce its size
  to create the center hole. On the center circle use the fixed LOD
  `{ FIXED : SUM([charging_point_count]) }` as a text label, formatted
  `#,##0`, with a smaller `Total points` caption.
- Use the four centralized band colors. Do not use nested `>=150` and `>=350`
  counts as separate slices.

#### `National EV Stock History`

- Source: `DS_NationalKBAHistory`.
- Filter `source_report_snapshot = 2026-07-01` and retain all 33
  `stock_date` rows from `2018-07-01` through `2026-07-01`.
- Columns: continuous `stock_date`, formatted `MMM YYYY`.
- Rows: `Measure Values`; filter `Measure Names` to
  `bev_passenger_car_stock` and `phev_passenger_car_stock`.
- Marks: Line; `Measure Names` on Color, with BEV `accent.navy` and PHEV
  `accent.gold`. Use `SUM` because each date is unique at this source grain.
- Turn on line-end labels only. Label the final BEV and PHEV values and format
  them as `#,##0`; do not label every one of the 33 marks.
- Add a small subtitle or annotation inside the card: `July 2026: BEV
  2,365,047 · PHEV 1,226,863`.
- Do not interpolate dates or add fabricated intermediate observations.

#### `Power Band Distribution`

- Source: `DS_PowerBands`.
- Rows: `power_band`, sorted ascending by `power_band_order`.
- Columns: `SUM(charging_point_count)`; Marks: Bar; Color by `power_band`.
- Label each bar with count and the stored percentage-point field. Use a zero
  baseline and a shared axis; no dual axes or truncated scales.

#### `Equipment Status`

- Source: `DS_EquipmentStatus`.
- Rows: `equipment_status`, sorted ascending by `status_order`.
- Columns: `SUM(equipment_count)`; Marks: Bar; Color by status.
- Label every row with `equipment_count` and `equipment_share_pct`, including
  the 20 `In Wartung` records. Keep the axis starting at zero and show the
  small category as a labelled row; never use a broken or manipulated axis.
- Use `accent.teal` for `In Betrieb` and `accent.gold` for `In Wartung`.

#### Methodology note

Use a dashboard text object, not a data join:

> Infrastructure is the BNetzA published register snapshot dated 30 September
> 2026; vehicle stock is the KBA registered passenger-car stock dated 1 July
> 2026. Charging-point bands use the maximum parsed declared power per point.
> Equipment and populated point slots are distinct measures. National KBA
> totals include `Sonstige`; the state view below uses only the 16 named
> Bundesländer. Counts do not measure utilization, demand, availability, or
> infrastructure adequacy.

### Dashboard assembly

Use a fixed 1600 × 900 desktop canvas, with 24 px outer padding and a 16 px
card gutter. Recommended composition:

1. Header and source-date strip: top 80 px.
2. Five-card KPI strip: y≈96–210.
3. Main row: donut at left and EV history at right, y≈230–565.
4. Bottom row: power-band bars at left and equipment status at right,
   y≈585–830.
5. Methodology note in the bottom margin or as a slim footer.

Place each chart in a white card on `canvas.outer`. Check at 1600 × 900 and at
the actual monitor size for title, label, and legend clipping.

## 5. Page 2 — `02 — Geographic View`

Header text:

- Title: `Germany EV Charging Analytics`
- Subtitle: `Executive Overview · Geographic View`
- Source labels: `BNetzA: 30 September 2026` and `KBA: 1 July 2026`

### Executive highlights

Use four compact cards:

| Highlight | Validated source field / calculation | Display |
|---|---|---|
| States covered | `COUNTD(state_name)` in `DS_StateCharging` | `16` |
| Most charging points | maximum `SUM(charging_point_count)` in `DS_StateCharging` | `Nordrhein-Westfalen · 41,536` |
| Highest BEV penetration | `100 * SUM(bev_passenger_car_stock) / SUM(passenger_car_stock)` in `DS_StateComparison` | `Hamburg · 5.97%` |
| Highest fast-point share | `100 * SUM(fast_point_count) / SUM(charging_point_count)` in `DS_StateComparison` or equivalent state charging fields | `Sachsen-Anhalt · 39.89%` |

These cards must be revalidated from the approved exports if the source files
are refreshed. They must not use numbers transcribed from a visual mockup.

### `Charging Points by State`

- Source: `DS_StateCharging`.
- Assign `state_name` the Tableau geographic role **State/Province**. In **Map
  → Edit Locations**, set Country/Region to `Germany` if Tableau needs the
  disambiguation.
- Put `state_name` on Detail and `SUM(charging_point_count)` on Color and
  Label. Use a sequential navy/teal scale and a light gray map background.
- Verify that all 16 named state geometries resolve and that the map has no
  `Unknown` marks. Record the result in the validation report.
- If official Tableau recognition does not resolve all 16 states, leave the map
  visibly marked as pending and use the ranking/table worksheets. Do not draw
  boundaries, import a fabricated shape, or infer geometry from a screenshot.

### `Top States by Charging Points`

- Source: `DS_StateCharging` only.
- Rows: `state_name`; Columns: `SUM(charging_point_count)`; Marks: Bar.
- Sort descending by the measure and apply a Top 10 filter by
  `SUM(charging_point_count)`.
- Put the count on Label, format `#,##0`, use a zero baseline, and keep the
  state names readable. Use `accent.teal` for the bars and `ink.navy` for the
  labels.

### `State Comparison`

Use the existing pre-combined `DS_StateComparison` source at its one-row-per-
state grain. Do not join or relate it to another fact.

Create these Tableau calculated fields:

```text
BEV stock = SUM([bev_passenger_car_stock])
Charging points = SUM([charging_point_count])
Fast point share =
    100 * SUM([fast_point_count]) / SUM([charging_point_count])
BEV penetration =
    100 * SUM([bev_passenger_car_stock]) / SUM([passenger_car_stock])
```

Build a text table with:

- Rows: `state_name`, sorted descending by `BEV penetration`.
- Columns: `BEV stock`, `Charging points`, `Fast point share`, `BEV
  penetration`.
- Text: formatted `#,##0` for stock and points; `0.00%` display fields for
  the two percentage measures (divide the percentage-point calculations by
  100 in a display-only calculation if necessary).
- Filters: fixed `kba_reference_date = 2026-07-01` and
  `bnetza_reference_date = 2026-09-30`; no user date filter.
- Style: white panel, thin `grid.gray` row dividers, right-aligned numeric
  columns, left-aligned state names, no zebra striping.

For the requested subtle in-cell charging-point bars, duplicate the table
worksheet as `State Comparison — point bars`, retain the same state sort, use
`Charging points` as a horizontal Bar mark with a zero baseline, and place it
directly beneath/behind the charging-point column in the dashboard. Keep the
numeric value on top of the bar and the remaining columns as text. Both
worksheets use the same `DS_StateComparison` source and the same fixed filters;
the composite is one executive table, not a fact-to-fact join.

Do not include `bevs_per_charging_point` in this table. It is contextual only
and must not be presented as an infrastructure adequacy measure.

### `BEV Penetration by State`

- Source: `DS_StateComparison`.
- Rows: `state_name`; Columns: calculated `BEV penetration`.
- Marks: horizontal Bar; sort descending; label every bar as `0.00%`.
- Use `accent.navy`, zero baseline, subtle gridlines, and no secondary axis.
- Keep the fixed KBA July 2026 date visible in the card subtitle.

### Dashboard assembly

Use the same fixed 1600 × 900 canvas and page tokens as Page 1:

1. Header and source-date strip: top 80 px.
2. Four highlight cards: y≈96–205.
3. Map and top-ten ranking: y≈225–535, with the map given enough width to
   show all state labels without clipping.
4. State comparison table and BEV-penetration bars: y≈555–840.
5. Footer note: `16-state KBA stock is separate from national Deutschland and
   Sonstige totals; charging and vehicle dates are not contemporaneous.`

## 6. Official Desktop MCP authoring and verification steps

Batch 22.1 found that the official Desktop build can perform the native
worksheet, dashboard, calculation, formatting, readback, image-export and
save operations needed here. It is a separate source build from the Web-only
npm package. Batch 22.2 completed the isolated source build and Codex
registration, and verified MCP initialization, the 85-tool surface and
headless template discovery. Batch 22.3 attempted the owner-approved
preference change, but Tableau reverted it during startup. Batch 22.4
confirmed the startup `FreeEditionActive` state, ruled out the inspected
preference/MCP alternatives and found no documented supported Free Edition
activation method. No workbook authoring was attempted.

1. Completed in Batch 22.2: install Node.js `v22.23.4` locally, build the
   pinned official source at tag `v5.3.0`, and register one local Codex stdio
   MCP entry. Keep computer-use disabled and do not change macOS privacy
   settings.
2. Completed in Batch 22.2: the isolated build produced
   `build/index.desktop.js` and `build/desktop/data/`; the MCP client points at
   that Desktop entry and does not use the Web-only `@tableau/mcp-server`
   package.
3. Do not retry the preference or launch Desktop solely to seek a different
   result. Only after the owner obtains a supported paid Desktop
   configuration/support answer should the read-only sequence run: launch
   Tableau Desktop 2026.3 with a disposable blank workbook, call
   `list-instances`, then use the returned PID as `session` for `get-app-info`,
   `get-capabilities`, `get-desktop-state`, `get-workbook-inventory` and
   `list-workbook-datasources`. Record the live External Client API version
   and capability response. See
   [`reports/batch22_4_tableau_external_api_diagnosis.md`](../reports/batch22_4_tableau_external_api_diagnosis.md).
4. Attach the six CSV sources in Section 2 with `open-file`, verify every
   datasource in workbook readback, and keep the sources separate. The
   high-level `apply-datasource` tool replaces an existing datasource; it does
   not import one.
5. Use the official template/field path to create the Page 1 worksheets and
   `01 — National Summary`. Use the requested executive-summary or validated
   custom layout, then read back the workbook and export a disposable image.
6. Create the Page 2 worksheets and `02 — Geographic View`. Assign
   `state_name` the official Tableau **State/Province** role with Germany as
   the country disambiguator. If any state is `Unknown`, leave the map pending;
   do not fabricate geometry.
7. Verify that the history line has exactly 33 marks per series, the donut has
   exactly four segments totalling 211,253, the equipment-status sheet labels
   20 `In Wartung` records, the state table has exactly 16 rows, and all four
   geographic highlights match
   `reports/batch21_tableau_overview_validation.md`.
8. Check the dashboard images at approximately 1600 × 900 and at the actual
   monitor size. Confirm no title, source date, label, legend, table column,
   or map mark is clipped. Fine typography, gridlines, card styling and table
   separators may require the official validated workbook/XML apply path.
9. Save only after the workbook opens successfully and passes the checks.
   Recommended local path:
   `tableau/germany_ev_charging_analytics_executive_overview.twb`.
   Optionally save a `.twbx` only after confirming the packaged data-source
   policy and source licensing. That path is a recommendation, not evidence
   that a file exists.
10. Capture one screenshot per dashboard at the final canvas size and add the
    relative paths to the Batch 21 validation report. Current screenshot
    references: **none — workbook not yet created**.
11. Do not publish to Tableau Public or any external service in this batch.

If the supported Desktop MCP smoke test remains unavailable, manual Desktop
authoring is a separate approval-gated fallback. It requires an approved GUI
host and applicable macOS Accessibility/visual permissions, a disposable
workbook, native save/reopen verification and no publication. This
specification does not authorize bypassing the live API checks, changing
security settings, or creating unverified workbook XML.

## 7. Validation and handoff status

The deterministic preparation command is:

```text
./.venv/bin/python scripts/21_prepare_tableau_overview.py
```

It reads the Batch 19 manifest and all nine CSV headers/checksums, validates
the listed raw/reference fingerprints, opens DuckDB with `read_only=True`,
validates the national and 16-state scopes, derives the four power bands and
status rows, and checks the DuckDB hash before and after. Results and derived
hashes are recorded in
[`reports/batch21_tableau_overview_validation.md`](../reports/batch21_tableau_overview_validation.md).

Current status:

- `DATA_PREPARATION_PASS`
- `DESKTOP_MCP_FEASIBILITY=CONDITIONAL_GO`
- `DESKTOP_MCP_SOURCE_BUILD=PASS`
- `DESKTOP_MCP_CODEX_REGISTRATION=PASS`
- `DESKTOP_MCP_HEADLESS_TEMPLATE_CHECK=PASS`
- `DESKTOP_MCP_LIVE_HANDSHAKE=BLOCKED_EXTERNAL_API_REVERTED_TO_DISABLED`
- `DESKTOP_MCP_STARTUP_DIAGNOSIS=ROOT_CAUSE_CONFIRMED_FREE_EDITION_INITIALIZATION`
- `DESKTOP_MCP_SUPPORTED_ACTIVATION=NOT_ESTABLISHED_FOR_CURRENT_FREE_EDITION_STATE`
- `GUI_AUTHORING_FALLBACK=FEASIBLE_APPROVAL_GATED`
- `TABLEAU_WORKBOOK_NOT_YET_CREATED`
- Desktop MCP build and headless MCP checks: passed
- Live Desktop API smoke test: blocked at `list-instances`; Tableau reverted the owner-approved preference to disabled during startup
- Screenshot validation: pending native authoring
- Official geographic map validation: pending native authoring
- External publication: not attempted
- Workbook path: none verified
