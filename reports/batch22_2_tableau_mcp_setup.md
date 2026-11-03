# Batch 22.2 — Tableau Desktop Authoring MCP setup

**Date:** 2026-11-03
**Status:** `MCP_SETUP_PARTIAL`

## Outcome

The approved local installation and Codex registration completed successfully,
but the real Tableau Desktop handshake is blocked because Tableau Desktop is
running with its External Client API disabled. No authoring call was made and
no workbook, project data, export, database object or source crosswalk was
modified.

## Installed source and runtime

- Official source only: `https://github.com/tableau/tableau-mcp.git`
- Isolated checkout: `/Users/admin/dev/tools/tableau-mcp`
- Selected stable tag: `v5.3.0`
- Selected source revision: `8c0ac37a336cd6c3dcf57f9a3dfc86b6541281f0`
- Local Node runtime: `/Users/admin/dev/tools/node-v22.23.4-darwin-x64`
- Node version: `v22.23.4`; npm version: `10.9.9`
- Download SHA-256: `efcc2b0db6f94bf53eddb038fe2b370277a042bd29e4f19b8f8e23598795b819`
- `npm ci`: passed; only a transitive `glob` deprecation warning was emitted.
- `npm run build:desktop`: passed with exit code `0`.
- Required artifacts exist: `build/index.desktop.js` and `build/desktop/data/`.

The Desktop build is the official source variant. The Web-only npm package was
not used, and the Tableau MCP source was not modified.

## Codex registration

Codex CLI `0.163.0` registered the following global stdio server through the
supported CLI:

```toml
[mcp_servers.tableau-desktop]
command = "/Users/admin/dev/tools/node-v22.23.4-darwin-x64/bin/node"
args = ["/Users/admin/dev/tools/tableau-mcp/build/index.desktop.js"]

[mcp_servers.tableau-desktop.env]
PRODUCT_TELEMETRY_ENABLED = "false"
```

`codex mcp list` shows `tableau-desktop` enabled. Existing `computer-use`,
`cua_repl` and `node_repl` entries were preserved. No Tableau Cloud URL,
credential, PAT, OAuth secret or external endpoint was added.

## Real handshake

Tableau Desktop was launched from `/Applications/Tableau Desktop 2026.3.app`.

- Tableau version: `2026.3.0`
- Build: `20263.26.1022.1645`
- Observed process: PID `65531`
- MCP initialize: passed; server reported `tableau-desktop-mcp` version `5.3.0`.
- MCP `tools/list`: passed; `85` tools were exposed.
- Headless `list-templates`: passed; returned `trend-line-chart`.
- `list-instances`: failed with the official error that no running Tableau
  Desktop instance was found and the External Client API discovery file was
  unavailable.
- `list-available-fields`, workbook inspection and datasource inspection were
  not attempted without a valid Desktop session.

The official MCP checks these macOS discovery directories, and neither exists
with an External API discovery file:

```text
/Users/admin/Library/Application Support/Tableau/Tableau/ExternalApi
/Users/admin/Library/Application Support/Tableau/ExternalApi
```

The read-only preference probe found:

```text
Settings.ExternalApiEnabled => 0
```

The official External Client API notes state that when access is disabled,
Desktop runs no listener and publishes no discovery file. This is the concrete
blocker. The installed process is also identified as `edition: "unlicensed"`
in its crash-report metadata, consistent with the project’s Free Edition
environment.

## Capability classification

The MCP surface exposes the requested capabilities, but Desktop-dependent
operations remain unverified because no live session was discovered.

| Capability | Classification | Evidence |
|---|---|---|
| Reading workbook metadata | `AVAILABLE_NOT_YET_VERIFIED` | `get-workbook-inventory`, `get-workbook-xml` and related tools were listed; no session was available. |
| Listing data sources | `AVAILABLE_NOT_YET_VERIFIED` | `list-workbook-datasources` was listed; no live call was possible. |
| Reading fields | `AVAILABLE_NOT_YET_VERIFIED` | `list-available-fields` was listed; it requires a live or cached workbook. |
| Creating worksheets | `AVAILABLE_NOT_YET_VERIFIED` | `add-worksheet` and template authoring tools were listed; no write was attempted. |
| Applying chart templates | `AVAILABLE_NOT_YET_VERIFIED` | Template discovery passed, but binding/apply requires a Desktop session. |
| Building dashboards | `AVAILABLE_NOT_YET_VERIFIED` | `add-dashboard`, `apply-dashboard` and dashboard batch tools were listed; no write was attempted. |
| Managing actions/interactivity | `AVAILABLE_NOT_YET_VERIFIED` | `author-action` was listed; no write was attempted. |
| Reading dashboard definitions | `AVAILABLE_NOT_YET_VERIFIED` | `list-dashboards` and `get-dashboard-xml` were listed; no session was available. |
| Saving native Tableau workbooks | `AVAILABLE_NOT_YET_VERIFIED` | `save-workbook` was listed; no workbook was created or saved. |
| Exporting screenshots/images | `AVAILABLE_NOT_YET_VERIFIED` | Dashboard/worksheet image export tools were listed; no live export was attempted. |

No requested authoring capability was absent from `tools/list`; the live API
connection needed to verify those capabilities is unavailable in the current
Desktop process.

## Safety and project state

- No Accessibility, Screen Recording or Apple Events permission was enabled.
- No computer-use or mouse automation fallback was enabled.
- No Tableau MCP source code was changed.
- No `add-*`, `apply-*`, `author-*`, `save-*` or workbook XML write tool was
  called.
- The analytical project’s DuckDB database, CSV exports, approved dashboard
  design and source crosswalks were not modified.
- No `.twb`, `.twbx`, screenshot, remote, upload or publication was created.

## Blocker and next approved action

Stop condition: the Tableau Desktop External Client API is disabled, so the
MCP cannot discover a session. Enabling the existing
`Settings.ExternalApiEnabled` preference and restarting Tableau would require
explicit owner approval under the Batch 22.2 authorization boundary. Until
that approval and a successful `list-instances` call, native dashboard
authoring is not verified and Batch 22 must not start.

## Reconnect and removal

After an approved API change and a Tableau Desktop restart, confirm the local
registration with:

```bash
codex mcp list
```

Then relaunch/reload the Codex VS Code extension if the new server is not yet
visible and repeat the read-only handshake starting with `list-instances`.
The detected PID must be passed as `session` to the live tools.

The supported removal command is:

```bash
codex mcp remove tableau-desktop
```

Re-adding it uses the same `codex mcp add tableau-desktop --env
PRODUCT_TELEMETRY_ENABLED=false -- ...` command recorded above. No removal was
performed in this batch.

## Official references

- [Tableau MCP repository](https://github.com/tableau/tableau-mcp)
- [Tableau Desktop Authoring MCP README](https://github.com/tableau/tableau-mcp/blob/main/docs/README.desktop.md)
- [Tableau External Client API layer](https://github.com/tableau/tableau-mcp/blob/main/src/desktop/externalApi/README.md)
