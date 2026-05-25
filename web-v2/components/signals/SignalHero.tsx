"use client";

import { useEffect, useState } from "react";
import type { OniData, ProductImageData, SignalApiResponse } from "@/lib/signals";
import { SignalStatusCard } from "./SignalStatusCard";

async function loadSignal<T>(path: string): Promise<SignalApiResponse<T> | null> {
  try {
    const response = await fetch(path);
    return (await response.json()) as SignalApiResponse<T>;
  } catch {
    return null;
  }
}

export function SignalHero() {
  const [oni, setOni] = useState<SignalApiResponse<OniData> | null>(null);
  const [mjo, setMjo] = useState<SignalApiResponse<ProductImageData> | null>(null);
  const [olr, setOlr] = useState<SignalApiResponse<ProductImageData> | null>(null);
  const [sst, setSst] = useState<SignalApiResponse<ProductImageData> | null>(null);

  useEffect(() => {
    loadSignal<OniData>("/api/signals/oni").then(setOni);
    loadSignal<ProductImageData>("/api/signals/mjo").then(setMjo);
    loadSignal<ProductImageData>("/api/signals/olr").then(setOlr);
    loadSignal<ProductImageData>("/api/signals/sst").then(setSst);
  }, []);

  const currentOni = oni?.data?.current;
  const oniTone = currentOni?.state === "El Nino" ? "warm" : currentOni?.state === "La Nina" ? "cool" : "neutral";

  return (
    <section className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
      <SignalStatusCard
        label="ENSO / ONI"
        value={currentOni ? `${currentOni.value > 0 ? "+" : ""}${currentOni.value.toFixed(1)} C` : "official"}
        state={currentOni ? `${currentOni.season} ${currentOni.year} · ${currentOni.state}` : "NOAA CPC product available"}
        source="NOAA CPC"
        href="https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php"
        tone={oniTone}
      />
      <SignalStatusCard
        label="MJO"
        value="RMM phase-space"
        state={mjo?.data?.statusLabel ?? "Official product available"}
        source="NOAA CPC"
        href="https://www.cpc.ncep.noaa.gov/products/precip/CWlink/MJO/whindex.shtml"
      />
      <SignalStatusCard
        label="OLR"
        value="Convection map"
        state={olr?.data?.statusLabel ?? "Official product available"}
        source="NOAA PSL"
        href="https://psl.noaa.gov/map/clim/olr.shtml"
        tone="cool"
      />
      <SignalStatusCard
        label="SST"
        value="SST anomaly"
        state={sst?.data?.statusLabel ?? "Official product available"}
        source="NOAA OSPO"
        href="https://www.ospo.noaa.gov/products/ocean/sst/anomaly/index.html"
        tone="warm"
      />
    </section>
  );
}
