---
name: terminal-integration-worker
description: Implement the integrated Windows terminal panel using the approved PTY/WebEngine/xterm.js stack with truthful failure states and cleanup.
---

# Terminal Integration Worker

NOTE: Startup and cleanup are handled by `worker-base`. This skill defines the work procedure for the integrated terminal feature.

## When to Use This Skill

Use this skill for features that modify:

- the Terminal panel itself
- PTY / ConPTY integration
- `QtWebEngine` / `QWebChannel` terminal embedding
- vendored terminal frontend assets
- terminal-specific tests and runtime checks
- terminal-related error/no-workspace states

Do not use this skill for generic editor/sidebar/status/persistence work unless it is inseparable from terminal behavior.

## Required Skills

None.

## Work Procedure

1. Read `mission.md`, `validation-contract.md`, `AGENTS.md`, `.factory/services.yaml`, `.factory/library/terminal.md`, and `.factory/research/terminal-stack.md` before changing code.
2. Confirm the approved stack and boundaries:
   - real session or explicit failure only
   - no runtime CDN
   - no fake prompt or transcript fallback
3. Add failing tests first for the fulfilled terminal assertions. Cover:
   - no-workspace state
   - dependency/init failure state
   - successful startup path if available
   - truthful restoration behavior when the panel is hidden/shown
4. Vendor or wire terminal assets locally and add Python dependencies truthfully.
5. Implement the PTY/WebEngine bridge with explicit lifecycle management:
   - workspace-aware startup
   - explicit failure reporting for missing PTY/WebEngine/WebChannel/assets
   - process cleanup on shutdown / feature verification
6. Validate the success path if the environment supports it. If not, validate the explicit failure path and return a clear handoff describing what prevented success-path verification.
7. Run targeted tests, then broader project checks from `.factory/services.yaml`.
8. Ensure no terminal process is left running after verification.

## Example Handoff

```json
{
  "salientSummary": "Implemented the Bottom Panel terminal using the approved PTY/WebEngine stack with explicit no-workspace and dependency-failure states. Added targeted terminal tests and verified the panel no longer falls back to a fake prompt transcript.",
  "whatWasImplemented": "Added terminal session/controller code, vendored local xterm.js assets, wired a QWebEngine/QWebChannel terminal host, surfaced explicit error states for missing dependencies and no-workspace startup, and integrated terminal reveal/restore behavior with the semantic Bottom Panel API.",
  "whatWasLeftUndone": "",
  "verification": {
    "commandsRun": [
      {
        "command": "python -m unittest tests.test_terminal_panel -v",
        "exitCode": 0,
        "observation": "Terminal no-workspace, init-failure, and restore tests passed."
      },
      {
        "command": "python -m compileall -q main.py src tests",
        "exitCode": 0,
        "observation": "Terminal integration modules compiled successfully."
      }
    ],
    "interactiveChecks": [
      {
        "action": "Opened a workspace and activated the Terminal panel.",
        "observed": "A real session started with cwd bound to the workspace and no fake prompt text was present."
      },
      {
        "action": "Activated Terminal with no workspace selected.",
        "observed": "The panel showed an explicit no-workspace state instead of inventing a current directory."
      }
    ]
  },
  "tests": {
    "added": [
      {
        "file": "tests/test_terminal_panel.py",
        "cases": [
          {
            "name": "test_terminal_requires_workspace_or_explicit_no_workspace_state",
            "verifies": "Terminal does not fabricate a cwd when no workspace is selected."
          },
          {
            "name": "test_terminal_failure_state_is_explicit",
            "verifies": "Missing PTY/WebEngine/assets surface an explicit terminal error instead of a fake prompt."
          }
        ]
      }
    ]
  },
  "discoveredIssues": []
}
```

## When to Return to Orchestrator

- The environment cannot provide a truthful success path and the explicit failure path still cannot be rendered correctly
- Required terminal assets or dependencies introduce a broader packaging decision outside the feature scope
- A child-process cleanup issue cannot be resolved safely within the session
- WebEngine/PTy behavior is blocked by an external system constraint the worker cannot fix
