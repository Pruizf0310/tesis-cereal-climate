"use client";

import { useEffect, useState } from "react";
import type { CropPoint, RiceDetailCache, RicePixelDetail } from "@/lib/types";
import { formatCoord } from "@/lib/utils";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { ENSOResponseChart } from "./ENSOResponseChart";
import { MJOPhaseWheel } from "./MJOPhaseWheel";
import { PhenologyTimeline } from "./PhenologyTimeline";

let detailCache: RiceDetailCache | null = null;
let detailRequest: Promise<RiceDetailCache> | null = null;

async function getPixelDetail(pid: string): Promise<RicePixelDetail | null> {
  if (!detailCache) {
    if (!detailRequest) {
      detailRequest = fetch("/data/rice_detail.json").then((response) => {
        if (!response.ok) throw new Error(`Unable to load rice_detail.json (${response.status})`);
        return response.json() as Promise<RiceDetailCache>;
      });
    }
    detailCache = await detailRequest;
  }
  return detailCache[pid] ?? null;
}

function signalLabel(oniR: number | null): string {
  if (oniR == null) return "ENSO sensitivity not scored";
  if (oniR >= 0.08) return "El Nino sensitivity";
  if (oniR <= -0.08) return "La Nina sensitivity";
  return "Weak ENSO sensitivity";
}

function regionLabel(region: string): string {
  return region.replace(/_/g, " ");
}

export function PixelClimatePanel({ point }: { point: CropPoint }) {
  const [detail, setDetail] = useState<RicePixelDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getPixelDetail(point.id)
      .then((data) => {
        if (cancelled) return;
        setDetail(data);
        setLoading(false);
      })
      .catch((err: Error) => {
        if (cancelled) return;
        setError(err.message);
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [point.id]);

  if (loading && !detail) {
    return (
      <div className="mt-5 space-y-3">
        <p className="kicker">Rice pixel</p>
        <div className="h-24 rounded-sm border border-line skeleton" />
        <p className="text-[11px] text-ink-mute">Loading per-pixel climate profile...</p>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="mt-5 space-y-3">
        <p className="kicker">Rice pixel</p>
        <h2 className="num font-display text-[22px] font-medium text-ink">{formatCoord(point.lat, point.lon)}</h2>
        <p className="text-[12px] leading-relaxed text-risk-high">
          {error ?? "No detail profile was found for this pixel."}
        </p>
      </div>
    );
  }

  return (
    <div className="mt-5 flex flex-col gap-5">
      <div>
        <div className="flex items-center justify-between gap-3">
          <p className="kicker">Rice pixel</p>
          <ConfidenceBadge confidence={detail.confidence} />
        </div>
        <h2 className="num mt-1.5 font-display text-[22px] font-medium tracking-tightest text-ink">
          {formatCoord(detail.lat, detail.lon)}
        </h2>
      </div>

      <section className="space-y-2 border-t border-line pt-4">
        <p className="kicker">Dominant climate signal</p>
        <p className="text-[13px] leading-snug text-ink">
          {signalLabel(detail.oni_r)}
          <span className="num text-ink-mute"> · r={detail.oni_r == null ? "na" : detail.oni_r.toFixed(2)}</span>
        </p>
      </section>

      <section className="space-y-2 border-t border-line pt-4">
        <p className="kicker">Phenological vulnerability</p>
        <PhenologyTimeline
          sensitivePhase={detail.sensitive_phase}
          criticalMonths={detail.critical_months}
          peakMonth={detail.peak_month}
        />
      </section>

      <section className="space-y-2 border-t border-line pt-4">
        <p className="kicker">Historical ENSO behavior</p>
        <ENSOResponseChart bins={detail.oni_bins} />
      </section>

      <section className="space-y-2 border-t border-line pt-4">
        <div className="flex items-end justify-between">
          <p className="kicker">MJO interaction</p>
          <span className="text-[10.5px] text-ink-mute">
            worst phase {detail.mjo_worst_phase ?? "na"}
          </span>
        </div>
        <MJOPhaseWheel
          phaseYield={detail.mjo_phase_yield}
          riskPhases={detail.mjo_risk_phases}
          worstPhase={detail.mjo_worst_phase}
        />
      </section>

      <section className="space-y-2 border-t border-line pt-4">
        <p className="kicker">Convective domain</p>
        <div className="rounded-sm border border-line bg-white/[0.02] p-3">
          <div className="flex items-center justify-between gap-3">
            <span className="capitalize text-[13px] text-ink">{regionLabel(detail.olr_region)}</span>
            <span className="num text-[12px] text-ink-dim">
              r={detail.olr_r == null ? "na" : detail.olr_r.toFixed(2)}
            </span>
          </div>
          <p className="mt-2 text-[10.5px] leading-snug text-ink-mute">
            MJO and OLR coherence:{" "}
            <span className={detail.mjo_olr_coherent ? "text-crop" : "text-warm"}>
              {detail.mjo_olr_coherent ? "consistent" : "not confirmed"}
            </span>
          </p>
        </div>
      </section>
    </div>
  );
}
