export function Footer() {
  return (
    <footer className="relative z-10 border-t border-line bg-bg-deep px-6 py-10 text-[12.5px] text-ink-mute">
      <div className="mx-auto flex max-w-[1400px] flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1.5">
          <p className="kicker">CerealRisk · exploratory climate-food risk intelligence</p>
          <p className="text-ink-dim">
            <span className="text-ink">Paola Andrea Ruiz Franco</span> · MSc Engineering — Water Resources
          </p>
          <p>Universidad Nacional de Colombia · Advisor: Carlos David Hoyos Ortiz</p>
        </div>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[11.5px]">
          <a
            href="https://github.com/Pruizf0310/tesis-cereal-climate"
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-ink"
          >
            Repository
          </a>
          <span aria-hidden className="h-3 w-px bg-line-strong" />
          <span>DOI · coming soon</span>
          <span aria-hidden className="h-3 w-px bg-line-strong" />
          <span className="num">© 1981–2016 GDHY · NOAA · GEOGLAM</span>
        </div>
      </div>
    </footer>
  );
}
