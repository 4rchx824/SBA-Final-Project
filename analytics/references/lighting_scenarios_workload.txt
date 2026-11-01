# BQ1: Lighting Comfort and Peak-Demand Analysis

## Purpose and scope

**How much can peak electricity demand be reduced in each zone without compromising lighting comfort?**

This README translates the lighting section of **SBA Proposal_IS4001_Group 2.pdf**, pages 2–9, into an analysis architecture grounded in the existing repository. Cleaning and the descriptive baseline are **completed upstream work**. The remaining work is lighting assessment, conditional reduction scenarios, and interpretation.

**Primary outcome:** zone peak-demand reduction in kW and %. **Secondary outcome:** lighting energy reduction in kWh. Scenario estimates do not establish that occupant comfort is preserved.

| Setting | Scope |
|---|---|
| Building | Chamchuri 5, CU-BEMS dataset |
| Zones | All 33 lighting zones; Floor 2 deep dive |
| Calibration | 6–31 March 2019 |
| Evaluation | April 2019 |
| Assumed operating hours | Weekdays 08:00–18:00 |
| Demand | Recorded AC + lighting + plug power within each zone |
| Scenario intervention | Reduce lighting only; retain recorded AC and plug demand |
| Lux assumption | 500 lux is illustrative, not a validated threshold for these sensors |
| No lux sensor | Demand analysis only; comfort-preserving savings remain undetermined |

Repository paths below are relative to its root. Existing filenames were checked against commit [`851207f480d9d2f7b62843452e5ebf1375b25d4f`](https://github.com/4rchx824/SBA-Final-Project/tree/851207f480d9d2f7b62843452e5ebf1375b25d4f). **NEW** identifies a proposed file, not an existing implementation.

## 1. Reuse the completed work

### Existing code and notebooks

| Exact filename | Existing responsibility | How the analysis uses it |
|---|---|---|
| `data-cleaning/main.ipynb` | Date alignment, invalid-value and spike treatment, short-gap interpolation, quality checks and exports | Reuse its cleaned outputs; do not redesign cleaning |
| `data-cleaning/README.md` | Cleaning assumptions and known limitations | Interpret gaps, repaired readings and sensor context |
| `data-cleaning/requirements.txt` | Package dependencies | Use the existing project environment |
| `baseline/_shared.py` | `clean_data_directory()` checks all 14 cleaned files; `read_clean_file()` selects columns and rejects duplicate timestamps | Reuse input validation |
| `baseline/lighting_peak_baseline.py` | Builds zone intervals, March P95 triggers, April peaks, lighting shares and lux sensitivity | Reuse calculations and preserve descriptive results |
| `baseline/lighting_peak_baseline.ipynb` | Calls the baseline implementation and displays results | Reference for comparison and Floor 2 findings |
| `baseline/README.md` | Baseline execution and limitations | Establish what is already supported |

The humidity notebooks and scripts belong to BQ2 and are not dependencies of this lighting analysis.

### Cleaned source files

Use these existing generated files under `data-cleaning/outputs/clean/`:

```text
2018Floor1.csv  2018Floor2.csv  2018Floor3.csv  2018Floor4.csv
2018Floor5.csv  2018Floor6.csv  2018Floor7.csv
2019Floor1.csv  2019Floor2.csv  2019Floor3.csv  2019Floor4.csv
2019Floor5.csv  2019Floor6.csv  2019Floor7.csv
```

The March/April Floor 2 analysis uses `data-cleaning/outputs/clean/2019Floor2.csv`. The existing baseline loader requires all 14 files. Cleaned files are generated locally and are not committed to GitHub; regenerate them only if they are missing.

Relevant source columns are `Date`, `z{zone}_Light(kW)`, `z{zone}_Plug(kW)`, `z{zone}_AC{n}(kW)` and `z{zone}_S1(lux)`. Use the actual available channels in each zone; not every zone has AC or a lux sensor.

### Existing supporting tables

At the reviewed commit, these files are committed directly under `data-cleaning/outputs/`:

| Filename | Analysis use | Limitation |
|---|---|---|
| `zone_hourly.csv` | Zone-level lighting, lux and activity patterns | Hourly averages cannot reconstruct 15-minute peaks; no exported coverage column |
| `floor_15min.csv` | Floor-level demand context and coverage | Not a substitute for zone-level intervals |
| `building_15min.csv` | Simultaneous floor reporting and building-demand coverage | Submeter aggregate, not an independent main meter |
| `daily_summary.csv` | Daily energy and inferred `day_type` | Closure labels are inferred, not verified occupancy |
| `data_quality.csv` | Sensor missingness and contextual warnings | Full-period missingness does not establish March/April coverage |
| `removed_readings.csv` | Audit removed values and reasons | Does not enumerate all interpolated missing readings |

**Path distinction:** the current `data-cleaning/main.ipynb` writes those six filenames to `data-cleaning/outputs/analytics/`, although the committed snapshots sit in `data-cleaning/outputs/`. Select one consistent output set and record the location. Do not silently mix snapshots and regenerated files. This is a path check, not a new cleaning task.

### Existing baseline outputs

The baseline generates these exact filenames under `baseline/outputs/`:

```text
lighting_zone_april_baseline.csv
lighting_floor2_april_baseline.csv
lighting_lux_sensitivity.csv
lighting_zone_april_peaks.png
lighting_peak_and_lux_baseline.png
```

They are generated outputs, not committed files in the reviewed tree. `lighting_lux_sensitivity.csv` counts intervals above illustrative thresholds; it does not estimate savings. The baseline currently keeps the zone interval table in memory rather than exporting it.

## 2. Architecture: two analysis branches, one shared input

```mermaid
flowchart TD
    A["Completed: data-cleaning/main.ipynb"] --> B["data-cleaning/outputs/clean/ — cleaned CSVs"]
    A --> C["Supporting quality and calendar tables"]
    B --> D["Completed: baseline/lighting_peak_baseline.py"]
    D --> E["baseline/outputs/ — existing baseline tables"]
    B --> F["NEW: lighting-analysis/prepare_inputs.py"]
    C --> F
    F --> G["NEW: lighting-analysis/outputs/zone_15min.csv"]
    G --> H["NEW: lighting-analysis/lighting_assessment.ipynb"]
    G --> I["NEW: lighting-analysis/lighting_scenarios.py"]
    E --> H
    E --> I
    I --> J["NEW: lighting-analysis/lighting_scenarios.ipynb"]
    H --> K["Lighting evidence and opportunity assessment"]
    J --> L["Conditional peak and energy impacts"]
    K --> M["NEW: lighting-analysis/lighting_findings.md"]
    L --> M
```

`prepare_inputs.py` is a small analysis adapter, not another cleaning pipeline. It reuses `_build_zone_intervals()` from `baseline/lighting_peak_baseline.py`, with the baseline directory on the import path, and adds calendar metadata and explicit validity flags. Keep the original baseline files unchanged.

### Shared interval contract

The proposed `lighting-analysis/outputs/zone_15min.csv` has one row per `(Date, floor, zone)` with no duplicates. Keep all timestamps, including rows with missing values. `Date` is the interval start, interpreted consistently as Bangkok local time.

| Field | Meaning |
|---|---|
| `Date`, `floor`, `zone` | Join key |
| `total_kW`, `light_kW`, `lux` | Existing baseline interval measures |
| `total_coverage`, `light_coverage`, `lux_coverage` | Existing baseline coverage fractions, 0–1 |
| `has_lux_sensor` | Sensor exists in source schema; distinct from missing readings |
| `is_operating_hour` | Weekday interval starting between 08:00 and 17:45 |
| `day_type` | Unique date-level lookup from supporting tables; inferred activity label |
| `power_complete` | All 15 cleaned minutes have every recorded zone power channel |
| `paired_complete` | Complete power plus 15 valid cleaned lux readings |

The baseline accepts 12/15 readings. The proposal specifies complete intervals. Preserve baseline values for reproduction, but use `power_complete`/`paired_complete` to define a separate strict scenario analysis. On complete power intervals the lighting component and zone total share the same minute support. If permitting partial intervals as a sensitivity test, recompute their components over a common set of valid minutes before subtraction.

“Complete after cleaning” can include interpolation. Do not label it “fully observed.” An observed-only sensitivity check requires matching the raw readings and removal log to cleaned values; do not infer original observation status from cleaned non-null counts.

## 3. Branch A: lighting conditions and opportunities

**NEW notebook:** `lighting-analysis/lighting_assessment.ipynb`.

**Inputs:** the shared interval table, `data_quality.csv`, `daily_summary.csv`, `zone_hourly.csv`, and the existing baseline outputs.

### Questions

1. When does lighting materially contribute to zone demand?
2. How does lighting use differ during and outside the assumed operating hours?
3. Do daytime power–lux patterns suggest a daylight opportunity?
4. Which zones have sufficient measurement evidence for further investigation?

### Analysis

- Plot lighting and total-demand profiles by zone and hour, with a Floor 2 comparison.
- Plot lux distributions and lighting-power/lux relationships, segmented by time of day and month.
- Compare daytime and nighttime lux at similar lighting power. Treat any daylight interpretation as exploratory.
- Quantify lighting energy outside assumed operating hours and separate weekends and inferred closures.
- Audit March/April sensor coverage, missingness at peak intervals and sensor-context warnings.
- Rank zones for scheduling audits, measurement validation or possible dimming trials.

High lux while lights are on does not establish that lights can be switched off. Low plug load does not establish vacancy. Ceiling-mounted ambient sensors cannot determine desk-level adequacy or occupant comfort by themselves.

### Outputs

Proposed files under `lighting-analysis/outputs/`:

- `lighting_opportunities.csv`: zone, lighting contribution, schedule patterns, coverage, evidence strength, suggested investigation and limitations.
- `lighting_assessment_figures/`: demand profiles, schedule heatmaps, lux distributions and power–lux plots.

This branch identifies evidence and constraints. It should not claim a validated comfort-safe reduction fraction from the available telemetry.

## 4. Branch B: conditional reduction and peak impact

**NEW implementation:** `lighting-analysis/lighting_scenarios.py`.

**NEW notebook:** `lighting-analysis/lighting_scenarios.ipynb`.

**Inputs:** the shared interval table, existing March baseline triggers for reproduction, and a shared proposed `lighting-analysis/config.json`.

### Calibration and eligibility

1. Reproduce the existing March P95 trigger calculations.
2. For the strict scenario mode, recalculate March P95 using complete intervals and freeze it before evaluating April. Keep this result separate from the original 80%-coverage baseline.
3. Report March and April coverage against their full expected timelines. Start with a configurable 80% period-coverage gate as a proposed screening choice, then test stricter gates. This is separate from requiring 15/15 readings within an interval.
4. Mark April operating-hour intervals above the March trigger. Group consecutive qualifying intervals into events; a missing interval breaks an event.
5. Separate missing sensors, missing lux, insufficient calibration and no headroom under the chosen assumption.

### Scenario design

| Case | Purpose |
|---|---|
| No reduction | Reference case and calculation check |
| Illustrative lux-constrained reduction | Quantify sensitivity under explicit, unvalidated assumptions |
| Future validated intervention | Requires task-plane measurements, approved targets and measured fixture response |

Reuse the baseline's illustrative lux targets `[100, 150, 200, 300, 500]`. Proposed electrical-power reduction caps are `[0, 0.05, 0.10, 0.20]`. These are assumptions for sensitivity analysis, not approved lighting settings.

A possible illustrative response model is:

```text
Assumption: lux_after = lux_before × (1 − r)
r = min(cap, max(0, 1 − target / lux_before))
```

Apply it only when lux is positive, the interval is a peak interval, and all data gates pass. Here `r` is an assumed electrical-power reduction fraction, not a dimmer command. The model does not separate daylight from electric light and is not validated for comfort. Zero permitted reduction is a valid outcome; do not lower targets merely to manufacture savings.

For each valid interval:

```text
reduction_kW = r × light_kW
scenario_total_kW = total_kW − reduction_kW
```

Retain no-action demand at observed intervals where the control would be disabled, with a clear reason. Missing demand stays missing. A disabled action or unknown comfort condition must not be reported as proven zero savings potential.

### Recompute peaks fairly

Recompute the maximum across the entire common valid April evaluation series, including intervals where no action occurs. Reducing the original maximum may expose a different peak.

```text
peak_reduction_kW = max(baseline_total_kW) − max(scenario_total_kW)
peak_reduction_pct = 100 × peak_reduction_kW / max(baseline_total_kW)
lighting_energy_saved_kWh = sum(reduction_kW × 0.25)
```

Both maxima must use the same timestamps. Handle zero denominators. Report missing-period coverage alongside results; incomplete data support an observed-period peak, not an assured monthly maximum. The weekday office-hours peak is also distinct from a full-month, all-hours peak.

For Floor 2/building coincidence, sum aligned zone demand before taking a maximum. Never add separate zone maxima. If simultaneous coverage is poor, report an audit rather than a full-month building-peak saving. Rescheduling, if explored separately, must include destination loads and any rebound; shifting usage alone does not necessarily save energy.

### Outputs

Proposed files under `lighting-analysis/outputs/`:

- `scenario_intervals.csv`: timestamp, zone, scenario, baseline/scenario demand, reduction, eligibility status and reason.
- `scenario_summary.csv`: peaks, reduction in kW/%, energy savings over valid periods, coverage and assumptions.
- `scenario_sensitivity.csv`: results by target, power-reduction cap and coverage policy.
- `building_coincidence_audit.csv`: expected and simultaneous valid interval counts for each completeness definition.
- `lighting_scenario_figures/`: before/after profiles and sensitivity comparisons.

Keep assumptions and provenance in `lighting-analysis/config.json` and a generated `lighting-analysis/outputs/run_manifest.json` containing source revision, selected paths, settings and package versions.

## 5. Combine the findings

**NEW report:** `lighting-analysis/lighting_findings.md`.

Join branch outputs by `floor` and `zone`; scenario tables additionally use `scenario_id`. The final comparison should contain:

| Evidence | Reported fields |
|---|---|
| Baseline | Zone peak, timestamp, lighting at original peak and lighting share |
| Lighting conditions | Sensor presence, lux patterns, schedule findings and measurement limitations |
| Conditional impact | Recomputed peak, kW/%, valid-period kWh, target and cap |
| Reliability | Calibration/evaluation coverage, exclusions and scenario status |
| Action | Scheduling audit, measurement validation, conditional pilot or insufficient evidence |

A zone with high conditional savings but inadequate comfort evidence is a candidate for validation, not immediate dimming.

If a pilot is feasible, collect representative task-plane lux, occupancy, activity type, lighting settings/power and occupant feedback. Use matched or alternating control/intervention periods. The proposal's future KPIs include no increase in lighting deficits or complaints, at least 95% valid occupied task-plane lux coverage, and comparable peak-demand reductions. Restore normal lighting on a breach or sensor failure. These outcomes cannot be evaluated from the existing ceiling lux data alone.

## 6. Findings that must be reconciled, not assumed

| Proposal or existing result | What the repository review established | Reporting rule |
|---|---|---|
| Complete 15-minute means | Baseline accepts at least 12/15 readings | Label strict and baseline-compatible analyses separately |
| 14 zones pass scenario gates | Saved baseline reports 31/33 with April demand coverage ≥80%; scenario gates are not implemented there | Export exclusion reasons; do not force either count |
| Maximum 138 lux | Cleaning notebook reports minute-level maximum 138; saved baseline reports April operating-hour 15-minute maximum 86.4 | State period and aggregation; these are different statistics |
| 8/2,880 complete building intervals | Committed `building_15min.csv` has 24 non-null April totals out of 2,880 under its aggregation | Recompute definitions; neither count establishes a reliable full-month peak |
| No dimming at 500 lux | Consistent with the reported sensor range | This is a rule outcome, not proof of zero physical savings potential |

The repository review inspected code, saved notebook outputs, committed tables and relevant figures. It did not regenerate the full cleaned dataset or independently rerun every baseline calculation.

## 7. Execution and verification

1. Reuse existing cleaned files and baseline outputs. Regenerate upstream outputs only if absent or intentionally refreshing the analysis snapshot.
2. Agree on paths, timestamps, coverage policy and scenario settings in the proposed `lighting-analysis/config.json`.
3. Implement and run the proposed `lighting-analysis/prepare_inputs.py` once to export the shared interval table.
4. Run the lighting-assessment and scenario branches independently against that frozen input.
5. Integrate their outputs in `lighting-analysis/lighting_findings.md`.

Acceptance checks:

- All 33 zones remain visible, including demand-only zones.
- Keys are unique and calendar joins do not multiply rows.
- Expected weekday-window counts are 720 March and 880 April intervals per zone before exclusions; all-hours April has 2,880 intervals.
- A no-change scenario reproduces baseline values exactly on the same rows.
- No reduction exceeds lighting power and no scenario power becomes negative.
- Missing calibration or lux never becomes an automatic valid zero value.
- A synthetic peak-shift case verifies that the maximum is recomputed.
- Partial-interval sensitivity uses common minute support for lighting and total power.
- Scenario assumptions, coverage and unsupported claims are explicit in every final table.

## References and reviewed diagnostics

- **SBA Proposal_IS4001_Group 2.pdf**, pages 2–9: supplied separately, not in the reviewed repository tree.
- [Lighting baseline implementation](https://github.com/4rchx824/SBA-Final-Project/blob/851207f480d9d2f7b62843452e5ebf1375b25d4f/baseline/lighting_peak_baseline.py)
- [Lighting baseline notebook](https://github.com/4rchx824/SBA-Final-Project/blob/851207f480d9d2f7b62843452e5ebf1375b25d4f/baseline/lighting_peak_baseline.ipynb)
- [Shared baseline readers](https://github.com/4rchx824/SBA-Final-Project/blob/851207f480d9d2f7b62843452e5ebf1375b25d4f/baseline/_shared.py)
- [Cleaning notebook](https://github.com/4rchx824/SBA-Final-Project/blob/851207f480d9d2f7b62843452e5ebf1375b25d4f/data-cleaning/main.ipynb)
- [Committed cleaning outputs](https://github.com/4rchx824/SBA-Final-Project/tree/851207f480d9d2f7b62843452e5ebf1375b25d4f/data-cleaning/outputs)
- [CU-BEMS dataset paper](https://doi.org/10.1038/s41597-020-00582-3): ceiling-mounted sensors and measurement context.

Lighting-relevant figures reviewed under `data-cleaning/outputs/figures/`:

| Purpose | Exact filenames |
|---|---|
| Dates | `3_1_floor7_date_format.png` |
| Missingness | `3_2_missing_heatmap_before.png`, `6_1_missing_heatmap_after.png`, `9_2_missing_side_by_side.png` |
| Gaps | `3_3_gap_lengths_before.png`, `6_2_gap_lengths_after.png`, `9_3_gap_lengths_side_by_side.png` |
| Power anomalies | `3_4_spike_ratio_before.png`, `3_5_spike_closeups_before.png`, `6_3_spike_ratio_after.png`, `6_4_spike_closeups_after.png`, `9_4_spike_ratio_side_by_side.png`, `9_5_spike_closeups_side_by_side.png` |
| Lux distributions | `3_6_env_hist_before.png`, `6_5_env_hist_after.png` |
| Constant readings | `3_8_constant_runs.png` |
| Schedule context | `3_9_daily_activity.png`, `9_7_activity_side_by_side.png` |
