# Lighting analytics process record

## Scope and starting state

This work completes and organises the retrospective lighting analytics (BQ1). Presentation, dashboard development and recommendations are outside this task. The existing humidity baseline is retained and relocated, not expanded into forecasting or failure detection.

The branch began with uncommitted schedule-window changes, which were preserved. Existing CSVs used an older scenario schema; the documented coincident-impact export was missing. Several Markdown reports repeated stale results with different coverage definitions. Historical execution claims were therefore not treated as current verification.

## Cleanup and changes

1. Moved baseline code/notebooks to `analytics/baseline/` and its results to `outputs/baseline/`. Updated imports and notebook root discovery without changing baseline calculation formulas.
2. Kept lighting code, the active `config.json` and analytical notebooks in `analytics/lighting/`; redirected analytical exports to `outputs/lighting/`.
3. Moved source PDFs and both supplied workload specifications to `analytics/references/`. They remain historical references, not current run guides.
4. Consolidated analytics READMEs, revision notes and standalone findings into this record and the root README. Removed the unused historical scenario configuration and stale generated lighting outputs after regeneration.
5. Kept unit tests and a new full-output audit in `tests/`. Preserved raw data and the separate upstream cleaning workflow/review. Local historical backup material under `tmp/` is ignored and is not a pipeline dependency.
6. Added scenario-specific peak timestamps, peak-shift flags, lighting kW/share at the original policy peak, distinct April power/paired-lux exclusion reasons and explicitly labelled repair-free simultaneous coverage.
7. Rebuilt analytical notebooks with inline figures and structured CSV/JSON outputs; removed generated recommendation documents from the analytical workflow.

## Run order

Install `analytics/requirements.txt`, then run `python analytics/run_lighting.py` from the repository root. The runner executes and saves:

1. `baseline/lighting_peak_baseline.ipynb`: descriptive baseline and Floor 2 context.
2. `lighting/prepare_inputs.ipynb`: cleaned-data adapter, baseline reconciliation, common-minute support, schema/calendar flags and input hashes.
3. `lighting/lighting_assessment.ipynb`: lighting contribution, schedule exposure, power/lux relationships, matched-power sensitivity, activity evidence and coverage.
4. `lighting/lighting_scenarios.ipynb`: March calibration, April scenarios, sensitivity, exclusion reasons, recomputed peaks, coincident coverage, combined export and full output audit.

Notebook paths above are relative to `analytics/`. Errors stop execution. Run unit tests with `python -m unittest discover -s tests -v`; rerun the export audit independently with `python tests/verify_lighting_outputs.py`.

## Data preparation

- Reuse 14 cleaned CU-BEMS floor/year files. Retain March 6-April 30, 2019 for 33 zones: 177,408 zone intervals. No raw-data recleaning occurs here.
- Use Bangkok local timestamps at 15-minute interval starts. March calibrates; April evaluates. Original April baseline zone peaks and March p95 triggers must reproduce.
- Preserve original baseline averages requiring at least 12/15 cleaned minutes. Add strict 15/15 power and paired-power/lux completeness flags.
- For partial support, calculate total, lighting and lux on shared valid minutes. Do not subtract components averaged over different observations.
- Separate sensor absence, missing readings and measured zero. Missing power stays missing; missing lux disables action without deleting valid demand. Withheld results remain missing.
- Use the upstream interpolation log for repair-free coverage and activity exclusions when supplied. Complete cleaned intervals can contain interpolation; absent provenance cannot establish repair-free status.
- Hash source data, configuration and adapter dependencies. Changes invalidate the shared table and require preparation again.

## Schedule definitions

| Analysis purpose | Window |
|---|---|
| Main office-hours assessment | Weekdays 08:00–17:00 |
| Comparison with the original baseline and schedule sensitivity | Weekdays 08:00–18:00 |
| Scheduling and occupancy-related investigation | All 24 hours, separating office hours, evenings, weekends and inferred closures |

Weekdays 08:00–17:00 are used as an assumed office schedule, supported by published university office hours and observed demand patterns. An 08:00–18:00 sensitivity analysis assesses dependence on this assumption. Neither schedule represents measured occupancy.

The [published Faculty of Engineering office hours](https://www.eng.chula.ac.th/en/about/contact) provide contextual support, not confirmation of Chamchuri 5's historical 2019 schedule. Inferred closures are analytical labels, not verified public holidays.

| Definition | March intervals/zone | April intervals/zone |
|---|---:|---:|
| Primary weekdays 08:00-17:00 | 648 | 792 |
| Extended sensitivity 08:00-18:00 | 720 | 880 |
| Original baseline 08:00-18:00 | 720 | 880 |

The branch's existing primary assumption is preserved and the proposal's longer window is explicitly compared. Each scenario window recalibrates March independently. Original-baseline columns remain distinct from scenario-specific peaks.

Weekday 17:00-18:00 is transition time, not measured vacancy. Outside-primary-hours energy includes transition energy; do not add it twice. The stacked chart uses disjoint categories with inferred closures/weekends taking precedence. Schedule changes reclassify observed energy; they do not create savings.

## Assessment methods

- Report lighting kW/share at each zone's original demand peak. Never sum individual zone maxima into a building peak.
- Report lighting energy, valid/expected intervals and mean demand by schedule segment. Outside-hours use is not automatically waste.
- Compare within-zone lighting/lux Spearman correlations and March/April day/night distributions.
- Freeze March power quantile bands for matched day/night lux comparisons. Require eight observations in both periods within each month/band. Repeat on inferred working days with the same bands.
- Fit independent lighting/plug states in March: 80% coverage, 96 valid observations, at least 10% in each cluster, two pooled-standard-deviation separation and a 0.02 kW deadband. Unsupported or ambiguous states remain unknown.
- Flag high lighting with low plug activity after 60 trailing minutes; missing/repaired readings break persistence when provenance exists. Test 30/60/90 minutes and ±10% boundary shifts. This is not an occupancy classifier.

## Conditional scenario methods

Primary: strict complete-cleaned support, March demand p95, 500 lux, 20% cap and 80% period coverage gate. The full grid covers two schedules, two support policies, two gates (80/95%), five targets (100/150/200/300/500 lux) and four caps (0/5/10/20%) for all 33 zones.

The illustrative response is `r = min(cap, max(0, 1 - target / ambient_lux))`; scenario demand is `total - r * lighting`. Only lighting changes. A valid high-demand trigger, sufficient evidence and positive ambient-light headroom are required. The response is not calibrated fixture behaviour.

Recompute both peaks over identical observed timestamps, including no-action intervals. Record peak times (first timestamp for ties), shifts, lighting contribution, conditional kW/%/kWh and calibration/evaluation coverage. Report distinct exclusion statuses. Zero-cap scenarios must reproduce baseline observations exactly.

Export all-hours, primary-window and extended-window simultaneous coverage separately, with complete-cleaned and repair-free policies labelled. Sum aligned zones before taking a maximum. Withhold coincident estimates below the coverage gate. These are submeter models, not independent main-meter validation.

## Output contract

Paths below are relative to `outputs/lighting/`.

| Files | Contents |
|---|---|
| `zone_15min.csv`, `run_manifest.json` | Shared intervals and source hashes |
| `lighting_opportunities.csv`, `lighting_coverage.csv` | Full-zone evidence and coverage |
| `lighting_schedule.csv`, `lighting_schedule_comparison.csv` | Disjoint segments and schedule sensitivity |
| `lighting_matched_lux_*.csv` | Frozen-band day/night comparisons |
| `lighting_activity_*.csv` | State calibration, sensitivity and interval evidence |
| `scenario_summary.csv` | One primary result per zone |
| `scenario_sensitivity.csv`, `scenario_schedule_comparison.csv` | Full grid and primary-rule schedule comparison |
| `scenario_intervals.csv.gz`, `scenario_exclusion_reasons.csv` | Exact modeled intervals and binding reason counts |
| `building_coincidence_audit.csv`, `coincident_scenario_impact.csv` | Simultaneous coverage and aligned peak comparisons |
| `lighting_target_validation.csv` | Baseline-compatible April operating-window lux/headroom by schedule |
| `combined_lighting_summary.csv`, `analysis_summary.json` | Joined evidence/scenarios and machine-readable outcomes |
| `assessment_manifest.json`, `scenario_manifest.json`, `verification.json` | Implementation provenance and audit receipt |
| `lighting_assessment_figures/`, `lighting_scenario_figures/` | Charts also embedded in executed notebooks |

Large shared/activity interval tables, compressed scenarios and PNGs are reproducible and ignored by Git. Compact CSV/JSON results remain reviewable. There is one active configuration; obsolete output schemas are removed.

## Verification and results

Verified on 1 November 2026:

- All four lighting workflow notebooks executed successfully: 19 code cells, zero cell errors, eight embedded charts. Notebook schemas were validated and the schedule/coincidence charts were visually inspected.
- All 30 unit tests passed, including synthetic positive reductions, peak shifts, missing demand, shared-minute arithmetic, frozen March calibration, repair-free coverage and schedule energy accounting.
- The streamed export audit passed for all **4,414,080 intervals across 5,280 zone/scenario combinations**. It checks arithmetic, missingness, caps, eligibility, unique keys, schedule windows, reconstructed peaks/energy, exclusion counts, reporting masks and source hashes. See `outputs/lighting/verification.json`.
- Both primary and extended windows have **17 reportable zones with zero modeled peak reduction and 16 withheld zones**. Withheld: nine without lux sensors, five with insufficient March calibration, one with insufficient April power coverage and one with insufficient April paired coverage. No tested grid setting produces a positive reported peak reduction.
- Maximum baseline-compatible April operating-window ambient lux is **86.40 lux** for both schedules, below all tested targets. This is explicitly a 15-minute operating-window measure, not an unlabelled raw-minute maximum.
- Building simultaneous power coverage is **0/792 primary operating intervals** and **0/880 extended operating intervals**; building impact is withheld. All-hours coverage is **24/2,880 complete-cleaned intervals**, or **8/2,880 repair-free intervals**. These definitions explain the previously conflicting figures.
- Floor 2 has **789/792 primary** and **877/880 extended** complete-cleaned operating intervals. Its aligned observed peak is **114.824 kW**, with zero conditional peak reduction under the primary rule. This is not a verified main-meter saving.

Source manifests preserve the execution-time revision plus file hashes; these identify the analytical inputs and implementation used for the saved results. Large intermediate files are available locally and regenerated by the runner. The humidity baseline was path-adjusted but not rerun or validated as a new BQ2 analysis.

## Interpretation limits

This is retrospective telemetry analysis. Ambient lux is not occupied task-plane illumination; plug activity is not attendance. Occupant feedback, calibrated fixture response and independent main-meter records are unavailable. Zero modeled reduction does not prove zero physical savings potential. The existing humidity notebook remains a descriptive baseline, outside this lighting execution/validation scope.
