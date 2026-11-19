# Triangle Maintenance and File Role Map (R63-T048)

## Overview

This maintenance guide explains how files in `exercises/practice/triangle` are organized, how the test runner locates and runs them, and how configuration paths are verified.

## File Role Map

| File Path | Role | Description | Maintained or Generated |
| :--- | :--- | :--- | :--- |
| `exercises/practice/triangle/triangle.go` | Solution Stub | Initial starter file with KindFromSides returning a blank Kind. Kept unsolved for students. | Maintained |
| `exercises/practice/triangle/triangle_test.go` | Test Suite | Unit tests verifying equilateral, isosceles, scalene, and invalid triangle cases. | Maintained |
| `exercises/practice/triangle/.meta/example.go` | Reference Solution | Reference implementation that passes all unit tests. | Maintained |
| `exercises/practice/triangle/.meta/config.json` | Metadata Configuration | Exercise metadata declaring file categories, blurb, and authors. | Maintained |
| `exercises/practice/triangle/.docs/instructions.md` | Instructions | Student-facing problem instructions. | Maintained |
| `exercises/practice/triangle/go.mod` | Go Module | Go module definition for the exercise. | Maintained |

### Distinction from Generated Exercises

Unlike exercises that synchronize with `problem-specifications` using a `gen.go` generator script and `cases_test.go`, the `triangle` exercise is maintained by hand:
- It has no `gen.go` file.
- It has no auto-generated `cases_test.go` file.
- All 20 test cases and benchmarks are maintained directly in `triangle_test.go`.

## Runner Resolution Workflow

The Exercism test runner resolves files using `exercises/practice/triangle/.meta/config.json`:
1. It reads the `files` object:
   - `files.solution`: `["triangle.go"]`
   - `files.test`: `["triangle_test.go"]`
   - `files.example`: `[".meta/example.go"]`
2. For student submissions, the runner combines `files.solution` and `files.test` to execute `go test .`.
3. In maintenance and track validation checks, the reference file `files.example[0]` (`.meta/example.go`) replaces `triangle.go` in an isolated scratch copy, and `go test -count=1 ./...` is run to verify that all 20 test cases pass.

## Reproducible Validation Commands

To validate that all files in `config.json` exist securely without path traversal:
```bash
python3 tools/course_checks/r63-t048.py
```

To run the complete check suite including invalid fixture assertions and test execution:
```bash
python3 work/R63-T048/check.py
```
