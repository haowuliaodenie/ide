from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QToolBar,
    QWidget,
)
import qtawesome as qta

from .models.shell_state import (
    BottomPanelId,
    CursorState,
    DirtyCloseAction,
    EditorSession,
    ProblemItem,
    ShellState,
    SideBarPanelId,
)
from .widgets.activity_bar import ActivityBar
from .widgets.bottom_panel import BottomPanel
from .widgets.editor_area import EditorArea
from .widgets.side_bar import SideBar
from .widgets.status_bar import StatusBar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 IDE Shell")
        self.resize(1280, 800)

        self.shell_state = ShellState()
        self.command_log: list[str] = []
        self._untitled_counter = 1
        self._side_bar_last_width = 280
        self._bottom_panel_last_height = 220
        self._command_routes: dict[str, Callable[..., Any]] = {}

        self._init_ui()
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._register_commands()
        self._connect_signals()
        self._refresh_workspace_state()
        self._refresh_status_bar()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.activity_bar = ActivityBar(self)
        main_layout.addWidget(self.activity_bar)

        self.main_splitter = QSplitter(Qt.Horizontal, self)
        self.main_splitter.setChildrenCollapsible(False)
        main_layout.addWidget(self.main_splitter)

        self.side_bar = SideBar(self)
        self.main_splitter.addWidget(self.side_bar)

        self.right_splitter = QSplitter(Qt.Vertical, self)
        self.right_splitter.setChildrenCollapsible(False)
        self.main_splitter.addWidget(self.right_splitter)

        self.editor_area = EditorArea(self)
        self.right_splitter.addWidget(self.editor_area)

        self.bottom_panel = BottomPanel(self)
        self.right_splitter.addWidget(self.bottom_panel)

        self.main_splitter.setSizes([self._side_bar_last_width, 1000])
        self.right_splitter.setSizes([580, self._bottom_panel_last_height])

        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)

    def _create_actions(self) -> None:
        icon_color = "#cccccc"

        self.new_file_action = QAction(
            qta.icon("fa5s.file-alt", color=icon_color), "New File", self
        )
        self.select_workspace_action = QAction(
            qta.icon("fa5s.folder-open", color=icon_color), "Open Folder...", self
        )
        self.save_file_action = QAction(
            qta.icon("fa5s.save", color=icon_color), "Save", self
        )
        self.toggle_side_bar_action = QAction("Toggle Side Bar", self)
        self.toggle_bottom_panel_action = QAction("Toggle Bottom Panel", self)
        self.show_terminal_action = QAction("Show Terminal", self)

    def _create_menus(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.new_file_action)
        file_menu.addAction(self.select_workspace_action)
        file_menu.addAction(self.save_file_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        view_menu.addAction(self.toggle_side_bar_action)
        view_menu.addAction(self.toggle_bottom_panel_action)

        terminal_menu = menubar.addMenu("Terminal")
        terminal_menu.addAction(self.show_terminal_action)

    def _create_toolbars(self) -> None:
        self.toolbar = QToolBar("Main Toolbar", self)
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        self.toolbar.addAction(self.new_file_action)
        self.toolbar.addAction(self.select_workspace_action)
        self.toolbar.addAction(self.save_file_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.show_terminal_action)

    def _register_commands(self) -> None:
        self._command_routes = {
            "new_file": self._handle_new_file,
            "select_workspace": self._handle_select_workspace,
            "save": self._handle_save_active_session,
            "show_terminal": lambda: self.show_bottom_panel(BottomPanelId.TERMINAL),
            "toggle_side_bar": self.toggle_side_bar,
            "toggle_bottom_panel": self.toggle_bottom_panel,
        }

    def _connect_signals(self) -> None:
        self.new_file_action.triggered.connect(lambda: self.route_command("new_file"))
        self.select_workspace_action.triggered.connect(
            lambda: self.route_command("select_workspace")
        )
        self.save_file_action.triggered.connect(lambda: self.route_command("save"))
        self.toggle_side_bar_action.triggered.connect(
            lambda: self.route_command("toggle_side_bar")
        )
        self.toggle_bottom_panel_action.triggered.connect(
            lambda: self.route_command("toggle_bottom_panel")
        )
        self.show_terminal_action.triggered.connect(
            lambda: self.route_command("show_terminal")
        )

        self.activity_bar.panel_selected.connect(self.activate_side_panel)
        self.side_bar.workspace_selection_requested.connect(
            lambda: self.route_command("select_workspace")
        )
        self.side_bar.file_open_requested.connect(self.open_file)
        self.editor_area.new_file_requested.connect(
            lambda: self.route_command("new_file")
        )
        self.editor_area.session_selected.connect(self._on_session_selected)
        self.editor_area.session_content_changed.connect(self._on_session_content_changed)
        self.editor_area.session_cursor_moved.connect(self._on_session_cursor_moved)
        self.editor_area.session_close_requested.connect(self._on_session_close_requested)
        self.bottom_panel.panel_selected.connect(self._on_bottom_panel_selected)
        self.bottom_panel.close_btn.clicked.connect(self.toggle_bottom_panel)

    def route_command(self, command_name: str, *args):
        self.command_log.append(command_name)
        handler = self._command_routes[command_name]
        return handler(*args)

    def activate_side_panel(self, panel_id: SideBarPanelId) -> None:
        if not self.shell_state.is_side_bar_visible:
            self.set_side_bar_visible(True)

        self.shell_state.active_side_panel = panel_id
        self.activity_bar.set_active_panel(panel_id)
        self.side_bar.switch_panel(panel_id)

    def show_bottom_panel(self, panel_id: BottomPanelId) -> None:
        if not self.shell_state.is_bottom_panel_visible:
            self.set_bottom_panel_visible(True)
        self.bottom_panel.show_panel(panel_id)
        self.shell_state.active_bottom_panel = panel_id

    def append_output(self, text: str, *, reveal: bool = False) -> None:
        if reveal:
            self.show_bottom_panel(BottomPanelId.OUTPUT)
        self.bottom_panel.append_output(text)

    def set_problems(
        self,
        problems: Sequence[ProblemItem],
        *,
        reveal: bool = False,
    ) -> None:
        if reveal:
            self.show_bottom_panel(BottomPanelId.PROBLEMS)
        self.bottom_panel.set_problems(problems)

    def clear_problems(self, *, reveal: bool = False) -> None:
        if reveal:
            self.show_bottom_panel(BottomPanelId.PROBLEMS)
        self.bottom_panel.clear_problems()

    def toggle_side_bar(self) -> None:
        self.set_side_bar_visible(not self.shell_state.is_side_bar_visible)

    def toggle_bottom_panel(self) -> None:
        self.set_bottom_panel_visible(not self.shell_state.is_bottom_panel_visible)

    def set_side_bar_visible(self, visible: bool) -> None:
        sizes = self.main_splitter.sizes()
        total_width = max(sum(sizes), self.main_splitter.width(), 1)
        if visible:
            target = self._side_bar_last_width or 280
            self.main_splitter.setSizes([target, max(total_width - target, 1)])
        else:
            if sizes[0] > 0:
                self._side_bar_last_width = sizes[0]
            self.main_splitter.setSizes([0, total_width])
        self.shell_state.is_side_bar_visible = visible

    def set_bottom_panel_visible(self, visible: bool) -> None:
        sizes = self.right_splitter.sizes()
        total_height = max(sum(sizes), self.right_splitter.height(), 1)
        if visible:
            target = self._bottom_panel_last_height or 220
            self.right_splitter.setSizes([max(total_height - target, 1), target])
        else:
            if sizes[1] > 0:
                self._bottom_panel_last_height = sizes[1]
            self.right_splitter.setSizes([total_height, 0])
        self.shell_state.is_bottom_panel_visible = visible

    def choose_workspace_directory(self) -> str:
        return QFileDialog.getExistingDirectory(self, "Select Workspace")

    def choose_save_path(self, suggested_name: str) -> str:
        path, _ = QFileDialog.getSaveFileName(self, "Save File", suggested_name)
        return path

    def resolve_dirty_close(self, session: EditorSession) -> DirtyCloseAction:
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Unsaved Changes")
        message_box.setIcon(QMessageBox.Warning)
        message_box.setText(f"Do you want to save changes to {session.display_name}?")
        message_box.setInformativeText(
            "Your changes will be lost if you do not save them."
        )
        save_button = message_box.addButton("Save", QMessageBox.AcceptRole)
        discard_button = message_box.addButton("Discard", QMessageBox.DestructiveRole)
        cancel_button = message_box.addButton("Cancel", QMessageBox.RejectRole)
        message_box.setDefaultButton(save_button)
        message_box.exec()

        clicked_button = message_box.clickedButton()
        if clicked_button is save_button:
            return DirtyCloseAction.SAVE
        if clicked_button is discard_button:
            return DirtyCloseAction.DISCARD
        if clicked_button is cancel_button:
            return DirtyCloseAction.CANCEL
        return DirtyCloseAction.CANCEL

    def _handle_new_file(self) -> EditorSession:
        display_name = f"Untitled-{self._untitled_counter}"
        self._untitled_counter += 1
        session = EditorSession(
            display_name=display_name,
            content="",
            saved_content="",
            is_dirty=False,
            cursor=CursorState(line=1, column=1),
            indentation="4 spaces",
            encoding="UTF-8",
            line_ending="LF",
            language="Plain Text",
        )
        self.shell_state.editor_sessions.append(session)
        self.shell_state.set_active_session(session)
        self.editor_area.open_session(session)
        self._refresh_status_bar()
        return session

    def _handle_select_workspace(self) -> Path | None:
        selected = self.choose_workspace_directory()
        if not selected:
            return None
        return self.set_workspace(selected)

    def set_workspace(self, path: str | Path | None) -> Path | None:
        if path is None:
            self.shell_state.workspace.set_path(None)
            self._refresh_workspace_state()
            self._refresh_status_bar()
            return None

        workspace_path = self._normalize_path(path)
        self.shell_state.workspace.set_path(workspace_path)
        self._refresh_workspace_state()
        self._refresh_status_bar()
        return workspace_path

    def open_file(self, file_path: str | Path) -> EditorSession | None:
        path = self._normalize_path(file_path)
        existing = self.shell_state.find_session_by_path(path)
        if existing is not None:
            self.shell_state.set_active_session(existing)
            self.editor_area.focus_session(existing.session_id)
            self._refresh_status_bar()
            return existing

        try:
            content = self._read_file_text(path)
        except (OSError, UnicodeError) as exc:
            self._report_file_error("open", path, exc)
            return None

        session = EditorSession(
            display_name=path.name,
            path=path,
            content=content,
            saved_content=content,
            is_dirty=False,
            cursor=CursorState(line=1, column=1),
            indentation="4 spaces",
            encoding="UTF-8",
            line_ending="LF",
            language=self._language_for_path(path),
        )
        self.shell_state.editor_sessions.append(session)
        self.shell_state.set_active_session(session)
        self.editor_area.open_session(session)
        self._refresh_status_bar()
        return session

    def _handle_save_active_session(self) -> bool:
        session = self.shell_state.active_session
        if session is None:
            return False
        return self._save_session(session)

    def _on_session_selected(self, session_id: str) -> None:
        if not session_id:
            self.shell_state.set_active_session(None)
            self._refresh_status_bar()
            return

        session = self._session_by_id(session_id)
        if session is None:
            return
        self.shell_state.set_active_session(session)
        self._refresh_status_bar()

    def _on_session_content_changed(self, session_id: str, content: str) -> None:
        session = self._session_by_id(session_id)
        if session is None:
            return
        session.content = content
        session.is_dirty = content != session.saved_content
        self.editor_area.update_session(session)
        if self.shell_state.active_session_id == session_id:
            self._refresh_status_bar()

    def _on_session_cursor_moved(self, session_id: str, line: int, column: int) -> None:
        session = self._session_by_id(session_id)
        if session is None:
            return
        session.cursor = CursorState(line=line, column=column)
        if self.shell_state.active_session_id == session_id:
            self._refresh_status_bar()

    def _on_session_close_requested(self, session_id: str) -> None:
        session = self._session_by_id(session_id)
        if session is None:
            return
        if session.is_dirty:
            resolution = self.resolve_dirty_close(session)
            if resolution is DirtyCloseAction.CANCEL:
                self.status_bar.showMessage(
                    f"Close canceled for {session.display_name}.",
                    3000,
                )
                return
            if resolution is DirtyCloseAction.SAVE and not self._save_session(session):
                return

        self._close_session(session_id)

    def _on_bottom_panel_selected(self, panel_id: BottomPanelId) -> None:
        self.shell_state.active_bottom_panel = panel_id

    def _refresh_workspace_state(self) -> None:
        workspace = self.shell_state.workspace
        if workspace.available and workspace.root_path is not None:
            self.side_bar.set_workspace(workspace.root_path)
        else:
            self.side_bar.show_no_workspace_state()

    def _refresh_status_bar(self) -> None:
        self.status_bar.set_branch("Branch: No Repository")
        self.status_bar.set_diagnostics(errors=0, warnings=0)
        self.status_bar.set_interpreter("Interpreter: No Environment")

        session = self.shell_state.active_session
        if session is None:
            self.status_bar.clear_file_context()
            return

        line = session.cursor.line if session.cursor.line is not None else 1
        column = session.cursor.column if session.cursor.column is not None else 1
        self.status_bar.set_cursor_position(line, column)
        self.status_bar.set_file_context(
            indentation=session.indentation,
            encoding=session.encoding,
            line_ending=session.line_ending,
            language=session.language,
        )

    def _session_by_id(self, session_id: str) -> EditorSession | None:
        for session in self.shell_state.editor_sessions:
            if session.session_id == session_id:
                return session
        return None

    def _save_session(self, session: EditorSession) -> bool:
        original_path = session.path
        original_display_name = session.display_name
        original_language = session.language

        target_path = original_path
        if target_path is None:
            selected = self.choose_save_path(session.display_name)
            if not selected:
                self.status_bar.showMessage("Save canceled.", 3000)
                return False
            target_path = self._normalize_path(selected)

        try:
            self._write_file_text(target_path, session.content)
        except (OSError, UnicodeError) as exc:
            self._report_file_error("save", target_path, exc)
            session.path = original_path
            session.display_name = original_display_name
            session.language = original_language
            self.editor_area.update_session(session)
            if self.shell_state.active_session_id == session.session_id:
                self._refresh_status_bar()
            return False

        session.path = target_path
        session.display_name = target_path.name
        session.language = self._language_for_path(target_path)
        session.saved_content = session.content
        session.is_dirty = False
        session.encoding = "UTF-8"
        session.line_ending = "LF"
        self.editor_area.update_session(session)
        if self.shell_state.active_session_id == session.session_id:
            self._refresh_status_bar()
        return True

    def _close_session(self, session_id: str) -> None:
        self.shell_state.editor_sessions = [
            existing
            for existing in self.shell_state.editor_sessions
            if existing.session_id != session_id
        ]
        self.editor_area.close_session(session_id)
        if self.shell_state.active_session_id == session_id:
            self.shell_state.set_active_session(None)
        self._refresh_status_bar()

    def _report_file_error(
        self,
        operation: str,
        path: Path,
        exc: Exception,
    ) -> None:
        self.append_output(f"Failed to {operation} {path}: {exc}", reveal=True)
        self.status_bar.showMessage(f"Failed to {operation} {path.name}", 4000)

    @staticmethod
    def _read_file_text(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _write_file_text(path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _normalize_path(path: str | Path) -> Path:
        candidate = Path(path)
        try:
            return candidate.resolve(strict=False)
        except OSError:
            return candidate.absolute()

    @staticmethod
    def _language_for_path(path: Path) -> str:
        suffix = path.suffix.lower()
        return {
            ".py": "Python",
            ".txt": "Plain Text",
            ".md": "Markdown",
            ".json": "JSON",
        }.get(suffix, "Plain Text")
