---
title: Relato de acuerdos y estado vigente de la tesis
aliases: [Acuerdos de tesis, Estado vigente de la tesis]
fecha_corte: 2026-10-09
estado: documento vivo
tags: [tesis, acuerdos, metodologia, seguimiento]
---

# Relato de acuerdos y estado vigente de la tesis

Actualizado al **9 de octubre de 2026, hora de Colombia**. Esta nota reconstruye el camino de trabajo, las conclusiones metodológicas alcanzadas y lo que sigue pendiente. «Conclusión de etapa» significa una decisión o un resultado verificable de ese paso; no equivale a una conclusión científica final de la tesis.

La reconstrucción se apoya en el chat **Resume acuerdos sobre tesis**, el chat **Reorganizar capítulos en Markdown**, las solicitudes recuperables de **Acumulado de amenazas climáticas** e **Interpretar primer resultado**, y los documentos y auditorías del repositorio. Algunas respuestas de los chats de ChatGPT solo se recuperan como referencias sin contenido: no se reconstruyen como acuerdos confirmados. Las propuestas futuras quedan identificadas como tales.

## Dónde estamos

La pregunta que terminó organizando el trabajo es: **¿ONI informa sobre las amenazas durante las fases agrícolas, MJO aporta información adicional a ONI y esas amenazas se relacionan con menores rendimientos?** La aplicación a seguros paramétricos necesita demostrar esos vínculos y evaluar anticipación y riesgo de base.

Ya tenemos el calendario operativo por píxel, la selección de píxeles de referencia, la tabla de amenazas con su revisión documental, el cálculo histórico completo de seis fases de maíz y el análisis ONI–ocurrencias. También se completaron las probabilidades condicionadas de EST para todo el maíz; el cálculo diario de las seis fases con MJO fue un piloto de diez píxeles. **El script de cruce de seis fases con rendimiento está preparado; en el último acuerdo comprobable no se había ejecutado el análisis completo.**

El siguiente trabajo es revisar la historia anual de cada píxel —seis exposiciones juntas y rendimiento—, resolver la correspondencia temporal y después interpretar asociaciones e impactos. Las gráficas y ese cálculo se retoman después de esta organización.

## 1. De correlaciones oceánicas a una cadena de riesgo agrícola

El trabajo previo incluía correlaciones SST–rendimiento, eliminación de tendencias y exploraciones de patrones. Al intentar llevar esas relaciones a seguros apareció la necesidad de explicar qué ocurre entre el océano y el rendimiento: la exposición del cultivo a una amenaza durante una fase sensible.

La cadena adoptada es **índices climáticos → exposición durante fases agrícolas → rendimiento anual → evaluación de un posible índice paramétrico**. El análisis SST–rendimiento conserva su valor exploratorio. ONI y MJO permiten formular preguntas concretas sobre la amenaza; OLR puede contribuir a interpretar convección y mecanismos, pero no confirma que se haya superado un umbral local de temperatura o lluvia.

**Conclusión vigente:** separar asociación histórica, mecanismo físico, anticipación y aplicación aseguradora. Un índice contemporáneo o una correlación elevada no demuestra capacidad de anticipación. Los rendimientos sin tendencia son la respuesta disponible; quitar la tendencia no convierte toda la variación restante en señal exclusivamente climática.

Capítulos relacionados: [[manuscript/chapters/01_introduccion|Introducción]], [[manuscript/chapters/02_marco_teorico|Marco teórico]] y [[manuscript/chapters/07_seguros_parametricos|Seguros paramétricos]].

## 2. De muchos papers a reglas auditables por fase

La revisión bibliográfica reunía nombres de fases, variables, tratamientos, umbrales y duraciones que no eran directamente intercambiables. Homologar el nombre de una fase no bastaba: había que conservar qué midió cada fuente y en qué condiciones.

Se trabajó sobre la revisión humana, manteniendo comentarios, colores y auditoría. La entrega documental de las **24 filas de cultivo–fase** incorporó fragmentos literales, ubicación y procedencia: L para los fragmentos; M para página, sección o tabla; N para el PDF; O para la procedencia de los componentes y fuentes complementarias. Esa entrega quedó inicialmente fuera de la carpeta principal y después se consolidó junto a la tabla humana, preservando ambas y registrando diferencias.

**Conclusión vigente:** una regla debe conservar variable, unidad, operador, valor, duración, ventana biológica y fuente. La tabla humana adoptada gobierna el cálculo; una aclaración documental no cambia automáticamente una regla aprobada. Una temperatura de tratamiento experimental o cardinal no es, por sí sola, un umbral universal de daño productivo.

La duración mínima de dos días adoptada para calor es un criterio operativo de inclusión de episodios; **no debe etiquetarse automáticamente como daño leve**. Las clasificaciones de severidad publicadas tienen sus propias duraciones y necesitan revisión específica.

**Pendiente de revisión humana:** corroborar los componentes en cada fuente y resolver las discrepancias. En FIL de maíz se calculó **32,7 °C**, como dice la tabla vigente; existe una referencia documental de **32,9 °C** que sigue sin resolverse. La reproducción del Excel no resuelve esa diferencia bibliográfica.

Fuentes de trabajo: [[outputs/agroclima_vigente/LEEME_VIGENTE|Consolidación vigente]], `outputs/agroclima_vigente/amenazas/tabla_maestra_revision_humana.xlsx`, `revision_documental_24_fragmentos_exactos.xlsx`, `reglas_24_fases_vigentes.csv` y `diferencias_revision_documental.csv`, dentro de esa misma carpeta.

Capítulos: [[manuscript/chapters/02_marco_teorico|Marco teórico]], [[manuscript/chapters/04_metodologia|Metodología]] y [[manuscript/chapters/06_discusion|Discusión]].

## 3. De calendarios agregados a seis ventanas por píxel

Los primeros calendarios y visualizaciones podían mezclar fechas de distintos lugares y producir fragmentos mensuales que no representaban el ciclo de una planta. Se pasó a calendarios individuales y luego a la correspondencia **regional-v4-2026-09-16**, que asigna bloques técnicos completos a seis ventanas continuas.

Los códigos EST, VEG, FLO, REP, FIL y MAT son una homologación operativa del proyecto. Su orden biológico depende del cultivo: REP puede preceder a FLO en arroz y trigo y seguirla en maíz y soya. En maíz, R1 se asigna a FLO, R2 a REP, R3 y R4–R5 a FIL y el bloque R6 a MAT. Esta partición analítica no afirma que todas las fuentes experimentales usen esas fronteras exactas.

**Conclusión vigente:** usar GGCMI para los extremos de siembra y madurez, junto con las fechas intermedias estimadas y la correspondencia v4. Las fases intermedias no son observaciones fenológicas anuales. Para calcular se usan los JSON por píxel, con límites semiabiertos y manejo de años bisiestos; el CSV sirve de vista auditable.

La selección es **secano**. Arroz conserva **temporada 1 y temporada 2**, sin equipararlas universalmente a invierno y verano meteorológicos. En trigo siguen existiendo alternativas de primavera e invierno y falta cerrar la selección correspondiente al análisis. Dos temporadas de exposición no convierten un rendimiento anual en dos observaciones independientes.

El año de temporada es el **año de siembra**. Cuando el ciclo cruza diciembre, debe verificarse su asociación con el año del rendimiento. Un calendario típico repetido tampoco permite estudiar si MJO alarga o acorta las fases reales de cada año.

Documentación: [[docs/regional_workflow_v4|Correspondencia regional v4]], [[outputs/agroclima_vigente/calendario/metodo_vigente_v4|Método consolidado]] y [[docs/pixel_calendar_method|Historia del calendario por coordenadas]]. Los documentos históricos conservan decisiones reemplazadas y deben leerse con sus avisos de versión.

Capítulos: [[manuscript/chapters/03_datos|Datos]] y [[manuscript/chapters/04_metodologia|Metodología]].

## 4. De todos los datos GDHY a los píxeles realmente analizados

El primer inventario contaba cualquier píxel con algún rendimiento válido. Al contrastarlo con las correlaciones previas vimos que eso ampliaba la población respecto al trabajo ya hecho. Se adoptaron como referencia los índices de los HDF5 de correlaciones y se exportaron a archivos locales reutilizables.

| Cultivo | Píxeles seleccionados | Resultado de la comparación histórica |
|---|---:|---|
| Maíz | 10.923 | Coinciden con la máscara de al menos 35 años válidos |
| Soya | 4.955 | Coinciden con la máscara de al menos 35 años válidos |
| Arroz | 3.186 | Coinciden con los 36 años válidos |
| Trigo | 10.505 | Tienen 33–36 años; la selección no se explica por un filtro único de cantidad |

**Conclusión vigente:** continuar con esos mismos píxeles, conservando coordenadas, índices originales y años válidos. Las coincidencias anteriores no demuestran por qué se eligió originalmente cada máscara; en trigo esa explicación sigue especialmente pendiente. Disponibilidad de GDHY no demuestra cultivo en todos los años ni superficie cultivada exacta dentro de la celda.

Se conserva el período **1981–2016**, con hasta 36 observaciones anuales por píxel. Ceros y valores negativos detrendidos no se eliminan automáticamente. La selección local evita depender del disco externo para recuperar los índices.

Capítulo: [[manuscript/chapters/03_datos|Datos]].

## 5. Del piloto diario al cálculo completo de maíz

Se empezó con EST de maíz, tres píxeles y 1981–1983; después se ampliaron diez píxeles a 1981–2016. Los ceros del piloto eran resultados locales válidos, no evidencia de ausencia global de la amenaza. La descarga mensual de series completas resultó demasiado lenta y voluminosa para escalar.

Por eso se cambió el motor: **GEE evalúa umbrales y rachas en las celdas nativas de ERA5-Land y devuelve resúmenes**, antes de agregar dentro del píxel GDHY. No se promedian primero las temperaturas para detectar las excedencias. La CPU local coordina y analiza; la GPU local no acelera el cálculo que ocurre en GEE. Los lotes completos se conservan para reanudar.

**Resultado auditado el 8 de octubre:** 98.307 lotes completados; **10.923 píxeles × 36 años × 6 fases = 2.359.368 filas**, sin combinaciones ausentes o duplicadas. Por fase: 393.228 filas, de ellas 391.140 con cobertura completa y 2.088 incompletas.

| Fase | Regla efectivamente calculada | Precisión que debe acompañarla |
|---|---|---|
| EST | Tmax ≥34 °C, racha ≥2 días | Ventana de establecimiento estimada |
| VEG | Tmax ≥34,6 °C, racha ≥2 días | V7–VT aproxima la referencia V6–VT |
| FLO | Tmax ≥33,7 °C, racha ≥2 días | R1 es más estrecha que la ventana R1–R3 de la fuente |
| REP | Tmax ≥33,7 °C, racha ≥2 días | R2 es más estrecha que R1–R3 |
| FIL | Tmax ≥32,7 °C, racha ≥2 días | Hasta inicio de R6; discrepancia 32,7/32,9 pendiente |
| MAT | Precipitación diaria >10 mm; contar días | Bloque terminal R6 como proxy de secado; sin cosecha observada |

**Conclusión vigente:** el cálculo reproduce variable, operador, umbral y duración de la tabla adoptada. Eso no valida la transferencia universal de los umbrales ni demuestra daño. El día climático es UTC. Los conteos medios espaciales pueden ser decimales.

No se pueden sumar las fases como episodios meteorológicos únicos: una racha que cruza FLO/REP puede recortarse, perder la duración mínima o aparecer en ambas fases. Además, EST–FIL cuentan episodios y MAT cuenta días de lluvia. **Dato incompleto no es cero.**

Auditoría: [[outputs/agroclima_vigente/diagnosticos/verificacion_maize_completo/COMPARATIVO_MAIZ_COMPLETO|Verificación del cálculo completo]]. Código: [[scripts/agroclima/pipeline_amenazas/LEEME_SEIS_FASES|Seis fases]].

Capítulos: [[manuscript/chapters/04_metodologia|Metodología]], [[manuscript/chapters/05_resultados|Resultados]] y [[manuscript/chapters/06_discusion|Discusión]].

## 6. De Pearson con ONI a preguntas de probabilidad

Primero se completó Pearson ONI–ocurrencias para todo el maíz. Cada estimación usa hasta 36 pares anuales por fase y píxel: ONI v6 se pondera por los días de esa ventana y se compara con su conteo de ocurrencias. ONI tiene centros mensuales de una media móvil trimestral; no es una observación diaria independiente.

**Conclusión de ese paso:** Pearson describe asociación lineal. No se transforma automáticamente en probabilidad y el producto específico no incluye p-valores, búsqueda de rezagos ni validación predictiva. Tampoco se repite un conteo anual en doce meses para fabricar observaciones mensuales.

Una revisión posterior fijó el interés en **mapas mensuales**, agrupando eneros, febreros, etc. Ese producto debe distinguirse del Pearson por fase ya calculado: requiere exposición realmente fechada y agregada por mes. El diseño mensual permanece como requisito para retomar las gráficas; no se declara completado a partir de una tabla anual.

Código y definición: [[scripts/agroclima/pipeline_amenazas/LEEME_MAIZE_ONI_PEARSON|ONI y ocurrencias]].

Capítulos: [[manuscript/chapters/04_metodologia|Metodología]] y [[manuscript/chapters/05_resultados|Resultados]].

## 7. De componentes MJO y semanas a estados diarios y probabilidades condicionadas

Los resúmenes anuales no conservaban cuándo ocurrieron los episodios. Para relacionarlos con MJO se recuperaron fechas diarias, incluyendo días válidos sin eventos. Una implementación exploratoria agrupó en siete días; ese criterio se descartó y se reemplazó por el cruce diario.

También se aclaró que ROMI local, disponible desde 1991, y **RMM oficial**, que cubre todo 1981–2016, son índices distintos. Se adoptó RMM oficial para mantener el período del rendimiento. RMM1 y RMM2 se interpretan juntos mediante fase y amplitud; no se correlacionan los números 1–8 como una magnitud lineal.

**Conclusión vigente:** estudiar **P(día afectado | ONI, estado diario de MJO, fase agrícola, lugar)**. Los días afectados deben pertenecer a episodios que cumplan umbral y duración. Se distinguen de la frecuencia de episodios por días de exposición y de la proporción de temporadas con eventos: sus denominadores y unidades son diferentes.

La duración de cada fase agrícola entra como exposición. Un episodio de cinco días aporta cinco días afectados, pero sigue siendo un episodio. Se conservan días con cero y se identifica exposición insuficiente. Los días consecutivos no son independientes; la incertidumbre y validación deben respetar la dependencia temporal.

El piloto diario de seis fases tuvo **10 píxeles**. Después se completó **EST para 10.923 píxeles y 36 temporadas**: 10.865 con cobertura completa y 58 sin cobertura válida. Se guardaron probabilidades ONI y ONI–MJO. Según la revisión registrada, solo 5.070 píxeles tenían alguna combinación de MJO activa que superaba los mínimos de exposición; eso no significa cobertura suficiente en las ocho fases para todos.

**Lo que no está cerrado:** comprobar información adicional de MJO frente a una referencia de la misma época y categoría ONI, con incertidumbre y evaluación en años excluidos. No basta seleccionar el estado con la probabilidad más alta. No se ha demostrado capacidad predictiva global ni se ha completado el análisis condicionado de las seis fases para todo el maíz.

Las gráficas deben conservar diferencias espaciales. Un promedio mundial o mapas enormes con diez puntos no responden bien a la pregunta. Quedó planteado mostrar diferencias de probabilidad en puntos porcentuales, perfiles de las ocho fases y MJO débil, y síntesis regionales con cobertura explícita. Son líneas entre categorías; una banda de dispersión espacial no es un intervalo de confianza.

Documentación: [[scripts/agroclima/pipeline_amenazas/LEEME_MAIZE_MJO_DIARIO|MJO diaria]] y [[scripts/agroclima/pipeline_amenazas/LEEME_PROBABILIDADES_UNA_FASE|Probabilidades de una fase]].

Capítulos: [[manuscript/chapters/04_metodologia|Metodología]], [[manuscript/chapters/05_resultados|Resultados]] y [[manuscript/chapters/06_discusion|Discusión]].

## 8. Acuerdo más reciente: las seis exposiciones juntas con el rendimiento

Una propuesta inicial se centraba en EST y otras medidas de exposición. El objetivo se precisó: ver, para cada píxel, qué rendimiento hubo en años con eventos en FLO y FIL, en EST–FLO–FIL o sin eventos en ninguna fase. **Ese acuerdo más reciente reemplaza el análisis aislado de EST como siguiente paso principal.**

La tabla adoptada tiene una fila por **píxel–temporada**, seis columnas con los conteos originales y una columna con el rendimiento anual sin tendencia. Primero se revisan combinaciones observadas e historia anual, conservando fuentes y ceros válidos. No se necesita ONI, MJO, GEE ni otra descarga para ese cruce.

**Conclusión vigente:** usar el CSV original de seis fases y el NetCDF detrendido. Emparejar por coordenadas verificadas y año; no por posición accidental del arreglo. «Sin eventos» significa cero en las seis reglas adoptadas, no ausencia de todo estrés posible.

El archivo de rendimiento inspeccionado no documenta suficientemente unidades ni convención de año. Por eso el script prepara dos escenarios separados: **same-label**, misma etiqueta de año, y **maturity-year**, año en que termina MAT. El segundo es una aproximación, no una confirmación del año de cosecha. No escoger automáticamente el escenario con mejor R².

Después de revisar la tabla, el script permite OLS por píxel con las seis fases simultáneas, al menos 20 pares válidos y validación en bloques de seis años excluidos. Informa fases constantes, dependencia exacta y colinealidad. Los coeficientes, términos por fase y R² parciales describen asociaciones; no son porcentajes de pérdida causal y los R² parciales no tienen por qué sumar el R² total. La implementación no calcula intervalos ni p-valores. El detrendido original puede haber usado todos los años, por lo que esta validación es exploratoria.

**Estado comprobable:** script preparado y probado con datos sintéticos; análisis completo pendiente en el último registro revisado. Los scripts largos se ejecutan localmente; las salidas se documentan y revisan antes de usarse. No se lanza aquí el cálculo de impacto.

Guía y resultados esperados: [[scripts/agroclima/pipeline_amenazas/LEEME_AMENAZAS_RENDIMIENTO|Cruce de seis amenazas con rendimiento]].

Capítulos: [[manuscript/chapters/04_metodologia|Metodología]], [[manuscript/chapters/05_resultados|Resultados]], [[manuscript/chapters/06_discusion|Discusión]] y [[manuscript/chapters/08_conclusiones|Conclusiones]].

## 9. Qué podremos llevar a seguros paramétricos

Las probabilidades describen exposición histórica condicionada al estado climático. El cruce anual permitirá comprobar si esa exposición se asocia con rendimientos menores. Juntas son piezas para evaluar un índice, pero todavía faltan la definición de pérdida, el disparador, la función de pago y la validación del riesgo de base.

**Conclusión vigente:** no presentar una excedencia como daño demostrado, una probabilidad de día afectado como probabilidad de pérdida anual, ni el índice bibliográfico antiguo de severidad como pérdida observada. La utilidad aseguradora necesita comprobar estabilidad temporal y espacial, información disponible antes del evento y concordancia entre disparador y pérdida.

Capítulo: [[manuscript/chapters/07_seguros_parametricos|Seguros paramétricos]].

## Registro resumido de vigencia

| Tema | Qué queda vigente | Qué quedó atrás o sigue pendiente |
|---|---|---|
| Repositorio | `C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate` | Copia de Documents/Codex es histórica |
| Escritura | Ocho capítulos Markdown y dos plantillas de papers | Adaptación de compilación final LaTeX pendiente |
| Calendario | Por píxel, secano, correspondencia v4 | Promedios de calendarios y ventanas compartidas de v3 reemplazados |
| Amenazas | Tabla humana más evidencia y diferencias preservadas | Revisión final de fuentes y FIL 32,7/32,9 pendientes |
| Píxeles | Selección de correlaciones previas | No ampliar automáticamente a todo GDHY disponible |
| Maíz, seis fases | Cálculo completo auditado | No equivale a daño validado ni a episodios únicos sumables |
| ONI | Pearson por fase completo; probabilidades EST completas | Mapas mensuales requieren su propio emparejamiento |
| MJO | RMM oficial y cruce diario | Semanas no son el método principal; ROMI no sustituye RMM |
| Rendimiento | Tabla conjunta de seis fases y escenarios temporales | Ejecución completa y convención de cosecha pendientes |
| Seguros | Evaluar exposición, pérdida, anticipación y riesgo de base | No hay producto asegurador validado |

## Próxima sesión: gráficas y cálculo de impacto

- [ ] Confirmar si existe una ejecución terminada del cruce amenazas–rendimiento posterior al último chat; revisar su manifiesto antes de repetir.
- [ ] Resolver o documentar la convención anual de GDHY y las unidades del detrendido.
- [ ] Revisar la tabla de seis exposiciones juntas por píxel y las combinaciones con cero.
- [ ] Mostrar historia anual: seis filas de exposición y rendimiento debajo, con faltantes diferenciados.
- [ ] Revisar asociaciones por fase, colinealidad y validación por bloques, sin asignar pérdidas causales.
- [ ] Retomar los mapas mensuales solicitados y las diferencias de probabilidad ONI–MJO con cobertura visible.
- [ ] Resolver la discrepancia FIL y cerrar revisión humana de fuentes antes de afirmar umbrales definitivos.
- [ ] Definir la extensión a soya, arroz y trigo, sin asumir que ya se completó.

## Cómo mantener esta nota y los capítulos en Obsidian

Abrir como bóveda la carpeta raíz del repositorio vigente. El índice [[TESIS_INICIO|Tesis — inicio]] reúne el relato y los ocho capítulos. Los enlaces apuntan a los archivos originales del repo: editar en Obsidian edita esos mismos Markdown. No hay sincronización entre duplicados que mantener.

Esta nota conserva el razonamiento y la vigencia. Los capítulos conservan la escritura académica; no se reemplazan con esta bitácora. Al cerrar un paso, actualizar aquí el resultado, la fuente, los pendientes y el capítulo al que se trasladará. Las notas de seguimiento de cada capítulo ofrecen enlaces de ida y vuelta sin insertar decisiones de trabajo dentro del texto académico.

Los documentos de consolidación del 7 de octubre que dicen que GEE todavía no calculó eventos describen ese corte histórico. Para el estado posterior de maíz prevalecen la auditoría del 8 de octubre y los registros de ejecución, sin borrar la historia.

### Historial de esta nota

| Fecha | Actualización | Evidencia |
|---|---|---|
| 2026-10-09 | Reconstrucción del relato, acuerdos reemplazados, estado y pendientes; conexión con capítulos | Chats recuperados y documentación local citada |

Para nuevas entradas: fecha, pregunta resuelta, evidencia, decisión que queda vigente, decisión reemplazada y efecto en los capítulos.
