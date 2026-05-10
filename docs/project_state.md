# Estado actual del proyecto de tesis

## Resumen

Este workspace limpio fue construido a partir de `C:\Users\paola\Tesis`, sin modificar la carpeta original. La carpeta histórica pesa aproximadamente 84,93 GiB, contiene 15.262 archivos y 577 carpetas. El objetivo del repo limpio es preservar lo importante para GitHub, Vercel y reproducibilidad científica sin copiar datasets pesados.

## Estructura limpia

- `docs/`: documentación técnica, decisiones, bitácora y estado del proyecto.
- `data_info/`: fichas metodológicas por dataset.
- `metadata/`: inventario de datos, calendarios y metadatos livianos.
- `scripts/`: scripts importantes reutilizables.
- `notebooks/importantes/`: notebooks que documentan el proceso científico usado.
- `notebooks/revisar/`: notebooks potencialmente útiles o no claros.
- `outputs/web/`: derivados livianos para visualización y Vercel.
- `manuscript/`: insumos de tesis/artículos y planificación académica.
- `web/`: futura aplicación React/Next.js.
- `archive/`: notas o material legado, sin copiar basura ni datasets pesados.

## Riesgos

- La carpeta original mezcla datos crudos, procesados, scripts, notebooks y resultados.
- Existen HDF5, NetCDF, TIFF, NPY y ZIP que no deben entrar a GitHub.
- Hay repositorios `.git` anidados en `Analisis Geoespacial` que no fueron copiados.
- Los notebooks pueden contener rutas absolutas locales.
- Algunos outputs livianos necesitan validación metodológica antes de publicarse.
- El pipeline final todavía debe modularizarse desde notebooks hacia scripts reproducibles.

## Scripts importantes copiados

- `scripts/correlacion_masiva.py`
- `scripts/thesis_paths.py`
- `scripts/export_geoglam_to_thesis.py`
- `scripts/inspect_geoglam_shapefile.py`
- `scripts/prepare_shapefile_excel_export.py`
- `scripts/build_geoglam_excel.mjs`

## Notebooks importantes copiados

- `notebooks/importantes/codigo para correlacionar todo ok.ipynb`
- `notebooks/importantes/Corr_todos.ipynb`
- `notebooks/importantes/CorrelacionesconSST.ipynb`
- `notebooks/importantes/SST.ipynb`
- `notebooks/importantes/TendRemove.ipynb`
- `notebooks/importantes/Tend_Remove_All Cereals.ipynb`
- `notebooks/importantes/ONI.ipynb`
- `notebooks/importantes/Calendario.ipynb`
- `notebooks/importantes/SOM ENSAYO 1.ipynb`
- `notebooks/importantes/Creación_Clústeres.ipynb`
- `notebooks/importantes/Puntos relevantes.ipynb`
- `notebooks/importantes/Visualizacion_prelim.ipynb`

## Notebooks para revisar

- `notebooks/revisar/Validación rendimientos.ipynb`
- `notebooks/revisar/Cereals.ipynb`
- `notebooks/revisar/RMM.ipynb`
- `notebooks/revisar/OLR.ipynb`
- `notebooks/revisar/grafica verifi corr.ipynb`
- `notebooks/revisar/Verificacion_corr_cluster_aleatorio.ipynb`
- `notebooks/revisar/nc_a_tif.ipynb`

## Decisiones tomadas

- Los notebooks `Untitled*` no se copiaron.
- Los checkpoints no se copiaron.
- Los notebooks de centinela no se copiaron.
- `Puntos relevantes.ipynb` es el único notebook de puntos incluido.
- TIFF, NetCDF, HDF5, NPY, NPZ y ZIP no se copiaron.
- `Analisis Geoespacial\Talleres de clase` no se copió.
- `Analisis Geoespacial\Proyecto_01 - copia` no se copió.

## Módulos científicos preliminares

- `preprocessing`: preparación de GDHY, SST, OLR y GEOGLAM.
- `detrending`: remoción de tendencia en SST/rendimientos.
- `climate_indices`: ENSO/ONI, MJO/RMM y otros índices.
- `correlations`: correlaciones SST-rendimiento.
- `som_analysis`: PCA/IPCA, SOM y clusters.
- `phenology`: calendarios agrícolas y ventanas fenológicas.
- `thresholds`: triggers y umbrales climáticos.
- `visualization`: mapas, figuras y productos científicos.
- `web_exports`: CSV/JSON/GeoJSON livianos para Vercel.

## Estado

El workspace es una versión curada inicial. Todavía no se debe inicializar Git hasta revisar notebooks, validar outputs web y confirmar que ningún archivo pesado fue copiado accidentalmente.
