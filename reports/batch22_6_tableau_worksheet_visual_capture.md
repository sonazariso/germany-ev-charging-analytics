# Batch 22.6 — Tableau Worksheet Visual Capture

**Date:** 2026-11-03
**Scope:** read-only visual capture of the existing Tableau Desktop 2026.3
window through the VS Code/Codex macOS host.
**Result:** `CANVAS_VISIBLE: NO`; `VISUAL_INTERACTION_NO_GO`; the project
remains `TABLEAU_WORKBOOK_NOT_YET_CREATED`.

## Executive result

The full-display macOS screenshot primitive works, but the visible Tableau
window body is not present in the capture. The screen contains the Tableau
menu bar over the desktop wallpaper; the 960 × 628 Tableau window body is
omitted. A native window-targeted `screencapture -l` call fails with
`could not create image from window`. A rectangle capture over the exact
window bounds also contains only the wallpaper.

CoreGraphics reports that the on-screen Tableau window has sharing state `0`
(`kCGWindowSharingNone`). This is the exact native capture limitation: the
window can be listed and activated, but its pixels are not made available to
the screen/window capture path. A one-time ScreenCaptureKit fallback from an
ad hoc Swift process was also denied by that process's TCC state; no
permission was changed or retried.

The Tableau menu state gives limited nonvisual evidence that the existing
`Tableau - Book10` window is in a worksheet context: `Window → Sheet 1` is
enabled and the Data menu lists `national_charging_2026_09_30` as an enabled
data source. That does not make the worksheet canvas visible. The capture and
Accessibility results show no canvas, Rows/Columns shelves, Marks card, Data
pane, field list or worksheet-tab controls that could safely ground a visual
interaction.

## Read-only activation and precondition

Batch 22.5 and the current project status were read before the probe. Tableau
was already running at:

```text
/Applications/Tableau Desktop 2026.3.app/Contents/MacOS/Tableau
PID 69858
window: Tableau - Book10
```

System Events set the existing Tableau process frontmost. No menu item,
coordinate, worksheet, field, data source, save command or workbook control
was activated. The window metadata was obtained without changing the
workbook:

| Property | Observed value |
|---|---|
| CoreGraphics window ID | `8660` |
| On screen | `true` |
| Layer / alpha | `0` / `1.0` |
| Bounds | `x=188, y=76, width=960, height=628` |
| Window sharing state | `0` (`kCGWindowSharingNone`) |
| Accessible title | `Tableau - Book10` |
| Accessible document element | `Book10.twb` |

## Capture methods and results

All temporary images were written under `/tmp/tableau-22-6.*`, outside the
tracked project directories, and were not added to Git.

### Full visible display

The native command was:

```bash
/usr/sbin/screencapture -x /tmp/tableau-22-6.*/full-screen.png
```

The command produced a valid 2560 × 1600 PNG. Its visible content was the
Tableau menu bar (`Tableau`, `File`, `Data`, `Worksheet`, `Dashboard`,
`Story`, `Analysis`, `Map`, `Format`, `Server`, `Window`, `Help`) over the
desktop wallpaper. No Tableau window body or worksheet pixels were visible.

### Native window-targeted capture

The supported window-ID form was attempted with window ID `8660`:

```bash
/usr/sbin/screencapture -x -l 8660 /tmp/tableau-22-6.*/tableau-window.png
```

It failed immediately with:

```text
could not create image from window
```

No window PNG was created. The failure is consistent with the CoreGraphics
sharing state `0` rather than with an incorrect window ID: the same ID is
reported on-screen with the expected bounds.

### Exact-bounds control capture

The known window rectangle was captured separately:

```bash
/usr/sbin/screencapture -x -R 188,76,960,628 \
  /tmp/tableau-22-6.*/tableau-window-rectangle.png
```

This produced a 1920 × 1256 Retina PNG, but the image contained only the
desktop wallpaper. It is a useful control result, not a successful Tableau
window capture.

### ScreenCaptureKit fallback

The current macOS SDK marks direct `CGWindowListCreateImage` use obsolete and
points to ScreenCaptureKit. A read-only ScreenCaptureKit window attempt was
made once. The ad hoc Swift process received:

```text
Error Domain=com.apple.ScreenCaptureKit.SCStreamErrorDomain Code=-3801
"The user declined TCCs for application, window, display capture"
```

No TCC setting was changed, and the fallback was not retried. The successful
`/usr/sbin/screencapture` display capture remains the authoritative capture
result for the current VS Code/Codex host.

## Visual and Accessibility comparison

| Inspection target | Result |
|---|---|
| Tableau menu bar | Visible in the full-display capture |
| Tableau window body | Not visible in either the display or exact-bounds capture |
| Actual worksheet canvas | Not visually visible |
| Rows shelf / Columns shelf | Not visible and not exposed as named Accessibility elements |
| Marks card | Not visible and not exposed as a named Accessibility element |
| Data pane / field list | Not visible and not exposed as named Accessibility elements |
| Worksheet tab strip | Not visible; no `AXTab` or `AXTabGroup` was exposed |
| Logical worksheet context | Limited menu evidence: enabled `Sheet 1`, listed charging data source and worksheet menu |
| Start/Data Source page distinction | Cannot be visually confirmed because the window body is excluded |

The accessible window tree exposed close, full-screen and minimize buttons,
two unnamed groups, the `Book10.twb` document image and the
`Tableau - Book10` title. It did not expose a field pane, worksheet canvas or
named shelf/card controls. The menu evidence is enough to say that Tableau
has an active worksheet context, but not enough to inspect or operate the
canvas safely.

## Feasibility and recommendation

Screenshot-based interaction is not reliable under the current host. A
coordinate click or drag would be ungrounded because the pixels being acted
on are unavailable to the capture path, and Accessibility does not supply the
missing worksheet controls. No safe visual interaction plan is proposed and
no interaction was attempted.

Stop pursuing local GUI visual automation with this capture setup. Reconsider
only after either a supported Tableau External Client API configuration passes
its live readback gate or an owner-approved host can capture the Tableau
window body with verified permissions and window sharing. Do not create the
two Executive Overview dashboards through blind coordinate automation.

## Safety and invariants

- No workbook, worksheet, dashboard, field, data source, preference, source
  file, export, database object or permission changed.
- The official Tableau MCP was not retried.
- No package was installed, no ChatGPT Work operation was used, and no
  external remote, upload or publication occurred.
- Temporary diagnostic images remain outside tracked project directories.

## Requested return values

```text
CANVAS_VISIBLE: NO
Screenshot method that worked: /usr/sbin/screencapture full-display capture (2560 × 1600); native window capture with -l failed because Tableau reports sharing state 0.
Actual visible Tableau controls: menu bar only; Accessibility also exposes the window chrome, Book10.twb document image and title. Rows/Columns shelves, Marks card, Data pane, fields and worksheet tabs are not visible/exposed.
Visual interaction feasibility: NO-GO; screenshot-based coordinate interaction cannot be safely grounded.
Recommendation: NO-GO for the current local GUI capture route; wait for a supported API or a separately approved host with verified window capture.
```
