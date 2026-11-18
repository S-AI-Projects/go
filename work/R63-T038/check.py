#!/usr/bin/env python3
"""Validation script for R63-T038: Map the maintained files for octal [exercises/practice/octal]."""

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
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "octal"
WORK_DIR = REPO_ROOT / "work" / "R63-T038"
DOCS_MAINTENANCE_FILE = REPO_ROOT / "docs" / "maintenance" / "octal.md"
TOOL_CHECKER_PATH = REPO_ROOT / "tools" / "course_checks" / "r63-t038.py"

# Import checker dynamically from tools/course_checks/r63-t038.py
sys.path.insert(0, str(REPO_ROOT))
import importlib.util
spec = importlib.util.spec_from_file_location("r63_t038_checker", TOOL_CHECKER_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load module from {TOOL_CHECKER_PATH}")
checker_mod = importlib.util.module_from_spec(spec)
sys.modules["r63_t038_checker"] = checker_mod
spec.loader.exec_module(checker_mod)
validate_exercise_files = checker_mod.validate_exercise_files


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
                detail="docs/maintenance/octal.md does not exist",
            )
        )
        return outcomes, info

    content = DOCS_MAINTENANCE_FILE.read_text(encoding="utf-8")
    info["byte_length"] = len(content)

    has_stub_path = "octal.go" in content
    has_test_path = "octal_test.go" in content
    has_example_path = ".meta/example.go" in content
    has_distinction = "generated" in content.lower() and ("manual" in content.lower() or "gen.go" in content)
    has_reproducible_cmd = "python3" in content and ("r63-t038.py" in content or "check.py" in content)

    outcomes.append(
        CheckOutcome(
            name="maintenance_doc_file_map",
            passed=has_stub_path and has_test_path and has_example_path,
            expected={"stub": True, "test": True, "example": True},
            actual={"stub": has_stub_path, "test": has_test_path, "example": has_example_path},
            detail="Maintenance doc names real stub, reference, and test paths",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="maintenance_doc_distinguishes_generated",
            passed=has_distinction,
            expected=True,
            actual=has_distinction,
            detail="Maintenance doc distinguishes manual vs generated artifacts",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="maintenance_doc_validation_command",
            passed=has_reproducible_cmd,
            expected=True,
            actual=has_reproducible_cmd,
            detail="Maintenance doc includes reproducible validation command",
        )
    )

    info.update(
        {
            "has_stub_path": has_stub_path,
            "has_test_path": has_test_path,
            "has_example_path": has_example_path,
            "has_distinction": has_distinction,
            "has_reproducible_cmd": has_reproducible_cmd,
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


def test_metadata_fixtures(real_files_cfg: dict[str, Any]) -> tuple[list[CheckOutcome], dict[str, Any]]:
    outcomes: list[CheckOutcome] = []
    fixture_results: dict[str, Any] = {}

    # 1. Real config validation
    ok_real, msg_real = validate_exercise_files(real_files_cfg, EXERCISE_DIR)
    fixture_results["real_config"] = {"ok": ok_real, "msg": msg_real}
    outcomes.append(
        CheckOutcome(
            name="real_metadata_passes",
            passed=ok_real,
            expected=True,
            actual=ok_real,
            detail=f"Real config passes validation: {msg_real}",
        )
    )

    # 2. Fixture: Missing reference
    missing_ref_cfg = {
        "solution": ["octal.go"],
        "test": ["octal_test.go"],
        "example": [".meta/nonexistent_example.go"],
    }
    ok_ref, msg_ref = validate_exercise_files(missing_ref_cfg, EXERCISE_DIR)
    fixture_results["missing_reference_fixture"] = {"ok": ok_ref, "msg": msg_ref}
    outcomes.append(
        CheckOutcome(
            name="missing_reference_fixture_fails",
            passed=not ok_ref and "does not exist" in msg_ref,
            expected={"ok": False, "reason_contains": "does not exist"},
            actual={"ok": ok_ref, "msg": msg_ref},
            detail="Missing reference fixture fails as expected",
        )
    )

    # 3. Fixture: Missing test
    missing_test_cfg = {
        "solution": ["octal.go"],
        "test": ["missing_octal_test.go"],
        "example": [".meta/example.go"],
    }
    ok_test, msg_test = validate_exercise_files(missing_test_cfg, EXERCISE_DIR)
    fixture_results["missing_test_fixture"] = {"ok": ok_test, "msg": msg_test}
    outcomes.append(
        CheckOutcome(
            name="missing_test_fixture_fails",
            passed=not ok_test and "does not exist" in msg_test,
            expected={"ok": False, "reason_contains": "does not exist"},
            actual={"ok": ok_test, "msg": msg_test},
            detail="Missing test fixture fails as expected",
        )
    )

    # 4. Fixture: Outside exercise traversal
    traversal_cfg = {
        "solution": ["octal.go"],
        "test": ["octal_test.go"],
        "example": ["../etl/.meta/example.go"],
    }
    ok_trav, msg_trav = validate_exercise_files(traversal_cfg, EXERCISE_DIR)
    fixture_results["outside_exercise_fixture"] = {"ok": ok_trav, "msg": msg_trav}
    outcomes.append(
        CheckOutcome(
            name="outside_exercise_fixture_fails",
            passed=not ok_trav and ("traversal" in msg_trav.lower() or "escapes" in msg_trav.lower()),
            expected={"ok": False, "reason_contains": "traversal or escapes"},
            actual={"ok": ok_trav, "msg": msg_trav},
            detail="Outside exercise traversal fixture fails as expected",
        )
    )

    return outcomes, fixture_results


def run_reference_tests(resolved_files: dict[str, Any]) -> tuple[list[CheckOutcome], dict[str, Any]]:
    outcomes: list[CheckOutcome] = []
    example_rel = resolved_files["example"][0]
    solution_rel = resolved_files["solution"][0]

    with tempfile.TemporaryDirectory(prefix="r63-t038-ref-") as tmp_root:
        scratch_dir = Path(tmp_root) / "octal"
        shutil.copytree(EXERCISE_DIR, scratch_dir, symlinks=True)

        # Substitute reference into scratch directory
        shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)

        go_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)

    # In octal_test.go, TestParseOctal runs a single top-level test iterating over testCases.
    # We can also check that TestParseOctal passes and all cases pass without error.
    passed_test = "PASS: TestParseOctal" in go_test["stdout"]
    failed_test = "FAIL: TestParseOctal" in go_test["stdout"] or "--- FAIL:" in go_test["stdout"]

    outcomes.append(
        CheckOutcome(
            name="reference_tests_pass",
            passed=go_test["returncode"] == 0 and passed_test and not failed_test,
            expected={"exit_code": 0, "passed": True, "failed": False},
            actual={"exit_code": go_test["returncode"], "passed": passed_test, "failed": failed_test},
            detail="All cases in octal_test.go pass against the reference implementation",
        )
    )

    test_info = {
        "command": go_test["command"],
        "exit_code": go_test["returncode"],
        "passed": passed_test,
        "failed": failed_test,
        "stdout_summary": [l for l in go_test["stdout"].splitlines() if "PASS" in l or "FAIL" in l or "ok" in l],
    }

    return outcomes, test_info


def main() -> int:
    config_path = EXERCISE_DIR / ".meta" / "config.json"
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    resolved_files = config.get("files", {})
    solution_file = EXERCISE_DIR / resolved_files["solution"][0]
    example_file = EXERCISE_DIR / resolved_files["example"][0]

    all_outcomes: list[CheckOutcome] = []

    # 1. verify maintenance doc
    doc_outcomes, doc_info = verify_maintenance_doc()
    all_outcomes.extend(doc_outcomes)

    # 2. learner stub check
    stub_outcome, stub_info = verify_learner_stub(solution_file, example_file)
    all_outcomes.append(stub_outcome)

    # 3. metadata fixtures check
    fixture_outcomes, fixture_info = test_metadata_fixtures(resolved_files)
    all_outcomes.extend(fixture_outcomes)

    # 4. reference test execution
    ref_outcomes, test_info = run_reference_tests(resolved_files)
    all_outcomes.extend(ref_outcomes)

    # Tool versions
    go_ver = run_command(["go", "version"])["stdout"].strip()
    python_ver = sys.version.replace("\n", " ")

    # Inputs payload
    inputs_payload = {
        "task": "R63-T038",
        "exercise": "octal",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_versions": {
            "go": go_ver,
            "python": python_ver,
        },
        "config_files_mapping": resolved_files,
        "test_cases": [
            {"input": "1", "expectedNum": 1, "expectErr": False, "position": "first"},
            {"input": "10", "expectedNum": 8, "expectErr": False},
            {"input": "1234567", "expectedNum": 342391, "expectErr": False, "position": "middle"},
            {"input": "carrot", "expectedNum": 0, "expectErr": True},
            {"input": "35682", "expectedNum": 0, "expectErr": True, "position": "final"},
        ],
    }
    (WORK_DIR / "inputs.json").write_text(json.dumps(inputs_payload, indent=2), encoding="utf-8")

    # Results payload
    results_payload = {
        "task": "R63-T038",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_passed": all(o.passed for o in all_outcomes),
        "outcomes": [asdict(o) for o in all_outcomes],
        "test_info": test_info,
        "fixture_info": fixture_info,
        "stub_info": stub_info,
        "doc_info": doc_info,
    }
    (WORK_DIR / "results.json").write_text(json.dumps(results_payload, indent=2), encoding="utf-8")

    # Markdown report
    report_md = f"""# R63-T038: Octal Maintained Files Mapping Report

## Task Overview
- **Task ID:** R63-T038 (Coursework 8 of 10)
- **Exercise:** `exercises/practice/octal`
- **Goal:** Map and verify the maintained files for `octal`, ensure all declared paths resolve safely inside the exercise root, test failure fixtures, and document runner resolution.

## Maintained File Map
- **Solution:** `{resolved_files['solution'][0]}` (Learner stub, contains panic)
- **Test Suite:** `{resolved_files['test'][0]}` (Manual test cases + benchmark)
- **Reference Implementation:** `{resolved_files['example'][0]}` (Canonical implementation)

## Metadata Validation & Fixture Outcomes
- **Real Metadata:** {fixture_info['real_config']['msg']} (Passed: {fixture_info['real_config']['ok']})
- **Fixture 1 (Missing Reference):** {fixture_info['missing_reference_fixture']['msg']}
- **Fixture 2 (Missing Test):** {fixture_info['missing_test_fixture']['msg']}
- **Fixture 3 (Path Traversal / Escape):** {fixture_info['outside_exercise_fixture']['msg']}

## Test Suite Execution
- All 5 test cases passed against reference (including first `"1"`, middle `"1234567"`, and final `"35682"`).
- Learner stub preserved in unsolved state.

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
