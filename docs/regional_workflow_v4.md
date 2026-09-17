# Regional calendars and duration-aware exposure workflow — v4

Version: `regional-v4-2026-09-16`. This document supersedes the coordinate-entry and combined-window workflow of v3. The original workbooks and matrix are preserved. Changes are project research decisions, not claims that every paper uses a standardized vocabulary.

## 1. Inputs and reproducible provenance

| Input | Role |
|---|---|
| [Original calendar Excel](../outputs/fenologia_v1/tabla_maestra_fenologia_global_v1.xlsx) | Eight technical stages per crop, original scale codes and normalized phase fractions in `Catálogo fases`. The sample sheet is not the complete matrix. |
| [Complete archived matrix](../outputs/fenologia_v1/tabla_maestra_fenologia_global_v1.csv.gz) | 687,328 original technical-stage rows; 85,916 crop/season/location calendars. Supplies the actual archived integer boundaries. |
| [Human-reviewed hazard Excel](../metadata/reviewed_sources/REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx) | Paper excerpts, source rows/pages, reviewed phase correspondence, quantities, thresholds and exposure durations. Read-only original. |
| [Versioned correspondence](../metadata/six_phase_correspondence_v4.json) | Explicit v4 overrides, biological rationale and supporting sources; preserves the earlier reviewed mapping alongside the operational mapping. |
| [Crop inventory](../web-v2/public/data/phase_pixel_inventory.csv) | Restricts selectable locations to the archived crop inventory. It does not prove cultivation in every historical year. |
| [Calendar provenance](pixel_calendar_provenance.json) | Source paths, SHA-256 hashes, versions and all generated season files. |
| [Variable registry](../web-v2/public/data/gee_rule_audit.json) | Exact equations, units, operators, durations, source assignments, transfer limitations and access route. |

The reviewed hazard workbook SHA-256 remains `cf4052536715a29402e67f5dcacdefaac10b23fcf6ecbaab4ea4a952e8b60e5f`. Orange exclusions and their reconciliation remain in the original harmonization audit; v4 does not reactivate them. There are 47 retained crop/phase/rule assignments and 35 distinct rules. Maize REP retains its reserved hazard slot pending the researcher's assignment.

### Calendar origin and estimated quantities

Planting and maturity endpoints originate in [GGCMI Phase 3 v1.01](https://doi.org/10.5281/zenodo.5062513). Intermediate phase dates were constructed by the project from normalized technical-stage fractions. They are not intermediate dates observed annually by GGCMI. The archived material does not establish a crop/location-calibrated paper derivation for every fraction; that uncertainty must remain explicit in the thesis.

The original scales are maize V/R, rice BBCH, soybean Fehr–Caviness and wheat Zadoks/BBCH. The six shared labels are an operational crosswalk: EST establishment, VEG vegetative growth, FLO flowering, REP reproductive development, FIL grain/seed filling, MAT maturation. They are not a new universal botanical scale. REP can precede FLO in rice/wheat and follow FLO in maize/soybean. Rows are ordered by actual chronology, not alphabetically or by a universal code sequence.

## 2. From eight technical stages to six continuous windows

The old monthly latitude aggregates could show disconnected fragments because different crop calendars were combined. V3 instead used individual calendars and joined ambiguous phase labels. V4 responds to the request for six phases by revising the assignment of intact technical blocks; it never cuts a block at an invented date.

| Crop | Correspondence decision | Scientific scope |
|---|---|---|
| Maize | R1 → FLO; R2 → REP; R3 and R4–R5 → FIL; R6 → MAT. Establishment and vegetative blocks retained. | R2 is early kernel/blister development. Filling can already begin biologically, so this is a mutually exclusive analytical partition. A published lag-stage treatment is not asserted to coincide exactly with the entire R2 window. |
| Rice | Leaf development and tillering → VEG; complete BBCH 30–39 panicle-initiation block joins booting/heading in REP; anthesis → FLO. | IRRI places the reproductive transition at panicle initiation. Retaining the complete original block does not resolve its internal transition timing. |
| Soybean | R5 and archived R6–R7 → FIL; terminal R8 block → MAT. | The aggregated R6–R7 block cannot identify an observed R7 date. The terminal maturity boundary is therefore an estimated operational boundary, not a newly measured date. |
| Wheat | Original reviewed single-phase correspondence retained. | Six consecutive windows already exist. |

Supporting stage descriptions: [University of Minnesota maize stages](https://ipmworld.umn.edu/maize-insect-pests-maize-growth-development), [University of Delaware maize stages](https://www.udel.edu/academics/colleges/canr/cooperative-extension/fact-sheets/corn-growth-stages-and-management/), [IRRI growth stages](https://www.knowledgebank.irri.org/ericeproduction/0.2._Growth_stages_of_the_rice_plant.htm), [Mississippi State soybean stages](https://www.extension.msstate.edu/publications/guide-soybean-growth-stages), [Nebraska soybean filling and maturity](https://cropwatch.unl.edu/setting-yield-soybean-and-avoiding-end-season-plant-stress-unl-cropwatch-aug-23-2013/).

Every technical day belongs to exactly one macro-phase; each macro-phase is a single contiguous interval with positive duration. The planting date, maturity date and total cycle remain unchanged. The 365-day reference calendar preserves month/day in leap years, assigning 29 February to the phase containing it without gaps or duplicate days. Cross-year phases retain their planting-year identifier.

## 3. Latitude bands and regional selection

Navigation uses 10-degree latitude bands, 30-degree longitude sectors and two-month planting regimes. These are transparent browsing groups, not claims of homogeneous climate. Rainfed/irrigated systems and multiple crop seasons remain separate.

Within each group the representative is an existing inventory cell minimizing the sum of absolute deviations from median planting day and median cycle length. Its intact calendar is displayed, together with the group's minimum/maximum cycle length and cell count. No monthly phase fragments are averaged. Calculations use the selected cell's own six windows, not the representative's dates for every cell.

Up to 12 candidates are selected deterministically for spatial spread, starting with the representative, before observing weather. The screening button checks the selected rule, duration, phase and year for those candidates. Results distinguish exposure, no qualifying exposure, missing/too-short data and query failure. This is a sample, not an exhaustive regional search. Selecting an exposed location after screening is outcome-based exploration; its historical frequency is not an unbiased regional probability. The complete JSON preserves screening outcomes, including failures.

## 4. Exact threat variables and access

[The full 35-rule table](variable_equivalences_v4.md) distinguishes source quantity, operational equation and limitations. Twenty-five definitions query GEE. Ten require a specified external measured or independently modelled quantity and are calculable through CSV import. A defined equivalence is not proof of globally calibrated damage prediction.

GEE collections:

- [ERA5-Land daily aggregates](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR): daily mean/minimum/maximum 2 m air temperature, daily precipitation, soil water layers.
- [ERA5-Land hourly](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY): 2 m temperature, hourly precipitation increments and 10 m wind components.
- [OpenLandMap field capacity at 33 kPa](https://developers.google.com/earth-engine/datasets/catalog/OpenLandMap_SOL_SOL_WATERCONTENT-33KPA_USDA-4B1C_M_v01): `b0` and `b10`, converted from volumetric percent to fraction. Static auxiliary reference for the explicitly qualified rice soil-moisture proxy.

Climate is reduced to a mean over the selected 0.5-degree crop-inventory cell at 11,132 m scale. This is not a farm observation or a crop-area-weighted estimate. Wind magnitude is computed from components before reduction. Negative rainfall artifacts become missing. Hourly precipitation timestamps denote the end of the accumulation interval and are shifted back one hour for event indexing.

### Explicit research qualifications

- Day/night means use fixed solar-clock cycles beginning at 06:00, with longitude/15 rounded to the nearest hour. Default day/night is 12/12 hours; the wheat 35/30 C treatment uses 16/8 hours (night 22:00–06:00). These are not astronomical sunrise/sunset. Each relevant cycle must have all required hourly samples. Paired treatments require both temperature conditions in the same cycle. Exports use UTC and include the solar offset.
- [Maize emergence cold experiment](https://doi.org/10.1371/journal.pone.0340773) specifies chamber temperature programming; 2 m reanalysis air temperature is a stated field transfer, not soil temperature.
- [Maize filling high-night-temperature study](https://doi.org/10.3389/fpls.2026.1826388) defines daily minimum temperature treatments and an 18-day exposure. V4 uses daily minimum, with the UTC-versus-local-day limitation disclosed.
- The rice relative-moisture proxy uses `100*(0.7*theta_0_7 + 0.3*theta_7_28)/theta_FC`. [Sun et al.](https://esd.copernicus.org/articles/16/1971/2025/) uses surface relative soil moisture, but the field-capacity denominator was not verified in the paper. It is a project choice combining two data products and requires local validation. It is not a percentile and not an exact reproduction of the source model.
- [Schauberger et al.](https://doi.org/10.1038/ncomms13931) accumulates fractional days in temperature bins over a fixed growing season using sinusoidal interpolation of daily extrema. V4 accumulates hourly reanalysis exposure above 30 C within the selected phase. Default classification is at least 24 accumulated hours, not 24 consecutive hours. The event cutoff and phase application are project choices; no phase-specific yield coefficient is inferred.
- Where the reviewed wording says more than one week, the operational count is at least eight complete nights; original workbook seven-day text remains preserved. Strict flooding durations greater than three/six days become four/seven complete days.
- When a paper supplies a treatment value but no damaging-duration breakpoint, the default is an explicitly marked analysis setting. Duration controls are sensitivity analysis, not a claim about the maximum a plant tolerates.

The ten external variables are soil matric potential, complete submergence, flooding/waterlogging, standing-water depth, matched-control moisture reduction, canopy minimum temperature and matched-control nighttime temperature difference. CSV templates require exact identifiers/units and a nonempty source. Empty values stay missing; mismatched coordinates, units, timestamps and binary indicators are rejected. The file is processed in the browser and its SHA-256 is retained. Rainfall is not substituted for flooding, 2 m air temperature is not silently substituted for canopy temperature, and climatological anomalies do not replace experimental controls.

## 5. Event duration, probability and downloads

For consecutive rules, qualifying runs must meet the selected duration; a missing time step breaks continuity and makes the annual phase ineligible for the probability denominator. The six-day maize rolling-mean rule marks the union of qualifying complete six-day windows; changing the minimum event duration does not change the averaging window. For accumulated soybean heat, all above-threshold hours contribute even if separated; exported intervals show the contributing runs.

`P(exposure in phase) = evaluable planting years meeting the selected event / evaluable planting years`.

A valid year requires the complete requested series and enough time to assess the selected duration. Missing, failed or too-short years are never counted as zero-event years. This is a historical frequency conditional on the selected crop cell, phase definition and threshold; it is not a fitted future probability, yield-loss probability or insurance payout. Calendars are repeated climatological estimates, not annual planting observations. A day/night cycle can extend into the next civil date but adjacent phase cycles remain contiguous.

The interface shows the selected-year series, threshold, event samples, longest runs by year, coverage, event intervals and duration sensitivity. Duration sensitivity recalculates the eligible denominator for each duration. Accumulated rules use total exposed hours for this curve, while their longest-run chart remains a separate diagnostic.

Downloads:

| File | Contents |
|---|---|
| Analysis series CSV | UTC timestamp, evaluated quantity, paired quantity if applicable, threshold flag, primary excess and qualifying-event membership, with crop/phase/year/coordinate and rule metadata. |
| Source series CSV | Hourly source values for day/night aggregations; otherwise the source-resolution analysis series. |
| Annual metrics CSV | Expected/available samples, validity, event outcome, longest run and exposed-sample count. |
| Exposure intervals CSV | Half-open UTC start/end and duration of qualifying runs, or contributing runs for accumulated exposure. |
| Complete JSON | All above plus source hashes, exact rule, effective duration, calendar provenance, screening results, requested years and failures. |

These exports support later joint/conditional trigger and parametric-index analysis. Such models and payout equations are not yet implemented. Failed years remain explicit in JSON. Stop retains completed responses; a prominent modal locks controls during processing and the calculate button uses a high-contrast lime color.

## 6. Reproduction and checks

From repository root, with Python/openpyxl and Node dependencies installed:

```text
python scripts/build_pixel_calendars.py
python scripts/build_regional_calendars.py
node scripts/build_gee_rule_audit.mjs
node scripts/build_variable_equivalences.mjs
cd web-v2
node scripts/check-pixel-calendars.mjs
node scripts/check-regional-calendars.mjs
node scripts/check-hazard-events.mjs
npx tsc --noEmit
npm run build
```

The hazard harmonization/orange-exclusion audit is retained separately. GEE configuration presence alone is not access verification. Production probes and their actual outcomes are recorded separately in the v4 live-verification artifact; old v3 artifacts remain historical.

## 7. Decision history

| Version | Change | Reason |
|---|---|---|
| Initial harmonization | Unified labels with retained source rows and exclusion reconciliation | Papers use different stage language, codes and experimental windows. |
| Coordinate v3 | Consecutive cell-specific intervals and explicit combined windows | Remove misleading disconnected monthly aggregate fragments without inventing dates. |
| Regional v4, 2026-09-16 | Six intact-block assignments; latitude/longitude/planting selectors | User requests six physically coherent phases and crop-present regional navigation. |
| Regional v4 | 35 exact quantity definitions: 25 GEE and 10 external-series routes | Resolve ambiguity while preserving differences between observations, treatments and proxies. |
| Regional v4 | Duration-aware screening, time series, probability and exports | Prepare reproducible inputs for subsequent conditional probabilities and parametric triggers. |

Commits preserve the code and generated assets for each decision. Original Excel files are unchanged; correspondence overrides live in a separate versioned file so the human review is not silently rewritten.
