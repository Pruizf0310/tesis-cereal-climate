"use client";

import { useEffect, useState } from "react";
import type { ProductImageData, SignalApiResponse } from "@/lib/signals";
import { OfficialSourceBadge } from "./OfficialSourceBadge";
import { SignalFallback } from "./SignalFallback";

const SOURCE_URL = "https://www.ospo.noaa.gov/products/ocean/sst/anomaly/index.html";

export function SSTMapPanel() {
  const [signal, setSignal] = useState<SignalApiResponse<ProductImageData> | null>(null);
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    fetch("/api/signals/sst")
      .then((r) => r.json())
      .then(setSignal)
      .catch(() => setSignal(null));
  }, []);

  const imageUrl = signal?.data?.imageUrl;

  useEffect(() => {
    setImageFailed(false);
  }, [imageUrl]);

  return (
    <section className="glass rounded-sm p-5 md:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="kicker">SST anomaly map</p>
          <h2 className="mt-2 font-display text-[22px] font-medium tracking-tightest text-ink">Oceanic forcing field</h2>
        </div>
        <OfficialSourceBadge source="NOAA OSPO" href={SOURCE_URL} />
      </div>

      <p className="mt-3 text-[12.5px] leading-relaxed text-ink-dim">
        SST anomalies represent the oceanic forcing behind ENSO and related teleconnection fingerprints.
      </p>

      <div className="mt-5">
        {imageUrl && !imageFailed ? (
          <div className="overflow-hidden rounded-sm border border-line bg-white p-2">
            <img
              src={imageUrl}
              alt="NOAA OSPO global SST anomaly map"
              className="w-full object-contain"
              onError={() => setImageFailed(true)}
            />
          </div>
        ) : (
          <SignalFallback
            title="SST map unavailable"
            message="The official SST anomaly image could not be loaded. Open the NOAA OSPO product directly."
            href={SOURCE_URL}
          />
        )}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 text-[11.5px] text-ink-dim sm:grid-cols-4">
        {["Nino 3.4", "Nino 4", "Equatorial Pacific", "Indian Ocean"].map((domain) => (
          <div key={domain} className="rounded-sm border border-line bg-white/[0.02] p-2.5">
            {domain}
          </div>
        ))}
      </div>
    </section>
  );
}
