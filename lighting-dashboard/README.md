# Lighting dashboard

A local, standalone dashboard for the verified Chamchuri 5 lighting analysis.

Open `dist/index.html` yourself in a browser. It works without a server. The dashboard has readable chart labels, floor filters, zone profiles, conditional scenario comparisons and data-quality explanations. Use ordinary screenshots of the relevant section for slides. There is no capture mode or export toolbar.

The dashboard uses a verified historical snapshot, not live readings. Missing scenario results stay withheld. Hourly charts average available April 2019 readings, and individual zone peaks are never summed into a building peak.

To refresh the snapshot from the main SBA project root after rerunning and auditing the analytics:

```powershell
python lighting-dashboard/export_data.py
node lighting-dashboard/verify.mjs
```

The exporter refuses stale or unaudited source data. Refreshing the browser alone does not update the analytical snapshot.

Code/data checks cover all 192 scenario configurations, primary totals, floor/search filtering, missing results, zero-cap identity and provenance display. The updated overview, a floor-filtered view and the zone/scenario sections were visually inspected in Chrome. This was not an exhaustive responsive or accessibility review. No site was published. The unused `.openai/hosting.json` records the earlier cancelled hosting setup.

## Reading the dashboard

Overview and zone profiles use the primary weekday 08:00–17:00 case; Scenario lab controls affect that section only. The priority card follows the floor filter and highlights signals that persist at P90/P95/P97.5, showing the zone with the most flagged time at P97.5 (then P95 as a tie-break). This is a screening priority, not a savings ranking. A zone with missing evidence shows a withheld result, not zero opportunity.

Zone insights compare flagged hours across the three March lux cutoffs. Scenario explanations distinguish candidate periods, modeled energy reductions and monthly zone-peak reductions. A zero-cap case retains the candidate flags but makes no electrical reduction. These are investigation priorities and conditional what-ifs, not verified vacancy or comfort-safe savings.

The outside-hours KPI uses the weekday clock schedule including holidays; the floor chart separately groups inferred closures under other hours. Both use recorded-period energy and should not be read as measured waste. The audit badge refers to the saved snapshot at export, not a fresh audit of local raw inputs.

## Quick review checks

- Select Floor 2: the priority card should highlight Zone 2, with 3.25 flagged hours at P95 and 2.25 at P97.5.
- Select Floor 1: flagged time should be withheld, with a missing-evidence explanation.
- Open Floor 2 Zone 2: compare 4.75 / 3.25 / 2.25 hours at P90 / P95 / P97.5.
- Set the reduction assumption to 0%: candidate flags remain, while modeled reductions become zero.
- Change Scenario lab controls: its results and explanation update; the overview remains the labelled primary case.
