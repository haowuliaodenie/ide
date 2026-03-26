from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta

from ..models.shell_state import BottomPanelId
from .empty_state import EmptyStateWidget


class BottomPanel(QWidget):
    panel_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomPanel")
        self.active_panel_id = BottomPanelId.OUTPUT

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header_widget = QWidget()
        self.header_widget.setObjectName("BottomPanelHeader")
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 10, 0)
        header_layout.setSpacing(5)

        self.panel_selector = QListWidget()
        self.panel_selector.setObjectName("BottomPanelSelector")
        self.panel_selector.setFlow(QListWidget.LeftToRight)
        self.panel_selector.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.panel_selector.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.panel_selector.setWrapping(False)
        self.panel_selector.setSpacing(0)
        self.panel_selector.setSelectionMode(QListWidget.SingleSelection)
        self.panel_selector.setFixedHeight(36)
        self.panel_selector.currentRowChanged.connect(self._on_current_row_changed)
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
        self.output_editor = QPlainTextEdit()
        self.output_editor.setObjectName("BottomPanelTextView")
        self.output_editor.setReadOnly(True)
        self.output_editor.setPlainText("")
        self.problems_view = QLabel(
            "No problems have been reported.", alignment=Qt.AlignCenter
        )
        self.problems_view.setObjectName("ProblemsView")

        self._panel_widgets = {
            BottomPanelId.TERMINAL: self.terminal_view,
            BottomPanelId.OUTPUT: self.output_editor,
            BottomPanelId.PROBLEMS: self.problems_view,
        }
        self._panel_order = [
            BottomPanelId.TERMINAL,
            BottomPanelId.OUTPUT,
            BottomPanelId.PROBLEMS,
        ]

        for panel_id in self._panel_order:
            item = QListWidgetItem(self._panel_widgets[panel_id].windowTitle() or panel_id.title)
            item.setText(panel_id.title)
            self.panel_selector.addItem(item)
            self.panel_stack.addWidget(self._panel_widgets[panel_id])

        self.show_panel(BottomPanelId.OUTPUT)

    def show_panel(self, panel_id: BottomPanelId) -> None:
        if panel_id not in self._panel_widgets:
            return
        index = self._panel_order.index(panel_id)
        self.panel_selector.blockSignals(True)
        self.panel_selector.setCurrentRow(index)
        self.panel_selector.blockSignals(False)
        self.panel_stack.setCurrentWidget(self._panel_widgets[panel_id])
        self.active_panel_id = panel_id
        self.panel_selected.emit(panel_id)

    def append_output(self, text: str) -> None:
        existing = self.output_editor.toPlainText()
        updated = f"{existing}\n{text}".strip() if existing else text
        self.output_editor.setPlainText(updated)

    def _on_current_row_changed(self, row: int) -> None:
        if not (0 <= row < len(self._panel_order)):
            return
        self.show_panel(self._panel_order[row])
