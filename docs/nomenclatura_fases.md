# Nomenclatura de fases y equivalencias entre cultivos

Decisión del 1 nov 2026. Semilla para la futura ontología de la tesis.

## Regla

Las seis fases homologadas se mantienen como **equivalencia** entre cultivos, pero la fase reproductiva se nombra según su momento frente a la floración:

| Código | Nombre | Cultivos | Qué pasa | Momento |
|---|---|---|---|---|
| EST | Establecimiento | todos | germinación y emergencia | inicio |
| VEG | Crecimiento vegetativo | todos | hojas, nudos, macollos | antes de la floración |
| REP-pre | Reproductiva previa a la floración | arroz, trigo | se forma la panícula o la espiga (iniciación, embuche, espigamiento) | antes de FLO |
| FLO | Floración | todos | antesis, polinización, emisión de estigmas | — |
| REP-pos | Reproductiva posterior a la floración | maíz, soya | cuaja el grano o se forman las vainas | después de FLO |
| FIL | Llenado | todos | llenado del grano o semilla | después de FLO |
| MAT | Maduración | todos | madurez y secado | final |

REP-pre y REP-pos son la misma **fase** (desarrollo reproductivo, «REP») en el vocabulario de seis fases, pero no el mismo **proceso** ni el mismo momento. No comparar cultivos por «REP» sin decir cuál.

En los archivos de datos (calendario_seis_fases_secano.csv, pares_v2, tablas de amenazas) el código sigue siendo `REP`; la distinción se deriva del cultivo.

## Etapas originales por cultivo

| Fase | Maíz (V/R) | Arroz (BBCH) | Soya (Fehr–Caviness) | Trigo (Zadoks) |
|---|---|---|---|---|
| EST | VE | 00–09 | VE–VC | 00–09 |
| VEG | V1–V6, V7–VT | 10–19, 20–29 | V1–Vn | 10–29, 30–39 |
| REP-pre | — | 30–39, 40–59 | — | 40–49, 50–59 |
| FLO | R1 | 60–69 | R1–R2 | 60–69 |
| REP-pos | R2 | — | R3, R4 | — |
| FIL | R3, R4–R5 | 70–79 | R5, R6–R7 | 70–89 |
| MAT | R6 | 80–99 | R8 | 90–99 |

Fuente: calendario_seis_fases_secano.csv (versión regional-v4-2026-09-16), verificado contra la Hoja1 de REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx.

## Inconsistencias conocidas (para resolver en la ontología)

1. La Hoja1 define REP con procesos posteriores a la floración (pod set, grain set), pero asigna a arroz y trigo etapas previas. Resuelto en nombre con REP-pre / REP-pos.
2. Elongación del tallo: en arroz BBCH 30–39 va a REP-pre (iniciación de panícula, criterio IRRI); en trigo Zadoks 30–39 va a VEG. La misma etapa de la escala BBCH cae en fases distintas según el cultivo.
3. En maíz, R2 (grano en ampolla) se asignó a REP-pos aunque el llenado ya puede empezar ahí (convención v4). La revisión humana original lo ponía en FIL.
4. VEG del maíz en el calendario = V1–V6 + V7–VT, pero el conteo de amenazas usó solo V7–VT (maize_seis_fases.py, STAGES).

## Fuentes de etapas

- Maíz: Hanway/Ritchie V/R (U. Minnesota; U. Delaware).
- Arroz: escala BBCH e IRRI (fase reproductiva = iniciación de panícula a espigamiento).
- Soya: Fehr y Caviness (Mississippi State; UNL CropWatch).
- Trigo: escala Zadoks / BBCH.
