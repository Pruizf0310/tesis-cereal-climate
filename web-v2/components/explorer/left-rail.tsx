"use client";

import { CROPS, SIGNALS, type Crop, type Signal } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Wheat, Sprout, Waves, ActivitySquare, Layers } from "lucide-react";

const CROP_ICON: Record<Crop, React.ReactNode> = {
  maize: <Sprout className="h-3.5 w-3.5" />,
  rice: <Waves className="h-3.5 w-3.5" />,
  wheat: <Wheat className="h-3.5 w-3.5" />,
  soybean: <ActivitySquare className="h-3.5 w-3.5" />
};

interface LeftRailProps {
  crop: Crop;
  onCropChange: (c: Crop) => void;
  signal: Signal;
  onSignalChange: (s: Signal) => void;
  loading: boolean;
  pointCount: number;
  cropLabel: string;
}

export function LeftRail({
  crop,
  onCropChange,
  signal,
  onSignalChange,
  loading,
  pointCount,
  cropLabel
}: LeftRailProps) {
  return (
    <aside className="pointer-events-auto glass relative h-full overflow-y-auto rounded-sm p-5 animate-fade-up">
      <div className="space-y-1">
        <p className="kicker">Layer controls</p>
        <h2 className="font-display text-[15px] font-medium tracking-tighter text-ink">
          Climate scenario
        </h2>
      </div>

      {/* CROP */}
      <div className="mt-6 space-y-2.5">
        <p className="kicker">Crop</p>
        <div className="grid grid-cols-2 gap-1.5">
          {CROPS.map((c) => (
            <button
              key={c.id}
              onClick={() => onCropChange(c.id)}
              className={cn(
                "flex items-center gap-2 rounded-sm border px-2.5 py-2 text-left text-[12px] font-medium transition-all",
                crop === c.id
                  ? "border-cool/40 bg-cool/[0.08] text-ink"
                  : "border-line bg-white/[0.02] text-ink-dim hover:border-line-strong hover:bg-white/[0.04] hover:text-ink"
              )}
            >
              <span className="text-cool/80">{CROP_ICON[c.id]}</span>
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* SIGNAL */}
      <div className="mt-5 space-y-2.5">
        <p className="kicker">Climate signal</p>
        <div className="space-y-1">
          {SIGNALS.map((s) => {
            const enabled = s.id === "ENSO";
            return (
              <button
                key={s.id}
                disabled={!enabled}
                onClick={() => onSignalChange(s.id)}
                className={cn(
                  "group flex w-full items-center justify-between rounded-sm border px-3 py-2.5 text-left transition-all",
                  signal === s.id && enabled
                    ? "border-cool/40 bg-cool/[0.08]"
                    : enabled
                      ? "border-line bg-white/[0.02] hover:border-line-strong hover:bg-white/[0.04]"
                      : "cursor-not-allowed border-line/50 bg-transparent opacity-50"
                )}
              >
                <div className="flex flex-col">
                  <span
                    className={cn(
                      "text-[12.5px] font-medium",
                      signal === s.id && enabled ? "text-ink" : "text-ink-dim"
                    )}
                  >
                    {s.label}
                  </span>
                  <span className="text-[10.5px] text-ink-mute">{s.sublabel}</span>
                </div>
                {!enabled && (
                  <span className="rounded-xs border border-line bg-white/[0.02] px-1.5 py-0.5 text-[9px] uppercase tracking-wider text-ink-mute">
                    soon
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* LAYERS */}
      <div className="mt-5 space-y-2.5">
        <p className="kicker flex items-center gap-1.5">
          <Layers className="h-3 w-3" /> Layers
        </p>
        <div className="space-y-1">
          {[
            { id: "points", label: "Crop pixel grid", on: true },
            { id: "som", label: "SOM class", on: false },
            { id: "phenology", label: "Phenology band", on: false },
            { id: "triggers", label: "Trigger candidates", on: false }
          ].map((l) => (
            <div
              key={l.id}
              className={cn(
                "flex items-center justify-between rounded-sm border px-3 py-2 text-[12px]",
                l.on
                  ? "border-cool/30 bg-cool/[0.05] text-ink"
                  : "border-line bg-white/[0.02] text-ink-dim"
              )}
            >
              <span>{l.label}</span>
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  l.on ? "bg-cool shadow-[0_0_8px_rgba(127,212,223,0.8)]" : "bg-ink-mute/40"
                )}
              />
            </div>
          ))}
        </div>
      </div>

      {/* DATA STATUS */}
      <div className="mt-6 border-t border-line pt-4">
        <p className="kicker mb-2">Loaded</p>
        <div className="flex items-baseline justify-between">
          <span className="num text-2xl font-medium text-ink">
            {loading ? "—" : pointCount.toLocaleString("en-US")}
          </span>
          <span className="text-[11px] text-ink-mute">{cropLabel.toLowerCase()} pixels</span>
        </div>
        <p className="mt-1 text-[10.5px] leading-snug text-ink-mute">
          1981–2016 GDHY × SOM intersection, filtered to pixels with at least 30 valid years and run-length ≥ 25.
        </p>
      </div>
    </aside>
  );
}
