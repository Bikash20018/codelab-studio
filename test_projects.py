import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import projects


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ('main.cpp', 'math.c', 'math.h', 'extra/other.c', 'build/skip.c', '.git/skip.c'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_discovery_and_explicit_selection_roundtrip(self):
        project = projects.Project(self.root, ['main.cpp', 'math.c'])
        self.assertEqual(set(project.files), {Path('main.cpp'), Path('math.c'), Path('math.h'), Path('extra/other.c')})
        project.save()
        self.assertEqual(projects.Project.load(self.root).sources, [Path('main.cpp'), Path('math.c')])
        (self.root / 'new.c').write_text('')
        self.assertNotIn(Path('new.c'), projects.Project(self.root).sources)

    def test_rejects_outside_root_headers_missing_and_empty_sources(self):
        for names in (['../outside.c'], ['math.h'], ['missing.c'], []):
            with self.subTest(names=names), self.assertRaises(ValueError):
                projects.Project(self.root, names).build_steps('gcc', 'g++', self.root / 'a.exe')

    def test_bad_manifest_is_reported(self):
        (self.root / '.codelab-project.json').write_text('{broken')
        with self.assertRaisesRegex(ValueError, 'project'):
            projects.Project(self.root)

    def test_per_language_compilation_and_cpp_linker(self):
        project = projects.Project(self.root, ['main.cpp', 'math.c'])
        steps = project.build_steps('gcc', 'g++', self.root / 'app.exe', ['-B', 'compiler support'])
        self.assertEqual([s[0] for s in steps], ['g++', 'gcc', 'g++'])
        for step in steps[:2]:
            self.assertIn('-c', step)
            self.assertIn('-g', step)
            self.assertIn('-O0', step)
            self.assertIn('-Wall', step)
            self.assertIn(str(self.root), step)
            self.assertIn('compiler support', step)
        self.assertIn('-std=gnu11', steps[1])
        self.assertIn('-std=gnu++17', steps[0])
        self.assertNotEqual(steps[0][steps[0].index('-o') + 1], steps[1][steps[1].index('-o') + 1])

    def test_real_mixed_project_builds_and_runs(self):
        tools = Path(__file__).parent / 'mingw64' / 'bin'
        gcc, gpp = tools / 'gcc.exe', tools / 'g++.exe'
        if not gcc.exists():
            self.skipTest('Bundled compiler unavailable')
        (self.root / 'math.h').write_text('#ifdef __cplusplus\nextern "C" {\n#endif\nint add(int,int);\n#ifdef __cplusplus\n}\n#endif\n')
        (self.root / 'math.c').write_text('#include "math.h"\nint add(int a,int b){return a+b;}\n')
        (self.root / 'main.cpp').write_text('#include <iostream>\n#include "math.h"\nint main(){std::cout << add(20,22) << "\\n";}\n')
        exe = self.root / 'result.exe'
        for command in projects.Project(self.root, ['main.cpp', 'math.c']).build_steps(gcc, gpp, exe):
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.stdout, '42\n')


if __name__ == '__main__':
    unittest.main()
