# Qué hace falta para reproducir los resultados

Estado al 3 nov 2026. Para quien clone el repositorio y quiera revisar o repetir los cálculos.

## Está en el repositorio

| Pieza | Dónde |
|---|---|
| Máscaras de píxeles (qué celdas entran, por cultivo) | `metadata/mascaras/` |
| Calendario de seis fases, maíz de secano | `outputs/agroclima_vigente/calendario/calendario_seis_fases_secano.csv` |
| Reglas de amenaza v1 (24) y tabla v2 de maíz | `outputs/agroclima_vigente/amenazas/` |
| ONI y RONI v6 (CPC), 1981–2016 | `metadata/reference/cpc_oni_roni_v6_1981_2016.csv` |
| Fuentes revisadas de fases y umbrales | `metadata/reviewed_sources/` |
| Código: amenazas (Earth Engine), cruces, correlaciones, píxel típico | `scripts/agroclima/pipeline_amenazas/` |
| Resultados del píxel de Nebraska (tendencia, SST, correlaciones) | `outputs/agroclima_vigente/pixel_tipico/` |
| Presentación de avance y su código | `presentacion/Avance_tesis.pptx`, `scripts/presentacion/` |
| Decisiones y auditorías | `docs/` (empezar por `RELATO_ACUERDOS_TESIS.md`) |

## No está, y cómo conseguirlo

| Pieza | Por qué no está | Cómo obtenerla |
|---|---|---|
| Rendimiento GDHY (NetCDF) | Archivos grandes; `.nc` está excluido | Iizumi y Sakai (2020), *Scientific Data* 7:97, https://doi.org/10.1038/s41597-020-0433-7. Datos: https://doi.org/10.1594/PANGAEA.909132 |
| Clima diario ERA5-Land | Se calcula en Google Earth Engine | Cuenta de Earth Engine con un proyecto de Cloud propio; colección `ECMWF/ERA5_LAND/DAILY_AGGR` |
| ONI completo 1950– (tabla CPC v6) | Dato externo; `pixel_tipico_correlaciones.py` lo lee de `01_Data/ONI/ONI.txt` | Tabla ONI de CPC/NOAA; el repositorio solo trae 1981–2016 |
| MJO (RMM, BoM) | Dato externo | https://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt (`check_rmm_source.py` verifica la descarga) |
| SST OISST v2.1 | Grande | NOAA PSL |
| Base de cruce `cruce_rendimiento_v2.sqlite` (1,7 GB) | Excede GitHub | Se regenera con la cadena de `pipeline_amenazas` (corridas en Earth Engine → `matriz_integrada.sqlite` → `cruzar_matriz_rendimiento.py` → `integrar_variables_v2_sqlite.py`), o se comparte aparte |
| HDF5 de correlaciones (`D:\*_correlacion_vectorizada.h5`, hasta 86 GB) | Excede GitHub | Ya no hace falta para la máscara; queda como histórico |
| Salidas pesadas: `outputs/agroclima_vigente/probabilidades/`, CSV > 5 MB y la versión local de `resumen_GDHY_anual.csv` (358 MB; en GitHub sigue la anterior) | Tamaño | Se regeneran con los scripts; pedirlas si se necesitan |

## Lo que todavía impide correrlo tal cual

1. **Rutas absolutas.** La mayoría de los scripts y configuraciones usan `C:/Users/paola/Tesis/...`. Para correrlos en otra máquina hay que cambiar esas rutas, idealmente a una configuración con rutas relativas al repositorio. Esa tarea está pendiente.
2. **Proyecto de Earth Engine.** `config_maize_seis_fases_gee.json` trae un proyecto de Cloud concreto; cada persona debe usar el suyo.
3. **Entorno de Python.** El `.venv` no se sube; se recrea con `scripts/agroclima/pipeline_amenazas/requirements-lock.txt` (versiones exactas) o `requirements.txt`.

## Orden mínimo para un píxel (Nebraska, 191325)

1. `pixel_tipico_tendencia.py`: rendimiento, su tendencia y las series por fase → `tendencia.xlsx`.
2. `pixel_tipico_correlaciones.py`: amenaza → rendimiento, índices → amenaza, tipos de año ENSO → `correlaciones.xlsx`.
3. `scripts/presentacion/slides_*.py`: diapositivas con esos resultados.

Los pasos 1 y 2 leen la base SQLite de cruce; sin ella, se pueden revisar los resultados guardados en `outputs/agroclima_vigente/pixel_tipico/`, que son los que muestra `presentacion/Avance_tesis.pptx`.
