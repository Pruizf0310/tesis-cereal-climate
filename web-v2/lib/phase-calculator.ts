import type { Crop } from "./types";

export type Phase = "F1" | "F2" | "F3";

export type PhaseVariable =
  | "tmax_c"
  | "tmean_c"
  | "tmin_c"
  | "precip_mm"
  | "rootzone_sm"
  | "swvl1"
  | "swvl2"
  | "swvl3";

export interface PixelInventoryRow {
  crop: Crop;
  pixel_id_h5: number;
  lat_idx: number;
  lon_idx: number;
  lat: number;
  lon: number;
  lon_ee: number;
  lat_band: string;
  pixel_lat_min: number;
  pixel_lat_max: number;
  pixel_lon_min_ee: number;
  pixel_lon_max_ee: number;
}

export interface PhaseWindow {
  start_doy: number;
  end_doy: number;
  crosses_year: boolean;
  months: string[];
  duration_days: number | null;
}

export interface CalendarBandWindow {
  latMin: number;
  latMax: number;
  latBand: string;
  phases: Partial<Record<Phase, PhaseWindow>>;
  matchPct: number;
  coveragePct: number;
}

export interface PhaseCalendarWindows {
  source: string;
  resolution: string;
  crops: Record<
    Crop,
    {
      label: string;
      seasons: Record<string, { label: string; bands: Record<string, CalendarBandWindow> }>;
    }
  >;
}

export interface DailyPhaseValue {
  date: string;
  doy: number;
  value: number | null;
  exceeds: boolean;
}

export interface AnnualPhaseMetric {
  year: number;
  n_days: number;
  n_exceedance_days: number;
  max_value: number | null;
  mean_value: number | null;
  p95_value: number | null;
  max_consecutive_exceedance_days: number;
  event_occurred: boolean;
  daily_values?: DailyPhaseValue[];
}

export interface PhaseCalculationRequest {
  lat: number;
  lon: number;
  crop: Crop;
  phase: Phase;
  variable: PhaseVariable;
  threshold: number;
  min_days_event: number;
  start_year: number;
  end_year: number;
  pixel?: PixelInventoryRow;
  phase_window?: PhaseWindow;
}

export interface PhaseCalculationResult {
  probability: number;
  event_years: number;
  valid_years: number;
  critical_years: number[];
  years_critical?: number[];
  annual: AnnualPhaseMetric[];
  selected_year?: number;
  daily?: DailyPhaseValue[];
  source?: string;
}

export interface PhaseCalculationResponse {
  ok: boolean;
  configured: boolean;
  message?: string;
  request?: PhaseCalculationRequest;
  result?: PhaseCalculationResult;
  details?: unknown;
}

export const PHASE_VARIABLES: { id: PhaseVariable; label: string; unit: string; direction: "above" }[] = [
  { id: "tmax_c", label: "Tmax", unit: "deg C", direction: "above" },
  { id: "tmean_c", label: "Tmean", unit: "deg C", direction: "above" },
  { id: "tmin_c", label: "Tmin", unit: "deg C", direction: "above" },
  { id: "precip_mm", label: "Precipitation", unit: "mm", direction: "above" },
  { id: "rootzone_sm", label: "Root-zone soil moisture", unit: "m3/m3", direction: "above" },
  { id: "swvl1", label: "Surface soil moisture", unit: "m3/m3", direction: "above" },
  { id: "swvl2", label: "Soil moisture layer 2", unit: "m3/m3", direction: "above" },
  { id: "swvl3", label: "Soil moisture layer 3", unit: "m3/m3", direction: "above" }
];

export const MIN_DAYS_EVENT_OPTIONS: { value: number; label: string }[] = [
  { value: 1, label: "At least 1 day exceeds threshold" },
  { value: 3, label: "At least 3 days exceed threshold" },
  { value: 5, label: "At least 5 days exceed threshold" }
];

export function wrapLon180(lon: number): number {
  return ((lon + 180) % 360 + 360) % 360 - 180;
}

export function gridCenter05(value: number): number {
  return Math.floor(value * 2) / 2 + 0.25;
}

export function latBandKeyFromInventory(value: string): string {
  return value.replace(/_to_/g, "_");
}

export function csvEscape(value: unknown): string {
  const text = value == null ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}
