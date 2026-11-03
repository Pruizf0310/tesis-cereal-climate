# MJO y ocurrencias: Pearson semanal y figuras

Primera ejecución recomendada (10 píxeles, descarga RMM oficial y consulta GEE):

```powershell
cd "C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas"
.\.venv\Scripts\python.exe -X utf8 .\maize_mjo_semanal.py --download-rmm --limit 10 --workers 4
```

Después de revisar tiempo, cobertura y gráficos, todos los píxeles:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\maize_mjo_semanal.py --download-rmm --limit 0 --workers 4
```

El script **no se ha ejecutado sobre los datos reales** durante su preparación. No instala bibliotecas. Usa la autenticación ADC y el proyecto GEE del cálculo original. `--download-rmm` descarga el archivo oficial de BoM solo si falta `01_Data/RMM/rmm_official.txt`; los datos anteriores no se reemplazan. Si BoM rechaza la descarga, el mensaje pide guardar el archivo e indicarlo mediante `--index-file "RUTA"`. Un archivo ROMI nunca se usa como RMM automáticamente.

## Qué calcula

1. Recupera calendario y reglas del plan del cálculo de maíz completo, verifica la huella del calendario y utiliza los mismos píxeles guardados localmente. No necesita los H5 externos.
2. En GEE calcula ocurrencias por celda ERA5-Land, conserva el contexto completo de cada fase para identificar cada racha y agrupa las confirmaciones en bloques consecutivos de siete días. Una racha ≥2 días cuenta una sola vez, en el segundo día. MAT cuenta días con precipitación por encima del umbral. Se promedia espacialmente después del conteo nativo. Se excluye una fase con cobertura incompleta en alguna celda. Se conserva el recorte de rachas en límites de fase del cálculo original.
3. Descarga resúmenes semanales, **no todas las series diarias**. No es posible obtener esos resúmenes a partir de los conteos anuales existentes. Los bloques se anclan al comienzo de cada fase, no a la semana civil. Los últimos 1–6 días sueltos se descartan y las fases menores de siete días no aportan bloques. Este piloto no cubre esos fragmentos.
4. Empareja cada bloque completo con el promedio de RMM1 y RMM2 de exactamente esas siete fechas, sin interpolar faltantes. Calcula dos Pearson contemporáneos por píxel/fase a través de todas las semanas válidas, con un mínimo configurable de 20 semanas. Incluye semanas con cero ocurrencias.
5. Exporta tabla de coeficientes/n/estado, pares semanales comprimidos y dos figuras en inglés: seis fases para RMM1 y seis para RMM2. El piloto tiene mapas regionales ampliados; el cálculo completo tiene mapas mundiales. La escala es la misma, con intervalos de −1 a +1 y gris para correlaciones no definidas.

## Alcance y costo

El piloto contiene 10 píxeles del sur de Sudamérica disponibles en el listado, seleccionados antes de ver correlaciones: no es globalmente representativo. Son 360 solicitudes reanudables a GEE. El paquete completo son 393.228 solicitudes (una por píxel–temporada), cada una con varias semanas y fases. Puede requerir mucho tiempo; no prometer minutos. Se muestra ETA medida y una proyección global preliminar durante el piloto. El cuello de botella es GEE, no GPU local. Cuatro solicitudes simultáneas por defecto; límites de GEE y complejidad de las tareas pueden impedir que aumentar workers acelere.

Caché verificada por SHA256 en `02_Procesados/Clima_ERA5_Land_cache/MJO_semanal/<fingerprint>`. Para reanudar, repetir el comando: reutiliza solicitudes completas y vuelve a intentar las restantes. Una ejecución parcial no tiene `provenance.json` final. Los gráficos se generan al completar las solicitudes. Los resultados están en `03_Resultados/Agroclima/vigente/correlaciones/maize_MJO_semanal`, y se copian también al repositorio local. No se suben a GitHub automáticamente. No ejecutar piloto y paquete completo a la vez sobre la misma caché.

## Interpretación

RMM1 y RMM2 son componentes firmadas, no escalas de intensidad por separado. Un coeficiente positivo con RMM1 **no** significa «MJO más fuerte causa más eventos». Los dos mapas describen asociaciones con las dos componentes; una conclusión sobre fase/intensidad conjunta requiere otro análisis.

Es Pearson simple, sin significancia, ajuste estacional, detrend ni búsqueda de rezagos. Las semanas y píxeles no son independientes; incluso bloques sin solapamiento tienen dependencia temporal. Antes de inferir teleconexión se requiere controlar estacionalidad, tendencias y autocorrelación, y evaluar incertidumbre. El conteo depende de la fase y del umbral; los mapas no demuestran pérdidas ni capacidad predictiva. Se mantienen los límites documentales del calendario y los umbrales originales.

## OLR: después, como análisis separado

RMM ya incorpora OLR y vientos en su definición. No se debe añadir OLR local como si fuera una tercera componente independiente de MJO. El siguiente análisis puede extraer **anomalías de OLR local** de los NetCDF existentes, agregarlas a las mismas ventanas semanales y correlacionarlas con ocurrencias, documentando la resolución y el emparejamiento espacial. Sirve para explorar contexto convectivo, no para atribuir por sí solo la relación a MJO. No lo calcula este script.

Fuentes: https://www.bom.gov.au/climate/mjo/ y https://www.psl.noaa.gov/mjo/index.html

## Actualización: fechas diarias persistentes

El mismo comando ahora guarda primero las fechas, sin cambiar los umbrales ni el calendario. La caché nueva está en `02_Procesados/Clima_ERA5_Land_cache/MJO_fechas/<fingerprint>`; conserva y no confunde los lotes semanales anteriores.

- `daily_occurrences_with_MJO.csv.gz`: todas las fechas de cada fase, con ceros válidos, calidad, cobertura nativa, conteo medio espacial de ocurrencias confirmadas ese día y las dos componentes MJO diarias. Los últimos días que no completan una semana también se conservan.
- `native_events_with_dates_MJO.csv.gz`: una fila por racha y celda nativa, o por día de precipitación. Incluye identificación de celda, fase, umbral, inicio observado, fecha de confirmación, final observado, duración y banderas de contacto con el inicio/final de fase. Añade MJO en el inicio y en la confirmación. Las fechas son UTC. La confirmación del calor es el día N de la racha; el inicio observado es N−1 días antes. La duración/final pueden conocerse solo posteriormente: no usarlos como información disponible al anticipar el inicio.
- Caché `*.native.json.gz`: estados diarios de superación del umbral y validez por celda, para auditar y reutilizar sin volver a GEE. No contiene los valores originales de temperatura o precipitación.
- `verification_against_original_annual_counts.csv`: compara la suma diaria con el conteo anual original. Si hay discrepancias o faltan combinaciones, se detiene antes de publicar mapas de correlación.

Las filas nativas incompletas están señaladas y no deben tratarse como eventos válidos para inferencia. Para correlaciones se excluye toda fase con alguna celda incompleta, como en el cálculo original. Los eventos de fases distintas no representan necesariamente fenómenos independientes: se conserva el recorte original de rachas en límites de fase; un inicio/final observado allí no establece el inicio/final meteorológico real fuera de la fase.

Las correlaciones y figuras finales siguen siendo **semanales**: las fechas diarias quedan disponibles para cruzar después con días específicos o rezagos de MJO. Los pares con cero ocurrencias se conservan; no debe correlacionarse solo la lista de eventos positivos. El módulo `fechas_ocurrencias_core.py` debe estar junto al script principal. No se ejecutó GEE durante esta actualización; se verificaron localmente la reconstrucción de rachas, fechas y conservación de días de semanas parciales.
