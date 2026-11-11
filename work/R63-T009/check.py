#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def compute_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    work_dir = Path(__file__).resolve().parent
    exercise_rel = "exercises/practice/clock"
    exercise_path = repo_root / exercise_rel
    config_file = exercise_path / ".meta" / "config.json"
    runner_script = repo_root / "tools" / "course_checks" / "r63-t009.py"

    print("=== [R63-T009] Automated Check ===")

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
    if not solution_files:
        raise AssertionError("Missing solution files in config.json")
    solution_filename = solution_files[0]
    learner_path = exercise_path / solution_filename

    # 3. Assert learner stub remains unsolved
    if not learner_path.exists():
        raise AssertionError(f"Learner solution file {learner_path} does not exist")
    with open(learner_path, "r") as f:
        learner_content = f.read()
    if 'panic("Please implement the New function")' not in learner_content:
        raise AssertionError("Learner solution stub appears modified or solved! It must remain unsolved.")
    print("✔ Confirmed learner stub is unsolved.")

    initial_hash = compute_hash(learner_path)
    print(f"Initial learner file hash: {initial_hash}")

    # 4. Test real mode
    print("Testing real reference execution...")
    res_real = subprocess.run([sys.executable, str(runner_script), "--mode", "real"], capture_output=True, text=True)
    print(res_real.stdout)
    if res_real.returncode != 0:
        print("STDERR:\n", res_real.stderr)
        raise AssertionError(f"Runner real mode failed with exit code {res_real.returncode}")

    # 5. Test failing reference mode
    print("Testing deliberate failing reference...")
    res_failing = subprocess.run([sys.executable, str(runner_script), "--mode", "failing"], capture_output=True, text=True)
    print(res_failing.stdout)
    if res_failing.returncode != 0:
        print("STDERR:\n", res_failing.stderr)
        raise AssertionError(f"Runner failing mode check failed: {res_failing.stderr}")

    # 6. Test zero-test mode
    print("Testing zero-test detection...")
    res_zero = subprocess.run([sys.executable, str(runner_script), "--mode", "zero-test"], capture_output=True, text=True)
    print(res_zero.stdout)
    if res_zero.returncode != 0:
        print("STDERR:\n", res_zero.stderr)
        raise AssertionError(f"Runner zero-test mode check failed: {res_zero.stderr}")

    # 7. Final hash verification
    final_hash = compute_hash(learner_path)
    print(f"Final learner file hash:   {final_hash}")
    if initial_hash != final_hash:
        raise AssertionError("Learner file hash changed after test suite execution!")
    print("✔ Learner file hashes are 100% identical before and after all test runs.")

    # 8. Save results
    results_data = {
        "task_id": "R63-T009",
        "exercise": exercise_rel,
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "learner_file_hash": initial_hash,
        "hash_verified_identical": True,
        "runner_modes_tested": ["real", "failing", "zero-test"],
        "status": "PASS"
    }

    with open(work_dir / "results.json", "w") as f:
        json.dump(results_data, f, indent=2)

    print("✔ All assertions passed successfully. Results saved to work/R63-T009/results.json")

if __name__ == "__main__":
    main()
