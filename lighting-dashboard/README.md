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

Code/data checks cover all 192 scenario configurations, primary totals, floor/search filtering, missing results, zero-cap identity and provenance display. The dashboard has not been visually verified; the user will inspect it. No site was published. The unused `.openai/hosting.json` records the earlier cancelled hosting setup.
