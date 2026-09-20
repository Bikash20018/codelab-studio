import subprocess
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import formatting


class FormattingTests(unittest.TestCase):
    def test_fixed_style_and_language_are_passed_without_config_lookup(self):
        with patch('formatting.subprocess.run', return_value=subprocess.CompletedProcess([], 0, 'int x;\n', '')) as run:
            self.assertEqual(formatting.format_code('int  x;', 'cpp', 'formatter.exe'), 'int x;\n')
        args, kwargs = run.call_args
        self.assertIn('--assume-filename=code.cpp', args[0])
        self.assertTrue(any(a.startswith('--style={') for a in args[0]))
        self.assertNotIn('--style=file', args[0])
        self.assertEqual(kwargs['input'], 'int  x;')
        self.assertFalse(kwargs.get('shell', False))

    def test_missing_and_failed_formatter_report_clear_errors(self):
        with self.assertRaisesRegex(ValueError, 'language'):
            formatting.format_code('', 'python', 'clang-format')
        with patch('formatting.subprocess.run', side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RuntimeError, 'not found'):
                formatting.format_code('int x;', 'c', 'missing.exe')
        with patch('formatting.subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'bad code')):
            with self.assertRaisesRegex(RuntimeError, 'bad code'):
                formatting.format_code('int x;', 'c', 'formatter.exe')

    def test_snippets_cover_both_languages(self):
        self.assertEqual(set(formatting.SNIPPETS), {'c', 'cpp'})
        for snippets in formatting.SNIPPETS.values():
            self.assertGreaterEqual(len(snippets), 4)
            self.assertTrue(all(label and code.strip() for label, code in snippets.items()))

    def test_real_formatter_changes_layout_and_preserves_code(self):
        here = Path(__file__).parent
        candidates = [here / 'tools/clang-format.exe', here / '.venv/Lib/site-packages/clang_format/data/bin/clang-format.exe']
        candidates += list((Path.home() / '.vscode/extensions').glob('ms-vscode.cpptools-*/LLVM/bin/clang-format.exe'))
        tool = next((str(p) for p in candidates if p.is_file()), shutil.which('clang-format'))
        if not tool:
            self.skipTest('clang-format unavailable')
        for lang in ('c', 'cpp'):
            formatted = formatting.format_code('int main(){int x=1;return x;}', lang, tool)
            self.assertIn('    int x = 1;', formatted)
            self.assertIn('return x;', formatted)
            self.assertEqual(formatting.format_code(formatted, lang, tool), formatted)


if __name__ == '__main__':
    unittest.main()
