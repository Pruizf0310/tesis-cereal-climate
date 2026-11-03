# Maíz: Pearson diario con RMM1 y RMM2

```powershell
cd "C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas"
.\.venv\Scripts\python.exe -X utf8 .\maize_mjo_diario.py --download-rmm --limit 10 --workers 4
```

No se ejecutó GEE durante la preparación. El comando utiliza RMM oficial ya guardado, descarga solo si falta, y reutiliza la caché de fechas compatible. Si faltan lotes, los extrae en GEE con las mismas fases y reglas del cálculo original. Para todos los píxeles, después del piloto, cambiar `--limit 10` por `--limit 0`. Para exigir cálculo exclusivamente local con fechas ya extraídas, añadir `--cache-only`: no inicializa GEE y se detiene si falta algún lote.

Cada observación es un **día UTC dentro de una fase**: X=RMM1 o RMM2 de esa fecha; Y=conteo medio espacial de ocurrencias confirmadas esa fecha. No se promedia MJO ni se agrupan días en semanas. Se incluyen ceros válidos y los últimos días de cada fase. Una racha de calor aporta una confirmación en su día N (N=duración mínima), no una ocurrencia por cada día caliente; cada día de precipitación que cumple el umbral sí cuenta individualmente. El inicio y final observados se conservan en otra tabla, con banderas de límites de fase.

Se calcula Pearson contemporáneo (rezago cero) por píxel y fase, por separado con RMM1 y RMM2, a través de todos los días válidos de 1981–2016. Cada componente excluye sus propios valores faltantes. El número de días aparece en `n_days`; no son observaciones estadísticamente independientes. Mínimo configurable de 20 días (`--min-days`), sin prueba de significancia, ajuste estacional, detrend ni pronóstico. Las series constantes quedan sin coeficiente. Un r positivo de RMM1 no equivale a «MJO más intensa»: las componentes firmadas se interpretan conjuntamente con fase/amplitud.

Las fechas deben reconstruir los conteos anuales originales; el script exporta la comprobación y se detiene ante discrepancias antes de publicar correlaciones y mapas. Se conserva el recorte original de las rachas en los límites de fase: no se reconstruye el fenómeno fuera de esas fechas. Se excluyen para Pearson las fases sin cobertura nativa completa.

Salidas nuevas en `03_Resultados/Agroclima/vigente/correlaciones/maize_MJO_diario`:

- `pearson_daily_by_pixel_phase.csv`: coeficiente, número de días y estado.
- `daily_occurrences_with_MJO.csv.gz`: días, calidad, conteo y MJO de cada fecha, incluidos ceros.
- `native_events_with_dates_MJO.csv.gz`: eventos por celda, fechas de inicio/confirmación/final y MJO en inicio y confirmación.
- `verification_against_original_annual_counts.csv`: verificación de sumas diarias.
- Dos figuras PNG/PDF en inglés, una por componente, seis fases por figura. Las etiquetas indican **daily** y **same-day**. No muestran ONI ni implican significancia.
- `provenance.json`: método, entradas, caché y límites.

La caché conserva estados nativos diarios de umbral/validez en `02_Procesados/Clima_ERA5_Land_cache/MJO_fechas`. Los resultados se copian al repositorio local. Se mantienen los scripts y resultados semanales anteriores. No ejecutar dos procesos sobre la misma caché simultáneamente.

ONI y MJO siguen separados: ONI usa valores de trimestres móviles centrados mensualmente y pares por temporada/fase; este análisis usa índices MJO diarios y pares diarios. No comparar el tamaño de sus coeficientes como si provinieran de idéntica agregación. OLR no se analiza aquí. Para anticipación se necesitan rezagos definidos de antemano y validación fuera de muestra.
