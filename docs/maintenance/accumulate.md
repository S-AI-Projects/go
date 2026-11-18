# Accumulate Exercise Maintenance & Isolated Runner

## Overview
This document details the isolated runner workflow for the `accumulate` exercise (`exercises/practice/accumulate`). The runner allows maintainers and automated grading pipelines to verify the maintained reference implementation without altering the learner's unsolved starter files or dirtying the git working tree.

## Tool Requirements
- **Go:** Go matching `go.mod` (Go 1.18 or newer, standard `go test` tooling).
- **Python:** Python 3 (standard library modules only: `hashlib`, `json`, `pathlib`, `shutil`, `subprocess`, `tempfile`). No third-party packages required.

## Maintenance Workflow

When evaluating candidate reference implementations or validating track changes, direct modifications to `exercises/practice/accumulate/accumulate.go` in the repository tree must be avoided so that student stubs remain untouched.

The runner accomplishes this through:
1. **Pre-Run Hashing:** Computes SHA-256 hashes of all files in `exercises/practice/accumulate/` before any execution.
2. **Temporary Scratch Isolation:** Copies the exercise tree into a secure temporary directory managed by `tempfile.TemporaryDirectory`.
3. **Reference Substitution:** Resolves `files.solution` and `files.example` from `.meta/config.json` and copies the reference into the temporary copy only.
4. **Test Execution:** Executes `go test -v -count=1 ./...` within the isolated directory.
5. **Clean Teardown:** Completely removes the temporary scratch space upon completion.
6. **Post-Run Integrity Verification:** Re-computes SHA-256 hashes to guarantee that no repository files were modified or left in a dirty state.
7. **Failure Propagation:** Propagates any test failure exit code and detects zero-test execution runs.

## Running the Verification

To run the isolated reference test:

```bash
python3 tools/course_checks/r63-t039.py
```

To run the full suite of runner tests (including verification of failing references, zero-test detection, and SHA-256 integrity checks):

```bash
python3 work/R63-T039/check.py
```
