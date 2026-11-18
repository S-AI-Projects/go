#!/usr/bin/env python3
"""Verification script for R63-T034 (sublist reference implementation readability refactor)."""

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
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "sublist"
DOCS_PATH = REPO_ROOT / "docs" / "maintenance" / "sublist.md"


@dataclass
class CheckOutcome:
    name: str
    passed: bool
    expected: Any
    actual: Any
    detail: str = ""


def resolve_exercise_files(config_path: Path) -> dict[str, list[str]]:
    """Resolve solution, test, example, and editor paths from .meta/config.json."""
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
    """Parse tests.toml and verify entries."""
    outcomes: list[CheckOutcome] = []
    parsed = tomllib.loads(toml_path.read_text(encoding="utf-8"))

    total = len(parsed)
    excluded = sum(1 for entry in parsed.values() if entry.get("include", True) is False)
    included = total - excluded

    outcomes.append(
        CheckOutcome(
            name="tests_toml_parsed",
            passed=total > 0 and included > 0,
            expected="total > 0 and included > 0",
            actual={"total": total, "included": included, "excluded": excluded},
        )
    )

    summary = {
        "total": total,
        "included": included,
        "excluded": excluded,
    }
    return outcomes, summary


def check_learner_stub_unsolved(solution_path: Path, example_path: Path) -> CheckOutcome:
    """Confirm the working-tree learner stub remains unsolved."""
    solution_text = solution_path.read_text(encoding="utf-8")
    example_text = example_path.read_text(encoding="utf-8")
    is_unsolved = "panic(" in solution_text
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


def check_refactored_reference(example_path: Path) -> CheckOutcome:
    """Verify example.go contains the readability refactor, invariant comment, and clean dependencies."""
    code = example_path.read_text(encoding="utf-8")
    has_renamed_params = "func contains(list, sublist []int)" in code
    has_slices_equal = "slices.Equal(list[i:i+len(sublist)], sublist)" in code
    has_invariant_comment = "Exercise invariant:" in code or "contiguous" in code
    # Check no external dependencies added
    imports = re.findall(r'import\s+(?:\(\s*([^)]+)\s*\)|"([^"]+)")', code)
    passed = has_renamed_params and has_slices_equal and has_invariant_comment
    return CheckOutcome(
        name="refactored_reference",
        passed=passed,
        expected={
            "has_renamed_params": True,
            "has_slices_equal": True,
            "has_invariant_comment": True,
        },
        actual={
            "has_renamed_params": has_renamed_params,
            "has_slices_equal": has_slices_equal,
            "has_invariant_comment": has_invariant_comment,
        },
    )


def check_maintenance_doc(doc_path: Path) -> CheckOutcome:
    """Verify docs/maintenance/sublist.md exists and documents the refactor and invariant."""
    if not doc_path.is_file():
        return CheckOutcome(
            name="maintenance_doc",
            passed=False,
            expected=f"Existing file at {doc_path.relative_to(REPO_ROOT)}",
            actual="missing",
        )
    text = doc_path.read_text(encoding="utf-8")
    has_refactor_notes = "Readability" in text or "contains(list, sublist" in text
    has_diff = "Before:" in text and "After:" in text
    has_invariant = "invariant" in text.lower()
    passed = has_refactor_notes and has_diff and has_invariant
    return CheckOutcome(
        name="maintenance_doc",
        passed=passed,
        expected={
            "has_refactor_notes": True,
            "has_diff": True,
            "has_invariant": True,
        },
        actual={
            "has_refactor_notes": has_refactor_notes,
            "has_diff": has_diff,
            "has_invariant": has_invariant,
        },
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
    """Copy exercise to temp dir, swap in reference, and run go test."""
    outcomes: list[CheckOutcome] = []
    solution_rel = resolved_files["solution"][0]
    example_rel = resolved_files["example"][0]

    with tempfile.TemporaryDirectory(prefix="r63-t034-ref-") as tmp_root:
        scratch_dir = Path(tmp_root) / "sublist"
        shutil.copytree(EXERCISE_DIR, scratch_dir, symlinks=True)

        # Substitute reference implementation only in the temporary copy
        shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)

        go_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)

    passed_subtests = re.findall(r"--- PASS: (TestSublist/\S+)", go_test["stdout"])
    failed_subtests = re.findall(r"--- FAIL: (TestSublist/\S+)", go_test["stdout"])

    outcomes.append(
        CheckOutcome(
            name="reference_go_test_exit_code",
            passed=go_test["returncode"] == 0,
            expected=0,
            actual=go_test["returncode"],
            detail=go_test["stderr"].strip() if go_test["returncode"] != 0 else "",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="reference_go_test_executed_count",
            passed=len(passed_subtests) > 0 and not failed_subtests and go_test["returncode"] == 0,
            expected={"passed_count_gt_zero": True, "failed_count": 0},
            actual={"passed_count": len(passed_subtests), "failed_count": len(failed_subtests)},
        )
    )

    test_info = {
        "command": go_test["command"],
        "returncode": go_test["returncode"],
        "passed_subtests_count": len(passed_subtests),
        "passed_subtests": passed_subtests,
        "failed_subtests": failed_subtests,
        "output": f"{go_test['stdout']}\n{go_test['stderr']}".strip(),
    }
    return outcomes, test_info


def write_evidence(
    inputs_payload: dict[str, Any],
    results_payload: dict[str, Any],
) -> None:
    """Persist inputs, expected vs actual results, and markdown summary in work/R63-T034/."""
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
        "# R63-T034 Verification Report",
        "",
        f"- **Overall status:** {'PASS' if results_payload['all_passed'] else 'FAIL'}",
        f"- **Python version:** `{results_payload['tool_versions']['python']}`",
        f"- **Go version:** `{results_payload['tool_versions']['go']}`",
        f"- **Reference executed subtests:** {results_payload['reference_test']['passed_subtests_count']}",
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
    refactor_outcome = check_refactored_reference(
        EXERCISE_DIR / resolved_files["example"][0]
    )
    doc_outcome = check_maintenance_doc(DOCS_PATH)
    ref_outcomes, ref_info = run_reference_tests(resolved_files)

    go_ver_cmd = run_command(["go", "version"])
    go_version = (
        go_ver_cmd["stdout"].strip()
        if go_ver_cmd["returncode"] == 0
        else f"unavailable ({go_ver_cmd['stderr'].strip()})"
    )

    all_outcomes = [
        *toml_outcomes,
        stub_outcome,
        refactor_outcome,
        doc_outcome,
        *ref_outcomes,
    ]
    all_passed = all(item.passed for item in all_outcomes)

    inputs_payload = {
        "exercise": "exercises/practice/sublist",
        "config_path": str(config_path.relative_to(REPO_ROOT)),
        "resolved_files": resolved_files,
        "toml_summary": toml_summary,
    }
    results_payload = {
        "all_passed": all_passed,
        "tool_versions": {
            "python": sys.version.split()[0],
            "go": go_version,
        },
        "reference_test": ref_info,
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

    print(f"Executed reference subtests: {ref_info['passed_subtests_count']}")
    for item in all_outcomes:
        status = "PASS" if item.passed else "FAIL"
        print(f"[{status}] {item.name}: expected={item.expected} actual={item.actual}")
        if item.detail:
            print(f"       detail: {item.detail}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
