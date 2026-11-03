# Cruce anual de la matriz integrada con rendimiento

El script `cruzar_matriz_rendimiento.py` lee la matriz integrada validada, la selección vigente de píxeles y el NetCDF GDHY de rendimiento ya detrendido. No consulta GEE ni descarga datos. No hace gráficos.

Para ejecutar otra vez, solo si no hay ya una ejecución activa:

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\CRUZAR_MATRIZ_RENDIMIENTO.ps1
```

Guarda una carpeta nueva en `C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\rendimiento\cruce_anual_ONI_MJO_FECHA_HORA`.

Produce una base SQLite y doce CSV.gz de pares anuales: seis fases por dos escenarios de año. Una fila es píxel × temporada × fase × escenario. Incluye amenazas, ONI de la ventana, proporción anual de días en cada estado MJO, cobertura de ese cruce, rendimiento detrendido y z por píxel. No replica los años como observaciones diarias.

El archivo de rendimiento no documenta su convención de año. Se conservan dos escenarios: `same-label` usa la etiqueta de temporada; `maturity-year` usa el año en que termina MAT, aproximación al año de cosecha. No elegir por el tamaño de la correlación. El archivo ya está detrendido: solo se centra y divide por su desviación estándar muestral para obtener z. Se conservan valores negativos y píxeles con 35 años. El mínimo de análisis es 30 pares.

Análisis:

- Pearson por píxel: porcentaje de días afectados (principal), conteo original (secundario) y ONI continuo (cruce directo separado). Son coeficientes puntuales, sin IC por píxel.
- Pearson regional: un punto por temporada, con bootstrap de 2000 temporadas compartidas, nunca de píxeles. Promedia exposición y z sobre los mismos pares válidos de cada temporada. El conjunto elegible se fija por región, fase, variable y escenario; una temporada requiere al menos 95 % de ese conjunto. La composición puede variar hasta 5 % y se registra el número exacto de píxeles por temporada. No representa un panel perfectamente balanceado.
- MJO: se incorpora su exposición anual a la matriz; todavía no se ajusta un modelo con los ocho estados ni se interpreta como aporte incremental sobre la amenaza.

Archivos principales: `cruce_rendimiento.sqlite`, `pares_FASE_ESCENARIO.csv.gz`, `pearson_por_pixel.csv`, `correlaciones_regionales.csv`, `series_regionales_anuales.csv`, `auditoria_correspondencia_anual.csv`, `bootstrap_temporadas.npz` y `completed.json`.

Los IC son exploratorios y no ajustan dependencia entre temporadas ni comparaciones múltiples. Las regiones siguen siendo provisionales. La estandarización usa la serie disponible completa, por lo que estos resultados no son una evaluación predictiva fuera de muestra. Solo `completed.json` con `prueba_parcial=false` acredita una ejecución completa.
