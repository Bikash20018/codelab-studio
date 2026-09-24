"""Local command navigation and bounded, cancellable source search (stdlib only)."""
from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
import threading
import tkinter as tk
from tkinter import ttk


def text_digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def filter_choices(rows, query):
    terms = query.casefold().split()
    matches = [row for row in rows if all(term in (row[0] + ' ' + row[1]).casefold()
                                         for term in terms)]
    return sorted(matches, key=lambda row: not row[0].casefold().startswith(query.casefold().strip()))


@dataclass
class SearchDocument:
    key: str
    label: str
    path: str = None
    text: str = None


@dataclass
class SearchHit:
    document: SearchDocument
    line: int
    column: int
    length: int
    preview: str
    digest: str


@dataclass
class SearchReport:
    hits: list = field(default_factory=list)
    scanned: int = 0
    skipped: int = 0
    truncated: bool = False
    cancelled: bool = False


def search_documents(documents, query, match_case=False, whole_word=False,
                     cancel=None, limit=1000, max_bytes=2_000_000):
    report = SearchReport()
    if not query:
        return report
    pattern = re.escape(query)
    if whole_word:
        pattern = r'(?<!\w)' + pattern + r'(?!\w)'
    regex = re.compile(pattern, 0 if match_case else re.IGNORECASE)
    for document in documents:
        if cancel and cancel.is_set():
            report.cancelled = True
            break
        try:
            content = document.text
            if content is None:
                with open(document.path, 'rb') as stream:
                    data = stream.read(max_bytes + 1)
                if len(data) > max_bytes:
                    report.skipped += 1
                    continue
                content = data.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
            if '\0' in content or len(content.encode('utf-8')) > max_bytes:
                report.skipped += 1
                continue
        except (OSError, UnicodeError):
            report.skipped += 1
            continue
        report.scanned += 1
        digest = text_digest(content)
        for number, line in enumerate(content.split('\n'), 1):
            if cancel and cancel.is_set():
                report.cancelled = True
                return report
            for match in regex.finditer(line):
                if cancel and cancel.is_set():
                    report.cancelled = True
                    return report
                if len(report.hits) >= limit:
                    report.truncated = True
                    return report
                # Keep the matching part visible, even in very long source lines.
                start = max(0, match.start() - 65)
                preview = ('…' if start else '') + line[start:start + 220].strip()
                report.hits.append(SearchHit(document, number, match.start() + 1,
                                             len(match.group()), preview, digest))
    return report


def setup_dialog(window, app, title, width, height):
    window.title(title)
    window.transient(app.root)
    window.configure(bg=app.colors['panel'])
    window.minsize(app.px(min(width, 560)), app.px(320))
    width = min(app.px(width), window.winfo_screenwidth() - 60)
    height = min(app.px(height), window.winfo_screenheight() - 100)
    x = max(0, app.root.winfo_rootx() + (app.root.winfo_width() - width) // 2)
    y = max(0, app.root.winfo_rooty() + 90)
    window.geometry(f'{width}x{height}+{x}+{y}')


def search_entry(parent, app, variable):
    c = app.colors
    return tk.Entry(parent, textvariable=variable, font=(app.ui, 13), bg=c['console'],
                    fg=c['fg'], insertbackground=c['cursor'], relief='flat',
                    highlightthickness=1, highlightbackground=c['border'],
                    highlightcolor=c['accent'], selectbackground=c['sel'])


class QuickPicker(tk.Toplevel):
    def __init__(self, app, files=False):
        super().__init__(app.root)
        self.app = app
        self.rows = app.file_choices() if files else app.command_choices()
        self.filtered = []
        c = app.colors
        setup_dialog(self, app, 'Quick open' if files else 'Command palette', 680, 430)
        tk.Label(self, text='Open a file' if files else 'What would you like to do?',
                 bg=c['panel'], fg=c['fg'], font=(app.ui, 16, 'bold'), anchor='w').pack(fill='x', padx=20, pady=(18, 10))
        self.query = tk.StringVar()
        self.entry = search_entry(self, app, self.query)
        self.entry.pack(fill='x', padx=20, ipady=10)
        body = tk.Frame(self, bg=c['panel'])
        self.table = ttk.Treeview(body, columns=('name', 'detail'), show='headings',
                                  style='Examples.Treeview', selectmode='browse')
        self.table.heading('name', text='File' if files else 'Command')
        self.table.heading('detail', text='Location' if files else 'Shortcut / category')
        self.table.column('name', width=280, minwidth=200)
        self.table.column('detail', width=270, minwidth=150)
        self.footer = tk.Label(self, bg=c['panel'], fg=c['muted'], anchor='w', font=(app.ui, 9))
        self.footer.pack(side='bottom', fill='x', padx=20, pady=12)
        body.pack(fill='both', expand=True, padx=20, pady=(12, 0))
        scrollbar = ttk.Scrollbar(body, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.table.pack(fill='both', expand=True)
        self.query.trace_add('write', lambda *_: self.refresh())
        self.entry.bind('<Down>', lambda e: self.move(1))
        self.entry.bind('<Up>', lambda e: self.move(-1))
        self.bind('<Return>', lambda e: self.accept())
        self.table.bind('<Double-1>', lambda e: self.accept())
        self.bind('<Escape>', lambda e: self.destroy())
        self.refresh()
        self.entry.focus_set()

    def refresh(self):
        self.filtered = filter_choices(self.rows, self.query.get())[:200]
        self.table.delete(*self.table.get_children())
        for i, row in enumerate(self.filtered):
            self.table.insert('', 'end', iid=str(i), values=row[:2])
        if self.filtered:
            self.table.selection_set('0')
        self.footer.configure(text=f'{len(self.filtered)} results  •  ↑ ↓ to choose  •  Enter to open  •  Esc to close'
                              if self.filtered else 'No matches. Try a file name or a different command.')

    def move(self, delta):
        if self.filtered:
            selected = self.table.selection()
            index = (int(selected[0]) + delta) % len(self.filtered) if selected else 0
            self.table.selection_set(str(index))
            self.table.see(str(index))
        return 'break'

    def accept(self):
        selected = self.table.selection()
        if selected:
            callback = self.filtered[int(selected[0])][2]
            self.destroy()
            callback()
        return 'break'


class WorkspaceSearch(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.cancel = threading.Event()
        self.generation = 0
        self.hits = []
        c = app.colors
        setup_dialog(self, app, 'Search workspace', 920, 560)
        tk.Label(self, text='Find across your code', bg=c['panel'], fg=c['fg'],
                 font=(app.ui, 18, 'bold'), anchor='w').pack(fill='x', padx=20, pady=(18, 4))
        scope = str(app.project.root) if app.project else 'Open programs'
        tk.Label(self, text=scope + '  •  Includes unsaved edits', bg=c['panel'], fg=c['muted'],
                 font=(app.ui, 9), anchor='w').pack(fill='x', padx=20, pady=(0, 14))
        row = tk.Frame(self, bg=c['panel'])
        row.pack(fill='x', padx=17)
        self.query = tk.StringVar()
        self.entry = search_entry(row, app, self.query)
        self.entry.pack(side='left', fill='x', expand=True, padx=3, ipady=8)
        app.button(row, 'Search', self.start, 'primary')
        app.button(row, 'Cancel', self.cancel.set, 'quiet')
        options = tk.Frame(self, bg=c['panel'])
        options.pack(fill='x', padx=20, pady=8)
        self.match_case = tk.BooleanVar()
        self.whole_word = tk.BooleanVar()
        for title, variable in (('Match case', self.match_case), ('Whole word', self.whole_word)):
            ttk.Checkbutton(options, text=title, variable=variable).pack(side='left', padx=(0, 18))
        self.status = tk.Label(self, text='Enter text and press Enter to search C/C++ sources and headers.',
                               bg=c['panel'], fg=c['muted'], anchor='w', font=(app.ui, 9))
        self.status.pack(fill='x', padx=20, pady=(0, 10))
        tk.Label(self, text='Double-click a match to open it. Search reads files only; it never changes your code.',
                 bg=c['panel'], fg=c['muted'], anchor='w', font=(app.ui, 9)).pack(side='bottom', fill='x', padx=20, pady=12)
        body = tk.Frame(self, bg=c['panel'])
        body.pack(fill='both', expand=True, padx=20)
        self.table = ttk.Treeview(body, columns=('file', 'line', 'code'), show='headings',
                                  style='Examples.Treeview', selectmode='browse')
        for name, title, width in (('file', 'File', 200), ('line', 'Line : column', 100), ('code', 'Matching code', 510)):
            self.table.heading(name, text=title)
            self.table.column(name, width=width, minwidth=70, stretch=name == 'code')
        scroll = ttk.Scrollbar(body, command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.table.pack(fill='both', expand=True)
        self.entry.bind('<Return>', lambda e: (self.start(), 'break')[1])
        self.table.bind('<Return>', lambda e: self.open_hit())
        self.table.bind('<Double-1>', lambda e: self.open_hit())
        self.bind('<Escape>', lambda e: self.destroy())
        ed = app.current()
        if ed and ed.text.tag_ranges('sel'):
            selected = ed.text.get('sel.first', 'sel.last')
            if '\n' not in selected:
                self.query.set(selected)
        self.entry.focus_set()

    def start(self):
        query = self.query.get()
        self.cancel.set()
        self.cancel = cancel = threading.Event()
        self.generation += 1
        generation = self.generation
        self.table.delete(*self.table.get_children())
        self.hits = []
        if not query:
            self.status.configure(text='Enter the text you want to find.')
            return
        documents = self.app.search_documents()
        match_case, whole_word = self.match_case.get(), self.whole_word.get()
        self.status.configure(text=f'Searching {len(documents)} files…')

        def worker():
            report = search_documents(documents, query, match_case, whole_word, cancel)
            self.app.ui_queue.put(lambda: self.finish(generation, report))
        threading.Thread(target=worker, daemon=True).start()

    def finish(self, generation, report):
        if not self.winfo_exists() or generation != self.generation:
            return
        self.hits = report.hits
        for i, hit in enumerate(self.hits):
            self.table.insert('', 'end', iid=str(i), values=(hit.document.label,
                              f'{hit.line} : {hit.column}', hit.preview))
        text = f'{len(report.hits)} matches in {report.scanned} files searched'
        if report.cancelled:
            text = 'Search cancelled. ' + text
        if report.truncated:
            text += ' • First 1,000 matches shown; narrow your search'
        if report.skipped:
            text += f' • {report.skipped} unreadable, binary or large files skipped (2 MB limit)'
        self.status.configure(text=text)

    def open_hit(self):
        selected = self.table.selection()
        if selected:
            if self.app.open_search_hit(self.hits[int(selected[0])]):
                self.destroy()
            else:
                self.status.configure(text='This file changed or closed. Search again to refresh its locations.')
        return 'break'

    def destroy(self):
        self.cancel.set()
        super().destroy()
