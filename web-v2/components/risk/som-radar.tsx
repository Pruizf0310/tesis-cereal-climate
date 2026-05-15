"use client";

import type { ClusterMean, SomClassSummary, TriggerCandidate } from "@/lib/types";
import { formatSigned } from "@/lib/utils";

const AXES: { key: keyof Omit<ClusterMean, "label">; label: string }[] = [
  { key: "nino12", label: "N1+2" },
  { key: "nino3", label: "N3" },
  { key: "nino34", label: "N3.4" },
  { key: "nino4", label: "N4" },
  { key: "iod_w", label: "IODw" },
  { key: "iod_e", label: "IODe" },
  { key: "tna", label: "TNA" },
  { key: "tsa", label: "TSA" }
];

// Normalize raw mean values into a small radius given expected scale (~ -0.5 to +0.5)
const MAX_ABS = 0.4;

interface RadarProps {
  mean: ClusterMean;
  summary?: SomClassSummary;
  trigger?: TriggerCandidate;
}

export function SomRadar({ mean, summary, trigger }: RadarProps) {
  const W = 260;
  const H = 240;
  const cx = W / 2;
  const cy = 110;
  const R = 78;

  const n = AXES.length;
  const angle = (i: number) => (Math.PI * 2 * i) / n - Math.PI / 2;

  const points = AXES.map((a, i) => {
    const v = (mean as any)[a.key] ?? 0;
    const r = (Math.max(-MAX_ABS, Math.min(MAX_ABS, v)) / MAX_ABS) * R;
    const sign = v >= 0;
    return {
      x: cx + Math.cos(angle(i)) * r,
      y: cy + Math.sin(angle(i)) * r,
      sign,
      label: a.label,
      raw: v
    };
  });

  const path =
    points
      .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(2)},${p.y.toFixed(2)}`)
      .join(" ") + " Z";

  // Class color rotates through a curated palette so cards feel distinct but unified
  const PALETTE = ["#7FD4DF", "#F1B257", "#7FAF7B", "#4FA0C9", "#D97B45", "#B23D3D", "#9F8CC9"];
  const color = PALETTE[mean.label % PALETTE.length];

  return (
    <article className="glass rounded-sm p-4 animate-fade-up">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="inline-block h-2 w-2 rotate-45"
            style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }}
          />
          <h3 className="font-display text-[14px] font-medium tracking-tight text-ink">
            Class {mean.label}
          </h3>
        </div>
        <span className="num text-[10.5px] text-ink-mute">
          {summary ? `${(summary.fraction * 100).toFixed(1)}%` : "—"}
        </span>
      </header>

      <svg viewBox={`0 0 ${W} ${H}`} className="mt-1 h-[210px] w-full">
        {/* Grid rings */}
        {[0.33, 0.66, 1].map((f) => (
          <circle
            key={f}
            cx={cx}
            cy={cy}
            r={R * f}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={1}
          />
        ))}
        {/* Axes */}
        {AXES.map((_, i) => {
          const a = angle(i);
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={cx + Math.cos(a) * R}
              y2={cy + Math.sin(a) * R}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth={1}
            />
          );
        })}
        {/* Mean polygon */}
        <path d={path} fill={`${color}33`} stroke={color} strokeWidth={1.4} />
        {/* Vertices */}
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={2} fill={color} />
        ))}
        {/* Axis labels */}
        {AXES.map((a, i) => {
          const an = angle(i);
          const lx = cx + Math.cos(an) * (R + 14);
          const ly = cy + Math.sin(an) * (R + 14);
          return (
            <text
              key={a.key}
              x={lx}
              y={ly + 3}
              fontSize={9}
              fill="#5B6E78"
              textAnchor="middle"
              className="num"
            >
              {a.label}
            </text>
          );
        })}
      </svg>

      <footer className="mt-2 grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-line bg-line text-[10.5px]">
        <div className="bg-bg-panel/80 px-2.5 py-1.5">
          <p className="kicker">ONI trigger</p>
          <p className="num mt-0.5 font-medium text-ink">
            {trigger ? `≥ ${formatSigned(trigger.trigger_oni_approx, 2)}` : "—"}
          </p>
        </div>
        <div className="bg-bg-panel/80 px-2.5 py-1.5">
          <p className="kicker">Yield Δ</p>
          <p className="num mt-0.5 font-medium" style={{ color }}>
            {trigger
              ? `${formatSigned(trigger.curve_min_yield, 2)} … ${formatSigned(
                  trigger.curve_max_yield,
                  2
                )}`
              : "—"}
          </p>
        </div>
      </footer>
    </article>
  );
}
