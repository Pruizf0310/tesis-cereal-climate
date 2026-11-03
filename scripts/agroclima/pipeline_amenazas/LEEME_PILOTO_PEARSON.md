# Piloto de teleconexiones: Pearson sencillo

Este experimento nuevo conserva los análisis anteriores. No consulta GEE ni requiere el disco de los H5. Utiliza los primeros diez píxeles del listado vigente de maíz que ya tienen temperatura diaria completa en caché. Están en el sur de Sudamérica y no representan la distribución mundial del maíz. La selección depende de disponibilidad previa, no del valor de correlación.

Ejecutar desde `C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas`:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\piloto_pearson.py
```

## Tres productos

1. **Doce mapas mensuales Pearson.** Cada punto compara el ONI v6 centrado en ese mes con el conteo de episodios de calor de ese mes, a través de 1981–2016. Regla exploratoria común: Tmax ≥34 °C durante ≥2 días consecutivos, durante todo el año. Se cuenta un episodio en el segundo día caliente; una racha que cruza un mes no se duplica. Se detecta primero por celda nativa ERA5-Land y después se promedia con pesos cos(latitud). Esta regla mensual homogénea permite comparar meses; no sustituye los umbrales específicos de las fases ni evalúa todavía lluvia/viento. Un mes con datos incompletos se excluye, no se vuelve cero.
2. **Seis mapas fenológicos Pearson.** Los mismos diez píxeles y los resultados existentes por fase: ONI ponderado por días de la ventana frente al conteo medio de amenazas de esa ventana. EST/VEG/REP/FLO/FIL son episodios de calor con sus reglas actuales; MAT son días con lluvia >10 mm. Se conservan las aproximaciones del calendario, el recorte FLO/REP y la discrepancia FIL 32,7/32,9 °C: el piloto no las resuelve. Los mapas mundiales Pearson ya calculados siguen disponibles en `correlaciones/maize_ONI_v6`, sin volver a procesarlos.
3. **Exploración diaria en tres píxeles preseleccionados** (posiciones 0, 4 y 9 del listado, no los de mayor correlación). Serie: fracción espacial diaria de celdas con Tmax ≥34 °C. No es un conteo de episodios ni un indicador de pérdida. Se resta climatología por mes/día y tendencia lineal. Welch con ventanas Hann de 512 días y 50% de solapamiento; se descarta todo segmento con faltantes, sin unir artificialmente tramos ni interpolar. Se guarda densidad espectral y coherencia con las dos componentes del **ROMI local**, identificado por su archivo `romi.cpcolr.1x-RMM.txt`; no se presenta como RMM. Se usa la intersección diaria disponible, normalmente 1991–2016. La banda 30–96 días se marca como referencia exploratoria; un pico o coherencia en esa banda no prueba influencia MJO. La tabla adicional guarda Pearson de las anomalías diarias con ROMI a 0, 7, 14, 21 y 28 días de antecedencia, todos predefinidos, sin seleccionar el máximo.

## Lectura y límites

Rojo significa asociación positiva; azul negativa; gris Pearson no definido o insuficientes pares. Un conteo constante no tiene r=0: su correlación no existe. Solo se calcula Pearson, sin Spearman, permutaciones ni p-valores. No se interpreta significancia con días independientes porque las series tienen autocorrelación. Los mapas son puntos regionales, no una superficie interpolada.

Las salidas quedan en `C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\diagnosticos\piloto_pearson`: CSV de coeficientes/n, series diarias agregadas, espectros/coherencia, tres figuras y procedencia con cobertura y tiempo medido.

Este piloto puede comprobar el funcionamiento y explorar diferencias entre meses/fases. Antes de extender el espectro se requiere una muestra de regiones agrícolas diversas seleccionada independientemente del resultado, estabilidad en períodos separados, sensibilidad al umbral, control de autocorrelación y evaluación de incertidumbre espectral.

Para seguros, una correlación contemporánea no basta. Hay que vincular exposición con pérdidas de rendimiento, medir probabilidades de pérdida con y sin evento, evaluar el riesgo de base y validar fuera de muestra. Para anticipación, usar únicamente índices que estaban publicados al emitir la señal: ONI centrado incluye meses vecinos y el procesamiento de índices/climatología de período completo no constituye una simulación operativa. Los rezagos del piloto tampoco demuestran capacidad predictiva.

Fuentes metodológicas: [ONI NOAA](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/), [ROMI/RMM NOAA PSL](https://www.psl.noaa.gov/mjo/current/), [Kiladis et al. 2014](https://www.psl.noaa.gov/mjo/mjoindex/pdf/kiladis14.pdf).
