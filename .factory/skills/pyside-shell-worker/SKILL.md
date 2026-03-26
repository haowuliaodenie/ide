---
name: pyside-shell-worker
description: Implement PySide6 IDE shell features, state models, workspace/editor flows, styling, and offscreen validation.
---

# PySide Shell Worker

NOTE: Startup and cleanup are handled by `worker-base`. This skill defines the work procedure for PySide6 IDE shell features.

## When to Use This Skill

Use this skill for features that modify:

- shell state models
- `MainWindow` composition / command wiring
- Activity Bar / Side Bar / Explorer behavior
- Editor sessions and file workflows
- Bottom Panel structure excluding the PTY/WebEngine terminal bridge
- Status Bar behavior
- persistence / `QSettings`
- theme tokenization / QSS cleanup
- offscreen `unittest` coverage for desktop shell behavior

## Required Skills

None.

## Work Procedure

1. Read `mission.md`, `validation-contract.md`, `AGENTS.md`, `.factory/services.yaml`, and relevant `.factory/library/*.md` files before changing code.
2. Inspect the current implementation in the exact files touched by the feature. Preserve the existing information architecture; refactor from the current structure instead of rewriting the entire app.
3. Write or update failing `unittest` coverage first for the assertions this feature fulfills. Prefer focused offscreen tests under `tests/`.
4. Implement the feature using explicit state and low-coupling boundaries:
   - keep `MainWindow` as composition/signal/command wiring layer
   - avoid reintroducing raw positional panel semantics where named panel state is required
   - do not ship fake data, fake success, or silent fallback behavior
5. Run the most targeted tests for the feature first. If they pass, run the broader project checks from `.factory/services.yaml`.
6. Perform at least one offscreen runtime sanity check for the affected user flow, not just pure unit assertions.
7. If the feature touches visible copy or empty/error states, inspect all relevant reachable panels/tabs to ensure no `Placeholder` or prototype text remains.
8. If the feature touches persistence, verify both normal restore and invalid-state recovery paths.
9. Stop and return to the orchestrator if:
   - requirements conflict with the mission boundary
   - a dependency or asset is missing and the truthful UI behavior cannot be completed
   - an unrelated pre-existing issue prevents verification

## Example Handoff

```json
{
  "salientSummary": "Implemented workspace-aware Explorer and path-backed editor sessions, replacing fake startup tabs and wiring menu actions into the real workflows. Added targeted offscreen tests for workspace selection, file open, new/save flows, and active-session synchronization.",
  "whatWasImplemented": "Added explicit workspace/editor session state, refactored MainWindow to coordinate named panel and command routing, rebuilt the Explorer no-workspace state plus real filesystem activation path, and upgraded EditorArea to handle untitled sessions, dirty state, save/save-as, close resolution, and empty-state restoration.",
  "whatWasLeftUndone": "",
  "verification": {
    "commandsRun": [
      {
        "command": "python -m unittest tests.test_sidebar_workspace -v",
        "exitCode": 0,
        "observation": "Workspace selection, explorer reroot, and file-activation tests passed."
      },
      {
        "command": "python -m unittest tests.test_editor_sessions -v",
        "exitCode": 0,
        "observation": "Open/new/save/dirty/close session tests passed."
      },
      {
        "command": "python -m compileall -q main.py src tests",
        "exitCode": 0,
        "observation": "Source tree compiled without syntax errors."
      }
    ],
    "interactiveChecks": [
      {
        "action": "Instantiated MainWindow in QT_QPA_PLATFORM=offscreen, selected a temporary workspace, and activated a real file from Explorer.",
        "observed": "Explorer rerooted correctly, the file opened in the editor, and status context switched to the active session."
      },
      {
        "action": "Created an untitled file, edited it, canceled save-as once, then completed save-as into the workspace.",
        "observed": "Dirty state remained after cancel, the active session adopted the chosen path in place after save, and Explorer reflected the new file."
      }
    ]
  },
  "tests": {
    "added": [
      {
        "file": "tests/test_editor_sessions.py",
        "cases": [
          {
            "name": "test_duplicate_open_reuses_existing_session",
            "verifies": "Opening the same path twice focuses the existing editor tab instead of duplicating it."
          },
          {
            "name": "test_save_as_cancel_keeps_untitled_dirty_session",
            "verifies": "Canceling the save path chooser leaves the session open, dirty, and pathless."
          }
        ]
      }
    ]
  },
  "discoveredIssues": []
}
```

## When to Return to Orchestrator

- The feature requires a new dependency or packaging decision not already covered by mission guidance
- A truthful implementation would require violating the “no fake fallback” boundary
- Validation depends on a missing external capability the worker cannot restore
- The feature naturally splits into a new dedicated follow-up because the current scope has become too large for one session
