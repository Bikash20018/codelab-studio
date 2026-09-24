# CodeLab Studio — C/C++ IDE for students

A Windows IDE (like a friendlier Dev-C++) in your choice of dark or light theme, built
on Python's standard library, with the free GCC compiler bundled inside, so students
need nothing else installed.

Developed by **Bikash Chhetri** — [www.bikashchhetri.com.np](https://www.bikashchhetri.com.np)

## What's new in 2.1.0

- **A clearer workspace:** blue-slate dark and crisp light themes, a compact command
  bar, persistent open programs and project navigation, visible learning tools,
  a redesigned welcome screen, and clearer build status.
- **Command palette (Ctrl+Shift+P):** search actions by name, see their shortcuts,
  and run them with Enter. Build commands adapt to whether a job is running.
- **Quick open (Ctrl+P):** filter open programs and project sources by file name or
  path, including unnamed programs, without opening duplicate tabs.
- **Workspace search (Ctrl+Shift+F):** find text across C/C++ sources and headers,
  with match-case and whole-word options. Results include unsaved editor contents
  and open at the exact match. Changed files require a fresh search before jumping.
  Search runs in the background, can be cancelled, skips unreadable/binary files
  and files over 2 MB, and displays at most 1,000 matches. Use Project > Refresh Files
  after adding files outside the app. Without a project it searches open programs.
- **Focus mode (Ctrl+Shift+M):** hide the sidebar and output, then restore their
  sizes. Starting a build restores the output automatically.
- **Save all (Ctrl+Alt+S):** save edited and unnamed programs together; cancelling
  a save stops the operation and keeps the remaining buffers intact.
- **Reliability:** edited welcome programs are included in recovery and navigation;
  theme switching keeps button contrast and correctly restores the dark palette.

## What's new in 2.0.0

- **Crash recovery:** every save is atomic (a failed write never truncates your file),
  and the workspace is snapshotted a moment after you stop typing. Reopening restores
  your tabs, unsaved text, cursor, scroll position, breakpoints, selected tab and open
  project folder. Tabs you closed on purpose are not restored; a file changed on disk
  behind your back reopens as a separate *(recovered)* tab instead of overwriting anything.
- **Format Code (Ctrl+Shift+I):** clang-format is bundled, so one keystroke reindents
  the file as a single undo step. `Learn & Tools > Insert Template` drops in loop,
  `if / else`, function and class skeletons.
- **Live input and output:** panel runs stream stdout and stderr as they are produced
  and accept one line of input at a time, so prompts appear before you answer them.
  Send EOF or Stop at any point; the 200,000-byte and time limits still apply.
- **Practice Exercises:** eight built-in C/C++ exercises, each with a prompt, a hint,
  starter code and several input/expected-output cases. Run your own code against every
  case, see expected against actual, and keep your progress between sessions. Nothing is
  submitted anywhere and no solution is filled in for you.
- **Real debugger:** `Debug` drives GDB through its machine interface — F5 start,
  F8 breakpoint, F6 step over, F7 step into, continue and stop, with the current source
  line highlighted and local variables listed. Commands that make no sense in the current
  state are disabled.
- **Multi-file projects:** `Project > Open Folder` shows a file tree; choose exactly which
  sources to build, mix C and C++ in one program, use the folder as an include root, and
  jump from a diagnostic to the right file. Open project tabs are saved before each build.
- **Light and dark themes:** `View > Dark/Light Theme` switches instantly and the choice
  persists. A Welcome view offers new file, open file, open folder, practice and recent
  files, and the status bar states what the current job is doing.

## What's new in 1.4.0

- **Find and replace inside the editor:** Ctrl+F / Ctrl+H, match case, whole words,
  previous/next with wrapping, match counts, and Replace All with a single undo.
- **Stop builds and panel runs:** use Stop or Shift+F5. Active buttons show job state;
  shutdown waits for the active job to terminate. Separate console windows remain
  independently controlled by their own close button.
- **Bounded execution:** panel runs stop after 10 seconds or more than 200,000 bytes
  on either output stream. Compiler jobs have a three-minute limit. The visible
  output keeps the latest 200,000 characters, with a clear explanation when stopped.
- **Problems tab:** compiler errors and warnings in a table with source navigation.
  A changed source cannot launch an outdated build or reuse stale error links.
- **Recent files and preferences:** File > Open Recent keeps the last ten files;
  font size and panel-run preference persist in `%APPDATA%\CodeLabStudio\settings.json`
  (or `~/.config/CodeLabStudio/settings.json` on Linux).
- **UI improvements:** keyboard-focusable toolbar buttons, file location context,
  dark output tabs, Copy Output, and scrollable example categories.
- **File safety fixes:** invalid UTF-8 is rejected instead of silently corrupted;
  UTF-8 BOM files open correctly; Save As updates the correct tab's language.

Run the source with `python codelab_studio.py`. The packaged release is
`dist/2.1.0/CodeLabStudio/CodeLabStudio.exe`; keep its whole folder together.
Previous releases remain in their versioned folders.

Validation: `python -m unittest -v test_studio test_upgrade test_execution_live
test_debugger test_formatting test_learning test_projects test_workbench` runs the regression,
recovery, streaming-execution, GDB, formatting, exercise and multi-file build
tests. `python test_examples.py` checks all 81 examples plus editor and
example-browser behavior. GCC/G++, GDB, clang-format and a working Tk display are
needed for the full suite. The runtime remains Python's standard library only.

**Features:** tabs · syntax highlighting · line numbers · auto-indent and bracket
closing · C (C11) / C++ (C++17) switch · F9 compile, F10 run, F11 compile & run ·
programs run in their own console window (so `scanf`/`cin` work) or inside the
Output panel with a live INPUT box, streaming output and an editable time limit
(120 seconds by default) · click an error to jump to its line ·
**New asks for the program name** (validated for Windows) instead of
piling up untitled buffers · **a compact command bar and workspace sidebar**, with
the file name in the title bar and the language switch in the status bar ·
**red wavy underlines on errors** (amber for warnings) like VS Code ·
plain-English tips for common mistakes · friendly crash messages (divide by zero,
bad pointer) · **81 built-in example programs** in 11 topics with a searchable
browser (**Ctrl+E**) and live preview · **word suggestions while you type**
(type `p`, get `printf`; Tab accepts, or use arrows then Enter; Ctrl+Space forces the list) ·
an **x** on every tab · comment toggle, find, go-to-line, zoom.

**Where the 2.0 tools live:** `Learn & Tools > Format Code` (Ctrl+Shift+I),
`Learn & Tools > Insert Template`, `Learn & Tools > Practice Exercises`,
`Project > Open Folder / Choose Build Files`, `Debug > Start Debugging` (F5),
`Toggle Breakpoint` (F8), `Step Over` (F6), `Step Into` (F7), and
`View > Welcome / Dark Theme / Light Theme`.

**Example topics:** getting started · decisions · loops & patterns · functions &
recursion · arrays & strings · pointers & structures · files · games & fun ·
C++ basics · C++ classes & objects · C++ STL.

## Folder layout

```
CodeLabStudio/
├── codelab_studio.py     the app
├── studio_features.py    workspace UI: recovery, project, debug, practice, themes
├── workbench.py          command actions, navigation, save all and focus mode
├── navigation.py         file/command pickers and cancellable workspace search
├── recovery.py           atomic saves and the session snapshot file
├── execution.py          streaming stdout/stderr with line-by-line stdin
├── debugger.py           GDB machine-interface backend
├── projects.py           multi-file / mixed C and C++ builds
├── learning.py           the practice exercises and output comparison
├── formatting.py         clang-format call and the code templates
├── examples.py           the 81 ready-made programs
├── test_*.py             one suite per module above
├── assets/app.ico, app.png
├── tools/clang-format.exe  the bundled formatter
├── build.bat             makes the .exe
├── installer.iss         makes Setup.exe (optional)
├── make_installer.bat    runs Inno Setup without opening its window
├── packaging/AppxManifest.xml  identity and file types for the Store package
├── make_msix.bat         makes the .msix from the build output
├── prune_toolchain.py    drops the toolchain parts the IDE never runs (Store build)
├── verify_toolchain.py   compiles, links and debugs with the pruned toolchain
├── licenses/             GPL and LLVM texts + the third-party notices, shipped in the app
└── mingw64/              ← you add this (GCC compiler + GDB)
```

## Build the .exe (on a Windows PC)

1. Install **Python 3.9+** from python.org (tick "Add python.exe to PATH").
2. Download **WinLibs GCC** from https://winlibs.com — pick the *Win64, UCRT*
   release **zip** (the "without LLVM" one is smaller; it still ships GDB, which the
   debugger needs). Extract it and move the `mingw64` folder into this folder.
3. Double-click **build.bat**. It bundles `assets\` and `tools\clang-format.exe`
   (the Format Code button) and then copies `mingw64\` beside the .exe.
4. Your app is in `dist\CodeLabStudio\` — run `CodeLabStudio.exe`. Copy that whole
   folder to a USB drive for lab computers; it works without installing.

## Make a real installer (optional)

Install **Inno Setup 6.3+** (jrsoftware.org), open `installer.iss`, press **Compile**.
You get `installer\CodeLabStudio-Setup-2.1.0.exe` with Start-menu/desktop shortcuts,
an uninstaller, and optional "Open with" for .c/.cpp files.

## Publish to the Microsoft Store

The Store build is the same PyInstaller folder, wrapped in an **MSIX** package instead of
an Inno installer. The Store strips your signature and re-signs the package itself, so a
purchased code-signing certificate is **not** needed — that requirement only applies to
the .exe/.msi submission route. Both channels keep shipping: the Store package for
students, the Inno installer for labs, USB sticks and anyone off the Store.

**1. Prerequisites.** Windows 10 1809 or newer, x64. The Windows SDK (this project used
10.0.26100.0) for `makeappx.exe`, `makepri.exe` and `signtool.exe`. Python with Pillow for
the icons. A Partner Center developer account from https://storedeveloper.microsoft.com —
individual registration is free and needs a personal Microsoft account, a government ID
and a selfie; company registration takes days to weeks and **cannot** be converted from an
individual account later, so choose before you sign up. The publisher display name you
pick at signup is shown to customers and goes into the manifest.

**2. Reserve the product name.** Partner Center > Apps and games > New product > App. The
reservation holds for three months. Do not put "GCC", "MinGW" or "Dev-C++" in the title —
naming another project's software in your own title invites a trademark rejection.
Mentioning it in the description is fine, and is in fact required (see step 8).

**3. Copy the identity values.** Product management > Product identity gives you three
strings. Paste them into `packaging\AppxManifest.xml` exactly, including case and
punctuation: `Package/Identity/Name`, `Package/Identity/Publisher` (the whole `CN=...`
string) and `Package/Properties/PublisherDisplayName`. Upload fails if any of them differ
by a character. Leave `Version="2.1.0.0"` alone: an MSIX version is always **four** parts
and the fourth is reserved for the Store — a non-zero fourth part is rejected at upload.
Bump the third part for a rebuild (2.0.1.0), the second for a feature release (2.1.0.0).
Every submission must be strictly higher than the last one that was accepted, including
after a failed certification. Keep `#define AppVersion` in `installer.iss` and the
`dist\<version>\` folder in step with the first three parts.

**4. Generate the icons.** `python make_assets.py` writes `assets\app.ico` and `app.png` as
before, plus the ~90 PNGs the manifest needs in `assets\msix\` — the app-list icon at five
scales, the taskbar target sizes with their unplated light and dark variants, the tiles,
the splash screen and the Store logo. MSIX cannot use `.ico` at all. Run it again whenever
the logo changes.

**5. Build.** `build.bat` first, then `make_msix.bat`. The second script mirrors the build
output into `msix\layout`, adds the manifest, `Assets\` and `licenses\`, removes the
toolchain parts the IDE never runs, then **proves the pruned toolchain still works** —
it compiles, links, runs and GDB-debugs a real program and refuses to pack if any of that
fails. Finally it runs `makepri.exe` (the scale and target-size icons are inert without
`resources.pri`; indexing the toolchain is slow but harmless) and packs
`installer\CodeLabStudio-2.1.0.0-x64.msix`.

**6. Test-sign and install it locally.** This step only proves the package installs and
runs; the certificate never leaves your machine.

```
powershell -Command "New-SelfSignedCertificate -Type Custom -KeyUsage DigitalSignature ^
  -CertStoreLocation 'Cert:\CurrentUser\My' -Subject 'CN=<your Publisher string>' ^
  -TextExtension @('2.5.29.37={text}1.3.6.1.5.5.7.3.3','2.5.29.19={text}') ^
  -FriendlyName 'CodeLab Studio MSIX TEST ONLY'"
```

The certificate's Subject must equal the manifest's `Publisher` exactly. Export it to a
`.pfx`, import that into `Cert:\LocalMachine\TrustedPeople` from an **elevated**
PowerShell, sign the package with `signtool sign /fd SHA256 ...`, then
`Add-AppxPackage -Path installer\CodeLabStudio-2.1.0.0-x64.msix`. Re-sign after every
repack. Smoke test: app launches, compile and run a `hello.c` saved in Documents, run in a
separate console, F5 into GDB, Ctrl+Shift+I formats, and a double-clicked `.c` file opens
in CodeLab Studio via *Open with*. Then run the Windows App Certification Kit
(`appcert.exe test -appxpackagepath ...`) — it catches most certification failures before
upload. Finish by removing the test package and deleting the test certificate from
`TrustedPeople`, so nothing on the machine keeps trusting it.

**7. Upload.** Partner Center > your product > Packages, and drop in the `.msix`. Identity,
version, architecture and the block map are validated within minutes. An unsigned or
test-signed package is accepted — the signature is replaced either way.

**8. Fill in the listing.** Free pricing (charging for a bundle whose value largely comes
from GPL'd GCC and GDB invites both licensing and "distinct value" scrutiny), category
Developer tools, the IARC questionnaire (no ads, no purchases, no user-to-user content —
it rates at the bottom), at least one 1366×768 or larger screenshot, and a 300×300 tile
icon. **The description must open with the disclosure** that the app bundles the
MinGW-w64 build of GCC/GDB (GPLv3) and LLVM clang-format (Apache-2.0 with LLVM exception),
that everything is contained in the package, and where the toolchain source lives. Store
policy wants that at the beginning of the description, not in a footnote.

**9. Write the certification notes.** This is the field that decides whether this app
passes. Say that it is an offline developer tool; give the tester literal steps (launch,
File > New, paste hello world, press F9, expect `Hello` in the Output panel, F5 to step
under GDB); state that `gcc.exe`, `g++.exe`, `gdb.exe` and `clang-format.exe` are bundled
third-party binaries invoked as child processes by design; state that nothing is
downloaded or executed from the network; and link the source offer from the risks below.
Certification takes hours to days — the long end, because of the package size and the
antimalware scan over roughly 12,900 bundled binaries.

### Certification risks, honestly

- **GPL license texts — done, and it was not Microsoft's rule.** GCC, G++, `ld` and GDB
  are GPLv3, and the WinLibs zip ships **no** COPYING or LICENSE file anywhere, so
  shipping it as-is was a GPL violation regardless of the channel. `licenses\` now
  carries GPLv3, GPLv2, both LGPLs, the GCC Runtime Library Exception, the mingw-w64
  and LLVM texts, and a `THIRD-PARTY-NOTICES.txt` naming each component and version.
  It ships inside every build and Help > **Licences and Source Code** opens it.
- **You owe the source, not just the license — answered by [SOURCE.md](SOURCE.md).**
  Conveying GCC/GDB binaries obliges you to provide the corresponding source. Since
  Microsoft's CDN does the delivering, the practical route is GPLv3 6(d): clear directions
  next to the binaries pointing at the source. `SOURCE.md` names every bundled component,
  its exact version and a direct upstream download (GCC 16.1.0 from ftp.gnu.org, GDB 17.2
  from sourceware.org, the WinLibs `16.1.0posix-14.0.0-ucrt-r4` build it all came from),
  and `licenses\THIRD-PARTY-NOTICES.txt` inside the app points at it. Keep that page
  reachable for as long as you ship this version and cite it in the Store description.
  "It is on winlibs.com somewhere" does not satisfy it.
- **GPL versus store terms is unsettled.** The Store's terms restrict what end users may do
  with the package; GPLv3 section 10 forbids adding restrictions. This is the argument that
  got VLC pulled from a store and has never been settled for the Microsoft Store. Microsoft
  is very unlikely to reject you over it, but a copyright holder could complain. The
  standard mitigation is exactly what this project already does: keep publishing the same
  binaries and the source offer yourself, outside the Store, under plain GPL terms — and
  say so in the listing.
- **This app compiles and runs code the user writes.** That is dynamic code execution, and
  a reviewer who discovers it without being told will reject it. Disclosed up front, it is
  the same posture as every other compiler on the Store and it passes. The corollary is
  permanent: never add a feature that downloads code from the internet and runs it.
- **Bundling tools you do not use — handled for the Store build.** The WinLibs kit also
  carries CMake, Ninja, ccache, Cppcheck, Doxygen, Premake, the Fortran and Objective-C
  back ends, man pages and translations, none of which CodeLab Studio invokes. Store
  policy says a product must not install secondary software it does not need, so
  `make_msix.bat` runs `prune_toolchain.py` over the staged copy and drops 382 MB of it,
  then `verify_toolchain.py` compiles, links, runs and GDB-debugs a program with what is
  left before anything is packed. The Inno installer still ships the complete kit.
- **A compiler and a debugger look like malware to a scanner.** GDB attaches to and
  controls processes; binutils are classic dual-use binaries. Expect a slow certification
  pass, and be ready to answer a false positive with the WinLibs provenance and hashes.
- **Leave no orphans.** A tester who ends up with a console window they cannot close fails
  you on usability. Check that Stop kills the whole process tree and that closing the IDE
  does not strand a console.

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

- **SmartScreen:** a Store-installed package is signed by Microsoft, so students see no
  warning at all. The warning is only about the side-loaded `CodeLabStudio-Setup-2.1.0.exe`
  and about an .msix you test-signed yourself — click *More info → Run anyway*, or sign
  the installer with a code-signing certificate.
- **Antivirus:** some tools flag PyInstaller apps by mistake; the `--onedir` build used
  here triggers this less than `--onefile`. The Store build is scanned once during
  certification and then carries Microsoft's signature, which usually settles Defender
  down — the cost moves to a slower first certification instead, because the package
  contains a compiler and a debugger.
- **Static linking:** compiled programs are linked with `-static`, so the `.exe` files
  students make run on any Windows PC. This matters more under MSIX: the install folder is
  replaced on every update and deleted on uninstall, so a program linked against DLLs in
  there would stop working the next time the Store updated the app. Static linking keeps
  the student's .exe theirs.
- **Package size:** the Store build is about 560 MB installed — `make_msix.bat` leaves out
  the 382 MB of the toolchain the IDE never runs. The Inno installer still carries the
  full 946 MB kit. Both are far under the Store's 25 GB limit; the number matters because
  it is what a student on a slow connection actually downloads.
- **The install folder is read-only.** A Store package lives under
  `C:\Program Files\WindowsApps\...`, which is ACL-locked and integrity-checked, so nothing
  can be dropped next to the .exe — dropping in your own `mingw64` folder works for the
  portable build only. If the Store build ever reports a missing compiler, repair or
  reinstall it; the advanced escape hatch is to install MinGW-w64 yourself and put its
  `bin` folder on PATH, which the compiler lookup honours.
- **Settings and recovery move.** For the packaged app Windows redirects
  `%APPDATA%\CodeLabStudio` into
  `%LOCALAPPDATA%\Packages\<PackageFamilyName>\LocalCache\Roaming\CodeLabStudio`. Settings,
  recent files and crash-recovery snapshots still work, but a student who switches from
  the installer to the Store build starts with an empty workspace.
- **File associations come from the manifest.** The .c/.cpp *Open with* entry is declared
  in `packaging\AppxManifest.xml`, not written to the registry — a packaged app's registry
  writes are private to the package and would never reach Explorer. The Inno installer
  keeps doing it the registry way for the side-loaded build.
- **Updates:** the Store build updates itself in the background. The side-loaded build is
  updated by running the newer installer over it.
- **Linux:** the source still runs there — `sudo apt install python3-tk g++` then
  `python3 codelab_studio.py`. The packaged release and the Store package are Windows-only.
