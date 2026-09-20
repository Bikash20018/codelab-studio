# Source code for the bundled third-party components

CodeLab Studio ships unmodified third-party programs so that students do not
have to install a compiler. Some of them are licensed under the GNU GPL, which
gives every person who receives those binaries the right to the corresponding
source code. This page is the "clear directions" GPLv3 section 6(d) asks for.

CodeLab Studio's own source is this repository.

## What is bundled

Everything under `mingw64\` comes from one upstream build, used as published,
with nothing patched or recompiled:

**winlibs personal build `gcc-16.1.0-mingw-w64ucrt-14.0.0-r4`**, x86_64, POSIX
threads, SEH, UCRT — <https://winlibs.com/> ·
[upstream release](https://github.com/brechtsanders/winlibs_mingw/releases/tag/16.1.0posix-14.0.0-ucrt-r4)
(the binary archive is `winlibs-x86_64-posix-seh-gcc-16.1.0-mingw-w64ucrt-14.0.0-r4.zip`).
The exact build string is repeated in `mingw64\version_info.txt` inside any
installation.

`tools\clang-format.exe` is LLVM's, under the Apache License 2.0 with the LLVM
exception.

## Where to get the corresponding source

| Component | Version | Source |
| --- | --- | --- |
| GCC (gcc, g++, cpp, cc1, cc1plus, libgcc, libstdc++) | 16.1.0 | <https://ftp.gnu.org/gnu/gcc/gcc-16.1.0/gcc-16.1.0.tar.xz> |
| GDB | 17.2 | <https://sourceware.org/pub/gdb/releases/gdb-17.2.tar.xz> |
| GNU Binutils (ld, as, ar, objdump) | 2.47.20260726 snapshot | <https://sourceware.org/pub/binutils/snapshots/> |
| MinGW-w64 runtime and headers | 14.0.0 | <https://github.com/mingw-w64/mingw-w64/releases> |
| GNU Make | 4.4.1 | <https://ftp.gnu.org/gnu/make/make-4.4.1.tar.gz> |
| GMP, MPFR, MPC, ISL (GCC's own prerequisites) | as shipped by the build above | <https://gcc.gnu.org/install/prerequisites.html> |
| LLVM clang-format | see `tools\ThirdPartyNotices.txt` | <https://github.com/llvm/llvm-project> |

The licence texts for all of these ship inside the app, in `licenses\`, and
Help > **Licences and Source Code** opens them.

## If a link ever breaks

Write to the address on <https://www.bikashchhetri.com.np> and ask for the
corresponding source of the version you received. It will be sent to you at no
charge beyond the cost of delivery.

## A note for students

Programs you write in CodeLab Studio are yours. Compiling with GCC does not put
your program under the GPL — that is exactly what the GCC Runtime Library
Exception (`licenses\GCC-Runtime-Library-Exception-3.1.txt`) is for.
