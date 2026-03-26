# Environment

Environment variables, external dependencies, and setup notes.

**What belongs here:** required env vars, local dependency notes, platform-specific caveats, packaging/runtime constraints.  
**What does NOT belong here:** service ports/commands (use `.factory/services.yaml`).

---

- Platform target: Windows desktop app using PySide6.
- Current runtime: `python 3.10.x`.
- Current repo is **not** a git repository; branch status must be explicit when unavailable.
- In the current Windows worker environment, `sh` may be unavailable even though `.factory/init.sh` exists. If startup setup is needed, run the script's Python body directly to create `tests/__init__.py`.
- The mission must remain local-only: no database, no backend service, no runtime network dependency.
- Terminal integration may add Python/package requirements during implementation:
  - `pywinpty`
  - any PySide6 WebEngine usage must rely on locally available PySide6 modules
- Terminal frontend assets must be vendored locally in the repo; do not rely on a CDN.
- If workspace selection is canceled or a persisted workspace path is invalid, the UI must remain explicit and truthful instead of silently falling back to the current working directory.
