import { SignalCardEnso } from "@/components/signals/enso-card";
import { SignalCardSoon } from "@/components/signals/soon-card";

export const metadata = {
  title: "Signals · CerealRisk",
  description:
    "The climate modes CerealRisk tracks: ENSO, MJO and the Pacific SST field that anchors them."
};

export default function SignalsPage() {
  return (
    <section className="relative min-h-[100dvh] w-full bg-bg-deep pt-14">
      <div className="grid-bg absolute inset-0 opacity-40 pointer-events-none" />

      <div className="relative mx-auto max-w-[1400px] px-6 pb-24 pt-16">
        <header className="max-w-[820px] animate-fade-up">
          <p className="kicker">Climate signals</p>
          <h1 className="mt-3 font-display text-[clamp(2.2rem,4.2vw,3.6rem)] font-medium leading-[1] tracking-tightest text-ink">
            ENSO and MJO: two coupled modes that drive agricultural exposure.
          </h1>
          <p className="mt-5 max-w-[640px] text-[14.5px] leading-relaxed text-ink-dim">
            CerealRisk tracks two climate modes. ENSO drives interannual yield swings through the
            Oceanic Niño Index, while the Madden–Julian Oscillation modulates precipitation and
            temperature on intraseasonal scales — compounding or dampening agricultural exposure
            within the same growing season.
          </p>
        </header>

        <div className="mt-14 grid grid-cols-1 gap-5 lg:grid-cols-2">
          <SignalCardEnso />
          <SignalCardSoon
            label="MJO"
            sublabel="Madden–Julian Oscillation"
            description="Eastward-propagating tropical convection. Tracked through RMM1/RMM2 amplitude and phase. Integration in progress."
            source="BoM RMM index · daily"
          />
        </div>

        {/* Methodology strip */}
        <section className="mt-20 grid grid-cols-1 gap-12 border-t border-line pt-12 md:grid-cols-3">
          <Stat label="Yield record" value="35 yrs" sub="1981–2016 · GDHY v1.2" />
          <Stat label="Pixels analyzed" value="3,187" sub="Quarter-degree · SOM-classified" />
          <Stat label="SOM classes" value="7" sub="Pacific climate classification" />
        </section>
      </div>
    </section>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div>
      <p className="kicker">{label}</p>
      <p className="num mt-2 font-display text-[clamp(1.8rem,3vw,2.6rem)] font-medium tracking-tightest text-ink">
        {value}
      </p>
      <p className="mt-1 text-[12px] text-ink-mute">{sub}</p>
    </div>
  );
}
