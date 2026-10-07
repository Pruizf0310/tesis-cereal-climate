# Piloto de frecuencia histórica: maíz, establecimiento, calor

**Ejecución vigente:** consulta [GUIA_EJECUCION.md](GUIA_EJECUCION.md). El comando `run` ya descarga directamente desde GEE y calcula los resultados. Los comandos `export/status` descritos abajo son la alternativa anterior mediante Drive.

Este paquete conserva los NetCDF/HDF5 originales. Parte de los índices H5 existentes y consulta la grilla ERA5-Land nativa dentro de cada celda GDHY de 0,5°. Guarda tres temperaturas diarias para reutilizarlas con otras reglas. No descarga la matriz de correlaciones.

## Antes de ejecutar

En `config.json`, poner el ID de proyecto GEE. Selección acordada: temporada principal y secano (`rf`); arroz conserva temporadas 1 y 2. La consolidación configura `calendar_dir` con los JSON por píxel versión regional-v4-2026-09-16 y confirma esa selección. No se asigna una variedad genética que GDHY no identifica. El calendario estima fases; no contiene observaciones anuales. Para el primer cálculo se usa EST y la regla Tmax ≥34 °C, racha ≥2 días, fuente Li EJA 2025.

Preparación genera candidatos sin lanzar tareas. Verifica `salidas/preparation.json` y `windows_candidate.csv`. Si no hay coincidencia espacial exacta, no asigna un calendario por cercanía.

## Ejecutar desde PowerShell / terminal de JupyterLab

```powershell
cd C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas
python -m pip install -r requirements.txt
python -m unittest test_eventos.py
python pipeline.py prepare
python pipeline.py authenticate
python pipeline.py export
python pipeline.py status
```

Descarga las exportaciones CSV de la carpeta `Tesis_ERA5_cache` de Google Drive y colócalas en `C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/ejecuciones/piloto_maize_EST/clima`. Luego:

```powershell
python pipeline.py analyze
```

Las tareas continúan en GEE aunque cierres Python. `tasks.json` evita reenviar automáticamente las mismas tareas; si fallan, consultar el error y retirar únicamente su entrada después de corregirlo. El clima exportado no depende del umbral: se reutiliza al cambiar la regla. Conserva columnas `x,y` de la grilla ERA, fechas y `pixel_id` estable para cruzar cultivos que comparten celda GDHY. Para ampliar cultivos se requiere preparar sus ventanas y reutilizar los CSV de los mismos píxeles; exportar únicamente celdas/años faltantes.

## Alcance y salidas

- Piloto por defecto: primeros 3 píxeles H5, años base 1981–1983. Incluye automáticamente años adicionales necesarios para fases que cruzan diciembre.
- `eventos.csv`: inicio, fin, duración y pico por evento/celda.
- `frecuencia_por_celda_fase.csv`: conteo anual por fase y celda, incluyendo ceros. Ventanas incompletas tienen conteos nulos, no ceros.
- `frecuencia_historica.csv`: eventos por temporada y proporción de temporadas afectadas, usando ventanas completas.
- `resumen_GDHY.csv`: promedio espacial de conteos y fracción del área evaluada afectada. No equivale a número de episodios meteorológicos independientes regionales ni a área cultivada afectada.
- `frecuencia_anual.png`: gráfico del piloto, calculado con datos reales descargados.
- `distribucion_frecuencias.png`: histograma de conteos por celda climática y temporada; incluye ceros.
- `provenance.json`: configuración y hashes de las entradas climáticas.

**Día UTC:** este extractor usa el producto diario de GEE. Si los umbrales requieren día local/nocturno u horas consecutivas hay que usar ERA5-Land horario y agregar con la convención temporal apropiada. No interpretar automáticamente los diarios UTC como día local. No se incluyen viento ni precipitación en este primer módulo.

**Calendario:** se supone DOY climatológico de 365 días, convertido a mes/día para conservar las fechas en años bisiestos. Confirmar esta convención con el calendario definitivo. Los años se etiquetan según el año base del calendario fuente; verificar relación con año de cosecha/rendimiento antes de hacer correlaciones.

**Espacio:** sample usa centros de celdas ERA dentro de la celda GDHY. Ponderación cos(lat), sin fracciones exactas de intersección en bordes y sin máscara subpíxel del cultivo. Se conserva la grilla original para mejorar esa ponderación posteriormente.

**Escala:** no poner todos los píxeles y 36 años de inmediato: este extractor crea una tarea por píxel/año. Está listo para un piloto y extracción por bloques pequeños; una ejecución global necesita empaquetar tareas por regiones/lotes y controlar cuotas. Colab no acelera el backend de GEE.

Fuente del producto: https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR
