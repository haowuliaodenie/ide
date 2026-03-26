# User Testing

Validation surface, flow expectations, and concurrency guidance for the PySide6 IDE shell mission.

**What belongs here:** user-testing surfaces, tooling, flow notes, resource-cost guidance, runtime gotchas discovered during validation.  
**What does NOT belong here:** general architecture notes (use `architecture.md`) or raw external research (use `.factory/research/`).

---

## Validation Surface

### Surface: PySide6 desktop UI

- Primary surface is the local desktop application launched from `main.py`.
- Default automated validation strategy is `QT_QPA_PLATFORM=offscreen` widget/integration testing using `unittest`.
- Validators should exercise:
  - startup shell composition
  - workspace selection / cancellation
  - Explorer rendering and activation
  - editor new/open/save/dirty/close flows
  - bottom-panel switching and restoration
  - status-bar updates from editor/workspace context
  - restart / persistence restoration

### Terminal-specific notes

- Terminal validation must prove one of:
  - a real session starts truthfully, or
  - an explicit no-workspace or dependency/init failure state is shown
- Validators must not accept a static transcript or prompt-like text as a real terminal.
- If a terminal session is started during validation, ensure spawned processes are cleaned up.

## Validation Concurrency

### Surface: offscreen PySide6 validation

- Measured dry-run startup/window creation overhead for the current shell prototype: roughly `75–100 MiB` per instance before terminal integration.
- Machine profile observed during planning:
  - 22 CPU cores
  - ~31.6 GiB RAM
- Planned maximum concurrent validators for this surface: **5**

### Rationale

- The machine has substantial CPU/RAM headroom.
- The shell is local-only and does not depend on external services.
- Even so, validators should remain conservative when Terminal + WebEngine coverage is active, because those checks are heavier than the baseline prototype.

## Required validation behavior

- Open all primary side-bar panels and bottom-panel tabs before concluding placeholder/prototype cleanup is complete.
- Validate command routes, not just helper methods.
- For restart scenarios, validate both:
  - valid persisted workspace/layout state
  - invalid persisted workspace-path recovery
