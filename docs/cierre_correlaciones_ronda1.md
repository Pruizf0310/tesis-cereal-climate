# Cierre de la primera ronda de correlaciones (maíz de secano)

**Fecha de cierre:** 29 oct 2026. **Estado:** análisis cerrado. No se vuelve a correr; queda como antecedente.

## Qué se hizo

- 10.923 píxeles GDHY de maíz de secano, 36 cosechas (1981–2016), seis fases (EST, VEG, FLO, REP, FIL, MAT).
- Alineación maturity-year: el rendimiento GDHY se etiqueta por año de cosecha (Iizumi y Sakai, 2020, *Sci Data* 7:97).
- Pearson por píxel y por grupo de calendario (hemisferio × trimestre de siembra) entre amenazas por fase y rendimiento sin tendencia; ONI (meses 0 a −11 antes de la cosecha) y MJO (fracción de días en fases 1–8).
- Corridas vigentes: `03_Resultados/Agroclima/vigente/rendimiento/cruce_v2_20261024_184932/` → `correlaciones_v2_20261024_185040`, `analisis_v2_20261025_222548`, `correlaciones_calendario_20261027_150249` (auditada) y `teleconexion_20261028_092051`.

## Qué mostró

| Pregunta | Resultado |
|---|---|
| ¿Calor y sequía por fase se asocian con el rendimiento? | Sí. Con Bonferroni sobreviven 14 celdas grupo×fase de calor, 11 de EDD29 y 9 de sequía. |
| ¿ONI se asocia con el rendimiento? | No de forma robusta: 0 celdas tras Bonferroni; ONI→rendimiento por píxel sin significancia de campo. |
| ¿MJO se asocia con el rendimiento? | No: 0 celdas tras Bonferroni. |
| ¿Se puede atribuir el impacto a una fase? | No con este diseño: VEG, FLO y FIL son colineales. |

## Por qué se cierra y se cambia de método

1. **El conteo de episodios no distingue duración** (sugerencia del director de tesis, 29 oct 2026): 10 episodios pueden ser 2 de 8 días, 3 de 2 días y 5 de 10 días. La variable `episodios` los trata igual.
2. **Al clima no se le quitó la tendencia**; solo al rendimiento. Se cuantificó el 29 oct (abajo).
3. Calendario fijo por píxel, 38–52 % de píxeles sin días de calor en algunas fases, autocorrelación lag-1 > 0,3 en 34 % de píxeles y píxeles de secano en zonas desérticas.

## Efecto de no haber quitado la tendencia al clima (verificado 29 oct 2026)

Script: `scripts/agroclima/pipeline_amenazas/pixel_tipico_tendencia.py`. Salida: `03_Resultados/Agroclima/vigente/pixel_tipico/tendencia_20261029_175706/tendencia.xlsx`.

- Como el rendimiento ya está sin tendencia, r(clima crudo, rendimiento sin tendencia) = r(ambos sin tendencia) · √(1 − R²), donde R² es la fracción de la variable climática explicada por el año. **El signo nunca cambia; solo la magnitud.**
- En los 10.923 píxeles, el cambio de r al quitar la tendencia al clima es mediana ≤ 0,004 y percentil 95 ≤ 0,04 en todas las fases y variables (episodios, EDD29, P − ETP). Menos de 0,25 % de los píxeles cambian más de 0,1.
- Sí hay tendencia climática en una parte de los píxeles: EDD29 en FIL tiene pendiente con p < 0,05 en 29 % de los píxeles (mediana +2,3 °C·día por década); por azar se esperaría 5 %.
- **Conclusión:** las conclusiones de la primera ronda se mantienen. En la segunda ronda se quitará la tendencia a ambas series por consistencia metodológica.

## Límite que no resuelve quitar la tendencia

La recta del rendimiento recoge tecnología y manejo, pero también cualquier efecto gradual del clima. Esa parte del efecto climático queda dentro de la recta y no en el residuo.

## Segunda ronda

Un píxel de referencia (191325, Nebraska, 42,75° N 97,25° O), evento por evento: tipo de evento, duración, intensidad y fase; correlación con cada variable sin tendencia, con diagramas de dispersión. Diapositivas 30–34 de la presentación oficial.
