#!/usr/bin/env python3
"""Ready-made example programs for CodeLab Studio.

Each entry is  (category, title, language, filename, source code).
Raw strings are used so the C / C++ escapes (\\n, \\t) stay exactly as typed.
Every program in this file is compiled by  test_examples.py  before release.
"""

EXAMPLES = [

    # ---- Getting started ---------------------------------------------------
    ("Getting started", "Hello World", "c", "hello.c", r'''#include <stdio.h>

int main(void)
{
    printf("Hello, World!\n");
    return 0;
}
'''),

    ("Getting started", "Print your name and class", "c", "about_me.c", r'''#include <stdio.h>

int main(void)
{
    char name[50];
    int class_no;

    printf("Your name : ");
    scanf("%49s", name);
    printf("Your class: ");
    scanf("%d", &class_no);

    printf("\nHello %s of class %d!\n", name, class_no);
    return 0;
}
'''),

    ("Getting started", "Sum of two numbers", "c", "sum.c", r'''#include <stdio.h>

int main(void)
{
    int a, b;

    printf("Enter two numbers: ");
    scanf("%d %d", &a, &b);

    printf("Sum = %d\n", a + b);
    return 0;
}
'''),

    ("Getting started", "Simple calculator", "c", "calculator.c", r'''#include <stdio.h>

int main(void)
{
    double a, b;
    char op;

    printf("Enter calculation (example  12 * 5 ): ");
    scanf("%lf %c %lf", &a, &op, &b);

    switch (op) {
        case '+': printf("%.2f\n", a + b); break;
        case '-': printf("%.2f\n", a - b); break;
        case '*': printf("%.2f\n", a * b); break;
        case '/':
            if (b == 0)
                printf("Cannot divide by zero.\n");
            else
                printf("%.2f\n", a / b);
            break;
        default:
            printf("Unknown operator '%c'. Use + - * /\n", op);
    }
    return 0;
}
'''),

    ("Getting started", "Swap two numbers", "c", "swap.c", r'''#include <stdio.h>

int main(void)
{
    int a, b, temp;

    printf("Enter two numbers: ");
    scanf("%d %d", &a, &b);

    temp = a;
    a = b;
    b = temp;

    printf("After swapping: a = %d, b = %d\n", a, b);
    return 0;
}
'''),

    ("Getting started", "Area and perimeter", "c", "area.c", r'''#include <stdio.h>

#define PI 3.14159265

int main(void)
{
    double length, breadth, radius;

    printf("Rectangle length and breadth: ");
    scanf("%lf %lf", &length, &breadth);
    printf("  area      = %.2f\n", length * breadth);
    printf("  perimeter = %.2f\n\n", 2 * (length + breadth));

    printf("Circle radius: ");
    scanf("%lf", &radius);
    printf("  area          = %.2f\n", PI * radius * radius);
    printf("  circumference = %.2f\n", 2 * PI * radius);
    return 0;
}
'''),

    ("Getting started", "Simple interest", "c", "interest.c", r'''#include <stdio.h>

int main(void)
{
    double principal, rate, years;

    printf("Principal (Rs): ");
    scanf("%lf", &principal);
    printf("Rate (%% per year): ");
    scanf("%lf", &rate);
    printf("Time (years): ");
    scanf("%lf", &years);

    double interest = principal * rate * years / 100.0;
    printf("\nInterest = Rs %.2f\n", interest);
    printf("Total    = Rs %.2f\n", principal + interest);
    return 0;
}
'''),

    ("Getting started", "Celsius to Fahrenheit", "c", "temperature.c", r'''#include <stdio.h>

int main(void)
{
    double celsius;

    printf("Temperature in Celsius: ");
    scanf("%lf", &celsius);

    printf("%.1f C = %.1f F\n", celsius, celsius * 9 / 5 + 32);
    return 0;
}
'''),

    ("Getting started", "ASCII value of a character", "c", "ascii.c", r'''#include <stdio.h>

int main(void)
{
    char ch;

    printf("Enter a character: ");
    scanf(" %c", &ch);

    printf("The ASCII value of '%c' is %d.\n", ch, ch);
    return 0;
}
'''),

    # ---- Decisions ---------------------------------------------------------
    ("Decisions", "Even or odd", "c", "even_odd.c", r'''#include <stdio.h>

int main(void)
{
    int n;

    printf("Enter a number: ");
    scanf("%d", &n);

    if (n % 2 == 0)
        printf("%d is even.\n", n);
    else
        printf("%d is odd.\n", n);
    return 0;
}
'''),

    ("Decisions", "Positive, negative or zero", "c", "sign.c", r'''#include <stdio.h>

int main(void)
{
    double n;

    printf("Enter a number: ");
    scanf("%lf", &n);

    if (n > 0)
        printf("Positive\n");
    else if (n < 0)
        printf("Negative\n");
    else
        printf("Zero\n");
    return 0;
}
'''),

    ("Decisions", "Largest of three numbers", "c", "largest3.c", r'''#include <stdio.h>

int main(void)
{
    double a, b, c;

    printf("Enter three numbers: ");
    scanf("%lf %lf %lf", &a, &b, &c);

    double big = a;
    if (b > big) big = b;
    if (c > big) big = c;

    printf("The largest number is %.2f\n", big);
    return 0;
}
'''),

    ("Decisions", "Vowel or consonant", "c", "vowel.c", r'''#include <stdio.h>
#include <ctype.h>

int main(void)
{
    char ch;

    printf("Enter a letter: ");
    scanf(" %c", &ch);
    ch = (char) tolower(ch);

    if (!isalpha((unsigned char) ch))
        printf("That is not a letter.\n");
    else if (ch == 'a' || ch == 'e' || ch == 'i' || ch == 'o' || ch == 'u')
        printf("%c is a vowel.\n", ch);
    else
        printf("%c is a consonant.\n", ch);
    return 0;
}
'''),

    ("Decisions", "Grade calculator", "c", "grade.c", r'''#include <stdio.h>

int main(void)
{
    double marks;

    printf("Enter marks (0-100): ");
    scanf("%lf", &marks);

    if (marks < 0 || marks > 100) {
        printf("Marks must be between 0 and 100.\n");
        return 1;
    }

    const char *grade;
    if      (marks >= 90) grade = "A+";
    else if (marks >= 80) grade = "A";
    else if (marks >= 70) grade = "B+";
    else if (marks >= 60) grade = "B";
    else if (marks >= 50) grade = "C+";
    else if (marks >= 40) grade = "C";
    else                  grade = "NG";

    printf("Grade: %s\n", grade);
    return 0;
}
'''),

    ("Decisions", "Leap year check", "c", "leap_year.c", r'''#include <stdio.h>

int main(void)
{
    int year;

    printf("Enter a year: ");
    scanf("%d", &year);

    if ((year % 4 == 0 && year % 100 != 0) || year % 400 == 0)
        printf("%d is a leap year.\n", year);
    else
        printf("%d is not a leap year.\n", year);
    return 0;
}
'''),

    ("Decisions", "Quadratic equation roots", "c", "quadratic.c", r'''#include <stdio.h>
#include <math.h>

/* Solves  ax^2 + bx + c = 0  */
int main(void)
{
    double a, b, c;

    printf("Enter a, b and c: ");
    scanf("%lf %lf %lf", &a, &b, &c);

    if (a == 0) {
        printf("Not a quadratic equation (a must not be 0).\n");
        return 1;
    }

    double d = b * b - 4 * a * c;
    if (d > 0) {
        printf("Two real roots: %.3f and %.3f\n",
               (-b + sqrt(d)) / (2 * a), (-b - sqrt(d)) / (2 * a));
    } else if (d == 0) {
        printf("Equal roots: %.3f\n", -b / (2 * a));
    } else {
        double re = -b / (2 * a);
        double im = fabs(sqrt(-d) / (2 * a));
        printf("Complex roots: %.3f + %.3fi and %.3f - %.3fi\n", re, im, re, im);
    }
    return 0;
}
'''),

    ("Decisions", "Days of the month", "c", "days_in_month.c", r'''#include <stdio.h>

int main(void)
{
    int month, year;

    printf("Enter month (1-12) and year: ");
    scanf("%d %d", &month, &year);

    int days;
    switch (month) {
        case 1: case 3: case 5: case 7: case 8: case 10: case 12:
            days = 31; break;
        case 4: case 6: case 9: case 11:
            days = 30; break;
        case 2:
            days = ((year % 4 == 0 && year % 100 != 0) || year % 400 == 0) ? 29 : 28;
            break;
        default:
            printf("There is no month %d.\n", month);
            return 1;
    }
    printf("Month %d of %d has %d days.\n", month, year, days);
    return 0;
}
'''),

    # ---- Loops and patterns ------------------------------------------------
    ("Loops & patterns", "Multiplication table", "c", "table.c", r'''#include <stdio.h>

int main(void)
{
    int n;

    printf("Table of which number? ");
    scanf("%d", &n);

    for (int i = 1; i <= 10; i++)
        printf("%3d x %2d = %4d\n", n, i, n * i);
    return 0;
}
'''),

    ("Loops & patterns", "Count 1 to N", "c", "count.c", r'''#include <stdio.h>

int main(void)
{
    int n, total = 0;

    printf("Count up to: ");
    scanf("%d", &n);

    for (int i = 1; i <= n; i++) {
        printf("%d ", i);
        total += i;
    }
    printf("\nSum of 1..%d = %d\n", n, total);
    return 0;
}
'''),

    ("Loops & patterns", "Factorial", "c", "factorial.c", r'''#include <stdio.h>

int main(void)
{
    int n;

    printf("Enter n (0-20): ");
    scanf("%d", &n);

    if (n < 0 || n > 20) {
        printf("Please enter a number from 0 to 20.\n");
        return 1;
    }

    long long result = 1;
    for (int i = 2; i <= n; i++)
        result *= i;

    printf("%d! = %lld\n", n, result);
    return 0;
}
'''),

    ("Loops & patterns", "Fibonacci series", "c", "fibonacci.c", r'''#include <stdio.h>

int main(void)
{
    int count;

    printf("How many terms? ");
    scanf("%d", &count);

    long long a = 0, b = 1;
    for (int i = 0; i < count; i++) {
        printf("%lld ", a);
        long long next = a + b;
        a = b;
        b = next;
    }
    printf("\n");
    return 0;
}
'''),

    ("Loops & patterns", "Sum and count of digits", "c", "digit_sum.c", r'''#include <stdio.h>

int main(void)
{
    long n;

    printf("Enter a number: ");
    scanf("%ld", &n);

    if (n < 0) n = -n;

    int sum = 0, digits = 0;
    long temp = n;
    do {
        sum += (int) (temp % 10);
        digits++;
        temp /= 10;
    } while (temp > 0);

    printf("%ld has %d digits and their sum is %d.\n", n, digits, sum);
    return 0;
}
'''),

    ("Loops & patterns", "Reverse a number", "c", "reverse_number.c", r'''#include <stdio.h>

int main(void)
{
    long n, reversed = 0;

    printf("Enter a number: ");
    scanf("%ld", &n);

    long temp = n < 0 ? -n : n;
    while (temp > 0) {
        reversed = reversed * 10 + temp % 10;
        temp /= 10;
    }

    printf("Reversed: %ld\n", n < 0 ? -reversed : reversed);
    return 0;
}
'''),

    ("Loops & patterns", "Palindrome number", "c", "palindrome_number.c", r'''#include <stdio.h>

int main(void)
{
    long n;

    printf("Enter a number: ");
    scanf("%ld", &n);

    long temp = n, reversed = 0;
    while (temp > 0) {
        reversed = reversed * 10 + temp % 10;
        temp /= 10;
    }

    if (reversed == n)
        printf("%ld is a palindrome.\n", n);
    else
        printf("%ld is not a palindrome.\n", n);
    return 0;
}
'''),

    ("Loops & patterns", "Armstrong number", "c", "armstrong.c", r'''#include <stdio.h>
#include <math.h>

int main(void)
{
    long n;

    printf("Enter a number: ");
    scanf("%ld", &n);

    int digits = 0;
    for (long t = n; t > 0; t /= 10)
        digits++;

    long sum = 0;
    for (long t = n; t > 0; t /= 10)
        sum += (long) pow((double) (t % 10), digits);

    if (sum == n)
        printf("%ld is an Armstrong number.\n", n);
    else
        printf("%ld is not an Armstrong number.\n", n);
    return 0;
}
'''),

    ("Loops & patterns", "Prime number check", "c", "prime.c", r'''#include <stdio.h>

int main(void)
{
    int n;

    printf("Enter a number: ");
    scanf("%d", &n);

    if (n < 2) {
        printf("%d is not prime.\n", n);
        return 0;
    }

    int is_prime = 1;
    for (int i = 2; (long) i * i <= n; i++) {
        if (n % i == 0) {
            is_prime = 0;
            break;
        }
    }

    printf("%d is %s.\n", n, is_prime ? "prime" : "not prime");
    return 0;
}
'''),

    ("Loops & patterns", "Prime numbers up to N", "c", "prime_list.c", r'''#include <stdio.h>

int main(void)
{
    int n;

    printf("List primes up to: ");
    scanf("%d", &n);

    int found = 0;
    for (int num = 2; num <= n; num++) {
        int is_prime = 1;
        for (int i = 2; i * i <= num; i++) {
            if (num % i == 0) { is_prime = 0; break; }
        }
        if (is_prime) {
            printf("%4d", num);
            if (++found % 10 == 0)
                printf("\n");
        }
    }
    printf("\nFound %d prime numbers.\n", found);
    return 0;
}
'''),

    ("Loops & patterns", "GCD and LCM", "c", "gcd_lcm.c", r'''#include <stdio.h>

int main(void)
{
    long a, b;

    printf("Enter two numbers: ");
    scanf("%ld %ld", &a, &b);

    long x = a, y = b;
    while (y != 0) {          /* Euclid's algorithm */
        long r = x % y;
        x = y;
        y = r;
    }

    printf("GCD = %ld\n", x);
    if (x != 0)
        printf("LCM = %ld\n", a / x * b);
    return 0;
}
'''),

    ("Loops & patterns", "Right triangle of stars", "c", "pattern_triangle.c", r'''#include <stdio.h>

int main(void)
{
    int rows;

    printf("How many rows? ");
    scanf("%d", &rows);

    for (int i = 1; i <= rows; i++) {
        for (int j = 0; j < i; j++)
            printf("* ");
        printf("\n");
    }
    return 0;
}
'''),

    ("Loops & patterns", "Star pyramid", "c", "pattern_pyramid.c", r'''#include <stdio.h>

int main(void)
{
    int rows;

    printf("How many rows? ");
    scanf("%d", &rows);

    for (int i = 1; i <= rows; i++) {
        for (int s = 0; s < rows - i; s++)
            printf(" ");
        for (int j = 0; j < 2 * i - 1; j++)
            printf("*");
        printf("\n");
    }
    return 0;
}
'''),

    ("Loops & patterns", "Diamond pattern", "c", "pattern_diamond.c", r'''#include <stdio.h>

int main(void)
{
    int rows;

    printf("Half height: ");
    scanf("%d", &rows);

    for (int i = 1; i <= rows; i++) {          /* top half */
        for (int s = 0; s < rows - i; s++) printf(" ");
        for (int j = 0; j < 2 * i - 1; j++)   printf("*");
        printf("\n");
    }
    for (int i = rows - 1; i >= 1; i--) {      /* bottom half */
        for (int s = 0; s < rows - i; s++) printf(" ");
        for (int j = 0; j < 2 * i - 1; j++)   printf("*");
        printf("\n");
    }
    return 0;
}
'''),

    ("Loops & patterns", "Floyd's triangle", "c", "pattern_floyd.c", r'''#include <stdio.h>

int main(void)
{
    int rows;

    printf("How many rows? ");
    scanf("%d", &rows);

    int value = 1;
    for (int i = 1; i <= rows; i++) {
        for (int j = 0; j < i; j++)
            printf("%4d", value++);
        printf("\n");
    }
    return 0;
}
'''),

    ("Loops & patterns", "Pascal's triangle", "c", "pattern_pascal.c", r'''#include <stdio.h>

int main(void)
{
    int rows;

    printf("How many rows? ");
    scanf("%d", &rows);

    for (int i = 0; i < rows; i++) {
        for (int s = 0; s < rows - i; s++)
            printf("  ");
        long value = 1;
        for (int j = 0; j <= i; j++) {
            printf("%4ld", value);
            value = value * (i - j) / (j + 1);
        }
        printf("\n");
    }
    return 0;
}
'''),

    # ---- Functions and recursion -------------------------------------------
    ("Functions & recursion", "Your first function", "c", "function_intro.c", r'''#include <stdio.h>

/* A function takes values in and gives one value back. */
int add(int a, int b)
{
    return a + b;
}

void greet(const char *name)
{
    printf("Namaste, %s!\n", name);
}

int main(void)
{
    greet("student");
    printf("7 + 5 = %d\n", add(7, 5));
    printf("2 + 3 + 4 = %d\n", add(add(2, 3), 4));
    return 0;
}
'''),

    ("Functions & recursion", "Factorial by recursion", "c", "recursion_factorial.c", r'''#include <stdio.h>

long long factorial(int n)
{
    if (n <= 1)               /* base case stops the recursion */
        return 1;
    return n * factorial(n - 1);
}

int main(void)
{
    int n;

    printf("Enter n (0-20): ");
    scanf("%d", &n);

    if (n < 0 || n > 20) {
        printf("Please enter a number from 0 to 20.\n");
        return 1;
    }
    printf("%d! = %lld\n", n, factorial(n));
    return 0;
}
'''),

    ("Functions & recursion", "Fibonacci by recursion", "c", "recursion_fibonacci.c", r'''#include <stdio.h>

long fib(int n)
{
    if (n < 2)
        return n;
    return fib(n - 1) + fib(n - 2);
}

int main(void)
{
    int count;

    printf("How many terms (try 10-30)? ");
    scanf("%d", &count);

    for (int i = 0; i < count; i++)
        printf("%ld ", fib(i));
    printf("\n");
    return 0;
}
'''),

    ("Functions & recursion", "Power of a number", "c", "power.c", r'''#include <stdio.h>

double power(double base, int exponent)
{
    if (exponent == 0)
        return 1.0;
    if (exponent < 0)
        return 1.0 / power(base, -exponent);
    return base * power(base, exponent - 1);
}

int main(void)
{
    double base;
    int exponent;

    printf("Enter base and exponent: ");
    scanf("%lf %d", &base, &exponent);

    printf("%.2f ^ %d = %g\n", base, exponent, power(base, exponent));
    return 0;
}
'''),

    ("Functions & recursion", "Tower of Hanoi", "c", "hanoi.c", r'''#include <stdio.h>

int moves = 0;

void hanoi(int n, char from, char to, char spare)
{
    if (n == 0)
        return;
    hanoi(n - 1, from, spare, to);
    printf("Move disk %d from %c to %c\n", n, from, to);
    moves++;
    hanoi(n - 1, spare, to, from);
}

int main(void)
{
    int n;

    printf("How many disks (1-10)? ");
    scanf("%d", &n);

    if (n < 1 || n > 10) {
        printf("Please choose 1 to 10 disks.\n");
        return 1;
    }

    hanoi(n, 'A', 'C', 'B');
    printf("\nSolved in %d moves.\n", moves);
    return 0;
}
'''),

    # ---- Arrays and strings ------------------------------------------------
    ("Arrays & strings", "Array average, biggest, smallest", "c", "array_stats.c", r'''#include <stdio.h>

#define MAX 100

int main(void)
{
    int n;
    double a[MAX];

    printf("How many numbers (1-%d)? ", MAX);
    scanf("%d", &n);
    if (n < 1 || n > MAX) {
        printf("Please enter 1 to %d.\n", MAX);
        return 1;
    }

    for (int i = 0; i < n; i++) {
        printf("Number %d: ", i + 1);
        scanf("%lf", &a[i]);
    }

    double total = a[0], big = a[0], small = a[0];
    for (int i = 1; i < n; i++) {
        total += a[i];
        if (a[i] > big)   big = a[i];
        if (a[i] < small) small = a[i];
    }

    printf("\nAverage : %.2f\n", total / n);
    printf("Biggest : %.2f\n", big);
    printf("Smallest: %.2f\n", small);
    return 0;
}
'''),

    ("Arrays & strings", "Sort an array (bubble sort)", "c", "bubble_sort.c", r'''#include <stdio.h>

#define MAX 100

int main(void)
{
    int n, a[MAX];

    printf("How many numbers (1-%d)? ", MAX);
    scanf("%d", &n);
    if (n < 1 || n > MAX) return 1;

    for (int i = 0; i < n; i++) {
        printf("Number %d: ", i + 1);
        scanf("%d", &a[i]);
    }

    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - 1 - i; j++) {
            if (a[j] > a[j + 1]) {
                int temp = a[j];
                a[j] = a[j + 1];
                a[j + 1] = temp;
            }
        }
    }

    printf("\nSorted: ");
    for (int i = 0; i < n; i++)
        printf("%d ", a[i]);
    printf("\n");
    return 0;
}
'''),

    ("Arrays & strings", "Linear search", "c", "linear_search.c", r'''#include <stdio.h>

#define MAX 100

int main(void)
{
    int n, key, a[MAX];

    printf("How many numbers? ");
    scanf("%d", &n);
    if (n < 1 || n > MAX) return 1;

    for (int i = 0; i < n; i++) {
        printf("Number %d: ", i + 1);
        scanf("%d", &a[i]);
    }

    printf("Search for: ");
    scanf("%d", &key);

    int found = -1;
    for (int i = 0; i < n; i++) {
        if (a[i] == key) { found = i; break; }
    }

    if (found >= 0)
        printf("Found %d at position %d.\n", key, found + 1);
    else
        printf("%d is not in the list.\n", key);
    return 0;
}
'''),

    ("Arrays & strings", "Binary search (sorted list)", "c", "binary_search.c", r'''#include <stdio.h>

#define MAX 100

int main(void)
{
    int n, key, a[MAX];

    printf("How many numbers? ");
    scanf("%d", &n);
    if (n < 1 || n > MAX) return 1;

    printf("Enter them in increasing order:\n");
    for (int i = 0; i < n; i++) {
        printf("Number %d: ", i + 1);
        scanf("%d", &a[i]);
    }

    printf("Search for: ");
    scanf("%d", &key);

    int low = 0, high = n - 1, found = -1;
    while (low <= high) {
        int mid = (low + high) / 2;
        if (a[mid] == key)      { found = mid; break; }
        else if (a[mid] < key)  low = mid + 1;
        else                    high = mid - 1;
    }

    if (found >= 0)
        printf("Found %d at position %d.\n", key, found + 1);
    else
        printf("%d is not in the list.\n", key);
    return 0;
}
'''),

    ("Arrays & strings", "Add two matrices", "c", "matrix_add.c", r'''#include <stdio.h>

int main(void)
{
    int rows, cols;

    printf("Rows and columns: ");
    scanf("%d %d", &rows, &cols);
    if (rows < 1 || rows > 10 || cols < 1 || cols > 10) {
        printf("Please use sizes from 1 to 10.\n");
        return 1;
    }

    int a[10][10], b[10][10];

    printf("First matrix:\n");
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            scanf("%d", &a[i][j]);

    printf("Second matrix:\n");
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            scanf("%d", &b[i][j]);

    printf("\nSum:\n");
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++)
            printf("%5d", a[i][j] + b[i][j]);
        printf("\n");
    }
    return 0;
}
'''),

    ("Arrays & strings", "Multiply two matrices", "c", "matrix_multiply.c", r'''#include <stdio.h>

int main(void)
{
    int r1, c1, r2, c2;

    printf("Rows and columns of matrix A: ");
    scanf("%d %d", &r1, &c1);
    printf("Rows and columns of matrix B: ");
    scanf("%d %d", &r2, &c2);

    if (c1 != r2) {
        printf("Cannot multiply: columns of A must equal rows of B.\n");
        return 1;
    }
    if (r1 > 10 || c1 > 10 || c2 > 10) {
        printf("Please use sizes up to 10.\n");
        return 1;
    }

    int a[10][10], b[10][10], result[10][10];

    printf("Matrix A:\n");
    for (int i = 0; i < r1; i++)
        for (int j = 0; j < c1; j++)
            scanf("%d", &a[i][j]);

    printf("Matrix B:\n");
    for (int i = 0; i < r2; i++)
        for (int j = 0; j < c2; j++)
            scanf("%d", &b[i][j]);

    for (int i = 0; i < r1; i++) {
        for (int j = 0; j < c2; j++) {
            result[i][j] = 0;
            for (int k = 0; k < c1; k++)
                result[i][j] += a[i][k] * b[k][j];
        }
    }

    printf("\nA x B:\n");
    for (int i = 0; i < r1; i++) {
        for (int j = 0; j < c2; j++)
            printf("%6d", result[i][j]);
        printf("\n");
    }
    return 0;
}
'''),

    ("Arrays & strings", "Transpose of a matrix", "c", "matrix_transpose.c", r'''#include <stdio.h>

int main(void)
{
    int rows, cols, a[10][10];

    printf("Rows and columns (max 10): ");
    scanf("%d %d", &rows, &cols);
    if (rows < 1 || rows > 10 || cols < 1 || cols > 10) return 1;

    printf("Enter the numbers:\n");
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            scanf("%d", &a[i][j]);

    printf("\nTranspose:\n");
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++)
            printf("%5d", a[i][j]);
        printf("\n");
    }
    return 0;
}
'''),

    ("Arrays & strings", "String length and reverse", "c", "string_reverse.c", r'''#include <stdio.h>
#include <string.h>

int main(void)
{
    char text[100];

    printf("Enter a word or sentence: ");
    if (fgets(text, sizeof text, stdin) == NULL)
        return 1;
    text[strcspn(text, "\n")] = '\0';     /* remove the Enter key */

    size_t length = strlen(text);
    printf("Length: %zu\n", length);

    printf("Reversed: ");
    for (size_t i = length; i > 0; i--)
        putchar(text[i - 1]);
    printf("\n");
    return 0;
}
'''),

    ("Arrays & strings", "Palindrome word check", "c", "palindrome_word.c", r'''#include <stdio.h>
#include <string.h>
#include <ctype.h>

int main(void)
{
    char text[100];

    printf("Enter a word: ");
    if (fgets(text, sizeof text, stdin) == NULL)
        return 1;
    text[strcspn(text, "\n")] = '\0';

    int left = 0, right = (int) strlen(text) - 1, ok = 1;
    while (left < right) {
        if (tolower((unsigned char) text[left]) != tolower((unsigned char) text[right])) {
            ok = 0;
            break;
        }
        left++;
        right--;
    }

    printf("\"%s\" is %sa palindrome.\n", text, ok ? "" : "not ");
    return 0;
}
'''),

    ("Arrays & strings", "Count vowels, letters and words", "c", "count_letters.c", r'''#include <stdio.h>
#include <ctype.h>
#include <string.h>

int main(void)
{
    char text[200];

    printf("Enter a sentence: ");
    if (fgets(text, sizeof text, stdin) == NULL)
        return 1;
    text[strcspn(text, "\n")] = '\0';

    int vowels = 0, letters = 0, digits = 0, words = 0, in_word = 0;
    for (int i = 0; text[i] != '\0'; i++) {
        unsigned char ch = (unsigned char) text[i];
        if (isalpha(ch)) {
            letters++;
            char low = (char) tolower(ch);
            if (strchr("aeiou", low))
                vowels++;
        } else if (isdigit(ch)) {
            digits++;
        }

        if (isspace(ch)) {
            in_word = 0;
        } else if (!in_word) {
            in_word = 1;
            words++;
        }
    }

    printf("Words   : %d\n", words);
    printf("Letters : %d\n", letters);
    printf("Vowels  : %d\n", vowels);
    printf("Digits  : %d\n", digits);
    return 0;
}
'''),

    ("Arrays & strings", "Copy, join and compare strings", "c", "string_functions.c", r'''#include <stdio.h>
#include <string.h>

int main(void)
{
    char first[50], second[50], joined[110];

    printf("First word : ");
    scanf("%49s", first);
    printf("Second word: ");
    scanf("%49s", second);

    strcpy(joined, first);
    strcat(joined, " ");
    strcat(joined, second);

    printf("\nJoined  : %s\n", joined);
    printf("Lengths : %zu and %zu\n", strlen(first), strlen(second));

    int cmp = strcmp(first, second);
    if (cmp == 0)
        printf("The words are the same.\n");
    else if (cmp < 0)
        printf("\"%s\" comes first in the dictionary.\n", first);
    else
        printf("\"%s\" comes first in the dictionary.\n", second);
    return 0;
}
'''),

    # ---- Pointers and structures -------------------------------------------
    ("Pointers & structures", "Pointer basics", "c", "pointer_intro.c", r'''#include <stdio.h>

int main(void)
{
    int value = 42;
    int *pointer = &value;      /* pointer holds the ADDRESS of value */

    printf("value          = %d\n", value);
    printf("&value         = %p\n", (void *) &value);
    printf("pointer        = %p\n", (void *) pointer);
    printf("*pointer       = %d\n", *pointer);

    *pointer = 99;              /* changing through the pointer */
    printf("value is now   = %d\n", value);
    return 0;
}
'''),

    ("Pointers & structures", "Swap using pointers", "c", "pointer_swap.c", r'''#include <stdio.h>

void swap(int *x, int *y)
{
    int temp = *x;
    *x = *y;
    *y = temp;
}

int main(void)
{
    int a, b;

    printf("Enter two numbers: ");
    scanf("%d %d", &a, &b);

    swap(&a, &b);               /* pass the addresses */
    printf("After swapping: a = %d, b = %d\n", a, b);
    return 0;
}
'''),

    ("Pointers & structures", "Array sum using a pointer", "c", "pointer_array.c", r'''#include <stdio.h>

int sum_array(const int *a, int n)
{
    int total = 0;
    for (int i = 0; i < n; i++)
        total += *(a + i);      /* same as a[i] */
    return total;
}

int main(void)
{
    int numbers[] = {5, 10, 15, 20, 25};
    int count = (int) (sizeof numbers / sizeof numbers[0]);

    for (int i = 0; i < count; i++)
        printf("numbers[%d] = %d\n", i, numbers[i]);

    printf("Total = %d\n", sum_array(numbers, count));
    return 0;
}
'''),

    ("Pointers & structures", "Dynamic memory (malloc)", "c", "dynamic_array.c", r'''#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    int n;

    printf("How many numbers? ");
    scanf("%d", &n);
    if (n < 1) return 1;

    int *a = malloc((size_t) n * sizeof *a);
    if (a == NULL) {
        printf("Out of memory.\n");
        return 1;
    }

    for (int i = 0; i < n; i++) {
        printf("Number %d: ", i + 1);
        scanf("%d", &a[i]);
    }

    long total = 0;
    for (int i = 0; i < n; i++)
        total += a[i];

    printf("Sum = %ld,  average = %.2f\n", total, (double) total / n);

    free(a);                    /* always give memory back */
    return 0;
}
'''),

    ("Pointers & structures", "Structure: one student", "c", "struct_student.c", r'''#include <stdio.h>

struct Student {
    char name[50];
    int  roll;
    float marks;
};

int main(void)
{
    struct Student s;

    printf("Name : ");
    scanf("%49s", s.name);
    printf("Roll : ");
    scanf("%d", &s.roll);
    printf("Marks: ");
    scanf("%f", &s.marks);

    printf("\n%-20s %-6s %s\n", "NAME", "ROLL", "MARKS");
    printf("%-20s %-6d %.2f\n", s.name, s.roll, s.marks);
    return 0;
}
'''),

    ("Pointers & structures", "Array of structures", "c", "struct_array.c", r'''#include <stdio.h>

#define MAX 50

struct Student {
    char name[30];
    int  roll;
    float marks;
};

int main(void)
{
    struct Student list[MAX];
    int n;

    printf("How many students (1-%d)? ", MAX);
    scanf("%d", &n);
    if (n < 1 || n > MAX) return 1;

    for (int i = 0; i < n; i++) {
        printf("\nStudent %d\n", i + 1);
        printf("  Name : ");
        scanf("%29s", list[i].name);
        printf("  Roll : ");
        scanf("%d", &list[i].roll);
        printf("  Marks: ");
        scanf("%f", &list[i].marks);
    }

    int top = 0;
    float total = 0;
    for (int i = 0; i < n; i++) {
        total += list[i].marks;
        if (list[i].marks > list[top].marks)
            top = i;
    }

    printf("\n%-20s %-6s %s\n", "NAME", "ROLL", "MARKS");
    for (int i = 0; i < n; i++)
        printf("%-20s %-6d %.2f\n", list[i].name, list[i].roll, list[i].marks);

    printf("\nClass average: %.2f\n", total / n);
    printf("Top student  : %s (%.2f)\n", list[top].name, list[top].marks);
    return 0;
}
'''),

    ("Pointers & structures", "Structure passed to a function", "c", "struct_function.c", r'''#include <stdio.h>

struct Rectangle {
    double width;
    double height;
};

double area(struct Rectangle r)
{
    return r.width * r.height;
}

void grow(struct Rectangle *r, double factor)
{
    r->width  *= factor;        /* -> is used with a pointer */
    r->height *= factor;
}

int main(void)
{
    struct Rectangle box = {3.0, 4.0};

    printf("Area now      : %.2f\n", area(box));
    grow(&box, 2.0);
    printf("After growing : %.2f x %.2f, area %.2f\n", box.width, box.height, area(box));
    return 0;
}
'''),

    # ---- Files -------------------------------------------------------------
    ("Files", "Write text to a file", "c", "file_write.c", r'''#include <stdio.h>

int main(void)
{
    FILE *fp = fopen("notes.txt", "w");
    if (fp == NULL) {
        printf("Could not create the file.\n");
        return 1;
    }

    fprintf(fp, "CodeLab Studio\n");
    fprintf(fp, "Line two of my file.\n");
    for (int i = 1; i <= 5; i++)
        fprintf(fp, "Line %d\n", i + 2);

    fclose(fp);
    printf("Saved notes.txt next to your program.\n");
    return 0;
}
'''),

    ("Files", "Read a file line by line", "c", "file_read.c", r'''#include <stdio.h>

int main(void)
{
    FILE *fp = fopen("notes.txt", "r");
    if (fp == NULL) {
        printf("notes.txt not found - run the \"Write text to a file\" example first.\n");
        return 1;
    }

    char line[200];
    int count = 0;
    while (fgets(line, sizeof line, fp) != NULL) {
        printf("%3d | %s", ++count, line);
    }

    fclose(fp);
    printf("\n%d lines read.\n", count);
    return 0;
}
'''),

    ("Files", "Append and count words", "c", "file_append.c", r'''#include <stdio.h>
#include <ctype.h>

int main(void)
{
    FILE *fp = fopen("notes.txt", "a");
    if (fp == NULL) {
        printf("Could not open notes.txt for writing.\n");
        return 1;
    }
    fprintf(fp, "Added by the append example.\n");
    fclose(fp);

    fp = fopen("notes.txt", "r");
    if (fp == NULL) {
        printf("Could not read notes.txt.\n");
        return 1;
    }

    int words = 0, in_word = 0, ch;
    while ((ch = fgetc(fp)) != EOF) {
        if (isspace(ch))
            in_word = 0;
        else if (!in_word) {
            in_word = 1;
            words++;
        }
    }
    fclose(fp);

    printf("notes.txt now has %d words.\n", words);
    return 0;
}
'''),

    # ---- Games and fun -----------------------------------------------------
    ("Games & fun", "Guess the number", "c", "guess_game.c", r'''#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(void)
{
    srand((unsigned) time(NULL));
    int secret = rand() % 100 + 1;
    int guess, tries = 0;

    printf("I am thinking of a number from 1 to 100.\n");

    do {
        printf("Your guess: ");
        if (scanf("%d", &guess) != 1)
            return 1;
        tries++;

        if (guess > secret)
            printf("  Too high!\n");
        else if (guess < secret)
            printf("  Too low!\n");
    } while (guess != secret);

    printf("\nCorrect! You found %d in %d tries.\n", secret, tries);
    return 0;
}
'''),

    ("Games & fun", "Roll two dice", "c", "dice.c", r'''#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(void)
{
    srand((unsigned) time(NULL));
    int rolls;

    printf("How many rolls? ");
    scanf("%d", &rolls);

    int counts[13] = {0};
    for (int i = 0; i < rolls; i++) {
        int total = rand() % 6 + 1 + rand() % 6 + 1;
        counts[total]++;
    }

    printf("\nTotal  Times  Chart\n");
    for (int total = 2; total <= 12; total++) {
        printf("%5d %6d  ", total, counts[total]);
        for (int star = 0; star < counts[total] * 40 / (rolls > 0 ? rolls : 1); star++)
            printf("#");
        printf("\n");
    }
    return 0;
}
'''),

    ("Games & fun", "Rock, paper, scissors", "c", "rock_paper_scissors.c", r'''#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(void)
{
    const char *names[] = {"rock", "paper", "scissors"};
    srand((unsigned) time(NULL));

    int rounds, you_win = 0, computer_wins = 0;
    printf("How many rounds? ");
    scanf("%d", &rounds);

    for (int i = 1; i <= rounds; i++) {
        int you;
        printf("\nRound %d - 0 rock, 1 paper, 2 scissors: ", i);
        if (scanf("%d", &you) != 1 || you < 0 || you > 2) {
            printf("Please type 0, 1 or 2.\n");
            return 1;
        }

        int computer = rand() % 3;
        printf("  You: %-8s  Computer: %s\n", names[you], names[computer]);

        if (you == computer)
            printf("  Draw.\n");
        else if ((you + 1) % 3 == computer) {
            printf("  Computer wins.\n");
            computer_wins++;
        } else {
            printf("  You win!\n");
            you_win++;
        }
    }

    printf("\nFinal score - you %d, computer %d\n", you_win, computer_wins);
    return 0;
}
'''),

    ("Games & fun", "Times-table quiz", "c", "quiz.c", r'''#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(void)
{
    srand((unsigned) time(NULL));
    int questions, score = 0;

    printf("How many questions? ");
    scanf("%d", &questions);

    for (int i = 1; i <= questions; i++) {
        int a = rand() % 12 + 1;
        int b = rand() % 12 + 1;
        int answer;

        printf("Q%d:  %d x %d = ", i, a, b);
        if (scanf("%d", &answer) != 1)
            return 1;

        if (answer == a * b) {
            printf("  Correct!\n");
            score++;
        } else {
            printf("  No - the answer is %d.\n", a * b);
        }
    }

    printf("\nYou scored %d out of %d.\n", score, questions);
    return 0;
}
'''),

    ("Games & fun", "Menu-driven bank account", "c", "bank_menu.c", r'''#include <stdio.h>

int main(void)
{
    double balance = 0;
    int choice;

    do {
        printf("\n===== MY BANK =====\n");
        printf("1. Deposit\n");
        printf("2. Withdraw\n");
        printf("3. Show balance\n");
        printf("4. Quit\n");
        printf("Choose: ");
        if (scanf("%d", &choice) != 1)
            return 1;

        double amount;
        switch (choice) {
            case 1:
                printf("Amount to deposit: ");
                scanf("%lf", &amount);
                if (amount <= 0)
                    printf("Enter a positive amount.\n");
                else {
                    balance += amount;
                    printf("Deposited Rs %.2f\n", amount);
                }
                break;
            case 2:
                printf("Amount to withdraw: ");
                scanf("%lf", &amount);
                if (amount <= 0)
                    printf("Enter a positive amount.\n");
                else if (amount > balance)
                    printf("Not enough money. Balance is Rs %.2f\n", balance);
                else {
                    balance -= amount;
                    printf("Took out Rs %.2f\n", amount);
                }
                break;
            case 3:
                printf("Balance: Rs %.2f\n", balance);
                break;
            case 4:
                printf("Goodbye!\n");
                break;
            default:
                printf("Choose 1 to 4.\n");
        }
    } while (choice != 4);

    return 0;
}
'''),

    # ---- C++ basics --------------------------------------------------------
    ("C++ basics", "Hello World", "cpp", "hello.cpp", r'''#include <iostream>
using namespace std;

int main()
{
    cout << "Hello, World!" << endl;
    return 0;
}
'''),

    ("C++ basics", "Input and output with cin", "cpp", "cin_cout.cpp", r'''#include <iostream>
#include <string>
using namespace std;

int main()
{
    string name;
    int age;

    cout << "Your name: ";
    getline(cin, name);
    cout << "Your age : ";
    cin >> age;

    cout << "\nHello " << name << "!" << endl;
    cout << "Next year you will be " << age + 1 << "." << endl;
    return 0;
}
'''),

    ("C++ basics", "Multiplication table", "cpp", "table.cpp", r'''#include <iostream>
#include <iomanip>
using namespace std;

int main()
{
    int n;

    cout << "Table of which number? ";
    cin >> n;

    for (int i = 1; i <= 10; i++)
        cout << setw(3) << n << " x " << setw(2) << i << " = " << setw(4) << n * i << endl;
    return 0;
}
'''),

    ("C++ basics", "Marks average with a vector", "cpp", "marks.cpp", r'''#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

int main()
{
    int count;

    cout << "How many students? ";
    cin >> count;
    if (count < 1) return 1;

    vector<double> marks(count);
    for (int i = 0; i < count; i++) {
        cout << "Marks of student " << i + 1 << ": ";
        cin >> marks[i];
    }

    double total = 0;
    for (double m : marks)
        total += m;

    cout << "Average : " << total / count << endl;
    cout << "Highest : " << *max_element(marks.begin(), marks.end()) << endl;
    cout << "Lowest  : " << *min_element(marks.begin(), marks.end()) << endl;
    return 0;
}
'''),

    ("C++ basics", "Number pyramid", "cpp", "pyramid.cpp", r'''#include <iostream>
#include <iomanip>
using namespace std;

int main()
{
    int rows;

    cout << "How many rows? ";
    cin >> rows;

    for (int i = 1; i <= rows; i++) {
        cout << setw(rows - i + 1) << "";
        for (int j = 1; j <= i; j++)
            cout << j << " ";
        cout << endl;
    }
    return 0;
}
'''),

    # ---- C++ classes and objects -------------------------------------------
    ("C++ classes & objects", "Your first class", "cpp", "class_intro.cpp", r'''#include <iostream>
#include <string>
using namespace std;

class Dog {
public:
    string name;
    int age;

    void speak() const
    {
        cout << name << " says: Woof!" << endl;
    }
};

int main()
{
    Dog d;
    d.name = "Kalu";
    d.age = 3;

    d.speak();
    cout << d.name << " is " << d.age << " years old." << endl;
    return 0;
}
'''),

    ("C++ classes & objects", "Student class with grade", "cpp", "student.cpp", r'''#include <iostream>
#include <string>
using namespace std;

class Student {
public:
    string name;
    int roll;
    double marks;

    string grade() const
    {
        if (marks >= 90) return "A+";
        if (marks >= 80) return "A";
        if (marks >= 70) return "B+";
        if (marks >= 60) return "B";
        if (marks >= 50) return "C+";
        if (marks >= 40) return "C";
        return "NG";
    }
};

int main()
{
    Student s;

    cout << "Name: ";
    getline(cin, s.name);
    cout << "Roll: ";
    cin >> s.roll;
    cout << "Marks: ";
    cin >> s.marks;

    cout << "\n" << s.name << " (roll " << s.roll << ") got grade " << s.grade() << endl;
    return 0;
}
'''),

    ("C++ classes & objects", "Constructor and private data", "cpp", "constructor.cpp", r'''#include <iostream>
#include <string>
using namespace std;

class BankAccount {
private:
    string owner;
    double balance;             // private: only this class can touch it

public:
    BankAccount(string name, double opening)   // constructor
        : owner(name), balance(opening) {}

    void deposit(double amount)
    {
        if (amount > 0)
            balance += amount;
    }

    bool withdraw(double amount)
    {
        if (amount <= 0 || amount > balance)
            return false;
        balance -= amount;
        return true;
    }

    void show() const
    {
        cout << owner << ": Rs " << balance << endl;
    }
};

int main()
{
    BankAccount account("Sita", 500);

    account.deposit(250);
    account.show();

    if (!account.withdraw(1000))
        cout << "Withdrawal refused - not enough money." << endl;

    account.withdraw(300);
    account.show();
    return 0;
}
'''),

    ("C++ classes & objects", "Inheritance", "cpp", "inheritance.cpp", r'''#include <iostream>
#include <string>
using namespace std;

class Person {                  // base class
protected:
    string name;
    int age;

public:
    Person(string n, int a) : name(n), age(a) {}

    void show() const
    {
        cout << name << ", age " << age;
    }
};

class Teacher : public Person { // derived class
    string subject;

public:
    Teacher(string n, int a, string s) : Person(n, a), subject(s) {}

    void showAll() const
    {
        show();
        cout << ", teaches " << subject << endl;
    }
};

int main()
{
    Teacher t("Ram Sir", 35, "Computer Science");
    t.showAll();
    return 0;
}
'''),

    ("C++ classes & objects", "Virtual functions (polymorphism)", "cpp", "polymorphism.cpp", r'''#include <iostream>
#include <vector>
#include <memory>
using namespace std;

class Shape {
public:
    virtual double area() const = 0;        // pure virtual
    virtual string name() const = 0;
    virtual ~Shape() = default;
};

class Circle : public Shape {
    double r;
public:
    explicit Circle(double radius) : r(radius) {}
    double area() const override { return 3.14159265 * r * r; }
    string name() const override { return "Circle"; }
};

class Rectangle : public Shape {
    double w, h;
public:
    Rectangle(double width, double height) : w(width), h(height) {}
    double area() const override { return w * h; }
    string name() const override { return "Rectangle"; }
};

int main()
{
    vector<unique_ptr<Shape>> shapes;
    shapes.push_back(make_unique<Circle>(2.0));
    shapes.push_back(make_unique<Rectangle>(3.0, 4.0));
    shapes.push_back(make_unique<Circle>(1.5));

    double total = 0;
    for (const auto &s : shapes) {
        cout << s->name() << " area = " << s->area() << endl;
        total += s->area();
    }
    cout << "Total area = " << total << endl;
    return 0;
}
'''),

    ("C++ classes & objects", "Operator overloading", "cpp", "operator_overload.cpp", r'''#include <iostream>
using namespace std;

class Fraction {
    int numerator, denominator;

    static int gcd(int a, int b) { return b == 0 ? a : gcd(b, a % b); }

public:
    Fraction(int n = 0, int d = 1) : numerator(n), denominator(d)
    {
        if (denominator == 0) denominator = 1;
        simplify();
    }

    void simplify()
    {
        int g = gcd(numerator < 0 ? -numerator : numerator,
                    denominator < 0 ? -denominator : denominator);
        if (g > 1) {
            numerator /= g;
            denominator /= g;
        }
    }

    Fraction operator+(const Fraction &other) const
    {
        return Fraction(numerator * other.denominator + other.numerator * denominator,
                        denominator * other.denominator);
    }

    friend ostream &operator<<(ostream &out, const Fraction &f)
    {
        return out << f.numerator << "/" << f.denominator;
    }
};

int main()
{
    Fraction a(1, 2), b(1, 3);
    cout << a << " + " << b << " = " << a + b << endl;
    return 0;
}
'''),

    # ---- C++ STL -----------------------------------------------------------
    ("C++ STL", "Vector: add, show, sort", "cpp", "stl_vector.cpp", r'''#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

int main()
{
    vector<int> numbers;
    int n;

    cout << "How many numbers? ";
    cin >> n;

    for (int i = 0; i < n; i++) {
        int value;
        cout << "Number " << i + 1 << ": ";
        cin >> value;
        numbers.push_back(value);
    }

    sort(numbers.begin(), numbers.end());

    cout << "\nSorted: ";
    for (int value : numbers)
        cout << value << " ";
    cout << "\nSize: " << numbers.size() << endl;
    return 0;
}
'''),

    ("C++ STL", "Map: count words", "cpp", "stl_map.cpp", r'''#include <iostream>
#include <map>
#include <sstream>
#include <string>
using namespace std;

int main()
{
    cout << "Type a sentence: ";
    string line;
    getline(cin, line);

    map<string, int> counts;
    istringstream words(line);
    string word;
    while (words >> word)
        counts[word]++;

    cout << "\nWord counts (alphabetical):\n";
    for (const auto &pair : counts)
        cout << "  " << pair.first << " : " << pair.second << endl;
    return 0;
}
'''),

    ("C++ STL", "Set: remove duplicates", "cpp", "stl_set.cpp", r'''#include <iostream>
#include <set>
using namespace std;

int main()
{
    int n;
    cout << "How many numbers? ";
    cin >> n;

    set<int> unique_numbers;        // a set keeps each value only once, in order
    for (int i = 0; i < n; i++) {
        int value;
        cout << "Number " << i + 1 << ": ";
        cin >> value;
        unique_numbers.insert(value);
    }

    cout << "\nDifferent values: ";
    for (int value : unique_numbers)
        cout << value << " ";
    cout << "\nYou typed " << n << " numbers, " << unique_numbers.size() << " were different." << endl;
    return 0;
}
'''),

    ("C++ STL", "Stack: reverse a word", "cpp", "stl_stack.cpp", r'''#include <iostream>
#include <stack>
#include <string>
using namespace std;

int main()
{
    cout << "Enter a word: ";
    string word;
    cin >> word;

    stack<char> letters;            // last in, first out
    for (char ch : word)
        letters.push(ch);

    cout << "Reversed: ";
    while (!letters.empty()) {
        cout << letters.top();
        letters.pop();
    }
    cout << endl;
    return 0;
}
'''),

    ("C++ STL", "Queue: a simple line", "cpp", "stl_queue.cpp", r'''#include <iostream>
#include <queue>
#include <string>
using namespace std;

int main()
{
    queue<string> line;             // first in, first out

    line.push("Anita");
    line.push("Bishal");
    line.push("Chirag");

    cout << "People waiting: " << line.size() << endl;

    while (!line.empty()) {
        cout << "Now serving: " << line.front() << endl;
        line.pop();
    }
    cout << "The line is empty." << endl;
    return 0;
}
'''),

    ("C++ STL", "Sort students by marks", "cpp", "stl_sort_struct.cpp", r'''#include <iostream>
#include <vector>
#include <algorithm>
#include <string>
#include <iomanip>
using namespace std;

struct Student {
    string name;
    double marks;
};

int main()
{
    int n;
    cout << "How many students? ";
    cin >> n;

    vector<Student> list(n);
    for (int i = 0; i < n; i++) {
        cout << "Name and marks of student " << i + 1 << ": ";
        cin >> list[i].name >> list[i].marks;
    }

    sort(list.begin(), list.end(),
         [](const Student &a, const Student &b) { return a.marks > b.marks; });

    cout << "\nRank  Name                 Marks\n";
    for (int i = 0; i < n; i++)
        cout << setw(4) << i + 1 << "  " << setw(20) << left << list[i].name
             << right << setw(6) << list[i].marks << endl;
    return 0;
}
'''),
]

# Menu / browser order. Any category not listed here is appended at the end.
CATEGORY_ORDER = [
    "Getting started",
    "Decisions",
    "Loops & patterns",
    "Functions & recursion",
    "Arrays & strings",
    "Pointers & structures",
    "Files",
    "Games & fun",
    "C++ basics",
    "C++ classes & objects",
    "C++ STL",
]


def categories():
    """Category names in teaching order, only those that actually have programs."""
    present = []
    for _cat, *_rest in EXAMPLES:
        if _cat not in present:
            present.append(_cat)
    ordered = [c for c in CATEGORY_ORDER if c in present]
    return ordered + [c for c in present if c not in ordered]


def by_category(name):
    return [e for e in EXAMPLES if e[0] == name]
