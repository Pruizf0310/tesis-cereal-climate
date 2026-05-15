interface SoonCardProps {
  label: string;
  sublabel: string;
  description: string;
  source: string;
}

export function SignalCardSoon({ label, sublabel, description, source }: SoonCardProps) {
  return (
    <article className="glass relative overflow-hidden rounded-sm p-6 animate-fade-up">
      <header className="flex items-start justify-between">
        <div>
          <p className="kicker">{sublabel}</p>
          <h2 className="mt-1 font-display text-[20px] font-medium tracking-tightest text-ink">{label}</h2>
        </div>
        <span className="rounded-xs border border-line bg-white/[0.02] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-ink-mute">
          pipeline
        </span>
      </header>

      <p className="mt-5 text-[12.5px] leading-relaxed text-ink-dim">{description}</p>

      {/* Skeleton chart that imitates the final visualization */}
      <div className="mt-5 space-y-2">
        <div className="skeleton h-[160px] w-full rounded-xs" />
        <div className="grid grid-cols-3 gap-1.5">
          <div className="skeleton h-7 rounded-xs" />
          <div className="skeleton h-7 rounded-xs" />
          <div className="skeleton h-7 rounded-xs" />
        </div>
      </div>

      <p className="mt-4 text-[11px] leading-snug text-ink-mute">{source}</p>
    </article>
  );
}
