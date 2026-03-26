# Architecture

Architectural decisions, module boundaries, and implementation notes for the PySide6 IDE shell upgrade.

**What belongs here:** state-model decisions, widget responsibilities, composition boundaries, cross-surface coordination rules.  
**What does NOT belong here:** validation flow details (use `user-testing.md`) or raw research dumps (use `.factory/research/`).

---

## Current shell shape to preserve

- `Activity Bar`
- `Side Bar`
- `Editor Area`
- `Bottom Panel`
- `Status Bar`

The information architecture stays intact. Workers should refactor the implementation, not replace the product shape.

## State-model direction

The upgraded shell should have explicit state for:

- workspace path / availability
- open editor sessions
- active file/session
- dirty state per session
- cursor position
- active side-bar panel
- active bottom-panel panel

Prefer small explicit data types over ad hoc widget-only state.

## MainWindow boundary

`MainWindow` should:

- compose major widgets
- register commands/actions
- connect signals
- coordinate shared state updates

`MainWindow` should not remain the long-term home for file I/O rules, editor-session truth, or terminal internals.

## Sidebar boundary

- Explorer must be driven by real filesystem state.
- No-workspace state must be explicit.
- `QFileSystemModel` defaults its root path to `.`; when no workspace is selected, explicitly reset the model with an empty root path and an invalid tree root index so the Explorer does not silently fall back to the process working directory.
- Non-Explorer panels remain professional empty states for this mission; do not fake search results, git state, debugger state, or extensions data.

## Editor boundary

- Empty state is first-class, not a hidden label behind fake tabs.
- File identity must be path-backed when saved, explicit when unsaved.
- Duplicate open for the same path should focus the existing session.

## Bottom panel boundary

- Use a dedicated selector + content stack design.
- Public behavior should use semantic panel identifiers, not raw numeric indices.
- Output / Problems are state views, not pseudo-editors for fake content.

## Terminal boundary

- Real shell session or explicit failure only.
- No fake prompt or canned transcript.
- Terminal must be workspace-aware and must stay truthful across no-workspace, init failure, hide/show, and restart scenarios.
