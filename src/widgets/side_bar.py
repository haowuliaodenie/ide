from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta

from ..models.shell_state import SideBarPanelId
from .empty_state import EmptyStateWidget


class SideBar(QWidget):
    workspace_selection_requested = Signal()
    file_open_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SideBar")
        self.current_panel_id = SideBarPanelId.EXPLORER
        self.explorer_root_path: Path | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header_widget = QWidget()
        self.header_widget.setObjectName("SideBarHeader")
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(15, 10, 10, 10)
        header_layout.setSpacing(5)

        self.title_label = QLabel(self.current_panel_id.title)
        self.title_label.setObjectName("SideBarTitle")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.action_btn = QToolButton()
        self.action_btn.setIcon(qta.icon("fa5s.folder-open", color="#cccccc"))
        self.action_btn.setToolTip("Select Workspace")
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.clicked.connect(self._on_header_action_clicked)
        header_layout.addWidget(self.action_btn)

        layout.addWidget(self.header_widget)

        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        self.explorer_widget = self._create_explorer_panel()
        self.search_widget = self._create_static_panel(
            "Search",
            "Search features are not configured in this shell yet.",
            "Search is unavailable until a real search workflow is implemented.",
        )
        self.scm_widget = self._create_static_panel(
            "Source Control",
            "Source control insights will appear here when repository integration exists.",
            "No repository workflow is connected in this shell yet.",
        )
        self.run_widget = self._create_static_panel(
            "Run and Debug",
            "Launch configurations and debug sessions will appear here when available.",
            "Debug tooling is not configured in this shell yet.",
        )
        self.extensions_widget = self._create_static_panel(
            "Extensions",
            "Installed extensions and marketplace results will appear here when supported.",
            "Extension management is unavailable in this shell yet.",
        )

        self._panel_order = [
            SideBarPanelId.EXPLORER,
            SideBarPanelId.SEARCH,
            SideBarPanelId.SOURCE_CONTROL,
            SideBarPanelId.RUN_AND_DEBUG,
            SideBarPanelId.EXTENSIONS,
        ]
        self._panel_widgets = {
            SideBarPanelId.EXPLORER: self.explorer_widget,
            SideBarPanelId.SEARCH: self.search_widget,
            SideBarPanelId.SOURCE_CONTROL: self.scm_widget,
            SideBarPanelId.RUN_AND_DEBUG: self.run_widget,
            SideBarPanelId.EXTENSIONS: self.extensions_widget,
        }

        for widget in self._panel_widgets.values():
            self.stacked_widget.addWidget(widget)

        self.switch_panel(SideBarPanelId.EXPLORER)
        self.show_no_workspace_state()

    def _create_explorer_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.explorer_empty_state = EmptyStateWidget(
            "Open a Workspace",
            "Select a folder to populate the Explorer with real files and directories.",
            "No workspace is currently selected.",
            "Select Workspace",
        )
        self.explorer_empty_state.action_requested.connect(
            self.workspace_selection_requested.emit
        )
        layout.addWidget(self.explorer_empty_state)

        self.file_model = QFileSystemModel(self)
        self.file_model.setReadOnly(True)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)
        self.tree_view.setRootIsDecorated(True)
        self.tree_view.setUniformRowHeights(True)
        self.tree_view.setIndentation(15)
        self.tree_view.doubleClicked.connect(self._on_tree_activated)
        self.tree_view.activated.connect(self._on_tree_activated)
        self.tree_view.hide()
        layout.addWidget(self.tree_view)

        self.select_workspace_button = self.explorer_empty_state.action_button
        return container

    def _create_static_panel(self, title: str, body: str, reason: str) -> EmptyStateWidget:
        return EmptyStateWidget(title, body, reason)

    def switch_panel(self, panel_id: SideBarPanelId) -> None:
        if panel_id not in self._panel_widgets:
            return

        self.current_panel_id = panel_id
        self.title_label.setText(panel_id.title)
        self.stacked_widget.setCurrentWidget(self._panel_widgets[panel_id])
        self.action_btn.setVisible(panel_id is SideBarPanelId.EXPLORER)

    def show_no_workspace_state(self) -> None:
        self.explorer_root_path = None
        self.file_model.setRootPath("")
        self.tree_view.setRootIndex(QModelIndex())
        self.explorer_empty_state.set_state(
            title="Open a Workspace",
            body="Select a folder to populate the Explorer with real files and directories.",
            reason="No workspace is currently selected.",
            action_text="Select Workspace",
        )
        self.explorer_empty_state.show()
        self.tree_view.hide()

    def set_workspace(self, path: str | Path | None) -> None:
        if path is None:
            self.show_no_workspace_state()
            return

        workspace_path = Path(path)
        self.explorer_root_path = workspace_path
        root_index = self.file_model.setRootPath(str(workspace_path))
        self.tree_view.setRootIndex(root_index)
        self.explorer_empty_state.hide()
        self.tree_view.show()

    def _on_tree_activated(self, index: QModelIndex) -> None:
        if not index.isValid():
            return

        file_path = Path(self.file_model.filePath(index))
        if file_path.is_dir():
            self.tree_view.setExpanded(index, not self.tree_view.isExpanded(index))
            return

        self.file_open_requested.emit(str(file_path))

    def _on_header_action_clicked(self) -> None:
        if self.current_panel_id is SideBarPanelId.EXPLORER:
            self.workspace_selection_requested.emit()
