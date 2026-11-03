# Maíz: base SQL y resultados consultables

`maize_base_sql.py` continúa a partir del cruce anual ya terminado. No descarga ni vuelve a calcular ERA5-Land. Lee los originales de `C:/Users/paola/Tesis` y escribe en `outputs/maize_sql`, dentro de esta carpeta de trabajo. Requiere numpy, pandas y matplotlib, disponibles en el entorno usado para los scripts anteriores.

Desde la carpeta que contiene el script, ejecutar con el Python del entorno:

```powershell
.\CONTINUAR_MAIZ_SQL.ps1
```

Ese lanzador usa la ruta del entorno Python existente, procesa los dos escenarios y crea una carpeta nueva con fecha. Para ejecutar un escenario manualmente:

```powershell
& 'C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas\.venv\Scripts\python.exe' -X utf8 .\maize_base_sql.py --output 'C:\Users\paola\Documents\ChatGPT\Tesis\outputs\maize_sql_completo'
```

Si ese entorno está en otra carpeta, usar su ruta completa. El script por defecto reutiliza la última ejecución de rendimiento con `completed.json`; `--run RUTA` permite fijarla. El resultado de rendimiento encontrado es `20261008_213708`, con ambos escenarios temporales completados. No necesita repetir ese ajuste.

Para el segundo escenario ejecutar otra vez con `--alignment maturity-year`. Se guardan separados; no elegir el escenario según el mejor ajuste. Para una prueba pequeña añadir `--limit-pixels 3` y otra carpeta de salida. Nunca sobrescribe una base existente. Una base `.pending.sqlite` es una ejecución incompleta, no un resultado publicado.

## Archivos

- `maize.sqlite`: SQLite estándar, con SQL, índices por píxel/año y un índice espacial RTree de centros. Abrir con DB Browser for SQLite o DBeaver.
- `pixels.geojson`: centros en longitud/latitud EPSG:4326 para QGIS. Es georreferenciación de píxeles, no polígonos de parcelas; `pixel_id` permite unir tablas. SQLite no se presenta como GeoPackage.
- `historia_pixel.png`: amenazas térmicas y rendimiento anual; `--pixel ID` elige el lugar.
- `rendimiento_por_ONI.png`: rendimiento medio por categoría ONI de la ventana y fase, con cantidad de años.
- `completed.json`: fuentes, hashes, cobertura y límites.

## Consultas

```sql
-- Historia completa de un lugar; reemplazar el ID.
SELECT * FROM consultation WHERE pixel_id=71854 ORDER BY season_year,phase;

-- Todos los lugares en un año.
SELECT * FROM consultation WHERE season_year=1998;

-- Diferencia observada respecto a temporadas neutrales del mismo lugar/fase.
SELECT * FROM differences WHERE pixel_id=71854;

-- Rendimiento de temporadas con >=10 días de cada combinación ONI–MJO.
-- 0 es MJO débil; 1–8 son fases activas. No son días de amenaza confirmada.
SELECT * FROM joint_yield WHERE pixel_id=71854 ORDER BY phase,index_combination;

-- Episodios Niño/Niña que se superpusieron a una fase agrícola.
SELECT * FROM episode_overlap WHERE pixel_id=71854;

-- Cuántos episodios distintos (no cuántos años/fases).
SELECT state,count(DISTINCT episode_id) FROM episode_overlap
WHERE pixel_id=71854 GROUP BY state;

-- Selección espacial por rectángulo de centros.
SELECT p.* FROM pixels p JOIN pixel_bounds b USING(pixel_id)
WHERE b.min_lon BETWEEN -76 AND -72 AND b.min_lat BETWEEN 0 AND 5;
```

`annual` conserva una observación por píxel/temporada. `phase_exposure` tiene seis filas por temporada, con reglas, cobertura, fechas, conteos y exposición a índices. `daily_indices` conserva ONI y MJO por fecha una sola vez: no multiplica innecesariamente la tabla diaria por todos los píxeles. `pixel_models` y `phase_associations` conservan los ajustes y su validación de la ejecución original.

## Qué responde y qué sigue pendiente

La base permite consultar frecuencias, rendimientos observados, diferencias frente a neutralidad y exposición a las ocho fases de MJO. Las tablas conjuntas cuentan temporadas, no toman cada día como un rendimiento independiente. Una temporada puede aparecer en varias combinaciones: sus grupos se superponen. Diez días y cinco temporadas son mínimos descriptivos explícitos, no pruebas estadísticas.

La categoría ONI por fase usa su media ponderada por días. `oni_episodes` identifica por separado secuencias de al menos cinco centros mensuales consecutivos con ONI >=0,5 o <=-0,5 y conserva el pico numérico; no etiqueta automáticamente «severo». Los episodios se detectan usando toda la serie ONI disponible antes de seleccionar ventanas 1981–2016. Los meses ONI representan índices trimestrales centrados, no observaciones diarias independientes.

Para demostrar coincidencia entre **días afectados** y MJO en las seis fases de todos los píxeles sigue faltando completar la extracción diaria. La base no inventa esa coincidencia a partir de conteos anuales. El script existente `maize_mjo_diario.py --limit 0 --workers 4` hace esa extracción con GEE, conserva caché, verifica contra los conteos anuales y luego `probabilidades_oni_mjo.py --daily-run RUTA` calcula días afectados condicionados a los índices. Es un cálculo distinto y potencialmente largo; no se lanzó aquí.

La diferencia de rendimiento es una asociación histórica en las unidades originales sin tendencia. Las unidades y la convención de cosecha no están documentadas suficientemente para porcentajes de pérdida. Los episodios son compartidos entre lugares; no contar cada píxel como un Niño independiente. La comparación MJO no demuestra aporte adicional, causalidad ni anticipación: requiere ajuste estacional, referencia bajo el mismo ONI, incertidumbre y validación en años excluidos.
