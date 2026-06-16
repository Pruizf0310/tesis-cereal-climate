# Risk pivot v2

`risk_pivot_v2` summarizes climate hazards by crop and derived phenological stage for the `/risk` page. It is generated from the workbook:

`C:\Users\paola\Tesis\03_Resultados\Fenologia\geoglam_cm4ew_tabla_maestra.xlsx`

The reproducible script is `scripts/build_risk_pivot_v2.py`.

## Source columns

The method reads the `tabla_maestra` sheet and uses these columns:

- `record_id`
- `cultivo`
- `fase_original`
- `fase_estandar`
- `phase_name`
- `variable_critica`
- `umbral_optimo`
- `umbral`
- `tipo_estres`
- `impacto_cultivo`
- `nivel_evidencia`
- `fuente`
- `enlace`
- `matched_sensib_clima`
- `matched_fenologia`
- `source_merge_status`
- `data_completeness`

Rows enter the pivot only when `matched_sensib_clima = TRUE`, `matched_fenologia = TRUE`, and `variable_critica`, `umbral`, and `impacto_cultivo` are not empty.

## Derived stages

`etapa_derivada` is inferred from `fase_original`, `fase_estandar`, `phase_name`, `variable_critica`, `tipo_estres`, and `impacto_cultivo`.

The script searches explicit stage keywords first:

- Germination, emergence, seedling, establishment and seed terms become `Germinación / establecimiento`.
- Vegetative, tillering, leaf area, foliar expansion, vegetative growth and early biomass terms become `Desarrollo vegetativo`.
- Flowering, anthesis, pollination, panicle, tassel, silk, seed-setting, reproductive and sterility terms become `Floración / reproducción`.
- Grain, grain filling, grain weight, seed and pod filling terms become `Llenado de grano / formación de rendimiento`.
- Maturation, harvest, senescence, grain quality and harvest moisture terms become `Maduración / cosecha`.

If there are no clear explicit terms, the macro-phase is used:

- `Siembra a vegetativa temprana` becomes `Germinación / establecimiento`.
- `Vegetativa a reproductiva` becomes `Floración / reproducción`.
- `Maduracion a cosecha` becomes `Llenado de grano / maduración`.

The intermediate calculation also assigns `confianza_etapa`: high when explicit terms are found in `impacto_cultivo` or `variable_critica`, medium when derived from macro-phase, and low when the signal is weaker.

## Quantitative impact

`impacto_cuantitativo` is an index calculated from percentages found in `impacto_cultivo`.

The script extracts explicit percentages, including ranges such as `51.07-53.36%` or `67-70%`. For ranges, it uses the maximum value. When several percentages appear in the same text, each is scored and the maximum weighted value is kept.

Formula:

```text
impacto_cuantitativo = porcentaje_extraído * peso_tipo_impacto * factor_evidencia
```

The result is capped at 100.

Impact-type weights:

- Yield, productivity or production: `1.00`
- Seed-setting, sterility, pollination, grain filling or grain weight: `0.90`
- Biomass: `0.70`
- Leaf area, foliar expansion or vegetative growth: `0.60`
- Photosynthesis or stomatal conductance: `0.50`
- Evapotranspiration, water use efficiency or WUE: `0.40`
- General physiological effect without a clear productive variable: `0.30`

Evidence factors:

- Field evidence or field validation: `1.20`
- Experimental, controlled environment or greenhouse evidence: `1.00`
- Review, literature or synthesis evidence: `0.90`
- Unclear evidence: `0.80`

If no percentage can be extracted, `impacto_cuantitativo` is set to `No determinado`.

## Qualitative impact

`impacto_cualitativo` is assigned from the impact text and, when available, the quantitative index.

- `Crítico`: mortality, severe loss, sterility, reproductive failure, floral abortion, pollination failure, non-recoverable damage, filling collapse, or quantitative impact above 50.
- `Alto`: direct reduction in yield, biomass, leaf area, seed-setting, filling, productivity or quality, or quantitative impact above 30 and up to 50.
- `Moderado`: physiology, photosynthesis, water use efficiency, evapotranspiration or growth effects without direct yield loss, or quantitative impact above 15 and up to 30.
- `Bajo`: preventive thresholds, suboptimal conditions, mild effects, or quantitative impact up to 15.
- `No determinado`: insufficient text evidence.

`categoria_impacto` is assigned from `impacto_cuantitativo`: 0-15 is low, >15-30 is moderate, >30-50 is high, and >50 is critical. Missing quantitative values remain `No determinado`.

## Consolidation

The final pivot groups by:

- `cultivo`
- `etapa_derivada`
- `amenaza`
- `umbral`

For each group, the script keeps the most severe qualitative impact, the maximum quantitative impact, the strongest available evidence, unique sources and links, and the `record_id` values used as `registros_base`.

## Outputs

The script writes:

- `outputs/geoglam_cm4ew_tabla_maestra_risk_v2.xlsx`
- `web-v2/public/data/risk_pivot_v2.json`

The Excel output keeps `tabla_maestra` intact and creates or replaces only the `risk_pivot_v2` sheet. The JSON powers the second section of `/risk`.

## Methodological limitation

El índice cuantitativo no representa pérdida observada directa ni probabilidad de pérdida. Es un índice bibliográfico de severidad construido a partir de impactos reportados en literatura, ponderados por cercanía al rendimiento y nivel de evidencia.
