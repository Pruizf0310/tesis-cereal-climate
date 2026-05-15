import type { CropPointRow, CropPoint, RiskLevel, EnsoState } from "./types";
import { wrapLon } from "./utils";

/**
 * Classify a pixel into a 4-bin risk scale.
 *
 * The signal we have today per pixel is `std` (yield-anomaly standard deviation
 * over the historical record). Higher std → larger excursions from climatology,
 * therefore higher exposure to climate-driven shocks.
 *
 * Thresholds are stable from the empirical distribution observed in the
 * intersected crop points (see notebooks/importantes/Visualizacion_prelim).
 */
export function riskFromStd(std: number): RiskLevel {
  if (!Number.isFinite(std)) return "low";
  if (std >= 1.6) return "extreme";
  if (std >= 1.1) return "high";
  if (std >= 0.6) return "moderate";
  return "low";
}

/** Pretty label for risk bin */
export function riskLabel(r: RiskLevel): string {
  return { low: "Low", moderate: "Moderate", high: "High", extreme: "Extreme" }[r];
}

/** ENSO state from ONI value (NOAA convention: |ONI| ≥ 0.5 °C for ≥ 5 consecutive months) */
export function ensoState(oni: number): EnsoState {
  if (!Number.isFinite(oni)) return "Neutral";
  if (oni >= 0.5) return "El Niño";
  if (oni <= -0.5) return "La Niña";
  return "Neutral";
}

/** Normalize a raw CSV row to a clean CropPoint */
export function normalizePoint(row: CropPointRow, index: number): CropPoint | null {
  const lat = Number(row.lat);
  const lonRaw = Number(row.lon);
  if (!Number.isFinite(lat) || !Number.isFinite(lonRaw)) return null;
  const lon = wrapLon(lonRaw);
  const std = Number(row.std);
  const cluster = Number(row.cluster);
  return {
    id: `${index}-${lat.toFixed(3)}-${lon.toFixed(3)}`,
    lat,
    lon,
    cluster: Number.isFinite(cluster) ? cluster : -1,
    std: Number.isFinite(std) ? std : 0,
    longestRun: Number(row.longest_run) || 0,
    yearsValid: Number(row.anos_validos) || 0,
    risk: riskFromStd(std)
  };
}
