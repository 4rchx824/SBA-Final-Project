"""Fail closed unless the current files match a successful full lighting audit."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = 'outputs/lighting/verification.json'


def digest(path):
    h = hashlib.sha256()
    if path.suffix == '.ipynb':
        # Execution rewrites outputs/metadata; only executable source is a dependency.
        notebook = json.loads(path.read_text(encoding='utf-8'))
        code = [''.join(cell['source']) for cell in notebook['cells']
                if cell['cell_type'] == 'code']
        return hashlib.sha256(json.dumps(code).encode('utf-8')).hexdigest()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def snapshot(root=ROOT):
    """Cover upstream dependencies, implementation, and the complete result bundle."""
    manifest = json.loads((root / 'outputs/lighting/run_manifest.json').read_text())
    paths = {root / p for p in manifest['sources']}
    paths.update(p for p in (root / 'outputs/lighting').rglob('*') if p.is_file())
    paths.update(p for p in (root / 'outputs/baseline').glob('lighting*') if p.is_file())
    paths.update((root / 'analytics').rglob('*.py'))
    paths.update((root / 'baseline').rglob('*.py'))
    for relative in ['baseline/lighting_peak_baseline.ipynb',
                     'analytics/lighting/prepare_inputs.ipynb',
                     'analytics/lighting/lighting_assessment.ipynb',
                     'analytics/lighting/lighting_scenarios.ipynb']:
        if (root / relative).exists():
            paths.add(root / relative)
    paths.update((root / 'analytics').rglob('*requirements.txt'))
    paths.add(root / 'tests/verify_lighting_outputs.py')
    paths.discard(root / RECEIPT)
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(paths)}


def check_freshness(root=ROOT):
    path = root / RECEIPT
    if not path.exists():
        raise ValueError('No audit receipt. Run python analytics/run_lighting.py.')
    receipt = json.loads(path.read_text())
    hashes = receipt.get('file_sha256')
    if receipt.get('status') != 'passed' or not hashes:
        raise ValueError('No hash-backed successful audit. Regenerate and audit lighting outputs.')
    for relative, expected in hashes.items():
        file = root / relative
        if not file.is_file() or digest(file) != expected:
            raise ValueError(f'Missing or changed: {relative}. Run python analytics/run_lighting.py.')
    current = snapshot(root)
    if current != hashes:
        raise ValueError('Result bundle or dependency set changed. Regenerate and audit lighting outputs.')
    return receipt


if __name__ == '__main__':
    try:
        check_freshness()
    except (ValueError, OSError, KeyError) as error:
        raise SystemExit(f'NOT VERIFIED: {error}')
    print('Verified: local source and result bytes match the successful full audit.')
