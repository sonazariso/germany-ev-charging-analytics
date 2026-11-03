# Tableau executive overview handoff

Batch 21 prepares exactly two dashboards:

1. `01 — National Summary`
2. `02 — Geographic View`

Use the separate validated CSV sources and the two deterministic presentation
files under `data/exports/tableau/preparation/`. Do not create unapproved
Fact-to-Fact relationships. The complete worksheet mappings, colors, layout,
manual Desktop steps and verification gates are in
[`docs/tableau-executive-overview.md`](../docs/tableau-executive-overview.md).

The workbook is not yet created. Batch 22.1 identified the official Tableau
Desktop Authoring MCP as a `CONDITIONAL_GO`, but Node.js/npm, MCP configuration
and a live Desktop External Client API smoke test are still pending approval.
See [`reports/batch22_1_tableau_desktop_mcp_feasibility.md`](../reports/batch22_1_tableau_desktop_mcp_feasibility.md).
Do not claim a `.twb`/`.twbx` path or screenshots until Tableau Desktop opens and
verifies the actual file. Do not publish externally.
