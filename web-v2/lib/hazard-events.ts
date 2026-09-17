export interface TriggerSpec {
 dataset:string; resolution:'day'|'hour'; band:string; operator:'>'|'>='|'<'|'<=';
 threshold:number; min_samples:number; unit:string; mode:'run'|'rolling_mean'|'accumulated';
 interpretation:string; conversion:'kelvin_to_celsius'|'metres_to_mm'|'identity';
 profile?:'day_mean'|'night_mean'|'night_min'|'paired_mean';secondary_threshold?:number;day_hours?:number;night_start?:number;window_samples?:number;
}
export interface AuditedRule {
 rule_id:string; crop:string; hazard:string; phases:string[]; threshold:string; exposure:string|null;
 status:'operational'|'unavailable'|'external'; reason:string; spec:TriggerSpec|null;
 equivalence?:{variable:string;equation:string;access:'gee'|'import';equivalence:string;duration_basis:string;note:string;csv_variable:string;evidence_update:string|null};
 evidence_category:string; source:string; doi:string; limitations:string;
 assignments:unknown[];
}
export interface Sample {time:number; value:number|null;secondary_value?:number|null;threshold_exceeded?:boolean|null;excess?:number|null;in_qualifying_event?:boolean}
// Disaggregated rainfall at t describes (t - 1 hour, t]; temperature is instantaneous.
export function sourceTimestampOffset(spec:TriggerSpec){return spec.band==='total_precipitation_hourly'?3600000:0;}
export interface AnnualExposure {
 year:number; start:string; end_exclusive:string; resolution:'day'|'hour'; expected_samples:number;
 available_samples:number; complete:boolean; evaluable:boolean; event_occurred:boolean|null;
 longest_run:number|null; observed_longest_run?:number|null; exposure_samples:number|null;
 events:{start:string;end_exclusive:string;duration:number}[];
 samples:Sample[];
}
function matches(v:number,s:TriggerSpec) {
 return s.operator==='>'?v>s.threshold:s.operator==='>='?v>=s.threshold:s.operator==='<'?v<s.threshold:v<=s.threshold;
}
/** Reindex first. Missing/invalid timestamps must never join separate exposures. */
export function evaluateExposure(year:number,start:Date,endExclusive:Date,raw:Sample[],spec:TriggerSpec):AnnualExposure {
 const step=spec.resolution==='hour'?3600000:86400000;
 const count=(+endExclusive-+start)/step;
 if(!Number.isInteger(count)||count<1||!Number.isInteger(spec.min_samples)||spec.min_samples<1) throw Error('Invalid evaluation interval');
 const byTime=new Map<number,number|null>();
 for(const sample of raw) {
   if(sample.time<+start||sample.time>=+endExclusive) continue;
   if((sample.time-+start)%step!==0||byTime.has(sample.time)) throw Error('Duplicate or off-grid GEE timestamp');
 byTime.set(sample.time,typeof sample.value==='number'&&Number.isFinite(sample.value)&&!(spec.conversion==='metres_to_mm'&&sample.value<0)?sample.value:null);
 }
 const secondary=new Map(raw.map(s=>[s.time,s.secondary_value]));
 const samples:Sample[]=Array.from({length:count},(_,i)=>{const time=+start+i*step;let value=byTime.get(time)??null;const second=secondary.get(time);if(spec.secondary_threshold!==undefined&&(typeof second!=='number'||!Number.isFinite(second)))value=null;return {time,value,...(spec.secondary_threshold!==undefined?{secondary_value:second??null}:{})};});
 const available=samples.filter(s=>s.value!==null).length;
 const complete=available===count, evaluable=complete&&count>=Math.max(spec.min_samples,spec.window_samples??1);
 const flags=samples.map(s=>s.value!==null&&matches(s.value,spec)&&(spec.secondary_threshold===undefined||s.secondary_value!>=spec.secondary_threshold));
 samples.forEach((s,i)=>{s.threshold_exceeded=s.value===null?null:flags[i];s.excess=s.value===null?null:Math.max(0,(spec.operator.startsWith('<')?-1:1)*(s.value-spec.threshold));});
 // For rolling means the event interval is the UNION of qualifying source windows.
 // Its duration is not a count of overlapping rolling windows.
 if(spec.mode==='rolling_mean') {
   flags.fill(false);
   const width=spec.window_samples??spec.min_samples;
   for(let end=width;end<=count;end++) {
     const window=samples.slice(end-width,end);
     if(window.every(s=>s.value!==null)&&matches(window.reduce((n,s)=>n+s.value!,0)/width,spec)) {
       for(let j=end-width;j<end;j++) flags[j]=true;
     }
   }
 }
 const events:AnnualExposure['events']=[];
 let longest=0,runStart=-1,exposure=0;
 for(let i=0;i<=count;i++) {
   if(i<count&&flags[i]) {exposure++;if(runStart<0)runStart=i;}
   else if(runStart>=0) {
     const length=i-runStart;longest=Math.max(longest,length);
     if(length>=spec.min_samples||spec.mode==='accumulated') events.push({start:new Date(+start+runStart*step).toISOString(),end_exclusive:new Date(+start+i*step).toISOString(),duration:length});
     runStart=-1;
   }
 }
 const occurred=spec.mode==='accumulated'?exposure>=spec.min_samples:events.length>0;
 samples.forEach(s=>{s.in_qualifying_event=evaluable&&occurred&&events.some(e=>s.time>=Date.parse(e.start)&&s.time<Date.parse(e.end_exclusive));});
 return {year,start:start.toISOString(),end_exclusive:endExclusive.toISOString(),resolution:spec.resolution,expected_samples:count,available_samples:available,complete,evaluable,
   event_occurred:evaluable?occurred:null,longest_run:evaluable?longest:null,observed_longest_run:complete?longest:null,exposure_samples:complete?exposure:null,events:evaluable?events:[],samples};
}
/** Fixed local solar-clock day/night cycles, beginning at 06:00; no split night. */
export function profileBounds(start:Date,end:Date,spec:TriggerSpec,lon:number){
 const solarOffsetHours=spec.profile?Math.round(lon/15):0;
 const shift=spec.profile?(6-solarOffsetHours)*3600000:0;
 return {start:new Date(+start+shift),endExclusive:new Date(+end+shift),solarOffsetHours};
}
export function aggregateProfile(raw:Sample[],start:Date,end:Date,spec:TriggerSpec):Sample[]{
 if(!spec.profile)return raw;
 const map=new Map<number,Sample>();for(const s of raw){if(map.has(s.time))throw Error('Duplicate source timestamp');map.set(s.time,s);}
 const output:Sample[]=[];
 for(let time=+start;time<+end;time+=86400000){
  const dayHours=spec.day_hours??12;
  const day=Array.from({length:dayHours},(_,i)=>map.get(time+i*3600000)?.value??null);
  const night=Array.from({length:24-dayHours},(_,i)=>map.get(time+(dayHours+i)*3600000)?.value??null);
  const mean=(v:(number|null)[])=>v.every(n=>typeof n==='number'&&Number.isFinite(n))?v.reduce<number>((a,b)=>a+b!,0)/v.length:null;
  const dm=mean(day),nm=mean(night);
  output.push({time,value:spec.profile==='day_mean'||spec.profile==='paired_mean'?dm:spec.profile==='night_min'?(nm===null?null:Math.min(...night as number[])):nm,...(spec.profile==='paired_mean'?{secondary_value:nm}:{})});
 }
 return output;
}
export function probabilityOfExposure(annual:AnnualExposure[]) {
 const valid=annual.filter(a=>a.evaluable),events=valid.filter(a=>a.event_occurred);
 return {valid_years:valid.length,event_years:events.length,probability:valid.length?events.length/valid.length:null};
}
