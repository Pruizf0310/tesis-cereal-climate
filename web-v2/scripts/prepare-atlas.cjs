const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {parseArgs}=require('node:util');
const load=require('./load-project-ts.cjs');
const {atlasSignature,packLayer,mergeAtlasRows}=load(path.join(__dirname,'../lib/atlas-precomputed.ts'));
const {pixelWindows}=load(path.join(__dirname,'../lib/pixel-phenology.ts'));
const {withinBounds}=load(path.join(__dirname,'../lib/atlas.ts'));
const root=path.join(__dirname,'..');
const read=file=>JSON.parse(fs.readFileSync(file,'utf8'));
const sha=text=>crypto.createHash('sha256').update(text).digest('hex').slice(0,20);
const atomic=(file,data)=>{fs.writeFileSync(file+'.tmp',data);fs.renameSync(file+'.tmp',file);};

async function main(){
  const {values:o}=parseArgs({options:{crop:{type:'string'},season:{type:'string'},rule:{type:'string'},first:{type:'string',default:'1981'},last:{type:'string',default:'2016'},bounds:{type:'string'},origin:{type:'string'},run:{type:'boolean',default:false},'max-requests':{type:'string',default:'200'},concurrency:{type:'string',default:'2'},output:{type:'string'},checkpoint:{type:'string'}}});
  const first=Number(o.first),last=Number(o.last),limit=Number(o['max-requests']),concurrency=Number(o.concurrency);
  if(!o.crop||!o.season||!o.rule)throw Error('Required: --crop --season --rule. Default mode prints a plan; --run starts requests.');
  if(!Number.isInteger(first)||!Number.isInteger(last)||first<1981||last<first||last>=new Date().getUTCFullYear())throw Error('Invalid complete planting-year range');
  if(!Number.isInteger(limit)||limit<1||!Number.isInteger(concurrency)||concurrency<1||concurrency>2)throw Error('Use a positive request limit and 1 or 2 workers');
  const bounds=o.bounds?o.bounds.split(',').map(Number):[-180,-90,180,90];
  if(bounds.length!==4||bounds.some(v=>!Number.isFinite(v))||bounds[1]<-90||bounds[3]>90||bounds[1]>bounds[3])throw Error('Bounds: west,south,east,north');
  const manifest=read(path.join(root,'public/data/pixel-calendars/manifest.json'));
  const rule=read(path.join(root,'public/data/gee_rule_audit.json')).rules.find(r=>r.crop===o.crop&&r.rule_id===o.rule);
  const entry=manifest.crops[o.crop]?.seasons[o.season];
  if(!rule||rule.status!=='operational'||!entry?.regional_url)throw Error('Select a crop season and an operational rule');
  const calendar=read(path.join(root,'public',entry.url));
  const regional=read(path.join(root,'public',entry.regional_url));
  const signature=atlasSignature(rule,manifest.version,manifest.inputs);
  const identity={crop:o.crop,season:o.season,rule_id:o.rule,signature};
  const id=sha(JSON.stringify(identity));
  const checkpoint=path.resolve(o.checkpoint??path.join(root,'.atlas-cache',id+'.ndjson'));
  let rows={};
  if(fs.existsSync(checkpoint)){
    const text=fs.readFileSync(checkpoint,'utf8');
    const lines=text.split('\n');
    for(let i=0;i<lines.length;i++){
      if(!lines[i].trim())continue;
      let record;try{record=JSON.parse(lines[i]);}catch{throw Error(`Invalid checkpoint line ${i+1}; preserve it and repair the truncated record before resuming`);}
      if(record.id!==id)throw Error('Checkpoint belongs to a different rule or calendar');
      rows[record.key]=mergeAtlasRows(rows[record.key]?{[record.key]:rows[record.key]}:{},{[record.key]:record.row})[record.key];
    }
  }
  const cells=regional.bands.flatMap(b=>b.zones.flatMap(z=>z.members.map(cell=>({cell,zone:z.id})))).filter(c=>withinBounds(c.cell,bounds));
  function* jobs(){for(const cell of cells){
    const [lat,lon]=cell.cell.split(',').map(Number);
    for(const phase of pixelWindows(calendar,lat,lon).filter(p=>p.macro_phases.some(c=>rule.phases.includes(c)))){
      const key=`${cell.cell}|${phase.phase_code}`;
      for(let year=first;year<=last;year++)if(!rows[key]?.years.some(y=>y.year===year&&!y.error))yield {...cell,key,phase:phase.phase_code,lat,lon,year};
    }
  }}
  let pending=0;for(const job of jobs())pending++;
  console.log(JSON.stringify({mode:o.run?'prepare':'plan',crop:o.crop,season:o.season,rule:o.rule,cells:cells.length,first,last,pending,request_limit:limit,concurrency,checkpoint}));
  if(!o.run)return;
  if(!o.origin)throw Error('--origin is required with --run; use the configured application server');
  const origin=new URL(o.origin);
  if(origin.protocol!=='https:'&&!(origin.protocol==='http:'&&['localhost','127.0.0.1'].includes(origin.hostname)))throw Error('Use HTTPS or localhost');
  if(origin.username||origin.password||origin.search||origin.hash)throw Error('Do not put credentials in the origin URL');
  const endpoint=new URL('/api/hazard-probability',origin);
  const configured=await fetch(endpoint,{signal:AbortSignal.timeout(30000)}).then(async r=>{if(!r.ok)throw Error('Source preflight failed');return r.json();});
  if(!configured.configured)throw Error('The source server has no Earth Engine connection');
  fs.mkdirSync(path.dirname(checkpoint),{recursive:true});
  const controller=new AbortController();
  process.once('SIGINT',()=>controller.abort());
  const iterator=jobs();let scheduled=0,done=0,valid=0,unavailable=0,failed=0,consecutiveFailures=0;
  const started=Date.now();
  async function worker(){while(!controller.signal.aborted&&scheduled<limit){
    const item=iterator.next();if(item.done)break;scheduled++;
    const job=item.value;let annual,provenance;
    try{
      const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},signal:AbortSignal.any([controller.signal,AbortSignal.timeout(310000)]),body:JSON.stringify({crop:o.crop,season_id:o.season,rule_id:o.rule,zone_id:job.zone,phase:job.phase,lat:job.lat,lon:job.lon,year:job.year,summary_only:true})});
      const result=await response.json();if(!response.ok)throw Error(result.error??`Source returned HTTP ${response.status}`);
      if(atlasSignature(result.rule,result.provenance?.calendar_version,result.provenance?.calendar_inputs)!==signature)throw Error('Source rule or calendar differs from the local registry; use an updated source server');
      if(result.request?.year!==job.year||result.request?.phase!==job.phase||result.request?.lat!==job.lat||result.request?.lon!==job.lon||result.request?.crop!==o.crop||result.request?.season_id!==o.season)throw Error('Source response does not match the requested cell-year');
      if(typeof result.annual?.evaluable!=='boolean'||(result.annual.evaluable&&typeof result.annual.event_occurred!=='boolean'))throw Error('Invalid annual event result');
      annual={year:job.year,event:result.annual.evaluable?result.annual.event_occurred:null};provenance=result.provenance;
      if(result.annual.evaluable)valid++;else unavailable++;consecutiveFailures=0;
    }catch(error){
      if(controller.signal.aborted)break;
      annual={year:job.year,event:null,error:error.message};failed++;
      if(++consecutiveFailures>=3)controller.abort();
    }
    const row={cell:job.cell,phase:job.phase,years:[annual]};
    fs.appendFileSync(checkpoint,JSON.stringify({id,key:job.key,row,provenance,retrieved_at:new Date().toISOString()})+'\n');
    rows[job.key]=mergeAtlasRows(rows[job.key]?{[job.key]:rows[job.key]}:{},{[job.key]:row})[job.key];done++;
    const elapsed=(Date.now()-started)/1000;
    console.log(JSON.stringify({finished:done,scheduled:Math.min(pending,limit),valid,unavailable,failed,current:{cell:job.cell,phase:job.phase,year:job.year},elapsed_seconds:Math.round(elapsed),remaining_seconds:done>=4?Math.round(elapsed/done*(Math.min(pending,limit)-done)):null}));
  }}
  await Promise.all(Array.from({length:concurrency},worker));
  let storedFirst=first,storedLast=last;
  for(const row of Object.values(rows))for(const year of row.years){storedFirst=Math.min(storedFirst,year.year);storedLast=Math.max(storedLast,year.year);}
  const layer=packLayer(rows,{...identity,first:storedFirst,last:storedLast,generated_at:new Date().toISOString()});
  const output=path.resolve(o.output??path.join(root,'public/data/atlas'));fs.mkdirSync(output,{recursive:true});
  const serialized=JSON.stringify(layer),filename=`${id}-${sha(serialized)}.json`;
  atomic(path.join(output,filename),serialized);
  const indexFile=path.join(output,'index.json');
  const index=fs.existsSync(indexFile)?read(indexFile):{schema:'cerealrisk-atlas-index-v1',layers:[]};
  index.layers=index.layers.filter(l=>!(l.crop===o.crop&&l.season===o.season&&l.rule_id===o.rule));
  index.layers.push({...identity,first:layer.first,last:layer.last,url:'/data/atlas/'+filename,generated_at:layer.generated_at,cells:layer.cells.length});
  atomic(indexFile,JSON.stringify(index,null,2)+'\n');
  console.log(JSON.stringify({status:controller.signal.aborted?'stopped':pending>done?'checkpoint_saved':'complete',layer:path.join(output,filename),valid,unavailable,failed,pending_after_run:pending-valid-unavailable}));
  if(failed)process.exitCode=1;
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
