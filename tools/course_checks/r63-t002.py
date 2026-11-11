#!/usr/bin/env python3
"""
Reusable focused regeneration check for relative-distance (R63-T002).
Verifies that the generator route from tests.toml and canonical-data.json
to cases_test.go is reproducible, deterministic, and preserves all canonical cases.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def normalize_generated_source(source_text: str) -> str:
    """Normalize generated comments such as commit hashes or timestamps."""
    lines = []
    for line in source_text.splitlines():
        if line.strip().startswith("// Commit:") or line.strip().startswith("// Generated at:"):
            lines.append("// Commit: <NORMALIZED>")
        else:
            lines.append(line)
    return "\n".join(lines).strip()

def run_generator_in_dir(target_repo: Path) -> str:
    """Run GO111MODULE=off go run .meta/gen.go in target_repo/exercises/practice/relative-distance"""
    exercise_dir = target_repo / "exercises" / "practice" / "relative-distance"
    gen_script = exercise_dir / ".meta" / "gen.go"
    if not gen_script.exists():
        raise FileNotFoundError(f"Generator script not found: {gen_script}")

    env = os.environ.copy()
    env["GO111MODULE"] = "off"

    res = subprocess.run(
        ["go", "run", str(gen_script)],
        cwd=exercise_dir,
        env=env,
        capture_output=True,
        text=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"Generator failed (exit {res.returncode}):\n{res.stderr}\n{res.stdout}")

    cases_file = exercise_dir / "cases_test.go"
    if not cases_file.exists():
        raise FileNotFoundError(f"Generated cases_test.go not found at {cases_file}")

    with open(cases_file, "r") as f:
        return f.read()

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    exercise_rel = Path("exercises") / "practice" / "relative-distance"
    print("=== [tools/course_checks/r63-t002.py] Running Regeneration Verification ===")

    # Step 1: Generate in Copy 1
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        dir1 = Path(tmp1) / "repo"
        dir2 = Path(tmp2) / "repo"

        # Copy repository trees (including gen, exercises, gotools)
        shutil.copytree(repo_root, dir1, symlinks=True, ignore=shutil.ignore_patterns(".git", "work"))
        shutil.copytree(repo_root, dir2, symlinks=True, ignore=shutil.ignore_patterns(".git", "work"))

        print("Executing Pass 1 generation...")
        gen1_raw = run_generator_in_dir(dir1)
        norm1 = normalize_generated_source(gen1_raw)

        print("Executing Pass 2 generation...")
        gen2_raw = run_generator_in_dir(dir2)
        norm2 = normalize_generated_source(gen2_raw)

        if norm1 != norm2:
            raise AssertionError("Indeterministic generation: pass 1 and pass 2 produced differing outputs!")

        print("✔ Two generations yield identical tests after timestamp/commit normalization.")

        # Step 2: Validate case count and expected cases
        cases = re.findall(r'description:\s*"([^"]+)"', norm1)
        print(f"✔ Found {len(cases)} generated cases in cases_test.go: {cases}")
        if len(cases) != 7:
            raise AssertionError(f"Expected 7 test cases, but found {len(cases)}!")

        expected_descriptions = [
            "Direct parent-child relation",
            "Sibling relationship",
            "Two degrees of separation, grandchild",
            "Unrelated individuals",
            "Complex graph, cousins",
            "Complex graph, no shortcut, far removed nephew",
            "Complex graph, some shortcuts, cross-down and cross-up, cousins several times removed, with unrelated family tree"
        ]

        for desc in expected_descriptions:
            if desc not in cases:
                raise AssertionError(f"Missing required case: '{desc}'")

        print("✔ All canonical cases are preserved without silent dropping.")
        print("✔ R63-T002 regeneration check PASSED.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Check failed: {e}", file=sys.stderr)
        sys.exit(1)
