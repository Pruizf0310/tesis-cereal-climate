"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ActivitySquare,
  BarChart3,
  CalendarDays,
  ChevronDown,
  Sprout,
  Waves,
  Wheat
} from "lucide-react";
import { cn } from "@/lib/utils";

type Phase = "F1" | "F2" | "F3";
type ViewMode = "calendar" | "duration";

interface PhenologyBand {
  id: string;
  latBand: string;
  latMin: number;
  latMax: number;
  regions: number;
  dominantRegions: number;
  coveragePct: number;
  matchPct: number;
  countries: string;
  examples: string;
  phaseDurations: Record<Phase, number>;
  phaseDurationStd: Record<Phase, number>;
  phases: Record<string, Phase | "">;
  internalPatterns: PhenologyPattern[];
}

interface PhenologyPattern {
  signature: string;
  latMin: number;
  latMax: number;
  regions: number;
  coveragePct: number;
  countries: string;
  examples: string;
  phaseDurations: Record<Phase, number>;
  phaseDurationStd: Record<Phase, number>;
  phases: Record<string, Phase | "">;
}

interface PhenologySeason {
  id: string;
  label: string;
  bands: PhenologyBand[];
}

interface PhenologyCrop {
  id: "maize" | "rice" | "wheat" | "soybean";
  label: string;
  seasons: PhenologySeason[];
}

interface PhenologyPayload {
  months: string[];
  phaseLegend: Record<Phase, string>;
  crops: PhenologyCrop[];
}

const CROP_ICONS: Record<PhenologyCrop["id"], React.ReactNode> = {
  maize: <Sprout className="h-3.5 w-3.5" />,
  rice: <Waves className="h-3.5 w-3.5" />,
  wheat: <Wheat className="h-3.5 w-3.5" />,
  soybean: <ActivitySquare className="h-3.5 w-3.5" />
};

const PHASE_COLORS: Record<Phase, string> = {
  F1: "#A7C957",
  F2: "#7FB069",
  F3: "#C08497"
};

const PHASE_TEXT: Record<Phase, string> = {
  F1: "text-[#A7C957]",
  F2: "text-[#7FB069]",
  F3: "text-[#C08497]"
};

export function PhenologyCalendar() {
  const [payload, setPayload] = useState<PhenologyPayload | null>(null);
  const [cropId, setCropId] = useState<PhenologyCrop["id"]>("maize");
  const [seasonId, setSeasonId] = useState<string>("");
  const [mode, setMode] = useState<ViewMode>("calendar");
  const [expandedBand, setExpandedBand] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/phenology_typical.json")
      .then((res) => res.json())
      .then((data: PhenologyPayload) => {
        setPayload(data);
        const firstCrop = data.crops.find((crop) => crop.id === cropId);
        setSeasonId(firstCrop?.seasons[0]?.id ?? "");
      });
  }, []);

  const crop = useMemo(
    () => payload?.crops.find((item) => item.id === cropId) ?? null,
    [payload, cropId]
  );
  const season = useMemo(
    () => crop?.seasons.find((item) => item.id === seasonId) ?? crop?.seasons[0] ?? null,
    [crop, seasonId]
  );

  function handleCrop(nextCrop: PhenologyCrop["id"]) {
    setCropId(nextCrop);
    const next = payload?.crops.find((item) => item.id === nextCrop);
    setSeasonId(next?.seasons[0]?.id ?? "");
    setExpandedBand(null);
  }

  if (!payload) {
    return (
      <div className="mt-6 grid h-[360px] place-items-center rounded-sm border border-line glass">
        <div className="h-2 w-36 overflow-hidden rounded-full bg-white/[0.04]">
          <div className="h-full w-1/2 animate-pulse bg-cool/50" />
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 rounded-sm border border-line glass animate-fade-up">
      <div className="flex flex-col gap-4 border-b border-line px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {payload.crops.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => handleCrop(item.id)}
              className={cn(
                "flex items-center gap-2 rounded-sm border px-3 py-2 text-[12px] font-medium transition-colors",
                cropId === item.id
                  ? "border-cool/40 bg-cool/[0.08] text-ink"
                  : "border-line bg-white/[0.02] text-ink-dim hover:text-ink"
              )}
            >
              <span className="text-cool/80">{CROP_ICONS[item.id]}</span>
              {item.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {crop && crop.seasons.length > 0 && (
            <select
              value={season?.id ?? ""}
              onChange={(event) => {
                setSeasonId(event.target.value);
                setExpandedBand(null);
              }}
              className="h-9 rounded-sm border border-line bg-bg-panel px-3 text-[12px] text-ink outline-none"
            >
              {crop.seasons.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          )}
          <button
            type="button"
            onClick={() => setMode("calendar")}
            className={modeButton(mode === "calendar")}
            title="Monthly Gantt calendar"
          >
            <CalendarDays className="h-3.5 w-3.5" />
            Calendar
          </button>
          <button
            type="button"
            onClick={() => setMode("duration")}
            className={modeButton(mode === "duration")}
            title="Average phase duration"
          >
            <BarChart3 className="h-3.5 w-3.5" />
            Duration
          </button>
        </div>
      </div>

      {!crop || !season ? (
        <div className="grid min-h-[320px] place-items-center px-6 py-12 text-center">
          <div>
            <p className="kicker">No complete calendar</p>
            <p className="mt-3 max-w-[520px] text-[13px] leading-relaxed text-ink-dim">
              The source workbook includes soybean risk references, but no complete regional
              phenological calendar with F1, F2 and F3 in the master table.
            </p>
          </div>
        </div>
      ) : mode === "calendar" ? (
        <CalendarView
          months={payload.months}
          season={season}
          expandedBand={expandedBand}
          onToggleBand={(bandId) => setExpandedBand(expandedBand === bandId ? null : bandId)}
        />
      ) : (
        <DurationView season={season} />
      )}
    </div>
  );
}

function CalendarView({
  months,
  season,
  expandedBand,
  onToggleBand
}: {
  months: string[];
  season: PhenologySeason;
  expandedBand: string | null;
  onToggleBand: (bandId: string) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[1120px] border-collapse">
        <thead>
          <tr className="border-b border-line text-left text-[10.5px] uppercase tracking-wider text-ink-mute">
            <Th>Lat band</Th>
            <Th>n</Th>
            <Th>Match</Th>
            <Th>Coverage</Th>
            <Th>F1 d</Th>
            <Th>F2 d</Th>
            <Th>F3 d</Th>
            {months.map((month) => (
              <Th key={month}>{month.slice(0, 3)}</Th>
            ))}
          </tr>
        </thead>
        <tbody>
          {season.bands.map((band) => {
            const isOpen = expandedBand === band.id;
            return (
              <CollapsedBandRows
                key={band.id}
                band={band}
                isOpen={isOpen}
                months={months}
                onToggle={() => onToggleBand(band.id)}
              />
            );
          })}
        </tbody>
      </table>
      <PhaseLegend />
    </div>
  );
}

function CollapsedBandRows({
  band,
  isOpen,
  months,
  onToggle
}: {
  band: PhenologyBand;
  isOpen: boolean;
  months: string[];
  onToggle: () => void;
}) {
  return (
    <>
      <tr className="border-b border-line/60 text-[12px] last:border-b-0 hover:bg-white/[0.02]">
        <Td>
          <button type="button" onClick={onToggle} className="flex w-full items-center gap-2 text-left">
            <ChevronDown className={cn("h-3.5 w-3.5 text-ink-mute transition-transform", isOpen && "rotate-180")} />
            <span>
              <span className="font-medium text-ink">{formatBand(band.latBand)}</span>
              <span className="mt-1 block max-w-[170px] truncate text-[10.5px] text-ink-mute" title={band.countries}>
                {band.countries || "dominant pattern"}
              </span>
            </span>
          </button>
        </Td>
        <Td className="num text-ink-dim">{band.regions}</Td>
        <Td className="num text-ink-dim">{band.matchPct.toFixed(0)}%</Td>
        <Td className="num text-ink-dim">{band.coveragePct.toFixed(1)}%</Td>
        {(["F1", "F2", "F3"] as Phase[]).map((phase) => (
          <Td key={phase} className={cn("num", PHASE_TEXT[phase])}>
            {band.phaseDurations[phase].toFixed(0)}
          </Td>
        ))}
        {months.map((month) => {
          const phase = band.phases[month];
          return <PhaseCell key={month} phase={phase} />;
        })}
      </tr>
      {isOpen && (
        <tr className="border-b border-line/60">
          <td colSpan={19} className="bg-white/[0.015] px-4 py-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <p className="kicker">Internal variability</p>
              <p className="text-[11px] text-ink-mute">
                {band.internalPatterns.length} patterns inside this 10° latitude band · dominant pattern uses{" "}
                {band.dominantRegions}/{band.regions} regions
              </p>
            </div>
            <div className="grid gap-3">
              {band.internalPatterns.map((pattern, index) => (
                <InternalPattern key={`${pattern.signature}-${index}`} pattern={pattern} months={months} />
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function InternalPattern({ pattern, months }: { pattern: PhenologyPattern; months: string[] }) {
  return (
    <div className="rounded-sm border border-line bg-bg-panel/55 p-3">
      <div className="mb-3 grid gap-2 text-[11px] text-ink-dim md:grid-cols-[1.2fr_0.8fr_1fr]">
        <div>
          <span className="font-medium text-ink">{formatBand(`${pattern.latMax.toFixed(1)} a ${pattern.latMin.toFixed(1)}`)}</span>
          <span className="ml-2 num">{pattern.regions} regions</span>
        </div>
        <div className="num">{pattern.coveragePct.toFixed(1)}% of band</div>
        <div className="truncate" title={pattern.examples}>
          {pattern.countries || "regional samples"}
        </div>
      </div>
      <div className="grid grid-cols-[120px_repeat(12,minmax(42px,1fr))] gap-1">
        <div className="flex items-center text-[10px] uppercase tracking-wider text-ink-mute">
          Pattern
        </div>
        {months.map((month) => (
          <PhaseBox key={month} phase={pattern.phases[month]} compact />
        ))}
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        {(["F1", "F2", "F3"] as Phase[]).map((phase) => (
          <div key={phase} className="rounded-[2px] border border-line bg-white/[0.02] px-2 py-1.5">
            <div className={cn("text-[10px] font-medium", PHASE_TEXT[phase])}>{phaseLabel(phase)}</div>
            <div className="num mt-0.5 text-[11px] text-ink-dim">
              {pattern.phaseDurations[phase].toFixed(0)} d ± {pattern.phaseDurationStd[phase].toFixed(0)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PhaseCell({ phase, compact = false }: { phase: Phase | ""; compact?: boolean }) {
  return (
    <td className={compact ? "block" : "px-1.5 py-3"}>
      <PhaseBox phase={phase} compact={compact} />
    </td>
  );
}

function PhaseBox({ phase, compact = false }: { phase: Phase | ""; compact?: boolean }) {
  return (
    <div
      className={cn(
        "grid place-items-center rounded-[2px] border font-semibold",
        compact ? "h-6 text-[9px]" : "h-7 text-[10px]",
        phase ? "border-white/10 text-bg-deep" : "border-white/[0.03] bg-white/[0.015] text-transparent"
      )}
      style={phase ? { backgroundColor: PHASE_COLORS[phase] } : undefined}
      title={phase ? `${phase} · ${phaseLabel(phase)}` : "No dominant growth phase"}
    >
      {phase}
    </div>
  );
}

function DurationView({ season }: { season: PhenologySeason }) {
  return (
    <div className="grid gap-4 p-4 lg:grid-cols-2">
      {season.bands.map((band) => {
        const total = (["F1", "F2", "F3"] as Phase[]).reduce(
          (sum, phase) => sum + band.phaseDurations[phase],
          0
        );
        return (
          <div key={`${band.latBand}-${band.coveragePct}`} className="rounded-sm border border-line bg-white/[0.02] p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-ink">{formatBand(band.latBand)}</p>
                <p className="mt-1 text-[11px] text-ink-mute">
                  {band.regions} regions · {band.coveragePct.toFixed(1)}% coverage
                </p>
              </div>
              <span className="num text-[11px] text-ink-mute">{band.matchPct.toFixed(0)}% match</span>
            </div>
            <div className="mt-4 space-y-3">
              {(["F1", "F2", "F3"] as Phase[]).map((phase) => {
                const days = band.phaseDurations[phase];
                const pct = total > 0 ? (days / total) * 100 : 0;
                return (
                  <div key={phase}>
                    <div className="mb-1 flex items-center justify-between text-[11.5px]">
                      <span className={cn("font-medium", PHASE_TEXT[phase])}>{phaseLabel(phase)}</span>
                      <span className="num text-ink-dim">
                        {days.toFixed(0)} d ± {band.phaseDurationStd[phase].toFixed(0)}
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-white/[0.05]">
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: PHASE_COLORS[phase] }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PhaseLegend() {
  return (
    <div className="flex flex-wrap gap-3 border-t border-line px-4 py-3 text-[11px] text-ink-dim">
      {(["F1", "F2", "F3"] as Phase[]).map((phase) => (
        <div key={phase} className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-[2px]" style={{ backgroundColor: PHASE_COLORS[phase] }} />
          <span>
            <span className="font-medium text-ink">{phase}</span> {phaseLabel(phase)}
          </span>
        </div>
      ))}
    </div>
  );
}

function phaseLabel(phase: Phase) {
  if (phase === "F1") return "establishment";
  if (phase === "F2") return "growth";
  return "maturation";
}

function formatBand(value: string) {
  return value.replace(/-/g, "−");
}

function modeButton(active: boolean) {
  return cn(
    "flex h-9 items-center gap-2 rounded-sm border px-3 text-[12px] font-medium transition-colors",
    active
      ? "border-warm/40 bg-warm/[0.09] text-ink"
      : "border-line bg-white/[0.02] text-ink-dim hover:text-ink"
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-3 py-3 font-medium">{children}</th>;
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={cn("px-3 py-3 align-middle", className)}>{children}</td>;
}
