> Historical version. The current regional selection, six-phase partition and 35 explicit variable definitions are documented in [Regional workflow v4](regional_workflow_v4.md). Earlier counts and shared-window decisions below are retained as decision history, not current behavior.

# Historical meteorological exposure frequency

## Scope and scientific status

The calculator evaluates the frequency of an operational meteorological condition. It does not estimate crop damage probability, validate an experimental threshold globally, or reconstruct annually observed crop development. Calendar timing is an estimate repeated across years; see [calendar provenance](pixel_calendar_method.md).

The [rule-by-rule audit](gee_rule_audit.md) covers all 35 distinct rules in the 47 active crop/phase assignments. Nine operational mappings are available and 26 remain unavailable with explicit reasons. These mappings are project interpretations of the existing human-reviewed workbook and its cited papers, not a new independent systematic literature review. The pending maize REP rule remains an unassigned placeholder.

The reviewed workbook's source rows, paper pages, phase assignments, thresholds, and evidence categories remain in `web-v2/public/data/gee_rule_audit.json` and `hazard_impact_harmonized_v3.json`. The former adds the exact server-owned measurement, units, operator, duration and decision. Experimental exposure frequencies must retain that qualification. In particular, maize grain-filling heat uses a six-day mean of daily maxima; wheat ripening rain is an experimental rainfall exposure, regardless of the inherited broad evidence-category label.

## Collections and measurement

* [ERA5-Land daily aggregates](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR): `temperature_2m` (daily mean), `temperature_2m_max`, `total_precipitation_sum`.
* [ERA5-Land hourly](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY): `temperature_2m`, `total_precipitation_hourly`. The latter is already an hourly increment, so it is not differenced again.
* [JRC monthly surface-water history](https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_MonthlyHistory) was assessed and is not used as daily submergence or water-depth evidence.

Hourly rainfall is labelled by the end of its accumulation period ([ECMWF accumulation conventions](https://confluence.ecmwf.int/pages/viewpage.action?pageId=197702790)). Query timestamps are therefore shifted forward one hour and returned samples are labelled by interval start: the image at 01:00 supplies the 00:00–01:00 exposure. Midnight at the phase end supplies its final hour. This prevents borrowing an hour from the previous phase or losing the last hour. Instantaneous hourly temperatures use their original timestamps; their reported duration is an operational count of consecutive hourly samples, not proof of continuous sub-hourly temperature exposure.

Temperature is converted from kelvin to Celsius; precipitation from metres to millimetres. Negative precipitation values are masked before spatial averaging. The catalogue documents accumulation/packing artefacts; this treatment cannot guarantee that every anomalous positive value has been removed. Spatial means are over the exact selected 0.5-degree calendar cell, at 11132 m reduction scale. Available unmasked reanalysis pixels contribute to that mean. This is not an observation at a farm or a probability for every native reanalysis pixel inside the cell. Dates and exposure units are UTC, not inferred local day/night periods. Daily minimum/maximum is never substituted for a nighttime/daytime experimental regime.

Soil water potential needs a retention relationship; relative soil moisture needs a defined denominator; waterlogging needs suitable daily hydrological observations; treatment anomalies need the relevant control. No substitute is silently inferred from rainfall or volumetric moisture.

## Calendar and events

The server resolves the same coordinate-specific sequence as the risk calendar using `lib/pixel-phenology.ts`. Exact grid centres are required. Combined phases form ONE interval, not duplicated overlapping intervals; each applicable trigger is evaluated separately in that enclosing interval. Internal phase-specific occurrence is unresolved. Rule IDs are deduplicated within a combined interval. Reference month/day boundaries are mapped to each planting year, including leap days and subsequent-year portions.

Queries cover one rule and one planting year. Each expected daily/hourly timestamp is reindexed. Missing or invalid values break continuity; duplicates or off-grid timestamps reject the result. Threshold inequalities are explicit. A run event is a maximal consecutive qualifying interval meeting the minimum exposure. Rolling-mean events use complete within-phase windows; overlapping qualifying windows are united before reporting duration, so duration is not inflated by counting overlapping windows. No exposure before or after the selected phase is borrowed to complete a trigger.

Only completely observed phases long enough to evaluate the rule enter the denominator. Missing-data years, failed queries and phases shorter than the required duration are unavailable. The frequency is `event years / valid years`; if no valid year exists, it is null, not zero. Event durations are in days or hours, with UTC starts and exclusive ends. These rules estimate occurrence inside the chosen phase window; they do not claim the full duration of events extending outside that window.

The UI reports valid years, event years, unavailable years, longest exposure, qualifying event intervals and progress. Downloads include raw timestamps, rules, request parameters, calendar source, collection/band, retrieval time and calendar uncertainty metadata. The original uncertainty is inherited descriptive metadata, not a newly estimated confidence interval. Stop produces partial results, explicitly labelled by completed requests.

## Access verification and reproducibility

Configured service-account variables alone do not prove data access. Successful live POST requests verify the requested collection/band, cell and dates only; they do not validate global completeness. See `gee_live_verification.json` when available for recorded deployment checks. Credentials are never included in outputs.

On 16 September 2026, all nine operational rules returned HTTP 200 and complete temporal coverage for the representative coordinates and planting year 2000 recorded in [the live verification](gee_live_verification.json), against commit `f98ce7d`. An additional [unmocked browser check](gee_live_ui_verification.json) evaluated three distinct triggers in one rice VEG+REP interval for planting years 2000 and 2001: all six GEE responses were complete. These checks distinguish successful data access from scientific calibration or exhaustive global validation.

Build the audit with `node scripts/build_gee_rule_audit.mjs`. From `web-v2`, run `node scripts/check-hazard-events.mjs`, `node scripts/check-pixel-calendars.mjs` and `npm run build`. The retired latitude-band `/api/calculate-phase-risk` POST returns HTTP 410; the new endpoint is `/api/hazard-probability`. Cached old clients must reload rather than silently receive incompatible results.
