'use strict';
const D=window.LIGHTING_DATA;
const $=id=>document.getElementById(id);
const fmt=(v,n=1)=>v==null?'—':Number(v).toLocaleString('en-US',{maximumFractionDigits:n,minimumFractionDigits:n});
const sum=(rows,key)=>rows.reduce((a,r)=>a+(r[key]??0),0);
const key=r=>`${r.floor}-${r.zone}`;
const zoneName=r=>`F${r.floor} · Z${r.zone}`;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let selected='2-2';
const scoped=rows=>rows.filter(r=>$('floor').value==='all'||r.floor===Number($('floor').value));
const primary=D.scenarios.filter(r=>r.scenario_id==='primary_strict_coverage0.8_q0.95_cap0.2');
const supported=r=>r!=null&&Number.isFinite(r.reported_peak_reduction_kW);
const statusNames={'no lux sensor':'No lux sensor','insufficient calibration':'Not enough March demand data','insufficient March lux calibration':'March lux reference unsupported','insufficient April power coverage':'Not enough April demand data','insufficient April paired coverage':'Not enough paired April data','no valid lux':'No usable April lux readings'};
const statusText=r=>supported(r)?'Enough data · conditional':(statusNames[r.status]??r.status);
// Compare the same primary policy/window across percentiles, independent of Scenario lab controls.
const investigationChecks=r=>[.9,.95,.975].map(q=>D.scenarios.find(x=>key(x)===key(r)&&x.schedule_id==='primary'&&x.policy==='strict'&&x.period_coverage_gate===.8&&x.reduction_cap===.2&&x.lux_quantile===q)?.reported_investigation_hours??null);
function scenarioRows(){return scoped(D.scenarios.filter(r=>r.schedule_id===$('schedule').value&&r.policy===$('policy').value&&r.lux_quantile===Number($('quantile').value)&&r.reduction_cap===Number($('cap').value)&&r.period_coverage_gate===Number($('gate').value)));}
function overview(){
 const rows=scoped(D.opportunities),ps=scoped(primary),energy=sum(rows,'april_valid_period_lighting_kWh'),outside=sum(rows,'outside_assumed_hours_lighting_kWh'),count=ps.filter(supported).length;
 const metrics=[['Lighting energy',fmt(energy/1000,2),'MWh','April · available readings'],['Outside office hours',energy?fmt(outside/energy*100):'—','%','Assumed weekdays 08–17h · holidays included'],['Zones with enough data',`${count}<small>/ ${rows.length}</small>`,'','Primary case · data checks passed'],['Flagged time',count?fmt(sum(ps,'reported_investigation_hours'),2):'—','zone-hours',count?'Primary case · zones may overlap in time':'Withheld: no zones pass the data checks']];
 $('metrics').innerHTML=metrics.map(([label,value,unit,note])=>`<div class="metric"><div class="metric-label">${label}</div><div class="metric-value">${value}<small>${unit}</small></div><div class="metric-note">${note}</div></div>`).join('');
 const recurring=ps.filter(supported).map(r=>({r,hours:investigationChecks(r)})).filter(x=>x.hours.every(h=>h!=null&&h>0)).sort((a,b)=>b.hours[2]-a.hours[2]||b.hours[1]-a.hours[1]);
 const lead=recurring[0];
 const insight=lead?`<h2>Review recurring signals.</h2><p>${zoneName(lead.r)} has ${fmt(lead.hours[1],2)} flagged hours at P95 and ${fmt(lead.hours[2],2)} at the stricter P97.5 cutoff. Check these periods against schedules and plug activity before proposing controls.</p>`:count?'<h2>No recurring signal across all cutoffs.</h2><p>No zone in this scope is flagged under every tested lux percentile. Treat isolated flags cautiously; this does not rule out physical savings opportunities.</p>':'<h2>Evidence is missing.</h2><p>No zone in this scope passes the primary scenario’s data checks. Resolve the missing evidence before estimating reductions; unavailable results are not zero savings.</p>';
 $('overview-insight').innerHTML=`<div class="eyebrow">INVESTIGATION PRIORITY · PRIMARY CASE</div>${insight}<div class="insight-stat"><span>${count?`${recurring.length}<span class="muted"> / ${count}</span>`:'—'}</span><small>${count?'eligible zones flagged at<br>all three lux cutoffs':'No comparable zone results<br>in this scope'}</small></div><a href="#explorer" class="text-link">Inspect zone evidence <span>↗</span></a>`;
 const floors=[...new Set(rows.map(r=>r.floor))].sort((a,b)=>a-b);
 const totals=floors.map(f=>{const s=D.schedules.filter(r=>r.floor===f);return{floor:f,operating:sum(s.filter(r=>r.schedule_segment==='weekday operating'),'valid_period_lighting_kWh'),transition:sum(s.filter(r=>r.schedule_segment==='weekday transition'),'valid_period_lighting_kWh'),other:sum(s.filter(r=>!['weekday operating','weekday transition'].includes(r.schedule_segment)),'valid_period_lighting_kWh')};});
 const maximum=Math.max(...totals.map(r=>r.operating+r.transition+r.other),1);
 $('energy-chart').innerHTML=totals.map(r=>`<div class="energy-row"><span>Floor ${r.floor}</span><div class="energy-track" role="img" aria-label="Floor ${r.floor}: operating ${fmt(r.operating)} kWh, transition ${fmt(r.transition)} kWh, other hours ${fmt(r.other)} kWh">${[['operating','mint'],['transition','purple'],['other','amber']].map(([k,c])=>`<i class="${c}" style="width:${r[k]/maximum*100}%" title="${k}: ${fmt(r[k])} kWh"></i>`).join('')}</div><span>${fmt((r.operating+r.transition+r.other)/1000,2)} MWh</span></div>`).join('');
}
function renderList(){
 const search=$('search').value.toLowerCase().replace(/[^a-z0-9]/g,'');
 let rows=scoped(D.opportunities).filter(r=>!search||`f${r.floor}z${r.zone}`.includes(search)||`floor${r.floor}zone${r.zone}`.includes(search));
 rows.sort((a,b)=>$('sort').value==='zone'?a.floor-b.floor||a.zone-b.zone:$('sort').value==='outside'?(b.outside_assumed_hours_energy_share_pct??-1)-(a.outside_assumed_hours_energy_share_pct??-1):b.april_valid_period_lighting_kWh-a.april_valid_period_lighting_kWh);
 if(rows.length&&!rows.some(r=>key(r)===selected))selected=key(rows[0]);
 $('zone-list').innerHTML=rows.length?rows.map(r=>{const p=primary.find(p=>key(p)===key(r));return`<button class="zone-option ${key(r)===selected?'selected':''}" data-zone="${key(r)}" aria-pressed="${key(r)===selected}"><span><span class="zone-name">Floor ${r.floor} / Zone ${r.zone}</span><small><i class="status-dot ${supported(p)?'':'withheld'}"></i>${supported(p)?'Enough data for scenarios':'Scenario result withheld'}</small></span><span class="zone-energy">${fmt(r.april_valid_period_lighting_kWh/1000,2)} MWh<small>${fmt(r.outside_assumed_hours_energy_share_pct,0)}% outside hours</small></span></button>`;}).join(''):'<div class="empty">No zones match this search.</div>';
 $('list-count').textContent=`${rows.length} ${rows.length===1?'zone':'zones'} · recorded-period lighting energy`;
 $('zone-list').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{selected=b.dataset.zone;renderList();}));
 renderDetail(rows.length?D.opportunities.find(r=>key(r)===selected):null);
}
function profile(r){
 const rows=D.profiles.filter(p=>key(p)===key(r)),w=620,h=165,left=36,right=12,top=13,bottom=27;
 const max=Math.max(...rows.flatMap(p=>[p.total_kW??0,p.light_kW??0]),.1)*1.1;
 const x=hour=>left+hour/23*(w-left-right),y=value=>h-bottom-value/max*(h-top-bottom);
 let content='';for(let i=0;i<=3;i++){const v=max*i/3;content+=`<line x1="${left}" x2="${w-right}" y1="${y(v)}" y2="${y(v)}" stroke="#edf1ec"/><text x="${left-7}" y="${y(v)+3}" text-anchor="end">${fmt(v,0)}</text>`;}
 [0,6,12,18,23].forEach(hour=>content+=`<text x="${x(hour)}" y="${h-6}" text-anchor="middle">${String(hour).padStart(2,'0')}:00</text>`);
 content+=`<rect x="${x(8)}" y="${top}" width="${x(17)-x(8)}" height="${h-top-bottom}" fill="#e8efe6" opacity=".35"/>`;
 for(const [field,color]of[['total_kW','#b4b2c7'],['light_kW','#6aab8e']]){let path='',gap=true;rows.forEach(p=>{if(p[field]==null){gap=true;return;}path+=`${gap?'M':'L'}${x(p.hour).toFixed(2)},${y(p[field]).toFixed(2)} `;gap=false;});content+=`<path d="${path}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round"/>`;}
 return`<svg class="profile-chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="April mean hourly total and lighting demand for Floor ${r.floor} Zone ${r.zone}, in kilowatts"><title>Mean hourly demand; observed valid intervals, not a typical-day simulation</title>${content}</svg>`;
}
function renderDetail(r){
 if(!r){$('zone-detail').innerHTML='<div class="empty">Choose a different search or floor to inspect a zone.</div>';return;}
 const p=primary.find(p=>key(p)===key(r));
 const checks=investigationChecks(r),complete=checks.every(h=>h!=null),recurring=complete&&checks.every(h=>h>0);
 const evidence=!supported(p)?`${statusText(p)}. Improve the evidence before proposing a reduction.`:!complete?'Some percentile comparisons are withheld; robustness cannot be established.':recurring?`Flagged time remains positive at all three cutoffs: ${fmt(checks[0],2)} / ${fmt(checks[1],2)} / ${fmt(checks[2],2)} hours at P90 / P95 / P97.5. Review the flagged periods against schedules and plug activity.`:checks.every(h=>h===0)?'No joint demand/lux flags under these three cutoffs. This does not establish no activity or no physical savings opportunity.':`The signal depends on the lux cutoff: ${fmt(checks[0],2)} / ${fmt(checks[1],2)} / ${fmt(checks[2],2)} hours at P90 / P95 / P97.5. Verify isolated periods before prioritising controls.`;
 $('zone-detail').innerHTML=`<div class="detail-title"><div><span class="eyebrow">ZONE SPOTLIGHT</span><h2>Floor ${r.floor}, Zone ${r.zone}</h2></div><span class="pill">${esc(statusText(p))}</span></div><div class="detail-metrics"><div><span>Lighting at original zone peak</span><strong>${fmt(r.lighting_share_at_peak_pct)}<small> %</small></strong></div><div><span>April all-hours power coverage</span><strong>${fmt(r.april_all_hours_total_coverage_pct)}<small> %</small></strong></div><div><span>March P95 lux trigger · primary</span><strong>${fmt(p.lux_calibration_supported?p.lux_trigger_lux:null)}<small> lux</small></strong></div></div><div class="profile-heading"><span>Mean hourly demand <span class="muted">· kW</span></span><div class="legend"><span><i class="swatch purple"></i>Total demand</span><span><i class="swatch mint"></i>Lighting</span></div></div>${profile(r)}<p class="chart-caption">April · all days · mean of available 15-minute readings. Shading marks 08–17h. Original peak share uses the baseline 08–18h window.</p><div class="detail-advice" style="margin-top:13px"><strong>What to investigate</strong><p>${esc(evidence)}</p><p>Ambient lux and plug activity cannot confirm vacancy or comfortable lighting. No dimming setting is approved by this analysis.</p></div>`;
}
function renderScenarios(){
 const rows=scenarioRows().sort((a,b)=>a.floor-b.floor||a.zone-b.zone),valid=rows.filter(supported);
 const flagged=valid.filter(r=>r.reported_investigation_hours>0).length,peakChanges=valid.filter(r=>r.reported_peak_reduction_kW>0).length;
 $('scenario-insight').textContent=!valid.length?'Results are withheld for this selection. Missing evidence cannot be interpreted as zero savings.':Number($('cap').value)===0?`${flagged} ${flagged===1?'zone has':'zones have'} flagged periods. This no-change case keeps those flags but sets all reductions to zero.`:`${flagged} of ${valid.length} eligible zones have flagged periods; ${peakChanges} ${peakChanges===1?'shows':'show'} a modeled zone-peak reduction. Lower energy can leave the monthly peak unchanged. Zone peak reductions are not a building-peak estimate.`;
 $('scenario-stats').innerHTML=`<div><strong>${valid.length}<small> / ${rows.length} zones</small></strong><span>Zones passing the selected data checks</span></div><div><strong>${valid.length?fmt(sum(valid,'reported_investigation_hours'),2):'—'}<small> zone-hours</small></strong><span>Flagged zone-hours · may overlap in time</span></div><div><strong>${valid.length?fmt(sum(valid,'reported_energy_reduction_kWh'),2):'—'}<small> kWh</small></strong><span>Modeled energy reduction · eligible zones only</span></div>`;
 $('scenario-table').innerHTML=rows.map(r=>`<tr><td>${zoneName(r)}</td><td><span class="status-label ${supported(r)?'':'withheld'}">${esc(statusText(r))}</span></td><td>${fmt(r.reported_investigation_hours,2)}</td><td>${fmt(r.observed_baseline_peak_kW,3)}</td><td>${supported(r)?fmt(r.observed_scenario_peak_kW,3):'—'}</td><td class="${r.reported_peak_reduction_kW>0?'positive':''}">${fmt(r.reported_peak_reduction_kW,3)}</td><td>${fmt(r.reported_energy_reduction_kWh,2)}</td><td>${fmt(r.april_coverage_pct)}%</td></tr>`).join('');
}
function quality(){
 const groups=new Map();primary.forEach(r=>{const label=supported(r)?'Enough data · comfort unverified':statusText(r);groups.set(label,(groups.get(label)||0)+1);});
 $('quality-bars').innerHTML=[...groups].sort((a,b)=>b[1]-a[1]).map(([s,n])=>`<div class="quality-row"><span>${esc(s)}</span><strong>${n}</strong><div class="quality-track"><i class="${s.startsWith('Enough data')?'good':''}" style="width:${n/33*100}%"></i></div></div>`).join('');
 $('audit-details').textContent=`${fmt(D.meta.audit.intervals_checked,0)} intervals · ${fmt(D.meta.audit.zone_scenario_combinations,0)} zone/scenario combinations · audited when exported`;
 $('provenance').innerHTML=`<strong>Audited snapshot, not live readings</strong><p>Exported ${esc(new Date(D.meta.generated_at).toLocaleString('en-GB',{timeZone:'Asia/Bangkok'}))} (Bangkok time). Calibration: ${D.meta.calibration}. Evaluation: ${D.meta.evaluation}. Analysis uses Bangkok local timestamps.</p><p>Sources: scenario_sensitivity.csv, lighting_opportunities.csv, lighting_schedule.csv, lighting_coverage.csv, coincident_scenario_impact.csv and zone_15min.csv. The dashboard embeds a snapshot generated only after the repository freshness check passed.</p><p>Complete cleaned intervals may include interpolation. The common-minute sensitivity requires at least 12 of 15 shared valid minutes. Neither policy establishes raw observed-only support. All scenario cutoffs use March telemetry; no absolute comfort target is assumed.</p><p>Audit checks: ${D.meta.audit.checks.map(esc).join(', ')}.</p>`;
}
$('floor').addEventListener('change',()=>{overview();renderList();renderScenarios();});
['search','sort'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',renderList));
['schedule','quantile','cap','policy','gate'].forEach(id=>$(id).addEventListener('change',renderScenarios));
$('reset').addEventListener('click',()=>{for(const [id,v]of Object.entries({schedule:'primary',quantile:'0.95',cap:'0.2',policy:'strict',gate:'0.8'}))$(id).value=v;renderScenarios();});
$('provenance-toggle').addEventListener('click',()=>{const open=$('provenance').hidden;$('provenance').hidden=!open;$('provenance-toggle').setAttribute('aria-expanded',open);$('provenance-toggle').textContent=open?'Hide provenance −':'View provenance +';});
const observer=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('active',a.hash===`#${e.target.id}`));}});},{rootMargin:'-10% 0px -65% 0px'});document.querySelectorAll('main section').forEach(s=>observer.observe(s));
overview();renderList();renderScenarios();quality();
