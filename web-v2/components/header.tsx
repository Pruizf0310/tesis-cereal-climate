import Link from "next/link";

const NAV = [
  { href: "/", label: "Explorer" },
  { href: "/signals", label: "Signals" },
  { href: "/risk", label: "Risk" },
  { href: "/about", label: "About" }
];

export function Header() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 flex h-14 items-center justify-between border-b border-line bg-bg-deep/60 px-6 backdrop-blur-md">
      <Link href="/" className="group flex items-center gap-2.5">
        <span
          aria-hidden
          className="relative h-4 w-4 rotate-45 rounded-[2px] bg-gradient-to-br from-cool via-crop to-warm shadow-[0_0_18px_rgba(127,212,223,0.45)] transition-transform group-hover:scale-110"
        />
        <span className="text-[13px] font-semibold tracking-[-0.01em] text-ink">
          CerealRisk
        </span>
      </Link>

      <nav aria-label="Primary" className="hidden items-center gap-1 md:flex">
        {NAV.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className="rounded-sm px-3 py-1.5 text-[12.5px] font-medium text-ink-dim transition-colors hover:bg-white/[0.04] hover:text-ink"
          >
            {label}
          </Link>
        ))}
      </nav>

      <div className="hidden items-center gap-2 md:flex">
        <span className="kicker">v0.2 · preview</span>
      </div>
    </header>
  );
}
