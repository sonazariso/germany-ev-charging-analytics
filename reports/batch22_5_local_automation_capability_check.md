# Batch 22.5 — Local Tableau GUI automation capability check

**Date:** 2026-11-03
**Scope:** Read-only macOS host, permission and capability investigation for
Tableau Desktop GUI automation through the VS Code Codex host.
**Result:** `LOCAL_AUTOMATION_PARTIAL`
**Project state:** `TABLEAU_WORKBOOK_NOT_YET_CREATED`

## Executive result

The local GUI fallback is operational at the host and permission layer, but it
is not yet a reliable Tableau authoring path. The shell used for this batch is
a child of the VS Code OpenAI Codex extension. Its read-only System Events and
native Accessibility probes can see Tableau's process, window title, window
controls and start-pane controls. The built-in macOS screenshot command also
captured a 2560 × 1600 PNG successfully.

The live blank Tableau window did not expose a named worksheet-tab strip or
field pane. Its Accessibility tree exposed the window/menu chrome, `New
Worksheet (⌘T)`, `Clear Sheet (⌥⇧⌫)`, a `Tables` outline and activation/start
pane content, but no `AXTab` or `AXTabGroup` worksheet controls and no field
pane controls. The screenshot showed Tableau's menu bar over the desktop but
no rendered worksheet canvas. A worksheet was not created, a tab was not
selected, and no chart, data source or workbook was edited.

This is therefore a partial pass for local automation prerequisites, not an
authoring pass. The existing Tableau External Client API preference remains
`0`; no permission, MCP, workbook, source, export, database or project-data
change was made.

## Phase 1 — host and built-in automation inventory

### Exact Codex automation host

The active shell for this batch reported the following parent chain:

| Component | Observed value |
|---|---|
| macOS | 15.8.1, build 24H32 |
| VS Code application | `/Applications/Visual Studio Code.app` |
| VS Code OpenAI extension host | `Code Helper (Plugin)` under the VS Code application |
| Codex app-server | `/Users/admin/.vscode/extensions/openai.chatgpt-26.1021.22027-darwin-x64/bin/macos-x86_64/codex` |
| Codex PID during the probe | `63398` |
| Codex code-mode child | `/Users/admin/.vscode/extensions/openai.chatgpt-26.1021.22027-darwin-x64/bin/macos-x86_64/codex-code-mode-host`, PID `63556` |
| Probe shell relationship | The shell running the checks had PPID `63398` |

The separate ChatGPT application and its computer-use service were visible in
the process inventory but were not invoked. No ChatGPT Work/CUA operation was
used for this batch.

The following built-in tools are present; no package was installed:

| Built-in option | Result |
|---|---|
| `/usr/bin/osascript` | Available; System Events UI scripting succeeded. |
| System Events UI scripting | Available; read Tableau windows and controls, set Tableau frontmost, and invoked the normal Quit menu. |
| macOS Accessibility APIs | Available; Swift `ApplicationServices` probe traversed the Tableau AX tree. |
| `/usr/sbin/screencapture` | Available; temporary PNG capture succeeded. |
| `/usr/bin/swift` and `/usr/bin/swiftc` | Available for native Accessibility API probes. |
| TCC database inspection | Direct read-only SQLite query was denied by macOS with `authorization denied`; no bypass was attempted. |

### Effective permission status

These are effective operation results, not claims based on a readable TCC
database row:

| Permission/capability | Status | Evidence |
|---|---|---|
| Accessibility | **PASS for the current VS Code/Codex host** | System Events read Tableau's window and controls; the native AX probe read an `AXApplication`, `AXWindow`, menu bar, buttons and nested controls, visiting 339 nodes. |
| Screen Recording | **PASS for the current host** | `/usr/sbin/screencapture` created a valid 2560 × 1600 RGBA PNG. |
| Apple Events / Automation | **PASS for System Events** | `osascript` queried visible applications, read Tableau UI state, brought Tableau frontmost and sent the normal Quit menu action. Direct Tableau authoring AppleScript was not required or attempted. |

No macOS privacy setting was changed. If a different host is used later and a
permission is denied, the relevant macOS location is **System Settings →
Privacy & Security**:

- **Accessibility:** add/enable the actual automation host, normally Visual
  Studio Code when the VS Code Codex extension owns the shell.
- **Screen & System Audio Recording** (named Screen Recording on some macOS
  versions): add/enable the actual host for visual screenshots.
- **Automation:** allow the host to control **System Events** only if the
  selected implementation uses Apple Events/System Events.

## Phase 2 — safe Tableau capability test

Tableau was not running during preflight. It was launched normally from
`/Applications/Tableau Desktop 2026.3.app`, without command-line flags or a
workbook path. The observed Tableau process was:

```text
/Applications/Tableau Desktop 2026.3.app/Contents/MacOS/Tableau
```

with PID `69292`. Tableau opened a blank unsaved window titled:

```text
Tableau - Book1
```

The window was reported as a focused, non-minimized `AXStandardWindow`, with a
960 × 628 accessible window size. The native AX probe found 339 nodes. It
identified:

- the Tableau application and window;
- the Tableau, File, Data, Server and Help menus;
- `New Worksheet (⌘T)` and `Clear Sheet (⌥⇧⌫)` controls;
- a start-pane `Tables` outline and activation/start-pane content;
- no `AXTab` or `AXTabGroup` worksheet-tab controls;
- no named field-pane controls.

The main-display screenshot was captured successfully, but its visible frame
contained Tableau's menu bar over the desktop and no rendered worksheet
canvas. The missing canvas is recorded as an observed UI/rendering state; it
is not attributed to a permission failure because the permission test itself
passed.

No worksheet tab selection was performed. Selecting a tab would require an
actual worksheet tab, which was not exposed in the blank start pane; creating
one would cross the explicit no-workbook-edit boundary. No fields were
dragged, no chart or data source was edited, and no workbook was saved.

The blank `Book1` created during this test was closed through Tableau's normal
Quit menu. The Tableau process exited, and the preference readback remained:

```text
Settings.ExternalApiEnabled => 0
```

## Phase 3 — feasibility assessment

| Capability | Classification | Verified evidence / limitation |
|---|---|---|
| See Tableau process and visible window title | **VERIFIED** | Process PID `69292`; title `Tableau - Book1`; AX window metadata readable. |
| Read basic Tableau UI hierarchy | **VERIFIED, LIMITED** | Menus, window controls, start-pane controls and 339 AX nodes were readable. |
| See a rendered worksheet canvas | **NOT VERIFIED** | Screenshot did not show a rendered canvas; the blank start pane exposed no worksheet tab strip. |
| Identify fields and field controls | **NOT VERIFIED** | No field pane or named field controls appeared in the blank start-pane AX tree. |
| Select worksheet tabs | **UNTESTED** | No worksheet tabs were exposed, and no workbook edit was authorized to create one. |
| Click/drag fields | **UNTESTED** | Explicitly not performed. |
| Create worksheets | **UNTESTED** | `New Worksheet` was visible to Accessibility, but it was not invoked. |
| Arrange dashboards | **UNTESTED** | No dashboard was created or changed. |
| Save native `.twb`/`.twbx` | **UNTESTED** | No workbook was saved; no native save/readback claim is made. |
| Capture screenshots | **VERIFIED for screen capture** | Valid 2560 × 1600 PNG captured; Tableau canvas content was not visually verified. |

## Safety record and decision

- No package, MCP configuration, Tableau preference, macOS permission,
  binary, workbook, datasource, chart, database object, CSV export, source
  file, remote, upload or publication changed.
- `Settings.ExternalApiEnabled` remains integer `0`.
- The official Desktop MCP was not retried; the prior External Client API
  diagnosis remains authoritative.
- No CUA/computer-use or ChatGPT Work operation was used.
- The temporary screenshot was moved to the user Trash after inspection and
  was not added to the repository.

`LOCAL_AUTOMATION_PARTIAL` is the correct result. The host and effective
permissions are sufficient for a controlled GUI smoke test, but actual
worksheet authoring controls, field interaction, dashboard layout, native
save/reopen and Tableau-canvas screenshot verification remain untested.

## Required next step

Do not start the two Executive Overview dashboards. The owner must choose one
of the following approval-gated paths:

1. provide/confirm a supported paid Tableau Desktop configuration and rerun
   the read-only External Client API handshake; or
2. explicitly approve one isolated GUI smoke test that may open a disposable
   blank workbook, create one disposable worksheet, inspect/select its tab and
   field pane, save to a temporary native path, reopen it, and remove the
   temporary artifact after verification.

Until that choice and the corresponding readback gate pass, the project
remains `TABLEAU_WORKBOOK_NOT_YET_CREATED`.
