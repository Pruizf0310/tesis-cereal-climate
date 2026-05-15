"use client";

import { cn } from "@/lib/utils";

const STRONG_NINO = [1982, 1997, 2015];
const STRONG_NINA = [1988, 1999, 2010];

interface YearScrubberProps {
  year: number;
  min: number;
  max: number;
  onChange: (y: number) => void;
}

export function YearScrubber({ year, min, max, onChange }: YearScrubberProps) {
  const range = max - min;
  const pct = ((year - min) / range) * 100;

  return (
    <div className="pointer-events-auto glass w-[560px] rounded-sm p-3.5 animate-fade-up">
      <div className="flex items-baseline justify-between">
        <div className="flex items-center gap-3">
          <p className="kicker">Year</p>
          <span className="num text-2xl font-medium leading-none tracking-tightest text-ink">
            {year}
          </span>
          <YearBadge year={year} />
        </div>
        <p className="text-[10.5px] text-ink-mute">1982 — 2016 · drag to scrub</p>
      </div>

      <div className="relative mt-4 h-7">
        {/* Track */}
        <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-line" />
        {/* ENSO markers */}
        {STRONG_NINO.map((y) => (
          <Marker key={`a-${y}`} year={y} min={min} max={max} color="var(--enso-nino)" />
        ))}
        {STRONG_NINA.map((y) => (
          <Marker key={`b-${y}`} year={y} min={min} max={max} color="var(--enso-nina)" />
        ))}
        {/* Filled portion */}
        <div
          className="absolute left-0 top-1/2 h-px -translate-y-1/2 bg-gradient-to-r from-cool/60 to-cool/20"
          style={{ width: `${pct}%` }}
        />
        {/* Thumb */}
        <div
          className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rotate-45 rounded-[1px] border border-cool bg-bg-deep shadow-[0_0_12px_rgba(127,212,223,0.8)]"
          style={{ left: `${pct}%` }}
        />
        <input
          aria-label="Year"
          type="range"
          min={min}
          max={max}
          step={1}
          value={year}
          onChange={(e) => onChange(Number(e.target.value))}
          className="absolute inset-0 h-full w-full cursor-ew-resize appearance-none bg-transparent opacity-0"
        />
      </div>

      {/* Decade rail */}
      <div className="mt-2 flex justify-between text-[10px] text-ink-mute">
        {[1985, 1990, 1995, 2000, 2005, 2010, 2015].map((d) => (
          <span key={d} className="num">
            {d}
          </span>
        ))}
      </div>
    </div>
  );
}

function YearBadge({ year }: { year: number }) {
  let label = "Neutral";
  let color: string = "var(--enso-neut)";
  if (STRONG_NINO.includes(year)) {
    label = "Strong El Niño";
    color = "var(--enso-nino)";
  } else if (STRONG_NINA.includes(year)) {
    label = "Strong La Niña";
    color = "var(--enso-nina)";
  }
  return (
    <span
      className={cn(
        "rounded-xs border px-1.5 py-0.5 text-[10px] font-medium tracking-tight"
      )}
      style={{ borderColor: `${color}40`, color, backgroundColor: `${color}14` }}
    >
      {label}
    </span>
  );
}

function Marker({ year, min, max, color }: { year: number; min: number; max: number; color: string }) {
  const pct = ((year - min) / (max - min)) * 100;
  return (
    <div
      className="absolute top-1/2 h-2 w-px -translate-x-1/2 -translate-y-1/2"
      style={{ left: `${pct}%`, backgroundColor: color }}
      title={`${year}`}
    />
  );
}
