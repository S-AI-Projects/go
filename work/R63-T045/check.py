#!/usr/bin/env python3
"""Check script for R63-T045 (isbn-verifier reference complexity study)."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = Path(__file__).resolve().parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "isbn-verifier"
DOCS_DIR = REPO_ROOT / "docs" / "maintenance"

BENCH_GO = """package isbnverifier

import (
	"fmt"
	"testing"
	"time"
)

func TestMeasurements(t *testing.T) {
	inputs := []struct {
		name string
		isbn string
	}{
		{"Compact_10chars", "3598215088"},
		{"Standard_13chars", "3-598-21508-8"},
		{"CheckDigitX_13chars", "3-598-21507-X"},
	}

	for _, tc := range inputs {
		// Assert correctness first
		if !IsValidISBN(tc.isbn) {
			t.Fatalf("expected valid for %s", tc.isbn)
		}

		// Warmup
		for i := 0; i < 10000; i++ {
			_ = IsValidISBN(tc.isbn)
		}

		var reps []int64
		for r := 0; r < 5; r++ {
			iters := 100000
			start := time.Now()
			for i := 0; i < iters; i++ {
				_ = IsValidISBN(tc.isbn)
			}
			elapsed := time.Since(start).Nanoseconds()
			nsPerOp := elapsed / int64(iters)
			reps = append(reps, nsPerOp)
		}
		fmt.Printf("MEASURE:%s:%v\\n", tc.name, reps)
	}
}
"""

def main():
    print("Starting check for R63-T045 isbn-verifier...")

    go_ver = subprocess.run(["go", "version"], capture_output=True, text=True).stdout.strip()
    py_ver = sys.version.replace("\n", " ")
    with open(WORK_DIR / "tool_versions.txt", "w") as f:
        f.write(f"Go: {go_ver}\nPython: {py_ver}\n")

    # 1. Check stub is unsolved
    stub_file = EXERCISE_DIR / "isbn_verifier.go"
    with open(stub_file, "r") as f:
        stub_content = f.read()
    if "panic(" not in stub_content:
        raise AssertionError("Learner stub in isbn_verifier.go should remain unsolved!")
    print("Original learner stub is untouched and unsolved.")

    # 2. Check example.go has complexity comment
    example_file = EXERCISE_DIR / ".meta" / "example.go"
    with open(example_file, "r") as f:
        example_content = f.read()
    if "Time Complexity:" not in example_content or "Space Complexity:" not in example_content:
        raise AssertionError("example.go should contain complexity comments!")
    print("example.go contains complexity comments.")

    # 3. Check maintenance doc exists
    doc_file = DOCS_DIR / "isbn-verifier.md"
    if not doc_file.exists():
        raise AssertionError("docs/maintenance/isbn-verifier.md does not exist!")
    with open(doc_file, "r") as f:
        doc_content = f.read()
    if "3598215088" not in doc_content or "3-598-21508-8" not in doc_content or "3-598-21507-X" not in doc_content:
        raise AssertionError("docs/maintenance/isbn-verifier.md must include the 3 valid input sizes!")
    print("Maintenance documentation exists with domain input sizes.")

    # 4. Run tests and measurements in temporary copy
    measurements = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "isbn-verifier"
        shutil.copytree(EXERCISE_DIR, tmp_exercise)

        # Substitute reference solution
        shutil.copyfile(tmp_exercise / ".meta" / "example.go", tmp_exercise / "isbn_verifier.go")

        # Run canonical tests
        proc = subprocess.run(["go", "test", "-v", "-count=1", "./..."], cwd=tmp_exercise, capture_output=True, text=True)
        if proc.returncode != 0:
            print("go test failed:\n", proc.stderr, proc.stdout)
            raise AssertionError(f"go test returned code {proc.returncode}")

        passed_tests = [line.strip() for line in proc.stdout.splitlines() if line.strip().startswith("--- PASS:")]
        if len(passed_tests) == 0:
            raise AssertionError("Zero tests executed!")
        print(f"Reference solution passed all {len(passed_tests)} tests.")

        # Run measurement test
        with open(tmp_exercise / "measure_test.go", "w") as f:
            f.write(BENCH_GO)

        bench_proc = subprocess.run(["go", "test", "-v", "-run", "TestMeasurements", "./..."], cwd=tmp_exercise, capture_output=True, text=True)
        if bench_proc.returncode != 0:
            print("benchmark failed:\n", bench_proc.stderr, bench_proc.stdout)
            raise AssertionError(f"benchmark failed with code {bench_proc.returncode}")

        for line in bench_proc.stdout.splitlines():
            if line.startswith("MEASURE:"):
                parts = line.split(":")
                name = parts[1]
                reps_str = parts[2].strip("[] \n")
                reps = [int(x.strip()) for x in reps_str.split()]
                reps_sorted = sorted(reps)
                median = reps_sorted[len(reps_sorted) // 2]
                measurements[name] = {
                    "reps_ns": reps,
                    "median_ns": median
                }
                print(f"Measured {name}: median = {median} ns, reps = {reps}")

    # 5. Save results.json and report.md
    results = {
        "task_id": "R63-T045",
        "exercise": "exercises/practice/isbn-verifier",
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "stub_unsolved": True,
        "complexity_comment_checked": True,
        "test_results": {
            "returncode": 0,
            "passed_tests_count": len(passed_tests),
            "passed_tests": passed_tests
        },
        "measurements": measurements,
        "status": "PASS"
    }

    with open(WORK_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    with open(WORK_DIR / "report.md", "w") as f:
        f.write("# Verification Report for R63-T045\n\n")
        f.write(f"- Status: PASS\n")
        f.write(f"- Tests executed: {len(passed_tests)}\n")
        f.write(f"- Go version: {go_ver}\n")
        f.write(f"- Python version: {py_ver}\n\n")
        f.write("## Empirical Measurements\n\n")
        for k, v in measurements.items():
            f.write(f"- **{k}**: median {v['median_ns']} ns, reps: {v['reps_ns']}\n")
        f.write("\nAll checks passed successfully.\n")

    print("All checks completed successfully!")

if __name__ == "__main__":
    main()
