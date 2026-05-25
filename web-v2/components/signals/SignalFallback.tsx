import { ExternalLink } from "lucide-react";

export function SignalFallback({
  title,
  message,
  href
}: {
  title: string;
  message: string;
  href: string;
}) {
  return (
    <div className="flex min-h-[260px] flex-col items-center justify-center rounded-sm border border-line bg-white/[0.02] p-8 text-center">
      <p className="kicker">{title}</p>
      <p className="mt-3 max-w-[420px] text-[12.5px] leading-relaxed text-ink-dim">{message}</p>
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="mt-5 inline-flex items-center gap-2 rounded-sm border border-line-strong bg-white/[0.03] px-3 py-2 text-[12px] text-ink transition hover:bg-white/[0.06]"
      >
        Open official product <ExternalLink className="h-3.5 w-3.5" />
      </a>
    </div>
  );
}
