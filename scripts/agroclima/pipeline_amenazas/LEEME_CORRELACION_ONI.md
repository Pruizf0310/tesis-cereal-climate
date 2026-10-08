# ONI v6 frente a amenazas por píxel y fase

Objetivo: evaluar asociaciones históricas entre ENSO y exposición a amenazas, antes de relacionarlas con rendimiento. Una correlación por píxel y fase utiliza hasta 36 pares anuales, 1981–2016. No se mezclan las seis fases como si fueran 216 años ni se consideran las celdas ERA internas como réplicas de ONI.

## Emparejamiento temporal

El ONI oficial tiene doce trimestres móviles centrados en cada mes: DJF=enero, JFM=febrero, …, NDJ=diciembre. No son doce anomalías mensuales independientes. Fuente elegida por la usuaria: ERSSTv6; copia original fechada conservada en `01_Data/ONI/ONI_v6_2026-10-08.html`. ONI v5 no se reemplazó.

Se asigna a cada día el ONI del trimestre centrado en su mes. Se promedia dentro de las fechas reales de la ventana utilizada por el motor de amenazas, ponderando por número de días. Ejemplo: 10 días en mayo y 20 en junio → `(10*ONI_AMJ + 20*ONI_MJJ)/30`. Mayo corresponde a AMJ y junio a MJJ. Si una ventana cruza de año se usan los índices del año siguiente correspondientes a las fechas. Los valores ausentes no se rellenan con el mes anterior.

Para cada píxel y fase: X=ONI medio ponderado de su ventana en cada año; Y=conteo medio de amenazas entre las celdas ERA completas del píxel GDHY en ese mismo año y ventana. EST/VEG/REP/FLO/FIL cuentan episodios de calor; MAT cuenta días de lluvia >10 mm. Por eso el mapa MAT tiene unidad de respuesta distinta aunque su coeficiente sea comparable matemáticamente.

## Cálculo y salidas

```powershell
.\.venv\Scripts\python.exe .\correlacion_oni_amenazas.py
```

Para medir sin calcular todas las permutaciones ni exportar pares:

```powershell
.\.venv\Scripts\python.exe .\correlacion_oni_amenazas.py --benchmark-only
```

Se ejecuta en CPU local, sin GPU, consultas a GEE ni H5 externos. Lee resultados por bloques de 100.000 filas, mantiene matrices de píxel×año, vectoriza los coeficientes y limita la memoria del remuestreo a bloques de 128 píxeles×64 permutaciones. Muestra tiempo de preparación, estimación del remuestreo por fase y tiempo total medido.

Spearman es la asociación monótona exploratoria principal, con rangos promedio para empates; Pearson es el contraste lineal. Mínimo configurable de 20 años válidos. Ceros de amenaza válidos se conservan. Series constantes no tienen correlación definida y se marcan como tales. Ventanas climáticas incompletas o ONI ausente se excluyen del par; no se sustituyen por cero.

P-valores exploratorios mediante 999 permutaciones de bloques de tres años, permutando ONI respecto de la amenaza; la misma permutación se usa en todos los píxeles y fases. Los bloques conservan el orden dentro de cada tramo, pero no garantizan representar toda la dependencia de ENSO. El remuestreo solo se calcula para series completas de 36 años; coeficientes de series más cortas pueden existir sin p-valor. Corrección Benjamini–Hochberg sobre todos los píxeles y seis fases conjuntamente, por separado para cada método. Resolución mínima de p=0,001; casos aislados pueden requerir más permutaciones para evaluar FDR.

Los mapas muestran coeficientes, no significancia: rojo=ONI más alto asociado a mayor frecuencia; azul=ONI más alto asociado a menor frecuencia. Gris=cultivo con correlación no definida o insuficientes pares. No implican causalidad. La significancia exploratoria se guarda en columnas p/q; requiere revisar estacionariedad, tendencias, longitud de bloques, estabilidad y sensibilidad antes de conclusiones de tesis.

Salidas en `03_Resultados/Agroclima/vigente/correlaciones/maize_ONI_v6`: dos figuras con seis paneles (Spearman/Pearson), tabla por píxel/fase con coeficientes/n/p/q/estado, pares temporales en CSV comprimido, ONI normalizado, resumen de cobertura y procedencia con tiempos. Se copian al repositorio local, sin commit automático.

## Alcance científico

Es una asociación contemporánea de fase (lag=0), no un pronóstico: el ONI centrado incluye meses vecinos y puede incluir información posterior al evento. No se busca el desfase que maximice la correlación. Explorar rezagos o seleccionar ventanas requeriría una hipótesis y validación separadas.

Se heredan las aproximaciones del calendario y las reglas ya calculadas: VEG V7–VT como proxy de V6–VT, FLO R1/REP R2 como particiones recortadas de R1–R3, MAT bloque R6 como proxy de secado y discrepancia FIL 32,7/32,9 °C. Estos mapas son provisionales respecto de esas decisiones. El año conserva la etiqueta de siembra; el cruce con rendimiento aún necesita validar el año de cosecha. No calcula ONI–rendimiento, amenaza–rendimiento ni MJO.

Fuentes: https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/ y https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html
