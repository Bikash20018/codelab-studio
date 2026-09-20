# Installer exit codes

`CodeLabStudio-Setup-<version>.exe` is built with [Inno Setup](https://jrsoftware.org/isinfo.php)
and returns Inno Setup's standard exit codes. This page is the documentation
referenced from the Microsoft Store submission's *Installer handling* field.

## Silent install

```
CodeLabStudio-Setup-2.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER
```

`/CURRENTUSER` installs for the signed-in user only, under
`%LOCALAPPDATA%\Programs\CodeLab Studio`, and needs no elevation. Drop it (or use
`/ALLUSERS`) for a per-machine install under `C:\Program Files\CodeLab Studio`,
which does require elevation.

## Silent uninstall

```
"%LOCALAPPDATA%\Programs\CodeLab Studio\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

Per-machine installs put `unins000.exe` in `%ProgramFiles%\CodeLab Studio` instead.

## Exit codes

| Code | Meaning | Store scenario |
| --- | --- | --- |
| `0` | Setup ran to completion. | Installation successful |
| `1` | Setup failed to initialize. | Install failure |
| `2` | The user cancelled before installation started. | Installation cancelled by user |
| `3` | A fatal error occurred while preparing the next installation phase. | Install failure |
| `4` | A fatal error occurred during installation. | Install failure |
| `5` | The user cancelled during installation, or chose Abort at a retry prompt. | Installation cancelled by user |
| `6` | Setup was forcefully terminated by a debugger. | Install failure |
| `7` | The Preparing to Install stage determined Setup cannot proceed, and aborted. | Install failure |
| `8` | The Preparing to Install stage determined a restart is required, and aborted. | Reboot required |

Codes `1`, `3`, `4`, `6` and `7` are all generic failures — Inno Setup does not
distinguish a full disk, a blocked write or a security policy from any other
fatal error, so none of them can be mapped to a specific cause. A disk-full
condition surfaces as `4`, the same as everything else that fails mid-copy.

The installer performs no network access, so no exit code corresponds to a
network failure.

## Detecting an existing installation

| | |
| --- | --- |
| Registry key | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{8F3C2A51-6B7D-4E1A-9C55-2D7B1E0A4C93}_is1` |
| Per-user installs | the same path under `HKCU` |
| Value to read | `DisplayVersion` |

## Requirements

64-bit Windows 10 version 1809 or newer. The installer is self-contained: the
GCC/GDB toolchain and clang-format are inside it, and nothing is downloaded
during installation.
