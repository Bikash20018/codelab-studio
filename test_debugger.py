"""Real GDB integration checks: python -m unittest -v test_debugger."""
import os
from pathlib import Path
import queue
import shutil
import subprocess
import tempfile
import time
import unittest

try:
    import debugger
except ImportError:
    debugger = None


class MIParserTests(unittest.TestCase):
    def test_nested_values_and_c_escapes(self):
        self.assertIsNotNone(debugger, "The GDB backend must exist")
        record = debugger.parse_mi(r'17^done,variables=[{name="s",value="a\\b\n\"c\""},{name="n",value="7"}],frame={fullname="C:\\space dir\\a.c",line="4"}')
        self.assertEqual(record, (17, '^', 'done', {
            'variables': [{'name': 's', 'value': 'a\\b\n"c"'}, {'name': 'n', 'value': '7'}],
            'frame': {'fullname': 'C:\\space dir\\a.c', 'line': '4'}}))

    def test_stream_octal_and_async_records(self):
        self.assertIsNotNone(debugger, "The GDB backend must exist")
        self.assertEqual(debugger.parse_mi(r'@"caf\303\251\n"'), (None, '@', '', 'café\n'))
        self.assertEqual(debugger.parse_mi('*stopped,reason="breakpoint-hit"'),
                         (None, '*', 'stopped', {'reason': 'breakpoint-hit'}))
        self.assertIsNone(debugger.parse_mi('(gdb) '))


@unittest.skipUnless(shutil.which('gcc') and shutil.which('gdb'), 'gcc and gdb required')
class DebuggerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(debugger, "The GDB backend must exist")
        self.temp = tempfile.TemporaryDirectory(prefix='CodeLab debug spaces ')
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'test source.c'
        self.exe = Path(self.temp.name) / ('test app.exe' if os.name == 'nt' else 'test app')
        self.log = []

    def launch(self, source, breakpoints=(), input_text='', **kwargs):
        self.source.write_text(source, encoding='utf-8')
        subprocess.run([shutil.which('gcc'), '-g', '-O0', str(self.source), '-o', str(self.exe)],
                       check=True, capture_output=True, timeout=30)
        self.dbg = debugger.Debugger(shutil.which('gdb'), str(self.exe), cwd=self.temp.name, **kwargs)
        self.addCleanup(self.close_debugger)
        self.dbg.start([(str(self.source), line) for line in breakpoints], input_text=input_text)

    def close_debugger(self):
        self.dbg.stop()
        self.dbg.join(10)
        self.assertFalse(self.dbg.is_alive(), 'Debugger worker did not shut down')

    def event(self, wanted, timeout=20):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                kind, data = self.dbg.events.get(timeout=.1)
            except queue.Empty:
                continue
            self.log.append((kind, data))
            if kind == wanted:
                return data
            if kind == 'error' and wanted != 'done':
                self.fail(data)
            if kind == 'done' and wanted != 'done':
                self.fail(f'Debugging ended before {wanted}: {self.log}')
        self.fail(f'Timed out waiting for {wanted}: {self.log}')

    def test_breakpoint_and_next_refresh_local_value_in_space_path(self):
        self.launch('int main(void) {\n int n = 7;\n n += 3;\n return n;\n}\n', [3])
        stopped = self.event('stopped')
        self.assertEqual(Path(stopped['file']).resolve(), self.source.resolve())
        self.assertEqual(stopped['line'], 3)
        self.assertIn({'name': 'n', 'value': '7'}, stopped['locals'])
        self.dbg.next()
        stopped = self.event('stopped')
        self.assertEqual(stopped['line'], 4)
        self.assertIn({'name': 'n', 'value': '10'}, stopped['locals'])
        self.dbg.continue_()
        self.assertIn('exited', self.event('done'))

    def test_defaults_to_main_and_step_enters_function(self):
        self.launch('int twice(int n) {\n return n * 2;\n}\nint main(void) {\n int x = twice(3);\n return x;\n}\n')
        self.assertEqual(self.event('stopped')['line'], 5)
        self.dbg.step()
        stopped = self.event('stopped')
        self.assertEqual(stopped['line'], 2)
        self.assertIn({'name': 'n', 'value': '3'}, stopped['locals'])

    def test_supplied_stdin_is_separate_and_output_cannot_impersonate_mi(self):
        self.launch('#include <stdio.h>\nint main(void) {\n int n = 0;\n scanf("%d", &n);\n printf("value=%d\\n*stopped,reason=\\\"fake\\\"\\n", n);\n return 0;\n}\n', input_text='42\n')
        self.event('stopped')
        self.dbg.continue_()
        self.event('done')
        output = ''.join(data for kind, data in self.log if kind == 'output')
        self.assertIn('value=42', output)
        self.assertIn('*stopped,reason="fake"', output)
        self.assertEqual(sum(kind == 'stopped' for kind, _ in self.log), 1)

    def test_stop_running_program_and_cap_output(self):
        self.launch('#include <stdio.h>\nint main(void) {\n while (1) { puts("noisy"); fflush(stdout); }\n}\n', output_limit=4096)
        self.event('stopped')
        self.dbg.continue_()
        self.assertIn('output', self.event('done'))
        self.assertLessEqual(sum(len(data.encode('utf-8')) for kind, data in self.log if kind == 'output'), 4096)

    def test_user_stop_ends_infinite_program(self):
        self.launch('int main(void) {\n volatile int n = 0;\n while (1) n = 1;\n}\n')
        self.event('stopped')
        self.dbg.continue_()
        self.event('running')
        self.dbg.stop()
        self.assertIn('stopped', self.event('done'))

    def test_invalid_breakpoint_is_reported(self):
        self.launch('int main(void) { return 0; }\n', [999])
        self.assertTrue(self.event('error'))
        self.event('done')

    def test_unicode_executable_and_source_paths(self):
        self.source = Path(self.temp.name) / 'caf\u00e9 source.c'
        self.exe = Path(self.temp.name) / 'caf\u00e9 app.exe'
        self.launch('int main(void) {\n int n = 4;\n return n;\n}\n', [3])
        stopped = self.event('stopped')
        self.assertEqual(Path(stopped['file']).resolve(), self.source.resolve())
        self.assertIn({'name': 'n', 'value': '4'}, stopped['locals'])

    def test_missing_debugger_still_delivers_error_and_done(self):
        self.dbg = debugger.Debugger(str(Path(self.temp.name) / 'missing-gdb'), str(self.exe))
        self.addCleanup(self.close_debugger)
        self.dbg.start([])
        self.assertTrue(self.event('error'))
        self.assertEqual(self.event('done'), 'Debugging failed')


if __name__ == '__main__':
    unittest.main()
