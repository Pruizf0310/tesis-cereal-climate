# Phase calculator GEE setup

The `/calculator` page never downloads or stores global daily series. It resolves the crop pixel and
phenology window in the browser, then posts one coordinate/crop/phase/variable request to:

```txt
POST /api/phase-calculator
```

The Next.js API route is a thin proxy. In production, configure it with:

```bash
GEE_ENDPOINT_URL=https://REGION-PROJECT.cloudfunctions.net/phase-calculator
GEE_ENDPOINT_API_KEY=optional-shared-secret
```

If `GEE_ENDPOINT_URL` is missing, the UI shows a clear "GEE not configured" message and no synthetic
probability is shown.

## Expected request

```json
{
  "lat": 4.75,
  "lon": -74.25,
  "crop": "maize",
  "phase": "F2",
  "variable": "tmax_c",
  "threshold": 35,
  "event_rule": "at_least_3",
  "start_year": 1981,
  "end_year": 2016,
  "pixel": {
    "lat": 4.75,
    "lon_ee": -74.25,
    "pixel_lat_min": 4.5,
    "pixel_lat_max": 5.0,
    "pixel_lon_min_ee": -74.5,
    "pixel_lon_max_ee": -74.0
  },
  "phase_window": {
    "start_doy": 182,
    "end_doy": 273,
    "crosses_year": false
  }
}
```

## Expected response

Return either `{ "result": ... }` or the result object directly:

```json
{
  "result": {
    "probability": 0.3333,
    "event_years": 12,
    "valid_years": 36,
    "years_critical": [1983, 1992],
    "annual": [
      {
        "year": 1981,
        "n_days": 92,
        "n_exceedance_days": 4,
        "max_value": 36.1,
        "mean_value": 28.4,
        "p95_value": 34.7,
        "max_consecutive_exceedance_days": 2,
        "event_occurred": true,
        "daily_values": [
          { "date": "1981-07-01", "doy": 182, "value": 31.4, "exceeds": false }
        ]
      }
    ]
  }
}
```

## GEE implementation notes

Use `ECMWF/ERA5_LAND/DAILY_AGGR` and query only the request polygon:

```txt
[lon - 0.25, lat - 0.25, lon + 0.25, lat + 0.25]
```

Variable mapping:

- `tmean_c`: `temperature_2m - 273.15`
- `tmax_c`: `temperature_2m_max - 273.15`
- `tmin_c`: `temperature_2m_min - 273.15`
- `precip_mm`: `total_precipitation_sum * 1000`
- `swvl1`: `volumetric_soil_water_layer_1`
- `rootzone_sm`: `swvl1 * 0.07 + swvl2 * 0.21 + swvl3 * 0.72`
- `water_deficit_mm`: optional, for example precipitation minus potential evaporation in mm

For each year, build the phase date range from `start_doy` and `end_doy`. If `crosses_year` is true,
the end date belongs to the following year. Compute:

- `n_days`
- `n_exceedance_days`
- `max_value`
- `mean_value`
- `p95_value`
- `max_consecutive_exceedance_days`
- `event_occurred`

Rules:

- `at_least_1`: `n_exceedance_days >= 1`
- `at_least_3`: `n_exceedance_days >= 3`
- `at_least_5`: `n_exceedance_days >= 5`
- `max_consecutive`: return the maximum run of exceedance days and set `event_occurred` according to
  the backend policy. The current UI sends only the climate threshold, not a separate run-length
  threshold.
