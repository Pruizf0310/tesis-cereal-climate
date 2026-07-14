import { PhaseCalculatorBoard } from "@/components/calculator/phase-calculator-board";

export const metadata = {
  title: "Phase calculator - CerealRisk",
  description: "One-pixel historical climate exceedance calculator by crop phenological phase."
};

export default function CalculatorPage() {
  return (
    <section className="relative min-h-[100dvh] w-full bg-bg-deep pt-14">
      <div className="grid-bg absolute inset-0 opacity-40 pointer-events-none" />
      <div className="relative mx-auto max-w-[1400px] px-6 pb-24 pt-16">
        <header className="max-w-[880px] animate-fade-up">
          <p className="kicker">Phase calculator</p>
          <h1 className="mt-3 font-display text-[clamp(2.2rem,4.2vw,3.6rem)] font-medium leading-[1] tracking-tightest text-ink">
            Historical climate exceedance by crop phase.
          </h1>
          <p className="mt-5 max-w-[680px] text-[14.5px] leading-relaxed text-ink-dim">
            Query one GDHY-compatible 0.5 degree cell at a time, attach the typical F1-F3 calendar
            for the selected crop and latitude band, then estimate event probability across 1981-2016.
          </p>
          <div className="mt-6 max-w-[760px] border-l border-cool/40 pl-4 text-[12.5px] leading-relaxed text-ink-dim">
            <p className="font-medium text-ink">How to use this calculator:</p>
            <ol className="mt-2 list-decimal space-y-1 pl-4">
              <li>Select a crop (Maize, Rice, Wheat or Soybean).</li>
              <li>Choose a latitude band; the pixel list will filter accordingly.</li>
              <li>Pick one pixel from the valid inventory table.</li>
              <li>Select a phenological phase (F1, F2 or F3).</li>
              <li>Adjust the year range if needed (default: 1981-2016).</li>
              <li>
                Click Calculate. ERA5-Land data is queried live from Google Earth Engine for the selected
                0.5 degree cell and phase window.
              </li>
            </ol>
            <p className="mt-3">
              The calculator returns the historical probability of exceeding the documented critical threshold
              for that crop-phase combination, a day-by-day breakdown by year, and a downloadable CSV with
              annual metrics.
            </p>
          </div>
        </header>

        <PhaseCalculatorBoard />
      </div>
    </section>
  );
}
