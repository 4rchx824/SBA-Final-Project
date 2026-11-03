# Smart Building Analytics

CU-BEMS analysis for Chamchuri 5, Bangkok: lighting demand, ambient-light patterns and conditional peak-reduction scenarios.

## Layout

- `analytics/lighting/`: analytical code/configuration and executed preparation, assessment and scenario notebooks.
- `analytics/baseline/`: descriptive lighting and humidity baseline code/notebooks.
- `analytics/references/`: original proposal, research paper and workload specifications.
- `tests/`: unit tests and full exported-output audit.
- `outputs/lighting/` and `outputs/baseline/`: generated analytical CSVs, JSON receipts and charts.
- `data/` and `data-cleaning/`: raw inputs and the separate upstream cleaning workflow. Cleaning outputs stay with that workflow.

## Getting started

### Set up the environment

Use **Python 3.14 or 3.15** (check with `python --version`). The full workflow has been run on both; the cleaning notebook has also been run on Python 3.9. The requirements pick a compatible pandas automatically: pandas 3.0.6 or newer on Python 3.15, because the pandas 2.x line crashes when it parses dates on 3.15. Allow about 1 GB of free disk space for the virtual environment and another 1 GB for generated outputs.

From the repository root, create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat
```

Install the dependencies. `analytics/requirements.txt` includes the data-cleaning requirements, so this one file covers every notebook:

```bash
python -m pip install --upgrade pip
python -m pip install -r analytics/requirements.txt
```

Register the environment as a Jupyter kernel:

```bash
# macOS / Linux
.venv/bin/python -m ipykernel install --user --name sba-py315 --display-name "Python 3.15 (SBA)"

# Windows PowerShell or Command Prompt
.venv\Scripts\python.exe -m ipykernel install --user --name sba-py315 --display-name "Python 3.15 (SBA)"
```

Check that the kernel is registered:

```bash
jupyter kernelspec list
```

`sba-py315` should appear in the list. In VS Code or JupyterLab, select **Python 3.15 (SBA)** as the notebook kernel. If `python` is a shell alias that bypasses the virtual environment, call `.venv/bin/python` (macOS/Linux) or `.venv\Scripts\python.exe` (Windows) directly. `.venv/` is in `.gitignore`, so the environment is never committed.

### Run order

1. **Cleaning:** run `data-cleaning/main.ipynb` (about 2 minutes). It recreates the cleaned files in `data-cleaning/outputs/clean/` (~700 MB, not stored in Git) and the aggregated tables and quality reports. Every later step needs these. Execution options and troubleshooting are in [`data-cleaning/README.md`](data-cleaning/README.md).
2. **Baselines:** run the notebook for the question you are analysing: `analytics/baseline/lighting_peak_baseline.ipynb` (Q1) or `analytics/baseline/humidity_risk_baseline.ipynb` (Q2).
3. **Lighting analytics:** run the commands below. The runner includes the lighting baseline notebook.

## Run lighting analytics

```powershell
python -m pip install -r analytics/requirements.txt
python analytics/run_lighting.py
python -m unittest discover -s tests -v
```

The runner executes and saves the lighting baseline, preparation, assessment and scenario notebooks in order. It requires the 14 cleaned input files and current aggregate/quality tables from `data-cleaning/main.ipynb`. It does not rerun cleaning or fetch weather.

Read [the process record](analytics/PROCESS.md) for methods, changes, output definitions and verified results. Large intermediate tables and generated PNGs remain locally reproducible; compact CSV/JSON outputs and executed notebooks are available for branch review.

The retained humidity baseline is a separate workflow. It uses the Open-Meteo ERA5 cache under `outputs/weather/` and is not part of the lighting execution command.

## Interpretation

Weekdays 08:00–17:00 are used as an assumed office schedule, supported by published university office hours and observed demand patterns. An 08:00–18:00 sensitivity analysis assesses dependence on this assumption. Neither schedule represents measured occupancy. See the [schedule definitions and source caveat](analytics/PROCESS.md#schedule-definitions).

The original baseline retains 08:00–18:00; scheduling and activity investigation covers all 24 hours. Ambient lux is not task-plane illuminance; activity proxies are not attendance labels. Zero conditional reduction does not establish zero physical savings potential. Comfort-preserving savings and independent building-wide impact remain unverified.
