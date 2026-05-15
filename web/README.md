# Web: Climate-Food-Risk Intelligence

Interfaz estática inicial para una plataforma visual de climate-food-risk intelligence asociada a la tesis.

## Propósito

La web prioriza exploración geoespacial e interacción visual. No es una página metodológica ni un catálogo de outputs. Está diseñada para que el usuario pueda navegar un mapamundi, filtrar cultivos, seleccionar señales ENSO/MJO/SST, explorar fases fenológicas y abrir un panel dinámico por pixel o zona.

## Archivos

- `index.html`: estructura del observatorio y explorador climático.
- `styles.css`: diseño premium, responsivo y geoespacial.
- `app.js`: mapa Leaflet, carga de CSV livianos, click en puntos y panel dinámico.
- `README.md`: esta guía.

## Datos conectados actualmente

La web carga CSV livianos desde `../outputs/web/`:

- `rice_puntos_utiles_interseccion.csv`
- `maize_puntos_utiles_interseccion.csv`
- `wheat_puntos_utiles_interseccion.csv`
- `soybean_puntos_utiles_interseccion.csv`

También deja preparada la conexión conceptual con:

- `geoglam_fases.csv`
- `som_assignments.csv`
- `oni_yield_pixel_year_merged.csv`
- `trigger_summary_preliminar.csv`

## Placeholders sofisticados

La interfaz incluye placeholders marcados como demo/preliminar para:

- zonas agrícolas globales;
- franjas fenológicas;
- mapas de correlación SST-rendimiento;
- hotspots;
- clases SOM;
- niveles de riesgo;
- trigger candidates.

Estos placeholders no son resultados científicos finales. Deben reemplazarse por archivos validados en `outputs/web_ready/` o `web/data/`.

## Dónde conectar futuros outputs

En `app.js` hay comentarios `TODO` para conectar:

- GeoJSON de zonas de cultivo;
- tiles o imágenes de correlación/riesgo;
- JSON de triggers;
- CSV agregados por región/pixel;
- capas SOM o fenológicas.

## Correr localmente

Desde la raíz del repositorio:

```powershell
python -m http.server 8000
```

Abrir:

```text
http://localhost:8000/web/
```

## Vercel

Para desplegar como prototipo estático:

1. Usar la raíz del repositorio como fuente del proyecto.
2. Servir `web/` como carpeta de la página.
3. Mantener `outputs/web/` accesible porque `app.js` carga archivos con rutas relativas.
4. Si Vercel se configura con `web/` como root, copiar outputs livianos a `web/data/` y actualizar rutas.

## Regla central

No cargar ni publicar archivos pesados: HDF5, NetCDF, TIFF, NPY, NPZ, ZIP o derivados no validados.
