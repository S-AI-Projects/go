#!/usr/bin/env python3
"""Verification script for R63-T032 (hello-world test-generation reproducibility)."""

from __future__ import annotations

import json
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
WORK_DIR = Path(__file__).resolve().parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "hello-world"
DOCS_PATH = REPO_ROOT / "docs" / "maintenance" / "hello-world.md"
TOOLS_CHECK_PATH = REPO_ROOT / "tools" / "course_checks" / "r63-t032.py"

TARGET_UUID = "af9ffe10-dc13-42d8-a742-e7bdafac449d"
EXPECTED_TOTAL_CASES = 1
EXPECTED_INCLUDED_CASES = 1
EXPECTED_EXCLUDED_CASES = 0


@dataclass
class CheckOutcome:
    name: str
    passed: bool
    expected: Any
    actual: Any
    detail: str = ""


def resolve_exercise_files(config_path: Path) -> dict[str, list[str]]:
    """Resolve solution, test, and example paths from .meta/config.json."""
    config = json.loads(config_path.read_text(encoding="utf-8"))
    files = config.get("files", {})
    resolved: dict[str, list[str]] = {}
    for key in ("solution", "test", "example"):
        entries = files.get(key)
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"Missing or empty files.{key} in {config_path}")
        for rel_path in entries:
            full_path = EXERCISE_DIR / rel_path
            if not full_path.is_file():
                raise FileNotFoundError(f"Configured {key} file not found: {full_path}")
        resolved[key] = list(entries)
    return resolved


def check_tests_toml(toml_path: Path) -> tuple[list[CheckOutcome], dict[str, Any]]:
    """Parse tests.toml and verify counts and rationale comment."""
    outcomes: list[CheckOutcome] = []
    parsed = tomllib.loads(toml_path.read_text(encoding="utf-8"))

    total = len(parsed)
    excluded = sum(1 for entry in parsed.values() if entry.get("include", True) is False)
    included = total - excluded

    outcomes.append(
        CheckOutcome(
            name="tests_toml_counts",
            passed=(
                total == EXPECTED_TOTAL_CASES
                and included == EXPECTED_INCLUDED_CASES
                and excluded == EXPECTED_EXCLUDED_CASES
            ),
            expected={
                "total": EXPECTED_TOTAL_CASES,
                "included": EXPECTED_INCLUDED_CASES,
                "excluded": EXPECTED_EXCLUDED_CASES,
            },
            actual={"total": total, "included": included, "excluded": excluded},
        )
    )

    entry = parsed.get(TARGET_UUID, {})
    description = entry.get("description", "")
    include_flag = entry.get("include", True)
    comment = entry.get("comment", "")
    has_valid_comment = (
        isinstance(comment, str)
        and bool(comment.strip())
        and any(token in comment for token in ("TestHelloWorld", "hello_world_test.go", "HelloWorld"))
    )

    outcomes.append(
        CheckOutcome(
            name=f"uuid_{TARGET_UUID}",
            passed=bool(description) and include_flag is True and has_valid_comment,
            expected={
                "description_non_empty": True,
                "include": True,
                "comment_names_test_or_operation": True,
            },
            actual={
                "description": description,
                "include": include_flag,
                "comment": comment,
            },
        )
    )

    summary = {
        "total": total,
        "included": included,
        "excluded": excluded,
        "target": {
            "uuid": TARGET_UUID,
            "description": description,
            "include": include_flag,
            "comment": comment,
        },
    }
    return outcomes, summary


def check_learner_stub_unsolved(solution_path: Path, example_path: Path) -> CheckOutcome:
    """Confirm the working-tree learner stub remains unsolved."""
    solution_text = solution_path.read_text(encoding="utf-8")
    example_text = example_path.read_text(encoding="utf-8")
    is_unsolved = "Goodbye, Mars!" in solution_text
    differs_from_example = solution_text != example_text
    return CheckOutcome(
        name="learner_stub_unsolved",
        passed=is_unsolved and differs_from_example,
        expected={"is_unsolved": True, "differs_from_example": True},
        actual={
            "is_unsolved": is_unsolved,
            "differs_from_example": differs_from_example,
        },
    )


def check_maintenance_doc(doc_path: Path) -> CheckOutcome:
    """Verify docs/maintenance/hello-world.md exists and documents route and mappings."""
    if not doc_path.is_file():
        return CheckOutcome(
            name="maintenance_doc",
            passed=False,
            expected=f"Existing file at {doc_path.relative_to(REPO_ROOT)}",
            actual="missing",
        )
    text = doc_path.read_text(encoding="utf-8")
    has_uuid = TARGET_UUID in text
    has_command = "configlet sync" in text
    has_mapping = "TestHelloWorld" in text
    has_inputs = "canonical-data.json" in text
    passed = has_uuid and has_command and has_mapping and has_inputs
    return CheckOutcome(
        name="maintenance_doc",
        passed=passed,
        expected={
            "has_uuid": True,
            "has_command": True,
            "has_mapping": True,
            "has_inputs": True,
        },
        actual={
            "has_uuid": has_uuid,
            "has_command": has_command,
            "has_mapping": has_mapping,
            "has_inputs": has_inputs,
        },
    )


def check_tools_check(tools_script_path: Path) -> CheckOutcome:
    """Run tools/course_checks/r63-t032.py to test regeneration consistency."""
    if not tools_script_path.is_file():
        return CheckOutcome(
            name="tools_course_check",
            passed=False,
            expected=f"Existing file at {tools_script_path.relative_to(REPO_ROOT)}",
            actual="missing",
        )
    proc = subprocess.run(
        [sys.executable, str(tools_script_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    passed = proc.returncode == 0
    return CheckOutcome(
        name="tools_course_check",
        passed=passed,
        expected={"returncode": 0},
        actual={"returncode": proc.returncode, "stdout": proc.stdout.strip()},
        detail=proc.stderr.strip() if proc.returncode != 0 else "",
    )


def run_command(cmd: list[str], cwd: Path | None = None) -> dict[str, Any]:
    """Run a child command safely and capture exit status and output."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "command": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except FileNotFoundError as exc:
        return {
            "command": cmd,
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
        }


def run_reference_tests(
    resolved_files: dict[str, list[str]],
) -> tuple[list[CheckOutcome], dict[str, Any]]:
    """Copy the exercise to a temp dir, swap in the reference, and run go test."""
    outcomes: list[CheckOutcome] = []
    solution_rel = resolved_files["solution"][0]
    example_rel = resolved_files["example"][0]

    with tempfile.TemporaryDirectory(prefix="r63-t032-") as tmp_root:
        scratch_dir = Path(tmp_root) / "hello-world"
        shutil.copytree(EXERCISE_DIR, scratch_dir, symlinks=True)

        # Substitute reference implementation only in the temporary copy
        shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)

        go_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)

    passed_tests = re.findall(r"--- PASS:\s+(\w+)", go_test["stdout"])
    failed_tests = re.findall(r"--- FAIL:\s+(\w+)", go_test["stdout"])

    outcomes.append(
        CheckOutcome(
            name="go_test_exit_code",
            passed=go_test["returncode"] == 0,
            expected=0,
            actual=go_test["returncode"],
            detail=go_test["stderr"].strip() if go_test["returncode"] != 0 else "",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="go_test_executed_count",
            passed=len(passed_tests) > 0 and not failed_tests and go_test["returncode"] == 0,
            expected={"passed_count_gt_zero": True, "failed_count": 0},
            actual={"passed_count": len(passed_tests), "failed_count": len(failed_tests)},
        )
    )
    outcomes.append(
        CheckOutcome(
            name="go_test_named_case",
            passed="TestHelloWorld" in passed_tests,
            expected="TestHelloWorld",
            actual=passed_tests,
        )
    )

    test_info = {
        "command": go_test["command"],
        "returncode": go_test["returncode"],
        "passed_tests_count": len(passed_tests),
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "output": f"{go_test['stdout']}\n{go_test['stderr']}".strip(),
    }
    return outcomes, test_info


def write_evidence(
    inputs_payload: dict[str, Any],
    results_payload: dict[str, Any],
) -> None:
    """Persist inputs, expected vs actual results, and markdown summary in work/R63-T032/."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    (WORK_DIR / "inputs.json").write_text(
        json.dumps(inputs_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    (WORK_DIR / "results.json").write_text(
        json.dumps(results_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# R63-T032 Verification Report",
        "",
        f"- **Overall status:** {'PASS' if results_payload['all_passed'] else 'FAIL'}",
        f"- **Python version:** `{results_payload['tool_versions']['python']}`",
        f"- **Go version:** `{results_payload['tool_versions']['go']}`",
        f"- **Executed tests:** {results_payload['go_test']['passed_tests_count']}",
        "",
        "## Checks",
        "",
        "| Check | Status | Expected | Actual |",
        "| --- | --- | --- | --- |",
    ]
    for check in results_payload["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        exp = json.dumps(check["expected"])
        act = json.dumps(check["actual"])
        lines.append(f"| `{check['name']}` | {status} | `{exp}` | `{act}` |")

    (WORK_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    config_path = EXERCISE_DIR / ".meta" / "config.json"
    toml_path = EXERCISE_DIR / ".meta" / "tests.toml"

    resolved_files = resolve_exercise_files(config_path)
    toml_outcomes, toml_summary = check_tests_toml(toml_path)
    stub_outcome = check_learner_stub_unsolved(
        EXERCISE_DIR / resolved_files["solution"][0],
        EXERCISE_DIR / resolved_files["example"][0],
    )
    doc_outcome = check_maintenance_doc(DOCS_PATH)
    tools_outcome = check_tools_check(TOOLS_CHECK_PATH)
    test_outcomes, test_info = run_reference_tests(resolved_files)

    go_ver_cmd = run_command(["go", "version"])
    go_version = (
        go_ver_cmd["stdout"].strip()
        if go_ver_cmd["returncode"] == 0
        else f"unavailable ({go_ver_cmd['stderr'].strip()})"
    )

    all_outcomes = [*toml_outcomes, stub_outcome, doc_outcome, tools_outcome, *test_outcomes]
    all_passed = all(item.passed for item in all_outcomes)

    inputs_payload = {
        "exercise": "exercises/practice/hello-world",
        "config_path": str(config_path.relative_to(REPO_ROOT)),
        "resolved_files": resolved_files,
        "target_uuid": TARGET_UUID,
        "toml_summary": toml_summary,
    }
    results_payload = {
        "all_passed": all_passed,
        "tool_versions": {
            "python": sys.version.split()[0],
            "go": go_version,
        },
        "go_test": test_info,
        "checks": [
            {
                "name": item.name,
                "passed": item.passed,
                "expected": item.expected,
                "actual": item.actual,
                "detail": item.detail,
            }
            for item in all_outcomes
        ],
    }

    write_evidence(inputs_payload, results_payload)

    print(f"Executed test functions: {test_info['passed_tests_count']}")
    for item in all_outcomes:
        status = "PASS" if item.passed else "FAIL"
        print(f"[{status}] {item.name}: expected={item.expected} actual={item.actual}")
        if item.detail:
            print(f"       detail: {item.detail}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
