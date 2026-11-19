#!/usr/bin/env python3
"""Check script for R63-T049: Run diamond without altering its learner files."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = Path(__file__).resolve().parent
DIAMOND_DIR = REPO_ROOT / "exercises" / "practice" / "diamond"
DOCS_FILE = REPO_ROOT / "docs" / "maintenance" / "diamond.md"
RUNNER_PATH = REPO_ROOT / "tools" / "course_checks" / "r63-t049.py"

# Import runner functions
import importlib.util
spec = importlib.util.spec_from_file_location("runner", str(RUNNER_PATH))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

FAILING_DIAMOND_GO = """package diamond

import "errors"

func Gen(char byte) (string, error) {
	return "", errors.New("deliberate failure for testing error handling")
}
"""

def main():
    print("Starting check for R63-T049 diamond...")

    go_ver = subprocess.run(["go", "version"], capture_output=True, text=True).stdout.strip()
    py_ver = sys.version.replace("\n", " ")
    with open(WORK_DIR / "tool_versions.txt", "w") as f:
        f.write(f"Go: {go_ver}\nPython: {py_ver}\n")

    # 1. Check learner stub is unsolved
    stub_file = DIAMOND_DIR / "diamond.go"
    with open(stub_file, "r") as f:
        stub_content = f.read()
    if "panic(" not in stub_content:
        raise AssertionError("Learner stub in diamond.go must remain unsolved!")
    print("Original learner stub is untouched and unsolved.")

    # 2. Check maintenance doc exists
    if not DOCS_FILE.exists():
        raise AssertionError("docs/maintenance/diamond.md does not exist!")
    print("Maintenance documentation exists.")

    initial_hashes = runner.compute_file_hashes(DIAMOND_DIR)

    # 3. Scenario 1: Real reference
    res1 = runner.run_isolated_test(DIAMOND_DIR)
    if not res1["hashes_preserved"]:
        raise AssertionError("Scenario 1 failed to preserve file hashes!")
    if not res1["tests_passed"] or res1["exit_code"] != 0:
        raise AssertionError(f"Scenario 1 real reference tests failed with code {res1['exit_code']}")
    print(f"Scenario 1 (real reference) passed all {res1['passed_count']} tests.")

    # 4. Scenario 2: Deliberately failing reference
    with tempfile.TemporaryDirectory() as tmpdir:
        fail_file = Path(tmpdir) / "failing.go"
        with open(fail_file, "w") as f:
            f.write(FAILING_DIAMOND_GO)

        res2 = runner.run_isolated_test(DIAMOND_DIR, solution_override=fail_file)
        if not res2["hashes_preserved"]:
            raise AssertionError("Scenario 2 failed to preserve file hashes!")
        if res2["exit_code"] == 0 or res2["tests_passed"]:
            raise AssertionError("Scenario 2 expected failing reference to produce non-zero exit code!")
        print("Scenario 2 (deliberately failing reference) correctly produced non-zero exit code.")

    # 5. Scenario 3: Empty test selection
    res3 = runner.run_isolated_test(DIAMOND_DIR, test_run_flag="NonExistentTestPattern")
    if not res3["hashes_preserved"]:
        raise AssertionError("Scenario 3 failed to preserve file hashes!")
    if not res3["zero_tests"]:
        raise AssertionError("Scenario 3 expected zero tests detected!")
    print("Scenario 3 (empty test selection) correctly detected zero tests.")

    # Verify overall file hashes unchanged
    final_hashes = runner.compute_file_hashes(DIAMOND_DIR)
    if initial_hashes != final_hashes:
        raise AssertionError("Overall learner files were modified during check runs!")
    print("Verified: learner files remained 100% identical and unmodified.")

    # 6. Save results.json and report.md
    results = {
        "task_id": "R63-T049",
        "exercise": "exercises/practice/diamond",
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "stub_unsolved": True,
        "scenarios": {
            "real_reference": {
                "exit_code": res1["exit_code"],
                "passed_count": res1["passed_count"],
                "hashes_preserved": res1["hashes_preserved"]
            },
            "failing_reference": {
                "exit_code": res2["exit_code"],
                "tests_passed": res2["tests_passed"],
                "hashes_preserved": res2["hashes_preserved"]
            },
            "empty_selection": {
                "exit_code": res3["exit_code"],
                "zero_tests": res3["zero_tests"],
                "hashes_preserved": res3["hashes_preserved"]
            }
        },
        "status": "PASS"
    }

    with open(WORK_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    with open(WORK_DIR / "report.md", "w") as f:
        f.write("# Verification Report for R63-T049\n\n")
        f.write("- Status: PASS\n")
        f.write(f"- Go version: {go_ver}\n")
        f.write(f"- Python version: {py_ver}\n")
        f.write(f"- Real reference tests passed: {res1['passed_count']}\n")
        f.write("- Failing reference produced non-zero exit code: True\n")
        f.write("- Empty test selection detected: True\n")
        f.write("- Learner file hashes preserved across all runs: True\n")

    print("All checks completed successfully!")

if __name__ == "__main__":
    main()
