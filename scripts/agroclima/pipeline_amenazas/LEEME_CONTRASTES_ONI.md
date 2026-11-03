# Frecuencias por categoría ONI y contrastes

En PowerShell:

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\EJECUTAR_CONTRASTES_ONI.ps1
```

Usa la matriz corregida de `outputs/matriz_frecuencias_ONI_corregida_20261019_165114` en modo de solo lectura. Crea una nueva carpeta `outputs/contrastes_frecuencias_ONI_FECHA_HORA`. No usa GEE, no descarga datos y no incluye todavía rendimiento o MJO.

El lanzador utiliza el entorno Python ya existente de la tesis; requiere numpy y pandas. Para cambiar rutas, se admiten `-InputDir`, `-Output` y `-Python`. Para fijar el diseño antes de mirar resultados se admiten `-Bootstrap` (predeterminado 2000), `-Seed` (20261019) y `-MinYears` (5). No cambiar estos parámetros buscando intervalos favorables.

## Qué calcula

Cada píxel y fase se resume en frío, neutral y cálido según las categorías ONI de su ventana ya guardadas en la matriz. En calor se usa **episodios por 100 días** y en MAT **porcentaje de días de lluvia afectados**. Los contrastes son diferencias absolutas entre cálido y neutral, y entre frío y neutral. En MAT la diferencia está en puntos porcentuales, no en porcentaje relativo.

Se conserva la media del conteo original como columna descriptiva adicional, con unidades distintas entre calor y MAT. Esa columna no es la medida usada para los contrastes. No se suman episodios entre fases.

El bootstrap sortea las 36 temporadas con reemplazo. Cada réplica usa exactamente los mismos años y multiplicidades en todos los píxeles y fases; cada fila conserva la categoría ONI de su ventana. No se remuestrean días ni se cuentan los píxeles como años independientes. Se guardan los pesos sorteados para reproducibilidad.

Se conservan medias con al menos una temporada y diferencias cuando existen ambas medias. Los IC del 95 % usan percentiles 2,5/97,5 y se muestran solo con **al menos cinco temporadas por categoría** y al menos el 95 % de réplicas estimables. Las filas con menos temporadas no se borran: conservan estimación, n y un estado explícito; sus IC quedan vacíos. El piso de cinco temporadas no garantiza precisión ni suficiencia para inferir.

Los IC por píxel son exploratorios, sin corrección FDR y sin ajuste de autocorrelación entre temporadas. No sustituyen la inferencia formal regional del plan; no se interpreta el porcentaje de píxeles con un signo como evidencia independiente.

## Archivos de salida

| Archivo / tabla | Filas esperadas | Contenido |
|---|---:|---|
| medias_por_categoria.csv | 196.614 | Píxel, coordenadas, fase, medida, categoría, número de temporadas, media, IC y cobertura espacial. |
| contrastes_ONI.csv | 131.076 | Píxel y fase, contraste, n en ambos grupos, medias, diferencia, IC, estado y cobertura espacial. |
| contrastes_ONI.sqlite | — | Las mismas tablas y los diagnósticos D3, consultables sin límite de filas de Excel. |
| D3_tendencias_por_pixel.csv | 65.538 | Pendiente lineal de la exposición por década en cada píxel y fase. |
| D3_series_anuales_por_dominio.csv | 216 sin regiones | Exposición media de cada año y fase, inicialmente para CONJUNTO. |
| D3_tendencias_por_dominio.csv | 6 sin regiones | Pendiente de las series medias del conjunto y, si se aportan, de las regiones. |
| D3_categorias_por_decada.csv | variable | Reparto de observaciones píxel-temporada entre categorías ONI y décadas. |

También se generan pesos de bootstrap, guía y `completed.json`. Los CSV no tienen celdas combinadas ni grupos vacíos por presentación; repiten los identificadores en cada fila. Los faltantes se exportan vacíos y los ceros válidos se conservan.

## D3 y regiones

Las pendientes por década son descriptivas, no un criterio automático para decidir si una tendencia es despreciable. El reparto decenal cuenta observaciones **píxel-temporada**, no eventos ENSO ni años independientes. Las décadas de borde son parciales: 1981–1989 y 2010–2016.

CONJUNTO es la media con igual peso para cada píxel; no es ponderación por área cultivada. El diagnóstico global no reemplaza el regional del plan. Si todavía no se han definido regiones, el registro indica `D3_regional_pendiente=true`.

Se puede aportar una asignación previamente definida, sin solapamientos, con columnas `pixel_id,region`:

```powershell
.\EJECUTAR_CONTRASTES_ONI.ps1 -Regions 'C:\ruta\regiones_predefinidas.csv'
```

Solo se añaden diagnósticos D3 regionales; los IC formales de contrastes regionales quedan para su script específico. No se inventan regiones geográficas ni se seleccionan según resultados. La sensibilidad con exposición sin tendencia no se ejecuta todavía: se decidirá tras revisar D3.

No se generan mapas: antes hay que congelar escalas, revisar cobertura y acordar las regiones. La distinción de soporte espacial parcial de los 58 píxeles permanece en los resúmenes.

## Validación y ejecución

La entrega verifica sintaxis, remuestreo frente a cálculo manual, pendientes conocidas y medias de un píxel real frente a SQL. No se ejecuta aquí el análisis integral. El proceso completo comprueba dimensiones, claves, consistencia de medias y diferencias, coherencia de IC, integridad SQLite y exportación numérica CSV. Publica `completed.json` únicamente al terminar.

Puede tardar varios minutos según CPU y BLAS. Muestra avance por fase. No es reanudable y nunca sobrescribe salidas: si se interrumpe, repetir con otra carpeta nueva. No usar resultados de una ejecución sin `completed.json`.
