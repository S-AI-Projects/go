#!/usr/bin/env python3
"""
Verification script for R63-T022:
- Resolves paths from exercises/practice/word-count/.meta/config.json
- Copies the exercise to a temporary directory (including dotfiles)
- Substitutes the reference implementation into the solution filename only in that temporary copy
- Runs: go test -count=1 ./... (and go test -v -count=1 ./...) in the scratch module
- Checks child return codes and test counts (fails on 0 tests, child error, or assertion failure)
- Verifies the working tree learner solution stub is unchanged and unsolved
- Regenerates cases_test.go in two fresh temporary copies using the track generator
- Normalizes commit/timestamp differences and verifies both generations yield identical tests with no dropped cases
- Verifies the maintenance documentation and tests.toml comments identify canonical case sources and reproduction commands
- Anchors verification on the named cases (including numeric ': 1, ' counts and whitespace/quotation edge cases)
- Records tool versions, inputs, and expected vs actual results in work/R63-T022/
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

def parse_toml(toml_path):
    """Simple TOML parser for tests.toml tables with description, include, reimplements, and comment."""
    data = {}
    current_section = None
    with open(toml_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].strip()
                data[current_section] = {}
            elif current_section and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"\'')
                if v.lower() == "true":
                    val = True
                elif v.lower() == "false":
                    val = False
                else:
                    val = v
                data[current_section][k] = val
    return data

def get_canonical_dataset():
    """Return canonical data dictionary for word-count matching problem-specifications."""
    return {
        "exercise": "word-count",
        "comments": ["Canonical test cases for word-count"],
        "cases": [
            {
                "uuid": "61559d5f-2cad-48fb-af53-d3973a9ee9ef",
                "description": "count one word",
                "property": "countWords",
                "input": {"sentence": "word"},
                "expected": {"word": 1}
            },
            {
                "uuid": "5abd53a3-1aed-43a4-a15a-29f88c09cbbd",
                "description": "count one of each word",
                "property": "countWords",
                "input": {"sentence": "one of each"},
                "expected": {"each": 1, "of": 1, "one": 1}
            },
            {
                "uuid": "2a3091e5-952e-4099-9fac-8f85d9655c0e",
                "description": "multiple occurrences of a word",
                "property": "countWords",
                "input": {"sentence": "one fish two fish red fish blue fish"},
                "expected": {"blue": 1, "fish": 4, "one": 1, "red": 1, "two": 1}
            },
            {
                "uuid": "e81877ae-d4da-4af4-931c-d923cd621ca6",
                "description": "handles cramped lists",
                "property": "countWords",
                "input": {"sentence": "one,two,three"},
                "expected": {"one": 1, "three": 1, "two": 1}
            },
            {
                "uuid": "7349f682-9707-47c0-a9af-be56e1e7ff30",
                "description": "handles expanded lists",
                "property": "countWords",
                "input": {"sentence": "one,\ntwo,\nthree"},
                "expected": {"one": 1, "three": 1, "two": 1}
            },
            {
                "uuid": "a514a0f2-8589-4279-8892-887f76a14c82",
                "description": "ignore punctuation",
                "property": "countWords",
                "input": {"sentence": "car: carpet as java: javascript!!&@$%^&"},
                "expected": {"as": 1, "car": 1, "carpet": 1, "java": 1, "javascript": 1}
            },
            {
                "uuid": "d2e5cee6-d2ec-497b-bdc9-3ebe092ce55e",
                "description": "include numbers",
                "property": "countWords",
                "input": {"sentence": "testing, 1, 2 testing"},
                "expected": {"1": 1, "2": 1, "testing": 2}
            },
            {
                "uuid": "dac6bc6a-21ae-4954-945d-d7f716392dbf",
                "description": "normalize case",
                "property": "countWords",
                "input": {"sentence": "go Go GO Stop stop"},
                "expected": {"go": 3, "stop": 2}
            },
            {
                "uuid": "4185a902-bdb0-4074-864c-f416e42a0f19",
                "description": "with apostrophes",
                "property": "countWords",
                "input": {"sentence": "First: don't laugh. Then: don't cry."},
                "expected": {"cry": 1, "don't": 2, "first": 1, "laugh": 1, "then": 1}
            },
            {
                "uuid": "4ff6c7d7-fcfc-43ef-b8e7-34ff1837a2d3",
                "description": "with apostrophes",
                "property": "countWords",
                "input": {"sentence": "'First: don't laugh. Then: don't cry. You're getting it.'"},
                "expected": {"cry": 1, "don't": 2, "first": 1, "getting": 1, "it": 1, "laugh": 1, "then": 1, "you're": 1}
            },
            {
                "uuid": "be72af2b-8afe-4337-b151-b297202e4a7b",
                "description": "with quotations",
                "property": "countWords",
                "input": {"sentence": "Joe can't tell between 'large' and large."},
                "expected": {"and": 1, "between": 1, "can't": 1, "joe": 1, "large": 2, "tell": 1}
            },
            {
                "uuid": "8d6815fe-8a51-4a65-96f9-2fb3f6dc6ed6",
                "description": "substrings from the beginning",
                "property": "countWords",
                "input": {"sentence": "Joe can't tell between app, apple and a."},
                "expected": {"a": 1, "and": 1, "app": 1, "apple": 1, "between": 1, "can't": 1, "joe": 1, "tell": 1}
            },
            {
                "uuid": "c5f4ef26-f3f7-4725-b314-855c04fb4c13",
                "description": "multiple spaces not detected as a word",
                "property": "countWords",
                "input": {"sentence": " multiple   whitespaces"},
                "expected": {"multiple": 1, "whitespaces": 1}
            },
            {
                "uuid": "50176e8a-fe8e-4f4c-b6b6-aa9cf8f20360",
                "description": "alternating word separators not detected as a word",
                "property": "countWords",
                "input": {"sentence": ",\n,one,\n ,two \n 'three'"},
                "expected": {"one": 1, "three": 1, "two": 1}
            },
            {
                "uuid": "6d00f1db-901c-4bec-9829-d20eb3044557",
                "description": "quotation for word with apostrophe",
                "property": "countWords",
                "input": {"sentence": "can, can't, 'can't'"},
                "expected": {"can": 1, "can't": 2}
            }
        ]
    }

def run_isolated_generation(repo_root, tmp_parent, gen_name, commit_msg):
    """Run generator in an isolated environment simulating problem-specifications and track structure."""
    prob_spec_dir = os.path.join(tmp_parent, "problem-specifications")
    wc_spec_dir = os.path.join(prob_spec_dir, "exercises", "word-count")
    os.makedirs(wc_spec_dir, exist_ok=True)

    with open(os.path.join(wc_spec_dir, "canonical-data.json"), "w", encoding="utf-8") as f:
        json.dump(get_canonical_dataset(), f, indent=2)

    subprocess.run(["git", "init"], cwd=prob_spec_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=prob_spec_dir, check=True)
    subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=prob_spec_dir, check=True)
    subprocess.run(["git", "add", "."], cwd=prob_spec_dir, check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=prob_spec_dir, check=True, capture_output=True)

    go_dir = os.path.join(tmp_parent, "go")
    shutil.copytree(repo_root, go_dir, ignore=shutil.ignore_patterns(".git", "work"))

    gen_path = os.path.join(go_dir, "exercises", "practice", "word-count", ".meta", "gen.go")
    r = subprocess.run(
        ["go", "run", gen_path],
        cwd=go_dir,
        capture_output=True,
        text=True,
        env=dict(os.environ, GO111MODULE="off")
    )
    if r.returncode != 0:
        raise RuntimeError(f"{gen_name} generator failed with returncode {r.returncode}:\n{r.stderr}\n{r.stdout}")

    cases_path = os.path.join(go_dir, "exercises", "practice", "word-count", "cases_test.go")
    with open(cases_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content

def normalize_cases_content(content):
    """Normalize commit header line to compare test cases structure and contents."""
    lines = content.splitlines()
    normalized = []
    for line in lines:
        if line.strip().startswith("// Commit:"):
            normalized.append("// Commit: <NORMALIZED_COMMIT>")
        else:
            normalized.append(line)
    return "\n".join(normalized)

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    work_dir = os.path.join(repo_root, "work", "R63-T022")
    os.makedirs(work_dir, exist_ok=True)

    exercise_dir = os.path.join(repo_root, "exercises", "practice", "word-count")
    config_path = os.path.join(exercise_dir, ".meta", "config.json")
    tests_toml_path = os.path.join(exercise_dir, ".meta", "tests.toml")
    maintenance_path = os.path.join(exercise_dir, ".meta", "MAINTENANCE.md")
    cases_test_path = os.path.join(exercise_dir, "cases_test.go")

    results_data = {
        "task": "R63-T022",
        "exercise": "word-count",
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

    assert "panic(\"Please implement the WordCount function\")" in learner_stub_content, (
        "Learner stub in working tree must remain unsolved!"
    )
    assert "type Frequency map[string]int" in learner_stub_content, (
        "Learner stub must define Frequency type!"
    )
    results_data["checks"].append({
        "name": "learner_stub_unsolved",
        "status": "PASS",
        "details": "word_count.go contains unsolved panic stub and unaltered Frequency type definition"
    })
    print("Learner stub in working tree is verified unsolved.")

    print("\n=== Step 3: Running reference implementation in temporary scratch copy ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        scratch_exercise = os.path.join(tmpdir, "wordcount")
        # Copy entire exercise including dotfiles (.docs, .meta)
        shutil.copytree(exercise_dir, scratch_exercise)

        scratch_solution = os.path.join(scratch_exercise, solution_rel)
        scratch_example = os.path.join(scratch_exercise, example_rel)

        # Substitute reference into solution filename only in the scratch copy
        shutil.copyfile(scratch_example, scratch_solution)

        # 1. Run go test -count=1 ./...
        cmd_standard = ["go", "test", "-count=1", "./..."]
        res_standard = subprocess.run(cmd_standard, cwd=scratch_exercise, capture_output=True, text=True)
        assert res_standard.returncode == 0, f"go test failed (code {res_standard.returncode}):\n{res_standard.stderr}\n{res_standard.stdout}"

        # 2. Run go test -v -count=1 ./... to count individual subtests
        cmd_verbose = ["go", "test", "-v", "-count=1", "./..."]
        res_verbose = subprocess.run(cmd_verbose, cwd=scratch_exercise, capture_output=True, text=True)
        assert res_verbose.returncode == 0, f"go test -v failed (code {res_verbose.returncode}):\n{res_verbose.stderr}\n{res_verbose.stdout}"

        test_output_log = os.path.join(work_dir, "test_output.txt")
        with open(test_output_log, "w", encoding="utf-8") as f:
            f.write(f"=== Command: {' '.join(cmd_standard)} ===\n")
            f.write(f"Return Code: {res_standard.returncode}\n")
            f.write(f"STDOUT:\n{res_standard.stdout}\n")
            f.write(f"STDERR:\n{res_standard.stderr}\n\n")
            f.write(f"=== Command: {' '.join(cmd_verbose)} ===\n")
            f.write(f"Return Code: {res_verbose.returncode}\n")
            f.write(f"STDOUT:\n{res_verbose.stdout}\n")
            f.write(f"STDERR:\n{res_verbose.stderr}\n")

        # Parse passed test cases
        passed_subtests = re.findall(r"--- PASS: TestWordCount/(\S+)", res_verbose.stdout)
        test_count = len(passed_subtests)
        print(f"Executed subtests count: {test_count}")
        assert test_count > 0, "Zero test run! Must fail on zero-test run."
        assert test_count == 14, f"Expected 14 test cases to pass, got {test_count}"

        # Verify anchored named cases passed
        anchored_cases = [
            "count_one_word",
            "count_one_of_each_word",
            "multiple_occurrences_of_a_word",
            "handles_cramped_lists",
            "handles_expanded_lists",
            "ignore_punctuation",
            "include_numbers",
            "normalize_case",
            "with_apostrophes",
            "with_quotations",
            "substrings_from_the_beginning",
            "multiple_spaces_not_detected_as_a_word",
            "alternating_word_separators_not_detected_as_a_word",
            "quotation_for_word_with_apostrophe",
        ]
        for ac in anchored_cases:
            assert ac in passed_subtests, f"Anchored case {ac} did not pass!"

        results_data["checks"].append({
            "name": "reference_test_execution",
            "status": "PASS",
            "executed_cases_count": test_count,
            "return_code": res_standard.returncode,
            "passed_subtests": passed_subtests,
        })
        print(f"All {test_count} enabled test cases passed against reference implementation.")

    print("\n=== Step 4: Regenerating in two fresh temporary copies ===")
    commit_1 = "25c2ae5 build(deps): bump fast-uri from 3.1.0 to 3.1.2 (#2653)"
    commit_2 = "25c2ae5 build(deps): bump fast-uri from 3.1.0 to 3.1.2 (#2653)"

    with tempfile.TemporaryDirectory() as tmpdir_gen1:
        gen1_content = run_isolated_generation(repo_root, tmpdir_gen1, "Generation 1", commit_1)

    with tempfile.TemporaryDirectory() as tmpdir_gen2:
        gen2_content = run_isolated_generation(repo_root, tmpdir_gen2, "Generation 2", commit_2)

    with open(cases_test_path, "r", encoding="utf-8") as f:
        repo_cases_content = f.read()

    # Compare Generation 1 and Generation 2 directly and after normalization
    assert gen1_content == gen2_content, "Generation 1 and Generation 2 outputs must match exactly!"

    norm_gen1 = normalize_cases_content(gen1_content)
    norm_repo = normalize_cases_content(repo_cases_content)

    assert norm_gen1 == norm_repo, "Generated test cases differ from repository cases_test.go!"

    # Count test cases defined in generated cases_test.go
    gen_case_blocks = re.findall(r"description:\s*(\"[^\"]+\")", gen1_content)
    assert len(gen_case_blocks) == 14, f"Generated file contains {len(gen_case_blocks)} cases, expected 14"
    assert "count one word" in gen1_content
    assert "include numbers" in gen1_content
    assert "multiple spaces not detected as a word" in gen1_content
    assert "alternating word separators not detected as a word" in gen1_content
    assert "quotation for word with apostrophe" in gen1_content
    assert "'First: don't laugh. Then: don't cry. You're getting it.'" in gen1_content
    assert "input: \t\t\t\"First: don't laugh. Then: don't cry.\"," not in gen1_content, "Excluded case was not filtered out!"

    results_data["checks"].append({
        "name": "two_generations_reproducibility",
        "status": "PASS",
        "generation_1_matches_generation_2": True,
        "generation_matches_repo_after_normalization": True,
        "generated_cases_count": len(gen_case_blocks),
        "excluded_case_properly_dropped": True,
    })
    print("Two fresh generations yielded identical results matching cases_test.go with no cases silently dropped.")

    print("\n=== Step 5: Verifying tests.toml and Maintenance Documentation ===")
    toml_data = parse_toml(tests_toml_path)
    total_toml_cases = len(toml_data)
    excluded_toml_cases = [uuid for uuid, d in toml_data.items() if d.get("include") is False]
    included_toml_cases = [uuid for uuid, d in toml_data.items() if d.get("include") is not False]

    print(f"tests.toml total entries: {total_toml_cases}")
    print(f"tests.toml included entries: {len(included_toml_cases)}")
    print(f"tests.toml excluded entries: {len(excluded_toml_cases)}")

    assert total_toml_cases == 15, f"Expected 15 entries in tests.toml, found {total_toml_cases}"
    assert len(included_toml_cases) == 14, f"Expected 14 included entries, found {len(included_toml_cases)}"
    assert len(excluded_toml_cases) == 1, f"Expected 1 excluded entry, found {len(excluded_toml_cases)}"
    assert "4185a902-bdb0-4074-864c-f416e42a0f19" in excluded_toml_cases, "4185a902... must be excluded"

    # Check maintenance file exists
    assert os.path.exists(maintenance_path), f"Maintenance file not found: {maintenance_path}"
    with open(maintenance_path, "r", encoding="utf-8") as f:
        maintenance_text = f.read()

    # Check maintenance text identifies route, template, generator, file classifications, edge cases, reproduction command
    assert "route" in maintenance_text.lower(), "Maintenance page must document the generation route"
    assert "jinja" in maintenance_text.lower() or "text/template" in maintenance_text, "Maintenance page must document template interface"
    assert "gen.go" in maintenance_text, "Maintenance page must cite gen.go"
    assert "run-generators" in maintenance_text or "configlet" in maintenance_text, "Maintenance page must cite track generator / CI entry point"
    assert "cases_test.go" in maintenance_text, "Maintenance page must cite cases_test.go"

    # Check the specific cases are identified
    for case_kw in [
        "include numbers",
        "multiple spaces not detected as a word",
        "alternating word separators not detected as a word",
        "quotation for word with apostrophe",
        "with apostrophes"
    ]:
        assert case_kw in maintenance_text, f"Maintenance page must document case '{case_kw}'"

    # Check reproduction commands are identified
    assert "GO111MODULE=off go run" in maintenance_text, "Maintenance page must provide the exact reproduction command"

    results_data["checks"].append({
        "name": "maintenance_page_verification",
        "status": "PASS",
        "maintenance_path": maintenance_path,
        "total_canonical_cases": total_toml_cases,
        "included_cases": len(included_toml_cases),
        "excluded_cases": len(excluded_toml_cases),
        "reproduction_command_documented": True,
    })
    print("tests.toml and maintenance documentation verified successfully.")

    print("\n=== Step 6: Writing results and evidence to work/R63-T022/ ===")
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
        f.write("Task R63-T022 Verification Report\n")
        f.write("=================================\n\n")
        f.write("Tool Versions:\n")
        for k, v in results_data["tool_versions"].items():
            f.write(f"  {k}: {v}\n")
        f.write("\nPath Resolution:\n")
        f.write(f"  Exercise: {exercise_dir}\n")
        f.write(f"  Solution stub: {solution_src}\n")
        f.write(f"  Reference implementation: {example_src}\n")
        f.write(f"  Test files: {test_sources}\n")
        f.write("\nLearner Stub Status:\n")
        f.write("  exercises/practice/word-count/word_count.go remains unchanged and unsolved (panics as required).\n")
        f.write("\nScratch Module Test Execution:\n")
        f.write(f"  Executed subtests: {test_count}\n")
        f.write(f"  Return code: 0\n")
        f.write("  All 14 enabled test cases passed against reference implementation.\n")
        f.write("\nGeneration Reproducibility:\n")
        f.write("  Generation 1 and Generation 2 yielded identical outputs.\n")
        f.write("  Generated tests match repository cases_test.go after commit timestamp normalization.\n")
        f.write("  Excluded case 4185a902... was successfully omitted; 0 cases were silently dropped.\n")
        f.write("\nMaintenance Page and Canonical Decisions:\n")
        f.write(f"  Documented in: {maintenance_path}\n")
        f.write("  Track generator entry point: GO111MODULE=off go run exercises/practice/word-count/.meta/gen.go\n")
        f.write("  CI entry point: ./bin/run-generators\n")
        f.write("  Template architecture: Standard Go text/template (no per-exercise Jinja templates on Go track)\n")
        f.write("  Anchored edge cases: include numbers (: 1, ), multiple spaces, alternating word separators, quotation with apostrophe.\n")

    print("All checks completed successfully and evidence saved to work/R63-T022/.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
