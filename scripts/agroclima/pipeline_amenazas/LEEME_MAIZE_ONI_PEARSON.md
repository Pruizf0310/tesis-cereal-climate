# Maíz: ONI v6 y ocurrencias por fase — Pearson únicamente

Ejecutar desde `C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas`:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\maize_oni_pearson.py
```

No descarga datos ni produce mapas. Usa la selección vigente de 10.923 píxeles y las seis fases de 1981–2016. Cada correlación utiliza hasta 36 pares anuales, no el acumulado histórico. X: ONI v6 ponderado por días dentro de las fechas de esa fase y píxel. Y: conteo medio espacial de ocurrencias en esa misma ventana. Se calcula Pearson sin Spearman, permutaciones, p-valores, ajuste de tendencia ni búsqueda de rezagos. Los ceros válidos cuentan; las ventanas incompletas y ONI faltante se excluyen. Las series constantes no tienen correlación definida. El mínimo es 20 pares (`--min-years 36` permite exigir todos).

La ventana usa el ONI trimestral móvil centrado en cada mes: enero=DJF, febrero=JFM, etc. Si la fase cruza meses se pondera por días y si cruza años se utiliza el año siguiente. No se usa ONI anual ni se repite el conteo anual para crear observaciones mensuales artificiales.

Salidas en una carpeta nueva por ejecución dentro de `03_Resultados/Agroclima/vigente/correlaciones/maize_ONI_Pearson`:

- `pearson_by_pixel_phase.csv`: 65.538 filas; coordenadas, fase, regla realmente aplicada, Pearson, número de pares y estado. Incluye por signo de ONI el número de temporadas válidas, temporadas con ocurrencias, porcentaje de temporadas con ocurrencias y conteo medio. ONI positivo/negativo no equivale a clasificación oficial El Niño/La Niña.
- `annual_ONI_occurrence_pairs.csv.gz`: tabla anual auditable con fechas, calidad, regla, conteo, ONI e indicador de inclusión. Las filas incompletas se conservan para revisión pero no entran en Pearson.
- `coverage_summary.csv`: cobertura por fase.
- `oni_v6_monthly_centers.csv`: índice utilizado.
- `provenance.json`: parámetros, huellas SHA256 y tiempo medido.

Las salidas se copian también al repositorio local; no se suben automáticamente a GitHub. Se conservan las ejecuciones previas y ONI v5. Requiere `correlacion_oni_amenazas.py` en la misma carpeta para leer ONI y fechas; importar esas funciones no ejecuta su análisis anterior.

El mayor costo es leer y comprimir 2,36 millones de filas: esperar pocos minutos y usar la estimación actualizada en terminal. El cálculo de Pearson es vectorizado en CPU y usa matrices pequeñas; no requiere GPU ni H5 externos. La interrupción deja una carpeta parcial sin `provenance.json`; repetir crea una nueva ejecución.

Interpretación: r positivo = ONI mayor asociado a más ocurrencias; r negativo = a menos. No es una prueba de causalidad, significancia ni capacidad predictiva. Para inferencia hay que evaluar dependencia temporal, tendencias y comparaciones múltiples. Para seguros se necesita además el cruce con pérdidas y validación fuera de muestra. Se mantienen las aproximaciones de fases y discrepancias documentales del cálculo climático original; no se cambian umbrales.
