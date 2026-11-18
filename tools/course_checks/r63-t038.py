#!/usr/bin/env python3
"""Path and configuration checker for R63-T038 (exercises/practice/octal)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
OCTAL_DIR = REPO_ROOT / "exercises" / "practice" / "octal"
CONFIG_PATH = OCTAL_DIR / ".meta" / "config.json"


def validate_exercise_files(
    files_config: dict[str, Any],
    base_dir: Path,
) -> tuple[bool, str]:
    """Validates the files mapping in an exercise's config.json.
    
    Ensures:
    1. Mandatory categories ('solution', 'test', 'example') exist.
    2. Paths do not use parent traversal (e.g. '..') and stay within base_dir.
    3. Every declared file actually exists on disk.
    """
    required_keys = ["solution", "test", "example"]
    for key in required_keys:
        if key not in files_config:
            return False, f"Missing required file category: '{key}'"
        if not isinstance(files_config[key], list) or len(files_config[key]) == 0:
            return False, f"Category '{key}' must be a non-empty list of paths"

    base_resolved = base_dir.resolve()

    for category, paths in files_config.items():
        if not isinstance(paths, list):
            continue
        for rel_path_str in paths:
            # Reject absolute paths or obvious traversal tokens
            if rel_path_str.startswith("/") or ".." in Path(rel_path_str).parts:
                return False, f"Path traversal rejected in '{category}': {rel_path_str}"

            target_path = (base_dir / rel_path_str).resolve()

            # Ensure the resolved path is strictly within base_dir
            try:
                target_path.relative_to(base_resolved)
            except ValueError:
                return False, f"Path escapes exercise root in '{category}': {rel_path_str}"

            if not target_path.is_file():
                return False, f"Declared file does not exist in '{category}': {rel_path_str}"

    return True, "All declared exercise files resolve securely and exist on disk."


def main() -> int:
    if not CONFIG_PATH.is_file():
        print(f"ERROR: config.json not found at {CONFIG_PATH}", file=sys.stderr)
        return 1

    with open(CONFIG_PATH, encoding="utf-8") as f:
        data = json.load(f)

    files_cfg = data.get("files", {})
    ok, msg = validate_exercise_files(files_cfg, OCTAL_DIR)
    if ok:
        print(f"SUCCESS: {msg}")
        return 0
    else:
        print(f"VALIDATION FAILED: {msg}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
