# Web dashboard design

## Product intent

The Batch 23 dashboard is a compact two-page executive surface for the
validated local evidence. It answers two questions in sequence:

1. What is the national charging-register picture and how does registered EV
   stock trend over time?
2. How does the current infrastructure and BEV picture differ across the 16
   federal states?

The design keeps exact values, dates, source grain and caveats close to the
visuals. It is deliberately descriptive and does not imply infrastructure
adequacy or utilization.

## Visual system

- Canvas: deep navy `#071522` with a slightly lighter header and panel
  surfaces.
- Cards: white surfaces with subtle borders and restrained shadows for a
  high-contrast analytical workspace.
- Infrastructure: cyan/blue tones.
- Fast and high-power emphasis: amber.
- EV stock: green for BEV, purple for PHEV.
- Typography: system sans-serif, strong numeric hierarchy, compact uppercase
  eyebrow labels and readable body copy.
- Layout rhythm: 8 px base spacing, generous panel padding, 14 px card radius.

## Page 1 — National Summary

The page opens with the BNetzA and KBA snapshot pills, then five large KPI
cards:

- registered charging equipment;
- charging-point slots;
- fast charging points;
- declared equipment nominal power;
- national registered BEVs, with PHEVs as a compact supplement.

The next row combines an interactive four-band charging-power donut with the
33-observation BEV/PHEV KBA history. The donut uses the mutually exclusive
normal, fast, high-power and ultra-fast definitions; the line chart keeps
BEV/PHEV end labels and shows exact stock, date and penetration in tooltips.

The lower row contains the horizontal power-band comparison and the current
equipment-status breakdown. Both charts use zero-based axes and explicit
numeric labels so small categories are not visually exaggerated.

## Page 2 — Geographic View

The page starts with four evidence-led highlights: NRW charging-point scale,
Hamburg BEV penetration, Sachsen-Anhalt fast-share intensity and the national
16-state BEV scope. A selection banner then keeps the active state visible and
offers a clear-selection action.

The main analysis row contains:

- a local Germany state choropleth with a sequential charging-point scale;
- a top-10 charging-point ranking with visible values and clickable rows.

The state comparison table is the detailed audit surface. It includes all 16
states, charging points, BEV stock, BEV penetration, fast share, and visible
data bars for the primary measures. A sort control changes the table order
without changing the underlying source grain.

The final chart compares BEV penetration by state. Map, ranking, table and
penetration-chart selections use the same state key so the active context is
consistent across the page.

## Interaction rules

- Header navigation switches between `#national` and `#geographic` without a
  server-side route.
- Donut segments and power bars highlight their selected band and expose exact
  count/share tooltips.
- Map states, ranking rows, table rows and BEV-penetration bars select a state.
- Selected state rows are keyboard-focusable; Enter/Space activates them.
- The geographic selection banner clears back to the all-state view.
- Tooltips always include the relevant date and metric grain.

## Methodology and accessibility

The visible notes explain maximum-per-point power parsing, registered-stock
meaning, 16-state scope, cross-snapshot timing and the limitation that the
BNetzA register is a published register rather than a utilization feed. The
table remains available as an exact-value alternative to the map and charts.
Buttons, links, and selectable rows use native controls or keyboard handlers;
the page layout collapses to one column on narrow screens.
