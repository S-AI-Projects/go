#!/usr/bin/env python3
"""Check script for R63-T044 (resistor-color-duo reference refactor)."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = Path(__file__).resolve().parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "resistor-color-duo"
DOCS_DIR = REPO_ROOT / "docs" / "maintenance"

def main():
    print("Starting check for R63-T044 resistor-color-duo...")

    # Tool versions
    go_ver = subprocess.run(["go", "version"], capture_output=True, text=True).stdout.strip()
    py_ver = sys.version.replace("\n", " ")
    with open(WORK_DIR / "tool_versions.txt", "w") as f:
        f.write(f"Go: {go_ver}\nPython: {py_ver}\n")

    # 1. Check learner stub is unsolved
    stub_file = EXERCISE_DIR / "resistor_color_duo.go"
    with open(stub_file, "r") as f:
        stub_content = f.read()
    if "panic(" not in stub_content:
        raise AssertionError("Learner stub in resistor_color_duo.go should remain unsolved!")
    print("Original learner stub is untouched and unsolved.")

    # 2. Check example.go has readability refactor
    example_file = EXERCISE_DIR / ".meta" / "example.go"
    with open(example_file, "r") as f:
        example_content = f.read()
    if "tens :=" not in example_content or "ones :=" not in example_content:
        raise AssertionError("example.go should contain named tens and ones variables!")
    print("example.go contains readability refactor.")

    # 3. Check tests.toml has comment for Ignore additional colors
    toml_file = EXERCISE_DIR / ".meta" / "tests.toml"
    with open(toml_file, "r") as f:
        toml_content = f.read()
    if "0c4fb44f-db7c-4d03-afa8-054350f156a8" not in toml_content or "comment =" not in toml_content:
        raise AssertionError("tests.toml should contain comment for UUID 0c4fb44f-db7c-4d03-afa8-054350f156a8")
    print("tests.toml contains comment for Ignore additional colors.")

    # 4. Check maintenance doc exists
    doc_file = DOCS_DIR / "resistor-color-duo.md"
    if not doc_file.exists():
        raise AssertionError("docs/maintenance/resistor-color-duo.md does not exist!")
    print("Maintenance documentation exists.")

    # 5. Run tests against example.go in temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "resistor-color-duo"
        shutil.copytree(EXERCISE_DIR, tmp_exercise)

        # Copy example.go to resistor_color_duo.go
        shutil.copyfile(tmp_exercise / ".meta" / "example.go", tmp_exercise / "resistor_color_duo.go")

        proc = subprocess.run(["go", "test", "-v", "-count=1", "./..."], cwd=tmp_exercise, capture_output=True, text=True)
        if proc.returncode != 0:
            print("go test failed:\n", proc.stderr, proc.stdout)
            raise AssertionError(f"go test returned code {proc.returncode}")

        passed_tests = [line.strip() for line in proc.stdout.splitlines() if line.strip().startswith("--- PASS:")]
        if len(passed_tests) == 0:
            raise AssertionError("Zero tests executed!")
        print(f"Reference solution passed all {len(passed_tests)} tests.")

    # 6. Save results.json and report.md
    results = {
        "task_id": "R63-T044",
        "exercise": "exercises/practice/resistor-color-duo",
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "tests_toml_checked": True,
        "refactor_checked": True,
        "stub_unsolved": True,
        "test_results": {
            "returncode": 0,
            "passed_tests_count": len(passed_tests),
            "passed_tests": passed_tests
        },
        "status": "PASS"
    }

    with open(WORK_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    with open(WORK_DIR / "report.md", "w") as f:
        f.write(f"# Verification Report for R63-T044\n\n")
        f.write(f"- Status: PASS\n")
        f.write(f"- Tests executed: {len(passed_tests)}\n")
        f.write(f"- Go version: {go_ver}\n")
        f.write(f"- Python version: {py_ver}\n\n")
        f.write(f"All checks passed successfully.\n")

    print("All checks completed successfully!")

if __name__ == "__main__":
    main()
