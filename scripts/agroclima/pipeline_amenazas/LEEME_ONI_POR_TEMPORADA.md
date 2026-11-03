# ONI regional en conteos por temporada

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\ONI_REGIONAL_POR_TEMPORADA.ps1
```

Reutiliza exactamente `regiones_utilizadas.csv` de `ONI_regional_20261020_111438`, por lo que conserva las 18 regiones ya empleadas. Siguen siendo provisionales. No vuelve a asignar países, no modifica las regiones ni el análisis por 100 días anterior.

Calcula desde `conteo_original` de la matriz corregida, no convirtiendo el promedio regional de tasas mediante una duración media. Se recalcula dentro de cada píxel/fase/categoría y después se agregan las diferencias con igual peso por píxel. Mantiene los mismos sorteos (semilla 20261019; 2.000 réplicas), mínimo de cinco temporadas por grupo y soporte fijo por contraste.

Unidades:

- EST, VEG, REP, FLO y FIL: **episodios medios por temporada**, dentro de la fase indicada.
- MAT: **días medios con lluvia >10 mm por temporada**, dentro de su ventana.

Son promedios espaciales y regionales: los decimales son válidos. La duración de las ventanas cambia entre fases/lugares; un conteo mayor por temporada no equivale por sí solo a una tasa mayor. No sumar los episodios de fases contiguas como eventos únicos. Los contrastes son asociaciones históricas, no pérdidas causales.

Genera las mismas tablas de contrastes, IC, soporte, series y diagnósticos D3, pero con unidades por temporada, en una carpeta nueva `ONI_regional_conteos_temporada_FECHA_HORA` dentro de la tesis. No usa la Tabla B ni los cachés diarios de MJO, ni consulta GEE.

Archivo principal: `contrastes_regionales.csv`. Ejemplo: diferencia +0,3 en FLO significa 0,3 episodios medios adicionales por temporada en esa fase y grupo ONI frente a neutral, sobre el soporte común de píxeles.

Para cambiar la asignación indicar `-Regions 'C:\ruta\regiones.csv'`. Para repetir con otra carpeta indicar `-Output`. No usar resultados sin `completed.json`.

La preparación verificó la selección de unidades, consistencia de conteos reales con tasas y el remuestreo con datos sintéticos; no ejecutó el análisis integral.
