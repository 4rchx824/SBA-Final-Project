# Analytics

Topic-specific analyses live in separate folders so the team can find code, notebooks and handoff documents together.

| Folder | Scope | Start here |
|---|---|---|
| [`lighting/`](lighting/) | BQ1 lighting assessment, occupancy-related evidence and conditional reduction scenarios | [Run guide](lighting/README.md), [assessment notebook](lighting/lighting_assessment.ipynb), [combined findings](lighting/lighting_combined_findings.md) |

Upstream cleaning remains in `data-cleaning/`; descriptive baselines remain in `baseline/`. Run cleaning → baseline → the topic adapter → the assessment notebook.

Generated outputs stay under each topic's `outputs/` and are ignored by Git. Executed notebooks and source/configuration files are shared in the repository.
