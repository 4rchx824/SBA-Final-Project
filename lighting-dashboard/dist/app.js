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
const supported=r=>r.reported_peak_reduction_kW!==null;
const statusText=r=>supported(r)?'Reportable · conditional':r.status;
function scenarioRows(){return scoped(D.scenarios.filter(r=>r.schedule_id===$('schedule').value&&r.policy===$('policy').value&&r.lux_quantile===Number($('quantile').value)&&r.reduction_cap===Number($('cap').value)&&r.period_coverage_gate===Number($('gate').value)));}
function overview(){
 const rows=scoped(D.opportunities),ps=scoped(primary),energy=sum(rows,'april_valid_period_lighting_kWh'),outside=sum(rows,'outside_assumed_hours_lighting_kWh'),count=ps.filter(supported).length;
 const metrics=[['Lighting energy',fmt(energy/1000,2),'MWh','Observed valid periods · all hours'],['Outside assumed hours',energy?fmt(outside/energy*100):'—','%','Schedule exposure, not proven waste'],['Reportable zones',`${count}<small>/ ${rows.length}</small>`,'','Primary scenario · coverage gates applied'],['Investigation time',fmt(sum(ps,'reported_investigation_hours'),2),'zone-hours','Primary case · overlapping zones may coincide']];
 $('metrics').innerHTML=metrics.map(([label,value,unit,note])=>`<div class="metric"><div class="metric-label">${label}<span>↗</span></div><div class="metric-value">${value}<small>${unit}</small></div><div class="metric-note">${note}</div></div>`).join('');
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
 $('zone-list').innerHTML=rows.length?rows.map(r=>{const p=primary.find(p=>key(p)===key(r));return`<button class="zone-option ${key(r)===selected?'selected':''}" data-zone="${key(r)}" aria-pressed="${key(r)===selected}"><span><span class="zone-name">Floor ${r.floor} / Zone ${r.zone}</span><small><i class="status-dot ${supported(p)?'':'withheld'}"></i>${supported(p)?'Reportable scenario':'Limited scenario evidence'}</small></span><span class="zone-energy">${fmt(r.april_valid_period_lighting_kWh/1000,2)} MWh<small>${fmt(r.outside_assumed_hours_energy_share_pct,0)}% outside hours</small></span></button>`;}).join(''):'<div class="empty">No zones match this search.</div>';
 $('list-count').textContent=`${rows.length} zones · valid-period lighting energy`;
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
 $('zone-detail').innerHTML=`<div class="detail-title"><div><span class="eyebrow">ZONE SPOTLIGHT</span><h2>Floor ${r.floor}, Zone ${r.zone}</h2></div><span class="pill">${esc(r.evidence_strength)}</span></div><div class="detail-metrics"><div><span>Lighting at original zone peak</span><strong>${fmt(r.lighting_share_at_peak_pct)}<small> %</small></strong></div><div><span>April all-hours power coverage</span><strong>${fmt(r.april_all_hours_total_coverage_pct)}<small> %</small></strong></div><div><span>March P95 lux trigger · primary</span><strong>${fmt(p.lux_trigger_lux)}<small> lux</small></strong></div></div><div class="profile-heading"><span>Mean hourly demand <span class="muted">· kW</span></span><div class="legend"><span><i class="swatch purple"></i>Total demand</span><span><i class="swatch mint"></i>Lighting</span></div></div>${profile(r)}<p class="chart-caption">April · all days · mean of available 15-minute readings. Shading marks 08–17h. Original peak share uses the baseline 08–18h window.</p><div class="detail-advice" style="margin-top:13px"><strong>Investigation direction</strong><br>${esc(r.suggested_investigation)}.</div>`;
}
function renderScenarios(){
 const rows=scenarioRows().sort((a,b)=>a.floor-b.floor||a.zone-b.zone),valid=rows.filter(supported);
 $('scenario-stats').innerHTML=`<div><strong>${valid.length}<small> / ${rows.length} zones</small></strong><span>Reportable under selected assumptions</span></div><div><strong>${valid.length?fmt(sum(valid,'reported_investigation_hours'),2):'—'}<small> zone-hours</small></strong><span>Candidate time · not building elapsed time</span></div><div><strong>${valid.length?fmt(sum(valid,'reported_energy_reduction_kWh'),2):'—'}<small> kWh</small></strong><span>Sum over reportable zones · conditional energy change</span></div>`;
 $('scenario-table').innerHTML=rows.map(r=>`<tr><td>${zoneName(r)}</td><td><span class="status-label ${supported(r)?'':'withheld'}">${esc(statusText(r))}</span></td><td>${fmt(r.reported_investigation_hours,2)}</td><td>${fmt(r.observed_baseline_peak_kW,3)}</td><td>${supported(r)?fmt(r.observed_scenario_peak_kW,3):'—'}</td><td class="${r.reported_peak_reduction_kW>0?'positive':''}">${fmt(r.reported_peak_reduction_kW,3)}</td><td>${fmt(r.reported_energy_reduction_kWh,2)}</td><td>${fmt(r.april_coverage_pct)}%</td></tr>`).join('');
}
function quality(){
 const groups=new Map();primary.forEach(r=>{const label=supported(r)?'Reportable · comfort unvalidated':r.status;groups.set(label,(groups.get(label)||0)+1);});
 $('quality-bars').innerHTML=[...groups].sort((a,b)=>b[1]-a[1]).map(([s,n])=>`<div class="quality-row"><span>${esc(s)}</span><strong>${n}</strong><div class="quality-track"><i class="${s.startsWith('Reportable')?'good':''}" style="width:${n/33*100}%"></i></div></div>`).join('');
 $('audit-details').textContent=`${fmt(D.meta.audit.intervals_checked,0)} intervals · ${fmt(D.meta.audit.zone_scenario_combinations,0)} zone/scenario combinations · source hashes verified at export`;
 $('provenance').innerHTML=`<strong>Verified snapshot, not a live feed</strong><p>Exported ${esc(new Date(D.meta.generated_at).toLocaleString())}. Calibration: ${D.meta.calibration}. Evaluation: ${D.meta.evaluation}. Analysis uses Bangkok local timestamps.</p><p>Sources: scenario_sensitivity.csv, lighting_opportunities.csv, lighting_schedule.csv, lighting_coverage.csv, coincident_scenario_impact.csv and zone_15min.csv. The dashboard embeds a snapshot generated only after the repository freshness check passed.</p><p>Complete cleaned intervals may include interpolation. The common-minute sensitivity requires at least 12 of 15 shared valid minutes. Neither policy establishes raw observed-only support. All scenario cutoffs use March telemetry; no absolute comfort target is assumed.</p><p>Audit checks: ${D.meta.audit.checks.map(esc).join(', ')}.</p>`;
}
$('floor').addEventListener('change',()=>{overview();renderList();renderScenarios();});
['search','sort'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',renderList));
['schedule','quantile','cap','policy','gate'].forEach(id=>$(id).addEventListener('change',renderScenarios));
$('reset').addEventListener('click',()=>{for(const [id,v]of Object.entries({schedule:'primary',quantile:'0.95',cap:'0.2',policy:'strict',gate:'0.8'}))$(id).value=v;renderScenarios();});
$('provenance-toggle').addEventListener('click',()=>{const open=$('provenance').hidden;$('provenance').hidden=!open;$('provenance-toggle').setAttribute('aria-expanded',open);$('provenance-toggle').textContent=open?'Hide provenance −':'View provenance +';});
const observer=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('active',a.hash===`#${e.target.id}`));}});},{rootMargin:'-10% 0px -65% 0px'});document.querySelectorAll('main section').forEach(s=>observer.observe(s));
overview();renderList();renderScenarios();quality();
