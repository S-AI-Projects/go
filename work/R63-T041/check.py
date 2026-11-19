#!/usr/bin/env python3
"""
Simple check script for R63-T041 perfect numbers exercise.
This script checks the solution, tests, and documentation.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_tests_toml(toml_path):
    """Simple parser to read entries from tests.toml without external tools."""
    entries = {}
    current_uuid = None
    with open(toml_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_uuid = line[1:-1].strip()
                entries[current_uuid] = {}
            elif current_uuid and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"')
                if val == "false":
                    entries[current_uuid][key] = False
                elif val == "true":
                    entries[current_uuid][key] = True
                else:
                    entries[current_uuid][key] = val
    return entries


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    work_dir = Path(__file__).resolve().parent
    exercise_rel = "exercises/practice/perfect-numbers"
    exercise_path = repo_root / exercise_rel
    config_file = exercise_path / ".meta" / "config.json"
    tests_toml_file = exercise_path / ".meta" / "tests.toml"
    doc_file = repo_root / "docs" / "maintenance" / "perfect-numbers.md"

    print("Starting check for R63-T041 perfect numbers...")

    # Step 1: Collect tool versions
    go_ver = subprocess.check_output(["go", "version"], text=True).strip()
    py_ver = sys.version.replace("\n", " ")
    print("Go version: " + go_ver)
    print("Python version: " + py_ver)

    tool_versions_path = work_dir / "tool_versions.txt"
    with open(tool_versions_path, "w", encoding="utf-8") as f:
        f.write("Go: " + go_ver + "\nPython: " + py_ver + "\n")

    # Step 2: Read config.json to find file names
    if not config_file.exists():
        raise AssertionError("config.json not found at " + str(config_file))

    with open(config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    solution_files = config_data.get("files", {}).get("solution", [])
    example_files = config_data.get("files", {}).get("example", [])
    if not solution_files or not example_files:
        raise AssertionError("Missing solution or example files in config.json")

    solution_rel = solution_files[0]
    example_rel = example_files[0]

    # Step 3: Check original learner stub is untouched and unsolved
    original_solution_path = exercise_path / solution_rel
    if not original_solution_path.exists():
        raise AssertionError("Original solution file not found: " + str(original_solution_path))

    with open(original_solution_path, "r", encoding="utf-8") as f:
        original_code = f.read()

    if "panic(" not in original_code:
        raise AssertionError("Learner solution is modified or solved. It must stay unsolved.")

    print("Original learner stub is untouched and unsolved.")

    # Step 4: Check tests.toml entries and comments
    if not tests_toml_file.exists():
        raise AssertionError("tests.toml not found at " + str(tests_toml_file))

    toml_entries = parse_tests_toml(tests_toml_file)
    total_cases = len(toml_entries)
    if total_cases != 14:
        raise AssertionError("Expected 14 test cases in tests.toml, found " + str(total_cases))

    excluded_cases = [k for k, v in toml_entries.items() if v.get("include") is False]
    if len(excluded_cases) != 0:
        raise AssertionError("Expected 0 excluded cases, found " + str(len(excluded_cases)))

    target_uuids = [
        "163e8e86-7bfd-4ee2-bd68-d083dc3381a3",
        "169a7854-0431-4ae0-9815-c3b6d967436d",
        "ee3627c4-7b36-4245-ba7c-8727d585f402",
    ]

    for uid in target_uuids:
        if uid not in toml_entries:
            raise AssertionError("Target UUID missing from tests.toml: " + uid)
        comment_text = toml_entries[uid].get("comment", "")
        if not comment_text:
            raise AssertionError("Target UUID is missing comment: " + uid)

    print("All target UUIDs have comments in tests.toml.")

    # Step 5: Check docs/maintenance/perfect-numbers.md exists and covers target cases
    if not doc_file.exists():
        raise AssertionError("Maintenance documentation missing: " + str(doc_file))

    with open(doc_file, "r", encoding="utf-8") as f:
        doc_content = f.read()

    for uid in target_uuids:
        if uid not in doc_content:
            raise AssertionError("Maintenance doc does not mention UUID: " + uid)

    print("Maintenance doc exists and includes all target UUIDs.")

    # Step 6: Copy exercise to temporary directory, replace solution with example.go, and run go test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_exercise = Path(temp_dir) / "perfect-numbers"
        shutil.copytree(exercise_path, temp_exercise)

        source_example = temp_exercise / example_rel
        target_solution = temp_exercise / solution_rel

        shutil.copyfile(source_example, target_solution)

        test_cmd = ["go", "test", "-count=1", "-v", "./..."]
        proc = subprocess.run(test_cmd, cwd=temp_exercise, capture_output=True, text=True)

        if proc.returncode != 0:
            print("Tests failed in temporary directory:")
            print(proc.stdout)
            print(proc.stderr)
            raise AssertionError("go test failed with exit code " + str(proc.returncode))

        test_lines = [
            line.strip()
            for line in proc.stdout.splitlines()
            if line.strip().startswith("--- PASS:")
        ]

        if len(test_lines) == 0:
            raise AssertionError("Zero tests passed. Expected tests to run.")

        print("Go test passed successfully. Found " + str(len(test_lines)) + " pass lines.")

    # Step 7: Write results.json
    results = {
        "task_id": "R63-T041",
        "exercise": exercise_rel,
        "tool_versions": {
            "go": go_ver,
            "python": py_ver,
        },
        "tests_toml": {
            "total_cases": total_cases,
            "excluded_cases": len(excluded_cases),
            "target_uuids_checked": target_uuids,
        },
        "learner_stub_unsolved": True,
        "test_results": {
            "exit_code": proc.returncode,
            "pass_count": len(test_lines),
            "tests": test_lines,
        },
        "status": "PASS",
    }

    results_file = work_dir / "results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")

    print("Results saved to " + str(results_file))
    print("All checks passed cleanly!")


if __name__ == "__main__":
    main()
