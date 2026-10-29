# SBA Final Project: Smart Building Analytics

IS4001 analysis of the CU-BEMS dataset from Chamchuri 5, an academic office building at Chulalongkorn University, Bangkok. The 14 raw CSVs cover Floors 1–7, July 2018–December 2019, at one-minute resolution: AC, lighting and plug power; indoor temperature, RH and ambient lux. Actual occupancy and task-plane illuminance are not supplied.

Dataset: [CU-BEMS, Scientific Data (2020)](https://doi.org/10.1038/s41597-020-00582-3).

## Setup

Use Python 3.11 or newer with compatible prebuilt packages; Python 3.15 is not required. Create a virtual environment and install the notebook dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r data-cleaning/requirements.txt
python -m ipykernel install --user --name sba --display-name "Python (SBA)"
```

On Windows activate with `.venv\Scripts\Activate.ps1`. Select **Python (SBA)** in your notebook editor.

## Required workflow

1. **Clean:** run [`data-cleaning/main.ipynb`](data-cleaning/main.ipynb) from `data-cleaning/` only if outputs are missing or intentionally refreshing. It exports 14 cleaned files, supporting tables and interpolation provenance.
2. **Baseline:** run the original [`baseline/lighting_peak_baseline.ipynb`](baseline/lighting_peak_baseline.ipynb) for Q1. Its source/calculations remain unchanged. It reports March demand p95, April zone peaks, lighting contribution and ambient-lux diagnostics. Use the separate humidity baseline for Q2.
3. **Shared assessment input:** run `python analytics/lighting/prepare_inputs.py`. This adapter reuses the baseline interval builder, adds calendar/schema/completeness fields and reconciles all 33 April daytime peaks with the saved baseline.
4. **Lighting assessment:** run [`analytics/lighting/lighting_assessment.ipynb`](analytics/lighting/lighting_assessment.ipynb). It delivers lighting–lux relationships, schedule patterns, Floor 2 comparisons, occupancy-related evidence, coverage limitations and a zone opportunity table.
5. **Reduction scenarios:** use the shared input and opportunity table for conditional reductions, recomputed peaks, sensitivity and building coincidence. These scenarios are separate future deliverables.

Do not skip cleaning or silently mix legacy `outputs/*.csv` snapshots with current `outputs/aggregated/*.csv` tables. The six existing cleaning tables remain tracked under `outputs/aggregated/` and `outputs/quality/`. Large cleaned files, the interpolation log and generated lighting-analysis outputs remain ignored; executed notebook results remain reviewable.

## Lighting interpretation

- The existing demand trigger is March weekday 08:00–18:00 zone demand p95 in **kW**. It is not a lux or occupancy threshold.
- Separate March lighting/plug operating states support exploratory activity assessment. Missing, flat or ambiguous states remain unknown. Outside-hours use and low plug activity are not confirmed waste or vacancy.
- Ceiling ambient lux is a relative indicator. The proposal's illustrative **500 lux** cannot directly validate desk-level comfort, and the research paper's DGP scale is not a lux threshold.
- The opportunity table reports evidence and investigations, not approved reduction fractions or realised savings. Task-plane measurements and local occupant feedback remain necessary.

See the [supplied workload instructions](analytics/lighting/README_analytics.txt), [assessment run guide](analytics/lighting/README.md), [business findings](analytics/lighting/lighting_findings.md), and [cleaning review](data-cleaning/REVIEW.md).

## Checks

```bash
python -m unittest discover -s tests -v
```
