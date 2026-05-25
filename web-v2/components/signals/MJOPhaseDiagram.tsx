"use client";

import { useEffect, useState } from "react";
import type { ProductImageData, SignalApiResponse } from "@/lib/signals";
import { OfficialSourceBadge } from "./OfficialSourceBadge";
import { SignalFallback } from "./SignalFallback";

const SOURCE_URL = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/MJO/whindex.shtml";

export function MJOPhaseDiagram() {
  const [signal, setSignal] = useState<SignalApiResponse<ProductImageData> | null>(null);
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    fetch("/api/signals/mjo")
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
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="kicker">MJO official RMM phase-space</p>
          <h2 className="mt-2 font-display text-[24px] font-medium tracking-tightest text-ink">
            Intraseasonal tropical convection phase and amplitude
          </h2>
          <p className="mt-2 max-w-[760px] text-[12.5px] leading-relaxed text-ink-dim">
            RMM phase-space shows the current intraseasonal tropical convection state. Values outside the unit
            circle indicate an active MJO. Counter-clockwise motion indicates eastward propagation across phases 1-8.
          </p>
        </div>
        <OfficialSourceBadge source="NOAA CPC" href={SOURCE_URL} />
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
        {imageUrl && !imageFailed ? (
          <div className="overflow-hidden rounded-sm border border-line bg-white p-2">
            <img
              src={imageUrl}
              alt="NOAA CPC RMM phase-space diagram"
              className="mx-auto max-h-[640px] w-full object-contain"
              onError={() => setImageFailed(true)}
            />
          </div>
        ) : (
          <SignalFallback
            title="MJO product unavailable"
            message="The official RMM phase-space diagram could not be loaded. Open the NOAA CPC product directly."
            href={SOURCE_URL}
          />
        )}
        <div className="rounded-sm border border-line bg-bg-panel/70 p-4">
          <p className="kicker">How to read it</p>
          <ul className="mt-3 space-y-3 text-[12px] leading-relaxed text-ink-dim">
            <li>Phases 2-3: Indian Ocean convection.</li>
            <li>Phases 4-5: Maritime Continent convection.</li>
            <li>Phases 6-7: Western Pacific convection.</li>
            <li>Phases 8-1: Western Hemisphere and Africa.</li>
            <li>The unit circle separates weak from active MJO amplitude.</li>
          </ul>
        </div>
      </div>
    </section>
  );
}
