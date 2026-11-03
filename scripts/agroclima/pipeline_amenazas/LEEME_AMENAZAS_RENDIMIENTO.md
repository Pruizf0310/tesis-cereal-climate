# Maíz: seis amenazas y rendimiento anual

Desde la carpeta de scripts:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\maize_amenazas_rendimiento.py
```

CPU local, sin GEE, ONI, MJO ni descargas. No necesita los H5 de D:. Incluye los 10.923 píxeles seleccionados y temporadas 1981–2016. No modifica ni sobrescribe los archivos originales. Cada ejecución tiene una carpeta nueva. No se ha ejecutado el análisis durante la preparación del script.

## Qué conserva y cruza

Lee el CSV completo `resumen_GDHY_anual.csv` del cálculo original de las seis fases, conserva sus reglas y conteos medios espaciales, y lo une al NetCDF de maíz sin tendencia por coordenadas exactas y año. El archivo detrendido no contiene metadatos sobre unidades ni convención de año de cosecha; por eso no se inventan porcentajes de pérdida ni una correspondencia temporal definitiva.

Por defecto produce DOS escenarios explícitos:

- `same-label`: temporada 1981 con rendimiento etiquetado 1981.
- `maturity-year`: temporada con el rendimiento del año en que termina MAT; es una aproximación al año de cosecha, no una validación del calendario GDHY. Las temporadas que caen fuera de 1981–2016 no tienen pareja.

Los escenarios son una revisión de sensibilidad, no se debe escoger automáticamente el que tenga mayor R². Si la fecha de cosecha y su convención documental quedan verificadas, se puede ejecutar solo el escenario correspondiente con `--year-alignment same-label` o `--year-alignment maturity-year`.

## Archivos en cada escenario

- `paired_annual_counts_yield.csv.gz`: una fila por píxel y temporada con EST, VEG, REP, FLO, FIL, MAT, rendimiento, combinación de fases con eventos, valores ajustados, predicción en bloques excluidos y términos asociados por fase.
- `observed_combinations.csv`: combinaciones observadas, años, cantidad de años y rendimiento medio/mediano por píxel. `NONE` significa cero en las seis reglas, no ausencia de cualquier estrés.
- `pixel_model_summary.csv`: cobertura, años sin eventos, R², R² ajustado, R² de validación por bloques, RMSE y estado del modelo.
- `phase_associations.csv`: Pearson marginal, coeficiente condicionado a las otras fases, R² parcial único, VIF y estado. Las unidades son las originales del archivo de rendimiento por unidad de conteo medio nativo. MAT cuenta días de lluvia, EST–FIL episodios de calor; no sumar estas unidades como eventos homogéneos.
- `pixel_<id>_annual_history.png/.pdf`: historia de las seis amenazas, rendimiento observado/ajustado/validación y términos asociados por fase. Por defecto usa el primer píxel seleccionado. `--pixel ID` permite elegir otro.

En la carpeta superior: `year_alignment_audit.csv` y `completed.json` documentan correspondencia temporal, fuentes, hashes y limitaciones. Los resultados se guardan en `03_Resultados/Agroclima/vigente/rendimiento/maize_seis_fases/<fecha>` y se copian al repositorio local. No hay commit ni push automático.

## Interpretación del modelo

Por píxel, OLS considera simultáneamente las seis fases variables, con intercepto y al menos 20 pares anuales válidos. El centrado/escalado interno evita problemas numéricos; los coeficientes se devuelven en las unidades originales. Es una transformación interna reversible, no altera el archivo de datos.

Los términos de cada fase son `coeficiente × (conteo anual − conteo medio)`; suman la desviación ajustada respecto al rendimiento medio. NO son pérdidas causales ni porcentajes de participación. Los R² parciales no suman el R² total: la variación compartida entre fases queda sin asignación arbitraria.

Si dos fases no se pueden separar por dependencia exacta, el script informa `PHASES_NOT_SEPARABLE` y no les asigna coeficientes. Las fases constantes no tienen coeficiente estimado. VIF >10 o condición >30 generan `UNSTABLE_COLLINEARITY`, como diagnóstico orientativo, no garantía estadística. No se calculan p-valores ni intervalos; la atribución causal no está identificada.

La validación excluye bloques contiguos de seis años. Cada ajuste se realiza solo con los años restantes. Si una fase no puede estimarse en entrenamiento o falta rango, no se inventa una predicción; R² de validación solo se publica con cobertura completa de los pares anuales. No se elige un modelo buscando el mejor resultado. La serie detrendida puede haber usado todos los años en su preparación original: esta validación es exploratoria, no una validación operativa de predicción independiente.

Ceros válidos se conservan; fases climáticas incompletas y rendimientos ausentes se excluyen del modelo. Rendimientos negativos sin tendencia se conservan. No se supone que el detrendido elimine toda variación no climática. Con 35–36 observaciones por píxel, las combinaciones raras no sustentan estimaciones firmes.

Las aproximaciones originales de calendario y fuentes permanecen visibles, incluida la discrepancia FIL 32.7/32.9 °C; este script no corrige ni recalcula el conteo climático. El coeficiente que resulte no valida por sí mismo el umbral para todas las regiones.
