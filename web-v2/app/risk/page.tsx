import { RiskBoard } from "@/components/risk/board";

export const metadata = {
  title: "Risk · Phenology",
  description: "Typical phenology calendars and crop-stage windows for climate hazard interpretation."
};

export default function RiskPage() {
  return (
    <section className="relative min-h-[100dvh] w-full bg-bg-deep pt-14">
      <div className="grid-bg absolute inset-0 opacity-40 pointer-events-none" />
      <div className="relative mx-auto max-w-[1400px] px-6 pb-24 pt-16">
        <header className="max-w-[820px] animate-fade-up">
          <p className="kicker">Risk</p>
          <h1 className="mt-3 font-display text-[clamp(2.2rem,4.2vw,3.6rem)] font-medium leading-[1] tracking-tightest text-ink">
            Risk · Phenological hazard windows
          </h1>
          <p className="mt-5 max-w-[640px] text-[14.5px] leading-relaxed text-ink-dim">
            Explore the eight technical stages of maize, rice, soybean and wheat by season,
            water system and latitude band, then review the literature-linked climate hazards assigned to each stage.
          </p>
        </header>

        <RiskBoard />
      </div>
    </section>
  );
}
