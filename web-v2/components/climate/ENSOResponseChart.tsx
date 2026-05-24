const LABELS = [
  ["sn", "Strong La Nina"],
  ["n", "La Nina"],
  ["neu", "Neutral"],
  ["el", "El Nino"],
  ["sel", "Strong El Nino"]
] as const;

const COLORS: Record<string, string> = {
  sn: "var(--enso-nina)",
  n: "#6FB7D5",
  neu: "var(--enso-neut)",
  el: "#D97B45",
  sel: "#B23D3D"
};

export function ENSOResponseChart({
  bins
}: {
  bins: Record<"sn" | "n" | "neu" | "el" | "sel", number | null>;
}) {
  const values = LABELS.map(([key]) => bins[key]).filter((v): v is number => typeof v === "number");
  const maxAbs = Math.max(0.25, ...values.map((v) => Math.abs(v)));

  return (
    <div className="space-y-2">
      {LABELS.map(([key, label]) => {
        const value = bins[key];
        const width = value == null ? 0 : Math.min(100, (Math.abs(value) / maxAbs) * 100);
        return (
          <div key={key} className="grid grid-cols-[86px_1fr_42px] items-center gap-2">
            <span className="text-[10.5px] text-ink-mute">{label}</span>
            <div className="relative h-2 rounded-xs bg-white/[0.04]">
              <span className="absolute left-1/2 top-[-2px] h-3 w-px bg-white/[0.08]" />
              {value != null && (
                <span
                  className="absolute top-0 h-2 rounded-xs"
                  style={{
                    width: `${width / 2}%`,
                    backgroundColor: COLORS[key],
                    left: value < 0 ? `${50 - width / 2}%` : "50%"
                  }}
                />
              )}
            </div>
            <span className="num text-right text-[10.5px] text-ink-dim">
              {value == null ? "na" : value.toFixed(2)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
