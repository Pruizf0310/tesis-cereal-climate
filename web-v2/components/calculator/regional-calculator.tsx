'use client';
import {useEffect,useRef,useState} from 'react';
import Papa from 'papaparse';
import {RegionalSelector,type RegionSelection} from '@/components/risk/regional-selector';
import {pixelWindows,phaseDates} from '@/lib/pixel-phenology';
import {evaluateExposure,type AuditedRule,type Sample} from '@/lib/hazard-events';
import {exposureRows,toCsv,type ExposureResponse} from '@/lib/hazard-exports';
import {ExposureCharts} from './exposure-charts';
const field='w-full rounded border border-line bg-bg-panel p-2.5 text-sm text-ink';
const button='rounded border border-line px-3 py-2 text-xs text-cool disabled:opacity-40';
interface Screen {cell:string;result?:ExposureResponse;error?:string}
function save(name:string,value:string,type='text/csv'){const url=URL.createObjectURL(new Blob([value],{type}));const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export function RegionalCalculator(){
 const [region,setRegion]=useState<RegionSelection|null>(null),[rules,setRules]=useState<AuditedRule[]>([]),[phase,setPhase]=useState('EST'),[ruleId,setRuleId]=useState(''),[duration,setDuration]=useState(1);
 const [cell,setCell]=useState(''),[screenYear,setScreenYear]=useState(2016),[first,setFirst]=useState(1981),[last,setLast]=useState(2016);
 const [screen,setScreen]=useState<Screen[]>([]),[results,setResults]=useState<ExposureResponse[]>([]),[failures,setFailures]=useState<{year:number;error:string}[]>([]),[error,setError]=useState('');
 const [busy,setBusy]=useState(false),[progress,setProgress]=useState({done:0,total:1,message:''}),[sourceFile,setSourceFile]=useState<File|null>(null);
 const abort=useRef<AbortController|null>(null),stop=useRef<HTMLButtonElement|null>(null);
 useEffect(()=>{fetch('/data/gee_rule_audit.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(a=>setRules(a.rules)).catch(()=>setError('Could not load the scientific rule registry.'));return()=>abort.current?.abort();},[]);
 const choices=rules.filter(r=>r.crop===region?.crop&&r.phases.includes(phase));
 const rule=choices.find(r=>r.rule_id===ruleId),spec=rule?.spec;
 useEffect(()=>{setCell(region?.zone.representative??'');setScreen([]);},[region]);
 useEffect(()=>{if(!choices.some(r=>r.rule_id===ruleId))setRuleId(choices[0]?.rule_id??'');},[region,phase,rules,ruleId]);
 useEffect(()=>{setDuration(spec?.min_samples??1);setSourceFile(null);},[ruleId,spec?.min_samples]);
 useEffect(()=>{setResults([]);setFailures([]);setError('');},[region,phase,ruleId,cell,first,last,duration]);
 useEffect(()=>{setScreen([]);},[region,phase,ruleId,duration,screenYear]);
 useEffect(()=>{if(!busy)return;stop.current?.focus();const prevent=(e:BeforeUnloadEvent)=>{e.preventDefault();e.returnValue='';};globalThis.addEventListener('beforeunload',prevent);return()=>globalThis.removeEventListener('beforeunload',prevent);},[busy]);
 const [lat,lon]=(cell||region?.zone.representative||'0,0').split(',').map(Number);
 const windows=region?pixelWindows(region.data,lat,lon):[],window=windows.find(w=>w.phase_code===phase);
 const latest=new Date().getUTCFullYear()-1;
 const validDuration=!!spec&&Number.isInteger(duration)&&duration>=1&&duration<=(spec.resolution==='hour'?8784:366);
 const validRange=Number.isInteger(first)&&Number.isInteger(last)&&first>=1981&&first<=last&&last<=latest&&(!window||+phaseDates(last,window).endExclusive<=Date.UTC(latest+1,0,1));
 const validScreen=Number.isInteger(screenYear)&&screenYear>=1981&&screenYear<=latest;
 async function query(key:string,year:number,signal:AbortSignal){
  const [latitude,longitude]=key.split(',').map(Number);
  const response=await fetch('/api/hazard-probability',{method:'POST',headers:{'Content-Type':'application/json'},signal,body:JSON.stringify({crop:region!.crop,season_id:region!.season,zone_id:region!.zone.id,phase,rule_id:ruleId,lat:latitude,lon:longitude,year,duration})});
  const data=await response.json();if(!response.ok)throw Error(data.error??'Query failed');return data as ExposureResponse;
 }
 function begin(total:number){const c=new AbortController();abort.current=c;setBusy(true);setError('');setProgress({done:0,total,message:'Preparing climate query…'});return c;}
 function end(c:AbortController){setBusy(false);abort.current=null;setProgress(p=>({...p,message:c.signal.aborted?'Stopped. Only completed requests are retained.':'Finished. Review results, coverage and any errors below.'}));}
 async function screenRegion(){
  if(!region||!rule||!validDuration||!validScreen)return;const candidates=region.zone.candidates,c=begin(candidates.length),out:Screen[]=[];setScreen([]);
  try{for(let i=0;i<candidates.length;i++){if(c.signal.aborted)break;setProgress({done:i,total:candidates.length,message:'Screening crop cell '+(i+1)+' of '+candidates.length+' · '+screenYear});try{out.push({cell:candidates[i],result:await query(candidates[i],screenYear,c.signal)});}catch(e){if(c.signal.aborted)break;out.push({cell:candidates[i],error:e instanceof Error?e.message:'Query failed'});}setScreen([...out]);setProgress(p=>({...p,done:i+1}));}
   const affected=out.find(s=>s.result?.annual.event_occurred);if(affected)setCell(affected.cell);
  }finally{end(c);}
 }
 async function calculate(){
  if(!rule||!region||!window||!validDuration||!validRange)return;
  const c=begin(last-first+1);setResults([]);setFailures([]);const out:ExposureResponse[]=[],bad:{year:number;error:string}[]=[];
  try{
   let imported:Record<string,string>[]=[];let sourceHash:string|null=null;
   if(rule.status==='external'){
    if(!sourceFile)throw Error('Choose the required external series CSV.');
    const bytes=await sourceFile.arrayBuffer();sourceHash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
    const parsed=Papa.parse<Record<string,string>>(new TextDecoder().decode(bytes),{header:true,skipEmptyLines:true});if(parsed.errors.length)throw Error('CSV parsing failed: '+parsed.errors[0].message);
    imported=parsed.data;
    const expected=['timestamp_utc','planting_year','latitude','longitude','variable','unit','value','source'];if(!expected.every(k=>parsed.meta.fields?.includes(k)))throw Error('Use the exact headers in the downloadable CSV template.');
    if(imported.some(r=>r.latitude.trim()===''||r.longitude.trim()===''||Number(r.latitude)!==lat||Number(r.longitude)!==lon||r.variable!==rule.equivalence?.csv_variable||r.unit!==spec!.unit||!r.source.trim()))throw Error('CSV coordinate, variable, unit or source does not match this selection.');
    for(const r of imported){if(!Number.isInteger(Number(r.planting_year))||!r.planting_year.trim()||!r.timestamp_utc.endsWith('Z')||!Number.isFinite(Date.parse(r.timestamp_utc))||(r.value.trim()!==''&&!Number.isFinite(Number(r.value))))throw Error('Each row needs a valid planting year, explicit UTC timestamp, and a numeric or empty value.');if(spec!.unit==='0/1'&&r.value.trim()!==''&&![0,1].includes(Number(r.value)))throw Error('Flooding/submergence indicators must be 0 or 1.');}
   }
   for(let year=first;year<=last;year++){
    if(c.signal.aborted)break;setProgress({done:year-first,total:last-first+1,message:'Calculating '+rule.hazard+' · planting year '+year});
    try{
     let response:ExposureResponse;
     if(rule.status==='external'){
      const dates=phaseDates(year,window),effective={...spec!,min_samples:duration};
      const raw:Sample[]=imported.filter(r=>Number(r.planting_year)===year).map(r=>({time:Date.parse(r.timestamp_utc),value:r.value.trim()===''?null:Number(r.value)}));
      if(raw.some(s=>s.time<+dates.start||s.time>=+dates.endExclusive))throw Error('CSV contains a timestamp outside the selected phase for this planting year.');
      response={annual:evaluateExposure(year,dates.start,dates.endExclusive,raw,effective),rule,effective_spec:effective,request:{crop:region.crop,season_id:region.season,phase,rule_id:ruleId,lat,lon,zone_id:region.zone.id,year,duration},provenance:{dataset:'Imported exact-variable series',calendar_version:region.version,source_file:sourceFile!.name,source_sha256:sourceHash,source_labels:[...new Set(imported.map(r=>r.source))],variable:rule.equivalence?.csv_variable,unit:spec!.unit,interpretation:rule.equivalence?.note,retrieved_at:new Date().toISOString()}};
     }else response=await query(cell,year,c.signal);
     out.push(response);setResults([...out]);
    }catch(e){if(c.signal.aborted)break;bad.push({year,error:e instanceof Error?e.message:'Query failed'});setFailures([...bad]);}
    setProgress(p=>({...p,done:year-first+1}));await new Promise(resolve=>setTimeout(resolve,0));
   }
  }catch(e){setError(e instanceof Error?e.message:'Calculation failed');}finally{end(c);}
 }
 function template(){if(!region||!window||!rule||!spec)return;const rows=[];for(let year=first;year<=last;year++){const d=phaseDates(year,window);for(let time=+d.start;time<+d.endExclusive;time+=spec.resolution==='hour'?3600000:86400000)rows.push({timestamp_utc:new Date(time).toISOString(),planting_year:year,latitude:lat,longitude:lon,variable:rule.equivalence?.csv_variable,unit:spec.unit,value:'',source:''});}save('required-series-'+ruleId+'.csv',toCsv(rows));}
 const context={version:'regional-v4-2026-09-16',region:region?{crop:region.crop,season:region.season,band:region.bandLabel,zone:region.zone.label,zone_id:region.zone.id,total_cells:region.zone.count}:null,selected_cell:cell,screening_year:screenYear,screening:screen,requested_years:[first,last],duration,failures,selection_note:'Candidates were spatially selected independently of weather. Selecting a cell after observing its screening-year event is outcome-based exploration, not an unbiased regional probability estimate.'};
 const cellOptions=region?[...new Set([region.zone.representative,...screen.filter(s=>s.result?.annual.event_occurred).map(s=>s.cell),...region.zone.candidates])]:[];
 return <div className="mt-8 space-y-5">
  <section className="rounded border border-line bg-bg-panel/60 p-5"><RegionalSelector disabled={busy} onChange={setRegion}/><p className="mt-3 text-xs leading-relaxed text-ink-dim">Choose a crop region. Every option belongs to the archived crop inventory; you do not need to enter a coordinate. Longitude and planting regimes separate different calendars within a latitude band.</p></section>
  <fieldset disabled={busy} className="grid gap-4 rounded border border-line p-5 sm:grid-cols-2 lg:grid-cols-3">
   <label className="grid gap-1 text-xs text-ink-dim">Phenological phase<select aria-label="Phenological phase" className={field} value={phase} onChange={e=>setPhase(e.target.value)}>{windows.map(w=><option key={w.phase_code} value={w.phase_code}>{w.phase_code} — {w.phase_label}</option>)}</select></label>
   <label className="grid gap-1 text-xs text-ink-dim sm:col-span-2">Threat / exact variable<select aria-label="Threat" className={field} value={ruleId} onChange={e=>setRuleId(e.target.value)}>{!choices.length&&<option value="">No reviewed trigger assigned</option>}{choices.map(r=><option key={r.rule_id} value={r.rule_id}>{r.hazard} — {r.equivalence?.variable} ({r.status==='external'?'external series':'GEE'})</option>)}</select></label>
   <label className="grid gap-1 text-xs text-ink-dim">Screening year<input aria-label="Screening year" type="number" className={field} value={screenYear} onChange={e=>setScreenYear(Number(e.target.value))}/></label>
   <label className="grid gap-1 text-xs text-ink-dim">{spec?.mode==='accumulated'?'Accumulated exposure':'Consecutive exposure'} ({spec?.resolution==='hour'?'hours':'daily cycles'})<input aria-label="Consecutive exposure" type="number" min={1} className={field} value={duration} onChange={e=>setDuration(Number(e.target.value))}/></label>
   <div className="flex items-end"><button className={button+' w-full'} disabled={!rule||rule.status!=='operational'||!validScreen||!validDuration} onClick={screenRegion}>Find exposed crop cells ({region?.zone.candidates.length??0} candidates)</button></div>
  </fieldset>
  {rule?.equivalence&&<section className="space-y-2 rounded border border-cool/30 p-4 text-xs leading-relaxed text-ink-dim"><h3 className="text-sm font-medium text-cool">{rule.equivalence.variable}</h3><p className="font-mono text-ink">{rule.equivalence.equation}</p><p>{rule.equivalence.note}</p><p><strong>Duration basis:</strong> {rule.equivalence.duration_basis} {duration!==spec?.min_samples&&'You changed the duration: this run is a sensitivity analysis.'}</p><p>Reviewed source: <a className="text-cool underline" href={rule.doi.startsWith('http')?rule.doi:'https://doi.org/'+rule.doi} target="_blank" rel="noreferrer">{rule.source}</a> · {rule.rule_id}</p>{rule.equivalence.evidence_update&&<p>{rule.equivalence.evidence_update}</p>}</section>}
  {!choices.length&&region&&<p className="rounded border border-line p-4 text-sm text-warm">{region.crop==='maize'&&phase==='REP'?'Maize REP remains reserved for the pending hazard assignment. Its calendar duration is defined; no temperature threshold is invented.':'No reviewed threat is assigned to this phase. The six-phase calendar remains complete.'}</p>}
  {screen.length>0&&<section className="rounded border border-line p-4 text-xs text-ink-dim"><h3 className="text-sm text-ink">Observed exposures in screening year {screenYear}</h3><p className="my-2">{screen.length} of {region?.zone.count} crop cells examined. This spatial sample is not an exhaustive regional search. A zero result means no qualifying exposure in the cells tested.</p><div className="flex flex-wrap gap-2">{screen.map(s=><button key={s.cell} disabled={busy} onClick={()=>setCell(s.cell)} className={'rounded border p-2 '+(s.result?.annual.event_occurred?'border-[#B9FF3B] text-[#B9FF3B]':'border-line text-ink-dim')}>{s.cell} · {s.error?'Query unavailable':s.result?.annual.event_occurred?'Event observed':s.result?.annual.evaluable?'No qualifying event':'Incomplete or too short'} · longest {s.result?.annual.observed_longest_run??s.result?.annual.longest_run??'—'} {spec?.resolution==='hour'?'h':'d'}</button>)}</div><p className="mt-3">Selecting an affected cell is outcome-based exploration. Its later frequency is not an unbiased probability for the entire region.</p></section>}
  <fieldset disabled={busy} className="grid gap-4 rounded border border-line p-5 sm:grid-cols-3">
   <label className="grid gap-1 text-xs text-ink-dim">Crop cell from this region<select aria-label="Crop cell" className={field} value={cell} onChange={e=>setCell(e.target.value)}>{cellOptions.map(k=><option key={k} value={k}>{k===region?.zone.representative?'Representative · ':'Crop cell · '}{k}{screen.find(s=>s.cell===k)?.result?.annual.event_occurred?' · event observed':''}</option>)}</select></label>
   <label className="grid gap-1 text-xs text-ink-dim">First planting year<input aria-label="First planting year" type="number" className={field} value={first} onChange={e=>setFirst(Number(e.target.value))}/></label>
   <label className="grid gap-1 text-xs text-ink-dim">Last planting year<input aria-label="Last planting year" type="number" className={field} value={last} onChange={e=>setLast(Number(e.target.value))}/></label>
  </fieldset>
  {window&&validRange&&<p className="text-xs text-ink-dim">Selected cell: {phase} · {phaseDates(first,window).start.toISOString().slice(0,10)} to {phaseDates(first,window).end.toISOString().slice(0,10)} for planting year {first}. {window.duration_days} reference days; leap years may add one. Dates are estimates, not annual crop observations.</p>}
  {!validRange&&<p className="text-sm text-warm">Use complete planting years from 1981; the entire phase must end before the current year.</p>}
  {rule?.status==='external'&&<fieldset disabled={busy} className="space-y-3 rounded border border-warm/40 p-4 text-sm text-ink-dim"><p>This exact variable needs an external measured or independently modelled series. Import the defined quantity; monthly water maps, rainfall and 2 m air temperature do not replace it.</p><button className={button} disabled={!validRange} onClick={template}>Download exact-variable CSV template</button><label className="block text-xs">Choose completed CSV<input aria-label="External series CSV" type="file" accept=".csv,text/csv" className="mt-2 block w-full" onChange={e=>{setSourceFile(e.target.files?.[0]??null);setResults([]);}}/></label><p className="text-xs">Template: UTC timestamps, planting year, selected latitude/longitude, variable identifier, exact unit, value and source. Empty values remain missing. The file is processed in your browser.</p></fieldset>}
  <div className="flex flex-wrap items-center gap-3"><button disabled={busy||!region||!rule||!validRange||!validDuration||(rule.status==='external'&&!sourceFile)} onClick={calculate} className="rounded-md border border-[#DBFF99] bg-[#B9FF3B] px-6 py-3 text-sm font-bold text-[#102000] shadow-[0_0_22px_rgba(185,255,59,0.25)] disabled:opacity-35">{busy?'PROCESSING…':'CALCULATE EXPOSURE PROBABILITY'}</button><span className="text-xs text-ink-dim" aria-live="polite">{progress.message}</span></div>
  {error&&<p role="alert" className="rounded border border-warm p-3 text-sm text-warm">{error}</p>}
  {failures.length>0&&<details className="text-xs text-warm"><summary>{failures.length} failed years — excluded from probability</summary>{failures.map(f=><p key={f.year}>{f.year}: {f.error}</p>)}</details>}
  {results.length>0&&<><ExposureCharts results={results} requested={last-first+1}/><section className="space-y-3 rounded border border-line p-4"><h3 className="text-sm text-ink">Download for trigger, conditional-probability and parametric-index analysis</h3><div className="flex flex-wrap gap-2">{(['series','source','annual','events'] as const).map(kind=><button key={kind} className={button} disabled={busy} onClick={()=>save(ruleId+'-'+kind+'.csv',toCsv(exposureRows(results,kind)))}>{kind==='series'?'Analysis series':kind==='source'?'Source series':kind==='annual'?'Annual metrics':'Event intervals'} CSV</button>)}<button className={button} disabled={busy} onClick={()=>save(ruleId+'-complete.json',JSON.stringify({...context,results},null,2),'application/json')}>Complete data + provenance JSON</button></div><p className="text-xs text-ink-mute">Exports retain threshold operators, duration, phase, location, UTC timestamps, raw/derived values, event flags, excess, annual coverage and data provenance. JSON includes screening results and failed years. No insurance payout or conditional model is inferred yet.</p></section></>}
  <p className="text-xs text-ink-mute"><a className="text-cool underline" href="https://github.com/Pruizf0310/tesis-cereal-climate/blob/main/docs/regional_workflow_v4.md" target="_blank" rel="noreferrer">Methods, evidence and versioned change log</a>. Contains modified Copernicus Climate Change Service information (2026). Neither the European Commission nor ECMWF is responsible for its use.</p>
  {busy&&<div role="dialog" aria-modal="true" aria-labelledby="processing-title" className="fixed inset-0 z-[200] grid place-items-center bg-black/80 p-6 backdrop-blur-sm" onKeyDown={e=>{if(e.key==='Tab'){e.preventDefault();stop.current?.focus();}}}><div className="w-full max-w-lg rounded-lg border border-[#B9FF3B] bg-[#091820] p-7 shadow-[0_0_50px_rgba(185,255,59,0.15)]"><div className="mb-4 h-10 w-10 animate-spin rounded-full border-4 border-[#B9FF3B]/20 border-t-[#B9FF3B]"/><h2 id="processing-title" className="text-xl font-semibold text-[#B9FF3B]">PROCESSING CLIMATE DATA</h2><p aria-live="polite" className="mt-3 text-sm text-ink">{progress.message}</p><div className="my-4 h-3 overflow-hidden rounded bg-white/10"><div className="h-full bg-[#B9FF3B] transition-all" style={{width:100*progress.done/progress.total+'%'}}/></div><p className="text-xs text-ink-dim">{progress.done}/{progress.total} requests complete. Keep this page open; controls are locked while processing.</p><button ref={stop} onClick={()=>abort.current?.abort()} className="mt-5 rounded border border-line px-4 py-2 text-sm text-ink">Stop and keep completed results</button></div></div>}
 </div>;
}
