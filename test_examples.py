#!/usr/bin/env python3
"""Compile every program in examples.py with the same flags the IDE uses.

Run it after editing examples.py:      python test_examples.py
Exit code 0 means every example builds cleanly (no errors, no warnings).
"""

import os
import shutil
import subprocess
import sys
import tempfile

from examples import EXAMPLES

IS_WIN = os.name == "nt"
HERE = os.path.dirname(os.path.abspath(__file__))


def find_tool(name):
    path = os.path.join(HERE, "mingw64", "bin", name + (".exe" if IS_WIN else ""))
    return path if os.path.isfile(path) else shutil.which(name)


def command(tool, lang, src, exe):
    cpp = lang == "cpp"
    cmd = [tool, "-x", "c++" if cpp else "c", src, "-x", "none", "-o", exe,
           "-std=gnu++17" if cpp else "-std=gnu11", "-Wall", "-g"]
    if IS_WIN:
        cmd.append("-static")
    if not cpp:
        cmd.append("-lm")
    return cmd


def check_manifest_workaround():
    """A compiler path with spaces must add -B, a clean one must not."""
    import codelab_studio as app_module

    class Stub:
        pass

    app, editor = Stub(), Stub()
    app.gcc, app.gpp, editor.lang = "gcc", "g++", "c"

    app.manifest_dir = None
    assert "-B" not in app_module.App.build_command(app, editor, "t.c", "t.exe"), \
        "-B added when the compiler path is fine"

    app.manifest_dir = r"C:\nospaces"
    cmd = app_module.App.build_command(app, editor, "t.c", "t.exe")
    assert cmd[1:3] == ["-B", r"C:\nospaces"], "-B missing or misplaced: %s" % cmd


def check_new_program_names():
    """The New dialog must reject names Windows cannot store."""
    import codelab_studio as app_module

    assert app_module.name_problem("program1") is None
    assert app_module.name_problem("my_first-prog2") is None
    for bad in ("", "   ", "my prog?", "a/b", "hello.", "con", "NUL", "x" * 61):
        assert app_module.name_problem(bad), "should have been rejected: %r" % bad


def check_editor_features():
    """Word suggestions, error squiggles and the x on each tab."""
    import tkinter as tk
    import codelab_studio as app_module

    class Key:
        def __init__(self, char, keysym):
            self.char, self.keysym, self.state = char, keysym, 0

    root = tk.Tk()
    root.geometry("1100x650+4000+4000")          # off to the side, not in the way
    try:
        app = app_module.App(root)
        editor = app.new_file("c", "#include <stdio.h>\n\nint main(void)\n{\n    \n}\n", "demo.c")
        root.update()

        editor.text.mark_set("insert", "5.4")
        editor.text.insert("insert", "p")
        editor.on_key_release(Key("p", "p"))
        root.update()
        assert editor.completer.visible(), "no suggestions after typing p"
        offered = [editor.completer.listbox.get(i).strip()
                   for i in range(editor.completer.listbox.size())]
        assert "printf" in offered, "printf not offered for p: %s" % offered
        assert offered[0] == "printf", "common words should come first: %s" % offered

        # Enter must NOT swap the word in until the student picks with an arrow key,
        # otherwise typing a finished word and pressing Enter silently rewrites it.
        assert editor.completer.accept(only_if_chosen=True) is None, \
            "Enter accepted a suggestion the student never selected"
        assert not editor.completer.visible(), "popup should close when Enter is let through"

        editor.text.insert("insert", "r")
        editor.on_key_release(Key("r", "r"))
        root.update()
        assert editor.completer.visible(), "no suggestions after typing pr"
        editor.completer.accept()
        root.update()
        assert editor.text.get("5.0", "5.end").strip() == "printf", \
            "accepting did not insert the word: %r" % editor.text.get("5.0", "5.end")
        assert not editor.completer.visible(), "popup stayed open after accepting"

        editor.on_keypress(Key("(", "parenleft"))    # auto-pair, then Backspace kills both
        root.update()
        assert editor.text.get("5.0", "5.end").strip() == "printf()", editor.text.get("5.0", "5.end")
        editor.on_backspace(None)
        assert editor.text.get("5.0", "5.end").strip() == "printf", \
            "Backspace left an orphan bracket: %r" % editor.text.get("5.0", "5.end")

        editor.set_diagnostics({5: ("error", 5), 3: ("warning", 1)})
        root.update()
        assert len(editor.squiggles) == 2, "expected 2 squiggles, got %d" % len(editor.squiggles)

        # jump-to-first-error reads the (kind, col) tuples, not bare strings
        first = min((l for l, (k, _c) in editor.diag.items() if k == "error"), default=None)
        assert first == 5, "first error line not found: %r" % first

        # A blank line must get a short squiggle, not one spanning the window:
        # line 2 of the fixture is empty, and "2.end-1c" would land on line 1.
        editor.set_diagnostics({2: ("error", 1)})
        root.update()
        assert len(editor.squiggles) == 1
        narrow = int(editor.squiggles[0].cget("width"))
        assert narrow < 60, "squiggle on a blank line is %dpx wide" % narrow

        editor.text.edit_modified(False)
        editor.text.insert("insert", "x")            # editing invalidates the markers
        root.update()
        assert not editor.diag, "stale diagnostics survived an edit"
        assert not editor.squiggles, "stale squiggles survived an edit"

        close_at = None
        for x in range(0, 600, 2):
            for y in range(2, 34, 2):
                if "close" in app.nb.identify(x, y):
                    close_at = Key("", "")
                    close_at.x, close_at.y = x, y
                    break
            if close_at:
                break
        assert close_at, "no close button found on the tabs"
        before = len(app.editors())
        app.on_tab_press(close_at)
        app.on_tab_release(close_at)
        root.update()
        assert len(app.editors()) == before - 1, "clicking the x did not close the tab"
    finally:
        root.destroy()


def check_browser():
    """Open the Examples browser off-screen and make sure it still filters and opens."""
    import tkinter as tk
    import codelab_studio as app_module

    root = tk.Tk()
    root.withdraw()
    try:
        app = app_module.App(root)
        dialog = app_module.ExamplesDialog(app)
        root.update()

        assert len(dialog.shown) == len(EXAMPLES), "browser did not list every example"

        dialog.query.set("pointer")
        root.update()
        assert dialog.shown, "search for 'pointer' found nothing"

        dialog.query.set("")
        dialog.pick_category("C++ STL")
        root.update()
        assert all(e[0] == "C++ STL" for e in dialog.shown), "category filter leaked other topics"

        before = len(app.editors())
        dialog.select_row(0)
        root.update()
        assert dialog.preview.get("1.0", "end-1c").strip(), "preview stayed empty"
        dialog.open_selected()
        root.update()
        assert len(app.editors()) == before + 1, "opening an example did not add a tab"
    finally:
        root.destroy()


def main():
    gcc, gpp = find_tool("gcc"), find_tool("g++")
    if not (gcc and gpp):
        print("gcc/g++ not found - put mingw64 next to this file or on PATH")
        return 2

    failures = []
    work = tempfile.mkdtemp(prefix="codelab_test_")
    try:
        for category, title, lang, fname, code in EXAMPLES:
            src = os.path.join(work, fname)
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(code)
            exe = os.path.splitext(src)[0] + (".exe" if IS_WIN else ".out")

            done = subprocess.run(command(gpp if lang == "cpp" else gcc, lang, src, exe),
                                  capture_output=True, text=True)
            noise = done.stderr.strip()
            if done.returncode != 0 or noise:
                failures.append((category, title, fname, noise or "unknown error"))
                print("FAIL  %-24s %s" % (category, title))
            else:
                print("ok    %-24s %s" % (category, title))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print("\n%d examples, %d failed." % (len(EXAMPLES), len(failures)))
    for category, title, fname, message in failures:
        print("\n--- %s / %s  (%s)\n%s" % (category, title, fname, message))
    if failures:
        return 1

    for check in (check_manifest_workaround, check_new_program_names,
                  check_editor_features, check_browser):
        try:
            check()
        except Exception as ex:                  # noqa: BLE001 - report anything that breaks
            print("%s FAILED: %s" % (check.__name__, ex))
            return 1
        print("%s ok." % check.__name__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
