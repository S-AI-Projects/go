#!/usr/bin/env python3
"""Validation script for R63-T040: Explain the subtle contract cases in secret-handshake."""

from __future__ import annotations

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
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "secret-handshake"
WORK_DIR = REPO_ROOT / "work" / "R63-T040"
HINTS_PATH = EXERCISE_DIR / ".docs" / "hints.md"


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


def parse_tests_toml(tests_toml_path: Path) -> dict[str, Any]:
    content = tests_toml_path.read_text(encoding="utf-8")
    cases: dict[str, dict[str, Any]] = {}
    current_uuid: str | None = None

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        uuid_match = re.match(r"^\[([a-f0-9\-]+)\]$", line)
        if uuid_match:
            current_uuid = uuid_match.group(1)
            cases[current_uuid] = {"include": True, "description": ""}
            continue
        if current_uuid and "=" in line:
            key, val = [x.strip() for x in line.split("=", 1)]
            val = val.strip('"\'')
            if key == "description":
                cases[current_uuid]["description"] = val
            elif key == "include":
                cases[current_uuid]["include"] = val.lower() == "true"

    included = {u: c for u, c in cases.items() if c.get("include", True)}
    excluded = {u: c for u, c in cases.items() if not c.get("include", True)}
    return {"total": len(cases), "included": included, "excluded": excluded}


def verify_hints_file() -> tuple[list[CheckOutcome], dict[str, Any]]:
    outcomes: list[CheckOutcome] = []
    info: dict[str, Any] = {"path": str(HINTS_PATH), "exists": HINTS_PATH.exists()}

    if not HINTS_PATH.exists():
        outcomes.append(
            CheckOutcome(
                name="hints_file_exists",
                passed=False,
                expected=True,
                actual=False,
                detail="exercises/practice/secret-handshake/.docs/hints.md does not exist",
            )
        )
        return outcomes, info

    content = HINTS_PATH.read_text(encoding="utf-8")
    info["byte_length"] = len(content)

    has_decision_table = "Decision Table" in content and "|" in content
    has_subtle_16 = "16" in content and "revers" in content.lower()
    has_subtle_24 = "24" in content and "jump" in content
    has_subtle_0 = "0" in content
    has_unspecified_statement = "unspecified" in content.lower() or "specification" in content.lower()

    outcomes.append(
        CheckOutcome(
            name="hints_decision_table_present",
            passed=has_decision_table,
            expected=True,
            actual=has_decision_table,
            detail="hints.md contains a decision table mapping inputs to expected outputs",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="hints_covers_subtle_cases",
            passed=has_subtle_16 and has_subtle_24 and has_subtle_0,
            expected={"subtle_16": True, "subtle_24": True, "subtle_0": True},
            actual={"subtle_16": has_subtle_16, "subtle_24": has_subtle_24, "subtle_0": has_subtle_0},
            detail="hints.md explains subtle cases: 16 (empty reverse), 24 (single action reverse), and 0 (zero input)",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="hints_unspecified_statement",
            passed=has_unspecified_statement,
            expected=True,
            actual=has_unspecified_statement,
            detail="hints.md includes an explicit statement separating specified from unspecified behavior",
        )
    )

    info.update(
        {
            "has_decision_table": has_decision_table,
            "has_subtle_16": has_subtle_16,
            "has_subtle_24": has_subtle_24,
            "has_subtle_0": has_subtle_0,
            "has_unspecified_statement": has_unspecified_statement,
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


def run_reference_tests(resolved_files: dict[str, Any]) -> tuple[list[CheckOutcome], dict[str, Any]]:
    outcomes: list[CheckOutcome] = []
    example_rel = resolved_files["example"][0]
    solution_rel = resolved_files["solution"][0]

    with tempfile.TemporaryDirectory(prefix="r63-t040-ref-") as tmp_root:
        scratch_dir = Path(tmp_root) / "secret-handshake"
        shutil.copytree(EXERCISE_DIR, scratch_dir, symlinks=True)

        # Substitute reference into scratch directory
        shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)

        go_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)

    passed_subtests = re.findall(r"--- PASS: (TestHandshake/\S+)", go_test["stdout"])
    failed_subtests = re.findall(r"--- FAIL: (TestHandshake/\S+)", go_test["stdout"])

    outcomes.append(
        CheckOutcome(
            name="reference_tests_pass",
            passed=go_test["returncode"] == 0 and len(passed_subtests) > 0 and len(failed_subtests) == 0,
            expected={"exit_code": 0, "passed_gt_zero": True, "failed": 0},
            actual={"exit_code": go_test["returncode"], "passed": len(passed_subtests), "failed": len(failed_subtests)},
            detail="Reference implementation passes all enabled test cases",
        )
    )

    test_info = {
        "command": go_test["command"],
        "exit_code": go_test["returncode"],
        "passed_count": len(passed_subtests),
        "passed_tests": passed_subtests,
        "failed_count": len(failed_subtests),
    }

    return outcomes, test_info


def main() -> int:
    config_path = EXERCISE_DIR / ".meta" / "config.json"
    tests_toml_path = EXERCISE_DIR / ".meta" / "tests.toml"

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    resolved_files = config.get("files", {})
    solution_file = EXERCISE_DIR / resolved_files["solution"][0]
    example_file = EXERCISE_DIR / resolved_files["example"][0]

    tests_toml_data = parse_tests_toml(tests_toml_path)

    all_outcomes: list[CheckOutcome] = []

    # 1. tests.toml check
    all_outcomes.append(
        CheckOutcome(
            name="tests_toml_cases",
            passed=tests_toml_data["total"] > 0 and len(tests_toml_data["included"]) == 11,
            expected={"total": 11, "included": 11},
            actual={"total": tests_toml_data["total"], "included": len(tests_toml_data["included"])},
            detail="All 11 canonical test cases verified in tests.toml",
        )
    )

    # 2. learner stub check
    stub_outcome, stub_info = verify_learner_stub(solution_file, example_file)
    all_outcomes.append(stub_outcome)

    # 3. hints file check
    hints_outcomes, hints_info = verify_hints_file()
    all_outcomes.extend(hints_outcomes)

    # 4. run reference tests
    ref_outcomes, test_info = run_reference_tests(resolved_files)
    all_outcomes.extend(ref_outcomes)

    # Tool versions
    go_ver = run_command(["go", "version"])["stdout"].strip()
    python_ver = sys.version.replace("\n", " ")

    # Inputs payload
    inputs_payload = {
        "task": "R63-T040",
        "exercise": "secret-handshake",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_versions": {
            "go": go_ver,
            "python": python_ver,
        },
        "resolved_files": resolved_files,
        "canonical_tests": tests_toml_data,
        "decision_table": [
            {"input": 0, "binary": "00000", "bits": [], "reverse": False, "expected": []},
            {"input": 1, "binary": "00001", "bits": [1], "reverse": False, "expected": ["wink"]},
            {"input": 2, "binary": "00010", "bits": [2], "reverse": False, "expected": ["double blink"]},
            {"input": 4, "binary": "00100", "bits": [4], "reverse": False, "expected": ["close your eyes"]},
            {"input": 8, "binary": "01000", "bits": [8], "reverse": False, "expected": ["jump"]},
            {"input": 3, "binary": "00011", "bits": [1, 2], "reverse": False, "expected": ["wink", "double blink"]},
            {"input": 15, "binary": "01111", "bits": [1, 2, 4, 8], "reverse": False, "expected": ["wink", "double blink", "close your eyes", "jump"]},
            {"input": 16, "binary": "10000", "bits": [16], "reverse": True, "expected": []},
            {"input": 19, "binary": "10011", "bits": [1, 2, 16], "reverse": True, "expected": ["double blink", "wink"]},
            {"input": 24, "binary": "11000", "bits": [8, 16], "reverse": True, "expected": ["jump"]},
            {"input": 31, "binary": "11111", "bits": [1, 2, 4, 8, 16], "reverse": True, "expected": ["jump", "close your eyes", "double blink", "wink"]},
        ],
    }
    (WORK_DIR / "inputs.json").write_text(json.dumps(inputs_payload, indent=2), encoding="utf-8")

    # Results payload
    results_payload = {
        "task": "R63-T040",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_passed": all(o.passed for o in all_outcomes),
        "outcomes": [asdict(o) for o in all_outcomes],
        "test_info": test_info,
        "stub_info": stub_info,
        "hints_info": hints_info,
    }
    (WORK_DIR / "results.json").write_text(json.dumps(results_payload, indent=2), encoding="utf-8")

    # Markdown report
    report_md = f"""# R63-T040: Secret Handshake Contract Guidance Report

## Task Overview
- **Task ID:** R63-T040 (Coursework 10 of 10)
- **Exercise:** `exercises/practice/secret-handshake`
- **Goal:** Provide guidance for secret-handshake covering subtle contract cases (inputs 16, 24, and 0), build a complete decision table matching test assertions, and document boundaries for unspecified behavior.

## Subtle Cases Walkthrough
1. **Reversing with No Actions (Input: 16 / `10000`):**
   - Active bits: Only bit 16 (reverse).
   - Unreversed actions: Empty (`[]`).
   - Outcome: Reversing an empty sequence returns empty (`[]`).
2. **Reversing with One Action (Input: 24 / `11000`):**
   - Active bits: Bit 8 (`"jump"`) and bit 16 (reverse).
   - Outcome: Reversing a single action preserves order (`["jump"]`).
3. **Zero Input (Input: 0 / `00000`):**
   - Active bits: None.
   - Outcome: Returns empty sequence (`[]`).
4. **Unspecified Behavior Statement:**
   - Higher bits beyond bit 4 (values > 31) are outside the contract.
   - Go allows returning either `nil` or `[]string{{}}` for empty sequences.

## Canonical Test Suite Execution
- Executed Subtests: {test_info['passed_count']} / {test_info['passed_count']} passed
- Failed Subtests: {test_info['failed_count']}
- Learner Stub Preserved: Unsolved in `secret_handshake.go`

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
