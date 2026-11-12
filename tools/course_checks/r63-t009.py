#!/usr/bin/env python3
"""
Isolated test runner for clock (R63-T009).
Runs reference implementation in an isolated temporary directory, reports real case
count, propagates failures, and verifies learner files remain untouched via SHA-256 hashing.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_isolated_test(exercise_dir: Path, mode: str = "real") -> dict:
    config_file = exercise_dir / ".meta" / "config.json"
    if not config_file.exists():
        raise FileNotFoundError(f"config.json not found at {config_file}")

    with open(config_file, "r") as f:
        config = json.load(f)

    solution_file = config["files"]["solution"][0]
    example_file = config["files"]["example"][0]

    learner_path = exercise_dir / solution_file
    hash_before = compute_file_hash(learner_path)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_exercise = Path(tmpdir) / "exercise"
            shutil.copytree(exercise_dir, tmp_exercise, symlinks=True)

            target_solution = tmp_exercise / solution_file
            if mode == "real":
                shutil.copyfile(tmp_exercise / example_file, target_solution)
            elif mode == "failing":
                # Deliberate failure: replace example with one that produces wrong clock calculation
                with open(tmp_exercise / example_file, "r") as f:
                    orig_ex = f.read()
                failing_ex = orig_ex.replace("h*60 + m", "h*60 + m + 999")
                with open(target_solution, "w") as f:
                    f.write(failing_ex)
            elif mode == "zero-test":
                shutil.copyfile(tmp_exercise / example_file, target_solution)

            cmd = ["go", "test", "-count=1", "-v"]
            if mode == "zero-test":
                # Filter to non-matching test name to produce zero tests
                cmd.extend(["-run", "^$"])
            else:
                cmd.append("./...")

            proc = subprocess.run(cmd, cwd=tmp_exercise, capture_output=True, text=True)

            executed_tests = [l.strip() for l in proc.stdout.splitlines() if l.strip().startswith("--- PASS:") or l.strip().startswith("--- FAIL:")]
            case_count = len(executed_tests)

            return {
                "exit_code": proc.returncode,
                "case_count": case_count,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "executed_tests": executed_tests
            }
    finally:
        hash_after = compute_file_hash(learner_path)
        if hash_before != hash_after:
            raise AssertionError(f"FATAL: Learner file {learner_path} was modified during run! Hash changed: {hash_before} -> {hash_after}")

def main():
    parser = argparse.ArgumentParser(description="Isolated runner for clock")
    parser.add_argument("--mode", choices=["real", "failing", "zero-test"], default="real")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    exercise_dir = repo_root / "exercises" / "practice" / "clock"

    print(f"=== [tools/course_checks/r63-t009.py] Running Isolated Clock Runner (mode={args.mode}) ===")
    res = run_isolated_test(exercise_dir, mode=args.mode)
    print(f"Run completed with exit code {res['exit_code']}, cases executed: {res['case_count']}")

    if args.mode == "real":
        if res["exit_code"] != 0:
            print("STDERR:\n", res["stderr"], file=sys.stderr)
            sys.exit(res["exit_code"])
        if res["case_count"] == 0:
            print("ERROR: Zero tests were executed!", file=sys.stderr)
            sys.exit(1)
        print(f"✔ Real reference passed all {res['case_count']} test cases successfully.")
    elif args.mode == "failing":
        if res["exit_code"] == 0:
            print("ERROR: Failing reference unexpectedly passed!", file=sys.stderr)
            sys.exit(1)
        print("✔ Failing reference correctly produced non-zero exit code.")
    elif args.mode == "zero-test":
        if res["case_count"] != 0:
            print("ERROR: Zero-test mode executed tests unexpectedly!", file=sys.stderr)
            sys.exit(1)
        print("✔ Zero-test mode detected zero test execution.")

if __name__ == "__main__":
    main()
