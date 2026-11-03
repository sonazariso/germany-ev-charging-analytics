# Batch 22.1 — Tableau Desktop Authoring MCP feasibility

**Date:** 2026-11-03
**Scope:** Read-only investigation of the official Tableau Desktop Authoring MCP for the two approved Executive Overview dashboards.
**Status:** `CONDITIONAL GO`

## Decision

The official Desktop build is a credible native authoring route. It can drive a
running Tableau Desktop instance through Tableau's External Client API, create
worksheets and dashboards, bind chart templates and fields, author calculated
fields, apply selected formatting and colors, read back workbook state, export
images, and save a native `.twb` or `.twbx`.

It is not operational in this environment yet. Node.js/npm are unavailable,
the Codex configuration has no Tableau Desktop MCP entry, computer use is
explicitly disabled, Tableau is not running, and no External Client API
discovery file exists. Tableau Desktop 2026.3.0 contains the External Client
API framework, but its live API version and the required workbook smoke test
could not be confirmed without launching/configuring the authoring path.

The recommended next step is therefore an approval-gated build and smoke test,
not manual field dragging and not the Web-only npm server.

## Official implementation reviewed

The repository was inspected at `main` commit `8c0ac37` on 2026-11-03.

- [Official repository README](https://github.com/tableau/tableau-mcp) states that
  `@tableau/mcp-server` is Web-only and that Desktop authoring is a separate
  source build.
- [Desktop Authoring MCP quickstart](https://github.com/tableau/tableau-mcp/blob/main/docs/README.desktop.md)
  requires Node.js `>=22.7.5`, `npm ci`, `npm run build:desktop`, and a running
  Tableau Desktop instance discovered by PID.
- [Desktop tool registry](https://github.com/tableau/tableau-mcp/blob/main/src/tools/desktop/toolName.ts)
  includes the authoring, readback, formatting, image-export and save tools.
- [External Client API layer](https://github.com/tableau/tableau-mcp/blob/main/src/desktop/externalApi/README.md)
  documents a loopback HTTP API discovered through per-instance files.

## Capability check

| Requirement | Result | Evidence and qualification |
|---|---|---|
| Create worksheets | **Supported** | `add-worksheet`; template/field tools can build and apply chart worksheets. |
| Create dashboards | **Supported** | `add-dashboard` and `run-dashboard-batch`; executive-summary and grid/row/column layouts are available. |
| Bind fields without manual dragging | **Supported** | `list-available-fields`, `resolve-field`, `add-field`, `bind-template`, and `build-worksheets-from-templates`. |
| Calculated fields | **Supported** | `author-calc` plus calculated-field validation. |
| Formatting and colors | **Partial** | Label/number formatting, member colors and dashboard-zone corner radius are first-class. Exact typography, axes, gridlines, card styling and some table details may require the supported workbook/XML apply or command path and live readback verification. |
| Save native workbooks | **Supported** | `save-workbook` accepts an absolute `.twb`/`.twbx` path; `workbook-export-as` can create a copy. Passing a path avoids a blocking Save dialog for a new workbook. |
| Add the six CSV subject sources | **Conditional** | `open-file` says a local datasource attaches to the open workbook. `apply-datasource` explicitly replaces an existing datasource and does **not** add/import `.tds`/`.tdsx`; each CSV attachment must be verified in the live workbook. |
| Four-segment donut | **Likely supported** | The bundled template catalog contains a donut template. The exact center total, labels, percentages and palette still need readback/image verification. |
| 33-period BEV/PHEV line | **Likely supported** | Bundled line and multi-line templates are present; the project CSV has the required 33 actual periods. |
| State bars, KPI cards and status bars | **Supported** | Bundled KPI, horizontal-bar and bar templates cover the requested chart families. |
| Real German state map | **Conditional** | A choropleth-map template exists, but Tableau's live `State/Province` recognition for all 16 German names must be tested. No geometry may be fabricated if any state is `Unknown`. |
| Native screenshots/readback | **Supported subject to API version** | Desktop image and workbook/worksheet readback tools are present; screenshot support has an API floor in the official source. |

## Local environment findings

| Check | Observed result |
|---|---|
| Tableau Desktop | `/Applications/Tableau Desktop 2026.3.app`; `CFBundleShortVersionString=2026.3.0`, build `20263.26.1022.1645`. |
| Tableau process | Not running during the investigation. |
| External API framework | `libtabexternalapi.dylib` and `libtabexternalapihost.dylib` are present in the installed app; `/v0` workbook routes are visible in the binary. |
| Node.js/npm | `node` and `npm` are not on `PATH`; no usable bundled Node/npm was found at the configured ChatGPT path. |
| Codex MCP configuration | `node_repl` is configured. `computer-use` and `cua_repl` entries exist but have `enabled = false`. No `tableau` or `tableau-desktop` MCP entry is configured. |
| Current callable tools | No Tableau or computer-use tool is exposed to this session. |
| Desktop discovery | Both documented macOS discovery directories are absent because Tableau is not running. |
| macOS TCC read-only probe | No matching Accessibility, Screen Capture or Apple Events grant rows were observed in the user TCC database. This is consistent with the Desktop MCP path not using those APIs; it is not a live authoring test. |

## macOS permissions conclusion

The official Desktop MCP does **not** require Accessibility, Screen Recording,
AppleScript/Apple Events or mouse/keyboard automation. It starts an MCP stdio
process and sends authenticated loopback HTTP requests to Tableau Desktop's
External Client API. It needs ordinary filesystem access to read the discovery
file/cache and write the explicitly requested workbook path.

The separate Codex computer-use fallback would have a different macOS
permission model and is currently disabled. It should not be enabled merely to
use the official Tableau Desktop MCP.

## Tableau 2026.3 compatibility assessment

The source explicitly supports the macOS discovery-root logic and the installed
2026.3 application contains the External Client API libraries. The current
official source describes the Athena V0 contract at API version `0.2.27`; the
core worksheet/dashboard/open/save tools have floors around `0.2.6`, datasource
and color tools around `0.2.10`, and screenshot support at `0.2.17`.

There is no official product-version matrix in the reviewed repository mapping
Tableau Desktop `2026.3.0` to an External Client API version. Compatibility is
therefore **probable but unverified** until a running instance returns a
discovery record and passes `get-app-info`, `get-capabilities`, and a disposable
worksheet/dashboard save smoke test.

## Exact installation and verification plan

These steps were **not executed** because the batch is read-only and package or
configuration changes were not approved.

1. Approve Node.js `>=22.7.5` and npm installation, preferably in the normal
   local toolchain. Keep the Tableau MCP source/build in an isolated tooling
   directory outside the analytical project.
2. Clone a pinned official Tableau MCP source revision, then run `npm ci` and
   `npm run build:desktop`. Do not use `npx @tableau/mcp-server` for Desktop;
   the official README says that package is Web-only.
3. After approval, add one local stdio MCP entry pointing at
   `build/index.desktop.js`, with `TRANSPORT=stdio` and the default
   `TOOL_PROFILE=dynamic-authoring`. No Tableau Server URL, PAT or Cloud
   credentials are needed for the Desktop profile.
4. Launch Tableau Desktop 2026.3.0 with a disposable blank workbook. Run
   `list-instances`, then use its PID as `session` for `get-app-info`,
   `get-capabilities`, `get-desktop-state`, `get-workbook-inventory` and
   `list-workbook-datasources`. Record the returned API version, capabilities,
   workbook path and unsaved state.
5. Verify the authoring path on the disposable workbook: attach one approved
   CSV with `open-file`; confirm it appears in datasource readback; add a
   worksheet and a dashboard; bind a KPI or bar template; author one harmless
   calculated field; apply labels/number format and a member color; compose a
   small executive-summary dashboard; export an image; and save to a temporary
   `.twb` path using `save-workbook`.
6. Reopen/read back the temporary workbook and verify the worksheet, dashboard,
   calculated field, datasource and image. If the map test is included, bind
   `state_name` as `State/Province`, disambiguate Country/Region as Germany,
   and require all 16 states to resolve with no `Unknown` marks.
7. Only after the smoke test passes, use the six approved CSV subject sources
   and the Batch 21 specification to author the two real dashboards. Verify
   the 33-period history, four donut slices, maintenance count 20, 16-row
   state table, all four geographic highlights, map recognition and image
   clipping before saving the requested project workbook.

## Limitations that can block completion

- The Desktop build is source-built and separate from the Web-only npm
  package; without Node/npm and an approved Codex MCP entry it cannot run.
- A running Tableau Desktop instance must expose the External Client API and a
  valid discovery file. The current machine has not yet demonstrated that
  live handshake for 2026.3.0.
- CSV import is not an `apply-datasource` operation. If `open-file` cannot
  attach all six subject CSVs in this Desktop build, the approved dashboards
  cannot be built natively without an additional approved import method.
- Official state-map recognition is a hard acceptance gate. A failed German
  state lookup cannot be repaired with fabricated geometry or screenshot-derived
  shapes.
- The high-level formatting tools do not expose every requested corporate
  styling detail. Exact 1600×900 composition, table column widths, subtle
  separators, typography and card treatment may require the official cached
  XML/command path and repeated readback checks; unsupported or unverified XML
  edits must not be used.
- A `.twb` with external CSV paths is editable but not self-contained. A `.twbx`
  should be created only after the project's packaging, source-license and
  path policy are approved.

## Minimum approved changes

1. Approve Node.js/npm and the isolated official Desktop source build.
2. Approve one Codex `tableau-desktop` stdio MCP entry; do not enable
   computer-use or change macOS privacy settings.
3. Approve the disposable smoke-test workbook and then a separate write batch
   for the two real dashboards.

Until those approvals and the live smoke test are complete, the repository
status remains `TABLEAU_WORKBOOK_NOT_YET_CREATED`; no `.twb`, `.twbx`,
screenshot or external publication is claimed.

## Investigation safety record

No package was installed. No Codex, Tableau or macOS setting was changed. No
database, export, raw source, reference file, workbook, remote, upload or
publication was modified or created. The official repository was cloned only
into a temporary directory for read-only source inspection.
