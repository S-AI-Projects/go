import os
import json
import subprocess
import shutil
import sys

def main():
    # Load config
    config_path = os.path.join('exercises', 'practice', 'split-second-stopwatch', '.meta', 'config.json')
    with open(config_path) as f:
        cfg = json.load(f)
    # Determine paths
    ex_dir = os.path.join('exercises', 'practice', 'split-second-stopwatch')
    tmp_dir = os.path.abspath('tmp_exercise')
    # Clean previous temp if exists
    if os.path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir, exist_ok=True)
    # Copy all files (including dotfiles) from exercise to temp
    for item in os.listdir(ex_dir):
        src = os.path.join(ex_dir, item)
        dst = os.path.join(tmp_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    # Also copy .meta directory
    meta_src = os.path.join(ex_dir, '.meta')
    meta_dst = os.path.join(tmp_dir, '.meta')
    # Replace reference implementation with alternative
    alt_path = os.path.abspath('alt_example.go')
    ref_path = os.path.join(tmp_dir, '.meta', 'example.go')
    shutil.copy2(alt_path, ref_path)
    # Run go test in temporary directory
    result = subprocess.run(['go', 'test', '-count=1', './...'], cwd=tmp_dir, capture_output=True, text=True)
    # Prepare report directory
    report_dir = os.path.abspath('')
    os.makedirs(report_dir, exist_ok=True)
    # Write outputs
    with open(os.path.join(report_dir, 'test_output.txt'), 'w') as f:
        f.write(result.stdout)
        f.write('\n')
        f.write(result.stderr)
    # Record tool versions
    go_version = subprocess.run(['go', 'version'], capture_output=True, text=True).stdout.strip()
    with open(os.path.join(report_dir, 'tool_versions.txt'), 'w') as f:
        f.write(f'go: {go_version}\n')
    # Determine pass/fail
    if result.returncode != 0:
        sys.exit(result.returncode)
    # Count passed tests (parsing go test output)
    passed = 0
    for line in result.stdout.splitlines():
        if line.strip().startswith('ok'):
            # example: ok   github.com/... 0.123s
            passed += 1
    # Save summary JSON
    summary = {
        'tests_executed': passed,
        'return_code': result.returncode,
    }
    with open(os.path.join(report_dir, 'results.json'), 'w') as f:
        json.dump(summary, f)

if __name__ == '__main__':
    main()
