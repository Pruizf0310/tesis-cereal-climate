# Maíz: probabilidades ONI y ONI–MJO para una fase

Ejecutar desde `C:\Users\paola\Tesis\02_Scripts\agroclima\pipeline_amenazas`:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\maize_probabilidades_una_fase.py --phase EST --workers 4
```

Incluye TODOS los píxeles del CSV vigente (10.923 en la versión actual) y TODAS las temporadas 1981–2016. No hay límite de diez píxeles. Usa el proyecto existente `jovial-opus-394022`, el calendario y las reglas congeladas del cálculo anual. EST: Tmax ≥34 °C, al menos dos días consecutivos. Es una regla histórica con ámbito regional de origen; su aplicación mundial no valida por sí misma la transferencia del umbral.

## Qué hace y cuánto tarda

1. Valida calendario, archivos RMM oficial y ONI v6, y píxeles seleccionados.
2. Reutiliza las matrices nativas verificadas del piloto, cuando existen.
3. Solicita a GEE únicamente la fase elegida. Agrupa hasta 36 años por píxel en una expresión. La paginación, los reintentos y la división de lotes por límites de recursos pueden aumentar las solicitudes reales.
4. Guarda matrices binarias diarias y validez por celda nativa, agrupadas por píxel. No descarga toda la serie de temperaturas ni vuelve a calcular las seis fases.
5. Calcula localmente episodios y días pertenecientes a episodios válidos, incluyendo todos los días de las rachas que alcanzan la duración mínima.
6. Calcula probabilidades ONI y ONI–MJO por píxel y mapas ONI. Conserva exposición anual para vincular posteriormente con rendimiento.

SÍ consume cómputo GEE. Cambiar la organización de las peticiones no elimina ese consumo. El modo restringido puede ralentizarlo. No hay un tiempo global validado: la consola estima el restante después de cuatro píxeles nuevos y actualiza esa estimación. Los tiempos de lotes grandes no son comparables directamente con los del piloto anterior.

Ctrl+C solicita la interrupción; algunas peticiones activas pueden tardar en terminar. Repite exactamente el mismo comando para continuar. Cada píxel terminado y los lotes climáticos completos quedan guardados. Los píxeles fallidos se anotan en `error.json`; su existencia no significa que la siguiente reanudación haya fallado. La finalización real se registra en `completed.json`.

`--workers 2` reduce concurrencia sin cambiar las rutas de reanudación. `--years-per-request 6` reduce el tamaño de cada expresión si las de 36 años son demasiado grandes; aumenta las peticiones y conserva la caché. No garantiza menor consumo. `--cache-only` prohíbe las consultas GEE y se detiene si falta información. Cambiar fase crea un producto independiente.

## Probabilidades y unidades

La probabilidad es la fracción de superficie nativa bajo un episodio válido, promediada sobre los días válidos de exposición a cada estado. Los ceros reales se conservan. Una fase con datos climáticos incompletos se excluye completa, según el criterio del cálculo anterior. La probabilidad no representa pérdida de rendimiento ni proporción de plantas dañadas.

ONI: categorías mensuales del índice centrado de tres meses: frío ≤−0.5 °C, cálido ≥0.5 °C, neutral entre ambos. NO son la clasificación oficial de episodios ENSO. El valor mensual se asigna a los días de su mes; esto NO agrega observaciones independientes ni lo convierte en un predictor disponible en tiempo real.

MJO: fase y amplitud oficiales diarias del archivo RMM. Amplitud ≤1: débil; >1: activa, fases 1–8. No se interpreta RMM1 o RMM2 por separado.

Los archivos incluyen probabilidad, días de exposición, número de temporadas y episodios por 100 días. La tabla conjunta también incluye una referencia de la misma época del año (mes) y categoría ONI, y la diferencia asociada al estado MJO. Las probabilidades crudas de la figura no están ajustadas estacionalmente; las referencias están en las tablas. No son pruebas causales ni de mejora predictiva fuera de muestra. Los mínimos de 30 días y tres temporadas son filtros de visualización, no garantías de precisión; las estimaciones sin cumplirlos se conservan con `eligible=False`.

No se calculan p-valores ni intervalos: la dependencia diaria y espacial debe abordarse con bloques antes de concluir que ONI o MJO informan de manera estable. El RMM oficial informa un cambio metodológico en 2014; requiere sensibilidad. No se ajustan aquí los modelos predictivos propuestos: este es el primer producto descriptivo y auditable.

## Archivos de salida

En `C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\probabilidades\maize_EST_global_1981_2016\<huella>`:

- `probabilities_ONI.csv`: probabilidades por píxel y categoría ONI.
- `probabilities_ONI_MJO.csv`: probabilidades conjuntas, exposición y referencia mensual dentro de ONI.
- `annual_exposure_for_yield_alignment.csv`: días equivalentes afectados y episodios medios por celda nativa, por píxel y temporada.
- `coverage.csv`: cobertura climática y conjunta por píxel.
- `global_ONI_probabilities.png/.pdf`: tres mapas globales, uno por categoría ONI, escala común 0–100 %.
- `por_pixel`: checkpoints completos y reanudables.
- `plan.json` y `completed.json`: procedencia y confirmación de finalización.

Al terminar, los productos finales pequeños se copian al repositorio local en `outputs/agroclima_vigente/probabilidades`. La caché climática queda en `02_Procesados/Clima_ERA5_Land_cache/ONI_MJO_una_fase`, sin duplicarla en Git. No se hace commit ni push automático.

El rendimiento no se correlaciona todavía. El calendario etiqueta temporadas por siembra; se debe verificar la correspondencia con el año de cosecha del rendimiento antes de unirlos. El rendimiento sin tendencia no es necesariamente señal climática exclusiva. Las fases se recortan a sus ventanas originales; no se suman episodios de fases diferentes como si fueran independientes.
