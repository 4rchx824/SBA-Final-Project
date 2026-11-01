"""Execute the complete lighting workflow and save reviewable notebooks."""
from pathlib import Path
import os

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    'analytics/baseline/lighting_peak_baseline.ipynb',
    'analytics/lighting/prepare_inputs.ipynb',
    'analytics/lighting/lighting_assessment.ipynb',
    'analytics/lighting/lighting_scenarios.ipynb',
]


def main():
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
    print('All lighting notebooks executed; audit receipt: outputs/lighting/verification.json', flush=True)


if __name__ == '__main__':
    main()
