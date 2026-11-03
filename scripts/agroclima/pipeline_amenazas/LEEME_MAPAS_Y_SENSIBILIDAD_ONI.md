# Mapas y sensibilidad sin tendencia

## Graficar

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\GRAFICAR_MAPAS_ONI.ps1
```

Usa la sensibilidad ya calculada en `outputs/sensibilidad_ONI_20261019_211459` y crea otra carpeta con fecha, sin sobrescribir datos ni consultar GEE. Requiere numpy, pandas y matplotlib del entorno existente. No requiere Cartopy o pyproj y no descarga mapas: usa el GeoJSON local.

Produce cuatro figuras, cada una en PNG de 450 dpi y SVG:

1. Calor original: cinco fases × cálido−neutral / frío−neutral.
2. Calor sin tendencia: los mismos paneles y escala.
3. MAT original: los dos contrastes, en puntos porcentuales de días afectados.
4. MAT sin tendencia: los mismos paneles y escala de MAT.

Equal Earth esférica, celdas de 0,5° sin interpolar, paleta azul–blanco–naranja, nueve clases discretas, histogramas y escalas simétricas congeladas. La fórmula de proyección sigue la implementación esférica de OSGeo/PROJ: https://github.com/OSGeo/PROJ/blob/master/src/projections/eqearth.cpp .

El archivo `escalas_congeladas.json` se guarda antes de dibujar. El límite es P98 de |diferencia|, agrupando ambos contrastes y ambas versiones para asegurar comparación; calor con límite común para sus diez paneles y MAT con el suyo. Valores fuera de rango se conservan y se cuentan; se indican mediante extremos extendidos de la barra. La clase central incluye cero y valores próximos a cero; no representa una prueba estadística.

Puntos indican IC no estimable; los contrastes siguen visibles. No se usa el IC por píxel para ocultar valores ni para afirmar inferencia regional. Los 58 píxeles de cobertura espacial parcial fija se conservan y se documentan. Se generan mapas exploratorios: regiones e inferencia regional siguen pendientes.

Para reutilizar exactamente las mismas escalas en otra exportación:

```powershell
.\GRAFICAR_MAPAS_ONI.ps1 -Scales 'C:\ruta\mapas\escalas_congeladas.json' -Dpi 600
```

Se admiten `-SensitivityDir`, `-Output`, `-Outline`, `-Python`, `-Dpi` y `-Formats`. Para una vista rápida usar `-Dpi 150 -Formats png`. No cambiar escalas por fase para intensificar colores.

## Recalcular la sensibilidad si se necesita

```powershell
& 'C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas\.venv\Scripts\python.exe' -u -X utf8 .\sensibilidad_tendencia_oni.py --input '..\outputs\contrastes_frecuencias_ONI_20261019_211055'
```

Después indicar la nueva salida mediante `-SensitivityDir` al graficar. Se conserva el análisis original como principal. La sensibilidad utiliza anomalías respecto a una tendencia lineal por píxel y fase; la diferencia entre categorías es algebraicamente igual a la de los residuos de esa tendencia. No se recortan anomalías negativas a cero.

Se reutilizan los mismos 2.000 sorteos de temporadas que en el análisis original. En cada réplica se **reajusta la tendencia**, incluyendo la incertidumbre de esa estimación; no se trata la tendencia ajustada una vez como si fuera conocida. Los IC son percentiles exploratorios y no ajustan autocorrelación entre temporadas ni multiplicidad. Los años de rendimiento no participan en esta sensibilidad.

La comparación conserva 131.076 filas e incluye diferencia original, diferencia sin tendencia, cambio absoluto con signo, IC y cobertura. Los cambios de signo incluyen diferencias próximas a cero: no equivalen a evidencia independiente o a una reversión robusta. Las medianas globales pueden ser cero por la abundancia de ceros; revisar también magnitudes y patrones espaciales.
