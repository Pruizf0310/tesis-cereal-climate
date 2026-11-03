# Ubicación oficial de resultados — actualizada el 20 de octubre de 2026

Todos los scripts ONI de esta carpeta guardan por defecto las salidas en:

`C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente\correlaciones\maize_ONI_frecuencias`

Esto reemplaza las referencias a salidas predeterminadas en `Documents/ChatGPT/Tesis/outputs` de guías anteriores. Los scripts permanecen en la carpeta de trabajo; los resultados definitivos están físicamente en la tesis.

Se trasladaron las matrices original y corregida, contrastes, sensibilidad, mapas y diagnósticos, comprobando SHA256 antes y después. En las carpetas anteriores se conservaron junctions de compatibilidad, no copias de los datos. El registro completo está en `registro_reubicacion_20261020.json` dentro de la ruta oficial.

Mapas actuales: `mapas_ONI_20261020_091318`.

El archivo `rutas_resultados_oni.py` centraliza la ruta predeterminada. Los lanzadores también apuntan a las entradas oficiales. Una ruta explícita mediante `--output` / `-Output` prevalece sobre esta configuración. No es necesario volver a calcular nada para reubicar los resultados.
