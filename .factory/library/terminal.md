# Terminal

Terminal implementation guidance for the integrated IDE panel.

**What belongs here:** approved terminal stack, behavior boundaries, lifecycle rules, validation notes.  
**What does NOT belong here:** raw research snippets (use `.factory/research/terminal-stack.md`).

---

## Approved direction

Use the approved stack from mission planning:

- `pywinpty` for Windows PTY / ConPTY access
- `QtWebEngine` + `QWebChannel` inside PySide6
- vendored `xterm.js` assets for terminal emulation/rendering

## Non-negotiable behavior

- Real session or explicit failure only
- No fake prompt or canned transcript
- No runtime CDN dependency for terminal assets
- No silent fallback to `QPlainTextEdit` pretending to be a terminal

## Workspace behavior

- With a selected workspace: terminal session cwd must match that workspace
- With no selected workspace: show explicit no-workspace state
- On dependency/init failure: show explicit PTY/WebEngine/WebChannel/asset-related failure state

## Lifecycle notes

- Do not orphan terminal child processes
- Hiding/showing the Bottom Panel must not silently replace a real session with fake content
- Restart restoration must remain truthful; do not show stale prompt text as if a terminal session were already live
