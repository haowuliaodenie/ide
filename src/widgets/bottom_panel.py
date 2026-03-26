from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QStackedWidget,
    QTabBar,
    QTreeWidget,
    QTreeWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta

from ..models.shell_state import BottomPanelId, ProblemItem
from .empty_state import EmptyStateWidget


class BottomPanel(QWidget):
    panel_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomPanel")
        self.active_panel_id = BottomPanelId.OUTPUT
        self._output_entries: list[str] = []
        self._problems: list[ProblemItem] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header_widget = QWidget()
        self.header_widget.setObjectName("BottomPanelHeader")
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 10, 0)
        header_layout.setSpacing(5)

        self.panel_selector = QTabBar()
        self.panel_selector.setObjectName("BottomPanelSelector")
        self.panel_selector.setDocumentMode(True)
        self.panel_selector.setDrawBase(False)
        self.panel_selector.setExpanding(False)
        self.panel_selector.setMovable(False)
        self.panel_selector.setUsesScrollButtons(False)
        self.panel_selector.setFixedHeight(36)
        self.panel_selector.currentChanged.connect(self._on_current_index_changed)
        header_layout.addWidget(self.panel_selector)

        self.close_btn = QToolButton()
        self.close_btn.setIcon(qta.icon("fa5s.times", color="#cccccc"))
        self.close_btn.setToolTip("Close Panel")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(self.close_btn, alignment=Qt.AlignTop | Qt.AlignRight)

        layout.addWidget(self.header_widget)

        self.panel_stack = QStackedWidget()
        layout.addWidget(self.panel_stack)

        self.terminal_view = EmptyStateWidget(
            "Terminal Unavailable",
            "Open a workspace and install the integrated terminal stack to launch a real shell session here.",
            "No terminal backend is configured in this build yet.",
        )
        self.output_page = self._create_output_panel()
        self.problems_page = self._create_problems_panel()

        self._panel_widgets = {
            BottomPanelId.TERMINAL: self.terminal_view,
            BottomPanelId.OUTPUT: self.output_page,
            BottomPanelId.PROBLEMS: self.problems_page,
        }
        self._panel_order = [
            BottomPanelId.TERMINAL,
            BottomPanelId.OUTPUT,
            BottomPanelId.PROBLEMS,
        ]

        for panel_id in self._panel_order:
            self.panel_selector.addTab(panel_id.title)
            self.panel_stack.addWidget(self._panel_widgets[panel_id])

        self._refresh_output_view()
        self._refresh_problems_view()
        self.show_panel(BottomPanelId.OUTPUT)

    def show_panel(self, panel_id: BottomPanelId) -> None:
        if panel_id not in self._panel_widgets:
            return
        index = self.panel_index(panel_id)
        self.panel_selector.blockSignals(True)
        self.panel_selector.setCurrentIndex(index)
        self.panel_selector.blockSignals(False)
        self.panel_stack.setCurrentWidget(self._panel_widgets[panel_id])
        self.active_panel_id = panel_id
        self.panel_selected.emit(panel_id)

    def append_output(self, text: str) -> None:
        if not text:
            return
        self._output_entries.append(text)
        self.output_editor.setPlainText("\n".join(self._output_entries))
        self._refresh_output_view()

    def clear_output(self) -> None:
        self._output_entries.clear()
        self.output_editor.clear()
        self._refresh_output_view()

    def set_problems(self, problems: Sequence[ProblemItem]) -> None:
        self._problems = list(problems)
        self.problems_tree.clear()

        for problem in self._problems:
            item = QTreeWidgetItem(
                [
                    problem.severity.title,
                    problem.message,
                    problem.location_text,
                    problem.source or "-",
                ]
            )
            self.problems_tree.addTopLevelItem(item)

        self._refresh_problems_view()

    def clear_problems(self) -> None:
        self.set_problems([])

    @property
    def problem_count(self) -> int:
        return len(self._problems)

    def panel_index(self, panel_id: BottomPanelId) -> int:
        return self._panel_order.index(panel_id)

    def widget_for_panel(self, panel_id: BottomPanelId) -> QWidget:
        return self._panel_widgets[panel_id]

    def _create_output_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.output_stack = QStackedWidget()
        layout.addWidget(self.output_stack)

        self.output_empty_state = EmptyStateWidget(
            "No Output",
            "Commands, file events, and shell messages will appear here when they occur.",
            "The shell has not emitted any output in this session.",
        )
        self.output_stack.addWidget(self.output_empty_state)

        self.output_editor = QPlainTextEdit()
        self.output_editor.setObjectName("BottomPanelTextView")
        self.output_editor.setReadOnly(True)
        self.output_editor.setPlainText("")
        self.output_stack.addWidget(self.output_editor)

        return container

    def _create_problems_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("ProblemsHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(8)

        self.problems_count_label = QLabel("0 Problems")
        self.problems_count_label.setObjectName("ProblemsCountLabel")
        header_layout.addWidget(self.problems_count_label)
        header_layout.addStretch()
        layout.addWidget(header)

        self.problems_stack = QStackedWidget()
        layout.addWidget(self.problems_stack)

        self.problems_empty_state = EmptyStateWidget(
            "No Problems",
            "Diagnostics will appear here when the shell reports real issues.",
            "0 problems are currently reported.",
        )
        self.problems_stack.addWidget(self.problems_empty_state)

        self.problems_tree = QTreeWidget()
        self.problems_tree.setObjectName("ProblemsTree")
        self.problems_tree.setAlternatingRowColors(False)
        self.problems_tree.setRootIsDecorated(False)
        self.problems_tree.setItemsExpandable(False)
        self.problems_tree.setUniformRowHeights(True)
        self.problems_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.problems_tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.problems_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.problems_tree.setHeaderLabels(["Severity", "Message", "Location", "Source"])
        self.problems_tree.header().setStretchLastSection(False)
        self.problems_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.problems_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.problems_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.problems_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.problems_stack.addWidget(self.problems_tree)

        return container

    def _refresh_output_view(self) -> None:
        target = self.output_editor if self._output_entries else self.output_empty_state
        self.output_stack.setCurrentWidget(target)

    def _refresh_problems_view(self) -> None:
        count = self.problem_count
        label = "Problem" if count == 1 else "Problems"
        self.problems_count_label.setText(f"{count} {label}")
        target = self.problems_tree if count else self.problems_empty_state
        self.problems_stack.setCurrentWidget(target)

    def _on_current_index_changed(self, index: int) -> None:
        if not (0 <= index < len(self._panel_order)):
            return
        self.show_panel(self._panel_order[index])
