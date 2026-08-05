# Tabla maestra de fenología

El archivo canónico de respaldo es `outputs/tabla_maestra_fenologia_web.xlsx`.

## Alcance

- Cultivos: maíz, arroz, trigo y soya.
- Maíz, arroz y trigo: fases, coordenadas, días julianos y duraciones provenientes de GEOGLAM CM4EW Calendars v1.3.
- Soya: 4.955 coordenadas del inventario espacial de la calculadora. GEOGLAM CM4EW v1.3 no aporta un calendario de soya; por eso sus fases y duraciones permanecen vacías.
- Amenazas: matriz de literatura para los cuatro cultivos, aún sujeta a comprobación contra fuentes primarias.

## Relación con la web

El libro es el respaldo científico maestro. La aplicación no lee XLSX directamente; actualmente consume los derivados de `web-v2/public/data/`:

- `phase_calendar_windows.json`
- `phase_critical_thresholds.json`
- `phase_pixel_inventory.csv`
- `phenology_typical.json`
- `risk_pivot_v2.json`

Los calendarios de la interfaz agregan la fenología a tres macrofases (F1, F2 y F3) y aproximan ventanas mensuales a días julianos. No deben considerarse sustitutos de las filas GEOGLAM detalladas del maestro.

## Regla de actualización

No se debe completar una fase, duración o amenaza sin registrar fuente, enlace y estado de revisión. Cuando se seleccione un calendario externo de soya, deberá quedar identificado como no GEOGLAM y deberá regenerarse el JSON de ventanas usado por la web.
