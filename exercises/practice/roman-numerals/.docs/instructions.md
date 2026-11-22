# Introduction

Your task is to convert a number from Arabic numerals to Roman numerals.

For this exercise, we are only concerned about traditional Roman numerals, in which the largest number is MMMCMXCIX (or 3,999).

~~~~exercism/note
There are lots of different ways to convert between Arabic and Roman numerals.
We recommend taking a naive approach first to familiarise yourself with the concept of Roman numerals and then search for more efficient methods.

Make sure to check out our Deep Dive video at the end to explore the different approaches you can take!
~~~~

## Metadata & Runner Explanation

The `roman-numerals` exercise metadata lives in `exercises/practice/roman-numerals/.meta/config.json`. It defines a **files** object with relative paths for the solution, test suite, and reference implementation (example). All paths must be confined to the exercise directory and must not contain parent‑directory components (`..`). The verifier validates these constraints before copying the exercise to a temporary sandbox.

When the runner executes the tests it follows these steps:
1. Reads `config.json` and resolves the `test` entries (`roman_numerals_test.go` and `cases_test.go`).
2. Generates the test harness from `.meta/tests.toml`, producing `cases_test.go`.
3. Takes the reference implementation from `.meta/example.go` and temporarily overwrites the learner’s solution file.
4. Copies the whole exercise to a temporary directory, runs `go test -count=1 ./...` and checks that:
   - the process exits with status 0,
   - at least one test reports `ok`,
   - the learner’s original files remain unchanged (hashes before/after are identical).
5. The script also exercises three failure scenarios (broken reference, missing test entries, and an empty test list) to confirm the validator correctly reports errors.

The verification script `work/R63-T029/check.py` implements all of the above.
