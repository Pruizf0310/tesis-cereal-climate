# Metodología de la tabla maestra global de fenología y amenazas v1.0.0

## Objetivo y decisión de cierre

Esta versión entrega una matriz operativa para arroz, maíz, soya y trigo por coordenada de 0,5°, sistema hídrico y temporada. Se construyó con la mejor información actualmente disponible, pero distingue expresamente entre calendarios globales, fases reconstruidas y umbrales científicos. No presenta las fechas intermedias como observaciones.

La unidad de análisis es:

`coordenada + cultivo + sistema hídrico + temporada + fase`

## Fuentes de calendario

1. **GGCMI Phase 3 v1.01** es el calendario principal de siembra y madurez por píxel, cultivo y sistema irrigado/secano: DOI `10.5281/zenodo.5062513`.
2. **SAGE Crop Planting Dates** se utilizó como comparación de siembra y cosecha. No reemplaza automáticamente GGCMI cuando difiere.
3. **MIRCA-OS 2020** se utilizó para comparar meses de siembra y madurez y confirmar cobertura. Para maíz, trigo y soya no constituye validación totalmente independiente porque sus calendarios se apoyan parcialmente en GGCMI.
4. **GEOGLAM** conserva utilidad para identificar ventanas agrícolas amplias y regiones, pero sus macrofases no se transformaron directamente en fases BBCH, Hanway, Fehr-Caviness o Zadoks.
5. El informe `deep-research-report-fenol.md` documentó que no existe un dataset global accesible con todas las fases intermedias por coordenada. GCPE sería la fuente más cercana, pero su descarga oficial no estaba operativa al cerrar esta versión.

La tabla conserva los calendarios que cruzan el cambio de año. `season_length_days` representa días transcurridos entre siembra y madurez; `cycle_days_inclusive = season_length_days + 1` incluye ambos extremos para construir intervalos diarios.

## Reconstrucción de fases

Las fases intermedias se reconstruyeron mediante una **plantilla fisiológica normalizada por cultivo**, reescalada al ciclo local comprendido entre siembra y madurez. El método se registra como `process_model_endpoints_only`.

Para una fase con fracciones acumuladas `f0` y `f1` y un ciclo inclusivo de `N` días:

```text
inicio = redondear(N × f0)
fin    = redondear(N × f1) − 1
duración = fin − inicio + 1
```

Los desplazamientos se suman al DOY de siembra en un eje continuo. Después se convierten nuevamente a DOY 1–365 y se guardan `start_year_offset` y `end_year_offset`.

### Plantillas utilizadas

| Cultivo | Escala | Fases operativas | Fronteras acumuladas del ciclo |
|---|---|---|---|
| Arroz | BBCH | 00–09; 10–19; 20–29; 30–39; 40–59; 60–69; 70–79; 80–99 | 0; 0,08; 0,17; 0,38; 0,52; 0,64; 0,70; 0,90; 1 |
| Maíz | Hanway/USDA | VE; V1–V6; V7–VT; R1; R2; R3; R4–R5; R6 | 0; 0,07; 0,28; 0,50; 0,56; 0,63; 0,72; 0,90; 1 |
| Soya | Fehr-Caviness | VE–VC; V1–Vn; R1–R2; R3; R4; R5; R6–R7; R8 | 0; 0,08; 0,38; 0,50; 0,58; 0,67; 0,78; 0,93; 1 |
| Trigo | Zadoks/BBCH | Z00–09; Z10–29; Z30–39; Z40–49; Z50–59; Z60–69; Z70–89; Z90–99 | 0; 0,07; 0,35; 0,50; 0,60; 0,68; 0,74; 0,93; 1 |

Estas fracciones son **priors operativos**, no duraciones universales. Se apoyan en la secuencia morfológica documentada por las guías IRRI/BBCH para arroz, UMN/Pioneer y Hanway para maíz, SDSU/NDSU/Fehr-Caviness para soya, y Zadoks/GRDC/UMN para trigo, junto con la estructura de fases de ORYZA, DSSAT y APSIM descrita en el informe de investigación. La duración real cambia con cultivar, temperatura, fotoperiodo, vernalización, agua y manejo.

En soya, las fases vegetativas y reproductivas pueden solaparse. La tabla usa `phase_axis = operational_exclusive` para permitir cruces climáticos sin duplicar días; no implica que el desarrollo biológico sea estrictamente excluyente.

## Incertidumbre y confianza

Como no existen eventos intermedios observados globales, la incertidumbre operativa de cada frontera se definió como:

```text
uncertainty_days = mínimo(30, máximo(7, techo(0,10 × season_length_days)))
```

La confianza máxima es **BAJA** cuando GGCMI coincide con SAGE dentro de 30 días y existe soporte MIRCA-OS. En los demás casos es **MUY_BAJA**. Esta clasificación se refiere a las fechas intermedias, no necesariamente a la existencia del cultivo o a los extremos de siembra y madurez.

## Umbrales y amenazas

Las reglas se guardan en una tabla normalizada independiente y la matriz de fases contiene sus identificadores en `threat_rule_ids`. Esto evita multiplicar las 687.328 filas por cada amenaza y permite reemplazar una regla sin reconstruir el calendario.

Se separaron cuatro tipos de evidencia:

- **Umbral modelado:** punto de cambio estimado al combinar experimentos, por ejemplo Liu et al. (2023), DOI `10.1016/j.xplc.2023.100629`.
- **Indicador regional:** definición aplicada históricamente a una región, por ejemplo Sun et al. (2025) para arroz del sur de China, DOI `10.5194/esd-16-1971-2025`.
- **Tratamiento experimental:** intensidad y duración que causaron daño, sin demostrar el inicio del daño, por ejemplo Zhang et al. (2023), DOI `10.3390/agronomy13082126`.
- **Asociación observacional o parámetro modelado:** útil como contexto, pero no como regla fenológica universal, por ejemplo Schauberger et al. (2017), DOI `10.1038/ncomms13931`, y Alsajri (2018), URI `https://hdl.handle.net/11668/20905`.

La duración experimental nunca se interpretó como duración máxima tolerable. Cuando el estudio no permitió estimarla se registró como no determinada.

Los principales umbrales consolidados son:

- floración de arroz: temperatura diurna >37,2 °C; temperatura nocturna >31,2 °C, con las limitaciones de la síntesis de Liu et al.;
- arroz del sur de China: calor medio ≥33 °C, sequía con humedad relativa del suelo ≤75 %, frío ≤20/17 °C y lluvia ≥25 mm/día, únicamente como indicadores regionales de Sun et al.;
- R1 de maíz: temperatura diurna >37,9 °C y nocturna >27,3 °C según Liu et al.;
- llenado de maíz: 39,4–41,5 °C durante seis días se conserva como tratamiento perjudicial, no como umbral de inicio;
- antesis de trigo: temperatura diurna >27,3 °C y nocturna >19,6 °C según Liu et al.;
- soya: >30 °C se conserva como asociación estacional para Estados Unidos, más fuerte en secano, sin atribuirla a una fase concreta; 46,92 °C es una temperatura cardinal máxima modelada de germinación y no una alerta de muerte térmica.

## Archivos y relación con la web

- `tabla_maestra_fenologia_global_v1.csv`: tabla larga completa.
- `tabla_maestra_fenologia_global_v1.csv.gz`: copia comprimida idéntica.
- `tabla_maestra_fenologia_global_v1.xlsx`: control documental, muestra estratificada, catálogo, amenazas y cobertura.
- `reglas_amenaza_v1.csv`: reglas normalizadas.
- `catalogo_fases_v1.csv`: definición de las 32 fases.

La web utiliza un resumen mensual derivado de la misma matriz. Para mantener la interfaz existente, las ocho fases se agregan solo para visualización en F1, F2 y F3. La tabla maestra conserva siempre las fases técnicas detalladas.

## Limitaciones y uso correcto

1. Las coordenadas, siembra y madurez proceden de calendarios globales estáticos, no de observaciones anuales de parcela.
2. Las fases intermedias son aproximaciones reproducibles basadas en extremos y priors; no deben citarse como fechas observadas.
3. Los umbrales no son específicos de cada coordenada. Su transferencia requiere comprobar clima, cultivar, sistema y variable meteorológica equivalente.
4. Los umbrales horarios de antesis no son idénticos a Tmax diaria de reanálisis.
5. La versión puede refinarse posteriormente sustituyendo fases estimadas por GCPE, PEP725, USDA NASS, observaciones nacionales o modelos calibrados, sin cambiar el esquema.

## Criterio de cierre

La versión v1.0.0 se considera apta para análisis exploratorio, cruce climático y visualización web porque conserva cobertura global, cuatro cultivos, sistemas irrigado/secano, temporadas, duraciones y reglas trazables. No es apta para recomendaciones agronómicas locales sin validación adicional.
