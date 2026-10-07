# Maíz: seis reglas, 1981–2016

Ejecutar desde esta carpeta:

```powershell
.\.venv\Scripts\python.exe .\maize_seis_fases.py
```

Sin `--limit`, procesa los 10.923 píxeles H5. Con `--limit 1` comprueba el primer píxel; la misma ejecución sin límite conserva sus fases terminadas. Ctrl+C conserva los meses y fases terminados; repetir el comando retoma lo pendiente. Un mes sin archivo de metadatos terminado se descarga nuevamente. No ejecutar dos instancias simultáneas sobre la misma carpeta.

Procesa un píxel por vez para limitar la RAM. Cada fase guarda tablas y gráficos inmediatamente. Temperaturas y precipitación usan archivos mensuales separados en la caché común. El progreso del paquete queda en `progreso_paquete.json`; el progreso mensual, en cada carpeta de fase. La estimación de paquete aparece al completar un píxel nuevo con las seis fases y no garantiza la velocidad futura de GEE.

Las reglas se leen de `reglas_24_fases_vigentes.csv`, sin editar la tabla maestra. Las cinco reglas térmicas requieren dos días consecutivos; MAT cuenta días individuales de precipitación estrictamente mayor que 10 mm. La precipitación de ERA5-Land `total_precipitation_sum` se convierte de metros a milímetros; las temperaturas, de kelvin a Celsius. Días UTC. Los años corresponden al año de siembra del calendario, incluyendo fechas del año siguiente cuando corresponde.

Ventanas del calendario: EST=VE; VEG=V7_VT, proxy disponible para V6–VT; FLO=R1; REP=R2; FIL=R3+R4_R5; MAT=R6, bloque terminal disponible. Fechas intermedias estimadas. FLO y REP conservan ventanas operativas exclusivas dentro de la ventana más amplia R1–R3 de la fuente. Las rachas se recortan en los bordes de fase: no sumar los conteos de fases como número de episodios meteorológicos únicos. MAT es un proxy del secado previo a cosecha, no una fecha observada de cosecha.

FIL mantiene 32,7 °C tal como aparece en la tabla maestra vigente. El fragmento documental previo reporta 32,9 °C en otra fuente: esta ejecución conserva la decisión vigente y no resuelve esa discrepancia editorial. Las fuentes completas, límites y textos literales quedan en `plan_ejecucion.json`.

Los resultados se guardan en `C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\ejecuciones\maize_seis_fases_1981_2016`. El consolidado final reúne resumen GDHY, frecuencias históricas por celda y eventos. Para consolidar las fases terminadas después de una interrupción:

```powershell
.\.venv\Scripts\python.exe .\maize_seis_fases.py --aggregate
```

El consolidado se copia al repositorio local; no hace commit/push automático. Los CSV climáticos completos permanecen en la tesis. Aún no se calcula la asociación estadística con rendimiento. Un cambio de reglas, calendario o código requiere una nueva carpeta de salida para no mezclar versiones.

Verificación: doce pruebas locales, incluidas lluvia >10 (excluye igualdad), días consecutivos contados individualmente en MAT, separación de caché lluvia/temperatura, ventanas entre años y consolidación que excluye fases incompletas. La descarga de precipitación real de GEE se ejecuta al iniciar el paquete; estas pruebas no sustituyen esa ejecución.
