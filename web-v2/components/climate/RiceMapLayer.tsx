import type { CropPoint, RiceMapFeature, RiceMapGeoJson } from "@/lib/types";

function confidenceToRisk(conf: RiceMapFeature["properties"]["conf"]): CropPoint["risk"] {
  if (conf === "h") return "high";
  if (conf === "m") return "moderate";
  return "low";
}

export function riceFeatureToPoint(feature: RiceMapFeature, index: number): CropPoint | null {
  const [lon, lat] = feature.geometry.coordinates;
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  return {
    id: feature.properties.id || `rice-${index}`,
    lat,
    lon,
    cluster: -1,
    std: Math.abs(Number(feature.properties.dr) || 0),
    longestRun: 0,
    yearsValid: 35,
    risk: confidenceToRisk(feature.properties.conf),
    climate: feature.properties
  };
}

export async function loadRiceMapLayer(): Promise<CropPoint[]> {
  const response = await fetch("/data/rice_map.geojson");
  if (!response.ok) {
    throw new Error(`Unable to load rice_map.geojson (${response.status})`);
  }
  const geojson = (await response.json()) as RiceMapGeoJson;
  return geojson.features.map(riceFeatureToPoint).filter((p): p is CropPoint => p !== null);
}
