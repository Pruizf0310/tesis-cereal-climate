# Qué es una mala cosecha

Decisión del 4 nov 2026. Se aplica igual en maíz, arroz, trigo y soya, píxel por píxel.

## Criterio

Para cada píxel GDHY y cada año de 1981 a 2016:

1. **Anomalía relativa.** a = rendimiento ÷ tendencia − 1. La tendencia es la recta 1981–2016 del propio píxel, la misma de `pixel_tipico_tendencia.py`.
2. **La vara del píxel.** z = (a − mediana(a)) ÷ (1,4826 × MAD(a)), con MAD = mediana(|a − mediana(a)|).
3. **Mala cosecha** si z ≤ −1 **y** a ≤ −5 %.

El número de malas cosechas sale de cada píxel; no se fija un percentil.

## Por qué cada pieza

| Pieza | Fuente | Texto (página) |
|---|---|---|
| Mediana y MAD en lugar de media y desviación típica | Leys, C., Ley, C., Klein, O., Bernard, P., Licata, L. (2013). Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median. *Journal of Experimental Social Psychology* 49(4):764–766. DOI 10.1016/j.jesp.2013.03.013. PDF: `04_Bibliography/05_Mala_cosecha/Leys_2013_JESP_MAD.pdf` | p. 2: «The median (M) is, like the mean, a measure of central tendency but offers the advantage of being very insensitive to the presence of outliers.» p. 2: «Usually, b = 1.4826, a constant linked to the assumption of normality of the data…» p. 3: «…the Median Absolute Deviation is the most robust dispersion/scale measure in presence of outliers…» |
| Corte z ≤ −1 | Utku, A., Radulescu, M., Barut, A., Alofaysan, H. (2026). Quantifying agricultural resilience under climate variability: a data-driven climate resilience index for European cereal systems. *Scientific Reports* 16:25339. DOI 10.1038/s41598-026-54921-2. Texto de PMC13473689 (el PDF no se pudo descargar; página sin verificar) | Sección «Climate resilience index»: «Z < − 1 was chosen because it reflects a deviation of more than one standard deviation below the average yield for each country-crop, thus reflecting significant shocks as opposed to mere variations within the time series.» Prueban también −0,5 y −1,5. |
| Pérdida mínima de 5 % | GEOGLAM Crop Monitor, clases de condición del cultivo, https://cropmonitor.org/global-classification-system (consultada 4 nov 2026) | Clase «Poor»: «Crop conditions are below average, with crop yields estimated at 5–10% below average.» La página da en otro lugar 5–25 %; el límite inferior (5 %) coincide en las dos. |

**Ningún artículo combina las tres piezas.** La combinación es de esta tesis y así se declara. Utku et al. usan la desviación típica y escala país; aquí se usa la MAD y el píxel.

## Por qué no solo el 5 %

La primera versión llamaba mala cosecha a toda pérdida ≥ 5 % (corrida `malas_cosechas_20261104_170636`, superada). En Nebraska daba 9 años, pero en la mediana de los píxeles marcaba un tercio de los años, y en 1.455 píxeles de maíz la mitad o más. En maíz, la desviación típica de la anomalía relativa tiene mediana de 17,6 %: una baja de 5 % es variación normal. Con la vara de cada píxel, la rareza es la misma en todos.

## Por qué la MAD y no la desviación típica

Un año extremo agranda la desviación típica. En Nebraska, 2012 (−42,5 %) la infla, y con la desviación típica quedan 4 malas cosechas; con la MAD quedan 5 (1983, 1988, 1991, 1995, 2012). Para un seguro, el disparador no debe depender del peor año de la serie.

## Resultado (corrida `malas_cosechas_20261104_213842`)

| Cultivo | Píxeles válidos | Malas cosechas por píxel (p10 / mediana / p90) | Píxeles con ≤ 2 | z ≤ −0,5 / z ≤ −1,5 (mediana) |
|---|---|---|---|---|
| Maíz | 10.763 | 3 / 5 / 8 | 1.004 | 10 / 2 |
| Arroz | 3.179 | 3 / 6 / 8 | 152 | 10 / 3 |
| Trigo | 10.430 | 3 / 5 / 8 | 734 | 10 / 3 |
| Soya | 4.950 | 3 / 6 / 8 | 243 | 10 / 3 |

Válido = al menos 30 años con rendimiento y tendencia positiva en los 36 años. Con z ≤ −1,5 quedan 2–3 eventos por píxel: muy pocos para la estadística.

## Reproducir

```
cd scripts/agroclima/pipeline_amenazas
.venv/Scripts/python.exe malas_cosechas_pixeles.py              # los 4 cultivos, z ≤ −1 y 5 %
.venv/Scripts/python.exe malas_cosechas_pixeles.py --corte -1.5  # sensibilidad
```

Salida en `03_Resultados/Agroclima/vigente/rendimiento/malas_cosechas_<fecha>/`: `malas_cosechas.xlsx` (una hoja por cultivo y un resumen), `anual_<cultivo>.csv.gz` (píxel × año) y `resumen.json`.

## Abierto

- Qué hacer con los píxeles con 2 o menos malas cosechas.
- La diapositiva «Qué es una mala cosecha» muestra el píxel de Nebraska (`slides_correlaciones.py`, `s_mala`).
