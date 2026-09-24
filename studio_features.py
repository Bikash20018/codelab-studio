"""Student workspace features, kept separate from the core text editor."""
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from recovery import SessionStore, fingerprint
from workbench import Workbench


LIGHT = {
    'bg': '#f8faff', 'panel': '#edf2f8', 'header': '#edf2f8', 'gutter': '#f0f4fa',
    'console': '#ffffff', 'btn': '#dde7f2', 'btn_hover': '#cedced', 'border': '#c9d5e5',
    'fg': '#25354a', 'muted': '#52647c', 'accent': '#255eaa', 'accent_fill': '#2863ad',
    'accent_hover': '#215797', 'go': '#197455', 'go_hover': '#146044', 'go_text': '#12694e',
    'status': '#edf2f8', 'cursor': '#255eaa', 'sel': '#d6e6fc', 'curline': '#eaf1fb',
    'errline': '#fff0f1', 'warnline': '#fff5dc', 'find': '#8b5d00',
    'danger': '#b52240', 'warn': '#895d00', 'ok': '#087153', 'note': '#245a9d',
    'func': '#805111', 'num': '#a84824', 'kw': '#80349d', 'type': '#245a9d',
    'pre': '#136779', 'str': '#416e1a', 'com': '#62708a',
}


class WorkspaceFeatures(Workbench):
    def init_features(self, colors, find_tool, resource, dark_colors):
        self.colors = colors
        self.dark_colors = dict(dark_colors)
        self.find_tool = find_tool
        self.resource = resource
        self.theme = self.settings.get('theme', 'dark')
        colors.update(LIGHT if self.theme == 'light' else self.dark_colors)
        self._session_job = None
        self._session_ready = False
        self._quitting = False
        self.session_store = None
        try:
            self.session_store = SessionStore(self.settings_path)
        except OSError:
            pass
        self.project = None
        self.project_exe = None
        self.project_snapshot = {}
        self.live_process = None
        self.debugger = None
        self.debug_paused = False
        self._debug_requested = False
        self._practice_requested = None
        self.practice_id = None
        self.practice_progress = dict(self.settings.get('practice_progress', {}))
        self.run_limit = self.settings.get('run_limit', 120)
        self.welcome_frame = None
        self.project_panel = None
        self._session_tick = None
        self.focus_mode = False

    def cancel_timer(self, timer):
        if timer:
            try:
                self.root.after_cancel(timer)
            except tk.TclError:
                pass

    def schedule_session(self):
        if not self._session_ready or self._quitting:
            return
        self.cancel_timer(self._session_job)
        self._session_job = self.root.after(750, self.save_session)

    def save_session(self, exclude=()):
        # A direct call must also drop the debounced one, or that orphan fires later
        # without this call's exclusions and resurrects tabs closed on purpose.
        self.cancel_timer(self._session_job)
        self._session_job = None
        if not self.session_store:
            return
        tabs = []
        active = 0
        for ed in self.editors():
            if ed in exclude or ed.is_welcome:
                continue
            if ed is self.current():
                active = len(tabs)
            tabs.append({'name': ed.display_name(), 'path': ed.path, 'lang': ed.lang,
                         'code': ed.code(), 'modified': ed.modified(),
                         'cursor': ed.text.index('insert'), 'yview': ed.text.yview()[0],
                         'disk': getattr(ed, 'disk_fingerprint', None),
                         'breakpoints': sorted(getattr(ed, 'breakpoints', set())),
                         'exercise': getattr(ed, 'exercise_id', None)})
        try:
            self.session_store.save({'tabs': tabs, 'active': active,
                                     'project': str(self.project.root) if self.project else None})
        except OSError:
            self.set_status('Recovery snapshot could not be saved', error=True)

    def session_tick(self):
        # Periodic snapshots also catch continuous typing (Tk Modified only fires
        # when its flag changes) and cursor changes made by keyboard shortcuts.
        if self._session_ready and not self._quitting:
            self.save_session()
        self._session_tick = self.root.after(5000, self.session_tick)

    def restore_session(self):
        data = self.session_store.load() if self.session_store else {}
        recovered = []
        for tab in data.get('tabs', []):
            path = tab.get('path')
            code = tab['code']
            dirty = bool(tab.get('modified')) or not path
            conflict = False
            if path:
                current_disk = fingerprint(path)
                if dirty and current_disk != tab.get('disk'):
                    conflict = True
                    path = None
                elif not dirty:
                    try:
                        code = Path(path).read_text(encoding='utf-8-sig')
                    except (OSError, UnicodeError):
                        path = None
                        dirty = True
            name = tab['name']
            if conflict:
                stem, ext = os.path.splitext(name)
                name = stem + ' (recovered)' + ext
            ed = self.new_file(tab['lang'], code, name)
            ed.path = path
            ed.disk_fingerprint = fingerprint(path) if path else None
            ed.text.edit_modified(dirty)
            ed.exercise_id = tab.get('exercise')
            ed.breakpoints = {n for n in tab.get('breakpoints', []) if isinstance(n, int) and n > 0}
            try:
                ed.text.mark_set('insert', str(tab.get('cursor', '1.0')))
                ed.text.yview_moveto(float(tab.get('yview', 0)))
            except (tk.TclError, ValueError, TypeError):
                pass
            self.refresh_tab(ed)
            recovered.append(ed)
        project = data.get('project')
        if isinstance(project, str) and os.path.isdir(project):
            self.open_project(project)
        if recovered:
            selected = data.get('active', 0)
            if not isinstance(selected, int):
                selected = 0
            self.nb.select(recovered[max(0, min(selected, len(recovered) - 1))])
            self.set_status('Workspace restored · unsaved work recovered')
        return bool(recovered)

    def close_features(self):
        for timer in (self._session_job, self._session_tick):
            self.cancel_timer(timer)
        if self.live_process:
            self.live_process.stop()
        if self.debugger:
            self.debugger.stop()
        if self.session_store:
            self.session_store.close()

    def hide_welcome(self):
        if self.welcome_frame is not None:
            self.welcome_frame.destroy()
            self.welcome_frame = None

    def show_welcome(self):
        self.hide_welcome()
        c = self.colors
        self.welcome_frame = frame = tk.Frame(self.nb, bg=c['bg'])
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        canvas = tk.Canvas(frame, bg=c['bg'], highlightthickness=0)
        scroll = ttk.Scrollbar(frame, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        canvas.pack(fill='both', expand=True)
        host = tk.Frame(canvas, bg=c['bg'])
        window = canvas.create_window(0, 0, window=host, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window, width=e.width))
        host.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        content = tk.Frame(host, bg=c['bg'])
        content.pack(fill='x', padx=28, pady=22)
        tk.Label(content, text='Your next idea,\nready to run.', font=(self.ui, 29, 'bold'),
                 justify='left', bg=c['bg'], fg=c['fg']).pack(anchor='w', pady=(0, 10))
        tk.Label(content, text='A workspace for writing, testing and understanding C and C++.',
                 wraplength=490, justify='left', font=(self.ui, 11), bg=c['bg'], fg=c['muted']).pack(anchor='w', pady=(0, 16))
        actions = tk.Frame(content, bg=c['bg'])
        actions.pack(anchor='w')
        self.button(actions, 'New C program', lambda: self.new_file_dialog('c'), 'primary')
        self.button(actions, 'New C++ program', lambda: self.new_file_dialog('cpp'))
        self.button(actions, 'Open folder', self.open_project)
        tk.Frame(content, bg=c['border'], height=1).pack(fill='x', pady=(22, 16))
        bottom = tk.Frame(content, bg=c['bg'])
        bottom.pack(fill='x')
        recent = tk.Frame(bottom, bg=c['bg'])
        recent.pack(side='left', fill='both', expand=True)
        tk.Label(recent, text='Pick up where you left off', bg=c['bg'], fg=c['fg'],
                 font=(self.ui, 11, 'bold')).pack(anchor='w', pady=(0, 8))
        for path in self.recent_files[:3]:
            tk.Button(recent, text=os.path.basename(path),
                      command=lambda p=path: self.open_path(p), bg=c['bg'], fg=c['accent'],
                      activebackground=c['sel'], activeforeground=c['fg'],
                      relief='flat', anchor='w', font=(self.ui, 10), cursor='hand2').pack(anchor='w')
        if not self.recent_files:
            tk.Label(recent, text='Your recent files will appear here.', bg=c['bg'],
                     fg=c['muted'], font=(self.ui, 10)).pack(anchor='w')
        guide = tk.Frame(bottom, bg=c['bg'])
        guide.pack(side='right', anchor='n', padx=(20, 0))
        tk.Label(guide, text='A faster way around', bg=c['bg'], fg=c['fg'],
                 font=(self.ui, 11, 'bold')).pack(anchor='w', pady=(0, 8))
        for shortcut, label in (('Ctrl+P', 'Open a file'), ('Ctrl+Shift+P', 'Find any command'), ('F11', 'Build and run')):
            tk.Label(guide, text=f'{shortcut}   {label}', bg=c['bg'], fg=c['muted'],
                     font=(self.ui, 9)).pack(anchor='w', pady=2)
        tk.Button(content, text='Continue to editor', command=self.hide_welcome,
                  bg=c['bg'], fg=c['accent'], activebackground=c['sel'], activeforeground=c['fg'],
                  relief='flat', cursor='hand2', font=(self.ui, 10)).pack(anchor='w', pady=(15, 0))
        def bind_scroll(widget):
            widget.bind('<MouseWheel>', lambda e: canvas.yview_scroll(-1 if e.delta > 0 else 1, 'units'))
            for child in widget.winfo_children():
                bind_scroll(child)
        bind_scroll(host)

    def set_theme(self, theme):
        if theme not in ('light', 'dark'):
            return
        old = dict(self.colors)
        self.colors.update(LIGHT if theme == 'light' else self.dark_colors)
        self.theme = theme
        if hasattr(self, 'theme_var'):
            self.theme_var.set(theme)
        mapping = {v.lower(): self.colors[k] for k, v in old.items()}

        def recolor(widget):
            for option in ('background', 'foreground', 'activebackground', 'activeforeground',
                           'selectbackground', 'selectforeground', 'insertbackground',
                           'highlightbackground', 'highlightcolor', 'disabledforeground',
                           'inactiveselectbackground'):
                try:
                    value = str(widget.cget(option)).lower()
                    if value in mapping:
                        widget.configure(**{option: mapping[value]})
                except tk.TclError:
                    pass
            for child in widget.winfo_children():
                recolor(child)
            kind = getattr(widget, '_button_kind', None)
            if kind:
                normal, hover, foreground = {'normal': ('btn', 'btn_hover', 'fg'),
                    'quiet': ('panel', 'btn', 'muted'), 'primary': ('accent_fill', 'accent_hover', None),
                    'go': ('go', 'go_hover', None)}[kind]
                widget.configure(bg=self.colors[normal], activebackground=self.colors[hover],
                                 fg=self.colors[foreground] if foreground else 'white',
                                 activeforeground=self.colors[foreground] if foreground else 'white',
                                 highlightbackground=self.colors[normal])
        recolor(self.root)
        self.style_ttk()
        for ed in self.editors():
            ed.configure_tags()
            ed.text.tag_configure('debugline', background=self.colors['sel'])
            ed.draw_gutter()
        for tag, key in (('ok', 'ok'), ('err', 'danger'), ('warn', 'warn'), ('note', 'note'),
                         ('info', 'muted'), ('code', 'muted'), ('prog', 'fg'), ('head', 'fg'), ('hint', 'find')):
            self.output.tag_configure(tag, foreground=self.colors[key])
        self.problems.tag_configure('error', foreground=self.colors['danger'])
        self.problems.tag_configure('warning', foreground=self.colors['warn'])
        if self.welcome_frame:
            self.show_welcome()
        self.save_settings()

    def replace_editor_text(self, ed, code):
        cursor = ed.text.index('insert')
        ed.text.edit_separator()
        ed.text.configure(autoseparators=False)
        try:
            ed.text.delete('1.0', 'end')
            ed.text.insert('1.0', code)
        finally:
            ed.text.configure(autoseparators=True)
            ed.text.edit_separator()
        ed.text.mark_set('insert', cursor)
        self.schedule_session()

    def format_current(self):
        from formatting import format_code
        ed = self.current()
        if not ed or self.busy:
            return
        tool = self.find_tool('clang-format')
        for candidate in (self.resource('tools', 'clang-format.exe'),
                          str(Path(__file__).parent / '.venv/Lib/site-packages/clang_format/data/bin/clang-format.exe')):
            if not tool and os.path.isfile(candidate):
                tool = candidate
        if not tool:
            messagebox.showerror('Format code', 'clang-format was not found. Use the full CodeLab Studio package '
                                 'or install clang-format and add it to PATH.', parent=self.root)
            return
        try:
            formatted = format_code(ed.code(), ed.lang, tool)
            if formatted != ed.code():
                self.replace_editor_text(ed, formatted)
            self.set_status('Code formatted · Ctrl+Z to undo')
        except (OSError, RuntimeError, ValueError) as ex:
            messagebox.showerror('Format code', str(ex), parent=self.root)

    def insert_snippet(self, label):
        from formatting import SNIPPETS
        ed = self.current()
        if not ed:
            return
        snippets = SNIPPETS[ed.lang]
        code = next((value for name, value in snippets.items() if name.lower() == label.lower()), None)
        if code is None:
            self.set_status('This template is only available for C++')
            return
        self.hide_welcome()
        ed.text.edit_separator()
        ed.text.insert('insert', code)
        ed.text.edit_separator()
        ed.text.focus_set()
        self.schedule_session()

    def feature_menus(self, menubar):
        tools = tk.Menu(menubar, tearoff=False)
        tools.add_command(label='Format Code', accelerator='Ctrl+Shift+I', command=self.format_current)
        snippets = tk.Menu(tools, tearoff=False)
        for name in ('for loop', 'while loop', 'if / else', 'function', 'class'):
            snippets.add_command(label=name.title(), command=lambda label=name: self.insert_snippet(label))
        tools.add_cascade(label='Insert Template', menu=snippets)
        tools.add_separator()
        tools.add_command(label='Practice Exercises', command=self.show_practice)
        menubar.add_cascade(label='Learn & Tools', menu=tools)
        project = tk.Menu(menubar, tearoff=False)
        project.add_command(label='Open Folder...', command=self.open_project)
        project.add_command(label='Choose Build Files...', command=self.choose_project_sources)
        project.add_command(label='Refresh Files', command=self.refresh_project_tree)
        project.add_command(label='Close Folder', command=self.close_project)
        menubar.add_cascade(label='Project', menu=project)
        debug = tk.Menu(menubar, tearoff=False)
        debug.add_command(label='Start Debugging', accelerator='F5', command=self.start_debug)
        debug.add_command(label='Toggle Breakpoint', accelerator='F8', command=self.toggle_breakpoint)
        debug.add_separator()
        debug.add_command(label='Step Over', accelerator='F6', command=lambda: self.debug_command('next'))
        debug.add_command(label='Step Into', accelerator='F7', command=lambda: self.debug_command('step'))
        debug.add_command(label='Continue', command=lambda: self.debug_command('continue_'))
        debug.add_command(label='Stop Debugging', command=self.stop)
        menubar.add_cascade(label='Debug', menu=debug)
        view = tk.Menu(menubar, tearoff=False)
        view.add_command(label='Welcome', command=self.show_welcome)
        view.add_command(label='Command Palette', accelerator='Ctrl+Shift+P', command=self.show_picker)
        view.add_command(label='Quick Open File', accelerator='Ctrl+P', command=lambda: self.show_picker(files=True))
        view.add_command(label='Focus Mode', accelerator='Ctrl+Shift+M', command=self.toggle_focus_mode)
        view.add_separator()
        self.theme_var = tk.StringVar(value=self.theme)
        for value in ('dark', 'light'):
            view.add_radiobutton(label=value.title() + ' Theme', value=value, variable=self.theme_var,
                                 command=lambda t=value: self.set_theme(t))
        menubar.add_cascade(label='View', menu=view)

    def build_workspace(self, parent):
        c = self.colors
        self.workspace = tk.PanedWindow(parent, orient='horizontal', bg=c['border'], sashwidth=4, bd=0)
        self.project_panel = tk.Frame(self.workspace, bg=c['panel'])
        self.workspace.add(self.project_panel, width=self.px(225), minsize=self.px(185), stretch='never')
        top = tk.Frame(self.project_panel, bg=c['panel'], padx=9)
        top.pack(fill='x', pady=(8, 0))
        tk.Label(top, text='Workspace', bg=c['panel'], fg=c['fg'], font=(self.ui, 11, 'bold')).pack(side='left', padx=4)
        self.focus_button = self.button(top, 'Focus', self.toggle_focus_mode, 'quiet', side='right')
        self.sidebar_action('Find in files', 'Ctrl+Shift+F', self.show_workspace_search)
        self.sidebar_action('Quick open', 'Ctrl+P', lambda: self.show_picker(files=True))
        footer = tk.Frame(self.project_panel, bg=c['panel'])
        footer.pack(side='bottom', fill='x', padx=8, pady=(5, 8))
        tk.Frame(footer, bg=c['border'], height=1).pack(fill='x', padx=6, pady=5)
        for actions in ((('Examples', self.show_examples), ('Practice', self.show_practice)),
                        (('Format', self.format_current), ('Check solution', self.check_practice))):
            row = tk.Frame(footer, bg=c['panel'])
            row.pack(fill='x')
            for title, callback in actions:
                button = self.button(row, title, callback, 'quiet')
                button.pack_configure(pady=1, expand=True, fill='x')
                button.configure(font=(self.ui, 9), padx=6)
        tk.Frame(self.project_panel, bg=c['border'], height=1).pack(fill='x', padx=14, pady=5)
        tk.Label(self.project_panel, text='Open programs', bg=c['panel'], fg=c['muted'],
                 font=(self.ui, 9, 'bold'), anchor='w', padx=15, pady=5).pack(fill='x')
        self.open_files = ttk.Treeview(self.project_panel, show='tree', height=2,
                                       style='Examples.Treeview', selectmode='browse')
        self.open_files.column('#0', width=self.px(195), minwidth=self.px(120))
        self.open_files.pack(fill='x', padx=8)
        self.open_files.bind('<ButtonRelease-1>', lambda e: self.open_sidebar_file())
        self.open_files.bind('<Return>', lambda e: self.open_sidebar_file())
        project_head = tk.Frame(self.project_panel, bg=c['panel'])
        project_head.pack(fill='x', padx=10, pady=(10, 0))
        tk.Label(project_head, text='Project files', bg=c['panel'], fg=c['muted'],
                 font=(self.ui, 9, 'bold')).pack(side='left', padx=4)
        self.button(project_head, 'Folder…', self.open_project, 'quiet', side='right')
        self.project_title = tk.Label(self.project_panel, bg=c['panel'], fg=c['muted'], wraplength=self.px(195),
                                      font=(self.ui, 8), padx=8, pady=6)
        self.project_title.pack(side='bottom', fill='x')
        tree_body = tk.Frame(self.project_panel, bg=c['panel'])
        tree_body.pack(fill='both', expand=True, padx=8)
        self.project_tree = ttk.Treeview(tree_body, show='tree', style='Examples.Treeview', selectmode='browse', height=2)
        self.project_tree.column('#0', width=self.px(190), minwidth=self.px(120))
        scrollbar = ttk.Scrollbar(tree_body, command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.project_tree.pack(fill='both', expand=True)
        self.project_tree.bind('<Double-1>', lambda e: self.open_project_file())
        self.project_tree.bind('<Return>', lambda e: self.open_project_file())
        self.project_title.configure(text='Open a folder to work with multiple files.')
        self._project_files = {}
        return self.workspace

    def sidebar_action(self, label, shortcut, command):
        row = tk.Frame(self.project_panel, bg=self.colors['panel'])
        row.pack(fill='x', padx=8)
        button = self.button(row, label, command, 'quiet')
        button.pack_configure(fill='x', expand=True, pady=0)
        button.configure(anchor='w', padx=8, pady=5, font=(self.ui, 9))
        if shortcut:
            button.configure(text=f'{label}   {shortcut}')

    def open_project(self, folder=None):
        from projects import Project
        if self.busy:
            self.set_status('Stop the current job before changing folders')
            return
        folder = folder or filedialog.askdirectory(parent=self.root, title='Open project folder')
        if not folder:
            return
        try:
            self.project = Project(folder)
        except (OSError, ValueError) as ex:
            messagebox.showerror('Open folder', str(ex), parent=self.root)
            return
        self.hide_welcome()
        self.project_exe = None
        if self.focus_mode:
            self.toggle_focus_mode()
        if str(self.project_panel) not in self.workspace.panes():
            self.workspace.add(self.project_panel, before=self.main_panes, width=self.px(225), minsize=self.px(185), stretch='never')
        self.refresh_project_tree()
        self.set_status('Project active · Build compiles the selected files in this folder')
        self.schedule_session()

    def close_project(self):
        if self.busy:
            return
        self.project = None
        self.project_exe = None
        self.project_tree.delete(*self.project_tree.get_children())
        self._project_files = {}
        self.project_title.configure(text='Open a folder to work with multiple files.')
        self.schedule_session()
        self.set_status('Folder closed · Build compiles the current file')

    def refresh_project_tree(self):
        if not self.project:
            return
        self.project.files = self.project.discover()
        self.project_tree.delete(*self.project_tree.get_children())
        self._project_files = {}
        parents = {'.': ''}
        selected = {str(p) for p in self.project.sources}
        for rel in self.project.files:
            parent = ''
            for i, part in enumerate(rel.parts[:-1]):
                key = str(Path(*rel.parts[:i + 1]))
                if key not in parents:
                    parents[key] = self.project_tree.insert(parent, 'end', text=part, open=True)
                parent = parents[key]
            mark = '● ' if str(rel) in selected else '  '
            item = self.project_tree.insert(parent, 'end', text=mark + rel.name)
            self._project_files[item] = self.project.root / rel
        self.project_title.configure(text=f'{self.project.root.name}\n{len(selected)} build files · ● included')

    def open_project_file(self):
        for item in self.project_tree.selection():
            path = self._project_files.get(item)
            if path:
                self.open_path(str(path))

    def choose_project_sources(self):
        if not self.project or self.busy:
            self.set_status('Open a project folder first')
            return
        win = tk.Toplevel(self.root)
        win.title('Choose files to build together')
        win.geometry('580x430')
        win.transient(self.root)
        c = self.colors
        win.configure(bg=c['panel'])
        tk.Label(win, text='Select the source files for one program. Include only one main function.',
                 bg=c['panel'], fg=c['fg'], wraplength=540, padx=15, pady=15).pack(fill='x')
        box = tk.Listbox(win, selectmode='multiple', exportselection=False, bg=c['console'], fg=c['fg'],
                         selectbackground=c['accent_fill'], selectforeground='white')
        box.pack(fill='both', expand=True, padx=15)
        files = [p for p in self.project.discover() if p.suffix.lower() in ('.c', '.cpp', '.cc', '.cxx', '.c++')]
        for i, path in enumerate(files):
            box.insert('end', str(path))
            if path in self.project.sources:
                box.selection_set(i)
        def accept():
            try:
                self.project.set_sources([files[i] for i in box.curselection()])
                self.project.save()
            except (OSError, ValueError) as ex:
                messagebox.showerror('Project', str(ex), parent=win)
                return
            self.project_exe = None
            self.refresh_project_tree()
            win.destroy()
        row = tk.Frame(win, bg=c['panel'])
        row.pack(fill='x', padx=12, pady=10)
        self.button(row, 'Save selection', accept, 'primary')

    def build_feature_panels(self):
        c = self.colors
        self.debug_panel = tk.Frame(self.output_tabs, bg=c['panel'])
        self.output_tabs.add(self.debug_panel, text='  Debugger  ')
        bar = tk.Frame(self.debug_panel, bg=c['panel'])
        bar.pack(fill='x')
        self.debug_buttons = []
        for label, command in (('Step over · F6', 'next'), ('Step into · F7', 'step'), ('Continue', 'continue_')):
            button = self.button(bar, label, lambda cmd=command: self.debug_command(cmd))
            button.configure(state='disabled')
            self.debug_buttons.append(button)
        self.button(bar, 'Stop', self.stop, 'quiet')
        self.debug_location = tk.Label(bar, text='Start with F5 · click the gutter to set a breakpoint',
                                       bg=c['panel'], fg=c['muted'])
        self.debug_location.pack(side='left', padx=10)
        self.variables = ttk.Treeview(self.debug_panel, columns=('name', 'value'), show='headings',
                                     style='Examples.Treeview', height=4)
        self.variables.heading('name', text='Variable')
        self.variables.heading('value', text='Value')
        self.variables.column('name', width=180, stretch=False)
        self.variables.pack(fill='both', expand=True)
        self.practice_panel = tk.Frame(self.output_tabs, bg=c['panel'])
        self.output_tabs.add(self.practice_panel, text='  Practice results  ')
        self.practice_results = tk.Text(self.practice_panel, bg=c['console'], fg=c['fg'],
                                        font=self.console_font, wrap='word', height=6, state='disabled')
        self.practice_results.pack(fill='both', expand=True)

    def build_live_input(self, parent):
        c = self.colors
        live = tk.Frame(parent, bg=c['panel'])
        live.pack(fill='x', padx=8, pady=(0, 5))
        tk.Label(live, text='Live input', bg=c['panel'], fg=c['muted']).pack(side='left', padx=5)
        self.live_input = tk.Entry(live, bg=c['console'], fg=c['fg'], insertbackground=c['cursor'],
                                    font=self.console_font, relief='flat')
        self.live_input.pack(side='left', fill='x', expand=True, ipady=5)
        self.live_input.bind('<Return>', lambda e: (self.send_live_input(), 'break')[1])
        self.send_button = self.button(live, 'Send ↵', self.send_live_input)
        self.eof_button = self.button(live, 'End input', self.end_live_input, 'quiet')
        self.send_button.configure(state='disabled')
        self.eof_button.configure(state='disabled')
        tk.Label(live, text='Time limit', bg=c['panel'], fg=c['muted']).pack(side='left', padx=(12, 3))
        self.limit_var = tk.StringVar(value=str(self.run_limit))
        limits = ttk.Combobox(live, textvariable=self.limit_var, values=('10', '30', '120', '300'),
                              width=5, state='readonly')
        limits.pack(side='left', padx=4)
        limits.bind('<<ComboboxSelected>>', lambda e: self.save_settings())
        tk.Label(live, text='seconds', bg=c['panel'], fg=c['muted']).pack(side='left')

    def send_live_input(self):
        if self.live_process:
            value = self.live_input.get()
            if self.live_process.send(value + '\n'):
                self.out(value + '\n', 'info')
                self.live_input.delete(0, 'end')
            else:
                self.set_status('Program input is closed or its input queue is full')

    def end_live_input(self):
        if self.live_process:
            self.live_process.close_input()
            self.send_button.configure(state='disabled')
            self.eof_button.configure(state='disabled')
            self.set_status('End of input sent · waiting for the program to finish')

    def start_live_run(self, exe):
        from execution import InteractiveProcess
        self.set_busy(True)
        self.output_tabs.select(0)
        self.out('\n▶ Running ' + os.path.basename(exe) + '\n', 'head')
        self.set_status('Running · type below and press Enter to send input')
        self._live_started = time.perf_counter()
        try:
            self.live_process = InteractiveProcess([exe], cwd=str(self.project.root) if self.project else os.path.dirname(exe),
                env=self.tool_env(), timeout=int(self.limit_var.get()), output_limit=200000)
            self.live_process.start()
            data = self.stdin_box.get('1.0', 'end-1c')
            if data:
                self.live_process.send(data if data.endswith('\n') else data + '\n')
            self.send_button.configure(state='normal')
            self.eof_button.configure(state='normal')
            self.live_input.focus_set()
        except (OSError, ValueError) as ex:
            self.live_process = None
            self.set_busy(False)
            self.out(f'Could not run program: {ex}\n', 'err')

    def poll_features(self):
        if self.live_process:
            for _ in range(100):
                try:
                    kind, value = self.live_process.events.get_nowait()
                except queue.Empty:
                    break
                if kind in ('stdout', 'stderr'):
                    self.out(value.replace('\r\n', '\n'), 'prog' if kind == 'stdout' else 'err')
                elif kind == 'done':
                    self.live_process = None
                    self.send_button.configure(state='disabled')
                    self.eof_button.configure(state='disabled')
                    self.run_done('', '', value.returncode, value.reason, time.perf_counter() - self._live_started)
                    break
        if self.debugger:
            for _ in range(100):
                try:
                    kind, value = self.debugger.events.get_nowait()
                except queue.Empty:
                    break
                self.debug_event(kind, value)
                if not self.debugger:
                    break

    def toggle_breakpoint(self, ed=None, line=None):
        ed = ed or self.current()
        if not ed:
            return
        if self.debugger:
            self.set_status('Stop debugging before changing breakpoints')
            return
        line = line or int(ed.text.index('insert').split('.')[0])
        if line in ed.breakpoints:
            ed.breakpoints.remove(line)
        else:
            ed.breakpoints.add(line)
        ed.draw_gutter()
        self.schedule_session()
        self.set_status(f'Breakpoint {"set" if line in ed.breakpoints else "removed"} at line {line}')

    def start_debug(self):
        if self.busy:
            return
        if not self.find_tool('gdb'):
            messagebox.showerror('Debugger', 'GDB was not found. Use the full package with the bundled compiler.', parent=self.root)
            return
        self._debug_requested = True
        self.compile(then_run=True)
        if not self.busy:
            self._debug_requested = False

    def launch_debug(self, exe):
        from debugger import Debugger
        ed = self.current()
        self.debug_hashes = {str(e): e.content_hash() for e in self.editors()}
        points = []
        for editor in self.editors():
            path = editor.path or (self.source_for_build(editor) if editor is ed else None)
            if path:
                points.extend((path, line) for line in editor.breakpoints)
        try:
            self.debugger = Debugger(self.find_tool('gdb'), exe,
                                     cwd=str(self.project.root) if self.project else os.path.dirname(exe), env=self.tool_env())
            self.debug_source = self.source_for_build(ed) if ed and not ed.path else None
            self.debug_editor = ed
            self.debugger.start(points, input_text=self.stdin_box.get('1.0', 'end-1c') + '\n')
            self.set_busy(True)
            self.output_tabs.select(self.debug_panel)
            self.debug_location.configure(text='Starting debugger…')
            self.set_status('Debugging · input comes from the preloaded input box')
        except (OSError, RuntimeError, ValueError) as ex:
            if self.debugger:
                self.debugger.stop()
            self.debugger = None
            self.set_busy(False)
            self.out(f'Could not start debugger: {ex}\n', 'err')

    def debug_command(self, command):
        if self.debugger and self.debug_paused:
            if any(e.content_hash() != self.debug_hashes.get(str(e), e.content_hash()) for e in self.editors()):
                self.set_status('Source changed · stop and restart debugging', error=True)
                return
            self.debug_paused = False
            for button in self.debug_buttons:
                button.configure(state='disabled')
            getattr(self.debugger, command)()

    def debug_event(self, kind, value):
        if kind == 'output':
            self.out(str(value), 'prog')
        elif kind == 'error':
            self.out('Debugger: ' + str(value) + '\n', 'err')
            self.set_status('Debugger error · see Output', error=True)
        elif kind == 'running':
            self.debug_paused = False
            self.debug_location.configure(text='Running…')
            for button in self.debug_buttons:
                button.configure(state='disabled')
            for ed in self.editors():
                ed.text.tag_remove('debugline', '1.0', 'end')
        elif kind == 'stopped':
            self.debug_paused = True
            for button in self.debug_buttons:
                button.configure(state='normal')
            self.variables.delete(*self.variables.get_children())
            for variable in value.get('locals', []):
                self.variables.insert('', 'end', values=(variable.get('name'), variable.get('value', '?')))
            path, line = value.get('file'), value.get('line', 0)
            self.debug_location.configure(text=f'{os.path.basename(path or "")}:{line} · {value.get("reason", "Paused")}')
            ed = None
            if path and self.debug_source and os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(self.debug_source)):
                ed = self.debug_editor
            elif path and os.path.isfile(path):
                ed = self.open_path(path)
            if ed and line and ed.content_hash() == self.debug_hashes.get(str(ed), ed.content_hash()):
                self.goto(ed, line)
                ed.text.tag_configure('debugline', background=self.colors['sel'])
                ed.text.tag_add('debugline', f'{line}.0', f'{line}.end+1c')
            self.set_status('Paused · inspect variables, step, or continue')
        elif kind == 'done':
            self.debugger = None
            self.debug_paused = False
            self.set_busy(False)
            self.debug_location.configure(text='Debugging finished')
            for button in self.debug_buttons:
                button.configure(state='disabled')
            for ed in self.editors():
                ed.text.tag_remove('debugline', '1.0', 'end')
            self.set_status('Debugging finished')

    def show_practice(self):
        from learning import EXERCISES
        self.hide_welcome()
        c = self.colors
        win = tk.Toplevel(self.root)
        win.title('Practice · CodeLab Studio')
        win.geometry('820x570')
        win.transient(self.root)
        win.configure(bg=c['panel'])
        tk.Label(win, text='Learn by solving', font=(self.ui, 20, 'bold'), bg=c['panel'],
                 fg=c['fg']).pack(anchor='w', padx=20, pady=(18, 5))
        tk.Label(win, text='Choose a challenge, write your solution, then check it against the test cases.',
                 bg=c['panel'], fg=c['muted']).pack(anchor='w', padx=20, pady=(0, 15))
        body = tk.Frame(win, bg=c['panel'])
        body.pack(fill='both', expand=True, padx=20)
        listing = tk.Listbox(body, width=28, exportselection=False, bg=c['console'], fg=c['fg'],
                             selectbackground=c['accent_fill'], selectforeground='white', font=(self.ui, 10))
        listing.pack(side='left', fill='y', padx=(0, 15))
        detail = tk.Text(body, wrap='word', bg=c['bg'], fg=c['fg'], font=(self.ui, 11), padx=15, pady=12, state='disabled')
        detail.pack(fill='both', expand=True)
        for item in EXERCISES:
            mark = '✓ ' if self.practice_progress.get(item['id']) else '  '
            listing.insert('end', mark + item['title'] + (' · C++' if item['lang'] == 'cpp' else ' · C'))
        def selected():
            return EXERCISES[listing.curselection()[0]] if listing.curselection() else EXERCISES[0]
        def render(hint=False):
            item = selected()
            text = item['title'] + '\n\n' + item['prompt'] + '\n\nSample input:\n' + item['cases'][0]['input']
            text += '\nExpected output:\n' + item['cases'][0]['expected']
            if hint:
                text += '\n\nHint: ' + item['hint']
            detail.configure(state='normal')
            detail.delete('1.0', 'end')
            detail.insert('1.0', text)
            detail.configure(state='disabled')
        def start():
            item = selected()
            ed = self.new_file(item['lang'], item['starter'], item['filename'])
            ed.exercise_id = item['id']
            self.practice_id = item['id']
            self.set_status('Practice opened · use Check solution in the toolbar')
            self.schedule_session()
            win.destroy()
        listing.bind('<<ListboxSelect>>', lambda e: render())
        listing.selection_set(0)
        render()
        row = tk.Frame(win, bg=c['panel'])
        row.pack(fill='x', padx=17, pady=12)
        self.button(row, 'Start challenge', start, 'primary')
        self.button(row, 'Show hint', lambda: render(True))

    def check_practice(self):
        from learning import EXERCISES
        ed = self.current()
        if self.busy or not ed:
            return
        item = next((x for x in EXERCISES if x['id'] == getattr(ed, 'exercise_id', None)), None)
        if not item:
            self.show_practice()
            return
        if self.project:
            messagebox.showinfo('Practice', 'Close the project folder to check this single-file exercise.', parent=self.root)
            return
        self._practice_requested = item
        self.compile(then_run=True)
        if not self.busy:
            self._practice_requested = None

    def run_practice_cases(self, exe, item):
        from execution import run_process
        from learning import compare_output
        self.set_busy(True)
        self.output_tabs.select(self.practice_panel)
        self.set_status('Checking practice cases…')
        def work():
            reports = []
            passed = 0
            for i, case in enumerate(item['cases'], 1):
                if self.cancel_job.is_set():
                    break
                try:
                    result = run_process([exe], input_text=case['input'], cwd=os.path.dirname(exe),
                                         env=self.tool_env(), timeout=5, cancel=self.cancel_job, output_limit=20000)
                    ok = result.returncode == 0 and not result.reason and compare_output(result.stdout, case['expected'])
                    passed += int(ok)
                    reports.append(f'Case {i}: {"PASS" if ok else "FAIL"}\nInput:\n{case["input"]}\n'
                                   f'Expected:\n{case["expected"]}\nActual:\n{result.stdout}\n'
                                   + (f'{result.reason or result.stderr}\n' if not ok else ''))
                except OSError as ex:
                    reports.append(f'Case {i}: Could not run: {ex}\n')
                    break
            cancelled = self.cancel_job.is_set()
            text = f'{item["title"]} — {passed}/{len(item["cases"])} passed' + (' · cancelled' if cancelled else '') + '\n\n' + '\n'.join(reports)
            def done():
                self.set_busy(False)
                self.practice_results.configure(state='normal')
                self.practice_results.delete('1.0', 'end')
                self.practice_results.insert('1.0', text)
                self.practice_results.configure(state='disabled')
                if passed == len(item['cases']) and not cancelled:
                    self.practice_progress[item['id']] = True
                    self.save_settings()
                self.set_status(f'Practice: {passed}/{len(item["cases"])} cases passed')
            self.ui_queue.put(done)
        threading.Thread(target=work, daemon=True).start()

    def project_state(self):
        state = {}
        if self.project:
            for rel in self.project.discover():
                path = str(self.project.root / rel)
                state[path] = fingerprint(path)
            state['__sources__'] = tuple(str(p) for p in self.project.sources)
            for ed in self.editors():
                if ed.path and os.path.abspath(ed.path) in state:
                    state['editor:' + ed.path] = ed.content_hash()
        return state

    def compile_project(self, then_run=False):
        from execution import run_process
        if self.busy or not self.project:
            return
        root = self.project.root
        for ed in self.editors():
            if ed.path and Path(ed.path).is_relative_to(root) and ed.modified() and not self.save(ed):
                return
        output = str(root / '.codelab-build' / ('program.exe' if os.name == 'nt' else 'program'))
        try:
            steps = self.project.build_steps(self.gcc, self.gpp, output,
                extra_flags=('-B', self.manifest_dir) if self.manifest_dir else ())
            # Add unbuffered stdio constructor to the final link command.
            helper = self.console_helper()
            steps[-1].extend(['-x', 'c', helper, '-x', 'none'])
            if os.name == 'nt':
                steps[-1].append('-static')
            self.project.save()
        except (OSError, ValueError, RuntimeError) as ex:
            self.out(f'Project: {ex}\n', 'err')
            self._debug_requested = False
            self._practice_requested = None
            return
        snapshot = self.project_state()
        self.set_busy(True)
        self.clear_output()
        self.set_status('Building project…')
        self.out(f'Building {root.name} · {len(self.project.sources)} source files\n', 'head')
        def work():
            text = ''
            rc = 0
            started = time.perf_counter()
            for command in steps:
                try:
                    result = run_process(command, cwd=str(root), env=self.tool_env(), timeout=180,
                                         cancel=self.cancel_job, output_limit=200000)
                    text += result.stdout + result.stderr
                    rc = result.returncode
                    if result.reason:
                        text += '\nBuild stopped: ' + result.reason + '\n'
                        rc = -1
                    if rc:
                        break
                except OSError as ex:
                    text += str(ex)
                    rc = -1
                    break
            self.ui_queue.put(lambda: self.project_build_done(output, snapshot, rc, text, time.perf_counter() - started, then_run))
        threading.Thread(target=work, daemon=True).start()

    def project_build_done(self, exe, snapshot, rc, text, elapsed, then_run):
        cancelled = self.cancel_job.is_set()
        self.set_busy(False)
        self.out(text, 'info')
        self.project_exe = None
        self.project_snapshot = {}
        rx = re.compile(r'^(.*?):(\d+)(?::(\d+))?:\s*(fatal error|error|warning|note):\s*(.*)$')
        for line in text.splitlines():
            match = rx.match(line)
            if not match:
                continue
            path, lineno, col, kind, msg = match.groups()
            path = os.path.abspath(os.path.join(str(self.project.root), path))
            item = self.problems.insert('', 'end', values=(kind.title(), os.path.basename(path), lineno, msg), tags=(kind,))
            self.problem_locations[item] = (path, snapshot.get(path), int(lineno), int(col or 1))
        self.output_tabs.tab(self.problems, text=f'  Problems ({len(self.problems.get_children())})  ')
        if cancelled or rc != 0 or snapshot != self.project_state():
            reason = 'Build stopped' if cancelled else 'Build failed' if rc else 'Sources changed; build again'
            self.out('\n' + reason + '\n', 'err')
            self.set_status(reason, error=True)
            self._debug_requested = False
            self._practice_requested = None
            return
        self.project_exe, self.project_snapshot = exe, snapshot
        self.out(f'\nBuild succeeded in {elapsed:.2f} s\n', 'ok')
        self.set_status('Project build succeeded')
        if then_run:
            self.launch(exe)

    def console_helper(self):
        folder = Path(self.settings_path).parent / 'build-support'
        folder.mkdir(parents=True, exist_ok=True)
        helper = folder / 'codelab_stdio.c'
        if not helper.exists():
            helper.write_text('#include <stdio.h>\n'
                'static void __attribute__((constructor)) codelab_stdio(void) {\n'
                '    setvbuf(stdout, NULL, _IONBF, 0);\n'
                '    setvbuf(stderr, NULL, _IONBF, 0);\n}\n', encoding='utf-8')
        return str(helper)
