#!/usr/bin/env python3
"""Check script for R63-T022 (word-count).

It copies the exercise to a temporary directory, substitutes the reference
implementation, runs the test suite, and verifies that at least one test
executed and that the command succeeded.
"""
import json, os, shutil, subprocess, sys, tempfile

def load_config(meta_dir):
    cfg_path = os.path.join(meta_dir, "config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)

def copy_exercise(src_dir, dst_dir):
    for root, dirs, files in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        dst_root = os.path.join(dst_dir, rel) if rel != '.' else dst_dir
        os.makedirs(dst_root, exist_ok=True)
        for name in files:
            shutil.copy2(os.path.join(root, name), os.path.join(dst_root, name))

def run_go_test(work_dir):
    result = subprocess.run(["go", "test", "-count=1", "./..."],
        cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return result

def main():
    exercise_root = os.path.abspath("exercises/practice/word-count")
    meta_dir = os.path.join(exercise_root, ".meta")
    cfg = load_config(meta_dir)
    sol_rel = cfg["files"]["solution"][0]
    ex_rel = cfg["files"]["example"][0]

    with tempfile.TemporaryDirectory() as td:
        copy_exercise(exercise_root, td)
        # Replace solution with reference implementation
        shutil.copy2(os.path.join(td, ex_rel), os.path.join(td, sol_rel))
        result = run_go_test(td)
        if result.returncode != 0 or "PASS" not in result.stdout:
            print("Reference test run failed", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            sys.exit(1)
        # Success
        summary = {"exercise": "word-count", "status": "ok", "output": result.stdout.splitlines()[-1]}
        print(json.dumps(summary, indent=2))
        sys.exit(0)

if __name__ == "__main__":
    main()
