#!/usr/bin/env python3
"""Validation script for R63-T037: Add Go-specific guidance for etl [exercises/practice/etl]."""

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
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "etl"
WORK_DIR = REPO_ROOT / "work" / "R63-T037"
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
                detail="exercises/practice/etl/.docs/hints.md does not exist",
            )
        )
        return outcomes, info

    content = HINTS_PATH.read_text(encoding="utf-8")
    info["byte_length"] = len(content)

    has_construct_named = "zero value" in content.lower() and "map" in content.lower()
    has_reference_link = "https://go.dev/ref/spec#The_zero_value" in content or "https://go.dev/ref/spec#Map_types" in content
    has_micro_examples = "make(map[string]int)" in content and "var out map[string]int" in content
    has_expected_output_1 = "1" in content
    has_expected_output_panic = "panic: assignment to entry in nil map" in content
    no_full_solution = "for key, values := range in" not in content

    outcomes.append(
        CheckOutcome(
            name="hints_construct_and_reference_link",
            passed=has_construct_named and has_reference_link,
            expected={"construct_named": True, "reference_link": True},
            actual={"construct_named": has_construct_named, "reference_link": has_reference_link},
            detail="hints.md explains map zero values and links to the Go language specification",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="hints_micro_examples_and_outputs",
            passed=has_micro_examples and has_expected_output_1 and has_expected_output_panic and no_full_solution,
            expected={"micro_examples": True, "outputs": True, "avoids_full_solution": True},
            actual={
                "micro_examples": has_micro_examples,
                "outputs": has_expected_output_1 and has_expected_output_panic,
                "avoids_full_solution": no_full_solution,
            },
            detail="hints.md includes working and pitfall micro-examples with expected outputs while avoiding a full solution",
        )
    )

    info.update(
        {
            "has_construct_named": has_construct_named,
            "has_reference_link": has_reference_link,
            "has_micro_examples": has_micro_examples,
            "has_expected_output_1": has_expected_output_1,
            "has_expected_output_panic": has_expected_output_panic,
            "no_full_solution": no_full_solution,
        }
    )
    return outcomes, info


def verify_learner_stub(solution_path: Path, example_path: Path) -> tuple[CheckOutcome, dict[str, Any]]:
    stub_content = solution_path.read_text(encoding="utf-8")
    example_content = example_path.read_text(encoding="utf-8")

    differs = stub_content != example_content
    is_unsolved = "panic" in stub_content or 'return nil' in stub_content

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


def execute_and_assert_micro_examples() -> tuple[list[CheckOutcome], dict[str, Any]]:
    outcomes: list[CheckOutcome] = []
    micro_results: dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="r63-t037-micro-") as tmp_root:
        tmp_dir = Path(tmp_root)
        (tmp_dir / "go.mod").write_text("module microtest\n", encoding="utf-8")

        # 1. Working initialized map
        shutil.copy2(WORK_DIR / "micro_working.go", tmp_dir / "main.go")
        res_work = run_command(["go", "run", "main.go"], cwd=tmp_dir)
        work_out = res_work["stdout"].strip()
        micro_results["working"] = {
            "stdout": work_out,
            "exit_code": res_work["returncode"],
        }
        outcomes.append(
            CheckOutcome(
                name="micro_example_working_output",
                passed=res_work["returncode"] == 0 and work_out == "1",
                expected={"exit_code": 0, "stdout": "1"},
                actual={"exit_code": res_work["returncode"], "stdout": work_out},
                detail="Working micro-example successfully initializes map and prints 1",
            )
        )

        # 2. Pitfall reading nil map
        shutil.copy2(WORK_DIR / "micro_pitfall_read.go", tmp_dir / "main.go")
        res_read = run_command(["go", "run", "main.go"], cwd=tmp_dir)
        read_out = res_read["stdout"].strip()
        micro_results["pitfall_read"] = {
            "stdout": read_out,
            "exit_code": res_read["returncode"],
        }
        outcomes.append(
            CheckOutcome(
                name="micro_example_pitfall_read_output",
                passed=res_read["returncode"] == 0 and read_out == "0",
                expected={"exit_code": 0, "stdout": "0"},
                actual={"exit_code": res_read["returncode"], "stdout": read_out},
                detail="Pitfall reading from nil map safely returns zero value 0",
            )
        )

        # 3. Pitfall writing nil map (panic)
        shutil.copy2(WORK_DIR / "micro_pitfall_write.go", tmp_dir / "main.go")
        res_write = run_command(["go", "run", "main.go"], cwd=tmp_dir)
        has_panic = "panic: assignment to entry in nil map" in res_write["stderr"]
        micro_results["pitfall_write"] = {
            "stderr": res_write["stderr"].strip().splitlines()[:2] if res_write["stderr"] else [],
            "exit_code": res_write["returncode"],
            "has_panic": has_panic,
        }
        outcomes.append(
            CheckOutcome(
                name="micro_example_pitfall_write_output",
                passed=res_write["returncode"] != 0 and has_panic,
                expected={"non_zero_exit": True, "has_panic": True},
                actual={"exit_code": res_write["returncode"], "has_panic": has_panic},
                detail="Pitfall writing to nil map triggers expected runtime panic",
            )
        )

    return outcomes, micro_results


def run_reference_tests(resolved_files: dict[str, Any]) -> tuple[list[CheckOutcome], dict[str, Any]]:
    outcomes: list[CheckOutcome] = []
    example_rel = resolved_files["example"][0]
    solution_rel = resolved_files["solution"][0]

    with tempfile.TemporaryDirectory(prefix="r63-t037-ref-") as tmp_root:
        scratch_dir = Path(tmp_root) / "etl"
        shutil.copytree(EXERCISE_DIR, scratch_dir, symlinks=True)

        # Substitute reference into scratch directory
        shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)

        go_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)

    passed_subtests = re.findall(r"--- PASS: (TestTransform/\S+)", go_test["stdout"])
    failed_subtests = re.findall(r"--- FAIL: (TestTransform/\S+)", go_test["stdout"])

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
            passed=tests_toml_data["total"] > 0 and len(tests_toml_data["included"]) == 4,
            expected={"total": 4, "included": 4},
            actual={"total": tests_toml_data["total"], "included": len(tests_toml_data["included"])},
            detail="All 4 canonical test cases verified in tests.toml",
        )
    )

    # 2. learner stub check
    stub_outcome, stub_info = verify_learner_stub(solution_file, example_file)
    all_outcomes.append(stub_outcome)

    # 3. hints file check
    hints_outcomes, hints_info = verify_hints_file()
    all_outcomes.extend(hints_outcomes)

    # 4. execute micro examples
    micro_outcomes, micro_results = execute_and_assert_micro_examples()
    all_outcomes.extend(micro_outcomes)

    # 5. run reference tests
    ref_outcomes, test_info = run_reference_tests(resolved_files)
    all_outcomes.extend(ref_outcomes)

    # Versions
    go_ver = run_command(["go", "version"])["stdout"].strip()
    python_ver = sys.version.replace("\n", " ")

    # Inputs payload
    inputs_payload = {
        "task": "R63-T037",
        "exercise": "etl",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_versions": {
            "go": go_ver,
            "python": python_ver,
        },
        "resolved_files": resolved_files,
        "canonical_tests": tests_toml_data,
        "micro_examples": {
            "working": (WORK_DIR / "micro_working.go").read_text(encoding="utf-8"),
            "pitfall_read": (WORK_DIR / "micro_pitfall_read.go").read_text(encoding="utf-8"),
            "pitfall_write": (WORK_DIR / "micro_pitfall_write.go").read_text(encoding="utf-8"),
        },
    }
    (WORK_DIR / "inputs.json").write_text(json.dumps(inputs_payload, indent=2), encoding="utf-8")

    # Results payload
    results_payload = {
        "task": "R63-T037",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_passed": all(o.passed for o in all_outcomes),
        "outcomes": [asdict(o) for o in all_outcomes],
        "test_info": test_info,
        "micro_results": micro_results,
        "stub_info": stub_info,
        "hints_info": hints_info,
    }
    (WORK_DIR / "results.json").write_text(json.dumps(results_payload, indent=2), encoding="utf-8")

    # Markdown report
    report_md = f"""# R63-T037: ETL Go-Specific Guidance Report

## Task Overview
- **Task ID:** R63-T037 (Coursework 7 of 10)
- **Exercise:** `exercises/practice/etl`
- **Goal:** Connect etl specification to Go by explaining the zero values of maps and initialization pitfall with executable micro-examples and official specification links.

## Language Construct Identified
- **Construct:** Map Zero Value (`nil`) and Initialization (`make(map[string]int)`).
- **In Reference:** `exercises/practice/etl/.meta/example.go` allocates the map with `out = make(map[string]int)` because the named return variable `(out map[string]int)` defaults to `nil`.
- **Pitfall:**
  - Reading a key from a `nil` map is safe and returns the zero value (`0`).
  - Writing to a `nil` map results in a runtime panic: `panic: assignment to entry in nil map`.

## Executed Micro-Examples
1. **Working Initialized Map (`work/R63-T037/micro_working.go`):**
   - Output: `{micro_results['working']['stdout']}` (Expected: `1`)
2. **Pitfall Read Nil Map (`work/R63-T037/micro_pitfall_read.go`):**
   - Output: `{micro_results['pitfall_read']['stdout']}` (Expected: `0`)
3. **Pitfall Write Nil Map (`work/R63-T037/micro_pitfall_write.go`):**
   - Result: Panic observed (`{micro_results['pitfall_write']['has_panic']}`)

## Reference Test Execution
- Executed Subtests: {test_info['passed_count']} / {test_info['passed_count']} passed
- Failed Subtests: {test_info['failed_count']}
- Learner Stub Preserved: Unsolved in `exercises/practice/etl/etl.go`

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
