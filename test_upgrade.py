"""Integration coverage for recovery, editor tools and the student workspace."""
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

import codelab_studio as studio


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = str(Path(self.temp.name) / 'settings.json')
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = studio.App(self.root, settings_path=self.settings)
        self.root.update()

    def tearDown(self):
        if self.root.winfo_exists():
            self.root.destroy()
        self.temp.cleanup()

    def test_failed_save_preserves_original(self):
        path = Path(self.temp.name) / 'safe.c'
        path.write_text('original', encoding='utf-8')
        ed = self.app.open_path(str(path))
        ed.text.insert('end', '\nchanged')
        with patch('os.replace', side_effect=OSError('disk unavailable')):
            with patch.object(studio.messagebox, 'showerror'):
                self.assertFalse(self.app.write_file(ed, str(path)))
        self.assertEqual(path.read_text(encoding='utf-8'), 'original')
        self.assertTrue(ed.modified())

    def test_recovers_unnamed_tab_and_cursor(self):
        self.assertTrue(hasattr(self.app, 'save_session'), 'Recovery snapshots are missing')
        ed = self.app.new_file('cpp', 'int main() {\n    return 42;\n}\n', 'practice.cpp')
        ed.text.insert('2.4', '// keep\n    ')
        ed.text.mark_set('insert', '3.8')
        expected = ed.code()
        self.app.save_session()
        self.root.destroy()
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = studio.App(self.root, settings_path=self.settings)
        self.root.update()
        restored = self.app.current()
        self.assertEqual(restored.code(), expected)
        self.assertEqual(restored.display_name(), 'practice.cpp')
        self.assertEqual(restored.text.index('insert'), '3.8')
        self.assertTrue(restored.modified())

    def test_recovery_never_overwrites_external_change(self):
        self.assertTrue(hasattr(self.app, 'save_session'), 'Recovery snapshots are missing')
        path = Path(self.temp.name) / 'external.c'
        path.write_text('original', encoding='utf-8')
        ed = self.app.open_path(str(path))
        ed.text.insert('end', '\nmy unsaved change')
        self.app.save_session()
        self.root.destroy()
        path.write_text('external edit', encoding='utf-8')
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = studio.App(self.root, settings_path=self.settings)
        self.root.update()
        restored = self.app.current()
        self.assertIsNone(restored.path, 'Conflicting recovery must become a separate unsaved copy')
        self.assertIn('my unsaved change', restored.code())
        self.assertEqual(path.read_text(encoding='utf-8'), 'external edit')

    def test_discarded_tab_stays_out_of_pending_snapshot(self):
        keep = self.app.new_file('c', 'int main(void) { return 0; }\n', 'keep.c')
        dropped = self.app.new_file('c', 'int main(void) { return 1; }\n', 'dropped.c')
        self.app.schedule_session()
        self.app._quitting = True  # the shutdown snapshot in quit() runs with this set
        self.app.save_session(exclude=[dropped])
        self.root.after(900, self.root.quit)
        self.root.mainloop()
        names = [tab['name'] for tab in self.app.session_store.load()['tabs']]
        self.assertIn(keep.display_name(), names)
        self.assertNotIn(dropped.display_name(), names,
                         'A pending snapshot must not restore a tab closed without saving')

    def test_theme_and_snippet_undo(self):
        self.assertTrue(hasattr(self.app, 'set_theme'), 'Light theme is missing')
        self.app.set_theme('light')
        self.assertEqual(self.app.load_settings()['theme'], 'light')
        ed = self.app.new_file('c', 'int main(void) {\n\n}\n', 'snippet.c')
        ed.text.mark_set('insert', '2.0')
        original = ed.code()
        self.app.insert_snippet('for loop')
        self.assertIn('for (', ed.code())
        ed.text.edit_undo()
        self.assertEqual(ed.code(), original)


if __name__ == '__main__':
    unittest.main()
