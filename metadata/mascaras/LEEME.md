# Máscaras de píxeles por cultivo

Qué píxeles de la grilla GDHY (0,5°) entran al análisis. Son las mismas selecciones que usaron las correlaciones originales (archivos HDF5 de `D:\`); se exportaron a CSV para no depender de ese disco.

| Archivo | Cultivo | Píxeles | Criterio que coincide |
|---|---|---:|---|
| `pixeles_maize.csv` | Maíz | 10.923 | Al menos 35 años válidos de GDHY en 1981–2016 |
| `pixeles_soybean.csv` | Soya | 4.955 | Al menos 35 años válidos |
| `pixeles_rice.csv` | Arroz | 3.186 | Los 36 años válidos |
| `pixeles_wheat.csv` | Trigo | 10.505 | Sin criterio único (33–36 años) |

El criterio de la tabla es la coincidencia comprobada, no la regla documentada con que se construyó cada HDF5. En trigo la selección sigue sin explicación (docs/RELATO_ACUERDOS_TESIS.md, sección 4).

## Columnas

- `pixel_id` = `lat_idx × 720 + lon_idx`. Es el identificador que usan todos los resultados.
- `h5_index`: orden original de la fila en el HDF5.
- `lat_idx`, `lon_idx`: índices en la grilla de GDHY (360 × 720).
- `latitude`, `longitude`: centro de la celda; longitud en [−180, 180).

## Integridad

`manifest.json` guarda el número de píxeles y el SHA-256 de cada CSV. `scripts/agroclima/pipeline_amenazas/maize_gee.py` (`read_pixels`) lo verifica antes de usar la lista. Las rutas del manifiesto apuntan a la ubicación original de los archivos; no hacen falta para leer los CSV.

## Límites

- Que haya rendimiento GDHY no demuestra que haya cultivo todos los años ni dice qué fracción de la celda está sembrada.
- El píxel de Nebraska (191325) pertenece a la máscara de maíz.
- Para tener la máscara como ráster, los índices permiten reconstruirla sobre la grilla de GDHY (lat de −89,75 a 89,75; lon de 0,25 a 359,75, en pasos de 0,5°). Ejemplo: Nebraska tiene lat_idx 265 y lon_idx 525, es decir, 42,75° N y 262,75° E (= −97,25°).
