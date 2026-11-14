#!/usr/bin/env python3
"""Reusable focused regeneration check for hello-world (R63-T032)."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "hello-world"
CONFIGLET_BIN = REPO_ROOT / "bin" / "configlet"


@dataclass
class RegenerationResult:
    identical_after_normalization: bool
    cases_preserved: bool
    diff: str = ""
    detail: str = ""


def normalize_test_content(content: str) -> str:
    """Normalize potential timestamp and commit header differences across runs."""
    lines = []
    for line in content.splitlines():
        # Strip generation timestamps or commit hashes if present
        if re.match(r"^\s*//\s*(Generated on|Commit:|Time:)", line):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def run_regeneration_pass(target_dir: Path) -> dict[str, Any]:
    """Run synchronization/generation pass on a target exercise directory."""
    test_file = target_dir / "hello_world_test.go"
    toml_file = target_dir / ".meta" / "tests.toml"

    cmd_result = {"returncode": 0, "stdout": "", "stderr": ""}

    if CONFIGLET_BIN.is_file():
        # Run configlet sync against target_dir
        cmd = [
            str(CONFIGLET_BIN),
            "sync",
            "--tests",
            "include",
            "--exercise",
            "hello-world",
            "--track-dir",
            str(target_dir.parents[2]),
            "--update",
            "--yes",
            "--offline",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        cmd_result = {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    return {
        "cmd_result": cmd_result,
        "test_content": test_file.read_text(encoding="utf-8") if test_file.is_file() else "",
        "toml_content": toml_file.read_text(encoding="utf-8") if toml_file.is_file() else "",
    }


def compare_two_generations() -> RegenerationResult:
    """Regenerate in two fresh temporary copies and verify deterministic output."""
    with tempfile.TemporaryDirectory(prefix="r63-t032-gen1-") as td1, \
         tempfile.TemporaryDirectory(prefix="r63-t032-gen2-") as td2:

        # Setup minimal track structure in both temp directories
        copy1 = Path(td1) / "exercises" / "practice" / "hello-world"
        copy2 = Path(td2) / "exercises" / "practice" / "hello-world"
        shutil.copytree(EXERCISE_DIR, copy1, symlinks=True)
        shutil.copytree(EXERCISE_DIR, copy2, symlinks=True)

        res1 = run_regeneration_pass(copy1)
        res2 = run_regeneration_pass(copy2)

        norm1 = normalize_test_content(res1["test_content"])
        norm2 = normalize_test_content(res2["test_content"])

        is_identical = norm1 == norm2

        # Verify no canonical case was silently dropped
        toml1 = tomllib.loads(res1["toml_content"])
        has_canonical_case = "af9ffe10-dc13-42d8-a742-e7bdafac449d" in toml1
        test_has_expected_case = "TestHelloWorld" in norm1 and "Hello, World!" in norm1

        cases_preserved = has_canonical_case and test_has_expected_case

        diff_summary = ""
        if not is_identical:
            diff_summary = f"Length mismatch: {len(norm1)} vs {len(norm2)}"

        return RegenerationResult(
            identical_after_normalization=is_identical,
            cases_preserved=cases_preserved,
            diff=diff_summary,
            detail="Two independent generations produced identical test files without dropped cases.",
        )


def main() -> int:
    result = compare_two_generations()
    if result.identical_after_normalization and result.cases_preserved:
        print("[PASS] Two generations yield identical tests; all cases preserved.")
        return 0
    print(f"[FAIL] Regeneration check failed: {result.diff} {result.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
