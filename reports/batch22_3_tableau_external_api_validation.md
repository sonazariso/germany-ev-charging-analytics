# Batch 22.3 — Tableau Desktop External Client API validation

**Date:** 2026-11-03
**Status:** `EXTERNAL_API_SETUP_PARTIAL`

## Result

The owner-approved preference change was attempted with a validated backup and
the exact user preference domain. The immediate write succeeded, but Tableau
Desktop 2026.3.0 rewrote the setting to its original disabled value during
startup. No External Client API listener or discovery file appeared, so the
official Desktop MCP could not discover a live session. No workbook authoring
or workbook inspection was performed.

The observed startup log records Tableau's `FreeEditionActive` state. This is
the strongest local explanation for the reversion, but this batch does not
claim an undocumented license rule as a causal fact. The safe conclusion is
that the supported enablement mechanism is not operational in this installed
Desktop state. No alternate command-line flag, binary edit, security bypass,
UI automation or unverified preference representation was attempted.

## Phase 1 — verified configuration source

Read-only inspection identified:

| Item | Verified value |
|---|---|
| Tableau application | `/Applications/Tableau Desktop 2026.3.app` |
| Application version/build | `2026.3.0` / `20263.26.1022.1645` |
| Preference domain | `com.tableau.Tableau-2026.3` |
| Physical preference file | `/Users/admin/Library/Preferences/com.tableau.Tableau-2026.3.plist` |
| Preference key | `Settings.ExternalApiEnabled` |
| Original value/type | `0`, integer / `CFNumber` |
| Managed-preference evidence | No matching user or system managed-preference file found |
| Restart requirement | Required; the official API contract states that Desktop launched with access off runs no listener and publishes no discovery file |

The setting is a direct user preference in the verified Tableau plist. It was
not read from a Tableau Cloud/Server endpoint, analytics extension, remote
debugger, or other API.

## Phase 2 — workbook preservation

No Tableau Desktop process was running during the preflight, and the
read-only AppleScript probe reported no running Tableau application or open
documents. Therefore there was no existing unsaved workbook to save before the
restart. The later launch did not receive any workbook mutation call; the
process was closed through a graceful quit request after validation failed.

## Phase 3 — preference backup

The exact verified plist was copied outside Git before editing:

```text
/Users/admin/dev/germany-ev-charging-analytics-private/tableau-settings-backups/20261103_210231/com.tableau.Tableau-2026.3.plist
```

- Backup timestamp: `2026-11-03 21:02:31 Europe/Berlin`
- Original SHA-256: `52429b40379e3ca181078614209916d7a92674a47479b1e8b3ce00e1551c3736`
- Backup SHA-256: `52429b40379e3ca181078614209916d7a92674a47479b1e8b3ce00e1551c3736`
- Byte comparison: passed
- Backup plist parse: passed
- Backup file mode: restrictive user-only permissions preserved

The backup contains only the verified Tableau preference file; it is outside
the repository and was not staged.

## Phase 4 — enablement attempt and rollback

The standard macOS user-defaults write was used against the verified domain,
with the existing integer type preserved:

```text
defaults write com.tableau.Tableau-2026.3 Settings.ExternalApiEnabled -int 1
```

Immediate validation passed: the value read back as integer `1`, and the
non-target plist entries matched the backup. After Tableau was launched, the
application rewrote the value to integer `0`. The original setting is now
restored, and the final readback is:

```text
Settings.ExternalApiEnabled => 0
```

The only non-sensitive non-target difference observed after the normal launch
was Tableau's `Settings.Startups` counter changing from `13` to `14`. The full
plist was not replaced, so unrelated application state was not rolled back
over the top of Tableau's own startup write.

## Phase 5 — restart result

- No old Tableau PID existed at preflight, so there was no prior process to
  quit or unsaved workbook to preserve.
- Tableau was launched normally from the existing application bundle.
- Observed launch PID: `66196`.
- The preference was `1` immediately before launch and `0` during/after
  startup.
- The process exited after a graceful quit request; no force-quit or
  `kill -9` was used.
- Final Tableau process state: no Tableau Desktop process running.

## Phase 6 — discovery-file verification

Neither documented location contained a discovery file after startup:

```text
/Users/admin/Library/Application Support/Tableau/Tableau/ExternalApi/
/Users/admin/Library/Application Support/Tableau/ExternalApi/
```

No discovery file was created manually, read credentials were not printed, and
no discovery file was modified.

## Phase 7 — actual MCP results

The existing Codex registration remained enabled and local:

- Server: `tableau-desktop`
- Entry point: `/Users/admin/dev/tools/tableau-mcp/build/index.desktop.js`
- Node runtime: `/Users/admin/dev/tools/node-v22.23.4-darwin-x64/bin/node`
- `PRODUCT_TELEMETRY_ENABLED=false`
- No Tableau Cloud/Server URL, PAT, OAuth secret or remote endpoint added

The official MCP calls returned:

1. `list-instances`: **failed** with `No running Tableau Desktop instances
   found.` This is consistent with the missing discovery file.
2. `list-templates`: **passed** headlessly; the catalog reported 137 total
   templates.
3. `list-available-fields`: not called because no valid Desktop session/PID
   was returned.
4. Live workbook metadata/XML/datasource inspection: not called because no
   valid Desktop session/PID was returned.

No `apply-*`, `add-*`, `author-*`, `save-*`, workbook XML write, screenshot,
dashboard, worksheet or datasource mutation tool was called.

## Security verification

- The MCP configuration remains local stdio only.
- No Tableau Cloud/Server authentication or external endpoint was added.
- No Accessibility, Screen Recording or computer-use permission was enabled
  by this batch.
- Codex still reports the computer-use and `cua_repl` entries as disabled.
- A fresh TCC database query was denied by macOS (`authorization denied`); the
  current batch therefore does not claim a fresh database-level permission
  read. Batch 22.1's prior read-only probe found no matching grants, and no
  permission-changing command was run here.
- No project DuckDB, CSV export, crosswalk, source file, workbook, screenshot,
  remote, upload or publication changed.

## Exact rollback procedure

The rollback is complete. To repeat it if needed:

1. Stop MCP calls and gracefully close Tableau Desktop.
2. Restore the original integer setting without replacing the plist:

   ```text
   defaults write com.tableau.Tableau-2026.3 Settings.ExternalApiEnabled -int 0
   ```

3. Relaunch Tableau normally if required and verify:

   ```text
   defaults read com.tableau.Tableau-2026.3 Settings.ExternalApiEnabled
   ```

4. Confirm that the result is `0` and that no External API discovery file is
   expected while access remains disabled.

The verified backup remains available for forensic comparison. It should not
be restored wholesale unless Tableau is closed and preserving unrelated
post-launch preferences has been explicitly considered.

## Outstanding limitation

The official Desktop MCP build and headless template catalog are operational,
but live Tableau Desktop connectivity is not verified. The next step requires
an official, supported way to keep External Client API access enabled in this
installed Tableau Desktop state, or a separately approved compatible Desktop
edition/build. Do not start the two Executive Overview dashboards, use UI
automation, or edit Tableau binaries until `list-instances` succeeds and a
read-only live workbook handshake passes.

## Official references

- [Tableau MCP v5.3.0 Desktop guide](https://github.com/tableau/tableau-mcp/blob/v5.3.0/docs/README.desktop.md)
- [Tableau MCP v5.3.0 External Client API source](https://github.com/tableau/tableau-mcp/blob/v5.3.0/src/desktop/externalApi/README.md)
- [Tableau MCP v5.3.0 External Client API contract](https://github.com/tableau/tableau-mcp/blob/v5.3.0/src/desktop/externalApi/__fixtures__/externalClientApi-openapi.json)
