"use client";

import { useEffect, useState } from "react";
import type { OniData, SignalApiResponse } from "@/lib/signals";
import { OfficialSourceBadge } from "./OfficialSourceBadge";
import { SignalFallback } from "./SignalFallback";

const SOURCE_URL = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php";

export function ONIHistoricalChart() {
  const [signal, setSignal] = useState<SignalApiResponse<OniData> | null>(null);

  useEffect(() => {
    fetch("/api/signals/oni")
      .then((r) => r.json())
      .then(setSignal)
      .catch(() => setSignal(null));
  }, []);

  if (signal && !signal.ok) {
    return (
      <PanelShell>
        <SignalFallback
          title="ONI unavailable"
          message="The NOAA CPC ONI table could not be parsed. Open the official source to inspect the latest value."
          href={SOURCE_URL}
        />
      </PanelShell>
    );
  }

  const series = signal?.data?.series ?? [];
  const current = signal?.data?.current;
  const events = signal?.data?.events ?? [];
  const recent = series.length > 180 ? series.slice(-180) : series;
  const W = 940;
  const H = 320;
  const pad = { l: 42, r: 20, t: 24, b: 34 };
  const innerW = W - pad.l - pad.r;
  const innerH = H - pad.t - pad.b;
  const minYear = recent[0]?.year ?? 1980;
  const maxYear = recent[recent.length - 1]?.year ?? 2026;
  const yMax = 3;
  const x = (i: number) => pad.l + (i / Math.max(1, recent.length - 1)) * innerW;
  const y = (v: number) => pad.t + innerH / 2 - (v / yMax) * (innerH / 2);

  return (
    <PanelShell>
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="kicker">ENSO / ONI historical context</p>
          <h2 className="mt-2 font-display text-[24px] font-medium tracking-tightest text-ink">
            Oceanic Nino Index as interannual ENSO state
          </h2>
          <p className="mt-2 max-w-[760px] text-[12.5px] leading-relaxed text-ink-dim">
            ONI summarizes 3-month SST anomalies in Nino 3.4. Values at or above +0.5 C indicate El Nino;
            values at or below -0.5 C indicate La Nina; values between them are neutral.
          </p>
        </div>
        <OfficialSourceBadge source="NOAA CPC" href={SOURCE_URL} />
      </div>

      <div className="mt-5 overflow-hidden rounded-sm border border-line bg-white/[0.02] p-3">
        <svg viewBox={`0 0 ${W} ${H}`} className="h-[300px] w-full">
          <rect x={pad.l} y={y(0.5)} width={innerW} height={y(-0.5) - y(0.5)} fill="rgba(255,255,255,0.035)" />
          {[-2, -1, -0.5, 0, 0.5, 1, 2].map((v) => (
            <line
              key={v}
              x1={pad.l}
              x2={pad.l + innerW}
              y1={y(v)}
              y2={y(v)}
              stroke={Math.abs(v) === 0.5 ? "rgba(230,238,242,0.22)" : "rgba(255,255,255,0.08)"}
              strokeDasharray={v === 0 ? "0" : "3 4"}
            />
          ))}
          {events.map((event) => {
            const start = recent.findIndex((d) => d.year >= event.start);
            const end = recent.findIndex((d) => d.year > event.end);
            if (start < 0) return null;
            const x0 = x(start);
            const x1 = x(end > 0 ? end : recent.length - 1);
            return (
              <g key={event.label}>
                <rect
                  x={x0}
                  y={pad.t}
                  width={Math.max(4, x1 - x0)}
                  height={innerH}
                  fill={event.type === "el" ? "rgba(217,123,69,0.09)" : "rgba(79,160,201,0.10)"}
                />
                <text x={x0 + 4} y={pad.t + 12} fontSize={10} fill="#8FA4B0" className="num">
                  {event.label}
                </text>
              </g>
            );
          })}
          {recent.map((d, i) => {
            const y0 = y(0);
            const y1 = y(d.value);
            const color = d.value >= 0.5 ? "#D97B45" : d.value <= -0.5 ? "#4FA0C9" : "#5B6E78";
            return (
              <rect
                key={`${d.year}-${d.season}-${i}`}
                x={x(i) - 1.4}
                width={2.8}
                y={Math.min(y0, y1)}
                height={Math.max(1, Math.abs(y1 - y0))}
                fill={color}
                opacity={Math.abs(d.value) >= 0.5 ? 0.92 : 0.55}
              />
            );
          })}
          {[-2, -1, 0, 1, 2].map((v) => (
            <text key={v} x={pad.l - 8} y={y(v) + 3} textAnchor="end" fontSize={10} fill="#5B6E78" className="num">
              {v > 0 ? `+${v}` : v}
            </text>
          ))}
          {[minYear, 1990, 2000, 2010, 2020, maxYear].map((yr) => {
            const i = recent.findIndex((d) => d.year >= yr);
            if (i < 0) return null;
            return (
              <text key={yr} x={x(i)} y={H - 10} textAnchor="middle" fontSize={10} fill="#5B6E78" className="num">
                {yr}
              </text>
            );
          })}
        </svg>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-3">
        <Metric label="Latest ONI" value={current ? `${current.value > 0 ? "+" : ""}${current.value.toFixed(1)} C` : "loading"} />
        <Metric label="ENSO state" value={current?.state ?? "latest available"} />
        <Metric label="Season" value={current ? `${current.season} ${current.year}` : "NOAA CPC"} />
      </div>
    </PanelShell>
  );
}

function PanelShell({ children }: { children: React.ReactNode }) {
  return <section className="glass rounded-sm p-5 md:p-6">{children}</section>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-sm border border-line bg-bg-panel/70 p-3">
      <p className="kicker">{label}</p>
      <p className="num mt-1 text-[15px] font-medium text-ink">{value}</p>
    </div>
  );
}
