# Tesis Cereal Climate

Repositorio limpio para una tesis de maestría sobre la relación entre variabilidad climática global y rendimiento de cereales, con aplicaciones en seguridad alimentaria, seguros paramétricos agrícolas y comunicación científica interactiva.

## Objetivo científico

Analizar cómo fenómenos climáticos de gran escala como ENSO, MJO, IOD, NAO y variabilidad del Atlántico tropical afectan el rendimiento global de maíz, arroz, trigo y soya. El proyecto combina procesamiento climático, correlaciones SST-rendimiento, reducción de dimensionalidad, SOM, fenología agrícola, triggers climáticos y visualización web.

## Estructura

```text
tesis-cereal-climate/
├── docs/
├── data_info/
├── metadata/
├── scripts/
├── notebooks/
│   ├── importantes/
│   └── revisar/
├── outputs/
│   └── web/
├── manuscript/
├── web/
└── archive/
```

## Datasets principales

- GDHY yield datasets.
- SST monthly/daily y SST detrended.
- ENSO / ONI.
- MJO / RMM.
- OLR.
- GEOGLAM crop calendars.
- Correlaciones SST-rendimiento almacenadas originalmente en HDF5/NetCDF.

Los datasets pesados no se versionan en GitHub. Este repositorio conserva código, notebooks curados, documentación, metadatos y outputs livianos para web.

## Flujo metodológico general

1. Documentar fuentes de datos y rutas externas.
2. Preprocesar índices climáticos, SST, calendarios agrícolas y rendimientos.
3. Remover tendencias y construir matrices comparables por cultivo/periodo.
4. Calcular correlaciones SST-rendimiento.
5. Reducir dimensionalidad y clasificar patrones con SOM/PCA.
6. Integrar fenología y detectar triggers climáticos.
7. Exportar resultados livianos para visualización web.
8. Comunicar resultados mediante dashboard React/Next.js desplegable en Vercel.

## Reglas de reproducibilidad

- No versionar archivos mayores a 100 MB.
- No versionar HDF5, NetCDF, TIFF, NPY, NPZ ni ZIP.
- Registrar fuente, ruta original, periodo, formato y uso científico de cada dataset.
- Mantener notebooks importantes como trazabilidad del proceso, pero convertir el flujo final a scripts/pipeline.
- Usar `outputs/web/` solo para derivados livianos consumibles por frontend.
- Usar Zenodo u otro almacenamiento externo para datos/resultados pesados cuando el proyecto esté listo para publicación.

## Vercel y Zenodo

La carpeta `web/` queda reservada para una aplicación React/Next.js. Los datos consumidos por la web deben estar en `outputs/web/` en formatos livianos como CSV, JSON, GeoJSON simplificado o imágenes optimizadas. Los datos científicos completos deben quedar fuera de GitHub y citarse mediante manifiestos, DOI o enlaces a Zenodo cuando estén publicados.
