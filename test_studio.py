"""Regression tests: python -m unittest -v test_studio"""
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import tkinter as tk
import unittest
from unittest.mock import patch

import codelab_studio as studio


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = studio.App(self.root, settings_path=str(Path(self.temp.name) / "settings.json"))
        self.editor = self.app.new_file("c", "int main(void) { return 0; }\n", "demo.c")
        self.root.update()

    def tearDown(self):
        self.root.destroy()
        self.temp.cleanup()

    def test_old_build_does_not_run_or_mark_edited_code(self):
        digest = self.editor.content_hash()
        self.editor.text.insert("1.0", "// changed\n")
        with patch.object(self.app, "launch") as launch:
            self.app.compile_done(self.editor, os.path.abspath("demo.c"), "demo.exe",
                                  digest, (0, "demo.c:1:1: warning: test"), .1, True)
        launch.assert_not_called()
        self.assertFalse(self.editor.diag)

    def test_invalid_utf8_is_not_silently_replaced(self):
        path = Path(self.temp.name) / "legacy.c"
        path.write_bytes(b"// caf\xe9\n")
        with patch.object(studio.messagebox, "showerror") as error:
            self.assertIsNone(self.app.open_path(str(path)))
        error.assert_called_once()
        self.assertEqual(path.read_bytes(), b"// caf\xe9\n")

    def test_save_as_changes_target_language_not_active_tab(self):
        other = self.app.new_file("c", "int x;", "other.c")
        path = str(Path(self.temp.name) / "demo.cpp")
        with patch.object(studio.filedialog, "asksaveasfilename", return_value=path):
            self.assertTrue(self.app.save_as(self.editor))
        self.assertEqual(self.editor.lang, "cpp")
        self.assertEqual(other.lang, "c")

    def test_replace_all_is_literal_and_one_undo(self):
        self.assertTrue(hasattr(self.app, "replace_all"), "Inline replace is missing")
        self.editor.text.delete("1.0", "end")
        self.editor.text.insert("1.0", "cat CAT scatter cat")
        self.editor.text.edit_reset()
        self.app.find_query.set("cat")
        self.app.replace_query.set("dog")
        self.app.find_whole.set(True)
        self.app.replace_all()
        self.assertEqual(self.editor.code(), "dog dog scatter dog")
        self.editor.text.edit_undo()
        self.assertEqual(self.editor.code(), "cat CAT scatter cat")

    def test_find_wrap_case_previous_and_literal_query(self):
        self.editor.text.delete("1.0", "end")
        self.editor.text.insert("1.0", "a.b A.B axb a.b")
        self.app.find_query.set("a.b")
        self.editor.text.mark_set("insert", "1.0")
        self.app.find_next()
        self.assertEqual(self.editor.text.index("sel.first"), "1.0")
        self.app.find_next()
        self.assertEqual(self.editor.text.index("sel.first"), "1.4")
        self.app.find_next(backwards=True)
        self.assertEqual(self.editor.text.index("sel.first"), "1.0")
        self.app.find_next(backwards=True)
        self.assertEqual(self.editor.text.index("sel.first"), "1.12")
        self.app.find_case.set(True)
        self.assertEqual(len(self.app.search_matches()), 2)

    def test_preferences_and_recent_files_survive_restart(self):
        path = str(Path(self.temp.name) / "saved.c")
        self.app.write_file(self.editor, path)
        self.app.run_in_panel.set(True)
        self.app.zoom(2)
        settings = self.app.load_settings()
        self.assertEqual(settings["recent_files"], [path])
        self.assertTrue(settings["run_in_panel"])
        self.assertEqual(settings["font_size"], 14)
        Path(self.app.settings_path).write_text('{broken', encoding="utf-8")
        self.assertEqual(self.app.load_settings(), {})

    def test_problem_link_cannot_jump_after_edit(self):
        digest = self.editor.content_hash()
        self.app.compile_done(self.editor, os.path.abspath("demo.c"), "demo.exe",
                              digest, (1, "demo.c:1:5: error: expected expression"), .1, False)
        rows = self.app.problems.get_children()
        self.assertEqual(len(rows), 1)
        self.editor.text.insert("1.0", "// new line\n")
        self.app.problems.selection_set(rows[0])
        with patch.object(self.app, "goto") as goto:
            self.app.goto_problem()
        goto.assert_not_called()

    def wait_for_job(self):
        deadline = time.monotonic() + 20
        while self.app.busy and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.02)
        self.root.update()
        self.assertFalse(self.app.busy, "build/run did not finish")

    def test_real_c_and_cpp_compile_and_panel_input(self):
        if not (self.app.gcc and self.app.gpp):
            self.skipTest("GCC is not installed")
        for lang, code in (
            ("c", '#include <stdio.h>\nint main(void) { int n; scanf("%d", &n); printf("answer=%d", n*2); }'),
            ("cpp", '#include <iostream>\nint main() { int n; std::cin >> n; std::cout << "answer=" << n*2; }'),
        ):
            with self.subTest(lang=lang):
                ed = self.app.new_file(lang, code, "input." + lang)
                self.app.write_file(ed, str(Path(self.temp.name) / ("input." + lang)))
                self.app.run_in_panel.set(True)
                self.app.stdin_box.delete("1.0", "end")
                self.app.stdin_box.insert("1.0", "21")
                self.app.compile_and_run()
                self.wait_for_job()
                output = self.app.output.get("1.0", "end")
                self.assertIn("Build succeeded", output)
                self.assertIn("answer=42", output)
                self.assertIn("exit code 0", output)

    def test_stop_button_recovers_from_infinite_program(self):
        if not self.app.gcc:
            self.skipTest("GCC is not installed")
        ed = self.app.new_file("c", "int main(void) { for (;;) {} }", "loop.c")
        self.app.write_file(ed, str(Path(self.temp.name) / "loop.c"))
        self.app.compile()
        self.wait_for_job()
        self.app.run_in_panel.set(True)
        self.app.run()
        self.root.after(200, self.app.stop)
        self.wait_for_job()
        self.assertIn("Program stopped by you", self.app.output.get("1.0", "end"))
        self.assertEqual(self.app.run_button.cget("state"), "normal")

    def test_readonly_output_rejects_paste(self):
        before = self.app.output.get("1.0", "end")
        self.root.clipboard_clear()
        self.root.clipboard_append("this must not be inserted")
        self.app.output.event_generate("<<Paste>>")
        self.assertEqual(self.app.output.get("1.0", "end"), before)


class ExecutionTests(unittest.TestCase):
    def run_program(self, source, **kwargs):
        self.assertTrue(hasattr(studio, "run_process"), "Bounded, cancellable runner is missing")
        return studio.run_process([sys.executable, "-c", source], **kwargs)

    def test_stdin_stdout_stderr_and_exit_code(self):
        result = self.run_program("import sys; print(input()); print('oops', file=sys.stderr); sys.exit(3)",
                                  input_text="hello\n", timeout=3)
        self.assertEqual(result.stdout.strip(), "hello")
        self.assertEqual(result.stderr.strip(), "oops")
        self.assertEqual(result.returncode, 3)

    def test_output_flood_is_bounded(self):
        result = self.run_program("import os\nwhile True: os.write(1, b'x' * 8192)",
                                  timeout=5, output_limit=16384)
        self.assertEqual(result.reason, "output_limit")
        self.assertLessEqual(len(result.stdout), 16384)

    def test_timeout_and_cancellation(self):
        result = self.run_program("import time; time.sleep(30)", timeout=.15)
        self.assertEqual(result.reason, "timeout")
        cancel = threading.Event()
        timer = threading.Timer(.15, cancel.set)
        timer.start()
        try:
            start = time.monotonic()
            result = self.run_program("import time; time.sleep(30)", timeout=5, cancel=cancel)
            self.assertEqual(result.reason, "cancelled")
            self.assertLess(time.monotonic() - start, 4)
        finally:
            timer.cancel()

    def test_stderr_flood_and_unconsumed_input_do_not_deadlock(self):
        result = self.run_program("import os\nwhile True: os.write(2, b'x' * 8192)",
                                  input_text="x" * 500_000, timeout=3, output_limit=8192)
        self.assertEqual(result.reason, "output_limit")
        self.assertLessEqual(len(result.stderr), 8192)


if __name__ == "__main__":
    unittest.main()
