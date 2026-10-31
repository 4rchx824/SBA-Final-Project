# Combined lighting assessment and scenario findings

## Study scope and limitations

This study identifies lighting-management opportunities and evaluates conditional reduction scenarios using existing telemetry. Comfort-preserving savings and actual building-wide impact cannot be verified because task-plane measurements, occupant feedback and independent main-meter data are unavailable.

Building access and additional measurement records are unavailable to the team. The site pilot and independent main-meter checks are therefore proposed future validation, not unfinished coding requirements for this retrospective study.

## Answer to the business question

The executed primary strict scenario (500 lux, 20% electrical-reduction cap, 80% period coverage gate) has 17 reportable zone results out of 33. Of those, 0 show a positive modeled operating-hour peak reduction. Other zones are withheld rather than interpreted as proven zero potential.

The maximum baseline-compatible April operating-hour ambient lux is 86.40, below every tested target (100, 150, 200, 300, 500 lux). The executed scenarios therefore test a rule with no observed ambient-light headroom, not a validated comfort-preserving intervention.

No observed reduction under these assumptions does not prove zero physical savings potential. Task-plane light, fixture response and occupant feedback are unavailable.

## Floor 2: assessment plus primary scenario

| Zone | Lighting at original peak (kW) | Outside-hours lighting (kWh) | Scenario status | Conditional peak reduction (kW) |
|---|---:|---:|---|---:|
| 1 | 8.415 | 139.66 | modeled result; comfort unvalidated | 0.000 |
| 2 | 2.650 | 43.12 | modeled result; comfort unvalidated | 0.000 |
| 3 | 1.097 | 208.30 | modeled result; comfort unvalidated | 0.000 |
| 4 | 1.850 | 46.37 | modeled result; comfort unvalidated | 0.000 |

Outside-hours lighting remains scheduling-audit exposure, not measured waste. Lighting/plug operating states are occupancy-related proxies, not attendance labels. The dimming scenario does not infer vacancy from these states.

## Building coincidence

| Scope | Simultaneous / expected intervals | Coverage (%) | Conditional peak change (kW) |
|---|---:|---:|---:|
| building | 0/880 | 0.00 | Withheld |
| Floor 2 | 877/880 | 99.66 | 0.000 |

The building result remains unavailable without simultaneous operating-hour measurements. Floor 2 is an aligned submeter model, not a validated main-meter saving. Separate zone maxima are never summed.

## What the sensitivity analysis covers

Executed combinations: strict complete-cleaned and common-minute partial policies; period coverage gates 80%/95%; targets 100/150/200/300/500 lux; caps 0/5/10/20%. All original March baseline triggers are reproduced before calculating policy-specific triggers. April never sets its own trigger. Both peak maxima use identical observed timestamps, including no-action intervals.

For the common-minute sensitivity, total, lighting and lux share the same valid minute support when paired measurements exist. Missing lux disables action and preserves observed power. Policy baselines differ and must not be pooled into one savings number. Complete cleaned intervals can include interpolation.

Zero modeled reduction is robust to the tested settings, but the number of reportable zones changes with completeness and coverage gates. Consult scenario_sensitivity.csv; missing estimates must not be pooled with zeros.

## Recommendations and future validation

- Audit the function and actual attendance of candidate circuits before changing schedules. Zone 3’s higher lighting share does not mean a large absolute peak opportunity.
- Validate representative occupied task-plane lighting, approved task requirements, dimmability and measured power/lux response. Collect occupant feedback with matched reference/intervention periods.
- Restore simultaneous zone reporting and obtain independent main-meter measurements before a building-wide impact claim.
- Present the zero model outcome alongside excluded/withheld cases. Do not lower targets simply to create savings.

## Audit trail

Inputs: `outputs/run_manifest.json`; implementation/settings: `outputs/scenario_manifest.json`; exact intervals: `outputs/scenario_intervals.csv.gz`; sensitivity: `outputs/scenario_sensitivity.csv`; exclusions: `outputs/scenario_exclusion_reasons.csv`; integrated table: `outputs/combined_lighting_summary.csv`. See `REVISION_NOTES.md` for changes and the README for study limitations.
