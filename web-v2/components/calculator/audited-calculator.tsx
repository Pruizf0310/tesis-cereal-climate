'use client';
import {useEffect,useRef,useState} from 'react';
import {pixelWindows,phaseDates,type PixelCalendarData,type PixelCalendarManifest} from '@/lib/pixel-phenology';
import {probabilityOfExposure,type AuditedRule,type AnnualExposure} from '@/lib/hazard-events';
const field='w-full rounded border border-line bg-bg-panel p-2 text-sm text-ink';
interface ResponseRow {annual:AnnualExposure;rule:AuditedRule;provenance:Record<string,unknown>;request:Record<string,unknown>}
interface Run {rule:AuditedRule;results:ResponseRow[];failures:{year:number;message:string}[]}
export function AuditedCalculator(){
 const [manifest,setManifest]=useState<PixelCalendarManifest|null>(null),[rules,setRules]=useState<AuditedRule[]>([]),[data,setData]=useState<PixelCalendarData|null>(null);
 const [crop,setCrop]=useState('rice'),[season,setSeason]=useState('rice_1__rf'),[lat,setLat]=useState('10.25'),[lon,setLon]=useState('105.25'),[phase,setPhase]=useState('EST');
 const [start,setStart]=useState(1981),[end,setEnd]=useState(2016),[error,setError]=useState(''),[runs,setRuns]=useState<Run[]>([]),[busy,setBusy]=useState(false),[progress,setProgress]=useState('');
 const abort=useRef<AbortController|null>(null);
 useEffect(()=>{Promise.all([fetch('/data/pixel-calendars/manifest.json').then(r=>{if(!r.ok)throw Error();return r.json();}),fetch('/data/gee_rule_audit.json').then(r=>{if(!r.ok)throw Error();return r.json();})]).then(([m,a])=>{setManifest(m);setRules(a.rules);}).catch(()=>setError('Calendar or rule audit could not be loaded.'));return()=>abort.current?.abort();},[]);
 useEffect(()=>{const entry=manifest?.crops[crop]?.seasons[season];setData(null);if(!entry)return;let active=true;fetch(entry.url).then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>{if(active){setData(d);setError('');}}).catch(()=>{if(active)setError('Coordinate calendar could not be loaded.');});return()=>{active=false;};},[manifest,crop,season]);
 useEffect(()=>{setRuns([]);setProgress('');},[crop,season,lat,lon,phase,start,end]);
 const latitude=Number(lat),longitude=Number(lon);
 const exact=lat.trim()!==''&&lon.trim()!==''&&Number.isFinite(latitude)&&Number.isFinite(longitude)&&latitude>=-89.75&&latitude<=89.75&&longitude>=-179.75&&longitude<=179.75&&Number.isInteger((latitude-.25)*2)&&Number.isInteger((longitude-.25)*2);
 const windows=data&&exact?pixelWindows(data,latitude,longitude):[];
 const selected=windows.find(w=>w.phase_code===phase);
 const applicable=selected?rules.filter(r=>r.crop===crop&&r.phases.some(p=>selected.macro_phases.includes(p))):[];
 const operational=applicable.filter(r=>r.status==='operational');
 const lastYear=new Date().getUTCFullYear()-1;
 const validYears=Number.isInteger(start)&&Number.isInteger(end)&&start>=1981&&end<=lastYear&&end>=start&&(!selected||+phaseDates(end,selected).endExclusive<=Date.UTC(lastYear+1,0,1));
 const previewYear=validYears?start:1981;
 async function calculate(targets:AuditedRule[]){
  if(!selected||!validYears||!targets.length)return;
  setBusy(true);setError('');setRuns([]);const controller=new AbortController();abort.current=controller;
  const next:Run[]=targets.map(rule=>({rule,results:[],failures:[]}));let done=0;
  try{
   for(const run of next)for(let year=start;year<=end;year++){
    if(controller.signal.aborted)break;
    setProgress(`${done+1} / ${targets.length*(end-start+1)} · ${run.rule.hazard} · planting year ${year}`);
    try{
     const response=await fetch('/api/hazard-probability',{method:'POST',headers:{'Content-Type':'application/json'},signal:controller.signal,body:JSON.stringify({crop,season_id:season,lat:latitude,lon:longitude,phase,rule_id:run.rule.rule_id,year})});
     const result=await response.json();if(!response.ok)throw Error(result.error??'Query failed');run.results.push(result);
    }catch(e){if(controller.signal.aborted)break;run.failures.push({year,message:e instanceof Error?e.message:'Query failed'});}
    done++;setRuns(next.map(r=>({...r,results:[...r.results],failures:[...r.failures]})));
   }
   setProgress(controller.signal.aborted?'Stopped. Results cover only the completed requests.':'Requests completed. Review valid and unavailable years below.');
  }finally{setBusy(false);abort.current=null;}
 }
 function exportResults(){const url=URL.createObjectURL(new Blob([JSON.stringify({audit_version:'2026-09-16',requested_years:[start,end],crop,season,lat,lon,phase,results:runs},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`exposure-${crop}-${phase}-${start}-${end}.json`;a.click();URL.revokeObjectURL(url);}
 return <div className="mt-10 space-y-6 text-ink">
  <fieldset disabled={busy} className="grid gap-4 rounded border border-line bg-bg-panel p-5 sm:grid-cols-2 lg:grid-cols-4">
   <label className="space-y-1 text-xs">Crop<select className={field} value={crop} onChange={e=>{const c=e.target.value;setCrop(c);setSeason(Object.keys(manifest?.crops[c]?.seasons??{})[0]??'');setPhase('EST');}}>{Object.entries(manifest?.crops??{}).map(([id,c])=><option key={id} value={id}>{c.label}</option>)}</select></label>
   <label className="space-y-1 text-xs">Season / water system<select className={field} value={season} onChange={e=>setSeason(e.target.value)}>{Object.entries(manifest?.crops[crop]?.seasons??{}).map(([id,s])=><option key={id} value={id}>{s.label} · {s.water_label}</option>)}</select></label>
   <label className="space-y-1 text-xs">Pixel centre latitude<input className={field} type="number" step="0.5" value={lat} onChange={e=>setLat(e.target.value)}/></label>
   <label className="space-y-1 text-xs">Pixel centre longitude<input className={field} type="number" step="0.5" value={lon} onChange={e=>setLon(e.target.value)}/></label>
   <label className="space-y-1 text-xs sm:col-span-2">Consecutive calendar interval<select className={field} value={phase} onChange={e=>setPhase(e.target.value)}><option value="">Select an interval</option>{windows.map(w=><option value={w.phase_code} key={w.phase_code}>{w.phase_code} · {w.phase_label} · {w.duration_days} reference days</option>)}</select></label>
   <label className="space-y-1 text-xs">First planting year<input className={field} type="number" min={1981} max={lastYear} value={start} onChange={e=>setStart(Number(e.target.value))}/></label>
   <label className="space-y-1 text-xs">Last planting year<input className={field} type="number" min={1981} max={lastYear} value={end} onChange={e=>setEnd(Number(e.target.value))}/></label>
  </fieldset>
  {error&&<p role="alert" className="text-warm">{error}</p>}
  {!data?<p>Loading calendar…</p>:!windows.length?<p className="text-warm">No calendar at this exact grid centre. Choose a coordinate available for this crop and season; no nearby pixel is substituted.</p>:!selected?<p>Select a calendar interval.</p>:<div className="space-y-3 rounded border border-line p-5 text-sm text-ink-dim">
   <p><strong className="text-ink">{selected.phase_code}</strong> · {phaseDates(previewYear,selected).start.toISOString().slice(0,10)} to {new Date(+phaseDates(previewYear,selected).endExclusive-86400000).toISOString().slice(0,10)} for planting year {previewYear} · {phaseDates(previewYear,selected).expectedDays} days.</p>
   <p>Dates repeat the estimated climatological calendar in each planting year. Leap days remain inside the consecutive sequence. The meteorological value is a spatial mean over the 0.5° cell.</p>
   {selected.shared&&<p className="text-warm">One combined interval: internal phase boundaries are unresolved. Each applicable trigger uses this entire interval; results cannot identify which internal phase experienced the exposure.</p>}
   {crop==='maize'&&selected.macro_phases.includes('REP')&&<p>Maize reproductive development: an additional hazard assignment is pending. No threshold or probability is invented for that missing rule.</p>}
  </div>}
  {!validYears&&<p className="text-warm">Choose planting years from 1981 with each full phase ending before the current calendar year.</p>}
  <div className="flex flex-wrap items-center gap-3"><button disabled={busy||!validYears||!operational.length} onClick={()=>calculate(operational)} className="rounded bg-cool px-4 py-2 text-sm text-bg-deep disabled:opacity-40">Calculate all operational triggers in this interval ({operational.length})</button>{busy&&<button onClick={()=>abort.current?.abort()} className="rounded border border-line p-2">Stop</button>}{runs.length>0&&<button onClick={exportResults} className="rounded border border-line p-2 text-sm">Download results and provenance</button>}</div>
  <p aria-live="polite" className="text-xs text-ink-dim">{progress}</p>
  <div className="space-y-3">{applicable.map(rule=><article key={rule.rule_id} className="rounded border border-line p-4"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="text-sm font-medium">{rule.hazard} · {rule.phases.join(' / ')} · {rule.threshold} · {rule.exposure??'Duration unresolved'}</h3><span className={rule.spec?'text-xs text-cool':'text-xs text-warm'}>{rule.spec?'Operational exposure':'Unavailable'}</span></div><p className="mt-2 text-xs leading-relaxed text-ink-dim">{rule.reason}</p><p className="mt-2 text-xs text-ink-mute">Evidence: {rule.evidence_category} · <a className="text-cool underline" target="_blank" rel="noreferrer" href={rule.doi.startsWith('http')?rule.doi:`https://doi.org/${rule.doi}`}>{rule.source}</a> · {rule.rule_id}</p>{rule.spec&&<button className="mt-3 text-xs text-cool underline disabled:opacity-40" disabled={busy||!validYears} onClick={()=>calculate([rule])}>Calculate this trigger</button>}</article>)}</div>
  {runs.map(run=><ExposureResult key={run.rule.rule_id} run={run} requested={end-start+1} busy={busy}/>)}
  <p className="text-xs leading-relaxed text-ink-mute">Probability = event years / fully observed, evaluable years. Missing samples, failed requests and phases shorter than the required exposure are excluded, with no zero substituted. All dates and samples use UTC. These are historical meteorological exposure frequencies, not crop damage probabilities. <a href="https://github.com/Pruizf0310/tesis-cereal-climate/blob/main/docs/gee_probability_method.md" className="text-cool underline" target="_blank" rel="noreferrer">Method and rule audit</a></p>
 </div>;
}
function ExposureResult({run,requested,busy}:{run:Run;requested:number;busy:boolean}){
 const annual=run.results.map(r=>r.annual),summary=probabilityOfExposure(annual),unit=run.rule.spec?.resolution==='hour'?'hours':'days';
 const maximum=Math.max(1,...annual.map(a=>a.longest_run??0));
 return <section className="rounded border border-line p-5"><h3 className="text-base">{run.rule.hazard} · {run.rule.threshold}</h3><div className="my-4 flex flex-wrap gap-8"><div><div className="text-3xl text-cool">{summary.probability===null?'Unavailable':`${(summary.probability*100).toFixed(1)}%`}</div><p className="text-xs text-ink-dim">{summary.event_years} event years / {summary.valid_years} valid years{busy?' · partial':''}</p></div><p className="text-xs text-ink-dim">{annual.length+run.failures.length} / {requested} requests completed<br/>{run.failures.length+annual.filter(a=>!a.evaluable).length} unavailable years</p></div>
  <p className="mb-3 text-xs text-ink-dim">{run.rule.spec?.mode==='rolling_mean'?'Longest union of qualifying six-day windows':'Longest consecutive threshold exposure'} ({unit}, UTC). Orange bars mark qualifying event years.</p>
  <div className="max-h-[420px] space-y-2 overflow-y-auto" role="img" aria-label={`Annual exposure durations in ${unit}; detailed values in the following table`}>{annual.map(a=><div key={a.year} className="flex items-center gap-3 text-xs"><span className="w-10 shrink-0">{a.year}</span><div className="h-4 flex-1 bg-white/5"><div className={a.event_occurred?'h-4 bg-warm':'h-4 bg-cool/60'} style={{width:`${100*(a.longest_run??0)/maximum}%`}}/></div><span className="w-20 text-right">{a.longest_run===null?'Unavailable':`${a.longest_run} ${unit}`}</span></div>)}</div>
  <details className="mt-5 text-xs"><summary className="cursor-pointer text-cool">Annual values, event intervals and unavailable years</summary><div className="mt-3 overflow-x-auto"><table className="w-full text-left"><thead><tr><th className="p-2">Planting year</th><th>Available / expected samples</th><th>Event</th><th>Qualifying intervals (UTC; end exclusive)</th></tr></thead><tbody>{annual.map(a=><tr key={a.year} className="border-t border-line"><td className="p-2">{a.year}</td><td>{a.available_samples} / {a.expected_samples}</td><td>{a.event_occurred===null?'Unavailable':a.event_occurred?'Yes':'No'}</td><td>{a.events.map(e=>`${e.start} → ${e.end_exclusive} (${e.duration} ${unit})`).join('; ')||'—'}</td></tr>)}{run.failures.map(f=><tr key={f.year}><td className="p-2">{f.year}</td><td colSpan={3}>{f.message}</td></tr>)}</tbody></table></div></details>
 </section>;
}
