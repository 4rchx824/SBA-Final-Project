# Cleaning review for lighting analytics

The pipeline is suitable for retrospective descriptive and operating-pattern analysis, with limitations below. Preserve original raw files and the removal audit. Cleaning is not proof that occupancy, comfort or achievable savings can be inferred.

| Component | Review | Action |
|---|---|---|
| Timestamp parsing | Explicit day-first parsing for 2019 Floor 7 is justified; complete minute grids expose outages | Retain; validate unique, ordered timestamps |
| Truncated Floor 6 file | Dropping junk and retaining the missing tail as blank avoids invented observations | Retain; report coverage |
| Power spikes | Extreme, brief readings compared with local context plausibly identify logger bursts | Retain heuristic with audit; real short events may still be removed; no maintenance confirmation |
| Temperature floor | 15 °C isolates the documented biased sensor but is contextual, not a physical impossibility boundary | Retain documented screening; exclude F5 Z1 from comfort inference; corrected overstrong notebook wording |
| Short interpolation | Useful for descriptive aggregates but can smooth switching and use future readings | Export per-column repaired runs; exclude repairs from operating calibration and compare April with/without repairs |
| Long gaps | Leaving them blank preserves uncertainty | Retain; never map missingness to inactivity |
| Lux | Low ceiling readings cannot establish desk illumination | Keep values; use relative changes; no forced rescaling to 500 lux |
| Constant standby | Constant low power can be legitimate operation | Retain; a flat meter has no supported two-state calibration |
| Closure labels | Energy-derived labels are hypotheses, not confirmed university closures | Context only; do not validate energy-derived occupancy with them |
| Aggregation | 80% post-cleaning coverage is useful but includes interpolated data | Retain coverage and separate per-measure interpolation fraction in assessment adapter |
| Output paths | Aggregated tables use `outputs/aggregated/`; quality reports use `outputs/quality/` | Document canonical paths and avoid silent fallbacks |

The spike detector's centered rolling window, global quantile and interpolation use information from later timestamps. This is a retrospective cleaning pipeline, not a leakage-free real-time deployment evaluation. March-only operating calibration prevents direct April threshold fitting, but does not turn the historical cleaning into an online algorithm.

Full cleaning notebook validation checks timeline completeness, duplicates, plausibility, residual spikes, short interior gaps and retention of energy-derived low-activity days. Data-quality flags and removal/interpolation audits remain necessary when investigating individual events.

## Verification on 29 October 2026

The complete cleaning notebook executed successfully (69 code cells; six built-in checks passed). All 444,484 repaired minute-values reconcile to the new interpolation-run export. Regenerated analytics match the legacy tables in shape, missingness, day labels, removed readings and quality flags. Compared with the prior exports, numeric differences are limited to rounding boundaries: 659 floor-energy entries differ by 0.001 kWh and seven hourly AC entries by 0.01 kW. No cleaning-rule change was introduced to obtain those differences. The execution environment was Python 3.9 with pandas 2.3.3 and Matplotlib 3.9.4; the project setup recommends a newer supported Python version.
