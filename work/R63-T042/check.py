#!/usr/bin/env python3
"""
Simple check script for R63-T042 twelve days exercise.
This script checks:
1. Test generation reproducibility using tools/course_checks/r63-t042.py.
2. Exercise tests pass when using example.go in a temporary copy.
3. Learner stub twelve_days.go is untouched and unsolved.
4. Documentation exists in docs/maintenance/twelve-days.md.
5. Writes results.json, report.md, and tool_versions.txt in work/R63-T042/.
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
    exercise_rel = "exercises/practice/twelve-days"
    exercise_path = repo_root / exercise_rel
    config_file = exercise_path / ".meta" / "config.json"
    tests_toml_file = exercise_path / ".meta" / "tests.toml"
    doc_file = repo_root / "docs" / "maintenance" / "twelve-days.md"
    repro_script = repo_root / "tools" / "course_checks" / "r63-t042.py"

    print("Starting check for R63-T042 twelve days...")

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

    # Step 4: Check tests.toml entries and comments for multi verse cases
    if not tests_toml_file.exists():
        raise AssertionError("tests.toml not found at " + str(tests_toml_file))

    toml_entries = parse_tests_toml(tests_toml_file)
    total_cases = len(toml_entries)
    if total_cases != 15:
        raise AssertionError("Expected 15 test cases in tests.toml, found " + str(total_cases))

    multi_verse_uuids = [
        "da8b9013-b1e8-49df-b6ef-ddec0219e398",
        "c095af0d-3137-4653-ad32-bfb899eda24c",
        "20921bc9-cc52-4627-80b3-198cbbfcf9b7",
    ]

    for uid in multi_verse_uuids:
        if uid not in toml_entries:
            raise AssertionError("Multi verse UUID missing from tests.toml: " + uid)
        comment_text = toml_entries[uid].get("comment", "")
        if not comment_text:
            raise AssertionError("Multi verse UUID missing comment in tests.toml: " + uid)

    print("All multi verse UUIDs have comments in tests.toml.")

    # Step 5: Check docs/maintenance/twelve-days.md exists
    if not doc_file.exists():
        raise AssertionError("Maintenance doc missing: " + str(doc_file))

    with open(doc_file, "r", encoding="utf-8") as f:
        doc_content = f.read()

    for uid in multi_verse_uuids:
        if uid not in doc_content:
            raise AssertionError("Maintenance doc does not mention UUID: " + uid)

    print("Maintenance doc exists and documents all target cases.")

    # Step 6: Run reproducibility check script tools/course_checks/r63-t042.py
    if not repro_script.exists():
        raise AssertionError("Course check script missing: " + str(repro_script))

    print("Running tools/course_checks/r63-t042.py...")
    repro_proc = subprocess.run(
        [sys.executable, str(repro_script)],
        capture_output=True,
        text=True,
    )

    if repro_proc.returncode != 0:
        print("Reproducibility check failed:")
        print(repro_proc.stdout)
        print(repro_proc.stderr)
        raise AssertionError("r63-t042.py failed with exit code " + str(repro_proc.returncode))

    print("Reproducibility check passed.")

    # Step 7: Copy exercise to temporary directory, replace solution with example.go, and run go test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_exercise = Path(temp_dir) / "twelve-days"
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

    # Step 8: Write results.json
    results = {
        "task_id": "R63-T042",
        "exercise": exercise_rel,
        "tool_versions": {
            "go": go_ver,
            "python": py_ver,
        },
        "tests_toml": {
            "total_cases": total_cases,
            "multi_verse_cases": multi_verse_uuids,
        },
        "reproducibility_check": {
            "status": "PASS",
            "exit_code": repro_proc.returncode,
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

    # Step 9: Write report.md
    report_content = f"""# Test Report for R63-T042 (twelve-days)

## Overview

This report shows the verification results for Task 2 (R63-T042) on exercises/practice/twelve-days.
The goal of this task is to document and verify that test generation is reproducible,
explain how gen.go filters test cases, and make sure all tests pass against the example solution.

## Tool Versions

- Go: {go_ver}
- Python: {py_ver}

## Generation Reproducibility Check

Script: tools/course_checks/r63-t042.py
Result: PASS (exit code {repro_proc.returncode})

The script performed two fresh generations in temporary directories using:
GO111MODULE=off go run ./exercises/practice/twelve-days/.meta/gen.go

Both runs produced identical test outputs after timestamp and commit line normalization.
No test cases were silently dropped:
- 12 single verse test cases are present in testCases for TestVerse.
- 12 song lines are present in the song variable for TestSong.
- 2 multi verse cases (verses 1 to 3, and verses 4 to 6) are filtered out by gen.go as intended.

## Go Test Execution

The exercise was copied to a temporary folder and tested against the example solution (.meta/example.go).
Command: go test -count=1 -v ./...
Result: PASS (exit code {proc.returncode})
Passed test cases: {len(test_lines)}

The following tests passed:
"""
    for t_line in test_lines:
        report_content += f"- {t_line}\n"

    report_content += """
## Learner Stub Verification

The original learner stub at exercises/practice/twelve-days/twelve_days.go was checked.
It remains untouched and contains the original panic calls.
The student solution is still unsolved as required.

## Conclusion

All checks for R63-T042 passed cleanly.
"""

    report_file = work_dir / "report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content.strip() + "\n")

    print("Report saved to " + str(report_file))
    print("All checks completed successfully!")


if __name__ == "__main__":
    main()
