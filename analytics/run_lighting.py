"""Execute the complete lighting workflow and save reviewable notebooks."""
from pathlib import Path
import os
import json
import subprocess
import sys

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    'baseline/lighting_peak_baseline.ipynb',
    'analytics/lighting/prepare_inputs.ipynb',
    'analytics/lighting/lighting_assessment.ipynb',
    'analytics/lighting/lighting_scenarios.ipynb',
]


def main():
    output = ROOT / 'outputs/lighting'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'verification.json').write_text(json.dumps({'status': 'in_progress'})+'\n')
    os.environ.setdefault('MPLBACKEND', 'module://matplotlib_inline.backend_inline')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    for relative in NOTEBOOKS:
        path = ROOT / relative
        print(f'Executing {relative}', flush=True)
        notebook = nbformat.read(path, as_version=4)
        client = NotebookClient(notebook, timeout=1800, kernel_name='python3',
                                resources={'metadata': {'path': str(ROOT)}})
        client.execute()
        nbformat.write(notebook, path)
        print(f'Saved {relative}', flush=True)
    subprocess.run([sys.executable, str(ROOT / 'tests/verify_lighting_outputs.py')], check=True)
    print('All lighting notebooks executed and outputs audited; receipt: outputs/lighting/verification.json', flush=True)


if __name__ == '__main__':
    main()
