# Smart Building Analytics

CU-BEMS analysis for Chamchuri 5, Bangkok: lighting demand, ambient-light patterns and conditional peak-reduction scenarios.

## Layout

- `analytics/lighting/`: analytical code/configuration and executed preparation, assessment and scenario notebooks.
- `analytics/baseline/`: descriptive lighting and humidity baseline code/notebooks.
- `analytics/references/`: original proposal, research paper and workload specifications.
- `tests/`: unit tests and full exported-output audit.
- `outputs/lighting/` and `outputs/baseline/`: generated analytical CSVs, JSON receipts and charts.
- `data/` and `data-cleaning/`: raw inputs and the separate upstream cleaning workflow. Cleaning outputs stay with that workflow.

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
