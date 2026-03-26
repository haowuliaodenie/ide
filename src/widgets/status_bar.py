from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QStatusBar, QWidget
import qtawesome as qta


class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setSizeGripEnabled(False)

        self.left_widget = QWidget()
        left_layout = QHBoxLayout(self.left_widget)
        left_layout.setContentsMargins(5, 0, 0, 0)
        left_layout.setSpacing(10)

        self.sync_icon = QLabel()
        self.sync_icon.setPixmap(qta.icon("fa5s.sync", color="#cccccc").pixmap(12, 12))
        left_layout.addWidget(self.sync_icon)

        self.branch_label = self._make_label("Branch: No Repository")
        left_layout.addWidget(self.branch_label)

        self.diagnostics_label = self._make_label("Problems: 0 errors, 0 warnings")
        left_layout.addWidget(self.diagnostics_label)

        left_layout.addStretch()
        self.addWidget(self.left_widget, 1)

        self.right_widget = QWidget()
        right_layout = QHBoxLayout(self.right_widget)
        right_layout.setContentsMargins(0, 0, 10, 0)
        right_layout.setSpacing(15)

        self.line_col_label = self._make_label("Ln -, Col -")
        right_layout.addWidget(self.line_col_label)

        self.spaces_label = self._make_label("Indent: -")
        right_layout.addWidget(self.spaces_label)

        self.encoding_label = self._make_label("Encoding: -")
        right_layout.addWidget(self.encoding_label)

        self.eol_label = self._make_label("EOL: -")
        right_layout.addWidget(self.eol_label)

        self.language_label = self._make_label("Language: -")
        right_layout.addWidget(self.language_label)

        self.interpreter_label = self._make_label("Interpreter: No Environment")
        right_layout.addWidget(self.interpreter_label)

        self.addPermanentWidget(self.right_widget)

    @staticmethod
    def _make_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setCursor(Qt.PointingHandCursor)
        return label

    def set_branch(self, text: str) -> None:
        self.branch_label.setText(text)

    def set_diagnostics(self, *, errors: int, warnings: int) -> None:
        self.diagnostics_label.setText(f"Problems: {errors} errors, {warnings} warnings")

    def set_cursor_position(self, line: int | None, col: int | None) -> None:
        if line is None or col is None:
            self.line_col_label.setText("Ln -, Col -")
            return
        self.line_col_label.setText(f"Ln {line}, Col {col}")

    def set_file_context(
        self,
        *,
        indentation: str,
        encoding: str,
        line_ending: str,
        language: str,
    ) -> None:
        self.spaces_label.setText(f"Indent: {indentation}")
        self.encoding_label.setText(f"Encoding: {encoding}")
        self.eol_label.setText(f"EOL: {line_ending}")
        self.language_label.setText(f"Language: {language}")

    def set_interpreter(self, text: str) -> None:
        self.interpreter_label.setText(text)

    def clear_file_context(self) -> None:
        self.set_cursor_position(None, None)
        self.set_file_context(
            indentation="-",
            encoding="-",
            line_ending="-",
            language="-",
        )

    def snapshot(self) -> dict[str, str]:
        return {
            "branch": self.branch_label.text(),
            "diagnostics": self.diagnostics_label.text(),
            "cursor": self.line_col_label.text(),
            "indentation": self.spaces_label.text(),
            "encoding": self.encoding_label.text(),
            "line_ending": self.eol_label.text(),
            "language": self.language_label.text(),
            "interpreter": self.interpreter_label.text(),
        }
