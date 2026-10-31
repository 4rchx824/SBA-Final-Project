"""Reproduce available-data checks; this does not execute a reduction scenario."""
import pandas as pd


def build_validation_tables(intervals, settings):
    start, end = pd.Timestamp(settings['evaluation_start']), pd.Timestamp(settings['evaluation_end'])
    expected = pd.date_range(start, end, freq='15min', inclusive='left')
    operating = (expected.dayofweek.isin(settings['operating_weekdays']) &
                 (expected.hour >= settings['operating_start_hour']) &
                 (expected.hour < settings['operating_end_hour']))
    evaluation = intervals.loc[intervals.Date.ge(start) & intervals.Date.lt(end)].copy()
    zones = pd.MultiIndex.from_frame(intervals[['floor', 'zone']].drop_duplicates())
    coverage = []
    for scope in ['building', 'Floor 2']:
        selected_zones = zones if scope == 'building' else zones[zones.get_level_values('floor') == 2]
        group = evaluation if scope == 'building' else evaluation.loc[evaluation.floor.eq(2)]
        for policy in ['baseline-compatible power', 'complete cleaned power']:
            # Count simultaneous intervals, never sum separate zone maxima.
            valid = group.total_kW.notna() if policy.startswith('baseline') else group.power_complete.fillna(False)
            wide = group.assign(valid=valid).pivot(index='Date', columns=['floor', 'zone'], values='valid')
            wide = wide.reindex(index=expected, columns=selected_zones).fillna(False).astype(bool)
            simultaneous = wide.all(axis=1) if len(selected_zones) else pd.Series(False, index=expected)
            for window, dates in [('all hours', expected), ('operating hours', expected[operating])]:
                count = int(simultaneous.reindex(dates).sum())
                coverage.append(dict(scope=scope, policy=policy, window=window,
                                     zones=len(selected_zones), expected_intervals=len(dates),
                                     simultaneous_intervals=count,
                                     coverage_pct=100 * count / len(dates) if len(dates) else float('nan')))
    daytime = evaluation.loc[evaluation.Date.isin(expected[operating])]
    lux = daytime.lux.dropna()
    headroom = []
    # These are the existing proposal targets, not newly validated comfort requirements.
    for target in [100, 150, 200, 300, 500]:
        above = int(lux.ge(target).sum()) if len(lux) else None
        headroom.append(dict(target_lux=target, valid_lux_intervals=len(lux),
                             maximum_ambient_lux=lux.max(), intervals_at_or_above_target=above,
                             status=('unavailable: no valid lux' if not len(lux) else
                                     'no observed headroom under target' if above == 0 else
                                     'target reached; control response remains unvalidated')))
    return pd.DataFrame(coverage), pd.DataFrame(headroom)
