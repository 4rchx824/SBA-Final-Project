"""Meaningful controls on scenario arithmetic, missingness and minute support."""
import sys
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'analytics/lighting'))
from lighting_scenarios import apply_scenario, summarize_scenario, calibrate_lux_trigger
from prepare_inputs import zone_minute_support


class LightingScenarioTests(unittest.TestCase):
    def series(self):
        return pd.DataFrame(dict(baseline_total_kW=[10.,9.,4.],lighting_kW=[4.,2.,1.],ambient_lux=[200.,80.,80.]),
                            index=pd.date_range('2019-04-01 08:00',periods=3,freq='15min'))

    def apply(self,series=None,**kwargs):
        defaults=dict(trigger=5.,calibration_ok=True,evaluation_ok=True,has_lux_sensor=True,lux_trigger=100,cap=.5)
        defaults.update(kwargs)
        return apply_scenario(self.series() if series is None else series,**defaults)

    def test_primary_method_has_no_fixed_lux_benchmarks(self):
        options = json.loads((ROOT / 'analytics/lighting/config.json').read_text())['scenarios']
        self.assertEqual(options['primary_lux_quantile'], .95)
        self.assertEqual(options['lux_quantiles'], [.90, .95, .975])
        self.assertNotIn('fixed_reference_lux', options)
        self.assertNotIn('primary_target_lux', options)

    def test_march_trigger_does_not_learn_from_april(self):
        march = self.series().rename(columns={'ambient_lux': 'ignored'})
        march['ambient_lux'] = [10., 20., 30.]
        march.index = pd.date_range('2019-03-06 08:00', periods=3, freq='15min')
        april = self.series()
        combined = pd.concat([march, april])
        before = calibrate_lux_trigger(combined.loc[combined.index.month == 3], .95, 1., 3)
        combined.loc[combined.index.month == 4, 'ambient_lux'] = 100000.
        after = calibrate_lux_trigger(combined.loc[combined.index.month == 3], .95, 1., 3)
        self.assertEqual(before, after)
        self.assertEqual(before['lux_trigger_lux'], 29.)

    def test_lux_calibration_withholds_sparse_or_flat_data(self):
        march = self.series()
        march['ambient_lux'] = [0., 10., 20.]
        fit = calibrate_lux_trigger(march, .95, 1., 3)
        self.assertTrue(fit['lux_calibration_supported'])
        self.assertEqual(fit['march_lux_valid_intervals'], 3)
        self.assertFalse(calibrate_lux_trigger(march, .95, 1., 4)['lux_calibration_supported'])
        march['ambient_lux'] = 80.
        self.assertFalse(calibrate_lux_trigger(march, .95, 1., 3)['lux_calibration_supported'])
        march['ambient_lux'] = np.nan
        fit = calibrate_lux_trigger(march, .95, 1., 3)
        out = self.apply(lux_trigger=fit['lux_trigger_lux'], lux_calibration_ok=False)
        self.assertTrue(out.reduction_kW.eq(0).all())
        self.assertTrue(out.eligibility_reason.eq('insufficient March lux calibration').all())

    def test_percentile_selects_candidates_without_becoming_a_dimming_target(self):
        data = self.series()
        data['ambient_lux'] = [101., 100., 99.]
        out = self.apply(data, lux_trigger=100., cap=.2, trigger=0.)
        self.assertEqual(out.investigation_flag.tolist(), [True, False, False])
        self.assertEqual(out.reduction_kW.tolist(), [.8, 0., 0.])
        no_change = self.apply(data, lux_trigger=100., cap=0., trigger=0.)
        self.assertEqual(no_change.investigation_flag.tolist(), out.investigation_flag.tolist())
        self.assertTrue(no_change.reduction_kW.eq(0).all())

    def test_peak_is_recomputed_after_original_peak_falls(self):
        out=self.apply();summary=summarize_scenario(out,True)
        self.assertEqual(out.scenario_total_kW.tolist(),[8.,9.,4.])
        self.assertEqual(summary['reported_peak_reduction_kW'],1.)
        self.assertEqual(summary['reported_energy_reduction_kWh'],.5)
        self.assertEqual(summary['baseline_peak_time'], out.index[0])
        self.assertEqual(summary['scenario_peak_time'], out.index[1])
        self.assertTrue(summary['peak_shifted'])
        self.assertEqual(summary['lighting_share_at_original_peak_pct'], 40.)

    def test_all_missing_peaks_are_not_a_peak_shift_or_zero_saving(self):
        data = self.series()
        data['baseline_total_kW'] = np.nan
        summary = summarize_scenario(self.apply(data), False)
        self.assertTrue(pd.isna(summary['baseline_peak_time']))
        self.assertIsNone(summary['peak_shifted'])
        self.assertTrue(pd.isna(summary['reported_peak_reduction_kW']))

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

    def test_below_lux_trigger_is_a_rule_zero_not_negative_reduction(self):
        data=self.series();data['ambient_lux']=50
        out=self.apply(data)
        self.assertTrue(out.reduction_kW.eq(0).all())
        self.assertEqual(out.eligibility_reason.iloc[0],'below March lux trigger')

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

    def test_invalid_supported_lux_triggers_are_rejected(self):
        for target in [0,-1,np.nan]:
            with self.assertRaises(ValueError):self.apply(lux_trigger=target)

    def test_common_minutes_exclude_lighting_when_other_power_is_missing(self):
        dates=pd.date_range('2019-03-06 08:00',periods=15,freq='min')
        data=pd.DataFrame({'z1_Light(kW)':[100.]+[1.]*14,'z1_AC1(kW)':[np.nan]+[2.]*14,'z1_S1(lux)':[100.]*15},index=dates)
        result=zone_minute_support(data,1).iloc[0]
        self.assertEqual(result.common_power_light_kW,1.)
        self.assertEqual(result.common_power_total_kW,3.)
        self.assertFalse(result.power_complete)
        self.assertAlmostEqual(result.common_paired_coverage,14/15)

if __name__=='__main__':unittest.main()
