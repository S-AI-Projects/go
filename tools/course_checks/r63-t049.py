#!/usr/bin/env python3
"""Isolated test runner for diamond (R63-T049)."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DIAMOND_DIR = REPO_ROOT / "exercises" / "practice" / "diamond"
CONFIG_PATH = DIAMOND_DIR / ".meta" / "config.json"

def compute_file_hashes(directory):
    """Computes SHA-256 hashes of all files in directory."""
    hashes = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(directory))
            h = hashlib.sha256()
            h.update(path.read_bytes())
            hashes[rel] = h.hexdigest()
    return hashes

def run_isolated_test(exercise_dir, solution_override=None, test_run_flag=None):
    """Runs tests in an isolated temporary copy without modifying the exercise directory."""
    hashes_before = compute_file_hashes(exercise_dir)

    with open(exercise_dir / ".meta" / "config.json", encoding="utf-8") as f:
        config = json.load(f)

    files_cfg = config.get("files", {})
    solution_rel = files_cfg["solution"][0]
    example_rel = files_cfg["example"][0]

    with tempfile.TemporaryDirectory(prefix="r63-t049-diamond-") as tmp_root:
        scratch_dir = Path(tmp_root) / "diamond"
        shutil.copytree(exercise_dir, scratch_dir, symlinks=True)

        if solution_override is not None:
            shutil.copy2(solution_override, scratch_dir / solution_rel)
        else:
            shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)

        cmd = ["go", "test", "-v", "-count=1"]
        if test_run_flag:
            cmd.extend(["-run", test_run_flag])
        cmd.append("./...")

        proc = subprocess.run(cmd, cwd=scratch_dir, capture_output=True, text=True)

    hashes_after = compute_file_hashes(exercise_dir)
    hashes_preserved = (hashes_before == hashes_after)

    passed_subtests = []
    failed_subtests = []
    for line in proc.stdout.splitlines():
        line_s = line.strip()
        if line_s.startswith("--- PASS:"):
            parts = line_s.split()
            if len(parts) >= 3:
                passed_subtests.append(parts[2])
        elif line_s.startswith("--- FAIL:"):
            parts = line_s.split()
            if len(parts) >= 3:
                failed_subtests.append(parts[2])

    zero_tests = (len(passed_subtests) == 0 and len(failed_subtests) == 0)
    tests_passed = (proc.returncode == 0 and len(passed_subtests) > 0 and len(failed_subtests) == 0)

    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "passed_tests": passed_subtests,
        "failed_tests": failed_subtests,
        "passed_count": len(passed_subtests),
        "failed_count": len(failed_subtests),
        "zero_tests": zero_tests,
        "tests_passed": tests_passed,
        "hashes_preserved": hashes_preserved
    }

def main():
    res = run_isolated_test(DIAMOND_DIR)
    if not res["hashes_preserved"]:
        print("FAIL: Learner files were modified during isolated run!", file=sys.stderr)
        sys.exit(2)
    if res["zero_tests"]:
        print("FAIL: Zero tests executed!", file=sys.stderr)
        sys.exit(3)
    if not res["tests_passed"]:
        print(f"FAIL: Tests failed with exit code {res['exit_code']}", file=sys.stderr)
        print(res["stdout"])
        print(res["stderr"], file=sys.stderr)
        sys.exit(res["exit_code"])

    print(f"PASS: Isolated runner executed {res['passed_count']} tests cleanly. Learner files preserved.")

if __name__ == "__main__":
    main()
