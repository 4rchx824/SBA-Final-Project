"""March-only operating-state calibration. States are not measured occupancy."""
import numpy as np
import pandas as pd

CALIBRATION_START = '2019-03-06'
EVALUATION_START = '2019-04-01'
EVALUATION_END = '2019-05-01'


def add_interpolation_fractions(intervals, quality_path):
    """Fraction of minutes repaired in any source column of each measure."""
    runs = pd.read_csv(quality_path, parse_dates=['start', 'end'])
    out = intervals.copy()
    for measure in ['light', 'plug', 'lux', 'total']:
        out[measure + '_interpolated_fraction'] = 0.0
    for (floor, zone), indices in out.groupby(['floor', 'zone']).groups.items():
        group = out.loc[indices]
        relevant = runs.loc[(runs.floor == floor) & runs.column.str.startswith(f'z{zone}_')]
        for measure, pattern in [('light', r'_Light\(kW\)$'), ('plug', r'_Plug\(kW\)$'),
                                 ('lux', r'_S1\(lux\)$'), ('total', r'\(kW\)$')]:
            repaired = set()
            for row in relevant.loc[relevant.column.str.contains(pattern)].itertuples():
                repaired.update(pd.date_range(row.start, row.end, freq='min'))
            if repaired:
                counts = pd.Series(1, index=pd.DatetimeIndex(sorted(repaired))).resample('15min').sum()
                out.loc[indices, measure + '_interpolated_fraction'] = group.Date.map(counts).fillna(0).to_numpy() / 15
    return out


def fit_states(values, minimum_count=96, minimum_share=.1, minimum_separation=2., minimum_gap=.02):
    """Deterministic two-means with explicit support/separation gates and deadband.

    Gates are modelling assumptions, not comfort requirements. Low <= low-cluster
    p95; high >= high-cluster p05; between these boundaries is unknown.
    """
    x = values.dropna().to_numpy(dtype=float)
    result = dict(n=len(x), low_kW=np.nan, high_kW=np.nan, standby_kW=np.nan,
                  separation=np.nan, low_share=np.nan, status='insufficient data')
    if len(x) < minimum_count:
        return result
    centers = np.quantile(x, [0.1, 0.9])
    if centers[1] - centers[0] < minimum_gap:
        result['status'] = 'no distinct operating states'
        return result
    for _ in range(100):
        lower = x <= centers.mean()
        if lower.all() or not lower.any():
            return result
        updated = np.array([x[lower].mean(), x[~lower].mean()])
        if np.allclose(updated, centers):
            centers = updated
            break
        centers = updated
    low, high = x[x <= centers.mean()], x[x > centers.mean()]
    pooled = np.sqrt((low.var() + high.var()) / 2)
    separation = (high.mean() - low.mean()) / max(pooled, 0.01)
    low_edge, high_edge = np.quantile(low, .95), np.quantile(high, .05)
    result.update(low_kW=low_edge, high_kW=high_edge, standby_kW=np.median(low),
                  separation=separation, low_share=len(low)/len(x))
    result['status'] = ('supported' if separation >= minimum_separation and min(len(low), len(high))/len(x) >= minimum_share
                        and high_edge - low_edge >= minimum_gap else 'no distinct operating states')
    return result


def classify(values, row, shift=0):
    state = pd.Series('unknown', index=values.index)
    if row.status != 'supported':
        return state
    # Shift both boundaries by a fraction of the gap for sensitivity.
    delta = shift * (row.high_kW - row.low_kW)
    state.loc[values <= max(0, row.low_kW + delta)] = 'low'
    state.loc[values >= row.high_kW + delta] = 'high'
    return state
