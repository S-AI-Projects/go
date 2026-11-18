#!/usr/bin/env python3
"""Verification script for R63-T033 (bob mutation-driven regression check)."""

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
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "bob"
DOCS_PATH = REPO_ROOT / "docs" / "maintenance" / "bob.md"
HINTS_PATH = EXERCISE_DIR / ".docs" / "hints.md"

REJECTING_UUID = "f7bc4b92-bdff-421e-a238-ae97f230ccac"  # "no letters"


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
    """Parse tests.toml and verify entries and comments."""
    outcomes: list[CheckOutcome] = []
    parsed = tomllib.loads(toml_path.read_text(encoding="utf-8"))

    total = len(parsed)
    excluded = sum(1 for entry in parsed.values() if entry.get("include", True) is False)
    included = total - excluded

    outcomes.append(
        CheckOutcome(
            name="tests_toml_parsed",
            passed=total > 0,
            expected="total > 0",
            actual=total,
        )
    )

    entry = parsed.get(REJECTING_UUID, {})
    comment = entry.get("comment", "")
    has_comment = isinstance(comment, str) and len(comment.strip()) > 0
    outcomes.append(
        CheckOutcome(
            name=f"uuid_{REJECTING_UUID}_comment",
            passed=has_comment,
            expected="non-empty comment key",
            actual=comment,
        )
    )

    summary = {
        "total": total,
        "included": included,
        "excluded": excluded,
        "rejecting_uuid": REJECTING_UUID,
        "rejecting_comment": comment,
    }
    return outcomes, summary


def check_learner_stub_unsolved(solution_path: Path, example_path: Path) -> CheckOutcome:
    """Confirm the working-tree learner stub remains unsolved."""
    solution_text = solution_path.read_text(encoding="utf-8")
    example_text = example_path.read_text(encoding="utf-8")
    is_unsolved = 'return ""' in solution_text
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


def check_hints_file(hints_path: Path) -> CheckOutcome:
    """Verify hints.md explains mistaken assumption with diagnostic input without full solution."""
    if not hints_path.is_file():
        return CheckOutcome(
            name="hints_file",
            passed=False,
            expected=f"Existing file at {hints_path.relative_to(REPO_ROOT)}",
            actual="missing",
        )
    text = hints_path.read_text(encoding="utf-8")
    has_letters_guidance = "letters" in text or "shouting" in text or "ToUpper" in text
    has_diagnostic_input = "1, 2, 3" in text or "4?" in text
    not_full_solution = "switch remark" not in text
    passed = has_letters_guidance and has_diagnostic_input and not_full_solution
    return CheckOutcome(
        name="hints_file",
        passed=passed,
        expected={
            "has_letters_guidance": True,
            "has_diagnostic_input": True,
            "does_not_leak_solution": True,
        },
        actual={
            "has_letters_guidance": has_letters_guidance,
            "has_diagnostic_input": has_diagnostic_input,
            "does_not_leak_solution": not_full_solution,
        },
    )


def check_maintenance_doc(doc_path: Path) -> CheckOutcome:
    """Verify docs/maintenance/bob.md records the mutant, rejecting test ID, and behavior."""
    if not doc_path.is_file():
        return CheckOutcome(
            name="maintenance_doc",
            passed=False,
            expected=f"Existing file at {doc_path.relative_to(REPO_ROOT)}",
            actual="missing",
        )
    text = doc_path.read_text(encoding="utf-8")
    has_uuid = REJECTING_UUID in text
    has_mutant = "strings.ToUpper(remark) == remark" in text
    has_rejected_status = "Rejected" in text or "Fails" in text
    has_reduced_input = "1" in text
    passed = has_uuid and has_mutant and has_rejected_status and has_reduced_input
    return CheckOutcome(
        name="maintenance_doc",
        passed=passed,
        expected={
            "has_rejecting_uuid": True,
            "has_mutant_code": True,
            "has_rejected_status": True,
            "has_reduced_input": True,
        },
        actual={
            "has_rejecting_uuid": has_uuid,
            "has_mutant_code": has_mutant,
            "has_rejected_status": has_rejected_status,
            "has_reduced_input": has_reduced_input,
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

    with tempfile.TemporaryDirectory(prefix="r63-t033-ref-") as tmp_root:
        scratch_dir = Path(tmp_root) / "bob"
        shutil.copytree(EXERCISE_DIR, scratch_dir, symlinks=True)

        # Substitute reference implementation only in the temporary copy
        shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)

        go_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)

    passed_subtests = re.findall(r"--- PASS: (TestHey/\S+)", go_test["stdout"])
    failed_subtests = re.findall(r"--- FAIL: (TestHey/\S+)", go_test["stdout"])

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
    }
    return outcomes, test_info


def run_mutant_tests(
    resolved_files: dict[str, list[str]],
) -> tuple[list[CheckOutcome], dict[str, Any]]:
    """Copy exercise to temp dir, apply deliberate mutant to example, and assert failure."""
    outcomes: list[CheckOutcome] = []
    solution_rel = resolved_files["solution"][0]
    example_rel = resolved_files["example"][0]

    with tempfile.TemporaryDirectory(prefix="r63-t033-mutant-") as tmp_root:
        scratch_dir = Path(tmp_root) / "bob"
        shutil.copytree(EXERCISE_DIR, scratch_dir, symlinks=True)

        original_code = (scratch_dir / example_rel).read_text(encoding="utf-8")
        # Mutate yelling check: drop the letter-presence check
        target_check = "return strings.ToUpper(remark) == remark && strings.ToLower(remark) != strings.ToUpper(remark)"
        mutated_check = "return strings.ToUpper(remark) == remark"
        if target_check not in original_code:
            raise ValueError(f"Could not locate target pattern to mutate in {example_rel}")
        mutated_code = original_code.replace(target_check, mutated_check, 1)

        (scratch_dir / solution_rel).write_text(mutated_code, encoding="utf-8")

        go_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)

    failed_subtests = re.findall(r"--- FAIL: (TestHey/\S+)", go_test["stdout"])

    mutant_failed_as_expected = go_test["returncode"] != 0 and len(failed_subtests) > 0
    rejected_target_case = "TestHey/no_letters" in failed_subtests

    outcomes.append(
        CheckOutcome(
            name="mutant_fails_tests",
            passed=mutant_failed_as_expected,
            expected="non-zero exit with failing subtests",
            actual=f"exit={go_test['returncode']}, failed_count={len(failed_subtests)}",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="mutant_rejected_by_named_case",
            passed=rejected_target_case,
            expected="TestHey/no_letters in failed subtests",
            actual=failed_subtests,
        )
    )

    mutant_info = {
        "command": go_test["command"],
        "returncode": go_test["returncode"],
        "failed_subtests": failed_subtests,
        "rejected_named_case": rejected_target_case,
    }
    return outcomes, mutant_info


def write_evidence(
    inputs_payload: dict[str, Any],
    results_payload: dict[str, Any],
) -> None:
    """Persist inputs, expected vs actual results, and markdown summary in work/R63-T033/."""
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
        "# R63-T033 Verification Report",
        "",
        f"- **Overall status:** {'PASS' if results_payload['all_passed'] else 'FAIL'}",
        f"- **Python version:** `{results_payload['tool_versions']['python']}`",
        f"- **Go version:** `{results_payload['tool_versions']['go']}`",
        f"- **Reference executed subtests:** {results_payload['reference_test']['passed_subtests_count']}",
        f"- **Mutant rejected by:** `{results_payload['mutant_test']['failed_subtests']}`",
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
    hints_outcome = check_hints_file(HINTS_PATH)
    doc_outcome = check_maintenance_doc(DOCS_PATH)
    ref_outcomes, ref_info = run_reference_tests(resolved_files)
    mutant_outcomes, mutant_info = run_mutant_tests(resolved_files)

    go_ver_cmd = run_command(["go", "version"])
    go_version = (
        go_ver_cmd["stdout"].strip()
        if go_ver_cmd["returncode"] == 0
        else f"unavailable ({go_ver_cmd['stderr'].strip()})"
    )

    all_outcomes = [
        *toml_outcomes,
        stub_outcome,
        hints_outcome,
        doc_outcome,
        *ref_outcomes,
        *mutant_outcomes,
    ]
    all_passed = all(item.passed for item in all_outcomes)

    inputs_payload = {
        "exercise": "exercises/practice/bob",
        "config_path": str(config_path.relative_to(REPO_ROOT)),
        "resolved_files": resolved_files,
        "rejecting_uuid": REJECTING_UUID,
        "toml_summary": toml_summary,
    }
    results_payload = {
        "all_passed": all_passed,
        "tool_versions": {
            "python": sys.version.split()[0],
            "go": go_version,
        },
        "reference_test": ref_info,
        "mutant_test": mutant_info,
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
