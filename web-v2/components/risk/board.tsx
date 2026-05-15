"use client";

import { useEffect, useState } from "react";
import { loadCsv } from "@/lib/csv";
import type { ClusterMean, TriggerCandidate, SomClassSummary } from "@/lib/types";
import { SomRadar } from "./som-radar";
import { TriggerTable } from "./trigger-table";
import { OniYieldCurve } from "./oni-yield-curve";

export function RiskBoard() {
  const [means, setMeans] = useState<ClusterMean[]>([]);
  const [triggers, setTriggers] = useState<TriggerCandidate[]>([]);
  const [summary, setSummary] = useState<SomClassSummary[]>([]);

  useEffect(() => {
    Promise.all([
      loadCsv<ClusterMean>("/data/cluster_means.csv"),
      loadCsv<TriggerCandidate>("/data/trigger_summary.csv"),
      loadCsv<SomClassSummary>("/data/som_summary.csv")
    ]).then(([m, t, s]) => {
      setMeans(m);
      setTriggers(t);
      setSummary(s);
    });
  }, []);

  const totalPixels = summary.reduce((s, r) => s + (r.count ?? 0), 0);

  return (
    <div className="mt-14 space-y-16">
      {/* SOM fingerprints */}
      <section>
        <div className="flex items-end justify-between border-b border-line pb-4">
          <div>
            <p className="kicker">Block 1</p>
            <h2 className="mt-1 font-display text-[22px] font-medium tracking-tightest text-ink">
              SOM class fingerprints
            </h2>
          </div>
          <p className="text-[11.5px] text-ink-mute">
            7 classes · {totalPixels.toLocaleString("en-US")} pixels
          </p>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {means.map((m) => {
            const s = summary.find((x) => x.label === m.label);
            const trigger = triggers.find((t) => t.som_label === m.label);
            return <SomRadar key={m.label} mean={m} summary={s} trigger={trigger} />;
          })}
        </div>
      </section>

      {/* ONI → yield curve */}
      <section>
        <div className="flex items-end justify-between border-b border-line pb-4">
          <div>
            <p className="kicker">Block 2</p>
            <h2 className="mt-1 font-display text-[22px] font-medium tracking-tightest text-ink">
              ONI threshold &rarr; yield response
            </h2>
          </div>
          <p className="text-[11.5px] text-ink-mute">35 years per pixel · top-2 critical seasons</p>
        </div>
        <OniYieldCurve triggers={triggers} />
      </section>

      {/* Trigger table */}
      <section>
        <div className="flex items-end justify-between border-b border-line pb-4">
          <div>
            <p className="kicker">Block 3</p>
            <h2 className="mt-1 font-display text-[22px] font-medium tracking-tightest text-ink">
              Exploratory trigger candidates
            </h2>
          </div>
          <p className="text-[11.5px] text-ink-mute">Not validated parametric thresholds</p>
        </div>
        <TriggerTable triggers={triggers} summary={summary} />
      </section>

      {/* Disclaimer */}
      <section className="border-t border-line pt-6">
        <p className="max-w-[820px] text-[12.5px] leading-relaxed text-ink-mute">
          These thresholds are exploratory empirical candidates derived from historical co-occurrence
          of ONI peaks and yield anomalies within each SOM class. They have not been validated for
          basis risk, hedging effectiveness, or actuarial deployment.
        </p>
      </section>
    </div>
  );
}
