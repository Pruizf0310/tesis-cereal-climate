'use client';
import {useState} from 'react';
import {pixelWindows} from '@/lib/pixel-phenology';
import {calendarDate,calendarPosition,REFERENCE_MONTHS} from '@/lib/calendar-display';
import {RegionalSelector,type RegionSelection} from './regional-selector';
const colors=['#7FD4DF','#76B7C5','#7FAF7B','#A7C957','#D7B45A','#D98B57'];

export function PhenologyCalendar(){
 const [region,setRegion]=useState<RegionSelection|null>(null);
 const key=region?.zone.representative,[lat,lon]=(key??'0,0').split(',').map(Number);
 const windows=region?pixelWindows(region.data,lat,lon):[];
 const cycle=region?.data.pixels[key??'']?.[1],first=windows[0],last=windows[windows.length-1];
 return <div className="mt-6 border border-line">
  <div className="border-b border-line p-4"><RegionalSelector onChange={setRegion}/></div>
  {region&&first&&last&&<>
   <div className="space-y-2 border-b border-line p-4 text-[12px] leading-relaxed text-ink-dim">
    <p><strong className="text-ink">{region.bandLabel} · {region.zone.label}</strong> · {region.zone.count} cells in the crop inventory.</p>
    <p>Reference cell: <strong className="text-ink">{key}</strong> · {lat<0?'Southern':'Northern'} hemisphere. The regional representative is one archived cell, not an average calendar.</p>
    <div className="grid gap-3 py-2 sm:grid-cols-3">
     <div><span className="block text-ink-mute">Reference planting</span><strong className="text-ink">{calendarDate(first.start_doy,first.start_year_offset)}</strong></div>
     <div><span className="block text-ink-mute">Reference maturity</span><strong className="text-ink">{calendarDate(last.end_doy,last.end_year_offset)}</strong></div>
     <div><span className="block text-ink-mute">Inclusive cycle</span><strong className="text-ink">{cycle} days</strong></div>
    </div>
    <p>Representative cycle: {cycle} days. Cycles across this group: {region.zone.cycle_range.join('–')} days. Calculations use each cell's own calendar.</p>
    <p className="border-l-2 border-warm pl-3"><strong className="text-ink">Reference dates, not observed annual phenology.</strong> GGCMI supplies multi-year mean planting and maturity dates, including gap-filled and spatially extrapolated values. Intermediate phase dates are project estimates from fixed crop-stage fractions; regional phase timing is not independently validated. Crop presence does not verify every season or water system.</p>
   </div>
   <div className="overflow-x-auto" tabIndex={0} aria-label="Monthly phase calendar">
    <table className="w-full min-w-[1100px] table-fixed text-left text-xs">
     <thead className="text-ink-mute"><tr>
      <th className="w-[200px] p-3">Phase / original stages</th>
      <th className="w-[195px] p-3">Estimated phase dates</th>
      <th className="w-[55px] p-2">Days</th>
      <th className="px-2 pt-3">
       <div className="grid grid-cols-2 pb-2 text-center font-normal"><span>Year 1 · planting year</span><span>Year 2</span></div>
       <div className="relative h-6" aria-label="January to December in each of two reference years">{REFERENCE_MONTHS.map(m=><span key={`${m.year}-${m.label}`} className="absolute border-l border-line text-center text-[9px] font-normal" style={{left:100*m.start/730+'%',width:100*m.days/730+'%'}}>{m.label}</span>)}</div>
      </th>
     </tr></thead>
     <tbody>{windows.map(w=>{
      const position=calendarPosition(w),start=calendarDate(w.start_doy,w.start_year_offset),end=calendarDate(w.end_doy,w.end_year_offset);
      return <tr key={w.phase_code} className="border-t border-line/50">
       <td className="p-3"><span className="font-medium text-cool">{w.phase_code} — {w.phase_label}</span><span className="mt-1 block text-[10px] text-ink-mute">{w.original_stages.join('; ')}</span></td>
       <td className="p-3 text-ink-dim"><span className="block">{start}</span><span className="block">to {end}</span></td>
       <td className="p-2 text-ink">{w.duration_days}</td>
       <td className="px-2 py-3"><div className="relative h-8 bg-white/5" aria-label={`${w.phase_code}: ${start} to ${end}; ${w.duration_days} days`}>
        {REFERENCE_MONTHS.map(m=><span key={`${m.year}-${m.label}`} aria-hidden className="absolute inset-y-0 border-l border-line/50" style={{left:100*m.start/730+'%'}}/>)}
        <span aria-hidden className="absolute inset-y-0 border-l-2 border-ink-mute" style={{left:'50%'}}/>
        <div data-phase-bar={w.phase_code} className="absolute inset-y-1 rounded-sm" title={`${w.phase_label}: ${start} to ${end}`} style={{left:position.left+'%',width:position.width+'%',backgroundColor:colors[w.phase_order-1]}}/>
       </div></td>
      </tr>;
     })}</tbody>
    </table>
   </div>
   <details className="border-t border-line p-4 text-xs text-ink-dim"><summary className="cursor-pointer text-cool">Evidence, estimates and correspondence revisions</summary><div className="mt-3 space-y-2">
    <p>All intermediate boundaries are inherited estimates from normalized technical-stage fractions. The same crop template is scaled to each local growing season; similar relative phase lengths are therefore a modelling assumption, not evidence of identical phenology across hemispheres. Six labels form an operational partition; biological processes can overlap.</p>
    <p>Source endpoint import checked against all 85,916 published calendars and the 12 original GGCMI files. No planting or maturity mismatches were found. This verifies transcription, not local agronomic validity. Cycle days include both endpoint dates; GGCMI growing-season length uses their difference.</p>
    <p>Maize: R1 → FLO; R2 early kernel development → REP; R3–R5 → FIL. Rice: panicle initiation in BBCH 30–39 → REP before flowering. Soybean: R5 through the archived R6–R7 block → FIL; the terminal R8 block → MAT. The precise R7 transition remains unresolved within the original aggregate.</p>
    <p><a className="text-cool underline" href="https://zenodo.org/records/5062513" target="_blank" rel="noreferrer">GGCMI planting/maturity source</a> · <a className="text-cool underline" href="https://github.com/Pruizf0310/tesis-cereal-climate/blob/main/docs/regional_workflow_v4.md" target="_blank" rel="noreferrer">Scientific correspondence and source history</a></p>
   </div></details>
  </>}
 </div>;
}
