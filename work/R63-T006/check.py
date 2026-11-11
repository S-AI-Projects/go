#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    work_dir = Path(__file__).resolve().parent
    exercise_rel = "exercises/practice/parallel-letter-frequency"
    exercise_path = repo_root / exercise_rel
    config_file = exercise_path / ".meta" / "config.json"
    hints_file = exercise_path / ".docs" / "hints.md"
    alternative_file = work_dir / "alternative.go"

    print("=== [R63-T006] Automated Check ===")

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
    if 'panic("Implement the Frequency function")' not in learner_content:
        raise AssertionError("Learner solution stub appears modified or solved! It must remain unsolved.")
    print("✔ Confirmed learner stub is unsolved.")

    # 4. Assert hints.md contains approach selection and worked example
    if not hints_file.exists():
        raise AssertionError("hints.md not found in .docs")
    with open(hints_file, "r") as f:
        hints_content = f.read()
    if "Fan-Out / Fan-In" not in hints_content or "Disjoint Slice Indexing" not in hints_content:
        raise AssertionError("hints.md missing two approaches explanation")
    if "cat" not in hints_content or "car" not in hints_content:
        raise AssertionError("hints.md missing small worked input example")
    print("✔ hints.md approach comparison and worked example validated.")

    # 5. Test Approach 1: Channel-based reference implementation
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "exercise"
        shutil.copytree(exercise_path, tmp_exercise, symlinks=True)

        target_solution = tmp_exercise / solution_filename
        shutil.copyfile(tmp_exercise / example_filename, target_solution)

        cmd = ["go", "test", "-count=1", "-v", "./..."]
        proc_ref = subprocess.run(cmd, cwd=tmp_exercise, capture_output=True, text=True)

        if proc_ref.returncode != 0:
            print("STDERR:\n", proc_ref.stderr)
            raise AssertionError(f"Reference implementation failed tests! exit code: {proc_ref.returncode}")

        executed_tests_ref = [l.strip() for l in proc_ref.stdout.splitlines() if l.strip().startswith("--- PASS:")]
        print(f"✔ Approach 1 (Channel Reference) PASSED all {len(executed_tests_ref)} tests.")

    # 6. Test Approach 2: Disjoint slice indexing alternative implementation
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "exercise"
        shutil.copytree(exercise_path, tmp_exercise, symlinks=True)

        target_solution = tmp_exercise / solution_filename
        shutil.copyfile(alternative_file, target_solution)

        cmd = ["go", "test", "-count=1", "-v", "./..."]
        proc_alt = subprocess.run(cmd, cwd=tmp_exercise, capture_output=True, text=True)

        if proc_alt.returncode != 0:
            print("STDERR:\n", proc_alt.stderr)
            raise AssertionError(f"Alternative implementation failed tests! exit code: {proc_alt.returncode}")

        executed_tests_alt = [l.strip() for l in proc_alt.stdout.splitlines() if l.strip().startswith("--- PASS:")]
        print(f"✔ Approach 2 (Slice WaitGroup Alternative) PASSED all {len(executed_tests_alt)} tests.")

    if len(executed_tests_ref) == 0 or len(executed_tests_alt) == 0:
        raise AssertionError("Zero tests executed! Verification failed.")

    # 7. Save check results to work/R63-T006/results.json
    results_data = {
        "task_id": "R63-T006",
        "exercise": exercise_rel,
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "approach_1_channel": {
            "exit_code": proc_ref.returncode,
            "pass_count": len(executed_tests_ref)
        },
        "approach_2_slice_wg": {
            "exit_code": proc_alt.returncode,
            "pass_count": len(executed_tests_alt)
        },
        "status": "PASS"
    }

    with open(work_dir / "results.json", "w") as f:
        json.dump(results_data, f, indent=2)

    print("✔ All assertions passed successfully. Results saved to work/R63-T006/results.json")

if __name__ == "__main__":
    main()
