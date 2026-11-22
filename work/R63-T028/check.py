import json
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path

EXERCISE_ROOT = Path('exercises/practice/go-counting')
CONFIG_PATH = EXERCISE_ROOT / '.meta' / 'config.json'

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_paths(config, base_dir: Path):
    errors = []
    files = config.get('files', {})
    for kind, paths in files.items():
        for rel in paths:
            # reject parent traversal
            if '..' in Path(rel).parts:
                errors.append(f"{kind} entry '{rel}' contains parent traversal '..'")
                continue
            full = base_dir / rel
            # must be inside base_dir
            try:
                full.relative_to(base_dir)
            except Exception:
                errors.append(f"{kind} entry '{rel}' resolves outside the exercise directory")
                continue
            if not full.is_file():
                errors.append(f"{kind} entry '{rel}' does not exist")
    return errors

def run_checks():
    results = {
        'real_config': {},
        'broken_configs': [],
        'go_test': {},
        'tool_versions': {}
    }
    # Load real config and validate
    real_cfg = load_config(CONFIG_PATH)
    real_errors = validate_paths(real_cfg, EXERCISE_ROOT)
    results['real_config']['validation_errors'] = real_errors
    # Prepare broken configs
    broken_examples = []
    # 1. missing example file
    cfg1 = json.loads(json.dumps(real_cfg))
    cfg1['files'].pop('example', None)
    broken_examples.append(('missing_example', cfg1))
    # 2. missing test file
    cfg2 = json.loads(json.dumps(real_cfg))
    test_list = cfg2['files'].get('test', [])
    if test_list:
        cfg2['files']['test'] = test_list[1:]  # drop first test entry
    broken_examples.append(('missing_test', cfg2))
    # 3. path outside exercise
    cfg3 = json.loads(json.dumps(real_cfg))
    cfg3['files']['solution'] = ['../outside.go']
    broken_examples.append(('outside_path', cfg3))

    for name, cfg in broken_examples:
        errs = validate_paths(cfg, EXERCISE_ROOT)
        results['broken_configs'].append({
            'name': name,
            'validation_errors': errs
        })

    # Run go test on a temporary copy with reference implementation substituted
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / EXERCISE_ROOT.name
        shutil.copytree(EXERCISE_ROOT, tmp_path)
        # locate example and solution paths
        example_rel = real_cfg['files']['example'][0]
        solution_rel = real_cfg['files']['solution'][0]
        example_path = tmp_path / example_rel
        solution_path = tmp_path / solution_rel
        # replace solution with example content
        shutil.copyfile(example_path, solution_path)
        # run go test
        cmd = ['go', 'test', '-count=1', './...']
        proc = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)
        results['go_test']['returncode'] = proc.returncode
        results['go_test']['stdout'] = proc.stdout
        results['go_test']['stderr'] = proc.stderr
        # check that at least one test ran (look for a line starting with ok )
        results['go_test']['test_ok'] = any(line.startswith('ok ') for line in proc.stdout.splitlines())

    # Record tool versions
    try:
        go_ver = subprocess.check_output(['go', 'version'], text=True).strip()
    except Exception:
        go_ver = 'unavailable'
    try:
        py_ver = subprocess.check_output([sys.executable, '--version'], text=True).strip()
    except Exception:
        py_ver = 'unavailable'
    results['tool_versions'] = {'go': go_ver, 'python': py_ver}

    # Write summary JSON to work/R63-T028/result.json
    out_path = Path('work/R63-T028') / 'result.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    # Exit status: non‑zero if any real validation errors or test failures
    if real_errors:
        sys.exit(1)
    if results['go_test']['returncode'] != 0 or not results['go_test']['test_ok']:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    run_checks()
