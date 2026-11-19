#!/usr/bin/env python3
"""Check script for R63-T046: Comparing two approaches to grains in Go."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = Path(__file__).resolve().parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "grains"
HINTS_FILE = EXERCISE_DIR / ".docs" / "hints.md"
DOCS_FILE = REPO_ROOT / "docs" / "maintenance" / "grains.md"
ALT_IMPL = WORK_DIR / "alternative_loop.go"

def main():
    print("Starting check for R63-T046 grains...")

    go_ver = subprocess.run(["go", "version"], capture_output=True, text=True).stdout.strip()
    py_ver = sys.version.replace("\n", " ")
    with open(WORK_DIR / "tool_versions.txt", "w") as f:
        f.write(f"Go: {go_ver}\nPython: {py_ver}\n")

    # 1. Check learner stub is unsolved
    stub_file = EXERCISE_DIR / "grains.go"
    with open(stub_file, "r") as f:
        stub_content = f.read()
    if "panic(" not in stub_content:
        raise AssertionError("Learner stub in grains.go must remain unsolved!")
    print("Original learner stub is untouched and unsolved.")

    # 2. Check hints.md has required sections
    if not HINTS_FILE.exists():
        raise AssertionError("hints.md does not exist!")
    with open(HINTS_FILE, "r") as f:
        hints_content = f.read()
    if "Approach Selection" not in hints_content or "Worked Example" not in hints_content:
        raise AssertionError("hints.md must contain Approach Selection and Worked Example!")
    print("hints.md contains approach guidance and worked example.")

    # 3. Check maintenance doc exists
    if not DOCS_FILE.exists():
        raise AssertionError("docs/maintenance/grains.md does not exist!")
    print("Maintenance documentation exists.")

    # 4. Test reference implementation in temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "grains"
        shutil.copytree(EXERCISE_DIR, tmp_exercise)
        shutil.copyfile(tmp_exercise / ".meta" / "example.go", tmp_exercise / "grains.go")

        proc_ref = subprocess.run(["go", "test", "-v", "-count=1", "./..."], cwd=tmp_exercise, capture_output=True, text=True)
        if proc_ref.returncode != 0:
            print("Reference tests failed:\n", proc_ref.stderr, proc_ref.stdout)
            raise AssertionError(f"Reference tests failed with exit code {proc_ref.returncode}")
        ref_passed = [l.strip() for l in proc_ref.stdout.splitlines() if l.strip().startswith("--- PASS:")]
        if len(ref_passed) == 0:
            raise AssertionError("Zero tests passed for reference!")
        print(f"Reference implementation passed all {len(ref_passed)} tests.")

    # 5. Test alternative implementation in temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "grains"
        shutil.copytree(EXERCISE_DIR, tmp_exercise)
        shutil.copyfile(ALT_IMPL, tmp_exercise / "grains.go")

        proc_alt = subprocess.run(["go", "test", "-v", "-count=1", "./..."], cwd=tmp_exercise, capture_output=True, text=True)
        if proc_alt.returncode != 0:
            print("Alternative tests failed:\n", proc_alt.stderr, proc_alt.stdout)
            raise AssertionError(f"Alternative tests failed with exit code {proc_alt.returncode}")
        alt_passed = [l.strip() for l in proc_alt.stdout.splitlines() if l.strip().startswith("--- PASS:")]
        if len(alt_passed) == 0:
            raise AssertionError("Zero tests passed for alternative!")
        print(f"Alternative implementation passed all {len(alt_passed)} tests.")

    # 6. Save results.json and report.md
    results = {
        "task_id": "R63-T046",
        "exercise": "exercises/practice/grains",
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "stub_unsolved": True,
        "hints_checked": True,
        "reference_tests": {
            "exit_code": 0,
            "passed_count": len(ref_passed),
            "passed_tests": ref_passed
        },
        "alternative_tests": {
            "exit_code": 0,
            "passed_count": len(alt_passed),
            "passed_tests": alt_passed
        },
        "status": "PASS"
    }

    with open(WORK_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    with open(WORK_DIR / "report.md", "w") as f:
        f.write("# Verification Report for R63-T046\n\n")
        f.write("- Status: PASS\n")
        f.write(f"- Go version: {go_ver}\n")
        f.write(f"- Python version: {py_ver}\n")
        f.write(f"- Reference tests passed: {len(ref_passed)}\n")
        f.write(f"- Alternative tests passed: {len(alt_passed)}\n\n")
        f.write("Both bitwise shifting and iterative loop approaches pass all canonical tests.\n")

    print("All checks completed successfully!")

if __name__ == "__main__":
    main()
