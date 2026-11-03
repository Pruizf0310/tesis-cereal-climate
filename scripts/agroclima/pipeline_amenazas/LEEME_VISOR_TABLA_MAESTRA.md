# Explorar la tabla maestra con Python

No requiere instalar paquetes: usa la biblioteca estándar de Python y abre las bases SQLite en solo lectura. No modifica resultados, no consulta GEE y no descarga datos. El visor escucha únicamente en `127.0.0.1`, no publica tus datos en internet.

## Abrir la vista

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\VER_TABLA_MAESTRA.ps1
```

Abre el navegador automáticamente. Conserva abierta la terminal; para cerrar el servicio usa Ctrl+C. Si no se abre el navegador, copia la dirección `http://127.0.0.1:PUERTO` que aparece en la terminal. El puerto se elige automáticamente.

La tabla anual principal se llama `pares_anuales`: 51 variables y 4.718.736 filas, una por píxel, temporada, fase y escenario de año. La otra base disponible contiene la matriz integrada ONI–MJO y sus tablas. El selector permite ver tablas analíticas, series y coeficientes sin mezclarlos con observaciones originales.

Funciones del visor:

1. Diccionario completo y buscable de todas las columnas. Descargable a CSV.
2. Filtros por región, fase, correspondencia de año, temporadas, píxel y otras categorías cuando están disponibles.
3. Vista de todas las columnas con desplazamiento horizontal; filas por páginas de 50, sin cargar toda la base. Puedes mostrar una selección de columnas.
4. Conteo exacto de las filas filtradas a petición.
5. Estadísticas y faltantes por variable: primeras 10.000 filas o conjunto filtrado completo. El alcance se indica explícitamente; las primeras filas no son una muestra aleatoria.
6. Dispersión configurable X–Y: un punto por temporada o primeras 1.000 filas válidas. La vista anual requiere fijar región, fase y correspondencia (y variable analizada si existe). No se calcula inferencia nueva.
7. Exportación completa del filtro a CSV hasta 100.000 filas. Si lo supera, exige restringir el filtro; no entrega una exportación silenciosamente truncada.
8. Guardar el gráfico a PNG y usar Imprimir/guardar PDF del navegador para conservar diccionario, perfil y gráfico de la revisión. La tabla ancha de filas se omite de la impresión.

## Primera exploración sugerida

- Base: Maestra anual + rendimiento; tabla: `pares_anuales`.
- Región: África austral; fase: FLO; correspondencia: `maturity-year`.
- Aplicar filtros. Examinar `pct_dias_afectados`, `z_rendimiento`, `oni_ventana` y `fraccion_dias_mjo_activa`.
- X: `pct_dias_afectados`; Y: `z_rendimiento`; un punto por temporada. Dibujar.
- Comparar después con `same-label`, sin elegir la correspondencia por la correlación que parezca más fuerte.
- Para consultar el análisis regional ya calculado, cambiar a `correlaciones_regionales` o `series_regionales_anuales` y fijar `variable = pct_dias_afectados`.

En la vista anual configurable se promedian X e Y sobre las mismas filas válidas, pero no se impone la cobertura regional del 95% utilizada por el análisis guardado. Para los resultados oficiales usa las tablas analíticas guardadas y sus intervalos. No agrupar filas de dos escenarios de año o distintas fases para crear un punto anual sin indicar esa mezcla.

## En terminal

Diccionario completo y cinco filas de ejemplo:

```powershell
.\VER_TABLA_MAESTRA.ps1 -Terminal
```

Para una muestra más estrecha:

```powershell
& 'C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas\.venv\Scripts\python.exe' -X utf8 .\visor_tabla_maestra.py --terminal --columns pixel_id,temporada,fase,region,pct_dias_afectados,z_rendimiento --limit 10
```

En cualquier tabla, vacío significa faltante; cero observado se conserva. La anomalía de rendimiento z no equivale a pérdida porcentual. La fracción espacial climática disponible no equivale a área cultivada. Las variables anuales repetidas en la matriz MJO mensual no deben sumarse entre filas.
