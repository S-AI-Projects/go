#!/usr/bin/env python3
"""
Reproducibility check for twelve days test generation (R63-T042).
This script checks that running the test generator twice produces
identical results after timestamp and commit normalization.
"""

import difflib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def normalize_text(text):
    """Normalize commit header and timestamp lines for reproducibility comparison."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("// Commit:"):
            lines.append("// Commit: normalized")
        elif stripped.startswith("// Generated") or "timestamp" in stripped.lower():
            lines.append("// Generated timestamp: normalized")
        else:
            lines.append(line.rstrip())
    return "\n".join(lines).strip()


def run_generator_in_temp_dir(repo_root):
    """Set up a fresh temporary directory, run gen.go, and return the generated content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Copy the required folders to run the generator
        shutil.copytree(repo_root / "gen", temp_path / "gen")
        shutil.copytree(repo_root / "gotools", temp_path / "gotools")
        shutil.copytree(
            repo_root / "exercises" / "practice" / "twelve-days",
            temp_path / "exercises" / "practice" / "twelve-days",
        )

        target_exercise = temp_path / "exercises" / "practice" / "twelve-days"
        cases_file = target_exercise / "cases_test.go"

        # Remove existing cases_test.go to verify new generation
        if cases_file.exists():
            cases_file.unlink()

        gen_cmd = ["go", "run", "./exercises/practice/twelve-days/.meta/gen.go"]
        gen_env = dict(os.environ, GO111MODULE="off")

        proc = subprocess.run(
            gen_cmd,
            cwd=temp_path,
            env=gen_env,
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            print("Generator failed with exit code:", proc.returncode)
            print("STDOUT:", proc.stdout)
            print("STDERR:", proc.stderr)
            raise AssertionError("Generator run failed with exit code " + str(proc.returncode))

        if not cases_file.exists():
            raise AssertionError("Generator did not produce cases_test.go")

        return cases_file.read_text(encoding="utf-8")


def check_tests_toml(repo_root):
    """Verify that tests.toml has comments for the multi verse cases."""
    toml_path = repo_root / "exercises" / "practice" / "twelve-days" / ".meta" / "tests.toml"
    if not toml_path.exists():
        raise AssertionError("tests.toml not found at " + str(toml_path))

    content = toml_path.read_text(encoding="utf-8")
    target_uuids = [
        "da8b9013-b1e8-49df-b6ef-ddec0219e398",
        "c095af0d-3137-4653-ad32-bfb899eda24c",
        "20921bc9-cc52-4627-80b3-198cbbfcf9b7",
    ]

    for uid in target_uuids:
        if uid not in content:
            raise AssertionError("Missing UUID in tests.toml: " + uid)

    print("All target multi verse UUIDs are present in tests.toml.")


def check_reproducibility():
    """Run two generations and check for identical outputs after normalization."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    exercise_path = repo_root / "exercises" / "practice" / "twelve-days"
    original_cases_path = exercise_path / "cases_test.go"

    if not original_cases_path.exists():
        raise AssertionError("Original cases_test.go not found at " + str(original_cases_path))

    original_cases = original_cases_path.read_text(encoding="utf-8")

    # Verify tests.toml comments
    check_tests_toml(repo_root)

    print("Running generation 1 in fresh temporary directory...")
    output1 = run_generator_in_temp_dir(repo_root)

    print("Running generation 2 in fresh temporary directory...")
    output2 = run_generator_in_temp_dir(repo_root)

    norm1 = normalize_text(output1)
    norm2 = normalize_text(output2)
    norm_orig = normalize_text(original_cases)

    # Check 1: Run 1 and Run 2 are identical after normalization
    if norm1 != norm2:
        diff = difflib.unified_diff(
            norm1.splitlines(keepends=True),
            norm2.splitlines(keepends=True),
            fromfile="run1",
            tofile="run2",
        )
        print("Differences between run 1 and run 2:")
        print("".join(diff))
        raise AssertionError("Generation runs 1 and 2 produced different outputs")

    print("Generation runs 1 and 2 produced identical normalized results.")

    # Check 2: Output matches the committed cases_test.go
    if norm1 != norm_orig:
        diff = difflib.unified_diff(
            norm_orig.splitlines(keepends=True),
            norm1.splitlines(keepends=True),
            fromfile="original",
            tofile="generated",
        )
        print("Differences between original and generated:")
        print("".join(diff))
        raise AssertionError("Generated output does not match committed cases_test.go")

    print("Generated output matches committed cases_test.go perfectly.")

    # Check 3: Check case count (12 testCases and 12 song lines)
    if "var testCases = []testCase{" not in output1:
        raise AssertionError("testCases slice not found in generated output")

    if "var song = []string{" not in output1:
        raise AssertionError("song slice not found in generated output")

    verse_count = output1.count("description:")
    if verse_count != 12:
        raise AssertionError("Expected 12 verses in testCases, found " + str(verse_count))

    print("Verified all 12 verses are present. No cases were dropped.")

    return {
        "status": "PASS",
        "verse_count": verse_count,
        "runs_identical": True,
        "matches_original": True,
    }


def main():
    print("Starting reproducibility check for twelve days (R63-T042)...")
    res = check_reproducibility()
    print("Reproducibility check finished successfully.")
    print("Status:", res["status"])


if __name__ == "__main__":
    main()
