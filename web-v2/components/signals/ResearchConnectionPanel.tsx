export function ResearchConnectionPanel() {
  return (
    <section className="rounded-sm border border-line bg-gradient-to-br from-crop/[0.08] via-bg-panel/70 to-bg-panel/30 p-5 md:p-6">
      <p className="kicker">Historical crop-yield response baseline</p>
      <h2 className="mt-2 font-display text-[22px] font-medium tracking-tightest text-ink">
        From climate signal to crop response
      </h2>
      <p className="mt-3 max-w-[860px] text-[13px] leading-relaxed text-ink-dim">
        ENSO, MJO, OLR and SST describe the current ocean-atmosphere state. In this thesis, these signals are linked
        to historical cereal yield anomalies and phenological windows to interpret agroclimatic sensitivity, not to
        produce deterministic crop forecasts.
      </p>
      <div className="mt-5 grid grid-cols-1 gap-2 sm:grid-cols-3">
        <Metric label="Historical rice pixels" value="3,186" />
        <Metric label="Crop response" value="Yield anomalies" />
        <Metric label="Use in thesis" value="Sensitivity context" />
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-sm border border-line bg-bg-panel/75 p-3">
      <p className="kicker">{label}</p>
      <p className="mt-1 text-[13px] font-medium text-ink">{value}</p>
    </div>
  );
}
