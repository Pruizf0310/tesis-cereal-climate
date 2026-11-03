---
title: Correlaciones amenazas por fase – rendimiento (maíz de secano)
fecha: 2026-10-23
entrega: 2026-10-27
estado: vigente
---

# Correlaciones entre amenazas por fase y rendimiento de maíz

Pregunta que responde: **¿en cuántos píxeles el número de episodios de calor (o de días de lluvia en MAT) en una fase se asocia con un rendimiento menor, y es esa cantidad mayor de lo que daría el azar?**

Plazo: martes 27 oct 2026. Alcance acordado el 23 oct 2026:

- Solo maíz de secano: 10.923 píxeles, temporadas 1981–2016.
- Variables: los conteos de las seis amenazas por fase.
- Año: madurez como alineación principal; same-label como sensibilidad.
- Rendimiento sin enmascarar.

ONI, MJO, arroz, soya y trigo quedan fuera de esta entrega.

Código: [`scripts/agroclima/correlaciones_rendimiento/correlacion_amenazas_rendimiento.py`](../scripts/agroclima/correlaciones_rendimiento/correlacion_amenazas_rendimiento.py). Auditoría previa: [auditoría del 23 oct](auditoria_rendimiento_maiz_2026-10-23.md).

## Cómo se ejecuta

Desde `scripts/agroclima/correlaciones_rendimiento/` (usa el Python de Anaconda, que trae numpy, pandas, h5py, scipy y matplotlib):

```bash
C:/Users/paola/anaconda3/python.exe -X utf8 correlacion_amenazas_rendimiento.py --piloto 200
```

```bash
C:/Users/paola/anaconda3/python.exe -X utf8 correlacion_amenazas_rendimiento.py --alineacion maturity-year
```

```bash
C:/Users/paola/anaconda3/python.exe -X utf8 correlacion_amenazas_rendimiento.py --alineacion same-label
```

- **Duración medida (23 oct, en esta laptop: Core Ultra 7 155U, sin GPU, con el navegador abierto):**

  | Configuración | Tiempo | RAM pico |
  |---|---:|---:|
  | Sin permutaciones (r, p_t, Spearman, FDR) | 14 s | 260 MB |
  | 1.000 permutaciones por prueba + 1.000 de campo | 4,3 min | 341 MB |
  | 2.000 por prueba + 1.000 de campo (configuración oficial) | 5,2 min | 340 MB |

  La lectura inicial del CSV de 357 MB suma unos 7 s más, solo la primera vez, porque deja un caché en `_cache/insumos_*.npz`. **Esta cadena no necesita cómputo adicional ni dejar la máquina trabajando varios días.** Sí lo necesitaría recalcular amenazas para otros cultivos, que va por GEE.
- **Memoria:** los arreglos son float32 de 10.923 × 36 × 6 (unos 9 MB). Las permutaciones van en lotes de 100 (`--perm-batch`). Cabe de sobra en los ≈1,3 GB libres.
- **Si se cae:** repite el mismo comando con `--run-id <id>`. El id aparece en la primera línea de `progreso.log`. Los bloques ya terminados (`bloques/bloque_NNNN.npz`) y los lotes de campo (`campo/campo_NNN.npy`) no se recalculan. Si cambias un parámetro, el script se niega a mezclar resultados.
- **Si Windows suspende el equipo,** el proceso se pausa y sigue al despertar. Para corridas largas, desactiva la suspensión mientras estés conectada a la corriente.
- **Dónde quedan:** `C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/correlaciones_rendimiento/maize/<run_id>/`. La carpeta `resultados/` se copia al repo en `outputs/agroclima_vigente/correlaciones_rendimiento/maize/<run_id>/`. El piloto no se copia.

## Entradas

| Entrada | Ruta | Control |
|---|---|---|
| Conteos por fase | `03_Resultados/.../maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv` | SHA-256 `0ebff649…` igual al auditado; sin duplicados ni faltantes |
| Rendimiento | `02_Procesados/GDHY_detrend/maize_yield_1981_2016_DETREND_clean.nc` | coordenadas verificadas contra la lista de píxeles; años 1981–2016 |
| Píxeles | `02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv` | 10.923 |
| Clase de auditoría | `outputs/agroclima_vigente/auditoria_rendimiento/maize/auditoria_por_pixel.csv` | se agrega como columna; no filtra nada |

Solo se leen; ningún archivo de entrada se modifica.

## Qué calcula, paso a paso

1. **Empareja** cada temporada (año de siembra) con el rendimiento del año en que termina MAT. Una fase con cobertura incompleta queda como faltante, no como cero.
2. Para cada píxel y fase toma los pares válidos (*n*) y calcula:
   - **r de Pearson** y **p bilateral con la prueba t** (gl = *n* − 2). Esta prueba es válida bajo H₀ si el rendimiento detrendido es aproximadamente normal e independiente entre años; la autocorrelación lag-1 se reporta en el manifiesto.
   - **p de permutación**, con 2.000 permutaciones del rendimiento entre los pares válidos. No asume normalidad, así que sirve de control porque los conteos tienen muchos ceros.
   - **ρ de Spearman** y su p, como alternativa robusta a valores extremos.
   - **r crítico** al 5 % para ese *n*: 0,334 con *n* = 35 y 0,329 con *n* = 36. La tabla completa está en `umbral_r_por_n.csv`.
3. **Qué se prueba y qué no.** Antes de mirar resultados se definió que no se prueba cuando:
   - *n* < 20 (`MENOS_DE_MIN_ANIOS`);
   - la fase no varía entre años (`FASE_CONSTANTE`, típico de zonas sin calor extremo);
   - hay menos de 3 años con evento (`POCOS_ANIOS_CON_EVENTO`), porque con 1–2 años el r depende de esos años.

   Esos casos quedan en la tabla, sin p.
4. **Multiplicidad.** Con unas 40.000 pruebas, el 5 % saldría significativo solo por azar. Por eso se reportan tres controles:
   - **FDR Benjamini–Hochberg global** (q ≤ 0,05) sobre todas las pruebas válidas: `q_bh_global` y `sig_bh_global`. **Es el criterio principal.**
   - BH dentro de cada fase: `sig_bh_fase`.
   - BH con α_FDR = 0,10, que según Wilks (2016) controla la significancia de campo al 5 % cuando hay correlación espacial: `sig_campo_wilks`.
5. **Significancia de campo por permutación.** Permuta el orden de los años del rendimiento con **la misma permutación para todos los píxeles** (1.000 veces). Así se conserva la correlación espacial entre píxeles vecinos y se rompe solo el vínculo año a año con el clima. Compara la fracción observada de pruebas con p < 0,05, total y solo negativas, contra esa distribución nula.

## Salidas (`resultados/`)

| Archivo | Contenido |
|---|---|
| `correlaciones_pixel_fase.csv.gz` | una fila por píxel × fase: n, años con evento, conteo medio, r, p_t, p_perm, ρ, p_spearman, r crítico, q/sig BH (global, por fase, Wilks), estado, clase de auditoría y máximo crudo t/ha |
| `resumen_por_fase.csv` | por fase: pruebas, r mediano, % r < 0, % p < 0,05 (esperado 5 %), significativas BH, n mediano y estados |
| `significancia_campo.csv` | fracción observada vs. nula (media y p95) y p de campo |
| `umbral_r_por_n.csv` | r crítico al 5 % y al 1 % para n = 20–36 |
| `mapas_r_seis_fases.png/.pdf` | r por píxel en las seis fases; círculo negro = significativo BH global |
| `manifiesto.json` | parámetros, hashes de entradas y código, unidades, autocorrelación, totales y limitaciones |

En la carpeta de la corrida también quedan `progreso.log` (bitácora con hora), `parametros.json` y `COMPLETADO`, que solo existe si la corrida terminó.

## Validación hecha el 23 oct

- **r y ρ contra scipy** (`pearsonr`, `spearmanr`) en 150 pares al azar: diferencia ≤5×10⁻⁵, que es el redondeo a 4 decimales. El p_t difiere ≤5×10⁻⁷.
- **r contra la corrida OLS del 8 oct** (Pearson marginal, maturity-year): 790 pares del piloto, diferencia ≤5×10⁻⁵.
- **Reanudación:** borré un bloque y un lote de campo y relancé con `--run-id`. La tabla final quedó idéntica.
- **Nula de campo calibrada:** la fracción de p < 0,05 bajo permutación tiene media de 5,1 %, como se espera.

## Resultados (corrida oficial `maturity-year_20261023_164328`)

Carpetas: [`outputs/agroclima_vigente/correlaciones_rendimiento/maize/maturity-year_20261023_164328/`](../outputs/agroclima_vigente/correlaciones_rendimiento/maize/maturity-year_20261023_164328/) y, como sensibilidad, `same-label_20261023_164842/`.

Hay 36.800 pruebas válidas (píxel × fase). Las 28.738 restantes no se prueban: 21.976 por fase constante, 6.414 por tener menos de 3 años con evento y 348 por *n* < 20. Con *n* = 35, el r crítico al 5 % es 0,334.

| Fase | Pruebas | r mediano | % r < 0 | % p < 0,05 (azar: 5 %) | Significativas BH global | de ellas negativas | p de campo (negativas) |
|---|---:|---:|---:|---:|---:|---:|---:|
| EST | 4.039 | −0,03 | 58 % | 5,7 % | 11 | 3 | 0,032 |
| VEG | 5.516 | −0,15 | 75 % | 24,1 % | 326 | 314 | <0,001 |
| REP | 5.193 | −0,11 | 69 % | 15,7 % | 67 | 57 | <0,001 |
| FLO | 5.237 | −0,11 | 70 % | 17,8 % | 95 | 83 | <0,001 |
| FIL | 7.147 | −0,09 | 66 % | 18,5 % | 195 | 175 | <0,001 |
| MAT | 9.668 | −0,01 | 51 % | 6,9 % | 71 | 4 | 0,095 |
| **Total** | **36.800** | | | **14,4 %** | **765** | **636** | **<0,001** |

"<0,001" significa que ninguna de las 1.000 permutaciones conjuntas igualó lo observado; con 1.000 permutaciones, el mínimo resoluble es 1/1.001.

Lectura:

1. **VEG, REP, FLO y FIL tienen significancia de campo:** la fracción de píxeles con asociación negativa entre episodios de calor y rendimiento es 4–9 veces la del azar (14–23 % frente a un p95 nulo de 3,8–5,0 %). EST queda en el límite (p de campo 0,03). MAT, la lluvia en madurez, no muestra señal de campo en sentido negativo.
2. Las 765 pruebas significativas con FDR se concentran en el Corn Belt de EE. UU. (VEG y FIL), en el este de Europa y la cuenca del Danubio (FIL) y en Sudáfrica (REP, FLO y FIL). El |r| mediano de las significativas es ≈0,56.
3. **Robustez a años extremos:** al quitar el año más influyente de cada serie, 669 de las 765 conservan |r| ≥ r crítico (VEG 94 %, FIL 96 %, REP 90 %, FLO 87 %; EST 64 % y MAT 34 %). Los años más influyentes son 2012 (232 casos) y 1988 (110), las sequías de EE. UU.: son años con sentido físico, no ruido.
4. **Pearson frente a Spearman:** el porcentaje de p < 0,05 es parecido (VEG 24,1 % frente a 21,8 %), pero con FDR Spearman deja 135 pruebas y Pearson 765. Spearman pierde potencia con conteos llenos de ceros y empates, y descarta la magnitud: 5 episodios cuentan igual que 1 si quedan en el mismo rango. Como el p de permutación de Pearson coincide con el p_t (24,2 % frente a 24,1 % en VEG), la significancia de Pearson no es un artefacto de normalidad. **Decisión (23 oct 2026, validada con el director de tesis):** Pearson es la medida principal y Spearman se conserva como sensibilidad, explicando esta diferencia.
5. **Sin los 661 píxeles con años >15 t/ha** (FDR recalculado sobre 34.433 pruebas): quedan 715 significativas frente a 765. Las proporciones por fase casi no cambian (VEG 297, FIL 189, FLO 81, MAT 71, REP 66, EST 11), así que el hallazgo no depende de los rendimientos inverosímiles.
6. **same-label** (sensibilidad): 609 significativas. Mismo patrón con algo menos de señal, coherente con que el año de madurez empareja mejor en los 1.591 píxeles cuyo ciclo cruza diciembre. La alineación no se escogió por este resultado: se decidió antes.
7. La autocorrelación lag-1 mediana del rendimiento detrendido es 0,15: es baja, pero hace al p_t levemente optimista. El p de permutación no corrige esto; la significancia de campo conjunta sí conserva la estructura espacial, no la temporal.

**Qué no se puede afirmar todavía:** cuánto rendimiento quita un episodio en cada fase. Eso es lo que en este trabajo se llama "asignar un impacto a una fase". La correlación marginal no separa VEG, FLO y FIL, que comparten los mismos veranos calientes. Para asignar impacto por fase hace falta un modelo conjunto con regularización o agregación espacial (por ejemplo, regional en lugar de píxel a píxel), porque el OLS de seis fases por píxel no tiene capacidad predictiva (ver auditoría).

## Cómo leer el resultado (y cómo no)

- **Es una asociación marginal:** VEG, FLO y FIL comparten los mismos veranos calientes, así que no se pueden leer como efectos separados. Una fase significativa no excluye que el efecto venga de otra.
- r = −0,4 significa que los años con más episodios tienden a tener rendimiento por debajo de la tendencia. **No es un porcentaje de pérdida ni una causa demostrada.**
- La unidad de r es adimensional. El rendimiento es una anomalía en t/ha. EST–FIL cuentan episodios de Tmax ≥ umbral con al menos 2 días; MAT cuenta días con P > 10 mm. No mezcles las dos unidades.
- **Lo que sí sostiene el artículo:** que la fracción de píxeles con asociación negativa supere a la nula de campo, y en cuántos píxeles sobrevive al FDR.

## Pendientes conocidos

- Sensibilidad sin píxeles inverosímiles: ya está reportada en el punto 5 de Resultados. Para repetirla, filtrar `raw_max_t_ha <= 15` (NO `clase == 'OK'`, porque esa clase saca también 362 píxeles solo "dudosos") y recalcular el FDR.
- Los mapas usan coma como separador de miles (4,039); en el texto del artículo debe ir punto (4.039).
- Confirmar en Iizumi & Sakai (2020) la convención de año de GDHY.
- La discrepancia FIL 32,7/32,9 °C sigue abierta y no la resuelve este cálculo.

## Referencias de método

- Benjamini, Y. & Hochberg, Y. (1995). Controlling the false discovery rate. *J. R. Stat. Soc. B* 57, 289–300.
- Wilks, D. S. (2016). "The stippling shows statistically significant grid points". *BAMS* 97, 2263–2273.
- Livezey, R. E. & Chen, W. Y. (1983). Statistical field significance and its determination by Monte Carlo techniques. *Mon. Wea. Rev.* 111, 46–59.
