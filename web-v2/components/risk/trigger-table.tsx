"use client";

import type { TriggerCandidate, SomClassSummary } from "@/lib/types";
import { formatNumber, formatSigned } from "@/lib/utils";

interface TriggerTableProps {
  triggers: TriggerCandidate[];
  summary: SomClassSummary[];
}

export function TriggerTable({ triggers, summary }: TriggerTableProps) {
  return (
    <div className="mt-6 overflow-x-auto rounded-sm border border-line glass animate-fade-up">
      <table className="w-full min-w-[640px] border-collapse">
        <thead>
          <tr className="border-b border-line text-left text-[10.5px] uppercase tracking-wider text-ink-mute">
            <Th>Class</Th>
            <Th>ONI threshold</Th>
            <Th>Yield Δ range</Th>
            <Th>Spread</Th>
            <Th>Sample (yrs)</Th>
            <Th>Cohort share</Th>
            <Th>Status</Th>
          </tr>
        </thead>
        <tbody>
          {triggers.map((t) => {
            const s = summary.find((x) => x.label === t.som_label);
            const range = (t.curve_max_yield ?? 0) - (t.curve_min_yield ?? 0);
            return (
              <tr
                key={t.som_label}
                className="border-b border-line/60 text-[12.5px] transition-colors last:border-b-0 hover:bg-white/[0.02]"
              >
                <Td>
                  <div className="flex items-center gap-2">
                    <span
                      className="inline-block h-1.5 w-1.5 rotate-45"
                      style={{ backgroundColor: colorFor(t.som_label) }}
                    />
                    Class {t.som_label}
                  </div>
                </Td>
                <Td className="num text-ink">≥ {formatSigned(t.trigger_oni_approx, 2)}</Td>
                <Td className="num">
                  <span className="text-enso-nina">{formatSigned(t.curve_min_yield, 2)}</span>
                  <span className="mx-1 text-ink-mute">·</span>
                  <span className="text-enso-nino">{formatSigned(t.curve_max_yield, 2)}</span>
                </Td>
                <Td className="num text-ink-dim">{formatNumber(range, 2)}</Td>
                <Td className="num text-ink-dim">{t.n_years}</Td>
                <Td className="num text-ink-dim">
                  {s ? `${(s.fraction * 100).toFixed(1)}%` : "—"}
                </Td>
                <Td>
                  <span className="rounded-xs border border-warm/30 bg-warm/[0.08] px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-warm">
                    exploratory
                  </span>
                </Td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 font-medium">{children}</th>;
}
function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-4 py-3 ${className ?? ""}`}>{children}</td>;
}

function colorFor(label: number): string {
  const PALETTE = ["#7FD4DF", "#F1B257", "#7FAF7B", "#4FA0C9", "#D97B45", "#B23D3D", "#9F8CC9"];
  return PALETTE[label % PALETTE.length];
}
