import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

// Exercise real rendering/filter handlers with a minimal DOM, without opening a browser.
const html=fs.readFileSync(new URL('dist/index.html',import.meta.url),'utf8');
const defaults={floor:'all',search:'',sort:'energy',schedule:'primary',quantile:'0.95',cap:'0.2',policy:'strict',gate:'0.8'};
const elements=new Map([...html.matchAll(/id="([^"]+)"/g)].map(([,id])=>[id,{value:defaults[id]??'',innerHTML:'',textContent:'',hidden:id==='provenance',handlers:{},addEventListener(event,fn){this.handlers[event]=fn;},querySelectorAll(){return[];},setAttribute(){}}]));
const context=vm.createContext({window:{},document:{getElementById:id=>{assert.ok(elements.has(id),`Unknown element: ${id}`);return elements.get(id);},querySelectorAll:()=>[],createElement:()=>({click(){}})},IntersectionObserver:class{observe(){}},URL:{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},Blob,setTimeout:fn=>fn()});
vm.runInContext(fs.readFileSync(new URL('dist/data.js',import.meta.url),'utf8'),context);
vm.runInContext(fs.readFileSync(new URL('dist/app.js',import.meta.url),'utf8'),context);
const run=s=>vm.runInContext(s,context);
assert.equal(run('scenarioRows().length'),33);
assert.equal(run('scenarioRows().filter(supported).length'),17);
assert.equal(run("sum(scenarioRows(),'reported_investigation_hours')"),19.25);
assert.ok(elements.get('zone-detail').innerHTML.includes('Floor 2, Zone 2'));
let cases=0;
for(const schedule of ['primary','extended','primary_holiday_excluded','extended_holiday_excluded'])for(const quantile of ['0.9','0.95','0.975'])for(const cap of ['0','0.05','0.1','0.2'])for(const policy of ['strict','common_minutes'])for(const gate of ['0.8','0.95']){
 for(const [id,value]of Object.entries({schedule,quantile,cap,policy,gate}))elements.get(id).value=value;
 elements.get('cap').handlers.change();
 assert.equal(run('scenarioRows().length'),33);
 assert.equal((elements.get('scenario-table').innerHTML.match(/<tr>/g)||[]).length,33);
 if(cap==='0')assert.equal(run("sum(scenarioRows(),'reported_peak_reduction_kW')"),0);
 cases++;
}
elements.get('reset').handlers.click();
elements.get('floor').value='2';elements.get('floor').handlers.change();
assert.equal(run('scenarioRows().length'),4);
assert.ok(run('scenarioRows().every(r=>r.floor===2)'));
elements.get('search').value='F2 Z2';elements.get('search').handlers.input();
assert.ok(elements.get('list-count').textContent.startsWith('1 zones'));
elements.get('search').value='no such zone';elements.get('search').handlers.input();
assert.ok(elements.get('zone-detail').innerHTML.includes('different search'));
elements.get('provenance-toggle').handlers.click();assert.equal(elements.get('provenance').hidden,false);
assert.ok(![...elements.values()].some(e=>/NaN|undefined/.test(e.innerHTML)));
for(const file of ['styles.css','app.js','data.js','scenario_summary.csv','lighting_opportunities.csv','lighting_schedule.csv'])assert.ok(fs.statSync(new URL('dist/'+file,import.meta.url)).size>0);
console.log(`PASS: ${cases} scenario configurations, all 33 zones, primary reconciliation, floor/search filtering, zero-cap identity, and provenance toggle. Browser not opened.`);

assert.ok(!/capture|download-slide|export-filtered/i.test(html));
for (const [,src] of html.matchAll(/<script[^>]+src="([^"]+)"/g)) assert.ok(fs.existsSync(new URL('dist/'+src,import.meta.url)));
