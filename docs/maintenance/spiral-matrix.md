# Spiral Matrix: Maintained Files & Metadata Architecture

## Overview
The `spiral-matrix` exercise generates an $n \times n$ square matrix filled with natural numbers $1$ to $n^2$ in spiral clockwise order.

This document describes the maintained file roles, metadata resolution rules in `.meta/config.json`, and how test runners and track tools resolve and distinguish generated versus hand-written artifacts.

---

## File Role Map

| File Path | Role Key in `config.json` | Maintenance Type | Description |
| :--- | :--- | :--- | :--- |
| `spiral_matrix.go` | `files.solution` | Hand-maintained | The unsolved starter file provided to the learner with function stub `SpiralMatrix(size int) [][]int`. |
| `spiral_matrix_test.go` | `files.test` | Hand-maintained | The Go test harness executing test runs (`TestSpiralMatrix`) and benchmarks. |
| `cases_test.go` | `files.test` | **Generated artifact** | Auto-generated test cases parsed from canonical problem specifications using `.meta/gen.go`. |
| `.meta/example.go` | `files.example` | Hand-maintained | The reference solution used by track CI and maintainer verification scripts to validate test suites. |
| `.meta/config.json` | N/A (Config) | Hand-maintained | Authoritative metadata mapping exercise files, authors, and origin sources. |
| `.meta/gen.go` | N/A (Generator) | Hand-maintained | Template generator that syncs canonical data to `cases_test.go`. |
| `.meta/tests.toml` | N/A (Config) | Hand-maintained | Tracks canonical test case inclusions and exclusions. |

---

## Resolution Rules & Path Safety
Track runners and automated tools resolve file paths according to the following strict safety invariants:
1. **Root Anchoring**: All paths declared in `.meta/config.json` under `files` are resolved relative to the exercise directory (`exercises/practice/spiral-matrix`).
2. **Traversal Prevention**: Paths must not contain parent directory traversal components (`..`) or absolute system paths. Any attempt to traverse outside the exercise directory must be rejected.
3. **Existence Verification**: Every declared file must exist on the local file system.

---

## How Test Runners Discover Files
- **Standard Go Toolchain (`go test`)**:
  When `go test -count=1 ./...` is invoked inside the exercise directory, the Go build system discovers all package files (`spiral_matrix.go`) and test files (`spiral_matrix_test.go`, `cases_test.go`) in the current package directory without inspecting `config.json`.
- **Track Verification Runners**:
  Track verification runners read `.meta/config.json` to substitute the reference implementation (`.meta/example.go`) in place of the learner solution stub (`spiral_matrix.go`) inside an isolated temporary directory before executing `go test`.

---

## Reproducible Validation Command
Run the path and configuration verification suite:
```bash
python3 tools/course_checks/r63-t008.py
```
Or run the full course verification check:
```bash
python3 work/R63-T008/check.py
```
