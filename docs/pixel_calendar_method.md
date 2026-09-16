# Coordinate calendars and macro-phase correspondence

## Sources kept in this repository

1. Calendar workbook: [tabla_maestra_fenologia_global_v1.xlsx](../outputs/fenologia_v1/tabla_maestra_fenologia_global_v1.xlsx). Its `Catálogo fases` sheet is the technical-stage template; `Muestra matriz` is explicitly a sample, not the full grid.
2. Complete calendar matrix: [tabla_maestra_fenologia_global_v1.csv.gz](../outputs/fenologia_v1/tabla_maestra_fenologia_global_v1.csv.gz), 687,328 stage records and 85,916 coordinate calendars.
3. Reviewed correspondence and threats: [REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx](../metadata/reviewed_sources/REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx). `Hoja1` supplies the six macro-phase names and crop-specific correspondences. The first sheet supplies the reviewed hazard evidence. The original workbook is archived without editing its cells.

File hashes, generated season files and coverage counts are recorded in [pixel_calendar_provenance.json](pixel_calendar_provenance.json). No credentials are part of these inputs.

## What is sourced and what is estimated

[GGCMI Phase 3 v1.01](https://zenodo.org/records/5062513), DOI 10.5281/zenodo.5062513, supplies representative planting/maturity endpoints on a 0.5° grid, separately by season and water system. It is not an annual observed phenology record. The historical project estimated eight intermediate stages using normalized cycle fractions. Their names follow BBCH (rice), V/R (maize and soybean), and Zadoks/BBCH (wheat). The workbook preserves those fractions and labels their timing as an endpoint-based estimate.

All intermediate macro-phase boundaries remain estimates. The name of a staging scale is not evidence for a specific fraction of the growing cycle. The historical workbook does not supply an individually calibrated bibliographic derivation for each fraction. Recorded timing uncertainty is carried forward; it is not a statistical confidence interval.

The reviewed papers describe different exposure windows. For example, Liu et al. (2023), DOI 10.1016/j.xplc.2023.100629, relates flowering heat to seed set; that outcome does not establish a separately timed post-flowering REP exposure. Zhang et al. (2023), DOI 10.3390/agronomy13082126, distinguishes lag-stage heating 5–10 days after silking from effective filling 25–30 days after silking. These describe biological correspondence and experimental windows, not pixel-specific calendar dates. Exact review rows, page references and retained assignments remain in [phenology_harmonization_audit.json](phenology_harmonization_audit.json) and each hazard's website details.

## Replacing the spatial-average display

The active calendar no longer presents a mean monthly distribution across a latitude band as if it were the development of one crop. It selects an exact coordinate and season and shows continuous intervals relative to planting, with start/end month-day and cycle-year offsets. Unknown coordinates are unavailable; no nearest-pixel or band-average substitution occurs.

Original technical intervals are imported from the complete archived matrix. The generator verifies that the eight parent stages are consecutive, nonempty, start at planting and finish at maturity. It does not move small values to neighbouring months, invent days, or recalculate rounded averages.

## Shared phase windows

The reviewed Excel explicitly places parts of maize R1 in FLO and REP, rice BBCH_30_39 in VEG and REP, and soybean R6_R7 in FIL and MAT. The archive has no separate dates for those parts. Following the researcher's clarification on 16 September, the complete adjacent macro-phases are united into one interval: FLO+REP for maize, VEG+REP for rice, FIL+MAT for soybean. Wheat retains six separate intervals. This is a partition of the original cycle: each day appears exactly once, consecutive intervals have no gap and no overlap, and the durations sum to the complete cycle.

The vocabulary has six macro-phases; the number of separable temporal intervals may be five. Multiple hazard triggers are evaluated separately in a combined interval, with their original evidence phase retained. A probability in a combined interval refers to that full enclosing window, not to an independently resolved internal phase. This coarser exposure window must be disclosed. A future calibrated split must be versioned as a separate timing model; the current implementation does not invent one.

Rows are displayed in temporal order for the selected crop. Uniform macro-phase terminology does not force flowering to precede booting in rice/wheat.

## Years and leap days

The archived calendar uses a 365-day reference. Applying it to a historical year preserves each boundary's month and day. Windows crossing February 29 include that date; windows crossing December carry the correct year offset. A result year identifies the planting year. These are annual weather events within fixed reference phenology, not observed annual sowing or maturity dates.

## Reproduction

With Python and openpyxl installed, run from the repository root:

```sh
python scripts/build_pixel_calendars.py
python scripts/build_harmonized_phenology_v3.py metadata/reviewed_sources/REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx
cd web-v2
node scripts/check-pixel-calendars.mjs
```

The Excel catalogue, reviewed crosswalk and complete matrix are all explicit generator inputs. The manifest stores their hashes. The coordinate-window resolver is shared by the calendar and the `/api/hazard-probability` API. The old latitude-band calculation endpoint is retired. See [exposure probability method](gee_probability_method.md) for audited measurement definitions, event durations and missing-data handling.
