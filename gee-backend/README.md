# CerealRisk GEE backend

FastAPI service for `/calculator`. It queries one ERA5-Land pixel, one crop, one phase and one
variable per request. It does not export to Drive, launch batch tasks, or download global daily
series.

## Endpoints

- `GET /health`
- `POST /calculate-phase-risk`

Example request:

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

## Environment

Set these as Cloud Run environment variables or secrets. Do not commit a Service Account JSON file.

```bash
GOOGLE_CLOUD_PROJECT=
GEE_SERVICE_ACCOUNT_EMAIL=
GEE_SERVICE_ACCOUNT_PRIVATE_KEY=
ALLOWED_ORIGIN=https://tesis-cereal-climate-egcl.vercel.app
PHASE_CALENDAR_PATH=data/phase_calendar_windows.json
```

`GEE_SERVICE_ACCOUNT_PRIVATE_KEY` must preserve newlines. In Cloud Run, store it as a secret or use
escaped `\n` sequences; the service converts escaped newlines before initializing Earth Engine.

## Deploy to Cloud Run

1. Create or select a Google Cloud project.
2. Enable Earth Engine access for the project and register the Service Account for Earth Engine.
3. Create a Service Account and grant the minimum permissions required by Earth Engine and Cloud Run.
4. Store the private key securely as a Cloud Run secret or environment variable.
5. Build and deploy:

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/cerealrisk-gee-backend ./gee-backend
gcloud run deploy cerealrisk-gee-backend \
  --image gcr.io/PROJECT_ID/cerealrisk-gee-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=PROJECT_ID,GEE_SERVICE_ACCOUNT_EMAIL=SERVICE_ACCOUNT_EMAIL,ALLOWED_ORIGIN=https://tesis-cereal-climate-egcl.vercel.app \
  --set-secrets GEE_SERVICE_ACCOUNT_PRIVATE_KEY=GEE_SERVICE_ACCOUNT_PRIVATE_KEY:latest
```

6. Copy the Cloud Run URL and configure Vercel:

```bash
NEXT_PUBLIC_GEE_API_URL=https://CLOUD_RUN_URL/calculate-phase-risk
```

7. Redeploy Vercel and test `/calculator`.

## ERA5-Land variables

- `tmax_c`: `temperature_2m_max - 273.15`
- `tmean_c`: `temperature_2m - 273.15`
- `tmin_c`: `temperature_2m_min - 273.15`
- `precip_mm`: `total_precipitation_sum * 1000`
- `swvl1`: `volumetric_soil_water_layer_1`
- `swvl2`: `volumetric_soil_water_layer_2`
- `swvl3`: `volumetric_soil_water_layer_3`
- `rootzone_sm`: `swvl1 * 0.07 + swvl2 * 0.21 + swvl3 * 0.72`

## Notes

The backend uses `data/phase_calendar_windows.json`, generated from the public web phenology file.
If a crop or latitude band has no typical phase window, the API returns `422` rather than fabricating
results.
