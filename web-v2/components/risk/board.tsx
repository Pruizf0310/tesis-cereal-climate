"use client";

import { PhenologyCalendar } from "./phenology-calendar";
import { RiskPivotV2 } from "./risk-pivot-v2";

export function RiskBoard() {
  return (
    <div className="mt-12 space-y-10">
      <section>
        <div className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="kicker">Phenological threat windows</p>
            <h2 className="mt-1 font-display text-[22px] font-medium tracking-tightest text-ink">
              Typical crop calendars
            </h2>
          </div>
          <p className="max-w-[520px] text-[11.5px] leading-relaxed text-ink-mute sm:text-right">
            Monthly F1-F3 windows grouped by latitude band, with internal variability available on click.
          </p>
        </div>
        <PhenologyCalendar />
      </section>

      <section>
        <div className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="kicker">Risk pivot v2</p>
            <h2 className="mt-1 font-display text-[22px] font-medium tracking-tightest text-ink">
              Resumen de amenazas e impacto por etapa fenológica
            </h2>
          </div>
          <p className="max-w-[680px] text-[11.5px] leading-relaxed text-ink-mute sm:text-right">
            La tabla sintetiza, para cada cultivo, las amenazas climáticas críticas asociadas a
            etapas fenológicas derivadas. El impacto cuantitativo se estima a partir de porcentajes
            reportados en la literatura, ponderados por tipo de variable afectada y nivel de
            evidencia. Cuando no existe porcentaje explícito, se conserva una clasificación
            cualitativa trazable al texto original.
          </p>
        </div>
        <RiskPivotV2 />
      </section>
    </div>
  );
}
