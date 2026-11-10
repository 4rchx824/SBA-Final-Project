"""Schedule boundaries and energy accounting across the two assumed windows."""
import json
from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'analytics/lighting'))
from schedules import operating_index, operating_mask, schedule_settings, transition_mask
from assessment import schedule_comparison

SETTINGS = json.loads((ROOT / 'analytics/lighting/config.json').read_text())


class ScheduleTests(unittest.TestCase):
    def test_actual_calendar_denominators(self):
        schedules = dict(schedule_settings(SETTINGS))
        for name, expected in [('primary', (648, 792)), ('extended', (720, 880))]:
            settings = schedules[name]
            self.assertEqual(len(operating_index(settings, '2019-03-06', '2019-04-01')), expected[0])
            self.assertEqual(len(operating_index(settings, '2019-04-01', '2019-05-01')), expected[1])

    def test_holiday_sensitivity_preserves_original_and_excludes_only_labelled_dates(self):
        settings = {**SETTINGS, 'university_holiday_dates': ['2019-04-08', '2019-04-12', '2019-04-15', '2019-04-16']}
        schedules = dict(schedule_settings(settings))
        expected = {'primary': 792, 'extended': 880,
                    'primary_holiday_excluded': 648, 'extended_holiday_excluded': 720}
        for name, count in expected.items():
            self.assertEqual(len(operating_index(schedules[name], '2019-04-01', '2019-05-01')), count)

    def test_transition_is_not_primary_operating_time(self):
        dates = pd.to_datetime(['2019-04-01 16:45', '2019-04-01 17:00', '2019-04-01 18:00', '2019-04-06 17:00'])
        self.assertEqual(operating_mask(dates, SETTINGS).tolist(), [True, False, False, False])
        self.assertEqual(transition_mask(dates, SETTINGS).tolist(), [False, True, False, False])

    def test_extending_schedule_only_reclassifies_energy(self):
        dates = pd.date_range('2019-04-01', periods=96, freq='15min')
        data = pd.DataFrame(dict(Date=dates, floor=2, zone=1, light_kW=2.,
                                 is_transition_hour=transition_mask(dates, SETTINGS)))
        result = schedule_comparison(data, SETTINGS).set_index(['schedule_id', 'period'])
        for sid in ['primary', 'extended']:
            total = sum(result.loc[(sid, period), 'lighting_kWh'] for period in ['operating', 'outside'])
            self.assertEqual(total, 48.)
        difference = result.loc[('primary', 'outside'), 'lighting_kWh'] - result.loc[('extended', 'outside'), 'lighting_kWh']
        self.assertEqual(difference, result.loc[('primary', 'transition'), 'lighting_kWh'])


if __name__ == '__main__':
    unittest.main()
