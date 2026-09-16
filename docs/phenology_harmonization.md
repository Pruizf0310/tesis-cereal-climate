# Phenological phase harmonization — 15 September 2026

> Calendar display update, 16 September: the first-listed-phase allocation described below is superseded by [coordinate calendars with explicit shared windows](pixel_calendar_method.md). This file preserves the hazard audit history.

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

Input: REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx, first worksheet, 63 rows. Columns T–V supply the observable variable, exact threshold/treatment value and exposure time. Empty exposure cells remain unspecified. Values and operators are preserved and translated to English. The workbook is read only.

The companion JSON audit records its SHA-256 and every original row's destination. Grouping uses crop × macro-phase × rule ID. Repeated original stages merge within that key, retaining all original codes, review rows and source pages. An evidence window spanning two supported macro-phases is indexed under both; this is not independent evidence or a new phase-specific effect estimate.

Eleven orange-marked rows do not enter as active assignments, but their review is reconciled against retained entries. Nine of the twelve non-published assignments (including one non-orange rice mismatch) retain the same rule/source in a supported phase. Three source rows have no same-rule replacement and must not be described as duplicates:

| Original rows | Review outcome | Retained evidence |
| --- | --- | --- |
| 33, 36, 42, 45, 51, 53 | Soybean seasonal heat is not assigned to unsupported EST/VEG/REP/MAT windows | Same rule in FLO and FIL, rows 38 and 48 |
| 50 | Soybean flooding evidence concerns flowering/podding, not filling | Same rule in FLO and REP, rows 41, 44 and 47 |
| 55 | Wheat heat experiment concerns seedlings | Same rule in EST, row 54; not specifically a germination trial |
| 23 | Rice submergence exposure does not establish a booting window | Same rule in VEG, rows 16, 17 and 19 |
| 10, 11 | Li 2025 rejected by human review as an onset threshold | No same-source replacement; other maize FIL studies are separate evidence |
| 34 | Alsajri 2018 gives a cardinal germination temperature, not a mortality/yield-loss threshold | No same-source replacement; other soybean EST hazards are separate evidence |

The website contains 47 grouped evidence entries in six sections per crop, plus a separately reserved maize REP row. Three-day wheat waterlogging remains the workbook value, explicitly described as a treatment without significant final-yield reduction; it is not advertised as a demonstrated yield-loss onset threshold. Row 67 remains contextual evidence only, pending user assignment of the maize REP threat.

## Calendar display only

No original calendar file, endpoint, phase date or duration is modified. The browser reads phenology_technical_v2.json and groups its existing stages for display into six rows. Combined windows (maize FLO+REP, rice VEG+REP, soybean FIL+MAT) are counted once under the first listed phase with an asterisk and an explicit note in both phases. The other phase is not assigned zero biological duration. Its separate dates are unresolved. Every original duration and monthly total is conserved; separate dates require additional evidence.

Only the hazard payload is generated by scripts/build_harmonized_phenology_v3.py. The intermediate v3 calendar file from the superseded implementation is removed. Archived source files retain original language; the active risk page uses English.
