#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    work_dir = Path(__file__).resolve().parent
    exercise_rel = "exercises/practice/series"
    exercise_path = repo_root / exercise_rel
    config_file = exercise_path / ".meta" / "config.json"
    hints_file = exercise_path / ".docs" / "hints.md"

    print("=== [R63-T007] Automated Check ===")

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
    if 'panic("Please implement the All function")' not in learner_content:
        raise AssertionError("Learner solution stub appears modified or solved! It must remain unsolved.")
    print("✔ Confirmed learner stub is unsolved.")

    # 4. Verify hints.md guidance and references
    if not hints_file.exists():
        raise AssertionError(f"hints.md missing at {hints_file}")
    with open(hints_file, "r") as f:
        hints_content = f.read()
    if "s[low:high]" not in hints_content or "https://go.dev/ref/spec#Slice_expressions" not in hints_content:
        raise AssertionError("hints.md missing required language references or slice expression construct")
    print("✔ hints.md content and specification links validated.")

    # 5. Execute micro-examples directly in Go and assert expected output
    snippet1 = """package main
import "fmt"
func main() {
    s := "49142"
    sub := s[0:3]
    fmt.Printf("%s\\n", sub)
}
"""
    with tempfile.TemporaryDirectory() as tmp1:
        f1 = Path(tmp1) / "main.go"
        with open(f1, "w") as f:
            f.write(snippet1)
        res1 = subprocess.run(["go", "run", "main.go"], cwd=tmp1, capture_output=True, text=True)
        if res1.returncode != 0:
            raise AssertionError(f"Micro-example 1 compilation failed: {res1.stderr}")
        out1 = res1.stdout.strip()
        if out1 != "491":
            raise AssertionError(f"Micro-example 1 output mismatch: got {out1!r}, expected '491'")
        print("✔ Micro-example 1 executed and returned expected output: '491'")

    snippet2 = """package main
import "fmt"
func main() {
    s := "491€2"
    sub := s[0:4]
    fmt.Printf("%q\\n", sub)
}
"""
    with tempfile.TemporaryDirectory() as tmp2:
        f2 = Path(tmp2) / "main.go"
        with open(f2, "w") as f:
            f.write(snippet2)
        res2 = subprocess.run(["go", "run", "main.go"], cwd=tmp2, capture_output=True, text=True)
        if res2.returncode != 0:
            raise AssertionError(f"Micro-example 2 compilation failed: {res2.stderr}")
        out2 = res2.stdout.strip()
        if out2 != '"491\\xe2"':
            raise AssertionError(f"Micro-example 2 output mismatch: got {out2!r}, expected '\"491\\\\xe2\"'")
        print('✔ Micro-example 2 executed and returned expected output: \'"491\\xe2"\'')

    # 6. Execute reference in an isolated scratch directory
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

    # 7. Save check results to work/R63-T007/results.json
    results_data = {
        "task_id": "R63-T007",
        "exercise": exercise_rel,
        "tool_versions": {
            "go": go_ver,
            "python": py_ver
        },
        "micro_example_1": {
            "output": out1,
            "expected": "491"
        },
        "micro_example_2": {
            "output": out2,
            "expected": '"491\\xe2"'
        },
        "test_run": {
            "exit_code": proc.returncode,
            "executed_cases_count": case_count,
            "executed_tests": executed_tests
        },
        "status": "PASS"
    }

    with open(work_dir / "results.json", "w") as f:
        json.dump(results_data, f, indent=2)

    print("✔ All assertions passed successfully. Results saved to work/R63-T007/results.json")

if __name__ == "__main__":
    main()
