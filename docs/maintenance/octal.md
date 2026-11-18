# Octal Exercise Maintenance & File Map

## Overview
This document defines the file-role map for the `octal` practice exercise (`exercises/practice/octal`), explains how test runners locate and execute files, and provides reproducible path validation commands.

## File-Role Map

| File Path | Role | Description | Maintained / Generated |
| :--- | :--- | :--- | :--- |
| `exercises/practice/octal/octal.go` | Solution Stub | Initial learner stub containing the function signature and panic statement. Kept unsolved. | Maintained |
| `exercises/practice/octal/octal_test.go` | Test Suite | Unit tests and benchmarks verifying base-8 parsing across valid and invalid inputs. | Maintained |
| `exercises/practice/octal/.meta/example.go` | Reference Implementation | Canonical solution using bitwise operations (`num<<3 + digit`) passing all test cases. | Maintained |
| `exercises/practice/octal/.meta/config.json` | Metadata Configuration | Exercise metadata defining authors, contributors, blurb, and the `files` mapping. | Maintained |
| `exercises/practice/octal/.docs/instructions.md` | Instructions | Student-facing problem description. | Maintained |
| `exercises/practice/octal/go.mod` | Go Module | Defines the `octal` Go module. | Maintained |

### Distinction from Generated Exercises
Unlike many modern Exercism practice exercises that synchronize with `problem-specifications` using `gen.go`, `cases_test.go`, and `.meta/tests.toml`, `octal` is a manual exercise:
- It has **no** `gen.go` generator script.
- It has **no** auto-generated `cases_test.go`.
- It has **no** `.meta/tests.toml` test-tracking file.
- All test cases (valid strings like `"1"`, `"10"`, `"1234567"`, and error cases like `"carrot"`, `"35682"`) are maintained directly within `octal_test.go`.

## Runner Resolution Workflow

The Exercism test runner and track verification scripts resolve files as follows:
1. **Config Lookup:** The runner reads `exercises/practice/octal/.meta/config.json` and parses the `files` object:
   - `files.solution`: `["octal.go"]`
   - `files.test`: `["octal_test.go"]`
   - `files.example`: `[".meta/example.go"]`
2. **Student Submission Evaluation:** When a student submits their solution, the test runner compiles `files.solution` and `files.test` together using `go test .`.
3. **Reference Verification:** In track CI and maintenance checks, the reference file `files.example[0]` (`.meta/example.go`) is copied onto `files.solution[0]` (`octal.go`) in an isolated scratch directory, and `go test -count=1 ./...` is executed. All 5 test cases must pass.

## Reproducible Validation

To verify that all declared files in `.meta/config.json` exist on disk, contain no path traversals, and resolve safely within the exercise root, run:

```bash
python3 tools/course_checks/r63-t038.py
```

To run the complete verification suite including reference execution and invalid fixture assertions:

```bash
python3 work/R63-T038/check.py
```
