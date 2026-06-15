# Phase calculator GEE setup

The `/calculator` page calls an external Cloud Run backend directly from the browser. It does not
store credentials in Vercel or in the frontend bundle.

```bash
NEXT_PUBLIC_GEE_API_URL=https://<cloud-run-url>/calculate-phase-risk
```

If this variable is missing, the UI shows `Backend GEE no configurado` and does not simulate results.

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

## Backend

The backend lives in `gee-backend/` and exposes:

```txt
POST /calculate-phase-risk
```

It authenticates Earth Engine with a Google Cloud Service Account using environment variables:

```bash
GOOGLE_CLOUD_PROJECT=
GEE_SERVICE_ACCOUNT_EMAIL=
GEE_SERVICE_ACCOUNT_PRIVATE_KEY=
ALLOWED_ORIGIN=https://tesis-cereal-climate-egcl.vercel.app
```

See `gee-backend/README.md` for Cloud Run deployment steps.
