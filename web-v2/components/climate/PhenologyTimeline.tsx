import { cn } from "@/lib/utils";

const MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];

export function PhenologyTimeline({
  sensitivePhase,
  criticalMonths,
  peakMonth
}: {
  sensitivePhase: string;
  criticalMonths: number[];
  peakMonth: number;
}) {
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-12 gap-1">
        {MONTHS.map((month, i) => {
          const m = i + 1;
          const critical = criticalMonths.includes(m);
          const peak = peakMonth === m;
          return (
            <div
              key={`${month}-${i}`}
              className={cn(
                "flex h-8 items-center justify-center rounded-xs border text-[10.5px]",
                peak
                  ? "border-warm bg-warm/[0.18] text-warm"
                  : critical
                    ? "border-crop/40 bg-crop/[0.10] text-crop"
                    : "border-line bg-white/[0.02] text-ink-mute"
              )}
            >
              {month}
            </div>
          );
        })}
      </div>
      <div className="flex items-center justify-between text-[10.5px] text-ink-mute">
        <span>Critical window: {criticalMonths.join(", ") || "not scored"}</span>
        <span className="text-warm">{sensitivePhase.replace("_", " ")}</span>
      </div>
    </div>
  );
}
