// NOAA Oceanic Niño Index — annual mean of DJF, MAM, JJA, SON seasons.
// Source: https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php
// We embed the series here because the site is fully static; this is the same value used to
// align the agricultural pixels in /outputs/web/oni_*.csv.
const ONI_ANNUAL: { year: number; oni: number }[] = [
  { year: 1982, oni: 1.0 },
  { year: 1983, oni: 0.4 },
  { year: 1984, oni: -0.5 },
  { year: 1985, oni: -0.6 },
  { year: 1986, oni: 0.3 },
  { year: 1987, oni: 1.4 },
  { year: 1988, oni: -1.0 },
  { year: 1989, oni: -0.3 },
  { year: 1990, oni: 0.2 },
  { year: 1991, oni: 1.0 },
  { year: 1992, oni: -0.1 },
  { year: 1993, oni: 0.3 },
  { year: 1994, oni: 0.6 },
  { year: 1995, oni: -0.3 },
  { year: 1996, oni: -0.3 },
  { year: 1997, oni: 1.6 },
  { year: 1998, oni: -1.0 },
  { year: 1999, oni: -1.1 },
  { year: 2000, oni: -0.7 },
  { year: 2001, oni: -0.2 },
  { year: 2002, oni: 0.9 },
  { year: 2003, oni: 0.2 },
  { year: 2004, oni: 0.4 },
  { year: 2005, oni: -0.3 },
  { year: 2006, oni: 0.3 },
  { year: 2007, oni: -0.6 },
  { year: 2008, oni: -0.8 },
  { year: 2009, oni: 0.4 },
  { year: 2010, oni: -0.7 },
  { year: 2011, oni: -0.7 },
  { year: 2012, oni: -0.1 },
  { year: 2013, oni: -0.3 },
  { year: 2014, oni: 0.4 },
  { year: 2015, oni: 1.5 },
  { year: 2016, oni: -0.2 }
];

export function SignalCardEnso() {
  const last = ONI_ANNUAL[ONI_ANNUAL.length - 1];
  const peak = ONI_ANNUAL.reduce((m, d) => (d.oni > m.oni ? d : m), ONI_ANNUAL[0]);
  const trough = ONI_ANNUAL.reduce((m, d) => (d.oni < m.oni ? d : m), ONI_ANNUAL[0]);

  // Chart dims
  const W = 480;
  const H = 200;
  const PAD = { t: 16, r: 16, b: 28, l: 32 };
  const innerW = W - PAD.l - PAD.r;
  const innerH = H - PAD.t - PAD.b;
  const yMax = 2;
  const xScale = (i: number) => PAD.l + (i / (ONI_ANNUAL.length - 1)) * innerW;
  const yScale = (v: number) => PAD.t + innerH / 2 - (v / yMax) * (innerH / 2);

  return (
    <article className="glass relative overflow-hidden rounded-sm p-6 animate-fade-up">
      <header className="flex items-start justify-between">
        <div>
          <p className="kicker">El Niño–Southern Oscillation</p>
          <h2 className="mt-1 font-display text-[20px] font-medium tracking-tightest text-ink">ENSO</h2>
          <p className="mt-1 text-[12px] text-ink-dim">Oceanic Niño Index · 3-month running mean</p>
        </div>
        <span className="rounded-xs border border-cool/30 bg-cool/[0.08] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-cool">
          live
        </span>
      </header>

      <div className="mt-5">
        <svg viewBox={`0 0 ${W} ${H}`} className="h-[200px] w-full">
          {/* zero band */}
          <rect
            x={PAD.l}
            y={yScale(0.5)}
            width={innerW}
            height={yScale(-0.5) - yScale(0.5)}
            fill="rgba(255,255,255,0.025)"
          />
          {/* horizontal grid */}
          {[-1.5, -1, -0.5, 0, 0.5, 1, 1.5].map((v) => (
            <line
              key={v}
              x1={PAD.l}
              x2={PAD.l + innerW}
              y1={yScale(v)}
              y2={yScale(v)}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth={1}
              strokeDasharray={v === 0 ? "0" : "2 3"}
            />
          ))}
          {/* y labels */}
          {[-1, 0, 1].map((v) => (
            <text
              key={v}
              x={PAD.l - 6}
              y={yScale(v) + 3}
              fontSize={9}
              fill="#5B6E78"
              textAnchor="end"
              className="num"
            >
              {v > 0 ? `+${v.toFixed(1)}` : v.toFixed(1)}
            </text>
          ))}
          {/* bars */}
          {ONI_ANNUAL.map((d, i) => {
            const x = xScale(i);
            const y0 = yScale(0);
            const y1 = yScale(d.oni);
            const color = d.oni >= 0.5 ? "#D97B45" : d.oni <= -0.5 ? "#4FA0C9" : "#5B6E78";
            return (
              <rect
                key={d.year}
                x={x - 5}
                width={10}
                y={Math.min(y0, y1)}
                height={Math.abs(y1 - y0)}
                fill={color}
                opacity={Math.abs(d.oni) > 0.5 ? 0.9 : 0.5}
              />
            );
          })}
          {/* x ticks every 5 years */}
          {ONI_ANNUAL.filter((d) => d.year % 5 === 0).map((d) => {
            const i = ONI_ANNUAL.findIndex((dd) => dd.year === d.year);
            return (
              <text
                key={d.year}
                x={xScale(i)}
                y={H - 8}
                fontSize={9}
                fill="#5B6E78"
                textAnchor="middle"
                className="num"
              >
                {d.year}
              </text>
            );
          })}
        </svg>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-px overflow-hidden rounded-sm border border-line bg-line text-[11px]">
        <Stat label="2016 end" value={`${last.oni > 0 ? "+" : ""}${last.oni.toFixed(1)}°C`} />
        <Stat label="Peak" value={`${peak.year} · +${peak.oni.toFixed(1)}`} accent="var(--enso-nino)" />
        <Stat label="Trough" value={`${trough.year} · ${trough.oni.toFixed(1)}`} accent="var(--enso-nina)" />
      </div>

      <p className="mt-4 text-[11px] leading-snug text-ink-mute">
        Source: NOAA CPC · ONI v5. CerealRisk aligns this index to each pixel&apos;s top-2 critical
        seasons before composing yield responses.
      </p>
    </article>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="bg-bg-panel/80 px-3 py-2.5">
      <p className="kicker">{label}</p>
      <p className="num mt-1 font-medium" style={{ color: accent ?? "var(--ink)" }}>
        {value}
      </p>
    </div>
  );
}
