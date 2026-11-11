#!/usr/bin/env python3
"""Verification script for R63-T031 (circular-buffer canonical-case rationale)."""

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
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "circular-buffer"
DOCS_PATH = REPO_ROOT / "docs" / "maintenance" / "circular-buffer.md"

TARGET_UUIDS = (
    "28268ed4-4ff3-45f3-820e-895b44d53dfa",
    "2e6db04a-58a1-425d-ade8-ac30b5f318f3",
    "90741fe8-a448-45ce-be2b-de009a24c144",
)

EXPECTED_TOTAL_CASES = 14
EXPECTED_INCLUDED_CASES = 14
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
    """Parse tests.toml and verify counts and rationales for target UUIDs."""
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

    rationale_tokens = ("TestRun", "cases_test.go", "ReadByte", "WriteByte", "NewBuffer")
    uuid_details: dict[str, Any] = {}
    for uuid in TARGET_UUIDS:
        entry = parsed.get(uuid)
        if not isinstance(entry, dict):
            outcomes.append(
                CheckOutcome(
                    name=f"uuid_{uuid}",
                    passed=False,
                    expected="TOML table with description and comment",
                    actual=None,
                    detail="UUID missing from tests.toml",
                )
            )
            continue

        description = entry.get("description", "")
        include_flag = entry.get("include", True)
        comment = entry.get("comment", "")
        has_valid_comment = (
            isinstance(comment, str)
            and bool(comment.strip())
            and any(token in comment for token in rationale_tokens)
        )
        outcomes.append(
            CheckOutcome(
                name=f"uuid_{uuid}",
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
        uuid_details[uuid] = {
            "description": description,
            "include": include_flag,
            "comment": comment,
        }

    summary = {
        "total": total,
        "included": included,
        "excluded": excluded,
        "targets": uuid_details,
    }
    return outcomes, summary


def check_learner_stub_unsolved(solution_path: Path, example_path: Path) -> CheckOutcome:
    """Confirm the working-tree learner stub remains unsolved."""
    solution_text = solution_path.read_text(encoding="utf-8")
    example_text = example_path.read_text(encoding="utf-8")
    has_panic_stubs = 'panic("Please implement the ' in solution_text
    differs_from_example = solution_text != example_text
    return CheckOutcome(
        name="learner_stub_unsolved",
        passed=has_panic_stubs and differs_from_example,
        expected={"has_panic_stubs": True, "differs_from_example": True},
        actual={
            "has_panic_stubs": has_panic_stubs,
            "differs_from_example": differs_from_example,
        },
    )


def check_maintenance_doc(doc_path: Path) -> CheckOutcome:
    """Verify docs/maintenance/circular-buffer.md exists and documents target UUIDs."""
    if not doc_path.is_file():
        return CheckOutcome(
            name="maintenance_doc",
            passed=False,
            expected=f"Existing file at {doc_path.relative_to(REPO_ROOT)}",
            actual="missing",
        )
    text = doc_path.read_text(encoding="utf-8")
    missing_uuids = [uuid for uuid in TARGET_UUIDS if uuid not in text]
    has_counts = "14" in text and "0" in text
    return CheckOutcome(
        name="maintenance_doc",
        passed=(not missing_uuids) and has_counts,
        expected={"all_target_uuids_present": True, "counts_recorded": True},
        actual={"missing_uuids": missing_uuids, "counts_recorded": has_counts},
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
    target_descriptions: dict[str, str],
) -> tuple[list[CheckOutcome], dict[str, Any]]:
    """Copy the exercise to a temp dir, swap in the reference, and run go test."""
    outcomes: list[CheckOutcome] = []
    solution_rel = resolved_files["solution"][0]
    example_rel = resolved_files["example"][0]

    with tempfile.TemporaryDirectory(prefix="r63-t031-") as tmp_root:
        scratch_dir = Path(tmp_root) / "circular-buffer"
        shutil.copytree(EXERCISE_DIR, scratch_dir, symlinks=True)

        # Substitute the reference implementation only in the temporary copy.
        shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)

        go_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)

    combined_output = f"{go_test['stdout']}\n{go_test['stderr']}".strip()
    passed_subtests = re.findall(r"--- PASS: (TestRun/\S+)", go_test["stdout"])
    failed_subtests = re.findall(r"--- FAIL: (TestRun/\S+)", go_test["stdout"])

    expected_named_subtests = {
        uuid: f"TestRun/{desc.replace(' ', '_')}"
        for uuid, desc in target_descriptions.items()
    }
    missing_named_subtests = [
        subtest
        for subtest in expected_named_subtests.values()
        if subtest not in passed_subtests
    ]

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
            passed=(
                len(passed_subtests) == EXPECTED_INCLUDED_CASES
                and len(passed_subtests) > 0
                and not failed_subtests
            ),
            expected={"passed_subtests": EXPECTED_INCLUDED_CASES, "failed_subtests": 0},
            actual={
                "passed_subtests": len(passed_subtests),
                "failed_subtests": len(failed_subtests),
            },
        )
    )
    outcomes.append(
        CheckOutcome(
            name="go_test_named_target_cases",
            passed=(go_test["returncode"] == 0 and not missing_named_subtests),
            expected=list(expected_named_subtests.values()),
            actual={
                "passed_subtests": passed_subtests,
                "missing_named_subtests": missing_named_subtests,
            },
        )
    )

    test_info = {
        "command": go_test["command"],
        "returncode": go_test["returncode"],
        "passed_subtests_count": len(passed_subtests),
        "passed_subtests": passed_subtests,
        "failed_subtests": failed_subtests,
        "output": combined_output,
    }
    return outcomes, test_info


def write_evidence(
    inputs_payload: dict[str, Any],
    results_payload: dict[str, Any],
) -> None:
    """Persist inputs, expected vs actual results, and markdown summary in work/R63-T031/."""
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
        "# R63-T031 Verification Report",
        "",
        f"- **Overall status:** {'PASS' if results_payload['all_passed'] else 'FAIL'}",
        f"- **Python version:** `{results_payload['tool_versions']['python']}`",
        f"- **Go version:** `{results_payload['tool_versions']['go']}`",
        f"- **Executed cases:** {results_payload['go_test']['passed_subtests_count']}",
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

    target_descriptions = {
        uuid: info["description"] for uuid, info in toml_summary["targets"].items()
    }
    test_outcomes, test_info = run_reference_tests(resolved_files, target_descriptions)

    go_ver_cmd = run_command(["go", "version"])
    go_version = (
        go_ver_cmd["stdout"].strip()
        if go_ver_cmd["returncode"] == 0
        else f"unavailable ({go_ver_cmd['stderr'].strip()})"
    )

    all_outcomes = [*toml_outcomes, stub_outcome, doc_outcome, *test_outcomes]
    all_passed = all(item.passed for item in all_outcomes)

    inputs_payload = {
        "exercise": "exercises/practice/circular-buffer",
        "config_path": str(config_path.relative_to(REPO_ROOT)),
        "resolved_files": resolved_files,
        "target_uuids": list(TARGET_UUIDS),
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

    print(f"Executed subtests: {test_info['passed_subtests_count']}")
    for item in all_outcomes:
        status = "PASS" if item.passed else "FAIL"
        print(f"[{status}] {item.name}: expected={item.expected} actual={item.actual}")
        if item.detail:
            print(f"       detail: {item.detail}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

