from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout, QWidget
import qtawesome as qta

from ..models.shell_state import SideBarPanelId


class ActivityBar(QWidget):
    panel_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActivityBar")
        self.setFixedWidth(48)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        self._buttons_by_panel: dict[SideBarPanelId, QToolButton] = {}
        icon_color = "#858585"
        icon_active_color = "#ffffff"
        icon_size = QSize(24, 24)

        actions = [
            (SideBarPanelId.EXPLORER, "fa5s.copy", "Explorer"),
            (SideBarPanelId.SEARCH, "fa5s.search", "Search"),
            (SideBarPanelId.SOURCE_CONTROL, "fa5s.code-branch", "Source Control"),
            (SideBarPanelId.RUN_AND_DEBUG, "fa5s.bug", "Run and Debug"),
            (SideBarPanelId.EXTENSIONS, "fa5s.cubes", "Extensions"),
        ]

        for panel_id, icon_name, tooltip in actions:
            button = QToolButton()
            button.setIcon(
                qta.icon(icon_name, color=icon_color, color_active=icon_active_color)
            )
            button.setIconSize(icon_size)
            button.setToolTip(tooltip)
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, current_panel=panel_id: self._on_button_clicked(
                    current_panel
                )
            )
            self._buttons_by_panel[panel_id] = button
            layout.addWidget(button)

        self.set_active_panel(SideBarPanelId.EXPLORER)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

        self.account_btn = QToolButton()
        self.account_btn.setIcon(
            qta.icon("fa5s.user-circle", color=icon_color, color_active=icon_active_color)
        )
        self.account_btn.setIconSize(icon_size)
        self.account_btn.setToolTip("Accounts")
        layout.addWidget(self.account_btn)

        self.settings_btn = QToolButton()
        self.settings_btn.setIcon(
            qta.icon("fa5s.cog", color=icon_color, color_active=icon_active_color)
        )
        self.settings_btn.setIconSize(icon_size)
        self.settings_btn.setToolTip("Manage")
        layout.addWidget(self.settings_btn)

    def button_for_panel(self, panel_id: SideBarPanelId) -> QToolButton:
        return self._buttons_by_panel[panel_id]

    def set_active_panel(self, panel_id: SideBarPanelId) -> None:
        for current_panel, button in self._buttons_by_panel.items():
            button.setChecked(current_panel == panel_id)

    def _on_button_clicked(self, panel_id: SideBarPanelId) -> None:
        self.set_active_panel(panel_id)
        self.panel_selected.emit(panel_id)
