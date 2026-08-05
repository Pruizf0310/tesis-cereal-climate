"use client";

import { PhenologyCalendar } from "./phenology-calendar";
import { RiskPivotV2 } from "./risk-pivot-v2";

export function RiskBoard() {
  return (
    <div className="mt-12 space-y-10">
      <section>
        <div className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="kicker">Phenological hazard windows</p>
            <h2 className="mt-1 font-display text-[22px] font-medium tracking-tightest text-ink">
              Typical crop calendars
            </h2>
          </div>
          <p className="max-w-[520px] text-[11.5px] leading-relaxed text-ink-mute sm:text-right">
            Eight crop-specific technical stages, displayed by 10° latitude band and month from the spatial master matrix.
          </p>
        </div>
        <PhenologyCalendar />
      </section>

      <section>
        <div className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="kicker">Literature-linked hazards</p>
            <h2 className="mt-1 font-display text-[22px] font-medium tracking-tightest text-ink">
              Hazard and impact summary by phenological stage
            </h2>
          </div>
          <p className="max-w-[680px] text-[11.5px] leading-relaxed text-ink-mute sm:text-right">
            Every technical stage is retained for maize, rice, soybean and wheat. Thresholds,
            impact statements, evidence scope and limitations remain traceable to the audited sources;
            missing evidence is shown explicitly instead of being inferred.
          </p>
        </div>
        <RiskPivotV2 />
      </section>
    </div>
  );
}
