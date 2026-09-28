# Territorial exposure atlas

The home page now explores the crop inventory spatially. `/explorer` retains the yield explorer, `/calculator` retains detailed analysis, and `/signals` redirects to `/`.

The interface is in English with consistent system typography and sentence case. A sequential blue scale runs from light (low frequency) to dark (high frequency), using the same boundaries across stages. Pending and insufficient-coverage states use a separate neutral legend. The selected climate variable, threshold, exposure condition and data source remain visible above the map.

## Interpretation

The atlas computes historical meteorological exposure frequencies, not crop loss probabilities. The selected audited rule retains its original threshold, duration, variable and phase applicability. Other phases are explicitly unassigned; a rule is never extended to another phase for display purposes.

Each cell's frequency is event years divided by evaluable years. Failed queries and non-evaluable years are excluded. Pending, partial and insufficient-coverage cells are gray. A fully queried cell is assigned a range only when it meets the user-selected minimum number of valid years (default 10). That minimum is a display filter, not statistical validation. Zero observed events is distinct from missing data. Range boundaries are fixed at zero, (0,20], (20,40], (40,60], (60,80], and (80,100] percent; these are descriptive frequency bins, not validated risk levels.

## Calculation and persistence

The visible map extent or entire crop inventory determines the cells queried, independently of exposure outcomes. All applicable phases for the selected rule are calculated. Two requests run concurrently against the existing `/api/hazard-probability` endpoint. Three consecutive service failures stop the run. Cancellation retains completed responses; rerunning skips cached successful years and retries failed requests. Cache keys include the complete rule, calendar version, crop, season and year range. Summary data remain in browser local storage and can be exported as JSON with the rule and calendar version. Storage failures are surfaced.

No global frequency raster is bundled. First-time visitors see the actual inventory and pending status until their selected area is computed. Global, multi-decadal calculations require many requests and are not an instant global product. A production-wide precomputed dataset or durable background computation service is still required for immediate colored maps for every visitor. This change does not claim to provide that dataset.

The local checkout has no configured Earth Engine credentials, so live climatological results were not verified locally. The existing deployed service configuration has not been changed. No synthetic probabilities ship with this UI.

## Verification

- `node node_modules/typescript/bin/tsc --noEmit`
- `node scripts/test-atlas.cjs`: missing versus zero, denominator, partial coverage, range boundaries and antimeridian selection.
- Browser checks: actual inventory on desktop and mobile, no horizontal overflow, phase comparison, Signals redirect, and no client exceptions.
- Controlled browser fixtures: area batch, non-evaluable year exclusion, cache persistence, repeat-run avoidance and range filtering. Fixtures are confined to test browser routing.
