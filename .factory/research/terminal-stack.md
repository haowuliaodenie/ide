# Terminal Stack Research

Raw research summary captured during mission planning for the Windows integrated terminal requirement.

## Recommendation

Preferred stack:

- `pywinpty`
- `xterm.js`
- `QtWebEngine` / `QWebChannel`

## Why

- `pywinpty` provides Windows PTY / ConPTY-backed shell access.
- `xterm.js` provides terminal emulation and rendering for ANSI / VT behavior.
- `QtWebEngine` / `QWebChannel` is the practical PySide6 bridge for embedding the rendered terminal in the desktop app.

## Rejected / weaker options

- `QProcess` + text widget only: not sufficient for a real integrated terminal experience.
- Pure text-area fake transcript: explicitly disallowed by the mission.
- Linux-centric terminal widgets without solid Windows/PySide6 support: higher risk for this mission.

## Validation implications

- Validate real session startup or explicit init failure.
- Validate cwd binding to the active workspace.
- Validate no-workspace behavior explicitly.
- Validate panel hide/show and restart truthfulness.

## Source trail

- `https://pypi.org/project/pywinpty/`
- `https://github.com/andfoy/pywinpty`
- `https://pyte.readthedocs.io/`
- `https://xtermjs.org/`
- `https://xtermjs.org/docs/`
- `https://doc.qt.io/qtforpython-6/PySide6/QtCore/QProcess.html`
- `https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/QWebEngineView.html`
- `https://doc.qt.io/qtforpython-6/PySide6/QtWebChannel/QWebChannel.html`
- `https://learn.microsoft.com/en-us/windows/console/creating-a-pseudoconsole-session`
- `https://learn.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences`
