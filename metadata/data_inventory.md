# Inventario de datos

| Dataset / componente | Tamaño aproximado original | Fuente | Ruta original | Formato | Uso científico | Entra al repo |
|---|---:|---|---|---|---|---|
| SST cruda diaria | ~21 GiB | NOAA/OISST u origen equivalente pendiente de confirmar | `C:\Users\paola\Tesis\01_Data\SST` | NetCDF `.nc` | Campo climático principal para correlaciones SST-rendimiento | No |
| SST mensual detrended | ~1,02 GiB | Derivado local | `C:\Users\paola\Tesis\02_Procesados\SST_monthly_detrended_1981_2025_0p5deg35.nc` | NetCDF `.nc` | Insumo procesado para correlaciones | No |
| OLR diario | ~4,03 GiB | NOAA/CPC u origen equivalente pendiente de confirmar | `C:\Users\paola\Tesis\01_Data\OLR` | NetCDF `.nc` | Variabilidad tropical/convección | No |
| ENSO / ONI | liviano | NOAA CPC | `C:\Users\paola\Tesis\01_Data\ONI\ONI_v5.html` | HTML/tabla | Índice ENSO para integración con rendimiento y clusters | Parcial; solo derivados livianos |
| MJO / RMM | pendiente | Bureau of Meteorology u origen equivalente pendiente de confirmar | relacionado con `02_Scripts\RMM.ipynb` | tabla/índice | Índice MJO para análisis climático | No hasta validar |
| GEOGLAM crop calendars | >500 MiB fuente ZIP + shapefile grande | GEOGLAM CM4EW | `C:\Users\paola\Tesis\01_Data\GEOGLAM_CM4EW_Calendars_V1.3 (1).zip` | ZIP/Shapefile/CSV derivado | Fenología y calendarios agrícolas | Solo CSV derivados livianos |
| GDHY yield datasets | pendiente | GDHY | rutas usadas en notebooks/scripts | tablas/raster pendiente de confirmar | Rendimiento de maíz, arroz, trigo y soya | No datasets pesados; sí muestras/metadatos |
| Correlaciones SST-rendimiento | 23,55 GiB H5 + NetCDF adicionales | Derivado local | `C:\Users\paola\Tesis\CORRELA_TODOS\rice_correlacion_vectorizada.h5` | HDF5 `.h5` / NetCDF | Resultado científico central | No; solo agregados web |
| SOM/PCA | ~711 MiB NPY + CSV livianos | Derivado local | `C:\Users\paola\Tesis\CORRELA_TODOS\rice_som_k6` | NPY/CSV | Clusters y patrones espaciales | CSV livianos sí, NPY no |
| Triggers ONI/rendimiento | liviano | Derivado local | `C:\Users\paola\Tesis\CORRELA_TODOS\rice_trigger_analysis` | CSV | Umbrales/triggers climáticos preliminares | Sí, revisar antes de publicar |
