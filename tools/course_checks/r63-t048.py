#!/usr/bin/env python3
"""Path and configuration validator for triangle (R63-T048)."""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TRIANGLE_DIR = REPO_ROOT / "exercises" / "practice" / "triangle"
CONFIG_PATH = TRIANGLE_DIR / ".meta" / "config.json"

def validate_config_dict(files_dict, base_dir):
    """Validates a files configuration dictionary against base_dir.
    Returns (ok, message).
    """
    required_keys = ["solution", "test", "example"]
    for key in required_keys:
        if key not in files_dict:
            return False, f"Missing required file category: '{key}'"
        if not isinstance(files_dict[key], list) or len(files_dict[key]) == 0:
            return False, f"Category '{key}' must be a non-empty list"

    base_resolved = base_dir.resolve()

    for category, paths in files_dict.items():
        if not isinstance(paths, list):
            continue
        for rel_path in paths:
            if ".." in Path(rel_path).parts:
                return False, f"Path traversal rejected in '{category}': {rel_path}"

            full_path = (base_dir / rel_path).resolve()
            try:
                full_path.relative_to(base_resolved)
            except ValueError:
                return False, f"Path escapes base directory in '{category}': {rel_path}"

            if not full_path.exists():
                return False, f"Declared file does not exist in '{category}': {rel_path}"

    return True, "All declared exercise files resolve securely and exist on disk."

def main():
    if not CONFIG_PATH.exists():
        print(f"Error: {CONFIG_PATH} does not exist", file=sys.stderr)
        sys.exit(1)

    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)

    files_dict = data.get("files", {})
    ok, msg = validate_config_dict(files_dict, TRIANGLE_DIR)
    if not ok:
        print(f"FAIL: {msg}", file=sys.stderr)
        sys.exit(1)

    print(f"PASS: {msg}")

if __name__ == "__main__":
    main()
