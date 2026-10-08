# Ejecución vigente: cálculo de seis reglas dentro de GEE

```powershell
.\.venv\Scripts\python.exe .\maize_seis_fases.py
```

El comando ahora usa `maize_gee.py` y `config_maize_seis_fases_gee.json`. Procesa todos los píxeles H5 de maíz, 1981–2016, seis fases. Conserva el extractor local anterior y su caché; este motor no necesita descargar las series diarias. Los resultados anteriores no se borran ni se mezclan con los nuevos.

GEE transforma cada ventana en arrays diarios sobre la cuadrícula nativa de ERA5-Land, aplica el umbral y cuenta la racha cuando llega a su segundo día, solo si los dos anteriores no eran ya parte de una racha. Una racha larga se cuenta una sola vez. Para MAT cuenta cada día >10 mm. Días enteramente ausentes y máscaras son huecos, nunca ceros válidos. Convierte kelvin a Celsius y metros a milímetros. Evalúa por celda ANTES de promediar en el píxel GDHY. Devuelve conteo medio, fracción espacial con eventos y cobertura por píxel, año de siembra y fase. Excluye celdas incompletas del promedio y conserva su indicador de cobertura.

Por defecto combina cuatro píxel-años (24 resultados de fase) por solicitud, con dos solicitudes concurrentes. No crea tareas de Drive ni requiere ampliar los permisos OAuth. Los lotes terminados se guardan de forma atómica con hash de integridad y versión de reglas/código/calendario. Ctrl+C detiene el envío de nuevos lotes; las solicitudes ya enviadas pueden tardar en cerrar. Repetir el mismo comando reutiliza los lotes completos. El avance se imprime cada lote y cada 15 segundos durante la espera; la estimación se basa en el ritmo real y puede cambiar por cuotas o condiciones del servicio.

Opciones de prueba: `--limit 1 --start-year 1981 --end-year 1981 --workers 1 --batch-size 1`. Se recomienda una configuración de salida separada para pruebas porque los consolidados corresponden a la selección de la última ejecución terminada; los lotes individuales anteriores permanecen guardados. No ejecutar dos instancias sobre la misma carpeta.

Resultados vigentes: `C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\ejecuciones\maize_seis_fases_GEE_1981_2016`. Al terminar genera `resumen_GDHY_anual.csv`, `frecuencia_historica_GDHY.csv`, `frecuencia_anual_conjunto.csv` y `frecuencia_seis_fases.png`, y los copia al repositorio local. El consolidado histórico promedia los conteos anuales medios por celda de cada píxel GDHY; no es un conteo de sistemas meteorológicos únicos. Los gráficos del conjunto dan igual peso a cada píxel GDHY y solo usan cobertura completa.

Este motor devuelve resúmenes anuales, no listas de fechas de cada episodio ni las temperaturas diarias. La caché anterior permite revisar fechas en los píxeles ya descargados. El código y los resultados distinguen `episodes` para calor de `days` para lluvia.

Se mantienen las decisiones científicas de la versión anterior: EST=VE; VEG=V7_VT como proxy de V6–VT; FLO=R1 y REP=R2, particiones exclusivas dentro de la ventana R1–R3 de la fuente; FIL=R3+R4_R5; MAT=R6 como bloque terminal disponible. Fechas estimadas, días UTC, rachas recortadas en límites de fase. No sumar fases como episodios únicos; la asociación con rendimiento requiere validar el año de cosecha. FIL conserva 32,7 °C de la tabla vigente, con la discrepancia documental de 32,9 °C pendiente de revisión humana. Los textos originales y límites de cada regla quedan en el plan de ejecución; la tabla maestra no se modifica.

Referencias técnicas: https://developers.google.com/earth-engine/apidocs/ee-image-arrayslice y https://developers.google.com/earth-engine/apidocs/ee-image-arrayreduce
