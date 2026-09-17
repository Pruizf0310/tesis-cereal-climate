"use client";

import { PhenologyCalendar } from "./regional-phenology-calendar";
import { RiskPivotV2 } from "./risk-pivot-v2";

export function RiskBoard() {
  return (
    <div className="mt-12 space-y-10">
      <aside className="rounded-sm border border-line p-4 text-[12px] leading-relaxed text-ink-dim">
        <h2 className="font-medium text-ink">Scientific basis for phase harmonization</h2>
        <p className="mt-2">The reviewed studies use different stage names, codes and boundaries. We map their biological descriptions to six project macro-phases: EST, VEG, FLO, REP, FIL and MAT. This is a research crosswalk; original crop scales and source evidence remain traceable in the details. REP may occur before or after flowering depending on the crop.</p>
        <p className="mt-2">The six-phase operational partition preserves the original technical intervals and records correspondence revisions. Intermediate dates remain estimates. A phase match does not turn an experimental treatment into a validated damage threshold. Maize REP is reserved pending hazard assignment.</p>
        <a href="https://doi.org/10.3390/agronomy13082126" target="_blank" rel="noreferrer" className="mt-2 inline-block text-cool underline">Example: Zhang et al. (2023), lag stage versus effective grain filling</a>
      </aside>
      <section>
        <div className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="kicker">Phenological hazard windows</p>
            <h2 className="mt-1 font-display text-[22px] font-medium tracking-tightest text-ink">
              Typical crop calendars
            </h2>
          </div>
          <p className="max-w-[520px] text-[11.5px] leading-relaxed text-ink-mute sm:text-right">
            Six consecutive phases for the selected latitude band and longitude/planting zone. A representative archived calendar preserves original dates; the range of cycle lengths remains visible.
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
            Reviewed phases are homologated to EST, VEG, FLO, REP, FIL and MAT. Thresholds,
            impact statements, evidence scope and limitations remain traceable to the audited sources;
            missing evidence is shown explicitly instead of being inferred.
          </p>
        </div>
        <RiskPivotV2 />
      </section>
    </div>
  );
}
