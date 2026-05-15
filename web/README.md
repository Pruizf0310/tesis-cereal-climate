# CerealRisk Intelligence

Static climate-food-risk intelligence interface for the thesis project. The web experience is designed as a modern geospatial product, not as a traditional academic page.

## What this version does

- Loads lightweight crop-pixel CSV files from `web/`.
- Displays agricultural pixels for rice, maize, wheat and soybean on an interactive Leaflet map.
- Colors pixels by crop, SOM class, variability or trigger proximity.
- Shows a dynamic pixel intelligence panel when a point is selected.
- Visualizes SOM climate-correlation fingerprints from `cluster_means.csv`.
- Visualizes ONI critical-window values against yield anomalies from `oni_yield_pixel_year_merged.csv`.
- Displays a phenology-aware timeline from `geoglam_resumen_fases.csv`.
- Shows research-grade candidate trigger signals from `trigger_summary_preliminar.csv`.
- Frames GitHub, Vercel and Zenodo as the open-science architecture for the project.

## Data connected

Current lightweight files copied into `web/`:

- `rice_puntos_utiles_interseccion.csv`
- `maize_puntos_utiles_interseccion.csv`
- `wheat_puntos_utiles_interseccion.csv`
- `soybean_puntos_utiles_interseccion.csv`
- `oni_yield_pixel_year_merged.csv`
- `geoglam_fases.csv`
- `geoglam_resumen_fases.csv`
- `som_assignments.csv`
- `som_class_summary.csv`
- `cluster_means.csv`
- `trigger_summary_preliminar.csv`
- `maize_yield.gif`
- `rgb_cereals_1981_2016.gif`

No heavy scientific data is loaded by the web.

## Run locally

From the repository root:

```powershell
python -m http.server 8000
```

Open:

```text
http://localhost:8000/web/
```

## Deploy on Vercel

Recommended static deployment settings:

- Framework preset: `Other`
- Root directory: `web`
- Build command: leave empty
- Output directory: `.`

Because data files are inside `web/`, the deployed static app can load them with stable relative paths.

## Future data integrations

The code is ready to connect future lightweight exports from Google Earth Engine, SST correlation workflows, MJO/RMM processing or web-ready geospatial layers:

- `web/*.geojson` for crop zones, hotspots or SOM regions.
- Raster tiles or static map images for SST/correlation layers.
- JSON files for validated trigger profiles.
- Region-level summaries for climate finance, insurance and food-system risk narratives.

Keep HDF5, NetCDF, TIFF, NPY, NPZ and ZIP files outside the web and outside GitHub.

