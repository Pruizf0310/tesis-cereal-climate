import type { RiceConfidence } from "@/lib/types";
import { cn } from "@/lib/utils";

const META: Record<RiceConfidence, { label: string; className: string }> = {
  high: { label: "High confidence", className: "border-crop/40 bg-crop/[0.10] text-crop" },
  moderate: { label: "Moderate confidence", className: "border-warm/40 bg-warm/[0.10] text-warm" },
  low: { label: "Low confidence", className: "border-line bg-white/[0.04] text-ink-dim" }
};

export function ConfidenceBadge({ confidence }: { confidence: RiceConfidence }) {
  const meta = META[confidence];
  return (
    <span className={cn("inline-flex rounded-xs border px-2 py-1 text-[10.5px] font-medium", meta.className)}>
      {meta.label}
    </span>
  );
}
