# Clock: Isolated Reference Runner & Maintenance Guide

## Overview
The `clock` exercise requires implementing time-of-day clock calculations (without dates) supporting addition, subtraction, equality, and formatted string output.

To maintain the exercise and verify reference implementation changes without mutating the learner solution starter files (`clock.go`), an isolated runner is implemented in `tools/course_checks/r63-t009.py`.

---

## Tool Requirements
- **Go toolchain**: Go matching `go.mod` (Go 1.21 or higher).
- **Python**: Python 3.10+ standard library (`hashlib`, `shutil`, `subprocess`, `tempfile`, `pathlib`).

---

## Runner Operation & Invariants
1. **Isolated Copy**: The runner creates a fresh ephemeral directory via `tempfile.TemporaryDirectory()`, copies all exercise files (including `.meta/` and `.docs/`), and copies the reference file (`.meta/example.go`) over the solution path (`clock.go`) strictly within the isolated directory.
2. **Failure Propagation & Reporting**:
   - Executes `go test -count=1 -v ./...`.
   - Counts individual passing subtests (`--- PASS:`).
   - If tests fail, propagates the non-zero exit code and stderr.
   - Rejects zero-test runs by failing if case count is 0.
3. **Learner File Immutability**:
   - Computes SHA-256 hashes of all learner files (`clock.go`) before any test execution.
   - Recomputes and asserts identical hashes after the run, ensuring no in-place modification or accidental solution leak occurs, even under test failure or interruption.

---

## Commands

### Normal Verification Run:
```bash
python3 tools/course_checks/r63-t009.py
```

### Full Course Verification Suite:
```bash
python3 work/R63-T009/check.py
```
This tests real reference success, deliberate mutant failure, empty test set handling, and learner hash immutability.
