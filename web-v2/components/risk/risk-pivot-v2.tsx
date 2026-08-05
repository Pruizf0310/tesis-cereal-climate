"use client";

import { useEffect, useMemo, useState } from "react";
import { ActivitySquare, ChevronDown, ExternalLink, Sprout, Waves, Wheat } from "lucide-react";
import { cn } from "@/lib/utils";

interface HazardDetails {
  phase_order: number;
  rule_id: string;
  evidence_type: string;
  spatial_scope: string;
  source: string;
  link: string;
  limitations: string;
}

interface HazardRow {
  crop: "maize" | "rice" | "soybean" | "wheat";
  phase_code: string;
  derived_stage: string;
  hazard: string;
  threshold: string;
  qualitative_impact: string;
  quantitative_impact: string;
  category: string;
  details: HazardDetails;
}

interface HazardPayload {
  version: string;
  source: string;
  interpretation: string;
  rows: HazardRow[];
}

const CROPS: { id: HazardRow["crop"]; label: string; icon: React.ReactNode }[] = [
  { id: "maize", label: "Maize", icon: <Sprout className="h-3.5 w-3.5" /> },
  { id: "rice", label: "Rice", icon: <Waves className="h-3.5 w-3.5" /> },
  { id: "soybean", label: "Soybean", icon: <ActivitySquare className="h-3.5 w-3.5" /> },
  { id: "wheat", label: "Wheat", icon: <Wheat className="h-3.5 w-3.5" /> }
];

const CATEGORY_CLASS: Record<string, string> = {
  "Modeled threshold": "border-cool/35 bg-cool/[0.08] text-cool",
  "Modeled threshold — provisional duration": "border-warm/35 bg-warm/[0.08] text-warm",
  "Regional indicator": "border-[#9F8CC9]/40 bg-[#9F8CC9]/10 text-[#B8A7DA]",
  "Damaging experimental treatment": "border-[#D98B57]/40 bg-[#D98B57]/10 text-[#E4A177]",
  "Secondary-source treatment": "border-[#D98B57]/35 bg-[#D98B57]/8 text-[#DDA07D]",
  "Seasonal observational association": "border-[#7FAF7B]/40 bg-[#7FAF7B]/10 text-[#91C18D]",
  "Modeled cardinal parameter": "border-[#76B7C5]/40 bg-[#76B7C5]/10 text-[#8CC8D2]",
  "Evidence gap": "border-line bg-white/[0.02] text-ink-mute"
};

export function RiskPivotV2() {
  const [payload, setPayload] = useState<HazardPayload | null>(null);
  const [cropId, setCropId] = useState<HazardRow["crop"]>("maize");
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [showGaps, setShowGaps] = useState(true);

  useEffect(() => {
    fetch("/data/hazard_impact_v2.json").then((res) => res.json()).then((data: HazardPayload) => setPayload(data));
  }, []);

  const rows = useMemo(
    () => (payload?.rows ?? []).filter((row) => row.crop === cropId && (showGaps || row.category !== "Evidence gap")),
    [payload, cropId, showGaps]
  );

  if (!payload) return <div className="mt-6 grid h-[280px] place-items-center rounded-sm border border-line glass"><div className="h-2 w-36 animate-pulse rounded-full bg-warm/40" /></div>;

  return (
    <div className="mt-6 overflow-hidden rounded-sm border border-line glass animate-fade-up">
      <div className="flex flex-col gap-4 border-b border-line px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {CROPS.map((crop) => (
            <button key={crop.id} type="button" onClick={() => { setCropId(crop.id); setExpandedRow(null); }} className={cropButton(cropId === crop.id)}>
              <span className="text-cool/80">{crop.icon}</span>{crop.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3 text-[11px] text-ink-mute">
          <label className="flex cursor-pointer items-center gap-2">
            <input type="checkbox" checked={showGaps} onChange={(event) => setShowGaps(event.target.checked)} className="accent-[#7FD4DF]" />
            Show evidence gaps
          </label>
          <span>{rows.length} phase–hazard rows</span>
        </div>
      </div>

      <div className="border-b border-line bg-warm/[0.025] px-4 py-3 text-[11px] leading-relaxed text-ink-dim">
        All eight technical stages are retained. A rule is a literature-backed candidate assigned to a crop stage; local occurrence still requires daily climate data for the coordinate and stage window.
      </div>

      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[1380px] border-collapse">
          <thead><tr className="border-b border-line text-left text-[10px] uppercase tracking-wider text-ink-mute">
            <Th>Derived stage</Th><Th>Hazard</Th><Th>Threshold</Th><Th>Qualitative impact</Th><Th>Quantitative impact</Th><Th>Category</Th><Th>Details</Th>
          </tr></thead>
          <tbody>
            {rows.map((row, index) => {
              const key = `${row.crop}-${row.phase_code}-${row.details.rule_id}-${index}`;
              const open = expandedRow === key;
              return <HazardTableRow key={key} row={row} open={open} onToggle={() => setExpandedRow(open ? null : key)} />;
            })}
          </tbody>
        </table>
      </div>

      <div className="grid gap-3 p-4 md:hidden">
        {rows.map((row, index) => {
          const key = `${row.crop}-${row.phase_code}-${row.details.rule_id}-${index}`;
          const open = expandedRow === key;
          return <HazardCard key={key} row={row} open={open} onToggle={() => setExpandedRow(open ? null : key)} />;
        })}
      </div>
      <div className="border-t border-line px-4 py-3 text-[10.5px] text-ink-mute">Source: {payload.source}. {payload.interpretation}</div>
    </div>
  );
}

function HazardTableRow({ row, open, onToggle }: { row: HazardRow; open: boolean; onToggle: () => void }) {
  return <>
    <tr className="border-b border-line/55 text-[11.5px] hover:bg-white/[0.02]">
      <Td className="max-w-[210px]"><span className="font-mono text-[9.5px] text-cool">{row.phase_code}</span><span className="mt-1 block font-medium text-ink">{row.derived_stage}</span></Td>
      <Td className="max-w-[190px] text-ink-dim">{row.hazard}</Td>
      <Td className="max-w-[280px] text-ink-dim">{row.threshold}</Td>
      <Td className="max-w-[290px] text-ink-dim">{row.qualitative_impact}</Td>
      <Td className="max-w-[230px] font-mono text-[10.5px] text-ink">{row.quantitative_impact}</Td>
      <Td><CategoryBadge category={row.category} /></Td>
      <Td><button type="button" onClick={onToggle} className="flex h-8 items-center gap-2 rounded-sm border border-line bg-white/[0.02] px-2.5 text-[11px] text-ink-dim hover:text-ink"><ChevronDown className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")} />View</button></Td>
    </tr>
    {open && <tr className="border-b border-line/55"><td colSpan={7} className="bg-white/[0.015] px-4 py-4"><Details details={row.details} /></td></tr>}
  </>;
}

function HazardCard({ row, open, onToggle }: { row: HazardRow; open: boolean; onToggle: () => void }) {
  return <article className="rounded-sm border border-line bg-white/[0.02] p-4">
    <div className="flex items-start justify-between gap-3"><div><p className="font-mono text-[10px] text-cool">{row.phase_code}</p><p className="mt-1 text-[12px] font-medium text-ink">{row.derived_stage}</p></div><CategoryBadge category={row.category} /></div>
    <p className="mt-3 text-[11px] text-ink-dim"><span className="font-medium text-ink">{row.hazard}:</span> {row.threshold}</p>
    <div className="mt-3 grid gap-2 text-[10.5px]"><Info label="Qualitative impact" value={row.qualitative_impact} /><Info label="Quantitative impact" value={row.quantitative_impact} /></div>
    <button type="button" onClick={onToggle} className="mt-3 flex h-8 items-center gap-2 rounded-sm border border-line px-2.5 text-[11px] text-ink-dim"><ChevronDown className={cn("h-3.5 w-3.5", open && "rotate-180")} />Details</button>
    {open && <div className="mt-3"><Details details={row.details} /></div>}
  </article>;
}

function Details({ details }: { details: HazardDetails }) {
  return <div className="grid gap-3 text-[11px] leading-relaxed text-ink-dim lg:grid-cols-3">
    <Info label="Rule ID" value={details.rule_id} /><Info label="Evidence type" value={details.evidence_type} /><Info label="Spatial scope" value={details.spatial_scope} />
    <Info label="Source" value={details.source} />
    <div className="rounded-[2px] border border-line bg-bg-panel/55 p-3"><p className="mb-1 text-[9.5px] uppercase tracking-wider text-ink-mute">Link</p>{details.link ? <a href={toHref(details.link)} target="_blank" rel="noreferrer" className="flex items-center gap-1 break-all text-cool/90"><ExternalLink className="h-3 w-3 shrink-0" />{details.link}</a> : "No external link recorded"}</div>
    <Info label="Limitations" value={details.limitations} />
  </div>;
}

function toHref(value: string) { return value.startsWith("http") ? value : `https://doi.org/${value}`; }
function CategoryBadge({ category }: { category: string }) { return <span className={cn("inline-flex max-w-[180px] rounded-[2px] border px-2 py-1 text-[9.5px] font-medium", CATEGORY_CLASS[category] ?? CATEGORY_CLASS["Evidence gap"])}>{category}</span>; }
function Info({ label, value }: { label: string; value: string }) { return <div className="rounded-[2px] border border-line bg-bg-panel/55 p-3"><p className="mb-1 text-[9.5px] uppercase tracking-wider text-ink-mute">{label}</p><p>{value}</p></div>; }
function cropButton(active: boolean) { return cn("flex h-9 items-center gap-2 rounded-sm border px-3 text-[12px] font-medium transition-colors", active ? "border-cool/40 bg-cool/[0.08] text-ink" : "border-line bg-white/[0.02] text-ink-dim hover:text-ink"); }
function Th({ children }: { children: React.ReactNode }) { return <th className="px-3 py-3 font-medium">{children}</th>; }
function Td({ children, className }: { children: React.ReactNode; className?: string }) { return <td className={cn("px-3 py-3 align-top", className)}>{children}</td>; }
