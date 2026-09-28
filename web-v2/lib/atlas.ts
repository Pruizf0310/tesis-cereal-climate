export interface AtlasYear { year: number; event: boolean | null; error?: string; }
export interface AtlasCell { cell: string; phase: string; years: AtlasYear[]; }
export const FREQUENCY_BINS = [
  {label: '0 %', color: '#e3eef8'},
  {label: '>0–20 %', color: '#bfd9ee'},
  {label: '>20–40 %', color: '#87b9da'},
  {label: '>40–60 %', color: '#4c91bf'},
  {label: '>60–80 %', color: '#23679d'},
  {label: '>80–100 %', color: '#104374'}
];
export function frequencyBin(value: number) { return value === 0 ? 0 : Math.min(5, Math.ceil(value * 5)); }
export function summarizeCell(row: AtlasCell | undefined, requested: number) {
  const years = row?.years ?? [];
  const valid = years.filter(y => typeof y.event === 'boolean');
  const events = valid.filter(y => y.event === true).length;
  return {valid: valid.length, events, completed: years.length, partial: years.length < requested,
    probability: valid.length ? events / valid.length : null};
}
export function withinBounds(cell: string, bounds: number[]) {
  const [lat, lon] = cell.split(',').map(Number);
  const [west,south,east,north] = bounds;
  if (lat < south || lat > north) return false;
  if (east-west >= 360) return true;
  return ((lon-west)%360+360)%360 <= ((east-west)%360+360)%360;
}
