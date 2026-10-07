# Ejecutar descarga, conteo y gráficos desde terminal

El entorno Python está instalado en `.venv` dentro de esta carpeta. Abre PowerShell y ejecuta:

```powershell
cd C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas
.\.venv\Scripts\python.exe .\pipeline.py run
```

La primera vez solicita el ID de proyecto habilitado en GEE y la autenticación de Google. El ID no es una contraseña. También puedes pasar `--project TU_ID` o definir `EE_PROJECT`. No se incluyen credenciales en el repositorio.

Si Google muestra “Esta aplicación está bloqueada”, detén el proceso anterior con Ctrl+C y ejecuta:

```powershell
.\.venv\Scripts\python.exe .\pipeline.py authenticate
.\.venv\Scripts\python.exe .\pipeline.py run
```

La autenticación corregida usa Google Cloud CLI cuando está instalado y solicita únicamente `cloud-platform`, aceptado por Earth Engine. No solicita Google Drive ni el permiso adicional de Storage de la configuración predeterminada. Se conserva el control IAM del proyecto. Esta corrección aborda una causa documentada de bloqueo OAuth; una política de cuenta/organización puede requerir revisión adicional. No se ha confirmado que resuelva la cuenta del usuario hasta completar el consentimiento.

Referencia: https://docs.cloud.google.com/docs/authentication/troubleshoot-adc#access_blocked_when_using_scopes

El comando prepara las ventanas de calendario, descarga automáticamente las tres temperaturas por meses y píxel, calcula eventos y genera CSV y gráficos. No requiere exportar ni descargar manualmente desde Drive. No cerrar la terminal mientras corre; si se interrumpe, repetir el mismo comando reutiliza los meses completos que ya están guardados y verificados por hash.

## Ubicaciones

- Código: `C:/Users/paola/Tesis/02_Scripts/agroclima/pipeline_amenazas/`.
- Clima compartido y reutilizable: `C:/Users/paola/Tesis/02_Procesados/Clima_ERA5_Land_cache/diario_UTC/`.
- Resultados: `C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/ejecuciones/piloto_maize_EST/`.
- Copia de resultados derivados: `C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/ejecuciones/piloto_maize_EST/`.

## Configuración inicial

Piloto real: 3 píxeles H5, años base 1981–1983, maíz secano EST, Tmax >=34 °C y >=2 días consecutivos. `config.json` permite modificar años y cantidad de píxeles; `pixel_limit=0` selecciona todos. Primero verificar el piloto y su duración: esta implementación hace consultas secuenciales por píxel y mes y no está optimizada para lanzar de golpe todo el dominio global.

Temperaturas conservadas: máxima, media y mínima del aire a 2 m, en °C. Se usa el producto diario UTC y su grilla nativa. Las reglas horarias/nocturnas requieren otro extractor. Las ventanas usan calendario por píxel versión regional-v4 y año de siembra; todavía no se relacionan estadísticamente con el año de rendimiento.

## Resultados generados

- `eventos.csv`: inicio, fin, duración y pico por evento/celda.
- `frecuencia_por_celda_fase.csv`: conteos por celda climática/año, incluidos ceros válidos.
- `frecuencia_historica.csv`: eventos por temporada y proporción de temporadas con eventos.
- `resumen_GDHY.csv`: conteo medio espacial y fracción del área evaluada afectada. No es área cultivada ponderada ni cantidad de episodios meteorológicos regionales independientes.
- `frecuencia_anual.png` y `distribucion_frecuencias.png`.
- `provenance.json`: configuración y hashes del clima usado.

Los años incompletos tienen conteos nulos y se excluyen del denominador de frecuencia. La copia al repositorio local ocurre después de completar el comando; publicar nuevas salidas requiere commit/push. El clima bruto se conserva en tesis, sin subir automáticamente bases grandes a GitHub.

Para recalcular con el clima ya guardado:

```powershell
.\.venv\Scripts\python.exe .\pipeline.py analyze
```

Si cambias píxeles, años o fases, ejecuta `run`: regenerará las ventanas y descargará lo que falte.

Autenticación manual opcional: `python pipeline.py authenticate`. Comprobaciones: `python -m unittest test_eventos.py`.

Pruebas automatizadas cubren continuidad, umbral, datos faltantes, años bisiestos, paginación y generación de tablas/gráficos con datos sintéticos. Eso no sustituye una ejecución real autenticada en GEE.
