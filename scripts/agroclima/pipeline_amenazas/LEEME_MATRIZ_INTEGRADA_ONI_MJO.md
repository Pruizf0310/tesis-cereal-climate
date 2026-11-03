# Matriz integrada para continuar los cálculos

```powershell
cd 'C:\Users\paola\Documents\ChatGPT\Tesis\pipeline_amenazas'
.\CONSOLIDAR_MATRIZ_ONI_MJO.ps1
```

Lee únicamente las fuentes locales completas: matriz anual corregida, Tabla B MJO finalizada y resultados regionales ONI con contexto. No descarga datos ni consulta GEE. Guarda una carpeta nueva `matriz_integrada_ONI_MJO_FECHA_HORA` en la carpeta oficial de resultados de la tesis.

La entrega principal es `matriz_integrada.sqlite`. Incluye:

| Tabla o vista | Contenido / unidad de una fila |
|---|---|
| `anual` | Matriz original completa: píxel × temporada × fase |
| `mjo_mensual` | Píxel × temporada × fase × año calendario × mes × ONI mensual × estado MJO observado |
| `referencia_mes_oni` | Referencia incluyendo todos los estados MJO, sobre pares válidos del mismo píxel, temporada, fase y mes calendario |
| `matriz_calculo` | Resumen MJO con coordenadas, región y valores anuales repetidos en sus filas correspondientes |
| `contexto_regional_oni` | Las 216 estimaciones regionales, IC, años y frecuencias de los mapas |
| `matriz_con_contexto_oni` | Matriz anterior enlazada a los dos contrastes ONI regionales; agrega contraste a la clave |
| `cobertura_regional_mjo` | Píxeles, temporadas distintas y observaciones píxel-día por región, fase, mes, ONI y MJO |
| `control_reconstruccion_anual` | Comparación de los días, conteos y exposición consolidados con los originales |

También exporta la matriz plana completa `matriz_calculo.csv.gz`, tablas regionales CSV y un ejemplo de 100 filas con el contexto ONI. Sin límite de filas de Excel. No hay celdas combinadas. Los valores anuales y regionales se repiten como atributos: no sumarlos entre las filas donde se repiten.

Conserva por separado ONI promedio de la ventana anual y ONI del mes del día. El año calendario evita mezclar enero de años diferentes dentro de una temporada que cruza años. Los estados observados sin exposición conservan cero. Los datos faltantes quedan vacíos; combinaciones sin observaciones no se inventan como ceros.

Se calculan días válidos, días afectados equivalentes, ocurrencias calificadas y fracciones descriptivas. La diferencia contra la referencia del mismo mes y ONI es descriptiva dentro de cada temporada: todavía no es la estimación MJO estratificada entre temporadas con bootstrap. Los IC ONI regionales son atributos regionales, no IC de MJO ni de un píxel.

Se comprueba la lectura completa de cada partición y su hash, la conservación de filas, la integridad SQLite y que cada ventana reproduzca los conteos anuales originales. `completed.json` confirma finalización; `prueba_parcial` debe ser `false`.

Los 216 archivos diarios originales se conservan para análisis que necesitan secuencia diaria, como rezagos y pasajes MJO. La consolidación no reconstruye esa secuencia desde los resúmenes.
