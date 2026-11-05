# Amenazas: citas textuales por regla

Generado el 2026-11-05 desde `validacion_umbrales_20261104.xlsx` (hoja «Reglas», 31 reglas). Cada cita se re-extrajo del PDF al generar este documento, recortando entre un inicio y un fin literales; si no aparecía, el script se detenía. Las traducciones son de Claude y no son cita. Las fases siguen `docs/nomenclatura_fases.md` (REP-pre en arroz y trigo; REP-pos en maíz y soya).

Convenciones de transcripción: saltos de línea → espacio; el guion suave de fin de línea se elimina; el guion normal de fin de línea se deja pegado (p. ej. «sever-ity»); ligaduras (ﬁ, ﬂ) → fi, fl; símbolos como «◦C», «℃» y «8C» (Sipaseuth, por «°C») se dejan como los imprime el PDF.

## Índice

- R01 — Maíz · EST · Calor
- R02 — Maíz · VEG · Calor
- R03 — Maíz · VEG · Calor
- R04 — Maíz · FLO · Calor
- R05 — Maíz · REP-pos · Calor
- R06 — Maíz · FIL · Calor
- R07 — Maíz · MAT · Lluvia durante el secado
- R08 — Arroz · EST · Calor
- R09 — Arroz · VEG · Calor
- R10 — Arroz · REP-pre · Calor
- R11 — Arroz · FLO · Calor
- R12 — Arroz · FIL · Calor
- R13 — Arroz · MAT · Calor
- R14 — Soya · EST · Helada
- R15 — Soya · VEG · Calor diurno sostenido
- R16 — Soya · FLO · Calor en antesis (modelo)
- R17 — Soya · REP-pos · Calor reproductivo (modelo)
- R18 — Soya · FIL · Lluvia / calidad de semilla
- R19 — Soya · MAT · Lluvia / calidad de semilla
- R20 — Trigo · EST · Frío en emergencia
- R21 — Trigo · VEG · Helada
- R22 — Trigo · REP-pre · Helada
- R23 — Trigo · FLO · Helada
- R24 — Trigo · FIL · Helada
- R25 — Trigo · MAT · Lluvia / longevidad de semilla
- R26 — Arroz · EST · Frío en establecimiento
- R27 — Arroz · REP-pre · Frío (esterilidad)
- R28 — Arroz · FLO · Frío (esterilidad)
- R29 — Soya · FIL · Calor
- R30 — Maíz (aplicable a los 4) · Todas las de la temporada (EST–MAT) · Sequía: racha seca
- R31 — Maíz (soya: 30 °C en la misma fuente) · Todas las de la temporada (EST–MAT) · Calor continuo: días sobre 29 °C (base del EDD29)

## R01 — Maíz · Calor · EST

- **Fase homologada (tesis):** EST (maíz: VE)
- **Etapa en la fuente:** V0–VE «Sowing to Seedling» (Li 2025a, Tabla 1)
- **Cobertura:** La fuente cubre un poco más: empieza en la siembra (V0), antes de la emergencia.
- **Umbral, variable y duración según la fuente:** Tmax diaria (Td max) ≥ 34 °C como umbral de disparo (Youden). Duración: Li 2025b toma eventos de 2 días o más.
- **Regla en el Excel:** Tmax ≥ 34 °C; Racha ≥ 2 días consecutivos (criterio de inclusión de Li 2025b); variable: Tmax diaria del aire a 2 m (ERA5-Land, temperature_2m_max)
- **Severidad:** Tabla 2 Li 2025b, V0–VE: leve 2.5~4.7 d; moderada 4.7~7.7 d; severa >7.7 d
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026). Validada con la definición de evento: racha ≥ 2 d (Li 2025b p. 4) y grados de la Tabla 2 de Li 2025b (p. 7) en días enteros (techo): menor que leve 2 d; leve 3–4 d; moderado 5–7 d; severo ≥ 8 d (V0–VE).

**Fuentes:**

- Li, Q.; Wang, P.; Li, Y.; et al. (2025a). Identifying trigger thresholds for heat damage at different growth stages of summer maize: A case study of the Huang-Huai-Hai Plain, China. European Journal of Agronomy 170, 127729. DOI 10.1016/j.eja.2025.127729  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\main.pdf`  
  Páginas: LiA-youden: p. PDF 8 / impresa 8; LiA-tabla1: p. PDF 3 / impresa 3; LiA-var: p. PDF 3 / impresa 3; LiA-3d: p. PDF 6 / impresa 6
- Li, Q.; et al. (2025b). Agronomy 15(7), 1545. DOI 10.3390/agronomy15071545  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-15-01545.pdf`  
  Páginas: LiB-dur: p. PDF 4 / impresa 4 of 17; LiB-tabla2: p. PDF 7 / impresa 7 of 17; LiB-sev-texto: p. PDF 7 / impresa 7 of 17; LiB-resumen: p. PDF 1 / impresa 1 of 17

**Citas textuales:**

**[LiA-youden] umbral por subfase (Youden)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 8, p. impresa 8; §3.2.2 Optimal trigger threshold determined by ROC curve and Youden index.  
_Re-extraído ahora con PyMuPDF._

> The Youden index peaked at 34◦C, 34.1◦C, 34.6◦C, and 34.8◦C for the V0-VE, VE-V6, V6-VT, and VT-R1 growth stages (Fig. S4), respectively, under the test thresholds of 32–35◦C and 33.3–35.4◦C (Fig. 5a, b, d, e). Similarly, the Youden index reached its maximum at 33.7◦C for the R1-R3 stage and at 32.9◦C for the R3-R6 growth stage under the test thresholds of 32–35◦C and 31.7–33.8◦C, respectively (Fig. 5c, f). Therefore, the Td max values of 34, 34.1, 34.6, 34.8, 33.7, and 32.9℃ were considered the optimal trigger thresholds for determining whether heat damage occurs in summer maize at different growth stages from V0 to R6.

_Traducción (no es cita):_ El índice de Youden alcanzó su máximo en 34 °C, 34,1 °C, 34,6 °C y 34,8 °C para las etapas V0-VE, VE-V6, V6-VT y VT-R1 (Fig. S4), respectivamente, con umbrales de prueba de 32–35 °C y 33,3–35,4 °C (Fig. 5a, b, d, e). De forma similar, el índice de Youden alcanzó su máximo en 33,7 °C para la etapa R1-R3 y en 32,9 °C para la etapa R3-R6, con umbrales de prueba de 32–35 °C y 31,7–33,8 °C, respectivamente (Fig. 5c, f). Por lo tanto, los valores de Td max de 34; 34,1; 34,6; 34,8; 33,7 y 32,9 °C se consideraron los umbrales de disparo óptimos para determinar si ocurre daño por calor en el maíz de verano en las distintas etapas de V0 a R6.

**[LiA-tabla1] definición de subfases** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; Tabla 1 (Division of summer maize growth stage in HHH region) y §2.2.3.  
_Re-extraído ahora con PyMuPDF._

> Table 1 Division of summer maize growth stage in HHH region. Growth stage Description HD samples HD-free samples V0–VE Sowing to Seedling 1357 1477 VE–V6 Seedling to Jointing 2444 3106 V6–VT Jointing to Tasseling 2787 2515 VT–R1 Tasseling to Flowering 1561 1742 R1–R3 Flowering to Milk ripening 655 570 R3–R6 Milk ripening to physiological maturity 336 433

_Traducción (no es cita):_ Tabla 1. División de las etapas de crecimiento del maíz de verano en la región HHH. Etapa | Descripción | Muestras con daño | Muestras sin daño. V0–VE: siembra a plántula, 1357, 1477. VE–V6: plántula a encañado, 2444, 3106. V6–VT: encañado a panoja, 2787, 2515. VT–R1: panoja a floración, 1561, 1742. R1–R3: floración a grano lechoso, 655, 570. R3–R6: grano lechoso a madurez fisiológica, 336, 433.

**[LiA-var] variable (Tmax diaria)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; §2.2.2 Meteorological data.  
_Re-extraído ahora con PyMuPDF._

> The daily maximum temperature (Td max) data for the summer maize growing season (June to September) were collected across the HHH Plain

_Traducción (no es cita):_ Los datos de temperatura máxima diaria (Td max) de la temporada del maíz de verano (junio a septiembre) se recolectaron en toda la llanura HHH

**[LiA-3d] duración observada en las muestras** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 6, p. impresa 6; §3.1 Characteristics of the HD dataset.  
_Re-extraído ahora con PyMuPDF._

> The majority of samples experienced HD lasting for ≥3 days, accounting for approximately 98.5 % of the total samples

_Traducción (no es cita):_ La mayoría de las muestras sufrió daño por calor que duró ≥3 días, alrededor del 98,5 % del total de muestras

**[LiB-dur] duración mínima de inclusión (≥2 d)** — Li, Q.; et al.; p. PDF 4, p. impresa 4 of 17; §2.3.2 K-Means Clustering Algorithm.  
_Re-extraído ahora con PyMuPDF._

> In this study, we focused on heat damage events lasting two days or more, which were temporally aggregated according to different growth stages (V0, VE, V6, VT, R1, R3, and R6).

_Traducción (no es cita):_ En este estudio nos centramos en eventos de daño por calor de dos días o más, que se agregaron en el tiempo según las distintas etapas de crecimiento (V0, VE, V6, VT, R1, R3 y R6).

**[LiB-tabla2] severidad por duración (tabla, decimales)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; Tabla 2 (The summer maize heat damage grade indicators).  
_Re-extraído ahora con PyMuPDF._

> Table 2. The summer maize heat damage grade indicators. The Growth Stages of Summer Maize Heat Damage Grade Indicators Mild/d Moderate/d Severe/d V0–VE 2.5~4.7 4.7~7.7 >7.7 VE–V6 3.7~5.9 5.9~8.6 >8.6 V6–VT 3.5~5.4 5.4~7.5 >7.5 VT–R1 2.3~4.5 4.5~7.9 >7.9 R1–R3 2.8~4.7 4.7~8.3 >8.3 R3–R6 3.2~5.3 5.3~8.1 >8.1

_Traducción (no es cita):_ Tabla 2. Indicadores de grado de daño por calor del maíz de verano. Etapa | Leve (d) | Moderado (d) | Severo (d): V0–VE 2,5~4,7 | 4,7~7,7 | >7,7; VE–V6 3,7~5,9 | 5,9~8,6 | >8,6; V6–VT 3,5~5,4 | 5,4~7,5 | >7,5; VT–R1 2,3~4,5 | 4,5~7,9 | >7,9; R1–R3 2,8~4,7 | 4,7~8,3 | >8,3; R3–R6 3,2~5,3 | 5,3~8,1 | >8,1.

**[LiB-sev-texto] severidad por duración (texto, días enteros)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; §3.1.1 Constructing Grade Indicators for Heat Damage.  
_Re-extraído ahora con PyMuPDF._

> The thresholds for these categories were determined as follows: 3–5 days for mild heat damage, 5–8 days for moderate heat damage, and more than 8 days for severe heat damage.

_Traducción (no es cita):_ Los umbrales de estas categorías se determinaron así: 3–5 días para daño leve, 5–8 días para daño moderado y más de 8 días para daño severo.

**[LiB-resumen] clases de duración en el resumen (moderado 6–8 d)** — Li, Q.; et al.; p. PDF 1, p. impresa 1 of 17; Abstract.  
_Re-extraído ahora con PyMuPDF._

> The results identified that the duration thresholds of mild, moderate, and severe heat damage at different growth stages of summer maize are 3–5 days, 6–8 days, and more than 8 days, respectively.

_Traducción (no es cita):_ Los resultados identificaron que los umbrales de duración del daño por calor leve, moderado y severo en las distintas etapas del maíz de verano son 3–5 días, 6–8 días y más de 8 días, respectivamente.

**Valores en conflicto:** Li 2025b da la severidad en días enteros en los resultados (3–5 / 5–8 / >8 d), en el resumen con otra clase moderada (3–5 / 6–8 / >8 d) y en decimales por etapa en la Tabla 2. Las citas de ambos textos están arriba: LiB-sev-texto, LiB-resumen, LiB-tabla2.

## R02 — Maíz · Calor · VEG

- **Fase homologada (tesis):** VEG, primera parte (maíz: V1–V6)
- **Etapa en la fuente:** VE–V6 «Seedling to Jointing»
- **Cobertura:** Equivalente a nuestra primera parte de VEG.
- **Umbral, variable y duración según la fuente:** Tmax diaria ≥ 34,1 °C. Duración: ≥ 2 días (Li 2025b).
- **Regla en el Excel:** Tmax ≥ 34.1 °C; Racha ≥ 2 días consecutivos; variable: Tmax diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Tabla 2 Li 2025b, VE–V6: leve 3.7~5.9 d; moderada 5.9~8.6 d; severa >8.6 d
- **Estado:** Sí (regla nueva). Validación Paola: Aprobada en el chat el 4 nov 2026 (maíz: «ok aprobados»).

**Fuentes:**

- Li, Q.; Wang, P.; Li, Y.; et al. (2025a). Identifying trigger thresholds for heat damage at different growth stages of summer maize: A case study of the Huang-Huai-Hai Plain, China. European Journal of Agronomy 170, 127729. DOI 10.1016/j.eja.2025.127729  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\main.pdf`  
  Páginas: LiA-youden: p. PDF 8 / impresa 8; LiA-tabla1: p. PDF 3 / impresa 3; LiA-var: p. PDF 3 / impresa 3; LiA-3d: p. PDF 6 / impresa 6
- Li, Q.; et al. (2025b). Agronomy 15(7), 1545. DOI 10.3390/agronomy15071545  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-15-01545.pdf`  
  Páginas: LiB-dur: p. PDF 4 / impresa 4 of 17; LiB-tabla2: p. PDF 7 / impresa 7 of 17; LiB-sev-texto: p. PDF 7 / impresa 7 of 17

**Citas textuales:**

**[LiA-youden] umbral por subfase (Youden)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 8, p. impresa 8; §3.2.2 Optimal trigger threshold determined by ROC curve and Youden index.  
_Re-extraído ahora con PyMuPDF._

> The Youden index peaked at 34◦C, 34.1◦C, 34.6◦C, and 34.8◦C for the V0-VE, VE-V6, V6-VT, and VT-R1 growth stages (Fig. S4), respectively, under the test thresholds of 32–35◦C and 33.3–35.4◦C (Fig. 5a, b, d, e). Similarly, the Youden index reached its maximum at 33.7◦C for the R1-R3 stage and at 32.9◦C for the R3-R6 growth stage under the test thresholds of 32–35◦C and 31.7–33.8◦C, respectively (Fig. 5c, f). Therefore, the Td max values of 34, 34.1, 34.6, 34.8, 33.7, and 32.9℃ were considered the optimal trigger thresholds for determining whether heat damage occurs in summer maize at different growth stages from V0 to R6.

_Traducción (no es cita):_ El índice de Youden alcanzó su máximo en 34 °C, 34,1 °C, 34,6 °C y 34,8 °C para las etapas V0-VE, VE-V6, V6-VT y VT-R1 (Fig. S4), respectivamente, con umbrales de prueba de 32–35 °C y 33,3–35,4 °C (Fig. 5a, b, d, e). De forma similar, el índice de Youden alcanzó su máximo en 33,7 °C para la etapa R1-R3 y en 32,9 °C para la etapa R3-R6, con umbrales de prueba de 32–35 °C y 31,7–33,8 °C, respectivamente (Fig. 5c, f). Por lo tanto, los valores de Td max de 34; 34,1; 34,6; 34,8; 33,7 y 32,9 °C se consideraron los umbrales de disparo óptimos para determinar si ocurre daño por calor en el maíz de verano en las distintas etapas de V0 a R6.

**[LiA-tabla1] definición de subfases** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; Tabla 1 (Division of summer maize growth stage in HHH region) y §2.2.3.  
_Re-extraído ahora con PyMuPDF._

> Table 1 Division of summer maize growth stage in HHH region. Growth stage Description HD samples HD-free samples V0–VE Sowing to Seedling 1357 1477 VE–V6 Seedling to Jointing 2444 3106 V6–VT Jointing to Tasseling 2787 2515 VT–R1 Tasseling to Flowering 1561 1742 R1–R3 Flowering to Milk ripening 655 570 R3–R6 Milk ripening to physiological maturity 336 433

_Traducción (no es cita):_ Tabla 1. División de las etapas de crecimiento del maíz de verano en la región HHH. Etapa | Descripción | Muestras con daño | Muestras sin daño. V0–VE: siembra a plántula, 1357, 1477. VE–V6: plántula a encañado, 2444, 3106. V6–VT: encañado a panoja, 2787, 2515. VT–R1: panoja a floración, 1561, 1742. R1–R3: floración a grano lechoso, 655, 570. R3–R6: grano lechoso a madurez fisiológica, 336, 433.

**[LiA-var] variable (Tmax diaria)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; §2.2.2 Meteorological data.  
_Re-extraído ahora con PyMuPDF._

> The daily maximum temperature (Td max) data for the summer maize growing season (June to September) were collected across the HHH Plain

_Traducción (no es cita):_ Los datos de temperatura máxima diaria (Td max) de la temporada del maíz de verano (junio a septiembre) se recolectaron en toda la llanura HHH

**[LiA-3d] duración observada en las muestras** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 6, p. impresa 6; §3.1 Characteristics of the HD dataset.  
_Re-extraído ahora con PyMuPDF._

> The majority of samples experienced HD lasting for ≥3 days, accounting for approximately 98.5 % of the total samples

_Traducción (no es cita):_ La mayoría de las muestras sufrió daño por calor que duró ≥3 días, alrededor del 98,5 % del total de muestras

**[LiB-dur] duración mínima de inclusión (≥2 d)** — Li, Q.; et al.; p. PDF 4, p. impresa 4 of 17; §2.3.2 K-Means Clustering Algorithm.  
_Re-extraído ahora con PyMuPDF._

> In this study, we focused on heat damage events lasting two days or more, which were temporally aggregated according to different growth stages (V0, VE, V6, VT, R1, R3, and R6).

_Traducción (no es cita):_ En este estudio nos centramos en eventos de daño por calor de dos días o más, que se agregaron en el tiempo según las distintas etapas de crecimiento (V0, VE, V6, VT, R1, R3 y R6).

**[LiB-tabla2] severidad por duración (tabla, decimales)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; Tabla 2 (The summer maize heat damage grade indicators).  
_Re-extraído ahora con PyMuPDF._

> Table 2. The summer maize heat damage grade indicators. The Growth Stages of Summer Maize Heat Damage Grade Indicators Mild/d Moderate/d Severe/d V0–VE 2.5~4.7 4.7~7.7 >7.7 VE–V6 3.7~5.9 5.9~8.6 >8.6 V6–VT 3.5~5.4 5.4~7.5 >7.5 VT–R1 2.3~4.5 4.5~7.9 >7.9 R1–R3 2.8~4.7 4.7~8.3 >8.3 R3–R6 3.2~5.3 5.3~8.1 >8.1

_Traducción (no es cita):_ Tabla 2. Indicadores de grado de daño por calor del maíz de verano. Etapa | Leve (d) | Moderado (d) | Severo (d): V0–VE 2,5~4,7 | 4,7~7,7 | >7,7; VE–V6 3,7~5,9 | 5,9~8,6 | >8,6; V6–VT 3,5~5,4 | 5,4~7,5 | >7,5; VT–R1 2,3~4,5 | 4,5~7,9 | >7,9; R1–R3 2,8~4,7 | 4,7~8,3 | >8,3; R3–R6 3,2~5,3 | 5,3~8,1 | >8,1.

**[LiB-sev-texto] severidad por duración (texto, días enteros)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; §3.1.1 Constructing Grade Indicators for Heat Damage.  
_Re-extraído ahora con PyMuPDF._

> The thresholds for these categories were determined as follows: 3–5 days for mild heat damage, 5–8 days for moderate heat damage, and more than 8 days for severe heat damage.

_Traducción (no es cita):_ Los umbrales de estas categorías se determinaron así: 3–5 días para daño leve, 5–8 días para daño moderado y más de 8 días para daño severo.

**Valores en conflicto:** ver R01 (severidad: texto vs. Tabla 2 de Li 2025b).

## R03 — Maíz · Calor · VEG

- **Fase homologada (tesis):** VEG, segunda parte (maíz: V7–VT)
- **Etapa en la fuente:** V6–VT «Jointing to Tasseling»
- **Cobertura:** Equivalente a nuestra segunda parte de VEG.
- **Umbral, variable y duración según la fuente:** Tmax diaria ≥ 34,6 °C. Duración: ≥ 2 días (Li 2025b).
- **Regla en el Excel:** Tmax ≥ 34.6 °C; Racha ≥ 2 días consecutivos; variable: Tmax diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Tabla 2 Li 2025b, V6–VT: leve 3.5~5.4 d; moderada 5.4~7.5 d; severa >7.5 d
- **Estado:** No (se acota a V7–VT). Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Li, Q.; Wang, P.; Li, Y.; et al. (2025a). Identifying trigger thresholds for heat damage at different growth stages of summer maize: A case study of the Huang-Huai-Hai Plain, China. European Journal of Agronomy 170, 127729. DOI 10.1016/j.eja.2025.127729  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\main.pdf`  
  Páginas: LiA-youden: p. PDF 8 / impresa 8; LiA-tabla1: p. PDF 3 / impresa 3; LiA-var: p. PDF 3 / impresa 3; LiA-3d: p. PDF 6 / impresa 6
- Li, Q.; et al. (2025b). Agronomy 15(7), 1545. DOI 10.3390/agronomy15071545  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-15-01545.pdf`  
  Páginas: LiB-dur: p. PDF 4 / impresa 4 of 17; LiB-tabla2: p. PDF 7 / impresa 7 of 17; LiB-sev-texto: p. PDF 7 / impresa 7 of 17

**Citas textuales:**

**[LiA-youden] umbral por subfase (Youden)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 8, p. impresa 8; §3.2.2 Optimal trigger threshold determined by ROC curve and Youden index.  
_Re-extraído ahora con PyMuPDF._

> The Youden index peaked at 34◦C, 34.1◦C, 34.6◦C, and 34.8◦C for the V0-VE, VE-V6, V6-VT, and VT-R1 growth stages (Fig. S4), respectively, under the test thresholds of 32–35◦C and 33.3–35.4◦C (Fig. 5a, b, d, e). Similarly, the Youden index reached its maximum at 33.7◦C for the R1-R3 stage and at 32.9◦C for the R3-R6 growth stage under the test thresholds of 32–35◦C and 31.7–33.8◦C, respectively (Fig. 5c, f). Therefore, the Td max values of 34, 34.1, 34.6, 34.8, 33.7, and 32.9℃ were considered the optimal trigger thresholds for determining whether heat damage occurs in summer maize at different growth stages from V0 to R6.

_Traducción (no es cita):_ El índice de Youden alcanzó su máximo en 34 °C, 34,1 °C, 34,6 °C y 34,8 °C para las etapas V0-VE, VE-V6, V6-VT y VT-R1 (Fig. S4), respectivamente, con umbrales de prueba de 32–35 °C y 33,3–35,4 °C (Fig. 5a, b, d, e). De forma similar, el índice de Youden alcanzó su máximo en 33,7 °C para la etapa R1-R3 y en 32,9 °C para la etapa R3-R6, con umbrales de prueba de 32–35 °C y 31,7–33,8 °C, respectivamente (Fig. 5c, f). Por lo tanto, los valores de Td max de 34; 34,1; 34,6; 34,8; 33,7 y 32,9 °C se consideraron los umbrales de disparo óptimos para determinar si ocurre daño por calor en el maíz de verano en las distintas etapas de V0 a R6.

**[LiA-tabla1] definición de subfases** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; Tabla 1 (Division of summer maize growth stage in HHH region) y §2.2.3.  
_Re-extraído ahora con PyMuPDF._

> Table 1 Division of summer maize growth stage in HHH region. Growth stage Description HD samples HD-free samples V0–VE Sowing to Seedling 1357 1477 VE–V6 Seedling to Jointing 2444 3106 V6–VT Jointing to Tasseling 2787 2515 VT–R1 Tasseling to Flowering 1561 1742 R1–R3 Flowering to Milk ripening 655 570 R3–R6 Milk ripening to physiological maturity 336 433

_Traducción (no es cita):_ Tabla 1. División de las etapas de crecimiento del maíz de verano en la región HHH. Etapa | Descripción | Muestras con daño | Muestras sin daño. V0–VE: siembra a plántula, 1357, 1477. VE–V6: plántula a encañado, 2444, 3106. V6–VT: encañado a panoja, 2787, 2515. VT–R1: panoja a floración, 1561, 1742. R1–R3: floración a grano lechoso, 655, 570. R3–R6: grano lechoso a madurez fisiológica, 336, 433.

**[LiA-var] variable (Tmax diaria)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; §2.2.2 Meteorological data.  
_Re-extraído ahora con PyMuPDF._

> The daily maximum temperature (Td max) data for the summer maize growing season (June to September) were collected across the HHH Plain

_Traducción (no es cita):_ Los datos de temperatura máxima diaria (Td max) de la temporada del maíz de verano (junio a septiembre) se recolectaron en toda la llanura HHH

**[LiA-3d] duración observada en las muestras** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 6, p. impresa 6; §3.1 Characteristics of the HD dataset.  
_Re-extraído ahora con PyMuPDF._

> The majority of samples experienced HD lasting for ≥3 days, accounting for approximately 98.5 % of the total samples

_Traducción (no es cita):_ La mayoría de las muestras sufrió daño por calor que duró ≥3 días, alrededor del 98,5 % del total de muestras

**[LiB-dur] duración mínima de inclusión (≥2 d)** — Li, Q.; et al.; p. PDF 4, p. impresa 4 of 17; §2.3.2 K-Means Clustering Algorithm.  
_Re-extraído ahora con PyMuPDF._

> In this study, we focused on heat damage events lasting two days or more, which were temporally aggregated according to different growth stages (V0, VE, V6, VT, R1, R3, and R6).

_Traducción (no es cita):_ En este estudio nos centramos en eventos de daño por calor de dos días o más, que se agregaron en el tiempo según las distintas etapas de crecimiento (V0, VE, V6, VT, R1, R3 y R6).

**[LiB-tabla2] severidad por duración (tabla, decimales)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; Tabla 2 (The summer maize heat damage grade indicators).  
_Re-extraído ahora con PyMuPDF._

> Table 2. The summer maize heat damage grade indicators. The Growth Stages of Summer Maize Heat Damage Grade Indicators Mild/d Moderate/d Severe/d V0–VE 2.5~4.7 4.7~7.7 >7.7 VE–V6 3.7~5.9 5.9~8.6 >8.6 V6–VT 3.5~5.4 5.4~7.5 >7.5 VT–R1 2.3~4.5 4.5~7.9 >7.9 R1–R3 2.8~4.7 4.7~8.3 >8.3 R3–R6 3.2~5.3 5.3~8.1 >8.1

_Traducción (no es cita):_ Tabla 2. Indicadores de grado de daño por calor del maíz de verano. Etapa | Leve (d) | Moderado (d) | Severo (d): V0–VE 2,5~4,7 | 4,7~7,7 | >7,7; VE–V6 3,7~5,9 | 5,9~8,6 | >8,6; V6–VT 3,5~5,4 | 5,4~7,5 | >7,5; VT–R1 2,3~4,5 | 4,5~7,9 | >7,9; R1–R3 2,8~4,7 | 4,7~8,3 | >8,3; R3–R6 3,2~5,3 | 5,3~8,1 | >8,1.

**[LiB-sev-texto] severidad por duración (texto, días enteros)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; §3.1.1 Constructing Grade Indicators for Heat Damage.  
_Re-extraído ahora con PyMuPDF._

> The thresholds for these categories were determined as follows: 3–5 days for mild heat damage, 5–8 days for moderate heat damage, and more than 8 days for severe heat damage.

_Traducción (no es cita):_ Los umbrales de estas categorías se determinaron así: 3–5 días para daño leve, 5–8 días para daño moderado y más de 8 días para daño severo.

**Valores en conflicto:** ver R01 (severidad: texto vs. Tabla 2 de Li 2025b).

## R04 — Maíz · Calor · FLO

- **Fase homologada (tesis):** FLO (maíz: R1)
- **Etapa en la fuente:** R1–R3 «Flowering to Milk ripening»
- **Cobertura:** La fuente cubre más: R1–R3 abarca FLO, REP-pos (R2) y el inicio de FIL (R3). La fuente también da VT–R1 «Tasseling to Flowering» = 34,8 °C, que no se usa (decisión del 3 nov 2026).
- **Umbral, variable y duración según la fuente:** Tmax diaria ≥ 33,7 °C. Duración: ≥ 2 días (Li 2025b).
- **Regla en el Excel:** Tmax ≥ 33.7 °C; Racha ≥ 2 días consecutivos; variable: Tmax diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Tabla 2 Li 2025b, R1–R3: leve 2.8~4.7 d; moderada 4.7~8.3 d; severa >8.3 d
- **Estado:** No (valor); sí la cita primaria. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Li, Q.; Wang, P.; Li, Y.; et al. (2025a). Identifying trigger thresholds for heat damage at different growth stages of summer maize: A case study of the Huang-Huai-Hai Plain, China. European Journal of Agronomy 170, 127729. DOI 10.1016/j.eja.2025.127729  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\main.pdf`  
  Páginas: LiA-youden: p. PDF 8 / impresa 8; LiA-tabla1: p. PDF 3 / impresa 3; LiA-var: p. PDF 3 / impresa 3; LiA-3d: p. PDF 6 / impresa 6
- Li, Q.; et al. (2025b). Agronomy 15(7), 1545. DOI 10.3390/agronomy15071545  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-15-01545.pdf`  
  Páginas: LiB-dur: p. PDF 4 / impresa 4 of 17; LiB-tabla2: p. PDF 7 / impresa 7 of 17; LiB-sev-texto: p. PDF 7 / impresa 7 of 17; LiB-umbrales: p. PDF 4 / impresa 4 of 17

**Citas textuales:**

**[LiA-youden] umbral por subfase (Youden)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 8, p. impresa 8; §3.2.2 Optimal trigger threshold determined by ROC curve and Youden index.  
_Re-extraído ahora con PyMuPDF._

> The Youden index peaked at 34◦C, 34.1◦C, 34.6◦C, and 34.8◦C for the V0-VE, VE-V6, V6-VT, and VT-R1 growth stages (Fig. S4), respectively, under the test thresholds of 32–35◦C and 33.3–35.4◦C (Fig. 5a, b, d, e). Similarly, the Youden index reached its maximum at 33.7◦C for the R1-R3 stage and at 32.9◦C for the R3-R6 growth stage under the test thresholds of 32–35◦C and 31.7–33.8◦C, respectively (Fig. 5c, f). Therefore, the Td max values of 34, 34.1, 34.6, 34.8, 33.7, and 32.9℃ were considered the optimal trigger thresholds for determining whether heat damage occurs in summer maize at different growth stages from V0 to R6.

_Traducción (no es cita):_ El índice de Youden alcanzó su máximo en 34 °C, 34,1 °C, 34,6 °C y 34,8 °C para las etapas V0-VE, VE-V6, V6-VT y VT-R1 (Fig. S4), respectivamente, con umbrales de prueba de 32–35 °C y 33,3–35,4 °C (Fig. 5a, b, d, e). De forma similar, el índice de Youden alcanzó su máximo en 33,7 °C para la etapa R1-R3 y en 32,9 °C para la etapa R3-R6, con umbrales de prueba de 32–35 °C y 31,7–33,8 °C, respectivamente (Fig. 5c, f). Por lo tanto, los valores de Td max de 34; 34,1; 34,6; 34,8; 33,7 y 32,9 °C se consideraron los umbrales de disparo óptimos para determinar si ocurre daño por calor en el maíz de verano en las distintas etapas de V0 a R6.

**[LiA-tabla1] definición de subfases** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; Tabla 1 (Division of summer maize growth stage in HHH region) y §2.2.3.  
_Re-extraído ahora con PyMuPDF._

> Table 1 Division of summer maize growth stage in HHH region. Growth stage Description HD samples HD-free samples V0–VE Sowing to Seedling 1357 1477 VE–V6 Seedling to Jointing 2444 3106 V6–VT Jointing to Tasseling 2787 2515 VT–R1 Tasseling to Flowering 1561 1742 R1–R3 Flowering to Milk ripening 655 570 R3–R6 Milk ripening to physiological maturity 336 433

_Traducción (no es cita):_ Tabla 1. División de las etapas de crecimiento del maíz de verano en la región HHH. Etapa | Descripción | Muestras con daño | Muestras sin daño. V0–VE: siembra a plántula, 1357, 1477. VE–V6: plántula a encañado, 2444, 3106. V6–VT: encañado a panoja, 2787, 2515. VT–R1: panoja a floración, 1561, 1742. R1–R3: floración a grano lechoso, 655, 570. R3–R6: grano lechoso a madurez fisiológica, 336, 433.

**[LiA-var] variable (Tmax diaria)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; §2.2.2 Meteorological data.  
_Re-extraído ahora con PyMuPDF._

> The daily maximum temperature (Td max) data for the summer maize growing season (June to September) were collected across the HHH Plain

_Traducción (no es cita):_ Los datos de temperatura máxima diaria (Td max) de la temporada del maíz de verano (junio a septiembre) se recolectaron en toda la llanura HHH

**[LiA-3d] duración observada en las muestras** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 6, p. impresa 6; §3.1 Characteristics of the HD dataset.  
_Re-extraído ahora con PyMuPDF._

> The majority of samples experienced HD lasting for ≥3 days, accounting for approximately 98.5 % of the total samples

_Traducción (no es cita):_ La mayoría de las muestras sufrió daño por calor que duró ≥3 días, alrededor del 98,5 % del total de muestras

**[LiB-dur] duración mínima de inclusión (≥2 d)** — Li, Q.; et al.; p. PDF 4, p. impresa 4 of 17; §2.3.2 K-Means Clustering Algorithm.  
_Re-extraído ahora con PyMuPDF._

> In this study, we focused on heat damage events lasting two days or more, which were temporally aggregated according to different growth stages (V0, VE, V6, VT, R1, R3, and R6).

_Traducción (no es cita):_ En este estudio nos centramos en eventos de daño por calor de dos días o más, que se agregaron en el tiempo según las distintas etapas de crecimiento (V0, VE, V6, VT, R1, R3 y R6).

**[LiB-tabla2] severidad por duración (tabla, decimales)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; Tabla 2 (The summer maize heat damage grade indicators).  
_Re-extraído ahora con PyMuPDF._

> Table 2. The summer maize heat damage grade indicators. The Growth Stages of Summer Maize Heat Damage Grade Indicators Mild/d Moderate/d Severe/d V0–VE 2.5~4.7 4.7~7.7 >7.7 VE–V6 3.7~5.9 5.9~8.6 >8.6 V6–VT 3.5~5.4 5.4~7.5 >7.5 VT–R1 2.3~4.5 4.5~7.9 >7.9 R1–R3 2.8~4.7 4.7~8.3 >8.3 R3–R6 3.2~5.3 5.3~8.1 >8.1

_Traducción (no es cita):_ Tabla 2. Indicadores de grado de daño por calor del maíz de verano. Etapa | Leve (d) | Moderado (d) | Severo (d): V0–VE 2,5~4,7 | 4,7~7,7 | >7,7; VE–V6 3,7~5,9 | 5,9~8,6 | >8,6; V6–VT 3,5~5,4 | 5,4~7,5 | >7,5; VT–R1 2,3~4,5 | 4,5~7,9 | >7,9; R1–R3 2,8~4,7 | 4,7~8,3 | >8,3; R3–R6 3,2~5,3 | 5,3~8,1 | >8,1.

**[LiB-sev-texto] severidad por duración (texto, días enteros)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; §3.1.1 Constructing Grade Indicators for Heat Damage.  
_Re-extraído ahora con PyMuPDF._

> The thresholds for these categories were determined as follows: 3–5 days for mild heat damage, 5–8 days for moderate heat damage, and more than 8 days for severe heat damage.

_Traducción (no es cita):_ Los umbrales de estas categorías se determinaron así: 3–5 días para daño leve, 5–8 días para daño moderado y más de 8 días para daño severo.

**[LiB-umbrales] umbrales citados (32,7 en R3–R6)** — Li, Q.; et al.; p. PDF 4, p. impresa 4 of 17; §2.3.1 Construction of Heat Damage Indicators for Different Grades.  
_Re-extraído ahora con PyMuPDF._

> Previous studies have identified different growth stages of summer maize and their corresponding heat stress thresholds: the sowing-to-emergence stage (early to mid-June), emergence-to-jointing stage (late June to mid-July), jointing-to-tasseling stage (mid to late July), tasseling-to-flowering stage (early August), flowering-to-milk-ripening stage (mid to late August), and milk-ripening-to-physiological-maturity stage (early to late September). The heat damage thresholds for these respective growth stages were determined as Td max ≥34 ◦C, 34.1 ◦C, 34.6 ◦C, 34.8 ◦C, 33.7 ◦C, and 32.7 ◦C [9,37].

_Traducción (no es cita):_ Estudios previos identificaron distintas etapas del maíz de verano y sus umbrales de estrés por calor: siembra a emergencia (inicios a mediados de junio), emergencia a encañado (finales de junio a mediados de julio), encañado a panoja (mediados a finales de julio), panoja a floración (inicios de agosto), floración a grano lechoso (mediados a finales de agosto) y grano lechoso a madurez fisiológica (inicios a finales de septiembre). Los umbrales de daño por calor para estas etapas se determinaron como Td max ≥ 34 °C; 34,1 °C; 34,6 °C; 34,8 °C; 33,7 °C y 32,7 °C [9,37].

**Valores en conflicto:** ver R01 (severidad: texto vs. Tabla 2 de Li 2025b).

## R05 — Maíz · Calor · REP-pos

- **Fase homologada (tesis):** REP-pos (maíz: R2)
- **Etapa en la fuente:** R1–R3 «Flowering to Milk ripening»
- **Cobertura:** La fuente cubre más (R1–R3); la misma ventana se usa para FLO: no contar dos veces el mismo episodio.
- **Umbral, variable y duración según la fuente:** Tmax diaria ≥ 33,7 °C. Duración: ≥ 2 días (Li 2025b).
- **Regla en el Excel:** Tmax ≥ 33.7 °C; Racha ≥ 2 días consecutivos; variable: Tmax diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Tabla 2 Li 2025b, R1–R3: leve 2.8~4.7 d; moderada 4.7~8.3 d; severa >8.3 d
- **Estado:** No (valor); sí la cita primaria. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Li, Q.; Wang, P.; Li, Y.; et al. (2025a). Identifying trigger thresholds for heat damage at different growth stages of summer maize: A case study of the Huang-Huai-Hai Plain, China. European Journal of Agronomy 170, 127729. DOI 10.1016/j.eja.2025.127729  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\main.pdf`  
  Páginas: LiA-youden: p. PDF 8 / impresa 8; LiA-tabla1: p. PDF 3 / impresa 3; LiA-var: p. PDF 3 / impresa 3; LiA-3d: p. PDF 6 / impresa 6
- Li, Q.; et al. (2025b). Agronomy 15(7), 1545. DOI 10.3390/agronomy15071545  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-15-01545.pdf`  
  Páginas: LiB-dur: p. PDF 4 / impresa 4 of 17; LiB-tabla2: p. PDF 7 / impresa 7 of 17; LiB-sev-texto: p. PDF 7 / impresa 7 of 17; LiB-umbrales: p. PDF 4 / impresa 4 of 17

**Citas textuales:**

**[LiA-youden] umbral por subfase (Youden)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 8, p. impresa 8; §3.2.2 Optimal trigger threshold determined by ROC curve and Youden index.  
_Re-extraído ahora con PyMuPDF._

> The Youden index peaked at 34◦C, 34.1◦C, 34.6◦C, and 34.8◦C for the V0-VE, VE-V6, V6-VT, and VT-R1 growth stages (Fig. S4), respectively, under the test thresholds of 32–35◦C and 33.3–35.4◦C (Fig. 5a, b, d, e). Similarly, the Youden index reached its maximum at 33.7◦C for the R1-R3 stage and at 32.9◦C for the R3-R6 growth stage under the test thresholds of 32–35◦C and 31.7–33.8◦C, respectively (Fig. 5c, f). Therefore, the Td max values of 34, 34.1, 34.6, 34.8, 33.7, and 32.9℃ were considered the optimal trigger thresholds for determining whether heat damage occurs in summer maize at different growth stages from V0 to R6.

_Traducción (no es cita):_ El índice de Youden alcanzó su máximo en 34 °C, 34,1 °C, 34,6 °C y 34,8 °C para las etapas V0-VE, VE-V6, V6-VT y VT-R1 (Fig. S4), respectivamente, con umbrales de prueba de 32–35 °C y 33,3–35,4 °C (Fig. 5a, b, d, e). De forma similar, el índice de Youden alcanzó su máximo en 33,7 °C para la etapa R1-R3 y en 32,9 °C para la etapa R3-R6, con umbrales de prueba de 32–35 °C y 31,7–33,8 °C, respectivamente (Fig. 5c, f). Por lo tanto, los valores de Td max de 34; 34,1; 34,6; 34,8; 33,7 y 32,9 °C se consideraron los umbrales de disparo óptimos para determinar si ocurre daño por calor en el maíz de verano en las distintas etapas de V0 a R6.

**[LiA-tabla1] definición de subfases** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; Tabla 1 (Division of summer maize growth stage in HHH region) y §2.2.3.  
_Re-extraído ahora con PyMuPDF._

> Table 1 Division of summer maize growth stage in HHH region. Growth stage Description HD samples HD-free samples V0–VE Sowing to Seedling 1357 1477 VE–V6 Seedling to Jointing 2444 3106 V6–VT Jointing to Tasseling 2787 2515 VT–R1 Tasseling to Flowering 1561 1742 R1–R3 Flowering to Milk ripening 655 570 R3–R6 Milk ripening to physiological maturity 336 433

_Traducción (no es cita):_ Tabla 1. División de las etapas de crecimiento del maíz de verano en la región HHH. Etapa | Descripción | Muestras con daño | Muestras sin daño. V0–VE: siembra a plántula, 1357, 1477. VE–V6: plántula a encañado, 2444, 3106. V6–VT: encañado a panoja, 2787, 2515. VT–R1: panoja a floración, 1561, 1742. R1–R3: floración a grano lechoso, 655, 570. R3–R6: grano lechoso a madurez fisiológica, 336, 433.

**[LiA-var] variable (Tmax diaria)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; §2.2.2 Meteorological data.  
_Re-extraído ahora con PyMuPDF._

> The daily maximum temperature (Td max) data for the summer maize growing season (June to September) were collected across the HHH Plain

_Traducción (no es cita):_ Los datos de temperatura máxima diaria (Td max) de la temporada del maíz de verano (junio a septiembre) se recolectaron en toda la llanura HHH

**[LiA-3d] duración observada en las muestras** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 6, p. impresa 6; §3.1 Characteristics of the HD dataset.  
_Re-extraído ahora con PyMuPDF._

> The majority of samples experienced HD lasting for ≥3 days, accounting for approximately 98.5 % of the total samples

_Traducción (no es cita):_ La mayoría de las muestras sufrió daño por calor que duró ≥3 días, alrededor del 98,5 % del total de muestras

**[LiB-dur] duración mínima de inclusión (≥2 d)** — Li, Q.; et al.; p. PDF 4, p. impresa 4 of 17; §2.3.2 K-Means Clustering Algorithm.  
_Re-extraído ahora con PyMuPDF._

> In this study, we focused on heat damage events lasting two days or more, which were temporally aggregated according to different growth stages (V0, VE, V6, VT, R1, R3, and R6).

_Traducción (no es cita):_ En este estudio nos centramos en eventos de daño por calor de dos días o más, que se agregaron en el tiempo según las distintas etapas de crecimiento (V0, VE, V6, VT, R1, R3 y R6).

**[LiB-tabla2] severidad por duración (tabla, decimales)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; Tabla 2 (The summer maize heat damage grade indicators).  
_Re-extraído ahora con PyMuPDF._

> Table 2. The summer maize heat damage grade indicators. The Growth Stages of Summer Maize Heat Damage Grade Indicators Mild/d Moderate/d Severe/d V0–VE 2.5~4.7 4.7~7.7 >7.7 VE–V6 3.7~5.9 5.9~8.6 >8.6 V6–VT 3.5~5.4 5.4~7.5 >7.5 VT–R1 2.3~4.5 4.5~7.9 >7.9 R1–R3 2.8~4.7 4.7~8.3 >8.3 R3–R6 3.2~5.3 5.3~8.1 >8.1

_Traducción (no es cita):_ Tabla 2. Indicadores de grado de daño por calor del maíz de verano. Etapa | Leve (d) | Moderado (d) | Severo (d): V0–VE 2,5~4,7 | 4,7~7,7 | >7,7; VE–V6 3,7~5,9 | 5,9~8,6 | >8,6; V6–VT 3,5~5,4 | 5,4~7,5 | >7,5; VT–R1 2,3~4,5 | 4,5~7,9 | >7,9; R1–R3 2,8~4,7 | 4,7~8,3 | >8,3; R3–R6 3,2~5,3 | 5,3~8,1 | >8,1.

**[LiB-sev-texto] severidad por duración (texto, días enteros)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; §3.1.1 Constructing Grade Indicators for Heat Damage.  
_Re-extraído ahora con PyMuPDF._

> The thresholds for these categories were determined as follows: 3–5 days for mild heat damage, 5–8 days for moderate heat damage, and more than 8 days for severe heat damage.

_Traducción (no es cita):_ Los umbrales de estas categorías se determinaron así: 3–5 días para daño leve, 5–8 días para daño moderado y más de 8 días para daño severo.

**[LiB-umbrales] umbrales citados (32,7 en R3–R6)** — Li, Q.; et al.; p. PDF 4, p. impresa 4 of 17; §2.3.1 Construction of Heat Damage Indicators for Different Grades.  
_Re-extraído ahora con PyMuPDF._

> Previous studies have identified different growth stages of summer maize and their corresponding heat stress thresholds: the sowing-to-emergence stage (early to mid-June), emergence-to-jointing stage (late June to mid-July), jointing-to-tasseling stage (mid to late July), tasseling-to-flowering stage (early August), flowering-to-milk-ripening stage (mid to late August), and milk-ripening-to-physiological-maturity stage (early to late September). The heat damage thresholds for these respective growth stages were determined as Td max ≥34 ◦C, 34.1 ◦C, 34.6 ◦C, 34.8 ◦C, 33.7 ◦C, and 32.7 ◦C [9,37].

_Traducción (no es cita):_ Estudios previos identificaron distintas etapas del maíz de verano y sus umbrales de estrés por calor: siembra a emergencia (inicios a mediados de junio), emergencia a encañado (finales de junio a mediados de julio), encañado a panoja (mediados a finales de julio), panoja a floración (inicios de agosto), floración a grano lechoso (mediados a finales de agosto) y grano lechoso a madurez fisiológica (inicios a finales de septiembre). Los umbrales de daño por calor para estas etapas se determinaron como Td max ≥ 34 °C; 34,1 °C; 34,6 °C; 34,8 °C; 33,7 °C y 32,7 °C [9,37].

**Valores en conflicto:** ver R01 (severidad: texto vs. Tabla 2 de Li 2025b).

## R06 — Maíz · Calor · FIL

- **Fase homologada (tesis):** FIL (maíz: R3, R4–R5)
- **Etapa en la fuente:** R3–R6 «Milk ripening to physiological maturity»
- **Cobertura:** La fuente cubre más: incluye R6, que en la tesis es MAT.
- **Umbral, variable y duración según la fuente:** Tmax diaria: 32,9 °C en Li 2025a (Youden); 32,7 °C en Li 2025b. Duración: ≥ 2 días (Li 2025b).
- **Regla en el Excel:** Tmax ≥ 32.9 °C; Racha ≥ 2 días consecutivos; variable: Tmax diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Tabla 2 Li 2025b, R3–R6: leve 3.2~5.3 d; moderada 5.3~8.1 d; severa >8.1 d
- **Estado:** Sí (32.7 → 32.9 °C). Validación Paola: Aprobada en el chat el 4 nov 2026 (maíz: «ok aprobados»).

**Fuentes:**

- Li, Q.; Wang, P.; Li, Y.; et al. (2025a). Identifying trigger thresholds for heat damage at different growth stages of summer maize: A case study of the Huang-Huai-Hai Plain, China. European Journal of Agronomy 170, 127729. DOI 10.1016/j.eja.2025.127729  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\main.pdf`  
  Páginas: LiA-youden: p. PDF 8 / impresa 8; LiA-tabla1: p. PDF 3 / impresa 3; LiA-var: p. PDF 3 / impresa 3; LiA-3d: p. PDF 6 / impresa 6
- Li, Q.; et al. (2025b). Agronomy 15(7), 1545. DOI 10.3390/agronomy15071545  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-15-01545.pdf`  
  Páginas: LiB-dur: p. PDF 4 / impresa 4 of 17; LiB-tabla2: p. PDF 7 / impresa 7 of 17; LiB-sev-texto: p. PDF 7 / impresa 7 of 17; LiB-umbrales: p. PDF 4 / impresa 4 of 17; LiB-ref37: p. PDF 16 / impresa 16 of 17; LiB-ref9: p. PDF 15 / impresa 15 of 17

**Citas textuales:**

**[LiA-youden] umbral por subfase (Youden)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 8, p. impresa 8; §3.2.2 Optimal trigger threshold determined by ROC curve and Youden index.  
_Re-extraído ahora con PyMuPDF._

> The Youden index peaked at 34◦C, 34.1◦C, 34.6◦C, and 34.8◦C for the V0-VE, VE-V6, V6-VT, and VT-R1 growth stages (Fig. S4), respectively, under the test thresholds of 32–35◦C and 33.3–35.4◦C (Fig. 5a, b, d, e). Similarly, the Youden index reached its maximum at 33.7◦C for the R1-R3 stage and at 32.9◦C for the R3-R6 growth stage under the test thresholds of 32–35◦C and 31.7–33.8◦C, respectively (Fig. 5c, f). Therefore, the Td max values of 34, 34.1, 34.6, 34.8, 33.7, and 32.9℃ were considered the optimal trigger thresholds for determining whether heat damage occurs in summer maize at different growth stages from V0 to R6.

_Traducción (no es cita):_ El índice de Youden alcanzó su máximo en 34 °C, 34,1 °C, 34,6 °C y 34,8 °C para las etapas V0-VE, VE-V6, V6-VT y VT-R1 (Fig. S4), respectivamente, con umbrales de prueba de 32–35 °C y 33,3–35,4 °C (Fig. 5a, b, d, e). De forma similar, el índice de Youden alcanzó su máximo en 33,7 °C para la etapa R1-R3 y en 32,9 °C para la etapa R3-R6, con umbrales de prueba de 32–35 °C y 31,7–33,8 °C, respectivamente (Fig. 5c, f). Por lo tanto, los valores de Td max de 34; 34,1; 34,6; 34,8; 33,7 y 32,9 °C se consideraron los umbrales de disparo óptimos para determinar si ocurre daño por calor en el maíz de verano en las distintas etapas de V0 a R6.

**[LiA-tabla1] definición de subfases** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; Tabla 1 (Division of summer maize growth stage in HHH region) y §2.2.3.  
_Re-extraído ahora con PyMuPDF._

> Table 1 Division of summer maize growth stage in HHH region. Growth stage Description HD samples HD-free samples V0–VE Sowing to Seedling 1357 1477 VE–V6 Seedling to Jointing 2444 3106 V6–VT Jointing to Tasseling 2787 2515 VT–R1 Tasseling to Flowering 1561 1742 R1–R3 Flowering to Milk ripening 655 570 R3–R6 Milk ripening to physiological maturity 336 433

_Traducción (no es cita):_ Tabla 1. División de las etapas de crecimiento del maíz de verano en la región HHH. Etapa | Descripción | Muestras con daño | Muestras sin daño. V0–VE: siembra a plántula, 1357, 1477. VE–V6: plántula a encañado, 2444, 3106. V6–VT: encañado a panoja, 2787, 2515. VT–R1: panoja a floración, 1561, 1742. R1–R3: floración a grano lechoso, 655, 570. R3–R6: grano lechoso a madurez fisiológica, 336, 433.

**[LiA-var] variable (Tmax diaria)** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 3, p. impresa 3; §2.2.2 Meteorological data.  
_Re-extraído ahora con PyMuPDF._

> The daily maximum temperature (Td max) data for the summer maize growing season (June to September) were collected across the HHH Plain

_Traducción (no es cita):_ Los datos de temperatura máxima diaria (Td max) de la temporada del maíz de verano (junio a septiembre) se recolectaron en toda la llanura HHH

**[LiA-3d] duración observada en las muestras** — Li, Q.; Wang, P.; Li, Y.; et al.; p. PDF 6, p. impresa 6; §3.1 Characteristics of the HD dataset.  
_Re-extraído ahora con PyMuPDF._

> The majority of samples experienced HD lasting for ≥3 days, accounting for approximately 98.5 % of the total samples

_Traducción (no es cita):_ La mayoría de las muestras sufrió daño por calor que duró ≥3 días, alrededor del 98,5 % del total de muestras

**[LiB-dur] duración mínima de inclusión (≥2 d)** — Li, Q.; et al.; p. PDF 4, p. impresa 4 of 17; §2.3.2 K-Means Clustering Algorithm.  
_Re-extraído ahora con PyMuPDF._

> In this study, we focused on heat damage events lasting two days or more, which were temporally aggregated according to different growth stages (V0, VE, V6, VT, R1, R3, and R6).

_Traducción (no es cita):_ En este estudio nos centramos en eventos de daño por calor de dos días o más, que se agregaron en el tiempo según las distintas etapas de crecimiento (V0, VE, V6, VT, R1, R3 y R6).

**[LiB-tabla2] severidad por duración (tabla, decimales)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; Tabla 2 (The summer maize heat damage grade indicators).  
_Re-extraído ahora con PyMuPDF._

> Table 2. The summer maize heat damage grade indicators. The Growth Stages of Summer Maize Heat Damage Grade Indicators Mild/d Moderate/d Severe/d V0–VE 2.5~4.7 4.7~7.7 >7.7 VE–V6 3.7~5.9 5.9~8.6 >8.6 V6–VT 3.5~5.4 5.4~7.5 >7.5 VT–R1 2.3~4.5 4.5~7.9 >7.9 R1–R3 2.8~4.7 4.7~8.3 >8.3 R3–R6 3.2~5.3 5.3~8.1 >8.1

_Traducción (no es cita):_ Tabla 2. Indicadores de grado de daño por calor del maíz de verano. Etapa | Leve (d) | Moderado (d) | Severo (d): V0–VE 2,5~4,7 | 4,7~7,7 | >7,7; VE–V6 3,7~5,9 | 5,9~8,6 | >8,6; V6–VT 3,5~5,4 | 5,4~7,5 | >7,5; VT–R1 2,3~4,5 | 4,5~7,9 | >7,9; R1–R3 2,8~4,7 | 4,7~8,3 | >8,3; R3–R6 3,2~5,3 | 5,3~8,1 | >8,1.

**[LiB-sev-texto] severidad por duración (texto, días enteros)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; §3.1.1 Constructing Grade Indicators for Heat Damage.  
_Re-extraído ahora con PyMuPDF._

> The thresholds for these categories were determined as follows: 3–5 days for mild heat damage, 5–8 days for moderate heat damage, and more than 8 days for severe heat damage.

_Traducción (no es cita):_ Los umbrales de estas categorías se determinaron así: 3–5 días para daño leve, 5–8 días para daño moderado y más de 8 días para daño severo.

**[LiB-umbrales] umbrales citados (32,7 en R3–R6)** — Li, Q.; et al.; p. PDF 4, p. impresa 4 of 17; §2.3.1 Construction of Heat Damage Indicators for Different Grades.  
_Re-extraído ahora con PyMuPDF._

> Previous studies have identified different growth stages of summer maize and their corresponding heat stress thresholds: the sowing-to-emergence stage (early to mid-June), emergence-to-jointing stage (late June to mid-July), jointing-to-tasseling stage (mid to late July), tasseling-to-flowering stage (early August), flowering-to-milk-ripening stage (mid to late August), and milk-ripening-to-physiological-maturity stage (early to late September). The heat damage thresholds for these respective growth stages were determined as Td max ≥34 ◦C, 34.1 ◦C, 34.6 ◦C, 34.8 ◦C, 33.7 ◦C, and 32.7 ◦C [9,37].

_Traducción (no es cita):_ Estudios previos identificaron distintas etapas del maíz de verano y sus umbrales de estrés por calor: siembra a emergencia (inicios a mediados de junio), emergencia a encañado (finales de junio a mediados de julio), encañado a panoja (mediados a finales de julio), panoja a floración (inicios de agosto), floración a grano lechoso (mediados a finales de agosto) y grano lechoso a madurez fisiológica (inicios a finales de septiembre). Los umbrales de daño por calor para estas etapas se determinaron como Td max ≥ 34 °C; 34,1 °C; 34,6 °C; 34,8 °C; 33,7 °C y 32,7 °C [9,37].

**[LiB-ref37] procedencia del umbral (ref. 37 = Li 2025a)** — Li, Q.; et al.; p. PDF 16, p. impresa 16 of 17; References, ref. 37.  
_Re-extraído ahora con PyMuPDF._

> Li, Q.; Wang, P.; Li, Y.; Tang, J.; Li, X.; Zhang, Y.; Han, D.; Zhao, Y.; Wang, Q.; Yang, Z. Identifying trigger thresholds for heat damage at different growth stages of summer maize: A case study of the Huang-Huai-Hai Plain, China. Eur. J. Agron. 2025, 170, 127729.

_Traducción (no es cita):_ Referencia 37 de Li 2025b: es el artículo de Li 2025a (Eur. J. Agron. 170, 127729).

**[LiB-ref9] procedencia del umbral (ref. 9, no está en carpeta)** — Li, Q.; et al.; p. PDF 15, p. impresa 15 of 17; References, ref. 9.  
_Re-extraído ahora con PyMuPDF._

> Li, Q.; Wang, P.J.; Li, Y.; Tang, J.; Li, X.; Zhang, Y.; Han, D.; Wang, Q.; Zhao, Y.; Yang, Z. Hazard assessment of compound drought and heat events on summer maize from agricultural and meteorological perspectives. Agric. Water Manag. 2025, 313, 109479.

_Traducción (no es cita):_ Referencia 9 de Li 2025b: evaluación de amenaza de eventos compuestos de sequía y calor en maíz de verano (Agric. Water Manag. 313, 109479). No está en la carpeta.

**Valores en conflicto:** Li 2025b escribe 32,7 °C para R3–R6 y lo atribuye a [9,37]; [37] es Li 2025a, que publica 32,9 °C. Las citas de ambos textos están arriba: LiB-umbrales, LiA-youden, LiB-ref37, LiB-ref9.

## R07 — Maíz · Lluvia durante el secado · MAT

- **Fase homologada (tesis):** MAT (maíz: R6)
- **Etapa en la fuente:** Etapa «Dry» (secado) en la Tabla 2; después de R6 (madurez fisiológica, 112 días después de la siembra)
- **Cobertura:** La fuente cubre otra cosa: el secado en campo posterior a R6, en octubre–noviembre en el Bajo Balsas (México).
- **Umbral, variable y duración según la fuente:** Número de días con precipitación mayor que 10 mm (Tabla 2; el resumen dice «igual o mayor»). La fuente no define duración mínima ni racha.
- **Regla en el Excel:** P diaria > 10 mm; Conteo de días; la fuente no publica racha mínima; variable: Precipitación diaria (ERA5-Land, total_precipitation_sum)
- **Severidad:** No publicada
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Ortega Gómez, A. M.; Montiel González, C.; Gallegos Tavera, Á.; et al. (2019). Nova Scientia 11(22), 26–52. DOI 10.21640/ns.v11i22.1682  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\Ortega_2019.pdf`  
  Páginas: Ortega-tabla2: p. PDF 11 / impresa 36; Ortega-resumen: p. PDF 3 / impresa 28; Ortega-fases: p. PDF 10 / impresa 35

**Citas textuales:**

**[Ortega-tabla2] umbral diario y fase (Dry)** — Ortega Gómez, A. M.; Montiel González, C.; Gallegos Tavera, Á.; et al.; p. PDF 11, p. impresa 36; Tabla 2 (Description climatic hazard indicators for maize), indicadores 9–10.  
_Re-extraído ahora con PyMuPDF._

> WDH10oct Number of wet days with precipitation higher than 10 mm for the month of October. Dry 10 WDH10nov Number of wet days with precipitation higher than 10 mm in the month of November.

_Traducción (no es cita):_ WDH10oct: número de días húmedos con precipitación mayor que 10 mm en el mes de octubre. Secado (Dry). 10. WDH10nov: número de días húmedos con precipitación mayor que 10 mm en el mes de noviembre.

**[Ortega-resumen] mismo indicador en el resumen (usa «equal to or greater than»)** — Ortega Gómez, A. M.; Montiel González, C.; Gallegos Tavera, Á.; et al.; p. PDF 3, p. impresa 28; Abstract (inglés).  
_Re-extraído ahora con PyMuPDF._

> precipitation equal to or greater than 10 mm in October and November (WDH10oct, WDH10nov).

_Traducción (no es cita):_ precipitación igual o mayor que 10 mm en octubre y noviembre (WDH10oct, WDH10nov).

**[Ortega-fases] etapas del maíz en la fuente** — Ortega Gómez, A. M.; Montiel González, C.; Gallegos Tavera, Á.; et al.; p. PDF 10, p. impresa 35; Indicators of climatic hazard (Figura 2).  
_Re-extraído ahora con PyMuPDF._

> The maize growth stages are (Figure 2): 1) vegetative phase (the development of 20 to 21 leaves or VT-Vn), and 2) reproductive phase (the flowering or R0-R1, 54 days after emergence, and physiological maturity or R6, 112 days after planting).

_Traducción (no es cita):_ Las etapas del maíz son (Figura 2): 1) fase vegetativa (desarrollo de 20 a 21 hojas, VT-Vn) y 2) fase reproductiva (floración, R0-R1, 54 días después de la emergencia, y madurez fisiológica, R6, 112 días después de la siembra).

## R08 — Arroz · Calor · EST

- **Fase homologada (tesis):** EST (arroz: BBCH 00–09)
- **Etapa en la fuente:** «Seedling emergence and establishment» (Yoshida 1981, Tabla 2.4)
- **Cobertura:** Equivalente; «establishment» puede extenderse al inicio de VEG.
- **Umbral, variable y duración según la fuente:** Temperatura media diaria, valor «High» = 35 °C (celda de tabla, sin operador). La fuente no da duración.
- **Regla en el Excel:** Tmedia > 35 °C; La fuente no publica duración; variable: Tmedia diaria del aire a 2 m (ERA5-Land, temperature_2m)
- **Severidad:** No publicada
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Yoshida, S. (1981). Fundamentals of Rice Crop Science. IRRI, Los Baños. Libro, sin DOI  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\Yoshida_1981.pdf`  
  Páginas: Yoshida-tabla24: p. PDF 80 / impresa 72; Yoshida-alcance: p. PDF 80 / impresa 72

**Citas textuales:**

**[Yoshida-tabla24] umbral (columna High) y estadístico (nota b)** — Yoshida, S.; p. PDF 80, p. impresa 72; Tabla 2.4 (Response of the rice plant to varying temperatures at different growth stages) y notas a/b.  
_Re-extraído ahora con pdfplumber (tabla leída por filas)._

> Table 2.4. Response of the rice plant to varying temperatures at different growth stages. a Critical temperature b (°C) Growth stage Low High Optimum Germination 10 45 20–35 Seedling emergence and establishment 12–13 35 25–30 Rooting 16 35 25–28 Leaf elongation 7–12 45 31 Tillering 9–16 33 25–31 Initiation of panicle – – primordia 15 – Panicle differentiation 15–20 38 Anthesis 22 35 30–33 Ripening 12–18 30 20–25 a Adapted and modified from Yoshida (1977a). b Refers to daily mean temperature except for germination.

_Traducción (no es cita):_ Tabla 2.4. Respuesta de la planta de arroz a distintas temperaturas en distintas etapas de crecimiento (a). Temperatura crítica (b) (°C): Baja | Alta | Óptima. Germinación 10 | 45 | 20–35; emergencia de plántula y establecimiento 12–13 | 35 | 25–30; enraizamiento 16 | 35 | 25–28; elongación de hoja 7–12 | 45 | 31; macollamiento 9–16 | 33 | 25–31; iniciación de primordios de panícula 15 | – | –; diferenciación de panícula 15–20 | 38 | –; antesis 22 | 35 | 30–33; maduración (ripening) 12–18 | 30 | 20–25. (a) Adaptada y modificada de Yoshida (1977a). (b) Se refiere a la temperatura media diaria, excepto en germinación.

**[Yoshida-alcance] alcance del umbral** — Yoshida, S.; p. PDF 80, p. impresa 72; Texto que remite a la Tabla 2.4.  
_Re-extraído ahora con PyMuPDF._

> The critically low and high temperatures, normally below 20°C and above 30°C, vary from one growth stage to another (Table 2.4). These critical temperatures differ according to variety, duration of critical temperature, diurnal changes, and physiological status of the plant.

_Traducción (no es cita):_ Las temperaturas críticas bajas y altas, normalmente por debajo de 20 °C y por encima de 30 °C, varían de una etapa a otra (Tabla 2.4). Estas temperaturas críticas difieren según la variedad, la duración de la temperatura crítica, los cambios diurnos y el estado fisiológico de la planta.

## R09 — Arroz · Calor · VEG

- **Fase homologada (tesis):** VEG (arroz: BBCH 10–29)
- **Etapa en la fuente:** «tillering–jointing» (Jiang 2023)
- **Cobertura:** La fuente cubre más al final: incluye el encañado (BBCH 30–39), que en la tesis es REP-pre.
- **Umbral, variable y duración según la fuente:** Tmax diaria; umbral 36 °C. Duración: proceso con Tmax sobre el umbral «at least 3 days» (p. 7).
- **Regla en el Excel:** Tmax > 36 °C; Proceso ≥ 3 días consecutivos; variable: Tmax diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Jiang 2024 (macollamiento): leve 3–6 d; moderada 7–9 d; severa >9 d
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q. (2023). Characteristic Identification of Heat Exposure Based on Disaster Events for Single-Season Rice along the Middle and Lower Reaches of the Yangtze River, China. Agronomy 13(10), 2574. DOI 10.3390/agronomy13102574  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-13-02574.pdf`  
  Páginas: Jiang-resumen: p. PDF 1 / impresa 1 of 20; Jiang-roc: p. PDF 10 / impresa 10 of 20; Jiang-dur: p. PDF 7 / impresa 7 of 20; Jiang-p2: p. PDF 2 / impresa 2 of 20; Jiang-fases: p. PDF 5 / impresa 5 of 20
- Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R. (2024). Dynamic Evaluation and Risk Projection of Heat Exposure Based on Disaster Events for Single-Season Rice along the Middle and Lower Reaches of the Yangtze River, China. Agronomy 14, 1737. DOI 10.3390/agronomy14081737 (acceso abierto)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Jiang_2024_Agronomy_14_1737.pdf`  
  Páginas: Jiang24-umbral: p. PDF 5 / impresa 5 of 21; Jiang24-sev: p. PDF 10 / impresa 10 of 21

**Citas textuales:**

**[Jiang-resumen] umbral Tmax por etapa** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 1, p. impresa 1 of 20; Abstract.  
_Re-extraído ahora con PyMuPDF._

> Critical temperature thresholds of Tmax at tillering–jointing, booting, flowering and filling were quantified as 36, 35, 35 and 38 ◦C, with higher IF values of 13.14, 10.93, 17.15 and 13.15, respectively.

_Traducción (no es cita):_ Los umbrales críticos de Tmax en macollamiento–encañado, embuche, floración y llenado se cuantificaron en 36, 35, 35 y 38 °C, con valores de IF más altos de 13,14; 10,93; 17,15 y 13,15, respectivamente.

**[Jiang-roc] umbral Tmax por etapa (ROC sobre registros de desastre)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 10, p. impresa 10 of 20; §3.2 (ROC, Figura 5).  
_Re-extraído ahora con PyMuPDF._

> The ROC curves for each phenological stage were drawn in Figure 5, illustrating a trade‑off between achieving a high true‑positive rate and a low false‑positive rate. Each test point on the ROC plot referred to a sensitivity‑specificity pair corresponding to a par‑ ticular decision threshold. AUC values were obtained from TPRs and FPRs at each test point, reaching 0.993 at tillering–jointing, 0.959 at booting, 0.989 at flowering, and 0.930 at filling, corresponding to ‘excellent’ performances of Tmax as the trigger factor to discrimi‑ nate whether heat occurred or no heat. Measured comprehensively by the method above, the Tmax values of 36, 35, 35. and 38 ◦C were sequentially confirmed as the optimal critical threshold for identifying the occurrence of heat exposure to single‑season rice in MLRYR as the phenological stage advanced.

_Traducción (no es cita):_ Las curvas ROC de cada etapa se dibujaron en la Figura 5 y muestran el compromiso entre una alta tasa de verdaderos positivos y una baja tasa de falsos positivos. Cada punto de prueba corresponde a un par sensibilidad-especificidad para un umbral de decisión. Los valores de AUC fueron 0,993 en macollamiento–encañado, 0,959 en embuche, 0,989 en floración y 0,930 en llenado, un desempeño «excelente» de Tmax como factor de disparo para discriminar si hubo o no calor. Medidos de forma integral con este método, los valores de Tmax de 36, 35, 35 y 38 °C se confirmaron sucesivamente como el umbral crítico óptimo para identificar la exposición al calor del arroz de una cosecha en la cuenca media-baja del Yangtsé, a medida que avanza la etapa.

**[Jiang-dur] duración (proceso ≥3 d)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 7, p. impresa 7 of 20; §2.5.2.  
_Re-extraído ahora con PyMuPDF._

> Generally speaking, most domestic studies consider a heat process where the maximum air temper‑ ature exceeds the critical threshold for at least 3 days.

_Traducción (no es cita):_ En general, la mayoría de los estudios nacionales considera un proceso de calor aquel en que la temperatura máxima del aire supera el umbral crítico durante al menos 3 días.

**[Jiang24-umbral] umbrales por etapa (heredados de Jiang 2023) y racha ≥3 d** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 5, p. impresa 5 of 21; §2.3.1.  
_Re-extraído ahora con PyMuPDF._

> The various thresh-olds of heat occurrence were set to 36 ◦C at tillering, 35 ◦C at booting, 35 ◦C at flowering, and 38 ◦C at filling in this study. A detailed description of the determination of the four growth stages mentioned above as crucial phenology phases for heat exposure can be found in M. Jiang [51]. Among all recorded historical disasters, rice heat samples of hot weather processes with continuous days ≥3 d were counted by the given critical threshold and di-vided into the corresponding growth stages.

_Traducción (no es cita):_ Los distintos umbrales de ocurrencia de calor se fijaron en 36 °C en macollamiento, 35 °C en embuche, 35 °C en floración y 38 °C en llenado en este estudio. La descripción de cómo se determinaron estas cuatro etapas fenológicas cruciales para la exposición al calor está en M. Jiang [51]. Entre todos los desastres históricos registrados, las muestras de calor con procesos de tiempo caluroso de ≥3 días continuos se contaron con el umbral crítico dado y se dividieron en las etapas correspondientes.

**[Jiang24-sev] severidad por duración** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 10, p. impresa 10 of 21; §3.2.2.  
_Re-extraído ahora con PyMuPDF._

> Not only at booting did hot weather persist for 3~5 d and 6~8 d induced mild and moderate rice heat, but also at flowering. There were slight extensions for heat durations at tillering and filling, with the 3~6 d and 7~9 d heat duration probably emerging as mild and moderate heat damage, respectively. Furthermore, heat durations of severe disasters at different growth stages for single-season rice mostly exceeded 9 d.

_Traducción (no es cita):_ No solo en embuche, sino también en floración, el tiempo caluroso que persistió 3~5 d y 6~8 d indujo calor leve y moderado en el arroz. En macollamiento y llenado las duraciones se extendieron levemente: 3~6 d y 7~9 d probablemente corresponden a daño leve y moderado, respectivamente. Además, la duración de los desastres severos en las distintas etapas del arroz de una cosecha superó en su mayoría los 9 d.

**[Jiang-p2] convención de duración citada (más de 3 días consecutivos)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 2, p. impresa 2 of 20; Introduction.  
_Re-extraído ahora con PyMuPDF._

> It is widely accepted that the heat stress process is defined according to the threshold of average temperature (Tave) at 30 ◦C or maximum temperature (Tmax) at 35 ◦C for more than 3 consecutive days throughout the reproductive phase [5,9,14,24,25].

_Traducción (no es cita):_ Es ampliamente aceptado que el proceso de estrés por calor se define según el umbral de temperatura media (Tave) de 30 °C o de temperatura máxima (Tmax) de 35 °C durante más de 3 días consecutivos a lo largo de la fase reproductiva [5,9,14,24,25].

**[Jiang-fases] etapas estudiadas** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 5, p. impresa 5 of 20; §2.3.1 Target Phenological Stages of Rice Heat Stress.  
_Re-extraído ahora con PyMuPDF._

> Furthermore, regardless of the rice characteristics and climate warming trends, the investigated phenological stages focused on the tillering–jointing, booting, flowering and filling stages, broadly grouped into one vegetative and three reproductive stages.

_Traducción (no es cita):_ Además, sin importar las características del arroz ni las tendencias de calentamiento, las etapas fenológicas estudiadas se centraron en macollamiento–encañado, embuche, floración y llenado, agrupadas en una etapa vegetativa y tres reproductivas.

**Valores en conflicto:** Jiang 2023 da dos formulaciones de la duración: «more than 3 consecutive days» (p. 2, convención citada para Tave 30 °C o Tmax 35 °C) y «at least 3 days» (p. 7, definición de proceso que usa el método). Más de 3 = 4 días o más; al menos 3 = 3 días o más. Las citas de ambos textos están arriba: Jiang-p2, Jiang-dur.

## R10 — Arroz · Calor · REP-pre

- **Fase homologada (tesis):** REP-pre (arroz: BBCH 30–59)
- **Etapa en la fuente:** «booting» (Jiang 2023); «jointing–booting (#1)» (Sun 2025)
- **Cobertura:** Jiang cubre menos: solo el embuche (BBCH 40–49), no la iniciación de panícula ni el espigado. Sun #1 va del encañado al día antes del espigado (≈ BBCH 30–49).
- **Umbral, variable y duración según la fuente:** Jiang: Tmax diaria, 35 °C; duración «at least 3 days» (p. 7) o «more than 3 consecutive days» (p. 2, convención citada). Sun: Tmedia ≥ 33 °C, ≥ 1 día.
- **Regla en el Excel:** Tmax > 35 °C; ≥ 3 días consecutivos con Tmax sobre el umbral (Jiang 2023, p. 7 §2.5.2: «exceeds the critical threshold for at least 3 days»); variable: Tmax diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Jiang 2024: leve 3~5 d; moderada 6~8 d; severa > 8 d
- **Estado:** Propuesta — decide Paola. Validación Paola: Aprobada: Jiang 2023 (Tmax 35/35/38 °C, más de 3 días consecutivos según la convención citada en Jiang 2023 p. 2). Se descartan los grados de Jiang 2024 porque su duración cuenta días con HCIId > 0, no días con Tmax sobre el umbral. (Decisión de Paola, 4 nov 2026.) | 5 nov 2026: Paola registra la duración como ≥ 3 días con la cita de la p. 7 (método); la p. 2 («more than 3 consecutive days», convención citada) queda como valor en conflicto.

**Fuentes:**

- Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q. (2023). Characteristic Identification of Heat Exposure Based on Disaster Events for Single-Season Rice along the Middle and Lower Reaches of the Yangtze River, China. Agronomy 13(10), 2574. DOI 10.3390/agronomy13102574  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-13-02574.pdf`  
  Páginas: Jiang-resumen: p. PDF 1 / impresa 1 of 20; Jiang-roc: p. PDF 10 / impresa 10 of 20; Jiang-dur: p. PDF 7 / impresa 7 of 20; Jiang-p2: p. PDF 2 / impresa 2 of 20; Jiang-fases: p. PDF 5 / impresa 5 of 20
- Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R. (2024). Dynamic Evaluation and Risk Projection of Heat Exposure Based on Disaster Events for Single-Season Rice along the Middle and Lower Reaches of the Yangtze River, China. Agronomy 14, 1737. DOI 10.3390/agronomy14081737 (acceso abierto)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Jiang_2024_Agronomy_14_1737.pdf`  
  Páginas: Jiang24-umbral: p. PDF 5 / impresa 5 of 21; Jiang24-sev: p. PDF 10 / impresa 10 of 21; Jiang24-flo: p. PDF 10 / impresa 10 of 21; Jiang24-hcii: p. PDF 6 / impresa 6 of 21
- Sun, R.; et al. (2025). Spatiotemporal variation of growth-stage specific concurrent climate extremes (arroz). Earth System Dynamics 16, 1971–1988. DOI 10.5194/esd-16-1971-2025  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\esd-16-1971-2025.pdf`  
  Páginas: Sun-fases: p. PDF 4 / impresa 1974; Sun-var: p. PDF 4 / impresa 1974; Sun-tabla1: p. PDF 5 / impresa 1975

**Citas textuales:**

**[Jiang-resumen] umbral Tmax por etapa** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 1, p. impresa 1 of 20; Abstract.  
_Re-extraído ahora con PyMuPDF._

> Critical temperature thresholds of Tmax at tillering–jointing, booting, flowering and filling were quantified as 36, 35, 35 and 38 ◦C, with higher IF values of 13.14, 10.93, 17.15 and 13.15, respectively.

_Traducción (no es cita):_ Los umbrales críticos de Tmax en macollamiento–encañado, embuche, floración y llenado se cuantificaron en 36, 35, 35 y 38 °C, con valores de IF más altos de 13,14; 10,93; 17,15 y 13,15, respectivamente.

**[Jiang-roc] umbral Tmax por etapa (ROC sobre registros de desastre)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 10, p. impresa 10 of 20; §3.2 (ROC, Figura 5).  
_Re-extraído ahora con PyMuPDF._

> The ROC curves for each phenological stage were drawn in Figure 5, illustrating a trade‑off between achieving a high true‑positive rate and a low false‑positive rate. Each test point on the ROC plot referred to a sensitivity‑specificity pair corresponding to a par‑ ticular decision threshold. AUC values were obtained from TPRs and FPRs at each test point, reaching 0.993 at tillering–jointing, 0.959 at booting, 0.989 at flowering, and 0.930 at filling, corresponding to ‘excellent’ performances of Tmax as the trigger factor to discrimi‑ nate whether heat occurred or no heat. Measured comprehensively by the method above, the Tmax values of 36, 35, 35. and 38 ◦C were sequentially confirmed as the optimal critical threshold for identifying the occurrence of heat exposure to single‑season rice in MLRYR as the phenological stage advanced.

_Traducción (no es cita):_ Las curvas ROC de cada etapa se dibujaron en la Figura 5 y muestran el compromiso entre una alta tasa de verdaderos positivos y una baja tasa de falsos positivos. Cada punto de prueba corresponde a un par sensibilidad-especificidad para un umbral de decisión. Los valores de AUC fueron 0,993 en macollamiento–encañado, 0,959 en embuche, 0,989 en floración y 0,930 en llenado, un desempeño «excelente» de Tmax como factor de disparo para discriminar si hubo o no calor. Medidos de forma integral con este método, los valores de Tmax de 36, 35, 35 y 38 °C se confirmaron sucesivamente como el umbral crítico óptimo para identificar la exposición al calor del arroz de una cosecha en la cuenca media-baja del Yangtsé, a medida que avanza la etapa.

**[Jiang-dur] duración (proceso ≥3 d)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 7, p. impresa 7 of 20; §2.5.2.  
_Re-extraído ahora con PyMuPDF._

> Generally speaking, most domestic studies consider a heat process where the maximum air temper‑ ature exceeds the critical threshold for at least 3 days.

_Traducción (no es cita):_ En general, la mayoría de los estudios nacionales considera un proceso de calor aquel en que la temperatura máxima del aire supera el umbral crítico durante al menos 3 días.

**[Jiang24-umbral] umbrales por etapa (heredados de Jiang 2023) y racha ≥3 d** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 5, p. impresa 5 of 21; §2.3.1.  
_Re-extraído ahora con PyMuPDF._

> The various thresh-olds of heat occurrence were set to 36 ◦C at tillering, 35 ◦C at booting, 35 ◦C at flowering, and 38 ◦C at filling in this study. A detailed description of the determination of the four growth stages mentioned above as crucial phenology phases for heat exposure can be found in M. Jiang [51]. Among all recorded historical disasters, rice heat samples of hot weather processes with continuous days ≥3 d were counted by the given critical threshold and di-vided into the corresponding growth stages.

_Traducción (no es cita):_ Los distintos umbrales de ocurrencia de calor se fijaron en 36 °C en macollamiento, 35 °C en embuche, 35 °C en floración y 38 °C en llenado en este estudio. La descripción de cómo se determinaron estas cuatro etapas fenológicas cruciales para la exposición al calor está en M. Jiang [51]. Entre todos los desastres históricos registrados, las muestras de calor con procesos de tiempo caluroso de ≥3 días continuos se contaron con el umbral crítico dado y se dividieron en las etapas correspondientes.

**[Jiang24-sev] severidad por duración** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 10, p. impresa 10 of 21; §3.2.2.  
_Re-extraído ahora con PyMuPDF._

> Not only at booting did hot weather persist for 3~5 d and 6~8 d induced mild and moderate rice heat, but also at flowering. There were slight extensions for heat durations at tillering and filling, with the 3~6 d and 7~9 d heat duration probably emerging as mild and moderate heat damage, respectively. Furthermore, heat durations of severe disasters at different growth stages for single-season rice mostly exceeded 9 d.

_Traducción (no es cita):_ No solo en embuche, sino también en floración, el tiempo caluroso que persistió 3~5 d y 6~8 d indujo calor leve y moderado en el arroz. En macollamiento y llenado las duraciones se extendieron levemente: 3~6 d y 7~9 d probablemente corresponden a daño leve y moderado, respectivamente. Además, la duración de los desastres severos en las distintas etapas del arroz de una cosecha superó en su mayoría los 9 d.

**[Jiang24-flo] severidad por duración en floración (ejemplo de los autores)** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 10, p. impresa 10 of 21; §3.2.2.  
_Re-extraído ahora con PyMuPDF._

> Taking the flowering stage as an example, rice was subjected to hot weather for 3~5 d (mild), 6~8 d (moderate) and > 8 d (severe) as the classification thresholds, and the accuracy of recognizing samples with different heat levels was approximately 77.9%.

_Traducción (no es cita):_ Tomando la floración como ejemplo, el arroz sometido a tiempo caluroso durante 3~5 d (leve), 6~8 d (moderado) y > 8 d (severo) como umbrales de clasificación, la precisión para reconocer muestras con distintos niveles de calor fue de aproximadamente 77,9 %.

**[Sun-fases] definición de etapas #1–#3** — Sun, R.; et al.; p. PDF 4, p. impresa 1974; §2.3.1.  
_Re-extraído ahora con PyMuPDF._

> Three growth stages that were most susceptible to extreme stress were considered in this study: jointing–booting stage (#1), heading–flowering stage (#2) and grain filling stage (#3). The jointing–booting stage refers to the period from the first day of jointing to the last day before heading. The heading–flowering stage refers to the period from heading to flowering and generally lasts for 10 d. The grain filling stage refers to the period from the 11th day after heading to ma-turity. The exact dates of the different stages were obtained from phenological records for each year and station.

_Traducción (no es cita):_ En este estudio se consideraron las tres etapas más susceptibles al estrés extremo: encañado–embuche (#1), espigado–floración (#2) y llenado (#3). Encañado–embuche va del primer día de encañado al último día antes del espigado. Espigado–floración va del espigado a la floración y suele durar 10 d. Llenado va del día 11 después del espigado hasta la madurez. Las fechas exactas se tomaron de registros fenológicos de cada año y estación.

**[Sun-var] variable (Tmedia) y corte 33 °C** — Sun, R.; et al.; p. PDF 4, p. impresa 1974; §2.3.2.  
_Re-extraído ahora con PyMuPDF._

> Following this concept, heat stress (H) sever-ity SH,g,t at a given growth stage (g) in a given year (t) that meets the condition can be computed by the cumulative de-viation of mean daily temperature (T ) above its threshold (Tbase) for all the days (i) within this stage. We used 33 °C as the base temperature (Table 1) in Eq. (1).

_Traducción (no es cita):_ Siguiendo este concepto, la severidad del estrés por calor (H) SH,g,t en una etapa (g) de un año (t) que cumple la condición se calcula como la desviación acumulada de la temperatura media diaria (T) por encima de su umbral (Tbase) en todos los días (i) de la etapa. Usamos 33 °C como temperatura base (Tabla 1) en la Ec. (1).

**[Sun-tabla1] umbral, duración y procedencia (normas NY/T)** — Sun, R.; et al.; p. PDF 5, p. impresa 1975; Tabla 1 (The thresholds of each individual extreme event) y nota.  
_Re-extraído ahora con PyMuPDF._

> Table 1. The thresholds of each individual extreme event. Rice type Growth stage Climate Indicator & threshold: daily mean temperature (T / °C), extremes daily total precipitation (PRE / mm), relative soil moisture (SM / %) Single–rice Jointing–booting (#1) Heat T ≥33 °C ≥1 successive day Heading–flowering (#2) Drought SM ≤75 % ≥10 successive days Grain filling (#3) Late–rice Heading–flowering (#2) Chilling T ≤20 °C ≥1 successive day Rain P ≥25 mm ≥1 successive day Grain filling (#3) Chilling T ≤17 °C ≥1 successive day Rain P ≥25 mm ≥1 successive day Note: The above thresholds are referenced from <NY/T 2915–2016>, Identification and classification of heat injury of rice; <NY/T 3043–2016>, Code of practice for field investigations and classification of rice seasonal drought stressess in southern–China; <NY/T 2285–2012>, Technical specification of field investigations and the grading of chilling damage to rice and; <DB5101/T 125–2021>, Indica rice weather stress level–continuous rain. NY/T is the Agricultural Information Resource Classification and Coding Specification in China. DB5101/T is the Local Standard of Chengdu, Sichuan Province. Thresholds for duration were relaxed from original standards to ensure adequate samples for later analyses.

_Traducción (no es cita):_ Tabla 1. Umbrales de cada evento extremo individual. Tipo de arroz | Etapa | Extremo | Indicador y umbral: temperatura media diaria (T, °C), precipitación diaria total (PRE, mm), humedad relativa del suelo (SM, %). Arroz de una cosecha: encañado–embuche (#1), espigado–floración (#2), llenado (#3): calor T ≥ 33 °C ≥ 1 día sucesivo; sequía SM ≤ 75 % ≥ 10 días sucesivos. Arroz tardío: espigado–floración (#2): frío T ≤ 20 °C ≥ 1 día; lluvia P ≥ 25 mm ≥ 1 día; llenado (#3): frío T ≤ 17 °C ≥ 1 día; lluvia P ≥ 25 mm ≥ 1 día. Nota: los umbrales provienen de NY/T 2915–2016 (identificación y clasificación del daño por calor en arroz), NY/T 3043–2016, NY/T 2285–2012 y DB5101/T 125–2021. Los umbrales de duración se relajaron respecto a las normas originales para tener muestras suficientes en los análisis.

**[Jiang-p2] convención de duración citada (más de 3 días consecutivos)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 2, p. impresa 2 of 20; Introduction.  
_Re-extraído ahora con PyMuPDF._

> It is widely accepted that the heat stress process is defined according to the threshold of average temperature (Tave) at 30 ◦C or maximum temperature (Tmax) at 35 ◦C for more than 3 consecutive days throughout the reproductive phase [5,9,14,24,25].

_Traducción (no es cita):_ Es ampliamente aceptado que el proceso de estrés por calor se define según el umbral de temperatura media (Tave) de 30 °C o de temperatura máxima (Tmax) de 35 °C durante más de 3 días consecutivos a lo largo de la fase reproductiva [5,9,14,24,25].

**[Jiang-fases] etapas estudiadas** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 5, p. impresa 5 of 20; §2.3.1 Target Phenological Stages of Rice Heat Stress.  
_Re-extraído ahora con PyMuPDF._

> Furthermore, regardless of the rice characteristics and climate warming trends, the investigated phenological stages focused on the tillering–jointing, booting, flowering and filling stages, broadly grouped into one vegetative and three reproductive stages.

_Traducción (no es cita):_ Además, sin importar las características del arroz ni las tendencias de calentamiento, las etapas fenológicas estudiadas se centraron en macollamiento–encañado, embuche, floración y llenado, agrupadas en una etapa vegetativa y tres reproductivas.

**[Jiang24-hcii] la duración de los grados se cuenta con HCIId > 0** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 6, p. impresa 6 of 21; §2.3.2.  
_Re-extraído ahora con PyMuPDF._

> HCIId = 0 is determined as the critical value of disaster-causing. HCIId ≤0 is identified as a non-disaster, while HCIId > 0 is identified as a disaster. Then, we focused on the duration (HCIId > 0) subjected to heat disaster processes and HCIId accumulation during the duration, two important components to reveal the heat disaster level within hot weather events.

_Traducción (no es cita):_ HCIId = 0 se determina como el valor crítico de causa de desastre. HCIId ≤ 0 se identifica como no desastre y HCIId > 0 como desastre. Luego nos centramos en la duración (HCIId > 0) de los procesos de desastre por calor y en la acumulación de HCIId durante esa duración, dos componentes importantes para revelar el nivel del desastre dentro de los eventos de tiempo caluroso.

**Valores en conflicto:** Jiang 2023 da dos formulaciones de la duración: «more than 3 consecutive days» (p. 2, convención citada para Tave 30 °C o Tmax 35 °C) y «at least 3 days» (p. 7, definición de proceso que usa el método). Más de 3 = 4 días o más; al menos 3 = 3 días o más. Las citas de ambos textos están arriba: Jiang-p2, Jiang-dur.

## R11 — Arroz · Calor · FLO

- **Fase homologada (tesis):** FLO (arroz: BBCH 60–69)
- **Etapa en la fuente:** «flowering» (Jiang 2023); «heading–flowering (#2)» (Sun 2025)
- **Cobertura:** Jiang ≈ equivalente. Sun #2 cubre más: incluye el espigado (BBCH 50–59, REP-pre) y dura unos 10 d.
- **Umbral, variable y duración según la fuente:** Jiang: Tmax diaria, 35 °C; duración como R10. Sun: Tmedia ≥ 33 °C, ≥ 1 día.
- **Regla en el Excel:** Tmax > 35 °C; ≥ 3 días consecutivos con Tmax sobre el umbral (Jiang 2023, p. 7 §2.5.2: «exceeds the critical threshold for at least 3 days»); variable: Tmax diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Jiang 2024: leve 3~5 d; moderada 6~8 d; severa > 8 d
- **Estado:** Propuesta — decide Paola. Validación Paola: Aprobada: Jiang 2023 (Tmax 35/35/38 °C, más de 3 días consecutivos según la convención citada en Jiang 2023 p. 2). Se descartan los grados de Jiang 2024 porque su duración cuenta días con HCIId > 0, no días con Tmax sobre el umbral. (Decisión de Paola, 4 nov 2026.) | 5 nov 2026: Paola registra la duración como ≥ 3 días con la cita de la p. 7 (método); la p. 2 («more than 3 consecutive days», convención citada) queda como valor en conflicto.

**Fuentes:**

- Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q. (2023). Characteristic Identification of Heat Exposure Based on Disaster Events for Single-Season Rice along the Middle and Lower Reaches of the Yangtze River, China. Agronomy 13(10), 2574. DOI 10.3390/agronomy13102574  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-13-02574.pdf`  
  Páginas: Jiang-resumen: p. PDF 1 / impresa 1 of 20; Jiang-roc: p. PDF 10 / impresa 10 of 20; Jiang-dur: p. PDF 7 / impresa 7 of 20; Jiang-p2: p. PDF 2 / impresa 2 of 20; Jiang-fases: p. PDF 5 / impresa 5 of 20
- Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R. (2024). Dynamic Evaluation and Risk Projection of Heat Exposure Based on Disaster Events for Single-Season Rice along the Middle and Lower Reaches of the Yangtze River, China. Agronomy 14, 1737. DOI 10.3390/agronomy14081737 (acceso abierto)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Jiang_2024_Agronomy_14_1737.pdf`  
  Páginas: Jiang24-umbral: p. PDF 5 / impresa 5 of 21; Jiang24-sev: p. PDF 10 / impresa 10 of 21; Jiang24-flo: p. PDF 10 / impresa 10 of 21; Jiang24-hcii: p. PDF 6 / impresa 6 of 21
- Sun, R.; et al. (2025). Spatiotemporal variation of growth-stage specific concurrent climate extremes (arroz). Earth System Dynamics 16, 1971–1988. DOI 10.5194/esd-16-1971-2025  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\esd-16-1971-2025.pdf`  
  Páginas: Sun-fases: p. PDF 4 / impresa 1974; Sun-var: p. PDF 4 / impresa 1974; Sun-tabla1: p. PDF 5 / impresa 1975

**Citas textuales:**

**[Jiang-resumen] umbral Tmax por etapa** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 1, p. impresa 1 of 20; Abstract.  
_Re-extraído ahora con PyMuPDF._

> Critical temperature thresholds of Tmax at tillering–jointing, booting, flowering and filling were quantified as 36, 35, 35 and 38 ◦C, with higher IF values of 13.14, 10.93, 17.15 and 13.15, respectively.

_Traducción (no es cita):_ Los umbrales críticos de Tmax en macollamiento–encañado, embuche, floración y llenado se cuantificaron en 36, 35, 35 y 38 °C, con valores de IF más altos de 13,14; 10,93; 17,15 y 13,15, respectivamente.

**[Jiang-roc] umbral Tmax por etapa (ROC sobre registros de desastre)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 10, p. impresa 10 of 20; §3.2 (ROC, Figura 5).  
_Re-extraído ahora con PyMuPDF._

> The ROC curves for each phenological stage were drawn in Figure 5, illustrating a trade‑off between achieving a high true‑positive rate and a low false‑positive rate. Each test point on the ROC plot referred to a sensitivity‑specificity pair corresponding to a par‑ ticular decision threshold. AUC values were obtained from TPRs and FPRs at each test point, reaching 0.993 at tillering–jointing, 0.959 at booting, 0.989 at flowering, and 0.930 at filling, corresponding to ‘excellent’ performances of Tmax as the trigger factor to discrimi‑ nate whether heat occurred or no heat. Measured comprehensively by the method above, the Tmax values of 36, 35, 35. and 38 ◦C were sequentially confirmed as the optimal critical threshold for identifying the occurrence of heat exposure to single‑season rice in MLRYR as the phenological stage advanced.

_Traducción (no es cita):_ Las curvas ROC de cada etapa se dibujaron en la Figura 5 y muestran el compromiso entre una alta tasa de verdaderos positivos y una baja tasa de falsos positivos. Cada punto de prueba corresponde a un par sensibilidad-especificidad para un umbral de decisión. Los valores de AUC fueron 0,993 en macollamiento–encañado, 0,959 en embuche, 0,989 en floración y 0,930 en llenado, un desempeño «excelente» de Tmax como factor de disparo para discriminar si hubo o no calor. Medidos de forma integral con este método, los valores de Tmax de 36, 35, 35 y 38 °C se confirmaron sucesivamente como el umbral crítico óptimo para identificar la exposición al calor del arroz de una cosecha en la cuenca media-baja del Yangtsé, a medida que avanza la etapa.

**[Jiang-dur] duración (proceso ≥3 d)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 7, p. impresa 7 of 20; §2.5.2.  
_Re-extraído ahora con PyMuPDF._

> Generally speaking, most domestic studies consider a heat process where the maximum air temper‑ ature exceeds the critical threshold for at least 3 days.

_Traducción (no es cita):_ En general, la mayoría de los estudios nacionales considera un proceso de calor aquel en que la temperatura máxima del aire supera el umbral crítico durante al menos 3 días.

**[Jiang24-umbral] umbrales por etapa (heredados de Jiang 2023) y racha ≥3 d** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 5, p. impresa 5 of 21; §2.3.1.  
_Re-extraído ahora con PyMuPDF._

> The various thresh-olds of heat occurrence were set to 36 ◦C at tillering, 35 ◦C at booting, 35 ◦C at flowering, and 38 ◦C at filling in this study. A detailed description of the determination of the four growth stages mentioned above as crucial phenology phases for heat exposure can be found in M. Jiang [51]. Among all recorded historical disasters, rice heat samples of hot weather processes with continuous days ≥3 d were counted by the given critical threshold and di-vided into the corresponding growth stages.

_Traducción (no es cita):_ Los distintos umbrales de ocurrencia de calor se fijaron en 36 °C en macollamiento, 35 °C en embuche, 35 °C en floración y 38 °C en llenado en este estudio. La descripción de cómo se determinaron estas cuatro etapas fenológicas cruciales para la exposición al calor está en M. Jiang [51]. Entre todos los desastres históricos registrados, las muestras de calor con procesos de tiempo caluroso de ≥3 días continuos se contaron con el umbral crítico dado y se dividieron en las etapas correspondientes.

**[Jiang24-sev] severidad por duración** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 10, p. impresa 10 of 21; §3.2.2.  
_Re-extraído ahora con PyMuPDF._

> Not only at booting did hot weather persist for 3~5 d and 6~8 d induced mild and moderate rice heat, but also at flowering. There were slight extensions for heat durations at tillering and filling, with the 3~6 d and 7~9 d heat duration probably emerging as mild and moderate heat damage, respectively. Furthermore, heat durations of severe disasters at different growth stages for single-season rice mostly exceeded 9 d.

_Traducción (no es cita):_ No solo en embuche, sino también en floración, el tiempo caluroso que persistió 3~5 d y 6~8 d indujo calor leve y moderado en el arroz. En macollamiento y llenado las duraciones se extendieron levemente: 3~6 d y 7~9 d probablemente corresponden a daño leve y moderado, respectivamente. Además, la duración de los desastres severos en las distintas etapas del arroz de una cosecha superó en su mayoría los 9 d.

**[Jiang24-flo] severidad por duración en floración (ejemplo de los autores)** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 10, p. impresa 10 of 21; §3.2.2.  
_Re-extraído ahora con PyMuPDF._

> Taking the flowering stage as an example, rice was subjected to hot weather for 3~5 d (mild), 6~8 d (moderate) and > 8 d (severe) as the classification thresholds, and the accuracy of recognizing samples with different heat levels was approximately 77.9%.

_Traducción (no es cita):_ Tomando la floración como ejemplo, el arroz sometido a tiempo caluroso durante 3~5 d (leve), 6~8 d (moderado) y > 8 d (severo) como umbrales de clasificación, la precisión para reconocer muestras con distintos niveles de calor fue de aproximadamente 77,9 %.

**[Sun-fases] definición de etapas #1–#3** — Sun, R.; et al.; p. PDF 4, p. impresa 1974; §2.3.1.  
_Re-extraído ahora con PyMuPDF._

> Three growth stages that were most susceptible to extreme stress were considered in this study: jointing–booting stage (#1), heading–flowering stage (#2) and grain filling stage (#3). The jointing–booting stage refers to the period from the first day of jointing to the last day before heading. The heading–flowering stage refers to the period from heading to flowering and generally lasts for 10 d. The grain filling stage refers to the period from the 11th day after heading to ma-turity. The exact dates of the different stages were obtained from phenological records for each year and station.

_Traducción (no es cita):_ En este estudio se consideraron las tres etapas más susceptibles al estrés extremo: encañado–embuche (#1), espigado–floración (#2) y llenado (#3). Encañado–embuche va del primer día de encañado al último día antes del espigado. Espigado–floración va del espigado a la floración y suele durar 10 d. Llenado va del día 11 después del espigado hasta la madurez. Las fechas exactas se tomaron de registros fenológicos de cada año y estación.

**[Sun-var] variable (Tmedia) y corte 33 °C** — Sun, R.; et al.; p. PDF 4, p. impresa 1974; §2.3.2.  
_Re-extraído ahora con PyMuPDF._

> Following this concept, heat stress (H) sever-ity SH,g,t at a given growth stage (g) in a given year (t) that meets the condition can be computed by the cumulative de-viation of mean daily temperature (T ) above its threshold (Tbase) for all the days (i) within this stage. We used 33 °C as the base temperature (Table 1) in Eq. (1).

_Traducción (no es cita):_ Siguiendo este concepto, la severidad del estrés por calor (H) SH,g,t en una etapa (g) de un año (t) que cumple la condición se calcula como la desviación acumulada de la temperatura media diaria (T) por encima de su umbral (Tbase) en todos los días (i) de la etapa. Usamos 33 °C como temperatura base (Tabla 1) en la Ec. (1).

**[Sun-tabla1] umbral, duración y procedencia (normas NY/T)** — Sun, R.; et al.; p. PDF 5, p. impresa 1975; Tabla 1 (The thresholds of each individual extreme event) y nota.  
_Re-extraído ahora con PyMuPDF._

> Table 1. The thresholds of each individual extreme event. Rice type Growth stage Climate Indicator & threshold: daily mean temperature (T / °C), extremes daily total precipitation (PRE / mm), relative soil moisture (SM / %) Single–rice Jointing–booting (#1) Heat T ≥33 °C ≥1 successive day Heading–flowering (#2) Drought SM ≤75 % ≥10 successive days Grain filling (#3) Late–rice Heading–flowering (#2) Chilling T ≤20 °C ≥1 successive day Rain P ≥25 mm ≥1 successive day Grain filling (#3) Chilling T ≤17 °C ≥1 successive day Rain P ≥25 mm ≥1 successive day Note: The above thresholds are referenced from <NY/T 2915–2016>, Identification and classification of heat injury of rice; <NY/T 3043–2016>, Code of practice for field investigations and classification of rice seasonal drought stressess in southern–China; <NY/T 2285–2012>, Technical specification of field investigations and the grading of chilling damage to rice and; <DB5101/T 125–2021>, Indica rice weather stress level–continuous rain. NY/T is the Agricultural Information Resource Classification and Coding Specification in China. DB5101/T is the Local Standard of Chengdu, Sichuan Province. Thresholds for duration were relaxed from original standards to ensure adequate samples for later analyses.

_Traducción (no es cita):_ Tabla 1. Umbrales de cada evento extremo individual. Tipo de arroz | Etapa | Extremo | Indicador y umbral: temperatura media diaria (T, °C), precipitación diaria total (PRE, mm), humedad relativa del suelo (SM, %). Arroz de una cosecha: encañado–embuche (#1), espigado–floración (#2), llenado (#3): calor T ≥ 33 °C ≥ 1 día sucesivo; sequía SM ≤ 75 % ≥ 10 días sucesivos. Arroz tardío: espigado–floración (#2): frío T ≤ 20 °C ≥ 1 día; lluvia P ≥ 25 mm ≥ 1 día; llenado (#3): frío T ≤ 17 °C ≥ 1 día; lluvia P ≥ 25 mm ≥ 1 día. Nota: los umbrales provienen de NY/T 2915–2016 (identificación y clasificación del daño por calor en arroz), NY/T 3043–2016, NY/T 2285–2012 y DB5101/T 125–2021. Los umbrales de duración se relajaron respecto a las normas originales para tener muestras suficientes en los análisis.

**[Jiang-p2] convención de duración citada (más de 3 días consecutivos)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 2, p. impresa 2 of 20; Introduction.  
_Re-extraído ahora con PyMuPDF._

> It is widely accepted that the heat stress process is defined according to the threshold of average temperature (Tave) at 30 ◦C or maximum temperature (Tmax) at 35 ◦C for more than 3 consecutive days throughout the reproductive phase [5,9,14,24,25].

_Traducción (no es cita):_ Es ampliamente aceptado que el proceso de estrés por calor se define según el umbral de temperatura media (Tave) de 30 °C o de temperatura máxima (Tmax) de 35 °C durante más de 3 días consecutivos a lo largo de la fase reproductiva [5,9,14,24,25].

**[Jiang-fases] etapas estudiadas** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 5, p. impresa 5 of 20; §2.3.1 Target Phenological Stages of Rice Heat Stress.  
_Re-extraído ahora con PyMuPDF._

> Furthermore, regardless of the rice characteristics and climate warming trends, the investigated phenological stages focused on the tillering–jointing, booting, flowering and filling stages, broadly grouped into one vegetative and three reproductive stages.

_Traducción (no es cita):_ Además, sin importar las características del arroz ni las tendencias de calentamiento, las etapas fenológicas estudiadas se centraron en macollamiento–encañado, embuche, floración y llenado, agrupadas en una etapa vegetativa y tres reproductivas.

**[Jiang24-hcii] la duración de los grados se cuenta con HCIId > 0** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 6, p. impresa 6 of 21; §2.3.2.  
_Re-extraído ahora con PyMuPDF._

> HCIId = 0 is determined as the critical value of disaster-causing. HCIId ≤0 is identified as a non-disaster, while HCIId > 0 is identified as a disaster. Then, we focused on the duration (HCIId > 0) subjected to heat disaster processes and HCIId accumulation during the duration, two important components to reveal the heat disaster level within hot weather events.

_Traducción (no es cita):_ HCIId = 0 se determina como el valor crítico de causa de desastre. HCIId ≤ 0 se identifica como no desastre y HCIId > 0 como desastre. Luego nos centramos en la duración (HCIId > 0) de los procesos de desastre por calor y en la acumulación de HCIId durante esa duración, dos componentes importantes para revelar el nivel del desastre dentro de los eventos de tiempo caluroso.

**Valores en conflicto:** Jiang 2023 da dos formulaciones de la duración: «more than 3 consecutive days» (p. 2, convención citada para Tave 30 °C o Tmax 35 °C) y «at least 3 days» (p. 7, definición de proceso que usa el método). Más de 3 = 4 días o más; al menos 3 = 3 días o más. Las citas de ambos textos están arriba: Jiang-p2, Jiang-dur.

## R12 — Arroz · Calor · FIL

- **Fase homologada (tesis):** FIL (arroz: BBCH 70–79)
- **Etapa en la fuente:** «filling» (Jiang 2023); «grain filling (#3)», del día 11 después del espigado a la madurez (Sun 2025); «post-heading» (Shi 2015)
- **Cobertura:** Jiang ≈ equivalente. Sun #3 y Shi cubren más: llegan hasta la madurez (MAT); Shi empieza en el espigado.
- **Umbral, variable y duración según la fuente:** Jiang: Tmax diaria, 38 °C; duración como R10. Shi: Tmax 35 °C (sin rachas). Sun: Tmedia ≥ 33 °C, ≥ 1 día.
- **Regla en el Excel:** Tmax > 38 °C; ≥ 3 días consecutivos con Tmax sobre el umbral (Jiang 2023, p. 7 §2.5.2: «exceeds the critical threshold for at least 3 days»); variable: Tmax diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Jiang 2024 (llenado): leve 3–6 d; moderada 7–9 d; severa >9 d
- **Estado:** Propuesta — decide Paola. Validación Paola: Aprobada: Jiang 2023 (Tmax 35/35/38 °C, más de 3 días consecutivos según la convención citada en Jiang 2023 p. 2). Se descartan los grados de Jiang 2024 porque su duración cuenta días con HCIId > 0, no días con Tmax sobre el umbral. (Decisión de Paola, 4 nov 2026.) | 5 nov 2026: Paola registra la duración como ≥ 3 días con la cita de la p. 7 (método); la p. 2 («more than 3 consecutive days», convención citada) queda como valor en conflicto.

**Fuentes:**

- Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q. (2023). Characteristic Identification of Heat Exposure Based on Disaster Events for Single-Season Rice along the Middle and Lower Reaches of the Yangtze River, China. Agronomy 13(10), 2574. DOI 10.3390/agronomy13102574  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-13-02574.pdf`  
  Páginas: Jiang-resumen: p. PDF 1 / impresa 1 of 20; Jiang-roc: p. PDF 10 / impresa 10 of 20; Jiang-dur: p. PDF 7 / impresa 7 of 20; Jiang-p2: p. PDF 2 / impresa 2 of 20; Jiang-fases: p. PDF 5 / impresa 5 of 20
- Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R. (2024). Dynamic Evaluation and Risk Projection of Heat Exposure Based on Disaster Events for Single-Season Rice along the Middle and Lower Reaches of the Yangtze River, China. Agronomy 14, 1737. DOI 10.3390/agronomy14081737 (acceso abierto)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Jiang_2024_Agronomy_14_1737.pdf`  
  Páginas: Jiang24-umbral: p. PDF 5 / impresa 5 of 21; Jiang24-sev: p. PDF 10 / impresa 10 of 21; Jiang24-hcii: p. PDF 6 / impresa 6 of 21
- Shi, P.; Tang, L.; Wang, L.; Sun, T.; Liu, L.; Cao, W.; Zhu, Y. (2015). Post-Heading Heat Stress in Rice of South China during 1981-2010. PLOS ONE 10(6), e0130642. DOI 10.1371/journal.pone.0130642 (acceso abierto)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Shi_2015_PLOSONE.pdf`  
  Páginas: Shi-umbral: p. PDF 14 / impresa 14 / 18
- Sun, R.; et al. (2025). Spatiotemporal variation of growth-stage specific concurrent climate extremes (arroz). Earth System Dynamics 16, 1971–1988. DOI 10.5194/esd-16-1971-2025  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\esd-16-1971-2025.pdf`  
  Páginas: Sun-fases: p. PDF 4 / impresa 1974; Sun-var: p. PDF 4 / impresa 1974; Sun-tabla1: p. PDF 5 / impresa 1975

**Citas textuales:**

**[Jiang-resumen] umbral Tmax por etapa** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 1, p. impresa 1 of 20; Abstract.  
_Re-extraído ahora con PyMuPDF._

> Critical temperature thresholds of Tmax at tillering–jointing, booting, flowering and filling were quantified as 36, 35, 35 and 38 ◦C, with higher IF values of 13.14, 10.93, 17.15 and 13.15, respectively.

_Traducción (no es cita):_ Los umbrales críticos de Tmax en macollamiento–encañado, embuche, floración y llenado se cuantificaron en 36, 35, 35 y 38 °C, con valores de IF más altos de 13,14; 10,93; 17,15 y 13,15, respectivamente.

**[Jiang-roc] umbral Tmax por etapa (ROC sobre registros de desastre)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 10, p. impresa 10 of 20; §3.2 (ROC, Figura 5).  
_Re-extraído ahora con PyMuPDF._

> The ROC curves for each phenological stage were drawn in Figure 5, illustrating a trade‑off between achieving a high true‑positive rate and a low false‑positive rate. Each test point on the ROC plot referred to a sensitivity‑specificity pair corresponding to a par‑ ticular decision threshold. AUC values were obtained from TPRs and FPRs at each test point, reaching 0.993 at tillering–jointing, 0.959 at booting, 0.989 at flowering, and 0.930 at filling, corresponding to ‘excellent’ performances of Tmax as the trigger factor to discrimi‑ nate whether heat occurred or no heat. Measured comprehensively by the method above, the Tmax values of 36, 35, 35. and 38 ◦C were sequentially confirmed as the optimal critical threshold for identifying the occurrence of heat exposure to single‑season rice in MLRYR as the phenological stage advanced.

_Traducción (no es cita):_ Las curvas ROC de cada etapa se dibujaron en la Figura 5 y muestran el compromiso entre una alta tasa de verdaderos positivos y una baja tasa de falsos positivos. Cada punto de prueba corresponde a un par sensibilidad-especificidad para un umbral de decisión. Los valores de AUC fueron 0,993 en macollamiento–encañado, 0,959 en embuche, 0,989 en floración y 0,930 en llenado, un desempeño «excelente» de Tmax como factor de disparo para discriminar si hubo o no calor. Medidos de forma integral con este método, los valores de Tmax de 36, 35, 35 y 38 °C se confirmaron sucesivamente como el umbral crítico óptimo para identificar la exposición al calor del arroz de una cosecha en la cuenca media-baja del Yangtsé, a medida que avanza la etapa.

**[Jiang-dur] duración (proceso ≥3 d)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 7, p. impresa 7 of 20; §2.5.2.  
_Re-extraído ahora con PyMuPDF._

> Generally speaking, most domestic studies consider a heat process where the maximum air temper‑ ature exceeds the critical threshold for at least 3 days.

_Traducción (no es cita):_ En general, la mayoría de los estudios nacionales considera un proceso de calor aquel en que la temperatura máxima del aire supera el umbral crítico durante al menos 3 días.

**[Jiang24-umbral] umbrales por etapa (heredados de Jiang 2023) y racha ≥3 d** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 5, p. impresa 5 of 21; §2.3.1.  
_Re-extraído ahora con PyMuPDF._

> The various thresh-olds of heat occurrence were set to 36 ◦C at tillering, 35 ◦C at booting, 35 ◦C at flowering, and 38 ◦C at filling in this study. A detailed description of the determination of the four growth stages mentioned above as crucial phenology phases for heat exposure can be found in M. Jiang [51]. Among all recorded historical disasters, rice heat samples of hot weather processes with continuous days ≥3 d were counted by the given critical threshold and di-vided into the corresponding growth stages.

_Traducción (no es cita):_ Los distintos umbrales de ocurrencia de calor se fijaron en 36 °C en macollamiento, 35 °C en embuche, 35 °C en floración y 38 °C en llenado en este estudio. La descripción de cómo se determinaron estas cuatro etapas fenológicas cruciales para la exposición al calor está en M. Jiang [51]. Entre todos los desastres históricos registrados, las muestras de calor con procesos de tiempo caluroso de ≥3 días continuos se contaron con el umbral crítico dado y se dividieron en las etapas correspondientes.

**[Jiang24-sev] severidad por duración** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 10, p. impresa 10 of 21; §3.2.2.  
_Re-extraído ahora con PyMuPDF._

> Not only at booting did hot weather persist for 3~5 d and 6~8 d induced mild and moderate rice heat, but also at flowering. There were slight extensions for heat durations at tillering and filling, with the 3~6 d and 7~9 d heat duration probably emerging as mild and moderate heat damage, respectively. Furthermore, heat durations of severe disasters at different growth stages for single-season rice mostly exceeded 9 d.

_Traducción (no es cita):_ No solo en embuche, sino también en floración, el tiempo caluroso que persistió 3~5 d y 6~8 d indujo calor leve y moderado en el arroz. En macollamiento y llenado las duraciones se extendieron levemente: 3~6 d y 7~9 d probablemente corresponden a daño leve y moderado, respectivamente. Además, la duración de los desastres severos en las distintas etapas del arroz de una cosecha superó en su mayoría los 9 d.

**[Shi-umbral] umbral 35 °C por LOOCV contra rendimiento (espigado–madurez)** — Shi, P.; Tang, L.; Wang, L.; Sun, T.; Liu, L.; Cao, W.; Zhu, Y.; p. PDF 14, p. impresa 14 / 18; Discussion.  
_Re-extraído ahora con PyMuPDF._

> In order to select the optimal high temperature threshold in the whole study region, the method of leave-one-out cross validation (LOOCV) was used to find the minimized mean square errors for grain yield predictions among different temperature thresholds (range from 30°C to 38°C with an interval of 0.2°C) (S1 Fig). Results showed that the 35°C was the optimal high tempera-ture threshold in rice in South China for the two types of statistical models.

_Traducción (no es cita):_ Para seleccionar el umbral óptimo de alta temperatura en toda la región, se usó validación cruzada dejando uno fuera (LOOCV) para encontrar el mínimo error cuadrático medio de las predicciones de rendimiento entre distintos umbrales (de 30 °C a 38 °C, cada 0,2 °C) (Fig. S1). Los resultados mostraron que 35 °C fue el umbral óptimo de alta temperatura para el arroz del sur de China en los dos tipos de modelos estadísticos.

**[Sun-fases] definición de etapas #1–#3** — Sun, R.; et al.; p. PDF 4, p. impresa 1974; §2.3.1.  
_Re-extraído ahora con PyMuPDF._

> Three growth stages that were most susceptible to extreme stress were considered in this study: jointing–booting stage (#1), heading–flowering stage (#2) and grain filling stage (#3). The jointing–booting stage refers to the period from the first day of jointing to the last day before heading. The heading–flowering stage refers to the period from heading to flowering and generally lasts for 10 d. The grain filling stage refers to the period from the 11th day after heading to ma-turity. The exact dates of the different stages were obtained from phenological records for each year and station.

_Traducción (no es cita):_ En este estudio se consideraron las tres etapas más susceptibles al estrés extremo: encañado–embuche (#1), espigado–floración (#2) y llenado (#3). Encañado–embuche va del primer día de encañado al último día antes del espigado. Espigado–floración va del espigado a la floración y suele durar 10 d. Llenado va del día 11 después del espigado hasta la madurez. Las fechas exactas se tomaron de registros fenológicos de cada año y estación.

**[Sun-var] variable (Tmedia) y corte 33 °C** — Sun, R.; et al.; p. PDF 4, p. impresa 1974; §2.3.2.  
_Re-extraído ahora con PyMuPDF._

> Following this concept, heat stress (H) sever-ity SH,g,t at a given growth stage (g) in a given year (t) that meets the condition can be computed by the cumulative de-viation of mean daily temperature (T ) above its threshold (Tbase) for all the days (i) within this stage. We used 33 °C as the base temperature (Table 1) in Eq. (1).

_Traducción (no es cita):_ Siguiendo este concepto, la severidad del estrés por calor (H) SH,g,t en una etapa (g) de un año (t) que cumple la condición se calcula como la desviación acumulada de la temperatura media diaria (T) por encima de su umbral (Tbase) en todos los días (i) de la etapa. Usamos 33 °C como temperatura base (Tabla 1) en la Ec. (1).

**[Sun-tabla1] umbral, duración y procedencia (normas NY/T)** — Sun, R.; et al.; p. PDF 5, p. impresa 1975; Tabla 1 (The thresholds of each individual extreme event) y nota.  
_Re-extraído ahora con PyMuPDF._

> Table 1. The thresholds of each individual extreme event. Rice type Growth stage Climate Indicator & threshold: daily mean temperature (T / °C), extremes daily total precipitation (PRE / mm), relative soil moisture (SM / %) Single–rice Jointing–booting (#1) Heat T ≥33 °C ≥1 successive day Heading–flowering (#2) Drought SM ≤75 % ≥10 successive days Grain filling (#3) Late–rice Heading–flowering (#2) Chilling T ≤20 °C ≥1 successive day Rain P ≥25 mm ≥1 successive day Grain filling (#3) Chilling T ≤17 °C ≥1 successive day Rain P ≥25 mm ≥1 successive day Note: The above thresholds are referenced from <NY/T 2915–2016>, Identification and classification of heat injury of rice; <NY/T 3043–2016>, Code of practice for field investigations and classification of rice seasonal drought stressess in southern–China; <NY/T 2285–2012>, Technical specification of field investigations and the grading of chilling damage to rice and; <DB5101/T 125–2021>, Indica rice weather stress level–continuous rain. NY/T is the Agricultural Information Resource Classification and Coding Specification in China. DB5101/T is the Local Standard of Chengdu, Sichuan Province. Thresholds for duration were relaxed from original standards to ensure adequate samples for later analyses.

_Traducción (no es cita):_ Tabla 1. Umbrales de cada evento extremo individual. Tipo de arroz | Etapa | Extremo | Indicador y umbral: temperatura media diaria (T, °C), precipitación diaria total (PRE, mm), humedad relativa del suelo (SM, %). Arroz de una cosecha: encañado–embuche (#1), espigado–floración (#2), llenado (#3): calor T ≥ 33 °C ≥ 1 día sucesivo; sequía SM ≤ 75 % ≥ 10 días sucesivos. Arroz tardío: espigado–floración (#2): frío T ≤ 20 °C ≥ 1 día; lluvia P ≥ 25 mm ≥ 1 día; llenado (#3): frío T ≤ 17 °C ≥ 1 día; lluvia P ≥ 25 mm ≥ 1 día. Nota: los umbrales provienen de NY/T 2915–2016 (identificación y clasificación del daño por calor en arroz), NY/T 3043–2016, NY/T 2285–2012 y DB5101/T 125–2021. Los umbrales de duración se relajaron respecto a las normas originales para tener muestras suficientes en los análisis.

**[Jiang-p2] convención de duración citada (más de 3 días consecutivos)** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 2, p. impresa 2 of 20; Introduction.  
_Re-extraído ahora con PyMuPDF._

> It is widely accepted that the heat stress process is defined according to the threshold of average temperature (Tave) at 30 ◦C or maximum temperature (Tmax) at 35 ◦C for more than 3 consecutive days throughout the reproductive phase [5,9,14,24,25].

_Traducción (no es cita):_ Es ampliamente aceptado que el proceso de estrés por calor se define según el umbral de temperatura media (Tave) de 30 °C o de temperatura máxima (Tmax) de 35 °C durante más de 3 días consecutivos a lo largo de la fase reproductiva [5,9,14,24,25].

**[Jiang-fases] etapas estudiadas** — Jiang, M.; Huo, Z.; Zhang, L.; Kong, R.; Li, M.; Mi, Q.; p. PDF 5, p. impresa 5 of 20; §2.3.1 Target Phenological Stages of Rice Heat Stress.  
_Re-extraído ahora con PyMuPDF._

> Furthermore, regardless of the rice characteristics and climate warming trends, the investigated phenological stages focused on the tillering–jointing, booting, flowering and filling stages, broadly grouped into one vegetative and three reproductive stages.

_Traducción (no es cita):_ Además, sin importar las características del arroz ni las tendencias de calentamiento, las etapas fenológicas estudiadas se centraron en macollamiento–encañado, embuche, floración y llenado, agrupadas en una etapa vegetativa y tres reproductivas.

**[Jiang24-hcii] la duración de los grados se cuenta con HCIId > 0** — Jiang, M.; Huo, Z.; Zhang, L.; Zhang, F.; Li, M.; Mi, Q.; Kong, R.; p. PDF 6, p. impresa 6 of 21; §2.3.2.  
_Re-extraído ahora con PyMuPDF._

> HCIId = 0 is determined as the critical value of disaster-causing. HCIId ≤0 is identified as a non-disaster, while HCIId > 0 is identified as a disaster. Then, we focused on the duration (HCIId > 0) subjected to heat disaster processes and HCIId accumulation during the duration, two important components to reveal the heat disaster level within hot weather events.

_Traducción (no es cita):_ HCIId = 0 se determina como el valor crítico de causa de desastre. HCIId ≤ 0 se identifica como no desastre y HCIId > 0 como desastre. Luego nos centramos en la duración (HCIId > 0) de los procesos de desastre por calor y en la acumulación de HCIId durante esa duración, dos componentes importantes para revelar el nivel del desastre dentro de los eventos de tiempo caluroso.

**Valores en conflicto:** Jiang 2023 da 38 °C para el llenado; Shi 2015 da 35 °C como óptimo, pero para toda la ventana espigado–madurez. Las citas de ambos textos están arriba: Jiang-roc, Shi-umbral.

**Valores en conflicto:** Jiang 2023 da dos formulaciones de la duración: «more than 3 consecutive days» (p. 2, convención citada para Tave 30 °C o Tmax 35 °C) y «at least 3 days» (p. 7, definición de proceso que usa el método). Más de 3 = 4 días o más; al menos 3 = 3 días o más. Las citas de ambos textos están arriba: Jiang-p2, Jiang-dur.

## R13 — Arroz · Calor · MAT

- **Fase homologada (tesis):** MAT (arroz: BBCH 80–99)
- **Etapa en la fuente:** «Ripening» (Yoshida 1981, Tabla 2.4)
- **Cobertura:** La fuente cubre más: «ripening» incluye llenado y maduración (BBCH 70–99).
- **Umbral, variable y duración según la fuente:** Temperatura media diaria, valor «High» = 30 °C. La fuente no da duración.
- **Regla en el Excel:** Tmedia > 30 °C; La fuente no publica duración; variable: Tmedia diaria del aire a 2 m (ERA5-Land)
- **Severidad:** No publicada
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Yoshida, S. (1981). Fundamentals of Rice Crop Science. IRRI, Los Baños. Libro, sin DOI  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\Yoshida_1981.pdf`  
  Páginas: Yoshida-tabla24: p. PDF 80 / impresa 72; Yoshida-alcance: p. PDF 80 / impresa 72

**Citas textuales:**

**[Yoshida-tabla24] umbral (columna High) y estadístico (nota b)** — Yoshida, S.; p. PDF 80, p. impresa 72; Tabla 2.4 (Response of the rice plant to varying temperatures at different growth stages) y notas a/b.  
_Re-extraído ahora con pdfplumber (tabla leída por filas)._

> Table 2.4. Response of the rice plant to varying temperatures at different growth stages. a Critical temperature b (°C) Growth stage Low High Optimum Germination 10 45 20–35 Seedling emergence and establishment 12–13 35 25–30 Rooting 16 35 25–28 Leaf elongation 7–12 45 31 Tillering 9–16 33 25–31 Initiation of panicle – – primordia 15 – Panicle differentiation 15–20 38 Anthesis 22 35 30–33 Ripening 12–18 30 20–25 a Adapted and modified from Yoshida (1977a). b Refers to daily mean temperature except for germination.

_Traducción (no es cita):_ Tabla 2.4. Respuesta de la planta de arroz a distintas temperaturas en distintas etapas de crecimiento (a). Temperatura crítica (b) (°C): Baja | Alta | Óptima. Germinación 10 | 45 | 20–35; emergencia de plántula y establecimiento 12–13 | 35 | 25–30; enraizamiento 16 | 35 | 25–28; elongación de hoja 7–12 | 45 | 31; macollamiento 9–16 | 33 | 25–31; iniciación de primordios de panícula 15 | – | –; diferenciación de panícula 15–20 | 38 | –; antesis 22 | 35 | 30–33; maduración (ripening) 12–18 | 30 | 20–25. (a) Adaptada y modificada de Yoshida (1977a). (b) Se refiere a la temperatura media diaria, excepto en germinación.

**[Yoshida-alcance] alcance del umbral** — Yoshida, S.; p. PDF 80, p. impresa 72; Texto que remite a la Tabla 2.4.  
_Re-extraído ahora con PyMuPDF._

> The critically low and high temperatures, normally below 20°C and above 30°C, vary from one growth stage to another (Table 2.4). These critical temperatures differ according to variety, duration of critical temperature, diurnal changes, and physiological status of the plant.

_Traducción (no es cita):_ Las temperaturas críticas bajas y altas, normalmente por debajo de 20 °C y por encima de 30 °C, varían de una etapa a otra (Tabla 2.4). Estas temperaturas críticas difieren según la variedad, la duración de la temperatura crítica, los cambios diurnos y el estado fisiológico de la planta.

## R14 — Soya · Helada · EST

- **Fase homologada (tesis):** EST (soya: VE–VC)
- **Etapa en la fuente:** Después de la emergencia, 15–25 días tras la siembra (Mourtzinis 2019)
- **Cobertura:** Equivalente; la fuente habla de la emergencia, no de VC.
- **Umbral, variable y duración según la fuente:** Temperatura mínima diaria < 0 °C (probabilidad de helada). La fuente no da duración (solo «prolonged periods» para −2 °C, sin cifra).
- **Regla en el Excel:** Tmin < 0 °C; Diaria; sin horas mínimas publicadas; variable: Tmin diaria del aire a 2 m (ERA5-Land, temperature_2m_min)
- **Severidad:** No publicada (el texto menciona daño mayor bajo −2 °C «for prolonged periods», sin cifra de duración)
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Mourtzinis, S.; Specht, J. E.; Conley, S. P. (2019). Scientific Reports 9, 2800. DOI 10.1038/s41598-019-38971-3  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\s41598-019-38971-3.pdf`  
  Páginas: Mourtzinis-tmin: p. PDF 4 / impresa 4; Mourtzinis-dano: p. PDF 4 / impresa 4

**Citas textuales:**

**[Mourtzinis-tmin] estadístico: Tmin diaria** — Mourtzinis, S.; Specht, J. E.; Conley, S. P.; p. PDF 4, p. impresa 4; Results and Discussion (Fig. 4).  
_Re-extraído ahora con PyMuPDF._

> Using the 21 days earlier sowing as a threshold, 2% of all 289 locations (all in North Dakota, South Dakota, and Minnesota) exceeded the 20% probability threshold for daily minimum temperatures to drop below 0 °C at emergence and only 0.3% had exceeded the 20% probability for daily minimum temperatures to drop below −1 °C (Fig. 4).

_Traducción (no es cita):_ Usando 21 días de siembra anticipada como umbral, 2 % de las 289 localidades (todas en Dakota del Norte, Dakota del Sur y Minnesota) superaron el 20 % de probabilidad de que la temperatura mínima diaria bajara de 0 °C en la emergencia, y solo 0,3 % superó el 20 % de probabilidad de que bajara de −1 °C (Fig. 4).

**[Mourtzinis-dano] amenaza y fase (helada tras emergencia)** — Mourtzinis, S.; Specht, J. E.; Conley, S. P.; p. PDF 4, p. impresa 4; Results and Discussion.  
_Re-extraído ahora con PyMuPDF._

> An important consideration in early sowing is spring frost occurrence, which can damage or destroy the crop (but only after emergence at 15–25 DAS)16. The current common recommendation to soybean producers is to sow the first field when frost probabilities are less than 20% on or after emergence. Minor frost damage on emerged seedlings may occur when temperature drops below 0 °C, but becomes more damaging when tempera-ture drops below −2 °C for prolonged periods.

_Traducción (no es cita):_ Un aspecto importante de la siembra temprana es la helada de primavera, que puede dañar o destruir el cultivo (pero solo después de la emergencia, a los 15–25 días después de la siembra)16. La recomendación actual a los productores es sembrar el primer lote cuando la probabilidad de helada sea menor de 20 % en la emergencia o después. Puede haber daño leve por helada en plántulas emergidas cuando la temperatura baja de 0 °C, pero el daño es mayor cuando baja de −2 °C por períodos prolongados.

## R15 — Soya · Calor diurno sostenido · VEG

- **Fase homologada (tesis):** VEG (soya: V1–Vn)
- **Etapa en la fuente:** Cuatro trifolios completamente expandidos (≈ V4) (Herritt y Fritschi 2020)
- **Cobertura:** La fuente cubre menos: solo V4, en cámara.
- **Umbral, variable y duración según la fuente:** Tratamiento de 45 °C de 9:00 a. m. a 1:00 p. m. (4 h/día) durante 7 días. No es un umbral de campo.
- **Regla en el Excel:** 45 °C (tratamiento); 4 h/día durante 7 días; variable: Temperatura horaria del aire (no disponible como regla diaria)
- **Severidad:** No publicada
- **Estado:** Eliminada. Validación Paola: ELIMINADA (decisión de Paola, 5 nov 2026): sin regla diaria con fuente verificable.

**Fuentes:**

- Herritt, M. T.; Fritschi, F. B. (2020). Frontiers in Plant Science 11, 153. DOI 10.3389/fpls.2020.00153  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\fpls-11-00153.pdf`  
  Páginas: Herritt-protocolo: p. PDF 3 / impresa 3

**Citas textuales:**

**[Herritt-protocolo] tratamiento experimental (45 °C, 4 h/d, 7 d)** — Herritt, M. T.; Fritschi, F. B.; p. PDF 3, p. impresa 3; Materials and Methods – Genotypes and Growth Conditions.  
_Re-extraído ahora con PyMuPDF._

> Plants were grown for three additional weeks until they reached four fully expanded trifoliate leaves. At that time, three temperature treatments were initiated, namely 28, 38, and 45°C maximum air temperatures which were imposed as follows: For the control treatment (28°C), the temperature regime was maintained the same as for initial growth. For elevated air temperature treatments, the temperature was increased gradually from 28°C at 7:00 am to reach 38 or 45°C by 9:00 am and held at these temperatures until 1:00 pm. Then the temperature was reduced from 38 or 45°C to 28°C from 1:00 pm to 3:00 pm and maintained at 28°C until 8:00 pm. Elevated temperatures that occur during the growing season often come in the form of heat waves that generally last a few to several days. Therefore, temperature treatments were imposed over the course of 7 days, at which point the experiments were terminated.

_Traducción (no es cita):_ Las plantas crecieron tres semanas más hasta tener cuatro hojas trifoliadas completamente expandidas. Entonces se iniciaron tres tratamientos de temperatura: 28, 38 y 45 °C de temperatura máxima del aire, impuestos así: en el control (28 °C) se mantuvo el régimen del crecimiento inicial. En los tratamientos de temperatura elevada, la temperatura subió gradualmente de 28 °C a las 7:00 a. m. hasta 38 o 45 °C a las 9:00 a. m. y se mantuvo hasta la 1:00 p. m. Luego bajó de 38 o 45 °C a 28 °C entre la 1:00 y las 3:00 p. m. y se mantuvo en 28 °C hasta las 8:00 p. m. Las temperaturas elevadas en la temporada suelen llegar como olas de calor que duran de unos pocos a varios días. Por eso los tratamientos se impusieron durante 7 días, momento en que terminaron los experimentos.

## R16 — Soya · Calor en antesis (modelo) · FLO

- **Fase homologada (tesis):** FLO (soya: R1–R2)
- **Etapa en la fuente:** TSP alrededor de la antesis: de 0,45 a 0,7 del período de crecimiento (Deryng 2014)
- **Cobertura:** No es una etapa Fehr–Caviness: es una fracción del ciclo del modelo; probablemente cubre R1 y parte de R2–R4.
- **Umbral, variable y duración según la fuente:** Teff diaria = (Tmedia + Tmax)/2 > 35 °C (Tcr); Tlim = 40 °C. Sin duración mínima: el factor es diario y se promedia en el TSP.
- **Regla en el Excel:** Teff > 35 °C (Tcr); límite 40 °C (Tlim); Diaria; sin racha mínima; variable: Teff diaria = (Tmedia + Tmax)/2 (ERA5-Land)
- **Severidad:** Función lineal entre Tcr y Tlim (ec. A.6)
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Deryng, D.; Conway, D.; Ramankutty, N.; Price, J.; Warren, R. (2014). Global crop yield response to extreme heat stress under multiple climate change futures. Environmental Research Letters 9, 034011. DOI 10.1088/1748-9326/9/3/034011  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\pdf.pdf`  
  Páginas: Deryng-teff: p. PDF 11 / impresa 10; Deryng-tsp: p. PDF 11 / impresa 10; Deryng-tablaA1: p. PDF 11 / impresa 10

**Citas textuales:**

**[Deryng-teff] estadístico Teff y umbrales** — Deryng, D.; Conway, D.; Ramankutty, N.; Price, J.; Warren, R.; p. PDF 11, p. impresa 10; Apéndice A.3 (tras ec. A.6).  
_Re-extraído ahora con PyMuPDF._

> Teff is defined as (Tmean + Tmax)/2, where Tmean is the daily mean temperature and Tmax is the daily maximum tempera-ture [44], Tlim is the limit temperature above which fHSAd is maximal. Crop specific Tcr and Tlim come from a synthesis of values found in the literature [10, 11, 14, 33, 45–49] (table A.1). Temperature tolerance differs for each crop. Here, HSA critical temperature thresholds are 25 ◦C for spring wheat, 32 ◦C for maize and 35 ◦C for soybean. Hence, as temperatures increase spring wheat yield is impacted first, followed by maize and finally soybean. However, HSA impact functions differ among crop type as temperature thresholds at zero pod-set are 35 ◦C for spring wheat, 45 ◦C for maize and 40 ◦C for soybean.

_Traducción (no es cita):_ Teff se define como (Tmedia + Tmax)/2, donde Tmedia es la temperatura media diaria y Tmax la máxima diaria [44]; Tlim es la temperatura límite por encima de la cual fHSAd es máximo. Tcr y Tlim por cultivo vienen de una síntesis de valores de la literatura [10, 11, 14, 33, 45–49] (Tabla A.1). La tolerancia a la temperatura difiere por cultivo. Aquí los umbrales críticos de HSA son 25 °C para trigo de primavera, 32 °C para maíz y 35 °C para soya. Así, al subir la temperatura se afecta primero el trigo de primavera, luego el maíz y por último la soya. Sin embargo, las funciones de impacto difieren: las temperaturas con cuajado de vainas nulo son 35 °C para trigo de primavera, 45 °C para maíz y 40 °C para soya.

**[Deryng-tsp] ventana fenológica (TSP)** — Deryng, D.; Conway, D.; Ramankutty, N.; Price, J.; Warren, R.; p. PDF 11, p. impresa 10; Apéndice A.3 Heat stress at anthesis.  
_Re-extraído ahora con PyMuPDF._

> Crop TSP includes a couple of days before and after anthesis and is estimated as a function of crop growing period length (GPL), which depends on growing degree days accumulation [5] and varies with crop cultivars. Anthesis is scheduled when the number of days since emergence reaches half of crop GPL (calculated between emergence and maturity), i.e., 0.5 GPL; TSP starts a few days before anthesis at 0.45 GPL and ends after anthesis at 0.7 GPL. A high temperature event occurs when daily effective temperature (Teff) exceeds a critical temperature (Tcr) threshold.

_Traducción (no es cita):_ El período sensible a la temperatura (TSP) del cultivo incluye un par de días antes y después de la antesis y se estima en función de la duración del período de crecimiento (GPL), que depende de la acumulación de grados-día [5] y varía según el cultivar. La antesis se programa cuando los días desde la emergencia llegan a la mitad del GPL (entre emergencia y madurez), es decir 0,5 GPL; el TSP empieza unos días antes de la antesis, en 0,45 GPL, y termina después, en 0,7 GPL. Ocurre un evento de alta temperatura cuando la temperatura efectiva diaria (Teff) supera un umbral de temperatura crítica (Tcr).

**[Deryng-tablaA1] valores Tcr/Tlim soya (PEGASUS 1.1 y Teixeira 2011)** — Deryng, D.; Conway, D.; Ramankutty, N.; Price, J.; Warren, R.; p. PDF 11, p. impresa 10; Tabla A.1.  
_Re-extraído ahora con PyMuPDF._

> Table A.1. Temperature critic (Tcr) and limit (Tlim) (in ◦C) for maize, wheat and soybean used in this study (PEGASUS 1.1) and corresponding values found in the literature. Maize Wheat Soybean Reference Tcr (◦C) Tlim (◦C) Tcr (◦C) Tlim (◦C) Tcr (◦C) Tlim (◦C) PEGASUS 1.1 32 45 25 35 35 40 Lobell et al (2013) [8] 30 Moriondo et al (2011) [10] 31 40 Semenov and Shewry (2011) [11] 27 Teixeira et al (2011) [14] 35 45 27 40 35 40

_Traducción (no es cita):_ Tabla A.1. Temperatura crítica (Tcr) y límite (Tlim) (°C) para maíz, trigo y soya usadas en este estudio (PEGASUS 1.1) y valores correspondientes de la literatura. Maíz Tcr/Tlim | Trigo Tcr/Tlim | Soya Tcr/Tlim. PEGASUS 1.1: 32/45 | 25/35 | 35/40. Lobell et al. (2013): 30 (maíz). Moriondo et al. (2011): 31/40 (trigo). Semenov y Shewry (2011): 27 (trigo). Teixeira et al. (2011): 35/45 | 27/40 | 35/40.

## R17 — Soya · Calor reproductivo (modelo) · REP-pos

- **Fase homologada (tesis):** REP-pos (soya: R3–R4)
- **Etapa en la fuente:** La misma TSP de Deryng 2014
- **Cobertura:** Homologación nuestra: el paper no define una regla aparte para formación de vainas.
- **Umbral, variable y duración según la fuente:** Igual que R16.
- **Regla en el Excel:** Teff > 35 °C (Tcr); límite 40 °C (Tlim); Diaria; sin racha mínima; variable: Teff diaria = (Tmedia + Tmax)/2 (ERA5-Land)
- **Severidad:** Función lineal entre Tcr y Tlim (ec. A.6)
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Deryng, D.; Conway, D.; Ramankutty, N.; Price, J.; Warren, R. (2014). Global crop yield response to extreme heat stress under multiple climate change futures. Environmental Research Letters 9, 034011. DOI 10.1088/1748-9326/9/3/034011  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\pdf.pdf`  
  Páginas: Deryng-teff: p. PDF 11 / impresa 10; Deryng-tsp: p. PDF 11 / impresa 10; Deryng-tablaA1: p. PDF 11 / impresa 10

**Citas textuales:**

**[Deryng-teff] estadístico Teff y umbrales** — Deryng, D.; Conway, D.; Ramankutty, N.; Price, J.; Warren, R.; p. PDF 11, p. impresa 10; Apéndice A.3 (tras ec. A.6).  
_Re-extraído ahora con PyMuPDF._

> Teff is defined as (Tmean + Tmax)/2, where Tmean is the daily mean temperature and Tmax is the daily maximum tempera-ture [44], Tlim is the limit temperature above which fHSAd is maximal. Crop specific Tcr and Tlim come from a synthesis of values found in the literature [10, 11, 14, 33, 45–49] (table A.1). Temperature tolerance differs for each crop. Here, HSA critical temperature thresholds are 25 ◦C for spring wheat, 32 ◦C for maize and 35 ◦C for soybean. Hence, as temperatures increase spring wheat yield is impacted first, followed by maize and finally soybean. However, HSA impact functions differ among crop type as temperature thresholds at zero pod-set are 35 ◦C for spring wheat, 45 ◦C for maize and 40 ◦C for soybean.

_Traducción (no es cita):_ Teff se define como (Tmedia + Tmax)/2, donde Tmedia es la temperatura media diaria y Tmax la máxima diaria [44]; Tlim es la temperatura límite por encima de la cual fHSAd es máximo. Tcr y Tlim por cultivo vienen de una síntesis de valores de la literatura [10, 11, 14, 33, 45–49] (Tabla A.1). La tolerancia a la temperatura difiere por cultivo. Aquí los umbrales críticos de HSA son 25 °C para trigo de primavera, 32 °C para maíz y 35 °C para soya. Así, al subir la temperatura se afecta primero el trigo de primavera, luego el maíz y por último la soya. Sin embargo, las funciones de impacto difieren: las temperaturas con cuajado de vainas nulo son 35 °C para trigo de primavera, 45 °C para maíz y 40 °C para soya.

**[Deryng-tsp] ventana fenológica (TSP)** — Deryng, D.; Conway, D.; Ramankutty, N.; Price, J.; Warren, R.; p. PDF 11, p. impresa 10; Apéndice A.3 Heat stress at anthesis.  
_Re-extraído ahora con PyMuPDF._

> Crop TSP includes a couple of days before and after anthesis and is estimated as a function of crop growing period length (GPL), which depends on growing degree days accumulation [5] and varies with crop cultivars. Anthesis is scheduled when the number of days since emergence reaches half of crop GPL (calculated between emergence and maturity), i.e., 0.5 GPL; TSP starts a few days before anthesis at 0.45 GPL and ends after anthesis at 0.7 GPL. A high temperature event occurs when daily effective temperature (Teff) exceeds a critical temperature (Tcr) threshold.

_Traducción (no es cita):_ El período sensible a la temperatura (TSP) del cultivo incluye un par de días antes y después de la antesis y se estima en función de la duración del período de crecimiento (GPL), que depende de la acumulación de grados-día [5] y varía según el cultivar. La antesis se programa cuando los días desde la emergencia llegan a la mitad del GPL (entre emergencia y madurez), es decir 0,5 GPL; el TSP empieza unos días antes de la antesis, en 0,45 GPL, y termina después, en 0,7 GPL. Ocurre un evento de alta temperatura cuando la temperatura efectiva diaria (Teff) supera un umbral de temperatura crítica (Tcr).

**[Deryng-tablaA1] valores Tcr/Tlim soya (PEGASUS 1.1 y Teixeira 2011)** — Deryng, D.; Conway, D.; Ramankutty, N.; Price, J.; Warren, R.; p. PDF 11, p. impresa 10; Tabla A.1.  
_Re-extraído ahora con PyMuPDF._

> Table A.1. Temperature critic (Tcr) and limit (Tlim) (in ◦C) for maize, wheat and soybean used in this study (PEGASUS 1.1) and corresponding values found in the literature. Maize Wheat Soybean Reference Tcr (◦C) Tlim (◦C) Tcr (◦C) Tlim (◦C) Tcr (◦C) Tlim (◦C) PEGASUS 1.1 32 45 25 35 35 40 Lobell et al (2013) [8] 30 Moriondo et al (2011) [10] 31 40 Semenov and Shewry (2011) [11] 27 Teixeira et al (2011) [14] 35 45 27 40 35 40

_Traducción (no es cita):_ Tabla A.1. Temperatura crítica (Tcr) y límite (Tlim) (°C) para maíz, trigo y soya usadas en este estudio (PEGASUS 1.1) y valores correspondientes de la literatura. Maíz Tcr/Tlim | Trigo Tcr/Tlim | Soya Tcr/Tlim. PEGASUS 1.1: 32/45 | 25/35 | 35/40. Lobell et al. (2013): 30 (maíz). Moriondo et al. (2011): 31/40 (trigo). Semenov y Shewry (2011): 27 (trigo). Teixeira et al. (2011): 35/45 | 27/40 | 35/40.

## R18 — Soya · Lluvia / calidad de semilla · FIL

- **Fase homologada (tesis):** FIL (soya: R5, R6–R7)
- **Etapa en la fuente:** Etapa reproductiva tardía R6–R8 (Weerasekara 2021)
- **Cobertura:** La fuente cubre otra ventana: no incluye R5 e incluye R8 (MAT). Es una sola ventana compartida con R19.
- **Umbral, variable y duración según la fuente:** Más de 100 mm de lluvia acumulada en R6–R8. La duración es la ventana completa.
- **Regla en el Excel:** > 100 mm acumulados en R6–R8; Ventana completa R6–R8; variable: Precipitación acumulada en la ventana (suma de P diaria ERA5-Land)
- **Severidad:** No publicada
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Weerasekara, I.; Sinniah, U. R.; et al. (2021). The Influence of Seed Production Environment on Seed Development and Quality of Soybean. Agronomy 11(7), 1430. DOI 10.3390/agronomy11071430  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-11-01430-v3.pdf`  
  Páginas: Weer-100mm: p. PDF 16 / impresa 16 of 19; Weer-fases: p. PDF 5 / impresa 5 of 19

**Citas textuales:**

**[Weer-100mm] umbral de lluvia acumulada** — Weerasekara, I.; Sinniah, U. R.; et al.; p. PDF 16, p. impresa 16 of 19; §5 Conclusions.  
_Re-extraído ahora con PyMuPDF._

> Maternal environmental conditions at the late reproductive stage (R6–R8) are the most critical factor in determining the initial seed quality. Rapid seed deterioration in the field occurred when more than 100 mm of cumulative rainfall coincided with the late reproductive stage.

_Traducción (no es cita):_ Las condiciones ambientales maternas en la etapa reproductiva tardía (R6–R8) son el factor más crítico para la calidad inicial de la semilla. El deterioro rápido de la semilla en campo ocurrió cuando más de 100 mm de lluvia acumulada coincidieron con la etapa reproductiva tardía.

**[Weer-fases] definición de etapas (R6–R8)** — Weerasekara, I.; Sinniah, U. R.; et al.; p. PDF 5, p. impresa 5 of 19; §3.1.  
_Re-extraído ahora con PyMuPDF._

> To understand the influence of production environment, the total growing period (TGP) was partitioned into three stages; (i) seed sowing (SS) to flowering (R1) as vegetative (VEG), (ii) flowering to full seed stage (R6) as early reproductive (ER), and (iii) full seed stage to full mature stage (R8) as late reproductive stage (LR).

_Traducción (no es cita):_ Para entender la influencia del ambiente de producción, el período total de crecimiento (TGP) se dividió en tres etapas: (i) siembra (SS) a floración (R1), vegetativa (VEG); (ii) floración a semilla completa (R6), reproductiva temprana (ER); y (iii) semilla completa a madurez completa (R8), reproductiva tardía (LR).

## R19 — Soya · Lluvia / calidad de semilla · MAT

- **Fase homologada (tesis):** MAT (soya: R8)
- **Etapa en la fuente:** Etapa reproductiva tardía R6–R8
- **Cobertura:** La fuente cubre más: R6–R8 (FIL y MAT). Misma ventana que R18.
- **Umbral, variable y duración según la fuente:** Igual que R18.
- **Regla en el Excel:** > 100 mm acumulados en R6–R8; Ventana completa R6–R8; variable: Precipitación acumulada en la ventana (suma de P diaria ERA5-Land)
- **Severidad:** No publicada
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Weerasekara, I.; Sinniah, U. R.; et al. (2021). The Influence of Seed Production Environment on Seed Development and Quality of Soybean. Agronomy 11(7), 1430. DOI 10.3390/agronomy11071430  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-11-01430-v3.pdf`  
  Páginas: Weer-100mm: p. PDF 16 / impresa 16 of 19; Weer-fases: p. PDF 5 / impresa 5 of 19

**Citas textuales:**

**[Weer-100mm] umbral de lluvia acumulada** — Weerasekara, I.; Sinniah, U. R.; et al.; p. PDF 16, p. impresa 16 of 19; §5 Conclusions.  
_Re-extraído ahora con PyMuPDF._

> Maternal environmental conditions at the late reproductive stage (R6–R8) are the most critical factor in determining the initial seed quality. Rapid seed deterioration in the field occurred when more than 100 mm of cumulative rainfall coincided with the late reproductive stage.

_Traducción (no es cita):_ Las condiciones ambientales maternas en la etapa reproductiva tardía (R6–R8) son el factor más crítico para la calidad inicial de la semilla. El deterioro rápido de la semilla en campo ocurrió cuando más de 100 mm de lluvia acumulada coincidieron con la etapa reproductiva tardía.

**[Weer-fases] definición de etapas (R6–R8)** — Weerasekara, I.; Sinniah, U. R.; et al.; p. PDF 5, p. impresa 5 of 19; §3.1.  
_Re-extraído ahora con PyMuPDF._

> To understand the influence of production environment, the total growing period (TGP) was partitioned into three stages; (i) seed sowing (SS) to flowering (R1) as vegetative (VEG), (ii) flowering to full seed stage (R6) as early reproductive (ER), and (iii) full seed stage to full mature stage (R8) as late reproductive stage (LR).

_Traducción (no es cita):_ Para entender la influencia del ambiente de producción, el período total de crecimiento (TGP) se dividió en tres etapas: (i) siembra (SS) a floración (R1), vegetativa (VEG); (ii) floración a semilla completa (R6), reproductiva temprana (ER); y (iii) semilla completa a madurez completa (R8), reproductiva tardía (LR).

## R20 — Trigo · Frío en emergencia · EST

- **Fase homologada (tesis):** EST (trigo: Zadoks 00–09)
- **Etapa en la fuente:** «initial seedling stage» (Le Roux 2024)
- **Cobertura:** Equivalente.
- **Umbral, variable y duración según la fuente:** Temperatura media diaria < 2 °C durante más de 2 días sucesivos.
- **Regla en el Excel:** Tmedia < 2 °C; Más de 2 días seguidos (≥ 3 d); variable: Tmedia diaria del aire a 2 m (ERA5-Land)
- **Severidad:** No publicada
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Le Roux, R.; et al. (2024). Scientific Reports 14, 8184. DOI 10.1038/s41598-024-58826-w  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\s41598-024-58826-w.pdf`  
  Páginas: LeRoux-2C: p. PDF 4 / impresa 4; LeRoux-ref33: p. PDF 12 / impresa 12

**Citas textuales:**

**[LeRoux-2C] fase, variable, umbral y duración** — Le Roux, R.; et al.; p. PDF 4, p. impresa 4; Ecoclimatic indicators for wheat.  
_Re-extraído ahora con PyMuPDF._

> Moreover, during the initial seedling stage, low daily average temperatures below 2 °C (during more than 2 successive days) delay emergence and induce poor vigor plantlets33.

_Traducción (no es cita):_ Además, durante la etapa inicial de plántula, temperaturas medias diarias bajas, por debajo de 2 °C (durante más de 2 días sucesivos), retrasan la emergencia e inducen plántulas de poco vigor33.

**[LeRoux-ref33] fuente original citada (no está en carpeta)** — Le Roux, R.; et al.; p. PDF 12, p. impresa 12; References, ref. 33.  
_Re-extraído ahora con PyMuPDF._

> 33. Jame, Y. W. & Cutforth, H. W. Simulating the effects of temperature and seeding depth on germination and emergence of spring wheat. Agric. For. Meteorol. 124, 207–218 (2004).

_Traducción (no es cita):_ Referencia 33: Jame y Cutforth (2004), simulación de los efectos de la temperatura y la profundidad de siembra en la germinación y emergencia del trigo de primavera. No está en la carpeta.

## R21 — Trigo · Helada · VEG

- **Fase homologada (tesis):** VEG (trigo: Zadoks 10–39)
- **Etapa en la fuente:** Alrededor del encañado: de 4 días antes a 20 días después (Feng 1999); «Jointing» (Shroyer 1995)
- **Cobertura:** La fuente cubre menos: solo el entorno del encañado (≈ Z30–39); los 16–20 días después del encañado pueden caer ya en embuche (Z40s, REP-pre).
- **Umbral, variable y duración según la fuente:** Feng: temperatura mínima diaria de estación ≤ −4,2 / −3,5 / −2,5 / −1,0 / 0 °C según días desde el encañado; un día basta (el dato es la Tmin del día con helada). Shroyer: 24 °F durante 2 horas.
- **Regla en el Excel:** Tmin ≤ −4.2 / −3.5 / −2.5 / −1.0 / 0 °C según días desde el encañado; 1 día (sin racha mínima); variable: Tmin diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Feng 1999: solo umbral de helada grave (≥5 % de plantas con espiga joven dañada); Shroyer: «Moderate to severe» (cualitativo)
- **Estado:** Propuesta — decide Paola. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Feng, Y. (冯玉香); He, W.; Sun, Z.; Zhong, X. (1999). 我国冬小麦霜冻害的气候分析 [Climatological study on frost damage of winter wheat in China]. 作物学报 (Acta Agronomica Sinica) 25(3), 335–340. Sin DOI  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Feng_1999_ActaAgronomicaSinica.pdf`  
  Páginas: Feng-umbral: p. PDF 4 / impresa 338; Feng-datos: p. PDF 2 / impresa 336; Feng-etapa: p. PDF 2 / impresa 336; Feng-clases: p. PDF 2 / impresa 336
- Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M. (1995). Spring Freeze Injury to Kansas Wheat. Kansas State University, C-646. Guía de extensión, sin DOI, no revisada por pares  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\spring-freeze-injury-to-kansas-wheat_C646.pdf`  
  Páginas: Shroyer-tabla1: p. PDF 2 / impresa sin número impreso; Shroyer-2h: p. PDF 3 / impresa sin número impreso

**Citas textuales:**

**[Feng-umbral] umbral de Tmin de abrigo por días desde el encañado** — Feng, Y.; p. PDF 4, p. impresa 338; §3.1 讨论 (Discusión).  
_PDF escaneado sin capa de texto: TRANSCRIPCIÓN desde la imagen de la página, cotejada visualmente; no se puede re-extraer._

> 研究小麦霜冻害最好用植株体温，但是气象站不进行这种观测。可供分析的完整资料是最低气温。历史资料表明，同一时段发生重霜冻害的最低气温有高有低，以其中的最高值作为指标，可以得出：拔节期到拔节前 4 天为－4.2℃，拔节后 1～5 天为－3.5℃，6～10 天为－2.5℃，11～15 天为－1.0℃，16～20 天为 0℃。这个指标与陶祖文的研究结果[4]相近。需要指出的是，在各个时段里都有许多日期的最低气温低于上述指标，但是并没有发生重霜冻害，而只发生轻霜冻害。这是因为最低气温与最低叶温之间没有一一对应的函数关系。

_Traducción (no es cita):_ Para estudiar el daño por helada en trigo lo mejor es usar la temperatura de la planta, pero las estaciones meteorológicas no hacen esa observación. El dato completo disponible es la temperatura mínima (del aire). Los registros históricos muestran que, en un mismo período, la temperatura mínima con que ocurrió helada grave fue unas veces más alta y otras más baja; tomando el valor más alto como indicador se obtiene: del encañado hasta 4 días antes del encañado, −4,2 °C; de 1 a 5 días después del encañado, −3,5 °C; de 6 a 10 días, −2,5 °C; de 11 a 15 días, −1,0 °C; de 16 a 20 días, 0 °C. Este indicador es cercano a los resultados de Tao Zuwen [4]. Hay que señalar que en cada período hubo muchos días con temperatura mínima por debajo de estos indicadores sin que ocurriera helada grave, solo helada leve. Esto se debe a que no hay una relación funcional uno a uno entre la temperatura mínima del aire y la temperatura mínima de la hoja.

**[Feng-datos] datos de campo (51 estaciones, 1981–1997)** — Feng, Y.; p. PDF 2, p. impresa 336; §1 研究方法 (Métodos).  
_PDF escaneado sin capa de texto: TRANSCRIPCIÓN desde la imagen de la página, cotejada visualmente; no se puede re-extraer._

> 霜冻害发生日的最低气温、当年的拔节期，霜冻害程度等取自河南、安徽、山东、山西、江苏、陕西等省 51 个农业气象基本观测站 1981～1997 年共 17 年的资料。

_Traducción (no es cita):_ La temperatura mínima del día en que ocurrió la helada, la fecha de encañado de ese año y el grado de daño se tomaron de los registros de 17 años (1981–1997) de 51 estaciones agrometeorológicas básicas de Henan, Anhui, Shandong, Shanxi, Jiangsu, Shaanxi y otras provincias.

**[Shroyer-tabla1] umbral por etapa (2 h)** — Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M.; p. PDF 2, p. impresa sin número impreso; Tabla 1 (Temperatures that cause freeze injury to wheat at spring growth stages).  
_Re-extraído ahora con pdfplumber (tabla leída por filas)._

> Table 1. Temperatures that cause freeze injury to wheat at spring growth stages and symptoms and yield effect of spring freeze injury. Approximate Growth injurious temperature Primary Yield stage (two hours) symptoms effect Tillering 12 F (-11 C) Leaf chlorosis; burning of leaf tips; silage odor; blue cast to fields Slight to moderate Jointing 24 F (-4 C) Death of growing point; leaf yellowing or burning; lesions, Moderate to severe splitting, or bending of lower stem; odor Boot 28 F (-2 C) Floret sterility; spike trapped in boot; damage to lower stem; leaf Moderate to severe discoloration; odor Heading 30 F (-1 C) Floret sterility; white awns or white spikes; damage to lower Severe stem; leaf discoloration Flowering 30 F (-1 C) Floret sterility; white awns or white spikes; damage to lower Severe stem; leaf discoloration Milk 28 F (-2 C) White awns or white spikes; damage to lower stems; leaf Moderate to severe discoloration; shrunken, roughened, or discolored kernels Dough 28 F (-2 C) Shriveled, discolored kernels; poor germination Slight to moderate

_Traducción (no es cita):_ Tabla 1. Temperaturas que causan daño por helada al trigo en las etapas de primavera, síntomas y efecto en el rendimiento. Etapa | Temperatura dañina aproximada (dos horas) | Síntomas principales | Efecto en rendimiento. Macollamiento 12 °F (−11 °C): clorosis, quemado de puntas, olor a ensilaje, tono azul del lote; leve a moderado. Encañado 24 °F (−4 °C): muerte del punto de crecimiento, amarillamiento o quemado de hojas, lesiones, rajadura o doblez del tallo inferior, olor; moderado a severo. Embuche 28 °F (−2 °C): esterilidad de flores, espiga atrapada en la vaina, daño al tallo inferior, decoloración, olor; moderado a severo. Espigado 30 °F (−1 °C): esterilidad de flores, aristas o espigas blancas, daño al tallo inferior, decoloración; severo. Floración 30 °F (−1 °C): igual que espigado; severo. Grano lechoso 28 °F (−2 °C): aristas o espigas blancas, daño a tallos, decoloración, granos arrugados o decolorados; moderado a severo. Grano pastoso 28 °F (−2 °C): granos arrugados y decolorados, baja germinación; leve a moderado.

**[Shroyer-2h] duración (2 h) y alcance** — Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M.; p. PDF 3, p. impresa sin número impreso; Temperatures that Cause Spring Freeze Injury.  
_Re-extraído ahora con PyMuPDF._

> The degree of injury to wheat from spring freezes is influenced by the duration of the low temperatures as well as the low temperature reached. Prolonged exposure to freezing causes much more injury than brief exposure to the same temperature. Temperatures at which injury can be expected, shown in Figure 1 and Table 1, are for two hours of exposure to each temperature. Less injury can be expected from shorter exposure times. Injury might occur at somewhat higher temperatures from longer exposure times.

_Traducción (no es cita):_ El grado de daño al trigo por heladas de primavera depende de la duración de las temperaturas bajas y de la temperatura mínima alcanzada. La exposición prolongada causa mucho más daño que una exposición breve a la misma temperatura. Las temperaturas de la Figura 1 y la Tabla 1 son para dos horas de exposición. Se espera menos daño con exposiciones más cortas, y puede haber daño a temperaturas algo más altas con exposiciones más largas.

**[Feng-etapa] cómo se cuentan los días desde el encañado** — Feng, Y.; p. PDF 2, p. impresa 336; §2.1 霜冻害与生育期.  
_PDF escaneado sin capa de texto: TRANSCRIPCIÓN desde la imagen de la página, cotejada visualmente; no se puede re-extraer._

> 为了分析春季霜冻害在发育进程中不同时段的发生机率，以拔节普遍期为基准，查出每次霜冻害发生日期离当年拔节期的天数，在拔节期前以负值表示，拔节后以正值表示。

_Traducción (no es cita):_ Para analizar la probabilidad de helada primaveral en distintos momentos del desarrollo, se tomó como base la fecha de encañado general (拔节普遍期) y se calculó cuántos días separaban cada helada de la fecha de encañado de ese año: negativos antes del encañado y positivos después.

**[Feng-clases] definición de helada leve y grave** — Feng, Y.; p. PDF 2, p. impresa 336; §1 研究方法.  
_PDF escaneado sin capa de texto: TRANSCRIPCIÓN desde la imagen de la página, cotejada visualmente; no se puede re-extraer._

> 霜冻害按危害程度分为轻重两种，仅仅是叶片受冻干枯，植株受害率达 5%以上的，包括叶尖冻枯、叶片冻枯 2～3 cm、甚至半片叶冻枯等等，都定为轻霜冻害；把幼穗冻坏株率达 5%以上、包括幼穗水浸状、发粘，以后不抽穗、抽出哑铃穗、半截穗、白穗，主茎冻死、大分蘖冻死等都定为重霜冻害。

_Traducción (no es cita):_ Según el daño, la helada se divide en leve y grave. Se clasifica como leve cuando solo se secan por congelación las hojas y la tasa de plantas afectadas llega a 5 % o más (puntas de hoja secas, 2–3 cm de hoja seca o incluso media hoja). Se clasifica como grave cuando 5 % o más de las plantas tienen la espiga joven dañada (espiga embebida o pegajosa, que luego no espiga, espigas en forma de pesa, espigas a medias o blancas) o hay muerte del tallo principal o de macollos grandes.

## R22 — Trigo · Helada · REP-pre

- **Fase homologada (tesis):** REP-pre (trigo: Zadoks 40–59)
- **Etapa en la fuente:** Embuche tardío (Z45) a mitad del espigado (Z55), susceptibilidad máxima desde Z49 (Zheng 2015); «Boot» y «Heading» (Shroyer)
- **Cobertura:** Zheng cubre menos: de Z40 a Z44 no hay susceptibilidad en el modelo.
- **Umbral, variable y duración según la fuente:** Zheng: temperatura mínima de abrigo < 0 °C; cada día cuenta. Shroyer: 28 °F (embuche) y 30 °F (espigado) durante 2 h.
- **Regla en el Excel:** Tmin < 0 °C; Cada día cuenta (sin racha mínima); variable: Tmin diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Modelo: multiplicador de rendimiento 0,1 por día con helada en Z49–Z80 (rampa 1→0,1 en Z45–Z55)
- **Estado:** Propuesta — decide Paola. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Zheng, B.; Chapman, S. C.; Christopher, J. T.; Frederiks, T. M.; Chenu, K. (2015). Frost trends and their estimated impact on yield in the Australian wheatbelt. Journal of Experimental Botany 66(12), 3611–3623. DOI 10.1093/jxb/erv163 (acceso abierto)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Zheng_2015_JXB.pdf`  
  Páginas: Zheng-umbral: p. PDF 3 / impresa 3613; Zheng-calib: p. PDF 3 / impresa 3613
- Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M. (1995). Spring Freeze Injury to Kansas Wheat. Kansas State University, C-646. Guía de extensión, sin DOI, no revisada por pares  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\spring-freeze-injury-to-kansas-wheat_C646.pdf`  
  Páginas: Shroyer-tabla1: p. PDF 2 / impresa sin número impreso; Shroyer-2h: p. PDF 3 / impresa sin número impreso

**Citas textuales:**

**[Zheng-umbral] umbral diario Tmin < 0 °C y ventana Z45–Z89** — Zheng, B.; Chapman, S. C.; Christopher, J. T.; Frederiks, T. M.; Chenu, K.; p. PDF 3, p. impresa 3613; Materials and methods – simulación de daño por helada post-espigamiento.  
_Re-extraído ahora con PyMuPDF._

> To approximate the distributions of exposed heads at susceptible post-heading stages, a multiplier was applied from 1 (i.e. no yield loss) at the late-booting average stage (Z45) followed by a linear decrease to 0.1 (i.e. 90% yield loss) against Zadoks score up to mid-heading (Z55), when almost all tillers would have reached the susceptible post-heading stage (Z49). Maximum susceptibility (i.e. all tillers susceptible) was then maintained until the start of dough development (Z80), with a constant yield multiplier of 0.1 (i.e. 90% yield loss) over the developmental period Z49–Z80 for each day with a minimum temperature below a threshold of 0 °C. After Z80, the yield multiplier was linearly increased over time (from 0.1 to 1) up to the completion of dough development (Z89), which reflected late frost events causing cessation of grain development.

_Traducción (no es cita):_ Para aproximar la distribución de espigas expuestas en etapas susceptibles posteriores al espigado, se aplicó un multiplicador desde 1 (sin pérdida) en el embuche tardío promedio (Z45), con descenso lineal hasta 0,1 (90 % de pérdida) según la escala Zadoks hasta mitad del espigado (Z55), cuando casi todos los macollos habrían llegado a la etapa susceptible (Z49). La susceptibilidad máxima (todos los macollos) se mantuvo hasta el inicio del grano pastoso (Z80), con multiplicador constante de 0,1 (90 % de pérdida) en el período Z49–Z80 por cada día con temperatura mínima por debajo de 0 °C. Después de Z80 el multiplicador subió linealmente (de 0,1 a 1) hasta el fin del grano pastoso (Z89), reflejando heladas tardías que detienen el llenado.

**[Zheng-calib] calibración del umbral (−5 a +2 °C) y medición en abrigo** — Zheng, B.; Chapman, S. C.; Christopher, J. T.; Frederiks, T. M.; Chenu, K.; p. PDF 3, p. impresa 3613; Materials and methods – umbral de abrigo meteorológico.  
_Re-extraído ahora con PyMuPDF._

> Climatic data used to determine frost occurrence were meas-ured within a Stevenson screen as these are the only reliable source of long-term temperature records for the Australian wheatbelt. However, Stevenson screen measurements are typically several degrees higher that the temperatures of the crop canopy during radi-ant frost events (Marcellos and Single, 1975; Frederiks et al., 2011, 2012). Previous studies have shown that after heading, crops are only damaged by canopy temperatures several degrees below 0 °C (Single, 1985; Frederiks et al., 2012). To determine a Stevenson screen tem-perature threshold, temperatures from –5 °C to +2 °C were assessed in 1 °C increments (data not shown). Based on consultation with agronomists and on trial data, it was determined that a threshold temperature of 0 °C best explained major recent incidences of frost damage. Using this threshold, simulations predicted that heading would occur after the main, mid-winter frost risk period when sow-ing dates recommended by industry guidelines were used for known frost-prone areas (Hollaway, 2014; Lush, 2014; Matthews et al., 2014; Shackley et al., 2014; Wheeler, 2014). Hence, a 0 °C threshold was used in the model-based simulations (‘Control’ or ‘Ctrl’).

_Traducción (no es cita):_ Los datos climáticos para determinar heladas se midieron en abrigo Stevenson, la única fuente confiable de registros largos en el cinturón triguero australiano. Sin embargo, el abrigo suele marcar varios grados más que el dosel durante heladas radiativas (Marcellos y Single, 1975; Frederiks et al., 2011, 2012). Estudios previos muestran que, después del espigado, el cultivo solo se daña con temperaturas del dosel varios grados bajo 0 °C (Single, 1985; Frederiks et al., 2012). Para fijar un umbral de abrigo se evaluaron temperaturas de −5 °C a +2 °C en pasos de 1 °C (datos no mostrados). Con base en consultas a agrónomos y en datos de ensayos, se determinó que 0 °C explicaba mejor los principales daños por helada recientes. Con este umbral, las simulaciones predijeron que el espigado ocurriría después del período principal de riesgo de helada invernal cuando se usaban las fechas de siembra recomendadas por la industria en zonas propensas (Hollaway, 2014; Lush, 2014; Matthews et al., 2014; Shackley et al., 2014; Wheeler, 2014). Por eso se usó un umbral de 0 °C en las simulaciones («Control»).

**[Shroyer-tabla1] umbral por etapa (2 h)** — Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M.; p. PDF 2, p. impresa sin número impreso; Tabla 1 (Temperatures that cause freeze injury to wheat at spring growth stages).  
_Re-extraído ahora con pdfplumber (tabla leída por filas)._

> Table 1. Temperatures that cause freeze injury to wheat at spring growth stages and symptoms and yield effect of spring freeze injury. Approximate Growth injurious temperature Primary Yield stage (two hours) symptoms effect Tillering 12 F (-11 C) Leaf chlorosis; burning of leaf tips; silage odor; blue cast to fields Slight to moderate Jointing 24 F (-4 C) Death of growing point; leaf yellowing or burning; lesions, Moderate to severe splitting, or bending of lower stem; odor Boot 28 F (-2 C) Floret sterility; spike trapped in boot; damage to lower stem; leaf Moderate to severe discoloration; odor Heading 30 F (-1 C) Floret sterility; white awns or white spikes; damage to lower Severe stem; leaf discoloration Flowering 30 F (-1 C) Floret sterility; white awns or white spikes; damage to lower Severe stem; leaf discoloration Milk 28 F (-2 C) White awns or white spikes; damage to lower stems; leaf Moderate to severe discoloration; shrunken, roughened, or discolored kernels Dough 28 F (-2 C) Shriveled, discolored kernels; poor germination Slight to moderate

_Traducción (no es cita):_ Tabla 1. Temperaturas que causan daño por helada al trigo en las etapas de primavera, síntomas y efecto en el rendimiento. Etapa | Temperatura dañina aproximada (dos horas) | Síntomas principales | Efecto en rendimiento. Macollamiento 12 °F (−11 °C): clorosis, quemado de puntas, olor a ensilaje, tono azul del lote; leve a moderado. Encañado 24 °F (−4 °C): muerte del punto de crecimiento, amarillamiento o quemado de hojas, lesiones, rajadura o doblez del tallo inferior, olor; moderado a severo. Embuche 28 °F (−2 °C): esterilidad de flores, espiga atrapada en la vaina, daño al tallo inferior, decoloración, olor; moderado a severo. Espigado 30 °F (−1 °C): esterilidad de flores, aristas o espigas blancas, daño al tallo inferior, decoloración; severo. Floración 30 °F (−1 °C): igual que espigado; severo. Grano lechoso 28 °F (−2 °C): aristas o espigas blancas, daño a tallos, decoloración, granos arrugados o decolorados; moderado a severo. Grano pastoso 28 °F (−2 °C): granos arrugados y decolorados, baja germinación; leve a moderado.

**[Shroyer-2h] duración (2 h) y alcance** — Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M.; p. PDF 3, p. impresa sin número impreso; Temperatures that Cause Spring Freeze Injury.  
_Re-extraído ahora con PyMuPDF._

> The degree of injury to wheat from spring freezes is influenced by the duration of the low temperatures as well as the low temperature reached. Prolonged exposure to freezing causes much more injury than brief exposure to the same temperature. Temperatures at which injury can be expected, shown in Figure 1 and Table 1, are for two hours of exposure to each temperature. Less injury can be expected from shorter exposure times. Injury might occur at somewhat higher temperatures from longer exposure times.

_Traducción (no es cita):_ El grado de daño al trigo por heladas de primavera depende de la duración de las temperaturas bajas y de la temperatura mínima alcanzada. La exposición prolongada causa mucho más daño que una exposición breve a la misma temperatura. Las temperaturas de la Figura 1 y la Tabla 1 son para dos horas de exposición. Se espera menos daño con exposiciones más cortas, y puede haber daño a temperaturas algo más altas con exposiciones más largas.

## R23 — Trigo · Helada · FLO

- **Fase homologada (tesis):** FLO (trigo: Zadoks 60–69)
- **Etapa en la fuente:** Dentro de Z49–Z80 (Zheng); «Flowering» (Shroyer)
- **Cobertura:** Zheng cubre más: Z49–Z80 incluye espigado, floración y llenado.
- **Umbral, variable y duración según la fuente:** Zheng: Tmin de abrigo < 0 °C, cada día. Shroyer: 30 °F durante 2 h.
- **Regla en el Excel:** Tmin < 0 °C; Cada día cuenta (sin racha mínima); variable: Tmin diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Modelo: multiplicador 0,1 por día con helada
- **Estado:** Propuesta — decide Paola. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Zheng, B.; Chapman, S. C.; Christopher, J. T.; Frederiks, T. M.; Chenu, K. (2015). Frost trends and their estimated impact on yield in the Australian wheatbelt. Journal of Experimental Botany 66(12), 3611–3623. DOI 10.1093/jxb/erv163 (acceso abierto)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Zheng_2015_JXB.pdf`  
  Páginas: Zheng-umbral: p. PDF 3 / impresa 3613; Zheng-calib: p. PDF 3 / impresa 3613
- Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M. (1995). Spring Freeze Injury to Kansas Wheat. Kansas State University, C-646. Guía de extensión, sin DOI, no revisada por pares  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\spring-freeze-injury-to-kansas-wheat_C646.pdf`  
  Páginas: Shroyer-tabla1: p. PDF 2 / impresa sin número impreso; Shroyer-2h: p. PDF 3 / impresa sin número impreso

**Citas textuales:**

**[Zheng-umbral] umbral diario Tmin < 0 °C y ventana Z45–Z89** — Zheng, B.; Chapman, S. C.; Christopher, J. T.; Frederiks, T. M.; Chenu, K.; p. PDF 3, p. impresa 3613; Materials and methods – simulación de daño por helada post-espigamiento.  
_Re-extraído ahora con PyMuPDF._

> To approximate the distributions of exposed heads at susceptible post-heading stages, a multiplier was applied from 1 (i.e. no yield loss) at the late-booting average stage (Z45) followed by a linear decrease to 0.1 (i.e. 90% yield loss) against Zadoks score up to mid-heading (Z55), when almost all tillers would have reached the susceptible post-heading stage (Z49). Maximum susceptibility (i.e. all tillers susceptible) was then maintained until the start of dough development (Z80), with a constant yield multiplier of 0.1 (i.e. 90% yield loss) over the developmental period Z49–Z80 for each day with a minimum temperature below a threshold of 0 °C. After Z80, the yield multiplier was linearly increased over time (from 0.1 to 1) up to the completion of dough development (Z89), which reflected late frost events causing cessation of grain development.

_Traducción (no es cita):_ Para aproximar la distribución de espigas expuestas en etapas susceptibles posteriores al espigado, se aplicó un multiplicador desde 1 (sin pérdida) en el embuche tardío promedio (Z45), con descenso lineal hasta 0,1 (90 % de pérdida) según la escala Zadoks hasta mitad del espigado (Z55), cuando casi todos los macollos habrían llegado a la etapa susceptible (Z49). La susceptibilidad máxima (todos los macollos) se mantuvo hasta el inicio del grano pastoso (Z80), con multiplicador constante de 0,1 (90 % de pérdida) en el período Z49–Z80 por cada día con temperatura mínima por debajo de 0 °C. Después de Z80 el multiplicador subió linealmente (de 0,1 a 1) hasta el fin del grano pastoso (Z89), reflejando heladas tardías que detienen el llenado.

**[Zheng-calib] calibración del umbral (−5 a +2 °C) y medición en abrigo** — Zheng, B.; Chapman, S. C.; Christopher, J. T.; Frederiks, T. M.; Chenu, K.; p. PDF 3, p. impresa 3613; Materials and methods – umbral de abrigo meteorológico.  
_Re-extraído ahora con PyMuPDF._

> Climatic data used to determine frost occurrence were meas-ured within a Stevenson screen as these are the only reliable source of long-term temperature records for the Australian wheatbelt. However, Stevenson screen measurements are typically several degrees higher that the temperatures of the crop canopy during radi-ant frost events (Marcellos and Single, 1975; Frederiks et al., 2011, 2012). Previous studies have shown that after heading, crops are only damaged by canopy temperatures several degrees below 0 °C (Single, 1985; Frederiks et al., 2012). To determine a Stevenson screen tem-perature threshold, temperatures from –5 °C to +2 °C were assessed in 1 °C increments (data not shown). Based on consultation with agronomists and on trial data, it was determined that a threshold temperature of 0 °C best explained major recent incidences of frost damage. Using this threshold, simulations predicted that heading would occur after the main, mid-winter frost risk period when sow-ing dates recommended by industry guidelines were used for known frost-prone areas (Hollaway, 2014; Lush, 2014; Matthews et al., 2014; Shackley et al., 2014; Wheeler, 2014). Hence, a 0 °C threshold was used in the model-based simulations (‘Control’ or ‘Ctrl’).

_Traducción (no es cita):_ Los datos climáticos para determinar heladas se midieron en abrigo Stevenson, la única fuente confiable de registros largos en el cinturón triguero australiano. Sin embargo, el abrigo suele marcar varios grados más que el dosel durante heladas radiativas (Marcellos y Single, 1975; Frederiks et al., 2011, 2012). Estudios previos muestran que, después del espigado, el cultivo solo se daña con temperaturas del dosel varios grados bajo 0 °C (Single, 1985; Frederiks et al., 2012). Para fijar un umbral de abrigo se evaluaron temperaturas de −5 °C a +2 °C en pasos de 1 °C (datos no mostrados). Con base en consultas a agrónomos y en datos de ensayos, se determinó que 0 °C explicaba mejor los principales daños por helada recientes. Con este umbral, las simulaciones predijeron que el espigado ocurriría después del período principal de riesgo de helada invernal cuando se usaban las fechas de siembra recomendadas por la industria en zonas propensas (Hollaway, 2014; Lush, 2014; Matthews et al., 2014; Shackley et al., 2014; Wheeler, 2014). Por eso se usó un umbral de 0 °C en las simulaciones («Control»).

**[Shroyer-tabla1] umbral por etapa (2 h)** — Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M.; p. PDF 2, p. impresa sin número impreso; Tabla 1 (Temperatures that cause freeze injury to wheat at spring growth stages).  
_Re-extraído ahora con pdfplumber (tabla leída por filas)._

> Table 1. Temperatures that cause freeze injury to wheat at spring growth stages and symptoms and yield effect of spring freeze injury. Approximate Growth injurious temperature Primary Yield stage (two hours) symptoms effect Tillering 12 F (-11 C) Leaf chlorosis; burning of leaf tips; silage odor; blue cast to fields Slight to moderate Jointing 24 F (-4 C) Death of growing point; leaf yellowing or burning; lesions, Moderate to severe splitting, or bending of lower stem; odor Boot 28 F (-2 C) Floret sterility; spike trapped in boot; damage to lower stem; leaf Moderate to severe discoloration; odor Heading 30 F (-1 C) Floret sterility; white awns or white spikes; damage to lower Severe stem; leaf discoloration Flowering 30 F (-1 C) Floret sterility; white awns or white spikes; damage to lower Severe stem; leaf discoloration Milk 28 F (-2 C) White awns or white spikes; damage to lower stems; leaf Moderate to severe discoloration; shrunken, roughened, or discolored kernels Dough 28 F (-2 C) Shriveled, discolored kernels; poor germination Slight to moderate

_Traducción (no es cita):_ Tabla 1. Temperaturas que causan daño por helada al trigo en las etapas de primavera, síntomas y efecto en el rendimiento. Etapa | Temperatura dañina aproximada (dos horas) | Síntomas principales | Efecto en rendimiento. Macollamiento 12 °F (−11 °C): clorosis, quemado de puntas, olor a ensilaje, tono azul del lote; leve a moderado. Encañado 24 °F (−4 °C): muerte del punto de crecimiento, amarillamiento o quemado de hojas, lesiones, rajadura o doblez del tallo inferior, olor; moderado a severo. Embuche 28 °F (−2 °C): esterilidad de flores, espiga atrapada en la vaina, daño al tallo inferior, decoloración, olor; moderado a severo. Espigado 30 °F (−1 °C): esterilidad de flores, aristas o espigas blancas, daño al tallo inferior, decoloración; severo. Floración 30 °F (−1 °C): igual que espigado; severo. Grano lechoso 28 °F (−2 °C): aristas o espigas blancas, daño a tallos, decoloración, granos arrugados o decolorados; moderado a severo. Grano pastoso 28 °F (−2 °C): granos arrugados y decolorados, baja germinación; leve a moderado.

**[Shroyer-2h] duración (2 h) y alcance** — Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M.; p. PDF 3, p. impresa sin número impreso; Temperatures that Cause Spring Freeze Injury.  
_Re-extraído ahora con PyMuPDF._

> The degree of injury to wheat from spring freezes is influenced by the duration of the low temperatures as well as the low temperature reached. Prolonged exposure to freezing causes much more injury than brief exposure to the same temperature. Temperatures at which injury can be expected, shown in Figure 1 and Table 1, are for two hours of exposure to each temperature. Less injury can be expected from shorter exposure times. Injury might occur at somewhat higher temperatures from longer exposure times.

_Traducción (no es cita):_ El grado de daño al trigo por heladas de primavera depende de la duración de las temperaturas bajas y de la temperatura mínima alcanzada. La exposición prolongada causa mucho más daño que una exposición breve a la misma temperatura. Las temperaturas de la Figura 1 y la Tabla 1 son para dos horas de exposición. Se espera menos daño con exposiciones más cortas, y puede haber daño a temperaturas algo más altas con exposiciones más largas.

## R24 — Trigo · Helada · FIL

- **Fase homologada (tesis):** FIL (trigo: Zadoks 70–89)
- **Etapa en la fuente:** Hasta Z80 con susceptibilidad máxima y descenso hasta Z89 (Zheng); «Milk» y «Dough» (Shroyer)
- **Cobertura:** Zheng ≈ equivalente (Z70–Z89).
- **Umbral, variable y duración según la fuente:** Zheng: Tmin de abrigo < 0 °C, cada día. Shroyer: 28 °F durante 2 h.
- **Regla en el Excel:** Tmin < 0 °C; Cada día cuenta (sin racha mínima); variable: Tmin diaria del aire a 2 m (ERA5-Land)
- **Severidad:** Modelo: multiplicador 0,1 hasta Z80; luego sube linealmente hasta 1 en Z89
- **Estado:** Propuesta — decide Paola. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Zheng, B.; Chapman, S. C.; Christopher, J. T.; Frederiks, T. M.; Chenu, K. (2015). Frost trends and their estimated impact on yield in the Australian wheatbelt. Journal of Experimental Botany 66(12), 3611–3623. DOI 10.1093/jxb/erv163 (acceso abierto)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Zheng_2015_JXB.pdf`  
  Páginas: Zheng-umbral: p. PDF 3 / impresa 3613; Zheng-calib: p. PDF 3 / impresa 3613
- Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M. (1995). Spring Freeze Injury to Kansas Wheat. Kansas State University, C-646. Guía de extensión, sin DOI, no revisada por pares  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\spring-freeze-injury-to-kansas-wheat_C646.pdf`  
  Páginas: Shroyer-tabla1: p. PDF 2 / impresa sin número impreso; Shroyer-2h: p. PDF 3 / impresa sin número impreso

**Citas textuales:**

**[Zheng-umbral] umbral diario Tmin < 0 °C y ventana Z45–Z89** — Zheng, B.; Chapman, S. C.; Christopher, J. T.; Frederiks, T. M.; Chenu, K.; p. PDF 3, p. impresa 3613; Materials and methods – simulación de daño por helada post-espigamiento.  
_Re-extraído ahora con PyMuPDF._

> To approximate the distributions of exposed heads at susceptible post-heading stages, a multiplier was applied from 1 (i.e. no yield loss) at the late-booting average stage (Z45) followed by a linear decrease to 0.1 (i.e. 90% yield loss) against Zadoks score up to mid-heading (Z55), when almost all tillers would have reached the susceptible post-heading stage (Z49). Maximum susceptibility (i.e. all tillers susceptible) was then maintained until the start of dough development (Z80), with a constant yield multiplier of 0.1 (i.e. 90% yield loss) over the developmental period Z49–Z80 for each day with a minimum temperature below a threshold of 0 °C. After Z80, the yield multiplier was linearly increased over time (from 0.1 to 1) up to the completion of dough development (Z89), which reflected late frost events causing cessation of grain development.

_Traducción (no es cita):_ Para aproximar la distribución de espigas expuestas en etapas susceptibles posteriores al espigado, se aplicó un multiplicador desde 1 (sin pérdida) en el embuche tardío promedio (Z45), con descenso lineal hasta 0,1 (90 % de pérdida) según la escala Zadoks hasta mitad del espigado (Z55), cuando casi todos los macollos habrían llegado a la etapa susceptible (Z49). La susceptibilidad máxima (todos los macollos) se mantuvo hasta el inicio del grano pastoso (Z80), con multiplicador constante de 0,1 (90 % de pérdida) en el período Z49–Z80 por cada día con temperatura mínima por debajo de 0 °C. Después de Z80 el multiplicador subió linealmente (de 0,1 a 1) hasta el fin del grano pastoso (Z89), reflejando heladas tardías que detienen el llenado.

**[Zheng-calib] calibración del umbral (−5 a +2 °C) y medición en abrigo** — Zheng, B.; Chapman, S. C.; Christopher, J. T.; Frederiks, T. M.; Chenu, K.; p. PDF 3, p. impresa 3613; Materials and methods – umbral de abrigo meteorológico.  
_Re-extraído ahora con PyMuPDF._

> Climatic data used to determine frost occurrence were meas-ured within a Stevenson screen as these are the only reliable source of long-term temperature records for the Australian wheatbelt. However, Stevenson screen measurements are typically several degrees higher that the temperatures of the crop canopy during radi-ant frost events (Marcellos and Single, 1975; Frederiks et al., 2011, 2012). Previous studies have shown that after heading, crops are only damaged by canopy temperatures several degrees below 0 °C (Single, 1985; Frederiks et al., 2012). To determine a Stevenson screen tem-perature threshold, temperatures from –5 °C to +2 °C were assessed in 1 °C increments (data not shown). Based on consultation with agronomists and on trial data, it was determined that a threshold temperature of 0 °C best explained major recent incidences of frost damage. Using this threshold, simulations predicted that heading would occur after the main, mid-winter frost risk period when sow-ing dates recommended by industry guidelines were used for known frost-prone areas (Hollaway, 2014; Lush, 2014; Matthews et al., 2014; Shackley et al., 2014; Wheeler, 2014). Hence, a 0 °C threshold was used in the model-based simulations (‘Control’ or ‘Ctrl’).

_Traducción (no es cita):_ Los datos climáticos para determinar heladas se midieron en abrigo Stevenson, la única fuente confiable de registros largos en el cinturón triguero australiano. Sin embargo, el abrigo suele marcar varios grados más que el dosel durante heladas radiativas (Marcellos y Single, 1975; Frederiks et al., 2011, 2012). Estudios previos muestran que, después del espigado, el cultivo solo se daña con temperaturas del dosel varios grados bajo 0 °C (Single, 1985; Frederiks et al., 2012). Para fijar un umbral de abrigo se evaluaron temperaturas de −5 °C a +2 °C en pasos de 1 °C (datos no mostrados). Con base en consultas a agrónomos y en datos de ensayos, se determinó que 0 °C explicaba mejor los principales daños por helada recientes. Con este umbral, las simulaciones predijeron que el espigado ocurriría después del período principal de riesgo de helada invernal cuando se usaban las fechas de siembra recomendadas por la industria en zonas propensas (Hollaway, 2014; Lush, 2014; Matthews et al., 2014; Shackley et al., 2014; Wheeler, 2014). Por eso se usó un umbral de 0 °C en las simulaciones («Control»).

**[Shroyer-tabla1] umbral por etapa (2 h)** — Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M.; p. PDF 2, p. impresa sin número impreso; Tabla 1 (Temperatures that cause freeze injury to wheat at spring growth stages).  
_Re-extraído ahora con pdfplumber (tabla leída por filas)._

> Table 1. Temperatures that cause freeze injury to wheat at spring growth stages and symptoms and yield effect of spring freeze injury. Approximate Growth injurious temperature Primary Yield stage (two hours) symptoms effect Tillering 12 F (-11 C) Leaf chlorosis; burning of leaf tips; silage odor; blue cast to fields Slight to moderate Jointing 24 F (-4 C) Death of growing point; leaf yellowing or burning; lesions, Moderate to severe splitting, or bending of lower stem; odor Boot 28 F (-2 C) Floret sterility; spike trapped in boot; damage to lower stem; leaf Moderate to severe discoloration; odor Heading 30 F (-1 C) Floret sterility; white awns or white spikes; damage to lower Severe stem; leaf discoloration Flowering 30 F (-1 C) Floret sterility; white awns or white spikes; damage to lower Severe stem; leaf discoloration Milk 28 F (-2 C) White awns or white spikes; damage to lower stems; leaf Moderate to severe discoloration; shrunken, roughened, or discolored kernels Dough 28 F (-2 C) Shriveled, discolored kernels; poor germination Slight to moderate

_Traducción (no es cita):_ Tabla 1. Temperaturas que causan daño por helada al trigo en las etapas de primavera, síntomas y efecto en el rendimiento. Etapa | Temperatura dañina aproximada (dos horas) | Síntomas principales | Efecto en rendimiento. Macollamiento 12 °F (−11 °C): clorosis, quemado de puntas, olor a ensilaje, tono azul del lote; leve a moderado. Encañado 24 °F (−4 °C): muerte del punto de crecimiento, amarillamiento o quemado de hojas, lesiones, rajadura o doblez del tallo inferior, olor; moderado a severo. Embuche 28 °F (−2 °C): esterilidad de flores, espiga atrapada en la vaina, daño al tallo inferior, decoloración, olor; moderado a severo. Espigado 30 °F (−1 °C): esterilidad de flores, aristas o espigas blancas, daño al tallo inferior, decoloración; severo. Floración 30 °F (−1 °C): igual que espigado; severo. Grano lechoso 28 °F (−2 °C): aristas o espigas blancas, daño a tallos, decoloración, granos arrugados o decolorados; moderado a severo. Grano pastoso 28 °F (−2 °C): granos arrugados y decolorados, baja germinación; leve a moderado.

**[Shroyer-2h] duración (2 h) y alcance** — Shroyer, J. P.; Mikesell, M. E.; Paulsen, G. M.; p. PDF 3, p. impresa sin número impreso; Temperatures that Cause Spring Freeze Injury.  
_Re-extraído ahora con PyMuPDF._

> The degree of injury to wheat from spring freezes is influenced by the duration of the low temperatures as well as the low temperature reached. Prolonged exposure to freezing causes much more injury than brief exposure to the same temperature. Temperatures at which injury can be expected, shown in Figure 1 and Table 1, are for two hours of exposure to each temperature. Less injury can be expected from shorter exposure times. Injury might occur at somewhat higher temperatures from longer exposure times.

_Traducción (no es cita):_ El grado de daño al trigo por heladas de primavera depende de la duración de las temperaturas bajas y de la temperatura mínima alcanzada. La exposición prolongada causa mucho más daño que una exposición breve a la misma temperatura. Las temperaturas de la Figura 1 y la Tabla 1 son para dos horas de exposición. Se espera menos daño con exposiciones más cortas, y puede haber daño a temperaturas algo más altas con exposiciones más largas.

## R25 — Trigo · Lluvia / longevidad de semilla · MAT

- **Fase homologada (tesis):** MAT (trigo: Zadoks 90–99)
- **Etapa en la fuente:** Final del secado de maduración, 55–56 días después de antesis (Ellis y Yadav 2016)
- **Cobertura:** Equivalente aproximado; la fecha es la del ensayo.
- **Umbral, variable y duración según la fuente:** Dos lluvias simuladas de 25 mm con 1 día de separación (tratamiento, no umbral).
- **Regla en el Excel:** 25 mm/día (tratamiento); filtro propuesto P ≥ 25 mm/día; 2 días consecutivos; variable: Precipitación diaria (ERA5-Land)
- **Severidad:** No publicada
- **Estado:** No. Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Ellis, R. H.; Yadav, G. (2016). Effect of simulated rainfall during wheat seed development and maturation on subsequent seed longevity is reversible. Seed Science Research 26, 67–76. DOI 10.1017/S0960258515000392  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\effect-of-simulated-rainfall-during-wheat-seed-development-and-maturation-on-subsequent-seed-longevity-is-reversible.pdf`  
  Páginas: Ellis-dosis: p. PDF 2–3 / impresa 68–69; Ellis-rev: p. PDF 8 / impresa 74

**Citas textuales:**

**[Ellis-dosis] tratamiento experimental (2 × 25 mm, 1 d de separación)** — Ellis, R. H.; Yadav, G.; p. PDF 2–3, p. impresa 68–69; Materials and methods (2010), cruza pp. 68–69.  
_Re-extraído ahora con PyMuPDF._

> The rainfall simulation was the equivalent of 25 mm rainfall, with two treatments applied late in seed maturation. Control plants were harvested at 55 (10 August), 56 (11 August) or 62 DAA (17 August). Wetting 1 was at 56 DAA, with seeds harvested 30 min after wetting (nominally 56.02 DAA) and 6 d later (62 DAA). The second treatment comprised two simulated rainfall events 1 d apart, each of 25 mm, [salto de pág. 68→69] at 55 and 56 DAA.

_Traducción (no es cita):_ La simulación de lluvia equivalió a 25 mm, con dos tratamientos aplicados al final de la maduración de la semilla. Las plantas control se cosecharon a los 55 (10 de agosto), 56 (11 de agosto) o 62 DDA (17 de agosto). El mojado 1 fue a los 56 DDA, con cosecha 30 min después (nominalmente 56,02 DDA) y 6 d después (62 DDA). El segundo tratamiento fueron dos lluvias simuladas con 1 d de separación, cada una de 25 mm, a los 55 y 56 DDA.

**[Ellis-rev] amenaza y reversibilidad** — Ellis, R. H.; Yadav, G.; p. PDF 8, p. impresa 74; Discussion.  
_Re-extraído ahora con PyMuPDF._

> rainfall causing ear wetting in planta late in maturation drying, insufficient to result in pre-harvest sprouting, may nonetheless reduce subsequent ex planta air-dry seed longevity immediately, but that in such circumstances the damage can be reversed by delaying harvest to enable a period of re-drying in planta.

_Traducción (no es cita):_ la lluvia que moja la espiga en la planta al final del secado de maduración, insuficiente para causar brotación precosecha, puede reducir de inmediato la longevidad posterior de la semilla seca fuera de la planta, pero en esas circunstancias el daño puede revertirse retrasando la cosecha para permitir un nuevo secado en la planta.

## R26 — Arroz · Frío en establecimiento · EST

- **Fase homologada (tesis):** EST (arroz: BBCH 00–09)
- **Etapa en la fuente:** Semillero, 30 días después de la siembra (Sipaseuth 2007)
- **Cobertura:** La fuente cubre más: 30 días de semillero incluyen el inicio de VEG; es arroz de trasplante.
- **Umbral, variable y duración según la fuente:** Media de la temperatura mínima de los 30 días después de la siembra: < 12 °C crítico; 12–16 °C riesgo; > 16 °C seguro.
- **Regla en el Excel:** < 12 °C = alto riesgo de fracaso; 12–16 °C = riesgo; > 16 °C = seguro; Ventana fija de 30 días; variable: Media de la Tmin diaria en los 30 d después de la siembra (ERA5-Land)
- **Severidad:** Tres clases (seguro, riesgo, fracaso)
- **Estado:** Propuesta — decide Paola (regla nueva). Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Sipaseuth; Basnayake, J.; Fukai, S.; et al. (2007). Opportunities to increasing dry season rice productivity in low temperature affected areas. Field Crops Research 102, 87–97. DOI 10.1016/j.fcr.2007.03.001 (PDF del sitio del laboratorio Linquist, UC Davis)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Sipaseuth_2007_FCR.pdf`  
  Páginas: Sipaseuth-resumen: p. PDF 1 / impresa 87; Sipaseuth-31: p. PDF 4 / impresa 90

**Citas textuales:**

**[Sipaseuth-resumen] umbral Tmin media 30 DDS** — Sipaseuth; Basnayake, J.; Fukai, S.; et al.; p. PDF 1, p. impresa 87; Abstract.  
_Re-extraído ahora con PyMuPDF._

> The mean minimum temperature of 12 8C for 30 days after seeding is critical and temperature below 12 8C resulted in high risk of crop failure due to poor germination, poor seedling growth or insufficient seedlings. Rice needs to be sown at times where the mean minimum temperature exceeds 12 8C or plastic covers are required to protect seedlings.

_Traducción (no es cita):_ La temperatura mínima media de 12 °C durante 30 días después de la siembra es crítica, y por debajo de 12 °C hubo alto riesgo de fracaso del cultivo por mala germinación, mal crecimiento de plántulas o plántulas insuficientes. El arroz debe sembrarse cuando la temperatura mínima media supere 12 °C, o se requieren cubiertas plásticas para proteger las plántulas.

**[Sipaseuth-31] clases de riesgo (12–16 °C)** — Sipaseuth; Basnayake, J.; Fukai, S.; et al.; p. PDF 4, p. impresa 90; §3.1.  
_Re-extraído ahora con PyMuPDF._

> When mean minimum temperatures were below 12 8C, seedling height (Fig. 2a) and dry weight (Fig. 2b) were reduced and in several occasions there was complete failure in germination.Meanminimum temperaturesbetween12 8C and 16 8C for 30dayswere consideredtoberiskyfor establishmentin the nursery and above 16 8C were considered safe from low temperature damage (Fig. 2).

_Traducción (no es cita):_ Cuando la temperatura mínima media fue menor de 12 °C, la altura (Fig. 2a) y el peso seco (Fig. 2b) de la plántula se redujeron y en varias ocasiones hubo fracaso total de la germinación. Temperaturas mínimas medias entre 12 °C y 16 °C durante 30 días se consideraron riesgosas para el establecimiento en el semillero, y por encima de 16 °C se consideraron seguras frente al daño por baja temperatura (Fig. 2).

## R27 — Arroz · Frío (esterilidad) · REP-pre

- **Fase homologada (tesis):** REP-pre (arroz: BBCH 30–59)
- **Etapa en la fuente:** Embuche: de 7 días después de la iniciación de panícula a 7 días antes del 50 % de espigado (Espe 2017)
- **Cobertura:** La fuente cubre menos: excluye la iniciación de panícula y el espigado.
- **Umbral, variable y duración según la fuente:** Grados acumulados de Tmin diaria por debajo del umbral: 17,2 °C (largo), 13 °C (medio), 13,8 °C (corto) (Tabla 1). Sin duración mínima.
- **Regla en el Excel:** Tmin < 13,8 °C (un solo umbral para arroz: valor central de largo 17,2 / medio 13,0 / corto 13,8 °C; decisión de Paola, 5 nov 2026); Sin racha mínima (grados acumulados en la fase); variable: Tmin diaria del aire a 2 m (ERA5-Land); grados acumulados bajo el umbral
- **Severidad:** Pérdida por °C acumulado (Tabla 1, medianas): largo 14.4, medio 64.7, corto 24.2 kg ha⁻¹ °C⁻¹
- **Estado:** Propuesta — decide Paola (regla nueva). Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Espe, M. B.; Hill, J. E.; Hijmans, R. J.; et al. (2017). Point stresses during reproductive stage rather than warming seasonal temperature determine yield in temperate rice. Global Change Biology 23, 4386–4395. DOI 10.1111/gcb.13719 (PDF del sitio del laboratorio Linquist, UC Davis)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Espe_2017_GCB.pdf`  
  Páginas: Espe-umbral: p. PDF 5 / impresa 4390; Espe-tabla1: p. PDF 5 / impresa 4390; Espe-fases: p. PDF 3 / impresa 4388; Espe-disc: p. PDF 8 / impresa 4393

**Citas textuales:**

**[Espe-umbral] umbrales de frío en embuche y calor en floración por tipo de grano** — Espe, M. B.; Hill, J. E.; Hijmans, R. J.; et al.; p. PDF 5, p. impresa 4390; §3 Results.  
_Re-extraído ahora con PyMuPDF._

> The temperature thresholds below or above which the crop experi-enced yield losses varied by grain type (Table 1). Medium and short grain types were estimated to have better tolerance to cooling stress during the booting stage, with temperature thresholds of 13.0°C and 13.8°C, compared to long grain types (17.2°C; Table 1). However, all three grain types were estimated to have similar thresholds (XoC) for cooling stress at flowering (Table 1). Long grain types were estimated to have better tolerance to heat during flow-ering and only experienced yield losses above an estimated thresh-old of 38.7°C, while medium and short grains were estimated to experience yield loss at lower temperatures (35.7 and 36.6°C, respectively) (Table 1), although the total impact of heat during flowering was low (Table 1).

_Traducción (no es cita):_ Los umbrales de temperatura por debajo o por encima de los cuales el cultivo tuvo pérdidas variaron por tipo de grano (Tabla 1). Se estimó que los granos medio y corto toleran mejor el frío en embuche, con umbrales de 13,0 °C y 13,8 °C, frente al grano largo (17,2 °C; Tabla 1). Sin embargo, los tres tipos tuvieron umbrales similares (XoC) para el frío en floración (Tabla 1). El grano largo toleró mejor el calor en floración y solo tuvo pérdidas por encima de 38,7 °C, mientras que el medio y el corto las tuvieron a temperaturas más bajas (35,7 y 36,6 °C) (Tabla 1), aunque el impacto total del calor en floración fue bajo (Tabla 1).

**[Espe-tabla1] umbrales por tipo de grano (columna Threshold °C)** — Espe, M. B.; Hill, J. E.; Hijmans, R. J.; et al.; p. PDF 5, p. impresa 4390; Tabla 1.  
_Re-extraído ahora con PyMuPDF._

> Median 90% CI Threshold Max. accum. (kg ha⁻1 °C⁻1) (°C) (P>°C) Cooling at booting Long 14.4 13.2–15.6 17.2 267 Medium 64.7 59–70.5 13 52 Short 24.2 19.7–28.6 13.8 83 Cooling at flowering Long 38 20.5–56.5 11.9 21 Medium 34.3 7.8–63.1 10.9 11 Short 25.4 4.9–53.5 11.6 18 Heating at flowering Long 70.8 44.9–97.4 38.7 7 Medium 19.7 14.6–24.8 35.7 31 Short 31.7 23.1–40.3 36.6 21

_Traducción (no es cita):_ Tabla 1 (columnas: mediana de pérdida en kg ha⁻¹ °C⁻¹; IC 90 %; umbral en °C; máximo acumulado en °C). Frío en embuche: largo 14,4; 13,2–15,6; 17,2; 267. Medio 64,7; 59–70,5; 13; 52. Corto 24,2; 19,7–28,6; 13,8; 83. Frío en floración: largo 38; 20,5–56,5; 11,9; 21. Medio 34,3; 7,8–63,1; 10,9; 11. Corto 25,4; 4,9–53,5; 11,6; 18. Calor en floración: largo 70,8; 44,9–97,4; 38,7; 7. Medio 19,7; 14,6–24,8; 35,7; 31. Corto 31,7; 23,1–40,3; 36,6; 21.

**[Espe-fases] definición de etapas (embuche, floración)** — Espe, M. B.; Hill, J. E.; Hijmans, R. J.; et al.; p. PDF 3, p. impresa 4388; §2.1.  
_Re-extraído ahora con PyMuPDF._

> For the purposes of defining crop stages, the vegetative stage was assumed to last from the date of planting to panicle initiation, the sensitive boot stage from 7 days after panicle initiation until 7 days prior to 50% heading, the flower-ing stage from 7 days prior to 50% heading to 7 days after 50% heading, and grain-fill from the date of 50% heading to 30 days fol-lowing.

_Traducción (no es cita):_ Para definir las etapas, se asumió que la etapa vegetativa va de la siembra a la iniciación de panícula; la etapa sensible de embuche, de 7 días después de la iniciación de panícula hasta 7 días antes del 50 % de espigado; la floración, de 7 días antes a 7 días después del 50 % de espigado; y el llenado, del 50 % de espigado hasta 30 días después.

**[Espe-disc] advertencia (estaciones vs. campo) y discrepancia 16.3 vs 17.2 °C** — Espe, M. B.; Hill, J. E.; Hijmans, R. J.; et al.; p. PDF 8, p. impresa 4393; Discussion.  
_Re-extraído ahora con PyMuPDF._

> The estimate for medium grain types (14°C) is simi-lar to previous estimates (12.5–15°C; Board et al., 1980). However, due to differences between collecting temperature data in-field, where temperatures are buffered by the large mass of flood water and plant matter verses at near-by weather stations, the estimates here should be taken as approximations. These estimates also con-firm long grain cultivars are not as tolerant of cool temperatures and begin to experience yield loss at a higher temperature (16.3°C; Table 1).

_Traducción (no es cita):_ La estimación para el grano medio (14 °C) es similar a estimaciones previas (12,5–15 °C; Board et al., 1980). Sin embargo, por las diferencias entre medir la temperatura en campo, donde la amortigua la gran masa de agua de inundación y de plantas, y en estaciones cercanas, estas estimaciones deben tomarse como aproximaciones. También confirman que los cultivares de grano largo toleran menos el frío y empiezan a perder rendimiento a una temperatura más alta (16,3 °C; Tabla 1).

**Valores en conflicto:** Espe 2017: la Tabla 1 y los resultados dan 17,2 °C para grano largo en embuche; la discusión dice 16,3 °C. También: la discusión da 14 °C para grano medio y la tabla 13 °C. Las citas de ambos textos están arriba: Espe-umbral, Espe-tabla1, Espe-disc.

## R28 — Arroz · Frío (esterilidad) · FLO

- **Fase homologada (tesis):** FLO (arroz: BBCH 60–69)
- **Etapa en la fuente:** Floración: de 7 días antes a 7 días después del 50 % de espigado (Espe 2017)
- **Cobertura:** La fuente cubre otra ventana: empieza 7 días antes del 50 % de espigado (parte del espigado, BBCH 50s, REP-pre).
- **Umbral, variable y duración según la fuente:** Grados acumulados de Tmin diaria por debajo de 11,9 °C (largo), 10,9 °C (medio), 11,6 °C (corto) (Tabla 1). Sin duración mínima.
- **Regla en el Excel:** Tmin < 11,6 °C (un solo umbral para arroz: valor central de largo 11,9 / medio 10,9 / corto 11,6 °C; decisión de Paola, 5 nov 2026); Sin racha mínima (grados acumulados en la fase); variable: Tmin diaria del aire a 2 m (ERA5-Land); grados acumulados bajo el umbral
- **Severidad:** Pérdida por °C acumulado (Tabla 1, medianas): largo 38, medio 34.3, corto 25.4 kg ha⁻¹ °C⁻¹
- **Estado:** Propuesta — decide Paola (regla nueva). Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Espe, M. B.; Hill, J. E.; Hijmans, R. J.; et al. (2017). Point stresses during reproductive stage rather than warming seasonal temperature determine yield in temperate rice. Global Change Biology 23, 4386–4395. DOI 10.1111/gcb.13719 (PDF del sitio del laboratorio Linquist, UC Davis)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Espe_2017_GCB.pdf`  
  Páginas: Espe-tabla1: p. PDF 5 / impresa 4390; Espe-umbral: p. PDF 5 / impresa 4390; Espe-fases: p. PDF 3 / impresa 4388; Espe-disc: p. PDF 8 / impresa 4393

**Citas textuales:**

**[Espe-tabla1] umbrales por tipo de grano (columna Threshold °C)** — Espe, M. B.; Hill, J. E.; Hijmans, R. J.; et al.; p. PDF 5, p. impresa 4390; Tabla 1.  
_Re-extraído ahora con PyMuPDF._

> Median 90% CI Threshold Max. accum. (kg ha⁻1 °C⁻1) (°C) (P>°C) Cooling at booting Long 14.4 13.2–15.6 17.2 267 Medium 64.7 59–70.5 13 52 Short 24.2 19.7–28.6 13.8 83 Cooling at flowering Long 38 20.5–56.5 11.9 21 Medium 34.3 7.8–63.1 10.9 11 Short 25.4 4.9–53.5 11.6 18 Heating at flowering Long 70.8 44.9–97.4 38.7 7 Medium 19.7 14.6–24.8 35.7 31 Short 31.7 23.1–40.3 36.6 21

_Traducción (no es cita):_ Tabla 1 (columnas: mediana de pérdida en kg ha⁻¹ °C⁻¹; IC 90 %; umbral en °C; máximo acumulado en °C). Frío en embuche: largo 14,4; 13,2–15,6; 17,2; 267. Medio 64,7; 59–70,5; 13; 52. Corto 24,2; 19,7–28,6; 13,8; 83. Frío en floración: largo 38; 20,5–56,5; 11,9; 21. Medio 34,3; 7,8–63,1; 10,9; 11. Corto 25,4; 4,9–53,5; 11,6; 18. Calor en floración: largo 70,8; 44,9–97,4; 38,7; 7. Medio 19,7; 14,6–24,8; 35,7; 31. Corto 31,7; 23,1–40,3; 36,6; 21.

**[Espe-umbral] umbrales de frío en embuche y calor en floración por tipo de grano** — Espe, M. B.; Hill, J. E.; Hijmans, R. J.; et al.; p. PDF 5, p. impresa 4390; §3 Results.  
_Re-extraído ahora con PyMuPDF._

> The temperature thresholds below or above which the crop experi-enced yield losses varied by grain type (Table 1). Medium and short grain types were estimated to have better tolerance to cooling stress during the booting stage, with temperature thresholds of 13.0°C and 13.8°C, compared to long grain types (17.2°C; Table 1). However, all three grain types were estimated to have similar thresholds (XoC) for cooling stress at flowering (Table 1). Long grain types were estimated to have better tolerance to heat during flow-ering and only experienced yield losses above an estimated thresh-old of 38.7°C, while medium and short grains were estimated to experience yield loss at lower temperatures (35.7 and 36.6°C, respectively) (Table 1), although the total impact of heat during flowering was low (Table 1).

_Traducción (no es cita):_ Los umbrales de temperatura por debajo o por encima de los cuales el cultivo tuvo pérdidas variaron por tipo de grano (Tabla 1). Se estimó que los granos medio y corto toleran mejor el frío en embuche, con umbrales de 13,0 °C y 13,8 °C, frente al grano largo (17,2 °C; Tabla 1). Sin embargo, los tres tipos tuvieron umbrales similares (XoC) para el frío en floración (Tabla 1). El grano largo toleró mejor el calor en floración y solo tuvo pérdidas por encima de 38,7 °C, mientras que el medio y el corto las tuvieron a temperaturas más bajas (35,7 y 36,6 °C) (Tabla 1), aunque el impacto total del calor en floración fue bajo (Tabla 1).

**[Espe-fases] definición de etapas (embuche, floración)** — Espe, M. B.; Hill, J. E.; Hijmans, R. J.; et al.; p. PDF 3, p. impresa 4388; §2.1.  
_Re-extraído ahora con PyMuPDF._

> For the purposes of defining crop stages, the vegetative stage was assumed to last from the date of planting to panicle initiation, the sensitive boot stage from 7 days after panicle initiation until 7 days prior to 50% heading, the flower-ing stage from 7 days prior to 50% heading to 7 days after 50% heading, and grain-fill from the date of 50% heading to 30 days fol-lowing.

_Traducción (no es cita):_ Para definir las etapas, se asumió que la etapa vegetativa va de la siembra a la iniciación de panícula; la etapa sensible de embuche, de 7 días después de la iniciación de panícula hasta 7 días antes del 50 % de espigado; la floración, de 7 días antes a 7 días después del 50 % de espigado; y el llenado, del 50 % de espigado hasta 30 días después.

**[Espe-disc] advertencia (estaciones vs. campo) y discrepancia 16.3 vs 17.2 °C** — Espe, M. B.; Hill, J. E.; Hijmans, R. J.; et al.; p. PDF 8, p. impresa 4393; Discussion.  
_Re-extraído ahora con PyMuPDF._

> The estimate for medium grain types (14°C) is simi-lar to previous estimates (12.5–15°C; Board et al., 1980). However, due to differences between collecting temperature data in-field, where temperatures are buffered by the large mass of flood water and plant matter verses at near-by weather stations, the estimates here should be taken as approximations. These estimates also con-firm long grain cultivars are not as tolerant of cool temperatures and begin to experience yield loss at a higher temperature (16.3°C; Table 1).

_Traducción (no es cita):_ La estimación para el grano medio (14 °C) es similar a estimaciones previas (12,5–15 °C; Board et al., 1980). Sin embargo, por las diferencias entre medir la temperatura en campo, donde la amortigua la gran masa de agua de inundación y de plantas, y en estaciones cercanas, estas estimaciones deben tomarse como aproximaciones. También confirman que los cultivares de grano largo toleran menos el frío y empiezan a perder rendimiento a una temperatura más alta (16,3 °C; Tabla 1).

## R29 — Soya · Calor · FIL

- **Fase homologada (tesis):** FIL (soya: R5, R6–R7)
- **Etapa en la fuente:** «grain filling» del modelo de Hoffman 2020
- **Cobertura:** La fuente cubre mucho más: los autores reconocen que su llenado representa todas las fases reproductivas R1–R8.
- **Umbral, variable y duración según la fuente:** Media de la Tmax diaria en la fase; umbral aproximado 30 °C para soya (29 °C maíz). Sin duración: es un promedio de la fase.
- **Regla en el Excel:** Tmax media de la fase > 30 °C (valor fijo; la fuente dice «approximately 30 °C»; decisión de Paola, 5 nov 2026); Toda la fase (promedio); variable: Media de la Tmax diaria en la fase (ERA5-Land)
- **Severidad:** No publicada como clases
- **Estado:** Propuesta — decide Paola (regla nueva). Validación Paola: VALIDADA (decisión de Paola, 5 nov 2026: «Sí, las 28»).

**Fuentes:**

- Hoffman, A. L.; Kemanian, A. R.; Forest, C. E. (2020). The response of maize, sorghum, and soybean yield to growing-phase climate revealed with machine learning. Environmental Research Letters 15, 094013. DOI 10.1088/1748-9326/ab7b22 (acceso abierto)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Hoffman_2020_ERL.pdf`  
  Páginas: Hoffman-gf: p. PDF 9 / impresa 8; Hoffman-resumen: p. PDF 2 / impresa 1; Hoffman-fases: p. PDF 3 / impresa 2; Hoffman-R1R8: p. PDF 17 / impresa 16

**Citas textuales:**

**[Hoffman-gf] umbral referido a TMAX-GF** — Hoffman, A. L.; Kemanian, A. R.; Forest, C. E.; p. PDF 9, p. impresa 8; Discussion.  
_Re-extraído ahora con PyMuPDF._

> Modeled yield responses of maize and soybean yields to TMAX-GF compare favorably to those found in other work wherein yields increase slowly with increasing temperature until a threshold and then fall off rapidly (Schlenker and Roberts 2009, Lobell et al 2014). We estimate the threshold temperatures at approximately 29 ◦C and 30 ◦C for maize and soy-bean, respectively.

_Traducción (no es cita):_ Las respuestas modeladas del rendimiento de maíz y soya a TMAX-GF se comparan bien con las de otros trabajos, en que el rendimiento sube lentamente con la temperatura hasta un umbral y luego cae rápido (Schlenker y Roberts 2009, Lobell et al. 2014). Estimamos las temperaturas umbral en aproximadamente 29 °C y 30 °C para maíz y soya, respectivamente.

**[Hoffman-resumen] umbral 30 °C soya** — Hoffman, A. L.; Kemanian, A. R.; Forest, C. E.; p. PDF 2, p. impresa 1; Abstract.  
_Re-extraído ahora con PyMuPDF._

> Responses to climate confirm prior findings revealing threshold-like responses to high temperature (yield decrease sharply when maximum temperature exceed 29 ◦C and 30 ◦C for maize and soybean), and reveal a higher temperature tolerance for sorghum, whose yield decreases gradually as maximum temperature exceeds 32.5 ◦C.

_Traducción (no es cita):_ Las respuestas al clima confirman hallazgos previos de respuestas de tipo umbral a la alta temperatura (el rendimiento cae bruscamente cuando la temperatura máxima supera 29 °C en maíz y 30 °C en soya) y revelan una mayor tolerancia del sorgo, cuyo rendimiento disminuye gradualmente cuando la temperatura máxima supera 32,5 °C.

**[Hoffman-fases] variables por fase (promedios)** — Hoffman, A. L.; Kemanian, A. R.; Forest, C. E.; p. PDF 3, p. impresa 2; §2.1.  
_Re-extraído ahora con PyMuPDF._

> For each climate variable in table 1, we computed four predictors based on phenological phases defined as establishment, critical window, and grain filling, and averages for the entire cycle from planting to maturity.

_Traducción (no es cita):_ Para cada variable climática de la Tabla 1 calculamos cuatro predictores según fases fenológicas definidas como establecimiento, ventana crítica y llenado, más los promedios de todo el ciclo de siembra a madurez.

**[Hoffman-R1R8] la «fase de llenado» de soya cubre R1–R8** — Hoffman, A. L.; Kemanian, A. R.; Forest, C. E.; p. PDF 17, p. impresa 16; Apéndice A.3.1.  
_Re-extraído ahora con PyMuPDF._

> Our results suggest that we are still capturing the establishment, or early-season, signal with the modeled critical window. In other words, the veget-ative (establishment) phase for soybean is likely not long enough in our model. Therefore, the phase which we intended to be the critical window is actu-ally contained within the grain filling phase, and the grain filling phase effectively represents all of soybean’s reproductive phases (R1-R8).

_Traducción (no es cita):_ Nuestros resultados sugieren que todavía capturamos la señal del establecimiento (inicio de temporada) dentro de la ventana crítica modelada. Es decir, la fase vegetativa (establecimiento) de la soya probablemente no es lo bastante larga en nuestro modelo. Por eso la fase que pretendíamos como ventana crítica queda contenida en la fase de llenado, y la fase de llenado representa en la práctica todas las fases reproductivas de la soya (R1-R8).

## R30 — Maíz (aplicable a los 4) · Sequía: racha seca · Todas las de la temporada (EST–MAT)

- **Fase homologada (tesis):** Todas (EST–MAT)
- **Etapa en la fuente:** Período j (anual) en la definición ETCCDI
- **Cobertura:** La fuente es un índice climático anual, no de cultivo; aplicarlo dentro de cada fase es adaptación nuestra.
- **Umbral, variable y duración según la fuente:** Precipitación diaria < 1 mm; se cuenta la racha más larga de días consecutivos. No da duración mínima ni umbral de daño.
- **Regla en el Excel:** P diaria < 1 mm; Días consecutivos; se cuenta la racha | DURACIÓN MÍNIMA (búsqueda 4 nov 2026): SIN FUENTE para un mínimo fijo. Ningún PDF abierto da una duración mínima de racha seca calibrada con rendimiento de maíz por fase. Lo más cercano: Fischer et al. 2013 calcula una duración crítica = agua disponible / ETP (8.2, 10.2 y 17.1 d en tres sitios de Tanzania), sin validar con rendimiento.; variable: total_precipitation_sum (mm/día)
- **Severidad:** No definida por la fuente
- **Estado:** Sí (regla nueva). Validación Paola: Aprobada en el chat el 4 nov 2026 («Sequía sí, así»).

**Fuentes:**

- ETCCDI (Expert Team on Climate Change Detection and Indices). Lista de los 27 índices. https://etccdi.pacificclimate.org/list_27_indices.shtml (consultada el 4 nov 2026)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\ETCCDI_27_indices.html`  
  Páginas: ETCCDI-cdd: p. PDF sin PDF (HTML) / impresa página web, sin paginación
- Fischer, B. M. C.; Mul, M. L.; Savenije, H. H. G. (2013). Determining spatial variability of dry spells: a Markov-based method, applied to the Makanya catchment, Tanzania. Hydrology and Earth System Sciences 17, 2161–2170. DOI 10.5194/hess-17-2161-2013 (acceso abierto)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Fischer_2013_HESS.pdf`  
  Páginas: Fischer-def: p. PDF 4 / impresa 2164; Fischer-ncr: p. PDF 6 / impresa 2166; Fischer-maiz: p. PDF 6 / impresa 2166; Fischer-tabla4: p. PDF 8 / impresa 2168; Fischer-concl: p. PDF 9 / impresa 2169

**Citas textuales:**

**[ETCCDI-cdd] definición de racha seca** — ETCCDI; p. PDF sin PDF (HTML), p. impresa página web, sin paginación; Entrada CDD.  
_Sin PDF: texto copiado del HTML guardado (re-extraído ahora)._

> CDD. Maximum length of dry spell, maximum number of consecutive days with RR < 1mm : Let RR ij be the daily precipitation amount on day i in period j . Count the largest number of consecutive days where: RR ij < 1mm

_Traducción (no es cita):_ CDD. Duración máxima de racha seca: número máximo de días consecutivos con RR < 1 mm. Sea RRij la precipitación diaria del día i en el período j. Se cuenta el mayor número de días consecutivos en que RRij < 1 mm.

**[Fischer-def] definición de racha seca y umbral de día seco** — Fischer, B. M. C.; Mul, M. L.; Savenije, H. H. G.; p. PDF 4, p. impresa 2164; §2.3.  
_Re-extraído ahora con PyMuPDF._

> Dry spells are defined as a number of consecutive days with-out rainfall, and consecutive days with rainfall are called wet spells. In this study we used a threshold of 0.1 mm day−1 to distinguish between a wet and a dry day, similar to De Groen (2002), Madamombe (1994) and El-Seed (1987). This threshold was used as we focussed on the meteorological dry spells. In future applications the threshold set should be com-patible with the field of application and their end users (e.g. for agricultural applications a threshold of 1 mm day−1 may be more appropriate, e.g. Enfors and Gordon, 2007, used 0.8 mm day−1).

_Traducción (no es cita):_ Las rachas secas se definen como un número de días consecutivos sin lluvia, y los días consecutivos con lluvia se llaman rachas húmedas. En este estudio usamos un umbral de 0,1 mm/día para distinguir un día húmedo de uno seco, como De Groen (2002), Madamombe (1994) y El-Seed (1987). Este umbral se usó porque nos enfocamos en rachas secas meteorológicas. En aplicaciones futuras el umbral debe ser compatible con el campo de aplicación y sus usuarios (p. ej., para aplicaciones agrícolas un umbral de 1 mm/día puede ser más apropiado; Enfors y Gordon, 2007, usaron 0,8 mm/día).

**[Fischer-ncr] duración crítica = agua disponible / ETP** — Fischer, B. M. C.; Mul, M. L.; Savenije, H. H. G.; p. PDF 6, p. impresa 2166; §2.5.  
_Re-extraído ahora con PyMuPDF._

> The critical dry spell length is the time period that the ecosys-tem can bridge. It is the ratio between the available soil mois-ture and the transpiration rate of the vegetation (see Eq. 11). If the transpiration demand is larger than the available soil moisture, the development of the plant will be hampered or, in the worst case, the plant will wilt. The critical dry spell length ncr (days) can thus be calculated at every point in space as the ratio of the available soil moisture θ (mm) to the potential evaporation Ep (mm day−1):

_Traducción (no es cita):_ La duración crítica de una racha seca es el período que el ecosistema puede sostener. Es la razón entre la humedad disponible del suelo y la tasa de transpiración de la vegetación (Ec. 11). Si la demanda de transpiración supera la humedad disponible, el desarrollo de la planta se afecta o, en el peor caso, la planta se marchita. La duración crítica ncr (días) se puede calcular en cada punto como la razón entre la humedad disponible del suelo θ (mm) y la evaporación potencial Ep (mm/día):

**[Fischer-maiz] supuesto para maíz (raíz 500 mm, 50 mm disponibles)** — Fischer, B. M. C.; Mul, M. L.; Savenije, H. H. G.; p. PDF 6, p. impresa 2166; §2.5.  
_Re-extraído ahora con PyMuPDF._

> To estimate the available soil moisture stock, it is assumed that maize, the staple crop grown in the area, has a root depth of approximately 500 mm. With the assumption that at the beginning of the rainy seasons this stock has been replen-ished, the available soil moisture for the crop is around 10 % (50 mm).

_Traducción (no es cita):_ Para estimar la reserva de humedad disponible se supone que el maíz, cultivo principal de la zona, tiene una profundidad de raíz de unos 500 mm. Suponiendo que al inicio de la temporada de lluvias esa reserva está recargada, la humedad disponible para el cultivo es de alrededor de 10 % (50 mm).

**[Fischer-tabla4] duración crítica por sitio (8.2 / 10.2 / 17.1 d)** — Fischer, B. M. C.; Mul, M. L.; Savenije, H. H. G.; p. PDF 8, p. impresa 2168; Tabla 4.  
_Re-extraído ahora con PyMuPDF._

> Table 4. Values of critical dry spell length ncr for the three locations indicated in Fig. 4. location θ D θ available Ep ncr available root depth to crop [mm d−1] [d] [%] [mm] [mm] 1 8 500 40 4.9 8.2 2 10 500 50 4.9 10.2 3 12 500 60 3.5 17.1

_Traducción (no es cita):_ Tabla 4. Duración crítica de racha seca ncr en los tres sitios de la Fig. 4. Sitio | θ disponible (%) | profundidad de raíz (mm) | θ disponible para el cultivo (mm) | Ep (mm/d) | ncr (d): 1 | 8 | 500 | 40 | 4,9 | 8,2; 2 | 10 | 500 | 50 | 4,9 | 10,2; 3 | 12 | 500 | 60 | 3,5 | 17,1.

**[Fischer-concl] rango de duración crítica 8–17 d** — Fischer, B. M. C.; Mul, M. L.; Savenije, H. H. G.; p. PDF 9, p. impresa 2169; Conclusions.  
_Re-extraído ahora con PyMuPDF._

> This is both the consequence of vary-ing soil conditions and potential evaporation, which lead to a wide range of critical dry spell length, between 8–17 days.

_Traducción (no es cita):_ Esto es consecuencia de la variación del suelo y de la evaporación potencial, que llevan a un rango amplio de duración crítica de racha seca, entre 8 y 17 días.

**Valores en conflicto:** No hay duración mínima con fuente: ETCCDI no fija mínimo y Fischer 2013 calcula una duración crítica que varía entre 8 y 17 días según el suelo y la ETP. Las citas de ambos textos están arriba: ETCCDI-cdd, Fischer-concl.

## R31 — Maíz (soya: 30 °C en la misma fuente) · Calor continuo: días sobre 29 °C (base del EDD29) · Todas las de la temporada (EST–MAT)

- **Fase homologada (tesis):** Todas (EST–MAT)
- **Etapa en la fuente:** Temporada de crecimiento marzo–agosto (maíz y soya) en EE. UU.
- **Cobertura:** La fuente usa toda la temporada, no fases.
- **Umbral, variable y duración según la fuente:** Exposición (fracción del día) a temperaturas por encima de 29 °C (maíz) o 30 °C (soya), interpolada entre Tmin y Tmax; no define rachas ni días consecutivos.
- **Regla en el Excel:** 29 °C (maíz); 30 °C (soya); Días consecutivos con Tmax > 29 °C (adaptación); la fuente usa °C·día | DURACIÓN MÍNIMA (búsqueda 4 nov 2026): SIN FUENTE para 29 °C (maíz) ni 30 °C (soya); Schlenker y Roberts no definen rachas. La única duración calibrada con daño es de Li 2025b (K-means sobre 184 registros), pero con umbrales de 32.7–34.8 °C, no 29 °C: leve desde 3 d (texto) o 2.3–3.7 d según la etapa (Tabla 2).; variable: temperature_2m_max (°C); EDD29 con Tmax y Tmin
- **Severidad:** La fuente da el efecto: un día a 40 °C en lugar de 29 °C ≈ −7 % de rendimiento
- **Estado:** Sí (regla nueva). Validación Paola: Aprobada en el chat el 4 nov 2026 («EDD29 también con esas fuentes»).

**Fuentes:**

- Schlenker, W.; Roberts, M. J. (2009). Nonlinear temperature effects indicate severe damages to U.S. crop yields under climate change. PNAS 106(37), 15594–15598. DOI 10.1073/pnas.0906865106 (texto completo PMC2747166)  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\01_Fenología y umbrales\nuevas_2026-11\Schlenker_Roberts_2009_PNAS_PMC2747166.html`  
  Páginas: SR-resumen: p. PDF sin PDF (HTML) / impresa HTML de PMC; corresponde a p. impresa 15594; SR-umbral: p. PDF sin PDF (HTML) / impresa HTML de PMC; página impresa no verificada; SR-ejemplo: p. PDF sin PDF (HTML) / impresa HTML de PMC; página impresa no verificada
- Li, Q.; et al. (2025b). Agronomy 15(7), 1545. DOI 10.3390/agronomy15071545  
  Archivo: `C:\Users\paola\Tesis\04_Bibliography\Fenología 24 amenazasa\agronomy-15-01545.pdf`  
  Páginas: LiB-dur: p. PDF 4 / impresa 4 of 17; LiB-sev-texto: p. PDF 7 / impresa 7 of 17; LiB-resumen: p. PDF 1 / impresa 1 of 17; LiB-tabla2: p. PDF 7 / impresa 7 of 17

**Citas textuales:**

**[SR-resumen] umbrales 29/30 °C** — Schlenker, W.; Roberts, M. J.; p. PDF sin PDF (HTML), p. impresa HTML de PMC; corresponde a p. impresa 15594; Abstract.  
_Sin PDF: texto copiado del HTML guardado (re-extraído ahora)._

> We find that yields increase with temperature up to 29° C for corn, 30° C for soybeans, and 32° C for cotton but that temperatures above these thresholds are very harmful.

_Traducción (no es cita):_ Encontramos que el rendimiento aumenta con la temperatura hasta 29 °C en maíz, 30 °C en soya y 32 °C en algodón, pero que las temperaturas por encima de esos umbrales son muy dañinas.

**[SR-umbral] umbral crítico por cultivo** — Schlenker, W.; Roberts, M. J.; p. PDF sin PDF (HTML), p. impresa HTML de PMC; página impresa no verificada; Results.  
_Sin PDF: texto copiado del HTML guardado (re-extraído ahora)._

> For corn, the critical threshold temperature is 29° C; for soybeans it is 30° C; and for cotton it is 32° C.

_Traducción (no es cita):_ En maíz, la temperatura umbral crítica es 29 °C; en soya, 30 °C; y en algodón, 32 °C.

**[SR-ejemplo] magnitud del daño y temporada** — Schlenker, W.; Roberts, M. J.; p. PDF sin PDF (HTML), p. impresa HTML de PMC; página impresa no verificada; Results (Fig. 1).  
_Sin PDF: texto copiado del HTML guardado (re-extraído ahora)._

> substituting a full day (24 h) at 29° C temperature with a full day at 40° C temperature results in a predicted yield decline of ≈7%, holding all else the same. The green histogram shows the average exposure to each one-degree Celsius interval during the growing season (March–August for corn and soybeans and April–October for cotton).

_Traducción (no es cita):_ sustituir un día completo (24 h) a 29 °C por un día completo a 40 °C produce una caída de rendimiento predicha de ≈7 %, con todo lo demás igual. El histograma verde muestra la exposición promedio a cada intervalo de 1 °C durante la temporada (marzo–agosto para maíz y soya, y abril–octubre para algodón).

**[LiB-dur] duración mínima de inclusión (≥2 d)** — Li, Q.; et al.; p. PDF 4, p. impresa 4 of 17; §2.3.2 K-Means Clustering Algorithm.  
_Re-extraído ahora con PyMuPDF._

> In this study, we focused on heat damage events lasting two days or more, which were temporally aggregated according to different growth stages (V0, VE, V6, VT, R1, R3, and R6).

_Traducción (no es cita):_ En este estudio nos centramos en eventos de daño por calor de dos días o más, que se agregaron en el tiempo según las distintas etapas de crecimiento (V0, VE, V6, VT, R1, R3 y R6).

**[LiB-sev-texto] severidad por duración (texto, días enteros)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; §3.1.1 Constructing Grade Indicators for Heat Damage.  
_Re-extraído ahora con PyMuPDF._

> The thresholds for these categories were determined as follows: 3–5 days for mild heat damage, 5–8 days for moderate heat damage, and more than 8 days for severe heat damage.

_Traducción (no es cita):_ Los umbrales de estas categorías se determinaron así: 3–5 días para daño leve, 5–8 días para daño moderado y más de 8 días para daño severo.

**[LiB-resumen] clases de duración en el resumen (moderado 6–8 d)** — Li, Q.; et al.; p. PDF 1, p. impresa 1 of 17; Abstract.  
_Re-extraído ahora con PyMuPDF._

> The results identified that the duration thresholds of mild, moderate, and severe heat damage at different growth stages of summer maize are 3–5 days, 6–8 days, and more than 8 days, respectively.

_Traducción (no es cita):_ Los resultados identificaron que los umbrales de duración del daño por calor leve, moderado y severo en las distintas etapas del maíz de verano son 3–5 días, 6–8 días y más de 8 días, respectivamente.

**[LiB-tabla2] severidad por duración (tabla, decimales)** — Li, Q.; et al.; p. PDF 7, p. impresa 7 of 17; Tabla 2 (The summer maize heat damage grade indicators).  
_Re-extraído ahora con PyMuPDF._

> Table 2. The summer maize heat damage grade indicators. The Growth Stages of Summer Maize Heat Damage Grade Indicators Mild/d Moderate/d Severe/d V0–VE 2.5~4.7 4.7~7.7 >7.7 VE–V6 3.7~5.9 5.9~8.6 >8.6 V6–VT 3.5~5.4 5.4~7.5 >7.5 VT–R1 2.3~4.5 4.5~7.9 >7.9 R1–R3 2.8~4.7 4.7~8.3 >8.3 R3–R6 3.2~5.3 5.3~8.1 >8.1

_Traducción (no es cita):_ Tabla 2. Indicadores de grado de daño por calor del maíz de verano. Etapa | Leve (d) | Moderado (d) | Severo (d): V0–VE 2,5~4,7 | 4,7~7,7 | >7,7; VE–V6 3,7~5,9 | 5,9~8,6 | >8,6; V6–VT 3,5~5,4 | 5,4~7,5 | >7,5; VT–R1 2,3~4,5 | 4,5~7,9 | >7,9; R1–R3 2,8~4,7 | 4,7~8,3 | >8,3; R3–R6 3,2~5,3 | 5,3~8,1 | >8,1.

**Valores en conflicto:** La duración con fuente (Li 2025b, clase leve desde 3 d o 2,3–3,7 d según la etapa) se calibró con umbrales de 32,7–34,8 °C, no con 29 °C; Schlenker y Roberts no definen rachas. Además, Li 2025b da la clase moderada como 5–8 d en resultados y 6–8 d en el resumen. Las citas de ambos textos están arriba: LiB-sev-texto, LiB-resumen, LiB-tabla2, SR-umbral.

