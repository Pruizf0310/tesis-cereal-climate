"""Malas cosechas por píxel en maíz, arroz, trigo y soya (GDHY 1981–2016).

Criterio (4 nov 2026): en cada píxel, con la anomalía relativa a = rendimiento / tendencia lineal 1981–2016 − 1,
  1 · anomalía estandarizada robusta z = (a − mediana(a)) / (1,4826 · MAD(a)), MAD = mediana(|a − mediana(a)|):
      mediana y MAD no se dejan arrastrar por un año extremo como 2012 (Leys et al. 2013, J. Exp. Soc. Psychol. 49:764,
      p. 2–3; b = 1,4826 hace la MAD comparable a la desviación típica);
  2 · mala cosecha si z ≤ −1: más de una desviación por debajo de lo normal del propio píxel (Utku et al. 2026, Sci. Rep.
      16:25339, «Climate resilience index»: Z < −1, con −0,5 y −1,5 como sensibilidad);
  3 · y además pérdida real ≥ 5 % frente a la tendencia (límite inferior de la clase «Poor» de GEOGLAM Crop Monitor),
      para que en los píxeles muy estables no entre un año sin pérdida.
Con solo el 5 % (primera versión) la mediana era un tercio de los años: en los píxeles variables una baja de 5 % es
variación normal. La tendencia es la misma recta de pixel_tipico_tendencia.py (reproduce el residuo de la SQLite v2 en maíz).

Entradas: 02_Procesados/GDHY_timeseries/<cultivo>_yield_1981_2016_RAW.nc y metadata/mascaras/pixeles_<cultivo>.csv.
Salida: carpeta malas_cosechas_<fecha> con
  malas_cosechas.xlsx   · una hoja por cultivo (una fila por píxel) y una hoja «resumen»;
  anual_<cultivo>.csv.gz · píxel × año: rendimiento, tendencia, pérdida relativa y si fue mala cosecha;
  resumen.json.
Uso: .venv/Scripts/python.exe malas_cosechas_pixeles.py [--cultivos maize rice wheat soybean] [--perdida 5]
"""
import argparse, json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

RAW = Path('C:/Users/paola/Tesis/02_Procesados/GDHY_timeseries')
MASCARAS = Path(__file__).resolve().parents[3] / 'metadata' / 'mascaras'
SALIDA = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/rendimiento')
ANIOS = np.arange(1981, 2017)
NOMBRE = dict(maize='Maíz', rice='Arroz', wheat='Trigo', soybean='Soya')
MIN_ANIOS = 30  # años válidos para ajustar la recta


def z_robusto(rel):
    """Anomalía estandarizada con mediana y MAD por píxel (filas); NaN se ignoran."""
    med = np.nanmedian(rel, 1, keepdims=True)
    mad = 1.4826 * np.nanmedian(np.abs(rel - med), 1, keepdims=True)
    return (rel - med) / np.where(mad > 0, mad, np.nan)


def cultivo(c, perdida, corte):
    m = pd.read_csv(MASCARAS / f'pixeles_{c}.csv', encoding='utf-8-sig')
    y = xr.open_dataset(RAW / f'{c}_yield_1981_2016_RAW.nc')['var'].values.astype(float)  # (36, 360, 720)
    y = y[:, m.lat_idx.values, m.lon_idx.values].T  # (píxeles, 36)
    ok = np.isfinite(y)
    n = ok.sum(1)
    # recta por mínimos cuadrados con los años válidos de cada píxel
    t = np.where(ok, ANIOS - ANIOS.mean(), 0.0)
    yv = np.where(ok, y, 0.0)
    tm = t.sum(1) / np.maximum(n, 1); ym = yv.sum(1) / np.maximum(n, 1)
    dt = np.where(ok, t - tm[:, None], 0.0)
    pend = (dt * (yv - ym[:, None])).sum(1) / np.maximum((dt ** 2).sum(1), 1e-12)
    tend = ym[:, None] + pend[:, None] * ((ANIOS - ANIOS.mean()) - tm[:, None])
    rel = np.where(ok & (tend > 0), y / tend - 1, np.nan) * 100
    valido = (n >= MIN_ANIOS) & (np.nanmin(tend, 1) > 0)
    z = z_robusto(rel)
    perdida_real = rel <= -perdida
    mala = (z <= corte) & perdida_real & valido[:, None]
    sens = {k: ((z <= k) & perdida_real & valido[:, None]).sum(1) for k in (-0.5, -1.5)}

    filas = pd.DataFrame(dict(
        pixel_id=m.pixel_id, latitud=m.latitude, longitud=m.longitude, anios_validos=n,
        pendiente_t_ha_por_decada=10 * pend, rendimiento_medio_t_ha=np.nanmean(y, 1), rendimiento_max_t_ha=np.nanmax(y, 1),
        valido=valido, malas_cosechas=np.where(valido, mala.sum(1), np.nan),
        pct_anios_malos=np.where(valido, 100 * mala.sum(1) / n, np.nan),
        peor_perdida_pct=np.where(valido, np.nanmin(rel, 1), np.nan),
        mad_pct=1.4826 * np.nanmedian(np.abs(rel - np.nanmedian(rel, 1, keepdims=True)), 1),
        quitados_por_5pct=np.where(valido, ((z <= corte) & ~perdida_real).sum(1), np.nan),
        malas_z_menos_0_5=np.where(valido, sens[-0.5], np.nan), malas_z_menos_1_5=np.where(valido, sens[-1.5], np.nan),
        anios_malos=[' '.join(map(str, ANIOS[r])) for r in mala]))
    filas['nota'] = np.select([~valido & (n < MIN_ANIOS), ~valido], [f'menos de {MIN_ANIOS} años válidos', 'tendencia ≤ 0 en algún año'], '')
    largo = pd.DataFrame(dict(pixel_id=np.repeat(m.pixel_id.values, len(ANIOS)), anio=np.tile(ANIOS, len(m)),
                              rendimiento_t_ha=y.ravel(), tendencia_t_ha=tend.ravel(), perdida_relativa_pct=rel.ravel(),
                              z_robusto=z.ravel(), mala_cosecha=mala.ravel().astype(int)))
    return filas, largo


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cultivos', nargs='+', default=['maize', 'rice', 'wheat', 'soybean'])
    ap.add_argument('--perdida', type=float, default=5.0, help='pérdida mínima frente a la tendencia, en %')
    ap.add_argument('--corte', type=float, default=-1.0, help='z robusto máximo para mala cosecha')
    a = ap.parse_args()
    out = SALIDA / f'malas_cosechas_{datetime.now():%Y%m%d_%H%M%S}'
    out.mkdir()
    hojas, resumen = {}, []
    for c in a.cultivos:
        f, largo = cultivo(c, a.perdida, a.corte)
        largo.to_csv(out / f'anual_{c}.csv.gz', index=False)
        hojas[NOMBRE[c]] = f
        v = f[f.valido]
        dist = v.malas_cosechas.value_counts().sort_index()
        resumen.append(dict(cultivo=NOMBRE[c], pixeles=len(f), validos=len(v), sin_mala_cosecha=int((v.malas_cosechas == 0).sum()),
                            con_1_o_2=int(v.malas_cosechas.between(1, 2).sum()), mediana_malas=float(v.malas_cosechas.median()),
                            p10_malas=float(v.malas_cosechas.quantile(.1)), p90_malas=float(v.malas_cosechas.quantile(.9)),
                            max_malas=int(v.malas_cosechas.max()), mediana_pct_anios=float(v.pct_anios_malos.median()),
                            distribucion={int(k): int(x) for k, x in dist.items()}))
        print(NOMBRE[c], resumen[-1]['validos'], 'píxeles válidos; mediana', resumen[-1]['mediana_malas'], 'malas cosechas')
    r = pd.DataFrame(resumen)
    with pd.ExcelWriter(out / 'malas_cosechas.xlsx') as w:
        r.drop(columns='distribucion').to_excel(w, sheet_name='resumen', index=False)
        for k, f in hojas.items():
            f.to_excel(w, sheet_name=k, index=False)
    (out / 'resumen.json').write_text(json.dumps(dict(
        criterio=(f'mala cosecha = z robusto (mediana y 1,4826·MAD de la anomalía relativa del píxel) ≤ {a.corte:g} '
                  f'y pérdida ≥ {a.perdida:g} % frente a la tendencia lineal 1981–2016'),
        fuentes=['Leys et al. 2013, J. Exp. Soc. Psychol. 49:764 (mediana y MAD, b = 1,4826)',
                 'Utku et al. 2026, Sci. Rep. 16:25339 (choque negativo: Z < −1; sensibilidad −0,5 y −1,5)',
                 'GEOGLAM Crop Monitor, clase Poor (≥ 5 % bajo el promedio)'],
        min_anios_validos=MIN_ANIOS, cultivos=resumen), ensure_ascii=False, indent=1), encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
