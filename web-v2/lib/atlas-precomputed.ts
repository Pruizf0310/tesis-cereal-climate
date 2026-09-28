import type {AtlasCell} from './atlas';
import type {AuditedRule} from './hazard-events';

export type AtlasRows = Record<string, AtlasCell>;
export const MAX_INTERACTIVE_QUERIES = 200;
export interface AtlasLayer {
  schema: 'cerealrisk-annual-atlas-v1';
  crop: string;
  season: string;
  rule_id: string;
  signature: string;
  first: number;
  last: number;
  generated_at: string;
  // One character per planting year: event, no event, unevaluable, failed, pending.
  cells: [string, string, string][];
}
export interface AtlasLayerEntry {
  crop: string; season: string; rule_id: string; signature: string;
  first: number; last: number; url: string; generated_at: string; cells: number;
}
function canonical(value: unknown): string {
  if(value === undefined) return 'null';
  if(value === null || typeof value !== 'object') return JSON.stringify(value);
  if(Array.isArray(value)) return '['+value.map(canonical).join(',')+']';
  const record=value as Record<string,unknown>;
  return '{'+Object.keys(record).sort().map(key=>JSON.stringify(key)+':'+canonical(record[key])).join(',')+'}';
}
export function atlasSignature(rule: AuditedRule, calendarVersion?: string, calendarInputs?: unknown) {
  return canonical({rule,calendarVersion,calendarInputs,evaluator:'hazard-events-v1'});
}
export function selectYears(rows: AtlasRows, first: number, last: number): AtlasRows {
  return Object.fromEntries(Object.entries(rows).map(([key,row])=>[key,{...row,years:row.years.filter(y=>y.year>=first&&y.year<=last)}]));
}
export function mergeAtlasRows(...sources: AtlasRows[]): AtlasRows {
  const result: AtlasRows={};
  for(const source of sources) for(const row of Object.values(source)) {
    const key=`${row.cell}|${row.phase}`;
    const years=new Map((result[key]?.years??[]).map(y=>[y.year,y]));
    for(const year of row.years) {
      const previous=years.get(year.year);
      if(!previous || previous.error || !year.error) years.set(year.year,year);
    }
    result[key]={cell:row.cell,phase:row.phase,years:[...years.values()].sort((a,b)=>a.year-b.year)};
  }
  return result;
}
export function unpackLayer(input: unknown, expected: Pick<AtlasLayer,'crop'|'season'|'rule_id'|'signature'>): AtlasRows {
  if(!input||typeof input!=='object') throw Error('Invalid saved layer');
  const layer=input as AtlasLayer;
  if(layer.schema!=='cerealrisk-annual-atlas-v1'||layer.crop!==expected.crop||layer.season!==expected.season||layer.rule_id!==expected.rule_id||layer.signature!==expected.signature) throw Error('Saved layer does not match the current rule and calendar');
  if(!Number.isInteger(layer.first)||!Number.isInteger(layer.last)||layer.first<1981||layer.last<layer.first||layer.last>=new Date().getUTCFullYear()||!Array.isArray(layer.cells)) throw Error('Invalid saved layer period');
  const result: AtlasRows={};
  for(const tuple of layer.cells) {
    if(!Array.isArray(tuple)||tuple.length!==3) throw Error('Invalid saved cell');
    const [cell,phase,states]=tuple;
    if(typeof cell!=='string'||typeof phase!=='string'||typeof states!=='string') throw Error('Invalid saved cell');
    const coordinate=cell.split(',').map(Number);
    if(coordinate.length!==2||coordinate.some(n=>!Number.isFinite(n))||Math.abs(coordinate[0])>90||Math.abs(coordinate[1])>180||!phase||states.length!==layer.last-layer.first+1||/[^01uf.]/.test(states)) throw Error('Invalid annual event states');
    const key=`${cell}|${phase}`;
    if(result[key]) throw Error('Duplicate saved cell and phase');
    result[key]={cell,phase,years:[...states].flatMap((state,i)=>state==='.'?[]:[{year:layer.first+i,event:state==='1'?true:state==='0'?false:null,...(state==='f'?{error:'Previous data query failed'}:{})}])};
  }
  return result;
}
export function packLayer(rows: AtlasRows, metadata: Omit<AtlasLayer,'schema'|'cells'>): AtlasLayer {
  const cells: AtlasLayer['cells']=Object.values(rows).map(row=>{
    const byYear=new Map(row.years.map(y=>[y.year,y]));
    const states=Array.from({length:metadata.last-metadata.first+1},(_,i)=>{
      const year=byYear.get(metadata.first+i);
      return !year?'.':year.error?'f':year.event===true?'1':year.event===false?'0':'u';
    }).join('');
    return [row.cell,row.phase,states];
  });
  const layer: AtlasLayer={schema:'cerealrisk-annual-atlas-v1',...metadata,cells};
  unpackLayer(layer,metadata);
  return layer;
}
export function estimateRemaining(elapsedSeconds: number, completed: number, total: number): number|null {
  return completed>=4&&elapsedSeconds>0?Math.max(0,Math.round(elapsedSeconds/completed*(total-completed))):null;
}
export function formatDuration(seconds: number): string {
  if(seconds<60) return `${Math.round(seconds)}s`;
  if(seconds<3600) return `${Math.floor(seconds/60)}m ${Math.round(seconds%60)}s`;
  if(seconds<86400) return `${Math.floor(seconds/3600)}h ${Math.floor(seconds%3600/60)}m`;
  return `${Math.floor(seconds/86400)}d ${Math.floor(seconds%86400/3600)}h`;
}
