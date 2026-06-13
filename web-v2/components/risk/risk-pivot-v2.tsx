"use client";

import { useEffect, useMemo, useState } from "react";
import { ActivitySquare, ChevronDown, ExternalLink, Sprout, Waves, Wheat } from "lucide-react";
import { cn } from "@/lib/utils";

type ImpactLabel = "Bajo" | "Moderado" | "Alto" | "Crítico" | "No determinado";

interface RiskPivotRow {
  cultivo: string;
  etapa_derivada: string;
  amenaza: string;
  umbral: string;
  impacto_cualitativo: ImpactLabel;
  impacto_cuantitativo: number | "No determinado";
  categoria_impacto: ImpactLabel;
  evidencia: string;
  fuente: string;
  enlace: string;
  criterio_calculo: string;
  registros_base: string;
}

const CROP_LABELS: Record<string, string> = {
  maize: "Maize",
  rice: "Rice",
  wheat: "Wheat",
  soybean: "Soybean",
  sorghum: "Sorghum",
  millet: "Millet",
  beans: "Beans",
  teff: "Teff"
};

const CROP_ICONS: Record<string, React.ReactNode> = {
  maize: <Sprout className="h-3.5 w-3.5" />,
  rice: <Waves className="h-3.5 w-3.5" />,
  wheat: <Wheat className="h-3.5 w-3.5" />,
  soybean: <ActivitySquare className="h-3.5 w-3.5" />
};

const BADGE_CLASS: Record<ImpactLabel, string> = {
  Bajo: "border-[color:var(--risk-low)]/40 bg-[color:var(--risk-low)]/12 text-[color:var(--risk-low)]",
  Moderado: "border-[color:var(--risk-mod)]/40 bg-[color:var(--risk-mod)]/12 text-[color:var(--risk-mod)]",
  Alto: "border-[color:var(--risk-high)]/40 bg-[color:var(--risk-high)]/12 text-[color:var(--risk-high)]",
  Crítico: "border-[color:var(--risk-extr)]/45 bg-[color:var(--risk-extr)]/14 text-[#E27A7A]",
  "No determinado": "border-line bg-white/[0.025] text-ink-mute"
};

export function RiskPivotV2() {
  const [rows, setRows] = useState<RiskPivotRow[]>([]);
  const [cropId, setCropId] = useState<string>("");
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/risk_pivot_v2.json")
      .then((res) => res.json())
      .then((data: RiskPivotRow[]) => {
        setRows(data);
        setCropId(data[0]?.cultivo ?? "");
      });
  }, []);

  const crops = useMemo(() => Array.from(new Set(rows.map((row) => row.cultivo))), [rows]);
  const visibleRows = useMemo(() => rows.filter((row) => row.cultivo === cropId), [rows, cropId]);

  function handleCrop(nextCrop: string) {
    setCropId(nextCrop);
    setExpandedRow(null);
  }

  if (!rows.length) {
    return (
      <div className="mt-6 grid h-[280px] place-items-center rounded-sm border border-line glass">
        <div className="h-2 w-36 overflow-hidden rounded-full bg-white/[0.04]">
          <div className="h-full w-1/2 animate-pulse bg-warm/50" />
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 rounded-sm border border-line glass animate-fade-up">
      <div className="flex flex-col gap-4 border-b border-line px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {crops.map((crop) => (
            <button
              key={crop}
              type="button"
              onClick={() => handleCrop(crop)}
              className={cn(
                "flex items-center gap-2 rounded-sm border px-3 py-2 text-[12px] font-medium transition-colors",
                cropId === crop
                  ? "border-cool/40 bg-cool/[0.08] text-ink"
                  : "border-line bg-white/[0.02] text-ink-dim hover:text-ink"
              )}
            >
              <span className="text-cool/80">{CROP_ICONS[crop] ?? <Sprout className="h-3.5 w-3.5" />}</span>
              {CROP_LABELS[crop] ?? crop}
            </button>
          ))}
        </div>
        <p className="text-[11px] text-ink-mute">
          {visibleRows.length} summarized threats · no latitude split
        </p>
      </div>

      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[1120px] border-collapse">
          <thead>
            <tr className="border-b border-line text-left text-[10.5px] uppercase tracking-wider text-ink-mute">
              <Th>Etapa derivada</Th>
              <Th>Amenaza</Th>
              <Th>Umbral</Th>
              <Th>Impacto cualitativo</Th>
              <Th>Impacto cuantitativo</Th>
              <Th>Categoría</Th>
              <Th>Detalle</Th>
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row, index) => {
              const key = rowKey(row, index);
              const isOpen = expandedRow === key;
              return (
                <RiskTableRow
                  key={key}
                  row={row}
                  isOpen={isOpen}
                  onToggle={() => setExpandedRow(isOpen ? null : key)}
                />
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="grid gap-3 p-4 md:hidden">
        {visibleRows.map((row, index) => {
          const key = rowKey(row, index);
          const isOpen = expandedRow === key;
          return (
            <RiskMobileCard
              key={key}
              row={row}
              isOpen={isOpen}
              onToggle={() => setExpandedRow(isOpen ? null : key)}
            />
          );
        })}
      </div>
    </div>
  );
}

function RiskTableRow({ row, isOpen, onToggle }: { row: RiskPivotRow; isOpen: boolean; onToggle: () => void }) {
  return (
    <>
      <tr className="border-b border-line/60 text-[12px] last:border-b-0 hover:bg-white/[0.02]">
        <Td className="max-w-[180px] font-medium text-ink">{row.etapa_derivada}</Td>
        <Td className="max-w-[260px] text-ink-dim">{row.amenaza}</Td>
        <Td className="max-w-[310px] text-ink-dim">{row.umbral}</Td>
        <Td>
          <ImpactBadge label={row.impacto_cualitativo} />
        </Td>
        <Td className="num text-ink">{formatQuant(row.impacto_cuantitativo)}</Td>
        <Td>
          <ImpactBadge label={row.categoria_impacto} />
        </Td>
        <Td>
          <button
            type="button"
            onClick={onToggle}
            className="flex h-8 items-center gap-2 rounded-sm border border-line bg-white/[0.02] px-2.5 text-[11px] text-ink-dim transition-colors hover:text-ink"
            title="Mostrar fuente, criterio y registros base"
          >
            <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", isOpen && "rotate-180")} />
            Ver
          </button>
        </Td>
      </tr>
      {isOpen && (
        <tr className="border-b border-line/60">
          <td colSpan={7} className="bg-white/[0.015] px-4 py-4">
            <RiskDetails row={row} />
          </td>
        </tr>
      )}
    </>
  );
}

function RiskMobileCard({ row, isOpen, onToggle }: { row: RiskPivotRow; isOpen: boolean; onToggle: () => void }) {
  return (
    <article className="rounded-sm border border-line bg-white/[0.02] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[12px] font-medium text-ink">{row.etapa_derivada}</p>
          <p className="mt-1 text-[11px] leading-relaxed text-ink-dim">{row.amenaza}</p>
        </div>
        <ImpactBadge label={row.categoria_impacto} />
      </div>
      <p className="mt-3 text-[11.5px] leading-relaxed text-ink-dim">{row.umbral}</p>
      <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
        <div className="rounded-[2px] border border-line bg-white/[0.02] p-2">
          <span className="block text-ink-mute">Impacto cualitativo</span>
          <span className="mt-1 block"><ImpactBadge label={row.impacto_cualitativo} /></span>
        </div>
        <div className="rounded-[2px] border border-line bg-white/[0.02] p-2">
          <span className="block text-ink-mute">Impacto cuantitativo</span>
          <span className="num mt-1 block text-ink">{formatQuant(row.impacto_cuantitativo)}</span>
        </div>
      </div>
      <button
        type="button"
        onClick={onToggle}
        className="mt-3 flex h-8 items-center gap-2 rounded-sm border border-line bg-white/[0.02] px-2.5 text-[11px] text-ink-dim"
      >
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", isOpen && "rotate-180")} />
        Fuente y trazabilidad
      </button>
      {isOpen && <div className="mt-3"><RiskDetails row={row} /></div>}
    </article>
  );
}

function RiskDetails({ row }: { row: RiskPivotRow }) {
  return (
    <div className="grid gap-3 text-[11.5px] leading-relaxed text-ink-dim lg:grid-cols-[1fr_1fr_1.4fr]">
      <Detail label="Fuente">{row.fuente}</Detail>
      <Detail label="Enlace">
        <div className="space-y-1">
          {row.enlace.split(";").map((link) => {
            const href = link.trim();
            if (!href) return null;
            return (
              <a
                key={href}
                href={href}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-cool/90 hover:text-cool"
              >
                <ExternalLink className="h-3 w-3 shrink-0" />
                <span className="truncate">{href}</span>
              </a>
            );
          })}
        </div>
      </Detail>
      <Detail label="Criterio de cálculo">{row.criterio_calculo}</Detail>
      <Detail label="Evidencia">{row.evidencia}</Detail>
      <Detail label="Registros base">
        <span className="line-clamp-3 break-words" title={row.registros_base}>
          {row.registros_base}
        </span>
      </Detail>
    </div>
  );
}

function Detail({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[2px] border border-line bg-bg-panel/55 p-3">
      <p className="mb-1 text-[10px] uppercase tracking-wider text-ink-mute">{label}</p>
      <div>{children}</div>
    </div>
  );
}

function ImpactBadge({ label }: { label: ImpactLabel }) {
  return (
    <span className={cn("inline-flex rounded-[2px] border px-2 py-1 text-[10.5px] font-medium", BADGE_CLASS[label])}>
      {label}
    </span>
  );
}

function formatQuant(value: RiskPivotRow["impacto_cuantitativo"]) {
  return typeof value === "number" ? value.toFixed(2) : value;
}

function rowKey(row: RiskPivotRow, index: number) {
  return `${row.cultivo}-${row.etapa_derivada}-${row.amenaza}-${index}`;
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-3 py-3 font-medium">{children}</th>;
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={cn("px-3 py-3 align-top", className)}>{children}</td>;
}
