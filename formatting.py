"""clang-format integration and small, editable language snippets."""
import os
import subprocess


STYLE = '{BasedOnStyle: LLVM, IndentWidth: 4, TabWidth: 4, UseTab: Never, BreakBeforeBraces: Allman, ColumnLimit: 100, SortIncludes: Never}'


def format_code(code, lang, tool):
    if lang not in ('c', 'cpp'):
        raise ValueError('Unsupported formatting language; choose C or C++.')
    if not tool:
        raise RuntimeError('clang-format was not found. Install or restore the bundled formatter.')
    try:
        result = subprocess.run(
            [str(tool), '--style=' + STYLE, '--assume-filename=code.' + ('cpp' if lang == 'cpp' else 'c')],
            input=code, text=True, encoding='utf-8', capture_output=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    except FileNotFoundError as exc:
        raise RuntimeError('clang-format was not found. Install or restore the bundled formatter.') from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Formatting timed out. Your original code has been kept.') from exc
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f'Could not run clang-format: {exc}') from exc
    if result.returncode:
        raise RuntimeError('Formatting failed: ' + (result.stderr.strip() or 'clang-format returned an error.'))
    return result.stdout


SNIPPETS = {
    'c': {
        'For loop': 'for (int i = 0; i < count; ++i)\n{\n    // Repeat work here.\n}\n',
        'Read an integer': 'int value;\nif (scanf("%d", &value) != 1)\n{\n    return 1;\n}\n',
        'Print a value': 'printf("%d\\n", value);\n',
        'Function': 'int add(int a, int b)\n{\n    return a + b;\n}\n',
        'Array traversal': 'int values[] = {1, 2, 3};\nint count = sizeof(values) / sizeof(values[0]);\nfor (int i = 0; i < count; ++i)\n{\n    printf("%d\\n", values[i]);\n}\n',
    },
    'cpp': {
        'For loop': 'for (int i = 0; i < count; ++i)\n{\n    // Repeat work here.\n}\n',
        'Read an integer': 'int value;\nif (!(std::cin >> value))\n{\n    return 1;\n}\n',
        'Print a value': 'std::cout << value << "\\n";\n',
        'Function': 'int add(int a, int b)\n{\n    return a + b;\n}\n',
        'Vector traversal': '// Requires #include <vector> and #include <iostream>.\nstd::vector<int> values = {1, 2, 3};\nfor (int value : values)\n{\n    std::cout << value << "\\n";\n}\n',
    },
}
