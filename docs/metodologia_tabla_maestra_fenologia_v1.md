# Tabla maestra global de fenología v1.0.0

La versión publicada el 5 de agosto de 2026 cubre arroz, maíz, soya y trigo por coordenada de 0,5°, sistema irrigado/secano y temporada. GGCMI Phase 3 v1.01 (`10.5281/zenodo.5062513`) aporta siembra y madurez; SAGE y MIRCA-OS se usan como comparación, no como sustitución automática ni validación totalmente independiente.

No existe una fuente global accesible que contenga todas las fases técnicas por coordenada. Por eso las fases intermedias se etiquetan como `process_model_endpoints_only`: una plantilla fisiológica por cultivo se reescala entre los extremos locales. Las fechas no son observaciones de campo y su confianza es baja o muy baja.

Las plantillas contienen ocho fases por cultivo:

- arroz: BBCH 00–09, 10–19, 20–29, 30–39, 40–59, 60–69, 70–79 y 80–99;
- maíz: VE, V1–V6, V7–VT, R1, R2, R3, R4–R5 y R6;
- soya: VE–VC, V1–Vn, R1–R2, R3, R4, R5, R6–R7 y R8;
- trigo: Z00–09, Z10–29, Z30–39, Z40–49, Z50–59, Z60–69, Z70–89 y Z90–99.

La web agrega estas fases en F1, F2 y F3 únicamente para la visualización mensual. Los archivos `phase_catalog_v1.json`, `phenology_master_summary.json` y `threat_rules_v1.json` conservan la versión, el detalle técnico y las reglas científicas.

Los umbrales están separados del calendario y mantienen su tipo de evidencia: umbral modelado, indicador regional, tratamiento experimental o asociación observacional. Las fuentes principales son Liu et al. 2023 (`10.1016/j.xplc.2023.100629`), Sun et al. 2025 (`10.5194/esd-16-1971-2025`), Zhang et al. 2023 (`10.3390/agronomy13082126`), Schauberger et al. 2017 (`10.1038/ncomms13931`) y Alsajri 2018 (`https://hdl.handle.net/11668/20905`). Una duración experimental no se interpreta como duración máxima tolerable.

La matriz completa contiene 85.916 calendarios y 687.328 registros de fase. Los intervalos conservan ciclos que cruzan el año y la suma de las ocho fases coincide con la duración inclusiva de cada ciclo. La versión es apropiada para análisis exploratorio, cruce climático y visualización global; no para recomendaciones agronómicas locales sin validación.
