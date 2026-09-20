#!/usr/bin/env python3
"""Prove a packaged toolchain still compiles, links, runs and debugs.

make_msix.bat runs this against the staged layout after prune_toolchain.py has
removed the parts of the WinLibs kit the IDE never calls.  It is the guard that
stops a pruning mistake from reaching the Microsoft Store: every step uses the
same flags codelab_studio.py uses, including -static.

    python verify_toolchain.py msix\\layout

Exits non-zero, loudly, on the first failure.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile

C_SOURCE = '#include <stdio.h>\nint main(void){int n=41;n++;printf("sum=%d\\n",n);return 0;}\n'
CPP_SOURCE = ('#include <iostream>\n#include <vector>\n#include <algorithm>\n'
              'int main(){std::vector<int> v{3,1,2};std::sort(v.begin(),v.end());'
              'for(int x:v)std::cout<<x;std::cout<<"\\n";return 0;}\n')

NO_WINDOW = 0x08000000 if os.name == 'nt' else 0


def run(command, cwd, timeout=180):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout, creationflags=NO_WINDOW)


def check(label, condition, detail=''):
    print(f'{"ok  " if condition else "FAIL"}  {label}')
    if not condition:
        if detail:
            print(detail.strip()[:2000])
        sys.exit(1)


def main(layout):
    # Absolute, always: GCC works out where its own cc1/collect2 live from the
    # path it was invoked by, and these commands run with cwd set elsewhere.
    binary = Path(layout).resolve() / 'mingw64' / 'bin'
    for tool in ('gcc.exe', 'g++.exe', 'gdb.exe', 'ld.exe', 'as.exe'):
        check(f'{tool} present', (binary / tool).is_file())

    with tempfile.TemporaryDirectory() as work:
        work = Path(work)
        (work / 'hello.c').write_text(C_SOURCE, encoding='utf-8')
        (work / 'hello.cpp').write_text(CPP_SOURCE, encoding='utf-8')

        built = run([str(binary / 'gcc.exe'), 'hello.c', '-o', 'hello_c.exe',
                     '-std=gnu11', '-Wall', '-g', '-O0', '-static', '-lm'], work)
        check('compile and link C', built.returncode == 0, built.stderr)
        ran = run([str(work / 'hello_c.exe')], work, timeout=60)
        check('run the C program', ran.stdout.strip() == 'sum=42', ran.stdout + ran.stderr)

        built = run([str(binary / 'g++.exe'), 'hello.cpp', '-o', 'hello_cpp.exe',
                     '-std=gnu++17', '-Wall', '-g', '-O0', '-static'], work)
        check('compile and link C++ (headers, STL, static libstdc++)',
              built.returncode == 0, built.stderr)
        ran = run([str(work / 'hello_cpp.exe')], work, timeout=60)
        check('run the C++ program', ran.stdout.strip() == '123', ran.stdout + ran.stderr)

        # --nx and -batch mirror how debugger.py drives GDB.
        session = run([str(binary / 'gdb.exe'), '--nx', '-batch',
                       '-ex', 'break main', '-ex', 'run', '-ex', 'info locals',
                       '-ex', 'next', '-ex', 'info locals', '-ex', 'kill',
                       str(work / 'hello_c.exe')], work, timeout=180)
        check('GDB breaks, runs and reads locals',
              'Breakpoint 1' in session.stdout and 'n = ' in session.stdout,
              session.stdout + session.stderr)

    print('\nToolchain verified: C, C++, static linking and GDB all work.')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
