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
| [`data-cleaning/`](data-cleaning/) | Data-cleaning notebook, its outputs (cleaned data, analytics tables, figures) and setup instructions |

More analysis folders will be added as each business question is developed.

## Getting started

Setup and run instructions, including the Python 3.15 environment and Jupyter kernel, are in [`data-cleaning/README.md`](data-cleaning/README.md).

The cleaned files in `data-cleaning/outputs/clean/` (~700 MB) are not stored in Git. Run `data-cleaning/main.ipynb` (about 2 minutes) to recreate them. The smaller analytics tables and all figures are included in the repo.
