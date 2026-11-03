# Tabla B diaria: clima + ONI + MJO

Ejecutar la tabla completa en PowerShell:

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\CONSTRUIR_TABLA_B_MJO.ps1
```

Para probar únicamente tres píxeles (incluido 81973, de cobertura espacial parcial fija):

```powershell
.\CONSTRUIR_TABLA_B_MJO.ps1 -Pilot
```

Guarda los resultados en la carpeta oficial de la tesis: `03_Resultados/Agroclima/vigente/correlaciones/maize_ONI_frecuencias/tabla_B_MJO_FECHA_HORA`. No sobrescribe resultados. Si se interrumpe, repetir en otra carpeta nueva; solo `completed.json` acredita finalización.

La tabla se divide en **216 CSV.gz**, uno por fase agrícola y temporada, para conservarla completa sin límite de Excel. Una fila es un píxel, temporada, fase y fecha. Las particiones comparten exactamente las mismas columnas; son una sola tabla lógica. El conjunto global puede ocupar varios GB y tardar bastante: cada día debe reconstruirse y exportarse. Se procesan cachés píxel a píxel; no se materializa toda la tabla en memoria.

Columnas: pixel_id, latitud, longitud, temporada, fase_cultivo, fecha, mes, fraccion_afectada, ocurrencias_calificadas_dia, oni_mes, cat_oni_mes, rmm1, rmm2, fase_mjo, amplitud_mjo, estado_mjo, mjo_valida, par_clima_oni_mjo_valido, estado_cobertura_espacial y fraccion_area_climatica_util.

El clima proviene de los cachés nativos existentes. Se verifican hashes, claves, fechas, reglas y soporte espacial fijo; se excluyen celdas permanentemente vacías. Un hueco temporal real detiene la recuperación. Los días afectados incluyen todos los días de una racha que cumple duración; la ocurrencia se anota en el día de calificación. MAT cuenta días.

Cada ventana reconstruida debe reproducir **conteo original y días afectados equivalentes** de la matriz anual corregida. Se verifica la lectura completa y el número de filas de cada CSV.gz antes de finalizar. No hay consultas GEE ni nuevas descargas.

ONI es el valor del mes centrado correspondiente a la fecha; la categoría usa ±0,5. No se confunde con el ONI promedio de ventana anual. RMM inválido se deja vacío. Estado débil: amplitud ≤1; fases activas 1–8 cuando amplitud >1, sujeto a valores RMM válidos. No se rellenan ausencias como MJO débil. Los días climáticos se conservan aunque falte índice y se marca el par válido.

Esta etapa construye la Tabla B. Todavía no genera probabilidades MJO, contrastes, regiones o bootstrap: eso se hará después de verificar cobertura por mes, ONI y estado MJO. La fracción espacial disponible no equivale a área cultivada.
