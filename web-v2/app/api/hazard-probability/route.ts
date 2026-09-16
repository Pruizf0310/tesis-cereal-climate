import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {NextResponse} from 'next/server';
import {pixelWindows,phaseDates,coordinateKey,type PixelCalendarData,type PixelCalendarManifest} from '@/lib/pixel-phenology';
import {evaluateExposure,sourceTimestampOffset,type AuditedRule,type Sample} from '@/lib/hazard-events';
export const runtime='nodejs';
export const dynamic='force-dynamic';
export const maxDuration=300;
const require=createRequire(import.meta.url);
const ee=require('@google/earthengine');
const read=(name:string)=>JSON.parse(readFileSync(join(process.cwd(),'public','data',name),'utf8'));
let initialized:Promise<void>|null=null;
function initialize() {
 if(initialized)return initialized;
 const project=process.env.GOOGLE_CLOUD_PROJECT,email=process.env.GEE_SERVICE_ACCOUNT_EMAIL,key=process.env.GEE_SERVICE_ACCOUNT_PRIVATE_KEY?.replace(/\\n/g,'\n');
 if(!project||!email||!key)throw Error('GEE credentials are not configured on this server.');
 initialized=new Promise<void>((resolve,reject)=>ee.data.authenticateViaPrivateKey({client_email:email,private_key:key,project_id:project},()=>ee.initialize(null,null,resolve,reject,null,project),reject)).catch(e=>{initialized=null;throw e;});
 return initialized;
}
function info<T>(value:any):Promise<T>{return new Promise((resolve,reject)=>value.getInfo((result:T,error:unknown)=>error?reject(error):resolve(result)));}
export async function GET(){
 return NextResponse.json({configured:Boolean(process.env.GOOGLE_CLOUD_PROJECT&&process.env.GEE_SERVICE_ACCOUNT_EMAIL&&process.env.GEE_SERVICE_ACCOUNT_PRIVATE_KEY),access_verified:false,message:'Configuration alone does not verify collection access. A successful POST verifies the requested collection, band, dates and cell.'});
}
export async function POST(request:Request){
 let body:any;try{body=await request.json();}catch{return NextResponse.json({error:'Invalid JSON.'},{status:400});}
 if(!body||typeof body!=='object')return NextResponse.json({error:'Invalid request.'},{status:400});
 const {crop,season_id,phase,rule_id,lat,lon,year}=body;
 const fail=(error:string)=>NextResponse.json({error},{status:400});
 if(!Number.isFinite(lat)||!Number.isFinite(lon)||lat < -89.75||lat>89.75||lon < -179.75||lon>179.75)return fail('Use a valid 0.5 degree cell centre.');
 // Exact centres only; coordinateKey rounding must not silently snap a request.
 if(Math.abs((lat-.25)*2-Math.round((lat-.25)*2))>1e-8||Math.abs((lon-.25)*2-Math.round((lon-.25)*2))>1e-8)return fail('Coordinates must be exact 0.5 degree grid centres.');
 if(!Number.isInteger(year)||year<1981||year>=new Date().getUTCFullYear())return fail('Choose a complete historical planting year from 1981 onward.');
 const manifest=read('pixel-calendars/manifest.json') as PixelCalendarManifest;
 const season=manifest.crops[crop]?.seasons?.[season_id];
 if(!season)return fail('Unknown crop or calendar season.');
 const calendar=read(season.url.replace('/data/','')) as PixelCalendarData;
 const window=pixelWindows(calendar,lat,lon).find(w=>w.phase_code===phase);
 if(!window)return fail('This exact coordinate has no selected calendar interval.');
 const audit=read('gee_rule_audit.json');
 const rule=(audit.rules as AuditedRule[]).find(r=>r.crop===crop&&r.rule_id===rule_id&&r.phases.some(p=>window.macro_phases.includes(p)));
 if(!rule||rule.status!=='operational'||!rule.spec)return fail(rule?.reason??'No audited operational trigger for this interval.');
 const spec=rule.spec,{start,endExclusive}=phaseDates(year,window);
 if(+endExclusive>Date.UTC(new Date().getUTCFullYear(),0,1))return fail('The full phase must end in a completed calendar year.');
 try{
   await initialize();
   const geometry=ee.Geometry.Rectangle([lon-.25,lat-.25,lon+.25,lat+.25],null,false);
   const sourceOffset=sourceTimestampOffset(spec);
   const collection=ee.ImageCollection(spec.dataset).filterDate(new Date(+start+sourceOffset).toISOString(),new Date(+endExclusive+sourceOffset).toISOString()).sort('system:time_start');
   // A timestamp list preserves null reductions and never compresses missing samples.
   const list=collection.toList(collection.size());
   const features=ee.FeatureCollection(list.map((item:any)=>{
     const image=ee.Image(item);let band=image.select(spec.band);
     if(spec.conversion==='metres_to_mm')band=band.updateMask(band.gte(0)).multiply(1000);
     else band=band.subtract(273.15);
     const value=band.rename('value').reduceRegion({reducer:ee.Reducer.mean(),geometry,scale:11132,maxPixels:1000000}).get('value');
     return ee.Feature(null,{time:ee.Number(image.get('system:time_start')).subtract(sourceOffset),value});
   }));
   const result=await info<{features:{properties:Sample}[]}>(features);
   const annual=evaluateExposure(year,start,endExclusive,result.features.map(f=>f.properties),spec);
   return NextResponse.json({ok:true,audit_version:'2026-09-16',request:{crop,season_id,phase,rule_id,lat,lon,year},rule,window,annual,
     provenance:{commit:process.env.VERCEL_GIT_COMMIT_SHA??null,audit_inputs:audit.inputs,calendar:manifest.source,calendar_doi:manifest.source_doi,coordinate:coordinateKey(lat,lon),dataset:spec.dataset,band:spec.band,timezone:'UTC',source_timestamp_offset_ms:sourceOffset,spatial_reducer:'Mean over the selected 0.5 degree cell at 11132 m scale; not a farm observation.',calendar_timing:'Estimated climatological boundaries repeated in each planting year.',combined_interval:window.shared,uncertainty_days:calendar.pixels[coordinateKey(lat,lon)][2],retrieved_at:new Date().toISOString()}});
 }catch(error){console.error('GEE exposure query failed:',error instanceof Error?error.name:'GEE error');return NextResponse.json({error:'GEE query failed. This year is unavailable and must not count as a zero-event year.'},{status:502});}
}
