export const metadata = {
  title: "About · CerealRisk",
  description:
    "Climate-Food Risk Explorer — geospatial intelligence platform for ENSO-MJO driven agricultural risk."
};

export default function AboutPage() {
  return (
    <section className="relative min-h-[100dvh] w-full bg-bg-deep pt-14">
      <div className="grid-bg absolute inset-0 opacity-40 pointer-events-none" />

      <div className="relative mx-auto max-w-[1400px] px-6 pb-24 pt-16">
        {/* Hero */}
        <header className="max-w-[780px] animate-fade-up">
          <p className="kicker">About</p>
          <h1 className="mt-3 font-display text-[clamp(2.2rem,4.2vw,3.6rem)] font-medium leading-[1] tracking-tightest text-ink">
            Geospatial intelligence for ENSO-MJO driven agricultural risk.
          </h1>
          <p className="mt-5 max-w-[620px] text-[14.5px] leading-relaxed text-ink-dim">
            CerealRisk is an interactive climate-risk platform that translates ENSO and MJO signals
            into spatially resolved agricultural exposure across global cereal systems.
          </p>
        </header>

        {/* Two-column layout */}
        <div className="mt-16 grid grid-cols-1 gap-12 md:grid-cols-2">
          {/* Left — platform */}
          <div className="space-y-8 animate-fade-up">
            <Section
              kicker="Platform"
              title="What this explores"
              body="The platform integrates 35 years of cereal yield records with ENSO and MJO climate indices. Each agricultural pixel is classified by its historical response to climate variability, revealing where crops are most exposed during critical phenological windows."
            />
            <Section
              kicker="Scope"
              title="Four cereal systems"
              body="Maize, rice, wheat and soybean — the four crops that supply the majority of global caloric intake. Each system is analyzed independently across its primary production regions."
            />
            <Section
              kicker="Signals"
              title="ENSO and MJO"
              body="The Oceanic Niño Index captures interannual climate swings. The Madden–Julian Oscillation adds intraseasonal resolution, modulating precipitation and temperature within the same growing season. Together, they explain a significant share of observed yield variance in climate-sensitive regions."
            />
          </div>

          {/* Right — methodology + context */}
          <div className="space-y-8 animate-fade-up">
            <Section
              kicker="Methodology"
              title="How risk is derived"
              body="Yield anomalies from the Global Dataset of Historical Yields are intersected with ENSO-phase composites and crop calendars from GEOGLAM. A Self-Organizing Map groups pixels by their Pacific climate fingerprint. Risk levels reflect yield-anomaly dispersion in each class."
            />
            <Section
              kicker="Application"
              title="Who this is for"
              body="The platform is designed for climate-risk analysts, agri-insurance teams, catastrophe modelers, and research institutions working at the intersection of climate variability and food-system resilience."
            />
            <Section
              kicker="Status"
              title="Exploratory intelligence"
              body="CerealRisk presents exploratory risk signals and trigger candidates derived from historical data. Results are research-grade and intended for analytical exploration, not operational decision-making."
            />
          </div>
        </div>

        {/* Data sources strip */}
        <div className="mt-20 border-t border-line pt-10">
          <p className="kicker mb-6">Data sources</p>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {[
              { label: "GDHY v1.2", sub: "Yield records · 1981–2016" },
              { label: "NOAA CPC", sub: "ONI v5 · ENSO index" },
              { label: "BoM RMM", sub: "MJO index · daily" },
              { label: "GEOGLAM", sub: "Crop calendars · phenology" }
            ].map((s) => (
              <div key={s.label} className="glass rounded-sm px-4 py-3">
                <p className="text-[13px] font-medium text-ink">{s.label}</p>
                <p className="mt-0.5 text-[11px] text-ink-mute">{s.sub}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Author */}
        <div className="mt-16 border-t border-line pt-10 animate-fade-up">
          <p className="kicker mb-4">Research</p>
          <div className="max-w-[520px] space-y-1 text-[13px] text-ink-dim">
            <p className="text-[15px] font-medium text-ink">Paola Andrea Ruiz Franco</p>
            <p>MSc Engineering — Water Resources</p>
            <p>Universidad Nacional de Colombia</p>
            <p className="pt-1">
              Thesis advisor:{" "}
              <span className="text-ink">Carlos David Hoyos Ortiz</span>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function Section({ kicker, title, body }: { kicker: string; title: string; body: string }) {
  return (
    <div className="border-t border-line pt-6">
      <p className="kicker">{kicker}</p>
      <h2 className="mt-2 font-display text-[17px] font-medium tracking-tighter text-ink">{title}</h2>
      <p className="mt-2 text-[13px] leading-relaxed text-ink-dim">{body}</p>
    </div>
  );
}
