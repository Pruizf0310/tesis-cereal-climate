# Phenological phase harmonization — 15 September 2026

## Research decision

Following the paper-by-paper review and human phase audit, this project adopts six shared macro-phases: EST (Establishment), VEG (Vegetative growth), FLO (Flowering), REP (Reproductive development), FIL (Grain/seed filling), and MAT (Maturation).

The reviewed literature uses different names, codes and phase boundaries across crops and studies. This does not mean that published staging scales do not exist: BBCH, Zadoks and crop-specific V/R scales remain valid source descriptions. The six labels are a project harmonization by biological correspondence, not a claim of a universally standardized scale. Original source stages, source links, page locations and review-row identifiers remain visible in the website.

## Evidence and assignment

- Liu et al. (2023) discusses heat during flowering and evaluates seed set. An effect on seed set does not independently establish exposure during post-flowering REP. The maize flowering rows therefore map to FLO only.
- Zhang et al. (2023), https://doi.org/10.3390/agronomy13082126, methods section 2.2 and results/Table 1, distinguishes lag stage (5–10 days after silking) from effective filling (25–30 days after silking). The former can inform initial kernel-set evidence, but does not provide a calibrated damage-onset temperature. Maize REP remains reserved for user assignment.
- The human audit preserves crop-specific distinctions: rice/wheat booting and heading map to REP before FLO; soybean pod formation maps to REP after FLO. The six definitions are not a universal chronological sequence across crops.
- Hazard assignments use the intersection of the reviewed paper macro-phases and original calendar macro-phases. A rice submergence assignment to booting is excluded because the reviewed exposure supports seedlings/vegetative growth, not that REP window.
- Experimental temperatures, durations and water levels remain study treatments where appropriate. Harmonizing a phase does not validate a universal threshold, local occurrence, transferability or an independent phase-specific yield effect.

## Selection and traceability

Input: REVISION_HUMANA_fases_macro_completada.xlsx, first worksheet. The companion JSON audit records its SHA-256 and row-level decisions. Eleven rows with orange review cells (theme accent 2, tint 0.3999755851924192) are excluded by crop × original phase × rule ID. Exclusion is not applied globally to a paper that remains relevant in another accepted phase. The workbook is read only.

The website contains 50 retained evidence rows and a separately reserved maize REP row. Three-day wheat waterlogging is explicitly described as a treatment without significant final-yield reduction; it is not advertised as a demonstrated yield-loss onset threshold.

## Calendar construction

The original GGCMI endpoint-based technical calendars remain the numerical source. Adjacent stages assigned to the same macro-phase are summed. Combined original windows remain combined: maize FLO+REP, rice VEG+REP, soybean FIL+MAT. They are not arbitrarily divided, and their days are not duplicated into separate rows. Every original duration and monthly total is conserved. Separate dates require additional evidence or an explicitly approved temporal model.

The v3 website payloads are separate from the historical v2 data, so older generators do not silently overwrite this reviewed release. Changes to the audit require a deliberate regeneration and review of the v3 payloads. Archived source files retain original language; the active risk page uses English.
