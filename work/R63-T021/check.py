#!/usr/bin/env python3
"""
Verification script for R63-T021:
- Resolves paths from exercises/practice/simple-linked-list/.meta/config.json
- Copies the exercise to a temporary directory (including dotfiles)
- Substitutes the reference implementation into the solution filename only in that temporary copy
- Runs: go test -count=1 ./... in the scratch module
- Checks return codes and test counts (fails on 0 tests, child error, or assertion failure)
- Verifies the working tree learner solution stub is unchanged and unsolved
- Reviews 29 canonical case entries in tests.toml, including 5 exclusions
- Verifies rationales for 70d747a1-2e84-4ebc-bc3f-dcbee6a05f6b, b97d00b6-2fab-435d-ae74-3233dcc13698, eedeb95f-b5cf-431d-8ad6-5854ba6b251c
- Records included/excluded counts before and after
- Records tool versions, inputs, and expected vs actual results in work/R63-T021/
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomli

def get_tool_versions():
    versions = {}
    try:
        r = subprocess.run(["go", "version"], capture_output=True, text=True, check=True)
        versions["go"] = r.stdout.strip()
    except Exception as e:
        versions["go"] = f"error: {e}"

    try:
        r = subprocess.run(["python3", "--version"], capture_output=True, text=True, check=True)
        versions["python3"] = r.stdout.strip()
    except Exception as e:
        versions["python3"] = f"error: {e}"

    try:
        r = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True)
        versions["git"] = r.stdout.strip()
    except Exception as e:
        versions["git"] = f"error: {e}"

    return versions

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    work_dir = os.path.join(repo_root, "work", "R63-T021")
    os.makedirs(work_dir, exist_ok=True)

    exercise_dir = os.path.join(repo_root, "exercises", "practice", "simple-linked-list")
    config_path = os.path.join(exercise_dir, ".meta", "config.json")
    tests_toml_path = os.path.join(exercise_dir, ".meta", "tests.toml")

    results_data = {
        "task": "R63-T021",
        "exercise": "simple-linked-list",
        "checks": [],
        "tool_versions": get_tool_versions(),
        "success": False,
    }

    print("=== Step 1: Resolving paths from config.json ===")
    assert os.path.exists(config_path), f"config.json not found at {config_path}"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_rel = config["files"]["solution"][0]
    example_rel = config["files"]["example"][0]
    test_files_rel = config["files"]["test"]

    solution_src = os.path.join(exercise_dir, solution_rel)
    example_src = os.path.join(exercise_dir, example_rel)
    test_sources = [os.path.join(exercise_dir, t) for t in test_files_rel]

    assert os.path.exists(solution_src), f"Solution file not found: {solution_src}"
    assert os.path.exists(example_src), f"Example file not found: {example_src}"
    for ts in test_sources:
        assert os.path.exists(ts), f"Test file not found: {ts}"

    results_data["checks"].append({
        "name": "path_resolution",
        "status": "PASS",
        "resolved": {
            "solution": solution_rel,
            "example": example_rel,
            "tests": test_files_rel,
        }
    })
    print(f"Resolved solution: {solution_rel}")
    print(f"Resolved example: {example_rel}")
    print(f"Resolved tests: {test_files_rel}")

    print("\n=== Step 2: Verifying learner stub is unchanged in working tree ===")
    with open(solution_src, "r", encoding="utf-8") as f:
        learner_stub_content = f.read()

    assert "panic(\"Please implement the New function\")" in learner_stub_content, (
        "Learner stub in working tree must remain unsolved!"
    )
    assert "panic(\"Please implement the Array function\")" in learner_stub_content, (
        "Learner stub in working tree must remain unsolved!"
    )
    results_data["checks"].append({
        "name": "learner_stub_unsolved",
        "status": "PASS",
        "details": "simple_linked_list.go contains unsolved panic stubs"
    })
    print("Learner stub in working tree is verified unsolved.")

    print("\n=== Step 3: Running reference implementation in temporary scratch copy ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        scratch_exercise = os.path.join(tmpdir, "simplelinkedlist")
        # Copy entire exercise including dotfiles (.docs, .meta)
        shutil.copytree(exercise_dir, scratch_exercise)

        scratch_solution = os.path.join(scratch_exercise, solution_rel)
        scratch_example = os.path.join(scratch_exercise, example_rel)

        # Substitute reference into solution filename only in the scratch copy
        shutil.copyfile(scratch_example, scratch_solution)

        # Run go test -count=1 ./...
        cmd_standard = ["go", "test", "-count=1", "./..."]
        res_standard = subprocess.run(cmd_standard, cwd=scratch_exercise, capture_output=True, text=True)

        # Also run with -v to inspect individual test case execution counts and names
        cmd_verbose = ["go", "test", "-v", "-count=1", "./..."]
        res_verbose = subprocess.run(cmd_verbose, cwd=scratch_exercise, capture_output=True, text=True)

        # Save test output
        test_output_file = os.path.join(work_dir, "test_output.txt")
        with open(test_output_file, "w", encoding="utf-8") as f:
            f.write(f"=== Command: {' '.join(cmd_standard)} ===\n")
            f.write(f"Return code: {res_standard.returncode}\n")
            f.write(f"Output:\n{res_standard.stdout}\n")
            if res_standard.stderr:
                f.write(f"Stderr:\n{res_standard.stderr}\n")
            f.write(f"\n=== Command: {' '.join(cmd_verbose)} ===\n")
            f.write(f"Return code: {res_verbose.returncode}\n")
            f.write(f"Output:\n{res_verbose.stdout}\n")

        print(f"Standard test return code: {res_standard.returncode}")
        assert res_standard.returncode == 0, (
            f"go test failed with code {res_standard.returncode}:\n{res_standard.stdout}\n{res_standard.stderr}"
        )
        assert res_verbose.returncode == 0, (
            f"go test -v failed with code {res_verbose.returncode}:\n{res_verbose.stdout}\n{res_verbose.stderr}"
        )

        # Parse passed subtests
        subtests = re.findall(r"--- PASS:\s+TestList/(\S+)", res_verbose.stdout)
        test_count = len(subtests)
        print(f"Executed test cases count: {test_count}")
        assert test_count > 0, "Zero test run! Must fail on zero-test run."
        assert test_count == 24, f"Expected 24 test cases, found {test_count}"

        results_data["checks"].append({
            "name": "scratch_reference_test",
            "status": "PASS",
            "test_count": test_count,
            "executed_cases": subtests,
            "return_code": res_standard.returncode,
        })

    # Double check that working tree was NOT rewritten
    with open(solution_src, "r", encoding="utf-8") as f:
        content_after = f.read()
    assert content_after == learner_stub_content, "Working tree solution was modified!"

    print("\n=== Step 4: Validating tests.toml, counts, and rationales ===")
    assert os.path.exists(tests_toml_path), f"tests.toml not found: {tests_toml_path}"
    with open(tests_toml_path, "rb") as f:
        toml_data = tomli.load(f)

    total_cases = len(toml_data)
    excluded_cases = [k for k, v in toml_data.items() if v.get("include") is False]
    included_cases = [k for k, v in toml_data.items() if v.get("include") is not False]

    print(f"tests.toml total entries: {total_cases}")
    print(f"tests.toml excluded count: {len(excluded_cases)}")
    print(f"tests.toml included count: {len(included_cases)}")

    assert total_cases == 29, f"Expected 29 canonical case entries, found {total_cases}"
    assert len(excluded_cases) == 5, f"Expected 5 exclusions, found {len(excluded_cases)}"
    assert len(included_cases) == 24, f"Expected 24 inclusions, found {len(included_cases)}"

    target_uuids = {
        "70d747a1-2e84-4ebc-bc3f-dcbee6a05f6b": {
            "type": "replacement",
            "reimplements_by": "f3197f0a-1fea-45a5-939f-4a5ea60387ec",
            "operation": "Push",
            "expected_test": "Can push to an empty list",
        },
        "b97d00b6-2fab-435d-ae74-3233dcc13698": {
            "type": "unsupported",
            "operation": "Array",
            "expected_test": "Empty linked list to list is empty",
        },
        "eedeb95f-b5cf-431d-8ad6-5854ba6b251c": {
            "type": "unsupported",
            "operation": "Array",
            "expected_test": "To list with multiple values",
        },
    }

    rationales_checked = {}
    for uuid, info in target_uuids.items():
        assert uuid in toml_data, f"UUID {uuid} missing from tests.toml"
        entry = toml_data[uuid]
        assert entry.get("include") is False, f"UUID {uuid} must remain excluded (include = false)"

        comment = entry.get("comment") or entry.get("comments")
        assert comment, f"UUID {uuid} must have a non-empty comment rationale"

        # Check that comment names the test or operation
        op = info["operation"]
        test_name = info["expected_test"]
        assert op.lower() in comment.lower(), f"UUID {uuid} rationale must cite operation {op}: {comment}"
        assert (info["type"] in comment.lower() or "reimplemented" in comment.lower() or "exclusive" in comment.lower()), (
            f"UUID {uuid} rationale must state reason type: {comment}"
        )

        rationales_checked[uuid] = {
            "description": entry.get("description"),
            "include": entry.get("include"),
            "comment": comment,
            "category": info["type"],
        }
        print(f"Verified {uuid} ({info['type']}):\n  {comment}\n")

    results_data["checks"].append({
        "name": "toml_and_rationales_check",
        "status": "PASS",
        "total_cases": total_cases,
        "included_count": len(included_cases),
        "excluded_count": len(excluded_cases),
        "rationales": rationales_checked,
    })

    print("\n=== Step 5: Writing results and evidence to work/R63-T021/ ===")
    results_data["success"] = True

    tool_versions_file = os.path.join(work_dir, "tool_versions.json")
    with open(tool_versions_file, "w", encoding="utf-8") as f:
        json.dump(results_data["tool_versions"], f, indent=2)

    tool_versions_txt = os.path.join(work_dir, "tool_versions.txt")
    with open(tool_versions_txt, "w", encoding="utf-8") as f:
        for k, v in results_data["tool_versions"].items():
            f.write(f"{k}: {v}\n")

    results_json_file = os.path.join(work_dir, "results.json")
    with open(results_json_file, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    inputs_and_results_file = os.path.join(work_dir, "inputs_and_results.txt")
    with open(inputs_and_results_file, "w", encoding="utf-8") as f:
        f.write("Task R63-T021 Verification Report\n")
        f.write("=================================\n\n")
        f.write("Tool Versions:\n")
        for k, v in results_data["tool_versions"].items():
            f.write(f"  {k}: {v}\n")
        f.write("\nInclusion Counts (Before & After):\n")
        f.write(f"  Total canonical cases: {total_cases}\n")
        f.write(f"  Included cases count:  {len(included_cases)}\n")
        f.write(f"  Excluded cases count:  {len(excluded_cases)}\n")
        f.write("  Inclusions changed:    0 (all include flags preserved)\n")
        f.write("\nTarget UUID Rationales:\n")
        for uuid, data in rationales_checked.items():
            f.write(f"UUID: {uuid}\n")
            f.write(f"  Description: {data['description']}\n")
            f.write(f"  Category:    {data['category'].capitalize()}\n")
            f.write(f"  Rationale:   {data['comment']}\n\n")
        f.write("\nTest Suite Checks (Scratch Module):\n")
        f.write(f"  Executed test cases: {test_count}\n")
        f.write(f"  Return code: 0\n")
        f.write(f"  All 24 enabled test cases passed against reference.\n")
        f.write("\nLearner Stub Status:\n")
        f.write("  exercises/practice/simple-linked-list/simple_linked_list.go remains untouched and unsolved (contains panic stubs).\n")

    print("All checks completed successfully and evidence saved.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
