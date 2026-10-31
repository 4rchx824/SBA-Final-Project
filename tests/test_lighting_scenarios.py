"""Meaningful controls on scenario arithmetic, missingness and minute support."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analytics/lighting'))
from lighting_scenarios import apply_scenario, summarize_scenario
from prepare_inputs import zone_minute_support


class LightingScenarioTests(unittest.TestCase):
    def series(self):
        return pd.DataFrame(dict(baseline_total_kW=[10.,9.,4.],lighting_kW=[4.,2.,1.],ambient_lux=[200.,80.,80.]),
                            index=pd.date_range('2019-04-01 08:00',periods=3,freq='15min'))

    def apply(self,series=None,**kwargs):
        defaults=dict(trigger=5.,calibration_ok=True,evaluation_ok=True,has_lux_sensor=True,target=100,cap=.5)
        defaults.update(kwargs)
        return apply_scenario(self.series() if series is None else series,**defaults)

    def test_peak_is_recomputed_after_original_peak_falls(self):
        out=self.apply();summary=summarize_scenario(out,True)
        self.assertEqual(out.scenario_total_kW.tolist(),[8.,9.,4.])
        self.assertEqual(summary['reported_peak_reduction_kW'],1.)
        self.assertEqual(summary['reported_energy_reduction_kWh'],.5)

    def test_no_change_reproduces_every_observed_value(self):
        out=self.apply(cap=0)
        pd.testing.assert_series_equal(out.baseline_total_kW,out.scenario_total_kW,check_names=False)
        self.assertTrue(out.eligibility_reason.eq('no-change reference').all())

    def test_missing_power_stays_missing(self):
        data=self.series();data.iloc[0,0]=np.nan
        out=self.apply(data)
        self.assertTrue(pd.isna(out.scenario_total_kW.iloc[0]))
        self.assertEqual(out.eligibility_reason.iloc[0],'missing power')

    def test_no_sensor_or_calibration_disables_action(self):
        for options,reason in [({'has_lux_sensor':False},'no lux sensor'),({'calibration_ok':False},'insufficient calibration')]:
            out=self.apply(**options)
            self.assertTrue(out.reduction_kW.eq(0).all())
            self.assertTrue(out.eligibility_reason.eq(reason).all())
            self.assertTrue(pd.isna(summarize_scenario(out,False)['reported_peak_reduction_kW']))

    def test_below_target_is_a_rule_zero_not_negative_reduction(self):
        data=self.series();data['ambient_lux']=50
        out=self.apply(data)
        self.assertTrue(out.reduction_kW.eq(0).all())
        self.assertEqual(out.eligibility_reason.iloc[0],'no headroom under target')

    def test_missing_lux_and_valid_zero_lux_have_distinct_reasons(self):
        data=self.series();data.loc[data.index[0],'ambient_lux']=np.nan;data.loc[data.index[1],'ambient_lux']=0
        out=self.apply(data)
        self.assertEqual(out.eligibility_reason.iloc[0],'missing lux')
        self.assertEqual(out.eligibility_reason.iloc[1],'nonpositive lux')
        self.assertTrue(out.reduction_kW.eq(0).all())

    def test_zero_peak_has_undefined_percentage(self):
        data=self.series()*0
        self.assertTrue(pd.isna(summarize_scenario(self.apply(data),True)['paired_observed_reduction_pct']))

    def test_missing_interval_breaks_high_demand_event(self):
        data=self.series();data.iloc[1,0]=np.nan;data.iloc[2,0]=10
        out=self.apply(data)
        self.assertEqual(out.high_demand_event.nunique(),2)

    def test_invalid_targets_are_rejected(self):
        for target in [0,-1,np.nan]:
            with self.assertRaises(ValueError):self.apply(target=target)

    def test_common_minutes_exclude_lighting_when_other_power_is_missing(self):
        dates=pd.date_range('2019-03-06 08:00',periods=15,freq='min')
        data=pd.DataFrame({'z1_Light(kW)':[100.]+[1.]*14,'z1_AC1(kW)':[np.nan]+[2.]*14,'z1_S1(lux)':[100.]*15},index=dates)
        result=zone_minute_support(data,1).iloc[0]
        self.assertEqual(result.common_power_light_kW,1.)
        self.assertEqual(result.common_power_total_kW,3.)
        self.assertFalse(result.power_complete)
        self.assertAlmostEqual(result.common_paired_coverage,14/15)

if __name__=='__main__':unittest.main()
