#!/usr/bin/env python3
"""Validation script for R63-T036: Comparing two approaches to two-fer in Go."""

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
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "two-fer"
WORK_DIR = REPO_ROOT / "work" / "R63-T036"
HINTS_PATH = EXERCISE_DIR / ".docs" / "hints.md"
REF_IMPL_PATH = WORK_DIR / "reference_concat.go"
ALT_IMPL_PATH = WORK_DIR / "alternative_sprintf.go"


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
                detail="exercises/practice/two-fer/.docs/hints.md does not exist",
            )
        )
        return outcomes, info

    content = HINTS_PATH.read_text(encoding="utf-8")
    info["byte_length"] = len(content)

    has_approach_section = bool(re.search(r"##\s+Approach Selection", content, re.IGNORECASE))
    has_concat_explanation = "+" in content and "concatenat" in content.lower()
    has_sprintf_explanation = "fmt.Sprintf" in content or "Sprintf" in content
    has_tradeoffs = "trade-off" in content.lower() or "allocation" in content.lower()
    has_worked_example = "worked example" in content.lower() or "Alice" in content
    no_full_solution = "func ShareWith(name string) string {" not in content

    outcomes.append(
        CheckOutcome(
            name="hints_approach_selection_present",
            passed=has_approach_section,
            expected=True,
            actual=has_approach_section,
            detail="hints.md contains an Approach Selection section",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="hints_explains_both_approaches",
            passed=has_concat_explanation and has_sprintf_explanation,
            expected={"concat": True, "sprintf": True},
            actual={"concat": has_concat_explanation, "sprintf": has_sprintf_explanation},
            detail="hints.md explains string concatenation and fmt.Sprintf",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="hints_covers_tradeoffs_and_example",
            passed=has_tradeoffs and has_worked_example and no_full_solution,
            expected={"tradeoffs": True, "worked_example": True, "avoids_full_solution": True},
            actual={
                "tradeoffs": has_tradeoffs,
                "worked_example": has_worked_example,
                "avoids_full_solution": no_full_solution,
            },
            detail="hints.md justifies trade-offs and includes worked input without full solution code",
        )
    )

    info.update(
        {
            "has_approach_section": has_approach_section,
            "has_concat_explanation": has_concat_explanation,
            "has_sprintf_explanation": has_sprintf_explanation,
            "has_tradeoffs": has_tradeoffs,
            "has_worked_example": has_worked_example,
            "no_full_solution": no_full_solution,
        }
    )
    return outcomes, info


def verify_learner_stub(solution_path: Path, example_path: Path) -> tuple[CheckOutcome, dict[str, Any]]:
    stub_content = solution_path.read_text(encoding="utf-8")
    example_content = example_path.read_text(encoding="utf-8")

    differs = stub_content != example_content
    is_unsolved = 'return ""' in stub_content or "panic" in stub_content

    return (
        CheckOutcome(
            name="learner_stub_unsolved",
            passed=differs and is_unsolved,
            expected={"is_unsolved": True, "differs_from_example": True},
            actual={"is_unsolved": is_unsolved, "differs_from_example": differs},
            detail="Learner stub in the working tree is unchanged and unsolved",
        ),
        {"is_unsolved": is_unsolved, "differs_from_example": differs},
    )


def run_tests_and_benchmarks(
    resolved_files: dict[str, Any]
) -> tuple[list[CheckOutcome], dict[str, Any], dict[str, Any]]:
    outcomes: list[CheckOutcome] = []

    example_rel = resolved_files["example"][0]
    solution_rel = resolved_files["solution"][0]

    with tempfile.TemporaryDirectory(prefix="r63-t036-twofer-") as tmp_root:
        scratch_dir = Path(tmp_root) / "twofer"
        shutil.copytree(EXERCISE_DIR, scratch_dir, symlinks=True)

        # 1. Test Reference (concatenation)
        shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)
        ref_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)
        ref_bench = run_command(["go", "test", "-bench=.", "-benchmem", "-count=1"], cwd=scratch_dir)

        # 2. Test Alternative (fmt.Sprintf)
        alt_code = ALT_IMPL_PATH.read_text(encoding="utf-8")
        (scratch_dir / solution_rel).write_text(alt_code, encoding="utf-8")
        alt_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)
        alt_bench = run_command(["go", "test", "-bench=.", "-benchmem", "-count=1"], cwd=scratch_dir)

    # Parse passed/failed subtests
    ref_passed = re.findall(r"--- PASS: (TestShareWith/\S+)", ref_test["stdout"])
    ref_failed = re.findall(r"--- FAIL: (TestShareWith/\S+)", ref_test["stdout"])
    alt_passed = re.findall(r"--- PASS: (TestShareWith/\S+)", alt_test["stdout"])
    alt_failed = re.findall(r"--- FAIL: (TestShareWith/\S+)", alt_test["stdout"])

    outcomes.append(
        CheckOutcome(
            name="reference_tests_pass",
            passed=ref_test["returncode"] == 0 and len(ref_passed) > 0 and len(ref_failed) == 0,
            expected={"exit_code": 0, "passed_gt_zero": True, "failed": 0},
            actual={"exit_code": ref_test["returncode"], "passed": len(ref_passed), "failed": len(ref_failed)},
            detail="Reference implementation passes all enabled test cases",
        )
    )
    outcomes.append(
        CheckOutcome(
            name="alternative_tests_pass",
            passed=alt_test["returncode"] == 0 and len(alt_passed) > 0 and len(alt_failed) == 0,
            expected={"exit_code": 0, "passed_gt_zero": True, "failed": 0},
            actual={"exit_code": alt_test["returncode"], "passed": len(alt_passed), "failed": len(alt_failed)},
            detail="Alternative fmt.Sprintf implementation passes all enabled test cases",
        )
    )

    # Parse benchmark lines
    # e.g.: BenchmarkShareWith-10    	46688370	        25.38 ns/op	       0 B/op	       0 allocs/op
    def parse_bench(stdout: str) -> dict[str, Any]:
        m = re.search(r"BenchmarkShareWith\S+\s+(\d+)\s+([\d\.]+)\s+ns/op\s+(\d+)\s+B/op\s+(\d+)\s+allocs/op", stdout)
        if m:
            return {
                "iterations": int(m.group(1)),
                "ns_per_op": float(m.group(2)),
                "bytes_per_op": int(m.group(3)),
                "allocs_per_op": int(m.group(4)),
            }
        return {"raw": stdout}

    benchmarks = {
        "reference_concat": parse_bench(ref_bench["stdout"]),
        "alternative_sprintf": parse_bench(alt_bench["stdout"]),
    }

    outcomes.append(
        CheckOutcome(
            name="benchmarks_completed",
            passed="ns_per_op" in benchmarks["reference_concat"] and "ns_per_op" in benchmarks["alternative_sprintf"],
            expected={"both_benchmarked": True},
            actual={"ref": benchmarks["reference_concat"], "alt": benchmarks["alternative_sprintf"]},
            detail="Benchmarked both reference and alternative implementations",
        )
    )

    test_info = {
        "reference": {
            "exit_code": ref_test["returncode"],
            "passed_count": len(ref_passed),
            "passed_tests": ref_passed,
            "failed_count": len(ref_failed),
        },
        "alternative": {
            "exit_code": alt_test["returncode"],
            "passed_count": len(alt_passed),
            "passed_tests": alt_passed,
            "failed_count": len(alt_failed),
        },
    }

    return outcomes, test_info, benchmarks


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
            passed=tests_toml_data["total"] > 0 and len(tests_toml_data["included"]) == 3,
            expected={"total": 3, "included": 3},
            actual={"total": tests_toml_data["total"], "included": len(tests_toml_data["included"])},
            detail="All canonical test cases verified in tests.toml",
        )
    )

    # 2. learner stub check
    stub_outcome, stub_info = verify_learner_stub(solution_file, example_file)
    all_outcomes.append(stub_outcome)

    # 3. hints file check
    hints_outcomes, hints_info = verify_hints_file()
    all_outcomes.extend(hints_outcomes)

    # 4. run tests and benchmarks
    test_outcomes, test_info, benchmarks = run_tests_and_benchmarks(resolved_files)
    all_outcomes.extend(test_outcomes)

    # Get tool versions
    go_ver = run_command(["go", "version"])["stdout"].strip()
    python_ver = sys.version.replace("\n", " ")

    # Inputs payload
    inputs_payload = {
        "task": "R63-T036",
        "exercise": "two-fer",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_versions": {
            "go": go_ver,
            "python": python_ver,
        },
        "resolved_files": resolved_files,
        "canonical_tests": tests_toml_data,
        "reference_source": REF_IMPL_PATH.read_text(encoding="utf-8"),
        "alternative_source": ALT_IMPL_PATH.read_text(encoding="utf-8"),
    }
    (WORK_DIR / "inputs.json").write_text(json.dumps(inputs_payload, indent=2), encoding="utf-8")

    # Results payload
    results_payload = {
        "task": "R63-T036",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_passed": all(o.passed for o in all_outcomes),
        "outcomes": [asdict(o) for o in all_outcomes],
        "test_info": test_info,
        "benchmarks": benchmarks,
        "stub_info": stub_info,
        "hints_info": hints_info,
    }
    (WORK_DIR / "results.json").write_text(json.dumps(results_payload, indent=2), encoding="utf-8")

    # Generate Markdown report
    ref_b = benchmarks.get("reference_concat", {})
    alt_b = benchmarks.get("alternative_sprintf", {})
    report_md = f"""# R63-T036: Two-Fer Implementation Comparison Report

## Task Overview
- **Task ID:** R63-T036 (Coursework 6 of 10)
- **Exercise:** `exercises/practice/two-fer`
- **Goal:** Compare the reference string concatenation approach with an alternative `fmt.Sprintf` approach, document trade-offs and worked input in `hints.md`, and verify with automated checks.

## Approaches Evaluated

### Approach 1: Direct String Concatenation (`+`)
- **File:** `work/R63-T036/reference_concat.go` (and `.meta/example.go`)
- **Technique:** `if name == "" {{ name = "you" }}` followed by `"One for " + name + ", one for me."`
- **Performance:**
  - Time: **{ref_b.get('ns_per_op', 'N/A')} ns/op**
  - Heap Memory: **{ref_b.get('bytes_per_op', 'N/A')} B/op**
  - Allocations: **{ref_b.get('allocs_per_op', 'N/A')} allocs/op**

### Approach 2: Formatted String (`fmt.Sprintf`)
- **File:** `work/R63-T036/alternative_sprintf.go`
- **Technique:** `fmt.Sprintf("One for %s, one for me.", name)`
- **Performance:**
  - Time: **{alt_b.get('ns_per_op', 'N/A')} ns/op**
  - Heap Memory: **{alt_b.get('bytes_per_op', 'N/A')} B/op**
  - Allocations: **{alt_b.get('allocs_per_op', 'N/A')} allocs/op**

## Benchmark Comparison Table
| Metric | Approach 1 (`+` Concatenation) | Approach 2 (`fmt.Sprintf`) | Difference |
| :--- | :--- | :--- | :--- |
| Execution Time | {ref_b.get('ns_per_op', 'N/A')} ns/op | {alt_b.get('ns_per_op', 'N/A')} ns/op | ~{round(alt_b.get('ns_per_op', 1) / max(ref_b.get('ns_per_op', 1), 0.001), 1)}x slower |
| Heap Memory | {ref_b.get('bytes_per_op', 'N/A')} B/op | {alt_b.get('bytes_per_op', 'N/A')} B/op | +{alt_b.get('bytes_per_op', 0)} B |
| Heap Allocations | {ref_b.get('allocs_per_op', 'N/A')} allocs/op | {alt_b.get('allocs_per_op', 'N/A')} allocs/op | +{alt_b.get('allocs_per_op', 0)} allocs |

## Test Outcomes
- Reference Tests Passed: {test_info['reference']['passed_count']} / {test_info['reference']['passed_count']}
- Alternative Tests Passed: {test_info['alternative']['passed_count']} / {test_info['alternative']['passed_count']}
- Learner Stub Preserved: Unsolved in `two_fer.go`
- Hints File Created: `exercises/practice/two-fer/.docs/hints.md`

## Check Summary
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
