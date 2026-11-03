---
title: Ontología de la tesis — LEEME
fecha: 2026-11-01
version: v0.1 (borrador en revisión)
estado: glosario listo; .owl no creado a propósito
---

# Ontología de la tesis — v0.1

Esta carpeta tiene la primera versión de una **ontología ligera** para la cadena de la tesis:

**variabilidad climática (ONI, RONI, RMM) → amenaza por fase fenológica → rendimiento de cereales (GDHY) → seguro paramétrico**

Todavía no hay archivo `.owl`. Primero revisa el glosario. Cuando esté aprobado, pasarlo a Protégé toma poco tiempo (ver el último apartado).

| Archivo | Qué contiene |
|---|---|
| `glosario.xlsx` | 66 conceptos, 23 relaciones, etapas por cultivo con su BBCH, unidades, fuentes y 10 decisiones pendientes |
| `LEEME.md` | Este documento: alcance, decisiones de diseño y paso a OWL |

## Para qué sirve (y para qué no)

Sirve para tres cosas concretas:

1. **Fijar el vocabulario.** «REP», «evento» o «umbral» significan una sola cosa en los capítulos, las tablas y el código.
2. **Hacer visibles las equivalencias entre cultivos.** Cada etapa original se ancla a la etapa principal BBCH (0–9). Así las inconsistencias se ven en una matriz y no hay que encontrarlas leyendo.
3. **Conectar con vocabularios reconocidos.** Cada concepto lleva, cuando existe, un URI externo verificado (AGROVOC, Plant Ontology, SOSA, CF, QUDT). Eso respalda la metodología frente al jurado.

**No** sirve para calcular: los scripts siguen leyendo el CSV y el Excel. **No** recalcula ni corrige el calendario v4 (es la versión final). **No** valida umbrales ni demuestra daño.

## Alcance de v0.1

- **Dentro:** cultivos (secano), temporadas, escalas fenológicas, etapas originales, seis fases homologadas (EST, VEG, REP-pre, FLO, REP-pos, FIL, MAT), amenazas, reglas, variables, umbrales, duración mínima, eventos, medidas de exposición, índices climáticos, píxel GDHY, celda ERA5-Land, rendimiento y fuentes.
- **Fuera (solo nombrado):** seguro de índice, disparador, función de pago y riesgo de base. Se modelan cuando exista la definición de pérdida (relato §9).
- **Instancias:** solo las de maíz v2 (tabla `tabla_maestra_v2_maiz.xlsx`). Soya, arroz y trigo entran como cultivos y etapas, sin reglas.

## Material de partida

- `docs/nomenclatura_fases.md`: semilla de las seis fases y de REP-pre/REP-pos.
- `docs/RELATO_ACUERDOS_TESIS.md`: acuerdos vigentes.
- `outputs/agroclima_vigente/amenazas/tabla_maestra_v2_maiz.xlsx`: 12 reglas de maíz, criterios C1–C6 y pendientes P1–P12.
- `C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\calendario\calendario_seis_fases_secano.csv`: regional-v4-2026-09-16, 257.748 filas. Se leyó solo para extraer las etapas por fase; no se modificó.

## Decisiones de diseño (propuestas; revísalas)

1. **BBCH como columna vertebral.** Cada etapa original lleva su etapa principal BBCH 0–9. En arroz el código es directo. En trigo, Zadoks equivale a BBCH en cereales. En maíz (V/R) y soya (Fehr–Caviness) el mapeo es **aproximado** y está marcado así en `Etapas_BBCH`: hay que confirmarlo en Meier (2018) antes de citarlo. BBCH no publica un URI por etapa, así que se cita la monografía (DOI 10.5073/20180906-074619).
2. **Las etapas son individuos por cultivo.** `arroz:BBCH_30_39` y `trigo:Z30_39` son distintos. Sin esto, «etapa pertenece_a fase» no se puede escribir, porque la misma etapa cae en fases diferentes.
3. **REP es superclase; REP-pre y REP-pos son subclases** restringidas por cultivo. Los archivos de datos siguen diciendo `REP` y la distinción se deriva del cultivo, como acordaste.
4. **«precede_a» se declara dentro de la secuencia de cada cultivo**, no entre fases genéricas: en arroz REP-pre precede a FLO y en maíz FLO precede a REP-pos. Equivale a `RO:0002090 immediately precedes`, porque las ventanas son semiabiertas y contiguas.
5. **Fase ≠ ventana.** La *fase* es el tipo (FLO). La *ventana* es su realización en un píxel y una temporada, con fechas estimadas. Los eventos ocurren en ventanas.

### Dos cambios frente a la propuesta inicial

- **«Umbral define amenaza» se reemplaza por una clase `Regla de amenaza`.** Un umbral solo (34 °C) no define nada sin variable, operador, duración, fase, cultivo y fuente. Eso ya lo exige el relato (§2). La regla es un patrón n-ario: `Regla define Amenaza`, `Regla aplica_a_fase Fase`, `Regla se_mide_con Variable`, `Regla tiene_umbral`… Además deja guardar umbrales candidatos con estado (FLO 33,7/34,8 °C; FIL 32,7/32,9 °C).
- **«Amenaza ocurre_en fase» se reemplaza por `Regla aplica_a_fase` (1..n) y `Evento ocurre_en_ventana`.** La regla seco-cálida cubre FLO+REP+FIL a la vez, y lo que ocurre de verdad es un evento concreto en un píxel y un año.

### Conceptos añadidos

Porque los datos los necesitan: **Temporada**, **Ventana de fase**, **Celda ERA5-Land** (las reglas se evalúan en celdas nativas antes de agregar al píxel GDHY), **Medida de exposición** con **Cobertura** («dato incompleto no es cero»), **Estado de la regla**, **Nivel de evidencia** y **Etapa principal BBCH**.

## Vocabularios externos usados

Cada URI se comprobó el 1 nov 2026: API de AGROVOC, OLS4 de EBI, Crossref o DataCite para los DOI, y la especificación W3C, QUDT o la tabla CF v95. El método está en la columna «Verificación». Al final se resolvieron otra vez las 127 URI del archivo. Las únicas respuestas no 200 fueron 25 «429 Too Many Requests» de `aims.fao.org`: límite de tasa al resolver en paralelo, y esos URI ya estaban confirmados uno por uno con la API de AGROVOC.

| Vocabulario | Uso |
|---|---|
| AGROVOC (FAO) | cultivos, fases, amenazas, variables, rendimiento, seguro de índice |
| Plant Ontology | etapas de planta entera (EST a MAT) |
| Crop Ontology | diccionarios de rasgos CO_322, CO_320, CO_336, CO_321 (solo `relatedMatch`; no se verificaron términos de etapa allí) |
| BBCH, Zadoks, V/R, Fehr–Caviness, Counce | escalas (citadas por DOI o referencia) |
| W3C SOSA/SSN | variable observable, procedimiento (regla), observación, resultado, sujeto observado (píxel) |
| CF Standard Names v95 | Tmax, Tmin, P, ETP (CF no tiene URI por nombre: se cita nombre y versión) |
| QUDT | °C, mm, mm/día, día, °C·día, t/ha, %, adimensional |
| OWL-Time, PROV-O, DCMI, GeoSPARQL, SKOS, RO/BFO | intervalo y duración, procedencia, fuentes, píxel, correspondencias, «precede» y «parte de» |

**Sin equivalente externo verificado** (términos propios de la tesis): P − ETP, EDD29, umbral, operador, episodio, día afectado, temporada con bandera, cuaje (REP-pos en AGROVOC). Se buscaron; no se inventó ningún identificador.

**Hallazgos que conviene conocer:**

- En Plant Ontology, *sporophyte reproductive stage* (PO:0007130) incluye floración, fruto y maduración. Es mucho más amplio que REP. Por eso REP lleva `broadMatch` y no `exactMatch`.
- En Plant Ontology, *stem elongation stage* (PO:0007089) cuelga del estadio **vegetativo**. Es un argumento para D1.
- AGROVOC traduce *seed filling* como «Hinchamiento de la semilla». Usa «llenado» como etiqueta propia.
- AGROVOC traduce *hazards* como «Peligro»; UNDRR usa «amenaza» en español. Se registran ambas.

## Decisiones pendientes para ti (lista corta)

El detalle, con opciones y una recomendación para discutir, está en la hoja `Decisiones`. Las tres primeras son las que la ontología **obliga** a resolver porque la matriz BBCH las expone:

| # | Decisión | Por qué |
|---|---|---|
| **D1** | Elongación del tallo (BBCH 3): arroz en REP-pre, trigo en VEG | La misma etapa BBCH cae en fases distintas. ¿Mantener y declarar el criterio, unificar en VEG o unificar en REP-pre? |
| **D2** | BBCH 8 (grano pastoso): arroz en MAT, trigo y maíz en FIL | El arroz es el único que corta el llenado en BBCH 7. |
| **D3** | VT del maíz (≈ BBCH 5) en VEG, y BBCH 5 en REP-pre en arroz y trigo | Se decide junto con P1 (umbral de FLO 34,8 o 33,7 °C). |
| D4 | R2 del maíz: REP-pos (vigente) o FIL | Ya estaba en `nomenclatura_fases.md`. |
| D5 | VEG del maíz: el calendario usa V1–VT y la regla solo V7–VT | Propuesta: propiedad `ventana_de_cálculo` en la regla. |
| D6 | `REP` en los datos frente a REP-pre/REP-pos en la ontología | Propuesta: superclase y subclases, sin tocar archivos. |
| D7 | «Evento» mezcla episodio, día afectado y bandera de temporada | Propuesta: tres subclases. |
| D8 | ETP: el código usa Hargreaves y la tabla v2 dice Penman-Monteith | Confirmar Hargreaves y corregir la tabla (P4). |
| D9 | RONI no aparece en scripts ni resultados | ¿Entra como propuesto o se quita hasta usarlo? |
| D10 | Unidades y convención de año del rendimiento sin tendencia | No asignar t/ha hasta confirmar. |

También necesito un dato que no invento: **el umbral de amplitud RMM que separa MJO activa de débil** en tus scripts.

## Cómo pasarlo a OWL en Protégé (cuando apruebes el glosario)

Protégé ya está instalado. Recomiendo hacerlo en este orden y no todo de una vez:

1. **Crear la ontología.** *File → New*. IRI sugerido: `https://github.com/<tu-usuario>/tesis-cereal-climate/ontologia/tcc#` (o el que prefieras; decide antes de crear individuos, porque cambiarlo después es tedioso). Guardar como `docs/ontologia/tcc.owl` en formato **Turtle** (*File → Save as → Turtle*): así Git muestra los cambios línea a línea.
2. **Importar prefijos, no ontologías enteras.** En *Active ontology → Ontology prefixes* añade `skos:`, `sosa:`, `time:`, `qudt:`, `dcterms:`, `prov:`, `geo:` y `obo:` (`http://purl.obolibrary.org/obo/`). **No** importes Plant Ontology ni AGROVOC completas: son enormes y vuelven lento el razonador. Basta referenciarlas por URI.
3. **Clases** (pestaña *Entities → Classes*): una por cada fila de tipo «Clase» del glosario. Pon la definición en `rdfs:comment`, la etiqueta en `rdfs:label@es` y la equivalencia como anotación `skos:closeMatch` (o la que diga la columna) con el URI como valor IRI.
4. **Propiedades** (*Object properties* y *Data properties*): las de la hoja `Relaciones`, con dominio y rango. Para `precede_a` marca *Transitive* solo si usas la versión no inmediata.
5. **Individuos** (*Individuals*): cultivos, escalas, fases y las etapas por cultivo de la hoja `Etapas_BBCH`. Para cargar muchas filas desde Excel usa el plugin **Cellfie** (*Tools → Create axioms from Excel workbook*) o, si no está, *File → Check for plugins…*. Lo usual es empezar a mano con maíz y después cargar el resto por Cellfie.
6. **Razonar.** *Reasoner → HermiT → Start reasoner*. Con D1 sin resolver, una consulta como «etapas con BBCH principal 3 que pertenecen a VEG» devuelve trigo y maíz, pero no arroz. Esa es la señal de que la ontología funciona.
7. **Validar** con *Window → Views → DL Query*. Pregunta de prueba: `Regla and aplica_a_fase value FLO`.

Si después quieres consultar los resultados (eventos, exposiciones) desde la ontología, el paso siguiente es exportar instancias desde Python con `rdflib`. No hace falta para la tesis; queda como opción.

## Historial

| Fecha | Cambio |
|---|---|
| 2026-11-01 | v0.1: glosario, relaciones, matriz BBCH, unidades, fuentes y decisiones D1–D10. Sin `.owl`. |
