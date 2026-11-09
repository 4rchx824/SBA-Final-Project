# Smart Building Analytics

CU-BEMS analysis for Chamchuri 5, Bangkok: lighting demand, ambient-light patterns and conditional peak-reduction scenarios.

## Layout

- `analytics/lighting/`: analytical code/configuration and executed preparation, assessment and scenario notebooks.
- `baseline/`: descriptive lighting and humidity baseline code/notebooks, plus cached weather input.
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
2. **Baselines:** run the notebook for the question you are analysing: `baseline/lighting_peak_baseline.ipynb` (Q1) or `baseline/humidity_risk_baseline.ipynb` (Q2).
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

### Verify freshness after pulling or downloading results

After pulling the latest changes or downloading results, check freshness before using or sharing lighting results:

```powershell
python analytics/check_lighting_freshness.py
```

**If the check passes, the local results match the successful audit. If it fails, or you cannot run the check, rerun the complete workflow:**

1. Update your checkout to the latest changes for the branch you want to analyse.
2. Install the current dependencies: `python -m pip install -r analytics/requirements.txt`.
3. Run all cells in `data-cleaning/main.ipynb` to regenerate the cleaned data and supporting tables.
4. Run `python analytics/run_lighting.py`. This rebuilds the lighting baseline, inputs, assessment and scenarios, then runs the full audit.
5. Run `python analytics/check_lighting_freshness.py` again. Only use the results once the workflow and freshness check both pass. If either fails, resolve the reported error before using the outputs.

These steps cover the lighting workflow. For humidity analysis, also rerun `baseline/humidity_risk_baseline.ipynb`; the lighting freshness check does not validate humidity results.

The freshness check does not download updates, so a pass does not mean your checkout contains the latest remote changes.
It exits unsuccessfully if an audited source, implementation, or output is missing or changed,
including ignored interval files. A copied `verification.json` alone is not proof of freshness.
Older receipts without file hashes are rejected. Run `python analytics/run_lighting.py` to
regenerate results and perform the full audit. A run or audit invalidates the previous success
receipt before starting; only a successful audit writes the hashes for the current bundle.

For remote automation, use the same order: supply current cleaned inputs, run the workflow,
run the freshness check, then publish the complete result bundle and its receipt together.
Configure publishing jobs to stop on nonzero exit codes. A Git pull contains only the tracked
subset and may require regeneration. This check verifies consistency with the files present;
it does not fetch newer remote commits or prove cleaning outputs match changed raw data.
Rerun cleaning first when raw inputs or cleaning logic change. Do not run concurrent writers
against the same output folder. Remote CI/publishing enforcement must be configured separately.

## Interpretation

Weekdays 08:00–17:00 are used as an assumed office schedule, supported by published university office hours and observed demand patterns. An 08:00–18:00 sensitivity analysis assesses dependence on this assumption. Neither schedule represents measured occupancy. See the [schedule definitions and source caveat](analytics/PROCESS.md#schedule-definitions).

The original baseline retains 08:00–18:00; scheduling and activity investigation covers all 24 hours. Ambient lux is not task-plane illuminance; activity proxies are not attendance labels. Zero conditional reduction does not establish zero physical savings potential. Comfort-preserving savings and independent building-wide impact remain unverified.

The holiday calendar is included in the lighting inputs. Additional holiday-excluded sensitivities compare both office windows against the original weekday-only cases; see the [holiday update](analytics/PROCESS.md#holiday-update-5-november-2026). Holiday observance is an assumption, not measured attendance.
