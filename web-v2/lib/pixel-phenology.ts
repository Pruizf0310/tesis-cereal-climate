import { MACRO_PHASES } from './macro-phases';

export interface PixelCalendarManifest {
  source: string;
  source_doi: string;
  shared_window_policy: string;
  version?:string;
  crops: Record<string, {label: string; seasons: Record<string, {label: string; water_label: string; water_system: string; url: string; regional_url?:string; pixel_count: number}>}>;
}
export interface PixelCalendarData {
  crop: string;
  season_id: string;
  templates: {code: string; name: string; macro_phases: string[]; fraction_start: number; fraction_end: number; timing_basis: string}[];
  pixels: Record<string, number[]>;
}
export interface PixelPhaseWindow {
  macro_phases: string[];
  phase_code: string; phase_label: string; phase_order: number;
  start_doy: number; end_doy: number; start_year_offset: number; end_year_offset: number;
  crosses_year: boolean; duration_days: number; months: string[];
  start_offset: number; end_offset: number; shared: boolean;
  original_stages: string[]; shared_stages: string[];
}
export function coordinateKey(lat: number, lon: number) {
  const wrapped = ((lon + 180) % 360 + 360) % 360 - 180;
  return `${lat.toFixed(2)},${wrapped.toFixed(2)}`;
}
export function pixelWindows(data: PixelCalendarData, lat: number, lon: number): PixelPhaseWindow[] {
  const tuple = data.pixels[coordinateKey(lat, lon)];
  if (!tuple) return [];
  const planting = tuple[0];
  // A parent stage spanning two labels unites those labels into one temporal interval.
  // Merge whole connected macro-phases, never allocate a parent stage twice.
  let groups: string[][] = MACRO_PHASES.map(p=>[p.code]);
  for (const stage of data.templates) {
    const joined = groups.filter(g=>g.some(code=>stage.macro_phases.includes(code)));
    groups = [...groups.filter(g=>!joined.includes(g)), joined.flat()];
  }
  return groups.map((codes) => {
    codes.sort((a,b)=>MACRO_PHASES.findIndex(p=>p.code===a)-MACRO_PHASES.findIndex(p=>p.code===b));
    const matched = data.templates.map((stage, i) => ({stage, start: tuple[3+i], end: tuple[4+i]})).filter(({stage}) => stage.macro_phases.some(code=>codes.includes(code)));
    if (!matched.length) throw new Error(`Missing phase correspondence: ${data.crop}/${codes}`);
    for (let i=1; i<matched.length; i++) if (matched[i-1].end !== matched[i].start) throw new Error('Non-contiguous phase mapping');
    const start = matched[0].start, end = matched[matched.length-1].end;
    const absStart = planting-1+start, absEnd = planting-1+end-1;
    return {macro_phases:codes,phase_code: codes.join('+'), phase_label: codes.map(code=>MACRO_PHASES.find(p=>p.code===code)!.name).join(' / '), phase_order: MACRO_PHASES.findIndex(p=>p.code===codes[0])+1,
      start_doy: absStart%365+1, end_doy: absEnd%365+1,
      start_year_offset: Math.floor(absStart/365), end_year_offset: Math.floor(absEnd/365),
      crosses_year: Math.floor(absStart/365)!==Math.floor(absEnd/365), duration_days: end-start,
      months: [], start_offset:start, end_offset:end, shared: matched.some(({stage})=>stage.macro_phases.length>1),
      original_stages:matched.map(({stage})=>`${stage.code} — ${stage.name}`),
      shared_stages:matched.filter(({stage})=>stage.macro_phases.length>1).map(({stage})=>`${stage.code}: ${stage.macro_phases.join(' + ')}`)};
  }).sort((a,b)=>a.start_offset-b.start_offset);
}
// Source DOY uses a 365-day climatological calendar. Preserve month/day in leap years.
export function referenceDate(plantingYear: number, doy: number, yearOffset=0) {
  const reference = new Date(Date.UTC(2001,0,doy));
  return new Date(Date.UTC(plantingYear+yearOffset+reference.getUTCFullYear()-2001,reference.getUTCMonth(),reference.getUTCDate()));
}
export function phaseDates(plantingYear: number, phase: PixelPhaseWindow) {
  const start = referenceDate(plantingYear,phase.start_doy,phase.start_year_offset);
  // Map the exclusive boundary itself, so Feb 29 cannot fall between two phases.
  const endExclusive = referenceDate(plantingYear,phase.end_doy+1,phase.end_year_offset);
  const end = new Date(endExclusive.getTime()-86400000);
  return {start,end,endExclusive,expectedDays: Math.round((endExclusive.getTime()-start.getTime())/86400000)};
}
