#!/usr/bin/env python3
"""Strip the bundled toolchain down to what CodeLab Studio actually runs.

The WinLibs package is a general-purpose developer kit: it carries CMake,
Ninja, ccache, Cppcheck, Doxygen, Premake, Fortran and Objective-C compilers,
man pages and translations.  CodeLab Studio never invokes any of them, and
Microsoft Store policy 10.2.3 objects to shipping secondary software a product
does not need - so the Store package leaves them out.

Run this against a COPY of the build output (make_msix.bat runs it against the
staged package layout).  It refuses to touch anything that is not a layout.

    python prune_toolchain.py msix\\layout            # prune
    python prune_toolchain.py msix\\layout --dry-run  # just report

The keep lists below were derived from the real dependency closure: ntldd -R
over every executable the app can launch.  Re-derive them if the toolchain is
upgraded; `--verify` in make_msix.bat compiles, links and debugs a program with
the pruned tree so a mistake here cannot reach the Store.
"""

import os
from pathlib import Path
import shutil
import sys


# Executables the app can start, directly or through the compiler driver.
KEEP_EXE = {
    'gcc', 'g++', 'cpp', 'c++',                     # compiler drivers
    'gcc-ar', 'gcc-nm', 'gcc-ranlib',               # LTO-aware wrappers gcc may call
    'ld', 'ld.bfd', 'as', 'ar', 'ranlib', 'nm',     # assembler and linker
    'objcopy', 'objdump', 'strip', 'dlltool', 'windres',
    'addr2line', 'readelf', 'size', 'strings', 'elfedit',
    'gdb',                                          # the Debug menu
    'mingw32-make',                                 # harmless, and expected in a toolchain
}

# DLLs the kept executables load, from `ntldd -R`, plus the GCC runtime
# libraries a student's program may need when it is not linked -static.
KEEP_DLL = {
    'libexpat-1', 'libgcc_s_seh-1', 'libgmp-10', 'libiconv-2', 'libintl-8',
    'libisl-23', 'liblzma-5', 'libmman', 'libmpc-3', 'libmpfr-6',
    'libncursesw6', 'libpython3.9', 'libsource-highlight-4', 'libstdc++-6',
    'libwinpthread-1', 'libzstd', 'xxhash', 'zlib1',
    'libatomic-1', 'libgomp-1', 'libquadmath-0', 'libssp-0',
}

# Compiler back ends for languages the IDE does not offer.
DROP_LIBEXEC = {'cc1obj.exe', 'cc1objplus.exe', 'f951.exe', 'lto1.exe', 'd21.exe', 'gnat1.exe'}

# Whole directories of documentation and unrelated tools.
DROP_SHARE = {'cmake', 'cppcheck', 'info', 'man', 'locale', 'doc', 'doxygen', 'premake'}


def _size(path):
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())


def prune(layout, dry_run=False):
    layout = Path(layout)
    mingw = layout / 'mingw64'
    if not (layout / 'CodeLabStudio.exe').is_file() or not (mingw / 'bin' / 'gcc.exe').is_file():
        raise SystemExit(f'Not a CodeLab Studio package layout: {layout}\n'
                         'Expected CodeLabStudio.exe and mingw64\\bin\\gcc.exe inside it.')
    if mingw.is_symlink():
        raise SystemExit(f'{mingw} is a symlink - refusing to prune the original toolchain.')

    removed, freed = [], 0
    for item in sorted((mingw / 'bin').iterdir()):
        stem, suffix = item.stem, item.suffix.lower()
        if suffix == '.exe':
            # x86_64-w64-mingw32-gcc and friends are the same drivers under
            # their target-prefixed names; keep whatever we keep unprefixed.
            base = stem[len('x86_64-w64-mingw32-'):] if stem.startswith('x86_64-w64-mingw32-') else stem
            if base in KEEP_EXE:
                continue
        elif suffix == '.dll':
            if stem.lower() in KEEP_DLL:
                continue
        else:
            continue       # .crt bundles, manifests and the like: leave alone
        freed += _size(item)
        removed.append(item)

    for parent in (mingw / 'libexec' / 'gcc').glob('*/*'):
        for name in DROP_LIBEXEC:
            victim = parent / name
            if victim.is_file():
                freed += _size(victim)
                removed.append(victim)

    share = mingw / 'share'
    if share.is_dir():
        for item in sorted(share.iterdir()):
            # share/gcc-16.1.0 holds the GDB pretty printers; share/gdb is GDB's
            # own data directory.  Both stay.
            head = item.name.lower().split('-')[0]
            if item.is_dir() and head in DROP_SHARE:
                freed += _size(item)
                removed.append(item)

    for item in removed:
        print(('would remove ' if dry_run else 'removed ') + str(item.relative_to(layout)))
        if not dry_run:
            shutil.rmtree(item) if item.is_dir() else item.unlink()

    print(f'\n{len(removed)} items, {freed / 1024 / 1024:.0f} MB '
          f'{"would be freed" if dry_run else "freed"}')
    return freed


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 1:
        raise SystemExit(__doc__)
    prune(args[0], dry_run='--dry-run' in sys.argv)
