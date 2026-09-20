"""Small deterministic exercises with visible input and expected output."""


def normalize_output(text):
    return '\n'.join(line.rstrip(' \t') for line in text.replace('\r\n', '\n').split('\n'))


def compare_output(actual, expected):
    return normalize_output(actual) == normalize_output(expected)


def describe_result(actual, expected):
    """repr makes missing newlines and unexpected spaces visible to beginners."""
    verdict = 'Passed' if compare_output(actual, expected) else 'Output differs'
    return f'{verdict}\nExpected: {expected!r}\nActual:   {actual!r}'


EXERCISES = [
    {
        'id': 'c-sum', 'title': 'Add two numbers', 'lang': 'c', 'filename': 'sum.c',
        'prompt': 'Read two integers between -1000 and 1000. Print their sum followed by a newline. Do not print an input prompt.',
        'hint': 'Read with scanf("%d %d", &a, &b), then print a + b using %d.',
        'starter': '#include <stdio.h>\n\nint main(void)\n{\n    // TODO: read two integers and print their sum.\n    return 0;\n}\n',
        'cases': [{'input': '2 3\n', 'expected': '5\n'}, {'input': '-7 4\n', 'expected': '-3\n'}, {'input': '0 0\n', 'expected': '0\n'}],
    },
    {
        'id': 'c-parity', 'title': 'Even or odd', 'lang': 'c', 'filename': 'parity.c',
        'prompt': 'Read one integer between -1000 and 1000. Print Even if it is divisible by 2, otherwise print Odd. End with a newline.',
        'hint': 'Use n % 2 == 0. This also works for zero and negative integers.',
        'starter': '#include <stdio.h>\n\nint main(void)\n{\n    // TODO: read an integer and decide its parity.\n    return 0;\n}\n',
        'cases': [{'input': '8\n', 'expected': 'Even\n'}, {'input': '-3\n', 'expected': 'Odd\n'}, {'input': '0\n', 'expected': 'Even\n'}, {'input': '-4\n', 'expected': 'Even\n'}],
    },
    {
        'id': 'c-countdown', 'title': 'Countdown', 'lang': 'c', 'filename': 'countdown.c',
        'prompt': 'Read an integer n between 0 and 20. Print each integer from n down to 0 on its own line, including both ends.',
        'hint': 'A for loop can start at n, continue while i >= 0, and subtract one each time.',
        'starter': '#include <stdio.h>\n\nint main(void)\n{\n    // TODO: read n and count down to zero.\n    return 0;\n}\n',
        'cases': [{'input': '3\n', 'expected': '3\n2\n1\n0\n'}, {'input': '0\n', 'expected': '0\n'}, {'input': '1\n', 'expected': '1\n0\n'}],
    },
    {
        'id': 'c-maximum', 'title': 'Largest array value', 'lang': 'c', 'filename': 'maximum.c',
        'prompt': 'Read a count n (1 to 100), followed by n integers between -1000 and 1000. Print the largest value and a newline.',
        'hint': 'Initialize the maximum from the first input value, not from zero, so all-negative arrays work.',
        'starter': '#include <stdio.h>\n\nint main(void)\n{\n    // TODO: read the count and find the maximum.\n    return 0;\n}\n',
        'cases': [{'input': '5\n3 9 2 9 1\n', 'expected': '9\n'}, {'input': '3\n-9 -2 -5\n', 'expected': '-2\n'}, {'input': '1\n-7\n', 'expected': '-7\n'}],
    },
    {
        'id': 'cpp-vowels', 'title': 'Count vowels', 'lang': 'cpp', 'filename': 'vowels.cpp',
        'prompt': 'Read one line of ASCII text (at most 100 characters). Count the vowels a, e, i, o, u, ignoring case. Print the count and a newline. The line may be empty.',
        'hint': 'Use std::getline and visit each character. Check both lowercase and uppercase vowels.',
        'starter': '#include <iostream>\n#include <string>\n\nint main()\n{\n    // TODO: read one line and count its vowels.\n    return 0;\n}\n',
        'cases': [{'input': 'Hello World\n', 'expected': '3\n'}, {'input': 'AEIOU xyz\n', 'expected': '5\n'}, {'input': '\n', 'expected': '0\n'}, {'input': 'rhythm\n', 'expected': '0\n'}],
    },
    {
        'id': 'cpp-sort', 'title': 'Sort a vector', 'lang': 'cpp', 'filename': 'sort.cpp',
        'prompt': 'Read n (1 to 100), then n integers between -1000 and 1000. Print them in ascending order, separated by single spaces, and finish with a newline.',
        'hint': 'Store values in std::vector<int>, call std::sort, and print a space before every value except the first.',
        'starter': '#include <algorithm>\n#include <iostream>\n#include <vector>\n\nint main()\n{\n    // TODO: read, sort, and print the values.\n    return 0;\n}\n',
        'cases': [{'input': '5\n3 1 4 1 2\n', 'expected': '1 1 2 3 4\n'}, {'input': '3\n-2 0 -5\n', 'expected': '-5 -2 0\n'}, {'input': '1\n7\n', 'expected': '7\n'}],
    },
    {
        'id': 'cpp-palindrome', 'title': 'Palindrome word', 'lang': 'cpp', 'filename': 'palindrome.cpp',
        'prompt': 'Read one nonempty lowercase word of at most 100 letters. Print Yes if it reads the same backwards, otherwise print No. End with a newline.',
        'hint': 'Compare characters from both ends moving toward the center, or compare with a reversed copy.',
        'starter': '#include <algorithm>\n#include <iostream>\n#include <string>\n\nint main()\n{\n    // TODO: read a word and check whether it is a palindrome.\n    return 0;\n}\n',
        'cases': [{'input': 'level\n', 'expected': 'Yes\n'}, {'input': 'hello\n', 'expected': 'No\n'}, {'input': 'a\n', 'expected': 'Yes\n'}, {'input': 'abba\n', 'expected': 'Yes\n'}],
    },
    {
        'id': 'cpp-frequency', 'title': 'Count a target value', 'lang': 'cpp', 'filename': 'frequency.cpp',
        'prompt': 'Read n (0 to 100) and a target integer, then n integers. All values are between -1000 and 1000. Print how often the target appears, followed by a newline.',
        'hint': 'Start a counter at zero. Increase it only when the current value equals the target.',
        'starter': '#include <iostream>\n\nint main()\n{\n    // TODO: count occurrences of the target in the input.\n    return 0;\n}\n',
        'cases': [{'input': '5 2\n2 1 2 3 2\n', 'expected': '3\n'}, {'input': '3 -1\n0 1 2\n', 'expected': '0\n'}, {'input': '0 7\n', 'expected': '0\n'}, {'input': '2 -1\n-1 -1\n', 'expected': '2\n'}],
    },
]
