#!/usr/bin/env python3
"""Check script for R63-T048: Map the maintained files for triangle."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = Path(__file__).resolve().parent
TRIANGLE_DIR = REPO_ROOT / "exercises" / "practice" / "triangle"
DOCS_FILE = REPO_ROOT / "docs" / "maintenance" / "triangle.md"
VALIDATOR = REPO_ROOT / "tools" / "course_checks" / "r63-t048.py"

# Add tools to sys.path to import validate_config_dict
sys.path.insert(0, str(REPO_ROOT / "tools" / "course_checks"))
import importlib.util
spec = importlib.util.spec_from_file_location("validator", str(VALIDATOR))
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

def main():
    print("Starting check for R63-T048 triangle...")

    go_ver = subprocess.run(["go", "version"], capture_output=True, text=True).stdout.strip()
    py_ver = sys.version.replace("\n", " ")
    with open(WORK_DIR / "tool_versions.txt", "w") as f:
        f.write(f"Go: {go_ver}\nPython: {py_ver}\n")

    # 1. Check stub is unsolved
    stub_file = TRIANGLE_DIR / "triangle.go"
    with open(stub_file, "r") as f:
        stub_content = f.read()
    if "return k" not in stub_content or "var k Kind" not in stub_content:
        raise AssertionError("Learner stub in triangle.go must remain unsolved!")
    print("Original learner stub is untouched and unsolved.")

    # 2. Check maintenance doc exists
    if not DOCS_FILE.exists():
        raise AssertionError("docs/maintenance/triangle.md does not exist!")
    with open(DOCS_FILE, "r") as f:
        doc_content = f.read()
    if "triangle.go" not in doc_content or "triangle_test.go" not in doc_content or ".meta/example.go" not in doc_content:
        raise AssertionError("docs/maintenance/triangle.md must name stub, test, and reference paths!")
    print("Maintenance documentation exists with file role mapping.")

    # 3. Test real config passes
    with open(TRIANGLE_DIR / ".meta" / "config.json", "r") as f:
        real_config = json.load(f)["files"]
    ok, msg = validator.validate_config_dict(real_config, TRIANGLE_DIR)
    if not ok:
        raise AssertionError(f"Real config validation failed: {msg}")
    print("Real config passed validation.")

    # 4. Test 3 invalid fixtures
    # Fixture 1: missing reference
    bad_ref = {"solution": ["triangle.go"], "test": ["triangle_test.go"], "example": [".meta/nonexistent.go"]}
    ok1, msg1 = validator.validate_config_dict(bad_ref, TRIANGLE_DIR)
    if ok1 or "does not exist" not in msg1:
        raise AssertionError(f"Expected missing reference fixture to fail, got: {ok1}, {msg1}")
    print(f"Fixture 1 (missing reference) failed as expected: {msg1}")

    # Fixture 2: missing test
    bad_test = {"solution": ["triangle.go"], "test": ["missing_triangle_test.go"], "example": [".meta/example.go"]}
    ok2, msg2 = validator.validate_config_dict(bad_test, TRIANGLE_DIR)
    if ok2 or "does not exist" not in msg2:
        raise AssertionError(f"Expected missing test fixture to fail, got: {ok2}, {msg2}")
    print(f"Fixture 2 (missing test) failed as expected: {msg2}")

    # Fixture 3: outside exercise traversal
    bad_traversal = {"solution": ["triangle.go"], "test": ["triangle_test.go"], "example": ["../grains/.meta/example.go"]}
    ok3, msg3 = validator.validate_config_dict(bad_traversal, TRIANGLE_DIR)
    if ok3 or "traversal" not in msg3.lower():
        raise AssertionError(f"Expected traversal fixture to fail, got: {ok3}, {msg3}")
    print(f"Fixture 3 (outside traversal) failed as expected: {msg3}")

    # 5. Run tests with example.go in temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "triangle"
        shutil.copytree(TRIANGLE_DIR, tmp_exercise)
        shutil.copyfile(tmp_exercise / ".meta" / "example.go", tmp_exercise / "triangle.go")

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
        "task_id": "R63-T048",
        "exercise": "exercises/practice/triangle",
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "stub_unsolved": True,
        "real_config_passed": True,
        "fixtures": {
            "missing_reference": {"ok": ok1, "msg": msg1},
            "missing_test": {"ok": ok2, "msg": msg2},
            "outside_traversal": {"ok": ok3, "msg": msg3}
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
        f.write("# Verification Report for R63-T048\n\n")
        f.write("- Status: PASS\n")
        f.write(f"- Go version: {go_ver}\n")
        f.write(f"- Python version: {py_ver}\n")
        f.write(f"- Tests executed: {len(passed_tests)}\n")
        f.write("- Real config passed: True\n")
        f.write("- All three invalid fixtures failed for intended reasons.\n")

    print("All checks completed successfully!")

if __name__ == "__main__":
    main()
