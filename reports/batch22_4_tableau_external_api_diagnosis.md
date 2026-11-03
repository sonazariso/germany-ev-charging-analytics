# Batch 22.4 — Tableau External Client API diagnosis

**Date:** 2026-11-03
**Scope:** read-only diagnosis after the Batch 22.3 startup reset
**Result:** `ROOT_CAUSE_CONFIRMED_STARTUP_FREE_EDITION_INITIALIZATION` for the
observed reset mechanism; `SUPPORTED_API_ACTIVATION_NOT_ESTABLISHED` for this
installation; `TABLEAU_WORKBOOK_NOT_YET_CREATED` remains unchanged.

## Executive conclusion

The immediate reset is confirmed: Tableau Desktop 2026.3.0 accepts the
owner-approved integer write of `Settings.ExternalApiEnabled=1` before launch,
then restores the value to integer `0` while initializing the installed
runtime. The same startup records `FreeEditionActive`, and no External Client
API discovery file or listener appears. This is strong evidence that the
runtime's edition/licensing initialization gate disables the setting during
startup.

The exact internal product rule connecting `FreeEditionActive` to this
preference is not published in the local logs or in the official MCP source;
the report therefore distinguishes the confirmed reset behavior from the
undocumented internal condition. No evidence supports a system preference,
managed profile, MCP configuration, type mismatch, binary problem or stale
discovery file as the cause.

No official Tableau documentation found in this investigation describes
`Settings.ExternalApiEnabled`, promises External Client API availability for
Free Edition, or provides a supported Free Edition switch for keeping this
API enabled. Free Edition is documented as a local authoring/storage mode;
paid licensing supports broader sharing/server/cloud functionality. That is
not enough to claim that activating a paid entitlement will automatically
enable this API, so the safe next step is an owner-approved licensing/support
decision rather than another preference attempt.

## Evidence and interpretation

| Evidence | Observed result | Interpretation |
|---|---|---|
| Batch 22.3 controlled write | The exact user-domain integer changed `0 → 1` and read back as `1` before launch. | The key, domain and value type are valid; the write itself was not rejected. |
| Batch 22.3 startup | Tableau restored the value to `0`; both documented discovery locations stayed absent; MCP `list-instances` failed. | The reset occurs during application startup and prevents the live bridge. |
| Tableau startup log | The launch recorded `Desktop free edition mode active`, `FreeEditionActive`, and `ATR or Desktop free edition enabled: 1`. | Edition initialization is the only direct startup signal correlated with the reset. |
| Local preference precedence | The target key exists only in the user plist. No matching system/ByHost/managed key or MDM enrollment was found. | A higher-precedence preference or managed policy is not supported by local evidence. |
| App and library inspection | The signed app is `com.tableausoftware.tableaudesktop`, version `2026.3.0`; the bundle contains the External Client API libraries. | The API implementation is installed; the failure is runtime availability, not a missing framework. |
| Official MCP source | The clean checkout at `../tools/tableau-mcp` is pinned to `v5.3.0`; the local OpenAPI fixture is version `0.2.28`, and the source contains no `Settings.ExternalApiEnabled` or Free Edition activation rule. | The MCP documents the API contract, not a supported switch for this Tableau edition. |
| Official MCP contract | The v5.3.0 contract says that with access off Desktop publishes no listener and no discovery file. | The absent discovery file is the expected result of an API-disabled runtime. |

The relevant local artifacts are outside Git where appropriate: the Tableau
startup log is under `~/Documents/My Tableau Repository/Logs/`, and the
verified plist backup is under
`../germany-ev-charging-analytics-private/tableau-settings-backups/20261103_210231/`.
No secret, token, email address or signed entitlement payload is reproduced
here.

### Hypothesis audit

1. **Startup licensing/edition gate — confirmed as the immediate mechanism.**
   The controlled pre-launch value, post-launch value, startup edition lines
   and missing discovery file form a consistent sequence. The undocumented
   internal conditional should not be stated more narrowly than this evidence
   allows.
2. **Managed/system preference override — not supported.** The user plist is
   the only readable plist containing the key; the system plist contains no
   matching setting; managed-preference paths are absent; the Mac is not MDM
   enrolled.
3. **Wrong domain, wrong type or stale alternate domain — rejected.** The
   exact Tableau 2026.3 domain and integer type accepted the write, while the
   alternate `com.tableausoftware.tableaudesktop` preferences contain no
   target key.
4. **MCP build/configuration failure — rejected for this symptom.** The pinned
   Desktop build initializes, exposes its tools and passes headless template
   discovery. Its source contract independently predicts no discovery file
   when Desktop access is off.
5. **Startup race or an undocumented secondary product condition — possible
   but unproven.** The logs do not print the exact preference-reset statement,
   so no source-level explanation beyond the observed edition gate is claimed.

## Official support and activation finding

The official sources reviewed were:

- [Tableau MCP Desktop build documentation](https://github.com/tableau/tableau-mcp/blob/v5.3.0/docs/README.desktop.md), which requires a running Tableau Desktop instance for the separate Desktop build.
- [Tableau MCP External Client API notes](https://github.com/tableau/tableau-mcp/blob/v5.3.0/src/desktop/externalApi/README.md) and the [v5.3.0 API contract](https://github.com/tableau/tableau-mcp/blob/v5.3.0/src/desktop/externalApi/__fixtures__/externalClientApi-openapi.json), which document loopback discovery and the no-listener/no-discovery behavior when access is disabled.
- Tableau's [Desktop edition comparison](https://help.tableau.com/current/pro/desktop/en-us/desktop_comparison.htm), [license activation guidance](https://help.tableau.com/current/pro/desktop/en-us/license_activation.htm), [activation methods](https://help.tableau.com/current/desktopdeploy/en-us/desktop_deploy_activate_license.htm), and [Desktop release notes](https://help.tableau.com/current/pro/desktop/en-us/whatsnew_desktop.htm).

Those sources establish the following boundaries:

- Free Edition is a supported local Desktop mode with local storage and live
  data use. It does not require paid-product activation for that local mode.
- Product-key activation, online/offline activation and login-based licensing
  are documented for paid Tableau products and broader sharing/server/cloud
  functionality. The owner must use Tableau's supported licensing flow if a
  paid entitlement is available.
- No reviewed official source documents `Settings.ExternalApiEnabled`, a
  Free Edition exception for the External Client API, or a supported way to
  force this setting to remain enabled in the current runtime.

Therefore the supported activation method for the **current Free Edition
state is not established**. Do not retry `defaults`, use a command-line
override, edit the plist repeatedly, patch binaries, inject code, fabricate
credentials, or bypass macOS security. If the owner has a paid Creator or
equivalent entitlement, the owner may separately activate the supported
Tableau Desktop edition through Tableau's documented flow and then request a
fresh read-only API compatibility check. That is a licensing decision, not an
activation method verified by this batch.

## MCP value and recommendation

The official Desktop MCP is not worthwhile as a live authoring route while
this Free Edition runtime suppresses the External Client API. Its build,
registration and headless template catalog remain useful evidence, but they do
not provide workbook access. Keep the isolated build and configuration
unchanged; pause further MCP enablement attempts until either:

- Tableau/owner confirms a supported licensed Desktop configuration that
  exposes the External Client API; or
- the owner explicitly chooses the GUI fallback below.

Only after a live `list-instances` call, app/capability readback and disposable
workbook readback pass should the two approved dashboards be authored.

## GUI fallback assessment

Manual Tableau Desktop authoring is technically feasible in Free Edition for a
local workbook because the documented local mode supports local storage and
live data. It has not been executed in this batch. The current Codex
configuration shows the computer-use and `cua_repl` entries disabled, and no
GUI-control tool is available in this session.

An owner-approved GUI host would need, as applicable:

- **Accessibility** permission for UI inspection/control; Apple documents that
  this allows an app to control the Mac through accessibility APIs.
- **Screen & System Audio Recording** for visual grounding or screenshots.
- **Automation** only if the chosen host uses Apple Events/AppleScript.
- Normal user access to the local project and a disposable Tableau workbook
  directory.

These permissions expand the control and observation surface. If approved,
use an isolated/disposable workbook, do not enter secrets into unrelated
windows, do not publish or upload, and keep the native save verification
local. The minimum smoke test is:

1. Open a blank workbook and attach the approved CSV sources as separate data
   sources.
2. Create one simple worksheet and one disposable dashboard.
3. Save a local `.twb` and verify that the file exists and is non-empty.
4. Close and reopen it in Tableau Desktop; verify the sheet/dashboard names,
   source paths and a screenshot at the target canvas size.
5. Stop if any source, map, label or save result is ambiguous. Do not create a
   packaged `.twbx` or publish until source licensing and owner approval are
   separately complete.

The GUI path is therefore **feasible but approval-gated**, with higher
interaction and privacy risk than the loopback MCP. The least-interaction
owner decision is one of: provide/confirm a supported paid Desktop entitlement
for a new API smoke test, or approve one isolated GUI host with the required
macOS permissions for a disposable local authoring test.

## Invariants and handoff

- `Settings.ExternalApiEnabled` remains `0`; no further enablement or restart
  was performed in Batch 22.4.
- No MCP package/configuration, macOS permission, binary, workbook, DuckDB
  object, source file, export, screenshot, remote, upload or publication
  changed.
- The Tableau workbook remains `TABLEAU_WORKBOOK_NOT_YET_CREATED`.
- The existing preference backup remains preserved outside Git.
- The official KPI/data model, BBSR layers, Crosswalk and Tableau CSV contracts
  remain unchanged. No KPI/schema documentation was changed because this
  diagnosis affects only the blocked authoring bridge.
