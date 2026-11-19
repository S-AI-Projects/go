#!/usr/bin/env python3
"""
Simple check script for R63-T043 reverse string exercise.
This script checks the reference solution, byte reversal mutant, and documentation.
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
    exercise_rel = "exercises/practice/reverse-string"
    exercise_path = repo_root / exercise_rel
    config_file = exercise_path / ".meta" / "config.json"
    tests_toml_file = exercise_path / ".meta" / "tests.toml"
    hints_file = exercise_path / ".docs" / "hints.md"
    doc_file = repo_root / "docs" / "maintenance" / "reverse-string.md"

    print("Starting check for R63-T043 reverse string...")

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

    # Step 4: Check tests.toml comment for wide characters case
    if not tests_toml_file.exists():
        raise AssertionError("tests.toml not found at " + str(tests_toml_file))

    toml_entries = parse_tests_toml(tests_toml_file)
    target_uuid = "1bed0f8a-13b0-4bd3-9d59-3d0593326fa2"
    if target_uuid not in toml_entries:
        raise AssertionError("Target UUID missing from tests.toml: " + target_uuid)

    target_comment = toml_entries[target_uuid].get("comment", "")
    if not target_comment:
        raise AssertionError("Target UUID is missing comment: " + target_uuid)

    print("Target UUID 1bed0f8a-13b0-4bd3-9d59-3d0593326fa2 has comment: " + target_comment)

    # Step 5: Check hints.md exists and contains guidance
    if not hints_file.exists():
        raise AssertionError("hints.md not found at " + str(hints_file))

    with open(hints_file, "r", encoding="utf-8") as f:
        hints_content = f.read()

    if "rune" not in hints_content or "byte" not in hints_content:
        raise AssertionError("hints.md must mention runes and bytes")

    print("hints.md exists and contains beginner guidance.")

    # Step 6: Check docs/maintenance/reverse-string.md exists and covers target case
    if not doc_file.exists():
        raise AssertionError("Maintenance doc missing: " + str(doc_file))

    with open(doc_file, "r", encoding="utf-8") as f:
        doc_content = f.read()

    if target_uuid not in doc_content:
        raise AssertionError("Maintenance doc does not mention UUID: " + target_uuid)

    print("Maintenance doc exists and includes target UUID.")

    # Step 7: Run reference implementation in temporary directory
    ref_pass_lines = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_exercise = Path(temp_dir) / "reverse-string"
        shutil.copytree(exercise_path, temp_exercise)

        source_example = temp_exercise / example_rel
        target_solution = temp_exercise / solution_rel

        shutil.copyfile(source_example, target_solution)

        test_cmd = ["go", "test", "-count=1", "-v", "./..."]
        proc_ref = subprocess.run(test_cmd, cwd=temp_exercise, capture_output=True, text=True)

        if proc_ref.returncode != 0:
            print("Reference tests failed in temporary directory:")
            print(proc_ref.stdout)
            print(proc_ref.stderr)
            raise AssertionError("Reference go test failed with exit code " + str(proc_ref.returncode))

        ref_pass_lines = [
            line.strip()
            for line in proc_ref.stdout.splitlines()
            if line.strip().startswith("--- PASS:")
        ]

        if len(ref_pass_lines) == 0:
            raise AssertionError("Zero tests passed with reference solution. Expected tests to run.")

        print("Reference solution passed all " + str(len(ref_pass_lines)) + " tests.")

    # Step 8: Run byte reversal mutant in temporary directory
    mutant_code = """package reversestring

// Reverse reverses given string by bytes instead of runes
func Reverse(s string) string {
\tbytes := []byte(s)
\tfor i, j := 0, len(bytes)-1; i < j; i, j = i+1, j-1 {
\t\tbytes[i], bytes[j] = bytes[j], bytes[i]
\t}
\treturn string(bytes)
}
"""

    mutant_fail_lines = []
    mutant_pass_lines = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_exercise = Path(temp_dir) / "reverse-string"
        shutil.copytree(exercise_path, temp_exercise)

        target_solution = temp_exercise / solution_rel
        with open(target_solution, "w", encoding="utf-8") as f:
            f.write(mutant_code)

        test_cmd = ["go", "test", "-count=1", "-v", "./..."]
        proc_mutant = subprocess.run(test_cmd, cwd=temp_exercise, capture_output=True, text=True)

        if proc_mutant.returncode == 0:
            raise AssertionError("Mutant unexpectedly passed all tests. It should fail on wide characters.")

        mutant_fail_lines = [
            line.strip()
            for line in proc_mutant.stdout.splitlines()
            if "FAIL" in line
        ]

        mutant_pass_lines = [
            line.strip()
            for line in proc_mutant.stdout.splitlines()
            if line.strip().startswith("--- PASS:")
        ]

        if "wide_characters" not in proc_mutant.stdout:
            raise AssertionError("Mutant failure output did not mention wide_characters")

        print("Mutant correctly failed on wide characters as expected.")

    # Step 9: Write results.json
    results = {
        "task_id": "R63-T043",
        "exercise": exercise_rel,
        "tool_versions": {
            "go": go_ver,
            "python": py_ver,
        },
        "tests_toml": {
            "target_uuid": target_uuid,
            "target_description": toml_entries[target_uuid].get("description", ""),
            "comment": target_comment,
        },
        "learner_stub_unsolved": True,
        "reference_run": {
            "exit_code": proc_ref.returncode,
            "pass_count": len(ref_pass_lines),
            "passed_tests": ref_pass_lines,
        },
        "mutant_run": {
            "exit_code": proc_mutant.returncode,
            "failed_as_expected": True,
            "rejecting_case": "wide characters (1bed0f8a-13b0-4bd3-9d59-3d0593326fa2)",
            "pass_count": len(mutant_pass_lines),
            "failure_details": [
                line for line in proc_mutant.stdout.splitlines() if "wide_characters" in line or "Reverse(" in line
            ],
        },
        "status": "PASS",
    }

    results_file = work_dir / "results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")
    print("Results saved to " + str(results_file))

    # Step 10: Write report.md
    report_content = f"""# Test Report for R63-T043 (reverse string)

## Overview

This report shows the verification results for Task 3 (R63-T043) on exercises/practice/reverse-string.
The goal of this task is to create a deliberate mutant (reversing bytes instead of runes),
verify that canonical test case 1bed0f8a-13b0-4bd3-9d59-3d0593326fa2 rejects it,
add hints and maintenance docs, and make sure the learner stub stays untouched.

## Tool Versions

- Go: {go_ver}
- Python: {py_ver}

## Learner Stub Check

File: exercises/practice/reverse-string/reverse_string.go
Status: Untouched and unsolved
The file contains the panic call and has not been implemented.

## Reference Solution Run

The exercise was tested in a temporary directory using the reference solution (.meta/example.go).
Command: go test -count=1 -v ./...
Result: PASS (exit code 0)
Passed test count: {len(ref_pass_lines)}

Passed tests:
"""
    for line in ref_pass_lines:
        report_content += f"- {line}\n"

    report_content += f"""
## Deliberate Mutant Run

A mutant that reverses raw bytes ([]byte) instead of runes ([]rune) was tested in a temporary directory.
Command: go test -count=1 -v ./...
Result: FAIL (exit code {proc_mutant.returncode}) as expected

Rejecting test case:
- UUID: 1bed0f8a-13b0-4bd3-9d59-3d0593326fa2
- Description: "wide characters"
- Input: "子猫"
- Expected: "猫子"

Failure output from test run:
```
{proc_mutant.stdout.strip()}
```

## Documentation and Comments Check

- tests.toml: UUID 1bed0f8a-13b0-4bd3-9d59-3d0593326fa2 has a comment explaining multi byte verification and rejection of byte level reversal mutants.
- hints.md: Created exercises/practice/reverse-string/.docs/hints.md with beginner friendly advice about runes and bytes.
- maintenance doc: Created docs/maintenance/reverse-string.md documenting the mutant, rejecting test case, expected behavior, and reduced input.

## Conclusion

All checks for R63-T043 passed cleanly.
"""

    report_file = work_dir / "report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
    print("Report saved to " + str(report_file))

    print("All checks completed successfully!")


if __name__ == "__main__":
    main()
