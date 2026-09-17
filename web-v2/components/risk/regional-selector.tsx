'use client';
import {useEffect,useState} from 'react';
import type {PixelCalendarData,PixelCalendarManifest} from '@/lib/pixel-phenology';
import type {CalendarZone,RegionalCalendar} from '@/lib/regional-calendar';
export interface RegionSelection {crop:string;season:string;band:string;bandLabel:string;zone:CalendarZone;data:PixelCalendarData;version:string}
const field='w-full rounded-sm border border-line bg-bg-panel p-2.5 text-[12px] text-ink';
export function RegionalSelector({disabled=false,onChange}:{disabled?:boolean;onChange:(value:RegionSelection|null)=>void}){
 const [manifest,setManifest]=useState<PixelCalendarManifest|null>(null),[crop,setCrop]=useState('maize'),[season,setSeason]=useState('maize__rf');
 const [regional,setRegional]=useState<RegionalCalendar|null>(null),[data,setData]=useState<PixelCalendarData|null>(null),[band,setBand]=useState(''),[zone,setZone]=useState(''),[error,setError]=useState('');
 useEffect(()=>{fetch('/data/pixel-calendars/manifest.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(setManifest).catch(()=>setError('Could not load regional calendars.'));},[]);
 useEffect(()=>{const entry=manifest?.crops[crop]?.seasons[season];if(!entry?.regional_url)return;let active=true;setData(null);setRegional(null);onChange(null);setError('');
  Promise.all([fetch(entry.url).then(r=>{if(!r.ok)throw Error();return r.json();}),fetch(entry.regional_url).then(r=>{if(!r.ok)throw Error();return r.json();})]).then(([d,r]:[PixelCalendarData,RegionalCalendar])=>{if(!active)return;setData(d);setRegional(r);const b=r.bands.find(b=>b.id==='0')??r.bands[0];setBand(b?.id??'');setZone(b?.zones[0]?.id??'');}).catch(()=>{if(active)setError('Could not load regional calendars.');});return()=>{active=false;};
 },[manifest,crop,season,onChange]);
 const selectedBand=regional?.bands.find(b=>b.id===band),selectedZone=selectedBand?.zones.find(z=>z.id===zone);
 useEffect(()=>{if(data&&selectedZone&&selectedBand&&regional)onChange({crop,season,band,bandLabel:selectedBand.label,zone:selectedZone,data,version:regional.version});},[data,selectedZone,selectedBand,regional,crop,season,band,onChange]);
 return <div><fieldset disabled={disabled} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
  <label className="grid gap-1 text-xs text-ink-dim">Crop<select aria-label="Calendar crop" className={field} value={crop} onChange={e=>{setCrop(e.target.value);const ids=Object.keys(manifest?.crops[e.target.value]?.seasons??{});setSeason(ids.find(s=>s.endsWith('__rf'))??ids[0]);}}>{Object.entries(manifest?.crops??{}).map(([id,c])=><option key={id} value={id}>{c.label}</option>)}</select></label>
  <label className="grid gap-1 text-xs text-ink-dim">Season / water system<select aria-label="Calendar season" className={field} value={season} onChange={e=>setSeason(e.target.value)}>{Object.entries(manifest?.crops[crop]?.seasons??{}).map(([id,s])=><option key={id} value={id}>{s.label} · {s.water_label}</option>)}</select></label>
  <label className="grid gap-1 text-xs text-ink-dim">Latitude band<select aria-label="Latitude band" className={field} value={band} onChange={e=>{setBand(e.target.value);setZone(regional?.bands.find(b=>b.id===e.target.value)?.zones[0]?.id??'');}}>{regional?.bands.map(b=><option key={b.id} value={b.id}>{b.label}</option>)}</select></label>
  <label className="grid gap-1 text-xs text-ink-dim">Longitude zone / planting season<select aria-label="Longitude zone" className={field} value={zone} onChange={e=>setZone(e.target.value)}>{selectedBand?.zones.map(z=><option key={z.id} value={z.id}>{z.label} · {z.count} crop cells</option>)}</select></label>
 </fieldset>{error&&<p className="mt-3 text-sm text-warm" role="alert">{error}</p>}{!data&&!error&&<p className="mt-3 text-xs text-ink-dim">Loading crop regions…</p>}</div>;
}
