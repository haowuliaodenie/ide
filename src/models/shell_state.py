from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4


class SideBarPanelId(str, Enum):
    EXPLORER = "explorer"
    SEARCH = "search"
    SOURCE_CONTROL = "source_control"
    RUN_AND_DEBUG = "run_and_debug"
    EXTENSIONS = "extensions"

    @property
    def title(self) -> str:
        return {
            SideBarPanelId.EXPLORER: "EXPLORER",
            SideBarPanelId.SEARCH: "SEARCH",
            SideBarPanelId.SOURCE_CONTROL: "SOURCE CONTROL",
            SideBarPanelId.RUN_AND_DEBUG: "RUN AND DEBUG",
            SideBarPanelId.EXTENSIONS: "EXTENSIONS",
        }[self]


class BottomPanelId(str, Enum):
    TERMINAL = "terminal"
    OUTPUT = "output"
    PROBLEMS = "problems"

    @property
    def title(self) -> str:
        return {
            BottomPanelId.TERMINAL: "Terminal",
            BottomPanelId.OUTPUT: "Output",
            BottomPanelId.PROBLEMS: "Problems",
        }[self]


class DirtyCloseAction(str, Enum):
    SAVE = "save"
    DISCARD = "discard"
    CANCEL = "cancel"


def _normalize_path(path: Path | None) -> Optional[Path]:
    if path is None:
        return None

    candidate = Path(path)
    try:
        return candidate.resolve(strict=False)
    except OSError:
        return candidate.absolute()


@dataclass
class WorkspaceState:
    root_path: Optional[Path] = None
    available: bool = False
    reason: str = "No workspace selected"

    def set_path(self, path: Optional[Path]) -> None:
        if path is None:
            self.root_path = None
            self.available = False
            self.reason = "No workspace selected"
            return

        self.root_path = _normalize_path(path)
        self.available = self.root_path.exists() and self.root_path.is_dir()
        self.reason = "" if self.available else "Workspace folder is unavailable"


@dataclass
class CursorState:
    line: Optional[int] = None
    column: Optional[int] = None


@dataclass
class EditorSession:
    session_id: str = field(default_factory=lambda: f"session-{uuid4().hex}")
    display_name: str = "Untitled-1"
    path: Optional[Path] = None
    content: str = ""
    saved_content: str = ""
    is_dirty: bool = False
    cursor: CursorState = field(default_factory=CursorState)
    language: str = "-"
    indentation: str = "-"
    encoding: str = "-"
    line_ending: str = "-"


@dataclass
class ShellState:
    workspace: WorkspaceState = field(default_factory=WorkspaceState)
    editor_sessions: list[EditorSession] = field(default_factory=list)
    active_session_id: Optional[str] = None
    active_side_panel: SideBarPanelId = SideBarPanelId.EXPLORER
    active_bottom_panel: BottomPanelId = BottomPanelId.OUTPUT
    is_side_bar_visible: bool = True
    is_bottom_panel_visible: bool = True

    @property
    def active_session(self) -> Optional[EditorSession]:
        for session in self.editor_sessions:
            if session.session_id == self.active_session_id:
                return session
        return None

    def set_active_session(self, session: Optional[EditorSession]) -> None:
        self.active_session_id = session.session_id if session else None

    def find_session_by_path(self, path: Path) -> Optional[EditorSession]:
        normalized = _normalize_path(path)
        for session in self.editor_sessions:
            if _normalize_path(session.path) == normalized:
                return session
        return None
