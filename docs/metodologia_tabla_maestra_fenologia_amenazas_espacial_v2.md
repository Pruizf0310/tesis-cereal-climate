# Metodología de la matriz maestra espacial de fenología y amenazas v2.0.0

## Propósito y unidad de análisis

Esta versión integra en una misma tabla los calendarios por coordenada, las fases técnicas estimadas y las reglas climáticas encontradas en la literatura auditada para arroz, maíz, soya y trigo. La unidad final es:

`coordenada × cultivo × sistema hídrico × temporada × fase técnica × amenaza`

Cada fase sin evidencia cuantitativa también genera una fila con `threat_rule_id = NO_VERIFIED_THRESHOLD`. Por tanto, ningún periodo fenológico desaparece ni queda ambiguamente vacío.

## Calendario espacial y duración de las fases

La siembra y madurez por píxel de 0,5° proceden principalmente de GGCMI Phase 3 v1.01 (`10.5281/zenodo.5062513`). SAGE y MIRCA-OS se conservaron como comparaciones; GEOGLAM se usó como referencia de ventanas amplias, no como fuente de fases técnicas completas.

No existe en las fuentes disponibles un calendario global observado de todas las fases intermedias. Por eso se aplicaron plantillas fisiológicas normalizadas entre la siembra y la madurez locales. El campo `timing_method = process_model_endpoints_only` identifica esta aproximación.

| Cultivo | Escala | Fases | Fracciones acumuladas asignadas |
|---|---|---|---|
| Arroz | BBCH | 00–09; 10–19; 20–29; 30–39; 40–59; 60–69; 70–79; 80–99 | 0; 0,08; 0,17; 0,38; 0,52; 0,64; 0,70; 0,90; 1 |
| Maíz | Hanway/USDA | VE; V1–V6; V7–VT; R1; R2; R3; R4–R5; R6 | 0; 0,07; 0,28; 0,50; 0,56; 0,63; 0,72; 0,90; 1 |
| Soya | Fehr-Caviness | VE–VC; V1–Vn; R1–R2; R3; R4; R5; R6–R7; R8 | 0; 0,08; 0,38; 0,50; 0,58; 0,67; 0,78; 0,93; 1 |
| Trigo | Zadoks/BBCH | Z00–09; Z10–29; Z30–39; Z40–49; Z50–59; Z60–69; Z70–89; Z90–99 | 0; 0,07; 0,35; 0,50; 0,60; 0,68; 0,74; 0,93; 1 |

Las fracciones son *priors* operativos y no duraciones universales. La incertidumbre de cada frontera se conserva como `min(30, max(7, ceil(0,10 × duración del ciclo)))` días. En soya, el eje exclusivo evita duplicar días aunque las fases vegetativas y reproductivas puedan solaparse biológicamente.

## Asignación explícita de amenazas

Las reglas se asignaron por cultivo y fase a **todas las coordenadas que tienen esa fase**. Esto significa “regla candidata que debe evaluarse durante esta ventana”, no “amenaza ocurrida” ni “umbral local validado”. La ocurrencia solo puede determinarse cruzando los DOY de la fase con datos climáticos diarios de la coordenada.

### Arroz

| Fase | Reglas asignadas |
|---|---|
| BBCH 00–09, 10–19, 20–29 | Sin umbral cuantitativo verificado |
| BBCH 30–39 | T media diaria ≥33 °C durante ≥1 día; indicador regional del sur de China |
| BBCH 40–59 | Humedad relativa del suelo ≤75 % durante ≥10 días; T media ≤20 °C durante ≥1 día; precipitación ≥25 mm/día durante ≥1 día; indicadores regionales |
| BBCH 60–69 | T diurna >37,2 °C; T nocturna >31,2 °C; T media ≤20 °C; precipitación ≥25 mm/día |
| BBCH 70–79 | T media ≤17 °C; precipitación ≥25 mm/día |
| BBCH 80–99 | Sin umbral cuantitativo verificado |

Los indicadores de 33 °C, humedad del suelo, frío y precipitación provienen de Sun et al. (2025), `10.5194/esd-16-1971-2025`, y conservan alcance regional. Los valores de floración provienen de Liu et al. (2023), `10.1016/j.xplc.2023.100629`.

### Maíz

| Fase | Reglas asignadas |
|---|---|
| VE, V1–V6, V7–VT, R2, R3, R6 | Sin umbral cuantitativo verificado en el catálogo auditado |
| R1 | T diurna >37,9 °C y T nocturna >27,3 °C; reducción significativa del cuajado según Liu et al. (2023) |
| R4–R5 | Tmax media 39,4–41,5 °C durante 6 días, 08:00–18:00; tratamiento perjudicial, no umbral universal |

### Trigo

| Fase | Reglas asignadas |
|---|---|
| Z00–09 y Z10–29 | 42 °C durante 24 h como tratamiento de fuente secundaria; se muestra solo como referencia, no como alerta validada |
| Z30–39, Z40–49, Z50–59, Z70–89, Z90–99 | Sin umbral cuantitativo verificado |
| Z60–69 | T diurna >27,3 °C y T nocturna >19,6 °C durante antesis según Liu et al. (2023) |

### Soya

| Fase | Reglas asignadas |
|---|---|
| VE–VC | Asociación estacional >30 °C y temperatura cardinal máxima modelada de germinación =46,92 °C |
| V1–Vn, R1–R2, R3, R4, R5, R6–R7, R8 | Asociación >30 °C copiada como contexto del ciclo completo, no como umbral específico de fase |

La asociación >30 °C procede de Schauberger et al. (2017), `10.1038/ncomms13931`, para Estados Unidos y es más fuerte en secano. El valor 46,92 °C de Alsajri (2018) es un parámetro cardinal modelado; no representa muerte térmica ni debe activar por sí solo una alerta agronómica.

## Campos que impiden interpretaciones incorrectas

- `threshold_availability`: indica si existe una regla cuantitativa.
- `assignment_basis`: explica que la regla se copió por cultivo y fase a cada coordenada.
- `geographic_transfer_status`: diferencia regla regional, experimental, secundaria o candidata transferida.
- `local_event_status`: queda `NOT_EVALUATED...` hasta cruzar clima diario.
- `web_use_status`: indica si la web debe mostrar la regla con advertencia o “sin umbral verificado”.
- `evidence_type`, `spatial_scope`, `source`, `doi_or_uri` y `rule_limitations`: conservan trazabilidad y límites.

## Cómo debe calcular la web una amenaza

1. Seleccionar coordenada, cultivo, sistema y temporada.
2. Recuperar `phase_start_doy`, `phase_end_doy` y los desplazamientos de año.
3. Mostrar todas las reglas asociadas a la fase, no solo una amenaza principal.
4. Para cada regla utilizable, obtener la variable climática diaria equivalente durante la ventana.
5. Aplicar operador, umbral y duración consecutiva o acumulada.
6. Informar por separado: regla candidata, evento observado, fuente, alcance y limitación.

No se deben comparar directamente umbrales horarios o de cámara con Tmax/Tmin diaria sin una transformación documentada. Tampoco se debe marcar una coordenada como afectada únicamente porque una regla esté asignada.

## Archivos finales

- `tabla_maestra_fenologia_amenazas_espacial_v2.csv`: tabla completa desplegada.
- `tabla_maestra_fenologia_amenazas_espacial_v2.csv.gz`: copia comprimida idéntica para distribución y GitHub.
- `tabla_maestra_fenologia_amenazas_espacial_v2.xlsx`: libro de control con muestra auditable, reglas, catálogo y metodología resumida.
- `phase_threat_matrix_v2.json`: catálogo ligero para que la web relacione fases y amenazas; las coordenadas y ventanas permanecen en los activos de calendario.

## Alcance científico

Esta versión es reproducible y apta para análisis exploratorio y actualización de la web. No convierte evidencia regional o experimental en verdad local. La validación local futura podrá reemplazar una regla sin modificar el calendario, siempre que conserve el identificador, la fase, la fuente y el ámbito de aplicabilidad.
