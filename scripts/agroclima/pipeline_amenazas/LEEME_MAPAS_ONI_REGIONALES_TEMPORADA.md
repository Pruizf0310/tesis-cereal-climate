# Mapas regionales ONI en conteos por temporada

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\MAPAS_ONI_REGIONALES_TEMPORADA.ps1
```

Este lanzador **sí genera mapas** a partir de `ONI_regional_conteos_temporada_20261020_144451`. No repite las estimaciones, bootstrap ni MJO y no modifica las tablas.

## Entrega

Seis figuras, una por fase (EST, VEG, FLO, REP, FIL y MAT), cada una en **PNG de 400 dpi y SVG**. En cada figura:

- Arriba: cálido−neutral; abajo: frío−neutral.
- Izquierda: mapa regional Equal Earth.
- Derecha: los 18 contrastes con intervalos del 95 % y número de píxeles elegibles entre corchetes.
- Una escala común de color para todas las figuras de calor; MAT tiene su escala propia.
- Borde sólido si el IC excluye cero y discontinuo si lo incluye; punteado si no se estima. No se ocultan regiones por significancia.

Calor: diferencia de **episodios medios por temporada y fase**. MAT: diferencia de **días medios de lluvia >10 mm por temporada**, no porcentaje ni episodios de calor.

El color es un resumen regional repetido en el polígono de la región, no una predicción para todos los lugares pintados. La lista de píxeles observados y elegibles sigue en las tablas. Los conteos no son tasas comparables entre ventanas de distinta duración. La comparación ONI se hizo dentro de cada píxel y fase.

Las regiones siguen siendo **provisionales**, según el atributo SUBREGION del mapa de países Natural Earth. Se comprueba que geometría y asignaciones coincidan con la propuesta usada; si se cambian regiones, hay que aportar geometrías compatibles antes de mapearlas. Rusia y otros casos transcontinentales heredan la clasificación de la propuesta, que debe revisarse antes de fijarla para el manuscrito.

## Salida

Se guarda una carpeta nueva en:

`C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias\mapas_ONI_regionales_temporada_FECHA_HORA`

Los nombres son `ONI_regional_EST_por_temporada.png/.svg`, etc. También se guardan `escalas_regionales_congeladas.json`, guía y `completed.json`.

Los límites de color son P98 de |diferencia|: ambos contrastes y cinco fases juntos para calor, MAT aparte. Las nueve clases son simétricas; extremos extendidos indican valores fuera del rango de color. Los histogramas cuentan regiones−contraste. Los ejes de intervalos incluyen todos los límites de IC, sin recortar; también son comunes entre fases de calor.

Para otra tabla o resolución:

```powershell
.\MAPAS_ONI_REGIONALES_TEMPORADA.ps1 -InputDir 'C:\ruta\otra_salida_por_temporada' -Dpi 600
```

Se admiten `-Output`, `-Formats png`, `-Scales` y `-Python`. Las escalas reutilizadas deben provenir de este script y cubrir íntegramente los intervalos actuales.

Requiere numpy, pandas y matplotlib, ya disponibles en el entorno usado. Los módulos `graficar_contrastes_oni_elegantes.py`, `proponer_regiones_oni.py` y `rutas_resultados_oni.py` deben permanecer junto al script. Sin Cartopy, nuevas instalaciones ni descargas. La preparación generó y revisó figuras de prueba a 120 dpi, sin ejecutar la exportación final.
