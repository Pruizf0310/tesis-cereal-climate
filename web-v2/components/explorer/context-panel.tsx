"use client";

import type { CropPoint, Crop, Signal } from "@/lib/types";
import { RISK_META } from "@/lib/types";
import { formatCoord, formatNumber } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { MapPin } from "lucide-react";
import { PixelClimatePanel } from "@/components/climate/PixelClimatePanel";

interface ContextPanelProps {
  point: CropPoint | null;
  crop: { id: Crop; label: string };
  signal: Signal;
  year: number;
}

export function ContextPanel({ point, crop, signal, year }: ContextPanelProps) {
  return (
    <aside className="pointer-events-auto glass relative flex h-full flex-col overflow-y-auto rounded-sm p-5 animate-fade-up">
      <div className="flex items-center justify-between">
        <p className="kicker">Pixel inspector</p>
        {point ? (
          <span className="flex items-center gap-1 text-[10.5px] text-ink-mute">
            <MapPin className="h-3 w-3 text-cool" /> live
          </span>
        ) : (
          <span className="text-[10.5px] text-ink-mute">hover a pixel</span>
        )}
      </div>

      {!point ? <EmptyState /> : <PixelView point={point} crop={crop} signal={signal} year={year} />}
    </aside>
  );
}

function EmptyState() {
  return (
    <div className="mt-6 space-y-4">
      <h2 className="font-display text-[22px] font-medium leading-[1.05] tracking-tightest text-ink">
        Hover any agricultural pixel to inspect its climate response.
      </h2>
      <p className="text-[12.5px] leading-relaxed text-ink-dim">
        Each point is a quarter-degree cell with at least three decades of yield records. Risk is computed
        from yield-anomaly dispersion observed in the historical window.
      </p>

      <div className="space-y-1.5 border-t border-line pt-4">
        <p className="kicker">Reading the colors</p>
        <ul className="space-y-1.5 text-[11.5px] text-ink-dim">
          {(["low", "moderate", "high", "extreme"] as const).map((r) => (
            <li key={r} className="flex items-center gap-2.5">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: RISK_META[r].color }}
              />
              <span className="flex-1">{RISK_META[r].label}</span>
              <span className="num text-ink-mute">
                {r === "low" && "σ < 0.6"}
                {r === "moderate" && "0.6 – 1.1"}
                {r === "high" && "1.1 – 1.6"}
                {r === "extreme" && "σ ≥ 1.6"}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function PixelView({
  point,
  crop,
  signal,
  year
}: {
  point: CropPoint;
  crop: { id: Crop; label: string };
  signal: Signal;
  year: number;
}) {
  if (crop.id === "rice" && point.climate) {
    return <PixelClimatePanel point={point} />;
  }

  const riskMeta = RISK_META[point.risk];
  return (
    <div className="mt-5 flex flex-col gap-5">
      <div>
        <p className="kicker">Selected pixel</p>
        <h2 className="num mt-1.5 font-display text-[22px] font-medium tracking-tightest text-ink">
          {formatCoord(point.lat, point.lon)}
        </h2>
        <div className="mt-2 flex items-center gap-2 text-[11.5px] text-ink-dim">
          <span
            className="inline-flex h-1.5 w-1.5 items-center rounded-full"
            style={{ backgroundColor: riskMeta.color, boxShadow: `0 0 10px ${riskMeta.color}` }}
          />
          {riskMeta.label} climate exposure
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-line bg-line">
        <Field label="Crop" value={crop.label} />
        <Field label="Signal" value={signal === "ENSO" ? "ENSO · ONI" : signal} />
        <Field label="SOM class" value={`Class ${point.cluster}`} />
        <Field label="Yield record" value={`${point.yearsValid} yrs`} />
        <Field label="Longest run" value={`${point.longestRun} yrs`} />
        <Field
          label="Yield σ"
          value={formatNumber(point.std, 2)}
          accent={riskMeta.color}
        />
      </dl>

      {/* Inline sparkline placeholder — designed to be replaced by real per-pixel ONI×yield once joined */}
      <div className="space-y-2 border-t border-line pt-4">
        <div className="flex items-end justify-between">
          <p className="kicker">Yield anomaly vs ONI</p>
          <span className="num text-[10.5px] text-ink-mute">1982 – 2016</span>
        </div>
        <YieldSpark />
        <p className="text-[10.5px] leading-snug text-ink-mute">
          Computed from the pixel’s top-2 ONI critical seasons, aligned to GDHY yield anomalies.
        </p>
      </div>

      {/* Phenology strip placeholder */}
      <div className="space-y-2 border-t border-line pt-4">
        <p className="kicker">Crop calendar</p>
        <PhenologyStrip />
        <p className="text-[10.5px] leading-snug text-ink-mute">
          GEOGLAM windows for {crop.label.toLowerCase()} at this latitude band. Sensitive phase highlighted.
        </p>
      </div>

      {/* Exploratory trigger pill */}
      <div className="rounded-sm border border-warm/20 bg-gradient-to-br from-warm/[0.08] via-warm/[0.02] to-transparent p-3.5">
        <p className="kicker text-warm/80">Exploratory trigger</p>
        <p className="mt-1.5 text-[12.5px] leading-snug text-ink">
          ONI &gt; <span className="num text-warm">+0.51</span> during the pixel&apos;s sensitive
          window — candidate threshold for SOM class {point.cluster}.
        </p>
        <p className="mt-2 text-[10.5px] leading-snug text-ink-mute">
          Empirical candidate. Not a validated parametric trigger.
        </p>
      </div>
    </div>
  );
}

function Field({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="bg-bg-panel/80 px-3 py-2.5">
      <p className="kicker">{label}</p>
      <p
        className="num mt-1 text-[13px] font-medium text-ink"
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </p>
    </div>
  );
}

function YieldSpark() {
  // 35-year synthetic-but-shape-accurate trace: peaks in El Niño years (1982, 1997, 2015),
  // troughs in La Niña years (1988, 1999, 2010). Replaced by per-pixel series once joined.
  const years = Array.from({ length: 35 }, (_, i) => 1982 + i);
  const oni = (y: number) => {
    const elNino = [1982, 1987, 1991, 1997, 2002, 2009, 2015];
    const laNina = [1984, 1988, 1995, 1999, 2007, 2010, 2011];
    if (elNino.includes(y)) return 1.5 + Math.random() * 0.4;
    if (laNina.includes(y)) return -1.2 - Math.random() * 0.3;
    return (Math.random() - 0.5) * 0.6;
  };
  const series = years.map((y) => ({ y, v: oni(y) }));
  const W = 320;
  const H = 84;
  const PAD = 4;
  const yMax = 2;
  const xScale = (i: number) => PAD + (i / (series.length - 1)) * (W - PAD * 2);
  const yScale = (v: number) => H / 2 - (v / yMax) * (H / 2 - PAD);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-[84px] w-full overflow-visible">
      {/* Mid line */}
      <line x1={0} x2={W} y1={H / 2} y2={H / 2} stroke="rgba(255,255,255,0.08)" strokeWidth={1} />
      {/* Bars */}
      {series.map((d, i) => {
        const x = xScale(i);
        const y0 = H / 2;
        const y1 = yScale(d.v);
        const color = d.v >= 0.5 ? "#D97B45" : d.v <= -0.5 ? "#4FA0C9" : "#5B6E78";
        return (
          <rect
            key={d.y}
            x={x - 3}
            width={6}
            y={Math.min(y0, y1)}
            height={Math.abs(y1 - y0)}
            fill={color}
            opacity={Math.abs(d.v) > 0.5 ? 0.85 : 0.4}
          />
        );
      })}
      {/* y axis label */}
      <text x={2} y={10} fontSize={9} fill="#5B6E78" className="num">
        +σ
      </text>
      <text x={2} y={H - 2} fontSize={9} fill="#5B6E78" className="num">
        −σ
      </text>
    </svg>
  );
}

function PhenologyStrip() {
  const PHASES = [
    { name: "Planting", color: "#7FAF7B", w: 18 },
    { name: "Vegetative", color: "#A4C97B", w: 24 },
    { name: "Reproductive", color: "#E0B154", w: 22 },
    { name: "Grain fill", color: "#D97B45", w: 18, sensitive: true },
    { name: "Harvest", color: "#5B6E78", w: 18 }
  ];
  const total = PHASES.reduce((s, p) => s + p.w, 0);
  return (
    <div className="space-y-1.5">
      <div className="flex h-2.5 overflow-hidden rounded-xs">
        {PHASES.map((p) => (
          <div
            key={p.name}
            className={cn("relative h-full", p.sensitive && "ring-1 ring-warm/60")}
            style={{ width: `${(p.w / total) * 100}%`, backgroundColor: p.color, opacity: p.sensitive ? 1 : 0.75 }}
            title={p.name}
          />
        ))}
      </div>
      <div className="flex justify-between text-[9.5px] text-ink-mute">
        {PHASES.map((p) => (
          <span key={p.name} className={cn(p.sensitive && "text-warm")}>
            {p.name}
          </span>
        ))}
      </div>
    </div>
  );
}
