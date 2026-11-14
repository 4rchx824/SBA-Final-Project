"""Export a compact dashboard snapshot only from a verified lighting bundle."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analytics'))
from check_lighting_freshness import check_freshness


def main():
    receipt = check_freshness(ROOT)
    source = ROOT / 'outputs/lighting'
    target = Path(__file__).parent / 'dist'
    target.mkdir(exist_ok=True)
    tables = {}
    for key, filename in {
        'scenarios': 'scenario_sensitivity',
        'opportunities': 'lighting_opportunities',
        'schedules': 'lighting_schedule',
        'coverage': 'lighting_coverage',
        'coincidence': 'coincident_scenario_impact',
    }.items():
        frame = pd.read_csv(source / (filename + '.csv'))
        tables[key] = json.loads(frame.to_json(orient='records', double_precision=8))
    intervals = pd.read_csv(source / 'zone_15min.csv', parse_dates=['Date'])
    april = intervals.loc[intervals.Date.dt.month.eq(4)].copy()
    april['hour'] = april.Date.dt.hour
    profiles = april.groupby(['floor', 'zone', 'hour'])[['total_kW', 'light_kW', 'lux']].mean().reset_index()
    tables['profiles'] = json.loads(profiles.to_json(orient='records', double_precision=6))
    tables['meta'] = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'calibration': '6–31 March 2019',
        'evaluation': '1–30 April 2019',
        'timezone': 'Asia/Bangkok',
        'audit': {k: v for k, v in receipt.items() if k != 'file_sha256'},
        'source_hashes': receipt['file_sha256'],
    }
    assert len(tables['scenarios']) == 6336
    assert len(tables['opportunities']) == 33
    assert len(profiles) == 33 * 24
    (target / 'data.js').write_text('window.LIGHTING_DATA=' + json.dumps(tables, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    for filename in ['scenario_summary.csv', 'lighting_opportunities.csv', 'lighting_schedule.csv']:
        (target / filename).write_bytes((source / filename).read_bytes())
    print('Exported verified snapshot: 33 zones, 6,336 scenarios, 792 hourly profile points.')


if __name__ == '__main__':
    main()
