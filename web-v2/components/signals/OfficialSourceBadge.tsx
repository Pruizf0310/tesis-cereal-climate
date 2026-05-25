import { ExternalLink } from "lucide-react";

export function OfficialSourceBadge({ source, href }: { source: string; href: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1.5 rounded-xs border border-cool/30 bg-cool/[0.08] px-2 py-1 text-[10.5px] font-medium text-cool transition hover:border-cool/60"
    >
      {source}
      <ExternalLink className="h-3 w-3" />
    </a>
  );
}
