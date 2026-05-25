export interface SignalApiResponse<T = unknown> {
  ok: boolean;
  signal: "oni" | "mjo" | "olr" | "sst";
  source: string;
  sourceUrl: string;
  lastUpdated?: string | null;
  data?: T;
  error?: string;
  fallbackUrl?: string;
}

export interface OniPoint {
  season: string;
  year: number;
  value: number;
}

export interface OniData {
  current: {
    season: string;
    year: number;
    value: number;
    state: "El Nino" | "La Nina" | "Neutral";
  } | null;
  series: OniPoint[];
  events: { label: string; start: number; end: number; type: "el" | "la" }[];
}

export interface ProductImageData {
  imageUrl?: string;
  productUrl: string;
  statusLabel: string;
  interpretativeLabel: string;
}

export function ensoState(value: number): "El Nino" | "La Nina" | "Neutral" {
  if (value >= 0.5) return "El Nino";
  if (value <= -0.5) return "La Nina";
  return "Neutral";
}
