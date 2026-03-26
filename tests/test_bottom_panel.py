import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QStackedWidget, QTabBar

from src.main_window import MainWindow
from src.models.shell_state import BottomPanelId, ProblemItem, ProblemSeverity


class BottomPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.windows = []

    def tearDown(self):
        for window in self.windows:
            window.close()
        self.app.processEvents()

    def create_window(self) -> MainWindow:
        window = MainWindow()
        self.windows.append(window)
        window.show()
        self.process_events()
        return window

    def process_events(self, iterations: int = 8) -> None:
        for _ in range(iterations):
            self.app.processEvents()

    def test_bottom_panel_uses_semantic_panel_switching_and_reveals_requested_panel(self):
        window = self.create_window()

        self.assertIsInstance(window.bottom_panel.panel_selector, QTabBar)
        self.assertIsInstance(window.bottom_panel.panel_stack, QStackedWidget)
        self.assertEqual(window.bottom_panel.active_panel_id, BottomPanelId.OUTPUT)

        window.set_bottom_panel_visible(False)
        self.process_events()
        self.assertFalse(window.shell_state.is_bottom_panel_visible)

        window.show_bottom_panel(BottomPanelId.PROBLEMS)
        self.process_events()

        problems_index = window.bottom_panel.panel_index(BottomPanelId.PROBLEMS)
        self.assertTrue(window.shell_state.is_bottom_panel_visible)
        self.assertEqual(window.shell_state.active_bottom_panel, BottomPanelId.PROBLEMS)
        self.assertEqual(window.bottom_panel.active_panel_id, BottomPanelId.PROBLEMS)
        self.assertEqual(window.bottom_panel.panel_selector.currentIndex(), problems_index)
        self.assertEqual(
            window.bottom_panel.panel_selector.tabText(problems_index),
            BottomPanelId.PROBLEMS.title,
        )
        self.assertIs(
            window.bottom_panel.panel_stack.currentWidget(),
            window.bottom_panel.widget_for_panel(BottomPanelId.PROBLEMS),
        )

        window.show_bottom_panel(BottomPanelId.OUTPUT)
        self.process_events()

        output_index = window.bottom_panel.panel_index(BottomPanelId.OUTPUT)
        self.assertEqual(window.shell_state.active_bottom_panel, BottomPanelId.OUTPUT)
        self.assertEqual(window.bottom_panel.panel_selector.currentIndex(), output_index)
        self.assertEqual(
            window.bottom_panel.panel_selector.tabText(output_index),
            BottomPanelId.OUTPUT.title,
        )
        self.assertIs(
            window.bottom_panel.panel_stack.currentWidget(),
            window.bottom_panel.widget_for_panel(BottomPanelId.OUTPUT),
        )

    def test_output_starts_truthful_and_appends_without_overwriting(self):
        window = self.create_window()

        self.assertEqual(window.bottom_panel.output_editor.toPlainText(), "")
        self.assertTrue(window.bottom_panel.output_editor.isReadOnly())
        self.assertEqual(
            window.bottom_panel.output_empty_state.title_label.text(),
            "No Output",
        )
        self.assertEqual(
            window.bottom_panel.output_empty_state.reason_label.text(),
            "The shell has not emitted any output in this session.",
        )

        window.append_output("First line")
        window.append_output("Second line")
        self.process_events()

        self.assertEqual(
            window.bottom_panel.output_editor.toPlainText(),
            "First line\nSecond line",
        )

    def test_problems_render_zero_state_non_empty_state_and_clear_back_to_zero(self):
        window = self.create_window()

        window.show_bottom_panel(BottomPanelId.PROBLEMS)
        self.process_events()

        self.assertEqual(window.bottom_panel.problem_count, 0)
        self.assertEqual(window.bottom_panel.problems_count_label.text(), "0 Problems")
        self.assertEqual(
            window.bottom_panel.problems_empty_state.title_label.text(),
            "No Problems",
        )
        self.assertTrue(window.bottom_panel.problems_empty_state.isVisible())

        problems = [
            ProblemItem(
                severity=ProblemSeverity.ERROR,
                message="Unexpected indent",
                path=Path("workspace/example.py"),
                line=12,
                column=8,
                source="Pyright",
            ),
            ProblemItem(
                severity=ProblemSeverity.WARNING,
                message="Unused import",
                path=Path("workspace/example.py"),
                line=3,
                column=1,
                source="Ruff",
            ),
        ]

        window.set_problems(problems, reveal=True)
        self.process_events()

        self.assertEqual(window.bottom_panel.problem_count, 2)
        self.assertEqual(window.shell_state.active_bottom_panel, BottomPanelId.PROBLEMS)
        self.assertEqual(window.bottom_panel.problems_count_label.text(), "2 Problems")
        self.assertEqual(window.bottom_panel.problems_tree.topLevelItemCount(), 2)

        first_problem = window.bottom_panel.problems_tree.topLevelItem(0)
        self.assertEqual(first_problem.text(0), "Error")
        self.assertEqual(first_problem.text(1), "Unexpected indent")
        self.assertEqual(first_problem.text(2), "workspace/example.py:12:8")
        self.assertEqual(first_problem.text(3), "Pyright")

        second_problem = window.bottom_panel.problems_tree.topLevelItem(1)
        self.assertEqual(second_problem.text(0), "Warning")
        self.assertEqual(second_problem.text(1), "Unused import")
        self.assertEqual(second_problem.text(2), "workspace/example.py:3:1")
        self.assertEqual(second_problem.text(3), "Ruff")

        window.clear_problems()
        self.process_events()

        self.assertEqual(window.bottom_panel.problem_count, 0)
        self.assertEqual(window.bottom_panel.problems_count_label.text(), "0 Problems")
        self.assertEqual(window.bottom_panel.problems_tree.topLevelItemCount(), 0)
        self.assertTrue(window.bottom_panel.problems_empty_state.isVisible())


if __name__ == "__main__":
    unittest.main()
