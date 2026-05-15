"use client";

import type { TriggerCandidate } from "@/lib/types";
import { formatSigned } from "@/lib/utils";

interface CurveProps {
  triggers: TriggerCandidate[];
}

const PALETTE = ["#7FD4DF", "#F1B257", "#7FAF7B", "#4FA0C9", "#D97B45", "#B23D3D", "#9F8CC9"];

export function OniYieldCurve({ triggers }: CurveProps) {
  const W = 1200;
  const H = 360;
  const PAD = { t: 20, r: 30, b: 36, l: 50 };
  const innerW = W - PAD.l - PAD.r;
  const innerH = H - PAD.t - PAD.b;

  // axis ranges
  const oniMin = -2.5;
  const oniMax = 2.5;
  const yMin = -1;
  const yMax = 0.5;
  const x = (o: number) =>
    PAD.l + ((o - oniMin) / (oniMax - oniMin)) * innerW;
  const y = (v: number) => PAD.t + ((yMax - v) / (yMax - yMin)) * innerH;

  return (
    <div className="mt-6 overflow-hidden rounded-sm border border-line glass animate-fade-up">
      <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full">
        {/* grid */}
        {[-2, -1, 0, 1, 2].map((v) => (
          <line
            key={`gx-${v}`}
            x1={x(v)}
            x2={x(v)}
            y1={PAD.t}
            y2={H - PAD.b}
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={1}
            strokeDasharray={v === 0 ? "0" : "2 3"}
          />
        ))}
        {[-1, -0.5, 0, 0.5].map((v) => (
          <line
            key={`gy-${v}`}
            x1={PAD.l}
            x2={W - PAD.r}
            y1={y(v)}
            y2={y(v)}
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={1}
            strokeDasharray={v === 0 ? "0" : "2 3"}
          />
        ))}

        {/* zero baseline */}
        <line
          x1={PAD.l}
          x2={W - PAD.r}
          y1={y(0)}
          y2={y(0)}
          stroke="rgba(255,255,255,0.18)"
          strokeWidth={1}
        />

        {/* per-class boxes */}
        {triggers.map((t) => {
          const c = PALETTE[t.som_label % PALETTE.length];
          const x0 = x(Math.max(t.trigger_oni_approx, oniMin));
          const x1 = x(oniMax);
          const yTop = y(t.curve_max_yield);
          const yBot = y(t.curve_min_yield);
          return (
            <g key={t.som_label}>
              {/* range */}
              <rect
                x={x0}
                y={yTop}
                width={x1 - x0}
                height={yBot - yTop}
                fill={c}
                fillOpacity={0.08}
                stroke={c}
                strokeOpacity={0.4}
                strokeWidth={1}
              />
              {/* threshold line */}
              <line
                x1={x0}
                x2={x0}
                y1={PAD.t}
                y2={H - PAD.b}
                stroke={c}
                strokeOpacity={0.65}
                strokeWidth={1}
                strokeDasharray="3 4"
              />
              {/* threshold label */}
              <text
                x={x0 + 4}
                y={PAD.t + 12}
                fontSize={10}
                fill={c}
                className="num"
              >
                {`C${t.som_label} · ≥${formatSigned(t.trigger_oni_approx, 2)}`}
              </text>
            </g>
          );
        })}

        {/* axes labels */}
        {[-2, -1, 0, 1, 2].map((v) => (
          <text
            key={`xl-${v}`}
            x={x(v)}
            y={H - PAD.b + 16}
            fontSize={10}
            fill="#5B6E78"
            textAnchor="middle"
            className="num"
          >
            {v > 0 ? `+${v}` : v}
          </text>
        ))}
        <text x={(PAD.l + W - PAD.r) / 2} y={H - 6} fontSize={10} fill="#8FA4B0" textAnchor="middle">
          Critical-season ONI (°C)
        </text>

        {[-1, -0.5, 0, 0.5].map((v) => (
          <text
            key={`yl-${v}`}
            x={PAD.l - 8}
            y={y(v) + 3}
            fontSize={10}
            fill="#5B6E78"
            textAnchor="end"
            className="num"
          >
            {v > 0 ? `+${v}` : v}
          </text>
        ))}
        <text
          x={14}
          y={(PAD.t + H - PAD.b) / 2}
          fontSize={10}
          fill="#8FA4B0"
          textAnchor="middle"
          transform={`rotate(-90 14 ${(PAD.t + H - PAD.b) / 2})`}
        >
          Yield anomaly (σ)
        </text>
      </svg>
    </div>
  );
}
