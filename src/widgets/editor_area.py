from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QStackedWidget,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from ..models.shell_state import EditorSession
from .empty_state import EmptyStateWidget


class CodeEditor(QPlainTextEdit):
    content_changed = Signal(str)
    cursor_position_changed_signal = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CodeEditor")
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.textChanged.connect(self._emit_content_changed)
        self.cursorPositionChanged.connect(self._emit_cursor_position)

    def _emit_content_changed(self) -> None:
        self.content_changed.emit(self.toPlainText())

    def _emit_cursor_position(self) -> None:
        cursor = self.textCursor()
        self.cursor_position_changed_signal.emit(
            cursor.blockNumber() + 1,
            cursor.positionInBlock() + 1,
        )


class EditorTabs(QWidget):
    current_changed = Signal(int)
    tab_close_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_index = -1
        self._widgets: list[QWidget] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("EditorTabBar")
        self.tab_bar.setMovable(True)
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setDocumentMode(True)
        self.tab_bar.currentChanged.connect(self._on_current_changed)
        self.tab_bar.tabCloseRequested.connect(self.tab_close_requested.emit)
        layout.addWidget(self.tab_bar)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

    def add_tab(self, widget: QWidget, label: str) -> int:
        self._widgets.append(widget)
        index = self.stack.addWidget(widget)
        self.tab_bar.addTab(label)
        self.set_current_index(index)
        return index

    def remove_tab(self, index: int) -> None:
        if not (0 <= index < len(self._widgets)):
            return

        widget = self._widgets.pop(index)
        self.tab_bar.removeTab(index)
        self.stack.removeWidget(widget)
        widget.deleteLater()

        if self._widgets:
            self.set_current_index(min(index, len(self._widgets) - 1))
        else:
            self._current_index = -1

    def set_tab_text(self, index: int, text: str) -> None:
        if 0 <= index < self.tab_bar.count():
            self.tab_bar.setTabText(index, text)

    def set_current_index(self, index: int) -> None:
        if not (0 <= index < len(self._widgets)):
            return
        if self._current_index == index and self.stack.currentIndex() == index:
            return
        self._current_index = index
        self.tab_bar.blockSignals(True)
        self.tab_bar.setCurrentIndex(index)
        self.tab_bar.blockSignals(False)
        self.stack.setCurrentIndex(index)
        self.current_changed.emit(index)

    def current_index(self) -> int:
        return self._current_index

    def widget(self, index: int) -> QWidget | None:
        if 0 <= index < len(self._widgets):
            return self._widgets[index]
        return None

    def count(self) -> int:
        return len(self._widgets)

    def index_of(self, widget: QWidget) -> int:
        try:
            return self._widgets.index(widget)
        except ValueError:
            return -1

    def _on_current_changed(self, index: int) -> None:
        if not (0 <= index < len(self._widgets)):
            return
        self._current_index = index
        self.stack.setCurrentIndex(index)
        self.current_changed.emit(index)


class EditorArea(QWidget):
    new_file_requested = Signal()
    session_selected = Signal(str)
    session_close_requested = Signal(str)
    session_content_changed = Signal(str, str)
    session_cursor_moved = Signal(str, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EditorArea")
        self._session_order: list[str] = []
        self._editors_by_session_id: dict[str, CodeEditor] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.container = QStackedWidget()
        layout.addWidget(self.container)

        self.empty_state = EmptyStateWidget(
            "No File Open",
            "Open a file from the Explorer or create a new file to begin editing.",
            "There is no active editor session yet.",
            "New File",
        )
        self.empty_state.action_requested.connect(self.new_file_requested.emit)
        self.new_file_button = self.empty_state.action_button
        self.container.addWidget(self.empty_state)

        self.tabs = EditorTabs()
        self.tabs.current_changed.connect(self._on_current_changed)
        self.tabs.tab_close_requested.connect(self._on_tab_close_requested)
        self.container.addWidget(self.tabs)
        self.container.setCurrentWidget(self.empty_state)

    @property
    def tab_count(self) -> int:
        return len(self._session_order)

    def is_showing_empty_state(self) -> bool:
        return self.container.currentWidget() is self.empty_state

    def open_session(self, session: EditorSession) -> None:
        if session.session_id in self._editors_by_session_id:
            self.focus_session(session.session_id)
            return

        editor = CodeEditor()
        editor.setPlainText(session.content)
        editor.content_changed.connect(
            lambda content, session_id=session.session_id: self.session_content_changed.emit(
                session_id, content
            )
        )
        editor.cursor_position_changed_signal.connect(
            lambda line, column, session_id=session.session_id: self.session_cursor_moved.emit(
                session_id, line, column
            )
        )

        label = self._session_label(session)
        self._editors_by_session_id[session.session_id] = editor
        self._session_order.append(session.session_id)
        self.tabs.add_tab(editor, label)
        self.container.setCurrentWidget(self.tabs)
        self.focus_session(session.session_id)
        editor.setFocus()

    def update_session(self, session: EditorSession) -> None:
        session_id = session.session_id
        editor = self._editors_by_session_id.get(session_id)
        if editor is None:
            return

        if editor.toPlainText() != session.content:
            editor.blockSignals(True)
            editor.setPlainText(session.content)
            editor.blockSignals(False)

        index = self._session_order.index(session_id)
        self.tabs.set_tab_text(index, self._session_label(session))

    def focus_session(self, session_id: str) -> None:
        if session_id not in self._session_order:
            return
        index = self._session_order.index(session_id)
        self.container.setCurrentWidget(self.tabs)
        self.tabs.set_current_index(index)
        editor = self._editors_by_session_id[session_id]
        editor.setFocus()

    def close_session(self, session_id: str) -> None:
        if session_id not in self._session_order:
            return

        index = self._session_order.index(session_id)
        self._session_order.pop(index)
        self._editors_by_session_id.pop(session_id, None)
        self.tabs.remove_tab(index)

        if self._session_order:
            next_session_id = self._session_order[self.tabs.current_index()]
            self.session_selected.emit(next_session_id)
        else:
            self.container.setCurrentWidget(self.empty_state)
            self.session_selected.emit("")

    def current_editor(self) -> CodeEditor | None:
        if not self._session_order:
            return None
        current_index = self.tabs.current_index()
        if current_index == -1:
            return None
        session_id = self._session_order[current_index]
        return self._editors_by_session_id[session_id]

    def editor_for_session(self, session_id: str) -> CodeEditor | None:
        return self._editors_by_session_id.get(session_id)

    def _on_current_changed(self, index: int) -> None:
        if not (0 <= index < len(self._session_order)):
            return
        self.session_selected.emit(self._session_order[index])

    def _on_tab_close_requested(self, index: int) -> None:
        if not (0 <= index < len(self._session_order)):
            return
        self.session_close_requested.emit(self._session_order[index])

    @staticmethod
    def _session_label(session: EditorSession) -> str:
        suffix = "*" if session.is_dirty else ""
        return f"{session.display_name}{suffix}"
