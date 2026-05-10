# GEOGLAM

- Descripción: calendarios agrícolas CM4EW usados para identificar ventanas fenológicas críticas por cultivo y región.
- Fuente oficial: GEOGLAM Crop Monitor for Early Warning / CM4EW.
- Resolución espacial/temporal: geometrías agrícolas y fases fenológicas; resolución exacta pendiente de documentación final.
- Periodo: depende del calendario GEOGLAM V1.3.
- Formato: ZIP/Shapefile fuente; CSV/XLSX derivados.
- Ruta original: `C:\Users\paola\Tesis\01_Data\GEOGLAM_CM4EW_Calendars_V1.3 (1).zip` y derivados en `C:\Users\paola\Tesis\02_Procesados\Fenologia\geoglam_cm4ew_calendars`.
- Scripts relacionados: `notebooks/importantes/Calendario.ipynb`, `scripts/export_geoglam_to_thesis.py`, `scripts/inspect_geoglam_shapefile.py`, `scripts/prepare_shapefile_excel_export.py`, `scripts/build_geoglam_excel.mjs`.
- Outputs derivados: `geoglam_data.csv`, `geoglam_fases.csv`, `geoglam_resumen_fases.csv`, `Calendario_Fenologico_Cereales.xlsx`.
- Notas metodológicas: no versionar ZIP ni shapefiles grandes. Conservar CSV/XLSX livianos y documentar fuente.
