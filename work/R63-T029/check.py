import json
import subprocess
import sys
import shutil
import tempfile
import hashlib
from pathlib import Path

EXERCISE_ROOT = Path('exercises/practice/roman-numerals')
CONFIG_PATH = EXERCISE_ROOT / '.meta' / 'config.json'

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_paths(config, base_dir: Path):
    errors = []
    files = config.get('files', {})
    for kind, paths in files.items():
        for rel in paths:
            if '..' in Path(rel).parts:
                errors.append(f"{kind} entry '{rel}' contains parent traversal '..'")
                continue
            full = base_dir / rel
            try:
                full.relative_to(base_dir)
            except Exception:
                errors.append(f"{kind} entry '{rel}' resolves outside the exercise directory")
                continue
            if not full.is_file():
                errors.append(f"{kind} entry '{rel}' does not exist")
    return errors

def file_hash(path: Path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def run_checks():
    results = {
        'real_config': {},
        'broken_configs': [],
        'go_test': {},
        'tool_versions': {},
        'hashes': {}
    }
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
        cfg2['files']['test'] = test_list[1:]
    broken_examples.append(('missing_test', cfg2))
    # 3. empty test list
    cfg3 = json.loads(json.dumps(real_cfg))
    cfg3['files']['test'] = []
    broken_examples.append(('empty_test', cfg3))

    for name, cfg in broken_examples:
        errs = validate_paths(cfg, EXERCISE_ROOT)
        results['broken_configs'].append({'name': name, 'validation_errors': errs})

    # Run go test on temporary copy with reference substitution
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / EXERCISE_ROOT.name
        shutil.copytree(EXERCISE_ROOT, tmp_path)
        # Hash learner file before
        sol_rel = real_cfg['files']['solution'][0]
        learner_path = EXERCISE_ROOT / sol_rel
        pre_hash = file_hash(learner_path)
        # replace solution with example
        example_rel = real_cfg['files']['example'][0]
        shutil.copyfile(tmp_path / example_rel, tmp_path / sol_rel)
        # Run go test
        proc = subprocess.run(['go', 'test', '-count=1', './...'], cwd=tmp_path, capture_output=True, text=True)
        results['go_test']['returncode'] = proc.returncode
        results['go_test']['stdout'] = proc.stdout
        results['go_test']['stderr'] = proc.stderr
        results['go_test']['test_ok'] = any(line.startswith('ok ') for line in proc.stdout.splitlines())
        # Hash learner file after
        post_hash = file_hash(learner_path)
        results['hashes']['pre'] = pre_hash
        results['hashes']['post'] = post_hash
        results['hashes']['unchanged'] = (pre_hash == post_hash)

    # Tool versions
    try:
        results['tool_versions']['go'] = subprocess.check_output(['go', 'version'], text=True).strip()
    except Exception:
        results['tool_versions']['go'] = 'unavailable'
    try:
        results['tool_versions']['python'] = subprocess.check_output([sys.executable, '--version'], text=True).strip()
    except Exception:
        results['tool_versions']['python'] = 'unavailable'

    # Write result JSON
    out_path = Path('work/R63-T029') / 'result.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # Exit status: non‑zero on any failure
    if real_errors:
        sys.exit(1)
    if results['go_test']['returncode'] != 0 or not results['go_test']['test_ok']:
        sys.exit(1)
    if not results['hashes']['unchanged']:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    run_checks()
