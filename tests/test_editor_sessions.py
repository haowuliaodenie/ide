import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.main_window import MainWindow
from src.models.shell_state import DirtyCloseAction


class EditorSessionWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.windows = []

    def tearDown(self):
        for window in self.windows:
            window.close()
        self.process_events()

    def create_window(self) -> MainWindow:
        window = MainWindow()
        self.windows.append(window)
        window.show()
        self.process_events()
        return window

    def process_events(self, iterations: int = 8) -> None:
        for _ in range(iterations):
            self.app.processEvents()

    def tab_labels(self, window: MainWindow) -> list[str]:
        return [
            window.editor_area.tabs.tab_bar.tabText(index)
            for index in range(window.editor_area.tabs.tab_bar.count())
        ]

    def test_opening_real_file_creates_or_focuses_path_backed_session(self):
        window = self.create_window()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            first_path = workspace / "alpha.py"
            second_path = workspace / "beta.py"
            first_path.write_text("print('alpha')\n", encoding="utf-8")
            second_path.write_text("print('beta')\n", encoding="utf-8")

            first_session = window.open_file(first_path)
            second_session = window.open_file(second_path)
            self.process_events()

            self.assertEqual(window.editor_area.tab_count, 2)
            self.assertEqual(window.shell_state.active_session.session_id, second_session.session_id)

            duplicate_session = window.open_file(first_path)
            self.process_events()

            self.assertIsNotNone(duplicate_session)
            self.assertEqual(duplicate_session.session_id, first_session.session_id)
            self.assertEqual(window.editor_area.tab_count, 2)
            self.assertEqual(window.shell_state.active_session.session_id, first_session.session_id)
            self.assertEqual(window.shell_state.active_session.path, first_path)
            self.assertEqual(
                window.editor_area.current_editor().toPlainText(),
                "print('alpha')\n",
            )
            active_editor = window.editor_area.current_editor()
            self.assertTrue(active_editor.hasFocus() or self.app.focusWidget() is active_editor)

    def test_new_file_creates_unique_untitled_editable_sessions(self):
        window = self.create_window()

        first_session = window.route_command("new_file")
        second_session = window.route_command("new_file")
        self.process_events()

        self.assertEqual(window.editor_area.tab_count, 2)
        self.assertEqual(first_session.display_name, "Untitled-1")
        self.assertEqual(second_session.display_name, "Untitled-2")
        self.assertIsNone(first_session.path)
        self.assertIsNone(second_session.path)
        self.assertEqual(window.shell_state.active_session.session_id, second_session.session_id)
        self.assertEqual(self.tab_labels(window), ["Untitled-1", "Untitled-2"])
        self.assertFalse(window.editor_area.current_editor().isReadOnly())

    def test_dirty_state_is_visible_and_scoped_to_the_edited_tab(self):
        window = self.create_window()

        first_session = window.route_command("new_file")
        second_session = window.route_command("new_file")
        self.process_events()

        window.editor_area.focus_session(first_session.session_id)
        self.process_events()
        window.editor_area.current_editor().setPlainText("modified once")
        self.process_events()

        self.assertTrue(first_session.is_dirty)
        self.assertFalse(second_session.is_dirty)
        self.assertEqual(self.tab_labels(window), ["Untitled-1*", "Untitled-2"])

        window.editor_area.focus_session(second_session.session_id)
        self.process_events()
        self.assertEqual(window.shell_state.active_session.session_id, second_session.session_id)
        self.assertFalse(second_session.is_dirty)
        self.assertEqual(self.tab_labels(window), ["Untitled-1*", "Untitled-2"])

        window.editor_area.focus_session(first_session.session_id)
        self.process_events()
        self.assertEqual(window.shell_state.active_session.session_id, first_session.session_id)
        self.assertTrue(first_session.is_dirty)
        self.assertEqual(self.tab_labels(window), ["Untitled-1*", "Untitled-2"])

    def test_save_writes_to_disk_and_cancelled_save_as_keeps_untitled_session(self):
        window = self.create_window()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            save_target = workspace / "created.py"

            session = window.route_command("new_file")
            self.process_events()
            window.editor_area.current_editor().setPlainText("print('created')\n")
            self.process_events()

            window.choose_save_path = lambda suggested_name: ""
            canceled = window.route_command("save")
            self.process_events()

            self.assertFalse(canceled)
            self.assertIsNone(session.path)
            self.assertEqual(session.display_name, "Untitled-1")
            self.assertTrue(session.is_dirty)
            self.assertFalse(save_target.exists())
            self.assertEqual(self.tab_labels(window), ["Untitled-1*"])

            window.choose_save_path = lambda suggested_name: str(save_target)
            saved = window.route_command("save")
            self.process_events()

            self.assertTrue(saved)
            self.assertEqual(session.path, save_target)
            self.assertEqual(session.display_name, "created.py")
            self.assertFalse(session.is_dirty)
            self.assertTrue(save_target.exists())
            self.assertEqual(save_target.read_text(encoding="utf-8"), "print('created')\n")
            self.assertEqual(self.tab_labels(window), ["created.py"])

            duplicate = window.open_file(save_target)
            self.process_events()

            self.assertEqual(window.editor_area.tab_count, 1)
            self.assertEqual(duplicate.session_id, session.session_id)
            self.assertEqual(window.shell_state.active_session.session_id, session.session_id)

    def test_open_and_save_failures_are_explicit_and_non_destructive(self):
        window = self.create_window()
        session = window.route_command("new_file")
        self.process_events()
        window.editor_area.current_editor().setPlainText("pending changes")
        self.process_events()

        def fail_read(path: Path) -> str:
            raise OSError("read denied")

        def fail_write(path: Path, content: str) -> None:
            raise OSError("disk full")

        window._read_file_text = fail_read
        failed_open = window.open_file(Path("C:/definitely-missing/example.py"))
        self.process_events()

        self.assertIsNone(failed_open)
        self.assertEqual(window.editor_area.tab_count, 1)
        self.assertEqual(window.shell_state.active_session.session_id, session.session_id)
        self.assertEqual(window.bottom_panel.active_panel_id.name.lower(), "output")
        self.assertIn("Failed to open", window.bottom_panel.output_editor.toPlainText())

        window.choose_save_path = lambda suggested_name: "C:/temp/failure.py"
        window._write_file_text = fail_write
        failed_save = window.route_command("save")
        self.process_events()

        self.assertFalse(failed_save)
        self.assertIsNone(session.path)
        self.assertEqual(session.display_name, "Untitled-1")
        self.assertTrue(session.is_dirty)
        self.assertEqual(self.tab_labels(window), ["Untitled-1*"])
        output_text = window.bottom_panel.output_editor.toPlainText()
        self.assertIn("Failed to save", output_text)
        self.assertIn("disk full", output_text)

    def test_dirty_close_requires_explicit_resolution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_target = Path(tmpdir) / "saved-from-close.py"

            cancel_window = self.create_window()
            cancel_session = cancel_window.route_command("new_file")
            self.process_events()
            cancel_window.editor_area.current_editor().setPlainText("cancel close")
            self.process_events()
            cancel_window.resolve_dirty_close = lambda session: DirtyCloseAction.CANCEL

            cancel_window._on_session_close_requested(cancel_session.session_id)
            self.process_events()

            self.assertEqual(cancel_window.editor_area.tab_count, 1)
            self.assertEqual(
                cancel_window.shell_state.active_session.session_id,
                cancel_session.session_id,
            )
            self.assertTrue(cancel_session.is_dirty)
            self.assertFalse(cancel_window.editor_area.is_showing_empty_state())

            discard_window = self.create_window()
            discard_session = discard_window.route_command("new_file")
            self.process_events()
            discard_window.editor_area.current_editor().setPlainText("discard close")
            self.process_events()
            discard_window.resolve_dirty_close = lambda session: DirtyCloseAction.DISCARD

            discard_window._on_session_close_requested(discard_session.session_id)
            self.process_events()

            self.assertEqual(discard_window.editor_area.tab_count, 0)
            self.assertIsNone(discard_window.shell_state.active_session)
            self.assertTrue(discard_window.editor_area.is_showing_empty_state())

            save_window = self.create_window()
            save_session = save_window.route_command("new_file")
            self.process_events()
            save_window.editor_area.current_editor().setPlainText("save close")
            self.process_events()
            save_window.resolve_dirty_close = lambda session: DirtyCloseAction.SAVE
            save_window.choose_save_path = lambda suggested_name: str(save_target)

            save_window._on_session_close_requested(save_session.session_id)
            self.process_events()

            self.assertTrue(save_target.exists())
            self.assertEqual(save_target.read_text(encoding="utf-8"), "save close")
            self.assertEqual(save_window.editor_area.tab_count, 0)
            self.assertIsNone(save_window.shell_state.active_session)
            self.assertTrue(save_window.editor_area.is_showing_empty_state())

    def test_tab_switching_and_non_final_close_keep_active_session_state_in_sync(self):
        window = self.create_window()

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            first_path = workspace / "one.txt"
            second_path = workspace / "two.txt"
            first_path.write_text("one", encoding="utf-8")
            second_path.write_text("two", encoding="utf-8")

            first_session = window.open_file(first_path)
            second_session = window.open_file(second_path)
            self.process_events()

            window.editor_area.tabs.tab_bar.setCurrentIndex(0)
            self.process_events()
            self.assertEqual(window.shell_state.active_session.session_id, first_session.session_id)
            self.assertEqual(window.shell_state.active_session.path, first_path)

            window._on_session_close_requested(second_session.session_id)
            self.process_events()
            self.assertEqual(window.editor_area.tab_count, 1)
            self.assertEqual(window.shell_state.active_session.session_id, first_session.session_id)
            self.assertEqual(window.shell_state.active_session.path, first_path)

            reopened_second = window.open_file(second_path)
            self.process_events()
            self.assertEqual(window.shell_state.active_session.session_id, reopened_second.session_id)

            window._on_session_close_requested(reopened_second.session_id)
            self.process_events()
            self.assertEqual(window.editor_area.tab_count, 1)
            self.assertEqual(window.shell_state.active_session.session_id, first_session.session_id)
            self.assertEqual(window.shell_state.active_session.path, first_path)

    def test_closing_the_last_tab_restores_the_editor_empty_state(self):
        window = self.create_window()
        session = window.route_command("new_file")
        self.process_events()

        window._on_session_close_requested(session.session_id)
        self.process_events()

        self.assertEqual(window.editor_area.tab_count, 0)
        self.assertTrue(window.editor_area.is_showing_empty_state())
        self.assertIsNone(window.shell_state.active_session)
        snapshot = window.status_bar.snapshot()
        self.assertEqual(snapshot["cursor"], "Ln -, Col -")
        self.assertEqual(snapshot["language"], "Language: -")


if __name__ == "__main__":
    unittest.main()
