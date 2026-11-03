# Mapas regionales ONI con contexto

Ejecutar en PowerShell:

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\ONI_REGIONALES_MAPAS_CLAROS.ps1
```

El lanzador usa la matriz anual corregida y la asignación regional del resultado `ONI_regional_conteos_temporada_20261020_144451`. Recalcula los intervalos con 2000 réplicas de bootstrap: selecciona 36 años con reemplazo y comparte esos años entre todos los píxeles, regiones y fases. No remuestrea píxeles ni permuta etiquetas ONI. Conserva el soporte de píxeles elegibles y exige al menos cinco temporadas en cada grupo del contraste.

Produce 12 figuras, una por fase y contraste, en PNG de 300 dpi y SVG. Solo colorea las celdas del maíz analizado. El color representa el contraste regional repetido sobre esas celdas; no es una estimación individual por píxel. El panel lateral presenta el contraste con IC, años fríos/neutrales/cálidos como mediana [mínimo–máximo] entre los píxeles elegibles, frecuencia histórica de todas las temporadas, frecuencia neutral y número de píxeles elegibles. Los años varían por píxel porque las ventanas fenológicas difieren.

Una daga marca regiones con menos de 30 píxeles elegibles. Es un aviso descriptivo, no una regla de significancia ni de exclusión. Para cambiarlo:

```powershell
.\ONI_REGIONALES_MAPAS_CLAROS.ps1 -MinPixels 50
```

Los resultados se guardan en una carpeta nueva `ONI_regional_maiz_contexto_FECHA_HORA` dentro de:

`C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias`

Archivos de datos:

- `tabla_completa_figuras.csv`: 216 estimaciones con IC, medias, años por categoría, cobertura y marca de pocos píxeles.
- `tabla_celdas_del_mapa.csv.gz`: todas las celdas y su elegibilidad, coordenadas y estimación regional asociada.
- `soporte_pixeles_por_contraste.csv`: soporte explícito de cada contraste.
- `tablas_figuras.sqlite`: tablas de estimaciones y celdas en una base de datos.
- `bootstrap_anios_compartidos.npz`: años y multiplicidades de cada réplica, para auditar el cálculo.
- `completed.json`: confirma que terminó y registra parámetros y fuentes.

Calor: episodios medios espaciales por temporada. MAT: días medios espaciales con lluvia >10 mm por temporada. Los decimales son válidos. Las regiones siguen siendo provisionales. Los IC son exploratorios, sin ajuste por autocorrelación ENSO ni comparaciones múltiples. El script lee datos locales; no consulta GEE ni usa la tabla MJO en construcción.
