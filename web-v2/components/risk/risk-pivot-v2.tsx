"use client";

import { useEffect, useMemo, useState } from "react";
import { ActivitySquare, ChevronDown, ExternalLink, Sprout, Waves, Wheat } from "lucide-react";
import { cn } from "@/lib/utils";

interface RiskPivotRow {
  cultivo: string;
  etapa_derivada: string;
  amenaza: string;
  umbral: string;
  impacto_cualitativo: string;
  impacto_cuantitativo: number | string;
  categoria_impacto: string;
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

const BADGE_CLASS: Record<string, string> = {
  Low: "border-[color:var(--risk-low)]/40 bg-[color:var(--risk-low)]/12 text-[color:var(--risk-low)]",
  Moderate: "border-[color:var(--risk-mod)]/40 bg-[color:var(--risk-mod)]/12 text-[color:var(--risk-mod)]",
  High: "border-[color:var(--risk-high)]/40 bg-[color:var(--risk-high)]/12 text-[color:var(--risk-high)]",
  Critical: "border-[color:var(--risk-extr)]/45 bg-[color:var(--risk-extr)]/14 text-[#E27A7A]",
  "Not determined": "border-line bg-white/[0.025] text-ink-mute"
};

const IMPACT_LABELS: Record<string, string> = {
  Bajo: "Low",
  Moderado: "Moderate",
  Alto: "High",
  Crítico: "Critical",
  "No determinado": "Not determined",
  Low: "Low",
  Moderate: "Moderate",
  High: "High",
  Critical: "Critical",
  "Not determined": "Not determined"
};

const STAGE_LABELS: Record<string, string> = {
  "Floración / reproducción": "Flowering / reproduction",
  "Germinación / establecimiento": "Germination / establishment",
  "Llenado de grano / formación de rendimiento": "Grain filling / yield formation",
  "Llenado de grano / maduración": "Grain filling / maturation",
  "Maduración / cosecha": "Maturation / harvest",
  "Desarrollo vegetativo": "Vegetative development",
  "No determinado": "Not determined"
};

const HAZARD_LABELS: Record<string, string> = {
  "Déficit hídrico en ventana reproductiva — Hídrico": "Water deficit during the reproductive window — Water stress",
  "Humedad del suelo en zona radicular — Hídrico": "Root-zone soil moisture — Water stress",
  "Temperatura durante llenado efectivo del grano — Térmico": "Temperature during effective grain filling — Heat stress",
  "Temperatura máxima durante antesis/floración — Térmico": "Maximum temperature during anthesis/flowering — Heat stress",
  "Potencial hídrico del suelo/solución — Hídrico": "Soil/solution water potential — Water stress",
  "Temperatura del aire durante llenado del grano — Térmico": "Air temperature during grain filling — Heat stress",
  "Temperatura del aire en antesis — Térmico": "Air temperature at anthesis — Heat stress",
  "Temperatura durante emergencia y crecimiento otoñal temprano — Térmico": "Temperature during emergence and early autumn growth — Heat stress",
  "Temperatura del aire en llenado medio a terminal — Térmico": "Air temperature during mid-to-terminal grain filling — Heat stress"
};

const THRESHOLD_LABELS: Record<string, string> = {
  "<30 mm en 10 días durante fase reproductiva en maíz grano (umbral empírico distrital); evidencia experimental complementaria con ψs ≈ −50 kPa como estrés manejado":
    "<30 mm over 10 days during the reproductive phase in grain maize (district-scale empirical threshold); complementary experimental evidence with ψs ≈ −50 kPa as managed stress",
  "θ < 0.183 cm³ cm⁻³ en 0–1 m, derivado con criterio FAO (p = 0.55) a partir de θFC = 0.26 y θWP = 0.12; por debajo de ese valor comenzó (K_s<1)":
    "θ < 0.183 cm³ cm⁻³ in 0-1 m soil depth, derived with the FAO criterion (p = 0.55) from θFC = 0.26 and θWP = 0.12; below this value, stress began (K_s<1)",
  "Tratamientos con Tmax media de 39.4–41.5 °C durante 7 días en llenado efectivo generaron daño claro; a 32.9 °C no hubo efecto significativo":
    "Treatments with mean Tmax of 39.4-41.5 °C for 7 days during effective grain filling caused clear damage; at 32.9 °C there was no significant effect",
  "≥35 °C durante antesis; en el experimento, el tratamiento térmico tuvo pico de 39 °C y se aplicó 48 h":
    "≥35 °C during anthesis; in the experiment, the heat treatment peaked at 39 °C and was applied for 48 h",
  "−0.046 a −0.056 MPa: umbral a partir del cual comienzan a caer evapotranspiración, expansión foliar y biomasa; en campo, la productividad cayó cuando se alcanzó −0.05 a −0.06 MPa":
    "−0.046 to −0.056 MPa: threshold where evapotranspiration, leaf expansion and biomass begin to decline; in field conditions, productivity declined at −0.05 to −0.06 MPa",
  "T media diaria >25 °C durante llenado se asocia a pérdida de calidad; en campo, un aumento de 1.6–3.1 °C durante llenado redujo el rendimiento":
    "Mean daily temperature >25 °C during filling is associated with quality loss; in the field, a 1.6-3.1 °C increase during filling reduced yield",
  "35/25 °C día/noche durante 7 días en antesis": "35/25 °C day/night for 7 days at anthesis",
  "<10 °C o >30 °C reducen significativamente la germinación; alrededor de 8 °C aún germina, pero con emergencia muy lenta y menor rendimiento posterior":
    "<10 °C or >30 °C significantly reduce germination; around 8 °C germination still occurs, but emergence is very slow and later yield is lower",
  "38/28 °C día/noche durante 7 días en llenado medio; además, >30 °C se asocia de forma consistente con caída del llenado":
    "38/28 °C day/night for 7 days during mid grain filling; >30 °C is also consistently associated with reduced filling"
};

const EVIDENCE_LABELS: Record<string, string> = {
  "Modelación empírica a escala distrital + experimento de campo": "District-scale empirical modeling + field experiment",
  "Experimental de campo multianual + umbral operativo derivado por balance hídrico":
    "Multi-year field experiment + operational threshold derived from water balance",
  "Experimental de campo": "Field experiment",
  "Experimental en ambiente controlado": "Controlled-environment experiment",
  "Experimental en invernadero con validación de campo": "Greenhouse experiment with field validation",
  "Experimental de campo + revisión": "Field experiment + review",
  "Experimental de campo multianual + síntesis fisiológica": "Multi-year field experiment + physiological synthesis"
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
          {visibleRows.length} summarized hazards · no latitude split
        </p>
      </div>

      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[1120px] border-collapse">
          <thead>
            <tr className="border-b border-line text-left text-[10.5px] uppercase tracking-wider text-ink-mute">
              <Th>Derived stage</Th>
              <Th>Hazard</Th>
              <Th>Threshold</Th>
              <Th>Qualitative impact</Th>
              <Th>Quantitative impact</Th>
              <Th>Category</Th>
              <Th>Details</Th>
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
        <Td className="max-w-[180px] font-medium text-ink">{displayStage(row.etapa_derivada)}</Td>
        <Td className="max-w-[260px] text-ink-dim">{displayHazard(row.amenaza)}</Td>
        <Td className="max-w-[310px] text-ink-dim">{displayThreshold(row.umbral)}</Td>
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
            title="Show source, method and base records"
          >
            <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", isOpen && "rotate-180")} />
            View
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
          <p className="text-[12px] font-medium text-ink">{displayStage(row.etapa_derivada)}</p>
          <p className="mt-1 text-[11px] leading-relaxed text-ink-dim">{displayHazard(row.amenaza)}</p>
        </div>
        <ImpactBadge label={row.categoria_impacto} />
      </div>
      <p className="mt-3 text-[11.5px] leading-relaxed text-ink-dim">{displayThreshold(row.umbral)}</p>
      <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
        <div className="rounded-[2px] border border-line bg-white/[0.02] p-2">
          <span className="block text-ink-mute">Qualitative impact</span>
          <span className="mt-1 block"><ImpactBadge label={row.impacto_cualitativo} /></span>
        </div>
        <div className="rounded-[2px] border border-line bg-white/[0.02] p-2">
          <span className="block text-ink-mute">Quantitative impact</span>
          <span className="num mt-1 block text-ink">{formatQuant(row.impacto_cuantitativo)}</span>
        </div>
      </div>
      <button
        type="button"
        onClick={onToggle}
        className="mt-3 flex h-8 items-center gap-2 rounded-sm border border-line bg-white/[0.02] px-2.5 text-[11px] text-ink-dim"
      >
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", isOpen && "rotate-180")} />
        Source and traceability
      </button>
      {isOpen && <div className="mt-3"><RiskDetails row={row} /></div>}
    </article>
  );
}

function RiskDetails({ row }: { row: RiskPivotRow }) {
  return (
    <div className="grid gap-3 text-[11.5px] leading-relaxed text-ink-dim lg:grid-cols-[1fr_1fr_1.4fr]">
      <Detail label="Source">{row.fuente}</Detail>
      <Detail label="Link">
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
      <Detail label="Calculation rule">{displayCriteria(row.criterio_calculo)}</Detail>
      <Detail label="Evidence">{displayEvidence(row.evidencia)}</Detail>
      <Detail label="Base records">
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

function ImpactBadge({ label }: { label: string }) {
  const displayLabel = displayImpact(label);
  return (
    <span className={cn("inline-flex rounded-[2px] border px-2 py-1 text-[10.5px] font-medium", BADGE_CLASS[displayLabel])}>
      {displayLabel}
    </span>
  );
}

function formatQuant(value: RiskPivotRow["impacto_cuantitativo"]) {
  if (typeof value === "number") return value.toFixed(2);
  return value === "No determinado" ? "Not determined" : value;
}

function rowKey(row: RiskPivotRow, index: number) {
  return `${row.cultivo}-${row.etapa_derivada}-${row.amenaza}-${index}`;
}

function displayStage(value: string) {
  return STAGE_LABELS[value] ?? value;
}

function displayHazard(value: string) {
  return HAZARD_LABELS[value] ?? value;
}

function displayThreshold(value: string) {
  return THRESHOLD_LABELS[value] ?? value;
}

function displayEvidence(value: string) {
  return EVIDENCE_LABELS[value] ?? value;
}

function displayCriteria(value: string) {
  if (value.startsWith("Porcentaje extraído")) {
    return "Percentage extracted from impact_cultivo, weighted by impact type and evidence level.";
  }
  if (value.startsWith("Regla cualitativa")) {
    return "Qualitative rule: no explicit percentage was found in impact_cultivo.";
  }
  if (value.startsWith("Cálculo mixto")) {
    return "Mixed calculation: extracted percentage where available and qualitative rule for records without an explicit percentage.";
  }
  return value;
}

function displayImpact(value: string) {
  return IMPACT_LABELS[value] ?? value;
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-3 py-3 font-medium">{children}</th>;
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={cn("px-3 py-3 align-top", className)}>{children}</td>;
}
