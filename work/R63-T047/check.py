#!/usr/bin/env python3
"""Check script for R63-T047: Add Go-specific guidance for prime-factors."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = Path(__file__).resolve().parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "prime-factors"
HINTS_FILE = EXERCISE_DIR / ".docs" / "hints.md"
DOCS_FILE = REPO_ROOT / "docs" / "maintenance" / "prime-factors.md"

WORKING_GO = """package main

import "fmt"

func main() {
	factors := []int64{}
	fmt.Println(len(factors) == 0)
	fmt.Println(factors != nil)
}
"""

PITFALL_GO = """package main

import (
	"fmt"
	"reflect"
)

func main() {
	var factors []int64
	fmt.Println(len(factors) == 0)
	fmt.Println(factors == nil)
	fmt.Println(reflect.DeepEqual(factors, []int64{}))
}
"""

def main():
    print("Starting check for R63-T047 prime-factors...")

    go_ver = subprocess.run(["go", "version"], capture_output=True, text=True).stdout.strip()
    py_ver = sys.version.replace("\n", " ")
    with open(WORK_DIR / "tool_versions.txt", "w") as f:
        f.write(f"Go: {go_ver}\nPython: {py_ver}\n")

    # 1. Check stub is unsolved
    stub_file = EXERCISE_DIR / "prime_factors.go"
    with open(stub_file, "r") as f:
        stub_content = f.read()
    if "panic(" not in stub_content:
        raise AssertionError("Learner stub in prime_factors.go must remain unsolved!")
    print("Original learner stub is untouched and unsolved.")

    # 2. Check hints.md has required sections
    if not HINTS_FILE.exists():
        raise AssertionError("hints.md does not exist!")
    with open(HINTS_FILE, "r") as f:
        hints_content = f.read()
    if "Go-Specific Guidance" not in hints_content or "https://go.dev/ref/spec#The_zero_value" not in hints_content:
        raise AssertionError("hints.md must contain Go-specific guidance and link to the Go spec!")
    print("hints.md contains Go-specific guidance and reference links.")

    # 3. Check maintenance doc exists
    if not DOCS_FILE.exists():
        raise AssertionError("docs/maintenance/prime-factors.md does not exist!")
    print("Maintenance documentation exists.")

    # 4. Execute micro-examples
    with tempfile.TemporaryDirectory() as tmpdir:
        working_file = Path(tmpdir) / "working.go"
        with open(working_file, "w") as f:
            f.write(WORKING_GO)
        proc_w = subprocess.run(["go", "run", str(working_file)], capture_output=True, text=True)
        if proc_w.returncode != 0 or proc_w.stdout.strip() != "true\ntrue":
            raise AssertionError(f"Working micro-example failed: {proc_w.stderr} {proc_w.stdout}")
        print("Working micro-example output verified: true, true.")

        pitfall_file = Path(tmpdir) / "pitfall.go"
        with open(pitfall_file, "w") as f:
            f.write(PITFALL_GO)
        proc_p = subprocess.run(["go", "run", str(pitfall_file)], capture_output=True, text=True)
        if proc_p.returncode != 0 or proc_p.stdout.strip() != "true\ntrue\nfalse":
            raise AssertionError(f"Pitfall micro-example failed: {proc_p.stderr} {proc_p.stdout}")
        print("Pitfall micro-example output verified: true, true, false.")

    # 5. Run tests with example.go in temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "prime-factors"
        shutil.copytree(EXERCISE_DIR, tmp_exercise)
        shutil.copyfile(tmp_exercise / ".meta" / "example.go", tmp_exercise / "prime_factors.go")

        proc_test = subprocess.run(["go", "test", "-v", "-count=1", "./..."], cwd=tmp_exercise, capture_output=True, text=True)
        if proc_test.returncode != 0:
            print("go test failed:\n", proc_test.stderr, proc_test.stdout)
            raise AssertionError(f"go test returned code {proc_test.returncode}")
        passed_tests = [l.strip() for l in proc_test.stdout.splitlines() if l.strip().startswith("--- PASS:")]
        if len(passed_tests) == 0:
            raise AssertionError("Zero tests passed!")
        print(f"Reference solution passed all {len(passed_tests)} tests.")

    # 6. Save results.json and report.md
    results = {
        "task_id": "R63-T047",
        "exercise": "exercises/practice/prime-factors",
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "stub_unsolved": True,
        "hints_checked": True,
        "micro_examples": {
            "working_output": proc_w.stdout.strip(),
            "pitfall_output": proc_p.stdout.strip()
        },
        "test_results": {
            "exit_code": 0,
            "passed_tests_count": len(passed_tests),
            "passed_tests": passed_tests
        },
        "status": "PASS"
    }

    with open(WORK_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    with open(WORK_DIR / "report.md", "w") as f:
        f.write("# Verification Report for R63-T047\n\n")
        f.write("- Status: PASS\n")
        f.write(f"- Go version: {go_ver}\n")
        f.write(f"- Python version: {py_ver}\n")
        f.write(f"- Tests executed: {len(passed_tests)}\n\n")
        f.write("Both working and pitfall micro-examples executed with expected outputs.\n")

    print("All checks completed successfully!")

if __name__ == "__main__":
    main()
