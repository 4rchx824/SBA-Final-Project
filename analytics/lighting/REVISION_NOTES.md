# Lighting analysis revision notes

## Changes

- Added conditional lighting scenarios and an executed notebook, following the supplied workload design.
- Added strict complete-cleaned and common-minute policies, March-only calibration, no-change checks, peak recalculation, sensitivity and explicit exclusion reasons. Common-minute calculations prevent subtracting components averaged over different readings.
- Added a working-day-only lighting–lux sensitivity using the original March bands, plus simultaneous building/Floor 2 coverage checks.
- Added combined findings and the study-limitations statement to the findings, generator, README and both notebooks.
- Retained the original active README wording except necessary additions and corrections. Both supplied workload READMEs are unchanged.
- Removed the separate historical review, detailed fieldwork plan and duplicate standalone audit command. Coverage/target checks remain shared by the scenario runner.

## Verified results

Both notebooks executed successfully and 25 tests pass. Checked all 2,323,200 exported scenario intervals across 2,640 zone/scenario combinations, including arithmetic and missing-demand preservation. The original baseline remains unchanged.

The primary strict scenario (500 lux, cap 20%, period gate 80%) gives zero modeled reduction for 17 reportable zones; 16 zones are withheld. This does not prove zero physical savings potential.

## Study limitations

This study identifies lighting-management opportunities and evaluates conditional reduction scenarios using existing telemetry. Comfort-preserving savings and actual building-wide impact cannot be verified because task-plane measurements, occupant feedback and independent main-meter data are unavailable.

The team has no building access or additional measurement records. Site comfort testing and independent main-meter validation are future work outside this retrospective study, not unfinished coding requirements.

## Teammate summary

> Added the lighting scenario analysis, assessment sensitivity, validation checks and combined findings. Documented that the model's zero reduction is conditional on the tested rules, and that comfort-safe savings and real building-wide impact cannot be verified with the available data. Preserved the original workload READMEs and kept only the necessary implementation documentation.
