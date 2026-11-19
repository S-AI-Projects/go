# Test Report for R63-T043 (reverse string)

## Overview

This report shows the verification results for Task 3 (R63-T043) on exercises/practice/reverse-string.
The goal of this task is to create a deliberate mutant (reversing bytes instead of runes),
verify that canonical test case 1bed0f8a-13b0-4bd3-9d59-3d0593326fa2 rejects it,
add hints and maintenance docs, and make sure the learner stub stays untouched.

## Tool Versions

- Go: go version go1.27.3 darwin/arm64
- Python: 3.9.6 (default, Aug 25 2026, 21:26:21)  [Clang 21.0.0 (clang-2100.3.34.2)]

## Learner Stub Check

File: exercises/practice/reverse-string/reverse_string.go
Status: Untouched and unsolved
The file contains the panic call and has not been implemented.

## Reference Solution Run

The exercise was tested in a temporary directory using the reference solution (.meta/example.go).
Command: go test -count=1 -v ./...
Result: PASS (exit code 0)
Passed test count: 11

Passed tests:
- --- PASS: TestReverse (0.00s)
- --- PASS: TestReverse/an_empty_string (0.00s)
- --- PASS: TestReverse/a_word (0.00s)
- --- PASS: TestReverse/a_capitalized_word (0.00s)
- --- PASS: TestReverse/a_sentence_with_punctuation (0.00s)
- --- PASS: TestReverse/a_palindrome (0.00s)
- --- PASS: TestReverse/an_even-sized_word (0.00s)
- --- PASS: TestReverse/wide_characters (0.00s)
- --- PASS: TestReverseMultibyte (0.00s)
- --- PASS: TestReverseMultibyte/a_multi-byte_test_case (0.00s)
- --- PASS: TestReverseOfReverse (0.00s)

## Deliberate Mutant Run

A mutant that reverses raw bytes ([]byte) instead of runes ([]rune) was tested in a temporary directory.
Command: go test -count=1 -v ./...
Result: FAIL (exit code 1) as expected

Rejecting test case:
- UUID: 1bed0f8a-13b0-4bd3-9d59-3d0593326fa2
- Description: "wide characters"
- Input: "子猫"
- Expected: "猫子"

Failure output from test run:
```
=== RUN   TestReverse
=== RUN   TestReverse/an_empty_string
=== RUN   TestReverse/a_word
=== RUN   TestReverse/a_capitalized_word
=== RUN   TestReverse/a_sentence_with_punctuation
=== RUN   TestReverse/a_palindrome
=== RUN   TestReverse/an_even-sized_word
=== RUN   TestReverse/wide_characters
    reverse_string_test.go:12: Reverse("子猫") = "\xab\x8c琭\xe5", want: "猫子"
--- FAIL: TestReverse (0.00s)
    --- PASS: TestReverse/an_empty_string (0.00s)
    --- PASS: TestReverse/a_word (0.00s)
    --- PASS: TestReverse/a_capitalized_word (0.00s)
    --- PASS: TestReverse/a_sentence_with_punctuation (0.00s)
    --- PASS: TestReverse/a_palindrome (0.00s)
    --- PASS: TestReverse/an_even-sized_word (0.00s)
    --- FAIL: TestReverse/wide_characters (0.00s)
=== RUN   TestReverseMultibyte
=== RUN   TestReverseMultibyte/a_multi-byte_test_case
    reverse_string_test.go:22: Reverse("Hello, 世界") = "\x8c\x95疸\xe4 ,olleH", want: "界世 ,olleH"
--- FAIL: TestReverseMultibyte (0.00s)
    --- FAIL: TestReverseMultibyte/a_multi-byte_test_case (0.00s)
=== RUN   TestReverseOfReverse
--- PASS: TestReverseOfReverse (0.00s)
FAIL
FAIL	reversestring	0.365s
FAIL
```

## Documentation and Comments Check

- tests.toml: UUID 1bed0f8a-13b0-4bd3-9d59-3d0593326fa2 has a comment explaining multi byte verification and rejection of byte level reversal mutants.
- hints.md: Created exercises/practice/reverse-string/.docs/hints.md with beginner friendly advice about runes and bytes.
- maintenance doc: Created docs/maintenance/reverse-string.md documenting the mutant, rejecting test case, expected behavior, and reduced input.

## Conclusion

All checks for R63-T043 passed cleanly.
