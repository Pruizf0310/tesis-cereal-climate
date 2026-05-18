"use client";

import { RISK_META } from "@/lib/types";
import { cn } from "@/lib/utils";

interface MapOverlayProps {
  cropLabel: string;
  pointCount: number;
  loading: boolean;
  error: string | null;
}

export function MapOverlay({ cropLabel, pointCount, loading, error }: MapOverlayProps) {
  return (
    <>
      {/* Top-left title card */}
      <div className="pointer-events-none absolute left-4 top-[72px] z-10 max-w-[420px] md:left-[316px]">
        <div className="pointer-events-auto glass relative rounded-sm px-4 py-3 animate-fade-up">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "flex h-1.5 w-1.5 items-center rounded-full transition-colors",
                loading
                  ? "bg-warm shadow-[0_0_8px_rgba(241,178,87,0.8)]"
                  : error
                    ? "bg-risk-extr shadow-[0_0_8px_rgba(178,61,61,0.8)]"
                    : "bg-cool shadow-[0_0_8px_rgba(127,212,223,0.8)]"
              )}
            />
            <p className="kicker">
              {loading ? "Loading layer" : error ? "Data unavailable" : "Live"}
            </p>
          </div>
          <h1 className="font-display mt-1 text-[18px] font-medium leading-tight tracking-tightest text-ink">
            Global {cropLabel.toLowerCase()} · climate exposure
          </h1>
          <p className="mt-0.5 text-[10.5px] text-ink-mute">
            Geospatial intelligence for ENSO-MJO driven agricultural risk.
          </p>
          <p className="mt-0.5 text-[11.5px] text-ink-dim">
            {error ? (
              <span className="text-risk-extr">{error}</span>
            ) : (
              <>
                <span className="num text-ink">{pointCount.toLocaleString("en-US")}</span> pixels ·
                yield-anomaly dispersion · 1981–2016
              </>
            )}
          </p>
        </div>
      </div>

      {/* Bottom-left risk legend */}
      <div className="pointer-events-none absolute bottom-[100px] left-4 z-10 hidden md:block md:left-[316px]">
        <div className="pointer-events-auto glass rounded-sm px-4 py-3 animate-fade-up">
          <p className="kicker mb-2">Climate exposure</p>
          <div className="flex h-1.5 w-[200px] overflow-hidden rounded-xs">
            {(["low", "moderate", "high", "extreme"] as const).map((r) => (
              <div
                key={r}
                className="flex-1"
                style={{ backgroundColor: RISK_META[r].color }}
              />
            ))}
          </div>
          <div className="num mt-1.5 flex justify-between text-[9.5px] text-ink-mute">
            <span>0.0σ</span>
            <span>0.6</span>
            <span>1.1</span>
            <span>1.6</span>
            <span>+</span>
          </div>
        </div>
      </div>
    </>
  );
}
