"use client";

import { useEffect, useMemo, useState } from "react";
import { CROPS, type Crop, type Signal, type CropPoint, type CropPointRow } from "@/lib/types";
import { loadCsv } from "@/lib/csv";
import { normalizePoint } from "@/lib/risk";
import { LeftRail } from "./left-rail";
import { ContextPanel } from "./context-panel";
import { YearScrubber } from "./year-scrubber";
import { MapView } from "./map";
import { MapOverlay } from "./map-overlay";
import { cn } from "@/lib/utils";
import { Sprout, Waves, Wheat, ActivitySquare, X } from "lucide-react";
import { loadRiceMapLayer } from "@/components/climate/RiceMapLayer";

const YEAR_MIN = 1982;
const YEAR_MAX = 2016;

const CROP_ICON: Record<Crop, React.ReactNode> = {
  maize: <Sprout className="h-3.5 w-3.5" />,
  rice: <Waves className="h-3.5 w-3.5" />,
  wheat: <Wheat className="h-3.5 w-3.5" />,
  soybean: <ActivitySquare className="h-3.5 w-3.5" />
};

export function Explorer() {
  const [crop, setCrop] = useState<Crop>("rice");
  const [signal, setSignal] = useState<Signal>("ENSO");
  const [year, setYear] = useState<number>(2015);
  const [points, setPoints] = useState<CropPoint[]>([]);
  const [selected, setSelected] = useState<CropPoint | null>(null);
  const [hover, setHover] = useState<CropPoint | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setSelected(null);
    setHover(null);
    const loader =
      crop === "rice"
        ? loadRiceMapLayer()
        : loadCsv<CropPointRow>(`/data/${crop}.csv`).then((rows) =>
            rows.map((row, i) => normalizePoint(row, i)).filter((p): p is CropPoint => p !== null)
          );

    loader
      .then((rows) => {
        if (cancelled) return;
        setPoints(rows);
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
  }, [crop]);

  const focus = hover ?? selected;
  const panelPoint = crop === "rice" ? selected : focus;
  const cropMeta = useMemo(() => CROPS.find((c) => c.id === crop)!, [crop]);

  return (
    <section className="relative h-[100dvh] w-full overflow-hidden pt-14">
      {/* Centered map frame */}
      <div className="absolute inset-x-3 bottom-28 top-24 overflow-hidden rounded-sm border border-line-strong bg-bg-panel/80 shadow-glass map-atmosphere md:left-[316px] md:right-[396px] md:bottom-24 md:top-28">
        <MapView
          points={points}
          onHover={setHover}
          onSelect={setSelected}
          selected={selected}
        />
      </div>

      {/* Left rail — filters — desktop only */}
      <div className="pointer-events-none absolute inset-y-14 left-0 z-10 hidden md:flex w-[300px] flex-col p-4">
        <LeftRail
          crop={crop}
          onCropChange={setCrop}
          signal={signal}
          onSignalChange={setSignal}
          loading={loading}
          pointCount={points.length}
          cropLabel={cropMeta.label}
        />
      </div>

      {/* Right rail — context panel — large screens only */}
      <div className="pointer-events-none absolute inset-y-14 right-0 z-10 hidden lg:flex w-[380px] flex-col p-4">
        <ContextPanel point={panelPoint} crop={cropMeta} signal={signal} year={year} />
      </div>

      {/* Map overlays — title (TL) and legend (BR) */}
      <MapOverlay cropLabel={cropMeta.label} pointCount={points.length} loading={loading} error={error} />

      {/* Mobile crop selector — shown below md */}
      <div className="pointer-events-none absolute left-0 right-0 bottom-20 z-10 flex md:hidden justify-center px-4">
        <div className="pointer-events-auto glass rounded-sm px-3 py-2.5 flex items-center gap-1.5">
          <p className="kicker mr-1">Crop</p>
          {CROPS.map((c) => (
            <button
              key={c.id}
              onClick={() => setCrop(c.id)}
              className={cn(
                "flex items-center gap-1.5 rounded-sm border px-2.5 py-1.5 text-[11.5px] font-medium transition-all",
                crop === c.id
                  ? "border-cool/40 bg-cool/[0.08] text-ink"
                  : "border-line bg-white/[0.02] text-ink-dim"
              )}
            >
              <span className="text-cool/80">{CROP_ICON[c.id]}</span>
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Year scrubber — bottom center */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 flex justify-center p-4">
        <YearScrubber year={year} min={YEAR_MIN} max={YEAR_MAX} onChange={setYear} />
      </div>

      {/* Responsive selected-pixel sheet */}
      {panelPoint && (
        <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 flex lg:hidden">
          <div className="pointer-events-auto glass max-h-[72dvh] w-full overflow-y-auto rounded-t-sm border-x-0 border-b-0 p-4 shadow-glass">
            <button
              type="button"
              onClick={() => setSelected(null)}
              className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-sm border border-line bg-white/[0.03] text-ink-dim"
              aria-label="Close pixel detail"
            >
              <X className="h-4 w-4" />
            </button>
            <ContextPanel point={panelPoint} crop={cropMeta} signal={signal} year={year} />
          </div>
        </div>
      )}
    </section>
  );
}
