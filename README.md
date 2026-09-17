# CodeLab Studio — C/C++ IDE for students

A dark-themed Windows IDE (like a friendlier Dev-C++) built on Python's standard
library, with the free GCC compiler bundled inside, so students need nothing else installed.

Developed by **Bikash Chhetri** — [www.bikashchhetri.com.np](https://www.bikashchhetri.com.np)

**Features:** tabs · syntax highlighting · line numbers · auto-indent and bracket
closing · C (C11) / C++ (C++17) switch · F9 compile, F10 run, F11 compile & run ·
programs run in their own console window (so `scanf`/`cin` work) or inside the
Output panel with an INPUT box and a 10-second loop guard · click an error to jump to
its line · **red wavy underlines on errors** (amber for warnings) like VS Code ·
plain-English tips for common mistakes · friendly crash messages (divide by zero,
bad pointer) · **81 built-in example programs** in 11 topics with a searchable
browser (**Ctrl+E**) and live preview · **word suggestions while you type**
(type `p`, get `printf`; Enter or Tab accepts, Ctrl+Space forces the list) ·
an **x** on every tab · comment toggle, find, go-to-line, zoom.

**Example topics:** getting started · decisions · loops & patterns · functions &
recursion · arrays & strings · pointers & structures · files · games & fun ·
C++ basics · C++ classes & objects · C++ STL.

## Folder layout

```
CodeLabStudio/
├── codelab_studio.py     the app
├── examples.py           the 81 ready-made programs
├── test_examples.py      compiles every example + checks the browser
├── assets/app.ico, app.png
├── build.bat             makes the .exe
├── installer.iss         makes Setup.exe (optional)
├── make_installer.bat    runs Inno Setup without opening its window
└── mingw64/              ← you add this (GCC compiler)
```

## Build the .exe (on a Windows PC)

1. Install **Python 3.9+** from python.org (tick "Add python.exe to PATH").
2. Download **WinLibs GCC** from https://winlibs.com — pick the *Win64, UCRT*
   release **zip** (the "without LLVM" one is smaller). Extract it and move the
   `mingw64` folder into this folder.
3. Double-click **build.bat**.
4. Your app is in `dist\CodeLabStudio\` — run `CodeLabStudio.exe`. Copy that whole
   folder to a USB drive for lab computers; it works without installing.

## Make a real installer (optional)

Install **Inno Setup 6.3+** (jrsoftware.org), open `installer.iss`, press **Compile**.
You get `installer\CodeLabStudio-Setup-1.0.0.exe` with Start-menu/desktop shortcuts,
an uninstaller, and optional "Open with" for .c/.cpp files.

## Customize

Top of `codelab_studio.py`: `APP_NAME`, `APP_VERSION`, `SUBTITLE`, `AUTHOR`,
`WEBSITE`. Colors are in the `C` dictionary. The logo is drawn in code by
`draw_logo()`; re-generate the icon files with `python make_assets.py` (needs Pillow).

Suggestion words live in `C_LIBRARY`, `CPP_LIBRARY` and `COMMON_WORDS`.

Example programs live in `examples.py` as `(category, title, language, filename,
code)` rows; add a category to `CATEGORY_ORDER` to place it in the menu. After
editing, run `python test_examples.py` — it compiles all of them with the same
flags the IDE uses and fails on any warning.

## Notes

- Windows SmartScreen will warn about any new unsigned .exe — click
  *More info → Run anyway*, or sign it with a code-signing certificate.
- Some antivirus tools flag PyInstaller apps by mistake; the `--onedir` build
  used here triggers this less than `--onefile`.
- Compiled programs are linked with `-static`, so the `.exe` files students make
  run on any Windows PC.
- Test on Linux: `sudo apt install python3-tk g++` then `python3 codelab_studio.py`.
