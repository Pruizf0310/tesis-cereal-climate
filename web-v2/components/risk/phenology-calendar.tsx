"use client";

import { useEffect, useMemo, useState } from "react";
import { ActivitySquare, Sprout, Waves, Wheat } from "lucide-react";
import { cn } from "@/lib/utils";

interface TechnicalPhase {
  code: string;
  name: string;
  order: number;
  average_duration_days: number;
  average_days_by_month: number[];
}

interface CalendarBand {
  id: string;
  season: string;
  season_label: string;
  water_system: "ir" | "rf";
  water_label: string;
  latitude_band: string;
  latitude_min: number;
  latitude_max: number;
  calendar_count: number;
  phases: TechnicalPhase[];
}

interface CropCalendar {
  id: "maize" | "rice" | "soybean" | "wheat";
  label: string;
  bands: CalendarBand[];
}

interface CalendarPayload {
  version: string;
  months: string[];
  source: string;
  warning: string;
  crops: CropCalendar[];
}

const PHASE_COLORS = ["#7FD4DF", "#76B7C5", "#7FAF7B", "#A7C957", "#D7B45A", "#D98B57", "#C08497", "#9F8CC9"];

const CROP_ICONS: Record<CropCalendar["id"], React.ReactNode> = {
  maize: <Sprout className="h-3.5 w-3.5" />,
  rice: <Waves className="h-3.5 w-3.5" />,
  soybean: <ActivitySquare className="h-3.5 w-3.5" />,
  wheat: <Wheat className="h-3.5 w-3.5" />
};

export function PhenologyCalendar() {
  const [payload, setPayload] = useState<CalendarPayload | null>(null);
  const [cropId, setCropId] = useState<CropCalendar["id"]>("maize");
  const [seasonId, setSeasonId] = useState("");
  const [waterSystem, setWaterSystem] = useState<"ir" | "rf">("rf");

  useEffect(() => {
    fetch("/data/phenology_technical_v2.json")
      .then((res) => res.json())
      .then((data: CalendarPayload) => {
        setPayload(data);
        const maize = data.crops.find((crop) => crop.id === "maize");
        setSeasonId(maize?.bands[0]?.season ?? "");
      });
  }, []);

  const crop = useMemo(() => payload?.crops.find((item) => item.id === cropId) ?? null, [payload, cropId]);
  const seasons = useMemo(
    () => Array.from(new Map((crop?.bands ?? []).map((band) => [band.season, band.season_label])).entries()),
    [crop]
  );
  const bands = useMemo(
    () => (crop?.bands ?? []).filter((band) => band.season === seasonId && band.water_system === waterSystem),
    [crop, seasonId, waterSystem]
  );

  function selectCrop(next: CropCalendar["id"]) {
    setCropId(next);
    const nextCrop = payload?.crops.find((item) => item.id === next);
    const preferred = nextCrop?.bands.find((band) => band.water_system === waterSystem) ?? nextCrop?.bands[0];
    setSeasonId(preferred?.season ?? "");
  }

  if (!payload) return <Loading />;

  return (
    <div className="mt-6 overflow-hidden rounded-sm border border-line glass animate-fade-up">
      <div className="flex flex-col gap-4 border-b border-line px-4 py-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {payload.crops.map((item) => (
            <button key={item.id} type="button" onClick={() => selectCrop(item.id)} className={cropButton(cropId === item.id)}>
              <span className="text-cool/80">{CROP_ICONS[item.id]}</span>{item.label}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select value={seasonId} onChange={(event) => setSeasonId(event.target.value)} className="h-9 rounded-sm border border-line bg-bg-panel px-3 text-[12px] text-ink outline-none">
            {seasons.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
          {(["rf", "ir"] as const).map((system) => (
            <button key={system} type="button" onClick={() => setWaterSystem(system)} className={cropButton(waterSystem === system)}>
              {system === "rf" ? "Rainfed" : "Irrigated"}
            </button>
          ))}
        </div>
      </div>

      <div className="border-b border-line bg-cool/[0.035] px-4 py-3 text-[11px] leading-relaxed text-ink-dim">
        <span className="font-medium text-ink">Technical calendar v2:</span> eight crop-specific stages reconstructed for every 0.5° calendar coordinate.
        Cells report the average number of stage-days falling in each month within the selected 10° latitude band. {payload.warning}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1320px] border-collapse">
          <thead>
            <tr className="border-b border-line text-left text-[10px] uppercase tracking-wider text-ink-mute">
              <Th>Latitude band</Th><Th>n</Th><Th>Technical stage</Th><Th>Average duration</Th>
              {payload.months.map((month) => <Th key={month}>{month}</Th>)}
            </tr>
          </thead>
          <tbody>
            {bands.flatMap((band) => band.phases.map((phase, phaseIndex) => (
              <tr key={`${band.id}-${phase.code}`} className={cn("border-b border-line/50 text-[11px] hover:bg-white/[0.02]", phaseIndex === 0 && "border-t border-t-cool/25")}>
                <Td className="font-medium text-ink">{phaseIndex === 0 ? band.latitude_band : ""}</Td>
                <Td className="num text-ink-mute">{phaseIndex === 0 ? band.calendar_count : ""}</Td>
                <Td>
                  <span className="mr-2 inline-block h-2.5 w-2.5 rounded-[2px]" style={{ backgroundColor: PHASE_COLORS[phase.order - 1] }} />
                  <span className="font-mono text-[10px] text-cool">{phase.code}</span>
                  <span className="ml-2 text-ink-dim">{phase.name}</span>
                </Td>
                <Td className="num text-ink-dim">{phase.average_duration_days.toFixed(1)} d</Td>
                {phase.average_days_by_month.map((days, monthIndex) => (
                  <td key={monthIndex} className="px-1.5 py-2">
                    <div
                      className={cn("grid h-7 min-w-[48px] place-items-center rounded-[2px] border text-[9.5px]", days >= 0.5 ? "border-white/10 text-bg-deep" : "border-white/[0.03] bg-white/[0.012] text-transparent")}
                      style={days >= 0.5 ? { backgroundColor: PHASE_COLORS[phase.order - 1], opacity: Math.max(0.38, Math.min(1, days / 20)) } : undefined}
                      title={`${phase.code}: ${days.toFixed(1)} average days in ${payload.months[monthIndex]}`}
                    >
                      {days >= 0.5 ? `${days.toFixed(0)}d` : "—"}
                    </div>
                  </td>
                ))}
              </tr>
            )))}
          </tbody>
        </table>
      </div>
      <div className="border-t border-line px-4 py-3 text-[10.5px] text-ink-mute">
        Source: {payload.source}. Latitude aggregation is for display only; the master matrix retains every coordinate and its exact DOY window.
      </div>
    </div>
  );
}

function Loading() {
  return <div className="mt-6 grid h-[320px] place-items-center rounded-sm border border-line glass"><div className="h-2 w-36 animate-pulse rounded-full bg-cool/40" /></div>;
}

function cropButton(active: boolean) {
  return cn("flex h-9 items-center gap-2 rounded-sm border px-3 text-[12px] font-medium transition-colors", active ? "border-cool/40 bg-cool/[0.08] text-ink" : "border-line bg-white/[0.02] text-ink-dim hover:text-ink");
}

function Th({ children }: { children: React.ReactNode }) { return <th className="px-3 py-3 font-medium">{children}</th>; }
function Td({ children, className }: { children: React.ReactNode; className?: string }) { return <td className={cn("px-3 py-2 align-middle", className)}>{children}</td>; }
