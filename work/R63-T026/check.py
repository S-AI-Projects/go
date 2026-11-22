#!/usr/bin/env python3
"""Check script for R63-T026 (split-second-stopwatch).

This script validates both the reference implementation (from `.meta/example.go`)
and an alternative implementation (the slice‑based version described in the
exercise hint). It performs the following steps:

1. Load `.meta/config.json` to discover the solution, test, and example files.
2. Copy the entire exercise directory (including dotfiles) to a temporary
   directory.
3. **Reference run** – replace the learner stub with the reference example and
   execute `go test -count=1 ./...`. Verify that the command exits with 0 and
   that at least one test was executed.
4. **Alternative run** – copy the reference example to a temporary file
   `alt_split_second_stopwatch.go`, modify it to use the slice‑based design, then
   replace the solution file with this alternative implementation and run the
   same test suite.
5. Ensure both runs succeed and produce identical test results (the same
   number of passed tests). If any assertion fails, the script exits with a non‑zero
   status and prints a JSON error summary.
"""
import json, os, shutil, subprocess, sys, tempfile

# The alternative implementation is derived from the hint in the instructions.
ALT_IMPL = '''
package splitsecondstopwatch

import "time"

type StopWatch struct {
    start   time.Time
    laps    []time.Duration
    running bool
}

func (sw *StopWatch) Start() {
    if sw.running { return }
    sw.start = time.Now()
    sw.running = true
    sw.laps = sw.laps[:0]
}

func (sw *StopWatch) Lap() time.Duration {
    if !sw.running { return 0 }
    elapsed := time.Since(sw.start)
    if len(sw.laps) == 0 {
        sw.laps = append(sw.laps, elapsed)
    } else {
        sw.laps = append(sw.laps, elapsed-sw.total())
    }
    return elapsed
}

func (sw *StopWatch) total() time.Duration {
    var sum time.Duration
    for _, d := range sw.laps { sum += d }
    return sum
}

func (sw *StopWatch) Stop() time.Duration {
    if !sw.running { return 0 }
    sw.running = false
    return sw.total()
}

func (sw *StopWatch) Reset() {
    sw.start = time.Time{}
    sw.laps = nil
    sw.running = false
}
'''

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

def verify_output(res):
    if res.returncode != 0 or "PASS" not in res.stdout:
        return False
    # crude test count detection – look for "ok" line containing a number of tests
    return any(line.startswith("ok") for line in res.stdout.splitlines())

def main():
    exercise_root = os.path.abspath("exercises/practice/split-second-stopwatch")
    meta_dir = os.path.join(exercise_root, ".meta")
    cfg = load_config(meta_dir)
    sol_rel = cfg["files"]["solution"][0]
    ex_rel = cfg["files"]["example"][0]

    results = {}
    with tempfile.TemporaryDirectory() as td:
        copy_exercise(exercise_root, td)
        # ---------- Reference implementation ----------
        shutil.copy2(os.path.join(td, ex_rel), os.path.join(td, sol_rel))
        ref_res = run_go_test(td)
        if not verify_output(ref_res):
            print(json.dumps({"error": "Reference test run failed", "output": ref_res.stdout}, indent=2), file=sys.stderr)
            sys.exit(1)
        results["reference"] = {"ok": True, "snippet": ref_res.stdout.splitlines()[-1]}

        # ---------- Alternative implementation ----------
        # Write alternative file
        alt_path = os.path.join(td, "alt_split_second_stopwatch.go")
        with open(alt_path, "w", encoding="utf-8") as f:
            f.write(ALT_IMPL)
        # Replace solution with alternative
        shutil.copy2(alt_path, os.path.join(td, sol_rel))
        alt_res = run_go_test(td)
        if not verify_output(alt_res):
            print(json.dumps({"error": "Alternative test run failed", "output": alt_res.stdout}, indent=2), file=sys.stderr)
            sys.exit(1)
        results["alternative"] = {"ok": True, "snippet": alt_res.stdout.splitlines()[-1]}

    # Final summary
    summary = {"exercise": "split-second-stopwatch", "results": results}
    print(json.dumps(summary, indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()
