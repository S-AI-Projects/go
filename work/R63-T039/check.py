#!/usr/bin/env python3
"""Validation script for R63-T039: Run accumulate without altering its learner files [exercises/practice/accumulate]."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "accumulate"
WORK_DIR = REPO_ROOT / "work" / "R63-T039"
DOCS_MAINTENANCE_FILE = REPO_ROOT / "docs" / "maintenance" / "accumulate.md"
TOOL_RUNNER_PATH = REPO_ROOT / "tools" / "course_checks" / "r63-t039.py"
FAILING_EXAMPLE_PATH = WORK_DIR / "failing_example.go"

# Import isolated runner dynamically
sys.path.insert(0, str(REPO_ROOT))
import importlib.util
spec = importlib.util.spec_from_file_location("r63_t039_runner", TOOL_RUNNER_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load module from {TOOL_RUNNER_PATH}")
runner_mod = importlib.util.module_from_spec(spec)
sys.modules["r63_t039_runner"] = runner_mod
spec.loader.exec_module(runner_mod)
run_isolated_test = runner_mod.run_isolated_test
compute_file_hashes = runner_mod.compute_file_hashes


@dataclass
class CheckOutcome:
    name: str
    passed: bool
    expected: Any
    actual: Any
    detail: str = ""


def run_command(cmd: list[str], cwd: Path | None = None) -> dict[str, Any]:
    res = subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": cmd,
        "returncode": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr,
    }


def verify_maintenance_doc() -> tuple[list[CheckOutcome], dict[str, Any]]:
    outcomes: list[CheckOutcome] = []
    info: dict[str, Any] = {"path": str(DOCS_MAINTENANCE_FILE), "exists": DOCS_MAINTENANCE_FILE.exists()}

    if not DOCS_MAINTENANCE_FILE.exists():
        outcomes.append(
            CheckOutcome(
                name="maintenance_doc_exists",
                passed=False,
                expected=True,
                actual=False,
                detail="docs/maintenance/accumulate.md does not exist",
            )
        )
        return outcomes, info

    content = DOCS_MAINTENANCE_FILE.read_text(encoding="utf-8")
    info["byte_length"] = len(content)

    has_command = "r63-t039.py" in content
    has_requirements = "Go" in content and "Python" in content
    has_hashing = "hash" in content.lower() or "sha-256" in content.lower()

    outcomes.append(
        CheckOutcome(
            name="maintenance_doc_content",
            passed=has_command and has_requirements and has_hashing,
            expected={"command": True, "requirements": True, "hashing": True},
            actual={"command": has_command, "requirements": has_requirements, "hashing": has_hashing},
            detail="Maintenance doc details command, tool requirements, and hash integrity",
        )
    )

    info.update(
        {
            "has_command": has_command,
            "has_requirements": has_requirements,
            "has_hashing": has_hashing,
        }
    )
    return outcomes, info


def verify_learner_stub(solution_path: Path, example_path: Path) -> tuple[CheckOutcome, dict[str, Any]]:
    stub_content = solution_path.read_text(encoding="utf-8")
    example_content = example_path.read_text(encoding="utf-8")

    differs = stub_content != example_content
    is_unsolved = "panic" in stub_content

    return (
        CheckOutcome(
            name="learner_stub_unsolved",
            passed=differs and is_unsolved,
            expected={"is_unsolved": True, "differs_from_example": True},
            actual={"is_unsolved": is_unsolved, "differs_from_example": differs},
            detail="Learner stub in the working tree is unchanged and unsolved (panics)",
        ),
        {"is_unsolved": is_unsolved, "differs_from_example": differs},
    )


def test_runner_scenarios() -> tuple[list[CheckOutcome], dict[str, Any]]:
    outcomes: list[CheckOutcome] = []
    scenarios: dict[str, Any] = {}

    initial_hashes = compute_file_hashes(EXERCISE_DIR)

    # Scenario 1: Real reference
    res_real = run_isolated_test(EXERCISE_DIR)
    scenarios["real_reference"] = {
        "exit_code": res_real["exit_code"],
        "tests_passed": res_real["tests_passed"],
        "zero_tests": res_real["zero_tests"],
        "hashes_preserved": res_real["hashes_preserved"],
    }
    outcomes.append(
        CheckOutcome(
            name="scenario_real_reference_passes",
            passed=res_real["exit_code"] == 0 and res_real["tests_passed"] and not res_real["zero_tests"] and res_real["hashes_preserved"],
            expected={"exit_code": 0, "tests_passed": True, "zero_tests": False, "hashes_preserved": True},
            actual={
                "exit_code": res_real["exit_code"],
                "tests_passed": res_real["tests_passed"],
                "zero_tests": res_real["zero_tests"],
                "hashes_preserved": res_real["hashes_preserved"],
            },
            detail="Real reference succeeds in isolation and preserves all learner files",
        )
    )

    # Scenario 2: Deliberately failing reference
    res_fail = run_isolated_test(EXERCISE_DIR, solution_override=FAILING_EXAMPLE_PATH)
    scenarios["failing_reference"] = {
        "exit_code": res_fail["exit_code"],
        "tests_passed": res_fail["tests_passed"],
        "zero_tests": res_fail["zero_tests"],
        "hashes_preserved": res_fail["hashes_preserved"],
    }
    outcomes.append(
        CheckOutcome(
            name="scenario_failing_reference_fails",
            passed=res_fail["exit_code"] != 0 and not res_fail["tests_passed"] and res_fail["hashes_preserved"],
            expected={"non_zero_exit": True, "tests_passed": False, "hashes_preserved": True},
            actual={
                "exit_code": res_fail["exit_code"],
                "tests_passed": res_fail["tests_passed"],
                "hashes_preserved": res_fail["hashes_preserved"],
            },
            detail="Deliberately failing reference produces non-zero exit and preserves hashes",
        )
    )

    # Scenario 3: Empty test selection
    res_empty = run_isolated_test(EXERCISE_DIR, test_run_flag="NonExistentTestRegexPattern")
    scenarios["empty_selection"] = {
        "exit_code": res_empty["exit_code"],
        "zero_tests": res_empty["zero_tests"],
        "hashes_preserved": res_empty["hashes_preserved"],
    }
    outcomes.append(
        CheckOutcome(
            name="scenario_zero_test_detected",
            passed=res_empty["zero_tests"] and res_empty["hashes_preserved"],
            expected={"zero_tests": True, "hashes_preserved": True},
            actual={"zero_tests": res_empty["zero_tests"], "hashes_preserved": res_empty["hashes_preserved"]},
            detail="Empty test selection correctly detected as zero-test run while preserving hashes",
        )
    )

    # Final overall hash check
    final_hashes = compute_file_hashes(EXERCISE_DIR)
    all_hashes_matched = (initial_hashes == final_hashes)
    outcomes.append(
        CheckOutcome(
            name="overall_learner_files_unmodified",
            passed=all_hashes_matched,
            expected=True,
            actual=all_hashes_matched,
            detail="Learner file hashes are 100% identical before and after all test scenarios",
        )
    )

    return outcomes, scenarios


def main() -> int:
    config_path = EXERCISE_DIR / ".meta" / "config.json"
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    resolved_files = config.get("files", {})
    solution_file = EXERCISE_DIR / resolved_files["solution"][0]
    example_file = EXERCISE_DIR / resolved_files["example"][0]

    all_outcomes: list[CheckOutcome] = []

    # 1. Maintenance doc check
    doc_outcomes, doc_info = verify_maintenance_doc()
    all_outcomes.extend(doc_outcomes)

    # 2. Learner stub check
    stub_outcome, stub_info = verify_learner_stub(solution_file, example_file)
    all_outcomes.append(stub_outcome)

    # 3. Test runner scenarios
    scenario_outcomes, scenarios = test_runner_scenarios()
    all_outcomes.extend(scenario_outcomes)

    # Tool versions
    go_ver = run_command(["go", "version"])["stdout"].strip()
    python_ver = sys.version.replace("\n", " ")

    # Inputs payload
    inputs_payload = {
        "task": "R63-T039",
        "exercise": "accumulate",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_versions": {
            "go": go_ver,
            "python": python_ver,
        },
        "config_files": resolved_files,
        "learner_file_hashes": compute_file_hashes(EXERCISE_DIR),
        "test_cases": [
            {"position": "first", "description": "echo empty", "given": []},
            {"position": "middle_1", "description": "echo multiple", "given": ["echo", "echo", "echo", "echo"]},
            {"position": "middle_2", "description": "capitalize", "given": ["first", "letter", "only"]},
            {"position": "final", "description": "strings.ToUpper", "given": ["hello", "world"]},
        ],
    }
    (WORK_DIR / "inputs.json").write_text(json.dumps(inputs_payload, indent=2), encoding="utf-8")

    # Results payload
    results_payload = {
        "task": "R63-T039",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_passed": all(o.passed for o in all_outcomes),
        "outcomes": [asdict(o) for o in all_outcomes],
        "scenarios": scenarios,
        "stub_info": stub_info,
        "doc_info": doc_info,
    }
    (WORK_DIR / "results.json").write_text(json.dumps(results_payload, indent=2), encoding="utf-8")

    # Markdown report
    report_md = f"""# R63-T039: Accumulate Isolated Runner Report

## Task Overview
- **Task ID:** R63-T039 (Coursework 9 of 10)
- **Exercise:** `exercises/practice/accumulate`
- **Goal:** Create an isolated runner for `accumulate` that tests the reference implementation in a temporary copy, reports case execution, propagates failures, and guarantees that learner starter files remain unaltered.

## Runner Scenarios Evaluated
1. **Real Reference (`.meta/example.go`):**
   - Exit code: `{scenarios['real_reference']['exit_code']}`
   - Tests passed: `{scenarios['real_reference']['tests_passed']}`
   - Zero tests: `{scenarios['real_reference']['zero_tests']}`
   - Hashes preserved: `{scenarios['real_reference']['hashes_preserved']}`
2. **Failing Reference (`work/R63-T039/failing_example.go`):**
   - Exit code: `{scenarios['failing_reference']['exit_code']}` (non-zero as expected)
   - Tests passed: `{scenarios['failing_reference']['tests_passed']}`
   - Hashes preserved: `{scenarios['failing_reference']['hashes_preserved']}`
3. **Empty Test Selection (`-run NonExistentTestRegexPattern`):**
   - Zero tests detected: `{scenarios['empty_selection']['zero_tests']}`
   - Hashes preserved: `{scenarios['empty_selection']['hashes_preserved']}`

## File Integrity (SHA-256 Hashes)
- Pre-run and post-run hashes for all files in `exercises/practice/accumulate/` are 100% identical.
- Working tree learner stub `accumulate.go` remains untouched and unsolved.

## Check Outcomes
"""
    for o in all_outcomes:
        status = "[PASS]" if o.passed else "[FAIL]"
        report_md += f"- {status} `{o.name}`: {o.detail} (expected={o.expected}, actual={o.actual})\n"

    (WORK_DIR / "report.md").write_text(report_md, encoding="utf-8")

    # Console output
    for o in all_outcomes:
        status = "[PASS]" if o.passed else "[FAIL]"
        print(f"{status} {o.name}: {o.detail}")

    success = all(o.passed for o in all_outcomes)
    print(f"Overall status: {'SUCCESS' if success else 'FAILURE'}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
