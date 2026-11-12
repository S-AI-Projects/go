#!/usr/bin/env python3
"""
Path and configuration checker for spiral-matrix (R63-T008).
Validates that all files declared in .meta/config.json resolve safely
inside the exercise directory and tests invalid fixtures for parent traversal,
missing test files, and missing reference files.
"""
import copy
import json
import os
import sys
from pathlib import Path

def validate_config(exercise_dir: Path, config_data: dict) -> None:
    """Validates files object in config_data relative to exercise_dir."""
    files_obj = config_data.get("files", {})
    if not files_obj:
        raise ValueError("Missing 'files' object in configuration")

    required_keys = ["solution", "test", "example"]
    for k in required_keys:
        if k not in files_obj or not files_obj[k]:
            raise ValueError(f"Missing required key '{k}' in files object")

    for category, file_list in files_obj.items():
        for rel_path_str in file_list:
            # 1. Reject absolute paths or parent directory traversal
            p = Path(rel_path_str)
            if p.is_absolute():
                raise PermissionError(f"Security violation: absolute path '{rel_path_str}' is forbidden")
            if ".." in p.parts:
                raise PermissionError(f"Security violation: parent directory traversal '..' detected in '{rel_path_str}'")

            # 2. Resolve target path
            full_path = (exercise_dir / p).resolve()
            # Ensure full_path is strictly within exercise_dir
            try:
                full_path.relative_to(exercise_dir.resolve())
            except ValueError:
                raise PermissionError(f"Security violation: path '{rel_path_str}' escapes exercise root")

            # 3. Check file exists
            if not full_path.exists():
                raise FileNotFoundError(f"Declared file '{rel_path_str}' does not exist on disk at {full_path}")
            if not full_path.is_file():
                raise IsADirectoryError(f"Declared path '{rel_path_str}' is not a regular file")

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    exercise_dir = repo_root / "exercises" / "practice" / "spiral-matrix"
    config_file = exercise_dir / ".meta" / "config.json"

    print("=== [tools/course_checks/r63-t008.py] Running Spiral Matrix Config Checker ===")

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found at {config_file}")

    with open(config_file, "r") as f:
        real_config = json.load(f)

    # 1. Test real configuration
    print("Checking production config.json...")
    validate_config(exercise_dir, real_config)
    print("✔ Real config.json passed validation successfully.")

    # 2. Test deliberately invalid fixture 1: missing-reference
    print("Testing fixture: missing-reference...")
    cfg_missing_ref = copy.deepcopy(real_config)
    cfg_missing_ref["files"]["example"] = [".meta/nonexistent_example.go"]
    try:
        validate_config(exercise_dir, cfg_missing_ref)
        raise AssertionError("Expected missing-reference fixture to fail, but it passed!")
    except FileNotFoundError as e:
        print(f"✔ missing-reference fixture failed as expected: {e}")

    # 3. Test deliberately invalid fixture 2: missing-test
    print("Testing fixture: missing-test...")
    cfg_missing_test = copy.deepcopy(real_config)
    cfg_missing_test["files"]["test"].append("missing_test.go")
    try:
        validate_config(exercise_dir, cfg_missing_test)
        raise AssertionError("Expected missing-test fixture to fail, but it passed!")
    except FileNotFoundError as e:
        print(f"✔ missing-test fixture failed as expected: {e}")

    # 4. Test deliberately invalid fixture 3: outside-exercise (parent traversal)
    print("Testing fixture: outside-exercise...")
    cfg_outside = copy.deepcopy(real_config)
    cfg_outside["files"]["solution"] = ["../../docs/ABOUT.md"]
    try:
        validate_config(exercise_dir, cfg_outside)
        raise AssertionError("Expected outside-exercise fixture to fail, but it passed!")
    except PermissionError as e:
        print(f"✔ outside-exercise fixture failed as expected: {e}")

    print("✔ All validation fixtures passed. R63-T008 check succeeded.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Check failed: {e}", file=sys.stderr)
        sys.exit(1)
