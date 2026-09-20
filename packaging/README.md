# MSIX packaging

How CodeLab Studio becomes a Microsoft Store submission. The Store re-signs the
package itself, so **no purchased code-signing certificate is needed** - that is
the whole reason this route exists instead of submitting the Inno `.exe`.

## Files

| File | What it is |
| --- | --- |
| `packaging/AppxManifest.xml` | The package manifest. Edit this one; `make_msix.bat` copies it into the layout. |
| `packaging/README.md` | This guide. |
| `make_msix.bat` | Stages the layout, prunes it, verifies it, builds `resources.pri`, packs the `.msix`. Optional local test-signing. |
| `make_assets.py` | Also emits `assets/msix/` (90 PNGs: tiles, target-size icons, unplated variants). |
| `prune_toolchain.py` | Removes the parts of the WinLibs kit the IDE never runs. Acts on the staged layout only. |
| `verify_toolchain.py` | Compiles, links, runs and GDB-debugs with the pruned tree. `make_msix.bat` stops if it fails. |
| `licenses/` | GPL/LGPL texts, the GCC Runtime Library Exception, the LLVM licence and `THIRD-PARTY-NOTICES.txt`. Shipped inside the package; surfaced by Help > Licences and Source Code. |
| `msix/layout/` | Generated staging folder. Mirrored from `dist/<version>/CodeLabStudio` on every run - never edit by hand. |
| `installer/CodeLabStudio-<version>.0-x64.msix` | The artifact you upload. |

The Inno route (`installer.iss` + `make_installer.bat`) stays alive alongside
this one. Keep publishing it: it is the non-Store channel that lets users
exercise their GPL rights on the bundled GCC/GDB outside the Store's terms.

## Prerequisites

- Windows 10/11 SDK, for `makeappx.exe` / `makepri.exe` / `signtool.exe`.
  `make_msix.bat` finds the newest `Windows Kits\10\bin\10.*\x64` by itself.
  <https://developer.microsoft.com/windows/downloads/windows-sdk/>
- Pillow, for `make_assets.py` (`pip install pillow`). The app itself needs neither.
- A Partner Center account with the product name reserved (free Individual
  registration as of the 2025 onboarding change).

## Order of operations

```bat
python make_assets.py                  :: assets/app.* + assets/msix/ (only when the logo changes)
build.bat                              :: dist\CodeLabStudio  -> move/copy to dist\2.0.0\CodeLabStudio
make_msix.bat 2.0.0                    :: -> installer\CodeLabStudio-2.0.0.0-x64.msix
make_msix.bat 2.0.0 testsign           :: optional: sign so you can install it locally
```

`make_msix.bat` mirrors the build output into `msix\layout`, drops in the
manifest, `Assets\` and `licenses\`, runs `prune_toolchain.py`, then runs
`verify_toolchain.py` - which compiles, links, runs and GDB-debugs a real
program with the pruned tree and **aborts the packaging** if anything is
missing. Only then does it build `resources.pri` and pack.

Then, before uploading:

```bat
"%ProgramFiles(x86)%\Windows Kits\10\App Certification Kit\appcert.exe" reset
"%ProgramFiles(x86)%\Windows Kits\10\App Certification Kit\appcert.exe" test ^
  -appxpackagepath "installer\CodeLabStudio-2.0.0.0-x64.msix" -reportoutputpath "installer\wack-report.xml"
```

Finally upload `installer\CodeLabStudio-2.0.0.0-x64.msix` to
**Partner Center > your app > Packages**. An unsigned or test-signed package is
accepted; the signature is replaced either way. `.msixupload` buys nothing here
(PyInstaller produces no PDBs the Store can symbolicate).

## Placeholders you must replace

All three live in `packaging/AppxManifest.xml` and all three are copied
verbatim - case, spaces and punctuation included - from
**Partner Center > Product management > Product identity**:

| Placeholder | Partner Center field |
| --- | --- |
| `Name="PLACEHOLDER.CodeLabStudio"` | Package/Identity/Name |
| `Publisher="CN=PLACEHOLDER-GUID-FROM-PARTNER-CENTER"` | Package/Identity/Publisher (the whole `CN=...` string) |
| `<PublisherDisplayName>PLACEHOLDER-...` | Package/Properties/PublisherDisplayName |

`make_msix.bat` warns (but still packs) while any `PLACEHOLDER` remains, so you
can test locally before the name is reserved. Partner Center will reject the
upload until they are real.

## Versioning

MSIX versions are always four parts and **the fourth must be 0** at submission -
Partner Center rejects anything else. `2.0.0` is `2.0.0.0`.

- bugfix rebuild -> `2.0.1.0` (never `2.0.0.1`)
- feature release -> `2.1.0.0`, next major -> `3.0.0.0`
- a CI build number goes in the **third** segment, `2.0.<build>.0`
- every submission must be strictly higher than anything previously accepted,
  including after a certification failure

Keep `installer.iss`'s `#define AppVersion`, the `dist\<version>\` folder and the
manifest's first three segments in sync. `make_msix.bat` refuses to pack if the
manifest version and its argument disagree.

## Local test install

`make_msix.bat <version> testsign` creates a throwaway self-signed certificate
(subject = the manifest's `Publisher`), exports `msix\codelab-test.pfx` and signs
the package. It deliberately stops there and **prints** the two commands that
change machine-wide state - importing the certificate into
`LocalMachine\TrustedPeople` (elevated) and `Add-AppxPackage` - plus the cleanup
commands. Run those yourself, and run the cleanup when you are done: a trusted
test certificate is a standing risk.

Smoke-test checklist after installing: app launches; compile+run a `hello.c`
saved under Documents; separate-console run; F5 GDB debug; Ctrl+Shift+I
clang-format; Help > Compiler Setup finds gcc under
`C:\Program Files\WindowsApps\...`; double-click a `.c` file (Open with >
CodeLab Studio).

## Still on you before you submit

The packaging is done; these are decisions and paperwork it cannot make:

- **Publish the source offer.** `licenses\THIRD-PARTY-NOTICES.txt` points at
  `https://www.bikashchhetri.com.np/codelab-studio/source` for the GPL
  components' corresponding source. That page has to exist and serve the
  WinLibs source archive for build `gcc-16.1.0-mingw-w64ucrt-14.0.0-r4`, free
  of charge, for as long as you distribute this version. GPLv3 6(d) allows
  pointing at a server; it does not allow pointing at nothing.
- **Open the listing description with the bundle disclosure** (policy 10.2.4):
  that the package contains the MinGW-w64 build of GCC/GDB (GPLv3) and LLVM
  clang-format (Apache-2.0 with the LLVM exception), fully contained, plus the
  source link above.
- **Say in the certification notes that the app compiles and runs code the user
  writes**, locally and offline, and give the tester literal steps.
- **Run the Windows App Certification Kit** on the packed `.msix` and read the
  report; it catches most failures before Partner Center does.
- **Keep the Inno installer published too.** It is the non-Store channel where a
  user can exercise their GPL rights without the Store's terms in the way.
