# Resultados vigentes: amenazas y calendario

Versión de consolidación: 2026-10-07. Esta carpeta es el punto de entrada vigente de la tesis.

## Calendario adoptado

`calendario/calendario_seis_fases_secano.csv` contiene las seis ventanas por píxel, preservadas desde los JSON del repositorio, versión regional-v4-2026-09-16. Se conserva cada archivo fuente, manifiesto y correspondencia. Riego queda fuera de esta selección.

Maíz y soya: temporada única disponible. Arroz: temporada 1 y temporada 2, ambas de secano; no se interpretan universalmente como invierno/verano meteorológico. Trigo: alternativas primavera/invierno conservadas; la elección de un solo tipo sigue pendiente. No combinar sus rendimientos como observaciones independientes.

Es un calendario operativo coherente adoptado para el cálculo, no fenología anual observada. Las fechas intermedias son estimadas. Año base = año de siembra; verificar asociación con año de rendimiento antes del análisis estadístico. La tabla CSV es una vista auditable; para ejecutar se usan los JSON con límites semiabiertos, incluidos años bisiestos.

## Amenazas

`amenazas/tabla_maestra_revision_humana.xlsx` preserva la versión actual de la carpeta Fenologia y toda la auditoría, comentarios y colores, sin alteraciones.

`amenazas/revision_documental_24_fragmentos_exactos.xlsx` recupera la entrega con citas literales, páginas y procedencia por componente que había quedado fuera de la carpeta de tesis.

`amenazas/reglas_24_fases_vigentes.csv` reúne las 24 reglas de la tabla humana con los fragmentos de la revisión documental. `diferencias_revision_documental.csv` registra discrepancias entre las dos entregas; las aclaraciones documentales no se convierten silenciosamente en reglas aprobadas. La frecuencia de eventos todavía no se ha calculado en GEE.

## Código, resultados y repositorio

Código ejecutable: `C:/Users/paola/Tesis/02_Scripts/agroclima/pipeline_amenazas/`.

Piloto: maíz EST, Tmax >=34 °C, >=2 días consecutivos; tres píxeles, 1981–1983. Usa calendario por píxel de secano, con la correspondencia v4. Falta configurar ID de proyecto GEE y autenticar. El día climático de este piloto es UTC.

Todos los nuevos archivos del piloto se escriben en `ejecuciones/piloto_maize_EST/`. Las salidas derivadas y reportes se copian también a `C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/`. El clima bruto permanece en tesis; GitHub recibe su procedencia y resultados derivados, evitando subir las bases científicas masivas.

El repositorio actualizado de trabajo está en `C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/`. No continuar desde la copia antigua de Documents/Codex sin actualizarla. Versionar las nuevas salidas requiere commit/push; el pipeline no publica automáticamente resultados no revisados. La web no se modifica con esta consolidación.

`diagnosticos/` contiene inventarios GDHY y la comparación con los píxeles de correlación. No son conteos climáticos.


## Ejecución automática desde terminal

Comando vigente: `.venv/Scripts/python.exe pipeline.py run`, desde `C:/Users/paola/Tesis/02_Scripts/agroclima/pipeline_amenazas/`. Consulta `GUIA_EJECUCION.md` en esa carpeta. Descarga directamente desde GEE, conserva caché compartida en `02_Procesados/Clima_ERA5_Land_cache/diario_UTC/`, calcula y guarda CSV/gráficos en resultados. No requiere descargar manualmente desde Drive. Necesita ID de proyecto y autenticación del usuario.
