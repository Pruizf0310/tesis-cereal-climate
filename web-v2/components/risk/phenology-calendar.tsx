"use client";
import { useEffect, useState } from 'react';
import { coordinateKey, pixelWindows, referenceDate, type PixelCalendarData, type PixelCalendarManifest } from '@/lib/pixel-phenology';

const colors = ['#7FD4DF','#76B7C5','#7FAF7B','#A7C957','#D7B45A','#D98B57'];
const input = 'rounded-sm border border-line bg-bg-panel px-3 py-2 text-[12px] text-ink';

export function PhenologyCalendar() {
  const [manifest,setManifest]=useState<PixelCalendarManifest|null>(null);
  const [crop,setCrop]=useState('maize');
  const [season,setSeason]=useState('maize__rf');
  const [data,setData]=useState<PixelCalendarData|null>(null);
  const [lat,setLat]=useState('5.25');
  const [lon,setLon]=useState('-75.25');
  const [error,setError]=useState('');
  useEffect(()=>{fetch('/data/pixel-calendars/manifest.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(setManifest).catch(()=>setError('Calendar metadata could not be loaded.'));},[]);
  useEffect(()=>{
    const entry=manifest?.crops[crop]?.seasons[season];
    if(!entry)return;
    let active=true; setData(null); setError('');
    fetch(entry.url).then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>{if(active)setData(d);}).catch(()=>{if(active)setError('Coordinate calendar could not be loaded.');});
    return ()=>{active=false;};
  },[manifest,crop,season]);
  function selectCrop(value:string){setCrop(value);const choices=Object.keys(manifest?.crops[value]?.seasons??{});setSeason(choices.find(s=>s.endsWith('__rf'))??choices[0]??'');}
  const exactCentre=lat.trim()!==''&&lon.trim()!==''&&Number.isFinite(Number(lat))&&Number.isFinite(Number(lon))&&Number(lat)>=-89.75&&Number(lat)<=89.75&&Number(lon)>=-179.75&&Number(lon)<=179.75&&Number.isInteger((Number(lat)-.25)*2)&&Number.isInteger((Number(lon)-.25)*2);
  const windows=data&&exactCentre?pixelWindows(data,Number(lat),Number(lon)):[];
  const tuple=data?.pixels[coordinateKey(Number(lat),Number(lon))];
  return <div className="mt-6 rounded-sm border border-line glass">
    <div className="flex flex-wrap items-end gap-3 border-b border-line p-4">
      <label className="grid gap-1 text-[11px] text-ink-mute">Crop<select aria-label="Calendar crop" className={input} value={crop} onChange={e=>selectCrop(e.target.value)}>{Object.entries(manifest?.crops??{}).map(([id,c])=><option key={id} value={id}>{c.label}</option>)}</select></label>
      <label className="grid gap-1 text-[11px] text-ink-mute">Season / water system<select aria-label="Calendar season" className={input} value={season} onChange={e=>setSeason(e.target.value)}>{Object.entries(manifest?.crops[crop]?.seasons??{}).map(([id,s])=><option key={id} value={id}>{s.label} · {s.water_label}</option>)}</select></label>
      <label className="grid gap-1 text-[11px] text-ink-mute">Pixel centre latitude<input aria-label="Calendar latitude" className={input+' w-32'} type="number" min="-89.75" max="89.75" step="0.5" value={lat} onChange={e=>setLat(e.target.value)}/></label>
      <label className="grid gap-1 text-[11px] text-ink-mute">Pixel centre longitude<input aria-label="Calendar longitude" className={input+' w-32'} type="number" min="-179.75" max="179.75" step="0.5" value={lon} onChange={e=>setLon(e.target.value)}/></label>
    </div>
    <p className="border-b border-line p-4 text-[12px] leading-relaxed text-ink-dim">One coordinate, one consecutive sequence from planting to maturity. Intermediate dates are estimated from the archived crop template. Where a boundary cannot be separated, macro-phases form one combined interval with multiple applicable hazard rules. Intervals never overlap and every cycle day belongs to exactly one interval. Year 0 is the planting year.</p>
    {error?<p className="p-4 text-warm">{error}</p>:!data?<p className="p-4 text-ink-mute">Loading coordinate calendars…</p>:!windows.length?<p className="p-4 text-warm">No calendar exists at this exact coordinate for the selected crop and season. Use a 0.5° grid centre (for example, 5.25, −75.25). No latitude-band average or neighbouring pixel is substituted.</p>:<>
      <div className="p-4 text-[12px] text-ink-dim">Pixel {lat}, {lon} · Cycle: {tuple![1]} days in the reference calendar · Timing uncertainty recorded in the source: ±{tuple![2]} days</div>
      <div className="overflow-x-auto"><table className="w-full min-w-[850px] text-left text-[12px]">
        <thead className="border-y border-line text-ink-mute"><tr><th className="p-3">Macro-phase / original stages</th><th className="p-3">Reference dates</th><th className="p-3">Days</th><th className="w-[38%] p-3">Continuous interval · day 0 to {tuple![1]} after planting</th></tr></thead>
        <tbody>{[...windows].sort((a,b)=>a.start_offset-b.start_offset||a.phase_order-b.phase_order).map(w=><tr key={w.phase_code} className="border-b border-line/50">
          <td className="p-3"><span className="font-medium text-cool">{w.phase_code} — {w.phase_label}</span><span className="mt-1 block max-w-sm text-[10px] text-ink-mute">{w.original_stages.join('; ')}</span>{w.shared&&<span className="mt-1 block max-w-sm text-[10px] text-warm">Combined interval: {w.shared_stages.join('; ')}. Internal boundary unresolved; evaluate the relevant triggers separately within this one window.</span>}</td>
          <td className="whitespace-nowrap p-3 text-ink-dim">{referenceDate(2001,w.start_doy).toISOString().slice(5,10)} Y{w.start_year_offset} → {referenceDate(2001,w.end_doy).toISOString().slice(5,10)} Y{w.end_year_offset}</td>
          <td className="p-3 text-ink">{w.duration_days}{w.shared?'*':''}</td>
          <td className="p-3"><div className="relative h-7 rounded bg-white/[0.04]" aria-label={`${w.phase_code}: days ${w.start_offset} to ${w.end_offset-1} after planting`}><div className="absolute top-0 h-7 rounded" style={{left:`${100*w.start_offset/tuple![1]}%`,width:`${100*w.duration_days/tuple![1]}%`,backgroundColor:colors[w.phase_order-1]}} /></div></td>
        </tr>)}</tbody>
      </table></div>
    </>}
    <div className="space-y-2 p-4 text-[11px] leading-relaxed text-ink-mute"><p>Source: <a className="text-cool underline" href="https://zenodo.org/records/5062513" target="_blank" rel="noreferrer">GGCMI Phase 3 v1.01 planting and maturity endpoints</a>. The papers support hazard timing and phase correspondence; they do not validate the template fractions or supply annual observed phase dates.</p><p><a className="text-cool underline" href="https://github.com/Pruizf0310/tesis-cereal-climate/blob/main/docs/pixel_calendar_method.md" target="_blank" rel="noreferrer">Method, source Excel files, estimated phases and reproducibility</a></p></div>
  </div>;
}
