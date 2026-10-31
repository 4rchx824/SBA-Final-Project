# Lighting assessment

This folder contains the lighting assessment: lighting–lux relationships, operating-hour patterns, Floor 2 comparisons, comfort-evidence limitations and occupancy-related investigation. The supplied architecture/workload instructions are included with its original content in [`README_analytics.txt`](README_analytics.txt).

## Run order

1. Reuse `data-cleaning/outputs/clean/` and the regenerated tables in `data-cleaning/outputs/aggregated/` and reports in `data-cleaning/outputs/quality/`. Run cleaning only if missing or intentionally refreshing the snapshot.
2. Run the original `baseline/lighting_peak_baseline.ipynb` if its outputs are missing or stale. Its calculations/source remain unchanged.
3. From the repository root run `python analytics/lighting/prepare_inputs.py` to freeze `outputs/zone_15min.csv` and `outputs/run_manifest.json`.
4. Run [`lighting_assessment.ipynb`](lighting_assessment.ipynb) top-to-bottom. It exports tables, selected figures, and [`lighting_findings.md`](lighting_findings.md).
5. Run [`lighting_scenarios.ipynb`](lighting_scenarios.ipynb) for conditional reductions, sensitivity, exclusion reasons and coincident coverage.
6. Read [`lighting_combined_findings.md`](lighting_combined_findings.md) for the executed assessment/scenario interpretation.

All 33 zones remain represented. March 6–31 calibration and April evaluation preserve 720/880 weekday operating-window intervals and 2,880 all-hours April intervals per zone. Timestamps use Bangkok local time. The adapter reconciles original baseline April daytime peaks and verifies unique joins; it never mixes legacy `outputs/*.csv` snapshots with regenerated `outputs/aggregated/*.csv` tables.

## Deliverables

- **Assessment notebook:** `lighting_assessment.ipynb`, with business questions, explanatory markdown, executed tables, interpretations and recommendations.
- **Zone opportunity table:** generated `outputs/lighting_opportunities.csv`, all 33 zones, observed lighting contribution, schedule exposure, coverage, activity status, investigation and limitations.
- **Selected charts:** generated `outputs/lighting_assessment_figures/`: Floor 2 demand profiles, schedule energy, power–lux relationships, lux distributions, and activity evidence. No before/after reduction plots or unnecessary cleaning-comparison charts are added.

Supporting tables include March/April coverage, schedule segment quantities/denominators, operating thresholds, activity-rule sensitivity and matched-power day/night lux comparisons. `config.json` records shared assumptions; `run_manifest.json` records paths, source hashes/revision and package versions. A changed source or shared interval table requires rerunning the adapter.

## Occupancy and comfort interpretation

The activity proxy requires independent plug-load evidence, not lux alone. A lighting-high/low-plug episode is a scheduling-audit candidate, not proven vacancy or waste. Flat, missing or overlapping states remain unknown. March fits are frozen before April. Persistence and threshold-shift sensitivity are reported, with no invented accuracy score.

Optional interpolation-run provenance comes from the small audit addition to the cleaning notebook. It does not alter the existing cleaning rules or cleaned numerical values. If absent, repair fractions remain unknown and repair-free flags are unavailable; complete cleaned intervals must never be called fully observed. With provenance present, repaired lighting/plug intervals are excluded from activity calibration/assessment. Reduction scenarios remain a separate analysis.

Ceiling ambient lux cannot establish task-plane adequacy. The illustrative 500 lux and the research paper's DGP scale do not determine activity eligibility or a safe dimming fraction. Compare lux within each zone, month and time-of-day context; only supported similar-power day/night bands provide a descriptive comparison. Validate actual attendance, task-plane light, essential circuits and occupant feedback before an intervention.

## Handoff contract

`outputs/zone_15min.csv` preserves baseline-compatible `total_kW`, `light_kW`, `lux` and coverage, and adds `plug_kW`, schema-presence flags, operating-hour/day-type context, strict `power_complete`/`paired_complete`, and repair fractions where provenance exists. “Complete” means 15 cleaned minutes; strict scenario arithmetic can use common support. Do not subtract components averaged over different partial-minute support.

The reduction-scenario analysis covers strict March trigger recalibration, April reduction scenarios, peak-shift checks, sensitivity to targets/caps and coincidence audits. The scenario implementation now exports conditional modeled reductions separately from this assessment; the combined report joins outputs on `floor`, `zone` and `scenario_id`.

## Verification

```bash
python -m unittest discover -s tests -v
```

## Folder naming

The supplied `README_analytics.txt` retains the original workload agreement (line endings normalised). Its proposed `lighting-analysis/` paths now map to `analytics/lighting/`. Use the commands and links in this README for the implemented layout.

## Added scenario analysis and validation

The new scenario notebook executes the design in the supplied workload document: March-only p95 calibration, strict complete-cleaned intervals and common-minute sensitivity, no-change checks, April peak recalculation and explicit exclusion reasons. Targets, caps and coverage gates are recorded in `config.json`. The original baseline implementation is unchanged.

Generated outputs include `scenario_summary.csv`, `scenario_sensitivity.csv`, `scenario_intervals.csv.gz`, `scenario_exclusion_reasons.csv`, `building_coincidence_audit.csv`, `coincident_scenario_impact.csv`, `combined_lighting_summary.csv` and `scenario_manifest.json`. These remain under ignored `outputs/`. The assessment also exports `lighting_matched_lux_working_days.csv`, a working-day-only comparison with the original March power-band edges held fixed.

```bash
python analytics/lighting/lighting_scenarios.py
```

See [REVISION_NOTES.md](REVISION_NOTES.md) for implementation comments, checks and a teammate summary.

## Study scope and limitations

This study identifies lighting-management opportunities and evaluates conditional reduction scenarios using existing telemetry. Comfort-preserving savings and actual building-wide impact cannot be verified because task-plane measurements, occupant feedback and independent main-meter data are unavailable.

The team has no building access or additional measurement records. The site pilot and independent main-meter checks are therefore proposed future validation, not unfinished coding requirements for this retrospective study. Zero modeled reduction under the tested rules does not prove zero physical savings potential.
