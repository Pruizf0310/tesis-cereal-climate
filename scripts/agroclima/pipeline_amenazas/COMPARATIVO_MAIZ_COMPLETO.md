# Verificación del cálculo completo de maíz — 8 de octubre de 2026

Comparación contra `amenazas/tabla_maestra_revision_humana.xlsx`, hoja maestra, filas 8–13, y todas las filas del resultado anual final.

98.307/98.307 lotes completados. 10.923 píxeles × 36 años × seis fases = 2.359.368 filas. Sin combinaciones píxel–año–fase ausentes o duplicadas. En cada fase: 393.228 filas, 391.140 con cobertura completa y 2.088 con cobertura incompleta. Las incompletas no equivalen a cero eventos y se excluyen del resumen histórico completo.

| Fase | Amenaza en Excel | Regla en Excel | Variable ERA5-Land utilizada | Regla calculada | Ventana del calendario aplicada | Correspondencia |
|---|---|---|---|---|---|---|
| EST | Calor | Tmax ≥34 °C, ≥2 días | temperature_2m_max | Idéntica; rachas ≥2 días | VE: siembra–emergencia | Coinciden variable y regla; calendario estimado |
| VEG | Calor | Tmax ≥34,6 °C, ≥2 días, V6–VT | temperature_2m_max | Idéntico umbral y duración | V7_VT | Aproximación: no resuelve exactamente V6–VT |
| REP | Calor | Tmax ≥33,7 °C, ≥2 días en ventana R1–R3, cuajado | temperature_2m_max | Idéntico umbral y duración; rachas recortadas | R2 | Ventana más estrecha que la fuente; no asegura episodio único entre fases |
| FLO | Calor | Tmax ≥33,7 °C, ≥2 días en ventana R1–R3 | temperature_2m_max | Idéntico umbral y duración; rachas recortadas | R1 | Ventana más estrecha que la fuente; no asegura episodio único entre fases |
| FIL | Calor | Tmax ≥32,7 °C, ≥2 días, R3–R6 | temperature_2m_max | Idéntico umbral de la tabla y duración | R3+R4_R5, hasta el inicio del bloque R6 | Coincide con Excel; discrepancia documental 32,9 °C pendiente |
| MAT | Lluvia durante secado en campo | P diaria >10 mm; contar días | total_precipitation_sum | >10 mm, días individuales | Bloque terminal R6 | Proxy del secado pos-R6; sin fecha observada de cosecha |

## Qué se obtuvo

GEE consultó ERA5-Land DAILY_AGGR y calculó sobre las celdas nativas, antes de resumirlas dentro de cada píxel GDHY. Tmax se convirtió de kelvin a Celsius y precipitación de metros a milímetros. Día UTC. Se descargaron resúmenes anuales de las seis fases, cobertura y frecuencias, no las series diarias completas ni las fechas individuales de los episodios. Las series de temperatura media y mínima del piloto no fueron variables de estas seis reglas del cálculo completo.

## Límites que permanecen

La auditoría confirma que la variable, operador, umbral y duración guardados en todas las filas coinciden con el Excel y el plan. No demuestra que todas las ventanas sean equivalencias exactas con los papers. Rachas que atraviesan R1/R2 se recortan: pueden perder la duración mínima en cada fragmento o producir un conteo en cada fase; no hay identificadores de episodios compartidos para garantizar no duplicación entre fases. No deben sumarse fases como episodios meteorológicos únicos.

La referencia documental aportada previamente indica 32,9 °C para R3–R6, mientras que la tabla vigente dice 32,7 °C. El cálculo conserva 32,7 °C: la correspondencia con Excel no resuelve la discrepancia bibliográfica. No se modificó el Excel ni se recalculó ninguna regla durante esta revisión.

Calendario: fechas intermedias estimadas, año etiquetado por siembra. Aún requiere alineación con el año de rendimiento. Las detecciones son excedencias bajo las reglas adoptadas, no comprobación independiente de daño productivo.

Detalle verificable en `comparativo_excel_calculo.csv` y `verificacion.json` de esta misma carpeta.
