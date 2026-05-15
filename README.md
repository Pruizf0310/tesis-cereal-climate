# Tesis Cereal Climate

Repositorio vivo de la tesis de maestría **“Categorización de los impactos de variabilidad climática global en el rendimiento de cereales y generación de insumos para seguros paramétricos orientados a fortalecer la seguridad alimentaria”**.

El proyecto estudia cómo señales de variabilidad climática global, especialmente **ENSO (El Niño-Southern Oscillation)** y **MJO (Madden-Julian Oscillation)**, se relacionan con anomalías de rendimiento de cereales. La plataforma integra datos climáticos, rendimiento agrícola, correlaciones SST-rendimiento, fenología agrícola y visualización geoespacial para explorar posibles señales de riesgo y futuros triggers climáticos aplicables a seguros paramétricos agrícolas.

## Alcance actual

El foco operativo actual está en:

- ENSO / ONI como señal climática principal ya documentada con outputs livianos.
- MJO / RMM como componente climático identificado y en revisión.
- SST y correlaciones SST-rendimiento como base espacial del análisis climático.
- Rendimiento de maíz, arroz, trigo y soya.
- Fenología agrícola con calendarios GEOGLAM.
- Outputs livianos para visualización web y exploración de riesgo.

El repositorio no afirma todavía triggers definitivos ni resultados validados para seguros. La plataforma está diseñada para evolucionar desde exploración científica hacia insumos paramétricos reproducibles.

## Arquitectura del proyecto

```text
tesis-cereal-climate/
├── docs/                 # documentación técnica y estado del proyecto
├── data_info/            # fichas de datasets y fuentes
├── metadata/             # inventario de datos y metadatos livianos
├── scripts/              # scripts curados del flujo científico
├── notebooks/            # notebooks importantes y material por revisar
├── outputs/
│   └── web/              # derivados livianos para visualización
├── manuscript/           # insumos de escritura académica
├── web/                  # plataforma web interactiva
└── archive/              # notas sobre material no migrado
```

## Datos y componentes

- **GDHY yield datasets**: rendimiento de cereales; datos pesados fuera del repo.
- **SST**: campo climático para correlaciones SST-rendimiento; NetCDF fuera del repo.
- **ENSO / ONI**: índice climático con derivados livianos para exploración.
- **MJO / RMM**: componente identificado, pendiente de consolidar en outputs finales.
- **GEOGLAM**: calendarios agrícolas y ventanas fenológicas.
- **Correlaciones SST-rendimiento**: resultados pesados documentados, no versionados.
- **SOM / patrones espaciales**: resúmenes livianos disponibles para exploración preliminar.

## Plataforma web

La carpeta `web/` contiene un prototipo estático publicable en Vercel. La experiencia está pensada como una plataforma de **climate-food-risk intelligence**: mapa global, filtros por cultivo/señal/fase/riesgo, panel dinámico por pixel o zona y placeholders claros para capas futuras.

La web consume únicamente archivos livianos desde `outputs/web/` y deja preparada la conexión futura con `outputs/web_ready/` o `web/data/`.

## Reproducibilidad

- No versionar archivos mayores a 100 MB.
- No versionar HDF5, NetCDF, TIFF, NPY, NPZ ni ZIP.
- Mantener datos pesados en almacenamiento externo o archivo científico.
- Registrar fuente, ruta original, formato, periodo y uso de cada dataset.
- Convertir notebooks críticos a scripts reproducibles a medida que el flujo madure.
- Publicar solo derivados livianos y documentados en la web.

## GitHub, Vercel y Zenodo

La arquitectura prevista separa tres roles:

- **GitHub**: repositorio vivo para código, documentación, notebooks curados, metadatos y control de cambios.
- **Vercel**: despliegue de la plataforma web interactiva para exploración visual de riesgo climático-agroalimentario.
- **Zenodo**: archivo científico futuro para releases estables, DOI citable, preservación de resultados reproducibles y conexión con publicaciones académicas.

La integración con Zenodo no está implementada todavía. El proyecto queda preparado conceptualmente para publicar versiones estables mediante releases de GitHub y archivarlas en Zenodo cuando existan resultados validados.
