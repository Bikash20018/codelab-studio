from pathlib import Path
import subprocess
import tempfile
import unittest

import learning


SOLUTIONS = {
    'c-sum': '#include <stdio.h>\nint main(void){int a,b;scanf("%d%d",&a,&b);printf("%d\\n",a+b);}\n',
    'c-parity': '#include <stdio.h>\nint main(void){int n;scanf("%d",&n);puts(n%2==0?"Even":"Odd");}\n',
    'c-countdown': '#include <stdio.h>\nint main(void){int n;scanf("%d",&n);for(int i=n;i>=0;--i)printf("%d\\n",i);}\n',
    'c-maximum': '#include <stdio.h>\nint main(void){int n,x,best;scanf("%d%d",&n,&best);for(int i=1;i<n;++i){scanf("%d",&x);if(x>best)best=x;}printf("%d\\n",best);}\n',
    'cpp-vowels': '#include <iostream>\n#include <string>\nint main(){std::string s;std::getline(std::cin,s);int n=0;for(char c:s)if(std::string("aeiouAEIOU").find(c)!=std::string::npos)++n;std::cout<<n<<"\\n";}\n',
    'cpp-sort': '#include <algorithm>\n#include <iostream>\n#include <vector>\nint main(){int n;std::cin>>n;std::vector<int> a(n);for(int &x:a)std::cin>>x;std::sort(a.begin(),a.end());for(int i=0;i<n;++i)std::cout<<(i?" ":"")<<a[i];std::cout<<"\\n";}\n',
    'cpp-palindrome': '#include <algorithm>\n#include <iostream>\n#include <string>\nint main(){std::string s;std::cin>>s;std::string r=s;std::reverse(r.begin(),r.end());std::cout<<(s==r?"Yes":"No")<<"\\n";}\n',
    'cpp-frequency': '#include <iostream>\nint main(){int n,target,x,count=0;std::cin>>n>>target;for(int i=0;i<n;++i){std::cin>>x;if(x==target)++count;}std::cout<<count<<"\\n";}\n',
}


class LearningTests(unittest.TestCase):
    def test_comparison_only_relaxes_line_endings_and_trailing_spaces(self):
        self.assertTrue(learning.compare_output('42  \r\nhello\t\r\n', '42\nhello\n'))
        for actual, expected in [(' 42\n', '42\n'), ('4 2\n', '42\n'), ('42\n\n', '42\n'), ('42', '42\n')]:
            self.assertFalse(learning.compare_output(actual, expected))
        report = learning.describe_result('41\n', '42\n')
        self.assertIn('Expected', report)
        self.assertIn('Actual', report)
        self.assertIn('41', report)
        self.assertIn('42', report)

    def test_catalog_balanced_and_each_case_has_distinct_input(self):
        self.assertEqual(len(learning.EXERCISES), 8)
        self.assertEqual(len({e['id'] for e in learning.EXERCISES}), 8)
        self.assertEqual(sum(e['lang'] == 'c' for e in learning.EXERCISES), 4)
        for exercise in learning.EXERCISES:
            self.assertTrue(all(exercise.get(k) for k in ('id', 'title', 'lang', 'filename', 'prompt', 'hint', 'starter', 'cases')))
            self.assertGreaterEqual(len(exercise['cases']), 3)
            self.assertEqual(len({c['input'] for c in exercise['cases']}), len(exercise['cases']))

    def test_starters_compile_but_do_not_pass_all_cases(self):
        tools = Path(__file__).parent / 'mingw64' / 'bin'
        if not (tools / 'gcc.exe').exists():
            self.skipTest('Bundled compiler unavailable')
        with tempfile.TemporaryDirectory() as temp:
            for exercise in learning.EXERCISES:
                with self.subTest(exercise=exercise['id']):
                    source = Path(temp) / exercise['filename']
                    source.write_text(exercise['starter'], encoding='utf-8')
                    exe = source.with_suffix('.exe')
                    cpp = exercise['lang'] == 'cpp'
                    command = [str(tools / ('g++.exe' if cpp else 'gcc.exe')), str(source), '-o', str(exe), '-Wall', '-Werror', '-static', '-std=gnu++17' if cpp else '-std=gnu11']
                    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    first = exercise['cases'][0]
                    result = subprocess.run([str(exe)], input=first['input'], capture_output=True, text=True, timeout=5)
                    self.assertFalse(learning.compare_output(result.stdout, first['expected']))

    def test_reference_solutions_pass_every_published_case(self):
        tools = Path(__file__).parent / 'mingw64' / 'bin'
        if not (tools / 'gcc.exe').exists():
            self.skipTest('Bundled compiler unavailable')
        with tempfile.TemporaryDirectory() as temp:
            for exercise in learning.EXERCISES:
                with self.subTest(exercise=exercise['id']):
                    source = Path(temp) / exercise['filename']
                    source.write_text(SOLUTIONS[exercise['id']], encoding='utf-8')
                    exe = source.with_suffix('.exe')
                    cpp = exercise['lang'] == 'cpp'
                    result = subprocess.run([str(tools / ('g++.exe' if cpp else 'gcc.exe')), str(source), '-o', str(exe), '-Wall', '-Werror', '-static', '-std=gnu++17' if cpp else '-std=gnu11'], capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    for case in exercise['cases']:
                        result = subprocess.run([str(exe)], input=case['input'], capture_output=True, text=True, timeout=5)
                        self.assertEqual(result.returncode, 0)
                        self.assertTrue(learning.compare_output(result.stdout, case['expected']), learning.describe_result(result.stdout, case['expected']))


if __name__ == '__main__':
    unittest.main()
