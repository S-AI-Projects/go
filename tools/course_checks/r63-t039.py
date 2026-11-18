#!/usr/bin/env python3
"""Isolated test runner for R63-T039 (exercises/practice/accumulate)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ACCUMULATE_DIR = REPO_ROOT / "exercises" / "practice" / "accumulate"
CONFIG_PATH = ACCUMULATE_DIR / ".meta" / "config.json"


def compute_file_hashes(directory: Path) -> dict[str, str]:
    """Computes SHA-256 hashes of all files in directory relative to directory root."""
    hashes: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(directory))
            h = hashlib.sha256()
            h.update(path.read_bytes())
            hashes[rel] = h.hexdigest()
    return hashes


def run_isolated_test(
    exercise_dir: Path,
    solution_override: Path | None = None,
    test_run_flag: str | None = None,
) -> dict[str, Any]:
    """Runs tests in an isolated temporary copy without modifying the exercise directory.
    
    1. Computes hashes of learner files before execution.
    2. Copies the exercise into a temporary directory.
    3. Resolves files from .meta/config.json and sets up the solution.
    4. Executes 'go test -count=1 ./...'.
    5. Cleans up the temporary directory.
    6. Asserts learner file hashes are unchanged.
    """
    hashes_before = compute_file_hashes(exercise_dir)

    with open(exercise_dir / ".meta" / "config.json", encoding="utf-8") as f:
        config = json.load(f)

    files_cfg = config.get("files", {})
    solution_rel = files_cfg["solution"][0]
    example_rel = files_cfg["example"][0]

    with tempfile.TemporaryDirectory(prefix="r63-t039-accumulate-") as tmp_root:
        scratch_dir = Path(tmp_root) / "accumulate"
        shutil.copytree(exercise_dir, scratch_dir, symlinks=True)

        # Substitute solution in the temporary directory only
        if solution_override is not None:
            shutil.copy2(solution_override, scratch_dir / solution_rel)
        else:
            shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)

        cmd = ["go", "test", "-v", "-count=1"]
        if test_run_flag:
            cmd.extend(["-run", test_run_flag])
        cmd.append("./...")

        proc = subprocess.run(cmd, cwd=scratch_dir, capture_output=True, text=True)
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode

    # Check hashes after cleanup
    hashes_after = compute_file_hashes(exercise_dir)
    hashes_preserved = (hashes_before == hashes_after)

    zero_tests = "[no tests to run]" in stdout or "warning: no tests to run" in stderr or "PASS: Test" not in stdout
    tests_passed = "PASS: Test" in stdout and exit_code == 0 and not zero_tests

    return {
        "command": cmd,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "hashes_preserved": hashes_preserved,
        "zero_tests": zero_tests,
        "tests_passed": tests_passed,
        "hashes_before": hashes_before,
        "hashes_after": hashes_after,
    }


def main() -> int:
    print(f"Running isolated tests for {ACCUMULATE_DIR.name}...")
    res = run_isolated_test(ACCUMULATE_DIR)

    if not res["hashes_preserved"]:
        print("ERROR: Working tree learner files were modified during the run!", file=sys.stderr)
        return 1

    if res["zero_tests"]:
        print("ERROR: Zero tests were executed during the run!", file=sys.stderr)
        return 1

    if not res["tests_passed"] or res["exit_code"] != 0:
        print(f"ERROR: Test execution failed with exit code {res['exit_code']}", file=sys.stderr)
        print(res["stdout"], file=sys.stderr)
        return res["exit_code"] if res["exit_code"] != 0 else 1

    print("SUCCESS: Reference implementation passed all tests in isolated environment.")
    print("SUCCESS: Working tree files verified completely unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
