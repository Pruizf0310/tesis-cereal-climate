import { Activity, ExternalLink } from "lucide-react";

interface SignalStatusCardProps {
  label: string;
  value: string;
  state: string;
  source: string;
  href: string;
  tone?: "warm" | "cool" | "neutral";
}

export function SignalStatusCard({ label, value, state, source, href, tone = "neutral" }: SignalStatusCardProps) {
  const color = tone === "warm" ? "text-warm" : tone === "cool" ? "text-cool" : "text-ink";
  return (
    <article className="glass rounded-sm p-4">
      <div className="flex items-center justify-between">
        <p className="kicker">{label}</p>
        <Activity className="h-3.5 w-3.5 text-cool" />
      </div>
      <p className={`num mt-3 text-[24px] font-medium ${color}`}>{value}</p>
      <p className="mt-1 text-[12px] text-ink-dim">{state}</p>
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="mt-4 inline-flex items-center gap-1.5 text-[10.5px] text-ink-mute transition hover:text-ink"
      >
        {source} <ExternalLink className="h-3 w-3" />
      </a>
    </article>
  );
}
