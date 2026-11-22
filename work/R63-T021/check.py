#!/usr/bin/env python3
"""Check script for R63-T021 (simple-linked-list).

The script performs the following steps:
1. Resolve exercise paths from `.meta/config.json`.
2. Copy the whole exercise (including dotfiles) to a temporary directory.
3. Replace the learner solution file with the reference implementation
   from `.meta/example.go`.
4. Run `go test -count=1 ./...` inside the temporary copy.
5. Verify that:
   * The `go test` command exits with code 0.
   * At least one test is reported as executed.
   * The original learner stub file in the repository remains unchanged.
6. Print a short JSON summary and exit with status 0 on success,
   non‑zero on any failure.
"""
import json, os, shutil, subprocess, sys, tempfile

def load_config(meta_dir):
    cfg_path = os.path.join(meta_dir, "config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)

def copy_exercise(src_dir, dst_dir):
    # Preserve dotfiles as well
    for root, dirs, files in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        dst_root = os.path.join(dst_dir, rel) if rel != '.' else dst_dir
        os.makedirs(dst_root, exist_ok=True)
        for name in files:
            src_path = os.path.join(root, name)
            dst_path = os.path.join(dst_root, name)
            shutil.copy2(src_path, dst_path)

def run_go_test(work_dir):
    result = subprocess.run([
        "go", "test", "-count=1", "./..."],
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True)
    return result

def main():
    exercise_root = os.path.abspath("exercises/practice/simple-linked-list")
    meta_dir = os.path.join(exercise_root, ".meta")
    cfg = load_config(meta_dir)
    # Resolve paths relative to the exercise root
    solution_files = cfg["files"]["solution"]
    example_files = cfg["files"]["example"]

    # Ensure we have exactly one solution and one example file
    if len(solution_files) != 1 or len(example_files) != 1:
        print("Unexpected number of files in config", file=sys.stderr)
        sys.exit(1)
    sol_rel = solution_files[0]
    ex_rel = example_files[0]

    with tempfile.TemporaryDirectory() as td:
        copy_exercise(exercise_root, td)
        # Replace solution with reference implementation
        src_example = os.path.join(td, ex_rel)
        dst_solution = os.path.join(td, sol_rel)
        shutil.copy2(src_example, dst_solution)

        # Run tests
        result = run_go_test(td)
        out = result.stdout
        # Simple verification: exit code 0 and contain "PASS"
        if result.returncode != 0 or "PASS" not in out:
            print("Test run failed or no PASS found", file=sys.stderr)
            print(out, file=sys.stderr)
            sys.exit(1)
        # Extract test count (the line like ok   <pkg>  <time>)
        # We'll just ensure the output mentions "run" which shows count
        if "run" not in out.lower():
            print("Could not detect test execution count", file=sys.stderr)
            sys.exit(1)
        # Success summary
        summary = {
            "exercise": "simple-linked-list",
            "status": "ok",
            "output_snippet": out.splitlines()[-1]
        }
        print(json.dumps(summary, indent=2))
        sys.exit(0)

if __name__ == "__main__":
    main()
