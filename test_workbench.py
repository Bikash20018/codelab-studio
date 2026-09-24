"""Navigation must reflect live buffers and never jump to stale search locations."""
from pathlib import Path
import tempfile
import threading
import time
import tkinter as tk
import unittest

import codelab_studio as studio


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = studio.App(self.root, settings_path=str(Path(self.temp.name) / 'settings.json'))
        self.root.update()

    def tearDown(self):
        self.root.destroy()
        self.temp.cleanup()

    def feature(self, name):
        self.assertTrue(hasattr(self.app, name), f'Missing workspace feature: {name}')
        return getattr(self.app, name)

    def test_quick_open_includes_unsaved_tabs_without_duplicates(self):
        items = self.feature('file_choices')
        folder = Path(self.temp.name)
        (folder / 'main.c').write_text('int main() {}', encoding='utf-8')
        self.app.open_project(str(folder))
        saved = self.app.open_path(str(folder / 'main.c'))
        draft = self.app.new_file('cpp', 'int value;', 'draft.cpp')
        choices = items()
        self.assertEqual(sum(row[0] == 'main.c' for row in choices), 1)
        row = next(row for row in choices if row[0] == 'draft.cpp')
        self.app.nb.select(saved)
        row[2]()
        self.assertIs(self.app.current(), draft)

    def test_search_uses_unsaved_buffer_and_navigates_to_exact_match(self):
        snapshot = self.feature('search_documents')
        from navigation import search_documents
        path = Path(self.temp.name) / 'main.c'
        path.write_text('old_disk_value\n', encoding='utf-8')
        self.app.open_project(self.temp.name)
        ed = self.app.open_path(str(path))
        self.app.replace_editor_text(ed, 'int value;\nvalue += 2;\n')
        report = search_documents(snapshot(), 'value')
        self.assertEqual([(hit.line, hit.column) for hit in report.hits], [(1, 5), (2, 1)])
        self.assertEqual(search_documents(snapshot(), 'old_disk_value').hits, [])
        self.assertTrue(self.app.open_search_hit(report.hits[1]))
        self.assertEqual(ed.text.get('sel.first', 'sel.last'), 'value')
        self.assertEqual(ed.text.index('insert'), '2.0')

    def test_search_refuses_stale_locations(self):
        snapshot = self.feature('search_documents')
        from navigation import search_documents
        ed = self.app.new_file('c', 'int value;\n', 'draft.c')
        hit = search_documents(snapshot(), 'value').hits[0]
        ed.text.insert('1.0', '// new line\n')
        self.assertFalse(self.app.open_search_hit(hit))
        self.assertIn('changed', self.app.status_msg.cget('text').lower())

    def test_focus_mode_restores_sidebar_and_output(self):
        toggle = self.feature('toggle_focus_mode')
        before = (self.app.workspace.panes(), self.app.main_panes.panes())
        toggle()
        self.assertNotIn(str(self.app.project_panel), self.app.workspace.panes())
        self.assertNotIn(str(self.app.output_panel), self.app.main_panes.panes())
        toggle()
        self.assertEqual((self.app.workspace.panes(), self.app.main_panes.panes()), before)

    def test_new_window_dark_theme_is_not_contaminated_by_previous_light_window(self):
        original = self.app.colors['bg']
        self.app.set_theme('light')
        self.root.destroy()
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = studio.App(self.root, settings_path=str(Path(self.temp.name) / 'fresh.json'))
        self.assertEqual(self.app.colors['bg'], original)
        self.app.set_theme('dark')
        self.assertEqual(self.app.theme_var.get(), 'dark')

    def test_edited_welcome_is_included_in_navigation_and_recovery(self):
        ed = self.app.current()
        ed.text.insert('end', '// my first edit\n')
        self.root.update()
        self.assertFalse(ed.is_welcome)
        self.assertTrue(any(row[0] == 'welcome.c' for row in self.app.file_choices()))
        self.assertTrue(any(doc.key == str(ed) for doc in self.app.search_documents()))
        self.app.save_session()
        self.assertTrue(any('my first edit' in tab['code'] for tab in self.app.session_store.load()['tabs']))

    def test_search_highlights_after_non_bmp_character(self):
        from navigation import search_documents
        ed = self.app.new_file('c', '// 😀 value\n', 'unicode.c')
        hit = search_documents(self.app.search_documents(), 'value').hits[0]
        self.assertTrue(self.app.open_search_hit(hit))
        self.assertEqual(ed.text.get('sel.first', 'sel.last'), 'value')

    def test_palette_executes_filtered_command_and_closes(self):
        picker = self.app.show_picker()
        picker.query.set('theme light')
        picker.accept()
        self.assertFalse(picker.winfo_exists())
        self.assertEqual(self.app.theme, 'light')

    def test_background_search_delivers_results_and_opens_buffer(self):
        ed = self.app.new_file('c', 'int total = 42;\n', 'answer.c')
        search = self.app.show_workspace_search()
        search.query.set('total')
        search.start()
        deadline = time.monotonic() + 5
        while not search.table.get_children() and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.02)
        self.assertEqual(len(search.table.get_children()), 1)
        search.table.selection_set('0')
        search.open_hit()
        self.assertFalse(search.winfo_exists())
        self.assertEqual(ed.text.get('sel.first', 'sel.last'), 'total')

    def test_save_all_persists_each_modified_file(self):
        editors = []
        for name in ('one.c', 'two.c'):
            path = Path(self.temp.name) / name
            path.write_text('int n;\n', encoding='utf-8')
            ed = self.app.open_path(str(path))
            ed.text.insert('1.0', '// updated\n')
            editors.append(ed)
        self.assertTrue(self.app.save_all())
        for ed in editors:
            self.assertFalse(ed.modified())
            self.assertEqual(Path(ed.path).read_text(encoding='utf-8'), '// updated\nint n;\n')

    def test_sidebar_shortcuts_fit_at_high_dpi(self):
        self.root.destroy()
        self.root = tk.Tk()
        self.root.tk.call('tk', 'scaling', 2.0)
        self.app = studio.App(self.root, settings_path=str(Path(self.temp.name) / 'dpi.json'))
        self.root.update()
        def children(widget):
            for child in widget.winfo_children():
                yield child
                yield from children(child)
        search = next(widget for widget in children(self.app.project_panel)
                      if isinstance(widget, tk.Button) and str(widget.cget('text')).startswith('Find in files'))
        self.assertGreaterEqual(search.winfo_width(), search.winfo_reqwidth())
        self.assertGreater(self.app.project_tree.winfo_height(), self.app.px(62))


class SearchTests(unittest.TestCase):
    def api(self):
        import importlib.util
        self.assertIsNotNone(importlib.util.find_spec('navigation'), 'Workspace search is missing')
        import navigation
        return navigation

    def test_case_words_unicode_and_result_limit(self):
        nav = self.api()
        docs = [nav.SearchDocument('draft', 'draft.c', None, 'café value VALUE values\nvalue')]
        report = nav.search_documents(docs, 'value', whole_word=True, limit=2)
        self.assertEqual([hit.column for hit in report.hits], [6, 12])
        self.assertTrue(report.truncated)
        report = nav.search_documents(docs, 'value', match_case=True, whole_word=True)
        self.assertEqual([(hit.line, hit.column) for hit in report.hits], [(1, 6), (2, 1)])

    def test_missing_binary_large_files_and_cancellation(self):
        nav = self.api()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'large.c'
            path.write_text('value' * 100, encoding='utf-8')
            docs = [nav.SearchDocument('large', 'large.c', str(path)),
                    nav.SearchDocument('missing', 'missing.c', str(Path(folder) / 'missing.c')),
                    nav.SearchDocument('binary', 'binary.c', None, 'value\x00')]
            report = nav.search_documents(docs, 'value', max_bytes=64)
            self.assertEqual(report.hits, [])
            self.assertEqual(report.skipped, 3)
            cancelled = threading.Event()
            cancelled.set()
            report = nav.search_documents(docs, 'value', cancel=cancelled)
            self.assertEqual(report.hits, [])
            self.assertTrue(report.cancelled)

    def test_command_filter_matches_multiple_terms_and_prioritizes_prefix(self):
        nav = self.api()
        rows = [('Open folder', 'Project', None), ('Close folder', 'Project', None),
                ('Format code', 'Editor', None)]
        self.assertEqual(nav.filter_choices(rows, 'folder open'), [rows[0]])
        self.assertEqual(nav.filter_choices(rows, 'format')[0], rows[2])
        self.assertEqual(nav.filter_choices(rows, 'nothing'), [])


if __name__ == '__main__':
    unittest.main()
