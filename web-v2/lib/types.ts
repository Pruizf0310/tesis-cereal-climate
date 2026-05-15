export type Crop = "rice" | "maize" | "wheat" | "soybean";

export const CROPS: { id: Crop; label: string }[] = [
  { id: "maize", label: "Maize" },
  { id: "rice", label: "Rice" },
  { id: "wheat", label: "Wheat" },
  { id: "soybean", label: "Soybean" }
];

export type Signal = "ENSO" | "MJO" | "SST";

export const SIGNALS: { id: Signal; label: string; sublabel: string }[] = [
  { id: "ENSO", label: "ENSO", sublabel: "El Niño–Southern Oscillation · ONI" },
  { id: "MJO", label: "MJO", sublabel: "Madden–Julian Oscillation · RMM" },
  { id: "SST", label: "SST", sublabel: "Pacific surface temperature" }
];

export type RiskLevel = "low" | "moderate" | "high" | "extreme";

export const RISK_META: Record<RiskLevel, { label: string; color: string }> = {
  low: { label: "Low", color: "var(--risk-low)" },
  moderate: { label: "Moderate", color: "var(--risk-mod)" },
  high: { label: "High", color: "var(--risk-high)" },
  extreme: { label: "Extreme", color: "var(--risk-extr)" }
};

export type EnsoState = "La Niña" | "Neutral" | "El Niño";

/** Source CSV row from {crop}_puntos_utiles_interseccion.csv */
export interface CropPointRow {
  lat: number;
  lon: number;
  anos_validos: number;
  gap: number;
  longest_run: number;
  cluster_raw: number;
  cluster: number;
  std: number;
}

/** Aggregated point used by the map */
export interface CropPoint {
  id: string;
  lat: number;
  lon: number;
  cluster: number;
  std: number;
  longestRun: number;
  yearsValid: number;
  risk: RiskLevel;
}

/** Row from oni_yield_pixel_year_merged.csv */
export interface OniYieldRow {
  pixel_id: number;
  som_label: number;
  Year: number;
  oni_critical_top2: number;
  yield_anomaly: number;
}

/** Row from trigger_summary_preliminar.csv */
export interface TriggerCandidate {
  som_label: number;
  trigger_oni_approx: number;
  curve_min_yield: number;
  curve_max_yield: number;
  n_years: number;
}

/** Row from cluster_means.csv */
export interface ClusterMean {
  label: number;
  nino12: number;
  nino3: number;
  nino34: number;
  nino4: number;
  iod_w: number;
  iod_e: number;
  tna: number;
  tsa: number;
}

/** Row from som_class_summary.csv */
export interface SomClassSummary {
  label: number;
  count: number;
  fraction: number;
}

/** Row from geoglam_resumen_fases.csv */
export interface PhaseSummary {
  phase_order: number;
  phase_code: string;
  phase_name: string;
  start_marker: string;
  end_marker: string;
  records_with_phase: number;
  records_without_phase: number;
  percent_with_phase: number;
}
