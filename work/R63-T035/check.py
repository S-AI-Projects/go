#!/usr/bin/env python3
"""Verification script for R63-T035 (forth reference implementation scaling study)."""

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
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "forth"
DOCS_PATH = REPO_ROOT / "docs" / "maintenance" / "forth.md"


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


def check_example_complexity_comment(example_path: Path) -> CheckOutcome:
    """Verify example.go contains complexity and invariant comments."""
    text = example_path.read_text(encoding="utf-8")
    has_time_complexity = "Time Complexity: O(N)" in text
    has_space_complexity = "Space Complexity: O(N" in text
    has_invariant = "Invariant:" in text
    passed = has_time_complexity and has_space_complexity and has_invariant
    return CheckOutcome(
        name="example_complexity_comment",
        passed=passed,
        expected={
            "has_time_complexity": True,
            "has_space_complexity": True,
            "has_invariant": True,
        },
        actual={
            "has_time_complexity": has_time_complexity,
            "has_space_complexity": has_space_complexity,
            "has_invariant": has_invariant,
        },
    )


def check_maintenance_doc(doc_path: Path) -> CheckOutcome:
    """Verify docs/maintenance/forth.md documents sizes, timings, startup vs algorithm cost, and limits."""
    if not doc_path.is_file():
        return CheckOutcome(
            name="maintenance_doc",
            passed=False,
            expected=f"Existing file at {doc_path.relative_to(REPO_ROOT)}",
            actual="missing",
        )
    text = doc_path.read_text(encoding="utf-8")
    has_sizes = "Small (3 tokens" in text and "Medium (9 tokens" in text and "Large (27 tokens" in text
    has_repetitions = "5 Repetitions" in text or "five repetitions" in text.lower()
    has_cost_statement = "Process Startup" in text and "Algorithm Execution Work" in text
    has_limits = "Limit of the Conclusion" in text
    passed = has_sizes and has_repetitions and has_cost_statement and has_limits
    return CheckOutcome(
        name="maintenance_doc",
        passed=passed,
        expected={
            "has_three_sizes": True,
            "has_repetitions": True,
            "has_cost_statement": True,
            "has_limits": True,
        },
        actual={
            "has_three_sizes": has_sizes,
            "has_repetitions": has_repetitions,
            "has_cost_statement": has_cost_statement,
            "has_limits": has_limits,
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


def run_reference_and_scaling_tests(
    resolved_files: dict[str, list[str]],
) -> tuple[list[CheckOutcome], dict[str, Any], dict[str, Any]]:
    """Copy exercise to temp dir, swap in reference, run canonical tests and scaling study."""
    outcomes: list[CheckOutcome] = []
    solution_rel = resolved_files["solution"][0]
    example_rel = resolved_files["example"][0]

    scaling_harness = """package forth

import (
	"fmt"
	"slices"
	"testing"
	"time"
)

func TestScalingStudy(t *testing.T) {
	cases := []struct {
		name     string
		input    []string
		expected []int
		tokens   int
	}{
		{"Small", []string{"1 2 +"}, []int{3}, 3},
		{"Medium", []string{"1 2 + 4 * 5 + 3 -"}, []int{14}, 9},
		{"Large", []string{"1 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 +"}, []int{105}, 27},
	}

	for _, c := range cases {
		// Assert correctness prior to timing
		res, err := Forth(c.input)
		if err != nil || !slices.Equal(res, c.expected) {
			t.Fatalf("Correctness failed for %s: got %v, err %v", c.name, res, err)
		}

		var reps []int64
		for r := 0; r < 5; r++ {
			start := time.Now()
			for iter := 0; iter < 1000; iter++ {
				_, _ = Forth(c.input)
			}
			elapsedNs := time.Since(start).Nanoseconds() / 1000
			reps = append(reps, elapsedNs)
		}
		slices.Sort(reps)
		medianNs := reps[2]
		fmt.Printf("SCALING_RESULT: name=%s tokens=%d median_ns=%d reps=%v\\n", c.name, c.tokens, medianNs, reps)
	}
}
"""

    with tempfile.TemporaryDirectory(prefix="r63-t035-ref-") as tmp_root:
        scratch_dir = Path(tmp_root) / "forth"
        shutil.copytree(EXERCISE_DIR, scratch_dir, symlinks=True)

        # Substitute reference implementation only in the temporary copy
        shutil.copy2(scratch_dir / example_rel, scratch_dir / solution_rel)

        # 1. Run canonical test suite
        go_test = run_command(["go", "test", "-v", "-count=1", "./..."], cwd=scratch_dir)

        # 2. Run scaling study
        (scratch_dir / "scaling_test.go").write_text(scaling_harness, encoding="utf-8")
        scaling_run = run_command(["go", "test", "-v", "-run", "TestScalingStudy", "./..."], cwd=scratch_dir)

    passed_subtests = re.findall(r"--- PASS: (TestForth/\S+)", go_test["stdout"])
    failed_subtests = re.findall(r"--- FAIL: (TestForth/\S+)", go_test["stdout"])

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

    scaling_results = {}
    for line in scaling_run["stdout"].splitlines():
        m = re.match(r"SCALING_RESULT: name=(\w+) tokens=(\d+) median_ns=(\d+) reps=\[(.*?)\]", line)
        if m:
            scaling_results[m.group(1)] = {
                "tokens": int(m.group(2)),
                "median_ns": int(m.group(3)),
                "reps": [int(x) for x in m.group(4).split()],
            }

    has_three_sizes = len(scaling_results) == 3 and all(s in scaling_results for s in ("Small", "Medium", "Large"))
    outcomes.append(
        CheckOutcome(
            name="scaling_study_measurements",
            passed=scaling_run["returncode"] == 0 and has_three_sizes,
            expected={"three_sizes_measured": True, "returncode": 0},
            actual={"measured_sizes": list(scaling_results.keys()), "returncode": scaling_run["returncode"]},
        )
    )

    test_info = {
        "command": go_test["command"],
        "returncode": go_test["returncode"],
        "passed_subtests_count": len(passed_subtests),
        "passed_subtests": passed_subtests,
        "failed_subtests": failed_subtests,
    }
    return outcomes, test_info, scaling_results


def write_evidence(
    inputs_payload: dict[str, Any],
    results_payload: dict[str, Any],
) -> None:
    """Persist inputs, expected vs actual results, and markdown summary in work/R63-T035/."""
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
        "# R63-T035 Verification Report",
        "",
        f"- **Overall status:** {'PASS' if results_payload['all_passed'] else 'FAIL'}",
        f"- **Python version:** `{results_payload['tool_versions']['python']}`",
        f"- **Go version:** `{results_payload['tool_versions']['go']}`",
        f"- **Reference executed subtests:** {results_payload['reference_test']['passed_subtests_count']}",
        f"- **Scaling measurements:** {json.dumps(results_payload['scaling_results'])}",
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
    comment_outcome = check_example_complexity_comment(
        EXERCISE_DIR / resolved_files["example"][0]
    )
    doc_outcome = check_maintenance_doc(DOCS_PATH)
    test_outcomes, test_info, scaling_info = run_reference_and_scaling_tests(resolved_files)

    go_ver_cmd = run_command(["go", "version"])
    go_version = (
        go_ver_cmd["stdout"].strip()
        if go_ver_cmd["returncode"] == 0
        else f"unavailable ({go_ver_cmd['stderr'].strip()})"
    )

    all_outcomes = [
        *toml_outcomes,
        stub_outcome,
        comment_outcome,
        doc_outcome,
        *test_outcomes,
    ]
    all_passed = all(item.passed for item in all_outcomes)

    inputs_payload = {
        "exercise": "exercises/practice/forth",
        "config_path": str(config_path.relative_to(REPO_ROOT)),
        "resolved_files": resolved_files,
        "input_sizes": {
            "Small": {"tokens": 3, "input": ["1 2 +"]},
            "Medium": {"tokens": 9, "input": ["1 2 + 4 * 5 + 3 -"]},
            "Large": {"tokens": 27, "input": ["1 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 +"]},
        },
        "toml_summary": toml_summary,
    }
    results_payload = {
        "all_passed": all_passed,
        "tool_versions": {
            "python": sys.version.split()[0],
            "go": go_version,
        },
        "reference_test": test_info,
        "scaling_results": scaling_info,
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

    print(f"Executed reference subtests: {test_info['passed_subtests_count']}")
    print(f"Scaling results: {scaling_info}")
    for item in all_outcomes:
        status = "PASS" if item.passed else "FAIL"
        print(f"[{status}] {item.name}: expected={item.expected} actual={item.actual}")
        if item.detail:
            print(f"       detail: {item.detail}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
