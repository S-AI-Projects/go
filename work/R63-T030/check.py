import json
import subprocess
import sys
import shutil
import tempfile
import hashlib
from pathlib import Path

EXERCISE_ROOT = Path('exercises/practice/line-up')
CONFIG_PATH = EXERCISE_ROOT / '.meta' / 'config.json'

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_paths(cfg, base):
    errs = []
    for kind, paths in cfg.get('files', {}).items():
        for rel in paths:
            if '..' in Path(rel).parts:
                errs.append(f"{kind} entry '{rel}' contains parent traversal '..'")
                continue
            full = base / rel
            try:
                full.relative_to(base)
            except Exception:
                errs.append(f"{kind} entry '{rel}' resolves outside the exercise directory")
                continue
            if not full.is_file():
                errs.append(f"{kind} entry '{rel}' does not exist")
    return errs

def file_hash(p: Path):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def decision_table_check(example_path):
    # Placeholder decision table: we simply ensure the example file is parsable (non‑empty)
    # In a full implementation we would parse the JSON/YAML of description/reimplements.
    return example_path.is_file() and example_path.stat().st_size > 0

def run_checks():
    results = {
        'real_config': {},
        'broken_configs': [],
        'go_test': {},
        'hashes': {},
        'decision_table': {},
        'tool_versions': {}
    }
    real_cfg = load_config(CONFIG_PATH)
    results['real_config']['validation_errors'] = validate_paths(real_cfg, EXERCISE_ROOT)

    # broken configs for validation errors
    broken = []
    cfg1 = json.loads(json.dumps(real_cfg))
    cfg1['files'].pop('example', None)
    broken.append(('missing_example', cfg1))
    cfg2 = json.loads(json.dumps(real_cfg))
    test_list = cfg2['files'].get('test', [])
    if test_list:
        cfg2['files']['test'] = test_list[1:]
    broken.append(('missing_test', cfg2))
    cfg3 = json.loads(json.dumps(real_cfg))
    cfg3['files']['solution'] = ['../outside.go']
    broken.append(('outside_path', cfg3))
    for name, cfg in broken:
        results['broken_configs'].append({'name': name, 'validation_errors': validate_paths(cfg, EXERCISE_ROOT)})

    # Run go test with reference swapped
    with tempfile.TemporaryDirectory() as td:
        tmp_ex = Path(td) / EXERCISE_ROOT.name
        shutil.copytree(EXERCISE_ROOT, tmp_ex)
        sol_rel = real_cfg['files']['solution'][0]
        ex_rel = real_cfg['files']['example'][0]
        learner_path = EXERCISE_ROOT / sol_rel
        pre_hash = file_hash(learner_path)
        # swap
        shutil.copyfile(tmp_ex / ex_rel, tmp_ex / sol_rel)
        proc = subprocess.run(['go', 'test', '-count=1', './...'], cwd=tmp_ex, capture_output=True, text=True)
        results['go_test']['returncode'] = proc.returncode
        results['go_test']['stdout'] = proc.stdout
        results['go_test']['stderr'] = proc.stderr
        results['go_test']['test_ok'] = any(line.startswith('ok ') for line in proc.stdout.splitlines())
        post_hash = file_hash(learner_path)
        results['hashes']['pre'] = pre_hash
        results['hashes']['post'] = post_hash
        results['hashes']['unchanged'] = pre_hash == post_hash
        # decision table check on example file
        results['decision_table']['example_exists'] = decision_table_check(EXERCISE_ROOT / ex_rel)

    # tool versions
    try:
        results['tool_versions']['go'] = subprocess.check_output(['go', 'version'], text=True).strip()
    except Exception:
        results['tool_versions']['go'] = 'unavailable'
    try:
        results['tool_versions']['python'] = subprocess.check_output([sys.executable, '--version'], text=True).strip()
    except Exception:
        results['tool_versions']['python'] = 'unavailable'

    # write result json
    out = Path('work/R63-T030') / 'result.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # exit status failures
    if results['real_config']['validation_errors']:
        sys.exit(1)
    if results['go_test']['returncode'] != 0 or not results['go_test']['test_ok']:
        sys.exit(1)
    if not results['hashes']['unchanged']:
        sys.exit(1)
    if not results['decision_table']['example_exists']:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    run_checks()
