# Tableau executive overview handoff

Batch 21 prepares exactly two dashboards:

1. `01 — National Summary`
2. `02 — Geographic View`

Use the separate validated CSV sources and the two deterministic presentation
files under `data/exports/tableau/preparation/`. Do not create unapproved
Fact-to-Fact relationships. The complete worksheet mappings, colors, layout,
manual Desktop steps and verification gates are in
[`docs/tableau-executive-overview.md`](../docs/tableau-executive-overview.md).

The workbook is not yet created. Batch 22.2 completed the isolated official
Tableau Desktop MCP source build and Codex `tableau-desktop` registration, and
headless template discovery passed. Batch 22.3 attempted the owner-approved
change to `Settings.ExternalApiEnabled`, but Tableau Desktop 2026.3.0 reverted
the integer value to `0` during startup and published no External Client API
discovery file. Batch 22.4 confirmed that the same startup records
`FreeEditionActive`; no supported Free Edition method for keeping the API
enabled was found. Do not retry the preference or use a binary/security
bypass. See
[`reports/batch22_2_tableau_mcp_setup.md`](../reports/batch22_2_tableau_mcp_setup.md)
and
[`reports/batch22_3_tableau_external_api_validation.md`](../reports/batch22_3_tableau_external_api_validation.md),
and
[`reports/batch22_4_tableau_external_api_diagnosis.md`](../reports/batch22_4_tableau_external_api_diagnosis.md),
plus the earlier
[`reports/batch22_1_tableau_desktop_mcp_feasibility.md`](../reports/batch22_1_tableau_desktop_mcp_feasibility.md).
Do not claim a `.twb`/`.twbx` path or screenshots until Tableau Desktop opens and
verifies the actual file. Do not publish externally.

Batch 22.5 performed the local GUI permission and capability check through the
VS Code OpenAI Codex host. System Events/Accessibility and Screen Recording
worked, and Tableau's process/window could be read. The blank `Tableau - Book1`
start pane did not expose worksheet tabs or a field pane, and the captured
screen did not show a rendered worksheet canvas. The result is
`LOCAL_AUTOMATION_PARTIAL`; no worksheet, data source, chart, workbook or
screenshot artifact was retained. See
[`reports/batch22_5_local_automation_capability_check.md`](../reports/batch22_5_local_automation_capability_check.md).
