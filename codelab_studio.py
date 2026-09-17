#!/usr/bin/env python3
"""
CodeLab Studio - a clean, friendly C / C++ IDE for students.

Runtime : Python 3.9+ on Windows 10/11 (also runs on Linux for testing)
Deps    : standard library only (tkinter)
Compiler: bundled MinGW-w64 in ./mingw64/bin next to the app, or gcc/g++ on PATH
"""

import bisect
import hashlib
import os
import queue
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter import font as tkfont

from examples import EXAMPLES, by_category, categories

# ---- Branding --------------------------------------------------------------
APP_NAME = "CodeLab Studio"
APP_VERSION = "1.2.0"
SUBTITLE = "C / C++ for Students"
AUTHOR = "Bikash Chhetri"
WEBSITE = "www.bikashchhetri.com.np"
WEBSITE_URL = "https://www.bikashchhetri.com.np"

IS_WIN = os.name == "nt"
EXE_EXT = ".exe" if IS_WIN else ".out"
NO_WINDOW = 0x08000000 if IS_WIN else 0      # CREATE_NO_WINDOW
NEW_CONSOLE = 0x00000010 if IS_WIN else 0    # CREATE_NEW_CONSOLE
RUN_TIMEOUT = 10                              # seconds, for "run inside panel"
WORK_DIR = os.path.join(tempfile.gettempdir(), "CodeLabStudio")

C = {
    "bg": "#1b1d2a", "panel": "#232638", "header": "#161826", "gutter": "#171927",
    "console": "#141622", "btn": "#2e3250", "btn_hover": "#3b4066",
    "fg": "#e4e6f1", "muted": "#7c819e", "accent": "#7c5cff", "accent_hover": "#9178ff",
    "go": "#12b886", "go_hover": "#20c997", "status": "#5b3fd6",
    "cursor": "#35e0b0", "sel": "#3a3f66", "curline": "#22253a",
    "errline": "#4a1f2e", "warnline": "#3f3420", "find": "#ffd166",
    "danger": "#ff5c7a", "warn": "#ffb454", "ok": "#3ddc97", "note": "#82aaff",
    "func": "#ffcb6b", "num": "#f78c6c", "kw": "#c792ea", "type": "#82aaff",
    "pre": "#89ddff", "str": "#c3e88d", "com": "#676e95",
}

# ---- Syntax ---------------------------------------------------------------
C_KEYWORDS = ("auto break case const continue default do else enum extern for goto if "
              "inline register restrict return sizeof static struct switch typedef union "
              "volatile while")
CPP_KEYWORDS = ("alignas alignof and catch class constexpr const_cast decltype delete "
                "dynamic_cast explicit export false final friend mutable namespace new "
                "noexcept not nullptr operator or override private protected public "
                "reinterpret_cast static_assert static_cast template this throw true try "
                "typeid typename using virtual xor")
TYPES = ("int char float double void long short signed unsigned bool _Bool size_t FILE "
         "string vector map set pair queue stack list deque array wchar_t int8_t int16_t "
         "int32_t int64_t uint8_t uint16_t uint32_t uint64_t cin cout cerr endl std")


def words_rx(words):
    return re.compile(r"\b(?:%s)\b" % "|".join(words.split()))


RX_KW = {"c": words_rx(C_KEYWORDS), "cpp": words_rx(C_KEYWORDS + " " + CPP_KEYWORDS)}
RX_TYPE = words_rx(TYPES)
RX_FUNC = re.compile(r"\b[A-Za-z_]\w*(?=\s*\()")
RX_NUM = re.compile(r"\b(?:0[xX][0-9a-fA-F]+|\d+\.?\d*(?:[eE][+-]?\d+)?)[fFuUlL]*\b")
RX_PRE = re.compile(r"^[ \t]*#[^\n]*", re.M)
RX_STR_COM = re.compile(
    r"(?P<com>//[^\n]*|/\*[\s\S]*?(?:\*/|\Z))"
    r"|(?P<str>\"(?:\\.|[^\"\\\n])*\"?|'(?:\\.|[^'\\\n])*'?)")
RX_DIAG = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):(?:(?P<col>\d+):)?\s*"
    r"(?P<kind>fatal error|error|warning|note):\s*(?P<msg>.*)$")

HINTS = [
    (r"expected (?:'[,;]' or )?';'", "A semicolon ; is missing - usually at the end of the line BEFORE the one shown."),
    (r"was not declared|undeclared", "Check spelling and capital letters, and declare variables before using them. "
                                     "In C++, did you forget #include or 'using namespace std;'?"),
    (r"No such file or directory", "Check the #include name, e.g. <stdio.h> for C or <iostream> for C++."),
    (r"undefined reference to `?(WinMain|main)", "Every program needs an  int main()  function."),
    (r"Permission denied", "Your previous program window is still open. Close it, then build again."),
    (r"cannot find .*default-manifest\.o|ld\.exe: cannot find C:/Program",
     "The compiler folder has a space in its path, which MinGW cannot handle. "
     "Move CodeLab Studio to a folder without spaces, for example C:\\CodeLabStudio."),
    (r"expected '}' at end of input", "A closing brace } is missing. Count your { and } pairs."),
    (r"format '%\w+' expects", "printf/scanf format does not match the variable: %d int, %f float, "
                               "%lf double (scanf), %c char, %s string."),
    (r"iostream.*No such file|stdio.h.*C\+\+", "Is the language correct? Switch between C and C++ at the top right."),
]

# Words offered by the suggestion popup, on top of the keywords above and whatever
# the student has already typed in the file.
C_LIBRARY = ("printf scanf puts putchar getchar fgets fputs fopen fclose fprintf fscanf "
             "fgetc fputc feof rewind malloc calloc realloc free exit abort atoi atof "
             "strlen strcpy strncpy strcat strncat strcmp strncmp strchr strstr strtok "
             "strcspn memset memcpy sqrt pow fabs floor ceil round sin cos tan log log10 "
             "abs labs rand srand time clock isalpha isdigit isalnum isspace isupper "
             "islower toupper tolower stdio.h stdlib.h string.h math.h ctype.h time.h "
             "NULL EOF stdin stdout stderr")
CPP_LIBRARY = ("cout cin cerr endl getline string vector map unordered_map set multiset "
               "pair queue stack deque array list tuple sort reverse find count accumulate "
               "max_element min_element push_back pop_back emplace_back size empty begin "
               "end front back insert erase clear substr length to_string stoi stod stof "
               "make_pair make_tuple unique_ptr shared_ptr make_unique make_shared setw "
               "setprecision fixed iostream iomanip algorithm sstream fstream numeric "
               "istringstream ostringstream ifstream ofstream")

# Offered before anything else of the same prefix - what students reach for daily.
COMMON_WORDS = frozenset(
    "printf scanf include int main return float double char void long for while do if else "
    "switch case break continue struct typedef sizeof const static malloc free NULL "
    "stdio.h stdlib.h string.h math.h strlen strcpy strcmp fopen fclose fgets "
    "cout cin endl string vector getline class public private using namespace new delete "
    "iostream push_back size sort".split())

RX_WORD = re.compile(r"[A-Za-z_]\w{2,}")
RX_PREFIX = re.compile(r"[A-Za-z_]\w*$")

PLAIN_QUOTES = {0x2018: "'", 0x2019: "'"}   # GCC prints curly quotes in UTF-8 locales

WIN_CRASHES = {0xC0000005: "memory access violation (bad pointer or array index)",
               0xC0000094: "integer division by zero",
               0xC00000FD: "stack overflow (too deep recursion?)"}

TEMPLATES = {
    "c": '#include <stdio.h>\n\nint main(void)\n{\n    printf("Hello, World!\\n");\n    return 0;\n}\n',
    "cpp": '#include <iostream>\nusing namespace std;\n\nint main()\n{\n'
           '    cout << "Hello, World!" << endl;\n    return 0;\n}\n',
}

WELCOME = """/*
 *  Welcome to CodeLab Studio!
 *
 *    F9   Compile            F10     Run
 *    F11  Compile & Run      Ctrl+S  Save
 *    Ctrl+/ Comment line     Ctrl+G  Go to line
 *
 *  Choose C or C++ at the top right.
 *
 *  New here?  Press  Ctrl+E  to browse the ready-made
 *  programs - loops, patterns, arrays, pointers, files,
 *  classes, the STL, and a few games to play with.
 *
 *  Start typing and a word list appears - Enter accepts it.
 */
""" + TEMPLATES["c"]

SOURCE_TYPES = [("C / C++ source", "*.c *.cpp *.cc *.cxx *.h *.hpp"), ("All files", "*.*")]


# ---- Helpers --------------------------------------------------------------
def app_dir():
    return os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))


def resource(*parts):
    return os.path.join(getattr(sys, "_MEIPASS", app_dir()), *parts)


def find_tool(name):
    for sub in ("mingw64", "mingw32", "compiler"):
        path = os.path.join(app_dir(), sub, "bin", name + (".exe" if IS_WIN else ""))
        if os.path.isfile(path):
            return path
    return shutil.which(name)


def lang_from_path(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".cpp", ".cc", ".cxx", ".c++", ".hpp", ".hh"):
        return "cpp"
    if ext in (".c", ".h"):
        return "c"
    return None


def pick_font(root, names, fallback):
    families = set(tkfont.families(root))
    return next((n for n in names if n in families), fallback)


def as_text(data):
    if data is None:
        return ""
    return data.decode("utf-8", "replace") if isinstance(data, bytes) else data


def describe_exit(rc):
    if rc is None:
        return None
    if IS_WIN:
        code = rc & 0xFFFFFFFF
        if code in WIN_CRASHES:
            return f"crashed: {WIN_CRASHES[code]}"
    elif rc < 0:
        return f"crashed with signal {-rc}" + (" (segmentation fault)" if rc == -11 else
                                               " (arithmetic error)" if rc == -8 else "")
    return None


def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def draw_logo(canvas, size):
    """The app mark: a rounded accent tile with a  </>  cut into it."""
    pad = size * 0.045
    round_rect(canvas, pad, pad, size - pad, size - pad, size * 0.27, fill=C["accent"], outline="")
    mid, span, rise = size / 2, size * 0.17, size * 0.15
    stroke = max(2, round(size * 0.055))
    line = dict(fill="white", width=stroke, capstyle="round", joinstyle="round")
    canvas.create_line(mid - span * 0.55, mid - rise, mid - span * 1.35, mid,
                       mid - span * 0.55, mid + rise, **line)
    canvas.create_line(mid + span * 0.55, mid - rise, mid + span * 1.35, mid,
                       mid + span * 0.55, mid + rise, **line)
    canvas.create_line(mid + span * 0.30, mid - rise * 1.35,
                       mid - span * 0.30, mid + rise * 1.35, **line)


def syntax_tags(widget, italic_font=None):
    """Give any Text widget the code colours used by the editor."""
    for tag in ("func", "num", "kw", "type", "pre", "str"):
        widget.tag_configure(tag, foreground=C[tag])
    widget.tag_configure("com", foreground=C["com"], **({"font": italic_font} if italic_font else {}))


def paint_syntax(widget, code, lang):
    """Colour `code` inside a Text widget that already has syntax_tags()."""
    starts = [0] + [m.end() for m in re.finditer("\n", code)]

    def idx(offset):
        line = bisect.bisect_right(starts, offset) - 1
        return f"{line + 1}.{offset - starts[line]}"

    for tag in ("func", "num", "kw", "type", "pre", "str", "com"):
        widget.tag_remove(tag, "1.0", "end")
    for tag, rx in (("func", RX_FUNC), ("num", RX_NUM), ("kw", RX_KW[lang]),
                    ("type", RX_TYPE), ("pre", RX_PRE)):
        for m in rx.finditer(code):
            widget.tag_add(tag, idx(m.start()), idx(m.end()))
    for m in RX_STR_COM.finditer(code):
        widget.tag_add(m.lastgroup, idx(m.start()), idx(m.end()))


# ---- Word suggestions -----------------------------------------------------
class Completer:
    """Small popup that offers keywords, library names and words already in the file.

    Typing  p  offers printf, pow, public, ...  Enter or Tab puts the word in,
    Escape hides it, and it never steals a key it is not showing for.
    """

    LIMIT = 10

    def __init__(self, editor):
        self.editor = editor
        self.popup = None
        self.listbox = None
        self.prefix = ""
        self.hide_job = None

    # -- state
    def visible(self):
        return self.popup is not None

    def vocabulary(self):
        lang = self.editor.lang
        words = set((C_KEYWORDS + " " + TYPES + " " + C_LIBRARY).split())
        if lang == "cpp":
            words.update((CPP_KEYWORDS + " " + CPP_LIBRARY).split())
        words.update(RX_WORD.findall(self.editor.code()))
        return words

    def current_prefix(self):
        line = self.editor.text.get("insert linestart", "insert")
        found = RX_PREFIX.search(line)
        return found.group() if found else ""

    # -- showing
    def refresh(self):
        prefix = self.current_prefix()
        if not prefix:
            return self.hide()
        matches = sorted((w for w in self.vocabulary()
                          if w.lower().startswith(prefix.lower()) and w != prefix),
                         key=lambda w: (w not in COMMON_WORDS, len(w), w.lower()))[:self.LIMIT]
        if not matches:
            return self.hide()
        self.prefix = prefix
        self.show(matches)

    def show(self, matches):
        spot = self.editor.text.bbox("insert")
        if spot is None:
            return self.hide()
        if self.popup is None:
            self.build()
        self.listbox.delete(0, "end")
        for word in matches:
            self.listbox.insert("end", "  " + word)
        self.listbox.selection_set(0)
        self.listbox.configure(height=len(matches))

        x, y, _w, height = spot
        widest = max(len(w) for w in matches) + 4
        self.popup.geometry("%dx%d+%d+%d" % (
            self.editor.app.code_font.measure("n") * widest + 16,
            len(matches) * (self.editor.app.code_font.metrics("linespace") + 4) + 6,
            self.editor.text.winfo_rootx() + x,
            self.editor.text.winfo_rooty() + y + height + 2))
        self.popup.deiconify()
        self.popup.lift()

    def build(self):
        self.popup = tk.Toplevel(self.editor)
        self.popup.overrideredirect(True)
        self.popup.configure(bg=C["accent"])
        self.listbox = tk.Listbox(
            self.popup, bg=C["panel"], fg=C["fg"], selectbackground=C["accent"],
            selectforeground="white", font=self.editor.app.code_font, relief="flat", bd=0,
            highlightthickness=0, activestyle="none", exportselection=False)
        self.listbox.pack(fill="both", expand=True, padx=1, pady=1)
        self.listbox.bind("<ButtonRelease-1>", lambda e: self.editor.after(1, self.accept))

    def hide(self):
        self.cancel_hide()
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None
            self.listbox = None

    def cancel_hide(self):
        """Clicking the list moves focus off the editor; keep the popup alive for it."""
        if self.hide_job is not None:
            self.editor.after_cancel(self.hide_job)
            self.hide_job = None

    def hide_soon(self):
        if self.visible() and self.hide_job is None:
            self.hide_job = self.editor.after(150, self.hide)

    # -- keys
    def move(self, delta):
        if not self.visible():
            return None
        size = self.listbox.size()
        current = (self.listbox.curselection() or (0,))[0]
        nxt = (current + delta) % size
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(nxt)
        self.listbox.see(nxt)
        return "break"

    def accept(self):
        self.cancel_hide()
        if not self.visible():
            return None
        picked = (self.listbox.curselection() or (0,))[0]
        word = self.listbox.get(picked).strip()
        self.hide()
        text = self.editor.text
        text.delete(f"insert-{len(self.prefix)}c", "insert")
        text.insert("insert", word)
        self.editor.schedule_highlight()
        return "break"


# ---- Editor tab -----------------------------------------------------------
class Editor(tk.Frame):
    PAIRS = {"(": ")", "[": "]", "{": "}"}
    _uid = 0

    def __init__(self, master, app, path=None, content="", lang="c", name=None):
        super().__init__(master, bg=C["bg"])
        Editor._uid += 1
        self.uid = Editor._uid
        self.app, self.path, self.lang = app, path, lang
        self.untitled_name = name
        self.is_welcome = False
        self.built_hash = self.built_exe = None
        self.diag = {}
        self.squiggles = []
        self._hl_job = None
        self._last_code = None

        self.gutter = tk.Canvas(self, width=52, bg=C["gutter"], highlightthickness=0, bd=0)
        self.text = t = tk.Text(
            self, wrap="none", undo=True, autoseparators=True, maxundo=-1,
            bg=C["bg"], fg=C["fg"], insertbackground=C["cursor"], insertwidth=2,
            selectbackground=C["sel"], selectforeground=C["fg"], inactiveselectbackground=C["sel"],
            relief="flat", bd=0, highlightthickness=0, padx=12, pady=8, font=app.code_font)
        vbar = ttk.Scrollbar(self, orient="vertical", command=t.yview)
        hbar = ttk.Scrollbar(self, orient="horizontal", command=t.xview)
        t.configure(yscrollcommand=lambda a, b: (vbar.set(a, b), self.draw_gutter()),
                    xscrollcommand=hbar.set)
        self.gutter.grid(row=0, column=0, sticky="ns")
        t.grid(row=0, column=1, sticky="nsew")
        vbar.grid(row=0, column=2, sticky="ns")
        hbar.grid(row=1, column=1, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.configure_tags()
        t.insert("1.0", content)
        t.edit_reset()
        t.edit_modified(False)
        t.mark_set("insert", "1.0")

        self.completer = Completer(self)
        t.bind("<<Modified>>", self.on_modified)
        t.bind("<KeyPress>", self.on_keypress)
        t.bind("<KeyRelease>", self.on_key_release)
        t.bind("<ButtonRelease-1>", lambda e: (self.completer.hide(), self.on_cursor_move()))
        t.bind("<FocusOut>", lambda e: self.completer.hide_soon())
        t.bind("<Down>", lambda e: self.completer.move(1))
        t.bind("<Up>", lambda e: self.completer.move(-1))
        t.bind("<Escape>", self.on_escape)
        t.bind("<Control-space>", lambda e: (self.completer.refresh(), "break")[1])
        t.bind("<Return>", self.on_return)
        t.bind("<Tab>", self.on_tab)
        t.bind("<Shift-Tab>", self.on_shift_tab)
        if not IS_WIN:
            t.bind("<ISO_Left_Tab>", self.on_shift_tab)
        t.bind("<Configure>", lambda e: self.draw_gutter())
        t.bind("<Control-MouseWheel>", lambda e: (app.zoom(1 if e.delta > 0 else -1), "break")[1])
        app.bind_shortcuts(t)
        self.highlight()
        self.mark_current_line()

    # -- state
    def display_name(self):
        return os.path.basename(self.path) if self.path else self.untitled_name

    def modified(self):
        return bool(self.text.edit_modified())

    def code(self):
        return self.text.get("1.0", "end-1c")

    def content_hash(self):
        return hashlib.sha1((self.lang + "\0" + self.code()).encode("utf-8")).hexdigest()

    def set_lang(self, lang):
        self.lang = lang
        self._last_code = None
        self.highlight()

    # -- visuals
    def configure_tags(self):
        t = self.text
        t.tag_configure("curline", background=C["curline"])
        t.tag_configure("warnline", background=C["warnline"])
        t.tag_configure("errline", background=C["errline"])
        syntax_tags(t, self.app.code_font_italic)
        t.tag_configure("find", background=C["find"], foreground="#111111")
        t.tag_raise("sel")
        self.update_tabs()

    def update_tabs(self):
        self.text.configure(tabs=(self.app.code_font.measure("    "),))

    def schedule_highlight(self):
        if self._hl_job:
            self.after_cancel(self._hl_job)
        self._hl_job = self.after(120, self.highlight)

    def highlight(self):
        self._hl_job = None
        code = self.code()
        if code == self._last_code:
            return
        self._last_code = code
        paint_syntax(self.text, code, self.lang)

    def mark_current_line(self):
        t = self.text
        t.tag_remove("curline", "1.0", "end")
        t.tag_add("curline", "insert linestart", "insert lineend+1c")

    def draw_gutter(self):
        g, t = self.gutter, self.text
        g.delete("all")
        total = int(t.index("end-1c").split(".")[0])
        width = self.app.code_font.measure(str(max(total, 99))) + 30
        if int(g.cget("width")) != width:
            g.configure(width=width)
        cur = int(t.index("insert").split(".")[0])
        first = int(t.index("@0,0").split(".")[0])
        for n in range(first, total + 1):
            info = t.dlineinfo(f"{n}.0")
            if info is None:
                break
            y, h = info[1], info[3]
            g.create_text(width - 12, y, anchor="ne", text=str(n), font=self.app.code_font,
                          fill=C["fg"] if n == cur else C["muted"])
            found = self.diag.get(n)
            if found:
                g.create_oval(6, y + h / 2 - 4, 14, y + h / 2 + 4, outline="",
                              fill=C["danger"] if found[0] == "error" else C["warn"])
        self.draw_squiggles()

    def set_diagnostics(self, diag):
        self.diag = diag
        t = self.text
        t.tag_remove("errline", "1.0", "end")
        t.tag_remove("warnline", "1.0", "end")
        for line, (kind, _col) in diag.items():
            t.tag_add("errline" if kind == "error" else "warnline", f"{line}.0", f"{line}.0 lineend+1c")
        self.draw_gutter()

    def draw_squiggles(self):
        """Red (or amber) wavy underline under the reported column, like VS Code.

        A Text widget cannot draw wavy underlines, so each one is a 3-pixel-tall
        canvas placed over the descender strip of that line.
        """
        for strip in self.squiggles:
            strip.destroy()
        self.squiggles.clear()
        if not self.diag:
            return

        t = self.text
        for line, (kind, col) in self.diag.items():
            start = t.bbox(f"{line}.{max(col - 1, 0)}")
            if start is None:                       # line is scrolled out of view
                continue
            last = t.bbox(f"{line}.end-1c") or start
            x, y, _w, height = start
            width = max(last[0] + last[2] - x, self.app.code_font.measure("nn"))

            strip = tk.Canvas(t, width=width, height=3, highlightthickness=0, bd=0,
                              bg=C["errline"] if kind == "error" else C["warnline"])
            points = []
            for step, px in enumerate(range(0, int(width) + 2, 2)):
                points.extend((px, 0 if step % 2 else 2))
            if len(points) >= 4:
                strip.create_line(*points, fill=C["danger"] if kind == "error" else C["warn"])
            strip.place(x=x, y=y + height - 3)
            self.squiggles.append(strip)

    # -- events
    def on_modified(self, _event=None):
        self.app.refresh_tab(self)
        self.schedule_highlight()

    def on_cursor_move(self, _event=None):
        self.mark_current_line()
        self.draw_gutter()
        self.app.update_status()
        self.schedule_highlight()

    def on_escape(self, _event):
        if self.completer.visible():
            self.completer.hide()
            return "break"
        return None

    SILENT_KEYS = ("Up", "Down", "Left", "Right", "Home", "End", "Prior", "Next",
                   "Escape", "Return", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R")

    def on_key_release(self, event):
        self.on_cursor_move()
        if event.state & 0x4 or event.keysym in self.SILENT_KEYS:
            return
        if event.keysym == "BackSpace" and not self.completer.visible():
            return
        if event.char and not (event.char.isalnum() or event.char == "_") \
                and event.keysym != "BackSpace":
            self.completer.hide()
            return
        self.completer.refresh()

    def on_keypress(self, event):
        t, ch = self.text, event.char
        if event.state & 0x4 or not ch:     # Control held / non-printing
            return None
        if ch in self.PAIRS and not t.tag_ranges("sel") and t.get("insert") in ("", "\n", " ", ")", "]", "}", ";", ","):
            t.insert("insert", ch + self.PAIRS[ch])
            t.mark_set("insert", "insert-1c")
            return "break"
        if ch in (")", "]", "}") and t.get("insert") == ch:
            t.mark_set("insert", "insert+1c")
            return "break"
        if ch == "}":
            before = t.get("insert linestart", "insert")
            if before.strip() == "" and before.endswith("    "):
                t.delete("insert-4c", "insert")
        return None

    def on_return(self, _event):
        if self.completer.visible():
            return self.completer.accept()
        t = self.text
        t.edit_separator()
        line = t.get("insert linestart", "insert")
        indent = re.match(r"[ \t]*", line).group()
        if line.rstrip().endswith("{"):
            if t.get("insert") == "}":
                t.insert("insert", "\n" + indent + "    \n" + indent)
                t.mark_set("insert", "insert -1 lines lineend")
            else:
                t.insert("insert", "\n" + indent + "    ")
        else:
            t.insert("insert", "\n" + indent)
        t.see("insert")
        self.on_cursor_move()
        return "break"

    def selected_lines(self):
        t = self.text
        if not t.tag_ranges("sel"):
            n = int(t.index("insert").split(".")[0])
            return n, n
        first = int(t.index("sel.first").split(".")[0])
        last_idx = t.index("sel.last")
        last = int(last_idx.split(".")[0])
        if last_idx.endswith(".0") and last > first:
            last -= 1
        return first, last

    def on_tab(self, _event):
        if self.completer.visible():
            return self.completer.accept()
        t = self.text
        if t.tag_ranges("sel"):
            first, last = self.selected_lines()
            for n in range(first, last + 1):
                t.insert(f"{n}.0", "    ")
        else:
            t.insert("insert", "    ")
        self.schedule_highlight()
        return "break"

    def on_shift_tab(self, _event):
        t = self.text
        first, last = self.selected_lines()
        for n in range(first, last + 1):
            head = t.get(f"{n}.0", f"{n}.4")
            spaces = len(head) - len(head.lstrip(" "))
            if spaces:
                t.delete(f"{n}.0", f"{n}.{spaces}")
        self.schedule_highlight()
        return "break"

    def toggle_comment(self):
        t = self.text
        first, last = self.selected_lines()
        lines = [t.get(f"{n}.0", f"{n}.end") for n in range(first, last + 1)]
        code_lines = [l for l in lines if l.strip()]
        uncomment = bool(code_lines) and all(l.lstrip().startswith("//") for l in code_lines)
        t.edit_separator()
        for n, line in zip(range(first, last + 1), lines):
            if not line.strip():
                continue
            pos = len(line) - len(line.lstrip())
            if uncomment:
                width = 3 if line[pos:pos + 3] == "// " else 2
                t.delete(f"{n}.{pos}", f"{n}.{pos + width}")
            else:
                t.insert(f"{n}.{pos}", "// ")
        t.edit_separator()
        self.schedule_highlight()


# ---- Examples browser -----------------------------------------------------
class ExamplesDialog(tk.Toplevel):
    """Searchable gallery of the ready-made programs, with a live preview."""

    ALL = "All programs"

    def __init__(self, app):
        super().__init__(app.root, bg=C["bg"])
        self.app = app
        self.shown = []
        self.title("Example Programs")
        self.transient(app.root)
        self.minsize(880, 540)
        self.configure(padx=0, pady=0)

        self.build_header()
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.build_categories(body)
        self.build_list(body)
        self.build_preview(body)
        self.build_footer()

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self.open_selected())
        self.refresh()
        self.center_on_parent(1060, 660)
        self.search.focus_set()
        self.grab_set()

    # -- layout
    def build_header(self):
        head = tk.Frame(self, bg=C["header"])
        head.pack(fill="x")
        box = tk.Frame(head, bg=C["header"])
        box.pack(side="left", padx=18, pady=14)
        tk.Label(box, text="Example Programs", bg=C["header"], fg=C["fg"],
                 font=(self.app.ui, 15, "bold")).pack(anchor="w")
        tk.Label(box, text=f"{len(EXAMPLES)} ready-made programs  ·  pick one, read it, change it",
                 bg=C["header"], fg=C["muted"], font=(self.app.ui, 9)).pack(anchor="w")

        wrap = tk.Frame(head, bg=C["console"])
        wrap.pack(side="right", padx=18)
        tk.Label(wrap, text="\U0001F50D", bg=C["console"], fg=C["muted"],
                 font=(self.app.ui, 10)).pack(side="left", padx=(10, 0))
        self.query = tk.StringVar()
        self.query.trace_add("write", lambda *_: self.refresh())
        self.search = tk.Entry(wrap, textvariable=self.query, width=26, bd=0, relief="flat",
                               bg=C["console"], fg=C["fg"], insertbackground=C["cursor"],
                               font=(self.app.ui, 11), highlightthickness=0)
        self.search.pack(side="left", padx=8, ipady=7)
        self.search.bind("<Down>", lambda e: (self.tree.focus_set(), self.select_row(0), "break")[2])

    def build_categories(self, parent):
        col = tk.Frame(parent, bg=C["bg"])
        col.pack(side="left", fill="y", pady=12)
        tk.Label(col, text="TOPICS", bg=C["bg"], fg=C["muted"],
                 font=(self.app.ui, 8, "bold")).pack(anchor="w", pady=(0, 6))

        self.category = self.ALL
        self.cat_labels = {}
        names = [self.ALL] + categories()
        for name in names:
            count = len(EXAMPLES) if name == self.ALL else len(by_category(name))
            row = tk.Label(col, text=f"  {name}   ({count})", anchor="w", width=24,
                           bg=C["bg"], fg=C["muted"], font=(self.app.ui, 10),
                           padx=6, pady=6, cursor="hand2")
            row.pack(fill="x", pady=1)
            row.bind("<Button-1>", lambda e, n=name: self.pick_category(n))
            row.bind("<Enter>", lambda e, n=name: self.hover_category(n, True))
            row.bind("<Leave>", lambda e, n=name: self.hover_category(n, False))
            self.cat_labels[name] = row
        self.paint_categories()

    def build_list(self, parent):
        col = tk.Frame(parent, bg=C["bg"])
        col.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        self.count_label = tk.Label(col, text="", bg=C["bg"], fg=C["muted"],
                                    font=(self.app.ui, 8, "bold"), anchor="w")
        self.count_label.pack(fill="x", pady=(0, 6))

        holder = tk.Frame(col, bg=C["console"])
        holder.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(holder, columns=("lang",), show="tree headings",
                                 style="Examples.Treeview", selectmode="browse")
        self.tree.heading("#0", text="  Program", anchor="w")
        self.tree.heading("lang", text="Language", anchor="w")
        self.tree.column("#0", width=250, stretch=True)
        self.tree.column("lang", width=90, stretch=False, anchor="w")
        bar = ttk.Scrollbar(holder, command=self.tree.yview)
        self.tree.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_preview())
        self.tree.bind("<Double-Button-1>", lambda e: self.open_selected())

    def build_preview(self, parent):
        col = tk.Frame(parent, bg=C["bg"], width=460)
        col.pack(side="left", fill="both", expand=True, pady=12)
        col.pack_propagate(False)

        bar = tk.Frame(col, bg=C["bg"])
        bar.pack(fill="x", pady=(0, 6))
        self.file_label = tk.Label(bar, text="", bg=C["bg"], fg=C["muted"],
                                   font=(self.app.ui, 8, "bold"), anchor="w")
        self.file_label.pack(side="left")
        self.badge = tk.Label(bar, text="", bg=C["accent"], fg="white", padx=8, pady=1,
                              font=(self.app.ui, 8, "bold"))
        self.badge.pack(side="right")

        holder = tk.Frame(col, bg=C["console"])
        holder.pack(fill="both", expand=True)
        self.preview = tk.Text(holder, bg=C["console"], fg=C["fg"], font=self.app.console_font,
                               relief="flat", bd=0, padx=12, pady=10, wrap="none",
                               highlightthickness=0, insertbackground=C["console"], cursor="arrow")
        vbar = ttk.Scrollbar(holder, command=self.preview.yview)
        hbar = ttk.Scrollbar(holder, orient="horizontal", command=self.preview.xview)
        self.preview.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        hbar.pack(side="bottom", fill="x")
        vbar.pack(side="right", fill="y")
        self.preview.pack(side="left", fill="both", expand=True)
        syntax_tags(self.preview)
        # read-only, but Ctrl+C and Ctrl+A still work
        self.preview.bind("<Key>", lambda e: None if (e.state & 0x4 and e.keysym.lower() in ("c", "a")) else "break")

    def build_footer(self):
        foot = tk.Frame(self, bg=C["panel"])
        foot.pack(fill="x", side="bottom")
        tk.Label(foot, text="Double-click a program, or press Enter, to open it in a new tab.",
                 bg=C["panel"], fg=C["muted"], font=(self.app.ui, 9)).pack(side="left", padx=18, pady=10)
        self.app.button(foot, "Close", self.destroy, side="right")
        self.app.button(foot, "Open in editor", self.open_selected, "primary", side="right")

    def center_on_parent(self, width, height):
        self.update_idletasks()
        parent = self.app.root
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 3
        self.geometry("%dx%d+%d+%d" % (width, height, max(x, 0), max(y, 0)))

    # -- behaviour
    def hover_category(self, name, entering):
        if name != self.category:
            self.cat_labels[name].configure(bg=C["panel"] if entering else C["bg"])

    def paint_categories(self):
        for name, label in self.cat_labels.items():
            chosen = name == self.category
            label.configure(bg=C["accent"] if chosen else C["bg"],
                            fg="white" if chosen else C["muted"],
                            font=(self.app.ui, 10, "bold" if chosen else "normal"))

    def pick_category(self, name):
        self.category = name
        self.paint_categories()
        self.refresh()

    def matches(self, entry, needle):
        category, title, lang, fname, code = entry
        if self.category != self.ALL and category != self.category:
            return False
        if not needle:
            return True
        language = "c++" if lang == "cpp" else "c"
        return needle in " ".join((title, category, fname, language, code)).lower()

    def refresh(self):
        needle = self.query.get().strip().lower()
        self.shown = [e for e in EXAMPLES if self.matches(e, needle)]

        self.tree.delete(*self.tree.get_children())
        for i, (category, title, lang, _fname, _code) in enumerate(self.shown):
            label = title if self.category != self.ALL else f"{title}"
            self.tree.insert("", "end", iid=str(i), text="  " + label,
                             values=("C++  ·  C++17" if lang == "cpp" else "C  ·  C11",))

        found = len(self.shown)
        where = "" if self.category == self.ALL else f" in {self.category}"
        self.count_label.configure(text=f"{found} PROGRAM{'' if found == 1 else 'S'}{where.upper()}")
        if self.shown:
            self.select_row(0)
        else:
            self.show_code(None)

    def select_row(self, index):
        if 0 <= index < len(self.shown):
            iid = str(index)
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.tree.see(iid)

    def selected(self):
        picked = self.tree.selection()
        return self.shown[int(picked[0])] if picked else None

    def show_preview(self):
        self.show_code(self.selected())

    def show_code(self, entry):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        if entry is None:
            self.file_label.configure(text="")
            self.badge.configure(text="", bg=C["bg"])
            self.preview.insert("1.0", "\n  No program matches that search.\n"
                                       "  Try a shorter word, or pick another topic.")
            return
        category, title, lang, fname, code = entry
        self.file_label.configure(text=fname.upper())
        self.badge.configure(text="C++" if lang == "cpp" else "C",
                             bg=C["accent"] if lang == "cpp" else C["go"])
        self.preview.insert("1.0", code)
        paint_syntax(self.preview, code, lang)

    def open_selected(self):
        entry = self.selected()
        if entry is None:
            return
        _category, _title, lang, fname, code = entry
        self.destroy()
        self.app.new_file(lang, code, fname)


# ---- Application ----------------------------------------------------------
class App:
    def __init__(self, root, files=()):
        self.root = root
        self.gcc, self.gpp = find_tool("gcc"), find_tool("g++")
        self.busy = False
        self.closing_tab = None         # index of the tab whose x is being pressed
        self.manifest_dir = None        # set by detect_compiler when the path has spaces
        self.default_lang = "c"
        self.untitled_counter = 0
        self.font_size = 12
        self.last_find = ""
        self.link_tags = []
        self.run_in_panel = tk.BooleanVar(value=False)
        self.ui_queue = queue.Queue()   # worker threads never touch Tk directly

        mono = pick_font(root, ["Cascadia Code", "Consolas", "JetBrains Mono", "DejaVu Sans Mono", "Menlo"], "Courier")
        self.ui = pick_font(root, ["Segoe UI", "Inter", "Ubuntu", "DejaVu Sans", "Helvetica Neue"], "Helvetica")
        self.code_font = tkfont.Font(root, family=mono, size=self.font_size)
        self.code_font_italic = tkfont.Font(root, family=mono, size=self.font_size, slant="italic")
        self.console_font = tkfont.Font(root, family=mono, size=10)

        self.shortcuts = {
            "<Control-n>": lambda: self.new_file(self.default_lang),
            "<Control-o>": self.open_file,
            "<Control-s>": self.save,
            "<Control-S>": self.save_as,
            "<Control-w>": self.close_tab,
            "<Control-f>": self.find,
            "<Control-e>": lambda: self.show_examples(),
            "<F3>": self.find_next,
            "<Control-g>": self.goto_line,
            "<Control-slash>": lambda: self.current() and self.current().toggle_comment(),
            "<F9>": self.compile,
            "<F10>": self.run,
            "<F11>": self.compile_and_run,
            "<Control-equal>": lambda: self.zoom(1),
            "<Control-plus>": lambda: self.zoom(1),
            "<Control-minus>": lambda: self.zoom(-1),
        }

        self.build_window()
        for f in files:
            self.open_path(f)
        if not self.editors():
            self.new_file("c", WELCOME, "welcome.c").is_welcome = True
        self.out(f"{APP_NAME} {APP_VERSION} ready.  Press F11 to compile & run.\n", "info")
        threading.Thread(target=self.detect_compiler, daemon=True).start()
        root.protocol("WM_DELETE_WINDOW", self.quit)
        self.poll_queue()

    def poll_queue(self):
        while True:
            try:
                self.ui_queue.get_nowait()()
            except queue.Empty:
                break
        self.root.after(40, self.poll_queue)

    # -- layout
    def build_window(self):
        r = self.root
        r.title(APP_NAME)
        r.geometry("1240x800")
        r.minsize(900, 560)
        r.configure(bg=C["bg"])
        self.set_icon()
        self.style_ttk()
        self.build_menu()
        self.build_header()
        self.build_toolbar()
        self.build_statusbar()

        paned = tk.PanedWindow(r, orient="vertical", bg=C["header"], sashwidth=5, bd=0, sashrelief="flat")
        paned.pack(fill="both", expand=True)
        self.nb = ttk.Notebook(paned, style="Closable.TNotebook")
        paned.add(self.nb, stretch="always", minsize=220)
        paned.add(self.build_output(paned), stretch="never", minsize=120, height=240)
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.on_tab_changed())
        self.nb.bind("<Button-2>", self.on_tab_middle_click)
        self.nb.bind("<ButtonPress-1>", self.on_tab_press, True)
        self.nb.bind("<ButtonRelease-1>", self.on_tab_release)
        for seq, fn in self.shortcuts.items():
            r.bind(seq, lambda e, f=fn: (f(), "break")[1])

    def set_icon(self):
        try:
            if IS_WIN and os.path.isfile(resource("assets", "app.ico")):
                self.root.iconbitmap(default=resource("assets", "app.ico"))
            elif os.path.isfile(resource("assets", "app.png")):
                self._icon = tk.PhotoImage(file=resource("assets", "app.png"))
                self.root.iconphoto(True, self._icon)
        except tk.TclError:
            pass   # icon is cosmetic

    def style_ttk(self):
        st = ttk.Style(self.root)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        self.make_closable_notebook(st)
        st.configure("Closable.TNotebook", background=C["panel"], borderwidth=0, tabmargins=(8, 6, 8, 0))
        st.configure("Closable.TNotebook.Tab", background=C["panel"], foreground=C["muted"],
                     padding=(14, 7, 6, 7), borderwidth=0, font=(self.ui, 10),
                     bordercolor=C["panel"], lightcolor=C["accent"])
        st.map("Closable.TNotebook.Tab", background=[("selected", C["bg"])],
               foreground=[("selected", C["fg"])])
        st.configure("TScrollbar", troughcolor=C["bg"], background=C["btn"], borderwidth=0,
                     bordercolor=C["bg"], gripcount=0)
        st.map("TScrollbar", background=[("active", C["btn_hover"])])
        st.configure("TCheckbutton", background=C["panel"], foreground=C["muted"], font=(self.ui, 9),
                     indicatorbackground=C["console"], indicatorforeground=C["cursor"])
        st.configure("Examples.Treeview", background=C["console"], fieldbackground=C["console"],
                     foreground=C["fg"], borderwidth=0, relief="flat", rowheight=27,
                     bordercolor=C["console"], lightcolor=C["console"], darkcolor=C["console"],
                     font=(self.ui, 10))
        st.map("Examples.Treeview", background=[("selected", C["accent"])],
               foreground=[("selected", "white")])
        st.configure("Examples.Treeview.Heading", background=C["panel"], foreground=C["muted"],
                     borderwidth=0, relief="flat", font=(self.ui, 8, "bold"), padding=(6, 6))
        st.map("Examples.Treeview.Heading", background=[("active", C["panel"])])

    def make_closable_notebook(self, st):
        """Add an  x  to every notebook tab.  ttk has no such option, so the tab layout
        is rebuilt with one extra image element that clicks are matched against."""
        def cross(color):
            img = tk.PhotoImage(master=self.root, width=14, height=14)
            for i in range(4, 10):
                for thick in (0, 1):
                    img.put(color, (i + thick, i))
                    img.put(color, (13 - i + thick, i))
            return img

        self.tab_icons = (cross(C["muted"]), cross("#ffffff"), cross(C["danger"]))
        try:
            st.element_create("close", "image", self.tab_icons[0],
                              ("active", self.tab_icons[1]), ("pressed", self.tab_icons[2]),
                              border=6, sticky="")
        except tk.TclError:
            return                      # element already exists (a second window)
        st.layout("Closable.TNotebook", [("Closable.TNotebook.client", {"sticky": "nswe"})])
        st.layout("Closable.TNotebook.Tab", [
            ("Closable.TNotebook.tab", {"sticky": "nswe", "children": [
                ("Closable.TNotebook.padding", {"side": "top", "sticky": "nswe", "children": [
                    ("Closable.TNotebook.focus", {"side": "top", "sticky": "nswe", "children": [
                        ("Closable.TNotebook.label", {"side": "left", "sticky": ""}),
                        ("Closable.TNotebook.close", {"side": "left", "sticky": ""}),
                    ]})]})]})])

    def on_tab_press(self, event):
        if "close" in self.nb.identify(event.x, event.y):
            self.closing_tab = self.nb.index(f"@{event.x},{event.y}")
            self.nb.state(["pressed"])
            return "break"
        return None

    def on_tab_release(self, event):
        if self.closing_tab is None:
            return
        self.nb.state(["!pressed"])
        try:
            index = self.nb.index(f"@{event.x},{event.y}")
        except tk.TclError:
            index = None
        if index == self.closing_tab and "close" in self.nb.identify(event.x, event.y):
            self.close_tab(self.root.nametowidget(self.nb.tabs()[index]))
        self.closing_tab = None

    def build_menu(self):
        m = tk.Menu(self.root)
        acc = {"tearoff": 0}

        f = tk.Menu(m, **acc)
        f.add_command(label="New C File", accelerator="Ctrl+N", command=lambda: self.new_file("c"))
        f.add_command(label="New C++ File", command=lambda: self.new_file("cpp"))
        f.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        f.add_separator()
        f.add_command(label="Save", accelerator="Ctrl+S", command=self.save)
        f.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as)
        f.add_command(label="Close Tab", accelerator="Ctrl+W", command=self.close_tab)
        f.add_separator()
        f.add_command(label="Exit", command=self.quit)
        m.add_cascade(label="File", menu=f)

        e = tk.Menu(m, **acc)
        gen = lambda name: lambda: self.current() and self.current().text.event_generate(name)
        e.add_command(label="Undo", accelerator="Ctrl+Z", command=gen("<<Undo>>"))
        e.add_command(label="Redo", accelerator="Ctrl+Y", command=gen("<<Redo>>"))
        e.add_separator()
        e.add_command(label="Cut", accelerator="Ctrl+X", command=gen("<<Cut>>"))
        e.add_command(label="Copy", accelerator="Ctrl+C", command=gen("<<Copy>>"))
        e.add_command(label="Paste", accelerator="Ctrl+V", command=gen("<<Paste>>"))
        e.add_command(label="Select All", accelerator="Ctrl+A", command=gen("<<SelectAll>>"))
        e.add_separator()
        e.add_command(label="Toggle Comment", accelerator="Ctrl+/", command=self.shortcuts["<Control-slash>"])
        e.add_command(label="Find...", accelerator="Ctrl+F", command=self.find)
        e.add_command(label="Find Next", accelerator="F3", command=self.find_next)
        e.add_command(label="Go to Line...", accelerator="Ctrl+G", command=self.goto_line)
        e.add_separator()
        e.add_command(label="Zoom In", accelerator="Ctrl++", command=lambda: self.zoom(1))
        e.add_command(label="Zoom Out", accelerator="Ctrl+-", command=lambda: self.zoom(-1))
        m.add_cascade(label="Edit", menu=e)

        b = tk.Menu(m, **acc)
        b.add_command(label="Compile", accelerator="F9", command=self.compile)
        b.add_command(label="Run", accelerator="F10", command=self.run)
        b.add_command(label="Compile & Run", accelerator="F11", command=self.compile_and_run)
        b.add_separator()
        b.add_checkbutton(label="Run inside Output panel", variable=self.run_in_panel)
        b.add_command(label="Clear Output", command=self.clear_output)
        m.add_cascade(label="Build", menu=b)

        self.examples_menu = x = tk.Menu(m, **acc)
        x.add_command(label="Browse All Examples...", accelerator="Ctrl+E", command=self.show_examples)
        x.add_separator()
        for name in categories():
            sub = tk.Menu(x, **acc)
            for _cat, title, lang, fname, code in by_category(name):
                sub.add_command(label=title,
                                command=lambda l=lang, n=fname, c=code: self.new_file(l, c, n))
            x.add_cascade(label=name, menu=sub)
        m.add_cascade(label="Examples", menu=x)

        h = tk.Menu(m, **acc)
        h.add_command(label="Compiler Setup", command=self.show_compiler_help)
        h.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        h.add_command(label=f"About {APP_NAME}", command=self.show_about)
        m.add_cascade(label="Help", menu=h)
        self.root.configure(menu=m)

    def build_header(self):
        h = tk.Frame(self.root, bg=C["header"])
        h.pack(fill="x")
        logo = tk.Canvas(h, width=44, height=44, bg=C["header"], highlightthickness=0)
        draw_logo(logo, 44)
        logo.pack(side="left", padx=(18, 12), pady=12)
        box = tk.Frame(h, bg=C["header"])
        box.pack(side="left")
        tk.Label(box, text=APP_NAME, bg=C["header"], fg=C["fg"], font=(self.ui, 16, "bold")).pack(anchor="w")

        credit = tk.Frame(box, bg=C["header"])
        credit.pack(anchor="w")
        tk.Label(credit, text=f"{SUBTITLE}  ·  Developed by {AUTHOR}  ·  ",
                 bg=C["header"], fg=C["muted"], font=(self.ui, 9)).pack(side="left")
        link = tk.Label(credit, text=WEBSITE, bg=C["header"], fg=C["note"], cursor="hand2",
                        font=(self.ui, 9, "underline"))
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: webbrowser.open(WEBSITE_URL))
        link.bind("<Enter>", lambda e: link.configure(fg=C["cursor"]))
        link.bind("<Leave>", lambda e: link.configure(fg=C["note"]))

        seg = tk.Frame(h, bg=C["panel"])
        seg.pack(side="right", padx=18)
        tk.Label(h, text="LANGUAGE", bg=C["header"], fg=C["muted"], font=(self.ui, 8, "bold")).pack(side="right")
        self.lang_btns = {}
        for key, label in (("c", "C  ·  C11"), ("cpp", "C++  ·  C++17")):
            b = tk.Label(seg, text=label, font=(self.ui, 10, "bold"), padx=14, pady=6, cursor="hand2")
            b.pack(side="left", padx=3, pady=3)
            b.bind("<Button-1>", lambda e, k=key: self.set_lang(k))
            self.lang_btns[key] = b

    def button(self, parent, text, command, kind="normal", side="left"):
        colors = {"normal": (C["btn"], C["btn_hover"], C["fg"]),
                  "primary": (C["accent"], C["accent_hover"], "white"),
                  "go": (C["go"], C["go_hover"], "white")}[kind]
        b = tk.Label(parent, text=text, bg=colors[0], fg=colors[2], padx=13, pady=6, cursor="hand2",
                     font=(self.ui, 10, "normal" if kind == "normal" else "bold"))
        b.bind("<Enter>", lambda e: b.configure(bg=colors[1]))
        b.bind("<Leave>", lambda e: b.configure(bg=colors[0]))
        b.bind("<ButtonRelease-1>", lambda e: command())
        b.pack(side=side, padx=3, pady=8)
        return b

    def build_toolbar(self):
        tb = tk.Frame(self.root, bg=C["panel"])
        tb.pack(fill="x")
        tk.Frame(tb, bg=C["panel"], width=10).pack(side="left")
        self.button(tb, "+  New", lambda: self.new_file(self.default_lang))
        self.button(tb, "Open", self.open_file)
        self.button(tb, "Save", self.save)
        tk.Frame(tb, bg=C["btn"], width=1, height=24).pack(side="left", padx=10)
        self.button(tb, "Compile  F9", self.compile, "primary")
        self.button(tb, "\u25B6  Run  F10", self.run, "go")
        self.button(tb, "\u26A1 Compile & Run  F11", self.compile_and_run, "go")
        tk.Frame(tb, bg=C["btn"], width=1, height=24).pack(side="left", padx=10)
        self.button(tb, "Examples  Ctrl+E", self.show_examples)
        ex = self.button(tb, "\u25BE", lambda: None)
        ex.bind("<ButtonRelease-1>", lambda e: self.examples_menu.tk_popup(
            ex.winfo_rootx(), ex.winfo_rooty() + ex.winfo_height()))
        tk.Frame(tb, bg=C["panel"], width=10).pack(side="right")
        self.button(tb, "A+", lambda: self.zoom(1), side="right")
        self.button(tb, "A\u2212", lambda: self.zoom(-1), side="right")

    def build_output(self, parent):
        wrap = tk.Frame(parent, bg=C["panel"])
        head = tk.Frame(wrap, bg=C["panel"])
        head.pack(fill="x")
        tk.Label(head, text="OUTPUT", bg=C["panel"], fg=C["muted"], font=(self.ui, 9, "bold")).pack(side="left", padx=14, pady=6)
        clear = tk.Label(head, text="Clear", bg=C["panel"], fg=C["muted"], cursor="hand2", font=(self.ui, 9))
        clear.pack(side="right", padx=14)
        clear.bind("<ButtonRelease-1>", lambda e: self.clear_output())
        ttk.Checkbutton(head, text="Run inside this panel (uses INPUT box, 10 s limit)",
                        variable=self.run_in_panel).pack(side="right", padx=8)

        body = tk.Frame(wrap, bg=C["panel"])
        body.pack(fill="both", expand=True)
        inbox = tk.Frame(body, bg=C["panel"])
        inbox.pack(side="right", fill="y")
        tk.Label(inbox, text="INPUT (stdin)", bg=C["panel"], fg=C["muted"], font=(self.ui, 8, "bold")).pack(anchor="w", padx=4)
        self.stdin_box = tk.Text(inbox, width=26, height=6, bg=C["console"], fg=C["fg"], insertbackground=C["cursor"],
                                 font=self.console_font, relief="flat", bd=0, padx=8, pady=6, highlightthickness=0)
        self.stdin_box.pack(fill="both", expand=True, padx=(4, 10), pady=(2, 10))

        self.output = o = tk.Text(body, bg=C["console"], fg=C["fg"], font=self.console_font, relief="flat", bd=0,
                                  padx=12, pady=8, wrap="word", highlightthickness=0, height=8,
                                  insertbackground=C["console"], cursor="arrow")
        sb = ttk.Scrollbar(body, command=o.yview)
        o.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=(0, 10))
        o.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        for tag, color in (("ok", C["ok"]), ("err", C["danger"]), ("warn", C["warn"]), ("note", C["note"]),
                           ("info", C["muted"]), ("code", "#a6accd"), ("prog", C["fg"])):
            o.tag_configure(tag, foreground=color)
        o.tag_configure("head", foreground=C["fg"], font=(self.console_font.actual("family"), 10, "bold"))
        o.tag_configure("hint", foreground=C["find"], lmargin1=8, lmargin2=24)
        o.tag_configure("link", underline=True)
        o.tag_bind("link", "<Enter>", lambda e: o.configure(cursor="hand2"))
        o.tag_bind("link", "<Leave>", lambda e: o.configure(cursor="arrow"))
        # read-only but still selectable / copyable
        o.bind("<Key>", lambda e: None if (e.state & 0x4 and e.keysym.lower() in ("c", "a")) else "break")
        return wrap

    def show_examples(self):
        existing = getattr(self, "_examples_dialog", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_set()
            return
        self._examples_dialog = ExamplesDialog(self)

    def build_statusbar(self):
        sb = tk.Frame(self.root, bg=C["status"])
        sb.pack(side="bottom", fill="x")
        mk = lambda: tk.Label(sb, bg=C["status"], fg="white", font=(self.ui, 9), padx=10, pady=3)
        self.status_msg = mk()
        self.status_msg.pack(side="left")
        self.status_comp = mk()
        self.status_comp.pack(side="right")
        self.status_lang = mk()
        self.status_lang.pack(side="right")
        self.status_pos = mk()
        self.status_pos.pack(side="right")
        self.status_comp.configure(text="Detecting compiler...")
        self.set_status("Ready")

    # -- helpers
    def bind_shortcuts(self, widget):
        for seq, fn in self.shortcuts.items():
            widget.bind(seq, lambda e, f=fn: (f(), "break")[1])

    def editors(self):
        return [self.root.nametowidget(t) for t in self.nb.tabs()]

    def current(self):
        sel = self.nb.select()
        return self.root.nametowidget(sel) if sel else None

    def set_status(self, text, error=False):
        self.status_msg.configure(text=("\u2716  " if error else "") + text)

    def update_status(self):
        ed = self.current()
        if not ed:
            return
        line, col = ed.text.index("insert").split(".")
        self.status_pos.configure(text=f"Ln {line}, Col {int(col) + 1}")
        self.status_lang.configure(text="C11" if ed.lang == "c" else "C++17")

    def refresh_tab(self, ed):
        if str(ed) not in self.nb.tabs():
            return
        self.nb.tab(ed, text=("\u25CF " if ed.modified() else "") + ed.display_name() + " ")
        if ed is self.current():
            self.root.title(f"{ed.display_name()}  -  {APP_NAME}")

    def on_tab_changed(self):
        for other in self.editors():
            other.completer.hide()
        ed = self.current()
        if not ed:
            return
        self.default_lang = ed.lang
        self.update_lang_buttons()
        self.refresh_tab(ed)
        self.update_status()
        ed.text.focus_set()
        ed.draw_gutter()

    def on_tab_middle_click(self, event):
        try:
            index = self.nb.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return
        self.close_tab(self.root.nametowidget(self.nb.tabs()[index]))

    def update_lang_buttons(self):
        for key, b in self.lang_btns.items():
            active = key == self.default_lang
            b.configure(bg=C["accent"] if active else C["panel"], fg="white" if active else C["muted"])

    def set_lang(self, lang):
        self.default_lang = lang
        ed = self.current()
        if ed and ed.lang != lang:
            ed.set_lang(lang)
            ed.built_hash = None
            if ed.path and lang_from_path(ed.path) not in (None, lang):
                self.out(f"Note: {ed.display_name()} will be compiled as "
                         f"{'C++' if lang == 'cpp' else 'C'} (its extension says otherwise).\n", "warn")
        self.update_lang_buttons()
        self.update_status()

    def zoom(self, delta):
        self.font_size = max(8, min(32, self.font_size + delta))
        self.code_font.configure(size=self.font_size)
        self.code_font_italic.configure(size=self.font_size)
        for ed in self.editors():
            ed.update_tabs()
            ed.draw_gutter()

    # -- output
    def out(self, text, *tags):
        self.output.insert("end", text, tags)
        self.output.see("end")

    def out_link(self, text, tag, ed, line, col):
        name = f"loc{len(self.link_tags)}"
        self.link_tags.append(name)
        self.output.insert("end", text, (tag, "link", name))
        self.output.tag_bind(name, "<Button-1>", lambda e: self.goto(ed, line, col))
        self.output.see("end")

    def clear_output(self):
        self.output.delete("1.0", "end")
        for name in self.link_tags:
            self.output.tag_delete(name)
        self.link_tags.clear()

    def goto(self, ed, line, col=1):
        if not ed.winfo_exists():
            return
        self.nb.select(ed)
        ed.text.mark_set("insert", f"{line}.{max(col - 1, 0)}")
        ed.text.see("insert")
        ed.text.focus_set()
        ed.on_cursor_move()

    # -- files
    def new_file(self, lang="c", content=None, name=None):
        self.untitled_counter += 1
        name = name or f"untitled{self.untitled_counter}.{'cpp' if lang == 'cpp' else 'c'}"
        ed = Editor(self.nb, self, content=TEMPLATES[lang] if content is None else content, lang=lang, name=name)
        self.nb.add(ed, text=name)
        self.nb.select(ed)
        self.on_tab_changed()
        return ed

    def open_file(self):
        paths = filedialog.askopenfilenames(parent=self.root, title="Open", filetypes=SOURCE_TYPES)
        for p in paths:
            self.open_path(p)

    def open_path(self, path):
        path = os.path.abspath(path)
        for ed in self.editors():
            if ed.path and os.path.normcase(ed.path) == os.path.normcase(path):
                self.nb.select(ed)
                return ed
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError as ex:
            messagebox.showerror(APP_NAME, f"Could not open the file.\n\n{ex}", parent=self.root)
            return None
        cur = self.current()
        ed = Editor(self.nb, self, path=path, content=content, lang=lang_from_path(path) or self.default_lang)
        self.nb.add(ed, text=ed.display_name())
        self.nb.select(ed)
        if cur is not None and cur.is_welcome and not cur.modified():
            self.nb.forget(cur)
            cur.destroy()
        self.on_tab_changed()
        self.set_status(f"Opened {path}")
        return ed

    def write_file(self, ed, path):
        code = ed.code()
        if not code.endswith("\n"):
            code += "\n"
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(code)
        except OSError as ex:
            messagebox.showerror(APP_NAME, f"Could not save the file.\n\n{ex}", parent=self.root)
            return False
        ed.path = os.path.abspath(path)
        ed.is_welcome = False
        ed.text.edit_modified(False)
        self.refresh_tab(ed)
        self.set_status(f"Saved {ed.path}")
        return True

    def save(self, ed=None):
        ed = ed or self.current()
        if not ed:
            return False
        return self.write_file(ed, ed.path) if ed.path else self.save_as(ed)

    def save_as(self, ed=None):
        ed = ed or self.current()
        if not ed:
            return False
        ext = ".cpp" if ed.lang == "cpp" else ".c"
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Save As", defaultextension=ext,
            initialfile=os.path.splitext(ed.display_name())[0] + ext, filetypes=SOURCE_TYPES)
        if not path or not self.write_file(ed, path):
            return False
        new_lang = lang_from_path(path)
        if new_lang and new_lang != ed.lang:
            self.set_lang(new_lang)
        return True

    def confirm_close(self, ed):
        if not ed.modified() or ed.is_welcome:
            return True
        self.nb.select(ed)
        answer = messagebox.askyesnocancel(APP_NAME, f"Save changes to {ed.display_name()}?", parent=self.root)
        if answer is None:
            return False
        return self.save(ed) if answer else True

    def close_tab(self, ed=None):
        ed = ed or self.current()
        if not ed or not self.confirm_close(ed):
            return False
        self.nb.forget(ed)
        ed.destroy()
        if not self.editors():
            self.new_file(self.default_lang)
        return True

    def quit(self):
        if all(self.confirm_close(ed) for ed in self.editors()):
            self.root.destroy()

    # -- search
    def find(self):
        if not self.current():
            return
        q = simpledialog.askstring("Find", "Find text:", initialvalue=self.last_find, parent=self.root)
        if q:
            self.last_find = q
            self.find_next()

    def find_next(self):
        ed = self.current()
        if not ed:
            return
        if not self.last_find:
            return self.find()
        t, q = ed.text, self.last_find
        t.tag_remove("find", "1.0", "end")
        pos = t.search(q, "insert+1c", stopindex="end", nocase=True) or t.search(q, "1.0", stopindex="end", nocase=True)
        if not pos:
            self.set_status(f"'{q}' not found", error=True)
            return
        t.tag_add("find", pos, f"{pos}+{len(q)}c")
        self.goto(ed, *(int(p) + i for i, p in enumerate(pos.split("."))))

    def goto_line(self):
        ed = self.current()
        if not ed:
            return
        total = int(ed.text.index("end-1c").split(".")[0])
        n = simpledialog.askinteger("Go to Line", f"Line number (1-{total}):", parent=self.root,
                                    minvalue=1, maxvalue=total)
        if n:
            self.goto(ed, n)

    # -- compiler
    def tool_env(self):
        env = os.environ.copy()
        tool = self.gpp or self.gcc
        if tool:
            env["PATH"] = os.path.dirname(tool) + os.pathsep + env.get("PATH", "")
        return env

    def detect_compiler(self):
        tool = self.gpp or self.gcc
        label = "No compiler found"
        if tool:
            try:
                first = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=20,
                                       creationflags=NO_WINDOW).stdout.splitlines()[0]
                m = re.search(r"(\d+\.\d+(?:\.\d+)?)", first)
                label = ("Clang " if "clang" in first.lower() else "GCC ") + m.group(1) if m else first[:40]
            except (OSError, subprocess.SubprocessError, IndexError):
                label = "Compiler not working"
            self.manifest_dir = self.fix_spaced_compiler_path(tool)
        self.ui_queue.put(lambda: self.compiler_ready(label))

    def fix_spaced_compiler_path(self, tool):
        """Work around a MinGW-w64 bug: GCC hands ld the path of default-manifest.o
        without quotes, so a space anywhere in the compiler's own path (for example
        C:\\Program Files\\...) breaks every link.  Keeping a copy of that one file in a
        folder without spaces and passing -B makes GCC find ours first.

        Returns the folder to pass to -B, or None when nothing needs fixing.
        """
        if not IS_WIN or " " not in tool:
            return None
        try:
            found = subprocess.run([tool, "-print-file-name=default-manifest.o"],
                                   capture_output=True, text=True, timeout=20,
                                   creationflags=NO_WINDOW).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None
        if not found or not os.path.isfile(found):
            return None

        for folder in (WORK_DIR,
                       os.path.join(os.environ.get("PUBLIC", r"C:\Users\Public"), "CodeLabStudio"),
                       r"C:\CodeLabStudio-compiler"):
            if " " in folder:
                continue
            try:
                os.makedirs(folder, exist_ok=True)
                copy = os.path.join(folder, "default-manifest.o")
                if not os.path.isfile(copy) or os.path.getsize(copy) != os.path.getsize(found):
                    shutil.copyfile(found, copy)
                return folder
            except OSError:
                continue
        return None

    def compiler_ready(self, label):
        self.status_comp.configure(text=label)
        if not (self.gcc and self.gpp):
            self.out("\u2716 C/C++ compiler not found.  Open Help > Compiler Setup.\n", "err")

    def show_compiler_help(self):
        messagebox.showinfo(
            "Compiler Setup",
            f"{APP_NAME} uses the free GCC compiler (MinGW-w64).\n\n"
            "1. Download a WinLibs GCC zip (Win64, UCRT) from winlibs.com\n"
            "2. Extract it and copy the  mingw64  folder next to the app:\n\n"
            f"   {os.path.join(app_dir(), 'mingw64', 'bin', 'g++.exe')}\n\n"
            "3. Restart the app.\n\n"
            f"gcc: {self.gcc or 'not found'}\ng++: {self.gpp or 'not found'}",
            parent=self.root)

    def source_for_build(self, ed):
        if ed.path:
            return ed.path if (not ed.modified() or self.save(ed)) else None
        folder = os.path.join(WORK_DIR, f"tab{ed.uid}")
        try:
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, ed.untitled_name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(ed.code() + "\n")
        except OSError as ex:
            messagebox.showerror(APP_NAME, f"Could not write a temporary file.\n\n{ex}", parent=self.root)
            return None
        return path

    def build_command(self, ed, src, exe):
        cpp = ed.lang == "cpp"
        cmd = [self.gpp if cpp else self.gcc, "-x", "c++" if cpp else "c", src, "-x", "none",
               "-o", exe, "-std=gnu++17" if cpp else "-std=gnu11", "-Wall", "-g"]
        if self.manifest_dir:
            cmd[1:1] = ["-B", self.manifest_dir]
        if IS_WIN:
            cmd.append("-static")      # program runs on any PC without MinGW DLLs
        if not cpp:
            cmd.append("-lm")
        return cmd

    def compile_and_run(self):
        self.compile(then_run=True)

    def compile(self, then_run=False):
        ed = self.current()
        if self.busy or not ed:
            return
        if not (self.gpp if ed.lang == "cpp" else self.gcc):
            self.show_compiler_help()
            return
        src = self.source_for_build(ed)
        if not src:
            return
        exe = os.path.splitext(src)[0] + EXE_EXT
        cmd = self.build_command(ed, src, exe)
        code_hash = ed.content_hash()

        self.busy = True
        self.clear_output()
        self.set_status("Compiling...")
        self.out(f"\u25B8 Compiling {os.path.basename(src)}\n", "head")
        shown = [os.path.basename(cmd[0])] + [os.path.basename(c) if c in (src, exe) else c for c in cmd[1:]]
        self.out("  " + " ".join(shlex.quote(c) for c in shown) + "\n\n", "info")

        def work():
            start = time.perf_counter()
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                   cwd=os.path.dirname(src), env=self.tool_env(), timeout=180,
                                   creationflags=NO_WINDOW)
                result = (p.returncode, p.stdout + p.stderr)
            except subprocess.TimeoutExpired:
                result = (-1, "The compiler took longer than 3 minutes and was stopped.")
            except OSError as ex:
                result = (-1, f"Could not start the compiler: {ex}")
            elapsed = time.perf_counter() - start
            self.ui_queue.put(lambda: self.compile_done(ed, src, exe, code_hash, result, elapsed, then_run))

        threading.Thread(target=work, daemon=True).start()

    def compile_done(self, ed, src, exe, code_hash, result, elapsed, then_run):
        self.busy = False
        rc, text = result
        if not ed.winfo_exists():
            return
        src_dir, src_key = os.path.dirname(src), os.path.normcase(os.path.abspath(src))
        errors = warnings = 0
        diag, hints = {}, []

        for line in text.splitlines():
            line = line.replace(src, os.path.basename(src))
            m = RX_DIAG.match(line)
            if m:
                kind, ln, col = m["kind"], int(m["line"]), int(m["col"] or 1)
                fpath = m["file"] if os.path.isabs(m["file"]) else os.path.join(src_dir, m["file"])
                same = os.path.normcase(os.path.abspath(fpath)) == src_key
                is_err = kind != "warning" and kind != "note"
                errors += is_err
                warnings += kind == "warning"
                tag = "err" if is_err else "warn" if kind == "warning" else "note"
                if same and kind != "note" and (diag.get(ln) or ("", 0))[0] != "error":
                    diag[ln] = ("error" if is_err else "warning", col)
                shown = f"{os.path.basename(fpath)}:{ln}:{col}: {kind}: {m['msg']}\n"
                if same:
                    self.out_link(shown, tag, ed, ln, col)
                else:
                    self.out(shown, tag)
            elif re.match(r"^\s*\d*\s*\|", line):
                self.out(line + "\n", "code")
            else:
                self.out(line + "\n", "err" if re.search(r"\berror\b|undefined reference", line) else "info")
            plain = line.translate(PLAIN_QUOTES)
            for rx, hint in HINTS:
                if hint not in hints and re.search(rx, plain):
                    hints.append(hint)

        ed.set_diagnostics(diag)
        plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
        warn_txt = f"  \u00B7  {plural(warnings, 'warning')}" if warnings else ""
        if rc == 0:
            ed.built_hash, ed.built_exe = code_hash, exe
            self.out(f"\n\u2714 Build succeeded in {elapsed:.2f} s{warn_txt}\n", "ok")
            self.set_status("Build succeeded")
            if then_run:
                self.launch(exe)
        else:
            ed.built_hash = None
            self.out(f"\n\u2716 Build failed  \u00B7  {plural(max(errors, 1), 'error')}{warn_txt}\n", "err")
            for hint in hints:
                self.out(f"\u279C Tip: {hint}\n", "hint")
            self.set_status("Build failed", error=True)
            first_error = min((l for l, k in diag.items() if k == "error"), default=None)
            if first_error:
                self.goto(ed, first_error)

    # -- running
    def run(self):
        ed = self.current()
        if self.busy or not ed:
            return
        fresh = (ed.built_exe and ed.built_hash == ed.content_hash() and os.path.isfile(ed.built_exe)
                 and not (ed.path and ed.modified()))
        if fresh:
            self.launch(ed.built_exe)
        else:
            self.compile(then_run=True)

    def launch(self, exe):
        if self.run_in_panel.get():
            return self.run_captured(exe)
        cwd, name = os.path.dirname(exe), os.path.basename(exe)
        try:
            if IS_WIN:
                self.launch_windows_console(exe, cwd, name)
            else:
                self.launch_unix_terminal(exe, cwd)
        except OSError as ex:
            self.out(f"Could not open a console window ({ex}); running inside the panel instead.\n", "warn")
            return self.run_captured(exe)
        self.out(f"\u25B6 {name} is running in a new window.\n", "info")
        self.set_status(f"Running {name}")

    def launch_windows_console(self, exe, cwd, name):
        os.makedirs(WORK_DIR, exist_ok=True)
        bat = os.path.join(WORK_DIR, f"run_{int(time.time() * 1000)}.bat")
        esc = lambda s: s.replace("%", "%%")
        title = re.sub(r"[&|<>^%\"]", "", name)
        with open(bat, "w", encoding="utf-8", newline="\r\n") as fh:
            fh.write("@echo off\nchcp 65001 >nul\n"
                     f"title {title} - {APP_NAME}\n"
                     f"cd /d \"{esc(cwd)}\"\n"
                     f"\"{esc(exe)}\"\n"
                     "set EXITCODE=%ERRORLEVEL%\n"
                     "echo.\necho ------------------------------------------------\n"
                     "echo Program finished with exit code %EXITCODE%\n"
                     "pause\n"
                     "(goto) 2>nul & del \"%~f0\"\n")
        subprocess.Popen(["cmd", "/c", bat], cwd=cwd, env=self.tool_env(), creationflags=NEW_CONSOLE)

    def launch_unix_terminal(self, exe, cwd):
        script = (f"cd {shlex.quote(cwd)}; {shlex.quote(exe)}; rc=$?; echo; "
                  "echo \"--- program finished with exit code $rc ---\"; read -p 'Press Enter to close...' _")
        term = next((t for t in ("x-terminal-emulator", "gnome-terminal", "konsole", "xterm") if shutil.which(t)), None)
        if not term:
            raise OSError("no terminal emulator found")
        sep = "--" if term == "gnome-terminal" else "-e"
        subprocess.Popen([term, sep, "bash", "-c", script], cwd=cwd)

    def run_captured(self, exe):
        data = self.stdin_box.get("1.0", "end-1c")
        if data and not data.endswith("\n"):
            data += "\n"
        name = os.path.basename(exe)
        self.busy = True
        self.set_status(f"Running {name}...")
        self.out(f"\n\u25B6 Running {name}\n", "head")
        self.out("\u2500" * 48 + "\n", "info")

        def work():
            start = time.perf_counter()
            try:
                p = subprocess.run([exe], input=data, capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", cwd=os.path.dirname(exe), env=self.tool_env(),
                                   timeout=RUN_TIMEOUT, creationflags=NO_WINDOW)
                res = (p.stdout, p.stderr, p.returncode, False)
            except subprocess.TimeoutExpired as ex:
                res = (as_text(ex.stdout), as_text(ex.stderr), None, True)
            except OSError as ex:
                res = ("", f"Could not start the program: {ex}", None, False)
            elapsed = time.perf_counter() - start
            self.ui_queue.put(lambda: self.run_done(*res, elapsed))

        threading.Thread(target=work, daemon=True).start()

    def run_done(self, stdout, stderr, rc, timed_out, elapsed):
        self.busy = False
        if stdout:
            self.out(stdout if stdout.endswith("\n") else stdout + "\n", "prog")
        if stderr:
            self.out(stderr if stderr.endswith("\n") else stderr + "\n", "err")
        self.out("\u2500" * 48 + "\n", "info")
        if timed_out:
            self.out(f"\u2716 Stopped after {RUN_TIMEOUT} s. Infinite loop, or waiting for input? "
                     "Type the input in the INPUT box.\n", "err")
            self.set_status("Program stopped (time limit)", error=True)
            return
        if rc is None:
            self.set_status("Program could not start", error=True)
            return
        crash = describe_exit(rc)
        if crash:
            self.out(f"\u2716 Program {crash}  ({elapsed:.2f} s)\n", "err")
            self.set_status("Program crashed", error=True)
        else:
            self.out(f"Program finished with exit code {rc}  ({elapsed:.2f} s)\n", "ok" if rc == 0 else "warn")
            self.set_status("Program finished")

    # -- dialogs
    def show_shortcuts(self):
        messagebox.showinfo("Keyboard Shortcuts", "\n".join([
            "F9\tCompile", "F10\tRun", "F11\tCompile & Run", "",
            "Ctrl+E\tBrowse example programs",
            "Ctrl+Space\tSuggest a word", "Enter / Tab\tAccept the suggestion",
            "Ctrl+W\tClose the current tab (or click the x on it)", "",
            "Ctrl+N\tNew file", "Ctrl+O\tOpen", "Ctrl+S\tSave", "Ctrl+Shift+S\tSave As", "Ctrl+W\tClose tab", "",
            "Ctrl+/\tComment / uncomment", "Tab / Shift+Tab\tIndent / unindent",
            "Ctrl+F, F3\tFind, find next", "Ctrl+G\tGo to line", "Ctrl + / -\tZoom",
        ]), parent=self.root)

    def show_about(self):
        if messagebox.askyesno(
                f"About {APP_NAME}",
                f"{APP_NAME} {APP_VERSION}\n{SUBTITLE}\n\n"
                f"Developed by {AUTHOR}\n{WEBSITE}\n\n"
                f"Compiler: {self.status_comp.cget('text')}\n"
                "Click any error in the Output panel to jump to that line.\n\n"
                "Open the website now?",
                parent=self.root):
            webbrowser.open(WEBSITE_URL)


def cleanup_work_dir():
    try:
        os.makedirs(WORK_DIR, exist_ok=True)
        cutoff = time.time() - 86400
        for name in os.listdir(WORK_DIR):
            path = os.path.join(WORK_DIR, name)
            if name.startswith("run_") and os.path.getmtime(path) < cutoff:
                os.remove(path)
    except OSError:
        pass   # temp cleanup is best-effort


def main():
    if IS_WIN:
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)          # sharp text on HiDPI screens
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CodeLab.Studio")
        except (AttributeError, OSError):
            pass
    cleanup_work_dir()
    root = tk.Tk()
    App(root, [a for a in sys.argv[1:] if os.path.isfile(a)])
    root.mainloop()


if __name__ == "__main__":
    main()
