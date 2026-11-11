#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    work_dir = Path(__file__).resolve().parent
    exercise_rel = "exercises/practice/beer-song"
    exercise_path = repo_root / exercise_rel
    config_file = exercise_path / ".meta" / "config.json"
    tests_toml_file = exercise_path / ".meta" / "tests.toml"

    print("=== [R63-T001] Automated Check ===")

    # 1. Collect tool versions
    go_ver = subprocess.check_output(["go", "version"], text=True).strip()
    py_ver = sys.version.replace("\n", " ")
    print(f"Tool versions: {go_ver} | Python: {py_ver}")
    with open(work_dir / "tool_versions.txt", "w") as f:
        f.write(f"Go: {go_ver}\nPython: {py_ver}\n")

    # 2. Check config.json exists and load paths
    if not config_file.exists():
        raise AssertionError(f"config.json not found at {config_file}")
    with open(config_file, "r") as f:
        config = json.load(f)

    solution_files = config.get("files", {}).get("solution", [])
    test_files = config.get("files", {}).get("test", [])
    example_files = config.get("files", {}).get("example", [])

    if not solution_files or not example_files:
        raise AssertionError("Missing solution or example files in config.json")

    solution_filename = solution_files[0]
    example_filename = example_files[0]

    # 3. Assert learner stub remains unsolved
    learner_solution_path = exercise_path / solution_filename
    if not learner_solution_path.exists():
        raise AssertionError(f"Learner solution file {learner_solution_path} does not exist")
    with open(learner_solution_path, "r") as f:
        learner_content = f.read()
    if 'panic("Please implement' not in learner_content:
        raise AssertionError("Learner solution stub appears modified or solved! It must remain unsolved.")
    print("✔ Confirmed learner stub is unsolved.")

    # 4. Verify tests.toml parsing and rationale for selected UUIDs
    with open(tests_toml_file, "rb") as f:
        toml_data = tomllib.load(f)

    target_uuids = [
        "5a02fd08-d336-4607-8006-246fe6fa9fb0",
        "77299ca6-545e-4217-a9cc-606b342e0187",
        "102cbca0-b197-40fd-b548-e99609b06428",
    ]

    total_cases = len(toml_data)
    excluded_cases = [k for k, v in toml_data.items() if isinstance(v, dict) and not v.get("include", True)]
    included_cases = total_cases - len(excluded_cases)

    print(f"Total canonical cases in TOML: {total_cases} (Included: {included_cases}, Excluded: {len(excluded_cases)})")

    uuids_checked = {}
    for uuid in target_uuids:
        if uuid not in toml_data:
            raise AssertionError(f"Target UUID {uuid} missing from tests.toml")
        entry = toml_data[uuid]
        comment = entry.get("comment", "")
        if not comment or len(comment.strip()) < 10:
            raise AssertionError(f"UUID {uuid} lacks an explanatory rationale in comment key")
        # Check that comment mentions tests or language limitation
        if not any(word in comment for word in ["Verse", "Song", "Test", "Go", "Canonical"]):
            raise AssertionError(f"UUID {uuid} comment does not cite the relevant Go operation or test")
        uuids_checked[uuid] = {
            "description": entry.get("description", ""),
            "comment": comment
        }
        print(f"✔ Validated rationale for UUID {uuid}: {comment[:60]}...")

    # 5. Execute reference in an isolated scratch directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "exercise"
        # Copy exercise directory including dotfiles
        shutil.copytree(exercise_path, tmp_exercise, symlinks=True)

        # Substitute the reference implementation into the solution filename
        example_path = tmp_exercise / example_filename
        target_solution = tmp_exercise / solution_filename
        if not example_path.exists():
            raise AssertionError(f"Example file {example_path} does not exist in temporary copy")
        shutil.copyfile(example_path, target_solution)

        # Run go test -count=1 -v ./...
        cmd = ["go", "test", "-count=1", "-v", "./..."]
        proc = subprocess.run(cmd, cwd=tmp_exercise, capture_output=True, text=True)

        print("=== Test Output Preview ===")
        print(proc.stdout[:400] + ("..." if len(proc.stdout) > 400 else ""))

        if proc.returncode != 0:
            print("STDERR:\n", proc.stderr)
            raise AssertionError(f"go test failed with non-zero exit code: {proc.returncode}")

        # Parse test results
        executed_tests = []
        for line in proc.stdout.splitlines():
            line_s = line.strip()
            if line_s.startswith("--- PASS:") or line_s.startswith("--- FAIL:"):
                executed_tests.append(line_s)

        case_count = len(executed_tests)
        print(f"Executed test count: {case_count}")
        if case_count == 0:
            raise AssertionError("Zero tests executed! Verification failed.")

    # 6. Save check results to work/R63-T001/results.json
    results_data = {
        "task_id": "R63-T001",
        "exercise": exercise_rel,
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "tests_toml_stats": {
            "total": total_cases,
            "included": included_cases,
            "excluded": len(excluded_cases)
        },
        "target_uuids_rationale": uuids_checked,
        "test_run": {
            "exit_code": proc.returncode,
            "executed_cases_count": case_count,
            "executed_tests": executed_tests
        },
        "status": "PASS"
    }

    with open(work_dir / "results.json", "w") as f:
        json.dump(results_data, f, indent=2)

    print("✔ All assertions passed successfully. Results saved to work/R63-T001/results.json")

if __name__ == "__main__":
    main()
