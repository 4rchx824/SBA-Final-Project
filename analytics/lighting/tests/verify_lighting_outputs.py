"""Integration audit of regenerated lighting outputs; run after the notebooks."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'outputs/lighting'
sys.path.insert(0, str(ROOT / 'analytics'))
from check_lighting_freshness import snapshot


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify_outputs():
    # A failed audit must never leave an older success receipt in place.
    (OUTPUT / 'verification.json').write_text(json.dumps({'status': 'in_progress'})+'\n')
    before = snapshot()
    summary = pd.read_csv(OUTPUT / 'scenario_sensitivity.csv')
    keys = ['floor', 'zone', 'scenario_id']
    assert not summary.duplicated(keys).any(), 'Duplicate summary keys'
    expected = summary.set_index(keys)
    calendar = pd.read_csv(ROOT / 'outputs/data-cleaned/aggregated/day_calendar.csv')
    holidays = pd.to_datetime(calendar.loc[calendar.observed_by_university.eq(True), 'Date'])
    totals, reason_counts = {}, Counter()
    interval_count = 0
    for chunk in pd.read_csv(OUTPUT / 'scenario_intervals.csv.gz', chunksize=100_000):
        interval_count += len(chunk)
        assert chunk.baseline_total_kW.isna().equals(chunk.scenario_total_kW.isna())
        assert chunk.baseline_total_kW.isna().equals(chunk.reduction_kW.isna())
        assert np.allclose(chunk.baseline_total_kW - chunk.reduction_kW,
                           chunk.scenario_total_kW, equal_nan=True)
        assert not chunk.reduction_kW.lt(-1e-9).any()
        assert not chunk.scenario_total_kW.lt(-1e-9).any()
        assert not (chunk.reduction_kW > chunk.lighting_kW + 1e-9).fillna(False).any()
        no_action = chunk.eligibility_reason.ne('eligible') & chunk.baseline_total_kW.notna()
        assert chunk.loc[no_action, 'reduction_kW'].eq(0).all()
        for key, group in chunk.groupby(keys, sort=False):
            setting = expected.loc[key]
            assert group.schedule_id.eq(setting.schedule_id).all()
            assert not (group.reduction_kW > setting.reduction_cap * group.lighting_kW + 1e-9).fillna(False).any()
            eligible = group.eligibility_reason.eq('eligible')
            assert group.loc[eligible, 'ambient_lux'].gt(setting.target_lux).all()
            assert group.loc[eligible, 'baseline_total_kW'].gt(setting.march_p95_kW).all()
            formula = ((1 - setting.target_lux / group.loc[eligible, 'ambient_lux'])
                       .clip(0, setting.reduction_cap) * group.loc[eligible, 'lighting_kW'])
            assert np.allclose(group.loc[eligible, 'reduction_kW'], formula)
            if setting.reduction_cap == 0:
                assert np.allclose(group.baseline_total_kW, group.scenario_total_kW, equal_nan=True)
            record = totals.setdefault(key, dict(rows=0, valid=0, base=-np.inf, after=-np.inf,
                                                reduction=0., dates=set()))
            dates = set(group.Date)
            assert len(dates) == len(group) and not record['dates'].intersection(dates), 'Duplicate interval keys'
            record['dates'].update(dates)
            record['rows'] += len(group)
            record['valid'] += int(group.baseline_total_kW.notna().sum())
            if group.baseline_total_kW.notna().any():
                record['base'] = max(record['base'], group.baseline_total_kW.max())
                record['after'] = max(record['after'], group.scenario_total_kW.max())
            record['reduction'] += group.reduction_kW.sum()
            reason_counts.update({(*key, reason): int(n) for reason, n in group.eligibility_reason.value_counts().items()})
    assert set(totals) == set(expected.index), (
        f'Detailed scenario file and summary disagree: {len(totals)} vs '
        f'{len(expected)} combinations. Run python analytics/run_lighting.py.')
    for key, record in totals.items():
        row = expected.loc[key]
        assert record['rows'] == row.april_expected_intervals
        assert record['valid'] == row.april_valid_intervals
        base = record['base'] if record['valid'] else np.nan
        after = record['after'] if record['valid'] else np.nan
        energy = record['reduction'] / 4 if record['valid'] else np.nan
        assert np.allclose([base, after, base-after, energy],
                           [row.observed_baseline_peak_kW, row.observed_scenario_peak_kW,
                            row.paired_observed_peak_reduction_kW, row.paired_observed_energy_reduction_kWh], equal_nan=True)
        dates = pd.DatetimeIndex(sorted(record['dates']))
        if row.schedule_id.endswith('_holiday_excluded'):
            assert not dates.normalize().isin(holidays).any()
        start, end = map(int, row.operating_window.replace('\u2013', '-').replace(':00', '').split('-'))
        assert ((dates.month == 4) & (dates.year == 2019) & (dates.day_of_week < 5) &
                (dates.hour >= start) & (dates.hour < end)).all()
    reported = summary.status.eq('modeled result; comfort unvalidated')
    assert summary.reported_peak_reduction_kW.notna().equals(reported)
    assert np.allclose(summary.loc[reported, 'reported_peak_reduction_kW'],
                       summary.loc[reported, 'paired_observed_peak_reduction_kW'])
    reasons = pd.read_csv(OUTPUT / 'scenario_exclusion_reasons.csv')
    assert reason_counts == Counter({(r.floor, r.zone, r.scenario_id, r.reason): r.intervals
                                     for r in reasons.itertuples()})
    primary = pd.read_csv(OUTPUT / 'scenario_summary.csv')
    combined = pd.read_csv(OUTPUT / 'combined_lighting_summary.csv')
    assert len(primary) == len(combined) == 33
    assert not combined.duplicated(['floor', 'zone']).any()
    impacts = pd.read_csv(OUTPUT / 'coincident_scenario_impact.csv')
    assert len(impacts) == 2 * summary.schedule_id.nunique()
    scenario_manifest = json.loads((OUTPUT / 'scenario_manifest.json').read_text())
    gate = scenario_manifest['settings']['scenarios']['primary_period_coverage_gate']
    assert impacts.loc[impacts.coverage_pct < gate * 100, 'reported_peak_reduction_kW'].isna().all()
    manifest = json.loads((OUTPUT / 'run_manifest.json').read_text())
    for relative, expected_digest in manifest['sources'].items():
        assert digest(ROOT / relative) == expected_digest, f'Stale source: {relative}'
    assert digest(OUTPUT / 'zone_15min.csv') == manifest['output_sha256']
    assert digest(OUTPUT / 'run_manifest.json') == scenario_manifest['input_manifest_sha256']
    assert digest(ROOT / 'analytics/lighting/lighting_scenarios.py') == scenario_manifest['implementation_sha256']
    assert digest(ROOT / 'analytics/lighting/validation_audit.py') == scenario_manifest['audit_source_sha256']
    assessment_manifest = json.loads((OUTPUT / 'assessment_manifest.json').read_text())
    assert digest(ROOT / 'analytics/lighting/assessment.py') == assessment_manifest['analysis_source_sha256']
    result = dict(status='passed', intervals_checked=interval_count,
                  zone_scenario_combinations=len(summary), primary_zones=len(primary),
                  reportable_zones=int(reported.loc[summary.scenario_id.isin(primary.scenario_id)].sum()),
                  checks=['interval arithmetic', 'missing demand preservation', 'no-change identity',
                          'reduction caps and eligibility', 'unique interval keys', 'window denominators',
                          'recomputed peaks and energy', 'exclusion reconciliation', 'reporting masks',
                          'coincident coverage gates', 'source and implementation hashes'])
    after = snapshot()
    if before != after:
        raise RuntimeError('Files changed during the audit; rerun after other writers finish.')
    result['file_sha256'] = after
    (OUTPUT / 'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify_outputs(), indent=2))
