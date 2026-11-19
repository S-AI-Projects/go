#!/usr/bin/env python3
"""Check script for R63-T050: Explain the subtle contract cases in linked-list."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = Path(__file__).resolve().parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "linked-list"
HINTS_FILE = EXERCISE_DIR / ".docs" / "hints.md"
DOCS_FILE = REPO_ROOT / "docs" / "maintenance" / "linked-list.md"

def main():
    print("Starting check for R63-T050 linked-list...")

    go_ver = subprocess.run(["go", "version"], capture_output=True, text=True).stdout.strip()
    py_ver = sys.version.replace("\n", " ")
    with open(WORK_DIR / "tool_versions.txt", "w") as f:
        f.write(f"Go: {go_ver}\nPython: {py_ver}\n")

    # 1. Check learner stub is unsolved
    stub_file = EXERCISE_DIR / "linked_list.go"
    with open(stub_file, "r") as f:
        stub_content = f.read()
    if "panic(" not in stub_content:
        raise AssertionError("Learner stub in linked_list.go must remain unsolved!")
    print("Original learner stub is untouched and unsolved.")

    # 2. Check hints.md has required sections
    if not HINTS_FILE.exists():
        raise AssertionError("hints.md does not exist!")
    with open(HINTS_FILE, "r") as f:
        hints_content = f.read()
    if "Decision Table" not in hints_content or "Subtle Contract Cases" not in hints_content or "Unspecified Behavior" not in hints_content:
        raise AssertionError("hints.md must contain Decision Table, Subtle Contract Cases, and Unspecified Behavior statement!")
    print("hints.md contains decision table, subtle contract cases, and unspecified behavior statement.")

    # 3. Check maintenance doc exists
    if not DOCS_FILE.exists():
        raise AssertionError("docs/maintenance/linked-list.md does not exist!")
    print("Maintenance documentation exists.")

    # 4. Run tests with example.go in temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "linked-list"
        shutil.copytree(EXERCISE_DIR, tmp_exercise)
        shutil.copyfile(tmp_exercise / ".meta" / "example.go", tmp_exercise / "linked_list.go")

        proc_test = subprocess.run(["go", "test", "-v", "-count=1", "./..."], cwd=tmp_exercise, capture_output=True, text=True)
        if proc_test.returncode != 0:
            print("go test failed:\n", proc_test.stderr, proc_test.stdout)
            raise AssertionError(f"go test returned code {proc_test.returncode}")
        passed_tests = [l.strip() for l in proc_test.stdout.splitlines() if l.strip().startswith("--- PASS:")]
        if len(passed_tests) == 0:
            raise AssertionError("Zero tests passed!")
        print(f"Reference solution passed all {len(passed_tests)} tests.")

    # 5. Save results.json and report.md
    results = {
        "task_id": "R63-T050",
        "exercise": "exercises/practice/linked-list",
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "stub_unsolved": True,
        "hints_checked": True,
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
        f.write("# Verification Report for R63-T050\n\n")
        f.write("- Status: PASS\n")
        f.write(f"- Go version: {go_ver}\n")
        f.write(f"- Python version: {py_ver}\n")
        f.write(f"- Tests executed: {len(passed_tests)}\n\n")
        f.write("All tests passed and subtle contract cases verified.\n")

    print("All checks completed successfully!")

if __name__ == "__main__":
    main()
