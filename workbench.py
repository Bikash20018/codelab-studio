"""Workspace navigation shared by the editor, sidebar and command palette."""
import os
from pathlib import Path

from navigation import QuickPicker, SearchDocument, WorkspaceSearch, text_digest


class Workbench:
    def select_editor(self, ed):
        if ed.winfo_exists():
            self.hide_welcome()
            self.nb.select(ed)
            ed.text.focus_set()

    def file_choices(self):
        rows, seen = [], set()
        for ed in self.editors():
            if ed.is_welcome:
                continue
            if ed.path:
                seen.add(os.path.normcase(os.path.abspath(ed.path)))
            rows.append((ed.display_name(), ed.path or 'Unsaved program',
                         lambda e=ed: self.select_editor(e)))
        if self.project:
            for rel in self.project.files:
                path = str(self.project.root / rel)
                if os.path.normcase(path) not in seen:
                    rows.append((rel.name, str(rel), lambda p=path: self.open_path(p)))
        return rows

    def command_choices(self):
        rows = [
            ('New C program', 'Ctrl+N', lambda: self.new_file_dialog('c')),
            ('New C++ program', 'File', lambda: self.new_file_dialog('cpp')),
            ('Open file', 'Ctrl+O', self.open_file),
            ('Open folder', 'Project', self.open_project),
            ('Quick open file', 'Ctrl+P', lambda: self.show_picker(files=True)),
            ('Search workspace', 'Ctrl+Shift+F', self.show_workspace_search),
            ('Save current file', 'Ctrl+S', self.save),
            ('Save all files', 'Ctrl+Alt+S', self.save_all),
            ('Find and replace', 'Ctrl+H', lambda: self.find(replace=True)),
            ('Go to line', 'Ctrl+G', self.goto_line),
            ('Format code', 'Ctrl+Shift+I', self.format_current),
            ('Browse examples', 'Ctrl+E', self.show_examples),
            ('Practice exercises', 'Learn', self.show_practice),
            ('Show welcome', 'Workspace', self.show_welcome),
            ('Toggle focus mode', 'Ctrl+Shift+M', self.toggle_focus_mode),
            ('Use light theme', 'Appearance', lambda: self.set_theme('light')),
            ('Use dark theme', 'Appearance', lambda: self.set_theme('dark')),
            ('Increase code size', 'Ctrl++', lambda: self.zoom(1)),
            ('Decrease code size', 'Ctrl+-', lambda: self.zoom(-1)),
            ('Keyboard shortcuts', 'Help', self.show_shortcuts),
        ]
        if self.busy:
            rows.append(('Stop build or run', 'Shift+F5', self.stop))
        else:
            rows.extend([
                ('Build and run', 'F11', self.compile_and_run),
                ('Build program', 'F9', self.compile),
                ('Start debugging', 'F5', self.start_debug),
                ('Check practice solution', 'Learn', self.check_practice),
            ])
        if self.project:
            rows.extend([('Choose build files', 'Project', self.choose_project_sources),
                         ('Refresh project files', 'Project', self.refresh_project_tree),
                         ('Close folder', 'Project', self.close_project)])
        return rows

    def show_picker(self, files=False):
        existing = getattr(self, '_picker', None)
        if existing and existing.winfo_exists():
            existing.destroy()
        self._picker = QuickPicker(self, files)
        return self._picker

    def show_workspace_search(self):
        existing = getattr(self, '_workspace_search', None)
        if existing and existing.winfo_exists():
            existing.lift()
            existing.entry.focus_set()
            return existing
        self._workspace_search = WorkspaceSearch(self)
        return self._workspace_search

    def search_documents(self):
        """Snapshot Tk buffers on the UI thread; the worker only reads Python data."""
        docs, seen = [], set()
        for ed in self.editors():
            if ed.is_welcome:
                continue
            if ed.path:
                path = Path(ed.path)
                if self.project and not path.is_relative_to(self.project.root):
                    continue
                seen.add(os.path.normcase(str(path)))
            label = str(Path(ed.path).relative_to(self.project.root)) if self.project and ed.path else ed.display_name()
            docs.append(SearchDocument(str(ed), label, ed.path, ed.code()))
        if self.project:
            for rel in self.project.files:
                path = str(self.project.root / rel)
                if os.path.normcase(path) not in seen:
                    docs.append(SearchDocument(path, str(rel), path))
        return docs

    def open_search_hit(self, hit):
        ed = next((ed for ed in self.editors() if str(ed) == hit.document.key or
                   (ed.path and hit.document.path and os.path.normcase(ed.path) == os.path.normcase(hit.document.path))), None)
        if ed is None and hit.document.path:
            ed = self.open_path(hit.document.path)
        if ed is None or text_digest(ed.code()) != hit.digest:
            self.set_status('Source changed or closed; search again to refresh matches')
            return False
        self.hide_welcome()
        self.nb.select(ed)
        ed.text.mark_set('insert', f'{hit.line}.0+{hit.column - 1}c')
        ed.text.see('insert')
        ed.text.focus_set()
        ed.on_cursor_move()
        ed.text.tag_remove('sel', '1.0', 'end')
        ed.text.tag_add('sel', 'insert', f'insert+{hit.length}c')
        return True

    def save_all(self):
        count = 0
        for ed in self.editors():
            if not ed.is_welcome and (ed.modified() or not ed.path):
                if not self.save(ed):
                    self.set_status('Save all stopped; remaining programs have not been saved')
                    return False
                count += 1
        self.set_status(f'Saved {count} programs' if count else 'All programs are saved')
        return True

    def refresh_open_files(self):
        if not hasattr(self, 'open_files'):
            return
        rows = [(str(ed), ('●  ' if ed.modified() else '    ') + ed.display_name())
                for ed in self.editors() if not ed.is_welcome]
        wanted = {key for key, _ in rows}
        for key in self.open_files.get_children():
            if key not in wanted:
                self.open_files.delete(key)
        for key, label in rows:
            if self.open_files.exists(key):
                self.open_files.item(key, text=label)
            else:
                self.open_files.insert('', 'end', iid=key, text=label)
        current = self.current()
        if current and self.open_files.exists(str(current)):
            self.open_files.selection_set(str(current))

    def open_sidebar_file(self):
        selection = self.open_files.selection()
        if selection:
            self.select_editor(self.root.nametowidget(selection[0]))

    def toggle_focus_mode(self):
        active = getattr(self, 'focus_mode', False)
        if active:
            self.workspace.add(self.project_panel, before=self.main_panes, width=self._sidebar_width,
                               minsize=self.px(185), stretch='never')
            self.main_panes.add(self.output_panel, stretch='never', minsize=self.px(150), height=self._output_height)
        else:
            self._sidebar_width = max(self.px(210), self.project_panel.winfo_width())
            self._output_height = max(self.px(230), self.output_panel.winfo_height())
            self.workspace.forget(self.project_panel)
            self.main_panes.forget(self.output_panel)
        self.focus_mode = not active
        self.focus_button.configure(text='Exit focus' if self.focus_mode else 'Focus')
        self.set_status('Focus mode • Ctrl+Shift+M restores the workspace' if self.focus_mode else 'Workspace restored')
