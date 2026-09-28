# Territorial exposure atlas

The home page now explores the crop inventory spatially. `/explorer` retains the yield explorer, `/calculator` retains detailed analysis, and `/signals` redirects to `/`.

The interface is in English with consistent system typography and sentence case. A sequential blue scale runs from light (low frequency) to dark (high frequency), using the same boundaries across stages. Pending and insufficient-coverage states use a separate neutral legend. The selected climate variable, threshold, exposure condition and data source remain visible above the map.

## Interpretation

The atlas computes historical meteorological exposure frequencies, not crop loss probabilities. The selected audited rule retains its original threshold, duration, variable and phase applicability. Other phases are explicitly unassigned; a rule is never extended to another phase for display purposes.

Each cell's frequency is event years divided by evaluable years. Failed queries and non-evaluable years are excluded. Pending, partial and insufficient-coverage cells are gray. A fully queried cell is assigned a range only when it meets the user-selected minimum number of valid years (default 10). That minimum is a display filter, not statistical validation. Zero observed events is distinct from missing data. Range boundaries are fixed at zero, (0,20], (20,40], (40,60], (60,80], and (80,100] percent; these are descriptive frequency bins, not validated risk levels.

## Calculation and persistence

The atlas first loads `public/data/atlas/index.json` and the matching compact annual layer. Rule, calendar version and calendar input signatures must match. Each cell-phase stores one character per planting year: `1` (event), `0` (no event), `u` (not evaluable), `f` (failed query), or `.` (pending). Changing years filters these saved annual states locally without requesting climate time series. Published results and browser results are merged; failed records never overwrite successful records. Browser cache keys no longer include the selected year range, so overlapping periods reuse the same annual results. Existing v1 caches for the selected period are migrated.

Interactive fallback is limited to 200 uncached annual requests. The visible map extent or entire crop inventory determines the cells queried, independently of exposure outcomes. All applicable phases for the selected rule are calculated. Two requests run concurrently against the existing `/api/hazard-probability` endpoint. The atlas requests `summary_only`, omitting raw samples from the response; detailed-analysis clients retain their full responses. Three consecutive service failures stop the run. Cancellation retains completed responses; rerunning skips saved successful years and retries failed requests. The counter separates valid, not-evaluable and failed records, identifies the current cell/phase/year, and shows elapsed time and an empirical remaining-time estimate after at least four completed requests. This estimate is not a service guarantee.

No global frequency layer is bundled yet: the index is explicitly empty. First-time visitors see the actual inventory and a missing-layer status. Large interactive runs are blocked instead of offering a multi-day browser calculation. This change provides the preparation and serving path, not an already computed climatology.

## Preparing shared layers

From `web-v2`, inspect a plan without starting climate requests:

```sh
node scripts/prepare-atlas.cjs --crop maize --season maize__rf --rule MAIZE_EMERGENCE_COLD6
```

Add `--run --origin https://cerealrisk.app` to prepare up to 200 missing records (the default budget), or explicitly set `--max-requests N`. Use `--bounds=west,south,east,north`, `--first`, and `--last` to scope preparation. The source application must have Earth Engine configured and must use the same rule/calendar registry. The command refuses mismatched source responses. There are at most two concurrent requests, with per-request timeouts. Repeating the command resumes from an append-only provenance checkpoint in ignored `.atlas-cache/`. Different year ranges reuse the same checkpoint. Keep one writer per output index; parallel CLI processes are not supported.

The command writes content-addressed annual layer files and an atomic index update under `public/data/atlas/`. Partial layers retain pending and failed states; they are never represented as zero-event years. Publishing these generated files makes them reusable across visitors. Checkpoint source provenance stays outside the public bundle. No background job is automatically launched by a visitor.

The first preparation still uses the existing audited cell/year endpoint. It does **not** claim to vectorize Earth Engine extraction or reduce the underlying reanalysis work. It moves that work out of the browser and prevents it being repeated across visitors and overlapping year ranges. Large-scale extraction remains a separate optimization: use resumable batch exports and shared climate-series storage rather than increasing interactive concurrency. Preserve spatial averaging before event classification, hourly versus daily resolution, local solar-clock profiles, missing-data rules and calendar boundaries. See [Earth Engine processing environments](https://developers.google.com/earth-engine/guides/processing_environments).

The local checkout has no configured Earth Engine credentials, so live climatological results were not verified locally. The existing deployed service configuration has not been changed. No synthetic probabilities ship with this UI.

## Verification

- `node node_modules/typescript/bin/tsc --noEmit`
- `node scripts/test-atlas.cjs`: missing versus zero, denominator, partial coverage, range boundaries and antimeridian selection.
- `node scripts/test-atlas-precomputed.cjs`: annual encoding, period reuse, rule/calendar compatibility, failed-record repair and ETA.
- `node scripts/test-prepare-atlas.cjs`: controlled local source, compact output, provenance checkpoint, restart without repeated data requests.
- Browser checks: actual inventory on desktop and mobile, no horizontal overflow, phase comparison, Signals redirect, and no client exceptions.
- Controlled browser fixtures: area batch, non-evaluable year exclusion, cache persistence, repeat-run avoidance, range filtering and a published layer that colors the map and filters years without climate queries. Fixtures are confined to test browser routing.
