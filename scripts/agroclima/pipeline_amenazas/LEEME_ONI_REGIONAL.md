# Propuesta de regiones y análisis ONI regional

La propuesta está en la carpeta oficial de la tesis, `propuesta_regiones_geograficas_20261020`, con mapa y tabla para revisar. No se usaron los contrastes ONI ni el rendimiento para definir límites.

## Revisar la propuesta

Se asigna el **centro del píxel** a los polígonos de países del mapa Natural Earth 1:110m existente. La región es su atributo SUBREGION, traducido al español. Son subregiones geográficas amplias, no zonas productoras ni regiones agroclimáticas homogéneas. La atribución de territorios y países transcontinentales proviene del mapa y debe revisarse. No se afirma equivalencia exacta con otra clasificación ONU actualizada.

Los centros sin intersección, islas no representadas o fronteras entre subregiones quedan **sin asignar**, con motivo explícito. No se les atribuye un país vecino por proximidad. Están en `pixeles_sin_asignacion.csv`. Revisar esos casos mediante geometría/dominio antes de cerrar regiones; tampoco se asigna un píxel basándose en su signo ONI.

Se puede editar/copiar `regiones_propuestas_para_revisar.csv`, conservar las columnas `pixel_id,region` y guardar una versión revisada. La propuesta original debe mantenerse como registro. Cada píxel admite una sola región.

## Ejecutar el análisis con la tabla que decidas utilizar

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
$regionesOni='C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias\propuesta_regiones_geograficas_20261020\regiones_propuestas_para_revisar.csv'
.\ANALISIS_ONI_REGIONAL.ps1 -Regions $regionesOni
```

Ese comando usa la propuesta, por lo que sus resultados siguen siendo provisionales. Sustituir la ruta por la versión revisada cuando se acuerde. No hay una regionalización oculta predeterminada: el lanzador exige indicar el archivo.

Atajo para seleccionar **explícitamente** esa propuesta provisional:

```powershell
.\ANALISIS_ONI_REGIONAL.ps1 -Proposal
```

Sin `-Proposal` ni `-Regions`, el lanzador se detiene: no elige regiones de manera implícita.

Lee la matriz corregida en modo de solo lectura. No usa GEE ni la Tabla B MJO; se puede ejecutar mientras se construye esta última. Requiere numpy y pandas del entorno existente. Guarda una carpeta nueva `ONI_regional_FECHA_HORA` dentro de la tesis.

## Estimación principal y calendario local

Para región, fase y contraste (cálido−neutral o frío−neutral):

1. Conservar la categoría del ONI de la ventana de **cada píxel**.
2. Seleccionar un soporte fijo de píxeles con al menos cinco temporadas válidas en ambos grupos.
3. Calcular la media de exposición de cada grupo **dentro de cada píxel**.
4. Restar las dos medias dentro del píxel y promediar esas diferencias, dando igual peso a cada píxel elegible.

Así no se impone una categoría única a toda la región ni se confunde un cambio de composición espacial entre grupos con un contraste dentro de los mismos lugares. Es un promedio regional estandarizado por píxel, no un simple promedio de todas las filas agrupadas por ONI.

Se usa episodios/100 días en calor y porcentaje de días afectados en MAT; las diferencias de MAT están en puntos porcentuales. La ponderación es por píxel, no por área cultivada. Los 58 píxeles recuperados conservan su soporte espacial parcial y se cuentan en la cobertura.

## Incertidumbre

Dos mil réplicas, semilla 20261019. Se sortean los mismos 36 años y multiplicidades para todos los píxeles de todas las regiones y fases. No se remuestrean píxeles ni días. Cada réplica recalcula las medias dentro de píxel.

El soporte de píxeles se mantiene fijo. Si una categoría queda sin observaciones para algún píxel de ese soporte en una réplica, esa réplica regional no es estimable; no se elimina el píxel de forma silenciosa. Se publica IC percentil 95 % si al menos 95 % de las réplicas son estimables. De lo contrario se conserva la estimación puntual, pero el IC queda vacío y se indica el motivo.

El soporte de cálido−neutral puede diferir del de frío−neutral. Se guarda la lista para cada contraste. Se reportan n de píxeles elegibles y mínimo/mediana/máximo de temporadas por categoría, en lugar de presentar observaciones píxel-temporada como años independientes.

El bootstrap conserva la dependencia espacial compartida por año. No ajusta explícitamente autocorrelación entre temporadas de un evento ENSO ni multiplicidad. Su interpretación depende de las regiones, cobertura y supuestos fijados; un IC no identifica causalidad.

## Archivos

- `contrastes_regionales.csv`: medias en soporte común, diferencias, IC y cobertura.
- `soporte_por_contraste.csv`: elegibilidad de cada píxel por región/fase/contraste.
- `series_anuales_descriptivas.csv`: medias anuales de la región y por categoría local. La composición por categoría puede cambiar: son descriptivas, no el estimador principal.
- `D3_tendencias_regionales.csv` y `D3_categorias_por_decada.csv`: diagnóstico regional de tendencia y reparto ONI por décadas, con décadas extremas parciales.
- `ONI_regional.sqlite`: las mismas tablas.
- Asignación usada, píxeles fuera del dominio, pesos bootstrap, fuentes y hashes.
- `completed.json` únicamente al terminar los controles.

No sobrescribe ni reanuda carpetas existentes. El análisis integral no se ejecutó durante la preparación del script; se verificaron funciones con ejemplos de resultado conocido. La propuesta geográfica sí se generó para revisión.
