import { cn } from "@/lib/utils";

export function MJOPhaseWheel({
  phaseYield,
  riskPhases,
  worstPhase
}: {
  phaseYield: Record<string, number | null>;
  riskPhases: number[];
  worstPhase: number | null;
}) {
  const phases = Array.from({ length: 8 }, (_, i) => i + 1);
  const hasValues = phases.some((phase) => phaseYield[String(phase)] != null);

  return (
    <div className="grid grid-cols-4 gap-1.5">
      {phases.map((phase) => {
        const value = phaseYield[String(phase)];
        const risk = riskPhases.includes(phase);
        const worst = worstPhase === phase;
        return (
          <div
            key={phase}
            className={cn(
              "rounded-sm border px-2 py-2",
              worst
                ? "border-risk-extr/50 bg-risk-extr/[0.12]"
                : risk
                  ? "border-warm/40 bg-warm/[0.08]"
                  : "border-line bg-white/[0.02]"
            )}
          >
            <div className="flex items-center justify-between">
              <span className="kicker">P{phase}</span>
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  worst ? "bg-risk-extr" : risk ? "bg-warm" : "bg-ink-mute/40"
                )}
              />
            </div>
            <p className="num mt-1 text-[12px] text-ink">
              {value == null ? "na" : value.toFixed(2)}
            </p>
          </div>
        );
      })}
      {!hasValues && (
        <p className="col-span-4 text-[10.5px] leading-snug text-ink-mute">
          MJO monthly phase arrays were not available during the local build, so phase risk remains unscored.
        </p>
      )}
    </div>
  );
}
