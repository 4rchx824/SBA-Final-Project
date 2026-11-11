# Lighting analytics process record

## Scope and starting state

This work completes and organises the retrospective lighting analytics (BQ1). Presentation, dashboard development and recommendations are outside this task. The existing humidity baseline is retained and relocated, not expanded into forecasting or failure detection.

The branch began with uncommitted schedule-window changes, which were preserved. Existing CSVs used an older scenario schema; the documented coincident-impact export was missing. Several Markdown reports repeated stale results with different coverage definitions. Historical execution claims were therefore not treated as current verification.

## Cleanup and changes

1. Moved baseline code/notebooks to `baseline/` and organized their generated results under `outputs/baseline/{humidity_risk_baseline,lighting_peak_baseline}/`. Updated imports and notebook root discovery without changing baseline calculation formulas.
   The baseline assets have since moved to the repository-root `baseline/` directory; current workflows and paths use that location.
2. Kept lighting code, the active `config.json` and analytical notebooks in `analytics/lighting/`; redirected analytical exports to `outputs/lighting/`.
3. Moved source PDFs and both supplied workload specifications to `analytics/references/`. They remain historical references, not current run guides.
4. Consolidated analytics READMEs, revision notes and standalone findings into this record and the root README. Removed the unused historical scenario configuration and stale generated lighting outputs after regeneration.
5. Kept unit tests and a new full-output audit in `analytics/lighting/tests/`. Preserved raw data and the separate upstream cleaning workflow/review. Local historical backup material under `tmp/` is ignored and is not a pipeline dependency.
6. Added scenario-specific peak timestamps, peak-shift flags, lighting kW/share at the original policy peak, distinct April power/paired-lux exclusion reasons and explicitly labelled repair-free simultaneous coverage.
7. Rebuilt analytical notebooks with inline figures and structured CSV/JSON outputs; removed generated recommendation documents from the analytical workflow.

## Run order

Install `analytics/requirements.txt`, then run `python analytics/run_lighting.py` from the repository root. The runner executes and saves:

1. `../baseline/lighting_peak_baseline.ipynb`: descriptive baseline and Floor 2 context.
2. `lighting/prepare_inputs.ipynb`: cleaned-data adapter, baseline reconciliation, common-minute support, schema/calendar flags and input hashes.
3. `lighting/lighting_assessment.ipynb`: lighting contribution, schedule exposure, power/lux relationships, matched-power sensitivity, activity evidence and coverage.
4. `lighting/lighting_scenarios.ipynb`: March calibration, April scenarios, sensitivity, exclusion reasons, recomputed peaks, coincident coverage, combined export and full output audit.

Notebook paths above are relative to `analytics/` except the baseline notebook, which is relative to the repository root. Errors stop execution. Run unit tests with `python -m unittest discover -s analytics/lighting/tests -v`; rerun the export audit independently with `python analytics/lighting/tests/verify_lighting_outputs.py`.

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

Primary: strict complete-cleaned support; March demand P95 **and** zone-specific March lux P95 as joint investigation triggers; 80% period coverage and at least 96 March lux observations. P90/P97.5 lux are predefined sensitivities. Calibrate each zone/window/policy separately using March only. Require a nonconstant lux series with a positive cutoff; include measured zero and retain missing readings as missing. Use linear percentile interpolation and strict exceedance, so ties are not automatically flagged.

The percentile identifies unusually bright conditions relative to that zone's March telemetry. It is not a minimum illumination requirement or a proven daylight contribution. April evaluates the frozen method; no percentile is selected for producing the largest April reduction. This retrospective method specification is not prospective preregistration.

Eligible intervals also exceeding the March demand trigger receive illustrative electrical what-ifs of 0/5/10/20% of observed lighting power (20% primary). `scenario_total = total - cap * lighting`; AC and plugs remain unchanged. A cap is an assumed electrical response, not a calibrated fixture response or comfort-safe saving. Compare candidate hours and outcomes across caps, percentiles, coverage gates, policies and calendar windows.

All investigation lux cutoffs are calculated from each zone’s March observations. No manually selected absolute lux benchmark or proportional lux-response formula is applied. A recorded maximum cannot establish occupied task-plane requirements.
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
| `lighting_lux_observations.csv` | Measured April operating-window lux count, median and maximum by zone |
| `lighting_lux_calibration.csv` | March per-zone percentile cutoffs, counts, coverage and support flags |
| `combined_lighting_summary.csv`, `analysis_summary.json` | Joined evidence/scenarios and machine-readable outcomes |
| `assessment_manifest.json`, `scenario_manifest.json`, `verification.json` | Implementation provenance and audit receipt |
| `lighting_assessment_figures/`, `lighting_scenario_figures/` | Charts also embedded in executed notebooks |

Large shared/activity interval tables, compressed scenarios and PNGs are reproducible and ignored by Git. Compact CSV/JSON results remain reviewable. There is one active configuration; obsolete output schemas are removed.

## Interpretation limits

This is retrospective telemetry analysis. Ambient lux is not occupied task-plane illumination; plug activity is not attendance. Occupant feedback, calibrated fixture response and independent main-meter records are unavailable. Zero modeled reduction does not prove zero physical savings potential. The existing humidity notebook remains a descriptive baseline, outside this lighting execution/validation scope.

## Holiday update (5 November 2026)

The lighting adapter now reads and validates `outputs/data-cleaned/aggregated/day_calendar.csv` and records its hash. Holiday metadata remains separate from the demand-inferred `day_type`. The university-observance field is a supplied calendar assumption based partly on later-year evidence, not verified historical building attendance.

Weekday-only primary and extended results remain reproducible. Two additional holiday-excluded sensitivities use the same respective windows but exclude labelled university holidays consistently from calibration, coverage, energy and coincident peaks. No March calibration dates are removed. April excludes 8, 12, 15 and 16 April: 648 primary-window and 720 extended-window intervals per zone. All readings remain in the all-hours assessment; outside-hours energy is reclassified, not saved.

The original lighting baseline needs no formula change: the cleaning update adds calendar labels without changing readings. It intentionally retains the original weekday-only definition. Compare holiday-adjusted scenario peaks against their own observed timestamps rather than treating a changed calendar as a physical reduction.

The April special holiday is independently supported by the [Thai Ministry of Labour's 2019 announcement](https://www.mol.go.th/en/news/pol-gen-adul-promotes-safe-travels-during-songkran-for-thai-and-migrant-workers); substitute dates are listed in the [Ministry of Foreign Affairs 2019 calendar](https://image.mfa.go.th/mfa/0/mkKfL2iULZ/migrate_directory/information-20191008-174401-631551.pdf). These establish holiday dates, not individual building closure.


### Teammate review before merge

- Preparation: `prepare_inputs.py` joins and validates the calendar; the preparation notebook displays the holiday dates and interval counts. Existing demand-inferred closure labels are preserved.
- Calculations: `schedules.py` adds `primary_holiday_excluded` and `extended_holiday_excluded`; coverage validation uses the same schedule mask as the scenarios. The original weekday-only cases and baseline are retained.
- Results: compare the four cases in `outputs/lighting/scenario_schedule_comparison.csv`, `lighting_schedule_comparison.csv` and `coincident_scenario_impact.csv`. Zero modeled reduction persists; the holiday-excluded Floor 2 coverage becomes 100%.
- Verification: 31 unit tests and the full exported-output audit pass. `verification.json` records 8,025,600 checked intervals. Notebook markdown explains assumptions and interpretation limits.
- Review the supplied university-observance assumption before merging. A public-holiday label does not verify vacancy, comfort-safe savings or actual main-meter impact. These changes are proposed on `lighting-analytics-pbl2` for teammate review.

## March-calibrated lux method (12 November 2026)

Implemented the March-percentile investigation method described above and removed the manually selected absolute lux benchmark scenarios. Updated configuration, March calibration, April eligibility, conditional electrical arithmetic, exports, notebook explanations and audit checks together. The original descriptive baseline is unchanged.

`lighting_lux_calibration.csv` records per-zone/window/policy/gate/percentile cutoffs, March observation counts, coverage and support. `scenario_summary.csv` contains only primary March-P95 cases; the investigation cutoff is `lux_trigger_lux`, with no absolute-target field. The sensitivity table records `trigger_method`, `lux_quantile` and `response_model`. `reported_investigation_hours` is withheld when reporting gates fail; zero is distinct from unavailable evidence.

Interpretation for review: prioritize zones where candidate hours recur across reasonable percentile/calendar/support choices, then inspect their all-hours lighting/plug activity and demand patterns. This ranks investigation opportunities; it does not identify confirmed vacancy, prove over-lighting or validate comfort-preserving reductions. Site measurements and fixture response would still be needed for operational deployment.

The runner performs the full export audit once, after saving all notebooks; manual notebook execution must be followed by the standalone audit command.

### Verified April results for the March-percentile method

All four workflow notebooks executed; 40 unit tests pass. The full streamed audit passed for 4,815,360 intervals across 6,336 zone/scenario combinations, including independent reconstruction of March cutoffs and checks for the conditional electrical response. The original baseline source notebook and calculations are preserved.

Under the primary weekday 08:00–17:00 / strict / 80% gate / March-P95-lux case, 17 zones are reportable and 16 are withheld. Reportable candidates total **19.25 zone-hours** in April; overlapping zone-hours must not be interpreted as building elapsed hours. P90/P97.5 produce 43.5/8.25 zone-hours, respectively. These are sensitivity results, not alternatives selected to maximise savings.

Floor 2 Zone 2 has 4.75/3.25/2.25 candidate hours at P90/P95/P97.5, making it a more robust investigation priority. Zones 1 and 4 each have 0.25 hours at P95 and none at P97.5; avoid strong conclusions from those isolated intervals. Zone 3 has no joint demand/lux flags under these three cases, which does not establish no occupancy or no physical savings opportunity.

The primary 20% electrical what-if yields a positive zone-peak reduction only in Floor 7 Zone 1 (approximately 0.447 kW, 1.05% of its policy baseline peak). That positive peak outcome disappears at P97.5. It is sensitive to the investigation rule and is not verified comfort-preserving or building-wide savings. Floor 2 individual and aligned peaks remain unchanged even where conditional energy reductions are nonzero. Building-wide simultaneous coverage still does not support a reported impact.

Cutoffs use cleaned telemetry and may include interpolated readings under the complete-cleaned policy; complete coverage is not proof of raw observed-only data. Ambient sensors, calendar labels and plug activity do not establish task-plane comfort or attendance. Next analytical use: inspect Zone 2's flagged timestamps against demand/activity profiles; any operational control still requires independent fixture and comfort validation.
