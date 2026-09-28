# Historical probability map: regional pilot

Prepared on 2026-09-28 through the deployed hazard-probability API at
https://tesis-cereal-climate-egcl.vercel.app, source commit
`2ef7c69e2658485fa97b17deab903919c5aca706`.

## Coverage and meaning

- Rice, first rainfed season (`rice_1__rf`).
- All seven inventory cells inside longitude 104.5 to 106, latitude 9.5 to 11.
- Planting years 1981 through 2016; phases REP, FLO and FIL.
- Rule `RICE_RAIN25`: spatially averaged daily precipitation >=25 mm/day,
  for at least one day wholly within the estimated phase window.
- Source: ERA5-Land DAILY_AGGR, `total_precipitation_sum`, metres to millimetres.
- Spatial support: 0.5-degree crop calendar cell, not a farm observation.
- 756 annual records: 746 evaluable, 10 unavailable, zero unresolved failed queries.
- The regional expansion took 367 seconds for 648 requests, followed by one
  successful retry of an isolated failure. The prior 108-record pilot was reused.
- Published annual layer: 5,125 bytes, excluding its small index. Raw climate
  time series were not downloaded locally. The local resumable checkpoint also
  retains response provenance and is ignored by Git.

The map estimates empirical historical event probability as event seasons divided
by evaluable seasons. Missing or invalid temporal samples exclude a season from
the denominator. An unavailable season is not a zero-event season. The calendar
uses estimated climatological dates repeated each planting year. Different cells
can have different calendar windows, so their frequency differences are not
attributable solely to climate differences. This is not a future forecast, crop
damage probability or an independently validated global damage threshold.

The threshold comes from a regional rainfall indicator in the reviewed rule
registry; applying it in this pilot demonstrates the computation, not local
agronomic validation. No ENSO/MJO conditioning or yield-loss relationship is used.

## Reproduction and extension

From `web-v2`, inspect the work estimate before starting:

```sh
node scripts/prepare-atlas.cjs --crop rice --season rice_1__rf --rule RICE_RAIN25 --bounds=104.5,9.5,106,11 --first 1981 --last 2016 --max-requests 1000
```

Add `--run --origin https://tesis-cereal-climate-egcl.vercel.app` to process.
The checkpoint reuses successful years and retries failures. It verifies the
source rule and calendar signature. Annual summaries support changing the
displayed year range without repeating climate queries. Publication requires
committing the new content-addressed layer and updated index.

This initial preparation still makes one API request per cell, phase and year,
with two workers. It is not a vectorized Earth Engine batch implementation.
Global expansion must not be mistaken for a completed dataset or launched
through thousands of interactive browser requests. Cloud-native aggregation
must preserve spatial-mean-before-threshold semantics, complete phase coverage,
calendar versioning, and each rule's run/rolling/accumulated operator, and be
checked against this reference implementation before replacing it.

## Website

`/probability` opens the saved rice layer and fits the calculated coverage. The
shared six-bin blue scale has fixed probability boundaries across phases.
Gray cells are uncalculated or insufficiently covered, never a low-probability
category. Cell selection shows annual outcomes and the denominator. `/risk`
remains the homepage with crop calendars, hazards and thresholds intact.
