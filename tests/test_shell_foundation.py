import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.main_window import MainWindow
from src.models.shell_state import BottomPanelId, SideBarPanelId


class ShellFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.windows = []

    def tearDown(self):
        for window in self.windows:
            window.close()
        self.app.processEvents()

    def create_window(self):
        window = MainWindow()
        self.windows.append(window)
        window.show()
        self.app.processEvents()
        return window

    def test_offscreen_startup_composes_full_workbench(self):
        window = self.create_window()

        self.assertIsNotNone(window.activity_bar)
        self.assertIsNotNone(window.side_bar)
        self.assertIsNotNone(window.editor_area)
        self.assertIsNotNone(window.bottom_panel)
        self.assertIs(window.statusBar(), window.status_bar)

        self.assertGreater(window.activity_bar.width(), 0)
        self.assertGreater(window.side_bar.width(), 0)
        self.assertGreater(window.editor_area.width(), 0)
        self.assertGreater(window.bottom_panel.height(), 0)

        main_sizes = window.main_splitter.sizes()
        right_sizes = window.right_splitter.sizes()

        self.assertGreater(main_sizes[0], 0)
        self.assertGreater(main_sizes[1], 0)
        self.assertGreater(right_sizes[0], 0)
        self.assertGreater(right_sizes[1], 0)

    def test_primary_navigation_uses_semantic_panel_state(self):
        window = self.create_window()
        window.set_side_bar_visible(False)
        self.app.processEvents()

        window.activity_bar.button_for_panel(SideBarPanelId.SEARCH).click()
        self.app.processEvents()

        self.assertTrue(window.shell_state.is_side_bar_visible)
        self.assertEqual(window.shell_state.active_side_panel, SideBarPanelId.SEARCH)
        self.assertEqual(window.side_bar.current_panel_id, SideBarPanelId.SEARCH)
        self.assertEqual(window.side_bar.title_label.text(), "SEARCH")
        self.assertTrue(window.activity_bar.button_for_panel(SideBarPanelId.SEARCH).isChecked())
        self.assertFalse(window.activity_bar.button_for_panel(SideBarPanelId.EXPLORER).isChecked())
        self.assertGreater(window.main_splitter.sizes()[0], 0)

    def test_startup_editor_context_is_truthful(self):
        window = self.create_window()

        self.assertTrue(window.editor_area.is_showing_empty_state())
        self.assertEqual(window.editor_area.tab_count, 0)
        self.assertIsNone(window.shell_state.active_session)

        snapshot = window.status_bar.snapshot()
        self.assertEqual(snapshot["branch"], "Branch: No Repository")
        self.assertEqual(snapshot["cursor"], "Ln -, Col -")
        self.assertEqual(snapshot["indentation"], "Indent: -")
        self.assertEqual(snapshot["encoding"], "Encoding: -")
        self.assertEqual(snapshot["line_ending"], "EOL: -")
        self.assertEqual(snapshot["language"], "Language: -")

    def test_shell_commands_drive_truthful_workflows(self):
        window = self.create_window()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            save_target = workspace / "created.py"

            window.choose_workspace_directory = lambda: str(workspace)
            window.choose_save_path = lambda suggested_name: str(save_target)

            window.select_workspace_action.trigger()
            self.app.processEvents()

            self.assertEqual(window.command_log[-1], "select_workspace")
            self.assertEqual(window.shell_state.workspace.root_path, workspace)
            self.assertEqual(window.side_bar.explorer_root_path, workspace)

            action_window = self.create_window()
            action_window.new_file_action.trigger()
            self.app.processEvents()

            self.assertEqual(action_window.command_log[-1], "new_file")
            self.assertEqual(len(action_window.shell_state.editor_sessions), 1)
            self.assertIsNone(action_window.shell_state.active_session.path)

            widget_window = self.create_window()
            widget_window.editor_area.new_file_button.click()
            self.app.processEvents()

            self.assertEqual(widget_window.command_log[-1], "new_file")
            self.assertEqual(len(widget_window.shell_state.editor_sessions), 1)
            self.assertIsNone(widget_window.shell_state.active_session.path)

            workspace_window = self.create_window()
            workspace_window.choose_workspace_directory = lambda: str(workspace)
            workspace_window.side_bar.select_workspace_button.click()
            self.app.processEvents()

            self.assertEqual(workspace_window.command_log[-1], "select_workspace")
            self.assertEqual(workspace_window.shell_state.workspace.root_path, workspace)

            window.new_file_action.trigger()
            self.app.processEvents()

            editor = window.editor_area.current_editor()
            editor.setPlainText("print('hello from shell')\n")
            self.app.processEvents()

            self.assertTrue(window.shell_state.active_session.is_dirty)

            window.save_file_action.trigger()
            self.app.processEvents()

            self.assertTrue(save_target.exists())
            self.assertEqual(save_target.read_text(encoding="utf-8"), "print('hello from shell')\n")
            self.assertEqual(window.shell_state.active_session.path, save_target)
            self.assertFalse(window.shell_state.active_session.is_dirty)

            window.toggle_bottom_panel_action.trigger()
            self.app.processEvents()
            self.assertFalse(window.shell_state.is_bottom_panel_visible)

            window.show_terminal_action.trigger()
            self.app.processEvents()

            self.assertTrue(window.shell_state.is_bottom_panel_visible)
            self.assertEqual(window.shell_state.active_bottom_panel, BottomPanelId.TERMINAL)
            self.assertEqual(window.bottom_panel.active_panel_id, BottomPanelId.TERMINAL)

            window.toggle_side_bar_action.trigger()
            self.app.processEvents()
            self.assertFalse(window.shell_state.is_side_bar_visible)

            window.activity_bar.button_for_panel(SideBarPanelId.EXPLORER).click()
            self.app.processEvents()

            self.assertTrue(window.shell_state.is_side_bar_visible)
            self.assertEqual(window.shell_state.active_side_panel, SideBarPanelId.EXPLORER)


if __name__ == "__main__":
    unittest.main()
