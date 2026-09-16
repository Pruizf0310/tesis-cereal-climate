export interface TriggerSpec {
 dataset:string; resolution:'day'|'hour'; band:string; operator:'>'|'>='|'<'|'<=';
 threshold:number; min_samples:number; unit:string; mode:'run'|'rolling_mean';
 interpretation:string; conversion:'kelvin_to_celsius'|'metres_to_mm';
}
export interface AuditedRule {
 rule_id:string; crop:string; hazard:string; phases:string[]; threshold:string; exposure:string|null;
 status:'operational'|'unavailable'; reason:string; spec:TriggerSpec|null;
 evidence_category:string; source:string; doi:string; limitations:string;
 assignments:unknown[];
}
export interface Sample {time:number; value:number|null}
export interface AnnualExposure {
 year:number; start:string; end_exclusive:string; resolution:'day'|'hour'; expected_samples:number;
 available_samples:number; complete:boolean; evaluable:boolean; event_occurred:boolean|null;
 longest_run:number|null; exposure_samples:number|null;
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
 const samples=Array.from({length:count},(_,i)=>({time:+start+i*step,value:byTime.get(+start+i*step)??null}));
 const available=samples.filter(s=>s.value!==null).length;
 const complete=available===count, evaluable=complete&&count>=spec.min_samples;
 const flags=samples.map(s=>s.value!==null&&matches(s.value,spec));
 // For rolling means the event interval is the UNION of qualifying source windows.
 // Its duration is not a count of overlapping rolling windows.
 if(spec.mode==='rolling_mean') {
   flags.fill(false);
   for(let end=spec.min_samples;end<=count;end++) {
     const window=samples.slice(end-spec.min_samples,end);
     if(window.every(s=>s.value!==null)&&matches(window.reduce((n,s)=>n+s.value!,0)/spec.min_samples,spec)) {
       for(let j=end-spec.min_samples;j<end;j++) flags[j]=true;
     }
   }
 }
 const events:AnnualExposure['events']=[];
 let longest=0,runStart=-1,exposure=0;
 for(let i=0;i<=count;i++) {
   if(i<count&&flags[i]) {exposure++;if(runStart<0)runStart=i;}
   else if(runStart>=0) {
     const length=i-runStart;longest=Math.max(longest,length);
     if(length>=spec.min_samples) events.push({start:new Date(+start+runStart*step).toISOString(),end_exclusive:new Date(+start+i*step).toISOString(),duration:length});
     runStart=-1;
   }
 }
 return {year,start:start.toISOString(),end_exclusive:endExclusive.toISOString(),resolution:spec.resolution,expected_samples:count,available_samples:available,complete,evaluable,
   event_occurred:evaluable?events.length>0:null,longest_run:evaluable?longest:null,exposure_samples:evaluable?exposure:null,events:evaluable?events:[],samples};
}
export function probabilityOfExposure(annual:AnnualExposure[]) {
 const valid=annual.filter(a=>a.evaluable),events=valid.filter(a=>a.event_occurred);
 return {valid_years:valid.length,event_years:events.length,probability:valid.length?events.length/valid.length:null};
}
