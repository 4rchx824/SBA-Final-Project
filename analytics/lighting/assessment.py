"""Descriptive lighting assessment; reduction simulations are a separate analysis."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from prepare_inputs import HERE, ROOT, load_inputs
from activity_states import fit_states, classify


def calibrate_activity(intervals, config):
    march=intervals.loc[intervals.month.eq('2019-03')]
    rows=[]
    for (floor,zone),group in march.groupby(['floor','zone']):
        for measure in ['light','plug']:
            # An upstream repair log permits a repair-free calibration; absent provenance is explicit.
            mask=group[measure+'_interpolated_fraction'].eq(0) if group.repair_provenance_available.all() else pd.Series(True,index=group.index)
            values=group[measure+'_kW'].where(mask)
            fit=fit_states(values,config['minimum_state_intervals'],config['minimum_cluster_share'],
                           config['minimum_state_separation'],config['minimum_boundary_gap_kW'])
            fit['calibration_coverage_pct']=100*values.notna().mean()
            if fit['calibration_coverage_pct'] < config['coverage_gate']*100:
                fit['status']='insufficient calibration coverage'
            rows.append(dict(floor=floor,zone=zone,measure=measure,
                             excludes_repaired=bool(group.repair_provenance_available.all()),**fit))
    return pd.DataFrame(rows)


def assess_activity(intervals,thresholds,minutes=60,shift=0):
    parts=[]
    for (floor,zone),group in intervals.loc[intervals.month.eq('2019-04')].groupby(['floor','zone']):
        group=group.sort_values('Date').copy()
        for measure in ['light','plug']:
            row=thresholds.loc[thresholds.floor.eq(floor)&thresholds.zone.eq(zone)&thresholds.measure.eq(measure)].iloc[0]
            values=group[measure+'_kW']
            if group.repair_provenance_available.all():
                values=values.where(group[measure+'_interpolated_fraction'].eq(0))
            group[measure+'_state']=classify(values,row,shift)
        candidate=group.light_state.eq('high')&group.plug_state.eq('low')
        breaks=candidate.ne(candidate.shift())|group.Date.diff().ne(pd.Timedelta(minutes=15))
        streak=candidate.groupby(breaks.cumsum()).cumsum()
        group['activity_mismatch']=candidate&streak.ge(int(np.ceil(minutes/15)))
        group['activity_known']=group.light_state.ne('unknown')&group.plug_state.ne('unknown')
        group['activity_state']=np.select(
            [~group.activity_known,group.activity_mismatch,group.plug_state.eq('high')],
            ['unknown','lighting high / sustained low plug activity','elevated plug activity'],
            default='other operating pattern')
        parts.append(group)
    return pd.concat(parts,ignore_index=True)


def schedule_table(april):
    rows=[]
    for (floor,zone,segment),group in april.groupby(['floor','zone','schedule_segment']):
        valid=group.light_kW.notna()
        rows.append(dict(floor=floor,zone=zone,schedule_segment=segment,
                         expected_intervals=len(group),valid_lighting_intervals=int(valid.sum()),
                         light_coverage_pct=100*valid.mean(),observed_lighting_hours=valid.sum()/4,
                         valid_period_lighting_kWh=group.light_kW.sum(min_count=1)/4,
                         mean_lighting_kW=group.light_kW.mean()))
    return pd.DataFrame(rows)


def coverage_table(intervals):
    rows=[]
    for (floor,zone,month),g in intervals.groupby(['floor','zone','month']):
        rows.append(dict(floor=floor,zone=zone,month=month,expected_intervals=len(g),
                         has_lux_sensor=bool(g.has_lux_sensor.iloc[0]),has_plug_meter=bool(g.has_plug_meter.iloc[0]),
                         total_coverage_pct=100*g.total_kW.notna().mean(),
                         light_coverage_pct=100*g.light_kW.notna().mean(),lux_coverage_pct=100*g.lux.notna().mean(),
                         paired_valid_pct=100*g.paired_valid.mean(),
                         power_complete_pct=100*g.power_complete.mean(),paired_complete_pct=100*g.paired_complete.mean(),
                         repair_free_power_complete_pct=(100*g.power_complete_without_repairs.mean() if g.repair_provenance_available.all() else np.nan)))
    return pd.DataFrame(rows)


def matched_day_night(intervals,config,working_days_only=False):
    """Compare ambient lux within March-derived lighting-power bands, month by month.

    Require both day and night support within a band. This is descriptive;
    neither shading nor occupant presence is controlled.
    """
    bins_rows,summary_rows=[],[]
    for (floor,zone),group in intervals.groupby(['floor','zone']):
        march=group.loc[group.month.eq('2019-03'),'light_kW'].dropna()
        edges=np.unique(march.quantile(np.linspace(0,1,config['matched_power_bins']+1)).to_numpy())
        # Hold March bands fixed so the sensitivity changes calendar mix, not calibration.
        if working_days_only:
            group=group.loc[group.day_type.eq('working day')]
        for month,g in group.groupby('month'):
            n_bins=0
            if len(edges)>=3 and g.has_lux_sensor.iloc[0]:
                g=g.loc[g.light_kW.notna()&g.lux.notna()].copy()
                g['period']=np.select([g.hour.between(8,17),g.hour.ge(20)|g.hour.lt(6)],['day','night'],default='twilight')
                g['band']=pd.cut(g.light_kW,edges,include_lowest=True)
                for band,b in g.groupby('band',observed=True):
                    day=b.loc[b.period.eq('day')]; night=b.loc[b.period.eq('night')]
                    if min(len(day),len(night))>=config['minimum_matched_bin_count']:
                        n_bins+=1
                        bins_rows.append(dict(floor=floor,zone=zone,month=month,power_band=str(band),
                            day_n=len(day),night_n=len(night),day_median_lux=day.lux.median(),night_median_lux=night.lux.median(),
                            day_minus_night_lux=day.lux.median()-night.lux.median(),
                            day_mean_light_kW=day.light_kW.mean(),night_mean_light_kW=night.light_kW.mean()))
            selected=[r for r in bins_rows if r['floor']==floor and r['zone']==zone and r['month']==month]
            differences=[r['day_minus_night_lux'] for r in selected]
            summary_rows.append(dict(floor=floor,zone=zone,month=month,matched_power_bands=n_bins,
                                     median_matched_day_minus_night_lux=np.median(differences) if differences else np.nan,
                                     status='descriptive paired power bands' if n_bins else 'insufficient matched day/night evidence'))
    cols=['floor','zone','month','power_band','day_n','night_n','day_median_lux','night_median_lux','day_minus_night_lux','day_mean_light_kW','night_mean_light_kW']
    return pd.DataFrame(bins_rows,columns=cols),pd.DataFrame(summary_rows)


def run_assessment():
    intervals,manifest=load_inputs(); config=manifest['settings']
    thresholds=calibrate_activity(intervals,config)
    april=assess_activity(intervals,thresholds,config['primary_activity_persistence_minutes'])
    schedule=schedule_table(april)
    coverage=coverage_table(intervals)
    matched_bands,matched_summary=matched_day_night(intervals,config)
    # Inferred closures/weekends can confound day/night comparisons; retain the original and show a sensitivity.
    _, working_summary = matched_day_night(intervals,config,working_days_only=True)
    baseline=pd.read_csv(ROOT/'baseline'/'outputs'/'lighting_zone_april_baseline.csv')
    # Quality warnings are audit metadata, not aggregated measurements.
    quality=pd.read_csv(ROOT/config['quality_reports']/'data_quality.csv')
    quality_notes=quality.loc[quality.unit.eq('lux')].groupby(['floor','zone']).note.apply(lambda x:'; '.join(x.dropna().unique()))
    opportunities=[]
    for (floor,zone),g in april.groupby(['floor','zone']):
        b=baseline.loc[baseline.floor.eq(floor)&baseline.zone.eq(zone)].iloc[0]
        light_energy=g.light_kW.sum(min_count=1)/4
        outside=~g.is_operating_hour
        outside_energy=g.loc[outside,'light_kW'].sum(min_count=1)/4
        closure=g.schedule_segment.eq('inferred closure')
        operating_nonclosure=g.is_operating_hour&~closure
        valid=g.light_kW.notna(); paired=g.light_kW.notna()&g.lux.notna()
        correlation=g.loc[paired,['light_kW','lux']].corr(method='spearman').iloc[0,1] if paired.sum()>=20 else np.nan
        flags=thresholds.loc[thresholds.floor.eq(floor)&thresholds.zone.eq(zone)]
        supported=flags.status.eq('supported').all()
        candidate_hours=g.activity_mismatch.sum()/4 if supported else np.nan
        power_cov=100*g.total_kW.notna().mean(); light_cov=100*valid.mean(); lux_cov=100*g.lux.notna().mean()
        sensor=bool(g.has_lux_sensor.iloc[0])
        if light_cov<80 or power_cov<80:
            evidence='incomplete power evidence'
            action='Restore/check metering before comparing lighting opportunities'
        elif not sensor:
            evidence='power only; no lux sensor'
            action='Audit schedules; install/validate task-plane measurement before comfort claims'
        elif lux_cov<80:
            evidence='partial ambient-light evidence'
            action='Audit schedules and investigate sensor outages'
        else:
            evidence='paired power/ambient evidence; comfort unvalidated'
            action='Audit schedules and validate task-plane lighting; no approved dimming fraction'
        row=dict(floor=floor,zone=zone,april_valid_period_lighting_kWh=light_energy,
                 outside_assumed_hours_lighting_kWh=outside_energy,
                 outside_assumed_hours_energy_share_pct=100*outside_energy/light_energy if light_energy>0 else np.nan,
                 weekday_outside_lighting_kWh=g.loc[g.schedule_segment.eq('weekday outside hours'),'light_kW'].sum(min_count=1)/4,
                 weekend_lighting_kWh=g.loc[g.schedule_segment.eq('weekend'),'light_kW'].sum(min_count=1)/4,
                 inferred_closure_lighting_kWh=g.loc[closure,'light_kW'].sum(min_count=1)/4,
                 normal_operating_mean_lighting_kW=g.loc[operating_nonclosure,'light_kW'].mean(),
                 outside_hours_mean_lighting_kW=g.loc[outside,'light_kW'].mean(),
                 has_lux_sensor=sensor,april_all_hours_total_coverage_pct=power_cov,
                 april_all_hours_light_coverage_pct=light_cov,april_all_hours_lux_coverage_pct=lux_cov,
                 april_clean_power_complete_pct=100*g.power_complete.mean(),
                 april_clean_paired_complete_pct=100*g.paired_complete.mean(),
                 ambient_lux_missing_at_daytime_zone_peak=pd.isna(b.ambient_lux_at_peak),
                 april_power_lux_spearman=correlation,paired_power_lux_intervals=int(paired.sum()),
                 activity_calibration_supported=bool(supported),activity_mismatch_hours=candidate_hours,
                 unknown_activity_hours=(~g.activity_known).sum()/4,
                 lighting_baseline_status=flags.loc[flags.measure.eq('light'),'status'].iloc[0],
                 plug_baseline_status=flags.loc[flags.measure.eq('plug'),'status'].iloc[0],
                 evidence_strength=evidence,suggested_investigation=action,
                 limitations='Outside-hours use is not confirmed waste; plug activity is not occupancy; ambient lux is not task-plane comfort.',
                 sensor_context_warning=quality_notes.get((floor,zone),'No ambient lux sensor in source schema.'))
        for col in ['march_p95_trigger_kW','march_coverage_pct','april_coverage_pct','april_peak_time','april_peak_total_kW','lighting_kW_at_peak','lighting_share_at_peak_pct','ambient_lux_at_peak','april_max_ambient_lux']:
            row[col]=b[col]
        if supported and candidate_hours>0:
            row['suggested_investigation']='Review lighting-high/low-plug episodes against actual attendance; '+action
        opportunities.append(row)
    opportunities=pd.DataFrame(opportunities).sort_values('outside_assumed_hours_lighting_kWh',ascending=False,na_position='last')
    opportunities.insert(0,'schedule_audit_order',range(1,len(opportunities)+1))
    # A descriptive order by observed outside-hours energy is not a validated savings ranking.
    sensitivity=[]
    for minutes in config['activity_persistence_minutes']:
        for shift in [-.1,0,.1]:
            activity=assess_activity(intervals,thresholds,minutes,shift)
            grouped=activity.groupby(['floor','zone']).agg(candidate_intervals=('activity_mismatch','sum'),known_intervals=('activity_known','sum'))
            grouped['candidate_hours']=grouped.candidate_intervals/4
            supported=thresholds.groupby(['floor','zone']).status.apply(lambda s:s.eq('supported').all())
            grouped.loc[~supported,'candidate_hours']=np.nan
            grouped['persistence_minutes']=minutes; grouped['boundary_shift_fraction']=shift
            sensitivity.append(grouped.reset_index())
    sensitivity=pd.concat(sensitivity,ignore_index=True)
    out=HERE/'outputs'
    for filename,table in [('lighting_opportunities',opportunities),('lighting_schedule',schedule),('lighting_coverage',coverage),
                           ('lighting_activity_thresholds',thresholds),('lighting_activity_sensitivity',sensitivity),
                           ('lighting_activity_intervals',april),('lighting_matched_lux_bands',matched_bands),('lighting_matched_lux_summary',matched_summary),('lighting_matched_lux_working_days',working_summary)]:
        table.to_csv(out/(filename+'.csv'),index=False)
    from prepare_inputs import sha256
    receipt={'shared_input_manifest': 'run_manifest.json',
             'analysis_source_sha256': sha256(Path(__file__)),
             'activity_source_sha256': sha256(HERE/'activity_states.py'),
             'scope': 'Descriptive lighting assessment; no reduction scenarios'}
    (out/'assessment_manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return dict(intervals=intervals,april=april,opportunities=opportunities,schedule=schedule,coverage=coverage,
                thresholds=thresholds,sensitivity=sensitivity,matched_bands=matched_bands,
                matched_summary=matched_summary,working_day_matched_summary=working_summary,manifest=manifest,output=out)


def plot_profiles(results):
    data=results['april'].query('floor == 2')
    g=data.loc[data.day_type.eq('working day')].groupby(['zone','hour'])[['total_kW','light_kW']].mean()
    fig,axes=plt.subplots(2,2,figsize=(12,7),layout='constrained')
    for zone,ax in zip(range(1,5),axes.flat):
        profile=g.loc[zone]
        ax.axvspan(8,18,color='#eeeeee',label='Assumed operating window')
        ax.plot(profile.index,profile.total_kW,color='#2878b5',label='Recorded total')
        ax.plot(profile.index,profile.light_kW,color='#c56624',label='Lighting')
        ax.set(title=f'F2 Z{zone}: average working-day profile',xlabel='Bangkok hour',ylabel='Mean demand (kW)',xlim=(0,23),ylim=(0,None))
        ax.set_xticks([0,4,8,12,16,20,23]); ax.legend(fontsize=8)
    fig.savefig(results['output']/'lighting_assessment_figures'/'floor2_demand_profiles.png',dpi=140)
    plt.show()


def plot_schedule(results):
    data=results['schedule'].query('floor == 2').pivot(index='zone',columns='schedule_segment',values='valid_period_lighting_kWh')
    order=['weekday operating','weekday outside hours','weekend','inferred closure']
    data=data.reindex(columns=order)
    fig,ax=plt.subplots(figsize=(11,4),layout='constrained')
    data.plot.barh(stacked=True,ax=ax,color=['#2878b5','#c56624','#809367','#aaaaaa'])
    ax.set(title='Floor 2: April lighting energy by schedule context',xlabel='Lighting energy over valid intervals (kWh)',ylabel='Zone')
    ax.legend(fontsize=8,loc='upper left',bbox_to_anchor=(1,1))
    fig.savefig(results['output']/'lighting_assessment_figures'/'floor2_schedule_energy.png',dpi=140)
    plt.show()


def plot_lux(results):
    data=results['intervals'].query('floor == 2')
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for zone,ax in zip(range(1,5),axes.flat):
        for month,marker in [('2019-03','o'),('2019-04','x')]:
            for day,color in [(True,'#c56624'),(False,'#2878b5')]:
                g=data.loc[data.zone.eq(zone)&data.month.eq(month)&data.lux.notna()&data.light_kW.notna()]
                g=g.loc[g.hour.between(8,17)] if day else g.loc[g.hour.ge(20)|g.hour.lt(6)]
                ax.scatter(g.light_kW,g.lux,s=7,alpha=.25,color=color,marker=marker,label=f'{"Mar" if month.endswith("03") else "Apr"} {"day" if day else "night"}')
        ax.set(title=f'F2 Z{zone}: lighting power versus ambient lux',xlabel='Lighting (kW)',ylabel='Ceiling ambient lux')
        ax.legend(fontsize=8)
    fig.savefig(results['output']/'lighting_assessment_figures'/'floor2_power_lux.png',dpi=140)
    plt.show()
    fig,axes=plt.subplots(2,2,figsize=(12,7),layout='constrained')
    for zone,ax in zip(range(1,5),axes.flat):
        g=data.loc[data.zone.eq(zone)]
        values=[];labels=[]
        for month in ['2019-03','2019-04']:
            for daytime in [True,False]:
                part=g.loc[g.month.eq(month)]
                part=part.loc[part.hour.between(8,17)] if daytime else part.loc[part.hour.ge(20)|part.hour.lt(6)]
                values.append(part.lux.dropna().to_numpy()); labels.append(f'{"Mar" if month.endswith("03") else "Apr"} {"day" if daytime else "night"}')
        ax.boxplot(values,showfliers=False)
        ax.set_xticks(range(1,5),labels)
        ax.set(title=f'F2 Z{zone}: ambient lux distribution',ylabel='Ceiling ambient lux')
    fig.savefig(results['output']/'lighting_assessment_figures'/'floor2_lux_distributions.png',dpi=140)
    plt.show()


def plot_activity(results):
    data=results['opportunities'].query('floor == 2').sort_values('zone')
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    for ax,column,title,color in [
        (axes[0],'activity_mismatch_hours','Lighting high / sustained low plug activity','#c56624'),
        (axes[1],'unknown_activity_hours','Time with insufficient activity evidence','#aaaaaa')]:
        ax.barh(data.zone,data[column],color=color)
        ax.set_yticks([1,2,3,4])
        ax.set_ylim(.5,4.5)
        maximum=max(data[column].max(),1)
        for row in data.itertuples():
            value=getattr(row,column)
            label='Unknown' if pd.isna(value) else f'{value:.2f} h'
            ax.text(0 if pd.isna(value) else value, row.zone, '  '+label,va='center',fontsize=9)
        ax.set(title=title,xlabel='April hours',ylabel='Floor 2 zone',xlim=(0,maximum*1.3))
    fig.suptitle('Occupancy-related audit evidence; no measured vacancy labels')
    fig.savefig(results['output']/'lighting_assessment_figures'/'floor2_activity_evidence.png',dpi=140)
    plt.show()


def write_findings(results):
    f2=results['opportunities'].query('floor == 2').sort_values('zone')
    lines=['# Lighting assessment findings','',
           'This assessment addresses lighting contribution, schedules, power–lux patterns and occupancy-related evidence. Conditional reduction simulations and coincident peak impacts are handled in the reduction-scenario analysis.','',
           '## Floor 2 findings','',
           '| Zone | Lighting at daytime peak (%) | Outside-hours lighting (kWh) | Outside-hours energy share (%) | Activity mismatch (h) | Unknown activity (h) |',
           '|---|---:|---:|---:|---:|---:|']
    for r in f2.itertuples():
        fmt=lambda x:'Unknown' if pd.isna(x) else f'{x:.2f}'
        lines.append(f'| {r.zone} | {fmt(r.lighting_share_at_peak_pct)} | {fmt(r.outside_assumed_hours_lighting_kWh)} | {fmt(r.outside_assumed_hours_energy_share_pct)} | {fmt(r.activity_mismatch_hours)} | {fmt(r.unknown_activity_hours)} |')
    z1=f2.loc[f2.zone.eq(1)].iloc[0]
    z3=f2.loc[f2.zone.eq(3)].iloc[0]
    lines += ['', f'Zone 1 has {z1.lighting_kW_at_peak:.2f} kW of lighting at its daytime demand peak, compared with {z3.lighting_kW_at_peak:.2f} kW in Zone 3. Zone 3’s higher lighting share ({z3.lighting_share_at_peak_pct:.2f}%) therefore does not imply a larger absolute peak opportunity.',
              '', f'Zone 3 uses {z3.outside_assumed_hours_lighting_kWh:.2f} kWh outside assumed hours ({z3.outside_assumed_hours_energy_share_pct:.2f}% of recorded lighting energy). Its stricter activity rule flags {z3.activity_mismatch_hours:.2f} hours. Prioritise a circuit-use and attendance audit; do not label all outside-hours energy as avoidable.',
              '', 'Matched-power lux estimates and support counts are exported by zone/month in `outputs/lighting_matched_lux_summary.csv`; band counts and residual power differences are inspectable in `outputs/lighting_matched_lux_bands.csv`.']
    lines+=['','Outside-hours use is measured over available lighting intervals, not estimated avoidable use. The schedule assumes weekdays 08:00–18:00; research/cleaning/security use may be legitimate. Inferred closures are energy-derived context, not attendance labels.','',
            '## Interpretation and recommendations','',
            '- Compare lighting at each zone’s own peak with actual scheduling evidence. Lighting share is an accounting contribution, not an achievable reduction.','- Floor 2 Zones 1 and 2 show no sustained lighting-high/low-plug mismatch under the primary rule. Retain their existing lighting until attendance and task needs justify changes.','- Floor 2 Zone 3 has a small mismatch signal. Validate its plug standby pattern and circulation/task function before calling it vacancy or waste.','- Floor 2 Zone 4 has almost constant plug load, so its activity assessment stays unknown. Obtain independent attendance evidence rather than lowering a threshold to force a result.','- Compare daytime/nighttime lux only at supported similar-power bands. Daylight, blinds and zone geometry confound the association; no lighting-off counterfactual is observed.','- Validate occupied task-plane lux and occupant feedback before a dimming trial. Ceiling ambient lux and the illustrative 500-lux reference do not establish comfort.','',
            '## Handoff to reduction scenarios','',
            'Use `outputs/zone_15min.csv`, `outputs/lighting_opportunities.csv`, `config.json` and `outputs/run_manifest.json`. The original baseline remains unchanged and the adapter reconciles its April daytime peaks for all 33 zones.','',
            'The shared table retains baseline-compatible values and adds `power_complete`/`paired_complete` for strict intervals. Complete after cleaning may include interpolation. Repair-free flags require the upstream interpolation audit and are not inferred from non-null counts. Missing comfort evidence must not be treated as automatic valid zero savings. Scenario percentages, peak shifts, sensitivity and building coincidence remain part of the reduction-scenario analysis.','',
            '## Evidence boundaries','',
            'The Thai thermal-comfort/glare study motivates local comfort surveys and separate thermal/visual assessment; it does not validate occupancy inference from lux. Its DGP scale cannot replace a lux threshold. The study’s seven Bangkok office buildings and window-facing occupants are not ground truth for Chamchuri 5.','',
            'Sources: [CU-BEMS](https://doi.org/10.1038/s41597-020-00582-3), [Chaloeytoy & Ichinose (2020)](https://digital.car.chula.ac.th/nakhara/vol19/iss1/6/), supplied `README_analytics.txt`, original lighting baseline and the generated source manifest.']
    (HERE/'lighting_findings.md').write_text('\n'.join(lines)+'\n')
