import os
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.main_window import MainWindow
from src.models.shell_state import SideBarPanelId


class SidebarWorkspaceTests(unittest.TestCase):
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

    def wait_until(self, predicate, timeout_ms: int = 1000) -> None:
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            self.process_events()
            if predicate():
                return
            QTest.qWait(20)
        self.fail("Timed out waiting for expected Qt state")

    def child_names(self, window: MainWindow, parent_index) -> list[str]:
        model = window.side_bar.file_model
        self.process_events()
        row_count = model.rowCount(parent_index)
        return [
            model.data(model.index(row, 0, parent_index))
            for row in range(row_count)
        ]

    def index_for_path(self, window: MainWindow, path: Path):
        index = window.side_bar.file_model.index(str(path))
        self.assertTrue(index.isValid(), f"Expected valid model index for {path}")
        return index

    def test_explorer_is_explicit_when_no_workspace_is_selected(self):
        window = self.create_window()

        self.assertEqual(window.side_bar.current_panel_id, SideBarPanelId.EXPLORER)
        self.assertIsNone(window.shell_state.workspace.root_path)
        self.assertFalse(window.shell_state.workspace.available)
        self.assertEqual(window.side_bar.explorer_empty_state.title_label.text(), "Open a Workspace")
        self.assertEqual(
            window.side_bar.explorer_empty_state.body_label.text(),
            "Select a folder to populate the Explorer with real files and directories.",
        )
        self.assertEqual(
            window.side_bar.explorer_empty_state.reason_label.text(),
            "No workspace is currently selected.",
        )
        self.assertEqual(window.side_bar.select_workspace_button.text(), "Select Workspace")
        self.assertIsNone(window.side_bar.explorer_root_path)
        self.assertEqual(window.side_bar.file_model.rootPath(), "")
        self.assertFalse(window.side_bar.tree_view.isVisible())
        self.assertTrue(window.side_bar.explorer_empty_state.isVisible())

    def test_selecting_workspace_reroots_explorer_and_cancel_keeps_state(self):
        window = self.create_window()

        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first_workspace = Path(first_tmp)
            second_workspace = Path(second_tmp)

            window.choose_workspace_directory = lambda: str(first_workspace)
            window.side_bar.select_workspace_button.click()
            self.process_events()

            self.assertEqual(window.command_log[-1], "select_workspace")
            self.assertEqual(window.shell_state.workspace.root_path, first_workspace)
            self.assertEqual(window.side_bar.explorer_root_path, first_workspace)
            self.assertEqual(Path(window.side_bar.file_model.rootPath()), first_workspace)
            self.assertEqual(
                Path(window.side_bar.file_model.filePath(window.side_bar.tree_view.rootIndex())),
                first_workspace,
            )
            self.assertTrue(window.side_bar.tree_view.isVisible())
            self.assertFalse(window.side_bar.explorer_empty_state.isVisible())

            window.choose_workspace_directory = lambda: ""
            window.side_bar.action_btn.click()
            self.process_events()

            self.assertEqual(window.command_log[-1], "select_workspace")
            self.assertEqual(window.shell_state.workspace.root_path, first_workspace)
            self.assertEqual(window.side_bar.explorer_root_path, first_workspace)
            self.assertEqual(Path(window.side_bar.file_model.rootPath()), first_workspace)

            window.choose_workspace_directory = lambda: str(second_workspace)
            window.side_bar.action_btn.click()
            self.process_events()

            self.assertEqual(window.command_log[-1], "select_workspace")
            self.assertEqual(window.shell_state.workspace.root_path, second_workspace)
            self.assertEqual(window.side_bar.explorer_root_path, second_workspace)
            self.assertEqual(Path(window.side_bar.file_model.rootPath()), second_workspace)
            self.assertEqual(
                Path(window.side_bar.file_model.filePath(window.side_bar.tree_view.rootIndex())),
                second_workspace,
            )

    def test_explorer_renders_the_real_filesystem_tree(self):
        window = self.create_window()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "alpha.txt").write_text("alpha", encoding="utf-8")
            nested = workspace / "nested"
            nested.mkdir()
            (nested / "beta.py").write_text("print('beta')\n", encoding="utf-8")

            window.set_workspace(workspace)
            self.process_events()

            root_index = window.side_bar.tree_view.rootIndex()
            root_names = sorted(self.child_names(window, root_index))
            self.assertEqual(root_names, ["alpha.txt", "nested"])

            nested_index = self.index_for_path(window, nested)
            window.side_bar.tree_view.expand(nested_index)
            self.wait_until(
                lambda: window.side_bar.file_model.rowCount(nested_index) == 1
            )

            nested_names = self.child_names(window, nested_index)
            self.assertEqual(nested_names, ["beta.py"])

    def test_explorer_activation_opens_files_but_directories_only_expand(self):
        window = self.create_window()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            folder = workspace / "folder"
            folder.mkdir()
            file_path = workspace / "notes.txt"
            file_path.write_text("workspace notes", encoding="utf-8")

            window.set_workspace(workspace)
            self.process_events()

            folder_index = self.index_for_path(window, folder)
            self.assertFalse(window.side_bar.tree_view.isExpanded(folder_index))

            window.side_bar._on_tree_activated(folder_index)
            self.process_events()

            self.assertTrue(window.side_bar.tree_view.isExpanded(folder_index))
            self.assertEqual(window.editor_area.tab_count, 0)
            self.assertIsNone(window.shell_state.active_session)

            window.side_bar._on_tree_activated(folder_index)
            self.process_events()
            self.assertFalse(window.side_bar.tree_view.isExpanded(folder_index))

            file_index = self.index_for_path(window, file_path)
            window.side_bar._on_tree_activated(file_index)
            self.process_events()

            self.assertEqual(window.editor_area.tab_count, 1)
            self.assertIsNotNone(window.shell_state.active_session)
            self.assertEqual(window.shell_state.active_session.path, file_path)
            self.assertEqual(
                window.editor_area.current_editor().toPlainText(),
                "workspace notes",
            )

    def test_non_explorer_panels_show_professional_empty_states(self):
        window = self.create_window()

        expectations = {
            SideBarPanelId.SEARCH: (
                window.side_bar.search_widget,
                "Search",
                "Search features are not configured in this shell yet.",
                "Search is unavailable until a real search workflow is implemented.",
            ),
            SideBarPanelId.SOURCE_CONTROL: (
                window.side_bar.scm_widget,
                "Source Control",
                "Source control insights will appear here when repository integration exists.",
                "No repository workflow is connected in this shell yet.",
            ),
            SideBarPanelId.RUN_AND_DEBUG: (
                window.side_bar.run_widget,
                "Run and Debug",
                "Launch configurations and debug sessions will appear here when available.",
                "Debug tooling is not configured in this shell yet.",
            ),
            SideBarPanelId.EXTENSIONS: (
                window.side_bar.extensions_widget,
                "Extensions",
                "Installed extensions and marketplace results will appear here when supported.",
                "Extension management is unavailable in this shell yet.",
            ),
        }

        for panel_id, (widget, title, body, reason) in expectations.items():
            window.activity_bar.button_for_panel(panel_id).click()
            self.process_events()

            self.assertEqual(window.side_bar.current_panel_id, panel_id)
            self.assertEqual(window.side_bar.title_label.text(), panel_id.title)
            self.assertEqual(widget.title_label.text(), title)
            self.assertEqual(widget.body_label.text(), body)
            self.assertEqual(widget.reason_label.text(), reason)
            combined_text = " ".join(
                [
                    widget.title_label.text(),
                    widget.body_label.text(),
                    widget.reason_label.text(),
                ]
            )
            self.assertNotIn("Placeholder", combined_text)
            self.assertNotIn("placeholder", combined_text)
            self.assertFalse(window.side_bar.action_btn.isVisible())


if __name__ == "__main__":
    unittest.main()
