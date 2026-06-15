# Phase calculator GEE setup

The `/calculator` page uses a Vercel backend route:

```txt
POST /api/calculate-phase-risk
```

The browser never receives Google credentials. Earth Engine credentials live only in Vercel
environment variables.

## Required Vercel environment variables

```bash
GOOGLE_CLOUD_PROJECT=
GEE_SERVICE_ACCOUNT_EMAIL=
GEE_SERVICE_ACCOUNT_PRIVATE_KEY=
```

`GEE_SERVICE_ACCOUNT_PRIVATE_KEY` can use escaped newlines (`\n`). The backend converts them before
initializing Earth Engine.

If these variables are missing, `/calculator` shows `Backend GEE no configurado` and does not
simulate results.

## No-credit-card route

Use an Earth Engine noncommercial project:

1. Register or create a Google Cloud project through Earth Engine noncommercial registration.
2. Enable the Earth Engine API for that project.
3. Create a Service Account in that project.
4. Grant the Service Account Earth Engine access/roles required for API calls.
5. Create a JSON key, copy only:
   - project id
   - client email
   - private key
6. Put those values in Vercel environment variables.
7. Redeploy Vercel.

This does not require Cloud Run, Cloud Build, Artifact Registry, Secret Manager, or Google Cloud
billing for the app runtime.

## Frontend request

```json
{
  "lat": 4.75,
  "lon": -74.25,
  "crop": "maize",
  "phase": "F2",
  "variable": "tmax_c",
  "threshold": 35,
  "start_year": 1981,
  "end_year": 2016,
  "min_days_event": 3
}
```

## Query scope

The Vercel backend queries one request at a time:

- one 0.5 degree polygon: `lat +/- 0.25`, `lon +/- 0.25`
- one crop
- one phase
- one ERA5-Land variable
- one year range

It does not export to Drive, launch batch tasks, download all pixels, or store daily global series.
