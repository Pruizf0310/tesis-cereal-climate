# Construir la matriz de frecuencias con ONI

Desde PowerShell:

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\CONSTRUIR_MATRIZ_FRECUENCIAS_ONI.ps1
```

Usa el entorno Python existente en `C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas\.venv`. No instala dependencias, no descarga datos y no consulta GEE. Requiere numpy y pandas. Dejar juntos `construir_matriz_frecuencias_oni.py` y `correlacion_oni_amenazas.py`.

Si cambian las rutas:

```powershell
.\CONSTRUIR_MATRIZ_FRECUENCIAS_ONI.ps1 -TesisRoot 'D:\Tesis' -Python 'D:\entorno\Scripts\python.exe' -Output 'D:\Resultados\matriz_ONI_nueva'
```

También puede ejecutarse directamente:

```powershell
& 'C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas\.venv\Scripts\python.exe' -u -X utf8 .\construir_matriz_frecuencias_oni.py --root 'C:\Users\paola\Tesis'
```

La salida predeterminada se crea en `outputs/matriz_frecuencias_ONI_FECHA_HORA`, al lado de la carpeta de scripts. Cada ejecución exige una carpeta nueva para no sobrescribir resultados. No es reanudable: si se interrumpe, repetir con una carpeta nueva. Solo una carpeta con `completed.json` representa una ejecución terminada; las salidas interrumpidas no deben utilizarse.

## Contenido

- SQLite con tabla `matriz` y clave única `(pixel_id, temporada, fase)`.
- La misma matriz en CSV comprimido `.csv.gz`.
- Ejemplo real de un píxel con 216 filas, abrible en Excel.
- Controles de calidad, ONI mensual, fuentes y hashes, y guía breve.

Se esperan 2.359.368 filas: 10.923 píxeles × 36 temporadas × 6 fases. La matriz completa supera el límite de una hoja Excel. Se preservan ceros, se dejan vacíos los faltantes y las medidas no aplicables y no se combinan celdas. Las ventanas incompletas permanecen con estado explícito.

Incluye coordenadas, temporada, fase, fechas, días válidos, episodios, días afectados equivalentes, episodios/100 días, porcentaje afectado, ONI de ventana y categoría frío/neutral/cálido, más columnas de trazabilidad. Para MAT, episodios y episodios/100 días quedan vacíos: su conteo original corresponde a días de lluvia.

## Fuentes y validaciones

Usa las rutas completas ya identificadas de las seis fases, sus tablas anuales de exposición, el calendario incluido en el resumen anual original, los píxeles seleccionados y ONI v6. Mantiene FIL en 32,7 °C. Las rutas de cada ejecución de probabilidades están fijadas en `RUNS` para evitar elegir una ejecución diferente por fecha.

Comprueba claves, coordenadas, reglas, duración de ventanas, coincidencia entre conteos originales y reconstruidos desde los diarios, integridad SQLite y equivalencia entre CSV y SQLite. Verifica el promedio ONI por un cálculo independiente de días por mes. Detiene la publicación si una comprobación falla.

El proceso usa CPU, memoria y disco locales. No se ha completado una ejecución integral de esta versión: se comprobó la concordancia de conteos en EST y VEG durante la ejecución inicial, que fue interrumpida. La sintaxis se comprueba antes de entregar; los controles restantes se ejecutan localmente. No incluye todavía promedios agrupados, contrastes, bootstrap, rendimiento ni MJO.
