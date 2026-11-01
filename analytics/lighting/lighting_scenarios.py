"""Retrospective illustrative scenarios; no validated comfort or control commands."""
import json
import numpy as np
import pandas as pd

from prepare_inputs import HERE, ROOT, OUTPUT, load_inputs, sha256
from validation_audit import build_validation_tables
from schedules import operating_index, schedule_settings, legacy_settings, label


def policy_series(group, policy):
    if policy == 'strict':
        total = group.total_kW.where(group.power_complete)
        light = group.light_kW.where(group.power_complete)
        lux = group.lux.where(group.paired_complete)
    elif policy == 'common_minutes':
        paired = group.common_paired_coverage.ge(.8)
        # Joint means share power/lux support. Keep observed power when lux disables control.
        total = group.common_paired_total_kW.where(paired, group.common_power_total_kW)
        light = group.common_paired_light_kW.where(paired, group.common_power_light_kW)
        lux = group.common_paired_lux.where(paired)
    else:
        raise ValueError(f'Unknown interval policy: {policy}')
    return pd.DataFrame(dict(baseline_total_kW=total, lighting_kW=light, ambient_lux=lux), index=group.index)


def apply_scenario(series, trigger, calibration_ok, evaluation_ok, has_lux_sensor, target, cap):
    """Preserve unknown demand and label why each observed interval takes no action."""
    if not np.isfinite(target) or target <= 0 or not 0 <= cap <= 1:
        raise ValueError('Target must be positive and power-reduction cap must be in [0, 1].')
    out = series.copy()
    reason = pd.Series('eligible', index=out.index)
    # Ordered reasons retain the first binding limitation, with missing demand explicit.
    conditions = [
        (out.baseline_total_kW.isna(), 'missing power'),
        (pd.Series(cap == 0, index=out.index), 'no-change reference'),
        (pd.Series(not calibration_ok, index=out.index), 'insufficient calibration'),
        (pd.Series(not evaluation_ok, index=out.index), 'insufficient evaluation coverage'),
        (pd.Series(not has_lux_sensor, index=out.index), 'no lux sensor'),
        (out.ambient_lux.isna(), 'missing lux'),
        (out.ambient_lux.le(0), 'nonpositive lux'),
        (out.lighting_kW.isna(), 'missing lighting'),
        (out.baseline_total_kW.le(trigger), 'below demand trigger'),
        (out.ambient_lux.le(target), 'no headroom under target')]
    for condition, label in conditions:
        reason.loc[reason.eq('eligible') & condition] = label
    fraction = (1 - target/out.ambient_lux).clip(lower=0, upper=cap)
    reduction = (fraction*out.lighting_kW).where(reason.eq('eligible'), 0.)
    reduction = reduction.where(out.baseline_total_kW.notna())
    out['reduction_kW'] = reduction
    out['scenario_total_kW'] = out.baseline_total_kW - reduction
    out['eligibility_reason'] = reason
    high = out.baseline_total_kW.gt(trigger) & out.baseline_total_kW.notna() if pd.notna(trigger) else pd.Series(False, index=out.index)
    breaks = high.ne(high.shift()) | out.index.to_series().diff().ne(pd.Timedelta(minutes=15))
    out['high_demand_event'] = breaks.cumsum().where(high).astype('Int64')
    if cap == 0:
        assert out.baseline_total_kW.equals(out.scenario_total_kW)
    assert not (out.reduction_kW > out.lighting_kW + 1e-9).fillna(False).any()
    assert not out.scenario_total_kW.lt(-1e-9).any()
    return out


def summarize_scenario(out, reportable):
    base = out.baseline_total_kW.max()
    after = out.scenario_total_kW.max()
    reduction = base-after
    energy = out.reduction_kW.sum(min_count=1)*.25
    base_time = out.baseline_total_kW.idxmax() if out.baseline_total_kW.notna().any() else pd.NaT
    after_time = out.scenario_total_kW.idxmax() if out.scenario_total_kW.notna().any() else pd.NaT
    light_at_peak = out.loc[base_time, 'lighting_kW'] if pd.notna(base_time) else np.nan
    return dict(observed_baseline_peak_kW=base, observed_scenario_peak_kW=after,
                baseline_peak_time=base_time, scenario_peak_time=after_time,
                peak_shifted=(base_time != after_time) if pd.notna(base_time) and pd.notna(after_time) else None,
                lighting_kW_at_original_peak=light_at_peak,
                lighting_share_at_original_peak_pct=100*light_at_peak/base if pd.notna(base) and base > 0 else np.nan,
                paired_observed_peak_reduction_kW=reduction,
                paired_observed_reduction_pct=100*reduction/base if pd.notna(base) and base > 0 else np.nan,
                paired_observed_energy_reduction_kWh=energy,
                reported_peak_reduction_kW=reduction if reportable else np.nan,
                reported_peak_reduction_pct=(100*reduction/base if reportable and pd.notna(base) and base > 0 else np.nan),
                reported_energy_reduction_kWh=energy if reportable else np.nan,
                high_demand_intervals=int(out.high_demand_event.notna().sum()),
                high_demand_events=int(out.high_demand_event.nunique()),
                modeled_action_intervals=int(out.reduction_kW.gt(0).sum()))


def run_scenarios():
    data, manifest = load_inputs(); settings = manifest['settings']; options = settings['scenarios']
    legacy_dates = operating_index(legacy_settings(settings), settings['calibration_start'], settings['evaluation_start'])
    legacy = pd.read_csv(ROOT/'outputs'/'baseline'/'lighting_zone_april_baseline.csv').set_index(['floor','zone'])
    summaries, reasons, primary_parts = [], [], []
    interval_path = OUTPUT/'scenario_intervals.csv.gz'
    # Stream one zone/policy at a time instead of retaining every sensitivity series in memory.
    import gzip
    with gzip.open(interval_path, 'wt') as stream:
        first = True
        for (floor, zone), group in data.groupby(['floor', 'zone']):
            source = group.set_index('Date').sort_index()
            original_trigger = source.total_kW.reindex(legacy_dates).quantile(.95)
            assert np.isclose(original_trigger, legacy.loc[(floor,zone),'march_p95_trigger_kW'],equal_nan=True), 'Original March trigger does not reproduce'
            for schedule_id, schedule in schedule_settings(settings):
                march_dates = operating_index(schedule, settings['calibration_start'], settings['evaluation_start'])
                april_dates = operating_index(schedule, settings['evaluation_start'], settings['evaluation_end'])
                for policy in options['policies']:
                    selected = policy_series(source, policy)
                    march = selected.reindex(march_dates); april = selected.reindex(april_dates)
                    march_coverage = march.baseline_total_kW.notna().mean()
                    april_coverage = april.baseline_total_kW.notna().mean()
                    trigger = march.baseline_total_kW.quantile(.95)
                    sensor = bool(group.has_lux_sensor.iloc[0])
                    for gate in options['period_coverage_gates']:
                        calibration_ok = march_coverage >= gate and pd.notna(trigger)
                        lux_coverage = april.ambient_lux.notna().mean()
                        evaluation_ok = april_coverage >= gate and (lux_coverage >= gate if sensor else True)
                        for target in options['lux_targets']:
                            for cap in options['power_reduction_caps']:
                                scenario_id = f'{schedule_id}_{policy}_coverage{gate:g}_lux{target}_cap{cap:g}'
                                out = apply_scenario(april, trigger, calibration_ok, evaluation_ok, sensor, target, cap)
                                reportable = calibration_ok and evaluation_ok and sensor and out.ambient_lux.notna().any()
                                summary = summarize_scenario(out, reportable)
                                summary.update(floor=floor, zone=zone, scenario_id=scenario_id, schedule_id=schedule_id, operating_window=label(schedule), policy=policy,
                                               period_coverage_gate=gate, target_lux=target, reduction_cap=cap,
                                               march_p95_kW=trigger, legacy_march_p95_kW=original_trigger, legacy_trigger_reproduced=True, march_expected_intervals=len(march_dates),
                                               march_valid_intervals=int(march.baseline_total_kW.notna().sum()),
                                               march_coverage_pct=100*march_coverage, april_expected_intervals=len(april_dates),
                                               april_valid_intervals=int(april.baseline_total_kW.notna().sum()),
                                               april_coverage_pct=100*april_coverage, april_lux_coverage_pct=100*lux_coverage, has_lux_sensor=sensor,
                                               status=('insufficient calibration' if not calibration_ok else
                                                       'insufficient April power coverage' if april_coverage < gate else
                                                       'no lux sensor' if not sensor else
                                                       'insufficient April paired coverage' if lux_coverage < gate else
                                                       'no valid lux' if not out.ambient_lux.notna().any() else
                                                       'modeled result; comfort unvalidated'))
                                summaries.append(summary)
                                for reason, count in out.eligibility_reason.value_counts().items():
                                    reasons.append(dict(floor=floor, zone=zone, scenario_id=scenario_id,
                                                        reason=reason, intervals=int(count)))
                                primary = (policy == 'strict' and gate == options['primary_period_coverage_gate'] and
                                           target == options['primary_target_lux'] and cap == options['primary_cap'])
                                if primary:
                                    primary_parts.append(out.assign(floor=floor, zone=zone, schedule_id=schedule_id))
                                out.assign(floor=floor, zone=zone, scenario_id=scenario_id, schedule_id=schedule_id).rename_axis('Date').reset_index().to_csv(stream,index=False,header=first)
                                first = False
    summary = pd.DataFrame(summaries); reasons = pd.DataFrame(reasons)
    summary.to_csv(OUTPUT/'scenario_sensitivity.csv',index=False)
    primary_mask = (summary.policy.eq('strict') & summary.period_coverage_gate.eq(options['primary_period_coverage_gate']) &
                    summary.target_lux.eq(options['primary_target_lux']) & summary.reduction_cap.eq(options['primary_cap']))
    comparison = summary.loc[primary_mask].copy()
    comparison.to_csv(OUTPUT/'scenario_schedule_comparison.csv',index=False)
    primary = comparison.loc[comparison.schedule_id.eq('primary')].copy()
    primary.to_csv(OUTPUT/'scenario_summary.csv',index=False)
    reasons.to_csv(OUTPUT/'scenario_exclusion_reasons.csv',index=False)
    validations = [(schedule_id, build_validation_tables(data, schedule)) for schedule_id, schedule in schedule_settings(settings)]
    coverage = pd.concat([tables[0].assign(schedule_id=sid) for sid,tables in validations],ignore_index=True)
    targets = pd.concat([tables[1].assign(schedule_id=sid) for sid,tables in validations],ignore_index=True)
    coverage.to_csv(OUTPUT/'building_coincidence_audit.csv',index=False)
    targets.to_csv(OUTPUT/'lighting_target_validation.csv',index=False)
    aligned = pd.concat(primary_parts).reset_index(names='Date')
    impacts = []
    for schedule_id, schedule in schedule_settings(settings):
        schedule_data = aligned.loc[aligned.schedule_id.eq(schedule_id)]
        april_dates = operating_index(schedule, settings['evaluation_start'], settings['evaluation_end'])
        for scope in ['building','Floor 2']:
            subset = schedule_data if scope == 'building' else schedule_data.loc[schedule_data.floor.eq(2)]
            n = subset[['floor','zone']].drop_duplicates().shape[0]
            base = subset.pivot(index='Date',columns=['floor','zone'],values='baseline_total_kW').sum(axis=1,min_count=n)
            after = subset.pivot(index='Date',columns=['floor','zone'],values='scenario_total_kW').sum(axis=1,min_count=n)
            valid = base.notna() & after.notna()
            count = int(valid.sum()); fraction = count/len(april_dates)
            impacts.append(dict(scope=scope,schedule_id=schedule_id,operating_window=label(schedule),simultaneous_intervals=count,expected_intervals=len(april_dates),
                                coverage_pct=100*fraction, observed_baseline_peak_kW=base.loc[valid].max(),
                                paired_observed_peak_reduction_kW=base.loc[valid].max()-after.loc[valid].max(),
                                reported_peak_reduction_kW=(base.loc[valid].max()-after.loc[valid].max()
                                                           if fraction >= options['primary_period_coverage_gate'] else np.nan),
                                status='insufficient simultaneous coverage' if fraction < options['primary_period_coverage_gate']
                                       else 'aligned submeter scenario only; comfort/main-meter unvalidated'))
    impacts = pd.DataFrame(impacts); impacts.to_csv(OUTPUT/'coincident_scenario_impact.csv',index=False)
    (OUTPUT/'scenario_manifest.json').write_text(json.dumps(dict(
        input_manifest_sha256=sha256(OUTPUT/'run_manifest.json'),
        implementation_sha256=sha256(HERE/'lighting_scenarios.py'),
        audit_source_sha256=sha256(HERE/'validation_audit.py'), settings=settings,
        evaluation_window='April weekday operating hours; not full-month peak',
        comfort_validation='not performed',independent_main_meter='not supplied'),indent=2)+'\n')
    return dict(settings=settings,schedule_comparison=comparison,summary=primary,sensitivity=summary,reasons=reasons,coverage=coverage,targets=targets,impacts=impacts)



def plot_scenario_results(results):
    """Show binding limitations and coverage; avoid indistinguishable zero-savings curves."""
    import matplotlib.pyplot as plt
    primary_ids = set(results['summary'].scenario_id)
    reasons = results['reasons'].loc[results['reasons'].scenario_id.isin(primary_ids) & results['reasons'].floor.eq(2)]
    counts = reasons.pivot(index='zone',columns='reason',values='intervals').fillna(0)/4
    fig, axes = plt.subplots(1,2,figsize=(13,4.5),layout='constrained')
    palette = ['#2878b5','#c56624','#809367','#aaaaaa','#735d9f','#c4a650']
    counts.plot.barh(stacked=True,ax=axes[0],color=palette[:len(counts.columns)])
    axes[0].set(title='Floor 2: why the primary rule takes no action',xlabel='April operating-window hours',ylabel='Zone')
    axes[0].legend(fontsize=8,loc='upper left',bbox_to_anchor=(0,-.20))
    coverage = results['coverage'].query("policy == 'complete cleaned power' and window == 'operating hours' and schedule_id == 'primary'")
    axes[1].barh(coverage.scope,coverage.coverage_pct,color=['#aaaaaa','#2878b5'])
    for r in coverage.itertuples():
        axes[1].text(r.coverage_pct, r.scope, f' {r.simultaneous_intervals}/{r.expected_intervals}',va='center')
    axes[1].set(title='Simultaneous power coverage',xlabel='Valid operating intervals (%)',xlim=(0,115))
    folder=OUTPUT/'lighting_scenario_figures';folder.mkdir(exist_ok=True)
    fig.savefig(folder/'scenario_limits_and_coverage.png',dpi=140)
    plt.show()


def export_combined_results(results, assessment):
    """Join evidence with scenarios without generating recommendation documents."""
    report = assessment['opportunities'].merge(
        results['summary'], on=['floor', 'zone'], validate='one_to_one',
        suffixes=('_assessment', '_scenario'))
    report.to_csv(OUTPUT / 'combined_lighting_summary.csv', index=False)
    primary = results['summary']
    overview = {
        'operating_window': label(results['settings']),
        'zones': len(primary),
        'reportable_zones': int(primary.reported_peak_reduction_kW.notna().sum()),
        'withheld_zones': int(primary.reported_peak_reduction_kW.isna().sum()),
        'positive_modeled_reduction_zones': int(primary.reported_peak_reduction_kW.gt(1e-9).sum()),
        'status_counts': primary.status.value_counts().to_dict(),
        'zone_scenario_combinations': len(results['sensitivity']),
        'comfort_preserving_savings': 'undetermined; ambient lux is not task-plane illuminance',
        'building_impact': 'unverified; aligned submeters are not an independent main meter',
        'zero_interpretation': 'No modeled reduction under the tested assumptions is not proof of zero physical potential.'
    }
    (OUTPUT / 'analysis_summary.json').write_text(json.dumps(overview, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    results = run_scenarios()
    from assessment import run_assessment
    export_combined_results(results, run_assessment())
    print(results['summary'][['floor','zone','status','reported_peak_reduction_kW']].to_string(index=False))
    print(results['impacts'].to_string(index=False))
