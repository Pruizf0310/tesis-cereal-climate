import { RiskBoard } from "@/components/risk/board";

export const metadata = {
  title: "Risk · CerealRisk",
  description:
    "Self-organized climate clusters, trigger candidates and the curve from El Niño to harvest loss."
};

export default function RiskPage() {
  return (
    <section className="relative min-h-[100dvh] w-full bg-bg-deep pt-14">
      <div className="grid-bg absolute inset-0 opacity-40 pointer-events-none" />
      <div className="relative mx-auto max-w-[1400px] px-6 pb-24 pt-16">
        <header className="max-w-[820px] animate-fade-up">
          <p className="kicker">Exploratory risk</p>
          <h1 className="mt-3 font-display text-[clamp(2.2rem,4.2vw,3.6rem)] font-medium leading-[1] tracking-tightest text-ink">
            From a climate fingerprint to a harvest loss.
          </h1>
          <p className="mt-5 max-w-[640px] text-[14.5px] leading-relaxed text-ink-dim">
            Each agricultural pixel is grouped into a Self-Organizing Map class that summarizes how
            it co-varies with Pacific and Atlantic SST modes. We then ask: when ONI crosses a
            threshold, how does yield respond?
          </p>
        </header>

        <RiskBoard />
      </div>
    </section>
  );
}
