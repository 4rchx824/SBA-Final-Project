"""Analysis adapter: reuse cleaned inputs and original baseline, without recleaning."""
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'baseline'))
from _shared import clean_data_directory, read_clean_file
from lighting_peak_baseline import _build_zone_intervals
from activity_states import add_interpolation_fractions


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def prepare_inputs():
    config_path = HERE / 'config.json'
    config = json.loads(config_path.read_text())
    clean_dir = clean_data_directory()
    support = ROOT / config['supporting_tables']
    supporting_paths = [support / f'{name}.csv' for name in ['data_quality','daily_summary','zone_hourly','removed_readings']]
    baseline_paths = [ROOT / 'baseline' / 'outputs' / name for name in
                      ['lighting_zone_april_baseline.csv','lighting_floor2_april_baseline.csv','lighting_lux_sensitivity.csv']]
    for path in supporting_paths + baseline_paths:
        if not path.exists():
            raise FileNotFoundError(f'Missing {path.relative_to(ROOT)}. Run cleaning then the original lighting baseline; no legacy fallback is used.')
    intervals = _build_zone_intervals(clean_dir)
    intervals = intervals.loc[(intervals.Date >= config['calibration_start']) &
                              (intervals.Date < config['evaluation_end'])].copy()
    # Add channels and schema presence flags without changing the baseline's values.
    pieces = []
    for floor in range(1,8):
        data = read_clean_file(clean_dir / f'2019Floor{floor}.csv', re.compile(r'z\d+_(?:AC\d+|Light|Plug)\(kW\)|z\d+_S1\(lux\)'))
        data = data.loc[config['calibration_start']:pd.Timestamp(config['evaluation_end'])-pd.Timedelta(minutes=1)]
        for zone in sorted(intervals.loc[intervals.floor.eq(floor), 'zone'].unique()):
            prefix = f'z{zone}_'
            power = [c for c in data if c.startswith(prefix) and c.endswith('(kW)')]
            plugs = [c for c in power if '_Plug' in c]
            lux = [c for c in data if c.startswith(prefix) and c.endswith('(lux)')]
            total_valid = data[power].notna().all(axis=1)
            lux_valid = data[lux].notna().all(axis=1) if lux else pd.Series(False,index=data.index)
            plug = data[plugs].sum(axis=1,min_count=len(plugs)) if plugs else pd.Series(np.nan,index=data.index)
            coverage = plug.notna().resample('15min').sum()/15
            item = pd.DataFrame({'plug_kW':plug.resample('15min').mean().where(coverage >= .8),
                                 'plug_coverage':coverage,
                                 'power_complete':total_valid.resample('15min').sum().eq(15),
                                 'paired_complete':(total_valid & lux_valid).resample('15min').sum().eq(15)})
            item['has_lux_sensor'] = bool(lux)
            item['has_plug_meter'] = bool(plugs)
            item['floor'],item['zone'] = floor,zone
            pieces.append(item.rename_axis('Date').reset_index())
    intervals = intervals.merge(pd.concat(pieces,ignore_index=True),on=['Date','floor','zone'],validate='one_to_one')
    daily = pd.read_csv(support / 'daily_summary.csv',parse_dates=['Date'])
    labels = daily[['Date','day_type']].drop_duplicates()
    if labels.Date.duplicated().any():
        raise ValueError('Conflicting floor day_type labels; resolve before joining.')
    labels = labels.rename(columns={'Date':'calendar_date'})
    intervals['calendar_date'] = intervals.Date.dt.normalize()
    intervals = intervals.merge(labels,on='calendar_date',how='left',validate='many_to_one')
    if intervals.day_type.isna().any():
        raise ValueError('The selected supporting table set lacks calendar labels for the evaluation period.')
    t=intervals.Date
    intervals['hour']=t.dt.hour
    intervals['month']=t.dt.strftime('%Y-%m')
    intervals['is_operating_hour']=(t.dt.dayofweek.isin(config['operating_weekdays']) &
                                    t.dt.hour.ge(config['operating_start_hour']) & t.dt.hour.lt(config['operating_end_hour']))
    intervals['schedule_segment']=np.select(
        [intervals.day_type.eq('closure'),t.dt.dayofweek.ge(5),intervals.is_operating_hour],
        ['inferred closure','weekend','weekday operating'],default='weekday outside hours')
    intervals['light_valid']=intervals.light_kW.notna()
    intervals['lux_valid']=intervals.lux.notna()
    intervals['paired_valid']=intervals.total_kW.notna() & intervals.light_kW.notna() & intervals.lux.notna()
    quality_path = clean_dir.parent / 'quality' / 'interpolated_runs.csv'
    # Upstream provenance is optional; never invent observed-only status if unavailable.
    if quality_path.exists():
        intervals = add_interpolation_fractions(intervals,quality_path)
        intervals['repair_provenance_available']=True
    else:
        for name in ['light','plug','lux','total']:
            intervals[name+'_interpolated_fraction']=np.nan
        intervals['repair_provenance_available']=False
    intervals['power_complete_without_repairs']=(intervals.power_complete & intervals.total_interpolated_fraction.eq(0))
    intervals['paired_complete_without_repairs']=(intervals.paired_complete & intervals.total_interpolated_fraction.eq(0) & intervals.lux_interpolated_fraction.eq(0))
    intervals=intervals.sort_values(['floor','zone','Date']).reset_index(drop=True)
    assert not intervals.duplicated(['Date','floor','zone']).any()
    counts=intervals.groupby(['floor','zone']).size()
    assert len(counts)==33 and counts.eq(5376).all(),counts
    for month,expected in [('2019-03',720),('2019-04',880)]:
        assert intervals.loc[intervals.month.eq(month)&intervals.is_operating_hour].groupby(['floor','zone']).size().eq(expected).all()
    # Reconcile with saved baseline on its exact operating-window definition.
    saved=pd.read_csv(baseline_paths[0])
    april=intervals.loc[intervals.month.eq('2019-04')&intervals.is_operating_hour]
    recalculated=april.groupby(['floor','zone']).total_kW.max().rename('recalculated').reset_index()
    check=saved.merge(recalculated,on=['floor','zone'],validate='one_to_one')
    if not np.allclose(check.april_peak_total_kW,check.recalculated,equal_nan=True):
        raise ValueError('Saved baseline does not reconcile with cleaned inputs. Rerun the original lighting baseline.')
    out=HERE/'outputs'; out.mkdir(exist_ok=True)
    intervals.to_csv(out/'zone_15min.csv',index=False)
    sources=sorted(clean_dir.glob('*Floor*.csv'))+supporting_paths+baseline_paths+[config_path,Path(__file__),HERE/'activity_states.py',ROOT/'baseline'/'lighting_peak_baseline.py']
    if quality_path.exists(): sources.append(quality_path)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    manifest={'source_revision':revision,'source_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
              'settings':config,'packages':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__},
              'sources':{str(p.relative_to(ROOT)):sha256(p) for p in sources},
              'output_sha256':sha256(out/'zone_15min.csv'),
              'baseline_reconciliation':'All 33 April operating-hour zone peaks reproduce saved baseline',
              'repair_note':'Complete after cleaning may include interpolation; repair-free flags require exported provenance.'}
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Prepared {len(intervals):,} intervals, 33 zones; saved baseline reconciled.')
    return intervals


def load_inputs():
    manifest_path=HERE/'outputs'/'run_manifest.json'
    if not manifest_path.exists():
        raise FileNotFoundError('Run analytics/lighting/prepare_inputs.py first.')
    manifest=json.loads(manifest_path.read_text())
    for relative,digest in manifest['sources'].items():
        path=ROOT/relative
        if not path.exists() or sha256(path)!=digest:
            raise ValueError(f'Input changed: {relative}. Rerun prepare_inputs.py.')
    path=HERE/'outputs'/'zone_15min.csv'
    if sha256(path)!=manifest['output_sha256']:
        raise ValueError('Shared interval table changed. Rerun prepare_inputs.py.')
    return pd.read_csv(path,parse_dates=['Date','calendar_date']),manifest


if __name__=='__main__':
    prepare_inputs()
