"""Validate simultaneous coverage and missing-versus-zero lighting evidence."""
import sys
import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'analytics/lighting'))
from validation_audit import build_validation_tables

SETTINGS = dict(evaluation_start='2019-04-01 08:00', evaluation_end='2019-04-01 09:00',
                operating_weekdays=[0, 1, 2, 3, 4], operating_start_hour=8, operating_end_hour=18)


class LightingValidationTests(unittest.TestCase):
    def data(self):
        dates = pd.date_range(SETTINGS['evaluation_start'], periods=4, freq='15min')
        return pd.DataFrame(dict(Date=list(dates)*2, floor=[2]*4+[3]*4, zone=1,
                                 total_kW=[1, None, 1, 1, None, 2, 2, 2],
                                 power_complete=[True, False, True, True, False, True, True, True], lux=80.))

    def test_individual_coverage_is_not_simultaneous_coverage(self):
        coverage, _ = build_validation_tables(self.data(), SETTINGS)
        building = coverage.query("scope == 'building' and window == 'operating hours'")
        self.assertTrue(building.simultaneous_intervals.eq(2).all())
        self.assertTrue(building.expected_intervals.eq(4).all())

    def test_missing_lux_does_not_become_proven_zero_headroom(self):
        data = self.data(); data['lux'] = float('nan')
        _, headroom = build_validation_tables(data, SETTINGS)
        self.assertTrue(headroom.valid_lux_intervals.eq(0).all())
        self.assertTrue(headroom.maximum_ambient_lux.isna().all())
        self.assertTrue(headroom.status.eq('unavailable: no valid lux').all())

    def test_observed_lux_summary_has_no_arbitrary_threshold(self):
        _, headroom = build_validation_tables(self.data(), SETTINGS)
        self.assertNotIn('target_lux', headroom.columns)
        self.assertTrue(headroom.valid_lux_intervals.eq(4).all())
        self.assertTrue(headroom.maximum_ambient_lux.eq(80).all())

    def test_repair_free_coverage_is_distinct_and_requires_provenance(self):
        data = self.data()
        data['repair_provenance_available'] = True
        data['power_complete_without_repairs'] = data.power_complete
        data.loc[2, 'power_complete_without_repairs'] = False
        coverage, _ = build_validation_tables(data, SETTINGS)
        selected = coverage.query("scope == 'building' and window == 'all hours'").set_index('policy')
        self.assertEqual(selected.loc['complete cleaned power', 'simultaneous_intervals'], 2)
        self.assertEqual(selected.loc['repair-free complete power', 'simultaneous_intervals'], 1)
        data['repair_provenance_available'] = False
        coverage, _ = build_validation_tables(data, SETTINGS)
        self.assertFalse(coverage.policy.eq('repair-free complete power').any())


if __name__ == '__main__':
    unittest.main()
