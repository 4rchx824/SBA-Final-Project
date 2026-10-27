# SBA Final Project: Smart Building Analytics

An IS4001 group project that uses the **CU-BEMS smart building energy and indoor-environment dataset** to investigate building-performance problems and recommend measurable actions.

## Data

The [`data/`](data/) folder holds the original CU-BEMS files: 14 CSVs, one per floor per year (Floors 1–7, July 2018 to December 2019), at one reading per minute. They contain:

- **Power (kW):** air-conditioning (AC), lighting and plug loads
- **Indoor environment:** temperature, relative humidity and illuminance (lux)

Occupancy and outdoor weather are not included.

Dataset reference: [CU-BEMS, Scientific Data (2020)](https://doi.org/10.1038/s41597-020-00582-3).

## Project structure

| Folder | Contents |
|---|---|
| [`data/`](data/) | Original raw CSV files (not modified) |
| [`data-cleaning/`](data-cleaning/) | Data-cleaning notebook, its outputs (cleaned data, analytics tables, figures) and notebook run instructions |
| [`baseline/`](baseline/) | Baseline notebooks for the proposal's lighting peak-demand and humidity/air-conditioning questions |

More analysis folders will be added as each business question is developed.

## Getting started

### Set up the environment

The data-cleaning notebook requires **Python 3.15** (check with `python --version`) and **pandas 3.0.6 or newer**. The version is pinned in [`data-cleaning/requirements.txt`](data-cleaning/requirements.txt). The pandas 2.x line has no prebuilt package for Python 3.15, and a copy compiled from source crashes when it parses dates. Allow about 1 GB of free disk space for the virtual environment and another 1 GB for generated outputs.

From the repository root, create a virtual environment and install the dependencies:

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

Then install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r data-cleaning/requirements.txt
```

On Python 3.15, pip may have to compile pandas from source. That can take a few minutes, and on macOS it needs the Xcode Command Line Tools (`xcode-select --install`).

Register the environment as a Jupyter kernel:

```bash
# macOS / Linux
python -m ipykernel install --user --name sba-py315 --display-name "Python 3.15 (SBA)"

# Windows PowerShell or Command Prompt
.venv\Scripts\python.exe -m ipykernel install --user --name sba-py315 --display-name "Python 3.15 (SBA)"
```

Check that the kernel is registered:

```bash
jupyter kernelspec list
```

`sba-py315` should appear in the list. VS Code can use `.venv` for new terminals; for notebooks, select **Python 3.15 (SBA)** as the kernel. If `python` resolves to an alias rather than the virtual environment's interpreter, use `.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS/Linux. `.venv/` is already in `.gitignore`, so the environment is never committed.

### Run the notebooks

The cleaned files in `data-cleaning/outputs/clean/` (~700 MB) are not stored in Git. Run `data-cleaning/main.ipynb` (about 2 minutes) to recreate them. The smaller analytics tables and all figures are included in the repo.

Run the cleaning notebook before either baseline notebook; they require the generated cleaned CSVs. Baseline run instructions and data limitations are in [`baseline/README.md`](baseline/README.md).

For detailed notebook execution options and paths, see [`data-cleaning/README.md`](data-cleaning/README.md).
