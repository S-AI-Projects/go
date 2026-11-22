# Instructions

Given a name and a number, your task is to produce a sentence using that name and that number as an [ordinal numeral][ordinal-numeral].
Yaʻqūb expects to use numbers from 1 up to 999.

Rules:

- Numbers ending in 1 (unless ending in 11) → `"st"`
- Numbers ending in 2 (unless ending in 12) → `"nd"`
- Numbers ending in 3 (unless ending in 13) → `"rd"`
- All other numbers → `"th"`

Examples:

- `"Mary", 1` → `"Mary, you are the 1st customer we serve today. Thank you!"`
- `"John", 12` → `"John, you are the 12th customer we serve today. Thank you!"`
- `"Dahir", 162` → `"Dahir, you are the 162nd customer we serve today. Thank you!"`

[ordinal-numeral]: https://en.wikipedia.org/wiki/Ordinal_numeral

## Metadata & Runner Explanation

The `line-up` exercise metadata lives in `exercises/practice/line-up/.meta/config.json`. It defines a **files** object that lists the relative paths for the solution, test suite, and the reference implementation (example). All paths must be confined to the `line-up` directory and must not contain parent‑traversal components (`..`). The verifier checks these constraints before copying the exercise to a temporary sandbox.

When the runner executes the tests it follows these steps:
1. Reads `config.json` and resolves the `test` entries (`line_up_test.go` and `cases_test.go`).
2. Generates the test harness from `.meta/tests.toml`, producing `cases_test.go`.
3. Takes the reference implementation from `.meta/example.go` and temporarily overwrites the learner’s solution file.
4. Copies the whole exercise to a temporary directory, runs `go test -count=1 ./...` and verifies that:
   - the process exits with status 0,
   - at least one test reports `ok`,
   - the learner’s original source file hash is unchanged before and after the temporary run.
5. The script also builds a **decision table** that maps each exercised input condition (description recreation, reimplements recreation, other key‑value preservation) to the expected outcome, and asserts that the reference implementation satisfies those expectations.

The verification script `work/R63-T030/check.py` implements all of the above.
