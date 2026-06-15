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
        </header>

        <PhaseCalculatorBoard />
      </div>
    </section>
  );
}
