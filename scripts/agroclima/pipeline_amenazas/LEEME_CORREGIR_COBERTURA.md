# Corregir cobertura espacial de los 58 píxeles

Ejecutar desde PowerShell:

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\CORREGIR_MATRIZ_COBERTURA.ps1
```

El lanzador toma por defecto la matriz terminada de `outputs/matriz_frecuencias_ONI_20261019_152551`. Usa Python del entorno existente de la tesis. El script de corrección solo necesita la biblioteca estándar de Python: no instala dependencias, no usa GEE y no descarga nada.

Para cambiar rutas:

```powershell
.\CORREGIR_MATRIZ_COBERTURA.ps1 -InputDir 'D:\Resultados\matriz_original' -TesisRoot 'D:\Tesis' -Output 'D:\Resultados\matriz_corregida_nueva' -Python 'D:\entorno\Scripts\python.exe'
```

También se puede ejecutar `corregir_matriz_cobertura_espacial.py` directamente con `--input CARPETA`, `--root RAIZ_TESIS` y, opcionalmente, `--output CARPETA_NUEVA`.

## Qué corrige

La regla anterior confundía celdas climáticas permanentemente sin datos con temporadas incompletas. Para cada uno de los 58 píxeles, el script vuelve a verificar las celdas de las **36 temporadas y las seis fases**, exige que el conjunto de celdas completas/vacías sea fijo, rechaza cualquier hueco temporal y calcula episodios y días afectados equivalentes sobre el soporte espacial disponible. Los pesos son coseno de latitud, como en los cálculos originales.

Se contrastan los 12.528 conteos recuperados con el resumen anual original. El script comprueba hashes de caché, fechas, reglas y longitudes de las series. Los índices ONI, sus categorías, fechas y calidad original se mantienen.

## Resultado

Se crea una carpeta nueva `outputs/matriz_frecuencias_ONI_corregida_FECHA_HORA` con:

- Base SQLite completa: **2.359.368 filas**, de las cuales se recuperan **12.528**, sin modificar las columnas preexistentes de las otras **2.346.840 filas**.
- CSV comprimido de la misma matriz, comprobado **fila por fila y columna por columna** frente a SQLite.
- Ejemplo real de un píxel recuperado: 216 filas.
- Control de calidad actualizado, fuentes/hashes y guía.
- `completed.json` únicamente al terminar y superar los controles.

La entrada se abre en modo de solo lectura y se copia mediante backup SQLite. No se modifica el archivo original ni sus CSV, los cachés o las fuentes. Cada salida requiere una carpeta nueva. El proceso no se reanuda; una ejecución interrumpida debe repetirse con otra salida. Se necesita espacio libre para otra base y otro CSV comprimido; su tamaño será mayor al original por las nuevas columnas.

## Cómo interpretar las columnas nuevas

| Columna | Interpretación |
|---|---|
| cobertura_temporal_completa | 1 si todos los días están disponibles sobre el soporte espacial utilizado. |
| estado_cobertura_espacial | `completa` para los píxeles anteriormente válidos; `parcial_fija` para los 58 recuperados. |
| fraccion_area_climatica_util | Fracción geométrica ponderada de las celdas con datos: entre aproximadamente 0,28 y 0,96 en los 58 píxeles. No es fracción de área cultivada. |
| celdas_validas_soporte_fijo | Número de celdas usadas en la recuperación; vacío en los otros píxeles, cuyo detalle nativo no se vuelve a auditar. |
| celdas_excluidas_sin_datos | Número de celdas permanentemente vacías en los recuperados; cero en los previamente completos. |
| recuperado_desde_cache | 1 en las 12.528 filas recuperadas; 0 en las demás. |

`estado_cobertura = completa` ahora significa cobertura **temporal** completa sobre el soporte disponible, incluyendo los recuperados. `calidad_origen` y `fraccion_cobertura_origen` no se alteran: las filas recuperadas conservan INCOMPLETE como etiqueta histórica. La distinción espacial queda explícita en las columnas nuevas.

No se rellena con cero la superficie sin datos ni se afirma que la porción observada sea toda la superficie de maíz. La ausencia espacial permanente se identifica a partir del conjunto observado 1981–2016, sin asumir por qué cada celda está vacía. MAT sigue contando días de lluvia y mantiene vacíos episodios y episodios/100 días.

Los 35 o 36 años de rendimiento no intervienen en esta corrección climática. Se conservarán las observaciones disponibles por píxel cuando se haga ese cruce.

## Verificación previa a entrega

Se comprueban sintaxis de Python/PowerShell y la reconstrucción en un píxel real, contrastando sus 216 ventanas con la auditoría previa. No se ejecuta aquí la corrección integral de la matriz: se lanza localmente. El proceso completo vuelve a verificar los 58 píxeles y todos los archivos de salida antes de declarar COMPLETO.
