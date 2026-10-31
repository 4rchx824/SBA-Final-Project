# Lighting assessment findings

This assessment addresses lighting contribution, schedules, power–lux patterns and occupancy-related evidence. Conditional reduction simulations and coincident peak impacts are handled in the reduction-scenario analysis.

## Floor 2 findings

| Zone | Lighting at daytime peak (%) | Outside-hours lighting (kWh) | Outside-hours energy share (%) | Activity mismatch (h) | Unknown activity (h) |
|---|---:|---:|---:|---:|---:|
| 1 | 15.17 | 139.66 | 9.04 | 0.00 | 46.00 |
| 2 | 5.65 | 43.12 | 9.88 | 0.00 | 86.50 |
| 3 | 52.32 | 208.30 | 52.63 | 5.75 | 107.25 |
| 4 | 14.13 | 46.37 | 12.08 | Unknown | 720.00 |

Zone 1 has 8.41 kW of lighting at its daytime demand peak, compared with 1.10 kW in Zone 3. Zone 3’s higher lighting share (52.32%) therefore does not imply a larger absolute peak opportunity.

Zone 3 uses 208.30 kWh outside assumed hours (52.63% of recorded lighting energy). Its stricter activity rule flags 5.75 hours. Prioritise a circuit-use and attendance audit; do not label all outside-hours energy as avoidable.

Matched-power lux estimates and support counts are exported by zone/month in `outputs/lighting_matched_lux_summary.csv`; band counts and residual power differences are inspectable in `outputs/lighting_matched_lux_bands.csv`.

Outside-hours use is measured over available lighting intervals, not estimated avoidable use. The schedule assumes weekdays 08:00–18:00; research/cleaning/security use may be legitimate. Inferred closures are energy-derived context, not attendance labels.

## Interpretation and recommendations

- Compare lighting at each zone’s own peak with actual scheduling evidence. Lighting share is an accounting contribution, not an achievable reduction.
- Floor 2 Zones 1 and 2 show no sustained lighting-high/low-plug mismatch under the primary rule. Retain their existing lighting until attendance and task needs justify changes.
- Floor 2 Zone 3 has a small mismatch signal. Validate its plug standby pattern and circulation/task function before calling it vacancy or waste.
- Floor 2 Zone 4 has almost constant plug load, so its activity assessment stays unknown. Obtain independent attendance evidence rather than lowering a threshold to force a result.
- Compare daytime/nighttime lux only at supported similar-power bands. Daylight, blinds and zone geometry confound the association; no lighting-off counterfactual is observed.
- Validate occupied task-plane lux and occupant feedback before a dimming trial. Ceiling ambient lux and the illustrative 500-lux reference do not establish comfort.

## Handoff to reduction scenarios

Use `outputs/zone_15min.csv`, `outputs/lighting_opportunities.csv`, `config.json` and `outputs/run_manifest.json`. The original baseline remains unchanged and the adapter reconciles its April daytime peaks for all 33 zones.

The shared table retains baseline-compatible values and adds `power_complete`/`paired_complete` for strict intervals. Complete after cleaning may include interpolation. Repair-free flags require the upstream interpolation audit and are not inferred from non-null counts. Missing comfort evidence must not be treated as automatic valid zero savings. Scenario percentages, peak shifts, sensitivity and building coincidence remain part of the reduction-scenario analysis.

## Evidence boundaries

The Thai thermal-comfort/glare study motivates local comfort surveys and separate thermal/visual assessment; it does not validate occupancy inference from lux. Its DGP scale cannot replace a lux threshold. The study’s seven Bangkok office buildings and window-facing occupants are not ground truth for Chamchuri 5.

Sources: [CU-BEMS](https://doi.org/10.1038/s41597-020-00582-3), [Chaloeytoy & Ichinose (2020)](https://digital.car.chula.ac.th/nakhara/vol19/iss1/6/), supplied `README_analytics.txt`, original lighting baseline and the generated source manifest.
