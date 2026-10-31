"""Tests for occupancy-related uncertainty, calendar partitions and frozen calibration."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analytics/lighting'))
from activity_states import fit_states, classify
from assessment import assess_activity, calibrate_activity, schedule_table, matched_day_night

CONFIG=dict(minimum_state_intervals=96,minimum_cluster_share=.1,minimum_state_separation=2.,
            minimum_boundary_gap_kW=.02,coverage_gate=.8,matched_power_bins=4,minimum_matched_bin_count=8)


class LightingAssessmentTests(unittest.TestCase):
    def thresholds(self):
        return pd.DataFrame([dict(floor=2,zone=1,measure=m,status='supported',low_kW=.2,high_kW=1.)
                             for m in ['light','plug']])

    def group(self):
        return pd.DataFrame(dict(Date=pd.date_range('2019-04-01',periods=8,freq='15min'),
                                 floor=2,zone=1,month='2019-04',light_kW=2.,plug_kW=.1,
                                 light_interpolated_fraction=0.,plug_interpolated_fraction=0.,
                                 repair_provenance_available=True,schedule_segment='weekday outside hours'))

    def test_flat_meter_does_not_create_activity(self):
        self.assertNotEqual(fit_states(pd.Series([.1]*200))['status'],'supported')

    def test_separated_states_are_supported(self):
        self.assertEqual(fit_states(pd.Series([.1]*100+[2.]*100))['status'],'supported')

    def test_deadband_is_unknown(self):
        row=self.thresholds().iloc[0]
        states=classify(pd.Series([.1,.5,2.,np.nan]),row)
        self.assertEqual(states.tolist(),['low','unknown','high','unknown'])

    def test_trailing_rule_never_retroactively_flags(self):
        result=assess_activity(self.group(),self.thresholds())
        self.assertEqual(result.activity_mismatch.tolist(),[False,False,False,True,True,True,True,True])

    def test_missing_and_repaired_values_break_activity(self):
        group=self.group();group.loc[3,'plug_kW']=np.nan;group.loc[5,'light_interpolated_fraction']=1/15
        result=assess_activity(group,self.thresholds())
        self.assertFalse(result.activity_mismatch.any())
        self.assertEqual(result.loc[3,'activity_state'],'unknown')

    def test_timestamp_gap_breaks_activity(self):
        result=assess_activity(self.group().drop(index=3),self.thresholds())
        self.assertFalse(result.loc[result.Date.lt('2019-04-01 01:45'),'activity_mismatch'].any())
        self.assertTrue(result.iloc[-1].activity_mismatch)

    def test_unsupported_plug_remains_unknown(self):
        thresholds=self.thresholds();thresholds.loc[thresholds.measure.eq('plug'),'status']='unsupported'
        result=assess_activity(self.group(),thresholds)
        self.assertTrue(result.activity_state.eq('unknown').all())
        self.assertFalse(result.activity_mismatch.any())

    def test_april_values_cannot_change_march_calibration(self):
        group=pd.concat([self.group()]*30,ignore_index=True)
        group['month']='2019-03';group.loc[120:,'light_kW']=.1;group.loc[120:,'plug_kW']=2.
        before=calibrate_activity(group,CONFIG)
        april=group.copy();april['month']='2019-04';april['light_kW']=999
        after=calibrate_activity(pd.concat([group,april],ignore_index=True),CONFIG)
        pd.testing.assert_frame_equal(before,after)

    def test_all_missing_schedule_energy_is_unknown_not_zero(self):
        group=self.group();group['light_kW']=np.nan
        result=schedule_table(group)
        self.assertTrue(np.isnan(result.iloc[0].valid_period_lighting_kWh))
        self.assertEqual(result.iloc[0].light_coverage_pct,0)

    def test_schedule_segments_reconcile_valid_energy(self):
        group=self.group();group.loc[4:,'schedule_segment']='weekend'
        result=schedule_table(group)
        self.assertAlmostEqual(result.valid_period_lighting_kWh.sum(),group.light_kW.sum()/4)

    def test_day_night_requires_common_power_support(self):
        group=self.group();group['hour']=12;group['has_lux_sensor']=True;group['lux']=10.;group['month']='2019-03'
        group=pd.concat([group]*30,ignore_index=True)
        group.loc[120:,'light_kW']=.1
        bands,summary=matched_day_night(group,CONFIG)
        self.assertTrue(bands.empty)
        self.assertTrue(summary.median_matched_day_minus_night_lux.isna().all())

if __name__=='__main__':
    unittest.main()
