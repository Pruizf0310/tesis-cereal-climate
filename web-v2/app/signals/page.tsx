import { SignalHero } from "@/components/signals/SignalHero";
import { ONIHistoricalChart } from "@/components/signals/ONIHistoricalChart";
import { MJOPhaseDiagram } from "@/components/signals/MJOPhaseDiagram";
import { OLRMapPanel } from "@/components/signals/OLRMapPanel";
import { SSTMapPanel } from "@/components/signals/SSTMapPanel";
import { ResearchConnectionPanel } from "@/components/signals/ResearchConnectionPanel";

export const metadata = {
  title: "Live climate signals · CerealRisk",
  description:
    "Operational ENSO, MJO, OLR and SST indicators used to interpret agroclimatic risk."
};

export default function SignalsPage() {
  return (
    <section className="relative min-h-[100dvh] w-full bg-bg-deep pt-14">
      <div className="grid-bg absolute inset-0 opacity-35 pointer-events-none" />

      <div className="relative mx-auto max-w-[1440px] px-4 pb-24 pt-12 sm:px-6 lg:px-8">
        <header className="max-w-[900px] animate-fade-up">
          <p className="kicker">Climate teleconnection monitoring room</p>
          <h1 className="mt-3 font-display text-[clamp(2.1rem,4vw,3.8rem)] font-medium leading-[1] tracking-tightest text-ink">
            Live climate signals
          </h1>
          <p className="mt-4 max-w-[760px] text-[15px] leading-relaxed text-ink-dim">
            Operational ENSO, MJO, OLR and SST indicators used to interpret agroclimatic risk.
          </p>
          <p className="mt-3 max-w-[820px] text-[12.5px] leading-relaxed text-ink-mute">
            These signals describe the current ocean-atmosphere state. They are used as climate context for
            interpreting historical crop-yield sensitivity patterns, not as deterministic crop-yield forecasts.
          </p>
        </header>

        <div className="mt-8">
          <SignalHero />
        </div>

        <div className="mt-8 space-y-8">
          <ONIHistoricalChart />
          <MJOPhaseDiagram />
          <div className="grid grid-cols-1 gap-8 xl:grid-cols-2">
            <OLRMapPanel />
            <SSTMapPanel />
          </div>
          <ResearchConnectionPanel />
        </div>
      </div>
    </section>
  );
}
