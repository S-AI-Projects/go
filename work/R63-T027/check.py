#!/usr/bin/env python3
"""
Verification script for R63-T027:
- Resolves paths from exercises/practice/rectangles/.meta/config.json
- Copies the exercise to a temporary directory (including dotfiles)
- Substitutes the reference implementation into the solution filename only in that temporary copy
- Runs: go test -count=1 ./... in the scratch module
- Checks return codes and test counts (fails on 0 tests, child error, or assertion failure)
- Verifies the working tree learner solution stub is unchanged and unsolved
- Executes both micro-examples and asserts outputs agree with published hint/guidance
- Asserts the guidance document names the reference construct and explains its relevance
- Records tool versions, inputs, and expected vs actual results in work/R63-T027/
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

def get_tool_versions():
    versions = {}
    try:
        r = subprocess.run(["go", "version"], capture_output=True, text=True, check=True)
        versions["go"] = r.stdout.strip()
    except Exception as e:
        versions["go"] = f"error: {e}"

    try:
        r = subprocess.run(["python3", "--version"], capture_output=True, text=True, check=True)
        versions["python3"] = r.stdout.strip()
    except Exception as e:
        versions["python3"] = f"error: {e}"

    try:
        r = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True)
        versions["git"] = r.stdout.strip()
    except Exception as e:
        versions["git"] = f"error: {e}"

    return versions

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    work_dir = os.path.join(repo_root, "work", "R63-T027")
    os.makedirs(work_dir, exist_ok=True)

    exercise_dir = os.path.join(repo_root, "exercises", "practice", "rectangles")
    config_path = os.path.join(exercise_dir, ".meta", "config.json")

    results_data = {
        "task": "R63-T027",
        "exercise": "rectangles",
        "checks": [],
        "tool_versions": get_tool_versions(),
        "success": False,
    }

    print("=== Step 1: Resolving paths from config.json ===")
    assert os.path.exists(config_path), f"config.json not found at {config_path}"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_rel = config["files"]["solution"][0]
    example_rel = config["files"]["example"][0]
    test_files_rel = config["files"]["test"]

    solution_src = os.path.join(exercise_dir, solution_rel)
    example_src = os.path.join(exercise_dir, example_rel)
    test_sources = [os.path.join(exercise_dir, t) for t in test_files_rel]

    assert os.path.exists(solution_src), f"Solution file not found: {solution_src}"
    assert os.path.exists(example_src), f"Example file not found: {example_src}"
    for ts in test_sources:
        assert os.path.exists(ts), f"Test file not found: {ts}"

    results_data["checks"].append({
        "name": "path_resolution",
        "status": "PASS",
        "resolved": {
            "solution": solution_rel,
            "example": example_rel,
            "tests": test_files_rel,
        }
    })
    print(f"Resolved solution: {solution_rel}")
    print(f"Resolved example: {example_rel}")
    print(f"Resolved tests: {test_files_rel}")

    print("\n=== Step 2: Verifying learner stub is unchanged in working tree ===")
    with open(solution_src, "r", encoding="utf-8") as f:
        learner_stub_content = f.read()

    assert "panic(\"Please implement the Count function\")" in learner_stub_content, (
        "Learner stub in working tree must remain unsolved!"
    )
    results_data["checks"].append({
        "name": "learner_stub_unsolved",
        "status": "PASS",
        "details": "rectangles.go still contains panic stub"
    })
    print("Learner stub in working tree is verified unsolved.")

    print("\n=== Step 3: Running reference implementation in temporary scratch copy ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        scratch_exercise = os.path.join(tmpdir, "rectangles")
        # Copy entire exercise including dotfiles (.docs, .meta)
        shutil.copytree(exercise_dir, scratch_exercise)

        scratch_solution = os.path.join(scratch_exercise, solution_rel)
        scratch_example = os.path.join(scratch_exercise, example_rel)

        # Substitute reference into solution filename only in the scratch copy
        shutil.copyfile(scratch_example, scratch_solution)

        # Run go test -count=1 ./...
        cmd_standard = ["go", "test", "-count=1", "./..."]
        res_standard = subprocess.run(cmd_standard, cwd=scratch_exercise, capture_output=True, text=True)

        # Also run with -v to inspect individual test case execution counts and names
        cmd_verbose = ["go", "test", "-v", "-count=1", "./..."]
        res_verbose = subprocess.run(cmd_verbose, cwd=scratch_exercise, capture_output=True, text=True)

        # Save test output
        test_output_file = os.path.join(work_dir, "test_output.txt")
        with open(test_output_file, "w", encoding="utf-8") as f:
            f.write(f"=== Command: {' '.join(cmd_standard)} ===\n")
            f.write(f"Return code: {res_standard.returncode}\n")
            f.write(f"Output:\n{res_standard.stdout}\n")
            if res_standard.stderr:
                f.write(f"Stderr:\n{res_standard.stderr}\n")
            f.write(f"\n=== Command: {' '.join(cmd_verbose)} ===\n")
            f.write(f"Return code: {res_verbose.returncode}\n")
            f.write(f"Output:\n{res_verbose.stdout}\n")

        print(f"Standard test return code: {res_standard.returncode}")
        assert res_standard.returncode == 0, f"go test failed with code {res_standard.returncode}:\n{res_standard.stdout}\n{res_standard.stderr}"
        assert res_verbose.returncode == 0, f"go test -v failed with code {res_verbose.returncode}:\n{res_verbose.stdout}\n{res_verbose.stderr}"

        # Parse passed subtests
        subtests = re.findall(r"--- PASS:\s+TestRectangles/(\S+)", res_verbose.stdout)
        test_count = len(subtests)
        print(f"Executed test cases count: {test_count}")
        print(f"Executed subtests: {subtests}")

        assert test_count > 0, "Zero test run! Must fail on zero-test run."
        assert test_count == 14, f"Expected 14 test cases, found {test_count}"

        # Check against tests.toml
        tests_toml_path = os.path.join(exercise_dir, ".meta", "tests.toml")
        with open(tests_toml_path, "r", encoding="utf-8") as f:
            tests_toml_content = f.read()

        toml_descriptions = re.findall(r'description\s*=\s*"([^"]+)"', tests_toml_content)
        print(f"Found {len(toml_descriptions)} cases in tests.toml: {toml_descriptions}")
        assert len(toml_descriptions) == 14, f"Expected 14 descriptions in tests.toml, found {len(toml_descriptions)}"

        results_data["checks"].append({
            "name": "scratch_reference_test",
            "status": "PASS",
            "test_count": test_count,
            "executed_cases": subtests,
            "toml_cases": toml_descriptions,
            "return_code": res_standard.returncode,
        })

    # Double check that working tree was NOT rewritten
    with open(solution_src, "r", encoding="utf-8") as f:
        content_after = f.read()
    assert content_after == learner_stub_content, "Working tree solution was modified!"

    print("\n=== Step 4: Executing micro-examples and asserting outputs ===")
    micro_ex_1_code = """package main

import "fmt"

func main() {
	asciiLine := "+--+"
	firstByte := asciiLine[0]
	asciiMatch := firstByte == '+'
	asciiLen := len(asciiLine)
	fmt.Printf("firstByte=%d char=%c match=%t len=%d\\n", firstByte, firstByte, asciiMatch, asciiLen)
}
"""

    micro_ex_2_code = """package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	unicodeLine := "┌──┐"
	unicodeByte := unicodeLine[0]
	unicodeMatch := rune(unicodeByte) == '┌'
	byteLen := len(unicodeLine)
	runeCount := utf8.RuneCountInString(unicodeLine)
	fmt.Printf("firstByte=%d rune=┌ match=%t byteLen=%d runeCount=%d\\n", unicodeByte, unicodeMatch, byteLen, runeCount)
}
"""

    with tempfile.TemporaryDirectory() as td:
        # Run Micro-example 1
        src1 = os.path.join(td, "snippet1.go")
        with open(src1, "w", encoding="utf-8") as f:
            f.write(micro_ex_1_code)
        r1 = subprocess.run(["go", "run", src1], capture_output=True, text=True, check=True)
        out1 = r1.stdout.strip()
        print(f"Micro-example 1 Output: {out1}")
        expected_out1 = "firstByte=43 char=+ match=true len=4"
        assert out1 == expected_out1, f"Micro-example 1 output mismatch: got {out1!r}, want {expected_out1!r}"

        # Run Micro-example 2
        src2 = os.path.join(td, "snippet2.go")
        with open(src2, "w", encoding="utf-8") as f:
            f.write(micro_ex_2_code)
        r2 = subprocess.run(["go", "run", src2], capture_output=True, text=True, check=True)
        out2 = r2.stdout.strip()
        print(f"Micro-example 2 Output: {out2}")
        expected_out2 = "firstByte=226 rune=┌ match=false byteLen=12 runeCount=4"
        assert out2 == expected_out2, f"Micro-example 2 output mismatch: got {out2!r}, want {expected_out2!r}"

    results_data["checks"].append({
        "name": "micro_example_1_ascii_byte_indexing",
        "status": "PASS",
        "input": "+--+",
        "actual": out1,
        "expected": expected_out1,
    })
    results_data["checks"].append({
        "name": "micro_example_2_unicode_pitfall",
        "status": "PASS",
        "input": "┌──┐",
        "actual": out2,
        "expected": expected_out2,
    })

    print("\n=== Step 5: Checking published guidance/hint document ===")
    guidance_file = os.path.join(exercise_dir, ".docs", "instructions.append.md")
    assert os.path.exists(guidance_file), f"Guidance file not found: {guidance_file}"

    with open(guidance_file, "r", encoding="utf-8") as f:
        guidance_text = f.read()

    # Verify guidance mentions the construct used in example.go
    assert "rune versus byte handling" in guidance_text.lower() or "byte indexing" in guidance_text.lower(), (
        "Guidance must name rune versus byte handling construct"
    )
    assert "diagram[rowIndex][i]" in guidance_text or "diagram[y][x]" in guidance_text, (
        "Guidance must reference the construct actually present in example.go"
    )
    assert "ascii" in guidance_text.lower(), "Guidance must explain relevance to ASCII input in rectangles"

    # Verify guidance includes both micro-example expected outputs
    assert expected_out1 in guidance_text, f"Guidance must publish micro-example 1 output: {expected_out1}"
    assert expected_out2 in guidance_text, f"Guidance must publish micro-example 2 output: {expected_out2}"

    # Verify why outcomes differ is explained
    assert "why the outcomes differ" in guidance_text.lower() or "differ" in guidance_text.lower(), (
        "Guidance must explain why the outcomes differ"
    )

    results_data["checks"].append({
        "name": "published_guidance_verification",
        "status": "PASS",
        "guidance_path": guidance_file,
        "construct_named": "rune versus byte handling (string byte indexing)",
        "micro_example_1_output_agreed": True,
        "micro_example_2_output_agreed": True,
    })
    print("Published guidance verified successfully.")

    print("\n=== Step 6: Writing results and evidence to work/R63-T027/ ===")
    results_data["success"] = True

    tool_versions_file = os.path.join(work_dir, "tool_versions.json")
    with open(tool_versions_file, "w", encoding="utf-8") as f:
        json.dump(results_data["tool_versions"], f, indent=2)

    tool_versions_txt = os.path.join(work_dir, "tool_versions.txt")
    with open(tool_versions_txt, "w", encoding="utf-8") as f:
        for k, v in results_data["tool_versions"].items():
            f.write(f"{k}: {v}\n")

    results_json_file = os.path.join(work_dir, "results.json")
    with open(results_json_file, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    inputs_and_results_file = os.path.join(work_dir, "inputs_and_results.txt")
    with open(inputs_and_results_file, "w", encoding="utf-8") as f:
        f.write("Task R63-T027 Verification Report\n")
        f.write("=================================\n\n")
        f.write("Tool Versions:\n")
        for k, v in results_data["tool_versions"].items():
            f.write(f"  {k}: {v}\n")
        f.write("\nTest Suite Checks (Scratch Module):\n")
        f.write(f"  Test count executed: {test_count}\n")
        f.write(f"  All 14 cases passed against reference.\n")
        f.write("\nMicro-Example 1 (ASCII byte indexing):\n")
        f.write(f"  Input: '+--+'\n")
        f.write(f"  Expected Output: {expected_out1}\n")
        f.write(f"  Actual Output:   {out1}\n")
        f.write(f"  Result: MATCH\n")
        f.write("\nMicro-Example 2 (Unicode box-drawing pitfall):\n")
        f.write(f"  Input: '┌──┐'\n")
        f.write(f"  Expected Output: {expected_out2}\n")
        f.write(f"  Actual Output:   {out2}\n")
        f.write(f"  Result: MATCH\n")
        f.write("\nLearner Stub Status:\n")
        f.write("  exercises/practice/rectangles/rectangles.go remains unchanged and unsolved (panics as required).\n")
        f.write("\nPublished Guidance Status:\n")
        f.write("  exercises/practice/rectangles/.docs/instructions.append.md published and verified.\n")

    print("All checks completed successfully and evidence saved.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
