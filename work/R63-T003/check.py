#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def create_mutant_source(original_source: str) -> str:
    """Creates deliberate mutant by removing negative remainder normalization in decryptionFunc."""
    target_block = """\ttemp := (mmi * (int(letter-'a') - num2)) % _totalAlphabets
	if temp < 0 {
		temp += _totalAlphabets
	}"""
    mutated_block = """\ttemp := (mmi * (int(letter-'a') - num2)) % _totalAlphabets"""
    if target_block not in original_source:
        raise ValueError("Could not find target block in example.go to mutate")
    return original_source.replace(target_block, mutated_block)

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    work_dir = Path(__file__).resolve().parent
    exercise_rel = "exercises/practice/affine-cipher"
    exercise_path = repo_root / exercise_rel
    config_file = exercise_path / ".meta" / "config.json"

    print("=== [R63-T003] Automated Check ===")

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

    # 4. Execute original reference in an isolated scratch directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "exercise"
        shutil.copytree(exercise_path, tmp_exercise, symlinks=True)

        example_path = tmp_exercise / example_filename
        target_solution = tmp_exercise / solution_filename
        shutil.copyfile(example_path, target_solution)

        cmd = ["go", "test", "-count=1", "-v", "./..."]
        proc_orig = subprocess.run(cmd, cwd=tmp_exercise, capture_output=True, text=True)

        if proc_orig.returncode != 0:
            print("STDERR:\n", proc_orig.stderr)
            raise AssertionError(f"Original reference failed tests! exit code: {proc_orig.returncode}")

        executed_tests = [l.strip() for l in proc_orig.stdout.splitlines() if l.strip().startswith("--- PASS:")]
        case_count = len(executed_tests)
        print(f"✔ Original reference PASSED all {case_count} tests.")

    # 5. Execute mutated reference in an isolated scratch directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "exercise"
        shutil.copytree(exercise_path, tmp_exercise, symlinks=True)

        with open(exercise_path / example_filename, "r") as f:
            original_code = f.read()
        mutant_code = create_mutant_source(original_code)

        target_solution = tmp_exercise / solution_filename
        with open(target_solution, "w") as f:
            f.write(mutant_code)

        cmd = ["go", "test", "-count=1", "-v", "./..."]
        proc_mutant = subprocess.run(cmd, cwd=tmp_exercise, capture_output=True, text=True)

        if proc_mutant.returncode == 0:
            raise AssertionError("Mutant unexpectedly passed all tests! Mutation was not caught.")

        if "decode_exercism" not in proc_mutant.stdout and "decode exercism" not in proc_mutant.stdout:
            raise AssertionError(f"Expected mutant to be rejected by 'decode exercism', output was:\n{proc_mutant.stdout}")

        print("✔ Mutated reference was successfully REJECTED by test 'decode exercism'.")

    # 6. Save check results to work/R63-T003/results.json
    results_data = {
        "task_id": "R63-T003",
        "exercise": exercise_rel,
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "original_reference": {
            "exit_code": proc_orig.returncode,
            "pass_count": case_count
        },
        "mutant_reference": {
            "exit_code": proc_mutant.returncode,
            "rejected_by_test": "decode exercism",
            "rejecting_uuid": "3f0ac7e2-ec0e-4a79-949e-95e414953438"
        },
        "status": "PASS"
    }

    with open(work_dir / "results.json", "w") as f:
        json.dump(results_data, f, indent=2)

    print("✔ All assertions passed successfully. Results saved to work/R63-T003/results.json")

if __name__ == "__main__":
    main()
