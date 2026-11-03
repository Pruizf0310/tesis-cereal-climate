---
title: Auditoría del cruce maíz de secano – rendimiento GDHY
fecha: 2026-10-23
estado: vigente
---

# Auditoría de los pasos previos de maíz de secano

**Fecha:** 23 oct 2026. **Alcance:** histórico de amenazas por fase, calendario GGCMI por píxel, cruce OLS con rendimiento GDHY (corrida `20261008_213708`) y el NetCDF detrendido que usan todos los cruces. Las probabilidades ONI y ONI–MJO no entran en la entrega del 27 oct; aquí no se re-auditaron.

Script reproducible: [`scripts/agroclima/auditoria_rendimiento/auditar_rendimiento_gdhy.py`](../scripts/agroclima/auditoria_rendimiento/auditar_rendimiento_gdhy.py). Salidas: [`outputs/agroclima_vigente/auditoria_rendimiento/maize/`](../outputs/agroclima_vigente/auditoria_rendimiento/maize/). Tarda unos 5 s.

```bash
C:/Users/paola/anaconda3/python.exe -X utf8 scripts/agroclima/auditoria_rendimiento/auditar_rendimiento_gdhy.py --crop maize
```

## Resumen en cinco puntos

1. **Los rendimientos de 22–31 t/ha vienen del GDHY crudo**, no de un error nuestro de unidades ni del detrend. La unidad oficial de GDHY es t/ha. Son estimaciones de modelo, no observaciones.
2. Esos valores son **físicamente inverosímiles para maíz grano** promediado en una celda de 0,5°. Entre 1981 y 2016, el máximo nacional de FAOSTAT fue 12,3 t/ha en Chile, 11,5 en España, 11,0 en EE. UU., 10,1 en Francia y 7,7 en Irán. Afectan a 661 de los 10.923 píxeles: 453 en EE. UU., 49 en España, 45 en Francia, 42 en Australia y 17 en Irán.
3. **Convención de año:** GDHY no la documenta. La evidencia indirecta apunta a año de cosecha. Se decidió el 23 oct usar **año de madurez** (fin de MAT) como alineación principal; same-label queda como sensibilidad.
4. **Detrend:** es una regresión lineal contra el año, ajustada con los 36 años en cada píxel. Se reproduce con diferencia ≤3×10⁻⁶. Para correlaciones esto es correcto. Para la validación por bloques del OLS hay fuga de información (el detrend vio los años excluidos).
5. **El OLS de seis fases del 8 oct no muestra capacidad predictiva:** el R² de validación por bloques tiene mediana −0,27, es decir, predice peor que la media. El R² dentro de muestra (mediana 0,12) no supera lo que da el azar con 6 predictores y unos 35 años (≈0,18).

## 1. Unidades y variable

| Archivo | Variable | Unidades en el archivo | Unidad real |
|---|---|---|---|
| `01_Data/CEREALS/gdhy_v1.2_v1.3_20190128/maize/yield_AAAA.nc4` | `var` (lat, lon), fill −9,99×10⁸ | ninguna | t/ha (documentación DIAS GDHY v1.2+v1.3) |
| `02_Procesados/GDHY_timeseries/maize_yield_1981_2016_RAW.nc` | `var` (time, lat, lon) | ninguna | t/ha; idéntico byte a byte en valores al crudo anual |
| `02_Procesados/GDHY_detrend/maize_yield_1981_2016_DETREND_clean.nc` | `var` (lat, lon, time) | ninguna | t/ha de anomalía (media 0 por píxel) |

- La carpeta `maize` de GDHY es la combinación de las temporadas *major* y *second*. En 2010 su media (2,42 t/ha) queda entre las dos (2,40 y 2,44), así que **no es una suma** de temporadas.
- Advertencia: el nombre `..._DETREND_clean.nc` es engañoso. El archivo **no pasó por el QAQC** del notebook `TendRemove.ipynb`; es el detrend directo del crudo (`Tend_Remove_All Cereals.ipynb`). Convendría renombrarlo, o al menos documentarlo así en el capítulo de Datos.
- Fuentes: DIAS, metadatos de GDHY v1.2+v1.3 (doi:10.20783/DIAS.564); Iizumi & Sakai (2020), *Scientific Data*, doi:10.1038/s41597-020-0433-7. El artículo usa el área cosechada **fija del año 2000** (Monfreda et al., 2008) para todos los años.

## 2. Valores inverosímiles (prioridad)

Percentiles del crudo en los 10.923 píxeles (todos los años): p50 = 2,72; p95 = 12,36; p99 = 15,85; p99,9 = 25,25; máximo = **31,28 t/ha**.

| Píxel (ejemplos) | Lugar | Media cruda 1981–2016 | Máximo | FAOSTAT nacional (2014) |
|---|---|---:|---:|---:|
| 190085 (42,25; 2,75) | Cataluña, España | 25,8 t/ha | 31,3 t/ha | 11,4 t/ha |
| 192225 (43,25; −7,25) | Galicia, España | 26,1 t/ha | 28,1 t/ha | 11,4 t/ha |
| 182978 (37,25; 49,25) | Guilán, Irán | 24,7 t/ha | 29,0 t/ha | 7,1 t/ha |
| **71854 (−40,25; −72,75)** | Los Lagos, Chile | ≈22 t/ha (8,6 → 27,9) | 27,9 t/ha | 10,1 t/ha |

**El píxel 71854 es el que el script del 8 oct grafica por defecto** (el primero de la lista). La figura `pixel_71854_annual_history` muestra una de las series menos creíbles de toda la base. Para el artículo conviene escoger un píxel representativo, por ejemplo del Corn Belt.

Hipótesis (no verificada): son celdas con muy poca área de maíz grano (en Galicia y el sur de Chile domina el maíz para ensilaje), donde la calibración satelital contra FAO se dispara.

Criterios usados (archivo `auditoria_por_pixel.csv`):

- **Inverosímil:** píxel-año >15 t/ha. Hay 6.037 píxel-año en 661 píxeles. El umbral supera el máximo nacional de FAOSTAT 1981–2016 de todos esos países (el más alto es Chile, con 12,3 t/ha). En EE. UU., 15 t/ha equivalen a unos 239 bu/acre como promedio de una celda de unos 50 km × 50 km de secano, muy por encima de los promedios de condado de secano habituales en ese periodo. Esta comparación con los condados no está verificada: conviene contrastarla con USDA-NASS por condado antes de citarla.
- **Dudoso (solo informativo):** píxel-año >3 × el rendimiento nacional FAOSTAT del mismo año. Hay 2.596 píxel-año. En países de rendimiento bajo, 3× puede ser real (riego local).
- Clases por píxel: OK 9.900; con años inverosímiles 533; dudoso 362; quedaría con <20 años si se enmascarara >15 t/ha: 128.

**Decisión (23 oct): no enmascarar.** El r de Pearson no depende de la escala de cada píxel, así que un nivel inflado pero constante no cambia la correlación. Un salto aislado sí puede cambiarla. Por eso el resultado de correlaciones trae la columna `clase_auditoria_rendimiento` para filtrar en una sensibilidad. **Recomendación:** antes de enviar el artículo, reportar al menos la cifra de pruebas significativas sin esos 661 píxeles. Si el resultado cambia, el revisor lo va a preguntar.

FAOSTAT: [`metadata/reference/faostat_owid_*_yield_t_ha.csv`](../metadata/reference/), descargado el 23 oct 2026 de Our World in Data (FAOSTAT QCL, elemento 5412, t/ha). Para EE. UU., OWID usa USDA-NASS.

## 3. Alineación del año agrícola

- El año de temporada del calendario es el **año de siembra** (GGCMI).
- **same-label:** temporada *t* ↔ rendimiento etiquetado *t*.
- **maturity-year:** temporada *t* ↔ rendimiento del año en que termina MAT. La fecha `end` del CSV es inclusiva: lo comprobé con los días-celda esperados, 11 días = 275/25.
- Las dos alineaciones difieren en **1.591 píxeles (14,6 %)**, siempre en las 36 temporadas: son ciclos que cruzan diciembre, sobre todo en el hemisferio sur.
- Evidencia sobre la convención de GDHY: el año 1981 falta en 76,2 % de los píxeles del sur y en 52,0 % del norte. Esto es coherente con un rendimiento etiquetado por **año de cosecha**: las cosechas del sur a inicios de 1981 crecieron en 1980, cuando no había datos satelitales. Es evidencia indirecta, no una confirmación.
- **Pendiente:** buscar en el PDF de Iizumi & Sakai (2020) o de Iizumi et al. (2014) la frase que define el año. Con eso, la decisión queda citada en el capítulo de Datos.

## 4. Detrend

- Método real: regresión lineal contra el año por píxel, con todos los años válidos de 1981–2016 (`linregress` en `TendRemove.ipynb`). Se reproduce con diferencia máxima de 3×10⁻⁶ t/ha, incluso en los 6.388 píxeles con algún año faltante. Los huecos se tratan por año real, sin desplazar índices.
- **Para correlaciones (la entrega del 27 oct):** correcto. No hay predicción fuera de muestra, así que no existe fuga.
- **Para la validación por bloques del OLS:** el detrend usó los años excluidos, así que el R² de validación es optimista. Aun así sale negativo. Si se retoma el OLS predictivo, el detrend debe ajustarse **dentro de cada bloque de entrenamiento**.
- Tendencia lineal en 36 años: en series como la de Chile (8,6 → 27,9 t/ha) la recta no captura la forma de la serie. Es otra razón para la sensibilidad sin los píxeles inverosímiles.

## 5. Corrida OLS del 8 oct (`outputs/agroclima_vigente/rendimiento/maize_seis_fases/20261008_213708`)

| | same-label | maturity-year |
|---|---:|---:|
| Píxeles OK / colinealidad / no separables / <20 años | 10.475 / 236 / 154 / 58 | 10.479 / 236 / 150 / 58 |
| R² dentro de muestra, mediana | 0,120 | 0,125 |
| R² validación por bloques, mediana | −0,274 | −0,268 |

Con *k* predictores y *n* ≈ 35, el R² esperado solo por azar es ≈ *k*/(*n*−1), es decir ≈0,18 con 6 fases. La mediana observada no lo supera. **Conclusión de etapa:** el OLS de seis fases simultáneas, píxel por píxel, no sirve como modelo predictivo. La entrega del 28 oct usa correlaciones marginales por fase con control de multiplicidad. Esa es la pregunta que sí se puede responder con 35 años: ¿hay más píxeles con asociación negativa calor–rendimiento de lo que daría el azar?

## 6. Calendario y amenazas

- Histórico de amenazas: el hash SHA-256 del CSV (`0ebff649…`) coincide con la corrida auditada el 8 oct; hay 2.359.368 filas, sin duplicados ni faltantes (el script de correlación lo vuelve a verificar).
- Calendario GGCMI por píxel: 10.923 píxeles × 6 fases en `calendario_seis_fases_secano.csv`. Los límites se cruzan con el CSV de amenazas.
- Sin cambios respecto a lo ya registrado: sigue pendiente la discrepancia FIL 32,7/32,9 °C y MAT sigue contando días de lluvia, no episodios.

## Riesgo operativo detectado (no es de esta tarea)

`outputs/agroclima_vigente/ejecuciones/maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv` pesa **357 MB** en el repo local y está versionado: el commit tiene un archivo de 1 KB y la copia local está modificada. Un `git commit -a` intentaría subirlo y GitHub lo rechaza por pasar de 100 MB. No lo toqué.
