from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class EmptyStateWidget(QWidget):
    action_requested = Signal()

    def __init__(
        self,
        title: str,
        body: str,
        reason: str = "",
        action_text: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("EmptyState")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("EmptyStateTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.body_label = QLabel(body)
        self.body_label.setObjectName("EmptyStateBody")
        self.body_label.setWordWrap(True)
        self.body_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.body_label)

        self.reason_label = QLabel(reason)
        self.reason_label.setObjectName("EmptyStateReason")
        self.reason_label.setWordWrap(True)
        self.reason_label.setAlignment(Qt.AlignCenter)
        self.reason_label.setVisible(bool(reason))
        layout.addWidget(self.reason_label)

        self.action_button = QPushButton(action_text or "")
        self.action_button.setObjectName("EmptyStateAction")
        self.action_button.setVisible(bool(action_text))
        self.action_button.clicked.connect(self.action_requested.emit)
        layout.addWidget(self.action_button, alignment=Qt.AlignCenter)

    def set_state(
        self,
        *,
        title: str,
        body: str,
        reason: str = "",
        action_text: str | None = None,
    ) -> None:
        self.title_label.setText(title)
        self.body_label.setText(body)
        self.reason_label.setText(reason)
        self.reason_label.setVisible(bool(reason))
        self.action_button.setText(action_text or "")
        self.action_button.setVisible(bool(action_text))
