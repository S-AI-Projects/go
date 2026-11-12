#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    work_dir = Path(__file__).resolve().parent
    exercise_rel = "exercises/practice/dnd-character"
    exercise_path = repo_root / exercise_rel
    config_file = exercise_path / ".meta" / "config.json"

    print("=== [R63-T005] Automated Check ===")

    # 1. Collect tool versions
    go_ver = subprocess.check_output(["go", "version"], text=True).strip()
    py_ver = sys.version.replace("\n", " ")
    print(f"Tool versions: {go_ver} | Python: {py_ver}")
    with open(work_dir / "tool_versions.txt", "w") as f:
        f.write(f"Go: {go_ver}\nPython: {py_ver}\n")

    # 2. Check config.json exists and load paths
    if not config_file.exists():
        raise AssertionError(f"config.json not found at {config_file}")
    with open(config_file, "r") as f:
        config = json.load(f)

    solution_files = config.get("files", {}).get("solution", [])
    test_files = config.get("files", {}).get("test", [])
    example_files = config.get("files", {}).get("example", [])

    if not solution_files or not example_files:
        raise AssertionError("Missing solution or example files in config.json")

    solution_filename = solution_files[0]
    example_filename = example_files[0]

    # 3. Assert learner stub remains unsolved
    learner_solution_path = exercise_path / solution_filename
    if not learner_solution_path.exists():
        raise AssertionError(f"Learner solution file {learner_solution_path} does not exist")
    with open(learner_solution_path, "r") as f:
        learner_content = f.read()
    if 'panic("Please implement' not in learner_content:
        raise AssertionError("Learner solution stub appears modified or solved! It must remain unsolved.")
    print("✔ Confirmed learner stub is unsolved.")

    # 4. Verify complexity comment exists in example.go
    example_path = exercise_path / example_filename
    with open(example_path, "r") as f:
        example_content = f.read()
    if "Complexity: O(1)" not in example_content:
        raise AssertionError("Complexity comment not found in example.go")
    print("✔ Complexity and invariant comment verified in example.go.")

    # 5. Execute reference in an isolated scratch directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise = Path(tmpdir) / "exercise"
        shutil.copytree(exercise_path, tmp_exercise, symlinks=True)

        target_solution = tmp_exercise / solution_filename
        shutil.copyfile(tmp_exercise / example_filename, target_solution)

        cmd = ["go", "test", "-count=1", "-v", "./..."]
        proc = subprocess.run(cmd, cwd=tmp_exercise, capture_output=True, text=True)

        print("=== Test Output Preview ===")
        print(proc.stdout[:400] + ("..." if len(proc.stdout) > 400 else ""))

        if proc.returncode != 0:
            print("STDERR:\n", proc.stderr)
            raise AssertionError(f"go test failed with non-zero exit code: {proc.returncode}")

        executed_tests = [l.strip() for l in proc.stdout.splitlines() if l.strip().startswith("--- PASS:")]
        case_count = len(executed_tests)
        print(f"Executed test count: {case_count}")
        if case_count == 0:
            raise AssertionError("Zero tests executed! Verification failed.")

    # 6. Run in-process micro-measurement script to distinguish algorithmic work from startup overhead
    # We measure Modifier across 3 representative input sizes: min (3), mid (10), max (18)
    # and report medians across 5 repetitions.
    bench_code = """package main

import (
	"fmt"
	"math"
	"sort"
	"time"
)

func Modifier(score int) int {
	return int(math.Floor(float64(score-10) / 2.0))
}

func measure(score int, iters int) int64 {
	start := time.Now()
	for i := 0; i < iters; i++ {
		_ = Modifier(score)
	}
	return time.Since(start).Nanoseconds() / int64(iters)
}

func main() {
	scores := []int{3, 10, 18}
	const iters = 100000
	const reps = 5

	for _, s := range scores {
		var samples []int64
		for r := 0; r < reps; r++ {
			samples = append(samples, measure(s, iters))
		}
		sort.Slice(samples, func(i, j int) bool { return samples[i] < samples[j] })
		median := samples[len(samples)/2]
		fmt.Printf("SCORE_%d_MEDIAN_NS=%d\\n", s, median)
	}
}
"""
    with tempfile.TemporaryDirectory() as tmpbench:
        main_file = Path(tmpbench) / "main.go"
        with open(main_file, "w") as f:
            f.write(bench_code)
        bench_proc = subprocess.run(["go", "run", "main.go"], cwd=tmpbench, capture_output=True, text=True)
        if bench_proc.returncode != 0:
            raise AssertionError(f"Benchmark helper failed: {bench_proc.stderr}")
        print("✔ Timing measurements completed:")
        print(bench_proc.stdout.strip())

    # 7. Save check results to work/R63-T005/results.json
    results_data = {
        "task_id": "R63-T005",
        "exercise": exercise_rel,
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "complexity": "O(1) time and space",
        "measurements": bench_proc.stdout.strip().splitlines(),
        "test_run": {
            "exit_code": proc.returncode,
            "executed_cases_count": case_count,
            "executed_tests": executed_tests
        },
        "status": "PASS"
    }

    with open(work_dir / "results.json", "w") as f:
        json.dump(results_data, f, indent=2)

    print("✔ All assertions passed successfully. Results saved to work/R63-T005/results.json")

if __name__ == "__main__":
    main()
