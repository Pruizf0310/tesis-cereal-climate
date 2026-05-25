"use client";

import { useEffect, useState } from "react";
import type { ProductImageData, SignalApiResponse } from "@/lib/signals";
import { OfficialSourceBadge } from "./OfficialSourceBadge";
import { SignalFallback } from "./SignalFallback";

const SOURCE_URL = "https://psl.noaa.gov/map/clim/olr.shtml";

export function OLRMapPanel() {
  const [signal, setSignal] = useState<SignalApiResponse<ProductImageData> | null>(null);
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    fetch("/api/signals/olr")
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
          <p className="kicker">OLR tropical convection anomaly map</p>
          <h2 className="mt-2 font-display text-[22px] font-medium tracking-tightest text-ink">Outgoing longwave radiation</h2>
        </div>
        <OfficialSourceBadge source="NOAA PSL" href={SOURCE_URL} />
      </div>

      <div className="mt-5">
        {imageUrl && !imageFailed ? (
          <div className="overflow-hidden rounded-sm border border-line bg-white p-2">
            <img
              src={imageUrl}
              alt="NOAA CPC spatial OLR anomaly map"
              className="mx-auto w-full max-w-[540px] object-contain"
              onError={() => setImageFailed(true)}
            />
          </div>
        ) : (
          <SignalFallback
            title="Official OLR map product"
            message="Negative OLR anomalies indicate enhanced tropical convection; positive anomalies indicate suppressed convection. Use the official PSL/CPC map products for latest tropical OLR anomalies."
            href={signal?.data?.productUrl ?? SOURCE_URL}
          />
        )}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 text-[11.5px] text-ink-dim sm:grid-cols-4">
        {["Indian Ocean", "Maritime Continent", "Western Pacific", "Indo-Pacific waveguide"].map((domain) => (
          <div key={domain} className="rounded-sm border border-line bg-white/[0.02] p-2.5">
            {domain}
          </div>
        ))}
      </div>
    </section>
  );
}
