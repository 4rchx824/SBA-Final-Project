# BQ2: AC degradation and mould risk

**BQ2:** How can weather conditions, air-con performance and humidity levels be analysed to detect zones at risk of air-con degradation, mould growth, or both?

Scope: Floors 3-7, zones 1, 2, 4 and 5 (20 zones), CU-BEMS building data with Bangkok ERA5 weather.

## Run order

| Order | Notebook | What it does | Main output |
|---|---|---|---|
| 1 | `notebooks/bq2_humidity.ipynb` | High humidity exposure by zone and its reasons | `outputs/bq2-humidity/zone_mould_metrics.csv` |
| 2 | `notebooks/bq2_ac.ipynb` | AC screen: Jul-Aug 2018 vs 2019 (Track B) | `outputs/bq2-zone-screen/inspection_shortlist.csv` |
| 3 | `notebooks/bq2_risk_matrix.ipynb` | Combines both into the final findings and risk matrix | `outputs/bq2-risk-matrix/` |

`bq2_utils.ipynb` holds the shared functions; each notebook loads it automatically. `src/bq2/` holds the Track B screening code used by `bq2_ac.ipynb`. `bq2_ac.ipynb` takes several minutes to run.

## Charts used in the presentation

| Slide | Chart | Made by |
|---|---|---|
| 1 | `outputs/bq2-risk-matrix/weather_vs_ac_and_mould.png` | `bq2_risk_matrix.ipynb`, section 1 |
| 2 | `outputs/bq2-humidity/time_of_wetness.png` and `damp_drivers.png` | `bq2_humidity.ipynb`, sections 2-3 |
| 3 | `outputs/bq2-risk-matrix/wet_zones_ac_on_off.png` | `bq2_risk_matrix.ipynb`, section 2 |
| 4 | `outputs/bq2-risk-matrix/ac_drying_2018_vs_2019.png` | `bq2_risk_matrix.ipynb`, section 3 |
| 5 | `outputs/bq2-risk-matrix/risk_matrix.png` | `bq2_risk_matrix.ipynb`, section 4 |

## Inputs from the rest of the project

This folder must sit next to these project folders:

- `data-cleaning/outputs/` — cleaned zone and floor tables (`analytics/zone_hourly.csv`, `clean/`)
- `data/` — raw floor files (used by the Track B input checks)
- `baseline/` — `humidity_risk_baseline.py` and the cached weather file `data/bangkok_era5_hourly_2018-2019.csv`

Install packages with `pip install -r requirements.txt` (run from this folder).

## Limitations

Sensors measure room air, not surfaces, so surface humidity assumes a surface 2 °C cooler than the room. The 2018 vs 2019 comparison covers only two summers, and the sensors were removed for a firmware update in between. There are no maintenance, setpoint or mould-inspection records, so results are **inspection priorities**, not confirmed faults or confirmed mould.
