'use client';
import {useEffect,useMemo,useRef,useState} from 'react';
import {Download,Play,Square,MapPin,ArrowUpRight,Loader2,Map,Columns3} from 'lucide-react';
import {FrequencyMap,type MapCell} from './frequency-map';
import {pixelWindows,type PixelCalendarData,type PixelCalendarManifest} from '@/lib/pixel-phenology';
import type {RegionalCalendar} from '@/lib/regional-calendar';
import type {AuditedRule} from '@/lib/hazard-events';
import {FREQUENCY_BINS,frequencyBin,summarizeCell,withinBounds,type AtlasCell} from '@/lib/atlas';
import {atlasSignature,selectYears,mergeAtlasRows,unpackLayer,MAX_INTERACTIVE_QUERIES,estimateRemaining,formatDuration,type AtlasLayerEntry} from '@/lib/atlas-precomputed';
import './atlas.css';

const cropNames:Record<string,string>={maize:'Maize',rice:'Rice',wheat:'Wheat',soybean:'Soybean'};
const phaseNames:Record<string,string>={EST:'Establishment',VEG:'Vegetative growth',FLO:'Flowering',REP:'Reproductive development',FIL:'Grain filling',MAT:'Maturation'};
type Rows=Record<string,AtlasCell>;
const rowKey=(cell:string,phase:string)=>`${cell}|${phase}`;
const percentage=(p:number|null)=>p===null?'Not estimated':`${(p*100).toFixed(1)} %`;
async function readJson(url:string,signal?:AbortSignal){const r=await fetch(url,{signal});if(!r.ok)throw Error('Could not load '+url);return r.json();}

export function ProbabilityAtlas(){
  const [manifest,setManifest]=useState<PixelCalendarManifest|null>(null),[rules,setRules]=useState<AuditedRule[]>([]);
  const [data,setData]=useState<PixelCalendarData|null>(null),[regions,setRegions]=useState<RegionalCalendar|null>(null);
  const [crop,setCrop]=useState('maize'),[season,setSeason]=useState('maize__rf'),[ruleId,setRuleId]=useState(''),[phase,setPhase]=useState('EST');
  const [first,setFirst]=useState(1981),[last,setLast]=useState(2016),[range,setRange]=useState(-1),[minimum,setMinimum]=useState(10);
  const [bounds,setBounds]=useState([-180,-90,180,90]),[scope,setScope]=useState('visible'),[selected,setSelected]=useState('');
  const [rows,setRows]=useState<Rows>({}),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  const [configured,setConfigured]=useState<boolean|null>(null),[progress,setProgress]=useState({done:0,total:0});
  const [layers,setLayers]=useState<AtlasLayerEntry[]>([]),[layerState,setLayerState]=useState('loading');
  const [indexState,setIndexState]=useState('loading');
  const [published,setPublished]=useState<Rows>({}),[savedAt,setSavedAt]=useState('');
  const [elapsed,setElapsed]=useState(0),[outcomes,setOutcomes]=useState({valid:0,unavailable:0,failed:0});
  const [currentQuery,setCurrentQuery]=useState('');
  const [compare,setCompare]=useState(false);
  const controller=useRef<AbortController|null>(null),rowsRef=useRef<Rows>({});
  useEffect(()=>{
    const c=new AbortController();
    Promise.all([readJson('/data/pixel-calendars/manifest.json',c.signal),readJson('/data/gee_rule_audit.json',c.signal)])
      .then(([m,a])=>{setManifest(m);setRules(a.rules);}).catch(e=>{if(!c.signal.aborted)setError(e.message);});
    readJson('/api/hazard-probability',c.signal).then(r=>setConfigured(r.configured)).catch(()=>{if(!c.signal.aborted)setConfigured(false);});
    readJson('/data/atlas/index.json',c.signal).then(index=>{if(!Array.isArray(index.layers))throw Error('Invalid layer index');setLayers(index.layers);setIndexState('ready');}).catch(()=>{if(!c.signal.aborted)setIndexState('error');});
    return()=>{c.abort();controller.current?.abort();};
  },[]);
  useEffect(()=>{
    const entry=manifest?.crops[crop]?.seasons[season];
    setData(null);setRegions(null);setSelected('');if(!entry?.regional_url)return;
    const c=new AbortController();setError('');
    Promise.all([readJson(entry.url,c.signal),readJson(entry.regional_url,c.signal)]).then(([d,r])=>{setData(d);setRegions(r);}).catch(e=>{if(!c.signal.aborted)setError(e.message);});
    return()=>c.abort();
  },[manifest,crop,season]);
  const choices=useMemo(()=>rules.filter(r=>r.crop===crop),[rules,crop]);
  const rule=choices.find(r=>r.rule_id===ruleId);
  useEffect(()=>{if(!choices.some(r=>r.rule_id===ruleId))setRuleId(choices.find(r=>r.status==='operational')?.rule_id??choices[0]?.rule_id??'');},[choices,ruleId]);
  const cells=useMemo(()=>regions?.bands.flatMap(b=>b.zones.flatMap(z=>z.members.map(cell=>({cell,zone:z.id}))))??[],[regions]);
  const phases=useMemo(()=>{if(!data||!cells.length)return [];const [lat,lon]=cells[0].cell.split(',').map(Number);return pixelWindows(data,lat,lon);},[data,cells]);
  useEffect(()=>{setPhase(current=>phases.some(p=>p.phase_code===current&&rule?.phases.some(c=>p.macro_phases.includes(c)))?current:phases.find(p=>rule?.phases.some(c=>p.macro_phases.includes(c)))?.phase_code??phases[0]?.phase_code??'EST');},[phases,rule]);
  const applicable=phases.filter(p=>rule?.phases.some(c=>p.macro_phases.includes(c)));
  const signature=useMemo(()=>rule?atlasSignature(rule,manifest?.version,manifest?.inputs):'',[rule,manifest]);
  const cacheKey=useMemo(()=> 'cerealrisk-atlas-v2:'+JSON.stringify({crop,season,signature}),[crop,season,signature]);
  useEffect(()=>{
    let saved:Rows={};try{saved=JSON.parse(localStorage.getItem(cacheKey)??'{}');}catch{setNotice('Saved results could not be restored.');}
    try{
      const legacyKey='cerealrisk-atlas-v1:'+JSON.stringify({crop,season,rule,first,last,calendar:manifest?.version});
      const legacy=localStorage.getItem(legacyKey);
      if(legacy){saved=mergeAtlasRows(saved,JSON.parse(legacy));localStorage.setItem(cacheKey,JSON.stringify(saved));}
    }catch{setNotice('Some older saved results could not be restored.');}
    rowsRef.current=saved;setRows(saved);setProgress({done:0,total:0});
  },[cacheKey,crop,season,rule,first,last,manifest?.version]);
  useEffect(()=>{
    setPublished({});setSavedAt('');
    if(!signature)return;
    const entry=layers.find(l=>l.crop===crop&&l.season===season&&l.rule_id===ruleId&&l.signature===signature);
    if(!entry){setLayerState(indexState==='loading'?'loading':indexState==='error'?'error':'empty');return;}
    const c=new AbortController();setLayerState('loading');
    readJson(entry.url,c.signal).then(layer=>{
      setPublished(unpackLayer(layer,{crop,season,rule_id:ruleId,signature}));setSavedAt(entry.generated_at);setLayerState('ready');
    }).catch(()=>{if(!c.signal.aborted)setLayerState('error');});
    return()=>c.abort();
  },[layers,crop,season,ruleId,signature,indexState]);
  useEffect(()=>{
    if(!busy)return;
    const started=Date.now();setElapsed(0);
    const timer=setInterval(()=>setElapsed((Date.now()-started)/1000),1000);
    return()=>clearInterval(timer);
  },[busy]);
  const allRows=useMemo(()=>mergeAtlasRows(published,rows),[published,rows]);
  const periodRows=useMemo(()=>selectYears(allRows,first,last),[allRows,first,last]);
  const requested=last-first+1;
  const validYears=Number.isInteger(first)&&Number.isInteger(last)&&first>=1981&&last>=first&&last<new Date().getUTCFullYear();
  const targetCells=useMemo(()=>cells.filter(c=>scope==='all'||withinBounds(c.cell,bounds)),[cells,bounds,scope]);
  const displayRows=useMemo(()=>cells.map(c=>({...c,...summarizeCell(periodRows[rowKey(c.cell,phase)],requested)})),[cells,periodRows,phase,requested]);
  const qualifies=(s:ReturnType<typeof summarizeCell>)=>!s.partial&&s.valid>=minimum&&s.probability!==null;
  const counts=FREQUENCY_BINS.map((_,i)=>displayRows.filter(s=>qualifies(s)&&frequencyBin(s.probability!)===i).length);
  const ranked=displayRows.filter(s=>qualifies(s)&&(range<0||frequencyBin(s.probability!)===range)).sort((a,b)=>b.probability!-a.probability!||b.valid-a.valid);
  const mapCells:MapCell[]=displayRows.map(s=>{
    const valid=qualifies(s),bin=valid?frequencyBin(s.probability!):-1;
    return {cell:s.cell,color:valid?FREQUENCY_BINS[bin].color:s.completed?'#747e85':'#aab1b8',opacity:range>=0?(bin===range?.95:.06):valid?.9:.38,label:percentage(s.probability)};
  });
  const selectedRow=selected?periodRows[rowKey(selected,phase)]:undefined;
  const summary=summarizeCell(selectedRow,requested);
  const totalQueries=targetCells.length*applicable.length*Math.max(0,requested);
  const cachedQueries=targetCells.reduce((sum,cell)=>sum+applicable.reduce((n,p)=>n+(periodRows[rowKey(cell.cell,p.phase_code)]?.years.filter(y=>!y.error).length??0),0),0);
  const pendingQueries=Math.max(0,totalQueries-cachedQueries);
  const tooLarge=pendingQueries>MAX_INTERACTIVE_QUERIES;
  const completedCells=displayRows.filter(row=>!row.partial).length;
  const eta=outcomes.valid+outcomes.unavailable>0?estimateRemaining(elapsed,progress.done,progress.total):null;
  function persist(next:Rows){rowsRef.current=next;setRows({...next});try{localStorage.setItem(cacheKey,JSON.stringify(next));}catch{setNotice('Browser storage is full. Download results before closing.');}}
  async function calculate(){
    if(!data||!rule||rule.status!=='operational'||!validYears||!configured||!targetCells.length||!applicable.length||tooLarge||layerState==='loading')return;
    const c=new AbortController();controller.current=c;setBusy(true);setError('');setNotice('');
    const next:Rows=structuredClone(mergeAtlasRows(published,rowsRef.current));
    const total=pendingQueries;setOutcomes({valid:0,unavailable:0,failed:0});setElapsed(0);setCurrentQuery('Preparing the selected area');
    function* pending(){for(const cell of targetCells)for(const p of applicable)for(let year=first;year<=last;year++){
      if(!next[rowKey(cell.cell,p.phase_code)]?.years.some(y=>y.year===year&&!y.error))yield {...cell,phase:p.phase_code,year};
    }}
    const jobs=pending();setProgress({done:0,total});let done=0,consecutiveFailures=0;
    // Two requests in flight limit Earth Engine pressure; cached years are never recomputed.
    async function worker(){while(!c.signal.aborted){
      const item=jobs.next();if(item.done)break;
      const job=item.value,key=rowKey(job.cell,job.phase),[lat,lon]=job.cell.split(',').map(Number);
      setCurrentQuery(`${job.cell} · ${job.phase} · ${job.year}`);
      try{
        const response=await fetch('/api/hazard-probability',{method:'POST',headers:{'Content-Type':'application/json'},signal:c.signal,
          body:JSON.stringify({crop,season_id:season,zone_id:job.zone,phase:job.phase,rule_id:ruleId,lat,lon,year:job.year,summary_only:true})});
        const result=await response.json();if(!response.ok)throw Error(result.error??'Query unavailable');
        if(typeof result.annual?.evaluable!=='boolean'||(result.annual.evaluable&&typeof result.annual.event_occurred!=='boolean'))throw Error('Incomplete climate response');
        const row=next[key]??{cell:job.cell,phase:job.phase,years:[]};
        row.years=[...row.years.filter(y=>y.year!==job.year),{year:job.year,event:result.annual.evaluable?result.annual.event_occurred:null}];next[key]=row;consecutiveFailures=0;
        setOutcomes(o=>({...o,valid:o.valid+Number(result.annual.evaluable),unavailable:o.unavailable+Number(!result.annual.evaluable)}));
      }catch(e){
        if(c.signal.aborted)break;
        const message=e instanceof Error?e.message:'Query failed';
        setOutcomes(o=>({...o,failed:o.failed+1}));
        const row=next[key]??{cell:job.cell,phase:job.phase,years:[]};row.years=[...row.years.filter(y=>y.year!==job.year),{year:job.year,event:null,error:message}];next[key]=row;
        if(++consecutiveFailures>=3){setError('Calculation stopped after repeated service failures. '+message);c.abort();}
      }
      done++;setProgress({done,total});persist(next);
    }}
    try{await Promise.all([worker(),worker()]);setNotice(c.signal.aborted?'Calculation stopped. Resume without repeating saved years.':'Calculation complete. Cells with insufficient coverage remain unclassified.');}
    finally{persist(next);setBusy(false);controller.current=null;}
  }
  function download(){
    const blob=new Blob([JSON.stringify({schema:'cerealrisk-atlas-v1',crop,season,first,last,rule,calendar_version:manifest?.version,interpretation:'Historical exposure frequency; not loss probability',rows:periodRows},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`atlas-${crop}-${first}-${last}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <main className="probability-atlas">
    <header className="atlas-heading"><div><p>CerealRisk / Exposure atlas</p><h1>Historical hazard occurrence</h1><span>Event frequency by crop and growth stage · {first}–{last}</span></div><a href="/about">Methods <ArrowUpRight size={15}/></a></header>
    <fieldset disabled={busy} className="atlas-toolbar">
      <label>Crop<select value={crop} onChange={e=>{setCrop(e.target.value);const seasons=Object.keys(manifest?.crops[e.target.value]?.seasons??{});setSeason(seasons.find(s=>s.endsWith('__rf'))??seasons[0]??'');setRange(-1);}}>{Object.keys(manifest?.crops??{maize:{}}).map(c=><option key={c} value={c}>{cropNames[c]??c}</option>)}</select></label>
      <label>Season / water system<select value={season} onChange={e=>setSeason(e.target.value)}>{Object.entries(manifest?.crops[crop]?.seasons??{}).map(([id,s])=><option key={id} value={id}>{s.label} · {s.water_label}</option>)}</select></label>
      <label className="atlas-threat">Hazard / event rule<select value={ruleId} onChange={e=>{setRuleId(e.target.value);setRange(-1);}}>{choices.map(r=><option value={r.rule_id} key={r.rule_id}>{r.hazard} · {r.threshold}{r.status!=='operational'?' · external data required':''}</option>)}</select></label>
      <label>From<input type="number" min={1981} max={last} value={first} onChange={e=>setFirst(Number(e.target.value))}/></label><label>To<input type="number" min={first} max={new Date().getUTCFullYear()-1} value={last} onChange={e=>setLast(Number(e.target.value))}/></label>
    </fieldset>
    {rule&&<section className="atlas-event-context" aria-label="Event definition">
      <div><span>Climate variable</span><strong>{rule.equivalence?.variable??rule.spec?.band??'External variable'}</strong></div>
      <div><span>Threshold</span><strong>{rule.threshold}</strong></div>
      <div><span>Exposure condition</span><strong>{rule.exposure??'Not defined'}</strong></div>
      <div><span>Data source</span><strong>{rule.spec?.dataset??'External time series'}</strong></div>
      <p>Event frequency = seasons with at least one qualifying event / valid seasons. Percentage ranges describe occurrence, not hazard intensity or crop loss.</p>
    </section>}
    {error&&<p className="atlas-message error" role="alert">{error}</p>}
    <div className="atlas-workspace"><section className="atlas-map-section">
      <div className="atlas-phase-tabs" role="tablist" aria-label="Crop growth stages">{phases.map(p=>{const n=cells.filter(c=>{const s=summarizeCell(periodRows[rowKey(c.cell,p.phase_code)],requested);return qualifies(s);}).length;return <button key={p.phase_code} role="tab" aria-selected={phase===p.phase_code} onClick={()=>{setPhase(p.phase_code);setRange(-1);}}><strong>{p.macro_phases.map(c=>phaseNames[c]??c).join(' / ')}</strong><span>{!rule?.phases.some(c=>p.macro_phases.includes(c))?'No assigned rule':`${n.toLocaleString('en-US')} calculated cells`}</span></button>;})}</div>
      <div className="atlas-view-switch"><button aria-pressed={!compare} onClick={()=>setCompare(false)}><Map size={15}/> Map</button><button aria-pressed={compare} onClick={()=>setCompare(true)}><Columns3 size={15}/> Compare stages</button></div>
      <div hidden={compare}><FrequencyMap cells={mapCells} onSelect={setSelected} onBounds={setBounds}/></div>
      {compare&&<div className="atlas-small-multiples">{phases.map(p=>{const assigned=rule?.phases.some(c=>p.macro_phases.includes(c));const points=cells.map(c=>{const s=summarizeCell(periodRows[rowKey(c.cell,p.phase_code)],requested),valid=qualifies(s),bin=valid?frequencyBin(s.probability!):-1;return {cell:c.cell,color:valid?FREQUENCY_BINS[bin].color:s.completed?'#747e85':'#aab1b8',opacity:range>=0?(bin===range?.95:.06):valid?.9:.38,label:percentage(s.probability)};});return <section key={p.phase_code}><h3>{p.macro_phases.map(c=>phaseNames[c]??c).join(' / ')}</h3>{assigned?<FrequencyMap compact cells={points} onSelect={cell=>{setPhase(p.phase_code);setSelected(cell);}} onBounds={()=>{}}/>:<div className="atlas-no-rule">No event rule assigned for this hazard</div>}</section>;})}</div>}
      <div className="atlas-legend">
        <div className="atlas-scale-heading"><strong>Historical event frequency</strong><button aria-pressed={range===-1} onClick={()=>setRange(-1)}>All ranges</button></div>
        <div className="atlas-frequency-scale">{FREQUENCY_BINS.map((b,i)=><button key={b.label} aria-pressed={range===i} onClick={()=>setRange(range===i?-1:i)} title={`${b.label}: ${counts[i]} cells`}><i style={{background:b.color}}/><span>{b.label}</span><small>{counts[i].toLocaleString('en-US')} cells</small></button>)}</div>
        <div className="atlas-missing-legend"><span><i style={{background:'#aab1b8'}}/>Not calculated</span><span><i style={{background:'#747e85'}}/>Insufficient coverage / partial</span></div>
      </div>
      <div className="atlas-map-note"><span>{cells.length.toLocaleString('en-US')} crop cells · {ranked.length.toLocaleString('en-US')} in the selected range</span><label>Minimum valid years <input type="number" min={1} max={Math.max(1,requested)} value={minimum} onChange={e=>setMinimum(Math.max(1,Math.min(Math.max(1,requested),Number(e.target.value)||1)))}/></label></div>
    </section><aside className="atlas-sidebar">
      <h2>Explore an area</h2><p className="atlas-muted">{targetCells.length.toLocaleString('en-US')} cells · {applicable.length} stages with this rule</p>
      <fieldset disabled={busy}><label>Extent<select value={scope} onChange={e=>setScope(e.target.value)}><option value="visible">Visible map area</option><option value="all">Entire crop inventory</option></select></label></fieldset>
      <div className="atlas-layer-status" role="status">
        <strong>{layerState==='loading'?'Loading saved layer…':layerState==='ready'?'Saved annual results loaded':layerState==='error'?'Saved layer could not be loaded':'No published layer for this rule yet'}</strong>
        {savedAt&&<span>Prepared {new Date(savedAt).toLocaleDateString('en-US')}</span>}
        <span>{cachedQueries.toLocaleString('en-US')} reusable annual records in this area</span>
      </div>
      <div className="atlas-query-count"><strong>{pendingQueries.toLocaleString('en-US')}</strong><span>annual queries still needed · {cachedQueries.toLocaleString('en-US')} already saved</span></div>
      {tooLarge&&<p className="atlas-warning">This area needs a prepared layer. Interactive checks are limited to {MAX_INTERACTIVE_QUERIES} uncached annual queries. Zoom into a smaller area for a local check; global maps require offline preparation.</p>}
      {!validYears&&<p role="alert" className="atlas-warning">Select complete years from 1981 onwards.</p>}
      {configured===false&&<p className="atlas-warning">Climate data connection is not configured on this server. Crop locations are available; event frequencies require Earth Engine.</p>}
      {rule&&rule.status!=='operational'&&<p className="atlas-warning">This rule requires an external time series. Event frequencies are unavailable with the current connection.</p>}
      <button className="atlas-primary" disabled={busy||!configured||!data||!validYears||!targetCells.length||!applicable.length||rule?.status!=='operational'||tooLarge||pendingQueries===0||layerState==='loading'} onClick={calculate}>{busy?<Loader2 size={16} className="animate-spin"/>:<Play size={16}/>} {busy?'Calculating…':pendingQueries===0?'Saved results ready':tooLarge?'Prepared layer required':'Calculate missing records'}</button>
      {busy&&<button className="atlas-stop" onClick={()=>controller.current?.abort()}><Square size={14}/> Stop and keep results</button>}
      {(busy||progress.total>0)&&<div aria-live="polite" className="atlas-progress">
        <progress value={progress.done} max={Math.max(1,progress.total)}/>
        <strong>{progress.done.toLocaleString('en-US')} / {progress.total.toLocaleString('en-US')} requests finished</strong>
        <span>{outcomes.valid} valid · {outcomes.unavailable} not evaluable · {outcomes.failed} failed</span>
        <span>{completedCells.toLocaleString('en-US')} cells finished in this stage</span>
        <span>Elapsed: {formatDuration(elapsed)}{busy?` · Remaining: ${eta===null?'measuring…':`about ${formatDuration(eta)}`}`:''}</span>
        {busy&&<span className="atlas-muted">Current: {currentQuery}</span>}
      </div>}
      {notice&&<p className="atlas-muted" role="status">{notice}</p>}
      <section className="atlas-detail"><h2><MapPin size={17}/>{selected||'Cell details'}</h2>{selected?<><strong className="atlas-number">{percentage(summary.probability)}</strong><p>{summary.events} event seasons / {summary.valid} valid seasons</p><p className="atlas-muted">{summary.completed} of {requested} years queried{summary.partial?' · partial result':''}{summary.valid<minimum?' · insufficient coverage for classification':''}</p>{summary.probability===0&&<p className="atlas-muted">No events observed in valid years. This does not imply that future events are impossible.</p>}<div className="atlas-years">{selectedRow?.years.slice().sort((a,b)=>a.year-b.year).map(y=><span key={y.year} title={`${y.year}: ${y.error??(y.event===null?'Not evaluable':y.event?'Event':'No event')}`} style={{background:y.event===null?'#e2e4e6':y.event?'#f0b69f':'#c6e4de'}}>{y.year}</span>)}</div></>:<p className="atlas-muted">{Object.keys(periodRows).length?'Select a cell on the map or in the table.':'No saved frequencies for this selection. Gray cells show crop locations, not low event probability.'}</p>}</section>
      <details className="atlas-method"><summary>Event rule and evidence</summary><p>{rule?.equivalence?.variable??rule?.hazard}</p><p>{rule?.threshold} · {rule?.exposure}</p><p>{rule?.reason}</p><p>{rule?.limitations}</p>{rule?.doi&&<a href={rule.doi.startsWith('http')?rule.doi:`https://doi.org/${rule.doi}`} target="_blank" rel="noreferrer">Rule source</a>}<p>Event seasons / evaluable seasons. Failed queries and incomplete years are excluded. This is not crop loss probability or insured risk.</p></details>
    </aside></div>
    <section className="atlas-results"><div className="atlas-results-heading"><div><h2>Spatial comparison</h2><p className="atlas-muted">{phase} · highest event frequency first · {minimum} valid years minimum</p></div><button disabled={!Object.keys(periodRows).length||busy} onClick={download}><Download size={16}/> Download results</button></div>
      {ranked.length?<div className="atlas-table"><table><thead><tr><th>Cell (latitude, longitude)</th><th>Event frequency</th><th>Event seasons</th><th>Valid / requested years</th><th>Frequency range</th></tr></thead><tbody>{ranked.slice(0,100).map(s=><tr key={s.cell}><td><button onClick={()=>setSelected(s.cell)}>{s.cell} <ArrowUpRight size={13}/></button></td><td>{percentage(s.probability)}</td><td>{s.events}</td><td>{s.valid} / {requested}</td><td><i style={{background:FREQUENCY_BINS[frequencyBin(s.probability!)].color}}/>{FREQUENCY_BINS[frequencyBin(s.probability!)].label}</td></tr>)}</tbody></table>{ranked.length>100&&<p>First 100 of {ranked.length} cells. The download includes all results.</p>}</div>:<p className="atlas-empty">{range>=0?'No calculated cells meet the coverage requirement in this range.':'Results appear after calculating an area. Pending cells have no assigned percentage.'}</p>}
    </section>
  </main>;
}
