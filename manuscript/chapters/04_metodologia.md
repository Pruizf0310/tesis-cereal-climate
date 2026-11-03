# 4. Metodología

Versión de trabajo consolidada con los dictados del 12 de octubre de 2026. Los textos dictados se ubican en el índice del capítulo conservando su redacción. Los complementos documentales solicitados están identificados como tales y no se atribuyen al dictado.

> **Cómo leer las marcas:** **[SIN DICTADO]** señala contenido todavía no narrado; **[CITA]** requiere publicación o documentación oficial; **[EVIDENCIA]** requiere archivos, scripts o resultados; **[JUSTIFICACIÓN]** requiere explicar una decisión; **[VERIFICAR]** requiere aclarar una afirmación. Las notas de respaldo se refieren al párrafo o tabla anterior. Las referencias ya identificadas se conservan; su presencia no resuelve automáticamente todas las dudas.


## 4.1 Diseño general de la investigación

**Enfoque de la investigación**

Lo primero que se hizo después de entender el problema y cómo se iba a realizar la investigación, definimos que la variabilidad climática la íbamos a estudiar a partir de ENSO y de la MJO, cuáles condiciones climáticas locales afectaban cada uno de los sitios en los que se cultivan cereales.

> **RESPALDO NECESARIO — [CITA + JUSTIFICACIÓN]:** Respaldar la elección de ENSO y MJO, sus escalas y su pertinencia para los lugares y cultivos estudiados.

Estamos estudiando el rendimiento de cuatro cultivos, que son el arroz, el maíz, el trigo y la soya, y con eso vamos a generar insumos para los seguros.

> **RESPALDO NECESARIO — [JUSTIFICACIÓN]:** Explicar la selección de cultivos y cómo los resultados servirán como insumos para seguros. Es un objetivo del estudio, no un resultado demostrado.

**Identificación y descarga de las bases de datos**

Lo primero que hicimos después de eso fue identificar y descargar las bases de datos. Para el rendimiento agrícola tenemos las bases de datos GDHY, que tienen un periodo de tiempo de datos de 1981 a 2016.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA]:** Citar GDHY y la versión descargada; adjuntar inventario que confirme 1981–2016.

Tenemos también la temperatura superficial del mar, el índice ONI y los índices de MJO, las variables meteorológicas locales y los fuentes de calendarios agrícolas.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA]:** Identificar producto, proveedor, versión, período, resolución y ruta de descarga de cada conjunto de datos.

**Datos de variabilidad climática**

Los datos obtenidos sobre la variabilidad climática como los índices ONI, las temperaturas superficiales del mar y los índices de la MJO fueron obtenidos de fuentes oficiales de la NOAA y tengo que verificar de dónde más conseguí los datos de SST.

> **RESPALDO NECESARIO — [CITA + VERIFICAR]:** Identificar los proveedores oficiales de ONI, SST y del índice MJO efectivamente utilizado. Comprobar la atribución conjunta a NOAA.

## 4.2 Preparación de los datos de rendimiento

**Rendimiento agrícola: GDHY**

GDHY se refiere al Global Dataset of Historical Yields. Es un conjunto de datos globales de rendimientos históricos, que es una base de datos pues científica y climática a nivel global. Sin embargo, esto no es un modelo híbrido basado en estadísticos de los de la FAO y teledetección por satélite.

> **RESPALDO NECESARIO — [CITA + VERIFICAR]:** Respaldar nombre, naturaleza y construcción de GDHY. Confirmar «no es un modelo híbrido» y la caracterización como base climática antes de conservar esas afirmaciones.

Es una cuadrícula de 0.5 grados, es decir aproximadamente 50 kilómetros por 50 kilómetros, series temporales anuales que abarcan desde 1981 hasta 2016 y la unidad de medida son toneladas por hectárea.

> **RESPALDO NECESARIO — [CITA + VERIFICAR]:** Citar resolución, período y unidades. Revisar la equivalencia 50 × 50 km: la distancia longitudinal de 0,5° cambia con la latitud.

Estos datos se enfocan estrictamente en los cuatro cultivos principales que representan la base de la seguridad alimentaria mundial. Son utilizados para hacer diferentes modelos de impactos de cambio climático y fenómenos meteorológicos y para evaluar y calibrar modelos de simulación de cultivos a escala continental o global. Eso dice pues su página web.

> **RESPALDO NECESARIO — [CITA]:** Citar cobertura de los cuatro cultivos, usos en modelos y la afirmación sobre seguridad alimentaria mundial. Incorporar la página o publicación exacta.

Esta base de datos fue publicada en el 2020 y constituye pues una fuente de información valiosa. Sin embargo, sus autores alertan sobre que las estimaciones del modelo no son exactas, pueden contener errores. Sin embargo, está el código disponible, se pueden...

> **RESPALDO NECESARIO — [CITA + VERIFICAR]:** Confirmar año de publicación y versión; localizar advertencia de errores y repositorio de código. Completar «se pueden…».

Estas bases de datos tienen series completas en todos los píxeles en los que se habla sobre las estadísticas que tiene la FAO y sobre las observaciones satelitales. Por lo tanto, se tuvo que tener en cuenta las series completas, los píxeles con series completas de al menos 35 o 36 años de datos.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + JUSTIFICACIÓN]:** Respaldar cobertura FAO/satélite y comprobar completitud por píxel; justificar el mínimo de 35 o 36 años. No inferir series completas de la cobertura espacial.

<!-- Pendiente: confirmar la transcripción «esto no es un modelo híbrido» y añadir la referencia de la página web mencionada. -->

### 4.2.1 Limpieza

Lo que se obtuvo de esa base GDHY versión 1.2 integrada con versión 1.3 fueron archivos .nc4 de rendimiento para cada año. Entonces era importante construir una serie anual de 36 observaciones mínimo por píxel antes de calcular las anomalías y poderlas relacionar con las demás variables del clima, especialmente con la temperatura superficial del mar en la primera instancia.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + JUSTIFICACIÓN]:** Documentar integración GDHY 1.2/1.3, archivos anuales y criterio de 36 observaciones; conciliar con la excepción de 35.

Lo que hicimos fue abrir y concatenar los archivos con Python xarray utilizando `open_mfdataset` y se encontró que no eran coordenadas compatibles. Entonces al revisar el código, las coordenadas y unirlas, necesitábamos combinar los años sin introducir conflictos entre las coordenadas. Entonces después de identificar exactamente cuáles eran las variables, eso nos obligó a corregir los scripts.

> **RESPALDO NECESARIO — [EVIDENCIA]:** Vincular scripts de concatenación, mensajes de incompatibilidad y corrección aplicada; registrar versión de xarray y opciones utilizadas.

Procesamos todos los archivos NetCDF, comprobamos los tipos de variables, las dimensiones y formas de los arreglos, el rango y el tipo de las coordenadas temporales, la extensión espacial y resolución de las grillas, cantidad de valores faltantes, compatibilidad entre los archivos de rendimiento y la temperatura superficial del mar, porque teníamos que verificar que fuéramos a comparar posteriormente archivos de las mismas magnitudes.

> **RESPALDO NECESARIO — [EVIDENCIA + VERIFICAR]:** Vincular informe de control de calidad y criterios. Precisar «mismas magnitudes»: rendimiento y SST tienen unidades distintas; requieren correspondencia espacial y temporal para correlacionarse.

**Características de los archivos revisados**

Además de comprobar que los archivos NetCDF abren correctamente, pues verificamos los variables, las dimensiones, las coordenadas, la integridad temporal y la validez numérica antes de utilizarlos en los análisis estadísticos.

> **RESPALDO NECESARIO — [EVIDENCIA]:** Incorporar lista de verificaciones, criterios de aceptación y diagnóstico de integridad temporal y numérica.

Obtuvimos como resultado rendimientos de GDHY de cuatro cultivos con las dimensiones de 36 por 360 por 720, una grilla completa global. Los archivos eran tipo numérico, la latitud es de -89.75 grados a 89.75 grados y la longitud de 0.25 a 359.75, con una resolución de 0.5 grados.

> **RESPALDO NECESARIO — [EVIDENCIA]:** Citar inventario o diagnóstico que muestre dimensiones, orden de ejes, tipo numérico, extensión y resolución. Una grilla global no implica rendimientos válidos en todas sus celdas.

Coordenada temporal de arroz, trigo y soya, los años entre 1981 y 2016; la coordenada temporal del maíz, 36 fechas incorrectas repetidas de 1970.

> **RESPALDO NECESARIO — [EVIDENCIA + VERIFICAR]:** Adjuntar metadatos originales y diagnóstico del maíz; verificar unidades/decodificación de tiempo y documentar la corrección de las fechas de 1970.

Y encontramos que para compararlo con la SST teníamos 529 meses desde septiembre de 1981 hasta septiembre de 2025.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN]:** Identificar el archivo SST, confirmar 529 meses y fechas, y documentar la selección del período común con rendimiento.

### 4.2.2 Detrending

Después de eso hicimos un proceso de limpieza de la tendencia tecnológica de los archivos, reconstruimos las coordenadas temporales y comprendimos que la escritura inicial de esa base de datos de rendimientos y la variable que realmente contenía los rendimientos, la convención espacial de coordenadas y los problemas de concatenación y exportación.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + JUSTIFICACIÓN]:** Documentar detrendido y reconstrucción temporal. Respaldar la interpretación de tendencia tecnológica: una tendencia ajustada no identifica por sí sola su causa.

**Librerías utilizadas y detrending**

Las librerías más utilizadas fueron xarray para la lectura, concatenación, selección y exportación de los NetCDF, NumPy para operaciones sobre los arreglos multidimensionales, Pandas, SciPy, `stats.linregress` para ajuste lineal por serie temporal, `numpy.polyfit`, `xarray.apply_ufunc`.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA]:** Registrar versiones y entorno; citar software científico según sus recomendaciones y comprobar cuáles funciones se ejecutaron.

Hicimos detrending lineal mediante regresión a ajuste polinomial de primer grado.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + JUSTIFICACIÓN]:** Añadir referencia del método, ecuación, eje temporal, tratamiento de faltantes y script. Precisar regresión lineal o ajuste polinomial y definición de anomalía.

### 4.2.3 Selección de píxeles válidos

Una vez tuvimos todos los archivos limpios de rendimientos con las series completas identificamos los píxeles. Seleccionamos los píxeles que tenían 36 años de datos. En algunos casos nos quedábamos con muy poquitos píxeles disponibles y bajamos la regla a 35 años de datos disponibles para poderlos correlacionar con la temperatura superficial del mar.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN]:** Documentar máscara de selección, cultivos que admitieron 35 años y tratamiento del año faltante, con conteos reproducibles.

## 4.3 Armonización espacial y temporal

También identificamos que las longitudes no estaban expresadas entre -180 grados y 180, sino entre 0 y 360 grados. Esto también hizo que determináramos cada una de las partes, que supiéramos bien qué tenía cada archivo, el lenguaje en el que estábamos trabajando.

> **RESPALDO NECESARIO — [EVIDENCIA]:** Conservar diagnóstico de coordenadas y transformación 0–360 a −180–180, si se aplicó, con comprobación de correspondencia espacial.

## 4.4 Análisis SST-rendimiento

**Procesamiento paralelo y almacenamiento**

Las librerías que utilizamos fueron xarray, NumPy, pandas, scipy, stats, math, matplotlib, cartopy, Dask y os.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA]:** Registrar entorno y versiones de las librerías efectivamente empleadas; vincular scripts y referencias de software pertinentes.

En esta configuración de procesamiento se hizo paralelo y se documentó utilizando Dask con 14 trabajadores. Lo que hicimos fue optimizar la capacidad computacional, las CPUs y las GPUs que podíamos emplear para calcular esas correlaciones y lo que hicimos fue convertir estos archivos en unos archivos .h5 que contenían información espacial también, pero contenida y guardada de otra forma para poder reducir la memoria y poder hacer los cálculos en un tiempo prudente.

> **RESPALDO NECESARIO — [EVIDENCIA + VERIFICAR]:** Respaldar 14 trabajadores y recursos realmente usados, especialmente GPU. Para reducción de memoria y tiempo, aportar mediciones o describirlo como propósito; identificar estructura y compresión HDF5.

Así las cosas quedamos con píxeles asociados a los HDF5: para trigo un número de píxeles de 10.505, para maíz 10.923, para arroz 3.186 y para soja 4.955.

> **RESPALDO NECESARIO — [EVIDENCIA]:** Vincular inventario HDF5 con los cuatro conteos; conciliar trigo 10.505 con el inventario posterior y explicar exclusiones.

### 4.4.1 Correlaciones punto-campo

Acá hicimos correlaciones punto campo. Estábamos estudiando la relación que hay entre estas dos variables y dado que los datos de temperatura superficial del mar son globales hicimos las correlaciones uno a uno entre un píxel con rendimiento, cómo se correlacionaba con toda la temperatura superficial del mar.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + JUSTIFICACIÓN]:** Identificar coeficiente, pares temporales, tratamiento de faltantes, dependencia temporal y evaluación de significancia y comparaciones múltiples, si corresponde.

Esas correlaciones las hicimos para los 12 meses del año. Identificamos en cada píxel todos los eneros, cómo se correlacionaban con ese rendimiento anual en ese píxel, todos los febreros cómo se correlacionaban con ese rendimiento en ese píxel, así todos los marzos, todos los junios, todos los julios.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN]:** Vincular cálculo de los 12 meses y especificar emparejamiento del mes SST con el año del rendimiento, rezagos y número de pares válidos.

Y esto tiene una explicación climática sobre la detección de las frecuencias o de las oscilaciones de los puntos máximos de las oscilaciones en el comportamiento cíclico de la temperatura superficial del mar.

> **RESPALDO NECESARIO — [CITA + VERIFICAR]:** Sustentar la interpretación de frecuencias, oscilaciones y máximos. Las correlaciones separadas por mes no estiman por sí solas frecuencias espectrales.

### 4.4.2 Identificación de patrones espaciales

**Síntesis de las correlaciones y relación con los fenómenos climáticos**

Lo que hicimos después de correlacionar toda la temperatura superficial del mar con el rendimiento fue buscar la forma de resumir esa información en mapas más cortos que pudiéramos mostrar e interpretar. Y aquí se sacan conclusiones sobre los patrones existentes y algunas estadísticas y, pues, información que nos indica o que nos da una alerta sobre cómo observar o cómo interpretar la información de rendimientos para poderla vincular con las demás variables climáticas que estamos considerando, con los fenómenos más importantes que modulan las lluvias y modulan la temperatura, los cuales son El Niño y la MJO.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA]:** Documentar síntesis de mapas y estadísticas; citar la modulación de lluvia y temperatura por ENSO/MJO y su alcance regional.

> **PENDIENTE DE AMPLIAR — ENSO y MJO:** ampliar la descripción de los fenómenos climáticos en el marco teórico. En la metodología, describir cómo utilizamos sus índices, sus escalas temporales y su relación con las variables locales y el rendimiento.

> **PENDIENTE DE AMPLIAR — Síntesis de mapas:** describir exactamente cómo resumimos las correlaciones mensuales, cuáles estadísticas calculamos y cuáles criterios utilizamos para mostrar e interpretar los patrones. Las conclusiones sobre los patrones se organizarán en resultados y discusión.

Teniendo todas esas variables mapeadas, la intención es buscar cuál o cómo afectan estos fenómenos de variabilidad al rendimiento y qué alertas se pueden tener al respecto.

## 4.5 Análisis ENSO-rendimiento

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** El dictado menciona el análisis con ONI como trabajo en curso; no describe todavía un procedimiento específico ENSO–rendimiento. Véase 4.11.

### 4.5.1 Relación con ONI

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** Falta dictar cómo se empareja ONI con amenazas y rendimiento, producto utilizado, período y estadístico.

### 4.5.2 Rezagos temporales

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictaron rezagos ENSO, su elección ni su cálculo. No se presume que se hayan aplicado.

### 4.5.3 Clasificación por fases ENSO

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictaron categorías ENSO, umbrales ni criterio de persistencia; citar la definición del índice si se utiliza.

## 4.6 Análisis MJO-rendimiento

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** El dictado menciona el análisis con MJO como trabajo en curso; no detalla su procedimiento. Véase 4.11.

### 4.6.1 Fases de la MJO

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictaron el índice MJO definitivo, componentes, amplitud, fases ni definición de actividad.

### 4.6.2 Rezagos temporales

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictaron rezagos MJO ni su justificación. No se presume que se hayan aplicado.

## 4.7 Construcción del calendario fenológico

**Construcción del calendario fenológico típico por píxel**

Entonces, metodológicamente hablando, lo que se hizo fue primero construir un calendario fenológico típico por cada uno de los cultivos en los píxeles donde hay rendimiento de los datos de GDHY que teníamos rendimiento. Buscamos e integramos con todos los calendarios disponibles en la web para cada uno de los cuatro cereales que tienen terminología diferente. Algunos tienen información de la FAO y están integrando, pues, otras fuentes.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + VERIFICAR]:** Identificar calendarios realmente consultados e integrados y sus vínculos con FAO. Delimitar la búsqueda antes de afirmar «todos los calendarios disponibles».

**Fuentes consultadas y función de cada una**

**Complemento basado en los registros del proyecto:** las fuentes identificadas son las siguientes. Queda pendiente precisar cualquier consulta adicional a FAO; los registros revisados no permiten afirmar que se descargó e integró directamente un calendario de FAO.

| Fuente | Autores o institución | Información y uso en el proyecto |
|---|---|---|
| GGCMI Phase 3 v1.01 | Jonas Jägermeyr, Christoph Müller, Sara Minoli, Deepak Ray y Stefan Siebert (2021) | Fuente principal de las fechas típicas de siembra y madurez por coordenada de 0,5°, cultivo, sistema hídrico y temporada. |
| SAGE Crop Calendar Dataset | William J. Sacks, Delphine Deryng, Jonathan A. Foley y Navin Ramankutty (2010) | Fechas de siembra y cosecha; se conservó como comparación con el calendario principal. |
| MIRCA-OS | Endalkachew A. Kebede, Kevin O. Oluoch, Stefan Siebert y colaboradores (2025) | Calendarios mensuales y áreas cultivadas de secano y riego; se conservó como comparación. |
| GEOGLAM CM4EW Calendars v1.3 | GEOGLAM / Crop Monitor for Early Warning | Referencia de ventanas amplias y fuente de una tabla inicial para maíz, arroz y trigo. Esa versión no aportó calendario de soya. |

Referencias bibliográficas verificadas: [GGCMI Phase 3](https://zenodo.org/records/5062513), [SAGE — Sacks et al. (2010)](https://sage.nelson.wisc.edu/data-and-models/datasets/crop-calendar-dataset/) y [MIRCA-OS — Kebede et al. (2025)](https://www.nature.com/articles/s41597-024-04313-w).

> **ACLARACIÓN DE FUENTE:** en el dictado se recordó GEOGLAM como origen del calendario típico. Los registros distinguen esa referencia inicial del calendario vigente, cuyos extremos de siembra y madurez proceden de GGCMI. GEOGLAM, SAGE y MIRCA-OS no se promediaron automáticamente para obtener las fechas actuales.

**Inventario ampliado de citas del calendario web**

Este inventario complementa las fuentes de fechas anteriores con las fuentes de las escalas, las guías de desarrollo y la correspondencia de fases. Se contrastó con el manifiesto del calendario web, `metadata/six_phase_correspondence_v4.json` y la metodología archivada de la tabla maestra. La revisión corresponde a los archivos locales de la web; queda pendiente contrastarlos con la versión desplegada si esta contiene cambios posteriores.

| Fuente que debe conservarse | Elemento del calendario que respalda | Estado de la referencia |
|---|---|---|
| GGCMI Phase 3 v1.01 — Jägermeyr, Müller, Minoli, Ray y Siebert | Siembra y madurez por coordenada, sistema y temporada | DOI 10.5281/zenodo.5062513; referencia principal ya incluida arriba. |
| Jägermeyr et al. (2021), *Climate impacts on global agriculture emerge earlier in new generation of climate and crop* | Selección de fuentes, relleno de vacíos y extrapolación del producto GGCMI | [Publicación asociada](https://doi.org/10.1038/s43016-021-00400-y), señalada por el proveedor del calendario. |
| SAGE — Sacks et al. (2010) | Comparación de fechas de siembra y cosecha | Referencia incluida arriba. |
| MIRCA-OS — Kebede et al. (2025) | Comparación de meses y cobertura | Referencia incluida arriba. La metodología histórica menciona «MIRCA-OS 2020»: verificar el archivo y si 2020 identifica el producto utilizado o un año de referencia. |
| GEOGLAM CM4EW Calendars v1.3 | Ventanas amplias, regiones y antecedente de la tabla inicial | Conservar la atribución institucional y el ZIP original; completar la ficha oficial y los créditos de esa versión. |
| BBCH, guías de arroz de IRRI | Nombres y secuencia de las etapas del arroz | Completar edición y autores de la escala BBCH efectivamente consultada. |
| Hanway/USDA, escala V/R | Nombres y secuencia de las etapas del maíz | Completar publicación y edición consultadas. |
| Fehr–Caviness | Nombres y secuencia de las etapas de soya | Completar publicación y edición consultadas. |
| Zadoks/BBCH | Nombres y secuencia de las etapas de trigo | Completar referencias originales y ediciones consultadas. |
| University of Minnesota, *Maize Insect Pests: Maize Growth & Development* | Descripción de VE, V, VT y R1–R6; soporte de la correspondencia de maíz | [Guía registrada en v4](https://ipmworld.umn.edu/maize-insect-pests-maize-growth-development). |
| University of Delaware Cooperative Extension, *Corn Growth Stages and Management* | Correspondencia de floración, desarrollo del grano, llenado y madurez del maíz | [Guía registrada en v4](https://www.udel.edu/academics/colleges/canr/cooperative-extension/fact-sheets/corn-growth-stages-and-management/). |
| IRRI, *Growth stages of the rice plant* | Transición reproductiva desde iniciación de panícula, embuchamiento, espigamiento y floración | [Guía registrada en v4](https://www.knowledgebank.irri.org/ericeproduction/0.2._Growth_stages_of_the_rice_plant.htm). |
| IRRI, documento con identificador 0471097608 | Soporte adicional de la correspondencia fenológica de arroz | [PDF registrado en v4](https://books.irri.org/0471097608_content.pdf). Completar título, autores, año y páginas; no se verificó el contenido del PDF en esta revisión. |
| IRRI, documento con identificador 0851996361 | Soporte adicional de la correspondencia fenológica de arroz | [PDF registrado en v4](https://books.irri.org/0851996361_content.pdf). Completar título, autores, año y páginas; no se verificó el contenido del PDF en esta revisión. |
| Mississippi State University Extension, *A Guide to Soybean Growth Stages* | Descripción de etapas reproductivas de soya y correspondencia de llenado y madurez | [Guía registrada en v4](https://www.extension.msstate.edu/publications/guide-soybean-growth-stages). |
| University of Nebraska–Lincoln, *Setting Yield in Soybean and Avoiding End-of-Season Plant Stress* | Llenado de semilla y madurez de soya | [Guía registrada en v4](https://cropwatch.unl.edu/setting-yield-soybean-and-avoiding-end-season-plant-stress-unl-cropwatch-aug-23-2013/). |
| Pioneer y University of Minnesota | Guías morfológicas de maíz citadas en la construcción de la plantilla inicial | La metodología v1 las menciona; recuperar título, autor, enlace y edición de Pioneer. Verificar si la guía UMN coincide con la conservada en v4. |
| South Dakota State University (SDSU) y North Dakota State University (NDSU) | Guías de desarrollo de soya citadas en la plantilla inicial | Recuperar las guías exactas, autores, años y enlaces del informe de investigación. |
| Grains Research and Development Corporation (GRDC) y University of Minnesota | Guías de desarrollo de trigo citadas en la plantilla inicial | Recuperar las guías exactas, autores, años y enlaces del informe de investigación. |
| ORYZA, DSSAT y APSIM | Estructura de fases de modelos citada como antecedente de las plantillas normalizadas | Recuperar publicaciones, versiones y pasajes consultados. La mención no prueba que se ejecutaran esos modelos ni que generaran las fechas del calendario. |
| `deep-research-report-fenol.md` | Informe interno que reunió fuentes de fenología y antecedentes de las plantillas | Citado por la metodología v1; pendiente recuperar el informe y cotejar su bibliografía completa. |
| Matriz original, catálogo de fases y revisión humana de correspondencias | Fracciones operativas y paso de ocho bloques técnicos a seis ventanas | Conservar como elaboración del proyecto, junto con la versión v4 y sus archivos de procedencia. Las fuentes biológicas no validan por sí solas las fracciones temporales. |

**Fuentes de ventanas experimentales que también deben conservarse al explicar la correspondencia con amenazas:** Liu et al. (2023), [DOI 10.1016/j.xplc.2023.100629](https://doi.org/10.1016/j.xplc.2023.100629), y Zhang et al. (2023), [DOI 10.3390/agronomy13082126](https://doi.org/10.3390/agronomy13082126). La documentación del calendario las utiliza para distinguir floración, desarrollo posterior y llenado; no aportan fechas por píxel. El catálogo completo de umbrales y sus demás autores deberá citarse al desarrollar el apartado de amenazas.

**Fuentes mencionadas como alternativas, pendientes o futuras:** GCPE, PEP725 y USDA NASS. Se conserva su mención para documentar la búsqueda, pero no se presentan como datos incorporados al calendario actual: la metodología v1 indica que GCPE no pudo descargarse y propone las otras fuentes para refinamientos futuros.

**Archivos adicionales localizados en la colección de calendarios:** se encontraron `MIRCA-OS_2020_rf_v2.csv` y `MIRCA-OS_2020_ir_v2.csv`, además de archivos para 2000, 2005, 2010 y 2015. Debe verificarse la referencia propia de esa versión v2 antes de atribuirla únicamente a la publicación de 2025. También existe `03_MIRCA2000_v1.1/condensed_cropping_calendars.zip`: conservar MIRCA2000 v1.1 en el inventario bibliográfico y comprobar su utilización directa o como antecedente de otras fuentes. La presencia del archivo no demuestra su incorporación al calendario web. Para SAGE se localizaron los archivos NetCDF comprimidos de maíz, arroz, soya, trigo y temporadas alternativas de maíz, arroz y trigo de invierno.

> **PENDIENTE DE CIERRE BIBLIOGRÁFICO:** completar cada ficha incompleta de este inventario y cotejar la bibliografía del informe de investigación original. Hasta recuperar esas referencias, este listado reúne todas las fuentes identificadas en los registros revisados, pero no permite afirmar que la bibliografía esté cerrada.

La nota local `04_MIRCA_OS_v2_2026/DESCARGA_MANUAL_MIRCA_OS.txt` identifica expresamente MIRCA-OS versión 2, publicada en marzo de 2026, y remite a este [recurso de HydroShare](https://www.hydroshare.org/resource/e4582ca0042148338bb5e0148b749ed6/). Conservar esta referencia específica junto con la publicación científica; quedan por cotejar sus metadatos oficiales y los archivos efectivamente usados en la comparación.

- [Método de la tabla maestra de fenología v1](</C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/docs/metodologia_tabla_maestra_fenologia_v1.md>).
- [Método de fenología y amenazas v2](</C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/docs/metodologia_tabla_maestra_fenologia_amenazas_espacial_v2.md>).
- [Correspondencia vigente v4](</C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/docs/regional_workflow_v4.md>).
- [Auditoría de los extremos del calendario](</C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/docs/calendar_endpoint_audit_2026-09-28.md>).
- [Tabla inicial basada en GEOGLAM](</C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/docs/tabla_maestra_fenologia.md>).

**Calendario típico y duraciones de las fases**

Una vez tuvimos consolidado el calendario fenológico típico que corresponde a las suposiciones hechas y están bien las hipótesis, porque es un análisis global sobre los sitios donde efectivamente hay cultivos de cereales y un comportamiento por latitud y un solo tipo de cultivo estamos analizando: el cultivo secano en las diferentes latitudes, y todos no inician en el mismo mes, no tienen la misma duración de días las temporadas entre cada uno de los cultivos; sin embargo, se conserva, según la información recopilada.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + VERIFICAR]:** Respaldar diferencias de inicio/duración y presencia efectiva del cultivo; justificar hipótesis y efecto de latitud sin tratar su validez como ya demostrada.

> **PENDIENTE DE AMPLIAR — Duraciones y extrapolación:** poner cuánto dice cada autor que dura cada una de las fases, para poder decir cómo fue que hicimos la extrapolación y decidimos unificar las fechas finales del calendario. Documentar las suposiciones y su alcance; la disponibilidad de un calendario en una celda no comprueba por sí sola que cada temporada se cultive efectivamente allí.

### 4.7.1 Asignación espacial del calendario

**Píxeles y correspondencia espacial**

Los píxeles del análisis se tomaron de la selección de GDHY utilizada en las correlaciones y conservada en los índices de los HDF5. Para cada coordenada se recuperó el calendario correspondiente al cultivo, sistema hídrico y temporada. La auditoría del 28 de septiembre de 2026 comprobó que los extremos de los 85.916 calendarios del inventario general coincidían con las coordenadas exactas de los NetCDF de GGCMI, sin sustituirlas por el vecino más cercano. Este inventario general es más amplio que los píxeles seleccionados para las correlaciones.

> **RESPALDO NECESARIO — [EVIDENCIA]:** Vincular selección HDF5, manifiesto y auditoría del 28-09-2026 que sustenta los 85.916 calendarios y coincidencias exactas.

En el análisis vigente se seleccionó secano. Para arroz se conservaron las temporadas 1 y 2; en trigo se mantuvieron las alternativas de primavera e invierno, cuya selección para el análisis todavía debe cerrarse.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN]:** Adjuntar selección de secano/temporadas y justificar su elección; conservar como pendiente la decisión de trigo.

### 4.7.2 Conversión de hitos fenológicos a fases

**Escalas y fases técnicas**

Las fuentes de fechas y las escalas de desarrollo cumplen funciones diferentes. GGCMI aporta siembra y madurez; las escalas permiten nombrar y ordenar las etapas intermedias. La tabla maestra utilizó ocho bloques técnicos por cultivo:

> **RESPALDO NECESARIO — [CITA + EVIDENCIA]:** Vincular GGCMI con los extremos y el catálogo del proyecto con los ocho bloques. Cada fila de la tabla siguiente requiere la referencia de su escala y el registro de agrupación.

| Cultivo | Escala registrada | Bloques técnicos |
|---|---|---|
| Arroz | BBCH | 00–09; 10–19; 20–29; 30–39; 40–59; 60–69; 70–79; 80–99 |
| Maíz | Hanway/USDA, escala V/R | VE; V1–V6; V7–VT; R1; R2; R3; R4–R5; R6 |
| Soya | Fehr–Caviness | VE–VC; V1–Vn; R1–R2; R3; R4; R5; R6–R7; R8 |
| Trigo | Zadoks/BBCH | Z00–09; Z10–29; Z30–39; Z40–49; Z50–59; Z60–69; Z70–89; Z90–99 |

> **PENDIENTE DE AMPLIAR — Referencias de las escalas:** completar las citas bibliográficas originales de Hanway/USDA, Fehr–Caviness, Zadoks y BBCH, y explicar el significado de cada bloque. Los nombres anteriores son los registrados en la documentación local.

**Integración y calendario operativo actual**

Con las fechas de siembra y madurez de cada píxel construimos las fases intermedias utilizando una plantilla de fracciones del ciclo para cada cultivo. Esas fracciones se reescalaron entre los extremos locales y se conservaron en la tabla maestra. Las fechas intermedias son estimaciones del proyecto; no son observaciones anuales suministradas por GGCMI.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN]:** Vincular fracciones, fórmula, redondeo y script. Justificar o calibrar las fracciones; citar GGCMI para distinguir extremos de fases intermedias.

Después se homologaron los bloques técnicos en seis fases: establecimiento (EST), crecimiento vegetativo (VEG), floración (FLO), desarrollo reproductivo (REP), llenado de grano o semilla (FIL) y maduración (MAT). La correspondencia vigente es la versión regional-v4-2026-09-16. El orden depende del cultivo: REP puede preceder a FLO en arroz y trigo y seguirla en maíz y soya.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + JUSTIFICACIÓN]:** Citar guías de desarrollo para el orden biológico y la correspondencia v4 para los seis códigos operativos.

En maíz, R1 se asignó a FLO, R2 a REP, R3 y R4–R5 a FIL y R6 a MAT. En arroz, el bloque BBCH 30–39 se integró con embuchamiento y espigamiento en REP, y la antesis se asignó a FLO. En soya, R5 y el bloque R6–R7 se asignaron a FIL y R8 a MAT. En trigo se conservó la correspondencia revisada de seis ventanas.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + JUSTIFICACIÓN]:** Respaldar cada asignación por cultivo con la guía y el archivo v4; explicar los bloques agregados y límites que no están observados.

Verificamos que las ventanas fueran continuas, no se superpusieran y cubrieran todo el ciclo. Al repetir el calendario típico en cada año, conservamos el mes y día de las fronteras, incluyendo el 29 de febrero cuando correspondiera. Cuando el ciclo cruza diciembre se conserva el desplazamiento de año y la temporada se identifica por el año de siembra. Los cálculos utilizan los calendarios por píxel en JSON; el CSV permite revisar las fechas y la correspondencia.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN]:** Vincular pruebas de continuidad, cobertura, años bisiestos y cruce de diciembre; documentar convención de año de siembra y archivos JSON/CSV.

> **PENDIENTE DE AMPLIAR — Fechas intermedias:** documentar las fracciones utilizadas, su justificación y la incertidumbre. Los registros no establecen una calibración bibliográfica por cultivo y lugar para cada fracción.

> **PENDIENTE DE AMPLIAR — Integración espacial y temporal:** describir la normalización de longitudes, el cruce entre los índices HDF5 y las coordenadas del calendario, los casos sin correspondencia, la selección de temporadas y la asociación entre año de siembra y año del rendimiento de GDHY.

> **PENDIENTE DE AMPLIAR — GEOGLAM y fuentes comparativas:** completar el enlace y la atribución de GEOGLAM CM4EW v1.3, identificar los archivos efectivamente utilizados de SAGE y MIRCA-OS y describir qué comparaciones se realizaron. Conservar la diferencia entre fuentes consultadas y fuentes incorporadas al cálculo.

**Revisión de las fases y construcción de la matriz**

Después de completar el calendario fenológico, lo que hicimos fue identificar para cada una de las fases. Nos falta hablar sobre la definición de fases estándares para cada uno de los cultivos. Entonces este proceso de definición de fases, pues se hizo de varias formas.

Primero revisamos cuáles eran las fases típicas macro de las que habla la FAO; son unas fases muy macro, son solo tres fases: las de establecimiento, como la etapa de siembra, crecimiento, pues como de vegetativo, reproductivo y cosecha.

> **RESPALDO NECESARIO — [CITA + VERIFICAR]:** Citar documento, página y nombres originales; comprobar atribución FAO y contradicción entre tres fases y categorías enumeradas.

> **PENDIENTE DE PRECISAR — Fases macro:** verificar el número y los términos exactos de las fases en la fuente consultada, así como su atribución a FAO o GEOGLAM. El dictado menciona tres fases, pero enumera más categorías; no cerrar esa correspondencia sin revisar la fuente.

Pero esto nos deja la información muy por fuera, mucha información de amenazas específicas por fuera. Entonces lo que hicimos fue buscar literatura que hablara de todas las fases de cada uno de los cultivos y armar una tabla maestra, una matriz grande en la que pudiéramos aplicar cuáles eran las fases y la terminología usada para cada tipo de cultivo según la literatura. Encontramos varias ampliaciones en los cultivos, en cada uno de los cultivos.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN]:** Vincular matriz de revisión, autores y criterios de búsqueda; mostrar qué detalle de amenazas se pierde con las macrofases.

> **PENDIENTE DE AMPLIAR — Fases encontradas por cultivo:** poner para el arroz cuántas fases encontramos, según cuáles autores, y así para maíz, trigo y soya. Distinguir el total de fases identificadas en la revisión de los ocho bloques técnicos adoptados por cultivo y de las seis fases homologadas finales.

Una vez tenemos la tabla, después de eso nos devolvimos al calendario fenológico típico y ajustamos con esas fases, pues definitivas y tomamos las decisiones en la homologación, en el ajuste, pues de definir cuál fase, cuál duración y según las fuentes, como correspondía, pues a cada etapa.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN]:** Documentar ajustes finales, versiones anterior y vigente, duración y fuente por frontera modificada.

## 4.8 Identificación de amenazas por fase fenológica

**Homologación en seis fases**

Otro criterio fue que no nos quedamos con las fases detectadas y construidas por las diferentes fuentes y las diferentes terminologías, sino que establecimos una equivalencia, una homologación para seis fases típicas en los cuatro cultivos.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN]:** Vincular tabla de homologación y explicar por qué se eligieron seis fases comunes.

Así la correspondencia se hizo de la siguiente manera: si un paper hablaba de una amenaza en una fase que cabía dentro de la fase de establecimiento, entonces esa amenaza era fase de establecimiento. Así, por ejemplo, otras tres amenazas en diferentes fases, pero esas tres fases eran parte de la fase reproductiva, entonces la homologación quedaba correspondiente a la fase reproductiva.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA]:** Añadir ejemplos reales con autor, fase original, ventana y fase homologada; respaldar inclusión biológica y temporal.

Por lo tanto, la tabla maestra construida tiene cuatro cultivos, tiene seis fases por cultivo, es decir, 24 datos de variable climática que amenaza cada una de esas fases y un umbral y la correspondencia directa con las bases de datos de ERA5-Land para poder hacer las correlaciones correspondientes.

> **RESPALDO NECESARIO — [EVIDENCIA + VERIFICAR]:** Vincular las 24 filas y su revisión; diferenciar variable disponible directamente de estadístico derivado y comprobar todas las equivalencias.

### 4.8.1 Amenaza

Posteriormente revisamos la literatura sobre las amenazas climáticas que afectaban cada una de las etapas de estos cultivos, que pudieran impactar el rendimiento o el crecimiento a nivel de la planta y la cosecha. Encontramos que todos los papers usan terminología diferente. No encontramos datos exactos sobre umbrales y amenazas específicas para cada una de las variables.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + VERIFICAR]:** Citar estudios y matriz comparativa que sustentan terminologías y vacíos. Delimitar «todos los papers» y «no encontramos datos exactos» al corpus revisado.

Sin embargo, dada la extensa información al respecto, se tomó la decisión de elegir las fuentes que hablaban sobre una amenaza específica y un umbral medible. Acá también teníamos otro criterio de la búsqueda de esta información y era que pudiéramos contrastar la variable medida con las fuentes de información de los datos disponibles de ERA5-Land, por ejemplo, con información de agroclimatología, variables como temperatura, precipitación.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA + JUSTIFICACIÓN]:** Documentar criterios de inclusión y fuentes elegidas; citar documentación ERA5-Land para disponibilidad de variables y cobertura.

También tenemos que decir que varias fases tenían más de una amenaza, pero lo que estamos eligiendo al final es una amenaza para cada fase, que cada fase tenga una amenaza, un umbral y una variable que se pueda medir y comprobar, contrastar con toda la data disponible en el rango de tiempo que tenemos del estudio y que podamos consultarlo de manera directa en ERA5-Land.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN + VERIFICAR]:** Vincular candidatas y selección por fase; verificar cobertura y equivalencia de cada variable, incluidas las derivadas y horarias.

> **PENDIENTE DE AMPLIAR — Selección final:** explicar cómo se eligió una amenaza entre varias candidatas por fase. Conservar la distinción entre umbral estimado, tratamiento experimental y criterio operativo, junto con la duración y la ventana de la fuente. Un tratamiento extremo no demuestra por sí solo el umbral de inicio del daño.

**Variables de las 24 filas de la tabla definitiva**

**Complemento documental:** la tabla `reglas_24_fases_vigentes.csv`, versión 2026-10-07, contiene 24 combinaciones cultivo–fase. No son 24 variables meteorológicas distintas. Las variables y los estadísticos seleccionados son:

> **RESPALDO NECESARIO — [CITA + EVIDENCIA]:** La tabla siguiente requiere trazabilidad POR FILA: autor/página para la amenaza y variable, fila de la matriz adoptada y producto/banda para su medición. El CSV citado al final respalda la selección, pero no sustituye las publicaciones originales.

| Cultivo | Fase | Variable o estadístico |
|---|---|---|
| Maíz | EST | Temperatura máxima diaria del aire |
| Maíz | VEG | Temperatura máxima diaria del aire |
| Maíz | REP | Temperatura máxima diaria del aire |
| Maíz | FLO | Temperatura máxima diaria del aire |
| Maíz | FIL | Temperatura máxima diaria del aire |
| Maíz | MAT | Precipitación total diaria |
| Arroz | EST | Temperatura media diaria del aire |
| Arroz | VEG | Temperatura máxima diaria del aire |
| Arroz | REP | Temperatura media diaria del aire |
| Arroz | FLO | Temperatura media diaria del aire |
| Arroz | FIL | Temperatura media diaria del aire |
| Arroz | MAT | Temperatura media diaria del aire |
| Soya | EST | Temperatura mínima diaria del aire a 2 m |
| Soya | VEG | Temperatura horaria del aire y permanencia en el nivel térmico definido |
| Soya | REP | Temperatura efectiva diaria: (temperatura media + temperatura máxima)/2 |
| Soya | FLO | Temperatura efectiva diaria: (temperatura media + temperatura máxima)/2 |
| Soya | FIL | Precipitación acumulada en la ventana R6–R8 |
| Soya | MAT | Precipitación acumulada en la ventana R6–R8 |
| Trigo | EST | Temperatura media diaria del aire a 2 m |
| Trigo | VEG | Temperatura horaria del aire, proxy de campo para helada |
| Trigo | REP | Temperatura horaria del aire, proxy de campo para helada |
| Trigo | FLO | Temperatura horaria del aire, proxy de campo para helada |
| Trigo | FIL | Temperatura horaria del aire, proxy de campo para helada |
| Trigo | MAT | Precipitación diaria y dos exposiciones sucesivas |

Para las variables diarias, el código utiliza ERA5-Land Daily Aggregates: `temperature_2m`, `temperature_2m_max`, `temperature_2m_min` y `total_precipitation_sum`. La temperatura se convierte de kelvin a grados Celsius y la precipitación de metros a milímetros. Las reglas de permanencia horaria requieren la colección horaria y no pueden comprobarse únicamente con máximas o mínimas diarias. La temperatura efectiva y los acumulados por ventana se calculan a partir de las variables fuente; no son bandas independientes del producto.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA]:** Citar fichas oficiales de ERA5-Land diario y horario y vincular código de bandas, unidades, conversiones, agregación y temperatura efectiva.

> **PENDIENTE DE AMPLIAR — Equivalencias y ejecución:** completar para cada fila el identificador de colección, banda, transformación, resolución temporal, duración, criterio de datos faltantes y unidad de conteo. Separar las reglas definidas para cuatro cultivos del cálculo completo ya auditado para maíz. Revisar el traslado de variables experimentales o de modelos al aire a 2 m y la aplicación de ventanas amplias, como R6–R8, a dos fases homologadas.

> **PENDIENTE DOCUMENTAL — Tabla definitiva:** incorporar las fuentes exactas por fila y resolver las observaciones de la revisión humana. En maíz FIL permanece la diferencia entre 32,7 °C en la regla utilizada y 32,9 °C en otra fuente documental.

Fuente del complemento: [Reglas de las 24 fases vigentes](</C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/amenazas/reglas_24_fases_vigentes.csv>). Los detalles anteriores proceden de la tabla definitiva, que debe distinguirse del catálogo histórico de 35 reglas de la web.

### 4.8.2 Umbral

En algunos casos fueron experimentos hechos con umbrales y se detectaron el punto máximo de amenaza; en otros estudios simplemente utilizaron, por ejemplo, varias etapas en las que se sometieron un cultivo a una temperatura de varios valores entre rangos, por ejemplo, y se determinó que en el rango extremo ahí ya la planta sí sufría, sin determinar exactamente si ese era el umbral límite o no.

> **RESPALDO NECESARIO — [CITA]:** Añadir ejemplos concretos con autor, tratamiento, resultado y página; distinguir umbral estimado de mayor tratamiento ensayado.

> **[DICTADO PARCIAL — PENDIENTE]:** Falta incorporar por cada una de las 24 filas el valor adoptado, unidad, operador, fuente y página, distinguiendo tratamientos de umbrales estimados.

### 4.8.3 Operador temporal

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictaron de forma completa operadores >, ≥, < o ≤, definición de episodio, acumulación y reglas para no duplicar eventos.

### 4.8.4 Duración y persistencia

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictaron las duraciones mínimas y persistencia de las 24 reglas. Diferenciar duración de fase, duración de exposición y duración experimental; citar cada valor.

## 4.9 Construcción de la base integrada

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictó el procedimiento completo de construcción de la base conjunta. La tabla de reglas de 24 filas no sustituye esa base de observaciones.

### 4.9.1 Unidad píxel-año

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictaron claves, estructura de filas, año de rendimiento frente a año de siembra, duplicados ni faltantes de la base integrada.

### 4.9.2 Integración con fases fenológicas

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictó el emparejamiento completo de exposiciones por fase con el rendimiento anual; precisar ciclos que cruzan años y temporadas múltiples.

### 4.9.3 Integración con eventos climáticos

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictó la estructura de integración de eventos con índices climáticos: fechas, categorías, amplitud, claves, agregación y datos faltantes.

## 4.10 Estimación de probabilidades

> **[DICTADO PARCIAL — PENDIENTE]:** El conteo de excedencias narrado se incorpora en 4.10.1. Falta precisar el paso de conteos y frecuencias a probabilidades, sus denominadores y la incertidumbre.

### 4.10.1 Probabilidad de excedencia de umbral

Lo otro que hicimos fue, una vez podemos consultar la data de ERA5-Land a través de Google Earth Engine, lo que hicimos fue traernos la variable que afecta la fase 1, por ejemplo, del cultivo 1, en esos días contamos cuántas veces se excedió el umbral de la amenaza y eso lo cruzamos con todos los años de cultivo en esas fechas, cuántas veces se excedió el umbral.

> **RESPALDO NECESARIO — [CITA + EVIDENCIA]:** Identificar colección GEE, consulta, fechas por píxel, regla de excedencia y salida; citar ERA5-Land y la plataforma utilizada.

Es decir, lo que hicimos fue un cálculo de frecuencias de las amenazas excediendo los umbrales en los años que tenemos de datos de rendimiento. Hasta ahí tenemos frecuencias de eventos de amenazas a los cultivos.

> **RESPALDO NECESARIO — [EVIDENCIA + JUSTIFICACIÓN]:** Vincular resultados y alcance por cultivo/fase; especificar conteo, exposición, denominador y faltantes para distinguir cantidades de frecuencias.

> **PENDIENTE DE AMPLIAR — Conteo y frecuencias:** describir la aplicación de las ventanas por píxel y año, el operador de cada umbral y la duración mínima. Precisar cuándo se cuentan días y cuándo episodios, cuál es el denominador de cada frecuencia y cómo se tratan los datos faltantes. Documentar el alcance ejecutado por cultivo y fase.

### 4.10.2 Probabilidad condicionada a ENSO

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictó el procedimiento de probabilidad condicionada a ENSO. Mantener como pendiente, sin inferir ejecución.

### 4.10.3 Probabilidad condicionada a MJO

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictó el procedimiento de probabilidad condicionada a MJO ni su combinación con ENSO. Mantener como pendiente, sin inferir ejecución.

## 4.11 Relación entre amenaza y anomalías de rendimiento

**Relación entre amenazas, variabilidad climática y rendimiento: trabajo en curso**

Posteriormente estamos trabajando en la correlación de esas amenazas con los índices ONI, MJO y temperatura superficial del mar para detectar probabilidades o cantidades de eventos y cómo afectaron el rendimiento, es decir, cuantificar el impacto y la relación variabilidad climática-rendimiento en unos datos de impacto finales de rendimiento. En eso estamos trabajando todavía.

> **RESPALDO NECESARIO — [JUSTIFICACIÓN + EVIDENCIA]:** Al completar el análisis, documentar método de asociación/probabilidad, índices y emparejamiento; respaldar cuantificación del impacto y sus límites. Mantenerlo como trabajo en curso.

> **PENDIENTE DE AMPLIAR — Análisis en curso:** describir por separado las correlaciones, las probabilidades condicionadas y el cruce con rendimiento; especificar el emparejamiento temporal, las unidades de análisis y la validación. Conservar el carácter de trabajo en curso y distinguir las asociaciones observadas de una atribución causal del impacto.

## 4.12 Identificación de potenciales triggers paramétricos

> **[SIN DICTADO — PENDIENTE DE DESARROLLAR]:** No se dictaron disparadores, función de pago, anticipación ni validación del riesgo de base. Se conserva como sección prevista; no como producto desarrollado.
