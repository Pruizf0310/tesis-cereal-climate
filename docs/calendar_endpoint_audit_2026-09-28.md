# Calendar audit, 28 September 2026

## Verified

The twelve local GGCMI Phase 3 v1.01 NetCDF files match the MD5 checksums
published at https://zenodo.org/records/5062513. Every one of the 85,916
published crop/season/water-system calendars was compared with its exact
NetCDF latitude and longitude, without nearest-cell substitution.

- Planting endpoint mismatches: 0.
- Maturity endpoint mismatches: 0.
- Missing or invalid source endpoints among published cells: 0.
- All web cycle lengths are source growing-season length plus one day:
  the web includes both planting and maturity dates. This convention is
  intentional, not a shifted endpoint.

Representative exact maize rainfed cells demonstrate different annual timing:

| Cell | Planting | Maturity |
| --- | --- | --- |
| 39.75, -95.25 | 27 April, planting year | 25 September, planting year |
| -35.25, -60.75 | 23 October, planting year | 25 March, following year |

The old chart aligned every season to day zero of planting and normalized bar
width by local cycle length. Fixed stage fractions therefore produced nearly
identical bar layouts across locations. The replacement uses the same January
to December two-year calendar axis everywhere. Date calculations and the
underlying climate-event windows have not been changed.

## Not verified as observations

GGCMI explicitly supplies static multi-year mean estimates of planting and
maturity, with gap filling and spatial extrapolation. It does not supply annual
observations of the intermediate stages. The project rescales fixed technical
stage fractions within each local cycle. Those fractions have not been
calibrated for every location, cultivar, water system or year. A correct import
does not establish agronomic validity of all six internal phase boundaries.

The crop inventory does not independently demonstrate the presence of each
season or water system. For example, rice season 2 at 35.25, -92.75 has a
15 January planting date in the original source. This is a review flag, not
proof of a transcription error or a basis for automatically changing the date.
Season-specific cultivated-area evidence and regional calendars are needed
before asserting that this season is actually grown at this cell.

Maturity is not necessarily the actual harvest date. A hemisphere alone cannot
define crop timing; tropical regimes, multiple seasons and winter/spring crops
must remain distinct. Dates must not be shifted by six months just to create
a north/south contrast.

## Remaining scientific closure

Confirm season and water-system occurrence using suitable spatial inventories;
review flagged endpoints against regional crop calendars; and calibrate or
replace internal phase timing with regional observations or a validated
phenology model. Until then, the interface explicitly distinguishes reference
endpoints from estimated phases and does not label either as observed annual
phenology. New scientific timing decisions must version the calendar and
invalidate incompatible probability layers.

## Reproduce

`scripts/audit_calendar_endpoints.py --source <GGCMI-directory> --output <report.json>`
requires Python and h5py. It checks the official checksums and every published
endpoint. Run `node scripts/test-calendar-display.cjs` and
`node scripts/check-pixel-calendars.mjs` from web-v2 to check the chart positions,
phase partition, leap dates and year crossings independently of the source audit.
