import { maizeReproductiveEvidence as evidence } from "@/lib/maize-reproductive-evidence";

export function MaizeReproductiveNote() {
  return (
    <aside className="border-b border-line bg-warm/[0.035] px-4 py-4 text-[11px] leading-relaxed text-ink-dim">
      <h3 className="font-medium text-ink">REP — Initial kernel set: heat evidence</h3>
      <p className="mt-1">Zhang et al. (2023) observed fewer kernels after six days of daytime heating, 5–10 days after silking. This supports heat as a hazard during initial kernel set, with possible overlap into R2. The paper calls this window the lag stage.</p>
      <p className="mt-1">A damage-onset temperature remains unresolved. The experiment does not define regional calendar dates or a threshold for climate exceedance calculations.</p>
      <a className="mt-2 inline-block text-cool underline underline-offset-2" href={`https://doi.org/${evidence.details.link}`} target="_blank" rel="noreferrer">Zhang et al. (2023), pp. 2, 5–6</a>
    </aside>
  );
}
